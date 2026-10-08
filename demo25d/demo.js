// FS3 2.5D draft (not part of the game).
// The play still happens in one plane (z = 0): steering, AI and hits are 2D.
// Everything is drawn in 3D: real MediaVP models, a perspective camera,
// backdrop layers at depth, MediaVP effect bitmaps. Draw order:
//   1. backdrop (nebula, sun, planet, stars, dust)
//   2. capital ships and their beams, sharing one depth buffer
//   3. depth cleared - fighters, their shots, explosions on top
// Keys: mouse flies, left button fires, C camera tilt, O flat camera,
// T makes the Hecate turn, P pause.
'use strict';
const cvs = document.getElementById('gl');
const gl = cvs.getContext('webgl', {antialias: true, alpha: false});
const HUD = document.getElementById('hud'), LOAD = document.getElementById('load');
if(!gl){ LOAD.textContent = 'WebGL is not available.'; throw new Error('no webgl'); }
const DERIV = !!gl.getExtension('OES_standard_derivatives');
gl.getExtension('OES_element_index_uint');

// ── math ─────────────────────────────────────────────────────
const V3 = {
  add: (a, b) => [a[0]+b[0], a[1]+b[1], a[2]+b[2]],
  sub: (a, b) => [a[0]-b[0], a[1]-b[1], a[2]-b[2]],
  mul: (a, s) => [a[0]*s, a[1]*s, a[2]*s],
  dot: (a, b) => a[0]*b[0]+a[1]*b[1]+a[2]*b[2],
  cross: (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]],
  len: a => Math.hypot(a[0], a[1], a[2]),
  norm: a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0]/l, a[1]/l, a[2]/l]; }
};
// column-major 4x4
function mMul(a, b){
  const o = new Float32Array(16);
  for(let c = 0; c < 4; c++) for(let r = 0; r < 4; r++){
    let s = 0; for(let k = 0; k < 4; k++) s += a[k*4+r]*b[c*4+k]; o[c*4+r] = s;
  }
  return o;
}
const mId = () => new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);
const mT = (x, y, z) => new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, x,y,z,1]);
const mS = s => new Float32Array([s,0,0,0, 0,s,0,0, 0,0,s,0, 0,0,0,1]);
const mRx = a => { const c = Math.cos(a), s = Math.sin(a); return new Float32Array([1,0,0,0, 0,c,s,0, 0,-s,c,0, 0,0,0,1]); };
const mRy = a => { const c = Math.cos(a), s = Math.sin(a); return new Float32Array([c,0,-s,0, 0,1,0,0, s,0,c,0, 0,0,0,1]); };
const mRz = a => { const c = Math.cos(a), s = Math.sin(a); return new Float32Array([c,s,0,0, -s,c,0,0, 0,0,1,0, 0,0,0,1]); };
function mPersp(fovy, asp, n, f){
  const t = 1/Math.tan(fovy/2), nf = 1/(n-f);
  return new Float32Array([t/asp,0,0,0, 0,t,0,0, 0,0,(f+n)*nf,-1, 0,0,2*f*n*nf,0]);
}
function mOrtho(w, h, n, f){
  return new Float32Array([2/w,0,0,0, 0,2/h,0,0, 0,0,-2/(f-n),0, 0,0,-(f+n)/(f-n),1]);
}
function mLook(eye, at, up){
  const z = V3.norm(V3.sub(eye, at)), x = V3.norm(V3.cross(up, z)), y = V3.cross(z, x);
  return new Float32Array([x[0],y[0],z[0],0, x[1],y[1],z[1],0, x[2],y[2],z[2],0,
    -V3.dot(x, eye), -V3.dot(y, eye), -V3.dot(z, eye), 1]);
}
const xf = (m, p) => [m[0]*p[0]+m[4]*p[1]+m[8]*p[2]+m[12], m[1]*p[0]+m[5]*p[1]+m[9]*p[2]+m[13], m[2]*p[0]+m[6]*p[1]+m[10]*p[2]+m[14]];
const xfDir = (m, p) => [m[0]*p[0]+m[4]*p[1]+m[8]*p[2], m[1]*p[0]+m[5]*p[1]+m[9]*p[2], m[2]*p[0]+m[6]*p[1]+m[10]*p[2]];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const rnd = (a, b) => a + Math.random()*(b-a);
const angWrap = a => { while(a > Math.PI) a -= 2*Math.PI; while(a < -Math.PI) a += 2*Math.PI; return a; };

