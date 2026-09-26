#!/usr/bin/env python3
"""FS3 v134 - messages and hull bars in the new look.

MESSAGES
  What concerns the whole fight no longer appears in the middle of the
  field. It goes into a small column on the left, under the objective
  line: at most three, each for about three seconds, newest on top, from
  the same kit as everything else. That is: hulls and weapons becoming
  available, the mission's radio lines (e.g. "GTD Orion inbound - hangar
  open"), REARMED, the new hull after a switch, ENEMY COMMS DOWN, BOSS
  DISARMED.
  What belongs to one ship stays at that ship - DOCKED, TURNING HOSTILE,
  TARGET ESCAPED, a subsystem destroyed, a ticket picked up - but smaller,
  quieter, without the black box, and in the forum's type.

HULL BARS
  The row of blocks becomes one narrow band with slanted ends, like the
  plates of the interface. The colour runs smoothly from green through
  yellow to red. Normally the band is half transparent; when the ship
  takes a hit it comes up to full for two seconds and settles again. A
  ship close to death stays at full and pulses. The subsystem symbols
  above it are unchanged.

TYPE
  The last Courier is gone from the field: ship names, the subsystem under
  the pointer, pickups (1UP and the ticket letters), SENSOR FAULT, the
  loading line.

Needs v133. Edits src/30_waves.js, src/40_world.js, src/50_combat.js and
src/70_ui.js in place, and writes the updated shipsim.js and fieldsim.js. Run assemble.py
afterwards.
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
ui = load("src/70_ui.js")

# ══ Messages that concern the whole fight go to the column ═════════════
wv = replace_once(
    wv,
    "  SUB_MSGS.push({x:W/2, y:H*0.42, txt:'ENEMY COMMS DOWN', life:200, ml:200, ally:true});\n",
    "  notice('ENEMY COMMS DOWN', 'good');\n",
    "notice: comms down")

wv = replace_once(
    wv,
    "      SUB_MSGS.push({x:W/2, y:H*0.40, txt:String(arg||'').toUpperCase(),\n"
    "                     life:200, ml:200, ally:true});\n",
    "      notice(String(arg||'').toUpperCase(), 'info');\n",
    "notice: meldung")

wo = replace_once(
    wo,
    "    SUB_MSGS.push({x:e.x, y:e.y-40, txt:'BOSS DISARMED', life:420, ml:420, ally:false});\n",
    "    notice('BOSS DISARMED', 'good');\n",
    "notice: boss disarmed")

ui = replace_once(
    ui,
    "    SUB_MSGS.push({x:W/2, y:H*0.34, txt:s.name.toUpperCase()+' AVAILABLE', life:260, ml:260, ally:true});\n",
    "    notice(s.name.toUpperCase()+' AVAILABLE', 'unlock');\n",
    "notice: hull available")

ui = replace_once(
    ui,
    "    SUB_MSGS.push({x:W/2, y:H*0.40, txt:weaponName(w).toUpperCase()+' AVAILABLE',\n"
    "                   life:260, ml:260, ally:true});\n",
    "    notice(weaponName(w).toUpperCase()+' AVAILABLE', 'unlock');\n",
    "notice: weapon available")

ui = replace_once(
    ui,
    "  SUB_MSGS.push({x:player.x+60, y:player.y-30, txt:weaponName(w).toUpperCase()+'  REARMED',\n"
    "                 life:170, ml:170, ally:true});\n",
    "  notice(weaponName(w).toUpperCase()+' REARMED', 'good');\n",
    "notice: rearmed")

ui = replace_once(
    ui,
    "  SUB_MSGS.push({x:player.x+60, y:player.y-30,\n"
    "                 txt:PLAYER_SHIPS[i].name.toUpperCase()+(again?'  NO REFIT':''),\n"
    "                 life:170, ml:170, ally:true});\n",
    "  notice(PLAYER_SHIPS[i].name.toUpperCase()+(again?' - NO REFIT':''), 'good');\n",
    "notice: ship switch")

# ── The column itself, drawn under the objective line ──────────────────
ui = replace_once(
    ui,
    "  if(pin && arriveT<=0 && !(cardUp && objCard.tone==='new' && objCard.txt===pin.txt)) drawObjLine(pin);\n"
    "  drawObjCard();\n"
    "}\n",
    "  const lineUp = pin && arriveT<=0 && !(cardUp && objCard.tone==='new' && objCard.txt===pin.txt);\n"
    "  if(lineUp) drawObjLine(pin);\n"
    "  drawNotices(HUD_H + 6 + (lineUp ? 26 : 0));\n"
    "  drawObjCard();\n"
    "}\n"
    "// ── NOTICES ──────────────────────────────────────────────────\n"
    "// What concerns the whole fight rather than one ship: a hull or weapon\n"
    "// becoming available, a radio line from the mission, a refit. A small\n"
    "// column under the objective line, never in the middle of the field.\n"
    "// Newest on top, at most NOTICE_MAX, each for NOTICE_TIME steps. Steps\n"
    "// of the game, so a pause holds them.\n"
    "const NOTICE_TIME = 320, NOTICE_FADE = 40, NOTICE_IN = 10, NOTICE_MAX = 3;\n"
    "const NOTICE_TONE = {unlock:null, info:'#7fd6ff', good:'#4dff88', bad:'#ff5533'};\n"
    "let NOTICES = [];\n"
    "function notice(txt, tone){\n"
    "  NOTICES.unshift({txt:String(txt), tone:tone||'info', t0:fc});\n"
    "  if(NOTICES.length > NOTICE_MAX) NOTICES.length = NOTICE_MAX;\n"
    "}\n"
    "function drawNotices(y0){\n"
    "  for(let i=NOTICES.length-1;i>=0;i--) if(fc-NOTICES[i].t0 >= NOTICE_TIME) NOTICES.splice(i,1);\n"
    "  let y = y0;\n"
    "  for(const n of NOTICES){\n"
    "    const age = fc - n.t0;\n"
    "    let a = 1;\n"
    "    if(age < NOTICE_IN) a = age/NOTICE_IN;\n"
    "    else if(age > NOTICE_TIME-NOTICE_FADE) a = (NOTICE_TIME-age)/NOTICE_FADE;\n"
    "    ctx.save();\n"
    "    ctx.globalAlpha = Math.max(0, a);\n"
    "    ctx.font = thValue(11, true);\n"
    "    const txt = thFit(n.txt, 360);\n"
    "    const pw = Math.round(ctx.measureText(txt).width + 24), ph = 18;\n"
    "    thPlate(8, y, pw, ph, thRGBA('panelBack', 0.62), 4);\n"
    "    // The mark on the left says what kind of news it is.\n"
    "    ctx.fillStyle = NOTICE_TONE[n.tone] || TH('accentWarm');\n"
    "    ctx.fillRect(13, y+4, 2, ph-8);\n"
    "    ctx.fillStyle = TH('text'); ctx.textAlign='left'; ctx.textBaseline='middle';\n"
    "    ctx.fillText(txt, 20, y+ph/2+1);\n"
    "    ctx.restore();\n"
    "    y += ph + 4;\n"
    "  }\n"
    "  ctx.textAlign='left'; ctx.textBaseline='top';\n"
    "}\n",
    "notices: column")

# Cleared with everything else at the start of a wave? No: a hull that
# became available at the end of a wave is still news in the next one.
# Cleared on a new run only.
ui = replace_once(
    ui,
    "function toTitleOrLaunch(){\n",
    "function toTitleOrLaunch(){\n"
    "  NOTICES = [];\n",
    "notices: new run")

# ══ Marks at a ship: quieter, in the forum's type ═════════════════════
wo = replace_once(
    wo,
    "    ctx.globalAlpha=Math.min(1,t*4);\n"
    "    ctx.font='bold 10px Courier New';\n"
    "    ctx.textAlign='center'; ctx.textBaseline='middle';\n"
    "    const y=m.y-(1-t)*30;\n"
    "    const tw=ctx.measureText(m.txt).width;\n"
    "    ctx.fillStyle='#100600';\n"
    "    ctx.fillRect((m.x-tw/2-5)|0,(y-8)|0,(tw+10)|0,16);\n",
    "    // Smaller and quieter than before: no box, a dark edge around the\n"
    "    // letters for contrast, and a shorter rise.\n"
    "    ctx.globalAlpha=Math.min(1,t*4)*0.92;\n"
    "    ctx.font=thValue(10, true);\n"
    "    ctx.textAlign='center'; ctx.textBaseline='middle';\n"
    "    const y=m.y-(1-t)*18;\n"
    "    ctx.lineWidth=3; ctx.strokeStyle='rgba(0,0,0,0.75)'; ctx.lineJoin='round';\n"
    "    ctx.strokeText(m.txt,m.x,y);\n",
    "sub msgs: quieter")

wo = replace_once(
    wo,
    "    ctx.globalAlpha=Math.min(1, t*2.2);\n"
    "    ctx.font='bold 11px Courier New';\n"
    "    ctx.textAlign='center'; ctx.textBaseline='middle';\n"
    "    const y=m.y-(1-t)*34;\n"
    "    ctx.fillStyle='#001018';\n"
    "    const w=ctx.measureText('+1 '+(TICKET_NAME[m.kind]||'')).width;\n"
    "    ctx.fillRect((m.x-w/2-6)|0,(y-9)|0,(w+12)|0,18);\n"
    "    ctx.fillStyle=m.rep?REPAIR_COL:'#8fe4ff';\n"
    "    ctx.fillText((m.kind==='repair'?'+':'+1 ')+(TICKET_NAME[m.kind]||''), m.x, y);\n",
    "    ctx.globalAlpha=Math.min(1, t*2.2)*0.92;\n"
    "    ctx.font=thValue(10, true);\n"
    "    ctx.textAlign='center'; ctx.textBaseline='middle';\n"
    "    const y=m.y-(1-t)*20;\n"
    "    const tt=(m.kind==='repair'?'+':'+1 ')+(TICKET_NAME[m.kind]||'');\n"
    "    ctx.lineWidth=3; ctx.strokeStyle='rgba(0,0,0,0.75)'; ctx.lineJoin='round';\n"
    "    ctx.strokeText(tt, m.x, y);\n"
    "    ctx.fillStyle=m.rep?REPAIR_COL:'#8fe4ff';\n"
    "    ctx.fillText(tt, m.x, y);\n",
    "ticket msgs: quieter")

# ══ Hull band ══════════════════════════════════════════════════════════
wo = replace_between(
    wo,
    "function drawHullBlocks(e, bx, by, bw, ratio, showShield){\n",
    "  // Subsysteme, dieselben Symbole wie auf dem Rumpf - aber OBERHALB des\n",
    "// ── HULL BAND ────────────────────────────────────────────────\n"
    "// One narrow band with slanted ends, like the plates of the interface.\n"
    "// Calm by default: half transparent. A hit brings it up to full for\n"
    "// HB_HOT steps and it settles again; a ship close to death stays full\n"
    "// and pulses. Hits are noticed from the hull (or shield) going down, so\n"
    "// every source of damage counts, enemy and allied alike.\n"
    "const HB_H = 4, HB_SLANT = 3, HB_CALM = 0.5, HB_HOT = 200;\n"
    "// Green through yellow to red, smoothly rather than in steps.\n"
    "function hullBandCol(r){\n"
    "  const g=[60,224,106], y=[255,204,68], d=[255,74,51];\n"
    "  const t = Math.max(0, Math.min(1, r));\n"
    "  const a = t>0.5 ? y : d, b = t>0.5 ? g : y, k = t>0.5 ? (t-0.5)*2 : t*2;\n"
    "  return 'rgb('+Math.round(a[0]+(b[0]-a[0])*k)+','+Math.round(a[1]+(b[1]-a[1])*k)+','\n"
    "        +Math.round(a[2]+(b[2]-a[2])*k)+')';\n"
    "}\n"
    "function hullBandPath(x, y, w){\n"
    "  ctx.beginPath();\n"
    "  ctx.moveTo(x+HB_SLANT, y); ctx.lineTo(x+w, y);\n"
    "  ctx.lineTo(x+w-HB_SLANT, y+HB_H); ctx.lineTo(x, y+HB_H);\n"
    "  ctx.closePath();\n"
    "}\n"
    "function drawHullBlocks(e, bx, by, bw, ratio, showShield){\n"
    "  if(e.invuln) return;\n"
    "  const cur = showShield ? e.bShield : e.hp;\n"
    "  if(e._hbLast!=null && cur < e._hbLast) e._hbHit = fc;\n"
    "  e._hbLast = cur;\n"
    "  const hot = (e._hbHit!=null) ? Math.max(0, 1-(fc-e._hbHit)/HB_HOT) : 0;\n"
    "  const crit = (ratio<=HULL_CRIT && !showShield);\n"
    "  let a = crit ? 1 : HB_CALM + (1-HB_CALM)*hot;\n"
    "  e._hbAlpha = a;\n"
    "  const w = Math.max(24, Math.round(bw)), x0 = Math.round(e.x - w/2), y = Math.round(by);\n"
    "  ctx.save();\n"
    "  ctx.globalAlpha = a;\n"
    "  hullBandPath(x0, y, w);\n"
    "  ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fill();\n"
    "  // The fill, clipped to the band so the slant holds at both ends.\n"
    "  ctx.save();\n"
    "  hullBandPath(x0, y, w); ctx.clip();\n"
    "  if(crit) ctx.globalAlpha = 0.55 + 0.45*Math.sin(fc*0.22);\n"
    "  ctx.fillStyle = showShield ? '#6fd8ff' : hullBandCol(ratio);\n"
    "  ctx.fillRect(x0, y, Math.max(0, Math.min(1, ratio))*w, HB_H);\n"
    "  ctx.restore();\n"
    "  // The edge says the side, as before: blue ours, red theirs.\n"
    "  hullBandPath(x0-0.5, y-0.5, w+1);\n"
    "  ctx.lineWidth = 1;\n"
    "  ctx.strokeStyle = (e.side==='ally') ? 'rgba(120,190,255,0.7)' : 'rgba(255,110,90,0.7)';\n"
    "  ctx.stroke();\n"
    "  ctx.restore();\n"
    "\n",
    "hull band")

# Ship name above the band: the forum's type, not Courier.
wo = replace_once(
    wo,
    "    ctx.font = 'bold 9px Courier New';\n"
    "    ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';\n"
    "    ctx.globalAlpha = 0.85;\n",
    "    ctx.font = thLabel(9);\n"
    "    ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';\n"
    "    ctx.globalAlpha = 0.85;\n",
    "ship name type")

# The subsystem under the pointer: same treatment as the marks.
wo = replace_once(
    wo,
    "    ctx.font='bold 9px Courier New';\n"
    "    ctx.textAlign='center'; ctx.textBaseline='bottom';\n"
    "    const tw=ctx.measureText(near.label).width;\n"
    "    ctx.globalAlpha=0.7; ctx.fillStyle='#000';\n"
    "    ctx.fillRect((nearP.x-tw/2-4)|0,(nearP.y-25)|0,(tw+8)|0,13);\n"
    "    ctx.globalAlpha=1;\n",
    "    ctx.font=thLabel(9);\n"
    "    ctx.textAlign='center'; ctx.textBaseline='bottom';\n"
    "    ctx.lineWidth=3; ctx.strokeStyle='rgba(0,0,0,0.75)'; ctx.lineJoin='round';\n"
    "    ctx.strokeText(near.label,nearP.x,nearP.y-13);\n",
    "subsystem name type")

# Pickups: 1UP and the ticket letters.
wo = replace_once(
    wo,
    "      ctx.fillStyle=REPAIR_COL;\n"
    "      ctx.font='bold 10px Courier New';\n",
    "      ctx.fillStyle=REPAIR_COL;\n"
    "      ctx.font=thValue(10, true);\n",
    "pickup 1UP type")
wo = replace_once(
    wo,
    "      ctx.fillStyle='#bfefff';\n"
    "      ctx.font='bold 10px Courier New';\n",
    "      ctx.fillStyle='#bfefff';\n"
    "      ctx.font=thValue(10, true);\n",
    "pickup ticket type")

cb = replace_once(
    cb,
    "    ctx.fillStyle='#ffdd44'; ctx.font='bold 9px Courier New';\n",
    "    ctx.fillStyle='#ffdd44'; ctx.font=thLabel(9);\n",
    "sensor fault type")

ui = replace_once(
    ui,
    "    ctx.fillStyle='#00ff88';ctx.font='16px Courier New';\n",
    "    ctx.fillStyle=TH('text');ctx.font=thValue(16, false);\n",
    "loading type")

open("src/30_waves.js", "w", encoding="utf-8").write(wv)
open("src/40_world.js", "w", encoding="utf-8").write(wo)
open("src/50_combat.js", "w", encoding="utf-8").write(cb)
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
        'ck9yZGVyJywnaW5zaWRlUGFuZWwnLCdjeWNsZUF0JywnZW50ZXJDeWNsZScsJ3RpdGxlRnNIaXQn'
        'LAogICd0aENoYW1mZXJQYXRoJywndGhQbGF0ZScsJ3RoR2xvd1BhdGgnLCd0aEJyYWNrZXRzJywn'
        'dGhTY2FsZScsJ3RoRnJhbWUnLCd0aFJHQkEnLCd0aEdsb3NzJywndGhDdXRHbGludCcsCiAgJ1RI'
        'JywndGhMYWJlbCcsJ3RoVmFsdWUnLCd0aEJldmVsJywndGhHbG93JywndGhQYW5lbCcsJ3RoQnV0'
        'dG9uJywndGhEaXZpZGVyJywnZHJhd1N3YXBJY29uJywnVUknLCd1aUhMUCcsJ3VpTGFiZWwnLCd1'
        'aVZhbHVlJywndWlDZWxsJywndWlEaWFsb2cnXTsKY29uc3Qga2V5SGFuZGxlciA9IGJldHdlZW4o'
        'ImRvY3VtZW50LmFkZEV2ZW50TGlzdGVuZXIoJ2tleWRvd24nLGZ1bmN0aW9uKGV2KXtcbiAgaWYo'
        'R1MhPT0ncGxheWluZycpIHJldHVybjsiKTsKY29uc3QgZG93blN0YXJ0ID0gc3JjLmluZGV4T2Yo'
        'IkNWUy5hZGRFdmVudExpc3RlbmVyKCdtb3VzZWRvd24nLCIpOwpjb25zdCBtb3VzZUhhbmRsZXIg'
        'PSBzcmMuc2xpY2Uoc3JjLmluZGV4T2YoJ2Z1bmN0aW9uJywgZG93blN0YXJ0KSwgYmxvY2tFbmQo'
        'c3JjLCBzcmMuaW5kZXhPZignZnVuY3Rpb24nLCBkb3duU3RhcnQpKSk7CmNvbnN0IGxhdW5jaCA9'
        'IGZuKCdsYXVuY2hHYW1lJyk7Cgpjb25zdCBDQUxMUyA9IFtdOwpjb25zdCBjdHhTdHViID0gbmV3'
        'IFByb3h5KHt9LCB7CiAgZ2V0Oih0LGspPT4gayBpbiB0ID8gdFtrXSA6IGZ1bmN0aW9uKCl7CiAg'
        'ICBDQUxMUy5wdXNoKHtmbjpTdHJpbmcoayksIGFyZ3M6W10uc2xpY2UuY2FsbChhcmd1bWVudHMp'
        'fSk7CiAgICAvLyBjcmVhdGVMaW5lYXJHcmFkaWVudCBoYXMgdG8gaGFuZCBiYWNrIHNvbWV0aGlu'
        'ZyB3aXRoIGFkZENvbG9yU3RvcC4KICAgIGlmKGs9PT0nY3JlYXRlTGluZWFyR3JhZGllbnQnKSBy'
        'ZXR1cm4ge2FkZENvbG9yU3RvcDpmdW5jdGlvbigpe319OwogICAgLy8gdGhGaXQgbWVhc3VyZXMg'
        'YmVmb3JlIGl0IGN1dHMsIHNvIHRoZSBzdHViIGhhcyB0byBhbnN3ZXIgd2l0aCBhIHdpZHRoLgog'
        'ICAgLy8gUm91Z2hseSAwLjU1IG9mIHRoZSBzZXQgcG9pbnQgc2l6ZSBwZXIgY2hhcmFjdGVyIGlz'
        'IGNsb3NlIGVub3VnaCBmb3IKICAgIC8vIHRoZSBsYXlvdXQgZGVjaXNpb25zIGJlaW5nIGNoZWNr'
        'ZWQgaGVyZS4KICAgIGlmKGs9PT0nbWVhc3VyZVRleHQnKXsKICAgICAgY29uc3QgcHggPSBwYXJz'
        'ZUZsb2F0KFN0cmluZyh0LmZvbnR8fCcxMHB4JykucmVwbGFjZSgvXmJvbGRccysvLCcnKSkgfHwg'
        'MTA7CiAgICAgIHJldHVybiB7d2lkdGg6IFN0cmluZyhhcmd1bWVudHNbMF18fCcnKS5sZW5ndGgg'
        'KiBweCAqIDAuNTV9OwogICAgfQogIH0sCiAgc2V0Oih0LGssdik9PnsgQ0FMTFMucHVzaCh7Zm46'
        'J3NldCAnK1N0cmluZyhrKSwgYXJnczpbdl19KTsgdFtrXT12OyByZXR1cm4gdHJ1ZTsgfQp9KTsK'
        'Ly8gSGVscGVycyBvdmVyIHRoZSByZWNvcmRlZCBkcmF3aW5nIGNhbGxzLgpjb25zdCBDTFIgICAg'
        'PSAoKT0+eyBDQUxMUy5sZW5ndGggPSAwOyB9Owpjb25zdCBkcmF3cyAgPSAoKT0+IENBTExTLmZp'
        'bHRlcihjPT5jLmZuPT09J2RyYXdJbWFnZScpOwpjb25zdCBjbGlwcyAgPSAoKT0+IENBTExTLmZp'
        'bHRlcihjPT5jLmZuPT09J2NsaXAnKTsKY29uc3QgYWxwaGFzID0gKCk9PiBDQUxMUy5maWx0ZXIo'
        'Yz0+Yy5mbj09PSdzZXQgZ2xvYmFsQWxwaGEnKS5tYXAoYz0+Yy5hcmdzWzBdKTsKLy8gRXZlcnkg'
        'c3ByaXRlIGhhcyB0byBzaXQgaW5zaWRlIGEgc2F2ZS9yZXN0b3JlIHBhaXIsIG90aGVyd2lzZSBp'
        'dHMgY2xpcCBhbmQKLy8gaXRzIGFscGhhIGxlYWsgaW50byB3aGF0ZXZlciBpcyBkcmF3biBuZXh0'
        'LgpmdW5jdGlvbiBiYWxhbmNlZCgpewogIGxldCBkID0gMCwgb2tBbGwgPSB0cnVlOwogIGZvcihj'
        'b25zdCBjIG9mIENBTExTKXsKICAgIGlmKGMuZm49PT0nc2F2ZScpIGQrKzsKICAgIGVsc2UgaWYo'
        'Yy5mbj09PSdyZXN0b3JlJyl7IGQtLTsgaWYoZDwwKSBva0FsbD1mYWxzZTsgfQogICAgZWxzZSBp'
        'ZigoYy5mbj09PSdkcmF3SW1hZ2UnIHx8IGMuZm49PT0nY2xpcCcpICYmIGQ8MSkgb2tBbGw9ZmFs'
        'c2U7CiAgfQogIHJldHVybiBva0FsbCAmJiBkPT09MDsKfQoKY29uc3Qgd29ybGQgPSBgCiAgY29u'
        'c3QgVz04MDAsSD01MDAsSFVEX0g9NTQsIFBMQVlFUl9TUERfRklHSFRFUj0zLjIsIFBMQVlFUl9T'
        'UERfQk9NQkVSPTIuNCwgUExBWUVSX1RVUk49MC4xNDsKICBsZXQgRlMxX01PREU9ZmFsc2UsIEdT'
        'PSdwbGF5aW5nJywgcGF1c2VkPWZhbHNlLCBjYWxsTWVudT1mYWxzZSwgd2F2ZT0xLCBzY29yZT0w'
        'LCBhbGxpZXM9W10sIGp1bXA9ZmFsc2U7CiAgbGV0IHNldHRpbmdzT3Blbj1mYWxzZSwgdXNlclBh'
        'dXNlZD1mYWxzZTsKICBsZXQgU1VCX01TR1M9W10sIE1PVVNFPXt4OjAseTowfSwgbGl2ZXM9Mywg'
        'cGxheWVyPXt4OjEwMCx5OjIwMCxodWxsTXVsdDoxfTsKICAvLyBOb3RpY2VzIGdvIHRvIHRoZSBj'
        'b2x1bW4gdW5kZXIgdGhlIG9iamVjdGl2ZSBsaW5lOyB0aGUgY29sdW1uIGl0c2VsZgogIC8vIGlz'
        'IG5vdCB1bmRlciB0ZXN0IGhlcmUsIG9ubHkgd2hhdCBpcyBhbm5vdW5jZWQuCiAgbGV0IE5PVElD'
        'RV9MT0c9W107IGZ1bmN0aW9uIG5vdGljZSh0LCB0b25lKXsgTk9USUNFX0xPRy5wdXNoKHt0eHQ6'
        'dCwgdG9uZTp0b25lfSk7IH0KICBsZXQgZXJhT2ZmPWZhbHNlLCBJTUdTPXt9LCBpc0ZpcmluZz1m'
        'YWxzZSwgbGF1bmNoZWQ9MDsKICBjb25zdCBjdHg9Q1RYLCBkb2N1bWVudD17Ym9keTp7Y2xhc3NM'
        'aXN0OnthZGQoKXt9LHJlbW92ZSgpe319fSwgZ2V0RWxlbWVudEJ5SWQoKXtyZXR1cm4ge3N0eWxl'
        'Ont9fTt9fTsKICBjb25zdCB3aW5kb3c9e307CiAgZnVuY3Rpb24gaW5KdW1wKCl7cmV0dXJuIGp1'
        'bXA7fSBmdW5jdGlvbiBlcmFTaGllbGRzT2ZmKCl7cmV0dXJuIGVyYU9mZjt9CiAgZnVuY3Rpb24g'
        'c2V0U2V0dGluZ3MoKXt9IGZ1bmN0aW9uIHRvZ2dsZUZ1bGxzY3JlZW4oKXt9IGZ1bmN0aW9uIHJl'
        'ZmluZVRpY2tldCgpe30gZnVuY3Rpb24gY2FsbEFsbHkoKXt9CiAgZnVuY3Rpb24gYWxseVJlYWR5'
        'KCl7cmV0dXJuIHRydWU7fSBmdW5jdGlvbiB0b2dnbGVDYWxsTWVudSgpe30gZnVuY3Rpb24gdG9H'
        'Qyh4LHkpe3JldHVybiB7eDp4LHk6eX07fQogIGxldCBzaGlwVW5sb2NrZWQ9MSwgc2hpcFN3YXBX'
        'YXZlPS0xLCBzaGlwTWVudT1mYWxzZSwgZ2FtZU92ZXJBdD0wOwogIGNvbnN0IEFMTFlfS0VZUz1b'
        'XSwgQUxMWV9PUkRFUj1bXSwgQUxMWV9TUEVDSUFMPSd4JywgQUxMWV9TUEVDSUFMX0tFWT0nUSc7'
        'CiAgJHtodWxsRmFjRGVjbH0KICAke3dwbkRlY2x9CiAgJHt3cG5EZWNsMn0KICAke3JtRGVjbH0K'
        'ICAke3dwblN0YXRlfQogICR7dGhlbWVzRGVjbH0KICBsZXQgRUNPPXtodWQ6J2hscCcsIHNjaGVt'
        'ZTonZmlyZSd9OwogICR7bWVudUJnRGVjbH0KICAke2hhbmdhckRlY2x9CiAgJHt2b2xsZXlEZWNs'
        'fQogIGxldCBNT1VOVFM9e307CiAgJHtzaGlwc0RlY2x9CiAgbGV0IFVJX1NISVBTPTE7CiAgJHtm'
        'YWNPbkRlY2x9CiAgJHtjeWNsZURlY2x9CiAgJHtuYW1lcy5tYXAoZm4pLmpvaW4oJ1xuJyl9CiAg'
        'Y29uc3Qgb25LZXkgPSAke2tleUhhbmRsZXJ9OwogIGNvbnN0IG9uRG93biA9ICR7bW91c2VIYW5k'
        'bGVyfTsKICByZXR1cm4gewogICAgZ2V0OihrKT0+ZXZhbChrKSwgc2V0OihrLHYpPT5ldmFsKGsr'
        'Jz12JyksIHJ1bjooY29kZSk9PmV2YWwoY29kZSkKICB9O2A7CmNvbnN0IFcgPSBuZXcgRnVuY3Rp'
        'b24oJ0NUWCcsIHdvcmxkKShjdHhTdHViKTsKbGV0IGZhaWxzID0gMDsKZnVuY3Rpb24gb2sobGFi'
        'ZWwsIGNvbmQpeyBjb25zb2xlLmxvZygoY29uZD8nICBvayAgICAnOicgIEZBSUwgICcpK2xhYmVs'
        'KTsgaWYoIWNvbmQpIGZhaWxzKys7IH0KY29uc3QgUCA9ICgpPT5XLmdldCgncGxheWVyJyk7CmNv'
        'bnN0IHJlc2V0ID0gKCk9PnsgVy5ydW4oIkdTPSdwbGF5aW5nJztwYXVzZWQ9ZmFsc2U7cmVzdW1l'
        'SG9sZD1mYWxzZTtjYWxsTWVudT1mYWxzZTtzaGlwTWVudT1mYWxzZTt3YXZlPTE7c2NvcmU9MDth'
        'bGxpZXM9W107anVtcD1mYWxzZTtGUzFfTU9ERT1mYWxzZTtzaGlwVW5sb2NrZWQ9MTtzaGlwU3dh'
        'cFdhdmU9LTE7U1VCX01TR1M9W107Tk9USUNFX0xPRz1bXTtwbGF5ZXI9e3g6MTAwLHk6MjAwLGh1'
        'bGxNdWx0OjF9O2FwcGx5U2hpcChQTEFZRVJfU0hJUFNbMF0ua2V5KSIpOyB9Owpjb25zdCBkZXN0'
        'cm95ZXIgPSAobyk9Pk9iamVjdC5hc3NpZ24oe2ltZzonZGVoYXRzaGVwc3V0Jywgc21hbGw6ZmFs'
        'c2UsIGRlYWQ6ZmFsc2UsIHdhcnBPdXQ6ZmFsc2V9LCBvfHx7fSk7Cgpjb25zb2xlLmxvZygnU3Rh'
        'cnQgc2hpcCcpOwpyZXNldCgpOwpvaygnc3RhcnRzIGluIHRoZSBUaG90aCcsIFAoKS5zaGlwPT09'
        'J2ZpdG90aCcpOwpvaygnVGhvdGggc3RhdHMgMy41IC8gMC4xNyAvIDEwMCAvIDEwMCAvIDIwIG1p'
        'c3NpbGVzJywgUCgpLnNwZD09PTMuNSAmJiBQKCkudHVybj09PTAuMTcgJiYgUCgpLm1heEhwPT09'
        'MTAwICYmIFAoKS5tYXhTaD09PTEwMCAmJiBQKCkuc2VjTWF4PT09MjAgJiYgUCgpLnNlY1R5cGU9'
        'PT0nbWlzc2lsZScpOwoKY29uc29sZS5sb2coJ1VubG9ja3MnKTsKcmVzZXQoKTsKVy5ydW4oInNj'
        'b3JlPTM5OTk7IHRpY2tTaGlwVW5sb2NrcygpIik7IG9rKCczOTk5IHBvaW50czogbm90aGluZyB1'
        'bmxvY2tlZCcsIFcuZ2V0KCdzaGlwVW5sb2NrZWQnKT09PTEpOwpXLnJ1bigic2NvcmU9NDAwMDsg'
        'dGlja1NoaXBVbmxvY2tzKCkiKTsgb2soJzQwMDAgcG9pbnRzOiBIb3J1cyB1bmxvY2tlZCwgb25l'
        'IG1lc3NhZ2UnLCBXLmdldCgnc2hpcFVubG9ja2VkJyk9PT0yICYmIFcuZ2V0KCdOT1RJQ0VfTE9H'
        'JykubGVuZ3RoPT09MSAmJiAvSE9SVVMvLnRlc3QoVy5nZXQoJ05PVElDRV9MT0cnKVswXS50eHQp'
        'KTsKVy5ydW4oInNjb3JlPTIzMDAwOyB0aWNrU2hpcFVubG9ja3MoKSIpOyBvaygnanVtcCB0byAy'
        'MzAwMDogT3NpcmlzLCBTZXJhcGlzLCBTZXRoIGF0IG9uY2UnLCBXLmdldCgnc2hpcFVubG9ja2Vk'
        'Jyk9PT01ICYmIFcuZ2V0KCdOT1RJQ0VfTE9HJykubGVuZ3RoPT09NCk7ClcucnVuKCJzY29yZT05'
        'OTk5OTk7IHRpY2tTaGlwVW5sb2NrcygpIik7IG9rKCduZXZlciBwYXN0IHRoZSBlbmQgb2YgdGhl'
        'IGxpc3QnLCBXLmdldCgnc2hpcFVubG9ja2VkJyk9PT04KTsKVy5ydW4oInRpY2tTaGlwVW5sb2Nr'
        'cygpIik7IG9rKCdzZXZlbiB1bmxvY2sgbWVzc2FnZXMgaW4gdG90YWwsIG5vbmUgcmVwZWF0ZWQn'
        'LCBXLmdldCgnTk9USUNFX0xPRycpLmxlbmd0aD09PTcpOwpyZXNldCgpOyBXLnJ1bigiRlMxX01P'
        'REU9dHJ1ZTsgc2NvcmU9OTk5OTk7IHRpY2tTaGlwVW5sb2NrcygpIik7IG9rKCdGUzEgbW9kZTog'
        'bm8gdW5sb2NrcycsIFcuZ2V0KCdzaGlwVW5sb2NrZWQnKT09PTEpOwpyZXNldCgpOyBXLnJ1bigi'
        'R1M9J2dhbWVvdmVyJzsgc2NvcmU9OTk5OTk7IHRpY2tTaGlwVW5sb2NrcygpIik7IG9rKCdub3Qg'
        'b3V0c2lkZSBwbGF5JywgVy5nZXQoJ3NoaXBVbmxvY2tlZCcpPT09MSk7Cgpjb25zb2xlLmxvZygn'
        'V2hlbiB0aGUgc3dpdGNoIGlzIGF2YWlsYWJsZScpOwpjb25zdCByZWFkeSA9IChzZXR1cCk9Pnsg'
        'cmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IHNldHVwKCk7IHJldHVybiBXLnJ1bign'
        'c2hpcFN3YXBSZWFkeSgpJyk7IH07Cm9rKCdubyBkZXN0cm95ZXI6IG5vdCByZWFkeScsIHJlYWR5'
        'KCgpPT57fSk9PT1mYWxzZSk7Cm9rKCdhbGxpZWQgVmFzdWRhbiBkZXN0cm95ZXI6IHJlYWR5Jywg'
        'cmVhZHkoKCk9Plcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pKT09PXRydWUpOwpvaygnTlRG'
        'IGh1bGwgKG50ZmRlaGVjYXRlKSBpcyBUZXJyYW4sIG5vIFRlcnJhbiBodWxscyBleGlzdDogbm90'
        'IHJlYWR5JywKICAgcmVhZHkoKCk9Plcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonbnRm'
        'ZGVoZWNhdGUnfSldKSk9PT1mYWxzZSk7Cm9rKCdjcnVpc2VyIG9ubHk6IG5vdCByZWFkeScsIHJl'
        'YWR5KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKHtpbWc6J2NybWVudHUnfSldKSk9PT1m'
        'YWxzZSk7Cm9rKCdDb2xvc3N1cyBhbG9uZSBpcyBhIGpvaW50IHlhcmQ6IHJlYWR5JywKICAgcmVh'
        'ZHkoKCk9Plcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonc2Rjb2xvc3N1cycsIGNvbG9z'
        'c3VzOnRydWV9KV0pKT09PXRydWUpOwpvaygnZGVhZCBkZXN0cm95ZXI6IG5vdCByZWFkeScsIHJl'
        'YWR5KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKHtkZWFkOnRydWV9KV0pKT09PWZhbHNl'
        'KTsKb2soJ2Rlc3Ryb3llciB3YXJwaW5nIG91dDogbm90IHJlYWR5JywgcmVhZHkoKCk9Plcuc2V0'
        'KCdhbGxpZXMnLFtkZXN0cm95ZXIoe3dhcnBPdXQ6dHJ1ZX0pXSkpPT09ZmFsc2UpOwpvaygnb25s'
        'eSB0aGUgc3RhcnQgc2hpcCB1bmxvY2tlZDogbm90IHJlYWR5JywgcmVhZHkoKCk9PnsgVy5zZXQo'
        'J2FsbGllcycsW2Rlc3Ryb3llcigpXSk7IFcucnVuKCdzaGlwVW5sb2NrZWQ9MScpOyB9KT09PWZh'
        'bHNlKTsKb2soJ2R1cmluZyBhIGp1bXA6IG5vdCByZWFkeScsIHJlYWR5KCgpPT57IFcuc2V0KCdh'
        'bGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bignanVtcD10cnVlJyk7IH0pPT09ZmFsc2UpOwpv'
        'aygnRlMxIG1vZGU6IG5vdCByZWFkeScsIHJlYWR5KCgpPT57IFcuc2V0KCdhbGxpZXMnLFtkZXN0'
        'cm95ZXIoKV0pOyBXLnJ1bignRlMxX01PREU9dHJ1ZScpOyB9KT09PWZhbHNlKTsKCmNvbnNvbGUu'
        'bG9nKCdTd2l0Y2hpbmcnKTsKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zOyBwbGF5ZXIu'
        'aHA9MTI7IHBsYXllci5zaD01OyBwbGF5ZXIuc2VjQW1tbz0xIik7IFcuc2V0KCdhbGxpZXMnLFtk'
        'ZXN0cm95ZXIoKV0pOwpXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOyBvaygnYnV0dG9uIG9wZW5z'
        'IHRoZSBtZW51IGFuZCBwYXVzZXMnLCBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUgJiYgVy5nZXQo'
        'J3BhdXNlZCcpPT09dHJ1ZSk7ClcucnVuKCJzd2FwU2hpcCgnZmlzZXJhcGlzJykiKTsgb2soJ2xv'
        'Y2tlZCBodWxsIChTZXJhcGlzKSByZWZ1c2VkJywgUCgpLnNoaXA9PT0nZml0b3RoJyAmJiBXLmdl'
        'dCgnc2hpcE1lbnUnKT09PXRydWUpOwpXLnJ1bigic3dhcFNoaXAoJ2ZpdG90aCcpIik7IG9rKCdj'
        'dXJyZW50IGh1bGwgcmVmdXNlZCcsIFcuZ2V0KCdzaGlwTWVudScpPT09dHJ1ZSAmJiBXLmdldCgn'
        'c2hpcFN3YXBXYXZlJyk9PT0tMSk7ClcucnVuKCJzd2FwU2hpcCgnYm9vc2lyaXMnKSIpOwovLyBU'
        'aGUgcGFuZWwgY2xvc2VzLCBidXQgdGhlIGdhbWUgc3RheXMgc3RvcHBlZDogY29taW5nIGJhY2sg'
        'aW50byB0aGUKLy8gZmlnaHQgaXMgdGhlIHBsYXllcidzIHRvIHRpbWUgbm93LCB3aGF0ZXZlciB0'
        'aGUgcGFuZWwgYW5kIGhvd2V2ZXIgaXQKLy8gd2FzIGxlZnQuCm9rKCdPc2lyaXMgdGFrZW4gYW5k'
        'IHRoZSBtZW51IGNsb3NlZCcsIFAoKS5zaGlwPT09J2Jvb3NpcmlzJyAmJiBXLmdldCgnc2hpcE1l'
        'bnUnKT09PWZhbHNlKTsKb2soJ2J1dCB0aGUgZ2FtZSBpcyBzdGlsbCBoZWxkJywgVy5nZXQoJ3Bh'
        'dXNlZCcpPT09dHJ1ZSAmJiBXLmdldCgncmVzdW1lSG9sZCcpPT09dHJ1ZSk7ClcucnVuKCdwb2lu'
        'dGVyQ29uc3VtZWQoe3g6NDAwLHk6MzAwfSknKTsKb2soJ2FuZCBvbmUgdGFwIHB1dHMgeW91IGJh'
        'Y2sgaW4gaXQnLCBXLmdldCgncGF1c2VkJyk9PT1mYWxzZSAmJiBXLmdldCgncmVzdW1lSG9sZCcp'
        'PT09ZmFsc2UpOwpvaygnT3NpcmlzIHN0YXRzIDIuNSAvIDAuMTAgLyAxNDAgLyAxMDAgLyAxMCBi'
        'b21icycsIFAoKS5zcGQ9PT0yLjUgJiYgUCgpLnR1cm49PT0wLjEwICYmIFAoKS5tYXhIcD09PTE0'
        'MCAmJiBQKCkubWF4U2g9PT0xMDAgJiYgUCgpLnNlY01heD09PTEwICYmIFAoKS5zZWNUeXBlPT09'
        'J2JvbWInKTsKb2soJ3JlZmlsbGVkOiBodWxsIDE0MCwgc2hpZWxkcyAxMDAsIDEwIGJvbWJzJywg'
        'UCgpLmhwPT09MTQwICYmIFAoKS5zaD09PTEwMCAmJiBQKCkuc2VjQW1tbz09PTEwKTsKb2soJ3N3'
        'aXRjaCBzcGVudCBmb3IgdGhpcyB3YXZlJywgVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpPT09ZmFs'
        'c2UpOwpXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOyBvaygnbWVudSBkb2VzIG5vdCBvcGVuIGFn'
        'YWluIHRoaXMgd2F2ZScsIFcuZ2V0KCdzaGlwTWVudScpPT09ZmFsc2UpOwpXLnJ1bignd2F2ZT0y'
        'Jyk7IG9rKCduZXh0IHdhdmU6IGF2YWlsYWJsZSBhZ2FpbicsIFcucnVuKCdzaGlwU3dhcFJlYWR5'
        'KCknKT09PXRydWUpOwoKY29uc29sZS5sb2coJ0N5Y2xlIHNjYWxpbmcgYW5kIHNoaWVsZHMnKTsK'
        'cmVzZXQoKTsgVy5ydW4oInBsYXllci5odWxsTXVsdD0xLjU7IHNoaXBVbmxvY2tlZD04Iik7IFcu'
        'c2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1lbnUoKTsgc3dh'
        'cFNoaXAoJ2Jvc2VraG1ldCcpIik7IG9rKCdTZWtobWV0IGF0IGN5Y2xlIHgxLjU6IGh1bGwgMjEw'
        'JywgUCgpLm1heEhwPT09MjEwICYmIFAoKS5ocD09PTIxMCk7CnJlc2V0KCk7IFcucnVuKCJlcmFP'
        'ZmY9dHJ1ZTsgc2hpcFVubG9ja2VkPTIiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7'
        'ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBzd2FwU2hpcCgnZmlob3J1cycpIik7IG9rKCdlcmEg'
        'd2l0aG91dCBzaGllbGRzOiBzaGllbGRzIHN0YXkgMCcsIFAoKS5zaD09PTAgJiYgUCgpLm1heFNo'
        'PT09MTAwKTsKVy5ydW4oJ2VyYU9mZj1mYWxzZScpOwoKY29uc29sZS5sb2coJ0NhbGwgbWVudSBh'
        'bmQgc3dpdGNoIG1lbnUgZXhjbHVkZSBlYWNoIG90aGVyJyk7CnJlc2V0KCk7IFcucnVuKCJzaGlw'
        'VW5sb2NrZWQ9MjsgY2FsbE1lbnU9dHJ1ZTsgcGF1c2VkPXRydWUiKTsgVy5zZXQoJ2FsbGllcycs'
        'W2Rlc3Ryb3llcigpXSk7ClcucnVuKCd0b2dnbGVTaGlwTWVudSgpJyk7IG9rKCdvcGVuaW5nIHRo'
        'ZSBzd2l0Y2ggY2xvc2VzIHRoZSBjYWxsIG1lbnUnLCBXLmdldCgnY2FsbE1lbnUnKT09PWZhbHNl'
        'ICYmIFcuZ2V0KCdzaGlwTWVudScpPT09dHJ1ZSk7Cgpjb25zb2xlLmxvZygnTWVudSBkcmF3aW5n'
        'IGFuZCB0YXBzJyk7CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBXLnNldCgnYWxs'
        'aWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCk7IGRyYXdTaGlwTWVu'
        'dSgpJyk7CmNvbnN0IHJlY3RzID0gVy5ydW4oJ3dpbmRvdy5fc2hpcFJlY3RzJyk7CmNvbnN0IHJv'
        'd09mID0gKGtleSk9PlcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycpLmZpbmQocj0+ci5zaGlwPT09'
        'a2V5KTsKb2soJ2VpZ2h0IHJvd3MgZHJhd24nLCByZWN0cy5sZW5ndGg9PT04KTsKb2soJ21lbnUg'
        'Zml0cyBvbiB0aGUgODAweDUwMCBmaWVsZCcsIHJlY3RzLmV2ZXJ5KHI9PnIueD49MCAmJiByLnk+'
        'PTAgJiYgci54K3Iudzw9ODAwICYmIHIueStyLmg8PTUwMCkpOwpvaygnZmlnaHRlcnMgZmlyc3Qs'
        'IHRoZW4gYm9tYmVycycsCiAgIHJlY3RzLm1hcChyPT5yLnNoaXApLmpvaW4oKT09PSdmaXRvdGgs'
        'Zmlob3J1cyxmaXNlcmFwaXMsZmlzZXRoLGZpdGF1cmV0LGJvb3NpcmlzLGJvYmFraGEsYm9zZWto'
        'bWV0Jyk7Cm9rKCdldmVyeSByb3cgaXMgZnVsbCB3aWR0aCBhbmQgdGhleSBkbyBub3Qgb3Zlcmxh'
        'cCcsCiAgIHJlY3RzLmV2ZXJ5KHI9PnIudz09PXJlY3RzWzBdLncpICYmCiAgIHJlY3RzLmV2ZXJ5'
        'KChyLGkpPT5pPT09MCB8fCByLnkgPj0gcmVjdHNbaS0xXS55K3JlY3RzW2ktMV0uaCkpOwpvaygn'
        'YSBsb2NrZWQgcm93IGlzIHRoaW5uZXIgdGhhbiBvbmUgdGhhdCBjYW4gYmUgdGFrZW4nLAogICBy'
        'b3dPZignYm9iYWtoYScpLmggPCByb3dPZignZmlob3J1cycpLmgpOwpvaygnb25seSBIb3J1cyBh'
        'bmQgT3NpcmlzIGFyZSB0YXBwYWJsZScsIHJlY3RzLmZpbHRlcihyPT5yLmtleSkubWFwKHI9PnIu'
        'a2V5KS5qb2luKCk9PT0nZmlob3J1cyxib29zaXJpcycpOwpjb25zdCBsb2NrZWQgPSByb3dPZign'
        'Ym9iYWtoYScpOwpXLnJ1bihgcG9pbnRlckNvbnN1bWVkKHt4OiR7bG9ja2VkLngrNX0seToke2xv'
        'Y2tlZC55KzV9fSlgKTsgb2soJ3RhcCBvbiBsb2NrZWQgQmFraGEga2VlcHMgdGhlIG1lbnUgb3Bl'
        'bicsIFcuZ2V0KCdzaGlwTWVudScpPT09dHJ1ZSAmJiBQKCkuc2hpcD09PSdmaXRvdGgnKTsKY29u'
        'c3QgaG9ydXMgPSByb3dPZignZmlob3J1cycpOwpXLnJ1bihgcG9pbnRlckNvbnN1bWVkKHt4OiR7'
        'aG9ydXMueCs1fSx5OiR7aG9ydXMueSs1fX0pYCk7IG9rKCd0YXAgb24gSG9ydXMgc3dpdGNoZXMn'
        'LCBQKCkuc2hpcD09PSdmaWhvcnVzJyAmJiBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKcmVz'
        'ZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIo'
        'KV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOwpXLnJ1bigncG9pbnRlckNvbnN1bWVkKHt4'
        'OjIseToyfSknKTsgb2soJ3RhcCBvdXRzaWRlIGNsb3NlcyB3aXRob3V0IHN3aXRjaGluZycsIFcu'
        'Z2V0KCdzaGlwTWVudScpPT09ZmFsc2UgJiYgUCgpLnNoaXA9PT0nZml0b3RoJyAmJiBXLnJ1bign'
        'c2hpcFN3YXBSZWFkeSgpJyk9PT10cnVlKTsKb2soJ2NhbmNlbGxpbmcgaG9sZHMgdGhlIHBhdXNl'
        'IGp1c3QgdGhlIHNhbWUnLCBXLmdldCgncmVzdW1lSG9sZCcpPT09dHJ1ZSk7ClcucnVuKCdjbGVh'
        'clJlc3VtZUhvbGQoKScpOwpXLnJ1bigid2luZG93Ll9zaGlwQnRuUmVjdD17eDo2OTUseTo0LHc6'
        'MjIsaDoyMH07IHBvaW50ZXJDb25zdW1lZCh7eDo3MDAseToxMH0pIik7IG9rKCd0YXAgb24gdGhl'
        'IGJhciBidXR0b24gb3BlbnMgdGhlIG1lbnUnLCBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUpOwoK'
        'Y29uc29sZS5sb2coJ1RoZSBwYW5lbCBzd2FsbG93cyBpdHMgb3duIGNsaWNrcycpOwp7CiAgcmVz'
        'ZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD04Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIo'
        'KV0pOwogIFcucnVuKCd0b2dnbGVTaGlwTWVudSgpJyk7IFcucnVuKCdkcmF3U2hpcE1lbnUoKScp'
        'OwogIGNvbnN0IHByID0gVy5ydW4oJ3dpbmRvdy5fc2hpcFBhbmVsUmVjdCcpOwogIG9rKCd0aGUg'
        'cGFuZWwgcmVwb3J0cyBpdHMgb3V0bGluZScsIHByICYmIHByLnc+MCAmJiBwci5oPjApOwogIC8v'
        'IFRoZSBoZWFkZXIgbGluZTogaW5zaWRlIHRoZSBwYW5lbCwgb24gbm8gcm93IGF0IGFsbC4KICBX'
        'LnJ1bihgcG9pbnRlckNvbnN1bWVkKHt4OiR7cHIueCs0MH0seToke3ByLnkrNn19KWApOwogIG9r'
        'KCdhIGNsaWNrIG9uIHRoZSBoZWFkZXIga2VlcHMgdGhlIHBhbmVsIG9wZW4nLCBXLmdldCgnc2hp'
        'cE1lbnUnKT09PXRydWUpOwogIC8vIEEgZ2FwIGJldHdlZW4gdHdvIHJvd3MuCiAgY29uc3QgcnMg'
        'PSBXLnJ1bignd2luZG93Ll9zaGlwUmVjdHMnKTsKICBjb25zdCBnYXBZID0gcnNbMF0ueSArIHJz'
        'WzBdLmggKyAyOwogIFcucnVuKGBwb2ludGVyQ29uc3VtZWQoe3g6JHtyc1swXS54KzQwfSx5OiR7'
        'Z2FwWX19KWApOwogIG9rKCdhIGNsaWNrIGluIHRoZSBnYXAgYmV0d2VlbiByb3dzIGtlZXBzIGl0'
        'IG9wZW4gdG9vJywgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlKTsKICAvLyBUaGUgZm9vdGVyLgog'
        'IFcucnVuKGBwb2ludGVyQ29uc3VtZWQoe3g6JHtwci54K3ByLncvMn0seToke3ByLnkrcHIuaC02'
        'fX0pYCk7CiAgb2soJ2FuZCBvbmUgb24gdGhlIGZvb3RlcicsIFcuZ2V0KCdzaGlwTWVudScpPT09'
        'dHJ1ZSk7CiAgb2soJ25vbmUgb2YgdGhlbSBzd2l0Y2hlZCB0aGUgc2hpcCcsIFAoKS5zaGlwPT09'
        'J2ZpdG90aCcpOwogIC8vIE91dHNpZGUgdGhlIG91dGxpbmUgaXMgc3RpbGwgb3V0c2lkZS4KICBX'
        'LnJ1bihgcG9pbnRlckNvbnN1bWVkKHt4OiR7cHIueC0xMn0seToke3ByLnkrcHIuaC8yfX0pYCk7'
        'CiAgb2soJ2EgY2xpY2sgYmVzaWRlIHRoZSBwYW5lbCBjbG9zZXMgaXQnLCBXLmdldCgnc2hpcE1l'
        'bnUnKT09PWZhbHNlKTsKfQoKY29uc29sZS5sb2coJ0tleWJvYXJkJyk7CmNvbnN0IGtleSA9IChj'
        'b2RlKT0+Vy5ydW4oYG9uS2V5KHtjb2RlOicke2NvZGV9JywgcHJldmVudERlZmF1bHQoKXt9fSlg'
        'KTsKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD00Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0'
        'cm95ZXIoKV0pOwprZXkoJ0tleVYnKTsgb2soJ1Ygb3BlbnMnLCBXLmdldCgnc2hpcE1lbnUnKT09'
        'PXRydWUpOwovLyBGb3VyIGh1bGxzIG9wZW46IHJvc3RlciAwIHRvIDMuIFRoZSBkaWdpdHMgZm9s'
        'bG93IHRoZSBwYW5lbCwgc28gNCBpcyB0aGUKLy8gU2V0aCwgd2hpY2ggaXMgc3RpbGwgbG9ja2Vk'
        'LCBhbmQgNiBpcyB0aGUgZmlyc3QgYm9tYmVyLgprZXkoJ0RpZ2l0NCcpOyBvaygnNCAodGhlIFNl'
        'dGgsIG5vdCB1bmxvY2tlZCB5ZXQpIGRvZXMgbm90aGluZycsCiAgICAgICAgICAgICAgICAgIFcu'
        'Z2V0KCdzaGlwTWVudScpPT09dHJ1ZSAmJiBQKCkuc2hpcD09PSdmaXRvdGgnKTsKa2V5KCdEaWdp'
        'dDYnKTsgb2soJzYgdGFrZXMgdGhlIE9zaXJpcywgZmlyc3Qgcm93IG9mIHRoZSBib21iZXJzJywK'
        'ICAgICAgICAgICAgICAgICAgUCgpLnNoaXA9PT0nYm9vc2lyaXMnICYmIFcuZ2V0KCdzaGlwTWVu'
        'dScpPT09ZmFsc2UpOwpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTQiKTsgVy5zZXQoJ2Fs'
        'bGllcycsW2Rlc3Ryb3llcigpXSk7IGtleSgnS2V5VicpOwprZXkoJ0RpZ2l0MycpOyBvaygnMyB0'
        'YWtlcyB0aGUgU2VyYXBpcywgdGhpcmQgcm93IGRvd24nLAogICAgICAgICAgICAgICAgICBQKCku'
        'c2hpcD09PSdmaXNlcmFwaXMnICYmIFcuZ2V0KCdzaGlwTWVudScpPT09ZmFsc2UpOwpyZXNldCgp'
        'OyBXLnJ1bigic2hpcFVubG9ja2VkPTQiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7'
        'IGtleSgnS2V5VicpOyBrZXkoJ0VzY2FwZScpOwpvaygnRXNjYXBlIGNsb3NlcycsIFcuZ2V0KCdz'
        'aGlwTWVudScpPT09ZmFsc2UpOwpvaygnYW5kIGhvbGRzIHRoZSBwYXVzZSwgbGlrZSBldmVyeSBv'
        'dGhlciB3YXkgb2YgbGVhdmluZyBhIHBhbmVsJywKICAgVy5nZXQoJ3BhdXNlZCcpPT09dHJ1ZSAm'
        'JiBXLmdldCgncmVzdW1lSG9sZCcpPT09dHJ1ZSk7ClcucnVuKCdjbGVhclJlc3VtZUhvbGQoKScp'
        'OwpvaygnYWZ0ZXIgdGhlIHRhcCB0aGUgZ2FtZSBydW5zIGFnYWluJywgVy5nZXQoJ3BhdXNlZCcp'
        'PT09ZmFsc2UpOwpyZXNldCgpOyBrZXkoJ0tleVYnKTsgb2soJ1Ygd2l0aG91dCBhIGRlc3Ryb3ll'
        'ciBkb2VzIG5vdGhpbmcnLCBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKCmNvbnNvbGUubG9n'
        'KCdSZXN0YXJ0IGd1YXJkJyk7ClcucnVuKCJsYXVuY2hHYW1lPWZ1bmN0aW9uKCl7bGF1bmNoZWQr'
        'K30iKTsKLy8gVGhlIHRpdGxlIGFuZCB0aGUgZ2FtZSBvdmVyIHNjcmVlbiBib3RoIGdvIHRocm91'
        'Z2ggdG9UaXRsZU9yTGF1bmNoIG5vdywKLy8gc28gdGhhdCBpcyB3aGF0IGhhcyB0byBiZSBpbiBw'
        'bGFjZSBmb3IgdGhlIHJlc3RhcnQgZ3VhcmQgdG8gYmUgdGVzdGVkLgpXLnJ1bigidG9UaXRsZU9y'
        'TGF1bmNoPWZ1bmN0aW9uKCl7IGlmKEdTPT09J2dhbWVvdmVyJyl7IEdTPSd0aXRsZSc7IHJldHVy'
        'bjsgfSBsYXVuY2hHYW1lKCk7IH0iKTsKY29uc3QgZG93biA9ICgpPT5XLnJ1bigib25Eb3duKHti'
        'dXR0b246MCwgY2xpZW50WDo0MDAsIGNsaWVudFk6MzAwfSkiKTsKVy5ydW4oIkdTPSd0aXRsZSc7'
        'IGxhdW5jaGVkPTAiKTsgZG93bigpOyBvaygndGFwIG9uIHRpdGxlIHN0YXJ0cyBhdCBvbmNlJywg'
        'Vy5nZXQoJ2xhdW5jaGVkJyk9PT0xKTsKVy5ydW4oIkdTPSdnYW1lb3Zlcic7IGdhbWVPdmVyQXQ9'
        'cGVyZm9ybWFuY2Uubm93KCk7IGxhdW5jaGVkPTAiKTsgZG93bigpOyBvaygndGFwIHJpZ2h0IGFm'
        'dGVyIGR5aW5nIGRvZXMgbm90IHJlc3RhcnQnLCBXLmdldCgnbGF1bmNoZWQnKT09PTApOwpXLnJ1'
        'bigiZ2FtZU92ZXJBdD1wZXJmb3JtYW5jZS5ub3coKS0yMDAwIik7IGRvd24oKTsKb2soJ3RhcCBh'
        'ZnRlciAyIHMgZ29lcyBiYWNrIHRvIHRoZSB0aXRsZSwgbm90IGludG8gdGhlIG5leHQgcnVuJywK'
        'ICAgVy5nZXQoJ2xhdW5jaGVkJyk9PT0wICYmIFcuZ2V0KCdHUycpPT09J3RpdGxlJyk7CgoKY29u'
        'c29sZS5sb2coJ0hhbmdhcnMgYnkgZmFjdGlvbicpOwpjb25zdCBjb2xvc3N1cyA9IChvKT0+T2Jq'
        'ZWN0LmFzc2lnbih7aW1nOidzZGNvbG9zc3VzJywgY29sb3NzdXM6dHJ1ZSwgc21hbGw6ZmFsc2Us'
        'IGRlYWQ6ZmFsc2UsIHdhcnBPdXQ6ZmFsc2V9LCBvfHx7fSk7Cm9rKCdodWxsIGZhY3Rpb24gY29t'
        'ZXMgZnJvbSB0aGUga2V5JywgVy5ydW4oImh1bGxGYWMoJ2RlaGF0c2hlcHN1dCcpIik9PT0ndmFz'
        'dWRhbicKICAgJiYgVy5ydW4oImh1bGxGYWMoJ2Rlb3Jpb25yaWdodCcpIik9PT0ndGVycmFuJyAm'
        'JiBXLnJ1bigiaHVsbEZhYygnc2Rjb2xvc3N1cycpIik9PT0nZ3R2YScpOwpvaygnYSBkZWZlY3Rl'
        'ZCBIYW1tZXIgb2YgTGlnaHQgVHlwaG9uIHN0aWxsIGNvdW50cyBhcyBWYXN1ZGFuJywKICAgcmVh'
        'ZHkoKCk9Plcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonZGV0eXBob24nLCBmYWN0aW9u'
        'Oidob2wnfSldKSk9PT10cnVlKTsKb2soJ2EgcmVuZWdhZGUgSGF0c2hlcHN1dCB0b28nLAogICBy'
        'ZWFkeSgoKT0+Vy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7aW1nOidkZWhhdHNoZXBzdXQnLCBm'
        'YWN0aW9uOidyZW5lZ2FkZSd9KV0pKT09PXRydWUpOwpvaygnVGVycmFuIE9yaW9uIG9ubHk6IG5v'
        'dCByZWFkeScsIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKHtpbWc6J2Rlb3Jp'
        'b25yaWdodCd9KV0pKT09PWZhbHNlKTsKb2soJ1RlcnJhbiBIZWNhdGUgb25seTogbm90IHJlYWR5'
        'JywgcmVhZHkoKCk9Plcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVoZWNhdGUnfSld'
        'KSk9PT1mYWxzZSk7Cm9rKCdPcmlvbiBwbHVzIFR5cGhvbjogcmVhZHksIHRoZSBsaXN0cyBhZGQg'
        'dXAnLAogICByZWFkeSgoKT0+Vy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7aW1nOidkZW9yaW9u'
        'cmlnaHQnfSksIGRlc3Ryb3llcih7aW1nOidkZXR5cGhvbid9KV0pKT09PXRydWUpOwpvaygndW5r'
        'bm93biBjYXBpdGFsIGh1bGw6IG5vdCByZWFkeScsIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVzJyxb'
        'ZGVzdHJveWVyKHtpbWc6J2RlZGVtb24nfSldKSk9PT1mYWxzZSk7CgpyZXNldCgpOyBXLnJ1bigi'
        'c2hpcFVubG9ja2VkPTMiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7aW1nOidkZW9yaW9u'
        'cmlnaHQnfSldKTsKb2soJ1Zhc3VkYW4gaHVsbCBub3Qgb2ZmZXJlZCBieSBhIFRlcnJhbiBoYW5n'
        'YXInLCBXLnJ1bigic2hpcE9mZmVyZWQoJ2ZpaG9ydXMnKSIpPT09ZmFsc2UpOwpXLnJ1bigic2hp'
        'cE1lbnU9dHJ1ZTsgc3dhcFNoaXAoJ2ZpaG9ydXMnKSIpOwpvaygnYW5kIGEgZm9yY2VkIHN3aXRj'
        'aCBpcyByZWZ1c2VkJywgUCgpLnNoaXA9PT0nZml0b3RoJyAmJiBXLmdldCgnc2hpcFN3YXBXYXZl'
        'Jyk9PT0tMSk7Clcuc2V0KCdhbGxpZXMnLFtjb2xvc3N1cygpXSk7Cm9rKCd0aGUgQ29sb3NzdXMg'
        'b2ZmZXJzIHRoZSBWYXN1ZGFuIGh1bGwnLCBXLnJ1bigic2hpcE9mZmVyZWQoJ2ZpaG9ydXMnKSIp'
        'PT09dHJ1ZSk7CgpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTMiKTsgVy5zZXQoJ2FsbGll'
        'cycsW2Rlc3Ryb3llcih7aW1nOidkZW9yaW9ucmlnaHQnfSldKTsKVy5ydW4oJ3RvZ2dsZVNoaXBN'
        'ZW51KCknKTsgb2soJ1RlcnJhbiBoYW5nYXIgb25seTogdGhlIG1lbnUgc3RheXMgc2h1dCcsIFcu'
        'Z2V0KCdzaGlwTWVudScpPT09ZmFsc2UpOwpXLnJ1bigic2hpcE1lbnU9dHJ1ZTsgZHJhd1NoaXBN'
        'ZW51KCkiKTsKb2soJ25vIGNlbGwgaXMgdGFwcGFibGUgaW4gdGhhdCBzdGF0ZScsIFcucnVuKCd3'
        'aW5kb3cuX3NoaXBSZWN0cycpLmV2ZXJ5KHI9PiFyLmtleSkpOwoKY29uc29sZS5sb2coJ0NvbG9z'
        'c3VzIGxpZnRzIHRoZSBvbmNlIHBlciB3YXZlIGxpbWl0Jyk7CnJlc2V0KCk7IFcucnVuKCJzaGlw'
        'VW5sb2NrZWQ9MyIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKVy5ydW4oInRvZ2ds'
        'ZVNoaXBNZW51KCk7IHN3YXBTaGlwKCdmaWhvcnVzJykiKTsKb2soJ2ZpcnN0IHN3aXRjaCBvZiB0'
        'aGUgd2F2ZSByZWZpdHMnLCBQKCkuc2hpcD09PSdmaWhvcnVzJyAmJiBQKCkuaHA9PT04MCAmJiBQ'
        'KCkuc2g9PT0xMDAgJiYgUCgpLnNlY0FtbW89PT0yMCk7Cm9rKCdubyBDb2xvc3N1czogc3BlbnQg'
        'Zm9yIHRoaXMgd2F2ZScsIFcucnVuKCdzaGlwU3dhcFJlYWR5KCknKT09PWZhbHNlKTsKVy5zZXQo'
        'J2FsbGllcycsW2Rlc3Ryb3llcigpLCBjb2xvc3N1cygpXSk7Cm9rKCdDb2xvc3N1cyBhcnJpdmVz'
        'OiBhdmFpbGFibGUgYWdhaW4gaW4gdGhlIHNhbWUgd2F2ZScsIFcucnVuKCdzaGlwU3dhcFJlYWR5'
        'KCknKT09PXRydWUpOwpXLnJ1bigicGxheWVyLmhwPTQwOyBwbGF5ZXIuc2g9NTA7IHBsYXllci5z'
        'ZWNBbW1vPTEwIik7ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBzd2FwU2hpcCgnYm9vc2lyaXMn'
        'KSIpOwpvaygnc2Vjb25kIHN3aXRjaCBoYXBwZW5zJywgUCgpLnNoaXA9PT0nYm9vc2lyaXMnKTsK'
        'b2soJ2h1bGwgY2FycmllcyBvdmVyIGFzIGEgZnJhY3Rpb24sIDQwLzgwIG9mIDE0MCA9IDcwJywg'
        'UCgpLmhwPT09NzApOwpvaygnc2hpZWxkcyBjYXJyeSBvdmVyLCA1MC8xMDAgb2YgMTAwID0gNTAn'
        'LCBQKCkuc2g9PT01MCk7Cm9rKCdhbW1vIGNhcnJpZXMgb3ZlciwgMTAvMjAgb2YgMTAgYm9tYnMg'
        'PSA1JywgUCgpLnNlY0FtbW89PT01KTsKb2soJ25vIHJlZml0OiBub3QgZnVsbCcsIFAoKS5ocDxQ'
        'KCkubWF4SHAgJiYgUCgpLnNlY0FtbW88UCgpLnNlY01heCk7CgpyZXNldCgpOyBXLnJ1bigic2hp'
        'cFVubG9ja2VkPTMiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpLCBjb2xvc3N1cygpXSk7'
        'ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBzd2FwU2hpcCgnZmlob3J1cycpIik7Cm9rKCd3aXRo'
        'IHRoZSBDb2xvc3N1cyB0aGVyZSB0aGUgZmlyc3Qgc3dpdGNoIHN0aWxsIHJlZml0cycsIFAoKS5o'
        'cD09PTgwICYmIFAoKS5zZWNBbW1vPT09MjApOwpXLnJ1bigicGxheWVyLmhwPTEiKTsKVy5ydW4o'
        'InRvZ2dsZVNoaXBNZW51KCk7IHN3YXBTaGlwKCdib29zaXJpcycpIik7Cm9rKCdhIG5lYXJseSBk'
        'ZWFkIGh1bGwgc3RheXMgYWxpdmUgYWZ0ZXIgY2Fycnlpbmcgb3ZlcicsIFAoKS5ocD49MSAmJiBQ'
        'KCkuaHA8PTMpOwoKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcuc2V0KCdhbGxp'
        'ZXMnLFtkZXN0cm95ZXIoKSwgY29sb3NzdXMoe2RlYWQ6dHJ1ZX0pXSk7ClcucnVuKCJ0b2dnbGVT'
        'aGlwTWVudSgpOyBzd2FwU2hpcCgnZmlob3J1cycpIik7Cm9rKCdkZWFkIENvbG9zc3VzIGdyYW50'
        'cyBub3RoaW5nJywgVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpPT09ZmFsc2UpOwpyZXNldCgpOyBX'
        'LnJ1bigic2hpcFVubG9ja2VkPTMiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpLCBjb2xv'
        'c3N1cyh7d2FycE91dDp0cnVlfSldKTsKVy5ydW4oInRvZ2dsZVNoaXBNZW51KCk7IHN3YXBTaGlw'
        'KCdmaWhvcnVzJykiKTsKb2soJ0NvbG9zc3VzIHdhcnBpbmcgb3V0IGdyYW50cyBub3RoaW5nJywg'
        'Vy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpPT09ZmFsc2UpOwoKcmVzZXQoKTsgVy5ydW4oInNoaXBV'
        'bmxvY2tlZD0zIik7IFcuc2V0KCdhbGxpZXMnLFtjb2xvc3N1cygpXSk7ClcucnVuKCJ0b2dnbGVT'
        'aGlwTWVudSgpOyBzd2FwU2hpcCgnZmlob3J1cycpIik7IFcucnVuKCJwbGF5ZXIuaHA9MjAiKTsK'
        'Vy5ydW4oInRvZ2dsZVNoaXBNZW51KCk7IHN3YXBTaGlwKCdmaXRvdGgnKSIpOwpvaygnYmFjayBv'
        'bnRvIHRoZSBzdGFydCBodWxsIGF0IHRoZSBDb2xvc3N1cywgMjAvODAgb2YgMTAwID0gMjUnLCBQ'
        'KCkuc2hpcD09PSdmaXRvdGgnICYmIFAoKS5ocD09PTI1KTsKVy5ydW4oJ3dhdmU9MicpOwpvaygn'
        'bmV3IHdhdmUgd2l0aCB0aGUgQ29sb3NzdXMgc3RpbGwgdGhlcmU6IHJlZml0cyBhZ2FpbicsIFcu'
        'cnVuKCdzaGlwU3dhcFJlYWR5KCknKT09PXRydWUpOwpXLnJ1bigidG9nZ2xlU2hpcE1lbnUoKTsg'
        'c3dhcFNoaXAoJ2ZpaG9ydXMnKSIpOyBvaygnYW5kIGl0IGlzIGEgZnVsbCBodWxsJywgUCgpLmhw'
        'PT09ODApOwoKY29uc29sZS5sb2coJ0N5Y2xlczogZWFjaCBicmluZ3MgaXRzIG93biBmbGVldCcp'
        'Owp7CiAgY29uc3QgaG9sID0gVy5ydW4oJ2N5Y2xlQXQoMSknKSwgbnRmID0gVy5ydW4oJ2N5Y2xl'
        'QXQoMzEpJyk7CiAgb2soJ3dhdmVzIDEgdG8gMzAgYXJlIHRoZSBIYW1tZXIgb2YgTGlnaHQgY3lj'
        'bGUnLCBXLnJ1bignY3ljbGVBdCgzMCknKT09PWhvbCAmJiBob2wuZmlyc3Q9PT0xKTsKICBvaygn'
        'd2F2ZSAzMSBvcGVucyB0aGUgTlRGIGN5Y2xlLCBhbmQgaXQgaG9sZHMgYWZ0ZXIgdGhhdCcsIG50'
        'Zi5maXJzdD09PTMxICYmIFcucnVuKCdjeWNsZUF0KDU5KScpPT09bnRmICYmIFcucnVuKCdjeWNs'
        'ZUF0KDE0MCknKT09PW50Zik7CiAgcmVzZXQoKTsKICBXLnJ1bigic2NvcmU9OTUwMDA7IGVudGVy'
        'Q3ljbGUoY3ljbGVBdCgzMSkpIik7CiAgb2soJ2VudGVyaW5nIGl0IHB1dHMgdGhlIHBsYXllciBp'
        'biBhIE15cm1pZG9uLCBmcmVzaCcsIFAoKS5zaGlwPT09J2ZpbXlybWlkb24nICYmIFAoKS5ocD09'
        'PVAoKS5tYXhIcCk7CiAgb2soJ3RoZSByb3N0ZXIgaXMgdGhlIFRlcnJhbiBvbmUsIGVpZ2h0IGh1'
        'bGxzJywKICAgICBXLnJ1bignUExBWUVSX1NISVBTLmxlbmd0aCcpPT09OCAmJiBXLnJ1bigiUExB'
        'WUVSX1NISVBTLmV2ZXJ5KHM9PnMuZmFjPT09J3RlcnJhbicpIikpOwogIG9rKCdpbiB0aGUgYWdy'
        'ZWVkIG9yZGVyJywKICAgICBXLnJ1bigiUExBWUVSX1NISVBTLm1hcChzPT5zLmtleSkuam9pbigp'
        'Iik9PT0nZmlteXJtaWRvbixmaWhlcmMsYm9hcnRlbWlzLGZpaGVyY21rMixib21lZHVzYSxmaWVy'
        'aW55ZXMsYm91cnNhLGZpYXJlcycpOwogIG9rKCdvbmx5IHRoZSBmaXJzdCBodWxsIGlzIG9wZW4n'
        'LCBXLmdldCgnc2hpcFVubG9ja2VkJyk9PT0xKTsKICBXLnJ1bigic2NvcmU9OTUwMDArMzk5OTsg'
        'dGlja1NoaXBVbmxvY2tzKCkiKTsKICBvaygndGhlIHBvaW50cyBicm91Z2h0IGludG8gdGhlIGN5'
        'Y2xlIGRvIG5vdCBjb3VudCcsIFcuZ2V0KCdzaGlwVW5sb2NrZWQnKT09PTEpOwogIFcucnVuKCJz'
        'Y29yZT05NTAwMCs0MDAwOyB0aWNrU2hpcFVubG9ja3MoKSIpOwogIG9rKCc0MDAwIHBvaW50cyBz'
        'Y29yZWQgSU4gdGhlIGN5Y2xlIG9wZW4gdGhlIEhlcmN1bGVzJywgVy5nZXQoJ3NoaXBVbmxvY2tl'
        'ZCcpPT09MiAmJiAvSEVSQ1VMRVMvLnRlc3QoVy5nZXQoJ05PVElDRV9MT0cnKS5zbGljZSgtMSlb'
        'MF0udHh0KSk7CiAgb2soJ3RoZSBUZXJyYW4gc3VwcG9ydCBjb2x1bW4gYW5zd2VycywgdGhlIFZh'
        'c3VkYW4gb25lIGRvZXMgbm90JywKICAgICBXLnJ1bignQUxMWV9GQUNfT04udGVycmFuJyk9PT10'
        'cnVlICYmIFcucnVuKCdBTExZX0ZBQ19PTi52YXN1ZGFuJyk9PT1mYWxzZSk7CiAgLy8gVGhlIGhh'
        'bmdhciBmb2xsb3dzIHRoZSBodWxsLCBzbyB0aGUgVGVycmFuIHJvc3RlciBuZWVkcyBhIFRlcnJh'
        'biBkZXN0cm95ZXIuCiAgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7aW1nOidkZW9yaW9ucmln'
        'aHQnfSldKTsKICBvaygnYSBUZXJyYW4gZGVzdHJveWVyIG9mZmVycyB0aGUgSGVyY3VsZXMnLCBX'
        'LnJ1bigic2hpcE9mZmVyZWQoJ2ZpaGVyYycpIik9PT10cnVlICYmIFcucnVuKCdzaGlwU3dhcFJl'
        'YWR5KCknKT09PXRydWUpOwogIFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOwogIG9rKCdh'
        'IFZhc3VkYW4gb25lIGRvZXMgbm90JywgVy5ydW4oInNoaXBPZmZlcmVkKCdmaWhlcmMnKSIpPT09'
        'ZmFsc2UgJiYgVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpPT09ZmFsc2UpOwogIFcucnVuKCJlbnRl'
        'ckN5Y2xlKGN5Y2xlQXQoMSkpIik7CiAgb2soJ2FuZCBiYWNrOiB0aGUgVmFzdWRhbiByb3N0ZXIg'
        'YW5kIGNvbHVtbicsIFAoKS5zaGlwPT09J2ZpdG90aCcgJiYKICAgICBXLnJ1bignQUxMWV9GQUNf'
        'T04udGVycmFuJyk9PT1mYWxzZSAmJiBXLnJ1bignQUxMWV9GQUNfT04udmFzdWRhbicpPT09dHJ1'
        'ZSk7Cn0Kb2soJ3RoZSBydW4gc3RhcnRzIGluIHRoZSBjeWNsZSBvZiBpdHMgZmlyc3Qgd2F2ZScs'
        'CiAgIC9lbHNlIGVudGVyQ3ljbGVcKGN5Y2xlQXRcKHdhdmVcKzFcKVwpOy8udGVzdChmbignbGF1'
        'bmNoR2FtZScpKSk7Cm9rKCdjcm9zc2luZyBpbnRvIGEgbmV3IGN5Y2xlIGhhbmRzIG92ZXIgdGhl'
        'IGZsZWV0JywKICAgL2lmXChfYyE9PWN5Y2xlTm93XCkgZW50ZXJDeWNsZVwoX2NcKTsvLnRlc3Qo'
        'Zm4oJ25leHRXYXZlJykpKTsKb2soJz9tPSBzdGFydHMgdGhlIHJ1biBhdCB0aGF0IHdhdmUgaW5z'
        'dGVhZCBvZiByZXBlYXRpbmcgaXQnLAogICAvU0NSSVBUX09ORVw/U0NSSVBUX09ORS0xOjAvLnRl'
        'c3QoZm4oJ2xhdW5jaEdhbWUnKSkgJiYgIS9TQ1JJUFRfT05FIFw/IFNDUklQVF9PTkUgOiBuLy50'
        'ZXN0KHNyYykpOwoKY29uc29sZS5sb2coJ1N1cHBvcnQgY2FsbHMgYnkgZmFjdGlvbicpOwpvaygn'
        'dGhlIFRlcnJhbiBjb2x1bW4gaXMgb2ZmIGluIHRoaXMgY3ljbGUnLCBzcmMuaW5jbHVkZXMoImNv'
        'bnN0IEFMTFlfRkFDX09OID0ge3RlcnJhbjpmYWxzZSwgdmFzdWRhbjp0cnVlLCBndHZhOnRydWV9'
        'OyIpKTsKb2soJ3RoZSBjYWxsIGlzIGdhdGVkIGluc2lkZSBjYWxsQWxseSwgbm90IG9ubHkgaW4g'
        'dGhlIG1lbnUnLAogICAvZnVuY3Rpb24gY2FsbEFsbHlcKGlkXClce1tcc1xTXXswLDQwMH1hbGx5'
        'RmFjT25cKGNkZWZcLmZhY1wpLy50ZXN0KHNyYykpOwpvaygndGhlIG1lbnUgbm8gbG9uZ2VyIHVz'
        'ZXMgdGhlIGZpeGVkIHR3byBjb2x1bW4gc3BsaXQnLCAhc3JjLmluY2x1ZGVzKCdBTExZX1RFUl9O'
        'PzA6MScpKTsKb2soJ3RoZSBDb2xvc3N1cyBpcyBhIEdUVkEgc2hpcCBub3cnLCAvY29sb3NzdXM6'
        'XHMqXHtjbHM6J2Rlc3Ryb3llcicsIGZhYzonZ3R2YScvLnRlc3Qoc3JjKSk7Cgpjb25zb2xlLmxv'
        'ZygnSHVsbCBwaWN0dXJlcyBpbiB0aGVpciBvd24gY2VsbCcpOwpjb25zdCBJTUcgPSAodyxoKT0+'
        'KHt3aWR0aDp3LCBoZWlnaHQ6aH0pOwpjb25zdCBBTExfSU1HUyA9IHtmaXRvdGg6SU1HKDEyMCw5'
        'MCksIGZpaG9ydXM6SU1HKDEyMCw5MCksIGJvb3NpcmlzOklNRygxNTAsMTEwKSwKICAgICAgICAg'
        'ICAgICAgICAgZmlzZXJhcGlzOklNRygxMjAsOTApLCBmaXNldGg6SU1HKDEyMCw5MCksIGJvYmFr'
        'aGE6SU1HKDE1MCwxMTApLAogICAgICAgICAgICAgICAgICBmaXRhdXJldDpJTUcoMTIwLDkwKSwg'
        'Ym9zZWtobWV0OklNRygxNTAsMTEwKX07CmNvbnN0IFBJQ1cgPSBXLnJ1bignSEdfUElDX1cnKSwg'
        'UElDSCA9IFcucnVuKCdIR19ST1cnKS02OwpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTgi'
        'KTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7IFcucnVuKCd0b2dnbGVTaGlwTWVudSgp'
        'Jyk7Clcuc2V0KCdJTUdTJywge30pOwpDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgpJyk7Cm9r'
        'KCdub3RoaW5nIGxvYWRlZCB5ZXQ6IG5vIHBpY3R1cmUsIG5vIGNyYXNoLCByb3dzIHN0aWxsIHRo'
        'ZXJlJywKICAgZHJhd3MoKS5sZW5ndGg9PT0wICYmIFcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycp'
        'Lmxlbmd0aD09PTgpOwpXLnNldCgnSU1HUycsIEFMTF9JTUdTKTsKQ0xSKCk7IFcucnVuKCdkcmF3'
        'U2hpcE1lbnUoKScpOwpvaygnb25lIGh1bGwgZHJhd24gcGVyIG9wZW4gcm93JywgZHJhd3MoKS5s'
        'ZW5ndGg9PT04KTsKLy8gVGhlIGdsb3NzIG9uIGVhY2ggcGxhdGUgY2xpcHMgYXMgd2VsbCwgc28g'
        'dGhpcyBjb3VudHMgYXQgbGVhc3Qgb25lIGNsaXAKLy8gcGVyIHBpY3R1cmUgcmF0aGVyIHRoYW4g'
        'ZXhhY3RseSBvbmUgaW4gdG90YWwuCm9rKCdlYWNoIG9uZSBjbGlwcGVkIHRvIGl0cyBvd24gY2Vs'
        'bCBmaXJzdCcsIGNsaXBzKCkubGVuZ3RoPj04KTsKb2soJ2VhY2ggb25lIGZpdHMgaW5zaWRlIHRo'
        'ZSBwaWN0dXJlIGNlbGwnLAogICBkcmF3cygpLmV2ZXJ5KGQ9PmQuYXJnc1szXTw9UElDVy01ICYm'
        'IGQuYXJnc1s0XTw9UElDSC01ICYmIGQuYXJnc1szXT4wICYmIGQuYXJnc1s0XT4wKSk7Cm9rKCdh'
        'c3BlY3QgcmF0aW8ga2VwdCcsIGRyYXdzKCkuZXZlcnkoZD0+TWF0aC5hYnMoKGQuYXJnc1szXS9k'
        'LmFyZ3NbNF0pIC0gKDEyMC85MCkpPDAuMDEKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg'
        'ICAgICAgICB8fCBNYXRoLmFicygoZC5hcmdzWzNdL2QuYXJnc1s0XSkgLSAoMTUwLzExMCkpPDAu'
        'MDEpKTsKb2soJ3NhdmUgYW5kIHJlc3RvcmUgc3RheSBiYWxhbmNlZCwgbm8gbGVha2luZyBjbGlw'
        'IG9yIGFscGhhJywgYmFsYW5jZWQoKSk7Cm9rKCdhIHBpY3R1cmUgaXMgYSBwaWN0dXJlIG5vdywg'
        'bm90IGEgd2F0ZXJtYXJrJywgYWxwaGFzKCkuZXZlcnkoYT0+YT4wLjkgJiYgYTw9MSkpOwp7CiAg'
        'Ly8gVGhyZWUgb3BlbiwgZml2ZSBsb2NrZWQ6IGEgbG9ja2VkIGh1bGwgaGFzIG5vIHJvdyB0YWxs'
        'IGVub3VnaCBmb3IgYQogIC8vIHBpY3R1cmUsIHNvIGl0IGdldHMgbm9uZSBhdCBhbGwuCiAgcmVz'
        'ZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIo'
        'KV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOwogIFcuc2V0KCdJTUdTJywgQUxMX0lNR1Mp'
        'OyBDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgpJyk7CiAgb2soJ2EgbG9ja2VkIGh1bGwgc2hv'
        'd3Mgbm8gcGljdHVyZScsIGRyYXdzKCkubGVuZ3RoPT09Myk7Cn0KcmVzZXQoKTsgVy5ydW4oInNo'
        'aXBVbmxvY2tlZD04Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9n'
        'Z2xlU2hpcE1lbnUoKScpOwpXLnNldCgnSU1HUycsIHtmaXRvdGg6SU1HKDAsMCl9KTsKQ0xSKCk7'
        'IFcucnVuKCdkcmF3U2hpcE1lbnUoKScpOwpvaygnYSB6ZXJvIHNpemVkIHNwcml0ZSBpcyBza2lw'
        'cGVkIGluc3RlYWQgb2YgZGl2aWRpbmcgYnkgemVybycsIGRyYXdzKCkubGVuZ3RoPT09MCk7Clcu'
        'c2V0KCdJTUdTJywge30pOwoKY29uc29sZS5sb2coJ0JhcnJlbHMgYW5kIHZvbGxleSBkYW1hZ2Us'
        'IGluIHRoZWlyIG93biBjb2x1bW5zJyk7CmNvbnN0IHRleHRzID0gKCk9PiBDQUxMUy5maWx0ZXIo'
        'Yz0+Yy5mbj09PSdmaWxsVGV4dCcpLm1hcChjPT4oe3M6U3RyaW5nKGMuYXJnc1swXSksIHg6Yy5h'
        'cmdzWzFdLCB5OmMuYXJnc1syXX0pKTsKLy8gQSBjb2x1bW4gaXMgY2hlY2tlZCBieSB3aGVyZSBp'
        'dCBhY3R1YWxseSBsYW5kczogdGhlIHggb2YgdGhlIGNvbHVtbiBpbiB0aGUKLy8gbGF5b3V0LCBh'
        'ZGRlZCB0byB0aGUgeCBvZiBhIHJvdyB0aGUgbWVudSBpdHNlbGYgcmVwb3J0ZWQuCmNvbnN0IGNv'
        'bFggPSAoayk9PiBXLnJ1bignSEdfQ09MUycpLmZpbmQoYz0+Yy5rPT09aykueDsKLy8gVGhlIGNv'
        'bHVtbiB0aXRsZXMgc2l0IG9uIHRoZSBzYW1lIHgsIHNvIGEgdmFsdWUgb25seSBjb3VudHMgd2hl'
        'biBpdCBhbHNvCi8vIHNpdHMgaW5zaWRlIGEgcm93Lgpjb25zdCBpbkNvbCA9IChrKT0+ewogIGNv'
        'bnN0IHgwID0gY29sWChrKSwgcnMgPSBXLnJ1bignd2luZG93Ll9zaGlwUmVjdHMnKTsKICByZXR1'
        'cm4gdGV4dHMoKS5maWx0ZXIodD0+IHJzLnNvbWUocj0+IHQueCA9PT0gci54ICsgeDAgJiYgdC55'
        'ID49IHIueSAmJiB0LnkgPD0gci55ICsgci5oKSk7Cn07CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5s'
        'b2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ3RvZ2dsZVNo'
        'aXBNZW51KCknKTsKVy5zZXQoJ01PVU5UUycsIHt9KTsKQ0xSKCk7IFcucnVuKCdkcmF3U2hpcE1l'
        'bnUoKScpOwpvaygnbm8gbW91bnQgZGF0YTogbm8gY2xhaW0gYWJvdXQgZ3VucyBvciB2b2xsZXkg'
        'YXQgYWxsJywKICAgaW5Db2woJ2d1bnMnKS5sZW5ndGg9PT0wICYmIGluQ29sKCd2b2xsZXknKS5s'
        'ZW5ndGg9PT0wKTsKVy5zZXQoJ01PVU5UUycsIHtmaXRvdGg6e3ByaW1hcnk6WzEsMV19LCBmaWhv'
        'cnVzOntwcmltYXJ5OlsxLDFdfSwgYm9vc2lyaXM6e3ByaW1hcnk6WzEsMV19LAogICAgICAgICAg'
        'ICAgICAgIGZpc2VyYXBpczp7cHJpbWFyeTpbMSwxXX0sIGZpc2V0aDp7cHJpbWFyeTpbMSwxXX0s'
        'IGJvYmFraGE6e3ByaW1hcnk6WzEsMV19LAogICAgICAgICAgICAgICAgIGZpdGF1cmV0Ontwcmlt'
        'YXJ5OlsxLDEsMV19LCBib3Nla2htZXQ6e3ByaW1hcnk6WzEsMV19fSk7CkNMUigpOyBXLnJ1bign'
        'ZHJhd1NoaXBNZW51KCknKTsKb2soJ2EgZmlndXJlIG9uIGV2ZXJ5IG9uZSBvZiB0aGUgZWlnaHQg'
        'cm93cycsCiAgIGluQ29sKCdndW5zJykubGVuZ3RoPT09OCAmJiBpbkNvbCgndm9sbGV5JykubGVu'
        'Z3RoPT09OCk7Cm9rKCd0aGUgc2V2ZW4gdHdvIGJhcnJlbCBodWxscyByZWFkIDIgYW5kIDUxJywK'
        'ICAgaW5Db2woJ2d1bnMnKS5maWx0ZXIodD0+dC5zPT09JzInKS5sZW5ndGg9PT03ICYmCiAgIGlu'
        'Q29sKCd2b2xsZXknKS5maWx0ZXIodD0+dC5zPT09JzUxJykubGVuZ3RoPT09Nyk7Cm9rKCd0aGUg'
        'VGF1cmV0IHJlYWRzIDMgYW5kIDU3JywKICAgaW5Db2woJ2d1bnMnKS5maWx0ZXIodD0+dC5zPT09'
        'JzMnKS5sZW5ndGg9PT0xICYmCiAgIGluQ29sKCd2b2xsZXknKS5maWx0ZXIodD0+dC5zPT09JzU3'
        'JykubGVuZ3RoPT09MSk7Cm9rKCd0aGUgZmlndXJlIG1hdGNoZXMgd2hhdCB2b2xsZXlEbWcgYWN0'
        'dWFsbHkgZG9lcycsCiAgIE1hdGgucm91bmQoVy5ydW4oJ3ZvbGxleVRvdGFsKDIpJykpPT09NTEg'
        'JiYgTWF0aC5yb3VuZChXLnJ1bigndm9sbGV5VG90YWwoMyknKSk9PT01NwogICAmJiBNYXRoLnJv'
        'dW5kKFcucnVuKCd2b2xsZXlUb3RhbCgxKScpKT09PTQ0KTsKb2soJ29uZSBiYXJyZWwgaXMgdGhl'
        'IGZhbGxiYWNrIG9mIHRoZSBmb3JtdWxhLCBub3QgYSBjcmFzaCcsIFcucnVuKCd2b2xsZXlUb3Rh'
        'bCgwKScpPT09NDQpOwp7CiAgLy8gVGhlIHBvaW50IG9mIHRoZSBjb2x1bW5zOiBodWxsIHNpdHMg'
        'dW5kZXIgaHVsbCBvbiBldmVyeSByb3cuCiAgY29uc3QgaHVsbHMgPSBpbkNvbCgnaHVsbCcpLm1h'
        'cCh0PT50LnMpLmpvaW4oKTsKICBvaygndGhlIGh1bGwgY29sdW1uIHJlYWRzIGRvd24gdGhlIGxp'
        'c3QgaW4gb3JkZXInLCBodWxscz09PScxMDAsODAsODAsMTI1LDEwMCwxNDAsMTAwLDE0MCcpOwog'
        'IGNvbnN0IHNoaWVsZHMgPSBpbkNvbCgnc2hpZWxkJykubWFwKHQ9PnQucykuam9pbigpOwogIG9r'
        'KCd0aGUgc2hpZWxkIGNvbHVtbiB0b28nLCBzaGllbGRzPT09JzEwMCwxMDAsNzAsMTMwLDEzMCwx'
        'MDAsMTAwLDEzMCcpOwogIG9rKCdldmVyeSB2YWx1ZSBpbiBhIGNvbHVtbiBzaGFyZXMgb25lIHgn'
        'LAogICAgIG5ldyBTZXQoaW5Db2woJ2h1bGwnKS5tYXAodD0+dC54KSkuc2l6ZT09PTEpOwp9CnsK'
        'ICAvLyBUd28gdW5sb2NrZWQgb2YgZWlnaHQ6IHRoZSBtZW51IG5lZWRzIHR3byB0byBvcGVuIGF0'
        'IGFsbC4KICByZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTIiKTsgVy5zZXQoJ2FsbGllcycs'
        'W2Rlc3Ryb3llcigpXSk7CiAgVy5zZXQoJ01PVU5UUycsIHtmaXRvdGg6e3ByaW1hcnk6WzEsMV19'
        'LCBmaWhvcnVzOntwcmltYXJ5OlsxLDFdfSwgZml0YXVyZXQ6e3ByaW1hcnk6WzEsMSwxXX19KTsK'
        'ICBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOyBDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgp'
        'Jyk7CiAgb2soJ29ubHkgdGhlIHR3byB1bmxvY2tlZCByb3dzIG1ha2UgYSBjbGFpbScsIGluQ29s'
        'KCdndW5zJykubGVuZ3RoPT09Mik7CiAgb2soJ3RoZSBsb2NrZWQgVGF1cmV0IHN0YXlzIHNpbGVu'
        'dCBldmVuIHdpdGggbW91bnQgZGF0YScsCiAgICAgaW5Db2woJ3ZvbGxleScpLmV2ZXJ5KHQ9PnQu'
        'cyE9PSc1NycpKTsKfQpXLnNldCgnTU9VTlRTJywge30pOwoKY29uc29sZS5sb2coJ09uZSBsb29r'
        'LCBhbmQgaXQgaXMgdGhlIGZvcnVtIG9uZScpOwpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2Vk'
        'PTMiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7IFcucnVuKCd0b2dnbGVTaGlwTWVu'
        'dSgpJyk7CkNMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKY29uc3QgaGxwRm9udHMgPSBD'
        'QUxMUy5maWx0ZXIoYz0+Yy5mbj09PSdzZXQgZm9udCcpLm1hcChjPT5TdHJpbmcoYy5hcmdzWzBd'
        'KSk7CmNvbnN0IGhscENlbGxzID0gVy5ydW4oJ3dpbmRvdy5fc2hpcFJlY3RzJykubWFwKHI9PnIu'
        'eCsnLCcrci55KycsJytyLncrJywnK3IuaCkuam9pbignfCcpOwpvaygnbm8gQ291cmllciBsZWZ0'
        'IGluIHRoZSBoYW5nYXInLCBobHBGb250cy5ldmVyeShmPT5mLmluZGV4T2YoJ0NvdXJpZXInKTww'
        'KSk7Cm9rKCdpdCB1c2VzIHRoZSBmb3J1bSBmYWNlcycsIGhscEZvbnRzLnNvbWUoZj0+Zi5pbmRl'
        'eE9mKCdUYWhvbWEnKT49MCkgJiYgaGxwRm9udHMuc29tZShmPT5mLmluZGV4T2YoJ1NlZ29lIFVJ'
        'Jyk+PTApKTsKb2soJ3ZhbHVlcyBhcmUgbm8gbG9uZ2VyIHNldCBpbiA4IGFuZCA5IHBpeGVscycs'
        'CiAgIGhscEZvbnRzLmZpbHRlcihmPT4vU2Vnb2UgVUkvLnRlc3QoZikpLnNvbWUoZj0+LzFbNC05'
        'XXB4Ly50ZXN0KGYpKSk7Cm9rKCd0aGUgYWN0aXZlIHJvdyBnZXRzIGEgZ2xvdyByaW5nJywgQ0FM'
        'TFMuc29tZShjPT5jLmZuPT09J3NldCBzaGFkb3dCbHVyJykpOwpvaygnbm8gcmluZyBsZWFrcyBv'
        'dXQgb2YgaXRzIHNhdmUvcmVzdG9yZScsIGJhbGFuY2VkKCkpOwpvaygnbm90aGluZyBjaG9vc2Vz'
        'IGJldHdlZW4gdHdvIGxvb2tzIGFueSBtb3JlJywgIS9FQ09cXC5odWQvLnRlc3Qoc3JjKSk7Clcu'
        'cnVuKCJFQ08uc2NoZW1lPSd2b2lkJyIpOyBDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgpJyk7'
        'Cm9rKCd0aGUgaGFuZ2FyIGRyYXdzIGluIFZvaWQgdG9vJywgQ0FMTFMubGVuZ3RoPjUwKTsKb2so'
        'J2FuZCB0aGUgcm93cyBkaWQgbm90IG1vdmUnLAogICBXLnJ1bignd2luZG93Ll9zaGlwUmVjdHMn'
        'KS5tYXAocj0+ci54KycsJytyLnkrJywnK3IudysnLCcrci5oKS5qb2luKCd8Jyk9PT1obHBDZWxs'
        'cyk7ClcucnVuKCJFQ08uc2NoZW1lPSdmaXJlJyIpOwoKY29uc29sZS5sb2coJ0V2ZXJ5dGhpbmcg'
        'aXMgZHJhd24gZnJvbSB0aGUgc3VyZmFjZSBraXQnKTsKewogIHJlc2V0KCk7IFcucnVuKCJzaGlw'
        'VW5sb2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ3RvZ2ds'
        'ZVNoaXBNZW51KCknKTsKICBDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgpJyk7CiAgLy8gR3Jh'
        'ZGllbnRzIGFyZSBhbGxvd2VkIGFnYWluLCBidXQgb25seSBhcyBnbG9zczogYSBzaG9ydCBmYWxs'
        'IG9mIGxpZ2h0CiAgLy8gb3ZlciB0aGUgdG9wIG9mIGEgcGxhdGUuIE5vbmUgbWF5IHJ1biB0aGUg'
        'aGVpZ2h0IG9mIGEgcGFuZWwgdGhlIHdheSB0aGUKICAvLyBvbGQgYm94IGdyYWRpZW50IGRpZC4K'
        'ICBjb25zdCBncmFkcyA9IENBTExTLmZpbHRlcihjPT5jLmZuPT09J2NyZWF0ZUxpbmVhckdyYWRp'
        'ZW50Jyk7CiAgb2soJ2V2ZXJ5IGdyYWRpZW50IGlzIGEgZ2xvc3MsIG5vdCBhIGZ1bGwgaGVpZ2h0'
        'IGZpbGwnLAogICAgIGdyYWRzLmxlbmd0aD4wICYmIGdyYWRzLmV2ZXJ5KGc9PihnLmFyZ3NbM10t'
        'Zy5hcmdzWzFdKTw9MjAwKSk7CiAgLy8gQSBjaGFtZmVyZWQgb3V0bGluZSBpcyBzaXggY29ybmVy'
        'cy4gQSByZWN0YW5nbGUgd291bGQgYmUgZm91ci4KICBjb25zdCBjbG9zZXMgPSBDQUxMUy5maWx0'
        'ZXIoYz0+Yy5mbj09PSdjbG9zZVBhdGgnKS5sZW5ndGg7CiAgb2soJ3RoZSBwYW5lbCBhbmQgZXZl'
        'cnkgcGxhdGUgYXJlIGNoYW1mZXJlZCwgbm90IHJlY3RhbmdsZXMnLCBjbG9zZXM+PTkpOwogIG9r'
        'KCdvbmUgc2NhbGUgdW5kZXIgZWFjaCBvZiB0aGUgdHdvIGdyb3VwIGhlYWRpbmdzJywKICAgICBD'
        'QUxMUy5maWx0ZXIoYz0+Yy5mbj09PSdzZXQgbGluZVdpZHRoJyAmJiBjLmFyZ3NbMF09PT0xKS5s'
        'ZW5ndGg+MCAmJiBjbG9zZXM+PTkpOwogIG9rKCdhIHJpbmcgaXMgZHJhd24sIGFuZCBvbmx5IGFy'
        'b3VuZCB0aGUgYWN0aXZlIHJvdycsCiAgICAgQ0FMTFMuZmlsdGVyKGM9PmMuZm49PT0nc2V0IHNo'
        'YWRvd0JsdXInICYmIGMuYXJnc1swXT09PTYpLmxlbmd0aD09PTIpOwogIG9rKCdub3RoaW5nIGxl'
        'YWtzIG91dCBvZiBhIHNhdmUvcmVzdG9yZScsIGJhbGFuY2VkKCkpOwp9CnsKICAvLyBUaGUga2l0'
        'IGlzIHNoYXJlZCwgc28gdGhlIGhhbmdhciBtdXN0IG5vdCByZWFjaCBwYXN0IGl0IGZvciBhIHNo'
        'YXBlIG9mCiAgLy8gaXRzIG93bi4gdGhCZXZlbCBhbmQgdGhQYW5lbCBiZWxvbmcgdG8gdGhlIHNj'
        'cmVlbnMgbm90IHlldCByZWJ1aWx0LgogIGNvbnN0IGEgPSBzcmMuaW5kZXhPZignZnVuY3Rpb24g'
        'ZHJhd1NoaXBNZW51KCknKTsKICBjb25zdCBib2R5ID0gc3JjLnNsaWNlKGEsIHNyYy5pbmRleE9m'
        'KCdmdW5jdGlvbiBkcmF3Q2FsbE1lbnUoKScpKTsKICBvaygndGhlIGhhbmdhciB1c2VzIG5vIGJl'
        'dmVsIGFuZCBubyBncmFkaWVudCBwYW5lbCcsCiAgICAgYm9keS5pbmRleE9mKCd0aEJldmVsJyk8'
        'MCAmJiBib2R5LmluZGV4T2YoJ3RoUGFuZWwnKTwwKTsKICBvaygnYW5kIG5vIGRpYWxvZyBmcmFt'
        'ZSBvZiBpdHMgb3duJywgYm9keS5pbmRleE9mKCd1aURpYWxvZycpPDApOwp9CnsKICAvLyBUaGUg'
        'ZGlnaXQgaXMgdGhlIGtleWJvYXJkIHNob3J0Y3V0LCBzbyBpdCBoYXMgdG8gZm9sbG93IHRoZSBo'
        'dWxsIHRocm91Z2gKICAvLyB0aGUgcmVncm91cGluZyByYXRoZXIgdGhhbiBjb3VudCByb3dzLgog'
        'IHJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJv'
        'eWVyKCldKTsgVy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsKICBDTFIoKTsgVy5ydW4oJ2RyYXdT'
        'aGlwTWVudSgpJyk7CiAgY29uc3QgcnMgPSBXLnJ1bignd2luZG93Ll9zaGlwUmVjdHMnKTsKICBj'
        'b25zdCBjaGlwWCA9IFcucnVuKCdIR19OVU0nKSArIFcucnVuKCdIR19OVU1fVycpLzI7CiAgY29u'
        'c3QgY2hpcCA9IChrZXkpPT57IGNvbnN0IHI9cnMuZmluZChyPT5yLnNoaXA9PT1rZXkpOwogICAg'
        'cmV0dXJuIHRleHRzKCkuZmluZCh0PT4gdC54PT09ci54K2NoaXBYICYmIHQueT49ci55ICYmIHQu'
        'eTw9ci55K3IuaCk7IH07CiAgb2soJ3RoZSBPc2lyaXMgc2hvd3MgNjogZmlyc3QgYm9tYmVyLCBz'
        'aXh0aCByb3cnLAogICAgIGNoaXAoJ2Jvb3NpcmlzJykgJiYgY2hpcCgnYm9vc2lyaXMnKS5zPT09'
        'JzYnKTsKICBvaygnYW5kIHRoZSBCYWtoYSBzaG93cyA3JywgY2hpcCgnYm9iYWtoYScpICYmIGNo'
        'aXAoJ2JvYmFraGEnKS5zPT09JzcnKTsKICBvaygndGhlIGRpZ2l0cyBydW4gMSB0byA4IHN0cmFp'
        'Z2h0IGRvd24gdGhlIHBhbmVsJywKICAgICBycy5tYXAocj0+Y2hpcChyLnNoaXApLnMpLmpvaW4o'
        'KT09PScxLDIsMyw0LDUsNiw3LDgnKTsKfQoKY29uc29sZS5sb2coJ1RoZSBwYW5lbCBncm93cyB3'
        'aXRoIHdoYXQgaXMgb3BlbicpOwp7CiAgY29uc3QgaGVpZ2h0ID0gKCk9PnsgY29uc3Qgcj1XLnJ1'
        'bignd2luZG93Ll9zaGlwUmVjdHMnKTsgcmV0dXJuIHJbci5sZW5ndGgtMV0ueStyW3IubGVuZ3Ro'
        'LTFdLmggLSByWzBdLnk7IH07CiAgcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0yIik7IFcu'
        'c2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKTsgZHJh'
        'd1NoaXBNZW51KCknKTsKICBjb25zdCBzbWFsbCA9IGhlaWdodCgpOwogIHJlc2V0KCk7IFcucnVu'
        'KCJzaGlwVW5sb2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4o'
        'J3RvZ2dsZVNoaXBNZW51KCk7IGRyYXdTaGlwTWVudSgpJyk7CiAgY29uc3QgYmlnID0gaGVpZ2h0'
        'KCk7CiAgb2soJ2VpZ2h0IG9wZW4gaHVsbHMgbmVlZCBtb3JlIHJvb20gdGhhbiB0d28nLCBiaWcg'
        'PiBzbWFsbCk7CiAgb2soJ2FuZCBpdCBzdGlsbCBmaXRzIG9uIHRoZSBmaWVsZCcsCiAgICAgVy5y'
        'dW4oJ3dpbmRvdy5fc2hpcFJlY3RzJykuZXZlcnkocj0+ci55Pj0wICYmIHIueStyLmg8PTUwMCkp'
        'Owp9Cgpjb25zb2xlLmxvZygnUmVhcm0gbmVlZHMgYSBjb3J2ZXR0ZSwgbm90IGFueSBzaGlwIGF0'
        'IGFsbCcpOwp7CiAgY29uc3QgY29ydmV0dGUgPSAoKT0+KHt0eXBlOidjb3J2ZXR0ZScsIHNpZGU6'
        'J2FsbHknLCBkZWFkOmZhbHNlLCB3YXJwT3V0OjAsIHdhcnA6MH0pOwogIHJlc2V0KCk7IFcuc2V0'
        'KCdhbGxpZXMnLCBbXSk7CiAgb2soJ25vdGhpbmcgb24gdGhlIGZpZWxkLCBubyByZWFybScsIFcu'
        'cnVuKCdyZWFybVJlYWR5KCknKT09PWZhbHNlKTsKICBXLnNldCgnYWxsaWVzJywgW2Rlc3Ryb3ll'
        'cigpXSk7CiAgb2soJ2EgZGVzdHJveWVyIGlzIGEgaGFuZ2FyLCBub3QgYW4gYXJtb3VyeScsIFcu'
        'cnVuKCdyZWFybVJlYWR5KCknKT09PWZhbHNlKTsKICBXLnNldCgnYWxsaWVzJywgW2NvcnZldHRl'
        'KCldKTsKICBvaygnYSBjb3J2ZXR0ZSBvcGVucyBpdCcsIFcucnVuKCdyZWFybVJlYWR5KCknKT09'
        'PXRydWUpOwogIGNvbnN0IHdhcnBpbmcgPSBjb3J2ZXR0ZSgpOyB3YXJwaW5nLndhcnAgPSA0MDsK'
        'ICBXLnNldCgnYWxsaWVzJywgW3dhcnBpbmddKTsKICBvaygnb25lIHN0aWxsIGNvbWluZyBvdXQg'
        'b2YgdGhlIHZvcnRleCBkb2VzIG5vdCcsIFcucnVuKCdyZWFybVJlYWR5KCknKT09PWZhbHNlKTsK'
        'ICBjb25zdCBkZWFkID0gY29ydmV0dGUoKTsgZGVhZC5kZWFkID0gdHJ1ZTsKICBXLnNldCgnYWxs'
        'aWVzJywgW2RlYWRdKTsKICBvaygnbm9yIGRvZXMgYSB3cmVjaycsIFcucnVuKCdyZWFybVJlYWR5'
        'KCknKT09PWZhbHNlKTsKICBXLnNldCgnYWxsaWVzJywgW2NvcnZldHRlKCldKTsKICBXLnNldCgn'
        'YWxsaWVzJywgW2NvcnZldHRlKCldKTsgICAvLyBhIGxpdmUgb25lIGFnYWluLCBhZnRlciB0aGUg'
        'd3JlY2sgYWJvdmUKICBXLnJ1bignY2xlYXJSZXN1bWVIb2xkKCknKTsgICAgICAvLyBhbmQgbm8g'
        'aG9sZCBsZWZ0IG92ZXIgZnJvbSBlYXJsaWVyCiAgLy8gUHJlc3MgdGhlIHJlY3RhbmdsZSB0aGUg'
        'YmFyIHJlcG9ydHMsIHRoZSB3YXkgYSBwbGF5ZXIgZG9lcy4gQ2FsbGluZwogIC8vIHRvZ2dsZVJl'
        'YXJtTWVudSgpIGhlcmUgdGVzdGVkIHRoZSBwYW5lbCBhbmQgbm90IHRoZSBidXR0b24sIHdoaWNo'
        'IGlzIGhvdwogIC8vIGEgYnV0dG9uIHRoYXQgd2FzIG5ldmVyIHdpcmVkIHRvIGFueXRoaW5nIHBh'
        'c3NlZC4KICAvLyBDbGVhciB0aGUgc2hpcCBidXR0b24gZmlyc3Q6IGFuIGVhcmxpZXIgY2FzZSBs'
        'ZWZ0IGEgcmVjdGFuZ2xlIHN0YW5kaW5nCiAgLy8gdGhhdCBjb3ZlcnMgdGhpcyBzcG90LCBhbmQg'
        'cG9pbnRlckNvbnN1bWVkIGFza3MgYWJvdXQgaXQgb25lIGxpbmUgc29vbmVyLgogIFcucnVuKCJ3'
        'aW5kb3cuX3NoaXBCdG5SZWN0PW51bGw7IHdpbmRvdy5fcmVhcm1CdG5SZWN0PXt4OjcwOSx5OjQs'
        'dzoyMixoOjQ2fTsiCiAgICAgICsgIiBwb2ludGVyQ29uc3VtZWQoe3g6NzE0LHk6MTJ9KSIpOwog'
        'IG9rKCdwcmVzc2luZyB0aGUgYnV0dG9uIGluIHRoZSBiYXIgb3BlbnMgdGhlIHBhbmVsJywgVy5n'
        'ZXQoJ3JlYXJtTWVudScpPT09dHJ1ZSk7CiAgVy5ydW4oInBvaW50ZXJDb25zdW1lZCh7eDo3MTQs'
        'eToxMn0pIik7CiAgb2soJ2FuZCBwcmVzc2luZyBpdCBhZ2FpbiBjbG9zZXMgaXQnLCBXLmdldCgn'
        'cmVhcm1NZW51Jyk9PT1mYWxzZSk7CiAgVy5ydW4oJ3NldFJlYXJtTWVudShmYWxzZSknKTsKfQoK'
        'Y29uc29sZS5sb2coJ1RoZSBzdGFuZGFyZCBmaXQgaXMgcHJvdmFibHkgdGhlIGd1biB0aGUgZ2Ft'
        'ZSBoYWQnKTsKewogIGNvbnN0IHAgPSBXLnJ1bigicHJpRGVmKCdwcm9tZXRoZXVzJykiKTsKICBv'
        'aygndGhlIFByb21ldGhldXMgY2FycmllcyBubyBmYWN0b3JzIGF0IGFsbCcsIHAuZG1nPT09MSAm'
        'JiBwLnJhdGU9PT0xKTsKICBvaygnYW5kIG5vIGxpbWl0IG9uIGl0cyByZWFjaCcsIHAucmFuZ2U9'
        'PT0wKTsKICByZXNldCgpOyBXLnJ1bigicGxheWVyLnByaT0ncHJvbWV0aGV1cyc7IGFwcGx5TG9h'
        'ZG91dCgpIik7CiAgb2soJ3NvIHRoZSByYXRlIG9mIGZpcmUgaXMgdGhlIG9sZCAyOCBzdGVwcycs'
        'IFcuZ2V0KCdwbGF5ZXInKS5mUj09PTI4KTsKICBjb25zdCBtID0gVy5ydW4oInNlY0RlZignbXg2'
        'NCcpIik7CiAgb2soJ3RoZSBNWC02NCBpcyB0aGUgb2xkIG1pc3NpbGUsIHRvIHRoZSBudW1iZXIn'
        'LAogICAgIG0uZG1nPT09MzUgJiYgbS5jZD09PTQ1ICYmIG0uc3BkPT09My41ICYmIG0ubGlmZT09'
        'PTIyMCAmJiBtLmhvbWluZz09PXRydWUpOwogIGNvbnN0IGMgPSBXLnJ1bigic2VjRGVmKCdjeWNs'
        'b3BzJykiKTsKICBvaygnYW5kIHRoZSBDeWNsb3BzIHRoZSBvbGQgYm9tYicsCiAgICAgYy5kbWc9'
        'PT04MCAmJiBjLmNkPT09OTAgJiYgYy5zcGQ9PT0xLjUgJiYgYy5saWZlPT09MzAwKTsKfQoKY29u'
        'c29sZS5sb2coJ0EgaHVsbCBjYW4gb25seSBjYXJyeSB3aGF0IGl0IGNhbiBjYXJyeScpOwp7CiAg'
        'cmVzZXQoKTsgVy5ydW4oImFwcGx5U2hpcCgnZml0b3RoJykiKTsKICBvaygnYSBmaWdodGVyIGlz'
        'IGdpdmVuIGEgbWlzc2lsZScsIFcucnVuKCJjdXJTZWMoKS5jbHMiKT09PSdtaXNzaWxlJyk7CiAg'
        'b2soJ2FuZCB0aGUgYmFyIGlzIHRvbGQgc28nLCBXLmdldCgncGxheWVyJykuc2VjVHlwZT09PSdt'
        'aXNzaWxlJyk7CiAgVy5ydW4oImFwcGx5U2hpcCgnYm9vc2lyaXMnKSIpOwogIG9rKCdhIGJvbWJl'
        'ciBjYW5ub3Qga2VlcCBpdCwgYW5kIGdldHMgYSBib21iJywgVy5ydW4oImN1clNlYygpLmNscyIp'
        'PT09J2JvbWInKTsKICBvaygnYW5kIHRoZSBiYXIgYWdhaW4nLCBXLmdldCgncGxheWVyJykuc2Vj'
        'VHlwZT09PSdib21iJyk7CiAgb2soJ29ubHkgYm9tYnMgYXJlIG9mZmVyZWQgdG8gaXQnLAogICAg'
        'IFcucnVuKCJzZWNvbmRhcmllc0ZvcignYm9vc2lyaXMnKSIpLmV2ZXJ5KHc9PncuY2xzPT09J2Jv'
        'bWInKSk7CiAgb2soJ2FuZCBvbmx5IG1pc3NpbGVzIHRvIGEgZmlnaHRlcicsCiAgICAgVy5ydW4o'
        'InNlY29uZGFyaWVzRm9yKCdmaXRvdGgnKSIpLmV2ZXJ5KHc9PncuY2xzPT09J21pc3NpbGUnKSk7'
        'CiAgb2soJ3RoZSByYWNrIHNpemUgc3RpbGwgY29tZXMgZnJvbSB0aGUgaHVsbCcsCiAgICAgVy5n'
        'ZXQoJ3BsYXllcicpLnNlY01heCA9PT0gVy5ydW4oInNoaXBTdGF0cygnYm9vc2lyaXMnKS5zZWMi'
        'KSk7Cn0KCmNvbnNvbGUubG9nKCdBIHJlZml0IGZpbGxzIHRoZSByYWNrIC0gdGhhdCBpcyB3aGF0'
        'IG1ha2VzIGl0IGEgcmVhcm0nKTsKewogIGNvbnN0IGNvcnZldHRlID0gKCk9Pih7dHlwZTonY29y'
        'dmV0dGUnLCBzaWRlOidhbGx5JywgZGVhZDpmYWxzZSwgd2FycE91dDowLCB3YXJwOjB9KTsKICBy'
        'ZXNldCgpOyBXLnJ1bigiYXBwbHlTaGlwKCdmaXRvdGgnKTsgc2NvcmU9MCIpOyBXLnNldCgnYWxs'
        'aWVzJywgW2NvcnZldHRlKCldKTsKICBXLnJ1bigncGxheWVyLnNlY0FtbW89MycpOwogIFcucnVu'
        'KCd0b2dnbGVSZWFybU1lbnUoKScpOwogIFcucnVuKCJmaXRXZWFwb24oJ214NjQnKSIpOwogIG9r'
        'KCdmaXR0aW5nIHdoYXQgaXMgYWxyZWFkeSBmaXR0ZWQgdG9wcyB0aGUgcmFjayB1cCcsCiAgICAg'
        'Vy5nZXQoJ3BsYXllcicpLnNlY0FtbW8gPT09IFcuZ2V0KCdwbGF5ZXInKS5zZWNNYXgpOwogIG9r'
        'KCdhbmQgY2xvc2VzIHRoZSBwYW5lbCcsIFcuZ2V0KCdyZWFybU1lbnUnKT09PWZhbHNlKTsKICAv'
        'LyBMb2NrZWQgd2VhcG9ucyBjYW5ub3QgYmUgdGFrZW4sIGhvd2V2ZXIgdGhleSBhcmUgcmVhY2hl'
        'ZC4KICBXLnJ1bigncGxheWVyLnNlY0FtbW89MzsgdG9nZ2xlUmVhcm1NZW51KCknKTsKICBXLnJ1'
        'bigiZml0V2VhcG9uKCdobDcnKSIpOwogIG9rKCdhIHdlYXBvbiBhYm92ZSB0aGUgc2NvcmUgY2Fu'
        'bm90IGJlIGZpdHRlZCcsIFcuZ2V0KCdwbGF5ZXInKS5wcmk9PT0ncHJvbWV0aGV1cycpOwogIG9r'
        'KCdhbmQgdGhlIHBhbmVsIHN0YXlzIG9wZW4nLCBXLmdldCgncmVhcm1NZW51Jyk9PT10cnVlKTsK'
        'ICBXLnJ1bignc2NvcmU9NjAwMCcpOwogIFcucnVuKCJmaXRXZWFwb24oJ2hsNycpIik7CiAgb2so'
        'J3Bhc3QgdGhlIHRocmVzaG9sZCBpdCBjYW4nLCBXLmdldCgncGxheWVyJykucHJpPT09J2hsNycp'
        'OwogIG9rKCdhbmQgdGhlIHJhdGUgb2YgZmlyZSBmb2xsb3dzIHRoZSB3ZWFwb24nLCBXLmdldCgn'
        'cGxheWVyJykuZlI9PT0xNyk7CiAgVy5ydW4oJ3Njb3JlPTA7IHBsYXllci5wcmk9InByb21ldGhl'
        'dXMiOyBhcHBseUxvYWRvdXQoKScpOwp9Cgpjb25zb2xlLmxvZygnVGhlIHJlYXJtIHBhbmVsJyk7'
        'CnsKICBjb25zdCBjb3J2ZXR0ZSA9ICgpPT4oe3R5cGU6J2NvcnZldHRlJywgc2lkZTonYWxseScs'
        'IGRlYWQ6ZmFsc2UsIHdhcnBPdXQ6MCwgd2FycDowfSk7CiAgcmVzZXQoKTsgVy5ydW4oImFwcGx5'
        'U2hpcCgnZml0b3RoJyk7IHNjb3JlPTkwMDAiKTsgVy5zZXQoJ2FsbGllcycsIFtjb3J2ZXR0ZSgp'
        'XSk7CiAgVy5ydW4oJ3RvZ2dsZVJlYXJtTWVudSgpJyk7CiAgQ0xSKCk7IFcucnVuKCdkcmF3UmVh'
        'cm1NZW51KCknKTsKICBjb25zdCBycyA9IFcucnVuKCd3aW5kb3cuX3JlYXJtUmVjdHMnKTsKICBj'
        'b25zdCBwciA9IFcucnVuKCd3aW5kb3cuX3JlYXJtUGFuZWxSZWN0Jyk7CiAgLy8gT25lIHJvdyBw'
        'ZXIgd2VhcG9uIHRoYXQgZXhpc3RzLCBvcGVuIG9yIG5vdDogYSBsb2NrZWQgb25lIGlzIGEgdGhp'
        'bgogIC8vIGxpbmUsIGFuZCBpdCBpcyBzdGlsbCBhIHJvdy4gVGhlIGNvdW50IGZvbGxvd3MgdGhl'
        'IHRhYmxlcyBzbyBhIG5ldwogIC8vIHdlYXBvbiBkb2VzIG5vdCBtYWtlIHRoaXMgZmFpbCBmb3Ig'
        'bm8gcmVhc29uLgogIGNvbnN0IG9mZmVyZWQgPSBXLnJ1bignUFJJTUFSSUVTJykubGVuZ3RoICsg'
        'Vy5ydW4oInNlY29uZGFyaWVzRm9yKCdmaXRvdGgnKSIpLmxlbmd0aDsKICBvaygnb25lIHJvdyBw'
        'ZXIgd2VhcG9uIG9uIG9mZmVyJywgcnMubGVuZ3RoPT09b2ZmZXJlZCk7CiAgb2soJ2V2ZXJ5IHJv'
        'dyBpcyBpbnNpZGUgdGhlIHBhbmVsJywKICAgICBycy5ldmVyeShyPT5yLng+PXByLnggJiYgci54'
        'K3Iudzw9cHIueCtwci53ICYmIHIueT49cHIueSAmJiByLnkrci5oPD1wci55K3ByLmgpKTsKICBv'
        'aygndGhlIHBhbmVsIGZpdHMgb24gdGhlIGZpZWxkJywgcHIueT49MCAmJiBwci55K3ByLmg8PTUw'
        'MCAmJiBwci54Pj0wICYmIHByLngrcHIudzw9ODAwKTsKICBvaygnbm8gQ291cmllciBhbnl3aGVy'
        'ZScsCiAgICAgQ0FMTFMuZmlsdGVyKGM9PmMuZm49PT0nc2V0IGZvbnQnKS5ldmVyeShjPT5TdHJp'
        'bmcoYy5hcmdzWzBdKS5pbmRleE9mKCdDb3VyaWVyJyk8MCkpOwogIG9rKCd0aGUgZml0dGVkIHdl'
        'YXBvbiBnZXRzIHRoZSByaW5nJywgQ0FMTFMuc29tZShjPT5jLmZuPT09J3NldCBzaGFkb3dCbHVy'
        'JykpOwogIG9rKCdub3RoaW5nIGxlYWtzIG91dCBvZiBhIHNhdmUvcmVzdG9yZScsIGJhbGFuY2Vk'
        'KCkpOwogIC8vIEEgY2xpY2sgaW5zaWRlIHRoZSBwYW5lbCB0aGF0IGhpdCBubyByb3cgbXVzdCBu'
        'b3QgY2xvc2UgaXQsIHRoZSBzYW1lCiAgLy8gcnVsZSB0aGUgaGFuZ2FyIGFuZCB0aGUgc3VwcG9y'
        'dCBtZW51IGZvbGxvdy4KICBXLnJ1bihgcG9pbnRlckNvbnN1bWVkKHt4OiR7cHIueCs0MH0seTok'
        'e3ByLnkrNn19KWApOwogIG9rKCdhIGNsaWNrIG9uIHRoZSBoZWFkZXIga2VlcHMgaXQgb3Blbics'
        'IFcuZ2V0KCdyZWFybU1lbnUnKT09PXRydWUpOwogIFcucnVuKGBwb2ludGVyQ29uc3VtZWQoe3g6'
        'JHtwci54LTEyfSx5OiR7cHIueStwci5oLzJ9fSlgKTsKICBvaygnYSBjbGljayBiZXNpZGUgaXQg'
        'Y2xvc2VzIGl0JywgVy5nZXQoJ3JlYXJtTWVudScpPT09ZmFsc2UpOwp9CnsKICAvLyBCZWxvdyB0'
        'aGUgdGhyZXNob2xkIHRoZSBITC03IGlzIGEgdGhpbiBsaW5lLCBub3QgYSByb3cgdGhhdCBjYW4g'
        'YmUgdGFrZW4uCiAgY29uc3QgY29ydmV0dGUgPSAoKT0+KHt0eXBlOidjb3J2ZXR0ZScsIHNpZGU6'
        'J2FsbHknLCBkZWFkOmZhbHNlLCB3YXJwT3V0OjAsIHdhcnA6MH0pOwogIHJlc2V0KCk7IFcucnVu'
        'KCJhcHBseVNoaXAoJ2ZpdG90aCcpOyBzY29yZT0wIik7IFcuc2V0KCdhbGxpZXMnLCBbY29ydmV0'
        'dGUoKV0pOwogIFcucnVuKCd0b2dnbGVSZWFybU1lbnUoKTsgZHJhd1JlYXJtTWVudSgpJyk7CiAg'
        'Y29uc3QgcnMgPSBXLnJ1bignd2luZG93Ll9yZWFybVJlY3RzJyk7CiAgb2soJ2EgbG9ja2VkIHdl'
        'YXBvbiByZXBvcnRzIG5vIGtleScsIHJzLnNvbWUocj0+ci5rZXk9PT1udWxsKSk7CiAgb2soJ2Fu'
        'ZCBpdHMgbGluZSBpcyB0aGlubmVyIHRoYW4gYSByb3cgdGhhdCBjYW4gYmUgdGFrZW4nLAogICAg'
        'IE1hdGgubWluKC4uLnJzLm1hcChyPT5yLmgpKSA8IE1hdGgubWF4KC4uLnJzLm1hcChyPT5yLmgp'
        'KSk7CiAgVy5ydW4oJ3NldFJlYXJtTWVudShmYWxzZSk7IHNjb3JlPTAnKTsKfQoKY29uc29sZS5s'
        'b2coJ1RoZSB0aXRsZSBzY3JlZW4nKTsKLy8gZHJhd1RpdGxlIGlzIHRvbyB0YW5nbGVkIHVwIHdp'
        'dGggdGhlIGJhY2tkcm9wIHRvIHJ1biBoZXJlLCBzbyB3aGF0IGlzCi8vIGNoZWNrZWQgaXMgdGhl'
        'IHR3byB0aGluZ3MgdGhhdCBtYWRlIGl0IGxvb2sgdGhlIHdheSBpdCBkaWQuCm9rKCdubyBvcGFx'
        'dWUgc2hlZXQgb3ZlciB0aGUgc2t5IGFueSBtb3JlJywgIS9maWxsU3R5bGU9J3JnYmFcKDAsMCw4'
        'LDBcLjc4XCknO2N0eFwuZmlsbFJlY3RcKDAsMCxXLEhcKS8udGVzdChzcmMpKTsKb2soJ3doYXQg'
        'aXMgbGVmdCBpcyBhIGdyYWRpZW50LCBzbyB0aGUgYmFja2Ryb3Agc2hvd3MgdGhyb3VnaCB0aGUg'
        'dG9wJywKICAgL2NyZWF0ZUxpbmVhckdyYWRpZW50XCgwLCAwLCAwLCBIXClbXHNcU117MCwyNjB9'
        'P3JnYmFcKDAsMCw4LDBcLjIwXCkvLnRlc3Qoc3JjKSk7Cm9rKCd0aGUgcGFzdGVkIGxvZ28gYW5k'
        'IGl0cyAzIGFyZSBnb25lJywKICAgIS9fbG9nb1Byb2Nlc3NlZC8udGVzdChzcmMpICYmICEvZnNf'
        'bG9nby8udGVzdChzcmMpKTsKb2soJ3RoZSB0aXRsZSBpcyBzZXQgaW4gdGhlIHRoZW1lIGZhY2Ug'
        'aW5zdGVhZCcsIC9GUkVFU1BBQ0UvLnRlc3Qoc3JjKSAmJiAvdGhMYWJlbFwoNTRcKS8udGVzdChz'
        'cmMpKTsKb2soJ2EgZnJlc2ggYmFja2Ryb3AgaXMgcm9sbGVkIGV2ZXJ5IHRpbWUgdGhlIHRpdGxl'
        'IGNvbWVzIHVwJywKICAgL2Z1bmN0aW9uIGVudGVyVGl0bGVcKFwpXHtbXHNcU117MCwzMDB9P25l'
        'YkN1ciA9IE5FQl9OQU1FU1tcc1xTXXswLDEyMH0/cm9sbEJvZGllc1woXCkvLnRlc3Qoc3JjKSk7'
        'Cm9rKCdhbmQgYSBib2R5IHRoYXQgbGVhdmVzIHRoZSB0aXRsZSBpcyByZXBsYWNlZCwgbm90IHdy'
        'YXBwZWQgcm91bmQnLAogICAvaWZcKEdTPT09J3RpdGxlJ1wpXHsgcm9sbEJvZGllc1woXCk7IHJl'
        'dHVybjsgXH0vLnRlc3Qoc3JjKSk7Cm9rKCd0aGUgdGl0bGUga2VlcHMgbW92aW5nIHdoaWxlIGl0'
        'IHNpdHMgdGhlcmUnLAogICAvaWZcKEdTPT09J3RpdGxlJ1wpXHsgZmNcK1wrOyB0aWNrU3RhcnNc'
        'KFwpOyB0aWNrTmVidWxhXChcKTsgcmV0dXJuOyBcfS8udGVzdChzcmMpKTsKb2soJ1RyeSBBZ2Fp'
        'biBnb2VzIGJhY2sgdG8gdGhlIHRpdGxlIHJhdGhlciB0aGFuIGludG8gdGhlIG5leHQgcnVuJywK'
        'ICAgL2Z1bmN0aW9uIHRvVGl0bGVPckxhdW5jaFwoXClce1tcc1xTXXswLDE2MH0/R1M9PT0nZ2Ft'
        'ZW92ZXInXCl7IGVudGVyVGl0bGVcKFwpLy50ZXN0KHNyYykpOwpvaygnYW5kIG5vdGhpbmcgY2Fs'
        'bHMgbGF1bmNoR2FtZSBzdHJhaWdodCBmcm9tIHRoZSBnYW1lIG92ZXIgc2NyZWVuJywKICAgIS9n'
        'YW1lT3ZlckF0PjE1MDBcKSBsYXVuY2hHYW1lXChcKS8udGVzdChzcmMpKTsKCmNvbnNvbGUubG9n'
        'KCdCYXIgYnV0dG9uIHBsYWNlbWVudCcpOwp7CiAgLy8gVGhlIHNoaXAgc3dpdGNoIGFuZCB0aGUg'
        'cmVhcm0gYnV0dG9uIGFyZSBkcmF3biBhcyBvbmUgcGFpciBub3csIHNvIHRoZQogIC8vIHNuaXBw'
        'ZXQgY292ZXJzIGJvdGggYW5kIGJvdGggYXJlIGNoZWNrZWQuCiAgY29uc3QgYSA9IHNyYy5pbmRl'
        'eE9mKCcgIC8vIFNISVAgU1dJVENIIGFuZCBSRUFSTScpLCBiID0gc3JjLmluZGV4T2YoJyAgLy8g'
        'U0VUVElOR1MgYW5kIFBBVVNFJyk7CiAgY29uc3Qgc25pcCA9IHNyYy5zbGljZShhLCBiKTsKICBX'
        'LnJ1bigidmFyIEgyPTU0OyBzaGlwTWVudT1mYWxzZTsgcmVhcm1NZW51PWZhbHNlOyBhbGxpZXM9'
        'W107IgogICAgICArICIgd2luZG93Ll9zaGlwQnRuUmVjdD11bmRlZmluZWQ7IHdpbmRvdy5fcmVh'
        'cm1CdG5SZWN0PXVuZGVmaW5lZDsgIiArIHNuaXApOwogIGNvbnN0IHIgPSBXLnJ1bignd2luZG93'
        'Ll9zaGlwQnRuUmVjdCcpLCBybSA9IFcucnVuKCd3aW5kb3cuX3JlYXJtQnRuUmVjdCcpOwogIG9r'
        'KCd0aGUgc2hpcCBidXR0b24gc2l0cyBiZXR3ZWVuIHRpY2tldHMgKDY2NSkgYW5kIGdlYXIgKDc0'
        'OCknLCByICYmIHIueD42NjUgJiYgci54K3Iudzw3NDgpOwogIG9rKCd0aGUgcmVhcm0gYnV0dG9u'
        'IHNpdHMgYmVzaWRlIGl0LCBhbHNvIGNsZWFyIG9mIHRoZSBnZWFyJywKICAgICBybSAmJiBybS54'
        'ID49IHIueCtyLncgJiYgcm0ueCtybS53IDwgNzQ4KTsKICBvaygndGhleSBkbyBub3Qgb3Zlcmxh'
        'cCcsIHJtICYmIHJtLnggPj0gci54ICsgci53KTsKICBXLnJ1bigiRlMxX01PREU9dHJ1ZTsgIiAr'
        'IHNuaXApOwogIG9rKCduZWl0aGVyIGJ1dHRvbiBpbiBGUzEgbW9kZScsCiAgICAgVy5ydW4oJ3dp'
        'bmRvdy5fc2hpcEJ0blJlY3QnKT09PW51bGwgJiYgVy5ydW4oJ3dpbmRvdy5fcmVhcm1CdG5SZWN0'
        'Jyk9PT1udWxsKTsKICBXLnJ1bignRlMxX01PREU9ZmFsc2UnKTsKfQpjb25zb2xlLmxvZygnQ3lj'
        'bGUgc2NhbGluZyBrZWVwcyB0aGUgaHVsbCcpOwpvaygnbmV4dFdhdmUgc2NhbGVzIGZyb20gdGhl'
        'IGh1bGwgYmFzZSwgbm90IGZyb20gMTAwJywgc3JjLmluY2x1ZGVzKCdwbGF5ZXIubWF4SHA9TWF0'
        'aC5yb3VuZCgocGxheWVyLmJhc2VIcHx8MTAwKSpwbSk7JykpOwpvaygncmVzcGF3biByZXN0b3Jl'
        'cyB0aGUgZnVsbCBodWxsJywgc3JjLmluY2x1ZGVzKCdwbGF5ZXIuaHA9cGxheWVyLm1heEhwO3Bs'
        'YXllci54PTgwOycpKTsKCmNvbnNvbGUubG9nKCdcbicgKyAoZmFpbHMgPyBmYWlscysnIEZBSUxF'
        'RCcgOiAnYWxsIHBhc3NlZCcpKTsKcHJvY2Vzcy5leGl0KGZhaWxzPzE6MCk7Cg=='
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
        'YXdQYXVzZWQnLAogICAnZHJhd1N1Yk1zZ3MnLCdkcmF3VGlja2V0TXNncycsJ2RyYXdJdGVtcycs'
        'J2RyYXdIdWxsQmxvY2tzJywnZHJhd1N1YnN5c3RlbXMnXS5mb3JFYWNoKHdyYXApOwogIC8vIFNv'
        'bWV0aGluZyBpbiBlYWNoIG9mIHRoZW0gdG8gZHJhdy4KICBjb25zdCBjYXAgPSBlbmVtaWVzLmZp'
        'bmQoZT0+ZS50eXBlPT09J2NydWlzZXInfHxlLnR5cGU9PT0nY29ydmV0dGUnKSB8fCBlbmVtaWVz'
        'WzBdOwogIFNVQl9NU0dTLnB1c2goe3g6MzAwLCB5OjI1MCwgdHh0OidET0NLRUQnLCBsaWZlOjE1'
        'MCwgbWw6MTUwLCBhbGx5OnRydWUsIHRvbmU6J2dvb2QnfSk7CiAgVElDS0VUX01TR1MucHVzaCh7'
        'eDozMjAsIHk6MjYwLCBraW5kOidjcnVpc2VyJywgbGlmZToxNTAsIG1sOjE1MCwgcmVwOmZhbHNl'
        'fSk7CiAgSVRFTVMucHVzaCh7eDozNDAsIHk6MjcwLCB2eDowLCB2eTowLCBraW5kOidsaWZlJywg'
        'bGlmZTo1MDB9KTsKICBJVEVNUy5wdXNoKHt4OjM2MCwgeToyNzAsIHZ4OjAsIHZ5OjAsIGtpbmQ6'
        'J2NvcnZldHRlJywgbGlmZTo1MDB9KTsKICBub3RpY2UoJ1RFU1QgTk9USUNFJywgJ2luZm8nKTsK'
        'ICBjdHguZmlsbFRleHQgPSBmdW5jdGlvbigpeyBpZihpbnNpZGUpIHVzZWQucHVzaChjdHguZm9u'
        'dCk7IHJldHVybiBvZi5hcHBseSh0aGlzLCBhcmd1bWVudHMpOyB9OwogIG9iakFubm91bmNlKCdO'
        'RVcgT0JKRUNUSVZFJywgJ1RFU1QnLCAnbmV3Jyk7IG9iakNhcmQudDAgPSBmYyAtIDQwOwogIGRy'
        'YXcoKTsKICB1c2VyUGF1c2VkID0gdHJ1ZTsgc3luY1BhdXNlKCk7IGRyYXcoKTsKICBjdHguZmls'
        'bFRleHQgPSBvZjsKICByZXR1cm4ge3NvbWV0aGluZ0RyYXduOiB1c2VkLmxlbmd0aD49NCwgZmxl'
        'ZVNob3duOiBmbGVlaW5nRW5lbWllcygpLmxlbmd0aD4wLCBub0NvdXJpZXI6IHVzZWQuZXZlcnko'
        'Zj0+IS9Db3VyaWVyLy50ZXN0KGYpKX07YCk7CgpzY2VuYXJpbygnTm90aWNlczogYSBjb2x1bW4s'
        'IG5vdCB0aGUgZmllbGQnLCAnbT0zMScsIGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCgzMDAp'
        'OwogIHNjb3JlID0gY3ljbGVCYXNlICsgNDAwMDsgdGlja1NoaXBVbmxvY2tzKCk7CiAgci51bmxv'
        'Y2tJc0FOb3RpY2UgPSBOT1RJQ0VTLmxlbmd0aD4wICYmIE5PVElDRVNbMF0udHh0PT09J0dURiBI'
        'RVJDVUxFUyBBVkFJTEFCTEUnICYmIE5PVElDRVNbMF0udG9uZT09PSd1bmxvY2snOwogIHIubm90'
        'SW5UaGVGaWVsZCA9ICFTVUJfTVNHUy5zb21lKG09Pi9BVkFJTEFCTEUvLnRlc3QobS50eHQpKTsK'
        'ICBjb25zdCBwbGF0ZXMgPSBbXTsgY29uc3Qgb3AgPSB0aFBsYXRlOwogIHRoUGxhdGUgPSBmdW5j'
        'dGlvbih4LHksdyxoKXsgcGxhdGVzLnB1c2goe3gseSx3LGh9KTsgcmV0dXJuIG9wLmFwcGx5KHRo'
        'aXMsIGFyZ3VtZW50cyk7IH07CiAgZHJhdygpOyB0aFBsYXRlID0gb3A7CiAgci5vblRoZUxlZnRV'
        'bmRlclRoZUJhciA9IHBsYXRlcy5zb21lKHA9PnAueD09PTggJiYgcC55Pj1IVURfSCs2ICYmIHAu'
        'aD09PTE4KTsKICBmb3IobGV0IGk9MDtpPDU7aSsrKSBub3RpY2UoJ04nK2ksICdpbmZvJyk7CiAg'
        'ci5hdE1vc3RUaHJlZU5ld2VzdEZpcnN0ID0gTk9USUNFUy5sZW5ndGg9PT0zICYmIE5PVElDRVNb'
        'MF0udHh0PT09J040JyAmJiBOT1RJQ0VTWzJdLnR4dD09PSdOMic7CiAgRlMuc3RlcChOT1RJQ0Vf'
        'VElNRSszMCk7IGRyYXcoKTsKICByLnRoZXlHb0FnYWluID0gTk9USUNFUy5sZW5ndGg9PT0wOwog'
        'IHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ05vdGljZXM6IHJhZGlvIGxpbmVzIG9mIGEgbWlzc2lv'
        'bicsICdtPTM0JywgYAogIEZTLnN0ZXAoNDAwKTsKICBGUy51bnRpbCgoKT0+Tk9USUNFUy5zb21l'
        'KG49Pi9PUklPTiBJTkJPVU5ELy50ZXN0KG4udHh0KSksIDYwMDAsIHRydWUpOwogIHJldHVybiB7'
        'b3Jpb25JbmJvdW5kOiBOT1RJQ0VTLnNvbWUobj0+bi50eHQ9PT0nR1REIE9SSU9OIElOQk9VTkQg'
        'LSBIQU5HQVIgT1BFTicgJiYgbi50b25lPT09J2luZm8nKSwKICAgICAgICAgIG5vdEluVGhlRmll'
        'bGQ6ICFTVUJfTVNHUy5zb21lKG09Pi9JTkJPVU5EL2kudGVzdChtLnR4dCkpfTtgKTsKCnNjZW5h'
        'cmlvKCdIdWxsIGJhbmQ6IGNhbG0sIGxpdCBieSBhIGhpdCwgZnVsbCB3aGVuIG5lYXJseSBkZWFk'
        'JywgJ209NDInLCBgCiAgRlMuc3RlcCg0MDApOwogIGNvbnN0IHYgPSBlbmVtaWVzLmZpbmQoZT0+'
        'ZS51aWQ9PT0nVjEnKTsKICBjb25zdCByID0ge307CiAgdi5faGJIaXQgPSBmYyAtIEhCX0hPVCAt'
        'IDE7IHYuX2hiTGFzdCA9IHYuaHA7IGRyYXcoKTsKICByLmNhbG1Jc0hhbGYgPSBNYXRoLmFicyh2'
        'Ll9oYkFscGhhIC0gSEJfQ0FMTSkgPCAxZS05OwogIHYuX2hiTGFzdCA9IHYuaHAgKyAxMDsgZHJh'
        'dygpOwogIHIuYUhpdExpZ2h0c0l0VXAgPSBNYXRoLmFicyh2Ll9oYkFscGhhIC0gMSkgPCAxZS05'
        'OwogIHYuX2hiSGl0ID0gZmMgLSBIQl9IT1QvMjsgdi5faGJMYXN0ID0gdi5ocDsgZHJhdygpOwog'
        'IHIuYW5kSXRTZXR0bGVzID0gdi5faGJBbHBoYSA+IEhCX0NBTE0gJiYgdi5faGJBbHBoYSA8IDE7'
        'CiAgdi5faGJIaXQgPSBmYyAtIEhCX0hPVCAtIDE7IHYuaHAgPSB2Lm1heEhwKjAuMTsgdi5faGJM'
        'YXN0ID0gdi5ocDsgZHJhdygpOwogIHIubmVhcmx5RGVhZFN0YXlzRnVsbCA9IE1hdGguYWJzKHYu'
        'X2hiQWxwaGEgLSAxKSA8IDFlLTk7CiAgci5jb2xvdXJSdW5zU21vb3RobHkgPSBodWxsQmFuZENv'
        'bCgxKT09PSdyZ2IoNjAsMjI0LDEwNiknICYmIGh1bGxCYW5kQ29sKDAuNSk9PT0ncmdiKDI1NSwy'
        'MDQsNjgpJwogICAgICAgICAgICAgICAgICAgICAgJiYgaHVsbEJhbmRDb2woMCk9PT0ncmdiKDI1'
        'NSw3NCw1MSknICYmIGh1bGxCYW5kQ29sKDAuNzUpIT09aHVsbEJhbmRDb2woMC44KTsKICByZXR1'
        'cm4gcjtgKTsKCnNjZW5hcmlvKCdDb2xvc3N1cyBiZWFtcyBhcmUgVGVycmFuJywgJycsIGAKICBy'
        'ZXR1cm4ge21haW46IGJlYW1Db2woJ2d0dmEnLCB0cnVlKT09PScjMDBmZjU1JywgYW50aUZpZ2h0'
        'ZXI6IGJlYW1Db2woJ2d0dmEnLCBmYWxzZSk9PT0nIzQ0OTlmZid9O2AsIHRydWUpOwoKc2NlbmFy'
        'aW8oJ0hvTCBzdGFydCB1bmNoYW5nZWQnLCAnbT0xJywgYAogIHJldHVybiB7d2F2ZTogd2F2ZSwg'
        'dGhvdGg6IHBsYXllci5zaGlwPT09J2ZpdG90aCcsIHZhc3VkYW5DYWxsOiBBTExZX0ZBQ19PTi52'
        'YXN1ZGFuPT09dHJ1ZSAmJiBBTExZX0ZBQ19PTi50ZXJyYW49PT1mYWxzZX07YCk7CgovLyDilIDi'
        'lIAgUnVubmVyIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgAooYXN5bmMoKT0+ewogIGNvbnN0IGJyb3dzZXIgPSBhd2Fp'
        'dCBjaHJvbWl1bS5sYXVuY2goKTsKICBsZXQgZmFpbHMgPSAwOwogIGNvbnN0IG9ubHkgPSBwcm9j'
        'ZXNzLmFyZ3ZbNF07CiAgZm9yKGNvbnN0IHNjIG9mIHNjZW5hcmlvcyl7CiAgICBpZihvbmx5ICYm'
        'IHNjLm5hbWUuaW5kZXhPZihvbmx5KTwwKSBjb250aW51ZTsKICAgIGNvbnN0IHBhZ2UgPSBhd2Fp'
        'dCBicm93c2VyLm5ld1BhZ2UoKTsKICAgIGNvbnN0IGVycnMgPSBbXTsKICAgIHBhZ2Uub24oJ3Bh'
        'Z2VlcnJvcicsIGU9PmVycnMucHVzaChTdHJpbmcoZS5tZXNzYWdlfHxlKSkpOwogICAgYXdhaXQg'
        'cGFnZS5nb3RvKCdmaWxlOi8vJyArIHRtcCArICc/JyArIHNjLnF1ZXJ5KTsKICAgIGF3YWl0IHBh'
        'Z2Uud2FpdEZvclRpbWVvdXQoMzAwKTsKICAgIGxldCByZXM7CiAgICB0cnl7CiAgICAgIHJlcyA9'
        'IGF3YWl0IHBhZ2UuZXZhbHVhdGUoSEVMUEVSUyArIGBcbkZTLmZha2VJbWFnZXMoKTtgICsgKHNj'
        'Lm5vTGF1bmNoID8gJycgOiAnIGxhdW5jaEdhbWUoKTsnKSArIGBcbihmdW5jdGlvbigpeyR7c2Mu'
        'Ym9keX19KSgpYCk7CiAgICB9Y2F0Y2goZSl7IHJlcyA9IG51bGw7IGVycnMucHVzaChTdHJpbmco'
        'ZS5tZXNzYWdlfHxlKSk7IH0KICAgIGNvbnNvbGUubG9nKHNjLm5hbWUgKyAnICAoPycgKyBzYy5x'
        'dWVyeSArICcpJyk7CiAgICBpZihyZXMpIGZvcihjb25zdCBbayx2XSBvZiBPYmplY3QuZW50cmll'
        'cyhyZXMpKXsKICAgICAgY29uc3QgZ29vZCA9ICh0eXBlb2Ygdj09PSdib29sZWFuJykgPyB2IDog'
        'dHJ1ZTsKICAgICAgaWYoIWdvb2QpIGZhaWxzKys7CiAgICAgIGNvbnNvbGUubG9nKChnb29kID8g'
        'JyAgb2sgICAgJyA6ICcgIEZBSUwgICcpICsgayArICh0eXBlb2Ygdj09PSdib29sZWFuJyA/ICcn'
        'IDogJyA9ICcgKyBKU09OLnN0cmluZ2lmeSh2KSkpOwogICAgfQogICAgaWYoZXJycy5sZW5ndGgp'
        'eyBmYWlscysrOyBjb25zb2xlLmxvZygnICBGQUlMICBwYWdlIGVycm9yczpcbiAgICAnICsgZXJy'
        'cy5zbGljZSgwLDQpLmpvaW4oJ1xuICAgICcpKTsgfQogICAgYXdhaXQgcGFnZS5jbG9zZSgpOwog'
        'IH0KICBhd2FpdCBicm93c2VyLmNsb3NlKCk7CiAgZnMudW5saW5rU3luYyh0bXApOwogIGNvbnNv'
        'bGUubG9nKCdcbicgKyAoZmFpbHMgPyBmYWlscyArICcgRkFJTEVEJyA6ICdhbGwgcGFzc2VkJykp'
        'OwogIHByb2Nlc3MuZXhpdChmYWlscyA/IDEgOiAwKTsKfSkoKTsK'
    ),
}
for name, data in TEST_FILES.items():
    open(name, 'wb').write(base64.b64decode(data))
print("v134 applied: notice column, quieter marks, hull band, no Courier in the field, checks updated. Now run: python3 assemble.py 134")
