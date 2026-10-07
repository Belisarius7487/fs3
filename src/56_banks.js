// ── WEAPON BANKS (v186) ──────────────────────────────────────
// The player flies FreeSpace's arsenal now (Silvio, variant 3): up to two
// primary and three secondary banks per hull, the default fit and the
// allowed weapons from the FS2 ships.tbl, the weapons from weapons.tbl,
// plus the game's own Sidhe and Dante.
//
// How the table values become game values:
//   - Primaries are anchored on the Prometheus R: it hits as hard as the
//     old Prometheus did. Every other gun keeps its FS2 ratio to it, per
//     shot and separately against hull, shield and subsystems.
//   - Missiles are anchored on the Harpoon (= the old MX-64, 35), bombs on
//     the Cyclops (= the old Cyclops, 80); the rest keep their FS2 ratio.
//   - Fire wait and lifetime are taken in seconds as they are; speed is
//     450 m/s = 9 points per step, as the old Prometheus flew.
//   - Weapon energy: store and recharge per hull from ships.tbl, cost per
//     shot from weapons.tbl, with one scale for each so that on the
//     Myrmidon a single bank never runs dry and both linked last about
//     ten seconds from full (Silvio). No ETS.
// The AI keeps its old weapons until its own step (AI_PRIMARIES,
// AI_SECONDARIES in 55_arms.js).

const MPS_TO_PX   = 0.02;    // m/s -> points per step
const BOLT_SPD_MAX = 16;     // faster rounds would step over a fighter
const EN_STORE_K  = 1/15;    // Max Weapon Eng -> game store (Myrmidon 150 -> 10)
const EN_REGEN_K  = 0.5556;  // Power Output -> regen per second (Myrmidon 2.4 -> 1.33)
const PRI_ANCHOR  = {d:18, a:1.1, s:0.8, u:0.35};            // Prometheus R
const MIS_ANCHOR  = {d:100, a:1.0, s:0.8, u:0.5, game:35};   // Harpoon
const BOMB_ANCHOR = {d:2000, a:1.0, s:0.02, u:0.5, game:80}; // Cyclops
// The old player beat (PLAYER_FR_BASE, 70_ui.js, loads later): 28 steps.
const FR_BASE_STEPS = 28;

