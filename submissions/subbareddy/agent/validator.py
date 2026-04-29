import pandas as pd

def validate_output():
    df = pd.read_csv("submissions/subbareddy/output/vs.csv")

    if "VSTESTCD" not in df.columns:
        print("Missing column")
    else:
        print("Validation Passed")