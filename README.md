# AI LENS — AI Engineer Hiring (Round 2 / Live Build)

Build an **agentic AI in Python** that converts raw clinical-trial vital-signs data into a CDISC-standard SDTM `VS` dataset, using the `sdtm.oak` R package as a black-box tool.

---

## At a glance

| | |
|---|---|
| **Role** | AI Engineer |
| **Round** | Round 2 — Live Agentic Build |
| **You write** | **Python.** No R or SAS knowledge required. |
| **You orchestrate** | An agent that calls `sdtm.oak` (R) via subprocess. |
| **Submission deadline** | **Today, 18:00 (6:00 PM) IST** |
| **How to submit** | See [`SUBMISSION.md`](./SUBMISSION.md) |

---

## What you actually build (in 4 lines)

1. An **agent** (Claude / OpenAI / LangGraph / Claude Agent SDK / your choice) that reads three inputs: raw VS data, an SDTM CT lookup CSV, and a list of `sdtm.oak` mapping functions.
2. The agent **plans** how to map each raw column to SDTM `VS` variables.
3. The agent **generates and runs an R script** that calls `sdtm.oak`. (Treat R as a tool, not a language to learn.)
4. The agent **validates** the output against SDTM rules and reports what it did.

You are graded on how you design the agent — not how well you write R.

---

## Read in this order (≈ 25 minutes total)

1. [`docs/01-clinical-trials.md`](./docs/01-clinical-trials.md) — what a clinical trial is, in plain English.
2. [`docs/02-data-flow.md`](./docs/02-data-flow.md) — Protocol → CRF → Raw → SDTM → ADaM → TFLs.
3. [`docs/03-sdtm-oak.md`](./docs/03-sdtm-oak.md) — the 3 inputs and 5 functions you need to understand.
4. [`docs/04-sdtm-ct.md`](./docs/04-sdtm-ct.md) — what the controlled-terminology CSV looks like.
5. [`docs/05-task.md`](./docs/05-task.md) — **the task itself.**
6. [`EVALUATION.md`](./EVALUATION.md) — how we grade.
7. [`SUBMISSION.md`](./SUBMISSION.md) — how to submit.

## Pre-work (do BEFORE the build window)

- Watch the intro video — pharmaverse `sdtm.oak` workshop walkthrough (≈ 30 min): <https://www.youtube.com/watch?v=t62MICj_5Ng>
- Skim the canonical R reference (you don't need to understand R syntax — just the *shape* of what's happening): <https://github.com/pharmaverse/sdtm.oak-workshop/blob/main/scripts/create_vs.R>
- Install R + the workshop packages so subprocess calls work on the day. Setup commands are in [`docs/05-task.md`](./docs/05-task.md).
- Pick your agent stack and have it working locally with API keys ready.

> ⚠️ Do **not** open `create_vs.R` and ask an AI to "rewrite this in Python." That defeats the round. We want an *agent* that reasons about the inputs, plans the mappings, and produces the R script itself.

## Questions during the build

Ask. Ambiguity is normal in clinical specs. Asking is a strength.