// snd: the FS2 launch sound (weapons.tbl $LaunchSnd, sounds.tbl), v187.
// fs: damage, velocity (m/s), fire wait (s), lifetime (s), energy per
// shot, armour / shield / subsystem factor - straight from weapons.tbl.
// unlock: points needed, unless it is part of the hull's default fit.
const ARSENAL_P = [
  {key:'promr', name:'Prometheus R', unlock:0, snd:'L_Prom_R',
   fs:{d:18, v:450, w:0.45, l:2.0, e:0.60, a:1.1, s:0.8, u:0.35},
   col:'#ccff88', glow:'rgba(180,255,80,0.30)', note:'the standard gun, cheap on energy'},
  {key:'subach', name:'Subach HL-7', unlock:0, snd:'L_Sidearm',
   fs:{d:15, v:450, w:0.20, l:2.0, e:0.20, a:0.9, s:0.7, u:0.3},
   col:'#bfe9ff', glow:'rgba(120,200,255,0.30)', note:'quick, light, almost no energy'},
  {key:'mekhu', name:'Mekhu HL-7', unlock:0, snd:'L_Sidearm',
   fs:{d:12, v:485, w:0.15, l:2.0, e:0.20, a:0.9, s:0.8, u:0.3},
   col:'#a8f0ff', glow:'rgba(110,220,255,0.30)', note:'the Vasudan HL-7, quicker still'},
  {key:'akheton', name:'Akheton SDG', unlock:4000, snd:'L_Scalpel',
   fs:{d:30, v:500, w:0.35, l:1.5, e:1.6, a:0.0, s:0.5, u:1.0},
   col:'#ff9ad5', glow:'rgba(255,120,200,0.32)', note:'shields and subsystems only - no hull damage'},
  {key:'morningstar', name:'Morning Star', unlock:8000, snd:'L_Flail',
   fs:{d:7, v:1000, w:0.15, l:2.0, e:0.8, a:0.5, s:1.3, u:0.2},
   col:'#fff2a8', glow:'rgba(255,240,150,0.30)', note:'fast and far, tears shields, hungry'},
  {key:'proms', name:'Prometheus S', unlock:12000, snd:'L_Prom_S',
   fs:{d:30, v:750, w:0.35, l:2.0, e:1.0, a:0.9, s:1.0, u:0.35},
   col:'#e8ff6a', glow:'rgba(220,255,90,0.32)', note:'heavier and faster than the R'},
  {key:'kayser', name:'UD-8 Kayser', unlock:18000, snd:'L_Kayser',
   fs:{d:28, v:650, w:0.25, l:1.5, e:1.2, a:1.0, s:0.9, u:0.35},
   col:'#b48cff', glow:'rgba(170,130,255,0.34)', note:'hard hitting all round, empties the store'},
  {key:'circe', name:'Circe', unlock:26000, snd:'L_Circle',
   fs:{d:45, v:450, w:0.40, l:3.0, e:1.0, a:0.0, s:1.0, u:0.0},
   col:'#7affd8', glow:'rgba(100,255,210,0.32)', note:'shields only - nothing gets through to the hull'},
  {key:'maxim', name:'Maxim', unlock:32000, snd:'L_Newton',
   fs:{d:20, v:1800, w:0.15, l:2.0, e:1.0, a:1.3, s:0.2, u:1.0},
   col:'#ff6a3a', glow:'rgba(255,100,50,0.34)', note:'hull and subsystems, useless against shields'}
];
// Secondaries. cargo: rack space per round (SBank Capacity / cargo =
// rounds). turn: FS2 turn time in seconds. homing: 'heat' goes for the
// nearest, 'aspect' keeps the target it was fired at.
const ARSENAL_S = [
  {key:'harpoon', name:'Harpoon', cls:'missile', unlock:0, snd:'m_shrike', homing:'aspect',
   fs:{d:100, v:250, w:2.0, l:5.0, a:1.0, s:0.8, u:0.5, cargo:2.5, turn:1.0},
   note:'the all-round aspect seeker'},
  {key:'rockeye', name:'Rockeye', cls:'missile', unlock:0, snd:'m_wasp', homing:'heat',
   fs:{d:45, v:190, w:0.5, l:10.0, a:1.0, s:0.8, u:0.8, cargo:4, turn:0.85},
   note:'heat seeker, quick off the rail'},
  {key:'tempest', name:'Tempest', cls:'missile', unlock:3000, snd:'m_fury', homing:null,
   fs:{d:45, v:360, w:0.3, l:1.8, a:0.9, s:0.5, u:0.6, cargo:0.25, turn:1},
   note:'dumbfire, a deep rack, short reach'},
  {key:'tornado', name:'Tornado', cls:'missile', unlock:10000, snd:'m_swarm', homing:'aspect',
   swarm:4, fan:0.6,
   fs:{d:25, v:230, w:2.5, l:7.0, a:2.0, s:1.0, u:0.3, cargo:1.25, turn:1.25},
   note:'four faster seekers, each its own target'},
  {key:'emp', name:'EMP Adv.', cls:'missile', unlock:14000, snd:'m_emp', homing:'aspect', emp:true,
   fs:{d:45, v:275, w:2.0, l:5.0, a:1.0, s:0.8, u:0.5, cargo:4, turn:1.0},
   note:'fighters near the blast stop firing for a while'},
  {key:'infyrno', name:'Infyrno', cls:'missile', unlock:18000, snd:'m_cluster', homing:null,
   burst:true, children:14, shardRange:90,
   fs:{d:150, v:120, w:5.0, l:7.0, a:1.0, s:0.75, u:1.0, cargo:10, turn:1,
       child:{d:100, v:250, l:0.3}},      // 14 x "Cluster Bomb Baby"
   note:'fired straight - press again to burst it into 14 small seekers'},
  {key:'trebuchet', name:'Trebuchet', cls:'missile', unlock:18000, snd:'m_angel', homing:'aspect',
   fs:{d:350, v:280, w:6.0, l:18.0, a:0.9, s:0.5, u:2.4, cargo:8, turn:3.0},
   note:'long range, heavy, for subsystems'},
  {key:'stiletto2', name:'Stiletto II', cls:'missile', unlock:26000, snd:'m_stiletto', homing:'heat', subs:true,
   fs:{d:775, v:220, w:2.0, l:25.0, a:0.01, s:0.0, u:1.0, cargo:8, turn:1.0},
   note:'into the subsystems, not the hull'},
  {key:'tagc', name:'TAG-C', cls:'missile', unlock:0, fromWave:67, snd:'m_angel', homing:'aspect', tag:true,
   fs:{d:10, v:205, w:8.0, l:13.0, a:0.1, s:0.1, u:0.1, cargo:4, turn:1.75},
   note:'marks the target - our beams find it, even in the nebula'},
  {key:'cyclops', name:'Cyclops', cls:'bomb', unlock:0, snd:'m_tsunami', homing:'aspect',
   fs:{d:2000, v:95, w:20.0, l:25.0, a:1.0, s:0.02, u:0.5, cargo:15, turn:1.0},
   note:'slow and heavy, for hulls that cannot dodge'}
];

