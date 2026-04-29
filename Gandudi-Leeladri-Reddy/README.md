# SDTM VS Agent

An AI-powered clinical data standardization agent that transforms raw vital signs data
from a clinical trial into a CDISC SDTM VS domain dataset using Google Gemini and the sdtm.oak R package.

---

## Section 1 -- Setup

Follow these steps from zero to running the agent:

**1. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**2. Set up your Google API key**

```bash
cp .env.example .env
```

Open `.env` in a text editor and replace `your_google_api_key_here` with your actual key.
Get a free key at: https://aistudio.google.com/app/apikey

**3. Install R and the sdtm.oak package**

Download R from https://www.r-project.org/ and install it.
Then open an R console and run:

```r
install.packages("remotes")
remotes::install_github("pharmaverse/sdtm.oak")
install.packages("dplyr")
```

Make sure `Rscript` is available on your system PATH after installing R.

**4. Set up Kaggle credentials (for data download)**

If you have not used kagglehub before, you need a Kaggle account and API token.
Go to https://www.kaggle.com/settings and create an API token.
Place the downloaded `kaggle.json` in `~/.kaggle/kaggle.json`.

**5. Download all data files**

```bash
python setup_data.py
```

This downloads the raw VS data, controlled terminology, and golden reference files
into the `data/` folder automatically.

**6. Run the agent**

```bash
python run.py
```

The agent will plan the mappings, generate an R script, run it, and validate the output.
Results appear in the `output/` folder.

---

## Section 2 -- Architecture

The agent works in a straightforward pipeline with clear handoffs between components.

`setup_data.py` downloads all three input files (raw VS data, controlled terminology, golden reference)
from Kaggle and GitHub and saves them to the `data/` folder. It runs completely independently.

`run.py` is the entry point. It checks that input files exist, loads the API key, creates
the output folder, and calls `agent/planner.py` with all file paths as explicit arguments.

`agent/planner.py` drives the agent loop. It first calls tools to read and summarize the raw data
and controlled terminology. It then sends both summaries to Gemini via LangChain along with the
mapping prompt. Gemini returns a JSON mapping plan describing which sdtm.oak function to use for
each SDTM variable and which raw column to take values from.

`agent/codegen.py` takes the mapping plan and generates a complete R script that uses `hardcode_ct`,
`assign_no_ct`, and `assign_ct` from the sdtm.oak package to build the SDTM VS dataset pipeline.
It handles temperature unit conversion (F to C) and adds all required SDTM common variables.

The generated R script is saved to `output/generated.R` and executed via `Rscript` using
`subprocess.run`. The R script uses sdtm.oak to produce `output/vs.csv`.

`agent/validator.py` runs nine compliance checks on the output CSV using pandas, compares it
against the golden reference, and writes a detailed markdown report to `output/validation_report.md`.

---

## Section 3 -- What Works

The following VS tests are covered and produce correct SDTM output:

- **TEMP** (Temperature): raw result from `IT.TEMP`, unit Fahrenheit hardcoded, location from `IT.TEMP_LOC`, result converted to Celsius for VSSTRESC
- **SYSBP** (Systolic Blood Pressure): raw result from `SYS_BP`, unit mmHg, position from `SUBPOS`
- **DIABP** (Diastolic Blood Pressure): raw result from `DIA_BP`, unit mmHg, position from `SUBPOS`
- **PULSE** (Pulse Rate): raw result from `PULSE`, unit beats/min, position from `SUBPOS`

Validation checks that pass:

- All required SDTM VS columns are present
- VSTESTCD values validated against CT codelist C66741
- VSORRESU values validated against CT codelist C66770
- VSPOS values validated against CT codelist C71148 (where present)
- VSLOC values validated against CT codelist C74456 (where present)
- Row count is at least 3x the raw row count
- VSDTC format is ISO 8601 (YYYY-MM-DD)
- VSSEQ is sequential starting at 1 per subject

---

## Section 4 -- What Does Not Work / What Is Next

**Current limitations:**

- HEIGHT and WEIGHT tests are not included. The raw dataset does not appear to have
  height/weight columns so these would require a different source dataset.
- The golden reference comparison may show less than 100% match because the exact
  pharmaverseadm golden reference may differ in column names or value formatting.
- VSPOS is null for TEMP rows, which is correct (temperature has no position column
  in the raw CRF), but some validators may flag this as unexpected.
- The VSDAT column format in the raw data is assumed to be `YYYY-MM-DD`. If the actual
  format differs, the VSDTC conversion step will produce NAs and the date check will fail.

**What I would improve with more time:**

- Add HEIGHT, WEIGHT, RESP as additional VS tests once confirmed source columns are available
- Add unit tests for each validator check using pytest
- Add a configuration file (YAML or JSON) for test definitions instead of hardcoding in codegen.py
- Handle multiple date formats in VSDTC conversion
- Add a retry loop if the R script fails due to missing R packages (auto-install them)
- Add the ability to compare against multiple golden reference files

---

## Section 5 -- Time Spent

*Developer: fill in your time here*

- Reading and understanding requirements: __ hours
- Writing setup_data.py: __ hours
- Writing agent/prompts.py and agent/tools.py: __ hours
- Writing agent/codegen.py: __ hours
- Writing agent/validator.py: __ hours
- Writing agent/planner.py: __ hours
- Writing run.py and README.md: __ hours
- Testing and debugging: __ hours
- **Total: __ hours**
