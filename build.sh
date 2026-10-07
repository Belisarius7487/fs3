#!/bin/bash
cd /home/belisarius/fs3-build || exit 1
python3 build_game.py \
  --sprites sprites \
  --icons icons \
  --mounts hlp_mounts_final.json \
  --game "$(ls -1 hlp_shooter_v*_logic.html | sort -V | tail -1)" \
  --out /var/www/html/fs3/game.html \
  --loader /var/www/html/fs3/index.html
# Music is not in the page; the game fetches it from here while it plays.
if [ -d music ]; then
  mkdir -p /var/www/html/fs3/music && cp -u music/*.mp3 /var/www/html/fs3/music/ 2>/dev/null
  echo "Musik kopiert: $(ls -1 music/*.mp3 2>/dev/null | wc -l) Stuecke"
fi
# 3D models (v191): the game fetches a hull's model the first time it shows it.
if [ -d models ]; then
  mkdir -p /var/www/html/fs3/models && cp -ru models/. /var/www/html/fs3/models/
  echo "Modelle kopiert: $(ls -1d models/*/ 2>/dev/null | wc -l) Schiffe"
fi
