# Clinical Trial Agent – Project Summary

## Project Goal

This project automates the conversion of raw clinical trial data into standardized SDTM (Study Data Tabulation Model) format using AI + rule-based validation.

Instead of manually checking and converting data, the system uses an intelligent agent pipeline to make the process faster, cleaner, and more accurate.

---

# How the Project Works

## Step 1: Input Raw Clinical Data

The user provides:

- Raw clinical trial datasets
- Source CSV / Excel / JSON files
- Clinical observations and patient records

These files may contain unstructured or inconsistent data.

---

## Step 2: Planner Agent

### planner.py

This module decides:

- what needs to be converted
- which SDTM domain is required
- what transformation steps should happen next

It acts like the brain of the system.

Example:

Raw lab data → should go to LB domain

---

## Step 3: Prompt Generation

### prompts.py

This module creates structured prompts for the LLM.

It tells the AI exactly:

- what to analyze
- how to map columns
- how to validate values
- how to generate proper SDTM output

This improves AI accuracy.

---

## Step 4: R Code Generator

### r_generator.py

This module generates R code automatically for:

- SDTM dataset transformation
- data cleaning
- variable mapping
- standardization

Instead of writing R manually, AI helps generate it.

---

## Step 5: Validation Engine

### validator.py

This is one of the most important parts.

It checks:

- missing values
- invalid formats
- rule violations
- SDTM compliance errors
- inconsistent mappings

This ensures the final output is correct.

---

## Step 6: Reporter Module

### reporter.py

This module generates final reports such as:

- validation summary
- error reports
- compliance reports
- final output review

This helps users understand what was fixed and what failed.

---

## Step 7: Final Clean Output

The system produces:

- standardized SDTM datasets
- validation reports
- generated R scripts
- clean structured output ready for submission

This is the final deliverable.

---

# Simple Flow

Raw Data
↓
Planner Agent
↓
Prompt Generation
↓
R Code Generation
↓
Validation Engine
↓
Report Generation
↓
Final SDTM Output

---

# Technologies Used

- Python
- LLM Integration
- R Code Generation
- Validation Engine
- SDTM Standards
- Git + GitHub
- Agent-based Workflow Design

---

# Why This Project is Strong

Because it solves a real industry problem:

Clinical trial companies spend huge time manually converting data into SDTM format.

This project reduces:

- manual effort
- human errors
- processing time

and improves:

- speed
- compliance
- scalability

---

# One-Line Interview Definition

“This project is an AI-powered clinical trial agent that automates SDTM conversion, validation, and reporting using LLMs, R code generation, and rule-based validation pipelines.”