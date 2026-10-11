#!/bin/bash
# FS3 - runs at the start of every Claude Code session.
#
# Nothing has to be installed for this project: it is plain node and python3,
# with no package.json and no requirements.txt. Playwright and Chromium, which
# the two browser stages need, come with the cloud container.
#
# So this hook does not install, it ORIENTS: it says which version is the
# newest, whether src/ and that logic file still agree, and whether the tools
# the checks need are there. A cloud session starts with no memory of the last
# one, and that is exactly what it would otherwise have to find out first.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0

echo "FS3 — Stand dieser Sitzung"

LOGIC=$(ls -1 hlp_shooter_v*_logic.html 2>/dev/null | sort -V | tail -1)
if [ -n "$LOGIC" ]; then
  VER=$(sed -E 's/.*_v([0-9]+)_logic\.html/\1/' <<<"$LOGIC")
  echo "  Neueste Version: v$VER  ($LOGIC)"
  echo "  Nächste Version wäre v$((VER + 1))"
  if python3 assemble.py "$VER" --verify > /dev/null 2>&1; then
    echo "  src/ und v$VER stimmen überein"
  else
    echo "  ACHTUNG: src/ ergibt nicht v$VER — hat jemand src/ geändert, ohne"
    echo "           assemble.py laufen zu lassen? Vor dem Prüfen klären."
  fi
else
  echo "  ACHTUNG: keine Logikdatei gefunden"
fi

echo "  Zweig: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unbekannt)"

# What the check stages need. Missing tools are worth knowing before a stage
# dies halfway through.
MISS=""
command -v node    > /dev/null || MISS="$MISS node"
command -v python3 > /dev/null || MISS="$MISS python3"
[ -d "$(npm root -g 2>/dev/null)/playwright" ] || MISS="$MISS playwright(fieldsim+warpsim)"
if [ -n "$MISS" ]; then
  echo "  FEHLT:$MISS"
else
  echo "  Werkzeuge: node $(node --version), $(python3 --version), Playwright da"
fi

# The exec bit does not survive every way of getting the files onto a machine.
[ -f checks.sh ] && [ ! -x checks.sh ] && chmod +x checks.sh

echo "  Prüfen mit: ./checks.sh   (oder ./checks.sh --fast ohne die Browserstufen)"
echo "  Regeln stehen in CLAUDE.md"

exit 0
