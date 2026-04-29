library(dplyr)

# Ensure output folder exists
dir.create("output", showWarnings = FALSE)

# Read raw data
vs_raw <- read.csv("vitals_raw_data.csv")

# Create STUDYID and USUBJID
vs_raw <- vs_raw %>%
  mutate(
    STUDYID = "STUDY1",
    USUBJID = paste(STUDYID, PATNUM, sep = "-")
  )

# ---------------------------
# TEMP
# ---------------------------
vs_temp <- vs_raw %>%
  filter(!is.na(TEMP)) %>%
  mutate(
    VSTESTCD = "TEMP",
    VSORRES = TEMP,
    VSORRESU = "C",
    VSSTRESC = TEMP,
    VSSTRESU = "C",
    VSPOS = ifelse(is.na(SUBPOS), "UNKNOWN", SUBPOS),
    VSLOC = TEMPLOC
  )

# ---------------------------
# SYSBP
# ---------------------------
vs_sysbp <- vs_raw %>%
  filter(!is.na(SYS_BP)) %>%
  mutate(
    VSTESTCD = "SYSBP",
    VSORRES = SYS_BP,
    VSORRESU = "mmHg",
    VSSTRESC = SYS_BP,
    VSSTRESU = "mmHg",
    VSPOS = ifelse(is.na(SUBPOS), "UNKNOWN", SUBPOS),
    VSLOC = LOC
  )

# ---------------------------
# DIABP
# ---------------------------
vs_diabp <- vs_raw %>%
  filter(!is.na(DIA_BP)) %>%
  mutate(
    VSTESTCD = "DIABP",
    VSORRES = DIA_BP,
    VSORRESU = "mmHg",
    VSSTRESC = DIA_BP,
    VSSTRESU = "mmHg",
    VSPOS = ifelse(is.na(SUBPOS), "UNKNOWN", SUBPOS),
    VSLOC = LOC
  )

# ---------------------------
# PULSE
# ---------------------------
vs_pulse <- vs_raw %>%
  filter(!is.na(PULSE)) %>%
  mutate(
    VSTESTCD = "PULSE",
    VSORRES = PULSE,
    VSORRESU = "beats/min",
    VSSTRESC = PULSE,
    VSSTRESU = "beats/min",
    VSPOS = ifelse(is.na(SUBPOS), "UNKNOWN", SUBPOS),
    VSLOC = LOC
  )

# ---------------------------
# Combine all tests
# ---------------------------
vs <- bind_rows(vs_temp, vs_sysbp, vs_diabp, vs_pulse)

# Select final SDTM columns
vs <- vs %>%
  select(
    STUDYID,
    USUBJID,
    VSTESTCD,
    VSORRES,
    VSORRESU,
    VSSTRESC,
    VSSTRESU,
    VSPOS,
    VSLOC
  )

# Write output
write.csv(vs, "output/vs.csv", row.names = FALSE)

cat("✅ SDTM VS dataset created: output/vs.csv\n")