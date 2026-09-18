#!/usr/bin/env python3
"""FS3 v120 - weapons become a thing you choose, and the rearm panel to do it.

Until now the armament hung on the hull and nowhere else: one gun for
everybody, and the secondary decided by whether the hull was a bomber. There
was no weapon anywhere in the code - only a fire routine with the numbers
written into it.

What this lays down:

  PRIMARIES / SECONDARIES   two tables. Everything that differs between two
                            weapons lives there, so the next one is a line of
                            data rather than a branch inside pShoot().
  player.pri / player.sec    what is actually fitted, by key.
  applyLoadout()             the single place that puts a choice onto the ship.
  rearm panel                a button in the bar beside the ship switch, and a
                             panel in the hangar's language. It needs an
                             allied CORVETTE on the field, the way the hangar
                             needs a destroyer.

The Prometheus is the gun the game already had, to the point: dmg and rate are
factors on the old fixed values and hers are both 1.0, so nothing about the
standard fit changes. Same for the MX-64 and the Cyclops. Only the names are
new, and the Mekhu HL-7, which is the first weapon that is actually a choice:
quicker and lighter, and the first gun in the game with a limited reach.

A switch refills the rack. That is deliberate and it is why the panel is
called REARM: with a corvette on the field you can top up by refitting the
same weapon, and that is a supply point rather than a loophole.

Ammunition stays a property of the HULL - PLAYER_SHIPS.sec - because a bomber
carrying ten and a fighter twenty is part of what tells them apart. A weapon
scales that with ammoMul rather than replacing it.

Reads hlp_shooter_v119_logic.html, writes hlp_shooter_v120_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v119_logic.html", "hlp_shooter_v120_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# ── 1. The tables ────────────────────────────────────────────────────
WEAPONS = r"""// ── WEAPONS ──────────────────────────────────────────────────
// A weapon is data. Everything that differs between two of them lives in
// these tables, so the next one is a line here rather than a branch inside
// the firing routine.
//
// dmg and rate are factors on the values the game fired with before this
// existed, and the Prometheus carries 1.0 for both. That is what makes the
// standard fit provably unchanged: the numbers are not retyped anywhere.
//
// range is how far a bolt travels before it gives out, in points. 0 means it
// runs to the edge of the field, the way every bolt used to.
const PLAYER_FR_BASE = 28;   // steps between shots at rate 1.0
const PRIMARIES = [
  {key:'prometheus', name:'Prometheus', unlock:0,
   dmg:1.00, rate:1.00, spd:9, range:0,
   col:'#ccff88', glow:'rgba(180,255,80,0.30)',
   note:'standard fit, and the longest reach of any gun'},
  // The same gun under two names: the Vasudan fleet calls it Mekhu, the
  // Terran one Subach. The game already renames hulls by era, so a weapon
  // with two names costs nothing but the second string.
  {key:'hl7', name:'Mekhu HL-7', nameTer:'Subach HL-7', unlock:6000,
   dmg:0.62, rate:0.60, spd:10.5, range:330,
   col:'#bfe9ff', glow:'rgba(120,200,255,0.30)',
   note:'quicker and lighter, and it runs out of reach early'}
];
// cls decides which hull may carry it: a fighter takes missiles, a bomber
// takes bombs, and neither takes the other's.
const SECONDARIES = [
  {key:'mx64', name:'MX-64', cls:'missile', unlock:0,
   ammoMul:1.0, dmg:35, cd:45, spd:3.5, life:220, homing:true,
   note:'light homing, quick off the rail'},
  {key:'cyclops', name:'Cyclops', cls:'bomb', unlock:0,
   ammoMul:1.0, dmg:80, cd:90, spd:1.5, life:300, homing:true,
   note:'slow and heavy, for hulls that cannot dodge'}
];
function priDef(key){
  for(const w of PRIMARIES) if(w.key===key) return w;
  return PRIMARIES[0];
}
function secDef(key){
  for(const w of SECONDARIES) if(w.key===key) return w;
  return SECONDARIES[0];
}
function curPri(){ return priDef(player.pri); }
function curSec(){ return secDef(player.sec); }
function hullSecCls(key){ return isBomberHull(key) ? 'bomb' : 'missile'; }
// A weapon's name can depend on who is flying it.
function weaponName(w){
  if(w.nameTer && shipFac(player.ship)==='terran') return w.nameTer;
  return w.name;
}
// Unlocks follow the score within a run, the same way the hulls do.
function weaponOpen(w){ return FS1_MODE || score >= (w.unlock||0); }
function secondariesFor(shipKey){
  const c = hullSecCls(shipKey), out = [];
  for(const w of SECONDARIES) if(w.cls===c) out.push(w);
  return out;
}
// The default rack for a hull, used when a switch of hull makes the fitted
// secondary impossible - a bomber cannot carry what a fighter carried.
function defaultSec(shipKey){
  const list = secondariesFor(shipKey);
  return list.length ? list[0].key : SECONDARIES[0].key;
}
// The one place that puts a choice onto the ship. The firing routines read
// the weapon, never the other way round.
function applyLoadout(){
  if(!priDef(player.pri) || curPri().key!==player.pri) player.pri = PRIMARIES[0].key;
  if(curSec().cls !== hullSecCls(player.ship)) player.sec = defaultSec(player.ship);
  player.fR = Math.max(5, Math.round(PLAYER_FR_BASE*curPri().rate));
  const s = shipStats(player.ship);
  player.secType = curSec().cls==='bomb' ? 'bomb' : 'missile';
  player.secMax  = Math.max(1, Math.round((s.sec||0)*curSec().ammoMul));
}
// A refit fills the rack. This is what makes the panel a rearm rather than a
// swap, and it is the whole reason a corvette on the field is worth keeping.
function rearmFull(){
  applyLoadout();
  player.secAmmo = player.secMax;
  player.secTimer = 0;
}
// Newly reached weapons are announced like newly reached hulls, so a
// threshold is something you notice rather than something you find.
const WPN_SEEN = {};
function tickWeaponUnlocks(){
  if(GS!=='playing' || FS1_MODE) return;
  for(const w of PRIMARIES.concat(SECONDARIES)){
    if(!w.unlock || WPN_SEEN[w.key] || score < w.unlock) continue;
    WPN_SEEN[w.key] = true;
    SUB_MSGS.push({x:W/2, y:H*0.40, txt:weaponName(w).toUpperCase()+' AVAILABLE',
                   life:260, ml:260, ally:true});
  }
}
// A rearm comes off an allied corvette, the way a hull comes out of a
// destroyer's hangar. One has to be on the field and finished warping in.
function corvetteOnField(){
  for(const a of allies)
    if(a.type==='corvette' && !a.dead && !a.warpOut && !(a.warp>0)) return true;
  return false;
}
function rearmReady(){
  if(GS!=='playing' || inJump()) return false;
  return corvetteOnField();
}
let rearmMenu = false;
function setRearmMenu(open){
  rearmMenu = open;
  if(open){ shipMenu = false; callMenu = false; }
  syncPause();
  if(open){
    document.body.classList.remove('nocursor');
  } else if(GS==='playing'){
    MOUSE.x = player.x; MOUSE.y = player.y;
    document.body.classList.add('nocursor');
  }
}
function toggleRearmMenu(){
  if(rearmMenu){ setRearmMenu(false); return; }
  if(!rearmReady()) return;
  setRearmMenu(true);
}
// Fitting a weapon. Both kinds go through here so the refill rule lives in
// one place, including the case of choosing what is already fitted.
function fitWeapon(key){
  if(!rearmMenu) return;
  let w = null, kind = '';
  for(const p of PRIMARIES)   if(p.key===key){ w = p; kind = 'pri'; }
  for(const s of SECONDARIES) if(s.key===key){ w = s; kind = 'sec'; }
  if(!w || !weaponOpen(w)) return;
  if(kind==='sec' && w.cls!==hullSecCls(player.ship)) return;
  if(kind==='pri') player.pri = w.key; else player.sec = w.key;
  setRearmMenu(false);
  rearmFull();
  SUB_MSGS.push({x:player.x+60, y:player.y-30, txt:weaponName(w).toUpperCase()+'  REARMED',
                 life:170, ml:170, ally:true});
}

