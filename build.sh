#!/bin/bash
cd /home/belisarius/fs3-build || exit 1
python3 build_game.py \
  --icons icons \
  --mounts hlp_mounts_final.json \
  --game "$(ls -1 hlp_shooter_v*_logic.html | sort -V | tail -1)" \
  --out /var/www/html/fs3/game.html \
  --loader /var/www/html/fs3/index.html \
  "$@"   # passes on --laut for the old, long output
# What the page does not carry itself is copied next to it. One line about
# it at the end, not three (Silvio, 16.11.2026: the build spelled out far
# too much).
copied=""
# Music is not in the page; the game fetches it from here while it plays.
if [ -d music ]; then
  mkdir -p /var/www/html/fs3/music && cp -u music/*.mp3 /var/www/html/fs3/music/ 2>/dev/null
  copied="Musik $(ls -1 music/*.mp3 2>/dev/null | wc -l)"
fi
# Backgrounds (v229): too big to live in the page, fetched like the music.
if [ -d nebulae ]; then
  mkdir -p /var/www/html/fs3/nebulae && cp -u nebulae/* /var/www/html/fs3/nebulae/ 2>/dev/null
  copied="$copied, Hintergruende $(ls -1 nebulae/* 2>/dev/null | wc -l) ($(du -sh nebulae 2>/dev/null | cut -f1))"
fi
# 3D models (v191): the game fetches a hull's model the first time it shows it.
if [ -d models ]; then
  mkdir -p /var/www/html/fs3/models && cp -ru models/. /var/www/html/fs3/models/
  copied="$copied, Modelle $(ls -1d models/*/ 2>/dev/null | wc -l) Schiffe"
fi
[ -n "$copied" ] && echo "  Kopiert: ${copied#, }"
