#!/usr/bin/env python3
"""FS3 v136 - NTF missions 43 to 48.

    43 Der NTF-Konvoi     three Tritons run for the edge; scan them first -
                          until scanned they cannot be destroyed - then
                          destroy the convoy
    44 Der Schwarm        wing after wing, an allied Deimos to rearm at and
                          allied fighters on the player's side
    45 Das Nadeloehr      three NTF Fenris as a blockade; an Orion has to
                          get through
    46 Die Wissenschaftler a parked Faustus that jumps on a deadline: take
                          out her navigation and her weapons, then an Argo
                          docks and takes her
    47 Die zweite Flucht  a forlorn hope: Iceni, Hecate, Aeolus and wings,
                          no allies. The Iceni gets away; the Hecate need not
    48 Die Aufklaerung    the player is put into a GTF Pegasus for this one
                          mission and has to scan all five subsystems of an
                          NTD Orion. The Pegasus cannot be locked: beams,
                          missiles and the destroyer's guns do not find her.
                          Fighters still see her.

Mechanics these need:
  - scanFirst: a scan target cannot be destroyed before it is scanned.
  - trigger 'gescannt': every ship of an id has been scanned.
  - scanSubs: the ship is scanned subsystem by subsystem - hold near each
    one until its ring fills. The capital's guns ignore a ship they cannot
    lock (the Pegasus) instead of aiming at her anyway.
  - ship:'<hull>' on a mission puts the player into that hull for the
    mission; the next wave hands the old one back, refitted. No switching
    at a hangar during such a mission.
  - flee on an enemy capital in a written mission (a jump deadline).

Needs v135. Edits src/30_waves.js, src/40_world.js, src/50_combat.js,
src/60_effects.js and src/70_ui.js in place, and writes the updated
shipsim.js, pausesim.js and fieldsim.js. Run assemble.py afterwards.
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
ui = load("src/70_ui.js")

# ══ Scanning: first-scan lock, subsystem scans, the trigger ════════════
wo = replace_once(
    wo,
    "  if(e.defectLock || e.captureLock){\n",
    "  // scanLock: a scan target that is to be scanned before it may die.\n"
    "  if(e.defectLock || e.captureLock || (e.scanLock && !e.scanned)){\n",
    "damageEnemy: scan lock")

wv = replace_once(
    wv,
    "           x:xx, y:yy, scan:u.scan?1:0, escape:u.escape,\n",
    "           x:xx, y:yy, scan:u.scan?1:0, escape:u.escape, scanFirst:u.scanFirst,\n",
    "scriptUnit: scanFirst")

wv = replace_once(
    wv,
    "             escWarp:u.escWarp, capture:u.capture,\n",
    "             escWarp:u.escWarp, capture:u.capture, flee:u.flee, scanSubs:u.scanSubs,\n"
    "             fleeFree:u.fleeFree,\n",
    "scriptUnit: flee, scanSubs")

wv = replace_once(
    wv,
    "  if(sp.capture) e.captureLock = true;\n",
    "  if(sp.capture) e.captureLock = true;\n"
    "  // Scanned before it may die: the scan is the point of it.\n"
    "  if(sp.scanFirst) e.scanLock = true;\n"
    "  // Scanned subsystem by subsystem, see tickSubScan().\n"
    "  if(sp.scanSubs && e.subs){ e.scanSubs = true; e.noTarget = true;\n"
    "    for(const s of e.subs){ s.scanT = 0; s.scanned = false; } }\n",
    "applySpawnOpts: scanFirst, scanSubs")

wv = replace_once(
    wv,
    "function drawScanRing(e){\n"
    "  if(!e.scan) return;\n",
    "// ── SUBSYSTEM SCAN ───────────────────────────────────────────\n"
    "// A ship that is read system by system: hold within SUB_SCAN_R of one of\n"
    "// its subsystems, undisturbed, until its ring fills. The nearest one in\n"
    "// reach is the one being read. When all five are done, so is the ship.\n"
    "const SUB_SCAN_R = 60, SUB_SCAN_TIME = 150;\n"
    "function tickSubScan(){\n"
    "  if(GS!=='playing') return;\n"
    "  for(const e of enemies){\n"
    "    if(!e.scanSubs || e.scanned || e.dead || e.warp>0) continue;\n"
    "    let best = null, bd = SUB_SCAN_R;\n"
    "    for(const s of e.subs){\n"
    "      if(s.scanned) continue;\n"
    "      const p = subPos(e, s), d = Math.hypot(player.x-p.x, player.y-p.y);\n"
    "      if(d <= bd){ bd = d; best = s; }\n"
    "    }\n"
    "    for(const s of e.subs){\n"
    "      if(s.scanned) continue;\n"
    "      if(s===best && player.shDelay<=0) s.scanT++;\n"
    "      else if(s.scanT>0) s.scanT = Math.max(0, s.scanT-SCAN_DECAY);\n"
    "      if(s.scanT >= SUB_SCAN_TIME){\n"
    "        s.scanned = true; score += 100;\n"
    "        const p = subPos(e, s);\n"
    "        SUB_MSGS.push({x:p.x, y:p.y-18, txt:s.label+' SCANNED', life:170, ml:170,\n"
    "                       ally:true, tone:'good'});\n"
    "      }\n"
    "    }\n"
    "    if(e.subs.every(function(s){ return s.scanned; })){\n"
    "      e.scanned = true; score += 500;\n"
    "      if(STATS.scans==null) STATS.scans = 0;\n"
    "      STATS.scans++;\n"
    "    }\n"
    "  }\n"
    "}\n"
    "function drawSubScan(e){\n"
    "  const pulse = 0.5 + 0.5*Math.sin(fc*0.10);\n"
    "  for(const s of e.subs){\n"
    "    const p = subPos(e, s);\n"
    "    ctx.save();\n"
    "    ctx.translate(p.x|0, p.y|0);\n"
    "    ctx.lineWidth = 1.5;\n"
    "    if(s.scanned){\n"
    "      ctx.strokeStyle = 'rgba(77,255,136,0.85)';\n"
    "      ctx.beginPath(); ctx.arc(0, 0, 11, 0, Math.PI*2); ctx.stroke();\n"
    "    } else {\n"
    "      ctx.strokeStyle = 'rgba(127,214,255,'+(0.35+0.35*pulse).toFixed(2)+')';\n"
    "      ctx.setLineDash([3,3]);\n"
    "      ctx.beginPath(); ctx.arc(0, 0, 12, 0, Math.PI*2); ctx.stroke();\n"
    "      ctx.setLineDash([]);\n"
    "      const t = Math.min(1, (s.scanT||0)/SUB_SCAN_TIME);\n"
    "      if(t>0){\n"
    "        ctx.strokeStyle = '#7fd6ff'; ctx.lineWidth = 2.5;\n"
    "        ctx.beginPath(); ctx.arc(0, 0, 12, -Math.PI/2, -Math.PI/2 + t*Math.PI*2); ctx.stroke();\n"
    "      }\n"
    "    }\n"
    "    ctx.restore();\n"
    "  }\n"
    "}\n"
    "function drawScanRing(e){\n"
    "  if(e.scanSubs && !e.scanned){ drawSubScan(e); return; }\n"
    "  if(!e.scan) return;\n",
    "subsystem scan")

wv = replace_once(
    wv,
    "    case 'erfuellt':\n",
    "    case 'gescannt': {\n"
    "      // Every ship of this id has been scanned - by any kind of scan.\n"
    "      if(!evSeen(ev.a)) return false;\n"
    "      for(const q of spawnQ) if(q.uid===ev.a) return false;\n"
    "      const us = byId(ev.a);\n"
    "      return us.length>0 && us.every(function(u){ return u.scanned; });\n"
    "    }\n"
    "    case 'erfuellt':\n",
    "evTrig: gescannt")

# ══ A mission may put the player into a hull of its own ════════════════
wv = replace_once(
    wv,
    "  missionObj = String(def.ziel || '').toUpperCase();\n",
    "  missionObj = String(def.ziel || '').toUpperCase();\n"
    "  if(def.ship) forceShip(def.ship);\n",
    "buildScripted: ship")

ui = replace_once(
    ui,
    "function shipStats(key){\n"
    "  for(const s of PLAYER_SHIPS) if(s.key===key) return s;\n",
    "// Hulls a mission can put the player into that no roster offers.\n"
    "const EXTRA_SHIPS = {\n"
    "  fipegasus: {key:'fipegasus', name:'GTF Pegasus', fac:'terran', spd:3.6, turn:0.17,\n"
    "              hp:80, sh:80, sec:20}\n"
    "};\n"
    "// The player's own hull while a mission lends another, or ''.\n"
    "let forcedPrev = '';\n"
    "function forceShip(key){\n"
    "  if(!forcedPrev) forcedPrev = player.ship;\n"
    "  applyShip(key);\n"
    "  notice(shipStats(key).name.toUpperCase()+' ASSIGNED', 'info');\n"
    "}\n"
    "// The next wave hands the player's own hull back, refitted.\n"
    "function releaseShip(){\n"
    "  if(!forcedPrev) return;\n"
    "  const k = forcedPrev; forcedPrev = '';\n"
    "  applyShip(k);\n"
    "}\n"
    "function shipStats(key){\n"
    "  for(const s of PLAYER_SHIPS) if(s.key===key) return s;\n"
    "  if(EXTRA_SHIPS[key]) return EXTRA_SHIPS[key];\n",
    "forced ship")

ui = replace_once(
    ui,
    "function shipSwapReady(){\n"
    "  if(GS!=='playing' || FS1_MODE || inJump()) return false;\n",
    "function shipSwapReady(){\n"
    "  if(GS!=='playing' || FS1_MODE || inJump()) return false;\n"
    "  if(forcedPrev) return false;      // this mission's hull is not negotiable\n",
    "no swap while forced")

fx = replace_once(
    fx,
    "  // Crossing into the next cycle hands over the fleet.\n"
    "  if(!FS1_MODE && !TEST_MODE){ const _c = cycleAt(wave); if(_c!==cycleNow) enterCycle(_c); }\n",
    "  // A hull lent for the last mission goes back first.\n"
    "  releaseShip();\n"
    "  // Crossing into the next cycle hands over the fleet.\n"
    "  if(!FS1_MODE && !TEST_MODE){ const _c = cycleAt(wave); if(_c!==cycleNow) enterCycle(_c); }\n",
    "nextWave: release")

fx = replace_once(
    fx,
    "  ITEMS=[];ticketFlash=0;TICKET_MSGS=[];SUB_MSGS=[];BAR_PULSE={};\n",
    "  ITEMS=[];ticketFlash=0;TICKET_MSGS=[];SUB_MSGS=[];BAR_PULSE={};forcedPrev='';\n",
    "new run: forced")

fx = replace_once(
    fx,
    "  tickScan();\n",
    "  tickScan();\n"
    "  tickSubScan();\n",
    "update: sub scan")

# ══ Guns do not aim at what they cannot lock ═══════════════════════════
cb = replace_once(
    cb,
    "    if(d<bd){ bd=d; best=a; }\n"
    "  }\n"
    "  return best || player;\n"
    "}\n",
    "    if(d<bd){ bd=d; best=a; }\n"
    "  }\n"
    "  // A ship that cannot be locked (the Pegasus) is not a target for the\n"
    "  // guns either; with nothing else in reach they hold fire.\n"
    "  return best || (canLockOn(player) ? player : null);\n"
    "}\n",
    "capGunTarget: stealth")
cb = replace_once(
    cb,
    "        const gt = capGunTarget(e);\n"
    "        const ga = ",
    "        const gt = capGunTarget(e);\n"
    "        if(!gt) continue;\n"
    "        const ga = ",
    "capitalFire: no target")

# ══ Missions 43 to 48 ══════════════════════════════════════════════════
wv = replace_once(
    wv,
    "       {t:'zerstoert', a:'V1', w:'nachschub', a2:'aus'}\n"
    "     ]}\n"
    "};\n",
    "       {t:'zerstoert', a:'V1', w:'nachschub', a2:'aus'}\n"
    "     ]},\n"
    "\n"
    "  43:{name:'Der NTF-Konvoi', fac:'ntf', o:'scan', live:5,\n"
    "      ziel:'SCAN THE TRITONS', u:[\n"
    "       // Three Tritons run for the right edge. They are to be scanned\n"
    "       // before anything else - until then they cannot be destroyed -\n"
    "       // and then the convoy is to be stopped for good.\n"
    "       {id:'T1', c:'fr', n:3, spr:'frtriton', escape:0.18, x:-60, scan:true,\n"
    "        scanFirst:true},\n"
    "       {id:'K1', c:'cr', n:1, spr:'ntfcraeolus'},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'gescannt', a:'T1', w:'ziel', a2:'DESTROY THE CONVOY'},\n"
    "       {t:'vernichtet', a:'T1', w:'zielerfuellt', a2:'CONVOY DESTROYED'},\n"
    "       {t:'verlaesst', a:'T1', w:'zielverfehlt', a2:'A TRITON GOT AWAY'}\n"
    "     ]},\n"
    "\n"
    "  44:{name:'Der Schwarm', fac:'ntf', o:'clear', live:7, u:[\n"
    "       // Wing after wing - the Tornado's hour. A Deimos to rearm at, and\n"
    "       // allied fighters on the player's side, with more of them later.\n"
    "       {id:'A1', c:'co', n:1, spr:'codeimos', side:'ally', still:true, hp:1.3},\n"
    "       {id:'W1', c:'fi', n:1, side:'ally'},\n"
    "       {id:'W2', c:'fi', n:1, side:'ally', wait:true},\n"
    "       {id:'E1', c:'fi', n:3},\n"
    "       {id:'E2', c:'fi', n:3, wait:true},\n"
    "       {id:'E3', c:'fi', n:3, wait:true},\n"
    "       {id:'B1', c:'bo', n:2, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'W2'},\n"
    "       {t:'alleZerstoert', a:'E2', w:'einwarpen', a2:'E3'},\n"
    "       {t:'alleZerstoert', a:'E2', w:'einwarpen', a2:'B1'}\n"
    "     ]},\n"
    "\n"
    "  45:{name:'Das Nadeloehr', fac:'ntf', o:'guard', live:5, crossEnds:true,\n"
    "      ziel:'GET THE ORION THROUGH', u:[\n"
    "       // Three NTF Fenris hold the line, each in her own lane and\n"
    "       // holding it. An Orion has to cross the field through them.\n"
    "       {id:'K1', c:'cr', n:1, spr:'ntfcrfenris', y:150, still:true},\n"
    "       {id:'K2', c:'cr', n:1, spr:'ntfcrfenris', y:265, still:true},\n"
    "       {id:'K3', c:'cr', n:1, spr:'ntfcrfenris', y:380, still:true},\n"
    "       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', crossSecs:70, hp:1.2},\n"
    "       {id:'E1', c:'fi', n:2}\n"
    "     ], ev:[\n"
    "       {t:'sek', a:3, w:'nachschub', a2:'an'},\n"
    "       {t:'verlaesst', a:'A1', w:'zielerfuellt', a2:'THE ORION IS THROUGH'},\n"
    "       {t:'verlaesst', a:'A1', w:'ende', a2:''},\n"
    "       {t:'vernichtet', a:'A1', w:'zielverfehlt', a2:'ORION LOST'},\n"
    "       {t:'vernichtet', a:'A1', w:'ende', a2:''}\n"
    "     ]},\n"
    "\n"
    "  46:{name:'Die Wissenschaftler', fac:'ntf', o:'clear', live:5,\n"
    "      ziel:'DISABLE THE FAUSTUS - NAVIGATION AND WEAPONS', u:[\n"
    "       // A Faustus parked under guard. She jumps when her deadline runs\n"
    "       // out - unless her navigation is gone. With navigation and weapons\n"
    "       // down an Argo comes to take her; until the Argo is lost she\n"
    "       // cannot be destroyed.\n"
    "       {id:'F1', c:'cr', n:1, spr:'scfaustus', still:true, x:560, y:250,\n"
    "        noFlak:true, capture:true, flee:60},\n"
    "       {id:'K1', c:'cr', n:1, spr:'ntfcraeolus'},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:1, wait:true},\n"
    "       {id:'T1', c:'tr', n:1, spr:'trargo', side:'ally', x:-40,\n"
    "        dockTo:'F1', wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'subsystem', a:'F1', b:'navigation+weapons', w:'einwarpen', a2:'T1'},\n"
    "       {t:'subsystem', a:'F1', b:'navigation+weapons', w:'ziel', a2:'COVER THE ARGO'},\n"
    "       {t:'angedockt', a:'T1', w:'kapern', a2:'F1'},\n"
    "       {t:'angedockt', a:'T1', w:'zielerfuellt', a2:'FAUSTUS CAPTURED'},\n"
    "       {t:'vernichtet', a:'T1', w:'freigeben', a2:'F1'},\n"
    "       {t:'vernichtet', a:'T1', w:'zielverfehlt', a2:'ARGO LOST'},\n"
    "       {t:'verlaesst', a:'F1', w:'zielverfehlt', a2:'THE FAUSTUS GOT AWAY'}\n"
    "     ]},\n"
    "\n"
    "  47:{name:'Die zweite Flucht', fac:'ntf', o:'clear', live:6,\n"
    "      ziel:'DESTROY THE HECATE', u:[\n"
    "       // A forlorn hope, and nobody on the player's side. The Iceni gets\n"
    "       // away - a minute, and no navigation to shoot - and comes back\n"
    "       // heavier for it. The Hecate does not have to.\n"
    "       {id:'V1', c:'ic', n:1, flee:60, navProof:true, fleeFree:true},\n"
    "       {id:'V2', c:'de', n:1, spr:'ntfdehecate'},\n"
    "       {id:'K1', c:'cr', n:1, spr:'ntfcraeolus'},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'B1', c:'bo', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'sek', a:2, w:'nachschub', a2:'an'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},\n"
    "       {t:'vernichtet', a:'V2', w:'zielerfuellt', a2:'HECATE DESTROYED'},\n"
    "       {t:'verlaesst', a:'V2', w:'zielverfehlt', a2:'THE HECATE WITHDREW'},\n"
    "       {t:'zerstoert', a:'V2', w:'nachschub', a2:'aus'}\n"
    "     ]},\n"
    "\n"
    "  48:{name:'Die Aufklaerung', fac:'ntf', o:'clear', live:4, ship:'fipegasus',\n"
    "      ziel:'SCAN THE NTD ORION - ALL FIVE SUBSYSTEMS', u:[\n"
    "       // The player flies a Pegasus for this one. Nothing can lock her -\n"
    "       // not the beams, not the missiles, not the destroyer's guns - but\n"
    "       // the fighters see her. Each subsystem of the Orion has to be\n"
    "       // held close until its ring fills. Then the Orion leaves.\n"
    "       {id:'V1', c:'de', n:1, spr:'ntfdeorion', still:true, x:520, y:260, scanSubs:true,\n"
    "        fleeFree:true},\n"
    "       {id:'E1', c:'fi', n:1},\n"
    "       {id:'E2', c:'fi', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'gescannt', a:'V1', w:'zielerfuellt', a2:'ORION SCANNED'},\n"
    "       {t:'gescannt', a:'V1', w:'raus', a2:'V1'}\n"
    "     ]}\n"
    "};\n",
    "missions 43-48")

open("src/30_waves.js", "w", encoding="utf-8").write(wv)
open("src/40_world.js", "w", encoding="utf-8").write(wo)
open("src/50_combat.js", "w", encoding="utf-8").write(cb)
open("src/60_effects.js", "w", encoding="utf-8").write(fx)
open("src/70_ui.js", "w", encoding="utf-8").write(ui)

# ── Test files ─────────────────────────────────────────────────────────
# The updated checks travel inside the patch, because .js files cannot be
# downloaded from the chat. Written last.
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
        'L2NvbnN0IEFMTFlfRkFDX09OID0gXHtbXn1dKlx9Oy8pWzBdOwpjb25zdCBleHRyYURlY2wgPSBz'
        'cmMubWF0Y2goL2NvbnN0IEVYVFJBX1NISVBTID0gKFx7W1xzXFNdKj9cblx9KTsvKVsxXTsKY29u'
        'c3QgaHVsbEZhY0RlY2wgPSBzcmMubWF0Y2goL2NvbnN0IEhVTExfRkFDID0gXHtbXHNcU10qP1x9'
        'Oy8pWzBdOwpjb25zdCBtZW51QmdEZWNsID0gc3JjLm1hdGNoKC9jb25zdCBNRU5VX0JHX0FMUEhB'
        'W1xzXFNdKj9jb25zdCBNRU5VX0JHX1BBRFxzKj1ccypbXGQuXSs7LylbMF07CmNvbnN0IGhhbmdh'
        'ckRlY2wgPSBzcmMubWF0Y2goL2NvbnN0IEhHX1dbXHNcU10qP1xuXF07LylbMF07CmNvbnN0IHRo'
        'ZW1lc0RlY2wgPSBzcmMubWF0Y2goL2NvbnN0IFRIRU1FUyA9IFx7W1xzXFNdKj9cblx9Oy8pWzBd'
        'OwovLyBUaGUgd2VhcG9uIHRhYmxlcyBhbmQgdGhlIHJlYXJtIHBhbmVsJ3MgbWVhc3VyZW1lbnRz'
        'Lgpjb25zdCB3cG5EZWNsICA9IHNyYy5tYXRjaCgvY29uc3QgUExBWUVSX0ZSX0JBU0VbXHNcU10q'
        'P1xuXF07LylbMF07CmNvbnN0IHdwbkRlY2wyID0gc3JjLm1hdGNoKC9jb25zdCBTRUNPTkRBUklF'
        'UyA9IFxbW1xzXFNdKj9cblxdOy8pWzBdOwpjb25zdCBybURlY2wgICA9IHNyYy5tYXRjaCgvY29u'
        'c3QgUk1fV1tcc1xTXSo/Y29uc3QgUk1fQ09MU19TRUMgPSBcW1tcc1xTXSo/XG5cXTsvKVswXTsK'
        'Ly8gcG9pbnRlckNvbnN1bWVkIHJlYWNoZXMgZm9yIHRoZSB0aXRsZSBvbiBhIGZpbmlzaGVkIHJ1'
        'bi4gU3RhcnRpbmcgYSBydW4KLy8gaXMgbm90IHdoYXQgdGhlc2UgZmlsZXMgdGVzdCwgc28gaXQg'
        'aXMgYSBzdHViLgpjb25zdCB3cG5TdGF0ZSA9ICdsZXQgcmVhcm1NZW51ID0gZmFsc2U7IGxldCBy'
        'ZXN1bWVIb2xkID0gZmFsc2U7JwogIC8vIFRoZSBiYXIgYXNrcyB3aGVyZSB0aGUgcG9pbnRlciBp'
        'cyBzaXR0aW5nOyBub3RoaW5nIGhvdmVycyBpbiBhIHRlc3QuCiAgKyAnIGNvbnN0IEhPVkVSID0g'
        'e3g6LTEsIHk6LTF9OyBmdW5jdGlvbiB0b1RpdGxlT3JMYXVuY2goKXt9OyBjb25zdCBXUE5fU0VF'
        'TiA9IHt9OyBjb25zdCBVSV9XRUFQT05TID0gZmFsc2U7JzsKCmNvbnN0IHZvbGxleURlY2wgPSBz'
        'cmMubWF0Y2goL2NvbnN0IFZPTExFWV9CQVNFW1xzXFNdKj9jb25zdCBWT0xMRVlfUEVSX0VYVFJB'
        'XHMqPVxzKltcZC5dKzsvKVswXTsKY29uc3QgbmFtZXMgPSBbCiAgJ3N5bmNDdXJzb3InLCdob3Zl'
        'cmluZycsCiAgJ3BhbmVsT3BlbicsJ2hvbGRSZXN1bWUnLCdjbGVhclJlc3VtZUhvbGQnLCdkcmF3'
        'UmVzdW1lSGludCcsCiAgJ2FwcGx5TG9hZG91dCcsJ3JlYXJtRnVsbCcsJ2N1clByaScsJ2N1clNl'
        'YycsJ3ByaURlZicsJ3NlY0RlZicsJ2h1bGxTZWNDbHMnLAogICd3ZWFwb25OYW1lJywnd2VhcG9u'
        'T3BlbicsJ3NlY29uZGFyaWVzRm9yJywnZGVmYXVsdFNlYycsJ2NvcnZldHRlT25GaWVsZCcsCiAg'
        'J3JlYXJtUmVhZHknLCdzZXRSZWFybU1lbnUnLCd0b2dnbGVSZWFybU1lbnUnLCdmaXRXZWFwb24n'
        'LCdyZWFybUxheW91dCcsCiAgJ2RyYXdSZWFybU1lbnUnLCdkcmF3UmVhcm1JY29uJywncmVhcm1H'
        'cm91cHMnLCdybVZhbHVlJywndGlja1dlYXBvblVubG9ja3MnLAogICd0aEZpdCcsJ2NhbGxNZW51'
        'TGF5b3V0JywnZHJhd0FsbHlSb3cnLCdkcmF3S2V5Q2hpcCcsJ2RyYXdIdWxsQ2VsbCcsJ2h1bGxD'
        'bGFzcycsJ2lzQm9tYmVySHVsbCcsJ3NoaXBTdGF0cycsJ2FwcGx5U2hpcCcsJ3RpY2tTaGlwVW5s'
        'b2NrcycsJ3NoaXBTd2FwUmVhZHknLAogICdzZXRTaGlwTWVudScsJ3RvZ2dsZVNoaXBNZW51Jywn'
        'c3dhcFNoaXAnLCdkcmF3U3dhcEljb24nLCdzdGF0UGlwcycsJ2RyYXdTaGlwTWVudScsJ3BvaW50'
        'ZXJDb25zdW1lZCcsCiAgJ3Jlc2V0UGxheWVyU2hpZWxkJywncGxheWVyU2MnLCdzZXRDYWxsTWVu'
        'dScsCiAgJ2h1bGxGYWMnLCdzaGlwRmFjJywnaGFuZ2FyU2VydmVzJywnaXNIYW5nYXJTaGlwJywn'
        'aGFuZ2FyRmFjcycsJ2NvbG9zc3VzT25GaWVsZCcsJ3NoaXBPZmZlcmVkJywKICAnbW91bnRzRm9y'
        'Jywnc3ByaXRlRmFjaW5nJywnZHJhd0h1bGxCZycsJ2RyYXdIdWxsQ2VsbCcsJ3ZvbGxleURtZycs'
        'J3ZvbGxleVRvdGFsJywncHJpbWFyeUNvdW50Jywnc3luY1BhdXNlJywKICAnaGFuZ2FyR3JvdXBz'
        'JywnaGFuZ2FyTGF5b3V0JywnZHJhd01pc3NpbGVJY29uJywnZHJhd0JvbWJJY29uJywnZHJhd0tl'
        'eUNoaXAnLAogICdoYW5nYXJPcmRlcicsJ2luc2lkZVBhbmVsJywnY3ljbGVBdCcsJ2VudGVyQ3lj'
        'bGUnLCd0aXRsZUZzSGl0JywnZm9yY2VTaGlwJywncmVsZWFzZVNoaXAnLAogICd0aENoYW1mZXJQ'
        'YXRoJywndGhQbGF0ZScsJ3RoR2xvd1BhdGgnLCd0aEJyYWNrZXRzJywndGhTY2FsZScsJ3RoRnJh'
        'bWUnLCd0aFJHQkEnLCd0aEdsb3NzJywndGhDdXRHbGludCcsCiAgJ1RIJywndGhMYWJlbCcsJ3Ro'
        'VmFsdWUnLCd0aEJldmVsJywndGhHbG93JywndGhQYW5lbCcsJ3RoQnV0dG9uJywndGhEaXZpZGVy'
        'JywnZHJhd1N3YXBJY29uJywnVUknLCd1aUhMUCcsJ3VpTGFiZWwnLCd1aVZhbHVlJywndWlDZWxs'
        'JywndWlEaWFsb2cnXTsKY29uc3Qga2V5SGFuZGxlciA9IGJldHdlZW4oImRvY3VtZW50LmFkZEV2'
        'ZW50TGlzdGVuZXIoJ2tleWRvd24nLGZ1bmN0aW9uKGV2KXtcbiAgaWYoR1MhPT0ncGxheWluZycp'
        'IHJldHVybjsiKTsKY29uc3QgZG93blN0YXJ0ID0gc3JjLmluZGV4T2YoIkNWUy5hZGRFdmVudExp'
        'c3RlbmVyKCdtb3VzZWRvd24nLCIpOwpjb25zdCBtb3VzZUhhbmRsZXIgPSBzcmMuc2xpY2Uoc3Jj'
        'LmluZGV4T2YoJ2Z1bmN0aW9uJywgZG93blN0YXJ0KSwgYmxvY2tFbmQoc3JjLCBzcmMuaW5kZXhP'
        'ZignZnVuY3Rpb24nLCBkb3duU3RhcnQpKSk7CmNvbnN0IGxhdW5jaCA9IGZuKCdsYXVuY2hHYW1l'
        'Jyk7Cgpjb25zdCBDQUxMUyA9IFtdOwpjb25zdCBjdHhTdHViID0gbmV3IFByb3h5KHt9LCB7CiAg'
        'Z2V0Oih0LGspPT4gayBpbiB0ID8gdFtrXSA6IGZ1bmN0aW9uKCl7CiAgICBDQUxMUy5wdXNoKHtm'
        'bjpTdHJpbmcoayksIGFyZ3M6W10uc2xpY2UuY2FsbChhcmd1bWVudHMpfSk7CiAgICAvLyBjcmVh'
        'dGVMaW5lYXJHcmFkaWVudCBoYXMgdG8gaGFuZCBiYWNrIHNvbWV0aGluZyB3aXRoIGFkZENvbG9y'
        'U3RvcC4KICAgIGlmKGs9PT0nY3JlYXRlTGluZWFyR3JhZGllbnQnKSByZXR1cm4ge2FkZENvbG9y'
        'U3RvcDpmdW5jdGlvbigpe319OwogICAgLy8gdGhGaXQgbWVhc3VyZXMgYmVmb3JlIGl0IGN1dHMs'
        'IHNvIHRoZSBzdHViIGhhcyB0byBhbnN3ZXIgd2l0aCBhIHdpZHRoLgogICAgLy8gUm91Z2hseSAw'
        'LjU1IG9mIHRoZSBzZXQgcG9pbnQgc2l6ZSBwZXIgY2hhcmFjdGVyIGlzIGNsb3NlIGVub3VnaCBm'
        'b3IKICAgIC8vIHRoZSBsYXlvdXQgZGVjaXNpb25zIGJlaW5nIGNoZWNrZWQgaGVyZS4KICAgIGlm'
        'KGs9PT0nbWVhc3VyZVRleHQnKXsKICAgICAgY29uc3QgcHggPSBwYXJzZUZsb2F0KFN0cmluZyh0'
        'LmZvbnR8fCcxMHB4JykucmVwbGFjZSgvXmJvbGRccysvLCcnKSkgfHwgMTA7CiAgICAgIHJldHVy'
        'biB7d2lkdGg6IFN0cmluZyhhcmd1bWVudHNbMF18fCcnKS5sZW5ndGggKiBweCAqIDAuNTV9Owog'
        'ICAgfQogIH0sCiAgc2V0Oih0LGssdik9PnsgQ0FMTFMucHVzaCh7Zm46J3NldCAnK1N0cmluZyhr'
        'KSwgYXJnczpbdl19KTsgdFtrXT12OyByZXR1cm4gdHJ1ZTsgfQp9KTsKLy8gSGVscGVycyBvdmVy'
        'IHRoZSByZWNvcmRlZCBkcmF3aW5nIGNhbGxzLgpjb25zdCBDTFIgICAgPSAoKT0+eyBDQUxMUy5s'
        'ZW5ndGggPSAwOyB9Owpjb25zdCBkcmF3cyAgPSAoKT0+IENBTExTLmZpbHRlcihjPT5jLmZuPT09'
        'J2RyYXdJbWFnZScpOwpjb25zdCBjbGlwcyAgPSAoKT0+IENBTExTLmZpbHRlcihjPT5jLmZuPT09'
        'J2NsaXAnKTsKY29uc3QgYWxwaGFzID0gKCk9PiBDQUxMUy5maWx0ZXIoYz0+Yy5mbj09PSdzZXQg'
        'Z2xvYmFsQWxwaGEnKS5tYXAoYz0+Yy5hcmdzWzBdKTsKLy8gRXZlcnkgc3ByaXRlIGhhcyB0byBz'
        'aXQgaW5zaWRlIGEgc2F2ZS9yZXN0b3JlIHBhaXIsIG90aGVyd2lzZSBpdHMgY2xpcCBhbmQKLy8g'
        'aXRzIGFscGhhIGxlYWsgaW50byB3aGF0ZXZlciBpcyBkcmF3biBuZXh0LgpmdW5jdGlvbiBiYWxh'
        'bmNlZCgpewogIGxldCBkID0gMCwgb2tBbGwgPSB0cnVlOwogIGZvcihjb25zdCBjIG9mIENBTExT'
        'KXsKICAgIGlmKGMuZm49PT0nc2F2ZScpIGQrKzsKICAgIGVsc2UgaWYoYy5mbj09PSdyZXN0b3Jl'
        'Jyl7IGQtLTsgaWYoZDwwKSBva0FsbD1mYWxzZTsgfQogICAgZWxzZSBpZigoYy5mbj09PSdkcmF3'
        'SW1hZ2UnIHx8IGMuZm49PT0nY2xpcCcpICYmIGQ8MSkgb2tBbGw9ZmFsc2U7CiAgfQogIHJldHVy'
        'biBva0FsbCAmJiBkPT09MDsKfQoKY29uc3Qgd29ybGQgPSBgCiAgY29uc3QgVz04MDAsSD01MDAs'
        'SFVEX0g9NTQsIFBMQVlFUl9TUERfRklHSFRFUj0zLjIsIFBMQVlFUl9TUERfQk9NQkVSPTIuNCwg'
        'UExBWUVSX1RVUk49MC4xNDsKICBsZXQgRlMxX01PREU9ZmFsc2UsIEdTPSdwbGF5aW5nJywgcGF1'
        'c2VkPWZhbHNlLCBjYWxsTWVudT1mYWxzZSwgd2F2ZT0xLCBzY29yZT0wLCBhbGxpZXM9W10sIGp1'
        'bXA9ZmFsc2U7CiAgbGV0IHNldHRpbmdzT3Blbj1mYWxzZSwgdXNlclBhdXNlZD1mYWxzZTsKICBs'
        'ZXQgU1VCX01TR1M9W10sIE1PVVNFPXt4OjAseTowfSwgbGl2ZXM9MywgcGxheWVyPXt4OjEwMCx5'
        'OjIwMCxodWxsTXVsdDoxfTsKICAvLyBOb3RpY2VzIGdvIHRvIHRoZSBjb2x1bW4gdW5kZXIgdGhl'
        'IG9iamVjdGl2ZSBsaW5lOyB0aGUgY29sdW1uIGl0c2VsZgogIC8vIGlzIG5vdCB1bmRlciB0ZXN0'
        'IGhlcmUsIG9ubHkgd2hhdCBpcyBhbm5vdW5jZWQuCiAgbGV0IE5PVElDRV9MT0c9W107IGZ1bmN0'
        'aW9uIG5vdGljZSh0LCB0b25lKXsgTk9USUNFX0xPRy5wdXNoKHt0eHQ6dCwgdG9uZTp0b25lfSk7'
        'IH0KICAvLyBUaGUgYmFyJ3MgYXR0ZW50aW9uIHB1bHNlcyBhcmUgdGhlIGZpZWxkIHNpbXVsYXRp'
        'b24ncyBidXNpbmVzcy4KICBsZXQgQkFSX1BVTFNFPXt9OyBmdW5jdGlvbiBiYXJQdWxzZUxldmVs'
        'KCl7IHJldHVybiAwOyB9IGZ1bmN0aW9uIGJhclB1bHNlKCl7fQogIC8vIEEgaHVsbCBsZW50IGJ5'
        'IGEgbWlzc2lvbiAoc2VlIGZvcmNlU2hpcCkuCiAgbGV0IGZvcmNlZFByZXY9Jyc7CiAgbGV0IGVy'
        'YU9mZj1mYWxzZSwgSU1HUz17fSwgaXNGaXJpbmc9ZmFsc2UsIGxhdW5jaGVkPTA7CiAgY29uc3Qg'
        'Y3R4PUNUWCwgZG9jdW1lbnQ9e2JvZHk6e2NsYXNzTGlzdDp7YWRkKCl7fSxyZW1vdmUoKXt9fX0s'
        'IGdldEVsZW1lbnRCeUlkKCl7cmV0dXJuIHtzdHlsZTp7fX07fX07CiAgY29uc3Qgd2luZG93PXt9'
        'OwogIGZ1bmN0aW9uIGluSnVtcCgpe3JldHVybiBqdW1wO30gZnVuY3Rpb24gZXJhU2hpZWxkc09m'
        'Zigpe3JldHVybiBlcmFPZmY7fQogIGZ1bmN0aW9uIHNldFNldHRpbmdzKCl7fSBmdW5jdGlvbiB0'
        'b2dnbGVGdWxsc2NyZWVuKCl7fSBmdW5jdGlvbiByZWZpbmVUaWNrZXQoKXt9IGZ1bmN0aW9uIGNh'
        'bGxBbGx5KCl7fQogIGZ1bmN0aW9uIGFsbHlSZWFkeSgpe3JldHVybiB0cnVlO30gZnVuY3Rpb24g'
        'dG9nZ2xlQ2FsbE1lbnUoKXt9IGZ1bmN0aW9uIHRvR0MoeCx5KXtyZXR1cm4ge3g6eCx5Onl9O30K'
        'ICBsZXQgc2hpcFVubG9ja2VkPTEsIHNoaXBTd2FwV2F2ZT0tMSwgc2hpcE1lbnU9ZmFsc2UsIGdh'
        'bWVPdmVyQXQ9MDsKICBjb25zdCBBTExZX0tFWVM9W10sIEFMTFlfT1JERVI9W10sIEFMTFlfU1BF'
        'Q0lBTD0neCcsIEFMTFlfU1BFQ0lBTF9LRVk9J1EnOwogICR7aHVsbEZhY0RlY2x9CiAgJHt3cG5E'
        'ZWNsfQogICR7d3BuRGVjbDJ9CiAgJHtybURlY2x9CiAgJHt3cG5TdGF0ZX0KICAke3RoZW1lc0Rl'
        'Y2x9CiAgbGV0IEVDTz17aHVkOidobHAnLCBzY2hlbWU6J2ZpcmUnfTsKICAke21lbnVCZ0RlY2x9'
        'CiAgJHtoYW5nYXJEZWNsfQogICR7dm9sbGV5RGVjbH0KICBsZXQgTU9VTlRTPXt9OwogICR7c2hp'
        'cHNEZWNsfQogIGxldCBVSV9TSElQUz0xOwogIGNvbnN0IEVYVFJBX1NISVBTID0gJHtleHRyYURl'
        'Y2x9OwogICR7ZmFjT25EZWNsfQogICR7Y3ljbGVEZWNsfQogICR7bmFtZXMubWFwKGZuKS5qb2lu'
        'KCdcbicpfQogIGNvbnN0IG9uS2V5ID0gJHtrZXlIYW5kbGVyfTsKICBjb25zdCBvbkRvd24gPSAk'
        'e21vdXNlSGFuZGxlcn07CiAgcmV0dXJuIHsKICAgIGdldDooayk9PmV2YWwoayksIHNldDooayx2'
        'KT0+ZXZhbChrKyc9dicpLCBydW46KGNvZGUpPT5ldmFsKGNvZGUpCiAgfTtgOwpjb25zdCBXID0g'
        'bmV3IEZ1bmN0aW9uKCdDVFgnLCB3b3JsZCkoY3R4U3R1Yik7CmxldCBmYWlscyA9IDA7CmZ1bmN0'
        'aW9uIG9rKGxhYmVsLCBjb25kKXsgY29uc29sZS5sb2coKGNvbmQ/JyAgb2sgICAgJzonICBGQUlM'
        'ICAnKStsYWJlbCk7IGlmKCFjb25kKSBmYWlscysrOyB9CmNvbnN0IFAgPSAoKT0+Vy5nZXQoJ3Bs'
        'YXllcicpOwpjb25zdCByZXNldCA9ICgpPT57IFcucnVuKCJHUz0ncGxheWluZyc7cGF1c2VkPWZh'
        'bHNlO3Jlc3VtZUhvbGQ9ZmFsc2U7Y2FsbE1lbnU9ZmFsc2U7c2hpcE1lbnU9ZmFsc2U7d2F2ZT0x'
        'O3Njb3JlPTA7YWxsaWVzPVtdO2p1bXA9ZmFsc2U7RlMxX01PREU9ZmFsc2U7c2hpcFVubG9ja2Vk'
        'PTE7c2hpcFN3YXBXYXZlPS0xO1NVQl9NU0dTPVtdO05PVElDRV9MT0c9W107cGxheWVyPXt4OjEw'
        'MCx5OjIwMCxodWxsTXVsdDoxfTthcHBseVNoaXAoUExBWUVSX1NISVBTWzBdLmtleSkiKTsgfTsK'
        'Y29uc3QgZGVzdHJveWVyID0gKG8pPT5PYmplY3QuYXNzaWduKHtpbWc6J2RlaGF0c2hlcHN1dCcs'
        'IHNtYWxsOmZhbHNlLCBkZWFkOmZhbHNlLCB3YXJwT3V0OmZhbHNlfSwgb3x8e30pOwoKY29uc29s'
        'ZS5sb2coJ1N0YXJ0IHNoaXAnKTsKcmVzZXQoKTsKb2soJ3N0YXJ0cyBpbiB0aGUgVGhvdGgnLCBQ'
        'KCkuc2hpcD09PSdmaXRvdGgnKTsKb2soJ1Rob3RoIHN0YXRzIDMuNSAvIDAuMTcgLyAxMDAgLyAx'
        'MDAgLyAyMCBtaXNzaWxlcycsIFAoKS5zcGQ9PT0zLjUgJiYgUCgpLnR1cm49PT0wLjE3ICYmIFAo'
        'KS5tYXhIcD09PTEwMCAmJiBQKCkubWF4U2g9PT0xMDAgJiYgUCgpLnNlY01heD09PTIwICYmIFAo'
        'KS5zZWNUeXBlPT09J21pc3NpbGUnKTsKCmNvbnNvbGUubG9nKCdVbmxvY2tzJyk7CnJlc2V0KCk7'
        'ClcucnVuKCJzY29yZT0zOTk5OyB0aWNrU2hpcFVubG9ja3MoKSIpOyBvaygnMzk5OSBwb2ludHM6'
        'IG5vdGhpbmcgdW5sb2NrZWQnLCBXLmdldCgnc2hpcFVubG9ja2VkJyk9PT0xKTsKVy5ydW4oInNj'
        'b3JlPTQwMDA7IHRpY2tTaGlwVW5sb2NrcygpIik7IG9rKCc0MDAwIHBvaW50czogSG9ydXMgdW5s'
        'b2NrZWQsIG9uZSBtZXNzYWdlJywgVy5nZXQoJ3NoaXBVbmxvY2tlZCcpPT09MiAmJiBXLmdldCgn'
        'Tk9USUNFX0xPRycpLmxlbmd0aD09PTEgJiYgL0hPUlVTLy50ZXN0KFcuZ2V0KCdOT1RJQ0VfTE9H'
        'JylbMF0udHh0KSk7ClcucnVuKCJzY29yZT0yMzAwMDsgdGlja1NoaXBVbmxvY2tzKCkiKTsgb2so'
        'J2p1bXAgdG8gMjMwMDA6IE9zaXJpcywgU2VyYXBpcywgU2V0aCBhdCBvbmNlJywgVy5nZXQoJ3No'
        'aXBVbmxvY2tlZCcpPT09NSAmJiBXLmdldCgnTk9USUNFX0xPRycpLmxlbmd0aD09PTQpOwpXLnJ1'
        'bigic2NvcmU9OTk5OTk5OyB0aWNrU2hpcFVubG9ja3MoKSIpOyBvaygnbmV2ZXIgcGFzdCB0aGUg'
        'ZW5kIG9mIHRoZSBsaXN0JywgVy5nZXQoJ3NoaXBVbmxvY2tlZCcpPT09OCk7ClcucnVuKCJ0aWNr'
        'U2hpcFVubG9ja3MoKSIpOyBvaygnc2V2ZW4gdW5sb2NrIG1lc3NhZ2VzIGluIHRvdGFsLCBub25l'
        'IHJlcGVhdGVkJywgVy5nZXQoJ05PVElDRV9MT0cnKS5sZW5ndGg9PT03KTsKcmVzZXQoKTsgVy5y'
        'dW4oIkZTMV9NT0RFPXRydWU7IHNjb3JlPTk5OTk5OyB0aWNrU2hpcFVubG9ja3MoKSIpOyBvaygn'
        'RlMxIG1vZGU6IG5vIHVubG9ja3MnLCBXLmdldCgnc2hpcFVubG9ja2VkJyk9PT0xKTsKcmVzZXQo'
        'KTsgVy5ydW4oIkdTPSdnYW1lb3Zlcic7IHNjb3JlPTk5OTk5OyB0aWNrU2hpcFVubG9ja3MoKSIp'
        'OyBvaygnbm90IG91dHNpZGUgcGxheScsIFcuZ2V0KCdzaGlwVW5sb2NrZWQnKT09PTEpOwoKY29u'
        'c29sZS5sb2coJ1doZW4gdGhlIHN3aXRjaCBpcyBhdmFpbGFibGUnKTsKY29uc3QgcmVhZHkgPSAo'
        'c2V0dXApPT57IHJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBzZXR1cCgpOyByZXR1'
        'cm4gVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpOyB9Owpvaygnbm8gZGVzdHJveWVyOiBub3QgcmVh'
        'ZHknLCByZWFkeSgoKT0+e30pPT09ZmFsc2UpOwpvaygnYWxsaWVkIFZhc3VkYW4gZGVzdHJveWVy'
        'OiByZWFkeScsIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKSk9PT10cnVl'
        'KTsKb2soJ05URiBodWxsIChudGZkZWhlY2F0ZSkgaXMgVGVycmFuLCBubyBUZXJyYW4gaHVsbHMg'
        'ZXhpc3Q6IG5vdCByZWFkeScsCiAgIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVy'
        'KHtpbWc6J250ZmRlaGVjYXRlJ30pXSkpPT09ZmFsc2UpOwpvaygnY3J1aXNlciBvbmx5OiBub3Qg'
        'cmVhZHknLCByZWFkeSgoKT0+Vy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7aW1nOidjcm1lbnR1'
        'J30pXSkpPT09ZmFsc2UpOwpvaygnQ29sb3NzdXMgYWxvbmUgaXMgYSBqb2ludCB5YXJkOiByZWFk'
        'eScsCiAgIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKHtpbWc6J3NkY29sb3Nz'
        'dXMnLCBjb2xvc3N1czp0cnVlfSldKSk9PT10cnVlKTsKb2soJ2RlYWQgZGVzdHJveWVyOiBub3Qg'
        'cmVhZHknLCByZWFkeSgoKT0+Vy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7ZGVhZDp0cnVlfSld'
        'KSk9PT1mYWxzZSk7Cm9rKCdkZXN0cm95ZXIgd2FycGluZyBvdXQ6IG5vdCByZWFkeScsIHJlYWR5'
        'KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKHt3YXJwT3V0OnRydWV9KV0pKT09PWZhbHNl'
        'KTsKb2soJ29ubHkgdGhlIHN0YXJ0IHNoaXAgdW5sb2NrZWQ6IG5vdCByZWFkeScsIHJlYWR5KCgp'
        'PT57IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bignc2hpcFVubG9ja2VkPTEn'
        'KTsgfSk9PT1mYWxzZSk7Cm9rKCdkdXJpbmcgYSBqdW1wOiBub3QgcmVhZHknLCByZWFkeSgoKT0+'
        'eyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ2p1bXA9dHJ1ZScpOyB9KT09'
        'PWZhbHNlKTsKb2soJ0ZTMSBtb2RlOiBub3QgcmVhZHknLCByZWFkeSgoKT0+eyBXLnNldCgnYWxs'
        'aWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ0ZTMV9NT0RFPXRydWUnKTsgfSk9PT1mYWxzZSk7'
        'Cgpjb25zb2xlLmxvZygnU3dpdGNoaW5nJyk7CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9'
        'MzsgcGxheWVyLmhwPTEyOyBwbGF5ZXIuc2g9NTsgcGxheWVyLnNlY0FtbW89MSIpOyBXLnNldCgn'
        'YWxsaWVzJyxbZGVzdHJveWVyKCldKTsKVy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsgb2soJ2J1'
        'dHRvbiBvcGVucyB0aGUgbWVudSBhbmQgcGF1c2VzJywgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVl'
        'ICYmIFcuZ2V0KCdwYXVzZWQnKT09PXRydWUpOwpXLnJ1bigic3dhcFNoaXAoJ2Zpc2VyYXBpcycp'
        'Iik7IG9rKCdsb2NrZWQgaHVsbCAoU2VyYXBpcykgcmVmdXNlZCcsIFAoKS5zaGlwPT09J2ZpdG90'
        'aCcgJiYgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlKTsKVy5ydW4oInN3YXBTaGlwKCdmaXRvdGgn'
        'KSIpOyBvaygnY3VycmVudCBodWxsIHJlZnVzZWQnLCBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUg'
        'JiYgVy5nZXQoJ3NoaXBTd2FwV2F2ZScpPT09LTEpOwpXLnJ1bigic3dhcFNoaXAoJ2Jvb3Npcmlz'
        'JykiKTsKLy8gVGhlIHBhbmVsIGNsb3NlcywgYnV0IHRoZSBnYW1lIHN0YXlzIHN0b3BwZWQ6IGNv'
        'bWluZyBiYWNrIGludG8gdGhlCi8vIGZpZ2h0IGlzIHRoZSBwbGF5ZXIncyB0byB0aW1lIG5vdywg'
        'd2hhdGV2ZXIgdGhlIHBhbmVsIGFuZCBob3dldmVyIGl0Ci8vIHdhcyBsZWZ0LgpvaygnT3Npcmlz'
        'IHRha2VuIGFuZCB0aGUgbWVudSBjbG9zZWQnLCBQKCkuc2hpcD09PSdib29zaXJpcycgJiYgVy5n'
        'ZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7Cm9rKCdidXQgdGhlIGdhbWUgaXMgc3RpbGwgaGVsZCcs'
        'IFcuZ2V0KCdwYXVzZWQnKT09PXRydWUgJiYgVy5nZXQoJ3Jlc3VtZUhvbGQnKT09PXRydWUpOwpX'
        'LnJ1bigncG9pbnRlckNvbnN1bWVkKHt4OjQwMCx5OjMwMH0pJyk7Cm9rKCdhbmQgb25lIHRhcCBw'
        'dXRzIHlvdSBiYWNrIGluIGl0JywgVy5nZXQoJ3BhdXNlZCcpPT09ZmFsc2UgJiYgVy5nZXQoJ3Jl'
        'c3VtZUhvbGQnKT09PWZhbHNlKTsKb2soJ09zaXJpcyBzdGF0cyAyLjUgLyAwLjEwIC8gMTQwIC8g'
        'MTAwIC8gMTAgYm9tYnMnLCBQKCkuc3BkPT09Mi41ICYmIFAoKS50dXJuPT09MC4xMCAmJiBQKCku'
        'bWF4SHA9PT0xNDAgJiYgUCgpLm1heFNoPT09MTAwICYmIFAoKS5zZWNNYXg9PT0xMCAmJiBQKCku'
        'c2VjVHlwZT09PSdib21iJyk7Cm9rKCdyZWZpbGxlZDogaHVsbCAxNDAsIHNoaWVsZHMgMTAwLCAx'
        'MCBib21icycsIFAoKS5ocD09PTE0MCAmJiBQKCkuc2g9PT0xMDAgJiYgUCgpLnNlY0FtbW89PT0x'
        'MCk7Cm9rKCdzd2l0Y2ggc3BlbnQgZm9yIHRoaXMgd2F2ZScsIFcucnVuKCdzaGlwU3dhcFJlYWR5'
        'KCknKT09PWZhbHNlKTsKVy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsgb2soJ21lbnUgZG9lcyBu'
        'b3Qgb3BlbiBhZ2FpbiB0aGlzIHdhdmUnLCBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKVy5y'
        'dW4oJ3dhdmU9MicpOyBvaygnbmV4dCB3YXZlOiBhdmFpbGFibGUgYWdhaW4nLCBXLnJ1bignc2hp'
        'cFN3YXBSZWFkeSgpJyk9PT10cnVlKTsKCmNvbnNvbGUubG9nKCdDeWNsZSBzY2FsaW5nIGFuZCBz'
        'aGllbGRzJyk7CnJlc2V0KCk7IFcucnVuKCJwbGF5ZXIuaHVsbE11bHQ9MS41OyBzaGlwVW5sb2Nr'
        'ZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKVy5ydW4oInRvZ2dsZVNoaXBN'
        'ZW51KCk7IHN3YXBTaGlwKCdib3Nla2htZXQnKSIpOyBvaygnU2VraG1ldCBhdCBjeWNsZSB4MS41'
        'OiBodWxsIDIxMCcsIFAoKS5tYXhIcD09PTIxMCAmJiBQKCkuaHA9PT0yMTApOwpyZXNldCgpOyBX'
        'LnJ1bigiZXJhT2ZmPXRydWU7IHNoaXBVbmxvY2tlZD0yIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0'
        'cm95ZXIoKV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAoJ2ZpaG9ydXMnKSIp'
        'OyBvaygnZXJhIHdpdGhvdXQgc2hpZWxkczogc2hpZWxkcyBzdGF5IDAnLCBQKCkuc2g9PT0wICYm'
        'IFAoKS5tYXhTaD09PTEwMCk7ClcucnVuKCdlcmFPZmY9ZmFsc2UnKTsKCmNvbnNvbGUubG9nKCdD'
        'YWxsIG1lbnUgYW5kIHN3aXRjaCBtZW51IGV4Y2x1ZGUgZWFjaCBvdGhlcicpOwpyZXNldCgpOyBX'
        'LnJ1bigic2hpcFVubG9ja2VkPTI7IGNhbGxNZW51PXRydWU7IHBhdXNlZD10cnVlIik7IFcuc2V0'
        'KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOwpXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOyBvaygn'
        'b3BlbmluZyB0aGUgc3dpdGNoIGNsb3NlcyB0aGUgY2FsbCBtZW51JywgVy5nZXQoJ2NhbGxNZW51'
        'Jyk9PT1mYWxzZSAmJiBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUpOwoKY29uc29sZS5sb2coJ01l'
        'bnUgZHJhd2luZyBhbmQgdGFwcycpOwpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTMiKTsg'
        'Vy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7IFcucnVuKCd0b2dnbGVTaGlwTWVudSgpOyBk'
        'cmF3U2hpcE1lbnUoKScpOwpjb25zdCByZWN0cyA9IFcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycp'
        'Owpjb25zdCByb3dPZiA9IChrZXkpPT5XLnJ1bignd2luZG93Ll9zaGlwUmVjdHMnKS5maW5kKHI9'
        'PnIuc2hpcD09PWtleSk7Cm9rKCdlaWdodCByb3dzIGRyYXduJywgcmVjdHMubGVuZ3RoPT09OCk7'
        'Cm9rKCdtZW51IGZpdHMgb24gdGhlIDgwMHg1MDAgZmllbGQnLCByZWN0cy5ldmVyeShyPT5yLng+'
        'PTAgJiYgci55Pj0wICYmIHIueCtyLnc8PTgwMCAmJiByLnkrci5oPD01MDApKTsKb2soJ2ZpZ2h0'
        'ZXJzIGZpcnN0LCB0aGVuIGJvbWJlcnMnLAogICByZWN0cy5tYXAocj0+ci5zaGlwKS5qb2luKCk9'
        'PT0nZml0b3RoLGZpaG9ydXMsZmlzZXJhcGlzLGZpc2V0aCxmaXRhdXJldCxib29zaXJpcyxib2Jh'
        'a2hhLGJvc2VraG1ldCcpOwpvaygnZXZlcnkgcm93IGlzIGZ1bGwgd2lkdGggYW5kIHRoZXkgZG8g'
        'bm90IG92ZXJsYXAnLAogICByZWN0cy5ldmVyeShyPT5yLnc9PT1yZWN0c1swXS53KSAmJgogICBy'
        'ZWN0cy5ldmVyeSgocixpKT0+aT09PTAgfHwgci55ID49IHJlY3RzW2ktMV0ueStyZWN0c1tpLTFd'
        'LmgpKTsKb2soJ2EgbG9ja2VkIHJvdyBpcyB0aGlubmVyIHRoYW4gb25lIHRoYXQgY2FuIGJlIHRh'
        'a2VuJywKICAgcm93T2YoJ2JvYmFraGEnKS5oIDwgcm93T2YoJ2ZpaG9ydXMnKS5oKTsKb2soJ29u'
        'bHkgSG9ydXMgYW5kIE9zaXJpcyBhcmUgdGFwcGFibGUnLCByZWN0cy5maWx0ZXIocj0+ci5rZXkp'
        'Lm1hcChyPT5yLmtleSkuam9pbigpPT09J2ZpaG9ydXMsYm9vc2lyaXMnKTsKY29uc3QgbG9ja2Vk'
        'ID0gcm93T2YoJ2JvYmFraGEnKTsKVy5ydW4oYHBvaW50ZXJDb25zdW1lZCh7eDoke2xvY2tlZC54'
        'KzV9LHk6JHtsb2NrZWQueSs1fX0pYCk7IG9rKCd0YXAgb24gbG9ja2VkIEJha2hhIGtlZXBzIHRo'
        'ZSBtZW51IG9wZW4nLCBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUgJiYgUCgpLnNoaXA9PT0nZml0'
        'b3RoJyk7CmNvbnN0IGhvcnVzID0gcm93T2YoJ2ZpaG9ydXMnKTsKVy5ydW4oYHBvaW50ZXJDb25z'
        'dW1lZCh7eDoke2hvcnVzLngrNX0seToke2hvcnVzLnkrNX19KWApOyBvaygndGFwIG9uIEhvcnVz'
        'IHN3aXRjaGVzJywgUCgpLnNoaXA9PT0nZmlob3J1cycgJiYgVy5nZXQoJ3NoaXBNZW51Jyk9PT1m'
        'YWxzZSk7CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBXLnNldCgnYWxsaWVzJyxb'
        'ZGVzdHJveWVyKCldKTsgVy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsKVy5ydW4oJ3BvaW50ZXJD'
        'b25zdW1lZCh7eDoyLHk6Mn0pJyk7IG9rKCd0YXAgb3V0c2lkZSBjbG9zZXMgd2l0aG91dCBzd2l0'
        'Y2hpbmcnLCBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlICYmIFAoKS5zaGlwPT09J2ZpdG90aCcg'
        'JiYgVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpPT09dHJ1ZSk7Cm9rKCdjYW5jZWxsaW5nIGhvbGRz'
        'IHRoZSBwYXVzZSBqdXN0IHRoZSBzYW1lJywgVy5nZXQoJ3Jlc3VtZUhvbGQnKT09PXRydWUpOwpX'
        'LnJ1bignY2xlYXJSZXN1bWVIb2xkKCknKTsKVy5ydW4oIndpbmRvdy5fc2hpcEJ0blJlY3Q9e3g6'
        'Njk1LHk6NCx3OjIyLGg6MjB9OyBwb2ludGVyQ29uc3VtZWQoe3g6NzAwLHk6MTB9KSIpOyBvaygn'
        'dGFwIG9uIHRoZSBiYXIgYnV0dG9uIG9wZW5zIHRoZSBtZW51JywgVy5nZXQoJ3NoaXBNZW51Jyk9'
        'PT10cnVlKTsKCmNvbnNvbGUubG9nKCdUaGUgcGFuZWwgc3dhbGxvd3MgaXRzIG93biBjbGlja3Mn'
        'KTsKewogIHJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxb'
        'ZGVzdHJveWVyKCldKTsKICBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOyBXLnJ1bignZHJhd1No'
        'aXBNZW51KCknKTsKICBjb25zdCBwciA9IFcucnVuKCd3aW5kb3cuX3NoaXBQYW5lbFJlY3QnKTsK'
        'ICBvaygndGhlIHBhbmVsIHJlcG9ydHMgaXRzIG91dGxpbmUnLCBwciAmJiBwci53PjAgJiYgcHIu'
        'aD4wKTsKICAvLyBUaGUgaGVhZGVyIGxpbmU6IGluc2lkZSB0aGUgcGFuZWwsIG9uIG5vIHJvdyBh'
        'dCBhbGwuCiAgVy5ydW4oYHBvaW50ZXJDb25zdW1lZCh7eDoke3ByLngrNDB9LHk6JHtwci55KzZ9'
        'fSlgKTsKICBvaygnYSBjbGljayBvbiB0aGUgaGVhZGVyIGtlZXBzIHRoZSBwYW5lbCBvcGVuJywg'
        'Vy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlKTsKICAvLyBBIGdhcCBiZXR3ZWVuIHR3byByb3dzLgog'
        'IGNvbnN0IHJzID0gVy5ydW4oJ3dpbmRvdy5fc2hpcFJlY3RzJyk7CiAgY29uc3QgZ2FwWSA9IHJz'
        'WzBdLnkgKyByc1swXS5oICsgMjsKICBXLnJ1bihgcG9pbnRlckNvbnN1bWVkKHt4OiR7cnNbMF0u'
        'eCs0MH0seToke2dhcFl9fSlgKTsKICBvaygnYSBjbGljayBpbiB0aGUgZ2FwIGJldHdlZW4gcm93'
        'cyBrZWVwcyBpdCBvcGVuIHRvbycsIFcuZ2V0KCdzaGlwTWVudScpPT09dHJ1ZSk7CiAgLy8gVGhl'
        'IGZvb3Rlci4KICBXLnJ1bihgcG9pbnRlckNvbnN1bWVkKHt4OiR7cHIueCtwci53LzJ9LHk6JHtw'
        'ci55K3ByLmgtNn19KWApOwogIG9rKCdhbmQgb25lIG9uIHRoZSBmb290ZXInLCBXLmdldCgnc2hp'
        'cE1lbnUnKT09PXRydWUpOwogIG9rKCdub25lIG9mIHRoZW0gc3dpdGNoZWQgdGhlIHNoaXAnLCBQ'
        'KCkuc2hpcD09PSdmaXRvdGgnKTsKICAvLyBPdXRzaWRlIHRoZSBvdXRsaW5lIGlzIHN0aWxsIG91'
        'dHNpZGUuCiAgVy5ydW4oYHBvaW50ZXJDb25zdW1lZCh7eDoke3ByLngtMTJ9LHk6JHtwci55K3By'
        'LmgvMn19KWApOwogIG9rKCdhIGNsaWNrIGJlc2lkZSB0aGUgcGFuZWwgY2xvc2VzIGl0JywgVy5n'
        'ZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7Cn0KCmNvbnNvbGUubG9nKCdLZXlib2FyZCcpOwpjb25z'
        'dCBrZXkgPSAoY29kZSk9PlcucnVuKGBvbktleSh7Y29kZTonJHtjb2RlfScsIHByZXZlbnREZWZh'
        'dWx0KCl7fX0pYCk7CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9NCIpOyBXLnNldCgnYWxs'
        'aWVzJyxbZGVzdHJveWVyKCldKTsKa2V5KCdLZXlWJyk7IG9rKCdWIG9wZW5zJywgVy5nZXQoJ3No'
        'aXBNZW51Jyk9PT10cnVlKTsKLy8gRm91ciBodWxscyBvcGVuOiByb3N0ZXIgMCB0byAzLiBUaGUg'
        'ZGlnaXRzIGZvbGxvdyB0aGUgcGFuZWwsIHNvIDQgaXMgdGhlCi8vIFNldGgsIHdoaWNoIGlzIHN0'
        'aWxsIGxvY2tlZCwgYW5kIDYgaXMgdGhlIGZpcnN0IGJvbWJlci4Ka2V5KCdEaWdpdDQnKTsgb2so'
        'JzQgKHRoZSBTZXRoLCBub3QgdW5sb2NrZWQgeWV0KSBkb2VzIG5vdGhpbmcnLAogICAgICAgICAg'
        'ICAgICAgICBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUgJiYgUCgpLnNoaXA9PT0nZml0b3RoJyk7'
        'CmtleSgnRGlnaXQ2Jyk7IG9rKCc2IHRha2VzIHRoZSBPc2lyaXMsIGZpcnN0IHJvdyBvZiB0aGUg'
        'Ym9tYmVycycsCiAgICAgICAgICAgICAgICAgIFAoKS5zaGlwPT09J2Jvb3NpcmlzJyAmJiBXLmdl'
        'dCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD00Iik7'
        'IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBrZXkoJ0tleVYnKTsKa2V5KCdEaWdpdDMn'
        'KTsgb2soJzMgdGFrZXMgdGhlIFNlcmFwaXMsIHRoaXJkIHJvdyBkb3duJywKICAgICAgICAgICAg'
        'ICAgICAgUCgpLnNoaXA9PT0nZmlzZXJhcGlzJyAmJiBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNl'
        'KTsKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD00Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0'
        'cm95ZXIoKV0pOyBrZXkoJ0tleVYnKTsga2V5KCdFc2NhcGUnKTsKb2soJ0VzY2FwZSBjbG9zZXMn'
        'LCBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKb2soJ2FuZCBob2xkcyB0aGUgcGF1c2UsIGxp'
        'a2UgZXZlcnkgb3RoZXIgd2F5IG9mIGxlYXZpbmcgYSBwYW5lbCcsCiAgIFcuZ2V0KCdwYXVzZWQn'
        'KT09PXRydWUgJiYgVy5nZXQoJ3Jlc3VtZUhvbGQnKT09PXRydWUpOwpXLnJ1bignY2xlYXJSZXN1'
        'bWVIb2xkKCknKTsKb2soJ2FmdGVyIHRoZSB0YXAgdGhlIGdhbWUgcnVucyBhZ2FpbicsIFcuZ2V0'
        'KCdwYXVzZWQnKT09PWZhbHNlKTsKcmVzZXQoKTsga2V5KCdLZXlWJyk7IG9rKCdWIHdpdGhvdXQg'
        'YSBkZXN0cm95ZXIgZG9lcyBub3RoaW5nJywgVy5nZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7Cgpj'
        'b25zb2xlLmxvZygnUmVzdGFydCBndWFyZCcpOwpXLnJ1bigibGF1bmNoR2FtZT1mdW5jdGlvbigp'
        'e2xhdW5jaGVkKyt9Iik7Ci8vIFRoZSB0aXRsZSBhbmQgdGhlIGdhbWUgb3ZlciBzY3JlZW4gYm90'
        'aCBnbyB0aHJvdWdoIHRvVGl0bGVPckxhdW5jaCBub3csCi8vIHNvIHRoYXQgaXMgd2hhdCBoYXMg'
        'dG8gYmUgaW4gcGxhY2UgZm9yIHRoZSByZXN0YXJ0IGd1YXJkIHRvIGJlIHRlc3RlZC4KVy5ydW4o'
        'InRvVGl0bGVPckxhdW5jaD1mdW5jdGlvbigpeyBpZihHUz09PSdnYW1lb3ZlcicpeyBHUz0ndGl0'
        'bGUnOyByZXR1cm47IH0gbGF1bmNoR2FtZSgpOyB9Iik7CmNvbnN0IGRvd24gPSAoKT0+Vy5ydW4o'
        'Im9uRG93bih7YnV0dG9uOjAsIGNsaWVudFg6NDAwLCBjbGllbnRZOjMwMH0pIik7ClcucnVuKCJH'
        'Uz0ndGl0bGUnOyBsYXVuY2hlZD0wIik7IGRvd24oKTsgb2soJ3RhcCBvbiB0aXRsZSBzdGFydHMg'
        'YXQgb25jZScsIFcuZ2V0KCdsYXVuY2hlZCcpPT09MSk7ClcucnVuKCJHUz0nZ2FtZW92ZXInOyBn'
        'YW1lT3ZlckF0PXBlcmZvcm1hbmNlLm5vdygpOyBsYXVuY2hlZD0wIik7IGRvd24oKTsgb2soJ3Rh'
        'cCByaWdodCBhZnRlciBkeWluZyBkb2VzIG5vdCByZXN0YXJ0JywgVy5nZXQoJ2xhdW5jaGVkJyk9'
        'PT0wKTsKVy5ydW4oImdhbWVPdmVyQXQ9cGVyZm9ybWFuY2Uubm93KCktMjAwMCIpOyBkb3duKCk7'
        'Cm9rKCd0YXAgYWZ0ZXIgMiBzIGdvZXMgYmFjayB0byB0aGUgdGl0bGUsIG5vdCBpbnRvIHRoZSBu'
        'ZXh0IHJ1bicsCiAgIFcuZ2V0KCdsYXVuY2hlZCcpPT09MCAmJiBXLmdldCgnR1MnKT09PSd0aXRs'
        'ZScpOwoKCmNvbnNvbGUubG9nKCdIYW5nYXJzIGJ5IGZhY3Rpb24nKTsKY29uc3QgY29sb3NzdXMg'
        'PSAobyk9Pk9iamVjdC5hc3NpZ24oe2ltZzonc2Rjb2xvc3N1cycsIGNvbG9zc3VzOnRydWUsIHNt'
        'YWxsOmZhbHNlLCBkZWFkOmZhbHNlLCB3YXJwT3V0OmZhbHNlfSwgb3x8e30pOwpvaygnaHVsbCBm'
        'YWN0aW9uIGNvbWVzIGZyb20gdGhlIGtleScsIFcucnVuKCJodWxsRmFjKCdkZWhhdHNoZXBzdXQn'
        'KSIpPT09J3Zhc3VkYW4nCiAgICYmIFcucnVuKCJodWxsRmFjKCdkZW9yaW9ucmlnaHQnKSIpPT09'
        'J3RlcnJhbicgJiYgVy5ydW4oImh1bGxGYWMoJ3NkY29sb3NzdXMnKSIpPT09J2d0dmEnKTsKb2so'
        'J2EgZGVmZWN0ZWQgSGFtbWVyIG9mIExpZ2h0IFR5cGhvbiBzdGlsbCBjb3VudHMgYXMgVmFzdWRh'
        'bicsCiAgIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKHtpbWc6J2RldHlwaG9u'
        'JywgZmFjdGlvbjonaG9sJ30pXSkpPT09dHJ1ZSk7Cm9rKCdhIHJlbmVnYWRlIEhhdHNoZXBzdXQg'
        'dG9vJywKICAgcmVhZHkoKCk9Plcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVoYXRz'
        'aGVwc3V0JywgZmFjdGlvbjoncmVuZWdhZGUnfSldKSk9PT10cnVlKTsKb2soJ1RlcnJhbiBPcmlv'
        'biBvbmx5OiBub3QgcmVhZHknLCByZWFkeSgoKT0+Vy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7'
        'aW1nOidkZW9yaW9ucmlnaHQnfSldKSk9PT1mYWxzZSk7Cm9rKCdUZXJyYW4gSGVjYXRlIG9ubHk6'
        'IG5vdCByZWFkeScsIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKHtpbWc6J2Rl'
        'aGVjYXRlJ30pXSkpPT09ZmFsc2UpOwpvaygnT3Jpb24gcGx1cyBUeXBob246IHJlYWR5LCB0aGUg'
        'bGlzdHMgYWRkIHVwJywKICAgcmVhZHkoKCk9Plcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2lt'
        'ZzonZGVvcmlvbnJpZ2h0J30pLCBkZXN0cm95ZXIoe2ltZzonZGV0eXBob24nfSldKSk9PT10cnVl'
        'KTsKb2soJ3Vua25vd24gY2FwaXRhbCBodWxsOiBub3QgcmVhZHknLCByZWFkeSgoKT0+Vy5zZXQo'
        'J2FsbGllcycsW2Rlc3Ryb3llcih7aW1nOidkZWRlbW9uJ30pXSkpPT09ZmFsc2UpOwoKcmVzZXQo'
        'KTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2lt'
        'ZzonZGVvcmlvbnJpZ2h0J30pXSk7Cm9rKCdWYXN1ZGFuIGh1bGwgbm90IG9mZmVyZWQgYnkgYSBU'
        'ZXJyYW4gaGFuZ2FyJywgVy5ydW4oInNoaXBPZmZlcmVkKCdmaWhvcnVzJykiKT09PWZhbHNlKTsK'
        'Vy5ydW4oInNoaXBNZW51PXRydWU7IHN3YXBTaGlwKCdmaWhvcnVzJykiKTsKb2soJ2FuZCBhIGZv'
        'cmNlZCBzd2l0Y2ggaXMgcmVmdXNlZCcsIFAoKS5zaGlwPT09J2ZpdG90aCcgJiYgVy5nZXQoJ3No'
        'aXBTd2FwV2F2ZScpPT09LTEpOwpXLnNldCgnYWxsaWVzJyxbY29sb3NzdXMoKV0pOwpvaygndGhl'
        'IENvbG9zc3VzIG9mZmVycyB0aGUgVmFzdWRhbiBodWxsJywgVy5ydW4oInNoaXBPZmZlcmVkKCdm'
        'aWhvcnVzJykiKT09PXRydWUpOwoKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcu'
        'c2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVvcmlvbnJpZ2h0J30pXSk7ClcucnVuKCd0'
        'b2dnbGVTaGlwTWVudSgpJyk7IG9rKCdUZXJyYW4gaGFuZ2FyIG9ubHk6IHRoZSBtZW51IHN0YXlz'
        'IHNodXQnLCBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKVy5ydW4oInNoaXBNZW51PXRydWU7'
        'IGRyYXdTaGlwTWVudSgpIik7Cm9rKCdubyBjZWxsIGlzIHRhcHBhYmxlIGluIHRoYXQgc3RhdGUn'
        'LCBXLnJ1bignd2luZG93Ll9zaGlwUmVjdHMnKS5ldmVyeShyPT4hci5rZXkpKTsKCmNvbnNvbGUu'
        'bG9nKCdDb2xvc3N1cyBsaWZ0cyB0aGUgb25jZSBwZXIgd2F2ZSBsaW1pdCcpOwpyZXNldCgpOyBX'
        'LnJ1bigic2hpcFVubG9ja2VkPTMiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7Clcu'
        'cnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBzd2FwU2hpcCgnZmlob3J1cycpIik7Cm9rKCdmaXJzdCBz'
        'd2l0Y2ggb2YgdGhlIHdhdmUgcmVmaXRzJywgUCgpLnNoaXA9PT0nZmlob3J1cycgJiYgUCgpLmhw'
        'PT09ODAgJiYgUCgpLnNoPT09MTAwICYmIFAoKS5zZWNBbW1vPT09MjApOwpvaygnbm8gQ29sb3Nz'
        'dXM6IHNwZW50IGZvciB0aGlzIHdhdmUnLCBXLnJ1bignc2hpcFN3YXBSZWFkeSgpJyk9PT1mYWxz'
        'ZSk7Clcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKSwgY29sb3NzdXMoKV0pOwpvaygnQ29sb3Nz'
        'dXMgYXJyaXZlczogYXZhaWxhYmxlIGFnYWluIGluIHRoZSBzYW1lIHdhdmUnLCBXLnJ1bignc2hp'
        'cFN3YXBSZWFkeSgpJyk9PT10cnVlKTsKVy5ydW4oInBsYXllci5ocD00MDsgcGxheWVyLnNoPTUw'
        'OyBwbGF5ZXIuc2VjQW1tbz0xMCIpOwpXLnJ1bigidG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAo'
        'J2Jvb3NpcmlzJykiKTsKb2soJ3NlY29uZCBzd2l0Y2ggaGFwcGVucycsIFAoKS5zaGlwPT09J2Jv'
        'b3NpcmlzJyk7Cm9rKCdodWxsIGNhcnJpZXMgb3ZlciBhcyBhIGZyYWN0aW9uLCA0MC84MCBvZiAx'
        'NDAgPSA3MCcsIFAoKS5ocD09PTcwKTsKb2soJ3NoaWVsZHMgY2Fycnkgb3ZlciwgNTAvMTAwIG9m'
        'IDEwMCA9IDUwJywgUCgpLnNoPT09NTApOwpvaygnYW1tbyBjYXJyaWVzIG92ZXIsIDEwLzIwIG9m'
        'IDEwIGJvbWJzID0gNScsIFAoKS5zZWNBbW1vPT09NSk7Cm9rKCdubyByZWZpdDogbm90IGZ1bGwn'
        'LCBQKCkuaHA8UCgpLm1heEhwICYmIFAoKS5zZWNBbW1vPFAoKS5zZWNNYXgpOwoKcmVzZXQoKTsg'
        'Vy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKSwgY29s'
        'b3NzdXMoKV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAoJ2ZpaG9ydXMnKSIp'
        'Owpvaygnd2l0aCB0aGUgQ29sb3NzdXMgdGhlcmUgdGhlIGZpcnN0IHN3aXRjaCBzdGlsbCByZWZp'
        'dHMnLCBQKCkuaHA9PT04MCAmJiBQKCkuc2VjQW1tbz09PTIwKTsKVy5ydW4oInBsYXllci5ocD0x'
        'Iik7ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBzd2FwU2hpcCgnYm9vc2lyaXMnKSIpOwpvaygn'
        'YSBuZWFybHkgZGVhZCBodWxsIHN0YXlzIGFsaXZlIGFmdGVyIGNhcnJ5aW5nIG92ZXInLCBQKCku'
        'aHA+PTEgJiYgUCgpLmhwPD0zKTsKCnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBX'
        'LnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCksIGNvbG9zc3VzKHtkZWFkOnRydWV9KV0pOwpXLnJ1'
        'bigidG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAoJ2ZpaG9ydXMnKSIpOwpvaygnZGVhZCBDb2xv'
        'c3N1cyBncmFudHMgbm90aGluZycsIFcucnVuKCdzaGlwU3dhcFJlYWR5KCknKT09PWZhbHNlKTsK'
        'cmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95'
        'ZXIoKSwgY29sb3NzdXMoe3dhcnBPdXQ6dHJ1ZX0pXSk7ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgp'
        'OyBzd2FwU2hpcCgnZmlob3J1cycpIik7Cm9rKCdDb2xvc3N1cyB3YXJwaW5nIG91dCBncmFudHMg'
        'bm90aGluZycsIFcucnVuKCdzaGlwU3dhcFJlYWR5KCknKT09PWZhbHNlKTsKCnJlc2V0KCk7IFcu'
        'cnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBXLnNldCgnYWxsaWVzJyxbY29sb3NzdXMoKV0pOwpXLnJ1'
        'bigidG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAoJ2ZpaG9ydXMnKSIpOyBXLnJ1bigicGxheWVy'
        'LmhwPTIwIik7ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBzd2FwU2hpcCgnZml0b3RoJykiKTsK'
        'b2soJ2JhY2sgb250byB0aGUgc3RhcnQgaHVsbCBhdCB0aGUgQ29sb3NzdXMsIDIwLzgwIG9mIDEw'
        'MCA9IDI1JywgUCgpLnNoaXA9PT0nZml0b3RoJyAmJiBQKCkuaHA9PT0yNSk7ClcucnVuKCd3YXZl'
        'PTInKTsKb2soJ25ldyB3YXZlIHdpdGggdGhlIENvbG9zc3VzIHN0aWxsIHRoZXJlOiByZWZpdHMg'
        'YWdhaW4nLCBXLnJ1bignc2hpcFN3YXBSZWFkeSgpJyk9PT10cnVlKTsKVy5ydW4oInRvZ2dsZVNo'
        'aXBNZW51KCk7IHN3YXBTaGlwKCdmaWhvcnVzJykiKTsgb2soJ2FuZCBpdCBpcyBhIGZ1bGwgaHVs'
        'bCcsIFAoKS5ocD09PTgwKTsKCmNvbnNvbGUubG9nKCdDeWNsZXM6IGVhY2ggYnJpbmdzIGl0cyBv'
        'd24gZmxlZXQnKTsKewogIGNvbnN0IGhvbCA9IFcucnVuKCdjeWNsZUF0KDEpJyksIG50ZiA9IFcu'
        'cnVuKCdjeWNsZUF0KDMxKScpOwogIG9rKCd3YXZlcyAxIHRvIDMwIGFyZSB0aGUgSGFtbWVyIG9m'
        'IExpZ2h0IGN5Y2xlJywgVy5ydW4oJ2N5Y2xlQXQoMzApJyk9PT1ob2wgJiYgaG9sLmZpcnN0PT09'
        'MSk7CiAgb2soJ3dhdmUgMzEgb3BlbnMgdGhlIE5URiBjeWNsZSwgYW5kIGl0IGhvbGRzIGFmdGVy'
        'IHRoYXQnLCBudGYuZmlyc3Q9PT0zMSAmJiBXLnJ1bignY3ljbGVBdCg1OSknKT09PW50ZiAmJiBX'
        'LnJ1bignY3ljbGVBdCgxNDApJyk9PT1udGYpOwogIHJlc2V0KCk7CiAgVy5ydW4oInNjb3JlPTk1'
        'MDAwOyBlbnRlckN5Y2xlKGN5Y2xlQXQoMzEpKSIpOwogIG9rKCdlbnRlcmluZyBpdCBwdXRzIHRo'
        'ZSBwbGF5ZXIgaW4gYSBNeXJtaWRvbiwgZnJlc2gnLCBQKCkuc2hpcD09PSdmaW15cm1pZG9uJyAm'
        'JiBQKCkuaHA9PT1QKCkubWF4SHApOwogIG9rKCd0aGUgcm9zdGVyIGlzIHRoZSBUZXJyYW4gb25l'
        'LCBlaWdodCBodWxscycsCiAgICAgVy5ydW4oJ1BMQVlFUl9TSElQUy5sZW5ndGgnKT09PTggJiYg'
        'Vy5ydW4oIlBMQVlFUl9TSElQUy5ldmVyeShzPT5zLmZhYz09PSd0ZXJyYW4nKSIpKTsKICBvaygn'
        'aW4gdGhlIGFncmVlZCBvcmRlcicsCiAgICAgVy5ydW4oIlBMQVlFUl9TSElQUy5tYXAocz0+cy5r'
        'ZXkpLmpvaW4oKSIpPT09J2ZpbXlybWlkb24sZmloZXJjLGJvYXJ0ZW1pcyxmaWhlcmNtazIsYm9t'
        'ZWR1c2EsZmllcmlueWVzLGJvdXJzYSxmaWFyZXMnKTsKICBvaygnb25seSB0aGUgZmlyc3QgaHVs'
        'bCBpcyBvcGVuJywgVy5nZXQoJ3NoaXBVbmxvY2tlZCcpPT09MSk7CiAgVy5ydW4oInNjb3JlPTk1'
        'MDAwKzM5OTk7IHRpY2tTaGlwVW5sb2NrcygpIik7CiAgb2soJ3RoZSBwb2ludHMgYnJvdWdodCBp'
        'bnRvIHRoZSBjeWNsZSBkbyBub3QgY291bnQnLCBXLmdldCgnc2hpcFVubG9ja2VkJyk9PT0xKTsK'
        'ICBXLnJ1bigic2NvcmU9OTUwMDArNDAwMDsgdGlja1NoaXBVbmxvY2tzKCkiKTsKICBvaygnNDAw'
        'MCBwb2ludHMgc2NvcmVkIElOIHRoZSBjeWNsZSBvcGVuIHRoZSBIZXJjdWxlcycsIFcuZ2V0KCdz'
        'aGlwVW5sb2NrZWQnKT09PTIgJiYgL0hFUkNVTEVTLy50ZXN0KFcuZ2V0KCdOT1RJQ0VfTE9HJyku'
        'c2xpY2UoLTEpWzBdLnR4dCkpOwogIG9rKCd0aGUgVGVycmFuIHN1cHBvcnQgY29sdW1uIGFuc3dl'
        'cnMsIHRoZSBWYXN1ZGFuIG9uZSBkb2VzIG5vdCcsCiAgICAgVy5ydW4oJ0FMTFlfRkFDX09OLnRl'
        'cnJhbicpPT09dHJ1ZSAmJiBXLnJ1bignQUxMWV9GQUNfT04udmFzdWRhbicpPT09ZmFsc2UpOwog'
        'IC8vIFRoZSBoYW5nYXIgZm9sbG93cyB0aGUgaHVsbCwgc28gdGhlIFRlcnJhbiByb3N0ZXIgbmVl'
        'ZHMgYSBUZXJyYW4gZGVzdHJveWVyLgogIFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzon'
        'ZGVvcmlvbnJpZ2h0J30pXSk7CiAgb2soJ2EgVGVycmFuIGRlc3Ryb3llciBvZmZlcnMgdGhlIEhl'
        'cmN1bGVzJywgVy5ydW4oInNoaXBPZmZlcmVkKCdmaWhlcmMnKSIpPT09dHJ1ZSAmJiBXLnJ1bign'
        'c2hpcFN3YXBSZWFkeSgpJyk9PT10cnVlKTsKICBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCld'
        'KTsKICBvaygnYSBWYXN1ZGFuIG9uZSBkb2VzIG5vdCcsIFcucnVuKCJzaGlwT2ZmZXJlZCgnZmlo'
        'ZXJjJykiKT09PWZhbHNlICYmIFcucnVuKCdzaGlwU3dhcFJlYWR5KCknKT09PWZhbHNlKTsKICBX'
        'LnJ1bigiZW50ZXJDeWNsZShjeWNsZUF0KDEpKSIpOwogIG9rKCdhbmQgYmFjazogdGhlIFZhc3Vk'
        'YW4gcm9zdGVyIGFuZCBjb2x1bW4nLCBQKCkuc2hpcD09PSdmaXRvdGgnICYmCiAgICAgVy5ydW4o'
        'J0FMTFlfRkFDX09OLnRlcnJhbicpPT09ZmFsc2UgJiYgVy5ydW4oJ0FMTFlfRkFDX09OLnZhc3Vk'
        'YW4nKT09PXRydWUpOwp9Cm9rKCd0aGUgcnVuIHN0YXJ0cyBpbiB0aGUgY3ljbGUgb2YgaXRzIGZp'
        'cnN0IHdhdmUnLAogICAvZWxzZSBlbnRlckN5Y2xlXChjeWNsZUF0XCh3YXZlXCsxXClcKTsvLnRl'
        'c3QoZm4oJ2xhdW5jaEdhbWUnKSkpOwpvaygnY3Jvc3NpbmcgaW50byBhIG5ldyBjeWNsZSBoYW5k'
        'cyBvdmVyIHRoZSBmbGVldCcsCiAgIC9pZlwoX2MhPT1jeWNsZU5vd1wpIGVudGVyQ3ljbGVcKF9j'
        'XCk7Ly50ZXN0KGZuKCduZXh0V2F2ZScpKSk7Cm9rKCc/bT0gc3RhcnRzIHRoZSBydW4gYXQgdGhh'
        'dCB3YXZlIGluc3RlYWQgb2YgcmVwZWF0aW5nIGl0JywKICAgL1NDUklQVF9PTkVcP1NDUklQVF9P'
        'TkUtMTowLy50ZXN0KGZuKCdsYXVuY2hHYW1lJykpICYmICEvU0NSSVBUX09ORSBcPyBTQ1JJUFRf'
        'T05FIDogbi8udGVzdChzcmMpKTsKCmNvbnNvbGUubG9nKCdBIG1pc3Npb24gY2FuIGxlbmQgYSBo'
        'dWxsJyk7CnsKICByZXNldCgpOyBXLnJ1bigic2NvcmU9OTUwMDA7IGVudGVyQ3ljbGUoY3ljbGVB'
        'dCgzMSkpOyBzaGlwVW5sb2NrZWQ9OCIpOwogIFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2lt'
        'ZzonZGVvcmlvbnJpZ2h0J30pXSk7CiAgb2soJ2JlZm9yZTogYSBUZXJyYW4gZGVzdHJveWVyIG9m'
        'ZmVycyBhIHN3aXRjaCcsIFcucnVuKCdzaGlwU3dhcFJlYWR5KCknKT09PXRydWUpOwogIFcucnVu'
        'KCJmb3JjZVNoaXAoJ2ZpcGVnYXN1cycpIik7CiAgb2soJ3RoZSBwbGF5ZXIgZmxpZXMgdGhlIGxl'
        'bnQgaHVsbCcsIFAoKS5zaGlwPT09J2ZpcGVnYXN1cycpOwogIG9rKCd3aXRoIGl0cyBvd24gZmln'
        'dXJlcywgbm90IHRoZSBmaWdodGVyIGRlZmF1bHRzJywKICAgICBQKCkubWF4U2g9PT04MCAmJiBQ'
        'KCkuc3BkPT09My42ICYmIFcucnVuKCJzaGlwU3RhdHMoJ2ZpcGVnYXN1cycpLm5hbWUiKT09PSdH'
        'VEYgUGVnYXN1cycpOwogIG9rKCdhbmQgdGhlIGhhbmdhciBpcyBjbG9zZWQgZm9yIHRoaXMgbWlz'
        'c2lvbicsIFcucnVuKCdzaGlwU3dhcFJlYWR5KCknKT09PWZhbHNlKTsKICBvaygnaXQgaXMgYW5u'
        'b3VuY2VkIGluIHRoZSBjb2x1bW4nLCBXLmdldCgnTk9USUNFX0xPRycpLnNvbWUobj0+L1BFR0FT'
        'VVMgQVNTSUdORUQvLnRlc3Qobi50eHQpKSk7CiAgVy5ydW4oInBsYXllci5ocD0xMDsgcmVsZWFz'
        'ZVNoaXAoKSIpOwogIG9rKCd0aGUgbmV4dCB3YXZlIGhhbmRzIHRoZSBvd24gaHVsbCBiYWNrLCBy'
        'ZWZpdHRlZCcsIFAoKS5zaGlwPT09J2ZpbXlybWlkb24nICYmIFAoKS5ocD09PVAoKS5tYXhIcCk7'
        'CiAgb2soJ2FuZCB0aGUgaGFuZ2FyIG9wZW5zIGFnYWluJywgVy5ydW4oJ3NoaXBTd2FwUmVhZHko'
        'KScpPT09dHJ1ZSk7CiAgVy5ydW4oInJlbGVhc2VTaGlwKCkiKTsKICBvaygncmVsZWFzaW5nIHR3'
        'aWNlIGNoYW5nZXMgbm90aGluZycsIFAoKS5zaGlwPT09J2ZpbXlybWlkb24nKTsKICBXLnJ1bigi'
        'ZW50ZXJDeWNsZShjeWNsZUF0KDEpKSIpOyAgIC8vIHRoZSB0ZXN0cyBiZWxvdyBleHBlY3QgdGhl'
        'IGZpcnN0IGZsZWV0Cn0Kb2soJ3RoZSBuZXh0IHdhdmUgcmVsZWFzZXMgYSBsZW50IGh1bGwgYmVm'
        'b3JlIGFueXRoaW5nIGVsc2UnLAogICAvcmVsZWFzZVNoaXBcKFwpO1tcc1xTXXswLDIwMH1lbnRl'
        'ckN5Y2xlLy50ZXN0KGZuKCduZXh0V2F2ZScpKSk7Cgpjb25zb2xlLmxvZygnU3VwcG9ydCBjYWxs'
        'cyBieSBmYWN0aW9uJyk7Cm9rKCd0aGUgVGVycmFuIGNvbHVtbiBpcyBvZmYgaW4gdGhpcyBjeWNs'
        'ZScsIHNyYy5pbmNsdWRlcygiY29uc3QgQUxMWV9GQUNfT04gPSB7dGVycmFuOmZhbHNlLCB2YXN1'
        'ZGFuOnRydWUsIGd0dmE6dHJ1ZX07IikpOwpvaygndGhlIGNhbGwgaXMgZ2F0ZWQgaW5zaWRlIGNh'
        'bGxBbGx5LCBub3Qgb25seSBpbiB0aGUgbWVudScsCiAgIC9mdW5jdGlvbiBjYWxsQWxseVwoaWRc'
        'KVx7W1xzXFNdezAsNDAwfWFsbHlGYWNPblwoY2RlZlwuZmFjXCkvLnRlc3Qoc3JjKSk7Cm9rKCd0'
        'aGUgbWVudSBubyBsb25nZXIgdXNlcyB0aGUgZml4ZWQgdHdvIGNvbHVtbiBzcGxpdCcsICFzcmMu'
        'aW5jbHVkZXMoJ0FMTFlfVEVSX04/MDoxJykpOwpvaygndGhlIENvbG9zc3VzIGlzIGEgR1RWQSBz'
        'aGlwIG5vdycsIC9jb2xvc3N1czpccypce2NsczonZGVzdHJveWVyJywgZmFjOidndHZhJy8udGVz'
        'dChzcmMpKTsKCmNvbnNvbGUubG9nKCdIdWxsIHBpY3R1cmVzIGluIHRoZWlyIG93biBjZWxsJyk7'
        'CmNvbnN0IElNRyA9ICh3LGgpPT4oe3dpZHRoOncsIGhlaWdodDpofSk7CmNvbnN0IEFMTF9JTUdT'
        'ID0ge2ZpdG90aDpJTUcoMTIwLDkwKSwgZmlob3J1czpJTUcoMTIwLDkwKSwgYm9vc2lyaXM6SU1H'
        'KDE1MCwxMTApLAogICAgICAgICAgICAgICAgICBmaXNlcmFwaXM6SU1HKDEyMCw5MCksIGZpc2V0'
        'aDpJTUcoMTIwLDkwKSwgYm9iYWtoYTpJTUcoMTUwLDExMCksCiAgICAgICAgICAgICAgICAgIGZp'
        'dGF1cmV0OklNRygxMjAsOTApLCBib3Nla2htZXQ6SU1HKDE1MCwxMTApfTsKY29uc3QgUElDVyA9'
        'IFcucnVuKCdIR19QSUNfVycpLCBQSUNIID0gVy5ydW4oJ0hHX1JPVycpLTY7CnJlc2V0KCk7IFcu'
        'cnVuKCJzaGlwVW5sb2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5y'
        'dW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsKVy5zZXQoJ0lNR1MnLCB7fSk7CkNMUigpOyBXLnJ1bign'
        'ZHJhd1NoaXBNZW51KCknKTsKb2soJ25vdGhpbmcgbG9hZGVkIHlldDogbm8gcGljdHVyZSwgbm8g'
        'Y3Jhc2gsIHJvd3Mgc3RpbGwgdGhlcmUnLAogICBkcmF3cygpLmxlbmd0aD09PTAgJiYgVy5ydW4o'
        'J3dpbmRvdy5fc2hpcFJlY3RzJykubGVuZ3RoPT09OCk7Clcuc2V0KCdJTUdTJywgQUxMX0lNR1Mp'
        'OwpDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgpJyk7Cm9rKCdvbmUgaHVsbCBkcmF3biBwZXIg'
        'b3BlbiByb3cnLCBkcmF3cygpLmxlbmd0aD09PTgpOwovLyBUaGUgZ2xvc3Mgb24gZWFjaCBwbGF0'
        'ZSBjbGlwcyBhcyB3ZWxsLCBzbyB0aGlzIGNvdW50cyBhdCBsZWFzdCBvbmUgY2xpcAovLyBwZXIg'
        'cGljdHVyZSByYXRoZXIgdGhhbiBleGFjdGx5IG9uZSBpbiB0b3RhbC4Kb2soJ2VhY2ggb25lIGNs'
        'aXBwZWQgdG8gaXRzIG93biBjZWxsIGZpcnN0JywgY2xpcHMoKS5sZW5ndGg+PTgpOwpvaygnZWFj'
        'aCBvbmUgZml0cyBpbnNpZGUgdGhlIHBpY3R1cmUgY2VsbCcsCiAgIGRyYXdzKCkuZXZlcnkoZD0+'
        'ZC5hcmdzWzNdPD1QSUNXLTUgJiYgZC5hcmdzWzRdPD1QSUNILTUgJiYgZC5hcmdzWzNdPjAgJiYg'
        'ZC5hcmdzWzRdPjApKTsKb2soJ2FzcGVjdCByYXRpbyBrZXB0JywgZHJhd3MoKS5ldmVyeShkPT5N'
        'YXRoLmFicygoZC5hcmdzWzNdL2QuYXJnc1s0XSkgLSAoMTIwLzkwKSk8MC4wMQogICAgICAgICAg'
        'ICAgICAgICAgICAgICAgICAgICAgICAgICAgIHx8IE1hdGguYWJzKChkLmFyZ3NbM10vZC5hcmdz'
        'WzRdKSAtICgxNTAvMTEwKSk8MC4wMSkpOwpvaygnc2F2ZSBhbmQgcmVzdG9yZSBzdGF5IGJhbGFu'
        'Y2VkLCBubyBsZWFraW5nIGNsaXAgb3IgYWxwaGEnLCBiYWxhbmNlZCgpKTsKb2soJ2EgcGljdHVy'
        'ZSBpcyBhIHBpY3R1cmUgbm93LCBub3QgYSB3YXRlcm1hcmsnLCBhbHBoYXMoKS5ldmVyeShhPT5h'
        'PjAuOSAmJiBhPD0xKSk7CnsKICAvLyBUaHJlZSBvcGVuLCBmaXZlIGxvY2tlZDogYSBsb2NrZWQg'
        'aHVsbCBoYXMgbm8gcm93IHRhbGwgZW5vdWdoIGZvciBhCiAgLy8gcGljdHVyZSwgc28gaXQgZ2V0'
        'cyBub25lIGF0IGFsbC4KICByZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTMiKTsgVy5zZXQo'
        'J2FsbGllcycsW2Rlc3Ryb3llcigpXSk7IFcucnVuKCd0b2dnbGVTaGlwTWVudSgpJyk7CiAgVy5z'
        'ZXQoJ0lNR1MnLCBBTExfSU1HUyk7IENMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKICBv'
        'aygnYSBsb2NrZWQgaHVsbCBzaG93cyBubyBwaWN0dXJlJywgZHJhd3MoKS5sZW5ndGg9PT0zKTsK'
        'fQpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTgiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ry'
        'b3llcigpXSk7IFcucnVuKCd0b2dnbGVTaGlwTWVudSgpJyk7Clcuc2V0KCdJTUdTJywge2ZpdG90'
        'aDpJTUcoMCwwKX0pOwpDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgpJyk7Cm9rKCdhIHplcm8g'
        'c2l6ZWQgc3ByaXRlIGlzIHNraXBwZWQgaW5zdGVhZCBvZiBkaXZpZGluZyBieSB6ZXJvJywgZHJh'
        'd3MoKS5sZW5ndGg9PT0wKTsKVy5zZXQoJ0lNR1MnLCB7fSk7Cgpjb25zb2xlLmxvZygnQmFycmVs'
        'cyBhbmQgdm9sbGV5IGRhbWFnZSwgaW4gdGhlaXIgb3duIGNvbHVtbnMnKTsKY29uc3QgdGV4dHMg'
        'PSAoKT0+IENBTExTLmZpbHRlcihjPT5jLmZuPT09J2ZpbGxUZXh0JykubWFwKGM9Pih7czpTdHJp'
        'bmcoYy5hcmdzWzBdKSwgeDpjLmFyZ3NbMV0sIHk6Yy5hcmdzWzJdfSkpOwovLyBBIGNvbHVtbiBp'
        'cyBjaGVja2VkIGJ5IHdoZXJlIGl0IGFjdHVhbGx5IGxhbmRzOiB0aGUgeCBvZiB0aGUgY29sdW1u'
        'IGluIHRoZQovLyBsYXlvdXQsIGFkZGVkIHRvIHRoZSB4IG9mIGEgcm93IHRoZSBtZW51IGl0c2Vs'
        'ZiByZXBvcnRlZC4KY29uc3QgY29sWCA9IChrKT0+IFcucnVuKCdIR19DT0xTJykuZmluZChjPT5j'
        'Lms9PT1rKS54OwovLyBUaGUgY29sdW1uIHRpdGxlcyBzaXQgb24gdGhlIHNhbWUgeCwgc28gYSB2'
        'YWx1ZSBvbmx5IGNvdW50cyB3aGVuIGl0IGFsc28KLy8gc2l0cyBpbnNpZGUgYSByb3cuCmNvbnN0'
        'IGluQ29sID0gKGspPT57CiAgY29uc3QgeDAgPSBjb2xYKGspLCBycyA9IFcucnVuKCd3aW5kb3cu'
        'X3NoaXBSZWN0cycpOwogIHJldHVybiB0ZXh0cygpLmZpbHRlcih0PT4gcnMuc29tZShyPT4gdC54'
        'ID09PSByLnggKyB4MCAmJiB0LnkgPj0gci55ICYmIHQueSA8PSByLnkgKyByLmgpKTsKfTsKcmVz'
        'ZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD04Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIo'
        'KV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOwpXLnNldCgnTU9VTlRTJywge30pOwpDTFIo'
        'KTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgpJyk7Cm9rKCdubyBtb3VudCBkYXRhOiBubyBjbGFpbSBh'
        'Ym91dCBndW5zIG9yIHZvbGxleSBhdCBhbGwnLAogICBpbkNvbCgnZ3VucycpLmxlbmd0aD09PTAg'
        'JiYgaW5Db2woJ3ZvbGxleScpLmxlbmd0aD09PTApOwpXLnNldCgnTU9VTlRTJywge2ZpdG90aDp7'
        'cHJpbWFyeTpbMSwxXX0sIGZpaG9ydXM6e3ByaW1hcnk6WzEsMV19LCBib29zaXJpczp7cHJpbWFy'
        'eTpbMSwxXX0sCiAgICAgICAgICAgICAgICAgZmlzZXJhcGlzOntwcmltYXJ5OlsxLDFdfSwgZmlz'
        'ZXRoOntwcmltYXJ5OlsxLDFdfSwgYm9iYWtoYTp7cHJpbWFyeTpbMSwxXX0sCiAgICAgICAgICAg'
        'ICAgICAgZml0YXVyZXQ6e3ByaW1hcnk6WzEsMSwxXX0sIGJvc2VraG1ldDp7cHJpbWFyeTpbMSwx'
        'XX19KTsKQ0xSKCk7IFcucnVuKCdkcmF3U2hpcE1lbnUoKScpOwpvaygnYSBmaWd1cmUgb24gZXZl'
        'cnkgb25lIG9mIHRoZSBlaWdodCByb3dzJywKICAgaW5Db2woJ2d1bnMnKS5sZW5ndGg9PT04ICYm'
        'IGluQ29sKCd2b2xsZXknKS5sZW5ndGg9PT04KTsKb2soJ3RoZSBzZXZlbiB0d28gYmFycmVsIGh1'
        'bGxzIHJlYWQgMiBhbmQgNTEnLAogICBpbkNvbCgnZ3VucycpLmZpbHRlcih0PT50LnM9PT0nMicp'
        'Lmxlbmd0aD09PTcgJiYKICAgaW5Db2woJ3ZvbGxleScpLmZpbHRlcih0PT50LnM9PT0nNTEnKS5s'
        'ZW5ndGg9PT03KTsKb2soJ3RoZSBUYXVyZXQgcmVhZHMgMyBhbmQgNTcnLAogICBpbkNvbCgnZ3Vu'
        'cycpLmZpbHRlcih0PT50LnM9PT0nMycpLmxlbmd0aD09PTEgJiYKICAgaW5Db2woJ3ZvbGxleScp'
        'LmZpbHRlcih0PT50LnM9PT0nNTcnKS5sZW5ndGg9PT0xKTsKb2soJ3RoZSBmaWd1cmUgbWF0Y2hl'
        'cyB3aGF0IHZvbGxleURtZyBhY3R1YWxseSBkb2VzJywKICAgTWF0aC5yb3VuZChXLnJ1bigndm9s'
        'bGV5VG90YWwoMiknKSk9PT01MSAmJiBNYXRoLnJvdW5kKFcucnVuKCd2b2xsZXlUb3RhbCgzKScp'
        'KT09PTU3CiAgICYmIE1hdGgucm91bmQoVy5ydW4oJ3ZvbGxleVRvdGFsKDEpJykpPT09NDQpOwpv'
        'aygnb25lIGJhcnJlbCBpcyB0aGUgZmFsbGJhY2sgb2YgdGhlIGZvcm11bGEsIG5vdCBhIGNyYXNo'
        'JywgVy5ydW4oJ3ZvbGxleVRvdGFsKDApJyk9PT00NCk7CnsKICAvLyBUaGUgcG9pbnQgb2YgdGhl'
        'IGNvbHVtbnM6IGh1bGwgc2l0cyB1bmRlciBodWxsIG9uIGV2ZXJ5IHJvdy4KICBjb25zdCBodWxs'
        'cyA9IGluQ29sKCdodWxsJykubWFwKHQ9PnQucykuam9pbigpOwogIG9rKCd0aGUgaHVsbCBjb2x1'
        'bW4gcmVhZHMgZG93biB0aGUgbGlzdCBpbiBvcmRlcicsIGh1bGxzPT09JzEwMCw4MCw4MCwxMjUs'
        'MTAwLDE0MCwxMDAsMTQwJyk7CiAgY29uc3Qgc2hpZWxkcyA9IGluQ29sKCdzaGllbGQnKS5tYXAo'
        'dD0+dC5zKS5qb2luKCk7CiAgb2soJ3RoZSBzaGllbGQgY29sdW1uIHRvbycsIHNoaWVsZHM9PT0n'
        'MTAwLDEwMCw3MCwxMzAsMTMwLDEwMCwxMDAsMTMwJyk7CiAgb2soJ2V2ZXJ5IHZhbHVlIGluIGEg'
        'Y29sdW1uIHNoYXJlcyBvbmUgeCcsCiAgICAgbmV3IFNldChpbkNvbCgnaHVsbCcpLm1hcCh0PT50'
        'LngpKS5zaXplPT09MSk7Cn0KewogIC8vIFR3byB1bmxvY2tlZCBvZiBlaWdodDogdGhlIG1lbnUg'
        'bmVlZHMgdHdvIHRvIG9wZW4gYXQgYWxsLgogIHJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9'
        'MiIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKICBXLnNldCgnTU9VTlRTJywge2Zp'
        'dG90aDp7cHJpbWFyeTpbMSwxXX0sIGZpaG9ydXM6e3ByaW1hcnk6WzEsMV19LCBmaXRhdXJldDp7'
        'cHJpbWFyeTpbMSwxLDFdfX0pOwogIFcucnVuKCd0b2dnbGVTaGlwTWVudSgpJyk7IENMUigpOyBX'
        'LnJ1bignZHJhd1NoaXBNZW51KCknKTsKICBvaygnb25seSB0aGUgdHdvIHVubG9ja2VkIHJvd3Mg'
        'bWFrZSBhIGNsYWltJywgaW5Db2woJ2d1bnMnKS5sZW5ndGg9PT0yKTsKICBvaygndGhlIGxvY2tl'
        'ZCBUYXVyZXQgc3RheXMgc2lsZW50IGV2ZW4gd2l0aCBtb3VudCBkYXRhJywKICAgICBpbkNvbCgn'
        'dm9sbGV5JykuZXZlcnkodD0+dC5zIT09JzU3JykpOwp9Clcuc2V0KCdNT1VOVFMnLCB7fSk7Cgpj'
        'b25zb2xlLmxvZygnT25lIGxvb2ssIGFuZCBpdCBpcyB0aGUgZm9ydW0gb25lJyk7CnJlc2V0KCk7'
        'IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsg'
        'Vy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsKQ0xSKCk7IFcucnVuKCdkcmF3U2hpcE1lbnUoKScp'
        'Owpjb25zdCBobHBGb250cyA9IENBTExTLmZpbHRlcihjPT5jLmZuPT09J3NldCBmb250JykubWFw'
        'KGM9PlN0cmluZyhjLmFyZ3NbMF0pKTsKY29uc3QgaGxwQ2VsbHMgPSBXLnJ1bignd2luZG93Ll9z'
        'aGlwUmVjdHMnKS5tYXAocj0+ci54KycsJytyLnkrJywnK3IudysnLCcrci5oKS5qb2luKCd8Jyk7'
        'Cm9rKCdubyBDb3VyaWVyIGxlZnQgaW4gdGhlIGhhbmdhcicsIGhscEZvbnRzLmV2ZXJ5KGY9PmYu'
        'aW5kZXhPZignQ291cmllcicpPDApKTsKb2soJ2l0IHVzZXMgdGhlIGZvcnVtIGZhY2VzJywgaGxw'
        'Rm9udHMuc29tZShmPT5mLmluZGV4T2YoJ1RhaG9tYScpPj0wKSAmJiBobHBGb250cy5zb21lKGY9'
        'PmYuaW5kZXhPZignU2Vnb2UgVUknKT49MCkpOwpvaygndmFsdWVzIGFyZSBubyBsb25nZXIgc2V0'
        'IGluIDggYW5kIDkgcGl4ZWxzJywKICAgaGxwRm9udHMuZmlsdGVyKGY9Pi9TZWdvZSBVSS8udGVz'
        'dChmKSkuc29tZShmPT4vMVs0LTldcHgvLnRlc3QoZikpKTsKb2soJ3RoZSBhY3RpdmUgcm93IGdl'
        'dHMgYSBnbG93IHJpbmcnLCBDQUxMUy5zb21lKGM9PmMuZm49PT0nc2V0IHNoYWRvd0JsdXInKSk7'
        'Cm9rKCdubyByaW5nIGxlYWtzIG91dCBvZiBpdHMgc2F2ZS9yZXN0b3JlJywgYmFsYW5jZWQoKSk7'
        'Cm9rKCdub3RoaW5nIGNob29zZXMgYmV0d2VlbiB0d28gbG9va3MgYW55IG1vcmUnLCAhL0VDT1xc'
        'Lmh1ZC8udGVzdChzcmMpKTsKVy5ydW4oIkVDTy5zY2hlbWU9J3ZvaWQnIik7IENMUigpOyBXLnJ1'
        'bignZHJhd1NoaXBNZW51KCknKTsKb2soJ3RoZSBoYW5nYXIgZHJhd3MgaW4gVm9pZCB0b28nLCBD'
        'QUxMUy5sZW5ndGg+NTApOwpvaygnYW5kIHRoZSByb3dzIGRpZCBub3QgbW92ZScsCiAgIFcucnVu'
        'KCd3aW5kb3cuX3NoaXBSZWN0cycpLm1hcChyPT5yLngrJywnK3IueSsnLCcrci53KycsJytyLmgp'
        'LmpvaW4oJ3wnKT09PWhscENlbGxzKTsKVy5ydW4oIkVDTy5zY2hlbWU9J2ZpcmUnIik7Cgpjb25z'
        'b2xlLmxvZygnRXZlcnl0aGluZyBpcyBkcmF3biBmcm9tIHRoZSBzdXJmYWNlIGtpdCcpOwp7CiAg'
        'cmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD04Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95'
        'ZXIoKV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOwogIENMUigpOyBXLnJ1bignZHJhd1No'
        'aXBNZW51KCknKTsKICAvLyBHcmFkaWVudHMgYXJlIGFsbG93ZWQgYWdhaW4sIGJ1dCBvbmx5IGFz'
        'IGdsb3NzOiBhIHNob3J0IGZhbGwgb2YgbGlnaHQKICAvLyBvdmVyIHRoZSB0b3Agb2YgYSBwbGF0'
        'ZS4gTm9uZSBtYXkgcnVuIHRoZSBoZWlnaHQgb2YgYSBwYW5lbCB0aGUgd2F5IHRoZQogIC8vIG9s'
        'ZCBib3ggZ3JhZGllbnQgZGlkLgogIGNvbnN0IGdyYWRzID0gQ0FMTFMuZmlsdGVyKGM9PmMuZm49'
        'PT0nY3JlYXRlTGluZWFyR3JhZGllbnQnKTsKICBvaygnZXZlcnkgZ3JhZGllbnQgaXMgYSBnbG9z'
        'cywgbm90IGEgZnVsbCBoZWlnaHQgZmlsbCcsCiAgICAgZ3JhZHMubGVuZ3RoPjAgJiYgZ3JhZHMu'
        'ZXZlcnkoZz0+KGcuYXJnc1szXS1nLmFyZ3NbMV0pPD0yMDApKTsKICAvLyBBIGNoYW1mZXJlZCBv'
        'dXRsaW5lIGlzIHNpeCBjb3JuZXJzLiBBIHJlY3RhbmdsZSB3b3VsZCBiZSBmb3VyLgogIGNvbnN0'
        'IGNsb3NlcyA9IENBTExTLmZpbHRlcihjPT5jLmZuPT09J2Nsb3NlUGF0aCcpLmxlbmd0aDsKICBv'
        'aygndGhlIHBhbmVsIGFuZCBldmVyeSBwbGF0ZSBhcmUgY2hhbWZlcmVkLCBub3QgcmVjdGFuZ2xl'
        'cycsIGNsb3Nlcz49OSk7CiAgb2soJ29uZSBzY2FsZSB1bmRlciBlYWNoIG9mIHRoZSB0d28gZ3Jv'
        'dXAgaGVhZGluZ3MnLAogICAgIENBTExTLmZpbHRlcihjPT5jLmZuPT09J3NldCBsaW5lV2lkdGgn'
        'ICYmIGMuYXJnc1swXT09PTEpLmxlbmd0aD4wICYmIGNsb3Nlcz49OSk7CiAgb2soJ2EgcmluZyBp'
        'cyBkcmF3biwgYW5kIG9ubHkgYXJvdW5kIHRoZSBhY3RpdmUgcm93JywKICAgICBDQUxMUy5maWx0'
        'ZXIoYz0+Yy5mbj09PSdzZXQgc2hhZG93Qmx1cicgJiYgYy5hcmdzWzBdPT09NikubGVuZ3RoPT09'
        'Mik7CiAgb2soJ25vdGhpbmcgbGVha3Mgb3V0IG9mIGEgc2F2ZS9yZXN0b3JlJywgYmFsYW5jZWQo'
        'KSk7Cn0KewogIC8vIFRoZSBraXQgaXMgc2hhcmVkLCBzbyB0aGUgaGFuZ2FyIG11c3Qgbm90IHJl'
        'YWNoIHBhc3QgaXQgZm9yIGEgc2hhcGUgb2YKICAvLyBpdHMgb3duLiB0aEJldmVsIGFuZCB0aFBh'
        'bmVsIGJlbG9uZyB0byB0aGUgc2NyZWVucyBub3QgeWV0IHJlYnVpbHQuCiAgY29uc3QgYSA9IHNy'
        'Yy5pbmRleE9mKCdmdW5jdGlvbiBkcmF3U2hpcE1lbnUoKScpOwogIGNvbnN0IGJvZHkgPSBzcmMu'
        'c2xpY2UoYSwgc3JjLmluZGV4T2YoJ2Z1bmN0aW9uIGRyYXdDYWxsTWVudSgpJykpOwogIG9rKCd0'
        'aGUgaGFuZ2FyIHVzZXMgbm8gYmV2ZWwgYW5kIG5vIGdyYWRpZW50IHBhbmVsJywKICAgICBib2R5'
        'LmluZGV4T2YoJ3RoQmV2ZWwnKTwwICYmIGJvZHkuaW5kZXhPZigndGhQYW5lbCcpPDApOwogIG9r'
        'KCdhbmQgbm8gZGlhbG9nIGZyYW1lIG9mIGl0cyBvd24nLCBib2R5LmluZGV4T2YoJ3VpRGlhbG9n'
        'Jyk8MCk7Cn0KewogIC8vIFRoZSBkaWdpdCBpcyB0aGUga2V5Ym9hcmQgc2hvcnRjdXQsIHNvIGl0'
        'IGhhcyB0byBmb2xsb3cgdGhlIGh1bGwgdGhyb3VnaAogIC8vIHRoZSByZWdyb3VwaW5nIHJhdGhl'
        'ciB0aGFuIGNvdW50IHJvd3MuCiAgcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD04Iik7IFcu'
        'c2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOwog'
        'IENMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKICBjb25zdCBycyA9IFcucnVuKCd3aW5k'
        'b3cuX3NoaXBSZWN0cycpOwogIGNvbnN0IGNoaXBYID0gVy5ydW4oJ0hHX05VTScpICsgVy5ydW4o'
        'J0hHX05VTV9XJykvMjsKICBjb25zdCBjaGlwID0gKGtleSk9PnsgY29uc3Qgcj1ycy5maW5kKHI9'
        'PnIuc2hpcD09PWtleSk7CiAgICByZXR1cm4gdGV4dHMoKS5maW5kKHQ9PiB0Lng9PT1yLngrY2hp'
        'cFggJiYgdC55Pj1yLnkgJiYgdC55PD1yLnkrci5oKTsgfTsKICBvaygndGhlIE9zaXJpcyBzaG93'
        'cyA2OiBmaXJzdCBib21iZXIsIHNpeHRoIHJvdycsCiAgICAgY2hpcCgnYm9vc2lyaXMnKSAmJiBj'
        'aGlwKCdib29zaXJpcycpLnM9PT0nNicpOwogIG9rKCdhbmQgdGhlIEJha2hhIHNob3dzIDcnLCBj'
        'aGlwKCdib2Jha2hhJykgJiYgY2hpcCgnYm9iYWtoYScpLnM9PT0nNycpOwogIG9rKCd0aGUgZGln'
        'aXRzIHJ1biAxIHRvIDggc3RyYWlnaHQgZG93biB0aGUgcGFuZWwnLAogICAgIHJzLm1hcChyPT5j'
        'aGlwKHIuc2hpcCkucykuam9pbigpPT09JzEsMiwzLDQsNSw2LDcsOCcpOwp9Cgpjb25zb2xlLmxv'
        'ZygnVGhlIHBhbmVsIGdyb3dzIHdpdGggd2hhdCBpcyBvcGVuJyk7CnsKICBjb25zdCBoZWlnaHQg'
        'PSAoKT0+eyBjb25zdCByPVcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycpOyByZXR1cm4gcltyLmxl'
        'bmd0aC0xXS55K3Jbci5sZW5ndGgtMV0uaCAtIHJbMF0ueTsgfTsKICByZXNldCgpOyBXLnJ1bigi'
        'c2hpcFVubG9ja2VkPTIiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7IFcucnVuKCd0'
        'b2dnbGVTaGlwTWVudSgpOyBkcmF3U2hpcE1lbnUoKScpOwogIGNvbnN0IHNtYWxsID0gaGVpZ2h0'
        'KCk7CiAgcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD04Iik7IFcuc2V0KCdhbGxpZXMnLFtk'
        'ZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKTsgZHJhd1NoaXBNZW51KCknKTsK'
        'ICBjb25zdCBiaWcgPSBoZWlnaHQoKTsKICBvaygnZWlnaHQgb3BlbiBodWxscyBuZWVkIG1vcmUg'
        'cm9vbSB0aGFuIHR3bycsIGJpZyA+IHNtYWxsKTsKICBvaygnYW5kIGl0IHN0aWxsIGZpdHMgb24g'
        'dGhlIGZpZWxkJywKICAgICBXLnJ1bignd2luZG93Ll9zaGlwUmVjdHMnKS5ldmVyeShyPT5yLnk+'
        'PTAgJiYgci55K3IuaDw9NTAwKSk7Cn0KCmNvbnNvbGUubG9nKCdSZWFybSBuZWVkcyBhIGNvcnZl'
        'dHRlLCBub3QgYW55IHNoaXAgYXQgYWxsJyk7CnsKICBjb25zdCBjb3J2ZXR0ZSA9ICgpPT4oe3R5'
        'cGU6J2NvcnZldHRlJywgc2lkZTonYWxseScsIGRlYWQ6ZmFsc2UsIHdhcnBPdXQ6MCwgd2FycDow'
        'fSk7CiAgcmVzZXQoKTsgVy5zZXQoJ2FsbGllcycsIFtdKTsKICBvaygnbm90aGluZyBvbiB0aGUg'
        'ZmllbGQsIG5vIHJlYXJtJywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09ZmFsc2UpOwogIFcuc2V0'
        'KCdhbGxpZXMnLCBbZGVzdHJveWVyKCldKTsKICBvaygnYSBkZXN0cm95ZXIgaXMgYSBoYW5nYXIs'
        'IG5vdCBhbiBhcm1vdXJ5JywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09ZmFsc2UpOwogIFcuc2V0'
        'KCdhbGxpZXMnLCBbY29ydmV0dGUoKV0pOwogIG9rKCdhIGNvcnZldHRlIG9wZW5zIGl0JywgVy5y'
        'dW4oJ3JlYXJtUmVhZHkoKScpPT09dHJ1ZSk7CiAgY29uc3Qgd2FycGluZyA9IGNvcnZldHRlKCk7'
        'IHdhcnBpbmcud2FycCA9IDQwOwogIFcuc2V0KCdhbGxpZXMnLCBbd2FycGluZ10pOwogIG9rKCdv'
        'bmUgc3RpbGwgY29taW5nIG91dCBvZiB0aGUgdm9ydGV4IGRvZXMgbm90JywgVy5ydW4oJ3JlYXJt'
        'UmVhZHkoKScpPT09ZmFsc2UpOwogIGNvbnN0IGRlYWQgPSBjb3J2ZXR0ZSgpOyBkZWFkLmRlYWQg'
        'PSB0cnVlOwogIFcuc2V0KCdhbGxpZXMnLCBbZGVhZF0pOwogIG9rKCdub3IgZG9lcyBhIHdyZWNr'
        'JywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09ZmFsc2UpOwogIFcuc2V0KCdhbGxpZXMnLCBbY29y'
        'dmV0dGUoKV0pOwogIFcuc2V0KCdhbGxpZXMnLCBbY29ydmV0dGUoKV0pOyAgIC8vIGEgbGl2ZSBv'
        'bmUgYWdhaW4sIGFmdGVyIHRoZSB3cmVjayBhYm92ZQogIFcucnVuKCdjbGVhclJlc3VtZUhvbGQo'
        'KScpOyAgICAgIC8vIGFuZCBubyBob2xkIGxlZnQgb3ZlciBmcm9tIGVhcmxpZXIKICAvLyBQcmVz'
        'cyB0aGUgcmVjdGFuZ2xlIHRoZSBiYXIgcmVwb3J0cywgdGhlIHdheSBhIHBsYXllciBkb2VzLiBD'
        'YWxsaW5nCiAgLy8gdG9nZ2xlUmVhcm1NZW51KCkgaGVyZSB0ZXN0ZWQgdGhlIHBhbmVsIGFuZCBu'
        'b3QgdGhlIGJ1dHRvbiwgd2hpY2ggaXMgaG93CiAgLy8gYSBidXR0b24gdGhhdCB3YXMgbmV2ZXIg'
        'd2lyZWQgdG8gYW55dGhpbmcgcGFzc2VkLgogIC8vIENsZWFyIHRoZSBzaGlwIGJ1dHRvbiBmaXJz'
        'dDogYW4gZWFybGllciBjYXNlIGxlZnQgYSByZWN0YW5nbGUgc3RhbmRpbmcKICAvLyB0aGF0IGNv'
        'dmVycyB0aGlzIHNwb3QsIGFuZCBwb2ludGVyQ29uc3VtZWQgYXNrcyBhYm91dCBpdCBvbmUgbGlu'
        'ZSBzb29uZXIuCiAgVy5ydW4oIndpbmRvdy5fc2hpcEJ0blJlY3Q9bnVsbDsgd2luZG93Ll9yZWFy'
        'bUJ0blJlY3Q9e3g6NzA5LHk6NCx3OjIyLGg6NDZ9OyIKICAgICAgKyAiIHBvaW50ZXJDb25zdW1l'
        'ZCh7eDo3MTQseToxMn0pIik7CiAgb2soJ3ByZXNzaW5nIHRoZSBidXR0b24gaW4gdGhlIGJhciBv'
        'cGVucyB0aGUgcGFuZWwnLCBXLmdldCgncmVhcm1NZW51Jyk9PT10cnVlKTsKICBXLnJ1bigicG9p'
        'bnRlckNvbnN1bWVkKHt4OjcxNCx5OjEyfSkiKTsKICBvaygnYW5kIHByZXNzaW5nIGl0IGFnYWlu'
        'IGNsb3NlcyBpdCcsIFcuZ2V0KCdyZWFybU1lbnUnKT09PWZhbHNlKTsKICBXLnJ1bignc2V0UmVh'
        'cm1NZW51KGZhbHNlKScpOwp9Cgpjb25zb2xlLmxvZygnVGhlIHN0YW5kYXJkIGZpdCBpcyBwcm92'
        'YWJseSB0aGUgZ3VuIHRoZSBnYW1lIGhhZCcpOwp7CiAgY29uc3QgcCA9IFcucnVuKCJwcmlEZWYo'
        'J3Byb21ldGhldXMnKSIpOwogIG9rKCd0aGUgUHJvbWV0aGV1cyBjYXJyaWVzIG5vIGZhY3RvcnMg'
        'YXQgYWxsJywgcC5kbWc9PT0xICYmIHAucmF0ZT09PTEpOwogIG9rKCdhbmQgbm8gbGltaXQgb24g'
        'aXRzIHJlYWNoJywgcC5yYW5nZT09PTApOwogIHJlc2V0KCk7IFcucnVuKCJwbGF5ZXIucHJpPSdw'
        'cm9tZXRoZXVzJzsgYXBwbHlMb2Fkb3V0KCkiKTsKICBvaygnc28gdGhlIHJhdGUgb2YgZmlyZSBp'
        'cyB0aGUgb2xkIDI4IHN0ZXBzJywgVy5nZXQoJ3BsYXllcicpLmZSPT09MjgpOwogIGNvbnN0IG0g'
        'PSBXLnJ1bigic2VjRGVmKCdteDY0JykiKTsKICBvaygndGhlIE1YLTY0IGlzIHRoZSBvbGQgbWlz'
        'c2lsZSwgdG8gdGhlIG51bWJlcicsCiAgICAgbS5kbWc9PT0zNSAmJiBtLmNkPT09NDUgJiYgbS5z'
        'cGQ9PT0zLjUgJiYgbS5saWZlPT09MjIwICYmIG0uaG9taW5nPT09dHJ1ZSk7CiAgY29uc3QgYyA9'
        'IFcucnVuKCJzZWNEZWYoJ2N5Y2xvcHMnKSIpOwogIG9rKCdhbmQgdGhlIEN5Y2xvcHMgdGhlIG9s'
        'ZCBib21iJywKICAgICBjLmRtZz09PTgwICYmIGMuY2Q9PT05MCAmJiBjLnNwZD09PTEuNSAmJiBj'
        'LmxpZmU9PT0zMDApOwp9Cgpjb25zb2xlLmxvZygnQSBodWxsIGNhbiBvbmx5IGNhcnJ5IHdoYXQg'
        'aXQgY2FuIGNhcnJ5Jyk7CnsKICByZXNldCgpOyBXLnJ1bigiYXBwbHlTaGlwKCdmaXRvdGgnKSIp'
        'OwogIG9rKCdhIGZpZ2h0ZXIgaXMgZ2l2ZW4gYSBtaXNzaWxlJywgVy5ydW4oImN1clNlYygpLmNs'
        'cyIpPT09J21pc3NpbGUnKTsKICBvaygnYW5kIHRoZSBiYXIgaXMgdG9sZCBzbycsIFcuZ2V0KCdw'
        'bGF5ZXInKS5zZWNUeXBlPT09J21pc3NpbGUnKTsKICBXLnJ1bigiYXBwbHlTaGlwKCdib29zaXJp'
        'cycpIik7CiAgb2soJ2EgYm9tYmVyIGNhbm5vdCBrZWVwIGl0LCBhbmQgZ2V0cyBhIGJvbWInLCBX'
        'LnJ1bigiY3VyU2VjKCkuY2xzIik9PT0nYm9tYicpOwogIG9rKCdhbmQgdGhlIGJhciBhZ2Fpbics'
        'IFcuZ2V0KCdwbGF5ZXInKS5zZWNUeXBlPT09J2JvbWInKTsKICBvaygnb25seSBib21icyBhcmUg'
        'b2ZmZXJlZCB0byBpdCcsCiAgICAgVy5ydW4oInNlY29uZGFyaWVzRm9yKCdib29zaXJpcycpIiku'
        'ZXZlcnkodz0+dy5jbHM9PT0nYm9tYicpKTsKICBvaygnYW5kIG9ubHkgbWlzc2lsZXMgdG8gYSBm'
        'aWdodGVyJywKICAgICBXLnJ1bigic2Vjb25kYXJpZXNGb3IoJ2ZpdG90aCcpIikuZXZlcnkodz0+'
        'dy5jbHM9PT0nbWlzc2lsZScpKTsKICBvaygndGhlIHJhY2sgc2l6ZSBzdGlsbCBjb21lcyBmcm9t'
        'IHRoZSBodWxsJywKICAgICBXLmdldCgncGxheWVyJykuc2VjTWF4ID09PSBXLnJ1bigic2hpcFN0'
        'YXRzKCdib29zaXJpcycpLnNlYyIpKTsKfQoKY29uc29sZS5sb2coJ0EgcmVmaXQgZmlsbHMgdGhl'
        'IHJhY2sgLSB0aGF0IGlzIHdoYXQgbWFrZXMgaXQgYSByZWFybScpOwp7CiAgY29uc3QgY29ydmV0'
        'dGUgPSAoKT0+KHt0eXBlOidjb3J2ZXR0ZScsIHNpZGU6J2FsbHknLCBkZWFkOmZhbHNlLCB3YXJw'
        'T3V0OjAsIHdhcnA6MH0pOwogIHJlc2V0KCk7IFcucnVuKCJhcHBseVNoaXAoJ2ZpdG90aCcpOyBz'
        'Y29yZT0wIik7IFcuc2V0KCdhbGxpZXMnLCBbY29ydmV0dGUoKV0pOwogIFcucnVuKCdwbGF5ZXIu'
        'c2VjQW1tbz0zJyk7CiAgVy5ydW4oJ3RvZ2dsZVJlYXJtTWVudSgpJyk7CiAgVy5ydW4oImZpdFdl'
        'YXBvbignbXg2NCcpIik7CiAgb2soJ2ZpdHRpbmcgd2hhdCBpcyBhbHJlYWR5IGZpdHRlZCB0b3Bz'
        'IHRoZSByYWNrIHVwJywKICAgICBXLmdldCgncGxheWVyJykuc2VjQW1tbyA9PT0gVy5nZXQoJ3Bs'
        'YXllcicpLnNlY01heCk7CiAgb2soJ2FuZCBjbG9zZXMgdGhlIHBhbmVsJywgVy5nZXQoJ3JlYXJt'
        'TWVudScpPT09ZmFsc2UpOwogIC8vIExvY2tlZCB3ZWFwb25zIGNhbm5vdCBiZSB0YWtlbiwgaG93'
        'ZXZlciB0aGV5IGFyZSByZWFjaGVkLgogIFcucnVuKCdwbGF5ZXIuc2VjQW1tbz0zOyB0b2dnbGVS'
        'ZWFybU1lbnUoKScpOwogIFcucnVuKCJmaXRXZWFwb24oJ2hsNycpIik7CiAgb2soJ2Egd2VhcG9u'
        'IGFib3ZlIHRoZSBzY29yZSBjYW5ub3QgYmUgZml0dGVkJywgVy5nZXQoJ3BsYXllcicpLnByaT09'
        'PSdwcm9tZXRoZXVzJyk7CiAgb2soJ2FuZCB0aGUgcGFuZWwgc3RheXMgb3BlbicsIFcuZ2V0KCdy'
        'ZWFybU1lbnUnKT09PXRydWUpOwogIFcucnVuKCdzY29yZT02MDAwJyk7CiAgVy5ydW4oImZpdFdl'
        'YXBvbignaGw3JykiKTsKICBvaygncGFzdCB0aGUgdGhyZXNob2xkIGl0IGNhbicsIFcuZ2V0KCdw'
        'bGF5ZXInKS5wcmk9PT0naGw3Jyk7CiAgb2soJ2FuZCB0aGUgcmF0ZSBvZiBmaXJlIGZvbGxvd3Mg'
        'dGhlIHdlYXBvbicsIFcuZ2V0KCdwbGF5ZXInKS5mUj09PTE3KTsKICBXLnJ1bignc2NvcmU9MDsg'
        'cGxheWVyLnByaT0icHJvbWV0aGV1cyI7IGFwcGx5TG9hZG91dCgpJyk7Cn0KCmNvbnNvbGUubG9n'
        'KCdUaGUgcmVhcm0gcGFuZWwnKTsKewogIGNvbnN0IGNvcnZldHRlID0gKCk9Pih7dHlwZTonY29y'
        'dmV0dGUnLCBzaWRlOidhbGx5JywgZGVhZDpmYWxzZSwgd2FycE91dDowLCB3YXJwOjB9KTsKICBy'
        'ZXNldCgpOyBXLnJ1bigiYXBwbHlTaGlwKCdmaXRvdGgnKTsgc2NvcmU9OTAwMCIpOyBXLnNldCgn'
        'YWxsaWVzJywgW2NvcnZldHRlKCldKTsKICBXLnJ1bigndG9nZ2xlUmVhcm1NZW51KCknKTsKICBD'
        'TFIoKTsgVy5ydW4oJ2RyYXdSZWFybU1lbnUoKScpOwogIGNvbnN0IHJzID0gVy5ydW4oJ3dpbmRv'
        'dy5fcmVhcm1SZWN0cycpOwogIGNvbnN0IHByID0gVy5ydW4oJ3dpbmRvdy5fcmVhcm1QYW5lbFJl'
        'Y3QnKTsKICAvLyBPbmUgcm93IHBlciB3ZWFwb24gdGhhdCBleGlzdHMsIG9wZW4gb3Igbm90OiBh'
        'IGxvY2tlZCBvbmUgaXMgYSB0aGluCiAgLy8gbGluZSwgYW5kIGl0IGlzIHN0aWxsIGEgcm93LiBU'
        'aGUgY291bnQgZm9sbG93cyB0aGUgdGFibGVzIHNvIGEgbmV3CiAgLy8gd2VhcG9uIGRvZXMgbm90'
        'IG1ha2UgdGhpcyBmYWlsIGZvciBubyByZWFzb24uCiAgY29uc3Qgb2ZmZXJlZCA9IFcucnVuKCdQ'
        'UklNQVJJRVMnKS5sZW5ndGggKyBXLnJ1bigic2Vjb25kYXJpZXNGb3IoJ2ZpdG90aCcpIikubGVu'
        'Z3RoOwogIG9rKCdvbmUgcm93IHBlciB3ZWFwb24gb24gb2ZmZXInLCBycy5sZW5ndGg9PT1vZmZl'
        'cmVkKTsKICBvaygnZXZlcnkgcm93IGlzIGluc2lkZSB0aGUgcGFuZWwnLAogICAgIHJzLmV2ZXJ5'
        'KHI9PnIueD49cHIueCAmJiByLngrci53PD1wci54K3ByLncgJiYgci55Pj1wci55ICYmIHIueSty'
        'Lmg8PXByLnkrcHIuaCkpOwogIG9rKCd0aGUgcGFuZWwgZml0cyBvbiB0aGUgZmllbGQnLCBwci55'
        'Pj0wICYmIHByLnkrcHIuaDw9NTAwICYmIHByLng+PTAgJiYgcHIueCtwci53PD04MDApOwogIG9r'
        'KCdubyBDb3VyaWVyIGFueXdoZXJlJywKICAgICBDQUxMUy5maWx0ZXIoYz0+Yy5mbj09PSdzZXQg'
        'Zm9udCcpLmV2ZXJ5KGM9PlN0cmluZyhjLmFyZ3NbMF0pLmluZGV4T2YoJ0NvdXJpZXInKTwwKSk7'
        'CiAgb2soJ3RoZSBmaXR0ZWQgd2VhcG9uIGdldHMgdGhlIHJpbmcnLCBDQUxMUy5zb21lKGM9PmMu'
        'Zm49PT0nc2V0IHNoYWRvd0JsdXInKSk7CiAgb2soJ25vdGhpbmcgbGVha3Mgb3V0IG9mIGEgc2F2'
        'ZS9yZXN0b3JlJywgYmFsYW5jZWQoKSk7CiAgLy8gQSBjbGljayBpbnNpZGUgdGhlIHBhbmVsIHRo'
        'YXQgaGl0IG5vIHJvdyBtdXN0IG5vdCBjbG9zZSBpdCwgdGhlIHNhbWUKICAvLyBydWxlIHRoZSBo'
        'YW5nYXIgYW5kIHRoZSBzdXBwb3J0IG1lbnUgZm9sbG93LgogIFcucnVuKGBwb2ludGVyQ29uc3Vt'
        'ZWQoe3g6JHtwci54KzQwfSx5OiR7cHIueSs2fX0pYCk7CiAgb2soJ2EgY2xpY2sgb24gdGhlIGhl'
        'YWRlciBrZWVwcyBpdCBvcGVuJywgVy5nZXQoJ3JlYXJtTWVudScpPT09dHJ1ZSk7CiAgVy5ydW4o'
        'YHBvaW50ZXJDb25zdW1lZCh7eDoke3ByLngtMTJ9LHk6JHtwci55K3ByLmgvMn19KWApOwogIG9r'
        'KCdhIGNsaWNrIGJlc2lkZSBpdCBjbG9zZXMgaXQnLCBXLmdldCgncmVhcm1NZW51Jyk9PT1mYWxz'
        'ZSk7Cn0KewogIC8vIEJlbG93IHRoZSB0aHJlc2hvbGQgdGhlIEhMLTcgaXMgYSB0aGluIGxpbmUs'
        'IG5vdCBhIHJvdyB0aGF0IGNhbiBiZSB0YWtlbi4KICBjb25zdCBjb3J2ZXR0ZSA9ICgpPT4oe3R5'
        'cGU6J2NvcnZldHRlJywgc2lkZTonYWxseScsIGRlYWQ6ZmFsc2UsIHdhcnBPdXQ6MCwgd2FycDow'
        'fSk7CiAgcmVzZXQoKTsgVy5ydW4oImFwcGx5U2hpcCgnZml0b3RoJyk7IHNjb3JlPTAiKTsgVy5z'
        'ZXQoJ2FsbGllcycsIFtjb3J2ZXR0ZSgpXSk7CiAgVy5ydW4oJ3RvZ2dsZVJlYXJtTWVudSgpOyBk'
        'cmF3UmVhcm1NZW51KCknKTsKICBjb25zdCBycyA9IFcucnVuKCd3aW5kb3cuX3JlYXJtUmVjdHMn'
        'KTsKICBvaygnYSBsb2NrZWQgd2VhcG9uIHJlcG9ydHMgbm8ga2V5JywgcnMuc29tZShyPT5yLmtl'
        'eT09PW51bGwpKTsKICBvaygnYW5kIGl0cyBsaW5lIGlzIHRoaW5uZXIgdGhhbiBhIHJvdyB0aGF0'
        'IGNhbiBiZSB0YWtlbicsCiAgICAgTWF0aC5taW4oLi4ucnMubWFwKHI9PnIuaCkpIDwgTWF0aC5t'
        'YXgoLi4ucnMubWFwKHI9PnIuaCkpKTsKICBXLnJ1bignc2V0UmVhcm1NZW51KGZhbHNlKTsgc2Nv'
        'cmU9MCcpOwp9Cgpjb25zb2xlLmxvZygnVGhlIHRpdGxlIHNjcmVlbicpOwovLyBkcmF3VGl0bGUg'
        'aXMgdG9vIHRhbmdsZWQgdXAgd2l0aCB0aGUgYmFja2Ryb3AgdG8gcnVuIGhlcmUsIHNvIHdoYXQg'
        'aXMKLy8gY2hlY2tlZCBpcyB0aGUgdHdvIHRoaW5ncyB0aGF0IG1hZGUgaXQgbG9vayB0aGUgd2F5'
        'IGl0IGRpZC4Kb2soJ25vIG9wYXF1ZSBzaGVldCBvdmVyIHRoZSBza3kgYW55IG1vcmUnLCAhL2Zp'
        'bGxTdHlsZT0ncmdiYVwoMCwwLDgsMFwuNzhcKSc7Y3R4XC5maWxsUmVjdFwoMCwwLFcsSFwpLy50'
        'ZXN0KHNyYykpOwpvaygnd2hhdCBpcyBsZWZ0IGlzIGEgZ3JhZGllbnQsIHNvIHRoZSBiYWNrZHJv'
        'cCBzaG93cyB0aHJvdWdoIHRoZSB0b3AnLAogICAvY3JlYXRlTGluZWFyR3JhZGllbnRcKDAsIDAs'
        'IDAsIEhcKVtcc1xTXXswLDI2MH0/cmdiYVwoMCwwLDgsMFwuMjBcKS8udGVzdChzcmMpKTsKb2so'
        'J3RoZSBwYXN0ZWQgbG9nbyBhbmQgaXRzIDMgYXJlIGdvbmUnLAogICAhL19sb2dvUHJvY2Vzc2Vk'
        'Ly50ZXN0KHNyYykgJiYgIS9mc19sb2dvLy50ZXN0KHNyYykpOwpvaygndGhlIHRpdGxlIGlzIHNl'
        'dCBpbiB0aGUgdGhlbWUgZmFjZSBpbnN0ZWFkJywgL0ZSRUVTUEFDRS8udGVzdChzcmMpICYmIC90'
        'aExhYmVsXCg1NFwpLy50ZXN0KHNyYykpOwpvaygnYSBmcmVzaCBiYWNrZHJvcCBpcyByb2xsZWQg'
        'ZXZlcnkgdGltZSB0aGUgdGl0bGUgY29tZXMgdXAnLAogICAvZnVuY3Rpb24gZW50ZXJUaXRsZVwo'
        'XClce1tcc1xTXXswLDMwMH0/bmViQ3VyID0gTkVCX05BTUVTW1xzXFNdezAsMTIwfT9yb2xsQm9k'
        'aWVzXChcKS8udGVzdChzcmMpKTsKb2soJ2FuZCBhIGJvZHkgdGhhdCBsZWF2ZXMgdGhlIHRpdGxl'
        'IGlzIHJlcGxhY2VkLCBub3Qgd3JhcHBlZCByb3VuZCcsCiAgIC9pZlwoR1M9PT0ndGl0bGUnXClc'
        'eyByb2xsQm9kaWVzXChcKTsgcmV0dXJuOyBcfS8udGVzdChzcmMpKTsKb2soJ3RoZSB0aXRsZSBr'
        'ZWVwcyBtb3Zpbmcgd2hpbGUgaXQgc2l0cyB0aGVyZScsCiAgIC9pZlwoR1M9PT0ndGl0bGUnXClc'
        'eyBmY1wrXCs7IHRpY2tTdGFyc1woXCk7IHRpY2tOZWJ1bGFcKFwpOyByZXR1cm47IFx9Ly50ZXN0'
        'KHNyYykpOwpvaygnVHJ5IEFnYWluIGdvZXMgYmFjayB0byB0aGUgdGl0bGUgcmF0aGVyIHRoYW4g'
        'aW50byB0aGUgbmV4dCBydW4nLAogICAvZnVuY3Rpb24gdG9UaXRsZU9yTGF1bmNoXChcKVx7W1xz'
        'XFNdezAsMTYwfT9HUz09PSdnYW1lb3ZlcidcKXsgZW50ZXJUaXRsZVwoXCkvLnRlc3Qoc3JjKSk7'
        'Cm9rKCdhbmQgbm90aGluZyBjYWxscyBsYXVuY2hHYW1lIHN0cmFpZ2h0IGZyb20gdGhlIGdhbWUg'
        'b3ZlciBzY3JlZW4nLAogICAhL2dhbWVPdmVyQXQ+MTUwMFwpIGxhdW5jaEdhbWVcKFwpLy50ZXN0'
        'KHNyYykpOwoKY29uc29sZS5sb2coJ0JhciBidXR0b24gcGxhY2VtZW50Jyk7CnsKICAvLyBUaGUg'
        'c2hpcCBzd2l0Y2ggYW5kIHRoZSByZWFybSBidXR0b24gYXJlIGRyYXduIGFzIG9uZSBwYWlyIG5v'
        'dywgc28gdGhlCiAgLy8gc25pcHBldCBjb3ZlcnMgYm90aCBhbmQgYm90aCBhcmUgY2hlY2tlZC4K'
        'ICBjb25zdCBhID0gc3JjLmluZGV4T2YoJyAgLy8gU0hJUCBTV0lUQ0ggYW5kIFJFQVJNJyksIGIg'
        'PSBzcmMuaW5kZXhPZignICAvLyBTRVRUSU5HUyBhbmQgUEFVU0UnKTsKICBjb25zdCBzbmlwID0g'
        'c3JjLnNsaWNlKGEsIGIpOwogIFcucnVuKCJ2YXIgSDI9NTQ7IHNoaXBNZW51PWZhbHNlOyByZWFy'
        'bU1lbnU9ZmFsc2U7IGFsbGllcz1bXTsiCiAgICAgICsgIiB3aW5kb3cuX3NoaXBCdG5SZWN0PXVu'
        'ZGVmaW5lZDsgd2luZG93Ll9yZWFybUJ0blJlY3Q9dW5kZWZpbmVkOyAiICsgc25pcCk7CiAgY29u'
        'c3QgciA9IFcucnVuKCd3aW5kb3cuX3NoaXBCdG5SZWN0JyksIHJtID0gVy5ydW4oJ3dpbmRvdy5f'
        'cmVhcm1CdG5SZWN0Jyk7CiAgb2soJ3RoZSBzaGlwIGJ1dHRvbiBzaXRzIGJldHdlZW4gdGlja2V0'
        'cyAoNjY1KSBhbmQgZ2VhciAoNzQ4KScsIHIgJiYgci54PjY2NSAmJiByLngrci53PDc0OCk7CiAg'
        'b2soJ3RoZSByZWFybSBidXR0b24gc2l0cyBiZXNpZGUgaXQsIGFsc28gY2xlYXIgb2YgdGhlIGdl'
        'YXInLAogICAgIHJtICYmIHJtLnggPj0gci54K3IudyAmJiBybS54K3JtLncgPCA3NDgpOwogIG9r'
        'KCd0aGV5IGRvIG5vdCBvdmVybGFwJywgcm0gJiYgcm0ueCA+PSByLnggKyByLncpOwogIFcucnVu'
        'KCJGUzFfTU9ERT10cnVlOyAiICsgc25pcCk7CiAgb2soJ25laXRoZXIgYnV0dG9uIGluIEZTMSBt'
        'b2RlJywKICAgICBXLnJ1bignd2luZG93Ll9zaGlwQnRuUmVjdCcpPT09bnVsbCAmJiBXLnJ1bign'
        'd2luZG93Ll9yZWFybUJ0blJlY3QnKT09PW51bGwpOwogIFcucnVuKCdGUzFfTU9ERT1mYWxzZScp'
        'Owp9CmNvbnNvbGUubG9nKCdDeWNsZSBzY2FsaW5nIGtlZXBzIHRoZSBodWxsJyk7Cm9rKCduZXh0'
        'V2F2ZSBzY2FsZXMgZnJvbSB0aGUgaHVsbCBiYXNlLCBub3QgZnJvbSAxMDAnLCBzcmMuaW5jbHVk'
        'ZXMoJ3BsYXllci5tYXhIcD1NYXRoLnJvdW5kKChwbGF5ZXIuYmFzZUhwfHwxMDApKnBtKTsnKSk7'
        'Cm9rKCdyZXNwYXduIHJlc3RvcmVzIHRoZSBmdWxsIGh1bGwnLCBzcmMuaW5jbHVkZXMoJ3BsYXll'
        'ci5ocD1wbGF5ZXIubWF4SHA7cGxheWVyLng9ODA7JykpOwoKY29uc29sZS5sb2coJ1xuJyArIChm'
        'YWlscyA/IGZhaWxzKycgRkFJTEVEJyA6ICdhbGwgcGFzc2VkJykpOwpwcm9jZXNzLmV4aXQoZmFp'
        'bHM/MTowKTsK'
    ),
    'pausesim.js': (
        'Ly8gUGF1c2UgYW5kIHBhbmVsIHN0YXRlIHNpbXVsYXRpb24uIFB1bGxzIHRoZSBSRUFMIG1lbnUg'
        'YW5kIHNldHRpbmdzCi8vIGZ1bmN0aW9ucyBvdXQgb2YgdGhlIGxvZ2ljIGZpbGUgYW5kIHJlcGxh'
        'eXMgdGFwIHNlcXVlbmNlcyBhZ2FpbnN0IHRoZW0sCi8vIGxvb2tpbmcgZm9yIGEgc3RhdGUgdGhl'
        'IHBsYXllciBjYW4gcmVhY2ggd2hlcmUgYSBwYW5lbCBpcyBvcGVuIHdoaWxlIHRoZQovLyBnYW1l'
        'IGtlZXBzIHJ1bm5pbmcuCi8vCi8vIFRoZSB0YXAgb3JkZXIgYmVsb3cgbWlycm9ycyB0aGUgbW91'
        'c2Vkb3duIGFuZCB0b3VjaHN0YXJ0IGhhbmRsZXJzLCB3aGljaAovLyBsaXZlIGluc2lkZSBhZGRF'
        'dmVudExpc3RlbmVyIGNsb3N1cmVzIGFuZCBjYW5ub3QgYmUgcHVsbGVkIG91dC4gSWYgdGhhdAov'
        'LyBvcmRlciBjaGFuZ2VzIGluIHRoZSBsb2dpYyBmaWxlLCB0aGlzIG1pcnJvciBoYXMgdG8gY2hh'
        'bmdlIHdpdGggaXQuCi8vCi8vIFVzYWdlOiBub2RlIHBhdXNlc2ltLmpzIDxsb2dpYy5odG1sPgpj'
        'b25zdCBmcyA9IHJlcXVpcmUoJ2ZzJyk7CmNvbnN0IGh0bWwgPSBmcy5yZWFkRmlsZVN5bmMocHJv'
        'Y2Vzcy5hcmd2WzJdLCAndXRmOCcpOwpjb25zdCBzcmMgPSBodG1sLm1hdGNoKC88c2NyaXB0W14+'
        'XSo+KFtcc1xTXSopPFwvc2NyaXB0Pi8pWzFdOwoKZnVuY3Rpb24gYmxvY2tFbmQocywgaSl7CiAg'
        'bGV0IGogPSBzLmluZGV4T2YoJ3snLCBpKSwgZGVwdGggPSAwOwogIGZvcig7IGogPCBzLmxlbmd0'
        'aDsgaisrKXsKICAgIGNvbnN0IGMgPSBzW2pdOwogICAgaWYoYyA9PT0gJ3snKSBkZXB0aCsrOwog'
        'ICAgZWxzZSBpZihjID09PSAnfScpeyBkZXB0aC0tOyBpZighZGVwdGgpIHJldHVybiBqICsgMTsg'
        'fQogICAgZWxzZSBpZihjID09PSAiJyIgfHwgYyA9PT0gJyInIHx8IGMgPT09ICdgJyl7IGNvbnN0'
        'IHEgPSBjOyBqKys7IHdoaWxlKGogPCBzLmxlbmd0aCAmJiBzW2pdICE9PSBxKSBqICs9IChzW2pd'
        'ID09PSAnXFwnKSA/IDIgOiAxOyB9CiAgICBlbHNlIGlmKHMuc3RhcnRzV2l0aCgnLy8nLCBqKSkg'
        'aiA9IHMuaW5kZXhPZignXG4nLCBqKTsKICAgIGVsc2UgaWYocy5zdGFydHNXaXRoKCcvKicsIGop'
        'KSBqID0gcy5pbmRleE9mKCcqLycsIGopICsgMTsKICB9CiAgdGhyb3cgbmV3IEVycm9yKCd1bmJh'
        'bGFuY2VkJyk7Cn0KZnVuY3Rpb24gZm4obmFtZSwgb3B0aW9uYWwpewogIGNvbnN0IGkgPSBzcmMu'
        'aW5kZXhPZignXG5mdW5jdGlvbiAnICsgbmFtZSArICcoJyk7CiAgaWYoaSA8IDApeyBpZihvcHRp'
        'b25hbCkgcmV0dXJuICcnOyB0aHJvdyBuZXcgRXJyb3IoJ21pc3NpbmcgZnVuY3Rpb24gJyArIG5h'
        'bWUpOyB9CiAgcmV0dXJuIHNyYy5zbGljZShpICsgMSwgYmxvY2tFbmQoc3JjLCBpKSk7Cn0KCi8v'
        'IFRoZSB3ZWFwb24gdGFibGVzIGFuZCB0aGUgcmVhcm0gcGFuZWwncyBtZWFzdXJlbWVudHMsIHNv'
        'IHRoZSBiYXIgYW5kIHRoZQovLyBwYXVzZSBsb2dpYyBjYW4gc2VlIHdoYXQgdGhleSBub3cgcmVh'
        'Y2ggZm9yLgpjb25zdCB3cG5EZWNsICA9IHNyYy5tYXRjaCgvY29uc3QgUExBWUVSX0ZSX0JBU0Vb'
        'XHNcU10qP1xuXF07LylbMF07CmNvbnN0IHdwbkRlY2wyID0gc3JjLm1hdGNoKC9jb25zdCBTRUNP'
        'TkRBUklFUyA9IFxbW1xzXFNdKj9cblxdOy8pWzBdOwpjb25zdCBybURlY2wgICA9IHNyYy5tYXRj'
        'aCgvY29uc3QgUk1fV1tcc1xTXSo/Y29uc3QgUk1fQ09MU19TRUMgPSBcW1tcc1xTXSo/XG5cXTsv'
        'KVswXTsKLy8gcG9pbnRlckNvbnN1bWVkIHJlYWNoZXMgZm9yIHRoZSB0aXRsZSBvbiBhIGZpbmlz'
        'aGVkIHJ1bi4gU3RhcnRpbmcgYSBydW4KLy8gaXMgbm90IHdoYXQgdGhlc2UgZmlsZXMgdGVzdCwg'
        'c28gaXQgaXMgYSBzdHViLgpjb25zdCB3cG5TdGF0ZSA9ICdsZXQgcmVhcm1NZW51ID0gZmFsc2U7'
        'IGxldCByZXN1bWVIb2xkID0gZmFsc2U7JwogIC8vIFRoZSBiYXIgYXNrcyB3aGVyZSB0aGUgcG9p'
        'bnRlciBpcyBzaXR0aW5nOyBub3RoaW5nIGhvdmVycyBpbiBhIHRlc3QuCiAgKyAnIGNvbnN0IEhP'
        'VkVSID0ge3g6LTEsIHk6LTF9OyBmdW5jdGlvbiB0b1RpdGxlT3JMYXVuY2goKXt9OyBjb25zdCBX'
        'UE5fU0VFTiA9IHt9OyBjb25zdCBVSV9XRUFQT05TID0gZmFsc2U7JzsKY29uc3QgbmFtZXMgPSBb'
        'CiAgJ3N5bmNDdXJzb3InLCdob3ZlcmluZycsCiAgJ3BhbmVsT3BlbicsJ2hvbGRSZXN1bWUnLCdj'
        'bGVhclJlc3VtZUhvbGQnLCdkcmF3UmVzdW1lSGludCcsCiAgJ2FwcGx5TG9hZG91dCcsJ3JlYXJt'
        'RnVsbCcsJ2N1clByaScsJ2N1clNlYycsJ3ByaURlZicsJ3NlY0RlZicsJ2h1bGxTZWNDbHMnLAog'
        'ICd3ZWFwb25OYW1lJywnd2VhcG9uT3BlbicsJ3NlY29uZGFyaWVzRm9yJywnZGVmYXVsdFNlYycs'
        'J2NvcnZldHRlT25GaWVsZCcsCiAgJ3JlYXJtUmVhZHknLCdzZXRSZWFybU1lbnUnLCd0b2dnbGVS'
        'ZWFybU1lbnUnLCdmaXRXZWFwb24nLCdyZWFybUxheW91dCcsCiAgJ2RyYXdSZWFybU1lbnUnLCdk'
        'cmF3UmVhcm1JY29uJywncmVhcm1Hcm91cHMnLCdybVZhbHVlJywndGlja1dlYXBvblVubG9ja3Mn'
        'LAogICdpbnNpZGVQYW5lbCcsCiAgJ3RoQ2hhbWZlclBhdGgnLCd0aFBsYXRlJywndGhHbG93UGF0'
        'aCcsJ3RoQnJhY2tldHMnLCd0aFNjYWxlJywndGhGcmFtZScsJ3RoUkdCQScsJ3RoR2xvc3MnLCd0'
        'aEN1dEdsaW50Jywnc2V0U2hpcE1lbnUnLCAndG9nZ2xlU2hpcE1lbnUnLCAnc2hpcFN3YXBSZWFk'
        'eScsICdzZXRDYWxsTWVudScsICd0b2dnbGVDYWxsTWVudScsCiAgICAgICAgICAgICAgICdzZXRT'
        'ZXR0aW5ncycsICdwb2ludGVyQ29uc3VtZWQnLCAnc2hpcE9mZmVyZWQnLCAnc2hpcEZhYycsICdo'
        'dWxsRmFjJywKICAgICAgICAgICAgICAgJ2hhbmdhckZhY3MnLCAnaXNIYW5nYXJTaGlwJywgJ2Nv'
        'bG9zc3VzT25GaWVsZCcsICdoYW5nYXJTZXJ2ZXMnLCAnaHVsbENsYXNzJ107CmNvbnN0IG9wdGlv'
        'bmFsID0gWydzeW5jUGF1c2UnXTsKCmNvbnN0IHdvcmxkID0gYAogIGNvbnN0IFc9ODAwLCBIPTUw'
        'MCwgSFVEX0g9NTQ7CiAgbGV0IEdTPSdwbGF5aW5nJywgcGF1c2VkPWZhbHNlLCB1c2VyUGF1c2Vk'
        'PWZhbHNlOwogIGxldCBzaGlwTWVudT1mYWxzZSwgY2FsbE1lbnU9ZmFsc2UsIHNldHRpbmdzT3Bl'
        'bj1mYWxzZSwgc2V0dGluZ3NQYWdlPTA7CiAgbGV0IHNldHRpbmdzV2FzUGF1c2VkPWZhbHNlLCBz'
        'aGlwVW5sb2NrZWQ9Mywgc2hpcFN3YXBXYXZlPS0xLCB3YXZlPTE7CiAgbGV0IEZTMV9NT0RFPWZh'
        'bHNlLCBhbGxpZXM9W10sIE1PVVNFPXt4OjAseTowfTsKICBsZXQgZW1wT3V0PTAsIGFsbHlDZD0w'
        'LCB0aWNrZXRzPXtjcnVpc2VyOjl9LCBHRUFSX09LPXRydWU7CiAgY29uc3QgZG9jdW1lbnQ9e2Jv'
        'ZHk6e2NsYXNzTGlzdDp7YWRkKCl7fSwgcmVtb3ZlKCl7fX19fTsKICBjb25zdCB3aW5kb3c9e307'
        'CiAgY29uc3QgSFVMTF9GQUM9e2RldHlwaG9uOid2YXN1ZGFuJywgZGVoYXRzaGVwc3V0Oid2YXN1'
        'ZGFuJywgZGVvcmlvbnJpZ2h0Oid0ZXJyYW4nLCBzZGNvbG9zc3VzOidndHZhJ307CiAgY29uc3Qg'
        'UExBWUVSX1NISVBTPVt7a2V5OidmaXRvdGgnLCBmYWM6J3Zhc3VkYW4nfSwge2tleTonZmlob3J1'
        'cycsIGZhYzondmFzdWRhbid9LCB7a2V5Oidib29zaXJpcycsIGZhYzondmFzdWRhbid9XTsKICBs'
        'ZXQgZm9yY2VkUHJldj0nJzsgICAvLyBubyBtaXNzaW9uLWxlbnQgaHVsbCBpbiB0aGVzZSB0ZXN0'
        'cwogIGxldCBwbGF5ZXI9e3NoaXA6J2ZpdG90aCcsIHg6NDAwLCB5OjI1MH07CiAgZnVuY3Rpb24g'
        'aW5KdW1wKCl7IHJldHVybiBmYWxzZTsgfQogIGZ1bmN0aW9uIGFsbHlSZWFkeSgpeyByZXR1cm4g'
        'dHJ1ZTsgfQogIGZ1bmN0aW9uIHN3YXBTaGlwKCl7fQogIGZ1bmN0aW9uIHJlZmluZVRpY2tldCgp'
        'e30KICBmdW5jdGlvbiBjYWxsQWxseSgpe30KICBmdW5jdGlvbiBzZXR0aW5nc0NsaWNrKCl7fQog'
        'IGZ1bmN0aW9uIGZpcmVTZWNvbmRhcnkoKXt9CiAgJHt3cG5EZWNsfQogICR7d3BuRGVjbDJ9CiAg'
        'JHtybURlY2x9CiAgJHt3cG5TdGF0ZX0KICAke25hbWVzLm1hcChuPT5mbihuKSkuam9pbignXG4n'
        'KX0KICAke29wdGlvbmFsLm1hcChuPT5mbihuLCB0cnVlKSkuam9pbignXG4nKX0KICAvLyBUaGUg'
        'dGhyZWUgSFVEIGJ1dHRvbnMsIGxhaWQgb3V0IGFzIHRoZSBiYXIgZG9lcy4KICB3aW5kb3cuX3No'
        'aXBCdG5SZWN0ICA9IHt4OjYwMCwgeToxMCwgdzo0MCwgaDozNH07CiAgd2luZG93Ll9hbGx5QnRu'
        'UmVjdCAgID0ge3g6NjU1LCB5OjEwLCB3OjQwLCBoOjM0fTsKICB3aW5kb3cuX3NldHRpbmdzQnRu'
        'UmVjdCA9IHt4Ojc0OCwgeToxMCwgdzo0MCwgaDozNH07CiAgd2luZG93Ll9wYXVzZUJ0blJlY3Qg'
        'ID0ge3g6NzAwLCB5OjEwLCB3OjQwLCBoOjM0fTsKICAvLyBNaXJyb3Igb2YgdGhlIGhhbmRsZXIg'
        'b3JkZXIgaW4gbW91c2Vkb3duIC8gdG91Y2hzdGFydC4KICBmdW5jdGlvbiB0YXAoeCwgeSl7CiAg'
        'ICBjb25zdCBwPXt4OngsIHk6eX07CiAgICBjb25zdCBoaXQ9KHIpPT4gciAmJiBwLng+PXIueCAm'
        'JiBwLng8PXIueCtyLncgJiYgcC55Pj1yLnkgJiYgcC55PD1yLnkrci5oOwogICAgaWYocG9pbnRl'
        'ckNvbnN1bWVkKHApKSByZXR1cm47CiAgICBpZihzZXR0aW5nc09wZW4peyBzZXR0aW5nc0NsaWNr'
        'KHAueCxwLnkpOyByZXR1cm47IH0KICAgIGlmKGhpdCh3aW5kb3cuX3NldHRpbmdzQnRuUmVjdCkp'
        'eyBzZXRTZXR0aW5ncyh0cnVlKTsgcmV0dXJuOyB9CiAgICBpZihoaXQod2luZG93Ll9wYXVzZUJ0'
        'blJlY3QpKXsKICAgICAgLy8gQWZ0ZXIgdGhlIGZpeCB0aGUgcGF1c2UgYnV0dG9uIG93bnMgaXRz'
        'IG93biBmbGFnOyBiZWZvcmUgaXQsIGl0CiAgICAgIC8vIHdyb3RlIHRoZSBzaGFyZWQgb25lLgog'
        'ICAgICBpZih0eXBlb2Ygc3luY1BhdXNlID09PSAnZnVuY3Rpb24nKXsgdXNlclBhdXNlZD0hdXNl'
        'clBhdXNlZDsgc3luY1BhdXNlKCk7IH0KICAgICAgZWxzZSBwYXVzZWQ9IXBhdXNlZDsKICAgICAg'
        'cmV0dXJuOwogICAgfQogICAgaWYoaGl0KHdpbmRvdy5fc2VjQnRuUmVjdCkpeyBmaXJlU2Vjb25k'
        'YXJ5KCk7IHJldHVybjsgfQogIH0KICByZXR1cm4ge2dldDooayk9PmV2YWwoayksIHNldDooayx2'
        'KT0+ZXZhbChrKyc9dicpLCBydW46KGNvZGUpPT5ldmFsKGNvZGUpfTtgOwoKY29uc3QgVyA9IG5l'
        'dyBGdW5jdGlvbih3b3JsZCkoKTsKY29uc3QgZml4ZWQgPSBXLnJ1bigidHlwZW9mIHN5bmNQYXVz'
        'ZSA9PT0gJ2Z1bmN0aW9uJyIpOwpsZXQgZmFpbHMgPSAwOwpmdW5jdGlvbiBvayhsYWJlbCwgY29u'
        'ZCl7IGNvbnNvbGUubG9nKChjb25kID8gJyAgb2sgICAgJyA6ICcgIEZBSUwgICcpICsgbGFiZWwp'
        'OyBpZighY29uZCkgZmFpbHMrKzsgfQoKY29uc3QgR0VBUiAgPSBbNzY4LCAyN107CmNvbnN0IFBB'
        'VVNFID0gWzcyMCwgMjddOwpjb25zdCBTSElQQiA9IFs2MjAsIDI3XTsKY29uc3QgRklFTEQgPSBb'
        'NDAwLCAzMDBdOwoKZnVuY3Rpb24gcmVzZXQoKXsKICBXLnJ1bigic2hpcE1lbnU9ZmFsc2U7IGNh'
        'bGxNZW51PWZhbHNlOyBzZXR0aW5nc09wZW49ZmFsc2U7IHBhdXNlZD1mYWxzZTsgdXNlclBhdXNl'
        'ZD1mYWxzZTsgc2V0dGluZ3NXYXNQYXVzZWQ9ZmFsc2U7IHdpbmRvdy5fc2hpcFJlY3RzPVtdOyB3'
        'aW5kb3cuX2NhbGxSZWN0cz1bXTsiKTsKICBXLnNldCgnYWxsaWVzJywgW3tpbWc6J2RldHlwaG9u'
        'Jywgc21hbGw6ZmFsc2UsIGRlYWQ6ZmFsc2UsIHdhcnBPdXQ6ZmFsc2V9XSk7Cn0KLy8gQSBwYW5l'
        'bCBvbiBzY3JlZW4gd2hpbGUgdGhlIGdhbWUga2VlcHMgcnVubmluZyBpcyB0aGUgZmFpbHVyZSB3'
        'ZSBsb29rIGZvci4KZnVuY3Rpb24gYnJva2VuKCl7CiAgY29uc3QgcyA9IFcucnVuKCIoe3BhdXNl'
        'ZDpwYXVzZWQsIHNoaXBNZW51OnNoaXBNZW51LCBjYWxsTWVudTpjYWxsTWVudSwgc2V0dGluZ3NP'
        'cGVuOnNldHRpbmdzT3Blbn0pIik7CiAgcmV0dXJuIChzLnNldHRpbmdzT3BlbiB8fCBzLnNoaXBN'
        'ZW51IHx8IHMuY2FsbE1lbnUpICYmICFzLnBhdXNlZDsKfQpmdW5jdGlvbiBzdGF0ZSgpewogIGNv'
        'bnN0IHMgPSBXLnJ1bigiKHtwYXVzZWQ6cGF1c2VkLCBzaGlwTWVudTpzaGlwTWVudSwgY2FsbE1l'
        'bnU6Y2FsbE1lbnUsIHNldHRpbmdzT3BlbjpzZXR0aW5nc09wZW59KSIpOwogIHJldHVybiAocy5z'
        'aGlwTWVudT8nc2hpcCAnOicnKSArIChzLmNhbGxNZW51PydjYWxsICc6JycpICsgKHMuc2V0dGlu'
        'Z3NPcGVuPydzZXR0aW5ncyAnOicnKQogICAgICAgKyAocy5wYXVzZWQ/J1BBVVNFRCc6J3J1bm5p'
        'bmcnKTsKfQoKY29uc29sZS5sb2coZml4ZWQgPyAnTG9naWMgZmlsZSBoYXMgdGhlIGRlcml2ZWQg'
        'cGF1c2UnIDogJ0xvZ2ljIGZpbGUgd3JpdGVzIHBhdXNlIGZyb20gc2V2ZXJhbCBwbGFjZXMnKTsK'
        'CmNvbnNvbGUubG9nKCdcbk9wZW5pbmcgYSBwYW5lbCBoYXMgdG8gc3RvcCB0aGUgZ2FtZScpOwpy'
        'ZXNldCgpOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOwpvaygnc3dpdGNoIG1lbnUgcGF1c2Vz'
        'JywgVy5nZXQoJ3BhdXNlZCcpPT09dHJ1ZSAmJiBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUpOwpy'
        'ZXNldCgpOyBXLnJ1bigndG9nZ2xlQ2FsbE1lbnUoKScpOwpvaygnY2FsbCBtZW51IHBhdXNlcycs'
        'IFcuZ2V0KCdwYXVzZWQnKT09PXRydWUpOwpyZXNldCgpOyBXLnJ1bignc2V0U2V0dGluZ3ModHJ1'
        'ZSknKTsKb2soJ3NldHRpbmdzIHBhdXNlcycsIFcuZ2V0KCdwYXVzZWQnKT09PXRydWUpOwoKY29u'
        'c29sZS5sb2coJ1xuVGhlIHRhcCBzZXF1ZW5jZSBmcm9tIHRoZSByZXBvcnQnKTsKcmVzZXQoKTsg'
        'Vy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsKVy5ydW4oYHRhcCgke0dFQVJbMF19LCAke0dFQVJb'
        'MV19KWApOwpjb25zdCBhZnRlck9uZSA9IHN0YXRlKCk7ClcucnVuKGB0YXAoJHtHRUFSWzBdfSwg'
        'JHtHRUFSWzFdfSlgKTsKY29uc29sZS5sb2coJyAgICBhZnRlciBvbmUgdGFwIG9uIHRoZSBnZWFy'
        'OiAgJyArIGFmdGVyT25lKTsKY29uc29sZS5sb2coJyAgICBhZnRlciB0aGUgc2Vjb25kIHRhcDog'
        'ICAgICAgJyArIHN0YXRlKCkpOwpvaygnYSBzdHlsdXMgdGFwIGNvdW50ZWQgdHdpY2UgZG9lcyBu'
        'b3QgbGVhdmUgYSBwYW5lbCBvdmVyIGEgcnVubmluZyBnYW1lJywgIWJyb2tlbigpKTsKCmNvbnNv'
        'bGUubG9nKCdcbkV2ZXJ5IG9yZGVyIG9mIHR3byBwYW5lbHMnKTsKY29uc3QgYWN0cyA9IHsKICAn'
        'b3BlbiBzd2l0Y2ggbWVudSc6ICd0b2dnbGVTaGlwTWVudSgpJywKICAnb3BlbiBjYWxsIG1lbnUn'
        'OiAgICd0b2dnbGVDYWxsTWVudSgpJywKICAnb3BlbiBzZXR0aW5ncyc6ICAgICdzZXRTZXR0aW5n'
        'cyh0cnVlKScsCiAgJ2Nsb3NlIHNldHRpbmdzJzogICAnc2V0U2V0dGluZ3MoZmFsc2UpJywKICAn'
        'dGFwIHRoZSBnZWFyJzogICAgIGB0YXAoJHtHRUFSWzBdfSwgJHtHRUFSWzFdfSlgLAogICd0YXAg'
        'cGF1c2UnOiAgICAgICAgYHRhcCgke1BBVVNFWzBdfSwgJHtQQVVTRVsxXX0pYCwKICAndGFwIHRo'
        'ZSBzaGlwIGJ1dHRvbic6IGB0YXAoJHtTSElQQlswXX0sICR7U0hJUEJbMV19KWAsCiAgJ3RhcCB0'
        'aGUgZmllbGQnOiAgICBgdGFwKCR7RklFTERbMF19LCAke0ZJRUxEWzFdfSlgCn07CmNvbnN0IGtl'
        'eXMgPSBPYmplY3Qua2V5cyhhY3RzKTsKbGV0IGJhZCA9IFtdOwpmb3IoY29uc3QgYSBvZiBrZXlz'
        'KSBmb3IoY29uc3QgYiBvZiBrZXlzKSBmb3IoY29uc3QgYyBvZiBrZXlzKXsKICByZXNldCgpOwog'
        'IFcucnVuKGFjdHNbYV0pOyBXLnJ1bihhY3RzW2JdKTsgVy5ydW4oYWN0c1tjXSk7CiAgaWYoYnJv'
        'a2VuKCkpIGJhZC5wdXNoKGEgKyAnIC0+ICcgKyBiICsgJyAtPiAnICsgYyArICcgID0gICcgKyBz'
        'dGF0ZSgpKTsKfQppZihiYWQubGVuZ3RoKXsKICBjb25zb2xlLmxvZygnICAgICcgKyBiYWQubGVu'
        'Z3RoICsgJyBvZiAnICsga2V5cy5sZW5ndGgqKjMgKyAnIHNlcXVlbmNlcyBsZWF2ZSBhIHBhbmVs'
        'IG92ZXIgYSBydW5uaW5nIGdhbWUsIGUuZy4nKTsKICBmb3IoY29uc3QgYiBvZiBiYWQuc2xpY2Uo'
        'MCw2KSkgY29uc29sZS5sb2coJyAgICAgICcgKyBiKTsKfQpvaygnbm8gc2VxdWVuY2Ugb2YgdGhy'
        'ZWUgYWN0aW9ucyBsZWF2ZXMgYSBwYW5lbCBvdmVyIGEgcnVubmluZyBnYW1lJywgYmFkLmxlbmd0'
        'aD09PTApOwoKY29uc29sZS5sb2coJ1xuQ2xvc2luZyBldmVyeXRoaW5nIGhhcyB0byBnaXZlIHRo'
        'ZSBnYW1lIGJhY2snKTsKcmVzZXQoKTsgVy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsgVy5ydW4o'
        'J3NldFNoaXBNZW51KGZhbHNlKScpOwovLyBDbG9zaW5nIGEgcGFuZWwgbm8gbG9uZ2VyIGhhbmRz'
        'IHRoZSBnYW1lIHN0cmFpZ2h0IGJhY2s6IGl0IGlzIGhlbGQgdW50aWwKLy8gb25lIGZ1cnRoZXIg'
        'dGFwLCB0aGUgc2FtZSBmb3IgZXZlcnkgcGFuZWwgYW5kIGV2ZXJ5IHdheSBvZiBsZWF2aW5nIG9u'
        'ZS4Kb2soJ2Nsb3NpbmcgdGhlIHN3aXRjaCBtZW51IGhvbGRzIHJhdGhlciB0aGFuIHJlc3VtZXMn'
        'LAogICBXLmdldCgncGF1c2VkJyk9PT10cnVlICYmIFcuZ2V0KCdyZXN1bWVIb2xkJyk9PT10cnVl'
        'KTsKVy5ydW4oJ2NsZWFyUmVzdW1lSG9sZCgpJyk7Cm9rKCdhbmQgdGhlIHRhcCBnaXZlcyB0aGUg'
        'Z2FtZSBiYWNrJywgVy5nZXQoJ3BhdXNlZCcpPT09ZmFsc2UpOwpyZXNldCgpOyBXLnJ1bignY2xl'
        'YXJSZXN1bWVIb2xkKCknKTsgVy5ydW4oYHRhcCgke1BBVVNFWzBdfSwgJHtQQVVTRVsxXX0pYCk7'
        'Cm9rKCd0aGUgcGF1c2UgYnV0dG9uIHN0aWxsIHBhdXNlcyBvbiBpdHMgb3duJywgVy5nZXQoJ3Bh'
        'dXNlZCcpPT09dHJ1ZSk7ClcucnVuKCdzZXRTZXR0aW5ncyh0cnVlKScpOyBXLnJ1bignc2V0U2V0'
        'dGluZ3MoZmFsc2UpJyk7Cm9rKCdzZXR0aW5ncyBvcGVuZWQgYW5kIGNsb3NlZCBvbiB0b3Agb2Yg'
        'YSBtYW51YWwgcGF1c2Uga2VlcHMgdGhlIHBhdXNlJywgVy5nZXQoJ3BhdXNlZCcpPT09dHJ1ZSk7'
        'CnJlc2V0KCk7IFcucnVuKCdzZXRTZXR0aW5ncyh0cnVlKScpOyBXLnJ1bignc2V0U2V0dGluZ3Mo'
        'ZmFsc2UpJyk7Cm9rKCdzZXR0aW5ncyBvcGVuZWQgYW5kIGNsb3NlZCB3aXRob3V0IGEgbWFudWFs'
        'IHBhdXNlIHJlc3VtZXMnLCBXLmdldCgncGF1c2VkJyk9PT1mYWxzZSk7Cgpjb25zb2xlLmxvZygn'
        'XG4nICsgKGZhaWxzID8gZmFpbHMgKyAnIEZBSUxFRCcgOiAnYWxsIHBhc3NlZCcpKTsKcHJvY2Vz'
        'cy5leGl0KGZhaWxzID8gMSA6IDApOwo='
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
        'cmUgbGVmdCBvdXQuCmZvcihsZXQgbT0xO208PTQ4O20rKykgaWYobSE9PTEyICYmIG0hPT0yMykg'
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
        'CnNjZW5hcmlvKCdNNDMgRGVyIE5URi1Lb252b2knLCAnbT00MycsIGAKICBjb25zdCByID0ge307'
        'CiAgRlMuc3RlcCg2MDApOwogIGNvbnN0IHQgPSBlbmVtaWVzLmZpbHRlcihlPT5lLnVpZD09PSdU'
        'MScpOwogIHIudGhyZWVUcml0b25zID0gdC5sZW5ndGg9PT0zICYmIHQuZXZlcnkoZT0+ZS5pbWc9'
        'PT0nZnJ0cml0b24nICYmIGUuZXNjYXBpbmc+MCk7CiAgci5zYXlzU2NhbkZpcnN0ID0gbWlzc2lv'
        'bk9iaj09PSdTQ0FOIFRIRSBUUklUT05TJzsKICBkYW1hZ2VFbmVteSh0WzBdLCB0WzBdLm1heEhw'
        'KjUsIHRbMF0ueCwgdFswXS55LCB0cnVlLCAnYm9sdCcpOyBGUy5zdGVwKDIpOwogIHIuY2Fubm90'
        'RGllVW5zY2FubmVkID0gZW5lbWllcy5pbmNsdWRlcyh0WzBdKTsKICBmb3IoY29uc3QgZSBvZiB0'
        'KSBGUy5ob2xkKGUueCwgZS55LCBTQ0FOX1RJTUUgKyAyMCk7CiAgci5hbGxTY2FubmVkID0gdC5l'
        'dmVyeShlPT5lLnNjYW5uZWQpOwogIEZTLnN0ZXAoMik7CiAgci50aGVuRGVzdHJveSA9IG1pc3Np'
        'b25PYmo9PT0nREVTVFJPWSBUSEUgQ09OVk9ZJzsKICBmb3IoY29uc3QgZSBvZiB0KSBlLmhwID0g'
        'MDsKICBjb25zdCBkb25lID0gRlMudW50aWwoKCk9PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09'
        'PSdDT05WT1kgREVTVFJPWUVEJywgMTUwMCwgZmFsc2UpOwogIHIuY29tcGxldGVDYXJkID0gZG9u'
        'ZT49MDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNDMgYSBUcml0b24gZ2V0cyBhd2F5OiBm'
        'YWlsZWQnLCAnbT00MycsIGAKICBGUy5zdGVwKDMwMCk7CiAgY29uc3QgdCA9IGVuZW1pZXMuZmls'
        'dGVyKGU9PmUudWlkPT09J1QxJyk7CiAgZm9yKGNvbnN0IGUgb2YgdCl7IGUuc2Nhbm5lZCA9IHRy'
        'dWU7IGUuZXNjYXBpbmcgPSAzOyB9CiAgY29uc3QgZiA9IEZTLnVudGlsKCgpPT4hIW9iakNhcmQg'
        'JiYgb2JqQ2FyZC50b25lPT09J2ZhaWwnLCAzMDAwLCBmYWxzZSk7CiAgcmV0dXJuIHtmYWlsQ2Fy'
        'ZDogZj49MCAmJiBvYmpDYXJkLnR4dD09PSdBIFRSSVRPTiBHT1QgQVdBWSd9O2ApOwoKc2NlbmFy'
        'aW8oJ000NCBEZXIgU2Nod2FybScsICdtPTQ0JywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVw'
        'KDQwMCk7CiAgci5hbGx5V2luZ3MgPSBhbGxpZXMuZmlsdGVyKGE9PmEuc21hbGwpLmxlbmd0aCA+'
        'PSAyOwogIHIuZGVpbW9zVG9SZWFybSA9IGFsbGllcy5zb21lKGE9PmEudWlkPT09J0ExJyAmJiBh'
        'LmltZz09PSdjb2RlaW1vcycpOwogIGNvbnN0IHNlZW4gPSB7fTsKICBGUy51bnRpbCgoKT0+eyBm'
        'b3IoY29uc3QgZSBvZiBlbmVtaWVzKSBpZihlLnVpZCkgc2VlbltlLnVpZF09MTsgZm9yKGNvbnN0'
        'IGEgb2YgYWxsaWVzKSBpZihhLnVpZCkgc2VlblthLnVpZF09MTsgcmV0dXJuIHdhdmVPdmVyOyB9'
        'LCAzMDAwMCwgdHJ1ZSk7CiAgci5hbGxUaGVXaW5ncyA9IFsnRTEnLCdFMicsJ0UzJywnQjEnLCdX'
        'MiddLmV2ZXJ5KGs9PnNlZW5ba10pOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000NSBEYXMg'
        'TmFkZWxvZWhyJywgJ209NDUnLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAoNTAwKTsKICBj'
        'b25zdCBrID0gZW5lbWllcy5maWx0ZXIoZT0+L15LWzEyM10kLy50ZXN0KGUudWlkfHwnJykpOwog'
        'IHIudGhyZWVGZW5yaXMgPSBrLmxlbmd0aD09PTMgJiYgay5ldmVyeShlPT5lLmltZz09PSdudGZj'
        'cmZlbnJpcycpOwogIGNvbnN0IHlzID0gay5tYXAoZT0+ZS55KS5zb3J0KChhLGIpPT5hLWIpOwog'
        'IHIuaW5TZXBhcmF0ZUxhbmVzID0geXMubGVuZ3RoPT09MyAmJiB5c1sxXS15c1swXSA+IDQwICYm'
        'IHlzWzJdLXlzWzFdID4gNDA7CiAgY29uc3QgbyA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J0Ex'
        'Jyk7CiAgci5vcmlvbkNyb3NzZXMgPSAhIW8gJiYgby50cmFuc2l0PT09dHJ1ZTsKICBvLmhwID0g'
        'by5tYXhIcCA9IDFlNzsgZm9yKGNvbnN0IHMgb2Ygby5zdWJzfHxbXSkgcy5ocCA9IHMubWF4SHAg'
        'PSAxZTc7CiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT57IGlmKGFsbGllcy5pbmNsdWRlcyhvKSkg'
        'by5ocCA9IG8ubWF4SHA7IHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nVEhFIE9S'
        'SU9OIElTIFRIUk9VR0gnOyB9LCA5MDAwLCB0cnVlKTsKICByLnRocm91Z2hDYXJkID0gdD49MDsK'
        'ICBGUy51bnRpbCgoKT0+d2F2ZU92ZXIgfHwgd2F2ZT40NSwgMzAwMCwgdHJ1ZSk7CiAgci53YXZl'
        'RW5kcyA9IHdhdmVPdmVyIHx8IHdhdmU+NDU7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTQ2'
        'IERpZSBXaXNzZW5zY2hhZnRsZXInLCAnbT00NicsIGAKICBjb25zdCByID0ge307CiAgc2NvcmUg'
        'PSAxMDAwOwogIEZTLnN0ZXAoNDAwKTsKICBjb25zdCBmID0gZW5lbWllcy5maW5kKGU9PmUudWlk'
        'PT09J0YxJyk7CiAgci5mYXVzdHVzUGFya2VkID0gISFmICYmIE1hdGguYWJzKGYueS0yNTApIDwg'
        'MTsKICByLm9uQURlYWRsaW5lID0gISFmICYmIGYuZmxlZVQ+MDsKICBkYW1hZ2VFbmVteShmLCBm'
        'Lm1heEhwKjUsIGYueCwgZi55LCB0cnVlLCAnYm9sdCcpOyBGUy5zdGVwKDIpOwogIHIuY2Fubm90'
        'QmVEZXN0cm95ZWQgPSBlbmVtaWVzLmluY2x1ZGVzKGYpOwogIGNvbnN0IGtpbGwgPSBpZD0+eyBm'
        'b3IoY29uc3QgcyBvZiBmLnN1YnMpIGlmKHMuaWQ9PT1pZCl7IHMuZGVhZD10cnVlOyBzLmhwPTA7'
        'IH0gfTsKICBraWxsKCduYXZpZ2F0aW9uJyk7IEZTLnN0ZXAoMik7CiAgY29uc3QgZnQgPSBmLmZs'
        'ZWVUOyBGUy5zdGVwKDIwMCk7CiAgci5ub05hdmlnYXRpb25Ob0p1bXAgPSBmLmZsZWVUPT09ZnQ7'
        'CiAgci5ub0FyZ29ZZXQgPSAhYWxsaWVzLnNvbWUoYT0+YS51aWQ9PT0nVDEnKSAmJiAhc3Bhd25R'
        'LnNvbWUocT0+cS51aWQ9PT0nVDEnKTsKICBraWxsKCd3ZWFwb25zJyk7IEZTLnN0ZXAoMik7CiAg'
        'ci5jb3ZlclRoZUFyZ28gPSBtaXNzaW9uT2JqPT09J0NPVkVSIFRIRSBBUkdPJzsKICBjb25zdCBn'
        'b3QgPSBGUy51bnRpbCgoKT0+ISFFVl9ET0NLWydUMSddLCA5MDAwLCB0cnVlKTsKICBGUy5zdGVw'
        'KDUpOwogIHIuZG9ja3NBbmRUYWtlcyA9IGdvdD49MCAmJiBmLmNhcHR1cmVkPT09dHJ1ZTsKICBy'
        'LmNvbXBsZXRlQ2FyZCA9ICEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdGQVVTVFVTIENBUFRV'
        'UkVEJzsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNDYgbGVmdCBhbG9uZSBzaGUganVtcHM6'
        'IGZhaWxlZCcsICdtPTQ2JywgYAogIEZTLnN0ZXAoMzAwKTsKICBjb25zdCBmID0gZW5lbWllcy5m'
        'aW5kKGU9PmUudWlkPT09J0YxJyk7CiAgZm9yKGNvbnN0IHMgb2YgZi5zdWJzKSBzLmhwID0gcy5t'
        'YXhIcCA9IDFlNzsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9PiEhb2JqQ2FyZCAmJiBvYmpDYXJk'
        'LnRvbmU9PT0nZmFpbCcsIDkwMDAsIHRydWUpOwogIHJldHVybiB7ZmFpbENhcmQ6IHQ+PTAgJiYg'
        'b2JqQ2FyZC50eHQ9PT0nVEhFIEZBVVNUVVMgR09UIEFXQVknfTtgKTsKCnNjZW5hcmlvKCdNNDcg'
        'RGllIHp3ZWl0ZSBGbHVjaHQnLCAnbT00NycsIGAKICBjb25zdCByID0ge307CiAgc2NvcmUgPSA1'
        'MDAwOwogIEZTLnN0ZXAoNDAwKTsKICByLmljZW5pID0gZW5lbWllcy5zb21lKGU9PmUudWlkPT09'
        'J1YxJyAmJiBlLmljZW5pKTsKICByLmhlY2F0ZSA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdW'
        'MicgJiYgZS5pbWc9PT0nbnRmZGVoZWNhdGUnKTsKICByLm5vQWxsaWVzID0gIWFsbGllcy5zb21l'
        'KGE9PiFhLnNtYWxsKTsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9PiFlbmVtaWVzLnNvbWUoZT0+'
        'ZS51aWQ9PT0nVjEnKSwgOTAwMCwgdHJ1ZSk7CiAgci5pY2VuaUdldHNBd2F5ID0gdD49MCAmJiBp'
        'Y2VuRXNjYXBlcz09PTEgJiYgc2NvcmU+PTUwMDA7CiAgY29uc3QgdiA9IGVuZW1pZXMuZmluZChl'
        'PT5lLnVpZD09PSdWMicpOyBpZih2KSB2LmhwID0gMDsKICByLmNvbXBsZXRlQ2FyZCA9IEZTLnVu'
        'dGlsKCgpPT4hIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nSEVDQVRFIERFU1RST1lFRCcsIDMw'
        'MDAsIGZhbHNlKSA+PSAwOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000OCBEaWUgQXVma2xh'
        'ZXJ1bmcnLCAnbT00OCcsIGAKICBjb25zdCByID0ge307CiAgc2NvcmUgPSAyMDAwOwogIHIuYW5u'
        'b3VuY2VkID0gTk9USUNFUy5zb21lKG49Pm4udHh0PT09J0dURiBQRUdBU1VTIEFTU0lHTkVEJyk7'
        'CiAgRlMuc3RlcCg0MDApOwogIHIuZmx5aW5nQVBlZ2FzdXMgPSBwbGF5ZXIuc2hpcD09PSdmaXBl'
        'Z2FzdXMnOwogIHIubm90aGluZ0xvY2tzSGVyID0gIWNhbkxvY2tPbihwbGF5ZXIpOwogIGNvbnN0'
        'IHYgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nVjEnKTsKICByLmd1bnNIb2xkRmlyZSA9IGNh'
        'cEd1blRhcmdldCh2KT09PW51bGw7CiAgci5ub0JlYW1PbkhlciA9ICFiZWFtVGFyZ2V0cyh2LCBm'
        'YWxzZSkuaW5jbHVkZXMocGxheWVyKTsKICByLm5vSGFuZ2FyID0gc2hpcFN3YXBSZWFkeSgpPT09'
        'ZmFsc2U7CiAgci5yaW5nc1Nob3duID0gISF2ICYmIHYuc2NhblN1YnM9PT10cnVlICYmIHYuc3Vi'
        'cy5ldmVyeShzPT4hcy5zY2FubmVkKTsKICBmb3IoY29uc3QgcyBvZiB2LnN1YnMpeyBjb25zdCBw'
        'ID0gc3ViUG9zKHYsIHMpOyBGUy5ob2xkKHAueCwgcC55LCBTVUJfU0NBTl9USU1FICsgMjApOyB9'
        'CiAgci5hbGxGaXZlU2Nhbm5lZCA9IHYuc3Vicy5ldmVyeShzPT5zLnNjYW5uZWQpICYmIHYuc2Nh'
        'bm5lZD09PXRydWU7CiAgRlMuc3RlcCgzKTsKICByLmNvbXBsZXRlQ2FyZCA9ICEhb2JqQ2FyZCAm'
        'JiBvYmpDYXJkLnR4dD09PSdPUklPTiBTQ0FOTkVEJzsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9'
        'PiFlbmVtaWVzLmluY2x1ZGVzKHYpLCAxNTAwLCBmYWxzZSk7CiAgci5vcmlvbkxlYXZlc1dpdGhv'
        'dXRQZW5hbHR5ID0gdD49MCAmJiBzY29yZSA+PSAyMDAwOwogIEZTLnVudGlsKCgpPT53YXZlPjQ4'
        'LCAzMDAwMCwgdHJ1ZSk7CiAgci5vd25IdWxsQmFja05leHRXYXZlID0gd2F2ZT09PTQ5ICYmIHBs'
        'YXllci5zaGlwPT09J2ZpbXlybWlkb24nOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ0NvbG9z'
        'c3VzIGJlYW1zIGFyZSBUZXJyYW4nLCAnJywgYAogIHJldHVybiB7bWFpbjogYmVhbUNvbCgnZ3R2'
        'YScsIHRydWUpPT09JyMwMGZmNTUnLCBhbnRpRmlnaHRlcjogYmVhbUNvbCgnZ3R2YScsIGZhbHNl'
        'KT09PScjNDQ5OWZmJ307YCwgdHJ1ZSk7CgpzY2VuYXJpbygnSG9MIHN0YXJ0IHVuY2hhbmdlZCcs'
        'ICdtPTEnLCBgCiAgcmV0dXJuIHt3YXZlOiB3YXZlLCB0aG90aDogcGxheWVyLnNoaXA9PT0nZml0'
        'b3RoJywgdmFzdWRhbkNhbGw6IEFMTFlfRkFDX09OLnZhc3VkYW49PT10cnVlICYmIEFMTFlfRkFD'
        'X09OLnRlcnJhbj09PWZhbHNlfTtgKTsKCi8vIOKUgOKUgCBSdW5uZXIg4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSACihh'
        'c3luYygpPT57CiAgY29uc3QgYnJvd3NlciA9IGF3YWl0IGNocm9taXVtLmxhdW5jaCgpOwogIGxl'
        'dCBmYWlscyA9IDA7CiAgY29uc3Qgb25seSA9IHByb2Nlc3MuYXJndls0XTsKICBmb3IoY29uc3Qg'
        'c2Mgb2Ygc2NlbmFyaW9zKXsKICAgIGlmKG9ubHkgJiYgc2MubmFtZS5pbmRleE9mKG9ubHkpPDAp'
        'IGNvbnRpbnVlOwogICAgY29uc3QgcGFnZSA9IGF3YWl0IGJyb3dzZXIubmV3UGFnZSgpOwogICAg'
        'Y29uc3QgZXJycyA9IFtdOwogICAgcGFnZS5vbigncGFnZWVycm9yJywgZT0+ZXJycy5wdXNoKFN0'
        'cmluZyhlLm1lc3NhZ2V8fGUpKSk7CiAgICBhd2FpdCBwYWdlLmdvdG8oJ2ZpbGU6Ly8nICsgdG1w'
        'ICsgJz8nICsgc2MucXVlcnkpOwogICAgYXdhaXQgcGFnZS53YWl0Rm9yVGltZW91dCgzMDApOwog'
        'ICAgbGV0IHJlczsKICAgIHRyeXsKICAgICAgcmVzID0gYXdhaXQgcGFnZS5ldmFsdWF0ZShIRUxQ'
        'RVJTICsgYFxuRlMuZmFrZUltYWdlcygpO2AgKyAoc2Mubm9MYXVuY2ggPyAnJyA6ICcgbGF1bmNo'
        'R2FtZSgpOycpICsgYFxuKGZ1bmN0aW9uKCl7JHtzYy5ib2R5fX0pKClgKTsKICAgIH1jYXRjaChl'
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
print("v136 applied: NTF missions 43-48, checks updated. Now run: python3 assemble.py 136")
