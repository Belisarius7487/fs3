
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
  scan_done: "@@FS3_SOUND:sounds/scan_done.wav@@",
  scan_start: "@@FS3_SOUND:sounds/scan_start.wav@@",
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
  // Subach (Terran name) and Mekhu (Vasudan name) are the same gun.
  wpn_subach: "@@FS3_SOUND:sounds/wpn_mekhu.mp3@@",
  wpn_prometheus: "@@FS3_SOUND:sounds/wpn_prometheus.mp3@@",
  wpn_sidhe: "@@FS3_SOUND:sounds/wpn_sidhe.mp3@@",
  // Capital ship turrets (v161). The Megafunk shares the Shivan turret
  // sound, as in FreeSpace.
  wpn_terran_turret: "@@FS3_SOUND:sounds/wpn_terran_turret.mp3@@",
  wpn_tht: "@@FS3_SOUND:sounds/wpn_tht.mp3@@",
  wpn_shivan_turret: "@@FS3_SOUND:sounds/wpn_shivan_turret.mp3@@",
  // The lasers of Shivan fighters and bombers.
  wpn_shivan_light: "@@FS3_SOUND:sounds/wpn_shivan_light.mp3@@",
  wpn_shivan_heavy: "@@FS3_SOUND:sounds/wpn_shivan_heavy.mp3@@",
  wpn_shivan_mega: "@@FS3_SOUND:sounds/wpn_shivan_mega.mp3@@"
};

// ── The mix ──
// A battle has dozens of sounds going at once. Played all at their own
// level they add up to a wall of noise (testers: "a nonstop Battle of
// Endor"). So:
//   - every sound has a level against the others (SND_MIX),
//   - what happens far from the player is quieter (sndAtt),
//   - each sound has a limit of copies at once (SND_VOICES) and a least
//     time between two starts (SND_GAP),
//   - above SND_BUSY sounds at once the minor ones (SND_MINOR) are left out,
//   - a compressor on the effects keeps the peaks in check.
const SND_MIX = {
  wpn_prometheus:0.20, wpn_sidhe:0.20, wpn_dante:0.24, wpn_subach:0.20,
  sec_mx64:0.30, sec_cyclops:0.36, sec_stiletto:0.50, sec_infyrno:0.34, sec_tornado:0.34,
  sec_empty:0.35, sec_cyclops_hit:0.50, missile_explosion:0.32,
  burst_dante:0.38, burst_infyrno:0.42,
  expl_small:0.34, expl_medium:0.50, expl_big:0.62, expl_meson:0.80,
  expl_secondary:0.22, expl_asteroid:0.30, expl_player:0.75,
  hit_shield:0.26, hit_player:0.34, sub_destroyed:0.40,
  scan_start:0.80, scan_done:0.90, scan_loop:0.70,
  warp_open:0.18, warp_in_big:0.36, warp_out_big:0.36,
  beam_charge:0.30, beam_loop:0.24, beam_down:0.26,
  ai_fire:0.05, ai_sec:0.14,
  // a dying capital ship and her wreckage (v183): their own voices, so
  // every blast that is seen is heard, at the moment it is seen
  death_roll:0.24
};
const SND_VOICES = {
  wpn_prometheus:3, wpn_sidhe:2, wpn_dante:2, wpn_subach:3,
  expl_secondary:2, expl_small:3, expl_medium:2, expl_big:2, missile_explosion:2,
  hit_shield:1, hit_player:1, warp_open:2, warp_in_big:2, warp_out_big:2,
  beam_charge:3, beam_down:2, ai_fire:2, ai_sec:1, sub_destroyed:2,
  death_roll:5
};
// Least time between two starts of one sound, in seconds.
const SND_GAP = {hit_player:0.15, hit_shield:0.15, sec_empty:0.35,
                 expl_secondary:0.15, expl_small:0.06, missile_explosion:0.08,
                 ai_fire:0.09, ai_sec:0.25, warp_open:0.25, beam_charge:0.10};
// Sounds that give way when the mix is busy.
const SND_MINOR = {ai_fire:1, ai_sec:1, expl_secondary:1, warp_open:1, beam_down:1,
                   hit_shield:1, missile_explosion:1};
const SND_BUSY = 10;
// The player's primaries and their sounds.
const PRI_SND = {prometheus:'wpn_prometheus', hl7:'wpn_subach', scatter:'wpn_sidhe', dante:'wpn_dante',
                 shl:'wpn_shivan_light', shh:'wpn_shivan_heavy', shm:'wpn_shivan_mega'};
