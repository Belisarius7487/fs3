#!/usr/bin/env python3
"""FS3 v129 - the NTF cycle begins: missions 31 to 36.

WHAT CHANGES

1. Cycles. A run is made of cycles of written missions, and each cycle brings
   its own fleet. From wave 31 the player flies Terran hulls: the run switches
   into a GTF Myrmidon, and the Terran roster opens by the points scored since
   the cycle began (Myrmidon, Hercules, Artemis, Hercules Mk II, Medusa,
   Erinyes, Ursa, Ares). The support call switches sides with it: Terran
   column on, Vasudan column off. PLAYER_SHIPS stays the one array everything
   reads; entering a cycle refills it in place.

2. ?m=NN starts the run AT mission NN and carries on from there (it used to
   repeat mission NN forever). The wave counter is NN, so hull growth, the
   cycle and its roster are the ones that mission is really played with.

3. Missions 31-36, as agreed with Silvio:
     31 Der Aufstand      allied Leviathan goes over to the NTF, as the NTF hull
     32 Die Frachtroute   two Poseidons, Medusa bombers with fighter cover
     33 Die Relaisstation a stationary Faustus; reinforcements while it stands
     34 Die Flakwand      two NTF Aeolus; an Orion brings the hangar
     35 Der Ueberlaeufer  an NTF Deimos crossing over, hunted by her own side
     36 Die Iceni         first meeting; short deadline, no way to stop the jump

4. Mechanics those need:
     - a capital ship can change sides (seite). It is rebuilt as an enemy of
       the same class, keeps its place and its share of hull, and flies on
       as the NTF variant of its hull where there is one.
     - a capital that is due to defect cannot be killed before it does
       (the defect lock now covers allies of every size).
     - the Iceni is a scripted unit (c:'ic') with her own deadline (flee),
       optionally without a navigation subsystem (navProof) and without a
       score penalty for getting away (fleeFree).
     - a stationary enemy capital stays where it is put (still + x).
     - noFlak for hulls that should not throw flak (the Faustus).
     - some hulls go up with a far bigger blast (Faustus, gas miners, comm
       node), as the mount data describes them.
     - protected non-combatants take the Terran side outside the Hammer of
       Light cycle.
     - a height given in a mission (y) is kept for enemy capitals too.

5. Fix, affects every cycle: a wing held back at the head of the spawn
   queue held back everything queued behind it, capital ships and
   freighters included (M32: the second Poseidon waited for a fighter wing).

Edits src/30_waves.js, src/40_world.js, src/50_combat.js, src/60_effects.js
and src/70_ui.js in place, and writes the updated checks shipsim.js,
swtest.js and the new fieldsim.js. Run assemble.py afterwards.
"""
import sys


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def load(p):
    return open(p, encoding="utf-8").read()


# Every part is read and patched first and written only at the end, so a
# search text that does not match leaves all files untouched.
wv = load("src/30_waves.js")
wo = load("src/40_world.js")
cb = load("src/50_combat.js")
fx = load("src/60_effects.js")
ui = load("src/70_ui.js")

# ══ 30_waves.js ═════════════════════════════════════════════════════════

# ── Cycles and the Terran roster ─────────────────────────────────────────
wv = replace_once(
    wv,
    "  {key:'bosekhmet', name:'GVB Sekhmet', fac:'vasudan', unlock:58000, spd:2.5, turn:0.12, hp:140, sh:130, sec:12}\n"
    "];\n",
    "  {key:'bosekhmet', name:'GVB Sekhmet', fac:'vasudan', unlock:58000, spd:2.5, turn:0.12, hp:140, sh:130, sec:12}\n"
    "];\n"
    "\n"
    "// ── CYCLES ───────────────────────────────────────────────────\n"
    "// A run is made of cycles of written missions, and each cycle brings its\n"
    "// own fleet: the hulls the player flies, the order they open in, and who\n"
    "// answers a support call. PLAYER_SHIPS above is the Hammer of Light roster\n"
    "// and stays the one array everything reads - entering a cycle refills it\n"
    "// in place, so no reader has to know that cycles exist.\n"
    "//\n"
    "// Inside a cycle, unlock counts the points scored SINCE the cycle began.\n"
    "// Every cycle opens its roster from the bottom, whatever the run brought\n"
    "// into it.\n"
    "const ROSTER_HOL = PLAYER_SHIPS.slice();\n"
    "const ROSTER_NTF = [\n"
    "  {key:'fimyrmidon', name:'GTF Myrmidon',      fac:'terran', unlock:0,     spd:3.4, turn:0.16, hp:100, sh:100, sec:20},\n"
    "  {key:'fiherc',     name:'GTF Hercules',      fac:'terran', unlock:4000,  spd:3.0, turn:0.14, hp:120, sh:110, sec:20},\n"
    "  {key:'boartemis',  name:'GTB Artemis',       fac:'terran', unlock:9000,  spd:2.6, turn:0.11, hp:130, sh:100, sec:10},\n"
    "  {key:'fihercmk2',  name:'GTF Hercules Mk II',fac:'terran', unlock:15000, spd:3.2, turn:0.16, hp:110, sh:120, sec:20},\n"
    "  {key:'bomedusa',   name:'GTB Medusa',        fac:'terran', unlock:22000, spd:2.4, turn:0.10, hp:150, sh:110, sec:12},\n"
    "  {key:'fierinyes',  name:'GTF Erinyes',       fac:'terran', unlock:31000, spd:2.8, turn:0.12, hp:130, sh:140, sec:20},\n"
    "  {key:'boursa',     name:'GTB Ursa',          fac:'terran', unlock:43000, spd:2.3, turn:0.10, hp:170, sh:130, sec:14},\n"
    "  {key:'fiares',     name:'GTF Ares',          fac:'terran', unlock:58000, spd:3.3, turn:0.15, hp:120, sh:140, sec:20}\n"
    "];\n"
    "// first: the first wave of the cycle. call: which support columns answer.\n"
    "const CYCLES = [\n"
    "  {first:1,  roster:ROSTER_HOL, call:{terran:false, vasudan:true}},\n"
    "  {first:31, roster:ROSTER_NTF, call:{terran:true,  vasudan:false}}\n"
    "];\n"
    "let cycleNow  = null;   // the CYCLES entry the run is in\n"
    "let cycleBase = 0;      // score when it began; hull unlocks count from here\n"
    "function cycleAt(n){\n"
    "  let c = CYCLES[0];\n"
    "  for(const x of CYCLES) if(n >= x.first) c = x;\n"
    "  return c;\n"
    "}\n"
    "// Puts the run into a cycle: its roster, its support columns, and its\n"
    "// first hull, fresh. The hull the player had belongs to the old fleet.\n"
    "function enterCycle(c){\n"
    "  cycleNow  = c;\n"
    "  cycleBase = score;\n"
    "  PLAYER_SHIPS.length = 0;\n"
    "  for(const s of c.roster) PLAYER_SHIPS.push(s);\n"
    "  for(const k in c.call) ALLY_FAC_ON[k] = c.call[k];\n"
    "  shipUnlocked = Math.max(1, Math.min(UI_SHIPS, PLAYER_SHIPS.length));\n"
    "  shipSwapWave = -1;\n"
    "  applyShip(PLAYER_SHIPS[0].key);\n"
    "}\n",
    "cycles")

# ── ?m=NN starts the run there; the generator is set up on the first wave ─
wv = replace_once(
    wv,
    "  // Geschriebene Welle, falls vorhanden. Mit ?m=3 laesst sich eine\n"
    "  // einzelne zum Pruefen anspringen; ohne den Parameter laufen sie der\n"
    "  // Reihe nach und der Wuerfel uebernimmt erst danach.\n"
    "  {\n"
    "    const sk = SCRIPT_ONE ? SCRIPT_ONE : n;\n"
    "    const def = SCRIPT_WAVES[sk];\n"
    "    if(def) return buildScripted(def);\n"
    "  }\n"
    "\n"
    "  if(n===1){ lastBossWave = 0; rollNextBoss(SEQ_LEN); lastK=''; lastO=''; }\n",
    "  // Written mission, if there is one for this wave. ?m=36 starts the run\n"
    "  // at wave 36 (see launchGame) and it carries on from there; the dice\n"
    "  // take over after the last written one.\n"
    "  {\n"
    "    const def = SCRIPT_WAVES[n];\n"
    "    if(def) return buildScripted(def);\n"
    "  }\n"
    "\n"
    "  // The generator is set up on the first wave the run actually plays,\n"
    "  // which is not wave 1 when ?m= starts it further in.\n"
    "  if(n===1 || n===SCRIPT_ONE){ lastBossWave = 0; rollNextBoss(Math.max(SEQ_LEN, n));\n"
    "                              lastK=''; lastO=''; }\n",
    "getWaveDef")

# ── Categories: the Iceni, and the NTF Deimos on the friendly side ──────
wv = replace_once(
    wv,
    "  codeimos:'ter_deimos', deorionright:'ter_orion', dehecate:'ter_hecate'\n"
    "};\n",
    "  codeimos:'ter_deimos', deorionright:'ter_orion', dehecate:'ter_hecate',\n"
    "  ntfcodeimos:'ntf_deimos'\n"
    "};\n"
    "// The NTF variant of a Terran capital hull. A ship that goes over to the\n"
    "// NTF flies on as this: same class, same size, NTF markings.\n"
    "const NTF_HULL = {\n"
    "  crleviathan:'ntfcrleviathan', crfenris:'ntfcrfenris', craeolus:'ntfcraeolus',\n"
    "  codeimos:'ntfcodeimos', deorionright:'ntfdeorion', deorionleft:'ntfdeorion',\n"
    "  dehecate:'ntfdehecate'\n"
    "};\n",
    "ALLY_ID")

wv = replace_once(
    wv,
    "const CAT_FIX = {sg:'sentry', fc:'container', fr:'freighter', tr:'freighter',\n"
    "                 ast:'ast', ep:'container'};\n",
    "const CAT_FIX = {sg:'sentry', fc:'container', fr:'freighter', tr:'freighter',\n"
    "                 ast:'ast', ep:'container', ic:'iceni'};\n",
    "CAT_FIX")

# The Iceni is one ship with her own spawn path in mkEnemy. She warps in like
# any capital, which the fixed categories below do not do.
wv = replace_once(
    wv,
    "  const fix = CAT_FIX[u.c];\n"
    "  if(!fix) return;                     // Klasse noch nicht spawnbar\n",
    "  if(u.c==='ic'){\n"
    "    // flee: seconds until she jumps. navProof: no navigation subsystem,\n"
    "    // so the jump cannot be stopped. fleeFree: her escape costs nothing.\n"
    "    put({time:t0, type:'iceni', spr:'coiceni',\n"
    "         y:(u.y!=null) ? u.y : H*0.5, x:u.x,\n"
    "         flee:u.flee, navProof:u.navProof, fleeFree:u.fleeFree});\n"
    "    return;\n"
    "  }\n"
    "  const fix = CAT_FIX[u.c];\n"
    "  if(!fix) return;                     // Klasse noch nicht spawnbar\n",
    "scriptUnit: iceni")

wv = replace_once(
    wv,
    "      put({time:t0+i*70, type:'protect', spr:u.spr, fac:'vasudan', noWarp:1,\n",
    "      put({time:t0+i*70, type:'protect', spr:u.spr,\n"
    "           fac:(fac==='hol') ? 'vasudan' : 'terran', noWarp:1,\n",
    "scriptUnit: protect side")

wv = replace_once(
    wv,
    "             x:u.x, escape:u.escape, invuln:u.invuln, edge:u.edge, capRam:u.capRam,\n"
    "             still:u.still,\n",
    "             x:u.x, escape:u.escape, invuln:u.invuln, edge:u.edge, capRam:u.capRam,\n"
    "             still:u.still, noFlak:u.noFlak, fixY:(u.y!=null),\n",
    "scriptUnit: noFlak")

# ── Spawn options ───────────────────────────────────────────────────────
wv = replace_once(
    wv,
    "  if(sp.disable) e.noFlee = true;\n",
    "  if(sp.disable) e.noFlee = true;\n"
    "  // A stationary ship placed with x stays at x. Without this the station\n"
    "  // drive takes it to the class's usual spot at the right.\n"
    "  if(sp.still && sp.x!=null && !sp.capRam) e.targetX = sp.x;\n"
    "  if(sp.noFlak) e.noFlak = true;\n"
    "  // A jump nobody can stop: there is no navigation subsystem to shoot.\n"
    "  if(sp.navProof && e.subs) e.subs = e.subs.filter(function(s){ return s.id!=='navigation'; });\n"
    "  if(sp.fleeFree) e.fleeFree = true;\n",
    "applySpawnOpts")

wv = replace_once(
    wv,
    "  if(sp.still){\n"
    "    e.vy = 0;\n",
    "  // A height the mission gives is kept. assignStation() picks a free\n"
    "  // lane on its own, which is right for ships that simply arrive. Set\n"
    "  // before still, which pins the ship to whatever height it has.\n"
    "  if(sp.fixY && !sp.capRam){ e.y = sp.y; e.warpY = sp.y; }\n"
    "  if(sp.still){\n"
    "    e.vy = 0;\n",
    "applySpawnOpts: fixY")

# ── Capital ships can change sides ──────────────────────────────────────
wv = replace_once(
    wv,
    "function defect(a){\n"
    "  const _i = allies.indexOf(a);\n",
    "function defect(a){\n"
    "  if(!a.small) return defectCap(a);\n"
    "  const _i = allies.indexOf(a);\n",
    "defect: capital branch")

wv = replace_once(
    wv,
    "// Waagerechte Fahrt eines Schuetzlings. Verlaesst er rechts das Feld, ist\n",
    "// A capital ship going over. The allied object is built for the allied\n"
    "// paths and the enemy paths expect other fields, so rather than convert\n"
    "// it, it is rebuilt as an enemy of the same class exactly the way the\n"
    "// spawn queue builds one. It keeps its place, its share of hull and its\n"
    "// mission id, and in the NTF cycle it flies on as the NTF variant.\n"
    "function defectCap(a){\n"
    "  const spr = (currentFaction==='ntf' && NTF_HULL[a.img]) || a.img;\n"
    "  const e = mkEnemy(hullClass(spr) + '_' + FAC_TAG[currentFaction], spr, a.y);\n"
    "  if(!e) return;\n"
    "  const _i = allies.indexOf(a);\n"
    "  if(_i >= 0) allies.splice(_i, 1);\n"
    "  e.side = 'enemy';\n"
    "  e.x = a.x; e.y = a.y; e.warpX = a.x; e.warpY = a.y;\n"
    "  e.warp = 0; e.warpMax = 1;\n"
    "  e.flip = needsFlip(e.img, true);\n"
    "  initWeapons(e); initSecAmmo(e); initLuciShield(e); initSubsystems(e); assignStation(e);\n"
    "  e.hp = Math.max(1, Math.round(e.maxHp * (a.maxHp ? a.hp/a.maxHp : 1)));\n"
    "  e.uid = a.uid;\n"
    "  enemies.push(e);\n"
    "  SUB_MSGS.push({x:e.x, y:e.y, txt:'TURNING HOSTILE',\n"
    "                 life:200, ml:200, ally:false});\n"
    "}\n"
    "// Waagerechte Fahrt eines Schuetzlings. Verlaesst er rechts das Feld, ist\n",
    "defectCap")

# ── Missions 31 to 36 ───────────────────────────────────────────────────
wv = replace_once(
    wv,
    "       {id:'E1', c:'fi', n:2}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},\n"
    "       {t:'alleZerstoert', a:'V1', w:'nachschub', a2:'aus'}\n"
    "     ]}\n"
    "};\n",
    "       {id:'E1', c:'fi', n:2}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},\n"
    "       {t:'alleZerstoert', a:'V1', w:'nachschub', a2:'aus'}\n"
    "     ]},\n"
    "\n"
    "  // ── NTF CYCLE ─────────────────────────────────────────────\n"
    "  // Waves 31 to 60. The player flies Terran hulls from here on, see\n"
    "  // CYCLES. The thread through the cycle is the Iceni: 36, 47 and 60.\n"
    "\n"
    "  31:{name:'Der Aufstand', fac:'ntf', o:'clear', live:4, u:[\n"
    "       // A patrol with a Leviathan. When the first NTF wing is down, she\n"
    "       // goes over - as the NTF hull - and has to be taken down as well.\n"
    "       // Until then she cannot die: the turn is the point of the mission.\n"
    "       {id:'A1', c:'cr', n:1, spr:'crleviathan', side:'ally'},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'meldung', a2:'GTC Leviathan turning hostile'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A1'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}\n"
    "     ]},\n"
    "\n"
    "  32:{name:'Die Frachtroute', fac:'ntf', o:'protect', live:5, hunt:'F1', u:[\n"
    "       // Two Poseidons cross. Medusa bombers go for them, with fighters\n"
    "       // along to keep the player busy.\n"
    "       {id:'F1', c:'fr', n:2, spr:'frposeidon', side:'ally', cross:0.40, x:-40},\n"
    "       {id:'B1', c:'bo', n:1, spr:'bomedusa'},\n"
    "       {id:'E1', c:'fi', n:1},\n"
    "       {id:'B2', c:'bo', n:1, spr:'bomedusa', wait:true},\n"
    "       {id:'E2', c:'fi', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'B2'},\n"
    "       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'E2'}\n"
    "     ]},\n"
    "\n"
    "  33:{name:'Die Relaisstation', fac:'ntf', o:'clear', live:5, u:[\n"
    "       // A Faustus parked as a relay. While she stands, wings keep coming.\n"
    "       // Weak hull, few guns, no flak - and a big blast when she goes.\n"
    "       {id:'S1', c:'cr', n:1, spr:'scfaustus', still:true, x:560, y:250,\n"
    "        hp:0.6, noFlak:true},\n"
    "       {id:'G1', c:'sg', n:4, spr:'sgcerberus'},\n"
    "       {id:'E1', c:'fi', n:1}\n"
    "     ], ev:[\n"
    "       {t:'sek', a:1, w:'nachschub', a2:'an'},\n"
    "       {t:'zerstoert', a:'S1', w:'nachschub', a2:'aus'}\n"
    "     ]},\n"
    "\n"
    "  34:{name:'Die Flakwand', fac:'ntf', o:'clear', live:5, u:[\n"
    "       // Two NTF Aeolus throwing flak. Once the first wing is down an\n"
    "       // Orion arrives, and with her the hangar: a bomber is the answer.\n"
    "       {id:'K1', c:'cr', n:2, spr:'ntfcraeolus'},\n"
    "       {id:'E1', c:'fi', n:1},\n"
    "       {id:'E2', c:'fi', n:1, wait:true},\n"
    "       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'A1'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'meldung',   a2:'GTD Orion inbound - hangar open'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}\n"
    "     ]},\n"
    "\n"
    "  35:{name:'Der Ueberlaeufer', fac:'ntf', o:'guard', live:5, hunt:'A1',\n"
    "      crossEnds:true, u:[\n"
    "       // An NTF Deimos coming over to the GTVA, still in NTF markings.\n"
    "       // Her own side wants her dead before she is across.\n"
    "       {id:'A1', c:'co', n:1, spr:'ntfcodeimos', side:'ally', crossSecs:55},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'B1', c:'bo', n:1, spr:'boartemis', wait:true},\n"
    "       {id:'E2', c:'fi', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},\n"
    "       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'E2'}\n"
    "     ]},\n"
    "\n"
    "  36:{name:'Die Iceni', fac:'ntf', o:'clear', live:5, u:[\n"
    "       // First meeting. She cannot be had yet: a short deadline and no\n"
    "       // navigation subsystem to stop the jump. Her getting away costs\n"
    "       // nothing - but she comes back heavier, as she always does.\n"
    "       {id:'V1', c:'ic', n:1, flee:25, navProof:true, fleeFree:true},\n"
    "       {id:'K1', c:'cr', n:1, spr:'ntfcrfenris'},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}\n"
    "     ]}\n"
    "};\n",
    "missions 31-36")

# ══ 40_world.js ═════════════════════════════════════════════════════════
wo = replace_once(
    wo,
    "  colossus:       {cls:'destroyer', fac:'gtva',    spr:'sdcolossus',   label:'GTVA Colossus',\n"
    "                   ticket:'colossus', colossus:true}\n"
    "};\n",
    "  colossus:       {cls:'destroyer', fac:'gtva',    spr:'sdcolossus',   label:'GTVA Colossus',\n"
    "                   ticket:'colossus', colossus:true},\n"
    "  // Mission use only, never on the call menu (not in ALLY_ORDER): an NTF\n"
    "  // Deimos coming over, still in NTF markings.\n"
    "  ntf_deimos:     {cls:'corvette',  fac:'terran',  spr:'ntfcodeimos',  label:'NTF Deimos'}\n"
    "};\n",
    "ALLY_DEFS")

wo = replace_once(
    wo,
    "  for(let i=allies.length-1;i>=0;i--){\n"
    "    const a = allies[i];\n"
    "    if(a.hp<=0 && !a.dead){\n",
    "  for(let i=allies.length-1;i>=0;i--){\n"
    "    const a = allies[i];\n"
    "    // An ally that is due to go over cannot die first. Enemy fire on\n"
    "    // allies does not pass through damageEnemy(), so the lock that sits\n"
    "    // there never reached them.\n"
    "    if(a.defectLock){\n"
    "      const dfl = a.maxHp * DISABLE_HULL_FLOOR;\n"
    "      if(a.hp < dfl) a.hp = dfl;\n"
    "    }\n"
    "    if(a.hp<=0 && !a.dead){\n",
    "updateAllies: lock")

wo = replace_once(
    wo,
    "function fleePenalty(e){ return (e && FLEE_PENALTY[e.type]) || 1000; }\n",
    "function fleePenalty(e){\n"
    "  if(e && e.fleeFree) return 0;      // an escape the mission intends\n"
    "  return (e && FLEE_PENALTY[e.type]) || 1000;\n"
    "}\n",
    "fleePenalty")

# ══ 50_combat.js ════════════════════════════════════════════════════════
cb = replace_once(
    cb,
    "function flakHas(e){ return !!FLAK_TYPES[e.type]; }\n",
    "function flakHas(e){ return !!FLAK_TYPES[e.type] && !e.noFlak; }\n",
    "flakHas")

# ══ 60_effects.js ═══════════════════════════════════════════════════════
# A wing held back at the head of the queue used to hold back everything
# behind it as well, capital ships and freighters included - the loop only
# ever looks at the head. The held wing now goes back into time order and
# the loop carries on with whatever else is due.
fx = replace_once(
    fx,
    "        for(const s of spawnQ) if(s.wing===_nx.wing) s.time=spawnT+GATE_RETRY;\n"
    "        break;\n",
    "        for(const s of spawnQ) if(s.wing===_nx.wing) s.time=spawnT+GATE_RETRY;\n"
    "        spawnQ.sort(function(a,b){ return a.time-b.time; });\n"
    "        continue;\n",
    "spawn gate: re-sort")
fx = replace_once(
    fx,
    "        } else { _nx.time=spawnT+LIVE_SMALL_RETRY; }\n"
    "        break;\n",
    "        } else { _nx.time=spawnT+LIVE_SMALL_RETRY; }\n"
    "        spawnQ.sort(function(a,b){ return a.time-b.time; });\n"
    "        continue;\n",
    "spawn cap: re-sort")

fx = replace_once(
    fx,
    "  score=0;lives=LIVES_START;wave=(FS1_MODE?fs1First()-1:0);fc=0;",
    "  score=0;lives=LIVES_START;wave=(FS1_MODE?fs1First()-1:(SCRIPT_ONE?SCRIPT_ONE-1:0));fc=0;",
    "launchGame: start wave")

fx = replace_once(
    fx,
    "          secTimer:0,secType:'missile'};\n"
    "  applyShip(PLAYER_SHIPS[0].key);\n",
    "          secTimer:0,secType:'missile'};\n"
    "  // The cycle of the first wave decides the fleet. FS1 has its own.\n"
    "  if(FS1_MODE || TEST_MODE) applyShip(PLAYER_SHIPS[0].key);\n"
    "  else enterCycle(cycleAt(wave+1));\n",
    "launchGame: cycle")

fx = replace_once(
    fx,
    "function nextWave(){\n"
    "  wave++;waveOver=false;waveCd=0;bossAlive=false;bossSlain=false;\n",
    "function nextWave(){\n"
    "  wave++;waveOver=false;waveCd=0;bossAlive=false;bossSlain=false;\n"
    "  // Crossing into the next cycle hands over the fleet.\n"
    "  if(!FS1_MODE && !TEST_MODE){ const _c = cycleAt(wave); if(_c!==cycleNow) enterCycle(_c); }\n",
    "nextWave: cycle")

fx = replace_once(
    fx,
    "        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;\n"
    "                if(_sp.hpMul) { _a.hp=Math.round(_a.hp*_sp.hpMul); _a.maxHp=Math.max(_a.maxHp,_a.hp); }\n",
    "        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;\n"
    "                _a.defectLock = evWillDefect(_sp.uid);\n"
    "                if(_sp.hpMul) { _a.hp=Math.round(_a.hp*_sp.hpMul); _a.maxHp=Math.max(_a.maxHp,_a.hp); }\n",
    "ally capital: lock")

fx = replace_once(
    fx,
    "  if(src) spawnWreck(src, shipType, x, y);\n",
    "  if(src) spawnWreck(src, shipType, x, y);\n"
    "  // Hulls the mount data calls out for a big blast radius. The class\n"
    "  // profile below still runs; this is the extra wave on top of it.\n"
    "  if(src && BIG_BLAST[src.img]){\n"
    "    const bb = BIG_BLAST[src.img];\n"
    "    spawnShock(x, y, bb.r, bb.force, bb.pct);\n"
    "    addShake(bb.shake, bb.shake*3);\n"
    "  }\n",
    "triggerExpl: big blast")

