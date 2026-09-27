#!/usr/bin/env python3
"""FS3 v149 - warp as in FreeSpace, two looks to compare.

    With ?warp=oval or ?warp=rund in the address a ship no longer fades in
    at the centre of its vortex. The vortex opens behind the ship's final
    spot, the ship shoots out of it nose first and slows down; whatever
    has not come through yet is cut off at the vortex. Jumping out runs
    the other way round: the vortex opens ahead, the ship speeds up into
    it and vanishes from the nose back.

    oval  the vortex is seen from the side, squeezed to a tall narrow
          oval across the flight path
    rund  the vortex stays round, as now

    Without the parameter everything stays as it is. Ships going through
    the Knossos keep the old look, their vortex belongs to the portal.
    Only the picture changes, not where the ship is in the game.

Needs v148. Edits src/20_render.js and src/70_ui.js in place. Run
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
    "function warpSeed(o){",
    "// ?warp=oval or ?warp=rund: ships come out of the vortex as in FreeSpace.\n"
    "const WARP_STYLE = (/[?&]warp=(oval|rund)/.exec(location.search) || [])[1] || '';\n"
    "const WARP_OVAL = 0.35;   // width of the side-on vortex against its height\n"
    "// Where ship and vortex are drawn during a FreeSpace style jump, or null\n"
    "// for the old look. Picture only: the ship's place in the game is e.x/e.y.\n"
    "//   warp in:  vortex opens (0-30 %), ship comes out nose first and slows\n"
    "//             down (25-80 %), vortex closes (75-100 %)\n"
    "//   warp out: ship speeds up into the vortex ahead (20-75 %)\n"
    "function fsWarp(e){\n"
    "  if(!WARP_STYLE || e.portalWarp || e.type==='asteroid') return null;\n"
    "  if(!(e.warp>0) && !(e.warpOut>0)) return null;\n"
    "  const img = IMGS[e.img]; const mW = e.warpMax||100;\n"
    "  if(!img || mW<=1) return null;\n"
    "  const out = e.warpOut>0;\n"
    "  const t = out ? (mW-e.warpOut)/mW : (mW-e.warp)/mW;\n"
    "  // Nose direction: sprites face right, turned by ang, then mirrored.\n"
    "  const s = e.flip ? -1 : 1, a = e.ang||0;\n"
    "  const fx = Math.cos(a)*s, fy = Math.sin(a)*s;\n"
    "  const L = img.width*e.sc, G = L*0.6;   // G: vortex to ship centre\n"
    "  const sg = out ? 1 : -1;                // ahead when leaving, behind when coming\n"
    "  let px = (e.warpX!=null ? e.warpX : e.x) + sg*fx*G;\n"
    "  const py = (e.warpY!=null ? e.warpY : e.y) + sg*fy*G;\n"
    "  px = Math.max(10, Math.min(W-10, px));  // keep the vortex on the screen\n"
    "  const wS = t<0.30 ? 0.05+0.95*t/0.30 : (t<0.75 ? 1 : Math.max(0, 1-(t-0.75)/0.25));\n"
    "  let u, vis = true;\n"
    "  if(!out){\n"
    "    const k = (t-0.25)/0.55; if(k<=0) vis = false;\n"
    "    const kk = Math.min(1, Math.max(0, k));\n"
    "    u = -(G+L/2)*Math.pow(1-kk, 3);         // fast out, then braking\n"
    "  } else {\n"
    "    const k = Math.min(1, Math.max(0, (t-0.20)/0.55)); if(k>=1) vis = false;\n"
    "    u = (G+L/2)*k*k*k;                      // speeding up into it\n"
    "  }\n"
    "  return {out, fx, fy, px, py, wS, wA: Math.min(1, wS*1.4), dx: fx*u, dy: fy*u, vis};\n"
    "}\n"
    "// Clip to the side of the vortex the ship is on: in front of it when\n"
    "// coming out, behind it when going in.\n"
    "function fsWarpClip(g){\n"
    "  const B = 5000, sg = g.out ? -1 : 1, tx = -g.fy, ty = g.fx;\n"
    "  ctx.beginPath();\n"
    "  ctx.moveTo(g.px+tx*B, g.py+ty*B);\n"
    "  ctx.lineTo(g.px+tx*B+g.fx*B*sg, g.py+ty*B+g.fy*B*sg);\n"
    "  ctx.lineTo(g.px-tx*B+g.fx*B*sg, g.py-ty*B+g.fy*B*sg);\n"
    "  ctx.lineTo(g.px-tx*B, g.py-ty*B);\n"
    "  ctx.closePath();\n"
    "  ctx.clip();\n"
    "}\n"
    "function warpSeed(o){",
    "fsWarp")

ui = replace_once(
    ui,
    "      if(e.warp>0 || e.warpOut>0){\n"
    "        try{\n",
    "      if(e.warp>0 || e.warpOut>0){\n"
    "        // FreeSpace style: the vortex stands across the flight path.\n"
    "        const fg = fsWarp(e);\n"
    "        if(fg){\n"
    "          try{\n"
    "            let WSf = 120; const fImg = IMGS[e.img];\n"
    "            if(fImg) WSf = Math.max(100, fImg.height*e.sc*1.9, fImg.width*e.sc*0.62);\n"
    "            ctx.save();\n"
    "            ctx.globalAlpha = fg.wA;\n"
    "            ctx.translate(fg.px|0, fg.py|0);\n"
    "            if(WARP_STYLE==='oval'){ ctx.rotate(Math.atan2(fg.fy, fg.fx)); ctx.scale(WARP_OVAL*fg.wS, fg.wS); }\n"
    "            else ctx.scale(fg.wS, fg.wS);\n"
    "            drawWarpFrame(warpSeed(e), WSf, false);\n"
    "            ctx.restore(); ctx.globalAlpha = 1;\n"
    "          }catch(ef){ ctx.restore(); ctx.globalAlpha = 1; }\n"
    "          continue;\n"
    "        }\n"
    "        try{\n",
    "vortex fs")

ui = replace_once(
    ui,
    "    var wAlpha=1;\n"
    "    if(e.warp>0){\n",
    "    var wAlpha=1;\n"
    "    // FreeSpace style: the hull slides through the vortex and is cut off\n"
    "    // where it has not come through yet. Nothing else is drawn until the\n"
    "    // jump is over.\n"
    "    const fgs = fsWarp(e);\n"
    "    if(fgs){\n"
    "      if(!fgs.vis) continue;\n"
    "      ctx.save();\n"
    "      fsWarpClip(fgs);\n"
    "      ctx.translate(fgs.dx, fgs.dy);\n"
    "      drawThrusters(e.img,e.x|0,e.y|0,e.sc,e.flip,e.faction,fgs.out?1:0.6,e.ang||0);\n"
    "      drawShip(e.img,e.x|0,e.y|0,e.sc,e.flip,e.ang||0);\n"
    "      ctx.restore();\n"
    "      continue;\n"
    "    }\n"
    "    if(e.warp>0){\n",
    "ship fs")

open("src/20_render.js", "w", encoding="utf-8").write(rd)
open("src/70_ui.js", "w", encoding="utf-8").write(ui)
