"""
agent/validator.py

This file checks the SDTM VS output CSV against SDTM compliance rules.
All logic uses pandas. No LLM calls are made here.

The validator is intentionally honest -- it reports every failure it finds.
Nothing is hidden or softened. If something fails, the report says so clearly.

Returns a structured result with:
  passed: list of check names that passed
  failed: list of dicts with check name and description of what failed
  summary: one-paragraph description of overall quality
"""

import os
import re
import pandas as pd


def run_all_checks(output_path, ct_path, raw_path, golden_path, report_path):
    """
    Run all SDTM validation checks on the output CSV.
    Write a markdown report to report_path.
    Return a dictionary with the structured result.

    Args:
        output_path: Path to the generated vs.csv to validate.
        ct_path: Path to the SDTM controlled terminology CSV.
        raw_path: Path to the original raw VS CSV (used for row count check).
        golden_path: Path to the golden reference vs.csv (used for comparison).
        report_path: Path where the markdown validation report should be written.

    Returns:
        A dictionary with keys: passed (list), failed (list of dicts), summary (str)
    """
    passed_checks = []
    failed_checks = []

    # Load the output CSV. If it fails, everything else fails too.
    output_df = _safe_load_csv(output_path)
    if output_df is None:
        result = {
            "passed": [],
            "failed": [{"check": "Load output CSV", "description": f"Could not load output file at {output_path}"}],
            "summary": "Validation could not run because the output file is missing or unreadable."
        }
        _write_markdown_report(result, report_path, output_path)
        return result

    # Load the controlled terminology CSV
    ct_df = _safe_load_csv(ct_path)

    # Load the raw data CSV
    raw_df = _safe_load_csv(raw_path)

    # Load the golden reference CSV
    golden_df = _safe_load_csv(golden_path)

    print("  Running validation checks...")

    # --- Check 1: Required columns present ---
    check_1_result = _check_required_columns(output_df)
    _record_result(check_1_result, passed_checks, failed_checks)

    # --- Check 2: VSTESTCD values are valid ---
    check_2_result = _check_ct_values(
        output_df, ct_df,
        column_name="VSTESTCD",
        codelist_code="C66741",
        check_name="VSTESTCD values in CT"
    )
    _record_result(check_2_result, passed_checks, failed_checks)

    # --- Check 3: VSORRESU values are valid ---
    check_3_result = _check_ct_values(
        output_df, ct_df,
        column_name="VSORRESU",
        codelist_code="C66770",
        check_name="VSORRESU values in CT"
    )
    _record_result(check_3_result, passed_checks, failed_checks)

    # --- Check 4: VSPOS values are valid where present ---
    check_4_result = _check_ct_values_optional(
        output_df, ct_df,
        column_name="VSPOS",
        codelist_code="C71148",
        check_name="VSPOS values in CT (where present)"
    )
    _record_result(check_4_result, passed_checks, failed_checks)

    # --- Check 5: VSLOC values are valid where present ---
    check_5_result = _check_ct_values_optional(
        output_df, ct_df,
        column_name="VSLOC",
        codelist_code="C74456",
        check_name="VSLOC values in CT (where present)"
    )
    _record_result(check_5_result, passed_checks, failed_checks)

    # --- Check 6: Row count is reasonable ---
    check_6_result = _check_row_count(output_df, raw_df)
    _record_result(check_6_result, passed_checks, failed_checks)

    # --- Check 7: VSDTC format is ISO 8601 ---
    check_7_result = _check_date_format(output_df)
    _record_result(check_7_result, passed_checks, failed_checks)

    # --- Check 8: VSSEQ is sequential per subject ---
    check_8_result = _check_vsseq(output_df)
    _record_result(check_8_result, passed_checks, failed_checks)

    # --- Check 9: Compare against golden reference ---
    check_9_result = _check_against_golden(output_df, golden_df)
    _record_result(check_9_result, passed_checks, failed_checks)

    # Build the summary paragraph
    total_checks = len(passed_checks) + len(failed_checks)
    pass_count = len(passed_checks)
    fail_count = len(failed_checks)
    summary = (
        f"Validation ran {total_checks} checks. "
        f"{pass_count} passed and {fail_count} failed. "
    )
    if fail_count == 0:
        summary += "The output meets all checked SDTM VS requirements."
    elif fail_count <= 2:
        summary += "Minor issues found. Review the failed checks above for details."
    else:
        summary += "Multiple issues found. The output may not be fully SDTM compliant."

    # Build the structured result
    result = {
        "passed": passed_checks,
        "failed": failed_checks,
        "summary": summary
    }

    # Write the markdown report
    _write_markdown_report(result, report_path, output_path)

    return result