fx = replace_once(
    fx,
    "function triggerExpl(x, y, shipType, faction, src) {\n",
    "// r: reach of the wave, pct: share of the player's hull it takes at full\n"
    "// strength. A destroyer's own wave is 260 and 0.040 for comparison.\n"
    "const BIG_BLAST = {\n"
    "  scfaustus:  {r:300, force:5.0, pct:0.070, shake:12},\n"
    "  incommnode: {r:320, force:5.2, pct:0.080, shake:14},\n"
    "  gmanuket:   {r:380, force:6.0, pct:0.100, shake:16},\n"
    "  gmrahu:     {r:380, force:6.0, pct:0.100, shake:16},\n"
    "  gmzephyrus: {r:400, force:6.4, pct:0.110, shake:16}\n"
    "};\n"
    "function triggerExpl(x, y, shipType, faction, src) {\n",
    "BIG_BLAST")

# ══ 70_ui.js ════════════════════════════════════════════════════════════
ui = replace_once(
    ui,
    "  while(shipUnlocked < PLAYER_SHIPS.length && score >= PLAYER_SHIPS[shipUnlocked].unlock){\n",
    "  // Counted from the start of the cycle: every cycle opens its own roster.\n"
    "  while(shipUnlocked < PLAYER_SHIPS.length && score-cycleBase >= PLAYER_SHIPS[shipUnlocked].unlock){\n",
    "tickShipUnlocks")

ui = replace_once(
    ui,
    "      ctx.fillText('unlocks at '+s.unlock.toLocaleString('en-US')+' points',\n",
    "      ctx.fillText('unlocks at '+(cycleBase+s.unlock).toLocaleString('en-US')+' points',\n",
    "hangar: unlock text")

open("src/30_waves.js", "w", encoding="utf-8").write(wv)
open("src/40_world.js", "w", encoding="utf-8").write(wo)
open("src/50_combat.js", "w", encoding="utf-8").write(cb)
open("src/60_effects.js", "w", encoding="utf-8").write(fx)
open("src/70_ui.js", "w", encoding="utf-8").write(ui)

