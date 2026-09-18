#!/usr/bin/env python3
"""FS3 v112 - the CLASSIC look goes, the hangar is rebuilt.

1. CLASSIC is removed. It was kept as a side by side reference; it is not
   wanted as one. Gone: the ECO.hud setting and the value stored for it, the
   INTERFACE row on settings page 3, drawHUDClassic() in full, and the
   CLASSIC branch inside UI/uiHLP/uiLabel/uiValue/uiCell/uiDialog. Those six
   helpers stay as plain pass-throughs: every screen still calls them with a
   trailing CLASSIC argument that is now ignored, and those arguments go away
   screen by screen as each screen is rebuilt.

2. The hangar is rebuilt from the ground up. Eight equally heavy 236x50
   tiles in two columns become one row per hull over the full width, split
   into FIGHTERS and BOMBERS, with the figures in fixed columns so hull sits
   under hull and hulls can actually be compared. The sprite gets a picture
   cell of its own on the left instead of lying behind the text. A locked
   hull collapses to a thin line. The active hull carries an accent bar on
   its left edge instead of a white frame.

Reads hlp_shooter_v111_logic.html, writes hlp_shooter_v112_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v111_logic.html", "hlp_shooter_v112_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def cut_between(text, start, end, new, label):
    """Replace everything from start up to (not including) end."""
    if text.count(start) != 1:
        sys.exit("Abbruch (%s): Startmarke %d-mal gefunden, erwartet einmal."
                 % (label, text.count(start)))
    if text.count(end) != 1:
        sys.exit("Abbruch (%s): Endmarke %d-mal gefunden, erwartet einmal."
                 % (label, text.count(end)))
    i = text.index(start)
    j = text.index(end)
    if j <= i:
        sys.exit("Abbruch (%s): Endmarke steht vor der Startmarke." % label)
    return text[:i] + new + text[j:]


src = open(SRC, encoding="utf-8").read()

# ── 1. The stored setting ────────────────────────────────────────────
src = replace_once(
    src,
    "let ECO = {res:1.5, blur:true, rim:true, glint:true, hud:'hlp', scheme:'fire'};",
    "let ECO = {res:1.5, blur:true, rim:true, glint:true, scheme:'fire'};",
    "ECO defaults",
)

src = replace_once(
    src,
    "      if(_eo.hud==='classic' || _eo.hud==='hlp') ECO.hud = _eo.hud;\n",
    "",
    "ECO load",
)

# ── 2. The six helpers lose their CLASSIC branch ─────────────────────
src = replace_once(
    src,
    "// One place that resolves a colour: the theme's role in HLP mode, the\n"
    "// previous literal in CLASSIC mode. This is what lets both looks share a\n"
    "// single drawing routine instead of being two copies that drift apart.\n"
    "function UI(role, classic){ return (ECO.hud==='classic') ? classic : TH(role); }\n"
    "function uiHLP(){ return ECO.hud!=='classic'; }\n"
    "function uiLabel(px, classic){ return uiHLP() ? thLabel(px) : classic; }\n"
    "function uiValue(px, bold, classic){ return uiHLP() ? thValue(px, bold) : classic; }\n",
    "// There is one look now. These four are what is left of the switch that\n"
    "// used to choose between two: callers still pass a trailing CLASSIC\n"
    "// argument, which is ignored here and disappears from each screen as that\n"
    "// screen is rebuilt.\n"
    "function UI(role){ return TH(role); }\n"
    "function uiHLP(){ return true; }\n"
    "function uiLabel(px){ return thLabel(px); }\n"
    "function uiValue(px, bold){ return thValue(px, bold); }\n",
    "UI helpers",
)

src = replace_once(
    src,
    "function uiCell(x, y, w, h, o){\n"
    "  o = o || {};\n"
    "  if(!uiHLP()){\n"
    "    ctx.fillStyle = o.fill; ctx.fillRect(x, y, w, h);\n"
    "    ctx.strokeStyle = o.stroke; ctx.lineWidth = o.lw || 1;\n"
    "    ctx.strokeRect(x, y, w, h);\n"
    "    return;\n"
    "  }\n"
    "  if(o.state==='off'){\n",
    "function uiCell(x, y, w, h, o){\n"
    "  o = o || {};\n"
    "  if(o.state==='off'){\n",
    "uiCell classic branch",
)

src = replace_once(
    src,
    "function uiDialog(x, y, w, h, classicFill, classicStroke){\n"
    "  ctx.fillStyle = uiHLP() ? 'rgba(0,0,0,0.78)' : 'rgba(0,0,0,0.72)';\n"
    "  ctx.fillRect(0, 0, W, H);\n"
    "  if(!uiHLP()){\n"
    "    ctx.fillStyle = classicFill; ctx.fillRect(x, y, w, h);\n"
    "    ctx.strokeStyle = classicStroke; ctx.lineWidth = 2; ctx.strokeRect(x, y, w, h);\n"
    "    return;\n"
    "  }\n"
    "  thPanel(x, y, w, h, TH('panelFront'), TH('back'));\n",
    "function uiDialog(x, y, w, h){\n"
    "  ctx.fillStyle = 'rgba(0,0,0,0.78)';\n"
    "  ctx.fillRect(0, 0, W, H);\n"
    "  thPanel(x, y, w, h, TH('panelFront'), TH('back'));\n",
    "uiDialog classic branch",
)

# ── 3. The settings row that offered the switch ──────────────────────
src = replace_once(
    src,
    "  if(settingsPage===2) return [\n"
    "    {label:'INTERFACE', hint:'HLP forum theme, or the previous look',\n"
    "     value:ECO.hud==='hlp'?'HLP':'CLASSIC', on:ECO.hud==='hlp',\n"
    "     act:'uistyle', enabled:true},\n"
    "    {label:'COLOUR SCHEME', hint:'the two schemes of the forum theme',\n"
    "     value:ECO.scheme==='void'?'VOID':'FIRE', on:true,\n"
    "     act:'scheme', enabled:ECO.hud==='hlp'}\n"
    "  ];\n",
    "  if(settingsPage===2) return [\n"
    "    {label:'COLOUR SCHEME', hint:'the two schemes of the forum theme',\n"
    "     value:ECO.scheme==='void'?'VOID':'FIRE', on:true,\n"
    "     act:'scheme', enabled:true}\n"
    "  ];\n",
    "settings row",
)

src = replace_once(
    src,
    "      else if(r.act==='uistyle'){ ECO.hud=(ECO.hud==='hlp')?'classic':'hlp'; ecoSave(); }\n",
    "",
    "settings action",
)

# ── 4. One bar left, so no branch in front of it ─────────────────────
src = replace_once(
    src,
    "// Which bar is drawn is a stored setting, so the old one and the new one can\n"
    "// be compared in a running game instead of in a mockup.\n"
    "function drawHUD(){\n"
    "  if(GS!=='playing') return;\n"
    "  if(ECO.hud==='classic') drawHUDClassic();\n"
    "  else                    drawHUDHLP();\n"
    "}\n",
    "function drawHUD(){\n"
    "  if(GS!=='playing') return;\n"
    "  drawHUDHLP();\n"
    "}\n",
    "drawHUD",
)

# The old bar in full. The marker below it is the next section banner.
src = cut_between(
    src,
    "\nfunction drawHUDClassic(){",
    "\n// ── CALL MENU ─────────────────────────────────────────────────",
    "\n",
    "drawHUDClassic",
)

# ── 5. The hangar, rebuilt ───────────────────────────────────────────
NEW_HANGAR = r"""// ── HANGAR LAYOUT ────────────────────────────────────────────
// The hangar is a comparison table, not a wall of tiles. One row per hull
// over the full width, fighters and bombers in groups of their own, and
// every figure in a fixed column so hull sits under hull and two hulls can
// be read against each other at a glance. A locked hull collapses to a thin
// line: something you cannot take should not weigh as much as something you
// can.
const HG_W        = 624;    // menu width, of 800 logical points
const HG_PAD      = 12;     // inner margin, also the left edge of every row
const HG_ROW      = 38;     // a hull that can be taken
const HG_ROW_LOCK = 18;     // a hull that cannot
const HG_GAP      = 4;
const HG_HEAD     = 20;     // group heading plus the column titles
const HG_TITLE    = 34;     // the header line of the panel
const HG_FOOT     = 20;
const HG_GROUPGAP = 8;
const HG_PIC      = 8;      // picture cell, measured from the row's left edge
const HG_PIC_W    = 52;
const HG_NAME     = 68;
const HG_PIC_ALPHA     = 0.95;   // it is a portrait now, not a watermark
const HG_PIC_ALPHA_OFF = 0.35;
// Column starts, measured from the row's left edge. The row is
// HG_W - 2*HG_PAD wide, so the last column has to end inside 600.
const HG_COLS = [
  {k:'hull',   x:210, label:'HULL'},
  {k:'shield', x:264, label:'SHIELD'},
  {k:'spd',    x:326, label:'SPD'},
  {k:'agi',    x:384, label:'AGI'},
  {k:'guns',   x:442, label:'GUNS'},
  {k:'volley', x:490, label:'VOLLEY'},
  {k:'sec',    x:548, label:'SEC'}
];
// Which hull belongs in which group. Read from the hull key, the same way
// the rest of the file decides what a bomber is, so a new hull lands in the
// right group without a second list to keep in step.
function hangarGroups(){
  const fi=[], bo=[];
  for(let i=0;i<PLAYER_SHIPS.length;i++)
    (isBomberHull(PLAYER_SHIPS[i].key) ? bo : fi).push(i);
  return [{head:'FIGHTERS', idx:fi}, {head:'BOMBERS', idx:bo}];
}
// Where everything sits, worked out before anything is drawn: the panel
// grows and shrinks with the number of hulls that are open, and both the
// drawing and the tap rectangles read the same plan rather than repeating
// the arithmetic.
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
// The sprite in its own cell, fitted whole and always facing right. Every
// hull is fitted to the same cell rather than to its real length, so the
// column stays a column. A sprite that has not loaded leaves the cell empty
// instead of throwing.
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
function drawShipMenu(){
  if(!shipMenu) return;
  const L  = hangarLayout();
  const mx = L.mx, my = L.my, rw = L.mw - HG_PAD*2;
  ctx.save();
  uiDialog(mx, my, L.mw, L.mh);

  // Header: what this is on the left, on what terms on the right.
  ctx.textBaseline='middle';
  ctx.textAlign='left';
  ctx.fillStyle=TH('textBright'); ctx.font=thLabel(14);
  ctx.fillText('SWITCH SHIP', mx+HG_PAD, my+18);
  ctx.textAlign='right';
  ctx.fillStyle=colossusOnField() ? TH('accentWarm') : TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText(colossusOnField() ? 'COLOSSUS HANGAR OPEN  -  NO REFIT AFTER THE FIRST SWITCH'
                                 : 'ONE SWITCH PER WAVE', mx+L.mw-HG_PAD, my+18);
  ctx.strokeStyle=TH('edgeDark'); ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(mx+HG_PAD, my+HG_TITLE-6.5);
  ctx.lineTo(mx+L.mw-HG_PAD, my+HG_TITLE-6.5); ctx.stroke();

  window._shipRects=[];
  for(const p of L.plan){
    const ry = my+p.y;
    // A group heading carries the column titles, so they are stated twice on
    // the way down the panel rather than once at the very top.
    if(p.head !== undefined){
      ctx.textAlign='left';
      ctx.fillStyle=TH('text'); ctx.font=thLabel(11);
      ctx.fillText(p.head, mx+HG_PAD, ry+11);
      ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
      for(const c of HG_COLS) ctx.fillText(c.label, mx+HG_PAD+c.x, ry+12);
      continue;
    }
    const s    = PLAYER_SHIPS[p.i];
    const rx   = mx+HG_PAD;
    const open = !p.locked && !p.off;

    if(p.locked){
      // A thin line with no surface under it: the name, and what it costs.
      ctx.textAlign='left';
      ctx.fillStyle=TH('textDim'); ctx.font=thValue(11, false);
      ctx.fillText(s.name, rx+HG_NAME, ry+p.h/2);
      ctx.fillText('unlocks at '+s.unlock.toLocaleString('en-US')+' points',
                   rx+HG_COLS[0].x, ry+p.h/2);
      window._shipRects.push({x:rx, y:ry, w:rw, h:p.h, ship:s.key, key:null});
      continue;
    }

    uiCell(rx, ry, rw, p.h, {state: p.cur ? 'on' : (open ? 'ready' : 'off')});
    // The active hull is marked by a bar on its own edge. A frame around the
    // whole row would compete with the ring the cell already carries.
    if(p.cur){ ctx.fillStyle=TH('accentWarm'); ctx.fillRect(rx, ry, 3, p.h); }
    drawHullCell(s.key, rx+HG_PIC, ry+3, HG_PIC_W, p.h-6, open || p.cur);

    ctx.textAlign='left';
    ctx.fillStyle = p.cur ? TH('accentWarm') : (open ? TH('textBright') : TH('textDim'));
    ctx.font=thValue(15, true);
    if(p.off){
      // Two lines only where there is a reason to give: the name, and why
      // the row cannot be taken right now.
      ctx.fillText(s.name, rx+HG_NAME, ry+13);
      ctx.fillStyle=TH('textDim'); ctx.font=thValue(9, false);
      ctx.fillText('NO '+(s.fac||'').toUpperCase()+' HANGAR ON THE FIELD', rx+HG_NAME, ry+27);
    } else {
      ctx.fillText(s.name, rx+HG_NAME, ry+p.h/2);
    }

    // The figures. Same column, same font, same baseline on every row.
    const vCol = open ? TH('textBright') : TH('textDim');
    const pCol = open ? TH('accentWarm')  : TH('textDim');
    const my2  = ry+p.h/2;
    ctx.font=thValue(15, false);
    ctx.fillStyle=vCol;
    ctx.fillText(String(s.hp), rx+HG_COLS[0].x, my2);
    ctx.fillText(String(s.sh), rx+HG_COLS[1].x, my2);
    statPips(rx+HG_COLS[2].x, my2-3, s.spd,  [2.2,2.5,2.9,3.2,3.5],      pCol);
    statPips(rx+HG_COLS[3].x, my2-3, s.turn, [0.08,0.10,0.12,0.14,0.17], pCol);
    // Barrels and volley are read from the mount data. No mount data means
    // no claim about either, rather than a made up one.
    const gn = primaryCount(s.key);
    if(gn){
      ctx.fillStyle=vCol;
      ctx.fillText(String(gn), rx+HG_COLS[4].x, my2);
      ctx.fillText(String(Math.round(volleyTotal(gn))), rx+HG_COLS[5].x, my2);
    }
    const secX = rx+HG_COLS[6].x;
    if(isBomberHull(s.key)) drawBombIcon(secX+10, my2, pCol);
    else                    drawMissileIcon(secX+10, my2, pCol);
    ctx.fillStyle=vCol; ctx.font=thValue(15, false);
    ctx.fillText(String(s.sec), secX+24, my2);

    // Every row swallows its own tap, so a row that cannot be taken cannot
    // close the panel by accident either.
    window._shipRects.push({x:rx, y:ry, w:rw, h:p.h, ship:s.key,
                            key:(open && !p.cur) ? s.key : null});
  }

  ctx.textAlign='center'; ctx.fillStyle=TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText('ESC or tap outside to cancel', mx+L.mw/2, my+L.mh-12);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}

