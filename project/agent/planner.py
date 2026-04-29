import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv

from agent.prompts import PLANNER_PROMPT
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_raw_columns():
    df = pd.read_csv("data/vs_raw.csv")
    return list(df.columns)

def ask_groq(message):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": PLANNER_PROMPT
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": 0
    }

    response = requests.post(
        GROQ_API_URL,
        headers=headers,
        json=payload
    )

    return response.json()


def create_mapping_plan():
    columns = get_raw_columns()

    prompt = f"""
These are the raw clinical trial columns:
{columns}
Map them into SDTM VS variables.
Supported tests:
TEMP,SYSBP,DIABP,PULSE
Return JSON only.
"""
    result = ask_groq(prompt)
    print(json.dumps(result))

    if "choices" not in result:
        print("Groq API Error")
        print(result)
        return None

    content = result["choices"][0]["message"]["content"]

    content = content.replace("```json", "").replace("```", "").strip()

    try:
        plan = json.loads(content)
        print("\nFinal Mapping Plan:\n")
        print(json.dumps(plan, indent=2))
        return plan

    except Exception as e:
        print("JSON Parse Error:", e)
        print(content)
        return None

if __name__ == "__main__":
    final_plan = create_mapping_plan()

    if final_plan:
        print("\nPlanner working successfully ")
    else:
        print("\nPlanner failed")