import subprocess
import os

R_PATH = r"C:\Program Files\R\R-4.6.0\bin\Rscript.exe"

def generate_r_script():
    base = os.getcwd()

    raw_path = os.path.join(base, "data", "vs_raw.csv").replace("\\", "/")
    ct_path  = os.path.join(base, "data", "sdtm_ct.csv").replace("\\", "/")
    out_path = os.path.join(base, "output", "vs.csv").replace("\\", "/")

    script = f"""
library(dplyr)

raw <- read.csv("{raw_path}")
ct  <- read.csv("{ct_path}")

vs_list <- list()

# ---- TEMP ----
temp_col <- names(raw)[grepl("TEMP", names(raw), ignore.case = TRUE)][1]

if (!is.na(temp_col)) {{
  temp <- data.frame(
    STUDYID = "STUDY1",
    USUBJID = paste0("STUDY1-", raw$PATNUM),
    VSTESTCD = "TEMP",
    VSTEST = "Temperature",
    VSORRES = raw[[temp_col]],
    VSORRESU = "F"
  )
  temp <- temp[!is.na(temp$VSORRES), ]
  vs_list[["TEMP"]] <- temp
}}

# ---- SYSBP ----
sys_col <- names(raw)[grepl("SYS", names(raw), ignore.case = TRUE)][1]

if (!is.na(sys_col)) {{
  sys <- data.frame(
    STUDYID = "STUDY1",
    USUBJID = paste0("STUDY1-", raw$PATNUM),
    VSTESTCD = "SYSBP",
    VSTEST = "Systolic Blood Pressure",
    VSORRES = raw[[sys_col]],
    VSORRESU = "mmHg"
  )
  sys <- sys[!is.na(sys$VSORRES), ]
  vs_list[["SYSBP"]] <- sys
}}

# ---- DIABP ----
dia_col <- names(raw)[grepl("DIA", names(raw), ignore.case = TRUE)][1]

if (!is.na(dia_col)) {{
  dia <- data.frame(
    STUDYID = "STUDY1",
    USUBJID = paste0("STUDY1-", raw$PATNUM),
    VSTESTCD = "DIABP",
    VSTEST = "Diastolic Blood Pressure",
    VSORRES = raw[[dia_col]],
    VSORRESU = "mmHg"
  )
  dia <- dia[!is.na(dia$VSORRES), ]
  vs_list[["DIABP"]] <- dia
}}

# ---- PULSE ----
pulse_col <- names(raw)[grepl("PULSE", names(raw), ignore.case = TRUE)][1]

if (!is.na(pulse_col)) {{
  pulse <- data.frame(
    STUDYID = "STUDY1",
    USUBJID = paste0("STUDY1-", raw$PATNUM),
    VSTESTCD = "PULSE",
    VSTEST = "Pulse Rate",
    VSORRES = raw[[pulse_col]],
    VSORRESU = "beats/min"
  )
  pulse <- pulse[!is.na(pulse$VSORRES), ]
  vs_list[["PULSE"]] <- pulse
}}

# ---- FINAL ----
if (length(vs_list) == 0) {{
  stop("No valid vital signs found")
}}

vs <- bind_rows(vs_list)

write.csv(vs, "{out_path}", row.names = FALSE)
"""

    with open("convert.R", "w") as f:
        f.write(script)


def run_r():
    result = subprocess.run(
        [R_PATH, "convert.R"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(result.stderr)