#!/usr/bin/env python3
"""FS3 v111 - the rest of the interface, in the theme's language.

v110 converted the top bar and left everything else in the old green and
yellow. This converts the three panels the player actually spends time in:
the settings window, the ship hangar and the support call.

No second copy of any drawing routine. UI() resolves a colour to the
theme's role in HLP mode and to the previous literal in CLASSIC mode, and
uiCell() / uiDialog() draw either the old flat fill with its loud border or
the theme's gradient with a bevel and, where something wants attention, the
glow ring. One routine, two looks, so they cannot drift apart.

Reads hlp_shooter_v110_logic.html, writes hlp_shooter_v111_logic.html.
"""
import sys

SRC, DST = "hlp_shooter_v110_logic.html", "hlp_shooter_v111_logic.html"


def rep(text, old, new, label, times=1):
    n = text.count(old)
    if n != times:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet %d-mal." % (label, n, times))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# ── 1. The resolver and the two shared surfaces ─────────────────────
src = rep(
    src,
    "function thButton(x, y, w, h, state){",
    """// One place that resolves a colour: the theme's role in HLP mode, the
// previous literal in CLASSIC mode. This is what lets both looks share a
// single drawing routine instead of being two copies that drift apart.
function UI(role, classic){ return (ECO.hud==='classic') ? classic : TH(role); }
function uiHLP(){ return ECO.hud!=='classic'; }
function uiLabel(px, classic){ return uiHLP() ? thLabel(px) : classic; }
function uiValue(px, bold, classic){ return uiHLP() ? thValue(px, bold) : classic; }
// A cell or a row. state: 'on' for the active one, 'ready' for available,
// 'off' for locked or unaffordable.
function uiCell(x, y, w, h, o){
  o = o || {};
  if(!uiHLP()){
    ctx.fillStyle = o.fill; ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = o.stroke; ctx.lineWidth = o.lw || 1;
    ctx.strokeRect(x, y, w, h);
    return;
  }
  if(o.state==='off'){
    ctx.fillStyle = TH('back'); ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = TH('edgeDark'); ctx.lineWidth = 1;
    ctx.strokeRect(x+0.5, y+0.5, w-1, h-1);
    return;
  }
  thPanel(x, y, w, h,
          o.state==='on' ? TH('raised')     : TH('panelFront'),
          o.state==='on' ? TH('panelFront') : TH('panelBack'));
  thBevel(x, y, w, h);
  if(o.state==='on')         thGlow(x, y, w, h, 1);
  else if(o.state==='ready') thGlow(x, y, w, h, 0.45);
}
// A panel over the playfield: the dim sheet behind it, then the panel body.
function uiDialog(x, y, w, h, classicFill, classicStroke){
  ctx.fillStyle = uiHLP() ? 'rgba(0,0,0,0.78)' : 'rgba(0,0,0,0.72)';
  ctx.fillRect(0, 0, W, H);
  if(!uiHLP()){
    ctx.fillStyle = classicFill; ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = classicStroke; ctx.lineWidth = 2; ctx.strokeRect(x, y, w, h);
    return;
  }
  thPanel(x, y, w, h, TH('panelFront'), TH('back'));
  thBevel(x, y, w, h);
  thGlow(x, y, w, h, 0.85);
}
function thButton(x, y, w, h, state){""",
    "resolver",
)

# ── 2. The settings row ─────────────────────────────────────────────
src = rep(
    src,
    """  ctx.fillStyle = enabled ? '#00160c' : '#0a0a0a';
  ctx.fillRect(bx,by,bw,bh);
  ctx.strokeStyle = enabled ? '#4499ff' : '#333'; ctx.lineWidth=1;
  ctx.strokeRect(bx,by,bw,bh);
  ctx.textAlign='left';
  ctx.fillStyle = enabled ? '#7fc4ff' : '#555'; ctx.font='bold 12px Courier New';
  ctx.fillText(label, bx+12, by+7);
  ctx.fillStyle = enabled ? '#007733' : '#3a3a3a'; ctx.font='9px Courier New';
  ctx.fillText(hint, bx+12, by+24);
  ctx.textAlign='right';
  ctx.fillStyle = on ? '#00ee55' : '#666'; ctx.font='bold 12px Courier New';
  ctx.fillText(value, bx+bw-12, by+14);""",
    """  uiCell(bx, by, bw, bh, {state: enabled ? (on?'ready':null) : 'off',
                          fill: enabled?'#00160c':'#0a0a0a',
                          stroke: enabled?'#4499ff':'#333'});
  ctx.textAlign='left';
  ctx.fillStyle = enabled ? UI('textBright','#7fc4ff') : UI('textDim','#555');
  ctx.font = uiValue(13, true, 'bold 12px Courier New');
  ctx.fillText(label, bx+12, by+7);
  ctx.fillStyle = enabled ? UI('textDim','#007733') : UI('edgeLight','#3a3a3a');
  ctx.font = uiValue(10, false, '9px Courier New');
  ctx.fillText(hint, bx+12, by+24);
  ctx.textAlign='right';
  ctx.fillStyle = on ? UI('accent','#00ee55') : UI('textDim','#666');
  ctx.font = uiValue(13, true, 'bold 12px Courier New');
  ctx.fillText(value, bx+bw-12, by+14);""",
    "setRow",
)

