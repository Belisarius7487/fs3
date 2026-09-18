#!/usr/bin/env python3
"""FS3 v110 - the HLP forum theme as the game's own look.

Colour and type now live in one place instead of at 142 draw calls. The
values are the forum theme's own: index.css :root for Fire, void.css
html.hlp-void for Void.

The theme's real identity is not its borders. At rest it uses a quiet bevel
- light top left, dark bottom right - and emphasis comes from a three layer
glow ring. The game did the opposite: a loud saturated border on everything
and no way to emphasise anything. thBevel() and thGlow() are those two
devices, and the new top bar is built from them.

The old bar is kept as drawHUDClassic() so the two can be compared in the
running game rather than in a mockup. Settings grew a third page for it.

Two fixes that belong to the same subject:
- statPips() left ctx.fillStyle on the colour of its last pip, so the AGI
  label inherited it: bright behind a full speed bar, dark behind an empty
  one. It now restores what it found.
- The GUN / DMG line sat on baseline 37 while SPD and AGI sit on 35.

Reads hlp_shooter_v109_logic.html, writes hlp_shooter_v110_logic.html.
"""
import sys

SRC, DST = "hlp_shooter_v109_logic.html", "hlp_shooter_v110_logic.html"


def replace_n(text, old, new, label, times=1):
    n = text.count(old)
    if n != times:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet %d-mal." % (label, n, times))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# 1. Two more stored settings
src = replace_n(
    src,
    "let ECO = {res:1.5, blur:true, rim:true, glint:true};",
    "let ECO = {res:1.5, blur:true, rim:true, glint:true, hud:'hlp', scheme:'fire'};",
    "ECO defaults",
)
src = replace_n(
    src,
    "      ECO.blur = !!_eo.blur; ECO.rim = !!_eo.rim; ECO.glint = !!_eo.glint;",
    "      ECO.blur = !!_eo.blur; ECO.rim = !!_eo.rim; ECO.glint = !!_eo.glint;\n"
    "      if(_eo.hud==='classic' || _eo.hud==='hlp') ECO.hud = _eo.hud;\n"
    "      if(_eo.scheme==='fire' || _eo.scheme==='void') ECO.scheme = _eo.scheme;",
    "ECO load",
)

