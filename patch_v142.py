#!/usr/bin/env python3
"""FS3 v142 - NTF missions 55 to 60, the end of the NTF cycle.

    55 Der Anflug         the Knossos at the right edge. Four NTF cruisers
                          come in from the left one after another and make
                          for the portal; none may reach it. Engines out
                          stops one.
    56 Die Verraeter      an allied Leviathan and a Deimos against fighters.
                          Once the first wing is down the Leviathan goes over
                          to the NTF and more fighters and bombers come.
    57 Die Nachhut        the player flies an Ursa with Stiletto bombs for
                          this one: two NTF Aeolus and an NTF Deimos hold the
                          rear. Engines and weapons of all three out; they
                          cannot be destroyed before that.
    58 Das Tor            the portal, and in front of it a line of sentry
                          guns, a Fenris and an Aeolus.
    59 Die letzte Sperre  an NTF Hecate and an NTF Orion in front of the
                          portal.
    60 Der Sprung         the Iceni runs for the portal and goes through -
                          she cannot be stopped. Her escort can.

Everything around it:
  - scene: missions with the same scene show the same backdrop, the same
    planets and suns in the same places and the same light, within one
    run. 55, 58, 59 and 60 share the Knossos scene. A new run rolls anew.
  - portal: a ship that runs for the right edge in such a mission jumps
    at the portal, through a turquoise vortex (images/warp_knossos.webp).
  - Trigger 'entkommen' N: N ships got away. 'subsystem' accepts several
    ids joined with '+'.
  - The Iceni can run (escape, escWarp), can be held above her hull floor
    (noKill) and can have no engines to shoot (engineProof).
  - sec on a mission: with ship, the player also carries that secondary
    for the mission; the next wave gives the old one back.

Needs v141. Edits src/00_head.html, src/20_render.js, src/30_waves.js,
src/40_world.js, src/60_effects.js and src/70_ui.js in place, and writes
the updated fieldsim.js and swtest.js. Run assemble.py afterwards.
"""
import sys


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def load(p):
    return open(p, encoding="utf-8").read()


hd = load("src/00_head.html")
rd = load("src/20_render.js")
wv = load("src/30_waves.js")
wo = load("src/40_world.js")
fx = load("src/60_effects.js")
ui = load("src/70_ui.js")

# ══ The turquoise vortex ════════════════════════════════════════════════
hd = replace_once(
    hd,
    '<img id="warp_img" src="@@FS3_ASSET:images/warp_img.webp@@" style="display:none">\n',
    '<img id="warp_img" src="@@FS3_ASSET:images/warp_img.webp@@" style="display:none">\n'
    '<img id="warp_knossos_img" src="@@FS3_ASSET:images/warp_knossos.webp@@" style="display:none">\n',
    "head img")
rd = replace_once(
    rd,
    "const HULL_IMG=document.getElementById('hull_img');\n",
    "// The Knossos vortex, turquoise. Same frame sheet layout as the normal\n"
    "// one; should it ever be a single picture instead, it is drawn whole.\n"
    "const KNOSSOS_WARP_IMG=document.getElementById('warp_knossos_img');\n"
    "function knossosWarpOk(){\n"
    "  return !!KNOSSOS_WARP_IMG && KNOSSOS_WARP_IMG.complete && KNOSSOS_WARP_IMG.naturalWidth>0;\n"
    "}\n"
    "const HULL_IMG=document.getElementById('hull_img');\n",
    "knossos img")
ui = replace_once(
    ui,
    "          ctx.drawImage(WARP_IMG,\n"
    "            (wF%WARP_COLS)*WARP_CELL, ((wF/WARP_COLS)|0)*WARP_CELL,\n"
    "            WARP_CELL, WARP_CELL,\n"
    "            -WS/2,-WS/2,WS,WS);\n",
    "          // Through the Knossos: the turquoise vortex.\n"
    "          if(e.portalWarp && knossosWarpOk()){\n"
    "            const _kw = KNOSSOS_WARP_IMG;\n"
    "            if(_kw.naturalWidth > WARP_CELL*1.5)\n"
    "              ctx.drawImage(_kw, (wF%WARP_COLS)*WARP_CELL, ((wF/WARP_COLS)|0)*WARP_CELL,\n"
    "                            WARP_CELL, WARP_CELL, -WS/2,-WS/2,WS,WS);\n"
    "            else ctx.drawImage(_kw, -WS/2,-WS/2,WS,WS);\n"
    "          } else\n"
    "          ctx.drawImage(WARP_IMG,\n"
    "            (wF%WARP_COLS)*WARP_CELL, ((wF/WARP_COLS)|0)*WARP_CELL,\n"
    "            WARP_CELL, WARP_CELL,\n"
    "            -WS/2,-WS/2,WS,WS);\n",
    "draw knossos warp")

# ══ The portal: runners jump at it ══════════════════════════════════════
wv = replace_once(
    wv,
    "    if(e.escWarp && e.x + _ew*0.5 >= W - TRANS_EDGE_PAD){\n"
    "      e.escaping = 0;\n",
    "    // With the Knossos on the field they jump at the portal, through its\n"
    "    // own vortex, instead of at the edge.\n"
    "    const _atJump = portalOn ? (e.x >= PORTAL_X) : (e.x + _ew*0.5 >= W - TRANS_EDGE_PAD);\n"
    "    if(e.escWarp && _atJump){\n"
    "      if(portalOn) e.portalWarp = true;\n"
    "      e.escaping = 0;\n",
    "escWarp portal")
wv = replace_once(
    wv,
    "function tickEscapers(){\n",
    "// Set by a mission with the Knossos in it (portal). Where the runners\n"
    "// jump: a little inside the right edge, at the ring.\n"
    "let portalOn = false;\n"
    "const PORTAL_X = 670;\n"
    "function tickEscapers(){\n",
    "portal vars")
wv = replace_once(
    wv,
    "  scanUnderFire = !!def.scanUnderFire;\n",
    "  scanUnderFire = !!def.scanUnderFire;\n"
    "  portalOn = !!def.portal;\n"
    "  if(def.scene) useScene(def.scene);\n",
    "portal+scene set")
fx = replace_once(
    fx,
    "  scanUnderFire=false;\n",
    "  scanUnderFire=false; portalOn=false;\n",
    "portal reset")

# ══ Scenes: the same sky for the same place, within a run ═══════════════
rd = replace_once(
    rd,
    "function rollBodies(){\n",
    "// A place that comes back within a run keeps its sky: the same backdrop,\n"
    "// the same planets and suns where they stood the first time, the same\n"
    "// light. The first mission of a scene takes whatever was rolled and\n"
    "// writes it down; every later one puts it back. A new run starts empty.\n"
    "let SCENES = {};\n"
    "function useScene(key){\n"
    "  const s = SCENES[key];\n"
    "  if(!s){\n"
    "    SCENES[key] = {neb: nebFading ? nebNxt : nebCur, light: lightAng,\n"
    "                   bodies: bodies.map(function(b){ return Object.assign({}, b); })};\n"
    "    return;\n"
    "  }\n"
    "  bodies = s.bodies.map(function(b){ return Object.assign({}, b); });\n"
    "  lightAng = s.light; lightSun = null;\n"
    "  for(const b of bodies) if(b.kind==='sun'){ lightSun = b; break; }\n"
    "  // Under the blackout the backdrop may still be fading over: then the\n"
    "  // one it fades to is the one that has to be right.\n"
    "  if(nebFading) nebNxt = s.neb; else nebCur = s.neb;\n"
    "}\n"
    "\n"
    "function rollBodies(){\n",
    "useScene")
fx = replace_once(
    fx,
    "currentFaction='ntf';icenEscapes=0;runTime=0;",
    "currentFaction='ntf';icenEscapes=0;runTime=0;SCENES={};",
    "scenes reset")

# ══ Triggers ════════════════════════════════════════════════════════════
wv = replace_once(
    wv,
    "    case 'subsystem': {\n"
    "      const su = byId(ev.a)[0];\n"
    "      if(!su || !hasSubsystems(su)) return false;\n"
    "      // Several may be named, joined with '+': all of them have to be down.\n"
    "      return String(ev.b || 'communication').split('+')\n"
    "               .every(function(id){ return !subOK(su, id); });\n"
    "    }\n",
    "    case 'subsystem': {\n"
    "      // Several ships joined with '+': on every one of them. Several\n"
    "      // systems joined with '+': all of them have to be down.\n"
    "      return evIds(ev.a).every(function(uid){\n"
    "        const su = byId(uid)[0];\n"
    "        if(!su || !hasSubsystems(su)) return false;\n"
    "        return String(ev.b || 'communication').split('+')\n"
    "                 .every(function(id){ return !subOK(su, id); });\n"
    "      });\n"
    "    }\n"
    "    // Ships that got away this wave (ran off the field or jumped).\n"
    "    case 'entkommen':    return escGone >= (ev.a||1);\n",
    "subsystem lists + entkommen")

# ══ The Iceni runs; unit options noKill and engineProof ════════════════
wv = replace_once(
    wv,
    "         flee:u.flee, navProof:u.navProof, fleeFree:u.fleeFree,\n"
    "         still:u.still, fixY:(u.y!=null)});\n",
    "         flee:u.flee, navProof:u.navProof, fleeFree:u.fleeFree,\n"
    "         still:u.still, fixY:(u.y!=null),\n"
    "         escape:u.escape, escWarp:u.escWarp, noKill:u.noKill, engineProof:u.engineProof});\n",
    "iceni put")
wv = replace_once(
    wv,
    "             fleeFree:u.fleeFree, hurt:u.hurt, armed:u.armed, noFlee:u.noFlee,\n",
    "             fleeFree:u.fleeFree, hurt:u.hurt, armed:u.armed, noFlee:u.noFlee,\n"
    "             noKill:u.noKill,\n",
    "enemy put noKill")
wv = replace_once(
    wv,
    "  if(sp.navProof && e.subs) e.subs = e.subs.filter(function(s){ return s.id!=='navigation'; });\n",
    "  if(sp.navProof && e.subs) e.subs = e.subs.filter(function(s){ return s.id!=='navigation'; });\n"
    "  // A run nobody can stop: no engines to shoot either.\n"
    "  if(sp.engineProof && e.subs) e.subs = e.subs.filter(function(s){ return s.id!=='engines'; });\n"
    "  // Held above her hull floor for the whole wave: she is not to die here.\n"
    "  if(sp.noKill) e.keepAlive = true;\n",
    "engineProof noKill")
wo = replace_once(
    wo,
    "  if(e.hp <= 0 && !e.dead && !e.captureLock &&\n",
    "  if(e.hp <= 0 && !e.dead && !e.captureLock && !e.keepAlive &&\n",
    "death roll keepAlive")
wo = replace_once(
    wo,
    "  if(e.defectLock || e.captureLock || (e.scanLock && !e.scanned)){\n",
    "  if(e.defectLock || e.captureLock || e.keepAlive || (e.scanLock && !e.scanned)){\n",
    "lock keepAlive")

# ══ A secondary with the lent hull ═════════════════════════════════════
wv = replace_once(
    wv,
    "  if(def.ship) forceShip(def.ship);\n",
    "  if(def.ship) forceShip(def.ship, def.sec);\n",
    "forceShip sec")
ui = replace_once(
    ui,
    "function forceShip(key){\n"
    "  if(!forcedPrev) forcedPrev = player.ship;\n"
    "  applyShip(key);\n",
    "// sec: the secondary that goes with the hull for this mission.\n"
    "let forcedSecPrev = '';\n"
    "function forceShip(key, sec){\n"
    "  if(!forcedPrev){ forcedPrev = player.ship; forcedSecPrev = player.sec; }\n"
    "  if(sec) player.sec = sec;\n"
    "  applyShip(key);\n",
    "forceShip")
ui = replace_once(
    ui,
    "  const k = forcedPrev; forcedPrev = '';\n"
    "  applyShip(k);\n",
    "  const k = forcedPrev; forcedPrev = '';\n"
    "  if(forcedSecPrev) player.sec = forcedSecPrev;\n"
    "  forcedSecPrev = '';\n"
    "  applyShip(k);\n",
    "releaseShip sec")