# ── 3. The settings window ──────────────────────────────────────────
src = rep(
    src,
    """  ctx.fillStyle='rgba(0,0,0,0.72)'; ctx.fillRect(0,0,W,H);
  ctx.fillStyle='rgba(0,14,6,0.96)'; ctx.fillRect(mx,my,mw,mh);
  ctx.strokeStyle='#00aa44'; ctx.lineWidth=2; ctx.strokeRect(mx,my,mw,mh);
  ctx.fillStyle='#00ee55'; ctx.font='bold 13px Courier New';""",
    """  uiDialog(mx, my, mw, mh, 'rgba(0,14,6,0.96)', '#00aa44');
  ctx.fillStyle=UI('textBright','#00ee55');
  ctx.font=uiLabel(13, 'bold 13px Courier New');""",
    "settings dialog",
)
src = rep(
    src,
    """  ctx.fillStyle='#00160c'; ctx.fillRect(bx, ny, 40, 18);
  ctx.fillRect(bx+bw-40, ny, 40, 18);
  ctx.strokeStyle='#4499ff'; ctx.lineWidth=1;
  ctx.strokeRect(bx, ny, 40, 18); ctx.strokeRect(bx+bw-40, ny, 40, 18);
  ctx.fillStyle='#7fc4ff'; ctx.font='bold 12px Courier New';""",
    """  uiCell(bx, ny, 40, 18, {state:'ready', fill:'#00160c', stroke:'#4499ff'});
  uiCell(bx+bw-40, ny, 40, 18, {state:'ready', fill:'#00160c', stroke:'#4499ff'});
  ctx.fillStyle=UI('accent','#7fc4ff');
  ctx.font=uiValue(13, true, 'bold 12px Courier New');""",
    "settings nav",
)
src = rep(
    src,
    "  ctx.fillStyle='#007733'; ctx.font='9px Courier New';\n"
    "  ctx.fillText('PAGE '+(settingsPage+1)+'/'+SETTINGS_PAGES, mx+mw/2, ny+5);",
    "  ctx.fillStyle=UI('textDim','#007733'); ctx.font=uiValue(10, false, '9px Courier New');\n"
    "  ctx.fillText('PAGE '+(settingsPage+1)+'/'+SETTINGS_PAGES, mx+mw/2, ny+5);",
    "settings page label",
)
src = rep(
    src,
    "  ctx.fillStyle='#005522'; ctx.font='9px Courier New';\n"
    "  ctx.fillText('FS3  '+GAME_VERSION, mx+mw/2, my+mh-hintH-verH+4);\n"
    "  ctx.fillStyle='#007733'; ctx.font='9px Courier New';\n"
    "  ctx.fillText('tap outside or press S to close', mx+mw/2, my+mh-hintH+6);",
    "  ctx.fillStyle=UI('edgeLight','#005522'); ctx.font=uiValue(10, false, '9px Courier New');\n"
    "  ctx.fillText('FS3  '+GAME_VERSION, mx+mw/2, my+mh-hintH-verH+4);\n"
    "  ctx.fillStyle=UI('textDim','#007733'); ctx.font=uiValue(10, false, '9px Courier New');\n"
    "  ctx.fillText('tap outside or press S to close', mx+mw/2, my+mh-hintH+6);",
    "settings footer",
)

