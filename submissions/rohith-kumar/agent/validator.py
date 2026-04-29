"""
agent/validator.py

Validates the generated SDTM VS output against:
- Required columns being present
- CT-controlled columns containing only valid values
- A diff against the golden standard
"""

import csv
from pathlib import Path


REQUIRED_COLS = ["STUDYID", "DOMAIN", "USUBJID", "VSSEQ", "VSTESTCD", "VSTEST", "VSORRES", "VSORRESU"]

CT_RULES = {
    "VSTESTCD": "C66741",
    "VSORRESU": "C66770",
    "VSSTRESU": "C66770",
    "VSPOS":    "C71148",
}


def load_csv(path):
    if not Path(path).exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate(output_path, golden_path, ct_path):
    output = load_csv(output_path)
    golden = load_csv(golden_path)
    ct     = load_csv(ct_path)

    # Build CT lookup: {codelist_code: {valid term_values}}
    ct_lookup = {}
    for row in ct:
        code = row.get("codelist_code", "").strip()
        term = row.get("term_value", "").strip()
        if code and term:
            ct_lookup.setdefault(code, set()).add(term)

    report_lines = ["# Validation Report\n"]
    passed = True

    # 1. Required columns
    report_lines.append("## Required Columns")
    if output:
        cols = set(output[0].keys())
        for col in REQUIRED_COLS:
            status = "✓" if col in cols else "❌ MISSING"
            if "MISSING" in status:
                passed = False
            report_lines.append(f"- {col}: {status}")
    else:
        report_lines.append("- ❌ output/vs.csv is empty")
        passed = False

    # 2. CT validation
    report_lines.append("\n## CT Validation")
    for col, clst in CT_RULES.items():
        if not output or col not in output[0]:
            continue
        valid = ct_lookup.get(clst, set())
        bad   = {r[col].strip() for r in output if r.get(col, "").strip() and r[col].strip() not in valid}
        if bad:
            report_lines.append(f"- ❌ {col} invalid values: {sorted(bad)}")
            passed = False
        else:
            report_lines.append(f"- ✓ {col} all values valid")

    # 3. Row count
    report_lines.append(f"\n## Row Counts")
    report_lines.append(f"- Output rows: {len(output)}")
    report_lines.append(f"- Golden rows: {len(golden)}")

    # 4. Golden diff (key columns)
    if golden and output:
        report_lines.append("\n## Diff vs Golden")
        golden_idx = {(r["USUBJID"], r["VSTESTCD"], r.get("VISITNUM","")): r for r in golden}
        mismatches = 0
        for row in output:
            key = (row.get("USUBJID",""), row.get("VSTESTCD",""), row.get("VISITNUM",""))
            if key in golden_idx:
                g = golden_idx[key]
                for col in ["VSORRES", "VSORRESU", "VSSTRESC", "VSSTRESU"]:
                    if g.get(col,"").strip() and row.get(col,"").strip() != g.get(col,"").strip():
                        report_lines.append(f"- {key} | {col}: got '{row.get(col,'')}' expected '{g.get(col,'')}'")
                        mismatches += 1
        if mismatches == 0:
            report_lines.append("- ✓ No mismatches found")

    report_lines.append(f"\n## Status: {'PASS ✅' if passed else 'FAIL ❌'}")
    return "\n".join(report_lines), passed