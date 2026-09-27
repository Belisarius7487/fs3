
// ── SOUND ────────────────────────────────────────────────────
// Sound effects through the Web Audio API. The files come from the
// FreeSpace MediaVPs (use in FS3 agreed with the FSU team) and are put into
// the page by build_game.py, one data URI per file. A file that is missing
// on the server leaves an empty string, and that sound simply stays silent.
// In the bare logic file the tokens are still there; they are skipped too.
//
// Browsers only allow sound after the player has touched or clicked the
// page, so nothing is set up before the first input. Everything below is
// a no-op until then, which is also what the simulations see.
//
// Names ending in _1, _2 ... (or _01, _02 ...) are variants of one sound;
// one of them is picked at random each time.
const SND_FILES = {
  beam_lucifer_charge: "@@FS3_SOUND:sounds/beam_lucifer_charge.mp3@@",
  beam_lucifer_down: "@@FS3_SOUND:sounds/beam_lucifer_down.mp3@@",
  beam_lucifer_loop: "@@FS3_SOUND:sounds/beam_lucifer_loop.wav@@",
  beam_shivan_large_charge: "@@FS3_SOUND:sounds/beam_shivan_large_charge.mp3@@",
  beam_shivan_large_down: "@@FS3_SOUND:sounds/beam_shivan_large_down.mp3@@",
  beam_shivan_large_loop: "@@FS3_SOUND:sounds/beam_shivan_large_loop.wav@@",
  beam_shivan_small_charge: "@@FS3_SOUND:sounds/beam_shivan_small_charge.mp3@@",
  beam_shivan_small_down: "@@FS3_SOUND:sounds/beam_shivan_small_down.mp3@@",
  beam_shivan_small_loop: "@@FS3_SOUND:sounds/beam_shivan_small_loop.wav@@",
  beam_terran_large_charge: "@@FS3_SOUND:sounds/beam_terran_large_charge.mp3@@",
  beam_terran_large_down: "@@FS3_SOUND:sounds/beam_terran_large_down.mp3@@",
  beam_terran_large_loop: "@@FS3_SOUND:sounds/beam_terran_large_loop.wav@@",
  beam_tervas_small_charge: "@@FS3_SOUND:sounds/beam_tervas_small_charge.mp3@@",
  beam_tervas_small_down: "@@FS3_SOUND:sounds/beam_tervas_small_down.mp3@@",
  beam_tervas_small_loop: "@@FS3_SOUND:sounds/beam_tervas_small_loop.wav@@",
  beam_vas_large_charge: "@@FS3_SOUND:sounds/beam_vas_large_charge.mp3@@",
  beam_vas_large_down: "@@FS3_SOUND:sounds/beam_vas_large_down.mp3@@",
  beam_vas_large_loop: "@@FS3_SOUND:sounds/beam_vas_large_loop.wav@@",
  burst_dante: "@@FS3_SOUND:sounds/burst_dante.mp3@@",
  burst_infyrno: "@@FS3_SOUND:sounds/burst_infyrno.mp3@@",
  expl_asteroid_1: "@@FS3_SOUND:sounds/expl_asteroid_1.mp3@@",
  expl_asteroid_2: "@@FS3_SOUND:sounds/expl_asteroid_2.mp3@@",
  expl_asteroid_3: "@@FS3_SOUND:sounds/expl_asteroid_3.mp3@@",
  expl_big_01: "@@FS3_SOUND:sounds/expl_big_01.mp3@@",
  expl_big_02: "@@FS3_SOUND:sounds/expl_big_02.mp3@@",
  expl_big_03: "@@FS3_SOUND:sounds/expl_big_03.mp3@@",
  expl_medium_1: "@@FS3_SOUND:sounds/expl_medium_1.mp3@@",
  expl_medium_2: "@@FS3_SOUND:sounds/expl_medium_2.mp3@@",
  expl_medium_3: "@@FS3_SOUND:sounds/expl_medium_3.mp3@@",
  expl_meson: "@@FS3_SOUND:sounds/expl_meson.mp3@@",
  expl_player: "@@FS3_SOUND:sounds/expl_player.mp3@@",
  expl_secondary_1: "@@FS3_SOUND:sounds/expl_secondary_1.mp3@@",
  expl_secondary_2: "@@FS3_SOUND:sounds/expl_secondary_2.mp3@@",
  expl_secondary_3: "@@FS3_SOUND:sounds/expl_secondary_3.mp3@@",
  expl_secondary_4: "@@FS3_SOUND:sounds/expl_secondary_4.mp3@@",
  expl_small_1: "@@FS3_SOUND:sounds/expl_small_1.mp3@@",
  expl_small_2: "@@FS3_SOUND:sounds/expl_small_2.mp3@@",
  expl_small_3: "@@FS3_SOUND:sounds/expl_small_3.mp3@@",
  hit_player: "@@FS3_SOUND:sounds/hit_player.mp3@@",
  hit_shield: "@@FS3_SOUND:sounds/hit_shield.mp3@@",
  missile_explosion: "@@FS3_SOUND:sounds/missile_explosion.mp3@@",
  scan: "@@FS3_SOUND:sounds/scan.mp3@@",
  sec_cyclops: "@@FS3_SOUND:sounds/sec_cyclops.mp3@@",
  sec_cyclops_hit: "@@FS3_SOUND:sounds/sec_cyclops_hit.mp3@@",
  sec_empty: "@@FS3_SOUND:sounds/sec_empty.mp3@@",
  sec_infyrno: "@@FS3_SOUND:sounds/sec_infyrno.mp3@@",
  sec_mx64: "@@FS3_SOUND:sounds/sec_mx64.mp3@@",
  sec_stiletto: "@@FS3_SOUND:sounds/sec_stiletto.mp3@@",
  sec_tornado: "@@FS3_SOUND:sounds/sec_tornado.mp3@@",
  sub_destroyed: "@@FS3_SOUND:sounds/sub_destroyed.mp3@@",
  warp_in_big: "@@FS3_SOUND:sounds/warp_in_big.mp3@@",
  warp_open: "@@FS3_SOUND:sounds/warp_open.mp3@@",
  warp_out_big: "@@FS3_SOUND:sounds/warp_out_big.mp3@@",
  wpn_dante: "@@FS3_SOUND:sounds/wpn_dante.mp3@@",
  wpn_mekhu: "@@FS3_SOUND:sounds/wpn_mekhu.mp3@@",
  wpn_prometheus: "@@FS3_SOUND:sounds/wpn_prometheus.mp3@@",
  wpn_sidhe: "@@FS3_SOUND:sounds/wpn_sidhe.mp3@@"
};

