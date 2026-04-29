"""
agent/planner.py

This is the LangChain agent that plans and executes the SDTM VS transformation.
It uses Google Gemini via LangChain to reason about the data and plan the mappings.
Then it calls codegen.py to generate R code, runs it, and validates the output.

The planner follows these steps:
  1. Read raw data to understand its structure
  2. Read controlled terminology to understand allowed values
  3. Ask Gemini to plan the column mappings
  4. Generate the R script from the plan
  5. Execute the R script
  6. Validate the output
  7. Report results
"""

import json
import os
import re

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI # type: ignore
from langchain_core.messages import HumanMessage, SystemMessage # type: ignore

from agent.prompts import SYSTEM_PROMPT, MAPPING_PROMPT, VALIDATION_PROMPT
from agent.tools import (
    read_raw_data,
    read_controlled_terminology,
    run_r_script,
    check_output_exists,
    save_r_script,
)
from agent.codegen import build_r_script
from agent.validator import run_all_checks


def run_planner(raw_path, ct_path, golden_path, output_csv_path, output_r_path, report_path):
    """
    Run the full SDTM VS agent pipeline from raw data to validated output.

    Args:
        raw_path: Path to the raw vital signs CSV file.
        ct_path: Path to the SDTM controlled terminology CSV file.
        golden_path: Path to the golden reference SDTM VS CSV file.
        output_csv_path: Path where the output vs.csv should be written.
        output_r_path: Path where the generated R script should be saved.
        report_path: Path where the validation report markdown should be written.
    """

    # Load environment variables from .env file
    load_dotenv()

    # Get the Google API key from the environment
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("ERROR: GOOGLE_API_KEY not found in environment. Check your .env file.")
        return

    # Set up the Gemini LLM via LangChain
    # gemini-1.5-flash is fast and cost-effective for this type of structured task
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0,  # Use 0 temperature for deterministic, factual mapping decisions
    )

    print()
    print("=" * 60)
    print("Starting SDTM VS Agent...")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # Step 1: Read the raw data to understand its structure
    # -------------------------------------------------------------------------
    print()
    print(f"Step 1 -- Reading raw vital signs data from {raw_path}")

    raw_data_info = read_raw_data.invoke({"file_path": raw_path})
    print(raw_data_info)

    # Extract column names from the tool output for use in the prompt
    raw_columns_line = ""
    raw_sample_lines = ""
    for line in raw_data_info.splitlines():
        if line.startswith("Column names:"):
            raw_columns_line = line.replace("Column names:", "").strip()
        if "rows" in line.lower() and "total" in line.lower():
            row_count_line = line

    # -------------------------------------------------------------------------
    # Step 2: Read the controlled terminology to understand allowed values
    # -------------------------------------------------------------------------
    print()
    print(f"Step 2 -- Reading controlled terminology from {ct_path}")

    ct_info = read_controlled_terminology.invoke({"file_path": ct_path})

    # Print a condensed version so the log is not too long
    ct_lines = ct_info.splitlines()
    for line in ct_lines[:20]:
        print(f"  {line}")
    if len(ct_lines) > 20:
        print(f"  ... ({len(ct_lines) - 20} more lines)")

    # -------------------------------------------------------------------------
    # Step 3: Ask Gemini to plan the column mappings
    # -------------------------------------------------------------------------
    print()
    print("Step 3 -- Asking Gemini to plan the column mappings...")

    # List the target SDTM variables we need to populate
    sdtm_target_variables = (
        "VSTESTCD, VSTEST, VSORRES, VSORRESU, VSSTRESC, VSSTRESN, VSSTRESU, "
        "VSPOS, VSLOC, VISIT, VISITNUM, VSDTC, STUDYID, DOMAIN, USUBJID, VSSEQ"
    )

    # Fill in the prompt template with actual values
    filled_mapping_prompt = MAPPING_PROMPT.format(
        raw_columns=raw_columns_line,
        raw_sample=raw_data_info,
        ct_summary=ct_info,
        sdtm_target_variables=sdtm_target_variables
    )

    # Send the prompt to Gemini with the system message
    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=filled_mapping_prompt)
        ]

        response = llm.invoke(messages)
        gemini_response_text = response.content

        print(f"  Gemini responded with {len(gemini_response_text)} characters")

        # Try to parse the JSON response from Gemini
        mapping_plan = _parse_mapping_plan(gemini_response_text)

        if mapping_plan:
            print(f"  Gemini returned a mapping plan with {len(mapping_plan)} entries")
        else:
            print("  WARNING: Could not parse Gemini's response as JSON.")
            print("  Using the safe fallback hardcoded mapping plan.")
            mapping_plan = _get_fallback_mapping_plan()

    except Exception as error:
        print(f"  ERROR calling Gemini: {error}")
        print("  Using the safe fallback hardcoded mapping plan.")
        mapping_plan = _get_fallback_mapping_plan()

    # -------------------------------------------------------------------------
    # Step 4: Log the mapping plan in a human-readable format
    # -------------------------------------------------------------------------
    print()
    print("Step 4 -- Mapping plan summary:")

    for entry in mapping_plan:
        test_code = entry.get("test_code", "UNKNOWN")
        sdtm_var = entry.get("sdtm_variable", "?")
        raw_col = entry.get("raw_column", "none")
        oak_func = entry.get("oak_function", "?")
        ct_list = entry.get("ct_codelist", "none")
        tgt_val = entry.get("tgt_val", "")

        if tgt_val:
            print(
                f"  {test_code} test: hardcode {sdtm_var} = '{tgt_val}' "
                f"using {oak_func}"
                + (f" with CT {ct_list}" if ct_list else "")
            )
        else:
            print(
                f"  {test_code} test: raw column {raw_col} maps to {sdtm_var} "
                f"using {oak_func}"
                + (f" with CT {ct_list}" if ct_list else "")
            )

    # -------------------------------------------------------------------------
    # Step 5: Generate the R script from the mapping plan
    # -------------------------------------------------------------------------
    print()
    print("Step 5 -- Generating R script...")

    # Generate the R script as a string
    r_script_content = build_r_script(
        mapping_plan=mapping_plan,
        raw_path=raw_path,
        ct_path=ct_path,
        output_path=output_csv_path
    )

    # Save the R script to disk using the tool
    save_result = save_r_script.invoke({
        "script_path": output_r_path,
        "script_content": r_script_content
    })
    print(f"  {save_result}")

    # -------------------------------------------------------------------------
    # Step 6: Run the R script
    # -------------------------------------------------------------------------
    print()
    print(f"Step 6 -- Running R script via Rscript: {output_r_path}")

    r_result = run_r_script.invoke({"script_path": output_r_path})

    # Log R's output
    if r_result.get("output"):
        print("  R script output:")
        for line in r_result["output"].splitlines():
            print(f"    {line}")

    if r_result.get("error"):
        # Print any stderr from R (may include warnings even on success)
        for line in r_result["error"].splitlines()[:20]:
            print(f"    R stderr: {line}")

    if r_result.get("success"):
        print("  R script completed successfully")
    else:
        print("  ERROR: R script failed.")
        print(f"  Full error message from R:\n{r_result.get('error', 'No error message captured')}")
        print("  Agent stopping because R script failed. Fix the error above and try again.")
        return

    # Confirm the output file was created
    output_check = check_output_exists.invoke({"file_path": output_csv_path})
    print(f"  Output check: {output_check}")

    # -------------------------------------------------------------------------
    # Step 7: Validate the output
    # -------------------------------------------------------------------------
    print()
    print("Step 7 -- Validating output...")

    validation_result = run_all_checks(
        output_path=output_csv_path,
        ct_path=ct_path,
        raw_path=raw_path,
        golden_path=golden_path,
        report_path=report_path
    )

    # If there are failures, optionally ask Gemini to explain them
    failed_checks = validation_result.get("failed", [])
    if failed_checks:
        print()
        print("  Asking Gemini to explain validation failures...")
        _get_gemini_validation_explanation(llm, failed_checks)

    # -------------------------------------------------------------------------
    # Step 8: Print final summary
    # -------------------------------------------------------------------------
    print()
    print("Step 8 -- Validation report written to:", report_path)
    print()
    print("=" * 60)
    print("Agent completed.")
    print()
    print(f"  Summary: {validation_result.get('summary', 'No summary')}")
    print()
    print(f"  Checks passed: {len(validation_result.get('passed', []))}")
    print(f"  Checks failed: {len(failed_checks)}")
    print()
    print("Output files:")
    print(f"  vs.csv              at {output_csv_path}")
    print(f"  R script            at {output_r_path}")
    print(f"  Validation report   at {report_path}")
    print("=" * 60)


