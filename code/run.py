from tool_wrapper import generate_r_script, run_r
from validator import validate

def main():
    print("Running SDTM conversion...")

    generate_r_script()
    run_r()

    report = validate("output/vs.csv", "data/sdtm_ct.csv")

    print("Done!")
    print(report)

if __name__ == "__main__":
    main()