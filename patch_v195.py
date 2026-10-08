#!/usr/bin/env python3
"""FS3 v195 - capital ship models with their turrets, support card without the hull bar.

    Models     The 3D previews of 13 support ships showed the hull alone:
               FreeSpace keeps turrets, beam emitters, engines and radar
               dishes on the finest detail level only, and the preview uses
               a coarser one (Silvio: the Hecate's beam a grey patch, two
               holes in the Deimos' bow, the Orion's engine section gone).
               The new models carry those parts. They come in
               models_v195.zip; the game asks for them under a new
               revision, so no cache hands out the old ones.
    Support    The card loses the hull bar: it repeated the HULL figure and
               every destroyer and the Colossus filled it (Silvio).

Needs v194. Edits src/58_model3d.js, src/70_ui.js and fieldsim.js. Run
assemble.py afterwards.
"""
import base64
import os
import sys

if "drawDoneButton" not in open("src/70_ui.js", encoding="utf-8").read():
    sys.exit("Abbruch: erst v194 einspielen.")
if "M3D_REV" in open("src/58_model3d.js", encoding="utf-8").read():
    sys.exit("Abbruch: v195 ist schon eingespielt.")

F = {}
def load(p):
    if p not in F: F[p] = open(p, encoding="utf-8").read()
def rep(p, old, new, count=1):
    load(p)
    n = F[p].count(old)
    if n != count:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet %d.\n%s" % (p, n, count, old[:200]))
    F[p] = F[p].replace(old, new)
rep('src/58_model3d.js',
    "// hi.bin with 1024 px textures once the player zooms in. Without WebGL,\n// or while a model loads, the caller draws the sprite as before.\nconst M3D_BASE    = 'models/';\nconst M3D_FOV     = 30 * Math.PI / 180;\nconst M3D_SPIN    = 0.6;          // rad/s while the pointer is on the picture\nconst M3D_YAW0    = 1.22;         // at rest: starboard side, bow to the right, a little of the bow\n",
    "// hi.bin with 1024 px textures once the player zooms in. Without WebGL,\n// or while a model loads, the caller draws the sprite as before.\nconst M3D_BASE    = 'models/';\n// v195: raised whenever the model files change, so neither the browser nor\n// Cloudflare hands out the old ones from its cache.\nconst M3D_REV     = 195;\nconst M3D_FOV     = 30 * Math.PI / 180;\nconst M3D_SPIN    = 0.6;          // rad/s while the pointer is on the picture\nconst M3D_YAW0    = 1.22;         // at rest: starboard side, bow to the right, a little of the bow\n")
rep('src/58_model3d.js',
    "function m3dLevel(key, tag, size){\n  const gl = M3D.gl;\n  const L = {state:'loading', parts:[], tex:{}};\n  fetch(M3D_BASE + key + '/' + tag + '.bin').then(function(r){\n    if(!r.ok) throw new Error('missing'); return r.arrayBuffer();\n  }).then(function(buf){\n    const hl = new DataView(buf).getUint32(0, true);\n",
    "function m3dLevel(key, tag, size){\n  const gl = M3D.gl;\n  const L = {state:'loading', parts:[], tex:{}};\n  fetch(M3D_BASE + key + '/' + tag + '.bin?r=' + M3D_REV).then(function(r){\n    if(!r.ok) throw new Error('missing'); return r.arrayBuffer();\n  }).then(function(buf){\n    const hl = new DataView(buf).getUint32(0, true);\n")
rep('src/58_model3d.js',
    "            L.tex[t][k] = tx; res();\n          };\n          im.onerror = function(){ res(); };       // no glow map is normal\n          im.src = M3D_BASE + key + '/' + t + '_' + k + size + '.webp';\n        }));\n      }\n    }\n",
    "            L.tex[t][k] = tx; res();\n          };\n          im.onerror = function(){ res(); };       // no glow map is normal\n          im.src = M3D_BASE + key + '/' + t + '_' + k + size + '.webp?r=' + M3D_REV;\n        }));\n      }\n    }\n")
rep('src/70_ui.js',
    "  if(d.cls === 'corvette') lines.push('Rearms you while she is on the field (R)');\n  const rk = allyTicket(id);\n  lines.push('In hand: '+(tickets[rk]||0)+(canRefine(rk) ? '  -  '+REFINE_COST+' refine into one of the next class' : ''));\n  // hull against the strongest of the same fleet\n  let top = 1;\n  for(const k in ALLY_DEFS){ const q = ALLY_DEFS[k]; if(q.fac === d.fac && !q.colossus) top = Math.max(top, allyHull(q)); }\n  if(d.colossus) top = allyHull(d);\n  return {model:d.spr, title:allyLabel(d), sub:(CM_FAC_HEAD[d.fac]||'').toUpperCase(), facts:facts,\n          barHead:'HULL AGAINST THE STRONGEST OF THE FLEET',\n          bars:[{l:'HULL', v:Math.min(1, allyHull(d)/top), cur:null, d:null, txt:String(allyHull(d))}],\n          lines:lines, hint:'KEY '+keyLabel+' OR CLICK TO CALL'};\n}\n\n// ── REARM PANEL (v190) ───────────────────────────────────────\n",
    "  if(d.cls === 'corvette') lines.push('Rearms you while she is on the field (R)');\n  const rk = allyTicket(id);\n  lines.push('In hand: '+(tickets[rk]||0)+(canRefine(rk) ? '  -  '+REFINE_COST+' refine into one of the next class' : ''));\n  // v195: no hull bar. It repeated the HULL figure of the facts, and every\n  // destroyer and the Colossus filled it to the end (Silvio).\n  return {model:d.spr, title:allyLabel(d), sub:(CM_FAC_HEAD[d.fac]||'').toUpperCase(), facts:facts,\n          bars:[], lines:lines, hint:'KEY '+keyLabel+' OR CLICK TO CALL'};\n}\n\n// ── REARM PANEL (v190) ───────────────────────────────────────\n")
rep('fieldsim.js',
    '  r.rebuiltAfterWipe = (D.built === fc && D.gen === CACHE_GEN) ? true : [D.built, fc, D.gen, CACHE_GEN];\n  return r;`);\n\n// ── Runner ─────────────────────────────────────────────────────────────\n(async()=>{\n  const browser = await chromium.launch();\n',
    "  r.rebuiltAfterWipe = (D.built === fc && D.gen === CACHE_GEN) ? true : [D.built, fc, D.gen, CACHE_GEN];\n  return r;`);\n\nscenario('v195: support card without the hull bar', 'm=26', `\n  const r = {};\n  const c = allyCard('colossus', 'G'), t = allyCard('vas_typhon', 'R');\n  r.noBar = c.bars.length === 0 && t.bars.length === 0;\n  r.hullStillInFacts = (c.facts.some(f=>f.indexOf('HULL ')===0) && t.facts.some(f=>f.indexOf('HULL ')===0)) ? true : c.facts.concat(t.facts);\n  setCallMenu(true); drawCallMenu(); setCallMenu(false); clearResumeHold();\n  r.draws = true;\n  return r;`);\n\n// ── Runner ─────────────────────────────────────────────────────────────\n(async()=>{\n  const browser = await chromium.launch();\n")

for p, t in F.items():
    open(p, "w", encoding="utf-8").write(t)
print("v195 eingespielt. Jetzt: python3 assemble.py 195")
