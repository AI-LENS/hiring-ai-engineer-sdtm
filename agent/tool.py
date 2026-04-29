import subprocess
import pandas as pd

# -------------------------
# TOOL 1: mapping (Used in fallback if LLM fails)
# -------------------------
def plan_mapping():
    return ["TEMP", "SYSBP", "DIABP", "PULSE"]


# -------------------------
# TOOL 2: Generate R transformation script (SDTM VS mapping using dplyr + CT)
# -------------------------
def generate_r_script(tests):

    script = """
.libPaths(c(
  "C:/Users/venka/Documents/R/win-library/4.6",
  .libPaths()
))

library(dplyr)

raw_data <- read.csv("data/vs_raw.csv")
ct <- read.csv("data/sdtm_ct.csv")

# -------------------------
# SAFE NORMALIZATION
# -------------------------
raw_data$SUBPOS <- ifelse(is.na(raw_data$SUBPOS), NA, toupper(raw_data$SUBPOS))
raw_data$IT.TEMP_LOC <- ifelse(is.na(raw_data$IT.TEMP_LOC), NA, toupper(raw_data$IT.TEMP_LOC))
ct$collected_value <- toupper(ct$collected_value)

# -------------------------
# TEMP
# -------------------------
temp <- raw_data %>%
  filter(!is.na(IT.TEMP)) %>%
  mutate(
    VSTESTCD = "TEMP",
    VSORRES = IT.TEMP,
    VSORRESU = "F"
  ) %>%
  left_join(
    ct %>%
      filter(codelist_code == "C71148") %>%
      select(collected_value, term_value_pos = term_value),
    by = c("SUBPOS" = "collected_value")
  ) %>%
  mutate(VSPOS = coalesce(term_value_pos, SUBPOS)) %>%
  select(-term_value_pos) %>%
  left_join(
    ct %>%
      filter(codelist_code == "C74456") %>%
      select(collected_value, term_value_loc = term_value),
    by = c("IT.TEMP_LOC" = "collected_value")
  ) %>%
  mutate(VSLOC = coalesce(term_value_loc, IT.TEMP_LOC)) %>%
  select(-term_value_loc)

# -------------------------
# SYSBP
# -------------------------
sysbp <- raw_data %>%
  filter(!is.na(SYS_BP)) %>%
  mutate(
    VSTESTCD = "SYSBP",
    VSORRES = SYS_BP,
    VSORRESU = "mmHg",
    VSLOC = NA_character_
  ) %>%
  left_join(
    ct %>%
      filter(codelist_code == "C71148") %>%
      select(collected_value, term_value_pos = term_value),
    by = c("SUBPOS" = "collected_value")
  ) %>%
  mutate(VSPOS = coalesce(term_value_pos, SUBPOS)) %>%
  select(-term_value_pos)

# -------------------------
# DIABP
# -------------------------
diabp <- raw_data %>%
  filter(!is.na(DIA_BP)) %>%
  mutate(
    VSTESTCD = "DIABP",
    VSORRES = DIA_BP,
    VSORRESU = "mmHg",
    VSLOC = NA_character_
  ) %>%
  left_join(
    ct %>%
      filter(codelist_code == "C71148") %>%
      select(collected_value, term_value_pos = term_value),
    by = c("SUBPOS" = "collected_value")
  ) %>%
  mutate(VSPOS = coalesce(term_value_pos, SUBPOS)) %>%
  select(-term_value_pos)

# -------------------------
# PULSE
# -------------------------
pulse <- raw_data %>%
  filter(!is.na(PULSE)) %>%
  mutate(
    VSTESTCD = "PULSE",
    VSORRES = PULSE,
    VSORRESU = "beats/min",
    VSLOC = NA_character_
  ) %>%
  left_join(
    ct %>%
      filter(codelist_code == "C71148") %>%
      select(collected_value, term_value_pos = term_value),
    by = c("SUBPOS" = "collected_value")
  ) %>%
  mutate(VSPOS = coalesce(term_value_pos, SUBPOS)) %>%
  select(-term_value_pos)

# -------------------------
# COMBINE
# -------------------------
vs <- bind_rows(temp, sysbp, diabp, pulse)

# -------------------------
# FINAL SDTM STRUCTURE
# -------------------------
vs <- vs %>%
  mutate(
    STUDYID = STUDY,
    DOMAIN = "VS",
    USUBJID = paste0("01-", PATNUM),
    VSSEQ = row_number(),

    VSDTC = as.Date(VTLD, format="%d-%b-%Y"),

    VSTEST = case_when(
      VSTESTCD == "SYSBP" ~ "Systolic Blood Pressure",
      VSTESTCD == "DIABP" ~ "Diastolic Blood Pressure",
      VSTESTCD == "PULSE" ~ "Pulse Rate",
      VSTESTCD == "TEMP" ~ "Temperature"
    ),

    VSSTRESC = VSORRES,
    VSSTRESN = as.numeric(VSORRES),
    VSSTRESU = VSORRESU,

    VISIT = INSTANCE,
    VISITNUM = as.numeric(factor(INSTANCE, levels = unique(INSTANCE)))
  ) %>%

  select(
    STUDYID, DOMAIN, USUBJID, VSSEQ,
    VSTESTCD, VSTEST, VSPOS, VSLOC,
    VSORRES, VSORRESU,
    VSSTRESC, VSSTRESN, VSSTRESU,
    VISIT, VISITNUM, VSDTC
  )

write.csv(vs, "output/vs.csv", row.names = FALSE)
"""

    return script

