# Developer Notes -- SDTM VS Agent

These notes document the decisions made, ambiguities encountered, and ideas for improvement
during the development of this agent. A future developer (or reviewer) should be able to
read this and understand why the code is structured the way it is.

---

## Decision 1 -- Why Gemini 2.5 Flash Was Chosen

Gemini 1.5 Flash was chosen over GPT-4 for several practical reasons:

First, the task is primarily a structured data-to-data mapping problem, not an open-ended
reasoning problem. Gemini 1.5 Flash is fast and accurate at structured tasks like producing
JSON output with specific keys and following a detailed template. GPT-4 would also work,
but it costs more and is slower for the same type of structured output.

Second, Google provides a free tier for Gemini API access via Google AI Studio, which
makes this project easier to set up and evaluate without billing requirements. The
LangChain integration via `langchain-google-genai` is well maintained and straightforward.

Third, the `temperature=0` setting makes the output deterministic. For clinical data
mapping, we want the same mapping plan every time, not creative variation. Flash
handles this well at zero temperature.

If GPT-4 is preferred, the only change needed is replacing `ChatGoogleGenerativeAI` with
`ChatOpenAI` in planner.py and swapping the `GOOGLE_API_KEY` for `OPENAI_API_KEY`.

---

## Decision 2 -- Why a Fallback Hardcoded Mapping Plan Exists

The agent includes a hardcoded fallback mapping plan that activates when Gemini is
unavailable or returns a response that cannot be parsed as valid JSON.

This decision was made because the goal of the project is to produce a correct SDTM VS
dataset. If Gemini is down or returns malformed output, the agent should still produce
a result rather than crashing with an unhelpful error. The fallback plan is based on
the well-known pharmaverse vs_raw column names and matches the expected transformation.

The fallback also serves as a specification document -- it shows exactly what mappings
are expected. If Gemini's output is very different from the fallback, that is a signal
that the prompt may need adjustment.

The fallback is NOT silently substituted. When it activates, the planner logs a clear
warning message saying "Using the safe fallback hardcoded mapping plan" so the developer
knows Gemini did not drive the decision for this run.

---

## Decision 3 -- Ambiguity: VSLOC Only for Temperature

Only the temperature test (TEMP) has a location column in the raw data (`IT.TEMP_LOC`).
Blood pressure (SYSBP, DIABP) and pulse rate (PULSE) do not have corresponding location
columns in the raw CRF.

This is a real clinical trial design decision. Temperature can be measured at different
body sites (oral, axillary, tympanic), so the location is captured. Blood pressure and
pulse measurements are taken at a single standard site (the upper arm), so no location
column is provided.

In the generated SDTM output, VSLOC is populated only for TEMP rows. For SYSBP, DIABP,
and PULSE rows, VSLOC is null. The validator is written to accept null VSLOC values and
only checks that non-null values are in the CT codelist C74456. This is the correct
SDTM behavior.

---

## Decision 4 -- Why Temperature Needs Unit Conversion

The raw vital signs data records temperature in Fahrenheit (`IT.TEMP` column).
The SDTM standard requires VSSTRESC (standardized result) and VSSTRESU (standardized unit)
to use the international standard unit for temperature, which is Celsius.

The conversion formula is: Celsius = (Fahrenheit - 32) * 5 / 9

The result is rounded to 1 decimal place to avoid spurious precision from the conversion.
For example, 98.6 F converts to 37.0 C, not 36.999999... C.

VSORRES and VSORRESU still record the original Fahrenheit value as measured, following
the SDTM principle that the original observation should be preserved in VSORRES.

---

## Decision 5 -- Why VSSTRESC Equals VSORRES for BP and Pulse

Blood pressure (mmHg) and pulse rate (beats/min) are already recorded in their standard
international units. No conversion is required.

SDTM requires VSSTRESC to hold the result in the standard unit and VSSTRESU to hold
the standard unit. When VSORRES is already in standard units, VSSTRESC is simply a
character copy of VSORRES and VSSTRESU equals VSORRESU.

This is different from temperature where a unit conversion is needed.

---

## Decision 6 -- Kaggle Dataset Search Strategy

The kagglehub library returns a local folder path after downloading a dataset.
The exact filename inside that folder is not guaranteed and may change between
versions of the dataset.

The `setup_data.py` script handles this by searching the downloaded folder for
files matching several naming patterns in priority order:

1. Files with "vs_raw" in the name (exact match preferred)
2. Files with "vs" and "raw" in the name
3. Files starting with "vs" in the name
4. Any available CSV as a last resort

For the golden reference, the search looks for:
1. Files with "golden", "vs_golden", or "pharmaversesdtm" in the name
2. Files with "vs_sdtm" or "sdtm_vs" in the name
3. Any vs.csv that is not the raw file

If no match is found, the script prints all available CSV files so the developer
can identify the correct file manually. An empty placeholder file is created so the
rest of the pipeline can still run without crashing.

---

## What I Would Improve With More Time

**Add HEIGHT and WEIGHT tests**

The pharmaverse vs_raw dataset may have height and weight columns depending on the
version. These tests follow the same sdtm.oak pattern as the other four tests.
They would need their own unit conversion logic (e.g., lbs to kg, inches to cm)
and would require confirming the raw column names from the actual downloaded dataset.

**Fix VSSEQ edge cases**

The current VSSEQ logic uses `row_number()` grouped by USUBJID. This works correctly
when rows are in a consistent order, but if the same patient has the same test at the
same visit (duplicate measurements), VSSEQ may not be unique. A more robust approach
would sort by VSDTC and VSTESTCD before assigning sequence numbers.

**Add unit tests for the validator**

Each validation check in `agent/validator.py` should have at least one passing and
one failing test case. This would make it safe to modify the validator without
accidentally breaking existing checks.

**Add R package auto-installation**

If the R script fails because sdtm.oak or dplyr is not installed, the agent should
detect this from the error message and offer to auto-install the missing packages
with `install.packages` before retrying. Currently the developer must install R
packages manually.

**Make test definitions configurable**

The test definitions in `codegen.py` (which raw columns map to which SDTM variables)
are currently hardcoded in a Python list. Moving these to a YAML configuration file
would make it easier to add new tests or handle different raw data column names
without changing Python code.
