#!/usr/bin/env python3
"""FS3 v215 - beams stay on their turret, fewer lags (Silvio, 11.10.2026).

    Beams      The stretch over the firing ship: fine steps along the ray,
               small gaps in the outline allowed (at the turret and between
               hull parts), smoothed from frame to frame. The coarse test
               of v214 gave 0 whenever the turret sat a hair outside the
               outline - the ray then seemed to start at the hull's edge,
               away from its turret, and jumped back the next frame
               (measured on the Deimos: 0, 96, 153, 288). Longer fade.
    Lags       From Silvio's lag log: damage pictures were rebuilt 8-26
               times a second per capital ship in a fight (each one goes to
               the graphics card) - now at most four times a second. The
               long frames came with ~900 particles: the cap is 650, faded
               particles draw no glow, bolts have two trail glows (three).

Needs v214. Edits src/20_render.js, 50_combat.js, 57_turrets.js.
Run assemble.py 215 afterwards.
"""
import base64
import os
import sys

if not os.path.exists("src/62_perf.js"):
    sys.exit("Abbruch: erst v214 einspielen.")
if "DMG_REBUILD_STEPS" in open("src/20_render.js", encoding="utf-8").read():
    sys.exit("v215 ist schon eingespielt.")

F = {}
def load(p):
    if p not in F: F[p] = open(p, encoding="utf-8").read()
def rep(p, old, new, count=1):
    load(p)
    n = F[p].count(old)
    if n != count:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet %d.\n%s" % (p, n, count, old[:200]))
    F[p] = F[p].replace(old, new)
rep('src/20_render.js',
    '  }\n}\nfunction tickParts(){\n  if(PARTS.length>900)PARTS.splice(0,PARTS.length-900);\n  for(var i=PARTS.length-1;i>=0;i--){\n    var p=PARTS[i];\n    if(p.ml===0) p.ml=p.life;\n',
    "  }\n}\nfunction tickParts(){\n  // v215: 650 (900 before) - in the lag log the long frames came with ~900\n  // particles, the time spent outside the game's code (drawing them on the\n  // graphics card, each a soft additive glow since v213)\n  if(PARTS.length>650)PARTS.splice(0,PARTS.length-650);\n  for(var i=PARTS.length-1;i>=0;i--){\n    var p=PARTS[i];\n    if(p.ml===0) p.ml=p.life;\n")
rep('src/20_render.js',
    "      var clr=p.clr||'#ffffff';\n      // v213: one soft glow with a white-hot heart (glowAt), no rings\n      ctx.globalAlpha=1;\n      glowAt(p.x, p.y, sz2*1.9, sz2*1.9, clr, a, 0.7);\n    }\n  }\n  ctx.restore(); // stellt globalAlpha, lineWidth, etc. wieder her\n",
    "      var clr=p.clr||'#ffffff';\n      // v213: one soft glow with a white-hot heart (glowAt), no rings\n      ctx.globalAlpha=1;\n      if(a > 0.04) glowAt(p.x, p.y, sz2*1.6, sz2*1.6, clr, a, 0.7);   // v215: smaller, none when faded\n    }\n  }\n  ctx.restore(); // stellt globalAlpha, lineWidth, etc. wieder her\n")
rep('src/20_render.js',
    '  return Math.max(1, Math.min(RES_X, 1/Math.max(0.05, e.sc), DMG_K_MAX));\n}\n// The ship, with what she has taken. Same transform as drawShip().\nfunction drawShipE(e, cx, cy, scale, flipX, ang){\n  // v211: in her turn (capTurnStep) the picture is narrowed about her middle\n  if(e.turnSq && !drawShipE._in){\n',
    "  return Math.max(1, Math.min(RES_X, 1/Math.max(0.05, e.sc), DMG_K_MAX));\n}\n// The ship, with what she has taken. Same transform as drawShip().\nconst DMG_REBUILD_STEPS = 25;   // v215: steps between two builds of one ship's damage picture\nfunction drawShipE(e, cx, cy, scale, flipX, ang){\n  // v211: in her turn (capTurnStep) the picture is narrowed about her middle\n  if(e.turnSq && !drawShipE._in){\n")
rep('src/20_render.js',
    '  if(D.gen !== CACHE_GEN){ D.gen = CACHE_GEN; D.dirty = true; D.built = -99; D.fBuilt = -1; D.fxT = -99; }\n  // the screen resolution changed (window, fullscreen): rebuild at the new one\n  if(D.can && D.k !== dmgK(e)) D.dirty = true;\n  if(D.dirty && (fc - (D.built||-99) >= 3 || !D.can || D.k !== dmgK(e))) dmgBuild(e, D);\n  const img = IMGS[e.img];\n  const w = img.width*scale, h = img.height*scale;\n  // v204: drawn from her model the marks lie on the model (f3dDmgBind,\n',
    '  if(D.gen !== CACHE_GEN){ D.gen = CACHE_GEN; D.dirty = true; D.built = -99; D.fBuilt = -1; D.fxT = -99; }\n  // the screen resolution changed (window, fullscreen): rebuild at the new one\n  if(D.can && D.k !== dmgK(e)) D.dirty = true;\n  // v215 (Silvio\'s lag log: "damage picture" built 8-26 times a second per\n  // capital ship in a fight, the lags fell outside the game\'s code - the\n  // picture goes up to the graphics card each time): at most four times a\n  // second; a new mark shows up to a quarter second later\n  if(D.dirty && (fc - (D.built||-99) >= DMG_REBUILD_STEPS || !D.can || D.k !== dmgK(e))) dmgBuild(e, D);\n  const img = IMGS[e.img];\n  const w = img.width*scale, h = img.height*scale;\n  // v204: drawn from her model the marks lie on the model (f3dDmgBind,\n')
