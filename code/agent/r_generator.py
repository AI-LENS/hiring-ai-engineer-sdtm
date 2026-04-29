def generate_r_script(plan):
    os.makedirs("output", exist_ok=True)
    temp = plan.get("TEMP", {})

    raw_col = temp.get("raw_column",      "IT.TEMP").replace(".", "_")
    loc_col = temp.get("location_column", "IT.TEMP_LOC").replace(".", "_")
    pos_col = temp.get("position_column", "SUBPOS").replace(".", "_")

    r_code = f'''
library(sdtm.oak)
library(dplyr)

raw_data <- read.csv("data/vs_raw.csv", stringsAsFactors = FALSE)
names(raw_data) <- gsub("\\\\.", "_", names(raw_data))

vsorres  <- assign_no_ct(raw_dat = raw_data, raw_var = "{raw_col}", tgt_var = "VSORRES",  id_vars = oak_id_vars())
vsstresc <- assign_no_ct(raw_dat = raw_data, raw_var = "{raw_col}", tgt_var = "VSSTRESC", id_vars = oak_id_vars())
vsloc    <- assign_no_ct(raw_dat = raw_data, raw_var = "{loc_col}", tgt_var = "VSLOC",    id_vars = oak_id_vars())
vspos    <- assign_no_ct(raw_dat = raw_data, raw_var = "{pos_col}", tgt_var = "VSPOS",    id_vars = oak_id_vars())

vstestcd <- hardcode_no_ct(raw_dat = raw_data, tgt_var = "VSTESTCD", tgt_val = "TEMP",        id_vars = oak_id_vars())
vstest   <- hardcode_no_ct(raw_dat = raw_data, tgt_var = "VSTEST",   tgt_val = "Temperature", id_vars = oak_id_vars())
vsorresu <- hardcode_no_ct(raw_dat = raw_data, tgt_var = "VSORRESU", tgt_val = "F",           id_vars = oak_id_vars())
vsstresu <- hardcode_no_ct(raw_dat = raw_data, tgt_var = "VSSTRESU", tgt_val = "C",           id_vars = oak_id_vars())

vs <- reduce(
  list(vsorres, vsstresc, vsloc, vspos, vstestcd, vstest, vsorresu, vsstresu),
  full_join
)

write.csv(vs, "output/vs.csv", row.names = FALSE, na = "")
cat("VS dataset created successfully\\n")
'''

    with open("output/generated.R", "w", encoding="utf-8") as f:
        f.write(r_code)
    print("generated.R created successfully")
