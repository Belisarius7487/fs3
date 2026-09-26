#!/usr/bin/env python3
"""FS3 v139 - NTF missions 49 to 54.

    49 Das Reparaturdock  a damaged NTF Deimos in front of the Arcadia; three
                          NTF transports come one after another, each that
                          docks puts a quarter of her hull back. Repaired,
                          she jumps. Destroy her first.
    50 Der Durchbruch     two NTF Aeolus and a line of sentry guns hold the
                          field. Once one Aeolus is down, an Orion comes
                          through the gap and has to get across.
    51 Die Rueckeroberung the NTF holds the Arcadia and her guns hold the
                          field. Guns out, an Elysium docks and boards her;
                          lose it and a second one comes, lose both and the
                          NTF keeps her.
    52 Das Artilleriefeuer a GTVA Mjolnir and a Deimos hold the field. Three
                          NTF capital ships come one after another, each on
                          a jump deadline. The Hecate at the end is the
                          objective.
    53 Der Gegenangriff   our Orion and Deimos; an NTF Hecate and an NTF
                          Orion jump in on top of them, bombers follow.
    54 Die Evakuierung    four Elysiums leave the Arcadia one after another
                          and fly out to the left; at least three have to
                          make it.

Mechanics these need:
  - Enemy transports can dock (dockTo, dockHold); one whose target is gone
    jumps out. 'heilen' works on an enemy ship; repaired, her jump counts
    as leaving ('verlaesst').
  - hurt: a ship arrives with only that share of her hull. noFlee: she
    does not run when her guns are gone.
  - armed: an installation that fires its guns and has subsystems. Taken
    ('kapern'), it stays where it is and stops fighting instead of jumping.
  - Effect 'kulisse': a ship becomes scenery (no longer fights, no longer
    counts for the end of the wave).
  - Triggers 'gerettet' N and 'verloren' N: protected ships through / lost.
  - Ids joined with '+' in a trigger: all of them (e.g. 'V1+V2').
  - cross below zero: a protected ship flies out to the left.
  - Allied capital ships in a written mission can have x and y, and
    callsOk: they do not block the support call.
  - The GTSG Mjolnir as an allied gun platform: one heavy beam, no drive,
    no subsystems.

Needs v138. Edits src/30_waves.js, src/40_world.js, src/50_combat.js and
src/60_effects.js in place, and writes the updated fieldsim.js and
swtest.js. Run assemble.py afterwards.
"""
import sys


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def load(p):
    return open(p, encoding="utf-8").read()


wv = load("src/30_waves.js")
wo = load("src/40_world.js")
cb = load("src/50_combat.js")
fx = load("src/60_effects.js")

# ══ Triggers: '+' lists, 'gerettet', 'verloren' ═════════════════════════
wv = replace_once(
    wv,
    "    case 'vernichtet':   return evSeen(ev.a) && byId(ev.a).length===0\n"
    "                              && !EV_LEFT[ev.a] && !EV_FLED[ev.a] && !EV_TAKEN[ev.a];\n"
    "    case 'alleZerstoert':return evSeen(ev.a) && byId(ev.a).length===0;\n",
    "    // Several ids joined with '+': every one of them.\n"
    "    case 'vernichtet':   return evIds(ev.a).every(function(id){\n"
    "                                return evSeen(id) && byId(id).length===0\n"
    "                                  && !EV_LEFT[id] && !EV_FLED[id] && !EV_TAKEN[id]; });\n"
    "    case 'alleZerstoert':return evIds(ev.a).every(function(id){\n"
    "                                return evSeen(id) && byId(id).length===0; });\n"
    "    // Protected ships through, and protected ships lost, this wave.\n"
    "    case 'gerettet':     return protSaved >= (ev.a||1);\n"
    "    case 'verloren':     return protLost  >= (ev.a||1);\n",
    "trigger lists")
wv = replace_once(
    wv,
    "function evSeen(id){ return !!EV_SEEN[id]; }\n",
    "function evSeen(id){ return !!EV_SEEN[id]; }\n"
    "// A trigger may name several ids joined with '+'.\n"
    "function evIds(a){ return String(a||'').split('+'); }\n",
    "evIds")
wv = replace_once(
    wv,
    "      if(evSeen(e.a) && byId(e.a).length===0) continue;\n",
    "      if(evIds(e.a).every(function(id){ return evSeen(id) && byId(id).length===0; })) continue;\n",
    "evPending lists")

# ══ Effects: heilen on the enemy side, kapern of an installation, kulisse
wv = replace_once(
    wv,
    "              if(ht.hp >= ht.maxHp*0.999){\n"
    "                ht.warpOut = ht.warpMax || 100;\n",
    "              if(ht.hp >= ht.maxHp*0.999){\n"
    "                ht.warpOut = ht.warpMax || 100;\n"
    "                // An enemy repaired and gone has left, not been destroyed.\n"
    "                if(ht.side!=='ally' && ht.uid){ EV_FLED[ht.uid] = true; ht.fleeFree = false; }\n",
    "heilen enemy")
wv = replace_once(
    wv,
    "      for(const u of byId(arg)){\n"
    "        if(u.side==='ally') continue;\n"
    "        u.captureLock = false; u.captured = true; u.fleeFree = true;\n",
    "      for(const u of byId(arg)){\n"
    "        if(u.side==='ally') continue;\n"
    "        // An installation does not jump. Taken, it stays where it is,\n"
    "        // stops fighting and becomes part of the scenery.\n"
    "        if(u.type==='station'){\n"
    "          u.captureLock = false; u.captured = true; u.noFire = true;\n"
    "          u.invuln = true; u.scenery = true; u.noTarget = true;\n"
    "          u.faction = 'terran';\n"
    "          EV_TAKEN[arg] = true;\n"
    "          score += u.pts || 0;\n"
    "          SUB_MSGS.push({x:u.x, y:u.y-60, txt:'CAPTURED', life:200, ml:200,\n"
    "                         ally:true, tone:'good'});\n"
    "          continue;\n"
    "        }\n"
    "        u.captureLock = false; u.captured = true; u.fleeFree = true;\n",
    "kapern station")
wv = replace_once(
    wv,
    "    case 'freigeben':\n"
    "      // The capture is off - her captors are gone. Now she can die.\n"
    "      for(const u of byId(arg)) u.captureLock = false;\n"
    "      break;\n",
    "    case 'freigeben':\n"
    "      // The capture is off - her captors are gone. Now she can die.\n"
    "      for(const u of byId(arg)) u.captureLock = false;\n"
    "      break;\n"
    "    case 'kulisse':\n"
    "      // Out of the fight: she stays, but no longer shoots and no longer\n"
    "      // counts for the end of the wave (the NTF keeps her).\n"
    "      for(const u of byId(arg)){\n"
    "        u.captureLock = false; u.noFire = true; u.invuln = true;\n"
    "        u.scenery = true; u.noTarget = true;\n"
    "      }\n"
    "      break;\n",
    "kulisse")

# ══ Spawning: ally x/y/callsOk, enemy dock/hurt/armed ══════════════════
wv = replace_once(
    wv,
    "             crossDir:u.crossDir, defectRun:u.defectRun, noWings:u.noWings}\n",
    "             crossDir:u.crossDir, defectRun:u.defectRun, noWings:u.noWings,\n"
    "             x:u.x, y:u.y, callsOk:u.callsOk}\n",
    "ally put xy")
wv = replace_once(
    wv,
    "             fleeFree:u.fleeFree,\n"
    "             still:u.still, noFlak:u.noFlak, fixY:(u.y!=null),\n",
    "             fleeFree:u.fleeFree, hurt:u.hurt, armed:u.armed, noFlee:u.noFlee,\n"
    "             still:u.still, noFlak:u.noFlak, fixY:(u.y!=null),\n",
    "enemy put hurt armed")
wv = replace_once(
    wv,
    "           x:xx, y:yy, scan:u.scan?1:0, escape:u.escape, scanFirst:u.scanFirst,\n",
    "           x:xx, y:yy, scan:u.scan?1:0, escape:u.escape, scanFirst:u.scanFirst,\n"
    "           dockTo:u.dockTo, dockHold:u.dockHold,\n",
    "enemy put dock")
wv = replace_once(
    wv,
    "  if(sp.dockTo) e.dockTo = sp.dockTo;\n"
    "  if(sp.pickup) e.pickup = true;\n",
    "  if(sp.dockTo) e.dockTo = sp.dockTo;\n"
    "  if(sp.dockHold) e.dockHold = Math.round(sp.dockHold*TICK_HZ);\n"
    "  if(sp.pickup) e.pickup = true;\n",
    "enemy dockHold")
wv = replace_once(
    wv,
    "  if(sp.fac) e.faction = sp.fac;\n"
    "  if(sp.scan){ e.scan = true; e.noTarget = true; }\n",
    "  if(sp.fac) e.faction = sp.fac;\n"
    "  if(sp.scan){ e.scan = true; e.noTarget = true; }\n"
    "  // Arrives with only this share of her hull; the bar shows the damage.\n"
    "  if(sp.hurt) e.hp = Math.max(1, Math.round(e.maxHp*sp.hurt));\n"
    "  // An installation that fights: its guns fire, and it has subsystems\n"
    "  // to shoot them out. It never runs, it has nowhere to go.\n"
    "  if(sp.armed){ e.armed = true; e.subsOn = true; e.noFlee = true; initSubsystems(e); }\n"
    "  // Stays and fights on with her guns gone instead of running.\n"
    "  if(sp.noFlee) e.noFlee = true;\n",
    "hurt armed")

# Protected ships flying out to the left.
wv = replace_once(
    wv,
    "  if(sp.cross && !sp.dockTo){\n"
    "    a.crossing = sp.cross;         // Bildpunkte je Schritt\n"
    "    a.flip = needsFlip(a.img, false);   // faehrt nach rechts, schaut nach rechts\n"
    "    if(sp.x == null) a.x = -40;    // von links herein\n"
    "  }\n",
    "  if(sp.cross && !sp.dockTo){\n"
    "    a.crossing = sp.cross;         // Bildpunkte je Schritt\n"
    "    // Below zero she flies out to the left and faces that way.\n"
    "    a.flip = needsFlip(a.img, sp.cross < 0);\n"
    "    if(sp.x == null) a.x = (sp.cross < 0) ? W+40 : -40;\n"
    "  }\n",
    "cross left spawn")
wv = replace_once(
    wv,
    "    if(a.x > W+60){\n",
    "    if(a.crossing > 0 ? a.x > W+60 : a.x < -60){\n",
    "cross left exit")
wv = replace_once(
    wv,
    "      SUB_MSGS.push({x:W-90, y:a.y,\n",
    "      SUB_MSGS.push({x:(a.crossing > 0) ? W-90 : 90, y:a.y,\n",
    "cross left msg")

# Docking: the boarding party's jump counts as saved only on our side; an
# enemy transport whose target is gone jumps out.
wv = replace_once(
    wv,
    "      if(e.uid) EV_LEFT[e.uid] = true;\n"
    "      protSaved++;\n"
    "      continue;\n",
    "      if(e.uid) EV_LEFT[e.uid] = true;\n"
    "      if(e.side==='ally') protSaved++;\n"
    "      continue;\n",
    "dockHold ally only")
wv = replace_once(
    wv,
    "function leaveEmpty(e, wasCargo){\n"
    "  if(e.dockRes && e.dockRes.resBy===e) e.dockRes.resBy = null;\n"
    "  e.dockRes = null; e.dockTo = null;\n",
    "function leaveEmpty(e, wasCargo){\n"
    "  if(e.dockRes && e.dockRes.resBy===e) e.dockRes.resBy = null;\n"
    "  e.dockRes = null; e.dockTo = null;\n"
    "  // An enemy transport whose ship is gone has nothing left to do here.\n"
    "  if(e.side!=='ally' && e.dockHold && !(e.warpOut>0)){\n"
    "    e.warpOut = e.warpMax = 120; e.warpX = e.x; e.warpY = e.y;\n"
    "    if(e.uid) EV_LEFT[e.uid] = true;\n"
    "  }\n",
    "enemy transport leaves")

# ══ Missions 49 - 54 ════════════════════════════════════════════════════
wv = replace_once(
    wv,
    "       {t:'gescannt', a:'V1', w:'zielerfuellt', a2:'ORION SCANNED'},\n"
    "       {t:'gescannt', a:'V1', w:'raus', a2:'V1'}\n"
    "     ]}\n"
    "};\n",
    "       {t:'gescannt', a:'V1', w:'zielerfuellt', a2:'ORION SCANNED'},\n"
    "       {t:'gescannt', a:'V1', w:'raus', a2:'V1'}\n"
    "     ]},\n"
    "\n"
    "  49:{name:'Das Reparaturdock', fac:'ntf', o:'clear', live:5,\n"
    "      ziel:'DESTROY THE DEIMOS BEFORE HER REPAIRS ARE DONE', u:[\n"
    "       // In front of the Arcadia the NTF patches up a Deimos. Three\n"
    "       // transports come one after another; each that docks puts a\n"
    "       // quarter of her hull back. Whole again, or once the last one\n"
    "       // has docked, she jumps.\n"
    "       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.36},\n"
    "       {id:'D1', c:'co', n:1, spr:'ntfcodeimos', still:true, x:420, y:250,\n"
    "        hp:1.8, hurt:0.25, noFlee:true},\n"
    "       {id:'T1', c:'tr', n:1, spr:'trargo', t:4,  x:860, y:120, dockTo:'D1', dockHold:4},\n"
    "       {id:'T2', c:'tr', n:1, spr:'trargo', t:24, x:860, y:400, dockTo:'D1', dockHold:4},\n"
    "       {id:'T3', c:'tr', n:1, spr:'trargo', t:44, x:860, y:140, dockTo:'D1', dockHold:4},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'angedockt', a:'T1', w:'heilen', a2:'D1'},\n"
    "       {t:'angedockt', a:'T2', w:'heilen', a2:'D1'},\n"
    "       {t:'angedockt', a:'T3', w:'heilen', a2:'D1'},\n"
    "       // After the last transport she goes, whole or not.\n"
    "       {t:'angedockt', a:'T3', w:'raus', a2:'D1'},\n"
    "       {t:'vernichtet', a:'D1', w:'zielerfuellt', a2:'DEIMOS DESTROYED'},\n"
    "       {t:'vernichtet', a:'D1', w:'ende', a2:''},\n"
    "       {t:'verlaesst', a:'D1', w:'zielverfehlt', a2:'THE DEIMOS WAS REPAIRED'},\n"
    "       {t:'verlaesst', a:'D1', w:'ende', a2:''}\n"
    "     ]},\n"
    "\n"
    "  50:{name:'Der Durchbruch', fac:'ntf', o:'guard', live:5, crossEnds:true,\n"
    "      noRocks:true, ziel:'BREAK THE BLOCKADE - DESTROY AN AEOLUS', u:[\n"
    "       // Two Aeolus and a line of sentry guns hold the field. Once one\n"
    "       // Aeolus is down, an Orion comes through the gap and has to get\n"
    "       // across.\n"
    "       {id:'K1', c:'cr', n:2, spr:'ntfcraeolus', still:true, x:600},\n"
    "       {id:'G1', c:'sg', n:4, spr:'sgcerberus', x:500},\n"
    "       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', crossSecs:60, hp:1.2,\n"
    "        wait:true},\n"
    "       {id:'E1', c:'fi', n:2}\n"
    "     ], ev:[\n"
    "       {t:'sek', a:4, w:'nachschub', a2:'an'},\n"
    "       {t:'anzahlUnter', a:'K1', b:2, w:'einwarpen', a2:'A1'},\n"
    "       {t:'anzahlUnter', a:'K1', b:2, w:'ziel', a2:'GET THE ORION THROUGH'},\n"
    "       {t:'verlaesst', a:'A1', w:'zielerfuellt', a2:'THE ORION IS THROUGH'},\n"
    "       {t:'verlaesst', a:'A1', w:'ende', a2:''},\n"
    "       {t:'vernichtet', a:'A1', w:'zielverfehlt', a2:'ORION LOST'},\n"
    "       {t:'vernichtet', a:'A1', w:'ende', a2:''}\n"
    "     ]},\n"
    "\n"
    "  51:{name:'Die Rueckeroberung', fac:'ntf', o:'clear', live:5,\n"
    "      ziel:'TAKE OUT THE WEAPONS OF THE ARCADIA', u:[\n"
    "       // The NTF holds the Arcadia and her guns hold the field. With the\n"
    "       // guns shot out an Elysium comes and boards her; until then she\n"
    "       // cannot be destroyed. Lose the Elysium and a second one comes,\n"
    "       // lose both and the NTF keeps her.\n"
    "       {id:'S1', c:'in', n:1, spr:'inarcadia', x:600, capture:true, armed:true},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:1, wait:true},\n"
    "       {id:'B1', c:'bo', n:1, wait:true},\n"
    "       {id:'T1', c:'tr', n:1, spr:'trelysium', side:'ally', x:-40, y:260,\n"
    "        dockTo:'S1', dockHold:8, wait:true},\n"
    "       {id:'T2', c:'tr', n:1, spr:'trelysium', side:'ally', x:-40, y:260,\n"
    "        dockTo:'S1', dockHold:8, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'subsystem', a:'S1', b:'weapons', w:'einwarpen', a2:'T1'},\n"
    "       {t:'subsystem', a:'S1', b:'weapons', w:'einwarpen', a2:'B1'},\n"
    "       {t:'subsystem', a:'S1', b:'weapons', w:'ziel', a2:'COVER THE ELYSIUM'},\n"
    "       {t:'angedockt', a:'T1', w:'kapern', a2:'S1'},\n"
    "       {t:'angedockt', a:'T1', w:'zielerfuellt', a2:'ARCADIA RETAKEN'},\n"
    "       {t:'vernichtet', a:'T1', w:'einwarpen', a2:'T2'},\n"
    "       {t:'vernichtet', a:'T1', w:'meldung', a2:'second elysium inbound'},\n"
    "       {t:'angedockt', a:'T2', w:'kapern', a2:'S1'},\n"
    "       {t:'angedockt', a:'T2', w:'zielerfuellt', a2:'ARCADIA RETAKEN'},\n"
    "       {t:'vernichtet', a:'T2', w:'kulisse', a2:'S1'},\n"
    "       {t:'vernichtet', a:'T2', w:'zielverfehlt', a2:'BOTH ELYSIUMS LOST'}\n"
    "     ]},\n"
    "\n"
    "  52:{name:'Das Artilleriefeuer', fac:'ntf', o:'clear', live:5,\n"
    "      ziel:'STOP THE NTF SHIPS BEFORE THEY JUMP', u:[\n"
    "       // A GTVA Mjolnir holds the field with a Deimos beside her. NTF\n"
    "       // capital ships come one after another, each on a deadline. Kept\n"
    "       // here long enough, the Mjolnir's beam finds them; shooting out\n"
    "       // navigation keeps them here. The Hecate at the end is the job.\n"
    "       {id:'M1', c:'cr', n:1, spr:'sgmjolnir', side:'ally', x:110, y:170, callsOk:true},\n"
    "       {id:'A1', c:'co', n:1, spr:'codeimos', side:'ally', still:true, y:390,\n"
    "        callsOk:true},\n"
    "       {id:'V1', c:'cr', n:1, spr:'ntfcraeolus', t:3, flee:40, y:180},\n"
    "       {id:'V2', c:'co', n:1, spr:'ntfcodeimos', flee:50, y:330, wait:true},\n"
    "       {id:'V3', c:'de', n:1, spr:'ntfdehecate', flee:60, y:250, wait:true},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'B1', c:'bo', n:1, wait:true},\n"
    "       {id:'E2', c:'fi', n:2, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'V1', w:'einwarpen', a2:'V2'},\n"
    "       {t:'alleZerstoert', a:'V1', w:'einwarpen', a2:'B1'},\n"
    "       {t:'alleZerstoert', a:'V2', w:'einwarpen', a2:'V3'},\n"
    "       {t:'alleZerstoert', a:'V2', w:'einwarpen', a2:'E2'},\n"
    "       {t:'vernichtet', a:'V1', w:'meldung', a2:'aeolus destroyed'},\n"
    "       {t:'verlaesst', a:'V1', w:'meldung', a2:'the aeolus got away'},\n"
    "       {t:'vernichtet', a:'V2', w:'meldung', a2:'deimos destroyed'},\n"
    "       {t:'verlaesst', a:'V2', w:'meldung', a2:'the deimos got away'},\n"
    "       {t:'vernichtet', a:'V3', w:'zielerfuellt', a2:'HECATE DESTROYED'},\n"
    "       {t:'verlaesst', a:'V3', w:'zielverfehlt', a2:'THE HECATE GOT AWAY'}\n"
    "     ]},\n"
    "\n"
    "  53:{name:'Der Gegenangriff', fac:'ntf', o:'clear', live:6,\n"
    "      ziel:'COVER THE FLEET', u:[\n"
    "       // Our Orion and a Deimos. An NTF Hecate and an NTF Orion jump in\n"
    "       // on top of them, bombers follow. Their loss is a blow, not the\n"
    "       // end of the mission: the NTF destroyers are the objective.\n"
    "       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', y:170, hp:1.3,\n"
    "        callsOk:true, noWings:true},\n"
    "       {id:'A2', c:'co', n:1, spr:'codeimos', side:'ally', y:390, callsOk:true},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'V1', c:'de', n:1, spr:'ntfdehecate', y:160, noFlee:true, wait:true},\n"
    "       {id:'V2', c:'de', n:1, spr:'ntfdeorion', y:370, noFlee:true, wait:true},\n"
    "       {id:'B1', c:'bo', n:2, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'sek', a:12, w:'einwarpen', a2:'V1'},\n"
    "       {t:'sek', a:12, w:'einwarpen', a2:'V2'},\n"
    "       {t:'sek', a:12, w:'ziel', a2:'DESTROY THE HECATE AND THE ORION'},\n"
    "       {t:'sek', a:18, w:'einwarpen', a2:'B1'},\n"
    "       {t:'vernichtet', a:'A1', w:'meldung', a2:'gtd orion lost'},\n"
    "       {t:'vernichtet', a:'A2', w:'meldung', a2:'gtcv deimos lost'},\n"
    "       {t:'vernichtet', a:'V1+V2', w:'zielerfuellt', a2:'COUNTERATTACK BROKEN'}\n"
    "     ]},\n"
    "\n"
    "  54:{name:'Die Evakuierung', fac:'ntf', o:'protect', live:5, hunt:'T1',\n"
    "      ziel:'GET THE ELYSIUMS OUT - AT LEAST THREE', u:[\n"
    "       // Four Elysiums leave the Arcadia one after another and fly out\n"
    "       // to the left, away from the NTF coming in from the right.\n"
    "       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.36},\n"
    "       {id:'T1', c:'tr', n:1, spr:'trelysium', side:'ally', t:2,  x:560, y:170, cross:-0.42},\n"
    "       {id:'T2', c:'tr', n:1, spr:'trelysium', side:'ally', t:11, x:560, y:330, cross:-0.42},\n"
    "       {id:'T3', c:'tr', n:1, spr:'trelysium', side:'ally', t:20, x:560, y:220, cross:-0.42},\n"
    "       {id:'T4', c:'tr', n:1, spr:'trelysium', side:'ally', t:29, x:560, y:390, cross:-0.42},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'B1', c:'bo', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'sek', a:6, w:'einwarpen', a2:'B1'},\n"
    "       {t:'sek', a:8, w:'nachschub', a2:'an'},\n"
    "       {t:'alleZerstoert', a:'T1', w:'jagd', a2:'T2'},\n"
    "       {t:'alleZerstoert', a:'T2', w:'jagd', a2:'T3'},\n"
    "       {t:'alleZerstoert', a:'T3', w:'jagd', a2:'T4'},\n"
    "       {t:'gerettet', a:3, w:'zielerfuellt', a2:'EVACUATION COMPLETE'},\n"
    "       {t:'verloren', a:2, w:'zielverfehlt', a2:'TOO MANY ELYSIUMS LOST'},\n"
    "       {t:'alleZerstoert', a:'T1+T2+T3+T4', w:'nachschub', a2:'aus'}\n"
    "     ]}\n"
    "};\n",
    "missions 49-54")