// ── shaders ──────────────────────────────────────────────────
function prog(vs, fs, attrs){
  const sh = (t, s) => { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o);
    if(!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(o)); return o; };
  const p = gl.createProgram();
  gl.attachShader(p, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(p);
  if(!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
  const L = {p};
  const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
  for(let i = 0; i < n; i++){ const u = gl.getActiveUniform(p, i); L[u.name] = gl.getUniformLocation(p, u.name); }
  for(const a of attrs) L[a] = gl.getAttribLocation(p, a);
  return L;
}
// The ship shader of the game's preview, in world space with a real sun.
const SHIP = prog(
  'attribute vec3 aP; attribute vec3 aN; attribute vec2 aT;' +
  'uniform mat4 uM; uniform mat4 uVP; varying vec3 vW; varying vec3 vN; varying vec2 vT;' +
  'void main(){ vec4 w = uM*vec4(aP,1.0); vW = w.xyz; vN = mat3(uM)*aN; vT = aT*3.99994-1.0; gl_Position = uVP*w; }',
  (DERIV ? '#extension GL_OES_standard_derivatives : enable\n#define DERIV 1\n' : '') +
  'precision mediump float; varying vec3 vW; varying vec3 vN; varying vec2 vT;' +
  'uniform sampler2D tC; uniform sampler2D tN; uniform sampler2D tG;' +
  'uniform float uHasN; uniform float uKind; uniform vec3 uCam; uniform vec3 uL1; uniform vec3 uL2; uniform float uFlash;' +
  'void main(){ vec3 N = normalize(vN);' +
  '\n#ifdef DERIV\n' +
  ' if(uHasN > 0.5){ vec3 d1 = dFdx(vW), d2 = dFdy(vW); vec2 t1 = dFdx(vT), t2 = dFdy(vT);' +
  '  vec3 c2 = cross(d2, N), c1 = cross(N, d1); vec3 T = c2*t1.x + c1*t2.x; vec3 B = c2*t1.y + c1*t2.y;' +
  '  float im = inversesqrt(max(max(dot(T,T), dot(B,B)), 1e-20));' +
  '  vec2 nm = texture2D(tN, vT).rg*2.0-1.0; vec3 tn = vec3(nm, sqrt(max(0.0, 1.0-dot(nm,nm))));' +
  '  N = normalize(T*im*tn.x - B*im*tn.y + N*tn.z); }\n' +
  '\n#endif\n' +
  ' vec3 base = uKind < 0.5 ? texture2D(tC, vT).rgb : (uKind > 1.5 ? vec3(0.05,0.07,0.10) : vec3(0.30,0.30,0.32));' +
  ' vec3 V = normalize(uCam - vW);' +
  ' float d = max(dot(N, uL1), 0.0)*1.05 + max(dot(N, uL2), 0.0)*0.25;' +
  ' float s = pow(max(dot(N, normalize(uL1+V)), 0.0), uKind > 1.5 ? 60.0 : 24.0)*(uKind > 1.5 ? 0.9 : 0.35);' +
  ' vec3 col = base*(0.16 + d*1.25) + vec3(s)*vec3(1.0,0.95,0.85);' +
  ' if(uKind < 0.5) col += texture2D(tG, vT).rgb;' +
  ' gl_FragColor = vec4(col + vec3(uFlash), 1.0); }',
  ['aP', 'aN', 'aT']);
// Textured quads: center + u axis + v axis. Additive.
const SPR = prog(
  'attribute vec2 aC; uniform vec3 uO; uniform vec3 uU; uniform vec3 uV; uniform mat4 uVP;' +
  'uniform vec2 uUVs; uniform vec2 uUVo; varying vec2 vT;' +
  'void main(){ vT = (aC*0.5+0.5)*uUVs + uUVo; gl_Position = uVP*vec4(uO + aC.x*uU + aC.y*uV, 1.0); }',
  'precision mediump float; varying vec2 vT; uniform sampler2D tX; uniform vec4 uCol;' +
  'void main(){ vec4 t = texture2D(tX, vT); gl_FragColor = vec4(t.rgb*uCol.rgb*uCol.a, t.a*uCol.a); }',
  ['aC']);
// Stars and dust.
const PTS = prog(
  'attribute vec3 aP; attribute float aB; uniform mat4 uVP; uniform float uPx; varying float vB;' +
  'void main(){ gl_Position = uVP*vec4(aP,1.0); gl_PointSize = uPx*(0.6+aB*1.4); vB = aB; }',
  'precision mediump float; varying float vB; uniform vec3 uCol;' +
  'void main(){ vec2 d = gl_PointCoord-0.5; float a = smoothstep(0.5, 0.0, length(d)); gl_FragColor = vec4(uCol*vB*a, 1.0); }',
  ['aP', 'aB']);

const QUAD = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, QUAD);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);

// ── loading ──────────────────────────────────────────────────
function tex(url, opt){
  opt = opt || {};
  return new Promise(res => {
    const im = new Image();
    im.onload = () => {
      const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
      const pot = !(im.width & (im.width-1)) && !(im.height & (im.height-1));
      if(pot){ gl.generateMipmap(gl.TEXTURE_2D); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); }
      else gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      const wrap = (opt.repeat && pot) ? gl.REPEAT : gl.CLAMP_TO_EDGE;
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wrap);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      res(t);
    };
    im.onerror = () => res(null);
    im.src = url;
  });
}
function px(r, g, b){
  const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([r, g, b, 255]));
  return t;
}
const WHITE = px(160, 160, 160), BLACK = px(0, 0, 0), FLATN = px(128, 128, 255);
async function loadModel(key){
  const base = 'm/' + key + '/';
  const [buf, meta] = await Promise.all([fetch(base + 'model.bin').then(r => r.arrayBuffer()), fetch(base + 'meta.json').then(r => r.json())]);
  const hl = new DataView(buf).getUint32(0, true);
  const head = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 4, hl)));
  const data = buf.slice(4 + hl);
  const mk = (target, from, bytes) => { const b = gl.createBuffer(); gl.bindBuffer(target, b);
    gl.bufferData(target, new Uint8Array(data, from, bytes), gl.STATIC_DRAW); return b; };
  const parts = head.parts.map(p => ({kind: p.kind, tex: (p.tex||'').toLowerCase(), n: p.ni, big: p.big,
    pos: mk(gl.ARRAY_BUFFER, p.pos, p.nv*6), nrm: mk(gl.ARRAY_BUFFER, p.nrm, p.nv*4),
    uv: mk(gl.ARRAY_BUFFER, p.uv, p.nv*4), idx: mk(gl.ELEMENT_ARRAY_BUFFER, p.idx, p.ni*(p.big?4:2))}));
  const texs = {};
  const jobs = [];
  for(const t in meta.tex){ texs[t] = {}; for(const k of meta.tex[t]) jobs.push(tex(base + t + '_' + k + '.webp').then(x => { texs[t][k] = x; })); }
  await Promise.all(jobs);
  return {key, parts, texs, meta, head};
}
const FX = {};
async function loadFx(){
  const one = (n, o) => tex('fx/' + n + '.webp', o).then(t => { FX[n] = t; });
  const names = ['boltpromS1grn', 'boltpromS1glow', 'laserglow01', 'bgreencore', 'bgreenhaze1', 'greenbeam2glow',
    'aaabeamaa', 'aaabeamab', 'aaabeamaglow', 'flareharpoon1orn', 'trailharpoon1vrm'].map(s => s.toLowerCase());
  const jobs = names.map(n => one(n, {repeat: /beam|core|haze|trail/.test(n)}));
  FX.exp = []; for(let i = 0; i <= 48; i += 4) jobs.push(tex('fx/exp04_' + String(i).padStart(4, '0') + '.webp').then(t => { FX.exp[i/4] = t; }));
  FX.hit = []; for(let i = 0; i < 8; i += 2) jobs.push(tex('fx/flashhitproms1grn_000' + i + '.webp').then(t => { FX.hit[i/2] = t; }));
  FX.muz = []; for(const i of [0, 4]) jobs.push(tex('fx/flashmuzproms1grn_000' + i + '.webp').then(t => { FX.muz.push(t); }));
  jobs.push(tex('fx/neb.jpg').then(t => { FX.neb = t; }));
  jobs.push(tex('fx/planet.webp').then(t => { FX.planet = t; }));
  jobs.push(tex('fx/sun.webp').then(t => { FX.sun = t; }));
  await Promise.all(jobs);
}

