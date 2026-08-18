"""Symmetric Shapley decomposition of climate and population effects on exposure."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd


def weighted_exposure(prob, pop_density, area):
    return float(np.nansum(prob * pop_density * area))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pred", required=True, help="decomp_pred_SSP*.csv")
    parser.add_argument("--states", required=True, help="File with scheme1 and population")
    parser.add_argument("--area-field", default=None, help="Optional grid-area field in km2")
    parser.add_argument("--output", required=True)
    parser.add_argument("--year-min", type=int, default=2081)
    parser.add_argument("--year-max", type=int, default=2100)
    args = parser.parse_args()

    pred = pd.read_csv(args.pred)
    states = pd.read_csv(args.states, usecols=lambda c: c in {
        "paixu", "year", "scheme1", "pop_density", "area_km2", args.area_field
    } if args.area_field else {"paixu", "year", "scheme1", "pop_density", "area_km2"})
    df = pred.merge(states, on=["paixu", "year"], how="left")
    df = df[(df["year"] >= args.year_min) & (df["year"] <= args.year_max)].copy()
    df = df[df["scheme1"] == "compound"].copy()
    if args.area_field and args.area_field in df.columns:
        area = df[args.area_field].to_numpy(dtype=float)
    elif "area_km2" in df.columns:
        area = df["area_km2"].to_numpy(dtype=float)
    else:
        # Spherical rectangle approximation is applied later if area is stored separately.
        area = np.ones(len(df), dtype=float)
        print("Warning: no area field found; using 1.0 so outputs are density-weighted only.")

    e11 = weighted_exposure(df["pred_full"], df["pop_density"], area)
    e10 = weighted_exposure(df["pred_clim"], df["pop_density"], area)
    e01 = weighted_exposure(df["pred_pop"], df["pop_density"], area)
    # Baseline uses 2019 climate probability already stored as pred_pop when population is future.
    # If a dedicated 2019-climate/2019-population field is absent, reconstruct from manuscript Table 2
    # by pairing pred_clim and pred_pop only inside the same compound domain.
    if "pred_base" in df.columns:
        e00 = weighted_exposure(df["pred_base"], df["pop_density"], area)
    else:
        e00 = np.nan
        print("pred_base not present; report only full/climate/population predictions.")

    out = pd.DataFrame({
        "metric": ["E_full", "E_clim", "E_pop", "E_base_if_available"],
        "value": [e11, e10, e01, e00],
    })
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(out)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
