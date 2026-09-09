#!/bin/bash
cd /home/belisarius/fs3-build || exit 1
python3 build_game.py \
  --sprites sprites \
  --icons icons \
  --mounts hlp_mounts_final.json \
  --game "$(ls -1 hlp_shooter_v*_logic.html | sort -V | tail -1)" \
  --out /var/www/html/fs3/index.html
