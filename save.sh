#!/bin/bash
# Saves a finished FS3 version to GitHub, from the server, in one step.
# Run it only after the version has been tested in the browser.
#
#   bash save.sh 112 "new hangar, CLASSIC removed"
#
# It stages everything that is not ignored, so a logic file from an earlier
# version that never made it into the repository is carried along instead of
# being left behind again.
set -e
cd /home/belisarius/fs3-build || exit 1

V="$1"
MSG="$2"

if [ -z "$V" ] || [ -z "$MSG" ]; then
  echo "Usage: bash save.sh <version> \"<description>\""
  echo "   eg: bash save.sh 112 \"new hangar, CLASSIC removed\""
  exit 1
fi

if [ ! -f "hlp_shooter_v${V}_logic.html" ]; then
  echo "STOP: hlp_shooter_v${V}_logic.html does not exist here."
  echo "      Run the patch first, then save."
  exit 1
fi

# The index in CODEMAP.md is rebuilt from the newest logic file, so it never
# describes an older version than the one being saved.
python3 codemap.py

git add -A

if git diff --cached --quiet; then
  echo "Nothing to save - the repository is already up to date."
  exit 0
fi

echo
echo "--- these files are being saved ---"
git diff --cached --name-only
echo

git commit -q -m "v${V}: ${MSG}"
git push

echo
echo "DONE: v${V} is in the repository."