// Banks of every hull the player can fly, from ships.tbl (genbanks.py).
// v187 (Silvio): Lamprey, Hornet, Piranha and Helios are out of the game;
// default Hornets became Tornados, default Piranhas Infyrnos.
// p/s: default fit, pa/sa: what the hull may carry, cap: secondary bank
// capacity, eng: Max Weapon Eng, pow: Power Output. At most 2 + 3 banks.
// The FS1 hulls (Apollo, Valkyrie, Athena) come from the FSPort table,
// their FS1 weapons mapped onto the nearest FS2 ones.
const SHIP_BANKS = {
  fitoth:{p:['promr'], pa:['mekhu','akheton','morningstar','proms','promr','circe'], s:['harpoon'], sa:['rockeye','tempest','harpoon','tornado','emp'], cap:[80], eng:150, pow:2.5},
  fihorus:{p:['mekhu','morningstar'], pa:['mekhu','morningstar','proms','promr','kayser','circe'], s:['rockeye','trebuchet'], sa:['rockeye','tempest','harpoon','trebuchet','tornado','emp'], cap:[40,40], eng:100, pow:2.2},
  boosiris:{p:['mekhu'], pa:['mekhu','akheton','morningstar','proms','promr','kayser','circe'], s:['infyrno','stiletto2','trebuchet'], sa:['rockeye','tempest','harpoon','trebuchet','stiletto2','cyclops','emp','infyrno'], cap:[40,40,20], eng:100, pow:3.0},
  fiserapis:{p:['promr','akheton'], pa:['mekhu','akheton','morningstar','proms','promr','circe','maxim'], s:['harpoon','harpoon'], sa:['rockeye','tempest','harpoon','tornado','emp'], cap:[60,30], eng:150, pow:3.4},
  fiseth:{p:['mekhu','mekhu'], pa:['mekhu','akheton','morningstar','proms','promr','kayser','circe'], s:['rockeye','stiletto2'], sa:['rockeye','tempest','harpoon','trebuchet','tornado','stiletto2','emp','infyrno'], cap:[40,80], eng:100, pow:3.0},
  bobakha:{p:['mekhu','mekhu'], pa:['mekhu','akheton','promr','proms','circe'], s:['infyrno','stiletto2'], sa:['rockeye','harpoon','stiletto2','cyclops','emp','infyrno','trebuchet'], cap:[80,100], eng:100, pow:4.3},
  fitauret:{p:['mekhu','mekhu'], pa:['mekhu','akheton','morningstar','proms','promr','kayser','circe'], s:['rockeye','rockeye'], sa:['rockeye','tempest','harpoon','trebuchet','tornado','stiletto2','emp','infyrno'], cap:[100,100], eng:100, pow:3.0},
  bosekhmet:{p:['promr'], pa:['mekhu','akheton','morningstar','proms','promr','circe','maxim'], s:['tornado','infyrno','cyclops'], sa:['rockeye','tempest','harpoon','tornado','trebuchet','stiletto2','cyclops','emp','infyrno'], cap:[80,80,80], eng:100, pow:3.0},
  fimyrmidon:{p:['promr','subach'], pa:['subach','akheton','morningstar','proms','promr','kayser'], s:['rockeye','tornado','tempest'], sa:['rockeye','tornado','tempest','trebuchet','stiletto2','emp','infyrno'], cap:[20,20,40], eng:150, pow:2.4},
  fiperseus:{p:['subach','promr'], pa:['subach','akheton','morningstar','proms','promr','kayser'], s:['harpoon','tornado'], sa:['rockeye','tempest','harpoon','trebuchet','stiletto2','tornado','emp'], cap:[40,40], eng:150, pow:2.0},
  fiherc:{p:['subach','promr'], pa:['subach','akheton','morningstar','proms','promr','kayser','circe','maxim'], s:['harpoon','tornado'], sa:['rockeye','tempest','harpoon','trebuchet','tornado','emp','infyrno'], cap:[60,60], eng:150, pow:3.0},
  boartemis:{p:['subach'], pa:['subach','proms','promr','circe','maxim'], s:['tornado','cyclops','cyclops'], sa:['rockeye','tornado','trebuchet','stiletto2','cyclops','emp','infyrno'], cap:[40,60,60], eng:100, pow:4.0},
  fihercmk2:{p:['subach','promr'], pa:['subach','akheton','morningstar','proms','promr','kayser','circe','maxim'], s:['harpoon','tornado'], sa:['rockeye','tempest','harpoon','trebuchet','infyrno','tornado','emp'], cap:[80,100], eng:150, pow:3.0},
  bomedusa:{p:['promr'], pa:['subach','proms','promr','circe','maxim'], s:['tornado','cyclops','cyclops'], sa:['rockeye','tornado','trebuchet','stiletto2','cyclops','emp','infyrno'], cap:[40,80,80], eng:100, pow:4.0},
  fierinyes:{p:['subach','promr'], pa:['subach','akheton','morningstar','proms','promr','kayser','circe','maxim'], s:['harpoon','tornado'], sa:['rockeye','tempest','harpoon','trebuchet','infyrno','tornado','emp'], cap:[40,50], eng:150, pow:3.3},
  boursa:{p:['promr','promr'], pa:['subach','akheton','morningstar','proms','promr','circe','maxim'], s:['tornado','infyrno','cyclops'], sa:['rockeye','tempest','harpoon','tornado','trebuchet','stiletto2','cyclops','emp','infyrno'], cap:[80,80,80], eng:150, pow:4.5},
  fiares:{p:['subach','promr'], pa:['subach','akheton','morningstar','proms','promr','kayser','circe','maxim'], s:['harpoon','tornado'], sa:['rockeye','tempest','harpoon','trebuchet','tornado','emp','infyrno'], cap:[90,100], eng:180, pow:5.0},
  fipegasus:{p:['subach'], pa:['subach','akheton','morningstar','promr','proms'], s:['harpoon','tornado'], sa:['rockeye','tempest','harpoon','trebuchet','tornado','emp'], cap:[20,10], eng:150, pow:3.0},
  fiptah:{p:['mekhu'], pa:['mekhu','akheton','morningstar','promr','proms'], s:['harpoon','tornado'], sa:['rockeye','tempest','harpoon','trebuchet','tornado','emp'], cap:[20,10], eng:150, pow:3.0},
  // SF Mara (terrans), the captured fighter of M78.
  fimara:{p:['subach','kayser'], pa:['subach','kayser'], s:['trebuchet','tornado'], sa:['trebuchet','rockeye','tempest','tornado','harpoon','emp'], cap:[105,105], eng:195, pow:4.5},
  fiulysses:{p:['subach','promr'], pa:['subach','akheton','morningstar','proms','promr','circe','maxim'], s:['harpoon'], sa:['rockeye','tempest','tornado','harpoon','emp'], cap:[40], eng:80, pow:2.0},
  fiapollo:{p:['promr','subach'], pa:['subach','promr','morningstar','proms'], s:['harpoon','harpoon'], sa:['harpoon','rockeye'], cap:[40,40], eng:100, pow:2.0},
  fivalyrie:{p:['subach','proms'], pa:['subach','promr','proms','kayser'], s:['harpoon'], sa:['harpoon','rockeye','trebuchet'], cap:[60], eng:100, pow:2.0},
  boathena:{p:['promr','morningstar'], pa:['subach','promr','morningstar'], s:['trebuchet','stiletto2'], sa:['rockeye','harpoon','trebuchet','stiletto2'], cap:[80,80], eng:100, pow:3.0}
};
// A hull without an entry (should not happen) flies this.
const BANKS_FALLBACK = {p:['promr'], pa:['promr'], s:['harpoon'], sa:['harpoon'], cap:[40], eng:150, pow:2.4};
function shipBanks(key){ return SHIP_BANKS[key] || BANKS_FALLBACK; }