# ══ Mjolnir ═════════════════════════════════════════════════════════════
wv = replace_once(
    wv,
    "  ntfcodeimos:'ntf_deimos'\n};\n",
    "  ntfcodeimos:'ntf_deimos', sgmjolnir:'ter_mjolnir'\n};\n",
    "ALLY_ID mjolnir")
wo = replace_once(
    wo,
    "  ntf_deimos:     {cls:'corvette',  fac:'terran',  spr:'ntfcodeimos',  label:'NTF Deimos'}\n};\n",
    "  ntf_deimos:     {cls:'corvette',  fac:'terran',  spr:'ntfcodeimos',  label:'NTF Deimos'},\n"
    "  // Mission use only: a gun platform. One heavy beam against capital\n"
    "  // ships, no drive and no subsystems. Cruiser class for hull and\n"
    "  // targeting, so bombers and beams treat her as a capital ship.\n"
    "  ter_mjolnir:    {cls:'cruiser',   fac:'terran',  spr:'sgmjolnir',    label:'GTSG Mjolnir',\n"
    "                   platform:true}\n};\n",
    "ALLY_DEFS mjolnir")
wo = replace_once(
    wo,
    "  initBeams(a);\n  initWeapons(a);\n  return a;\n}\n",
    "  // A platform is already in place and does not move.\n"
    "  if(d.platform){ a.platform = true; a.vy = 0; a.minY = a.y; a.maxY = a.y;\n"
    "                  a.warp = 0; a.warpMax = 1; }\n"
    "  initBeams(a);\n  initWeapons(a);\n  return a;\n}\n",
    "mkAlly platform")
wo = replace_once(
    wo,
    "  for(const a of allies) if(!a.small && !a.guard) return false;\n",
    "  // callsOk: a mission ship that does not stand in for a called escort.\n"
    "  for(const a of allies) if(!a.small && !a.guard && !a.callsOk) return false;\n",
    "allyReady callsOk")

fx = replace_once(
    fx,
    "        if(_a) initSubsystems(_a);\n"
    "        if(_a && _sp.still){ _a.vy=0; _a.minY=_a.y; _a.maxY=_a.y; }\n",
    "        if(_a) initSubsystems(_a);\n"
    "        // A place the mission gives. Allied capital ships do not drive\n"
    "        // anywhere in x, so x is simply where she stands.\n"
    "        if(_a && _sp.x!=null){ _a.x=_sp.x; _a.warpX=_sp.x; _a.targetX=_sp.x; }\n"
    "        if(_a && _sp.y!=null){ _a.y=_sp.y; _a.warpY=_sp.y;\n"
    "                               if(_a.platform){ _a.minY=_sp.y; _a.maxY=_sp.y; } }\n"
    "        if(_a && _a.platform) _a.subs = null;\n"
    "        if(_a && _sp.callsOk) _a.callsOk = true;\n"
    "        if(_a && _sp.still){ _a.vy=0; _a.minY=_a.y; _a.maxY=_a.y; }\n",
    "ally spawn xy")

# ══ Installations that fight; enemy transports that dock ═══════════════
cb = replace_once(
    cb,
    "function hasSubsystems(e){\n"
    "  return e && (e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||e.type==='boss');\n",
    "function hasSubsystems(e){\n"
    "  // An installation only when a mission arms it (subsOn).\n"
    "  return e && (e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||e.type==='boss'\n"
    "               || (e.type==='station' && !!e.subsOn));\n",
    "hasSubsystems station")
cb = replace_once(
    cb,
    "  boss:      {rate:[80,140],  big:0.38,\n",
    "  // An armed installation: many mounts, so each one fires slowly.\n"
    "  station:   {rate:[260,420], big:0.30,\n"
    "              sec:{type:'missile', rate:[520,860], dmg:16, spd:2.6, turn:0.026}},\n"
    "  boss:      {rate:[80,140],  big:0.38,\n",
    "WPN station")
wo = replace_once(
    wo,
    "  if(e.hp <= 0 && !e.dead &&\n"
    "     (e.type==='destroyer'||e.type==='boss'||e.type==='station')){\n",
    "  // A ship that is to be taken does not start to break up: the lock\n"
    "  // below holds her hull instead.\n"
    "  if(e.hp <= 0 && !e.dead && !e.captureLock &&\n"
    "     (e.type==='destroyer'||e.type==='boss'||e.type==='station')){\n",
    "death roll capture")
fx = replace_once(
    fx,
    "    else if(e.type==='freighter'){\n"
    "      if(e.warp>0){ e.warp--; e.x-=0.3; continue; }\n",
    "    else if(e.type==='freighter'){\n"
    "      if(e.warp>0){ e.warp--; e.x-=0.3; continue; }\n"
    "      // Leaving after a dock: through the vortex, then gone.\n"
    "      if(e.warpOut>0){ e.warpOut--; if(e.warpOut<=0) enemies.splice(i,1); continue; }\n"
    "      // On its way to a dock tickDocking() does the driving, and a\n"
    "      // transport with a job does not turn and run when shot at.\n"
    "      if(e.dockTo) continue;\n",
    "enemy freighter dock")
fx = replace_once(
    fx,
    "    else if(e.type==='corvette'||e.type==='destroyer'){\n",
    "    else if(e.type==='station'){\n"
    "      // An armed installation fires until its guns are out or it is\n"
    "      // taken. The unarmed ones are scenery or targets and stay quiet.\n"
    "      if(e.armed && !e.captured) capitalFire(e);\n"
    "    }\n"
    "    else if(e.type==='corvette'||e.type==='destroyer'){\n",
    "station fires")

open("src/30_waves.js", "w", encoding="utf-8").write(wv)
open("src/40_world.js", "w", encoding="utf-8").write(wo)
open("src/50_combat.js", "w", encoding="utf-8").write(cb)
open("src/60_effects.js", "w", encoding="utf-8").write(fx)

