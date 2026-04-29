"""
run.py

This is the single entry point for the SDTM VS Agent.
Running "python run.py" does everything: reads raw data, plans mappings,
generates R code, runs it, validates the output, and writes the reports.

Before starting, this script checks that all required data files exist.
If they are missing, it tells the user to run setup_data.py first.
"""

import os
import sys
from dotenv import load_dotenv


def check_required_files(file_paths):
    """
    Check that all required data files exist on disk.
    Returns a list of any files that are missing.

    Args:
        file_paths: A list of file path strings to check.

    Returns:
        A list of file paths that do not exist.
    """
    missing = []
    for path in file_paths:
        if not os.path.exists(path):
            missing.append(path)
    return missing


def main():
    """
    Main entry point that orchestrates the full agent pipeline.
    All file paths are defined here and passed to the planner as arguments
    so nothing is hardcoded deep inside the agent code.
    """

    # --- Define all file paths here so they are easy to find and change ---

    # Input data files (must exist before running)
    raw_data_path = "data/vs_raw.csv"
    ct_path = "data/sdtm_ct.csv"
    golden_path = "data/vs_golden.csv"

    # Output files (created by the agent)
    output_folder = "output"
    output_csv_path = os.path.join(output_folder, "vs.csv")
    output_r_path = os.path.join(output_folder, "generated.R")
    report_path = os.path.join(output_folder, "validation_report.md")

    # --- Step 1: Check that required input files exist ---
    required_files = [raw_data_path, ct_path, golden_path]
    missing_files = check_required_files(required_files)

    if missing_files:
        print()
        print("ERROR: The following required data files are missing:")
        for missing_file in missing_files:
            print(f"  {missing_file}")
        print()
        print("Please run the data setup script first:")
        print("  python setup_data.py")
        print()
        print("That script will download all required data files automatically.")
        sys.exit(1)

    # --- Step 2: Load the .env file and check for the Google API key ---
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not google_api_key:
        print()
        print("ERROR: GOOGLE_API_KEY is not set in your environment.")
        print()
        print("To fix this:")
        print("  1. Copy .env.example to .env")
        print("     cp .env.example .env")
        print("  2. Open .env and add your Google API key:")
        print("     GOOGLE_API_KEY=your_key_here")
        print("  3. Get a free API key at: https://aistudio.google.com/app/apikey")
        print()
        sys.exit(1)

    # --- Step 3: Create the output folder if it does not exist ---
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
        print(f"Created output folder: {output_folder}/")

    # --- Step 4: Run the agent ---
    # Import here so we can show the setup messages before any import errors
    from agent.planner import run_planner

    run_planner(
        raw_path=raw_data_path,
        ct_path=ct_path,
        golden_path=golden_path,
        output_csv_path=output_csv_path,
        output_r_path=output_r_path,
        report_path=report_path
    )

    # --- Step 5: Print the final success message ---
    print()
    print("Agent finished. Output files are ready at:")
    print(f"  vs.csv              at {output_csv_path}")
    print(f"  R script            at {output_r_path}")
    print(f"  Validation report   at {report_path}")
    print()


if __name__ == "__main__":
    main()
