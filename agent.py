"""
agent.py — Main SDTM VS conversion agent using LangChain + Google Gemini.

Architecture
────────────

  ┌──────────────────────────────────────────────────────────────────┐
  │  SDTMVSAgent                                                     │
  │                                                                  │
  │  Step 1 ── Inspect      inspect_raw_data()  inspect_ct()        │
  │  Step 2 ── Plan         planner.plan_mappings()  [LLM]          │
  │  Step 3 ── Build R      r_script_builder.build_r_script()       │
  │  Step 4 ── Run R        tools.run_r_script()  [subprocess]      │
  │  Step 5 ── Validate     tools.validate_sdtm_output()            │
  │  Step 6 ── Report       Gemini summarises what happened  [LLM]  │
  │                                                                  │
  │  Retry loop: if Step 4 fails, ask Gemini to fix the R script.   │
  │  (max 2 retries — keeps the loop visible and bounded)           │
  └──────────────────────────────────────────────────────────────────┘

Design choices
──────────────
• Steps 1, 3, 4, 5 are deterministic — no LLM involvement.
• Step 2 uses the LLM for column-to-variable semantic matching.
• Step 6 uses the LLM for natural-language summarisation only.
• The retry in Step 4 uses the LLM as a targeted R-debugging assistant.
• Every step prints a clear log line so a reviewer can follow execution.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import (
    GEMINI_MODEL, RAW_VS_CSV, CT_CSV, OUTPUT_CSV,
    R_SCRIPT_PATH, GOLDEN_CSV,
)
from tools import inspect_raw_data, inspect_ct, run_r_script, validate_sdtm_output, pretty
from planner import plan_mappings
from r_script_builder import build_r_script


# ══════════════════════════════════════════════════════════════════════════════
# Logging helpers
# ══════════════════════════════════════════════════════════════════════════════

def _log(step: str, msg: str) -> None:
    width = 72
    print(f"\n{'─' * width}")
    print(f"  {step}")
    print(f"{'─' * width}")
    print(textwrap.indent(msg, "  "))


def _log_dict(step: str, data: dict) -> None:
    _log(step, pretty(data))


# ══════════════════════════════════════════════════════════════════════════════
# LLM-powered R script repair (retry helper)
# ══════════════════════════════════════════════════════════════════════════════

_REPAIR_SYSTEM = """\
You are an expert in the R package sdtm.oak. Given a broken R script and its \
error output, return ONLY the corrected R script (no explanation, no fences). \
Do not change the overall logic — only fix the syntax or API usage errors shown \
in the stderr output.
"""


def _repair_r_script(
    broken_script : str,
    stderr        : str,
    llm           : ChatGoogleGenerativeAI,
) -> str:
    """Ask Gemini to fix a broken R script. Returns corrected script text."""
    msg = (
        f"=== BROKEN R SCRIPT ===\n{broken_script}\n\n"
        f"=== STDERR / ERROR ===\n{stderr}\n\n"
        "Return ONLY the corrected R script."
    )
    response = llm.invoke([
        SystemMessage(content=_REPAIR_SYSTEM),
        HumanMessage(content=msg),
    ])
    # Strip any stray markdown fences
    script = response.content.strip()
    if script.startswith("```"):
        script = "\n".join(script.split("\n")[1:])
    if script.endswith("```"):
        script = "\n".join(script.split("\n")[:-1])
    return script.strip()


# ══════════════════════════════════════════════════════════════════════════════
# Final report generator
# ══════════════════════════════════════════════════════════════════════════════

_REPORT_SYSTEM = """\
You are a CDISC data standards reviewer. Write a concise (≤ 300 word) \
plain-English summary of what the SDTM VS agent did, what succeeded, \
what failed or was uncertain, and what a programmer should address next. \
Be factual — base the summary strictly on the data provided.
"""


def _generate_report(
    mapping_plan     : dict[str, Any],
    validation_report: dict[str, Any],
    r_result         : dict[str, Any],
    llm              : ChatGoogleGenerativeAI,
) -> str:
    payload = {
        "mapping_plan"     : mapping_plan,
        "r_execution"      : r_result,
        "validation_report": validation_report,
    }
    response = llm.invoke([
        SystemMessage(content=_REPORT_SYSTEM),
        HumanMessage(content=json.dumps(payload, indent=2, default=str)),
    ])
    return response.content.strip()


# ══════════════════════════════════════════════════════════════════════════════
# Main agent class
# ══════════════════════════════════════════════════════════════════════════════

class SDTMVSAgent:
    """
    Agentic pipeline that converts raw VS data into an SDTM VS dataset
    by orchestrating sdtm.oak (R) as a black-box tool.
    """

    MAX_RETRIES = 2

    def __init__(
        self,
        raw_csv    : str = RAW_VS_CSV,
        ct_csv     : str = CT_CSV,
        output_csv : str = OUTPUT_CSV,
        r_script   : str = R_SCRIPT_PATH,
        study_id   : str = "CDISCPILOT01",
        api_key    : str | None = None,
    ):
        self.raw_csv    = raw_csv
        self.ct_csv     = ct_csv
        self.output_csv = output_csv
        self.r_script   = r_script
        self.study_id   = study_id

        # Single shared LLM instance — all steps use the same model/temp
        self.llm = ChatGoogleGenerativeAI(
            model        = GEMINI_MODEL,
            temperature  = 0,            # deterministic for planning
            google_api_key = api_key or os.environ.get("GOOGLE_API_KEY"),
        )

    # ──────────────────────────────────────────────────────────────────────────
    def run(self) -> dict[str, Any]:
        """
        Execute the full agent pipeline.

        Returns a dict with keys:
          mapping_plan, r_script, r_result, validation, report, success
        """
        print("\n" + "═" * 72)
        print("  SDTM VS AGENT  —  LangChain + Google Gemini")
        print("═" * 72)

        # ── Step 1: Inspect inputs ─────────────────────────────────────────────
        _log("STEP 1 · Inspect raw data", f"Reading: {self.raw_csv}")
        raw_summary = inspect_raw_data(self.raw_csv)
        _log("STEP 1 · Raw data summary", pretty(raw_summary))

        _log("STEP 1 · Inspect CT", f"Reading: {self.ct_csv}")
        ct_summary = inspect_ct(self.ct_csv)
        _log("STEP 1 · CT summary (code list keys)", str(list(ct_summary.keys())))

        # ── Step 2: Plan mappings (LLM) ────────────────────────────────────────
        _log("STEP 2 · Plan column-to-SDTM mappings", "Calling Gemini planner …")
        mapping_plan = plan_mappings(raw_summary, ct_summary, llm=self.llm)
        _log("STEP 2 · Mapping plan", pretty(mapping_plan))

        # ── Step 3: Build R script (deterministic) ─────────────────────────────
        _log("STEP 3 · Build R script", "Generating sdtm.oak script …")
        r_script_text = build_r_script(
            mapping_plan = mapping_plan,
            raw_csv      = self.raw_csv,
            ct_csv       = self.ct_csv,
            output_csv   = self.output_csv,
            study_id     = self.study_id,
        )
        _log("STEP 3 · R script preview (first 30 lines)",
             "\n".join(r_script_text.splitlines()[:30]))

        # ── Step 4: Run R script (with retry) ─────────────────────────────────
        r_result = None
        current_script = r_script_text

        for attempt in range(1, self.MAX_RETRIES + 2):   # 1-based, up to MAX+1
            _log(f"STEP 4 · Run R script (attempt {attempt})",
                 f"Executing: {self.r_script}")
            r_result = run_r_script(current_script, self.r_script)

            _log(f"STEP 4 · R execution result (attempt {attempt})",
                 pretty(r_result))

            if r_result["success"]:
                break

            if attempt > self.MAX_RETRIES:
                _log("STEP 4 · Max retries reached", "Proceeding to validation with failed R run.")
                break

            # R failed → ask Gemini to fix the script
            _log(f"STEP 4 · R failed — asking Gemini to repair (attempt {attempt})",
                 "Calling LLM repair …")
            current_script = _repair_r_script(
                broken_script = current_script,
                stderr        = r_result["stderr"],
                llm           = self.llm,
            )
            _log(f"STEP 4 · Repaired script preview",
                 "\n".join(current_script.splitlines()[:20]))

        # ── Step 5: Validate output ────────────────────────────────────────────
        _log("STEP 5 · Validate SDTM output", f"Checking: {self.output_csv}")
        validation = validate_sdtm_output(self.output_csv, self.ct_csv)
        _log("STEP 5 · Validation report", pretty(validation))

        # ── Step 6: Generate natural-language report (LLM) ────────────────────
        _log("STEP 6 · Generate summary report", "Asking Gemini to summarise …")
        report = _generate_report(mapping_plan, validation, r_result, self.llm)
        _log("STEP 6 · Final report", report)

        # ── Summary ─────────────────────────────────────────────────────────────
        success = r_result is not None and r_result["success"] and validation["valid"]
        status  = "✅ SUCCESS" if success else "⚠️  COMPLETED WITH ISSUES"

        print("\n" + "═" * 72)
        print(f"  AGENT FINISHED — {status}")
        print("═" * 72 + "\n")

        return {
            "mapping_plan"    : mapping_plan,
            "r_script"        : current_script,
            "r_result"        : r_result,
            "validation"      : validation,
            "report"          : report,
            "success"         : success,
        }


# ══════════════════════════════════════════════════════════════════════════════
# CLI entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="SDTM VS Agent — converts raw VS data to SDTM using sdtm.oak"
    )
    parser.add_argument("--raw-csv",    default=RAW_VS_CSV,    help="Path to raw VS CSV")
    parser.add_argument("--ct-csv",     default=CT_CSV,        help="Path to CT CSV")
    parser.add_argument("--output-csv", default=OUTPUT_CSV,    help="Path for output SDTM CSV")
    parser.add_argument("--r-script",   default=R_SCRIPT_PATH, help="Path to write R script")
    parser.add_argument("--study-id",   default="CDISCPILOT01",help="STUDYID value")
    parser.add_argument("--api-key",    default=None,          help="Google API key (or set GOOGLE_API_KEY env var)")
    args = parser.parse_args()

    agent = SDTMVSAgent(
        raw_csv    = args.raw_csv,
        ct_csv     = args.ct_csv,
        output_csv = args.output_csv,
        r_script   = args.r_script,
        study_id   = args.study_id,
        api_key    = args.api_key,
    )

    result = agent.run()
    sys.exit(0 if result["success"] else 1)