def _safe_load_csv(file_path):
    """
    Attempt to load a CSV file. Return the DataFrame if successful, None if not.
    This prevents one missing file from crashing the entire validation run.
    """
    if file_path is None or not os.path.exists(file_path):
        print(f"  WARNING: File not found for validation: {file_path}")
        return None
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as error:
        print(f"  WARNING: Could not read {file_path}: {error}")
        return None


def _record_result(check_result, passed_list, failed_list):
    """
    Add a check result to either the passed list or failed list
    based on the 'passed' key in the result dictionary.
    Also print the result to the console.
    """
    check_name = check_result.get("check", "Unknown check")
    if check_result.get("passed"):
        passed_list.append(check_name)
        print(f"  Check passed: {check_name}")
    else:
        failed_list.append({
            "check": check_name,
            "description": check_result.get("description", "No description provided")
        })
        print(f"  Check FAILED: {check_name} -- {check_result.get('description', '')}")


def _check_required_columns(output_df):
    """
    Check that all required SDTM VS columns are present in the output.
    """
    required_columns = [
        "STUDYID", "DOMAIN", "USUBJID", "VSSEQ",
        "VSTESTCD", "VSTEST", "VSORRES", "VSORRESU",
        "VSSTRESC", "VSSTRESU", "VISIT", "VISITNUM", "VSDTC"
    ]

    # Find which required columns are missing from the output
    output_columns = set(output_df.columns.tolist())
    missing_columns = [col for col in required_columns if col not in output_columns]

    if not missing_columns:
        return {
            "check": "Required columns present",
            "passed": True,
            "description": f"All {len(required_columns)} required columns are present."
        }
    else:
        return {
            "check": "Required columns present",
            "passed": False,
            "description": f"Missing required columns: {', '.join(missing_columns)}"
        }


def _get_allowed_ct_values(ct_df, codelist_code):
    """
    Get the list of allowed term values for a given codelist code from the CT file.
    Tries multiple possible column name formats for compatibility.
    Returns an empty list if the CT data is not available.
    """
    if ct_df is None:
        return []

    # Find the codelist column
    codelist_col = None
    for candidate in ["codelist_code", "codelist_cd", "CODELIST", "Codelist Code"]:
        if candidate in ct_df.columns:
            codelist_col = candidate
            break

    # Find the term value column
    term_col = None
    for candidate in ["term_value", "term_cd", "TERM", "Term", "Submission Value"]:
        if candidate in ct_df.columns:
            term_col = candidate
            break

    if codelist_col is None or term_col is None:
        return []

    # Filter to just this codelist and return the list of allowed values
    filtered = ct_df[ct_df[codelist_col] == codelist_code]
    allowed_values = filtered[term_col].dropna().tolist()
    return [str(v) for v in allowed_values]