rep('src/50_combat.js',
    '    // (drawnHullRun), then fading out over the stretch under it - the two\n    // pieces no longer lie on top of each other beside her hull, which was\n    // the hard edge (Silvio)\n    const len = own ? drawnHullRun(e, mpF.x, mpF.y, ang) : 2000/CAM.z;\n    const g = fxG();                           // v209: v207 widths on the screen\n    if(len <= 0) continue;\n    const ex=mpF.x+Math.cos(ang)*len, ey=mpF.y+Math.sin(ang)*len;\n',
    '    // (drawnHullRun), then fading out over the stretch under it - the two\n    // pieces no longer lie on top of each other beside her hull, which was\n    // the hard edge (Silvio)\n    const len = own ? ownRunSmooth(e, b, mpF.x, mpF.y, ang) : 2000/CAM.z;\n    const g = fxG();                           // v209: v207 widths on the screen\n    if(len <= 0) continue;\n    const ex=mpF.x+Math.cos(ang)*len, ey=mpF.y+Math.sin(ang)*len;\n')
rep('src/50_combat.js',
    '    // running along it (drawBeamRay, 61_glow.js); a little wider while the\n    // shot builds up and as it dies away\n    const bw = (b.large?7.5:3.6)*g;\n    const fade = own ? Math.max(6, bw*3) : 0;\n    drawBeamRay(mpF.x, mpF.y, ang, own ? len + fade : len, bw*flicker, col, 0.95, fc, bw, fade);\n    if(hid) drawBeamOrb(e, b);\n  }\n',
    '    // running along it (drawBeamRay, 61_glow.js); a little wider while the\n    // shot builds up and as it dies away\n    const bw = (b.large?7.5:3.6)*g;\n    const fade = own ? Math.max(10, bw*5) : 0;     // v215: a longer fade\n    drawBeamRay(mpF.x, mpF.y, ang, own ? len + fade : len, bw*flicker, col, 0.95, fc, bw, fade);\n    if(hid) drawBeamOrb(e, b);\n  }\n')
rep('src/50_combat.js',
    '  let last = 0;\n  for(let t = 0; t <= box; t += st) if(onHullAt(e, x + c*t, y + s*t)) last = t;\n  return last;\n}\n// How far a ray from (x,y) at angle a runs before it leaves the box of\n// ship e.\n',
    "  let last = 0;\n  for(let t = 0; t <= box; t += st) if(onHullAt(e, x + c*t, y + s*t)) last = t;\n  return last;\n}\n// v215 (Silvio: beams still jumped, the ray apart from its turret): the\n// first test stepped coarsely and gave 0 whenever the turret sat a hair\n// outside the outline - then the ray seemed to start at the hull's edge,\n// and the next frame it was back (measured on the Deimos: 0, 96, 153, 288).\n// Now: fine steps, a gap of up to HULL_GAP units allowed (at the turret and\n// between parts of the hull), the end of that first stretch of hull, and\n// smoothed per beam from frame to frame.\nconst HULL_GAP = 16;\nfunction hullRunFine(e, x, y, a){\n  const box = ownHullRun(e, x, y, a);\n  if(!(box > 0) || typeof onHullAt !== 'function') return box;\n  const c = Math.cos(a), s = Math.sin(a), st = Math.max(2, box/400);\n  let last = -1, miss = 0;\n  for(let t = 0; t <= box; t += st){\n    if(onHullAt(e, x + c*t, y + s*t)){ last = t; miss = 0; }\n    else if(last >= 0 || t > HULL_GAP){ miss += st; if(miss > HULL_GAP) break; }\n  }\n  return Math.max(0, last);\n}\nfunction ownRunSmooth(e, b, x, y, a){\n  const v = hullRunFine(e, x, y, a);\n  if(b._ownFc == null || fc - b._ownFc > 6 || b._own == null){ b._own = v; }\n  else b._own += (v - b._own)*0.2;\n  b._ownFc = fc;\n  return b._own;\n}\n// How far a ray from (x,y) at angle a runs before it leaves the box of\n// ship e.\n")
rep('src/57_turrets.js',
    '  ctx.save();\n  ctx.translate(bx, by);\n  ctx.rotate(ang);\n  for(let k=3;k>=1;k--) glowAt(-len*0.55*k, 0, len*0.75, wid*0.9, glow, 0.30*(4-k)/3, 0);\n  glowAt(0, 0, len*0.95, wid*1.7, glow, 0.95, 0);\n  glowAt(0, 0, len*0.62, wid*0.85, core, 1, 0.5);\n  glowAt(len*0.08, 0, len*0.34, wid*0.42, hot, 1, 1);\n',
    '  ctx.save();\n  ctx.translate(bx, by);\n  ctx.rotate(ang);\n  // v215: two trail glows (three before), less to fill on the graphics card\n  for(let k=2;k>=1;k--) glowAt(-len*0.6*k, 0, len*0.8, wid*0.9, glow, 0.32*(3-k)/2, 0);\n  glowAt(0, 0, len*0.95, wid*1.7, glow, 0.95, 0);\n  glowAt(0, 0, len*0.62, wid*0.85, core, 1, 0.5);\n  glowAt(len*0.08, 0, len*0.34, wid*0.42, hot, 1, 1);\n')

for p, t in F.items():
    open(p, "w", encoding="utf-8").write(t)
print("v215 eingespielt. Jetzt: python3 assemble.py 215")
