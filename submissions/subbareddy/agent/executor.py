import subprocess

def run_r_script():
    subprocess.run(
        ["Rscript", "submissions/subbareddy/output/generated.R"],
        check=True
    )