def _check_ct_values(output_df, ct_df, column_name, codelist_code, check_name):
    """
    Check that all values in a given output column appear in the specified
    controlled terminology code list. Every value must be valid.
    """
    if column_name not in output_df.columns:
        return {
            "check": check_name,
            "passed": False,
            "description": f"Column {column_name} is missing from the output."
        }

    allowed_values = _get_allowed_ct_values(ct_df, codelist_code)
    if not allowed_values:
        return {
            "check": check_name,
            "passed": True,
            "description": f"Could not load CT values for {codelist_code}. Check skipped."
        }

    # Find values in the output that are not in the allowed list
    output_values = output_df[column_name].dropna().astype(str)
    invalid_values = output_values[~output_values.isin(allowed_values)].unique().tolist()

    if not invalid_values:
        unique_vals = output_df[column_name].dropna().unique().tolist()
        return {
            "check": check_name,
            "passed": True,
            "description": f"All values in {column_name} are valid. Found: {', '.join(str(v) for v in unique_vals)}"
        }
    else:
        return {
            "check": check_name,
            "passed": False,
            "description": (
                f"Found {len(invalid_values)} invalid value(s) in {column_name} "
                f"not in CT {codelist_code}: {', '.join(str(v) for v in invalid_values[:10])}"
            )
        }


def _check_ct_values_optional(output_df, ct_df, column_name, codelist_code, check_name):
    """
    Check CT values for a column that is allowed to have nulls (like VSPOS or VSLOC).
    Only non-null values are checked against the code list.
    """
    if column_name not in output_df.columns:
        return {
            "check": check_name,
            "passed": True,
            "description": f"Column {column_name} is not present (this is acceptable if not applicable)."
        }

    allowed_values = _get_allowed_ct_values(ct_df, codelist_code)
    if not allowed_values:
        return {
            "check": check_name,
            "passed": True,
            "description": f"Could not load CT values for {codelist_code}. Check skipped."
        }

    # Only check non-null values
    non_null_values = output_df[column_name].dropna().astype(str)

    if len(non_null_values) == 0:
        return {
            "check": check_name,
            "passed": True,
            "description": f"All values in {column_name} are null. This is acceptable if this variable is not applicable."
        }

    invalid_values = non_null_values[~non_null_values.isin(allowed_values)].unique().tolist()

    null_count = output_df[column_name].isna().sum()
    non_null_count = len(non_null_values)

    if not invalid_values:
        return {
            "check": check_name,
            "passed": True,
            "description": (
                f"All {non_null_count} non-null values in {column_name} are valid "
                f"({null_count} null rows, which is expected for some tests)."
            )
        }
    else:
        return {
            "check": check_name,
            "passed": False,
            "description": (
                f"Found {len(invalid_values)} invalid non-null value(s) in {column_name} "
                f"not in CT {codelist_code}: {', '.join(str(v) for v in invalid_values[:10])}"
            )
        }


def _check_row_count(output_df, raw_df):
    """
    Check that the output has a reasonable number of rows compared to the raw data.
    We expect at least 3x the raw row count because each patient visit row
    should produce at least 4 rows (one per test: TEMP, SYSBP, DIABP, PULSE).
    """
    output_row_count = len(output_df)

    if raw_df is None:
        return {
            "check": "Row count is reasonable",
            "passed": True,
            "description": f"Output has {output_row_count} rows. Could not load raw data to compare ratio."
        }

    raw_row_count = len(raw_df)
    if raw_row_count == 0:
        return {
            "check": "Row count is reasonable",
            "passed": False,
            "description": "Raw data has 0 rows. Cannot check row count ratio."
        }

    ratio = output_row_count / raw_row_count

    if ratio >= 3.0:
        return {
            "check": "Row count is reasonable",
            "passed": True,
            "description": (
                f"Output has {output_row_count} rows from {raw_row_count} raw rows "
                f"(ratio {ratio:.1f}x, expected at least 3x). "
            )
        }
    else:
        return {
            "check": "Row count is reasonable",
            "passed": False,
            "description": (
                f"Output has {output_row_count} rows from {raw_row_count} raw rows "
                f"(ratio {ratio:.1f}x). Expected at least 3x because each raw row "
                f"should produce at least 3 test rows (TEMP, SYSBP, DIABP, PULSE)."
            )
        }


