#!/usr/bin/env python3
"""FS3 v200 - no hitches when a big ship warps in.

    Loading    Silvio: short hitches when a capital ship warped in (the
               Moloch in M77). Measured: her model was loaded when she
               appeared, and handing its textures to the graphics card
               blocked the game - eight uploads in a row for her fine
               level. Now every 3D capital ship loads while the title
               shows (a bar: LOADING 3D SHIPS n/24). The pictures are
               decoded off the game's thread and handed over one at a time
               between frames, and every ship is drawn once out of sight so
               the driver has her ready. A ship not loaded yet when she
               appears loads as before, now also in small steps.

Needs v199b. Edits src/59_field3d.js, src/70_ui.js and fieldsim.js. Run
assemble.py 200 afterwards.
"""
import base64
import os
import sys

if not os.path.exists("src/59_field3d.js"):
    sys.exit("Abbruch: erst v199 einspielen.")
_f = open("src/59_field3d.js", encoding="utf-8").read()
if "v199b" not in _f:
    sys.exit("Abbruch: erst v199b einspielen.")
if "F3D_PRE" in _f:
    sys.exit("Abbruch: v200 ist schon eingespielt.")

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
    "      for(const k of (F3D_GANIM[t] ? ['c', 'n', 'g', 'ga'] : ['c', 'n', 'g'])){\n        jobs.push(new Promise(function(res){\n          const im = new Image();\n          im.onload = function(){\n            if(gl !== F3D.gl) return res();\n            const tx = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tx);\n            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);\n",
    "      for(const k of (F3D_GANIM[t] ? ['c', 'n', 'g', 'ga'] : ['c', 'n', 'g'])){\n        jobs.push(new Promise(function(res){\n          const im = new Image();\n          // v200: decoded by the browser off the game's thread, then handed\n          // to the graphics card in the upload queue - one at a time between\n          // frames instead of all in one (Silvio: hitches when a big ship\n          // warped in, the Moloch in M77).\n          const up = function(){\n            if(gl !== F3D.gl) return res();\n            const tx = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tx);\n            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);\n")
rep('src/59_field3d.js',
    "            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);\n            L.tex[t][k] = tx; res();\n          };\n          im.onerror = function(){ res(); };       // no glow map is normal\n          im.src = M3D_BASE + key + '/' + t + '_' + k + size + '.webp?r=' + rev;\n        }));\n",
    "            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);\n            L.tex[t][k] = tx; res();\n          };\n          im.onload = function(){\n            const go = function(){ f3dUpload(up); };\n            if(im.decode) im.decode().then(go, go); else go();\n          };\n          im.onerror = function(){ res(); };       // no glow map is normal\n          im.src = M3D_BASE + key + '/' + t + '_' + k + size + '.webp?r=' + rev;\n        }));\n")
