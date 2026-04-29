"""
agent/prompts.py

All LLM prompt templates are stored here as plain Python string constants.
No f-strings at this level. Placeholders use {variable_name} format.
They get filled in by the planner when it calls the LLM.

Keeping all prompts in one file makes them easy to find, review, and update
without digging through application logic.
"""


# This prompt tells Gemini what role it is playing and what tools it has available.
# It is sent as the system message before any user messages.
SYSTEM_PROMPT = """
You are a clinical data mapping expert specializing in CDISC SDTM standards.
Your job is to map raw clinical trial vital signs data into the SDTM VS domain
using the sdtm.oak R package.

You have access to five sdtm.oak functions. Here is what each one does:

1. hardcode_ct
   Use this when the target value is a fixed string that must be validated
   against a controlled terminology (CT) code list.
   Example: hardcoding VSTESTCD = "TEMP" where "TEMP" must be in code list C66741.

2. assign_no_ct
   Use this when you want to copy a value directly from a raw column into
   an SDTM variable without any controlled terminology validation.
   Example: copying IT.TEMP into VSORRES as a free-text result.

3. assign_ct
   Use this when you want to copy a value from a raw column but the value
   must be validated against a controlled terminology code list.
   Example: mapping IT.TEMP_LOC to VSLOC where values must be in code list C74456.

4. hardcode_no_ct
   Use this when the target value is a fixed string that does NOT need
   CT validation. Use sparingly -- prefer hardcode_ct when a code list exists.

5. generate_oak_id_vars
   Use this once at the start to add tracking columns (oak_id_vars) to the
   raw dataset so sdtm.oak can trace each output row back to its source row.

The output must follow SDTM VS domain rules:
- VSTESTCD values must be short codes like TEMP, SYSBP, DIABP, PULSE
- VSTEST values are the full descriptive name like Temperature, Systolic Blood Pressure
- VSORRES is the result as recorded in the raw data
- VSSTRESC is the result in standard units (Celsius for temperature, same value for BP and pulse)
- VSSTRESU is the standardized unit (C for temperature, mmHg for BP, beats/min for pulse)
"""


# This prompt asks Gemini to produce a structured JSON mapping plan
# given what it finds in the raw data and controlled terminology files.
# The planner fills in {raw_columns}, {sdtm_target_variables}, and {ct_summary}
# before sending this to the LLM.
MAPPING_PROMPT = """
You are mapping raw clinical vital signs data to the SDTM VS domain.

Raw data columns available:
{raw_columns}

Sample of raw data (first 3 rows):
{raw_sample}

Controlled terminology code lists available:
{ct_summary}

Target SDTM variables to populate:
{sdtm_target_variables}

Your task is to produce a detailed mapping plan as a JSON array.
Each element in the array represents one mapping operation.

Rules:
- VSTESTCD must use hardcode_ct with code list C66741 (VSTESTCD = TEMP, SYSBP, DIABP, PULSE)
- VSTEST must use hardcode_ct with code list C67153 (full test name)
- VSORRES must use assign_no_ct to copy from the matching raw column
- VSORRESU must use hardcode_ct with code list C66770 (unit code)
- VSSTRESC is the standardized result (for temperature, convert F to C; for others copy VSORRES)
- VSSTRESU is the standardized unit with code list C66770
- VSLOC only applies to temperature, use assign_ct with code list C74456
- VSPOS applies to blood pressure and pulse, use assign_ct with code list C71148 from SUBPOS column

Return ONLY a valid JSON array. No explanation text, no markdown, no code blocks.
Just the raw JSON array starting with [ and ending with ].

Each element must have these exact keys:
{{
  "raw_column": "the raw CSV column to use, or null if hardcoded",
  "sdtm_variable": "the SDTM target column name",
  "oak_function": "hardcode_ct or assign_no_ct or assign_ct or hardcode_no_ct",
  "ct_codelist": "the code list code like C66741 or null",
  "test_code": "the VSTESTCD value this mapping belongs to like TEMP or SYSBP",
  "tgt_val": "the hardcoded target value if oak_function is hardcode_ct or hardcode_no_ct, else null",
  "notes": "any uncertainty or special handling needed"
}}

Include mappings for all four tests: TEMP, SYSBP, DIABP, PULSE.
"""


# This prompt is used when the validator finds failures.
# It asks Gemini to explain each failure in plain English and suggest a fix.
# The planner fills in {validation_failures} before sending to the LLM.
VALIDATION_PROMPT = """
The SDTM VS dataset produced by the agent has the following validation failures:

{validation_failures}

For each failure listed above, please:
1. Explain in plain English what the failure means and why it matters for SDTM compliance
2. Suggest a specific fix that would resolve the failure
3. If the failure is expected (like VSPOS being empty for temperature rows), say so

Format your response as a numbered list matching the order of the failures above.
Be specific and practical. A junior developer should be able to read your explanation
and know exactly what to change in the R script or mapping plan to fix it.
"""
