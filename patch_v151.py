#!/usr/bin/env python3
"""FS3 v151 - FreeSpace warp: the vortex stays open until the ship is out.

    The vortex of a ship coming in closed on a fixed clock, at three
    quarters of the jump. A big hull that warps in at the right edge had
    not cleared it by then - the Deimos had about a quarter, the Orion
    a fifth of her length still in it - and the vortex closed on her.
    Now the vortex stays open until the stern has passed it, also after
    the jump itself is over while the ship flies on, and only then
    closes. A ship that never clears it (half off the screen) closes it
    after three seconds at the latest.

Needs v150. Edits src/20_render.js and src/70_ui.js in place. Run
assemble.py afterwards.
"""
import sys


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def load(p):
    return open(p, encoding="utf-8").read()


rd = load("src/20_render.js")
ui = load("src/70_ui.js")

rd = replace_once(
    rd,
    "// Clip to the side of the vortex the ship is on: in front of it when\n",
    "// The vortex of a ship coming in lives on its own: it opens with the\n"
    "// jump, stays open until the stern has passed it (also after the jump\n"
    "// is over and the ship flies on) and only then closes.\n"
    "let FS_PORTALS = [];\n"
    "const FS_PORTAL_LINGER = 3;    // seconds after the jump before it closes anyway\n"
    "function fsPortalOpen(e, g, WS){\n"
    "  if(e._fsp) return;\n"
    "  e._fsp = {e, px:g.px, py:g.py, fx:g.fx, fy:g.fy, WS, mW:e.warpMax||100,\n"
    "            t0:fc - ((e.warpMax||100) - e.warp), closeT:-1};\n"
    "  FS_PORTALS.push(e._fsp);\n"
    "}\n"
    "function fsPortalCleared(p){\n"
    "  const e = p.e;\n"
    "  if(e.dead || (enemies.indexOf(e)<0 && allies.indexOf(e)<0)) return true;\n"
    "  const img = IMGS[e.img]; if(!img) return true;\n"
    "  const g = (e.warp>0) ? fsWarp(e) : null;\n"
    "  const cx = e.x + (g ? g.dx : 0), cy = e.y + (g ? g.dy : 0), L = img.width*e.sc;\n"
    "  // Distance of the stern past the vortex, along the flight path.\n"
    "  return ((cx - p.fx*L/2) - p.px)*p.fx + ((cy - p.fy*L/2) - p.py)*p.fy > 0;\n"
    "}\n"
    "function drawFsPortals(){\n"
    "  for(let i=FS_PORTALS.length-1; i>=0; i--){\n"
    "    const p = FS_PORTALS[i], age = fc - p.t0;\n"
    "    if(p.closeT < 0 && age >= p.mW*0.75 &&\n"
    "       (fsPortalCleared(p) || age > p.mW + FS_PORTAL_LINGER*TICK_HZ)) p.closeT = fc;\n"
    "    let wS = Math.min(1, 0.05 + 0.95*age/(p.mW*0.30));\n"
    "    if(p.closeT >= 0) wS = Math.min(wS, 1 - (fc - p.closeT)/(p.mW*0.25));\n"
    "    if(wS <= 0){ FS_PORTALS.splice(i,1); if(p.e._fsp===p) p.e._fsp = null; continue; }\n"
    "    ctx.save();\n"
    "    ctx.globalAlpha = Math.min(1, wS*1.4);\n"
    "    ctx.translate(p.px|0, p.py|0);\n"
    "    if(WARP_STYLE==='oval'){ ctx.rotate(Math.atan2(p.fy, p.fx)); ctx.scale(WARP_OVAL*wS, wS); }\n"
    "    else ctx.scale(wS, wS);\n"
    "    drawWarpFrame(warpSeed(p.e), p.WS, false);\n"
    "    ctx.restore(); ctx.globalAlpha = 1;\n"
    "  }\n"
    "}\n"
    "// Clip to the side of the vortex the ship is on: in front of it when\n",
    "portals")

ui = replace_once(
    ui,
    "            if(fImg) WSf = Math.max(100, fImg.height*e.sc*1.9, fImg.width*e.sc*0.62);\n",
    "            if(fImg) WSf = Math.max(100, fImg.height*e.sc*1.9, fImg.width*e.sc*0.62);\n"
    "            // Coming in: the vortex is drawn by drawFsPortals() below.\n"
    "            if(!fg.out){ fsPortalOpen(e, fg, WSf); continue; }\n",
    "open portal")
ui = replace_once(
    ui,
    "        }catch(ew){ctx.restore();ctx.globalAlpha=1;}\n"
    "      }\n"
    "    }\n"
    "  }\n",
    "        }catch(ew){ctx.restore();ctx.globalAlpha=1;}\n"
    "      }\n"
    "    }\n"
    "    try{ drawFsPortals(); }catch(ep){ ctx.restore(); ctx.globalAlpha=1; }\n"
    "  }\n",
    "draw portals")

open("src/20_render.js", "w", encoding="utf-8").write(rd)
open("src/70_ui.js", "w", encoding="utf-8").write(ui)