// ── scene ────────────────────────────────────────────────────
const SUN = [-5200, 2600, -9000];
// the key light comes from the sun's side but in front of the ships, so
// the flank the player sees is lit (FreeSpace cheats the same way)
const L1 = V3.norm([-0.55, 0.45, 0.70]), L2 = V3.norm([0.7, -0.3, 0.5]);
const BOUND = {x: 1700, y: 760};
let MODELS = {};
let ships = [], bolts = [], beams = [], fxs = [];
let player;
const CAM = {x: 0, y: 0, lift: 220, tilt: 1, ortho: false, dist: 1200};
const TILTS = [0, 220, 520];

// A ship: position in the plane, heading, the yaw that decides which flank
// faces the camera, a bank roll, and its picture length in world units.
function mkShip(o){
  const m = MODELS[o.model], sz = m.meta.size, ext = m.meta.ext;
  const s = o.len * ext / sz[2];
  return Object.assign({vx: 0, vy: 0, h: 0, yaw: Math.PI/2, yawT: Math.PI/2, roll: 0, flash: 0, hp: 6, dead: 0,
    cool: 0, scale: s, half: o.len/2, height: o.len * sz[1]/sz[2] / 2, depth: o.len * sz[0]/sz[2] / 2}, o);
}
// model matrix: plane position, climb in the plane, yaw about the ship's
// vertical axis, bank about its length, scale
function shipM(sh){
  const side = Math.sin(sh.yaw);
  const elev = sh.cap ? 0 : clamp(Math.atan2(Math.sin(sh.h), Math.abs(Math.cos(sh.h))), -1.1, 1.1);
  let m = mT(sh.x, sh.y, sh.z || 0);
  m = mMul(m, mRz(elev*side));
  m = mMul(m, mRy(sh.yaw));
  m = mMul(m, mRz(sh.roll));
  m = mMul(m, mS(sh.scale));
  return m;
}

function setupScene(){
  ships = [];
  ships.push(mkShip({model: 'deorionright', cap: true, team: 0, x: -720, y: -230, z: 0, len: 820, speed: 5, yaw: Math.PI/2, yawT: Math.PI/2, name: 'GTD Orion'}));
  ships.push(mkShip({model: 'dehecate', cap: true, team: 1, x: 880, y: 210, z: 0, len: 760, speed: 5, yaw: -Math.PI/2, yawT: -Math.PI/2, name: 'NTF Hecate', turnEvery: 34, turnT: 18}));
  player = mkShip({model: 'fimyrmidon', team: 0, x: -200, y: 60, len: 34, speed: 330, player: true});
  ships.push(player);
  ships.push(mkShip({model: 'fiperseus', team: 0, x: -320, y: -40, len: 36, speed: 300, ai: true}));
  for(let i = 0; i < 3; i++) ships.push(mkShip({model: 'fiherc', team: 1, x: 600 + i*90, y: -120 + i*120, len: 40, speed: 280, ai: true, yaw: -Math.PI/2, yawT: -Math.PI/2, h: Math.PI}));
}

// ── input ────────────────────────────────────────────────────
const MOUSE = {x: 0, y: 0, down: false, wx: 0, wy: 0};
let paused = false;
cvs.addEventListener('mousemove', e => { MOUSE.x = e.clientX; MOUSE.y = e.clientY; });
cvs.addEventListener('mousedown', e => { if(e.button === 0) MOUSE.down = true; });
window.addEventListener('mouseup', e => { if(e.button === 0) MOUSE.down = false; });
window.addEventListener('keydown', e => {
  if(e.code === 'KeyC'){ CAM.tilt = (CAM.tilt+1) % TILTS.length; }
  if(e.code === 'KeyO'){ CAM.ortho = !CAM.ortho; }
  if(e.code === 'KeyT'){ const h = ships[1]; if(h && h.yaw === h.yawT) h.yawT = -h.yawT; }
  if(e.code === 'KeyP'){ paused = !paused; }
});

