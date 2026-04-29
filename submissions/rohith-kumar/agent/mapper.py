"""
agent/mapper.py
Final Fix: Mandatory sdtm.oak ID generation.
"""
import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

SDTM_OAK_CONTEXT = """
You are an expert R developer mapping data to SDTM VS using sdtm.oak.

========================
CRITICAL INITIALIZATION (MANDATORY)
========================
Before ANY mapping, you MUST initialize the raw data with ID variables.
Example:
raw_vitals <- read_csv("vs_raw.csv") %>%
  generate_oak_id_vars(pat_var = "PATNUM", raw_src = "vitals")

(Note: Use "PATNUM" or the subject ID column from the raw data).

========================
MAPPING RULES
========================
Use %>% pipes. In every sdtm.oak function, you MUST pass 'raw_dat = .'
Functions:
- assign_no_ct(raw_dat = ., raw_var = "IT.TEMP", tgt_var = "VSORRES")
- hardcode_ct(raw_dat = ., raw_var = "", tgt_var = "VSTESTCD", tgt_val = "TEMP", ct_clst = "C66741")

========================
EXAMPLE PIPELINE
========================
vs_TEMP <- raw_vitals %>%
  filter(!is.na(IT.TEMP)) %>%
  assign_no_ct(raw_dat = ., raw_var = "IT.TEMP", tgt_var = "VSORRES") %>%
  hardcode_ct(raw_dat = ., raw_var = "", tgt_var = "VSTESTCD", tgt_val = "TEMP", ct_clst = "C66741") %>%
  mutate(VSSTRESC = as.character(VSORRES))

========================
FINAL OUTPUT
========================
- Map: TEMP, SYSBP, DIABP, PULSE.
- bind_rows() all outputs.
- Add STUDYID, DOMAIN="VS", USUBJID, VSDTC.
- write_csv(vs_final, "output/vs.csv")

Output ONLY valid R code.
"""

def get_llm_mapping_plan(raw_columns: list, ct_path: str) -> str:
    print("LLM is planning the SDTM mapping with OAK IDs...")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Detect subject ID column (usually PATNUM or USUBJID)
    pat_col = "PATNUM" if "PATNUM" in raw_columns else "USUBJID"
    
    prompt = f"{SDTM_OAK_CONTEXT}\n\nRaw columns: {raw_columns}\nSubject Column: {pat_col}"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Generate ONLY valid R code. MUST use generate_oak_id_vars first."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    code = response.choices[0].message.content or ""
    code = re.sub(r"^```[a-zA-Z]*\n?", "", code.strip())
    code = re.sub(r"\n?```$", "", code.strip())
    return code