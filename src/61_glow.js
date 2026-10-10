// ── SOFT LIGHT (v213, Silvio: effects package, part 1) ─────────────
// The glows were drawn as filled circles and ellipses stacked on top of
// each other - every layer had a hard edge, which showed as a visible
// ring of light against a dark or a bright background. Everything that
// glows now draws a pre-rendered soft sprite (a gaussian falloff, no edge)
// with additive light, cached per colour.
const GLOW_SPR = {}, GLOW_RGB = {}, GLOW_N = 64;
// a CSS colour as [r, g, b] (0..255), read once through a 1x1 canvas
function glowRGB(col){
  if(GLOW_RGB[col]) return GLOW_RGB[col];
  let rgb = [255, 255, 255];
  try{
    const m = /^#([0-9a-f]{6})$/i.exec(col);
    const q = /^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)/i.exec(col);   // its alpha is the caller's business
    if(m){ const v = parseInt(m[1], 16); rgb = [(v>>16)&255, (v>>8)&255, v&255]; }
    else if(q){ rgb = [+q[1]|0, +q[2]|0, +q[3]|0]; }
    else {
      const c = document.createElement('canvas'); c.width = c.height = 1;
      const g = c.getContext('2d'); g.fillStyle = '#000'; g.fillStyle = col; g.fillRect(0, 0, 1, 1);
      const d = g.getImageData(0, 0, 1, 1).data; rgb = [d[0], d[1], d[2]];
    }
  }catch(e){}
  return (GLOW_RGB[col] = rgb);
}
// A round soft glow: white hot in the middle (hot 0..1), the colour round
// it, falling off to nothing at the edge.
function glowSprite(col, hot){
  const k = col + '|' + (hot || 0);
  if(GLOW_SPR[k]) return GLOW_SPR[k];
  if(typeof document === 'undefined') return null;
  const c = document.createElement('canvas'); c.width = c.height = GLOW_N;
  const g = c.getContext('2d'), r = GLOW_N/2, [R, G, B] = glowRGB(col), h = hot || 0;
  const gr = g.createRadialGradient(r, r, 0, r, r, r);
  // a gaussian in steps: no step is visible as an edge
  for(let i = 0; i <= 10; i++){
    const t = i/10, f = Math.exp(-t*t*4.2)*(1 - t);           // reaches 0 at the rim
    const w = h*Math.exp(-t*t*40);                             // the white core
    const cr = Math.round(R + (255 - R)*w), cg = Math.round(G + (255 - G)*w), cb = Math.round(B + (255 - B)*w);
    gr.addColorStop(t, 'rgba(' + cr + ',' + cg + ',' + cb + ',' + Math.min(1, f + w*0.6).toFixed(3) + ')');
  }
  g.fillStyle = gr; g.fillRect(0, 0, GLOW_N, GLOW_N);
  return (GLOW_SPR[k] = c);
}
// Draws one glow, centred, rx by ry (radii), turned by ang. Additive.
function glowAt(x, y, rx, ry, col, alpha, hot, ang){
  const s = glowSprite(col, hot); if(!s || !(rx > 0) || !(ry > 0) || !(alpha > 0)) return;
  const op = ctx.globalCompositeOperation, a0 = ctx.globalAlpha;
  ctx.globalCompositeOperation = 'lighter';
  ctx.globalAlpha = a0*Math.min(1, alpha);
  if(ang){
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
    ctx.drawImage(s, -rx, -ry, rx*2, ry*2);
    ctx.restore();
  } else ctx.drawImage(s, x - rx, y - ry, rx*2, ry*2);
  ctx.globalCompositeOperation = op; ctx.globalAlpha = a0;
}

