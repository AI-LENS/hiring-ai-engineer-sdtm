# 🧠 SDTM Vital Signs Transformation Pipeline

## 📌 Problem Statement

Clinical trial data is often stored in raw format and must be transformed into standardized formats such as **SDTM (Study Data Tabulation Model)** for regulatory submission.

This project builds an **automated pipeline** that:

* Takes raw vital signs data (`vs_raw.csv`)
* Transforms it into SDTM-compliant structure
* Generates output using an **R script**
* Validates the final dataset using Python

---

## 🎯 Objective

Convert raw clinical data into SDTM format with the following structure:

| Column   | Description                           |
| -------- | ------------------------------------- |
| VSTESTCD | Test Code (TEMP, SYSBP, DIABP, PULSE) |
| VSORRES  | Observed Result                       |

---

## 🏗️ Project Structure

```
hiring-ai-engineer-sdtm/
│
├── vs_raw.csv
│
└── submissions/
    └── subbareddy/
        ├── agent/
        │   ├── codegen.py      # Generates R script
        │   ├── executor.py     # Runs R script
        │   ├── validator.py    # Validates output
        │   ├── planner.py      # (Optional)
        │   └── prompts.py      # (Optional)
        │
        ├── output/
        │   ├── generated.R     # Auto-generated R script
        │   └── vs.csv          # Final output
        │
        ├── run.py              # Main pipeline
        ├── requirements.txt
        └── README.md
```

---

## ⚙️ Workflow

### Step 1: Generate R Script

Python dynamically creates an R script using `codegen.py`.

### Step 2: Execute R Script

The script reads raw data and transforms it into SDTM format.

### Step 3: Validate Output

Python validates:

* File existence
* Required columns
* Data integrity

---

## 🔄 Data Transformation Logic

Input (`vs_raw.csv`):

```
IT.TEMP, SYS_BP, DIA_BP, PULSE
98, 120, 80, 70
```

Transformation:

* TEMP → IT.TEMP
* SYSBP → SYS_BP
* DIABP → DIA_BP
* PULSE → PULSE

---

## 🧪 Generated R Script

```r
raw <- read.csv("../../../vs_raw.csv")

temp <- data.frame(VSTESTCD="TEMP", VSORRES=raw$IT.TEMP)
sysbp <- data.frame(VSTESTCD="SYSBP", VSORRES=raw$SYS_BP)
diabp <- data.frame(VSTESTCD="DIABP", VSORRES=raw$DIA_BP)
pulse <- data.frame(VSTESTCD="PULSE", VSORRES=raw$PULSE)

final <- rbind(temp, sysbp, diabp, pulse)

write.csv(final, "submissions/subbareddy/output/vs.csv", row.names=FALSE)
```

---

## 🚀 How to Run

### 1. Install Requirements

```bash
pip install pandas
```

Ensure R is installed and `Rscript` is available.

---

### 2. Run Pipeline

```bash
python submissions/subbareddy/run.py
```

---

## ✅ Expected Output

### Terminal Output

```
Step 1: Generating R script...
R script created successfully

Step 2: Running R script...

Step 3: Validating output...
Validation Passed ✅
```

---

### Output File

```
submissions/subbareddy/output/vs.csv
```

### Sample Output

```
VSTESTCD,VSORRES
TEMP,98
SYSBP,120
DIABP,80
PULSE,70
```

---

## 🔍 Validation Checks

* File exists
* Required columns present
* No empty dataset
* Correct transformation mapping

---

## 🧠 Key Concepts Demonstrated

* Cross-language execution (Python → R)
* Data transformation pipelines
* SDTM standardization
* Modular agent-based design
* Error handling & validation

---

## ⚠️ Common Issues & Fixes

| Issue               | Solution                         |
| ------------------- | -------------------------------- |
| `sdtm.oak` error    | Remove library usage             |
| File not found      | Fix relative paths (`../../../`) |
| No output generated | Ensure `codegen.py` is correct   |
| Wrong folder path   | Use consistent `submissions/`    |

---

## 🚀 Future Improvements

* Integrate LangChain / Agentic AI
* Add schema validation
* Extend to other SDTM domains
* Add UI dashboard
* Automate CT (Controlled Terminology)

---

## 🧑‍💻 Author

**Subba Reddy**
AI / Data Science Enthusiast

---

## 📌 Summary

This project demonstrates how to:

* Automate clinical data transformation
* Integrate Python and R pipelines
* Build production-style data workflows
* Apply SDTM standards in practice

---

✔ End-to-end working pipeline
✔ Clean modular design
✔ Ready for interview demonstration
