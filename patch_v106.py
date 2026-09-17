#!/usr/bin/env python3
"""FS3 v106 - hull sprites behind the menu cells.

Every tile in the ship switch menu and every row in the support call menu
shows the hull it offers, faintly, behind its own label. One helper for both
menus: clipped to the cell, drawn before the text, low alpha so the labels
stay readable, and always facing right. Locked or unaffordable rows get a
dimmer version. A missing sprite leaves the cell exactly as it was.

Reads hlp_shooter_v105_logic.html, writes hlp_shooter_v106_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v105_logic.html", "hlp_shooter_v106_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# ── 1. The shared helper, in front of the switch menu ────────────────
src = replace_once(
    src,
    "function drawShipMenu(){\n  if(!shipMenu) return;",
    """// Faint hull behind a menu cell, clipped to it, so a row shows the ship it
// offers instead of its name alone. Drawn before the text and at low alpha
// so the labels stay readable. Fitted whole rather than cropped: a long
// destroyer ends up flat and wide, which is what it looks like. Right
// aligned, away from the label column, and always facing right regardless
// of which way the sprite was drawn. A sprite that has not loaded leaves
// the cell untouched.
const MENU_BG_ALPHA     = 0.26;   // unlocked, or affordable
const MENU_BG_ALPHA_OFF = 0.11;   // locked, or out of tickets
const MENU_BG_PAD       = 3;
function drawHullBg(key, x, y, w, h, lit){
  const img = IMGS[key];
  if(!img || !img.width || !img.height) return;
  const p  = MENU_BG_PAD;
  const sc = Math.min((w-p*2)/img.width, (h-p*2)/img.height);
  if(!(sc > 0)) return;
  const dw = img.width*sc, dh = img.height*sc;
  ctx.save();
  ctx.beginPath(); ctx.rect(x+1, y+1, w-2, h-2); ctx.clip();
  ctx.globalAlpha = lit ? MENU_BG_ALPHA : MENU_BG_ALPHA_OFF;
  ctx.translate(x+w-p-dw/2, y+h/2);
  if(spriteFacing(key)==='left') ctx.scale(-1,1);
  ctx.drawImage(img, -dw/2, -dh/2, dw, dh);
  ctx.restore();
}
function drawShipMenu(){
  if(!shipMenu) return;""",
    "drawHullBg helper",
)

# ── 2. Switch menu cells ─────────────────────────────────────────────
src = replace_once(
    src,
    "    ctx.strokeStyle=cur?'#ffffff':(open?'#ffbb22':'#333'); ctx.lineWidth=cur?2:1;\n"
    "    ctx.strokeRect(bx,by,bw,bh);\n"
    "    ctx.textAlign='left';",
    "    ctx.strokeStyle=cur?'#ffffff':(open?'#ffbb22':'#333'); ctx.lineWidth=cur?2:1;\n"
    "    ctx.strokeRect(bx,by,bw,bh);\n"
    "    drawHullBg(s.key, bx, by, bw, bh, open || cur);\n"
    "    ctx.textAlign='left';",
    "switch menu sprite",
)

# ── 3. Call menu rows ────────────────────────────────────────────────
src = replace_once(
    src,
    "    ctx.strokeStyle=ok?(vas?'#ffbb22':'#4499ff'):'#333'; ctx.lineWidth=1;\n"
    "    ctx.strokeRect(bx,by,bw,bh);\n"
    "    ctx.textAlign='left';",
    "    ctx.strokeStyle=ok?(vas?'#ffbb22':'#4499ff'):'#333'; ctx.lineWidth=1;\n"
    "    ctx.strokeRect(bx,by,bw,bh);\n"
    "    drawHullBg(d.spr, bx, by, bw, bh, ok);\n"
    "    ctx.textAlign='left';",
    "call menu sprite",
)

# ── 4. The Colossus row ──────────────────────────────────────────────
src = replace_once(
    src,
    "    ctx.strokeStyle=ok?'#66ffe0':'#333'; ctx.lineWidth=ok?2:1;\n"
    "    ctx.strokeRect(cbx,cby,cbw,bh);\n"
    "    ctx.textAlign='left';",
    "    ctx.strokeStyle=ok?'#66ffe0':'#333'; ctx.lineWidth=ok?2:1;\n"
    "    ctx.strokeRect(cbx,cby,cbw,bh);\n"
    "    drawHullBg(cd.spr, cbx, cby, cbw, bh, ok);\n"
    "    ctx.textAlign='left';",
    "colossus row sprite",
)

for name in ("drawHullBg(s.key", "drawHullBg(d.spr", "drawHullBg(cd.spr", "function drawHullBg("):
    if name not in src:
        sys.exit("Abbruch: '%s' fehlt im Ergebnis." % name)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
