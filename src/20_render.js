// ── SURFACE KIT ───────────────────────────────────────────────
// One vocabulary of shapes for every panel in the game. A screen picks from
// this and adds nothing of its own, which is the only thing that keeps six
// screens looking like one interface.
//
// The chamfer is the signature: the top left and bottom right corner cut off
// at 45 degrees. Angular rather than rounded, because that is the register a
// FreeSpace interface is in, and it reads as a machined edge rather than a
// web card. Six points at row scale, twelve at panel scale.
function thChamferPath(x, y, w, h, c){
  if(c === undefined) c = 6;
  c = Math.min(c, w/2, h/2);
  ctx.beginPath();
  ctx.moveTo(x+c,   y);
  ctx.lineTo(x+w,   y);
  ctx.lineTo(x+w,   y+h-c);
  ctx.lineTo(x+w-c, y+h);
  ctx.lineTo(x,     y+h);
  ctx.lineTo(x,     y+c);
  ctx.closePath();
}
// A theme colour with an alpha put on it. The table stores 'rgb(r,g,b)',
// which cannot carry one.
function thRGBA(role, a){
  const c = TH(role);
  return c.indexOf('rgb(')===0 ? 'rgba('+c.slice(4,-1)+','+a+')' : c;
}
// Gloss: one shallow fall of light over the top of a plate, clipped to the
// plate's own outline. This is the sheen, and it is deliberately not the
// old box gradient - it covers the top third and then stops, so a stack of
// plates still reads as a list and not as a stack of boxes.
function thGloss(x, y, w, h, c){
  ctx.save();
  thChamferPath(x, y, w, h, c); ctx.clip();
  const gr = ctx.createLinearGradient(0, y, 0, y+Math.max(8, h*0.42));
  gr.addColorStop(0, 'rgba(255,255,255,0.075)');
  gr.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = gr; ctx.fillRect(x, y, w, h);
  ctx.restore();
}
// The two cut faces of the chamfer, lit. The only place in this interface
// where a highlight sits on an edge, and what makes the corner read as
// milled rather than merely missing.
function thCutGlint(x, y, w, h, c, col){
  if(c === undefined) c = 6;
  ctx.save();
  ctx.strokeStyle = col || 'rgba(255,255,255,0.22)'; ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x+0.5, y+c+0.5);       ctx.lineTo(x+c+0.5, y+0.5);
  ctx.moveTo(x+w-c-0.5, y+h-0.5);   ctx.lineTo(x+w-0.5, y+h-c-0.5);
  ctx.stroke();
  ctx.restore();
}
// A flat plate: a dark outline all round, one bright hairline along the
// top, the gloss over its top third and the cut faces lit. Every surface
// in the game comes from here, which is why the sheen is applied once,
// in this function, and never per screen.
function thPlate(x, y, w, h, fill, c){
  if(c === undefined) c = 6;
  thChamferPath(x, y, w, h, c);
  ctx.fillStyle = fill;
  ctx.fill();
  thGloss(x, y, w, h, c);
  ctx.lineWidth = 1;
  ctx.strokeStyle = TH('edgeDark');
  thChamferPath(x+0.5, y+0.5, w-1, h-1, c);
  ctx.stroke();
  ctx.strokeStyle = TH('edgeLight');
  ctx.beginPath();
  ctx.moveTo(x+c+0.5, y+0.5); ctx.lineTo(x+w-0.5, y+0.5);
  ctx.stroke();
  thCutGlint(x, y, w, h, c);
}
// The theme's ring, following a chamfered outline instead of a rectangle.
// Emphasis in this interface is light, never a louder border.
function thGlowPath(x, y, w, h, c, k){
  const g = TH('glow'), s = (k === undefined) ? 1 : k;
  ctx.save();
  ctx.lineWidth = 1;
  ctx.shadowColor = 'rgba('+g+','+(0.40*s)+')'; ctx.shadowBlur = 6;
  ctx.strokeStyle = 'rgba('+g+','+(0.65*s)+')';
  thChamferPath(x+0.5, y+0.5, w-1, h-1, c); ctx.stroke();
  ctx.shadowColor = 'rgba('+g+','+(0.20*s)+')'; ctx.shadowBlur = 14;
  thChamferPath(x+0.5, y+0.5, w-1, h-1, c); ctx.stroke();
  ctx.restore();
}
// Two short angles, on exactly the two corners the chamfer leaves square, so
// the ornament and the cut belong to the same figure instead of fighting for
// the same corner. This marks the one thing that is active, nothing else.
function thBrackets(x, y, w, h, col, len){
  const L = len || 8;
  ctx.save();
  ctx.strokeStyle = col; ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(x+w-L, y+0.5);   ctx.lineTo(x+w-0.5, y+0.5);   ctx.lineTo(x+w-0.5, y+L);
  ctx.moveTo(x+0.5, y+h-L);   ctx.lineTo(x+0.5, y+h-0.5);   ctx.lineTo(x+L, y+h-0.5);
  ctx.stroke();
  ctx.restore();
}
// A hairline with a short tick dropped at each given offset, like the scale
// on an instrument. Wherever figures stand in columns, this is what ties them
// to their headings without drawing a table grid.
function thScale(x, y, w, ticks, col){
  ctx.save();
  ctx.strokeStyle = col; ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x, y+0.5); ctx.lineTo(x+w, y+0.5);
  for(let i=0;i<ticks.length;i++){
    ctx.moveTo(x+ticks[i]+0.5, y+0.5); ctx.lineTo(x+ticks[i]+0.5, y+4.5);
  }
  ctx.stroke();
  ctx.restore();
}
// Text that cannot leave its cell. Everything here sits in a fixed grid, so
// the one thing a string may not do is grow past the width it was given. Set
// the font first, then ask: what comes back fits, cut and closed with an
// ellipsis if it had to be. This is why a long label can no longer push its
// way out of a button.
function thFit(txt, maxW){
  txt = String(txt);
  if(!(maxW > 0)) return '';
  if(ctx.measureText(txt).width <= maxW) return txt;
  let s = txt;
  while(s.length > 1 && ctx.measureText(s+'\u2026').width > maxW) s = s.slice(0, -1);
  return s + '\u2026';
}
// A panel over the playfield, built from the kit: the sheet that dims the
// battle, the plate, the ring, and a rule under the header. The rule is two
// weights and stops short of the right edge - the one asymmetry in the whole
// vocabulary, so every panel has a reading direction.
function thFrame(x, y, w, h, headH){
  ctx.fillStyle = 'rgba(0,0,0,0.62)';
  ctx.fillRect(0, 0, W, H);
  thPlate(x, y, w, h, thRGBA('panelBack', 0.90), 12);
  thGlowPath(x, y, w, h, 12, 0.9);
  if(headH){
    const run = Math.round(w*0.34);
    ctx.lineWidth = 2; ctx.strokeStyle = TH('accentWarm');
    ctx.beginPath();
    ctx.moveTo(x+12, y+headH-1); ctx.lineTo(x+12+run, y+headH-1);
    ctx.stroke();
    ctx.lineWidth = 1; ctx.strokeStyle = TH('edgeLight');
    ctx.beginPath();
    ctx.moveTo(x+12+run+10, y+headH-0.5); ctx.lineTo(x+w-12, y+headH-0.5);
    ctx.stroke();
  }
}

// Eine Stelle, an der die Weichzeichnung abgeschaltet wird. Sechs
// verstreute Abfragen waeren sechs Gelegenheiten, eine zu vergessen.
function ecoBlur(v){ return ECO.blur ? 0 : v; }

let MAX_RES = ECO.res;      // cap so 4K screens do not allocate absurd canvases
let RES_X = 1, RES_Y = 1;

// One scale for both axes. Two independent scales are what squashed the
// picture as soon as the logical canvas stopped matching the screen's
// ratio. The element is sized and centred here rather than in CSS, so
// getBoundingClientRect returns exactly the drawn area and every pointer
// conversion in the file keeps working unchanged.
// The fullscreen API only answers to a genuine user gesture, which is why
// this hangs off buttons rather than being applied automatically.
function isFullscreen(){
  return !!(document.fullscreenElement || document.webkitFullscreenElement);
}
function fullscreenAvailable(){
  const el = document.documentElement;
  return !!(el.requestFullscreen || el.webkitRequestFullscreen);
}
function toggleFullscreen(){
  try{
    if(isFullscreen()){
      if(document.exitFullscreen) document.exitFullscreen();
      else if(document.webkitExitFullscreen) document.webkitExitFullscreen();
    } else {
      const el = document.documentElement;
      if(el.requestFullscreen) el.requestFullscreen();
      else if(el.webkitRequestFullscreen) el.webkitRequestFullscreen();
    }
  }catch(ex){}
  // The viewport changes a moment after the switch, not during it.
  setTimeout(applyResolution, 120);
  setTimeout(applyResolution, 500);
}

function applyResolution(){
  const availW = window.innerWidth  || 800;
  const availH = window.innerHeight || 500;
  const fit = Math.min(availW/W, availH/H);
  const cssW = Math.max(1, Math.round(W*fit));
  const cssH = Math.max(1, Math.round(H*fit));
  CVS.style.width  = cssW+'px';
  CVS.style.height = cssH+'px';
  CVS.style.left = Math.round((availW-cssW)/2)+'px';
  CVS.style.top  = Math.round((availH-cssH)/2)+'px';
  const dpr = window.devicePixelRatio || 1;
  const res = Math.max(1, Math.min(MAX_RES, cssW*dpr/W));
  RES_X = res; RES_Y = res;
  CVS.width  = Math.round(W*RES_X);
  CVS.height = Math.round(H*RES_Y);
  ctx.setTransform(RES_X, 0, 0, RES_Y, 0, 0);
  ctx.imageSmoothingEnabled = true;
  if('imageSmoothingQuality' in ctx) ctx.imageSmoothingQuality = 'high';
}

// CVS.width = ... setzt die Transformation zurueck; applyResolution setzt
// sie unmittelbar danach wieder. Ein einziger Aufruf reicht also.
function ecoSetRes(v){
  ECO.res = v; MAX_RES = v; ecoSave(); applyResolution();
}

applyResolution();
window.addEventListener('resize', applyResolution);
// A toolbar sliding in or out changes the visual viewport without always
// firing a window resize, which would leave the canvas the wrong height.
if(window.visualViewport){
  window.visualViewport.addEventListener('resize', applyResolution);
  window.visualViewport.addEventListener('scroll', applyResolution);
}
document.addEventListener('fullscreenchange', function(){ setTimeout(applyResolution, 60); });
document.addEventListener('webkitfullscreenchange', function(){ setTimeout(applyResolution, 60); });
window.addEventListener('orientationchange', function(){ setTimeout(applyResolution, 150); });

// A 2D context is not guaranteed to survive. Chromium on Android drops
// the backing store when the GPU process runs short of memory and hands
// back a context reset to defaults: identity transform, empty save stack.
// Calling preventDefault on contextlost asks the browser to restore it,
// and applyResolution puts the device pixel scale back afterwards.
// Sprites and alpha masks are unaffected, they live outside the canvas.
let ctxRestores = 0, ctxNoticeUntil = 0;
CVS.addEventListener('contextlost', function(ev){ ev.preventDefault(); }, false);
CVS.addEventListener('contextrestored', function(){
  ctxRestores++;
  ctxNoticeUntil = Date.now() + 6000;
  applyResolution();
}, false);
document.addEventListener('visibilitychange', function(){
  if(!document.hidden) applyResolution();
});

// Diagnostic only: shows for six seconds that a restore happened, so the
// event can be confirmed on a tablet without a console.
function drawCtxNotice(){
  if(!ctxNoticeUntil || Date.now() > ctxNoticeUntil) return;
  ctx.save();
  ctx.globalAlpha = 0.85;
  ctx.fillStyle = '#ffcc00';
  ctx.font = '10px Courier New';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'bottom';
  ctx.fillText('CTX RESTORED x' + ctxRestores, 6, H - 4);
  ctx.restore();
}
window.addEventListener('orientationchange', function(){ setTimeout(applyResolution, 120); });

// Filled by the packer from the icons folder. Left empty the HUD falls
// back to the symbols it draws itself, so the game still runs unpacked.
const ICON_DATA={};

// Hintergrundkoerper, vom Packer aus den Ordnern planets/ und suns/
// gefuellt. Format je Eintrag: {src, cx, cy, r}. Bei r > 0 ist das Bild
// ein JPEG ohne Alphakanal und die Scheibe wird beim Zeichnen als Kreis
// ausgeschnitten - der Alphakanal eines Planeten ist eine Kreisscheibe
// und damit nichts, was man speichern muesste. Bei r == 0 hat das Bild
// einen echten Alphakanal und wird unveraendert gezeichnet; das gilt fuer
// die Sonnen mit ihrer weichen Korona und fuer den Ringplaneten, dessen
// Ring ein Kreisschnitt abschneiden wuerde.
const PLANET_DATA={};
const SUN_DATA={};

// ── ASSET LOADING ─────────────────────────────────────────────
const IMGS={},NEBS={},ICONS={};
let imgsLoaded=0,nebsLoaded=0,iconsLoaded=0;
for(const [k,src] of Object.entries(ICON_DATA)){
  const img=new Image();img.onload=()=>{ICONS[k]=img;iconsLoaded++;};img.src=src;}
for(const [k,src] of Object.entries(SPR_DATA)){
  const img=new Image();img.onload=()=>{IMGS[k]=img;imgsLoaded++;if(typeof buildMask==='function')buildMask(k);};img.src=src;}
for(const [k,src] of Object.entries(NEB_DATA)){
  const img=new Image();img.onload=()=>{NEBS[k]=img;nebsLoaded++;};img.src=src;}
const BODY_IMG={};
for(const [k,b] of Object.entries(PLANET_DATA)){
  const img=new Image();img.onload=()=>{BODY_IMG[k]=img;};img.src=b.src;}
for(const [k,b] of Object.entries(SUN_DATA)){
  const img=new Image();img.onload=()=>{BODY_IMG[k]=img;};img.src=b.src;}
