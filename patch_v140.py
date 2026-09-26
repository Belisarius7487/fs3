#!/usr/bin/env python3
"""FS3 v140 - fixes to missions 50 to 54, beams under the hulls.

    Crossings   an allied capital ship on a written crossing (M50's Orion,
                also M45 and the others) warps in on screen and then sets
                off, instead of popping up half outside the left edge.
    M51         an installation has no engines and no navigation.
    M52         two Mjolnirs that take turns, and a real battle: six NTF
                capital ships in two lanes, one after another per lane,
                never more than two at once, all holding their height, on
                shorter deadlines. The Mjolnirs do not vanish at the end of
                the wave; they are there until the screen is black.
    M53         no support call while both of our ships are in the field;
                once one of them is lost the call is free.
    Waves       a wave could end in the same step its last ship died, before
                the event that brings the next one in had fired (M52 did).
    M54         'EVACUATION COMPLETE' only once every Elysium is out or
                lost, and a notice for each one that makes it.
    Beams       the ray is drawn under every hull, so it seems to run
                through the ship it hits. Charge glow and muzzle orb stay on
                top of the firing ship.

Needs v139. Edits src/30_waves.js, src/40_world.js, src/50_combat.js,
src/60_effects.js and src/70_ui.js in place, and writes the updated
fieldsim.js and swtest.js. Run assemble.py afterwards.
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

# ══ Crossings warp in ═══════════════════════════════════════════════════
fx = replace_once(
    fx,
    "          _a.x = _toLeft ? W + 20 : -20;  _a.warpX = _a.x;  _a.warp = 0;\n",
    "          // She warps in on screen, like every other capital ship, and\n"
    "          // sets off once through. Starting half outside the edge with\n"
    "          // no vortex read as popping into existence.\n"
    "          _a.x = _toLeft ? W - _gh - TRANS_EDGE_PAD : _gh + TRANS_EDGE_PAD;\n"
    "          _a.warpX = _a.x;\n",
    "crossing warps in")

# ══ Installations: no engines, no navigation ═══════════════════════════
cb = replace_once(
    cb,
    "            hp:hp, maxHp:hp, dead:false};\n  });\n}\n",
    "            hp:hp, maxHp:hp, dead:false};\n  });\n"
    "  // An installation neither moves nor jumps.\n"
    "  if(e.type==='station')\n"
    "    e.subs = e.subs.filter(function(s){ return s.id!=='engines' && s.id!=='navigation'; });\n"
    "}\n",
    "station subs")

# ══ Platforms stay until the screen is black; staggered beams ══════════
wo = replace_once(
    wo,
    "    if(waveOver && !a.warpOut){ a.warpOut = a.warpMax; a.warpX = a.x; a.warpY = a.y; }\n",
    "    // A gun platform has no jump drive. It stays until the field goes\n"
    "    // dark and the next wave clears it away.\n"
    "    if(waveOver && !a.warpOut && !a.platform){ a.warpOut = a.warpMax; a.warpX = a.x; a.warpY = a.y; }\n",
    "platform stays")
fx = replace_once(
    fx,
    "      waveCd=Math.max(TRANS_CLEAR+TRANS_OUT, allies.length?(allies[0].warpMax+TRANS_OUT):0);\n",
    "      // The longest jump among the escorts, not just the first one's.\n"
    "      let _wmax = 0;\n"
    "      for(const _al of allies) if(!_al.platform) _wmax = Math.max(_wmax, _al.warpMax||0);\n"
    "      waveCd=Math.max(TRANS_CLEAR+TRANS_OUT, _wmax ? _wmax+TRANS_OUT : 0);\n",
    "waveCd longest")
wv = replace_once(
    wv,
    "             x:u.x, y:u.y, callsOk:u.callsOk}\n",
    "             x:u.x, y:u.y, callsOk:u.callsOk, beamDelay:u.beamDelay}\n",
    "ally put beamDelay")
fx = replace_once(
    fx,
    "        if(_a && _sp.callsOk) _a.callsOk = true;\n",
    "        if(_a && _sp.callsOk) _a.callsOk = true;\n"
    "        // beamDelay: seconds before her beams first look for a target,\n"
    "        // so two platforms do not open up together.\n"
    "        if(_a && _a.beams && _sp.beamDelay!=null)\n"
    "          for(const _b of _a.beams){ _b.state='idle'; _b.timer = 30 + _sp.beamDelay*TICK_HZ; }\n",
    "ally spawn beamDelay")
cb = replace_once(
    cb,
    "    if(b.state==='idle') {\n"
    "      if(b.timer<=0) {\n"
    "        // Find a target first. With no target it will not charge, the\n"
    "        // turret holds fire and retries shortly after.\n",
    "    if(b.state==='idle') {\n"
    "      // Gun platforms take turns: while another one is in the first\n"
    "      // half of its charge, this one waits.\n"
    "      if(b.timer<=0 && e.platform && platformCharging(e)) { b.timer = 60; continue; }\n"
    "      if(b.timer<=0) {\n"
    "        // Find a target first. With no target it will not charge, the\n"
    "        // turret holds fire and retries shortly after.\n",
    "platform turns")
cb = replace_once(
    cb,
    "function drawBeams(e) {\n",
    "// Is another gun platform on this side early in its charge?\n"
    "function platformCharging(self){\n"
    "  for(const o of allies){\n"
    "    if(o===self || !o.platform || o.dead || !o.beams) continue;\n"
    "    for(const b of o.beams){\n"
    "      if(b.state!=='charging') continue;\n"
    "      const cm = b.chargeMax || b.chargeT;\n"
    "      if(cm - b.timer < cm*0.5) return true;\n"
    "    }\n"
    "  }\n"
    "  return false;\n"
    "}\n"
    "\n"
    "// The ray itself. Drawn before any hull, so every ship lies on top of\n"
    "// it and a hit looks like the beam running through the target rather\n"
    "// than being painted across it.\n"
    "function drawBeamRays(e) {\n"
    "  if(!e.beams) return;\n"
    "  for(const b of e.beams) {\n"
    "    if(b.state!=='firing') continue;\n"
    "    const col=beamCol(e.faction, b.large);\n"
    "    const ang = b.type==='slash' ? b.curAngle : b.angle;\n"
    "    const mpF=mountPos(e,b);\n"
    "    const len=2000;\n"
    "    const ex=mpF.x+Math.cos(ang)*len, ey=mpF.y+Math.sin(ang)*len;\n"
    "    const flicker=0.85+0.15*Math.sin(fc*0.8);\n"
    "    ctx.save();\n"
    "    // Outer glow\n"
    "    ctx.globalAlpha=0.15*flicker;\n"
    "    ctx.strokeStyle=col; ctx.lineWidth=b.large?22:10;\n"
    "    ctx.shadowColor=col; ctx.shadowBlur=ecoBlur(30);\n"
    "    ctx.beginPath(); ctx.moveTo(mpF.x,mpF.y); ctx.lineTo(ex,ey); ctx.stroke();\n"
    "    // Mid glow\n"
    "    ctx.globalAlpha=0.35*flicker;\n"
    "    ctx.lineWidth=b.large?10:5;\n"
    "    ctx.beginPath(); ctx.moveTo(mpF.x,mpF.y); ctx.lineTo(ex,ey); ctx.stroke();\n"
    "    // Core\n"
    "    ctx.globalAlpha=0.95*flicker;\n"
    "    ctx.strokeStyle='#ffffff';\n"
    "    ctx.lineWidth=b.large?2.5:1.5;\n"
    "    ctx.shadowBlur=ecoBlur(6);\n"
    "    ctx.beginPath(); ctx.moveTo(mpF.x,mpF.y); ctx.lineTo(ex,ey); ctx.stroke();\n"
    "    ctx.restore();\n"
    "  }\n"
    "}\n"
    "\n"
    "// Charge glow and muzzle orb, on top of the firing ship. The ray is\n"
    "// drawn separately, under the hulls, by drawBeamRays().\n"
    "function drawBeams(e) {\n",
    "drawBeamRays")
cb = replace_once(
    cb,
    "      const ang = b.type==='slash' ? b.curAngle : b.angle;\n"
    "      const mpF=mountPos(e,b);\n"
    "      const len=2000;\n"
    "      const ex=mpF.x+Math.cos(ang)*len, ey=mpF.y+Math.sin(ang)*len;\n"
    "      const flicker=0.85+0.15*Math.sin(fc*0.8);\n"
    "      ctx.save();\n"
    "      // Outer glow\n"
    "      ctx.globalAlpha=0.15*flicker;\n"
    "      ctx.strokeStyle=col; ctx.lineWidth=b.large?22:10;\n"
    "      ctx.shadowColor=col; ctx.shadowBlur=ecoBlur(30);\n"
    "      ctx.beginPath(); ctx.moveTo(mpF.x,mpF.y); ctx.lineTo(ex,ey); ctx.stroke();\n"
    "      // Mid glow\n"
    "      ctx.globalAlpha=0.35*flicker;\n"
    "      ctx.lineWidth=b.large?10:5;\n"
    "      ctx.beginPath(); ctx.moveTo(mpF.x,mpF.y); ctx.lineTo(ex,ey); ctx.stroke();\n"
    "      // Core\n"
    "      ctx.globalAlpha=0.95*flicker;\n"
    "      ctx.strokeStyle='#ffffff';\n"
    "      ctx.lineWidth=b.large?2.5:1.5;\n"
    "      ctx.shadowBlur=ecoBlur(6);\n"
    "      ctx.beginPath(); ctx.moveTo(mpF.x,mpF.y); ctx.lineTo(ex,ey); ctx.stroke();\n",
    "      const ang = b.type==='slash' ? b.curAngle : b.angle;\n"
    "      const mpF=mountPos(e,b);\n"
    "      const flicker=0.85+0.15*Math.sin(fc*0.8);\n"
    "      ctx.save();\n",
    "drawBeams top only")
ui = replace_once(
    ui,
    "  // Wreckage sits behind the ships: it is scenery that bites, not a unit.\n",
    "  // Beam rays under every hull: a ship lies on top of the beam that\n"
    "  // hits it, which reads as the beam running through her.\n"
    "  for(const e of SHIPS_ON_FIELD){\n"
    "    try{ drawBeamRays(e); }catch(eb){ ctx.restore(); }\n"
    "  }\n"
    "  ctx.globalAlpha=1;\n"
    "\n"
    "  // Wreckage sits behind the ships: it is scenery that bites, not a unit.\n",
    "rays pass")

# ══ Effect 'ruf'; 'gerettet' waits for the last one ═════════════════════
wv = replace_once(
    wv,
    "    case 'kulisse':\n",
    "    case 'ruf':\n"
    "      // From now on this ship no longer blocks the support call.\n"
    "      for(const u of byId(arg)) u.callsOk = true;\n"
    "      break;\n"
    "    case 'kulisse':\n",
    "ruf")
wv = replace_once(
    wv,
    "    case 'gerettet':     return protSaved >= (ev.a||1);\n",
    "    // Only once nobody is still under way: 'three are out' while a\n"
    "    // fourth is in the field reads as if she did not count.\n"
    "    case 'gerettet':     return protSaved >= (ev.a||1) && !crossPending()\n"
    "                                && !spawnQ.some(function(q){ return q.type==='protect'; });\n",
    "gerettet waits")

# ══ A trigger whose target is gone may still be about to fire ══════════
wv = replace_once(
    wv,
    "      if(evIds(e.a).every(function(id){ return evSeen(id) && byId(id).length===0; })) continue;\n",
    "      // Gone does not mean it cannot fire: 'alleZerstoert' fires exactly\n"
    "      // then. Only a trigger that is not true now can never be again.\n"
    "      // Checked before the event tick, the wave could end in the very\n"
    "      // step the last ship died, and the next one never came.\n"
    "      if(evIds(e.a).every(function(id){ return evSeen(id) && byId(id).length===0; })\n"
    "         && !evTrig(e)) continue;\n",
    "evPending fires")

# ══ Missions ════════════════════════════════════════════════════════════
wv = replace_once(
    wv,
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
    "     ]},\n",
    "       // Two Mjolnirs take turns; the Deimos keeps to the bottom edge.\n"
    "       {id:'M1', c:'cr', n:1, spr:'sgmjolnir', side:'ally', x:70, y:140, callsOk:true},\n"
    "       {id:'M2', c:'cr', n:1, spr:'sgmjolnir', side:'ally', x:70, y:360, callsOk:true,\n"
    "        beamDelay:8},\n"
    "       {id:'A1', c:'co', n:1, spr:'codeimos', side:'ally', still:true, x:200, y:440,\n"
    "        callsOk:true},\n"
    "       // Two lanes, one ship at a time in each: never more than two\n"
    "       // capital ships on the NTF side at once. All hold their height.\n"
    "       {id:'V1', c:'cr', n:1, spr:'ntfcraeolus',    t:3,  flee:30, y:170, still:true},\n"
    "       {id:'V3', c:'co', n:1, spr:'ntfcodeimos',          flee:38, y:170, still:true, wait:true},\n"
    "       {id:'V5', c:'de', n:1, spr:'ntfdehecate',          flee:48, y:170, still:true, wait:true},\n"
    "       {id:'V2', c:'cr', n:1, spr:'ntfcrfenris',    t:14, flee:30, y:350, still:true},\n"
    "       {id:'V4', c:'cr', n:1, spr:'ntfcrleviathan',       flee:30, y:350, still:true, wait:true},\n"
    "       {id:'V6', c:'de', n:1, spr:'ntfdeorion',           flee:48, y:350, still:true, wait:true},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'B1', c:'bo', n:1, wait:true},\n"
    "       {id:'E2', c:'fi', n:1, wait:true},\n"
    "       {id:'B2', c:'bo', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'V1', w:'einwarpen', a2:'V3'},\n"
    "       {t:'alleZerstoert', a:'V3', w:'einwarpen', a2:'V5'},\n"
    "       {t:'alleZerstoert', a:'V2', w:'einwarpen', a2:'V4'},\n"
    "       {t:'alleZerstoert', a:'V4', w:'einwarpen', a2:'V6'},\n"
    "       {t:'alleZerstoert', a:'V1', w:'einwarpen', a2:'B1'},\n"
    "       {t:'alleZerstoert', a:'V2', w:'einwarpen', a2:'E2'},\n"
    "       {t:'alleZerstoert', a:'V4', w:'einwarpen', a2:'B2'},\n"
    "       {t:'verlaesst', a:'V1', w:'meldung', a2:'the aeolus got away'},\n"
    "       {t:'verlaesst', a:'V2', w:'meldung', a2:'the fenris got away'},\n"
    "       {t:'verlaesst', a:'V3', w:'meldung', a2:'the deimos got away'},\n"
    "       {t:'verlaesst', a:'V4', w:'meldung', a2:'the leviathan got away'},\n"
    "       {t:'vernichtet', a:'V5+V6', w:'zielerfuellt', a2:'NTF BATTLE GROUP DESTROYED'},\n"
    "       {t:'verlaesst', a:'V5', w:'zielverfehlt', a2:'THE HECATE GOT AWAY'},\n"
    "       {t:'verlaesst', a:'V6', w:'zielverfehlt', a2:'THE ORION GOT AWAY'}\n"
    "     ]},\n",
    "m52")
wv = replace_once(
    wv,
    "       // Our Orion and a Deimos. An NTF Hecate and an NTF Orion jump in\n"
    "       // on top of them, bombers follow. Their loss is a blow, not the\n"
    "       // end of the mission: the NTF destroyers are the objective.\n"
    "       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', y:170, hp:1.3,\n"
    "        callsOk:true, noWings:true},\n"
    "       {id:'A2', c:'co', n:1, spr:'codeimos', side:'ally', y:390, callsOk:true},\n",
    "       // Our Orion and a Deimos. An NTF Hecate and an NTF Orion jump in\n"
    "       // on top of them, bombers follow. Their loss is a blow, not the\n"
    "       // end of the mission: the NTF destroyers are the objective.\n"
    "       // No support call while both are in the field - there is no room\n"
    "       // for a third ship; once one is lost the call is free.\n"
    "       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', y:170, hp:1.3,\n"
    "        noWings:true},\n"
    "       {id:'A2', c:'co', n:1, spr:'codeimos', side:'ally', y:390},\n",
    "m53 units")
wv = replace_once(
    wv,
    "       {t:'vernichtet', a:'A1', w:'meldung', a2:'gtd orion lost'},\n"
    "       {t:'vernichtet', a:'A2', w:'meldung', a2:'gtcv deimos lost'},\n",
    "       {t:'vernichtet', a:'A1', w:'meldung', a2:'gtd orion lost'},\n"
    "       {t:'vernichtet', a:'A2', w:'meldung', a2:'gtcv deimos lost'},\n"
    "       {t:'zerstoert', a:'A1', w:'ruf', a2:'A2'},\n"
    "       {t:'zerstoert', a:'A2', w:'ruf', a2:'A1'},\n",
    "m53 ruf")
wv = replace_once(
    wv,
    "       {t:'alleZerstoert', a:'T3', w:'jagd', a2:'T4'},\n",
    "       {t:'alleZerstoert', a:'T3', w:'jagd', a2:'T4'},\n"
    "       {t:'verlaesst', a:'T1', w:'meldung', a2:'first elysium is out'},\n"
    "       {t:'verlaesst', a:'T2', w:'meldung', a2:'second elysium is out'},\n"
    "       {t:'verlaesst', a:'T3', w:'meldung', a2:'third elysium is out'},\n"
    "       {t:'verlaesst', a:'T4', w:'meldung', a2:'fourth elysium is out'},\n",
    "m54 notices")

open("src/30_waves.js", "w", encoding="utf-8").write(wv)
open("src/40_world.js", "w", encoding="utf-8").write(wo)
open("src/50_combat.js", "w", encoding="utf-8").write(cb)
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
        'IGZhbHNlKSA+PSAwOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001NCBEaWUgRXZha3VpZXJ1'
        'bmcnLCAnbT01NCcsIGAKICBjb25zdCByID0ge307CiAgbGV0IHQxID0gbnVsbDsKICBGUy51bnRp'
        'bCgoKT0+eyB0MSA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J1QxJyk7IHJldHVybiAhIXQxOyB9'
        'LCAxMDAwLCBmYWxzZSk7CiAgci5sZWF2ZXNUaGVTdGF0aW9uID0gISF0MSAmJiBNYXRoLmFicyh0'
        'MS54LTU2MCkgPCAxNSAmJiB0MS5jcm9zc2luZyA8IDAgJiYgdDEuZmxpcD09PW5lZWRzRmxpcCh0'
        'MS5pbWcsIHRydWUpOwogIGNvbnN0IHgwID0gdDEueDsgRlMuc3RlcCgxMDApOwogIHIuZmxpZXNM'
        'ZWZ0ID0gdDEueCA8IHgwIC0gMzA7CiAgLy8gS2VlcCB0aGVtIGFsaXZlOyB0aGV5IGZseSBvdXQg'
        'dG8gdGhlIGxlZnQuCiAgY29uc3Qga2VlcCA9ICgpPT57IGZvcihjb25zdCBhIG9mIGFsbGllcykg'
        'aWYoL15ULy50ZXN0KGEudWlkfHwnJykpIGEuaHAgPSBhLm1heEhwID0gMWU3OyB9OwogIGNvbnN0'
        'IHQgPSBGUy51bnRpbCgoKT0+eyBrZWVwKCk7IHJldHVybiBwcm90U2F2ZWQ+PTE7IH0sIDMwMDAs'
        'IHRydWUpOwogIHIuZmlyc3RPdXQgPSB0Pj0wOwogIEZTLnN0ZXAoNSk7CiAgci5ub3RpY2VGb3JJ'
        'dCA9IE5PVElDRVMuc29tZShuPT5uLnR4dD09PSdGSVJTVCBFTFlTSVVNIElTIE9VVCcpOwogIC8v'
        'IFRocmVlIG91dCB3aGlsZSB0aGUgZm91cnRoIGlzIHN0aWxsIGZseWluZzogbm90IHlldCBjb21w'
        'bGV0ZS4KICBGUy51bnRpbCgoKT0+eyBrZWVwKCk7IHJldHVybiBwcm90U2F2ZWQ+PTM7IH0sIDkw'
        'MDAsIHRydWUpOwogIGNvbnN0IHQ0ID0gYWxsaWVzLmZpbmQoYT0+YS51aWQ9PT0nVDQnKTsKICBy'
        'Lm5vdENvbXBsZXRlV2hpbGVPbmVGbGllcyA9ICEhdDQgJiYgIShvYmpDYXJkICYmIG9iakNhcmQu'
        'dHh0PT09J0VWQUNVQVRJT04gQ09NUExFVEUnKTsKICBjb25zdCBjID0gRlMudW50aWwoKCk9Pnsg'
        'a2VlcCgpOyByZXR1cm4gISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J0VWQUNVQVRJT04gQ09N'
        'UExFVEUnOyB9LCA5MDAwLCB0cnVlKTsKICByLnRocmVlT3V0Q29tcGxldGUgPSBjPj0wICYmIHBy'
        'b3RTYXZlZD49MzsKICBjb25zdCB3ID0gRlMudW50aWwoKCk9Pnsga2VlcCgpOyByZXR1cm4gd2F2'
        'ZU92ZXI7IH0sIDkwMDAsIHRydWUsIHRydWUpOwogIHIud2F2ZUVuZHMgPSB3Pj0wOwogIHJldHVy'
        'biByO2ApOwoKc2NlbmFyaW8oJ001NCB0d28gbG9zdDogZmFpbGVkJywgJ209NTQnLCBgCiAgY29u'
        'c3QgciA9IHt9OwogIGxldCBuID0gMDsKICBjb25zdCBmID0gRlMudW50aWwoKCk9PnsgZm9yKGNv'
        'bnN0IGEgb2YgYWxsaWVzKSBpZigvXlRbMTJdJC8udGVzdChhLnVpZHx8JycpKSBhLmhwID0gMDsK'
        'ICAgIHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC50b25lPT09J2ZhaWwnOyB9LCAzMDAwLCB0'
        'cnVlKTsKICByLmZhaWxDYXJkID0gZj49MCAmJiBvYmpDYXJkLnR4dD09PSdUT08gTUFOWSBFTFlT'
        'SVVNUyBMT1NUJzsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdCZWFtcyBydW4gdW5kZXIgdGhl'
        'IGh1bGxzJywgJ209NDInLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAoMzAwKTsKICBjb25z'
        'dCBzaG9vdGVyID0gYWxsaWVzLmNvbmNhdChlbmVtaWVzKS5maW5kKG89Pm8uYmVhbXMgJiYgby5i'
        'ZWFtcy5sZW5ndGgpOwogIGNvbnN0IGIgPSBzaG9vdGVyLmJlYW1zWzBdOwogIGIuc3RhdGUgPSAn'
        'ZmlyaW5nJzsgYi50aW1lciA9IDFlNjsgYi5hbmdsZSA9IDA7IGIuY3VyQW5nbGUgPSAwOwogIGNv'
        'bnN0IG9yZGVyID0gW107CiAgY29uc3QgX3IgPSBkcmF3QmVhbVJheXMsIF9zID0gZHJhd1NoaXA7'
        'CiAgZHJhd0JlYW1SYXlzID0gZnVuY3Rpb24oZSl7IGlmKGUuYmVhbXMgJiYgZS5iZWFtcy5zb21l'
        'KHg9Pnguc3RhdGU9PT0nZmlyaW5nJykpIG9yZGVyLnB1c2goJ3JheScpOyByZXR1cm4gX3IuYXBw'
        'bHkodGhpcywgYXJndW1lbnRzKTsgfTsKICBkcmF3U2hpcCA9IGZ1bmN0aW9uKCl7IG9yZGVyLnB1'
        'c2goJ3NoaXAnKTsgcmV0dXJuIF9zLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07CiAgdHJ5IHsg'
        'ZHJhdygpOyB9IGZpbmFsbHkgeyBkcmF3QmVhbVJheXMgPSBfcjsgZHJhd1NoaXAgPSBfczsgfQog'
        'IGNvbnN0IGxhc3RSYXkgPSBvcmRlci5sYXN0SW5kZXhPZigncmF5JyksIGZpcnN0U2hpcCA9IG9y'
        'ZGVyLmluZGV4T2YoJ3NoaXAnKTsKICByLnJheURyYXduID0gbGFzdFJheT49MDsKICByLnVuZGVy'
        'RXZlcnlTaGlwID0gbGFzdFJheT49MCAmJiBmaXJzdFNoaXA+bGFzdFJheTsKICByZXR1cm4gcjtg'
        'KTsKCnNjZW5hcmlvKCdhbGxpZWQgY3JhZnQgaG9sZCBmaXJlIHdpdGggbm90aGluZyB0byBzaG9v'
        'dCcsICdtPTQ0JywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDMwMCk7CiAgY29uc3QgZmkg'
        'PSBta0FsbHlTbWFsbCgnZmlnaHRlcicsICd0ZXJyYW4nLCAnZmloZXJjJywgSCowLjUpOwogIGNv'
        'bnN0IGJvID0gbWtBbGx5U21hbGwoJ2JvbWJlcicsICd0ZXJyYW4nLCAnYm9hcnRlbWlzJywgSCow'
        'LjYpOwogIGZpLndhcnAgPSAwOyBiby53YXJwID0gMDsgYWxsaWVzLnB1c2goZmksIGJvKTsKICAv'
        'LyBPbmx5IHRoaW5ncyBhbiBlc2NvcnQgaGFzIG5vIGJ1c2luZXNzIHNob290aW5nIGF0OiBub3Ro'
        'aW5nLCBhbmQgYW4KICAvLyBpbnZ1bG5lcmFibGUgc3RhdGlvbiBhdCB0aGUgcmlnaHQgZWRnZS4K'
        'ICBjb25zdCBrZWVwID0gZW5lbWllczsgZW5lbWllcyA9IFtdOwogIGNvbnN0IHN0ID0gbWtFbmVt'
        'eSgnY3JfbnRmJywgJ250ZmNyYWVvbHVzJywgSCowLjUpOyBzdC54ID0gVy00MDsgc3Qud2FycCA9'
        'IDA7CiAgc3QuaW52dWxuID0gdHJ1ZTsgc3Quc2NlbmVyeSA9IHRydWU7CiAgY29uc3Qgc2hvdHMg'
        'PSAoKT0+cEJ1bGxldHMuZmlsdGVyKGI9PmIuYWxseSkubGVuZ3RoOwogIGxldCBuID0gMDsKICBm'
        'b3IoY29uc3QgbGlzdCBvZiBbW10sIFtzdF1dKXsKICAgIGVuZW1pZXMgPSBsaXN0OwogICAgZm9y'
        'KGNvbnN0IGEgb2YgW2ZpLCBib10pewogICAgICBhLmhlYWQgPSAwOyBhLnggPSBXKjAuNDsKICAg'
        'ICAgZm9yKGxldCBrPTA7azw0MDtrKyspewogICAgICAgIGNvbnN0IGIwID0gc2hvdHMoKTsKICAg'
        'ICAgICBhLmZUID0gMDsgc21hbGxGaXJlKGEsIHNtYWxsVGFyZ2V0KGEpKTsKICAgICAgICBpZihh'
        'LnNlY1QpIGZvcihsZXQgaT0wO2k8YS5zZWNULmxlbmd0aDtpKyspIGEuc2VjVFtpXSA9IDA7CiAg'
        'ICAgICAgZmlyZVNlY29uZGFyaWVzKGEsIFdQTlthLnR5cGVdKTsKICAgICAgICBuICs9IHNob3Rz'
        'KCktYjA7CiAgICAgIH0KICAgIH0KICB9CiAgZW5lbWllcyA9IGtlZXA7CiAgci5ub1Nob3RzQXRO'
        'b3RoaW5nID0gbj09PTA7CiAgci5fbiA9IG47CiAgLy8gV2l0aCBhIHJlYWwgZW5lbXkgaW4gcmVh'
        'Y2ggdGhleSBzdGlsbCBmaXJlLgogIGNvbnN0IGZvZSA9IGVuZW1pZXMuZmluZChlPT5lLnR5cGU9'
        'PT0nZmlnaHRlcicgJiYgIShlLndhcnA+MCkpIHx8IGVuZW1pZXMuZmluZChlPT4hKGUud2FycD4w'
        'KSAmJiAhZS5pbnZ1bG4pOwogIGxldCBtID0gMDsKICBpZihmb2UpeyBmaS54ID0gZm9lLngtODA7'
        'IGZpLnkgPSBmb2UueTsgZmkuaGVhZCA9IDA7CiAgICBmb3IobGV0IGs9MDtrPDU7aysrKXsgY29u'
        'c3QgYjAgPSBzaG90cygpOyBmaS5mVCA9IDA7IHNtYWxsRmlyZShmaSwgZm9lKTsgbSArPSBzaG90'
        'cygpLWIwOyB9IH0KICByLnN0aWxsRmlyZUF0RW5lbWllcyA9IG0+MDsKICByZXR1cm4gcjtgKTsK'
        'CnNjZW5hcmlvKCdNNDMgRGVyIE5URi1Lb252b2knLCAnbT00MycsIGAKICBjb25zdCByID0ge307'
        'CiAgRlMuc3RlcCg2MDApOwogIGNvbnN0IHQgPSBlbmVtaWVzLmZpbHRlcihlPT5lLnVpZD09PSdU'
        'MScpOwogIHIudGhyZWVUcml0b25zID0gdC5sZW5ndGg9PT0zICYmIHQuZXZlcnkoZT0+ZS5pbWc9'
        'PT0nZnJ0cml0b24nICYmIGUuZXNjYXBpbmc+MCk7CiAgci5zYXlzU2NhbkZpcnN0ID0gbWlzc2lv'
        'bk9iaj09PSdTQ0FOIFRIRSBUUklUT05TJzsKICBkYW1hZ2VFbmVteSh0WzBdLCB0WzBdLm1heEhw'
        'KjUsIHRbMF0ueCwgdFswXS55LCB0cnVlLCAnYm9sdCcpOyBGUy5zdGVwKDIpOwogIHIuY2Fubm90'
        'RGllVW5zY2FubmVkID0gZW5lbWllcy5pbmNsdWRlcyh0WzBdKTsKICByLm5vQWVvbHVzID0gIWVu'
        'ZW1pZXMuc29tZShlPT5lLnVpZD09PSdLMScpICYmICFzcGF3blEuc29tZShxPT5xLnVpZD09PSdL'
        'MScpOwogIC8vIFVuZGVyIGZpcmUgdGhlIHdob2xlIHRpbWU6IGluIHRoaXMgbWlzc2lvbiB0aGUg'
        'c2NhbiBzdGlsbCBmaWxscy4KICBmb3IoY29uc3QgZSBvZiB0KSBmb3IobGV0IGk9MDtpPFNDQU5f'
        'VElNRSsyMDtpKyspewogICAgcGxheWVyLnggPSBlLng7IHBsYXllci55ID0gZS55OyBNT1VTRS54'
        'ID0gZS54OyBNT1VTRS55ID0gZS55OwogICAgcGxheWVyLnNoRGVsYXkgPSA5MDsgcGxheWVyLmhw'
        'ID0gcGxheWVyLm1heEhwOyBGUy5zdGVwKDEpOyB9CiAgci5hbGxTY2FubmVkID0gdC5ldmVyeShl'
        'PT5lLnNjYW5uZWQpOwogIEZTLnN0ZXAoMik7CiAgci50aGVuRGVzdHJveSA9IG1pc3Npb25PYmo9'
        'PT0nREVTVFJPWSBUSEUgQ09OVk9ZJzsKICBGUy5zdGVwKDIwMCk7CiAgci5hZW9sdXNBZnRlclRo'
        'ZVNjYW4gPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nSzEnICYmIGUuaW1nPT09J250ZmNyYWVv'
        'bHVzJyk7CiAgZm9yKGNvbnN0IGUgb2YgdCkgZS5ocCA9IDA7CiAgY29uc3QgZG9uZSA9IEZTLnVu'
        'dGlsKCgpPT4hIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nQ09OVk9ZIERFU1RST1lFRCcsIDE1'
        'MDAsIGZhbHNlKTsKICByLmNvbXBsZXRlQ2FyZCA9IGRvbmU+PTA7CiAgcmV0dXJuIHI7YCk7Cgpz'
        'Y2VuYXJpbygnTTQzIGEgVHJpdG9uIGdldHMgYXdheTogZmFpbGVkJywgJ209NDMnLCBgCiAgRlMu'
        'c3RlcCgzMDApOwogIGNvbnN0IHQgPSBlbmVtaWVzLmZpbHRlcihlPT5lLnVpZD09PSdUMScpOwog'
        'IGZvcihjb25zdCBlIG9mIHQpeyBlLnNjYW5uZWQgPSB0cnVlOyBlLmVzY2FwaW5nID0gMzsgfQog'
        'IGNvbnN0IGYgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9iakNhcmQudG9uZT09PSdmYWls'
        'JywgMzAwMCwgZmFsc2UpOwogIHJldHVybiB7ZmFpbENhcmQ6IGY+PTAgJiYgb2JqQ2FyZC50eHQ9'
        'PT0nQSBUUklUT04gR09UIEFXQVknfTtgKTsKCnNjZW5hcmlvKCdNNDQgRGVyIFNjaHdhcm0nLCAn'
        'bT00NCcsIGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCg0MDApOwogIHIubm9BbGx5V2luZ0F0'
        'U3RhcnQgPSAhYWxsaWVzLnNvbWUoYT0+YS5zbWFsbCk7CiAgci5kZWltb3NUb1JlYXJtID0gYWxs'
        'aWVzLnNvbWUoYT0+YS51aWQ9PT0nQTEnICYmIGEuaW1nPT09J2NvZGVpbW9zJyk7CiAgY29uc3Qg'
        'c2VlbiA9IHt9OwogIGxldCBtYXhXaW5nID0gMCwgc3RyYXkgPSAwOwogIEZTLnVudGlsKCgpPT57'
        'IGZvcihjb25zdCBlIG9mIGVuZW1pZXMpIGlmKGUudWlkKSBzZWVuW2UudWlkXT0xOyBmb3IoY29u'
        'c3QgYSBvZiBhbGxpZXMpIGlmKGEudWlkKSBzZWVuW2EudWlkXT0xOwogICAgY29uc3Qgc20gPSBh'
        'bGxpZXMuZmlsdGVyKGE9PmEuc21hbGwgJiYgIWEuZGVhZCk7IG1heFdpbmcgPSBNYXRoLm1heCht'
        'YXhXaW5nLCBzbS5sZW5ndGgpOwogICAgaWYoc20uc29tZShhPT5hLnVpZCE9PSdXMicpKSBzdHJh'
        'eSsrOyByZXR1cm4gd2F2ZU92ZXI7IH0sIDMwMDAwLCB0cnVlKTsKICAvLyBPbmUgYWxsaWVkIHdp'
        'bmcsIHRoZSBvbmUgdGhlIG1pc3Npb24gc2VuZHM7IHRoZSBEZWltb3MgYWRkcyBub25lLgogIHIu'
        'b25lQWxseVdpbmdPbmx5ID0gbWF4V2luZz4wICYmIG1heFdpbmc8PTQgJiYgc3RyYXk9PT0wOwog'
        'IHIuYWxsVGhlV2luZ3MgPSBbJ0UxJywnRTInLCdFMycsJ0IxJywnVzInXS5ldmVyeShrPT5zZWVu'
        'W2tdKTsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNDUgRGFzIE5hZGVsb2VocicsICdtPTQ1'
        'JywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDUwMCk7CiAgY29uc3QgayA9IGVuZW1pZXMu'
        'ZmlsdGVyKGU9Pi9eS1sxMjNdJC8udGVzdChlLnVpZHx8JycpKTsKICByLnRocmVlRmVucmlzID0g'
        'ay5sZW5ndGg9PT0zICYmIGsuZXZlcnkoZT0+ZS5pbWc9PT0nbnRmY3JmZW5yaXMnKTsKICBjb25z'
        'dCB5cyA9IGsubWFwKGU9PmUueSkuc29ydCgoYSxiKT0+YS1iKTsKICByLmluU2VwYXJhdGVMYW5l'
        'cyA9IHlzLmxlbmd0aD09PTMgJiYgeXNbMV0teXNbMF0gPiA0MCAmJiB5c1syXS15c1sxXSA+IDQw'
        'OwogIGNvbnN0IG8gPSBhbGxpZXMuZmluZChhPT5hLnVpZD09PSdBMScpOwogIHIub3Jpb25Dcm9z'
        'c2VzID0gISFvICYmIG8udHJhbnNpdD09PXRydWU7CiAgby5ocCA9IG8ubWF4SHAgPSAxZTc7IGZv'
        'cihjb25zdCBzIG9mIG8uc3Vic3x8W10pIHMuaHAgPSBzLm1heEhwID0gMWU3OwogIGxldCByb2Nr'
        'cyA9IDA7CiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT57IGlmKGFsbGllcy5pbmNsdWRlcyhvKSkg'
        'by5ocCA9IG8ubWF4SHA7CiAgICBpZihlbmVtaWVzLnNvbWUoZT0+ZS50eXBlPT09J2FzdGVyb2lk'
        'JykpIHJvY2tzKys7CiAgICByZXR1cm4gISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J1RIRSBP'
        'UklPTiBJUyBUSFJPVUdIJzsgfSwgOTAwMCwgdHJ1ZSk7CiAgci50aHJvdWdoQ2FyZCA9IHQ+PTA7'
        'CiAgci5ub0FzdGVyb2lkcyA9IHJvY2tzPT09MDsKICBGUy51bnRpbCgoKT0+d2F2ZU92ZXIgfHwg'
        'd2F2ZT40NSwgMzAwMCwgdHJ1ZSk7CiAgci53YXZlRW5kcyA9IHdhdmVPdmVyIHx8IHdhdmU+NDU7'
        'CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTQ2IERpZSBXaXNzZW5zY2hhZnRsZXInLCAnbT00'
        'NicsIGAKICBjb25zdCByID0ge307CiAgc2NvcmUgPSAxMDAwOwogIEZTLnN0ZXAoNDAwKTsKICBj'
        'b25zdCBmID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J0YxJyk7CiAgci5mYXVzdHVzUGFya2Vk'
        'ID0gISFmICYmIE1hdGguYWJzKGYueS0yNTApIDwgMTsKICByLm9uQURlYWRsaW5lID0gISFmICYm'
        'IGYuZmxlZVQ+MDsKICAvLyBUaGUgY291bnRkb3duIHNpdHMgYXQgdGhlIHJpZ2h0IGVkZ2UsIGNs'
        'ZWFyIG9mIHRoZSBvYmplY3RpdmUgbGluZS4KICBjb25zdCBfZnQgPSBbXSwgX3BsID0gW107CiAg'
        'Y29uc3QgX2Z4ID0gY3R4LmZpbGxUZXh0LCBfdHAgPSB0aFBsYXRlOwogIGN0eC5maWxsVGV4dCA9'
        'IGZ1bmN0aW9uKHQsIHgsIHkpeyBfZnQucHVzaCh7dDpTdHJpbmcodCksIHgsIHl9KTsgcmV0dXJu'
        'IF9meC5hcHBseSh0aGlzLCBhcmd1bWVudHMpOyB9OwogIHRoUGxhdGUgPSBmdW5jdGlvbih4LCB5'
        'LCB3LCBoKXsgX3BsLnB1c2goe3gsIHksIHcsIGh9KTsgcmV0dXJuIF90cC5hcHBseSh0aGlzLCBh'
        'cmd1bWVudHMpOyB9OwogIHRyeSB7IGRyYXdPYmpMaW5lKHt0eHQ6bWlzc2lvbk9iaiwgY29sOicj'
        'ZmZmJ30pOyBkcmF3RmxlZVdhcm5pbmcoKTsgfQogIGZpbmFsbHkgeyBjdHguZmlsbFRleHQgPSBf'
        'Zng7IHRoUGxhdGUgPSBfdHA7IH0KICBjb25zdCBfZncgPSBfZnQuZmluZChvPT4vSlVNUElORyBP'
        'VVQgSU4vLnRlc3Qoby50KSk7CiAgci5jb3VudGRvd25OYW1lc1NoaXAgPSAhIV9mdyAmJiAvRkFV'
        'U1RVUy8udGVzdChfZncudCk7CiAgY29uc3QgX29sID0gX3BsWzBdLCBfY2QgPSBfcGxbX3BsLmxl'
        'bmd0aC0xXTsKICByLmNvdW50ZG93bkNsZWFyT2ZPYmplY3RpdmUgPSAhIV9vbCAmJiAhIV9jZCAm'
        'JiBfcGwubGVuZ3RoPj0yICYmCiAgICAoX29sLngrX29sLncgPCBfY2QueCkgJiYgKF9jZC54K19j'
        'ZC53IDw9IFcpOwogIGRhbWFnZUVuZW15KGYsIGYubWF4SHAqNSwgZi54LCBmLnksIHRydWUsICdi'
        'b2x0Jyk7IEZTLnN0ZXAoMik7CiAgci5jYW5ub3RCZURlc3Ryb3llZCA9IGVuZW1pZXMuaW5jbHVk'
        'ZXMoZik7CiAgY29uc3Qga2lsbCA9IGlkPT57IGZvcihjb25zdCBzIG9mIGYuc3VicykgaWYocy5p'
        'ZD09PWlkKXsgcy5kZWFkPXRydWU7IHMuaHA9MDsgfSB9OwogIGtpbGwoJ25hdmlnYXRpb24nKTsg'
        'RlMuc3RlcCgyKTsKICBjb25zdCBmdCA9IGYuZmxlZVQ7IEZTLnN0ZXAoMjAwKTsKICByLm5vTmF2'
        'aWdhdGlvbk5vSnVtcCA9IGYuZmxlZVQ9PT1mdDsKICByLm5vQXJnb1lldCA9ICFhbGxpZXMuc29t'
        'ZShhPT5hLnVpZD09PSdUMScpICYmICFzcGF3blEuc29tZShxPT5xLnVpZD09PSdUMScpOwogIGtp'
        'bGwoJ3dlYXBvbnMnKTsgRlMuc3RlcCgyKTsKICByLmNvdmVyVGhlQXJnbyA9IG1pc3Npb25PYmo9'
        'PT0nQ09WRVIgVEhFIEFSR08nOwogIGxldCBhcmdvID0gbnVsbDsKICBjb25zdCBhdCA9IEZTLnVu'
        'dGlsKCgpPT57IGFyZ28gPSBhbGxpZXMuZmluZChhPT5hLnVpZD09PSdUMScpOyByZXR1cm4gISFh'
        'cmdvICYmIGFyZ28uaG9sZFQhPW51bGw7IH0sIDkwMDAsIHRydWUpOwogIC8vIEJvYXJkaW5nIHRh'
        'a2VzIGl0cyB0aW1lOiBzaGUgc3RheXMgb24gdGhlIEZhdXN0dXMsIG5vdGhpbmcgaXMgdGFrZW4g'
        'eWV0LgogIGNvbnN0IGF4ID0gYXJnbyAmJiBhcmdvLng7CiAgRlMuc3RlcCg0MDApOwogIHIuYm9h'
        'cmRpbmdIb2xkcyA9IGF0Pj0wICYmICFFVl9ET0NLWydUMSddICYmICFmLmNhcHR1cmVkICYmIE1h'
        'dGguYWJzKGFyZ28ueC1heCkgPCAxICYmIGVuZW1pZXMuaW5jbHVkZXMoZik7CiAgY29uc3QgZ290'
        'ID0gRlMudW50aWwoKCk9PiEhRVZfRE9DS1snVDEnXSwgOTAwMCwgdHJ1ZSk7CiAgRlMuc3RlcCg1'
        'KTsKICByLmRvY2tzQW5kVGFrZXMgPSBnb3Q+PTAgJiYgZi5jYXB0dXJlZD09PXRydWU7CiAgLy8g'
        'QW5kIHRoZW4gYm90aCBqdW1wIC0gdGhlIEFyZ28gZG9lcyBub3QgZmx5IG9uIHRvIHRoZSByaWdo'
        'dC4KICByLmFyZ29KdW1wc091dCA9ICEhYXJnbyAmJiBhcmdvLndhcnBPdXQ+MCAmJiAhYXJnby5j'
        'cm9zc2luZzsKICByLmNvbXBsZXRlQ2FyZCA9ICEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdG'
        'QVVTVFVTIENBUFRVUkVEJzsKICBGUy5zdGVwKDMwMCk7CiAgci5ub0ZhaWx1cmVBZnRlcndhcmRz'
        'ID0gIWFsbGllcy5pbmNsdWRlcyhhcmdvKSAmJiAhKG9iakNhcmQgJiYgb2JqQ2FyZC50b25lPT09'
        'J2ZhaWwnKTsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNDYgbGVmdCBhbG9uZSBzaGUganVt'
        'cHM6IGZhaWxlZCcsICdtPTQ2JywgYAogIEZTLnN0ZXAoMzAwKTsKICBjb25zdCBmID0gZW5lbWll'
        'cy5maW5kKGU9PmUudWlkPT09J0YxJyk7CiAgZm9yKGNvbnN0IHMgb2YgZi5zdWJzKSBzLmhwID0g'
        'cy5tYXhIcCA9IDFlNzsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9PiEhb2JqQ2FyZCAmJiBvYmpD'
        'YXJkLnRvbmU9PT0nZmFpbCcsIDkwMDAsIHRydWUpOwogIHJldHVybiB7ZmFpbENhcmQ6IHQ+PTAg'
        'JiYgb2JqQ2FyZC50eHQ9PT0nVEhFIEZBVVNUVVMgR09UIEFXQVknfTtgKTsKCnNjZW5hcmlvKCdN'
        'NDcgRGllIHp3ZWl0ZSBGbHVjaHQnLCAnbT00NycsIGAKICBjb25zdCByID0ge307CiAgc2NvcmUg'
        'PSA1MDAwOwogIEZTLnN0ZXAoNDAwKTsKICByLmljZW5pID0gZW5lbWllcy5zb21lKGU9PmUudWlk'
        'PT09J1YxJyAmJiBlLmljZW5pKTsKICByLmhlY2F0ZSA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09'
        'PSdWMicgJiYgZS5pbWc9PT0nbnRmZGVoZWNhdGUnKTsKICByLm5vQWxsaWVzID0gIWFsbGllcy5z'
        'b21lKGE9PiFhLnNtYWxsKTsKICByLm5vQWVvbHVzID0gIWVuZW1pZXMuc29tZShlPT5lLnVpZD09'
        'PSdLMScpOwogIGNvbnN0IF92MSA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdWMScpLCBfdjIg'
        'PSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nVjInKTsKICBjb25zdCBfeTEgPSBfdjEgJiYgX3Yx'
        'LnksIF95MiA9IF92MiAmJiBfdjIueTsKICBGUy5zdGVwKDMwMCk7CiAgci5zaGlwc0hvbGRIZWln'
        'aHQgPSAhIV92MSAmJiAhIV92MiAmJiBNYXRoLmFicyhfdjEueS1feTEpPDAuNSAmJiBNYXRoLmFi'
        'cyhfdjIueS1feTIpPDAuNSAmJgogICAgTWF0aC5hYnMoX3YxLnktMTUwKTwxICYmIE1hdGguYWJz'
        'KF92Mi55LTM1MCk8MTsKICByLmljZW5pRm9ydHlTZWNvbmRzID0gISFfdjEgJiYgX3YxLmZsZWVU'
        'PjAgJiYgX3YxLmZsZWVUIDw9IDQwKlRJQ0tfSFo7CiAgci5ub0VuZGxlc3NSZWluZm9yY2VtZW50'
        'ID0gIWV2UmVpbmY7CiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT4hZW5lbWllcy5zb21lKGU9PmUu'
        'dWlkPT09J1YxJyksIDkwMDAsIHRydWUpOwogIHIuaWNlbmlHZXRzQXdheSA9IHQ+PTAgJiYgaWNl'
        'bkVzY2FwZXM9PT0xICYmIHNjb3JlPj01MDAwOwogIGNvbnN0IHYgPSBlbmVtaWVzLmZpbmQoZT0+'
        'ZS51aWQ9PT0nVjInKTsgaWYodikgdi5ocCA9IDA7CiAgci5jb21wbGV0ZUNhcmQgPSBGUy51bnRp'
        'bCgoKT0+ISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J0hFQ0FURSBERVNUUk9ZRUQnLCAzMDAw'
        'LCBmYWxzZSkgPj0gMDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNDggRGllIEF1ZmtsYWVy'
        'dW5nJywgJ209NDgnLCBgCiAgY29uc3QgciA9IHt9OwogIHNjb3JlID0gMjAwMDsKICByLmFubm91'
        'bmNlZCA9IE5PVElDRVMuc29tZShuPT5uLnR4dD09PSdHVEYgUEVHQVNVUyBBU1NJR05FRCcpOwog'
        'IEZTLnN0ZXAoNDAwKTsKICByLmZseWluZ0FQZWdhc3VzID0gcGxheWVyLnNoaXA9PT0nZmlwZWdh'
        'c3VzJzsKICByLm5vdGhpbmdMb2Nrc0hlciA9ICFjYW5Mb2NrT24ocGxheWVyKTsKICBjb25zdCB2'
        'ID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyk7CiAgci5ndW5zSG9sZEZpcmUgPSBjYXBH'
        'dW5UYXJnZXQodik9PT1udWxsOwogIHIubm9CZWFtT25IZXIgPSAhYmVhbVRhcmdldHModiwgZmFs'
        'c2UpLmluY2x1ZGVzKHBsYXllcik7CiAgci5ub0hhbmdhciA9IHNoaXBTd2FwUmVhZHkoKT09PWZh'
        'bHNlOwogIHIucmluZ3NTaG93biA9ICEhdiAmJiB2LnNjYW5TdWJzPT09dHJ1ZSAmJiB2LnN1YnMu'
        'ZXZlcnkocz0+IXMuc2Nhbm5lZCk7CiAgZm9yKGNvbnN0IHMgb2Ygdi5zdWJzKXsgY29uc3QgcCA9'
        'IHN1YlBvcyh2LCBzKTsgRlMuaG9sZChwLngsIHAueSwgU1VCX1NDQU5fVElNRSArIDIwKTsgfQog'
        'IHIuYWxsRml2ZVNjYW5uZWQgPSB2LnN1YnMuZXZlcnkocz0+cy5zY2FubmVkKSAmJiB2LnNjYW5u'
        'ZWQ9PT10cnVlOwogIEZTLnN0ZXAoMyk7CiAgci5jb21wbGV0ZUNhcmQgPSAhIW9iakNhcmQgJiYg'
        'b2JqQ2FyZC50eHQ9PT0nT1JJT04gU0NBTk5FRCc7CiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT4h'
        'ZW5lbWllcy5pbmNsdWRlcyh2KSwgMTUwMCwgZmFsc2UpOwogIHIub3Jpb25MZWF2ZXNXaXRob3V0'
        'UGVuYWx0eSA9IHQ+PTAgJiYgc2NvcmUgPj0gMjAwMDsKICBGUy51bnRpbCgoKT0+d2F2ZT40OCwg'
        'MzAwMDAsIHRydWUpOwogIHIub3duSHVsbEJhY2tOZXh0V2F2ZSA9IHdhdmU9PT00OSAmJiBwbGF5'
        'ZXIuc2hpcD09PSdmaW15cm1pZG9uJzsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdDb2xvc3N1'
        'cyBiZWFtcyBhcmUgVGVycmFuJywgJycsIGAKICByZXR1cm4ge21haW46IGJlYW1Db2woJ2d0dmEn'
        'LCB0cnVlKT09PScjMDBmZjU1JywgYW50aUZpZ2h0ZXI6IGJlYW1Db2woJ2d0dmEnLCBmYWxzZSk9'
        'PT0nIzQ0OTlmZid9O2AsIHRydWUpOwoKc2NlbmFyaW8oJ0hvTCBzdGFydCB1bmNoYW5nZWQnLCAn'
        'bT0xJywgYAogIHJldHVybiB7d2F2ZTogd2F2ZSwgdGhvdGg6IHBsYXllci5zaGlwPT09J2ZpdG90'
        'aCcsIHZhc3VkYW5DYWxsOiBBTExZX0ZBQ19PTi52YXN1ZGFuPT09dHJ1ZSAmJiBBTExZX0ZBQ19P'
        'Ti50ZXJyYW49PT1mYWxzZX07YCk7CgovLyDilIDilIAgUnVubmVyIOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgAooYXN5'
        'bmMoKT0+ewogIGNvbnN0IGJyb3dzZXIgPSBhd2FpdCBjaHJvbWl1bS5sYXVuY2goKTsKICBsZXQg'
        'ZmFpbHMgPSAwOwogIGNvbnN0IG9ubHkgPSBwcm9jZXNzLmFyZ3ZbNF07CiAgZm9yKGNvbnN0IHNj'
        'IG9mIHNjZW5hcmlvcyl7CiAgICBpZihvbmx5ICYmIHNjLm5hbWUuaW5kZXhPZihvbmx5KTwwKSBj'
        'b250aW51ZTsKICAgIGNvbnN0IHBhZ2UgPSBhd2FpdCBicm93c2VyLm5ld1BhZ2UoKTsKICAgIGNv'
        'bnN0IGVycnMgPSBbXTsKICAgIHBhZ2Uub24oJ3BhZ2VlcnJvcicsIGU9PmVycnMucHVzaChTdHJp'
        'bmcoZS5tZXNzYWdlfHxlKSkpOwogICAgYXdhaXQgcGFnZS5nb3RvKCdmaWxlOi8vJyArIHRtcCAr'
        'ICc/JyArIHNjLnF1ZXJ5KTsKICAgIGF3YWl0IHBhZ2Uud2FpdEZvclRpbWVvdXQoMzAwKTsKICAg'
        'IGxldCByZXM7CiAgICB0cnl7CiAgICAgIHJlcyA9IGF3YWl0IHBhZ2UuZXZhbHVhdGUoSEVMUEVS'
        'UyArIGBcbkZTLmZha2VJbWFnZXMoKTtgICsgKHNjLm5vTGF1bmNoID8gJycgOiAnIGxhdW5jaEdh'
        'bWUoKTsnKSArIGBcbihmdW5jdGlvbigpeyR7c2MuYm9keX19KSgpYCk7CiAgICB9Y2F0Y2goZSl7'
        'IHJlcyA9IG51bGw7IGVycnMucHVzaChTdHJpbmcoZS5tZXNzYWdlfHxlKSk7IH0KICAgIGNvbnNv'
        'bGUubG9nKHNjLm5hbWUgKyAnICAoPycgKyBzYy5xdWVyeSArICcpJyk7CiAgICBpZihyZXMpIGZv'
        'cihjb25zdCBbayx2XSBvZiBPYmplY3QuZW50cmllcyhyZXMpKXsKICAgICAgY29uc3QgZ29vZCA9'
        'ICh0eXBlb2Ygdj09PSdib29sZWFuJykgPyB2IDogdHJ1ZTsKICAgICAgaWYoIWdvb2QpIGZhaWxz'
        'Kys7CiAgICAgIGNvbnNvbGUubG9nKChnb29kID8gJyAgb2sgICAgJyA6ICcgIEZBSUwgICcpICsg'
        'ayArICh0eXBlb2Ygdj09PSdib29sZWFuJyA/ICcnIDogJyA9ICcgKyBKU09OLnN0cmluZ2lmeSh2'
        'KSkpOwogICAgfQogICAgaWYoZXJycy5sZW5ndGgpeyBmYWlscysrOyBjb25zb2xlLmxvZygnICBG'
        'QUlMICBwYWdlIGVycm9yczpcbiAgICAnICsgZXJycy5zbGljZSgwLDQpLmpvaW4oJ1xuICAgICcp'
        'KTsgfQogICAgYXdhaXQgcGFnZS5jbG9zZSgpOwogIH0KICBhd2FpdCBicm93c2VyLmNsb3NlKCk7'
        'CiAgZnMudW5saW5rU3luYyh0bXApOwogIGNvbnNvbGUubG9nKCdcbicgKyAoZmFpbHMgPyBmYWls'
        'cyArICcgRkFJTEVEJyA6ICdhbGwgcGFzc2VkJykpOwogIHByb2Nlc3MuZXhpdChmYWlscyA/IDEg'
        'OiAwKTsKfSkoKTsK'
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
        'cm4nLCAnZnJlaWdlYmVuJywgJ2t1bGlzc2UnLCAncnVmJ10pOwoKbGV0IGVycm9ycyA9IDAsIG1p'
        'c3Npb25zID0gMDsKZm9yKGNvbnN0IGtleSBvZiBPYmplY3Qua2V5cyhTQ1JJUFRfV0FWRVMpLnNv'
        'cnQoKGEsIGIpID0+IGEgLSBiKSl7CiAgY29uc3QgbSA9IFNDUklQVF9XQVZFU1trZXldLCB1bml0'
        'cyA9IG0udSB8fCBbXSwgZXZzID0gbS5ldiB8fCBbXTsKICBjb25zdCB0YWcgPSAnTScgKyBTdHJp'
        'bmcoa2V5KS5wYWRTdGFydCgzLCAnMCcpOwogIGNvbnN0IGlkcyA9IG5ldyBNYXAoKTsKICBjb25z'
        'dCBiYWQgPSBbXTsKICBtaXNzaW9ucysrOwoKICBmb3IoY29uc3QgdSBvZiB1bml0cyl7CiAgICBp'
        'ZighdS5pZCkgYmFkLnB1c2goJ3VuaXQgd2l0aG91dCBpZCAoJyArIHUuYyArICcpJyk7CiAgICBl'
        'bHNlIGlmKGlkcy5oYXModS5pZCkpIGJhZC5wdXNoKCdpZCB1c2VkIHR3aWNlOiAnICsgdS5pZCk7'
        'CiAgICBpZHMuc2V0KHUuaWQsIHUpOwogICAgaWYoIUNBVF9GQUNbdS5jXSAmJiAhQ0FUX0ZJWFt1'
        'LmNdKQogICAgICBiYWQucHVzaCh1LmlkICsgJzogdW5rbm93biBjYXRlZ29yeSAiJyArIHUuYyAr'
        'ICciIC0gd291bGQgbmV2ZXIgc3Bhd24nKTsKICB9CiAgZm9yKGNvbnN0IHUgb2YgdW5pdHMpCiAg'
        'ICBpZih1LnNwciAmJiAhSFVMTF9LRVlTLmhhcyh1LnNwcikpIGJhZC5wdXNoKHUuaWQgKyAnOiB1'
        'bmtub3duIGh1bGwgIicgKyB1LnNwciArICciJyk7CiAgaWYobS5mYWMgIT09IENZQ0xFX0ZBQygr'
        'a2V5KSkgYmFkLnB1c2goJ2ZhY3Rpb24gJyArIG0uZmFjICsgJywgYnV0IHRoaXMgd2F2ZSBiZWxv'
        'bmdzIHRvIHRoZSAnICsgQ1lDTEVfRkFDKCtrZXkpICsgJyBjeWNsZScpOwogIGZvcihjb25zdCB1'
        'IG9mIHVuaXRzKXsKICAgIGlmKHUuZG9ja1RvICYmICFpZHMuaGFzKHUuZG9ja1RvKSkgYmFkLnB1'
        'c2godS5pZCArICc6IGRvY2tUbyBwb2ludHMgYXQgbWlzc2luZyBpZCAnICsgdS5kb2NrVG8pOwog'
        'ICAgaWYodS5hdCAmJiAhaWRzLmhhcyh1LmF0KSkgICAgICAgICBiYWQucHVzaCh1LmlkICsgJzog'
        'YXQgcG9pbnRzIGF0IG1pc3NpbmcgaWQgJyArIHUuYXQpOwogIH0KCiAgY29uc3Qgd2FycGVkSW4g'
        'PSBuZXcgU2V0KCk7CiAgbGV0IHJlaW5mT24gPSBmYWxzZSwgcmVpbmZPZmYgPSBmYWxzZTsKICBl'
        'dnMuZm9yRWFjaCgoZSwgaSkgPT4gewogICAgY29uc3Qgd2hlcmUgPSAnZXZlbnQgJyArIChpICsg'
        'MSkgKyAnICgnICsgZS50ICsgJyAtPiAnICsgZS53ICsgJyknOwogICAgY29uc3QgYXJnID0gKGUu'
        'YTIgIT09IHVuZGVmaW5lZCkgPyBlLmEyIDogZS5hOwogICAgaWYoIVRSSUdHRVJTLmhhcyhlLnQp'
        'KSBiYWQucHVzaCh3aGVyZSArICc6IHVua25vd24gdHJpZ2dlciAiJyArIGUudCArICciJyk7CiAg'
        'ICBpZighRUZGRUNUUy5oYXMoZS53KSkgIGJhZC5wdXNoKHdoZXJlICsgJzogdW5rbm93biBlZmZl'
        'Y3QgIicgKyBlLncgKyAnIicpOwogICAgLy8gQSB0cmlnZ2VyIG1heSBuYW1lIHNldmVyYWwgaWRz'
        'IGpvaW5lZCB3aXRoICcrJy4KICAgIGlmKFRSSUdHRVJTLmhhcyhlLnQpICYmICFUUklHX05PX0lE'
        'LmhhcyhlLnQpKQogICAgICBmb3IoY29uc3QgaWQgb2YgU3RyaW5nKGUuYSkuc3BsaXQoJysnKSkK'
        'ICAgICAgICBpZighaWRzLmhhcyhpZCkpIGJhZC5wdXNoKHdoZXJlICsgJzogdHJpZ2dlciBwb2lu'
        'dHMgYXQgbWlzc2luZyBpZCAnICsgaWQpOwogICAgaWYoZS50ID09PSAnYW5nZWRvY2t0JyAmJiBp'
        'ZHMuaGFzKGUuYSkgJiYgIWlkcy5nZXQoZS5hKS5kb2NrVG8pCiAgICAgIGJhZC5wdXNoKHdoZXJl'
        'ICsgJzogJyArIGUuYSArICcgaGFzIG5vIGRvY2tUbywgaXQgY2FuIG5ldmVyIGRvY2snKTsKICAg'
        'IGlmKEVGRkVDVF9VTklULmhhcyhlLncpICYmICFpZHMuaGFzKGFyZykpCiAgICAgIGJhZC5wdXNo'
        'KHdoZXJlICsgJzogZWZmZWN0IHBvaW50cyBhdCBtaXNzaW5nIGlkICcgKyBhcmcpOwogICAgaWYo'
        'ZS53ID09PSAnamFnZCcgJiYgYXJnICYmICFpZHMuaGFzKGFyZykpCiAgICAgIGJhZC5wdXNoKHdo'
        'ZXJlICsgJzogaHVudCB0YXJnZXQgaXMgYSBtaXNzaW5nIGlkICcgKyBhcmcpOwogICAgaWYoZS53'
        'ID09PSAnZWlud2FycGVuJyl7CiAgICAgIHdhcnBlZEluLmFkZChhcmcpOwogICAgICBpZihpZHMu'
        'aGFzKGFyZykgJiYgIWlkcy5nZXQoYXJnKS53YWl0KQogICAgICAgIGJhZC5wdXNoKHdoZXJlICsg'
        'JzogJyArIGFyZyArICcgaXMgbm90IHdhaXRpbmcgLSB3YXJwaW5nIGl0IGluIGRvZXMgbm90aGlu'
        'ZycpOwogICAgfQogICAgaWYoZS53ID09PSAnbmFjaHNjaHViJyl7IGlmKGFyZyA9PT0gJ2F1cycp'
        'IHJlaW5mT2ZmID0gdHJ1ZTsgZWxzZSByZWluZk9uID0gdHJ1ZTsgfQogICAgaWYoZS53ID09PSAn'
        'ZW5kZScpIHJlaW5mT2ZmID0gdHJ1ZTsKICB9KTsKICBmb3IoY29uc3QgdSBvZiB1bml0cykKICAg'
        'IGlmKHUud2FpdCAmJiAhd2FycGVkSW4uaGFzKHUuaWQpKSBiYWQucHVzaCh1LmlkICsgJzogd2Fp'
        'dHMsIGJ1dCBubyBldmVudCBldmVyIHdhcnBzIGl0IGluJyk7CiAgaWYocmVpbmZPbiAmJiAhcmVp'
        'bmZPZmYpIGJhZC5wdXNoKCdyZWluZm9yY2VtZW50cyBzd2l0Y2hlZCBvbiwgbmV2ZXIgc3dpdGNo'
        'ZWQgb2ZmJyk7CiAgaWYobS5odW50ICYmICFpZHMuaGFzKG0uaHVudCkpIGJhZC5wdXNoKCdodW50'
        'IHBvaW50cyBhdCBtaXNzaW5nIGlkICcgKyBtLmh1bnQpOwoKICBpZihiYWQubGVuZ3RoKXsgZXJy'
        'b3JzICs9IGJhZC5sZW5ndGg7IGNvbnNvbGUubG9nKHRhZyArICcgJyArIChtLm5hbWUgfHwgJycp'
        'KTsgYmFkLmZvckVhY2goYiA9PiBjb25zb2xlLmxvZygnICAgJyArIGIpKTsgfQp9CmNvbnNvbGUu'
        'bG9nKCdcbicgKyBtaXNzaW9ucyArICcgbWlzc2lvbnMgY2hlY2tlZCwgJyArIGVycm9ycyArICcg'
        'cHJvYmxlbXMnKTsKY29uc29sZS5sb2coJ2tub3duIHRyaWdnZXJzOiAnICsgWy4uLlRSSUdHRVJT'
        'XS5qb2luKCcgJykpOwpjb25zb2xlLmxvZygna25vd24gZWZmZWN0czogICcgKyBbLi4uRUZGRUNU'
        'U10uam9pbignICcpKTsKcHJvY2Vzcy5leGl0KGVycm9ycyA/IDEgOiAwKTsK'
    ),
}
for name, data in TEST_FILES.items():
    open(name, 'wb').write(base64.b64decode(data))
print("v140 applied: fixes to missions 50-54, beams under the hulls, checks updated. Now run: python3 assemble.py 140")
