#!/usr/bin/env python3
"""FS3 v105 - support and hangar by faction.

- Colossus is a joint GTVA project, not a Terran one: fac:'gtva'.
- Support call list is gated per faction (ALLY_FAC_ON). The Hammer of Light
  cycle is fought on the Vasudan side, so the Terran column is off. The menu
  lays out one column per active faction; the Colossus keeps her own row.
- Hangars are faction bound: a hull may only be taken from a destroyer of
  its own faction. The Colossus serves both. Faction comes from the hull
  key, not from a unit's faction field, because defectors carry 'hol' or
  'renegade' there while still flying a Vasudan hull.
- Colossus on station lifts the once-per-wave limit. The first switch of a
  wave still refits; every further one carries hull, shields and ammo over
  as fractions, so no repair loop.

Reads hlp_shooter_v104_logic.html, writes hlp_shooter_v105_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v104_logic.html", "hlp_shooter_v105_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# ── 1. Colossus faction ──────────────────────────────────────────────
src = replace_once(
    src,
    "  colossus:       {cls:'destroyer', fac:'terran',  spr:'sdcolossus',   label:'GTVA Colossus',",
    "  // Joint Terran and Vasudan project, so she belongs to neither column.\n"
    "  colossus:       {cls:'destroyer', fac:'gtva',    spr:'sdcolossus',   label:'GTVA Colossus',",
    "colossus fac",
)

# ── 2. Which factions answer a support call ──────────────────────────
src = replace_once(
    src,
    "const ALLY_SPECIAL = 'colossus';\nconst ALLY_SPECIAL_KEY = 'C';\n",
    "const ALLY_SPECIAL = 'colossus';\n"
    "const ALLY_SPECIAL_KEY = 'C';\n"
    "// Which support factions answer in the current cycle. The Hammer of Light\n"
    "// cycle is fought on the Vasudan side, so no Terran fleet is on call. A\n"
    "// later cycle switches its own factions back on by setting these.\n"
    "const ALLY_FAC_ON = {terran:false, vasudan:true, gtva:true};\n"
    "function allyFacOn(fac){ return ALLY_FAC_ON[fac] !== false; }\n"
    "// One column per active faction, in ALLY_ORDER order. With a single\n"
    "// faction on call the menu is one column wide instead of leaving a gap.\n"
    "function callCols(){\n"
    "  const cols=[];\n"
    "  for(const fac of ['terran','vasudan']){\n"
    "    if(!allyFacOn(fac)) continue;\n"
    "    const col=[];\n"
    "    for(let i=0;i<ALLY_ORDER.length;i++){\n"
    "      const d=ALLY_DEFS[ALLY_ORDER[i]];\n"
    "      if(d && d.fac===fac) col.push({id:ALLY_ORDER[i], d:d, key:ALLY_KEYS[i]});\n"
    "    }\n"
    "    if(col.length) cols.push(col);\n"
    "  }\n"
    "  return cols;\n"
    "}\n",
    "ALLY_FAC_ON",
)

# ── 3. Gate the call at its single choke point ───────────────────────
src = replace_once(
    src,
    "function callAlly(id){\n  if(!allyReady()) return false;\n  if(!allyAffordable(id)) return false;",
    "function callAlly(id){\n"
    "  if(!allyReady()) return false;\n"
    "  // Gated here rather than in the menu: the key handler and any future\n"
    "  // caller come through this function too.\n"
    "  const cdef = ALLY_DEFS[id];\n"
    "  if(!cdef || !allyFacOn(cdef.fac)) return false;\n"
    "  if(!allyAffordable(id)) return false;",
    "callAlly gate",
)

# ── 4. Call menu layout follows the active factions ──────────────────
src = replace_once(
    src,
    "  const bw=190, bh=38, gap=6, cols=2, rows=ALLY_TER_N;\n"
    "  const mw=bw*cols+gap*(cols+1), mh=bh*rows+gap*(rows+1)+30+bh+gap;",
    "  const COLS=callCols();\n"
    "  const bw=190, bh=38, gap=6, cols=Math.max(1,COLS.length);\n"
    "  let rows=1; for(const c of COLS) rows=Math.max(rows,c.length);\n"
    "  const showCol=allyFacOn(ALLY_DEFS[ALLY_SPECIAL].fac);\n"
    "  const mw=bw*cols+gap*(cols+1), mh=bh*rows+gap*(rows+1)+30+(showCol?bh+gap:0);",
    "call menu size",
)

src = replace_once(
    src,
    "  for(let i=0;i<ALLY_ORDER.length;i++){\n"
    "    const id=ALLY_ORDER[i], d=ALLY_DEFS[id];\n"
    "    // Column major: the whole Terran list first, then the Vasudan one.\n"
    "    const c=i<ALLY_TER_N?0:1, r=i<ALLY_TER_N?i:(i-ALLY_TER_N);\n",
    "  const CELLS=[];\n"
    "  for(let ci=0;ci<COLS.length;ci++)\n"
    "    for(let ri=0;ri<COLS[ci].length;ri++)\n"
    "      CELLS.push({id:COLS[ci][ri].id, d:COLS[ci][ri].d, key:COLS[ci][ri].key, c:ci, r:ri});\n"
    "  for(let i=0;i<CELLS.length;i++){\n"
    "    const id=CELLS[i].id, d=CELLS[i].d;\n"
    "    // One column per faction, filled top down.\n"
    "    const c=CELLS[i].c, r=CELLS[i].r;\n",
    "call menu cells",
)

src = replace_once(
    src,
    "    ctx.fillText('['+ALLY_KEYS[i]+']', bx+7, by+7);",
    "    ctx.fillText('['+CELLS[i].key+']', bx+7, by+7);",
    "call menu key label",
)

src = replace_once(
    src,
    "  // The Colossus gets her own row across the full width.\n"
    "  {\n"
    "    const cd=ALLY_DEFS[ALLY_SPECIAL];\n"
    "    const cbx=mx+gap, cby=my+30+gap+ALLY_TER_N*(bh+gap);",
    "  // The Colossus gets her own row across the full width.\n"
    "  if(showCol){\n"
    "    const cd=ALLY_DEFS[ALLY_SPECIAL];\n"
    "    const cbx=mx+gap, cby=my+30+gap+rows*(bh+gap);",
    "colossus row",
)

# ── 5. Player hulls carry a faction ──────────────────────────────────
src = replace_once(
    src,
    """const PLAYER_SHIPS = [
  {key:'fitoth',    name:'GVF Thoth',   unlock:0,     spd:3.5, turn:0.17, hp:100, sh:100, sec:20},
  {key:'fihorus',   name:'GVF Horus',   unlock:4000,  spd:3.2, turn:0.17, hp:80,  sh:100, sec:20},
  {key:'boosiris',  name:'GVB Osiris',  unlock:9000,  spd:2.5, turn:0.10, hp:140, sh:100, sec:10},
  {key:'fiserapis', name:'GVF Serapis', unlock:15000, spd:3.5, turn:0.17, hp:80,  sh:70,  sec:20},
  {key:'fiseth',    name:'GVF Seth',    unlock:22000, spd:2.5, turn:0.10, hp:125, sh:130, sec:20},
  {key:'bobakha',   name:'GVB Bakha',   unlock:31000, spd:2.5, turn:0.12, hp:100, sh:100, sec:8},
  {key:'fitauret',  name:'GVF Tauret',  unlock:43000, spd:2.9, turn:0.10, hp:100, sh:130, sec:20},
  {key:'bosekhmet', name:'GVB Sekhmet', unlock:58000, spd:2.5, turn:0.12, hp:140, sh:130, sec:12}
];""",
    """// fac decides which hangar hands the hull out. Only Vasudan hulls exist so