# ══ Missions 55 - 60 ════════════════════════════════════════════════════
wv = replace_once(
    wv,
    "       {t:'alleZerstoert', a:'T1+T2+T3+T4', w:'nachschub', a2:'aus'}\n"
    "     ]}\n"
    "};\n",
    "       {t:'alleZerstoert', a:'T1+T2+T3+T4', w:'nachschub', a2:'aus'}\n"
    "     ]},\n"
    "\n"
    "  // 55, 58, 59 and 60 are the same place: the Knossos at the right edge,\n"
    "  // under the same sky within a run (scene).\n"
    "  55:{name:'Der Anflug', fac:'ntf', o:'clear', live:5, scene:'knossos', portal:true,\n"
    "      ziel:'STOP THE CRUISERS BEFORE THEY REACH THE PORTAL', u:[\n"
    "       // Four NTF cruisers come in from the left one after another and\n"
    "       // make for the portal. None may reach it; engines out stops one.\n"
    "       {id:'P1', c:'in', n:1, spr:'inknossos45deg', invuln:true, edge:0.5, y:275},\n"
    "       {id:'K1', c:'cr', n:1, spr:'ntfcraeolus',    t:2,  x:-80, y:170, escape:0.28, escWarp:true},\n"
    "       {id:'K2', c:'cr', n:1, spr:'ntfcrfenris',    t:16, x:-80, y:340, escape:0.28, escWarp:true},\n"
    "       {id:'K3', c:'cr', n:1, spr:'ntfcrleviathan', t:32, x:-80, y:210, escape:0.28, escWarp:true},\n"
    "       {id:'K4', c:'cr', n:1, spr:'ntfcraeolus',    t:48, x:-80, y:360, escape:0.28, escWarp:true},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'sek', a:6, w:'nachschub', a2:'an'},\n"
    "       {t:'alleZerstoert', a:'K1+K2+K3+K4', w:'nachschub', a2:'aus'},\n"
    "       {t:'entkommen', a:1, w:'zielverfehlt', a2:'A CRUISER REACHED THE PORTAL'},\n"
    "       {t:'vernichtet', a:'K1+K2+K3+K4', w:'zielerfuellt', a2:'ALL CRUISERS STOPPED'}\n"
    "     ]},\n"
    "\n"
    "  56:{name:'Die Verraeter', fac:'ntf', o:'clear', live:5,\n"
    "      ziel:'COVER THE FLEET', u:[\n"
    "       // A Leviathan and a Deimos of ours against fighters. Once the\n"
    "       // first wing is down the Leviathan goes over to the NTF, and more\n"
    "       // fighters and bombers come.\n"
    "       {id:'A1', c:'cr', n:1, spr:'crleviathan', side:'ally', y:170},\n"
    "       {id:'A2', c:'co', n:1, spr:'codeimos', side:'ally', y:390},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:2, wait:true},\n"
    "       {id:'B1', c:'bo', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A1'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'meldung', a2:'the leviathan has gone over to the ntf'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'ziel', a2:'DESTROY THE LEVIATHAN'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},\n"
    "       {t:'vernichtet', a:'A2', w:'meldung', a2:'gtcv deimos lost'},\n"
    "       {t:'vernichtet', a:'A1', w:'zielerfuellt', a2:'TRAITOR DESTROYED'}\n"
    "     ]},\n"
    "\n"
    "  57:{name:'Die Nachhut', fac:'ntf', o:'clear', live:5, ship:'boursa', sec:'stiletto',\n"
    "      ziel:'DISABLE THE REARGUARD - ENGINES AND WEAPONS OF ALL THREE', u:[\n"
    "       // The player flies an Ursa with Stiletto bombs for this one. Two\n"
    "       // Aeolus and a Deimos hold the rear; they are to be left dead in\n"
    "       // space, not destroyed - until then they cannot be.\n"
    "       {id:'K1', c:'cr', n:1, spr:'ntfcraeolus', still:true, x:580, y:140,\n"
    "        capture:true, noFlee:true},\n"
    "       {id:'K2', c:'cr', n:1, spr:'ntfcraeolus', still:true, x:580, y:380,\n"
    "        capture:true, noFlee:true},\n"
    "       {id:'D1', c:'co', n:1, spr:'ntfcodeimos', still:true, x:440, y:260,\n"
    "        capture:true, noFlee:true},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:2, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'subsystem', a:'K1', b:'engines+weapons', w:'meldung', a2:'first aeolus disabled'},\n"
    "       {t:'subsystem', a:'K2', b:'engines+weapons', w:'meldung', a2:'second aeolus disabled'},\n"
    "       {t:'subsystem', a:'D1', b:'engines+weapons', w:'meldung', a2:'deimos disabled'},\n"
    "       {t:'subsystem', a:'K1+K2+D1', b:'engines+weapons', w:'zielerfuellt', a2:'REARGUARD DISABLED'},\n"
    "       {t:'subsystem', a:'K1+K2+D1', b:'engines+weapons', w:'kulisse', a2:'K1'},\n"
    "       {t:'subsystem', a:'K1+K2+D1', b:'engines+weapons', w:'kulisse', a2:'K2'},\n"
    "       {t:'subsystem', a:'K1+K2+D1', b:'engines+weapons', w:'kulisse', a2:'D1'}\n"
    "     ]},\n"
    "\n"
    "  58:{name:'Das Tor', fac:'ntf', o:'clear', live:5, scene:'knossos', portal:true,\n"
    "      ziel:'BREAK THE DEFENCE IN FRONT OF THE PORTAL', u:[\n"
    "       // In front of the portal: a line of sentry guns, a Fenris and an\n"
    "       // Aeolus. Fighters until both cruisers are down.\n"
    "       {id:'P1', c:'in', n:1, spr:'inknossos45deg', invuln:true, edge:0.5, y:275},\n"
    "       {id:'G1', c:'sg', n:6, spr:'sgcerberus', x:540},\n"
    "       {id:'K1', c:'cr', n:1, spr:'ntfcrfenris', still:true, x:620, y:150},\n"
    "       {id:'K2', c:'cr', n:1, spr:'ntfcraeolus', still:true, x:620, y:380},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'B1', c:'bo', n:1, wait:true},\n"
    "       {id:'E2', c:'fi', n:2, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'sek', a:4, w:'nachschub', a2:'an'},\n"
    "       {t:'alleZerstoert', a:'K1+K2', w:'nachschub', a2:'aus'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},\n"
    "       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'alleZerstoert', a:'K1+K2+G1', w:'zielerfuellt', a2:'PORTAL DEFENCE BROKEN'}\n"
    "     ]},\n"
    "\n"
    "  59:{name:'Die letzte Sperre', fac:'ntf', o:'clear', live:5, scene:'knossos', portal:true,\n"
    "      ziel:'DESTROY THE HECATE AND THE ORION', u:[\n"
    "       // The last two destroyers of the NTF, in front of the portal.\n"
    "       {id:'P1', c:'in', n:1, spr:'inknossos45deg', invuln:true, edge:0.5, y:275},\n"
    "       {id:'V1', c:'de', n:1, spr:'ntfdehecate', still:true, y:160, noFlee:true},\n"
    "       {id:'V2', c:'de', n:1, spr:'ntfdeorion',  still:true, y:370, noFlee:true},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:1, wait:true},\n"
    "       {id:'B1', c:'bo', n:2, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'sek', a:15, w:'einwarpen', a2:'B1'},\n"
    "       {t:'vernichtet', a:'V1', w:'meldung', a2:'hecate destroyed'},\n"
    "       {t:'vernichtet', a:'V2', w:'meldung', a2:'orion destroyed'},\n"
    "       {t:'vernichtet', a:'V1+V2', w:'zielerfuellt', a2:'THE WAY TO THE PORTAL IS OPEN'}\n"
    "     ]},\n"
    "\n"
    "  60:{name:'Der Sprung', fac:'ntf', o:'clear', live:6, scene:'knossos', portal:true,\n"
    "      ziel:'DESTROY THE ESCORT OF THE ICENI', u:[\n"
    "       // The Iceni runs for the portal and goes through. She cannot be\n"
    "       // stopped - no engines, no navigation to shoot, and she does not\n"
    "       // die here. Her escort can be destroyed.\n"
    "       {id:'P1', c:'in', n:1, spr:'inknossos45deg', invuln:true, edge:0.5, y:275},\n"
    "       {id:'V1', c:'ic', n:1, x:-150, y:270, escape:0.2, escWarp:true, noKill:true,\n"
    "        engineProof:true, navProof:true, fleeFree:true},\n"
    "       {id:'K1', c:'cr', n:1, spr:'ntfcraeolus', still:true, x:560, y:130},\n"
    "       {id:'K2', c:'cr', n:1, spr:'ntfcrfenris', still:true, x:600, y:410},\n"
    "       {id:'C1', c:'co', n:1, spr:'ntfcodeimos', still:true, x:400, y:420},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:2, wait:true},\n"
    "       {id:'B1', c:'bo', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},\n"
    "       {t:'verlaesst', a:'V1', w:'meldung', a2:'the iceni is through the knossos'},\n"
    "       {t:'vernichtet', a:'K1+K2+C1', w:'zielerfuellt', a2:'ESCORT DESTROYED'}\n"
    "     ]}\n"
    "};\n",
    "missions 55-60")

