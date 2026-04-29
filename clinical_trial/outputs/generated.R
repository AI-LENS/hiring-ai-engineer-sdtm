
library(sdtm.oak)
library(dplyr)

# Load data
raw_data <- read.csv("../vs_raw.csv")

# 1. Prepare ID variables
raw_id <- generate_oak_id_vars(raw_data, pat_var = "PATNUM", raw_src = "EDC")

# 2. Create measurement pipelines
all_tests <- list()

# Mapping for IT.TEMP
all_tests[["IT.TEMP"]] <- raw_id %>%
  mutate(VSTESTCD = "IT.TEMP") %>%
  mutate(VSTEST = "Temperature") %>%
  mutate(VSORRES = as.character(IT.TEMP))

# Mapping for IT.TEMP_LOC
all_tests[["IT.TEMP_LOC"]] <- raw_id %>%
  mutate(VSTESTCD = "IT.TEMP_LOC") %>%
  mutate(VSTEST = "Temperature Location") %>%
  mutate(VSORRES = as.character(IT.TEMP_LOC))

# Mapping for BP.SYS
all_tests[["BP.SYS"]] <- raw_id %>%
  mutate(VSTESTCD = "BP.SYS") %>%
  mutate(VSTEST = "Systolic Blood Pressure") %>%
  mutate(VSORRES = as.character(SYS_BP))

# Mapping for BP.DIA
all_tests[["BP.DIA"]] <- raw_id %>%
  mutate(VSTESTCD = "BP.DIA") %>%
  mutate(VSTEST = "Diastolic Blood Pressure") %>%
  mutate(VSORRES = as.character(DIA_BP))

# Mapping for PULSE
all_tests[["PULSE"]] <- raw_id %>%
  mutate(VSTESTCD = "PULSE") %>%
  mutate(VSTEST = "Pulse") %>%
  mutate(VSORRES = as.character(PULSE))

# 3. Combine and Save
if (length(all_tests) > 0) {
    final_vs <- bind_rows(all_tests)
    write.csv(final_vs, "vs.csv", row.names = FALSE)
}
