"""Build the flood activation index (FAI) from four hydrometeorological indicators."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

INDICATORS = ["flow_r95d", "max_discharge", "Rx5day", "R95d"]


def fit_fai_transform(hist: pd.DataFrame):
    x = hist[INDICATORS].to_numpy(dtype=float)
    scaler = StandardScaler().fit(x)
    xs = scaler.transform(x)
    pca = PCA(n_components=1).fit(xs)
    pc1 = pca.transform(xs).ravel()
    mu, sd = float(pc1.mean()), float(pc1.std())
    lo, hi = mu - 3.0 * sd, mu + 3.0 * sd
    pc1_c = np.clip(pc1, lo, hi)
    mn, mx = float(pc1_c.min()), float(pc1_c.max())
    params = {
        "indicators": INDICATORS,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "pca_components": pca.components_[0].tolist(),
        "pca_explained_variance_ratio": float(pca.explained_variance_ratio_[0]),
        "pc1_clip_lo": lo,
        "pc1_clip_hi": hi,
        "pc1_min": mn,
        "pc1_max": mx,
    }
    return scaler, pca, params


def apply_fai(df: pd.DataFrame, scaler, pca, params) -> np.ndarray:
    x = df[INDICATORS].fillna(0.0).to_numpy(dtype=float)
    pc1 = pca.transform(scaler.transform(x)).ravel()
    pc1_c = np.clip(pc1, params["pc1_clip_lo"], params["pc1_clip_hi"])
    return (pc1_c - params["pc1_min"]) / (params["pc1_max"] - params["pc1_min"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", required=True, help="1990-2019 panel used to fit FAI")
    parser.add_argument("--output", required=True, help="Historical panel with FAI appended")
    parser.add_argument("--params-out", required=True, help="JSON of historical FAI transform")
    args = parser.parse_args()

    hist = pd.read_csv(args.historical, low_memory=False)
    scaler, pca, params = fit_fai_transform(hist)
    hist["flood_activation_index"] = apply_fai(hist, scaler, pca, params)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    hist.to_csv(args.output, index=False)
    Path(args.params_out).write_text(json.dumps(params, indent=2), encoding="utf-8")
    print(f"PC1 variance explained: {params['pca_explained_variance_ratio']:.4f}")
    print(f"Loadings: {dict(zip(INDICATORS, np.round(pca.components_[0], 4)))}")
    print(f"Wrote {args.output}")
    print(f"Wrote {args.params_out}")


if __name__ == "__main__":
    main()
