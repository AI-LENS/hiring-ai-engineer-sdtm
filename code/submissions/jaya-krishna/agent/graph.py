import operator
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from agent.tools import get_data_schemas, execute_r_script, validate_sdtm_output


MAX_ITERATIONS = 5
CANONICAL_R_SCRIPT = """\
.libPaths("R_libs")
library(sdtm.oak)
library(dplyr)
library(readr)

raw_ds <- read_csv("csv_files/vs_raw.csv")

raw_ds <- generate_oak_id_vars(
  raw_ds,
  pat_var   = "PATNUM",
  raw_ds_nm = "vs_raw"
)

# --- TEMP ---
temp_ds <- raw_ds |>
  assign_no_ct(raw_var = "IT.TEMP", tgt_var = "VSORRES") |>
  hardcode_ct(tgt_var = "VSTESTCD", ct_val = "TEMP",        ct_clst_cd = "C66741") |>
  hardcode_ct(tgt_var = "VSTEST",   ct_val = "Temperature", ct_clst_cd = "C67153") |>
  assign_ct(  raw_var = "TMPTC",    tgt_var = "VSORRESU",   ct_clst_cd = "C66770")

# --- SYSBP ---
sysbp_ds <- raw_ds |>
  assign_no_ct(raw_var = "SYS_BP",  tgt_var = "VSORRES") |>
  hardcode_ct(tgt_var = "VSTESTCD", ct_val = "SYSBP",                   ct_clst_cd = "C66741") |>
  hardcode_ct(tgt_var = "VSTEST",   ct_val = "Systolic Blood Pressure", ct_clst_cd = "C67153") |>
  hardcode_ct(tgt_var = "VSORRESU", ct_val = "mmHg",                    ct_clst_cd = "C66770")

# --- DIABP ---
diabp_ds <- raw_ds |>
  assign_no_ct(raw_var = "DIA_BP",  tgt_var = "VSORRES") |>
  hardcode_ct(tgt_var = "VSTESTCD", ct_val = "DIABP",                    ct_clst_cd = "C66741") |>
  hardcode_ct(tgt_var = "VSTEST",   ct_val = "Diastolic Blood Pressure", ct_clst_cd = "C67153") |>
  hardcode_ct(tgt_var = "VSORRESU", ct_val = "mmHg",                     ct_clst_cd = "C66770")

# --- PULSE ---
pulse_ds <- raw_ds |>
  assign_no_ct(raw_var = "PULSE",   tgt_var = "VSORRES") |>
  hardcode_ct(tgt_var = "VSTESTCD", ct_val = "PULSE",      ct_clst_cd = "C66741") |>
  hardcode_ct(tgt_var = "VSTEST",   ct_val = "Pulse Rate", ct_clst_cd = "C67153") |>
  hardcode_ct(tgt_var = "VSORRESU", ct_val = "beats/min",  ct_clst_cd = "C66770")

vs_long <- bind_rows(temp_ds, sysbp_ds, diabp_ds, pulse_ds) |>
  mutate(
    STUDYID = STUDY,
    USUBJID = paste(STUDY, PATNUM, sep = "-"),
    DOMAIN  = "VS"
  )

write_csv(vs_long, "output/vs.csv", na = "")
"""


# 1. Define the Graph State
class AgentState(TypedDict):
    """
    Maintains the state of the graph across iterations.
    messages:   Full dialogue between system, agent, and tools.
    status:     Pipeline outcome — continue / completed / limit_reached.
    iterations: Agent cycle counter enforcing MAX_ITERATIONS cap.
    """
    messages:   Annotated[list[BaseMessage], operator.add]
    status:     str
    iterations: int


# LLM and tool initialization
llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0.0
)

tools = [get_data_schemas, execute_r_script, validate_sdtm_output]
llm_with_tools = llm.bind_tools(tools)


# 2. Define the core cognitive node
def agent_node(state: AgentState):
    """
    The reasoning engine. On iteration 0 the system prompt is prepended.
    The agent decides which tool to call and interprets tool results.
    On retries it reads stderr and fixes only the reported lines.
    """
    messages   = state["messages"]
    iterations = state.get("iterations", 0)

    if iterations == 0:
        system_prompt = SystemMessage(content=f"""
You are a Biometrics Data Engineer running an SDTM VS conversion pipeline.

=== PIPELINE (follow in order) ===
1. Call get_data_schemas to confirm column names and valid CT values.
2. Call execute_r_script with the canonical R script provided below.
3. Call validate_sdtm_output to check CT compliance and output shape.
4. If validation fails: read the specific error, fix only that line in the
   R script, call execute_r_script again, then validate again.
5. When validation passes say exactly: PROCESS COMPLETE

=== WHY THE SCRIPT IS PRE-WRITTEN ===
The sdtm.oak function signatures, column mappings, and file paths are fixed
domain knowledge. Generating them from scratch risks hallucination (e.g.
inventing map_vs() which does not exist). The LLM's role is schema
confirmation and targeted error recovery — not script authorship.

=== CANONICAL R SCRIPT — submit this verbatim in step 2 ===
{CANONICAL_R_SCRIPT}

=== IF EXECUTE_R_SCRIPT RETURNS FAILURE ===
- Read stderr carefully.
- Fix only the exact line(s) mentioned.
- Do not rewrite the whole script.
- Do not change file paths or function names that are not in the error.

=== BANNED FUNCTIONS — these do not exist in sdtm.oak ===
map_vs(), create_vs(), oak_map()
""")
        messages = [system_prompt] + messages

    response = llm_with_tools.invoke(messages)

    iterations += 1
    if "PROCESS COMPLETE" in response.content:
        status = "completed"
    elif iterations >= MAX_ITERATIONS:
        status = "limit_reached"
    else:
        status = "continue"

    return {
        "messages":   [response],
        "status":     status,
        "iterations": iterations,
    }


# 3. Define the tool execution node
def tool_node(state: AgentState):
    """
    Executes tools requested by the LLM and returns results as ToolMessages.
    No interception or override — what the agent submits is what runs.
    The canonical script is provided to the agent in the system prompt;
    enforcing correctness is the agent's responsibility, not this node's.
    """
    messages     = state["messages"]
    last_message = messages[-1]
    tool_map     = {t.name: t for t in tools}
    tool_responses = []

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            selected_tool = tool_map[tool_name]
            result        = selected_tool.invoke(tool_args)

            # ToolMessage with matching tool_call_id is required by LangChain
            # so the model can correlate each result to its originating call.
            tool_responses.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                )
            )

    return {"messages": tool_responses}


# 4. Define Edge Logic
def should_continue(state: AgentState):
    """Determines whether to cycle back to the agent or terminate the graph."""
    messages     = state["messages"]
    last_message = messages[-1]

    if state["status"] in ("completed", "limit_reached"):
        return "end"
    elif hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    else:
        return "end"


# 5. Compile the LangGraph
def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end":      END
        }
    )
    workflow.add_edge("tools", "agent")
    return workflow.compile()