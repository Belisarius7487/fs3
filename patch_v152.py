#!/usr/bin/env python3
"""FS3 v152 - FreeSpace warp: no stop and go at either end of the jump.

    Coming in, the ship shot out of the vortex and braked to a standstill
    at four fifths of the jump, stood there until the jump was over and
    then set off again to its battle position. Going out, it stopped dead
    when the jump began, stood for a fifth of it and only then sped up
    into the vortex.

    Now the ship comes out fast and brakes all through the jump down to
    the speed it flies at afterwards, so it carries straight on. Going
    out it keeps the speed it had and speeds up from there into the
    vortex.

Needs v151. Edits src/20_render.js and src/70_ui.js in place. Run
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
    "  let u, vis = true;\n"
    "  if(!out){\n"
    "    const k = (t-0.25)/0.55; if(k<=0) vis = false;\n"
    "    const kk = Math.min(1, Math.max(0, k));\n"
    "    u = -(G+L/2)*Math.pow(1-kk, 3);         // fast out, then braking\n"
    "  } else {\n"
    "    const k = Math.min(1, Math.max(0, (t-0.20)/0.55)); if(k>=1) vis = false;\n"
    "    u = (G+L/2)*k*k*k;                      // speeding up into it\n"
    "  }\n",
    "  // u: how far the picture is from the ship's place, along the nose.\n"
    "  // D is the whole way through the vortex, Dk the ticks it takes.\n"
    "  let u, vis = true;\n"
    "  const D = G + L/2;\n"
    "  if(!out){\n"
    "    // Out fast, braking all through the jump (25-100 %) down to the\n"
    "    // speed the ship flies at afterwards, less what the game already\n"
    "    // moves it during the jump - so it carries on without a stop.\n"
    "    const Dk = mW*0.75, el = mW - e.warp;\n"
    "    if(e._fsE0 == null){ e._fsE0 = el; e._fsX0 = e.x; e._fsY0 = e.y; }\n"
    "    const dt = el - e._fsE0;\n"
    "    const drift = dt > 0 ? ((e.x-e._fsX0)*fx + (e.y-e._fsY0)*fy)/dt : 0;\n"
    "    const c = Math.min(0.9*D, Math.max(0, fsExitSpeed(e) - drift)*Dk);\n"
    "    const k = (t-0.25)/0.75; if(k<=0) vis = false;\n"
    "    const w = 1 - Math.min(1, Math.max(0, k));\n"
    "    u = -D*w*w*w - c*(w - w*w*w);\n"
    "  } else {\n"
    "    // Keeps the speed it had and speeds up from there (0-75 %).\n"
    "    const Dk = mW*0.75;\n"
    "    if(e._fsV == null) e._fsV = Math.max(0, (e._fvx||0)*fx + (e._fvy||0)*fy);\n"
    "    const c = Math.min(0.9*D, e._fsV*Dk);\n"
    "    const k = Math.min(1, Math.max(0, t/0.75)); if(k>=1) vis = false;\n"
    "    u = c*k + (D-c)*k*k*k;\n"
    "  }\n",
    "profiles")

rd = replace_once(
    rd,
    "// The vortex of a ship coming in lives on its own: it opens with the\n",
    "// Speed along the nose a ship flies at right after coming in, in points\n"
    "// a tick - the same numbers the game moves it by.\n"
    "function fsExitSpeed(e){\n"
    "  if(e.transit) return Math.abs(e.transitV||0);\n"
    "  if(e.escaping) return Math.abs(e.escaping);\n"
    "  if(e.small || e.type==='fighter' || e.type==='bomber') return e.spd || 1.5;\n"
    "  if(allies.indexOf(e) >= 0 || e.targetX == null || !(e.x > e.targetX)) return 0;\n"
    "  if(e.type==='cruiser') return 0.8;\n"
    "  if(e.type==='corvette' || e.type==='destroyer') return 0.6;\n"
    "  if(e.type==='boss') return Math.max(0.25, Math.min(1.5, (e.x-e.targetX)*0.04));\n"
    "  return 0;\n"
    "}\n"
    "// Speed of a ship outside a jump, smoothed, so a jump out can start\n"
    "// from it. Measured on the picture, per game tick.\n"
    "function fsTrack(e){\n"
    "  if(!WARP_STYLE || e.warp>0 || e.warpOut>0) return;\n"
    "  e._fsE0 = null; e._fsV = null;\n"
    "  if(e._lfc != null && fc > e._lfc){\n"
    "    const n = fc - e._lfc;\n"
    "    e._fvx = (e._fvx||0)*0.8 + 0.2*(e.x - e._lx)/n;\n"
    "    e._fvy = (e._fvy||0)*0.8 + 0.2*(e.y - e._ly)/n;\n"
    "  }\n"
    "  e._lfc = fc; e._lx = e.x; e._ly = e.y;\n"
    "}\n"
    "// The vortex of a ship coming in lives on its own: it opens with the\n",
    "helpers")

ui = replace_once(
    ui,
    "    const fgs = fsWarp(e);\n",
    "    fsTrack(e);\n"
    "    const fgs = fsWarp(e);\n",
    "track")

open("src/20_render.js", "w", encoding="utf-8").write(rd)
open("src/70_ui.js", "w", encoding="utf-8").write(ui)