def _parse_mapping_plan(gemini_response_text):
    """
    Try to parse the JSON mapping plan from Gemini's response text.
    Gemini sometimes wraps JSON in markdown code blocks, so we strip those first.
    Returns the parsed list of mapping entries, or None if parsing fails.
    """
    if not gemini_response_text:
        return None

    # Remove markdown code block fences if present (```json ... ``` or ``` ... ```)
    cleaned_text = re.sub(r"```(?:json)?", "", gemini_response_text).strip()
    cleaned_text = cleaned_text.replace("```", "").strip()

    # Try to find a JSON array in the text by looking for [ ... ]
    json_match = re.search(r"\[.*\]", cleaned_text, re.DOTALL)
    if json_match:
        json_text = json_match.group(0)
    else:
        json_text = cleaned_text

    try:
        parsed = json.loads(json_text)
        # Confirm it is a list and each item has the required keys
        if not isinstance(parsed, list):
            print("  WARNING: Gemini response was JSON but not a list.")
            return None

        # Check that at least one entry looks like a mapping plan entry
        required_keys = {"sdtm_variable", "oak_function", "test_code"}
        valid_entries = [e for e in parsed if isinstance(e, dict) and required_keys.issubset(e.keys())]

        if not valid_entries:
            print("  WARNING: Gemini response was a list but entries did not have expected keys.")
            return None

        return parsed

    except json.JSONDecodeError as error:
        print(f"  WARNING: Could not parse JSON from Gemini response: {error}")
        print(f"  Response preview: {gemini_response_text[:200]}")
        return None


