import pandas as pd

def validate(output_path, ct_path):
    report = {}

    # Load files
    df = pd.read_csv(output_path)
    ct = pd.read_csv(ct_path)

    # Required columns
    required = ["STUDYID", "USUBJID", "VSTESTCD", "VSORRES"]

    report["missing_columns"] = [c for c in required if c not in df.columns]

    # Null check
    report["null_vsorres"] = int(df["VSORRES"].isna().sum())

    # Valid test codes
    if "VSTESTCD" in ct.columns:
        valid_terms = set(ct["VSTESTCD"])
    else:
        valid_terms = set(df["VSTESTCD"])  # fallback

    report["invalid_test_codes"] = int(
        (~df["VSTESTCD"].isin(valid_terms)).sum()
    )

    # Row count
    report["row_count"] = len(df)

    return report