# 2. The token layer
src = replace_n(
    src,
    "function ecoSave(){\n  try{ localStorage.setItem('fs3_eco', JSON.stringify(ECO)); }catch(ex){}\n}",
    """function ecoSave(){
  try{ localStorage.setItem('fs3_eco', JSON.stringify(ECO)); }catch(ex){}
}

// HLP THEME TOKENS
// The two colour schemes of the HLP forum theme, copied from the theme's own
// CSS: index.css :root for Fire, void.css html.hlp-void for Void. The names
// are the roles the forum gives them, not the places the game draws, so a
// colour is looked up here instead of being typed at a draw call.
const THEMES = {
  fire: {
    back:'rgb(19,19,19)',         // body_bg
    panelBack:'rgb(37,18,18)',    // window_bg_2
    panelFront:'rgb(43,22,23)',   // window_bg_1
    raised:'rgb(52,26,26)',       // main_bg
    barTop:'rgb(72,36,36)',       // between main_bg and top_section
    edgeLight:'rgb(75,35,35)',    // main_border_cool_light
    edgeDark:'rgb(12,5,5)',       // main_border_cool_dark
    glow:'160,58,35',             // glow-rgb
    text:'rgb(185,170,153)',      // body_text
    textBright:'rgb(225,205,182)',// white
    textDim:'rgb(122,101,88)',
    accent:'rgb(156,214,255)',    // link
    accentWarm:'rgb(253,191,146)' // link_hover
  },
  void: {
    back:'rgb(14,10,24)',
    panelBack:'rgb(22,10,44)',
    panelFront:'rgb(28,13,54)',
    raised:'rgb(32,14,62)',
    barTop:'rgb(46,20,86)',
    edgeLight:'rgb(72,28,112)',
    edgeDark:'rgb(8,3,18)',
    glow:'155,48,225',
    text:'rgb(185,170,220)',
    textBright:'rgb(225,205,255)',
    textDim:'rgb(120,104,150)',
    accent:'rgb(180,145,255)',
    accentWarm:'rgb(195,95,255)'
  }
};
function TH(role){ return (THEMES[ECO.scheme] || THEMES.fire)[role]; }
// Type follows the forum as well: Tahoma for labels and headings, Segoe UI
// for values and running text. Both are system faces, so nothing has to
// finish loading before the first frame can be drawn.
function thLabel(px){ return 'bold '+px+'px Tahoma, "Segoe UI", sans-serif'; }
function thValue(px, bold){ return (bold?'bold ':'')+px+'px "Segoe UI", Tahoma, sans-serif'; }
// The resting edge: light from above left, dark below right. Quiet on
// purpose - in this theme a border is not what carries emphasis.
function thBevel(x, y, w, h){
  ctx.lineWidth = 1;
  ctx.strokeStyle = TH('edgeLight');
  ctx.beginPath();
  ctx.moveTo(x+0.5, y+h-0.5); ctx.lineTo(x+0.5, y+0.5); ctx.lineTo(x+w-0.5, y+0.5);
  ctx.stroke();
  ctx.strokeStyle = TH('edgeDark');
  ctx.beginPath();
  ctx.moveTo(x+w-0.5, y+0.5); ctx.lineTo(x+w-0.5, y+h-0.5); ctx.lineTo(x+0.5, y+h-0.5);
  ctx.stroke();
}
// What the forum emphasises with: a 1 px ring plus two blurred ones at
// falling opacity. Canvas has no box-shadow, so the blur comes from
// shadowBlur on a stroke. k scales the whole ring down for a weaker state.
function thGlow(x, y, w, h, k){
  const g = TH('glow'), s = (k===undefined) ? 1 : k;
  ctx.save();
  ctx.lineWidth = 1;
  ctx.shadowColor = 'rgba('+g+','+(0.40*s)+')'; ctx.shadowBlur = 6;
  ctx.strokeStyle = 'rgba('+g+','+(0.65*s)+')';
  ctx.strokeRect(x+0.5, y+0.5, w-1, h-1);
  ctx.shadowColor = 'rgba('+g+','+(0.20*s)+')'; ctx.shadowBlur = 14;
  ctx.strokeRect(x+0.5, y+0.5, w-1, h-1);
  ctx.restore();
}
// Every surface in the theme carries a vertical gradient, lighter at the top.
function thPanel(x, y, w, h, top, bottom){
  const gr = ctx.createLinearGradient(0, y, 0, y+h);
  gr.addColorStop(0, top); gr.addColorStop(1, bottom);
  ctx.fillStyle = gr; ctx.fillRect(x, y, w, h);
}
// A hairline divider, bevelled like everything else.
function thDivider(x, y0, y1){
  ctx.lineWidth = 1;
  ctx.strokeStyle = TH('edgeDark');
  ctx.beginPath(); ctx.moveTo(x+0.5, y0); ctx.lineTo(x+0.5, y1); ctx.stroke();
  ctx.strokeStyle = TH('edgeLight');
  ctx.beginPath(); ctx.moveTo(x+1.5, y0); ctx.lineTo(x+1.5, y1); ctx.stroke();
}
// One button, drawn the theme's way: quiet at rest, ringed when it wants
// attention. The caller owns whatever goes inside it.
function thButton(x, y, w, h, state){
  thPanel(x, y, w, h, TH('raised'), TH('panelBack'));
  thBevel(x, y, w, h);
  if(state==='on') thGlow(x, y, w, h, 1);
  else if(state==='ready') thGlow(x, y, w, h, 0.5);
}""",
    "token layer",
)

