"""
tools.py — Deterministic tool functions called by the LangChain agent.

Design principle: every tool here is deterministic and side-effect-free
(or has a single, clearly labelled side effect — writing a file or running R).
LLM reasoning happens in the agent/planner; heavy lifting happens here.

Tools exposed to the agent
───────────────────────────
1.  inspect_raw_data(path)          → data summary (columns, dtypes, sample rows)
2.  inspect_ct(path)                → CT code-list summary keyed by codelist_code
3.  run_r_script(script, out_csv)   → executes R via subprocess, returns stdout/stderr
4.  validate_sdtm_output(out, ct)   → checks CT compliance + shape; returns report dict
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from config import VS_CT_CODELISTS, REQUIRED_SDTM_COLS


# ══════════════════════════════════════════════════════════════════════════════
# 1. inspect_raw_data
# ══════════════════════════════════════════════════════════════════════════════

def inspect_raw_data(path: str) -> dict[str, Any]:
    """
    Read a raw VS CSV and return a structured summary the planner can reason over.

    Returns
    -------
    {
      "columns"     : [list of column names],
      "dtypes"      : {col: dtype_str, ...},
      "row_count"   : int,
      "sample_rows" : [list of dicts, first 3 rows],
      "null_counts" : {col: int, ...},
    }
    """
    if not Path(path).exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")

    df = pd.read_csv(path)

    return {
        "columns"    : df.columns.tolist(),
        "dtypes"     : {c: str(t) for c, t in df.dtypes.items()},
        "row_count"  : len(df),
        "sample_rows": df.head(3).to_dict(orient="records"),
        "null_counts": df.isnull().sum().to_dict(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. inspect_ct
# ══════════════════════════════════════════════════════════════════════════════

def inspect_ct(path: str) -> dict[str, Any]:
    """
    Parse the CDISC Controlled Terminology CSV and return a compact summary.

    Expected columns: codelist_code, codelist_name, term_value, collected_value

    Returns
    -------
    {
      "<codelist_code>": {
          "name"            : "VS Test Code",
          "term_values"     : ["TEMP", "SYSBP", ...],
          "collected_values": ["TEMP", "Temperature", ...],
      },
      ...
    }
    """
    if not Path(path).exists():
        raise FileNotFoundError(f"CT file not found: {path}")

    df = pd.read_csv(path)

    # Normalise column names to lowercase for robustness
    df.columns = [c.strip().lower() for c in df.columns]

    required = {"codelist_code", "codelist_name", "term_value", "collected_value"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"CT CSV is missing columns: {missing}")

    summary: dict[str, Any] = {}
    for code, group in df.groupby("codelist_code"):
        summary[str(code)] = {
            "name"            : group["codelist_name"].iloc[0],
            "term_values"     : group["term_value"].dropna().unique().tolist(),
            "collected_values": group["collected_value"].dropna().unique().tolist(),
        }
    return summary


# ══════════════════════════════════════════════════════════════════════════════
# 3. run_r_script
# ══════════════════════════════════════════════════════════════════════════════

def run_r_script(script_content: str, script_path: str) -> dict[str, Any]:
    """
    Write *script_content* to *script_path* and execute it with Rscript.

    Returns
    -------
    {
      "returncode": int,
      "stdout"    : str,
      "stderr"    : str,
      "success"   : bool,
    }

    The caller decides what to do with errors — we never swallow them here.
    """
    Path(script_path).parent.mkdir(parents=True, exist_ok=True)
    Path(script_path).write_text(script_content, encoding="utf-8")

    result = subprocess.run(
        ["Rscript", "--vanilla", script_path],
        capture_output=True,
        text=True,
        timeout=180,          # 3 min; real sdtm.oak runs are fast
    )

    return {
        "returncode": result.returncode,
        "stdout"    : result.stdout.strip(),
        "stderr"    : result.stderr.strip(),
        "success"   : result.returncode == 0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. validate_sdtm_output
# ══════════════════════════════════════════════════════════════════════════════

def validate_sdtm_output(output_csv: str, ct_csv: str) -> dict[str, Any]:
    """
    Run deterministic SDTM VS validation checks on the output CSV.

    Checks
    ──────
    a) File exists and is non-empty
    b) DOMAIN == "VS" for every row
    c) Required columns are present
    d) No STUDYID / USUBJID / VSTESTCD nulls
    e) VSTESTCD values are within C66741 term_values
    f) VSPOS values (when present) are within C71148 term_values
    g) VSLOC values (when present) are within C74456 term_values
    h) VSSTRESU values (when present) are within C66770 term_values
    i) VSSTRESN is numeric (or null) — never a string
    j) VSDTC matches ISO 8601 pattern (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)

    Returns a structured report; agent uses this to decide whether to re-plan.
    """
    import re

    report: dict[str, Any] = {
        "passed" : [],
        "failed" : [],
        "warnings": [],
    }

    def ok(msg: str)   : report["passed"].append(msg)
    def fail(msg: str) : report["failed"].append(msg)
    def warn(msg: str) : report["warnings"].append(msg)

    # ── a) File exists ─────────────────────────────────────────────────────────
    if not Path(output_csv).exists():
        fail("Output CSV not found — R script likely failed.")
        report["valid"] = False
        return report
    ok("Output CSV exists")

    df = pd.read_csv(output_csv)
    if df.empty:
        fail("Output CSV is empty.")
        report["valid"] = False
        return report
    ok(f"Output CSV has {len(df)} rows and {len(df.columns)} columns")

    # ── b) DOMAIN ──────────────────────────────────────────────────────────────
    if "DOMAIN" in df.columns:
        bad = df[df["DOMAIN"] != "VS"]
        if bad.empty:
            ok("DOMAIN == 'VS' for all rows")
        else:
            fail(f"DOMAIN != 'VS' for {len(bad)} rows: {bad['DOMAIN'].unique().tolist()}")
    else:
        warn("DOMAIN column not present")

    # ── c) Required columns ────────────────────────────────────────────────────
    missing_cols = [c for c in REQUIRED_SDTM_COLS if c not in df.columns]
    if missing_cols:
        fail(f"Missing required SDTM VS columns: {missing_cols}")
    else:
        ok("All required SDTM VS columns present")

    # ── d) No nulls in key identifiers ────────────────────────────────────────
    for key_col in ["STUDYID", "USUBJID", "VSTESTCD"]:
        if key_col in df.columns:
            n_null = df[key_col].isnull().sum()
            if n_null:
                fail(f"{key_col} has {n_null} null values — identifier must be complete")
            else:
                ok(f"{key_col} has no nulls")

    # ── Load CT for value checks ───────────────────────────────────────────────
    try:
        ct = inspect_ct(ct_csv)
    except Exception as exc:
        warn(f"Could not load CT for value checks: {exc}")
        ct = {}

    # ── e–h) CT-constrained columns ───────────────────────────────────────────
    CT_CHECKS = {
        "VSTESTCD" : VS_CT_CODELISTS["VSTESTCD"],
        "VSPOS"    : VS_CT_CODELISTS["VSPOS"],
        "VSLOC"    : VS_CT_CODELISTS["VSLOC"],
        "VSSTRESU" : VS_CT_CODELISTS["VSSTRESU"],
    }

    for col, clst in CT_CHECKS.items():
        if col not in df.columns:
            continue
        non_null = df[col].dropna()
        if non_null.empty:
            warn(f"{col} is entirely null (may be intentional)")
            continue

        allowed = set(ct.get(clst, {}).get("term_values", []))
        if not allowed:
            warn(f"No CT entries found for code list {clst} ({col}) — skipping value check")
            continue

        bad_vals = set(non_null.unique()) - allowed
        if bad_vals:
            fail(f"{col}: values not in CT ({clst}): {sorted(bad_vals)}")
        else:
            ok(f"{col}: all values conform to CT {clst}")

    # ── i) VSSTRESN numeric ────────────────────────────────────────────────────
    if "VSSTRESN" in df.columns:
        non_null_sn = df["VSSTRESN"].dropna()
        try:
            pd.to_numeric(non_null_sn, errors="raise")
            ok("VSSTRESN is numeric")
        except (ValueError, TypeError):
            fail("VSSTRESN contains non-numeric values")

    # ── j) VSDTC ISO 8601 ─────────────────────────────────────────────────────
    if "VSDTC" in df.columns:
        iso_pattern = re.compile(
            r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$"
        )
        bad_dates = df["VSDTC"].dropna().apply(
            lambda v: not iso_pattern.match(str(v))
        )
        n_bad = bad_dates.sum()
        if n_bad:
            fail(f"VSDTC: {n_bad} values do not match ISO 8601 pattern")
        else:
            ok("VSDTC conforms to ISO 8601")

    report["valid"] = len(report["failed"]) == 0
    return report


# ══════════════════════════════════════════════════════════════════════════════
# Utility — pretty-print a tool result for logging
# ══════════════════════════════════════════════════════════════════════════════

def pretty(obj: Any, indent: int = 2) -> str:
    return json.dumps(obj, indent=indent, default=str)