"""

src = cut_between(
    src,
    "function drawShipMenu(){",
    "function drawCallMenu(){",
    NEW_HANGAR,
    "drawShipMenu",
)

# ── 6. Two switches for looking at the interface ─────────────────────
# A panel cannot be judged if getting to it takes twenty minutes of play.
src = replace_once(
    src,
    "const TEST_MATCH = /[?&]test=([1-4])/.exec(location.search);",
    "// Review switches for the interface work, and for nothing else.\n"
    "// ?ships=N opens N hulls from the start, ?ui=1 puts a destroyer and a\n"
    "// Colossus ticket in hand, so a panel can be looked at without playing up\n"
    "// to it first. Neither touches a rule the panel is being judged on.\n"
    "const UI_SHIPS_MATCH = /[?&]ships=([1-8])/.exec(location.search);\n"
    "const UI_SHIPS   = UI_SHIPS_MATCH ? parseInt(UI_SHIPS_MATCH[1],10) : 1;\n"
    "const UI_TICKETS = /[?&]ui=1/.test(location.search);\n"
    "\n"
    "const TEST_MATCH = /[?&]test=([1-4])/.exec(location.search);",
    "review switches",
)

src = replace_once(
    src,
    "  shipUnlocked=1; shipSwapWave=-1; shipMenu=false;",
    "  shipUnlocked=UI_SHIPS; shipSwapWave=-1; shipMenu=false;",
    "unlock switch",
)

src = replace_once(
    src,
    "  tickets={cruiser:TICKET_START.cruiser, corvette:TICKET_START.corvette,\n"
    "           destroyer:TICKET_START.destroyer, colossus:TICKET_START.colossus};\n",
    "  tickets={cruiser:TICKET_START.cruiser, corvette:TICKET_START.corvette,\n"
    "           destroyer:TICKET_START.destroyer, colossus:TICKET_START.colossus};\n"
    "  if(UI_TICKETS){ tickets.destroyer+=1; tickets.colossus+=1; }\n",
    "ticket switch",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
