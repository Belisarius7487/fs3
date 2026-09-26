#!/usr/bin/env python3
"""FS3 v133 - objectives in the new look, and the fixes from the v132 test.

OBJECTIVES
  The old banner (Courier, a box, blinking) is gone. In its place:
  - a card that comes in at the top of the field for about two seconds
    whenever there is something new: NEW OBJECTIVE, OBJECTIVE COMPLETE,
    OBJECTIVE FAILED, PARTIAL SUCCESS.
  - a line under the bar, on the left, that keeps the current objective in
    view afterwards without covering the fight.
  Nothing blinks. Missions can now say what they want in words:
  - a mission's own objective at the start (ziel:'...' on the mission),
  - effects 'ziel' (new objective), 'zielerfuellt' and 'zielverfehlt'
    (the result card, with a line of text).
  While a mission speaks for itself, the automatic result cards stay quiet,
  so nothing is announced twice.
  The countdown for a ship about to jump, the pause screen and the FPS and
  OBJ read-outs are drawn from the same kit now as well.

MISSIONS
  M33  says what to do: destroy the Faustus relay.
  M38  she keeps a fixed height in the middle of the field, and the Elysium
       only comes once BOTH her engines and her weapons are down - she can
       no longer shoot it to pieces. The objective line walks through it.
  M40  more of it: three rounds of Hercules Mk II and Ursa, and
       reinforcements until the last bombers are down.
  M42  says what to do: her weapons first, then her. If she withdraws
       instead, that is a failed objective.

OTHER
  - Freighters, transports, gas miners and the Hippocrates have a hull bar
    now, like the warships.
  - The Colossus fires green main beams and blue anti-fighter beams like
    every Terran ship. Her faction became 'gtva' along the way, and the
    colour table did not know it.
  - Mission triggers: 'subsystem' accepts several joined with '+' (all of
    them down); new trigger 'vernichtet' (destroyed - not left, not fled,
    not taken). A ship that finishes a crossing, jumps on a deadline or is
    captured is recorded as such, so 'zerstoert' no longer mistakes a
    captured ship for a destroyed one.

Needs v132. Edits src/30_waves.js, src/40_world.js, src/50_combat.js,
src/60_effects.js and src/70_ui.js in place, and writes the updated
docksim.js and fieldsim.js. Run assemble.py afterwards.
"""
import sys


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def replace_between(text, start, end, new, label):
    """Replaces everything from start up to (not including) end."""
    if text.count(start) != 1 or text.count(end) != 1:
        sys.exit("Abbruch (%s): Anfang %d-mal, Ende %d-mal gefunden, erwartet je einmal."
                 % (label, text.count(start), text.count(end)))
    i = text.index(start)
    j = text.index(end)
    if j <= i:
        sys.exit("Abbruch (%s): Ende steht vor dem Anfang." % label)
    return text[:i] + new + text[j:]


def load(p):
    return open(p, encoding="utf-8").read()


wv = load("src/30_waves.js")
wo = load("src/40_world.js")
cb = load("src/50_combat.js")
fx = load("src/60_effects.js")
ui = load("src/70_ui.js")

# ══ 30_waves.js ═════════════════════════════════════════════════════════

# ── Event stores: taken and fled, beside left ──────────────────────────
wv = replace_once(
    wv,
    "let EV = [], EV_HELD = {}, EV_SEEN = {}, EV_LEFT = {}, EV_DOCK = {};\n",
    "let EV = [], EV_HELD = {}, EV_SEEN = {}, EV_LEFT = {}, EV_DOCK = {};\n"
    "// EV_TAKEN: captured ('kapern'). EV_FLED: jumped out on a deadline.\n"
    "// Neither is a kill, and 'vernichtet' asks for a kill.\n"
    "let EV_TAKEN = {}, EV_FLED = {};\n",
    "EV stores")

wv = replace_once(
    wv,
    "  EV = []; EV_HELD = {}; EV_SEEN = {}; EV_LEFT = {}; EV_DOCK = {}; EV_POS = {};\n",
    "  EV = []; EV_HELD = {}; EV_SEEN = {}; EV_LEFT = {}; EV_DOCK = {}; EV_POS = {};\n"
    "  EV_TAKEN = {}; EV_FLED = {};\n",
    "evReset")

wv = replace_once(
    wv,
    "    case 'zerstoert':    return evSeen(ev.a) && byId(ev.a).length===0 && !EV_LEFT[ev.a];\n",
    "    case 'zerstoert':    return evSeen(ev.a) && byId(ev.a).length===0 && !EV_LEFT[ev.a] && !EV_TAKEN[ev.a];\n"
    "    // Destroyed and nothing else: not left, not fled on a deadline, not\n"
    "    // taken. 'zerstoert' stays as it was, because written missions rely\n"
    "    // on it firing for a ship that jumped out.\n"
    "    case 'vernichtet':   return evSeen(ev.a) && byId(ev.a).length===0\n"
    "                              && !EV_LEFT[ev.a] && !EV_FLED[ev.a] && !EV_TAKEN[ev.a];\n",
    "evTrig: vernichtet")

wv = replace_once(
    wv,
    "    case 'verlaesst':    return !!EV_LEFT[ev.a];\n",
    "    case 'verlaesst':    return !!EV_LEFT[ev.a] || !!EV_FLED[ev.a];\n",
    "evTrig: verlaesst")

wv = replace_once(
    wv,
    "      return !subOK(su, ev.b || 'communication');\n",
    "      // Several may be named, joined with '+': all of them have to be down.\n"
    "      return String(ev.b || 'communication').split('+')\n"
    "               .every(function(id){ return !subOK(su, id); });\n",
    "evTrig: subsystem list")

wv = replace_once(
    wv,
    "    if(['zerstoert','alleZerstoert','verlaesst','anzahlUnter','rumpfUnter','subsystem'].indexOf(e.t)>=0){\n",
    "    if(['zerstoert','vernichtet','alleZerstoert','verlaesst','anzahlUnter','rumpfUnter','subsystem'].indexOf(e.t)>=0){\n",
    "evPending: vernichtet")

# ── Effects: objectives in words; a capture is recorded as such ─────────
wv = replace_once(
    wv,
    "        EV_LEFT[arg] = true;\n"
    "        score += u.pts || 0;\n",
    "        EV_TAKEN[arg] = true;\n"
    "        score += u.pts || 0;\n",
    "kapern: taken")

wv = replace_once(
    wv,
    "    case 'freigeben':\n",
    "    case 'ziel':\n"
    "      // The mission's own objective, in words. Announced by a card and\n"
    "      // kept in the line under the bar.\n"
    "      missionObj = String(arg || '').toUpperCase();\n"
    "      missionObjUsed = true;\n"
    "      break;\n"
    "    case 'zielerfuellt':\n"
    "    case 'zielverfehlt':\n"
    "      missionObj = '';\n"
    "      missionObjUsed = true;\n"
    "      objAnnounce(ev.w==='zielerfuellt' ? 'OBJECTIVE COMPLETE' : 'OBJECTIVE FAILED',\n"
    "                  String(arg || '').toUpperCase(),\n"
    "                  ev.w==='zielerfuellt' ? 'done' : 'fail');\n"
    "      break;\n"
    "    case 'freigeben':\n",
    "evFire: ziel")

# The mission's opening objective.
wv = replace_once(
    wv,
    "  waveMod = def.mod || MOD_NONE;\n"
    "  if(nebulaOn()) nebTint",
    "  waveMod = def.mod || MOD_NONE;\n"
    "  // A mission that states its objective in words speaks for itself for\n"
    "  // the whole wave; the automatic result cards then stay quiet.\n"
    "  missionObj = String(def.ziel || '').toUpperCase();\n"
    "  missionObjUsed = !!def.ziel || (def.ev||[]).some(function(e){ return /^ziel/.test(e.w); });\n"
    "  if(nebulaOn()) nebTint",
    "buildScripted: ziel")

# A crossing that is through has left.
wv = replace_once(
    wv,
    "      crossDone++; if(!a.emptyRun) protSaved++;\n",
    "      crossDone++; if(!a.emptyRun) protSaved++;\n"
    "      if(a.uid) EV_LEFT[a.uid] = true;\n",
    "crossing: left")

# ── Missions ────────────────────────────────────────────────────────────
wv = replace_once(
    wv,
    "  33:{name:'Die Relaisstation', fac:'ntf', o:'clear', live:5, u:[\n",
    "  33:{name:'Die Relaisstation', fac:'ntf', o:'clear', live:5,\n"
    "      ziel:'DESTROY THE FAUSTUS RELAY', u:[\n",
    "M33: ziel")
wv = replace_once(
    wv,
    "       {t:'sek', a:1, w:'nachschub', a2:'an'},\n"
    "       {t:'zerstoert', a:'S1', w:'nachschub', a2:'aus'}\n",
    "       {t:'sek', a:1, w:'nachschub', a2:'an'},\n"
    "       {t:'zerstoert', a:'S1', w:'nachschub', a2:'aus'},\n"
    "       {t:'vernichtet', a:'S1', w:'zielerfuellt', a2:'RELAY DESTROYED'}\n",
    "M33: result")

wv = replace_between(
    wv,
    "  38:{name:'Die Kaperung'",
    "  39:{name:'Die Gasernte'",
    "  38:{name:'Die Kaperung', fac:'ntf', o:'clear', live:5,\n"
    "      ziel:'DISABLE THE DEIMOS - ENGINES AND WEAPONS', u:[\n"
    "       // An NTF Deimos makes for the right edge and jumps there. With\n"
    "       // her engines AND her weapons down an Elysium comes to take her -\n"
    "       // with her guns still up it would not live to dock. She keeps a\n"
    "       // fixed height mid-field, so both subsystems can be reached.\n"
    "       // Until the Elysium is lost she cannot be destroyed.\n"
    "       {id:'D1', c:'co', n:1, spr:'ntfcodeimos', x:-60, y:260, escape:0.22,\n"
    "        escWarp:true, capture:true},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'E2', c:'fi', n:1, wait:true},\n"
    "       {id:'T1', c:'tr', n:1, spr:'trelysium', side:'ally', x:-40,\n"
    "        dockTo:'D1', wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'subsystem', a:'D1', b:'engines+weapons', w:'einwarpen', a2:'T1'},\n"
    "       {t:'subsystem', a:'D1', b:'engines+weapons', w:'ziel', a2:'COVER THE ELYSIUM'},\n"
    "       {t:'angedockt', a:'T1', w:'kapern', a2:'D1'},\n"
    "       {t:'angedockt', a:'T1', w:'zielerfuellt', a2:'DEIMOS CAPTURED'},\n"
    "       {t:'vernichtet', a:'T1', w:'freigeben', a2:'D1'},\n"
    "       {t:'vernichtet', a:'T1', w:'zielverfehlt', a2:'ELYSIUM LOST'},\n"
    "       {t:'verlaesst', a:'D1', w:'zielverfehlt', a2:'THE DEIMOS GOT AWAY'}\n"
    "     ]},\n"
    "\n",
    "M38")

wv = replace_between(
    wv,
    "  40:{name:'Der Sensorsturm'",
    "  41:{name:'Das Lazarett'",
    "  40:{name:'Der Sensorsturm', fac:'ntf', o:'guard', live:5, mod:'emp', u:[\n"
    "       // An EMP storm, which is a nebula phenomenon: haze, and now and\n"
    "       // then no lock for anybody. Three rounds of Hercules Mk II and\n"
    "       // Ursa go for an Orion, with reinforcements until the last\n"
    "       // bombers are down.\n"
    "       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', hp:1.2},\n"
    "       {id:'E1', c:'fi', n:2, spr:'fihercmk2'},\n"
    "       {id:'B1', c:'bo', n:1, spr:'boursa', wait:true},\n"
    "       {id:'E2', c:'fi', n:2, spr:'fihercmk2', wait:true},\n"
    "       {id:'B2', c:'bo', n:1, spr:'boursa', wait:true},\n"
    "       {id:'E3', c:'fi', n:2, spr:'fihercmk2', wait:true},\n"
    "       {id:'B3', c:'bo', n:2, spr:'boursa', wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},\n"
    "       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'B2'},\n"
    "       {t:'alleZerstoert', a:'E2', w:'einwarpen', a2:'E3'},\n"
    "       {t:'alleZerstoert', a:'B2', w:'einwarpen', a2:'B3'},\n"
    "       {t:'alleZerstoert', a:'B3', w:'nachschub', a2:'aus'}\n"
    "     ]},\n"
    "\n",
    "M40")

wv = replace_once(
    wv,
    "  42:{name:'Die Hecate', fac:'ntf', o:'guard', live:5, u:[\n",
    "  42:{name:'Die Hecate', fac:'ntf', o:'guard', live:5,\n"
    "      ziel:'DISABLE HECATE WEAPONS', u:[\n",
    "M42: ziel")
wv = replace_once(
    wv,
    "       {t:'subsystem', a:'V1', b:'weapons', w:'meldung', a2:'Hecate weapons offline'},\n"
    "       {t:'zerstoert', a:'V1', w:'nachschub', a2:'aus'}\n",
    "       {t:'subsystem', a:'V1', b:'weapons', w:'ziel', a2:'DESTROY THE HECATE'},\n"
    "       {t:'vernichtet', a:'V1', w:'zielerfuellt', a2:'HECATE DESTROYED'},\n"
    "       {t:'verlaesst', a:'V1', w:'zielverfehlt', a2:'THE HECATE WITHDREW'},\n"
    "       {t:'zerstoert', a:'V1', w:'nachschub', a2:'aus'}\n",
    "M42: steps")

# ══ 40_world.js ═════════════════════════════════════════════════════════
wo = replace_once(
    wo,
    "    e.fleeT--;\n"
    "    if(e.fleeT<=0){\n",
    "    e.fleeT--;\n"
    "    if(e.fleeT<=0){\n"
    "      if(e.uid) EV_FLED[e.uid] = true;     // she jumps on her deadline\n",
    "runFlee: fled")

# ══ 50_combat.js ════════════════════════════════════════════════════════
cb = replace_once(
    cb,
    "  if(faction==='hol') faction = 'vasudan';\n",
    "  if(faction==='hol') faction = 'vasudan';\n"
    "  // The Colossus belongs to no side's column any more ('gtva'), but she\n"
    "  // is a Terran-built ship and fires Terran beams.\n"
    "  if(faction==='gtva') faction = 'terran';\n",
    "beamCol: gtva")

# ══ 60_effects.js ═══════════════════════════════════════════════════════
fx = replace_once(
    fx,
    "  objWasSet=false; objDoneT=0; objFailed=false; objSeenOnce=false;\n",
    "  objWasSet=false; objDoneT=0; objFailed=false; objSeenOnce=false;\n"
    "  missionObj=''; missionObjUsed=false; objCard=null; objPinned='';\n",
    "nextWave: objectives")

# ══ 70_ui.js ════════════════════════════════════════════════════════════

# ── Hull bars for freighters too ────────────────────────────────────────
ui = replace_once(
    ui,
    "      if(e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||\n"
    "         e.type==='boss'||e.type==='station'){\n"
    "        const hbImg=IMGS[e.img];if(hbImg){\n"
    "          var bwMult=(e.type==='boss'?0.75:(e.type==='destroyer'?0.55:0.70));\n",
    "      // Freighters count too: transports, miners and hospital ships are\n"
    "      // often what a mission is about, and how much hull they have left is\n"
    "      // what decides how hard to fight for them.\n"
    "      if(e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||\n"
    "         e.type==='boss'||e.type==='station'||e.type==='freighter'){\n"
    "        const hbImg=IMGS[e.img];if(hbImg){\n"
    "          var bwMult=(e.type==='boss'?0.75:(e.type==='destroyer'?0.55:\n"
    "                     (e.type==='freighter'?0.80:0.70)));\n",
    "hull bars: freighters")

