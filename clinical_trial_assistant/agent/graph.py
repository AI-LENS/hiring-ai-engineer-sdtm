from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from .state import AgentState
from .tools import read_csv_metadata, execute_r_script
from .prompts import SYSTEM_PROMPT
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")



llm = ChatGroq(model="llama-3.3-70b-versatile")

def planner_node(state: AgentState):
    # LLM decides which raw column goes to which SDTM variable
    prompt = f"{SYSTEM_PROMPT}\nRaw Data: {state['raw_data_summary']}\nCT: {state['ct_data_summary']}\nCreate a mapping plan."
    response = llm.invoke(prompt)
    return {"plan": response.content, "status": "executing"}

# ... (imports remain the same as Source 17)

def generator_node(state: AgentState):
    prompt = f"""
    {SYSTEM_PROMPT}

    INPUT FILES:
    - Raw Data is located at: "output/raw_data.csv"
    - CT Data is located at: "output/ct_data.csv"

    DATA CONTEXT:
    {state['raw_data_summary']}
    {state['ct_data_summary']}

    PLAN:
    {state['plan']}

    TASK:
    Generate a full R script using 'sdtm.oak'.
    1. Read inputs using read.csv("output/raw_data.csv") and read.csv("output/ct_data.csv").
    2. Map TEMP, SYSBP, DIABP, and PULSE using the long-format pipeline.
    3. Save the final dataset to "output/vs.csv" using write.csv(..., row.names=FALSE).
    """
    response = llm.invoke(prompt)
    return {"r_script": response.content}


def executor_node(state: AgentState):
    res = execute_r_script(state['r_script'])

    if "Error" in res:
        return {"validation_results": res, "status": "complete"}

    try:
        df = pd.read_csv("output/vs.csv")

        required_cols = [
            "STUDYID","USUBJID","VSTESTCD",
            "VSORRES","VSORRESU"
        ]

        missing = [c for c in required_cols if c not in df.columns]

        if missing:
            return {
                "validation_results": f"Missing columns: {missing}",
                "status": "complete"
            }

        return {
            "validation_results": f"Success. Rows: {len(df)}",
            "status": "complete"
        }

    except Exception as e:
        return {
            "validation_results": str(e),
            "status": "complete"
        }

workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("generator", generator_node)
workflow.add_node("executor", executor_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "generator")
workflow.add_edge("generator", "executor")
workflow.add_edge("executor", END)

app_graph = workflow.compile()