// Game values from the table values, once at load.
(function finishArsenal(){
  for(const w of ARSENAL_P){
    const f = w.fs;
    w.dmg  = f.d / PRI_ANCHOR.d;
    w.f    = {a:f.a/PRI_ANCHOR.a, s:f.s/PRI_ANCHOR.s, u:f.u/PRI_ANCHOR.u};
    w.wait = Math.max(4, Math.round(f.w*60));
    w.rate = w.wait / FR_BASE_STEPS;
    w.spd  = Math.min(BOLT_SPD_MAX, f.v*MPS_TO_PX);
    w.life = Math.round(f.l*60);
    w.en   = f.e;
    w.range = 0;
  }
  for(const w of ARSENAL_S){
    const f = w.fs, anc = (w.cls==='bomb') ? BOMB_ANCHOR : MIS_ANCHOR;
    w.dmg  = f.d * anc.game / anc.d;
    w.f    = {a:f.a/anc.a, s:f.s/anc.s, u:f.u/anc.u};
    w.cd   = Math.max(6, Math.round(f.w*60));
    w.spd  = f.v*MPS_TO_PX;
    w.life = Math.round(f.l*60);
    // Turn: FS2's $Turn Time is the time for a half circle, whatever the
    // speed. A missile steers by adding turn to its velocity each step, so
    // a faster one needs more of it to come round as quickly (v187b: the
    // Harpoon is faster than the old MX-64 and sailed past what it chased).
    // Bombs keep their slow fixed rate.
    w.turn = (w.cls==='bomb') ? 0.06 / (f.turn||1)
                              : w.spd * Math.PI / (60 * (f.turn||1));
    w.cargo = f.cargo;
    if(f.child){            // spawned warheads, same anchor as the round
      w.childDmg  = f.child.d * anc.game / anc.d;
      w.childSpd  = f.child.v * MPS_TO_PX;
      w.childLife = Math.max(1, Math.round(f.child.l*60));
    }
  }
})();