// How loud each sound sits against the others (1 = as recorded), and how
// many copies of it may sound at once. The files come at very different
// levels; the scan beep for instance is recorded far below the rest.
const SND_MIX = {
  wpn_prometheus:0.30, wpn_sidhe:0.30, wpn_dante:0.34, wpn_mekhu:0.30,
  sec_mx64:0.45, sec_cyclops:0.55, sec_stiletto:0.75, sec_infyrno:0.50, sec_tornado:0.50,
  sec_empty:0.50, sec_cyclops_hit:0.80, missile_explosion:0.55,
  burst_dante:0.70, burst_infyrno:0.70,
  expl_small:0.55, expl_medium:0.75, expl_big:0.85, expl_meson:0.95,
  expl_secondary:0.45, expl_asteroid:0.50, expl_player:0.90,
  hit_shield:0.45, hit_player:0.55, sub_destroyed:0.60, scan:1.00,
  warp_open:0.35, warp_in_big:0.55, warp_out_big:0.55,
  beam_charge:0.50, beam_loop:0.45, beam_down:0.45,
  ai_fire:0.10, ai_sec:0.25
};
const SND_VOICES = {
  wpn_prometheus:4, wpn_sidhe:3, wpn_dante:3, wpn_mekhu:3,
  expl_secondary:3, expl_small:4, missile_explosion:3, hit_shield:2, hit_player:2,
  warp_open:3, beam_charge:4, beam_down:3, ai_fire:3, ai_sec:2
};
// Least time between two starts of one sound, in seconds. Hits land on
// every step while a beam holds the player; ten a second are plenty.
const SND_GAP = {hit_player:0.12, hit_shield:0.12, sec_empty:0.35,
                 expl_secondary:0.08, ai_fire:0.05};
// The player's primaries and their sounds.
const PRI_SND = {prometheus:'wpn_prometheus', scatter:'wpn_sidhe', dante:'wpn_dante'};
const SND_LOOP_MAX = 4;   // beam loops heard at once; more fire silently

// Beams: which sound set a battery uses, and how long it charges. The loop
// starts exactly when the charge time is up, while the charge sound plays
// on to its end (Silvio's timings). The charge time of the game is set to
// the same figure, so the beam appears with the loop.
const BEAM_SND_CHARGE = {terran_large:3, tervas_small:1.5, shivan_small:1,
                         vas_large:2, lucifer:3, shivan_large:1.5};
