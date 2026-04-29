
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
