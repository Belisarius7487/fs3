#!/bin/bash
# FS3 - run every check stage against one logic file.
#
#   ./checks.sh              the newest hlp_shooter_v*_logic.html
#   ./checks.sh 216          that version
#   ./checks.sh --fast       everything except the two browser stages
#
# Exit code 0 means every stage is green, anything else means at least one
# is not. The full output of each stage is kept in checks.log.
#
# Why the exit code of a stage is not enough: swtest reports its problems in
# the text and still exits 0. So a stage counts as failed when it exits
# non-zero OR its output names a non-zero number of failures or problems OR
# it prints a FAIL line.
set -uo pipefail
cd "$(dirname "$0")" || exit 1

FAST=0
VER=""
for a in "$@"; do
  case "$a" in
    --fast) FAST=1 ;;
    [0-9]*) VER="$a" ;;
    *) echo "unknown argument: $a"; exit 2 ;;
  esac
done

if [ -n "$VER" ]; then
  LOGIC="hlp_shooter_v${VER}_logic.html"
else
  LOGIC=$(ls -1 hlp_shooter_v*_logic.html 2>/dev/null | sort -V | tail -1)
fi
[ -f "$LOGIC" ] || { echo "STOP: $LOGIC does not exist. Run assemble.py first."; exit 2; }

# The commonest way to check nothing at all: change a part in src/ and then
# run the stages against a logic file assembled before the change. Compared
# by text, not by file time - a fresh clone sets every file time at once.
LV=$(sed -E 's/.*_v([0-9]+)_logic\.html/\1/' <<<"$LOGIC")
if ! python3 assemble.py "$LV" --verify > /dev/null 2>&1; then
  echo "STOP: $LOGIC is not what the parts in src/ make."
  python3 assemble.py "$LV" --verify 2>&1 | sed 's/^/      /'
  exit 2
fi

MOUNTS=hlp_mounts_final.json
LOG=checks.log
: > "$LOG"
echo "FS3 checks against $LOGIC"
echo

# loadtest expects the script of the logic file as v82.js.
python3 - "$LOGIC" <<'EOF' || exit 2
import re, sys
s = open(sys.argv[1], encoding='utf-8').read()
open('v82.js', 'w', encoding='utf-8').write(
    re.search(r'<script[^>]*>([\s\S]*)</script>', s).group(1))
EOF

PASS=0
FAILED=()

# Decides whether a stage counts as failed, and says why. Its exit code is
# not enough on its own: swtest reports its problems in the text and warpsim
# calls them "findings".
judge() {
  local name="$1" out="$2" rc="$3"
  {
    echo "===== $name ====="
    printf '%s\n' "$out"
    echo "----- exit $rc -----"
    echo
  } >> "$LOG"
  if [ "$rc" -ne 0 ] \
     || grep -qE '[1-9][0-9]* (problems?|failed|findings)' <<<"$out" \
     || grep -qE '^ *FAIL' <<<"$out"; then
    echo "FAILED"
    printf '%s\n' "$out" | grep -E '^ *FAIL|[1-9][0-9]* (problems?|failed|findings)|Error|error:' | head -4 | sed 's/^/             /'
    FAILED+=("$name")
  else
    echo "ok"
    PASS=$((PASS + 1))
  fi
}

run() {
  local name="$1"; shift
  printf '  %-10s ' "$name"
  local out rc
  out=$("$@" 2>&1); rc=$?
  judge "$name" "$out" "$rc"
}

run "syntax"   node --check v82.js
run "loadtest" node loadtest.js
run "swtest"   node swtest.js   "$LOGIC"
run "docksim"  node docksim.js  "$LOGIC" "$MOUNTS"
run "mechsim"  node mechsim.js
run "shipsim"  node shipsim.js  "$LOGIC"
run "callsim"  node callsim.js  "$LOGIC"
run "pausesim" node pausesim.js "$LOGIC"
run "hudsim"   node hudsim.js   "$LOGIC"
run "ramsim"   node ramsim.js   "$LOGIC"
run "wpnsim"   node wpnsim.js   "$LOGIC"
run "nctest"   node nctest.js   "$LOGIC"

# These two load the whole game into a headless browser and play real
# missions. They are the slow ones - around ten minutes each - and they are
# the only stages that can see whether a mission actually plays out.
if [ $FAST -eq 1 ]; then
  echo
  echo "  fieldsim and warpsim skipped (--fast). Run without --fast before delivering."
else
  # Side by side, not one after the other. They are independent, each keeps
  # about one core busy, and warpsim alone is around an hour and a half -
  # measured at 1.6 minutes a mission over missions 1-60. Run in turn they
  # put the wait past two hours for no reason.
  #
  # Their output goes to a file as it is produced, so the run can be watched
  # while it happens. Captured in a variable, as the short stages are, there
  # is nothing to see until the stage ends.
  echo "  fieldsim and warpsim now run side by side; this takes a good hour."
  echo "  Watch them: tail -f checks.fieldsim.log checks.warpsim.log"
  node fieldsim.js "$LOGIC" "$MOUNTS" > checks.fieldsim.log 2>&1 &
  FPID=$!
  node warpsim.js  "$LOGIC" "$MOUNTS" > checks.warpsim.log 2>&1 &
  WPID=$!
  wait $FPID; FRC=$?
  wait $WPID; WRC=$?
  printf '  %-10s ' "fieldsim"; judge "fieldsim" "$(cat checks.fieldsim.log)" "$FRC"
  printf '  %-10s ' "warpsim";  judge "warpsim"  "$(cat checks.warpsim.log)"  "$WRC"
fi

echo
if [ ${#FAILED[@]} -eq 0 ]; then
  echo "ALL GREEN - $PASS stages passed. Details in $LOG"
  exit 0
fi
echo "NOT GREEN - $PASS passed, failed: ${FAILED[*]}"
echo "Details in $LOG"
exit 1
