# SDTM VS Agent — LangChain + Google Gemini

A production-grade agentic pipeline that converts **raw clinical-trial Vital Signs data** into a **CDISC SDTM VS dataset**, orchestrating the [`sdtm.oak`](https://github.com/pharmaverse/sdtm.oak) R package as a black-box tool.

---

## What it does (4-line version)

1. **Inspects** raw VS data and the CDISC Controlled Terminology CSV (deterministic)
2. **Plans** which raw column maps to which SDTM VS variable using Gemini (LLM)
3. **Generates and runs** an R script that calls `sdtm.oak` (deterministic R builder + subprocess)
4. **Validates** the output against SDTM rules and reports what it did (deterministic + LLM summary)

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  SDTMVSAgent  (agent.py)                                       │
│                                                                │
│  Step 1 ── Inspect      inspect_raw_data()  inspect_ct()      │
│  Step 2 ── Plan         planner.plan_mappings()   [Gemini]    │
│  Step 3 ── Build R      r_script_builder.build_r_script()     │
│  Step 4 ── Run R        tools.run_r_script()   [subprocess]   │
│  Step 5 ── Validate     tools.validate_sdtm_output()          │
│  Step 6 ── Report       Gemini summarises outcome   [Gemini]  │
│                                                                │
│  Retry loop (max 2): if R fails, Gemini repairs the script.   │
└────────────────────────────────────────────────────────────────┘
```

### Files

| File | Role |
|------|------|
| `agent.py` | Orchestrator — runs all 6 steps, retry loop, CLI |
| `planner.py` | LLM-powered column→SDTM mapping planner |
| `r_script_builder.py` | Deterministic R code generator from JSON plan |
| `tools.py` | Data inspection, R executor, SDTM validator |
| `config.py` | Paths, CT code lists, model settings |
| `tests/test_tools.py` | Unit tests (no R / Gemini required) |
| `setup.sh` | One-time R + data setup |

---

## Design Decisions

### Where the LLM is used — and why

| Step | LLM? | Rationale |
|------|------|-----------|
| Inspect data | ❌ | Pure I/O — deterministic is faster and auditable |
| Plan mappings | ✅ Gemini | Column names are arbitrary (IT.TEMP, SYS_BP). Semantic intent matching is what LLMs do best |
| Build R script | ❌ | R syntax bugs from LLMs are random. Keep generation deterministic and testable |
| Run R | ❌ | subprocess — no LLM needed |
| Validate output | ❌ | CT compliance is a lookup — deterministic, not probabilistic |
| Repair broken R | ✅ Gemini | Targeted fix of syntax/API errors surfaced by stderr — bounded and logged |
| Write report | ✅ Gemini | Natural-language summarisation of structured results |

**The LLM has a narrow, typed contract.** The planner outputs a JSON schema; the builder consumes it. LLM hallucinations cannot corrupt R syntax because they never reach R directly.

### CT compliance: hard, not soft

The validator checks every CT-constrained column against `term_values` from the actual CT CSV — not a hardcoded list in Python. If the CT changes, the validator picks it up automatically.

### Retry loop is visible and bounded

The retry cap is `MAX_RETRIES = 2`. Every attempt and its outcome is printed. A silent infinite retry loop would be worse than a visible failure.

---

## Quick Start

### Prerequisites

- Python ≥ 3.10
- R ≥ 4.2 ([download](https://cran.r-project.org/))
- A [Google AI Studio API key](https://aistudio.google.com/app/apikey)

### 1 — Install R packages and export sample data

```bash
bash setup.sh
```

This installs `sdtm.oak`, `dplyr`, `pharmaverseraw`, `pharmaversesdtm`, exports
`data/vs_raw.csv` and `data/vs_golden.csv`, and downloads `data/sdtm_ct.csv`.

### 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3 — Set your API key

```bash
export GOOGLE_API_KEY="your-google-api-key-here"
```

### 4 — Run the agent

```bash
python agent.py
```

Or with explicit paths:

```bash
python agent.py \
  --raw-csv  data/vs_raw.csv \
  --ct-csv   data/sdtm_ct.csv \
  --output-csv data/vs_sdtm_output.csv \
  --study-id CDISCPILOT01
```

### 5 — Run tests (no R or API key needed)

```bash
pytest tests/test_tools.py -v
```

---

## Output

The agent writes `data/vs_sdtm_output.csv` — an SDTM VS dataset with:

| Column | Description |
|--------|-------------|
| `STUDYID` | Study identifier |
| `DOMAIN` | Always `VS` |
| `USUBJID` | Unique subject ID (`{STUDYID}-{PATNUM}`) |
| `VSTESTCD` | Test code (SYSBP, DIABP, TEMP, PULSE) |
| `VSTEST` | Test label |
| `VSORRES / VSORRESU` | Original result + unit |
| `VSSTRESC / VSSTRESN / VSSTRESU` | Standardised result (char/num) + unit |
| `VSPOS` | Body position (CT-validated) |
| `VSLOC` | Anatomical location (CT-validated, where applicable) |
| `VISIT / VSDTC` | Visit label and ISO 8601 date |

---

## Validation Checks

| Check | What it tests |
|-------|--------------|
| File exists + non-empty | R script wrote output |
| `DOMAIN == "VS"` for all rows | No stray records |
| All required columns present | SDTMIG completeness |
| No nulls in `STUDYID / USUBJID / VSTESTCD` | Identifier integrity |
| `VSTESTCD` values in C66741 | CT compliance |
| `VSPOS` values in C71148 | CT compliance |
| `VSLOC` values in C74456 | CT compliance |
| `VSSTRESU` values in C66770 | CT compliance |
| `VSSTRESN` is numeric | Type correctness |
| `VSDTC` matches ISO 8601 | Date format |

---

## Ambiguities found and resolved

| Ambiguity | Resolution |
|-----------|-----------|
| `IT.TEMP` is in Fahrenheit but SDTM expects Celsius | Planner detects unit via CT C66770; builder applies `(F − 32) × 5/9` conversion |
| Raw data has no `VISITNUM` column | Agent detects absence; sets `VISITNUM = NA` (valid SDTM optional) |
| CT CSV column names may vary in capitalisation | `inspect_ct()` normalises all column names to lowercase before parsing |
| `sdtm.oak` functions require `id_vars` on every call | `oak_id_vars()` is passed deterministically by the builder — the planner never sees this detail |

---

## What I'd do with more time

1. **Schema versioning** — pin CT release date in the output metadata so SDTM reviewers know which CDISC CT quarter was used
2. **Golden-set diff** — auto-compare output against `vs_golden.csv` and report column-by-column concordance
3. **ADaM bridge** — derive `AVAL` / `ABLFL` columns from the SDTM output as a bonus downstream step
4. **LangGraph state machine** — replace the hand-rolled retry loop with a proper graph so new steps can be inserted without touching the orchestrator
5. **Parallelise test blocks** — each VS test (TEMP, SYSBP …) is independent; run them as parallel R subprocesses for speed

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Google AI Studio key |
| `RAW_VS_CSV` | `data/vs_raw.csv` | Raw VS input path |
| `CT_CSV` | `data/sdtm_ct.csv` | CT lookup path |
| `OUTPUT_CSV` | `data/vs_sdtm_output.csv` | SDTM output path |
| `R_SCRIPT` | `scripts/generated_mapping.R` | Where to write the R script |
