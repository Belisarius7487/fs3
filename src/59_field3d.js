// ── CAPITAL SHIPS IN 3D ON THE FIELD (v196) ──────────────────
// The 2.5D plan, step 1 (Silvio): capital ships that have a converted
// model are drawn from it instead of from their sprite. Everything the game
// does with a ship stays as it was - position, facing, hits, mounts and the
// damage logic all read the sprite as before; only the picture of the hull
// comes from a WebGL canvas the size of the field. That canvas is copied
// into the field once a frame, after the backdrop, beams and wreckage and
// before the small craft, so fighters and shots stay on top of the
// capitals. A perspective camera looks straight at the middle of the
// field: the plane z = 0 lands exactly where the 2D drawing has it, and
// only the hull's own depth shows perspective. Capitals among themselves
// share one depth buffer, so an overlap is a real overlap.
// Without WebGL, until a model has loaded, or for a hull without a model
// (the Shivans and the NTF reskins for now) the sprite is drawn as before.
// v197: the Shivan capital ships as well (first line)
const F3D_KEYS = ['crcain', 'crlilith', 'crrakshasa', 'comoloch', 'dedemon', 'deravana', 'sdlucifer', 'sdsathanas',
  'crfenris', 'crleviathan', 'craeolus', 'codeimos', 'deorionright', 'dehecate',
  'craten', 'crmentu', 'cosobek', 'detyphon', 'dehatshepsut', 'sdcolossus', 'sgmjolnir',
  'cacharybdis', 'casetekh', 'coiceni'];
const F3D_ALIAS = {deorionleft: 'deorionright'};
const F3D_FOV = 30*Math.PI/180;
// key light from the upper left and in front, a weak fill from below
// right - the same as the previews
const F3D_L1 = [-0.45, 0.65, 0.62], F3D_L2 = [0.7, -0.25, 0.4];
const F3D = {ok: null, gl: null, can: null, prog: null, loc: null, models: {}, white: null, black: null, flatN: null,
             // &f3d=0 in the address draws every ship as a sprite, to compare
             off: (typeof location !== 'undefined' && /[?&]f3d=0(&|$)/.test(location.search||''))};