"""

src = replace_once(
    src,
    "// ── HANGAR LAYOUT ────────────────────────────────────────────",
    WEAPONS + "// ── HANGAR LAYOUT ────────────────────────────────────────────",
    "weapon tables",
)

src = replace_once(
    src,
    "    ship:'fiherc',secAmmo:0,secMax:0,secTimer:0,secType:'missile'};",
    "    ship:'fiherc',secAmmo:0,secMax:0,secTimer:0,secType:'missile',\n"
    "    pri:'prometheus',sec:'mx64'};",
    "player fields",
)

# ── 2. The hull hands over to the loadout ────────────────────────────
src = replace_once(
    src,
    "  player.secMax = s.sec;\n"
    "  player.secAmmo= s.sec;\n"
    "  player.secType= isBomberHull(key) ? 'bomb' : 'missile';\n",
    "  // The hull still sets the size of the rack; the weapon scales it. A\n"
    "  // bomber carrying ten and a fighter twenty is part of what tells them\n"
    "  // apart, so that stays a property of the hull.\n"
    "  applyLoadout();\n"
    "  player.secAmmo= player.secMax;\n",
    "applyShip loadout",
)

src = replace_once(
    src,
    "  tickShipUnlocks();",
    "  tickShipUnlocks();\n"
    "  tickWeaponUnlocks();",
    "unlock tick",
)

# ── 3. Firing reads the weapon ───────────────────────────────────────
src = replace_once(
    src,
    "function pShoot(){\n"
    "  const flip=player.flip||false;\n"
    "  const a=player.head||0;      // shots leave along the nose, not the draw angle\n"
    "  const nx=Math.cos(a), ny=Math.sin(a);\n"
    "  const bvx=nx*9, bvy=ny*9;\n"
    "  const pts=mountList(player.ship,player.x,player.y,playerSc(),flip,'primary',player.ang||0);\n"
    "  if(pts&&pts.length){\n"
    "    const d=volleyDmg(pts.length);\n"
    "    for(const p of pts) pBullets.push({x:p.x,y:p.y,vx:bvx,vy:bvy,w:14,h:3,dmg:d});\n"
    "    STATS.shots++;\n"
    "    return;\n"
    "  }",
    "function pShoot(){\n"
    "  const flip=player.flip||false;\n"
    "  const a=player.head||0;      // shots leave along the nose, not the draw angle\n"
    "  const nx=Math.cos(a), ny=Math.sin(a);\n"
    "  // Speed, damage, colour and reach all come off the fitted gun now.\n"
    "  const wp=curPri();\n"
    "  const bvx=nx*wp.spd, bvy=ny*wp.spd;\n"
    "  // range is a distance, the bullet counts steps, so one is turned into\n"
    "  // the other here rather than at every place that makes a bullet.\n"
    "  const life=wp.range ? Math.max(1, Math.round(wp.range/wp.spd)) : 0;\n"
    "  const pts=mountList(player.ship,player.x,player.y,playerSc(),flip,'primary',player.ang||0);\n"
    "  if(pts&&pts.length){\n"
    "    const d=volleyDmg(pts.length)*wp.dmg;\n"
    "    for(const p of pts) pBullets.push({x:p.x,y:p.y,vx:bvx,vy:bvy,w:14,h:3,dmg:d,\n"
    "                                       col:wp.col,glow:wp.glow,pLife:life});\n"
    "    STATS.shots++;\n"
    "    return;\n"
    "  }",
    "pShoot",
)

src = replace_once(
    src,
    "  pBullets.push({x:x+30*nx+4*ny, y:y+30*ny-4*nx, vx:bvx,vy:bvy,w:14,h:3});\n"
    "  pBullets.push({x:x+30*nx-4*ny, y:y+30*ny+4*nx, vx:bvx,vy:bvy,w:14,h:3});",
    "  pBullets.push({x:x+30*nx+4*ny, y:y+30*ny-4*nx, vx:bvx,vy:bvy,w:14,h:3,\n"
    "                 col:wp.col,glow:wp.glow,pLife:life});\n"
    "  pBullets.push({x:x+30*nx-4*ny, y:y+30*ny+4*nx, vx:bvx,vy:bvy,w:14,h:3,\n"
    "                 col:wp.col,glow:wp.glow,pLife:life});",
    "pShoot fallback",
)

src = replace_once(
    src,
    "function fireSecondary(){\n"
    "  if(player.secAmmo<=0||player.secTimer>0) return;\n"
    "  player.secAmmo--;\n"
    "  if(player.secType==='missile'){\n"
    "    player.secTimer=45;\n"
    "    // Rakete: schnell, leichtes Homing\n"
    "    const sp=secMount(), sa=player.head||0;\n"
    "    pBullets.push({x:sp.x,y:sp.y,vx:Math.cos(sa)*3.5,vy:Math.sin(sa)*3.5,\n"
    "      w:18,h:6,sec:true,type:'missile',homing:true,life:220,\n"
    "      target:null,dmg:35});\n"
    "  } else {\n"
    "    player.secTimer=90;\n"
    "    // Bomb: slow, heavy damage\n"
    "    const sp=secMount(), sa=player.head||0;\n"
    "    pBullets.push({x:sp.x,y:sp.y,vx:Math.cos(sa)*1.5,vy:Math.sin(sa)*1.5,\n"
    "      w:16,h:16,sec:true,type:'bomb',homing:true,life:300,\n"
    "      dmg:80});\n"
    "  }\n"
    "}",
    "function fireSecondary(){\n"
    "  if(player.secAmmo<=0||player.secTimer>0) return;\n"
    "  player.secAmmo--;\n"
    "  // One rail for both kinds: what differs is in the table, not here.\n"
    "  const wp=curSec(), bomb=(wp.cls==='bomb');\n"
    "  const sp=secMount(), sa=player.head||0;\n"
    "  player.secTimer=wp.cd;\n"
    "  pBullets.push({x:sp.x, y:sp.y,\n"
    "    vx:Math.cos(sa)*wp.spd, vy:Math.sin(sa)*wp.spd,\n"
    "    w:bomb?16:18, h:bomb?16:6, sec:true,\n"
    "    type:bomb?'bomb':'missile', homing:!!wp.homing, life:wp.life,\n"
    "    target:null, dmg:wp.dmg, wpn:wp.key});\n"
    "}",
    "fireSecondary",
)

# ── 4. A bolt can now run out ────────────────────────────────────────
src = replace_once(
    src,
    "    const b=pBullets[i];b.x+=b.vx; if(b.vy) b.y+=b.vy;\n"
    "    if(debrisEatsBolt(b)){ pBullets.splice(i,1); continue; }",
    "    const b=pBullets[i];b.x+=b.vx; if(b.vy) b.y+=b.vy;\n"
    "    // A gun with a limited reach: the bolt gives out on its own. Without\n"
    "    // pLife it runs to the edge, which is what every bolt used to do.\n"
    "    if(b.pLife){ if(--b.pLife<=0){ pBullets.splice(i,1); continue; } }\n"
    "    if(debrisEatsBolt(b)){ pBullets.splice(i,1); continue; }",
    "bolt range",
)

src = replace_once(
    src,
    "        clr: b.ally ? (b.fac==='vasudan'?'#ffd257':'#7fc4ff') : '#ccff88'});",
    "        clr: b.ally ? (b.fac==='vasudan'?'#ffd257':'#7fc4ff') : (b.col||'#ccff88')});",
    "trail colour",
)

src = replace_once(
    src,
    "      const aGlow = b.ally ? (b.fac==='vasudan'?'rgba(255,200,60,0.32)':'rgba(90,180,255,0.32)')\n"
    "                           : 'rgba(180,255,80,0.3)';\n"
    "      const aCore = b.ally ? (b.fac==='vasudan'?'#ffd257':'#7fc4ff') : '#ccff88';",
    "      const aGlow = b.ally ? (b.fac==='vasudan'?'rgba(255,200,60,0.32)':'rgba(90,180,255,0.32)')\n"
    "                           : (b.glow||'rgba(180,255,80,0.3)');\n"
    "      const aCore = b.ally ? (b.fac==='vasudan'?'#ffd257':'#7fc4ff') : (b.col||'#ccff88');",
    "bolt colour",
)

# ── 5. The panel ─────────────────────────────────────────────────────
PANEL = r"""// ── REARM PANEL ──────────────────────────────────────────────
// Same shape as the hangar, because it is the same kind of decision: a list
// of things you may take, with the figures that let you choose between them.
// Built entirely from the surface kit; nothing here invents a shape.
const RM_W        = 660;
const RM_PAD      = 12;
const RM_ROW      = 38;
const RM_ROW_LOCK = 20;
const RM_GAP      = 4;
const RM_HEAD     = 24;
const RM_TITLE    = 34;
const RM_FOOT     = 18;
const RM_GROUPGAP = 14;
const RM_NUM      = 8;
const RM_NUM_W    = 16;
const RM_NAME     = 30;
// Two kinds of weapon, two sets of columns. Both are measured from the row's
// left edge, and the row is RM_W - 2*RM_PAD wide.
const RM_COLS_PRI = [
  {k:'dmg',   x:300, label:'VOLLEY'},
  {k:'rate',  x:366, label:'ROF'},
  {k:'spd',   x:432, label:'SPEED'},
  {k:'range', x:504, label:'REACH'}
];
const RM_COLS_SEC = [
  {k:'dmg',    x:300, label:'DAMAGE'},
  {k:'ammo',   x:366, label:'RACK'},
  {k:'reload', x:432, label:'RELOAD'},
  {k:'spd',    x:504, label:'SPEED'},
  {k:'seek',   x:566, label:'SEEKING'}
];
// What each column actually says for a weapon. Kept beside the columns so a
// new figure is added in one place rather than two.
function rmValue(w, k, pri){
  if(pri){
    if(k==='dmg')   return String(Math.round(VOLLEY_BASE*w.dmg));
    if(k==='rate')  return (Math.round(600/Math.max(5, Math.round(PLAYER_FR_BASE*w.rate)))/10).toFixed(1)+'/s';
    if(k==='spd')   return String(w.spd);
    if(k==='range') return w.range ? String(w.range) : 'FULL';
    return '';
  }
  if(k==='dmg')    return String(w.dmg);
  if(k==='ammo')   return String(Math.max(1, Math.round((shipStats(player.ship).sec||0)*w.ammoMul)));
  if(k==='reload') return (Math.round(w.cd/6)/10).toFixed(1)+'s';
  if(k==='spd')    return String(w.spd);
  if(k==='seek')   return w.homing ? 'YES' : 'NO';
  return '';
}
function rearmGroups(){
  return [{head:'PRIMARY', pri:true,  cols:RM_COLS_PRI, list:PRIMARIES},
          {head:(hullSecCls(player.ship)==='bomb') ? 'BOMBS' : 'MISSILES',
           pri:false, cols:RM_COLS_SEC, list:secondariesFor(player.ship)}];
}
function rearmLayout(){
  const plan = [];
  let h = RM_TITLE, n = 0;
  for(const g of rearmGroups()){
    if(!g.list.length) continue;
    plan.push({head:g.head, y:h, cols:g.cols});
    h += RM_HEAD;
    for(const w of g.list){
      const open = weaponOpen(w);
      const cur  = g.pri ? (w.key===player.pri) : (w.key===player.sec);
      const rh   = open ? RM_ROW : RM_ROW_LOCK;
      plan.push({w:w, y:h, h:rh, cur:cur, open:open, pri:g.pri, cols:g.cols,
                 num:++n});
      h += rh + RM_GAP;
    }
    h += RM_GROUPGAP;
  }
  h += RM_FOOT;
  return {mx:((W-RM_W)/2)|0, my:((H-h)/2)|0, mw:RM_W, mh:h, plan:plan};
}
function drawRearmMenu(){
  if(!rearmMenu) return;
  const L = rearmLayout(), mx = L.mx, my = L.my, rw = L.mw - RM_PAD*2;
  ctx.save();
  thFrame(mx, my, L.mw, L.mh, RM_TITLE);
  window._rearmPanelRect = {x:mx, y:my, w:L.mw, h:L.mh};

  ctx.textBaseline='middle'; ctx.textAlign='left';
  ctx.fillStyle=TH('textBright'); ctx.font=thLabel(14);
  ctx.fillText('REARM', mx+RM_PAD, my+16);
  ctx.textAlign='right';
  ctx.fillStyle=TH('accentWarm'); ctx.font=thValue(10, false);
  ctx.fillText('CORVETTE ON STATION  -  A REFIT FILLS THE RACK',
               mx+L.mw-RM_PAD, my+16);

  window._rearmRects=[];
  for(const p of L.plan){
    const ry = my+p.y, rx = mx+RM_PAD;
    if(p.head !== undefined){
      ctx.textAlign='left';
      ctx.fillStyle=TH('text'); ctx.font=thLabel(11);
      ctx.fillText(p.head, rx, ry+8);
      ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
      for(const c of p.cols) ctx.fillText(c.label, rx+c.x, ry+9);
      thScale(rx, ry+15, rw, p.cols.map(function(c){ return c.x; }), TH('edgeLight'));
      continue;
    }
    const w = p.w;
    if(!p.open){
      ctx.textAlign='left'; ctx.fillStyle=TH('textDim'); ctx.font=thValue(11, false);
      ctx.fillText(thFit(weaponName(w), 240), rx+RM_NAME, ry+p.h/2);
      ctx.fillText('unlocks at '+w.unlock.toLocaleString('en-US')+' points',
                   rx+p.cols[0].x, ry+p.h/2);
      window._rearmRects.push({x:rx, y:ry, w:rw, h:p.h, key:null});
      continue;
    }

    thPlate(rx, ry, rw, p.h, p.cur ? TH('raised') : TH('panelFront'));
    if(p.cur){
      thGlowPath(rx, ry, rw, p.h, 6, 1);
      thBrackets(rx, ry, rw, p.h, TH('accentWarm'));
      ctx.fillStyle=TH('accentWarm');
      ctx.fillRect(rx, ry+6, 3, p.h-12);
    }
    drawKeyChip(p.num, rx+RM_NUM, ry+(p.h-16)/2, RM_NUM_W, 16, true);

    // Name on top, what it is for underneath. The note is the part that
    // explains a choice the figures alone would not.
    const textW = p.cols[0].x - RM_NAME - 10;
    ctx.textAlign='left';
    ctx.fillStyle = p.cur ? TH('accentWarm') : TH('textBright');
    ctx.font=thValue(14, true);
    ctx.fillText(thFit(weaponName(w), textW), rx+RM_NAME, ry+13);
    ctx.fillStyle=TH('textDim'); ctx.font=thValue(9, false);
    ctx.fillText(thFit(w.note, textW), rx+RM_NAME, ry+27);

    ctx.fillStyle=TH('textBright'); ctx.font=thValue(15, false);
    for(const c of p.cols) ctx.fillText(rmValue(w, c.k, p.pri), rx+c.x, ry+p.h/2);

    window._rearmRects.push({x:rx, y:ry, w:rw, h:p.h, key:w.key});
  }

  ctx.textAlign='center'; ctx.fillStyle=TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText('ESC or tap outside to cancel', mx+L.mw/2, my+L.mh-11);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}
