"""
agent/tools.py

All LangChain tools are defined here using the @tool decorator.
Each tool does one specific job and returns a plain string or dictionary
so the LLM can read and understand the result.

These tools are the hands of the agent -- they interact with the file system,
run R scripts, and read data. The LLM brain decides when and how to use them.
"""

import os
import subprocess
import shutil
import pandas as pd

from langchain_core.tools import tool # type: ignore


@tool
def read_raw_data(file_path: str) -> str:
    """
    Read a raw CSV file and return its column names and first 3 rows as a readable string.
    This helps the LLM understand the structure and content of the raw data
    before deciding how to map columns to SDTM variables.

    Args:
        file_path: The path to the CSV file to read.

    Returns:
        A string showing column names and sample rows, or an error message.
    """
    try:
        # Check that the file actually exists before trying to read it
        if not os.path.exists(file_path):
            return f"ERROR: File not found at path: {file_path}"

        # Read the CSV file into a pandas DataFrame
        dataframe = pd.read_csv(file_path)

        # Get the list of column names as a comma-separated string
        column_names = ", ".join(dataframe.columns.tolist())

        # Get the total number of rows
        row_count = len(dataframe)

        # Get the first 3 rows as a string, using a tab separator for readability
        sample_rows = dataframe.head(3).to_string(index=False)

        # Build a readable summary string
        result = (
            f"File: {file_path}\n"
            f"Total rows: {row_count}\n"
            f"Column names: {column_names}\n"
            f"\nFirst 3 rows:\n{sample_rows}"
        )

        return result

    except pd.errors.EmptyDataError:
        return f"ERROR: The file at {file_path} is empty or has no readable content."

    except Exception as error:
        return f"ERROR reading file {file_path}: {str(error)}"


@tool
def read_controlled_terminology(file_path: str) -> str:
    """
    Read the SDTM controlled terminology CSV and return a grouped summary
    showing each code list and its allowed term values.
    This helps the LLM know which values are valid for each SDTM variable.

    The CT file is expected to have columns like:
    codelist_code, codelist_name, term_value, term_label (or similar)

    Args:
        file_path: The path to the controlled terminology CSV file.

    Returns:
        A string summarizing each code list and its allowed values, or an error message.
    """
    try:
        # Check that the file exists
        if not os.path.exists(file_path):
            return f"ERROR: CT file not found at path: {file_path}"

        # Read the controlled terminology file
        ct_df = pd.read_csv(file_path)

        # Show the column names so we can confirm what we are working with
        columns_found = ", ".join(ct_df.columns.tolist())

        # Build the summary output, starting with a header
        summary_lines = [
            f"Controlled Terminology file: {file_path}",
            f"Columns found: {columns_found}",
            f"Total rows: {len(ct_df)}",
            "",
            "Code list summary:",
        ]

        # Try to find the column that holds the code list identifier
        # Different versions of the CT file may use different column names
        codelist_col = None
        for candidate in ["codelist_code", "codelist_cd", "CODELIST", "Codelist Code"]:
            if candidate in ct_df.columns:
                codelist_col = candidate
                break

        # Try to find the column that holds the allowed term value
        term_col = None
        for candidate in ["term_value", "term_cd", "TERM", "Term", "Submission Value"]:
            if candidate in ct_df.columns:
                term_col = candidate
                break

        # Try to find the column that holds the human-readable term label
        label_col = None
        for candidate in ["term_label", "DECODED_VALUE", "Preferred Term", "NCI Preferred Term"]:
            if candidate in ct_df.columns:
                label_col = candidate
                break

        # If we could not find the expected columns, just show a raw sample
        if codelist_col is None or term_col is None:
            summary_lines.append(
                "WARNING: Expected columns not found. Showing raw sample instead."
            )
            summary_lines.append(ct_df.head(10).to_string(index=False))
            return "\n".join(summary_lines)

        # Group by code list and list all allowed term values
        grouped = ct_df.groupby(codelist_col)

        for codelist_code, group in grouped:
            # Get the list of allowed term values for this code list
            term_values = group[term_col].dropna().tolist()
            term_values_str = ", ".join(str(v) for v in term_values[:20])

            # If there are more than 20 terms, add a note
            if len(term_values) > 20:
                term_values_str += f" ... ({len(term_values)} total)"

            # Get the code list name if available
            if label_col and label_col in group.columns:
                codelist_label = group[label_col].iloc[0] if not group[label_col].empty else ""
                summary_lines.append(
                    f"  {codelist_code}: {codelist_label} -- allowed values: {term_values_str}"
                )
            else:
                summary_lines.append(
                    f"  {codelist_code}: allowed values: {term_values_str}"
                )

        return "\n".join(summary_lines)

    except Exception as error:
        return f"ERROR reading controlled terminology file {file_path}: {str(error)}"