# 3. Split the bar into the old one and the new one
src = replace_n(
    src,
    "function drawHUD(){\n  if(GS!=='playing') return;\n  var H2=HUD_H,mid=(H2/2)|0;",
    """// Which bar is drawn is a stored setting, so the old one and the new one can
// be compared in a running game instead of in a mockup.
function drawHUD(){
  if(GS!=='playing') return;
  if(ECO.hud==='classic') drawHUDClassic();
  else                    drawHUDHLP();
}

// THE HLP BAR
// Same geometry as the old bar down to the pixel, so every pointer rectangle
// and everything that reads them keeps working. What changed is the surface:
// one palette, a bevel at rest, a glow ring for emphasis, and colour kept
// for meaning - green and amber for the hull, blue for the shield, the
// accent for anything that can be pressed.
function drawHUDHLP(){
  var H2=HUD_H, mid=(H2/2)|0;

  thPanel(0, 0, W, H2, TH('barTop'), TH('panelBack'));
  ctx.fillStyle=TH('panelBack'); ctx.fillRect(0, H-8, W, 8);
  ctx.strokeStyle=TH('edgeLight'); ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(0, H2-0.5); ctx.lineTo(W, H2-0.5); ctx.stroke();

  ctx.textBaseline='middle'; ctx.textAlign='left';

  // SCORE, WAVE, TIME
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('SCORE', 8, mid-9);
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(16, true);
  ctx.fillText(String(score).padStart(7,'0'), 8, mid+5);
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('TIME', 8, mid+19);
  ctx.fillStyle=callMenu?TH('textDim'):TH('text'); ctx.font=thValue(11, false);
  ctx.fillText(fmtTime(runTime), 34, mid+19);

  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('WAVE', 98, mid-9);
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(16, true);
  ctx.fillText(String(wave).padStart(3,'0'), 98, mid+5);

  thDivider(178, 4, H2-4);

  // HULL and SHIELD. The bars keep their own colours: those carry state.
  var hx=184, hw=110, hy=7, hh=9;
  var hR=player.hp/player.maxHp;
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('HULL', hx, hy+4);
  ctx.fillStyle=TH('edgeDark'); ctx.fillRect(hx, hy+11, hw, hh);
  ctx.globalAlpha=(hR<=HULL_CRIT)?(0.55+0.45*Math.sin(fc*0.22)):1;
  ctx.fillStyle=hullCol(hR);
  ctx.fillRect(hx, hy+11, (hw*hR)|0, hh);
  ctx.globalAlpha=1;
  thBevel(hx, hy+11, hw, hh);

  var sy=hy+24;
  var sR=player.sh/player.maxSh;
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('SHIELD', hx, sy+4);
  ctx.fillStyle=TH('edgeDark'); ctx.fillRect(hx, sy+11, hw, hh);
  ctx.fillStyle=sR>.5?'#0099ff':'#0055cc';
  ctx.fillRect(hx, sy+11, (hw*sR)|0, hh);
  thBevel(hx, sy+11, hw, hh);
  if(player.shDelay===0 && player.sh<player.maxSh && fc%30<15){
    ctx.fillStyle='rgba(0,100,200,0.2)'; ctx.fillRect(hx, sy+11, hw, hh);
  }

  thDivider(306, 4, H2-4);

  // LIVES
  var lx=312;
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('LIVES', lx, mid-9);
  var lIsB=isBomberHull(player.ship);
  var lIco=ICONS[lIsB?'bomberlives':'fighterlives'];
  var lsy=(mid+2)|0, usedW;
  if(lIco){
    var lh=15, lw=Math.max(1, Math.round(lIco.width*(lh/lIco.height)));
    ctx.drawImage(lIco, lx|0, (lsy-5)|0, lw, lh);
    usedW=lw;
  } else {
    ctx.fillStyle=TH('text');
    ctx.fillRect(lx, lsy+2, 11, 3); ctx.fillRect(lx+2, lsy, 7, 2);
    ctx.fillRect(lx+2, lsy+5, 7, 2); ctx.fillRect(lx+9, lsy+2, 4, 3);
    usedW=13;
  }
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(15, true);
  ctx.fillText(String(lives), lx+usedW+7, lsy+2);

  thDivider(406, 4, H2-4);

  // SECONDARY WEAPON
  var secX=412, secBW=34, secBH=H2-10, secBY=5;
  var isMissile=player.secType==='missile';
  var secRdy=player.secTimer===0 && player.secAmmo>0;
  var secClr=isMissile?'#ff8800':'#cc2200';
  thButton(secX, secBY, secBW, secBH, secRdy?'ready':null);
  if(isMissile) drawMissileIcon(secX+secBW/2, secBY+13, secRdy?secClr:TH('textDim'));
  else          drawBombIcon(secX+secBW/2, secBY+13, secRdy?secClr:TH('textDim'));
  ctx.fillStyle=secRdy?TH('textBright'):TH('textDim'); ctx.font=thValue(13, true);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillText(String(player.secAmmo).padStart(2,'0'), secX+secBW/2, secBY+31);
  if(player.secTimer>0){
    var cdMax=isMissile?45:90, cdW=secBW-8;
    ctx.fillStyle=TH('edgeDark'); ctx.fillRect(secX+4, secBY+secBH-6, cdW, 3);
    ctx.fillStyle=secClr;
    ctx.fillRect(secX+4, secBY+secBH-6, (cdW*(1-player.secTimer/cdMax))|0, 3);
  }
  ctx.textAlign='left'; ctx.textBaseline='middle';
  window._secBtnRect={x:secX, y:secBY, w:secBW, h:secBH};

  thDivider(449, 4, H2-4);

  // SUPPORT
  var alX=455, alBW=76, alBH=H2-10, alBY=5;
  var alRdy=allyReady(), alCan=alRdy && anyTicket();
  thButton(alX, alBY, alBW, alBH, alCan?'ready':null);
  ctx.textAlign='left';
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('SUPPORT', alX+5, alBY+9);
  ctx.fillStyle=alCan?TH('accent'):TH('textDim'); ctx.font=thValue(11, true);
  ctx.fillText(alRdy?(anyTicket()?'READY':'NO TICKET'):(allies.length?'DEPLOYED':'STANDBY'),
               alX+5, alBY+26);
  ctx.fillStyle=TH('textDim'); ctx.font=thValue(8, false);
  ctx.fillText('TAP / [C]', alX+5, alBY+alBH-7);
  window._allyBtnRect={x:alX, y:alBY, w:alBW, h:alBH};

  // TICKETS
  {
    var tkX=537, tkY=3, tkW=64, tkH=24;
    for(var ti=0; ti<TICKET_ORDER.length; ti++){
      var tk=TICKET_ORDER[ti], tn=tickets[tk]||0;
      var lit=tn>0;
      var fresh=(ticketFlash>0 && ticketFlashKind===tk && fc%16<10);
      var col=fresh?TH('accentWarm'):(lit?TH('accent'):TH('textDim'));
      var tico=ICONS[TICKET_ICON[tk]];
      var tcx=tkX+(ti%2)*tkW, tcy=tkY+((ti/2)|0)*tkH;
      ctx.textAlign='left'; ctx.textBaseline='top';
      ctx.fillStyle=col; ctx.font=thValue(13, true);
      ctx.fillText(tn+'x', tcx, tcy+5);
      var icoX=tcx+21;
      if(tico){
        ctx.globalAlpha=lit?1:0.28;
        var tih=11, tiw=Math.max(1, Math.round(tico.width*(tih/tico.height)));
        ctx.drawImage(tico, icoX, tcy+5, tiw, tih);
        ctx.globalAlpha=1;
      } else {
        ctx.fillStyle=col; ctx.font=thLabel(10);
        ctx.fillText(TICKET_ABBR[tk], icoX, tcy+6);
      }
    }
  }
  ctx.textBaseline='middle';

  // SHIP SWITCH
  if(!FS1_MODE){
    var swW=22, swH=H2-8, swX=Math.round((665+W-52)/2-swW/2), swY=4;
    var swOn=shipSwapReady()||shipMenu;
    thButton(swX, swY, swW, swH, shipMenu?'on':(swOn?'ready':null));
    drawSwapIcon(swX+swW/2, swY+swH/2, swOn?TH('accentWarm'):TH('textDim'));
    window._shipBtnRect={x:swX, y:swY, w:swW, h:swH};
  } else window._shipBtnRect=null;

  // SETTINGS and PAUSE
  var stbX=W-52, stbY=4, stbW=22, stbH=H2-8;
  thButton(stbX, stbY, stbW, stbH, settingsOpen?'on':null);
  drawGear(stbX+stbW/2, stbY+stbH/2, 7, settingsOpen?TH('textBright'):TH('text'));
  window._settingsBtnRect={x:stbX, y:stbY, w:stbW, h:stbH};

  var pbX=W-26, pbY=4, pbW=22, pbH=H2-8;
  thButton(pbX, pbY, pbW, pbH, paused?'on':null);
  drawPauseIcon(pbX+pbW/2, pbY+pbH/2, paused?TH('textBright'):TH('text'), !paused);
  window._pauseBtnRect={x:pbX, y:pbY, w:pbW, h:pbH};

  ctx.textAlign='left'; ctx.textBaseline='top';
}

function drawHUDClassic(){
  var H2=HUD_H,mid=(H2/2)|0;""",
    "HUD split",
)

