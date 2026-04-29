from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    raw_data_summary: str
    ct_data_summary: str
    plan: str
    r_script: str
    validation_results: str
    status: str  # "planning", "executing", "validating", "complete"
    errors: List[str]