const TOTAL=Object.keys(SPR_DATA).length+Object.keys(NEB_DATA).length;
const WARP_IMG=document.getElementById('warp_img');
// The vortex used to be an animated WebP. Whether a browser advances the
// frames of an image it is not showing is up to the browser, and it is
// one shared timeline for every vortex on the field either way. The same
// file is now baked into a frame sheet at build time and the frame is
// picked from each ship's own warp progress, so every vortex opens and
// closes with the ship that is coming through it.
// The size of one frame is read off the sheet: nine frames across, so
// a 2304 pixel sheet has 256 pixel frames and the old one 100.
const WARP_COLS=9, WARP_FRAMES=75;
// The Knossos vortex, turquoise. Same frame sheet layout as the normal
// one; should it ever be a single picture instead, it is drawn whole.
const KNOSSOS_WARP_IMG=document.getElementById('warp_knossos_img');
function knossosWarpOk(){
  return !!KNOSSOS_WARP_IMG && KNOSSOS_WARP_IMG.complete && KNOSSOS_WARP_IMG.naturalWidth>0;
}
// The glow behind the vortex, one per kind.
const WARP_GLOW_IMG=document.getElementById('warp_glow_img');
const KNOSSOS_GLOW_IMG=document.getElementById('warp_glow_knossos_img');
function imgReady(im){ return !!im && im.complete && im.naturalWidth>0; }
// One vortex frame at the current transform, centred, WS across, with
// its glow behind it. knossos: the turquoise one of the portal.
const WARP_GLOW_SIZE = 2.0;     // glow width as a multiple of the vortex
// The frames are a loop, played at its own pace from the vortex's own
// starting frame (seed), however long the vortex stays open.
const WARP_FPS = 30;
// Turn of the vortex, radians a second (1.6 is about a quarter turn).
const WARP_SPIN = 1.6;
// Ships come out of the vortex as in FreeSpace, through a side-on oval.
// ?warp=rund: the same with a round vortex; ?warp=alt: the old fade in
// at the centre of the vortex.
const WARP_STYLE = (function(){
  const m = /[?&]warp=(oval|rund|alt)/.exec(location.search);
  if(!m) return 'oval';
  return m[1]==='alt' ? '' : m[1];
})();
const WARP_OVAL = 0.35;   // width of the side-on vortex against its height
// Where ship and vortex are drawn during a FreeSpace style jump, or null
// for the old look. Picture only: the ship's place in the game is e.x/e.y.
//   warp in:  vortex opens, the ship comes out nose first and brakes down
//             to the speed it flies on at, ending with the jump
//   warp out: the ship keeps its speed and speeds up into the vortex
// Where the vortex stands and which way the nose points are fixed at the
// first tick of the jump, so the cut and the vortex stay together.
function fsNose(e){
  // The way the picture faces, turned by ang, then mirrored. Most
  // pictures face right, some big hulls face left.
  const s = (e.flip ? -1 : 1) * (spriteFacing(e.img)==='left' ? -1 : 1), a = e.ang||0;
  return {x: Math.cos(a)*s, y: Math.sin(a)*s};
}
function fsSmall(e){ return e.small || e.type==='fighter' || e.type==='bomber'; }
// Where a ship ends up after the jump. Fighters and bombers are held
// inside the field once they fly (shipBound); one that jumps in on the
// edge is put there at once, so its picture comes out to that spot.
function fsLanding(e){
  if(!fsSmall(e)) return {x: e.x, y: e.y};
  const b = shipBound(e);
  return {x: Math.max(b, Math.min(W-b, e.x)), y: Math.max(HUD_H+b, Math.min(H-b, e.y))};
}
function fsWarp(e){
  // A ship going through the Knossos jumps the same way, into a vortex
  // ahead of her; only its colour is the portal's (drawFsPortals).
  if(!WARP_STYLE || e.type==='asteroid') return null;
  if(!(e.warp>0) && !(e.warpOut>0)) return null;
  const img = IMGS[e.img]; const mW = e.warpMax||100;
  if(!img || mW<=1) return null;
  const out = e.warpOut>0;
  const t = out ? (mW-e.warpOut)/mW : (mW-e.warp)/mW;
  let q = e._fsG;
  if(!q || q.out !== out){
    const f = fsNose(e), L = img.width*e.sc, G = L*0.6;   // G: vortex to ship centre
    const sg = out ? 1 : -1;               // ahead when leaving, behind when coming
    const at = out ? {x: e.x, y: e.y} : fsLanding(e);
    // On the screen edge at the most: what sticks out beyond it cannot be
    // seen, so nothing pops into view when the cut goes.
    const px = Math.max(0, Math.min(W, at.x + sg*f.x*G));
    e._fsG = q = {out, fx: f.x, fy: f.y, L, G, px, py: at.y + sg*f.y*G,
                  x0: e.x, y0: e.y, lx: at.x, ly: at.y, e0: out ? mW-e.warpOut : mW-e.warp, v0: null};
  }
  const fx = q.fx, fy = q.fy, L = q.L, D = q.G + L/2;   // D: the whole way through
  const wS = t<0.30 ? 0.05+0.95*t/0.30 : (t<0.75 ? 1 : Math.max(0, 1-(t-0.75)/0.25));
  // Going out the picture leaves from where the jump began, whatever the
  // game still does with the ship meanwhile.
  let u, vis = true, bx = out ? q.x0 : e.x, by = out ? q.y0 : e.y;
  if(!out){
    const at = fsLanding(e); bx = at.x; by = at.y;
    // Speed wanted at the end, less what the game already moves the ship
    // during the jump - so it carries on without a stop.
    const el = mW - e.warp, dt = el - q.e0;
    const drift = dt > 0 ? ((at.x-q.lx)*fx + (at.y-q.ly)*fy)/dt : 0;
    const v = Math.max(0, fsExitSpeed(e) - drift);
    // Coming out takes the last three quarters of the jump, or less for a
    // fast, short ship: it has to leave at least as fast as it goes on.
    const Dk = Math.min(mW*0.75, v > 0 ? 1.4*D/v : 1e9);
    const c = Math.min(1.45*D, v*Dk);
    const k = 1 - (mW - el)/Dk; if(k<=0) vis = false;
    const w = 1 - Math.min(1, Math.max(0, k));
    u = -D*w*w*w - c*(w - w*w*w);
  } else {
    // Keeps the speed it had and speeds up from there.
    if(q.v0 == null) q.v0 = fsSmall(e)
      ? Math.max(0, (e._fvx1||0)*fx + (e._fvy1||0)*fy)
      : Math.max(0, (e._fvx||0)*fx + (e._fvy||0)*fy);
    const Dk = Math.min(mW*0.75, q.v0 > 0 ? 1.4*D/q.v0 : 1e9);
    const c = Math.min(1.45*D, q.v0*Dk);
    const k = Math.min(1, Math.max(0, (mW - e.warpOut)/Dk)); if(k>=1) vis = false;
    u = c*k + (D-c)*k*k*k;
  }
  return {out, fx, fy, px: q.px, py: q.py, wS, wA: Math.min(1, wS*1.4),
          dx: bx - e.x + fx*u, dy: by - e.y + fy*u, vis};
}
// Speed along the nose a ship flies at right after coming in, in points
// a tick - the same numbers the game moves it by.
function fsExitSpeed(e){
  if(e.transit) return Math.abs(e.transitV||0);
  if(e.crossLeft) return e.crossLeft;     // the Lucifer driving across (M74)
  if(e.escaping) return Math.abs(e.escaping);
  // A fighter flies along its heading, which the picture only follows
  // roughly: what counts is the part along the nose.
  if(fsSmall(e)){ const f = fsNose(e), h = e.head||0;
    return (e.spd || 1.5)*Math.max(0, Math.cos(h)*f.x + Math.sin(h)*f.y); }
  if(allies.indexOf(e) >= 0 || e.targetX == null || !(e.x > e.targetX)) return 0;
  if(e.type==='cruiser') return 0.8;
  if(e.type==='corvette' || e.type==='destroyer') return 0.6;
  if(e.type==='boss') return Math.max(0.25, Math.min(1.5, (e.x-e.targetX)*0.04));
  return 0;
}
// Speed of a ship outside a jump, smoothed, so a jump out can start
// from it. Measured on the picture, per game tick.
function fsTrack(e){
  if(!WARP_STYLE || e.warp>0 || e.warpOut>0) return;
  e._fsG = null;
  if(e._lfc != null && fc > e._lfc){
    const n = fc - e._lfc;
    e._fvx = (e._fvx||0)*0.8 + 0.2*(e.x - e._lx)/n;
    e._fvy = (e._fvy||0)*0.8 + 0.2*(e.y - e._ly)/n;
    e._fvx1 = (e.x - e._lx)/n; e._fvy1 = (e.y - e._ly)/n;
  }
  e._lfc = fc; e._lx = e.x; e._ly = e.y;
}
// The vortex of a ship coming in lives on its own: it opens with the
// jump, stays open until the stern has passed it (also after the jump
// is over and the ship flies on) and only then closes.
let FS_PORTALS = [];
const FS_PORTAL_LINGER = 3;    // seconds after the jump before it closes anyway
function fsPortalOpen(e, g, WS){
  if(e._fsp) return;
  e._fsp = {e, px:g.px, py:g.py, fx:g.fx, fy:g.fy, WS, mW:e.warpMax||100,
            t0:fc - ((e.warpMax||100) - e.warp), closeT:-1};
  FS_PORTALS.push(e._fsp);
}
function fsPortalCleared(p){
  const e = p.e;
  if(e.dead || (enemies.indexOf(e)<0 && allies.indexOf(e)<0)) return true;
  const img = IMGS[e.img]; if(!img) return true;
  const g = (e.warp>0) ? fsWarp(e) : null;
  const cx = e.x + (g ? g.dx : 0), cy = e.y + (g ? g.dy : 0), L = img.width*e.sc;
  // Distance of the stern past the vortex, along the flight path.
  return ((cx - p.fx*L/2) - p.px)*p.fx + ((cy - p.fy*L/2) - p.py)*p.fy > 0;
}
const FS_PORTAL_MAX = 20;      // seconds after the jump, for a ship still moving out
// The ship still moving on along its nose (measured by fsTrack).
function fsPortalMoving(p){
  const e = p.e;
  return ((e._fvx||0)*p.fx + (e._fvy||0)*p.fy) > 0.05;
}
// only: which portals to draw this call (each ship's own just before her,
// v177); without it, all of them.
function drawFsPortals(only){
  for(let i=FS_PORTALS.length-1; i>=0; i--){
    const p = FS_PORTALS[i], age = fc - p.t0;
    if(only && !only(p)) continue;
    if(p.closeT < 0 && age >= p.mW*0.75 && (fsPortalCleared(p) ||
       (age > p.mW + FS_PORTAL_LINGER*TICK_HZ && !fsPortalMoving(p)) ||
       age > p.mW + FS_PORTAL_MAX*TICK_HZ)) p.closeT = fc;
    let wS = Math.min(1, 0.05 + 0.95*age/(p.mW*0.30));
    if(p.closeT >= 0) wS = Math.min(wS, 1 - (fc - p.closeT)/(p.mW*0.25));
    if(wS <= 0){ FS_PORTALS.splice(i,1); if(p.e._fsp===p) p.e._fsp = null; continue; }
    ctx.save();
    ctx.globalAlpha = Math.min(1, wS*1.4);
    ctx.translate(p.px|0, p.py|0);
    if(WARP_STYLE==='oval'){ ctx.rotate(Math.atan2(p.fy, p.fx)); ctx.scale(WARP_OVAL*wS, wS); }
    else ctx.scale(wS, wS);
    drawWarpFrame(warpSeed(p.e), p.WS, !!p.e.portalWarp);
    ctx.restore(); ctx.globalAlpha = 1;
  }
}
// Clip to the side of the vortex the ship is on: in front of it when
// coming out, behind it when going in.
function fsWarpClip(g){
  const B = 5000, sg = g.out ? -1 : 1, tx = -g.fy, ty = g.fx;
  ctx.beginPath();
  ctx.moveTo(g.px+tx*B, g.py+ty*B);
  ctx.lineTo(g.px+tx*B+g.fx*B*sg, g.py+ty*B+g.fy*B*sg);
  ctx.lineTo(g.px-tx*B+g.fx*B*sg, g.py-ty*B+g.fy*B*sg);
  ctx.lineTo(g.px-tx*B, g.py-ty*B);
  ctx.closePath();
  ctx.clip();
}
function warpSeed(o){
  if(o._wseed == null) o._wseed = Math.random()*WARP_FRAMES;
  return o._wseed;
}
// Through the Knossos: the turquoise vortex. Coming in, the arrival
// decides; going out, only a jump at the portal itself. A ship that came in
// through the portal and jumps out anywhere else leaves through a normal
// blue vortex (Silvio, v173: the Rakshasa in M61).
function warpTurquoise(e){
  return e.warpOut>0 ? !!e.portalOut : !!e.portalWarp;
}
function drawWarpFrame(seed, WS, knossos){
  const wF = Math.floor(fc*WARP_FPS/TICK_HZ + (seed||0)) % WARP_FRAMES;
  const sheet = (knossos && imgReady(KNOSSOS_WARP_IMG)) ? KNOSSOS_WARP_IMG : WARP_IMG;
  const glow  = (knossos && imgReady(KNOSSOS_GLOW_IMG)) ? KNOSSOS_GLOW_IMG : WARP_GLOW_IMG;
  if(imgReady(glow)){
    const G = WS*WARP_GLOW_SIZE, op = ctx.globalCompositeOperation;
    ctx.globalCompositeOperation = 'lighter';
    ctx.drawImage(glow, -G/2, -G/2, G, G);
    ctx.globalCompositeOperation = op;
  }
  if(!imgReady(sheet)) return;
  // The vortex turns; the glow above stays level.
  ctx.save();
  ctx.rotate(fc*WARP_SPIN/TICK_HZ + (seed||0));
  // A single picture rather than a sheet is drawn whole.
  if(sheet.naturalWidth < WARP_COLS*40) ctx.drawImage(sheet, -WS/2, -WS/2, WS, WS);
  else {
    const C = sheet.naturalWidth/WARP_COLS;
    ctx.drawImage(sheet, (wF%WARP_COLS)*C, ((wF/WARP_COLS)|0)*C, C, C, -WS/2, -WS/2, WS, WS);
  }
  ctx.restore();
}
const HULL_IMG=document.getElementById('hull_img');
const WARP_SIZE=120; // Rendered size of the vortex in px