// ── BANK STATE ───────────────────────────────────────────────
// player.pb: primary banks [{key, t}], player.sb: secondary banks
// [{key, ammo, max, t}], player.pMode: 0 = bank 1, 1 = bank 2, 2 = linked,
// player.sSel: the selected secondary bank, player.en / enMax / enRe: the
// weapon energy store and its recharge per step.
// The fit of every hull the player has set up in this run, so going back
// to a hull gives back its banks.
let FITS = {};
function bankAmmoMax(shipKey, i, wkey){
  const b = shipBanks(shipKey), w = secDefP(wkey);
  const cap = (b.cap && b.cap[i] != null) ? b.cap[i] : (b.cap && b.cap.length ? b.cap[b.cap.length-1] : 40);
  return Math.max(1, Math.floor(cap / Math.max(0.01, w.cargo || 1)));
}
function priDefP(key){ for(const w of ARSENAL_P) if(w.key===key) return w; return priDef(key); }
function secDefP(key){ for(const w of ARSENAL_S) if(w.key===key) return w; return ARSENAL_S[0]; }
// The default fit of a hull, or what the player made of it this run.
function fitFor(key){
  const b = shipBanks(key);
  const f = FITS[key];
  return {p:(f && f.p) ? f.p.slice() : b.p.slice(0,2), s:(f && f.s) ? f.s.slice() : b.s.slice(0,3)};
}
// Puts a fit onto the player. keepSec: fractions of each rack to keep.
function setBanks(shipKey, fit, keepSec){
  const b = shipBanks(shipKey);
  player.pb = fit.p.map(function(k){ return {key:k, t:0}; });
  player.sb = fit.s.map(function(k, i){
    const mx = bankAmmoMax(shipKey, i, k);
    return {key:k, max:mx, ammo:mx, t:0};
  });
  if(keepSec != null) for(const s of player.sb) s.ammo = Math.min(s.max, Math.round(s.max*keepSec));
  if(!(player.pMode >= 0) || player.pMode >= bankModes()) player.pMode = 0;
  if(!(player.sSel >= 0) || player.sSel >= player.sb.length) player.sSel = 0;
  player.enMax = Math.max(1, (b.eng || 150) * EN_STORE_K);
  player.enRe  = (b.pow || 2.4) * EN_REGEN_K / 60;
  if(player.en == null || !(player.en >= 0) || player.en > player.enMax) player.en = player.enMax;
  syncLegacyWeapons();
}
// How many primary modes the fitted banks give: one per bank, plus linked.
function bankModes(){
  const n = (player.pb || []).length;
  return n >= 2 ? 3 : Math.max(1, n);
}
// The banks that fire in the current mode.
function firingBanks(){
  const pb = player.pb || [];
  if(pb.length < 2) return pb;
  if(player.pMode === 2) return pb;
  return [pb[player.pMode] || pb[0]];
}
function selSecBank(){ return (player.sb || [])[player.sSel || 0] || null; }
// The old single-weapon fields, still read by the practice log, the hangar
// and a few tests: the first firing bank and the selected rack.
function syncLegacyWeapons(){
  const fb = firingBanks()[0];
  player.pri = fb ? fb.key : 'promr';
  const s = selSecBank();
  player.sec = s ? s.key : '';
  player.secAmmo = s ? s.ammo : 0;
  player.secMax  = s ? s.max : 0;
  player.secType = (s && secDefP(s.key).cls==='bomb') ? 'bomb' : 'missile';
}
// Mouse wheel up / Q: the next primary mode (bank 1, bank 2, linked).
function cyclePrimary(){
  const n = bankModes();
  if(n < 2) return;
  player.pMode = ((player.pMode||0) + 1) % n;
  syncLegacyWeapons();
  const pb = player.pb;
  const txt = player.pMode===2 ? 'PRIMARIES LINKED' : weaponNameP(priDefP(pb[player.pMode].key)).toUpperCase();
  notice(txt, 'info');
  sndPlay('ui_click', player.x);
}
// Mouse wheel down / E: the next secondary bank.
function cycleSecondary(){
  const n = (player.sb || []).length;
  if(n < 2) return;
  player.sSel = ((player.sSel||0) + 1) % n;
  syncLegacyWeapons();
  notice(weaponNameP(secDefP(player.sb[player.sSel].key)).toUpperCase(), 'info');
  sndPlay('ui_click', player.x);
}
function weaponNameP(w){ return (typeof weaponName === 'function') ? weaponName(w) : w.name; }

