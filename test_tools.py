"""
tests/test_tools.py — Unit tests for deterministic tool functions.

Run with:  pytest tests/test_tools.py -v

These tests do NOT require R, Gemini, or network access.
They validate the Python-side logic — the parts most likely to introduce
silent bugs (CT compliance checks, validation rules, R script structure).
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Add parent to path so imports work without installing the package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import inspect_raw_data, inspect_ct, validate_sdtm_output
from r_script_builder import build_r_script


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def sample_raw_csv(tmp_path: Path) -> str:
    path = tmp_path / "vs_raw.csv"
    path.write_text(
        "PATNUM,VISIT,IT.TEMP,IT.TEMP_LOC,SYS_BP,DIA_BP,PULSE,SUBPOS,VSDAT\n"
        "375,Screening,98.6,ORAL CAVITY,120,80,72,SITTING,2020-01-15\n"
        "375,Week 2,99.1,ORAL CAVITY,118,78,70,SITTING,2020-01-29\n"
        "376,Screening,97.9,ORAL CAVITY,130,85,68,SUPINE,2020-01-16\n",
        encoding="utf-8",
    )
    return str(path)


@pytest.fixture()
def sample_ct_csv(tmp_path: Path) -> str:
    path = tmp_path / "sdtm_ct.csv"
    rows = [
        ("codelist_code", "codelist_name",       "term_value",   "collected_value"),
        ("C66741",        "VS Test Code",         "TEMP",         "TEMP"),
        ("C66741",        "VS Test Code",         "SYSBP",        "SYSBP"),
        ("C66741",        "VS Test Code",         "DIABP",        "DIABP"),
        ("C66741",        "VS Test Code",         "PULSE",        "PULSE"),
        ("C66770",        "Unit",                 "C",            "C"),
        ("C66770",        "Unit",                 "C",            "Celsius"),
        ("C66770",        "Unit",                 "F",            "F"),
        ("C66770",        "Unit",                 "mmHg",         "mmHg"),
        ("C66770",        "Unit",                 "beats/min",    "beats/min"),
        ("C71148",        "Position",             "SUPINE",       "SUPINE"),
        ("C71148",        "Position",             "SITTING",      "SITTING"),
        ("C74456",        "Anatomical Location",  "ORAL CAVITY",  "ORAL CAVITY"),
        ("C74456",        "Anatomical Location",  "ARM",          "ARM"),
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    return str(path)


@pytest.fixture()
def valid_sdtm_csv(tmp_path: Path) -> str:
    path = tmp_path / "vs_sdtm.csv"
    df = pd.DataFrame({
        "STUDYID" : ["CDISCPILOT01"] * 3,
        "DOMAIN"  : ["VS"] * 3,
        "USUBJID" : ["CDISCPILOT01-375", "CDISCPILOT01-375", "CDISCPILOT01-376"],
        "VSTESTCD": ["TEMP",  "SYSBP",  "DIABP"],
        "VSTEST"  : ["Temperature", "Systolic Blood Pressure", "Diastolic Blood Pressure"],
        "VSORRES" : ["98.6",  "120",    "80"],
        "VSORRESU": ["F",     "mmHg",   "mmHg"],
        "VSSTRESC": ["37.0",  "120.0",  "80.0"],
        "VSSTRESN": [37.0,    120.0,    80.0],
        "VSSTRESU": ["C",     "mmHg",   "mmHg"],
        "VSPOS"   : ["SITTING", "SITTING", "SUPINE"],
        "VSLOC"   : ["ORAL CAVITY", None, None],
        "VISITNUM": [1, 1, 1],
        "VISIT"   : ["Screening"] * 3,
        "VSDTC"   : ["2020-01-15"] * 3,
    })
    df.to_csv(path, index=False)
    return str(path)


# ══════════════════════════════════════════════════════════════════════════════
# Tests: inspect_raw_data
# ══════════════════════════════════════════════════════════════════════════════

class TestInspectRawData:
    def test_returns_expected_keys(self, sample_raw_csv):
        result = inspect_raw_data(sample_raw_csv)
        assert set(result.keys()) == {"columns", "dtypes", "row_count", "sample_rows", "null_counts"}

    def test_row_count(self, sample_raw_csv):
        result = inspect_raw_data(sample_raw_csv)
        assert result["row_count"] == 3

    def test_columns_present(self, sample_raw_csv):
        result = inspect_raw_data(sample_raw_csv)
        assert "IT.TEMP" in result["columns"]
        assert "PATNUM"  in result["columns"]

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            inspect_raw_data("/nonexistent/path/raw.csv")


# ══════════════════════════════════════════════════════════════════════════════
# Tests: inspect_ct
# ══════════════════════════════════════════════════════════════════════════════

class TestInspectCT:
    def test_correct_code_lists(self, sample_ct_csv):
        result = inspect_ct(sample_ct_csv)
        assert "C66741" in result
        assert "C66770" in result
        assert "C71148" in result
        assert "C74456" in result

    def test_term_values(self, sample_ct_csv):
        result = inspect_ct(sample_ct_csv)
        assert "TEMP" in result["C66741"]["term_values"]
        assert "SYSBP" in result["C66741"]["term_values"]

    def test_collected_values_synonyms(self, sample_ct_csv):
        result = inspect_ct(sample_ct_csv)
        # 'Celsius' maps to 'C'
        assert "Celsius" in result["C66770"]["collected_values"]

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            inspect_ct("/no/such/file.csv")

    def test_missing_columns(self, tmp_path):
        bad = tmp_path / "bad_ct.csv"
        bad.write_text("code,value\nX,Y\n")
        with pytest.raises(ValueError, match="missing columns"):
            inspect_ct(str(bad))


# ══════════════════════════════════════════════════════════════════════════════
# Tests: validate_sdtm_output
# ══════════════════════════════════════════════════════════════════════════════

class TestValidateSDTMOutput:
    def test_valid_file_passes(self, valid_sdtm_csv, sample_ct_csv):
        report = validate_sdtm_output(valid_sdtm_csv, sample_ct_csv)
        assert report["valid"], f"Unexpected failures: {report['failed']}"

    def test_missing_file_fails(self, sample_ct_csv):
        report = validate_sdtm_output("/no/such/output.csv", sample_ct_csv)
        assert not report["valid"]
        assert any("not found" in m for m in report["failed"])

    def test_bad_vstestcd_fails(self, tmp_path, sample_ct_csv):
        path = tmp_path / "bad.csv"
        df = pd.DataFrame({
            "STUDYID" : ["X"],
            "DOMAIN"  : ["VS"],
            "USUBJID" : ["X-001"],
            "VSTESTCD": ["HEARTRATE"],   # Not in C66741
            "VSTEST"  : ["Heart Rate"],
            "VSORRES" : ["72"],
            "VSORRESU": ["beats/min"],
            "VSSTRESC": ["72"],
            "VSSTRESN": [72.0],
            "VSSTRESU": ["beats/min"],
            "VSPOS"   : ["SITTING"],
            "VISITNUM": [1],
            "VISIT"   : ["Screening"],
            "VSDTC"   : ["2020-01-15"],
        })
        df.to_csv(path, index=False)
        report = validate_sdtm_output(str(path), sample_ct_csv)
        assert not report["valid"]
        assert any("VSTESTCD" in m for m in report["failed"])

    def test_bad_iso_date_fails(self, tmp_path, sample_ct_csv):
        path = tmp_path / "bad_date.csv"
        df = pd.DataFrame({
            "STUDYID" : ["X"],
            "DOMAIN"  : ["VS"],
            "USUBJID" : ["X-001"],
            "VSTESTCD": ["TEMP"],
            "VSTEST"  : ["Temperature"],
            "VSORRES" : ["98.6"],
            "VSORRESU": ["F"],
            "VSSTRESC": ["37.0"],
            "VSSTRESN": [37.0],
            "VSSTRESU": ["C"],
            "VSPOS"   : ["SITTING"],
            "VISITNUM": [1],
            "VISIT"   : ["Screening"],
            "VSDTC"   : ["01/15/2020"],   # US format — invalid
        })
        df.to_csv(path, index=False)
        report = validate_sdtm_output(str(path), sample_ct_csv)
        assert not report["valid"]
        assert any("VSDTC" in m for m in report["failed"])

    def test_non_numeric_vsstresn_fails(self, tmp_path, sample_ct_csv):
        path = tmp_path / "bad_num.csv"
        df = pd.DataFrame({
            "STUDYID" : ["X"],
            "DOMAIN"  : ["VS"],
            "USUBJID" : ["X-001"],
            "VSTESTCD": ["TEMP"],
            "VSTEST"  : ["Temperature"],
            "VSORRES" : ["98.6"],
            "VSORRESU": ["F"],
            "VSSTRESC": ["37.0"],
            "VSSTRESN": ["thirty-seven"],   # ← not numeric
            "VSSTRESU": ["C"],
            "VSPOS"   : ["SITTING"],
            "VISITNUM": [1],
            "VISIT"   : ["Screening"],
            "VSDTC"   : ["2020-01-15"],
        })
        df.to_csv(path, index=False)
        report = validate_sdtm_output(str(path), sample_ct_csv)
        assert not report["valid"]
        assert any("VSSTRESN" in m for m in report["failed"])


# ══════════════════════════════════════════════════════════════════════════════
# Tests: r_script_builder
# ══════════════════════════════════════════════════════════════════════════════

class TestRScriptBuilder:
    @pytest.fixture()
    def minimal_plan(self) -> dict:
        return {
            "pat_var"      : "PATNUM",
            "date_col"     : "VSDAT",
            "visit_col"    : "VISIT",
            "visitnum_col" : None,
            "position_col" : "SUBPOS",
            "tests": [
                {
                    "testcd"         : "TEMP",
                    "testname"       : "Temperature",
                    "raw_result_col" : "IT.TEMP",
                    "raw_unit_col"   : None,
                    "fixed_unit"     : "F",
                    "loc_col"        : "IT.TEMP_LOC",
                    "vstestcd_clst"  : "C66741",
                    "vstest_clst"    : "C67153",
                    "vsorresu_clst"  : "C66770",
                    "vsstresu_clst"  : "C66770",
                    "vsloc_clst"     : "C74456",
                    "vspos_clst"     : "C71148",
                    "std_unit"       : "C",
                    "conversion"     : "celsius",
                },
            ],
        }

    def test_contains_required_functions(self, minimal_plan):
        script = build_r_script(minimal_plan, "raw.csv", "ct.csv", "out.csv")
        assert "hardcode_ct"           in script
        assert "assign_no_ct"          in script
        assert "assign_ct"             in script
        assert "generate_oak_id_vars"  in script
        assert "oak_id_vars"           in script
        assert "bind_rows"             in script

    def test_celsius_conversion_present(self, minimal_plan):
        script = build_r_script(minimal_plan, "raw.csv", "ct.csv", "out.csv")
        assert "32" in script and "5/9" in script

    def test_output_write_call(self, minimal_plan):
        script = build_r_script(minimal_plan, "raw.csv", "ct.csv", "out.csv")
        assert "write.csv" in script

    def test_domain_vs_hardcoded(self, minimal_plan):
        script = build_r_script(minimal_plan, "raw.csv", "ct.csv", "out.csv")
        assert '"VS"' in script

    def test_multiple_tests_all_present(self, minimal_plan):
        # Add a second test
        minimal_plan["tests"].append({
            "testcd"         : "SYSBP",
            "testname"       : "Systolic Blood Pressure",
            "raw_result_col" : "SYS_BP",
            "raw_unit_col"   : None,
            "fixed_unit"     : "mmHg",
            "loc_col"        : None,
            "vstestcd_clst"  : "C66741",
            "vstest_clst"    : "C67153",
            "vsorresu_clst"  : "C66770",
            "vsstresu_clst"  : "C66770",
            "vsloc_clst"     : "C74456",
            "vspos_clst"     : "C71148",
            "std_unit"       : "mmHg",
            "conversion"     : "none",
        })
        script = build_r_script(minimal_plan, "raw.csv", "ct.csv", "out.csv")
        assert "vs_temp"  in script
        assert "vs_sysbp" in script