rep('src/59_field3d.js',
    "    return Promise.all(jobs);\n  }).then(function(){ L.state = 'ready'; }, function(){ L.state = 'failed'; });\n  return L;\n}\n// The coarse level comes first so the ship shows soon; the full one (every\n// part of the finest level, v196) follows and takes over once it is in.\n",
    "    return Promise.all(jobs);\n  }).then(function(){ L.state = 'ready'; }, function(){ L.state = 'failed'; });\n  return L;\n}\n// ── UPLOADS AND LOADING UP FRONT (v200) ──────────────────────\n// Handing a texture to the graphics card blocks the game while it runs\n// (measured in M77: the Moloch's fine level, eight uploads one after the\n// other). The queue does them between frames, a few milliseconds at a time.\nconst F3D_UPQ = [];\nlet F3D_PUMP = false;\nconst F3D_UP_MS = 6;\nfunction f3dNow(){ return (typeof performance !== 'undefined') ? performance.now() : Date.now(); }\nfunction f3dUpload(job){\n  F3D_UPQ.push(job);\n  if(!F3D_PUMP){ F3D_PUMP = true; setTimeout(f3dPump, 0); }\n}\nfunction f3dPump(){\n  const t0 = f3dNow();\n  // at least one job per turn, more while there is time\n  do { const j = F3D_UPQ.shift(); try{ j(); }catch(e){ F3D.err = String(e && e.message || e); } }\n  while(F3D_UPQ.length && f3dNow() - t0 < F3D_UP_MS);\n  if(F3D_UPQ.length) setTimeout(f3dPump, 4); else F3D_PUMP = false;\n}\n// Silvio: load every 3D capital ship before the game starts, not when she\n// warps in. Starts as soon as the title shows; the title shows how far it\n// is. A ship not ready by the time she appears loads as before.\nconst F3D_PRE = {on: false, done: false, n: 0, of: 0};\nfunction f3dPreload(){\n  if(F3D_PRE.on || F3D.off || typeof document === 'undefined' || !f3dInit()) return;\n  F3D_PRE.on = true; F3D_PRE.of = F3D_KEYS.length;\n  const tick = function(){\n    if(!F3D.gl){ F3D_PRE.done = true; return; }      // context lost: as before\n    let n = 0;\n    for(const k of F3D_KEYS){ const m = f3dModel(k); if(m.full && m.full.state !== 'loading') n++; }\n    F3D_PRE.n = n;\n    if(n < F3D_KEYS.length) setTimeout(tick, 250);\n    else { F3D_PRE.done = true; f3dWarm(); }\n  };\n  tick();\n}\n// Every loaded ship drawn once, out of sight: the graphics driver sets a\n// texture up for good only the first time it is used (in sight: what lies\n// outside the picture is never drawn), and that first time\n// cost a frame of 0.4 s at the start of a mission (measured).\nfunction f3dWarm(){\n  const gl = F3D.gl; if(!gl) return;\n  const ks = F3D_KEYS.slice();\n  const one = function(){\n    const k = ks.shift(); if(!k || gl !== F3D.gl) return;\n    try{\n      const L = f3dReadyLevel(k);\n      if(L && typeof IMGS !== 'undefined' && IMGS[k]){\n        const e = {img: k, sc: 64/Math.max(1, IMGS[k].width), flip: false, ang: 0};\n        f3dRender([{e: e, L: L, x: W/2, y: H/2, a: 1, clip: null}], true);\n      }\n    }catch(er){}\n    setTimeout(one, 30);\n  };\n  one();\n}\n// The bar on the title screen while the ships load.\nfunction f3dPreloadBar(){\n  if(!F3D_PRE.on) f3dPreload();\n  if(!F3D_PRE.on || F3D_PRE.done) return;\n  const w = 220, h = 4, x = W/2 - w/2, y = H - 34;\n  ctx.save();\n  ctx.fillStyle = 'rgba(255,255,255,0.15)'; ctx.fillRect(x, y, w, h);\n  ctx.fillStyle = (typeof TH === 'function') ? TH('glow') : '#7cf';\n  ctx.fillRect(x, y, w*F3D_PRE.n/Math.max(1, F3D_PRE.of), h);\n  ctx.fillStyle = (typeof TH === 'function') ? TH('text') : '#ccc';\n  ctx.font = (typeof thValue === 'function') ? thValue(11, false) : '11px sans-serif';\n  ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';\n  ctx.fillText('LOADING 3D SHIPS ' + F3D_PRE.n + '/' + F3D_PRE.of, W/2, y - 4);\n  ctx.restore();\n}\n// The coarse level comes first so the ship shows soon; the full one (every\n// part of the finest level, v196) follows and takes over once it is in.\n")
rep('src/59_field3d.js',
    "}\n// Draws the given ships into the field canvas and copies it into the\n// field. items: {e, L, x, y, a (alpha), clip (screen half-plane or null)}.\nfunction f3dRender(items){\n  const gl = F3D.gl, can = F3D.can, loc = F3D.loc;\n  const pw = (typeof CVS !== 'undefined' && CVS.width) || Math.round(W), ph = (typeof CVS !== 'undefined' && CVS.height) || Math.round(H);\n  if(can.width !== pw || can.height !== ph){ can.width = pw; can.height = ph; }\n",
    "}\n// Draws the given ships into the field canvas and copies it into the\n// field. items: {e, L, x, y, a (alpha), clip (screen half-plane or null)}.\nfunction f3dRender(items, warm){\n  const gl = F3D.gl, can = F3D.can, loc = F3D.loc;\n  const pw = (typeof CVS !== 'undefined' && CVS.width) || Math.round(W), ph = (typeof CVS !== 'undefined' && CVS.height) || Math.round(H);\n  if(can.width !== pw || can.height !== ph){ can.width = pw; can.height = ph; }\n")
