import pandas as pd


class SDTMValidator:
    def __init__(self, vs_csv, ct_csv, golden_csv, val_report, diff_report):
        self.vs_csv = vs_csv
        self.golden_csv = golden_csv
        self.val_report = val_report
        self.diff_report = diff_report

    def validate(self):
        df = pd.read_csv(self.vs_csv)

        report = []

        if len(df) > 0:
            report.append(f"Rows: {len(df)} OK")
        else:
            report.append("Dataset empty")

        required = ["USUBJID", "VSTESTCD", "VSORRES"]
        missing = [c for c in required if c not in df.columns]

        if not missing:
            report.append("Required columns present")
        else:
            report.append(f"Missing: {missing}")

        self.val_report.write_text("\n".join(report), encoding="utf-8")

    def diff_vs_golden(self):
        df = pd.read_csv(self.vs_csv)
        gold = pd.read_csv(self.golden_csv)

        diff = abs(len(df) - len(gold))

        self.diff_report.write_text(
            f"Row difference: {diff}",
            encoding="utf-8"
        )