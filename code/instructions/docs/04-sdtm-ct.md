# 04 · The Controlled Terminology (CT) File

The `study_ct.csv` file is the **lookup table** that turns messy collected values into CDISC-standard SDTM values. Without it, no mapping works.

## What it looks like

| codelist_code | codelist_name | term_value | collected_value |
|---|---|---|---|
| C66741 | VS Test Code | TEMP | TEMP |
| C66741 | VS Test Code | SYSBP | SYSBP |
| C66770 | Unit | C | C |
| C66770 | Unit | C | Celsius |
| C66770 | Unit | F | F |
| C66770 | Unit | mmHg | mmHg |
| C71148 | Position | SUPINE | Supine |
| C71148 | Position | SUPINE | Lying down |
| C71148 | Position | SITTING | Sitting |
| C74456 | Anatomical Location | ORAL CAVITY | ORAL CAVITY |
| C74456 | Anatomical Location | ARM | Arm |

- `codelist_code` — CDISC NCI Thesaurus code for the code list. Joins to `ct_clst =` in `sdtm.oak`.
- `term_value` — the **submission value** that goes into SDTM.
- `collected_value` — what the EDC actually has. Multiple synonyms map to one term.

## Code lists you'll need for VS

| Code list | What it covers |
|---|---|
| `C66741` | VS Test Code (`VSTESTCD`) |
| `C67153` | VS Test Name (`VSTEST`) |
| `C66770` | Units (`VSORRESU`, `VSSTRESU`) |
| `C71148` | Position (`VSPOS`) |
| `C74456` | Anatomical Location (`VSLOC`) |

## How a study CT is built (conceptually)

1. Start from CDISC's published master CT (refreshed quarterly).
2. Filter to code lists used by the in-scope domains (here: VS).
3. Add rows for every collected value/synonym the CRF can produce (`Lying down` → `SUPINE`).
4. Validate: every CRF dropdown maps to exactly one `term_value`.
5. Version it (CDISC CT release date + protocol version).

## What you'll do with it

You **don't build CT from scratch**. The workshop ships one. Get it from:
<https://github.com/pharmaverse/sdtm.oak-workshop/blob/main/datasets/sdtm_ct.csv>

Your agent should:
- **Load it** (read the CSV in Python and pass to R, or have R read it directly).
- **Reason about it** — pick the right `codelist_code` for each target variable.
- **Validate against it** — every value your agent puts in `VSTESTCD` / `VSPOS` / `VSORRESU` etc. must appear as a `term_value` for that code list. If it doesn't, that's a hard SDTM violation. We'll check.

Next: [`05-task.md`](./05-task.md).