# ── Test files ─────────────────────────────────────────────────────────
# The updated checks travel inside the patch, because .js files could not be
# downloaded from the chat. They are written after the source parts, so a
# patch that aborts writes none of them either.
import base64
TEST_FILES = {
    'shipsim.js': (
        'Ly8gU2hpcCBzd2l0Y2ggc2ltdWxhdGlvbi4gUHVsbHMgdGhlIFJFQUwgZnVuY3Rpb25zIG91dCBv'
        'ZiB0aGUgbG9naWMgZmlsZSBhbmQKLy8gcnVucyB0aGVtIGFnYWluc3Qgc3RhbmQtaW5zIGZvciB0'
        'aGUgd29ybGQuIFVzYWdlOiBub2RlIHNoaXBzaW0uanMgPGxvZ2ljLmh0bWw+CmNvbnN0IGZzID0g'
        'cmVxdWlyZSgnZnMnKTsKY29uc3QgaHRtbCA9IGZzLnJlYWRGaWxlU3luYyhwcm9jZXNzLmFyZ3Zb'
        'Ml0sICd1dGY4Jyk7CmNvbnN0IHNyYyA9IGh0bWwubWF0Y2goLzxzY3JpcHRbXj5dKj4oW1xzXFNd'
        'Kik8XC9zY3JpcHQ+LylbMV07CgpmdW5jdGlvbiBibG9ja0VuZChzLCBpKXsKICBpID0gcy5pbmRl'
        'eE9mKCd7JywgaSk7IGxldCBkID0gMDsKICBmb3IoOyBpIDwgcy5sZW5ndGg7IGkrKyl7CiAgICBj'
        'b25zdCBjID0gc1tpXTsKICAgIGlmKGM9PT0iJyJ8fGM9PT0nIid8fGM9PT0nYCcpeyBjb25zdCBx'
        'PWM7IGkrKzsgd2hpbGUoaTxzLmxlbmd0aCAmJiBzW2ldIT09cSl7IGlmKHNbaV09PT0nXFwnKSBp'
        'Kys7IGkrKzsgfSB9CiAgICBlbHNlIGlmKHMuc3RhcnRzV2l0aCgnLy8nLCBpKSkgaSA9IHMuaW5k'
        'ZXhPZignXG4nLCBpKTsKICAgIGVsc2UgaWYocy5zdGFydHNXaXRoKCcvKicsIGkpKSBpID0gcy5p'
        'bmRleE9mKCcqLycsIGkpICsgMTsKICAgIGVsc2UgaWYoYz09PSd7JykgZCsrOwogICAgZWxzZSBp'
        'ZihjPT09J30nKXsgZC0tOyBpZihkPT09MCkgcmV0dXJuIGkrMTsgfQogIH0KICB0aHJvdyBuZXcg'
        'RXJyb3IoJ25vIGJsb2NrIGVuZCcpOwp9CmZ1bmN0aW9uIGZuKG5hbWUpewogIGNvbnN0IGkgPSBz'
        'cmMuaW5kZXhPZignXG5mdW5jdGlvbiAnK25hbWUrJygnKTsKICBpZihpPDApIHRocm93IG5ldyBF'
        'cnJvcignbWlzc2luZyBmdW5jdGlvbiAnK25hbWUpOwogIHJldHVybiBzcmMuc2xpY2UoaSsxLCBi'
        'bG9ja0VuZChzcmMsIGkpKTsKfQpmdW5jdGlvbiBiZXR3ZWVuKHN0YXJ0VGV4dCl7CiAgY29uc3Qg'
        'aSA9IHNyYy5pbmRleE9mKHN0YXJ0VGV4dCk7IGlmKGk8MCkgdGhyb3cgbmV3IEVycm9yKCdtaXNz'
        'aW5nICcrc3RhcnRUZXh0KTsKICBjb25zdCBqID0gc3JjLmluZGV4T2YoJ2Z1bmN0aW9uJywgaSk7'
        'CiAgcmV0dXJuIHNyYy5zbGljZShqLCBibG9ja0VuZChzcmMsIGopKTsKfQpjb25zdCBzaGlwc0Rl'
        'Y2wgPSBzcmMubWF0Y2goL2NvbnN0IFBMQVlFUl9TSElQUyA9IFxbW1xzXFNdKj9cXTsvKVswXTsK'
        'Ly8gVGhlIGN5Y2xlIHRhYmxlcyBhbmQgdGhlIHN1cHBvcnQgY29sdW1ucyB0aGV5IHN3aXRjaC4K'
        'Y29uc3QgY3ljbGVEZWNsID0gc3JjLm1hdGNoKC9jb25zdCBST1NURVJfSE9MW1xzXFNdKj9cbmxl'
        'dCBjeWNsZUJhc2UgPSAwO1teXG5dKi8pWzBdOwpjb25zdCBmYWNPbkRlY2wgPSBzcmMubWF0Y2go'
        'L2NvbnN0IEFMTFlfRkFDX09OID0gXHtbXn1dKlx9Oy8pWzBdOwpjb25zdCBodWxsRmFjRGVjbCA9'
        'IHNyYy5tYXRjaCgvY29uc3QgSFVMTF9GQUMgPSBce1tcc1xTXSo/XH07LylbMF07CmNvbnN0IG1l'
        'bnVCZ0RlY2wgPSBzcmMubWF0Y2goL2NvbnN0IE1FTlVfQkdfQUxQSEFbXHNcU10qP2NvbnN0IE1F'
        'TlVfQkdfUEFEXHMqPVxzKltcZC5dKzsvKVswXTsKY29uc3QgaGFuZ2FyRGVjbCA9IHNyYy5tYXRj'
        'aCgvY29uc3QgSEdfV1tcc1xTXSo/XG5cXTsvKVswXTsKY29uc3QgdGhlbWVzRGVjbCA9IHNyYy5t'
        'YXRjaCgvY29uc3QgVEhFTUVTID0gXHtbXHNcU10qP1xuXH07LylbMF07Ci8vIFRoZSB3ZWFwb24g'
        'dGFibGVzIGFuZCB0aGUgcmVhcm0gcGFuZWwncyBtZWFzdXJlbWVudHMuCmNvbnN0IHdwbkRlY2wg'
        'ID0gc3JjLm1hdGNoKC9jb25zdCBQTEFZRVJfRlJfQkFTRVtcc1xTXSo/XG5cXTsvKVswXTsKY29u'
        'c3Qgd3BuRGVjbDIgPSBzcmMubWF0Y2goL2NvbnN0IFNFQ09OREFSSUVTID0gXFtbXHNcU10qP1xu'
        'XF07LylbMF07CmNvbnN0IHJtRGVjbCAgID0gc3JjLm1hdGNoKC9jb25zdCBSTV9XW1xzXFNdKj9j'
        'b25zdCBSTV9DT0xTX1NFQyA9IFxbW1xzXFNdKj9cblxdOy8pWzBdOwovLyBwb2ludGVyQ29uc3Vt'
        'ZWQgcmVhY2hlcyBmb3IgdGhlIHRpdGxlIG9uIGEgZmluaXNoZWQgcnVuLiBTdGFydGluZyBhIHJ1'
        'bgovLyBpcyBub3Qgd2hhdCB0aGVzZSBmaWxlcyB0ZXN0LCBzbyBpdCBpcyBhIHN0dWIuCmNvbnN0'
        'IHdwblN0YXRlID0gJ2xldCByZWFybU1lbnUgPSBmYWxzZTsgbGV0IHJlc3VtZUhvbGQgPSBmYWxz'
        'ZTsnCiAgLy8gVGhlIGJhciBhc2tzIHdoZXJlIHRoZSBwb2ludGVyIGlzIHNpdHRpbmc7IG5vdGhp'
        'bmcgaG92ZXJzIGluIGEgdGVzdC4KICArICcgY29uc3QgSE9WRVIgPSB7eDotMSwgeTotMX07IGZ1'
        'bmN0aW9uIHRvVGl0bGVPckxhdW5jaCgpe307IGNvbnN0IFdQTl9TRUVOID0ge307IGNvbnN0IFVJ'
        'X1dFQVBPTlMgPSBmYWxzZTsnOwoKY29uc3Qgdm9sbGV5RGVjbCA9IHNyYy5tYXRjaCgvY29uc3Qg'
        'Vk9MTEVZX0JBU0VbXHNcU10qP2NvbnN0IFZPTExFWV9QRVJfRVhUUkFccyo9XHMqW1xkLl0rOy8p'
        'WzBdOwpjb25zdCBuYW1lcyA9IFsKICAnc3luY0N1cnNvcicsJ2hvdmVyaW5nJywKICAncGFuZWxP'
        'cGVuJywnaG9sZFJlc3VtZScsJ2NsZWFyUmVzdW1lSG9sZCcsJ2RyYXdSZXN1bWVIaW50JywKICAn'
        'YXBwbHlMb2Fkb3V0JywncmVhcm1GdWxsJywnY3VyUHJpJywnY3VyU2VjJywncHJpRGVmJywnc2Vj'
        'RGVmJywnaHVsbFNlY0NscycsCiAgJ3dlYXBvbk5hbWUnLCd3ZWFwb25PcGVuJywnc2Vjb25kYXJp'
        'ZXNGb3InLCdkZWZhdWx0U2VjJywnY29ydmV0dGVPbkZpZWxkJywKICAncmVhcm1SZWFkeScsJ3Nl'
        'dFJlYXJtTWVudScsJ3RvZ2dsZVJlYXJtTWVudScsJ2ZpdFdlYXBvbicsJ3JlYXJtTGF5b3V0JywK'
        'ICAnZHJhd1JlYXJtTWVudScsJ2RyYXdSZWFybUljb24nLCdyZWFybUdyb3VwcycsJ3JtVmFsdWUn'
        'LCd0aWNrV2VhcG9uVW5sb2NrcycsCiAgJ3RoRml0JywnY2FsbE1lbnVMYXlvdXQnLCdkcmF3QWxs'
        'eVJvdycsJ2RyYXdLZXlDaGlwJywnZHJhd0h1bGxDZWxsJywnaHVsbENsYXNzJywnaXNCb21iZXJI'
        'dWxsJywnc2hpcFN0YXRzJywnYXBwbHlTaGlwJywndGlja1NoaXBVbmxvY2tzJywnc2hpcFN3YXBS'
        'ZWFkeScsCiAgJ3NldFNoaXBNZW51JywndG9nZ2xlU2hpcE1lbnUnLCdzd2FwU2hpcCcsJ2RyYXdT'
        'd2FwSWNvbicsJ3N0YXRQaXBzJywnZHJhd1NoaXBNZW51JywncG9pbnRlckNvbnN1bWVkJywKICAn'
        'cmVzZXRQbGF5ZXJTaGllbGQnLCdwbGF5ZXJTYycsJ3NldENhbGxNZW51JywKICAnaHVsbEZhYycs'
        'J3NoaXBGYWMnLCdoYW5nYXJTZXJ2ZXMnLCdpc0hhbmdhclNoaXAnLCdoYW5nYXJGYWNzJywnY29s'
        'b3NzdXNPbkZpZWxkJywnc2hpcE9mZmVyZWQnLAogICdtb3VudHNGb3InLCdzcHJpdGVGYWNpbmcn'
        'LCdkcmF3SHVsbEJnJywnZHJhd0h1bGxDZWxsJywndm9sbGV5RG1nJywndm9sbGV5VG90YWwnLCdw'
        'cmltYXJ5Q291bnQnLCdzeW5jUGF1c2UnLAogICdoYW5nYXJHcm91cHMnLCdoYW5nYXJMYXlvdXQn'
        'LCdkcmF3TWlzc2lsZUljb24nLCdkcmF3Qm9tYkljb24nLCdkcmF3S2V5Q2hpcCcsCiAgJ2hhbmdh'
        'ck9yZGVyJywnaW5zaWRlUGFuZWwnLCdjeWNsZUF0JywnZW50ZXJDeWNsZScsCiAgJ3RoQ2hhbWZl'
        'clBhdGgnLCd0aFBsYXRlJywndGhHbG93UGF0aCcsJ3RoQnJhY2tldHMnLCd0aFNjYWxlJywndGhG'
        'cmFtZScsJ3RoUkdCQScsJ3RoR2xvc3MnLCd0aEN1dEdsaW50JywKICAnVEgnLCd0aExhYmVsJywn'
        'dGhWYWx1ZScsJ3RoQmV2ZWwnLCd0aEdsb3cnLCd0aFBhbmVsJywndGhCdXR0b24nLCd0aERpdmlk'
        'ZXInLCdkcmF3U3dhcEljb24nLCdVSScsJ3VpSExQJywndWlMYWJlbCcsJ3VpVmFsdWUnLCd1aUNl'
        'bGwnLCd1aURpYWxvZyddOwpjb25zdCBrZXlIYW5kbGVyID0gYmV0d2VlbigiZG9jdW1lbnQuYWRk'
        'RXZlbnRMaXN0ZW5lcigna2V5ZG93bicsZnVuY3Rpb24oZXYpe1xuICBpZihHUyE9PSdwbGF5aW5n'
        'JykgcmV0dXJuOyIpOwpjb25zdCBkb3duU3RhcnQgPSBzcmMuaW5kZXhPZigiQ1ZTLmFkZEV2ZW50'
        'TGlzdGVuZXIoJ21vdXNlZG93bicsIik7CmNvbnN0IG1vdXNlSGFuZGxlciA9IHNyYy5zbGljZShz'
        'cmMuaW5kZXhPZignZnVuY3Rpb24nLCBkb3duU3RhcnQpLCBibG9ja0VuZChzcmMsIHNyYy5pbmRl'
        'eE9mKCdmdW5jdGlvbicsIGRvd25TdGFydCkpKTsKY29uc3QgbGF1bmNoID0gZm4oJ2xhdW5jaEdh'
        'bWUnKTsKCmNvbnN0IENBTExTID0gW107CmNvbnN0IGN0eFN0dWIgPSBuZXcgUHJveHkoe30sIHsK'
        'ICBnZXQ6KHQsayk9PiBrIGluIHQgPyB0W2tdIDogZnVuY3Rpb24oKXsKICAgIENBTExTLnB1c2go'
        'e2ZuOlN0cmluZyhrKSwgYXJnczpbXS5zbGljZS5jYWxsKGFyZ3VtZW50cyl9KTsKICAgIC8vIGNy'
        'ZWF0ZUxpbmVhckdyYWRpZW50IGhhcyB0byBoYW5kIGJhY2sgc29tZXRoaW5nIHdpdGggYWRkQ29s'
        'b3JTdG9wLgogICAgaWYoaz09PSdjcmVhdGVMaW5lYXJHcmFkaWVudCcpIHJldHVybiB7YWRkQ29s'
        'b3JTdG9wOmZ1bmN0aW9uKCl7fX07CiAgICAvLyB0aEZpdCBtZWFzdXJlcyBiZWZvcmUgaXQgY3V0'
        'cywgc28gdGhlIHN0dWIgaGFzIHRvIGFuc3dlciB3aXRoIGEgd2lkdGguCiAgICAvLyBSb3VnaGx5'
        'IDAuNTUgb2YgdGhlIHNldCBwb2ludCBzaXplIHBlciBjaGFyYWN0ZXIgaXMgY2xvc2UgZW5vdWdo'
        'IGZvcgogICAgLy8gdGhlIGxheW91dCBkZWNpc2lvbnMgYmVpbmcgY2hlY2tlZCBoZXJlLgogICAg'
        'aWYoaz09PSdtZWFzdXJlVGV4dCcpewogICAgICBjb25zdCBweCA9IHBhcnNlRmxvYXQoU3RyaW5n'
        'KHQuZm9udHx8JzEwcHgnKS5yZXBsYWNlKC9eYm9sZFxzKy8sJycpKSB8fCAxMDsKICAgICAgcmV0'
        'dXJuIHt3aWR0aDogU3RyaW5nKGFyZ3VtZW50c1swXXx8JycpLmxlbmd0aCAqIHB4ICogMC41NX07'
        'CiAgICB9CiAgfSwKICBzZXQ6KHQsayx2KT0+eyBDQUxMUy5wdXNoKHtmbjonc2V0ICcrU3RyaW5n'
        'KGspLCBhcmdzOlt2XX0pOyB0W2tdPXY7IHJldHVybiB0cnVlOyB9Cn0pOwovLyBIZWxwZXJzIG92'
        'ZXIgdGhlIHJlY29yZGVkIGRyYXdpbmcgY2FsbHMuCmNvbnN0IENMUiAgICA9ICgpPT57IENBTExT'
        'Lmxlbmd0aCA9IDA7IH07CmNvbnN0IGRyYXdzICA9ICgpPT4gQ0FMTFMuZmlsdGVyKGM9PmMuZm49'
        'PT0nZHJhd0ltYWdlJyk7CmNvbnN0IGNsaXBzICA9ICgpPT4gQ0FMTFMuZmlsdGVyKGM9PmMuZm49'
        'PT0nY2xpcCcpOwpjb25zdCBhbHBoYXMgPSAoKT0+IENBTExTLmZpbHRlcihjPT5jLmZuPT09J3Nl'
        'dCBnbG9iYWxBbHBoYScpLm1hcChjPT5jLmFyZ3NbMF0pOwovLyBFdmVyeSBzcHJpdGUgaGFzIHRv'
        'IHNpdCBpbnNpZGUgYSBzYXZlL3Jlc3RvcmUgcGFpciwgb3RoZXJ3aXNlIGl0cyBjbGlwIGFuZAov'
        'LyBpdHMgYWxwaGEgbGVhayBpbnRvIHdoYXRldmVyIGlzIGRyYXduIG5leHQuCmZ1bmN0aW9uIGJh'
        'bGFuY2VkKCl7CiAgbGV0IGQgPSAwLCBva0FsbCA9IHRydWU7CiAgZm9yKGNvbnN0IGMgb2YgQ0FM'
        'TFMpewogICAgaWYoYy5mbj09PSdzYXZlJykgZCsrOwogICAgZWxzZSBpZihjLmZuPT09J3Jlc3Rv'
        'cmUnKXsgZC0tOyBpZihkPDApIG9rQWxsPWZhbHNlOyB9CiAgICBlbHNlIGlmKChjLmZuPT09J2Ry'
        'YXdJbWFnZScgfHwgYy5mbj09PSdjbGlwJykgJiYgZDwxKSBva0FsbD1mYWxzZTsKICB9CiAgcmV0'
        'dXJuIG9rQWxsICYmIGQ9PT0wOwp9Cgpjb25zdCB3b3JsZCA9IGAKICBjb25zdCBXPTgwMCxIPTUw'
        'MCxIVURfSD01NCwgUExBWUVSX1NQRF9GSUdIVEVSPTMuMiwgUExBWUVSX1NQRF9CT01CRVI9Mi40'
        'LCBQTEFZRVJfVFVSTj0wLjE0OwogIGxldCBGUzFfTU9ERT1mYWxzZSwgR1M9J3BsYXlpbmcnLCBw'
        'YXVzZWQ9ZmFsc2UsIGNhbGxNZW51PWZhbHNlLCB3YXZlPTEsIHNjb3JlPTAsIGFsbGllcz1bXSwg'
        'anVtcD1mYWxzZTsKICBsZXQgc2V0dGluZ3NPcGVuPWZhbHNlLCB1c2VyUGF1c2VkPWZhbHNlOwog'
        'IGxldCBTVUJfTVNHUz1bXSwgTU9VU0U9e3g6MCx5OjB9LCBsaXZlcz0zLCBwbGF5ZXI9e3g6MTAw'
        'LHk6MjAwLGh1bGxNdWx0OjF9OwogIGxldCBlcmFPZmY9ZmFsc2UsIElNR1M9e30sIGlzRmlyaW5n'
        'PWZhbHNlLCBsYXVuY2hlZD0wOwogIGNvbnN0IGN0eD1DVFgsIGRvY3VtZW50PXtib2R5OntjbGFz'
        'c0xpc3Q6e2FkZCgpe30scmVtb3ZlKCl7fX19LCBnZXRFbGVtZW50QnlJZCgpe3JldHVybiB7c3R5'
        'bGU6e319O319OwogIGNvbnN0IHdpbmRvdz17fTsKICBmdW5jdGlvbiBpbkp1bXAoKXtyZXR1cm4g'
        'anVtcDt9IGZ1bmN0aW9uIGVyYVNoaWVsZHNPZmYoKXtyZXR1cm4gZXJhT2ZmO30KICBmdW5jdGlv'
        'biBzZXRTZXR0aW5ncygpe30gZnVuY3Rpb24gdG9nZ2xlRnVsbHNjcmVlbigpe30gZnVuY3Rpb24g'
        'cmVmaW5lVGlja2V0KCl7fSBmdW5jdGlvbiBjYWxsQWxseSgpe30KICBmdW5jdGlvbiBhbGx5UmVh'
        'ZHkoKXtyZXR1cm4gdHJ1ZTt9IGZ1bmN0aW9uIHRvZ2dsZUNhbGxNZW51KCl7fSBmdW5jdGlvbiB0'
        'b0dDKHgseSl7cmV0dXJuIHt4OngseTp5fTt9CiAgbGV0IHNoaXBVbmxvY2tlZD0xLCBzaGlwU3dh'
        'cFdhdmU9LTEsIHNoaXBNZW51PWZhbHNlLCBnYW1lT3ZlckF0PTA7CiAgY29uc3QgQUxMWV9LRVlT'
        'PVtdLCBBTExZX09SREVSPVtdLCBBTExZX1NQRUNJQUw9J3gnLCBBTExZX1NQRUNJQUxfS0VZPSdR'
        'JzsKICAke2h1bGxGYWNEZWNsfQogICR7d3BuRGVjbH0KICAke3dwbkRlY2wyfQogICR7cm1EZWNs'
        'fQogICR7d3BuU3RhdGV9CiAgJHt0aGVtZXNEZWNsfQogIGxldCBFQ089e2h1ZDonaGxwJywgc2No'
        'ZW1lOidmaXJlJ307CiAgJHttZW51QmdEZWNsfQogICR7aGFuZ2FyRGVjbH0KICAke3ZvbGxleURl'
        'Y2x9CiAgbGV0IE1PVU5UUz17fTsKICAke3NoaXBzRGVjbH0KICBsZXQgVUlfU0hJUFM9MTsKICAk'
        'e2ZhY09uRGVjbH0KICAke2N5Y2xlRGVjbH0KICAke25hbWVzLm1hcChmbikuam9pbignXG4nKX0K'
        'ICBjb25zdCBvbktleSA9ICR7a2V5SGFuZGxlcn07CiAgY29uc3Qgb25Eb3duID0gJHttb3VzZUhh'
        'bmRsZXJ9OwogIHJldHVybiB7CiAgICBnZXQ6KGspPT5ldmFsKGspLCBzZXQ6KGssdik9PmV2YWwo'
        'aysnPXYnKSwgcnVuOihjb2RlKT0+ZXZhbChjb2RlKQogIH07YDsKY29uc3QgVyA9IG5ldyBGdW5j'
        'dGlvbignQ1RYJywgd29ybGQpKGN0eFN0dWIpOwpsZXQgZmFpbHMgPSAwOwpmdW5jdGlvbiBvayhs'
        'YWJlbCwgY29uZCl7IGNvbnNvbGUubG9nKChjb25kPycgIG9rICAgICc6JyAgRkFJTCAgJykrbGFi'
        'ZWwpOyBpZighY29uZCkgZmFpbHMrKzsgfQpjb25zdCBQID0gKCk9PlcuZ2V0KCdwbGF5ZXInKTsK'
        'Y29uc3QgcmVzZXQgPSAoKT0+eyBXLnJ1bigiR1M9J3BsYXlpbmcnO3BhdXNlZD1mYWxzZTtyZXN1'
        'bWVIb2xkPWZhbHNlO2NhbGxNZW51PWZhbHNlO3NoaXBNZW51PWZhbHNlO3dhdmU9MTtzY29yZT0w'
        'O2FsbGllcz1bXTtqdW1wPWZhbHNlO0ZTMV9NT0RFPWZhbHNlO3NoaXBVbmxvY2tlZD0xO3NoaXBT'
        'd2FwV2F2ZT0tMTtTVUJfTVNHUz1bXTtwbGF5ZXI9e3g6MTAwLHk6MjAwLGh1bGxNdWx0OjF9O2Fw'
        'cGx5U2hpcChQTEFZRVJfU0hJUFNbMF0ua2V5KSIpOyB9Owpjb25zdCBkZXN0cm95ZXIgPSAobyk9'
        'Pk9iamVjdC5hc3NpZ24oe2ltZzonZGVoYXRzaGVwc3V0Jywgc21hbGw6ZmFsc2UsIGRlYWQ6ZmFs'
        'c2UsIHdhcnBPdXQ6ZmFsc2V9LCBvfHx7fSk7Cgpjb25zb2xlLmxvZygnU3RhcnQgc2hpcCcpOwpy'
        'ZXNldCgpOwpvaygnc3RhcnRzIGluIHRoZSBUaG90aCcsIFAoKS5zaGlwPT09J2ZpdG90aCcpOwpv'
        'aygnVGhvdGggc3RhdHMgMy41IC8gMC4xNyAvIDEwMCAvIDEwMCAvIDIwIG1pc3NpbGVzJywgUCgp'
        'LnNwZD09PTMuNSAmJiBQKCkudHVybj09PTAuMTcgJiYgUCgpLm1heEhwPT09MTAwICYmIFAoKS5t'
        'YXhTaD09PTEwMCAmJiBQKCkuc2VjTWF4PT09MjAgJiYgUCgpLnNlY1R5cGU9PT0nbWlzc2lsZScp'
        'OwoKY29uc29sZS5sb2coJ1VubG9ja3MnKTsKcmVzZXQoKTsKVy5ydW4oInNjb3JlPTM5OTk7IHRp'
        'Y2tTaGlwVW5sb2NrcygpIik7IG9rKCczOTk5IHBvaW50czogbm90aGluZyB1bmxvY2tlZCcsIFcu'
        'Z2V0KCdzaGlwVW5sb2NrZWQnKT09PTEpOwpXLnJ1bigic2NvcmU9NDAwMDsgdGlja1NoaXBVbmxv'
        'Y2tzKCkiKTsgb2soJzQwMDAgcG9pbnRzOiBIb3J1cyB1bmxvY2tlZCwgb25lIG1lc3NhZ2UnLCBX'
        'LmdldCgnc2hpcFVubG9ja2VkJyk9PT0yICYmIFcuZ2V0KCdTVUJfTVNHUycpLmxlbmd0aD09PTEg'
        'JiYgL0hPUlVTLy50ZXN0KFcuZ2V0KCdTVUJfTVNHUycpWzBdLnR4dCkpOwpXLnJ1bigic2NvcmU9'
        'MjMwMDA7IHRpY2tTaGlwVW5sb2NrcygpIik7IG9rKCdqdW1wIHRvIDIzMDAwOiBPc2lyaXMsIFNl'
        'cmFwaXMsIFNldGggYXQgb25jZScsIFcuZ2V0KCdzaGlwVW5sb2NrZWQnKT09PTUgJiYgVy5nZXQo'
        'J1NVQl9NU0dTJykubGVuZ3RoPT09NCk7ClcucnVuKCJzY29yZT05OTk5OTk7IHRpY2tTaGlwVW5s'
        'b2NrcygpIik7IG9rKCduZXZlciBwYXN0IHRoZSBlbmQgb2YgdGhlIGxpc3QnLCBXLmdldCgnc2hp'
        'cFVubG9ja2VkJyk9PT04KTsKVy5ydW4oInRpY2tTaGlwVW5sb2NrcygpIik7IG9rKCdzZXZlbiB1'
        'bmxvY2sgbWVzc2FnZXMgaW4gdG90YWwsIG5vbmUgcmVwZWF0ZWQnLCBXLmdldCgnU1VCX01TR1Mn'
        'KS5sZW5ndGg9PT03KTsKcmVzZXQoKTsgVy5ydW4oIkZTMV9NT0RFPXRydWU7IHNjb3JlPTk5OTk5'
        'OyB0aWNrU2hpcFVubG9ja3MoKSIpOyBvaygnRlMxIG1vZGU6IG5vIHVubG9ja3MnLCBXLmdldCgn'
        'c2hpcFVubG9ja2VkJyk9PT0xKTsKcmVzZXQoKTsgVy5ydW4oIkdTPSdnYW1lb3Zlcic7IHNjb3Jl'
        'PTk5OTk5OyB0aWNrU2hpcFVubG9ja3MoKSIpOyBvaygnbm90IG91dHNpZGUgcGxheScsIFcuZ2V0'
        'KCdzaGlwVW5sb2NrZWQnKT09PTEpOwoKY29uc29sZS5sb2coJ1doZW4gdGhlIHN3aXRjaCBpcyBh'
        'dmFpbGFibGUnKTsKY29uc3QgcmVhZHkgPSAoc2V0dXApPT57IHJlc2V0KCk7IFcucnVuKCJzaGlw'
        'VW5sb2NrZWQ9MyIpOyBzZXR1cCgpOyByZXR1cm4gVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpOyB9'
        'Owpvaygnbm8gZGVzdHJveWVyOiBub3QgcmVhZHknLCByZWFkeSgoKT0+e30pPT09ZmFsc2UpOwpv'
        'aygnYWxsaWVkIFZhc3VkYW4gZGVzdHJveWVyOiByZWFkeScsIHJlYWR5KCgpPT5XLnNldCgnYWxs'
        'aWVzJyxbZGVzdHJveWVyKCldKSk9PT10cnVlKTsKb2soJ05URiBodWxsIChudGZkZWhlY2F0ZSkg'
        'aXMgVGVycmFuLCBubyBUZXJyYW4gaHVsbHMgZXhpc3Q6IG5vdCByZWFkeScsCiAgIHJlYWR5KCgp'
        'PT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKHtpbWc6J250ZmRlaGVjYXRlJ30pXSkpPT09ZmFs'
        'c2UpOwpvaygnY3J1aXNlciBvbmx5OiBub3QgcmVhZHknLCByZWFkeSgoKT0+Vy5zZXQoJ2FsbGll'
        'cycsW2Rlc3Ryb3llcih7aW1nOidjcm1lbnR1J30pXSkpPT09ZmFsc2UpOwpvaygnQ29sb3NzdXMg'
        'YWxvbmUgaXMgYSBqb2ludCB5YXJkOiByZWFkeScsCiAgIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVz'
        'JyxbZGVzdHJveWVyKHtpbWc6J3NkY29sb3NzdXMnLCBjb2xvc3N1czp0cnVlfSldKSk9PT10cnVl'
        'KTsKb2soJ2RlYWQgZGVzdHJveWVyOiBub3QgcmVhZHknLCByZWFkeSgoKT0+Vy5zZXQoJ2FsbGll'
        'cycsW2Rlc3Ryb3llcih7ZGVhZDp0cnVlfSldKSk9PT1mYWxzZSk7Cm9rKCdkZXN0cm95ZXIgd2Fy'
        'cGluZyBvdXQ6IG5vdCByZWFkeScsIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVy'
        'KHt3YXJwT3V0OnRydWV9KV0pKT09PWZhbHNlKTsKb2soJ29ubHkgdGhlIHN0YXJ0IHNoaXAgdW5s'
        'b2NrZWQ6IG5vdCByZWFkeScsIHJlYWR5KCgpPT57IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIo'
        'KV0pOyBXLnJ1bignc2hpcFVubG9ja2VkPTEnKTsgfSk9PT1mYWxzZSk7Cm9rKCdkdXJpbmcgYSBq'
        'dW1wOiBub3QgcmVhZHknLCByZWFkeSgoKT0+eyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCld'
        'KTsgVy5ydW4oJ2p1bXA9dHJ1ZScpOyB9KT09PWZhbHNlKTsKb2soJ0ZTMSBtb2RlOiBub3QgcmVh'
        'ZHknLCByZWFkeSgoKT0+eyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ0ZT'
        'MV9NT0RFPXRydWUnKTsgfSk9PT1mYWxzZSk7Cgpjb25zb2xlLmxvZygnU3dpdGNoaW5nJyk7CnJl'
        'c2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MzsgcGxheWVyLmhwPTEyOyBwbGF5ZXIuc2g9NTsg'
        'cGxheWVyLnNlY0FtbW89MSIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKVy5ydW4o'
        'J3RvZ2dsZVNoaXBNZW51KCknKTsgb2soJ2J1dHRvbiBvcGVucyB0aGUgbWVudSBhbmQgcGF1c2Vz'
        'JywgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlICYmIFcuZ2V0KCdwYXVzZWQnKT09PXRydWUpOwpX'
        'LnJ1bigic3dhcFNoaXAoJ2Zpc2VyYXBpcycpIik7IG9rKCdsb2NrZWQgaHVsbCAoU2VyYXBpcykg'
        'cmVmdXNlZCcsIFAoKS5zaGlwPT09J2ZpdG90aCcgJiYgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVl'
        'KTsKVy5ydW4oInN3YXBTaGlwKCdmaXRvdGgnKSIpOyBvaygnY3VycmVudCBodWxsIHJlZnVzZWQn'
        'LCBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUgJiYgVy5nZXQoJ3NoaXBTd2FwV2F2ZScpPT09LTEp'
        'OwpXLnJ1bigic3dhcFNoaXAoJ2Jvb3NpcmlzJykiKTsKLy8gVGhlIHBhbmVsIGNsb3NlcywgYnV0'
        'IHRoZSBnYW1lIHN0YXlzIHN0b3BwZWQ6IGNvbWluZyBiYWNrIGludG8gdGhlCi8vIGZpZ2h0IGlz'
        'IHRoZSBwbGF5ZXIncyB0byB0aW1lIG5vdywgd2hhdGV2ZXIgdGhlIHBhbmVsIGFuZCBob3dldmVy'
        'IGl0Ci8vIHdhcyBsZWZ0LgpvaygnT3NpcmlzIHRha2VuIGFuZCB0aGUgbWVudSBjbG9zZWQnLCBQ'
        'KCkuc2hpcD09PSdib29zaXJpcycgJiYgVy5nZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7Cm9rKCdi'
        'dXQgdGhlIGdhbWUgaXMgc3RpbGwgaGVsZCcsIFcuZ2V0KCdwYXVzZWQnKT09PXRydWUgJiYgVy5n'
        'ZXQoJ3Jlc3VtZUhvbGQnKT09PXRydWUpOwpXLnJ1bigncG9pbnRlckNvbnN1bWVkKHt4OjQwMCx5'
        'OjMwMH0pJyk7Cm9rKCdhbmQgb25lIHRhcCBwdXRzIHlvdSBiYWNrIGluIGl0JywgVy5nZXQoJ3Bh'
        'dXNlZCcpPT09ZmFsc2UgJiYgVy5nZXQoJ3Jlc3VtZUhvbGQnKT09PWZhbHNlKTsKb2soJ09zaXJp'
        'cyBzdGF0cyAyLjUgLyAwLjEwIC8gMTQwIC8gMTAwIC8gMTAgYm9tYnMnLCBQKCkuc3BkPT09Mi41'
        'ICYmIFAoKS50dXJuPT09MC4xMCAmJiBQKCkubWF4SHA9PT0xNDAgJiYgUCgpLm1heFNoPT09MTAw'
        'ICYmIFAoKS5zZWNNYXg9PT0xMCAmJiBQKCkuc2VjVHlwZT09PSdib21iJyk7Cm9rKCdyZWZpbGxl'
        'ZDogaHVsbCAxNDAsIHNoaWVsZHMgMTAwLCAxMCBib21icycsIFAoKS5ocD09PTE0MCAmJiBQKCku'
        'c2g9PT0xMDAgJiYgUCgpLnNlY0FtbW89PT0xMCk7Cm9rKCdzd2l0Y2ggc3BlbnQgZm9yIHRoaXMg'
        'd2F2ZScsIFcucnVuKCdzaGlwU3dhcFJlYWR5KCknKT09PWZhbHNlKTsKVy5ydW4oJ3RvZ2dsZVNo'
        'aXBNZW51KCknKTsgb2soJ21lbnUgZG9lcyBub3Qgb3BlbiBhZ2FpbiB0aGlzIHdhdmUnLCBXLmdl'
        'dCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKVy5ydW4oJ3dhdmU9MicpOyBvaygnbmV4dCB3YXZlOiBh'
        'dmFpbGFibGUgYWdhaW4nLCBXLnJ1bignc2hpcFN3YXBSZWFkeSgpJyk9PT10cnVlKTsKCmNvbnNv'
        'bGUubG9nKCdDeWNsZSBzY2FsaW5nIGFuZCBzaGllbGRzJyk7CnJlc2V0KCk7IFcucnVuKCJwbGF5'
        'ZXIuaHVsbE11bHQ9MS41OyBzaGlwVW5sb2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJv'
        'eWVyKCldKTsKVy5ydW4oInRvZ2dsZVNoaXBNZW51KCk7IHN3YXBTaGlwKCdib3Nla2htZXQnKSIp'
        'OyBvaygnU2VraG1ldCBhdCBjeWNsZSB4MS41OiBodWxsIDIxMCcsIFAoKS5tYXhIcD09PTIxMCAm'
        'JiBQKCkuaHA9PT0yMTApOwpyZXNldCgpOyBXLnJ1bigiZXJhT2ZmPXRydWU7IHNoaXBVbmxvY2tl'
        'ZD0yIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1l'
        'bnUoKTsgc3dhcFNoaXAoJ2ZpaG9ydXMnKSIpOyBvaygnZXJhIHdpdGhvdXQgc2hpZWxkczogc2hp'
        'ZWxkcyBzdGF5IDAnLCBQKCkuc2g9PT0wICYmIFAoKS5tYXhTaD09PTEwMCk7ClcucnVuKCdlcmFP'
        'ZmY9ZmFsc2UnKTsKCmNvbnNvbGUubG9nKCdDYWxsIG1lbnUgYW5kIHN3aXRjaCBtZW51IGV4Y2x1'
        'ZGUgZWFjaCBvdGhlcicpOwpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTI7IGNhbGxNZW51'
        'PXRydWU7IHBhdXNlZD10cnVlIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOwpXLnJ1'
        'bigndG9nZ2xlU2hpcE1lbnUoKScpOyBvaygnb3BlbmluZyB0aGUgc3dpdGNoIGNsb3NlcyB0aGUg'
        'Y2FsbCBtZW51JywgVy5nZXQoJ2NhbGxNZW51Jyk9PT1mYWxzZSAmJiBXLmdldCgnc2hpcE1lbnUn'
        'KT09PXRydWUpOwoKY29uc29sZS5sb2coJ01lbnUgZHJhd2luZyBhbmQgdGFwcycpOwpyZXNldCgp'
        'OyBXLnJ1bigic2hpcFVubG9ja2VkPTMiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7'
        'IFcucnVuKCd0b2dnbGVTaGlwTWVudSgpOyBkcmF3U2hpcE1lbnUoKScpOwpjb25zdCByZWN0cyA9'
        'IFcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycpOwpjb25zdCByb3dPZiA9IChrZXkpPT5XLnJ1bign'
        'd2luZG93Ll9zaGlwUmVjdHMnKS5maW5kKHI9PnIuc2hpcD09PWtleSk7Cm9rKCdlaWdodCByb3dz'
        'IGRyYXduJywgcmVjdHMubGVuZ3RoPT09OCk7Cm9rKCdtZW51IGZpdHMgb24gdGhlIDgwMHg1MDAg'
        'ZmllbGQnLCByZWN0cy5ldmVyeShyPT5yLng+PTAgJiYgci55Pj0wICYmIHIueCtyLnc8PTgwMCAm'
        'JiByLnkrci5oPD01MDApKTsKb2soJ2ZpZ2h0ZXJzIGZpcnN0LCB0aGVuIGJvbWJlcnMnLAogICBy'
        'ZWN0cy5tYXAocj0+ci5zaGlwKS5qb2luKCk9PT0nZml0b3RoLGZpaG9ydXMsZmlzZXJhcGlzLGZp'
        'c2V0aCxmaXRhdXJldCxib29zaXJpcyxib2Jha2hhLGJvc2VraG1ldCcpOwpvaygnZXZlcnkgcm93'
        'IGlzIGZ1bGwgd2lkdGggYW5kIHRoZXkgZG8gbm90IG92ZXJsYXAnLAogICByZWN0cy5ldmVyeShy'
        'PT5yLnc9PT1yZWN0c1swXS53KSAmJgogICByZWN0cy5ldmVyeSgocixpKT0+aT09PTAgfHwgci55'
        'ID49IHJlY3RzW2ktMV0ueStyZWN0c1tpLTFdLmgpKTsKb2soJ2EgbG9ja2VkIHJvdyBpcyB0aGlu'
        'bmVyIHRoYW4gb25lIHRoYXQgY2FuIGJlIHRha2VuJywKICAgcm93T2YoJ2JvYmFraGEnKS5oIDwg'
        'cm93T2YoJ2ZpaG9ydXMnKS5oKTsKb2soJ29ubHkgSG9ydXMgYW5kIE9zaXJpcyBhcmUgdGFwcGFi'
        'bGUnLCByZWN0cy5maWx0ZXIocj0+ci5rZXkpLm1hcChyPT5yLmtleSkuam9pbigpPT09J2ZpaG9y'
        'dXMsYm9vc2lyaXMnKTsKY29uc3QgbG9ja2VkID0gcm93T2YoJ2JvYmFraGEnKTsKVy5ydW4oYHBv'
        'aW50ZXJDb25zdW1lZCh7eDoke2xvY2tlZC54KzV9LHk6JHtsb2NrZWQueSs1fX0pYCk7IG9rKCd0'
        'YXAgb24gbG9ja2VkIEJha2hhIGtlZXBzIHRoZSBtZW51IG9wZW4nLCBXLmdldCgnc2hpcE1lbnUn'
        'KT09PXRydWUgJiYgUCgpLnNoaXA9PT0nZml0b3RoJyk7CmNvbnN0IGhvcnVzID0gcm93T2YoJ2Zp'
        'aG9ydXMnKTsKVy5ydW4oYHBvaW50ZXJDb25zdW1lZCh7eDoke2hvcnVzLngrNX0seToke2hvcnVz'
        'LnkrNX19KWApOyBvaygndGFwIG9uIEhvcnVzIHN3aXRjaGVzJywgUCgpLnNoaXA9PT0nZmlob3J1'
        'cycgJiYgVy5nZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5s'
        'b2NrZWQ9MyIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ3RvZ2dsZVNo'
        'aXBNZW51KCknKTsKVy5ydW4oJ3BvaW50ZXJDb25zdW1lZCh7eDoyLHk6Mn0pJyk7IG9rKCd0YXAg'
        'b3V0c2lkZSBjbG9zZXMgd2l0aG91dCBzd2l0Y2hpbmcnLCBXLmdldCgnc2hpcE1lbnUnKT09PWZh'
        'bHNlICYmIFAoKS5zaGlwPT09J2ZpdG90aCcgJiYgVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpPT09'
        'dHJ1ZSk7Cm9rKCdjYW5jZWxsaW5nIGhvbGRzIHRoZSBwYXVzZSBqdXN0IHRoZSBzYW1lJywgVy5n'
        'ZXQoJ3Jlc3VtZUhvbGQnKT09PXRydWUpOwpXLnJ1bignY2xlYXJSZXN1bWVIb2xkKCknKTsKVy5y'
        'dW4oIndpbmRvdy5fc2hpcEJ0blJlY3Q9e3g6Njk1LHk6NCx3OjIyLGg6MjB9OyBwb2ludGVyQ29u'
        'c3VtZWQoe3g6NzAwLHk6MTB9KSIpOyBvaygndGFwIG9uIHRoZSBiYXIgYnV0dG9uIG9wZW5zIHRo'
        'ZSBtZW51JywgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlKTsKCmNvbnNvbGUubG9nKCdUaGUgcGFu'
        'ZWwgc3dhbGxvd3MgaXRzIG93biBjbGlja3MnKTsKewogIHJlc2V0KCk7IFcucnVuKCJzaGlwVW5s'
        'b2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKICBXLnJ1bigndG9nZ2xl'
        'U2hpcE1lbnUoKScpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKICBjb25zdCBwciA9IFcucnVu'
        'KCd3aW5kb3cuX3NoaXBQYW5lbFJlY3QnKTsKICBvaygndGhlIHBhbmVsIHJlcG9ydHMgaXRzIG91'
        'dGxpbmUnLCBwciAmJiBwci53PjAgJiYgcHIuaD4wKTsKICAvLyBUaGUgaGVhZGVyIGxpbmU6IGlu'
        'c2lkZSB0aGUgcGFuZWwsIG9uIG5vIHJvdyBhdCBhbGwuCiAgVy5ydW4oYHBvaW50ZXJDb25zdW1l'
        'ZCh7eDoke3ByLngrNDB9LHk6JHtwci55KzZ9fSlgKTsKICBvaygnYSBjbGljayBvbiB0aGUgaGVh'
        'ZGVyIGtlZXBzIHRoZSBwYW5lbCBvcGVuJywgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlKTsKICAv'
        'LyBBIGdhcCBiZXR3ZWVuIHR3byByb3dzLgogIGNvbnN0IHJzID0gVy5ydW4oJ3dpbmRvdy5fc2hp'
        'cFJlY3RzJyk7CiAgY29uc3QgZ2FwWSA9IHJzWzBdLnkgKyByc1swXS5oICsgMjsKICBXLnJ1bihg'
        'cG9pbnRlckNvbnN1bWVkKHt4OiR7cnNbMF0ueCs0MH0seToke2dhcFl9fSlgKTsKICBvaygnYSBj'
        'bGljayBpbiB0aGUgZ2FwIGJldHdlZW4gcm93cyBrZWVwcyBpdCBvcGVuIHRvbycsIFcuZ2V0KCdz'
        'aGlwTWVudScpPT09dHJ1ZSk7CiAgLy8gVGhlIGZvb3Rlci4KICBXLnJ1bihgcG9pbnRlckNvbnN1'
        'bWVkKHt4OiR7cHIueCtwci53LzJ9LHk6JHtwci55K3ByLmgtNn19KWApOwogIG9rKCdhbmQgb25l'
        'IG9uIHRoZSBmb290ZXInLCBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUpOwogIG9rKCdub25lIG9m'
        'IHRoZW0gc3dpdGNoZWQgdGhlIHNoaXAnLCBQKCkuc2hpcD09PSdmaXRvdGgnKTsKICAvLyBPdXRz'
        'aWRlIHRoZSBvdXRsaW5lIGlzIHN0aWxsIG91dHNpZGUuCiAgVy5ydW4oYHBvaW50ZXJDb25zdW1l'
        'ZCh7eDoke3ByLngtMTJ9LHk6JHtwci55K3ByLmgvMn19KWApOwogIG9rKCdhIGNsaWNrIGJlc2lk'
        'ZSB0aGUgcGFuZWwgY2xvc2VzIGl0JywgVy5nZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7Cn0KCmNv'
        'bnNvbGUubG9nKCdLZXlib2FyZCcpOwpjb25zdCBrZXkgPSAoY29kZSk9PlcucnVuKGBvbktleSh7'
        'Y29kZTonJHtjb2RlfScsIHByZXZlbnREZWZhdWx0KCl7fX0pYCk7CnJlc2V0KCk7IFcucnVuKCJz'
        'aGlwVW5sb2NrZWQ9NCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKa2V5KCdLZXlW'
        'Jyk7IG9rKCdWIG9wZW5zJywgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlKTsKLy8gRm91ciBodWxs'
        'cyBvcGVuOiByb3N0ZXIgMCB0byAzLiBUaGUgZGlnaXRzIGZvbGxvdyB0aGUgcGFuZWwsIHNvIDQg'
        'aXMgdGhlCi8vIFNldGgsIHdoaWNoIGlzIHN0aWxsIGxvY2tlZCwgYW5kIDYgaXMgdGhlIGZpcnN0'
        'IGJvbWJlci4Ka2V5KCdEaWdpdDQnKTsgb2soJzQgKHRoZSBTZXRoLCBub3QgdW5sb2NrZWQgeWV0'
        'KSBkb2VzIG5vdGhpbmcnLAogICAgICAgICAgICAgICAgICBXLmdldCgnc2hpcE1lbnUnKT09PXRy'
        'dWUgJiYgUCgpLnNoaXA9PT0nZml0b3RoJyk7CmtleSgnRGlnaXQ2Jyk7IG9rKCc2IHRha2VzIHRo'
        'ZSBPc2lyaXMsIGZpcnN0IHJvdyBvZiB0aGUgYm9tYmVycycsCiAgICAgICAgICAgICAgICAgIFAo'
        'KS5zaGlwPT09J2Jvb3NpcmlzJyAmJiBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKcmVzZXQo'
        'KTsgVy5ydW4oInNoaXBVbmxvY2tlZD00Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0p'
        'OyBrZXkoJ0tleVYnKTsKa2V5KCdEaWdpdDMnKTsgb2soJzMgdGFrZXMgdGhlIFNlcmFwaXMsIHRo'
        'aXJkIHJvdyBkb3duJywKICAgICAgICAgICAgICAgICAgUCgpLnNoaXA9PT0nZmlzZXJhcGlzJyAm'
        'JiBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tl'
        'ZD00Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBrZXkoJ0tleVYnKTsga2V5KCdF'
        'c2NhcGUnKTsKb2soJ0VzY2FwZSBjbG9zZXMnLCBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsK'
        'b2soJ2FuZCBob2xkcyB0aGUgcGF1c2UsIGxpa2UgZXZlcnkgb3RoZXIgd2F5IG9mIGxlYXZpbmcg'
        'YSBwYW5lbCcsCiAgIFcuZ2V0KCdwYXVzZWQnKT09PXRydWUgJiYgVy5nZXQoJ3Jlc3VtZUhvbGQn'
        'KT09PXRydWUpOwpXLnJ1bignY2xlYXJSZXN1bWVIb2xkKCknKTsKb2soJ2FmdGVyIHRoZSB0YXAg'
        'dGhlIGdhbWUgcnVucyBhZ2FpbicsIFcuZ2V0KCdwYXVzZWQnKT09PWZhbHNlKTsKcmVzZXQoKTsg'
        'a2V5KCdLZXlWJyk7IG9rKCdWIHdpdGhvdXQgYSBkZXN0cm95ZXIgZG9lcyBub3RoaW5nJywgVy5n'
        'ZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7Cgpjb25zb2xlLmxvZygnUmVzdGFydCBndWFyZCcpOwpX'
        'LnJ1bigibGF1bmNoR2FtZT1mdW5jdGlvbigpe2xhdW5jaGVkKyt9Iik7Ci8vIFRoZSB0aXRsZSBh'
        'bmQgdGhlIGdhbWUgb3ZlciBzY3JlZW4gYm90aCBnbyB0aHJvdWdoIHRvVGl0bGVPckxhdW5jaCBu'
        'b3csCi8vIHNvIHRoYXQgaXMgd2hhdCBoYXMgdG8gYmUgaW4gcGxhY2UgZm9yIHRoZSByZXN0YXJ0'
        'IGd1YXJkIHRvIGJlIHRlc3RlZC4KVy5ydW4oInRvVGl0bGVPckxhdW5jaD1mdW5jdGlvbigpeyBp'
        'ZihHUz09PSdnYW1lb3ZlcicpeyBHUz0ndGl0bGUnOyByZXR1cm47IH0gbGF1bmNoR2FtZSgpOyB9'
        'Iik7CmNvbnN0IGRvd24gPSAoKT0+Vy5ydW4oIm9uRG93bih7YnV0dG9uOjAsIGNsaWVudFg6NDAw'
        'LCBjbGllbnRZOjMwMH0pIik7ClcucnVuKCJHUz0ndGl0bGUnOyBsYXVuY2hlZD0wIik7IGRvd24o'
        'KTsgb2soJ3RhcCBvbiB0aXRsZSBzdGFydHMgYXQgb25jZScsIFcuZ2V0KCdsYXVuY2hlZCcpPT09'
        'MSk7ClcucnVuKCJHUz0nZ2FtZW92ZXInOyBnYW1lT3ZlckF0PXBlcmZvcm1hbmNlLm5vdygpOyBs'
        'YXVuY2hlZD0wIik7IGRvd24oKTsgb2soJ3RhcCByaWdodCBhZnRlciBkeWluZyBkb2VzIG5vdCBy'
        'ZXN0YXJ0JywgVy5nZXQoJ2xhdW5jaGVkJyk9PT0wKTsKVy5ydW4oImdhbWVPdmVyQXQ9cGVyZm9y'
        'bWFuY2Uubm93KCktMjAwMCIpOyBkb3duKCk7Cm9rKCd0YXAgYWZ0ZXIgMiBzIGdvZXMgYmFjayB0'
        'byB0aGUgdGl0bGUsIG5vdCBpbnRvIHRoZSBuZXh0IHJ1bicsCiAgIFcuZ2V0KCdsYXVuY2hlZCcp'
        'PT09MCAmJiBXLmdldCgnR1MnKT09PSd0aXRsZScpOwoKCmNvbnNvbGUubG9nKCdIYW5nYXJzIGJ5'
        'IGZhY3Rpb24nKTsKY29uc3QgY29sb3NzdXMgPSAobyk9Pk9iamVjdC5hc3NpZ24oe2ltZzonc2Rj'
        'b2xvc3N1cycsIGNvbG9zc3VzOnRydWUsIHNtYWxsOmZhbHNlLCBkZWFkOmZhbHNlLCB3YXJwT3V0'
        'OmZhbHNlfSwgb3x8e30pOwpvaygnaHVsbCBmYWN0aW9uIGNvbWVzIGZyb20gdGhlIGtleScsIFcu'
        'cnVuKCJodWxsRmFjKCdkZWhhdHNoZXBzdXQnKSIpPT09J3Zhc3VkYW4nCiAgICYmIFcucnVuKCJo'
        'dWxsRmFjKCdkZW9yaW9ucmlnaHQnKSIpPT09J3RlcnJhbicgJiYgVy5ydW4oImh1bGxGYWMoJ3Nk'
        'Y29sb3NzdXMnKSIpPT09J2d0dmEnKTsKb2soJ2EgZGVmZWN0ZWQgSGFtbWVyIG9mIExpZ2h0IFR5'
        'cGhvbiBzdGlsbCBjb3VudHMgYXMgVmFzdWRhbicsCiAgIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVz'
        'JyxbZGVzdHJveWVyKHtpbWc6J2RldHlwaG9uJywgZmFjdGlvbjonaG9sJ30pXSkpPT09dHJ1ZSk7'
        'Cm9rKCdhIHJlbmVnYWRlIEhhdHNoZXBzdXQgdG9vJywKICAgcmVhZHkoKCk9Plcuc2V0KCdhbGxp'
        'ZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVoYXRzaGVwc3V0JywgZmFjdGlvbjoncmVuZWdhZGUnfSld'
        'KSk9PT10cnVlKTsKb2soJ1RlcnJhbiBPcmlvbiBvbmx5OiBub3QgcmVhZHknLCByZWFkeSgoKT0+'
        'Vy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7aW1nOidkZW9yaW9ucmlnaHQnfSldKSk9PT1mYWxz'
        'ZSk7Cm9rKCdUZXJyYW4gSGVjYXRlIG9ubHk6IG5vdCByZWFkeScsIHJlYWR5KCgpPT5XLnNldCgn'
        'YWxsaWVzJyxbZGVzdHJveWVyKHtpbWc6J2RlaGVjYXRlJ30pXSkpPT09ZmFsc2UpOwpvaygnT3Jp'
        'b24gcGx1cyBUeXBob246IHJlYWR5LCB0aGUgbGlzdHMgYWRkIHVwJywKICAgcmVhZHkoKCk9Plcu'
        'c2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVvcmlvbnJpZ2h0J30pLCBkZXN0cm95ZXIo'
        'e2ltZzonZGV0eXBob24nfSldKSk9PT10cnVlKTsKb2soJ3Vua25vd24gY2FwaXRhbCBodWxsOiBu'
        'b3QgcmVhZHknLCByZWFkeSgoKT0+Vy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7aW1nOidkZWRl'
        'bW9uJ30pXSkpPT09ZmFsc2UpOwoKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcu'
        'c2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVvcmlvbnJpZ2h0J30pXSk7Cm9rKCdWYXN1'
        'ZGFuIGh1bGwgbm90IG9mZmVyZWQgYnkgYSBUZXJyYW4gaGFuZ2FyJywgVy5ydW4oInNoaXBPZmZl'
        'cmVkKCdmaWhvcnVzJykiKT09PWZhbHNlKTsKVy5ydW4oInNoaXBNZW51PXRydWU7IHN3YXBTaGlw'
        'KCdmaWhvcnVzJykiKTsKb2soJ2FuZCBhIGZvcmNlZCBzd2l0Y2ggaXMgcmVmdXNlZCcsIFAoKS5z'
        'aGlwPT09J2ZpdG90aCcgJiYgVy5nZXQoJ3NoaXBTd2FwV2F2ZScpPT09LTEpOwpXLnNldCgnYWxs'
        'aWVzJyxbY29sb3NzdXMoKV0pOwpvaygndGhlIENvbG9zc3VzIG9mZmVycyB0aGUgVmFzdWRhbiBo'
        'dWxsJywgVy5ydW4oInNoaXBPZmZlcmVkKCdmaWhvcnVzJykiKT09PXRydWUpOwoKcmVzZXQoKTsg'
        'Vy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzon'
        'ZGVvcmlvbnJpZ2h0J30pXSk7ClcucnVuKCd0b2dnbGVTaGlwTWVudSgpJyk7IG9rKCdUZXJyYW4g'
        'aGFuZ2FyIG9ubHk6IHRoZSBtZW51IHN0YXlzIHNodXQnLCBXLmdldCgnc2hpcE1lbnUnKT09PWZh'
        'bHNlKTsKVy5ydW4oInNoaXBNZW51PXRydWU7IGRyYXdTaGlwTWVudSgpIik7Cm9rKCdubyBjZWxs'
        'IGlzIHRhcHBhYmxlIGluIHRoYXQgc3RhdGUnLCBXLnJ1bignd2luZG93Ll9zaGlwUmVjdHMnKS5l'
        'dmVyeShyPT4hci5rZXkpKTsKCmNvbnNvbGUubG9nKCdDb2xvc3N1cyBsaWZ0cyB0aGUgb25jZSBw'
        'ZXIgd2F2ZSBsaW1pdCcpOwpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTMiKTsgVy5zZXQo'
        'J2FsbGllcycsW2Rlc3Ryb3llcigpXSk7ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBzd2FwU2hp'
        'cCgnZmlob3J1cycpIik7Cm9rKCdmaXJzdCBzd2l0Y2ggb2YgdGhlIHdhdmUgcmVmaXRzJywgUCgp'
        'LnNoaXA9PT0nZmlob3J1cycgJiYgUCgpLmhwPT09ODAgJiYgUCgpLnNoPT09MTAwICYmIFAoKS5z'
        'ZWNBbW1vPT09MjApOwpvaygnbm8gQ29sb3NzdXM6IHNwZW50IGZvciB0aGlzIHdhdmUnLCBXLnJ1'
        'bignc2hpcFN3YXBSZWFkeSgpJyk9PT1mYWxzZSk7Clcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIo'
        'KSwgY29sb3NzdXMoKV0pOwpvaygnQ29sb3NzdXMgYXJyaXZlczogYXZhaWxhYmxlIGFnYWluIGlu'
        'IHRoZSBzYW1lIHdhdmUnLCBXLnJ1bignc2hpcFN3YXBSZWFkeSgpJyk9PT10cnVlKTsKVy5ydW4o'
        'InBsYXllci5ocD00MDsgcGxheWVyLnNoPTUwOyBwbGF5ZXIuc2VjQW1tbz0xMCIpOwpXLnJ1bigi'
        'dG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAoJ2Jvb3NpcmlzJykiKTsKb2soJ3NlY29uZCBzd2l0'
        'Y2ggaGFwcGVucycsIFAoKS5zaGlwPT09J2Jvb3NpcmlzJyk7Cm9rKCdodWxsIGNhcnJpZXMgb3Zl'
        'ciBhcyBhIGZyYWN0aW9uLCA0MC84MCBvZiAxNDAgPSA3MCcsIFAoKS5ocD09PTcwKTsKb2soJ3No'
        'aWVsZHMgY2Fycnkgb3ZlciwgNTAvMTAwIG9mIDEwMCA9IDUwJywgUCgpLnNoPT09NTApOwpvaygn'
        'YW1tbyBjYXJyaWVzIG92ZXIsIDEwLzIwIG9mIDEwIGJvbWJzID0gNScsIFAoKS5zZWNBbW1vPT09'
        'NSk7Cm9rKCdubyByZWZpdDogbm90IGZ1bGwnLCBQKCkuaHA8UCgpLm1heEhwICYmIFAoKS5zZWNB'
        'bW1vPFAoKS5zZWNNYXgpOwoKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcuc2V0'
        'KCdhbGxpZXMnLFtkZXN0cm95ZXIoKSwgY29sb3NzdXMoKV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1l'
        'bnUoKTsgc3dhcFNoaXAoJ2ZpaG9ydXMnKSIpOwpvaygnd2l0aCB0aGUgQ29sb3NzdXMgdGhlcmUg'
        'dGhlIGZpcnN0IHN3aXRjaCBzdGlsbCByZWZpdHMnLCBQKCkuaHA9PT04MCAmJiBQKCkuc2VjQW1t'
        'bz09PTIwKTsKVy5ydW4oInBsYXllci5ocD0xIik7ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBz'
        'd2FwU2hpcCgnYm9vc2lyaXMnKSIpOwpvaygnYSBuZWFybHkgZGVhZCBodWxsIHN0YXlzIGFsaXZl'
        'IGFmdGVyIGNhcnJ5aW5nIG92ZXInLCBQKCkuaHA+PTEgJiYgUCgpLmhwPD0zKTsKCnJlc2V0KCk7'
        'IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCksIGNv'
        'bG9zc3VzKHtkZWFkOnRydWV9KV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAo'
        'J2ZpaG9ydXMnKSIpOwpvaygnZGVhZCBDb2xvc3N1cyBncmFudHMgbm90aGluZycsIFcucnVuKCdz'
        'aGlwU3dhcFJlYWR5KCknKT09PWZhbHNlKTsKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0z'
        'Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKSwgY29sb3NzdXMoe3dhcnBPdXQ6dHJ1ZX0p'
        'XSk7ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBzd2FwU2hpcCgnZmlob3J1cycpIik7Cm9rKCdD'
        'b2xvc3N1cyB3YXJwaW5nIG91dCBncmFudHMgbm90aGluZycsIFcucnVuKCdzaGlwU3dhcFJlYWR5'
        'KCknKT09PWZhbHNlKTsKCnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBXLnNldCgn'
        'YWxsaWVzJyxbY29sb3NzdXMoKV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAo'
        'J2ZpaG9ydXMnKSIpOyBXLnJ1bigicGxheWVyLmhwPTIwIik7ClcucnVuKCJ0b2dnbGVTaGlwTWVu'
        'dSgpOyBzd2FwU2hpcCgnZml0b3RoJykiKTsKb2soJ2JhY2sgb250byB0aGUgc3RhcnQgaHVsbCBh'
        'dCB0aGUgQ29sb3NzdXMsIDIwLzgwIG9mIDEwMCA9IDI1JywgUCgpLnNoaXA9PT0nZml0b3RoJyAm'
        'JiBQKCkuaHA9PT0yNSk7ClcucnVuKCd3YXZlPTInKTsKb2soJ25ldyB3YXZlIHdpdGggdGhlIENv'
        'bG9zc3VzIHN0aWxsIHRoZXJlOiByZWZpdHMgYWdhaW4nLCBXLnJ1bignc2hpcFN3YXBSZWFkeSgp'
        'Jyk9PT10cnVlKTsKVy5ydW4oInRvZ2dsZVNoaXBNZW51KCk7IHN3YXBTaGlwKCdmaWhvcnVzJyki'
        'KTsgb2soJ2FuZCBpdCBpcyBhIGZ1bGwgaHVsbCcsIFAoKS5ocD09PTgwKTsKCmNvbnNvbGUubG9n'
        'KCdDeWNsZXM6IGVhY2ggYnJpbmdzIGl0cyBvd24gZmxlZXQnKTsKewogIGNvbnN0IGhvbCA9IFcu'
        'cnVuKCdjeWNsZUF0KDEpJyksIG50ZiA9IFcucnVuKCdjeWNsZUF0KDMxKScpOwogIG9rKCd3YXZl'
        'cyAxIHRvIDMwIGFyZSB0aGUgSGFtbWVyIG9mIExpZ2h0IGN5Y2xlJywgVy5ydW4oJ2N5Y2xlQXQo'
        'MzApJyk9PT1ob2wgJiYgaG9sLmZpcnN0PT09MSk7CiAgb2soJ3dhdmUgMzEgb3BlbnMgdGhlIE5U'
        'RiBjeWNsZSwgYW5kIGl0IGhvbGRzIGFmdGVyIHRoYXQnLCBudGYuZmlyc3Q9PT0zMSAmJiBXLnJ1'
        'bignY3ljbGVBdCg1OSknKT09PW50ZiAmJiBXLnJ1bignY3ljbGVBdCgxNDApJyk9PT1udGYpOwog'
        'IHJlc2V0KCk7CiAgVy5ydW4oInNjb3JlPTk1MDAwOyBlbnRlckN5Y2xlKGN5Y2xlQXQoMzEpKSIp'
        'OwogIG9rKCdlbnRlcmluZyBpdCBwdXRzIHRoZSBwbGF5ZXIgaW4gYSBNeXJtaWRvbiwgZnJlc2gn'
        'LCBQKCkuc2hpcD09PSdmaW15cm1pZG9uJyAmJiBQKCkuaHA9PT1QKCkubWF4SHApOwogIG9rKCd0'
        'aGUgcm9zdGVyIGlzIHRoZSBUZXJyYW4gb25lLCBlaWdodCBodWxscycsCiAgICAgVy5ydW4oJ1BM'
        'QVlFUl9TSElQUy5sZW5ndGgnKT09PTggJiYgVy5ydW4oIlBMQVlFUl9TSElQUy5ldmVyeShzPT5z'
        'LmZhYz09PSd0ZXJyYW4nKSIpKTsKICBvaygnaW4gdGhlIGFncmVlZCBvcmRlcicsCiAgICAgVy5y'
        'dW4oIlBMQVlFUl9TSElQUy5tYXAocz0+cy5rZXkpLmpvaW4oKSIpPT09J2ZpbXlybWlkb24sZmlo'
        'ZXJjLGJvYXJ0ZW1pcyxmaWhlcmNtazIsYm9tZWR1c2EsZmllcmlueWVzLGJvdXJzYSxmaWFyZXMn'
        'KTsKICBvaygnb25seSB0aGUgZmlyc3QgaHVsbCBpcyBvcGVuJywgVy5nZXQoJ3NoaXBVbmxvY2tl'
        'ZCcpPT09MSk7CiAgVy5ydW4oInNjb3JlPTk1MDAwKzM5OTk7IHRpY2tTaGlwVW5sb2NrcygpIik7'
        'CiAgb2soJ3RoZSBwb2ludHMgYnJvdWdodCBpbnRvIHRoZSBjeWNsZSBkbyBub3QgY291bnQnLCBX'
        'LmdldCgnc2hpcFVubG9ja2VkJyk9PT0xKTsKICBXLnJ1bigic2NvcmU9OTUwMDArNDAwMDsgdGlj'
        'a1NoaXBVbmxvY2tzKCkiKTsKICBvaygnNDAwMCBwb2ludHMgc2NvcmVkIElOIHRoZSBjeWNsZSBv'
        'cGVuIHRoZSBIZXJjdWxlcycsIFcuZ2V0KCdzaGlwVW5sb2NrZWQnKT09PTIgJiYgL0hFUkNVTEVT'
        'Ly50ZXN0KFcuZ2V0KCdTVUJfTVNHUycpLnNsaWNlKC0xKVswXS50eHQpKTsKICBvaygndGhlIFRl'
        'cnJhbiBzdXBwb3J0IGNvbHVtbiBhbnN3ZXJzLCB0aGUgVmFzdWRhbiBvbmUgZG9lcyBub3QnLAog'
        'ICAgIFcucnVuKCdBTExZX0ZBQ19PTi50ZXJyYW4nKT09PXRydWUgJiYgVy5ydW4oJ0FMTFlfRkFD'
        'X09OLnZhc3VkYW4nKT09PWZhbHNlKTsKICAvLyBUaGUgaGFuZ2FyIGZvbGxvd3MgdGhlIGh1bGws'
        'IHNvIHRoZSBUZXJyYW4gcm9zdGVyIG5lZWRzIGEgVGVycmFuIGRlc3Ryb3llci4KICBXLnNldCgn'
        'YWxsaWVzJyxbZGVzdHJveWVyKHtpbWc6J2Rlb3Jpb25yaWdodCd9KV0pOwogIG9rKCdhIFRlcnJh'
        'biBkZXN0cm95ZXIgb2ZmZXJzIHRoZSBIZXJjdWxlcycsIFcucnVuKCJzaGlwT2ZmZXJlZCgnZmlo'
        'ZXJjJykiKT09PXRydWUgJiYgVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpPT09dHJ1ZSk7CiAgVy5z'
        'ZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7CiAgb2soJ2EgVmFzdWRhbiBvbmUgZG9lcyBub3Qn'
        'LCBXLnJ1bigic2hpcE9mZmVyZWQoJ2ZpaGVyYycpIik9PT1mYWxzZSAmJiBXLnJ1bignc2hpcFN3'
        'YXBSZWFkeSgpJyk9PT1mYWxzZSk7CiAgVy5ydW4oImVudGVyQ3ljbGUoY3ljbGVBdCgxKSkiKTsK'
        'ICBvaygnYW5kIGJhY2s6IHRoZSBWYXN1ZGFuIHJvc3RlciBhbmQgY29sdW1uJywgUCgpLnNoaXA9'
        'PT0nZml0b3RoJyAmJgogICAgIFcucnVuKCdBTExZX0ZBQ19PTi50ZXJyYW4nKT09PWZhbHNlICYm'
        'IFcucnVuKCdBTExZX0ZBQ19PTi52YXN1ZGFuJyk9PT10cnVlKTsKfQpvaygndGhlIHJ1biBzdGFy'
        'dHMgaW4gdGhlIGN5Y2xlIG9mIGl0cyBmaXJzdCB3YXZlJywKICAgL2Vsc2UgZW50ZXJDeWNsZVwo'
        'Y3ljbGVBdFwod2F2ZVwrMVwpXCk7Ly50ZXN0KGZuKCdsYXVuY2hHYW1lJykpKTsKb2soJ2Nyb3Nz'
        'aW5nIGludG8gYSBuZXcgY3ljbGUgaGFuZHMgb3ZlciB0aGUgZmxlZXQnLAogICAvaWZcKF9jIT09'
        'Y3ljbGVOb3dcKSBlbnRlckN5Y2xlXChfY1wpOy8udGVzdChmbignbmV4dFdhdmUnKSkpOwpvaygn'
        'P209IHN0YXJ0cyB0aGUgcnVuIGF0IHRoYXQgd2F2ZSBpbnN0ZWFkIG9mIHJlcGVhdGluZyBpdCcs'
        'CiAgIC9TQ1JJUFRfT05FXD9TQ1JJUFRfT05FLTE6MC8udGVzdChmbignbGF1bmNoR2FtZScpKSAm'
        'JiAhL1NDUklQVF9PTkUgXD8gU0NSSVBUX09ORSA6IG4vLnRlc3Qoc3JjKSk7Cgpjb25zb2xlLmxv'
        'ZygnU3VwcG9ydCBjYWxscyBieSBmYWN0aW9uJyk7Cm9rKCd0aGUgVGVycmFuIGNvbHVtbiBpcyBv'
        'ZmYgaW4gdGhpcyBjeWNsZScsIHNyYy5pbmNsdWRlcygiY29uc3QgQUxMWV9GQUNfT04gPSB7dGVy'
        'cmFuOmZhbHNlLCB2YXN1ZGFuOnRydWUsIGd0dmE6dHJ1ZX07IikpOwpvaygndGhlIGNhbGwgaXMg'
        'Z2F0ZWQgaW5zaWRlIGNhbGxBbGx5LCBub3Qgb25seSBpbiB0aGUgbWVudScsCiAgIC9mdW5jdGlv'
        'biBjYWxsQWxseVwoaWRcKVx7W1xzXFNdezAsNDAwfWFsbHlGYWNPblwoY2RlZlwuZmFjXCkvLnRl'
        'c3Qoc3JjKSk7Cm9rKCd0aGUgbWVudSBubyBsb25nZXIgdXNlcyB0aGUgZml4ZWQgdHdvIGNvbHVt'
        'biBzcGxpdCcsICFzcmMuaW5jbHVkZXMoJ0FMTFlfVEVSX04/MDoxJykpOwpvaygndGhlIENvbG9z'
        'c3VzIGlzIGEgR1RWQSBzaGlwIG5vdycsIC9jb2xvc3N1czpccypce2NsczonZGVzdHJveWVyJywg'
        'ZmFjOidndHZhJy8udGVzdChzcmMpKTsKCmNvbnNvbGUubG9nKCdIdWxsIHBpY3R1cmVzIGluIHRo'
        'ZWlyIG93biBjZWxsJyk7CmNvbnN0IElNRyA9ICh3LGgpPT4oe3dpZHRoOncsIGhlaWdodDpofSk7'
        'CmNvbnN0IEFMTF9JTUdTID0ge2ZpdG90aDpJTUcoMTIwLDkwKSwgZmlob3J1czpJTUcoMTIwLDkw'
        'KSwgYm9vc2lyaXM6SU1HKDE1MCwxMTApLAogICAgICAgICAgICAgICAgICBmaXNlcmFwaXM6SU1H'
        'KDEyMCw5MCksIGZpc2V0aDpJTUcoMTIwLDkwKSwgYm9iYWtoYTpJTUcoMTUwLDExMCksCiAgICAg'
        'ICAgICAgICAgICAgIGZpdGF1cmV0OklNRygxMjAsOTApLCBib3Nla2htZXQ6SU1HKDE1MCwxMTAp'
        'fTsKY29uc3QgUElDVyA9IFcucnVuKCdIR19QSUNfVycpLCBQSUNIID0gVy5ydW4oJ0hHX1JPVycp'
        'LTY7CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVz'
        'dHJveWVyKCldKTsgVy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsKVy5zZXQoJ0lNR1MnLCB7fSk7'
        'CkNMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKb2soJ25vdGhpbmcgbG9hZGVkIHlldDog'
        'bm8gcGljdHVyZSwgbm8gY3Jhc2gsIHJvd3Mgc3RpbGwgdGhlcmUnLAogICBkcmF3cygpLmxlbmd0'
        'aD09PTAgJiYgVy5ydW4oJ3dpbmRvdy5fc2hpcFJlY3RzJykubGVuZ3RoPT09OCk7Clcuc2V0KCdJ'
        'TUdTJywgQUxMX0lNR1MpOwpDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgpJyk7Cm9rKCdvbmUg'
        'aHVsbCBkcmF3biBwZXIgb3BlbiByb3cnLCBkcmF3cygpLmxlbmd0aD09PTgpOwovLyBUaGUgZ2xv'
        'c3Mgb24gZWFjaCBwbGF0ZSBjbGlwcyBhcyB3ZWxsLCBzbyB0aGlzIGNvdW50cyBhdCBsZWFzdCBv'
        'bmUgY2xpcAovLyBwZXIgcGljdHVyZSByYXRoZXIgdGhhbiBleGFjdGx5IG9uZSBpbiB0b3RhbC4K'
        'b2soJ2VhY2ggb25lIGNsaXBwZWQgdG8gaXRzIG93biBjZWxsIGZpcnN0JywgY2xpcHMoKS5sZW5n'
        'dGg+PTgpOwpvaygnZWFjaCBvbmUgZml0cyBpbnNpZGUgdGhlIHBpY3R1cmUgY2VsbCcsCiAgIGRy'
        'YXdzKCkuZXZlcnkoZD0+ZC5hcmdzWzNdPD1QSUNXLTUgJiYgZC5hcmdzWzRdPD1QSUNILTUgJiYg'
        'ZC5hcmdzWzNdPjAgJiYgZC5hcmdzWzRdPjApKTsKb2soJ2FzcGVjdCByYXRpbyBrZXB0JywgZHJh'
        'd3MoKS5ldmVyeShkPT5NYXRoLmFicygoZC5hcmdzWzNdL2QuYXJnc1s0XSkgLSAoMTIwLzkwKSk8'
        'MC4wMQogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHx8IE1hdGguYWJzKChk'
        'LmFyZ3NbM10vZC5hcmdzWzRdKSAtICgxNTAvMTEwKSk8MC4wMSkpOwpvaygnc2F2ZSBhbmQgcmVz'
        'dG9yZSBzdGF5IGJhbGFuY2VkLCBubyBsZWFraW5nIGNsaXAgb3IgYWxwaGEnLCBiYWxhbmNlZCgp'
        'KTsKb2soJ2EgcGljdHVyZSBpcyBhIHBpY3R1cmUgbm93LCBub3QgYSB3YXRlcm1hcmsnLCBhbHBo'
        'YXMoKS5ldmVyeShhPT5hPjAuOSAmJiBhPD0xKSk7CnsKICAvLyBUaHJlZSBvcGVuLCBmaXZlIGxv'
        'Y2tlZDogYSBsb2NrZWQgaHVsbCBoYXMgbm8gcm93IHRhbGwgZW5vdWdoIGZvciBhCiAgLy8gcGlj'
        'dHVyZSwgc28gaXQgZ2V0cyBub25lIGF0IGFsbC4KICByZXNldCgpOyBXLnJ1bigic2hpcFVubG9j'
        'a2VkPTMiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7IFcucnVuKCd0b2dnbGVTaGlw'
        'TWVudSgpJyk7CiAgVy5zZXQoJ0lNR1MnLCBBTExfSU1HUyk7IENMUigpOyBXLnJ1bignZHJhd1No'
        'aXBNZW51KCknKTsKICBvaygnYSBsb2NrZWQgaHVsbCBzaG93cyBubyBwaWN0dXJlJywgZHJhd3Mo'
        'KS5sZW5ndGg9PT0zKTsKfQpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTgiKTsgVy5zZXQo'
        'J2FsbGllcycsW2Rlc3Ryb3llcigpXSk7IFcucnVuKCd0b2dnbGVTaGlwTWVudSgpJyk7Clcuc2V0'
        'KCdJTUdTJywge2ZpdG90aDpJTUcoMCwwKX0pOwpDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgp'
        'Jyk7Cm9rKCdhIHplcm8gc2l6ZWQgc3ByaXRlIGlzIHNraXBwZWQgaW5zdGVhZCBvZiBkaXZpZGlu'
        'ZyBieSB6ZXJvJywgZHJhd3MoKS5sZW5ndGg9PT0wKTsKVy5zZXQoJ0lNR1MnLCB7fSk7Cgpjb25z'
        'b2xlLmxvZygnQmFycmVscyBhbmQgdm9sbGV5IGRhbWFnZSwgaW4gdGhlaXIgb3duIGNvbHVtbnMn'
        'KTsKY29uc3QgdGV4dHMgPSAoKT0+IENBTExTLmZpbHRlcihjPT5jLmZuPT09J2ZpbGxUZXh0Jyku'
        'bWFwKGM9Pih7czpTdHJpbmcoYy5hcmdzWzBdKSwgeDpjLmFyZ3NbMV0sIHk6Yy5hcmdzWzJdfSkp'
        'OwovLyBBIGNvbHVtbiBpcyBjaGVja2VkIGJ5IHdoZXJlIGl0IGFjdHVhbGx5IGxhbmRzOiB0aGUg'
        'eCBvZiB0aGUgY29sdW1uIGluIHRoZQovLyBsYXlvdXQsIGFkZGVkIHRvIHRoZSB4IG9mIGEgcm93'
        'IHRoZSBtZW51IGl0c2VsZiByZXBvcnRlZC4KY29uc3QgY29sWCA9IChrKT0+IFcucnVuKCdIR19D'
        'T0xTJykuZmluZChjPT5jLms9PT1rKS54OwovLyBUaGUgY29sdW1uIHRpdGxlcyBzaXQgb24gdGhl'
        'IHNhbWUgeCwgc28gYSB2YWx1ZSBvbmx5IGNvdW50cyB3aGVuIGl0IGFsc28KLy8gc2l0cyBpbnNp'
        'ZGUgYSByb3cuCmNvbnN0IGluQ29sID0gKGspPT57CiAgY29uc3QgeDAgPSBjb2xYKGspLCBycyA9'
        'IFcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycpOwogIHJldHVybiB0ZXh0cygpLmZpbHRlcih0PT4g'
        'cnMuc29tZShyPT4gdC54ID09PSByLnggKyB4MCAmJiB0LnkgPj0gci55ICYmIHQueSA8PSByLnkg'
        'KyByLmgpKTsKfTsKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD04Iik7IFcuc2V0KCdhbGxp'
        'ZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOwpXLnNldCgnTU9V'
        'TlRTJywge30pOwpDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgpJyk7Cm9rKCdubyBtb3VudCBk'
        'YXRhOiBubyBjbGFpbSBhYm91dCBndW5zIG9yIHZvbGxleSBhdCBhbGwnLAogICBpbkNvbCgnZ3Vu'
        'cycpLmxlbmd0aD09PTAgJiYgaW5Db2woJ3ZvbGxleScpLmxlbmd0aD09PTApOwpXLnNldCgnTU9V'
        'TlRTJywge2ZpdG90aDp7cHJpbWFyeTpbMSwxXX0sIGZpaG9ydXM6e3ByaW1hcnk6WzEsMV19LCBi'
        'b29zaXJpczp7cHJpbWFyeTpbMSwxXX0sCiAgICAgICAgICAgICAgICAgZmlzZXJhcGlzOntwcmlt'
        'YXJ5OlsxLDFdfSwgZmlzZXRoOntwcmltYXJ5OlsxLDFdfSwgYm9iYWtoYTp7cHJpbWFyeTpbMSwx'
        'XX0sCiAgICAgICAgICAgICAgICAgZml0YXVyZXQ6e3ByaW1hcnk6WzEsMSwxXX0sIGJvc2VraG1l'
        'dDp7cHJpbWFyeTpbMSwxXX19KTsKQ0xSKCk7IFcucnVuKCdkcmF3U2hpcE1lbnUoKScpOwpvaygn'
        'YSBmaWd1cmUgb24gZXZlcnkgb25lIG9mIHRoZSBlaWdodCByb3dzJywKICAgaW5Db2woJ2d1bnMn'
        'KS5sZW5ndGg9PT04ICYmIGluQ29sKCd2b2xsZXknKS5sZW5ndGg9PT04KTsKb2soJ3RoZSBzZXZl'
        'biB0d28gYmFycmVsIGh1bGxzIHJlYWQgMiBhbmQgNTEnLAogICBpbkNvbCgnZ3VucycpLmZpbHRl'
        'cih0PT50LnM9PT0nMicpLmxlbmd0aD09PTcgJiYKICAgaW5Db2woJ3ZvbGxleScpLmZpbHRlcih0'
        'PT50LnM9PT0nNTEnKS5sZW5ndGg9PT03KTsKb2soJ3RoZSBUYXVyZXQgcmVhZHMgMyBhbmQgNTcn'
        'LAogICBpbkNvbCgnZ3VucycpLmZpbHRlcih0PT50LnM9PT0nMycpLmxlbmd0aD09PTEgJiYKICAg'
        'aW5Db2woJ3ZvbGxleScpLmZpbHRlcih0PT50LnM9PT0nNTcnKS5sZW5ndGg9PT0xKTsKb2soJ3Ro'
        'ZSBmaWd1cmUgbWF0Y2hlcyB3aGF0IHZvbGxleURtZyBhY3R1YWxseSBkb2VzJywKICAgTWF0aC5y'
        'b3VuZChXLnJ1bigndm9sbGV5VG90YWwoMiknKSk9PT01MSAmJiBNYXRoLnJvdW5kKFcucnVuKCd2'
        'b2xsZXlUb3RhbCgzKScpKT09PTU3CiAgICYmIE1hdGgucm91bmQoVy5ydW4oJ3ZvbGxleVRvdGFs'
        'KDEpJykpPT09NDQpOwpvaygnb25lIGJhcnJlbCBpcyB0aGUgZmFsbGJhY2sgb2YgdGhlIGZvcm11'
        'bGEsIG5vdCBhIGNyYXNoJywgVy5ydW4oJ3ZvbGxleVRvdGFsKDApJyk9PT00NCk7CnsKICAvLyBU'
        'aGUgcG9pbnQgb2YgdGhlIGNvbHVtbnM6IGh1bGwgc2l0cyB1bmRlciBodWxsIG9uIGV2ZXJ5IHJv'
        'dy4KICBjb25zdCBodWxscyA9IGluQ29sKCdodWxsJykubWFwKHQ9PnQucykuam9pbigpOwogIG9r'
        'KCd0aGUgaHVsbCBjb2x1bW4gcmVhZHMgZG93biB0aGUgbGlzdCBpbiBvcmRlcicsIGh1bGxzPT09'
        'JzEwMCw4MCw4MCwxMjUsMTAwLDE0MCwxMDAsMTQwJyk7CiAgY29uc3Qgc2hpZWxkcyA9IGluQ29s'
        'KCdzaGllbGQnKS5tYXAodD0+dC5zKS5qb2luKCk7CiAgb2soJ3RoZSBzaGllbGQgY29sdW1uIHRv'
        'bycsIHNoaWVsZHM9PT0nMTAwLDEwMCw3MCwxMzAsMTMwLDEwMCwxMDAsMTMwJyk7CiAgb2soJ2V2'
        'ZXJ5IHZhbHVlIGluIGEgY29sdW1uIHNoYXJlcyBvbmUgeCcsCiAgICAgbmV3IFNldChpbkNvbCgn'
        'aHVsbCcpLm1hcCh0PT50LngpKS5zaXplPT09MSk7Cn0KewogIC8vIFR3byB1bmxvY2tlZCBvZiBl'
        'aWdodDogdGhlIG1lbnUgbmVlZHMgdHdvIHRvIG9wZW4gYXQgYWxsLgogIHJlc2V0KCk7IFcucnVu'
        'KCJzaGlwVW5sb2NrZWQ9MiIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKICBXLnNl'
        'dCgnTU9VTlRTJywge2ZpdG90aDp7cHJpbWFyeTpbMSwxXX0sIGZpaG9ydXM6e3ByaW1hcnk6WzEs'
        'MV19LCBmaXRhdXJldDp7cHJpbWFyeTpbMSwxLDFdfX0pOwogIFcucnVuKCd0b2dnbGVTaGlwTWVu'
        'dSgpJyk7IENMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKICBvaygnb25seSB0aGUgdHdv'
        'IHVubG9ja2VkIHJvd3MgbWFrZSBhIGNsYWltJywgaW5Db2woJ2d1bnMnKS5sZW5ndGg9PT0yKTsK'
        'ICBvaygndGhlIGxvY2tlZCBUYXVyZXQgc3RheXMgc2lsZW50IGV2ZW4gd2l0aCBtb3VudCBkYXRh'
        'JywKICAgICBpbkNvbCgndm9sbGV5JykuZXZlcnkodD0+dC5zIT09JzU3JykpOwp9Clcuc2V0KCdN'
        'T1VOVFMnLCB7fSk7Cgpjb25zb2xlLmxvZygnT25lIGxvb2ssIGFuZCBpdCBpcyB0aGUgZm9ydW0g'
        'b25lJyk7CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBXLnNldCgnYWxsaWVzJyxb'
        'ZGVzdHJveWVyKCldKTsgVy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsKQ0xSKCk7IFcucnVuKCdk'
        'cmF3U2hpcE1lbnUoKScpOwpjb25zdCBobHBGb250cyA9IENBTExTLmZpbHRlcihjPT5jLmZuPT09'
        'J3NldCBmb250JykubWFwKGM9PlN0cmluZyhjLmFyZ3NbMF0pKTsKY29uc3QgaGxwQ2VsbHMgPSBX'
        'LnJ1bignd2luZG93Ll9zaGlwUmVjdHMnKS5tYXAocj0+ci54KycsJytyLnkrJywnK3IudysnLCcr'
        'ci5oKS5qb2luKCd8Jyk7Cm9rKCdubyBDb3VyaWVyIGxlZnQgaW4gdGhlIGhhbmdhcicsIGhscEZv'
        'bnRzLmV2ZXJ5KGY9PmYuaW5kZXhPZignQ291cmllcicpPDApKTsKb2soJ2l0IHVzZXMgdGhlIGZv'
        'cnVtIGZhY2VzJywgaGxwRm9udHMuc29tZShmPT5mLmluZGV4T2YoJ1RhaG9tYScpPj0wKSAmJiBo'
        'bHBGb250cy5zb21lKGY9PmYuaW5kZXhPZignU2Vnb2UgVUknKT49MCkpOwpvaygndmFsdWVzIGFy'
        'ZSBubyBsb25nZXIgc2V0IGluIDggYW5kIDkgcGl4ZWxzJywKICAgaGxwRm9udHMuZmlsdGVyKGY9'
        'Pi9TZWdvZSBVSS8udGVzdChmKSkuc29tZShmPT4vMVs0LTldcHgvLnRlc3QoZikpKTsKb2soJ3Ro'
        'ZSBhY3RpdmUgcm93IGdldHMgYSBnbG93IHJpbmcnLCBDQUxMUy5zb21lKGM9PmMuZm49PT0nc2V0'
        'IHNoYWRvd0JsdXInKSk7Cm9rKCdubyByaW5nIGxlYWtzIG91dCBvZiBpdHMgc2F2ZS9yZXN0b3Jl'
        'JywgYmFsYW5jZWQoKSk7Cm9rKCdub3RoaW5nIGNob29zZXMgYmV0d2VlbiB0d28gbG9va3MgYW55'
        'IG1vcmUnLCAhL0VDT1xcLmh1ZC8udGVzdChzcmMpKTsKVy5ydW4oIkVDTy5zY2hlbWU9J3ZvaWQn'
        'Iik7IENMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKb2soJ3RoZSBoYW5nYXIgZHJhd3Mg'
        'aW4gVm9pZCB0b28nLCBDQUxMUy5sZW5ndGg+NTApOwpvaygnYW5kIHRoZSByb3dzIGRpZCBub3Qg'
        'bW92ZScsCiAgIFcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycpLm1hcChyPT5yLngrJywnK3IueSsn'
        'LCcrci53KycsJytyLmgpLmpvaW4oJ3wnKT09PWhscENlbGxzKTsKVy5ydW4oIkVDTy5zY2hlbWU9'
        'J2ZpcmUnIik7Cgpjb25zb2xlLmxvZygnRXZlcnl0aGluZyBpcyBkcmF3biBmcm9tIHRoZSBzdXJm'
        'YWNlIGtpdCcpOwp7CiAgcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD04Iik7IFcuc2V0KCdh'
        'bGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOwogIENMUigp'
        'OyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKICAvLyBHcmFkaWVudHMgYXJlIGFsbG93ZWQgYWdh'
        'aW4sIGJ1dCBvbmx5IGFzIGdsb3NzOiBhIHNob3J0IGZhbGwgb2YgbGlnaHQKICAvLyBvdmVyIHRo'
        'ZSB0b3Agb2YgYSBwbGF0ZS4gTm9uZSBtYXkgcnVuIHRoZSBoZWlnaHQgb2YgYSBwYW5lbCB0aGUg'
        'd2F5IHRoZQogIC8vIG9sZCBib3ggZ3JhZGllbnQgZGlkLgogIGNvbnN0IGdyYWRzID0gQ0FMTFMu'
        'ZmlsdGVyKGM9PmMuZm49PT0nY3JlYXRlTGluZWFyR3JhZGllbnQnKTsKICBvaygnZXZlcnkgZ3Jh'
        'ZGllbnQgaXMgYSBnbG9zcywgbm90IGEgZnVsbCBoZWlnaHQgZmlsbCcsCiAgICAgZ3JhZHMubGVu'
        'Z3RoPjAgJiYgZ3JhZHMuZXZlcnkoZz0+KGcuYXJnc1szXS1nLmFyZ3NbMV0pPD0yMDApKTsKICAv'
        'LyBBIGNoYW1mZXJlZCBvdXRsaW5lIGlzIHNpeCBjb3JuZXJzLiBBIHJlY3RhbmdsZSB3b3VsZCBi'
        'ZSBmb3VyLgogIGNvbnN0IGNsb3NlcyA9IENBTExTLmZpbHRlcihjPT5jLmZuPT09J2Nsb3NlUGF0'
        'aCcpLmxlbmd0aDsKICBvaygndGhlIHBhbmVsIGFuZCBldmVyeSBwbGF0ZSBhcmUgY2hhbWZlcmVk'
        'LCBub3QgcmVjdGFuZ2xlcycsIGNsb3Nlcz49OSk7CiAgb2soJ29uZSBzY2FsZSB1bmRlciBlYWNo'
        'IG9mIHRoZSB0d28gZ3JvdXAgaGVhZGluZ3MnLAogICAgIENBTExTLmZpbHRlcihjPT5jLmZuPT09'
        'J3NldCBsaW5lV2lkdGgnICYmIGMuYXJnc1swXT09PTEpLmxlbmd0aD4wICYmIGNsb3Nlcz49OSk7'
        'CiAgb2soJ2EgcmluZyBpcyBkcmF3biwgYW5kIG9ubHkgYXJvdW5kIHRoZSBhY3RpdmUgcm93JywK'
        'ICAgICBDQUxMUy5maWx0ZXIoYz0+Yy5mbj09PSdzZXQgc2hhZG93Qmx1cicgJiYgYy5hcmdzWzBd'
        'PT09NikubGVuZ3RoPT09Mik7CiAgb2soJ25vdGhpbmcgbGVha3Mgb3V0IG9mIGEgc2F2ZS9yZXN0'
        'b3JlJywgYmFsYW5jZWQoKSk7Cn0KewogIC8vIFRoZSBraXQgaXMgc2hhcmVkLCBzbyB0aGUgaGFu'
        'Z2FyIG11c3Qgbm90IHJlYWNoIHBhc3QgaXQgZm9yIGEgc2hhcGUgb2YKICAvLyBpdHMgb3duLiB0'
        'aEJldmVsIGFuZCB0aFBhbmVsIGJlbG9uZyB0byB0aGUgc2NyZWVucyBub3QgeWV0IHJlYnVpbHQu'
        'CiAgY29uc3QgYSA9IHNyYy5pbmRleE9mKCdmdW5jdGlvbiBkcmF3U2hpcE1lbnUoKScpOwogIGNv'
        'bnN0IGJvZHkgPSBzcmMuc2xpY2UoYSwgc3JjLmluZGV4T2YoJ2Z1bmN0aW9uIGRyYXdDYWxsTWVu'
        'dSgpJykpOwogIG9rKCd0aGUgaGFuZ2FyIHVzZXMgbm8gYmV2ZWwgYW5kIG5vIGdyYWRpZW50IHBh'
        'bmVsJywKICAgICBib2R5LmluZGV4T2YoJ3RoQmV2ZWwnKTwwICYmIGJvZHkuaW5kZXhPZigndGhQ'
        'YW5lbCcpPDApOwogIG9rKCdhbmQgbm8gZGlhbG9nIGZyYW1lIG9mIGl0cyBvd24nLCBib2R5Lmlu'
        'ZGV4T2YoJ3VpRGlhbG9nJyk8MCk7Cn0KewogIC8vIFRoZSBkaWdpdCBpcyB0aGUga2V5Ym9hcmQg'
        'c2hvcnRjdXQsIHNvIGl0IGhhcyB0byBmb2xsb3cgdGhlIGh1bGwgdGhyb3VnaAogIC8vIHRoZSBy'
        'ZWdyb3VwaW5nIHJhdGhlciB0aGFuIGNvdW50IHJvd3MuCiAgcmVzZXQoKTsgVy5ydW4oInNoaXBV'
        'bmxvY2tlZD04Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9nZ2xl'
        'U2hpcE1lbnUoKScpOwogIENMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKICBjb25zdCBy'
        'cyA9IFcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycpOwogIGNvbnN0IGNoaXBYID0gVy5ydW4oJ0hH'
        'X05VTScpICsgVy5ydW4oJ0hHX05VTV9XJykvMjsKICBjb25zdCBjaGlwID0gKGtleSk9PnsgY29u'
        'c3Qgcj1ycy5maW5kKHI9PnIuc2hpcD09PWtleSk7CiAgICByZXR1cm4gdGV4dHMoKS5maW5kKHQ9'
        'PiB0Lng9PT1yLngrY2hpcFggJiYgdC55Pj1yLnkgJiYgdC55PD1yLnkrci5oKTsgfTsKICBvaygn'
        'dGhlIE9zaXJpcyBzaG93cyA2OiBmaXJzdCBib21iZXIsIHNpeHRoIHJvdycsCiAgICAgY2hpcCgn'
        'Ym9vc2lyaXMnKSAmJiBjaGlwKCdib29zaXJpcycpLnM9PT0nNicpOwogIG9rKCdhbmQgdGhlIEJh'
        'a2hhIHNob3dzIDcnLCBjaGlwKCdib2Jha2hhJykgJiYgY2hpcCgnYm9iYWtoYScpLnM9PT0nNycp'
        'OwogIG9rKCd0aGUgZGlnaXRzIHJ1biAxIHRvIDggc3RyYWlnaHQgZG93biB0aGUgcGFuZWwnLAog'
        'ICAgIHJzLm1hcChyPT5jaGlwKHIuc2hpcCkucykuam9pbigpPT09JzEsMiwzLDQsNSw2LDcsOCcp'
        'Owp9Cgpjb25zb2xlLmxvZygnVGhlIHBhbmVsIGdyb3dzIHdpdGggd2hhdCBpcyBvcGVuJyk7CnsK'
        'ICBjb25zdCBoZWlnaHQgPSAoKT0+eyBjb25zdCByPVcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycp'
        'OyByZXR1cm4gcltyLmxlbmd0aC0xXS55K3Jbci5sZW5ndGgtMV0uaCAtIHJbMF0ueTsgfTsKICBy'
        'ZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTIiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3ll'
        'cigpXSk7IFcucnVuKCd0b2dnbGVTaGlwTWVudSgpOyBkcmF3U2hpcE1lbnUoKScpOwogIGNvbnN0'
        'IHNtYWxsID0gaGVpZ2h0KCk7CiAgcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD04Iik7IFcu'
        'c2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKTsgZHJh'
        'd1NoaXBNZW51KCknKTsKICBjb25zdCBiaWcgPSBoZWlnaHQoKTsKICBvaygnZWlnaHQgb3BlbiBo'
        'dWxscyBuZWVkIG1vcmUgcm9vbSB0aGFuIHR3bycsIGJpZyA+IHNtYWxsKTsKICBvaygnYW5kIGl0'
        'IHN0aWxsIGZpdHMgb24gdGhlIGZpZWxkJywKICAgICBXLnJ1bignd2luZG93Ll9zaGlwUmVjdHMn'
        'KS5ldmVyeShyPT5yLnk+PTAgJiYgci55K3IuaDw9NTAwKSk7Cn0KCmNvbnNvbGUubG9nKCdSZWFy'
        'bSBuZWVkcyBhIGNvcnZldHRlLCBub3QgYW55IHNoaXAgYXQgYWxsJyk7CnsKICBjb25zdCBjb3J2'
        'ZXR0ZSA9ICgpPT4oe3R5cGU6J2NvcnZldHRlJywgc2lkZTonYWxseScsIGRlYWQ6ZmFsc2UsIHdh'
        'cnBPdXQ6MCwgd2FycDowfSk7CiAgcmVzZXQoKTsgVy5zZXQoJ2FsbGllcycsIFtdKTsKICBvaygn'
        'bm90aGluZyBvbiB0aGUgZmllbGQsIG5vIHJlYXJtJywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09'
        'ZmFsc2UpOwogIFcuc2V0KCdhbGxpZXMnLCBbZGVzdHJveWVyKCldKTsKICBvaygnYSBkZXN0cm95'
        'ZXIgaXMgYSBoYW5nYXIsIG5vdCBhbiBhcm1vdXJ5JywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09'
        'ZmFsc2UpOwogIFcuc2V0KCdhbGxpZXMnLCBbY29ydmV0dGUoKV0pOwogIG9rKCdhIGNvcnZldHRl'
        'IG9wZW5zIGl0JywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09dHJ1ZSk7CiAgY29uc3Qgd2FycGlu'
        'ZyA9IGNvcnZldHRlKCk7IHdhcnBpbmcud2FycCA9IDQwOwogIFcuc2V0KCdhbGxpZXMnLCBbd2Fy'
        'cGluZ10pOwogIG9rKCdvbmUgc3RpbGwgY29taW5nIG91dCBvZiB0aGUgdm9ydGV4IGRvZXMgbm90'
        'JywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09ZmFsc2UpOwogIGNvbnN0IGRlYWQgPSBjb3J2ZXR0'
        'ZSgpOyBkZWFkLmRlYWQgPSB0cnVlOwogIFcuc2V0KCdhbGxpZXMnLCBbZGVhZF0pOwogIG9rKCdu'
        'b3IgZG9lcyBhIHdyZWNrJywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09ZmFsc2UpOwogIFcuc2V0'
        'KCdhbGxpZXMnLCBbY29ydmV0dGUoKV0pOwogIFcuc2V0KCdhbGxpZXMnLCBbY29ydmV0dGUoKV0p'
        'OyAgIC8vIGEgbGl2ZSBvbmUgYWdhaW4sIGFmdGVyIHRoZSB3cmVjayBhYm92ZQogIFcucnVuKCdj'
        'bGVhclJlc3VtZUhvbGQoKScpOyAgICAgIC8vIGFuZCBubyBob2xkIGxlZnQgb3ZlciBmcm9tIGVh'
        'cmxpZXIKICAvLyBQcmVzcyB0aGUgcmVjdGFuZ2xlIHRoZSBiYXIgcmVwb3J0cywgdGhlIHdheSBh'
        'IHBsYXllciBkb2VzLiBDYWxsaW5nCiAgLy8gdG9nZ2xlUmVhcm1NZW51KCkgaGVyZSB0ZXN0ZWQg'
        'dGhlIHBhbmVsIGFuZCBub3QgdGhlIGJ1dHRvbiwgd2hpY2ggaXMgaG93CiAgLy8gYSBidXR0b24g'
        'dGhhdCB3YXMgbmV2ZXIgd2lyZWQgdG8gYW55dGhpbmcgcGFzc2VkLgogIC8vIENsZWFyIHRoZSBz'
        'aGlwIGJ1dHRvbiBmaXJzdDogYW4gZWFybGllciBjYXNlIGxlZnQgYSByZWN0YW5nbGUgc3RhbmRp'
        'bmcKICAvLyB0aGF0IGNvdmVycyB0aGlzIHNwb3QsIGFuZCBwb2ludGVyQ29uc3VtZWQgYXNrcyBh'
        'Ym91dCBpdCBvbmUgbGluZSBzb29uZXIuCiAgVy5ydW4oIndpbmRvdy5fc2hpcEJ0blJlY3Q9bnVs'
        'bDsgd2luZG93Ll9yZWFybUJ0blJlY3Q9e3g6NzA5LHk6NCx3OjIyLGg6NDZ9OyIKICAgICAgKyAi'
        'IHBvaW50ZXJDb25zdW1lZCh7eDo3MTQseToxMn0pIik7CiAgb2soJ3ByZXNzaW5nIHRoZSBidXR0'
        'b24gaW4gdGhlIGJhciBvcGVucyB0aGUgcGFuZWwnLCBXLmdldCgncmVhcm1NZW51Jyk9PT10cnVl'
        'KTsKICBXLnJ1bigicG9pbnRlckNvbnN1bWVkKHt4OjcxNCx5OjEyfSkiKTsKICBvaygnYW5kIHBy'
        'ZXNzaW5nIGl0IGFnYWluIGNsb3NlcyBpdCcsIFcuZ2V0KCdyZWFybU1lbnUnKT09PWZhbHNlKTsK'
        'ICBXLnJ1bignc2V0UmVhcm1NZW51KGZhbHNlKScpOwp9Cgpjb25zb2xlLmxvZygnVGhlIHN0YW5k'
        'YXJkIGZpdCBpcyBwcm92YWJseSB0aGUgZ3VuIHRoZSBnYW1lIGhhZCcpOwp7CiAgY29uc3QgcCA9'
        'IFcucnVuKCJwcmlEZWYoJ3Byb21ldGhldXMnKSIpOwogIG9rKCd0aGUgUHJvbWV0aGV1cyBjYXJy'
        'aWVzIG5vIGZhY3RvcnMgYXQgYWxsJywgcC5kbWc9PT0xICYmIHAucmF0ZT09PTEpOwogIG9rKCdh'
        'bmQgbm8gbGltaXQgb24gaXRzIHJlYWNoJywgcC5yYW5nZT09PTApOwogIHJlc2V0KCk7IFcucnVu'
        'KCJwbGF5ZXIucHJpPSdwcm9tZXRoZXVzJzsgYXBwbHlMb2Fkb3V0KCkiKTsKICBvaygnc28gdGhl'
        'IHJhdGUgb2YgZmlyZSBpcyB0aGUgb2xkIDI4IHN0ZXBzJywgVy5nZXQoJ3BsYXllcicpLmZSPT09'
        'MjgpOwogIGNvbnN0IG0gPSBXLnJ1bigic2VjRGVmKCdteDY0JykiKTsKICBvaygndGhlIE1YLTY0'
        'IGlzIHRoZSBvbGQgbWlzc2lsZSwgdG8gdGhlIG51bWJlcicsCiAgICAgbS5kbWc9PT0zNSAmJiBt'
        'LmNkPT09NDUgJiYgbS5zcGQ9PT0zLjUgJiYgbS5saWZlPT09MjIwICYmIG0uaG9taW5nPT09dHJ1'
        'ZSk7CiAgY29uc3QgYyA9IFcucnVuKCJzZWNEZWYoJ2N5Y2xvcHMnKSIpOwogIG9rKCdhbmQgdGhl'
        'IEN5Y2xvcHMgdGhlIG9sZCBib21iJywKICAgICBjLmRtZz09PTgwICYmIGMuY2Q9PT05MCAmJiBj'
        'LnNwZD09PTEuNSAmJiBjLmxpZmU9PT0zMDApOwp9Cgpjb25zb2xlLmxvZygnQSBodWxsIGNhbiBv'
        'bmx5IGNhcnJ5IHdoYXQgaXQgY2FuIGNhcnJ5Jyk7CnsKICByZXNldCgpOyBXLnJ1bigiYXBwbHlT'
        'aGlwKCdmaXRvdGgnKSIpOwogIG9rKCdhIGZpZ2h0ZXIgaXMgZ2l2ZW4gYSBtaXNzaWxlJywgVy5y'
        'dW4oImN1clNlYygpLmNscyIpPT09J21pc3NpbGUnKTsKICBvaygnYW5kIHRoZSBiYXIgaXMgdG9s'
        'ZCBzbycsIFcuZ2V0KCdwbGF5ZXInKS5zZWNUeXBlPT09J21pc3NpbGUnKTsKICBXLnJ1bigiYXBw'
        'bHlTaGlwKCdib29zaXJpcycpIik7CiAgb2soJ2EgYm9tYmVyIGNhbm5vdCBrZWVwIGl0LCBhbmQg'
        'Z2V0cyBhIGJvbWInLCBXLnJ1bigiY3VyU2VjKCkuY2xzIik9PT0nYm9tYicpOwogIG9rKCdhbmQg'
        'dGhlIGJhciBhZ2FpbicsIFcuZ2V0KCdwbGF5ZXInKS5zZWNUeXBlPT09J2JvbWInKTsKICBvaygn'
        'b25seSBib21icyBhcmUgb2ZmZXJlZCB0byBpdCcsCiAgICAgVy5ydW4oInNlY29uZGFyaWVzRm9y'
        'KCdib29zaXJpcycpIikuZXZlcnkodz0+dy5jbHM9PT0nYm9tYicpKTsKICBvaygnYW5kIG9ubHkg'
        'bWlzc2lsZXMgdG8gYSBmaWdodGVyJywKICAgICBXLnJ1bigic2Vjb25kYXJpZXNGb3IoJ2ZpdG90'
        'aCcpIikuZXZlcnkodz0+dy5jbHM9PT0nbWlzc2lsZScpKTsKICBvaygndGhlIHJhY2sgc2l6ZSBz'
        'dGlsbCBjb21lcyBmcm9tIHRoZSBodWxsJywKICAgICBXLmdldCgncGxheWVyJykuc2VjTWF4ID09'
        'PSBXLnJ1bigic2hpcFN0YXRzKCdib29zaXJpcycpLnNlYyIpKTsKfQoKY29uc29sZS5sb2coJ0Eg'
        'cmVmaXQgZmlsbHMgdGhlIHJhY2sgLSB0aGF0IGlzIHdoYXQgbWFrZXMgaXQgYSByZWFybScpOwp7'
        'CiAgY29uc3QgY29ydmV0dGUgPSAoKT0+KHt0eXBlOidjb3J2ZXR0ZScsIHNpZGU6J2FsbHknLCBk'
        'ZWFkOmZhbHNlLCB3YXJwT3V0OjAsIHdhcnA6MH0pOwogIHJlc2V0KCk7IFcucnVuKCJhcHBseVNo'
        'aXAoJ2ZpdG90aCcpOyBzY29yZT0wIik7IFcuc2V0KCdhbGxpZXMnLCBbY29ydmV0dGUoKV0pOwog'
        'IFcucnVuKCdwbGF5ZXIuc2VjQW1tbz0zJyk7CiAgVy5ydW4oJ3RvZ2dsZVJlYXJtTWVudSgpJyk7'
        'CiAgVy5ydW4oImZpdFdlYXBvbignbXg2NCcpIik7CiAgb2soJ2ZpdHRpbmcgd2hhdCBpcyBhbHJl'
        'YWR5IGZpdHRlZCB0b3BzIHRoZSByYWNrIHVwJywKICAgICBXLmdldCgncGxheWVyJykuc2VjQW1t'
        'byA9PT0gVy5nZXQoJ3BsYXllcicpLnNlY01heCk7CiAgb2soJ2FuZCBjbG9zZXMgdGhlIHBhbmVs'
        'JywgVy5nZXQoJ3JlYXJtTWVudScpPT09ZmFsc2UpOwogIC8vIExvY2tlZCB3ZWFwb25zIGNhbm5v'
        'dCBiZSB0YWtlbiwgaG93ZXZlciB0aGV5IGFyZSByZWFjaGVkLgogIFcucnVuKCdwbGF5ZXIuc2Vj'
        'QW1tbz0zOyB0b2dnbGVSZWFybU1lbnUoKScpOwogIFcucnVuKCJmaXRXZWFwb24oJ2hsNycpIik7'
        'CiAgb2soJ2Egd2VhcG9uIGFib3ZlIHRoZSBzY29yZSBjYW5ub3QgYmUgZml0dGVkJywgVy5nZXQo'
        'J3BsYXllcicpLnByaT09PSdwcm9tZXRoZXVzJyk7CiAgb2soJ2FuZCB0aGUgcGFuZWwgc3RheXMg'
        'b3BlbicsIFcuZ2V0KCdyZWFybU1lbnUnKT09PXRydWUpOwogIFcucnVuKCdzY29yZT02MDAwJyk7'
        'CiAgVy5ydW4oImZpdFdlYXBvbignaGw3JykiKTsKICBvaygncGFzdCB0aGUgdGhyZXNob2xkIGl0'
        'IGNhbicsIFcuZ2V0KCdwbGF5ZXInKS5wcmk9PT0naGw3Jyk7CiAgb2soJ2FuZCB0aGUgcmF0ZSBv'
        'ZiBmaXJlIGZvbGxvd3MgdGhlIHdlYXBvbicsIFcuZ2V0KCdwbGF5ZXInKS5mUj09PTE3KTsKICBX'
        'LnJ1bignc2NvcmU9MDsgcGxheWVyLnByaT0icHJvbWV0aGV1cyI7IGFwcGx5TG9hZG91dCgpJyk7'
        'Cn0KCmNvbnNvbGUubG9nKCdUaGUgcmVhcm0gcGFuZWwnKTsKewogIGNvbnN0IGNvcnZldHRlID0g'
        'KCk9Pih7dHlwZTonY29ydmV0dGUnLCBzaWRlOidhbGx5JywgZGVhZDpmYWxzZSwgd2FycE91dDow'
        'LCB3YXJwOjB9KTsKICByZXNldCgpOyBXLnJ1bigiYXBwbHlTaGlwKCdmaXRvdGgnKTsgc2NvcmU9'
        'OTAwMCIpOyBXLnNldCgnYWxsaWVzJywgW2NvcnZldHRlKCldKTsKICBXLnJ1bigndG9nZ2xlUmVh'
        'cm1NZW51KCknKTsKICBDTFIoKTsgVy5ydW4oJ2RyYXdSZWFybU1lbnUoKScpOwogIGNvbnN0IHJz'
        'ID0gVy5ydW4oJ3dpbmRvdy5fcmVhcm1SZWN0cycpOwogIGNvbnN0IHByID0gVy5ydW4oJ3dpbmRv'
        'dy5fcmVhcm1QYW5lbFJlY3QnKTsKICAvLyBPbmUgcm93IHBlciB3ZWFwb24gdGhhdCBleGlzdHMs'
        'IG9wZW4gb3Igbm90OiBhIGxvY2tlZCBvbmUgaXMgYSB0aGluCiAgLy8gbGluZSwgYW5kIGl0IGlz'
        'IHN0aWxsIGEgcm93LiBUaGUgY291bnQgZm9sbG93cyB0aGUgdGFibGVzIHNvIGEgbmV3CiAgLy8g'
        'd2VhcG9uIGRvZXMgbm90IG1ha2UgdGhpcyBmYWlsIGZvciBubyByZWFzb24uCiAgY29uc3Qgb2Zm'
        'ZXJlZCA9IFcucnVuKCdQUklNQVJJRVMnKS5sZW5ndGggKyBXLnJ1bigic2Vjb25kYXJpZXNGb3Io'
        'J2ZpdG90aCcpIikubGVuZ3RoOwogIG9rKCdvbmUgcm93IHBlciB3ZWFwb24gb24gb2ZmZXInLCBy'
        'cy5sZW5ndGg9PT1vZmZlcmVkKTsKICBvaygnZXZlcnkgcm93IGlzIGluc2lkZSB0aGUgcGFuZWwn'
        'LAogICAgIHJzLmV2ZXJ5KHI9PnIueD49cHIueCAmJiByLngrci53PD1wci54K3ByLncgJiYgci55'
        'Pj1wci55ICYmIHIueStyLmg8PXByLnkrcHIuaCkpOwogIG9rKCd0aGUgcGFuZWwgZml0cyBvbiB0'
        'aGUgZmllbGQnLCBwci55Pj0wICYmIHByLnkrcHIuaDw9NTAwICYmIHByLng+PTAgJiYgcHIueCtw'
        'ci53PD04MDApOwogIG9rKCdubyBDb3VyaWVyIGFueXdoZXJlJywKICAgICBDQUxMUy5maWx0ZXIo'
        'Yz0+Yy5mbj09PSdzZXQgZm9udCcpLmV2ZXJ5KGM9PlN0cmluZyhjLmFyZ3NbMF0pLmluZGV4T2Yo'
        'J0NvdXJpZXInKTwwKSk7CiAgb2soJ3RoZSBmaXR0ZWQgd2VhcG9uIGdldHMgdGhlIHJpbmcnLCBD'
        'QUxMUy5zb21lKGM9PmMuZm49PT0nc2V0IHNoYWRvd0JsdXInKSk7CiAgb2soJ25vdGhpbmcgbGVh'
        'a3Mgb3V0IG9mIGEgc2F2ZS9yZXN0b3JlJywgYmFsYW5jZWQoKSk7CiAgLy8gQSBjbGljayBpbnNp'
        'ZGUgdGhlIHBhbmVsIHRoYXQgaGl0IG5vIHJvdyBtdXN0IG5vdCBjbG9zZSBpdCwgdGhlIHNhbWUK'
        'ICAvLyBydWxlIHRoZSBoYW5nYXIgYW5kIHRoZSBzdXBwb3J0IG1lbnUgZm9sbG93LgogIFcucnVu'
        'KGBwb2ludGVyQ29uc3VtZWQoe3g6JHtwci54KzQwfSx5OiR7cHIueSs2fX0pYCk7CiAgb2soJ2Eg'
        'Y2xpY2sgb24gdGhlIGhlYWRlciBrZWVwcyBpdCBvcGVuJywgVy5nZXQoJ3JlYXJtTWVudScpPT09'
        'dHJ1ZSk7CiAgVy5ydW4oYHBvaW50ZXJDb25zdW1lZCh7eDoke3ByLngtMTJ9LHk6JHtwci55K3By'
        'LmgvMn19KWApOwogIG9rKCdhIGNsaWNrIGJlc2lkZSBpdCBjbG9zZXMgaXQnLCBXLmdldCgncmVh'
        'cm1NZW51Jyk9PT1mYWxzZSk7Cn0KewogIC8vIEJlbG93IHRoZSB0aHJlc2hvbGQgdGhlIEhMLTcg'
        'aXMgYSB0aGluIGxpbmUsIG5vdCBhIHJvdyB0aGF0IGNhbiBiZSB0YWtlbi4KICBjb25zdCBjb3J2'
        'ZXR0ZSA9ICgpPT4oe3R5cGU6J2NvcnZldHRlJywgc2lkZTonYWxseScsIGRlYWQ6ZmFsc2UsIHdh'
        'cnBPdXQ6MCwgd2FycDowfSk7CiAgcmVzZXQoKTsgVy5ydW4oImFwcGx5U2hpcCgnZml0b3RoJyk7'
        'IHNjb3JlPTAiKTsgVy5zZXQoJ2FsbGllcycsIFtjb3J2ZXR0ZSgpXSk7CiAgVy5ydW4oJ3RvZ2ds'
        'ZVJlYXJtTWVudSgpOyBkcmF3UmVhcm1NZW51KCknKTsKICBjb25zdCBycyA9IFcucnVuKCd3aW5k'
        'b3cuX3JlYXJtUmVjdHMnKTsKICBvaygnYSBsb2NrZWQgd2VhcG9uIHJlcG9ydHMgbm8ga2V5Jywg'
        'cnMuc29tZShyPT5yLmtleT09PW51bGwpKTsKICBvaygnYW5kIGl0cyBsaW5lIGlzIHRoaW5uZXIg'
        'dGhhbiBhIHJvdyB0aGF0IGNhbiBiZSB0YWtlbicsCiAgICAgTWF0aC5taW4oLi4ucnMubWFwKHI9'
        'PnIuaCkpIDwgTWF0aC5tYXgoLi4ucnMubWFwKHI9PnIuaCkpKTsKICBXLnJ1bignc2V0UmVhcm1N'
        'ZW51KGZhbHNlKTsgc2NvcmU9MCcpOwp9Cgpjb25zb2xlLmxvZygnVGhlIHRpdGxlIHNjcmVlbicp'
        'OwovLyBkcmF3VGl0bGUgaXMgdG9vIHRhbmdsZWQgdXAgd2l0aCB0aGUgYmFja2Ryb3AgdG8gcnVu'
        'IGhlcmUsIHNvIHdoYXQgaXMKLy8gY2hlY2tlZCBpcyB0aGUgdHdvIHRoaW5ncyB0aGF0IG1hZGUg'
        'aXQgbG9vayB0aGUgd2F5IGl0IGRpZC4Kb2soJ25vIG9wYXF1ZSBzaGVldCBvdmVyIHRoZSBza3kg'
        'YW55IG1vcmUnLCAhL2ZpbGxTdHlsZT0ncmdiYVwoMCwwLDgsMFwuNzhcKSc7Y3R4XC5maWxsUmVj'
        'dFwoMCwwLFcsSFwpLy50ZXN0KHNyYykpOwpvaygnd2hhdCBpcyBsZWZ0IGlzIGEgZ3JhZGllbnQs'
        'IHNvIHRoZSBiYWNrZHJvcCBzaG93cyB0aHJvdWdoIHRoZSB0b3AnLAogICAvY3JlYXRlTGluZWFy'
        'R3JhZGllbnRcKDAsIDAsIDAsIEhcKVtcc1xTXXswLDI2MH0/cmdiYVwoMCwwLDgsMFwuMjBcKS8u'
        'dGVzdChzcmMpKTsKb2soJ3RoZSBwYXN0ZWQgbG9nbyBhbmQgaXRzIDMgYXJlIGdvbmUnLAogICAh'
        'L19sb2dvUHJvY2Vzc2VkLy50ZXN0KHNyYykgJiYgIS9mc19sb2dvLy50ZXN0KHNyYykpOwpvaygn'
        'dGhlIHRpdGxlIGlzIHNldCBpbiB0aGUgdGhlbWUgZmFjZSBpbnN0ZWFkJywgL0ZSRUVTUEFDRS8u'
        'dGVzdChzcmMpICYmIC90aExhYmVsXCg1NFwpLy50ZXN0KHNyYykpOwpvaygnYSBmcmVzaCBiYWNr'
        'ZHJvcCBpcyByb2xsZWQgZXZlcnkgdGltZSB0aGUgdGl0bGUgY29tZXMgdXAnLAogICAvZnVuY3Rp'
        'b24gZW50ZXJUaXRsZVwoXClce1tcc1xTXXswLDMwMH0/bmViQ3VyID0gTkVCX05BTUVTW1xzXFNd'
        'ezAsMTIwfT9yb2xsQm9kaWVzXChcKS8udGVzdChzcmMpKTsKb2soJ2FuZCBhIGJvZHkgdGhhdCBs'
        'ZWF2ZXMgdGhlIHRpdGxlIGlzIHJlcGxhY2VkLCBub3Qgd3JhcHBlZCByb3VuZCcsCiAgIC9pZlwo'
        'R1M9PT0ndGl0bGUnXClceyByb2xsQm9kaWVzXChcKTsgcmV0dXJuOyBcfS8udGVzdChzcmMpKTsK'
        'b2soJ3RoZSB0aXRsZSBrZWVwcyBtb3Zpbmcgd2hpbGUgaXQgc2l0cyB0aGVyZScsCiAgIC9pZlwo'
        'R1M9PT0ndGl0bGUnXClceyBmY1wrXCs7IHRpY2tTdGFyc1woXCk7IHRpY2tOZWJ1bGFcKFwpOyBy'
        'ZXR1cm47IFx9Ly50ZXN0KHNyYykpOwpvaygnVHJ5IEFnYWluIGdvZXMgYmFjayB0byB0aGUgdGl0'
        'bGUgcmF0aGVyIHRoYW4gaW50byB0aGUgbmV4dCBydW4nLAogICAvZnVuY3Rpb24gdG9UaXRsZU9y'
        'TGF1bmNoXChcKVx7W1xzXFNdezAsMTYwfT9HUz09PSdnYW1lb3ZlcidcKXsgZW50ZXJUaXRsZVwo'
        'XCkvLnRlc3Qoc3JjKSk7Cm9rKCdhbmQgbm90aGluZyBjYWxscyBsYXVuY2hHYW1lIHN0cmFpZ2h0'
        'IGZyb20gdGhlIGdhbWUgb3ZlciBzY3JlZW4nLAogICAhL2dhbWVPdmVyQXQ+MTUwMFwpIGxhdW5j'
        'aEdhbWVcKFwpLy50ZXN0KHNyYykpOwoKY29uc29sZS5sb2coJ0JhciBidXR0b24gcGxhY2VtZW50'
        'Jyk7CnsKICAvLyBUaGUgc2hpcCBzd2l0Y2ggYW5kIHRoZSByZWFybSBidXR0b24gYXJlIGRyYXdu'
        'IGFzIG9uZSBwYWlyIG5vdywgc28gdGhlCiAgLy8gc25pcHBldCBjb3ZlcnMgYm90aCBhbmQgYm90'
        'aCBhcmUgY2hlY2tlZC4KICBjb25zdCBhID0gc3JjLmluZGV4T2YoJyAgLy8gU0hJUCBTV0lUQ0gg'
        'YW5kIFJFQVJNJyksIGIgPSBzcmMuaW5kZXhPZignICAvLyBTRVRUSU5HUyBhbmQgUEFVU0UnKTsK'
        'ICBjb25zdCBzbmlwID0gc3JjLnNsaWNlKGEsIGIpOwogIFcucnVuKCJ2YXIgSDI9NTQ7IHNoaXBN'
        'ZW51PWZhbHNlOyByZWFybU1lbnU9ZmFsc2U7IGFsbGllcz1bXTsiCiAgICAgICsgIiB3aW5kb3cu'
        'X3NoaXBCdG5SZWN0PXVuZGVmaW5lZDsgd2luZG93Ll9yZWFybUJ0blJlY3Q9dW5kZWZpbmVkOyAi'
        'ICsgc25pcCk7CiAgY29uc3QgciA9IFcucnVuKCd3aW5kb3cuX3NoaXBCdG5SZWN0JyksIHJtID0g'
        'Vy5ydW4oJ3dpbmRvdy5fcmVhcm1CdG5SZWN0Jyk7CiAgb2soJ3RoZSBzaGlwIGJ1dHRvbiBzaXRz'
        'IGJldHdlZW4gdGlja2V0cyAoNjY1KSBhbmQgZ2VhciAoNzQ4KScsIHIgJiYgci54PjY2NSAmJiBy'
        'Lngrci53PDc0OCk7CiAgb2soJ3RoZSByZWFybSBidXR0b24gc2l0cyBiZXNpZGUgaXQsIGFsc28g'
        'Y2xlYXIgb2YgdGhlIGdlYXInLAogICAgIHJtICYmIHJtLnggPj0gci54K3IudyAmJiBybS54K3Jt'
        'LncgPCA3NDgpOwogIG9rKCd0aGV5IGRvIG5vdCBvdmVybGFwJywgcm0gJiYgcm0ueCA+PSByLngg'
        'KyByLncpOwogIFcucnVuKCJGUzFfTU9ERT10cnVlOyAiICsgc25pcCk7CiAgb2soJ25laXRoZXIg'
        'YnV0dG9uIGluIEZTMSBtb2RlJywKICAgICBXLnJ1bignd2luZG93Ll9zaGlwQnRuUmVjdCcpPT09'
        'bnVsbCAmJiBXLnJ1bignd2luZG93Ll9yZWFybUJ0blJlY3QnKT09PW51bGwpOwogIFcucnVuKCdG'
        'UzFfTU9ERT1mYWxzZScpOwp9CmNvbnNvbGUubG9nKCdDeWNsZSBzY2FsaW5nIGtlZXBzIHRoZSBo'
        'dWxsJyk7Cm9rKCduZXh0V2F2ZSBzY2FsZXMgZnJvbSB0aGUgaHVsbCBiYXNlLCBub3QgZnJvbSAx'
        'MDAnLCBzcmMuaW5jbHVkZXMoJ3BsYXllci5tYXhIcD1NYXRoLnJvdW5kKChwbGF5ZXIuYmFzZUhw'
        'fHwxMDApKnBtKTsnKSk7Cm9rKCdyZXNwYXduIHJlc3RvcmVzIHRoZSBmdWxsIGh1bGwnLCBzcmMu'
        'aW5jbHVkZXMoJ3BsYXllci5ocD1wbGF5ZXIubWF4SHA7cGxheWVyLng9ODA7JykpOwoKY29uc29s'
        'ZS5sb2coJ1xuJyArIChmYWlscyA/IGZhaWxzKycgRkFJTEVEJyA6ICdhbGwgcGFzc2VkJykpOwpw'
        'cm9jZXNzLmV4aXQoZmFpbHM/MTowKTsK'
    ),
    'swtest.js': (
        'Ly8gTWlzc2lvbiBkYXRhIHRlc3QuIFJlYnVpbHQgaW4gdjEwMiBmcm9tIHRoZSBoYW5kb2ZmIGRl'
        'c2NyaXB0aW9uLCB0aGUKLy8gb3JpZ2luYWwgZmlsZSB3YXMgbG9zdC4gUmVhZHMgU0NSSVBUX1dB'
        'VkVTIGFuZCB0aGUga25vd24gdHJpZ2dlcnMsCi8vIGVmZmVjdHMgYW5kIGNhdGVnb3JpZXMgc3Ry'
        'YWlnaHQgb3V0IG9mIHRoZSBsb2dpYyBmaWxlLCBzbyBpdCBjYW4gbmV2ZXIKLy8gZHJpZnQgZnJv'
        'bSB3aGF0IHRoZSBnYW1lIGFjdHVhbGx5IGFjY2VwdHMuCi8vIFVzYWdlOiBub2RlIHN3dGVzdC5q'
        'cyBobHBfc2hvb3Rlcl92MTAyX2xvZ2ljLmh0bWwKY29uc3QgZnMgPSByZXF1aXJlKCdmcycpOwpj'
        'b25zdCBodG1sID0gZnMucmVhZEZpbGVTeW5jKHByb2Nlc3MuYXJndlsyXSB8fCAnaGxwX3Nob290'
        'ZXJfdjEwMl9sb2dpYy5odG1sJywgJ3V0ZjgnKTsKY29uc3Qgc3JjID0gaHRtbC5tYXRjaCgvPHNj'
        'cmlwdFtePl0qPihbXHNcU10qKTxcL3NjcmlwdD4vKVsxXTsKCi8vIEJyYWNlIG1hdGNoaW5nIHRo'
        'YXQgc2tpcHMgc3RyaW5ncyBhbmQgY29tbWVudHMuCmZ1bmN0aW9uIGJsb2NrRW5kKGZyb20pewog'
        'IGxldCBpID0gc3JjLmluZGV4T2YoJ3snLCBmcm9tKSwgZCA9IDA7CiAgZm9yKDsgaSA8IHNyYy5s'
        'ZW5ndGg7IGkrKyl7CiAgICBjb25zdCBjaCA9IHNyY1tpXSwgbnggPSBzcmNbaSsxXTsKICAgIGlm'
        'KGNoID09PSAnLycgJiYgbnggPT09ICcvJyl7IGkgPSBzcmMuaW5kZXhPZignXG4nLCBpKTsgY29u'
        'dGludWU7IH0KICAgIGlmKGNoID09PSAnLycgJiYgbnggPT09ICcqJyl7IGkgPSBzcmMuaW5kZXhP'
        'ZignKi8nLCBpKSArIDE7IGNvbnRpbnVlOyB9CiAgICBpZihjaCA9PT0gJyInIHx8IGNoID09PSAi'
        'JyIgfHwgY2ggPT09ICdgJyl7CiAgICAgIGNvbnN0IHEgPSBjaDsgaSsrOwogICAgICB3aGlsZShz'
        'cmNbaV0gIT09IHEpeyBpZihzcmNbaV0gPT09ICdcXCcpIGkrKzsgaSsrOyB9CiAgICAgIGNvbnRp'
        'bnVlOwogICAgfQogICAgaWYoY2ggPT09ICd7JykgZCsrOwogICAgZWxzZSBpZihjaCA9PT0gJ30n'
        'KXsgZC0tOyBpZihkID09PSAwKSByZXR1cm4gaSArIDE7IH0KICB9CiAgdGhyb3cgbmV3IEVycm9y'
        'KCd1bmJhbGFuY2VkIGF0ICcgKyBmcm9tKTsKfQpmdW5jdGlvbiBib2R5KGhlYWQpewogIGNvbnN0'
        'IGF0ID0gc3JjLmluZGV4T2YoaGVhZCk7CiAgaWYoYXQgPCAwKSB0aHJvdyBuZXcgRXJyb3IoJ21p'
        'c3Npbmc6ICcgKyBoZWFkKTsKICByZXR1cm4gc3JjLnNsaWNlKGF0LCBibG9ja0VuZChhdCkpOwp9'
        'CmNvbnN0IGNhc2VzT2YgPSB0eHQgPT4gbmV3IFNldChbLi4udHh0Lm1hdGNoQWxsKC9jYXNlXHMr'
        'JyhcdyspJy9nKV0ubWFwKG0gPT4gbVsxXSkpOwoKY29uc3QgVFJJR0dFUlMgPSBjYXNlc09mKGJv'
        'ZHkoJ2Z1bmN0aW9uIGV2VHJpZygnKSk7CmNvbnN0IEVGRkVDVFMgID0gY2FzZXNPZihib2R5KCdm'
        'dW5jdGlvbiBldkZpcmUoJykpOwpjb25zdCBDQVRfRklYICA9IGV2YWwoJygnICsgYm9keSgnY29u'
        'c3QgQ0FUX0ZJWCA9JykucmVwbGFjZSgvXmNvbnN0IENBVF9GSVggPVxzKi8sICcnKSArICcpJyk7'
        'CmNvbnN0IENBVF9GQUMgID0gZXZhbCgnKCcgKyBib2R5KCdjb25zdCBDQVRfRkFDID0nKS5yZXBs'
        'YWNlKC9eY29uc3QgQ0FUX0ZBQyA9XHMqLywgJycpICsgJyknKTsKY29uc3QgVyA9IDgwMCwgSCA9'
        'IDUwMCwgSFVEX0ggPSA0NCwgVElDS19IWiA9IDEwMDsKLy8gRXZlcnkgaHVsbCBhIG1pc3Npb24g'
        'bmFtZXMgaGFzIHRvIGV4aXN0LiBBIG1pc3NwZWx0IGtleSBzcGF3bnMgbm90aGluZywKLy8gb3Ig'
        'YSBzaGlwIG9mIHRoZSB3cm9uZyBzaXplLCBhbmQgc2F5cyBub3RoaW5nIGFib3V0IGl0Lgpjb25z'
        'dCBIVUxMX0tFWVMgPSBuZXcgU2V0KE9iamVjdC5rZXlzKGV2YWwoJygnICsgc3JjLm1hdGNoKC9j'
        'b25zdCBIVUxMX0xFTiA9IChce1tefV0qXH0pLylbMV0gKyAnKScpKSk7Ci8vIFdoaWNoIGZhY3Rp'
        'b24gZWFjaCBibG9jayBvZiBtaXNzaW9ucyBpcyBmb3VnaHQgYWdhaW5zdC4KY29uc3QgQ1lDTEVf'
        'RkFDID0gbiA9PiBuIDw9IDMwID8gJ2hvbCcgOiBuIDw9IDYwID8gJ250ZicgOiAnc2hpdmFuJzsK'
        'Y29uc3QgU0NSSVBUX1dBVkVTID0gZXZhbCgnKCcgKyBib2R5KCdjb25zdCBTQ1JJUFRfV0FWRVMg'
        'PScpLnJlcGxhY2UoL15jb25zdCBTQ1JJUFRfV0FWRVMgPVxzKi8sICcnKSArICcpJyk7CgovLyBU'
        'cmlnZ2VycyB3aXRob3V0IGEgdW5pdCBhcyB0YXJnZXQsIGFuZCBlZmZlY3RzIHdob3NlIGFyZ3Vt'
        'ZW50IGlzIGEgdW5pdC4KY29uc3QgVFJJR19OT19JRCAgPSBuZXcgU2V0KFsnc2VrJywgJ2VyZnVl'
        'bGx0J10pOwpjb25zdCBFRkZFQ1RfVU5JVCA9IG5ldyBTZXQoWydlaW53YXJwZW4nLCAnc2VpdGUn'
        'LCAncmF1cycsICdoZWlsZW4nXSk7CgpsZXQgZXJyb3JzID0gMCwgbWlzc2lvbnMgPSAwOwpmb3Io'
        'Y29uc3Qga2V5IG9mIE9iamVjdC5rZXlzKFNDUklQVF9XQVZFUykuc29ydCgoYSwgYikgPT4gYSAt'
        'IGIpKXsKICBjb25zdCBtID0gU0NSSVBUX1dBVkVTW2tleV0sIHVuaXRzID0gbS51IHx8IFtdLCBl'
        'dnMgPSBtLmV2IHx8IFtdOwogIGNvbnN0IHRhZyA9ICdNJyArIFN0cmluZyhrZXkpLnBhZFN0YXJ0'
        'KDMsICcwJyk7CiAgY29uc3QgaWRzID0gbmV3IE1hcCgpOwogIGNvbnN0IGJhZCA9IFtdOwogIG1p'
        'c3Npb25zKys7CgogIGZvcihjb25zdCB1IG9mIHVuaXRzKXsKICAgIGlmKCF1LmlkKSBiYWQucHVz'
        'aCgndW5pdCB3aXRob3V0IGlkICgnICsgdS5jICsgJyknKTsKICAgIGVsc2UgaWYoaWRzLmhhcyh1'
        'LmlkKSkgYmFkLnB1c2goJ2lkIHVzZWQgdHdpY2U6ICcgKyB1LmlkKTsKICAgIGlkcy5zZXQodS5p'
        'ZCwgdSk7CiAgICBpZighQ0FUX0ZBQ1t1LmNdICYmICFDQVRfRklYW3UuY10pCiAgICAgIGJhZC5w'
        'dXNoKHUuaWQgKyAnOiB1bmtub3duIGNhdGVnb3J5ICInICsgdS5jICsgJyIgLSB3b3VsZCBuZXZl'
        'ciBzcGF3bicpOwogIH0KICBmb3IoY29uc3QgdSBvZiB1bml0cykKICAgIGlmKHUuc3ByICYmICFI'
        'VUxMX0tFWVMuaGFzKHUuc3ByKSkgYmFkLnB1c2godS5pZCArICc6IHVua25vd24gaHVsbCAiJyAr'
        'IHUuc3ByICsgJyInKTsKICBpZihtLmZhYyAhPT0gQ1lDTEVfRkFDKCtrZXkpKSBiYWQucHVzaCgn'
        'ZmFjdGlvbiAnICsgbS5mYWMgKyAnLCBidXQgdGhpcyB3YXZlIGJlbG9uZ3MgdG8gdGhlICcgKyBD'
        'WUNMRV9GQUMoK2tleSkgKyAnIGN5Y2xlJyk7CiAgZm9yKGNvbnN0IHUgb2YgdW5pdHMpewogICAg'
        'aWYodS5kb2NrVG8gJiYgIWlkcy5oYXModS5kb2NrVG8pKSBiYWQucHVzaCh1LmlkICsgJzogZG9j'
        'a1RvIHBvaW50cyBhdCBtaXNzaW5nIGlkICcgKyB1LmRvY2tUbyk7CiAgICBpZih1LmF0ICYmICFp'
        'ZHMuaGFzKHUuYXQpKSAgICAgICAgIGJhZC5wdXNoKHUuaWQgKyAnOiBhdCBwb2ludHMgYXQgbWlz'
        'c2luZyBpZCAnICsgdS5hdCk7CiAgfQoKICBjb25zdCB3YXJwZWRJbiA9IG5ldyBTZXQoKTsKICBs'
        'ZXQgcmVpbmZPbiA9IGZhbHNlLCByZWluZk9mZiA9IGZhbHNlOwogIGV2cy5mb3JFYWNoKChlLCBp'
        'KSA9PiB7CiAgICBjb25zdCB3aGVyZSA9ICdldmVudCAnICsgKGkgKyAxKSArICcgKCcgKyBlLnQg'
        'KyAnIC0+ICcgKyBlLncgKyAnKSc7CiAgICBjb25zdCBhcmcgPSAoZS5hMiAhPT0gdW5kZWZpbmVk'
        'KSA/IGUuYTIgOiBlLmE7CiAgICBpZighVFJJR0dFUlMuaGFzKGUudCkpIGJhZC5wdXNoKHdoZXJl'
        'ICsgJzogdW5rbm93biB0cmlnZ2VyICInICsgZS50ICsgJyInKTsKICAgIGlmKCFFRkZFQ1RTLmhh'
        'cyhlLncpKSAgYmFkLnB1c2god2hlcmUgKyAnOiB1bmtub3duIGVmZmVjdCAiJyArIGUudyArICci'
        'Jyk7CiAgICBpZihUUklHR0VSUy5oYXMoZS50KSAmJiAhVFJJR19OT19JRC5oYXMoZS50KSAmJiAh'
        'aWRzLmhhcyhlLmEpKQogICAgICBiYWQucHVzaCh3aGVyZSArICc6IHRyaWdnZXIgcG9pbnRzIGF0'
        'IG1pc3NpbmcgaWQgJyArIGUuYSk7CiAgICBpZihlLnQgPT09ICdhbmdlZG9ja3QnICYmIGlkcy5o'
        'YXMoZS5hKSAmJiAhaWRzLmdldChlLmEpLmRvY2tUbykKICAgICAgYmFkLnB1c2god2hlcmUgKyAn'
        'OiAnICsgZS5hICsgJyBoYXMgbm8gZG9ja1RvLCBpdCBjYW4gbmV2ZXIgZG9jaycpOwogICAgaWYo'
        'RUZGRUNUX1VOSVQuaGFzKGUudykgJiYgIWlkcy5oYXMoYXJnKSkKICAgICAgYmFkLnB1c2god2hl'
        'cmUgKyAnOiBlZmZlY3QgcG9pbnRzIGF0IG1pc3NpbmcgaWQgJyArIGFyZyk7CiAgICBpZihlLncg'
        'PT09ICdqYWdkJyAmJiBhcmcgJiYgIWlkcy5oYXMoYXJnKSkKICAgICAgYmFkLnB1c2god2hlcmUg'
        'KyAnOiBodW50IHRhcmdldCBpcyBhIG1pc3NpbmcgaWQgJyArIGFyZyk7CiAgICBpZihlLncgPT09'
        'ICdlaW53YXJwZW4nKXsKICAgICAgd2FycGVkSW4uYWRkKGFyZyk7CiAgICAgIGlmKGlkcy5oYXMo'
        'YXJnKSAmJiAhaWRzLmdldChhcmcpLndhaXQpCiAgICAgICAgYmFkLnB1c2god2hlcmUgKyAnOiAn'
        'ICsgYXJnICsgJyBpcyBub3Qgd2FpdGluZyAtIHdhcnBpbmcgaXQgaW4gZG9lcyBub3RoaW5nJyk7'
        'CiAgICB9CiAgICBpZihlLncgPT09ICduYWNoc2NodWInKXsgaWYoYXJnID09PSAnYXVzJykgcmVp'
        'bmZPZmYgPSB0cnVlOyBlbHNlIHJlaW5mT24gPSB0cnVlOyB9CiAgICBpZihlLncgPT09ICdlbmRl'
        'JykgcmVpbmZPZmYgPSB0cnVlOwogIH0pOwogIGZvcihjb25zdCB1IG9mIHVuaXRzKQogICAgaWYo'
        'dS53YWl0ICYmICF3YXJwZWRJbi5oYXModS5pZCkpIGJhZC5wdXNoKHUuaWQgKyAnOiB3YWl0cywg'
        'YnV0IG5vIGV2ZW50IGV2ZXIgd2FycHMgaXQgaW4nKTsKICBpZihyZWluZk9uICYmICFyZWluZk9m'
        'ZikgYmFkLnB1c2goJ3JlaW5mb3JjZW1lbnRzIHN3aXRjaGVkIG9uLCBuZXZlciBzd2l0Y2hlZCBv'
        'ZmYnKTsKICBpZihtLmh1bnQgJiYgIWlkcy5oYXMobS5odW50KSkgYmFkLnB1c2goJ2h1bnQgcG9p'
        'bnRzIGF0IG1pc3NpbmcgaWQgJyArIG0uaHVudCk7CgogIGlmKGJhZC5sZW5ndGgpeyBlcnJvcnMg'
        'Kz0gYmFkLmxlbmd0aDsgY29uc29sZS5sb2codGFnICsgJyAnICsgKG0ubmFtZSB8fCAnJykpOyBi'
        'YWQuZm9yRWFjaChiID0+IGNvbnNvbGUubG9nKCcgICAnICsgYikpOyB9Cn0KY29uc29sZS5sb2co'
        'J1xuJyArIG1pc3Npb25zICsgJyBtaXNzaW9ucyBjaGVja2VkLCAnICsgZXJyb3JzICsgJyBwcm9i'
        'bGVtcycpOwpjb25zb2xlLmxvZygna25vd24gdHJpZ2dlcnM6ICcgKyBbLi4uVFJJR0dFUlNdLmpv'
        'aW4oJyAnKSk7CmNvbnNvbGUubG9nKCdrbm93biBlZmZlY3RzOiAgJyArIFsuLi5FRkZFQ1RTXS5q'
        'b2luKCcgJykpOwpwcm9jZXNzLmV4aXQoZXJyb3JzID8gMSA6IDApOwo='
    ),
    'fieldsim.js': (
        'Ly8gRmllbGQgc2ltdWxhdGlvbjogcnVucyB0aGUgUkVBTCBnYW1lIGluIGEgaGVhZGxlc3MgYnJv'
        'd3Nlci4KLy8KLy8gVGhlIG90aGVyIHNpbXVsYXRpb25zIGxpZnQgc2luZ2xlIGZ1bmN0aW9ucyBv'
        'dXQgb2YgdGhlIGxvZ2ljIGZpbGUuIFRoaXMgb25lCi8vIGxvYWRzIHRoZSB3aG9sZSBmaWxlLCBz'
        'dGFydHMgYSByZWFsIHJ1biB3aXRoID9tPU5OIGFuZCBzdGVwcyB0aGUgcmVhbAovLyB1cGRhdGUo'
        'KSAtIHNwYXduIHF1ZXVlLCBldmVudHMsIGFsbGllZCBhbmQgZW5lbXkgZmxpZ2h0LCB0aGUgbG90'
        'LiBUaGF0IGlzCi8vIHRoZSBwYXJ0IHRoZSBvdGhlcnMgY2Fubm90IHNlZTogd2hldGhlciBhIG1p'
        'c3Npb24gYWN0dWFsbHkgcGxheXMgb3V0LgovLwovLyBObyBzcHJpdGVzIGFyZSBlbWJlZGRlZCBp'
        'biBhIGxvZ2ljIGZpbGUsIHNvIGV2ZXJ5IGh1bGwgZ2V0cyBhIHBsYWluIG9wYXF1ZQovLyBzdGFu'
        'ZC1pbiBvZiBhIGZpdHRpbmcgc2hhcGUsIGFuZCB0aGUgbW91bnQgZGF0YSBpcyBwdXQgaW4gdGhl'
        'IHdheSB0aGUKLy8gcGFja2VyIHB1dHMgaXQgaW4uIFRoZSBwbGF5ZXIgY2Fubm90IGRpZTsgdGhl'
        'IHNjZW5hcmlvcyBkZWNpZGUgd2hhdCBnZXRzCi8vIHNob3QgZG93biwgYW5kIHdoZW4uCi8vCi8v'
        'IE5lZWRzIFBsYXl3cmlnaHQgd2l0aCBDaHJvbWl1bSAoaXQgcnVucyB3aGVyZSB0aGUgYnVpbGQg'
        'aXMgY2hlY2tlZCwgbm90IG9uCi8vIHRoZSBzZXJ2ZXIpLgovLyBVc2FnZTogbm9kZSBmaWVsZHNp'
        'bS5qcyA8bG9naWMuaHRtbD4gW2hscF9tb3VudHNfZmluYWwuanNvbl0KY29uc3QgZnMgPSByZXF1'
        'aXJlKCdmcycpLCBwYXRoID0gcmVxdWlyZSgncGF0aCcpLCBvcyA9IHJlcXVpcmUoJ29zJyk7CmNv'
        'bnN0IHsgZXhlY1N5bmMgfSA9IHJlcXVpcmUoJ2NoaWxkX3Byb2Nlc3MnKTsKY29uc3QgUFcgPSBw'
        'YXRoLmpvaW4oZXhlY1N5bmMoJ25wbSByb290IC1nJykudG9TdHJpbmcoKS50cmltKCksICdwbGF5'
        'd3JpZ2h0Jyk7CmNvbnN0IHsgY2hyb21pdW0gfSA9IHJlcXVpcmUoUFcpOwoKY29uc3QgbG9naWMg'
        'PSBwcm9jZXNzLmFyZ3ZbMl07CmNvbnN0IG1vdW50cyA9IHByb2Nlc3MuYXJndlszXSB8fCAnaGxw'
        'X21vdW50c19maW5hbC5qc29uJzsKbGV0IGh0bWwgPSBmcy5yZWFkRmlsZVN5bmMobG9naWMsICd1'
        'dGY4Jyk7CmNvbnN0IE0gPSBmcy5yZWFkRmlsZVN5bmMobW91bnRzLCAndXRmOCcpOwovLyBTYW1l'
        'IHNoYXBlIGFzIGJ1aWxkX2dhbWUucHkncyByZW5kZXJfbW91bnRzKCksIHBsYWNlZCBmaXJzdCBz'
        'byBpdCBleGlzdHMKLy8gYmVmb3JlIGFueXRoaW5nIGFza3MgZm9yIGl0LgpodG1sID0gaHRtbC5y'
        'ZXBsYWNlKC88c2NyaXB0KFtePl0qKT4vLCAnPHNjcmlwdCQxPlxuY29uc3QgTU9VTlRTPScgKyBK'
        'U09OLnN0cmluZ2lmeShKU09OLnBhcnNlKE0pKSArICc7XG4nKTsKY29uc3QgdG1wID0gcGF0aC5q'
        'b2luKG9zLnRtcGRpcigpLCAnZmllbGRzaW1fJyArIHByb2Nlc3MucGlkICsgJy5odG1sJyk7CmZz'
        'LndyaXRlRmlsZVN5bmModG1wLCBodG1sKTsKCi8vIEluLXBhZ2UgaGVscGVycy4gRXZlcnl0aGlu'
        'ZyBoZXJlIHJ1bnMgYWdhaW5zdCB0aGUgZ2FtZSdzIG93biBnbG9iYWxzLgpjb25zdCBIRUxQRVJT'
        'ID0gYAogIHdpbmRvdy5GUyA9IHsKICAgIGZha2VJbWFnZXMoKXsKICAgICAgZm9yKGNvbnN0IGsg'
        'b2YgT2JqZWN0LmtleXMoSFVMTF9MRU4pKXsKICAgICAgICBjb25zdCBzbWFsbCA9IC9eKGZpfGJv'
        'fHNnfGZjfGVwKS8udGVzdChrKSAmJiBIVUxMX0xFTltrXSA8IDgwOwogICAgICAgIGNvbnN0IGMg'
        'PSBkb2N1bWVudC5jcmVhdGVFbGVtZW50KCdjYW52YXMnKTsKICAgICAgICBjLndpZHRoID0gc21h'
        'bGwgPyA2MCA6IDMyMDsgYy5oZWlnaHQgPSBzbWFsbCA/IDQwIDogOTA7CiAgICAgICAgY29uc3Qg'
        'ZyA9IGMuZ2V0Q29udGV4dCgnMmQnKTsgZy5maWxsU3R5bGUgPSAnIzg4OCc7IGcuZmlsbFJlY3Qo'
        'MCwwLGMud2lkdGgsYy5oZWlnaHQpOwogICAgICAgIElNR1Nba10gPSBjOwogICAgICB9CiAgICB9'
        'LAogICAgc3RlcChuKXsgZm9yKGxldCBpPTA7aTxuO2krKyl7IHBsYXllci5ocCA9IHBsYXllci5t'
        'YXhIcDsgcGxheWVyLnNoID0gcGxheWVyLm1heFNoOwogICAgICAgICAgICAgaWYodHlwZW9mIGxp'
        'dmVzIT09J3VuZGVmaW5lZCcpIGxpdmVzID0gMzsgdXBkYXRlKCk7IGlmKGklMjU9PT0wKSBkcmF3'
        'KCk7IH0gfSwKICAgIC8vIFNob290IGRvd24gZXZlcnkgZW5lbXkgZmlnaHRlciBhbmQgYm9tYmVy'
        'IHRoYXQgaXMgb3V0IG9mIGl0cyB2b3J0ZXguCiAgICBraWxsU21hbGwoKXsgZm9yKGNvbnN0IGUg'
        'b2YgZW5lbWllcykgaWYoKGUudHlwZT09PSdmaWdodGVyJ3x8ZS50eXBlPT09J2JvbWJlcicpICYm'
        'ICEoZS53YXJwPjApKSBlLmhwID0gMDsgfSwKICAgIGtpbGxJZChpZCl7IGZvcihjb25zdCBlIG9m'
        'IGVuZW1pZXMpIGlmKGUudWlkPT09aWQgJiYgIShlLndhcnA+MCkpIGUuaHAgPSAwOyB9LAogICAg'
        'Ly8gU3RlcCB1bnRpbCBjb25kKCkgaG9sZHMsIGNsZWFyaW5nIHNtYWxsIGNyYWZ0IGV2ZXJ5IHNv'
        'IG9mdGVuLgogICAgdW50aWwoY29uZCwgbWF4LCBjbGVhciwgYWxsKXsgZm9yKGxldCB0PTA7dDxt'
        'YXg7dCs9MjApeyBpZihjb25kKCkpIHJldHVybiB0OwogICAgICAgICAgICAgaWYoY2xlYXIgJiYg'
        'dCUyMDA9PT0wKSBGUy5raWxsU21hbGwoKTsKICAgICAgICAgICAgIGlmKGFsbCAmJiB0JTIwMD09'
        'PTApIGZvcihjb25zdCBlIG9mIGVuZW1pZXMpIGlmKCEoZS53YXJwPjApICYmICFlLmludnVsbiAm'
        'JiAhZS5zY2VuZXJ5KSBlLmhwID0gMDsKICAgICAgICAgICAgIEZTLnN0ZXAoMjApOyB9IHJldHVy'
        'biAtMTsgfSwKICAgIGlkcyhpZCl7IHJldHVybiBieUlkKGlkKTsgfSwKICAgIGVuZW15SWRzKCl7'
        'IHJldHVybiBlbmVtaWVzLm1hcChlPT5lLnVpZHx8ZS50eXBlKTsgfSwKICAgIGFsbHlJZHMoKXsg'
        'cmV0dXJuIGFsbGllcy5tYXAoYT0+YS51aWR8fGEudHlwZSk7IH0KICB9O2A7Cgpjb25zdCBzY2Vu'
        'YXJpb3MgPSBbXTsKZnVuY3Rpb24gc2NlbmFyaW8obmFtZSwgcXVlcnksIGJvZHkpeyBzY2VuYXJp'
        'b3MucHVzaCh7bmFtZSwgcXVlcnksIGJvZHl9KTsgfQoKLy8g4pSA4pSAIFNjZW5hcmlvcyDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAK'
        'c2NlbmFyaW8oJ00zMSBEZXIgQXVmc3RhbmQnLCAnbT0zMScsIGAKICBjb25zdCByID0ge307CiAg'
        'ci53YXZlID0gd2F2ZTsgci5zaGlwID0gcGxheWVyLnNoaXA7CiAgci50ZXJyYW5DYWxsID0gQUxM'
        'WV9GQUNfT04udGVycmFuPT09dHJ1ZSAmJiBBTExZX0ZBQ19PTi52YXN1ZGFuPT09ZmFsc2U7CiAg'
        'RlMuc3RlcCg0MDApOwogIGNvbnN0IGEgPSBhbGxpZXMuZmluZCh4PT54LnVpZD09PSdBMScpOwog'
        'IHIuYWxseUF0U3RhcnQgPSAhIWEgJiYgYS5pbWc9PT0nY3JsZXZpYXRoYW4nOwogIHIubG9ja1Nl'
        'dCA9ICEhYSAmJiBhLmRlZmVjdExvY2s9PT10cnVlOwogIC8vIEhhbW1lciBoZXIgd2hpbGUgc2hl'
        'IGlzIHN0aWxsIG91cnM6IHNoZSBtdXN0IG5vdCBkaWUgYmVmb3JlIHRoZSB0dXJuLgogIGlmKGEp'
        'eyBhLmhwID0gMTsgRlMuc3RlcCg1KTsgfQogIHIuc3Vydml2ZXNMb2NrID0gISFhbGxpZXMuZmlu'
        'ZCh4PT54LnVpZD09PSdBMScpOwogIEZTLnVudGlsKCgpPT4hZW5lbWllcy5zb21lKGU9PmUudWlk'
        'PT09J0UxJykgJiYgIXNwYXduUS5zb21lKHE9PnEudWlkPT09J0UxJyksIDYwMDAsIHRydWUpOwog'
        'IEZTLnN0ZXAoNDApOwogIGNvbnN0IGUgPSBlbmVtaWVzLmZpbmQoeD0+eC51aWQ9PT0nQTEnKTsK'
        'ICByLnR1cm5lZCA9ICEhZSAmJiAhYWxsaWVzLnNvbWUoeD0+eC51aWQ9PT0nQTEnKTsKICByLm50'
        'Zkh1bGwgPSAhIWUgJiYgZS5pbWc9PT0nbnRmY3JsZXZpYXRoYW4nOwogIHIuZW5lbXlTaGFwZSA9'
        'ICEhZSAmJiBlLnR5cGU9PT0nY3J1aXNlcicgJiYgZS5zaWRlPT09J2VuZW15JyAmJiAhZS5kZWFk'
        'ICYmIGUuaHA+MDsKICByLmhhc1N1YnMgPSAhIWUgJiYgISFlLnN1YnMgJiYgZS5zdWJzLmxlbmd0'
        'aD09PTU7CiAgci5oYXNHdW5zID0gISFlICYmICEhKGUuZ3Vuc3x8ZS5tb3VudHN8fGUud3BufHxl'
        'LmJlYW1zKTsKICBGUy5zdGVwKDIwMCk7CiAgci53YXZlT3BlbldoaWxlU2hlTGl2ZXMgPSAhd2F2'
        'ZU92ZXI7CiAgRlMuc3RlcCgzMDApOwogIHIuc3RheXNPbkZpZWxkID0gISFlICYmIGUueCA+IDAg'
        'JiYgZS54IDwgVyAmJiBlLnkgPiBIVURfSCAmJiBlLnkgPCBIOwogIEZTLmtpbGxJZCgnQTEnKTsg'
        'RlMudW50aWwoKCk9PndhdmVPdmVyLCA0MDAwLCB0cnVlKTsKICByLndhdmVFbmRzID0gd2F2ZU92'
        'ZXI7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTMyIERpZSBGcmFjaHRyb3V0ZScsICdtPTMy'
        'JywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDMwMCk7CiAgY29uc3QgZiA9IGFsbGllcy5m'
        'aWx0ZXIoeD0+eC51aWQ9PT0nRjEnKTsKICByLnR3b0ZyZWlnaHRlcnMgPSBmLmxlbmd0aD09PTIg'
        'JiYgZi5ldmVyeSh4PT54LmltZz09PSdmcnBvc2VpZG9uJyk7CiAgci50ZXJyYW5TaWRlID0gZi5l'
        'dmVyeSh4PT54LmZhY3Rpb249PT0ndGVycmFuJyk7CiAgci5tZWR1c2FzID0gZW5lbWllcy5maWx0'
        'ZXIoZT0+ZS51aWQ9PT0nQjEnKS5ldmVyeShlPT5lLmltZz09PSdib21lZHVzYScpICYmIGVuZW1p'
        'ZXMuc29tZShlPT5lLnVpZD09PSdCMScpOwogIHIuZmlnaHRlckNvdmVyID0gZW5lbWllcy5zb21l'
        'KGU9PmUudWlkPT09J0UxJyAmJiBlLnR5cGU9PT0nZmlnaHRlcicpIHx8IHNwYXduUS5zb21lKHE9'
        'PnEudWlkPT09J0UxJyk7CiAgY29uc3QgeDAgPSBmLmxlbmd0aCA/IGZbMF0ueCA6IDA7IEZTLnN0'
        'ZXAoMzAwKTsKICByLmNyb3NzaW5nID0gZi5sZW5ndGg+MCAmJiBmWzBdLnggPiB4MDsKICBGUy51'
        'bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdCMScpLCA0MDAwLCB0cnVlKTsKICBG'
        'Uy5zdGVwKDMwMCk7CiAgci5zZWNvbmRSYWlkID0gZW5lbWllcy5zb21lKGU9PmUudWlkPT09J0Iy'
        'JykgfHwgc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nQjInKTsKICByLmVuZHNXaGVuVGhyb3VnaCA9'
        'IEZTLnVudGlsKCgpPT53YXZlT3ZlciwgMjAwMDAsIHRydWUpID49IDA7CiAgcmV0dXJuIHI7YCk7'
        'CgpzY2VuYXJpbygnTTMzIERpZSBSZWxhaXNzdGF0aW9uJywgJ209MzMnLCBgCiAgY29uc3QgciA9'
        'IHt9OwogIEZTLnN0ZXAoMzAwKTsKICBjb25zdCBzID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09'
        'J1MxJyk7CiAgci5mYXVzdHVzID0gISFzICYmIHMuaW1nPT09J3NjZmF1c3R1cyc7CiAgci5hdEdp'
        'dmVuSGVpZ2h0ID0gISFzICYmIE1hdGguYWJzKHMueS0yNTApIDwgMTsKICBjb25zdCB4MCA9IHMg'
        'PyBzLnggOiAwOwogIEZTLnN0ZXAoMTIwMCk7CiAgci5zdGF5c1B1dCA9ICEhcyAmJiBNYXRoLmFi'
        'cyhzLngteDApIDwgMSAmJiBNYXRoLmFicyhzLnktMjUwKSA8IDE7CiAgci5ub0ZsYWsgPSAhIXMg'
        'JiYgZmxha0hhcyhzKT09PWZhbHNlOwogIHIuZ3VucyA9IGVuZW1pZXMuZmlsdGVyKGU9PmUudWlk'
        'PT09J0cxJykubGVuZ3RoPT09NDsKICAvLyBSZWluZm9yY2VtZW50cyBrZWVwIGNvbWluZyB3aGls'
        'ZSBzaGUgc3RhbmRzLgogIEZTLmtpbGxTbWFsbCgpOyBGUy5zdGVwKDkwMCk7CiAgci5yZWluZm9y'
        'Y2VkID0gZW5lbWllcy5zb21lKGU9PmUudHlwZT09PSdmaWdodGVyJyAmJiAhZS51aWQpIHx8IHNw'
        'YXduUS5zb21lKHE9PiFxLnVpZCAmJiAvXmZpXy8udGVzdChxLnR5cGUpKTsKICBjb25zdCBiZWZv'
        'cmUgPSBTSE9DS1MubGVuZ3RoOwogIEZTLmtpbGxJZCgnUzEnKTsgRlMuc3RlcCgzKTsKICByLmJp'
        'Z0JsYXN0ID0gU0hPQ0tTLnNvbWUoaz0+ay5yTWF4PT09MzAwKTsKICBGUy5raWxsU21hbGwoKTsg'
        'RlMuc3RlcCgxMjAwKTsgRlMua2lsbFNtYWxsKCk7IEZTLnN0ZXAoNjAwKTsKICByLnJlaW5mT2Zm'
        'ID0gZXZSZWluZj09PWZhbHNlOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ00zNCBEaWUgRmxh'
        'a3dhbmQnLCAnbT0zNCcsIGAKICBjb25zdCByID0ge307CiAgc2NvcmUgPSAyMDAwMDsgICAvLyBl'
        'bm91Z2ggZm9yIHRoZSBBcnRlbWlzIHRvIGJlIG9wZW4gaW4gdGhpcyBjeWNsZQogIEZTLnN0ZXAo'
        'NDAwKTsKICBjb25zdCBrID0gZW5lbWllcy5maWx0ZXIoZT0+ZS51aWQ9PT0nSzEnKTsKICByLnR3'
        'b0Flb2x1cyA9IGsubGVuZ3RoPT09MiAmJiBrLmV2ZXJ5KGU9PmUuaW1nPT09J250ZmNyYWVvbHVz'
        'Jyk7CiAgci5mbGFrID0gay5ldmVyeShlPT5mbGFrSGFzKGUpKTsKICByLm5vSGFuZ2FyWWV0ID0g'
        'IWFsbGllcy5zb21lKGE9PmEudWlkPT09J0ExJyk7CiAgRlMudW50aWwoKCk9PiFlbmVtaWVzLnNv'
        'bWUoZT0+ZS51aWQ9PT0nRTEnKSAmJiAhc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nRTEnKSwgNTAw'
        'MCwgdHJ1ZSk7CiAgRlMuc3RlcCg0MDApOwogIGNvbnN0IG8gPSBhbGxpZXMuZmluZChhPT5hLnVp'
        'ZD09PSdBMScpOwogIHIub3Jpb24gPSAhIW8gJiYgby5pbWc9PT0nZGVvcmlvbnJpZ2h0JzsKICB0'
        'aWNrU2hpcFVubG9ja3MoKTsKICByLmJvbWJlck9mZmVyZWQgPSBzaGlwT2ZmZXJlZCgnYm9hcnRl'
        'bWlzJykgJiYgc2hpcFN3YXBSZWFkeSgpOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ00zNSBE'
        'ZXIgVWViZXJsYWV1ZmVyJywgJ209MzUnLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAoMzAw'
        'KTsKICBjb25zdCBkID0gYWxsaWVzLmZpbmQoYT0+YS51aWQ9PT0nQTEnKTsKICByLm50ZkRlaW1v'
        'cyA9ICEhZCAmJiBkLmltZz09PSdudGZjb2RlaW1vcycgJiYgZC50eXBlPT09J2NvcnZldHRlJzsK'
        'ICByLmZhY2VzUmlnaHQgPSAhIWQgJiYgZC5mbGlwPT09bmVlZHNGbGlwKCdudGZjb2RlaW1vcycs'
        'IGZhbHNlKTsKICByLmNyb3NzaW5nID0gISFkICYmIGQudHJhbnNpdD09PXRydWU7CiAgci5odW50'
        'ZWQgPSB3YXZlSHVudD09PSdBMSc7CiAgci5yZWFybSA9IGNvcnZldHRlT25GaWVsZCgpOwogIHIu'
        'bm90T25DYWxsTWVudSA9IEFMTFlfT1JERVIuaW5kZXhPZignbnRmX2RlaW1vcycpPDA7CiAgY29u'
        'c3QgZ290ID0gRlMudW50aWwoKCk9PiFhbGxpZXMuc29tZShhPT5hLnVpZD09PSdBMScpLCA5MDAw'
        'LCB0cnVlKTsKICByLmdldHNBY3Jvc3MgPSBnb3Q+PTAgJiYgIWd1YXJkTG9zdDsKICBGUy51bnRp'
        'bCgoKT0+d2F2ZU92ZXIsIDQwMDAsIHRydWUpOwogIHIud2F2ZUVuZHMgPSB3YXZlT3ZlcjsKICBy'
        'ZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNMzYgRGllIEljZW5pJywgJ209MzYnLCBgCiAgY29uc3Qg'
        'ciA9IHt9OwogIGNvbnN0IHMwID0gc2NvcmUgPSA1MDAwOwogIEZTLnN0ZXAoMzAwKTsKICBjb25z'
        'dCBpID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyk7CiAgci5pY2VuaSA9ICEhaSAmJiBp'
        'LmljZW5pPT09dHJ1ZSAmJiBpLmltZz09PSdjb2ljZW5pJzsKICByLm5vTmF2aWdhdGlvbiA9ICEh'
        'aSAmJiAhIWkuc3VicyAmJiBpLnN1YnMubGVuZ3RoPT09NCAmJiBzdWJPSyhpLCduYXZpZ2F0aW9u'
        'Jyk7CiAgci5kZWFkbGluZSA9ICEhaSAmJiBpLmZsZWVUPjAgJiYgaS5mbGVlVCA8PSAyNSpUSUNL'
        'X0haOwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdW'
        'MScpLCA2MDAwLCBmYWxzZSk7CiAgci5qdW1wc091dCA9IHQ+PTAgJiYgaWNlbkVzY2FwZXM9PT0x'
        'OwogIHIubm9QZW5hbHR5ID0gc2NvcmUgPj0gczA7CiAgci5mZW5yaXMgPSBlbmVtaWVzLnNvbWUo'
        'ZT0+ZS51aWQ9PT0nSzEnICYmIGUuaW1nPT09J250ZmNyZmVucmlzJyk7CiAgcmV0dXJuIHI7YCk7'
        'CgpzY2VuYXJpbygnQ3ljbGUgY2hhbmdlIDMwIC0+IDMxJywgJ209MzAnLCBgCiAgY29uc3QgciA9'
        'IHt9OwogIHIuc3RhcnRzVmFzdWRhbiA9IHBsYXllci5zaGlwPT09J2ZpdG90aCcgJiYgQUxMWV9G'
        'QUNfT04udmFzdWRhbj09PXRydWU7CiAgc2NvcmUgPSA5MDAwMDsKICAvLyBDbGVhciB3YXZlIDMw'
        'IGJ5IGZvcmNlIGFuZCBsZXQgdGhlIGp1bXAgaGFwcGVuLgogIGZvcihsZXQgaz0wO2s8NjAgJiYg'
        'd2F2ZT09PTMwO2srKyl7IGZvcihjb25zdCBlIG9mIGVuZW1pZXMpIGlmKCEoZS53YXJwPjApICYm'
        'ICFlLmludnVsbikgZS5ocD0wOyBGUy5zdGVwKDIwMCk7IH0KICByLndhdmUgPSB3YXZlOwogIHIu'
        'bXlybWlkb24gPSBwbGF5ZXIuc2hpcD09PSdmaW15cm1pZG9uJzsKICByLm9uZUh1bGwgPSBzaGlw'
        'VW5sb2NrZWQ9PT0xICYmIGN5Y2xlQmFzZT09PXNjb3JlIC0gKHNjb3JlLWN5Y2xlQmFzZSk7CiAg'
        'ci5iYXNlU2V0ID0gY3ljbGVCYXNlID49IDkwMDAwOwogIHIudGVycmFuID0gQUxMWV9GQUNfT04u'
        'dGVycmFuPT09dHJ1ZSAmJiBBTExZX0ZBQ19PTi52YXN1ZGFuPT09ZmFsc2U7CiAgcmV0dXJuIHI7'
        'YCk7CgpzY2VuYXJpbygnTTEzIGJvdGggdHJhbnNwb3J0cyBvbiB0aW1lJywgJ209MTMnLCBgCiAg'
        'RlMuc3RlcCgzMDApOwogIHJldHVybiB7Ym90aFRyYW5zcG9ydHM6IGFsbGllcy5maWx0ZXIoYT0+'
        'YS51aWQ9PT0nVDEnKS5sZW5ndGg9PT0yfTtgKTsKCi8vIEV2ZXJ5IHdyaXR0ZW4gbWlzc2lvbiBo'
        'YXMgdG8gY29tZSB0byBhbiBlbmQgd2hlbiBpdHMgZW5lbWllcyBnbyBkb3duLAovLyB3aXRoIG5v'
        'dGhpbmcgdGhyb3duIG9uIHRoZSB3YXkuIEVuZW15IHNoaXBzIGFyZSBjbGVhcmVkIGV2ZXJ5IHR3'
        'byBzZWNvbmRzCi8vIG9uY2UgdGhleSBhcmUgb3V0IG9mIHRoZWlyIHZvcnRleCAtIGEgcGxheWVy'
        'IHdobyBoaXRzIGV2ZXJ5dGhpbmcuCi8vIFNjYW4gbWlzc2lvbnMgKDEyLCAyMykgbmVlZCB0aGUg'
        'cGxheWVyIHRvIGZseSB0aGUgc2NhbiBhbmQgYXJlIGxlZnQgb3V0Lgpmb3IobGV0IG09MTttPD0z'
        'NjttKyspIGlmKG0hPT0xMiAmJiBtIT09MjMpIHNjZW5hcmlvKCdNJyArIFN0cmluZyhtKS5wYWRT'
        'dGFydCgyLCcwJykgKyAnIHBsYXlzIHRvIHRoZSBlbmQnLCAnbT0nICsgbSwgYAogIGNvbnN0IHQg'
        'PSBGUy51bnRpbCgoKT0+d2F2ZU92ZXIsIDQwMDAwLCBmYWxzZSwgdHJ1ZSk7CiAgSVRFTVMubGVu'
        'Z3RoID0gMDsgICAgIC8vIHBpY2t1cHMgaG9sZCB0aGUganVtcCBvcGVuIHVudGlsIHRoZXkgZXhw'
        'aXJlCiAgY29uc3QgaiA9IEZTLnVudGlsKCgpPT53YXZlID09PSAke219KzEsIDYwMDAsIGZhbHNl'
        'LCBmYWxzZSk7CiAgcmV0dXJuIHtlbmRzOiB0ID49IDAsIG5leHRXYXZlOiBqID49IDB9O2ApOwoK'
        'c2NlbmFyaW8oJ0hvTCBzdGFydCB1bmNoYW5nZWQnLCAnbT0xJywgYAogIHJldHVybiB7d2F2ZTog'
        'd2F2ZSwgdGhvdGg6IHBsYXllci5zaGlwPT09J2ZpdG90aCcsIHZhc3VkYW5DYWxsOiBBTExZX0ZB'
        'Q19PTi52YXN1ZGFuPT09dHJ1ZSAmJiBBTExZX0ZBQ19PTi50ZXJyYW49PT1mYWxzZX07YCk7Cgov'
        'LyDilIDilIAgUnVubmVyIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgAooYXN5bmMoKT0+ewogIGNvbnN0IGJyb3dzZXIg'
        'PSBhd2FpdCBjaHJvbWl1bS5sYXVuY2goKTsKICBsZXQgZmFpbHMgPSAwOwogIGNvbnN0IG9ubHkg'
        'PSBwcm9jZXNzLmFyZ3ZbNF07CiAgZm9yKGNvbnN0IHNjIG9mIHNjZW5hcmlvcyl7CiAgICBpZihv'
        'bmx5ICYmIHNjLm5hbWUuaW5kZXhPZihvbmx5KTwwKSBjb250aW51ZTsKICAgIGNvbnN0IHBhZ2Ug'
        'PSBhd2FpdCBicm93c2VyLm5ld1BhZ2UoKTsKICAgIGNvbnN0IGVycnMgPSBbXTsKICAgIHBhZ2Uu'
        'b24oJ3BhZ2VlcnJvcicsIGU9PmVycnMucHVzaChTdHJpbmcoZS5tZXNzYWdlfHxlKSkpOwogICAg'
        'YXdhaXQgcGFnZS5nb3RvKCdmaWxlOi8vJyArIHRtcCArICc/JyArIHNjLnF1ZXJ5KTsKICAgIGF3'
        'YWl0IHBhZ2Uud2FpdEZvclRpbWVvdXQoMzAwKTsKICAgIGxldCByZXM7CiAgICB0cnl7CiAgICAg'
        'IHJlcyA9IGF3YWl0IHBhZ2UuZXZhbHVhdGUoSEVMUEVSUyArIGBcbkZTLmZha2VJbWFnZXMoKTsg'
        'bGF1bmNoR2FtZSgpO1xuKGZ1bmN0aW9uKCl7JHtzYy5ib2R5fX0pKClgKTsKICAgIH1jYXRjaChl'
        'KXsgcmVzID0gbnVsbDsgZXJycy5wdXNoKFN0cmluZyhlLm1lc3NhZ2V8fGUpKTsgfQogICAgY29u'
        'c29sZS5sb2coc2MubmFtZSArICcgICg/JyArIHNjLnF1ZXJ5ICsgJyknKTsKICAgIGlmKHJlcykg'
        'Zm9yKGNvbnN0IFtrLHZdIG9mIE9iamVjdC5lbnRyaWVzKHJlcykpewogICAgICBjb25zdCBnb29k'
        'ID0gKHR5cGVvZiB2PT09J2Jvb2xlYW4nKSA/IHYgOiB0cnVlOwogICAgICBpZighZ29vZCkgZmFp'
        'bHMrKzsKICAgICAgY29uc29sZS5sb2coKGdvb2QgPyAnICBvayAgICAnIDogJyAgRkFJTCAgJykg'
        'KyBrICsgKHR5cGVvZiB2PT09J2Jvb2xlYW4nID8gJycgOiAnID0gJyArIEpTT04uc3RyaW5naWZ5'
        'KHYpKSk7CiAgICB9CiAgICBpZihlcnJzLmxlbmd0aCl7IGZhaWxzKys7IGNvbnNvbGUubG9nKCcg'
        'IEZBSUwgIHBhZ2UgZXJyb3JzOlxuICAgICcgKyBlcnJzLnNsaWNlKDAsNCkuam9pbignXG4gICAg'
        'JykpOyB9CiAgICBhd2FpdCBwYWdlLmNsb3NlKCk7CiAgfQogIGF3YWl0IGJyb3dzZXIuY2xvc2Uo'
        'KTsKICBmcy51bmxpbmtTeW5jKHRtcCk7CiAgY29uc29sZS5sb2coJ1xuJyArIChmYWlscyA/IGZh'
        'aWxzICsgJyBGQUlMRUQnIDogJ2FsbCBwYXNzZWQnKSk7CiAgcHJvY2Vzcy5leGl0KGZhaWxzID8g'
        'MSA6IDApOwp9KSgpOwo='
    ),
}
for name, data in TEST_FILES.items():
    open(name, 'wb').write(base64.b64decode(data))
print("v129 applied: NTF cycle, missions 31-36. Checks updated: shipsim.js, swtest.js, fieldsim.js. Now run: python3 assemble.py 129")
