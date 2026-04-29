"""
run.py — SDTM VS Mapping Agent

5 phases:
  1. Read    — load vs_raw.csv and sdtm_ct.csv
  2. Plan    — LLM reads columns + sdtm.oak docs, writes an R mapping script
  3. Generate — save that script to output/generated.R
  4. Execute  — run it via Rscript subprocess
  5. Validate — check required cols, CT values, diff against golden
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from agent.mapper    import get_llm_mapping_plan
from agent.validator import validate

load_dotenv()

BASE    = Path(__file__).parent
OUT_DIR = BASE / "output"
OUT_DIR.mkdir(exist_ok=True)

# Auto-detect Rscript
RSCRIPT = shutil.which("Rscript") or next(
    (p for p in [
        r"C:\R\bin\Rscript.exe",
        r"C:\Program Files\R\R-4.6.0\bin\Rscript.exe",
        r"C:\Program Files\R\R-4.5.0\bin\Rscript.exe",
        "/usr/bin/Rscript",
    ] if Path(p).exists()),
    None
)


def main():
    # ── Phase 1: Read ─────────────────────────────────────────
    print("\n--- Phase 1: Reading inputs ---")
    raw_df = pd.read_csv(BASE / "vs_raw.csv")
    print(f"  vs_raw.csv: {len(raw_df)} rows, columns: {raw_df.columns.tolist()}")

    # ── Phase 2: Plan (LLM) ───────────────────────────────────
    print("\n--- Phase 2: LLM planning ---")
    r_code = get_llm_mapping_plan(
        raw_columns=raw_df.columns.tolist(),
        ct_path="sdtm_ct.csv",
    )

    # ── Phase 3: Generate R script ────────────────────────────
    print("\n--- Phase 3: Saving generated.R ---")
    r_file = OUT_DIR / "generated.R"
    r_file.write_text(r_code, encoding="utf-8")
    print(f"  Saved {r_file} ({len(r_code.splitlines())} lines)")

    # ── Phase 4: Execute ──────────────────────────────────────
    print("\n--- Phase 4: Running Rscript ---")
    if not RSCRIPT:
        print("  ❌ Rscript not found. Add R to PATH or edit RSCRIPT candidates in run.py.")
        sys.exit(1)

    print(f" Using: {RSCRIPT}")
    result = subprocess.run(
        [RSCRIPT, str(r_file)],
        capture_output=True, text=True, cwd=str(BASE),
    )

    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())

    if result.returncode != 0:
        print(" ❌ R script failed. Check output/generated.R for syntax errors.")
        sys.exit(1)

    print("✅ output/vs.csv created.")

    # ── Phase 5: Validate ─────────────────────────────────────
    print("\n--- Phase 5: Validating output ---")
    report, passed = validate(
        output_path=OUT_DIR / "vs.csv",
        golden_path=BASE / "vs_golden.csv",
        ct_path=BASE / "sdtm_ct.csv",
    )

    report_file = OUT_DIR / "validation_report.md"
    report_file.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n  Report saved to {report_file}")
    print(f"\n{'✅ PASS' if passed else '❌ FAIL'}")


if __name__ == "__main__":
    main()