def _get_fallback_mapping_plan():
    """
    Return a safe hardcoded mapping plan to use when Gemini is unavailable
    or returns an unparseable response.

    This plan covers the four main VS tests: TEMP, SYSBP, DIABP, PULSE.
    It uses the known column names from the pharmaverse vs_raw dataset.
    """
    fallback_plan = [
        # Temperature mappings
        {
            "raw_column": None,
            "sdtm_variable": "VSTESTCD",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C66741",
            "test_code": "TEMP",
            "tgt_val": "TEMP",
            "notes": "Hardcoded test code for temperature"
        },
        {
            "raw_column": None,
            "sdtm_variable": "VSTEST",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C67153",
            "test_code": "TEMP",
            "tgt_val": "Temperature",
            "notes": "Hardcoded test label for temperature"
        },
        {
            "raw_column": "IT.TEMP",
            "sdtm_variable": "VSORRES",
            "oak_function": "assign_no_ct",
            "ct_codelist": None,
            "test_code": "TEMP",
            "tgt_val": None,
            "notes": "Raw temperature result"
        },
        {
            "raw_column": None,
            "sdtm_variable": "VSORRESU",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C66770",
            "test_code": "TEMP",
            "tgt_val": "F",
            "notes": "Temperature recorded in Fahrenheit"
        },
        {
            "raw_column": "IT.TEMP_LOC",
            "sdtm_variable": "VSLOC",
            "oak_function": "assign_ct",
            "ct_codelist": "C74456",
            "test_code": "TEMP",
            "tgt_val": None,
            "notes": "Measurement location for temperature"
        },
        # Systolic Blood Pressure mappings
        {
            "raw_column": None,
            "sdtm_variable": "VSTESTCD",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C66741",
            "test_code": "SYSBP",
            "tgt_val": "SYSBP",
            "notes": "Hardcoded test code for systolic blood pressure"
        },
        {
            "raw_column": None,
            "sdtm_variable": "VSTEST",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C67153",
            "test_code": "SYSBP",
            "tgt_val": "Systolic Blood Pressure",
            "notes": "Hardcoded test label for systolic blood pressure"
        },
        {
            "raw_column": "SYS_BP",
            "sdtm_variable": "VSORRES",
            "oak_function": "assign_no_ct",
            "ct_codelist": None,
            "test_code": "SYSBP",
            "tgt_val": None,
            "notes": "Raw systolic blood pressure result"
        },
        {
            "raw_column": None,
            "sdtm_variable": "VSORRESU",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C66770",
            "test_code": "SYSBP",
            "tgt_val": "mmHg",
            "notes": "Blood pressure recorded in mmHg"
        },
        {
            "raw_column": "SUBPOS",
            "sdtm_variable": "VSPOS",
            "oak_function": "assign_ct",
            "ct_codelist": "C71148",
            "test_code": "SYSBP",
            "tgt_val": None,
            "notes": "Subject position during blood pressure measurement"
        },
        # Diastolic Blood Pressure mappings
        {
            "raw_column": None,
            "sdtm_variable": "VSTESTCD",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C66741",
            "test_code": "DIABP",
            "tgt_val": "DIABP",
            "notes": "Hardcoded test code for diastolic blood pressure"
        },
        {
            "raw_column": None,
            "sdtm_variable": "VSTEST",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C67153",
            "test_code": "DIABP",
            "tgt_val": "Diastolic Blood Pressure",
            "notes": "Hardcoded test label for diastolic blood pressure"
        },
        {
            "raw_column": "DIA_BP",
            "sdtm_variable": "VSORRES",
            "oak_function": "assign_no_ct",
            "ct_codelist": None,
            "test_code": "DIABP",
            "tgt_val": None,
            "notes": "Raw diastolic blood pressure result"
        },
        {
            "raw_column": None,
            "sdtm_variable": "VSORRESU",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C66770",
            "test_code": "DIABP",
            "tgt_val": "mmHg",
            "notes": "Blood pressure recorded in mmHg"
        },
        {
            "raw_column": "SUBPOS",
            "sdtm_variable": "VSPOS",
            "oak_function": "assign_ct",
            "ct_codelist": "C71148",
            "test_code": "DIABP",
            "tgt_val": None,
            "notes": "Subject position during blood pressure measurement"
        },
        # Pulse Rate mappings
        {
            "raw_column": None,
            "sdtm_variable": "VSTESTCD",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C66741",
            "test_code": "PULSE",
            "tgt_val": "PULSE",
            "notes": "Hardcoded test code for pulse rate"
        },
        {
            "raw_column": None,
            "sdtm_variable": "VSTEST",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C67153",
            "test_code": "PULSE",
            "tgt_val": "Pulse Rate",
            "notes": "Hardcoded test label for pulse rate"
        },
        {
            "raw_column": "PULSE",
            "sdtm_variable": "VSORRES",
            "oak_function": "assign_no_ct",
            "ct_codelist": None,
            "test_code": "PULSE",
            "tgt_val": None,
            "notes": "Raw pulse rate result"
        },
        {
            "raw_column": None,
            "sdtm_variable": "VSORRESU",
            "oak_function": "hardcode_ct",
            "ct_codelist": "C66770",
            "test_code": "PULSE",
            "tgt_val": "beats/min",
            "notes": "Pulse rate recorded in beats per minute"
        },
        {
            "raw_column": "SUBPOS",
            "sdtm_variable": "VSPOS",
            "oak_function": "assign_ct",
            "ct_codelist": "C71148",
            "test_code": "PULSE",
            "tgt_val": None,
            "notes": "Subject position during pulse measurement"
        },
    ]

    return fallback_plan


def _get_gemini_validation_explanation(llm, failed_checks):
    """
    Ask Gemini to explain the validation failures in plain English
    and suggest fixes. This is informational only -- it does not re-run anything.
    """
    if not failed_checks:
        return

    # Format the failures as a numbered list for the prompt
    failures_text = "\n".join(
        f"{i + 1}. {f.get('check', 'Unknown')}: {f.get('description', '')}"
        for i, f in enumerate(failed_checks)
    )

    filled_validation_prompt = VALIDATION_PROMPT.format(
        validation_failures=failures_text
    )

    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=filled_validation_prompt)
        ]

        response = llm.invoke(messages)
        explanation_text = response.content

        print("  Gemini's explanation of failures:")
        for line in explanation_text.splitlines()[:30]:
            print(f"    {line}")
        if len(explanation_text.splitlines()) > 30:
            print("    ... (truncated, see full response in logs)")

    except Exception as error:
        print(f"  Could not get Gemini explanation: {error}")
