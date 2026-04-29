def generate_r_script():
    print("Generating R script (fixed)...")

    script = """
raw <- read.csv("../../../vs_raw.csv")

temp <- data.frame(VSTESTCD="TEMP", VSORRES=raw$IT.TEMP)
sysbp <- data.frame(VSTESTCD="SYSBP", VSORRES=raw$SYS_BP)
diabp <- data.frame(VSTESTCD="DIABP", VSORRES=raw$DIA_BP)
pulse <- data.frame(VSTESTCD="PULSE", VSORRES=raw$PULSE)

final <- rbind(temp, sysbp, diabp, pulse)

write.csv(final, "submissions/subbareddy/output/vs.csv", row.names=FALSE)
"""

    with open("submissions/subbareddy/output/generated.R", "w") as f:
        f.write(script)

    print("generated.R created successfully")