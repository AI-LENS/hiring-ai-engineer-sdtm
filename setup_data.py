"""
setup_data.py

This script downloads all data files that the SDTM VS agent needs to run.
Run it once before running run.py.

Usage:
    python setup_data.py

It does not import anything from the agent folder.
It only uses standard libraries plus kagglehub and requests.
"""

import os
import shutil
import pathlib
import requests
import kagglehub # type: ignore


# The local folder where all downloaded data will be stored
DATA_FOLDER = pathlib.Path("data")


def create_data_folder():
    """
    Create the data folder if it does not already exist.
    This is where all downloaded files will be saved.
    """
    if not DATA_FOLDER.exists():
        DATA_FOLDER.mkdir(parents=True)
        print(f"Created folder: {DATA_FOLDER.resolve()}")
    else:
        print(f"Data folder already exists: {DATA_FOLDER.resolve()}")


def download_raw_vitals():
    """
    Download the pharmaverse raw vital signs dataset from Kaggle using kagglehub.
    The dataset is 'patrickward/pharmaverse-datasets'.
    We look for a file that contains raw vital signs data (vs_raw).
    The file is saved as data/vs_raw.csv.
    """
    print("\nStep 2 -- Downloading raw vital signs data from Kaggle...")

    try:
        # Download the dataset. kagglehub returns the local folder path.
        dataset_path = kagglehub.dataset_download("patrickward/pharmaverse-datasets")
        print(f"  Dataset downloaded to: {dataset_path}")

        # Walk through all files in the downloaded folder to find the vs_raw file.
        # The exact filename may vary so we search for any CSV with 'vs_raw' in the name.
        found_file = None
        all_csv_files = []

        for root, dirs, files in os.walk(dataset_path):
            for filename in files:
                if filename.endswith(".csv"):
                    full_path = os.path.join(root, filename)
                    all_csv_files.append(full_path)
                    # Check for vs_raw in the filename (case insensitive)
                    if "vs_raw" in filename.lower() or "vs_raw" in full_path.lower():
                        found_file = full_path
                        break
            if found_file:
                break

        # If we did not find a vs_raw file by name, look for any file with 'vs' in the name
        # that also has typical vital signs columns
        if not found_file:
            print("  Could not find a file named vs_raw. Searching for VS-related CSVs...")
            for csv_path in all_csv_files:
                filename_lower = os.path.basename(csv_path).lower()
                if "vs" in filename_lower and "raw" in filename_lower:
                    found_file = csv_path
                    break

        # If still not found, try any file with 'vs' in name
        if not found_file:
            for csv_path in all_csv_files:
                filename_lower = os.path.basename(csv_path).lower()
                if filename_lower.startswith("vs"):
                    found_file = csv_path
                    print(f"  Found candidate VS file: {csv_path}")
                    break

        # Last resort: list all CSV files and let the user know
        if not found_file and all_csv_files:
            print("  WARNING: Could not find vs_raw.csv by name.")
            print("  All CSV files found in the dataset:")
            for f in all_csv_files:
                print(f"    {f}")
            # Use the first CSV as a fallback
            found_file = all_csv_files[0]
            print(f"  Using first available CSV as fallback: {found_file}")

        if found_file:
            destination = DATA_FOLDER / "vs_raw.csv"
            shutil.copy2(found_file, destination)
            print(f"  Raw VS data saved to: {destination.resolve()}")
            return str(destination)
        else:
            print("  ERROR: No CSV files found in the downloaded dataset.")
            print("  Manual fallback: Download vs_raw.csv from the pharmaverse GitHub")
            print("  and place it in the data/ folder manually.")
            return None

    except Exception as error:
        print(f"  ERROR downloading raw vitals from Kaggle: {error}")
        print("  Manual fallback: Visit https://www.kaggle.com/datasets/patrickward/pharmaverse-datasets")
        print("  Download vs_raw.csv and place it in the data/ folder.")
        return None


def download_controlled_terminology():
    """
    Download the SDTM controlled terminology CSV from the pharmaverse GitHub repository.
    This file maps coded values to their allowed terms for each code list.
    It is saved as data/sdtm_ct.csv.
    """
    print("\nStep 3 -- Downloading SDTM controlled terminology from GitHub...")

    ct_url = (
        "https://raw.githubusercontent.com/pharmaverse/sdtm.oak-workshop"
        "/main/datasets/sdtm_ct.csv"
    )

    try:
        response = requests.get(ct_url, timeout=30)
        response.raise_for_status()

        destination = DATA_FOLDER / "sdtm_ct.csv"
        destination.write_bytes(response.content)
        print(f"  Controlled terminology saved to: {destination.resolve()}")
        return str(destination)

    except requests.exceptions.ConnectionError:
        print("  ERROR: Could not connect to GitHub. Check your internet connection.")
        print("  Manual fallback: Download sdtm_ct.csv from:")
        print(f"  {ct_url}")
        print("  and place it in the data/ folder.")
        return None

    except requests.exceptions.HTTPError as error:
        print(f"  ERROR: HTTP error when downloading CT file: {error}")
        print("  Manual fallback: Visit the pharmaverse sdtm.oak-workshop GitHub repository")
        print("  and download datasets/sdtm_ct.csv to the data/ folder.")
        return None

    except Exception as error:
        print(f"  ERROR downloading controlled terminology: {error}")
        return None


