#!/usr/bin/env python3
"""FS3 v130 - fixes and changes from the v129 test.

M31 Der Aufstand
  The Leviathan that goes over faced the wrong way: the NTF hull is drawn
  facing left, and a ship that simply stood there kept that. Now, once she
  has turned, she heads for the right edge facing where she goes, and the
  moment she gets there she jumps out. The player has to stop her - kill
  her, or kill her engines, which stops the run as it does for every ship
  on an escape course. She turns with at least 60 % hull, so she is a
  target and not a wreck the allied wings finish off.

M35 Der Ueberlaeufer
  The Deimos crosses from right to left now, away from the NTF side. And
  the fight no longer runs dry halfway: once the first wing is down,
  reinforcements keep coming until she is across. When she jumps, anything
  still queued is dropped and nothing more arrives.

M36 Die Iceni
  Her stern hung out of the picture. Her station point was a fixed distance
  from the edge, which does not fit a hull that size; it is now worked out
  from her width so the whole ship is on screen. Same for the Iceni the
  random waves bring.

Pickups (tickets, hull repair, extra life)
  Once the ship comes within reach they are drawn to it like a magnet, and
  having been caught they follow it until collected.

Also
  An ally that leaves at the end of its crossing now counts as having left
  ('verlaesst' fires). Before this only the 'raus' effect set it, so an
  event waiting for a crossing ship to leave never fired (also M005).

Needs v129 applied first. Edits src/30_waves.js, src/40_world.js and
src/60_effects.js in place, and writes the updated fieldsim.js.
Run assemble.py afterwards.
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
fx = load("src/60_effects.js")

# ══ 30_waves.js ═════════════════════════════════════════════════════════

# ── M31: after the turn she runs for the right edge ────────────────────
wv = replace_once(
    wv,
    "  e.hp = Math.max(1, Math.round(e.maxHp * (a.maxHp ? a.hp/a.maxHp : 1)));\n"
    "  e.uid = a.uid;\n"
    "  enemies.push(e);\n",
    "  e.hp = Math.max(1, Math.round(e.maxHp * (a.maxHp ? a.hp/a.maxHp : 1)));\n"
    "  e.uid = a.uid;\n"
    "  // She turns with at least DEFECT_MIN_HULL of her hull. Held at the\n"
    "  // lock's floor until the turn, she would otherwise go over as a wreck\n"
    "  // that the allied wings finish before the player gets a shot in.\n"
    "  e.hp = Math.max(e.hp, Math.round(e.maxHp*DEFECT_MIN_HULL));\n"
    "  // defectRun: after the turn she makes for the right edge, facing where\n"
    "  // she goes, and jumps out the moment she gets there. The same course\n"
    "  // as any escaper, so killing her engines stops her.\n"
    "  if(a.defectRun){\n"
    "    e.escaping = a.defectRun;\n"
    "    e.escWarp = true;\n"
    "    e.noFlee = true;\n"
    "    const _ri = IMGS[e.img];\n"
    "    e.targetX = W + (_ri ? _ri.width*e.sc : 120)*2;\n"
    "    e.vx = 0;\n"
    "    e.flip = needsFlip(e.img, false);\n"
    "    escTotal++;\n"
    "  }\n"
    "  enemies.push(e);\n",
    "defectCap: run")

wv = replace_once(
    wv,
    "function defectCap(a){\n",
    "const DEFECT_MIN_HULL = 0.6;\n"
    "function defectCap(a){\n",
    "DEFECT_MIN_HULL")

# An escaper with escWarp jumps as soon as its hull is fully at the right
# edge, instead of driving out of the picture. The jump itself runs through
# runFlee(), which already takes the flee penalty when it completes.
wv = replace_once(
    wv,
    "    e.x += e.escaping;\n"
    "    // Erst weg, wenn der Rumpf ganz draussen ist - nicht wenn die Mitte\n"
    "    // den Rand erreicht und das Heck noch im Bild steht.\n"
    "    const _ei = IMGS[e.img];\n"
    "    const _ew = _ei ? _ei.width*e.sc : 120;\n",
    "    e.x += e.escaping;\n"
    "    // Erst weg, wenn der Rumpf ganz draussen ist - nicht wenn die Mitte\n"
    "    // den Rand erreicht und das Heck noch im Bild steht.\n"
    "    const _ei = IMGS[e.img];\n"
    "    const _ew = _ei ? _ei.width*e.sc : 120;\n"
    "    if(e.escWarp && e.x + _ew*0.5 >= W - TRANS_EDGE_PAD){\n"
    "      e.escaping = 0;\n"
    "      escGone++;\n"
    "      EV_LEFT[e.uid] = true;\n"
    "      e.warpOut = e.warpMax > 1 ? e.warpMax : 160;\n"
    "      e.warpX = e.x; e.warpY = e.y;\n"
    "      SUB_MSGS.push({x:W-110, y:e.y, txt:'TARGET ESCAPED', life:170, ml:170,\n"
    "                     ally:false, tone:'bad'});\n"
    "      continue;\n"
    "    }\n",
    "tickEscapers: escWarp")

# The mission unit carries defectRun and crossDir through to the ally.
wv = replace_once(
    wv,
    "             crossSecs:u.crossSecs, still:u.still}\n",
    "             crossSecs:u.crossSecs, still:u.still,\n"
    "             crossDir:u.crossDir, defectRun:u.defectRun}\n",
    "scriptUnit: ally options")

wv = replace_once(
    wv,
    "       {id:'A1', c:'cr', n:1, spr:'crleviathan', side:'ally'},\n",
    "       // After the turn she runs for the right edge and jumps out there.\n"
    "       {id:'A1', c:'cr', n:1, spr:'crleviathan', side:'ally', defectRun:0.25},\n",
    "M31: defectRun")

wv = replace_once(
    wv,
    "       // An NTF Deimos coming over to the GTVA, still in NTF markings.\n"
    "       // Her own side wants her dead before she is across.\n"
    "       {id:'A1', c:'co', n:1, spr:'ntfcodeimos', side:'ally', crossSecs:55},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'B1', c:'bo', n:1, spr:'boartemis', wait:true},\n"
    "       {id:'E2', c:'fi', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},\n"
    "       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'E2'}\n"
    "     ]},\n",
    "       // An NTF Deimos coming over to the GTVA, still in NTF markings.\n"
    "       // She crosses right to left, away from the NTF side, and her own\n"
    "       // side keeps coming until she is across. When she jumps, the\n"
    "       // fight is over: nothing still queued arrives.\n"
    "       // Half again her hull: with her own side coming the whole way,\n"
    "       // the standard one did not last the crossing.\n"
    "       {id:'A1', c:'co', n:1, spr:'ntfcodeimos', side:'ally', crossSecs:55,\n"
    "        crossDir:'left', hp:1.5},\n"
    "       {id:'E1', c:'fi', n:2},\n"
    "       {id:'B1', c:'bo', n:1, spr:'boartemis', wait:true},\n"
    "       {id:'E2', c:'fi', n:1, wait:true}\n"
    "     ], ev:[\n"
    "       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},\n"
    "       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},\n"
    "       // The first wing hunts her; what follows is a screen for the\n"
    "       // player to cut through. All of it diving on her was too much.\n"
    "       {t:'alleZerstoert', a:'E1', w:'jagd', a2:''},\n"
    "       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'E2'},\n"
    "       {t:'verlaesst', a:'A1', w:'ende', a2:''}\n"
    "     ]},\n",
    "M35: direction and reinforcements")

# ══ 40_world.js ═════════════════════════════════════════════════════════

# ── M36: the Iceni's station point comes from her width ─────────────────
wo = replace_once(
    wo,
    "      targetX:W-74-Math.random()*34,\n",
    "      // From her width, so the whole hull is on screen. A fixed distance\n"
    "      // from the edge left the stern of a ship this size outside.\n"
    "      targetX:W-(img ? img.width*sc*0.5 : 150)-12-Math.random()*34,\n",
    "iceni: station point")

# ── A crossing may run right to left; leaving is recorded ───────────────
wo = replace_once(
    wo,
    "    if(a.transit && subOK(a,'engines')){\n"
    "      a.x += a.transitV;\n"
    "      if(a.x >= a.transitEnd && !a.warpOut){\n"
    "        a.warpOut = a.warpMax; a.warpX = a.x; a.warpY = a.y;\n",
    "    if(a.transit && subOK(a,'engines')){\n"
    "      a.x += a.transitV;\n"
    "      // transitV is negative on a crossing to the left.\n"
    "      const _there = (a.transitV >= 0) ? (a.x >= a.transitEnd) : (a.x <= a.transitEnd);\n"
    "      if(_there && !a.warpOut){\n"
    "        a.warpOut = a.warpMax; a.warpX = a.x; a.warpY = a.y;\n"
    "        // She has left, as far as the mission's events are concerned.\n"
    "        if(a.uid) EV_LEFT[a.uid] = true;\n",
    "transit: direction and leave")

# ── Pickups are drawn to the ship ───────────────────────────────────────
wo = replace_once(
    wo,
    "const ITEM_R = 15;             // pickup radius on top of the ship's own size\n",
    "const ITEM_R = 15;             // pickup radius on top of the ship's own size\n"
    "// The magnet. Within MAGNET_R of the ship a pickup is caught and from then\n"
    "// on flies to it, gaining MAGNET_PULL per step up to MAGNET_MAX - faster\n"
    "// than any hull flies, so a caught pickup always arrives.\n"
    "const MAGNET_R    = 120;\n"
    "const MAGNET_PULL = 0.45;\n"
    "const MAGNET_MAX  = 7.5;\n",
    "magnet constants")

wo = replace_once(
    wo,
    "    if(it.vx==null) it.vx=ITEM_DRIFT;\n"
    "    it.x += it.vx; it.y += it.vy;\n",
    "    if(it.vx==null) it.vx=ITEM_DRIFT;\n"
    "    if(GS==='playing' && player.hp>0){\n"
    "      const mdx=player.x-it.x, mdy=player.y-it.y, md=Math.hypot(mdx,mdy);\n"
    "      if(md < MAGNET_R) it.caught = true;\n"
    "      if(it.caught && md > 0){\n"
    "        it.vx += mdx/md*MAGNET_PULL; it.vy += mdy/md*MAGNET_PULL;\n"
    "        const ms=Math.hypot(it.vx, it.vy);\n"
    "        if(ms > MAGNET_MAX){ it.vx=it.vx/ms*MAGNET_MAX; it.vy=it.vy/ms*MAGNET_MAX; }\n"
    "      }\n"
    "    }\n"
    "    it.x += it.vx; it.y += it.vy;\n",
    "magnet")

# ══ 60_effects.js ═══════════════════════════════════════════════════════
fx = replace_once(
    fx,
    "          _a.guard = true;\n"
    "          _a.x = -20;  _a.warpX = _a.x;  _a.warp = 0;\n"
    "          _a.transit = true;\n"
    "          const _gi = IMGS[_a.img];\n"
    "          const _gh = _gi ? _gi.width*_a.sc*0.5 : 120;\n"
    "          _a.transitEnd = W - _gh - TRANS_EDGE_PAD;\n"
    "          _a.transitV = (_a.transitEnd - _a.x) / (_sp.crossSecs*TICK_HZ);\n"
    "          _a.flip = needsFlip(_a.img, false);\n",
    "          _a.guard = true;\n"
    "          _a.transit = true;\n"
    "          const _gi = IMGS[_a.img];\n"
    "          const _gh = _gi ? _gi.width*_a.sc*0.5 : 120;\n"
    "          // crossDir 'left': in from the right edge, out on the left.\n"
    "          const _toLeft = (_sp.crossDir === 'left');\n"
    "          _a.x = _toLeft ? W + 20 : -20;  _a.warpX = _a.x;  _a.warp = 0;\n"
    "          _a.transitEnd = _toLeft ? _gh + TRANS_EDGE_PAD : W - _gh - TRANS_EDGE_PAD;\n"
    "          _a.transitV = (_a.transitEnd - _a.x) / (_sp.crossSecs*TICK_HZ);\n"
    "          _a.flip = needsFlip(_a.img, _toLeft);\n",
    "crossing: direction")

fx = replace_once(
    fx,
    "        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;\n"
    "                _a.defectLock = evWillDefect(_sp.uid);\n",
    "        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;\n"
    "                _a.defectLock = evWillDefect(_sp.uid);\n"
    "                if(_sp.defectRun) _a.defectRun = _sp.defectRun;\n",
    "ally capital: defectRun")

open("src/30_waves.js", "w", encoding="utf-8").write(wv)
open("src/40_world.js", "w", encoding="utf-8").write(wo)
open("src/60_effects.js", "w", encoding="utf-8").write(fx)

# ── Test file ──────────────────────────────────────────────────────────
# The field simulation with the new scenarios travels inside the patch,
# because .js files cannot be downloaded from the chat. Written last.
import base64
FIELDSIM = (
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
    'IHRoYXQgaXMgb3V0IG9mIGl0cyB2b3J0ZXgsCiAgICAvLyB0aGUgYm9tYnMgaW4gZmxpZ2h0IGFu'
    'ZCByb2NrcyBjbG9zaW5nIG9uIGFuIGVzY29ydCAtIHdoYXQgYSBwbGF5ZXIKICAgIC8vIGRlZmVu'
    'ZGluZyBvbmUgZG9lcy4KICAgIGtpbGxTbWFsbCgpeyBmb3IoY29uc3QgZSBvZiBlbmVtaWVzKSBp'
    'ZigoZS50eXBlPT09J2ZpZ2h0ZXInfHxlLnR5cGU9PT0nYm9tYmVyJykgJiYgIShlLndhcnA+MCkp'
    'IGUuaHAgPSAwOwogICAgICAgICAgICAgICAgIGZvcihsZXQgaT1lQnVsbGV0cy5sZW5ndGgtMTtp'
    'Pj0wO2ktLSkgaWYoZUJ1bGxldHNbaV0ua2luZD09PSdib21iJykgZUJ1bGxldHMuc3BsaWNlKGks'
    'MSk7CiAgICAgICAgICAgICAgICAgLy8gTG9vc2Ugcm9ja3MgYWJvdXQgdG8gaGl0IGFuIGVzY29y'
    'dCBhcyB3ZWxsLgogICAgICAgICAgICAgICAgIGZvcihjb25zdCBlIG9mIGVuZW1pZXMpIGlmKGUu'
    'dHlwZT09PSdhc3Rlcm9pZCcgJiYgIWUuc2NlbmVyeSAmJgogICAgICAgICAgICAgICAgICAgYWxs'
    'aWVzLnNvbWUoYT0+IWEuc21hbGwgJiYgTWF0aC5oeXBvdChhLngtZS54LCBhLnktZS55KSA8IDE4'
    'MCkpIGUuaHAgPSAwOyB9LAogICAga2lsbElkKGlkKXsgZm9yKGNvbnN0IGUgb2YgZW5lbWllcykg'
    'aWYoZS51aWQ9PT1pZCAmJiAhKGUud2FycD4wKSkgZS5ocCA9IDA7IH0sCiAgICAvLyBTdGVwIHVu'
    'dGlsIGNvbmQoKSBob2xkcywgY2xlYXJpbmcgc21hbGwgY3JhZnQgZXZlcnkgc28gb2Z0ZW4uCiAg'
    'ICB1bnRpbChjb25kLCBtYXgsIGNsZWFyLCBhbGwpeyBmb3IobGV0IHQ9MDt0PG1heDt0Kz0yMCl7'
    'IGlmKGNvbmQoKSkgcmV0dXJuIHQ7CiAgICAgICAgICAgICBpZihjbGVhciAmJiB0JTIwMD09PTAp'
    'IEZTLmtpbGxTbWFsbCgpOwogICAgICAgICAgICAgaWYoYWxsICYmIHQlMjAwPT09MCkgZm9yKGNv'
    'bnN0IGUgb2YgZW5lbWllcykgaWYoIShlLndhcnA+MCkgJiYgIWUuaW52dWxuICYmICFlLnNjZW5l'
    'cnkpIGUuaHAgPSAwOwogICAgICAgICAgICAgRlMuc3RlcCgyMCk7IH0gcmV0dXJuIC0xOyB9LAog'
    'ICAgaWRzKGlkKXsgcmV0dXJuIGJ5SWQoaWQpOyB9LAogICAgZW5lbXlJZHMoKXsgcmV0dXJuIGVu'
    'ZW1pZXMubWFwKGU9PmUudWlkfHxlLnR5cGUpOyB9LAogICAgYWxseUlkcygpeyByZXR1cm4gYWxs'
    'aWVzLm1hcChhPT5hLnVpZHx8YS50eXBlKTsgfQogIH07YDsKCmNvbnN0IHNjZW5hcmlvcyA9IFtd'
    'OwpmdW5jdGlvbiBzY2VuYXJpbyhuYW1lLCBxdWVyeSwgYm9keSl7IHNjZW5hcmlvcy5wdXNoKHtu'
    'YW1lLCBxdWVyeSwgYm9keX0pOyB9CgovLyDilIDilIAgU2NlbmFyaW9zIOKUgOKUgOKUgOKUgOKU'
    'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
    'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
    'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgApzY2VuYXJpbygn'
    'TTMxIERlciBBdWZzdGFuZCcsICdtPTMxJywgYAogIGNvbnN0IHIgPSB7fTsKICByLndhdmUgPSB3'
    'YXZlOyByLnNoaXAgPSBwbGF5ZXIuc2hpcDsKICByLnRlcnJhbkNhbGwgPSBBTExZX0ZBQ19PTi50'
    'ZXJyYW49PT10cnVlICYmIEFMTFlfRkFDX09OLnZhc3VkYW49PT1mYWxzZTsKICBGUy5zdGVwKDQw'
    'MCk7CiAgY29uc3QgYSA9IGFsbGllcy5maW5kKHg9PngudWlkPT09J0ExJyk7CiAgci5hbGx5QXRT'
    'dGFydCA9ICEhYSAmJiBhLmltZz09PSdjcmxldmlhdGhhbic7CiAgci5sb2NrU2V0ID0gISFhICYm'
    'IGEuZGVmZWN0TG9jaz09PXRydWU7CiAgLy8gSGFtbWVyIGhlciB3aGlsZSBzaGUgaXMgc3RpbGwg'
    'b3Vyczogc2hlIG11c3Qgbm90IGRpZSBiZWZvcmUgdGhlIHR1cm4uCiAgaWYoYSl7IGEuaHAgPSAx'
    'OyBGUy5zdGVwKDUpOyB9CiAgci5zdXJ2aXZlc0xvY2sgPSAhIWFsbGllcy5maW5kKHg9PngudWlk'
    'PT09J0ExJyk7CiAgRlMudW50aWwoKCk9PiFlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nRTEnKSAm'
    'JiAhc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nRTEnKSwgNjAwMCwgdHJ1ZSk7CiAgRlMuc3RlcCg0'
    'MCk7CiAgY29uc3QgZSA9IGVuZW1pZXMuZmluZCh4PT54LnVpZD09PSdBMScpOwogIHIudHVybmVk'
    'ID0gISFlICYmICFhbGxpZXMuc29tZSh4PT54LnVpZD09PSdBMScpOwogIHIubnRmSHVsbCA9ICEh'
    'ZSAmJiBlLmltZz09PSdudGZjcmxldmlhdGhhbic7CiAgci5lbmVteVNoYXBlID0gISFlICYmIGUu'
    'dHlwZT09PSdjcnVpc2VyJyAmJiBlLnNpZGU9PT0nZW5lbXknICYmICFlLmRlYWQgJiYgZS5ocD4w'
    'OwogIHIuaGFzU3VicyA9ICEhZSAmJiAhIWUuc3VicyAmJiBlLnN1YnMubGVuZ3RoPT09NTsKICBy'
    'Lmhhc0d1bnMgPSAhIWUgJiYgISEoZS5ndW5zfHxlLm1vdW50c3x8ZS53cG58fGUuYmVhbXMpOwog'
    'IHIuZmFjZXNXaGVyZVNoZUdvZXMgPSAhIWUgJiYgZS5mbGlwPT09bmVlZHNGbGlwKGUuaW1nLCBm'
    'YWxzZSk7CiAgY29uc3QgeDAgPSBlID8gZS54IDogMDsKICBGUy5zdGVwKDIwMCk7CiAgci53YXZl'
    'T3BlbldoaWxlU2hlTGl2ZXMgPSAhd2F2ZU92ZXI7CiAgci5oZWFkc1JpZ2h0ID0gISFlICYmIGUu'
    'eCA+IHgwOwogIC8vIExlZnQgYWxvbmUgc2hlIHJlYWNoZXMgdGhlIGVkZ2UgYW5kIGp1bXBzLgog'
    'IGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+ISFFVl9MRUZUWydBMSddLCA4MDAwLCB0cnVlKTsKICBy'
    'Lmp1bXBzQXRUaGVFZGdlID0gdD49MCAmJiBlLndhcnBPdXQ+MCAmJiBlLnggPCBXOwogIHIud2hp'
    'bGVGdWxseU9uU2NyZWVuID0gISFlICYmIGUueCArIElNR1NbZS5pbWddLndpZHRoKmUuc2MqMC41'
    'IDw9IFc7CiAgRlMudW50aWwoKCk9PiFlbmVtaWVzLmluY2x1ZGVzKGUpLCAxMDAwLCBmYWxzZSk7'
    'CiAgci5nb25lQWZ0ZXJKdW1wID0gIWVuZW1pZXMuaW5jbHVkZXMoZSk7CiAgRlMudW50aWwoKCk9'
    'PndhdmVPdmVyLCA0MDAwLCB0cnVlKTsKICByLndhdmVFbmRzID0gd2F2ZU92ZXI7CiAgcmV0dXJu'
    'IHI7YCk7CgpzY2VuYXJpbygnTTMxIGVuZ2luZXMgc3RvcCBoZXInLCAnbT0zMScsIGAKICBGUy5z'
    'dGVwKDMwMCk7CiAgRlMudW50aWwoKCk9PiFlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nRTEnKSAm'
    'JiAhc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nRTEnKSwgNjAwMCwgdHJ1ZSk7CiAgRlMuc3RlcCg0'
    'MCk7CiAgY29uc3QgZSA9IGVuZW1pZXMuZmluZCh4PT54LnVpZD09PSdBMScpOwogIGZvcihjb25z'
    'dCBzIG9mIGUuc3VicykgaWYocy5pZD09PSdlbmdpbmVzJyl7IHMuZGVhZCA9IHRydWU7IHMuaHAg'
    'PSAwOyB9CiAgY29uc3QgeDAgPSBlLng7IEZTLnN0ZXAoNjAwKTsKICByZXR1cm4ge3N0b3BwZWQ6'
    'IE1hdGguYWJzKGUueC14MCkgPCAwLjAxICYmICFFVl9MRUZUWydBMSddfTtgKTsKCnNjZW5hcmlv'
    'KCdNMzIgRGllIEZyYWNodHJvdXRlJywgJ209MzInLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0'
    'ZXAoMzAwKTsKICBjb25zdCBmID0gYWxsaWVzLmZpbHRlcih4PT54LnVpZD09PSdGMScpOwogIHIu'
    'dHdvRnJlaWdodGVycyA9IGYubGVuZ3RoPT09MiAmJiBmLmV2ZXJ5KHg9PnguaW1nPT09J2ZycG9z'
    'ZWlkb24nKTsKICByLnRlcnJhblNpZGUgPSBmLmV2ZXJ5KHg9PnguZmFjdGlvbj09PSd0ZXJyYW4n'
    'KTsKICByLm1lZHVzYXMgPSBlbmVtaWVzLmZpbHRlcihlPT5lLnVpZD09PSdCMScpLmV2ZXJ5KGU9'
    'PmUuaW1nPT09J2JvbWVkdXNhJykgJiYgZW5lbWllcy5zb21lKGU9PmUudWlkPT09J0IxJyk7CiAg'
    'ci5maWdodGVyQ292ZXIgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nRTEnICYmIGUudHlwZT09'
    'PSdmaWdodGVyJykgfHwgc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nRTEnKTsKICBjb25zdCB4MCA9'
    'IGYubGVuZ3RoID8gZlswXS54IDogMDsgRlMuc3RlcCgzMDApOwogIHIuY3Jvc3NpbmcgPSBmLmxl'
    'bmd0aD4wICYmIGZbMF0ueCA+IHgwOwogIEZTLnVudGlsKCgpPT4hZW5lbWllcy5zb21lKGU9PmUu'
    'dWlkPT09J0IxJyksIDQwMDAsIHRydWUpOwogIEZTLnN0ZXAoMzAwKTsKICByLnNlY29uZFJhaWQg'
    'PSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nQjInKSB8fCBzcGF3blEuc29tZShxPT5xLnVpZD09'
    'PSdCMicpOwogIHIuZW5kc1doZW5UaHJvdWdoID0gRlMudW50aWwoKCk9PndhdmVPdmVyLCAyMDAw'
    'MCwgdHJ1ZSkgPj0gMDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNMzMgRGllIFJlbGFpc3N0'
    'YXRpb24nLCAnbT0zMycsIGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0'
    'IHMgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nUzEnKTsKICByLmZhdXN0dXMgPSAhIXMgJiYg'
    'cy5pbWc9PT0nc2NmYXVzdHVzJzsKICByLmF0R2l2ZW5IZWlnaHQgPSAhIXMgJiYgTWF0aC5hYnMo'
    'cy55LTI1MCkgPCAxOwogIGNvbnN0IHgwID0gcyA/IHMueCA6IDA7CiAgRlMuc3RlcCgxMjAwKTsK'
    'ICByLnN0YXlzUHV0ID0gISFzICYmIE1hdGguYWJzKHMueC14MCkgPCAxICYmIE1hdGguYWJzKHMu'
    'eS0yNTApIDwgMTsKICByLm5vRmxhayA9ICEhcyAmJiBmbGFrSGFzKHMpPT09ZmFsc2U7CiAgci5n'
    'dW5zID0gZW5lbWllcy5maWx0ZXIoZT0+ZS51aWQ9PT0nRzEnKS5sZW5ndGg9PT00OwogIC8vIFJl'
    'aW5mb3JjZW1lbnRzIGtlZXAgY29taW5nIHdoaWxlIHNoZSBzdGFuZHMuCiAgRlMua2lsbFNtYWxs'
    'KCk7IEZTLnN0ZXAoOTAwKTsKICByLnJlaW5mb3JjZWQgPSBlbmVtaWVzLnNvbWUoZT0+ZS50eXBl'
    'PT09J2ZpZ2h0ZXInICYmICFlLnVpZCkgfHwgc3Bhd25RLnNvbWUocT0+IXEudWlkICYmIC9eZmlf'
    'Ly50ZXN0KHEudHlwZSkpOwogIGNvbnN0IGJlZm9yZSA9IFNIT0NLUy5sZW5ndGg7CiAgRlMua2ls'
    'bElkKCdTMScpOyBGUy5zdGVwKDMpOwogIHIuYmlnQmxhc3QgPSBTSE9DS1Muc29tZShrPT5rLnJN'
    'YXg9PT0zMDApOwogIEZTLmtpbGxTbWFsbCgpOyBGUy5zdGVwKDEyMDApOyBGUy5raWxsU21hbGwo'
    'KTsgRlMuc3RlcCg2MDApOwogIHIucmVpbmZPZmYgPSBldlJlaW5mPT09ZmFsc2U7CiAgcmV0dXJu'
    'IHI7YCk7CgpzY2VuYXJpbygnTTM0IERpZSBGbGFrd2FuZCcsICdtPTM0JywgYAogIGNvbnN0IHIg'
    'PSB7fTsKICBzY29yZSA9IDIwMDAwOyAgIC8vIGVub3VnaCBmb3IgdGhlIEFydGVtaXMgdG8gYmUg'
    'b3BlbiBpbiB0aGlzIGN5Y2xlCiAgRlMuc3RlcCg0MDApOwogIGNvbnN0IGsgPSBlbmVtaWVzLmZp'
    'bHRlcihlPT5lLnVpZD09PSdLMScpOwogIHIudHdvQWVvbHVzID0gay5sZW5ndGg9PT0yICYmIGsu'
    'ZXZlcnkoZT0+ZS5pbWc9PT0nbnRmY3JhZW9sdXMnKTsKICByLmZsYWsgPSBrLmV2ZXJ5KGU9PmZs'
    'YWtIYXMoZSkpOwogIHIubm9IYW5nYXJZZXQgPSAhYWxsaWVzLnNvbWUoYT0+YS51aWQ9PT0nQTEn'
    'KTsKICBGUy51bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdFMScpICYmICFzcGF3'
    'blEuc29tZShxPT5xLnVpZD09PSdFMScpLCA1MDAwLCB0cnVlKTsKICBGUy5zdGVwKDQwMCk7CiAg'
    'Y29uc3QgbyA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J0ExJyk7CiAgci5vcmlvbiA9ICEhbyAm'
    'JiBvLmltZz09PSdkZW9yaW9ucmlnaHQnOwogIHRpY2tTaGlwVW5sb2NrcygpOwogIHIuYm9tYmVy'
    'T2ZmZXJlZCA9IHNoaXBPZmZlcmVkKCdib2FydGVtaXMnKSAmJiBzaGlwU3dhcFJlYWR5KCk7CiAg'
    'cmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTM1IERlciBVZWJlcmxhZXVmZXInLCAnbT0zNScsIGAK'
    'ICBjb25zdCByID0ge307CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IGQgPSBhbGxpZXMuZmluZChh'
    'PT5hLnVpZD09PSdBMScpOwogIHIubnRmRGVpbW9zID0gISFkICYmIGQuaW1nPT09J250ZmNvZGVp'
    'bW9zJyAmJiBkLnR5cGU9PT0nY29ydmV0dGUnOwogIHIuY29tZXNGcm9tVGhlUmlnaHQgPSAhIWQg'
    'JiYgZC54ID4gVyowLjY7CiAgci5mYWNlc0xlZnQgPSAhIWQgJiYgZC5mbGlwPT09bmVlZHNGbGlw'
    'KCdudGZjb2RlaW1vcycsIHRydWUpOwogIHIuY3Jvc3NpbmcgPSAhIWQgJiYgZC50cmFuc2l0PT09'
    'dHJ1ZTsKICByLmZpcnN0V2luZ0h1bnRzSGVyID0gd2F2ZUh1bnQ9PT0nQTEnOwogIGNvbnN0IHgw'
    'ID0gZCA/IGQueCA6IDA7IEZTLnN0ZXAoMjAwKTsKICByLmhlYWRzTGVmdCA9ICEhZCAmJiBkLngg'
    'PCB4MDsKICBGUy51bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdFMScpICYmICFz'
    'cGF3blEuc29tZShxPT5xLnVpZD09PSdFMScpLCA1MDAwLCB0cnVlKTsKICBGUy5zdGVwKDIwKTsK'
    'ICByLnJlaW5mb3JjZW1lbnRzT24gPSBldlJlaW5mPT09dHJ1ZTsKICByLmZvbGxvd1Vwc1NjcmVl'
    'biA9IHdhdmVIdW50PT09Jyc7CiAgci5yZWFybSA9IGNvcnZldHRlT25GaWVsZCgpOwogIHIubm90'
    'T25DYWxsTWVudSA9IEFMTFlfT1JERVIuaW5kZXhPZignbnRmX2RlaW1vcycpPDA7CiAgY29uc3Qg'
    'Z290ID0gRlMudW50aWwoKCk9PiFhbGxpZXMuc29tZShhPT5hLnVpZD09PSdBMScpLCA5MDAwLCB0'
    'cnVlKTsKICByLmdldHNBY3Jvc3MgPSBnb3Q+PTAgJiYgIWd1YXJkTG9zdDsKICByLmxlZnRDb3Vu'
    'dHMgPSAhIUVWX0xFRlRbJ0ExJ107CiAgci5ub3RoaW5nTW9yZUNvbWVzID0gZXZSZWluZj09PWZh'
    'bHNlICYmIHNwYXduUS5sZW5ndGg9PT0wOwogIEZTLnVudGlsKCgpPT53YXZlT3ZlciwgNDAwMCwg'
    'dHJ1ZSk7CiAgci53YXZlRW5kcyA9IHdhdmVPdmVyOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8o'
    'J00zNiBEaWUgSWNlbmknLCAnbT0zNicsIGAKICBjb25zdCByID0ge307CiAgY29uc3QgczAgPSBz'
    'Y29yZSA9IDUwMDA7CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IGkgPSBlbmVtaWVzLmZpbmQoZT0+'
    'ZS51aWQ9PT0nVjEnKTsKICByLmljZW5pID0gISFpICYmIGkuaWNlbmk9PT10cnVlICYmIGkuaW1n'
    'PT09J2NvaWNlbmknOwogIHIubm9OYXZpZ2F0aW9uID0gISFpICYmICEhaS5zdWJzICYmIGkuc3Vi'
    'cy5sZW5ndGg9PT00ICYmIHN1Yk9LKGksJ25hdmlnYXRpb24nKTsKICByLmRlYWRsaW5lID0gISFp'
    'ICYmIGkuZmxlZVQ+MCAmJiBpLmZsZWVUIDw9IDI1KlRJQ0tfSFo7CiAgRlMuc3RlcCg2MDApOwog'
    'IHIud2hvbGVIdWxsT25TY3JlZW4gPSAhIWkgJiYgaS54ICsgSU1HU1tpLmltZ10ud2lkdGgqaS5z'
    'YyowLjUgPD0gVzsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9PiFlbmVtaWVzLnNvbWUoZT0+ZS51'
    'aWQ9PT0nVjEnKSwgNjAwMCwgZmFsc2UpOwogIHIuanVtcHNPdXQgPSB0Pj0wICYmIGljZW5Fc2Nh'
    'cGVzPT09MTsKICByLm5vUGVuYWx0eSA9IHNjb3JlID49IHMwOwogIHIuZmVucmlzID0gZW5lbWll'
    'cy5zb21lKGU9PmUudWlkPT09J0sxJyAmJiBlLmltZz09PSdudGZjcmZlbnJpcycpOwogIHJldHVy'
    'biByO2ApOwoKc2NlbmFyaW8oJ0N5Y2xlIGNoYW5nZSAzMCAtPiAzMScsICdtPTMwJywgYAogIGNv'
    'bnN0IHIgPSB7fTsKICByLnN0YXJ0c1Zhc3VkYW4gPSBwbGF5ZXIuc2hpcD09PSdmaXRvdGgnICYm'
    'IEFMTFlfRkFDX09OLnZhc3VkYW49PT10cnVlOwogIHNjb3JlID0gOTAwMDA7CiAgLy8gQ2xlYXIg'
    'd2F2ZSAzMCBieSBmb3JjZSBhbmQgbGV0IHRoZSBqdW1wIGhhcHBlbi4KICBmb3IobGV0IGs9MDtr'
    'PDYwICYmIHdhdmU9PT0zMDtrKyspeyBmb3IoY29uc3QgZSBvZiBlbmVtaWVzKSBpZighKGUud2Fy'
    'cD4wKSAmJiAhZS5pbnZ1bG4pIGUuaHA9MDsgRlMuc3RlcCgyMDApOyB9CiAgci53YXZlID0gd2F2'
    'ZTsKICByLm15cm1pZG9uID0gcGxheWVyLnNoaXA9PT0nZmlteXJtaWRvbic7CiAgci5vbmVIdWxs'
    'ID0gc2hpcFVubG9ja2VkPT09MSAmJiBjeWNsZUJhc2U9PT1zY29yZSAtIChzY29yZS1jeWNsZUJh'
    'c2UpOwogIHIuYmFzZVNldCA9IGN5Y2xlQmFzZSA+PSA5MDAwMDsKICByLnRlcnJhbiA9IEFMTFlf'
    'RkFDX09OLnRlcnJhbj09PXRydWUgJiYgQUxMWV9GQUNfT04udmFzdWRhbj09PWZhbHNlOwogIHJl'
    'dHVybiByO2ApOwoKc2NlbmFyaW8oJ00xMyBib3RoIHRyYW5zcG9ydHMgb24gdGltZScsICdtPTEz'
    'JywgYAogIEZTLnN0ZXAoMzAwKTsKICByZXR1cm4ge2JvdGhUcmFuc3BvcnRzOiBhbGxpZXMuZmls'
    'dGVyKGE9PmEudWlkPT09J1QxJykubGVuZ3RoPT09Mn07YCk7CgovLyBFdmVyeSB3cml0dGVuIG1p'
    'c3Npb24gaGFzIHRvIGNvbWUgdG8gYW4gZW5kIHdoZW4gaXRzIGVuZW1pZXMgZ28gZG93biwKLy8g'
    'd2l0aCBub3RoaW5nIHRocm93biBvbiB0aGUgd2F5LiBFbmVteSBzaGlwcyBhcmUgY2xlYXJlZCBl'
    'dmVyeSB0d28gc2Vjb25kcwovLyBvbmNlIHRoZXkgYXJlIG91dCBvZiB0aGVpciB2b3J0ZXggLSBh'
    'IHBsYXllciB3aG8gaGl0cyBldmVyeXRoaW5nLgovLyBTY2FuIG1pc3Npb25zICgxMiwgMjMpIG5l'
    'ZWQgdGhlIHBsYXllciB0byBmbHkgdGhlIHNjYW4gYW5kIGFyZSBsZWZ0IG91dC4KZm9yKGxldCBt'
    'PTE7bTw9MzY7bSsrKSBpZihtIT09MTIgJiYgbSE9PTIzKSBzY2VuYXJpbygnTScgKyBTdHJpbmco'
    'bSkucGFkU3RhcnQoMiwnMCcpICsgJyBwbGF5cyB0byB0aGUgZW5kJywgJ209JyArIG0sIGAKICBj'
    'b25zdCB0ID0gRlMudW50aWwoKCk9PndhdmVPdmVyLCA0MDAwMCwgZmFsc2UsIHRydWUpOwogIElU'
    'RU1TLmxlbmd0aCA9IDA7ICAgICAvLyBwaWNrdXBzIGhvbGQgdGhlIGp1bXAgb3BlbiB1bnRpbCB0'
    'aGV5IGV4cGlyZQogIGNvbnN0IGogPSBGUy51bnRpbCgoKT0+d2F2ZSA9PT0gJHttfSsxLCA2MDAw'
    'LCBmYWxzZSwgZmFsc2UpOwogIHJldHVybiB7ZW5kczogdCA+PSAwLCBuZXh0V2F2ZTogaiA+PSAw'
    'fTtgKTsKCnNjZW5hcmlvKCdQaWNrdXBzIGFyZSBkcmF3biB0byB0aGUgc2hpcCcsICdtPTEnLCBg'
    'CiAgRlMuc3RlcCgyMDApOwogIGNvbnN0IHIgPSB7fTsKICB0aWNrZXRzLmNydWlzZXIgPSAwOwog'
    'IElURU1TLnB1c2goe3g6cGxheWVyLngrMTAwLCB5OnBsYXllci55LCB2eDpJVEVNX0RSSUZULCB2'
    'eTowLCBraW5kOidjcnVpc2VyJywgbGlmZTo1MDAwfSk7CiAgSVRFTVMucHVzaCh7eDpwbGF5ZXIu'
    'eCs0MDAsIHk6cGxheWVyLnkrMTAwLCB2eDowLCB2eTowLCBraW5kOidyZXBhaXInLCBsaWZlOjUw'
    'MDB9KTsKICBjb25zdCBmYXIgPSBJVEVNU1sxXTsKICBGUy5zdGVwKDYwKTsKICByLm5lYXJPbmVD'
    'b2xsZWN0ZWQgPSB0aWNrZXRzLmNydWlzZXI9PT0xOwogIHIuZmFyT25lTGVmdEFsb25lID0gSVRF'
    'TVMuaW5jbHVkZXMoZmFyKSAmJiAhZmFyLmNhdWdodDsKICAvLyBDYXVnaHQsIGl0IGtlZXBzIGZv'
    'bGxvd2luZyBldmVuIGlmIHRoZSBzaGlwIHB1bGxzIGF3YXkuCiAgcGxheWVyLnggPSAxMDA7IHBs'
    'YXllci55ID0gMjUwOwogIElURU1TLnB1c2goe3g6MjEwLCB5OjI1MCwgdng6MCwgdnk6MCwga2lu'
    'ZDonY29ydmV0dGUnLCBsaWZlOjUwMDB9KTsKICBjb25zdCBjID0gSVRFTVNbSVRFTVMubGVuZ3Ro'
    'LTFdOwogIEZTLnN0ZXAoMSk7CiAgci5jYXVnaHQgPSBjLmNhdWdodD09PXRydWU7CiAgbGV0IGdv'
    'dCA9IGZhbHNlOwogIGZvcihsZXQgaz0wO2s8MjAwICYmICFnb3Q7aysrKXsgcGxheWVyLnggPSA2'
    'MDsgcGxheWVyLnkgPSAyNTA7IEZTLnN0ZXAoMSk7IGdvdCA9ICFJVEVNUy5pbmNsdWRlcyhjKTsg'
    'fQogIHIuZm9sbG93c0FuZEFycml2ZXMgPSBnb3Q7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygn'
    'SG9MIHN0YXJ0IHVuY2hhbmdlZCcsICdtPTEnLCBgCiAgcmV0dXJuIHt3YXZlOiB3YXZlLCB0aG90'
    'aDogcGxheWVyLnNoaXA9PT0nZml0b3RoJywgdmFzdWRhbkNhbGw6IEFMTFlfRkFDX09OLnZhc3Vk'
    'YW49PT10cnVlICYmIEFMTFlfRkFDX09OLnRlcnJhbj09PWZhbHNlfTtgKTsKCi8vIOKUgOKUgCBS'
    'dW5uZXIg4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
    '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
    '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
    '4pSA4pSA4pSA4pSA4pSA4pSACihhc3luYygpPT57CiAgY29uc3QgYnJvd3NlciA9IGF3YWl0IGNo'
    'cm9taXVtLmxhdW5jaCgpOwogIGxldCBmYWlscyA9IDA7CiAgY29uc3Qgb25seSA9IHByb2Nlc3Mu'
    'YXJndls0XTsKICBmb3IoY29uc3Qgc2Mgb2Ygc2NlbmFyaW9zKXsKICAgIGlmKG9ubHkgJiYgc2Mu'
    'bmFtZS5pbmRleE9mKG9ubHkpPDApIGNvbnRpbnVlOwogICAgY29uc3QgcGFnZSA9IGF3YWl0IGJy'
    'b3dzZXIubmV3UGFnZSgpOwogICAgY29uc3QgZXJycyA9IFtdOwogICAgcGFnZS5vbigncGFnZWVy'
    'cm9yJywgZT0+ZXJycy5wdXNoKFN0cmluZyhlLm1lc3NhZ2V8fGUpKSk7CiAgICBhd2FpdCBwYWdl'
    'LmdvdG8oJ2ZpbGU6Ly8nICsgdG1wICsgJz8nICsgc2MucXVlcnkpOwogICAgYXdhaXQgcGFnZS53'
    'YWl0Rm9yVGltZW91dCgzMDApOwogICAgbGV0IHJlczsKICAgIHRyeXsKICAgICAgcmVzID0gYXdh'
    'aXQgcGFnZS5ldmFsdWF0ZShIRUxQRVJTICsgYFxuRlMuZmFrZUltYWdlcygpOyBsYXVuY2hHYW1l'
    'KCk7XG4oZnVuY3Rpb24oKXske3NjLmJvZHl9fSkoKWApOwogICAgfWNhdGNoKGUpeyByZXMgPSBu'
    'dWxsOyBlcnJzLnB1c2goU3RyaW5nKGUubWVzc2FnZXx8ZSkpOyB9CiAgICBjb25zb2xlLmxvZyhz'
    'Yy5uYW1lICsgJyAgKD8nICsgc2MucXVlcnkgKyAnKScpOwogICAgaWYocmVzKSBmb3IoY29uc3Qg'
    'W2ssdl0gb2YgT2JqZWN0LmVudHJpZXMocmVzKSl7CiAgICAgIGNvbnN0IGdvb2QgPSAodHlwZW9m'
    'IHY9PT0nYm9vbGVhbicpID8gdiA6IHRydWU7CiAgICAgIGlmKCFnb29kKSBmYWlscysrOwogICAg'
    'ICBjb25zb2xlLmxvZygoZ29vZCA/ICcgIG9rICAgICcgOiAnICBGQUlMICAnKSArIGsgKyAodHlw'
    'ZW9mIHY9PT0nYm9vbGVhbicgPyAnJyA6ICcgPSAnICsgSlNPTi5zdHJpbmdpZnkodikpKTsKICAg'
    'IH0KICAgIGlmKGVycnMubGVuZ3RoKXsgZmFpbHMrKzsgY29uc29sZS5sb2coJyAgRkFJTCAgcGFn'
    'ZSBlcnJvcnM6XG4gICAgJyArIGVycnMuc2xpY2UoMCw0KS5qb2luKCdcbiAgICAnKSk7IH0KICAg'
    'IGF3YWl0IHBhZ2UuY2xvc2UoKTsKICB9CiAgYXdhaXQgYnJvd3Nlci5jbG9zZSgpOwogIGZzLnVu'
    'bGlua1N5bmModG1wKTsKICBjb25zb2xlLmxvZygnXG4nICsgKGZhaWxzID8gZmFpbHMgKyAnIEZB'
    'SUxFRCcgOiAnYWxsIHBhc3NlZCcpKTsKICBwcm9jZXNzLmV4aXQoZmFpbHMgPyAxIDogMCk7Cn0p'
    'KCk7Cg=='
)
open('fieldsim.js', 'wb').write(base64.b64decode(FIELDSIM))
print("v130 applied: M31, M35, M36 fixed, pickups magnetic, fieldsim.js updated. Now run: python3 assemble.py 130")