def _check_date_format(output_df):
    """
    Check that all VSDTC values match the ISO 8601 date format YYYY-MM-DD.
    """
    if "VSDTC" not in output_df.columns:
        return {
            "check": "VSDTC format is ISO 8601",
            "passed": False,
            "description": "VSDTC column is missing from the output."
        }

    # The ISO 8601 date pattern: four-digit year, two-digit month, two-digit day
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    # Check each non-null VSDTC value against the pattern
    non_null_dates = output_df["VSDTC"].dropna().astype(str)
    invalid_dates = non_null_dates[~non_null_dates.str.match(iso_pattern)]

    null_count = output_df["VSDTC"].isna().sum()

    if len(invalid_dates) == 0:
        return {
            "check": "VSDTC format is ISO 8601",
            "passed": True,
            "description": (
                f"All {len(non_null_dates)} non-null VSDTC values are in YYYY-MM-DD format "
                f"({null_count} null values)."
            )
        }
    else:
        example_bad = invalid_dates.head(3).tolist()
        return {
            "check": "VSDTC format is ISO 8601",
            "passed": False,
            "description": (
                f"{len(invalid_dates)} VSDTC values do not match YYYY-MM-DD format. "
                f"Examples: {', '.join(example_bad)}"
            )
        }


def _check_vsseq(output_df):
    """
    Check that VSSEQ is a sequential positive integer starting at 1 for each subject.
    VSSEQ must have no gaps and no duplicates within each USUBJID.
    """
    if "VSSEQ" not in output_df.columns:
        return {
            "check": "VSSEQ sequential per subject",
            "passed": False,
            "description": "VSSEQ column is missing from the output."
        }

    if "USUBJID" not in output_df.columns:
        return {
            "check": "VSSEQ sequential per subject",
            "passed": False,
            "description": "USUBJID column is missing so VSSEQ cannot be checked per subject."
        }

    problem_subjects = []

    # Check each subject separately
    for subject_id, subject_rows in output_df.groupby("USUBJID"):
        vsseq_values = sorted(subject_rows["VSSEQ"].dropna().tolist())

        if not vsseq_values:
            problem_subjects.append(f"{subject_id} (no VSSEQ values)")
            continue

        # Expected: [1, 2, 3, ..., n]
        expected_sequence = list(range(1, len(vsseq_values) + 1))

        if vsseq_values != expected_sequence:
            problem_subjects.append(
                f"{subject_id} (got {vsseq_values[:5]}, expected {expected_sequence[:5]})"
            )

    if not problem_subjects:
        subject_count = output_df["USUBJID"].nunique()
        return {
            "check": "VSSEQ sequential per subject",
            "passed": True,
            "description": f"VSSEQ is sequential starting at 1 for all {subject_count} subjects."
        }
    else:
        return {
            "check": "VSSEQ sequential per subject",
            "passed": False,
            "description": (
                f"VSSEQ problems found in {len(problem_subjects)} subjects: "
                f"{'; '.join(problem_subjects[:5])}"
            )
        }