# -- Test files ------------------------------------------------------------
# The updated checks travel inside the patch, because .js files cannot be
# downloaded from the chat. Written last.
import base64
TEST_FILES = {
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
        'MCwwLGMud2lkdGgsYy5oZWlnaHQpOwogICAgICAgIElNR1Nba10gPSBjOwogICAgICB9CiAgICAg'
        'IC8vIE5vdGhpbmcgaXMgcmVhbGx5IGxvYWRlZCBmcm9tIGRpc2sgaGVyZS4gV2l0aG91dCB0aGlz'
        'IGRyYXcoKSBzdG9wcwogICAgICAvLyBhdCBpdHMgbG9hZGluZyBzY3JlZW4gYW5kIG5vbmUgb2Yg'
        'dGhlIGZpZWxkIGlzIGV2ZXIgZHJhd24uCiAgICAgIGltZ3NMb2FkZWQgPSBUT1RBTDsgbmVic0xv'
        'YWRlZCA9IDA7CiAgICB9LAogICAgc3RlcChuKXsgZm9yKGxldCBpPTA7aTxuO2krKyl7IHBsYXll'
        'ci5ocCA9IHBsYXllci5tYXhIcDsgcGxheWVyLnNoID0gcGxheWVyLm1heFNoOwogICAgICAgICAg'
        'ICAgaWYodHlwZW9mIGxpdmVzIT09J3VuZGVmaW5lZCcpIGxpdmVzID0gMzsgdXBkYXRlKCk7IGlm'
        'KGklMjU9PT0wKSBkcmF3KCk7IH0gfSwKICAgIC8vIFNob290IGRvd24gZXZlcnkgZW5lbXkgZmln'
        'aHRlciBhbmQgYm9tYmVyIHRoYXQgaXMgb3V0IG9mIGl0cyB2b3J0ZXgsCiAgICAvLyB0aGUgYm9t'
        'YnMgaW4gZmxpZ2h0IGFuZCByb2NrcyBjbG9zaW5nIG9uIGFuIGVzY29ydCAtIHdoYXQgYSBwbGF5'
        'ZXIKICAgIC8vIGRlZmVuZGluZyBvbmUgZG9lcy4KICAgIGtpbGxTbWFsbCgpeyBmb3IoY29uc3Qg'
        'ZSBvZiBlbmVtaWVzKSBpZigoZS50eXBlPT09J2ZpZ2h0ZXInfHxlLnR5cGU9PT0nYm9tYmVyJykg'
        'JiYgIShlLndhcnA+MCkpIGUuaHAgPSAwOwogICAgICAgICAgICAgICAgIGZvcihsZXQgaT1lQnVs'
        'bGV0cy5sZW5ndGgtMTtpPj0wO2ktLSkgaWYoZUJ1bGxldHNbaV0ua2luZD09PSdib21iJykgZUJ1'
        'bGxldHMuc3BsaWNlKGksMSk7CiAgICAgICAgICAgICAgICAgLy8gTG9vc2Ugcm9ja3MgYWJvdXQg'
        'dG8gaGl0IGFuIGVzY29ydCBhcyB3ZWxsLgogICAgICAgICAgICAgICAgIGZvcihjb25zdCBlIG9m'
        'IGVuZW1pZXMpIGlmKGUudHlwZT09PSdhc3Rlcm9pZCcgJiYgIWUuc2NlbmVyeSAmJgogICAgICAg'
        'ICAgICAgICAgICAgYWxsaWVzLnNvbWUoYT0+IWEuc21hbGwgJiYgTWF0aC5oeXBvdChhLngtZS54'
        'LCBhLnktZS55KSA8IDE4MCkpIGUuaHAgPSAwOyB9LAogICAga2lsbElkKGlkKXsgZm9yKGNvbnN0'
        'IGUgb2YgZW5lbWllcykgaWYoZS51aWQ9PT1pZCAmJiAhKGUud2FycD4wKSkgZS5ocCA9IDA7IH0s'
        'CiAgICAvLyBTaXQgb24gYSBwb2ludCwgdW5kaXN0dXJiZWQsIGZvciBuIHN0ZXBzOiBob3cgYSBz'
        'Y2FuIGlzIGZsb3duLgogICAgaG9sZCh4LCB5LCBuKXsgZm9yKGxldCBpPTA7aTxuO2krKyl7IHBs'
        'YXllci54ID0geDsgcGxheWVyLnkgPSB5OyBwbGF5ZXIuc2hEZWxheSA9IDA7IE1PVVNFLnggPSB4'
        'OyBNT1VTRS55ID0geTsgRlMuc3RlcCgxKTsgfSB9LAogICAgLy8gU3RlcCB1bnRpbCBjb25kKCkg'
        'aG9sZHMsIGNsZWFyaW5nIHNtYWxsIGNyYWZ0IGV2ZXJ5IHNvIG9mdGVuLgogICAgLy8gZXZlcnk6'
        'IGhvdyBvZnRlbiB0aGUgc21hbGwgY3JhZnQgYXJlIGNsZWFyZWQsIGluIHN0ZXBzIChkZWZhdWx0'
        'IDIwMCkuCiAgICB1bnRpbChjb25kLCBtYXgsIGNsZWFyLCBhbGwsIGV2ZXJ5KXsgY29uc3QgZXYg'
        'PSBldmVyeSB8fCAyMDA7CiAgICAgICAgICAgZm9yKGxldCB0PTA7dDxtYXg7dCs9MjApeyBpZihj'
        'b25kKCkpIHJldHVybiB0OwogICAgICAgICAgICAgaWYoY2xlYXIgJiYgdCVldj09PTApIEZTLmtp'
        'bGxTbWFsbCgpOwogICAgICAgICAgICAgaWYoYWxsICYmIHQlMjAwPT09MCkgZm9yKGNvbnN0IGUg'
        'b2YgZW5lbWllcyl7CiAgICAgICAgICAgICAgIGlmKGUud2FycD4wIHx8IGUuaW52dWxuIHx8IGUu'
        'c2NlbmVyeSkgY29udGludWU7CiAgICAgICAgICAgICAgIC8vIEEgcHJpemUgaXMgbm90IHNob3Qg'
        'ZG93bjogaXRzIGVuZ2luZXMgYXJlLCB0aGVuIGl0IGlzIHRha2VuLgogICAgICAgICAgICAgICBp'
        'ZihlLmNhcHR1cmVMb2NrKXsgZm9yKGNvbnN0IHMgb2YgKGUuc3Vic3x8W10pKSBpZihzLmlkPT09'
        'J2VuZ2luZXMnfHxzLmlkPT09J3dlYXBvbnMnfHxzLmlkPT09J25hdmlnYXRpb24nKXsgcy5kZWFk'
        'PXRydWU7IHMuaHA9MDsgfSBjb250aW51ZTsgfQogICAgICAgICAgICAgICAvLyBTY2FuIHRhcmdl'
        'dHMgYXJlIHNjYW5uZWQgZmlyc3QsIGFzIHRoZSBwbGF5ZXIgd291bGQuCiAgICAgICAgICAgICAg'
        'IGlmKGUuc2NhblN1YnMgJiYgIWUuc2Nhbm5lZCl7IGZvcihjb25zdCBzIG9mIGUuc3Vicykgcy5z'
        'Y2FuVCA9IDFlOTsgY29udGludWU7IH0KICAgICAgICAgICAgICAgaWYoZS5zY2FuTG9jayAmJiAh'
        'ZS5zY2FubmVkKXsgZS5zY2FubmVkID0gdHJ1ZTsgY29udGludWU7IH0KICAgICAgICAgICAgICAg'
        'ZS5ocCA9IDA7IH0KICAgICAgICAgICAgIEZTLnN0ZXAoMjApOyB9IHJldHVybiAtMTsgfSwKICAg'
        'IGlkcyhpZCl7IHJldHVybiBieUlkKGlkKTsgfSwKICAgIGVuZW15SWRzKCl7IHJldHVybiBlbmVt'
        'aWVzLm1hcChlPT5lLnVpZHx8ZS50eXBlKTsgfSwKICAgIGFsbHlJZHMoKXsgcmV0dXJuIGFsbGll'
        'cy5tYXAoYT0+YS51aWR8fGEudHlwZSk7IH0KICB9O2A7Cgpjb25zdCBzY2VuYXJpb3MgPSBbXTsK'
        'ZnVuY3Rpb24gc2NlbmFyaW8obmFtZSwgcXVlcnksIGJvZHksIG5vTGF1bmNoKXsgc2NlbmFyaW9z'
        'LnB1c2goe25hbWUsIHF1ZXJ5LCBib2R5LCBub0xhdW5jaH0pOyB9CgovLyDilIDilIAgU2NlbmFy'
        'aW9zIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgApzY2VuYXJpbygnTTMxIERlciBBdWZzdGFuZCcsICdtPTMxJywgYAogIGNvbnN0IHIg'
        'PSB7fTsKICByLndhdmUgPSB3YXZlOyByLnNoaXAgPSBwbGF5ZXIuc2hpcDsKICByLnRlcnJhbkNh'
        'bGwgPSBBTExZX0ZBQ19PTi50ZXJyYW49PT10cnVlICYmIEFMTFlfRkFDX09OLnZhc3VkYW49PT1m'
        'YWxzZTsKICBGUy5zdGVwKDQwMCk7CiAgY29uc3QgYSA9IGFsbGllcy5maW5kKHg9PngudWlkPT09'
        'J0ExJyk7CiAgci5hbGx5QXRTdGFydCA9ICEhYSAmJiBhLmltZz09PSdjcmxldmlhdGhhbic7CiAg'
        'ci5sb2NrU2V0ID0gISFhICYmIGEuZGVmZWN0TG9jaz09PXRydWU7CiAgLy8gSGFtbWVyIGhlciB3'
        'aGlsZSBzaGUgaXMgc3RpbGwgb3Vyczogc2hlIG11c3Qgbm90IGRpZSBiZWZvcmUgdGhlIHR1cm4u'
        'CiAgaWYoYSl7IGEuaHAgPSAxOyBGUy5zdGVwKDUpOyB9CiAgci5zdXJ2aXZlc0xvY2sgPSAhIWFs'
        'bGllcy5maW5kKHg9PngudWlkPT09J0ExJyk7CiAgLy8gU3RlcCBieSBzdGVwIHVwIHRvIHRoZSB0'
        'dXJuOiB3aGVyZSBzaGUgd2FzIGxhc3QgYXMgYW4gYWxseSwgYW5kIHdoZXJlCiAgLy8gc2hlIGlz'
        'IGluIHRoZSBmaXJzdCBzdGVwIGFzIGFuIGVuZW15LgogIGxldCBsYXN0ID0gbnVsbCwgZmlyc3Qg'
        'PSBudWxsOwogIGZvcihsZXQgaz0wO2s8ODAwMCAmJiAhZmlyc3Q7aysrKXsKICAgIGlmKGslMjAw'
        'PT09MCkgRlMua2lsbFNtYWxsKCk7CiAgICBjb25zdCBhbCA9IGFsbGllcy5maW5kKHg9PngudWlk'
        'PT09J0ExJyk7CiAgICBpZihhbCkgbGFzdCA9IHt4OmFsLngsIHk6YWwueX07CiAgICBGUy5zdGVw'
        'KDEpOwogICAgY29uc3QgZW4gPSBlbmVtaWVzLmZpbmQoeD0+eC51aWQ9PT0nQTEnKTsKICAgIGlm'
        'KGVuKSBmaXJzdCA9IHt4OmVuLngsIHk6ZW4ueX07CiAgfQogIHIudHVybnNJblBsYWNlID0gISFs'
        'YXN0ICYmICEhZmlyc3QgJiYgTWF0aC5hYnMoZmlyc3QueC1sYXN0LngpIDwgMiAmJiBNYXRoLmFi'
        'cyhmaXJzdC55LWxhc3QueSkgPCAyOwogIGNvbnN0IGUgPSBlbmVtaWVzLmZpbmQoeD0+eC51aWQ9'
        'PT0nQTEnKTsKICAvLyBGcm9tIGhlcmUgb24gdGhlIGFsbGllZCB3aW5ncyBjb3VsZCBzaG9vdCBo'
        'ZXIgZG93biBvciBoaXQgaGVyIGVuZ2luZXMKICAvLyBiZWZvcmUgc2hlIGdldHMgYW55d2hlcmUg'
        'LSB0aGF0IGlzIHRoZSBnYW1lIC0gc28gZm9yIHRoZSBjaGVja3MgYmVsb3cKICAvLyBzaGUgYW5k'
        'IGhlciBzdWJzeXN0ZW1zIGFyZSBtYWRlIHRvbyB0b3VnaCBmb3IgdGhlbS4KICBpZihlKXsgZS5o'
        'cCA9IGUubWF4SHAgPSAxZTc7IGZvcihjb25zdCBzIG9mIGUuc3Vic3x8W10pIHMuaHAgPSBzLm1h'
        'eEhwID0gMWU3OyB9CiAgRlMuc3RlcCg0MCk7CiAgci50dXJuZWQgPSAhIWUgJiYgIWFsbGllcy5z'
        'b21lKHg9PngudWlkPT09J0ExJyk7CiAgci5udGZIdWxsID0gISFlICYmIGUuaW1nPT09J250ZmNy'
        'bGV2aWF0aGFuJzsKICByLmVuZW15U2hhcGUgPSAhIWUgJiYgZS50eXBlPT09J2NydWlzZXInICYm'
        'IGUuc2lkZT09PSdlbmVteScgJiYgIWUuZGVhZCAmJiBlLmhwPjA7CiAgci5oYXNTdWJzID0gISFl'
        'ICYmICEhZS5zdWJzICYmIGUuc3Vicy5sZW5ndGg9PT01OwogIHIuaGFzR3VucyA9ICEhZSAmJiAh'
        'IShlLmd1bnN8fGUubW91bnRzfHxlLndwbnx8ZS5iZWFtcyk7CiAgci5mYWNlc1doZXJlU2hlR29l'
        'cyA9ICEhZSAmJiBlLmZsaXA9PT1uZWVkc0ZsaXAoZS5pbWcsIGZhbHNlKTsKICBjb25zdCB4MCA9'
        'IGUgPyBlLnggOiAwOwogIEZTLnN0ZXAoMjAwKTsKICByLndhdmVPcGVuV2hpbGVTaGVMaXZlcyA9'
        'ICF3YXZlT3ZlcjsKICByLmhlYWRzUmlnaHQgPSAhIWUgJiYgZS54ID4geDA7CiAgLy8gTGVmdCBh'
        'bG9uZSBzaGUgcmVhY2hlcyB0aGUgZWRnZSBhbmQganVtcHMuCiAgY29uc3QgdCA9IEZTLnVudGls'
        'KCgpPT4hIUVWX0xFRlRbJ0ExJ10sIDgwMDAsIHRydWUpOwogIHIuanVtcHNBdFRoZUVkZ2UgPSB0'
        'Pj0wICYmIGUud2FycE91dD4wICYmIGUueCA8IFc7CiAgci53aGlsZUZ1bGx5T25TY3JlZW4gPSAh'
        'IWUgJiYgZS54ICsgSU1HU1tlLmltZ10ud2lkdGgqZS5zYyowLjUgPD0gVzsKICBGUy51bnRpbCgo'
        'KT0+IWVuZW1pZXMuaW5jbHVkZXMoZSksIDEwMDAsIGZhbHNlKTsKICByLmdvbmVBZnRlckp1bXAg'
        'PSAhZW5lbWllcy5pbmNsdWRlcyhlKTsKICBGUy51bnRpbCgoKT0+d2F2ZU92ZXIgfHwgd2F2ZT4z'
        'MSwgNDAwMCwgdHJ1ZSk7CiAgci53YXZlRW5kcyA9IHdhdmVPdmVyIHx8IHdhdmU+MzE7CiAgcmV0'
        'dXJuIHI7YCk7CgpzY2VuYXJpbygnTTMxIGVuZ2luZXMgc3RvcCBoZXInLCAnbT0zMScsIGAKICBG'
        'Uy5zdGVwKDMwMCk7CiAgRlMudW50aWwoKCk9PiFlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nRTEn'
        'KSAmJiAhc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nRTEnKSwgNjAwMCwgdHJ1ZSk7CiAgRlMuc3Rl'
        'cCg0MCk7CiAgY29uc3QgZSA9IGVuZW1pZXMuZmluZCh4PT54LnVpZD09PSdBMScpOwogIGZvcihj'
        'b25zdCBzIG9mIGUuc3VicykgaWYocy5pZD09PSdlbmdpbmVzJyl7IHMuZGVhZCA9IHRydWU7IHMu'
        'aHAgPSAwOyB9CiAgY29uc3QgeDAgPSBlLng7IEZTLnN0ZXAoNjAwKTsKICByZXR1cm4ge3N0b3Bw'
        'ZWQ6IE1hdGguYWJzKGUueC14MCkgPCAwLjAxICYmICFFVl9MRUZUWydBMSddfTtgKTsKCnNjZW5h'
        'cmlvKCdNMzIgRGllIEZyYWNodHJvdXRlJywgJ209MzInLCBgCiAgY29uc3QgciA9IHt9OwogIEZT'
        'LnN0ZXAoMzAwKTsKICBjb25zdCBmID0gYWxsaWVzLmZpbHRlcih4PT54LnVpZD09PSdGMScpOwog'
        'IHIudHdvRnJlaWdodGVycyA9IGYubGVuZ3RoPT09MiAmJiBmLmV2ZXJ5KHg9PnguaW1nPT09J2Zy'
        'cG9zZWlkb24nKTsKICByLnRlcnJhblNpZGUgPSBmLmV2ZXJ5KHg9PnguZmFjdGlvbj09PSd0ZXJy'
        'YW4nKTsKICByLm1lZHVzYXMgPSBlbmVtaWVzLmZpbHRlcihlPT5lLnVpZD09PSdCMScpLmV2ZXJ5'
        'KGU9PmUuaW1nPT09J2JvbWVkdXNhJykgJiYgZW5lbWllcy5zb21lKGU9PmUudWlkPT09J0IxJyk7'
        'CiAgci5maWdodGVyQ292ZXIgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nRTEnICYmIGUudHlw'
        'ZT09PSdmaWdodGVyJykgfHwgc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nRTEnKTsKICBjb25zdCB4'
        'MCA9IGYubGVuZ3RoID8gZlswXS54IDogMDsgRlMuc3RlcCgzMDApOwogIHIuY3Jvc3NpbmcgPSBm'
        'Lmxlbmd0aD4wICYmIGZbMF0ueCA+IHgwOwogIEZTLnVudGlsKCgpPT4hZW5lbWllcy5zb21lKGU9'
        'PmUudWlkPT09J0IxJyksIDQwMDAsIHRydWUpOwogIEZTLnN0ZXAoMzAwKTsKICByLnNlY29uZFJh'
        'aWQgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nQjInKSB8fCBzcGF3blEuc29tZShxPT5xLnVp'
        'ZD09PSdCMicpOwogIHIuZW5kc1doZW5UaHJvdWdoID0gRlMudW50aWwoKCk9PndhdmVPdmVyLCAy'
        'MDAwMCwgdHJ1ZSkgPj0gMDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNMzMgRGllIFJlbGFp'
        'c3N0YXRpb24nLCAnbT0zMycsIGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCgzMDApOwogIGNv'
        'bnN0IHMgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nUzEnKTsKICByLmZhdXN0dXMgPSAhIXMg'
        'JiYgcy5pbWc9PT0nc2NmYXVzdHVzJzsKICByLmF0R2l2ZW5IZWlnaHQgPSAhIXMgJiYgTWF0aC5h'
        'YnMocy55LTI1MCkgPCAxOwogIGNvbnN0IHgwID0gcyA/IHMueCA6IDA7CiAgRlMuc3RlcCgxMjAw'
        'KTsKICByLnN0YXlzUHV0ID0gISFzICYmIE1hdGguYWJzKHMueC14MCkgPCAxICYmIE1hdGguYWJz'
        'KHMueS0yNTApIDwgMTsKICByLm5vRmxhayA9ICEhcyAmJiBmbGFrSGFzKHMpPT09ZmFsc2U7CiAg'
        'ci5ndW5zID0gZW5lbWllcy5maWx0ZXIoZT0+ZS51aWQ9PT0nRzEnKS5sZW5ndGg9PT00OwogIC8v'
        'IFJlaW5mb3JjZW1lbnRzIGtlZXAgY29taW5nIHdoaWxlIHNoZSBzdGFuZHMuCiAgRlMua2lsbFNt'
        'YWxsKCk7IEZTLnN0ZXAoOTAwKTsKICByLnJlaW5mb3JjZWQgPSBlbmVtaWVzLnNvbWUoZT0+ZS50'
        'eXBlPT09J2ZpZ2h0ZXInICYmICFlLnVpZCkgfHwgc3Bhd25RLnNvbWUocT0+IXEudWlkICYmIC9e'
        'ZmlfLy50ZXN0KHEudHlwZSkpOwogIGNvbnN0IGJlZm9yZSA9IFNIT0NLUy5sZW5ndGg7CiAgRlMu'
        'a2lsbElkKCdTMScpOyBGUy5zdGVwKDMpOwogIHIuYmlnQmxhc3QgPSBTSE9DS1Muc29tZShrPT5r'
        'LnJNYXg9PT0zMDApOwogIEZTLmtpbGxTbWFsbCgpOyBGUy5zdGVwKDEyMDApOyBGUy5raWxsU21h'
        'bGwoKTsgRlMuc3RlcCg2MDApOwogIHIucmVpbmZPZmYgPSBldlJlaW5mPT09ZmFsc2U7CiAgcmV0'
        'dXJuIHI7YCk7CgpzY2VuYXJpbygnTTM0IERpZSBGbGFrd2FuZCcsICdtPTM0JywgYAogIGNvbnN0'
        'IHIgPSB7fTsKICBzY29yZSA9IDIwMDAwOyAgIC8vIGVub3VnaCBmb3IgdGhlIEFydGVtaXMgdG8g'
        'YmUgb3BlbiBpbiB0aGlzIGN5Y2xlCiAgRlMuc3RlcCg0MDApOwogIGNvbnN0IGsgPSBlbmVtaWVz'
        'LmZpbHRlcihlPT5lLnVpZD09PSdLMScpOwogIHIudHdvQWVvbHVzID0gay5sZW5ndGg9PT0yICYm'
        'IGsuZXZlcnkoZT0+ZS5pbWc9PT0nbnRmY3JhZW9sdXMnKTsKICByLmZsYWsgPSBrLmV2ZXJ5KGU9'
        'PmZsYWtIYXMoZSkpOwogIHIubm9IYW5nYXJZZXQgPSAhYWxsaWVzLnNvbWUoYT0+YS51aWQ9PT0n'
        'QTEnKTsKICBGUy51bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdFMScpICYmICFz'
        'cGF3blEuc29tZShxPT5xLnVpZD09PSdFMScpLCA1MDAwLCB0cnVlKTsKICBGUy5zdGVwKDQwMCk7'
        'CiAgY29uc3QgbyA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J0ExJyk7CiAgci5vcmlvbiA9ICEh'
        'byAmJiBvLmltZz09PSdkZW9yaW9ucmlnaHQnOwogIHRpY2tTaGlwVW5sb2NrcygpOwogIHIuYm9t'
        'YmVyT2ZmZXJlZCA9IHNoaXBPZmZlcmVkKCdib2FydGVtaXMnKSAmJiBzaGlwU3dhcFJlYWR5KCk7'
        'CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTM1IERlciBVZWJlcmxhZXVmZXInLCAnbT0zNScs'
        'IGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IGQgPSBhbGxpZXMuZmlu'
        'ZChhPT5hLnVpZD09PSdBMScpOwogIHIubnRmRGVpbW9zID0gISFkICYmIGQuaW1nPT09J250ZmNv'
        'ZGVpbW9zJyAmJiBkLnR5cGU9PT0nY29ydmV0dGUnOwogIHIuY29tZXNGcm9tVGhlUmlnaHQgPSAh'
        'IWQgJiYgZC54ID4gVyowLjY7CiAgci5mYWNlc0xlZnQgPSAhIWQgJiYgZC5mbGlwPT09bmVlZHNG'
        'bGlwKCdudGZjb2RlaW1vcycsIHRydWUpOwogIHIuY3Jvc3NpbmcgPSAhIWQgJiYgZC50cmFuc2l0'
        'PT09dHJ1ZTsKICByLmZpcnN0V2luZ0h1bnRzSGVyID0gd2F2ZUh1bnQ9PT0nQTEnOwogIGNvbnN0'
        'IHgwID0gZCA/IGQueCA6IDA7IEZTLnN0ZXAoMjAwKTsKICByLmhlYWRzTGVmdCA9ICEhZCAmJiBk'
        'LnggPCB4MDsKICBGUy51bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdFMScpICYm'
        'ICFzcGF3blEuc29tZShxPT5xLnVpZD09PSdFMScpLCA1MDAwLCB0cnVlKTsKICBGUy5zdGVwKDIw'
        'KTsKICByLnJlaW5mb3JjZW1lbnRzT24gPSBldlJlaW5mPT09dHJ1ZTsKICByLmZvbGxvd1Vwc1Nj'
        'cmVlbiA9IHdhdmVIdW50PT09Jyc7CiAgci5yZWFybSA9IGNvcnZldHRlT25GaWVsZCgpOwogIHIu'
        'bm90T25DYWxsTWVudSA9IEFMTFlfT1JERVIuaW5kZXhPZignbnRmX2RlaW1vcycpPDA7CiAgLy8g'
        'V2hhdCBpcyBjaGVja2VkIGhlcmUgaXMgdGhlIGNyb3NzaW5nLCBub3QgdGhlIGJhbGFuY2UgLSBT'
        'aWx2aW8gcGxheXMKICAvLyB0aGF0LiBTbyBzaGUgaXMgbWFkZSB0b28gdG91Z2ggdG8gbG9zZSBv'
        'biB0aGUgd2F5LgogIGQuaHAgPSBkLm1heEhwID0gMWU3OwogIGZvcihjb25zdCBzIG9mIGQuc3Vi'
        'c3x8W10pIHMuaHAgPSBzLm1heEhwID0gMWU3OyAgICAvLyBlbmdpbmVzIHRvbzogZGVhZCBlbmdp'
        'bmVzIHN0b3AgYSBjcm9zc2luZwogIGNvbnN0IGdvdCA9IEZTLnVudGlsKCgpPT57IGlmKGFsbGll'
        'cy5pbmNsdWRlcyhkKSkgZC5ocCA9IGQubWF4SHA7IHJldHVybiAhYWxsaWVzLnNvbWUoYT0+YS51'
        'aWQ9PT0nQTEnKTsgfSwgOTAwMCwgdHJ1ZSk7CiAgci5nZXRzQWNyb3NzID0gZ290Pj0wICYmICFn'
        'dWFyZExvc3Q7CiAgci5sZWZ0Q291bnRzID0gISFFVl9MRUZUWydBMSddOwogIHIubm90aGluZ01v'
        'cmVDb21lcyA9IGV2UmVpbmY9PT1mYWxzZSAmJiBzcGF3blEubGVuZ3RoPT09MDsKICBGUy51bnRp'
        'bCgoKT0+d2F2ZU92ZXIsIDQwMDAsIHRydWUpOwogIHIud2F2ZUVuZHMgPSB3YXZlT3ZlcjsKICBy'
        'ZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNMzYgRGllIEljZW5pJywgJ209MzYnLCBgCiAgY29uc3Qg'
        'ciA9IHt9OwogIGNvbnN0IHMwID0gc2NvcmUgPSA1MDAwOwogIEZTLnN0ZXAoMzAwKTsKICBjb25z'
        'dCBpID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyk7CiAgci5pY2VuaSA9ICEhaSAmJiBp'
        'LmljZW5pPT09dHJ1ZSAmJiBpLmltZz09PSdjb2ljZW5pJzsKICByLm5vTmF2aWdhdGlvbiA9ICEh'
        'aSAmJiAhIWkuc3VicyAmJiBpLnN1YnMubGVuZ3RoPT09NCAmJiBzdWJPSyhpLCduYXZpZ2F0aW9u'
        'Jyk7CiAgci5kZWFkbGluZSA9ICEhaSAmJiBpLmZsZWVUPjAgJiYgaS5mbGVlVCA8PSAyNSpUSUNL'
        'X0haOwogIEZTLnN0ZXAoNjAwKTsKICByLndob2xlSHVsbE9uU2NyZWVuID0gISFpICYmIGkueCAr'
        'IElNR1NbaS5pbWddLndpZHRoKmkuc2MqMC41IDw9IFc7CiAgY29uc3QgdCA9IEZTLnVudGlsKCgp'
        'PT4hZW5lbWllcy5zb21lKGU9PmUudWlkPT09J1YxJyksIDYwMDAsIGZhbHNlKTsKICByLmp1bXBz'
        'T3V0ID0gdD49MCAmJiBpY2VuRXNjYXBlcz09PTE7CiAgci5ub1BlbmFsdHkgPSBzY29yZSA+PSBz'
        'MDsKICByLmZlbnJpcyA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdLMScgJiYgZS5pbWc9PT0n'
        'bnRmY3JmZW5yaXMnKTsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdDeWNsZSBjaGFuZ2UgMzAg'
        'LT4gMzEnLCAnbT0zMCcsIGAKICBjb25zdCByID0ge307CiAgci5zdGFydHNWYXN1ZGFuID0gcGxh'
        'eWVyLnNoaXA9PT0nZml0b3RoJyAmJiBBTExZX0ZBQ19PTi52YXN1ZGFuPT09dHJ1ZTsKICBzY29y'
        'ZSA9IDkwMDAwOwogIC8vIENsZWFyIHdhdmUgMzAgYnkgZm9yY2UgYW5kIGxldCB0aGUganVtcCBo'
        'YXBwZW4uCiAgZm9yKGxldCBrPTA7azw2MCAmJiB3YXZlPT09MzA7aysrKXsgZm9yKGNvbnN0IGUg'
        'b2YgZW5lbWllcykgaWYoIShlLndhcnA+MCkgJiYgIWUuaW52dWxuKSBlLmhwPTA7IEZTLnN0ZXAo'
        'MjAwKTsgfQogIHIud2F2ZSA9IHdhdmU7CiAgci5teXJtaWRvbiA9IHBsYXllci5zaGlwPT09J2Zp'
        'bXlybWlkb24nOwogIHIub25lSHVsbCA9IHNoaXBVbmxvY2tlZD09PTEgJiYgY3ljbGVCYXNlPT09'
        'c2NvcmUgLSAoc2NvcmUtY3ljbGVCYXNlKTsKICByLmJhc2VTZXQgPSBjeWNsZUJhc2UgPj0gOTAw'
        'MDA7CiAgci50ZXJyYW4gPSBBTExZX0ZBQ19PTi50ZXJyYW49PT10cnVlICYmIEFMTFlfRkFDX09O'
        'LnZhc3VkYW49PT1mYWxzZTsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNMTMgYm90aCB0cmFu'
        'c3BvcnRzIG9uIHRpbWUnLCAnbT0xMycsIGAKICBGUy5zdGVwKDMwMCk7CiAgcmV0dXJuIHtib3Ro'
        'VHJhbnNwb3J0czogYWxsaWVzLmZpbHRlcihhPT5hLnVpZD09PSdUMScpLmxlbmd0aD09PTJ9O2Ap'
        'OwoKLy8gRXZlcnkgd3JpdHRlbiBtaXNzaW9uIGhhcyB0byBjb21lIHRvIGFuIGVuZCB3aGVuIGl0'
        'cyBlbmVtaWVzIGdvIGRvd24sCi8vIHdpdGggbm90aGluZyB0aHJvd24gb24gdGhlIHdheS4gRW5l'
        'bXkgc2hpcHMgYXJlIGNsZWFyZWQgZXZlcnkgdHdvIHNlY29uZHMKLy8gb25jZSB0aGV5IGFyZSBv'
        'dXQgb2YgdGhlaXIgdm9ydGV4IC0gYSBwbGF5ZXIgd2hvIGhpdHMgZXZlcnl0aGluZy4KLy8gU2Nh'
        'biBtaXNzaW9ucyAoMTIsIDIzKSBuZWVkIHRoZSBwbGF5ZXIgdG8gZmx5IHRoZSBzY2FuIGFuZCBh'
        'cmUgbGVmdCBvdXQuCmZvcihsZXQgbT0xO208PTU0O20rKykgaWYobSE9PTEyICYmIG0hPT0yMykg'
        'c2NlbmFyaW8oJ00nICsgU3RyaW5nKG0pLnBhZFN0YXJ0KDIsJzAnKSArICcgcGxheXMgdG8gdGhl'
        'IGVuZCcsICdtPScgKyBtLCBgCiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT53YXZlT3ZlciwgNDAw'
        'MDAsIGZhbHNlLCB0cnVlKTsKICBJVEVNUy5sZW5ndGggPSAwOyAgICAgLy8gcGlja3VwcyBob2xk'
        'IHRoZSBqdW1wIG9wZW4gdW50aWwgdGhleSBleHBpcmUKICBjb25zdCBqID0gRlMudW50aWwoKCk9'
        'PndhdmUgPT09ICR7bX0rMSwgNjAwMCwgZmFsc2UsIGZhbHNlKTsKICByZXR1cm4ge2VuZHM6IHQg'
        'Pj0gMCwgbmV4dFdhdmU6IGogPj0gMH07YCk7CgpzY2VuYXJpbygnUGlja3VwcyBhcmUgZHJhd24g'
        'dG8gdGhlIHNoaXAnLCAnbT0xJywgYAogIEZTLnN0ZXAoMjAwKTsKICBjb25zdCByID0ge307CiAg'
        'dGlja2V0cy5jcnVpc2VyID0gMDsKICBJVEVNUy5wdXNoKHt4OnBsYXllci54KzEwMCwgeTpwbGF5'
        'ZXIueSwgdng6SVRFTV9EUklGVCwgdnk6MCwga2luZDonY3J1aXNlcicsIGxpZmU6NTAwMH0pOwog'
        'IElURU1TLnB1c2goe3g6cGxheWVyLngrNDAwLCB5OnBsYXllci55KzEwMCwgdng6MCwgdnk6MCwg'
        'a2luZDoncmVwYWlyJywgbGlmZTo1MDAwfSk7CiAgY29uc3QgZmFyID0gSVRFTVNbMV07CiAgRlMu'
        'c3RlcCg2MCk7CiAgci5uZWFyT25lQ29sbGVjdGVkID0gdGlja2V0cy5jcnVpc2VyPT09MTsKICBy'
        'LmZhck9uZUxlZnRBbG9uZSA9IElURU1TLmluY2x1ZGVzKGZhcikgJiYgIWZhci5jYXVnaHQ7CiAg'
        'Ly8gQ2F1Z2h0LCBpdCBrZWVwcyBmb2xsb3dpbmcgZXZlbiBpZiB0aGUgc2hpcCBwdWxscyBhd2F5'
        'LgogIHBsYXllci54ID0gMTAwOyBwbGF5ZXIueSA9IDI1MDsKICBJVEVNUy5wdXNoKHt4OjIxMCwg'
        'eToyNTAsIHZ4OjAsIHZ5OjAsIGtpbmQ6J2NvcnZldHRlJywgbGlmZTo1MDAwfSk7CiAgY29uc3Qg'
        'YyA9IElURU1TW0lURU1TLmxlbmd0aC0xXTsKICBGUy5zdGVwKDEpOwogIHIuY2F1Z2h0ID0gYy5j'
        'YXVnaHQ9PT10cnVlOwogIGxldCBnb3QgPSBmYWxzZTsKICBmb3IobGV0IGs9MDtrPDIwMCAmJiAh'
        'Z290O2srKyl7IHBsYXllci54ID0gNjA7IHBsYXllci55ID0gMjUwOyBGUy5zdGVwKDEpOyBnb3Qg'
        'PSAhSVRFTVMuaW5jbHVkZXMoYyk7IH0KICByLmZvbGxvd3NBbmRBcnJpdmVzID0gZ290OwogIHJl'
        'dHVybiByO2ApOwoKc2NlbmFyaW8oJ1RpdGxlOiBmdWxsc2NyZWVuIGJ1dHRvbicsICcnLCBgCiAg'
        'Y29uc3QgciA9IHt9OwogIGxldCBjYWxscyA9IDA7CiAgdG9nZ2xlRnVsbHNjcmVlbiA9IGZ1bmN0'
        'aW9uKCl7IGNhbGxzKys7IH07CiAgZHJhdygpOwogIGNvbnN0IGIgPSB3aW5kb3cuX3RpdGxlRnNS'
        'ZWN0OwogIHIuc2hvd24gPSAhIWIgJiYgYi54ID49IDAgJiYgYi54ICsgYi53IDw9IFcgJiYgYi55'
        'ID49IDAgJiYgYi55ICsgYi5oIDw9IEg7CiAgci5jbGVhck9mVGhlVGl0bGUgPSAhIWIgJiYgYi55'
        'ICsgYi5oIDwgMTI4IC0gNTQ7CiAgY29uc3QgY3IgPSBDVlMuZ2V0Qm91bmRpbmdDbGllbnRSZWN0'
        'KCk7CiAgY29uc3QgY2xpY2sgPSAoZ3gsIGd5KT0+ewogICAgY29uc3QgZXYgPSBuZXcgTW91c2VF'
        'dmVudCgnbW91c2Vkb3duJywge2J1dHRvbjowLCBidWJibGVzOnRydWUsCiAgICAgIGNsaWVudFg6'
        'IGNyLmxlZnQgKyBneCpjci53aWR0aC9XLCBjbGllbnRZOiBjci50b3AgKyBneSpjci5oZWlnaHQv'
        'SH0pOwogICAgQ1ZTLmRpc3BhdGNoRXZlbnQoZXYpOwogICAgQ1ZTLmRpc3BhdGNoRXZlbnQobmV3'
        'IE1vdXNlRXZlbnQoJ21vdXNldXAnLCB7YnV0dG9uOjAsIGJ1YmJsZXM6dHJ1ZX0pKTsKICB9Owog'
        'IGNsaWNrKGIueCArIGIudy8yLCBiLnkgKyBiLmgvMik7CiAgci5idXR0b25Td2l0Y2hlcyA9IGNh'
        'bGxzPT09MTsKICByLmFuZERvZXNOb3RTdGFydFRoZVJ1biA9IEdTPT09J3RpdGxlJzsKICBkb2N1'
        'bWVudC5kaXNwYXRjaEV2ZW50KG5ldyBLZXlib2FyZEV2ZW50KCdrZXlkb3duJywge2NvZGU6J0tl'
        'eUYnfSkpOwogIGRvY3VtZW50LmRpc3BhdGNoRXZlbnQobmV3IEtleWJvYXJkRXZlbnQoJ2tleXVw'
        'Jywge2NvZGU6J0tleUYnfSkpOwogIHIuZktleU9uVGhlVGl0bGUgPSBjYWxscz09PTIgJiYgR1M9'
        'PT0ndGl0bGUnOwogIGNsaWNrKFcvMiwgSC8yKTsKICByLmVsc2V3aGVyZVN0YXJ0c1RoZVJ1biA9'
        'IEdTPT09J3BsYXlpbmcnICYmIGNhbGxzPT09MjsKICByZXR1cm4gcjtgLCB0cnVlKTsKCnNjZW5h'
        'cmlvKCdNMzcgRGllIFVuc2ljaHRiYXJlbicsICdtPTM3JywgYAogIGNvbnN0IHIgPSB7fTsKICBG'
        'Uy5zdGVwKDQwMCk7CiAgY29uc3QgbG9raXMgPSBlbmVtaWVzLmZpbHRlcihlPT5lLnVpZD09PSdF'
        'MScpOwogIHIubG9raXMgPSBsb2tpcy5sZW5ndGg+MCAmJiBsb2tpcy5ldmVyeShlPT5lLmltZz09'
        'PSdmaWxva2knKTsKICByLm5vTG9ja09uVGhlbSA9IGxva2lzLmxlbmd0aD4wICYmIGxva2lzLmV2'
        'ZXJ5KGU9PiFjYW5Mb2NrT24oZSkpOwogIHIuaW5QbGFpblNpZ2h0ID0gbG9raXMuZXZlcnkoZT0+'
        'IWUuaGlkZGVuICYmICFlLmNsb2FrICYmIGUuYWxwaGE9PT11bmRlZmluZWQpOwogIC8vIEFuIGVu'
        'ZW15IGZpZ2h0ZXIgb2YgYW55IG90aGVyIGh1bGwgY2FuIHN0aWxsIGJlIGxvY2tlZC4KICBjb25z'
        'dCBvdGhlciA9IHtzaWRlOidlbmVteScsIGltZzonZmloZXJjJ307CiAgci5vdGhlcnNTdGlsbExv'
        'Y2thYmxlID0gY2FuTG9ja09uKG90aGVyKTsKICAvLyBBIHBsYXllciBMb2tpIGxhdGVyIG9uIGtl'
        'ZXBzIGl0cyBvd24gcnVsZXM6IHRoZSBuby1sb2NrIGlzIGVuZW15IG9ubHkuCiAgci5vbmx5VGhl'
        'RW5lbXlTaWRlID0gY2FuTG9ja09uKHtzaWRlOidhbGx5JywgaW1nOidmaWxva2knfSk7CiAgLy8g'
        'Q2xlYXIgdGhlbSBsb3QgYnkgbG90IGFuZCBub3RlIGV2ZXJ5IGxvdCB0aGF0IHNob3dzIHVwLgog'
        'IGNvbnN0IHNlZW4gPSB7fTsKICBGUy51bnRpbCgoKT0+eyBmb3IoY29uc3QgZSBvZiBlbmVtaWVz'
        'KSBpZihlLnVpZCl7IHNlZW5bZS51aWRdID0gc2VlbltlLnVpZF0gfHwgZS5pbWc7IH0gcmV0dXJu'
        'IHdhdmVPdmVyOyB9LCAyMDAwMCwgdHJ1ZSk7CiAgci50aHJlZUxvdHNPZkxva2lzID0gc2Vlbi5F'
        'MT09PSdmaWxva2knICYmIHNlZW4uRTI9PT0nZmlsb2tpJyAmJiBzZWVuLkUzPT09J2ZpbG9raSc7'
        'CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTM4IERpZSBLYXBlcnVuZycsICdtPTM4JywgYAog'
        'IGNvbnN0IHIgPSB7fTsKICBzY29yZSA9IDEwMDA7CiAgRlMuc3RlcCg0MDApOwogIGNvbnN0IGQg'
        'PSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nRDEnKTsKICByLmRlaW1vcyA9ICEhZCAmJiBkLmlt'
        'Zz09PSdudGZjb2RlaW1vcyc7CiAgci5taWRGaWVsZCA9ICEhZCAmJiBNYXRoLmFicyhkLnktMjYw'
        'KSA8IDE7CiAgci5oZWFkc1JpZ2h0ID0gISFkICYmIGQuZXNjYXBpbmc+MCAmJiBkLmZsaXA9PT1u'
        'ZWVkc0ZsaXAoZC5pbWcsIGZhbHNlKTsKICByLnNheXNXaGF0VG9EbyA9IG1pc3Npb25PYmo9PT0n'
        'RElTQUJMRSBUSEUgREVJTU9TIC0gRU5HSU5FUyBBTkQgV0VBUE9OUyc7CiAgZGFtYWdlRW5lbXko'
        'ZCwgZC5tYXhIcCo1LCBkLngsIGQueSwgdHJ1ZSwgJ2JvbHQnKTsgRlMuc3RlcCgzKTsKICByLmNh'
        'bm5vdEJlRGVzdHJveWVkID0gZW5lbWllcy5pbmNsdWRlcyhkKSAmJiBkLmhwID4gMDsKICBjb25z'
        'dCBraWxsID0gaWQ9PnsgZm9yKGNvbnN0IHMgb2YgZC5zdWJzKSBpZihzLmlkPT09aWQpeyBzLmRl'
        'YWQ9dHJ1ZTsgcy5ocD0wOyB9IH07CiAga2lsbCgnZW5naW5lcycpOwogIGNvbnN0IHgwID0gZC54'
        'OyBGUy5zdGVwKDMwMCk7CiAgci5lbmdpbmVzU3RvcEhlciA9IE1hdGguYWJzKGQueC14MCkgPCAw'
        'LjAxOwogIHIubm9FbHlzaXVtV2hpbGVIZXJHdW5zV29yayA9ICFhbGxpZXMuc29tZShhPT5hLnVp'
        'ZD09PSdUMScpICYmICFzcGF3blEuc29tZShxPT5xLnVpZD09PSdUMScpOwogIGtpbGwoJ3dlYXBv'
        'bnMnKTsgRlMuc3RlcCgyKTsKICByLm5ld09iamVjdGl2ZSA9IG1pc3Npb25PYmo9PT0nQ09WRVIg'
        'VEhFIEVMWVNJVU0nOwogIEZTLnN0ZXAoMjAwKTsKICByLmVseXNpdW1Db21lc09uY2VCb3RoQXJl'
        'RG93biA9IGFsbGllcy5zb21lKGE9PmEudWlkPT09J1QxJyAmJiBhLmltZz09PSd0cmVseXNpdW0n'
        'KSB8fCBzcGF3blEuc29tZShxPT5xLnVpZD09PSdUMScpIHx8ICEhRVZfRE9DS1snVDEnXTsKICBj'
        'b25zdCBnb3QgPSBGUy51bnRpbCgoKT0+ISFFVl9ET0NLWydUMSddLCA5MDAwLCB0cnVlKTsKICBG'
        'Uy5zdGVwKDUpOwogIHIuZG9ja3MgPSBnb3Q+PTA7CiAgci50YWtlbiA9IGQuY2FwdHVyZWQ9PT10'
        'cnVlICYmICEhRVZfVEFLRU5bJ0QxJ10gJiYgKGQud2FycE91dD4wIHx8ICFlbmVtaWVzLmluY2x1'
        'ZGVzKGQpKTsKICByLmNvbXBsZXRlQ2FyZCA9ICEhb2JqQ2FyZCAmJiBvYmpDYXJkLmhlYWQ9PT0n'
        'T0JKRUNUSVZFIENPTVBMRVRFJyAmJiBvYmpDYXJkLnR4dD09PSdERUlNT1MgQ0FQVFVSRUQnOwog'
        'IHIucG9pbnRzRm9ySGVyID0gc2NvcmUgPj0gMTAwMCArIChkLnB0c3x8MCk7CiAgRlMudW50aWwo'
        'KCk9PiFlbmVtaWVzLmluY2x1ZGVzKGQpLCAxMDAwLCBmYWxzZSk7CiAgRlMuc3RlcCg1MCk7CiAg'
        'ci5ub0ZhaWx1cmVBZnRlcndhcmRzID0gIShvYmpDYXJkICYmIG9iakNhcmQudG9uZT09PSdmYWls'
        'Jyk7CiAgci5sZWF2ZXNXaXRob3V0UGVuYWx0eSA9ICFlbmVtaWVzLmluY2x1ZGVzKGQpICYmIHNj'
        'b3JlID49IDEwMDAgKyAoZC5wdHN8fDApOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ00zOCBF'
        'bHlzaXVtIGxvc3Q6IHNoZSBjYW4gZGllJywgJ209MzgnLCBgCiAgRlMuc3RlcCg0MDApOwogIGNv'
        'bnN0IGQgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nRDEnKTsKICBmb3IoY29uc3QgcyBvZiBk'
        'LnN1YnMpIGlmKHMuaWQ9PT0nZW5naW5lcyd8fHMuaWQ9PT0nd2VhcG9ucycpeyBzLmRlYWQ9dHJ1'
        'ZTsgcy5ocD0wOyB9CiAgRlMudW50aWwoKCk9PmFsbGllcy5zb21lKGE9PmEudWlkPT09J1QxJyks'
        'IDIwMDAsIHRydWUpOwogIGZvcihjb25zdCBhIG9mIGFsbGllcykgaWYoYS51aWQ9PT0nVDEnKSBh'
        'LmhwID0gMDsKICBGUy5zdGVwKDMwKTsKICBjb25zdCBmcmVlZCA9IGQuY2FwdHVyZUxvY2s9PT1m'
        'YWxzZTsKICBjb25zdCBmYWlsQ2FyZCA9ICEhb2JqQ2FyZCAmJiBvYmpDYXJkLnRvbmU9PT0nZmFp'
        'bCcgJiYgb2JqQ2FyZC50eHQ9PT0nRUxZU0lVTSBMT1NUJzsKICBkLmhwID0gMDsgRlMuc3RlcCgz'
        'MDApOwogIHJldHVybiB7ZnJlZWQ6IGZyZWVkLCBmYWlsQ2FyZDogZmFpbENhcmQsIHRoZW5EZXN0'
        'cm95YWJsZTogIWVuZW1pZXMuaW5jbHVkZXMoZCkgJiYgIUVWX0xFRlRbJ0QxJ119O2ApOwoKc2Nl'
        'bmFyaW8oJ00zOCBsZWZ0IGFsb25lIHNoZSBqdW1wcyBhdCB0aGUgZWRnZScsICdtPTM4JywgYAog'
        'IEZTLnN0ZXAoMzAwKTsKICBjb25zdCBkID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J0QxJyk7'
        'CiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT4hIUVWX0xFRlRbJ0QxJ10sIDgwMDAsIHRydWUpOwog'
        'IEZTLnN0ZXAoMik7CiAgcmV0dXJuIHtqdW1wczogdD49MCAmJiBkLndhcnBPdXQ+MCAmJiAhZC5j'
        'YXB0dXJlZCwgb25TY3JlZW46IGQueCArIElNR1NbZC5pbWddLndpZHRoKmQuc2MqMC41IDw9IFcs'
        'CiAgICAgICAgICBmYWlsQ2FyZDogISFvYmpDYXJkICYmIG9iakNhcmQudG9uZT09PSdmYWlsJyAm'
        'JiBvYmpDYXJkLnR4dD09PSdUSEUgREVJTU9TIEdPVCBBV0FZJ307YCk7CgpzY2VuYXJpbygnTTM5'
        'IERpZSBHYXNlcm50ZScsICdtPTM5JywgYAogIGNvbnN0IHIgPSB7fTsKICByLm5lYnVsYSA9IG5l'
        'YnVsYU9uKCk9PT10cnVlOwogIEZTLnN0ZXAoMTYwMCk7CiAgY29uc3QgbSA9IGVuZW1pZXMuZmls'
        'dGVyKGU9Pi9eTS8udGVzdChlLnVpZHx8JycpKTsKICByLnRocmVlTWluZXJzID0gbS5sZW5ndGg9'
        'PT0zICYmIG0uZXZlcnkoZT0+ZS5pbWc9PT0nZ216ZXBoeXJ1cycpOwogIHIucnVubmluZyA9IG0u'
        'ZXZlcnkoZT0+ZS5lc2NhcGluZz4wKTsKICByLmZlbnJpcyA9IGVuZW1pZXMuc29tZShlPT5lLnVp'
        'ZD09PSdLMScgJiYgZS5pbWc9PT0nbnRmY3JmZW5yaXMnKTsKICBjb25zdCBtMSA9IGVuZW1pZXMu'
        'ZmluZChlPT5lLnVpZD09PSdNMScpOwogIG0xLmhwID0gMDsgRlMuc3RlcCgzKTsKICByLmdpYW50'
        'Qmxhc3QgPSBTSE9DS1Muc29tZShrPT5rLnJNYXg9PT00MDApOwogIHJldHVybiByO2ApOwoKc2Nl'
        'bmFyaW8oJ000MCBEZXIgU2Vuc29yc3R1cm0nLCAnbT00MCcsIGAKICBjb25zdCByID0ge307CiAg'
        'ci5uZWJ1bGEgPSBuZWJ1bGFPbigpPT09dHJ1ZTsKICBjb25zdCBzZWVuID0ge307CiAgY29uc3Qg'
        'bm90ZSA9ICgpPT57IGZvcihjb25zdCBlIG9mIGVuZW1pZXMpIGlmKGUudWlkKSBzZWVuW2UudWlk'
        'XT0xOyB9OwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+eyBub3RlKCk7IHJldHVybiBlbXBPdXQ+'
        'MDsgfSwgNjAwMCwgdHJ1ZSk7CiAgci5zdG9ybUhpdHMgPSB0Pj0wOwogIHIubm9Mb2NrSW5UaGVT'
        'dG9ybSA9ICFjYW5Mb2NrT24oe3NpZGU6J2VuZW15JywgaW1nOidmaWhlcmNtazInfSk7CiAgci5v'
        'cmlvbiA9IGFsbGllcy5zb21lKGE9PmEudWlkPT09J0ExJyAmJiBhLmltZz09PSdkZW9yaW9ucmln'
        'aHQnKTsKICBGUy51bnRpbCgoKT0+eyBub3RlKCk7IHJldHVybiB3YXZlT3ZlcjsgfSwgNDAwMDAs'
        'IHRydWUpOwogIHIudGhyZWVSb3VuZHMgPSBbJ0UxJywnQjEnLCdFMicsJ0IyJywnRTMnLCdCMydd'
        'LmV2ZXJ5KGs9PnNlZW5ba10pOwogIGlmKCFyLnRocmVlUm91bmRzKSByLnNlZW4gPSBPYmplY3Qu'
        'a2V5cyhzZWVuKS5qb2luKCkgKyAnIHwgJyArIEVWLm1hcChlPT5lLmErJz4nK2UudysnPicrKGUu'
        'd2F8fCcnKSsnOicrZS5kb25lKS5qb2luKCcgJyk7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygn'
        'TTQxIERhcyBMYXphcmV0dCcsICdtPTQxJywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDMw'
        'MCk7CiAgY29uc3QgaCA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J0gxJyk7CiAgci5oaXBwb2Ny'
        'YXRlcyA9ICEhaCAmJiBoLmltZz09PSdtZWhpcHBvY3JhdGVzJzsKICByLmh1bnRlZCA9IHdhdmVI'
        'dW50PT09J0gxJzsKICBjb25zdCB4MCA9IGggPyBoLnggOiAwOyBGUy5zdGVwKDMwMCk7CiAgci5j'
        'cm9zc2VzU2xvd2x5ID0gISFoICYmIGgueCA+IHgwICYmIChoLngteDApIDwgMTAwOwogIHIuYm9t'
        'YmVycyA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdCMScgJiYgZS5pbWc9PT0nYm9tZWR1c2En'
        'KTsKICBjb25zdCBvcmlnID0gZHJhd0h1bGxCbG9ja3M7IGxldCBiYXJGb3IgPSBmYWxzZTsKICBk'
        'cmF3SHVsbEJsb2NrcyA9IGZ1bmN0aW9uKGUpeyBpZihlPT09aCkgYmFyRm9yID0gdHJ1ZTsgcmV0'
        'dXJuIG9yaWcuYXBwbHkodGhpcywgYXJndW1lbnRzKTsgfTsKICBkcmF3KCk7IGRyYXdIdWxsQmxv'
        'Y2tzID0gb3JpZzsKICByLmh1bGxCYXJPblRoZUhpcHBvY3JhdGVzID0gYmFyRm9yOwogIGNvbnN0'
        'IGdvdCA9IEZTLnVudGlsKCgpPT4hYWxsaWVzLmluY2x1ZGVzKGgpLCA5MDAwLCB0cnVlKTsKICBy'
        'LmdldHNUaHJvdWdoID0gZ290Pj0wICYmICFndWFyZExvc3Q7CiAgcmV0dXJuIHI7YCk7CgpzY2Vu'
        'YXJpbygnTTQyIERpZSBIZWNhdGUnLCAnbT00MicsIGAKICBjb25zdCByID0ge307CiAgRlMuc3Rl'
        'cCg0MDApOyBkcmF3KCk7CiAgci5zYXlzV2hhdFRvRG8gPSBtaXNzaW9uT2JqPT09J0RJU0FCTEUg'
        'SEVDQVRFIFdFQVBPTlMnICYmIG9ialBpbm5lZD09PSdESVNBQkxFIEhFQ0FURSBXRUFQT05TJzsK'
        'ICBjb25zdCB2ID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyk7CiAgci5oZWNhdGUgPSAh'
        'IXYgJiYgdi5pbWc9PT0nbnRmZGVoZWNhdGUnOwogIHIub3Jpb24gPSBhbGxpZXMuc29tZShhPT5h'
        'LnVpZD09PSdBMScpOwogIEZTLnVudGlsKCgpPT4hZW5lbWllcy5zb21lKGU9PmUudWlkPT09J0Ux'
        'JykgJiYgIXNwYXduUS5zb21lKHE9PnEudWlkPT09J0UxJyksIDUwMDAsIHRydWUpOwogIEZTLnN0'
        'ZXAoMjApOwogIHIucmVpbmZvcmNlbWVudHNPbiA9IGV2UmVpbmY9PT10cnVlOwogIGZvcihjb25z'
        'dCBzIG9mIHYuc3VicykgaWYocy5pZD09PSd3ZWFwb25zJyl7IHMuZGVhZD10cnVlOyBzLmhwPTA7'
        'IH0KICBGUy5zdGVwKDIwKTsgZHJhdygpOwogIHIubmV4dFN0ZXAgPSBtaXNzaW9uT2JqPT09J0RF'
        'U1RST1kgVEhFIEhFQ0FURScgJiYgISFvYmpDYXJkICYmIG9iakNhcmQuaGVhZD09PSdORVcgT0JK'
        'RUNUSVZFJyAmJiBvYmpDYXJkLnR4dD09PSdERVNUUk9ZIFRIRSBIRUNBVEUnOwogIHIuZGlzYXJt'
        'ZWRXaXRoZHJhd3MgPSB2LmZsZWVUPjA7CiAgLy8gQSBkZXN0cm95ZXIgZ29lcyBkb3duIGluIGEg'
        'ZGVhdGggcm9sbCB0aGF0IHRha2VzIGEgd2hpbGUuCiAgdi5ocCA9IDA7CiAgci5jb21wbGV0ZUNh'
        'cmQgPSBGUy51bnRpbCgoKT0+eyBkcmF3KCk7IHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC5o'
        'ZWFkPT09J09CSkVDVElWRSBDT01QTEVURScKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg'
        'ICAgICAgICAgICAgJiYgb2JqQ2FyZC50eHQ9PT0nSEVDQVRFIERFU1RST1lFRCc7IH0sIDIwMDAs'
        'IGZhbHNlKSA+PSAwOwogIEZTLnN0ZXAoMzAwKTsKICByLnJlaW5mb3JjZW1lbnRzT2ZmV2hlblNo'
        'ZXNHb25lID0gZXZSZWluZj09PWZhbHNlOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000MiBz'
        'aGUgd2l0aGRyYXdzOiBmYWlsZWQnLCAnbT00MicsIGAKICBGUy5zdGVwKDQwMCk7CiAgY29uc3Qg'
        'diA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdWMScpOwogIC8vIFRvbyB0b3VnaCBmb3IgdGhl'
        'IE9yaW9uIGFuZCBoZXIgd2luZ3MsIGFuZCBoZXIgbmF2aWdhdGlvbiB3aXRoIGl0IC0KICAvLyB3'
        'aXRoIHRoYXQgc2hvdCBvdXQgc2hlIGNvdWxkIG5vdCBqdW1wIGF0IGFsbC4KICB2LmhwID0gdi5t'
        'YXhIcCA9IDFlNzsKICBmb3IoY29uc3QgcyBvZiB2LnN1YnMpeyBpZihzLmlkPT09J3dlYXBvbnMn'
        'KXsgcy5kZWFkPXRydWU7IHMuaHA9MDsgfSBlbHNlIHMuaHAgPSBzLm1heEhwID0gMWU3OyB9CiAg'
        'Y29uc3QgdCA9IEZTLnVudGlsKCgpPT4hIW9iakNhcmQgJiYgb2JqQ2FyZC50b25lPT09J2ZhaWwn'
        'LCA2MDAwLCB0cnVlKTsKICBjb25zdCByID0ge2ZhaWxDYXJkOiB0Pj0wICYmIG9iakNhcmQudHh0'
        'PT09J1RIRSBIRUNBVEUgV0lUSERSRVcnLCBub3RDb21wbGV0ZTogIShvYmpDYXJkICYmIG9iakNh'
        'cmQudG9uZT09PSdkb25lJyl9OwogIEZTLnVudGlsKCgpPT4hZW5lbWllcy5pbmNsdWRlcyh2KSwg'
        'MTAwMCwgZmFsc2UpOyBGUy5zdGVwKDUwKTsKICByLnJlaW5mT2ZmID0gZXZSZWluZj09PWZhbHNl'
        'OwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ00zMyBzYXlzIHdoYXQgdG8gZG8nLCAnbT0zMycs'
        'IGAKICBGUy5zdGVwKDMwMCk7CiAgY29uc3Qgb2sxID0gbWlzc2lvbk9iaj09PSdERVNUUk9ZIFRI'
        'RSBGQVVTVFVTIFJFTEFZJzsKICBjb25zdCBzMSA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdT'
        'MScpOyBzMS5ocCA9IDA7IEZTLnN0ZXAoNSk7CiAgcmV0dXJuIHtzYXlzV2hhdFRvRG86IG9rMSwg'
        'Y29tcGxldGVDYXJkOiAhIW9iakNhcmQgJiYgb2JqQ2FyZC5oZWFkPT09J09CSkVDVElWRSBDT01Q'
        'TEVURScgJiYgb2JqQ2FyZC50eHQ9PT0nUkVMQVkgREVTVFJPWUVEJ307YCk7CgpzY2VuYXJpbygn'
        'QXV0b21hdGljIG9iamVjdGl2ZXM6IGNhcmQsIHRoZW4gdGhlIGxpbmUnLCAnbT0zNScsIGAKICAv'
        'LyBNMzUgc3RhdGVzIG5vIG9iamVjdGl2ZSBvZiBpdHMgb3duOyBQUk9URUNUIFRIRSAuLi4gY29t'
        'ZXMgZnJvbSB0aGUgZmllbGQuCiAgY29uc3QgciA9IHt9OwogIGNvbnN0IHQgPSBGUy51bnRpbCgo'
        'KT0+eyBkcmF3KCk7IHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC5oZWFkPT09J05FVyBPQkpF'
        'Q1RJVkUnOyB9LCAxNTAwLCBmYWxzZSk7CiAgci5jYXJkRm9yVGhlTmV3T2JqZWN0aXZlID0gdD49'
        'MCAmJiAvXlBST1RFQ1QgVEhFIC8udGVzdChvYmpDYXJkLnR4dCk7CiAgLy8gSXRzIGNsb2NrIHN0'
        'YXJ0cyBvbmNlIHRoZSBqdW1wIGluIGlzIG92ZXIsIHNvIHdhaXQgZm9yIGl0IHJhdGhlciB0aGFu'
        'CiAgLy8gY291bnQgc3RlcHMuCiAgci5jYXJkR29lc0FnYWluID0gRlMudW50aWwoKCk9PnsgZHJh'
        'dygpOyByZXR1cm4gb2JqQ2FyZD09PW51bGw7IH0sIE9CSl9DQVJEX1RJTUUqMywgZmFsc2UpID49'
        'IDA7CiAgci5saW5lS2VlcHNJdCA9IC9eUFJPVEVDVCBUSEUgLy50ZXN0KG9ialBpbm5lZCk7CiAg'
        'cmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTmV3IGxvb2s6IG5vIENvdXJpZXIgbGVmdCBpbiB0aGVz'
        'ZScsICdtPTM2JywgYAogIEZTLnN0ZXAoNzAwKTsKICBzaG93RnBzID0gdHJ1ZTsgc2hvd09iaiA9'
        'IHRydWU7CiAgY29uc3QgdXNlZCA9IFtdOyBjb25zdCBvZiA9IGN0eC5maWxsVGV4dDsKICBsZXQg'
        'aW5zaWRlID0gMDsKICBjb25zdCB3cmFwID0gbmFtZT0+eyBjb25zdCBmID0gd2luZG93W25hbWVd'
        'OyB3aW5kb3dbbmFtZV0gPSBmdW5jdGlvbigpeyBpbnNpZGUrKzsgdHJ5eyByZXR1cm4gZi5hcHBs'
        'eSh0aGlzLCBhcmd1bWVudHMpOyB9IGZpbmFsbHl7IGluc2lkZS0tOyB9IH07IH07CiAgWydkcmF3'
        'RmllbGRCYW5uZXInLCdkcmF3RmxlZVdhcm5pbmcnLCdkcmF3RnBzJywnZHJhd09iakNvdW50Jywn'
        'ZHJhd1BhdXNlZCcsCiAgICdkcmF3U3ViTXNncycsJ2RyYXdUaWNrZXRNc2dzJywnZHJhd0l0ZW1z'
        'JywnZHJhd0h1bGxCbG9ja3MnLCdkcmF3U3Vic3lzdGVtcyddLmZvckVhY2god3JhcCk7CiAgLy8g'
        'U29tZXRoaW5nIGluIGVhY2ggb2YgdGhlbSB0byBkcmF3LgogIGNvbnN0IGNhcCA9IGVuZW1pZXMu'
        'ZmluZChlPT5lLnR5cGU9PT0nY3J1aXNlcid8fGUudHlwZT09PSdjb3J2ZXR0ZScpIHx8IGVuZW1p'
        'ZXNbMF07CiAgU1VCX01TR1MucHVzaCh7eDozMDAsIHk6MjUwLCB0eHQ6J0RPQ0tFRCcsIGxpZmU6'
        'MTUwLCBtbDoxNTAsIGFsbHk6dHJ1ZSwgdG9uZTonZ29vZCd9KTsKICBUSUNLRVRfTVNHUy5wdXNo'
        'KHt4OjMyMCwgeToyNjAsIGtpbmQ6J2NydWlzZXInLCBsaWZlOjE1MCwgbWw6MTUwLCByZXA6ZmFs'
        'c2V9KTsKICBJVEVNUy5wdXNoKHt4OjM0MCwgeToyNzAsIHZ4OjAsIHZ5OjAsIGtpbmQ6J2xpZmUn'
        'LCBsaWZlOjUwMH0pOwogIElURU1TLnB1c2goe3g6MzYwLCB5OjI3MCwgdng6MCwgdnk6MCwga2lu'
        'ZDonY29ydmV0dGUnLCBsaWZlOjUwMH0pOwogIG5vdGljZSgnVEVTVCBOT1RJQ0UnLCAnaW5mbycp'
        'OwogIGN0eC5maWxsVGV4dCA9IGZ1bmN0aW9uKCl7IGlmKGluc2lkZSkgdXNlZC5wdXNoKGN0eC5m'
        'b250KTsgcmV0dXJuIG9mLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07CiAgb2JqQW5ub3VuY2Uo'
        'J05FVyBPQkpFQ1RJVkUnLCAnVEVTVCcsICduZXcnKTsgb2JqQ2FyZC50MCA9IGZjIC0gNDA7CiAg'
        'ZHJhdygpOwogIHVzZXJQYXVzZWQgPSB0cnVlOyBzeW5jUGF1c2UoKTsgZHJhdygpOwogIGN0eC5m'
        'aWxsVGV4dCA9IG9mOwogIHJldHVybiB7c29tZXRoaW5nRHJhd246IHVzZWQubGVuZ3RoPj00LCBm'
        'bGVlU2hvd246IGZsZWVpbmdFbmVtaWVzKCkubGVuZ3RoPjAsIG5vQ291cmllcjogdXNlZC5ldmVy'
        'eShmPT4hL0NvdXJpZXIvLnRlc3QoZikpfTtgKTsKCnNjZW5hcmlvKCdOb3RpY2VzOiBhIGNvbHVt'
        'biwgbm90IHRoZSBmaWVsZCcsICdtPTMxJywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDMw'
        'MCk7CiAgc2NvcmUgPSBjeWNsZUJhc2UgKyA0MDAwOyB0aWNrU2hpcFVubG9ja3MoKTsKICByLnVu'
        'bG9ja0lzQU5vdGljZSA9IE5PVElDRVMubGVuZ3RoPjAgJiYgTk9USUNFU1swXS50eHQ9PT0nR1RG'
        'IEhFUkNVTEVTIEFWQUlMQUJMRScgJiYgTk9USUNFU1swXS50b25lPT09J3VubG9jayc7CiAgci5u'
        'b3RJblRoZUZpZWxkID0gIVNVQl9NU0dTLnNvbWUobT0+L0FWQUlMQUJMRS8udGVzdChtLnR4dCkp'
        'OwogIGNvbnN0IHBsYXRlcyA9IFtdOyBjb25zdCBvcCA9IHRoUGxhdGU7CiAgdGhQbGF0ZSA9IGZ1'
        'bmN0aW9uKHgseSx3LGgpeyBwbGF0ZXMucHVzaCh7eCx5LHcsaH0pOyByZXR1cm4gb3AuYXBwbHko'
        'dGhpcywgYXJndW1lbnRzKTsgfTsKICBkcmF3KCk7IHRoUGxhdGUgPSBvcDsKICByLm9uVGhlTGVm'
        'dFVuZGVyVGhlQmFyID0gcGxhdGVzLnNvbWUocD0+cC54PT09OCAmJiBwLnk+PUhVRF9IKzYgJiYg'
        'cC5oPT09MTgpOwogIGZvcihsZXQgaT0wO2k8NTtpKyspIG5vdGljZSgnTicraSwgJ2luZm8nKTsK'
        'ICByLmF0TW9zdFRocmVlTmV3ZXN0Rmlyc3QgPSBOT1RJQ0VTLmxlbmd0aD09PTMgJiYgTk9USUNF'
        'U1swXS50eHQ9PT0nTjQnICYmIE5PVElDRVNbMl0udHh0PT09J04yJzsKICBGUy5zdGVwKE5PVElD'
        'RV9USU1FKzMwKTsgZHJhdygpOwogIHIudGhleUdvQWdhaW4gPSBOT1RJQ0VTLmxlbmd0aD09PTA7'
        'CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTm90aWNlczogcmFkaW8gbGluZXMgb2YgYSBtaXNz'
        'aW9uJywgJ209MzQnLCBgCiAgRlMuc3RlcCg0MDApOwogIEZTLnVudGlsKCgpPT5OT1RJQ0VTLnNv'
        'bWUobj0+L09SSU9OIElOQk9VTkQvLnRlc3Qobi50eHQpKSwgNjAwMCwgdHJ1ZSk7CiAgcmV0dXJu'
        'IHtvcmlvbkluYm91bmQ6IE5PVElDRVMuc29tZShuPT5uLnR4dD09PSdHVEQgT1JJT04gSU5CT1VO'
        'RCAtIEhBTkdBUiBPUEVOJyAmJiBuLnRvbmU9PT0naW5mbycpLAogICAgICAgICAgbm90SW5UaGVG'
        'aWVsZDogIVNVQl9NU0dTLnNvbWUobT0+L0lOQk9VTkQvaS50ZXN0KG0udHh0KSl9O2ApOwoKc2Nl'
        'bmFyaW8oJ0h1bGwgYmFuZDogY2FsbSwgbGl0IGJ5IGEgaGl0LCBmdWxsIHdoZW4gbmVhcmx5IGRl'
        'YWQnLCAnbT00MicsIGAKICBGUy5zdGVwKDQwMCk7CiAgY29uc3QgdiA9IGVuZW1pZXMuZmluZChl'
        'PT5lLnVpZD09PSdWMScpOwogIGNvbnN0IHIgPSB7fTsKICB2Ll9oYkhpdCA9IGZjIC0gSEJfSE9U'
        'IC0gMTsgdi5faGJMYXN0ID0gdi5ocDsgZHJhdygpOwogIHIuY2FsbUlzSGFsZiA9IE1hdGguYWJz'
        'KHYuX2hiQWxwaGEgLSBIQl9DQUxNKSA8IDFlLTk7CiAgdi5faGJMYXN0ID0gdi5ocCArIDEwOyBk'
        'cmF3KCk7CiAgci5hSGl0TGlnaHRzSXRVcCA9IE1hdGguYWJzKHYuX2hiQWxwaGEgLSAxKSA8IDFl'
        'LTk7CiAgdi5faGJIaXQgPSBmYyAtIEhCX0hPVC8yOyB2Ll9oYkxhc3QgPSB2LmhwOyBkcmF3KCk7'
        'CiAgci5hbmRJdFNldHRsZXMgPSB2Ll9oYkFscGhhID4gSEJfQ0FMTSAmJiB2Ll9oYkFscGhhIDwg'
        'MTsKICB2Ll9oYkhpdCA9IGZjIC0gSEJfSE9UIC0gMTsgdi5ocCA9IHYubWF4SHAqMC4xOyB2Ll9o'
        'Ykxhc3QgPSB2LmhwOyBkcmF3KCk7CiAgci5uZWFybHlEZWFkU3RheXNGdWxsID0gTWF0aC5hYnMo'
        'di5faGJBbHBoYSAtIDEpIDwgMWUtOTsKICByLmNvbG91clJ1bnNTbW9vdGhseSA9IGh1bGxCYW5k'
        'Q29sKDEpPT09J3JnYig2MCwyMjQsMTA2KScgJiYgaHVsbEJhbmRDb2woMC41KT09PSdyZ2IoMjU1'
        'LDIwNCw2OCknCiAgICAgICAgICAgICAgICAgICAgICAmJiBodWxsQmFuZENvbCgwKT09PSdyZ2Io'
        'MjU1LDc0LDUxKScgJiYgaHVsbEJhbmRDb2woMC43NSkhPT1odWxsQmFuZENvbCgwLjgpOwogIHJl'
        'dHVybiByO2ApOwoKc2NlbmFyaW8oJ1BpY2t1cHMgbGlnaHQgdXAgdGhlIGJhciwgbm90IHRoZSBm'
        'aWVsZCcsICdtPTMxJywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDMwMCk7CiAgY29uc3Qg'
        'dGFrZSA9IChraW5kKT0+eyBJVEVNUy5wdXNoKHt4OnBsYXllci54KzUsIHk6cGxheWVyLnksIHZ4'
        'OjAsIHZ5OjAsIGtpbmQ6a2luZCwgbGlmZTo1MDB9KTsgRlMuc3RlcCgzKTsgfTsKICBUSUNLRVRf'
        'TVNHUy5sZW5ndGggPSAwOyBCQVJfUFVMU0UgPSB7fTsKICB0YWtlKCdjcnVpc2VyJyk7CiAgci50'
        'aWNrZXRMaWdodHNJdHNTeW1ib2wgPSAhIUJBUl9QVUxTRVsndGlja2V0OmNydWlzZXInXSAmJiAh'
        'QkFSX1BVTFNFWyd0aWNrZXQ6Y3J1aXNlciddLndlYWs7CiAgci5ub1dvcmRzSW5UaGVGaWVsZCA9'
        'IFRJQ0tFVF9NU0dTLmxlbmd0aD09PTA7CiAgLy8gVGhlIGhhcm5lc3MgcHV0cyB0aGUgaHVsbCBi'
        'YWNrIHRvIGZ1bGwgZXZlcnkgc3RlcCwgc28gdGhlc2UgdHdvIHRha2UKICAvLyB0aGUgcGlja3Vw'
        'IHN0cmFpZ2h0IHRocm91Z2ggdXBkYXRlSXRlbXMoKS4KICBjb25zdCB0YWtlTm93ID0gKGtpbmQp'
        'PT57IElURU1TLnB1c2goe3g6cGxheWVyLngrNSwgeTpwbGF5ZXIueSwgdng6MCwgdnk6MCwga2lu'
        'ZDpraW5kLCBsaWZlOjUwMH0pOyB1cGRhdGVJdGVtcygpOyB9OwogIHBsYXllci5ocCA9IHBsYXll'
        'ci5tYXhIcCowLjU7IHRha2VOb3coJ3JlcGFpcicpOwogIHIucmVwYWlyTGlnaHRzVGhlSHVsbCA9'
        'ICEhQkFSX1BVTFNFLmh1bGwgJiYgIUJBUl9QVUxTRS5odWxsLndlYWs7CiAgLy8gVGhlIGhhcm5l'
        'c3Mga2VlcHMgdGhlIGh1bGwgYXQgZnVsbCwgc28gdGhpcyBvbmUgY2hhbmdlcyBub3RoaW5nLgog'
        'IGRlbGV0ZSBCQVJfUFVMU0UuaHVsbDsgdGFrZSgncmVwYWlyJyk7CiAgci5yZXBhaXJBdEZ1bGxJ'
        'c0RpbW1lZCA9ICEhQkFSX1BVTFNFLmh1bGwgJiYgQkFSX1BVTFNFLmh1bGwud2VhazsKICBsaXZl'
        'cyA9IExJVkVTX01BWCAtIDE7IHRha2UoJ2xpZmUnKTsKICByLmxpZmVMaWdodHNMaXZlcyA9ICEh'
        'QkFSX1BVTFNFLmxpdmVzICYmICFCQVJfUFVMU0UubGl2ZXMud2VhazsKICBsaXZlcyA9IExJVkVT'
        'X01BWDsgZGVsZXRlIEJBUl9QVUxTRS5saXZlczsgdGFrZU5vdygnbGlmZScpOwogIHIubGlmZUF0'
        'TWF4SXNEaW1tZWQgPSAhIUJBUl9QVUxTRS5saXZlcyAmJiBCQVJfUFVMU0UubGl2ZXMud2VhazsK'
        'ICAvLyBEcmF3bjogdGhlIGdsb3cgcmluZyBnb2VzIHJvdW5kIHRoZSBodWxsIGJhciBhbmQgdGhl'
        'IHRpY2tldCBjZWxsLgogIGNvbnN0IHJpbmdzID0gW107IGNvbnN0IG9nID0gdGhHbG93UGF0aDsK'
        'ICB0aEdsb3dQYXRoID0gZnVuY3Rpb24oeCx5LHcsaCl7IHJpbmdzLnB1c2goe3gseSx3LGh9KTsg'
        'cmV0dXJuIG9nLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07CiAgYmFyUHVsc2UoJ2h1bGwnKTsg'
        'YmFyUHVsc2UoJ3RpY2tldDpjcnVpc2VyJyk7IEZTLnN0ZXAoNDApOyBkcmF3KCk7IHRoR2xvd1Bh'
        'dGggPSBvZzsKICByLnJpbmdBcm91bmRIdWxsID0gcmluZ3Muc29tZShnPT5nLng9PT0xODEgJiYg'
        'Zy53PT09MTE2KTsKICByLnJpbmdBcm91bmRUaWNrZXQgPSByaW5ncy5zb21lKGc9PmcueD09PTUz'
        'MyAmJiBnLnc9PT01OCk7CiAgLy8gSXRzIHRpbWUgaXMgdXA6IHRoZSBwdWxzZSBpcyBvdmVyIGFu'
        'ZCBnb25lLiAoU3RlcHBpbmcgdGhlIGdhbWUgdG8gZ2V0CiAgLy8gdGhlcmUgd291bGQgbGV0IGxv'
        'b3QgZnJvbSB0aGUgZmlnaHQgbGlnaHQgaXQgdXAgYWdhaW4uKQogIGJhclB1bHNlKCdodWxsJyk7'
        'IEJBUl9QVUxTRS5odWxsLnQwID0gZmMgLSBCQVJfUFVMU0VfVDsKICByLmFuZEl0RW5kcyA9IGJh'
        'clB1bHNlTGV2ZWwoJ2h1bGwnKT09PTAgJiYgIUJBUl9QVUxTRS5odWxsOwogIHIuc29mdE5vdEhh'
        'cmQgPSAoKCk9PnsgYmFyUHVsc2UoJ2h1bGwnKTsgY29uc3QgYSA9IGJhclB1bHNlTGV2ZWwoJ2h1'
        'bGwnKTsgRlMuc3RlcCgxMCk7IGNvbnN0IGIgPSBiYXJQdWxzZUxldmVsKCdodWxsJyk7IHJldHVy'
        'biBhPT09MCAmJiBiPjAgJiYgYjwxOyB9KSgpOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ01p'
        'c3Npb24gcmV3YXJkIHRpY2tldDogaW4gdGhlIGJhcicsICdtPTM1JywgYAogIEZTLnN0ZXAoMzAw'
        'KTsKICBjb25zdCBkID0gYWxsaWVzLmZpbmQoYT0+YS51aWQ9PT0nQTEnKTsKICBkLmhwID0gZC5t'
        'YXhIcCA9IDFlNzsgZm9yKGNvbnN0IHMgb2YgZC5zdWJzfHxbXSkgcy5ocCA9IHMubWF4SHAgPSAx'
        'ZTc7CiAgVElDS0VUX01TR1MubGVuZ3RoID0gMDsKICAvLyBSb2NrcyBhbmQgd3JlY2thZ2UgdGFr'
        'ZSBhIHNoYXJlIG9mIHRoZSBodWxsIHJhdGhlciB0aGFuIHBvaW50cywgc28gYQogIC8vIGJpZyBo'
        'dWxsIGFsb25lIGRvZXMgbm90IGtlZXAgaGVyIGFsaXZlOiBzaGUgaXMgdG9wcGVkIHVwIGFzIHNo'
        'ZSBnb2VzLgogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+eyBpZihhbGxpZXMuaW5jbHVkZXMoZCkp'
        'IGQuaHAgPSBkLm1heEhwOyByZXR1cm4gd2F2ZU92ZXI7IH0sIDEyMDAwLCB0cnVlKTsKICBjb25z'
        'dCBrID0gT2JqZWN0LmtleXMoQkFSX1BVTFNFKS5maW5kKHg9Pi9edGlja2V0Oi8udGVzdCh4KSk7'
        'CiAgY29uc3QgciA9IHtyZXdhcmRlZDogdD49MCAmJiAhIWssIG5vdEluVGhlRmllbGQ6IFRJQ0tF'
        'VF9NU0dTLmxlbmd0aD09PTB9OwogIGlmKCFyLnJld2FyZGVkKSByLmRiZyA9IHt0LCBnbDpndWFy'
        'ZExvc3QsIGd3Omd1YXJkV2FudGVkLCBnczpndWFyZFNwYXduZWQsIGtleXM6T2JqZWN0LmtleXMo'
        'QkFSX1BVTFNFKSwgd2F2ZSwgZmN9OwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ0EgY29ydmV0'
        'dGUgYXJyaXZlczogUkVBUk0gY2FsbHMnLCAnbT0zNScsIGAKICBCQVJfUFVMU0UgPSB7fTsKICAv'
        'LyBUaGUgYnV0dG9uIGJlY29tZXMgdXNhYmxlIG9uY2Ugc2hlIGlzIHRoZXJlIGFuZCB0aGUganVt'
        'cCBpbiBpcyBvdmVyLgogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+ISFCQVJfUFVMU0UucmVhcm0s'
        'IDMwMDAsIHRydWUpOwogIGNvbnN0IGNhbGxlZCA9IHJlYXJtUmVhZHkoKTsKICBjb25zdCB0MCA9'
        'IEJBUl9QVUxTRS5yZWFybSA/IEJBUl9QVUxTRS5yZWFybS50MCA6IC0xOwogIEZTLnN0ZXAoMTAw'
        'KTsKICByZXR1cm4ge3JlYXJtQ2FsbHM6IHQ+PTAgJiYgY2FsbGVkLCBvbmx5T25jZU5vdEV2ZXJ5'
        'U3RlcDogIUJBUl9QVUxTRS5yZWFybSB8fCBCQVJfUFVMU0UucmVhcm0udDA9PT10MH07YCk7Cgpz'
        'Y2VuYXJpbygnQSBkZXN0cm95ZXIgYXJyaXZlczogU0hJUCBTV0lUQ0ggY2FsbHMnLCAnbT0zNCZz'
        'aGlwcz04JywgYAogIEJBUl9QVUxTRSA9IHt9OwogIEZTLnN0ZXAoMzAwKTsKICBjb25zdCBiZWZv'
        'cmUgPSAhIUJBUl9QVUxTRS5zd2FwOwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+c2hpcFN3YXBS'
        'ZWFkeSgpLCA2MDAwLCB0cnVlKTsKICBGUy5zdGVwKDIpOwogIHJldHVybiB7bm90QmVmb3JlVGhl'
        'T3Jpb246ICFiZWZvcmUsIHN3YXBDYWxsczogdD49MCAmJiAhIUJBUl9QVUxTRS5zd2FwfTtgKTsK'
        'CnNjZW5hcmlvKCdNNDkgRGFzIFJlcGFyYXR1cmRvY2snLCAnbT00OScsIGAKICBjb25zdCByID0g'
        'e307CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IGQgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0n'
        'RDEnKTsKICByLmFyY2FkaWFCZWhpbmQgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nUzEnICYm'
        'IGUuaW1nPT09J2luYXJjYWRpYScgJiYgZS5pbnZ1bG4pOwogIHIuZGVpbW9zSHVydCA9ICEhZCAm'
        'JiBNYXRoLmFicyhkLmhwL2QubWF4SHAgLSAwLjI1KSA8IDAuMDI7CiAgci5zYXlzV2hhdCA9IG1p'
        'c3Npb25PYmo9PT0nREVTVFJPWSBUSEUgREVJTU9TIEJFRk9SRSBIRVIgUkVQQUlSUyBBUkUgRE9O'
        'RSc7CiAgbGV0IHQxID0gbnVsbDsKICBGUy51bnRpbCgoKT0+eyB0MSA9IGVuZW1pZXMuZmluZChl'
        'PT5lLnVpZD09PSdUMScpOyByZXR1cm4gISF0MTsgfSwgMjAwMCwgdHJ1ZSk7CiAgci50cmFuc3Bv'
        'cnRDb21lcyA9ICEhdDEgJiYgdDEuaW1nPT09J3RyYXJnbyc7CiAgLy8gSHVsbCBqdXN0IGJlZm9y'
        'ZSB0aGUgZG9jaywgc3RlcHBlZCBzaW5nbHkgc28gbm90aGluZyBlbHNlIGdldHMgaW4uCiAgbGV0'
        'IGgwID0gZC5ocCwgZ290ID0gLTE7CiAgZm9yKGxldCBpPTA7aTw2MDAwO2krKyl7IGlmKEVWX0RP'
        'Q0tbJ1QxJ10peyBnb3QgPSBpOyBicmVhazsgfSBoMCA9IGQuaHA7IGlmKGklMjAwPT09MCkgRlMu'
        'a2lsbFNtYWxsKCk7IEZTLnN0ZXAoMSk7IH0KICByLmRvY2tSZXBhaXJzQVF1YXJ0ZXIgPSBnb3Q+'
        'PTAgJiYgTWF0aC5hYnMoKGQuaHAtaDApL2QubWF4SHAgLSAwLjI1KSA8IDAuMDM7CiAgci50cmFu'
        'c3BvcnRKdW1wc091dCA9IHQxLndhcnBPdXQ+MCB8fCAhZW5lbWllcy5pbmNsdWRlcyh0MSk7CiAg'
        'Ly8gQWxsIHRocmVlIHRocm91Z2g6IHNoZSBpcyB3aG9sZSBhbmQganVtcHMuIFRoYXQgaXMgYSBm'
        'YWlsdXJlLgogIGZvcihjb25zdCBlIG9mIGVuZW1pZXMpIGlmKGUudHlwZT09PSdmaWdodGVyJ3x8'
        'ZS50eXBlPT09J2JvbWJlcicpIGUuaHAgPSAwOwogIGNvbnN0IGYgPSBGUy51bnRpbCgoKT0+ISFv'
        'YmpDYXJkICYmIG9iakNhcmQudG9uZT09PSdmYWlsJywgOTAwMCwgdHJ1ZSk7CiAgci5yZXBhaXJl'
        'ZFNoZUp1bXBzID0gZj49MCAmJiBvYmpDYXJkLnR4dD09PSdUSEUgREVJTU9TIFdBUyBSRVBBSVJF'
        'RCcgJiYgISFFVl9ET0NLWydUMyddOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000OSBkZXN0'
        'cm95ZWQgaW4gdGltZScsICdtPTQ5JywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDcwMCk7'
        'CiAgY29uc3QgZCA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdEMScpOwogIGQuaHAgPSAwOwog'
        'IGNvbnN0IGMgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J0RFSU1P'
        'UyBERVNUUk9ZRUQnLCAxNTAwLCBmYWxzZSk7CiAgci5jb21wbGV0ZUNhcmQgPSBjPj0wOwogIHIu'
        'bm9Nb3JlVHJhbnNwb3J0cyA9ICFzcGF3blEuc29tZShxPT4vXlQvLnRlc3QocS51aWR8fCcnKSk7'
        'CiAgLy8gT25lIGFscmVhZHkgb24gaXRzIHdheSBoYXMgbm90aGluZyBsZWZ0IHRvIGRvY2sgd2l0'
        'aCBhbmQgbGVhdmVzLgogIGNvbnN0IHQgPSBlbmVtaWVzLmZpbmQoZT0+L15ULy50ZXN0KGUudWlk'
        'fHwnJykpOwogIGlmKHQpeyBGUy5zdGVwKDMwMCk7IHIuc3RyYXlMZWF2ZXMgPSAhZW5lbWllcy5p'
        'bmNsdWRlcyh0KSB8fCB0LndhcnBPdXQ+MDsgfSBlbHNlIHIuc3RyYXlMZWF2ZXMgPSB0cnVlOwog'
        'IHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001MCBEZXIgRHVyY2hicnVjaCcsICdtPTUwJywgYAog'
        'IGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDUwMCk7CiAgY29uc3QgayA9IGVuZW1pZXMuZmlsdGVy'
        'KGU9PmUudWlkPT09J0sxJyk7CiAgci50d29BZW9sdXMgPSBrLmxlbmd0aD09PTIgJiYgay5ldmVy'
        'eShlPT5lLmltZz09PSdudGZjcmFlb2x1cycpOwogIHIuc2VudHJ5TGluZSA9IGVuZW1pZXMuZmls'
        'dGVyKGU9PmUudWlkPT09J0cxJyAmJiBlLnR5cGU9PT0nc2VudHJ5JykubGVuZ3RoPT09NDsKICBy'
        'Lm5vT3Jpb25ZZXQgPSAhYWxsaWVzLnNvbWUoYT0+YS51aWQ9PT0nQTEnKTsKICByLnNheXNCcmVh'
        'ayA9IG1pc3Npb25PYmo9PT0nQlJFQUsgVEhFIEJMT0NLQURFIC0gREVTVFJPWSBBTiBBRU9MVVMn'
        'OwogIGtbMF0uaHAgPSAwOwogIGxldCBvID0gbnVsbDsKICBGUy51bnRpbCgoKT0+eyBvID0gYWxs'
        'aWVzLmZpbmQoYT0+YS51aWQ9PT0nQTEnKTsgcmV0dXJuICEhbzsgfSwgMjAwMCwgdHJ1ZSk7CiAg'
        'ci5vcmlvblRocm91Z2hUaGVHYXAgPSAhIW8gJiYgby50cmFuc2l0PT09dHJ1ZTsKICBGUy5zdGVw'
        'KDIpOwogIHIubmV3T2JqZWN0aXZlID0gbWlzc2lvbk9iaj09PSdHRVQgVEhFIE9SSU9OIFRIUk9V'
        'R0gnOwogIG8uaHAgPSBvLm1heEhwID0gMWU3OyBmb3IoY29uc3QgcyBvZiBvLnN1YnN8fFtdKSBz'
        'LmhwID0gcy5tYXhIcCA9IDFlNzsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9PnsgaWYoYWxsaWVz'
        'LmluY2x1ZGVzKG8pKSBvLmhwID0gby5tYXhIcDsgcmV0dXJuICEhb2JqQ2FyZCAmJiBvYmpDYXJk'
        'LnR4dD09PSdUSEUgT1JJT04gSVMgVEhST1VHSCc7IH0sIDkwMDAsIHRydWUpOwogIHIudGhyb3Vn'
        'aENhcmQgPSB0Pj0wOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001MSBEaWUgUnVlY2tlcm9i'
        'ZXJ1bmcnLCAnbT01MScsIGAKICBjb25zdCByID0ge307CiAgc2NvcmUgPSAxMDAwOwogIEZTLnN0'
        'ZXAoMzAwKTsKICBjb25zdCBzID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1MxJyk7CiAgci5h'
        'cm1lZEFyY2FkaWEgPSAhIXMgJiYgcy50eXBlPT09J3N0YXRpb24nICYmIHMuYXJtZWQgJiYgISFz'
        'LnN1YnMgJiYgcy5zdWJzLnNvbWUoeD0+eC5pZD09PSd3ZWFwb25zJyk7CiAgLy8gSGVyIGd1bnMg'
        'ZmlyZS4KICBGUy5raWxsU21hbGwoKTsgZUJ1bGxldHMubGVuZ3RoID0gMDsKICBsZXQgc2hvdHMg'
        'PSAwOwogIGZvcihsZXQgaT0wO2k8NDAwO2krKyl7IEZTLmtpbGxTbWFsbCgpOyBjb25zdCBuMCA9'
        'IGVCdWxsZXRzLmxlbmd0aDsgRlMuc3RlcCgxKTsgc2hvdHMgKz0gTWF0aC5tYXgoMCwgZUJ1bGxl'
        'dHMubGVuZ3RoLW4wKTsgfQogIHIuZ3Vuc0ZpcmUgPSBzaG90cyA+IDA7CiAgZGFtYWdlRW5lbXko'
        'cywgcy5tYXhIcCo1LCBzLngsIHMueSwgdHJ1ZSwgJ2JvbHQnKTsgRlMuc3RlcCgzKTsKICByLmNh'
        'bm5vdEJlRGVzdHJveWVkID0gZW5lbWllcy5pbmNsdWRlcyhzKSAmJiBzLnJvbGxUPT1udWxsICYm'
        'IHMuaHA+MDsKICByLm5vRWx5c2l1bVlldCA9ICFhbGxpZXMuc29tZShhPT5hLnVpZD09PSdUMScp'
        'OwogIGZvcihjb25zdCB4IG9mIHMuc3VicykgaWYoeC5pZD09PSd3ZWFwb25zJyl7IHguZGVhZCA9'
        'IHRydWU7IHguaHAgPSAwOyB9CiAgRlMuc3RlcCgzKTsKICByLmNvdmVyVGhlRWx5c2l1bSA9IG1p'
        'c3Npb25PYmo9PT0nQ09WRVIgVEhFIEVMWVNJVU0nOwogIC8vIEd1bnMgb3V0OiBzaGUgZmFsbHMg'
        'c2lsZW50LgogIHNob3RzID0gMDsKICBmb3IobGV0IGk9MDtpPDMwMDtpKyspeyBGUy5raWxsU21h'
        'bGwoKTsgY29uc3QgbjAgPSBlQnVsbGV0cy5sZW5ndGg7IEZTLnN0ZXAoMSk7IHNob3RzICs9IE1h'
        'dGgubWF4KDAsIGVCdWxsZXRzLmxlbmd0aC1uMCk7IH0KICByLnNpbGVudFdpdGhvdXRHdW5zID0g'
        'c2hvdHM9PT0wOwogIGxldCBlbCA9IG51bGw7CiAgRlMudW50aWwoKCk9PnsgZWwgPSBhbGxpZXMu'
        'ZmluZChhPT5hLnVpZD09PSdUMScpOyByZXR1cm4gISFlbDsgfSwgMzAwMCwgdHJ1ZSk7CiAgZWwu'
        'aHAgPSBlbC5tYXhIcCA9IDFlNzsKICBjb25zdCBob2xkID0gRlMudW50aWwoKCk9PnsgZWwuaHAg'
        'PSBlbC5tYXhIcDsgcmV0dXJuIGVsLmhvbGRUIT1udWxsOyB9LCA5MDAwLCB0cnVlKTsKICBGUy5z'
        'dGVwKDQwMCk7CiAgci5ib2FyZGluZ1Rha2VzVGltZSA9IGhvbGQ+PTAgJiYgIXMuY2FwdHVyZWQ7'
        'CiAgY29uc3QgZ290ID0gRlMudW50aWwoKCk9PnsgaWYoYWxsaWVzLmluY2x1ZGVzKGVsKSkgZWwu'
        'aHAgPSBlbC5tYXhIcDsgcmV0dXJuICEhRVZfRE9DS1snVDEnXTsgfSwgMzAwMCwgdHJ1ZSk7CiAg'
        'RlMuc3RlcCgzKTsKICByLnRha2VuQW5kU3RheXMgPSBnb3Q+PTAgJiYgcy5jYXB0dXJlZD09PXRy'
        'dWUgJiYgZW5lbWllcy5pbmNsdWRlcyhzKSAmJiAhKHMud2FycE91dD4wKSAmJiBzLnNjZW5lcnk9'
        'PT10cnVlOwogIHIuY29tcGxldGVDYXJkID0gISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J0FS'
        'Q0FESUEgUkVUQUtFTic7CiAgY29uc3QgdyA9IEZTLnVudGlsKCgpPT53YXZlT3ZlciwgNjAwMCwg'
        'dHJ1ZSk7CiAgci53YXZlRW5kcyA9IHc+PTA7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTUx'
        'IGJvdGggRWx5c2l1bXMgbG9zdDogZmFpbGVkJywgJ209NTEnLCBgCiAgY29uc3QgciA9IHt9Owog'
        'IEZTLnN0ZXAoMzAwKTsKICBjb25zdCBzID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1MxJyk7'
        'CiAgZm9yKGNvbnN0IHggb2Ygcy5zdWJzKSBpZih4LmlkPT09J3dlYXBvbnMnKXsgeC5kZWFkID0g'
        'dHJ1ZTsgeC5ocCA9IDA7IH0KICBsZXQgZWwgPSBudWxsOwogIEZTLnVudGlsKCgpPT57IGVsID0g'
        'YWxsaWVzLmZpbmQoYT0+YS51aWQ9PT0nVDEnKTsgcmV0dXJuICEhZWw7IH0sIDMwMDAsIHRydWUp'
        'OwogIGVsLmhwID0gMDsKICBsZXQgZTIgPSBudWxsOwogIEZTLnVudGlsKCgpPT57IGUyID0gYWxs'
        'aWVzLmZpbmQoYT0+YS51aWQ9PT0nVDInKTsgcmV0dXJuICEhZTI7IH0sIDMwMDAsIHRydWUpOwog'
        'IHIuc2Vjb25kQ29tZXMgPSAhIWUyOwogIGUyLmhwID0gMDsKICBjb25zdCBmID0gRlMudW50aWwo'
        'KCk9PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnRvbmU9PT0nZmFpbCcsIDE1MDAsIGZhbHNlKTsKICBy'
        'LmZhaWxDYXJkID0gZj49MCAmJiBvYmpDYXJkLnR4dD09PSdCT1RIIEVMWVNJVU1TIExPU1QnOwog'
        'IHIubnRmS2VlcHNIZXIgPSBlbmVtaWVzLmluY2x1ZGVzKHMpICYmIHMuc2NlbmVyeT09PXRydWUg'
        'JiYgIXMuY2FwdHVyZWQ7CiAgY29uc3QgdyA9IEZTLnVudGlsKCgpPT53YXZlT3ZlciwgNjAwMCwg'
        'dHJ1ZSwgdHJ1ZSk7CiAgci53YXZlRW5kcyA9IHc+PTA7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJp'
        'bygnTTUyIERhcyBBcnRpbGxlcmllZmV1ZXInLCAnbT01MicsIGAKICBjb25zdCByID0ge307CiAg'
        'dGlja2V0cy5jcnVpc2VyID0gMTsKICBGUy5zdGVwKDQwMCk7CiAgY29uc3QgbSA9IGFsbGllcy5m'
        'aW5kKGE9PmEudWlkPT09J00xJyk7CiAgci5tam9sbmlySW5QbGFjZSA9ICEhbSAmJiBtLmltZz09'
        'PSdzZ21qb2xuaXInICYmIE1hdGguYWJzKG0ueC0xMTApPDEgJiYgTWF0aC5hYnMobS55LTE3MCk8'
        'MSAmJiAhbS5zdWJzCiAgICAgICAgICAgICAgICAgICAgICYmICEhbS5iZWFtcyAmJiBtLmJlYW1z'
        'LnNvbWUoYj0+Yi5sYXJnZSk7CiAgci5kZWltb3NCZXNpZGUgPSBhbGxpZXMuc29tZShhPT5hLnVp'
        'ZD09PSdBMScgJiYgYS5pbWc9PT0nY29kZWltb3MnKTsKICByLnN1cHBvcnRTdGlsbENhbGxhYmxl'
        'ID0gYWxseVJlYWR5KCk7CiAgY29uc3QgdiA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdWMScp'
        'OwogIHIub25BRGVhZGxpbmUgPSAhIXYgJiYgdi5mbGVlVD4wOwogIC8vIFRoZSBNam9sbmlyJ3Mg'
        'YmVhbSBmaW5kcyBoZXI6IGh1bGwgZ29lcyBkb3duIHdpdGggbm9ib2R5IGVsc2UgZmlyaW5nLgog'
        'IGZvcihjb25zdCBhIG9mIGFsbGllcykgaWYoYSE9PW0pIGEubm9GaXJlID0gdHJ1ZTsKICBjb25z'
        'dCBoMCA9IHYuaHA7IGxldCBoaXQgPSBmYWxzZTsKICBmb3IobGV0IGk9MDtpPDMwMDAgJiYgIWhp'
        'dDtpKz0yMCl7IEZTLmtpbGxTbWFsbCgpOyBmb3IoY29uc3QgYSBvZiBhbGxpZXMpeyBpZihhLnVp'
        'ZD09PSdBMScpeyBhLmJlYW1zID0gbnVsbDsgYS5ndW5UID0gbnVsbDsgfSB9CiAgICBGUy5zdGVw'
        'KDIwKTsgaGl0ID0gdi5ocCA8IGgwIC0gdi5tYXhIcCowLjEwOyB9CiAgci5tam9sbmlySGl0cyA9'
        'IGhpdDsKICB2LmhwID0gMDsKICBsZXQgdjIgPSBudWxsOwogIEZTLnVudGlsKCgpPT57IHYyID0g'
        'ZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YyJyk7IHJldHVybiAhIXYyOyB9LCAyMDAwLCB0cnVl'
        'KTsKICByLm5leHRDb21lcyA9ICEhdjIgJiYgdjIuaW1nPT09J250ZmNvZGVpbW9zJyAmJiB2Mi5m'
        'bGVlVD4wOwogIHYyLmhwID0gMDsKICBsZXQgdjMgPSBudWxsOwogIEZTLnVudGlsKCgpPT57IHYz'
        'ID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YzJyk7IHJldHVybiAhIXYzOyB9LCAyMDAwLCB0'
        'cnVlKTsKICByLmhlY2F0ZUxhc3QgPSAhIXYzICYmIHYzLmltZz09PSdudGZkZWhlY2F0ZSc7CiAg'
        'RlMuc3RlcCgzMDApOwogIHYzLmhwID0gMDsKICByLmNvbXBsZXRlQ2FyZCA9IEZTLnVudGlsKCgp'
        'PT4hIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nSEVDQVRFIERFU1RST1lFRCcsIDMwMDAsIGZh'
        'bHNlKSA+PSAwOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001MyBEZXIgR2VnZW5hbmdyaWZm'
        'JywgJ209NTMnLCBgCiAgY29uc3QgciA9IHt9OwogIHRpY2tldHMuY3J1aXNlciA9IDE7CiAgRlMu'
        'c3RlcCgzMDApOwogIGNvbnN0IGExID0gYWxsaWVzLmZpbmQoYT0+YS51aWQ9PT0nQTEnKSwgYTIg'
        'PSBhbGxpZXMuZmluZChhPT5hLnVpZD09PSdBMicpOwogIHIuZmxlZXRQbGFjZWQgPSAhIWExICYm'
        'ICEhYTIgJiYgTWF0aC5hYnMoYTEueS0xNzApPDYwICYmIE1hdGguYWJzKGEyLnktMzkwKTw2MDsK'
        'ICByLnN1cHBvcnRTdGlsbENhbGxhYmxlID0gYWxseVJlYWR5KCk7CiAgci5ub0VuZW15RGVzdHJv'
        'eWVyc1lldCA9ICFlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nVjEnfHxlLnVpZD09PSdWMicpOwog'
        'IEZTLnVudGlsKCgpPT5lbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nVjEnKSAmJiBlbmVtaWVzLnNv'
        'bWUoZT0+ZS51aWQ9PT0nVjInKSwgMjAwMCwgdHJ1ZSk7CiAgci50aGV5SnVtcEluID0gZW5lbWll'
        'cy5zb21lKGU9PmUudWlkPT09J1YxJyAmJiBlLmltZz09PSdudGZkZWhlY2F0ZScpICYmIGVuZW1p'
        'ZXMuc29tZShlPT5lLnVpZD09PSdWMicgJiYgZS5pbWc9PT0nbnRmZGVvcmlvbicpOwogIEZTLnN0'
        'ZXAoMik7CiAgci5uZXdPYmplY3RpdmUgPSBtaXNzaW9uT2JqPT09J0RFU1RST1kgVEhFIEhFQ0FU'
        'RSBBTkQgVEhFIE9SSU9OJzsKICBjb25zdCB2MSA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdW'
        'MScpOyB2MS5ocCA9IDA7CiAgRlMuc3RlcCg0MDApOwogIHIubm90RG9uZVdpdGhPbmUgPSAhKG9i'
        'akNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nQ09VTlRFUkFUVEFDSyBCUk9LRU4nKTsKICBjb25zdCB2'
        'MiA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdWMicpOyBpZih2MikgdjIuaHAgPSAwOwogIHIu'
        'Y29tcGxldGVDYXJkID0gRlMudW50aWwoKCk9PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdD'
        'T1VOVEVSQVRUQUNLIEJST0tFTicsIDMwMDAsIGZhbHNlKSA+PSAwOwogIHJldHVybiByO2ApOwoK'
        'c2NlbmFyaW8oJ001NCBEaWUgRXZha3VpZXJ1bmcnLCAnbT01NCcsIGAKICBjb25zdCByID0ge307'
        'CiAgbGV0IHQxID0gbnVsbDsKICBGUy51bnRpbCgoKT0+eyB0MSA9IGFsbGllcy5maW5kKGE9PmEu'
        'dWlkPT09J1QxJyk7IHJldHVybiAhIXQxOyB9LCAxMDAwLCBmYWxzZSk7CiAgci5sZWF2ZXNUaGVT'
        'dGF0aW9uID0gISF0MSAmJiBNYXRoLmFicyh0MS54LTU2MCkgPCAxNSAmJiB0MS5jcm9zc2luZyA8'
        'IDAgJiYgdDEuZmxpcD09PW5lZWRzRmxpcCh0MS5pbWcsIHRydWUpOwogIGNvbnN0IHgwID0gdDEu'
        'eDsgRlMuc3RlcCgxMDApOwogIHIuZmxpZXNMZWZ0ID0gdDEueCA8IHgwIC0gMzA7CiAgLy8gS2Vl'
        'cCB0aGVtIGFsaXZlOyB0aGV5IGZseSBvdXQgdG8gdGhlIGxlZnQuCiAgY29uc3Qga2VlcCA9ICgp'
        'PT57IGZvcihjb25zdCBhIG9mIGFsbGllcykgaWYoL15ULy50ZXN0KGEudWlkfHwnJykpIGEuaHAg'
        'PSBhLm1heEhwID0gMWU3OyB9OwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+eyBrZWVwKCk7IHJl'
        'dHVybiBwcm90U2F2ZWQ+PTE7IH0sIDMwMDAsIHRydWUpOwogIHIuZmlyc3RPdXQgPSB0Pj0wOwog'
        'IGNvbnN0IGMgPSBGUy51bnRpbCgoKT0+eyBrZWVwKCk7IHJldHVybiAhIW9iakNhcmQgJiYgb2Jq'
        'Q2FyZC50eHQ9PT0nRVZBQ1VBVElPTiBDT01QTEVURSc7IH0sIDkwMDAsIHRydWUpOwogIHIudGhy'
        'ZWVPdXRDb21wbGV0ZSA9IGM+PTAgJiYgcHJvdFNhdmVkPj0zOwogIGNvbnN0IHcgPSBGUy51bnRp'
        'bCgoKT0+eyBrZWVwKCk7IHJldHVybiB3YXZlT3ZlcjsgfSwgOTAwMCwgdHJ1ZSwgdHJ1ZSk7CiAg'
        'ci53YXZlRW5kcyA9IHc+PTA7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTU0IHR3byBsb3N0'
        'OiBmYWlsZWQnLCAnbT01NCcsIGAKICBjb25zdCByID0ge307CiAgbGV0IG4gPSAwOwogIGNvbnN0'
        'IGYgPSBGUy51bnRpbCgoKT0+eyBmb3IoY29uc3QgYSBvZiBhbGxpZXMpIGlmKC9eVFsxMl0kLy50'
        'ZXN0KGEudWlkfHwnJykpIGEuaHAgPSAwOwogICAgcmV0dXJuICEhb2JqQ2FyZCAmJiBvYmpDYXJk'
        'LnRvbmU9PT0nZmFpbCc7IH0sIDMwMDAsIHRydWUpOwogIHIuZmFpbENhcmQgPSBmPj0wICYmIG9i'
        'akNhcmQudHh0PT09J1RPTyBNQU5ZIEVMWVNJVU1TIExPU1QnOwogIHJldHVybiByO2ApOwoKc2Nl'
        'bmFyaW8oJ2FsbGllZCBjcmFmdCBob2xkIGZpcmUgd2l0aCBub3RoaW5nIHRvIHNob290JywgJ209'
        'NDQnLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAoMzAwKTsKICBjb25zdCBmaSA9IG1rQWxs'
        'eVNtYWxsKCdmaWdodGVyJywgJ3RlcnJhbicsICdmaWhlcmMnLCBIKjAuNSk7CiAgY29uc3QgYm8g'
        'PSBta0FsbHlTbWFsbCgnYm9tYmVyJywgJ3RlcnJhbicsICdib2FydGVtaXMnLCBIKjAuNik7CiAg'
        'Zmkud2FycCA9IDA7IGJvLndhcnAgPSAwOyBhbGxpZXMucHVzaChmaSwgYm8pOwogIC8vIE9ubHkg'
        'dGhpbmdzIGFuIGVzY29ydCBoYXMgbm8gYnVzaW5lc3Mgc2hvb3RpbmcgYXQ6IG5vdGhpbmcsIGFu'
        'ZCBhbgogIC8vIGludnVsbmVyYWJsZSBzdGF0aW9uIGF0IHRoZSByaWdodCBlZGdlLgogIGNvbnN0'
        'IGtlZXAgPSBlbmVtaWVzOyBlbmVtaWVzID0gW107CiAgY29uc3Qgc3QgPSBta0VuZW15KCdjcl9u'
        'dGYnLCAnbnRmY3JhZW9sdXMnLCBIKjAuNSk7IHN0LnggPSBXLTQwOyBzdC53YXJwID0gMDsKICBz'
        'dC5pbnZ1bG4gPSB0cnVlOyBzdC5zY2VuZXJ5ID0gdHJ1ZTsKICBjb25zdCBzaG90cyA9ICgpPT5w'
        'QnVsbGV0cy5maWx0ZXIoYj0+Yi5hbGx5KS5sZW5ndGg7CiAgbGV0IG4gPSAwOwogIGZvcihjb25z'
        'dCBsaXN0IG9mIFtbXSwgW3N0XV0pewogICAgZW5lbWllcyA9IGxpc3Q7CiAgICBmb3IoY29uc3Qg'
        'YSBvZiBbZmksIGJvXSl7CiAgICAgIGEuaGVhZCA9IDA7IGEueCA9IFcqMC40OwogICAgICBmb3Io'
        'bGV0IGs9MDtrPDQwO2srKyl7CiAgICAgICAgY29uc3QgYjAgPSBzaG90cygpOwogICAgICAgIGEu'
        'ZlQgPSAwOyBzbWFsbEZpcmUoYSwgc21hbGxUYXJnZXQoYSkpOwogICAgICAgIGlmKGEuc2VjVCkg'
        'Zm9yKGxldCBpPTA7aTxhLnNlY1QubGVuZ3RoO2krKykgYS5zZWNUW2ldID0gMDsKICAgICAgICBm'
        'aXJlU2Vjb25kYXJpZXMoYSwgV1BOW2EudHlwZV0pOwogICAgICAgIG4gKz0gc2hvdHMoKS1iMDsK'
        'ICAgICAgfQogICAgfQogIH0KICBlbmVtaWVzID0ga2VlcDsKICByLm5vU2hvdHNBdE5vdGhpbmcg'
        'PSBuPT09MDsKICByLl9uID0gbjsKICAvLyBXaXRoIGEgcmVhbCBlbmVteSBpbiByZWFjaCB0aGV5'
        'IHN0aWxsIGZpcmUuCiAgY29uc3QgZm9lID0gZW5lbWllcy5maW5kKGU9PmUudHlwZT09PSdmaWdo'
        'dGVyJyAmJiAhKGUud2FycD4wKSkgfHwgZW5lbWllcy5maW5kKGU9PiEoZS53YXJwPjApICYmICFl'
        'LmludnVsbik7CiAgbGV0IG0gPSAwOwogIGlmKGZvZSl7IGZpLnggPSBmb2UueC04MDsgZmkueSA9'
        'IGZvZS55OyBmaS5oZWFkID0gMDsKICAgIGZvcihsZXQgaz0wO2s8NTtrKyspeyBjb25zdCBiMCA9'
        'IHNob3RzKCk7IGZpLmZUID0gMDsgc21hbGxGaXJlKGZpLCBmb2UpOyBtICs9IHNob3RzKCktYjA7'
        'IH0gfQogIHIuc3RpbGxGaXJlQXRFbmVtaWVzID0gbT4wOwogIHJldHVybiByO2ApOwoKc2NlbmFy'
        'aW8oJ000MyBEZXIgTlRGLUtvbnZvaScsICdtPTQzJywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5z'
        'dGVwKDYwMCk7CiAgY29uc3QgdCA9IGVuZW1pZXMuZmlsdGVyKGU9PmUudWlkPT09J1QxJyk7CiAg'
        'ci50aHJlZVRyaXRvbnMgPSB0Lmxlbmd0aD09PTMgJiYgdC5ldmVyeShlPT5lLmltZz09PSdmcnRy'
        'aXRvbicgJiYgZS5lc2NhcGluZz4wKTsKICByLnNheXNTY2FuRmlyc3QgPSBtaXNzaW9uT2JqPT09'
        'J1NDQU4gVEhFIFRSSVRPTlMnOwogIGRhbWFnZUVuZW15KHRbMF0sIHRbMF0ubWF4SHAqNSwgdFsw'
        'XS54LCB0WzBdLnksIHRydWUsICdib2x0Jyk7IEZTLnN0ZXAoMik7CiAgci5jYW5ub3REaWVVbnNj'
        'YW5uZWQgPSBlbmVtaWVzLmluY2x1ZGVzKHRbMF0pOwogIHIubm9BZW9sdXMgPSAhZW5lbWllcy5z'
        'b21lKGU9PmUudWlkPT09J0sxJykgJiYgIXNwYXduUS5zb21lKHE9PnEudWlkPT09J0sxJyk7CiAg'
        'Ly8gVW5kZXIgZmlyZSB0aGUgd2hvbGUgdGltZTogaW4gdGhpcyBtaXNzaW9uIHRoZSBzY2FuIHN0'
        'aWxsIGZpbGxzLgogIGZvcihjb25zdCBlIG9mIHQpIGZvcihsZXQgaT0wO2k8U0NBTl9USU1FKzIw'
        'O2krKyl7CiAgICBwbGF5ZXIueCA9IGUueDsgcGxheWVyLnkgPSBlLnk7IE1PVVNFLnggPSBlLng7'
        'IE1PVVNFLnkgPSBlLnk7CiAgICBwbGF5ZXIuc2hEZWxheSA9IDkwOyBwbGF5ZXIuaHAgPSBwbGF5'
        'ZXIubWF4SHA7IEZTLnN0ZXAoMSk7IH0KICByLmFsbFNjYW5uZWQgPSB0LmV2ZXJ5KGU9PmUuc2Nh'
        'bm5lZCk7CiAgRlMuc3RlcCgyKTsKICByLnRoZW5EZXN0cm95ID0gbWlzc2lvbk9iaj09PSdERVNU'
        'Uk9ZIFRIRSBDT05WT1knOwogIEZTLnN0ZXAoMjAwKTsKICByLmFlb2x1c0FmdGVyVGhlU2NhbiA9'
        'IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdLMScgJiYgZS5pbWc9PT0nbnRmY3JhZW9sdXMnKTsK'
        'ICBmb3IoY29uc3QgZSBvZiB0KSBlLmhwID0gMDsKICBjb25zdCBkb25lID0gRlMudW50aWwoKCk9'
        'PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdDT05WT1kgREVTVFJPWUVEJywgMTUwMCwgZmFs'
        'c2UpOwogIHIuY29tcGxldGVDYXJkID0gZG9uZT49MDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlv'
        'KCdNNDMgYSBUcml0b24gZ2V0cyBhd2F5OiBmYWlsZWQnLCAnbT00MycsIGAKICBGUy5zdGVwKDMw'
        'MCk7CiAgY29uc3QgdCA9IGVuZW1pZXMuZmlsdGVyKGU9PmUudWlkPT09J1QxJyk7CiAgZm9yKGNv'
        'bnN0IGUgb2YgdCl7IGUuc2Nhbm5lZCA9IHRydWU7IGUuZXNjYXBpbmcgPSAzOyB9CiAgY29uc3Qg'
        'ZiA9IEZTLnVudGlsKCgpPT4hIW9iakNhcmQgJiYgb2JqQ2FyZC50b25lPT09J2ZhaWwnLCAzMDAw'
        'LCBmYWxzZSk7CiAgcmV0dXJuIHtmYWlsQ2FyZDogZj49MCAmJiBvYmpDYXJkLnR4dD09PSdBIFRS'
        'SVRPTiBHT1QgQVdBWSd9O2ApOwoKc2NlbmFyaW8oJ000NCBEZXIgU2Nod2FybScsICdtPTQ0Jywg'
        'YAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDQwMCk7CiAgci5ub0FsbHlXaW5nQXRTdGFydCA9'
        'ICFhbGxpZXMuc29tZShhPT5hLnNtYWxsKTsKICByLmRlaW1vc1RvUmVhcm0gPSBhbGxpZXMuc29t'
        'ZShhPT5hLnVpZD09PSdBMScgJiYgYS5pbWc9PT0nY29kZWltb3MnKTsKICBjb25zdCBzZWVuID0g'
        'e307CiAgbGV0IG1heFdpbmcgPSAwLCBzdHJheSA9IDA7CiAgRlMudW50aWwoKCk9PnsgZm9yKGNv'
        'bnN0IGUgb2YgZW5lbWllcykgaWYoZS51aWQpIHNlZW5bZS51aWRdPTE7IGZvcihjb25zdCBhIG9m'
        'IGFsbGllcykgaWYoYS51aWQpIHNlZW5bYS51aWRdPTE7CiAgICBjb25zdCBzbSA9IGFsbGllcy5m'
        'aWx0ZXIoYT0+YS5zbWFsbCAmJiAhYS5kZWFkKTsgbWF4V2luZyA9IE1hdGgubWF4KG1heFdpbmcs'
        'IHNtLmxlbmd0aCk7CiAgICBpZihzbS5zb21lKGE9PmEudWlkIT09J1cyJykpIHN0cmF5Kys7IHJl'
        'dHVybiB3YXZlT3ZlcjsgfSwgMzAwMDAsIHRydWUpOwogIC8vIE9uZSBhbGxpZWQgd2luZywgdGhl'
        'IG9uZSB0aGUgbWlzc2lvbiBzZW5kczsgdGhlIERlaW1vcyBhZGRzIG5vbmUuCiAgci5vbmVBbGx5'
        'V2luZ09ubHkgPSBtYXhXaW5nPjAgJiYgbWF4V2luZzw9NCAmJiBzdHJheT09PTA7CiAgci5hbGxU'
        'aGVXaW5ncyA9IFsnRTEnLCdFMicsJ0UzJywnQjEnLCdXMiddLmV2ZXJ5KGs9PnNlZW5ba10pOwog'
        'IHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000NSBEYXMgTmFkZWxvZWhyJywgJ209NDUnLCBgCiAg'
        'Y29uc3QgciA9IHt9OwogIEZTLnN0ZXAoNTAwKTsKICBjb25zdCBrID0gZW5lbWllcy5maWx0ZXIo'
        'ZT0+L15LWzEyM10kLy50ZXN0KGUudWlkfHwnJykpOwogIHIudGhyZWVGZW5yaXMgPSBrLmxlbmd0'
        'aD09PTMgJiYgay5ldmVyeShlPT5lLmltZz09PSdudGZjcmZlbnJpcycpOwogIGNvbnN0IHlzID0g'
        'ay5tYXAoZT0+ZS55KS5zb3J0KChhLGIpPT5hLWIpOwogIHIuaW5TZXBhcmF0ZUxhbmVzID0geXMu'
        'bGVuZ3RoPT09MyAmJiB5c1sxXS15c1swXSA+IDQwICYmIHlzWzJdLXlzWzFdID4gNDA7CiAgY29u'
        'c3QgbyA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J0ExJyk7CiAgci5vcmlvbkNyb3NzZXMgPSAh'
        'IW8gJiYgby50cmFuc2l0PT09dHJ1ZTsKICBvLmhwID0gby5tYXhIcCA9IDFlNzsgZm9yKGNvbnN0'
        'IHMgb2Ygby5zdWJzfHxbXSkgcy5ocCA9IHMubWF4SHAgPSAxZTc7CiAgbGV0IHJvY2tzID0gMDsK'
        'ICBjb25zdCB0ID0gRlMudW50aWwoKCk9PnsgaWYoYWxsaWVzLmluY2x1ZGVzKG8pKSBvLmhwID0g'
        'by5tYXhIcDsKICAgIGlmKGVuZW1pZXMuc29tZShlPT5lLnR5cGU9PT0nYXN0ZXJvaWQnKSkgcm9j'
        'a3MrKzsKICAgIHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nVEhFIE9SSU9OIElT'
        'IFRIUk9VR0gnOyB9LCA5MDAwLCB0cnVlKTsKICByLnRocm91Z2hDYXJkID0gdD49MDsKICByLm5v'
        'QXN0ZXJvaWRzID0gcm9ja3M9PT0wOwogIEZTLnVudGlsKCgpPT53YXZlT3ZlciB8fCB3YXZlPjQ1'
        'LCAzMDAwLCB0cnVlKTsKICByLndhdmVFbmRzID0gd2F2ZU92ZXIgfHwgd2F2ZT40NTsKICByZXR1'
        'cm4gcjtgKTsKCnNjZW5hcmlvKCdNNDYgRGllIFdpc3NlbnNjaGFmdGxlcicsICdtPTQ2JywgYAog'
        'IGNvbnN0IHIgPSB7fTsKICBzY29yZSA9IDEwMDA7CiAgRlMuc3RlcCg0MDApOwogIGNvbnN0IGYg'
        'PSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nRjEnKTsKICByLmZhdXN0dXNQYXJrZWQgPSAhIWYg'
        'JiYgTWF0aC5hYnMoZi55LTI1MCkgPCAxOwogIHIub25BRGVhZGxpbmUgPSAhIWYgJiYgZi5mbGVl'
        'VD4wOwogIC8vIFRoZSBjb3VudGRvd24gc2l0cyBhdCB0aGUgcmlnaHQgZWRnZSwgY2xlYXIgb2Yg'
        'dGhlIG9iamVjdGl2ZSBsaW5lLgogIGNvbnN0IF9mdCA9IFtdLCBfcGwgPSBbXTsKICBjb25zdCBf'
        'ZnggPSBjdHguZmlsbFRleHQsIF90cCA9IHRoUGxhdGU7CiAgY3R4LmZpbGxUZXh0ID0gZnVuY3Rp'
        'b24odCwgeCwgeSl7IF9mdC5wdXNoKHt0OlN0cmluZyh0KSwgeCwgeX0pOyByZXR1cm4gX2Z4LmFw'
        'cGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07CiAgdGhQbGF0ZSA9IGZ1bmN0aW9uKHgsIHksIHcsIGgp'
        'eyBfcGwucHVzaCh7eCwgeSwgdywgaH0pOyByZXR1cm4gX3RwLmFwcGx5KHRoaXMsIGFyZ3VtZW50'
        'cyk7IH07CiAgdHJ5IHsgZHJhd09iakxpbmUoe3R4dDptaXNzaW9uT2JqLCBjb2w6JyNmZmYnfSk7'
        'IGRyYXdGbGVlV2FybmluZygpOyB9CiAgZmluYWxseSB7IGN0eC5maWxsVGV4dCA9IF9meDsgdGhQ'
        'bGF0ZSA9IF90cDsgfQogIGNvbnN0IF9mdyA9IF9mdC5maW5kKG89Pi9KVU1QSU5HIE9VVCBJTi8u'
        'dGVzdChvLnQpKTsKICByLmNvdW50ZG93bk5hbWVzU2hpcCA9ICEhX2Z3ICYmIC9GQVVTVFVTLy50'
        'ZXN0KF9mdy50KTsKICBjb25zdCBfb2wgPSBfcGxbMF0sIF9jZCA9IF9wbFtfcGwubGVuZ3RoLTFd'
        'OwogIHIuY291bnRkb3duQ2xlYXJPZk9iamVjdGl2ZSA9ICEhX29sICYmICEhX2NkICYmIF9wbC5s'
        'ZW5ndGg+PTIgJiYKICAgIChfb2wueCtfb2wudyA8IF9jZC54KSAmJiAoX2NkLngrX2NkLncgPD0g'
        'Vyk7CiAgZGFtYWdlRW5lbXkoZiwgZi5tYXhIcCo1LCBmLngsIGYueSwgdHJ1ZSwgJ2JvbHQnKTsg'
        'RlMuc3RlcCgyKTsKICByLmNhbm5vdEJlRGVzdHJveWVkID0gZW5lbWllcy5pbmNsdWRlcyhmKTsK'
        'ICBjb25zdCBraWxsID0gaWQ9PnsgZm9yKGNvbnN0IHMgb2YgZi5zdWJzKSBpZihzLmlkPT09aWQp'
        'eyBzLmRlYWQ9dHJ1ZTsgcy5ocD0wOyB9IH07CiAga2lsbCgnbmF2aWdhdGlvbicpOyBGUy5zdGVw'
        'KDIpOwogIGNvbnN0IGZ0ID0gZi5mbGVlVDsgRlMuc3RlcCgyMDApOwogIHIubm9OYXZpZ2F0aW9u'
        'Tm9KdW1wID0gZi5mbGVlVD09PWZ0OwogIHIubm9BcmdvWWV0ID0gIWFsbGllcy5zb21lKGE9PmEu'
        'dWlkPT09J1QxJykgJiYgIXNwYXduUS5zb21lKHE9PnEudWlkPT09J1QxJyk7CiAga2lsbCgnd2Vh'
        'cG9ucycpOyBGUy5zdGVwKDIpOwogIHIuY292ZXJUaGVBcmdvID0gbWlzc2lvbk9iaj09PSdDT1ZF'
        'UiBUSEUgQVJHTyc7CiAgbGV0IGFyZ28gPSBudWxsOwogIGNvbnN0IGF0ID0gRlMudW50aWwoKCk9'
        'PnsgYXJnbyA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J1QxJyk7IHJldHVybiAhIWFyZ28gJiYg'
        'YXJnby5ob2xkVCE9bnVsbDsgfSwgOTAwMCwgdHJ1ZSk7CiAgLy8gQm9hcmRpbmcgdGFrZXMgaXRz'
        'IHRpbWU6IHNoZSBzdGF5cyBvbiB0aGUgRmF1c3R1cywgbm90aGluZyBpcyB0YWtlbiB5ZXQuCiAg'
        'Y29uc3QgYXggPSBhcmdvICYmIGFyZ28ueDsKICBGUy5zdGVwKDQwMCk7CiAgci5ib2FyZGluZ0hv'
        'bGRzID0gYXQ+PTAgJiYgIUVWX0RPQ0tbJ1QxJ10gJiYgIWYuY2FwdHVyZWQgJiYgTWF0aC5hYnMo'
        'YXJnby54LWF4KSA8IDEgJiYgZW5lbWllcy5pbmNsdWRlcyhmKTsKICBjb25zdCBnb3QgPSBGUy51'
        'bnRpbCgoKT0+ISFFVl9ET0NLWydUMSddLCA5MDAwLCB0cnVlKTsKICBGUy5zdGVwKDUpOwogIHIu'
        'ZG9ja3NBbmRUYWtlcyA9IGdvdD49MCAmJiBmLmNhcHR1cmVkPT09dHJ1ZTsKICAvLyBBbmQgdGhl'
        'biBib3RoIGp1bXAgLSB0aGUgQXJnbyBkb2VzIG5vdCBmbHkgb24gdG8gdGhlIHJpZ2h0LgogIHIu'
        'YXJnb0p1bXBzT3V0ID0gISFhcmdvICYmIGFyZ28ud2FycE91dD4wICYmICFhcmdvLmNyb3NzaW5n'
        'OwogIHIuY29tcGxldGVDYXJkID0gISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J0ZBVVNUVVMg'
        'Q0FQVFVSRUQnOwogIEZTLnN0ZXAoMzAwKTsKICByLm5vRmFpbHVyZUFmdGVyd2FyZHMgPSAhYWxs'
        'aWVzLmluY2x1ZGVzKGFyZ28pICYmICEob2JqQ2FyZCAmJiBvYmpDYXJkLnRvbmU9PT0nZmFpbCcp'
        'OwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000NiBsZWZ0IGFsb25lIHNoZSBqdW1wczogZmFp'
        'bGVkJywgJ209NDYnLCBgCiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IGYgPSBlbmVtaWVzLmZpbmQo'
        'ZT0+ZS51aWQ9PT0nRjEnKTsKICBmb3IoY29uc3QgcyBvZiBmLnN1YnMpIHMuaHAgPSBzLm1heEhw'
        'ID0gMWU3OwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9iakNhcmQudG9u'
        'ZT09PSdmYWlsJywgOTAwMCwgdHJ1ZSk7CiAgcmV0dXJuIHtmYWlsQ2FyZDogdD49MCAmJiBvYmpD'
        'YXJkLnR4dD09PSdUSEUgRkFVU1RVUyBHT1QgQVdBWSd9O2ApOwoKc2NlbmFyaW8oJ000NyBEaWUg'
        'endlaXRlIEZsdWNodCcsICdtPTQ3JywgYAogIGNvbnN0IHIgPSB7fTsKICBzY29yZSA9IDUwMDA7'
        'CiAgRlMuc3RlcCg0MDApOwogIHIuaWNlbmkgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nVjEn'
        'ICYmIGUuaWNlbmkpOwogIHIuaGVjYXRlID0gZW5lbWllcy5zb21lKGU9PmUudWlkPT09J1YyJyAm'
        'JiBlLmltZz09PSdudGZkZWhlY2F0ZScpOwogIHIubm9BbGxpZXMgPSAhYWxsaWVzLnNvbWUoYT0+'
        'IWEuc21hbGwpOwogIHIubm9BZW9sdXMgPSAhZW5lbWllcy5zb21lKGU9PmUudWlkPT09J0sxJyk7'
        'CiAgY29uc3QgX3YxID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyksIF92MiA9IGVuZW1p'
        'ZXMuZmluZChlPT5lLnVpZD09PSdWMicpOwogIGNvbnN0IF95MSA9IF92MSAmJiBfdjEueSwgX3ky'
        'ID0gX3YyICYmIF92Mi55OwogIEZTLnN0ZXAoMzAwKTsKICByLnNoaXBzSG9sZEhlaWdodCA9ICEh'
        'X3YxICYmICEhX3YyICYmIE1hdGguYWJzKF92MS55LV95MSk8MC41ICYmIE1hdGguYWJzKF92Mi55'
        'LV95Mik8MC41ICYmCiAgICBNYXRoLmFicyhfdjEueS0xNTApPDEgJiYgTWF0aC5hYnMoX3YyLnkt'
        'MzUwKTwxOwogIHIuaWNlbmlGb3J0eVNlY29uZHMgPSAhIV92MSAmJiBfdjEuZmxlZVQ+MCAmJiBf'
        'djEuZmxlZVQgPD0gNDAqVElDS19IWjsKICByLm5vRW5kbGVzc1JlaW5mb3JjZW1lbnQgPSAhZXZS'
        'ZWluZjsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9PiFlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0n'
        'VjEnKSwgOTAwMCwgdHJ1ZSk7CiAgci5pY2VuaUdldHNBd2F5ID0gdD49MCAmJiBpY2VuRXNjYXBl'
        'cz09PTEgJiYgc2NvcmU+PTUwMDA7CiAgY29uc3QgdiA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09'
        'PSdWMicpOyBpZih2KSB2LmhwID0gMDsKICByLmNvbXBsZXRlQ2FyZCA9IEZTLnVudGlsKCgpPT4h'
        'IW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nSEVDQVRFIERFU1RST1lFRCcsIDMwMDAsIGZhbHNl'
        'KSA+PSAwOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000OCBEaWUgQXVma2xhZXJ1bmcnLCAn'
        'bT00OCcsIGAKICBjb25zdCByID0ge307CiAgc2NvcmUgPSAyMDAwOwogIHIuYW5ub3VuY2VkID0g'
        'Tk9USUNFUy5zb21lKG49Pm4udHh0PT09J0dURiBQRUdBU1VTIEFTU0lHTkVEJyk7CiAgRlMuc3Rl'
        'cCg0MDApOwogIHIuZmx5aW5nQVBlZ2FzdXMgPSBwbGF5ZXIuc2hpcD09PSdmaXBlZ2FzdXMnOwog'
        'IHIubm90aGluZ0xvY2tzSGVyID0gIWNhbkxvY2tPbihwbGF5ZXIpOwogIGNvbnN0IHYgPSBlbmVt'
        'aWVzLmZpbmQoZT0+ZS51aWQ9PT0nVjEnKTsKICByLmd1bnNIb2xkRmlyZSA9IGNhcEd1blRhcmdl'
        'dCh2KT09PW51bGw7CiAgci5ub0JlYW1PbkhlciA9ICFiZWFtVGFyZ2V0cyh2LCBmYWxzZSkuaW5j'
        'bHVkZXMocGxheWVyKTsKICByLm5vSGFuZ2FyID0gc2hpcFN3YXBSZWFkeSgpPT09ZmFsc2U7CiAg'
        'ci5yaW5nc1Nob3duID0gISF2ICYmIHYuc2NhblN1YnM9PT10cnVlICYmIHYuc3Vicy5ldmVyeShz'
        'PT4hcy5zY2FubmVkKTsKICBmb3IoY29uc3QgcyBvZiB2LnN1YnMpeyBjb25zdCBwID0gc3ViUG9z'
        'KHYsIHMpOyBGUy5ob2xkKHAueCwgcC55LCBTVUJfU0NBTl9USU1FICsgMjApOyB9CiAgci5hbGxG'
        'aXZlU2Nhbm5lZCA9IHYuc3Vicy5ldmVyeShzPT5zLnNjYW5uZWQpICYmIHYuc2Nhbm5lZD09PXRy'
        'dWU7CiAgRlMuc3RlcCgzKTsKICByLmNvbXBsZXRlQ2FyZCA9ICEhb2JqQ2FyZCAmJiBvYmpDYXJk'
        'LnR4dD09PSdPUklPTiBTQ0FOTkVEJzsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9PiFlbmVtaWVz'
        'LmluY2x1ZGVzKHYpLCAxNTAwLCBmYWxzZSk7CiAgci5vcmlvbkxlYXZlc1dpdGhvdXRQZW5hbHR5'
        'ID0gdD49MCAmJiBzY29yZSA+PSAyMDAwOwogIEZTLnVudGlsKCgpPT53YXZlPjQ4LCAzMDAwMCwg'
        'dHJ1ZSk7CiAgci5vd25IdWxsQmFja05leHRXYXZlID0gd2F2ZT09PTQ5ICYmIHBsYXllci5zaGlw'
        'PT09J2ZpbXlybWlkb24nOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ0NvbG9zc3VzIGJlYW1z'
        'IGFyZSBUZXJyYW4nLCAnJywgYAogIHJldHVybiB7bWFpbjogYmVhbUNvbCgnZ3R2YScsIHRydWUp'
        'PT09JyMwMGZmNTUnLCBhbnRpRmlnaHRlcjogYmVhbUNvbCgnZ3R2YScsIGZhbHNlKT09PScjNDQ5'
        'OWZmJ307YCwgdHJ1ZSk7CgpzY2VuYXJpbygnSG9MIHN0YXJ0IHVuY2hhbmdlZCcsICdtPTEnLCBg'
        'CiAgcmV0dXJuIHt3YXZlOiB3YXZlLCB0aG90aDogcGxheWVyLnNoaXA9PT0nZml0b3RoJywgdmFz'
        'dWRhbkNhbGw6IEFMTFlfRkFDX09OLnZhc3VkYW49PT10cnVlICYmIEFMTFlfRkFDX09OLnRlcnJh'
        'bj09PWZhbHNlfTtgKTsKCi8vIOKUgOKUgCBSdW5uZXIg4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSACihhc3luYygpPT57'
        'CiAgY29uc3QgYnJvd3NlciA9IGF3YWl0IGNocm9taXVtLmxhdW5jaCgpOwogIGxldCBmYWlscyA9'
        'IDA7CiAgY29uc3Qgb25seSA9IHByb2Nlc3MuYXJndls0XTsKICBmb3IoY29uc3Qgc2Mgb2Ygc2Nl'
        'bmFyaW9zKXsKICAgIGlmKG9ubHkgJiYgc2MubmFtZS5pbmRleE9mKG9ubHkpPDApIGNvbnRpbnVl'
        'OwogICAgY29uc3QgcGFnZSA9IGF3YWl0IGJyb3dzZXIubmV3UGFnZSgpOwogICAgY29uc3QgZXJy'
        'cyA9IFtdOwogICAgcGFnZS5vbigncGFnZWVycm9yJywgZT0+ZXJycy5wdXNoKFN0cmluZyhlLm1l'
        'c3NhZ2V8fGUpKSk7CiAgICBhd2FpdCBwYWdlLmdvdG8oJ2ZpbGU6Ly8nICsgdG1wICsgJz8nICsg'
        'c2MucXVlcnkpOwogICAgYXdhaXQgcGFnZS53YWl0Rm9yVGltZW91dCgzMDApOwogICAgbGV0IHJl'
        'czsKICAgIHRyeXsKICAgICAgcmVzID0gYXdhaXQgcGFnZS5ldmFsdWF0ZShIRUxQRVJTICsgYFxu'
        'RlMuZmFrZUltYWdlcygpO2AgKyAoc2Mubm9MYXVuY2ggPyAnJyA6ICcgbGF1bmNoR2FtZSgpOycp'
        'ICsgYFxuKGZ1bmN0aW9uKCl7JHtzYy5ib2R5fX0pKClgKTsKICAgIH1jYXRjaChlKXsgcmVzID0g'
        'bnVsbDsgZXJycy5wdXNoKFN0cmluZyhlLm1lc3NhZ2V8fGUpKTsgfQogICAgY29uc29sZS5sb2co'
        'c2MubmFtZSArICcgICg/JyArIHNjLnF1ZXJ5ICsgJyknKTsKICAgIGlmKHJlcykgZm9yKGNvbnN0'
        'IFtrLHZdIG9mIE9iamVjdC5lbnRyaWVzKHJlcykpewogICAgICBjb25zdCBnb29kID0gKHR5cGVv'
        'ZiB2PT09J2Jvb2xlYW4nKSA/IHYgOiB0cnVlOwogICAgICBpZighZ29vZCkgZmFpbHMrKzsKICAg'
        'ICAgY29uc29sZS5sb2coKGdvb2QgPyAnICBvayAgICAnIDogJyAgRkFJTCAgJykgKyBrICsgKHR5'
        'cGVvZiB2PT09J2Jvb2xlYW4nID8gJycgOiAnID0gJyArIEpTT04uc3RyaW5naWZ5KHYpKSk7CiAg'
        'ICB9CiAgICBpZihlcnJzLmxlbmd0aCl7IGZhaWxzKys7IGNvbnNvbGUubG9nKCcgIEZBSUwgIHBh'
        'Z2UgZXJyb3JzOlxuICAgICcgKyBlcnJzLnNsaWNlKDAsNCkuam9pbignXG4gICAgJykpOyB9CiAg'
        'ICBhd2FpdCBwYWdlLmNsb3NlKCk7CiAgfQogIGF3YWl0IGJyb3dzZXIuY2xvc2UoKTsKICBmcy51'
        'bmxpbmtTeW5jKHRtcCk7CiAgY29uc29sZS5sb2coJ1xuJyArIChmYWlscyA/IGZhaWxzICsgJyBG'
        'QUlMRUQnIDogJ2FsbCBwYXNzZWQnKSk7CiAgcHJvY2Vzcy5leGl0KGZhaWxzID8gMSA6IDApOwp9'
        'KSgpOwo='
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
        'ZW50IGlzIGEgdW5pdC4KLy8gZ2VyZXR0ZXQgLyB2ZXJsb3JlbiBjb3VudCBwcm90ZWN0ZWQgc2hp'
        'cHMsIHRoZXkgbmFtZSBubyB1bml0Lgpjb25zdCBUUklHX05PX0lEICA9IG5ldyBTZXQoWydzZWsn'
        'LCAnZXJmdWVsbHQnLCAnZ2VyZXR0ZXQnLCAndmVybG9yZW4nXSk7CmNvbnN0IEVGRkVDVF9VTklU'
        'ID0gbmV3IFNldChbJ2VpbndhcnBlbicsICdzZWl0ZScsICdyYXVzJywgJ2hlaWxlbicsICdrYXBl'
        'cm4nLCAnZnJlaWdlYmVuJywgJ2t1bGlzc2UnXSk7CgpsZXQgZXJyb3JzID0gMCwgbWlzc2lvbnMg'
        'PSAwOwpmb3IoY29uc3Qga2V5IG9mIE9iamVjdC5rZXlzKFNDUklQVF9XQVZFUykuc29ydCgoYSwg'
        'YikgPT4gYSAtIGIpKXsKICBjb25zdCBtID0gU0NSSVBUX1dBVkVTW2tleV0sIHVuaXRzID0gbS51'
        'IHx8IFtdLCBldnMgPSBtLmV2IHx8IFtdOwogIGNvbnN0IHRhZyA9ICdNJyArIFN0cmluZyhrZXkp'
        'LnBhZFN0YXJ0KDMsICcwJyk7CiAgY29uc3QgaWRzID0gbmV3IE1hcCgpOwogIGNvbnN0IGJhZCA9'
        'IFtdOwogIG1pc3Npb25zKys7CgogIGZvcihjb25zdCB1IG9mIHVuaXRzKXsKICAgIGlmKCF1Lmlk'
        'KSBiYWQucHVzaCgndW5pdCB3aXRob3V0IGlkICgnICsgdS5jICsgJyknKTsKICAgIGVsc2UgaWYo'
        'aWRzLmhhcyh1LmlkKSkgYmFkLnB1c2goJ2lkIHVzZWQgdHdpY2U6ICcgKyB1LmlkKTsKICAgIGlk'
        'cy5zZXQodS5pZCwgdSk7CiAgICBpZighQ0FUX0ZBQ1t1LmNdICYmICFDQVRfRklYW3UuY10pCiAg'
        'ICAgIGJhZC5wdXNoKHUuaWQgKyAnOiB1bmtub3duIGNhdGVnb3J5ICInICsgdS5jICsgJyIgLSB3'
        'b3VsZCBuZXZlciBzcGF3bicpOwogIH0KICBmb3IoY29uc3QgdSBvZiB1bml0cykKICAgIGlmKHUu'
        'c3ByICYmICFIVUxMX0tFWVMuaGFzKHUuc3ByKSkgYmFkLnB1c2godS5pZCArICc6IHVua25vd24g'
        'aHVsbCAiJyArIHUuc3ByICsgJyInKTsKICBpZihtLmZhYyAhPT0gQ1lDTEVfRkFDKCtrZXkpKSBi'
        'YWQucHVzaCgnZmFjdGlvbiAnICsgbS5mYWMgKyAnLCBidXQgdGhpcyB3YXZlIGJlbG9uZ3MgdG8g'
        'dGhlICcgKyBDWUNMRV9GQUMoK2tleSkgKyAnIGN5Y2xlJyk7CiAgZm9yKGNvbnN0IHUgb2YgdW5p'
        'dHMpewogICAgaWYodS5kb2NrVG8gJiYgIWlkcy5oYXModS5kb2NrVG8pKSBiYWQucHVzaCh1Lmlk'
        'ICsgJzogZG9ja1RvIHBvaW50cyBhdCBtaXNzaW5nIGlkICcgKyB1LmRvY2tUbyk7CiAgICBpZih1'
        'LmF0ICYmICFpZHMuaGFzKHUuYXQpKSAgICAgICAgIGJhZC5wdXNoKHUuaWQgKyAnOiBhdCBwb2lu'
        'dHMgYXQgbWlzc2luZyBpZCAnICsgdS5hdCk7CiAgfQoKICBjb25zdCB3YXJwZWRJbiA9IG5ldyBT'
        'ZXQoKTsKICBsZXQgcmVpbmZPbiA9IGZhbHNlLCByZWluZk9mZiA9IGZhbHNlOwogIGV2cy5mb3JF'
        'YWNoKChlLCBpKSA9PiB7CiAgICBjb25zdCB3aGVyZSA9ICdldmVudCAnICsgKGkgKyAxKSArICcg'
        'KCcgKyBlLnQgKyAnIC0+ICcgKyBlLncgKyAnKSc7CiAgICBjb25zdCBhcmcgPSAoZS5hMiAhPT0g'
        'dW5kZWZpbmVkKSA/IGUuYTIgOiBlLmE7CiAgICBpZighVFJJR0dFUlMuaGFzKGUudCkpIGJhZC5w'
        'dXNoKHdoZXJlICsgJzogdW5rbm93biB0cmlnZ2VyICInICsgZS50ICsgJyInKTsKICAgIGlmKCFF'
        'RkZFQ1RTLmhhcyhlLncpKSAgYmFkLnB1c2god2hlcmUgKyAnOiB1bmtub3duIGVmZmVjdCAiJyAr'
        'IGUudyArICciJyk7CiAgICAvLyBBIHRyaWdnZXIgbWF5IG5hbWUgc2V2ZXJhbCBpZHMgam9pbmVk'
        'IHdpdGggJysnLgogICAgaWYoVFJJR0dFUlMuaGFzKGUudCkgJiYgIVRSSUdfTk9fSUQuaGFzKGUu'
        'dCkpCiAgICAgIGZvcihjb25zdCBpZCBvZiBTdHJpbmcoZS5hKS5zcGxpdCgnKycpKQogICAgICAg'
        'IGlmKCFpZHMuaGFzKGlkKSkgYmFkLnB1c2god2hlcmUgKyAnOiB0cmlnZ2VyIHBvaW50cyBhdCBt'
        'aXNzaW5nIGlkICcgKyBpZCk7CiAgICBpZihlLnQgPT09ICdhbmdlZG9ja3QnICYmIGlkcy5oYXMo'
        'ZS5hKSAmJiAhaWRzLmdldChlLmEpLmRvY2tUbykKICAgICAgYmFkLnB1c2god2hlcmUgKyAnOiAn'
        'ICsgZS5hICsgJyBoYXMgbm8gZG9ja1RvLCBpdCBjYW4gbmV2ZXIgZG9jaycpOwogICAgaWYoRUZG'
        'RUNUX1VOSVQuaGFzKGUudykgJiYgIWlkcy5oYXMoYXJnKSkKICAgICAgYmFkLnB1c2god2hlcmUg'
        'KyAnOiBlZmZlY3QgcG9pbnRzIGF0IG1pc3NpbmcgaWQgJyArIGFyZyk7CiAgICBpZihlLncgPT09'
        'ICdqYWdkJyAmJiBhcmcgJiYgIWlkcy5oYXMoYXJnKSkKICAgICAgYmFkLnB1c2god2hlcmUgKyAn'
        'OiBodW50IHRhcmdldCBpcyBhIG1pc3NpbmcgaWQgJyArIGFyZyk7CiAgICBpZihlLncgPT09ICdl'
        'aW53YXJwZW4nKXsKICAgICAgd2FycGVkSW4uYWRkKGFyZyk7CiAgICAgIGlmKGlkcy5oYXMoYXJn'
        'KSAmJiAhaWRzLmdldChhcmcpLndhaXQpCiAgICAgICAgYmFkLnB1c2god2hlcmUgKyAnOiAnICsg'
        'YXJnICsgJyBpcyBub3Qgd2FpdGluZyAtIHdhcnBpbmcgaXQgaW4gZG9lcyBub3RoaW5nJyk7CiAg'
        'ICB9CiAgICBpZihlLncgPT09ICduYWNoc2NodWInKXsgaWYoYXJnID09PSAnYXVzJykgcmVpbmZP'
        'ZmYgPSB0cnVlOyBlbHNlIHJlaW5mT24gPSB0cnVlOyB9CiAgICBpZihlLncgPT09ICdlbmRlJykg'
        'cmVpbmZPZmYgPSB0cnVlOwogIH0pOwogIGZvcihjb25zdCB1IG9mIHVuaXRzKQogICAgaWYodS53'
        'YWl0ICYmICF3YXJwZWRJbi5oYXModS5pZCkpIGJhZC5wdXNoKHUuaWQgKyAnOiB3YWl0cywgYnV0'
        'IG5vIGV2ZW50IGV2ZXIgd2FycHMgaXQgaW4nKTsKICBpZihyZWluZk9uICYmICFyZWluZk9mZikg'
        'YmFkLnB1c2goJ3JlaW5mb3JjZW1lbnRzIHN3aXRjaGVkIG9uLCBuZXZlciBzd2l0Y2hlZCBvZmYn'
        'KTsKICBpZihtLmh1bnQgJiYgIWlkcy5oYXMobS5odW50KSkgYmFkLnB1c2goJ2h1bnQgcG9pbnRz'
        'IGF0IG1pc3NpbmcgaWQgJyArIG0uaHVudCk7CgogIGlmKGJhZC5sZW5ndGgpeyBlcnJvcnMgKz0g'
        'YmFkLmxlbmd0aDsgY29uc29sZS5sb2codGFnICsgJyAnICsgKG0ubmFtZSB8fCAnJykpOyBiYWQu'
        'Zm9yRWFjaChiID0+IGNvbnNvbGUubG9nKCcgICAnICsgYikpOyB9Cn0KY29uc29sZS5sb2coJ1xu'
        'JyArIG1pc3Npb25zICsgJyBtaXNzaW9ucyBjaGVja2VkLCAnICsgZXJyb3JzICsgJyBwcm9ibGVt'
        'cycpOwpjb25zb2xlLmxvZygna25vd24gdHJpZ2dlcnM6ICcgKyBbLi4uVFJJR0dFUlNdLmpvaW4o'
        'JyAnKSk7CmNvbnNvbGUubG9nKCdrbm93biBlZmZlY3RzOiAgJyArIFsuLi5FRkZFQ1RTXS5qb2lu'
        'KCcgJykpOwpwcm9jZXNzLmV4aXQoZXJyb3JzID8gMSA6IDApOwo='
    ),
}
for name, data in TEST_FILES.items():
    open(name, 'wb').write(base64.b64decode(data))
print("v139 applied: NTF missions 49-54, checks updated. Now run: python3 assemble.py 139")
