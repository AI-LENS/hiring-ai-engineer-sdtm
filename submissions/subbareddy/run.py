from agent.codegen import generate_r_script
from agent.executor import run_r_script
from agent.validator import validate_output
from agent.planner import create_plan


def run_pipeline():
    plan = create_plan()

    for step in plan:
        print(f"Step {step['step']}: {step['name']}...")

        if step["action"] == "codegen":
            generate_r_script()

        elif step["action"] == "execute":
            run_r_script()

        elif step["action"] == "validate":
            validate_output()


if __name__ == "__main__":
    run_pipeline()