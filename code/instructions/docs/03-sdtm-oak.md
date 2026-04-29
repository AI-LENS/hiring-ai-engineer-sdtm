# 03 · `sdtm.oak` — What Your Agent Calls

`sdtm.oak` is an R package that does the actual SDTM mapping. **You don't need to learn R.** Your agent generates an R script and runs it via `subprocess`. You only need to understand what goes *in* and what comes *out*.

Repo: <https://github.com/pharmaverse/sdtm.oak>

## The 3 inputs `sdtm.oak` always needs

### 1. Raw data

A CSV / data frame from the EDC. Columns reflect the form, not SDTM. Sample VS raw (from `pharmaverseraw::vs_raw`):

```
PATNUM   VISIT      IT.TEMP   IT.TEMP_LOC   SYS_BP   DIA_BP   PULSE   SUBPOS    VSDAT
375      Screening  98.6      ORAL CAVITY   120      80       72      SITTING   2020-01-15
375      Week 2     99.1      ORAL CAVITY   118      78       70      SITTING   2020-01-29
```

One row = one CRF page filled at one visit. Multiple measurements live in *columns*. SDTM wants them in *rows* — so part of the job is reshaping wide → long.

### 2. Study Controlled Terminology (`study_ct.csv`)

A lookup table that says, for every variable that has a controlled vocabulary, which CDISC code list applies and what the allowed values are. See [`04-sdtm-ct.md`](./04-sdtm-ct.md) for structure.

### 3. The `sdtm.oak` mapping functions (the agent's tool vocabulary)

Five functions cover almost all of VS:

| Function | What it does | Example |
|---|---|---|
| `assign_no_ct()` | Copy raw value to target as-is | `VSORRES ← IT.TEMP` |
| `assign_ct()` | Copy raw value, normalized via CT lookup | `VSPOS ← SUBPOS` (`Supine` → `SUPINE`) |
| `hardcode_no_ct()` | Set a constant | `VSDRVFL ← "Y"` |
| `hardcode_ct()` | Set a constant, validated against CT | `VSTESTCD ← "TEMP"` (in code list `C66741`) |
| `condition_add()` | Filter raw data inline before mapping | only set `VSLOC` where `IT.TEMP` is not missing |

Plus two helpers:

- `generate_oak_id_vars(pat_var = "PATNUM", raw_src = "vitals")` — adds lineage IDs to the raw data.
- `oak_id_vars()` — pass to `id_vars =` so each mapping joins on the same lineage keys.

## The pattern (this is the whole game)

For each VS test (`TEMP`, `SYSBP`, `DIABP`, `PULSE`, ...), build a small pipeline:

```
raw_data
  → hardcode_ct(VSTESTCD = "TEMP",  ct_clst = "C66741")
  → filter VSTESTCD not missing
  → hardcode_ct(VSTEST   = "Temperature", ct_clst = "C67153")
  → assign_no_ct(VSORRES ← IT.TEMP)
  → hardcode_ct(VSORRESU = "F", ct_clst = "C66770")
  → assign_ct(VSLOC ← IT.TEMP_LOC, ct_clst = "C74456")
  → derive VSSTRESC = (VSORRES − 32) × 5/9       # F → C
  → hardcode_ct(VSSTRESU = "C", ct_clst = "C66770")
```

Then row-bind all per-test pipelines and apply common variables (`STUDYID`, `USUBJID`, dates, sequence) at the end.

## Why this is an agent problem

The pattern is repetitive, rule-bound, and verifiable — perfect for an agent if you frame it well. **The agent's job: read the inputs, decide which function applies for each target variable, generate the R script, run it, validate the output.**

Next: [`04-sdtm-ct.md`](./04-sdtm-ct.md).