def download_golden_reference():
    """
    Download the golden reference SDTM VS dataset from Kaggle using kagglehub.
    This is the expected correct output that the validator will compare against.
    It is saved as data/vs_golden.csv.
    """
    print("\nStep 4 -- Downloading golden reference SDTM VS dataset from Kaggle...")

    try:
        # Download the same pharmaverse dataset - the golden output is in there too
        dataset_path = kagglehub.dataset_download("patrickward/pharmaverse-datasets")
        print(f"  Dataset path: {dataset_path}")

        # Walk through all files looking for the standardized VS dataset.
        # Look for files named vs.csv, vs_golden.csv, pharmaversesdtm_vs.csv etc.
        found_file = None
        all_csv_files = []

        for root, dirs, files in os.walk(dataset_path):
            for filename in files:
                if filename.endswith(".csv"):
                    full_path = os.path.join(root, filename)
                    all_csv_files.append(full_path)

        # Priority search: look for golden or sdtm vs files
        search_patterns = [
            "vs_golden", "golden", "pharmaversesdtm", "sdtm_vs",
            "pharmaverse_sdtm_vs", "vs_sdtm"
        ]

        for pattern in search_patterns:
            for csv_path in all_csv_files:
                if pattern in csv_path.lower():
                    found_file = csv_path
                    print(f"  Found golden reference candidate: {csv_path}")
                    break
            if found_file:
                break

        # If not found with patterns, look for a vs.csv that is NOT vs_raw.csv
        if not found_file:
            for csv_path in all_csv_files:
                filename = os.path.basename(csv_path).lower()
                if filename == "vs.csv" or (
                    "vs" in filename and "raw" not in filename
                ):
                    found_file = csv_path
                    print(f"  Using as golden reference: {csv_path}")
                    break

        if found_file:
            destination = DATA_FOLDER / "vs_golden.csv"
            shutil.copy2(found_file, destination)
            print(f"  Golden reference saved to: {destination.resolve()}")
            return str(destination)
        else:
            print("  WARNING: Could not find a golden reference VS file.")
            print("  All available CSV files:")
            for f in all_csv_files:
                print(f"    {f}")
            print("  The validator will skip the golden comparison check.")

            # Create a minimal placeholder so the validator does not crash
            destination = DATA_FOLDER / "vs_golden.csv"
            placeholder_content = (
                "STUDYID,DOMAIN,USUBJID,VSSEQ,VSTESTCD,VSTEST,"
                "VSORRES,VSORRESU,VSSTRESC,VSSTRESU,VISIT,VISITNUM,VSDTC\n"
            )
            destination.write_text(placeholder_content)
            print(f"  Created empty placeholder at: {destination.resolve()}")
            print("  Replace this file with the real golden reference for full validation.")
            return str(destination)

    except Exception as error:
        print(f"  ERROR downloading golden reference from Kaggle: {error}")
        print("  Manual fallback: Visit https://www.kaggle.com/datasets/patrickward/pharmaverse-datasets")
        print("  Download the standardized VS dataset and save it as data/vs_golden.csv")
        return None


def print_final_summary(vs_raw_path, ct_path, golden_path):
    """
    Print a summary of all files that were downloaded and are ready to use.
    This helps the user confirm that setup completed successfully.
    """
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)

    files_to_check = {
        "Raw VS data      (data/vs_raw.csv)": DATA_FOLDER / "vs_raw.csv",
        "Controlled terms (data/sdtm_ct.csv)": DATA_FOLDER / "sdtm_ct.csv",
        "Golden reference (data/vs_golden.csv)": DATA_FOLDER / "vs_golden.csv",
    }

    all_ready = True
    for label, path in files_to_check.items():
        if path.exists() and path.stat().st_size > 0:
            size_kb = path.stat().st_size / 1024
            print(f"  READY   {label}  ({size_kb:.1f} KB)")
        else:
            print(f"  MISSING {label}")
            all_ready = False

    print()
    if all_ready:
        print("All files are ready. You can now run: python run.py")
    else:
        print("Some files are missing. See the error messages above for manual steps.")
    print("=" * 60)


def main():
    """
    Main function that runs all setup steps in order.
    Each step is independent so a failure in one does not stop the others.
    """
    print("=" * 60)
    print("SDTM VS Agent -- Data Setup")
    print("=" * 60)

    # Step 1: Create the data folder
    print("\nStep 1 -- Creating data folder...")
    create_data_folder()

    # Step 2: Download raw vital signs
    vs_raw_path = download_raw_vitals()

    # Step 3: Download controlled terminology
    ct_path = download_controlled_terminology()

    # Step 4: Download golden reference
    golden_path = download_golden_reference()

    # Step 5: Print final summary
    print_final_summary(vs_raw_path, ct_path, golden_path)


if __name__ == "__main__":
    main()
