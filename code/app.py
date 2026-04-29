import streamlit as st
import pandas as pd
import os
from tool_wrapper import generate_r_script, run_r
from validator import validate

st.set_page_config(page_title="SDTM VS Converter", layout="wide")

st.title("🧠 SDTM VS Conversion Agent")

st.info("""
Upload ONLY the raw dataset (vs_raw.csv)

System uses internally:
✔ Controlled Terminology (data/sdtm_ct.csv)
✔ Deterministic mapping rules
""")

raw_file = st.file_uploader("Upload vs_raw.csv", type=["csv"])

if raw_file:
    raw_df = pd.read_csv(raw_file)

    st.subheader("📊 Raw Data Preview")
    st.dataframe(raw_df.head())

    if st.button("🚀 Run Conversion"):

        os.makedirs("data", exist_ok=True)
        os.makedirs("output", exist_ok=True)

        raw_path = os.path.join("data", "vs_raw.csv")
        ct_path  = os.path.join("data", "sdtm_ct.csv")
        out_path = os.path.join("output", "vs.csv")

        # Save raw
        raw_df.to_csv(raw_path, index=False)

        # ✅ Hard checks (no old errors again)
        if not os.path.exists(raw_path) or os.stat(raw_path).st_size == 0:
            st.error("❌ Raw file not saved or empty")
            st.stop()

        if not os.path.exists(ct_path):
            st.error("❌ Internal CT file missing at data/sdtm_ct.csv")
            st.stop()

        if os.stat(ct_path).st_size == 0:
            st.error("❌ sdtm_ct.csv is empty")
            st.stop()

        # Run pipeline
        generate_r_script()
        try:
            run_r()
        except Exception as e:
            st.error(f"❌ R failed:\n{e}")
            st.stop()

        # Load output
        if os.path.exists(out_path) and os.stat(out_path).st_size > 0:
            out_df = pd.read_csv(out_path)

            st.success("✅ SDTM Generated")

            st.subheader("📊 Output Preview")
            st.dataframe(out_df.sample(20))

            st.subheader("📊 Output Info")
            st.write({"rows": len(out_df), "columns": list(out_df.columns)})

            st.subheader("🧪 Validation Report")
            report = validate(out_path, ct_path)
            st.json(report)

            st.download_button(
                "📥 Download SDTM CSV",
                out_df.to_csv(index=False),
                "vs_output.csv",
                mime="text/csv"
            )
        else:
            st.error("❌ Output not generated")