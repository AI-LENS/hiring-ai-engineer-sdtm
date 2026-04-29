# Submission — Round 2

**Deadline: today, 18:00 (6:00 PM) IST.** Late submissions are not accepted.

You submit by opening a **Pull Request to this repository.** No email, no zip.

---

## Step-by-step

1. **Fork** this repo to your own GitHub account: <https://github.com/AI-LENS/hiring-ai-engineer-sdtm/fork>

2. On your fork, **create a branch** named after you:
   ```
   submission/<firstname>-<lastname>
   ```
   Example: `submission/ananya-rao`

3. Add your work under the path:
   ```
   submissions/<firstname>-<lastname>/
   ```
   So your fork's tree looks like:
   ```
   submissions/ananya-rao/
   ├── README.md            # how to run, architecture, what works, what's next
   ├── run.py               # entry point — produces vs.csv + validation_report.md
   ├── agent/               # your agent code (tools, prompts, control flow)
   ├── output/
   │   ├── vs.csv           # your generated SDTM VS dataset
   │   ├── generated.R      # the R script your agent produced
   │   └── validation_report.md
   ├── requirements.txt     # or pyproject.toml / uv.lock
   └── notes.md             # decisions, ambiguities flagged, what you'd improve
   ```

4. **Commit and push** your branch to your fork.

5. **Open a Pull Request** from your fork's `submission/<firstname>-<lastname>` branch back to `AI-LENS/hiring-ai-engineer-sdtm:main`.

   - **PR title:** `[Round 2] <Firstname Lastname> — Submission`
   - **PR description must include:**
     - One-paragraph summary of your approach.
     - Setup commands so reviewers can run your code on a clean machine.
     - Time spent (rough breakdown by phase).
     - Anything you'd like reviewers to focus on or skip.

6. **Do not merge the PR.** Reviewers do not merge submissions; the PR existing is the submission. The timestamp of the PR creation (or your last push to the branch before 18:00 IST) is what we use for the deadline.

---

## What your `submissions/<firstname>-<lastname>/README.md` must cover

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
- Modifying any files **outside** your `submissions/<firstname>-<lastname>/` folder. (PRs that touch shared docs, other candidates' folders, or this file will be rejected.)

## If something goes wrong

- **PR won't open / fork issues:** comment on the issue tracker of this repo with your GitHub handle and we'll help.
- **Last-minute push fails before 18:00 IST:** the timestamp on your last successful push to your fork's submission branch is what counts. Push early and often — don't batch a single push at 17:59.
