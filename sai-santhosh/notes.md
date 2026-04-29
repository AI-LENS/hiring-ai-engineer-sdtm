# Technical Notes

## 1. CT Mapping Limitations

### What is implemented
- **C71148 (VSPOS)**: SUBPOS values are looked up in `sdtm_ct.csv` and mapped
  to the standardised VSPOS term via a `left_join` in R.
- **C66741 (VSTESTCD)** and **C66770 (VSORRESU)**: validated in Python post-hoc
  against hard-coded representative subsets. They are **not** looked up
  dynamically from `sdtm_ct.csv` because VSTESTCD is derived from the raw
  column mapping, not from a free-text field requiring CT lookup.

### What is NOT implemented
- C66742 (VSTEST), C71113 (EPOCH), C74456 (VISIT) — out of scope for this demo.
- If the CT file uses different column names than `codelist_code / term_value /
  collected_value`, the R join will fail silently (no VSPOS).

---

## 2. Unit Conversion Logic

### Temperature: Fahrenheit → Celsius

```
C = (F - 32) × 5 / 9
```

Applied in the generated R script:
```r
VSSTRESN = round((IT.TEMP - 32) * 5 / 9, 2)
VSSTRESU = "C"
```

- `VSORRES` retains the original value in Fahrenheit (collected value).
- `VSORRESU` = `"F"` (original unit).
- `VSSTRESN` / `VSSTRESU` hold the standardised numeric value and unit.

### Other vitals (BP, PULSE)
No conversion — `VSSTRESN = as.numeric(raw_value)` and `VSSTRESU = VSORRESU`.

---

## 3. Differences vs Golden Dataset

Common reasons for mismatches:

| Column | Likely Cause |
|---|---|
| `VSDTC` | Date column absent in raw data → `NA`; golden may have dates |
| `VSPOS` | CT file mismatch or extra whitespace in SUBPOS |
| `USUBJID` | STUDYID constant differs from golden |
| `VSSEQ` | Row ordering differs if golden uses a different sort key |
| `VSSTRESN` | Rounding precision (we use 2 decimal places) |

---

## 4. Assumptions Made

1. `PATNUM` is the subject identifier column (detected dynamically; falls back
   to `PATNUM` if no match found).
2. `SUBPOS` contains position values; `IT.TEMP_LOC` contains location values —
   both normalised to UPPERCASE before CT lookup.
3. Temperature is always recorded in Fahrenheit in the raw data.
4. Missing raw values (`NA`) are excluded from each test dataset via
   `filter(!is.na(...))`.
5. `STUDYID` is a pipeline constant (`"STUDY-001"`); override via `planner.py`
   or the LLM output.
6. The `sdtm.oak` R package is intentionally **not used** to keep the
   environment requirements minimal. The generated R script uses only `dplyr`.

---

## 5. LangChain Integration Notes

- The planner uses **LCEL** (LangChain Expression Language):
  `Prompt | LLM | OutputParser`.
- The LLM is `claude-opus-4-5` (`temperature=0`) for deterministic output.
- After the LLM call, `_parse_and_enrich()` merges the static `STATIC_COLUMN_MAP`
  over the LLM output — this prevents the LLM from drifting on unit codes or
  conversion flags.
- If the LLM returns invalid JSON (network failure, rate limit, etc.) the
  pipeline falls back entirely to the static map and continues.
