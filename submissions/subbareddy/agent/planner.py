def create_plan():
    """
    Defines the execution plan for SDTM pipeline
    """
    plan = [
        {
            "step": 1,
            "name": "Generate R Script",
            "action": "codegen"
        },
        {
            "step": 2,
            "name": "Execute R Script",
            "action": "execute"
        },
        {
            "step": 3,
            "name": "Validate Output",
            "action": "validate"
        }
    ]
    return plan