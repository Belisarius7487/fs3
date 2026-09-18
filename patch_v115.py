#!/usr/bin/env python3
"""FS3 v115 - the support menu is rebuilt in the hangar's language.

The overflow had a cause worth naming: the panel was as wide as its columns,
and the Colossus row was as wide as the panel. With only one faction on call
the panel is 202 points wide, while her line of text needs about 240. So the
text left the button. Nothing was checking, because nothing could.

Two things change:

1. thFit joins the kit. Everything in this interface sits in a fixed grid,
   and the one thing a string may not do is grow past the cell it was given.
   thFit measures and cuts. From here on no label can leave its column, in
   any panel, in any language.

2. The support menu is built the way the hangar is: a fixed panel width, one
   plate per ship with a key chip and a picture cell of its own, name and
   particulars on two lines, the tickets in hand on the right, and the refine
   button on its own ground. Terran and Vasudan keep their columns, each under
   its own heading and scale. The Colossus keeps her full width row, now under
   a heading of her own, and the panel no longer shrinks under her.

Nothing about what the menu does changes: the same entries, the same keys,
the same tickets, the same refining.

Reads hlp_shooter_v114_logic.html, writes hlp_shooter_v115_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v114_logic.html", "hlp_shooter_v115_logic.html"


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

# ── 1. thFit joins the kit ───────────────────────────────────────────
src = replace_once(
    src,
    "// A panel over the playfield, built from the kit: the sheet that dims the",
    "// Text that cannot leave its cell. Everything here sits in a fixed grid, so\n"
    "// the one thing a string may not do is grow past the width it was given. Set\n"
    "// the font first, then ask: what comes back fits, cut and closed with an\n"
    "// ellipsis if it had to be. This is why a long label can no longer push its\n"
    "// way out of a button.\n"
    "function thFit(txt, maxW){\n"
    "  txt = String(txt);\n"
    "  if(!(maxW > 0)) return '';\n"
    "  if(ctx.measureText(txt).width <= maxW) return txt;\n"
    "  let s = txt;\n"
    "  while(s.length > 1 && ctx.measureText(s+'\\u2026').width > maxW) s = s.slice(0, -1);\n"
    "  return s + '\\u2026';\n"
    "}\n"
    "// A panel over the playfield, built from the kit: the sheet that dims the",
    "thFit",
)

# ── 2. The support menu ──────────────────────────────────────────────
NEW_CALL = r"""// ── SUPPORT MENU LAYOUT ──────────────────────────────────────
// Built like the hangar: a fixed panel width, one plate per ship, the figures
// in their places. The width is fixed on purpose. It used to follow the number
// of faction columns, which meant that with a single faction on call the panel
// became narrower than the Colossus line of text that had to sit inside it.
const CM_W        = 636;
const CM_PAD      = 12;
const CM_ROW      = 38;
const CM_GAP      = 4;
const CM_HEAD     = 22;
const CM_TITLE    = 34;
const CM_FOOT     = 18;
const CM_GROUPGAP = 12;
const CM_NUM      = 6;    // key chip, measured from the row's left edge
const CM_NUM_W    = 16;
const CM_PIC      = 28;   // picture cell
const CM_PIC_W    = 44;
const CM_NAME     = 78;
const CM_REFINE_W = 46;   // refining keeps its own ground on the right
const CM_TICKET_W = 34;   // and the count in hand sits beside it
// Where everything sits, before anything is drawn. Both the drawing and the
// tap rectangles read this rather than working it out twice.
function callMenuLayout(){
  const COLS = callCols();
  const n    = Math.max(1, COLS.length);
  const colw = ((CM_W - CM_PAD*(n+1))/n)|0;
  let rows = 1;
  for(const c of COLS) rows = Math.max(rows, c.length);
  const showCol = allyFacOn(ALLY_DEFS[ALLY_SPECIAL].fac);
  let y = CM_TITLE;
  const headY = y; y += CM_HEAD;
  const rowY  = y; y += rows*(CM_ROW+CM_GAP);
  let colHeadY = 0, colRowY = 0;
  if(showCol){
    y += CM_GROUPGAP;
    colHeadY = y; y += CM_HEAD;
    colRowY  = y; y += CM_ROW + CM_GAP;
  }
  y += CM_FOOT;
  return {mx:((W-CM_W)/2)|0, my:((H-y)/2)|0, mw:CM_W, mh:y,
          COLS:COLS, colw:colw, showCol:showCol,
          headY:headY, rowY:rowY, colHeadY:colHeadY, colRowY:colRowY};
}
const CM_FAC_HEAD = {terran:'TERRAN FLEET', vasudan:'VASUDAN FLEET', gtva:'JOINT COMMAND'};
// One ship, on its own plate. Same parts and the same order as a hangar row,
// because they are the same kind of object: something you can take, with
// figures that let you decide whether to.
function drawAllyRow(x, y, w, id, d, keyLabel, hot){
  const ok  = allyAffordable(id);
  const rk  = allyTicket(id);
  const ref = canRefine(rk);
  thPlate(x, y, w, CM_ROW,
          (hot && ok) ? TH('raised') : (ok ? TH('panelFront') : TH('back')));
  // The Colossus is the rarest thing in the menu, so she is the one row that
  // carries the active marks.
  if(hot && ok){
    thGlowPath(x, y, w, CM_ROW, 6, 1);
    thBrackets(x, y, w, CM_ROW, TH('accentWarm'));
  }
  drawKeyChip(keyLabel, x+CM_NUM, y+(CM_ROW-16)/2, CM_NUM_W, 16, ok);
  drawHullCell(d.spr, x+CM_PIC, y+3, CM_PIC_W, CM_ROW-6, ok);

  // What is left for the name once the count and the refine button have had
  // their share. thFit gets told this number, so nothing can run past it.
  const rightKeep = CM_TICKET_W + (ref ? CM_REFINE_W + 4 : 0) + 8;
  const textW = w - CM_NAME - rightKeep;

  ctx.textAlign='left'; ctx.textBaseline='middle';
  ctx.fillStyle = ok ? TH('textBright') : TH('textDim');
  ctx.font = thValue(13, true);
  ctx.fillText(thFit(d.label, textW), x+CM_NAME, y+13);

  let sub;
  if(d.colossus)                sub = COLOSSUS_TIME+' s on station, then she jumps out';
  else if(d.cls==='destroyer')  sub = 'DESTROYER  -  HULL '+capHull(HULL[d.cls])+'  -  WINGS';
  else                          sub = d.cls.toUpperCase()+'  -  HULL '+capHull(HULL[d.cls]);
  ctx.fillStyle = TH('textDim'); ctx.font = thValue(9, false);
  ctx.fillText(thFit(sub, textW), x+CM_NAME, y+27);

  // How many are in hand, not merely whether one can be afforded.
  ctx.textAlign='right';
  ctx.fillStyle = ok ? TH('accent') : TH('textDim');
  ctx.font = thValue(14, true);
  ctx.fillText((tickets[rk]||0)+'x', x+w-(ref ? CM_REFINE_W+8 : 10), y+CM_ROW/2);
  ctx.textAlign='left';

  // Refining sits on its own generous button. A narrow one against a call
  // button is how a destroyer gets spent by accident.
  if(ref){
    const rx = x+w-CM_REFINE_W-2, ry = y+2, rh = CM_ROW-4;
    thPlate(rx, ry, CM_REFINE_W, rh, TH('panelBack'), 4);
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillStyle = TH('accentWarm'); ctx.font = thValue(13, true);
    ctx.fillText(REFINE_COST+'\u2192', rx+CM_REFINE_W/2, ry+rh/2-5);
    ctx.fillStyle = TH('textDim'); ctx.font = thLabel(7);
    ctx.fillText('REFINE', rx+CM_REFINE_W/2, ry+rh/2+8);
    ctx.textAlign='left';
    window._callRects.push({x:rx, y:ry, w:CM_REFINE_W, h:rh, refine:rk});
    if(ok) window._callRects.push({x:x, y:y, w:w-CM_REFINE_W-4, h:CM_ROW, id:id});
  } else if(ok){
    window._callRects.push({x:x, y:y, w:w, h:CM_ROW, id:id});
  }
}
function drawCallMenu(){
  if(!callMenu) return;
  const L  = callMenuLayout();
  const mx = L.mx, my = L.my;
  ctx.save();
  thFrame(mx, my, L.mw, L.mh, CM_TITLE);
  window._callPanelRect = {x:mx, y:my, w:L.mw, h:L.mh};

  ctx.textBaseline='middle'; ctx.textAlign='left';
  ctx.fillStyle=TH('textBright'); ctx.font=thLabel(14);
  ctx.fillText('REQUEST SUPPORT', mx+CM_PAD, my+16);
  ctx.textAlign='right';
  ctx.fillStyle=TH('textDim'); ctx.font=thValue(10, false);
  ctx.fillText('THREE OF A CLASS REFINE INTO ONE OF THE NEXT', mx+L.mw-CM_PAD, my+16);

  window._callRects=[];
  for(let ci=0;ci<L.COLS.length;ci++){
    const col = L.COLS[ci];
    const cx  = mx + CM_PAD + ci*(L.colw + CM_PAD);
    ctx.textAlign='left';
    ctx.fillStyle=TH('text'); ctx.font=thLabel(11);
    ctx.fillText(CM_FAC_HEAD[col[0].d.fac] || '', cx, my+L.headY+7);
    thScale(cx, my+L.headY+14, L.colw, [CM_PIC, CM_NAME], TH('edgeLight'));
    for(let ri=0;ri<col.length;ri++){
      drawAllyRow(cx, my+L.rowY+ri*(CM_ROW+CM_GAP), L.colw,
                  col[ri].id, col[ri].d, col[ri].key, false);
    }
  }

  if(L.showCol){
    const cd = ALLY_DEFS[ALLY_SPECIAL];
    const cx = mx + CM_PAD, cw = L.mw - CM_PAD*2;
    ctx.textAlign='left';
    ctx.fillStyle=TH('text'); ctx.font=thLabel(11);
    ctx.fillText(CM_FAC_HEAD.gtva, cx, my+L.colHeadY+7);
    thScale(cx, my+L.colHeadY+14, cw, [CM_PIC, CM_NAME], TH('edgeLight'));
    drawAllyRow(cx, my+L.colRowY, cw, ALLY_SPECIAL, cd, ALLY_SPECIAL_KEY, true);
  }

  ctx.textAlign='center'; ctx.fillStyle=TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText('ESC or tap outside to cancel', mx+L.mw/2, my+L.mh-11);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}

"""

# The cut ends at setCallMenu: it, toggleCallMenu and insidePanel sit between
# the menu and pointerConsumed, and none of them is being replaced.
src = cut_between(src, "function drawCallMenu(){", "\nfunction setCallMenu(open){", NEW_CALL, "drawCallMenu")

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
