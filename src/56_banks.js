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
// v212 (Silvio): no round may be slower than the player's ship - 1.1 x the
// fastest small craft (90 m/s, SMALL_VEL) on the game scale, before TEMPO_K
const PROJ_MIN = 4.5;
function pSpd(v){ return Math.max(v || 0, PROJ_MIN); }
// Blast radii (FS2 metres) on the field: the capital-ship scale, where a
// cruiser of ~250 m is ~100 px long (v190).
const BLAST_PX_PER_M = 0.4;
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
   col:'#ff6a3a', glow:'rgba(255,100,50,0.34)', note:'hull and subsystems, useless against shields'},
  // v240 (F21, Silvio 14.10.2026): the FS1 guns, for the FS1 strand only.
  // Values straight from FSPort's weapons.tbl, on the same anchor as the
  // FS2 guns above. era: the strand they belong to. fs1: the original FS1
  // mission from which the player (p) and the computer (c) carry it.
  {key:'ml16', name:'ML-16 Laser', era:'fs1', fs1:{p:1, c:1}, snd:'L_light',
   fs:{d:5, v:450, w:0.2, l:2.0, e:0.2, a:1, s:0.1, u:0.3},
   col:'#ff8f8f', glow:'rgba(255,110,110,0.30)', note:'the old standard laser, quick and light'},
  {key:'dadv', name:'D-Advanced', era:'fs1', fs1:{p:17, c:17}, snd:'L_disrupter',
   fs:{d:25, v:575, w:0.6, l:1.5, e:0.75, a:0, s:1, u:1},
   col:'#d6a2ff', glow:'rgba(200,140,255,0.32)', note:'shields and subsystems only - no hull damage'},
  {key:'avenger', name:'Avenger', era:'fs1', fs1:{p:8, c:2}, snd:'L_avenge',
   fs:{d:16, v:525, w:0.25, l:1.9, e:0.3, a:1.25, s:0.85, u:0.35},
   // F71 (v258, Silvio): orange-white, not blue-white.
   col:'#ffd6a8', glow:'rgba(255,140,50,0.38)', note:'the fleet gun, good against everything'},
  {key:'prom1', name:'Prometheus', era:'fs1', fs1:{p:16, c:17}, snd:'L_flux',
   fs:{d:20, v:450, w:0.3, l:2.0, e:0.4, a:1.3, s:0.7, u:0.35},
   col:'#ccff88', glow:'rgba(180,255,80,0.30)', note:'hard on hulls'},
  {key:'banshee', name:'Banshee', era:'fs1', fs1:{p:21, c:21}, snd:'L_banshee',
   fs:{d:26, v:650, w:0.4, l:1.5, e:1.6, a:0.7, s:1.2, u:0.35},
   col:'#ffb466', glow:'rgba(255,160,80,0.34)', note:'tears shields, empties the store'}
];
// Secondaries. bigFirst (v189, Silvio): slow to turn, so the seeker goes
// for a capital ship when there is one and only takes a fighter otherwise.
// cargo: rack space per round (SBank Capacity / cargo =
// rounds). turn: FS2 turn time in seconds. homing: 'heat' goes for the
// nearest, 'aspect' keeps the target it was fired at.
const ARSENAL_S = [
  {key:'harpoon', name:'Harpoon', cls:'missile', unlock:0, snd:'m_shrike', homing:'aspect',
   fs:{d:100, v:250, w:2.0, l:5.0, a:1.0, s:0.8, u:0.5, cargo:2.5, turn:1.0, lock:2.0},
   note:'the all-round aspect seeker'},
  {key:'rockeye', name:'Rockeye', cls:'missile', unlock:0, snd:'m_wasp', homing:'heat',
   fs:{d:45, v:190, w:0.5, l:10.0, a:1.0, s:0.8, u:0.8, cargo:4, turn:0.85, cone:100},
   note:'heat seeker, quick off the rail'},
  {key:'tempest', name:'Tempest', cls:'missile', unlock:3000, snd:'m_fury', homing:null,
   fs:{d:45, v:360, w:0.3, l:1.8, a:0.9, s:0.5, u:0.6, cargo:0.25, turn:1},
   note:'dumbfire, a deep rack, short reach'},
  {key:'tornado', name:'Tornado', cls:'missile', unlock:10000, snd:'m_swarm', homing:'aspect',
   swarm:4, fan:0.6,
   fs:{d:25, v:230, w:2.5, l:7.0, a:2.0, s:1.0, u:0.3, cargo:1.25, turn:1.25, lock:2.25},
   note:'four faster seekers, each its own target'},
  {key:'emp', name:'EMP Adv.', cls:'missile', unlock:14000, snd:'m_emp', homing:'aspect', emp:true,
   fs:{d:45, v:275, w:2.0, l:5.0, a:1.0, s:0.8, u:0.5, cargo:4, turn:1.0, lock:2.0},
   note:'fighters near the blast stop firing for a while'},
  {key:'infyrno', name:'Infyrno', cls:'missile', unlock:18000, snd:'m_cluster', homing:null,
   burst:true, children:14, shardRange:90,
   fs:{d:150, v:120, w:5.0, l:7.0, a:1.0, s:0.75, u:1.0, cargo:10, turn:1,
       child:{d:100, v:250, l:0.3}},      // 14 x "Cluster Bomb Baby"
   note:'fired straight - press again to burst it into 14 small seekers'},
  {key:'trebuchet', name:'Trebuchet', cls:'missile', unlock:18000, snd:'m_angel', homing:'aspect', bigFirst:true,
   fs:{d:350, v:280, w:6.0, l:18.0, a:0.9, s:0.5, u:2.4, cargo:8, turn:3.0, lock:3.5},
   note:'long range, heavy, for subsystems'},
  {key:'stiletto2', name:'Stiletto II', cls:'missile', unlock:26000, snd:'m_stiletto', homing:'heat', subs:true, bigFirst:true,
   fs:{d:775, v:220, w:2.0, l:25.0, a:0.01, s:0.0, u:1.0, cargo:8, turn:1.0, cone:80},
   note:'into the subsystems, not the hull'},
  {key:'tagc', name:'TAG-C', cls:'missile', unlock:0, fromWave:67, snd:'m_angel', homing:'aspect', tag:true,
   fs:{d:10, v:205, w:8.0, l:13.0, a:0.1, s:0.1, u:0.1, cargo:4, turn:1.75, lock:2.5},
   note:'marks the target - our beams find it, even in the nebula'},
  {key:'cyclops', name:'Cyclops', cls:'bomb', unlock:0, snd:'m_tsunami', homing:'aspect', bigFirst:true,
   fs:{d:2000, v:95, w:20.0, l:25.0, a:1.0, s:0.02, u:0.5, cargo:15, turn:1.0, lock:5.0,
       blast:{i:100, o:200}},             // FS2 inner / outer radius (v190)
   note:'slow and heavy, for hulls that cannot dodge'},
  // v240 (F21): the FS1 missiles (fighters) and bombs (bombers), for the
  // FS1 strand only. d v w l a s u cargo from FSPort's weapons.tbl as
  // approved. Not in the approved values, so taken as in FS: turn 1 s,
  // a heat seeker's view cone 90 degrees (the FS default), an aspect
  // seeker's lock as the FS2 Harpoon (missiles) or Cyclops (bombs). Blast
  // radii only on bombs: missiles only hit what they hit (v190). The
  // Stiletto is scaled like its FS2 successor, the Stiletto II, on the
  // missile anchor; on the bomb anchor it would do a tenth of that.
  {key:'mx50', name:'MX-50', cls:'missile', era:'fs1', fs1:{p:1, c:2}, snd:'m_wasp', homing:'heat',
   fs:{d:25, v:150, w:0.75, l:10.0, a:1, s:0.4, u:1, cargo:4, turn:1, cone:90},
   note:'the standard heat seeker'},
  {key:'fury', name:'Fury', cls:'missile', era:'fs1', fs1:{p:1, c:1}, snd:'m_fury', homing:null,
   fs:{d:30, v:300, w:0.3, l:3.0, a:1, s:0.5, u:0.6, cargo:0.5, turn:1},
   note:'dumbfire, a deep rack, short reach'},
  {key:'interceptor', name:'Interceptor', cls:'missile', era:'fs1', fs1:{p:11, c:8}, snd:'m_shrike', homing:'aspect',
   fs:{d:150, v:250, w:2.0, l:5.0, a:1, s:0.8, u:0.5, cargo:4, turn:1, lock:2.0},
   note:'a heavy aspect seeker against fighters'},
  {key:'phoenix', name:'Phoenix V', cls:'missile', era:'fs1', fs1:{p:13, c:5}, snd:'m_angel', homing:'aspect', bigFirst:true,
   fs:{d:350, v:175, w:5.0, l:10.0, a:1, s:0.5, u:0.8, cargo:8, turn:1, lock:2.0},
   note:'long range, heavy, slow to reload'},
  {key:'hornet1', name:'Hornet', cls:'missile', era:'fs1', fs1:{p:18, c:21}, snd:'m_swarm', homing:'aspect',
   fs:{d:25, v:190, w:2.0, l:7.0, a:2, s:1, u:0.3, cargo:1, turn:1, lock:2.0},
   note:'a light aspect seeker, a deep rack'},
  {key:'dmissile', name:'D-Missile', cls:'bomb', era:'fs1', fs1:{p:24, c:29}, snd:'m_mag', homing:'aspect', bigFirst:true,
   fs:{d:1, v:80, w:5.0, l:15.0, a:0, s:0, u:1, cargo:8, turn:1, lock:5.0, blast:{i:10, o:400}},
   note:'a bomb for the systems of a big ship'},
  {key:'synaptic', name:'Synaptic', cls:'bomb', era:'fs1', fs1:{p:15, c:13}, snd:'m_cluster', hitSnd:'clusterboom', homing:'aspect', bigFirst:true,
   fs:{d:60, v:90, w:5.0, l:2.5, a:1, s:0.75, u:1, cargo:15, turn:1, lock:5.0, blast:{i:50, o:100}},
   note:'a cluster bomb'},
  {key:'stiletto1', name:'Stiletto', cls:'bomb', anchor:'missile', era:'fs1', fs1:{p:10, c:10}, snd:'m_stiletto', homing:'heat', subs:true, bigFirst:true,
   fs:{d:775, v:150, w:2.0, l:15.0, a:0.01, s:0, u:1, cargo:8, turn:1, cone:90},
   note:'into the subsystems, not the hull'},
  {key:'tsunami', name:'Tsunami', cls:'bomb', era:'fs1', fs1:{p:13, c:13}, snd:'m_tsunami', homing:'aspect', bigFirst:true,
   fs:{d:1500, v:60, w:20.0, l:25.0, a:1, s:0.02, u:2, cargo:15, turn:1, lock:5.0, blast:{i:50, o:150}},
   note:'the heavy bomb'},
  {key:'harbinger', name:'Harbinger', cls:'bomb', era:'fs1', fs1:{p:26, c:26}, snd:'m_harbinger', hitSnd:'clusterboom', homing:'aspect', bigFirst:true,
   fs:{d:3200, v:50, w:30.0, l:30.0, a:1, s:0.01, u:16, cargo:40, turn:1, lock:5.0, blast:{i:100, o:250}},
   note:'the heaviest bomb there is'}
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
function shipBanks(key){
  if(fs1Arms()) return fs1Banks(key);
  return SHIP_BANKS[key] || BANKS_FALLBACK;
}

// ── FS1 BANKS (v240, F21) ────────────────────────────────────
// The FS1 strand flies the FS1 arsenal. Default banks and rack capacity per
// hull from FSPort's ships.tbl ($Default PBanks, $Default SBanks, $SBank
// Capacity). Silvio: Disruptor and Flail are out, also for the computer -
// the Disruptor becomes the D-Advanced (before that is available, the
// Avenger), the Flail the Avenger. The Shivans keep their lasers; their
// missiles are the Terran ones.
const FS1_FITS = {
  fiapollo:{p:['avenger','ml16'], s:['mx50','mx50'], cap:[40,40]},
  fivalyrie:{p:['ml16','prom1'], s:['mx50'], cap:[60]},
  fiherc:{p:['avenger','dadv'], s:['interceptor','fury'], cap:[60,60]},
  filoki:{p:['avenger','dadv'], s:['interceptor'], cap:[20]},
  boathena:{p:['avenger','avenger'], s:['phoenix','stiletto1'], cap:[80,80]},
  bomedusa:{p:['avenger'], s:['hornet1','mx50','tsunami'], cap:[40,80,80]},
  boursa:{p:['avenger','avenger'], s:['mx50','synaptic','tsunami'], cap:[80,80,80]},
  fianubis:{p:['ml16'], s:['fury'], cap:[60]},
  fihorus:{p:['avenger','avenger'], s:['mx50','phoenix'], cap:[40,40]},
  fiseth:{p:['ml16','avenger'], s:['mx50','stiletto1'], cap:[40,80]},
  fitoth:{p:['prom1'], s:['interceptor'], cap:[80]},
  boamun:{p:['banshee','avenger'], s:['tsunami','synaptic','synaptic'], cap:[60,60,80]},
  boosiris:{p:['avenger'], s:['synaptic','stiletto1','phoenix'], cap:[40,40,20]},
  fibasilisk:{p:['shm','shh'], s:['phoenix','hornet1'], cap:[80,80]},
  fidragon:{p:['shh','shh'], s:['interceptor'], cap:[20]},
  fimanticore:{p:['shm'], s:['interceptor','mx50'], cap:[40,40]},
  fiscorpion:{p:['shl','shh'], s:['mx50'], cap:[40]},
  boshaitan:{p:['shl','shh'], s:['mx50'], cap:[40]},
  bonephilim:{p:['shl'], s:['mx50','synaptic','phoenix'], cap:[40,40,40]}
};
// What stands in for a weapon that is not out yet, in the order of the
// FS1 campaign. The ML-16, the Fury and the Shivan lasers are there from
// the first mission; a bomb with nothing before it leaves the bank empty.
const FS1_STANDIN = {
  dadv:'avenger', avenger:'ml16', prom1:'avenger', banshee:'avenger',
  interceptor:'mx50', phoenix:'mx50', hornet1:'mx50', mx50:'fury',
  harbinger:'tsunami', tsunami:'stiletto1', synaptic:'stiletto1', dmissile:'stiletto1'
};
// Only the written missions of the FS1 strand fly it. The practice mode
// (?fs1=) and the tests keep the arsenal they always had.
function fs1Arms(){
  return typeof currentEra !== 'undefined' && currentEra === 'fs1'
      && typeof missionOrig !== 'undefined' && missionOrig > 0;
}
function fs1Def(key){
  for(const w of ARSENAL_P) if(w.key===key) return w;
  for(const w of ARSENAL_S) if(w.key===key) return w;
  return null;
}
// Is this FS1 weapon out yet, for the player (who 'p') or the computer
// ('c')? Weapons that are not FS1 ones (the Shivan lasers) always are.
function fs1Out(key, who){
  const w = fs1Def(key);
  if(!w || !w.fs1) return true;
  return missionOrig >= (w.fs1[who] || 1);
}
// The weapon actually carried for a table entry: the entry, or what stands
// in for it until it is out. '' when nothing does (a bomb before mission 10).
function fs1Carried(key, who){
  let k = key, n = 0;
  while(k && !fs1Out(k, who) && n++ < 8) k = FS1_STANDIN[k] || '';
  return k || '';
}
// The banks of a hull in the FS1 strand, for the player. Its default fit as
// FS1 had it, every weapon replaced by its stand-in until it is out. It may
// carry every FS1 gun, and the FS1 missiles (fighters) or bombs (bombers).
function fs1Banks(key){
  const b = SHIP_BANKS[key] || BANKS_FALLBACK, d = FS1_FITS[key];
  const bomber = (typeof isBomberHull === 'function') && isBomberHull(key);
  const p = (d ? d.p : b.p.map(function(){ return 'avenger'; }))
              .map(function(k){ return fs1Carried(k, 'p') || 'ml16'; }).slice(0, 2);
  const s = (d ? d.s : b.s.map(function(){ return bomber ? 'stiletto1' : 'mx50'; }))
              .map(function(k){ return fs1Carried(k, 'p'); })
              .filter(function(k){ return !!k; }).slice(0, 3);
  const pa = [], sa = [];
  for(const w of ARSENAL_P) if(w.era==='fs1') pa.push(w.key);
  for(const w of ARSENAL_S) if(w.era==='fs1' && (w.cls==='bomb')===bomber) sa.push(w.key);
  return {p:p, pa:pa, s:s, sa:sa, cap:(d && d.cap) || b.cap, eng:b.eng, pow:b.pow};
}
// The computer's loadout in the FS1 strand (aiLoadout, 55_arms.js): the
// same table with the computer's dates. A fighter fires its first missile
// bank, a bomber its first bomb.
function fs1AiLoadout(key, old){
  const d = FS1_FITS[key];
  if(!d) return old;
  const p = d.p.map(function(k){ return fs1Carried(k, 'c') || 'ml16'; });
  const sec = d.s.map(function(k){ return fs1Carried(k, 'c'); }).filter(function(k){ return !!k; });
  const bomb = sec.find(function(k){ const w = fs1Def(k); return w && w.cls==='bomb'; });
  const mis  = sec.find(function(k){ const w = fs1Def(k); return w && w.cls!=='bomb'; });
  const bomber = /^bo/.test(key);
  return {p:p.length > 1 ? p : p[0], s:(bomber ? (bomb || mis) : (mis || bomb)) || 'fury',
          pair:!!(old && old.pair)};
}

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
    // anchor: a bomb scaled like a missile (the FS1 Stiletto, v240)
    const f = w.fs, anc = ((w.anchor || w.cls)==='bomb') ? BOMB_ANCHOR : MIS_ANCHOR;
    w.dmg  = f.d * anc.game / anc.d;
    w.f    = {a:f.a/anc.a, s:f.s/anc.s, u:f.u/anc.u};
    w.cd   = Math.max(6, Math.round(f.w*60));
    w.spd  = f.v*MPS_TO_PX;
    w.life = Math.round(f.l*60);
    // v212 (Silvio): no round slower than the ships (PROJ_MIN); a raised
    // one keeps its FS reach, so it lives shorter
    if(w.spd < PROJ_MIN){ w.life = Math.max(1, Math.round(w.life*w.spd/PROJ_MIN)); w.spd = PROJ_MIN; }
    // Turn: FS2's $Turn Time is the time for a half circle, whatever the
    // speed. A missile steers by adding turn to its velocity each step, so
    // a faster one needs more of it to come round as quickly (v187b: the
    // Harpoon is faster than the old MX-64 and sailed past what it chased).
    // Bombs keep their slow fixed rate.
    w.turn = (w.cls==='bomb') ? 0.06 / (f.turn||1)
                              : w.spd * Math.PI / (60 * (f.turn||1));
    w.cargo = f.cargo;
    // v210: FS2 $Min Lock Time of an aspect seeker (steps) and +View Cone
    // of a heat seeker (half of it, rad) - weapons.tbl
    w.lockT = Math.round((f.lock || 0)*60);
    w.cone  = (f.cone || 0)*Math.PI/360;
    if(f.blast) w.blast = {i:f.blast.i*BLAST_PX_PER_M, o:f.blast.o*BLAST_PX_PER_M};
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
// Which arsenal the fitted banks came from: 'fs1' or 'std' (v240).
let armsNow = 'std';
// The primary mode the player picked last, and for how many banks (F57,
// Silvio 22.10.2026): a new mission or a hull swap puts it back as long
// as the number of primary banks is the same.
let PMODE_PREF = null;
// The fit a hull was given in one strand is not the fit of another (v240):
// FS1 weapons do not go into an FS2 rack and the other way round.
function fitKey(key){ return fs1Arms() ? 'fs1:' + key : key; }
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
  const f = FITS[fitKey(key)];
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
  if(PMODE_PREF && PMODE_PREF.n === player.pb.length && PMODE_PREF.mode < bankModes()) player.pMode = PMODE_PREF.mode;
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
// dir -1 (v207): the previous one (FS2: comma)
function cyclePrimary(dir){
  const n = bankModes();
  if(n < 2) return;
  player.pMode = ((player.pMode||0) + (dir < 0 ? n - 1 : 1)) % n;
  PMODE_PREF = {n:(player.pb||[]).length, mode:player.pMode};
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
// v253: a gun the mission hands out goes into the first primary bank (the
// D-Advanced in Shieldbreaker, Silvio), whether it is out yet or not.
function missionPri(key){
  if(!player.pb || !player.pb.length || !key) return false;
  // F72 (v258): a list fits one gun per bank, as far as there are banks
  // (two Avengers in Rain on Ribos IV).
  if(Array.isArray(key)){
    for(let i=0;i<key.length && i<player.pb.length;i++) player.pb[i] = {key:key[i], t:0};
    syncLegacyWeapons();
    return true;
  }
  player.pb[0] = {key:key, t:0};
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
    // The game's own guns belong to the random arc, not to the FS1 strand.
    if(!fs1Arms())
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
// v190 (Silvio): half the FS2 outer radius of 300 m is enough.
const EMP_R = Math.round(150*BLAST_PX_PER_M), EMP_T = 300;
function empBurst(x, y){
  for(const e of enemies){
    if(!(e.type==='fighter' || e.type==='bomber') || e.dead) continue;
    if(Math.hypot(e.x-x, e.y-y) < EMP_R) e.empT = EMP_T;
  }
  spawnRing(x, y, EMP_R, 30, 2, 140, 200, 255);
}

// ── BLAST (v190) ─────────────────────────────────────────────
// A bomb goes off over an area, as in FS2: full damage out to the inner
// radius, falling off to nothing at the outer one. Besides the ship it
// struck it hits every enemy in reach - and the player who flew in too
// close (Silvio: that is what keeps a bomber off its target). Missiles
// only ever hit what they hit.
function boxDist(x, y, r){
  const dx = Math.max(r[0]-x, 0, x-(r[0]+r[2])), dy = Math.max(r[1]-y, 0, y-(r[1]+r[3]));
  return Math.hypot(dx, dy);
}
function blastFall(d, bl){ return d <= bl.i ? 1 : (d >= bl.o ? 0 : 1-(d-bl.i)/(bl.o-bl.i)); }
function warheadBlast(b, bl, struck){
  for(let j=enemies.length-1;j>=0;j--){
    const e = enemies[j];
    if(e===struck || e.dead || e.warp>0) continue;
    if(b.ally && playerOnly(e)) continue;
    // v249: and through a ship that is to be taken (FS1 M4)
    if(b.ally && (e.captureLock || e.captured)) continue;
    const k = blastFall(boxDist(b.x, b.y, eBox(e)), bl);
    if(k <= 0) continue;
    DMG_F = b.f || null;
    damageEnemy(e, b.dmg*k, b.x, b.y, !b.ally, 'sec', 'bomb');
    DMG_F = null;
    if(e.hp<=0 && !e.dead) killEnemy(e, j, true, false);
  }
  // An allied bomber's blast spares us; our own does not.
  if(b.ally || GS!=='playing' || !(player.hp>0) || inJump()) return;
  const k = blastFall(boxDist(b.x, b.y, pBox()), bl);
  if(k <= 0) return;
  const dmg = b.dmg*k;
  plogSrc('own blast');
  if(player.sh>0){
    const abs = Math.min(player.sh, dmg);
    player.sh -= abs; player.shDelay = 90; player.shHit = SH_FLASH;
    shieldHit(player.x, player.y);
    if(dmg>abs){ player.hp -= dmg-abs; hullHit(player.x, player.y); }
  } else { player.hp -= dmg; hullHit(player.x, player.y); }
  if(player.hp<=0) playerDie();
}
