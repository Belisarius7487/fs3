// ── 3D MODELS (v191) ─────────────────────────────────────────
// The real MediaVP models, drawn with WebGL into an offscreen canvas and
// copied onto the 2D screen like any picture. Stage 1: the ship in the
// rearm window. Files live in models/<hull>/ next to the page and are
// fetched only when a hull is first shown: lo.bin with 512 px textures,
// hi.bin with 1024 px textures once the player zooms in. Without WebGL,
// or while a model loads, the caller draws the sprite as before.
const M3D_BASE    = 'models/';
// v195: raised whenever the model files change, so neither the browser nor
// Cloudflare hands out the old ones from its cache.
const M3D_REV     = 201;
const M3D_FOV     = 30 * Math.PI / 180;
const M3D_SPIN    = 0.6;          // rad/s while the pointer is on the picture
const M3D_YAW0    = 1.22;         // at rest: starboard side, bow to the right, a little of the bow
const M3D_PITCH0  = 0.20;         // and a little from above
const M3D_ZOOM_HI = 1.4;          // from here the finer level is loaded
const M3D_ZOOM_MAX = 3.0;
// v194: only the last few hulls shown keep their buffers and textures on
// the graphics card. Going down the hangar list used to load every hull
// and keep it; when the card runs short the browser may wipe the game's
// own cached pictures (Silvio: a damaged Hatshepsut lost her hull).
const M3D_KEEP    = 4;
const M3D = {gl:null, can:null, ok:null, prog:null, deriv:false, models:{}, white:null, black:null};

function m3dInit(){
  if(M3D.ok !== null) return M3D.ok;
  M3D.ok = false;
  try{
    if(typeof document === 'undefined' || !document.createElement) return false;
    const can = document.createElement('canvas');
    // v193 (Silvio: turning and zoom looked jerky): the model canvas sits as
    // its own layer over the game canvas, so the browser composites it on
    // the GPU instead of the page copying every frame back into the 2D
    // picture. Pointer events go through it to the game below.
    const ov = !!(document.body && document.body.appendChild);
    if(ov){
      const st = can.style;
      st.position = 'fixed'; st.pointerEvents = 'none'; st.zIndex = '5'; st.display = 'none';
      st.left = '0px'; st.top = '0px';
      document.body.appendChild(can);
    }
    M3D.overlay = ov;
    const gl = can.getContext('webgl', {alpha:true, premultipliedAlpha:true, antialias:true, preserveDrawingBuffer:!ov});
    if(!gl) return false;
    // A lost context takes every buffer and texture with it: drop it all,
    // and the next picture starts over on a fresh canvas (v194).
    can.addEventListener('webglcontextlost', function(ev){
      ev.preventDefault();
      if(can.parentNode) can.parentNode.removeChild(can);
      M3D.models = {}; M3D.gl = null; M3D.can = null; M3D.ok = null; M3D.box = null;
    }, false);
    M3D.deriv = !!gl.getExtension('OES_standard_derivatives');
    gl.getExtension('OES_element_index_uint');
    const vs = 'attribute vec3 aP; attribute vec3 aN; attribute vec2 aT;'
      + 'uniform mat4 uMV; uniform mat4 uPr; varying vec3 vP; varying vec3 vN; varying vec2 vT;'
      + 'void main(){ vec4 p = uMV*vec4(aP,1.0); vP = p.xyz; vN = mat3(uMV)*aN; vT = aT*3.99994-1.0; gl_Position = uPr*p; }';
    const fs = (M3D.deriv ? '#extension GL_OES_standard_derivatives : enable\n#define DERIV 1\n' : '')
      + 'precision mediump float; varying vec3 vP; varying vec3 vN; varying vec2 vT;'
      + 'uniform sampler2D tC; uniform sampler2D tN; uniform sampler2D tG;'
      + 'uniform float uHasN; uniform float uKind; uniform vec3 uFlat;'
      + 'void main(){'
      + ' vec3 N = normalize(vN);'
      + '\n#ifdef DERIV\n'
      + ' if(uHasN > 0.5){ vec3 d1 = dFdx(vP), d2 = dFdy(vP); vec2 t1 = dFdx(vT), t2 = dFdy(vT);'
      + '  vec3 c2 = cross(d2, N), c1 = cross(N, d1); vec3 T = c2*t1.x + c1*t2.x; vec3 B = c2*t1.y + c1*t2.y;'
      + '  float im = inversesqrt(max(max(dot(T,T), dot(B,B)), 1e-12));'
      + '  vec2 nm = texture2D(tN, vT).rg*2.0-1.0; vec3 tn = vec3(nm, sqrt(max(0.0, 1.0-dot(nm,nm))));'
      + '  N = normalize(T*im*tn.x - B*im*tn.y + N*tn.z); }\n'
      + '\n#endif\n'
      + ' vec3 base = uKind < 0.5 ? texture2D(tC, vT).rgb : uFlat;'
      + ' vec3 V = normalize(-vP);'
      + ' vec3 L1 = normalize(vec3(-0.45, 0.65, 0.62)), L2 = normalize(vec3(0.7, -0.25, 0.4));'
      + ' float d = max(dot(N, L1), 0.0)*0.95 + max(dot(N, L2), 0.0)*0.30;'
      + ' float s = pow(max(dot(N, normalize(L1+V)), 0.0), uKind > 1.5 ? 60.0 : 24.0)*(uKind > 1.5 ? 0.9 : 0.35);'
      + ' vec3 col = base*(0.30 + d*1.15)*1.15 + vec3(s);'
      + ' if(uKind < 0.5) col += texture2D(tG, vT).rgb;'
      + ' gl_FragColor = vec4(col, 1.0); }';
    const sh = function(t, src){ const s = gl.createShader(t); gl.shaderSource(s, src); gl.compileShader(s);
      if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(pr);
    if(!gl.getProgramParameter(pr, gl.LINK_STATUS)) return false;
    const loc = {};
    for(const a of ['aP','aN','aT']) loc[a] = gl.getAttribLocation(pr, a);
    for(const u of ['uMV','uPr','tC','tN','tG','uHasN','uKind','uFlat']) loc[u] = gl.getUniformLocation(pr, u);
    const px = function(r,g,b){ const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([r,g,b,255])); return t; };
    M3D.white = px(160,160,160); M3D.black = px(0,0,0); M3D.flatN = px(128,128,255);
    M3D.gl = gl; M3D.can = can; M3D.prog = pr; M3D.loc = loc;
    M3D.ok = true;
  }catch(e){ M3D.ok = false; M3D.err = String(e && e.message || e); }
  return M3D.ok;
}