# -------------------------
# TOOL 3: run R
# -------------------------
def run_r_script():
    subprocess.run(["Rscript", "output/generated.R"], check=True)


# -------------------------
# TOOL 4: validation
# -------------------------
def validate():

    df = pd.read_csv("output/vs.csv")
    golden = pd.read_csv("data/vs_golden.csv")
    ct = pd.read_csv("data/sdtm_ct.csv")

    report = []

    # -------------------------
    # Row count
    # -------------------------
    report.append(f"Generated rows: {len(df)}")
    report.append(f"Golden rows: {len(golden)}")

    if len(df) < len(golden) * 0.7:
        report.append("⚠️ Row count too low (possible missing mappings)")

    # -------------------------
    # Column check
    # -------------------------
    missing_cols = set(golden.columns) - set(df.columns)
    extra_cols = set(df.columns) - set(golden.columns)

    if missing_cols:
        report.append(f"Missing columns: {missing_cols}")
    if extra_cols:
        report.append(f"Extra columns: {extra_cols}")

    # -------------------------
    # Required SDTM variables
    # -------------------------
    required = [
        "STUDYID","DOMAIN","USUBJID","VSTESTCD",
        "VSORRES","VSORRESU","VSSTRESC","VSSTRESU"
    ]

    missing_required = [c for c in required if c not in df.columns]
    if missing_required:
        report.append(f"❌ Missing required columns: {missing_required}")
    else:
        report.append("✔ Required columns present")

    # -------------------------
    # CT VALIDATION
    # -------------------------
    report.append("\nCT Validation:")

    def check_ct(column, code):
        if column not in df.columns:
            return f"{column} not present"

        allowed = ct[ct["codelist_code"] == code]["term_value"].dropna().unique()
        invalid = df[~df[column].isin(allowed) & df[column].notna()]

        return f"{column}: {len(invalid)} invalid values"

    report.append(check_ct("VSPOS", "C71148"))
    report.append(check_ct("VSLOC", "C74456"))
    report.append(check_ct("VSORRESU", "C66770"))

    # -------------------------
    # Basic sanity checks
    # -------------------------
    if "VSORRES" in df.columns:
        nulls = df["VSORRES"].isna().sum()
        report.append(f"Missing VSORRES values: {nulls}")

    if "USUBJID" in df.columns:
        unique_subj = df["USUBJID"].nunique()
        report.append(f"Unique subjects: {unique_subj}")

    # -------------------------
    # Write report
    # -------------------------
    with open("output/validation_report.txt", "w", encoding="utf-8") as f:
        for r in report:
            f.write(r + "\n")

    print("\n Validation Report:")
    for r in report:
        print(r)