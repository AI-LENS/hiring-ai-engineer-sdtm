#!/usr/bin/env bash
# setup.sh — One-time setup: install R packages and export sample datasets.
# Run once before the agent:  bash setup.sh

set -euo pipefail

echo "═══════════════════════════════════════════════════════"
echo "  SDTM VS Agent — One-time Setup"
echo "═══════════════════════════════════════════════════════"

# ── 1. Check R is available ────────────────────────────────────────────────
if ! command -v Rscript &>/dev/null; then
  echo "ERROR: Rscript not found. Install R from https://cran.r-project.org/"
  exit 1
fi

R_VERSION=$(Rscript --version 2>&1 | head -1)
echo "R found: $R_VERSION"

# ── 2. Install CRAN packages ───────────────────────────────────────────────
echo ""
echo "Installing CRAN packages (sdtm.oak, dplyr, remotes)…"
Rscript -e 'install.packages(
  c("sdtm.oak", "dplyr", "remotes"),
  repos = "https://cloud.r-project.org",
  quiet = TRUE
)'

# ── 3. Install pharmaverse GitHub packages ─────────────────────────────────
echo ""
echo "Installing pharmaverseraw and pharmaversesdtm from GitHub…"
Rscript -e 'remotes::install_github("pharmaverse/pharmaverseraw",  quiet = TRUE)'
Rscript -e 'remotes::install_github("pharmaverse/pharmaversesdtm", quiet = TRUE)'

# ── 4. Export CSV datasets ─────────────────────────────────────────────────
echo ""
echo "Exporting vs_raw.csv and vs_golden.csv …"
mkdir -p data

Rscript -e 'write.csv(pharmaverseraw::vs_raw,      "data/vs_raw.csv",    row.names = FALSE)'
Rscript -e 'write.csv(pharmaversesdtm::vs,         "data/vs_golden.csv", row.names = FALSE)'

# ── 5. Download CT CSV ─────────────────────────────────────────────────────
echo ""
echo "Downloading sdtm_ct.csv from pharmaverse workshop…"
CT_URL="https://raw.githubusercontent.com/pharmaverse/sdtm.oak-workshop/main/datasets/sdtm_ct.csv"

if command -v curl &>/dev/null; then
  curl -sSL "$CT_URL" -o data/sdtm_ct.csv
elif command -v wget &>/dev/null; then
  wget -q "$CT_URL" -O data/sdtm_ct.csv
else
  echo "WARNING: curl/wget not found. Please download manually:"
  echo "  $CT_URL  →  data/sdtm_ct.csv"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Setup complete. Files in data/:"
ls -lh data/
echo ""
echo "  Next step:  export GOOGLE_API_KEY=<your-key>"
echo "              python agent.py"
echo "═══════════════════════════════════════════════════════"