rep('src/59_field3d.js',
    '    }\n  }\n  gl.disable(gl.BLEND);\n  ctx.drawImage(can, 0, 0, W, H);\n}\nfunction f3dNorm(v){ const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0]/l, v[1]/l, v[2]/l]; }\n// Whether a ship is drawn here this frame, and how: the same decisions the\n',
    '    }\n  }\n  gl.disable(gl.BLEND);\n  if(!warm) ctx.drawImage(can, 0, 0, W, H);\n}\nfunction f3dNorm(v){ const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0]/l, v[1]/l, v[2]/l]; }\n// Whether a ship is drawn here this frame, and how: the same decisions the\n')
rep('src/70_ui.js',
    "  if(GS==='playing' && subspaceOn()) drawSubspace();\n  else { drawNebula(); drawBodies(); drawStars(); }\n\n  if(GS==='title'){drawTitle();return;}\n  if(GS==='gameover'){drawGO();return;}\n\n  const loaded=imgsLoaded+nebsLoaded;\n",
    "  if(GS==='playing' && subspaceOn()) drawSubspace();\n  else { drawNebula(); drawBodies(); drawStars(); }\n\n  if(GS==='title'){drawTitle(); if(typeof f3dPreloadBar==='function') try{ f3dPreloadBar(); }catch(ep){} return;}\n  if(GS==='gameover'){drawGO();return;}\n\n  const loaded=imgsLoaded+nebsLoaded;\n")
rep('fieldsim.js',
    '  try{ draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }\n  return r;`);\n\n// ── Runner ─────────────────────────────────────────────────────────────\n(async()=>{\n  const browser = await chromium.launch();\n',
    "  try{ draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }\n  return r;`);\n\nscenario('v200: models loaded up front, uploads queued between frames', 'm=77', `\n  const r = {};\n  r.haveQueue = typeof f3dUpload === 'function' && typeof f3dPreload === 'function' && !!F3D_PRE;\n  // the queue runs every job, a few at a time\n  let n = 0; for(let i=0;i<5;i++) f3dUpload(function(){ n++; });\n  await new Promise(function(res){ setTimeout(res, 120); });\n  r.queueRuns = n === 5 && F3D_UPQ.length === 0;\n  // no model files here: the preload ends without hanging, the game runs\n  f3dPreload();\n  for(let i=0;i<40 && F3D_PRE.on && !F3D_PRE.done;i++) await new Promise(function(res){ setTimeout(res, 300); });\n  r.preloadEnds = !F3D_PRE.on || F3D_PRE.done;\n  try{ GS='title'; draw(); GS='playing'; draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }\n  return r;`);\n\n// ── Runner ─────────────────────────────────────────────────────────────\n(async()=>{\n  const browser = await chromium.launch();\n")
rep('fieldsim.js',
    "    await page.waitForTimeout(300);\n    let res;\n    try{\n      res = await page.evaluate(HELPERS + `\\nFS.fakeImages();` + (sc.noLaunch ? '' : ' launchGame();') + `\\n(function(){${sc.body}})()`);\n    }catch(e){ res = null; errs.push(String(e.message||e)); }\n    console.log(sc.name + '  (?' + sc.query + ')');\n    if(res) for(const [k,v] of Object.entries(res)){\n",
    "    await page.waitForTimeout(300);\n    let res;\n    try{\n      res = await page.evaluate(HELPERS + `\\nFS.fakeImages();` + (sc.noLaunch ? '' : ' launchGame();') + `\\n(async function(){${sc.body}})()`);\n    }catch(e){ res = null; errs.push(String(e.message||e)); }\n    console.log(sc.name + '  (?' + sc.query + ')');\n    if(res) for(const [k,v] of Object.entries(res)){\n")

for p, t in F.items():
    open(p, "w", encoding="utf-8").write(t)
print("v200 eingespielt. Jetzt: python3 assemble.py 200")
