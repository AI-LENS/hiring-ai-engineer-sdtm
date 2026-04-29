from agent.planner import create_mapping_plan
from agent.r_generator import generate_r_script, run_r_script
from agent.validator import run_validation
from agent.reporter import generate_report


def main():
    print("CLINICAL AGENT STARTED")

    print("STEP 1: Generating mapping plan...\n")

    plan = create_mapping_plan()

    if not plan:
        print("Planner failed. Stopping execution.")
        return

    print("Planner completed successfully \n")

    print("STEP 2: Generating R script...\n")
    generate_r_script(plan)
    print("R script generated successfully \n")

    print("STEP 3: Running R transformation...\n")
    run_r_script()
    print("R execution completed \n")

    print("STEP 4: Running validation...\n")
    run_validation()
    print("Validation completed \n")

    print("STEP 5: Generating final report...\n")
    generate_report()
    print("Report generated successfully \n")

    print("CLINICAL AGENT FINISHED")

    print("Generated files:vs.csv,genrated.R,valdation_report.md")
    

if __name__ == "__main__":
    main()