function rnd(arr){return arr[Math.floor(Math.random()*arr.length)];}

// ── ALPHA MASKS ─────────────────────────────────────────
// Each sprite gets one downscaled map built once,
// recording only where the ship is opaque. That lets
// us restrict hits to visible hull rather than the
// bounding rectangle. Die Abfrage danach ist ein Feldzugriff.
const MASKS = {};
const MASK_MAX = 256;    // largest edge length of a map
const MASK_MIN_A = 24;   // alpha threshold above which a point counts as hull

function buildMask(key){
  const img = IMGS[key];
  if(!img || !img.width) return null;
  try{
    const f = Math.min(1, MASK_MAX/Math.max(img.width, img.height));
    const mw = Math.max(1, Math.round(img.width*f));
    const mh = Math.max(1, Math.round(img.height*f));
    const c = document.createElement('canvas');
    c.width = mw; c.height = mh;
    const g = c.getContext('2d', {willReadFrequently:true});
    g.drawImage(img, 0, 0, mw, mh);
    const d = g.getImageData(0, 0, mw, mh).data;
    const bits = new Uint8Array(mw*mh);
    for(let i=0, p=3; i<bits.length; i++, p+=4) bits[i] = d[p] > MASK_MIN_A ? 1 : 0;
    const m = {w:mw, h:mh, bits:bits};
    MASKS[key] = m;
    return m;
  }catch(err){
    MASKS[key] = false;   // failed once, do not retry
    return null;
  }
}

function getMask(key){
  const m = MASKS[key];
  if(m === false) return null;
  if(m) return m;
  return buildMask(key);
}

// Does this world point land on visible hull?
// cx,cy = ship centre, sc = scale, flip = mirrored
function onHull(key, cx, cy, sc, flip, wx, wy, ang){
  const img = IMGS[key];
  if(!img) return true;                 // with no image, behave as before
  const m = getMask(key);
  if(!m) return true;                   // no map available, do not block
  const pw = img.width*sc, ph = img.height*sc;
  // Undo the ship rotation first, so the mask lookup happens in
  // sprite space no matter which way the hull is pointing.
  let ox = wx - cx, oy = wy - cy;
  if(ang){
    const ca = Math.cos(-ang), sa = Math.sin(-ang);
    const rx = ox*ca - oy*sa, ry = ox*sa + oy*ca;
    ox = rx; oy = ry;
  }
  let lx = ox / pw + 0.5;               // 0..1 across the sprite width
  const ly = oy / ph + 0.5;
  if(flip) lx = 1 - lx;
  if(lx < 0 || lx >= 1 || ly < 0 || ly >= 1) return false;
  const mx = (lx*m.w)|0, my = (ly*m.h)|0;
  return m.bits[my*m.w + mx] === 1;
}

// A bolt is elongated. Instead of just the centre point, nose, middle
// and tail are tested, or thin structures slip through. The probe runs
// along the round's own heading. Testing across its width instead, as
// this did before, let steeply incoming missiles miss narrow wings.
function probeAxis(b){
  const off = (b.w||8)*0.4;
  const vx = b.vx||0, vy = b.vy||0;
  const sp = Math.hypot(vx, vy);
  if(!sp) return [off, 0];
  return [vx/sp*off, vy/sp*off];
}

function bulletOnHull(e, b){
  if(e && e.ghost) return false;    // shots pass through (M78, v178)
  if(e.type === 'asteroid') return true;
  const ea = e.ang || 0;
  const pr = probeAxis(b);
  return onHull(e.img, e.x, e.y, e.sc, e.flip, b.x+pr[0], b.y+pr[1], ea)
      || onHull(e.img, e.x, e.y, e.sc, e.flip, b.x,       b.y,       ea)
      || onHull(e.img, e.x, e.y, e.sc, e.flip, b.x-pr[0], b.y-pr[1], ea);
}

function bulletOnPlayer(b){
  const sc = playerSc(), fl = player.flip || false;
  const pa = player.ang || 0;
  const pr = probeAxis(b);
  return onHull(player.ship, player.x, player.y, sc, fl, b.x+pr[0], b.y+pr[1], pa)
      || onHull(player.ship, player.x, player.y, sc, fl, b.x,       b.y,       pa)
      || onHull(player.ship, player.x, player.y, sc, fl, b.x-pr[0], b.y-pr[1], pa);
}

// ── DRAW SHIP ─────────────────────────────────────────────────
// ── METALLISCHER LOOK ─────────────────────────────────────────
// Die Sprites sind vorgerendert, das Licht ist eingebacken und dreht sich
// beim Fliegen mit dem Rumpf mit. Genau das ist bei Metall falsch: der
// Glanzpunkt muss stehen bleiben, waehrend sich das Objekt dreht. Beide
// Ebenen hier arbeiten deshalb gegen die Rotation.
const GLINT={};            // je Sprite eine gebackene Glanzkarte
const GLINT_CUT = 168;     // ab dieser Helligkeit zaehlt ein Pixel als Glanz
const GLINT_BASE = 0.10;   // Grundschimmer, auch im ungünstigsten Winkel
const GLINT_SWING = 0.42;  // Zuwachs, wenn die Breitseite ins Licht kommt
const RIM_STRENGTH = 0.55; // Helligkeit der Lichtkante
const RIM_MIN_W = 90;      // erst ab dieser Darstellungsbreite lohnt sie sich

function buildGlint(key){
  const img = IMGS[key];
  if(!img || !img.width){ return null; }
  try{
    const c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    const g = c.getContext('2d', {willReadFrequently:true});
    g.drawImage(img, 0, 0);
    const d = g.getImageData(0, 0, c.width, c.height);
    const p = d.data;
    for(let i=0; i<p.length; i+=4){
      const a = p[i+3];
      if(a < 8){ p[i+3] = 0; continue; }
      const lum = p[i]*0.299 + p[i+1]*0.587 + p[i+2]*0.114;
      let t = (lum-GLINT_CUT)/(255-GLINT_CUT);
      if(t < 0) t = 0;
      // Quadratisch, damit nur die wirklich hellen Stellen stehen bleiben
      // und nicht die halbe Lackierung mitleuchtet.
      p[i]=255; p[i+1]=250; p[i+2]=238; p[i+3] = (a*t*t)|0;
    }
    g.putImageData(d, 0, 0);
    // Weichzeichnen, sonst ist es kein Glanz sondern ein Ausschnitt.
    const c2 = document.createElement('canvas');
    c2.width = c.width; c2.height = c.height;
    const g2 = c2.getContext('2d');
    if('filter' in g2) g2.filter = 'blur(1.2px)';
    g2.drawImage(c, 0, 0);
    GLINT[key] = c2;
    return c2;
  }catch(err){
    GLINT[key] = false;   // einmal gescheitert, nicht noch einmal versuchen
    return null;
  }
}

// Ein einziger wiederverwendeter Puffer fuer alle Lichtkanten. Ein Puffer
// je Schiff und Bild waere auf einem Tablet nicht zu bezahlen.
const RIM_C = document.createElement('canvas');
RIM_C.width = 640; RIM_C.height = 640;
const RIM_G = RIM_C.getContext('2d');

// Die Lichtkante wird gegen die Rotation gerechnet: das Sprite wird ein
// zweites Mal versetzt abgezogen, und was uebrig bleibt, ist eine Sichel
// auf der Lichtseite. Nur fuer Kreuzer und groesser - an einem Jaeger von
// 58 px sind zwei Pixel Kante nicht zu sehen, kosten aber dasselbe.
function drawRimLight(key, cx, cy, scale, flipX, ang){
  const img = IMGS[key];
  if(!img || !img.width) return;
  const w = img.width*scale, h = img.height*scale;
  if(w < RIM_MIN_W) return;
  const span = Math.hypot(w, h);
  if(span > RIM_C.width) return;          // zu gross fuer den Puffer
  const la = lightAngleAt(cx, cy);
  const d = Math.max(1.5, w*0.022);
  const bx = RIM_C.width/2, by = RIM_C.height/2;

  RIM_G.setTransform(1,0,0,1,0,0);
  RIM_G.clearRect(0,0,RIM_C.width,RIM_C.height);
  RIM_G.globalCompositeOperation = 'source-over';
  RIM_G.save();
  RIM_G.translate(bx, by);
  if(ang) RIM_G.rotate(ang);
  if(flipX) RIM_G.scale(-1,1);
  RIM_G.drawImage(img, -w/2, -h/2, w, h);
  RIM_G.restore();

  // Dieselbe Silhouette, vom Licht weg versetzt, wieder abziehen.
  RIM_G.globalCompositeOperation = 'destination-out';
  RIM_G.save();
  RIM_G.translate(bx + Math.cos(la)*d, by + Math.sin(la)*d);
  if(ang) RIM_G.rotate(ang);
  if(flipX) RIM_G.scale(-1,1);
  RIM_G.drawImage(img, -w/2, -h/2, w, h);
  RIM_G.restore();

  // Die Sichel traegt noch die Rumpffarben. Einfarbig einfaerben.
  RIM_G.globalCompositeOperation = 'source-in';
  RIM_G.fillStyle = 'rgba(226,236,255,1)';
  RIM_G.fillRect(0,0,RIM_C.width,RIM_C.height);
  RIM_G.globalCompositeOperation = 'source-over';

  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.globalAlpha = RIM_STRENGTH;
  ctx.drawImage(RIM_C, bx-span/2, by-span/2, span, span,
                (cx-span/2)|0, (cy-span/2)|0, span, span);
  ctx.restore();
}

function drawShip(key,cx,cy,scale,flipX,ang){
  ctx.save();
  const img=IMGS[key];
  if(!img){ctx.restore();return;}
  const w=img.width*scale,h=img.height*scale;
  ctx.translate(cx|0,cy|0);
  // Rotation comes before the mirror, which fixes the order every other
  // helper has to invert. Sprites that face right need no mirror at all
  // once they can rotate, so for flying ships flipX stays false.
  if(ang)ctx.rotate(ang);
  if(flipX)ctx.scale(-1,1);
  ctx.drawImage(img,-w/2,-h/2,w,h);
  // Glanzlicht. Ein langer Rumpf faengt das Licht auf der Breitseite, also
  // zweimal je Umdrehung - daher der doppelte Winkel.
  // Bei abgeschaltetem Glanz wird die Karte gar nicht erst gebacken.
  // buildGlint liest das ganze Sprite per getImageData und legt zwei
  // Puffer an - genau der Ruck beim ersten Auftauchen eines neuen
  // Rumpftyps kommt von dort.
  const gl = ECO.glint ? null
           : ((GLINT[key]!==undefined) ? GLINT[key] : buildGlint(key));
  if(gl){
    const rel = (ang||0) - lightAngleAt(cx, cy);
    const inten = GLINT_BASE + GLINT_SWING*(0.5-0.5*Math.cos(rel*2));
    ctx.globalCompositeOperation='lighter';
    ctx.globalAlpha = inten;
    ctx.drawImage(gl,-w/2,-h/2,w,h);
    ctx.globalAlpha = 1;
  }
  ctx.restore();
  if(!ECO.rim && w >= RIM_MIN_W) drawRimLight(key,cx,cy,scale,flipX,ang);
}

// ── NEBULA BACKGROUND ─────────────────────────────────────────
let nebCur=NEB_NAMES[0],nebNxt=NEB_NAMES[1],nebAlpha=1.0,nebFading=false;
// 0.004 ergab 250 Schritte, also 2.5 s Ueberblendung bei vollem Licht.
// Das dunkle Fenster ist nur 121 Schritte breit (die letzten 63 von
// TRANS_OUT plus die ersten 58 von TRANS_IN), also passt die Blende
// jetzt hinein.
const NEB_FADE_SPEED=0.0084; // ~120 Schritte = 1.2 s

function startNebFade(){
  if(nebFading)return;
  // rollBodies() stand hier. startNebFade() feuert aber bei waveCd < 63,
  // und dort ist die Blende gerade erst angesprungen: near = 0.557, k =
  // 0.016, also 1.5 % Schwaerzung. Die Ueberblendung des Hintergrunds
  // vertraegt das, weil sie sich ueber 120 Schritte zieht; der Wechsel
  // der Koerper ist ein harter Sprung in einem einzigen Bild und war
  // deshalb sichtbar. Er liegt jetzt in nextWave(), im Scheitel.
  // Pick a different random background
  let candidates=NEB_NAMES.filter(n=>n!==nebCur);
  nebNxt=candidates[Math.floor(Math.random()*candidates.length)];
  nebAlpha=1.0;nebFading=true;
}

function tickNebula(){
  tickBodies();
  if(nebFading){
    nebAlpha-=NEB_FADE_SPEED;
    if(nebAlpha<=0){nebAlpha=0;nebCur=nebNxt;nebFading=false;nebAlpha=1.0;}
  }
}

// Die Bilder liegen in 900x450, das Feld ist 800x500. Ein
// drawImage(img,0,0,W,H) hat sie deshalb seit jeher um 25 % gestaucht.
// Bei Nebelschwaden faellt das nicht auf, bei einem Planeten sofort,
// deshalb wird jetzt seitenverhaeltnistreu gefuellt und der Ueberstand
// mittig beschnitten.
function drawNebFit(img, alpha){
  const sc = Math.max(W/img.width, H/img.height);
  const dw = img.width*sc, dh = img.height*sc;
  ctx.globalAlpha = alpha;
  ctx.drawImage(img, (W-dw)/2, (H-dh)/2, dw, dh);
}

