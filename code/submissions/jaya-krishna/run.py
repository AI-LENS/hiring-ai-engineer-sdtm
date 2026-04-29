import os
from dotenv import load_dotenv
load_dotenv()
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from agent.graph import build_graph, MAX_ITERATIONS


def main():
    print("Initializing LangGraph SDTM VS Generation Pipeline...")
    app = build_graph()

    initial_instruction = HumanMessage(content=(
        "Begin the SDTM conversion process. Analyze the input schemas, "
        "write and execute the R script utilizing sdtm.oak, run validation, "
        "and conclude with 'PROCESS COMPLETE' upon success."
    ))

    try:
        final_state = app.invoke({
            "messages": [initial_instruction],
            "status": "start",
            "iterations": 0,
        })
        role_map = {
            AIMessage:     "Agent",
            HumanMessage:  "Human",
            SystemMessage: "System",
            ToolMessage:   "Tool",
        }

        with open("notes.md", "w") as f:
            f.write("# SDTM Pipeline Execution Log\n\n")

            for msg in final_state["messages"]:
                role = role_map.get(type(msg), "Unknown")
                f.write(f"### {role}:\n{msg.content}\n\n")

                # Log any tool calls the agent made
                if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                    for tool_call in msg.tool_calls:
                        f.write(f"*Called Tool: `{tool_call['name']}` with args: `{tool_call['args']}`*\n\n")

        # Surface final pipeline outcome clearly
        final_status = final_state.get("status", "unknown")
        iterations_used = final_state.get("iterations", "unknown")

        if final_status == "completed":
            print(f"\n Pipeline completed successfully in {iterations_used}/{MAX_ITERATIONS} iterations.")
            print("Artifacts stored in output/ directory.")
        elif final_status == "limit_reached":
            print(f"\n Pipeline hit the iteration limit ({MAX_ITERATIONS}). Output may be incomplete.")
            print("Review notes.md and output/validation_report.md for details.")
        else:
            print(f"\n Pipeline ended with status: '{final_status}'. Review notes.md for details.")
    except Exception as e:
        print(f"Pipeline failure encountered: {str(e)}")


if __name__ == "__main__":
    main()