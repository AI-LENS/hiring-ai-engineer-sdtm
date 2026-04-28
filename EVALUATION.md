# Evaluation Criteria

> **Guiding principle: clarity is preferred over complexity.**
> A simple, readable agent that handles four VS tests correctly and explains its reasoning will outscore a clever multi-layer system whose behaviour reviewers cannot follow. If you have to choose between adding a feature and making your existing work easier to read, choose readability.

We grade on six dimensions. Each is weighted equally unless noted.

| # | Dimension | What we look for |
|---|---|---|
| 1 | **Critical problem solving** | Did you decompose the problem correctly? Did you spot the highest-risk pieces (CT lookup, wide→long reshape, validation) and tackle them first? When something didn't work, did you debug it methodically? |
| 2 | **Problem-statement comprehension** | Did you understand what SDTM is, what `sdtm.oak` does, what the 3 inputs are, and why the agent design matters? Or did you skip to coding without grounding? Asking clarifying questions counts in your favor. |
| 3 | **Agent design quality** | Clean separation between tools, planner, validator. Sensible prompts. Reasonable tool surface. Not just one giant prompt. |
| 4 | **Domain rigor** | Output respects CT (no invalid `VSTESTCD` values, units in their code list). Missing values handled. Lineage IDs preserved. Output shape matches SDTM expectations. |
| 5 | **Engineering quality** | Code is readable. Errors surface, not swallow. Validation is real, not theatrical. README/run instructions work. |
| 6 | **Communication** | You explain decisions out loud as you build. Your final write-up tells us what the agent did, where it was uncertain, what you'd do with more time. |

## Bonus signals

- You catch a real ambiguity in the inputs and document how you resolved it.
- Your validator finds a bug your agent introduced — and fixes it.
- You make a defensible call about where to use LLM reasoning vs. deterministic code.
- You show one well-designed unit test.

## Hard fails

- Output contains values not in the relevant CT code list (silent SDTM violation).
- "Agent" is a single prompt with no tool use, planning, or validation loop.
- You copy `create_vs.R` and translate it line-by-line. (We will detect this.)
- You do not run your own code before submitting.

## A note on completion

A thoughtful **partial** submission scores higher than a rushed full one. Cover TEMP and SYSBP well before you reach for HEIGHT and WEIGHT.