# ── 4. The hangar ───────────────────────────────────────────────────
src = rep(
    src,
    """  ctx.fillStyle='rgba(0,0,0,0.72)'; ctx.fillRect(0,0,W,H);
  ctx.fillStyle='#020c06'; ctx.fillRect(mx,my,mw,mh);
  ctx.strokeStyle='#ffbb22'; ctx.lineWidth=2; ctx.strokeRect(mx,my,mw,mh);
  ctx.fillStyle='#ffd257'; ctx.font='bold 12px Courier New';""",
    """  uiDialog(mx, my, mw, mh, '#020c06', '#ffbb22');
  ctx.fillStyle=UI('textBright','#ffd257');
  ctx.font=uiLabel(13, 'bold 12px Courier New');""",
    "hangar dialog",
)
src = rep(
    src,
    """    ctx.fillStyle=cur?'#2a1e00':(open?'#160f00':'#0a0a0a'); ctx.fillRect(bx,by,bw,bh);
    ctx.strokeStyle=cur?'#ffffff':(open?'#ffbb22':'#333'); ctx.lineWidth=cur?2:1;
    ctx.strokeRect(bx,by,bw,bh);""",
    """    uiCell(bx, by, bw, bh, {state: cur?'on':(open?'ready':'off'),
                            fill: cur?'#2a1e00':(open?'#160f00':'#0a0a0a'),
                            stroke: cur?'#ffffff':(open?'#ffbb22':'#333'),
                            lw: cur?2:1});""",
    "hangar cell",
)
src = rep(
    src,
    "    ctx.fillStyle=open?'#aa7722':'#444'; ctx.font='bold 9px Courier New';\n"
    "    ctx.fillText('['+(i+1)+']', bx+6, by+6);\n"
    "    ctx.fillStyle=open?'#ffd257':'#555'; ctx.font='bold 12px Courier New';\n"
    "    ctx.fillText(s.name, bx+30, by+5);",
    "    ctx.fillStyle=open?UI('textDim','#aa7722'):UI('edgeLight','#444');\n"
    "    ctx.font=uiValue(10, true, 'bold 9px Courier New');\n"
    "    ctx.fillText(uiHLP()?String(i+1):'['+(i+1)+']', bx+6, by+6);\n"
    "    ctx.fillStyle=open?UI('textBright','#ffd257'):UI('textDim','#555');\n"
    "    ctx.font=uiValue(13, true, 'bold 12px Courier New');\n"
    "    ctx.fillText(s.name, bx+30, by+5);",
    "hangar name",
)
src = rep(
    src,
    "    if(cur){ ctx.fillStyle='#ffffff'; ctx.font='bold 9px Courier New'; ctx.textAlign='right';",
    "    if(cur){ ctx.fillStyle=UI('accentWarm','#ffffff');\n"
    "             ctx.font=uiLabel(9, 'bold 9px Courier New'); ctx.textAlign='right';",
    "hangar active tag",
)
src = rep(
    src,
    "      ctx.fillStyle='#997733'; ctx.font='9px Courier New';\n"
    "      ctx.fillText('HULL '+s.hp+'  SHIELD '+s.sh+'  '+s.sec+(isBomberHull(s.key)?' BOMBS':' MISSILES'), bx+30, by+21);\n"
    "      ctx.fillText('SPD', bx+30, by+35);  statPips(bx+54,  by+36, s.spd,  [2.2,2.5,2.9,3.2,3.5], '#ffbb22');\n"
    "      ctx.fillText('AGI', bx+104, by+35); statPips(bx+128, by+36, s.turn, [0.08,0.10,0.12,0.14,0.17], '#ffbb22');",
    "      ctx.fillStyle=UI('text','#997733'); ctx.font=uiValue(10, false, '9px Courier New');\n"
    "      ctx.fillText('HULL '+s.hp+'  SHIELD '+s.sh+'  '+s.sec+(isBomberHull(s.key)?' BOMBS':' MISSILES'), bx+30, by+21);\n"
    "      ctx.fillText('SPD', bx+30, by+35);  statPips(bx+54,  by+36, s.spd,  [2.2,2.5,2.9,3.2,3.5], UI('accentWarm','#ffbb22'));\n"
    "      ctx.fillText('AGI', bx+104, by+35); statPips(bx+128, by+36, s.turn, [0.08,0.10,0.12,0.14,0.17], UI('accentWarm','#ffbb22'));",
    "hangar stats",
)
src = rep(
    src,
    "        ctx.textAlign='right'; ctx.font='8px Courier New'; ctx.fillStyle='#997733';",
    "        ctx.textAlign='right'; ctx.font=uiValue(9, false, '8px Courier New');\n"
    "        ctx.fillStyle=UI('textDim','#997733');",
    "hangar gun line",
)
src = rep(
    src,
    "      ctx.fillStyle='#555'; ctx.font='9px Courier New';\n"
    "      ctx.fillText(off ? 'NO '+(s.fac||'').toUpperCase()+' HANGAR ON THE FIELD'",
    "      ctx.fillStyle=UI('textDim','#555'); ctx.font=uiValue(10, false, '9px Courier New');\n"
    "      ctx.fillText(off ? 'NO '+(s.fac||'').toUpperCase()+' HANGAR ON THE FIELD'",
    "hangar locked text",
)
src = rep(
    src,
    "  ctx.textAlign='center'; ctx.fillStyle='#556'; ctx.font='9px Courier New';\n"
    "  ctx.fillText('ESC or tap outside to cancel', mx+mw/2, my+mh-15);",
    "  ctx.textAlign='center'; ctx.fillStyle=UI('textDim','#556');\n"
    "  ctx.font=uiValue(10, false, '9px Courier New');\n"
    "  ctx.fillText('ESC or tap outside to cancel', mx+mw/2, my+mh-15);",
    "hangar hint",
)