// Every step: the store recharges and the bank clocks run down.
function bankTick(){
  if(!player.pb) return;
  if(player.en < player.enMax) player.en = Math.min(player.enMax, player.en + player.enRe);
  for(const b of player.pb) if(b.t > 0) b.t--;
  for(const s of (player.sb || [])) if(s.t > 0) s.t--;
}
// The trigger is held: every firing bank that is ready and can pay fires.
// Returns true when something left the barrels.
function pShootBanks(){
  let fired = false;
  for(const b of firingBanks()){
    if(b.t > 0) continue;
    const w = priDefP(b.key);
    if(player.en < w.en){ if(!fired) player.enEmptyT = 20; continue; }
    player.en -= w.en;
    b.t = w.wait;
    pShootWith(w, bankMounts(b));
    fired = true;
  }
  return fired;
}
// Which barrels a bank fires from. With two banks the mounts are shared
// out between them; linked, every barrel fires.
function bankMounts(b){
  const pb = player.pb || [];
  if(pb.length < 2) return null;
  return {bank:pb.indexOf(b), of:pb.length};
}

// ── MISSION FITS ─────────────────────────────────────────────
// A mission that needs a certain weapon puts it into a bank, as FS2
// missions do: sec into the first secondary bank (the Stiletto in M57),
// giveSec into the last (the TAG from M67). The rack is filled.
function missionSec(key, last){
  if(!player.sb || !player.sb.length || !key) return false;
  const i = last ? player.sb.length-1 : 0;
  const mx = bankAmmoMax(player.ship, i, key);
  player.sb[i] = {key:key, max:mx, ammo:mx, t:0};
  player.sSel = i;
  syncLegacyWeapons();
  return true;
}
// The old secondary keys of the mission data, onto the arsenal.
const OLD_SEC_KEY = {stiletto:'stiletto2', tag:'tagc', mx64:'harpoon', cyclops:'cyclops', infyrno:'infyrno', tornado:'tornado'};
function arsenalKey(k){ return OLD_SEC_KEY[k] || k; }