open("src/00_head.html", "w", encoding="utf-8").write(hd)
open("src/20_render.js", "w", encoding="utf-8").write(rd)
open("src/30_waves.js", "w", encoding="utf-8").write(wv)
open("src/40_world.js", "w", encoding="utf-8").write(wo)
open("src/60_effects.js", "w", encoding="utf-8").write(fx)
open("src/70_ui.js", "w", encoding="utf-8").write(ui)

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
        'cmUgbGVmdCBvdXQuCmZvcihsZXQgbT0xO208PTYwO20rKykgaWYobSE9PTEyICYmIG0hPT0yMykg'
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
        'ci5vcmlvblRocm91Z2hUaGVHYXAgPSAhIW8gJiYgby50cmFuc2l0PT09dHJ1ZTsKICAvLyBTaGUg'
        'd2FycHMgaW4gb24gc2NyZWVuIGluc3RlYWQgb2YgcG9wcGluZyB1cCBhdCB0aGUgZWRnZS4KICBj'
        'b25zdCBfb2kgPSBJTUdTW28uaW1nXSwgX29oID0gX29pID8gX29pLndpZHRoKm8uc2MqMC41IDog'
        'MDsKICByLm9yaW9uV2FycHNJbiA9IG8ud2FycD4wICYmIG8ueCAtIF9vaCA+PSAwOwogIEZTLnN0'
        'ZXAoMik7CiAgci5uZXdPYmplY3RpdmUgPSBtaXNzaW9uT2JqPT09J0dFVCBUSEUgT1JJT04gVEhS'
        'T1VHSCc7CiAgby5ocCA9IG8ubWF4SHAgPSAxZTc7IGZvcihjb25zdCBzIG9mIG8uc3Vic3x8W10p'
        'IHMuaHAgPSBzLm1heEhwID0gMWU3OwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+eyBpZihhbGxp'
        'ZXMuaW5jbHVkZXMobykpIG8uaHAgPSBvLm1heEhwOyByZXR1cm4gISFvYmpDYXJkICYmIG9iakNh'
        'cmQudHh0PT09J1RIRSBPUklPTiBJUyBUSFJPVUdIJzsgfSwgOTAwMCwgdHJ1ZSk7CiAgci50aHJv'
        'dWdoQ2FyZCA9IHQ+PTA7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTUxIERpZSBSdWVja2Vy'
        'b2JlcnVuZycsICdtPTUxJywgYAogIGNvbnN0IHIgPSB7fTsKICBzY29yZSA9IDEwMDA7CiAgRlMu'
        'c3RlcCgzMDApOwogIGNvbnN0IHMgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nUzEnKTsKICBy'
        'LmFybWVkQXJjYWRpYSA9ICEhcyAmJiBzLnR5cGU9PT0nc3RhdGlvbicgJiYgcy5hcm1lZCAmJiAh'
        'IXMuc3VicyAmJiBzLnN1YnMuc29tZSh4PT54LmlkPT09J3dlYXBvbnMnKTsKICByLm5vRW5naW5l'
        'c05vTmF2aWdhdGlvbiA9ICEhcyAmJiAhcy5zdWJzLnNvbWUoeD0+eC5pZD09PSdlbmdpbmVzJyB8'
        'fCB4LmlkPT09J25hdmlnYXRpb24nKTsKICAvLyBIZXIgZ3VucyBmaXJlLgogIEZTLmtpbGxTbWFs'
        'bCgpOyBlQnVsbGV0cy5sZW5ndGggPSAwOwogIGxldCBzaG90cyA9IDA7CiAgZm9yKGxldCBpPTA7'
        'aTw0MDA7aSsrKXsgRlMua2lsbFNtYWxsKCk7IGNvbnN0IG4wID0gZUJ1bGxldHMubGVuZ3RoOyBG'
        'Uy5zdGVwKDEpOyBzaG90cyArPSBNYXRoLm1heCgwLCBlQnVsbGV0cy5sZW5ndGgtbjApOyB9CiAg'
        'ci5ndW5zRmlyZSA9IHNob3RzID4gMDsKICBkYW1hZ2VFbmVteShzLCBzLm1heEhwKjUsIHMueCwg'
        'cy55LCB0cnVlLCAnYm9sdCcpOyBGUy5zdGVwKDMpOwogIHIuY2Fubm90QmVEZXN0cm95ZWQgPSBl'
        'bmVtaWVzLmluY2x1ZGVzKHMpICYmIHMucm9sbFQ9PW51bGwgJiYgcy5ocD4wOwogIHIubm9FbHlz'
        'aXVtWWV0ID0gIWFsbGllcy5zb21lKGE9PmEudWlkPT09J1QxJyk7CiAgZm9yKGNvbnN0IHggb2Yg'
        'cy5zdWJzKSBpZih4LmlkPT09J3dlYXBvbnMnKXsgeC5kZWFkID0gdHJ1ZTsgeC5ocCA9IDA7IH0K'
        'ICBGUy5zdGVwKDMpOwogIHIuY292ZXJUaGVFbHlzaXVtID0gbWlzc2lvbk9iaj09PSdDT1ZFUiBU'
        'SEUgRUxZU0lVTSc7CiAgLy8gR3VucyBvdXQ6IHNoZSBmYWxscyBzaWxlbnQuCiAgc2hvdHMgPSAw'
        'OwogIGZvcihsZXQgaT0wO2k8MzAwO2krKyl7IEZTLmtpbGxTbWFsbCgpOyBjb25zdCBuMCA9IGVC'
        'dWxsZXRzLmxlbmd0aDsgRlMuc3RlcCgxKTsgc2hvdHMgKz0gTWF0aC5tYXgoMCwgZUJ1bGxldHMu'
        'bGVuZ3RoLW4wKTsgfQogIHIuc2lsZW50V2l0aG91dEd1bnMgPSBzaG90cz09PTA7CiAgbGV0IGVs'
        'ID0gbnVsbDsKICBGUy51bnRpbCgoKT0+eyBlbCA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J1Qx'
        'Jyk7IHJldHVybiAhIWVsOyB9LCAzMDAwLCB0cnVlKTsKICBlbC5ocCA9IGVsLm1heEhwID0gMWU3'
        'OwogIGNvbnN0IGhvbGQgPSBGUy51bnRpbCgoKT0+eyBlbC5ocCA9IGVsLm1heEhwOyByZXR1cm4g'
        'ZWwuaG9sZFQhPW51bGw7IH0sIDkwMDAsIHRydWUpOwogIEZTLnN0ZXAoNDAwKTsKICByLmJvYXJk'
        'aW5nVGFrZXNUaW1lID0gaG9sZD49MCAmJiAhcy5jYXB0dXJlZDsKICBjb25zdCBnb3QgPSBGUy51'
        'bnRpbCgoKT0+eyBpZihhbGxpZXMuaW5jbHVkZXMoZWwpKSBlbC5ocCA9IGVsLm1heEhwOyByZXR1'
        'cm4gISFFVl9ET0NLWydUMSddOyB9LCAzMDAwLCB0cnVlKTsKICBGUy5zdGVwKDMpOwogIHIudGFr'
        'ZW5BbmRTdGF5cyA9IGdvdD49MCAmJiBzLmNhcHR1cmVkPT09dHJ1ZSAmJiBlbmVtaWVzLmluY2x1'
        'ZGVzKHMpICYmICEocy53YXJwT3V0PjApICYmIHMuc2NlbmVyeT09PXRydWU7CiAgci5jb21wbGV0'
        'ZUNhcmQgPSAhIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nQVJDQURJQSBSRVRBS0VOJzsKICBj'
        'b25zdCB3ID0gRlMudW50aWwoKCk9PndhdmVPdmVyLCA2MDAwLCB0cnVlKTsKICByLndhdmVFbmRz'
        'ID0gdz49MDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNTEgYm90aCBFbHlzaXVtcyBsb3N0'
        'OiBmYWlsZWQnLCAnbT01MScsIGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCgzMDApOwogIGNv'
        'bnN0IHMgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nUzEnKTsKICBmb3IoY29uc3QgeCBvZiBz'
        'LnN1YnMpIGlmKHguaWQ9PT0nd2VhcG9ucycpeyB4LmRlYWQgPSB0cnVlOyB4LmhwID0gMDsgfQog'
        'IGxldCBlbCA9IG51bGw7CiAgRlMudW50aWwoKCk9PnsgZWwgPSBhbGxpZXMuZmluZChhPT5hLnVp'
        'ZD09PSdUMScpOyByZXR1cm4gISFlbDsgfSwgMzAwMCwgdHJ1ZSk7CiAgZWwuaHAgPSAwOwogIGxl'
        'dCBlMiA9IG51bGw7CiAgRlMudW50aWwoKCk9PnsgZTIgPSBhbGxpZXMuZmluZChhPT5hLnVpZD09'
        'PSdUMicpOyByZXR1cm4gISFlMjsgfSwgMzAwMCwgdHJ1ZSk7CiAgci5zZWNvbmRDb21lcyA9ICEh'
        'ZTI7CiAgZTIuaHAgPSAwOwogIGNvbnN0IGYgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9i'
        'akNhcmQudG9uZT09PSdmYWlsJywgMTUwMCwgZmFsc2UpOwogIHIuZmFpbENhcmQgPSBmPj0wICYm'
        'IG9iakNhcmQudHh0PT09J0JPVEggRUxZU0lVTVMgTE9TVCc7CiAgci5udGZLZWVwc0hlciA9IGVu'
        'ZW1pZXMuaW5jbHVkZXMocykgJiYgcy5zY2VuZXJ5PT09dHJ1ZSAmJiAhcy5jYXB0dXJlZDsKICBj'
        'b25zdCB3ID0gRlMudW50aWwoKCk9PndhdmVPdmVyLCA2MDAwLCB0cnVlLCB0cnVlKTsKICByLndh'
        'dmVFbmRzID0gdz49MDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNTIgRGFzIEFydGlsbGVy'
        'aWVmZXVlcicsICdtPTUyJywgYAogIGNvbnN0IHIgPSB7fTsKICB0aWNrZXRzLmNydWlzZXIgPSAx'
        'OwogIEZTLnN0ZXAoNDAwKTsKICBjb25zdCBtcyA9IGFsbGllcy5maWx0ZXIoYT0+YS51aWQ9PT0n'
        'TTEnIHx8IGEudWlkPT09J00yJyk7CiAgci50d29Nam9sbmlycyA9IG1zLmxlbmd0aD09PTIgJiYg'
        'bXMuZXZlcnkobT0+bS5pbWc9PT0nc2dtam9sbmlyJyAmJiBtLnBsYXRmb3JtICYmICFtLnN1YnMg'
        'JiYgbS5iZWFtcyAmJiBtLmJlYW1zLnNvbWUoYj0+Yi5sYXJnZSkpOwogIGNvbnN0IG0xID0gbXMu'
        'ZmluZChtPT5tLnVpZD09PSdNMScpLCBtMiA9IG1zLmZpbmQobT0+bS51aWQ9PT0nTTInKTsKICBy'
        'LmluUGxhY2UgPSAhIW0xICYmICEhbTIgJiYgTWF0aC5hYnMobTEueC03MCk8MSAmJiBNYXRoLmFi'
        'cyhtMS55LTE0MCk8MSAmJiBNYXRoLmFicyhtMi55LTM2MCk8MTsKICByLmRlaW1vc0F0VGhlQm90'
        'dG9tID0gYWxsaWVzLnNvbWUoYT0+YS51aWQ9PT0nQTEnICYmIGEuaW1nPT09J2NvZGVpbW9zJyAm'
        'JiBNYXRoLmFicyhhLnktNDQwKTwxKTsKICByLnN1cHBvcnRTdGlsbENhbGxhYmxlID0gYWxseVJl'
        'YWR5KCk7CiAgY29uc3QgX3YxID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyk7CiAgci5z'
        'aG9ydGVyRGVhZGxpbmUgPSAhIV92MSAmJiBfdjEuZmxlZVQ+MCAmJiBfdjEuZmxlZVQgPD0gMzAq'
        'VElDS19IWjsKICAvLyBUaGV5IHRha2UgdHVybnM6IG5ldmVyIGJvdGggZWFybHkgaW4gdGhlaXIg'
        'Y2hhcmdlIHRvZ2V0aGVyLgogIGxldCB0b2dldGhlciA9IDAsIGNoYXJnZWQgPSB7TTE6MCwgTTI6'
        'MH07CiAgZm9yKGxldCBpPTA7aTw0MDAwO2krPTEwKXsgRlMua2lsbFNtYWxsKCk7IGZvcihjb25z'
        'dCBlIG9mIGVuZW1pZXMpIGlmKGUuZmxlZVQ+MCkgZS5mbGVlVCA9IDFlNjsKICAgIEZTLnN0ZXAo'
        'MTApOwogICAgY29uc3QgZWFybHkgPSBtcy5maWx0ZXIobT0+bS5iZWFtcy5zb21lKGI9PmIuc3Rh'
        'dGU9PT0nY2hhcmdpbmcnICYmIChiLmNoYXJnZU1heCAtIGIudGltZXIpIDwgYi5jaGFyZ2VNYXgq'
        'MC40KSk7CiAgICBpZihlYXJseS5sZW5ndGg9PT0yKSB0b2dldGhlcisrOwogICAgZm9yKGNvbnN0'
        'IG0gb2YgbXMpIGlmKG0uYmVhbXMuc29tZShiPT5iLnN0YXRlPT09J2ZpcmluZycpKSBjaGFyZ2Vk'
        'W20udWlkXSsrOyB9CiAgci50YWtlVHVybnMgPSB0b2dldGhlcj09PTAgJiYgY2hhcmdlZC5NMT4w'
        'ICYmIGNoYXJnZWQuTTI+MDsKICAvLyBUd28gbGFuZXMsIG5ldmVyIG1vcmUgdGhhbiB0d28gTlRG'
        'IGNhcGl0YWwgc2hpcHMgYXQgb25jZS4KICBsZXQgbW9zdCA9IDA7IGNvbnN0IHNlZW4gPSB7fTsK'
        'ICBGUy51bnRpbCgoKT0+eyBjb25zdCBjYXBzID0gZW5lbWllcy5maWx0ZXIoZT0+L15WLy50ZXN0'
        'KGUudWlkfHwnJykgJiYgIShlLndhcnA+MCkpOwogICAgbW9zdCA9IE1hdGgubWF4KG1vc3QsIGNh'
        'cHMubGVuZ3RoKTsgZm9yKGNvbnN0IGUgb2YgY2Fwcykgc2VlbltlLnVpZF0gPSBlOwogICAgZm9y'
        'KGNvbnN0IGUgb2YgY2FwcykgaWYoZS53YXJwPD0wICYmIGUueCA8IFctNjApeyBlLmhwID0gMDsg'
        'fQogICAgcmV0dXJuIFsnVjEnLCdWMicsJ1YzJywnVjQnLCdWNScsJ1Y2J10uZXZlcnkoaz0+RVZf'
        'U0VFTltrXSkgJiYgIWJ5SWQoJ1Y1JykubGVuZ3RoICYmICFieUlkKCdWNicpLmxlbmd0aDsgfSwg'
        'MjAwMDAsIHRydWUpOwogIHIuYWxsU2l4Q29tZSA9IHdhdmU9PT01MiAmJiBbJ1YxJywnVjInLCdW'
        'MycsJ1Y0JywnVjUnLCdWNiddLmV2ZXJ5KGs9PkVWX1NFRU5ba10pOwogIHIubmV2ZXJNb3JlVGhh'
        'blR3byA9IG1vc3Q8PTI7CiAgci5jb21wbGV0ZUNhcmQgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJk'
        'ICYmIG9iakNhcmQudHh0PT09J05URiBCQVRUTEUgR1JPVVAgREVTVFJPWUVEJywgMzAwLCBmYWxz'
        'ZSkgPj0gMDsKICAvLyBObyBqdW1wIGRyaXZlOiB0aGUgTWpvbG5pcnMgc3RheSB1bnRpbCB0aGUg'
        'ZmllbGQgZ29lcyBkYXJrLgogIEZTLnVudGlsKCgpPT53YXZlT3ZlciwgNjAwMCwgdHJ1ZSwgdHJ1'
        'ZSk7CiAgRlMuc3RlcCg2MCk7CiAgci5tam9sbmlyc1N0YXkgPSBhbGxpZXMuaW5jbHVkZXMobTEp'
        'ICYmICEobTEud2FycE91dD4wKSAmJiBhbGxpZXMuaW5jbHVkZXMobTIpOwogIHJldHVybiByO2Ap'
        'OwoKc2NlbmFyaW8oJ001MyBEZXIgR2VnZW5hbmdyaWZmJywgJ209NTMnLCBgCiAgY29uc3QgciA9'
        'IHt9OwogIHRpY2tldHMuY3J1aXNlciA9IDE7CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IGExID0g'
        'YWxsaWVzLmZpbmQoYT0+YS51aWQ9PT0nQTEnKSwgYTIgPSBhbGxpZXMuZmluZChhPT5hLnVpZD09'
        'PSdBMicpOwogIHIuZmxlZXRQbGFjZWQgPSAhIWExICYmICEhYTIgJiYgTWF0aC5hYnMoYTEueS0x'
        'NzApPDYwICYmIE1hdGguYWJzKGEyLnktMzkwKTw2MDsKICByLm5vQ2FsbFdoaWxlQm90aFN0YW5k'
        'ID0gIWFsbHlSZWFkeSgpOwogIHIubm9FbmVteURlc3Ryb3llcnNZZXQgPSAhZW5lbWllcy5zb21l'
        'KGU9PmUudWlkPT09J1YxJ3x8ZS51aWQ9PT0nVjInKTsKICBGUy51bnRpbCgoKT0+ZW5lbWllcy5z'
        'b21lKGU9PmUudWlkPT09J1YxJykgJiYgZW5lbWllcy5zb21lKGU9PmUudWlkPT09J1YyJyksIDIw'
        'MDAsIHRydWUpOwogIHIudGhleUp1bXBJbiA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdWMScg'
        'JiYgZS5pbWc9PT0nbnRmZGVoZWNhdGUnKSAmJiBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nVjIn'
        'ICYmIGUuaW1nPT09J250ZmRlb3Jpb24nKTsKICBGUy5zdGVwKDIpOwogIHIubmV3T2JqZWN0aXZl'
        'ID0gbWlzc2lvbk9iaj09PSdERVNUUk9ZIFRIRSBIRUNBVEUgQU5EIFRIRSBPUklPTic7CiAgY29u'
        'c3QgdjEgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nVjEnKTsgdjEuaHAgPSAwOwogIEZTLnN0'
        'ZXAoNDAwKTsKICByLm5vdERvbmVXaXRoT25lID0gIShvYmpDYXJkICYmIG9iakNhcmQudHh0PT09'
        'J0NPVU5URVJBVFRBQ0sgQlJPS0VOJyk7CiAgLy8gT25lIG9mIG91cnMgbG9zdDogbm93IHRoZSBj'
        'YWxsIGlzIGZyZWUuCiAgYTIuaHAgPSAwOyBGUy5zdGVwKDMwMCk7CiAgci5jYWxsRnJlZUFmdGVy'
        'QUxvc3MgPSBhbGx5UmVhZHkoKTsKICBjb25zdCB2MiA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09'
        'PSdWMicpOyBpZih2MikgdjIuaHAgPSAwOwogIHIuY29tcGxldGVDYXJkID0gRlMudW50aWwoKCk9'
        'PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdDT1VOVEVSQVRUQUNLIEJST0tFTicsIDMwMDAs'
        'IGZhbHNlKSA+PSAwOwogIC8vIE91ciBzaGlwcyBqdW1wIG91dCBhdCB0aGUgZW5kIG9mIHRoZSB3'
        'YXZlOiB0aGF0IGlzIG5vdCBhIGxvc3MuCiAgY29uc3Qgc2FpZCA9IG5ldyBTZXQoKTsKICBGUy51'
        'bnRpbCgoKT0+eyBmb3IoY29uc3QgbiBvZiBOT1RJQ0VTKSBzYWlkLmFkZChuLnR4dCk7IHJldHVy'
        'biB3YXZlPT09NTQ7IH0sIDkwMDAsIHRydWUsIHRydWUpOwogIHIuanVtcElzTm9Mb3NzID0gIXNh'
        'aWQuaGFzKCdHVEQgT1JJT04gTE9TVCcpOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001NCBE'
        'aWUgRXZha3VpZXJ1bmcnLCAnbT01NCcsIGAKICBjb25zdCByID0ge307CiAgbGV0IHQxID0gbnVs'
        'bDsKICBGUy51bnRpbCgoKT0+eyB0MSA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J1QxJyk7IHJl'
        'dHVybiAhIXQxOyB9LCAxMDAwLCBmYWxzZSk7CiAgci5sZWF2ZXNUaGVTdGF0aW9uID0gISF0MSAm'
        'JiBNYXRoLmFicyh0MS54LTU2MCkgPCAxNSAmJiB0MS5jcm9zc2luZyA8IDAgJiYgdDEuZmxpcD09'
        'PW5lZWRzRmxpcCh0MS5pbWcsIHRydWUpOwogIGNvbnN0IHgwID0gdDEueDsgRlMuc3RlcCgxMDAp'
        'OwogIHIuZmxpZXNMZWZ0ID0gdDEueCA8IHgwIC0gMzA7CiAgLy8gS2VlcCB0aGVtIGFsaXZlOyB0'
        'aGV5IGZseSBvdXQgdG8gdGhlIGxlZnQuCiAgY29uc3Qga2VlcCA9ICgpPT57IGZvcihjb25zdCBh'
        'IG9mIGFsbGllcykgaWYoL15ULy50ZXN0KGEudWlkfHwnJykpIGEuaHAgPSBhLm1heEhwID0gMWU3'
        'OyB9OwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+eyBrZWVwKCk7IHJldHVybiBwcm90U2F2ZWQ+'
        'PTE7IH0sIDMwMDAsIHRydWUpOwogIHIuZmlyc3RPdXQgPSB0Pj0wOwogIEZTLnN0ZXAoNSk7CiAg'
        'ci5ub3RpY2VGb3JJdCA9IE5PVElDRVMuc29tZShuPT5uLnR4dD09PSdGSVJTVCBFTFlTSVVNIElT'
        'IE9VVCcpOwogIC8vIFRocmVlIG91dCB3aGlsZSB0aGUgZm91cnRoIGlzIHN0aWxsIGZseWluZzog'
        'bm90IHlldCBjb21wbGV0ZS4KICBGUy51bnRpbCgoKT0+eyBrZWVwKCk7IHJldHVybiBwcm90U2F2'
        'ZWQ+PTM7IH0sIDkwMDAsIHRydWUpOwogIGNvbnN0IHQ0ID0gYWxsaWVzLmZpbmQoYT0+YS51aWQ9'
        'PT0nVDQnKTsKICByLm5vdENvbXBsZXRlV2hpbGVPbmVGbGllcyA9ICEhdDQgJiYgIShvYmpDYXJk'
        'ICYmIG9iakNhcmQudHh0PT09J0VWQUNVQVRJT04gQ09NUExFVEUnKTsKICBjb25zdCBjID0gRlMu'
        'dW50aWwoKCk9Pnsga2VlcCgpOyByZXR1cm4gISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J0VW'
        'QUNVQVRJT04gQ09NUExFVEUnOyB9LCA5MDAwLCB0cnVlKTsKICByLnRocmVlT3V0Q29tcGxldGUg'
        'PSBjPj0wICYmIHByb3RTYXZlZD49MzsKICBjb25zdCB3ID0gRlMudW50aWwoKCk9Pnsga2VlcCgp'
        'OyByZXR1cm4gd2F2ZU92ZXI7IH0sIDkwMDAsIHRydWUsIHRydWUpOwogIHIud2F2ZUVuZHMgPSB3'
        'Pj0wOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001NCB0d28gbG9zdDogZmFpbGVkJywgJ209'
        'NTQnLCBgCiAgY29uc3QgciA9IHt9OwogIGxldCBuID0gMDsKICBjb25zdCBmID0gRlMudW50aWwo'
        'KCk9PnsgZm9yKGNvbnN0IGEgb2YgYWxsaWVzKSBpZigvXlRbMTJdJC8udGVzdChhLnVpZHx8Jycp'
        'KSBhLmhwID0gMDsKICAgIHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC50b25lPT09J2ZhaWwn'
        'OyB9LCAzMDAwLCB0cnVlKTsKICByLmZhaWxDYXJkID0gZj49MCAmJiBvYmpDYXJkLnR4dD09PSdU'
        'T08gTUFOWSBFTFlTSVVNUyBMT1NUJzsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdCZWFtcyBy'
        'dW4gdW5kZXIgdGhlIGh1bGxzJywgJ209NDInLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAo'
        'MzAwKTsKICBjb25zdCBzaG9vdGVyID0gYWxsaWVzLmNvbmNhdChlbmVtaWVzKS5maW5kKG89Pm8u'
        'YmVhbXMgJiYgby5iZWFtcy5sZW5ndGgpOwogIGNvbnN0IGIgPSBzaG9vdGVyLmJlYW1zWzBdOwog'
        'IGIuc3RhdGUgPSAnZmlyaW5nJzsgYi50aW1lciA9IDFlNjsgYi5hbmdsZSA9IDA7IGIuY3VyQW5n'
        'bGUgPSAwOwogIGNvbnN0IG9yZGVyID0gW107CiAgY29uc3QgX3IgPSBkcmF3QmVhbVJheXMsIF9z'
        'ID0gZHJhd1NoaXA7CiAgZHJhd0JlYW1SYXlzID0gZnVuY3Rpb24oZSwgb3duKXsgaWYoZS5iZWFt'
        'cyAmJiBlLmJlYW1zLnNvbWUoeD0+eC5zdGF0ZT09PSdmaXJpbmcnKSkgb3JkZXIucHVzaChvd24g'
        'PyAnb3duJyA6ICdyYXknKTsgcmV0dXJuIF9yLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07CiAg'
        'ZHJhd1NoaXAgPSBmdW5jdGlvbihpbWcpeyBvcmRlci5wdXNoKGltZz09PXNob290ZXIuaW1nID8g'
        'J3Nob290ZXInIDogJ3NoaXAnKTsgcmV0dXJuIF9zLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07'
        'CiAgdHJ5IHsgZHJhdygpOyB9IGZpbmFsbHkgeyBkcmF3QmVhbVJheXMgPSBfcjsgZHJhd1NoaXAg'
        'PSBfczsgfQogIGNvbnN0IGxhc3RSYXkgPSBvcmRlci5sYXN0SW5kZXhPZigncmF5JyksIGZpcnN0'
        'U2hpcCA9IE1hdGgubWluKC4uLlsnc2hpcCcsJ3Nob290ZXInXS5tYXAoaz0+b3JkZXIuaW5kZXhP'
        'ZihrKSkuZmlsdGVyKGk9Pmk+PTApKTsKICByLnJheURyYXduID0gbGFzdFJheT49MDsKICAvLyBV'
        'bmRlciB0aGUgc2hpcHMgaXQgaGl0cy4uLgogIHIudW5kZXJUaGVUYXJnZXRzID0gbGFzdFJheT49'
        'MCAmJiBmaXJzdFNoaXA+bGFzdFJheTsKICAvLyAuLi5idXQgb24gdG9wIG9mIHRoZSBzaGlwIHRo'
        'YXQgZmlyZXMgaXQuCiAgY29uc3Qgc2ggPSBvcmRlci5pbmRleE9mKCdzaG9vdGVyJyksIG93biA9'
        'IG9yZGVyLmluZGV4T2YoJ293bicpOwogIHIub25Ub3BPZlRoZVNob290ZXIgPSBzaD49MCAmJiBv'
        'd24+c2g7CiAgci5vd25TdHJldGNoU2hvcnQgPSBvd25IdWxsUnVuKHNob290ZXIsIHNob290ZXIu'
        'eCwgc2hvb3Rlci55LCAwKSA+IDAgJiYgb3duSHVsbFJ1bihzaG9vdGVyLCBzaG9vdGVyLngsIHNo'
        'b290ZXIueSwgMCkgPCAxMDAwOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ0tub3Nzb3Mgc2Nl'
        'bmU6IHNhbWUgc2t5IHdpdGhpbiBhIHJ1bicsICdtPTU1JywgYAogIGNvbnN0IHIgPSB7fTsKICBG'
        'Uy5zdGVwKDUwKTsKICAvLyBNYWtlIHN1cmUgdGhlcmUgaXMgc29tZXRoaW5nIGluIHRoZSBza3kg'
        'dG8gY29tcGFyZSwgdGhlbiB3cml0ZSB0aGUKICAvLyBzY2VuZSBkb3duIGFnYWluIGZyb20gdGhh'
        'dC4KICAvLyBUaGUgaGFybmVzcyBoYXMgbm8gcGxhbmV0IHBpY3R1cmVzLCBzbyB0d28gc3RhbmQt'
        'aW5zLgogIGJvZGllcyA9IFt7a2V5Oid0ZXN0cGxhbmV0Jywga2luZDoncGxhbmV0JywgbWV0YTp7'
        'cjowLGN4OjAuNSxjeTowLjV9LCB3OjIyMCwgeDozMTAsIHk6MTkwLCBzcGQ6MC4wNX0sCiAgICAg'
        'ICAgICAgIHtrZXk6J3Rlc3RzdW4nLCBraW5kOidzdW4nLCBtZXRhOntyOjAsY3g6MC41LGN5OjAu'
        'NX0sIHc6MTIwLCB4OjYyMCwgeToxMjAsIHNwZDowLjA0fV07CiAgZGVsZXRlIFNDRU5FUy5rbm9z'
        'c29zOyB1c2VTY2VuZSgna25vc3NvcycpOwogIGNvbnN0IG5lYiA9IG5lYkN1ciwga2V5cyA9IGJv'
        'ZGllcy5tYXAoYj0+Yi5rZXkpLmpvaW4oJywnKSwgcG9zID0gYm9kaWVzLm1hcChiPT5NYXRoLnJv'
        'dW5kKGIueCkrJy8nK01hdGgucm91bmQoYi55KSkuam9pbignLCcpLCBsYSA9IGxpZ2h0QW5nOwog'
        'IHIucG9ydGFsVGhlcmUgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nUDEnICYmIGUuaW1nPT09'
        'J2lua25vc3NvczQ1ZGVnJyAmJiBlLmludnVsbiAmJiBlLnNjZW5lcnkpOwogIC8vIFRvIDU2OiBh'
        'IGRpZmZlcmVudCBwbGFjZSwgYSBmcmVzaCByb2xsLgogIHN0YXJ0TmViRmFkZSgpOyBmb3IobGV0'
        'IGk9MDtpPDIwMDtpKyspIHRpY2tOZWJ1bGEoKTsKICB3YXZlT3ZlciA9IGZhbHNlOyBuZXh0V2F2'
        'ZSgpOyBGUy5zdGVwKDUpOwogIC8vIE9uIHRvIDU4IHRocm91Z2ggNTcsIHdpdGggdGhlIGJhY2tk'
        'cm9wIGZhZGluZyBvdmVyIGVhY2ggdGltZS4KICBzdGFydE5lYkZhZGUoKTsgRlMuc3RlcCg1KTsg'
        'bmV4dFdhdmUoKTsgRlMuc3RlcCg1KTsKICBzdGFydE5lYkZhZGUoKTsgRlMuc3RlcCg1KTsgbmV4'
        'dFdhdmUoKTsKICByLmF0VGhlR2F0ZSA9IHdhdmU9PT01ODsKICBjb25zdCBwbGFjZXNOb3cgPSBi'
        'b2RpZXMubWFwKGI9Pk1hdGgucm91bmQoYi54KSsnLycrTWF0aC5yb3VuZChiLnkpKS5qb2luKCcs'
        'Jyk7CiAgZm9yKGxldCBpPTA7aTwyMDA7aSsrKSB0aWNrTmVidWxhKCk7CiAgci5zYW1lQmFja2Ry'
        'b3AgPSBuZWJDdXI9PT1uZWI7CiAgci5zYW1lQm9kaWVzID0gYm9kaWVzLm1hcChiPT5iLmtleSku'
        'am9pbignLCcpPT09a2V5czsKICByLnNhbWVQbGFjZXMgPSBwbGFjZXNOb3c9PT1wb3M7CiAgci5z'
        'YW1lTGlnaHQgPSBsaWdodEFuZz09PWxhOwogIC8vIEEgbmV3IHJ1biByb2xscyBhbmV3OiB0aGUg'
        'Ym9vayBpcyBlbXB0eS4KICBsYXVuY2hHYW1lKCk7CiAgci5uZXdSdW5Gb3JnZXRzID0gKFNDUklQ'
        'VF9PTkU9PT01NSkgPyAhIVNDRU5FUy5rbm9zc29zICYmIE9iamVjdC5rZXlzKFNDRU5FUykubGVu'
        'Z3RoPT09MSA6IE9iamVjdC5rZXlzKFNDRU5FUykubGVuZ3RoPT09MDsKICByZXR1cm4gcjtgKTsK'
        'CnNjZW5hcmlvKCdNNTUgRGVyIEFuZmx1ZycsICdtPTU1JywgYAogIGNvbnN0IHIgPSB7fTsKICBs'
        'ZXQgayA9IG51bGw7CiAgRlMudW50aWwoKCk9PnsgayA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09'
        'PSdLMScgJiYgIShlLndhcnA+MCkpOyByZXR1cm4gISFrOyB9LCAyMDAwLCB0cnVlKTsKICByLmNy'
        'dWlzZXJGcm9tVGhlTGVmdCA9ICEhayAmJiBrLnggPCAxMDAgJiYgay5lc2NhcGluZz4wICYmIGsu'
        'ZXNjV2FycDsKICBrLmhwID0gay5tYXhIcCA9IDFlNzsKICBjb25zdCBmID0gRlMudW50aWwoKCk9'
        'Pnsgay5ocCA9IGsubWF4SHA7IHJldHVybiBrLndhcnBPdXQ+MDsgfSwgNjAwMCwgdHJ1ZSk7CiAg'
        'ci5qdW1wc0F0VGhlUG9ydGFsID0gZj49MCAmJiBrLnggPj0gUE9SVEFMX1ggJiYgay54IDwgVyAm'
        'JiBrLnBvcnRhbFdhcnA9PT10cnVlOwogIEZTLnN0ZXAoNSk7CiAgci5mYWlsQ2FyZCA9ICEhb2Jq'
        'Q2FyZCAmJiBvYmpDYXJkLnR4dD09PSdBIENSVUlTRVIgUkVBQ0hFRCBUSEUgUE9SVEFMJzsKICBy'
        'ZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNTUgYWxsIHN0b3BwZWQnLCAnbT01NScsIGAKICBjb25z'
        'dCByID0ge307CiAgbGV0IGsgPSBudWxsOwogIEZTLnVudGlsKCgpPT57IGsgPSBlbmVtaWVzLmZp'
        'bmQoZT0+ZS51aWQ9PT0nSzEnICYmICEoZS53YXJwPjApKTsgcmV0dXJuICEhazsgfSwgMjAwMCwg'
        'dHJ1ZSk7CiAgZm9yKGNvbnN0IHMgb2Ygay5zdWJzKSBpZihzLmlkPT09J2VuZ2luZXMnKXsgcy5k'
        'ZWFkID0gdHJ1ZTsgcy5ocCA9IDA7IH0KICBjb25zdCB4MCA9IGsueDsgRlMuc3RlcCgyMDApOwog'
        'IHIuZW5naW5lc1N0b3BIZXIgPSBNYXRoLmFicyhrLngteDApIDwgMC4wMTsKICBjb25zdCBzZWVu'
        'ID0ge307CiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT57IGZvcihjb25zdCBlIG9mIGVuZW1pZXMp'
        'IGlmKC9eSy8udGVzdChlLnVpZHx8JycpICYmICEoZS53YXJwPjApKXsgc2VlbltlLnVpZF09MTsg'
        'ZS5ocCA9IDA7IH0KICAgIHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nQUxMIENS'
        'VUlTRVJTIFNUT1BQRUQnOyB9LCAxMjAwMCwgdHJ1ZSk7CiAgci5jb21wbGV0ZUNhcmQgPSB0Pj0w'
        'ICYmIE9iamVjdC5rZXlzKHNlZW4pLmxlbmd0aD09PTQ7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJp'
        'bygnTTU2IERpZSBWZXJyYWV0ZXInLCAnbT01NicsIGAKICBjb25zdCByID0ge307CiAgRlMuc3Rl'
        'cCgzMDApOwogIGNvbnN0IGExID0gYWxsaWVzLmZpbmQoYT0+YS51aWQ9PT0nQTEnKTsKICByLmFs'
        'bGllZExldmlhdGhhbiA9ICEhYTEgJiYgYTEuaW1nPT09J2NybGV2aWF0aGFuJzsKICByLmRlaW1v'
        'c1RvbyA9IGFsbGllcy5zb21lKGE9PmEudWlkPT09J0EyJyAmJiBhLmltZz09PSdjb2RlaW1vcycp'
        'OwogIEZTLnVudGlsKCgpPT4hYWxsaWVzLmluY2x1ZGVzKGExKSwgMzAwMCwgdHJ1ZSk7CiAgY29u'
        'c3QgdCA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdBMScpOwogIHIuZ29lc092ZXIgPSAhIXQg'
        'JiYgdC5zaWRlPT09J2VuZW15JyAmJiB0LmltZz09PSdudGZjcmxldmlhdGhhbic7CiAgRlMuc3Rl'
        'cCgzKTsKICByLm5ld09iamVjdGl2ZSA9IG1pc3Npb25PYmo9PT0nREVTVFJPWSBUSEUgTEVWSUFU'
        'SEFOJzsKICByLm1vcmVDb21pbmcgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nRTInKSB8fCBz'
        'cGF3blEuc29tZShxPT5xLnVpZD09PSdFMicgfHwgcS51aWQ9PT0nQjEnKSB8fCBlbmVtaWVzLnNv'
        'bWUoZT0+ZS51aWQ9PT0nQjEnKTsKICB0LmhwID0gMDsKICByLmNvbXBsZXRlQ2FyZCA9IEZTLnVu'
        'dGlsKCgpPT4hIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nVFJBSVRPUiBERVNUUk9ZRUQnLCAx'
        'NTAwLCBmYWxzZSkgPj0gMDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNTcgRGllIE5hY2ho'
        'dXQnLCAnbT01NycsIGAKICBjb25zdCByID0ge307CiAgY29uc3QgcHJldlNlYyA9IHBsYXllci5z'
        'ZWM7CiAgRlMuc3RlcCgzMDApOwogIHIudXJzYVdpdGhTdGlsZXR0byA9IHBsYXllci5zaGlwPT09'
        'J2JvdXJzYScgJiYgcGxheWVyLnNlYz09PSdzdGlsZXR0byc7CiAgY29uc3QgdXMgPSBbJ0sxJywn'
        'SzInLCdEMSddLm1hcChpZD0+ZW5lbWllcy5maW5kKGU9PmUudWlkPT09aWQpKTsKICByLnRocmVl'
        'SG9sZFRoZVJlYXIgPSB1cy5ldmVyeShCb29sZWFuKTsKICBkYW1hZ2VFbmVteSh1c1swXSwgdXNb'
        'MF0ubWF4SHAqNSwgdXNbMF0ueCwgdXNbMF0ueSwgdHJ1ZSwgJ2JvbHQnKTsgRlMuc3RlcCgyKTsK'
        'ICByLmNhbm5vdEJlRGVzdHJveWVkWWV0ID0gZW5lbWllcy5pbmNsdWRlcyh1c1swXSk7CiAgZm9y'
        'KGNvbnN0IHUgb2YgdXMpIGZvcihjb25zdCBzIG9mIHUuc3VicykgaWYocy5pZD09PSdlbmdpbmVz'
        'J3x8cy5pZD09PSd3ZWFwb25zJyl7IHMuZGVhZCA9IHRydWU7IHMuaHAgPSAwOyB9CiAgY29uc3Qg'
        'YyA9IEZTLnVudGlsKCgpPT4hIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nUkVBUkdVQVJEIERJ'
        'U0FCTEVEJywgMTUwMCwgZmFsc2UpOwogIHIuY29tcGxldGVDYXJkID0gYz49MDsKICByLmxlZnRB'
        'c1dyZWNrcyA9IHVzLmV2ZXJ5KHU9PmVuZW1pZXMuaW5jbHVkZXModSkgJiYgdS5zY2VuZXJ5KTsK'
        'ICBjb25zdCB3ID0gRlMudW50aWwoKCk9PndhdmU9PT01OCwgOTAwMCwgdHJ1ZSwgdHJ1ZSk7CiAg'
        'ci5uZXh0V2F2ZU93blNoaXBCYWNrID0gdz49MCAmJiBwbGF5ZXIuc2hpcCE9PSdib3Vyc2EnICYm'
        'IHBsYXllci5zZWMhPT0nc3RpbGV0dG8nOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001OCBE'
        'YXMgVG9yJywgJ209NTgnLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAoNDAwKTsKICByLnBv'
        'cnRhbFRoZXJlID0gZW5lbWllcy5zb21lKGU9PmUudWlkPT09J1AxJyAmJiBlLmltZz09PSdpbmtu'
        'b3Nzb3M0NWRlZycpOwogIHIuc2VudHJ5TGluZSA9IGVuZW1pZXMuZmlsdGVyKGU9PmUudWlkPT09'
        'J0cxJykubGVuZ3RoPT09NjsKICByLnR3b0NydWlzZXJzID0gZW5lbWllcy5zb21lKGU9PmUudWlk'
        'PT09J0sxJyAmJiBlLmltZz09PSdudGZjcmZlbnJpcycpICYmIGVuZW1pZXMuc29tZShlPT5lLnVp'
        'ZD09PSdLMicgJiYgZS5pbWc9PT0nbnRmY3JhZW9sdXMnKTsKICBmb3IoY29uc3QgZSBvZiBlbmVt'
        'aWVzKSBpZigvXihLfEcpLy50ZXN0KGUudWlkfHwnJykpIGUuaHAgPSAwOwogIHIuY29tcGxldGVD'
        'YXJkID0gRlMudW50aWwoKCk9PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdQT1JUQUwgREVG'
        'RU5DRSBCUk9LRU4nLCAxNTAwLCBmYWxzZSkgPj0gMDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlv'
        'KCdNNTkgRGllIGxldHp0ZSBTcGVycmUnLCAnbT01OScsIGAKICBjb25zdCByID0ge307CiAgRlMu'
        'c3RlcCg1MDApOwogIGNvbnN0IHYxID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyksIHYy'
        'ID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YyJyk7CiAgci50d29EZXN0cm95ZXJzID0gISF2'
        'MSAmJiAhIXYyICYmIHYxLmltZz09PSdudGZkZWhlY2F0ZScgJiYgdjIuaW1nPT09J250ZmRlb3Jp'
        'b24nOwogIHIuaW5Gcm9udE9mVGhlUG9ydGFsID0gZW5lbWllcy5zb21lKGU9PmUudWlkPT09J1Ax'
        'Jyk7CiAgdjEuaHAgPSAwOyBGUy5zdGVwKDMwMCk7CiAgci5ub3RZZXQgPSAhKG9iakNhcmQgJiYg'
        'b2JqQ2FyZC50eHQ9PT0nVEhFIFdBWSBUTyBUSEUgUE9SVEFMIElTIE9QRU4nKTsKICB2Mi5ocCA9'
        'IDA7CiAgci5jb21wbGV0ZUNhcmQgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9iakNhcmQu'
        'dHh0PT09J1RIRSBXQVkgVE8gVEhFIFBPUlRBTCBJUyBPUEVOJywgMzAwMCwgZmFsc2UpID49IDA7'
        'CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTYwIERlciBTcHJ1bmcnLCAnbT02MCcsIGAKICBj'
        'b25zdCByID0ge307CiAgc2NvcmUgPSAzMDAwOwogIGNvbnN0IGVzYzAgPSBpY2VuRXNjYXBlczsK'
        'ICBsZXQgdiA9IG51bGw7CiAgRlMudW50aWwoKCk9PnsgdiA9IGVuZW1pZXMuZmluZChlPT5lLnVp'
        'ZD09PSdWMScgJiYgIShlLndhcnA+MCkpOyByZXR1cm4gISF2OyB9LCAzMDAwLCB0cnVlKTsKICBy'
        'LmljZW5pUnVucyA9ICEhdiAmJiB2LmljZW5pICYmIHYuZXNjYXBpbmc+MDsKICByLm5vdGhpbmdU'
        'b1Nob290T3V0ID0gISF2ICYmICF2LnN1YnMuc29tZShzPT5zLmlkPT09J2VuZ2luZXMnIHx8IHMu'
        'aWQ9PT0nbmF2aWdhdGlvbicpOwogIGRhbWFnZUVuZW15KHYsIHYubWF4SHAqNSwgdi54LCB2Lnks'
        'IHRydWUsICdib2x0Jyk7IEZTLnN0ZXAoMik7CiAgci5jYW5ub3RCZURlc3Ryb3llZCA9IGVuZW1p'
        'ZXMuaW5jbHVkZXModikgJiYgdi5ocD4wOwogIGNvbnN0IGogPSBGUy51bnRpbCgoKT0+di53YXJw'
        'T3V0PjAsIDkwMDAsIHRydWUpOwogIHIudGhyb3VnaFRoZVBvcnRhbCA9IGo+PTAgJiYgdi5wb3J0'
        'YWxXYXJwPT09dHJ1ZSAmJiB2LnggPj0gUE9SVEFMX1g7CiAgRlMudW50aWwoKCk9PiFlbmVtaWVz'
        'LmluY2x1ZGVzKHYpLCAxMDAwLCBmYWxzZSk7CiAgRlMuc3RlcCg1KTsKICByLnNoZUdvdEF3YXkg'
        'PSBpY2VuRXNjYXBlcz09PWVzYzArMSAmJiBOT1RJQ0VTLnNvbWUobj0+bi50eHQ9PT0nVEhFIElD'
        'RU5JIElTIFRIUk9VR0ggVEhFIEtOT1NTT1MnKTsKICBmb3IoY29uc3QgZSBvZiBlbmVtaWVzKSBp'
        'ZigvXihLfEMpLy50ZXN0KGUudWlkfHwnJykpIGUuaHAgPSAwOwogIHIuY29tcGxldGVDYXJkID0g'
        'RlMudW50aWwoKCk9PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdFU0NPUlQgREVTVFJPWUVE'
        'JywgMzAwMCwgZmFsc2UpID49IDA7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnYWxsaWVkIGNy'
        'YWZ0IGhvbGQgZmlyZSB3aXRoIG5vdGhpbmcgdG8gc2hvb3QnLCAnbT00NCcsIGAKICBjb25zdCBy'
        'ID0ge307CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IGZpID0gbWtBbGx5U21hbGwoJ2ZpZ2h0ZXIn'
        'LCAndGVycmFuJywgJ2ZpaGVyYycsIEgqMC41KTsKICBjb25zdCBibyA9IG1rQWxseVNtYWxsKCdi'
        'b21iZXInLCAndGVycmFuJywgJ2JvYXJ0ZW1pcycsIEgqMC42KTsKICBmaS53YXJwID0gMDsgYm8u'
        'd2FycCA9IDA7IGFsbGllcy5wdXNoKGZpLCBibyk7CiAgLy8gT25seSB0aGluZ3MgYW4gZXNjb3J0'
        'IGhhcyBubyBidXNpbmVzcyBzaG9vdGluZyBhdDogbm90aGluZywgYW5kIGFuCiAgLy8gaW52dWxu'
        'ZXJhYmxlIHN0YXRpb24gYXQgdGhlIHJpZ2h0IGVkZ2UuCiAgY29uc3Qga2VlcCA9IGVuZW1pZXM7'
        'IGVuZW1pZXMgPSBbXTsKICBjb25zdCBzdCA9IG1rRW5lbXkoJ2NyX250ZicsICdudGZjcmFlb2x1'
        'cycsIEgqMC41KTsgc3QueCA9IFctNDA7IHN0LndhcnAgPSAwOwogIHN0LmludnVsbiA9IHRydWU7'
        'IHN0LnNjZW5lcnkgPSB0cnVlOwogIGNvbnN0IHNob3RzID0gKCk9PnBCdWxsZXRzLmZpbHRlcihi'
        'PT5iLmFsbHkpLmxlbmd0aDsKICBsZXQgbiA9IDA7CiAgZm9yKGNvbnN0IGxpc3Qgb2YgW1tdLCBb'
        'c3RdXSl7CiAgICBlbmVtaWVzID0gbGlzdDsKICAgIGZvcihjb25zdCBhIG9mIFtmaSwgYm9dKXsK'
        'ICAgICAgYS5oZWFkID0gMDsgYS54ID0gVyowLjQ7CiAgICAgIGZvcihsZXQgaz0wO2s8NDA7aysr'
        'KXsKICAgICAgICBjb25zdCBiMCA9IHNob3RzKCk7CiAgICAgICAgYS5mVCA9IDA7IHNtYWxsRmly'
        'ZShhLCBzbWFsbFRhcmdldChhKSk7CiAgICAgICAgaWYoYS5zZWNUKSBmb3IobGV0IGk9MDtpPGEu'
        'c2VjVC5sZW5ndGg7aSsrKSBhLnNlY1RbaV0gPSAwOwogICAgICAgIGZpcmVTZWNvbmRhcmllcyhh'
        'LCBXUE5bYS50eXBlXSk7CiAgICAgICAgbiArPSBzaG90cygpLWIwOwogICAgICB9CiAgICB9CiAg'
        'fQogIGVuZW1pZXMgPSBrZWVwOwogIHIubm9TaG90c0F0Tm90aGluZyA9IG49PT0wOwogIHIuX24g'
        'PSBuOwogIC8vIFdpdGggYSByZWFsIGVuZW15IGluIHJlYWNoIHRoZXkgc3RpbGwgZmlyZS4KICBj'
        'b25zdCBmb2UgPSBlbmVtaWVzLmZpbmQoZT0+ZS50eXBlPT09J2ZpZ2h0ZXInICYmICEoZS53YXJw'
        'PjApKSB8fCBlbmVtaWVzLmZpbmQoZT0+IShlLndhcnA+MCkgJiYgIWUuaW52dWxuKTsKICBsZXQg'
        'bSA9IDA7CiAgaWYoZm9lKXsgZmkueCA9IGZvZS54LTgwOyBmaS55ID0gZm9lLnk7IGZpLmhlYWQg'
        'PSAwOwogICAgZm9yKGxldCBrPTA7azw1O2srKyl7IGNvbnN0IGIwID0gc2hvdHMoKTsgZmkuZlQg'
        'PSAwOyBzbWFsbEZpcmUoZmksIGZvZSk7IG0gKz0gc2hvdHMoKS1iMDsgfSB9CiAgci5zdGlsbEZp'
        'cmVBdEVuZW1pZXMgPSBtPjA7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTQzIERlciBOVEYt'
        'S29udm9pJywgJ209NDMnLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAoNjAwKTsKICBjb25z'
        'dCB0ID0gZW5lbWllcy5maWx0ZXIoZT0+ZS51aWQ9PT0nVDEnKTsKICByLnRocmVlVHJpdG9ucyA9'
        'IHQubGVuZ3RoPT09MyAmJiB0LmV2ZXJ5KGU9PmUuaW1nPT09J2ZydHJpdG9uJyAmJiBlLmVzY2Fw'
        'aW5nPjApOwogIHIuc2F5c1NjYW5GaXJzdCA9IG1pc3Npb25PYmo9PT0nU0NBTiBUSEUgVFJJVE9O'
        'Uyc7CiAgZGFtYWdlRW5lbXkodFswXSwgdFswXS5tYXhIcCo1LCB0WzBdLngsIHRbMF0ueSwgdHJ1'
        'ZSwgJ2JvbHQnKTsgRlMuc3RlcCgyKTsKICByLmNhbm5vdERpZVVuc2Nhbm5lZCA9IGVuZW1pZXMu'
        'aW5jbHVkZXModFswXSk7CiAgci5ub0Flb2x1cyA9ICFlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0n'
        'SzEnKSAmJiAhc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nSzEnKTsKICAvLyBVbmRlciBmaXJlIHRo'
        'ZSB3aG9sZSB0aW1lOiBpbiB0aGlzIG1pc3Npb24gdGhlIHNjYW4gc3RpbGwgZmlsbHMuCiAgZm9y'
        'KGNvbnN0IGUgb2YgdCkgZm9yKGxldCBpPTA7aTxTQ0FOX1RJTUUrMjA7aSsrKXsKICAgIHBsYXll'
        'ci54ID0gZS54OyBwbGF5ZXIueSA9IGUueTsgTU9VU0UueCA9IGUueDsgTU9VU0UueSA9IGUueTsK'
        'ICAgIHBsYXllci5zaERlbGF5ID0gOTA7IHBsYXllci5ocCA9IHBsYXllci5tYXhIcDsgRlMuc3Rl'
        'cCgxKTsgfQogIHIuYWxsU2Nhbm5lZCA9IHQuZXZlcnkoZT0+ZS5zY2FubmVkKTsKICBGUy5zdGVw'
        'KDIpOwogIHIudGhlbkRlc3Ryb3kgPSBtaXNzaW9uT2JqPT09J0RFU1RST1kgVEhFIENPTlZPWSc7'
        'CiAgRlMuc3RlcCgyMDApOwogIHIuYWVvbHVzQWZ0ZXJUaGVTY2FuID0gZW5lbWllcy5zb21lKGU9'
        'PmUudWlkPT09J0sxJyAmJiBlLmltZz09PSdudGZjcmFlb2x1cycpOwogIGZvcihjb25zdCBlIG9m'
        'IHQpIGUuaHAgPSAwOwogIGNvbnN0IGRvbmUgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9i'
        'akNhcmQudHh0PT09J0NPTlZPWSBERVNUUk9ZRUQnLCAxNTAwLCBmYWxzZSk7CiAgci5jb21wbGV0'
        'ZUNhcmQgPSBkb25lPj0wOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000MyBhIFRyaXRvbiBn'
        'ZXRzIGF3YXk6IGZhaWxlZCcsICdtPTQzJywgYAogIEZTLnN0ZXAoMzAwKTsKICBjb25zdCB0ID0g'
        'ZW5lbWllcy5maWx0ZXIoZT0+ZS51aWQ9PT0nVDEnKTsKICBmb3IoY29uc3QgZSBvZiB0KXsgZS5z'
        'Y2FubmVkID0gdHJ1ZTsgZS5lc2NhcGluZyA9IDM7IH0KICBjb25zdCBmID0gRlMudW50aWwoKCk9'
        'PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnRvbmU9PT0nZmFpbCcsIDMwMDAsIGZhbHNlKTsKICByZXR1'
        'cm4ge2ZhaWxDYXJkOiBmPj0wICYmIG9iakNhcmQudHh0PT09J0EgVFJJVE9OIEdPVCBBV0FZJ307'
        'YCk7CgpzY2VuYXJpbygnTTQ0IERlciBTY2h3YXJtJywgJ209NDQnLCBgCiAgY29uc3QgciA9IHt9'
        'OwogIEZTLnN0ZXAoNDAwKTsKICByLm5vQWxseVdpbmdBdFN0YXJ0ID0gIWFsbGllcy5zb21lKGE9'
        'PmEuc21hbGwpOwogIHIuZGVpbW9zVG9SZWFybSA9IGFsbGllcy5zb21lKGE9PmEudWlkPT09J0Ex'
        'JyAmJiBhLmltZz09PSdjb2RlaW1vcycpOwogIGNvbnN0IHNlZW4gPSB7fTsKICBsZXQgbWF4V2lu'
        'ZyA9IDAsIHN0cmF5ID0gMDsKICBGUy51bnRpbCgoKT0+eyBmb3IoY29uc3QgZSBvZiBlbmVtaWVz'
        'KSBpZihlLnVpZCkgc2VlbltlLnVpZF09MTsgZm9yKGNvbnN0IGEgb2YgYWxsaWVzKSBpZihhLnVp'
        'ZCkgc2VlblthLnVpZF09MTsKICAgIGNvbnN0IHNtID0gYWxsaWVzLmZpbHRlcihhPT5hLnNtYWxs'
        'ICYmICFhLmRlYWQpOyBtYXhXaW5nID0gTWF0aC5tYXgobWF4V2luZywgc20ubGVuZ3RoKTsKICAg'
        'IGlmKHNtLnNvbWUoYT0+YS51aWQhPT0nVzInKSkgc3RyYXkrKzsgcmV0dXJuIHdhdmVPdmVyOyB9'
        'LCAzMDAwMCwgdHJ1ZSk7CiAgLy8gT25lIGFsbGllZCB3aW5nLCB0aGUgb25lIHRoZSBtaXNzaW9u'
        'IHNlbmRzOyB0aGUgRGVpbW9zIGFkZHMgbm9uZS4KICByLm9uZUFsbHlXaW5nT25seSA9IG1heFdp'
        'bmc+MCAmJiBtYXhXaW5nPD00ICYmIHN0cmF5PT09MDsKICByLmFsbFRoZVdpbmdzID0gWydFMScs'
        'J0UyJywnRTMnLCdCMScsJ1cyJ10uZXZlcnkoaz0+c2VlbltrXSk7CiAgcmV0dXJuIHI7YCk7Cgpz'
        'Y2VuYXJpbygnTTQ1IERhcyBOYWRlbG9laHInLCAnbT00NScsIGAKICBjb25zdCByID0ge307CiAg'
        'RlMuc3RlcCg1MDApOwogIGNvbnN0IGsgPSBlbmVtaWVzLmZpbHRlcihlPT4vXktbMTIzXSQvLnRl'
        'c3QoZS51aWR8fCcnKSk7CiAgci50aHJlZUZlbnJpcyA9IGsubGVuZ3RoPT09MyAmJiBrLmV2ZXJ5'
        'KGU9PmUuaW1nPT09J250ZmNyZmVucmlzJyk7CiAgY29uc3QgeXMgPSBrLm1hcChlPT5lLnkpLnNv'
        'cnQoKGEsYik9PmEtYik7CiAgci5pblNlcGFyYXRlTGFuZXMgPSB5cy5sZW5ndGg9PT0zICYmIHlz'
        'WzFdLXlzWzBdID4gNDAgJiYgeXNbMl0teXNbMV0gPiA0MDsKICBjb25zdCBvID0gYWxsaWVzLmZp'
        'bmQoYT0+YS51aWQ9PT0nQTEnKTsKICByLm9yaW9uQ3Jvc3NlcyA9ICEhbyAmJiBvLnRyYW5zaXQ9'
        'PT10cnVlOwogIG8uaHAgPSBvLm1heEhwID0gMWU3OyBmb3IoY29uc3QgcyBvZiBvLnN1YnN8fFtd'
        'KSBzLmhwID0gcy5tYXhIcCA9IDFlNzsKICBsZXQgcm9ja3MgPSAwOwogIGNvbnN0IHQgPSBGUy51'
        'bnRpbCgoKT0+eyBpZihhbGxpZXMuaW5jbHVkZXMobykpIG8uaHAgPSBvLm1heEhwOwogICAgaWYo'
        'ZW5lbWllcy5zb21lKGU9PmUudHlwZT09PSdhc3Rlcm9pZCcpKSByb2NrcysrOwogICAgcmV0dXJu'
        'ICEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdUSEUgT1JJT04gSVMgVEhST1VHSCc7IH0sIDkw'
        'MDAsIHRydWUpOwogIHIudGhyb3VnaENhcmQgPSB0Pj0wOwogIHIubm9Bc3Rlcm9pZHMgPSByb2Nr'
        'cz09PTA7CiAgRlMudW50aWwoKCk9PndhdmVPdmVyIHx8IHdhdmU+NDUsIDMwMDAsIHRydWUpOwog'
        'IHIud2F2ZUVuZHMgPSB3YXZlT3ZlciB8fCB3YXZlPjQ1OwogIHJldHVybiByO2ApOwoKc2NlbmFy'
        'aW8oJ000NiBEaWUgV2lzc2Vuc2NoYWZ0bGVyJywgJ209NDYnLCBgCiAgY29uc3QgciA9IHt9Owog'
        'IHNjb3JlID0gMTAwMDsKICBGUy5zdGVwKDQwMCk7CiAgY29uc3QgZiA9IGVuZW1pZXMuZmluZChl'
        'PT5lLnVpZD09PSdGMScpOwogIHIuZmF1c3R1c1BhcmtlZCA9ICEhZiAmJiBNYXRoLmFicyhmLnkt'
        'MjUwKSA8IDE7CiAgci5vbkFEZWFkbGluZSA9ICEhZiAmJiBmLmZsZWVUPjA7CiAgLy8gVGhlIGNv'
        'dW50ZG93biBzaXRzIGF0IHRoZSByaWdodCBlZGdlLCBjbGVhciBvZiB0aGUgb2JqZWN0aXZlIGxp'
        'bmUuCiAgY29uc3QgX2Z0ID0gW10sIF9wbCA9IFtdOwogIGNvbnN0IF9meCA9IGN0eC5maWxsVGV4'
        'dCwgX3RwID0gdGhQbGF0ZTsKICBjdHguZmlsbFRleHQgPSBmdW5jdGlvbih0LCB4LCB5KXsgX2Z0'
        'LnB1c2goe3Q6U3RyaW5nKHQpLCB4LCB5fSk7IHJldHVybiBfZnguYXBwbHkodGhpcywgYXJndW1l'
        'bnRzKTsgfTsKICB0aFBsYXRlID0gZnVuY3Rpb24oeCwgeSwgdywgaCl7IF9wbC5wdXNoKHt4LCB5'
        'LCB3LCBofSk7IHJldHVybiBfdHAuYXBwbHkodGhpcywgYXJndW1lbnRzKTsgfTsKICB0cnkgeyBk'
        'cmF3T2JqTGluZSh7dHh0Om1pc3Npb25PYmosIGNvbDonI2ZmZid9KTsgZHJhd0ZsZWVXYXJuaW5n'
        'KCk7IH0KICBmaW5hbGx5IHsgY3R4LmZpbGxUZXh0ID0gX2Z4OyB0aFBsYXRlID0gX3RwOyB9CiAg'
        'Y29uc3QgX2Z3ID0gX2Z0LmZpbmQobz0+L0pVTVBJTkcgT1VUIElOLy50ZXN0KG8udCkpOwogIHIu'
        'Y291bnRkb3duTmFtZXNTaGlwID0gISFfZncgJiYgL0ZBVVNUVVMvLnRlc3QoX2Z3LnQpOwogIGNv'
        'bnN0IF9vbCA9IF9wbFswXSwgX2NkID0gX3BsW19wbC5sZW5ndGgtMV07CiAgci5jb3VudGRvd25D'
        'bGVhck9mT2JqZWN0aXZlID0gISFfb2wgJiYgISFfY2QgJiYgX3BsLmxlbmd0aD49MiAmJgogICAg'
        'KF9vbC54K19vbC53IDwgX2NkLngpICYmIChfY2QueCtfY2QudyA8PSBXKTsKICBkYW1hZ2VFbmVt'
        'eShmLCBmLm1heEhwKjUsIGYueCwgZi55LCB0cnVlLCAnYm9sdCcpOyBGUy5zdGVwKDIpOwogIHIu'
        'Y2Fubm90QmVEZXN0cm95ZWQgPSBlbmVtaWVzLmluY2x1ZGVzKGYpOwogIGNvbnN0IGtpbGwgPSBp'
        'ZD0+eyBmb3IoY29uc3QgcyBvZiBmLnN1YnMpIGlmKHMuaWQ9PT1pZCl7IHMuZGVhZD10cnVlOyBz'
        'LmhwPTA7IH0gfTsKICBraWxsKCduYXZpZ2F0aW9uJyk7IEZTLnN0ZXAoMik7CiAgY29uc3QgZnQg'
        'PSBmLmZsZWVUOyBGUy5zdGVwKDIwMCk7CiAgci5ub05hdmlnYXRpb25Ob0p1bXAgPSBmLmZsZWVU'
        'PT09ZnQ7CiAgci5ub0FyZ29ZZXQgPSAhYWxsaWVzLnNvbWUoYT0+YS51aWQ9PT0nVDEnKSAmJiAh'
        'c3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nVDEnKTsKICBraWxsKCd3ZWFwb25zJyk7IEZTLnN0ZXAo'
        'Mik7CiAgci5jb3ZlclRoZUFyZ28gPSBtaXNzaW9uT2JqPT09J0NPVkVSIFRIRSBBUkdPJzsKICBs'
        'ZXQgYXJnbyA9IG51bGw7CiAgY29uc3QgYXQgPSBGUy51bnRpbCgoKT0+eyBhcmdvID0gYWxsaWVz'
        'LmZpbmQoYT0+YS51aWQ9PT0nVDEnKTsgcmV0dXJuICEhYXJnbyAmJiBhcmdvLmhvbGRUIT1udWxs'
        'OyB9LCA5MDAwLCB0cnVlKTsKICAvLyBCb2FyZGluZyB0YWtlcyBpdHMgdGltZTogc2hlIHN0YXlz'
        'IG9uIHRoZSBGYXVzdHVzLCBub3RoaW5nIGlzIHRha2VuIHlldC4KICBjb25zdCBheCA9IGFyZ28g'
        'JiYgYXJnby54OwogIEZTLnN0ZXAoNDAwKTsKICByLmJvYXJkaW5nSG9sZHMgPSBhdD49MCAmJiAh'
        'RVZfRE9DS1snVDEnXSAmJiAhZi5jYXB0dXJlZCAmJiBNYXRoLmFicyhhcmdvLngtYXgpIDwgMSAm'
        'JiBlbmVtaWVzLmluY2x1ZGVzKGYpOwogIGNvbnN0IGdvdCA9IEZTLnVudGlsKCgpPT4hIUVWX0RP'
        'Q0tbJ1QxJ10sIDkwMDAsIHRydWUpOwogIEZTLnN0ZXAoNSk7CiAgci5kb2Nrc0FuZFRha2VzID0g'
        'Z290Pj0wICYmIGYuY2FwdHVyZWQ9PT10cnVlOwogIC8vIEFuZCB0aGVuIGJvdGgganVtcCAtIHRo'
        'ZSBBcmdvIGRvZXMgbm90IGZseSBvbiB0byB0aGUgcmlnaHQuCiAgci5hcmdvSnVtcHNPdXQgPSAh'
        'IWFyZ28gJiYgYXJnby53YXJwT3V0PjAgJiYgIWFyZ28uY3Jvc3Npbmc7CiAgci5jb21wbGV0ZUNh'
        'cmQgPSAhIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nRkFVU1RVUyBDQVBUVVJFRCc7CiAgRlMu'
        'c3RlcCgzMDApOwogIHIubm9GYWlsdXJlQWZ0ZXJ3YXJkcyA9ICFhbGxpZXMuaW5jbHVkZXMoYXJn'
        'bykgJiYgIShvYmpDYXJkICYmIG9iakNhcmQudG9uZT09PSdmYWlsJyk7CiAgcmV0dXJuIHI7YCk7'
        'CgpzY2VuYXJpbygnTTQ2IGxlZnQgYWxvbmUgc2hlIGp1bXBzOiBmYWlsZWQnLCAnbT00NicsIGAK'
        'ICBGUy5zdGVwKDMwMCk7CiAgY29uc3QgZiA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdGMScp'
        'OwogIGZvcihjb25zdCBzIG9mIGYuc3Vicykgcy5ocCA9IHMubWF4SHAgPSAxZTc7CiAgY29uc3Qg'
        'dCA9IEZTLnVudGlsKCgpPT4hIW9iakNhcmQgJiYgb2JqQ2FyZC50b25lPT09J2ZhaWwnLCA5MDAw'
        'LCB0cnVlKTsKICByZXR1cm4ge2ZhaWxDYXJkOiB0Pj0wICYmIG9iakNhcmQudHh0PT09J1RIRSBG'
        'QVVTVFVTIEdPVCBBV0FZJ307YCk7CgpzY2VuYXJpbygnTTQ3IERpZSB6d2VpdGUgRmx1Y2h0Jywg'
        'J209NDcnLCBgCiAgY29uc3QgciA9IHt9OwogIHNjb3JlID0gNTAwMDsKICBGUy5zdGVwKDQwMCk7'
        'CiAgci5pY2VuaSA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdWMScgJiYgZS5pY2VuaSk7CiAg'
        'ci5oZWNhdGUgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nVjInICYmIGUuaW1nPT09J250ZmRl'
        'aGVjYXRlJyk7CiAgci5ub0FsbGllcyA9ICFhbGxpZXMuc29tZShhPT4hYS5zbWFsbCk7CiAgci5u'
        'b0Flb2x1cyA9ICFlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nSzEnKTsKICBjb25zdCBfdjEgPSBl'
        'bmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nVjEnKSwgX3YyID0gZW5lbWllcy5maW5kKGU9PmUudWlk'
        'PT09J1YyJyk7CiAgY29uc3QgX3kxID0gX3YxICYmIF92MS55LCBfeTIgPSBfdjIgJiYgX3YyLnk7'
        'CiAgRlMuc3RlcCgzMDApOwogIHIuc2hpcHNIb2xkSGVpZ2h0ID0gISFfdjEgJiYgISFfdjIgJiYg'
        'TWF0aC5hYnMoX3YxLnktX3kxKTwwLjUgJiYgTWF0aC5hYnMoX3YyLnktX3kyKTwwLjUgJiYKICAg'
        'IE1hdGguYWJzKF92MS55LTE1MCk8MSAmJiBNYXRoLmFicyhfdjIueS0zNTApPDE7CiAgci5pY2Vu'
        'aUZvcnR5U2Vjb25kcyA9ICEhX3YxICYmIF92MS5mbGVlVD4wICYmIF92MS5mbGVlVCA8PSA0MCpU'
        'SUNLX0haOwogIHIubm9FbmRsZXNzUmVpbmZvcmNlbWVudCA9ICFldlJlaW5mOwogIGNvbnN0IHQg'
        'PSBGUy51bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdWMScpLCA5MDAwLCB0cnVl'
        'KTsKICByLmljZW5pR2V0c0F3YXkgPSB0Pj0wICYmIGljZW5Fc2NhcGVzPT09MSAmJiBzY29yZT49'
        'NTAwMDsKICBjb25zdCB2ID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YyJyk7IGlmKHYpIHYu'
        'aHAgPSAwOwogIHIuY29tcGxldGVDYXJkID0gRlMudW50aWwoKCk9PiEhb2JqQ2FyZCAmJiBvYmpD'
        'YXJkLnR4dD09PSdIRUNBVEUgREVTVFJPWUVEJywgMzAwMCwgZmFsc2UpID49IDA7CiAgcmV0dXJu'
        'IHI7YCk7CgpzY2VuYXJpbygnTTQ4IERpZSBBdWZrbGFlcnVuZycsICdtPTQ4JywgYAogIGNvbnN0'
        'IHIgPSB7fTsKICBzY29yZSA9IDIwMDA7CiAgci5hbm5vdW5jZWQgPSBOT1RJQ0VTLnNvbWUobj0+'
        'bi50eHQ9PT0nR1RGIFBFR0FTVVMgQVNTSUdORUQnKTsKICBGUy5zdGVwKDQwMCk7CiAgci5mbHlp'
        'bmdBUGVnYXN1cyA9IHBsYXllci5zaGlwPT09J2ZpcGVnYXN1cyc7CiAgci5ub3RoaW5nTG9ja3NI'
        'ZXIgPSAhY2FuTG9ja09uKHBsYXllcik7CiAgY29uc3QgdiA9IGVuZW1pZXMuZmluZChlPT5lLnVp'
        'ZD09PSdWMScpOwogIHIuZ3Vuc0hvbGRGaXJlID0gY2FwR3VuVGFyZ2V0KHYpPT09bnVsbDsKICBy'
        'Lm5vQmVhbU9uSGVyID0gIWJlYW1UYXJnZXRzKHYsIGZhbHNlKS5pbmNsdWRlcyhwbGF5ZXIpOwog'
        'IHIubm9IYW5nYXIgPSBzaGlwU3dhcFJlYWR5KCk9PT1mYWxzZTsKICByLnJpbmdzU2hvd24gPSAh'
        'IXYgJiYgdi5zY2FuU3Vicz09PXRydWUgJiYgdi5zdWJzLmV2ZXJ5KHM9PiFzLnNjYW5uZWQpOwog'
        'IGZvcihjb25zdCBzIG9mIHYuc3Vicyl7IGNvbnN0IHAgPSBzdWJQb3Modiwgcyk7IEZTLmhvbGQo'
        'cC54LCBwLnksIFNVQl9TQ0FOX1RJTUUgKyAyMCk7IH0KICByLmFsbEZpdmVTY2FubmVkID0gdi5z'
        'dWJzLmV2ZXJ5KHM9PnMuc2Nhbm5lZCkgJiYgdi5zY2FubmVkPT09dHJ1ZTsKICBGUy5zdGVwKDMp'
        'OwogIHIuY29tcGxldGVDYXJkID0gISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J09SSU9OIFND'
        'QU5ORUQnOwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+IWVuZW1pZXMuaW5jbHVkZXModiksIDE1'
        'MDAsIGZhbHNlKTsKICByLm9yaW9uTGVhdmVzV2l0aG91dFBlbmFsdHkgPSB0Pj0wICYmIHNjb3Jl'
        'ID49IDIwMDA7CiAgRlMudW50aWwoKCk9PndhdmU+NDgsIDMwMDAwLCB0cnVlKTsKICByLm93bkh1'
        'bGxCYWNrTmV4dFdhdmUgPSB3YXZlPT09NDkgJiYgcGxheWVyLnNoaXA9PT0nZmlteXJtaWRvbic7'
        'CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnQ29sb3NzdXMgYmVhbXMgYXJlIFRlcnJhbicsICcn'
        'LCBgCiAgcmV0dXJuIHttYWluOiBiZWFtQ29sKCdndHZhJywgdHJ1ZSk9PT0nIzAwZmY1NScsIGFu'
        'dGlGaWdodGVyOiBiZWFtQ29sKCdndHZhJywgZmFsc2UpPT09JyM0NDk5ZmYnfTtgLCB0cnVlKTsK'
        'CnNjZW5hcmlvKCdIb0wgc3RhcnQgdW5jaGFuZ2VkJywgJ209MScsIGAKICByZXR1cm4ge3dhdmU6'
        'IHdhdmUsIHRob3RoOiBwbGF5ZXIuc2hpcD09PSdmaXRvdGgnLCB2YXN1ZGFuQ2FsbDogQUxMWV9G'
        'QUNfT04udmFzdWRhbj09PXRydWUgJiYgQUxMWV9GQUNfT04udGVycmFuPT09ZmFsc2V9O2ApOwoK'
        'Ly8g4pSA4pSAIFJ1bm5lciDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKKGFzeW5jKCk9PnsKICBjb25zdCBicm93c2Vy'
        'ID0gYXdhaXQgY2hyb21pdW0ubGF1bmNoKCk7CiAgbGV0IGZhaWxzID0gMDsKICBjb25zdCBvbmx5'
        'ID0gcHJvY2Vzcy5hcmd2WzRdOwogIGZvcihjb25zdCBzYyBvZiBzY2VuYXJpb3MpewogICAgaWYo'
        'b25seSAmJiBzYy5uYW1lLmluZGV4T2Yob25seSk8MCkgY29udGludWU7CiAgICBjb25zdCBwYWdl'
        'ID0gYXdhaXQgYnJvd3Nlci5uZXdQYWdlKCk7CiAgICBjb25zdCBlcnJzID0gW107CiAgICBwYWdl'
        'Lm9uKCdwYWdlZXJyb3InLCBlPT5lcnJzLnB1c2goU3RyaW5nKGUubWVzc2FnZXx8ZSkpKTsKICAg'
        'IGF3YWl0IHBhZ2UuZ290bygnZmlsZTovLycgKyB0bXAgKyAnPycgKyBzYy5xdWVyeSk7CiAgICBh'
        'd2FpdCBwYWdlLndhaXRGb3JUaW1lb3V0KDMwMCk7CiAgICBsZXQgcmVzOwogICAgdHJ5ewogICAg'
        'ICByZXMgPSBhd2FpdCBwYWdlLmV2YWx1YXRlKEhFTFBFUlMgKyBgXG5GUy5mYWtlSW1hZ2VzKCk7'
        'YCArIChzYy5ub0xhdW5jaCA/ICcnIDogJyBsYXVuY2hHYW1lKCk7JykgKyBgXG4oZnVuY3Rpb24o'
        'KXske3NjLmJvZHl9fSkoKWApOwogICAgfWNhdGNoKGUpeyByZXMgPSBudWxsOyBlcnJzLnB1c2go'
        'U3RyaW5nKGUubWVzc2FnZXx8ZSkpOyB9CiAgICBjb25zb2xlLmxvZyhzYy5uYW1lICsgJyAgKD8n'
        'ICsgc2MucXVlcnkgKyAnKScpOwogICAgaWYocmVzKSBmb3IoY29uc3QgW2ssdl0gb2YgT2JqZWN0'
        'LmVudHJpZXMocmVzKSl7CiAgICAgIGNvbnN0IGdvb2QgPSAodHlwZW9mIHY9PT0nYm9vbGVhbicp'
        'ID8gdiA6IHRydWU7CiAgICAgIGlmKCFnb29kKSBmYWlscysrOwogICAgICBjb25zb2xlLmxvZygo'
        'Z29vZCA/ICcgIG9rICAgICcgOiAnICBGQUlMICAnKSArIGsgKyAodHlwZW9mIHY9PT0nYm9vbGVh'
        'bicgPyAnJyA6ICcgPSAnICsgSlNPTi5zdHJpbmdpZnkodikpKTsKICAgIH0KICAgIGlmKGVycnMu'
        'bGVuZ3RoKXsgZmFpbHMrKzsgY29uc29sZS5sb2coJyAgRkFJTCAgcGFnZSBlcnJvcnM6XG4gICAg'
        'JyArIGVycnMuc2xpY2UoMCw0KS5qb2luKCdcbiAgICAnKSk7IH0KICAgIGF3YWl0IHBhZ2UuY2xv'
        'c2UoKTsKICB9CiAgYXdhaXQgYnJvd3Nlci5jbG9zZSgpOwogIGZzLnVubGlua1N5bmModG1wKTsK'
        'ICBjb25zb2xlLmxvZygnXG4nICsgKGZhaWxzID8gZmFpbHMgKyAnIEZBSUxFRCcgOiAnYWxsIHBh'
        'c3NlZCcpKTsKICBwcm9jZXNzLmV4aXQoZmFpbHMgPyAxIDogMCk7Cn0pKCk7Cg=='
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
        'LCAnZXJmdWVsbHQnLCAnZ2VyZXR0ZXQnLCAndmVybG9yZW4nLCAnZW50a29tbWVuJ10pOwpjb25z'
        'dCBFRkZFQ1RfVU5JVCA9IG5ldyBTZXQoWydlaW53YXJwZW4nLCAnc2VpdGUnLCAncmF1cycsICdo'
        'ZWlsZW4nLCAna2FwZXJuJywgJ2ZyZWlnZWJlbicsICdrdWxpc3NlJywgJ3J1ZiddKTsKCmxldCBl'
        'cnJvcnMgPSAwLCBtaXNzaW9ucyA9IDA7CmZvcihjb25zdCBrZXkgb2YgT2JqZWN0LmtleXMoU0NS'
        'SVBUX1dBVkVTKS5zb3J0KChhLCBiKSA9PiBhIC0gYikpewogIGNvbnN0IG0gPSBTQ1JJUFRfV0FW'
        'RVNba2V5XSwgdW5pdHMgPSBtLnUgfHwgW10sIGV2cyA9IG0uZXYgfHwgW107CiAgY29uc3QgdGFn'
        'ID0gJ00nICsgU3RyaW5nKGtleSkucGFkU3RhcnQoMywgJzAnKTsKICBjb25zdCBpZHMgPSBuZXcg'
        'TWFwKCk7CiAgY29uc3QgYmFkID0gW107CiAgbWlzc2lvbnMrKzsKCiAgZm9yKGNvbnN0IHUgb2Yg'
        'dW5pdHMpewogICAgaWYoIXUuaWQpIGJhZC5wdXNoKCd1bml0IHdpdGhvdXQgaWQgKCcgKyB1LmMg'
        'KyAnKScpOwogICAgZWxzZSBpZihpZHMuaGFzKHUuaWQpKSBiYWQucHVzaCgnaWQgdXNlZCB0d2lj'
        'ZTogJyArIHUuaWQpOwogICAgaWRzLnNldCh1LmlkLCB1KTsKICAgIGlmKCFDQVRfRkFDW3UuY10g'
        'JiYgIUNBVF9GSVhbdS5jXSkKICAgICAgYmFkLnB1c2godS5pZCArICc6IHVua25vd24gY2F0ZWdv'
        'cnkgIicgKyB1LmMgKyAnIiAtIHdvdWxkIG5ldmVyIHNwYXduJyk7CiAgfQogIGZvcihjb25zdCB1'
        'IG9mIHVuaXRzKQogICAgaWYodS5zcHIgJiYgIUhVTExfS0VZUy5oYXModS5zcHIpKSBiYWQucHVz'
        'aCh1LmlkICsgJzogdW5rbm93biBodWxsICInICsgdS5zcHIgKyAnIicpOwogIGlmKG0uZmFjICE9'
        'PSBDWUNMRV9GQUMoK2tleSkpIGJhZC5wdXNoKCdmYWN0aW9uICcgKyBtLmZhYyArICcsIGJ1dCB0'
        'aGlzIHdhdmUgYmVsb25ncyB0byB0aGUgJyArIENZQ0xFX0ZBQygra2V5KSArICcgY3ljbGUnKTsK'
        'ICBmb3IoY29uc3QgdSBvZiB1bml0cyl7CiAgICBpZih1LmRvY2tUbyAmJiAhaWRzLmhhcyh1LmRv'
        'Y2tUbykpIGJhZC5wdXNoKHUuaWQgKyAnOiBkb2NrVG8gcG9pbnRzIGF0IG1pc3NpbmcgaWQgJyAr'
        'IHUuZG9ja1RvKTsKICAgIGlmKHUuYXQgJiYgIWlkcy5oYXModS5hdCkpICAgICAgICAgYmFkLnB1'
        'c2godS5pZCArICc6IGF0IHBvaW50cyBhdCBtaXNzaW5nIGlkICcgKyB1LmF0KTsKICB9CgogIGNv'
        'bnN0IHdhcnBlZEluID0gbmV3IFNldCgpOwogIGxldCByZWluZk9uID0gZmFsc2UsIHJlaW5mT2Zm'
        'ID0gZmFsc2U7CiAgZXZzLmZvckVhY2goKGUsIGkpID0+IHsKICAgIGNvbnN0IHdoZXJlID0gJ2V2'
        'ZW50ICcgKyAoaSArIDEpICsgJyAoJyArIGUudCArICcgLT4gJyArIGUudyArICcpJzsKICAgIGNv'
        'bnN0IGFyZyA9IChlLmEyICE9PSB1bmRlZmluZWQpID8gZS5hMiA6IGUuYTsKICAgIGlmKCFUUklH'
        'R0VSUy5oYXMoZS50KSkgYmFkLnB1c2god2hlcmUgKyAnOiB1bmtub3duIHRyaWdnZXIgIicgKyBl'
        'LnQgKyAnIicpOwogICAgaWYoIUVGRkVDVFMuaGFzKGUudykpICBiYWQucHVzaCh3aGVyZSArICc6'
        'IHVua25vd24gZWZmZWN0ICInICsgZS53ICsgJyInKTsKICAgIC8vIEEgdHJpZ2dlciBtYXkgbmFt'
        'ZSBzZXZlcmFsIGlkcyBqb2luZWQgd2l0aCAnKycuCiAgICBpZihUUklHR0VSUy5oYXMoZS50KSAm'
        'JiAhVFJJR19OT19JRC5oYXMoZS50KSkKICAgICAgZm9yKGNvbnN0IGlkIG9mIFN0cmluZyhlLmEp'
        'LnNwbGl0KCcrJykpCiAgICAgICAgaWYoIWlkcy5oYXMoaWQpKSBiYWQucHVzaCh3aGVyZSArICc6'
        'IHRyaWdnZXIgcG9pbnRzIGF0IG1pc3NpbmcgaWQgJyArIGlkKTsKICAgIGlmKGUudCA9PT0gJ2Fu'
        'Z2Vkb2NrdCcgJiYgaWRzLmhhcyhlLmEpICYmICFpZHMuZ2V0KGUuYSkuZG9ja1RvKQogICAgICBi'
        'YWQucHVzaCh3aGVyZSArICc6ICcgKyBlLmEgKyAnIGhhcyBubyBkb2NrVG8sIGl0IGNhbiBuZXZl'
        'ciBkb2NrJyk7CiAgICBpZihFRkZFQ1RfVU5JVC5oYXMoZS53KSAmJiAhaWRzLmhhcyhhcmcpKQog'
        'ICAgICBiYWQucHVzaCh3aGVyZSArICc6IGVmZmVjdCBwb2ludHMgYXQgbWlzc2luZyBpZCAnICsg'
        'YXJnKTsKICAgIGlmKGUudyA9PT0gJ2phZ2QnICYmIGFyZyAmJiAhaWRzLmhhcyhhcmcpKQogICAg'
        'ICBiYWQucHVzaCh3aGVyZSArICc6IGh1bnQgdGFyZ2V0IGlzIGEgbWlzc2luZyBpZCAnICsgYXJn'
        'KTsKICAgIGlmKGUudyA9PT0gJ2VpbndhcnBlbicpewogICAgICB3YXJwZWRJbi5hZGQoYXJnKTsK'
        'ICAgICAgaWYoaWRzLmhhcyhhcmcpICYmICFpZHMuZ2V0KGFyZykud2FpdCkKICAgICAgICBiYWQu'
        'cHVzaCh3aGVyZSArICc6ICcgKyBhcmcgKyAnIGlzIG5vdCB3YWl0aW5nIC0gd2FycGluZyBpdCBp'
        'biBkb2VzIG5vdGhpbmcnKTsKICAgIH0KICAgIGlmKGUudyA9PT0gJ25hY2hzY2h1YicpeyBpZihh'
        'cmcgPT09ICdhdXMnKSByZWluZk9mZiA9IHRydWU7IGVsc2UgcmVpbmZPbiA9IHRydWU7IH0KICAg'
        'IGlmKGUudyA9PT0gJ2VuZGUnKSByZWluZk9mZiA9IHRydWU7CiAgfSk7CiAgZm9yKGNvbnN0IHUg'
        'b2YgdW5pdHMpCiAgICBpZih1LndhaXQgJiYgIXdhcnBlZEluLmhhcyh1LmlkKSkgYmFkLnB1c2go'
        'dS5pZCArICc6IHdhaXRzLCBidXQgbm8gZXZlbnQgZXZlciB3YXJwcyBpdCBpbicpOwogIGlmKHJl'
        'aW5mT24gJiYgIXJlaW5mT2ZmKSBiYWQucHVzaCgncmVpbmZvcmNlbWVudHMgc3dpdGNoZWQgb24s'
        'IG5ldmVyIHN3aXRjaGVkIG9mZicpOwogIGlmKG0uaHVudCAmJiAhaWRzLmhhcyhtLmh1bnQpKSBi'
        'YWQucHVzaCgnaHVudCBwb2ludHMgYXQgbWlzc2luZyBpZCAnICsgbS5odW50KTsKCiAgaWYoYmFk'
        'Lmxlbmd0aCl7IGVycm9ycyArPSBiYWQubGVuZ3RoOyBjb25zb2xlLmxvZyh0YWcgKyAnICcgKyAo'
        'bS5uYW1lIHx8ICcnKSk7IGJhZC5mb3JFYWNoKGIgPT4gY29uc29sZS5sb2coJyAgICcgKyBiKSk7'
        'IH0KfQpjb25zb2xlLmxvZygnXG4nICsgbWlzc2lvbnMgKyAnIG1pc3Npb25zIGNoZWNrZWQsICcg'
        'KyBlcnJvcnMgKyAnIHByb2JsZW1zJyk7CmNvbnNvbGUubG9nKCdrbm93biB0cmlnZ2VyczogJyAr'
        'IFsuLi5UUklHR0VSU10uam9pbignICcpKTsKY29uc29sZS5sb2coJ2tub3duIGVmZmVjdHM6ICAn'
        'ICsgWy4uLkVGRkVDVFNdLmpvaW4oJyAnKSk7CnByb2Nlc3MuZXhpdChlcnJvcnMgPyAxIDogMCk7'
        'Cg=='
    ),
}
for name, data in TEST_FILES.items():
    open(name, 'wb').write(base64.b64decode(data))
print("v142 applied: NTF missions 55-60, checks updated. Now run: python3 assemble.py 142")