// far; a Terran list is added when a cycle needs one.
const PLAYER_SHIPS = [
  {key:'fitoth',    name:'GVF Thoth',   fac:'vasudan', unlock:0,     spd:3.5, turn:0.17, hp:100, sh:100, sec:20},
  {key:'fihorus',   name:'GVF Horus',   fac:'vasudan', unlock:4000,  spd:3.2, turn:0.17, hp:80,  sh:100, sec:20},
  {key:'boosiris',  name:'GVB Osiris',  fac:'vasudan', unlock:9000,  spd:2.5, turn:0.10, hp:140, sh:100, sec:10},
  {key:'fiserapis', name:'GVF Serapis', fac:'vasudan', unlock:15000, spd:3.5, turn:0.17, hp:80,  sh:70,  sec:20},
  {key:'fiseth',    name:'GVF Seth',    fac:'vasudan', unlock:22000, spd:2.5, turn:0.10, hp:125, sh:130, sec:20},
  {key:'bobakha',   name:'GVB Bakha',   fac:'vasudan', unlock:31000, spd:2.5, turn:0.12, hp:100, sh:100, sec:8},
  {key:'fitauret',  name:'GVF Tauret',  fac:'vasudan', unlock:43000, spd:2.9, turn:0.10, hp:100, sh:130, sec:20},
  {key:'bosekhmet', name:'GVB Sekhmet', fac:'vasudan', unlock:58000, spd:2.5, turn:0.12, hp:140, sh:130, sec:12}
];""",
    "PLAYER_SHIPS fac",
)

# ── 6. Hangar helpers ────────────────────────────────────────────────
src = replace_once(
    src,
    "function isBomberHull(key){ return hullClass(key)==='bo'; }",
    """function isBomberHull(key){ return hullClass(key)==='bo'; }
