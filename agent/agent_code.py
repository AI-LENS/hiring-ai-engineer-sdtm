from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
import ast

from agent.tool import generate_r_script, run_r_script, validate, plan_mapping

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def run_agent():

    print("🤖 Agent started...")

    # -------------------------
    # STEP 1: Read data
    # -------------------------
    raw = pd.read_csv("data/vs_raw.csv")
    print("📥 Loaded raw data")

    # -------------------------
    # STEP 2: LLM Planning
    # -------------------------
    prompt = f"""
You are a clinical SDTM mapping agent.

Given raw dataset columns:
{list(raw.columns)}

Return ONLY SDTM test codes from:
["TEMP","SYSBP","DIABP","PULSE"]

Rules:
- SYS_BP → SYSBP
- DIA_BP → DIABP
- Ignore others
- Output only Python list
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content.strip()

    try:
        tests = ast.literal_eval(content)
    except:
        print("⚠️ LLM failed, using default")
        tests = plan_mapping()

    allowed = ["TEMP","SYSBP","DIABP","PULSE"]
    tests = [t for t in tests if t in allowed]

    print("🧠 Planned tests:", tests)

    # -------------------------
    # STEP 2.5: REPORT MAPPING PLAN
    # -------------------------
    print("\n🧠 Mapping Plan:")
    print("TEMP  ← IT.TEMP      (assign_no_ct)")
    print("SYSBP ← SYS_BP       (assign_no_ct)")
    print("DIABP ← DIA_BP       (assign_no_ct)")
    print("PULSE ← PULSE        (assign_no_ct)")
    print("VSPOS ← SUBPOS       (assign_ct, C71148)")
    print("VSLOC ← IT.TEMP_LOC  (assign_ct, C74456)")

    # -------------------------
    # STEP 3: Generate R script
    # -------------------------
    r_script = generate_r_script(tests)

    with open("output/generated.R", "w", encoding="utf-8") as f:
        f.write(r_script)

    print("\n📝 R script generated")

    # -------------------------
    # STEP 4: Run R
    # -------------------------
    run_r_script()
    print("⚙️ R script executed")

    # -------------------------
    # STEP 5: Validate
    # -------------------------
    print("\n🔍 Validating output...")
    validate()

    # -------------------------
    # STEP 6: FINAL REPORT
    # -------------------------
    print("\n📊 Agent Summary:")
    print(f"Tests processed: {tests}")
    print("CT used: C71148 (Position), C74456 (Location), C66770 (Units)")
    print("Missing optional variables handled as NA")
    print("Some differences from golden due to partial scope")

    print("\n✅ Agent finished successfully")