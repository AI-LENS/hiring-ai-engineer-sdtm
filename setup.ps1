Write-Host "Initializing isolated Python Virtual Environment..." -ForegroundColor Cyan
python -m venv agent_env

Write-Host "Installing Python Agent Dependencies..." -ForegroundColor Cyan
.\agent_env\Scripts\python.exe -m pip install --upgrade pip
.\agent_env\Scripts\pip.exe install -r requirements.txt

# NEW: Create a local folder for R packages to avoid Admin permission errors
$RLibPath = "$PWD\R_libs"
if (-Not (Test-Path $RLibPath)) {
    New-Item -ItemType Directory -Path $RLibPath | Out-Null
}
# Tell R to use this local folder for this session
$env:R_LIBS_USER = $RLibPath

# Ensures R dependencies are downloaded directly from CRAN
Rscript -e "if (!require('remotes')) install.packages('remotes', repos='https://cloud.r-project.org')"
Rscript -e "remotes::install_github('pharmaverse/sdtm.oak', upgrade='never')"
Rscript -e "if (!require('pharmaverseraw')) install.packages('pharmaverseraw', repos='https://cloud.r-project.org')"
Rscript -e "if (!require('dplyr')) install.packages(c('dplyr', 'readr'), repos='https://cloud.r-project.org')"

Write-Host "Setup complete. Environment is ready." -ForegroundColor Green