// ── simulation ───────────────────────────────────────────────
function fighterFly(sh, tx, ty, dt, throttle){
  if(!(dt > 0)) return;
  const want = Math.atan2(ty - sh.y, tx - sh.x);
  const d = angWrap(want - sh.h), rate = 3.2;
  const turn = clamp(d, -rate*dt, rate*dt);
  sh.h = angWrap(sh.h + turn);
  sh.roll += (clamp(-turn/dt*0.32, -1.0, 1.0) - sh.roll)*Math.min(1, dt*5);
  const sp = sh.speed*throttle;
  sh.vx += (Math.cos(sh.h)*sp - sh.vx)*Math.min(1, dt*3);
  sh.vy += (Math.sin(sh.h)*sp - sh.vy)*Math.min(1, dt*3);
  // the flank shown follows the direction of flight, with some hysteresis
  const c = Math.cos(sh.h);
  if(c > 0.25) sh.yawT = Math.PI/2; else if(c < -0.25) sh.yawT = -Math.PI/2;
}
function gunPoints(sh, M){
  const g = MODELS[sh.model].meta.guns;
  const pts = (g && g[0] && g[0].length) ? g[0] : [[0, 0, 0.9]];
  return pts.map(p => xf(M, p));
}
function fire(sh, M){
  const fwd = xfDir(M, [0, 0, 1]); const f2 = V3.norm([fwd[0], fwd[1], 0]);
  for(const p of gunPoints(sh, M)){
    bolts.push({x: p[0], y: p[1], z: p[2], vx: f2[0]*950 + sh.vx, vy: f2[1]*950 + sh.vy, t: 0, life: 1.4, team: sh.team});
    fxs.push({kind: 'muz', x: p[0], y: p[1], z: p[2], t: 0, life: 0.08, size: 26, team: sh.team});
  }
}
function capHit(c, x, y){
  // hull as an ellipse in the plane; it narrows while she turns
  const along = c.half*Math.abs(Math.sin(c.yaw)) + c.depth*Math.abs(Math.cos(c.yaw));
  const dx = (x - c.x)/along, dy = (y - c.y)/(c.height*0.9);
  return dx*dx + dy*dy < 1;
}
function explode(x, y, z, size){ fxs.push({kind: 'exp', x, y, z, t: 0, life: 1.2, size}); }

function step(dt){
  // world point under the pointer: the ray from the camera onto z = 0
  const w = screenToPlane(MOUSE.x, MOUSE.y); MOUSE.wx = w[0]; MOUSE.wy = w[1];
  for(const sh of ships){
    if(sh.dead > 0){ sh.dead -= dt; if(sh.dead <= 0) respawn(sh); continue; }
    if(sh.cap){
      sh.x += Math.sin(sh.yaw)*sh.speed*dt;
      if(sh.turnEvery){ sh.turnT -= dt; if(sh.turnT <= 0){ sh.turnT = sh.turnEvery; sh.yawT = -sh.yawT; } }
    } else if(sh.player){
      const d = Math.hypot(MOUSE.wx - sh.x, MOUSE.wy - sh.y);
      fighterFly(sh, MOUSE.wx, MOUSE.wy, dt, clamp(d/220, 0.15, 1));
    } else {
      // pick the nearest enemy fighter, keep a little off it
      let best = null, bd = 1e9;
      for(const o of ships) if(!o.cap && !o.dead && o.team !== sh.team){ const d = Math.hypot(o.x-sh.x, o.y-sh.y); if(d < bd){ bd = d; best = o; } }
      sh.tgt = best;
      if(best){
        const lead = bd/950;
        const tx = best.x + best.vx*lead, ty = best.y + best.vy*lead;
        fighterFly(sh, tx + Math.sin(performance.now()/900 + sh.x)*60, ty, dt, bd < 140 ? 0.6 : 1);
        const a = Math.abs(angWrap(Math.atan2(ty - sh.y, tx - sh.x) - sh.h));
        sh.cool -= dt;
        if(a < 0.12 && bd < 650 && sh.cool <= 0){ sh.cool = 0.35; fire(sh, shipM(sh)); }
      }
    }
    // the yaw turn: slow and heavy for capitals, quick for fighters
    const yr = sh.cap ? Math.PI/9 : Math.PI/0.55;
    if(sh.yaw !== sh.yawT){
      const d = sh.yawT - sh.yaw;
      sh.yaw = Math.abs(d) <= yr*dt ? sh.yawT : sh.yaw + Math.sign(d)*yr*dt;
    }
    if(!sh.cap){
      sh.x += sh.vx*dt; sh.y += sh.vy*dt;
      sh.x = clamp(sh.x, -BOUND.x, BOUND.x); sh.y = clamp(sh.y, -BOUND.y, BOUND.y);
    }
    sh.flash = Math.max(0, sh.flash - dt*4);
  }
  // the player's guns
  player.cool -= dt;
  if(MOUSE.down && player.cool <= 0 && !player.dead){ player.cool = 0.16; fire(player, shipM(player)); }
  // bolts
  for(const b of bolts){
    b.t += dt; b.x += b.vx*dt; b.y += b.vy*dt;
    for(const sh of ships){
      if(sh.dead || sh.team === b.team || b.t > b.life) continue;
      const hit = sh.cap ? capHit(sh, b.x, b.y) : Math.hypot(sh.x - b.x, sh.y - b.y) < sh.half*0.8;
      if(hit){
        b.t = b.life + 1; sh.flash = 0.35;
        fxs.push({kind: 'hit', x: b.x, y: b.y, z: sh.cap ? sh.depth*0.6 : 2, t: 0, life: 0.25, size: sh.cap ? 60 : 40});
        if(!sh.cap && !sh.player){ sh.hp--; if(sh.hp <= 0){ explode(sh.x, sh.y, 0, 170); sh.dead = 3; } }
      }
    }
  }
  bolts = bolts.filter(b => b.t < b.life);
  // capital beams: heavy ones ship to ship, anti-fighter ones at fighters
  for(const c of ships){
    if(!c.cap) continue;
    c.beamT = (c.beamT || rnd(2, 5)) - dt;
    c.aaaT = (c.aaaT || rnd(1, 3)) - dt;
    const foe = ships.find(o => o.cap && o.team !== c.team);
    const M = shipM(c);
    if(c.beamT <= 0 && foe){
      c.beamT = rnd(6, 9);
      const tur = bigTurrets(c);
      if(tur.length){
        const t = tur[Math.floor(Math.random()*tur.length)];
        beams.push({ship: c, tur: t, kind: 'heavy', target: foe, off: rnd(-0.45, 0.45), t: 0, life: 3.2});
      }
    }
    if(c.aaaT <= 0){
      c.aaaT = rnd(2.5, 4.5);
      const tgt = ships.filter(o => !o.cap && !o.dead && o.team !== c.team && Math.hypot(o.x-c.x, o.y-c.y) < 950);
      const tur = smallTurrets(c);
      if(tgt.length && tur.length) beams.push({ship: c, tur: tur[Math.floor(Math.random()*tur.length)], kind: 'aaa', target: tgt[0], t: 0, life: 1.1});
    }
  }
  for(const bm of beams){
    bm.t += dt;
    if(bm.kind === 'aaa' && bm.t > 0.6 && bm.target && !bm.target.dead && !bm.target.player && !bm.hit){
      bm.hit = true; bm.target.hp -= 3; bm.target.flash = 0.5;
      if(bm.target.hp <= 0){ explode(bm.target.x, bm.target.y, 0, 170); bm.target.dead = 3; }
    }
  }
  beams = beams.filter(b => b.t < b.life);
  for(const f of fxs) f.t += dt;
  fxs = fxs.filter(f => f.t < f.life);
}
function respawn(sh){
  sh.hp = 6; sh.dead = 0;
  sh.x = sh.team ? BOUND.x - 50 : -BOUND.x + 50; sh.y = rnd(-400, 400);
  sh.h = sh.team ? Math.PI : 0; sh.yaw = sh.yawT = sh.team ? -Math.PI/2 : Math.PI/2; sh.vx = sh.vy = 0;
}
function bigTurrets(c){
  if(!c._big){ const t = MODELS[c.model].meta.turrets.slice().sort((a, b) => b.big - a.big); c._big = t.slice(0, 4); }
  return c._big;
}
function smallTurrets(c){
  if(!c._small){ const t = MODELS[c.model].meta.turrets.slice().sort((a, b) => a.big - b.big); c._small = t.slice(0, Math.max(1, t.length >> 1)); }
  return c._small;
}

