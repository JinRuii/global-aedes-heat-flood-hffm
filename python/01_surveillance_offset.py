"""Estimate relative surveillance capacity and the HFFM offset."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import statsmodels.api as sm


def add_surveillance_offset(df: pd.DataFrame, lat_limit: float = 53.75) -> pd.DataFrame:
    out = df.copy()
    out["log_healthcare"] = np.log(out["healthcare_motor_mean"] + 1.0)
    out["log_gdp"] = np.log(out["gdp_per_capita"] + 1.0)
    out["is_endemic_zone"] = np.where(np.abs(out["Y"]) <= lat_limit, 1, 0)

    train = out.loc[out["is_endemic_zone"] == 1].copy()
    vars_ = ["log_healthcare", "log_gdp", "built_ratio"]
    x_mean = train[vars_].mean()
    x_std = train[vars_].std(ddof=1)

    x_train = (train[vars_] - x_mean) / x_std
    x_train = sm.add_constant(x_train)
    model = sm.Logit(train["dcz_occ"], x_train).fit(disp=True)

    x_all = (out[vars_] - x_mean) / x_std
    x_all = sm.add_constant(x_all)
    out["detect_prob"] = model.predict(x_all)
    out["detect_prob_clipped"] = np.clip(out["detect_prob"], 0.001, 0.999)
    out["surveillance_offset"] = np.log(
        out["detect_prob_clipped"] / (1.0 - out["detect_prob_clipped"])
    )
    return out, model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Historical panel CSV before offset")
    parser.add_argument("--output", required=True, help="Output panel with surveillance fields")
    parser.add_argument("--lat-limit", type=float, default=53.75)
    args = parser.parse_args()

    df = pd.read_csv(args.input, low_memory=False)
    out, model = add_surveillance_offset(df, lat_limit=args.lat_limit)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(model.summary())
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