// ── BEAMS (v213) ──
// A beam was three stroked lines (glow, mid, core) - flat, and with hard
// edges. Now its cross section is a soft profile (white core, coloured
// sheath, a wide faint halo), and light runs along it: bands of
// brightness that travel from the turret to the target, so it reads as
// energy streaming out rather than a painted stripe.
const BEAM_TEX = {}, BEAM_FLOW = {};
function beamTex(col){
  if(BEAM_TEX[col]) return BEAM_TEX[col];
  if(typeof document === 'undefined') return null;
  const c = document.createElement('canvas'); c.width = 4; c.height = 64;
  const g = c.getContext('2d'), [R, G, B] = glowRGB(col);
  const gr = g.createLinearGradient(0, 0, 0, 64);
  for(let i = 0; i <= 16; i++){
    const t = i/16, d = Math.abs(t - 0.5)*2;                   // 0 middle .. 1 edge
    const halo = Math.exp(-d*d*3.0)*(1 - d)*0.55, sheath = Math.exp(-d*d*18), core = Math.exp(-d*d*120);
    const w = Math.min(1, core*1.2);
    const r = Math.round(R + (255 - R)*w), gg = Math.round(G + (255 - G)*w), b = Math.round(B + (255 - B)*w);
    gr.addColorStop(t, 'rgba(' + r + ',' + gg + ',' + b + ',' + Math.min(1, halo + sheath*0.8 + core).toFixed(3) + ')');
  }
  g.fillStyle = gr; g.fillRect(0, 0, 4, 64);
  return (BEAM_TEX[col] = c);
}
// bands along the beam: a strip that repeats, soft light and dark
function beamFlow(col){
  if(BEAM_FLOW[col]) return BEAM_FLOW[col];
  if(typeof document === 'undefined') return null;
  const c = document.createElement('canvas'); c.width = 128; c.height = 32;
  const g = c.getContext('2d'), [R, G, B] = glowRGB(col);
  for(let x = 0; x < 128; x++){
    const v = 0.5 + 0.30*Math.sin(x/128*Math.PI*2*3) + 0.20*Math.sin(x/128*Math.PI*2*7 + 1.3);
    const gr = g.createLinearGradient(0, 0, 0, 32);
    gr.addColorStop(0, 'rgba(0,0,0,0)');
    gr.addColorStop(0.5, 'rgba(' + Math.round(R*0.5 + 127) + ',' + Math.round(G*0.5 + 127) + ',' + Math.round(B*0.5 + 127) + ',' + (v*0.55).toFixed(3) + ')');
    gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr; g.fillRect(x, 0, 1, 32);
  }
  return (BEAM_FLOW[col] = c);
}
// The ray from (x0,y0) at angle ang, len long, w wide (the sheath; the
// halo reaches about twice as far). t: time for the flow.
function drawBeamRay(x0, y0, ang, len, w, col, alpha, t){
  const tex = beamTex(col); if(!tex || !(len > 0)) return;
  ctx.save();
  ctx.translate(x0, y0); ctx.rotate(ang);
  ctx.globalCompositeOperation = 'lighter';
  ctx.globalAlpha = Math.min(1, alpha);
  // the body, a little thicker towards the turret
  ctx.drawImage(tex, 0, -w*1.6, len, w*3.2);
  // the flow, moving outward
  const fl = beamFlow(col);
  if(fl){
    const seg = w*14, off = -((t*w*0.9) % seg);
    ctx.globalAlpha = Math.min(1, alpha)*0.9;
    ctx.beginPath(); ctx.rect(0, -w*2, len, w*4); ctx.clip();
    for(let x = off; x < len; x += seg) ctx.drawImage(fl, x, -w*0.9, seg, w*1.8);
  }
  ctx.restore();
}
// The orb at a beam turret: layered soft glows, a white-hot heart and a
// thin flare across it. r: its radius on the screen.
function drawBeamGlowOrb(x, y, r, col, alpha, ang){
  if(!(r > 0)) return;
  glowAt(x, y, r*3.2, r*3.2, col, alpha*0.45, 0);
  glowAt(x, y, r*1.6, r*1.6, col, alpha*0.9, 0.9);
  // the flare: long and thin, across the line of fire
  glowAt(x, y, r*4.5, r*0.28, col, alpha*0.55, 0.6, (ang || 0) + Math.PI/2);
  glowAt(x, y, r*2.6, r*0.22, col, alpha*0.35, 0.6, ang || 0);
}

