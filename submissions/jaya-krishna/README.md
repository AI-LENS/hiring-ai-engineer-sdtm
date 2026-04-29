\# SDTM Vital Signs Automation Agent



An AI-powered data engineering pipeline designed to automate the transformation of raw clinical vital signs data into a CDISC-compliant SDTM (`VS`) dataset. 



This project utilizes a \*\*Cyclic LangGraph State Machine\*\* powered by Google's `gemini-1.5-flash` model. The AI agent acts as an orchestrator, writing, executing, and mathematically validating deterministic R code using the `sdtm.oak` package.



\## 🏗️ Architecture



To ensure strict data integrity and eliminate LLM hallucinations, the pipeline separates probabilistic reasoning from deterministic execution:



1\. \*\*The Brain (LangGraph + Gemini 1.5 Flash):\*\* Manages the state, decides which tools to call, and interprets compilation or validation errors to self-correct code.

2\. \*\*The Hands (Python Subprocesses):\*\* Securely writes R code to disk and triggers isolated execution.

3\. \*\*The Engine (R + sdtm.oak):\*\* Performs the actual data mapping, utilizing `generate\_oak\_id\_vars()`, `assign\_no\_ct()`, and `hardcode\_ct()` to map data directly into long-format SDTM.

4\. \*\*The Judge (Pandas Validation):\*\* Mathematically validates the output against SDTM structural requirements and CDISC Controlled Terminology (Codelists: C66741, C67153, C66770).



\### Execution Flow

1\. \*\*`get\_data\_schemas`\*\*: Reads raw data headers and exact Controlled Terminology rules.

2\. \*\*`execute\_r\_script`\*\*: Injects a canonical `sdtm.oak` mapping script, anchors the working directory, and runs the R subprocess.

3\. \*\*`validate\_sdtm\_output`\*\*: Checks for missing values, mandatory columns, and strict CT alignment.

4\. \*\*Self-Correction Loop\*\*: If validation fails, the agent reads the `stderr`, updates the code, and cycles back to step 2 (capped at a `MAX\_ITERATIONS` limit to prevent infinite loops).



\---



\## 📂 Project Structure



```text

hiring-ai-engineer-sdtm/

├── agent/                   # Core agentic logic

│   ├── graph.py             # LangGraph state machine \& LLM routing

│   └── tools.py             # Python-to-R tool definitions and validation logic

├── csv\_files/               # Input data dependencies

│   ├── vs\_raw.csv           # Raw source data

│   ├── sdtm\_ct.csv          # CDISC Controlled Terminology lookup

│   └── vs\_golden.csv        # Expected outcome (for reference)

├── output/                  # Generated artifacts (created at runtime)

│   ├── vs.csv               # The final SDTM dataset

│   ├── generated.R          # The R script executed by the agent

│   └── validation\_report.md # CT compliance and shape metrics

├── .env                     # Private environment variables (API keys)

├── requirements.txt         # Python dependencies

├── run.py                   # Main execution entry point

└── notes.md                 # Execution monologue and reasoning log

