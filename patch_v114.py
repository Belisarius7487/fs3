#!/usr/bin/env python3
"""FS3 v114 - the kit reaches every window, and two faults in the hangar go.

1. A click inside the hangar that missed a row counted as a click outside and
   closed the panel. The header, the group headings, the gaps between rows and
   the footer all belong to the panel. Both menus now report their own outline
   and swallow anything that lands on it. The call menu had the same fault.

2. The keyboard digits. The groups reorder the list, so a digit taken from the
   roster no longer matched the row it sat on. The order shown is now the order
   the keys follow: 1 to 5 the fighters, 6 to 8 the bombers.

3. The warm accent was taken from the theme's link_hover, rgb(253,191,146),
   which is pale and reads as ochre on a dark surface. It becomes the colour of
   the board links on the forum index. PROVISIONAL: measured off a screenshot,
   which is a JPEG on a dark ground, so the true value is likely a little
   brighter. One line to change once the value is read from index.css.

4. Gloss and transparency enter the kit rather than one screen:
     thRGBA       a theme colour with an alpha on it
     thGloss      one shallow fall of light over the top of a plate, clipped
                  to its outline. Not the old box gradient: it covers the top
                  third and stops.
     thCutGlint   the cut faces of the chamfer, lit, so a corner reads as
                  milled rather than merely missing
   Both are folded into thPlate, so every plate in the game gains them at once.
   Panels are no longer opaque: the battle shows faintly behind them.

5. The shared helpers are rewired to the kit: thBevel, uiCell, uiDialog and
   thButton. That is what carries the change into the call menu, the settings
   panel, the pause panel and the gauges in the bar without any of their
   layouts moving. thPanel is left for the bar surface until the bar is rebuilt.

6. The game over screen is rebuilt. It was the last place still setting 52 px
   Courier and raw hex colours.

Reads hlp_shooter_v113_logic.html, writes hlp_shooter_v114_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v113_logic.html", "hlp_shooter_v114_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def cut_between(text, start, end, new, label):
    if text.count(start) != 1:
        sys.exit("Abbruch (%s): Startmarke %d-mal gefunden, erwartet einmal."
                 % (label, text.count(start)))
    if text.count(end) != 1:
        sys.exit("Abbruch (%s): Endmarke %d-mal gefunden, erwartet einmal."
                 % (label, text.count(end)))
    i, j = text.index(start), text.index(end)
    if j <= i:
        sys.exit("Abbruch (%s): Endmarke steht vor der Startmarke." % label)
    return text[:i] + new + text[j:]


src = open(SRC, encoding="utf-8").read()

# ── 1. The warm accent ───────────────────────────────────────────────
src = replace_once(
    src,
    "    accentWarm:'rgb(253,191,146)' // link_hover",
    "    // The colour of the board links on the forum index, not link_hover:\n"
    "    // that one is pale and turns to ochre on a dark surface.\n"
    "    // PROVISIONAL - measured off a screenshot, to be replaced with the\n"
    "    // exact value from the theme's index.css.\n"
    "    accentWarm:'rgb(208,128,66)'",
    "fire accent",
)

# ── 2. Gloss, glint and alpha join the kit ───────────────────────────
src = replace_once(
    src,
    "// A flat plate. No gradient and no bevel: what marks the edge is a dark\n"
    "// outline all round plus one bright hairline along the top, and the cut\n"
    "// corners do the rest.\n"
    "function thPlate(x, y, w, h, fill, c){\n"
    "  if(c === undefined) c = 6;\n"
    "  thChamferPath(x, y, w, h, c);\n"
    "  ctx.fillStyle = fill;\n"
    "  ctx.fill();\n",
    "// A theme colour with an alpha put on it. The table stores 'rgb(r,g,b)',\n"
    "// which cannot carry one.\n"
    "function thRGBA(role, a){\n"
    "  const c = TH(role);\n"
    "  return c.indexOf('rgb(')===0 ? 'rgba('+c.slice(4,-1)+','+a+')' : c;\n"
    "}\n"
    "// Gloss: one shallow fall of light over the top of a plate, clipped to the\n"
    "// plate's own outline. This is the sheen, and it is deliberately not the\n"
    "// old box gradient - it covers the top third and then stops, so a stack of\n"
    "// plates still reads as a list and not as a stack of boxes.\n"
    "function thGloss(x, y, w, h, c){\n"
    "  ctx.save();\n"
    "  thChamferPath(x, y, w, h, c); ctx.clip();\n"
    "  const gr = ctx.createLinearGradient(0, y, 0, y+Math.max(8, h*0.42));\n"
    "  gr.addColorStop(0, 'rgba(255,255,255,0.075)');\n"
    "  gr.addColorStop(1, 'rgba(255,255,255,0)');\n"
    "  ctx.fillStyle = gr; ctx.fillRect(x, y, w, h);\n"
    "  ctx.restore();\n"
    "}\n"
    "// The two cut faces of the chamfer, lit. The only place in this interface\n"
    "// where a highlight sits on an edge, and what makes the corner read as\n"
    "// milled rather than merely missing.\n"
    "function thCutGlint(x, y, w, h, c, col){\n"
    "  if(c === undefined) c = 6;\n"
    "  ctx.save();\n"
    "  ctx.strokeStyle = col || 'rgba(255,255,255,0.22)'; ctx.lineWidth = 1;\n"
    "  ctx.beginPath();\n"
    "  ctx.moveTo(x+0.5, y+c+0.5);       ctx.lineTo(x+c+0.5, y+0.5);\n"
    "  ctx.moveTo(x+w-c-0.5, y+h-0.5);   ctx.lineTo(x+w-0.5, y+h-c-0.5);\n"
    "  ctx.stroke();\n"
    "  ctx.restore();\n"
    "}\n"
    "// A flat plate: a dark outline all round, one bright hairline along the\n"
    "// top, the gloss over its top third and the cut faces lit. Every surface\n"
    "// in the game comes from here, which is why the sheen is applied once,\n"
    "// in this function, and never per screen.\n"
    "function thPlate(x, y, w, h, fill, c){\n"
    "  if(c === undefined) c = 6;\n"
    "  thChamferPath(x, y, w, h, c);\n"
    "  ctx.fillStyle = fill;\n"
    "  ctx.fill();\n"
    "  thGloss(x, y, w, h, c);\n",
    "gloss and glint",
)

src = replace_once(
    src,
    "  ctx.strokeStyle = TH('edgeLight');\n"
    "  ctx.beginPath();\n"
    "  ctx.moveTo(x+c+0.5, y+0.5); ctx.lineTo(x+w-0.5, y+0.5);\n"
    "  ctx.stroke();\n"
    "}",
    "  ctx.strokeStyle = TH('edgeLight');\n"
    "  ctx.beginPath();\n"
    "  ctx.moveTo(x+c+0.5, y+0.5); ctx.lineTo(x+w-0.5, y+0.5);\n"
    "  ctx.stroke();\n"
    "  thCutGlint(x, y, w, h, c);\n"
    "}",
    "plate glint",
)

# The panel is no longer a wall: the battle shows faintly behind it.
src = replace_once(
    src,
    "  ctx.fillStyle = 'rgba(0,0,0,0.80)';\n"
    "  ctx.fillRect(0, 0, W, H);\n"
    "  thPlate(x, y, w, h, TH('panelBack'), 12);",
    "  ctx.fillStyle = 'rgba(0,0,0,0.62)';\n"
    "  ctx.fillRect(0, 0, W, H);\n"
    "  thPlate(x, y, w, h, thRGBA('panelBack', 0.90), 12);",
    "panel transparency",
)

# ── 3. The shared helpers, rewired to the kit ────────────────────────
src = replace_once(
    src,
    "// The resting edge: light from above left, dark below right. Quiet on\n"
    "// purpose - in this theme a border is not what carries emphasis.\n"
    "function thBevel(x, y, w, h){\n"
    "  ctx.lineWidth = 1;\n"
    "  ctx.strokeStyle = TH('edgeLight');\n"
    "  ctx.beginPath();\n"
    "  ctx.moveTo(x+0.5, y+h-0.5); ctx.lineTo(x+0.5, y+0.5); ctx.lineTo(x+w-0.5, y+0.5);\n"
    "  ctx.stroke();\n"
    "  ctx.strokeStyle = TH('edgeDark');\n"
    "  ctx.beginPath();\n"
    "  ctx.moveTo(x+w-0.5, y+0.5); ctx.lineTo(x+w-0.5, y+h-0.5); ctx.lineTo(x+0.5, y+h-0.5);\n"
    "  ctx.stroke();\n"
    "}",
    "// The resting edge. Once a bevel in the forum's manner, now the kit's\n"
    "// outline: chamfered, one dark line all round, one bright line on top.\n"
    "// Kept under its old name because the bar still calls it for the gauges,\n"
    "// and it disappears when the bar is rebuilt.\n"
    "function thBevel(x, y, w, h){\n"
    "  ctx.lineWidth = 1;\n"
    "  ctx.strokeStyle = TH('edgeDark');\n"
    "  thChamferPath(x+0.5, y+0.5, w-1, h-1, 4);\n"
    "  ctx.stroke();\n"
    "  ctx.strokeStyle = TH('edgeLight');\n"
    "  ctx.beginPath();\n"
    "  ctx.moveTo(x+4.5, y+0.5); ctx.lineTo(x+w-0.5, y+0.5);\n"
    "  ctx.stroke();\n"
    "  thCutGlint(x, y, w, h, 4);\n"
    "}",
    "thBevel",
)

src = replace_once(
    src,
    "function uiCell(x, y, w, h, o){\n"
    "  o = o || {};\n"
    "  if(o.state==='off'){\n"
    "    ctx.fillStyle = TH('back'); ctx.fillRect(x, y, w, h);\n"
    "    ctx.strokeStyle = TH('edgeDark'); ctx.lineWidth = 1;\n"
    "    ctx.strokeRect(x+0.5, y+0.5, w-1, h-1);\n"
    "    return;\n"
    "  }\n"
    "  thPanel(x, y, w, h,\n"
    "          o.state==='on' ? TH('raised')     : TH('panelFront'),\n"
    "          o.state==='on' ? TH('panelFront') : TH('panelBack'));\n"
    "  thBevel(x, y, w, h);\n"
    "  if(o.state==='on')         thGlow(x, y, w, h, 1);\n"
    "  else if(o.state==='ready') thGlow(x, y, w, h, 0.45);\n"
    "}",
    "function uiCell(x, y, w, h, o){\n"
    "  o = o || {};\n"
    "  thPlate(x, y, w, h,\n"
    "          o.state==='on'  ? TH('raised') :\n"
    "          o.state==='off' ? TH('back')   : TH('panelFront'));\n"
    "  // Emphasis belongs to one thing at a time: the ring and the angles are\n"
    "  // the active state only. What is merely available is the normal case and\n"
    "  // gets nothing.\n"
    "  if(o.state==='on'){\n"
    "    thGlowPath(x, y, w, h, 6, 1);\n"
    "    thBrackets(x, y, w, h, TH('accentWarm'));\n"
    "  }\n"
    "}",
    "uiCell",
)

src = replace_once(
    src,
    "// A panel over the playfield: the dim sheet behind it, then the panel body.\n"
    "function uiDialog(x, y, w, h){\n"
    "  ctx.fillStyle = 'rgba(0,0,0,0.78)';\n"
    "  ctx.fillRect(0, 0, W, H);\n"
    "  thPanel(x, y, w, h, TH('panelFront'), TH('back'));\n"
    "  thBevel(x, y, w, h);\n"
    "  thGlow(x, y, w, h, 0.85);\n"
    "}",
    "// A panel over the playfield. One frame for all of them now, so the call\n"
    "// menu, the settings panel and the pause panel are the same object as the\n"
    "// hangar. Their contents have not moved; only what they are drawn on has.\n"
    "function uiDialog(x, y, w, h){\n"
    "  thFrame(x, y, w, h, 0);\n"
    "}",
    "uiDialog",
)

src = replace_once(
    src,
    "function thButton(x, y, w, h, state){\n"
    "  thPanel(x, y, w, h, TH('raised'), TH('panelBack'));\n"
    "  thBevel(x, y, w, h);\n"
    "  if(state==='on') thGlow(x, y, w, h, 1);\n"
    "  else if(state==='ready') thGlow(x, y, w, h, 0.5);\n"
    "}",
    "function thButton(x, y, w, h, state){\n"
    "  thPlate(x, y, w, h, TH('raised'), 4);\n"
    "  if(state==='on')           thGlowPath(x, y, w, h, 4, 1);\n"
    "  else if(state==='ready')   thGlowPath(x, y, w, h, 4, 0.5);\n"
    "}",
    "thButton",
)

# ── 4. A panel swallows its own clicks ───────────────────────────────
src = replace_once(
    src,
    "  if(shipMenu){\n"
    "    for(const r of (window._shipRects||[]))\n"
    "      if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){ if(r.key) swapShip(r.key); return true; }\n"
    "    setShipMenu(false); return true;\n"
    "  }",
    "  if(shipMenu){\n"
    "    for(const r of (window._shipRects||[]))\n"
    "      if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){ if(r.key) swapShip(r.key); return true; }\n"
    "    // Inside the panel but on no row: the header, a group heading, a gap\n"
    "    // between rows or the footer. That is still the panel, so it swallows\n"
    "    // the click. Only outside the outline does the panel close.\n"
    "    if(insidePanel(window._shipPanelRect, p)) return true;\n"
    "    setShipMenu(false); return true;\n"
    "  }",
    "ship panel clicks",
)

src = replace_once(
    src,
    "    setCallMenu(false); return true;\n"
    "  }",
    "    if(insidePanel(window._callPanelRect, p)) return true;\n"
    "    setCallMenu(false); return true;\n"
    "  }",
    "call panel clicks",
)

src = replace_once(
    src,
    "function pointerConsumed(p){",
    "// A panel outline, as reported by whatever drew it last. Anything landing\n"
    "// on it belongs to that panel, whether or not it hit something usable.\n"
    "function insidePanel(r, p){\n"
    "  return !!r && p.x>=r.x && p.x<=r.x+r.w && p.y>=r.y && p.y<=r.y+r.h;\n"
    "}\n"
    "function pointerConsumed(p){",
    "insidePanel",
)

src = replace_once(
    src,
    "  ctx.save();\n"
    "  thFrame(mx, my, L.mw, L.mh, HG_TITLE);",
    "  ctx.save();\n"
    "  thFrame(mx, my, L.mw, L.mh, HG_TITLE);\n"
    "  window._shipPanelRect = {x:mx, y:my, w:L.mw, h:L.mh};",
    "ship panel rect",
)

# ── 5. The digits follow the order that is shown ─────────────────────
src = replace_once(
    src,
    "function hangarLayout(){",
    "// The order the rows appear in, as roster indices. The groups reorder the\n"
    "// list, and the keyboard has to agree with what is on screen, so both read\n"
    "// this and nothing counts rows on its own.\n"
    "function hangarOrder(){\n"
    "  const out = [];\n"
    "  for(const g of hangarGroups()) for(const i of g.idx) out.push(i);\n"
    "  return out;\n"
    "}\n"
    "function hangarLayout(){",
    "hangarOrder",
)

src = replace_once(
    src,
    "// The digit that takes this hull from the keyboard, in a chip of its own. It\n"
    "// is the shortcut, not decoration, which is why it stays with the hull rather\n"
    "// than counting the rows: the groups reorder the list, the keys do not.",
    "// The digit that takes this hull from the keyboard, in a chip of its own. It\n"
    "// is the shortcut, not decoration, and it counts down the panel as shown:\n"
    "// fighters 1 to 5, bombers 6 to 8. The key handler reads the same order.",
    "chip comment",
)

src = replace_once(
    src,
    "    drawKeyChip(p.i+1, rx+HG_NUM, ry+(p.h-16)/2, HG_NUM_W, 16, open || p.cur);",
    "    drawKeyChip(ORDER.indexOf(p.i)+1, rx+HG_NUM, ry+(p.h-16)/2,\n"
    "                HG_NUM_W, 16, open || p.cur);",
    "chip digit",
)

src = replace_once(
    src,
    "  const TICKS = HG_COLS.map(function(c){ return c.x; });",
    "  const TICKS = HG_COLS.map(function(c){ return c.x; });\n"
    "  const ORDER = hangarOrder();",
    "order in draw",
)

src = replace_once(
    src,
    "    var si = parseInt(sd,10);\n"
    "    if(si>=1 && si<=PLAYER_SHIPS.length){ swapShip(PLAYER_SHIPS[si-1].key); ev.preventDefault(); }",
    "    var si = parseInt(sd,10);\n"
    "    // The same order the panel shows, so the digit beside a hull is the\n"
    "    // digit that takes it.\n"
    "    var ord = hangarOrder();\n"
    "    if(si>=1 && si<=ord.length){ swapShip(PLAYER_SHIPS[ord[si-1]].key); ev.preventDefault(); }",
    "digit key",
)

src = replace_once(
    src,
    "  uiDialog(mx, my, mw, mh, '#020c06', '#00ee55');",
    "  uiDialog(mx, my, mw, mh, '#020c06', '#00ee55');\n"
    "  window._callPanelRect = {x:mx, y:my, w:mw, h:mh};",
    "call panel rect",
)

# ── 6. The game over screen ──────────────────────────────────────────
NEW_GO = r"""function drawGO(){
  // A panel like every other panel, and the figures read as a list: label on
  // the left, value on the right, a hairline between. The run is over, so
  // there is nothing to do here but read it and decide to go again.
  const PW = 380, PH = 252;
  const px = ((W-PW)/2)|0, py = ((H-PH)/2)|0;
  thFrame(px, py, PW, PH, 54);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.save();
  ctx.shadowColor = 'rgba('+TH('glow')+',0.60)'; ctx.shadowBlur = 20;
  ctx.fillStyle = TH('textBright'); ctx.font = thLabel(30);
  ctx.fillText('GAME OVER', px+PW/2, py+28);
  ctx.restore();

  const rows = [['SCORE', String(score).padStart(7,'0')],
                ['WAVE',  String(wave).padStart(3,'0')],
                ['TIME',  fmtTime(runTime)]];
  for(let i=0;i<rows.length;i++){
    const ry = py+82+i*38;
    ctx.textAlign='left';
    ctx.fillStyle = TH('textDim'); ctx.font = thLabel(9);
    ctx.fillText(rows[i][0], px+30, ry);
    ctx.textAlign='right';
    ctx.fillStyle = TH('textBright'); ctx.font = thValue(21, false);
    ctx.fillText(rows[i][1], px+PW-30, ry);
    if(i < rows.length-1){
      ctx.strokeStyle = TH('edgeDark'); ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(px+30, ry+19.5); ctx.lineTo(px+PW-30, ry+19.5);
      ctx.stroke();
    }
  }

  // The one thing that can be done, as a button rather than a blinking line
  // of text. The ring is what pulses; the button itself stays put.
  const bw = 250, bh = 32;
  const bx = px+((PW-bw)/2|0), by = py+PH-50;
  thButton(bx, by, bw, bh, (fc%60<42) ? 'on' : 'ready');
  ctx.textAlign='center';
  ctx.fillStyle = TH('textBright'); ctx.font = thLabel(11);
  ctx.fillText('SPACE / ENTER  -  TRY AGAIN', bx+bw/2, by+bh/2+1);

  ctx.textAlign='left'; ctx.textBaseline='top';
}
"""

src = cut_between(src, "function drawGO(){", "\n\n// ── TOUCH & MAUS STEUERUNG", NEW_GO, "drawGO")

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