// Three rounds stacked, the way a rack is loaded.
function drawRearmIcon(cx, cy, col){
  ctx.save();
  ctx.fillStyle=col; ctx.strokeStyle=col; ctx.lineWidth=1.2;
  for(let i=-1;i<=1;i++){
    const y = cy + i*4.5;
    ctx.beginPath();
    ctx.moveTo(cx-6, y-1.4);
    ctx.lineTo(cx+3, y-1.4);
    ctx.lineTo(cx+6, y);
    ctx.lineTo(cx+3, y+1.4);
    ctx.lineTo(cx-6, y+1.4);
    ctx.closePath();
    ctx.fill();
  }
  ctx.restore();
}

"""

src = replace_once(
    src,
    "// ── SUPPORT MENU LAYOUT ──────────────────────────────────────",
    PANEL + "// ── SUPPORT MENU LAYOUT ──────────────────────────────────────",
    "rearm panel",
)

src = replace_once(
    src,
    "  try{drawShipMenu();}catch(e){}",
    "  try{drawShipMenu();}catch(e){}\n"
    "  try{drawRearmMenu();}catch(e){}",
    "draw call",
)

# ── 6. The button, beside the ship switch ────────────────────────────
src = replace_once(
    src,
    "  // SHIP SWITCH\n"
    "  if(!FS1_MODE){\n"
    "    var swW=22, swH=H2-8, swX=Math.round((665+W-52)/2-swW/2), swY=4;\n"
    "    var swOn=shipSwapReady()||shipMenu;\n"
    "    thButton(swX, swY, swW, swH, shipMenu?'on':(swOn?'ready':null));\n"
    "    drawSwapIcon(swX+swW/2, swY+swH/2, swOn?TH('accentWarm'):TH('textDim'));\n"
    "    window._shipBtnRect={x:swX, y:swY, w:swW, h:swH};\n"
    "  } else window._shipBtnRect=null;",
    "  // SHIP SWITCH and REARM, as a pair. Two buttons that both open a panel\n"
    "  // over the field belong together, so they are centred as one group in\n"
    "  // the gap between the tickets and the gear.\n"
    "  if(!FS1_MODE){\n"
    "    var swW=22, swH=H2-8, swY=4, swGap=4;\n"
    "    var grpX=Math.round((665+W-52)/2-(swW*2+swGap)/2);\n"
    "    var swX=grpX, rmX=grpX+swW+swGap;\n"
    "    var swOn=shipSwapReady()||shipMenu;\n"
    "    thButton(swX, swY, swW, swH, shipMenu?'on':(swOn?'ready':null));\n"
    "    drawSwapIcon(swX+swW/2, swY+swH/2, swOn?TH('accentWarm'):TH('textDim'));\n"
    "    window._shipBtnRect={x:swX, y:swY, w:swW, h:swH};\n"
    "    var rmOn=rearmReady()||rearmMenu;\n"
    "    thButton(rmX, swY, swW, swH, rearmMenu?'on':(rmOn?'ready':null));\n"
    "    drawRearmIcon(rmX+swW/2, swY+swH/2, rmOn?TH('accentWarm'):TH('textDim'));\n"
    "    window._rearmBtnRect={x:rmX, y:swY, w:swW, h:swH};\n"
    "  } else { window._shipBtnRect=null; window._rearmBtnRect=null; }",
    "bar buttons",
)

# ── 7. Taps and keys ─────────────────────────────────────────────────
src = replace_once(
    src,
    "  if(shipMenu){\n"
    "    for(const r of (window._shipRects||[]))",
    "  if(rearmMenu){\n"
    "    for(const r of (window._rearmRects||[]))\n"
    "      if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){ if(r.key) fitWeapon(r.key); return true; }\n"
    "    if(insidePanel(window._rearmPanelRect, p)) return true;\n"
    "    setRearmMenu(false); return true;\n"
    "  }\n"
    "  if(shipMenu){\n"
    "    for(const r of (window._shipRects||[]))",
    "rearm taps",
)

src = replace_once(
    src,
    "  if(ev.code==='KeyV'){ toggleShipMenu(); ev.preventDefault(); return; }",
    "  if(ev.code==='KeyV'){ toggleShipMenu(); ev.preventDefault(); return; }\n"
    "  if(ev.code==='KeyR'){ toggleRearmMenu(); ev.preventDefault(); return; }\n"
    "  if(rearmMenu){\n"
    "    if(ev.code==='Escape'){ setRearmMenu(false); ev.preventDefault(); return; }\n"
    "    var rd = ev.code.indexOf('Digit')===0 ? ev.code.slice(5)\n"
    "           : (ev.code.indexOf('Numpad')===0 ? ev.code.slice(6) : '');\n"
    "    var ri = parseInt(rd,10);\n"
    "    // The panel numbers its rows straight down, so the digit beside a\n"
    "    // weapon is the digit that fits it.\n"
    "    if(ri>=1){\n"
    "      for(const q of rearmLayout().plan)\n"
    "        if(q.num===ri && q.open){ fitWeapon(q.w.key); break; }\n"
    "      ev.preventDefault();\n"
    "    }\n"
    "    return;\n"
    "  }",
    "rearm keys",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