// ── camera ───────────────────────────────────────────────────
let VP = mId(), EYE = [0, 0, 1000], VIEWM = mId(), PROJ = mId();
function camera(dt){
  CAM.x += (player.x + player.vx*0.35 - CAM.x)*Math.min(1, dt*2.2);
  CAM.y += (player.y + player.vy*0.25 - CAM.y)*Math.min(1, dt*2.2);
  CAM.x = clamp(CAM.x, -BOUND.x + 500, BOUND.x - 500); CAM.y = clamp(CAM.y, -BOUND.y + 260, BOUND.y - 260);
  CAM.lift += (TILTS[CAM.tilt] - CAM.lift)*Math.min(1, dt*3);
  const asp = cvs.width/cvs.height;
  EYE = [CAM.x, CAM.y + CAM.lift, CAM.dist];
  VIEWM = mLook(EYE, [CAM.x, CAM.y, 0], [0, 1, 0]);
  const fov = 40*Math.PI/180;
  if(CAM.ortho){ const hh = 2*CAM.dist*Math.tan(fov/2); PROJ = mOrtho(hh*asp, hh, 10, 30000); }
  else PROJ = mPersp(fov, asp, 10, 30000);
  VP = mMul(PROJ, VIEWM);
}
function screenToPlane(sx, sy){
  const r = cvs.getBoundingClientRect();
  const nx = (sx - r.left)/r.width*2 - 1, ny = 1 - (sy - r.top)/r.height*2;
  const inv = invert(VP);
  const a = unproj(inv, nx, ny, -1), b = unproj(inv, nx, ny, 1);
  const t = a[2]/(a[2] - b[2]);
  return [a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t];
}
function unproj(inv, x, y, z){
  const v = [inv[0]*x+inv[4]*y+inv[8]*z+inv[12], inv[1]*x+inv[5]*y+inv[9]*z+inv[13], inv[2]*x+inv[6]*y+inv[10]*z+inv[14], inv[3]*x+inv[7]*y+inv[11]*z+inv[15]];
  return [v[0]/v[3], v[1]/v[3], v[2]/v[3]];
}
function invert(m){
  const inv = new Float32Array(16);
  inv[0] = m[5]*m[10]*m[15]-m[5]*m[11]*m[14]-m[9]*m[6]*m[15]+m[9]*m[7]*m[14]+m[13]*m[6]*m[11]-m[13]*m[7]*m[10];
  inv[4] = -m[4]*m[10]*m[15]+m[4]*m[11]*m[14]+m[8]*m[6]*m[15]-m[8]*m[7]*m[14]-m[12]*m[6]*m[11]+m[12]*m[7]*m[10];
  inv[8] = m[4]*m[9]*m[15]-m[4]*m[11]*m[13]-m[8]*m[5]*m[15]+m[8]*m[7]*m[13]+m[12]*m[5]*m[11]-m[12]*m[7]*m[9];
  inv[12] = -m[4]*m[9]*m[14]+m[4]*m[10]*m[13]+m[8]*m[5]*m[14]-m[8]*m[6]*m[13]-m[12]*m[5]*m[10]+m[12]*m[6]*m[9];
  inv[1] = -m[1]*m[10]*m[15]+m[1]*m[11]*m[14]+m[9]*m[2]*m[15]-m[9]*m[3]*m[14]-m[13]*m[2]*m[11]+m[13]*m[3]*m[10];
  inv[5] = m[0]*m[10]*m[15]-m[0]*m[11]*m[14]-m[8]*m[2]*m[15]+m[8]*m[3]*m[14]+m[12]*m[2]*m[11]-m[12]*m[3]*m[10];
  inv[9] = -m[0]*m[9]*m[15]+m[0]*m[11]*m[13]+m[8]*m[1]*m[15]-m[8]*m[3]*m[13]-m[12]*m[1]*m[11]+m[12]*m[3]*m[9];
  inv[13] = m[0]*m[9]*m[14]-m[0]*m[10]*m[13]-m[8]*m[1]*m[14]+m[8]*m[2]*m[13]+m[12]*m[1]*m[10]-m[12]*m[2]*m[9];
  inv[2] = m[1]*m[6]*m[15]-m[1]*m[7]*m[14]-m[5]*m[2]*m[15]+m[5]*m[3]*m[14]+m[13]*m[2]*m[7]-m[13]*m[3]*m[6];
  inv[6] = -m[0]*m[6]*m[15]+m[0]*m[7]*m[14]+m[4]*m[2]*m[15]-m[4]*m[3]*m[14]-m[12]*m[2]*m[7]+m[12]*m[3]*m[6];
  inv[10] = m[0]*m[5]*m[15]-m[0]*m[7]*m[13]-m[4]*m[1]*m[15]+m[4]*m[3]*m[13]+m[12]*m[1]*m[7]-m[12]*m[3]*m[5];
  inv[14] = -m[0]*m[5]*m[14]+m[0]*m[6]*m[13]+m[4]*m[1]*m[14]-m[4]*m[2]*m[13]-m[12]*m[1]*m[6]+m[12]*m[2]*m[5];
  inv[3] = -m[1]*m[6]*m[11]+m[1]*m[7]*m[10]+m[5]*m[2]*m[11]-m[5]*m[3]*m[10]-m[9]*m[2]*m[7]+m[9]*m[3]*m[6];
  inv[7] = m[0]*m[6]*m[11]-m[0]*m[7]*m[10]-m[4]*m[2]*m[11]+m[4]*m[3]*m[10]+m[8]*m[2]*m[7]-m[8]*m[3]*m[6];
  inv[11] = -m[0]*m[5]*m[11]+m[0]*m[7]*m[9]+m[4]*m[1]*m[11]-m[4]*m[3]*m[9]-m[8]*m[1]*m[7]+m[8]*m[3]*m[5];
  inv[15] = m[0]*m[5]*m[10]-m[0]*m[6]*m[9]-m[4]*m[1]*m[10]+m[4]*m[2]*m[9]+m[8]*m[1]*m[6]-m[8]*m[2]*m[5];
  let det = m[0]*inv[0]+m[1]*inv[4]+m[2]*inv[8]+m[3]*inv[12]; det = det ? 1/det : 0;
  for(let i = 0; i < 16; i++) inv[i] *= det;
  return inv;
}