// ── SUBSPACE (v170) ─────────────────────────────────────────
// Seen from the side, the tunnel of FreeSpace is a band: Silvio's two noise
// textures run across it at two speeds, squeezed flat, darkened towards
// the walls at top and bottom, and dimmed so the shots stay readable.
// Speeds as in the approved probe (about 140 and 200 px/s).
const SUB_A_IMG = document.getElementById('subspace_a_img');
const SUB_B_IMG = document.getElementById('subspace_b_img');
const SUB_LAYERS = [
  {img:SUB_A_IMG, vx:1.4, vy:0.16, sw:0.8, sh:0.2, a:1.0,  op:'source-over'},
  {img:SUB_B_IMG, vx:2.0, vy:0.34, sw:0.8, sh:0.2, a:0.75, op:'lighter'}
];
// Each layer is built once into a canvas of 2 x 2 tiles - the texture, its
// mirror image across, down and both - at whole-pixel sizes. That sheet
// tiles without a seam and without an overlap (v171, Silvio: a faint line
// where tiles overlapped), and a canvas is not thrown away by the browser
// while the tab is in the background, which is where the flicker after
// switching tabs came from.
function subSheet(L){
  if(L.sheet) return L.sheet;
  if(!imgReady(L.img)) return null;
  const tw = Math.round(L.img.width*L.sw), th = Math.round(L.img.height*L.sh);
  const c = document.createElement('canvas');
  c.width = tw*2; c.height = th*2;
  const g = c.getContext('2d');
  for(let i=0;i<2;i++) for(let j=0;j<2;j++){
    g.save();
    g.translate(i*tw + (i ? tw : 0), j*th + (j ? th : 0));
    g.scale(i ? -1 : 1, j ? -1 : 1);
    g.drawImage(L.img, 0, 0, tw, th);
    g.restore();
  }
  L.sheet = c;
  return c;
}
function subspaceOn(){ return waveMod==='subspace'; }
function drawSubspace(){
  const top = HUD_H, h = H - HUD_H;
  ctx.fillStyle = '#03040c'; ctx.fillRect(0, top, W, h);
  for(const L of SUB_LAYERS){
    const s = subSheet(L);
    if(!s) continue;
    const sw = s.width, sh = s.height;
    const ox = -Math.floor((fc*L.vx) % sw), oy = -Math.floor((fc*L.vy) % sh);
    ctx.save();
    ctx.globalAlpha = L.a; ctx.globalCompositeOperation = L.op;
    for(let x = ox; x < W; x += sw)
      for(let y = top + oy - sh; y < H; y += sh)
        ctx.drawImage(s, x, y);
    ctx.restore();
  }
  // The tube's walls, and a general dimming for readability.
  const g = ctx.createLinearGradient(0, top, 0, H);
  g.addColorStop(0, 'rgba(0,0,0,0.88)'); g.addColorStop(0.2, 'rgba(0,0,0,0.38)');
  g.addColorStop(0.5, 'rgba(0,0,0,0.22)'); g.addColorStop(0.8, 'rgba(0,0,0,0.38)');
  g.addColorStop(1, 'rgba(0,0,0,0.88)');
  ctx.fillStyle = g; ctx.fillRect(0, top, W, h);
}
function drawNebula(){
  const imgA=NEBS[nebCur];
  if(imgA) drawNebFit(imgA, nebFading?nebAlpha:1.0);
  if(nebFading){
    const imgB=NEBS[nebNxt];
    if(imgB) drawNebFit(imgB, 1.0-nebAlpha);
  }
  ctx.globalAlpha=1.0;
}

// ── HINTERGRUNDKOERPER ────────────────────────────────────────
// Null bis zwei Planeten, dazu mit einer gewissen Wahrscheinlichkeit eine
// Sonne. Sie ziehen sehr langsam von rechts nach links und werden beim
// Wellenwechsel zusammen mit dem Hintergrund im Dunkeln getauscht, damit
// der Wechsel nicht sichtbar springt.
const BODY_PLANET_MAX = 2;
const SUN_CHANCE = 0.40;
const PLANET_W_MIN = 150, PLANET_W_MAX = 420;
const SUN_W_MIN = 90, SUN_W_MAX = 900;
// Was groesser erscheint, steht naeher und zieht schneller. Damit ergibt
// sich die Tiefenstaffelung aus der Groesse allein.
const BODY_SPD_MIN = 0.03, BODY_SPD_MAX = 0.13;
// Zwei Bremsen gegen den Kontrastverlust: eine grosse, helle Sonne wuerde
// sonst die Geschosse schlucken, die auf hellem Grund stehen statt auf
// schwarzem.
const SUN_GLOW_MAX = 0.30;
const BODY_DIM_MAX = 0.35;

let bodies = [];

// ── LICHT ─────────────────────────────────────────────────────
// Die Sonne im Hintergrund ist die Lichtquelle, und zwar als Punktlicht:
// jedes Schiff bekommt seinen eigenen Winkel. Ein Jaeger dicht an einer
// grossen Sonne wird damit sichtbar anders angeleuchtet als einer am
// gegenueberliegenden Rand, und genau das verkauft den Effekt. In den
// rund sechs von zehn Wellen ohne Sonne gilt ein fester Ersatzwinkel, der
// die ganze Welle ueber steht; gewechselt wird er unter der Blende.
let lightAng = 0;
let lightSun = null;

function rollLight(){
  lightAng = Math.random()*Math.PI*2;
  lightSun = null;
  for(const b of bodies) if(b.kind==='sun'){ lightSun = b; break; }
}

// Richtung, in die das Licht laeuft. Die beleuchtete Seite liegt also
// entgegengesetzt, bei Winkel + PI.
function lightAngleAt(x, y){
  if(lightSun) return Math.atan2(y-lightSun.y, x-lightSun.x);
  return lightAng;
}

// Gezogen wurde bisher mit Zuruecklegen, also konnte derselbe Planet
// zweimal im selben Bild stehen. Bei 48 Grafiken und zwei Planeten sind
// das rund 2 % je Welle - selten genug, dass es lange nicht auffaellt,
// haeufig genug, dass es irgendwann auffaellt. usedBodies sperrt die
// Auswahl dieser Welle, prevBodies zusaetzlich die der vorherigen, damit
// auch ueber den Wechsel hinweg nichts unmittelbar wiederkehrt.
let usedBodies = [], prevBodies = [];

function makeBody(kind){
  const all = kind==='sun' ? Object.keys(SUN_DATA) : Object.keys(PLANET_DATA);
  if(!all.length) return null;
  let pool = all.filter(function(k){
    return usedBodies.indexOf(k)<0 && prevBodies.indexOf(k)<0;
  });
  // Notausgang, falls jemand den Ordner mit zwei Bildern fuellt: lieber
  // eine Wiederholung als gar kein Planet.
  if(!pool.length) pool = all.filter(function(k){ return usedBodies.indexOf(k)<0; });
  if(!pool.length) pool = all;
  const key = pool[(Math.random()*pool.length)|0];
  usedBodies.push(key);
  const meta = (kind==='sun' ? SUN_DATA : PLANET_DATA)[key];
  const wMin = kind==='sun' ? SUN_W_MIN : PLANET_W_MIN;
  const wMax = kind==='sun' ? SUN_W_MAX : PLANET_W_MAX;
  const w = wMin + Math.random()*(wMax-wMin);
  return {
    key:key, kind:kind, meta:meta, w:w,
    // Darf ueber den Rand hinausragen. Immer vollstaendig im Bild waere
    // die langweiligste aller Anordnungen.
    x: -w*0.3 + Math.random()*(W+w*0.6),
    y: HUD_H - w*0.25 + Math.random()*(H-HUD_H+w*0.5),
    spd: BODY_SPD_MIN + (w/SUN_W_MAX)*(BODY_SPD_MAX-BODY_SPD_MIN)
  };
}

// A place that comes back within a run keeps its sky: the same backdrop,
// the same planets and suns where they stood the first time, the same
// light. The first mission of a scene takes whatever was rolled and
// writes it down; every later one puts it back. A new run starts empty.
let SCENES = {};
function useScene(key){
  const s = SCENES[key];
  if(!s){
    SCENES[key] = {neb: nebFading ? nebNxt : nebCur, light: lightAng,
                   bodies: bodies.map(function(b){ return Object.assign({}, b); })};
    return;
  }
  bodies = s.bodies.map(function(b){ return Object.assign({}, b); });
  lightAng = s.light; lightSun = null;
  for(const b of bodies) if(b.kind==='sun'){ lightSun = b; break; }
  // Under the blackout the backdrop may still be fading over: then the
  // one it fades to is the one that has to be right.
  if(nebFading) nebNxt = s.neb; else nebCur = s.neb;
}

function rollBodies(){
  prevBodies = usedBodies;
  usedBodies = [];
  const out=[];
  const n=(Math.random()*(BODY_PLANET_MAX+1))|0;
  for(let i=0;i<n;i++){ const b=makeBody('planet'); if(b) out.push(b); }
  if(Math.random()<SUN_CHANCE){ const b=makeBody('sun'); if(b) out.push(b); }
  // Klein zuerst zeichnen: der naehere Koerper verdeckt dann den ferneren.
  out.sort(function(a,b){ return a.w-b.w; });
  bodies=out;
  rollLight();
}

function tickBodies(){
  for(const b of bodies){
    b.x -= b.spd;
    if(b.x + b.w < -40){
      // In a wave the set is fixed and a body that leaves comes back round.
      // On the title there is no wave to end, so the same two planets would
      // circle for as long as anyone waits. There they are rolled anew.
      if(GS==='title'){ rollBodies(); return; }
      b.x = W + b.w*0.5 + Math.random()*200;
    }
  }
}

function drawBodies(){
  if(!bodies.length) return;
  // Die verbleibenden 8 %, die die Blende offen laesst, wuerden den
  // Wechsel immer noch durchblitzen lassen. Also gehen die Koerper mit
  // der Blende ganz weg und kommen dahinter neu wieder.
  const bodyA = 1-jumpDark();
  if(bodyA <= 0.01) return;
  ctx.globalAlpha = bodyA;
  let dim = 0;
  for(const b of bodies){
    const img = BODY_IMG[b.key];
    if(!img || !img.complete || !img.naturalWidth) continue;
    const h = b.w*img.height/img.width;
    const x0 = b.x - b.w/2, y0 = b.y - h/2;
    if(b.kind==='sun'){
      dim = Math.max(dim, Math.min(BODY_DIM_MAX, (b.w/SUN_W_MAX)*BODY_DIM_MAX));
      const gr = Math.min(SUN_GLOW_MAX, (b.w/SUN_W_MAX)*SUN_GLOW_MAX + 0.06);
      const g = ctx.createRadialGradient(b.x,b.y,b.w*0.42, b.x,b.y,b.w*1.25);
      g.addColorStop(0,'rgba(255,224,160,'+gr.toFixed(3)+')');
      g.addColorStop(0.55,'rgba(255,180,90,'+(gr*0.35).toFixed(3)+')');
      g.addColorStop(1,'rgba(255,150,60,0)');
      ctx.save();
      ctx.globalCompositeOperation='lighter';
      ctx.fillStyle=g;
      ctx.fillRect(b.x-b.w*1.3, b.y-b.w*1.3, b.w*2.6, b.w*2.6);
      ctx.restore();
    }
    ctx.save();
    if(b.meta.r>0){
      // JPEG ohne Alphakanal: die Scheibe wird als Kreis ausgeschnitten.
      // Radius eine Spur kleiner als gemessen, sonst steht der dunkle
      // Rand des Bildes als Saum ueber.
      const cx = x0 + b.meta.cx*b.w, cy = y0 + b.meta.cy*h;
      ctx.beginPath();
      ctx.arc(cx, cy, b.meta.r*b.w*0.995, 0, Math.PI*2);
      ctx.clip();
    }
    ctx.drawImage(img, x0, y0, b.w, h);
    ctx.restore();
  }
  ctx.globalAlpha = 1;
  if(dim>0){
    ctx.fillStyle='rgba(4,6,12,'+(dim*bodyA).toFixed(3)+')';
    ctx.fillRect(0,0,W,H);
  }
}

// ── PALETTE ───────────────────────────────────────────────────
const P={
  pShot:'#ffffaa',eS:'#ff3300',eSB:'#ff9900',
  eA:'#ffff22',eB:'#ff8800',eC:'#ff2200',
  ui:'#00ff88',uiDk:'#004422',bHP:'#dd44ff',cr:'#ff9900',
};

// ── STARS ─────────────────────────────────────────────────────
const STARS=Array.from({length:120},()=>({
  x:Math.random()*W,y:Math.random()*H,
  spd:0.3+Math.random()*1.2,sz:Math.random()<0.06?2:1,
  clr:['#ffffff','#aaaaff','#ffcccc'][Math.floor(Math.random()*3)],
}));
function tickStars(){for(const s of STARS){s.x-=s.spd;if(s.x<0){s.x=W;s.y=Math.random()*H;}}}
function drawStars(){for(const s of STARS){ctx.fillStyle=s.clr;ctx.globalAlpha=0.7;ctx.fillRect(s.x|0,s.y|0,s.sz,s.sz);}ctx.globalAlpha=1;}

