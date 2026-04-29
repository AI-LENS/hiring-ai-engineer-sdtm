"""
planner.py — LLM-powered mapping planner.

Given a raw-data summary and the CT summary, the planner asks Gemini to
produce a structured JSON mapping plan that the R script builder can consume.

Why use an LLM here?
────────────────────
The column names in raw data are arbitrary (IT.TEMP, SYS_BP, SUBPOS …).
Mapping them to SDTM variable names requires reading intent, not just
pattern matching. The LLM is well-suited for this; deterministic code is not.

Why NOT use an LLM for R code generation?
─────────────────────────────────────────
R syntax bugs from an LLM are random and hard to debug.  We keep R generation
deterministic (r_script_builder.py) and give the LLM a narrow, well-typed
JSON schema to fill in instead.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import GEMINI_MODEL, VS_TESTS, VS_CT_CODELISTS


# ── Prompt text ──────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a CDISC SDTM data-standards expert working on the Vital Signs (VS) domain.

Your job is to analyse a raw dataset summary and a Controlled Terminology (CT) \
summary, then produce a structured JSON mapping plan that a downstream code \
generator will use to create an sdtm.oak R script.

Rules
─────
1. Return ONLY a JSON object — no prose, no markdown fences, no explanation.
2. Strictly follow the JSON schema provided in the user message.
3. Only include VS tests you are confident can be mapped (raw column exists + \
not all-null).
4. Use the CT code lists to confirm valid term_values before choosing \
fixed_unit / std_unit.
5. Choose conversion = "celsius" only for temperature raw values in Fahrenheit.
6. Choose conversion = "none" for blood pressure, pulse, etc.
7. If a column is ambiguous, prefer the interpretation that is most common in \
clinical trials.
8. Do not invent column names that are not in the raw data summary.
"""

_USER_TEMPLATE = """\
=== RAW DATA SUMMARY ===
{raw_summary}

=== CONTROLLED TERMINOLOGY SUMMARY (relevant code lists only) ===
{ct_summary}

=== KNOWN VS TESTS ===
{vs_tests}

=== JSON SCHEMA TO FILL ===
{{
  "pat_var"      : "<column that holds subject / patient ID>",
  "date_col"     : "<column that holds visit date (VSDTC source)>",
  "visit_col"    : "<column that holds visit label (VISIT source)>",
  "visitnum_col" : "<column for numeric visit number, or null>",
  "position_col" : "<column for body position (VSPOS), or null>",
  "tests": [
    {{
      "testcd"         : "<VSTESTCD value, e.g. TEMP>",
      "testname"       : "<VSTEST value, e.g. Temperature>",
      "raw_result_col" : "<raw column holding numeric result>",
      "raw_unit_col"   : "<raw column holding unit, or null>",
      "fixed_unit"     : "<literal unit string when raw_unit_col is null, e.g. F>",
      "loc_col"        : "<raw column for anatomical location, or null>",
      "vstestcd_clst"  : "C66741",
      "vstest_clst"    : "C67153",
      "vsorresu_clst"  : "C66770",
      "vsstresu_clst"  : "C66770",
      "vsloc_clst"     : "C74456",
      "vspos_clst"     : "C71148",
      "std_unit"       : "<standardised unit term_value from C66770>",
      "conversion"     : "<one of: celsius | none>"
    }}
  ]
}}

Produce the filled JSON now.
"""


# ══════════════════════════════════════════════════════════════════════════════
# Public function
# ══════════════════════════════════════════════════════════════════════════════

def plan_mappings(
    raw_summary : dict[str, Any],
    ct_summary  : dict[str, Any],
    llm         : ChatGoogleGenerativeAI | None = None,
) -> dict[str, Any]:
    """
    Call Gemini to produce a mapping plan from raw column analysis + CT summary.

    Parameters
    ----------
    raw_summary : output of tools.inspect_raw_data()
    ct_summary  : output of tools.inspect_ct()
    llm         : optional pre-built LangChain LLM; created here if None

    Returns
    -------
    Parsed JSON dict conforming to the schema in _USER_TEMPLATE.
    Raises ValueError if the LLM response cannot be parsed as JSON.
    """
    if llm is None:
        llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0)

    # Filter CT summary to only the code lists the VS domain needs
    relevant_ct = {
        code: info
        for code, info in ct_summary.items()
        if code in VS_CT_CODELISTS.values()
    }

    user_msg = _USER_TEMPLATE.format(
        raw_summary = json.dumps(raw_summary, indent=2, default=str),
        ct_summary  = json.dumps(relevant_ct,  indent=2, default=str),
        vs_tests    = json.dumps(VS_TESTS,      indent=2),
    )

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_msg),
    ]

    response = llm.invoke(messages)
    raw_text = response.content.strip()

    # Strip any accidental markdown fences (defensive)
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$",           "", raw_text)

    try:
        plan = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Planner returned non-JSON response.\n"
            f"Error : {exc}\n"
            f"Response:\n{raw_text}"
        ) from exc

    _validate_plan(plan)
    return plan


def _validate_plan(plan: dict[str, Any]) -> None:
    """Lightweight structural validation of the planner's JSON output."""
    required_top = {"pat_var", "date_col", "visit_col", "tests"}
    missing = required_top - set(plan.keys())
    if missing:
        raise ValueError(f"Mapping plan missing required top-level keys: {missing}")

    if not isinstance(plan["tests"], list) or len(plan["tests"]) == 0:
        raise ValueError("Mapping plan 'tests' must be a non-empty list.")

    required_per_test = {
        "testcd", "testname", "raw_result_col",
        "vstestcd_clst", "vstest_clst", "std_unit", "conversion",
    }
    for i, test in enumerate(plan["tests"]):
        missing_t = required_per_test - set(test.keys())
        if missing_t:
            raise ValueError(f"Test #{i} missing keys: {missing_t}")
        if test["conversion"] not in ("celsius", "none"):
            raise ValueError(
                f"Test #{i} has invalid conversion value: {test['conversion']!r}"
            )
