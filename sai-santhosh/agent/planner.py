import pandas as pd
import json
import logging
import re
from pathlib import Path

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

log = logging.getLogger(__name__)

STATIC_MAP = {
    "IT.TEMP": ("TEMP", "Temperature", "F", True, "C"),
    "SYS_BP": ("SYSBP", "Systolic Blood Pressure", "mmHg", False, "mmHg"),
    "DIA_BP": ("DIABP", "Diastolic Blood Pressure", "mmHg", False, "mmHg"),
    "PULSE": ("PULSE", "Pulse Rate", "beats/min", False, "beats/min"),
}


def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


class SDTMPlanner:
    def __init__(self, raw_csv: Path, ct_csv: Path):
        self.raw_csv = raw_csv
        self.ct_csv = ct_csv

        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Return ONLY JSON."),
            ("human", "Columns: {columns}. Map to SDTM VS.")
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

    def run(self):
        df = pd.read_csv(self.raw_csv, nrows=5)
        cols = df.columns.tolist()

        log.info(f"Detected columns: {cols}")

        try:
            output = self.chain.invoke({"columns": cols})
            json.loads(extract_json(output))
        except Exception as e:
            log.warning(f"LLM failed, fallback used: {e}")

        plan = {
            "studyid": "STUDY1",
            "subj_col": "PATNUM",
            "pos_col": "SUBPOS",
            "date_col": None,
            "columns": [],
        }

        for col in cols:
            if col in STATIC_MAP:
                vstestcd, vstest, unit, convert, std_unit = STATIC_MAP[col]

                plan["columns"].append({
                    "raw_col": col,
                    "vstestcd": vstestcd,
                    "vstest": vstest,
                    "vsorresu": unit,
                    "convert": convert,
                    "vstresu": std_unit,
                })

        log.info(f"Final plan: {plan}")
        return plan