// The player's own guns: every shot is heard. When all voices of one
// are busy the oldest is cut short instead of the new shot left out -
// a Dante sound is longer than the time between two Dante shots.
const SND_STEAL = {wpn_prometheus:1, wpn_subach:1, wpn_sidhe:1, wpn_dante:1};
const SND_LOOP_MAX = 3;   // beam loops heard at once; more fire silently
// Distance from the player: full level up to SND_NEAR points, then it
// falls off, down to SND_ATT_MIN at the far side of the field.
const SND_NEAR = 140, SND_FALL = 300, SND_ATT_MIN = 0.22;
function sndAtt(x, y){
  if(x == null || typeof player === 'undefined' || !player) return 1;
  const d = Math.hypot(x - player.x, (y == null ? player.y : y) - player.y);
  return Math.max(SND_ATT_MIN, 1/(1 + Math.max(0, d - SND_NEAR)/SND_FALL));
}

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

// Settings, kept in the browser like the ECO ones. on: everything (the
// mute button on the title and in the bar); vol: effects; mus: music.
let SND = {on:true, vol:0.6, mus:0.5};
try{
  const _ss = JSON.parse(localStorage.getItem('fs3_snd') || 'null');
  if(_ss && typeof _ss === 'object'){
    SND.on = _ss.on !== false;
    if(typeof _ss.vol === 'number') SND.vol = Math.max(0, Math.min(1, _ss.vol));
    if(typeof _ss.mus === 'number') SND.mus = Math.max(0, Math.min(1, _ss.mus));
  }
}catch(ex){}
function sndSave(){ try{ localStorage.setItem('fs3_snd', JSON.stringify(SND)); }catch(ex){} }
const SND_VOL_STEPS = [1, 0.75, 0.6, 0.5, 0.25];
const MUS_VOL_STEPS = [1, 0.75, 0.5, 0.25, 0];
function sndStep(steps, v){
  let i = steps.indexOf(v);
  if(i < 0){ i = 0; while(i < steps.length-1 && steps[i] > v) i++; i--; }
  return steps[(i+1) % steps.length];
}

let sndCtx = null, sndOut = null;
const SND_BUF = {};            // name -> [AudioBuffer, ...] (variants)
const SND_PLAYING = {};        // channel -> number of voices sounding
const SND_LAST = {};           // channel -> audio time it last started
let SND_ALL = 0;               // one-shots sounding at all
let SND_BEAMS = [];            // {e, b, src, c, base} for every beam loop
const SND_SRCS = {};           // channel -> sources sounding, oldest first
let SND_SCANS = [];            // scan loops: {o, src}