// ── drawing ──────────────────────────────────────────────────
function drawShip(sh){
  const m = MODELS[sh.model], M = shipM(sh);
  gl.useProgram(SHIP.p);
  gl.uniformMatrix4fv(SHIP.uM, false, M); gl.uniformMatrix4fv(SHIP.uVP, false, VP);
  gl.uniform3fv(SHIP.uCam, EYE); gl.uniform3fv(SHIP.uL1, L1); gl.uniform3fv(SHIP.uL2, L2);
  gl.uniform1f(SHIP.uFlash, sh.flash*0.35);
  gl.uniform1i(SHIP.tC, 0); gl.uniform1i(SHIP.tN, 1); gl.uniform1i(SHIP.tG, 2);
  for(const p of m.parts){
    const tx = m.texs[p.tex] || {};
    const kind = p.kind === 'tex' && tx.c ? 0 : (p.kind === 'glass' ? 2 : 1);
    gl.uniform1f(SHIP.uKind, kind);
    gl.uniform1f(SHIP.uHasN, kind === 0 && tx.n ? 1 : 0);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tx.c || WHITE);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, tx.n || FLATN);
    gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, tx.g || BLACK);
    gl.bindBuffer(gl.ARRAY_BUFFER, p.pos); gl.enableVertexAttribArray(SHIP.aP); gl.vertexAttribPointer(SHIP.aP, 3, gl.SHORT, true, 6, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, p.nrm); gl.enableVertexAttribArray(SHIP.aN); gl.vertexAttribPointer(SHIP.aN, 3, gl.BYTE, true, 4, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, p.uv); gl.enableVertexAttribArray(SHIP.aT); gl.vertexAttribPointer(SHIP.aT, 2, gl.UNSIGNED_SHORT, true, 4, 0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, p.idx);
    gl.drawElements(gl.TRIANGLES, p.n, p.big ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT, 0);
  }
  gl.disableVertexAttribArray(SHIP.aP); gl.disableVertexAttribArray(SHIP.aN); gl.disableVertexAttribArray(SHIP.aT);
  return M;
}
// camera-facing axes for billboards
function camAxes(){ return [[VIEWM[0], VIEWM[4], VIEWM[8]], [VIEWM[1], VIEWM[5], VIEWM[9]], [VIEWM[2], VIEWM[6], VIEWM[10]]]; }
function sprBegin(){
  gl.useProgram(SPR.p);
  gl.uniformMatrix4fv(SPR.uVP, false, VP);
  gl.bindBuffer(gl.ARRAY_BUFFER, QUAD); gl.enableVertexAttribArray(SPR.aC); gl.vertexAttribPointer(SPR.aC, 2, gl.FLOAT, false, 0, 0);
  gl.activeTexture(gl.TEXTURE0); gl.uniform1i(SPR.tX, 0);
  gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE); gl.depthMask(false);
}
function spr(t, o, u, v, col, uvs, uvo){
  if(!t) return;
  gl.bindTexture(gl.TEXTURE_2D, t);
  gl.uniform3fv(SPR.uO, o); gl.uniform3fv(SPR.uU, u); gl.uniform3fv(SPR.uV, v);
  gl.uniform4fv(SPR.uCol, col || [1, 1, 1, 1]);
  gl.uniform2fv(SPR.uUVs, uvs || [1, 1]); gl.uniform2fv(SPR.uUVo, uvo || [0, 0]);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}