function beamSndClass(e, b){
  if(b.large && (e.img==='sdlucifer' || e.img==='sdsathanas')) return 'lucifer';
  if(e.faction==='shivan') return b.large ? 'shivan_large' : 'shivan_small';
  if(!b.large) return 'tervas_small';
  return (e.faction==='vasudan' || e.faction==='hol') ? 'vas_large' : 'terran_large';
}
// Charge time of one battery, in game steps.
function beamChargeTicks(e, b){
  return Math.round((BEAM_SND_CHARGE[beamSndClass(e, b)] || 3) * TICK_HZ);
}

// Settings, kept in the browser like the ECO ones.
let SND = {on:true, vol:0.75};
try{
  const _ss = JSON.parse(localStorage.getItem('fs3_snd') || 'null');
  if(_ss && typeof _ss === 'object'){
    SND.on = _ss.on !== false;
    if(typeof _ss.vol === 'number') SND.vol = Math.max(0, Math.min(1, _ss.vol));
  }
}catch(ex){}
function sndSave(){ try{ localStorage.setItem('fs3_snd', JSON.stringify(SND)); }catch(ex){} }
const SND_VOL_STEPS = [1, 0.75, 0.5, 0.25];

let sndCtx = null, sndOut = null;
const SND_BUF = {};            // name -> [AudioBuffer, ...] (variants)
const SND_PLAYING = {};        // name -> number of voices sounding
const SND_LAST = {};           // name -> audio time it last started
let SND_BEAMS = [];            // {e, b, src, g} for every beam loop

function sndBase(name){ return name.replace(/_0*\d+$/, ''); }
function sndApplyVolume(){
  if(sndOut) sndOut.gain.value = SND.on ? SND.vol : 0;
}
// First touch, click or key: create the context and decode the files.
function sndUnlock(){
  if(sndCtx){ if(sndCtx.state==='suspended' && !paused) sndCtx.resume(); return; }
  const AC = window.AudioContext || window.webkitAudioContext;
  if(!AC) return;
  try{ sndCtx = new AC(); }catch(ex){ sndCtx = null; return; }
  sndOut = sndCtx.createGain();
  sndOut.connect(sndCtx.destination);
  sndApplyVolume();
  for(const name of Object.keys(SND_FILES)){
    const src = SND_FILES[name];
    if(!src || src.indexOf('data:') !== 0) continue;     // missing on the server
    fetch(src).then(function(r){ return r.arrayBuffer(); })
      .then(function(ab){ return new Promise(function(ok, bad){ sndCtx.decodeAudioData(ab, ok, bad); }); })
      .then(function(buf){ const k = sndBase(name); (SND_BUF[k] = SND_BUF[k] || []).push(buf); })
      .catch(function(){});
  }
}
['pointerdown', 'touchend', 'keydown'].forEach(function(ev){
  window.addEventListener(ev, sndUnlock, true);
});

// Left and right after where it happens on the field.
function sndPan(x){
  if(x == null) return 0;
  return Math.max(-0.8, Math.min(0.8, (x/W*2 - 1)*0.8));
}
// Starts one sound. mix: a channel of its own for level, voice count and
// spacing when a file is shared (the beam sets, and the guns of every
// other ship, which must not take the voices of the player's own gun).
// Returns the source, or null if nothing played.
function sndStart(name, x, vol, loop, mix){
  if(!sndCtx || !SND.on || sndCtx.state !== 'running') return null;
  const bufs = SND_BUF[name]; if(!bufs || !bufs.length) return null;
  const ch = mix || name;
  if((SND_PLAYING[ch]||0) >= (SND_VOICES[ch] || 6)) return null;
  // The same sound twice within a few ms only makes it louder.
  const now = sndCtx.currentTime;
  if(!loop && SND_LAST[ch] != null && now - SND_LAST[ch] < (SND_GAP[ch] || 0.03)) return null;
  SND_LAST[ch] = now;
  const src = sndCtx.createBufferSource();
  src.buffer = bufs[(Math.random()*bufs.length)|0];
  src.loop = !!loop;
  const g = sndCtx.createGain();
  g.gain.value = (SND_MIX[mix || name] || 0.6) * (vol == null ? 1 : vol);
  let node = g;
  if(sndCtx.createStereoPanner){
    const p = sndCtx.createStereoPanner(); p.pan.value = sndPan(x);
    g.connect(p); node = p;
  }
  src.connect(g); node.connect(sndOut);
  SND_PLAYING[ch] = (SND_PLAYING[ch]||0) + 1;
  src.onended = function(){ SND_PLAYING[ch] = Math.max(0, (SND_PLAYING[ch]||1) - 1); };
  src.start();
  src._g = g;
  return src;
}
// A sound at a place on the field. vol scales its level (1 = its mix).
function sndPlay(name, x, vol){ sndStart(name, x, vol, false); }
// A shot of any ship but the player's. Until the other ships carry the
// weapons of the game they all sound like a Prometheus (Silvio).
function sndAiShot(x){ sndStart('wpn_prometheus', x, 1, false, 'ai_fire'); }
function sndAiSec(x, bomb){ sndStart(bomb ? 'sec_cyclops' : 'sec_mx64', x, 1, false, 'ai_sec'); }
// A ship going up. Fighters, bombers and rocks at once; a capital ship
// starts with its secondary blasts and the big one comes with the final
// detonation (see scheduleExpl).
function sndExpl(x, type, src){
  if(src && src.player){ sndPlay('expl_player', x); return; }
  if(type==='asteroid') sndPlay('expl_asteroid', x);
  else if(type==='fighter' || type==='bomber' || type==='sentry' || type==='container') sndPlay('expl_small', x);
  else if(type==='station') sndPlay('expl_big', x);
  else sndPlay('expl_secondary', x);
}
function sndStop(src){
  if(!src) return;
  try{
    const t = sndCtx.currentTime;
    src._g.gain.setValueAtTime(src._g.gain.value, t);
    src._g.gain.linearRampToValueAtTime(0, t + 0.06);
    src.stop(t + 0.07);
  }catch(ex){}
}