function sndBase(name){ return name.replace(/_0*\d+$/, ''); }
function sndApplyVolume(){
  if(sndOut) sndOut.gain.value = SND.on ? SND.vol : 0;
  musicApplyVolume();
}
// The mute button: everything off or on, kept for the next visit.
function sndToggleMute(){
  SND.on = !SND.on; sndSave(); sndApplyVolume();
  if(SND.on) sndUnlock();
}
// First touch, click or key: create the context and decode the files.
function sndUnlock(){
  musicUnlock();
  if(sndCtx){ if(sndCtx.state==='suspended' && !paused && GS==='playing') sndCtx.resume(); return; }
  const AC = window.AudioContext || window.webkitAudioContext;
  if(!AC) return;
  try{ sndCtx = new AC(); }catch(ex){ sndCtx = null; return; }
  // Effects -> compressor -> volume -> speakers.
  sndOut = sndCtx.createGain();
  let into = sndOut;
  if(sndCtx.createDynamicsCompressor){
    const k = sndCtx.createDynamicsCompressor();
    k.threshold.value = -20; k.knee.value = 12; k.ratio.value = 4;
    k.attack.value = 0.004; k.release.value = 0.25;
    k.connect(sndOut); into = k;
  }
  sndCtx._in = into;
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
// x, y: where it happens (level falls off with distance from the player).
// Returns the source, or null if nothing played.
function sndStart(name, x, vol, loop, mix, y){
  if(!sndCtx || !SND.on || sndCtx.state !== 'running') return null;
  const bufs = SND_BUF[name]; if(!bufs || !bufs.length) return null;
  const ch = mix || name;
  if((SND_PLAYING[ch]||0) >= (SND_VOICES[ch] || 4)){
    if(!SND_STEAL[ch] || !(SND_SRCS[ch]||[]).length) return null;
    const old = SND_SRCS[ch].shift();
    old._stolen = true;
    SND_PLAYING[ch] = Math.max(0, SND_PLAYING[ch]-1);
    if(!old.loop) SND_ALL = Math.max(0, SND_ALL-1);
    sndStop(old);
  }
  if(!loop && SND_ALL >= SND_BUSY && SND_MINOR[ch]) return null;
  const now = sndCtx.currentTime;
  if(!loop && !SND_STEAL[ch] && SND_LAST[ch] != null && now - SND_LAST[ch] < (SND_GAP[ch] || 0.03)) return null;
  SND_LAST[ch] = now;
  const src = sndCtx.createBufferSource();
  src.buffer = bufs[(Math.random()*bufs.length)|0];
  src.loop = !!loop;
  const g = sndCtx.createGain();
  const base = (SND_MIX[ch] || 0.3) * (vol == null ? 1 : vol);
  g.gain.value = base * sndAtt(x, y);
  let node = g;
  if(sndCtx.createStereoPanner){
    const p = sndCtx.createStereoPanner(); p.pan.value = sndPan(x);
    g.connect(p); node = p;
  }
  src.connect(g); node.connect(sndCtx._in || sndOut);
  SND_PLAYING[ch] = (SND_PLAYING[ch]||0) + 1;
  if(!loop) SND_ALL++;
  (SND_SRCS[ch] = SND_SRCS[ch] || []).push(src);
  src.onended = function(){
    const l = SND_SRCS[ch], k = l ? l.indexOf(src) : -1;
    if(k >= 0) l.splice(k, 1);
    if(src._stolen) return;          // already counted off when it was cut
    SND_PLAYING[ch] = Math.max(0, (SND_PLAYING[ch]||1) - 1);
    if(!loop) SND_ALL = Math.max(0, SND_ALL - 1);
  };
  src.start();
  src._g = g; src._base = base;
  return src;
}
// A sound at a place on the field. vol scales its level (1 = its mix).
function sndPlay(name, x, vol, y){ sndStart(name, x, vol, false, null, y); }
// The blasts of a dying ship and of her wreckage (v183).
function sndDeath(x, vol, y){ sndStart('expl_secondary', x, vol, false, 'death_roll', y); }
function sndStop(src){
  if(!src) return;
  try{
    const t = sndCtx.currentTime;
    src._g.gain.setValueAtTime(src._g.gain.value, t);
    src._g.gain.linearRampToValueAtTime(0, t + 0.06);
    src.stop(t + 0.07);
  }catch(ex){}
}
// A shot of any ship but the player's. Until the other ships carry the
// weapons of the game they all sound like a Prometheus (Silvio).
// key: the gun's own sound (capital turrets), Prometheus if none is given.
function sndAiShot(x, y, key){ sndStart(key || 'wpn_prometheus', x, 1, false, 'ai_fire', y); }
function sndAiSec(x, bomb, y){ sndStart(bomb ? 'sec_cyclops' : 'sec_mx64', x, 1, false, 'ai_sec', y); }
// A ship going up. Fighters, bombers and rocks at once; a capital ship
// starts with its secondary blasts and the big one comes with the final
// detonation (see scheduleExpl).
function sndExpl(x, type, src, y){
  if(src && src.player){ sndPlay('expl_player', x, 1, y); return; }
  // A ship that has rolled: the breakup is the big one, heard with it
  // (v183). Her secondaries were heard during the roll.
  if(src && src.rolled){ sndPlay((type==='cruiser' || type==='freighter') ? 'expl_medium' : 'expl_big', x, 1, y); return; }
  if(type==='asteroid') sndPlay('expl_asteroid', x, 1, y);
  else if(type==='fighter' || type==='bomber' || type==='sentry' || type==='container') sndPlay('expl_small', x, 1, y);
  else if(type==='station') sndPlay('expl_big', x, 1, y);
  else sndPlay('expl_secondary', x, 1, y);
}

// Beams. phase 'charge': the charge sound starts; 'fire': the loop starts
// (it is stopped again by sndTick when the beam ends, for whatever
// reason); 'abort': the charge was given up, its sound is cut.
function sndBeam(e, b, phase){
  if(!sndCtx) return;
  const c = beamSndClass(e, b), x = e.x;
  if(phase==='charge'){ sndStop(b._sndC); b._sndC = sndStart('beam_'+c+'_charge', x, 1, false, 'beam_charge', e.y); }
  else if(phase==='abort'){ sndStop(b._sndC); b._sndC = null; }
  else if(phase==='fire'){
    if(SND_BEAMS.length >= SND_LOOP_MAX) return;
    const src = sndStart('beam_'+c+'_loop', x, 1, true, 'beam_loop', e.y);
    if(src) SND_BEAMS.push({e:e, b:b, src:src, c:c});
  }
}

// Scans: the short beep repeats for as long as a scan runs and stops when
// it is done or broken off; the long sound follows when it is done.
// o is the ship or the subsystem. Called every step while scanning
// (running), and once when it stops.
function sndScanStep(o, x, y, running){
  if(running){
    o._sndScanT = fc;
    if(!o._sndScan){
      o._sndScan = true;
      const src = sndStart('scan_start', x, 1, true, 'scan_loop', y);
      if(src) SND_SCANS.push({o:o, src:src});
    }
  } else if(o._sndScan){
    o._sndScan = false;
    for(let i=SND_SCANS.length-1; i>=0; i--)
      if(SND_SCANS[i].o === o){ sndStop(SND_SCANS[i].src); SND_SCANS.splice(i, 1); }
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
      if(e.warp > 0 && !e._sndW){ e._sndW = 'in'; sndPlay(small ? 'warp_open' : 'warp_in_big', e.x, 1, e.y); }
      else if(e.warpOut > 0 && e._sndW !== 'out'){ e._sndW = 'out'; sndPlay(small ? 'warp_open' : 'warp_out_big', e.x, 1, e.y); }
      else if(!(e.warp > 0) && !(e.warpOut > 0) && e._sndW === 'in') e._sndW = 'done';
    }
  }
  // Beam loops end when the beam stops firing, its ship dies, jumps out or
  // leaves the field. The power down follows. While they run their level
  // follows the distance to the player.
  for(let i=SND_BEAMS.length-1; i>=0; i--){
    const s = SND_BEAMS[i], e = s.e;
    const gone = e.dead || e.warpOut > 0 || (enemies.indexOf(e) < 0 && allies.indexOf(e) < 0);
    if(s.b.state === 'firing' && !gone){
      if(fc % 10 === 0) s.src._g.gain.value = s.src._base * sndAtt(e.x, e.y);
      continue;
    }
    sndStop(s.src);
    sndStart('beam_'+s.c+'_down', e.x, 1, false, 'beam_down', e.y);
    SND_BEAMS.splice(i, 1);
  }
  // A scan loop whose scan was not continued this step (target gone,
  // wave over) stops by itself.
  for(let i=SND_SCANS.length-1; i>=0; i--){
    const s = SND_SCANS[i];
    if(fc - (s.o._sndScanT||0) > 2){ sndStop(s.src); s.o._sndScan = false; SND_SCANS.splice(i, 1); }
  }
}
// Everything off at once: a new game or the title screen.
function sndAllOff(){
  for(const s of SND_BEAMS) sndStop(s.src);
  SND_BEAMS = [];
  for(const s of SND_SCANS){ sndStop(s.src); s.o._sndScan = false; }
  SND_SCANS = [];
  sndHp = null; sndSh = null;
}

