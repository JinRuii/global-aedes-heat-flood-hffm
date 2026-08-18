"""Apply the historical FAI transform to future river and rainfall panels."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

INDICATORS = ["flow_r95d", "max_discharge", "Rx5day", "R95d"]
SCENARIOS = ["SSP1", "SSP3", "SSP5"]


def load_transform(params_path: Path):
    params = json.loads(Path(params_path).read_text(encoding="utf-8"))
    scaler = StandardScaler()
    scaler.mean_ = np.array(params["scaler_mean"], dtype=float)
    scaler.scale_ = np.array(params["scaler_scale"], dtype=float)
    scaler.var_ = scaler.scale_ ** 2
    scaler.n_features_in_ = len(params["indicators"])
    pca = PCA(n_components=1)
    pca.components_ = np.array(params["pca_components"], dtype=float).reshape(1, -1)
    pca.explained_variance_ratio_ = np.array([params["pca_explained_variance_ratio"]])
    pca.n_features_in_ = len(params["indicators"])
    return scaler, pca, params


def to_fai(values, scaler, pca, params):
    pc1 = pca.transform(scaler.transform(values)).ravel()
    pc1_c = np.clip(pc1, params["pc1_clip_lo"], params["pc1_clip_hi"])
    return (pc1_c - params["pc1_min"]) / (params["pc1_max"] - params["pc1_min"])


def melt_indicator(path: Path, value_name: str) -> pd.DataFrame:
    wide = pd.read_csv(path)
    return wide.melt(id_vars="paixu", var_name="year", value_name=value_name)


def build_scenario(river_dir: Path, rain_dir: Path, pref: str) -> pd.DataFrame:
    aliases = {"SSP1": ["SSP1"], "SSP3": ["SSP3", "SSP370"], "SSP5": ["SSP5"]}
    names = aliases[pref]
    def first_existing(folder, pattern_prefix, pattern_suffix):
        for name in names:
            p = folder / f"{pattern_prefix}{name}{pattern_suffix}"
            if p.exists():
                return p
        raise FileNotFoundError(f"Missing {pattern_prefix}*{pattern_suffix} for {pref}")

    rr = melt_indicator(first_existing(river_dir, "river_panel_", "_r95d.csv"), "flow_r95d")
    ra = melt_indicator(first_existing(river_dir, "river_panel_", "_annualmax.csv"), "max_discharge")
    rx = melt_indicator(first_existing(rain_dir, "rain_panel_", "_rx5day.csv"), "Rx5day")
    r5 = melt_indicator(first_existing(rain_dir, "rain_panel_", "_r95d.csv"), "R95d")
    d = rr.merge(ra, on=["paixu", "year"]).merge(rx, on=["paixu", "year"]).merge(r5, on=["paixu", "year"])
    d["year"] = d["year"].astype(int)
    d.loc[:, INDICATORS] = d[INDICATORS].fillna(0.0)
    return d


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--river-dir", required=True)
    parser.add_argument("--rain-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    scaler, pca, params = load_transform(args.params)
    hist = pd.read_csv(args.historical, usecols=["paixu", "year", "flood_activation_index"])
    hist = hist.rename(columns={"flood_activation_index": "FAI"})

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fut_frames = []
    for pref in SCENARIOS:
        d = build_scenario(Path(args.river_dir), Path(args.rain_dir), pref)
        d["FAI"] = to_fai(d[INDICATORS].to_numpy(dtype=float), scaler, pca, params)
        d[["paixu", "year"] + INDICATORS + ["FAI"]].to_csv(out_dir / f"future_FAI_{pref}.csv", index=False)
        fut_frames.append(d[["paixu", "year", "FAI"]].assign(scenario=pref))
        print(f"{pref}: median FAI={np.nanmedian(d['FAI']):.3f}")

    print(f"Wrote future FAI files to {out_dir}")


if __name__ == "__main__":
    main()
