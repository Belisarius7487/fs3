#!/usr/bin/env python3
"""FS3 v104 - ship switch.

- Ship selection screen removed; every run starts in the GVF Thoth.
- Per-hull stats (speed, agility, hull, shields, secondary rounds).
- Hulls unlock by score during a run and are lost on game over.
- Switch button in the top bar: needs an allied destroyer on the field,
  once per wave, free; hull, shields and secondary rounds are refilled.

Reads hlp_shooter_v103_logic.html, writes hlp_shooter_v104_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import re
import sys

SRC, DST = "hlp_shooter_v103_logic.html", "hlp_shooter_v104_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def js_block_end(text, start):
    """Index just past the brace block that opens at or after start.
    Skips strings, template literals and comments."""
    i = text.index("{", start)
    depth, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"`":
            q = c
            i += 1
            while i < n and text[i] != q:
                i += 2 if text[i] == "\\" else 1
        elif text.startswith("//", i):
            i = text.index("\n", i)
        elif text.startswith("/*", i):
            i = text.index("*/", i) + 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    sys.exit("Abbruch: Blockende nicht gefunden.")


def remove_function(text, header, label, lead=""):
    """Remove a top-level function (and optional leading comment lines)."""
    anchor = lead + header
    if text.count(anchor) != 1:
        sys.exit("Abbruch (%s): Funktionskopf %d-mal gefunden." % (label, text.count(anchor)))
    start = text.index(anchor)
    end = js_block_end(text, start + len(lead))
    if text[end:end + 1] == "\n":
        end += 1
    return text[:start] + text[end:]


with open(SRC, encoding="utf-8") as fh:
    t = fh.read()

# ---------------------------------------------------------------- data ----
pships_start = t.index("const PSHIPS={")
pships_end = t.index("};", pships_start) + 2
if t.count("const PSHIPS={") != 1:
    sys.exit("Abbruch (PSHIPS): Block nicht eindeutig.")
PLAYER_SHIPS = r"""// ── PLAYER SHIPS ─────────────────────────────────────────────
// Unlock order for the Hammer of Light cycle; the first entry is the
// starting ship. unlock is the score at which a hull becomes selectable
// during a run. Values come from the notes in the mount file:
// spd  top speed in px per logic step (fighter default 3.2)
// turn max heading change per logic step (default 0.14)
// hp   hull before cycle scaling, sh shield maximum, sec secondary rounds
const PLAYER_SHIPS = [
  {key:'fitoth',    name:'GVF Thoth',   unlock:0,     spd:3.5, turn:0.17, hp:100, sh:100, sec:20},
  {key:'fihorus',   name:'GVF Horus',   unlock:4000,  spd:3.2, turn:0.17, hp:80,  sh:100, sec:20},
  {key:'boosiris',  name:'GVB Osiris',  unlock:9000,  spd:2.5, turn:0.10, hp:140, sh:100, sec:10},
  {key:'fiserapis', name:'GVF Serapis', unlock:15000, spd:3.5, turn:0.17, hp:80,  sh:70,  sec:20},
  {key:'fiseth',    name:'GVF Seth',    unlock:22000, spd:2.5, turn:0.10, hp:125, sh:130, sec:20},
  {key:'bobakha',   name:'GVB Bakha',   unlock:31000, spd:2.5, turn:0.12, hp:100, sh:100, sec:8},
  {key:'fitauret',  name:'GVF Tauret',  unlock:43000, spd:2.9, turn:0.10, hp:100, sh:130, sec:20},
  {key:'bosekhmet', name:'GVB Sekhmet', unlock:58000, spd:2.5, turn:0.12, hp:140, sh:130, sec:12}
];"""
t = t[:pships_start] + PLAYER_SHIPS + t[pships_end:]

t = replace_once(t,
    "let selectedShip='fiherc',selectedShipType='fighter';\n",
    "let shipUnlocked=1;     // how many PLAYER_SHIPS entries this run has unlocked\n"
    "let shipSwapWave=-1;    // wave in which the free switch was spent\n"
    "let shipMenu=false;     // is the ship menu open?\n"
    "let gameOverAt=0;       // guards against restarting with the tap that died\n",
    "state")

# ------------------------------------------------------ launch and death ----
t = replace_once(t,
    "  var isFighter=PSHIPS.fighters.some(function(s){return s.key===selectedShip;});\n"
    "  selectedShipType=isFighter?'fighter':'bomber';\n",
    "  shipUnlocked=1; shipSwapWave=-1; shipMenu=false;\n",
    "launch reset")
t = replace_once(t,
    "          spd:isFighter?PLAYER_SPD_FIGHTER:PLAYER_SPD_BOMBER,\n",
    "          spd:PLAYER_SPD_FIGHTER, turn:PLAYER_TURN, baseHp:100,\n",
    "launch spd")
t = replace_once(t, "          ship:selectedShip,\n", "          ship:PLAYER_SHIPS[0].key,\n", "launch ship")
t = replace_once(t,
    "          secAmmo:isFighter?20:10,secMax:isFighter?20:10,\n"
    "          secTimer:0,secType:isFighter?'missile':'bomb'};\n",
    "          secAmmo:0,secMax:0,\n"
    "          secTimer:0,secType:'missile'};\n"
    "  applyShip(PLAYER_SHIPS[0].key);\n",
    "launch sec")
t = replace_once(t,
    "    if(--lives<=0){GS='gameover';return;}",
    "    if(--lives<=0){GS='gameover';gameOverAt=performance.now();return;}",
    "gameover time")
# A respawn used to come back with 100 hull whatever the maximum was.
t = replace_once(t,
    "  player.hp=100;player.x=80;player.y=H/2;eBullets=[];",
    "  player.hp=player.maxHp;player.x=80;player.y=H/2;eBullets=[];",
    "respawn hull")
t = remove_function(t, "function startGame(){", "startGame")

# ---------------------------------------------------------- next wave ----
t = replace_once(t,
    "    if(un.length) player.ship = un[un.length-1];",
    "    if(un.length && player.ship!==un[un.length-1]) applyShip(un[un.length-1]);",
    "fs1 roster")
t = replace_once(t,
    "    player.maxHp=Math.round(100*pm);",
    "    player.maxHp=Math.round((player.baseHp||100)*pm);",
    "cycle scaling")

t = replace_once(t,
    '  // In the campaign the roster grows as the briefings hand it over. Until\n  // the selection screen learns about eras, the newest unlocked hull is\n  // simply assigned; the player keeps whatever he already flies if it is\n  // still the newest.\n  if(FS1_MODE){\n    // PSHIPS is a list of {key,name} entries, not a map, so it cannot be\n    // asked whether it holds a key - and it lists the FS2 roster anyway,\n    // which has none of these hulls in it. The selection screen therefore\n    // stays cosmetic in campaign mode until it learns about eras.',
    "  // In the campaign the roster grows as the briefings hand it over; the\n"
    "  // newest unlocked hull is assigned and the switch button stays hidden.\n"
    "  if(FS1_MODE){",
    "fs1 comment")

# ------------------------------------------------------- flight model ----
t = replace_once(t,
    "player.head+=Math.max(-PLAYER_TURN,Math.min(PLAYER_TURN,dAng));",
    "player.head+=Math.max(-(player.turn||PLAYER_TURN),Math.min(player.turn||PLAYER_TURN,dAng));",
    "turn rate")
t = replace_once(t,
    "  const isBomber = PSHIPS.bombers.some(function(b){return b.key===(key||player.ship);});",
    "  const isBomber = isBomberHull(key || player.ship);",
    "playerSc")
t = replace_once(t,
    "      icoKey = PSHIPS.bombers.some(function(b){return b.key===player.ship;})",
    "      icoKey = isBomberHull(player.ship)",
    "life pickup icon")
t = replace_once(t,
    "  var lIsB = PSHIPS.bombers.some(function(b){return b.key===player.ship;});",
    "  var lIsB = isBomberHull(player.ship);",
    "lives icon")
t = replace_once(t, "  tickEvents();\n  if(arriveT>0) arriveT--;",
                 "  tickEvents();\n  tickShipUnlocks();\n  if(arriveT>0) arriveT--;", "unlock tick")

# --------------------------------------------------- selection screen ----
t = replace_once(t, "  if(GS==='shipselect'){drawShipSelect();return;}\n", "", "draw dispatch")
t = remove_function(t, "function handleShipSelect_unused(e){", "dead handler",
                    lead="// Dead code: nothing calls this, onShipScreenClick is the live handler.\n"
                         "// Left here it invited a second fix in the wrong place.\n")
t = replace_once(t, "let hoverShipIdx=-1;\n// hover mousemove entfernt (in neuen mousemove integriert)\n", "", "hover state")
t = remove_function(t, "function drawShipSelect(){", "drawShipSelect")
t = remove_function(t, "function onShipScreenClick(mx, my) {", "onShipScreenClick")

hover = re.compile(r"  // Hover for ship select\n  if\(GS==='shipselect'\)\{\n.*?\n  \}\n", re.S)
if len(hover.findall(t)) != 1:
    sys.exit("Abbruch (hover): Block nicht eindeutig.")
t = hover.sub("", t)

RESTART = "if(GS==='title'||performance.now()-gameOverAt>1500) launchGame();"
t = replace_once(t,
    "    if(GS==='title'||GS==='gameover'){\n"
    "      GS='shipselect';\n"
    "      document.getElementById('launchBtn').style.display='block';\n"
    "      document.body.classList.remove('nocursor');\n"
    "    } else if(GS==='shipselect') onShipScreenClick(p.x,p.y);\n",
    "    if(GS==='title'||GS==='gameover'){ " + RESTART + " }\n",
    "mousedown start")
t = replace_once(t,
    "  if(GS==='title'||GS==='gameover'){\n"
    "    GS='shipselect';\n"
    "    document.getElementById('launchBtn').style.display='block';\n"
    "  } else if(GS==='shipselect') onShipScreenClick(p.x,p.y);\n",
    "  if(GS==='title'||GS==='gameover'){ " + RESTART + " }\n",
    "touchstart start")
t = replace_once(t,
    "  if(GS==='title'&&(ev.code==='Space'||ev.code==='Enter')){GS='shipselect';document.getElementById('launchBtn').style.display='block';}\n"
    "  if(GS==='shipselect'&&ev.code==='Enter') launchGame();\n"
    "  if(GS==='gameover'&&(ev.code==='Space'||ev.code==='Enter')){GS='shipselect';document.getElementById('launchBtn').style.display='block';}\n",
    "  if((GS==='title'||GS==='gameover')&&(ev.code==='Space'||ev.code==='Enter')){ " + RESTART + " }\n",
    "keys start")
t = replace_once(t, "  if(ev.code==='KeyS' && !callMenu && (GS==='playing'||GS==='shipselect')){",
                 "  if(ev.code==='KeyS' && !callMenu && !shipMenu && GS==='playing'){", "key S")
t = replace_once(t, "  if(ev.code==='KeyF' && (GS==='playing'||GS==='shipselect')){",
                 "  if(ev.code==='KeyF' && GS==='playing'){", "key F")

# ------------------------------------------------------ switch logic ----
SWITCH = r"""// ── SHIP SWITCH ──────────────────────────────────────────────
// Stats for any hull. Hulls outside PLAYER_SHIPS (the FS1 roster) get the
// old fighter or bomber defaults.
function isBomberHull(key){ return hullClass(key)==='bo'; }
function shipStats(key){
  for(const s of PLAYER_SHIPS) if(s.key===key) return s;
  const b = isBomberHull(key);
  return {key:key, name:key, spd:b?PLAYER_SPD_BOMBER:PLAYER_SPD_FIGHTER, turn:PLAYER_TURN,
          hp:100, sh:100, sec:b?10:20};
}
// Puts the player into a hull with everything refilled.
function applyShip(key){
  const s = shipStats(key);
  player.ship   = key;
  player.spd    = s.spd;
  player.turn   = s.turn;
  player.baseHp = s.hp;
  player.maxHp  = Math.round(s.hp*(player.hullMult||1));
  player.hp     = player.maxHp;
  player.maxSh  = s.sh;
  resetPlayerShield();
  player.secMax = s.sec;
  player.secAmmo= s.sec;
  player.secType= isBomberHull(key) ? 'bomb' : 'missile';
}
// Unlocks follow the score within a run. Several thresholds can fall in
// one step, e.g. after a big bonus, so this loops.
function tickShipUnlocks(){
  if(GS!=='playing' || FS1_MODE) return;
  while(shipUnlocked < PLAYER_SHIPS.length && score >= PLAYER_SHIPS[shipUnlocked].unlock){
    const s = PLAYER_SHIPS[shipUnlocked++];
    SUB_MSGS.push({x:W/2, y:H*0.34, txt:s.name.toUpperCase()+' AVAILABLE', life:260, ml:260, ally:true});
  }
}
// The switch lands from an allied destroyer's hangar, so one has to be on
// the field. The campaign mode assigns its hulls itself.
function shipSwapReady(){
  if(GS!=='playing' || FS1_MODE || inJump()) return false;
  if(shipSwapWave===wave || shipUnlocked<2) return false;
  for(const a of allies)
    if(!a.small && !a.dead && !a.warpOut && hullClass(a.img)==='de') return true;
  return false;
}
function setShipMenu(open){
  shipMenu = open;
  paused   = open;
  if(open){
    document.body.classList.remove('nocursor');
  } else if(GS==='playing'){
    MOUSE.x = player.x; MOUSE.y = player.y;
    document.body.classList.add('nocursor');
  }
}
function toggleShipMenu(){
  if(shipMenu){ setShipMenu(false); return; }
  if(!shipSwapReady()) return;
  if(callMenu) setCallMenu(false);
  setShipMenu(true);
}
function swapShip(key){
  if(!shipMenu || key===player.ship) return;
  const i = PLAYER_SHIPS.findIndex(function(s){return s.key===key;});
  if(i<0 || i>=shipUnlocked) return;
  setShipMenu(false);
  applyShip(key);
  shipSwapWave = wave;
  SUB_MSGS.push({x:player.x+60, y:player.y-30, txt:PLAYER_SHIPS[i].name.toUpperCase(),
                 life:170, ml:170, ally:true});
}
// Two arrows passing each other.
function drawSwapIcon(cx, cy, col){
  ctx.save();
  ctx.strokeStyle=col; ctx.fillStyle=col; ctx.lineWidth=1.5;
  ctx.beginPath(); ctx.moveTo(cx-6,cy-3); ctx.lineTo(cx+3,cy-3); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx+7,cy-3); ctx.lineTo(cx+2,cy-6.5); ctx.lineTo(cx+2,cy+0.5); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(cx+6,cy+3); ctx.lineTo(cx-3,cy+3); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx-7,cy+3); ctx.lineTo(cx-2,cy-0.5); ctx.lineTo(cx-2,cy+6.5); ctx.closePath(); ctx.fill();
  ctx.restore();
}
// Filled pips for a value against its steps, so players compare hulls
// without reading raw numbers.
function statPips(x, y, v, steps, lit){
  let n = 0; for(const s of steps) if(v>=s-1e-9) n++;
  for(let i=0;i<steps.length;i++){
    ctx.fillStyle = i<n ? lit : '#1c2a22';
    ctx.fillRect(x+i*7, y, 5, 5);
  }
}
function drawShipMenu(){
  if(!shipMenu) return;
  const bw=236, bh=50, gap=8, cols=2, rows=Math.ceil(PLAYER_SHIPS.length/cols);
  const mw=bw*cols+gap*(cols+1), mh=30+rows*(bh+gap)+gap+22;
  const mx=((W-mw)/2)|0, my=((H-mh)/2)|0;
  ctx.save();
  ctx.fillStyle='rgba(0,0,0,0.72)'; ctx.fillRect(0,0,W,H);
  ctx.fillStyle='#020c06'; ctx.fillRect(mx,my,mw,mh);
  ctx.strokeStyle='#ffbb22'; ctx.lineWidth=2; ctx.strokeRect(mx,my,mw,mh);
  ctx.fillStyle='#ffd257'; ctx.font='bold 12px Courier New';
  ctx.textAlign='center'; ctx.textBaseline='top';
  ctx.fillText('SWITCH SHIP  -  ONCE PER WAVE', mx+mw/2, my+9);
  window._shipRects=[];
  for(let i=0;i<PLAYER_SHIPS.length;i++){
    const s=PLAYER_SHIPS[i], open=i<shipUnlocked, cur=s.key===player.ship;
    const bx=mx+gap+(i%cols)*(bw+gap), by=my+30+gap+((i/cols)|0)*(bh+gap);
    ctx.fillStyle=cur?'#2a1e00':(open?'#160f00':'#0a0a0a'); ctx.fillRect(bx,by,bw,bh);
    ctx.strokeStyle=cur?'#ffffff':(open?'#ffbb22':'#333'); ctx.lineWidth=cur?2:1;
    ctx.strokeRect(bx,by,bw,bh);
    ctx.textAlign='left';
    ctx.fillStyle=open?'#aa7722':'#444'; ctx.font='bold 9px Courier New';
    ctx.fillText('['+(i+1)+']', bx+6, by+6);
    ctx.fillStyle=open?'#ffd257':'#555'; ctx.font='bold 12px Courier New';
    ctx.fillText(s.name, bx+30, by+5);
    if(cur){ ctx.fillStyle='#ffffff'; ctx.font='bold 9px Courier New'; ctx.textAlign='right';
             ctx.fillText('ACTIVE', bx+bw-6, by+6); ctx.textAlign='left'; }
    if(open){
      ctx.fillStyle='#997733'; ctx.font='9px Courier New';
      ctx.fillText('HULL '+s.hp+'  SHIELD '+s.sh+'  '+s.sec+(isBomberHull(s.key)?' BOMBS':' MISSILES'), bx+30, by+21);
      ctx.fillText('SPD', bx+30, by+35);  statPips(bx+54,  by+36, s.spd,  [2.2,2.5,2.9,3.2,3.5], '#ffbb22');
      ctx.fillText('AGI', bx+104, by+35); statPips(bx+128, by+36, s.turn, [0.08,0.10,0.12,0.14,0.17], '#ffbb22');
    } else {
      ctx.fillStyle='#555'; ctx.font='9px Courier New';
      ctx.fillText('UNLOCKS AT '+s.unlock.toLocaleString('en-US')+' POINTS', bx+30, by+25);
    }
    // Every cell swallows its tap, so a locked or active hull cannot close
    // the menu by accident.
    window._shipRects.push({x:bx,y:by,w:bw,h:bh,key:(open&&!cur)?s.key:null});
  }
  ctx.textAlign='center'; ctx.fillStyle='#556'; ctx.font='9px Courier New';
  ctx.fillText('ESC or tap outside to cancel', mx+mw/2, my+mh-15);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}

