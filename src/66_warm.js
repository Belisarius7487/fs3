// ── MISSION WARM-UP (F104, v307) ─────────────────────────────
// Silvio's lag log of v306: the first seconds of M6 stutter, later the same
// mission is smooth. Everything that stuttered was work done for the first
// time: the jump vortex of the Galatea, her hit map and damage tables, the
// rim light of the rocks, the missile trail and the smoke sheet.
// v308: the rim light is one sheet per rock shape (rockLightSheet). In v307
// it was 1152 small canvases, and handing those to the graphics card took
// 0.7 s on Silvio's PC - a black second at the start of M6.
// All of that is done here once, in the darkest picture of the fade-in
// (arriveT = TRANS_IN, the field is 92 % black), where a longer picture is
// not seen.
// nextWave() only asks for it; the work is done by the next draw(), right
// after the picture has been cleared. Copies drawn before that clear (from
// update()) may be thrown away by the browser unseen, because the clear
// covers the whole canvas; drawn after it they reach the graphics card.
// &warm=0 switches it off, to compare.
const WARM_ON = urlNum('warm', 1, 0, 1);
let WARM_DUE = false;
let WARM_LAST = null;             // what the last warm-up did (tests, lag log)
// unit classes whose hulls carry a hit map and a damage picture
const WARM_BIG = {cr:1, co:1, de:1, sd:1, ic:1, in:1};
function missionWarmAsk(){ WARM_DUE = !!WARM_ON; }
function missionWarm(){
  WARM_DUE = false;
  if(typeof document === 'undefined' || typeof ctx === 'undefined') return null;
  const t0 = (typeof performance !== 'undefined') ? performance.now() : 0;
  const R = {hulls: 0, masks: 0, dmg: 0, lights: 0, vortex: false, srcs: 0, ms: 0};
  const srcs = [];                // everything the 2D canvas draws from later
  // the scenery again: its copies from nextWave() lie before the clear
  try{ sceneWarm(); }catch(err){}

  const def = (typeof SCRIPT_WAVES !== 'undefined' && !FS1_MODE && !TEST_MODE) ? SCRIPT_WAVES[wave] : null;
  const us = (def && def.u) || [];

  // 1. the capital ships of this mission, those that come later too:
  //    the hit map from the model and the tables of the damage picture
  const seen = {};
  for(const u of us){
    const k = u.spr;
    if(!k || seen[k] || !WARM_BIG[u.c]) continue;
    seen[k] = 1;
    const img = IMGS[k];
    if(!img || !img.width) continue;
    R.hulls++;
    try{
      const mk = f3dKey({img: k});
      if(mk && !f3dSmall(mk) && !F3D_MASKED[k] && f3dReadyLevel(mk)){
        f3dMask(k, mk);
        if(F3D_MASKED[k]) R.masks++;
      }
    }catch(err){}
    try{
      if(DMG_INFO[k] === undefined && dmgInfo(k)) R.dmg++;
    }catch(err){}
  }
  try{ if(R.hulls) srcs.push(dmgGlow()); }catch(err){}

  // 2. the jump vortex: once through the 3D path, as good as invisible,
  //    and its two sheets for the 2D path of the small craft
  try{
    if(WARP_STYLE === 'oval' && typeof f3dWarp === 'function')
      R.vortex = !!f3dWarp(s2wX(W/2), s2wY(H/2), 1, 0, 40, 1, 0.004, 0, false, 0);
  }catch(err){}
  for(const im of [WARP_IMG, WARP_GLOW_IMG]){
    if(imgReady(im)) srcs.push(imgBmp(im) || im);
  }

  // 3. missile trail and smoke
  try{
    if(fxReady()){
      if(FX_IMG.trail) srcs.push(FX_IMG.trail);
      if(FX_IMG.smoke) srcs.push(FX_IMG.smoke);
    }
  }catch(err){}

  // 4. rocks in this mission: every shape and its sheet of rim lights
  let rocks = us.some(function(u){ return u.c === 'ast'; });
  if(!rocks && typeof spawnQ !== 'undefined') rocks = spawnQ.some(function(s){ return s.type === 'ast'; });
  if(rocks){
    try{
      for(const t of AST_TEX){
        srcs.push(t.c);
        const S = rockLightSheet(t);
        if(S){ srcs.push(S); R.lights++; }
      }
    }catch(err){}
  }

  // one small copy of each, in the corner under the bar: the browser hands
  // a picture to the graphics card the first time it is drawn from.
  // 0.004 is 1/255 - less and the browser skips the drawing altogether.
  ctx.save();
  try{
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 0.004;
    for(const im of srcs){
      if(!im || !im.width) continue;
      try{ ctx.drawImage(im, 0, 0, 2, 2); R.srcs++; }catch(err){}
    }
  }catch(err){}
  ctx.restore();

  R.ms = ((typeof performance !== 'undefined') ? performance.now() : 0) - t0;
  WARM_LAST = R;
  if(typeof perfNote === 'function')
    perfNote('warm-up ' + R.ms.toFixed(0) + ' ms: ' + R.hulls + ' hulls, ' + R.lights + ' rock sheets, ' + R.srcs + ' pictures');
  return R;
}
