import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from agent.planner import SDTMPlanner
from agent.generator import RScriptGenerator
from agent.validator import SDTMValidator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

log = logging.getLogger("run")

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

RAW_CSV = INPUT_DIR / "vs_raw.csv"
CT_CSV = INPUT_DIR / "sdtm_ct.csv"
GOLDEN_CSV = INPUT_DIR / "vs_golden.csv"

R_SCRIPT = OUTPUT_DIR / "generated.R"
VS_OUT = OUTPUT_DIR / "vs.csv"
VAL_REPORT = OUTPUT_DIR / "validation_report.md"
DIFF_REPORT = OUTPUT_DIR / "diff_report.md"


def main():
    log.info("🚀 Starting SDTM VS pipeline")

    planner = SDTMPlanner(RAW_CSV, CT_CSV)
    plan = planner.run()

    generator = RScriptGenerator(
        plan=plan,
        raw_csv=RAW_CSV,
        ct_csv=CT_CSV,
        vs_out=VS_OUT,
        r_script_path=R_SCRIPT,
    )
    generator.write()

    if not generator.execute():
        log.error("❌ R execution failed")
        sys.exit(1)

    validator = SDTMValidator(
        vs_csv=VS_OUT,
        ct_csv=CT_CSV,
        golden_csv=GOLDEN_CSV,
        val_report=VAL_REPORT,
        diff_report=DIFF_REPORT,
    )
    validator.validate()
    validator.diff_vs_golden()

    log.info("✅ Pipeline completed successfully")


if __name__ == "__main__":
    main()