// ── BEAM CHARGE PARTICLES (v213, Silvio) ──
// Light round the turret is drawn into the charge: each mote starts out
// slow and falls in ever faster, as if the charge were swallowing it.
// They hang on the turret (e, b), so they follow her when she moves or
// turns. Drawn as short streaks along their fall.
let CHARGE_PARTS = [];
const CHARGE_CAP = 260;
function chargeSpawn(e, b, g, large){
  if(CHARGE_PARTS.length >= CHARGE_CAP) return;
  const a = Math.random()*Math.PI*2;
  CHARGE_PARTS.push({e: e, b: b, a: a, r: (large ? 34 : 20)*(1 + Math.random()*1.2)*g, v: 0.05*g,
                     acc: (large ? 0.045 : 0.035)*g*(0.7 + Math.random()*0.6), g: g, large: large, prev: null});
}
function chargeTick(){
  for(let i = CHARGE_PARTS.length - 1; i >= 0; i--){
    const p = CHARGE_PARTS[i];
    if(!p.b || p.b.state !== 'charging' || p.e.dead || !(p.e.beams && p.e.beams.indexOf(p.b) >= 0)){ CHARGE_PARTS.splice(i, 1); continue; }
    p.prev = p.r;
    p.v += p.acc; p.acc *= 1.04;        // falls in ever faster
    p.r -= p.v;
    if(p.r <= 1.2*p.g) CHARGE_PARTS.splice(i, 1);
  }
}
function drawChargeParts(e, b){
  for(const p of CHARGE_PARTS){
    if(p.e !== e || (b && p.b !== b)) continue;
    const m = mountPosV(p.e, p.b), col = beamCol(p.e.faction, p.b.large);
    const c = Math.cos(p.a), s = Math.sin(p.a), r1 = p.r, r0 = Math.max(p.r, (p.prev || p.r) + p.v*2.5);
    const near = 1 - Math.min(1, p.r/((p.large ? 60 : 36)*p.g));          // brighter as it nears
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = 0.25 + 0.6*near;
    ctx.strokeStyle = col; ctx.lineCap = 'round';
    ctx.lineWidth = (p.large ? 1.6 : 1.1)*p.g;
    ctx.beginPath(); ctx.moveTo(m.x + c*r0, m.y + s*r0); ctx.lineTo(m.x + c*r1, m.y + s*r1); ctx.stroke();
    ctx.restore();
    glowAt(m.x + c*r1, m.y + s*r1, (p.large ? 2.6 : 1.8)*p.g, (p.large ? 2.6 : 1.8)*p.g, col, 0.5 + 0.5*near, 0.8);
  }
}

// ── STARS (v213, Silvio) ──
// The stars were single pixels drawn after the planets, so they lay on
// top of them. Now they are three layers painted once - many faint ones,
// fewer brighter ones with a soft halo, a few large ones - drawn behind
// the planets and suns (drawStars before drawBodies), each layer moving
// with the camera by its own share (parallax), wrapped across the screen.
const STAR_LAYERS = [];
function starLayers(){
  if(STAR_LAYERS.length || typeof document === 'undefined') return STAR_LAYERS;
  const spec = [{n: 520, s: [0.25, 0.55], b: [0.30, 0.70], par: 0.35},
                {n: 140, s: [0.45, 0.85], b: [0.55, 0.95], par: 0.7},
                {n: 14,  s: [0.8, 1.2],  b: [0.85, 1.0], par: 1.1}];
  const tints = [[255,255,255],[205,220,255],[255,236,214],[220,232,255],[255,250,235]];
  const k = (typeof RES_X !== 'undefined') ? Math.max(1, RES_X) : 1;
  for(const L of spec){
    const c = document.createElement('canvas'); c.width = Math.round(W*k); c.height = Math.round(H*k);
    const g = c.getContext('2d'); g.scale(k, k);
    for(let i = 0; i < L.n; i++){
      const x = Math.random()*W, y = Math.random()*H, sz = L.s[0] + Math.random()*(L.s[1] - L.s[0]);
      const br = L.b[0] + Math.random()*(L.b[1] - L.b[0]), t = tints[(Math.random()*tints.length)|0];
      const rgb = t[0] + ',' + t[1] + ',' + t[2];
      // each star wraps round the edges, so the tiles join
      for(const ox of [0, -W, W]) for(const oy of [0, -H, H]){
        const px = x + ox, py = y + oy;
        if(px < -8 || px > W + 8 || py < -8 || py > H + 8) continue;
        // a sharp point with a faint halo - not a soft blob
        const gr = g.createRadialGradient(px, py, 0, px, py, sz*2.2);
        gr.addColorStop(0, 'rgba(' + rgb + ',' + br.toFixed(3) + ')');
        gr.addColorStop(0.18, 'rgba(' + rgb + ',' + (br*0.85).toFixed(3) + ')');
        gr.addColorStop(0.32, 'rgba(' + rgb + ',' + (br*0.18).toFixed(3) + ')');
        gr.addColorStop(1, 'rgba(' + rgb + ',0)');
        g.fillStyle = gr; g.beginPath(); g.arc(px, py, sz*2.2, 0, Math.PI*2); g.fill();
      }
    }
    STAR_LAYERS.push({c: c, par: L.par});
  }
  return STAR_LAYERS;
}
