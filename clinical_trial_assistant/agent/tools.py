import subprocess
import pandas as pd
import os
import re

def read_csv_metadata(file_object):
    """Saves files to output/ and returns metadata for the agent[cite: 13, 20]."""
    df = pd.read_csv(file_object)
    if not os.path.exists("output"):
        os.makedirs("output")
            
    # Standardize filenames for the R script[cite: 4, 20]
    filename = "raw_data.csv" if "PATNUM" in df.columns else "ct_data.csv"
    df.to_csv(f"output/{filename}", index=False)
    
    if hasattr(file_object, 'seek'):
        file_object.seek(0)
    return f"Columns: {df.columns.tolist()}\nSample Data:\n{df.head(2).to_string()}"

def execute_r_script(script_content: str):
    """Cleans conversational text and runs the R script[cite: 4, 20]."""
    # Extract only the code between backticks[cite: 20]
    match = re.search(r"```[rR]?\s*(.*?)\s*```", script_content, re.DOTALL)
    clean_script = match.group(1).strip() if match else script_content.strip()

    script_path = "output/generated_map.R"
    with open(script_path, "w") as f:
        f.write(clean_script)
    
    # Execute the R script via subprocess[cite: 4, 8, 20]
    result = subprocess.run(["Rscript", script_path], capture_output=True, text=True)
    
    if result.returncode != 0:
        return f"Error: {result.stderr}"
    
    return "Success: SDTM VS generated at output/vs.csv"