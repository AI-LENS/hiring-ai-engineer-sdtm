# Submission

**Deadline: today, 18:00 (6:00 PM) IST.** Late submissions are not accepted.

## What to submit

A **single zip** (or public GitHub repo link) containing:

```
your-submission/
├── README.md           # how to run, what you built, what you'd do with more time
├── run.py              # entry point — produces vs.csv and validation_report.md
├── agent/              # your agent code (tools, prompts, control flow)
├── output/
│   ├── vs.csv          # your generated SDTM VS dataset
│   ├── generated.R     # the R script your agent produced
│   └── validation_report.md
├── requirements.txt    # or pyproject.toml / uv.lock
└── notes.md            # decisions, ambiguities you flagged, what you'd improve
```

## How to submit

Email **monomics2@gmail.com** with subject:

> `[AI Engineer Stage 2] <Your Name> — Submission`

Body must include:
- Link to public repo **or** zip attachment.
- One-paragraph summary of your approach.
- Any setup notes the reviewers need to run your code.

## README.md content (in your submission)

Keep it short. Cover:
1. **Setup** — exact commands to install and run.
2. **Architecture** — 5–10 lines on how the agent is wired (tools, planner, validator).
3. **What works** — VS tests covered, validation passes.
4. **What doesn't / what's next** — be honest.
5. **Time spent** on each phase.

## Allowed and expected

- Any AI tool (Claude Code, Cursor, Copilot, custom agents).
- Any agent framework (Anthropic SDK, OpenAI, LangGraph, CrewAI, plain function-calling, your own).
- Any Python libraries.
- Calling R via `subprocess`. You may also use `rpy2` if you prefer.

## Not allowed

- Submitting `create_vs.R` translated to Python (we check).
- Submitting code you didn't run.
- Hardcoding the golden output to pass validation.
