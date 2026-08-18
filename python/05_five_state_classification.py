"""Classify five thermal-flood climate-risk states."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd

TSI_LOW = 77.8
TSI_HIGH = 236.1
FAI_WATER = 0.24
FAI_DEFAULT = 0.407


def classify(tsi, fai, x_r):
    x_star = np.maximum(FAI_WATER, np.where(np.isnan(x_r), FAI_DEFAULT, x_r))
    state = np.full(len(tsi), "water", dtype=object)
    state[tsi < TSI_LOW] = "cold"
    state[tsi > TSI_HIGH] = "heat"
    mid = (tsi >= TSI_LOW) & (tsi <= TSI_HIGH)
    state[mid & (fai < FAI_WATER)] = "water"
    state[mid & (fai >= FAI_WATER) & (fai < x_star)] = "flushing"
    state[mid & (fai >= x_star)] = "compound"
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--thresholds", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input, low_memory=False)
    thr = pd.read_csv(args.thresholds)
    if "x_r" not in df.columns:
        df = df.merge(thr, on="region_acronym", how="left")
    df["scheme1"] = classify(
        df["thermal_suitability_integral"].to_numpy(dtype=float),
        df["flood_activation_index"].to_numpy(dtype=float),
        df["x_r"].to_numpy(dtype=float),
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(df["scheme1"].value_counts())
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
