# 02 · Data Flow — From Protocol to Submission

A clinical trial is a pipeline of documents and datasets. Six artifacts matter:

```
Protocol  ──►  CRF  ──►  Raw data  ──►  SDTM  ──►  ADaM  ──►  TFLs  ──►  FDA
   │                                       ▲          ▲
   └───────────  SAP  ────────────────────┘          │
                                          (drives ADaM design)
```

| Artifact | What it is | Format |
|---|---|---|
| **Protocol** | The trial's master plan: eligibility, schedule, endpoints. | PDF / Word |
| **CRF** | The form sites fill in for each subject visit. **aCRF** = annotated CRF showing which form field maps to which SDTM column. | PDF / EDC system |
| **SAP** | Statistical Analysis Plan — exactly how analyses will be done. Drives ADaM design. | PDF |
| **Raw data** | What the EDC system exports. Column names are arbitrary (`PATNUM`, `IT.TEMP`, `SYS_BP`). **Your input.** | CSV / SAS |
| **SDTM** | Standardized observations, one row per measurement, fixed column names per domain. **Your output.** | CSV / XPT |
| **ADaM** | Analysis-ready datasets derived from SDTM. (Out of scope for this task.) | CSV / XPT |
| **TFLs** | Tables, Figures, Listings for the final report. (Out of scope.) | PDF / RTF |

## SDTM domains

SDTM splits data into **domains**, each a 2-letter code:

| Code | Domain | Code | Domain |
|---|---|---|---|
| `DM` | Demographics | `AE` | Adverse Events |
| **`VS`** | **Vital Signs ← your task** | `CM` | Concomitant Meds |
| `LB` | Labs | `EX` | Exposure |

## Key VS variables you'll produce

| Variable | Meaning |
|---|---|
| `STUDYID` | Study identifier |
| `USUBJID` | Unique subject ID |
| `VSTESTCD` | Short code: `SYSBP`, `DIABP`, `TEMP`, `PULSE` |
| `VSTEST` | Long label: `Systolic Blood Pressure`, `Temperature` |
| `VSORRES` / `VSORRESU` | Original result + original units |
| `VSSTRESC` / `VSSTRESN` / `VSSTRESU` | Standardized result (char/num) + standardized units |
| `VSPOS` | Body position: `SUPINE`, `SITTING` |
| `VSLOC` | Body location: `ARM`, `ORAL CAVITY` |
| `VISIT` / `VISITNUM` | Visit info |
| `VSDTC` | ISO 8601 date/time |

Next: [`03-sdtm-oak.md`](./03-sdtm-oak.md).
