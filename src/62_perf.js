// ── LAG LOG (v214, Silvio) ──────────────────────────────────────
// Short, noticeable hitches at no fixed moment. The practice log now keeps
// what happened when: models and textures being loaded, ships warping in
// and out, explosions, damage pictures being built, new glow sprites - and
// every frame that took far too long, with what happened in the second
// before it. Shown in the practice log text (plogText) under "lags".
const PERF_LAG_MS = 50;           // a frame longer than this counts as a lag
const PERF_LOOK_MS = 1000;        // what happened this long before it is listed with it
const PERF_EV_MAX = 300;          // recent events kept
let PERF_EV = [];
function perfNow(){ return (typeof performance !== 'undefined') ? performance.now() : Date.now(); }
// never lets an error out: it is called from the loaders, and a throw
// there left a model "loading" for good (the field test caught it)
function perfNote(txt){
  try{
    PERF_EV.push({ms: perfNow(), t: (typeof PL !== 'undefined' && PL) ? PL.t : 0, txt: txt});
    if(PERF_EV.length > PERF_EV_MAX) PERF_EV.splice(0, PERF_EV.length - PERF_EV_MAX);
  }catch(e){}
}
// Called once per frame by the main loop: the frame's length and how much
// of it went to the steps (update) and to drawing.
function perfFrame(dt, updMs, drawMs, steps){
  if(!(dt > PERF_LAG_MS)) return;
  if(typeof GS !== 'undefined' && GS !== 'playing') return;
  if(typeof paused !== 'undefined' && paused) return;
  const now = perfNow();
  const recent = PERF_EV.filter(function(e){ return now - e.ms <= PERF_LOOK_MS + dt; })
                        .map(function(e){ return e.txt; });
  // the same kind of event many times: counted, not listed one by one
  const cnt = {};
  for(const r of recent) cnt[r] = (cnt[r] || 0) + 1;
  const what = Object.keys(cnt).map(function(k){ return cnt[k] > 1 ? k + ' x' + cnt[k] : k; });
  const rec = {t: (typeof PL !== 'undefined' && PL) ? PL.t : 0, ms: Math.round(dt), upd: Math.round(updMs),
               draw: Math.round(drawMs), steps: steps, what: what,
               parts: (typeof PARTS !== 'undefined') ? PARTS.length : 0,
               bolts: ((typeof pBullets !== 'undefined') ? pBullets.length : 0) + ((typeof eBullets !== 'undefined') ? eBullets.length : 0)};
  if(typeof PL !== 'undefined' && PL){ (PL.lags = PL.lags || []).push(rec); if(PL.lags.length > 200) PL.lags.shift(); }
}
// Once per step: ships starting to warp in or out (no hook needed in the
// many places that start a warp).
function perfTick(){
  const scan = function(list){
    for(const e of list){
      if(!e || e.small) continue;
      if(e.warp > 0 && !e._pwI){ e._pwI = true; perfNote('warp in ' + (e.img || e.type)); }
      if(e.warpOut > 0 && !e._pwO){ e._pwO = true; perfNote('warp out ' + (e.img || e.type)); }
    }
  };
  if(typeof enemies !== 'undefined') scan(enemies);
  if(typeof allies !== 'undefined') scan(allies);
}
// The lines for one wave of the practice log.
function perfLines(r){
  const L = [];
  const lags = r.lags || [];
  L.push('  lags (frames over ' + PERF_LAG_MS + ' ms): ' + lags.length +
         (lags.length ? ', longest ' + Math.max.apply(null, lags.map(function(x){ return x.ms; })) + ' ms' : ''));
  for(const g of lags.slice(0, 40)){
    // elsewhere: time the game's own code did not use - the browser,
    // garbage collection, the graphics card (texture uploads)
    L.push('    ' + plogTime(g.t) + '  ' + g.ms + ' ms (update ' + g.upd + ' / draw ' + g.draw + ' / elsewhere ' + Math.max(0, g.ms - g.upd - g.draw) + ', ' + g.steps + ' steps, ' +
           g.parts + ' particles, ' + g.bolts + ' rounds)' + (g.what.length ? '  after: ' + g.what.join('; ') : '  after: nothing logged'));
  }
  if(lags.length > 40) L.push('    ... ' + (lags.length - 40) + ' more');
  return L;
}