# ── 5. The support call ─────────────────────────────────────────────
src = rep(
    src,
    """  ctx.fillStyle='rgba(0,0,0,0.72)'; ctx.fillRect(0,0,W,H);
  ctx.fillStyle='#020c06'; ctx.fillRect(mx,my,mw,mh);
  ctx.strokeStyle='#00ee55'; ctx.lineWidth=2; ctx.strokeRect(mx,my,mw,mh);
  ctx.fillStyle='#00ee55'; ctx.font='bold 12px Courier New';""",
    """  uiDialog(mx, my, mw, mh, '#020c06', '#00ee55');
  ctx.fillStyle=UI('textBright','#00ee55');
  ctx.font=uiLabel(13, 'bold 12px Courier New');""",
    "call dialog",
)
src = rep(
    src,
    "    ctx.fillStyle=ok?'#00160c':'#0a0a0a';\n"
    "    ctx.fillRect(bx,by,bw,bh);\n"
    "    ctx.strokeStyle=ok?(vas?'#ffbb22':'#4499ff'):'#333'; ctx.lineWidth=1;\n"
    "    ctx.strokeRect(bx,by,bw,bh);",
    "    uiCell(bx, by, bw, bh, {state: ok?'ready':'off',\n"
    "                            fill: ok?'#00160c':'#0a0a0a',\n"
    "                            stroke: ok?(vas?'#ffbb22':'#4499ff'):'#333'});",
    "call row",
)
src = rep(
    src,
    "    ctx.fillStyle=ok?'#00aa44':'#444'; ctx.font='bold 9px Courier New';\n"
    "    ctx.fillText('['+CELLS[i].key+']', bx+7, by+7);",
    "    ctx.fillStyle=ok?UI('textDim','#00aa44'):UI('edgeLight','#444');\n"
    "    ctx.font=uiValue(10, true, 'bold 9px Courier New');\n"
    "    ctx.fillText(uiHLP()?CELLS[i].key:'['+CELLS[i].key+']', bx+7, by+7);",
    "call key",
)
src = rep(
    src,
    "    ctx.fillStyle=ok?'#7fd8ff':'#3a3a3a'; ctx.font='bold 10px Courier New';\n"
    "    ctx.fillText((tickets[allyTicket(id)]||0)+'x', bx+7, by+20);\n"
    "    ctx.fillStyle=ok?(vas?'#ffd257':'#7fc4ff'):'#555'; ctx.font='bold 12px Courier New';\n"
    "    ctx.fillText(d.label, bx+30, by+5);\n"
    "    ctx.fillStyle=ok?'#007733':'#3a3a3a'; ctx.font='9px Courier New';",
    "    ctx.fillStyle=ok?UI('accent','#7fd8ff'):UI('edgeLight','#3a3a3a');\n"
    "    ctx.font=uiValue(11, true, 'bold 10px Courier New');\n"
    "    ctx.fillText((tickets[allyTicket(id)]||0)+'x', bx+7, by+20);\n"
    "    ctx.fillStyle=ok?UI('textBright',(vas?'#ffd257':'#7fc4ff')):UI('textDim','#555');\n"
    "    ctx.font=uiValue(13, true, 'bold 12px Courier New');\n"
    "    ctx.fillText(d.label, bx+30, by+5);\n"
    "    ctx.fillStyle=ok?UI('text','#007733'):UI('edgeLight','#3a3a3a');\n"
    "    ctx.font=uiValue(10, false, '9px Courier New');",
    "call label",
)
src = rep(
    src,
    "      ctx.fillStyle='#052018';\n"
    "      ctx.fillRect(rx,ry,rw,rh);\n"
    "      ctx.strokeStyle='#00cc88'; ctx.lineWidth=1;\n"
    "      ctx.strokeRect(rx,ry,rw,rh);\n"
    "      ctx.fillStyle='#00eeaa'; ctx.font='bold 13px Courier New';",
    "      uiCell(rx, ry, rw, rh, {state:'ready', fill:'#052018', stroke:'#00cc88'});\n"
    "      ctx.fillStyle=UI('accentWarm','#00eeaa');\n"
    "      ctx.font=uiValue(14, true, 'bold 13px Courier New');",
    "call refine",
)
src = rep(
    src,
    "      ctx.font='7px Courier New'; ctx.fillStyle='#008866';",
    "      ctx.font=uiValue(8, false, '7px Courier New');\n"
    "      ctx.fillStyle=UI('textDim','#008866');",
    "call refine label",
)
src = rep(
    src,
    "    ctx.fillStyle=ok?'#001a18':'#0a0a0a';\n"
    "    ctx.fillRect(cbx,cby,cbw,bh);\n"
    "    ctx.strokeStyle=ok?'#66ffe0':'#333'; ctx.lineWidth=ok?2:1;\n"
    "    ctx.strokeRect(cbx,cby,cbw,bh);",
    "    // The Colossus is the one row that gets the full ring: she is the\n"
    "    // rarest thing in the menu.\n"
    "    uiCell(cbx, cby, cbw, bh, {state: ok?'on':'off',\n"
    "                               fill: ok?'#001a18':'#0a0a0a',\n"
    "                               stroke: ok?'#66ffe0':'#333', lw: ok?2:1});",
    "colossus row",
)
src = rep(
    src,
    "    ctx.fillStyle=ok?'#00aa44':'#444'; ctx.font='bold 9px Courier New';\n"
    "    ctx.fillText('['+ALLY_SPECIAL_KEY+']', cbx+7, cby+7);\n"
    "    ctx.fillStyle=ok?'#a8fff0':'#3a3a3a'; ctx.font='bold 10px Courier New';\n"
    "    ctx.fillText((tickets[ALLY_SPECIAL]||0)+'x', cbx+7, cby+20);\n"
    "    ctx.fillStyle=ok?'#a8fff0':'#555'; ctx.font='bold 12px Courier New';\n"
    "    ctx.fillText(cd.label, cbx+34, cby+5);\n"
    "    ctx.fillStyle=ok?'#008866':'#3a3a3a'; ctx.font='9px Courier New';",
    "    ctx.fillStyle=ok?UI('textDim','#00aa44'):UI('edgeLight','#444');\n"
    "    ctx.font=uiValue(10, true, 'bold 9px Courier New');\n"
    "    ctx.fillText(uiHLP()?ALLY_SPECIAL_KEY:'['+ALLY_SPECIAL_KEY+']', cbx+7, cby+7);\n"
    "    ctx.fillStyle=ok?UI('accent','#a8fff0'):UI('edgeLight','#3a3a3a');\n"
    "    ctx.font=uiValue(11, true, 'bold 10px Courier New');\n"
    "    ctx.fillText((tickets[ALLY_SPECIAL]||0)+'x', cbx+7, cby+20);\n"
    "    ctx.fillStyle=ok?UI('textBright','#a8fff0'):UI('textDim','#555');\n"
    "    ctx.font=uiValue(13, true, 'bold 12px Courier New');\n"
    "    ctx.fillText(cd.label, cbx+34, cby+5);\n"
    "    ctx.fillStyle=ok?UI('text','#008866'):UI('edgeLight','#3a3a3a');\n"
    "    ctx.font=uiValue(10, false, '9px Courier New');",
    "colossus text",
)
src = rep(
    src,
    "  ctx.textAlign='center'; ctx.fillStyle='#556';\n"
    "  ctx.font='9px Courier New';\n"
    "  ctx.fillText('ESC or tap outside to cancel', mx+mw/2, my+mh-14);",
    "  ctx.textAlign='center'; ctx.fillStyle=UI('textDim','#556');\n"
    "  ctx.font=uiValue(10, false, '9px Courier New');\n"
    "  ctx.fillText('ESC or tap outside to cancel', mx+mw/2, my+mh-14);",
    "call hint",
)

for name in ("function UI(", "function uiCell(", "function uiDialog(", "uiLabel(13,"):
    if name not in src:
        sys.exit("Abbruch: '%s' fehlt im Ergebnis." % name)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