@tool
def run_r_script(script_path: str) -> dict:
    """Runs an R script using Rscript and returns the output and any errors."""

    # Use the full path to Rscript because Windows PATH may not include R
    rscript_path = r"C:\Program Files\R\R-4.6.0\bin\Rscript.exe"

    # Check if Rscript actually exists at that path before trying to run it
    import os
    if not os.path.exists(rscript_path):
        return {
            "success": False,
            "output": "",
            "error": f"Rscript not found at {rscript_path}. Please check your R installation."
        }

    # Run the R script and capture all output
    result = subprocess.run(
        [rscript_path, script_path],
        capture_output=True,
        text=True
    )

    # Return success or failure with the full output
    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr
    }

@tool
def check_output_exists(file_path: str) -> str:
    """
    Check whether an output file exists and contains data.
    Returns a plain English message describing what was found.
    This helps the agent confirm that R produced output before continuing.

    Args:
        file_path: The path to check.

    Returns:
        A string message saying whether the file exists and has data.
    """
    # Check whether the file exists on disk
    if not os.path.exists(file_path):
        return f"File does not exist at path: {file_path}"

    # Check the file size in bytes
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return f"File exists at {file_path} but it is empty (0 bytes). The R script may have failed."

    # If the file is a CSV, try to count the rows for a better report
    if file_path.endswith(".csv"):
        try:
            df = pd.read_csv(file_path)
            row_count = len(df)
            col_count = len(df.columns)
            if row_count == 0:
                return (
                    f"File exists at {file_path} ({file_size} bytes) "
                    f"but the CSV has 0 data rows. The R script ran but produced no output."
                )
            return (
                f"File exists and has data: {file_path} "
                f"({row_count} rows, {col_count} columns, {file_size} bytes)"
            )
        except Exception:
            # If we cannot read it as CSV, at least confirm it is not empty
            return f"File exists at {file_path} ({file_size} bytes) but could not be read as CSV."

    # For non-CSV files, just report the file size
    return f"File exists at {file_path} ({file_size} bytes)"


@tool
def save_r_script(script_path: str, script_content: str) -> str:
    """
    Save an R script to the specified path on disk.
    Creates any parent directories that do not exist yet.
    Returns a confirmation message.

    Args:
        script_path: Where to save the .R file.
        script_content: The full text content of the R script.

    Returns:
        A confirmation message with the path and line count.
    """
    try:
        # Create the parent directory if it does not exist
        parent_directory = os.path.dirname(script_path)
        if parent_directory and not os.path.exists(parent_directory):
            os.makedirs(parent_directory, exist_ok=True)

        # Write the script content to the file
        with open(script_path, "w", encoding="utf-8") as script_file:
            script_file.write(script_content)

        # Count lines for a helpful message
        line_count = len(script_content.splitlines())

        return (
            f"R script saved successfully to: {script_path} "
            f"({line_count} lines)"
        )

    except PermissionError:
        return f"ERROR: Permission denied when trying to save to {script_path}"

    except Exception as error:
        return f"ERROR saving R script to {script_path}: {str(error)}"
