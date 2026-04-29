"""
config.py — Central configuration for the SDTM VS Agent.

Defines file paths, CT code-list metadata, and SDTM VS column expectations.
Keeping constants here (not scattered across tools) makes the agent auditable.
"""

import os

# ── Paths ──────────────────────────────────────────────────────────────────────
RAW_VS_CSV      = os.environ.get("RAW_VS_CSV",  "data/vs_raw.csv")
CT_CSV          = os.environ.get("CT_CSV",       "data/sdtm_ct.csv")
GOLDEN_CSV      = os.environ.get("GOLDEN_CSV",   "data/vs_golden.csv")
OUTPUT_CSV      = os.environ.get("OUTPUT_CSV",   "data/vs_sdtm_output.csv")
R_SCRIPT_PATH   = os.environ.get("R_SCRIPT",     "scripts/generated_mapping.R")

# ── CT code lists relevant to the VS domain ───────────────────────────────────
VS_CT_CODELISTS = {
    "VSTESTCD" : "C66741",   # VS Test Code
    "VSTEST"   : "C67153",   # VS Test Name
    "VSORRESU" : "C66770",   # Original units
    "VSSTRESU" : "C66770",   # Standardised units
    "VSPOS"    : "C71148",   # Position (SUPINE / SITTING …)
    "VSLOC"    : "C74456",   # Anatomical location (ARM / ORAL CAVITY …)
}

# ── Required SDTM VS columns (SDTMIG v3.3 VS domain) ─────────────────────────
REQUIRED_SDTM_COLS = [
    "STUDYID", "DOMAIN", "USUBJID",
    "VSTESTCD", "VSTEST",
    "VSORRES", "VSORRESU",
    "VSSTRESC", "VSSTRESN", "VSSTRESU",
    "VSPOS", "VISITNUM", "VISIT", "VSDTC",
]

# ── Vital-sign tests to map (test-code → human label) ─────────────────────────
VS_TESTS = {
    "SYSBP" : "Systolic Blood Pressure",
    "DIABP" : "Diastolic Blood Pressure",
    "PULSE" : "Pulse Rate",
    "TEMP"  : "Temperature",
}

# ── Gemini model ───────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.0-flash"