# ── The objective card and line ────────────────────────────────────────
ui = replace_between(
    ui,
    "function drawFieldBanner(){\n",
    "// Stacked, most urgent at the top. Three at once is already more capital\n",
    "// ── OBJECTIVES ───────────────────────────────────────────────\n"
    "// Two parts. A card comes in at the top of the field whenever there is\n"
    "// something new to know - a new objective, one met, one failed - and goes\n"
    "// again after a couple of seconds. A line under the bar, on the left,\n"
    "// keeps the current objective in view afterwards without covering the\n"
    "// fight. Nothing blinks: the card arriving is the signal.\n"
    "const OBJ_CARD_TIME = 230;    // steps a card stays, fades included\n"
    "const OBJ_CARD_FADE = 18;     // steps to come in, and to go\n"
    "const OBJ_TONE = {done:'#4dff88', fail:'#ff5533', part:'#ffcc44'};\n"
    "let objCard = null;           // {head, txt, tone, t0}\n"
    "let objPinned = '';           // the objective the last card announced\n"
    "let missionObj = '';          // a mission's own objective, see 'ziel'\n"
    "let missionObjUsed = false;   // this wave speaks for itself\n"
    "function objStrip(t){ return String(t||'').replace(/^\\[\\s*/, '').replace(/\\s*\\]$/, ''); }\n"
    "function objAnnounce(head, txt, tone){ objCard = {head:head, txt:txt, tone:tone, t0:fc}; }\n"
    "// What the player is to do right now, or null. A mission's own words\n"
    "// come first; otherwise whatever the field says.\n"
    "function currentObjective(){\n"
    "  if(missionObj) return {txt:missionObj, col:TH('accentWarm')};\n"
    "  // A mission that speaks for itself is not talked over by the field:\n"
    "  // between its own objectives there is nothing automatic to announce.\n"
    "  if(missionObjUsed) return null;\n"
    "  const ob = objectiveText();\n"
    "  return ob ? {txt:objStrip(ob.txt), col:ob.col} : null;\n"
    "}\n"
    "function drawFieldBanner(){\n"
    "  if(GS!=='playing') return;\n"
    "  const ob = objectiveText();\n"
    "  const prev = objPinned;\n"
    "  // Bookkeeping of the automatic objectives, as before: while one stands\n"
    "  // it counts as set, and when it goes it was met or failed.\n"
    "  if(ob){ objWasSet = true; objSeenOnce = true; }\n"
    "  else if(objWasSet){\n"
    "    objWasSet = false; objDoneT = OBJ_DONE_TIME; objFailed = guardLost;\n"
    "    if(!missionObjUsed){\n"
    "      if(objFailed && protSaved>0)\n"
    "        objAnnounce('PARTIAL SUCCESS', protSaved+' OF '+(protSaved+protLost)+' GOT THROUGH', 'part');\n"
    "      else objAnnounce(objFailed ? 'OBJECTIVE FAILED' : 'OBJECTIVE COMPLETE',\n"
    "                       prev || 'OBJECTIVE', objFailed ? 'fail' : 'done');\n"
    "    }\n"
    "  }\n"
    "  if(objDoneT>0 && !paused) objDoneT--;\n"
    "  const cur = currentObjective();\n"
    "  if(cur){ if(cur.txt!==objPinned){ objPinned = cur.txt; objAnnounce('NEW OBJECTIVE', cur.txt, 'new'); } }\n"
    "  else objPinned = '';\n"
    "  // A card waits for the jump in to finish: nobody reads it in the dark.\n"
    "  if(objCard && arriveT>0) objCard.t0 = fc;\n"
    "  // The line: the objective, or failing that what is left to do.\n"
    "  let pin = cur;\n"
    "  if(!pin){\n"
    "    const bossInQ = spawnQ.some(function(s){ return s.type==='boss_ntf'||s.type==='boss_sh'; });\n"
    "    if(bossInQ || bossAlive) pin = {txt:'BOSS FIGHT', col:'#ff5533'};\n"
    "    else if(!spawnQ.length && liveThreatCount()>0) pin = {txt:'CLEAR THE FIELD', col:'#ff5533'};\n"
    "  }\n"
    "  // While the card is announcing this very objective, the line waits.\n"
    "  const cardAge = objCard ? fc - objCard.t0 : 1e9;\n"
    "  const cardUp = objCard && cardAge < OBJ_CARD_TIME - OBJ_CARD_FADE;\n"
    "  if(pin && arriveT<=0 && !(cardUp && objCard.tone==='new' && objCard.txt===pin.txt)) drawObjLine(pin);\n"
    "  drawObjCard();\n"
    "}\n"
    "// The line under the bar: a plate from the kit, a small wedge in the\n"
    "// objective's colour, the words.\n"
    "function drawObjLine(pin){\n"
    "  ctx.save();\n"
    "  ctx.font = thValue(12, true);\n"
    "  const txt = thFit(pin.txt, 380);\n"
    "  const tw = ctx.measureText(txt).width;\n"
    "  const px = 8, py = HUD_H+6, pw = Math.round(tw+32), ph = 20;\n"
    "  thPlate(px, py, pw, ph, thRGBA('panelBack', 0.66), 5);\n"
    "  ctx.fillStyle = pin.col;\n"
    "  ctx.beginPath(); ctx.moveTo(px+10, py+6); ctx.lineTo(px+16, py+10); ctx.lineTo(px+10, py+14);\n"
    "  ctx.closePath(); ctx.fill();\n"
    "  ctx.fillStyle = TH('textBright'); ctx.textAlign = 'left'; ctx.textBaseline = 'middle';\n"
    "  ctx.fillText(txt, px+23, py+ph/2+1);\n"
    "  ctx.restore();\n"
    "  ctx.textAlign='left'; ctx.textBaseline='top';\n"
    "}\n"
    "// The card: comes down a few points as it fades in, stands, fades out.\n"
    "// Below any jump-out countdowns, so the two never overlap.\n"
    "function drawObjCard(){\n"
    "  if(!objCard) return;\n"
    "  const age = fc - objCard.t0;\n"
    "  if(age >= OBJ_CARD_TIME){ objCard = null; return; }\n"
    "  let a = 1;\n"
    "  if(age < OBJ_CARD_FADE) a = age/OBJ_CARD_FADE;\n"
    "  else if(age > OBJ_CARD_TIME-OBJ_CARD_FADE) a = (OBJ_CARD_TIME-age)/OBJ_CARD_FADE;\n"
    "  if(arriveT>0) return;\n"
    "  const col = objCard.tone==='new' ? TH('accentWarm') : OBJ_TONE[objCard.tone];\n"
    "  ctx.save();\n"
    "  ctx.font = thValue(16, true);\n"
    "  const maxW = W-160;\n"
    "  const txt = thFit(objCard.txt, maxW-40);\n"
    "  const cw = Math.round(Math.max(280, Math.min(maxW, ctx.measureText(txt).width+56)));\n"
    "  const ch = 54;\n"
    "  const rows = Math.min(FLEE_ROWS, fleeingEnemies().length);\n"
    "  const cx = ((W-cw)/2)|0;\n"
    "  const cy = (HUD_H + 12 + rows*26 - (1-a)*10)|0;\n"
    "  ctx.globalAlpha = a;\n"
    "  thPlate(cx, cy, cw, ch, thRGBA('panelBack', 0.80), 8);\n"
    "  thGlowPath(cx, cy, cw, ch, 8, 0.8);\n"
    "  ctx.textAlign='center'; ctx.textBaseline='middle';\n"
    "  ctx.fillStyle = col; ctx.font = thLabel(10);\n"
    "  ctx.fillText(objCard.head, W/2, cy+15);\n"
    "  // A short rule in the card's colour under the heading.\n"
    "  ctx.fillRect(W/2-22, cy+23, 44, 2);\n"
    "  ctx.fillStyle = TH('textBright'); ctx.font = thValue(16, true);\n"
    "  ctx.fillText(txt, W/2, cy+38);\n"
    "  ctx.restore();\n"
    "  ctx.textAlign='left'; ctx.textBaseline='top';\n"
    "}\n"
    "\n",
    "objectives: card and line")

# ── The jump-out countdown in the same kit ─────────────────────────────
ui = replace_once(
    ui,
    "  ctx.save();\n"
    "  ctx.font='bold 12px Courier New';\n"
    "  ctx.textAlign='center'; ctx.textBaseline='top';\n"
    "  let row=0;\n"
    "  for(const flr of list){\n",
    "  ctx.save();\n"
    "  ctx.font=thValue(12, true);\n"
    "  ctx.textAlign='center'; ctx.textBaseline='middle';\n"
    "  let row=0;\n"
    "  for(const flr of list){\n",
    "flee: font")
ui = replace_once(
    ui,
    "    const tw=ctx.measureText(txt).width;\n"
    "    const bx=((W-tw)/2-10)|0;\n"
    "    ctx.globalAlpha=0.72;\n"
    "    ctx.fillStyle='#000';\n"
    "    ctx.fillRect(bx, by, (tw+20)|0, 20);\n"
    "    ctx.globalAlpha=1;\n"
    "    ctx.strokeStyle=urgent?'#ff5500':'#ffbb22'; ctx.lineWidth=1;\n"
    "    ctx.strokeRect(bx, by, (tw+20)|0, 20);\n"
    "    ctx.fillStyle=urgent?'#ff7733':'#ffcc44';\n"
    "    ctx.fillText(txt, W/2, by+5);\n",
    "    const tw=ctx.measureText(txt).width;\n"
    "    const bw=(tw+28)|0, bx=((W-bw)/2)|0;\n"
    "    thPlate(bx, by, bw, 20, thRGBA('panelBack', 0.72), 5);\n"
    "    ctx.fillStyle=urgent?'#ff7733':'#ffcc44';\n"
    "    ctx.fillText(txt, W/2, by+11);\n",
    "flee: plate")

# ── FPS and OBJ read-outs ──────────────────────────────────────────────
ui = replace_between(
    ui,
    "function drawFps(){\n",
    "// No need to remember the previous pause any more: closing the panel\n",
    "// A small plate from the kit, right aligned under the bar.\n"
    "function drawReadout(txt, row, col){\n"
    "  ctx.save();\n"
    "  ctx.font = thValue(11, true);\n"
    "  const tw = ctx.measureText(txt).width;\n"
    "  const pw = Math.round(tw+16), ph = 16;\n"
    "  const px = W-6-pw, py = HUD_H+6+row*20;\n"
    "  thPlate(px, py, pw, ph, thRGBA('panelBack', 0.66), 4);\n"
    "  ctx.fillStyle = col; ctx.textAlign='left'; ctx.textBaseline='middle';\n"
    "  ctx.fillText(txt, px+8, py+ph/2+1);\n"
    "  ctx.restore();\n"
    "  ctx.textAlign='left'; ctx.textBaseline='top';\n"
    "}\n"
    "function drawFps(){\n"
    "  if(!showFps) return;\n"
    "  drawReadout('FPS '+(fpsVal||'--'), 0, fpsVal && fpsVal<40 ? '#ff9900' : TH('textBright'));\n"
    "}\n"
    "// Object counter. Three numbers instead of a sum: a sum says that it\n"
    "// grows, three say which list grows.\n"
    "let showObj=false;\n"
    "function drawObjCount(){\n"
    "  if(!showObj) return;\n"
    "  const ships = enemies.length + allies.length;\n"
    "  const shots = pBullets.length + eBullets.length;\n"
    "  const junk  = debris.length + PARTS.length + ITEMS.length;\n"
    "  drawReadout('OBJ '+ships+'/'+shots+'/'+junk, showFps ? 1 : 0, TH('text'));\n"
    "}\n"
    "\n",
    "fps and obj")

# ── Pause screen ───────────────────────────────────────────────────────
ui = replace_once(
    ui,
    "  if(paused && !settingsOpen){\n"
    "    ctx.fillStyle='rgba(0,0,0,0.55)';ctx.fillRect(0,0,W,H);\n"
    "    ctx.fillStyle='#ffffff';ctx.font='bold 32px Courier New';\n"
    "    ctx.textAlign='center';ctx.textBaseline='middle';\n"
    "    ctx.fillText('PAUSED',W/2,H/2-20);\n"
    "    ctx.font='14px Courier New';ctx.fillStyle='#aaaaaa';\n"
    "    ctx.fillText('Press P or tap to resume',W/2,H/2+20);\n"
    "    ctx.textAlign='left';ctx.textBaseline='top';\n"
    "  }\n",
    "  if(paused && !settingsOpen) drawPaused();\n",
    "pause: call")