// ── PARTICLES ─────────────────────────────────────────────────
let PARTS=[];
function boom(x,y,n,big){
  for(let i=0;i<n;i++){
    const a=Math.random()*Math.PI*2,spd=big?1.5+Math.random()*4:0.5+Math.random()*2.5;
    const lf=(big?45+Math.random()*55:20+Math.random()*30)|0;
    PARTS.push({x,y,vx:Math.cos(a)*spd,vy:Math.sin(a)*spd,life:lf,ml:lf,
      sz:big?(3+Math.random()*5|0):(2+Math.random()*3|0),
      clr:[P.eA,P.eB,P.eC,'#ffffff'][Math.floor(Math.random()*4)]});
  }
}
function tickParts(){
  if(PARTS.length>900)PARTS.splice(0,PARTS.length-900);
  for(var i=PARTS.length-1;i>=0;i--){
    var p=PARTS[i];
    if(p.ml===0) p.ml=p.life;
    if(p.type==='mag'){
      p.x+=(p.tx-p.x)*0.28; p.y+=(p.ty-p.y)*0.28;
    } else if(p.type==='fb'||p.type==='ring'){
      // static
    } else if(p.free){
      // In space: nothing slows it, nothing pulls it, nothing lifts it.
      p.x+=p.vx; p.y+=p.vy;
    } else {
      p.x+=p.vx||0; p.y+=p.vy||0;
      if(p.vx)p.vx*=0.96; if(p.vy)p.vy*=0.96;
      if(p.type==='smoke') p.y-=0.2; // Smoke drifts upward slightly
    }
    if(--p.life<=0)PARTS.splice(i,1);
  }
}
function drawParts(){
  ctx.save();
  for(var pi=0;pi<PARTS.length;pi++){
    var p=PARTS[pi];
    if(!p.ml||p.ml===0) p.ml=p.life;
    var a=p.ml>0?Math.max(0,Math.min(1,p.life/p.ml)):1;

    if(p.type==='fb'){
      // Feuerball: Radialverlauf (eigenes save/restore)
      var prog=1-(p.life/p.ml);
      var r=Math.max(2, p.maxR*(0.4+0.6*prog));
      try {
        var gr=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r);
        gr.addColorStop(0,'rgba(255,255,255,1)');
        gr.addColorStop(0.25,'rgba(255,240,100,'+a+')');
        gr.addColorStop(0.55,'rgba(255,100,0,'+a*0.85+')');
        gr.addColorStop(0.8,'rgba(180,30,0,'+a*0.5+')');
        gr.addColorStop(1,'rgba(60,0,0,0)');
        ctx.globalAlpha=1;
        ctx.fillStyle=gr;
        ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fill();
      } catch(ex){
        ctx.globalAlpha=a;
        ctx.fillStyle='rgba(255,150,0,0.8)';
        ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fill();
      }
      p.r=r;

    } else if(p.type==='ring'){
      var rp=Math.pow(1-(p.life/p.ml),0.5);
      var rr=p.r+(p.maxR-p.r)*rp;
      ctx.globalAlpha=Math.min(1,a*1.2);
      ctx.strokeStyle='rgba('+p.cr+','+p.cg+','+p.cb+','+Math.min(1,a*1.2)+')';
      ctx.lineWidth=Math.max(0.5,p.lw*(1.5-rp));
      ctx.beginPath();ctx.arc(p.x,p.y,rr,0,Math.PI*2);ctx.stroke();

    } else if(p.type==='mag'){
      // Magnetic particles: stacked circles for glow, no shadowBlur
      ctx.globalAlpha=a*0.35;
      ctx.fillStyle=p.clr||'#ffffff';
      ctx.beginPath();ctx.arc(p.x,p.y,(p.sz||1.5)*2.5,0,Math.PI*2);ctx.fill();
      ctx.globalAlpha=a;
      ctx.fillStyle='#ffffff';
      ctx.beginPath();ctx.arc(p.x,p.y,p.sz||1.5,0,Math.PI*2);ctx.fill();

    } else if(p.type==='deb'){
      // Debris: glow from stacked circles
      var tp=1-(p.life/p.ml);
      var dclr=lerpRGB(p.sr,p.sg,p.sb,p.er,p.eg,p.eb,tp);
      var sz=Math.max(0.8,p.sz*(1-tp*0.4));
      // Outer glow, large and transparent
      ctx.globalAlpha=a*0.25;
      ctx.fillStyle=lerpRGB(255,220,100,200,80,0,tp*0.7);
      ctx.beginPath();ctx.arc(p.x,p.y,sz*1.8,0,Math.PI*2);ctx.fill();
      // Core
      ctx.globalAlpha=a;
      ctx.fillStyle=dclr;
      ctx.beginPath();ctx.arc(p.x,p.y,sz*0.7,0,Math.PI*2);ctx.fill();

    } else if(p.free){
      dmgDrawPart(p, a);

    } else if(p.type==='smoke'){
      var tp2=1-(p.life/p.ml);
      var v=p.v||50;
      ctx.globalAlpha=a*0.3;
      ctx.fillStyle='rgb('+v+','+v+','+v+')';
      var sr2=p.sz*(1+tp2*1.5);
      ctx.beginPath();ctx.arc(p.x,p.y,sr2,0,Math.PI*2);ctx.fill();

    } else {
      // Default: two stacked circles for glow, no shadowBlur
      var sz2=p.sz||2;
      var clr=p.clr||'#ffffff';
      // Outer glow
      ctx.globalAlpha=a*0.28;
      ctx.fillStyle=clr;
      ctx.beginPath();ctx.arc(p.x,p.y,sz2*1.6,0,Math.PI*2);ctx.fill();
      // Core
      ctx.globalAlpha=a;
      ctx.fillStyle=clr;
      ctx.beginPath();ctx.arc(p.x,p.y,sz2*0.6,0,Math.PI*2);ctx.fill();
      // White centre point
      ctx.globalAlpha=a*0.8;
      ctx.fillStyle='#ffffff';
      ctx.beginPath();ctx.arc(p.x,p.y,sz2*0.2,0,Math.PI*2);ctx.fill();
    }
  }
  ctx.restore(); // stellt globalAlpha, lineWidth, etc. wieder her
}


let GS='title';
let paused=false;
// The pause flag has one owner. Panels and the pause button each state
// their own wish below and syncPause() derives the result. Assigning
// paused from several places is what let a panel sit on screen while the
// game kept running: whichever writer ran last won.
let userPaused=false;   // the pause button and the P key
// Every panel that covers the field, by name. A panel adds itself here and
// nowhere else.
//
// This used to be one line that named the panels one by one, and a new
// panel had to be written into it by hand. The rearm panel was not, so it
// opened over a game that carried on running underneath it. Asking whether
// ANY of them is open cannot be forgotten in the same way.
function panelOpen(){
  return !!(shipMenu || callMenu || rearmMenu || settingsOpen);
}
// After a panel closes the game stays stopped until one more tap. However
// the panel was left - a choice made, ESC, a tap outside - the return to
// the fight is the player's to time, not the panel's.
let resumeHold = false;
function syncPause(){
  paused = !!(panelOpen() || resumeHold || userPaused);
}
// Called by every panel as it closes.
function holdResume(){
  if(GS==='playing') resumeHold = true;
  syncPause();
}
// Any tap or key lifts it, and that input does nothing else.
function clearResumeHold(){
  if(!resumeHold) return false;
  resumeHold = false;
  syncPause();
  if(GS==='playing'){ MOUSE.x = player.x; MOUSE.y = player.y; }
  syncCursor();
  return true;
}

const K={};
const MOUSE={x:400,y:250,down:false};
// Ten, because the game asks for far more than it did when this was three
// and hull damage now carries across waves.
const LIVES_START = 10;
const LIVES_ICONS_MAX = 4;   // above this the bar shows a count, not a row
let score=0,lives=LIVES_START,wave=0,fc=0;
// Elapsed time of the current run, in logic steps. Only counts while the
// game is actually running, so a long look at the call menu is not a way
// to a better time once there is a ranking.
let runTime=0;
function fmtTime(t){
  const s=Math.floor(t/TICK_HZ);
  const h=Math.floor(s/3600), m=Math.floor(s/60)%60, sec=s%60;
  const p=function(v){ return (v<10?'0':'')+v; };
  return h ? (h+':'+p(m)+':'+p(sec)) : (p(m)+':'+p(sec));
}
let currentFaction='ntf';
let shipUnlocked=1;     // how many PLAYER_SHIPS entries this run has unlocked
let shipSwapWave=-1;    // wave in which the free switch was spent
let shipMenu=false;     // is the ship menu open?
let gameOverAt=0;       // guards against restarting with the tap that died
let player={x:80,y:250,ang:0,head:0,aimAng:0,flip:false,vx:0,vy:0,
    hp:100,maxHp:100,sh:100,maxSh:100,
    shRecharge:0.22,shDelay:0,shHit:0,fT:0,fR:28,spd:3.2,
    ship:'fiherc',secAmmo:0,secMax:0,secTimer:0,secType:'missile',
    pri:'prometheus',sec:'mx64'};
let pBullets=[],eBullets=[],enemies=[];
let spawnQ=[],spawnT=0,waveOver=false,waveCd=0;

// Capital ship arrival offsets, in steps after the wave starts. They keep
// their own rhythm regardless of what the small craft are doing.
const CAP_FIRST = 260;
// A boss needs a run up. Arriving with the first wing would rob the
// wave of any build, and the escort would be irrelevant.
const CAP_FIRST_BOSS = 900;
const CAP_GAP = {cr:520, co:640, de:760, boss:520};
const WING_FIRST = 90;      // first wing arrives promptly, the wave has to start

// Builds the queue from a wave spec. Fighter and bomber wings alternate on
// the wave's own interval, so a swarm really is dense and a patrol really
// is sparse, instead of both inheriting a span from the capital schedule.
function buildWave(spec){
  const q=[];
  let ct=(spec.caps[0]&&spec.caps[0].indexOf('boss')===0)?CAP_FIRST_BOSS:CAP_FIRST;
  for(let i=0;i<spec.caps.length;i++){
    const type=spec.caps[i];
    const kind=type.split('_')[0];
    const entry={time:ct, type:type};
    // Only the first capital of a Runner wave carries the deadline.
    if(spec.flee && i===0){ entry.flee=spec.flee; fleeTotal++; }
    q.push(entry);
    ct += CAP_GAP[kind] || 560;
  }

  // Wings, alternating fighters and bombers so a wave with both does not
  // deliver all its fighters first and all its bombers afterwards.
  const order=[];
  let fi=spec.fi, bo=spec.bo;
  while(fi>0 || bo>0){
    if(fi>0){ order.push(spec.fiType); fi--; }
    if(bo>0){ order.push(spec.boType); bo--; }
  }
  let wt=WING_FIRST;
  for(const type of order){
    const pool=poolFor(type)||[];
    const spr=pool.length ? pool[(Math.random()*pool.length)|0] : null;
    const wid=++wingSeq;
    const size=WING_MIN+((Math.random()*(WING_MAX-WING_MIN+1))|0);
    const half=(size-1)*WING_SPACING*0.5;
    const lo=HUD_H+26+half, hi=H-26-half;
    const mid=(lo>=hi)?(HUD_H+H)/2:lo+Math.random()*(hi-lo);
    for(let k=0;k<size;k++){
      q.push({time: wt + k*WING_STAGGER, type: type, spr: spr, wing: wid,
              y: mid - half + k*WING_SPACING});
    }
    wt += spec.pause;
  }

  // Asteroids are scenery and keep arriving singly across the whole wave.
  const astSpan=Math.max(wt, ct);
  for(let i=0;i<spec.ast;i++){
    q.push({time: Math.max(30, Math.round(60 + astSpan*(i/Math.max(1,spec.ast))
                                        + (Math.random()-0.5)*120)), type:'ast'});
  }
  return q.sort(function(a,b){ return a.time-b.time; });
}

