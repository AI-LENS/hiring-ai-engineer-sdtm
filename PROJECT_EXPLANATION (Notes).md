# SDTM VS Mapping Agent — Project Explanation

## 📌 Overview

This project builds an **AI-powered data transformation agent** that converts raw clinical trial vital signs data into **SDTM (Study Data Tabulation Model) VS domain format**.

The system reads raw data, applies mapping logic and controlled terminology (CT), generates an R transformation script, executes it, and validates the final dataset.

---

## Objective

Clinical trial data collected from hospitals is:

* Unstructured
* Inconsistent
* Not regulatory-ready

Regulatory bodies like the FDA require **standardized SDTM datasets**.

👉 This project automates that transformation using an **agent-based approach**.

---

## 📥 Inputs

### 1. Raw Data (`vs_raw.csv`)

* Source: EDC / hospital systems
* Format: Wide (multiple measurements per row)
* Example columns:

  * `SYS_BP`, `DIA_BP`, `PULSE`, `IT.TEMP`
  * `SUBPOS`, `IT.TEMP_LOC`

---

### 2. Controlled Terminology (`sdtm_ct.csv`)

* Acts as a lookup table
* Standardizes values

Example:

| collected_value | term_value  |
| --------------- | ----------- |
| Supine          | SUPINE      |
| Oral cavity     | ORAL CAVITY |

---

### 3. Mapping Logic

Defines how raw variables map to SDTM variables.

---

## ⚙️ What the Agent Does

### Step 1 — Read Data

Loads raw dataset using Python.

---

### Step 2 — Planning (LLM)

Uses OpenAI model to identify which tests exist:

```python
["TEMP","SYSBP","DIABP","PULSE"]
```

---

### Step 3 — Generate R Script

Dynamically creates an R script that:

* Converts wide → long format
* Maps raw variables to SDTM variables
* Applies CT using joins
* Standardizes values

---

### Step 4 — Execute Transformation

Runs R script via:

```python
subprocess.run(["Rscript", ...])
```

---

### Step 5 — Validation

Checks:

* Required SDTM columns present
* CT compliance (no invalid values)
* Missing values
* Comparison with golden dataset

---

### Step 6 — Reporting

Agent prints:

* Mapping decisions
* CT usage
* Differences from golden dataset

---

## 🔄 Mapping Logic (Core Transformation)

| Raw Column  | SDTM Column | Method         |
| ----------- | ----------- | -------------- |
| SYS_BP      | VSORRES     | Direct mapping |
| DIA_BP      | VSORRES     | Direct mapping |
| PULSE       | VSORRES     | Direct mapping |
| IT.TEMP     | VSORRES     | Direct mapping |
| SUBPOS      | VSPOS       | CT mapping     |
| IT.TEMP_LOC | VSLOC       | CT mapping     |

---

## 🔁 Key Transformation

👉 Wide → Long conversion

Example:

Raw (1 row):

```
SYS_BP=131, DIA_BP=64, PULSE=57
```

Converted to:

```
SYSBP row
DIABP row
PULSE row
```

---

## 🧪 Validation Results

* ✅ Required columns present
* ✅ No missing VSORRES values
* ✅ 0 invalid CT values
* ⚠️ Fewer rows than golden (expected)
* ⚠️ Missing optional SDTM variables (not required)

---

## ⚠️ Why `sdtm.oak` Was NOT Used Directly

Although the project description referenced `sdtm.oak`, it was not used due to:

### 1. Environment / Installation Issues

* R library path permission errors
* Package installation failures on Windows

### 2. Version Compatibility Problems

* Function signatures differed from documentation
* `assign_ct()` errors due to argument mismatch

### 3. Debugging Complexity

* Errors were opaque and hard to trace
* Slowed development significantly

---

## ✅ Alternative Approach Used

Instead of `sdtm.oak`, the transformation was implemented using:

* `dplyr`
* `left_join()` for CT mapping
* `mutate()` for variable creation

This approach:

* Follows the same SDTM logic
* Is more transparent
* Easier to debug
* Fully controllable

---

## 🔍 CT Mapping Implementation

Example:

```r
left_join(ct, by = c("SUBPOS" = "collected_value")) %>%
mutate(VSPOS = coalesce(term_value, SUBPOS))
```

👉 Ensures:

* Standard values when available
* Falls back to original if no match

---

## 🧠 Agent Design

The system follows a simple agent architecture:

* LLM → Planning
* Tool → Script generation
* Tool → Execution
* Tool → Validation

---

## 🏁 Final Output

Generated file:

```
output/vs.csv
```

Contains:

* SDTM-compliant structure
* Standardized values
* One row per measurement

---

## 🚀 Conclusion

This project demonstrates:

* Real-world clinical data transformation
* Controlled terminology usage
* Agent-based automation
* End-to-end pipeline from raw → SDTM

---

## 💬 Summary (Simple)

> Built an AI agent that converts raw hospital data into standardized SDTM format using mapping logic, controlled terminology, and automated validation.

---
