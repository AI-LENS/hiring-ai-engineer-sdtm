# 05 · The Task

Build a **Python agent** that takes raw VS data + a CT CSV and produces an SDTM `VS` dataset by orchestrating `sdtm.oak`.

## Deadline

**Today, 18:00 (6:00 PM) IST.** Submit per [`SUBMISSION.md`](../SUBMISSION.md).

## Inputs (you fetch these yourself)

| Input | Where | Notes |
|---|---|---|
| Raw VS data | `pharmaverseraw::vs_raw` (R package) — or export it to CSV via the R one-liner below | ~100 rows of vital signs |
| Study CT | <https://raw.githubusercontent.com/pharmaverse/sdtm.oak-workshop/main/datasets/sdtm_ct.csv> | The lookup table |
| Reference VS aCRF (PDF) | <https://github.com/pharmaverse/sdtm.oak-workshop/blob/main/specs/vs/VITALSIGNS_aCRF.pdf> | Tells you which raw column maps to which SDTM variable |
| Reference R script | <https://github.com/pharmaverse/sdtm.oak-workshop/blob/main/scripts/create_vs.R> | The human-written version. **Don't copy it. Use it for sanity-checking only.** |
| Expected output (golden) | `pharmaversesdtm::vs` | What a correct SDTM VS looks like |

### One-time setup (do before the build window)

```bash
# 1) Install R from https://cran.r-project.org/  (macOS: brew install r)

# 2) Install the R packages
Rscript -e 'install.packages(c("sdtm.oak","dplyr","remotes"), repos="https://cloud.r-project.org")'
Rscript -e 'remotes::install_github("pharmaverse/pharmaverseraw")'
Rscript -e 'remotes::install_github("pharmaverse/pharmaversesdtm")'

# 3) Export the raw and golden datasets to CSV so Python can see them
Rscript -e 'write.csv(pharmaverseraw::vs_raw, "vs_raw.csv", row.names=FALSE)'
Rscript -e 'write.csv(pharmaversesdtm::vs, "vs_golden.csv", row.names=FALSE)'

# 4) Python — whatever venv/poetry/uv setup you prefer
pip install anthropic pandas  # or openai, langgraph, etc.
```

## The build

Build a Python agent that:

1. **Reads** `vs_raw.csv`, `sdtm_ct.csv`, and a description of the 5 `sdtm.oak` functions (Doc [`03-sdtm-oak.md`](./03-sdtm-oak.md) is yours to feed it).
2. **Plans** the mapping for each VS test (TEMP, SYSBP, DIABP, PULSE, ...): which raw column → which SDTM variable, which `sdtm.oak` function applies, which CT code list to use.
3. **Generates an R script** that calls `sdtm.oak` and writes `vs.csv`.
4. **Runs the script** via `subprocess.run(["Rscript", ...])`.
5. **Validates** the output:
   - All CT-controlled variables only contain valid `term_value`s.
   - Required variables present (`STUDYID`, `USUBJID`, `VSTESTCD`, `VSORRES`, ...).
   - Row count is reasonable (long format: more rows than raw, because each test becomes a row).
   - Diff against `vs_golden.csv` and report mismatches.
6. **Reports** what it did — which mappings it chose, where it was uncertain, what it skipped.

### Minimum scope (must do)

Cover at least **TEMP, SYSBP, DIABP, PULSE** end-to-end through `VSORRES` / `VSORRESU` / `VSSTRESC` / `VSSTRESU` / `VSPOS` (where applicable) / `VSLOC` (where applicable).

### Stretch (do if time)

- Add `HEIGHT` and `WEIGHT`.
- Derive `VSSEQ` (per-subject sequence).
- Construct `USUBJID` from `STUDYID` + `PATNUM`.
- Convert dates to ISO 8601 `VSDTC`.
- Wire visit info (`VISIT`, `VISITNUM`).

## Clarity over complexity

If you find yourself adding a fourth abstraction layer, an extra agent, or a fancier framework feature — stop and ask whether your existing code reads clearly. Reviewers reward solutions they can follow. A flat, well-named pipeline beats a clever graph almost every time in this exercise.

## What we don't want

- A Python rewrite of `create_vs.R` with no agent loop.
- Hand-coded mappings hidden behind an LLM call (`prompt = "here is the answer, format it"`).
- Skipping validation. We *will* run your output through SDTM checks.

## What we do want

- A clear agent design — tool definitions, prompts, control flow.
- Visible reasoning — your agent should log its decisions.
- Honest validation — when something is wrong, the agent should *say so*, not silently pass.
- A working `python run.py` (or equivalent) that produces `vs.csv` and a validation report.

Now read [`../EVALUATION.md`](../EVALUATION.md) and [`../SUBMISSION.md`](../SUBMISSION.md).