// ── UNLOCKS ──────────────────────────────────────────────────
// Standard fit always, everything else the hull may carry by points
// (Silvio). fromWave: handed out with a mission (Dante 61, TAG-C 67).
function weaponOpenFor(w, shipKey){
  const b = shipBanks(shipKey);
  if(b.p.indexOf(w.key) >= 0 || b.s.indexOf(w.key) >= 0) return true;
  return weaponOpen(w);
}
// What a bank may take: the hull's allowed list, plus the game's own guns
// for every fighter and bomber (Sidhe, Dante), in the order of the arsenal.
function bankChoices(shipKey, pri){
  const b = shipBanks(shipKey), out = [];
  if(pri){
    for(const w of ARSENAL_P) if(b.pa.indexOf(w.key) >= 0 || b.p.indexOf(w.key) >= 0) out.push(w);
    for(const k of ['scatter','dante']){ const w = priDef(k); if(w && w.key===k) out.push(w); }
  } else {
    for(const w of ARSENAL_S) if(b.sa.indexOf(w.key) >= 0 || b.s.indexOf(w.key) >= 0) out.push(w);
  }
  return out;
}
// The next weapon a bank can be switched to (rearm list). Skips what is
// not open yet.
function nextChoice(shipKey, pri, cur){
  const list = bankChoices(shipKey, pri).filter(function(w){ return weaponOpenFor(w, shipKey); });
  if(!list.length) return cur;
  let i = -1;
  for(let k=0;k<list.length;k++) if(list[k].key===cur) i = k;
  return list[(i+1) % list.length].key;
}

// ── EMP ──────────────────────────────────────────────────────
// Fighters and bombers near the blast lose their fire control for a while.
const EMP_R = 150, EMP_T = 300;
function empBurst(x, y){
  for(const e of enemies){
    if(!(e.type==='fighter' || e.type==='bomber') || e.dead) continue;
    if(Math.hypot(e.x-x, e.y-y) < EMP_R) e.empT = EMP_T;
  }
  spawnRing(x, y, EMP_R, 30, 2, 140, 200, 255);
}