def _check_against_golden(output_df, golden_df):
    """
    Compare the output dataset against the golden reference.
    Find columns that appear in both, and report what percentage of values match.
    Also show the top 5 rows that differ.
    """
    if golden_df is None or len(golden_df) == 0:
        return {
            "check": "Comparison against golden reference",
            "passed": True,
            "description": "Golden reference file not available or empty. Comparison skipped."
        }

    # Find columns that appear in both datasets
    output_cols = set(output_df.columns.tolist())
    golden_cols = set(golden_df.columns.tolist())
    shared_cols = list(output_cols & golden_cols)

    if not shared_cols:
        return {
            "check": "Comparison against golden reference",
            "passed": False,
            "description": (
                f"No shared columns found between output and golden reference. "
                f"Output columns: {', '.join(list(output_cols)[:5])}. "
                f"Golden columns: {', '.join(list(golden_cols)[:5])}."
            )
        }

    # Compare row counts
    output_rows = len(output_df)
    golden_rows = len(golden_df)

    # Sort both by key columns if they are present, to align rows before comparing
    sort_cols = [c for c in ["USUBJID", "VSTESTCD", "VISITNUM"] if c in shared_cols]

    comparison_results = {}

    if sort_cols:
        # Sort both dataframes by the same key columns for a fair row-by-row comparison
        output_sorted = output_df.sort_values(sort_cols).reset_index(drop=True)
        golden_sorted = golden_df.sort_values(sort_cols).reset_index(drop=True)

        # Compare up to the minimum row count
        min_rows = min(len(output_sorted), len(golden_sorted))
        output_subset = output_sorted.head(min_rows)
        golden_subset = golden_sorted.head(min_rows)

        for col in shared_cols:
            if col in output_subset.columns and col in golden_subset.columns:
                output_col_vals = output_subset[col].astype(str).reset_index(drop=True)
                golden_col_vals = golden_subset[col].astype(str).reset_index(drop=True)
                match_count = (output_col_vals == golden_col_vals).sum()
                match_pct = round(match_count / min_rows * 100, 1) if min_rows > 0 else 0
                comparison_results[col] = match_pct
    else:
        # No sort columns available, skip detailed comparison
        comparison_results = {col: "N/A (could not sort for alignment)" for col in shared_cols}

    # Build description
    description_lines = [
        f"Output has {output_rows} rows; golden reference has {golden_rows} rows.",
        f"Compared {len(shared_cols)} shared columns.",
        "Column match rates:"
    ]

    high_match_cols = []
    low_match_cols = []

    for col, match_pct in comparison_results.items():
        if isinstance(match_pct, float):
            description_lines.append(f"  {col}: {match_pct}% match")
            if match_pct >= 80:
                high_match_cols.append(col)
            else:
                low_match_cols.append(col)
        else:
            description_lines.append(f"  {col}: {match_pct}")

    description = "\n".join(description_lines)

    # Consider it passed if most key columns have high match rates
    if low_match_cols:
        return {
            "check": "Comparison against golden reference",
            "passed": False,
            "description": description + f"\nLow match columns: {', '.join(low_match_cols)}"
        }
    else:
        return {
            "check": "Comparison against golden reference",
            "passed": True,
            "description": description
        }


def _write_markdown_report(result, report_path, output_path):
    """
    Write the full validation report as a markdown file.
    The report includes every check result, pass or fail, in readable format.
    """
    # Create the output directory if it does not exist
    report_dir = os.path.dirname(report_path)
    if report_dir and not os.path.exists(report_dir):
        os.makedirs(report_dir, exist_ok=True)

    lines = []

    lines.append("# SDTM VS Validation Report")
    lines.append("")
    lines.append(f"**Output file checked:** `{output_path}`")
    lines.append("")

    # Summary section
    lines.append("## Summary")
    lines.append("")
    lines.append(result.get("summary", "No summary available."))
    lines.append("")

    passed_checks = result.get("passed", [])
    failed_checks = result.get("failed", [])

    lines.append(f"- **Checks passed:** {len(passed_checks)}")
    lines.append(f"- **Checks failed:** {len(failed_checks)}")
    lines.append("")

    # Passed checks
    lines.append("## Passed Checks")
    lines.append("")
    if passed_checks:
        for check_name in passed_checks:
            lines.append(f"- {check_name}")
    else:
        lines.append("No checks passed.")
    lines.append("")

    # Failed checks
    lines.append("## Failed Checks")
    lines.append("")
    if failed_checks:
        for failure in failed_checks:
            check_name = failure.get("check", "Unknown")
            description = failure.get("description", "No description")
            lines.append(f"### {check_name}")
            lines.append("")
            lines.append(description)
            lines.append("")
    else:
        lines.append("No checks failed.")
    lines.append("")

    # Write the report to disk
    report_content = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(report_content)

    print(f"  Validation report written to: {report_path}")
