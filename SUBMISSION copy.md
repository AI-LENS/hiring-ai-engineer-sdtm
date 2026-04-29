# SUBMISSION.md — Agent Design Write-up

## What the agent does

The agent converts raw VS clinical-trial data into an SDTM VS dataset by running
six deterministic + LLM steps in sequence:

1. **Inspect** — reads raw CSV columns, dtypes, nulls; reads CT code-list structure
2. **Plan** — Gemini analyses column names semantically and returns a typed JSON mapping plan
3. **Build R** — a deterministic Python function turns the JSON plan into a valid sdtm.oak R script
4. **Run R** — subprocess call to `Rscript`; stderr is captured and surfaced, never swallowed
5. **Validate** — Python checks CT compliance, required columns, ISO dates, numeric types
6. **Report** — Gemini writes a plain-English summary of what worked and what needs attention

## Where I used LLM reasoning vs. deterministic code

| Decision point | Choice | Why |
|----------------|--------|-----|
| Column→SDTM variable matching | **LLM** | "IT.TEMP" → TEMP requires semantic inference, not regex |
| R script generation | **Deterministic** | LLM R-code has random syntax bugs; a template is reproducible |
| CT value validation | **Deterministic** | It's a lookup table — probabilistic is wrong here |
| R error repair | **LLM** | Targeted, bounded, fully logged; max 2 retries |
| Final report | **LLM** | Structured data → natural language is an LLM strength |

## What I'm uncertain about

- **VISITNUM**: the raw data from `pharmaverseraw::vs_raw` may not have a numeric visit column. The agent sets it to `NA` (valid per SDTMIG optional rules) but a reviewer might prefer `VISITNUM` derived from visit order.
- **F → C conversion**: the planner infers this from the CT (F is a collected value for C66770) but if a site collects temperature in Celsius the same column could arrive pre-converted. A real pipeline would add a unit-detection heuristic.
- **sdtm.oak API surface**: the five functions documented in the task spec are what I've used. The real package has more; a more complete implementation would handle `derive_vars_merged()` for EPOCH, for example.

## What I'd do with more time

See README.md — section "What I'd do with more time".

## Hard fails I avoided

- ✅ No values outside CT code lists in the output (validator catches this)
- ✅ Not a single giant prompt — clear separation of planner / builder / validator
- ✅ Did not copy `create_vs.R` — the R script is generated from a JSON plan, not translated line-by-line
