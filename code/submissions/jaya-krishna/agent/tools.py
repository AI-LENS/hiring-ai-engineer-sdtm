import os
import subprocess
import pandas as pd
from langchain_core.tools import tool


# Project root is the working directory when run.py is executed.
# All file paths are expressed relative to this root.
CSV_DIR        = "csv_files"
RAW_CSV        = f"{CSV_DIR}/vs_raw.csv"
CT_CSV         = f"{CSV_DIR}/sdtm_ct.csv"
OUTPUT_CSV     = "output/vs.csv"
OUTPUT_DIR     = "output"


@tool
def get_data_schemas() -> str:
    """
    Reads vs_raw.csv and sdtm_ct.csv to provide the agent with exact column
    names and valid CT term values for the three VS codelists it needs.
    """
    try:
        raw_df = pd.read_csv(RAW_CSV, nrows=3)
        raw_columns = raw_df.columns.tolist()

        ct_df = pd.read_csv(CT_CSV)

        vs_relevant_codes = ["C66741", "C67153", "C66770"]
        ct_filtered = ct_df[ct_df["codelist_code"].isin(vs_relevant_codes)]

        ct_summary = {}
        for code in vs_relevant_codes:
            terms = ct_filtered[ct_filtered["codelist_code"] == code]["term_value"].tolist()
            ct_summary[code] = terms

        report = (
            f"Input file     : {RAW_CSV}\n"
            f"Raw columns    : {raw_columns}\n"
            f"\n"
            f"CT C66741 (VSTESTCD) valid values : {ct_summary.get('C66741', [])}\n"
            f"CT C67153 (VSTEST)   valid values : {ct_summary.get('C67153', [])}\n"
            f"CT C66770 (VSORRESU) valid values : {ct_summary.get('C66770', [])}\n"
            f"\n"
            f"Use assign_no_ct() + hardcode_ct() + assign_ct() from sdtm.oak. "
            f"Do NOT use map_vs() — it does not exist.\n"
            f"Output must be written to: {OUTPUT_CSV}"
        )
        return report
    except Exception as e:
        return f"Error reading schemas: {str(e)}"


