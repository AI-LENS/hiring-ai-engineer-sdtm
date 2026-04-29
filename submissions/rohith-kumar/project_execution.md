# Project Execution Report: SDTM VS Mapping Agent

## Overview
This document outlines the implementation, methodology, and technical challenges encountered during the development of the Agentic AI pipeline for clinical trial data standardization.

## Implementation Details
The project is built as a **5-Phase Pipeline** designed to orchestrate the `sdtm.oak` R package via Python to convert raw Vital Signs (VS) data into CDISC-standard SDTM format.

### Key Components Implemented:
* **Orchestration Layer (`run.py`):** A centralized coordinator that manages data flow between Python and R, handles environment auto-detection (locating `Rscript`), and triggers validation.
* **Planning Agent (`agent/mapper.py`):** An LLM-powered engine (using Llama-3 via Groq) that interprets raw data schemas and translates them into functional R mapping code.
* **Validation Suite (`agent/validator.py`):** A post-execution utility that performs automated checks against Controlled Terminology (CT), verifies required SDTM columns, and conducts a row-level diff against "golden" reference data.
* **Output Management:** A structured directory system to ensure `generated.R`, `vs.csv`, and `validation_report.md` are captured and persisted.

## Methodology & Approach
The core philosophy behind this implementation is **"Clarity over Complexity."** Instead of building a rigid hard-coded script, the approach focused on creating a **Dynamic Planning Loop**.

1.  **Context-Rich Prompting:** The agent is fed the specific function signatures of `sdtm.oak` and explicit rules (e.g., forbidding `sdtm.oak` inside `mutate()`) to ensure the generated code is syntactically compatible with tidyverse pipes (`%>%`).
2.  **Explicit Data Binding:** To address R's functional requirements, the approach forces the agent to use explicit data binding (`raw_dat = .`) in every pipe step.
3.  **Hybrid Orchestration:** The agent uses `sdtm.oak` for domain-specific clinical mappings (like `hardcode_ct`) while leveraging `dplyr` for structural tasks like filtering, binding rows, and sequence generation (`VSSEQ`).
4.  **Sequential Validation:** The pipeline is strictly ordered; validation only occurs if the R execution succeeds, ensuring the `validation_report.md` reflects true output.

## Encountered Errors & Resolution
During the iterative development of the agent, several critical execution errors were identified and addressed:

### 1. R Environment & Pathing Errors
* **Error:** `FileNotFoundError: [WinError 2] The system cannot find the file specified`.
* **Context:** Python was unable to locate the `Rscript` executable on the Windows PATH.
* **Resolution:** Implemented an auto-detection logic in `run.py` to scan common installation directories and allow for manual path overrides.

### 2. Functional Signature Mismatches
* **Error:** `Argument raw_dat must be class <data.frame>, but is a string`.
* **Context:** The LLM was incorrectly placing an empty string `""` as the first argument in `hardcode_ct` instead of allowing the pipe to pass the dataframe.
* **Resolution:** Refined the system prompt to enforce the pipe-compatible signature where the dataframe is handled implicitly.

### 3. Missing Mandatory ID Variables
* **Error:** `Required variables oak_id, raw_source, and patient_number are missing in raw_dat`.
* **Context:** `sdtm.oak` requires internal lineage variables to be initialized before mapping.
* **Resolution:** Added a mandatory initialization phase in the agent's planning logic using `generate_oak_id_vars()`.

### 4. Argument Mapping Logic
* **Error:** `argument "raw_var" is missing, with no default`.
* **Context:** In certain versions of the package, `hardcode_ct` insists on a `raw_var` parameter even when hardcoding values.
* **Resolution:** Standardized the agent to provide `raw_var = ""` as a placeholder to satisfy the package's internal validation.