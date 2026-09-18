#!/usr/bin/env python3
"""FS3 v113 - one set of shapes for every panel, applied to the hangar first.

The colours were right, the construction was not: a forum bevel around every
rectangle, a gradient on every surface, and a glow ring on everything that
was merely available. Eight framed boxes in a stack.

What replaces it is a small, fixed vocabulary that every panel in the game
will use, so the screens look machined by the same hand instead of each being
decorated on its own:

  thChamferPath  the signature - top left and bottom right corner cut off at
                 45 degrees. Angular, not rounded: that is the register a
                 FreeSpace interface is in.
  thPlate        a flat surface, no gradient, no bevel. Its edge is a dark
                 outline plus one bright hairline along the top: the light
                 rail.
  thGlowPath     the theme's glow ring, following a chamfered outline instead
                 of a rectangle.
  thBrackets     two short angles on the corners the chamfer leaves square,
                 the way a reticle marks what it has hold of. Reserved for
                 the active row.
  thScale        a hairline with a tick dropped at every column, like the
                 scale on an instrument. It ties figures to their headings.
  thFrame        the panel itself: sheet, plate, ring, and a rule under the
                 header that stops short of the right edge.

The old thBevel and thPanel stay for now: the bar, the call menu and the
settings panel still use them, and they change over as each of those screens
is rebuilt.

The hangar also gets its air: wider panel, taller rows, real space between
the two groups, and the digit that switches a hull on the keyboard is shown
beside the hull it belongs to.

Reads hlp_shooter_v112_logic.html, writes hlp_shooter_v113_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v112_logic.html", "hlp_shooter_v113_logic.html"


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

# ── 1. The surface kit, next to the helpers it will replace ──────────
KIT = r"""
// ── SURFACE KIT ───────────────────────────────────────────────
// One vocabulary of shapes for every panel in the game. A screen picks from
// this and adds nothing of its own, which is the only thing that keeps six
// screens looking like one interface.
//
// The chamfer is the signature: the top left and bottom right corner cut off
// at 45 degrees. Angular rather than rounded, because that is the register a
// FreeSpace interface is in, and it reads as a machined edge rather than a
// web card. Six points at row scale, twelve at panel scale.
function thChamferPath(x, y, w, h, c){
  if(c === undefined) c = 6;
  c = Math.min(c, w/2, h/2);
  ctx.beginPath();
  ctx.moveTo(x+c,   y);
  ctx.lineTo(x+w,   y);
  ctx.lineTo(x+w,   y+h-c);
  ctx.lineTo(x+w-c, y+h);
  ctx.lineTo(x,     y+h);
  ctx.lineTo(x,     y+c);
  ctx.closePath();
}
// A flat plate. No gradient and no bevel: what marks the edge is a dark
// outline all round plus one bright hairline along the top, and the cut
// corners do the rest.
function thPlate(x, y, w, h, fill, c){
  if(c === undefined) c = 6;
  thChamferPath(x, y, w, h, c);
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.lineWidth = 1;
  ctx.strokeStyle = TH('edgeDark');
  thChamferPath(x+0.5, y+0.5, w-1, h-1, c);
  ctx.stroke();
  ctx.strokeStyle = TH('edgeLight');
  ctx.beginPath();
  ctx.moveTo(x+c+0.5, y+0.5); ctx.lineTo(x+w-0.5, y+0.5);
  ctx.stroke();
}
// The theme's ring, following a chamfered outline instead of a rectangle.
// Emphasis in this interface is light, never a louder border.
function thGlowPath(x, y, w, h, c, k){
  const g = TH('glow'), s = (k === undefined) ? 1 : k;
  ctx.save();
  ctx.lineWidth = 1;
  ctx.shadowColor = 'rgba('+g+','+(0.40*s)+')'; ctx.shadowBlur = 6;
  ctx.strokeStyle = 'rgba('+g+','+(0.65*s)+')';
  thChamferPath(x+0.5, y+0.5, w-1, h-1, c); ctx.stroke();
  ctx.shadowColor = 'rgba('+g+','+(0.20*s)+')'; ctx.shadowBlur = 14;
  thChamferPath(x+0.5, y+0.5, w-1, h-1, c); ctx.stroke();
  ctx.restore();
}
// Two short angles, on exactly the two corners the chamfer leaves square, so
// the ornament and the cut belong to the same figure instead of fighting for
// the same corner. This marks the one thing that is active, nothing else.
function thBrackets(x, y, w, h, col, len){
  const L = len || 8;
  ctx.save();
  ctx.strokeStyle = col; ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(x+w-L, y+0.5);   ctx.lineTo(x+w-0.5, y+0.5);   ctx.lineTo(x+w-0.5, y+L);
  ctx.moveTo(x+0.5, y+h-L);   ctx.lineTo(x+0.5, y+h-0.5);   ctx.lineTo(x+L, y+h-0.5);
  ctx.stroke();
  ctx.restore();
}
// A hairline with a short tick dropped at each given offset, like the scale
// on an instrument. Wherever figures stand in columns, this is what ties them
// to their headings without drawing a table grid.
function thScale(x, y, w, ticks, col){
  ctx.save();
  ctx.strokeStyle = col; ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x, y+0.5); ctx.lineTo(x+w, y+0.5);
  for(let i=0;i<ticks.length;i++){
    ctx.moveTo(x+ticks[i]+0.5, y+0.5); ctx.lineTo(x+ticks[i]+0.5, y+4.5);
  }
  ctx.stroke();
  ctx.restore();
}
// A panel over the playfield, built from the kit: the sheet that dims the
// battle, the plate, the ring, and a rule under the header. The rule is two
// weights and stops short of the right edge - the one asymmetry in the whole
// vocabulary, so every panel has a reading direction.
function thFrame(x, y, w, h, headH){
  ctx.fillStyle = 'rgba(0,0,0,0.80)';
  ctx.fillRect(0, 0, W, H);
  thPlate(x, y, w, h, TH('panelBack'), 12);
  thGlowPath(x, y, w, h, 12, 0.9);
  if(headH){
    const run = Math.round(w*0.34);
    ctx.lineWidth = 2; ctx.strokeStyle = TH('accentWarm');
    ctx.beginPath();
    ctx.moveTo(x+12, y+headH-1); ctx.lineTo(x+12+run, y+headH-1);
    ctx.stroke();
    ctx.lineWidth = 1; ctx.strokeStyle = TH('edgeLight');
    ctx.beginPath();
    ctx.moveTo(x+12+run+10, y+headH-0.5); ctx.lineTo(x+w-12, y+headH-0.5);
    ctx.stroke();
  }
}
"""

src = replace_once(
    src,
    "// Eine Stelle, an der die Weichzeichnung abgeschaltet wird. Sechs",
    KIT.lstrip("\n") + "\n// Eine Stelle, an der die Weichzeichnung abgeschaltet wird. Sechs",
    "surface kit",
)

# ── 2. The hangar, drawn from the kit ────────────────────────────────
NEW_HANGAR = r"""// ── HANGAR LAYOUT ────────────────────────────────────────────
// The hangar is a comparison table, not a wall of tiles. One row per hull
// over the full width, fighters and bombers in groups of their own, and every
// figure in a fixed column so hull sits under hull and two hulls can be read
// against each other at a glance. A locked hull collapses to a thin line:
// something you cannot take should not weigh as much as something you can.
//
// Everything visible here comes out of the SURFACE KIT. No shape is invented
// for this panel.
const HG_W        = 660;    // panel width, of 800 logical points
const HG_PAD      = 12;     // inner margin, also the left edge of every row
const HG_ROW      = 38;     // a hull that can be taken
const HG_ROW_LOCK = 20;     // a hull that cannot
const HG_GAP      = 4;
const HG_HEAD     = 24;     // group heading, its scale and the column titles
const HG_TITLE    = 34;     // header line of the panel
const HG_FOOT     = 18;
const HG_GROUPGAP = 14;     // the air that separates fighters from bombers
const HG_NUM      = 8;      // the keyboard digit, measured from the row's left
const HG_NUM_W    = 16;
const HG_PIC      = 30;     // picture cell
const HG_PIC_W    = 52;
const HG_NAME     = 92;
const HG_PIC_ALPHA     = 0.95;   // it is a portrait now, not a watermark
const HG_PIC_ALPHA_OFF = 0.35;
// Column starts, measured from the row's left edge. The row is
// HG_W - 2*HG_PAD wide, so the last column has to end inside 636.
const HG_COLS = [
  {k:'hull',   x:232, label:'HULL'},
  {k:'shield', x:292, label:'SHIELD'},
  {k:'spd',    x:356, label:'SPD'},
  {k:'agi',    x:420, label:'AGI'},
  {k:'guns',   x:484, label:'GUNS'},
  {k:'volley', x:530, label:'VOLLEY'},
  {k:'sec',    x:586, label:'SEC'}
];
// Which hull belongs in which group. Read from the hull key, the same way the
// rest of the file decides what a bomber is, so a new hull lands in the right
// group without a second list to keep in step.
function hangarGroups(){
  const fi=[], bo=[];
  for(let i=0;i<PLAYER_SHIPS.length;i++)
    (isBomberHull(PLAYER_SHIPS[i].key) ? bo : fi).push(i);
  return [{head:'FIGHTERS', idx:fi}, {head:'BOMBERS', idx:bo}];
}
// Where everything sits, worked out before anything is drawn: the panel grows
// and shrinks with the number of hulls that are open, and both the drawing and
// the tap rectangles read the same plan rather than repeating the arithmetic.
function hangarLayout(){
  const groups = hangarGroups();
  const plan = [];
  let h = HG_TITLE;
  for(const g of groups){
    if(!g.idx.length) continue;
    plan.push({head:g.head, y:h});
    h += HG_HEAD;
    for(const i of g.idx){
      const s = PLAYER_SHIPS[i];
      const cur    = s.key===player.ship;
      const locked = i>=shipUnlocked;
      // Unlocked, but no hangar of its faction on the field: it keeps a full
      // row, because it is yours and its figures still have to be readable.
      const off    = !locked && !cur && !shipOffered(s.key);
      const rh     = locked ? HG_ROW_LOCK : HG_ROW;
      plan.push({i:i, y:h, h:rh, cur:cur, locked:locked, off:off});
      h += rh + HG_GAP;
    }
    h += HG_GROUPGAP;
  }
  h += HG_FOOT;
  return {mx:((W-HG_W)/2)|0, my:((H-h)/2)|0, mw:HG_W, mh:h, plan:plan};
}
// The sprite in its own cell, fitted whole and always facing right. Every hull
// is fitted to the same cell rather than to its real length, so the column
// stays a column. A sprite that has not loaded leaves the cell empty instead
// of throwing.
function drawHullCell(key, x, y, w, h, lit){
  const img = IMGS[key];
  if(!img || !img.width || !img.height) return;
  const p  = 3;
  const sc = Math.min((w-p*2)/img.width, (h-p*2)/img.height);
  if(!(sc > 0)) return;
  const dw = img.width*sc, dh = img.height*sc;
  ctx.save();
  ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  ctx.globalAlpha = lit ? HG_PIC_ALPHA : HG_PIC_ALPHA_OFF;
  ctx.translate(x+w/2, y+h/2);
  if(spriteFacing(key)==='left') ctx.scale(-1,1);
  ctx.drawImage(img, -dw/2, -dh/2, dw, dh);
  ctx.restore();
}
// The digit that takes this hull from the keyboard, in a chip of its own. It
// is the shortcut, not decoration, which is why it stays with the hull rather
// than counting the rows: the groups reorder the list, the keys do not.
function drawKeyChip(d, x, y, w, h, lit){
  thPlate(x, y, w, h, TH('back'), 3);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillStyle = lit ? TH('text') : TH('textDim');
  ctx.font = thValue(10, true);
  ctx.fillText(String(d), x+w/2, y+h/2+0.5);
  ctx.textAlign='left';
}
function drawShipMenu(){
  if(!shipMenu) return;
  const L  = hangarLayout();
  const mx = L.mx, my = L.my, rw = L.mw - HG_PAD*2;
  ctx.save();
  thFrame(mx, my, L.mw, L.mh, HG_TITLE);

  // Header: what this is on the left, on what terms on the right.
  ctx.textBaseline='middle';
  ctx.textAlign='left';
  ctx.fillStyle=TH('textBright'); ctx.font=thLabel(14);
  ctx.fillText('SWITCH SHIP', mx+HG_PAD, my+16);
  ctx.textAlign='right';
  ctx.fillStyle=colossusOnField() ? TH('accentWarm') : TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText(colossusOnField() ? 'COLOSSUS HANGAR OPEN  -  NO REFIT AFTER THE FIRST SWITCH'
                                 : 'ONE SWITCH PER WAVE', mx+L.mw-HG_PAD, my+16);

  const TICKS = HG_COLS.map(function(c){ return c.x; });
  window._shipRects=[];
  for(const p of L.plan){
    const ry = my+p.y;
    // A group heading carries the column titles and the scale under them, so
    // the reading is set up twice on the way down instead of once at the top.
    if(p.head !== undefined){
      ctx.textAlign='left'; ctx.textBaseline='middle';
      ctx.fillStyle=TH('text'); ctx.font=thLabel(11);
      ctx.fillText(p.head, mx+HG_PAD, ry+8);
      ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
      for(const c of HG_COLS) ctx.fillText(c.label, mx+HG_PAD+c.x, ry+9);
      thScale(mx+HG_PAD, ry+15, rw, TICKS, TH('edgeLight'));
      continue;
    }
    const s    = PLAYER_SHIPS[p.i];
    const rx   = mx+HG_PAD;
    const open = !p.locked && !p.off;

    if(p.locked){
      // A thin line with no plate under it: the name, and what it costs.
      ctx.textAlign='left'; ctx.textBaseline='middle';
      ctx.fillStyle=TH('textDim'); ctx.font=thValue(11, false);
      ctx.fillText(s.name, rx+HG_NAME, ry+p.h/2);
      ctx.fillText('unlocks at '+s.unlock.toLocaleString('en-US')+' points',
                   rx+HG_COLS[0].x, ry+p.h/2);
      window._shipRects.push({x:rx, y:ry, w:rw, h:p.h, ship:s.key, key:null});
      continue;
    }

    thPlate(rx, ry, rw, p.h,
            p.cur ? TH('raised') : (open ? TH('panelFront') : TH('back')));
    if(p.cur){
      // Three marks for the one row that is active, and they are the kit's,
      // not this panel's: the ring, the two angles, the bar on the edge.
      thGlowPath(rx, ry, rw, p.h, 6, 1);
      thBrackets(rx, ry, rw, p.h, TH('accentWarm'));
      ctx.fillStyle=TH('accentWarm');
      ctx.fillRect(rx, ry+6, 3, p.h-12);
    }
    drawKeyChip(p.i+1, rx+HG_NUM, ry+(p.h-16)/2, HG_NUM_W, 16, open || p.cur);
    drawHullCell(s.key, rx+HG_PIC, ry+3, HG_PIC_W, p.h-6, open || p.cur);

    ctx.textAlign='left'; ctx.textBaseline='middle';
    ctx.fillStyle = p.cur ? TH('accentWarm') : (open ? TH('textBright') : TH('textDim'));
    ctx.font=thValue(15, true);
    if(p.off){
      // Two lines only where there is a reason to give: the name, and why the
      // row cannot be taken right now.
      ctx.fillText(s.name, rx+HG_NAME, ry+13);
      ctx.fillStyle=TH('textDim'); ctx.font=thValue(9, false);
      ctx.fillText('NO '+(s.fac||'').toUpperCase()+' HANGAR ON THE FIELD', rx+HG_NAME, ry+27);
    } else {
      ctx.fillText(s.name, rx+HG_NAME, ry+p.h/2);
    }

    // The figures. Same column, same font, same baseline on every row.
    const vCol = open ? TH('textBright') : TH('textDim');
    const pCol = open ? TH('accentWarm')  : TH('textDim');
    const cy   = ry+p.h/2;
    ctx.font=thValue(15, false);
    ctx.fillStyle=vCol;
    ctx.fillText(String(s.hp), rx+HG_COLS[0].x, cy);
    ctx.fillText(String(s.sh), rx+HG_COLS[1].x, cy);
    statPips(rx+HG_COLS[2].x, cy-3, s.spd,  [2.2,2.5,2.9,3.2,3.5],      pCol);
    statPips(rx+HG_COLS[3].x, cy-3, s.turn, [0.08,0.10,0.12,0.14,0.17], pCol);
    // Barrels and volley are read from the mount data. No mount data means no
    // claim about either, rather than a made up one.
    const gn = primaryCount(s.key);
    if(gn){
      ctx.fillStyle=vCol;
      ctx.fillText(String(gn), rx+HG_COLS[4].x, cy);
      ctx.fillText(String(Math.round(volleyTotal(gn))), rx+HG_COLS[5].x, cy);
    }
    const secX = rx+HG_COLS[6].x;
    if(isBomberHull(s.key)) drawBombIcon(secX+10, cy, pCol);
    else                    drawMissileIcon(secX+10, cy, pCol);
    ctx.fillStyle=vCol; ctx.font=thValue(15, false);
    ctx.fillText(String(s.sec), secX+24, cy);

    // Every row swallows its own tap, so a row that cannot be taken cannot
    // close the panel by accident either.
    window._shipRects.push({x:rx, y:ry, w:rw, h:p.h, ship:s.key,
                            key:(open && !p.cur) ? s.key : null});
  }

  ctx.textAlign='center'; ctx.fillStyle=TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText('ESC or tap outside to cancel', mx+L.mw/2, my+L.mh-11);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}

"""

src = cut_between(
    src,
    "// ── HANGAR LAYOUT ────────────────────────────────────────────",
    "function drawCallMenu(){",
    NEW_HANGAR,
    "hangar",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