function bill(t, p, size, col){ const [R, U] = camAxes(); spr(t, p, V3.mul(R, size), V3.mul(U, size), col); }
// a quad from a to b, w wide, turned to face the camera
function streak(t, a, b, w, col, uvs, uvo){
  const d = V3.sub(b, a), mid = V3.mul(V3.add(a, b), 0.5);
  const toCam = V3.norm(V3.sub(EYE, mid));
  const side = V3.norm(V3.cross(d, toCam));
  spr(t, mid, V3.mul(d, 0.5), V3.mul(side, w/2), col, uvs, uvo);
}
let STAR = null, DUST = null;
function mkPoints(n, box, bright){
  const a = new Float32Array(n*4);
  for(let i = 0; i < n; i++){
    a[i*4] = rnd(box[0], box[1]); a[i*4+1] = rnd(box[2], box[3]); a[i*4+2] = rnd(box[4], box[5]);
    a[i*4+3] = Math.pow(Math.random(), 2.2)*bright;
  }
  const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, a, gl.STATIC_DRAW);
  return {b, n};
}
function drawPoints(P, pxs, col){
  gl.useProgram(PTS.p); gl.uniformMatrix4fv(PTS.uVP, false, VP);
  gl.uniform1f(PTS.uPx, pxs); gl.uniform3fv(PTS.uCol, col);
  gl.bindBuffer(gl.ARRAY_BUFFER, P.b);
  gl.enableVertexAttribArray(PTS.aP); gl.vertexAttribPointer(PTS.aP, 3, gl.FLOAT, false, 16, 0);
  gl.enableVertexAttribArray(PTS.aB); gl.vertexAttribPointer(PTS.aB, 1, gl.FLOAT, false, 16, 12);
  gl.drawArrays(gl.POINTS, 0, P.n);
  gl.disableVertexAttribArray(PTS.aP); gl.disableVertexAttribArray(PTS.aB);
}
function thrusterGlows(sh, M, t){
  const g = MODELS[sh.model].meta.thrusters;
  const pulse = 0.85 + 0.15*Math.sin(t*23 + sh.x);
  for(const th of g){
    const p = xf(M, th.pos);
    bill(FX.laserglow01, p, Math.max(4, th.rad*sh.scale*2.6)*pulse, [0.55, 0.75, 1.0, 0.9]);
  }
}
function drawBeams(t){
  for(const bm of beams){
    const c = bm.ship, M = shipM(c);
    const src = xf(M, bm.tur.points[0] || bm.tur.pos);
    const tg = bm.target;
    let end;
    if(tg.cap){ end = [tg.x + bm.off*tg.half*Math.sin(tg.yaw), tg.y + rnd(-0.1, 0.1)*tg.height, tg.depth*0.4]; }
    else end = [tg.x, tg.y, 0];
    const k = bm.t/bm.life;
    const ramp = bm.kind === 'heavy' ? clamp(Math.min(bm.t/0.5, (bm.life - bm.t)/0.4), 0, 1) : clamp(Math.min(bm.t/0.15, (bm.life - bm.t)/0.15), 0, 1);
    const len = V3.len(V3.sub(end, src));
    if(bm.kind === 'heavy'){
      streak(FX.bgreenhaze1, src, end, 70*ramp, [0.6, 1, 0.6, 0.8], [len/260, 1], [-t*1.6, 0]);
      streak(FX.bgreencore, src, end, 30*ramp, [1, 1, 1, 1], [len/200, 1], [-t*2.4, 0]);
      bill(FX.greenbeam2glow, src, 55*ramp, [1, 1, 1, 1]);
      if(ramp > 0.5 && Math.random() < 0.5) fxs.push({kind: 'exp', x: end[0] + rnd(-12, 12), y: end[1] + rnd(-12, 12), z: end[2], t: 0, life: 0.8, size: rnd(50, 90)});
    } else {
      streak(FX.aaabeamab, src, end, 14*ramp, [0.6, 0.8, 1, 1], [len/180, 1], [-t*3, 0]);
      streak(FX.aaabeamaa, src, end, 7*ramp, [1, 1, 1, 1], [len/120, 1], [-t*4, 0]);
      bill(FX.aaabeamaglow, src, 22*ramp, [0.7, 0.85, 1, 1]);
    }
  }
}
function drawFx(layerCap){
  for(const f of fxs){
    const k = f.t/f.life, p = [f.x, f.y, f.z || 0];
    if(f.kind === 'exp'){ const fr = FX.exp[Math.min(FX.exp.length - 1, Math.floor(k*FX.exp.length))]; bill(fr, p, f.size*(0.7 + 0.5*k), [1, 1, 1, 1]); }
    if(f.kind === 'hit'){ const fr = FX.hit[Math.min(FX.hit.length - 1, Math.floor(k*FX.hit.length))]; bill(fr, p, f.size, f.team ? [1, 0.4, 0.3, 1] : [1, 1, 1, 1]); }
    if(f.kind === 'muz'){ bill(FX.muz[k < 0.5 ? 0 : 1], p, f.size, f.team ? [1, 0.4, 0.3, 1] : [1, 1, 1, 1]); }
  }
}
function drawBolts(){
  for(const b of bolts){
    const d = V3.norm([b.vx, b.vy, 0]);
    const a = [b.x - d[0]*24, b.y - d[1]*24, b.z], e = [b.x + d[0]*24, b.y + d[1]*24, b.z];
    if(b.team){ streak(FX.laserglow01, a, e, 16, [1, 0.25, 0.15, 1]); streak(FX.laserglow01, a, e, 6, [1, 0.8, 0.6, 1]); }
    else { streak(FX.boltproms1glow, a, e, 30, [1, 1, 1, 0.8]); streak(FX.boltproms1grn, a, e, 26, [1, 1, 1, 1]); }
  }
}
function drawBackdrop(){
  gl.disable(gl.DEPTH_TEST); gl.depthMask(false);
  // nebula far behind: it barely moves
  gl.useProgram(SPR.p); sprBegin();
  gl.blendFunc(gl.ONE, gl.ZERO);
  spr(FX.neb, [0, 0, -14000], [15000, 0, 0], [0, 8400, 0], [0.55, 0.55, 0.62, 1]);
  gl.blendFunc(gl.ONE, gl.ONE);
  drawPoints(STAR, 2.2*DPR, [1, 1, 1]);
  sprBegin();
  spr(FX.sun, SUN, [1600, 0, 0], [0, 1600, 0], [1, 0.95, 0.85, 1]);
  // planet: drawn as a lit disc, not additive
  gl.useProgram(SPR.p); sprBegin();
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  spr(FX.planet, [3600, 1500, -9500], [1250, 0, 0], [0, 1250, 0], [0.9, 0.9, 0.95, 1]);
  gl.blendFunc(gl.ONE, gl.ONE);
  drawPoints(DUST, 1.6*DPR, [0.55, 0.6, 0.7]);
}