// ── MUSIC ────────────────────────────────────────────────────
// Silvio's pieces, not put into the page but fetched from the music folder
// next to it while they play. build_game.py puts the names of the files it
// found into MUSIC_LIST; the name says what a piece is for:
//   title_screen_*  the title          fight_*    a wave (a playlist)
//   boss_*          a boss is on the field (boss_vasudan for a Vasudan one)
//   game_over_*     after the last life    credits*   kept for later
// A piece plays to its end; then the next one of its kind is faded in.
// A change of situation (title, wave, boss, game over) fades over as well.
// The music runs on its own audio context, so it goes on quietly while
// the game is paused and the effects are frozen.
const MUSIC_LIST = "@@FS3_MUSIC_LIST@@";
const MUSIC_DIR = 'music/';
const MUSIC_FADE = 2.5;          // seconds of cross fade
const MUSIC_PAUSED = 0.4;        // level while paused or in a panel
function musicFiles(){
  if(MUSIC_LIST.indexOf('@@') === 0) return [];
  return MUSIC_LIST.split(',').map(function(s){ return s.trim(); }).filter(Boolean);
}
// files: the list to pick from (the tests give their own).
function musicPick(kind, avoid, files){
  const all = files || musicFiles();
  let list;
  if(kind==='boss_vasudan') list = all.filter(f => /^boss_vasudan/.test(f));
  else if(kind==='boss') list = all.filter(f => /^boss_/.test(f) && !/^boss_vasudan/.test(f));
  else if(kind==='title') list = all.filter(f => /^title_screen/.test(f));
  else if(kind==='game_over') list = all.filter(f => /^game_over/.test(f));
  else list = all.filter(f => /^fight_/.test(f));
  if(!list.length && kind==='boss_vasudan') return musicPick('boss', avoid, all);
  if(!list.length && kind==='boss') return musicPick('fight', avoid, all);
  if(!list.length) return null;
  const others = list.filter(f => f !== avoid);
  const from = others.length ? others : list;
  return from[(Math.random()*from.length)|0];
}
let musCtx = null, musOut = null;
let MUS = [];                    // the playing decks: {el, g, file, kind, t0, fade}
let musKind = null, musLast = null, musCheck = 0, musLevelSet = -1;
function musicUnlock(){
  if(musCtx || !musicFiles().length) return;
  const AC = window.AudioContext || window.webkitAudioContext;
  if(!AC) return;
  try{ musCtx = new AC(); }catch(ex){ musCtx = null; return; }
  musOut = musCtx.createGain();
  musOut.connect(musCtx.destination);
  musicApplyVolume();
}
function musicLevel(){
  const hold = (typeof paused !== 'undefined' && paused && GS === 'playing');
  return (SND.on ? SND.mus : 0) * (hold ? MUSIC_PAUSED : 1);
}
function musicApplyVolume(){
  if(!musOut) return;
  const t = musCtx.currentTime;
  musOut.gain.cancelScheduledValues(t);
  musOut.gain.setTargetAtTime(musicLevel(), t, 0.15);
}
// A new deck with one piece, faded in; the others fade out and go.
function musicStart(kind){
  if(!musCtx) return;
  const file = musicPick(kind, musLast);
  if(!file) return;
  musLast = file;
  const el = new Audio(MUSIC_DIR + file);
  el.preload = 'auto';
  let g;
  try{
    const src = musCtx.createMediaElementSource(el);
    g = musCtx.createGain(); g.gain.value = 0;
    src.connect(g); g.connect(musOut);
  }catch(ex){ return; }
  const t = musCtx.currentTime;
  for(const d of MUS){
    d.g.gain.cancelScheduledValues(t);
    d.g.gain.setValueAtTime(d.g.gain.value, t);
    d.g.gain.linearRampToValueAtTime(0, t + MUSIC_FADE);
    d.out = true; d.tEnd = performance.now() + MUSIC_FADE*1000 + 200;
  }
  g.gain.setValueAtTime(0, t);
  g.gain.linearRampToValueAtTime(1, t + MUSIC_FADE);
  const deck = {el:el, g:g, file:file, kind:kind, out:false};
  MUS.push(deck);
  el.play().catch(function(){});
}
// What should be playing now.
function musicWant(){
  if(GS === 'title') return 'title';
  if(GS === 'gameover') return 'game_over';
  for(const e of enemies){
    if(e.type === 'boss' && !e.dead && !(e.warp > 0))
      return (e.faction === 'vasudan' || e.faction === 'hol') ? 'boss_vasudan' : 'boss';
  }
  return 'fight';
}
// Every frame, from the main loop.
function musicTick(){
  if(!musCtx) return;
  if(!SND.on || SND.mus <= 0){
    // Nothing to hear: stop the decks rather than stream silence.
    if(MUS.length){ for(const d of MUS){ try{ d.el.pause(); }catch(ex){} } MUS = []; musKind = null; }
    return;
  }
  if(musCtx.state === 'suspended') musCtx.resume();
  // Pause and panels turn the music down, not off.
  const lv = musicLevel();
  if(lv !== musLevelSet){ musLevelSet = lv; musicApplyVolume(); }
  const now = performance.now();
  // Faded out decks go.
  for(let i=MUS.length-1; i>=0; i--){
    const d = MUS[i];
    if(d.out && now > d.tEnd){ try{ d.el.pause(); d.el.src = ''; }catch(ex){} MUS.splice(i, 1); }
  }
  if(now < musCheck) return;
  musCheck = now + 250;
  const want = musicWant();
  const cur = MUS.length ? MUS[MUS.length-1] : null;
  // A new situation, nothing playing, or the piece is about to end.
  const ending = cur && cur.el.duration > 0 && !cur.el.paused &&
                 cur.el.currentTime > cur.el.duration - MUSIC_FADE;
  const stopped = cur && (cur.el.ended || cur.el.error);
  if(want !== musKind || !cur || cur.out || ending || stopped){
    musKind = want;
    musicStart(want);
  }
}
