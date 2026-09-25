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
const WARP_COLS=9, WARP_CELL=100, WARP_FRAMES=75;
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
  if(PARTS.length>600)PARTS.splice(0,PARTS.length-600);
  for(var i=PARTS.length-1;i>=0;i--){
    var p=PARTS[i];
    if(p.ml===0) p.ml=p.life;
    if(p.type==='mag'){
      p.x+=(p.tx-p.x)*0.28; p.y+=(p.ty-p.y)*0.28;
    } else if(p.type==='fb'||p.type==='ring'){
      // static
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