ui = replace_once(
    ui,
    "// The countdown used to live in the HUD bar, in the same strip as the\n",
    "// The pause notice: a panel from the kit over a dimmed field.\n"
    "function drawPaused(){\n"
    "  ctx.fillStyle='rgba(0,0,8,0.50)'; ctx.fillRect(0,0,W,H);\n"
    "  const pw=300, ph=92, px=((W-pw)/2)|0, py=((H-ph)/2)|0;\n"
    "  thPlate(px, py, pw, ph, thRGBA('panelBack', 0.90), 12);\n"
    "  thGlowPath(px, py, pw, ph, 12, 0.9);\n"
    "  ctx.textAlign='center'; ctx.textBaseline='middle';\n"
    "  ctx.save();\n"
    "  ctx.shadowColor='rgba('+TH('glow')+',0.55)'; ctx.shadowBlur=ecoBlur(18);\n"
    "  ctx.fillStyle=TH('textBright'); ctx.font=thLabel(28);\n"
    "  ctx.fillText('PAUSED', W/2, py+36);\n"
    "  ctx.restore();\n"
    "  ctx.fillStyle=TH('textDim'); ctx.font=thValue(12, false);\n"
    "  ctx.fillText('Press P or tap to resume', W/2, py+68);\n"
    "  ctx.textAlign='left'; ctx.textBaseline='top';\n"
    "}\n"
    "\n"
    "// The countdown used to live in the HUD bar, in the same strip as the\n",
    "pause: panel")

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
    'docksim.js': (
        'Ly8gRG9ja2luZyBzaW11bGF0aW9uLiBQdWxscyB0aGUgUkVBTCBmdW5jdGlvbnMgb3V0IG9mIHRo'
        'ZSBsb2dpYyBmaWxlIGFuZAovLyBydW5zIHRoZW0gYWdhaW5zdCBhIG1pbmltYWwgd29ybGQuIE9u'
        'bHkgdGhlIHNoaXAgb2JqZWN0cywgdGhlIGRlYXRoIG9mIGFuCi8vIGFsbHkgYW5kIHRoZSB0aWNr'
        'IG9yZGVyIGFyZSBzdGFuZC1pbnM7IGV2ZXJ5IGRvY2tpbmcgcnVsZSBpcyB0aGUgZ2FtZSdzLgov'
        'LyBVc2FnZTogbm9kZSBkb2Nrc2ltLmpzIGhscF9zaG9vdGVyX3YxMDJfbG9naWMuaHRtbCBobHBf'
        'bW91bnRzX2ZpbmFsLmpzb24KY29uc3QgZnMgPSByZXF1aXJlKCdmcycpOwpjb25zdCBodG1sID0g'
        'ZnMucmVhZEZpbGVTeW5jKHByb2Nlc3MuYXJndlsyXSB8fCAnaGxwX3Nob290ZXJfdjEwMl9sb2dp'
        'Yy5odG1sJywgJ3V0ZjgnKTsKY29uc3Qgc3JjID0gaHRtbC5tYXRjaCgvPHNjcmlwdFtePl0qPihb'
        'XHNcU10qKTxcL3NjcmlwdD4vKVsxXTsKY29uc3QgTU9VTlRTID0gSlNPTi5wYXJzZShmcy5yZWFk'
        'RmlsZVN5bmMocHJvY2Vzcy5hcmd2WzNdIHx8ICdobHBfbW91bnRzX2ZpbmFsLmpzb24nLCAndXRm'
        'OCcpKTsKCi8vIEJyYWNlIG1hdGNoaW5nIHRoYXQgc2tpcHMgc3RyaW5ncyBhbmQgY29tbWVudHMu'
        'CmZ1bmN0aW9uIGJsb2NrKGZyb20pewogIGxldCBpID0gc3JjLmluZGV4T2YoJ3snLCBmcm9tKSwg'
        'ZCA9IDA7CiAgZm9yKDsgaSA8IHNyYy5sZW5ndGg7IGkrKyl7CiAgICBjb25zdCBjaCA9IHNyY1tp'
        'XSwgbnggPSBzcmNbaSsxXTsKICAgIGlmKGNoID09PSAnLycgJiYgbnggPT09ICcvJyl7IGkgPSBz'
        'cmMuaW5kZXhPZignXG4nLCBpKTsgY29udGludWU7IH0KICAgIGlmKGNoID09PSAnLycgJiYgbngg'
        'PT09ICcqJyl7IGkgPSBzcmMuaW5kZXhPZignKi8nLCBpKSArIDE7IGNvbnRpbnVlOyB9CiAgICBp'
        'ZihjaCA9PT0gJyInIHx8IGNoID09PSAiJyIgfHwgY2ggPT09ICdgJyl7CiAgICAgIGNvbnN0IHEg'
        'PSBjaDsgaSsrOwogICAgICB3aGlsZShzcmNbaV0gIT09IHEpeyBpZihzcmNbaV0gPT09ICdcXCcp'
        'IGkrKzsgaSsrOyB9CiAgICAgIGNvbnRpbnVlOwogICAgfQogICAgaWYoY2ggPT09ICd7JykgZCsr'
        'OwogICAgZWxzZSBpZihjaCA9PT0gJ30nKXsgZC0tOyBpZihkID09PSAwKSByZXR1cm4gaSArIDE7'
        'IH0KICB9CiAgdGhyb3cgbmV3IEVycm9yKCd1bmJhbGFuY2VkIGF0ICcgKyBmcm9tKTsKfQpmdW5j'
        'dGlvbiBmbihuYW1lKXsKICBjb25zdCBhdCA9IHNyYy5pbmRleE9mKCdmdW5jdGlvbiAnICsgbmFt'
        'ZSArICcoJyk7CiAgaWYoYXQgPCAwKSB0aHJvdyBuZXcgRXJyb3IoJ21pc3NpbmcgZnVuY3Rpb24g'
        'JyArIG5hbWUpOwogIHJldHVybiBzcmMuc2xpY2UoYXQsIGJsb2NrKGF0KSk7Cn0KZnVuY3Rpb24g'
        'Y29uc3RPYmoobmFtZSl7CiAgY29uc3QgYXQgPSBzcmMuaW5kZXhPZignY29uc3QgJyArIG5hbWUg'
        'KyAnID0nKTsKICByZXR1cm4gc3JjLnNsaWNlKGF0LCBibG9jayhhdCkpICsgJzsnOwp9Cgpjb25z'
        'dCBOQU1FUyA9IFsnZG9ja1BvaW50JywnZG9ja09mZnNldCcsJ3VuaXRBbGl2ZScsJ2lkUGVuZGlu'
        'ZycsJ2NhcmdvTG9zdCcsJ2NsYWltQ2FyZ28nLAogICdsZWF2ZUVtcHR5JywnY2FyZ29TdGlsbFdh'
        'bnRlZCcsJ2NhcnJ5Q2FyZ28nLCdkcm9wQ2FyZ28nLCd0aWNrQ2FycnknLCd0aWNrRG9ja2luZycs'
        'CiAgJ3RpY2tDcm9zc0d1YXJkcycsJ2tpbGxFbmVteScsJ2J5SWQnLCdldlNlZW4nLCdtb3VudHNG'
        'b3InLCdodWxsQ2xhc3MnLAogICdsaXZlVGhyZWF0Q291bnQnLCdzY3JpcHRVbml0c1Jlc29sdmVk'
        'J107Cgpjb25zdCB3b3JsZCA9IGAKbGV0IGVuZW1pZXM9W10sIGFsbGllcz1bXSwgU1VCX01TR1M9'
        'W10sIEVWX0RPQ0s9e30sIEVWX1NFRU49e30sIEVWX0hFTEQ9e30sIEVWX0xFRlQ9e30sIHNwYXdu'
        'UT1bXTsKbGV0IHByb3RTYXZlZD0wLCBwcm90TG9zdD0wLCBndWFyZExvc3Q9ZmFsc2UsIGd1YXJk'
        'R29uZT1mYWxzZSwgY3Jvc3NEb25lPTAsIGNyb3NzVG90YWw9MDsKbGV0IHNjb3JlPTAsIGJvc3NB'
        'bGl2ZT1mYWxzZSwgYm9zc1NsYWluPWZhbHNlLCBleHBsPTA7CmNvbnN0IFc9ODAwLCBIPTUwMCwg'
        'SFVEX0g9NDQsIERPQ0tfU1BEPTAuNTUsIERPQ0tfTkVBUj0yMjsKY29uc3QgTU9VTlRTID0gJHtK'
        'U09OLnN0cmluZ2lmeShNT1VOVFMpfTsKY29uc3QgSU1HUyA9IHsgZnJiYXN0Ont3aWR0aDo2MCxo'
        'ZWlnaHQ6MjZ9LCBmY3ZjMzp7d2lkdGg6MzAsaGVpZ2h0OjIyfSwKICB0cmlzaXM6e3dpZHRoOjYw'
        'LGhlaWdodDoyNH0sIGRlaGF0c2hlcHN1dDp7d2lkdGg6MzkxLGhlaWdodDoxNTB9IH07CmZ1bmN0'
        'aW9uIHN0YXRLaWxsKCl7fSBmdW5jdGlvbiBtYXliZURyb3BUaWNrZXQoKXt9CmZ1bmN0aW9uIHRy'
        'aWdnZXJFeHBsKCl7IGV4cGwrKzsgfQoke05BTUVTLm1hcChmbikuam9pbignXG4nKX0KJHtjb25z'
        'dE9iaignU0NSSVBUX1dBVkVTJyl9CmA7CmNvbnN0IFRJQ0tfSFogPSAxMDA7CmNvbnN0IGFwaSA9'
        'IG5ldyBGdW5jdGlvbignVElDS19IWicsIHdvcmxkICsgYApyZXR1cm4geyBnZXQgZW5lbWllcygp'
        'e3JldHVybiBlbmVtaWVzO30sIHNldCBlbmVtaWVzKHYpe2VuZW1pZXM9djt9LAogIGdldCBhbGxp'
        'ZXMoKXtyZXR1cm4gYWxsaWVzO30sIHNldCBhbGxpZXModil7YWxsaWVzPXY7fSwKICBnZXQgcHJv'
        'dFNhdmVkKCl7cmV0dXJuIHByb3RTYXZlZDt9LCBnZXQgcHJvdExvc3QoKXtyZXR1cm4gcHJvdExv'
        'c3Q7fSwKICBnZXQgZXhwbCgpe3JldHVybiBleHBsO30sIFNVQl9NU0dTLCBFVl9TRUVOLCBFVl9I'
        'RUxELCBzcGF3blEsCiAgcmVzZXQoKXsgZW5lbWllcz1bXTsgYWxsaWVzPVtdOyBTVUJfTVNHUy5s'
        'ZW5ndGg9MDsgZm9yKGNvbnN0IGsgaW4gRVZfRE9DSykgZGVsZXRlIEVWX0RPQ0tba107CiAgICBm'
        'b3IoY29uc3QgayBpbiBFVl9TRUVOKSBkZWxldGUgRVZfU0VFTltrXTsgZm9yKGNvbnN0IGsgaW4g'
        'RVZfSEVMRCkgZGVsZXRlIEVWX0hFTERba107CiAgICBzcGF3blEubGVuZ3RoPTA7IHByb3RTYXZl'
        'ZD0wOyBwcm90TG9zdD0wOyBndWFyZExvc3Q9ZmFsc2U7IGV4cGw9MDsgfSwKICB0aWNrRG9ja2lu'
        'ZywgdGlja0Nyb3NzR3VhcmRzLCB0aWNrQ2FycnksIGtpbGxFbmVteSwgZG9ja1BvaW50LCBsaXZl'
        'VGhyZWF0Q291bnQsCiAgc2NyaXB0VW5pdHNSZXNvbHZlZCwgU0NSSVBUX1dBVkVTIH07YCkoVElD'
        'S19IWik7CgovLyDilIDilIAgU3RhbmQtaW5zIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgApsZXQgdWlkYyA9IDA7CmZ1bmN0aW9uIGZyZWlnaHRlcih1aWQsIHgsIHksIGRvY2tUbywg'
        'c2lkZSl7CiAgY29uc3QgbyA9IHt1aWQsIHR5cGU6J2ZyZWlnaHRlcicsIGltZzonZnJiYXN0Jywg'
        'eCwgeSwgc2M6MSwgZmxpcDpmYWxzZSwgd2FycDowLCBkZWFkOmZhbHNlLAogICAgZ3VhcmQ6dHJ1'
        'ZSwgZG9ja1RvLCBjcm9zc0FmdGVyOjAuMzgsIGhwOjEwMCwgbWF4SHA6MTAwLCBfbjorK3VpZGN9'
        'OwogIGFwaS5FVl9TRUVOW3VpZF0gPSB0cnVlOwogIChzaWRlID09PSAnZW5lbXknID8gYXBpLmVu'
        'ZW1pZXMgOiBhcGkuYWxsaWVzKS5wdXNoKG8pOyByZXR1cm4gbzsKfQpmdW5jdGlvbiBjb250YWlu'
        'ZXIodWlkLCB4LCB5LCBzaWRlKXsKICBjb25zdCBvID0ge3VpZCwgdHlwZTonY29udGFpbmVyJywg'
        'aW1nOidmY3ZjMycsIHgsIHksIHNjOjEsIGZsaXA6c2lkZT09PSdlbmVteScsIHdhcnA6MCwKICAg'
        'IGRlYWQ6ZmFsc2UsIGd1YXJkOnNpZGUhPT0nZW5lbXknLCBwaWNrdXA6dHJ1ZSwgaHA6NjAsIG1h'
        'eEhwOjYwLCBwdHM6NDAsIF9uOisrdWlkY307CiAgYXBpLkVWX1NFRU5bdWlkXSA9IHRydWU7CiAg'
        'KHNpZGUgPT09ICdlbmVteScgPyBhcGkuZW5lbWllcyA6IGFwaS5hbGxpZXMpLnB1c2gobyk7IHJl'
        'dHVybiBvOwp9Ci8vIE1pcnJvcnMgdGhlIGRlYXRoIGJyYW5jaCBvZiB1cGRhdGVBbGxpZXMoKTog'
        'c3BsaWNlLCBhbmQgY291bnQgYSBndWFyZC4KZnVuY3Rpb24gYWxseURpZXMoYSl7CiAgYS5kZWFk'
        'ID0gdHJ1ZTsgYS5ocCA9IDA7CiAgY29uc3QgaSA9IGFwaS5hbGxpZXMuaW5kZXhPZihhKTsgaWYo'
        'aSA+PSAwKSBhcGkuYWxsaWVzLnNwbGljZShpLCAxKTsKICBpZihhLmd1YXJkKXsgLyogdXBkYXRl'
        'QWxsaWVzOiBwcm90TG9zdCsrICovIGFwaS5fbG9zdEJ5R3VhcmQgPSAoYXBpLl9sb3N0QnlHdWFy'
        'ZHx8MCkgKyAxOyB9Cn0KLy8gdGljayBvcmRlciBhcyBpbiB1cGRhdGUoKTogZG9ja2luZyAuLi4g'
        'Y3Jvc3NpbmcgLi4uIG1vdmVtZW50LCB0aGVuIGNhcnJ5CmxldCBzaGFyZWQgPSAwLCBsYWcgPSAw'
        'OwpmdW5jdGlvbiBzdGVwKCl7CiAgYXBpLnRpY2tEb2NraW5nKCk7CiAgYXBpLnRpY2tDcm9zc0d1'
        'YXJkcygpOwogIGFwaS50aWNrQ2FycnkoKTsKICAvLyBubyB0d28gZnJlaWdodGVycyBvbiBvbmUg'
        'Y29udGFpbmVyLCBldmVyCiAgY29uc3Qgc2VlbiA9IG5ldyBNYXAoKTsKICBmb3IoY29uc3QgZiBv'
        'ZiBhcGkuZW5lbWllcy5jb25jYXQoYXBpLmFsbGllcykpewogICAgY29uc3QgYyA9IGYuZG9ja2Vk'
        'VG8gfHwgZi5kb2NrUmVzOwogICAgaWYoIWMpIGNvbnRpbnVlOwogICAgaWYoc2Vlbi5oYXMoYykp'
        'IHNoYXJlZCsrOwogICAgc2Vlbi5zZXQoYywgZik7CiAgfQogIC8vIGNhcnJpZWQgY2FyZ286IGJv'
        'dGggZG9jayBwb2ludHMgbWVldCwgd2l0aCBubyBsYWcgYWZ0ZXIgbW92aW5nCiAgZm9yKGNvbnN0'
        'IGYgb2YgYXBpLmFsbGllcykgaWYoZi5kb2NrZWRUbyAmJiAhZi5kb2NrZWRUby5kZWFkKXsKICAg'
        'IGNvbnN0IGEgPSBhcGkuZG9ja1BvaW50KGYpLCBiID0gYXBpLmRvY2tQb2ludChmLmRvY2tlZFRv'
        'KTsKICAgIGxhZyA9IE1hdGgubWF4KGxhZywgTWF0aC5oeXBvdChhLngtYi54LCBhLnktYi55KSk7'
        'CiAgfQp9CmZ1bmN0aW9uIHJ1bihuLCBob29rKXsgZm9yKGxldCB0ID0gMDsgdCA8IG47IHQrKyl7'
        'IGlmKGhvb2spIGhvb2sodCk7IHN0ZXAoKTsgfSB9CmNvbnN0IGxvc3QgPSAoKSA9PiBhcGkucHJv'
        'dExvc3QgKyAoYXBpLl9sb3N0QnlHdWFyZHx8MCk7CmxldCBwYXNzID0gMCwgZmFpbCA9IDA7CmZ1'
        'bmN0aW9uIGNoZWNrKG5hbWUsIG9rLCBpbmZvKXsKICBjb25zb2xlLmxvZygob2sgPyAnICBvayAg'
        'ICAnIDogJyAgRkFJTCAgJykgKyBuYW1lICsgKGluZm8gPyAnICAgKCcgKyBpbmZvICsgJyknIDog'
        'JycpKTsKICBvayA/IHBhc3MrKyA6IGZhaWwrKzsKfQpmdW5jdGlvbiBiZWdpbih0aXRsZSl7IGFw'
        'aS5yZXNldCgpOyBhcGkuX2xvc3RCeUd1YXJkID0gMDsgc2hhcmVkID0gMDsgbGFnID0gMDsgY29u'
        'c29sZS5sb2coJ1xuJyArIHRpdGxlKTsgfQpjb25zdCBtc2dzID0gdCA9PiBhcGkuU1VCX01TR1Mu'
        'ZmlsdGVyKG0gPT4gbS50eHQgPT09IHQpLmxlbmd0aDsKCi8vIOKUgOKUgCAxLiBFcXVhbCBudW1i'
        'ZXJzIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgApiZWdpbignMSAgdHdvIGZyZWlnaHRlcnMsIHR3byBjb250YWluZXJz'
        'Jyk7CmNvbnRhaW5lcignQzEnLCAxNTAsIDE4MCk7IGNvbnRhaW5lcignQzEnLCAxNzAsIDMyMCk7'
        'CmZyZWlnaHRlcignRjEnLCAtNDAsIDIwMCwgJ0MxJyk7IGZyZWlnaHRlcignRjEnLCAtNDAsIDMw'
        'MCwgJ0MxJyk7CnJ1big2MDAwKTsKY2hlY2soJ2JvdGggZGVsaXZlcmVkJywgYXBpLnByb3RTYXZl'
        'ZCA9PT0gMiAmJiBtc2dzKCdERUxJVkVSRUQnKSA9PT0gMiwgJ3NhdmVkICcgKyBhcGkucHJvdFNh'
        'dmVkKTsKY2hlY2soJ25vdGhpbmcgbG9zdCcsIGxvc3QoKSA9PT0gMCk7CmNoZWNrKCduZXZlciB0'
        'd28gb24gb25lIGNvbnRhaW5lcicsIHNoYXJlZCA9PT0gMCk7CmNoZWNrKCdjYXJnbyBzaXRzIGV4'
        'YWN0bHkgb24gdGhlIGRvY2sgcG9pbnQnLCBsYWcgPCAwLjAxLCAnbWF4IGdhcCAnICsgbGFnLnRv'
        'Rml4ZWQoNCkgKyAnIHB4Jyk7CgovLyDilIDilIAgMi4gTW9yZSBmcmVpZ2h0ZXJzIHRoYW4gY29u'
        'dGFpbmVycyDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIAKYmVnaW4oJzIgIHRocmVlIGZyZWlnaHRlcnMsIHR3byBj'
        'b250YWluZXJzJyk7CmNvbnRhaW5lcignQzEnLCAxNTAsIDE4MCk7IGNvbnRhaW5lcignQzEnLCAx'
        'NzAsIDMyMCk7CmZyZWlnaHRlcignRjEnLCAtNDAsIDIwMCwgJ0MxJyk7IGZyZWlnaHRlcignRjEn'
        'LCAtNjAsIDI1MCwgJ0MxJyk7IGZyZWlnaHRlcignRjEnLCAtODAsIDMwMCwgJ0MxJyk7CnJ1big2'
        'MDAwKTsKY2hlY2soJ3R3byBkZWxpdmVyZWQsIG9uZSBsZWZ0IGVtcHR5JywgYXBpLnByb3RTYXZl'
        'ZCA9PT0gMiAmJiBtc2dzKCdMRUZUIEVNUFRZJykgPT09IDEsCiAgICAgICdzYXZlZCAnICsgYXBp'
        'LnByb3RTYXZlZCArICcsIGVtcHR5ICcgKyBtc2dzKCdMRUZUIEVNUFRZJykpOwpjaGVjaygnbmV2'
        'ZXIgdHdvIG9uIG9uZSBjb250YWluZXInLCBzaGFyZWQgPT09IDApOwpjaGVjaygnd2F2ZSBub3Qg'
        'aGVsZCAobm8gZnJlaWdodGVyIGxlZnQpJywgYXBpLmFsbGllcy5sZW5ndGggPT09IDAsIGFwaS5h'
        'bGxpZXMubGVuZ3RoICsgJyBsZWZ0Jyk7CgovLyDilIDilIAgMy4gTW9yZSBjb250YWluZXJzIHRo'
        'YW4gZnJlaWdodGVycyDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKYmVnaW4oJzMgIHR3byBmcmVpZ2h0ZXJzLCB0'
        'aHJlZSBjb250YWluZXJzIChyYXcsIHdpdGhvdXQgdGhlIGNvdW50IGZpeCknKTsKY29udGFpbmVy'
        'KCdDMScsIDE1MCwgMTUwKTsgY29udGFpbmVyKCdDMScsIDE3MCwgMjUwKTsgY29udGFpbmVyKCdD'
        'MScsIDE5MCwgMzUwKTsKZnJlaWdodGVyKCdGMScsIC00MCwgMjAwLCAnQzEnKTsgZnJlaWdodGVy'
        'KCdGMScsIC00MCwgMzAwLCAnQzEnKTsKcnVuKDYwMDApOwpjaGVjaygndHdvIGRlbGl2ZXJlZCcs'
        'IGFwaS5wcm90U2F2ZWQgPT09IDIpOwpjaGVjaygndGhpcmQgb25lIGxlZnQgYmVoaW5kIGFuZCBj'
        'b3VudGVkIG9uY2UnLCBtc2dzKCdDQVJHTyBMRUZUIEJFSElORCcpID09PSAxICYmIGxvc3QoKSA9'
        'PT0gMSk7CmNoZWNrKCdsZWZ0LWJlaGluZCBjb250YWluZXIgaXMgc2NlbmVyeSwgbm8gbG9uZ2Vy'
        'IGEgZ3VhcmQnLAogICAgICBhcGkuYWxsaWVzLmV2ZXJ5KGMgPT4gYy5zY2VuZXJ5ICYmICFjLmd1'
        'YXJkKSk7CmNoZWNrKCdyZXN1bHQgd291bGQgcmVhZCBQQVJUSUFMIDIvMycsIGFwaS5wcm90U2F2'
        'ZWQgPT09IDIgJiYgbG9zdCgpID09PSAxKTsKCi8vIOKUgOKUgCA0LiBDYXJyaWVyIGRpZXMgd2l0'
        'aCBjYXJnbyDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKYmVnaW4oJzQg'
        'IGNhcnJpZXIgZGVzdHJveWVkIHdoaWxlIGNhcnJ5aW5nJyk7CmNvbnN0IGM0ID0gY29udGFpbmVy'
        'KCdDMScsIDE1MCwgMjAwKTsgY29uc3QgZjQgPSBmcmVpZ2h0ZXIoJ0YxJywgLTQwLCAyNTAsICdD'
        'MScpOwpydW4oNjAwMCwgdCA9PiB7IGlmKGY0LmRvY2tlZFRvICYmIGY0LnggPiA0MDAgJiYgIWY0'
        'LmRlYWQpIGFsbHlEaWVzKGY0KTsgfSk7CmNoZWNrKCdjYXJnbyBkZXN0cm95ZWQgd2l0aCBpdCcs'
        'IGM0LmRlYWQgJiYgYXBpLmFsbGllcy5pbmRleE9mKGM0KSA8IDAgJiYgYXBpLmV4cGwgPT09IDEp'
        'OwpjaGVjaygnY291bnRlZCBvbmNlICh0aGUgZnJlaWdodGVyKSwgbm90IHR3aWNlJywgbG9zdCgp'
        'ID09PSAxLCAnbG9zdCAnICsgbG9zdCgpKTsKY2hlY2soJ25vdCByZXBvcnRlZCBhcyBsZWZ0IGJl'
        'aGluZCcsIG1zZ3MoJ0NBUkdPIExFRlQgQkVISU5EJykgPT09IDApOwoKLy8g4pSA4pSAIDUuIENh'
        'cmdvIGRpZXMgYmVmb3JlIGRvY2tpbmcgKGFsbGllZCBjb250YWluZXIpIOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgApiZWdpbignNSAgYWxsaWVkIGNvbnRhaW5lciBkZXN0cm95ZWQg'
        'YmVmb3JlIGRvY2tpbmcnKTsKY29uc3QgYzUgPSBjb250YWluZXIoJ0MxJywgMzAwLCAxODApOyBj'
        'b250YWluZXIoJ0MxJywgMzIwLCAzMjApOwpjb25zdCBmNSA9IGZyZWlnaHRlcignRjEnLCAtNDAs'
        'IDIwMCwgJ0MxJyk7IGZyZWlnaHRlcignRjEnLCAtNDAsIDMwMCwgJ0MxJyk7CnJ1big2MDAwLCB0'
        'ID0+IHsgaWYodCA9PT0gMTAwKSBhbGx5RGllcyhmNS5kb2NrUmVzKTsgfSk7CmNoZWNrKCdpdHMg'
        'ZnJlaWdodGVyIGxlYXZlcyBlbXB0eSwgZG9lcyBub3QgdGFrZSB0aGUgb3RoZXInLCBtc2dzKCdM'
        'RUZUIEVNUFRZJykgPT09IDEgJiYgYXBpLnByb3RTYXZlZCA9PT0gMSwKICAgICAgJ3NhdmVkICcg'
        'KyBhcGkucHJvdFNhdmVkKTsKY2hlY2soJ25ldmVyIHR3byBvbiBvbmUgY29udGFpbmVyJywgc2hh'
        'cmVkID09PSAwKTsKY2hlY2soJ2NvdW50ZWQgb25jZScsIGxvc3QoKSA9PT0gMSwgJ2xvc3QgJyAr'
        'IGxvc3QoKSk7CgovLyDilIDilIAgNWIuIEVuZW15IGNvbnRhaW5lciBzaG90IGJ5IHRoZSBwbGF5'
        'ZXIgKE0wMjMpIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgApiZWdpbign'
        'NWIgc2Nhbm5lZCBlbmVteSBjb250YWluZXIgc2hvdCBiZWZvcmUgcGlja3VwJyk7CmNvbnN0IGM1'
        'YiA9IGNvbnRhaW5lcignQzEnLCAzMDAsIDIwMCwgJ2VuZW15Jyk7IGNvbnRhaW5lcignQzEnLCAz'
        'MjAsIDMzMCwgJ2VuZW15Jyk7CmZyZWlnaHRlcignRjEnLCAtNDAsIDIwMCwgJ0MxJyk7IGZyZWln'
        'aHRlcignRjEnLCAtNDAsIDMwMCwgJ0MxJyk7CnJ1big2MDAwLCB0ID0+IHsgaWYodCA9PT0gMTAw'
        'KSBhcGkua2lsbEVuZW15KGM1YiwgbnVsbCwgdHJ1ZSwgZmFsc2UpOyB9KTsKY2hlY2soJ29uZSBk'
        'ZWxpdmVyZWQsIG9uZSBlbXB0eScsIGFwaS5wcm90U2F2ZWQgPT09IDEgJiYgbXNncygnTEVGVCBF'
        'TVBUWScpID09PSAxKTsKY2hlY2soJ2NvdW50ZWQgb25jZScsIGxvc3QoKSA9PT0gMSwgJ2xvc3Qg'
        'JyArIGxvc3QoKSk7CmNoZWNrKCdubyBlbmVteSBjb250YWluZXIgaG9sZHMgdGhlIHdhdmUnLCBh'
        'cGkubGl2ZVRocmVhdENvdW50KCkgPT09IDAsICd0aHJlYXRzICcgKyBhcGkubGl2ZVRocmVhdENv'
        'dW50KCkpOwoKLy8g4pSA4pSAIDYuIEZyZWlnaHRlciBkaWVzIG9uIHRoZSB3YXkg4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSACmJlZ2luKCc2ICBmcmVpZ2h0ZXIgZGVzdHJveWVkIGJl'
        'Zm9yZSBkb2NraW5nJyk7CmNvbnRhaW5lcignQzEnLCAzMDAsIDIwMCk7IGNvbnN0IGY2ID0gZnJl'
        'aWdodGVyKCdGMScsIC00MCwgMjUwLCAnQzEnKTsKcnVuKDYwMDAsIHQgPT4geyBpZih0ID09PSAx'
        'MDApIGFsbHlEaWVzKGY2KTsgfSk7CmNoZWNrKCdjb250YWluZXIgcmVsZWFzZWQgYXMgbGVmdCBi'
        'ZWhpbmQnLCBtc2dzKCdDQVJHTyBMRUZUIEJFSElORCcpID09PSAxKTsKY2hlY2soJ2NvdW50ZWQg'
        'b25jZSAodGhlIGZyZWlnaHRlciksIG5vdCB0d2ljZScsIGxvc3QoKSA9PT0gMSwgJ2xvc3QgJyAr'
        'IGxvc3QoKSk7CgovLyDilIDilIAgNy4gRnJlaWdodGVyIGFycml2ZXMgYmVmb3JlIGl0cyBjb250'
        'YWluZXIg4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        'CmJlZ2luKCc3ICBmcmVpZ2h0ZXIgaW4gdGhlIGZpZWxkLCBjb250YWluZXIgc3RpbGwgcXVldWVk'
        'Jyk7CmZyZWlnaHRlcignRjEnLCAtNDAsIDI1MCwgJ0MxJyk7IGFwaS5FVl9TRUVOWydDMSddID0g'
        'dHJ1ZTsKYXBpLnNwYXduUS5wdXNoKHt1aWQ6J0MxJywgdHlwZToncHJvdGVjdCcsIHNwcjonZmN2'
        'YzMnfSk7CnJ1big1MCk7CmNoZWNrKCd3YWl0cyBpbnN0ZWFkIG9mIGxlYXZpbmcgZW1wdHknLCBt'
        'c2dzKCdMRUZUIEVNUFRZJykgPT09IDAgJiYgbXNncygnTk8gQ0FSR08nKSA9PT0gMCk7CgovLyDi'
        'lIDilIAgOC4gRnJlaWdodGVycyBoZWxkIGJhY2sgZm9yIGFuIGV2ZW50IChNMDIzKSDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKYmVnaW4oJzggIGZyZWlnaHRl'
        'cnMgaGVsZCBmb3IgYW4gZXZlbnQnKTsKY29udGFpbmVyKCdDMScsIDMwMCwgMjAwLCAnZW5lbXkn'
        'KTsKYXBpLkVWX0hFTERbJ0YxJ10gPSBbe3VpZDonRjEnLCB0eXBlOidwcm90ZWN0JywgZG9ja1Rv'
        'OidDMSd9XTsKcnVuKDUwKTsKY2hlY2soJ2NvbnRhaW5lciBpcyBub3QgZGVjbGFyZWQgbGVmdCBi'
        'ZWhpbmQnLCBtc2dzKCdDQVJHTyBMRUZUIEJFSElORCcpID09PSAwKTsKCi8vIOKUgOKUgCA5LiBN'
        'MDI3OiB0aHJlZSB0cmFuc3BvcnRzLCBvbmUgZGVzdHJveWVyIOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgApiZWdpbignOSAgdHJhbnNwb3J0cyBk'
        'b2NraW5nIGF0IGEgZGVzdHJveWVyIG9uZSBhZnRlciBhbm90aGVyJyk7CmNvbnN0IGQ5ID0ge3Vp'
        'ZDonQTEnLCB0eXBlOidkZXN0cm95ZXInLCBpbWc6J2RlaGF0c2hlcHN1dCcsIHg6NTIwLCB5OjMw'
        'MCwgc2M6MSwgZmxpcDpmYWxzZSwKICAgICAgICAgICAgd2FycDowLCBkZWFkOmZhbHNlLCBocDoy'
        'MDAwLCBtYXhIcDo2NTAwfTsKYXBpLmFsbGllcy5wdXNoKGQ5KTsgYXBpLkVWX1NFRU5bJ0ExJ10g'
        'PSB0cnVlOwpjb25zdCB0cyA9IFtdOwpsZXQgZG9ja3MgPSAwLCBnYXAgPSAwOwpydW4oOTAwMCwg'
        'dCA9PiB7CiAgaWYodCA9PT0gMCB8fCAodHMubGVuZ3RoICYmIHRzLmxlbmd0aCA8IDMgJiYgdHNb'
        'dHMubGVuZ3RoLTFdLmNyb3NzaW5nICYmIHRzLmxlbmd0aCA9PT0gZG9ja3MpKQogICAgdHMucHVz'
        'aChPYmplY3QuYXNzaWduKGZyZWlnaHRlcignVCcgKyAodHMubGVuZ3RoKzEpLCAtNDAsIDIwMCwg'
        'J0ExJyksIHtpbWc6J3RyaXNpcycsIGd1YXJkOnRydWV9KSk7CiAgY29uc3QgbGFzdCA9IHRzW3Rz'
        'Lmxlbmd0aC0xXTsKICBpZihsYXN0ICYmIGxhc3QuY3Jvc3NpbmcgJiYgIWxhc3QuX2MpeyBsYXN0'
        'Ll9jID0gMTsgZG9ja3MrKzsKICAgIGNvbnN0IGEgPSBhcGkuZG9ja1BvaW50KGxhc3QpLCBiID0g'
        'YXBpLmRvY2tQb2ludChkOSk7IGdhcCA9IE1hdGgubWF4KGdhcCwgTWF0aC5oeXBvdChhLngtYi54'
        'LCBhLnktYi55KSk7IH0KfSk7CmNoZWNrKCdhbGwgdGhyZWUgZG9ja2VkJywgZG9ja3MgPT09IDMs'
        'IGRvY2tzICsgJyBkb2NrZWQnKTsKY2hlY2soJ2RvY2sgcG9pbnRzIG1lZXQnLCBnYXAgPD0gMS4w'
        'MSwgJ2dhcCAnICsgZ2FwLnRvRml4ZWQoMikgKyAnIHB4Jyk7CmNoZWNrKCdub3RoaW5nIHJlcG9y'
        'dGVkIGFzIGNhcmdvJywgbXNncygnTk8gQ0FSR08nKSA9PT0gMCAmJiBtc2dzKCdMRUZUIEVNUFRZ'
        'JykgPT09IDApOwoKLy8g4pSA4pSAIDEwLiBGcmVpZ2h0ZXIgY291bnQgZnJvbSB0aGUgbWlzc2lv'
        'biBkYXRhIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gApiZWdpbignMTAgZnJlaWdodGVyIGNvdW50IGZvbGxvd3MgdGhlIGNvbnRhaW5lcnMnKTsKY29u'
        'c3QgY250ID0gKG0sIGlkKSA9PiBhcGkuc2NyaXB0VW5pdHNSZXNvbHZlZChhcGkuU0NSSVBUX1dB'
        'VkVTW21dKS5maW5kKHUgPT4gdS5pZCA9PT0gaWQpOwpjaGVjaygnTTAwOTogdHdvIGNvbnRhaW5l'
        'cnMsIHR3byBmcmVpZ2h0ZXJzJywgY250KDksICdGMScpLm4gPT09IDIgJiYgY250KDksICdDMScp'
        'LnBpY2t1cCk7CmNoZWNrKCdNMDIzOiB0aHJlZSBjb250YWluZXJzLCBub3cgdGhyZWUgZnJlaWdo'
        'dGVycycsIGNudCgyMywgJ0YxJykubiA9PT0gMyAmJiBjbnQoMjMsICdDMScpLnBpY2t1cCwKICAg'
        'ICAgJ3dhcyAnICsgYXBpLlNDUklQVF9XQVZFU1syM10udS5maW5kKHUgPT4gdS5pZCA9PT0gJ0Yx'
        'Jykubik7CmNoZWNrKCdNMDI3OiB0cmFuc3BvcnRzIHVuY2hhbmdlZCcsIGNudCgyNywgJ1QxJyku'
        'biA9PT0gMSAmJiAhY250KDI3LCAnQTEnKS5waWNrdXApOwpjaGVjaygnbWlzc2lvbiBkYXRhIGl0'
        'c2VsZiB1bnRvdWNoZWQnLCBhcGkuU0NSSVBUX1dBVkVTWzIzXS51LmZpbmQodSA9PiB1LmlkID09'
        'PSAnRjEnKS5uID09PSAyKTsKCmNvbnNvbGUubG9nKCdcbicgKyBwYXNzICsgJyBwYXNzZWQsICcg'
        'KyBmYWlsICsgJyBmYWlsZWQnKTsKcHJvY2Vzcy5leGl0KGZhaWwgPyAxIDogMCk7Cg=='
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
        'CiAgICAvLyBTdGVwIHVudGlsIGNvbmQoKSBob2xkcywgY2xlYXJpbmcgc21hbGwgY3JhZnQgZXZl'
        'cnkgc28gb2Z0ZW4uCiAgICAvLyBldmVyeTogaG93IG9mdGVuIHRoZSBzbWFsbCBjcmFmdCBhcmUg'
        'Y2xlYXJlZCwgaW4gc3RlcHMgKGRlZmF1bHQgMjAwKS4KICAgIHVudGlsKGNvbmQsIG1heCwgY2xl'
        'YXIsIGFsbCwgZXZlcnkpeyBjb25zdCBldiA9IGV2ZXJ5IHx8IDIwMDsKICAgICAgICAgICBmb3Io'
        'bGV0IHQ9MDt0PG1heDt0Kz0yMCl7IGlmKGNvbmQoKSkgcmV0dXJuIHQ7CiAgICAgICAgICAgICBp'
        'ZihjbGVhciAmJiB0JWV2PT09MCkgRlMua2lsbFNtYWxsKCk7CiAgICAgICAgICAgICBpZihhbGwg'
        'JiYgdCUyMDA9PT0wKSBmb3IoY29uc3QgZSBvZiBlbmVtaWVzKXsKICAgICAgICAgICAgICAgaWYo'
        'ZS53YXJwPjAgfHwgZS5pbnZ1bG4gfHwgZS5zY2VuZXJ5KSBjb250aW51ZTsKICAgICAgICAgICAg'
        'ICAgLy8gQSBwcml6ZSBpcyBub3Qgc2hvdCBkb3duOiBpdHMgZW5naW5lcyBhcmUsIHRoZW4gaXQg'
        'aXMgdGFrZW4uCiAgICAgICAgICAgICAgIGlmKGUuY2FwdHVyZUxvY2speyBmb3IoY29uc3QgcyBv'
        'ZiAoZS5zdWJzfHxbXSkpIGlmKHMuaWQ9PT0nZW5naW5lcyd8fHMuaWQ9PT0nd2VhcG9ucycpeyBz'
        'LmRlYWQ9dHJ1ZTsgcy5ocD0wOyB9IGNvbnRpbnVlOyB9CiAgICAgICAgICAgICAgIGUuaHAgPSAw'
        'OyB9CiAgICAgICAgICAgICBGUy5zdGVwKDIwKTsgfSByZXR1cm4gLTE7IH0sCiAgICBpZHMoaWQp'
        'eyByZXR1cm4gYnlJZChpZCk7IH0sCiAgICBlbmVteUlkcygpeyByZXR1cm4gZW5lbWllcy5tYXAo'
        'ZT0+ZS51aWR8fGUudHlwZSk7IH0sCiAgICBhbGx5SWRzKCl7IHJldHVybiBhbGxpZXMubWFwKGE9'
        'PmEudWlkfHxhLnR5cGUpOyB9CiAgfTtgOwoKY29uc3Qgc2NlbmFyaW9zID0gW107CmZ1bmN0aW9u'
        'IHNjZW5hcmlvKG5hbWUsIHF1ZXJ5LCBib2R5LCBub0xhdW5jaCl7IHNjZW5hcmlvcy5wdXNoKHtu'
        'YW1lLCBxdWVyeSwgYm9keSwgbm9MYXVuY2h9KTsgfQoKLy8g4pSA4pSAIFNjZW5hcmlvcyDilIDi'
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
        'ZCh4PT54LnVpZD09PSdBMScpOwogIC8vIFN0ZXAgYnkgc3RlcCB1cCB0byB0aGUgdHVybjogd2hl'
        'cmUgc2hlIHdhcyBsYXN0IGFzIGFuIGFsbHksIGFuZCB3aGVyZQogIC8vIHNoZSBpcyBpbiB0aGUg'
        'Zmlyc3Qgc3RlcCBhcyBhbiBlbmVteS4KICBsZXQgbGFzdCA9IG51bGwsIGZpcnN0ID0gbnVsbDsK'
        'ICBmb3IobGV0IGs9MDtrPDgwMDAgJiYgIWZpcnN0O2srKyl7CiAgICBpZihrJTIwMD09PTApIEZT'
        'LmtpbGxTbWFsbCgpOwogICAgY29uc3QgYWwgPSBhbGxpZXMuZmluZCh4PT54LnVpZD09PSdBMScp'
        'OwogICAgaWYoYWwpIGxhc3QgPSB7eDphbC54LCB5OmFsLnl9OwogICAgRlMuc3RlcCgxKTsKICAg'
        'IGNvbnN0IGVuID0gZW5lbWllcy5maW5kKHg9PngudWlkPT09J0ExJyk7CiAgICBpZihlbikgZmly'
        'c3QgPSB7eDplbi54LCB5OmVuLnl9OwogIH0KICByLnR1cm5zSW5QbGFjZSA9ICEhbGFzdCAmJiAh'
        'IWZpcnN0ICYmIE1hdGguYWJzKGZpcnN0LngtbGFzdC54KSA8IDIgJiYgTWF0aC5hYnMoZmlyc3Qu'
        'eS1sYXN0LnkpIDwgMjsKICBjb25zdCBlID0gZW5lbWllcy5maW5kKHg9PngudWlkPT09J0ExJyk7'
        'CiAgLy8gRnJvbSBoZXJlIG9uIHRoZSBhbGxpZWQgd2luZ3MgY291bGQgc2hvb3QgaGVyIGRvd24g'
        'b3IgaGl0IGhlciBlbmdpbmVzCiAgLy8gYmVmb3JlIHNoZSBnZXRzIGFueXdoZXJlIC0gdGhhdCBp'
        'cyB0aGUgZ2FtZSAtIHNvIGZvciB0aGUgY2hlY2tzIGJlbG93CiAgLy8gc2hlIGFuZCBoZXIgc3Vi'
        'c3lzdGVtcyBhcmUgbWFkZSB0b28gdG91Z2ggZm9yIHRoZW0uCiAgaWYoZSl7IGUuaHAgPSBlLm1h'
        'eEhwID0gMWU3OyBmb3IoY29uc3QgcyBvZiBlLnN1YnN8fFtdKSBzLmhwID0gcy5tYXhIcCA9IDFl'
        'NzsgfQogIEZTLnN0ZXAoNDApOwogIHIudHVybmVkID0gISFlICYmICFhbGxpZXMuc29tZSh4PT54'
        'LnVpZD09PSdBMScpOwogIHIubnRmSHVsbCA9ICEhZSAmJiBlLmltZz09PSdudGZjcmxldmlhdGhh'
        'bic7CiAgci5lbmVteVNoYXBlID0gISFlICYmIGUudHlwZT09PSdjcnVpc2VyJyAmJiBlLnNpZGU9'
        'PT0nZW5lbXknICYmICFlLmRlYWQgJiYgZS5ocD4wOwogIHIuaGFzU3VicyA9ICEhZSAmJiAhIWUu'
        'c3VicyAmJiBlLnN1YnMubGVuZ3RoPT09NTsKICByLmhhc0d1bnMgPSAhIWUgJiYgISEoZS5ndW5z'
        'fHxlLm1vdW50c3x8ZS53cG58fGUuYmVhbXMpOwogIHIuZmFjZXNXaGVyZVNoZUdvZXMgPSAhIWUg'
        'JiYgZS5mbGlwPT09bmVlZHNGbGlwKGUuaW1nLCBmYWxzZSk7CiAgY29uc3QgeDAgPSBlID8gZS54'
        'IDogMDsKICBGUy5zdGVwKDIwMCk7CiAgci53YXZlT3BlbldoaWxlU2hlTGl2ZXMgPSAhd2F2ZU92'
        'ZXI7CiAgci5oZWFkc1JpZ2h0ID0gISFlICYmIGUueCA+IHgwOwogIC8vIExlZnQgYWxvbmUgc2hl'
        'IHJlYWNoZXMgdGhlIGVkZ2UgYW5kIGp1bXBzLgogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+ISFF'
        'Vl9MRUZUWydBMSddLCA4MDAwLCB0cnVlKTsKICByLmp1bXBzQXRUaGVFZGdlID0gdD49MCAmJiBl'
        'LndhcnBPdXQ+MCAmJiBlLnggPCBXOwogIHIud2hpbGVGdWxseU9uU2NyZWVuID0gISFlICYmIGUu'
        'eCArIElNR1NbZS5pbWddLndpZHRoKmUuc2MqMC41IDw9IFc7CiAgRlMudW50aWwoKCk9PiFlbmVt'
        'aWVzLmluY2x1ZGVzKGUpLCAxMDAwLCBmYWxzZSk7CiAgci5nb25lQWZ0ZXJKdW1wID0gIWVuZW1p'
        'ZXMuaW5jbHVkZXMoZSk7CiAgRlMudW50aWwoKCk9PndhdmVPdmVyIHx8IHdhdmU+MzEsIDQwMDAs'
        'IHRydWUpOwogIHIud2F2ZUVuZHMgPSB3YXZlT3ZlciB8fCB3YXZlPjMxOwogIHJldHVybiByO2Ap'
        'OwoKc2NlbmFyaW8oJ00zMSBlbmdpbmVzIHN0b3AgaGVyJywgJ209MzEnLCBgCiAgRlMuc3RlcCgz'
        'MDApOwogIEZTLnVudGlsKCgpPT4hZW5lbWllcy5zb21lKGU9PmUudWlkPT09J0UxJykgJiYgIXNw'
        'YXduUS5zb21lKHE9PnEudWlkPT09J0UxJyksIDYwMDAsIHRydWUpOwogIEZTLnN0ZXAoNDApOwog'
        'IGNvbnN0IGUgPSBlbmVtaWVzLmZpbmQoeD0+eC51aWQ9PT0nQTEnKTsKICBmb3IoY29uc3QgcyBv'
        'ZiBlLnN1YnMpIGlmKHMuaWQ9PT0nZW5naW5lcycpeyBzLmRlYWQgPSB0cnVlOyBzLmhwID0gMDsg'
        'fQogIGNvbnN0IHgwID0gZS54OyBGUy5zdGVwKDYwMCk7CiAgcmV0dXJuIHtzdG9wcGVkOiBNYXRo'
        'LmFicyhlLngteDApIDwgMC4wMSAmJiAhRVZfTEVGVFsnQTEnXX07YCk7CgpzY2VuYXJpbygnTTMy'
        'IERpZSBGcmFjaHRyb3V0ZScsICdtPTMyJywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDMw'
        'MCk7CiAgY29uc3QgZiA9IGFsbGllcy5maWx0ZXIoeD0+eC51aWQ9PT0nRjEnKTsKICByLnR3b0Zy'
        'ZWlnaHRlcnMgPSBmLmxlbmd0aD09PTIgJiYgZi5ldmVyeSh4PT54LmltZz09PSdmcnBvc2VpZG9u'
        'Jyk7CiAgci50ZXJyYW5TaWRlID0gZi5ldmVyeSh4PT54LmZhY3Rpb249PT0ndGVycmFuJyk7CiAg'
        'ci5tZWR1c2FzID0gZW5lbWllcy5maWx0ZXIoZT0+ZS51aWQ9PT0nQjEnKS5ldmVyeShlPT5lLmlt'
        'Zz09PSdib21lZHVzYScpICYmIGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdCMScpOwogIHIuZmln'
        'aHRlckNvdmVyID0gZW5lbWllcy5zb21lKGU9PmUudWlkPT09J0UxJyAmJiBlLnR5cGU9PT0nZmln'
        'aHRlcicpIHx8IHNwYXduUS5zb21lKHE9PnEudWlkPT09J0UxJyk7CiAgY29uc3QgeDAgPSBmLmxl'
        'bmd0aCA/IGZbMF0ueCA6IDA7IEZTLnN0ZXAoMzAwKTsKICByLmNyb3NzaW5nID0gZi5sZW5ndGg+'
        'MCAmJiBmWzBdLnggPiB4MDsKICBGUy51bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09'
        'PSdCMScpLCA0MDAwLCB0cnVlKTsKICBGUy5zdGVwKDMwMCk7CiAgci5zZWNvbmRSYWlkID0gZW5l'
        'bWllcy5zb21lKGU9PmUudWlkPT09J0IyJykgfHwgc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nQjIn'
        'KTsKICByLmVuZHNXaGVuVGhyb3VnaCA9IEZTLnVudGlsKCgpPT53YXZlT3ZlciwgMjAwMDAsIHRy'
        'dWUpID49IDA7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTMzIERpZSBSZWxhaXNzdGF0aW9u'
        'JywgJ209MzMnLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAoMzAwKTsKICBjb25zdCBzID0g'
        'ZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1MxJyk7CiAgci5mYXVzdHVzID0gISFzICYmIHMuaW1n'
        'PT09J3NjZmF1c3R1cyc7CiAgci5hdEdpdmVuSGVpZ2h0ID0gISFzICYmIE1hdGguYWJzKHMueS0y'
        'NTApIDwgMTsKICBjb25zdCB4MCA9IHMgPyBzLnggOiAwOwogIEZTLnN0ZXAoMTIwMCk7CiAgci5z'
        'dGF5c1B1dCA9ICEhcyAmJiBNYXRoLmFicyhzLngteDApIDwgMSAmJiBNYXRoLmFicyhzLnktMjUw'
        'KSA8IDE7CiAgci5ub0ZsYWsgPSAhIXMgJiYgZmxha0hhcyhzKT09PWZhbHNlOwogIHIuZ3VucyA9'
        'IGVuZW1pZXMuZmlsdGVyKGU9PmUudWlkPT09J0cxJykubGVuZ3RoPT09NDsKICAvLyBSZWluZm9y'
        'Y2VtZW50cyBrZWVwIGNvbWluZyB3aGlsZSBzaGUgc3RhbmRzLgogIEZTLmtpbGxTbWFsbCgpOyBG'
        'Uy5zdGVwKDkwMCk7CiAgci5yZWluZm9yY2VkID0gZW5lbWllcy5zb21lKGU9PmUudHlwZT09PSdm'
        'aWdodGVyJyAmJiAhZS51aWQpIHx8IHNwYXduUS5zb21lKHE9PiFxLnVpZCAmJiAvXmZpXy8udGVz'
        'dChxLnR5cGUpKTsKICBjb25zdCBiZWZvcmUgPSBTSE9DS1MubGVuZ3RoOwogIEZTLmtpbGxJZCgn'
        'UzEnKTsgRlMuc3RlcCgzKTsKICByLmJpZ0JsYXN0ID0gU0hPQ0tTLnNvbWUoaz0+ay5yTWF4PT09'
        'MzAwKTsKICBGUy5raWxsU21hbGwoKTsgRlMuc3RlcCgxMjAwKTsgRlMua2lsbFNtYWxsKCk7IEZT'
        'LnN0ZXAoNjAwKTsKICByLnJlaW5mT2ZmID0gZXZSZWluZj09PWZhbHNlOwogIHJldHVybiByO2Ap'
        'OwoKc2NlbmFyaW8oJ00zNCBEaWUgRmxha3dhbmQnLCAnbT0zNCcsIGAKICBjb25zdCByID0ge307'
        'CiAgc2NvcmUgPSAyMDAwMDsgICAvLyBlbm91Z2ggZm9yIHRoZSBBcnRlbWlzIHRvIGJlIG9wZW4g'
        'aW4gdGhpcyBjeWNsZQogIEZTLnN0ZXAoNDAwKTsKICBjb25zdCBrID0gZW5lbWllcy5maWx0ZXIo'
        'ZT0+ZS51aWQ9PT0nSzEnKTsKICByLnR3b0Flb2x1cyA9IGsubGVuZ3RoPT09MiAmJiBrLmV2ZXJ5'
        'KGU9PmUuaW1nPT09J250ZmNyYWVvbHVzJyk7CiAgci5mbGFrID0gay5ldmVyeShlPT5mbGFrSGFz'
        'KGUpKTsKICByLm5vSGFuZ2FyWWV0ID0gIWFsbGllcy5zb21lKGE9PmEudWlkPT09J0ExJyk7CiAg'
        'RlMudW50aWwoKCk9PiFlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nRTEnKSAmJiAhc3Bhd25RLnNv'
        'bWUocT0+cS51aWQ9PT0nRTEnKSwgNTAwMCwgdHJ1ZSk7CiAgRlMuc3RlcCg0MDApOwogIGNvbnN0'
        'IG8gPSBhbGxpZXMuZmluZChhPT5hLnVpZD09PSdBMScpOwogIHIub3Jpb24gPSAhIW8gJiYgby5p'
        'bWc9PT0nZGVvcmlvbnJpZ2h0JzsKICB0aWNrU2hpcFVubG9ja3MoKTsKICByLmJvbWJlck9mZmVy'
        'ZWQgPSBzaGlwT2ZmZXJlZCgnYm9hcnRlbWlzJykgJiYgc2hpcFN3YXBSZWFkeSgpOwogIHJldHVy'
        'biByO2ApOwoKc2NlbmFyaW8oJ00zNSBEZXIgVWViZXJsYWV1ZmVyJywgJ209MzUnLCBgCiAgY29u'
        'c3QgciA9IHt9OwogIEZTLnN0ZXAoMzAwKTsKICBjb25zdCBkID0gYWxsaWVzLmZpbmQoYT0+YS51'
        'aWQ9PT0nQTEnKTsKICByLm50ZkRlaW1vcyA9ICEhZCAmJiBkLmltZz09PSdudGZjb2RlaW1vcycg'
        'JiYgZC50eXBlPT09J2NvcnZldHRlJzsKICByLmNvbWVzRnJvbVRoZVJpZ2h0ID0gISFkICYmIGQu'
        'eCA+IFcqMC42OwogIHIuZmFjZXNMZWZ0ID0gISFkICYmIGQuZmxpcD09PW5lZWRzRmxpcCgnbnRm'
        'Y29kZWltb3MnLCB0cnVlKTsKICByLmNyb3NzaW5nID0gISFkICYmIGQudHJhbnNpdD09PXRydWU7'
        'CiAgci5maXJzdFdpbmdIdW50c0hlciA9IHdhdmVIdW50PT09J0ExJzsKICBjb25zdCB4MCA9IGQg'
        'PyBkLnggOiAwOyBGUy5zdGVwKDIwMCk7CiAgci5oZWFkc0xlZnQgPSAhIWQgJiYgZC54IDwgeDA7'
        'CiAgRlMudW50aWwoKCk9PiFlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nRTEnKSAmJiAhc3Bhd25R'
        'LnNvbWUocT0+cS51aWQ9PT0nRTEnKSwgNTAwMCwgdHJ1ZSk7CiAgRlMuc3RlcCgyMCk7CiAgci5y'
        'ZWluZm9yY2VtZW50c09uID0gZXZSZWluZj09PXRydWU7CiAgci5mb2xsb3dVcHNTY3JlZW4gPSB3'
        'YXZlSHVudD09PScnOwogIHIucmVhcm0gPSBjb3J2ZXR0ZU9uRmllbGQoKTsKICByLm5vdE9uQ2Fs'
        'bE1lbnUgPSBBTExZX09SREVSLmluZGV4T2YoJ250Zl9kZWltb3MnKTwwOwogIC8vIFdoYXQgaXMg'
        'Y2hlY2tlZCBoZXJlIGlzIHRoZSBjcm9zc2luZywgbm90IHRoZSBiYWxhbmNlIC0gU2lsdmlvIHBs'
        'YXlzCiAgLy8gdGhhdC4gU28gc2hlIGlzIG1hZGUgdG9vIHRvdWdoIHRvIGxvc2Ugb24gdGhlIHdh'
        'eS4KICBkLmhwID0gZC5tYXhIcCA9IDFlNzsKICBmb3IoY29uc3QgcyBvZiBkLnN1YnN8fFtdKSBz'
        'LmhwID0gcy5tYXhIcCA9IDFlNzsgICAgLy8gZW5naW5lcyB0b286IGRlYWQgZW5naW5lcyBzdG9w'
        'IGEgY3Jvc3NpbmcKICBjb25zdCBnb3QgPSBGUy51bnRpbCgoKT0+IWFsbGllcy5zb21lKGE9PmEu'
        'dWlkPT09J0ExJyksIDkwMDAsIHRydWUpOwogIHIuZ2V0c0Fjcm9zcyA9IGdvdD49MCAmJiAhZ3Vh'
        'cmRMb3N0OwogIHIubGVmdENvdW50cyA9ICEhRVZfTEVGVFsnQTEnXTsKICByLm5vdGhpbmdNb3Jl'
        'Q29tZXMgPSBldlJlaW5mPT09ZmFsc2UgJiYgc3Bhd25RLmxlbmd0aD09PTA7CiAgRlMudW50aWwo'
        'KCk9PndhdmVPdmVyLCA0MDAwLCB0cnVlKTsKICByLndhdmVFbmRzID0gd2F2ZU92ZXI7CiAgcmV0'
        'dXJuIHI7YCk7CgpzY2VuYXJpbygnTTM2IERpZSBJY2VuaScsICdtPTM2JywgYAogIGNvbnN0IHIg'
        'PSB7fTsKICBjb25zdCBzMCA9IHNjb3JlID0gNTAwMDsKICBGUy5zdGVwKDMwMCk7CiAgY29uc3Qg'
        'aSA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdWMScpOwogIHIuaWNlbmkgPSAhIWkgJiYgaS5p'
        'Y2VuaT09PXRydWUgJiYgaS5pbWc9PT0nY29pY2VuaSc7CiAgci5ub05hdmlnYXRpb24gPSAhIWkg'
        'JiYgISFpLnN1YnMgJiYgaS5zdWJzLmxlbmd0aD09PTQgJiYgc3ViT0soaSwnbmF2aWdhdGlvbicp'
        'OwogIHIuZGVhZGxpbmUgPSAhIWkgJiYgaS5mbGVlVD4wICYmIGkuZmxlZVQgPD0gMjUqVElDS19I'
        'WjsKICBGUy5zdGVwKDYwMCk7CiAgci53aG9sZUh1bGxPblNjcmVlbiA9ICEhaSAmJiBpLnggKyBJ'
        'TUdTW2kuaW1nXS53aWR0aCppLnNjKjAuNSA8PSBXOwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+'
        'IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdWMScpLCA2MDAwLCBmYWxzZSk7CiAgci5qdW1wc091'
        'dCA9IHQ+PTAgJiYgaWNlbkVzY2FwZXM9PT0xOwogIHIubm9QZW5hbHR5ID0gc2NvcmUgPj0gczA7'
        'CiAgci5mZW5yaXMgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nSzEnICYmIGUuaW1nPT09J250'
        'ZmNyZmVucmlzJyk7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnQ3ljbGUgY2hhbmdlIDMwIC0+'
        'IDMxJywgJ209MzAnLCBgCiAgY29uc3QgciA9IHt9OwogIHIuc3RhcnRzVmFzdWRhbiA9IHBsYXll'
        'ci5zaGlwPT09J2ZpdG90aCcgJiYgQUxMWV9GQUNfT04udmFzdWRhbj09PXRydWU7CiAgc2NvcmUg'
        'PSA5MDAwMDsKICAvLyBDbGVhciB3YXZlIDMwIGJ5IGZvcmNlIGFuZCBsZXQgdGhlIGp1bXAgaGFw'
        'cGVuLgogIGZvcihsZXQgaz0wO2s8NjAgJiYgd2F2ZT09PTMwO2srKyl7IGZvcihjb25zdCBlIG9m'
        'IGVuZW1pZXMpIGlmKCEoZS53YXJwPjApICYmICFlLmludnVsbikgZS5ocD0wOyBGUy5zdGVwKDIw'
        'MCk7IH0KICByLndhdmUgPSB3YXZlOwogIHIubXlybWlkb24gPSBwbGF5ZXIuc2hpcD09PSdmaW15'
        'cm1pZG9uJzsKICByLm9uZUh1bGwgPSBzaGlwVW5sb2NrZWQ9PT0xICYmIGN5Y2xlQmFzZT09PXNj'
        'b3JlIC0gKHNjb3JlLWN5Y2xlQmFzZSk7CiAgci5iYXNlU2V0ID0gY3ljbGVCYXNlID49IDkwMDAw'
        'OwogIHIudGVycmFuID0gQUxMWV9GQUNfT04udGVycmFuPT09dHJ1ZSAmJiBBTExZX0ZBQ19PTi52'
        'YXN1ZGFuPT09ZmFsc2U7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTEzIGJvdGggdHJhbnNw'
        'b3J0cyBvbiB0aW1lJywgJ209MTMnLCBgCiAgRlMuc3RlcCgzMDApOwogIHJldHVybiB7Ym90aFRy'
        'YW5zcG9ydHM6IGFsbGllcy5maWx0ZXIoYT0+YS51aWQ9PT0nVDEnKS5sZW5ndGg9PT0yfTtgKTsK'
        'Ci8vIEV2ZXJ5IHdyaXR0ZW4gbWlzc2lvbiBoYXMgdG8gY29tZSB0byBhbiBlbmQgd2hlbiBpdHMg'
        'ZW5lbWllcyBnbyBkb3duLAovLyB3aXRoIG5vdGhpbmcgdGhyb3duIG9uIHRoZSB3YXkuIEVuZW15'
        'IHNoaXBzIGFyZSBjbGVhcmVkIGV2ZXJ5IHR3byBzZWNvbmRzCi8vIG9uY2UgdGhleSBhcmUgb3V0'
        'IG9mIHRoZWlyIHZvcnRleCAtIGEgcGxheWVyIHdobyBoaXRzIGV2ZXJ5dGhpbmcuCi8vIFNjYW4g'
        'bWlzc2lvbnMgKDEyLCAyMykgbmVlZCB0aGUgcGxheWVyIHRvIGZseSB0aGUgc2NhbiBhbmQgYXJl'
        'IGxlZnQgb3V0Lgpmb3IobGV0IG09MTttPD00MjttKyspIGlmKG0hPT0xMiAmJiBtIT09MjMpIHNj'
        'ZW5hcmlvKCdNJyArIFN0cmluZyhtKS5wYWRTdGFydCgyLCcwJykgKyAnIHBsYXlzIHRvIHRoZSBl'
        'bmQnLCAnbT0nICsgbSwgYAogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+d2F2ZU92ZXIsIDQwMDAw'
        'LCBmYWxzZSwgdHJ1ZSk7CiAgSVRFTVMubGVuZ3RoID0gMDsgICAgIC8vIHBpY2t1cHMgaG9sZCB0'
        'aGUganVtcCBvcGVuIHVudGlsIHRoZXkgZXhwaXJlCiAgY29uc3QgaiA9IEZTLnVudGlsKCgpPT53'
        'YXZlID09PSAke219KzEsIDYwMDAsIGZhbHNlLCBmYWxzZSk7CiAgcmV0dXJuIHtlbmRzOiB0ID49'
        'IDAsIG5leHRXYXZlOiBqID49IDB9O2ApOwoKc2NlbmFyaW8oJ1BpY2t1cHMgYXJlIGRyYXduIHRv'
        'IHRoZSBzaGlwJywgJ209MScsIGAKICBGUy5zdGVwKDIwMCk7CiAgY29uc3QgciA9IHt9OwogIHRp'
        'Y2tldHMuY3J1aXNlciA9IDA7CiAgSVRFTVMucHVzaCh7eDpwbGF5ZXIueCsxMDAsIHk6cGxheWVy'
        'LnksIHZ4OklURU1fRFJJRlQsIHZ5OjAsIGtpbmQ6J2NydWlzZXInLCBsaWZlOjUwMDB9KTsKICBJ'
        'VEVNUy5wdXNoKHt4OnBsYXllci54KzQwMCwgeTpwbGF5ZXIueSsxMDAsIHZ4OjAsIHZ5OjAsIGtp'
        'bmQ6J3JlcGFpcicsIGxpZmU6NTAwMH0pOwogIGNvbnN0IGZhciA9IElURU1TWzFdOwogIEZTLnN0'
        'ZXAoNjApOwogIHIubmVhck9uZUNvbGxlY3RlZCA9IHRpY2tldHMuY3J1aXNlcj09PTE7CiAgci5m'
        'YXJPbmVMZWZ0QWxvbmUgPSBJVEVNUy5pbmNsdWRlcyhmYXIpICYmICFmYXIuY2F1Z2h0OwogIC8v'
        'IENhdWdodCwgaXQga2VlcHMgZm9sbG93aW5nIGV2ZW4gaWYgdGhlIHNoaXAgcHVsbHMgYXdheS4K'
        'ICBwbGF5ZXIueCA9IDEwMDsgcGxheWVyLnkgPSAyNTA7CiAgSVRFTVMucHVzaCh7eDoyMTAsIHk6'
        'MjUwLCB2eDowLCB2eTowLCBraW5kOidjb3J2ZXR0ZScsIGxpZmU6NTAwMH0pOwogIGNvbnN0IGMg'
        'PSBJVEVNU1tJVEVNUy5sZW5ndGgtMV07CiAgRlMuc3RlcCgxKTsKICByLmNhdWdodCA9IGMuY2F1'
        'Z2h0PT09dHJ1ZTsKICBsZXQgZ290ID0gZmFsc2U7CiAgZm9yKGxldCBrPTA7azwyMDAgJiYgIWdv'
        'dDtrKyspeyBwbGF5ZXIueCA9IDYwOyBwbGF5ZXIueSA9IDI1MDsgRlMuc3RlcCgxKTsgZ290ID0g'
        'IUlURU1TLmluY2x1ZGVzKGMpOyB9CiAgci5mb2xsb3dzQW5kQXJyaXZlcyA9IGdvdDsKICByZXR1'
        'cm4gcjtgKTsKCnNjZW5hcmlvKCdUaXRsZTogZnVsbHNjcmVlbiBidXR0b24nLCAnJywgYAogIGNv'
        'bnN0IHIgPSB7fTsKICBsZXQgY2FsbHMgPSAwOwogIHRvZ2dsZUZ1bGxzY3JlZW4gPSBmdW5jdGlv'
        'bigpeyBjYWxscysrOyB9OwogIGRyYXcoKTsKICBjb25zdCBiID0gd2luZG93Ll90aXRsZUZzUmVj'
        'dDsKICByLnNob3duID0gISFiICYmIGIueCA+PSAwICYmIGIueCArIGIudyA8PSBXICYmIGIueSA+'
        'PSAwICYmIGIueSArIGIuaCA8PSBIOwogIHIuY2xlYXJPZlRoZVRpdGxlID0gISFiICYmIGIueSAr'
        'IGIuaCA8IDEyOCAtIDU0OwogIGNvbnN0IGNyID0gQ1ZTLmdldEJvdW5kaW5nQ2xpZW50UmVjdCgp'
        'OwogIGNvbnN0IGNsaWNrID0gKGd4LCBneSk9PnsKICAgIGNvbnN0IGV2ID0gbmV3IE1vdXNlRXZl'
        'bnQoJ21vdXNlZG93bicsIHtidXR0b246MCwgYnViYmxlczp0cnVlLAogICAgICBjbGllbnRYOiBj'
        'ci5sZWZ0ICsgZ3gqY3Iud2lkdGgvVywgY2xpZW50WTogY3IudG9wICsgZ3kqY3IuaGVpZ2h0L0h9'
        'KTsKICAgIENWUy5kaXNwYXRjaEV2ZW50KGV2KTsKICAgIENWUy5kaXNwYXRjaEV2ZW50KG5ldyBN'
        'b3VzZUV2ZW50KCdtb3VzZXVwJywge2J1dHRvbjowLCBidWJibGVzOnRydWV9KSk7CiAgfTsKICBj'
        'bGljayhiLnggKyBiLncvMiwgYi55ICsgYi5oLzIpOwogIHIuYnV0dG9uU3dpdGNoZXMgPSBjYWxs'
        'cz09PTE7CiAgci5hbmREb2VzTm90U3RhcnRUaGVSdW4gPSBHUz09PSd0aXRsZSc7CiAgZG9jdW1l'
        'bnQuZGlzcGF0Y2hFdmVudChuZXcgS2V5Ym9hcmRFdmVudCgna2V5ZG93bicsIHtjb2RlOidLZXlG'
        'J30pKTsKICBkb2N1bWVudC5kaXNwYXRjaEV2ZW50KG5ldyBLZXlib2FyZEV2ZW50KCdrZXl1cCcs'
        'IHtjb2RlOidLZXlGJ30pKTsKICByLmZLZXlPblRoZVRpdGxlID0gY2FsbHM9PT0yICYmIEdTPT09'
        'J3RpdGxlJzsKICBjbGljayhXLzIsIEgvMik7CiAgci5lbHNld2hlcmVTdGFydHNUaGVSdW4gPSBH'
        'Uz09PSdwbGF5aW5nJyAmJiBjYWxscz09PTI7CiAgcmV0dXJuIHI7YCwgdHJ1ZSk7CgpzY2VuYXJp'
        'bygnTTM3IERpZSBVbnNpY2h0YmFyZW4nLCAnbT0zNycsIGAKICBjb25zdCByID0ge307CiAgRlMu'
        'c3RlcCg0MDApOwogIGNvbnN0IGxva2lzID0gZW5lbWllcy5maWx0ZXIoZT0+ZS51aWQ9PT0nRTEn'
        'KTsKICByLmxva2lzID0gbG9raXMubGVuZ3RoPjAgJiYgbG9raXMuZXZlcnkoZT0+ZS5pbWc9PT0n'
        'Zmlsb2tpJyk7CiAgci5ub0xvY2tPblRoZW0gPSBsb2tpcy5sZW5ndGg+MCAmJiBsb2tpcy5ldmVy'
        'eShlPT4hY2FuTG9ja09uKGUpKTsKICByLmluUGxhaW5TaWdodCA9IGxva2lzLmV2ZXJ5KGU9PiFl'
        'LmhpZGRlbiAmJiAhZS5jbG9hayAmJiBlLmFscGhhPT09dW5kZWZpbmVkKTsKICAvLyBBbiBlbmVt'
        'eSBmaWdodGVyIG9mIGFueSBvdGhlciBodWxsIGNhbiBzdGlsbCBiZSBsb2NrZWQuCiAgY29uc3Qg'
        'b3RoZXIgPSB7c2lkZTonZW5lbXknLCBpbWc6J2ZpaGVyYyd9OwogIHIub3RoZXJzU3RpbGxMb2Nr'
        'YWJsZSA9IGNhbkxvY2tPbihvdGhlcik7CiAgLy8gQSBwbGF5ZXIgTG9raSBsYXRlciBvbiBrZWVw'
        'cyBpdHMgb3duIHJ1bGVzOiB0aGUgbm8tbG9jayBpcyBlbmVteSBvbmx5LgogIHIub25seVRoZUVu'
        'ZW15U2lkZSA9IGNhbkxvY2tPbih7c2lkZTonYWxseScsIGltZzonZmlsb2tpJ30pOwogIC8vIENs'
        'ZWFyIHRoZW0gbG90IGJ5IGxvdCBhbmQgbm90ZSBldmVyeSBsb3QgdGhhdCBzaG93cyB1cC4KICBj'
        'b25zdCBzZWVuID0ge307CiAgRlMudW50aWwoKCk9PnsgZm9yKGNvbnN0IGUgb2YgZW5lbWllcykg'
        'aWYoZS51aWQpeyBzZWVuW2UudWlkXSA9IHNlZW5bZS51aWRdIHx8IGUuaW1nOyB9IHJldHVybiB3'
        'YXZlT3ZlcjsgfSwgMjAwMDAsIHRydWUpOwogIHIudGhyZWVMb3RzT2ZMb2tpcyA9IHNlZW4uRTE9'
        'PT0nZmlsb2tpJyAmJiBzZWVuLkUyPT09J2ZpbG9raScgJiYgc2Vlbi5FMz09PSdmaWxva2knOwog'
        'IHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ00zOCBEaWUgS2FwZXJ1bmcnLCAnbT0zOCcsIGAKICBj'
        'b25zdCByID0ge307CiAgc2NvcmUgPSAxMDAwOwogIEZTLnN0ZXAoNDAwKTsKICBjb25zdCBkID0g'
        'ZW5lbWllcy5maW5kKGU9PmUudWlkPT09J0QxJyk7CiAgci5kZWltb3MgPSAhIWQgJiYgZC5pbWc9'
        'PT0nbnRmY29kZWltb3MnOwogIHIubWlkRmllbGQgPSAhIWQgJiYgTWF0aC5hYnMoZC55LTI2MCkg'
        'PCAxOwogIHIuaGVhZHNSaWdodCA9ICEhZCAmJiBkLmVzY2FwaW5nPjAgJiYgZC5mbGlwPT09bmVl'
        'ZHNGbGlwKGQuaW1nLCBmYWxzZSk7CiAgci5zYXlzV2hhdFRvRG8gPSBtaXNzaW9uT2JqPT09J0RJ'
        'U0FCTEUgVEhFIERFSU1PUyAtIEVOR0lORVMgQU5EIFdFQVBPTlMnOwogIGRhbWFnZUVuZW15KGQs'
        'IGQubWF4SHAqNSwgZC54LCBkLnksIHRydWUsICdib2x0Jyk7IEZTLnN0ZXAoMyk7CiAgci5jYW5u'
        'b3RCZURlc3Ryb3llZCA9IGVuZW1pZXMuaW5jbHVkZXMoZCkgJiYgZC5ocCA+IDA7CiAgY29uc3Qg'
        'a2lsbCA9IGlkPT57IGZvcihjb25zdCBzIG9mIGQuc3VicykgaWYocy5pZD09PWlkKXsgcy5kZWFk'
        'PXRydWU7IHMuaHA9MDsgfSB9OwogIGtpbGwoJ2VuZ2luZXMnKTsKICBjb25zdCB4MCA9IGQueDsg'
        'RlMuc3RlcCgzMDApOwogIHIuZW5naW5lc1N0b3BIZXIgPSBNYXRoLmFicyhkLngteDApIDwgMC4w'
        'MTsKICByLm5vRWx5c2l1bVdoaWxlSGVyR3Vuc1dvcmsgPSAhYWxsaWVzLnNvbWUoYT0+YS51aWQ9'
        'PT0nVDEnKSAmJiAhc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nVDEnKTsKICBraWxsKCd3ZWFwb25z'
        'Jyk7IEZTLnN0ZXAoMik7CiAgci5uZXdPYmplY3RpdmUgPSBtaXNzaW9uT2JqPT09J0NPVkVSIFRI'
        'RSBFTFlTSVVNJzsKICBGUy5zdGVwKDIwMCk7CiAgci5lbHlzaXVtQ29tZXNPbmNlQm90aEFyZURv'
        'd24gPSBhbGxpZXMuc29tZShhPT5hLnVpZD09PSdUMScgJiYgYS5pbWc9PT0ndHJlbHlzaXVtJykg'
        'fHwgc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nVDEnKSB8fCAhIUVWX0RPQ0tbJ1QxJ107CiAgY29u'
        'c3QgZ290ID0gRlMudW50aWwoKCk9PiEhRVZfRE9DS1snVDEnXSwgOTAwMCwgdHJ1ZSk7CiAgRlMu'
        'c3RlcCg1KTsKICByLmRvY2tzID0gZ290Pj0wOwogIHIudGFrZW4gPSBkLmNhcHR1cmVkPT09dHJ1'
        'ZSAmJiAhIUVWX1RBS0VOWydEMSddICYmIChkLndhcnBPdXQ+MCB8fCAhZW5lbWllcy5pbmNsdWRl'
        'cyhkKSk7CiAgci5jb21wbGV0ZUNhcmQgPSAhIW9iakNhcmQgJiYgb2JqQ2FyZC5oZWFkPT09J09C'
        'SkVDVElWRSBDT01QTEVURScgJiYgb2JqQ2FyZC50eHQ9PT0nREVJTU9TIENBUFRVUkVEJzsKICBy'
        'LnBvaW50c0ZvckhlciA9IHNjb3JlID49IDEwMDAgKyAoZC5wdHN8fDApOwogIEZTLnVudGlsKCgp'
        'PT4hZW5lbWllcy5pbmNsdWRlcyhkKSwgMTAwMCwgZmFsc2UpOwogIEZTLnN0ZXAoNTApOwogIHIu'
        'bm9GYWlsdXJlQWZ0ZXJ3YXJkcyA9ICEob2JqQ2FyZCAmJiBvYmpDYXJkLnRvbmU9PT0nZmFpbCcp'
        'OwogIHIubGVhdmVzV2l0aG91dFBlbmFsdHkgPSAhZW5lbWllcy5pbmNsdWRlcyhkKSAmJiBzY29y'
        'ZSA+PSAxMDAwICsgKGQucHRzfHwwKTsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNMzggRWx5'
        'c2l1bSBsb3N0OiBzaGUgY2FuIGRpZScsICdtPTM4JywgYAogIEZTLnN0ZXAoNDAwKTsKICBjb25z'
        'dCBkID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J0QxJyk7CiAgZm9yKGNvbnN0IHMgb2YgZC5z'
        'dWJzKSBpZihzLmlkPT09J2VuZ2luZXMnfHxzLmlkPT09J3dlYXBvbnMnKXsgcy5kZWFkPXRydWU7'
        'IHMuaHA9MDsgfQogIEZTLnVudGlsKCgpPT5hbGxpZXMuc29tZShhPT5hLnVpZD09PSdUMScpLCAy'
        'MDAwLCB0cnVlKTsKICBmb3IoY29uc3QgYSBvZiBhbGxpZXMpIGlmKGEudWlkPT09J1QxJykgYS5o'
        'cCA9IDA7CiAgRlMuc3RlcCgzMCk7CiAgY29uc3QgZnJlZWQgPSBkLmNhcHR1cmVMb2NrPT09ZmFs'
        'c2U7CiAgY29uc3QgZmFpbENhcmQgPSAhIW9iakNhcmQgJiYgb2JqQ2FyZC50b25lPT09J2ZhaWwn'
        'ICYmIG9iakNhcmQudHh0PT09J0VMWVNJVU0gTE9TVCc7CiAgZC5ocCA9IDA7IEZTLnN0ZXAoMzAw'
        'KTsKICByZXR1cm4ge2ZyZWVkOiBmcmVlZCwgZmFpbENhcmQ6IGZhaWxDYXJkLCB0aGVuRGVzdHJv'
        'eWFibGU6ICFlbmVtaWVzLmluY2x1ZGVzKGQpICYmICFFVl9MRUZUWydEMSddfTtgKTsKCnNjZW5h'
        'cmlvKCdNMzggbGVmdCBhbG9uZSBzaGUganVtcHMgYXQgdGhlIGVkZ2UnLCAnbT0zOCcsIGAKICBG'
        'Uy5zdGVwKDMwMCk7CiAgY29uc3QgZCA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdEMScpOwog'
        'IGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+ISFFVl9MRUZUWydEMSddLCA4MDAwLCB0cnVlKTsKICBG'
        'Uy5zdGVwKDIpOwogIHJldHVybiB7anVtcHM6IHQ+PTAgJiYgZC53YXJwT3V0PjAgJiYgIWQuY2Fw'
        'dHVyZWQsIG9uU2NyZWVuOiBkLnggKyBJTUdTW2QuaW1nXS53aWR0aCpkLnNjKjAuNSA8PSBXLAog'
        'ICAgICAgICAgZmFpbENhcmQ6ICEhb2JqQ2FyZCAmJiBvYmpDYXJkLnRvbmU9PT0nZmFpbCcgJiYg'
        'b2JqQ2FyZC50eHQ9PT0nVEhFIERFSU1PUyBHT1QgQVdBWSd9O2ApOwoKc2NlbmFyaW8oJ00zOSBE'
        'aWUgR2FzZXJudGUnLCAnbT0zOScsIGAKICBjb25zdCByID0ge307CiAgci5uZWJ1bGEgPSBuZWJ1'
        'bGFPbigpPT09dHJ1ZTsKICBGUy5zdGVwKDE2MDApOwogIGNvbnN0IG0gPSBlbmVtaWVzLmZpbHRl'
        'cihlPT4vXk0vLnRlc3QoZS51aWR8fCcnKSk7CiAgci50aHJlZU1pbmVycyA9IG0ubGVuZ3RoPT09'
        'MyAmJiBtLmV2ZXJ5KGU9PmUuaW1nPT09J2dtemVwaHlydXMnKTsKICByLnJ1bm5pbmcgPSBtLmV2'
        'ZXJ5KGU9PmUuZXNjYXBpbmc+MCk7CiAgci5mZW5yaXMgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9'
        'PT0nSzEnICYmIGUuaW1nPT09J250ZmNyZmVucmlzJyk7CiAgY29uc3QgbTEgPSBlbmVtaWVzLmZp'
        'bmQoZT0+ZS51aWQ9PT0nTTEnKTsKICBtMS5ocCA9IDA7IEZTLnN0ZXAoMyk7CiAgci5naWFudEJs'
        'YXN0ID0gU0hPQ0tTLnNvbWUoaz0+ay5yTWF4PT09NDAwKTsKICByZXR1cm4gcjtgKTsKCnNjZW5h'
        'cmlvKCdNNDAgRGVyIFNlbnNvcnN0dXJtJywgJ209NDAnLCBgCiAgY29uc3QgciA9IHt9OwogIHIu'
        'bmVidWxhID0gbmVidWxhT24oKT09PXRydWU7CiAgY29uc3Qgc2VlbiA9IHt9OwogIGNvbnN0IG5v'
        'dGUgPSAoKT0+eyBmb3IoY29uc3QgZSBvZiBlbmVtaWVzKSBpZihlLnVpZCkgc2VlbltlLnVpZF09'
        'MTsgfTsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9Pnsgbm90ZSgpOyByZXR1cm4gZW1wT3V0PjA7'
        'IH0sIDYwMDAsIHRydWUpOwogIHIuc3Rvcm1IaXRzID0gdD49MDsKICByLm5vTG9ja0luVGhlU3Rv'
        'cm0gPSAhY2FuTG9ja09uKHtzaWRlOidlbmVteScsIGltZzonZmloZXJjbWsyJ30pOwogIHIub3Jp'
        'b24gPSBhbGxpZXMuc29tZShhPT5hLnVpZD09PSdBMScgJiYgYS5pbWc9PT0nZGVvcmlvbnJpZ2h0'
        'Jyk7CiAgRlMudW50aWwoKCk9Pnsgbm90ZSgpOyByZXR1cm4gd2F2ZU92ZXI7IH0sIDQwMDAwLCB0'
        'cnVlKTsKICByLnRocmVlUm91bmRzID0gWydFMScsJ0IxJywnRTInLCdCMicsJ0UzJywnQjMnXS5l'
        'dmVyeShrPT5zZWVuW2tdKTsKICBpZighci50aHJlZVJvdW5kcykgci5zZWVuID0gT2JqZWN0Lmtl'
        'eXMoc2Vlbikuam9pbigpICsgJyB8ICcgKyBFVi5tYXAoZT0+ZS5hKyc+JytlLncrJz4nKyhlLndh'
        'fHwnJykrJzonK2UuZG9uZSkuam9pbignICcpOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000'
        'MSBEYXMgTGF6YXJldHQnLCAnbT00MScsIGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCgzMDAp'
        'OwogIGNvbnN0IGggPSBhbGxpZXMuZmluZChhPT5hLnVpZD09PSdIMScpOwogIHIuaGlwcG9jcmF0'
        'ZXMgPSAhIWggJiYgaC5pbWc9PT0nbWVoaXBwb2NyYXRlcyc7CiAgci5odW50ZWQgPSB3YXZlSHVu'
        'dD09PSdIMSc7CiAgY29uc3QgeDAgPSBoID8gaC54IDogMDsgRlMuc3RlcCgzMDApOwogIHIuY3Jv'
        'c3Nlc1Nsb3dseSA9ICEhaCAmJiBoLnggPiB4MCAmJiAoaC54LXgwKSA8IDEwMDsKICByLmJvbWJl'
        'cnMgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nQjEnICYmIGUuaW1nPT09J2JvbWVkdXNhJyk7'
        'CiAgY29uc3Qgb3JpZyA9IGRyYXdIdWxsQmxvY2tzOyBsZXQgYmFyRm9yID0gZmFsc2U7CiAgZHJh'
        'd0h1bGxCbG9ja3MgPSBmdW5jdGlvbihlKXsgaWYoZT09PWgpIGJhckZvciA9IHRydWU7IHJldHVy'
        'biBvcmlnLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07CiAgZHJhdygpOyBkcmF3SHVsbEJsb2Nr'
        'cyA9IG9yaWc7CiAgci5odWxsQmFyT25UaGVIaXBwb2NyYXRlcyA9IGJhckZvcjsKICBjb25zdCBn'
        'b3QgPSBGUy51bnRpbCgoKT0+IWFsbGllcy5pbmNsdWRlcyhoKSwgOTAwMCwgdHJ1ZSk7CiAgci5n'
        'ZXRzVGhyb3VnaCA9IGdvdD49MCAmJiAhZ3VhcmRMb3N0OwogIHJldHVybiByO2ApOwoKc2NlbmFy'
        'aW8oJ000MiBEaWUgSGVjYXRlJywgJ209NDInLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAo'
        'NDAwKTsgZHJhdygpOwogIHIuc2F5c1doYXRUb0RvID0gbWlzc2lvbk9iaj09PSdESVNBQkxFIEhF'
        'Q0FURSBXRUFQT05TJyAmJiBvYmpQaW5uZWQ9PT0nRElTQUJMRSBIRUNBVEUgV0VBUE9OUyc7CiAg'
        'Y29uc3QgdiA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdWMScpOwogIHIuaGVjYXRlID0gISF2'
        'ICYmIHYuaW1nPT09J250ZmRlaGVjYXRlJzsKICByLm9yaW9uID0gYWxsaWVzLnNvbWUoYT0+YS51'
        'aWQ9PT0nQTEnKTsKICBGUy51bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdFMScp'
        'ICYmICFzcGF3blEuc29tZShxPT5xLnVpZD09PSdFMScpLCA1MDAwLCB0cnVlKTsKICBGUy5zdGVw'
        'KDIwKTsKICByLnJlaW5mb3JjZW1lbnRzT24gPSBldlJlaW5mPT09dHJ1ZTsKICBmb3IoY29uc3Qg'
        'cyBvZiB2LnN1YnMpIGlmKHMuaWQ9PT0nd2VhcG9ucycpeyBzLmRlYWQ9dHJ1ZTsgcy5ocD0wOyB9'
        'CiAgRlMuc3RlcCgyMCk7IGRyYXcoKTsKICByLm5leHRTdGVwID0gbWlzc2lvbk9iaj09PSdERVNU'
        'Uk9ZIFRIRSBIRUNBVEUnICYmICEhb2JqQ2FyZCAmJiBvYmpDYXJkLmhlYWQ9PT0nTkVXIE9CSkVD'
        'VElWRScgJiYgb2JqQ2FyZC50eHQ9PT0nREVTVFJPWSBUSEUgSEVDQVRFJzsKICByLmRpc2FybWVk'
        'V2l0aGRyYXdzID0gdi5mbGVlVD4wOwogIC8vIEEgZGVzdHJveWVyIGdvZXMgZG93biBpbiBhIGRl'
        'YXRoIHJvbGwgdGhhdCB0YWtlcyBhIHdoaWxlLgogIHYuaHAgPSAwOwogIHIuY29tcGxldGVDYXJk'
        'ID0gRlMudW50aWwoKCk9PnsgZHJhdygpOyByZXR1cm4gISFvYmpDYXJkICYmIG9iakNhcmQuaGVh'
        'ZD09PSdPQkpFQ1RJVkUgQ09NUExFVEUnCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg'
        'ICAgICAgICAgICYmIG9iakNhcmQudHh0PT09J0hFQ0FURSBERVNUUk9ZRUQnOyB9LCAyMDAwLCBm'
        'YWxzZSkgPj0gMDsKICBGUy5zdGVwKDMwMCk7CiAgci5yZWluZm9yY2VtZW50c09mZldoZW5TaGVz'
        'R29uZSA9IGV2UmVpbmY9PT1mYWxzZTsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNDIgc2hl'
        'IHdpdGhkcmF3czogZmFpbGVkJywgJ209NDInLCBgCiAgRlMuc3RlcCg0MDApOwogIGNvbnN0IHYg'
        'PSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nVjEnKTsKICAvLyBUb28gdG91Z2ggZm9yIHRoZSBP'
        'cmlvbiBhbmQgaGVyIHdpbmdzLCBhbmQgaGVyIG5hdmlnYXRpb24gd2l0aCBpdCAtCiAgLy8gd2l0'
        'aCB0aGF0IHNob3Qgb3V0IHNoZSBjb3VsZCBub3QganVtcCBhdCBhbGwuCiAgdi5ocCA9IHYubWF4'
        'SHAgPSAxZTc7CiAgZm9yKGNvbnN0IHMgb2Ygdi5zdWJzKXsgaWYocy5pZD09PSd3ZWFwb25zJyl7'
        'IHMuZGVhZD10cnVlOyBzLmhwPTA7IH0gZWxzZSBzLmhwID0gcy5tYXhIcCA9IDFlNzsgfQogIGNv'
        'bnN0IHQgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9iakNhcmQudG9uZT09PSdmYWlsJywg'
        'NjAwMCwgdHJ1ZSk7CiAgY29uc3QgciA9IHtmYWlsQ2FyZDogdD49MCAmJiBvYmpDYXJkLnR4dD09'
        'PSdUSEUgSEVDQVRFIFdJVEhEUkVXJywgbm90Q29tcGxldGU6ICEob2JqQ2FyZCAmJiBvYmpDYXJk'
        'LnRvbmU9PT0nZG9uZScpfTsKICBGUy51bnRpbCgoKT0+IWVuZW1pZXMuaW5jbHVkZXModiksIDEw'
        'MDAsIGZhbHNlKTsgRlMuc3RlcCg1MCk7CiAgci5yZWluZk9mZiA9IGV2UmVpbmY9PT1mYWxzZTsK'
        'ICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNMzMgc2F5cyB3aGF0IHRvIGRvJywgJ209MzMnLCBg'
        'CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IG9rMSA9IG1pc3Npb25PYmo9PT0nREVTVFJPWSBUSEUg'
        'RkFVU1RVUyBSRUxBWSc7CiAgY29uc3QgczEgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nUzEn'
        'KTsgczEuaHAgPSAwOyBGUy5zdGVwKDUpOwogIHJldHVybiB7c2F5c1doYXRUb0RvOiBvazEsIGNv'
        'bXBsZXRlQ2FyZDogISFvYmpDYXJkICYmIG9iakNhcmQuaGVhZD09PSdPQkpFQ1RJVkUgQ09NUExF'
        'VEUnICYmIG9iakNhcmQudHh0PT09J1JFTEFZIERFU1RST1lFRCd9O2ApOwoKc2NlbmFyaW8oJ0F1'
        'dG9tYXRpYyBvYmplY3RpdmVzOiBjYXJkLCB0aGVuIHRoZSBsaW5lJywgJ209MzUnLCBgCiAgLy8g'
        'TTM1IHN0YXRlcyBubyBvYmplY3RpdmUgb2YgaXRzIG93bjsgUFJPVEVDVCBUSEUgLi4uIGNvbWVz'
        'IGZyb20gdGhlIGZpZWxkLgogIGNvbnN0IHIgPSB7fTsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9'
        'PnsgZHJhdygpOyByZXR1cm4gISFvYmpDYXJkICYmIG9iakNhcmQuaGVhZD09PSdORVcgT0JKRUNU'
        'SVZFJzsgfSwgMTUwMCwgZmFsc2UpOwogIHIuY2FyZEZvclRoZU5ld09iamVjdGl2ZSA9IHQ+PTAg'
        'JiYgL15QUk9URUNUIFRIRSAvLnRlc3Qob2JqQ2FyZC50eHQpOwogIC8vIEl0cyBjbG9jayBzdGFy'
        'dHMgb25jZSB0aGUganVtcCBpbiBpcyBvdmVyLCBzbyB3YWl0IGZvciBpdCByYXRoZXIgdGhhbgog'
        'IC8vIGNvdW50IHN0ZXBzLgogIHIuY2FyZEdvZXNBZ2FpbiA9IEZTLnVudGlsKCgpPT57IGRyYXco'
        'KTsgcmV0dXJuIG9iakNhcmQ9PT1udWxsOyB9LCBPQkpfQ0FSRF9USU1FKjMsIGZhbHNlKSA+PSAw'
        'OwogIHIubGluZUtlZXBzSXQgPSAvXlBST1RFQ1QgVEhFIC8udGVzdChvYmpQaW5uZWQpOwogIHJl'
        'dHVybiByO2ApOwoKc2NlbmFyaW8oJ05ldyBsb29rOiBubyBDb3VyaWVyIGxlZnQgaW4gdGhlc2Un'
        'LCAnbT0zNicsIGAKICBGUy5zdGVwKDcwMCk7CiAgc2hvd0ZwcyA9IHRydWU7IHNob3dPYmogPSB0'
        'cnVlOwogIGNvbnN0IHVzZWQgPSBbXTsgY29uc3Qgb2YgPSBjdHguZmlsbFRleHQ7CiAgbGV0IGlu'
        'c2lkZSA9IDA7CiAgY29uc3Qgd3JhcCA9IG5hbWU9PnsgY29uc3QgZiA9IHdpbmRvd1tuYW1lXTsg'
        'd2luZG93W25hbWVdID0gZnVuY3Rpb24oKXsgaW5zaWRlKys7IHRyeXsgcmV0dXJuIGYuYXBwbHko'
        'dGhpcywgYXJndW1lbnRzKTsgfSBmaW5hbGx5eyBpbnNpZGUtLTsgfSB9OyB9OwogIFsnZHJhd0Zp'
        'ZWxkQmFubmVyJywnZHJhd0ZsZWVXYXJuaW5nJywnZHJhd0ZwcycsJ2RyYXdPYmpDb3VudCcsJ2Ry'
        'YXdQYXVzZWQnXS5mb3JFYWNoKHdyYXApOwogIGN0eC5maWxsVGV4dCA9IGZ1bmN0aW9uKCl7IGlm'
        'KGluc2lkZSkgdXNlZC5wdXNoKGN0eC5mb250KTsgcmV0dXJuIG9mLmFwcGx5KHRoaXMsIGFyZ3Vt'
        'ZW50cyk7IH07CiAgb2JqQW5ub3VuY2UoJ05FVyBPQkpFQ1RJVkUnLCAnVEVTVCcsICduZXcnKTsg'
        'b2JqQ2FyZC50MCA9IGZjIC0gNDA7CiAgZHJhdygpOwogIHVzZXJQYXVzZWQgPSB0cnVlOyBzeW5j'
        'UGF1c2UoKTsgZHJhdygpOwogIGN0eC5maWxsVGV4dCA9IG9mOwogIHJldHVybiB7c29tZXRoaW5n'
        'RHJhd246IHVzZWQubGVuZ3RoPj00LCBmbGVlU2hvd246IGZsZWVpbmdFbmVtaWVzKCkubGVuZ3Ro'
        'PjAsIG5vQ291cmllcjogdXNlZC5ldmVyeShmPT4hL0NvdXJpZXIvLnRlc3QoZikpfTtgKTsKCnNj'
        'ZW5hcmlvKCdDb2xvc3N1cyBiZWFtcyBhcmUgVGVycmFuJywgJycsIGAKICByZXR1cm4ge21haW46'
        'IGJlYW1Db2woJ2d0dmEnLCB0cnVlKT09PScjMDBmZjU1JywgYW50aUZpZ2h0ZXI6IGJlYW1Db2wo'
        'J2d0dmEnLCBmYWxzZSk9PT0nIzQ0OTlmZid9O2AsIHRydWUpOwoKc2NlbmFyaW8oJ0hvTCBzdGFy'
        'dCB1bmNoYW5nZWQnLCAnbT0xJywgYAogIHJldHVybiB7d2F2ZTogd2F2ZSwgdGhvdGg6IHBsYXll'
        'ci5zaGlwPT09J2ZpdG90aCcsIHZhc3VkYW5DYWxsOiBBTExZX0ZBQ19PTi52YXN1ZGFuPT09dHJ1'
        'ZSAmJiBBTExZX0ZBQ19PTi50ZXJyYW49PT1mYWxzZX07YCk7CgovLyDilIDilIAgUnVubmVyIOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgAooYXN5bmMoKT0+ewogIGNvbnN0IGJyb3dzZXIgPSBhd2FpdCBjaHJvbWl1bS5s'
        'YXVuY2goKTsKICBsZXQgZmFpbHMgPSAwOwogIGNvbnN0IG9ubHkgPSBwcm9jZXNzLmFyZ3ZbNF07'
        'CiAgZm9yKGNvbnN0IHNjIG9mIHNjZW5hcmlvcyl7CiAgICBpZihvbmx5ICYmIHNjLm5hbWUuaW5k'
        'ZXhPZihvbmx5KTwwKSBjb250aW51ZTsKICAgIGNvbnN0IHBhZ2UgPSBhd2FpdCBicm93c2VyLm5l'
        'd1BhZ2UoKTsKICAgIGNvbnN0IGVycnMgPSBbXTsKICAgIHBhZ2Uub24oJ3BhZ2VlcnJvcicsIGU9'
        'PmVycnMucHVzaChTdHJpbmcoZS5tZXNzYWdlfHxlKSkpOwogICAgYXdhaXQgcGFnZS5nb3RvKCdm'
        'aWxlOi8vJyArIHRtcCArICc/JyArIHNjLnF1ZXJ5KTsKICAgIGF3YWl0IHBhZ2Uud2FpdEZvclRp'
        'bWVvdXQoMzAwKTsKICAgIGxldCByZXM7CiAgICB0cnl7CiAgICAgIHJlcyA9IGF3YWl0IHBhZ2Uu'
        'ZXZhbHVhdGUoSEVMUEVSUyArIGBcbkZTLmZha2VJbWFnZXMoKTtgICsgKHNjLm5vTGF1bmNoID8g'
        'JycgOiAnIGxhdW5jaEdhbWUoKTsnKSArIGBcbihmdW5jdGlvbigpeyR7c2MuYm9keX19KSgpYCk7'
        'CiAgICB9Y2F0Y2goZSl7IHJlcyA9IG51bGw7IGVycnMucHVzaChTdHJpbmcoZS5tZXNzYWdlfHxl'
        'KSk7IH0KICAgIGNvbnNvbGUubG9nKHNjLm5hbWUgKyAnICAoPycgKyBzYy5xdWVyeSArICcpJyk7'
        'CiAgICBpZihyZXMpIGZvcihjb25zdCBbayx2XSBvZiBPYmplY3QuZW50cmllcyhyZXMpKXsKICAg'
        'ICAgY29uc3QgZ29vZCA9ICh0eXBlb2Ygdj09PSdib29sZWFuJykgPyB2IDogdHJ1ZTsKICAgICAg'
        'aWYoIWdvb2QpIGZhaWxzKys7CiAgICAgIGNvbnNvbGUubG9nKChnb29kID8gJyAgb2sgICAgJyA6'
        'ICcgIEZBSUwgICcpICsgayArICh0eXBlb2Ygdj09PSdib29sZWFuJyA/ICcnIDogJyA9ICcgKyBK'
        'U09OLnN0cmluZ2lmeSh2KSkpOwogICAgfQogICAgaWYoZXJycy5sZW5ndGgpeyBmYWlscysrOyBj'
        'b25zb2xlLmxvZygnICBGQUlMICBwYWdlIGVycm9yczpcbiAgICAnICsgZXJycy5zbGljZSgwLDQp'
        'LmpvaW4oJ1xuICAgICcpKTsgfQogICAgYXdhaXQgcGFnZS5jbG9zZSgpOwogIH0KICBhd2FpdCBi'
        'cm93c2VyLmNsb3NlKCk7CiAgZnMudW5saW5rU3luYyh0bXApOwogIGNvbnNvbGUubG9nKCdcbicg'
        'KyAoZmFpbHMgPyBmYWlscyArICcgRkFJTEVEJyA6ICdhbGwgcGFzc2VkJykpOwogIHByb2Nlc3Mu'
        'ZXhpdChmYWlscyA/IDEgOiAwKTsKfSkoKTsK'
    ),
}
for name, data in TEST_FILES.items():
    open(name, 'wb').write(base64.b64decode(data))
print("v133 applied: objectives, M33/M38/M40/M42, hull bars, Colossus beams, checks updated. Now run: python3 assemble.py 133")