"""
t = replace_once(t, "function drawCallMenu(){", SWITCH + "function drawCallMenu(){", "switch block")

# --------------------------------------------------------- input ----
t = replace_once(t,
    "  if(GS!=='playing') return false;\n  if(callMenu){",
    "  if(GS!=='playing') return false;\n"
    "  if(shipMenu){\n"
    "    for(const r of (window._shipRects||[]))\n"
    "      if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){ if(r.key) swapShip(r.key); return true; }\n"
    "    setShipMenu(false); return true;\n"
    "  }\n"
    "  var rsw=window._shipBtnRect;\n"
    "  if(rsw&&p.x>=rsw.x&&p.x<=rsw.x+rsw.w&&p.y>=rsw.y&&p.y<=rsw.y+rsw.h){ toggleShipMenu(); return true; }\n"
    "  if(callMenu){",
    "pointerConsumed")
t = replace_once(t, "  if(callMenu) return;\n  if(p.y<HUD_H&&GS==='playing') return; // HUD area, no movement input",
                 "  if(callMenu||shipMenu) return;\n  if(p.y<HUD_H&&GS==='playing') return; // HUD area, no movement input",
                 "touchmove")
t = replace_once(t,
    "  if(GS!=='playing') return;\n  if(ev.code==='KeyC'){ toggleCallMenu(); ev.preventDefault(); return; }",
    "  if(GS!=='playing') return;\n"
    "  if(ev.code==='KeyV'){ toggleShipMenu(); ev.preventDefault(); return; }\n"
    "  if(shipMenu){\n"
    "    if(ev.code==='Escape'){ setShipMenu(false); ev.preventDefault(); return; }\n"
    "    var sd = ev.code.indexOf('Digit')===0 ? ev.code.slice(5) : (ev.code.indexOf('Numpad')===0 ? ev.code.slice(6) : '');\n"
    "    var si = parseInt(sd,10);\n"
    "    if(si>=1 && si<=PLAYER_SHIPS.length){ swapShip(PLAYER_SHIPS[si-1].key); ev.preventDefault(); }\n"
    "    return;\n"
    "  }\n"
    "  if(ev.code==='KeyC'){ toggleCallMenu(); ev.preventDefault(); return; }",
    "keys switch")
t = replace_once(t, "  try{drawCallMenu();}catch(e){}\n",
                 "  try{drawCallMenu();}catch(e){}\n  try{drawShipMenu();}catch(e){}\n", "menu draw")

# ----------------------------------------------------------- HUD ----
t = replace_once(t, "  // ── PAUSE BUTTON ───────────────────────────────\n",
    "  // ── SHIP SWITCH BUTTON ─────────────────────────\n"
    "  // In the gap between the ticket grid (ends at 665) and the gear.\n"
    "  if(!FS1_MODE){\n"
    "    var swW=22, swH=H2-8, swX=Math.round((665+W-52)/2-swW/2), swY=4;\n"
    "    var swOn=shipSwapReady()||shipMenu;\n"
    "    ctx.fillStyle=shipMenu?'#553b00':(swOn?'#221800':'#0a0a0a');\n"
    "    ctx.fillRect(swX,swY,swW,swH);\n"
    "    ctx.strokeStyle=swOn?'#ffbb22':'#333'; ctx.lineWidth=2;\n"
    "    ctx.strokeRect(swX,swY,swW,swH);\n"
    "    drawSwapIcon(swX+swW/2, swY+swH/2, swOn?'#ffbb22':'#444');\n"
    "    window._shipBtnRect={x:swX,y:swY,w:swW,h:swH};\n"
    "  } else window._shipBtnRect=null;\n\n"
    "  // ── PAUSE BUTTON ───────────────────────────────\n",
    "hud button")

# --------------------------------------------------------- checks ----
for gone in ("PSHIPS", "selectedShip", "shipselect", "hoverShipIdx", "_selFsRect",
             "drawShipSelect", "onShipScreenClick", "handleShipSelect_unused", "startGame("):
    if gone in t:
        sys.exit("Abbruch: '%s' kommt noch vor." % gone)

with open(DST, "w", encoding="utf-8") as fh:
    fh.write(t)
print("Geschrieben: %s (%.0f KB)" % (DST, len(t.encode("utf-8")) / 1024))
