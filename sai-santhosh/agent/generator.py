import subprocess
from pathlib import Path
from textwrap import dedent


class RScriptGenerator:
    def __init__(self, plan, raw_csv, ct_csv, vs_out, r_script_path):
        self.plan = plan
        self.raw_csv = Path(raw_csv).as_posix()
        self.ct_csv = Path(ct_csv).as_posix()
        self.vs_out = Path(vs_out).as_posix()
        self.r_script_path = r_script_path

    def write(self):
        self.r_script_path.write_text(self.build_script(), encoding="utf-8")

    def execute(self):
        result = subprocess.run(
            ["Rscript", str(self.r_script_path)],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print(result.stderr)
        return result.returncode == 0

    def build_script(self):
        blocks = []

        for col in self.plan["columns"]:
            raw = col["raw_col"]

            if col["convert"]:
                vsstres = f"({raw} - 32) * 5/9"
                vsstresu = '"C"'
            else:
                vsstres = raw
                vsstresu = f'"{col["vstresu"]}"'

            block = f"""
ds_{col['vstestcd']} <- raw_data %>%
  filter(!is.na({raw})) %>%
  mutate(
    STUDYID = "{self.plan['studyid']}",
    USUBJID = paste0("{self.plan['studyid']}-", PATNUM),
    VSTESTCD = "{col['vstestcd']}",
    VSTEST = "{col['vstest']}",
    VSORRES = {raw},
    VSORRESU = "{col['vsorresu']}",
    VSSTRESN = {vsstres},
    VSSTRESU = {vsstresu},
    VSPOS = toupper(SUBPOS)
  )
"""
            blocks.append(block)

        datasets = ",\n".join([f"ds_{c['vstestcd']}" for c in self.plan["columns"]])

        return dedent(f"""
library(dplyr)

raw_data <- read.csv("{self.raw_csv}")
ct <- read.csv("{self.ct_csv}")

{''.join(blocks)}

vs <- bind_rows({datasets})

vs <- vs %>%
  arrange(USUBJID, VSTESTCD) %>%
  group_by(USUBJID) %>%
  mutate(VSSEQ = row_number()) %>%
  ungroup()

write.csv(vs, "{self.vs_out}", row.names = FALSE)
""")