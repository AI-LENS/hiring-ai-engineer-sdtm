import streamlit as st
import pandas as pd
import os
from run import run_langchain_agent, generate_r_script, run_orchestration

st.set_page_config(page_title="SDTM Agent Dashboard", layout="wide")

st.title("🧪 Clinical SDTM Mapping Agent")

# Sidebar for Setup
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Groq API Key", type="password")
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    uploaded_file = st.file_uploader("Upload Raw EDC CSV", type="csv")

if uploaded_file and api_key:
    # Save the file
    with open("vs_raw.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("🚀 Run Orchestration"):
        with st.status("Agent Pipeline Running...", expanded=True) as status:
            # Step 1: LLM Reasoning
            st.write("🧠 Consulting LangChain...")
            mappings = run_langchain_agent()
            
            # Step 2: Generate R
            st.write("📝 Writing R Script...")
            generate_r_script(mappings)
            
            # Step 3: Run R
            st.write("⚙️ Executing R Subprocess...")
            run_orchestration()
            
            status.update(label="Workflow Complete!", state="complete")

        # --- DISPLAY RESULTS ---
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📄 Generated R Code")
            # This reads the script the agent just wrote
            if os.path.exists("output/generated.R"):
                with open("output/generated.R", "r") as f:
                    r_code = f.read()
                st.code(r_code, language="r")

        with col2:
            st.subheader("📊 Processed SDTM Data")
            if os.path.exists("output/vs.csv"):
                df_vs = pd.read_csv("output/vs.csv")
                st.dataframe(df_vs, use_container_width=True)
                
                # Download Button
                st.download_button(
                    label="Download SDTM CSV",
                    data=df_vs.to_csv(index=False),
                    file_name="vs_sdtm.csv",
                    mime="text/csv"
                )
            else:
                st.error("CSV not generated. Check terminal for R errors.")

else:
    st.info("Please enter your API Key and upload a CSV to begin.")