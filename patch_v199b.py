#!/usr/bin/env python3
"""FS3 v199b - no more still picture at the start of a mission.

    Start      Silvio: missions with 3D capital ships froze for a few
               seconds at the start. The hit map from the model (v199) was
               drawn as one canvas path of every triangle - 90,000 for the
               Sathanas, seconds of work. It is now filled cell by cell
               (a few milliseconds), the same map.

Needs v199. Edits src/59_field3d.js. Run assemble.py 199 afterwards.
"""
import base64
import os
import sys

if not os.path.exists("src/59_field3d.js"):
    sys.exit("Abbruch: erst v199 einspielen.")
_f = open("src/59_field3d.js", encoding="utf-8").read()
if "F3D_GUNS" not in _f:
    sys.exit("Abbruch: erst v199 einspielen.")
if "v199b" in _f:
    sys.exit("Abbruch: v199b ist schon eingespielt.")

F = {}
def load(p):
    if p not in F: F[p] = open(p, encoding="utf-8").read()
def rep(p, old, new, count=1):
    load(p)
    n = F[p].count(old)
    if n != count:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet %d.\n%s" % (p, n, count, old[:200]))
    F[p] = F[p].replace(old, new)
rep('src/59_field3d.js',
    "  try{\n    const f = Math.min(1, MASK_MAX/Math.max(img.width, img.height));\n    const mw = Math.max(1, Math.round(img.width*f)), mh = Math.max(1, Math.round(img.height*f));\n    const c = document.createElement('canvas'); c.width = mw; c.height = mh;\n    const g = c.getContext('2d', {willReadFrequently: true});\n    const hd = L.head, e = hd.ext/32767, s = mw/hd.size[2];\n    const sg = spriteFacing(skey) === 'left' ? -1 : 1;\n    g.fillStyle = '#fff'; g.beginPath();\n    for(const pt of L.cpu){\n      const P = pt.pos, I = pt.idx;\n      for(let i = 0; i + 2 < I.length; i += 3){\n",
    "  try{\n    const f = Math.min(1, MASK_MAX/Math.max(img.width, img.height));\n    const mw = Math.max(1, Math.round(img.width*f)), mh = Math.max(1, Math.round(img.height*f));\n    const hd = L.head, e = hd.ext/32767, s = mw/hd.size[2];\n    const sg = spriteFacing(skey) === 'left' ? -1 : 1;\n    // v199b (Silvio: a few seconds of still picture at the start): filled\n    // here pixel by pixel instead of as one canvas path - a path of 90,000\n    // triangles held the Sathanas up for seconds. Each triangle sets the\n    // map cells whose centre it covers, at most a few dozen cells apiece.\n    const bits = new Uint8Array(mw*mh);\n    for(const pt of L.cpu){\n      const P = pt.pos, I = pt.idx;\n      for(let i = 0; i + 2 < I.length; i += 3){\n")
rep('src/59_field3d.js',
    "        const ax = mw/2 + sg*P[a+2]*e*s, ay = mh/2 - P[a+1]*e*s;\n        const bx = mw/2 + sg*P[b+2]*e*s, by = mh/2 - P[b+1]*e*s;\n        const cx = mw/2 + sg*P[c3+2]*e*s, cy = mh/2 - P[c3+1]*e*s;\n        // all one way round, or the front and back faces cancel out\n        g.moveTo(ax, ay);\n        if((bx-ax)*(cy-ay) - (by-ay)*(cx-ax) >= 0){ g.lineTo(bx, by); g.lineTo(cx, cy); }\n        else { g.lineTo(cx, cy); g.lineTo(bx, by); }\n        g.closePath();\n      }\n    }\n    g.fill();\n    const d = g.getImageData(0, 0, mw, mh).data;\n    const bits = new Uint8Array(mw*mh);\n    for(let i = 0, p = 3; i < bits.length; i++, p += 4) bits[i] = d[p] > MASK_MIN_A ? 1 : 0;\n    MASKS[skey] = {w: mw, h: mh, bits: bits, model: true};\n    // the hull's box is read off the map again (40_world.js)\n    if(typeof SPR_BOX !== 'undefined') delete SPR_BOX[skey];\n",
    "        const ax = mw/2 + sg*P[a+2]*e*s, ay = mh/2 - P[a+1]*e*s;\n        const bx = mw/2 + sg*P[b+2]*e*s, by = mh/2 - P[b+1]*e*s;\n        const cx = mw/2 + sg*P[c3+2]*e*s, cy = mh/2 - P[c3+1]*e*s;\n        const ar = (bx-ax)*(cy-ay) - (by-ay)*(cx-ax);\n        const x0 = Math.max(0, Math.floor(Math.min(ax, bx, cx))), x1 = Math.min(mw-1, Math.ceil(Math.max(ax, bx, cx)));\n        const y0 = Math.max(0, Math.floor(Math.min(ay, by, cy))), y1 = Math.min(mh-1, Math.ceil(Math.max(ay, by, cy)));\n        if(x1 < x0 || y1 < y0) continue;\n        if(Math.abs(ar) < 1e-6){\n          // edge-on: a sliver still counts where it lies (thin spines)\n          bits[(Math.min(mh-1, Math.max(0, Math.round(ay))))*mw + Math.min(mw-1, Math.max(0, Math.round(ax)))] = 1;\n          continue;\n        }\n        const sgn = ar > 0 ? 1 : -1;\n        for(let y = y0; y <= y1; y++){\n          const py = y + 0.5;\n          for(let x = x0; x <= x1; x++){\n            const px = x + 0.5;\n            const w0 = ((bx-ax)*(py-ay) - (by-ay)*(px-ax))*sgn;\n            const w1 = ((cx-bx)*(py-by) - (cy-by)*(px-bx))*sgn;\n            const w2 = ((ax-cx)*(py-cy) - (ay-cy)*(px-cx))*sgn;\n            if(w0 >= 0 && w1 >= 0 && w2 >= 0) bits[y*mw + x] = 1;\n          }\n        }\n        // a triangle smaller than a cell still marks the cell it sits in\n        if(x1 - x0 <= 1 && y1 - y0 <= 1){\n          const mx = Math.min(mw-1, Math.max(0, Math.floor((ax+bx+cx)/3))), my = Math.min(mh-1, Math.max(0, Math.floor((ay+by+cy)/3)));\n          bits[my*mw + mx] = 1;\n        }\n      }\n    }\n    MASKS[skey] = {w: mw, h: mh, bits: bits, model: true};\n    // the hull's box is read off the map again (40_world.js)\n    if(typeof SPR_BOX !== 'undefined') delete SPR_BOX[skey];\n")

for p, t in F.items():
    open(p, "w", encoding="utf-8").write(t)
print("v199b eingespielt. Jetzt: python3 assemble.py 199")