# 4. statPips no longer leaves its colour behind
src = replace_n(
    src,
    "function statPips(x, y, v, steps, lit){\n  let n = 0; for(const s of steps) if(v>=s-1e-9) n++;",
    "function statPips(x, y, v, steps, lit){\n"
    "  // Restores the fill colour it found. Without this the next text drawn\n"
    "  // inherited the colour of the last pip, which is why the AGI label was\n"
    "  // bright behind a full speed bar and dark behind an empty one.\n"
    "  const prevFill = ctx.fillStyle;\n"
    "  let n = 0; for(const s of steps) if(v>=s-1e-9) n++;",
    "statPips head",
)
src = replace_n(
    src,
    "    ctx.fillStyle = i<n ? lit : '#1c2a22';\n    ctx.fillRect(x+i*7, y, 5, 5);\n  }\n}",
    "    ctx.fillStyle = i<n ? lit : '#1c2a22';\n"
    "    ctx.fillRect(x+i*7, y, 5, 5);\n"
    "  }\n"
    "  ctx.fillStyle = prevFill;\n}",
    "statPips tail",
)

# 5. The GUN line onto the same baseline as SPD and AGI
src = replace_n(
    src,
    "        ctx.fillText('GUN '+gn+'  DMG '+Math.round(volleyTotal(gn)), bx+bw-6, by+37);",
    "        ctx.fillText('GUN '+gn+'  DMG '+Math.round(volleyTotal(gn)), bx+bw-6, by+35);",
    "gun baseline",
)

