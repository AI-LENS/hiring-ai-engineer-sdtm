
library(dplyr)

raw_data <- read.csv("C:/Users/SAI SANTOSH/OneDrive/Pictures/Desktop/AI_LENS_CODING/input/vs_raw.csv")
ct <- read.csv("C:/Users/SAI SANTOSH/OneDrive/Pictures/Desktop/AI_LENS_CODING/input/sdtm_ct.csv")


ds_TEMP <- raw_data %>%
  filter(!is.na(IT.TEMP)) %>%
  mutate(
    STUDYID = "STUDY1",
    USUBJID = paste0("STUDY1-", PATNUM),
    VSTESTCD = "TEMP",
    VSTEST = "Temperature",
    VSORRES = IT.TEMP,
    VSORRESU = "F",
    VSSTRESN = (IT.TEMP - 32) * 5/9,
    VSSTRESU = "C",
    VSPOS = toupper(SUBPOS)
  )

ds_SYSBP <- raw_data %>%
  filter(!is.na(SYS_BP)) %>%
  mutate(
    STUDYID = "STUDY1",
    USUBJID = paste0("STUDY1-", PATNUM),
    VSTESTCD = "SYSBP",
    VSTEST = "Systolic Blood Pressure",
    VSORRES = SYS_BP,
    VSORRESU = "mmHg",
    VSSTRESN = SYS_BP,
    VSSTRESU = "mmHg",
    VSPOS = toupper(SUBPOS)
  )

ds_DIABP <- raw_data %>%
  filter(!is.na(DIA_BP)) %>%
  mutate(
    STUDYID = "STUDY1",
    USUBJID = paste0("STUDY1-", PATNUM),
    VSTESTCD = "DIABP",
    VSTEST = "Diastolic Blood Pressure",
    VSORRES = DIA_BP,
    VSORRESU = "mmHg",
    VSSTRESN = DIA_BP,
    VSSTRESU = "mmHg",
    VSPOS = toupper(SUBPOS)
  )

ds_PULSE <- raw_data %>%
  filter(!is.na(PULSE)) %>%
  mutate(
    STUDYID = "STUDY1",
    USUBJID = paste0("STUDY1-", PATNUM),
    VSTESTCD = "PULSE",
    VSTEST = "Pulse Rate",
    VSORRES = PULSE,
    VSORRESU = "beats/min",
    VSSTRESN = PULSE,
    VSSTRESU = "beats/min",
    VSPOS = toupper(SUBPOS)
  )


vs <- bind_rows(ds_TEMP,
ds_SYSBP,
ds_DIABP,
ds_PULSE)

vs <- vs %>%
  arrange(USUBJID, VSTESTCD) %>%
  group_by(USUBJID) %>%
  mutate(VSSEQ = row_number()) %>%
  ungroup()

write.csv(vs, "C:/Users/SAI SANTOSH/OneDrive/Pictures/Desktop/AI_LENS_CODING/output/vs.csv", row.names = FALSE)
