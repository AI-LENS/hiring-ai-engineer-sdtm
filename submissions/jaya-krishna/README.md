cls# SDTM Vital Signs Automation Agent

## Setup
Ensure you have Python 3.10+ and R 4.0+ installed.
1. Add your API key to a `.env` file: `GOOGLE_API_KEY=your_key`
2. Create and activate a virtual environment: `python -m venv venv` & `.\venv\Scripts\activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the pipeline: `python run.py`
*(Note: The script will automatically download necessary R packages via subprocess if missing).*

## Architecture
This agent utilizes a **Cyclic LangGraph State Machine** powered by Gemini 1.5 Flash. It strictly separates probabilistic reasoning from deterministic execution. The AI acts as an orchestrator: it reads schemas via a tool, injects a canonical `sdtm.oak` script, executes it via a Python subprocess, and relies on a strict Pandas-based validation tool to mathematically grade the output. If validation fails, the agent reads the `stderr`, updates the code, and loops until success (capped at 5 iterations).

## What Works
* The agent successfully maps all required VS tests (TEMP, SYSBP, DIABP, PULSE).
* Full CDISC Controlled Terminology compliance for C66741 (VSTESTCD), C67153 (VSTEST), and C66770 (VSORRESU).
* Mathematical validation passes, ensuring exact row counts and no missing mandatory SDTM variables.

## What Doesn't / What's Next
* **Dynamic R Generation:** Currently, the agent relies on an injected canonical script to prevent hallucinating non-existent `sdtm.oak` functions. The next step is feeding the agent the raw PDF aCRF specs so it can generate the R mapping syntax entirely from scratch.
* **Domain Agnosticism:** The validator currently hardcodes VS-specific codelists. A production version would dynamically fetch rules based on the target domain (DM, AE, etc.).

## Time Spent (Approx. 6.5 Hours)
* **Setup & R Environment config:** ~1.5 hour
* **Agent Flow & LangGraph Architecture:** ~1.5 hours
* **R Subprocess & Pandas Validation Logic:** ~1.5 hours
* **Debugging & Pipeline Hardening:** ~1.5 minutes