function f3dKey(e){
  if(!e || !e.img || e.type === 'asteroid') return null;
  const k = F3D_ALIAS[e.img] || e.img;
  return F3D_KEYS.indexOf(k) >= 0 ? k : null;
}
function f3dInit(){
  if(F3D.ok !== null) return F3D.ok;
  F3D.ok = false;
  try{
    if(typeof document === 'undefined' || !document.createElement) return false;
    const can = document.createElement('canvas');
    const gl = can.getContext('webgl', {alpha: true, premultipliedAlpha: true, antialias: true,
                                        preserveDrawingBuffer: true, depth: true});
    if(!gl) return false;
    const deriv = !!gl.getExtension('OES_standard_derivatives');
    gl.getExtension('OES_element_index_uint');
    const vs = 'attribute vec3 aP; attribute vec3 aN; attribute vec2 aT;'
      + 'uniform mat4 uM; uniform mat4 uVP; varying vec3 vW; varying vec3 vN; varying vec2 vT;'
      + 'void main(){ vec4 w = uM*vec4(aP,1.0); vW = w.xyz; vN = mat3(uM)*aN; vT = aT*3.99994-1.0; gl_Position = uVP*w; }';
    const fs = (deriv ? '#extension GL_OES_standard_derivatives : enable\n#define DERIV 1\n' : '')
      + 'precision mediump float; varying vec3 vW; varying vec3 vN; varying vec2 vT;'
      + 'uniform sampler2D tC; uniform sampler2D tN; uniform sampler2D tG;'
      + 'uniform float uHasN; uniform float uKind; uniform vec3 uCam; uniform vec3 uL1; uniform vec3 uL2;'
      + 'uniform vec3 uClip; uniform float uA;'
      + 'void main(){'
      + ' if(dot(uClip.xy, vW.xy) + uClip.z < 0.0) discard;'
      + ' vec3 N = normalize(vN);'
      + '\n#ifdef DERIV\n'
      + ' if(uHasN > 0.5){ vec3 d1 = dFdx(vW), d2 = dFdy(vW); vec2 t1 = dFdx(vT), t2 = dFdy(vT);'
      + '  vec3 c2 = cross(d2, N), c1 = cross(N, d1); vec3 T = c2*t1.x + c1*t2.x; vec3 B = c2*t1.y + c1*t2.y;'
      + '  float im = inversesqrt(max(max(dot(T,T), dot(B,B)), 1e-20));'
      + '  vec2 nm = texture2D(tN, vT).rg*2.0-1.0; vec3 tn = vec3(nm, sqrt(max(0.0, 1.0-dot(nm,nm))));'
      + '  N = normalize(T*im*tn.x - B*im*tn.y + N*tn.z); }\n'
      + '\n#endif\n'
      + ' vec3 base = uKind < 0.5 ? texture2D(tC, vT).rgb : (uKind > 1.5 ? vec3(0.05,0.07,0.10) : vec3(0.30,0.30,0.32));'
      + ' vec3 V = normalize(uCam - vW);'
      + ' float d = max(dot(N, uL1), 0.0)*0.95 + max(dot(N, uL2), 0.0)*0.30;'
      + ' float s = pow(max(dot(N, normalize(uL1+V)), 0.0), uKind > 1.5 ? 60.0 : 24.0)*(uKind > 1.5 ? 0.9 : 0.35);'
      + ' vec3 col = base*(0.30 + d*1.15)*1.15 + vec3(s);'
      + ' if(uKind < 0.5) col += texture2D(tG, vT).rgb;'
      + ' gl_FragColor = vec4(col*uA, uA); }';
    const sh = function(t, src){ const s = gl.createShader(t); gl.shaderSource(s, src); gl.compileShader(s);
      if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(pr);
    if(!gl.getProgramParameter(pr, gl.LINK_STATUS)) return false;
    const loc = {};
    for(const a of ['aP', 'aN', 'aT']) loc[a] = gl.getAttribLocation(pr, a);
    for(const u of ['uM', 'uVP', 'tC', 'tN', 'tG', 'uHasN', 'uKind', 'uCam', 'uL1', 'uL2', 'uClip', 'uA']) loc[u] = gl.getUniformLocation(pr, u);
    const px = function(r, g, b){ const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([r, g, b, 255])); return t; };
    F3D.white = px(160, 160, 160); F3D.black = px(0, 0, 0); F3D.flatN = px(128, 128, 255);
    // a lost context takes every buffer with it: start over, sprites meanwhile
    can.addEventListener('webglcontextlost', function(ev){
      ev.preventDefault(); F3D.models = {}; F3D.gl = null; F3D.ok = null;
    }, false);
    F3D.gl = gl; F3D.can = can; F3D.prog = pr; F3D.loc = loc;
    F3D.ok = true;
  }catch(e){ F3D.ok = false; F3D.err = String(e && e.message || e); }
  return F3D.ok;
}
// One level of a model into this context: the same files the previews use.
function f3dLevel(key, tag, size){
  const gl = F3D.gl, rev = (typeof M3D_REV !== 'undefined') ? M3D_REV : 0;
  const L = {state: 'loading', parts: [], tex: {}};
  fetch(M3D_BASE + key + '/' + tag + '.bin?r=' + rev).then(function(r){
    if(!r.ok) throw new Error('missing'); return r.arrayBuffer();
  }).then(function(buf){
    if(gl !== F3D.gl) throw new Error('lost');
    const hl = new DataView(buf).getUint32(0, true);
    const head = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 4, hl)));
    const data = buf.slice(4 + hl);
    L.head = head;
    const want = {};
    for(const p of head.parts){
      const mk = function(target, from, bytes){ const b = gl.createBuffer(); gl.bindBuffer(target, b);
        gl.bufferData(target, new Uint8Array(data, from, bytes), gl.STATIC_DRAW); return b; };
      L.parts.push({kind: p.kind, tex: (p.tex||'').toLowerCase(), n: p.ni, big: p.big,
        pos: mk(gl.ARRAY_BUFFER, p.pos, p.nv*6), nrm: mk(gl.ARRAY_BUFFER, p.nrm, p.nv*4),
        uv: mk(gl.ARRAY_BUFFER, p.uv, p.nv*4), idx: mk(gl.ELEMENT_ARRAY_BUFFER, p.idx, p.ni*(p.big?4:2))});
      if(p.kind === 'tex') want[(p.tex||'').toLowerCase()] = true;
    }
    const jobs = [];
    for(const t in want){
      L.tex[t] = {};
      for(const k of ['c', 'n', 'g']){
        jobs.push(new Promise(function(res){
          const im = new Image();
          im.onload = function(){
            if(gl !== F3D.gl) return res();
            const tx = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tx);
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
            gl.generateMipmap(gl.TEXTURE_2D);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
            L.tex[t][k] = tx; res();
          };
          im.onerror = function(){ res(); };       // no glow map is normal
          im.src = M3D_BASE + key + '/' + t + '_' + k + size + '.webp?r=' + rev;
        }));
      }
    }
    return Promise.all(jobs);
  }).then(function(){ L.state = 'ready'; }, function(){ L.state = 'failed'; });
  return L;
}
// The coarse level comes first so the ship shows soon; the full one (every
// part of the finest level, v196) follows and takes over once it is in.
function f3dModel(key){
  let m = F3D.models[key];
  if(!m){
    m = F3D.models[key] = {lo: f3dLevel(key, 'lo', 512), full: null};
  }
  if(!m.full && m.lo.state !== 'loading') m.full = f3dLevel(key, 'full', 1024);
  return m;
}
function f3dReadyLevel(key){
  if(F3D.off || !f3dInit()) return null;
  const m = f3dModel(key);
  if(m.full && m.full.state === 'ready') return m.full;
  return m.lo.state === 'ready' ? m.lo : null;
}
function f3dMat(e, x, y, L){
  const right = (spriteFacing(e.img) === 'right') !== !!e.flip;
  const yaw = right ? Math.PI/2 : -Math.PI/2;
  const img = IMGS[e.img], w = img ? img.width*e.sc : 100;
  const s = w/Math.max(0.01, L.head.size[2]/L.head.ext);
  const a = -(e.ang||0), ca = Math.cos(a), sa = Math.sin(a), cy = Math.cos(yaw), sy = Math.sin(yaw);
  // translate * rotZ(a) * rotY(yaw) * scale, column-major
  return new Float32Array([
    s*ca*cy, s*sa*cy, -s*sy, 0,
    -s*sa,   s*ca,    0,     0,
    s*ca*sy, s*sa*sy, s*cy,  0,
    x,       -y,      0,     1]);
}
function f3dVP(){
  const D = (H/2)/Math.tan(F3D_FOV/2), asp = W/H, f = 1/Math.tan(F3D_FOV/2);
  const near = D*0.3, far = D*3, nf = 1/(near - far);
  const P = [f/asp,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0];
  const ex = W/2, ey = -H/2;
  // camera at (ex, ey, D) looking down -z: the view only moves the world
  const Vw = [1,0,0,0, 0,1,0,0, 0,0,1,0, -ex,-ey,-D,1];
  const o = new Float32Array(16);
  for(let c = 0; c < 4; c++) for(let r = 0; r < 4; r++){
    let s = 0; for(let k = 0; k < 4; k++) s += P[k*4+r]*Vw[c*4+k]; o[c*4+r] = s;
  }
  return {vp: o, eye: [ex, ey, D]};
}
// Draws the given ships into the field canvas and copies it into the
// field. items: {e, L, x, y, a (alpha), clip (screen half-plane or null)}.
function f3dRender(items){
  const gl = F3D.gl, can = F3D.can, loc = F3D.loc;
  const pw = (typeof CVS !== 'undefined' && CVS.width) || Math.round(W), ph = (typeof CVS !== 'undefined' && CVS.height) || Math.round(H);
  if(can.width !== pw || can.height !== ph){ can.width = pw; can.height = ph; }
  gl.viewport(0, 0, pw, ph);
  gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST); gl.enable(gl.CULL_FACE); gl.cullFace(gl.BACK);
  gl.useProgram(F3D.prog);
  const cam = f3dVP();
  gl.uniformMatrix4fv(loc.uVP, false, cam.vp);
  gl.uniform3fv(loc.uCam, cam.eye);
  gl.uniform3fv(loc.uL1, f3dNorm(F3D_L1)); gl.uniform3fv(loc.uL2, f3dNorm(F3D_L2));
  gl.uniform1i(loc.tC, 0); gl.uniform1i(loc.tN, 1); gl.uniform1i(loc.tG, 2);
  for(const it of items){
    const L = it.L;
    gl.uniformMatrix4fv(loc.uM, false, f3dMat(it.e, it.x, it.y, L));
    gl.uniform1f(loc.uA, it.a);
    // the clip of a ship sliding through her vortex (fsWarpClip), in the
    // field's own units with y turned up
    if(it.clip){ const c = it.clip; gl.uniform3f(loc.uClip, c.sg*c.fx, -c.sg*c.fy, -c.sg*(c.px*c.fx + c.py*c.fy)); }
    else gl.uniform3f(loc.uClip, 0, 0, 1);
    if(it.a < 1){ gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); } else gl.disable(gl.BLEND);
    for(const p of L.parts){
      const tx = L.tex[p.tex] || {};
      const kind = p.kind === 'tex' && tx.c ? 0 : (p.kind === 'glass' ? 2 : 1);
      gl.uniform1f(loc.uKind, kind);
      gl.uniform1f(loc.uHasN, kind === 0 && tx.n ? 1 : 0);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tx.c || F3D.white);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, tx.n || F3D.flatN);
      gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, tx.g || F3D.black);
      gl.bindBuffer(gl.ARRAY_BUFFER, p.pos); gl.enableVertexAttribArray(loc.aP);
      gl.vertexAttribPointer(loc.aP, 3, gl.SHORT, true, 6, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, p.nrm); gl.enableVertexAttribArray(loc.aN);
      gl.vertexAttribPointer(loc.aN, 3, gl.BYTE, true, 4, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, p.uv); gl.enableVertexAttribArray(loc.aT);
      gl.vertexAttribPointer(loc.aT, 2, gl.UNSIGNED_SHORT, true, 4, 0);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, p.idx);
      gl.drawElements(gl.TRIANGLES, p.n, p.big ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT, 0);
    }
  }
  gl.disable(gl.BLEND);
  ctx.drawImage(can, 0, 0, W, H);
}
function f3dNorm(v){ const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0]/l, v[1]/l, v[2]/l]; }
// Whether a ship is drawn here this frame, and how: the same decisions the
// ship loop in draw() makes for a sprite (vortex, fade in and out).
function f3dVis(e){
  fsTrack(e);
  const g = fsWarp(e);
  if(g){
    if(!g.vis) return null;
    const out = !!g.out;
    return {x: (e.x|0) + g.dx, y: (e.y|0) + g.dy, a: 1, g: g,
            clip: {sg: out ? -1 : 1, fx: g.fx, fy: g.fy, px: g.px, py: g.py}};
  }
  let a = 1;
  if(e.warp > 0){
    const m = e.warpMax||100, el = m - e.warp;
    if(el < m*0.40) return null;
    if(el < m*0.60) a = (el - m*0.40)/(m*0.20);
  } else if(e.warpOut > 0){
    const m = e.warpMax||100, el = m - e.warpOut;
    if(el > m*0.60) return null;
    if(el > m*0.40) a = 1 - (el - m*0.40)/(m*0.20);
  }
  return {x: e.x|0, y: e.y|0, a: a, g: null, clip: null};
}
// Called by draw() before the ship loop. Draws the vortex and thrusters of
// every 3D ship (they lie under the hull), then all the 3D hulls at once,
// and returns the set of ships the loop must not draw a sprite hull for.
function f3dFieldPass(list){
  const done = new Set();
  if(F3D.off || typeof document === 'undefined') return done;
  const items = [];
  for(const e of list){
    const key = f3dKey(e); if(!key) continue;
    const L = f3dReadyLevel(key); if(!L) continue;
    done.add(e);
    try{ drawVortexOf(e); }catch(ev){ ctx.restore(); }
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    const v = f3dVis(e); e._f3v = v;
    if(!v) continue;
    try{
      ctx.save();
      if(v.g){ fsWarpClip(v.g); ctx.translate(v.g.dx, v.g.dy); }
      else ctx.globalAlpha = v.a;
      drawThrusters(e.img, e.x|0, e.y|0, e.sc, e.flip, e.faction, v.g ? (v.g.out ? 1 : 0.6) : (e.warp > 0 ? 0.35 : 1), e.ang||0, e);
      ctx.restore();
    }catch(et){ ctx.restore(); }
    ctx.globalAlpha = 1;
    items.push({e: e, L: L, x: v.x, y: v.y, a: v.a, clip: v.clip});
  }
  if(items.length){
    try{ f3dRender(items); }catch(er){ F3D.err = String(er && er.message || er); }
  }
  return done;
}
// After the 3D hulls, in the ship loop's order: what she has taken (the
// damage marks alone, 20_render.js), then marks, bar, shields and beams.
function f3dShipTop(e){
  const v = e._f3v; if(!v) return;
  if(v.g){
    // in her vortex: the hull only, cut like the sprite would be
    ctx.save(); fsWarpClip(v.g); ctx.translate(v.g.dx, v.g.dy);
    f3dDamage(e);
    ctx.restore();
    return;
  }
  ctx.globalAlpha = v.a;
  f3dDamage(e);
  drawShipTop(e);
  ctx.globalAlpha = 1;
}
function f3dDamage(e){
  e._gl3 = true;
  try{ drawShipE(e, e.x|0, e.y|0, e.sc, e.flip, e.ang||0); }
  finally{ e._gl3 = false; }
}