// One detail level: the parts as GPU buffers, plus the textures they use.
function m3dLevel(key, tag, size){
  const gl = M3D.gl;
  const L = {state:'loading', parts:[], tex:{}};
  // v201: the full level is packed (full.bin.gz), see f3dFetchBin
  f3dFetchBin(M3D_BASE + key + '/' + (tag === 'full' ? 'full.bin.gz' : tag + '.bin')).then(function(buf){
    const hl = new DataView(buf).getUint32(0, true);
    const head = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 4, hl)));
    const base = 4 + hl, data = buf.slice(base);
    L.head = head;
    const want = {};
    for(const p of head.parts){
      const mk = function(target, from, bytes){ const b = gl.createBuffer(); gl.bindBuffer(target, b);
        gl.bufferData(target, new Uint8Array(data, from, bytes), gl.STATIC_DRAW); return b; };
      L.parts.push({kind:p.kind, tex:(p.tex||'').toLowerCase(), n:p.ni, big:p.big,
        pos:mk(gl.ARRAY_BUFFER, p.pos, p.nv*6), nrm:mk(gl.ARRAY_BUFFER, p.nrm, p.nv*4),
        uv:mk(gl.ARRAY_BUFFER, p.uv, p.nv*4), idx:mk(gl.ELEMENT_ARRAY_BUFFER, p.idx, p.ni*(p.big?4:2))});
      if(p.kind === 'tex') want[(p.tex||'').toLowerCase()] = true;
    }
    const jobs = [];
    for(const t in want){
      L.tex[t] = {};
      for(const k of ['c','n','g']){
        jobs.push(new Promise(function(res){
          const im = new Image();
          im.onload = function(){
            const tx = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tx);
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
            gl.generateMipmap(gl.TEXTURE_2D);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
            gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
            L.tex[t][k] = tx; res();
          };
          im.onerror = function(){ res(); };       // no glow map is normal
          im.src = M3D_BASE + key + '/' + t + '_' + k + size + '.webp?r=' + M3D_REV;
        }));
      }
    }
    return Promise.all(jobs);
  }).then(function(){ L.state = 'ready'; }, function(){ L.state = 'failed'; });
  return L;
}
function m3dModel(key){
  let m = M3D.models[key];
  if(!m){ m = M3D.models[key] = {lo:m3dLevel(key, 'lo', 512), hi:null}; }
  m.seen = (typeof performance !== 'undefined') ? performance.now() : Date.now();
  return m;
}
// Gives a level's buffers and textures back to the graphics card.
function m3dFree(L){
  const gl = M3D.gl;
  if(!L || !gl) return;
  for(const p of L.parts){ gl.deleteBuffer(p.pos); gl.deleteBuffer(p.nrm); gl.deleteBuffer(p.uv); gl.deleteBuffer(p.idx); }
  for(const t in L.tex) for(const k in L.tex[t]) gl.deleteTexture(L.tex[t][k]);
  L.parts = []; L.tex = {}; L.state = 'freed';
}
// Keeps the M3D_KEEP hulls shown last, frees the rest. A hull still
// loading is left alone; it is trimmed on a later frame. A freed hull
// loads again (from the browser cache) when it is shown again.
function m3dTrim(cur){
  const ks = Object.keys(M3D.models);
  if(ks.length <= M3D_KEEP) return;
  ks.sort(function(a, b){ return (M3D.models[a].seen||0) - (M3D.models[b].seen||0); });
  let n = ks.length;
  for(const k of ks){
    if(n <= M3D_KEEP) break;
    const m = M3D.models[k];
    if(k === cur || m.lo.state === 'loading' || (m.hi && m.hi.state === 'loading')) continue;
    m3dFree(m.lo); m3dFree(m.hi);
    delete M3D.models[k]; n--;
  }
}
function m3dMat(yaw, pitch, dist){
  const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
  // rotate about y (yaw), then about x (pitch), then push away from the eye
  return new Float32Array([
    cy,  sy*sp, -sy*cp, 0,
    0,   cp,     sp,    0,
    sy, -cy*sp,  cy*cp, 0,
    0,   0,     -dist,  1]);
}
function m3dPersp(aspect, near, far){
  const f = 1/Math.tan(M3D_FOV/2), nf = 1/(near-far);
  return new Float32Array([f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0]);
}
// Draws the hull into the box (x, y, w, h) of the 2D screen. False when
// it cannot (no WebGL, not loaded yet, files missing): draw the sprite.
function m3dDraw(key, x, y, w, h, o){
  if(!key || !m3dInit()) return false;
  const m = m3dModel(key);
  m3dTrim(key);
  o = o || {};
  // v196: a capital ship has a 'full' level (every part of the finest
  // level, 59_field3d.js) and takes it right away: the coarser levels show
  // black patches where the finest one has its detail parts (Silvio: Orion).
  const cap = typeof F3D_KEYS !== 'undefined' && F3D_KEYS.indexOf(key) >= 0;
  if((cap || Math.max(o.zoom||1, M3D_VIEW.zoomT||1) >= M3D_ZOOM_HI) && !m.hi) m.hi = m3dLevel(key, cap ? 'full' : 'hi', 1024);
  const L = (m.hi && m.hi.state === 'ready') ? m.hi : m.lo;
  if(L.state !== 'ready') return false;
  const gl = M3D.gl, can = M3D.can, loc = M3D.loc;
  let pw, ph;
  if(M3D.overlay && typeof CVS !== 'undefined' && CVS.getBoundingClientRect){
    // place the layer over the box, in CSS pixels, sharp on a HiDPI screen
    const r = CVS.getBoundingClientRect(), sx = r.width / W, sy = r.height / H;
    const dpr = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;
    const cl = Math.round(r.left + x*sx), ct = Math.round(r.top + y*sy);
    const cw = Math.max(1, Math.round(w*sx)), ch = Math.max(1, Math.round(h*sy));
    const st = can.style, box = cl+','+ct+','+cw+','+ch;
    if(M3D.box !== box){ M3D.box = box; st.left = cl+'px'; st.top = ct+'px'; st.width = cw+'px'; st.height = ch+'px'; }
    pw = Math.max(1, Math.round(cw*dpr)); ph = Math.max(1, Math.round(ch*dpr));
    if(st.display === 'none') st.display = 'block';
    M3D.used = true;
  } else {
    const k = (typeof CVS !== 'undefined' && CVS.width) ? CVS.width / W : 1;
    pw = Math.max(1, Math.round(w*k)); ph = Math.max(1, Math.round(h*k));
  }
  if(can.width !== pw || can.height !== ph){ can.width = pw; can.height = ph; }
  gl.viewport(0, 0, pw, ph);
  gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST); gl.enable(gl.CULL_FACE); gl.cullFace(gl.BACK);
  gl.useProgram(M3D.prog);
  // Fit: the longest half-extent is 1 after scaling by ext.
  const hd = L.head, e = hd.ext, aspect = pw/ph, t = Math.tan(M3D_FOV/2);
  // Fit for every turn: the hull's footprint is a circle in the ground
  // plane, so it never grows out of the box while it spins.
  const rxz = Math.hypot(hd.size[0], hd.size[2])/2/e, hy = hd.size[1]/2/e;
  const pt = o.pitch == null ? M3D_PITCH0 : o.pitch;
  const vy = hy*Math.cos(pt) + rxz*Math.sin(pt);
  const fit = Math.max(rxz + 0.94*rxz/(t*aspect), rxz*Math.cos(pt) + 0.94*vy/t);
  const dist = rxz + (fit - rxz)/(o.zoom||1);
  const mv = m3dMat(o.yaw == null ? M3D_YAW0 : o.yaw, o.pitch == null ? M3D_PITCH0 : o.pitch, dist);
  gl.uniformMatrix4fv(loc.uMV, false, mv);
  gl.uniformMatrix4fv(loc.uPr, false, m3dPersp(aspect, 0.05, dist + 4));
  gl.uniform1i(loc.tC, 0); gl.uniform1i(loc.tN, 1); gl.uniform1i(loc.tG, 2);
  for(const p of L.parts){
    const tx = L.tex[p.tex] || {};
    const kind = p.kind === 'tex' && tx.c ? 0 : (p.kind === 'glass' ? 2 : 1);
    gl.uniform1f(loc.uKind, kind);
    gl.uniform3f(loc.uFlat, kind === 2 ? 0.05 : 0.30, kind === 2 ? 0.07 : 0.30, kind === 2 ? 0.10 : 0.32);
    gl.uniform1f(loc.uHasN, kind === 0 && tx.n ? 1 : 0);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tx.c || M3D.white);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, tx.n || M3D.flatN);
    gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, tx.g || M3D.black);
    gl.bindBuffer(gl.ARRAY_BUFFER, p.pos); gl.enableVertexAttribArray(loc.aP);
    gl.vertexAttribPointer(loc.aP, 3, gl.SHORT, true, 6, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, p.nrm); gl.enableVertexAttribArray(loc.aN);
    gl.vertexAttribPointer(loc.aN, 3, gl.BYTE, true, 4, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, p.uv); gl.enableVertexAttribArray(loc.aT);
    gl.vertexAttribPointer(loc.aT, 2, gl.UNSIGNED_SHORT, true, 4, 0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, p.idx);
    gl.drawElements(gl.TRIANGLES, p.n, p.big ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT, 0);
  }
  if(!M3D.overlay) ctx.drawImage(can, x, y, w, h);
  return true;
}
// Called once per frame after everything is drawn: a model that was not
// drawn this frame (its window closed) takes its layer away.
function m3dEndFrame(){
  if(!M3D.overlay || !M3D.can) return;
  if(!M3D.used && M3D.can.style.display !== 'none') M3D.can.style.display = 'none';
  M3D.used = false;
}
// The picture's own state: turning while the pointer is on it, zoom from
// the wheel, easing back to rest when the pointer leaves.
// v193: the turn speeds up and slows down instead of starting and
// stopping dead, and the wheel sets a target the zoom glides to.
const M3D_VIEW = {yaw:M3D_YAW0, zoom:1, zoomT:1, spin:0, t:0, key:null};
const M3D_EASE_SPIN = 3.0, M3D_EASE_ZOOM = 9.0, M3D_EASE_REST = 3.0;
function m3dView(key, hot){
  const now = (typeof performance !== 'undefined') ? performance.now() : Date.now();
  const dt = M3D_VIEW.t ? Math.min(0.05, (now - M3D_VIEW.t)/1000) : 0;
  M3D_VIEW.t = now;
  if(M3D_VIEW.key !== key){ M3D_VIEW.key = key; M3D_VIEW.yaw = M3D_YAW0; M3D_VIEW.zoom = M3D_VIEW.zoomT = 1; M3D_VIEW.spin = 0; }
  const ease = function(rate){ return 1 - Math.exp(-rate*dt); };
  M3D_VIEW.spin += ((hot ? M3D_SPIN : 0) - M3D_VIEW.spin)*ease(M3D_EASE_SPIN);
  M3D_VIEW.yaw += M3D_VIEW.spin*dt;
  if(!hot){
    M3D_VIEW.zoomT = 1;
    // back to rest the short way round, once the turn has run out
    if(M3D_VIEW.spin < 0.05){
      let d = (M3D_YAW0 - M3D_VIEW.yaw) % (Math.PI*2);
      if(d > Math.PI) d -= Math.PI*2; if(d < -Math.PI) d += Math.PI*2;
      M3D_VIEW.yaw += d*ease(M3D_EASE_REST);
    }
  }
  M3D_VIEW.zoom += (M3D_VIEW.zoomT - M3D_VIEW.zoom)*ease(M3D_EASE_ZOOM);
  return {yaw:M3D_VIEW.yaw, zoom:M3D_VIEW.zoom};
}
function m3dWheel(dy){
  M3D_VIEW.zoomT = Math.max(1, Math.min(M3D_ZOOM_MAX, M3D_VIEW.zoomT*(dy < 0 ? 1.12 : 1/1.12)));
}
