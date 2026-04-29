# agent/r_generator.py

import os
import subprocess

from agent.planner import create_mapping_plan


def generate_r_script(plan):
    """
    Create generated.R file using planner output
    """

    os.makedirs("output", exist_ok=True)

    temp_info = plan.get("TEMP", {})

    raw_column = temp_info.get("raw_column", "IT.TEMP")
    location_column = temp_info.get("location_column", "IT.TEMP_LOC")
    position_column = temp_info.get("position_column", "SUBPOS")

    r_code = f"""
library(sdtm.oak)
library(dplyr)

# Read files
raw_data <- read.csv("data/vs_raw.csv")
study_ct <- read.csv("data/sdtm_ct.csv")

# TEMP mapping only (first version)

final_vs <- raw_data %>%
  mutate(
    STUDYID = "STUDY001",
    USUBJID = paste("STUDY001", PATNUM, sep = "-"),
    VSTESTCD = "TEMP",
    VSTEST = "Temperature",
    VSORRES = {raw_column},
    VSORRESU = "F",
    VSSTRESC = round(({raw_column} - 32) * 5/9, 2),
    VSSTRESU = "C",
    VSPOS = {position_column},
    VSLOC = {location_column}
  ) %>%
  select(
    STUDYID,
    USUBJID,
    VSTESTCD,
    VSTEST,
    VSORRES,
    VSORRESU,
    VSSTRESC,
    VSSTRESU,
    VSPOS,
    VSLOC
  )

write.csv(final_vs, "output/vs.csv", row.names = FALSE)

cat("VS dataset created successfully\\n")
"""

    with open("output/generated.R", "w", encoding="utf-8") as file:
        file.write(r_code)

    print("generated.R created successfully")


def run_r_script():
    """
    Run generated R script using subprocess
    """

    try:
        result = subprocess.run(
            ["Rscript", "output/generated.R"],
            capture_output=True,
            text=True
        )

        print("\nR OUTPUT:\n")
        print(result.stdout)

        if result.stderr:
            print("\nR ERRORS:\n")
            print(result.stderr)

    except Exception as error:
        print("Failed to run R script:")
        print(error)


if __name__ == "__main__":
    plan = create_mapping_plan()

    if plan:
        generate_r_script(plan)
        run_r_script()
    else:
        print("Planner failed. Cannot generate R script.")