// ── PERMANENT DAMAGE ON CAPITAL SHIPS (v180, reworked v182) ────
// What a capital ship has taken stays on her, in layers, none of them a
// hole to the stars (Silvio, v181: "huge shapeless holes, slapped on"):
//   scoring     small streaks of carbon where hits land, a little in from
//               the edge they struck, building up;
//   lights      window zones flicker and go dark as the hull goes down;
//   gashes      from 70 % down, several narrow tears along the plating,
//               each small: dark inside, frames showing across it, cracks
//               running off its ends, the lit edge catching the light. A
//               fresh one glows white-orange and cools to a few embers;
//   fire        glows inside the tears, more of it the lower the hull;
//   venting     now and then a tear spits a jet of burning gas; some bleed
//               air as white vapour; smoke and sparks come out of them.
//               All of it flies free in space: it leaves with the ship's
//               own velocity plus the push of the gas and then goes
//               straight on - no drag, no gravity, nothing rising. A ship
//               that turns or changes speed leaves it behind (Silvio, v182);
//   blasts      below 50 % small secondary explosions go off on the hull,
//               more often as she weakens;
//   arcs        below 30 % blue-white discharges jump across the tears;
//   craters     where a subsystem was destroyed: a charred pit, burning;
//   engines     a tear near a nozzle makes it sputter, a damaged engines
//               subsystem makes every flame unsteady, a destroyed one puts
//               them out to a faint afterglow.
// All of it is looks only. Hits are still tested against the undamaged
// shape, and tears keep their distance from subsystems.
// The lasting part is drawn once into a canvas per ship, at the screen's
// resolution, and redrawn only when it changes. The glow on the hull (hot
// edges, embers, fire in the tears, arcs) goes into a second, small canvas,
// refreshed every third frame and cut to the hull. Flame jets, vapour,
// smoke and sparks are free particles in space (dmgEmit).
const DMG_SCORCH_STEP = 0.03;     // share of the hull per new scoring mark
const DMG_GROW = 30;              // steps a mark or a tear takes to open
const DMG_LIGHTS_FROM = 0.80;     // windows start going dark below this
const DMG_GASH_FROM = 0.72, DMG_GASH_TO = 0.15;
const DMG_BLAST_BELOW = 0.50;     // secondary explosions below this
const DMG_ARCS_BELOW = 0.30;
const DMG_NEAR_ENGINE = 0.5;      // tear within this share of the half length
const DMG_K_MAX = 3;
const DMG_MARK_MAX = 6;           // largest scoring mark, game units
const DMG_GASH_MAX = 34;          // longest tear, game units: big hulls get more, not bigger              // finest damage picture, pixels per unit
const DMG_INFO = {};              // per sprite: solid grid, light zones, dark copy
function dmgEligible(e){
  if(!e || e.dead || !IMGS[e.img]) return false;
  return e.type==='cruiser' || e.type==='corvette' || e.type==='destroyer' ||
         e.type==='boss' || e.type==='station' || e.type==='ally' || !!e.platform ||
         (e.side==='ally' && !e.small && e.type!=='freighter' && e.type!=='transport');
}
function dmgSeed(n){ const x = Math.sin(n*12.9898)*43758.5453; return x - Math.floor(x); }
// One look at the sprite: where it is solid, where its lights are.
function dmgInfo(key){
  if(DMG_INFO[key] !== undefined) return DMG_INFO[key];
  const img = IMGS[key];
  try{
    const W = img.width, H = img.height;
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g = c.getContext('2d', {willReadFrequently:true});
    g.drawImage(img, 0, 0);
    const d = g.getImageData(0, 0, W, H), p = d.data;
    const GX = 48, GY = Math.max(8, Math.round(48*H/W));
    const solid = new Float32Array(GX*GY);
    const cnt = new Float32Array(GX*GY);
    // lights: bright, coloured pixels. Their dark copy is what a dead zone shows.
    const dark = g.createImageData(W, H), q = dark.data;
    const ZX = 10, ZY = Math.max(3, Math.round(10*H/W));
    const zl = new Int32Array(ZX*ZY);
    for(let y=0;y<H;y++) for(let x=0;x<W;x++){
      const i = (y*W+x)*4, a = p[i+3];
      const gi = Math.min(GY-1, (y*GY/H)|0)*GX + Math.min(GX-1, (x*GX/W)|0);
      cnt[gi]++; if(a > 150) solid[gi]++;
      const mx = Math.max(p[i],p[i+1],p[i+2]), mn = Math.min(p[i],p[i+1],p[i+2]);
      if(a > 150 && mx > 170 && mx-mn > 40){
        const lum = (p[i]+p[i+1]+p[i+2])/3;
        q[i]=lum*0.32; q[i+1]=lum*0.30; q[i+2]=lum*0.30; q[i+3]=a;
        zl[Math.min(ZY-1,(y*ZY/H)|0)*ZX + Math.min(ZX-1,(x*ZX/W)|0)]++;
      }
    }
    for(let i=0;i<solid.length;i++) solid[i] = cnt[i] ? solid[i]/cnt[i] : 0;
    const dc = document.createElement('canvas'); dc.width = W; dc.height = H;
    dc.getContext('2d').putImageData(dark, 0, 0);
    const zones = [];
    for(let i=0;i<zl.length;i++) if(zl[i] > 3)
      zones.push({sx:(i%ZX)*W/ZX, sy:((i/ZX)|0)*H/ZY, sw:W/ZX, sh:H/ZY, r:dmgSeed(i+W)});
    zones.sort(function(a,b){ return a.r-b.r; });
    DMG_INFO[key] = {GX:GX, GY:GY, solid:solid, dark:dc, zones:zones};
  }catch(err){ DMG_INFO[key] = null; }
  return DMG_INFO[key];
}
// Solid at a point given in fractions of the half extents (-1..1)?
function dmgSolid(inf, u, v, grow){
  const gx = Math.round((u*0.5+0.5)*inf.GX - 0.5), gy = Math.round((v*0.5+0.5)*inf.GY - 0.5);
  for(let j=-grow;j<=grow;j++) for(let i=-grow;i<=grow;i++){
    const x = gx+i, y = gy+j;
    if(x<0||y<0||x>=inf.GX||y>=inf.GY) return false;
    if(inf.solid[y*inf.GX+x] < 0.7) return false;
  }
  return true;
}
function dmgState(e){
  if(e.dm) return e.dm;
  const inf = dmgInfo(e.img); if(!inf) return null;
  const img = IMGS[e.img], big = img.width*e.sc;
  e.dm = {inf:inf, scorch:[], gashes:[], craters:[], acc:0, dirty:true, dead:0, dying:[],
          maxScorch: Math.round(Math.max(10, Math.min(60, big/7))),
          nGash: big < 160 ? 3 : (big < 260 ? 4 : (big < 360 ? 5 : (big < 600 ? 7 : 9))),
          seed: (Math.random()*1e6)|0, can:null, frame:null, born:fc, nextBlast:0};
  return e.dm;
}
// World point to sprite fractions (dx,dy as the mounts use them).
function dmgLocal(e, x, y){
  const img = IMGS[e.img], hw = img.width*e.sc/2, hh = img.height*e.sc/2;
  let px = x-e.x, py = y-e.y; const a = -(e.ang||0);
  if(a){ const c=Math.cos(a), s=Math.sin(a); const qx=px*c-py*s; py=px*s+py*c; px=qx; }
  if(e.flip) px = -px;
  return {u: px/hw, v: py/hh, hw: hw, hh: hh};
}
function dmgWorld(e, u, v){
  const img = IMGS[e.img], hw = img.width*e.sc/2, hh = img.height*e.sc/2;
  let px = u*hw*(e.flip ? -1 : 1), py = v*hh; const a = e.ang||0;
  if(a){ const c=Math.cos(a), s=Math.sin(a); const qx=px*c-py*s; py=px*s+py*c; px=qx; }
  return {x: e.x+px, y: e.y+py};
}
// A hit on the hull: now and then it leaves a streak of scoring.
function dmgHit(e, hx, hy, amount){
  if(!dmgEligible(e) || !e.maxHp || hx==null) return;
  const D = dmgState(e); if(!D) return;
  D.acc += amount/e.maxHp;
  if(D.acc < DMG_SCORCH_STEP) return;
  D.acc -= DMG_SCORCH_STEP;
  const L = dmgLocal(e, hx, hy);
  // In from the edge it struck, by a sixth to a third of the hull's height.
  let px = L.u*L.hw, py = L.v*L.hh;
  const len = Math.hypot(px, py) || 1;
  const dir = Math.atan2(py, px);                 // the way the shot came in
  const depth = (0.15 + Math.random()*0.2) * L.hh*2;
  const k = Math.max(0, 1 - depth/len);
  px *= k; py *= k;
  px += (Math.random()-0.5)*L.hh*0.5; py += (Math.random()-0.5)*L.hh*0.3;
  let u = px/L.hw, v = py/L.hh;
  for(let i=0;i<8 && !dmgSolid(D.inf, u, v, 0);i++){ u *= 0.8; v *= 0.8; }
  if(!dmgSolid(D.inf, u, v, 0)) return;
  // Close to an old one: that one gets darker instead.
  for(const s of D.scorch){
    if(Math.hypot((s.u-u)*L.hw, (s.v-v)*L.hh) < Math.min(s.r*L.hh*2, DMG_MARK_MAX)*0.6){ s.a = Math.min(0.9, s.a+0.15); D.dirty = true; return; }
  }
  if(D.scorch.length >= D.maxScorch) return;
  D.scorch.push({u:u, v:v, r:0.07+Math.random()*0.05, len:1.8+Math.random()*1.6,
                 rot:dir + (Math.random()-0.5)*0.6, a:0.5+Math.random()*0.25, t0:fc, sd:Math.random()*99});
  D.dirty = true;
}
// A subsystem has gone: its crater.
function dmgCrater(e, s){
  if(!dmgEligible(e)) return;
  const D = dmgState(e); if(!D) return;
  const pts = [];
  for(let i=0;i<9;i++){ const a = i/9*Math.PI*2, r = 0.7 + 0.5*Math.random(); pts.push({x:Math.cos(a)*r, y:Math.sin(a)*r*0.75}); }
  D.craters.push({u:s.dx, v:s.dy, t0:fc, sd:Math.random()*99, id:s.id, pts:pts});
  D.dirty = true;
}
function dmgSubsFar(e, u, v, need){
  if(!e.subs) return true;
  const img = IMGS[e.img], hw = img.width*e.sc/2, hh = img.height*e.sc/2;
  for(const s of e.subs) if(Math.hypot((s.dx-u)*hw, (s.dy-v)*hh) < need) return false;
  return true;
}
// The shape of a tear: a narrow jagged slit along the plating, with the
// frames behind it showing across and cracks running off. Offsets are in
// hull heights, about the tear's centre.
function dmgGashShape(L, Wd, rot, sd){
  const n = 9, top = [], bot = [], mid = [];
  const c = Math.cos(rot), s = Math.sin(rot);
  const R = function(x, y){ return {x: x*c - y*s, y: x*s + y*c}; };
  for(let i=0;i<n;i++){
    const t = i/(n-1)*2 - 1;
    const x = t*L/2;
    const cy = Wd*0.35*Math.sin(t*2.3 + sd) * (1 - t*t);
    const half = Wd/2 * Math.pow(Math.max(0, 1 - t*t), 0.55);
    const ja = (0.55 + 0.9*dmgSeed(sd + i*3.1)), jb = (0.55 + 0.9*dmgSeed(sd + i*5.7));
    top.push(R(x, cy - half*ja)); bot.push(R(x, cy + half*jb)); mid.push(R(x, cy));
  }
  // the frames: across the slit where it is wide enough
  const ribs = [];
  for(let i=2;i<n-2;i+=2) ribs.push({a: top[i], b: bot[i]});
  // cracks off the two ends and one off a side
  const cracks = [];
  for(const end of [0, n-1]){
    const p = mid[end], d = end ? 1 : -1;
    const a1 = rot + (d>0 ? 0 : Math.PI) + (dmgSeed(sd+end+11)-0.5)*1.2;
    const l1 = L*(0.15 + 0.2*dmgSeed(sd+end+13));
    const k = {x: p.x + Math.cos(a1)*l1*0.5 + (dmgSeed(sd+end+17)-0.5)*Wd*0.6, y: p.y + Math.sin(a1)*l1*0.5};
    cracks.push([p, k, {x: p.x + Math.cos(a1)*l1, y: p.y + Math.sin(a1)*l1}]);
  }
  const si = 3 + Math.floor(dmgSeed(sd+23)*3), sp = (dmgSeed(sd+29) < 0.5) ? top[si] : bot[si];
  const sa = rot + Math.PI/2 * (sp === top[si] ? -1 : 1) + (dmgSeed(sd+31)-0.5)*0.8;
  cracks.push([sp, {x: sp.x + Math.cos(sa)*Wd*1.4, y: sp.y + Math.sin(sa)*Wd*1.4}]);
  return {top: top, bot: bot, mid: mid, ribs: ribs, cracks: cracks};
}
// Where the next tear goes: a battered stretch of solid hull, clear of the
// subsystems and of the tears already there.
function dmgGashSite(e, D){
  const img = IMGS[e.img], w = img.width*e.sc, h = img.height*e.sc, hw = w/2, hh = h/2;
  const cand = D.scorch.map(function(s){ return {u:s.u, v:s.v}; });
  for(let i=0;i<60;i++) cand.push({u:Math.random()*1.7-0.85, v:Math.random()*1.3-0.65});
  for(let tries=0; tries<3; tries++){
    // a tear is narrow: a fifth to two fifths of the hull's height long,
    // never more than a tenth of her length
    const shrink = Math.pow(0.7, tries);
    const L = Math.min(h*(0.28 + 0.2*Math.random()), w*0.12, DMG_GASH_MAX*(0.75 + 0.25*Math.random())) * shrink;
    const Wd = L*(0.17 + 0.09*Math.random());
    const rot = (Math.random()-0.5)*0.9;        // mostly along the plating
    let best = null, bs = -1;
    for(const c of cand){
      // solid all along the slit, with a little to spare
      let ok = true;
      for(let j=-2;j<=2 && ok;j++){
        const x = (c.u*hw + Math.cos(rot)*L*0.55*j/2)/hw, y = (c.v*hh + Math.sin(rot)*L*0.55*j/2)/hh;
        if(!dmgSolid(D.inf, x, y, 0)) ok = false;
      }
      if(!ok) continue;
      if(!dmgSubsFar(e, c.u, c.v, L*0.5 + 4)) continue;
      if(D.gashes.some(function(g){ return Math.hypot((g.u-c.u)*hw, (g.v-c.v)*hh) < (g.L*h + L)*0.75; })) continue;
      let sc = 0; for(const s of D.scorch) if(Math.hypot((s.u-c.u)*hw, (s.v-c.v)*hh) < L*1.5) sc += s.a;
      sc += Math.random()*0.4;
      if(sc > bs){ bs = sc; best = c; }
    }
    if(best){
      const sd = Math.random()*99;
      const sh = dmgGashShape(L/h, Wd/h, rot, sd);
      // which way is out: away from the hull's long axis
      const nrm = {x: -Math.sin(rot), y: Math.cos(rot)};
      if(nrm.y*best.v < 0 || (Math.abs(best.v) < 0.05 && dmgSeed(sd) < 0.5)){ nrm.x = -nrm.x; nrm.y = -nrm.y; }
      return {u:best.u, v:best.v, L:L/h, Wd:Wd/h, rot:rot, sh:sh, n:nrm, t0:fc, sd:sd,
              vent: dmgSeed(sd+41) < 0.45, jetP: 3 + 4*dmgSeed(sd+43), jetPh: dmgSeed(sd+47)*9};
    }
  }
  return null;
}
// Per frame: lights, tears and the blasts follow the hull.
function dmgTick(e, D){
  const f = Math.max(0, Math.min(1, e.hp/e.maxHp));
  // lights
  const want = Math.round(D.inf.zones.length * Math.max(0, Math.min(1, (DMG_LIGHTS_FROM-f)/0.6)) * 0.85);
  if(D.quiet && want > D.dead){ D.dead = want; D.dirty = true; }
  if(want > D.dead && !D.dying.length){ D.dying.push({i:D.dead, until:fc+45}); D.dead++; }
  if(want < D.dead){ D.dead = want; D.dirty = true; }
  for(let i=D.dying.length-1;i>=0;i--) if(fc >= D.dying[i].until){ D.dying.splice(i,1); D.dirty = true; }
  // tears
  const img = IMGS[e.img], h = img.height*e.sc;
  for(let k=0;k<D.nGash;k++){
    const thr = DMG_GASH_FROM - (DMG_GASH_FROM-DMG_GASH_TO)*(D.nGash>1 ? k/(D.nGash-1) : 0);
    const g = D.gashes[k];
    if(!g && f < thr && D.gashes.length===k){
      const ng = dmgGashSite(e, D);
      if(ng){ ng.thr = thr; D.gashes.push(ng); D.dirty = true;
        if(D.quiet){ ng.t0 = fc - TICK_HZ*20; continue; }   // there before we came
        const w = dmgWorld(e, ng.u, ng.v);
        spawnFireball(w.x, w.y, Math.max(8, ng.L*h*0.7), 18);
        spawnDebris(w.x, w.y, 6, 255,220,170, 200,120,60, false);
        sndPlay('expl_secondary', w.x, 0.45, w.y);
      } else { D.nGash = k; }
      break;
    }
    if(g && f > g.thr + 0.08){ D.gashes.splice(k); D.dirty = true; break; }   // patched up
  }
  // secondary explosions: small, somewhere on her, more often as she weakens
  if(f < DMG_BLAST_BELOW && !D.quiet && !(e.warp > 0) && !(e.warpOut > 0)){
    if(!D.nextBlast) D.nextBlast = fc + TICK_HZ*(1 + Math.random()*3);
    if(fc >= D.nextBlast){
      let u, v;
      if(D.gashes.length && Math.random() < 0.6){ const g = D.gashes[(Math.random()*D.gashes.length)|0]; u = g.u; v = g.v; }
      else { u = Math.random()*1.6-0.8; v = Math.random()*1.2-0.6; }
      if(dmgSolid(D.inf, u, v, 0)){
        const w = dmgWorld(e, u, v);
        spawnFireball(w.x, w.y, h*(0.12 + 0.12*Math.random()), 16);
        spawnDebris(w.x, w.y, 4, 255,230,180, 220,130,60, false);
        sndPlay('expl_secondary', w.x, 0.25, w.y);
      }
      D.nextBlast = fc + TICK_HZ*(1.2 + 6*f + Math.random()*2.5);
    }
  }
  // still opening or still darkening: keep the picture current
  for(const s of D.scorch) if(fc - s.t0 < DMG_GROW) D.dirty = true;
  for(const g of D.gashes) if(fc - g.t0 < DMG_GROW) D.dirty = true;
  for(const c of D.craters) if(fc - c.t0 < DMG_GROW) D.dirty = true;
  D.quiet = false;
}
// The damage a ship already has when she first appears: scoring over the
// hull, and (on the next tick) her lights and tears, all at once and without
// the bursts.
function dmgPreset(e){
  const D = dmgState(e); if(!D) return;
  const lost = 1 - Math.max(0, e.hp)/e.maxHp;
  const n = Math.round(lost/DMG_SCORCH_STEP);
  for(let i=0;i<n*3 && D.scorch.length<Math.min(n, D.maxScorch);i++){
    const u = Math.random()*1.7-0.85, v = Math.random()*1.4-0.7;
    if(!dmgSolid(D.inf, u, v, 0)) continue;
    D.scorch.push({u:u, v:v, r:0.05+Math.random()*0.05, len:1.8+Math.random()*1.6,
                   rot:Math.random()*Math.PI*2, a:0.35+Math.random()*0.25, t0:fc-DMG_GROW, sd:Math.random()*99});
  }
  D.quiet = true; D.dirty = true;
}
// A tear's outline as a path, its width opening over DMG_GROW steps.
function dmgGashPath(g, gs, w, h){
  const o = 0.25 + 0.75*Math.min(1, (fc - gs.t0)/DMG_GROW);
  const cx = (gs.u*0.5+0.5)*w, cy = (gs.v*0.5+0.5)*h, sh = gs.sh;
  const P = function(p, mp){ return {x: cx + (mp.x + (p.x-mp.x)*o)*h, y: cy + (mp.y + (p.y-mp.y)*o)*h}; };
  g.beginPath();
  for(let i=0;i<sh.top.length;i++){ const q = P(sh.top[i], sh.mid[i]); if(i===0) g.moveTo(q.x, q.y); else g.lineTo(q.x, q.y); }
  for(let i=sh.bot.length-1;i>=0;i--){ const q = P(sh.bot[i], sh.mid[i]); g.lineTo(q.x, q.y); }
  g.closePath();
  return P;
}
// The lasting picture: sprite, dark windows, scoring, tears, craters.
function dmgBuild(e, D){
  const img = IMGS[e.img], w = img.width*e.sc, h = img.height*e.sc;
  const k = dmgK(e), pw = Math.max(1, Math.round(w*k)), ph = Math.max(1, Math.round(h*k));
  if(!D.can || D.can.width!==pw || D.can.height!==ph){
    D.can = document.createElement('canvas'); D.can.width = pw; D.can.height = ph;
  }
  D.k = k;
  const g = D.can.getContext('2d');
  g.setTransform(pw/w, 0, 0, ph/h, 0, 0);       // drawn in game units
  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1;
  g.clearRect(0, 0, w, h);
  g.drawImage(img, 0, 0, w, h);
  // dark windows
  const inf = D.inf, kx = w/img.width, ky = h/img.height;
  for(let i=0;i<D.dead && i<inf.zones.length;i++){
    if(D.dying.some(function(d){ return d.i===i; })) continue;
    const z = inf.zones[i];
    g.drawImage(inf.dark, z.sx, z.sy, z.sw, z.sh, z.sx*kx, z.sy*ky, z.sw*kx, z.sh*ky);
  }
  // everything below only where there is hull
  g.globalCompositeOperation = 'source-atop';
  // scoring: a streak of small splashes along the line the shot came in
  for(const s of D.scorch){
    // a hit marks a few metres of plating, whatever the ship's size
    const gt = Math.min(1, (fc - s.t0)/DMG_GROW), r = Math.min(s.r*h, DMG_MARK_MAX);
    const cx = (s.u*0.5+0.5)*w, cy = (s.v*0.5+0.5)*h;
    g.save(); g.translate(cx, cy); g.rotate(s.rot);
    for(let j=0;j<4;j++){
      const t = j/3, rr = r*(1 - 0.55*t)*(0.8 + 0.4*dmgSeed(s.sd+j));
      g.fillStyle = 'rgba(14,10,8,'+(s.a*gt*(1 - 0.5*t)).toFixed(3)+')';
      g.beginPath();
      g.ellipse(-t*r*s.len, (dmgSeed(s.sd+j+5)-0.5)*r*0.6, rr*1.4, rr*0.6, (dmgSeed(s.sd+j+9)-0.5)*0.5, 0, Math.PI*2);
      g.fill();
    }
    // the pit where it struck
    g.fillStyle = 'rgba(4,3,2,'+(0.8*gt).toFixed(3)+')';
    g.beginPath(); g.arc(0, 0, Math.max(0.35, r*0.22), 0, Math.PI*2); g.fill();
    g.restore();
  }
  const unit = Math.max(0.35, 1/k);              // about one screen pixel
  // tears
  for(const gs of D.gashes){
    const cx = (gs.u*0.5+0.5)*w, cy = (gs.v*0.5+0.5)*h, L = gs.L*h, Wd = gs.Wd*h;
    // soot round it, stretched along it
    g.save(); g.translate(cx, cy); g.rotate(gs.rot); g.scale(1, (Wd*2.6)/(L*0.8));
    const gr = g.createRadialGradient(0, 0, L*0.15, 0, 0, L*0.8);
    gr.addColorStop(0, 'rgba(10,7,5,0.6)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(0, 0, L*0.8, 0, Math.PI*2); g.fill();
    g.restore();
    // cracks running off it
    g.strokeStyle = 'rgba(12,9,7,0.9)'; g.lineWidth = unit; g.lineCap = 'round'; g.lineJoin = 'round';
    for(const cr of gs.sh.cracks){
      g.beginPath(); g.moveTo(cx+cr[0].x*h, cy+cr[0].y*h);
      for(let i=1;i<cr.length;i++) g.lineTo(cx+cr[i].x*h, cy+cr[i].y*h);
      g.stroke();
    }
    // the dark inside
    const P = dmgGashPath(g, gs, w, h);
    g.fillStyle = '#0b0908'; g.fill();
    // frames behind it, faintly lit
    g.strokeStyle = 'rgba(70,62,54,0.9)'; g.lineWidth = Math.max(unit, Wd*0.12);
    for(const rb of gs.sh.ribs){
      const mi = gs.sh.mid[gs.sh.ribs.indexOf(rb)*2+2];
      const a = P(rb.a, mi), b = P(rb.b, mi);
      g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
    }
    // the torn lip: the upper edge catches the light, the lower is in shadow
    g.lineWidth = unit;
    g.strokeStyle = 'rgba(205,198,186,0.55)';
    g.beginPath();
    gs.sh.top.forEach(function(p, i){ const q = P(p, gs.sh.mid[i]); if(i) g.lineTo(q.x, q.y-unit*0.6); else g.moveTo(q.x, q.y-unit*0.6); });
    g.stroke();
    g.strokeStyle = 'rgba(0,0,0,0.7)';
    g.beginPath();
    gs.sh.bot.forEach(function(p, i){ const q = P(p, gs.sh.mid[i]); if(i) g.lineTo(q.x, q.y+unit*0.6); else g.moveTo(q.x, q.y+unit*0.6); });
    g.stroke();
  }
  // craters: a charred pit
  for(const c of D.craters){
    const gt = Math.min(1, (fc - c.t0)/DMG_GROW);
    const cx = (c.u*0.5+0.5)*w, cy = (c.v*0.5+0.5)*h, r = h*0.07*(0.4+0.6*gt);
    const gr = g.createRadialGradient(cx, cy, r*0.5, cx, cy, r*2.2);
    gr.addColorStop(0, 'rgba(10,7,5,0.7)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(cx, cy, r*2.2, 0, Math.PI*2); g.fill();
    g.fillStyle = '#0b0908'; g.beginPath();
    c.pts.forEach(function(p, i){ if(i) g.lineTo(cx+p.x*r, cy+p.y*r); else g.moveTo(cx+p.x*r, cy+p.y*r); });
    g.closePath(); g.fill();
    g.strokeStyle = 'rgba(205,198,186,0.45)'; g.lineWidth = unit; g.stroke();
  }
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalCompositeOperation = 'source-over';
  D.dirty = false; D.built = fc;
}
function dmgK(e){
  return Math.max(1, Math.min(RES_X, 1/Math.max(0.05, e.sc), DMG_K_MAX));
}
// The ship, with what she has taken. Same transform as drawShip().
function drawShipE(e, cx, cy, scale, flipX, ang){
  // A ship that comes on already hurt (a mission sets her hull low) brings
  // her damage with her: marked and torn from the first frame, quietly.
  if(!e.dm && e.maxHp && e.hp < e.maxHp*0.95 && dmgEligible(e)) dmgPreset(e);
  const D = e.dm;
  if(!D || !dmgEligible(e) || (!D.scorch.length && !D.gashes.length && !D.craters.length && !D.dead && !D.dying.length)){
    if(D) dmgTick(e, D);
    drawShip(e.img, cx, cy, scale, flipX, ang); return;
  }
  dmgTick(e, D);
  // the screen resolution changed (window, fullscreen): rebuild at the new one
  if(D.can && D.k !== dmgK(e)) D.dirty = true;
  if(D.dirty && (fc - (D.built||-99) >= 3 || !D.can || D.k !== dmgK(e))) dmgBuild(e, D);
  const img = IMGS[e.img];
  const w = img.width*scale, h = img.height*scale;
  ctx.save();
  ctx.translate(cx|0, cy|0);
  if(ang) ctx.rotate(ang);
  if(flipX) ctx.scale(-1, 1);
  // The gloss as on any hull, laid on the damaged picture, in a frame
  // canvas of her own.
  const gl = ECO.glint ? null : ((GLINT[e.img]!==undefined) ? GLINT[e.img] : buildGlint(e.img));
  if(gl){
    const cw = D.can.width, ch = D.can.height;
    if(!D.frame || D.frame.width!==cw || D.frame.height!==ch){
      D.frame = document.createElement('canvas'); D.frame.width = cw; D.frame.height = ch;
    }
    // Recomposed only when the picture or the light on it has changed.
    const rel = (ang||0) - lightAngleAt(cx, cy);
    const gi = Math.round((GLINT_BASE + GLINT_SWING*(0.5-0.5*Math.cos(rel*2)))*50)/50;
    if(D.fBuilt !== D.built || D.fGi !== gi){
      const g = D.frame.getContext('2d');
      g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1;
      g.clearRect(0, 0, cw, ch);
      g.drawImage(D.can, 0, 0);
      g.globalCompositeOperation = 'lighter';
      g.globalAlpha = gi;
      g.drawImage(gl, 0, 0, cw, ch);
      g.globalAlpha = 1;
      g.globalCompositeOperation = 'source-over';
      D.fBuilt = D.built; D.fGi = gi;
    }
    ctx.drawImage(D.frame, -w/2, -h/2, w, h);
  } else ctx.drawImage(D.can, -w/2, -h/2, w, h);
  // the lights on their way out: flickering
  for(const d of D.dying){
    if(dmgSeed(fc*0.37 + d.i) < 0.5) continue;
    const z = D.inf.zones[d.i]; if(!z) continue;
    const kx = w/img.width, ky = h/img.height;
    ctx.drawImage(D.inf.dark, z.sx, z.sy, z.sw, z.sh, -w/2+z.sx*kx, -h/2+z.sy*ky, z.sw*kx, z.sh*ky);
  }
  ctx.restore();
  if(!ECO.rim && w >= RIM_MIN_W) drawRimLight(e.img, cx, cy, scale, flipX, ang);
  dmgFx(e, D, cx, cy, w, h, flipX, ang);
}
// One soft glow, drawn once and stamped: cheaper than a gradient a frame.
let DMG_GLOW = null;
function dmgGlow(){
  if(DMG_GLOW) return DMG_GLOW;
  const c = document.createElement('canvas'); c.width = c.height = 32;
  const g = c.getContext('2d'), gr = g.createRadialGradient(16,16,0,16,16,16);
  gr.addColorStop(0, 'rgba(255,215,140,1)'); gr.addColorStop(0.4, 'rgba(255,140,40,0.6)');
  gr.addColorStop(1, 'rgba(255,80,10,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 32, 32);
  return (DMG_GLOW = c);
}
function dmgStamp(g, x, y, r, a){
  if(a <= 0.01 || r <= 0.2) return;
  g.globalAlpha = Math.min(1, a);
  g.drawImage(dmgGlow(), x-r, y-r, r*2, r*2);
}
// The glow on the hull: one small canvas over the damaged stretch,
// refreshed every third frame and stamped every frame.
function dmgFx(e, D, cx, cy, w, h, flipX, ang){
  if(!D.gashes.length && !D.craters.length) return;
  const unit = Math.max(1, h/40);
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  const take = function(u, v, r){
    const x = (u*0.5+0.5)*w, y = (v*0.5+0.5)*h;
    x0 = Math.min(x0, x - r - unit*14); x1 = Math.max(x1, x + r + unit*4);
    y0 = Math.min(y0, y - r - unit*6); y1 = Math.max(y1, y + r + unit*4);
  };
  for(const gs of D.gashes) take(gs.u, gs.v, gs.L*h*0.7);
  for(const c of D.craters) take(c.u, c.v, h*0.12);
  x0 = Math.floor(x0); y0 = Math.floor(y0);
  const fw = Math.ceil(x1 - x0), fh = Math.ceil(y1 - y0);   // game units
  const k = D.k || 1, cw = Math.ceil(fw*k), ch = Math.ceil(fh*k);
  if(!D.fxL || D.fxL.width!==cw || D.fxL.height!==ch){
    D.fxL = document.createElement('canvas'); D.fxL.width = cw; D.fxL.height = ch;
    D.fxT = -99;
  }
  const opening = D.gashes.some(function(gs){ return fc - gs.t0 < DMG_GROW; });
  if(fc - D.fxT >= 3 || opening){
    const gl = D.fxL.getContext('2d');
    gl.setTransform(1,0,0,1,0,0);
    gl.globalCompositeOperation = 'source-over'; gl.globalAlpha = 1;
    gl.clearRect(0, 0, cw, ch);
    gl.setTransform(cw/fw, 0, 0, ch/fh, -x0*cw/fw, -y0*ch/fh);
    dmgFxDraw(gl, e, D, w, h);
    // Glow only where there is hull: cut to the damaged picture.
    gl.globalCompositeOperation = 'destination-in'; gl.globalAlpha = 1;
    gl.drawImage(D.can, 0, 0, w, h);
    gl.globalCompositeOperation = 'source-over'; gl.globalAlpha = 1;
    D.fxT = fc;
  }
  ctx.save();
  ctx.translate(cx|0, cy|0);
  if(ang) ctx.rotate(ang);
  if(flipX) ctx.scale(-1, 1);
  ctx.drawImage(D.fxL, -w/2+x0, -h/2+y0, fw, fh);
  ctx.restore();
}
// On the hull: hot edges cooling to embers, fire inside the tears, arcs.
function dmgFxDraw(g, e, D, w, h){
  const t = fc/TICK_HZ, f = e.hp/e.maxHp;
  const px = Math.max(0.35, 1/(D.k||1));
  g.globalCompositeOperation = 'lighter';
  g.lineCap = 'round'; g.lineJoin = 'round';
  for(const gs of D.gashes){
    const age = (fc - gs.t0)/TICK_HZ, heat = Math.exp(-age/2.5);
    const cx = (gs.u*0.5+0.5)*w, cy = (gs.v*0.5+0.5)*h, Wd = gs.Wd*h, L = gs.L*h;
    const P = dmgGashPath(g, gs, w, h);
    // fresh: the whole edge white-orange, cooling over a few seconds
    if(heat > 0.03){
      g.strokeStyle = 'rgba(255,'+(150+100*heat|0)+','+(60+170*heat|0)+','+(0.95*heat).toFixed(3)+')';
      g.lineWidth = px*2; g.stroke();
    }
    // later: a few stretches of the edge still glowing, wandering slowly
    const edge = gs.sh.top.concat(gs.sh.bot);
    for(let i=0;i<edge.length-1;i++){
      if(i === gs.sh.top.length-1) continue;
      const b = Math.pow(Math.max(0, Math.sin(i*1.9 + gs.sd + t*0.6)), 6) * 0.75;
      if(b < 0.05) continue;
      const mi = gs.sh.mid[i < gs.sh.top.length ? i : i - gs.sh.top.length];
      const mj = gs.sh.mid[(i+1) < gs.sh.top.length ? i+1 : i+1 - gs.sh.top.length];
      const a = P(edge[i], mi), c = P(edge[i+1], mj);
      g.strokeStyle = 'rgba(255,110,30,'+b.toFixed(3)+')'; g.lineWidth = px*1.5;
      g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(c.x, c.y); g.stroke();
    }
    // fire inside: small tongues flickering along it, more as she weakens
    const nf = f < 0.3 ? 3 : (f < 0.55 ? 2 : 1);
    for(let j=0;j<nf;j++){
      const q = gs.sh.mid[2 + ((j*3 + (gs.sd|0)) % (gs.sh.mid.length-4))];
      const fl = 0.5 + 0.5*Math.sin(t*(9 + j*3) + gs.sd*3 + j) * dmgSeed(((fc/2)|0) + j + gs.sd);
      dmgStamp(g, cx + q.x*h, cy + q.y*h, Wd*(0.55 + 0.45*fl), 0.25 + 0.4*fl);
    }
    // below 30 %: discharges across the tear
    if(f < DMG_ARCS_BELOW && dmgSeed(((fc/3)|0) + gs.sd*7) > 0.72){
      const a = gs.sh.top[2 + ((fc/3|0) % 4)], b = gs.sh.bot[2 + ((fc/5|0) % 4)];
      g.strokeStyle = 'rgba(175,205,255,0.95)'; g.lineWidth = px*1.2;
      g.beginPath(); g.moveTo(cx + a.x*h, cy + a.y*h - Wd*0.6);
      for(let s=1;s<5;s++){
        const tt = s/5;
        g.lineTo(cx + (a.x + (b.x-a.x)*tt)*h + (dmgSeed(fc+s)-0.5)*Wd*1.4,
                 cy + (a.y + (b.y-a.y)*tt)*h + (dmgSeed(fc+s+7)-0.5)*Wd*1.4);
      }
      g.lineTo(cx + b.x*h, cy + b.y*h + Wd*0.6); g.stroke();
    }
  }
  for(const c of D.craters){
    const ccx = (c.u*0.5+0.5)*w, ccy = (c.v*0.5+0.5)*h, r = h*0.05;
    const fl = 0.5 + 0.5*Math.sin(t*7 + c.sd) * dmgSeed(((fc/2)|0) + c.sd);
    dmgStamp(g, ccx, ccy, r*(1 + 0.5*fl), 0.4 + 0.4*fl);
  }
  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1;
}
// What leaves a tear: flame, vapour, smoke and sparks, as free particles in
// space (Silvio, v182). Each starts with the ship's own velocity at that
// moment plus the push of the gas, then flies straight on - no drag, no
// gravity, nothing rising. Flying steadily, a plume stays with the ship;
// turning, speeding up or braking, she leaves it behind and it bends.
// Called once per tick for every ship that carries damage.
function dmgEmitAll(){
  for(let i=0;i<enemies.length;i++) if(enemies[i].dm) dmgEmit(enemies[i]);
  for(let i=0;i<allies.length;i++) if(allies[i].dm) dmgEmit(allies[i]);
}
function dmgEmit(e){
  const D = e.dm;
  // the ship's velocity over the last tick
  let svx = (D.lx==null) ? 0 : e.x - D.lx, svy = (D.ly==null) ? 0 : e.y - D.ly;
  D.lx = e.x; D.ly = e.y;
  if(Math.abs(svx) > 30 || Math.abs(svy) > 30){ svx = 0; svy = 0; }   // a jump, not flight
  if(e.dead || e.warp > 0 || e.warpOut > 0 || !IMGS[e.img]) return;
  if(!D.gashes.length && !D.craters.length) return;
  const f = Math.max(0, e.hp/e.maxHp), t = fc/TICK_HZ;
  const h = IMGS[e.img].height*e.sc;
  const fl = e.flip ? -1 : 1, ca = Math.cos(e.ang||0), sa = Math.sin(e.ang||0);
  const dirW = function(x, y){ x *= fl; return {x: x*ca - y*sa, y: x*sa + y*ca}; };
  const push = function(o){ o.free = true; o.ml = o.life; PARTS.push(o); };
  for(const gs of D.gashes){
    if(fc - gs.t0 < DMG_GROW) continue;
    const at = dmgWorld(e, gs.u, gs.v), n = dirW(gs.n.x, gs.n.y), q = {x: -n.y, y: n.x};
    const L = gs.L*h, Wd = gs.Wd*h, age = (fc - gs.t0)/TICK_HZ;
    const out = function(speed, spread){
      const k = (Math.random()-0.5)*spread;
      return {vx: svx + (n.x + q.x*k)*speed, vy: svy + (n.y + q.y*k)*speed};
    };
    // a jet of flame now and then, oftener as she weakens: burning gas
    // driven out, opening into a cone and gone in a moment
    const per = gs.jetP*(0.5 + f), ph = (t + gs.jetPh) % per;
    if(ph < 0.6 && (fc & 1) === 0){
      const env = Math.sin(ph/0.6*Math.PI);
      const v = out(L*0.07*(0.7 + 0.5*Math.random())*(0.5 + 0.5*env), 0.5);
      push({type:'dfl', x: at.x, y: at.y, vx: v.vx, vy: v.vy, life: 18 + (Math.random()*12|0),
            r0: Math.min(Wd*0.7, 5)*env + 0.6, r1: Math.min(Wd*(1.6 + 1.0*env), 12)});
    }
    // air bleeding out: strong at first, later in breaths
    if(gs.vent){
      const str = age < 12 ? 1 - age/14 : 0.3*Math.max(0, Math.sin(t*0.8 + gs.sd));
      if(str > 0.05 && fc % 3 === 0 && Math.random() < str + 0.2){
        const v = out(L*0.016*(0.7 + 0.6*Math.random()), 0.7);
        push({type:'dvap', x: at.x, y: at.y, vx: v.vx, vy: v.vy, life: 45 + (Math.random()*35|0),
              r0: Math.min(Wd*0.4, 2.5), r1: Math.min(Wd*(1.3 + 0.6*Math.random()), 9), al: 0.38*Math.min(1, str + 0.2)});
      }
    }
    // smoke from what burns inside, pushed out slowly
    if(fc % 12 === (gs.sd|0) % 12){
      const v = out(L*0.006*(0.6 + 0.8*Math.random()), 1.2);
      push({type:'dsmk', x: at.x, y: at.y, vx: v.vx, vy: v.vy, life: 90 + (Math.random()*50|0),
            r0: Math.min(Wd*0.5, 3), r1: Math.min(Wd*(1.4 + 0.8*Math.random()), 10), al: 0.24});
    }
    // sparks: a few bright flecks thrown out, now and then
    if(f < 0.6 && Math.random() < 0.025){
      for(let j=0;j<2+(Math.random()*3|0);j++){
        const v = out(L*(0.09 + 0.08*Math.random()), 1.6);
        push({type:'dspk', x: at.x, y: at.y, vx: v.vx, vy: v.vy, svx: svx, svy: svy,
              life: 25 + (Math.random()*25|0), w: Math.max(0.5, Wd*0.12)});
      }
    }
  }
  for(const c of D.craters){
    if(fc % 12 !== (c.sd|0) % 12) continue;
    const at = dmgWorld(e, c.u, c.v), a = Math.random()*Math.PI*2, sp = Math.min(h*0.002, 0.25)*(0.5 + Math.random());
    push({type:'dsmk', x: at.x, y: at.y, vx: svx + Math.cos(a)*sp, vy: svy + Math.sin(a)*sp,
          life: 90 + (Math.random()*50|0), r0: Math.min(h*0.02, 3), r1: Math.min(h*0.06, 10), al: 0.24});
  }
}
function dmgDrawPart(p, a){
  const k = 1 - a;                               // 0 new .. 1 gone
  const r = p.r0 + (p.r1 - p.r0)*Math.sqrt(k);
  if(p.type==='dfl'){
    // white-yellow at the start, orange, then a dull red as it thins
    ctx.globalCompositeOperation = 'lighter';
    dmgStamp(ctx, p.x, p.y, r, a*a*0.95);
    if(k < 0.35) dmgStamp(ctx, p.x, p.y, r*0.45, (0.35 - k)*2.4);
    ctx.globalCompositeOperation = 'source-over';
  } else if(p.type==='dvap'){
    ctx.globalAlpha = p.al*a;
    ctx.fillStyle = '#d8dee6';
    ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI*2); ctx.fill();
  } else if(p.type==='dsmk'){
    ctx.globalAlpha = p.al*a*Math.min(1, k*8);
    ctx.fillStyle = '#3c3936';
    ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI*2); ctx.fill();
  } else if(p.type==='dspk'){
    // a short streak along its path relative to the ship it left
    const rx = p.vx - p.svx, ry = p.vy - p.svy;
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = a;
    ctx.strokeStyle = 'rgb(255,'+(140 + 100*a|0)+',90)';
    ctx.lineWidth = p.w;
    ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x - rx*1.5, p.y - ry*1.5); ctx.stroke();
    ctx.globalCompositeOperation = 'source-over';
  }
  ctx.globalAlpha = 1;
}
// How a nozzle burns, given the damage (thruster t of ship e, index i).
function dmgThrust(e, t, i){
  if(!e) return 1;
  let k = 1;
  const en = e.subs ? e.subs.find(function(s){ return s.id==='engines'; }) : null;
  if(en){
    if(en.dead){
      // out: a faint afterglow, and a spark now and then
      k = 0.10 + (dmgSeed(((fc/5)|0) + i*7) > 0.93 ? 0.35 : 0);
      return k;
    }
    const lost = 1 - Math.max(0, en.hp)/en.maxHp;
    if(lost > 0.05) k *= 1 - lost*0.65*dmgSeed(((fc/3)|0) + i*11);
  }
  const D = e.dm;
  if(D && D.gashes.length){
    for(const gs of D.gashes){
      if(Math.hypot(gs.u - t.dx, gs.v - t.dy) < DMG_NEAR_ENGINE*2){
        // sputtering: now low, now gone for a moment
        const r = dmgSeed(((fc/4)|0) + i*13 + gs.sd);
        k *= r < 0.22 ? 0.08 : (0.55 + 0.45*r);
        break;
      }
    }
  }
  return k;
}
