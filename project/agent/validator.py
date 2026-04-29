# agent/validator.py

import pandas as pd
import os


REQUIRED_COLUMNS = [
    "STUDYID",
    "USUBJID",
    "VSTESTCD",
    "VSTEST",
    "VSORRES",
    "VSORRESU",
    "VSSTRESC",
    "VSSTRESU"
]


def check_file_exists():
    """
    Check if output/vs.csv exists
    """

    if not os.path.exists("output/vs.csv"):
        print("vs.csv not found")
        return False

    return True


def check_required_columns(df):
    """
    Check required SDTM columns
    """

    missing = []

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing.append(col)

    if missing:
        print("\nMissing Columns:")
        print(missing)
    else:
        print("\nAll required columns present ✅")

    return missing


def check_row_count(df):
    """
    Compare output rows vs raw rows
    """

    raw_df = pd.read_csv("data/vs_raw.csv")

    raw_rows = len(raw_df)
    output_rows = len(df)

    print(f"\nRaw rows: {raw_rows}")
    print(f"Output rows: {output_rows}")

    if output_rows >= raw_rows:
        print("Row count looks reasonable ✅")
    else:
        print("Row count may be incorrect ⚠️")


def check_ct_values(df):
    """
    Simple CT validation
    """

    print("\nChecking CT values...")

    valid_test_codes = ["TEMP", "SYSBP", "DIABP", "PULSE"]
    valid_units = ["F", "C", "mmHg", "bpm"]

    invalid_testcd = df[
        ~df["VSTESTCD"].isin(valid_test_codes)
    ]

    invalid_units = df[
        ~df["VSORRESU"].isin(valid_units)
    ]

    if len(invalid_testcd) == 0:
        print("VSTESTCD validation passed ✅")
    else:
        print("Invalid VSTESTCD found ⚠️")

    if len(invalid_units) == 0:
        print("VSORRESU validation passed ✅")
    else:
        print("Invalid units found ⚠️")


def compare_with_golden(df):
    """
    Compare row count with golden dataset
    """

    golden_df = pd.read_csv("data/vs_golden.csv")

    print(f"\nGolden rows: {len(golden_df)}")
    print(f"Our rows: {len(df)}")

    difference = abs(len(golden_df) - len(df))

    print(f"Row difference: {difference}")


def run_validation():
    """
    Main validation flow
    """

    if not check_file_exists():
        return

    df = pd.read_csv("output/vs.csv")

    print("\nStarting validation...\n")

    check_required_columns(df)
    check_row_count(df)
    check_ct_values(df)
    compare_with_golden(df)

    print("\nValidation completed ✅")


if __name__ == "__main__":
    run_validation()