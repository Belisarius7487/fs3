// ── COLLECTED EFFECTS (F104, v304) ─────────────────────────────────
// Silvio's Brave traces: the browser's graphics process is busy 85-98 % of
// every second during a fight, the game itself 3-6 ms a frame. Every single
// 2D drawing call (a glow, a spark, a fireball) travels through that
// process on its own - some 500 a frame. Effects made of many like parts
// are collected here instead and drawn by the graphics card in ONE call:
// each part is a small textured rectangle, all pictures sit in one texture
// (the atlas), and the result is put into the 2D canvas once.
//
// Additive light and solid parts share the one pass, in the order they are
// put: colours are premultiplied, and a part that only adds light writes an
// alpha of 0 - the copy into the 2D canvas (source-over) then adds it,
// while a solid part covers what is under it.
//
// The pictures are the very sprites the 2D path draws (glowSprite,
// fbSprite), so the look is the same. Without WebGL, or with &fxgl=0, the
// 2D path draws as before.
const FXB = {ok: null, off: false, live: false, bmp: false, can: null, gl: null, uX: null, n: 0, gen: 1, dirty: false,
             cell: 0, sub: null, disc: null, x0: 1e9, y0: 1e9, x1: -1e9, y1: -1e9, flushes: 0};
const FXB_MAXQ = 4096;            // rectangles in one call
const FXB_AT = 1024;              // the atlas, pixels square
const FXB_CELL = 128;             // its cells; a picture of 64 or less takes a quarter
const FXB_FL = 8;                 // floats per corner: x, y, u, v, r, g, b, a
const FXB_SWITCH = (typeof urlNum === 'function') ? urlNum('fxgl', 1, 0, 1) : 1;
let FXB_V = null;
function fxbInit(){
  if(FXB.ok !== null) return FXB.ok;
  FXB.ok = false;
  try{
    if(typeof document === 'undefined' || !document.createElement || typeof CVS === 'undefined') return false;
    // v305: measured in the built-in browser - drawImage() from a WebGL
    // canvas into the 2D canvas costs a fixed ~3 ms each time, whatever the
    // size of the part copied (the browser copies the whole drawing buffer
    // and switches between its two graphics contexts). An OffscreenCanvas
    // hands its picture over without a copy (transferToImageBitmap) and
    // starts the next one empty: no measurable cost. Where a browser has no
    // WebGL on an OffscreenCanvas, the plain canvas is used as before.
    const opt = {alpha: true, premultipliedAlpha: true, antialias: false,
                 depth: false, stencil: false, preserveDrawingBuffer: false};
    let can = null, gl = null;
    if(typeof OffscreenCanvas !== 'undefined' && OffscreenCanvas.prototype.transferToImageBitmap){
      try{ can = new OffscreenCanvas(2, 2); gl = can.getContext('webgl', opt); }catch(eo){ gl = null; }
      FXB.bmp = !!gl;
    }
    if(!gl){ can = document.createElement('canvas'); gl = can.getContext('webgl', opt); }
    if(!gl) return false;
    const sh = function(type, src){
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error('fxb shader');
      return s;
    };
    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER,
      'attribute vec2 aP; attribute vec2 aT; attribute vec4 aC; uniform vec4 uX; varying vec2 vT; varying vec4 vC;'
      + 'void main(){ vT = aT; vC = aC; gl_Position = vec4(aP.x*uX.x + uX.y, aP.y*uX.z + uX.w, 0.0, 1.0); }'));
    gl.attachShader(pr, sh(gl.FRAGMENT_SHADER,
      // full precision where the card has it, as every shader here (F102)
      '#ifdef GL_FRAGMENT_PRECISION_HIGH\nprecision highp float;\n#else\nprecision mediump float;\n#endif\n'
      + 'uniform sampler2D uS; varying vec2 vT; varying vec4 vC;'
      + 'void main(){ gl_FragColor = texture2D(uS, vT)*vC; }'));
    gl.bindAttribLocation(pr, 0, 'aP'); gl.bindAttribLocation(pr, 1, 'aT'); gl.bindAttribLocation(pr, 2, 'aC');
    gl.linkProgram(pr);
    if(!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error('fxb link');
    gl.useProgram(pr);
    FXB.uX = gl.getUniformLocation(pr, 'uX');
    gl.uniform1i(gl.getUniformLocation(pr, 'uS'), 0);
    FXB_V = new Float32Array(FXB_MAXQ*4*FXB_FL);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, FXB_V.byteLength, gl.DYNAMIC_DRAW);
    const ix = new Uint16Array(FXB_MAXQ*6);
    for(let q = 0; q < FXB_MAXQ; q++){
      const o = q*6, v = q*4;
      ix[o] = v; ix[o+1] = v+1; ix[o+2] = v+2; ix[o+3] = v; ix[o+4] = v+2; ix[o+5] = v+3;
    }
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, ix, gl.STATIC_DRAW);
    const st = FXB_FL*4;
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, st, 0);
    gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 2, gl.FLOAT, false, st, 8);
    gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 4, gl.FLOAT, false, st, 16);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, gl.createTexture());
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, FXB_AT, FXB_AT, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    // the 2D canvas draws its pictures smoothed and with mipmaps when they
    // are drawn small (imageSmoothingQuality 'high'): the same here
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    // a bolt's glow is drawn long and thin: sampled along its length too,
    // it matches the 2D picture best (largest deviation 14 instead of 34)
    const an = gl.getExtension('EXT_texture_filter_anisotropic');
    if(an) gl.texParameterf(gl.TEXTURE_2D, an.TEXTURE_MAX_ANISOTROPY_EXT, 4);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
    gl.disable(gl.DEPTH_TEST); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    gl.clearColor(0, 0, 0, 0);
    // a lost context: the 2D path takes over for good
    if(can.addEventListener) can.addEventListener('webglcontextlost', function(){ FXB.ok = false; FXB.n = 0; });
    // a solid dot (debris cores), white, tinted by the part that uses it
    const d = document.createElement('canvas'); d.width = d.height = 64;
    const g = d.getContext('2d'); g.fillStyle = '#fff'; g.beginPath(); g.arc(32, 32, FXB_DISC_R, 0, Math.PI*2); g.fill();
    FXB.disc = d;
    FXB.can = can; FXB.gl = gl; FXB.ok = true;
  }catch(e){ FXB.ok = false; }
  return FXB.ok;
}
const FXB_DISC_R = 28;            // the dot's radius in its 64 pixel picture
function fxbOn(){ return !FXB.off && FXB_SWITCH !== 0 && fxbInit(); }
// A picture's place in the atlas; it is put there the first time it is used.
// null: the atlas is full.
function fxbTile(c){
  const t = c._fxb;
  if(t && t.gen === FXB.gen) return t;
  const gl = FXB.gl, w = c.width, h = c.height, per = FXB_AT/FXB_CELL, half = FXB_CELL/2;
  if(w > FXB_CELL || h > FXB_CELL) return null;
  const small = (w <= half && h <= half);
  let x, y;
  if(small && FXB.sub && FXB.sub.k < 4){
    const k = FXB.sub.k++; x = FXB.sub.x + (k & 1)*half; y = FXB.sub.y + (k >> 1)*half;
  } else {
    if(FXB.cell >= per*per) return null;
    x = (FXB.cell % per)*FXB_CELL; y = ((FXB.cell/per) | 0)*FXB_CELL; FXB.cell++;
    if(small) FXB.sub = {x: x, y: y, k: 1};
  }
  gl.texSubImage2D(gl.TEXTURE_2D, 0, x, y, gl.RGBA, gl.UNSIGNED_BYTE, c);
  FXB.dirty = true;
  if(typeof perfNote === 'function') perfNote('fx atlas tile');
  return (c._fxb = {gen: FXB.gen, u0: x/FXB_AT, v0: y/FXB_AT, u1: (x + w)/FXB_AT, v1: (y + h)/FXB_AT});
}
// The atlas is full (hundreds of glow colours): start it again, empty.
function fxbAtlasReset(){
  const gl = FXB.gl;
  FXB.gen++; FXB.cell = 0; FXB.sub = null;
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, FXB_AT, FXB_AT, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
  FXB.dirty = true;
}
function fxbBegin(){ FXB.n = 0; FXB.x0 = FXB.y0 = 1e9; FXB.x1 = FXB.y1 = -1e9; }
// One part: picture c centred on the world point (x, y), rx by ry (half
// sizes), turned by ang. add: it only adds its light. r, g, b (0..1) tint
// a white picture.
function fxbPut(c, x, y, rx, ry, ang, al, add, r, g, b){
  if(!c || !(rx > 0) || !(ry > 0) || !(al > 0)) return;
  let t = c._fxb;
  if(!t || t.gen !== FXB.gen){
    t = fxbTile(c);
    if(!t){ fxbFlush(); fxbAtlasReset(); t = fxbTile(c); if(!t) return; }
  }
  if(FXB.n >= FXB_MAXQ) fxbFlush();
  if(al > 1) al = 1;
  const cr = (r === undefined ? 1 : r)*al, cg = (g === undefined ? 1 : g)*al, cb = (b === undefined ? 1 : b)*al, ca = add ? 0 : al;
  let ax = rx, ay = 0, bx = 0, by = ry;
  if(ang){ const co = Math.cos(ang), si = Math.sin(ang); ax = rx*co; ay = rx*si; bx = -ry*si; by = ry*co; }
  const V = FXB_V; let o = FXB.n*4*FXB_FL;
  V[o] = x - ax - bx; V[o+1] = y - ay - by; V[o+2] = t.u0; V[o+3] = t.v0; V[o+4] = cr; V[o+5] = cg; V[o+6] = cb; V[o+7] = ca; o += 8;
  V[o] = x + ax - bx; V[o+1] = y + ay - by; V[o+2] = t.u1; V[o+3] = t.v0; V[o+4] = cr; V[o+5] = cg; V[o+6] = cb; V[o+7] = ca; o += 8;
  V[o] = x + ax + bx; V[o+1] = y + ay + by; V[o+2] = t.u1; V[o+3] = t.v1; V[o+4] = cr; V[o+5] = cg; V[o+6] = cb; V[o+7] = ca; o += 8;
  V[o] = x - ax + bx; V[o+1] = y - ay + by; V[o+2] = t.u0; V[o+3] = t.v1; V[o+4] = cr; V[o+5] = cg; V[o+6] = cb; V[o+7] = ca;
  FXB.n++;
  const mx = Math.abs(ax) + Math.abs(bx), my = Math.abs(ay) + Math.abs(by);
  if(x - mx < FXB.x0) FXB.x0 = x - mx;
  if(x + mx > FXB.x1) FXB.x1 = x + mx;
  if(y - my < FXB.y0) FXB.y0 = y - my;
  if(y + my > FXB.y1) FXB.y1 = y + my;
}
// A soft glow, as glowAdd() draws it (61_glow.js).
function fxbGlow(x, y, rx, ry, col, al, hot, ang){
  fxbPut(glowSprite(col, hot), x, y, rx, ry, ang || 0, al, true);
}
// Draws what was collected - one call - and copies the part of the picture
// it covers into the 2D canvas, through the camera of this frame.
function fxbFlush(){
  const n = FXB.n;
  if(!n) return;
  const gl = FXB.gl, can = FXB.can, pw = CVS.width, ph = CVS.height;
  const z = CAM.z, ox = FIELD_CX - CAM.x*z + CAM_SHX, oy = FIELD_CY - CAM.y*z + CAM_SHY, kx = pw/W, ky = ph/H;
  const px0 = Math.max(0, Math.floor((FXB.x0*z + ox)*kx) - 1), py0 = Math.max(0, Math.floor((FXB.y0*z + oy)*ky) - 1);
  const px1 = Math.min(pw, Math.ceil((FXB.x1*z + ox)*kx) + 1), py1 = Math.min(ph, Math.ceil((FXB.y1*z + oy)*ky) + 1);
  fxbBegin();
  if(px1 <= px0 || py1 <= py0) return;
  if(can.width !== pw || can.height !== ph){ can.width = pw; can.height = ph; }
  gl.viewport(0, 0, pw, ph);
  // a picture handed over (FXB.bmp) leaves an empty buffer behind: nothing to clear
  if(!FXB.bmp){ gl.enable(gl.SCISSOR_TEST); gl.scissor(px0, ph - py1, px1 - px0, py1 - py0); gl.clear(gl.COLOR_BUFFER_BIT); }
  if(FXB.dirty){ gl.generateMipmap(gl.TEXTURE_2D); FXB.dirty = false; }
  gl.uniform4f(FXB.uX, z*2/W, ox*2/W - 1, -z*2/H, 1 - oy*2/H);
  gl.bufferSubData(gl.ARRAY_BUFFER, 0, FXB_V.subarray(0, n*4*FXB_FL));
  gl.drawElements(gl.TRIANGLES, n*6, gl.UNSIGNED_SHORT, 0);
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  if(FXB.bmp){
    const bm = can.transferToImageBitmap();
    ctx.drawImage(bm, px0, py0, px1 - px0, py1 - py0, px0, py0, px1 - px0, py1 - py0);
    bm.close();
  } else ctx.drawImage(can, px0, py0, px1 - px0, py1 - py0, px0, py0, px1 - px0, py1 - py0);
  ctx.restore();
  FXB.flushes++;
}
// Behind the title screen: the pictures the fights use go into the atlas
// and one invisible part is drawn, so the first fight does not wait for the
// shader and the texture (as glowWarm() does for the 2D sprites).
function fxbWarm(){
  if(!fxbOn() || typeof CAM === 'undefined') return;
  try{
    for(const k in GLOW_SPR) fxbTile(GLOW_SPR[k]);
    if(typeof fbSprite === 'function') for(let k = 0; k <= 10; k++){ const f = fbSprite(k/10); if(f) fxbTile(f); }
    fxbBegin();
    fxbPut(FXB.disc, CAM.x, CAM.y, 1, 1, 0, 0.004, true);
    fxbFlush();
  }catch(e){ FXB.ok = false; }
}