# 6. Settings: a third page for the look
src = replace_n(
    src,
    "function settingsRows(){\n  if(settingsPage===1) return [",
    """const SETTINGS_PAGES = 3;
const SETTINGS_TITLES = ['SETTINGS', 'ECONOMY', 'APPEARANCE'];
function settingsRows(){
  if(settingsPage===2) return [
    {label:'INTERFACE', hint:'HLP forum theme, or the previous look',
     value:ECO.hud==='hlp'?'HLP':'CLASSIC', on:ECO.hud==='hlp',
     act:'uistyle', enabled:true},
    {label:'COLOUR SCHEME', hint:'the two schemes of the forum theme',
     value:ECO.scheme==='void'?'VOID':'FIRE', on:true,
     act:'scheme', enabled:ECO.hud==='hlp'}
  ];
  if(settingsPage===1) return [""",
    "settings pages",
)
src = replace_n(
    src,
    "  const bw=300, bh=40, gap=8, rows=4;",
    "  const bw=300, bh=40, gap=8;\n"
    "  // The height follows the page, so a shorter page leaves no hole.\n"
    "  const rows=Math.max(1, settingsRows().length);",
    "settings rows count",
)
src = replace_n(
    src,
    "  ctx.fillText(settingsPage===1?'ECONOMY':'SETTINGS', mx+mw/2, my+9);",
    "  ctx.fillText(SETTINGS_TITLES[settingsPage]||'SETTINGS', mx+mw/2, my+9);",
    "settings title",
)
src = replace_n(
    src,
    "  ctx.fillText('PAGE '+(settingsPage+1)+'/2', mx+mw/2, ny+5);\n"
    "  window._setRects.push({x:bx, y:ny, w:40, h:18, act:'page'});\n"
    "  window._setRects.push({x:bx+bw-40, y:ny, w:40, h:18, act:'page'});",
    "  ctx.fillText('PAGE '+(settingsPage+1)+'/'+SETTINGS_PAGES, mx+mw/2, ny+5);\n"
    "  // Separate actions: with three pages one toggle cannot reach them all.\n"
    "  window._setRects.push({x:bx, y:ny, w:40, h:18, act:'pageprev'});\n"
    "  window._setRects.push({x:bx+bw-40, y:ny, w:40, h:18, act:'pagenext'});",
    "settings paging rects",
)
src = replace_n(
    src,
    "      else if(r.act==='page'){ settingsPage=settingsPage?0:1; }",
    "      else if(r.act==='pagenext'){ settingsPage=(settingsPage+1)%SETTINGS_PAGES; }\n"
    "      else if(r.act==='pageprev'){ settingsPage=(settingsPage+SETTINGS_PAGES-1)%SETTINGS_PAGES; }\n"
    "      else if(r.act==='uistyle'){ ECO.hud=(ECO.hud==='hlp')?'classic':'hlp'; ecoSave(); }\n"
    "      else if(r.act==='scheme'){ ECO.scheme=(ECO.scheme==='void')?'fire':'void'; ecoSave(); }",
    "settings actions",
)

for name in ("function drawHUDHLP(", "function drawHUDClassic(", "function thGlow(",
             "function thBevel(", "const THEMES", "prevFill", "'uistyle'", "'scheme'"):
    if name not in src:
        sys.exit("Abbruch: '%s' fehlt im Ergebnis." % name)
if "by+37" in src:
    sys.exit("Abbruch: die alte Grundlinie 37 ist noch vorhanden.")

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
