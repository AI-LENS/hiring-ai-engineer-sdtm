import pandas as pd

url = "https://raw.githubusercontent.com/pharmaverse/sdtm.oak-workshop/main/datasets/sdtm_ct.csv"

ct = pd.read_csv(url)

ct.to_csv("sdtm_ct.csv", index=False)

print("Downloaded stdm_ct.csv")