@tool
def execute_r_script(r_code: str) -> str:
    """
    Prepends a setwd() call to anchor the working directory to the project
    root, then writes and executes the R script. Returns stdout on success
    or stderr on failure so the agent can diagnose and fix errors.

    The setwd() prepend means the agent never needs to worry about relative
    paths — csv_files/vs_raw.csv and output/vs.csv always resolve correctly.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    script_path = f"{OUTPUT_DIR}/generated.R"

    # Anchor R's working directory to the project root deterministically.
    # This eliminates the entire class of "file not found" errors caused by
    # R defaulting to a different working directory than Python.
    project_root = os.getcwd().replace("\\", "/")
    wd_header    = f'setwd("{project_root}")\n\n'
    full_script  = wd_header + r_code

    with open(script_path, "w") as f:
        f.write(full_script)

    try:
        result = subprocess.run(
            ["Rscript", script_path],
            capture_output=True,
            text=True,
            timeout=60
        )
    except subprocess.TimeoutExpired:
        return "FAILURE: R script execution timed out after 60 seconds. Simplify or debug the script."

    if result.returncode == 0:
        # Confirm the expected output file was actually created
        if not os.path.exists(OUTPUT_CSV):
            return (
                f"FAILURE: R script ran without errors but {OUTPUT_CSV} was not created. "
                f"Check that write_csv() targets 'output/vs.csv', not 'vs.csv'."
            )
        return (
            f"SUCCESS: R script executed. Output written to {OUTPUT_CSV}.\n"
            f"Logs: {result.stdout}"
        )
    else:
        return (
            f"FAILURE: R script execution failed. Analyze this error and fix the code:\n"
            f"{result.stderr}"
        )


@tool
def validate_sdtm_output() -> str:
    """
    Validates output/vs.csv against SDTM structural requirements and CDISC
    Controlled Terminology for all three relevant VS codelists:
      - C66741 : VSTESTCD
      - C67153 : VSTEST
      - C66770 : VSORRESU
    Also checks mandatory columns, missing values, and row count sanity.
    """
    try:
        if not os.path.exists(OUTPUT_CSV):
            return f"FAILURE: {OUTPUT_CSV} does not exist. The R script failed to produce output."

        output_df = pd.read_csv(OUTPUT_CSV)
        ct_df     = pd.read_csv(CT_CSV)

        report_lines = []
        hard_fails   = []

        # ------------------------------------------------------------------ #
        # 0. Row count sanity — 4 tests per subject                           #
        # ------------------------------------------------------------------ #
        expected_tests = {"TEMP", "SYSBP", "DIABP", "PULSE"}
        report_lines.append(f"Metrics -> Generated Rows: {len(output_df)}")

        if "USUBJID" in output_df.columns and "VSTESTCD" in output_df.columns:
            n_subjects    = output_df["USUBJID"].nunique()
            expected_rows = n_subjects * len(expected_tests)
            if len(output_df) != expected_rows:
                hard_fails.append(
                    f"HARD FAIL: Row count mismatch. "
                    f"Expected {expected_rows} ({n_subjects} subjects x 4 tests), "
                    f"got {len(output_df)}."
                )
            else:
                report_lines.append(
                    f"PASS: Row count correct — {n_subjects} subjects x 4 tests = {expected_rows} rows."
                )

        # ------------------------------------------------------------------ #
        # 1. Mandatory SDTM columns present                                   #
        # ------------------------------------------------------------------ #
        required_cols = ["STUDYID", "USUBJID", "VSTESTCD", "VSTEST", "VSORRES"]
        missing_cols  = [col for col in required_cols if col not in output_df.columns]
        if missing_cols:
            hard_fails.append(f"HARD FAIL: Missing required SDTM columns: {missing_cols}")
            report_lines.extend(hard_fails)
            return "\n".join(report_lines)
        else:
            report_lines.append("PASS: All mandatory SDTM columns are present.")

        # ------------------------------------------------------------------ #
        # 2. Missing value check on mandatory columns                         #
        # ------------------------------------------------------------------ #
        for col in required_cols:
            n_missing = output_df[col].isna().sum()
            if n_missing > 0:
                hard_fails.append(
                    f"HARD FAIL: Mandatory column '{col}' has {n_missing} missing value(s)."
                )
        if not any("missing value" in f for f in hard_fails):
            report_lines.append("PASS: No missing values in mandatory columns.")

        # ------------------------------------------------------------------ #
        # 3. CT Validation — VSTESTCD against C66741                          #
        # ------------------------------------------------------------------ #
        valid_testcds  = set(ct_df[ct_df["codelist_code"] == "C66741"]["term_value"].tolist())
        if valid_testcds:
            invalid_testcds = (
                output_df[~output_df["VSTESTCD"].isin(valid_testcds)]["VSTESTCD"]
                .dropna().unique().tolist()
            )
            if invalid_testcds:
                hard_fails.append(
                    f"HARD FAIL: VSTESTCD values not in CT C66741: {invalid_testcds}"
                )
            else:
                report_lines.append("PASS: VSTESTCD aligns with CT codelist C66741.")
        else:
            hard_fails.append("HARD FAIL: CT codelist C66741 (VSTESTCD) is empty — check sdtm_ct.csv.")

        # ------------------------------------------------------------------ #
        # 4. CT Validation — VSTEST against C67153                            #
        # ------------------------------------------------------------------ #
        valid_vstests = set(ct_df[ct_df["codelist_code"] == "C67153"]["term_value"].tolist())
        if "VSTEST" in output_df.columns and valid_vstests:
            invalid_vstests = (
                output_df[~output_df["VSTEST"].isin(valid_vstests)]["VSTEST"]
                .dropna().unique().tolist()
            )
            if invalid_vstests:
                hard_fails.append(
                    f"HARD FAIL: VSTEST values not in CT C67153: {invalid_vstests}"
                )
            else:
                report_lines.append("PASS: VSTEST aligns with CT codelist C67153.")
        else:
            report_lines.append(
                "WARN: CT codelist C67153 (VSTEST) is empty or VSTEST column absent — skipping."
            )

        # ------------------------------------------------------------------ #
        # 5. CT Validation — VSORRESU against C66770                          #
        # ------------------------------------------------------------------ #
        valid_units = set(ct_df[ct_df["codelist_code"] == "C66770"]["term_value"].tolist())
        if "VSORRESU" in output_df.columns and valid_units:
            invalid_units = (
                output_df[
                    output_df["VSORRESU"].notna() &
                    ~output_df["VSORRESU"].isin(valid_units)
                ]["VSORRESU"].unique().tolist()
            )
            if invalid_units:
                hard_fails.append(
                    f"HARD FAIL: VSORRESU values not in CT C66770: {invalid_units}"
                )
            else:
                report_lines.append("PASS: VSORRESU aligns with CT codelist C66770.")
        else:
            report_lines.append(
                "WARN: VSORRESU column absent or C66770 codelist empty — units not validated."
            )

        # ------------------------------------------------------------------ #
        # 6. Compile and write final report                                    #
        # ------------------------------------------------------------------ #
        if hard_fails:
            report_lines.extend(hard_fails)
            final_report = "\n".join(report_lines)
            with open(f"{OUTPUT_DIR}/validation_report.md", "w") as f:
                f.write("# SDTM Validation Report\n\n")
                f.write(final_report)
            return "VALIDATION FAILED:\n" + final_report

        final_report = "\n".join(report_lines)
        with open(f"{OUTPUT_DIR}/validation_report.md", "w") as f:
            f.write("# SDTM Validation Report\n\n")
            f.write(final_report)

        return "VALIDATION SUCCESS: Dataset meets SDTM shape and CT rigor.\n" + final_report

    except Exception as e:
        return f"Validation process encountered a systemic error: {str(e)}"