// ── frame ────────────────────────────────────────────────────
let DPR = 1, last = 0, fps = 0, fpsT = 0, fpsN = 0;
function resize(){
  DPR = Math.min(2, window.devicePixelRatio || 1);
  const w = Math.round(cvs.clientWidth*DPR), h = Math.round(cvs.clientHeight*DPR);
  if(cvs.width !== w || cvs.height !== h){ cvs.width = w; cvs.height = h; }
}
function frame(now){
  requestAnimationFrame(frame);
  const dt = last ? Math.min(0.05, (now - last)/1000) : 0; last = now;
  fpsT += dt; fpsN++; if(fpsT > 0.5){ fps = Math.round(fpsN/fpsT); fpsT = 0; fpsN = 0; }
  resize();
  if(!paused && dt > 0) step(dt);
  camera(dt);
  const t = now/1000;
  gl.viewport(0, 0, cvs.width, cvs.height);
  gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  drawBackdrop();
  // layer 2: capital ships and their beams, one depth buffer
  gl.enable(gl.DEPTH_TEST); gl.depthMask(true); gl.disable(gl.BLEND);
  gl.enable(gl.CULL_FACE); gl.cullFace(gl.BACK);
  const capM = [];
  for(const sh of ships) if(sh.cap) capM.push([sh, drawShip(sh)]);
  gl.disable(gl.CULL_FACE);
  sprBegin();
  for(const [sh, M] of capM) thrusterGlows(sh, M, t);
  drawBeams(t);
  // layer 3: fighters, their shots and every flash, above the capitals
  gl.depthMask(true); gl.clear(gl.DEPTH_BUFFER_BIT); gl.disable(gl.BLEND);
  gl.enable(gl.CULL_FACE);
  const fM = [];
  for(const sh of ships) if(!sh.cap && !sh.dead) fM.push([sh, drawShip(sh)]);
  gl.disable(gl.CULL_FACE);
  sprBegin();
  for(const [sh, M] of fM) thrusterGlows(sh, M, t);
  drawBolts();
  drawFx();
  gl.depthMask(true); gl.disable(gl.BLEND);
  HUD.textContent = 'FS3  2.5D draft  -  not the game\n' +
    'mouse: fly   left button: fire\n' +
    'C: camera tilt (' + ['level', 'a little above', 'high'][CAM.tilt] + ')   O: ' + (CAM.ortho ? 'flat camera (today)' : 'perspective') + '\n' +
    'T: the Hecate turns now   P: pause\n' + fps + ' fps';
}

(async function(){
  try{
    const keys = ['deorionright', 'dehecate', 'fimyrmidon', 'fiherc', 'fiperseus'];
    let n = 0;
    await Promise.all([loadFx(), ...keys.map(k => loadModel(k).then(m => { MODELS[k] = m; LOAD.textContent = 'loading models ... ' + (++n) + ' / ' + keys.length; }))]);
    STAR = mkPoints(2600, [-16000, 16000, -9000, 9000, -11000, -3000], 1);
    DUST = mkPoints(900, [-2600, 2600, -1500, 1500, -700, 500], 0.6);
    setupScene();
    LOAD.style.display = 'none';
    requestAnimationFrame(frame);
  }catch(e){ LOAD.textContent = 'error: ' + e.message; console.error(e); }
})();
