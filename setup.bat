@echo off
REM setup.bat — One-time setup: install R packages and export sample datasets.
REM Run once before the agent:  setup.bat

echo ═══════════════════════════════════════════════════════
echo   SDTM VS Agent — One-time Setup
echo ═══════════════════════════════════════════════════════

REM ── 1. Check R is available ────────────────────────────────────────────────
where Rscript >nul 2>nul
if %errorlevel% neq 0 (
  echo ERROR: Rscript not found. Install R from https://cran.r-project.org/
  pause
  exit /b 1
)

for /f "tokens=*" %%i in ('Rscript --version 2^>^&1') do set R_VERSION=%%i
echo R found: %R_VERSION%

REM ── 2. Install CRAN packages ───────────────────────────────────────────────
echo.
echo Installing CRAN packages (sdtm.oak, dplyr, remotes)…
Rscript -e "install.packages(c('sdtm.oak', 'dplyr', 'remotes'), repos = 'https://cloud.r-project.org', quiet = TRUE)"

REM ── 3. Install pharmaverse GitHub packages ─────────────────────────────────
echo.
echo Installing pharmaverseraw and pharmaversesdtm from GitHub…
Rscript -e "remotes::install_github('pharmaverse/pharmaverseraw', quiet = TRUE)"
Rscript -e "remotes::install_github('pharmaverse/pharmaversesdtm', quiet = TRUE)"

REM ── 4. Export CSV datasets ─────────────────────────────────────────────────
echo.
echo Exporting vs_raw.csv and vs_golden.csv …
if not exist data mkdir data

Rscript -e "write.csv(pharmaverseraw::vs_raw, 'data/vs_raw.csv', row.names = FALSE)"
Rscript -e "write.csv(pharmaversesdtm::vs, 'data/vs_golden.csv', row.names = FALSE)"

REM ── 5. Download CT CSV ─────────────────────────────────────────────────────
echo.
echo Downloading sdtm_ct.csv from pharmaverse workshop…
set CT_URL=https://raw.githubusercontent.com/pharmaverse/sdtm.oak-workshop/main/datasets/sdtm_ct.csv

where curl >nul 2>nul
if %errorlevel% equ 0 (
  curl -sSL "%CT_URL%" -o data/sdtm_ct.csv
) else (
  where wget >nul 2>nul
  if %errorlevel% equ 0 (
    wget -q "%CT_URL%" -O data/sdtm_ct.csv
  ) else (
    echo WARNING: curl/wget not found. Please download manually:
    echo   %CT_URL%  -^>  data/sdtm_ct.csv
  )
)

echo.
echo ═══════════════════════════════════════════════════════
echo   Setup complete. Files in data/:
dir data/
echo.
echo   Next step:  set GOOGLE_API_KEY=<your-key>
echo               python agent.py
echo ═══════════════════════════════════════════════════════
pause