// Faction of a capital hull, read from the key and not from a unit's faction
// field: a defector carries 'hol' or 'renegade' there while still flying the
// hull it always had, and the hull is what has a hangar.
const HULL_FAC = {
  detyphon:'vasudan', dehatshepsut:'vasudan',
  deorionleft:'terran', deorionright:'terran', dehecate:'terran',
  ntfdeorion:'terran', ntfdehecate:'terran',
  sdcolossus:'gtva'
};
function hullFac(key){ return HULL_FAC[key] || ''; }
function shipFac(key){
  for(const s of PLAYER_SHIPS) if(s.key===key) return s.fac || '';
  return '';
}
// A hangar hands out hulls of its own faction. The Colossus is a joint yard
// and serves both.
function hangarServes(hangarFac, shipFac_){
  return hangarFac==='gtva' || (!!hangarFac && hangarFac===shipFac_);
}
// The Colossus counts as a hangar although her class is sd, no other sd hull
// does, and she is the only one that can be on the allied side anyway.
function isHangarShip(a){
  if(!a || a.small || a.dead || a.warpOut) return false;
  return hullClass(a.img)==='de' || a.img==='sdcolossus';
}
// Every friendly hangar out there right now. Two destroyers of different
// factions both count and their lists add up, rather than one winning.
function hangarFacs(){
  const out=[];
  for(const a of allies){
    if(!isHangarShip(a)) continue;
    const f=hullFac(a.img);
    if(f && out.indexOf(f)<0) out.push(f);
  }
  return out;
}
function colossusOnField(){
  for(const a of allies) if(a.colossus && !a.dead && !a.warpOut) return true;
  return false;
}
// Is this hull on offer from anything currently on the field?
function shipOffered(key){
  const sf=shipFac(key);
  const hf=hangarFacs();
  for(let i=0;i<hf.length;i++) if(hangarServes(hf[i], sf)) return true;
  return false;
}""",
    "hangar helpers",
)

# ── 7. applyShip can carry state over ────────────────────────────────
src = replace_once(
    src,
    "// Puts the player into a hull with everything refilled.\nfunction applyShip(key){",
    "// Puts the player into a hull. Without keep everything is refilled. With\n"
    "// keep - fractions of the old hull, shields and ammo - the state carries\n"
    "// over in proportion, so a half wrecked fighter stays half wrecked on a\n"
    "// tougher hull instead of gaining or losing absolute points.\n"
    "function applyShip(key, keep){",
    "applyShip signature",
)

src = replace_once(
    src,
    "  player.secType= isBomberHull(key) ? 'bomb' : 'missile';\n}",
    "  player.secType= isBomberHull(key) ? 'bomb' : 'missile';\n"
    "  if(keep){\n"
    "    player.hp      = Math.max(1, Math.round(player.maxHp*keep.hp));\n"
    "    player.sh      = Math.min(player.maxSh, Math.round(player.maxSh*keep.sh));\n"
    "    player.secAmmo = Math.min(player.secMax, Math.round(player.secMax*keep.sec));\n"
    "  }\n}",
    "applyShip keep",
)

# ── 8. Readiness: faction, and the Colossus exception ────────────────
src = replace_once(
    src,
    """function shipSwapReady(){
  if(GS!=='playing' || FS1_MODE || inJump()) return false;
  if(shipSwapWave===wave || shipUnlocked<2) return false;
  for(const a of allies)
    if(!a.small && !a.dead && !a.warpOut && hullClass(a.img)==='de') return true;
  return false;
}""",
    """function shipSwapReady(){
  if(GS!=='playing' || FS1_MODE || inJump()) return false;
  if(shipUnlocked<2) return false;
  // One switch per wave, except while the Colossus is on station: her yard
  // stays open, and only the first switch of a wave refits.
  if(shipSwapWave===wave && !colossusOnField()) return false;
  // Something other than the active hull has to be unlocked AND on offer
  // from a hangar that is actually on the field.
  for(let i=0;i<shipUnlocked && i<PLAYER_SHIPS.length;i++){
    const s=PLAYER_SHIPS[i];
    if(s.key!==player.ship && shipOffered(s.key)) return true;
  }
  return false;
}""",
    "shipSwapReady",
)

# ── 9. The switch itself ─────────────────────────────────────────────
src = replace_once(
    src,
    """function swapShip(key){
  if(!shipMenu || key===player.ship) return;
  const i = PLAYER_SHIPS.findIndex(function(s){return s.key===key;});
  if(i<0 || i>=shipUnlocked) return;
  setShipMenu(false);
  applyShip(key);
  shipSwapWave = wave;
  SUB_MSGS.push({x:player.x+60, y:player.y-30, txt:PLAYER_SHIPS[i].name.toUpperCase(),
                 life:170, ml:170, ally:true});
}""",
    """function swapShip(key){
  if(!shipMenu || key===player.ship) return;
  const i = PLAYER_SHIPS.findIndex(function(s){return s.key===key;});
  if(i<0 || i>=shipUnlocked) return;
  if(!shipOffered(key)) return;
  // The first switch of a wave arrives fresh. A further one is only reachable
  // at the Colossus and carries the current state over in proportion, so the
  // open yard cannot be used as a repair bay.
  const again = (shipSwapWave===wave);
  const keep  = again ? {hp:  player.maxHp>0  ? player.hp/player.maxHp       : 1,
                         sh:  player.maxSh>0  ? player.sh/player.maxSh       : 0,
                         sec: player.secMax>0 ? player.secAmmo/player.secMax : 0} : null;
  setShipMenu(false);
  applyShip(key, keep);
  shipSwapWave = wave;
  SUB_MSGS.push({x:player.x+60, y:player.y-30,
                 txt:PLAYER_SHIPS[i].name.toUpperCase()+(again?'  NO REFIT':''),
                 life:170, ml:170, ally:true});
}""",
    "swapShip",
)

# ── 10. Menu: heading and the unavailable reason ─────────────────────
src = replace_once(
    src,
    "  ctx.fillText('SWITCH SHIP  -  ONCE PER WAVE', mx+mw/2, my+9);",
    "  ctx.fillText(colossusOnField() ? 'SWITCH SHIP  -  COLOSSUS HANGAR OPEN'\n"
    "                                 : 'SWITCH SHIP  -  ONCE PER WAVE', mx+mw/2, my+9);",
    "menu heading",
)

src = replace_once(
    src,
    "    const s=PLAYER_SHIPS[i], open=i<shipUnlocked, cur=s.key===player.ship;",
    "    const s=PLAYER_SHIPS[i], cur=s.key===player.ship;\n"
    "    // Unlocked, but no hangar of its faction on the field: shown with a\n"
    "    // reason instead of a score threshold, and not takeable.\n"
    "    const off  = (i<shipUnlocked) && !cur && !shipOffered(s.key);\n"
    "    const open = (i<shipUnlocked) && !off;",
    "menu cell state",
)

src = replace_once(
    src,
    "      ctx.fillText('UNLOCKS AT '+s.unlock.toLocaleString('en-US')+' POINTS', bx+30, by+25);",
    "      ctx.fillText(off ? 'NO '+(s.fac||'').toUpperCase()+' HANGAR ON THE FIELD'\n"
    "                       : 'UNLOCKS AT '+s.unlock.toLocaleString('en-US')+' POINTS', bx+30, by+25);",
    "menu locked reason",
)

# ── Names that must be gone or present ───────────────────────────────
for name in ("ALLY_TER_N?0:1",):
    if name in src:
        sys.exit("Abbruch: alte Spaltenrechnung '%s' noch vorhanden." % name)
for name in ("ALLY_FAC_ON", "hangarFacs", "colossusOnField", "shipOffered", "HULL_FAC"):
    if name not in src:
        sys.exit("Abbruch: '%s' fehlt im Ergebnis." % name)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
