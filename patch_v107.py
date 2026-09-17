#!/usr/bin/env python3
"""FS3 v107 - barrels and volley damage in the switch menu.

Each unlocked fighter or bomber cell gets a line stating how many primary
barrels the hull has and what one volley does in total. Both numbers come
from the same places the game fires from - the packer injected mount data
and volleyDmg() - so the menu cannot drift away from pShoot().

A hull with no mount data falls back to two fixed muzzles in pShoot(), and
those carry no damage figure, so for such a hull the line is left out rather
than stating a number the game does not use.

Reads hlp_shooter_v106_logic.html, writes hlp_shooter_v107_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v106_logic.html", "hlp_shooter_v107_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# ── 1. Two small readers, next to the menu that uses them ────────────
src = replace_once(
    src,
    "function drawShipMenu(){\n  if(!shipMenu) return;",
    """// How many primary barrels a hull really fires with. Read from the mount
// data the packer injects, not from PLAYER_SHIPS, so this number and the one
// pShoot() uses cannot drift apart. Zero means no mount data: pShoot() then
// uses its two fallback muzzles, which carry no damage figure of their own.
function primaryCount(key){
  const m = mountsFor(key);
  return (m && m.primary && m.primary.length) ? m.primary.length : 0;
}
// volleyDmg() is the damage of a single barrel, which is why more barrels do
// not simply multiply. This is what a whole volley lands.
function volleyTotal(n){ if(!n || n < 1) n = 1; return volleyDmg(n)*n; }
function drawShipMenu(){
  if(!shipMenu) return;""",
    "primaryCount helper",
)

# ── 2. The line itself, right of the agility pips ────────────────────
src = replace_once(
    src,
    "      ctx.fillText('AGI', bx+104, by+35); statPips(bx+128, by+36, s.turn, [0.08,0.10,0.12,0.14,0.17], '#ffbb22');",
    "      ctx.fillText('AGI', bx+104, by+35); statPips(bx+128, by+36, s.turn, [0.08,0.10,0.12,0.14,0.17], '#ffbb22');\n"
    "      // Right aligned into the gap the pips leave, one size smaller.\n"
    "      const gn=primaryCount(s.key);\n"
    "      if(gn){\n"
    "        ctx.textAlign='right'; ctx.font='8px Courier New'; ctx.fillStyle='#997733';\n"
    "        ctx.fillText('GUN '+gn+'  DMG '+Math.round(volleyTotal(gn)), bx+bw-6, by+37);\n"
    "        ctx.textAlign='left';\n"
    "      }",
    "gun line",
)

for name in ("function primaryCount(", "function volleyTotal(", "'GUN '+gn+'  DMG '"):
    if name not in src:
        sys.exit("Abbruch: '%s' fehlt im Ergebnis." % name)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
