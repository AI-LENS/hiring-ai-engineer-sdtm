# 01 · Clinical Trials in 2 Minutes

A **clinical trial** is a controlled experiment to test if a new drug is **safe** and **effective** in humans. A pharma company (the **sponsor**) runs the trial across many hospitals (**sites**) on hundreds or thousands of patients (**subjects**). Regulators like the FDA review the results before approving the drug.

Trials happen in phases:

| Phase | Who | Question |
|---|---|---|
| 1 | 20–80 healthy people | Is it safe? What dose? |
| 2 | 100–300 patients | Does it work? |
| 3 | 1000s of patients | Better than current treatment? |
| 4 | Post-approval | Long-term effects? |

## What data is collected?

For every subject, at every visit, sites collect things like:

- **Demographics** — age, sex, race
- **Vital signs (VS)** — BP, pulse, temperature ← *the data you'll work with*
- **Labs** — blood/urine test values
- **Adverse events** — anything bad that happens
- **Drug exposure** — what dose, when

The data starts **messy**: dozens of sites, different column names, different date formats, free-text fields. Before anything can be submitted to the FDA, it has to be **standardized**.

## Why standardize?

The FDA receives data from hundreds of sponsors. If everyone used different column names, review would be impossible. So **CDISC** (an industry standards body) defined fixed schemas. Every drug submission must conform. The schema you'll target is called **SDTM**.

That's all the trial background you need. Next: [`02-data-flow.md`](./02-data-flow.md).
