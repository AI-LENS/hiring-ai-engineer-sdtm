This project builds an **agentic AI pipeline in Python** to convert raw clinical trial **Vital Signs (VS)** data into a **CDISC SDTM-compliant dataset**, using the `sdtm.oak` R package as a transformation engine.

Pipeline:

Raw Data → LLM Planner → R Script Generator → Execution → Validation

---

## 🧠 Architecture Diagram

```
          +------------------+
          |   Raw VS Data    |
          +------------------+
                    |
                    v
          +------------------+
          |  LLM Planner     |
          | (LangChain/Groq) |
          +------------------+
                    |
                    v
          +------------------+
          | Mapping Plan     |
          +------------------+
                    |
                    v
          +------------------+
          | R Script Gen     |
          +------------------+
                    |
                    v
          +------------------+
          |  R Execution     |
          | (sdtm.oak style) |
          +------------------+
                    |
                    v
          +------------------+
          | SDTM VS Dataset  |
          +------------------+
                    |
                    v
          +------------------+
          | Validation       |
          +------------------+
```

---

## 📂 Project Structure

```
AI_LENS_CODING/
├── input/
│   ├── vs_raw.csv
│   ├── sdtm_ct.csv
│   └── vs_golden.csv
├── agent/
│   ├── planner.py
│   ├── generator.py
│   └── validator.py
├── output/
│   ├── vs.csv
│   ├── generated.R
│   ├── validation_report.md
│   └── diff_report.md
├── run.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### Python
```
pip install -r requirements.txt
```

### R
```
Rscript -e "install.packages(c('dplyr','remotes'), repos='https://cloud.r-project.org')"
Rscript -e "remotes::install_github('pharmaverse/pharmaverseraw')"
Rscript -e "remotes::install_github('pharmaverse/pharmaversesdtm')"
```

---

## 🔑 Environment (Optional)

Create `.env`:

```
GROQ_API_KEY=your_key_here
```

Fallback works without API.

---

## 🚀 Run

```
python run.py
```

---

## 📊 Output

- vs.csv → final dataset  
- generated.R → transformation script  
- validation_report.md  
- diff_report.md  

---

## ✅ Features

- LLM-based planning
- Deterministic fallback
- R orchestration
- Validation + diff
- Clean modular design

---

## ⚠️ Limitations

- Not full SDTM compliance
- Partial CT usage
- Row mismatch with golden dataset

---

## 🧠 Design Decisions

- LLM used only for planning
- Deterministic mapping for reliability
- Separation of concerns (planner/generator/validator)

---

## 🔮 Future Work

- Full CT enforcement
- Better wide→long transformation
- More variables & domains

---

## 💬 Summary

A clean, agent-based system combining:
- LLM reasoning
- deterministic logic
- Python + R integration

Designed for clarity, reliability, and extensibility.