// Beams. phase 'charge': the charge sound starts; 'fire': the loop starts
// (it is stopped again by sndTick when the beam ends, for whatever
// reason); 'abort': the charge was given up, its sound is cut.
function sndBeam(e, b, phase){
  if(!sndCtx) return;
  const c = beamSndClass(e, b), x = e.x;
  if(phase==='charge'){ sndStop(b._sndC); b._sndC = sndStart('beam_'+c+'_charge', x, 1, false, 'beam_charge'); }
  else if(phase==='abort'){ sndStop(b._sndC); b._sndC = null; }
  else if(phase==='fire'){
    if(SND_BEAMS.length >= SND_LOOP_MAX) return;
    const src = sndStart('beam_'+c+'_loop', x, 1, true, 'beam_loop');
    if(src) SND_BEAMS.push({e:e, b:b, src:src, c:c});
  }
}

// Once a game step: pause, the player's hits, jumps, and beams that ended.
let sndHp = null, sndSh = null;
function sndTick(){
  if(!sndCtx) return;
  // Pause and the settings panel freeze the sound with the game.
  const hold = paused || GS !== 'playing';
  if(hold && sndCtx.state === 'running') sndCtx.suspend();
  else if(!hold && sndCtx.state === 'suspended') sndCtx.resume();
  if(hold) return;
  // The player's hull and shield: a drop since the last step is a hit.
  if(sndHp != null){
    if(player.hp < sndHp - 0.6) sndPlay('hit_player', player.x);
    else if(player.sh < sndSh - 0.6) sndPlay('hit_shield', player.x);
  }
  sndHp = player.hp; sndSh = player.sh;
  // Jumps. The big ships have their own, long sounds; everything smaller
  // shares the opening of the vortex.
  for(const list of [enemies, allies]){
    for(const e of list){
      if(e.type==='asteroid' || (e.warpMax||0) <= 1) continue;
      const small = e.small || e.type==='fighter' || e.type==='bomber' ||
                    e.type==='sentry' || e.type==='container';
      if(e.warp > 0 && !e._sndW){ e._sndW = 'in'; sndPlay(small ? 'warp_open' : 'warp_in_big', e.x); }
      else if(e.warpOut > 0 && e._sndW !== 'out'){ e._sndW = 'out'; sndPlay(small ? 'warp_open' : 'warp_out_big', e.x); }
      else if(!(e.warp > 0) && !(e.warpOut > 0) && e._sndW === 'in') e._sndW = 'done';
    }
  }
  // Beam loops end when the beam stops firing, its ship dies, jumps out or
  // leaves the field. The power down follows.
  for(let i=SND_BEAMS.length-1; i>=0; i--){
    const s = SND_BEAMS[i], e = s.e;
    const gone = e.dead || e.warpOut > 0 || (enemies.indexOf(e) < 0 && allies.indexOf(e) < 0);
    if(s.b.state === 'firing' && !gone) continue;
    sndStop(s.src);
    sndStart('beam_'+s.c+'_down', e.x, 1, false, 'beam_down');
    SND_BEAMS.splice(i, 1);
  }
}
// Everything off at once: a new game or the title screen.
function sndAllOff(){
  for(const s of SND_BEAMS) sndStop(s.src);
  SND_BEAMS = [];
  sndHp = null; sndSh = null;
}
