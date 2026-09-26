// ── ERAS ─────────────────────────────────────────────────────
// Which hulls exist, and which rules hold, depends on when the campaign is
// set. Kept out of ROLES on purpose: the packer reads that block and takes
// everything in quotes for a ship key, so it tolerates no structure of its
// own. These are plain arrays and the packer never looks at them.
const ERA_POOLS = {
  fs1: {
    ter_fighters:   ['fiapollo','fivalyrie','fiulysses','fiherc'],
    ter_bombers:    ['boathena','bomedusa','boursa'],
    ter_cruisers:   ['crfenris','crleviathan'],
    vas_fighters:   ['fianubis','fihorus','fiseth','fitoth'],
    vas_bombers:    ['boamun','boosiris'],
    vas_cruisers:   ['craten'],
    sh_fighters:    ['fibasilisk','fidragon','fimanticore','fiscorpion'],
    sh_bombers:     ['boshaitan','bonephilim'],
    sh_cruisers:    ['crcain','crlilith']
  }
};

// noBeams: FS1 has no beam weapons at all, the Lucifer excepted. That
// needs no replacement weapon - capitalFire() already fires conventional
// rounds from the gun mounts, quite separately from the beams. Skipping
// initBeams leaves the turrets doing exactly what they did.
// shieldWave: shields reach the fleet with the prototypes from The Hammer
// and the Anvil. Before that wave the player and his escorts fly without.
const ERA_RULES = {
  // shivanShieldPen: share of a primary hit that a Shivan shield actually
  // loses. At 0.25 a gun needs four times its damage to bring the shield
  // down and nothing reaches the hull until it is gone. That is the FS1
  // picture: the fleet's guns are useless against them and missiles are
  // the answer. Lifted at shieldWave, when the fleet catches up.
  // avengerWave: ab hier wirken Primaerwaffen normal gegen shivanische
  // Schilde. Eine Welle vor den Schilden, weil das Kommandobriefing von
  // The Hammer and the Anvil die Avenger-Kanone auf allen terranischen und
  // vasudanischen Schiffen meldet, ausdruecklich als wirksam dagegen.
  fs1: {noBeams:true, shieldWave:9, avengerWave:8, shivanShieldPen:0.25},
  str: {noBeams:true, shieldWave:0},
  fs2: {noBeams:false, shieldWave:0}
};

let currentEra = 'fs2';        // the endless mode is FS2 and stays so
let waveFeud = false;          // hostile factions fighting each other

function eraRule(k){
  const r = ERA_RULES[currentEra];
  return r ? r[k] : undefined;
}
function eraPool(name){
  const p = ERA_POOLS[currentEra];
  return (p && p[name]) ? p[name] : null;
}
// True while the fleet has not been given shields yet.
function eraShieldsOff(){
  const w = eraRule('shieldWave');
  return !!w && wave < w;
}
// How much of a hit a shield really loses. One everywhere except against
// Shivan hulls in the early part of FS1, where a primary bolt mostly comes
// straight back off. Missiles, bombs and beams are exempt: they were the
// answer in the original and they stay the answer here.
function shieldPen(e, kind){
  const p = eraRule('shivanShieldPen');
  if(!p) return 1;
  const aw = eraRule('avengerWave');
  if(aw && wave >= aw) return 1;          // the Avenger cannon arrives
  if(e.faction !== 'shivan') return 1;
  if(kind==='sec' || kind==='bomb' || kind==='beam') return 1;
  return p;
}

// The one place the player's shield is set. There were two, and only one
// of them knew about the era: dying in an FS1 wave handed the shield back
// at full, after which it never recharged because the recharge did know.
function resetPlayerShield(){
  player.sh = eraShieldsOff() ? 0 : player.maxSh;
}

// ── FS1 CAMPAIGN ─────────────────────────────────────────────
// Reached with ?fs1=1. The endless mode is untouched and still runs
// without the parameter.
// ?fs1=1 startet die Kampagne, ?fs1=7 startet sie bei Welle 7. Ohne den
// Sprungparameter waren die Wellen 8 bis 10 unerreichbar, weil vorher die
// Leben ausgehen.
const SCRIPT_MATCH = /[?&]m=(\d+)/.exec(location.search);
const SCRIPT_ONE = SCRIPT_MATCH ? (parseInt(SCRIPT_MATCH[1],10)||0) : 0;
const FS1_MATCH = /[?&]fs1=(\d+)/.exec(location.search);
const FS1_MODE  = !!FS1_MATCH;
const FS1_FIRST_RAW = FS1_MATCH ? (parseInt(FS1_MATCH[1],10)||1) : 1;
// FS1_PLAN steht weiter unten. Beim Laden darauf zuzugreifen wuerde das
// Skript stumm abbrechen - genau die Falle aus v79, siehe Handoff
// Abschnitt 11. Deshalb erst im Aufruf klemmen.
function fs1First(){
  return Math.max(1, Math.min(FS1_PLAN.length, FS1_FIRST_RAW));
}

// Uebungsmodus. Nur in der Kampagne: im Endlosmodus ist der Lebensverlust
// die einzige Uhr, die laeuft.
let practiceMode = false;

// What the player is allowed to fly, checked against the command briefings
// of Acts 1 and 2, where each of these is announced as new technology.
// The Hercules is deliberately late: three gun mounts in an early wave
// would walk straight through the Shivan shield rule.
const FS1_SHIPS = [
  {wave:1,  key:'fiapollo'},
  {wave:4,  key:'fivalyrie'},
  {wave:10, key:'boathena'},
  {wave:13, key:'bomedusa'},
  {wave:15, key:'fiherc'},
  {wave:17, key:'fiulysses'},
  {wave:24, key:'boursa'}
];
function fs1ShipsUpTo(w){
  const out=[];
  for(const s of FS1_SHIPS) if(w>=s.wave && SPR_DATA[s.key]) out.push(s.key);
  return out;
}

// Memory between waves. The original leans on it constantly: the Vasudan
// ace only turns up if the Orff came through, and First Strike has no
// subject at all if the Taranis was destroyed the wave before. Reset when
// a run starts, never mid-campaign.
let CAMP = {};
function campReset(){ CAMP = {orffOk:true, taranisAlive:true, cargoLost:0}; }

// A freighter that reaches the edge got away. The briefing for Small
// Deadly Space is explicit that this is a defeat - they bring back
// reinforcements - so it costs points, like a lost escort does.
const RUNNER_PENALTY = 200;

// Ein Laeufer soll gejagt und nicht abgeschossen werden. Aus der Laenge
// allein waere die Bast 169 Rumpf, also 1,1 s Spielerfeuer. Mit 2.5 sind
// es 423 und damit die 2,7 s, die der Endlosmodus seit je hat - und die
// Laengenunterschiede schlagen trotzdem durch:
//   Isis 27 m -> 325 (2,1 s) . Elysium 32 m -> 370 (2,4 s)
//   Bast 38 m -> 423 (2,7 s) . Maat 56 m -> 570 (3,6 s)
// Gerechnet gegen 44 Schaden je 28 Schritte, also 157 je Sekunde bei
// voller Trefferquote; auf ein fliehendes Ziel sitzt nicht jede Salve.
const RUNNER_HP_MUL = 2.5;

// mod:null statt MOD_NONE. Diese Tabelle wird beim Laden ausgewertet und
// steht weit vor der Deklaration von MOD_NONE; ein Zugriff darauf bricht
// das ganze Skript ab, noch bevor etwas gezeichnet wird. buildFS1Wave()
// setzt den Vorgabewert spaeter mit plan.mod || MOD_NONE.
const FS1_PLAN = [
  {n:1, name:'EVE OF DESTRUCTION', fac:'vasudan', mod:null,
   guard:{type:'cr_ntf', spr:'crfenris', fac:'terran', hp:1.0, still:true},
   wings:[['fianubis',2,0.40],['fianubis',2,0.30],['fianubis',3,0.35],
          ['fianubis',3,0.50],['fianubis',3,0]], noShield:true},

  {n:2, name:'THE FIELD OF BATTLE', fac:'vasudan', mod:'astfield',
   wings:[['fianubis',3,0],['fianubis',3,0],['fianubis',3,0],
          ['fianubis',3,0]], ace:'fiseth', noShield:true},

  {n:3, name:'SMALL DEADLY SPACE', fac:'vasudan', mod:null,
   wings:[['fianubis',3,0],['fianubis',2,0],['fianubis',3,0]],
   runners:[['frbast',2]], protect:[['fcvc3',3]], noShield:true},

  {n:4, name:'AVENGING ANGELS', fac:'vasudan', mod:null,
   wings:[['fiapollo',2,0,'renegade'],['fiapollo',2,0,'renegade'],
          ['fihorus',2,0],['boosiris',1,0],['fianubis',3,0]],
   runners:[['trisis',1],['trelysium',1]], noShield:true},

  {n:5, name:'OUT OF THE DARK, INTO THE NIGHT', fac:'vasudan', mod:null,
   feud:true,
   wings:[['fianubis',3,0],['fianubis',3,0],['boamun',2,0],
          ['fibasilisk',4,0,'shivan']],
   cap:{type:'cr_ntf', spr:'craten', fac:'vasudan'},
   protect:[['scfaustus',1]], noShield:true},

  {n:6, name:'PAVING THE WAY', fac:'shivan', mod:'astfield',
   guard:{type:'cr_ntf', spr:'deorionleft', fac:'terran', hp:1.0, still:true},
   wings:[['boshaitan',2,0,'shivan']], noShield:true},

  {n:7, name:"PANDORA'S BOX", fac:'shivan', mod:'ambush',
   wings:[['fibasilisk',1,0,'shivan'],['fibasilisk',3,0,'shivan'],
          ['fibasilisk',3,0,'shivan']],
   sentries:[['sgtrident',6]], scans:[['fcsc5',4]], noShield:true},

  {n:8, name:'THE HAMMER AND THE ANVIL', fac:'shivan', mod:null,
   wings:[['fibasilisk',2,0,'shivan'],['fibasilisk',4,0,'shivan'],
          ['fiscorpion',3,0,'shivan']],
   turncoats:[['fianubis',3],['fiseth',2]],
   protect:[['frposeidon',3]], noShield:true},

  {n:9, name:'THE DARKNESS AND THE LIGHT', fac:'vasudan', mod:null,
   wings:[['fiseth',3,0],['fiseth',3,0]],
   runners:[['frmaat',2]], scans:[['fcvc3',3]],
   cap:{type:'cr_ntf', spr:'crcain', fac:'shivan', leave:true}},

  {n:10, name:'FIRST STRIKE', fac:'shivan', mod:null,
   wings:[['fibasilisk',3,0,'shivan'],['fibasilisk',4,0,'shivan'],
          ['fiscorpion',2,0,'shivan']],
   cap:{type:'cr_ntf', spr:'crcain', fac:'shivan', disable:true, hp:1.6},
   protect:[['frchronos',1]]}
];

function buildFS1Wave(n){
  const plan = FS1_PLAN[(n-1) % FS1_PLAN.length];
  currentEra = 'fs1';
  currentFaction = plan.fac==='shivan' ? 'shivan' : 'ntf';
  waveLive = 10;
  fleeTotal = 0; fleeEscaped = 0;
  guardWanted = false; guardSpawned = false; guardLost = false;
  guardClass = 'cruiser'; guardFrac = GUARD_HULL_FRAC; guardReward = 'cruiser';
  astAim = (plan.mod==='astfield'); transitSecs = 0; guardGone = false;
  astStreamCd = AST_STREAM_MEAN;
  empOut = 0; empWarn = 0; empNext = 0;
  BOMB_PORTALS = []; bombRaidLeft = 0; bombRaidCd = 99999;
  reinfAt = 0; reinfDone = true;
  gateWings = true; gateWing = 0;
  disableTarget = null;
  waveMod = plan.mod || MOD_NONE;
  waveFeud = !!plan.feud;
  // Der Titel stand bisher nur im Plan und wurde nirgends angezeigt.
  waveTitle = 'WAVE '+n+'   '+plan.name;
  titleT = TITLE_TIME;

  const q = [];
  let t = 60;

  // Everything that is simply standing there when the wave opens: cargo to
  // be protected or scanned, gun platforms guarding a depot.
  for(const [spr,cnt] of (plan.protect||[]))
    for(let k=0;k<cnt;k++)
      q.push({time:1, type:'protect', spr:spr, fac:'terran', noWarp:1,
              x:W*(0.28+0.10*k), y:H*(0.34+0.16*k)});
  for(const [spr,cnt] of (plan.scans||[]))
    for(let k=0;k<cnt;k++)
      q.push({time:1, type:'container', spr:spr, fac:plan.fac, scan:1,
              noWarp:1, x:W*(0.58+0.09*k), y:H*(0.40+0.16*k)});
  for(const [spr,cnt] of (plan.sentries||[]))
    for(let k=0;k<cnt;k++)
      q.push({time:1, type:'sentry', spr:spr, fac:plan.fac, noWarp:1,
              x:W*(0.80+0.06*(k%2)), y:H*(0.18+0.13*k)});

  // Freighters and transports crossing the field. Catching them before the
  // edge is the job; the ones that get through cost points.
  for(const [spr,cnt] of (plan.runners||[]))
    for(let k=0;k<cnt;k++){
      q.push({time:t, type:'freighter', spr:spr, fac:plan.fac, runner:1,
              hpMul:RUNNER_HP_MUL, y:H*(0.30+0.22*k)});
      fleeTotal++;
    }

  if(plan.guard)
    q.push({time:20, type:plan.guard.type, spr:plan.guard.spr,
            fac:plan.guard.fac, guard:1, still:plan.guard.still?1:0,
            noWarp:1, x:W*0.30, y:H*0.5});

  if(plan.cap)
    q.push({time:260, type:plan.cap.type, spr:plan.cap.spr, fac:plan.cap.fac,
            disable:plan.cap.disable?1:0, hpMul:plan.cap.hp||0,
            y:H*0.5});

  for(const w of (plan.wings||[])){
    const [spr,cnt,hp,fac] = w;
    const wid = ++wingSeq;
    const mid = HUD_H+80+Math.random()*(H-HUD_H-160);
    const half = (cnt-1)*WING_SPACING*0.5;
    for(let k=0;k<cnt;k++)
      q.push({time:t+k*WING_STAGGER, type:'fi_ntf', spr:spr, wing:wid,
              fac:fac||plan.fac, hpMul:hp||0,
              noShield:(plan.noShield && (fac||plan.fac)!=='shivan')?1:0,
              y:mid-half+k*WING_SPACING});
    t += 140;
  }

  // The ace only appears if the Orff came through the wave before. That
  // condition is in the original and it is the reason the campaign needs a
  // memory at all.
  if(plan.ace && CAMP.orffOk)
    q.push({time:t+120, type:'fi_ntf', spr:plan.ace, wing:++wingSeq,
            fac:plan.fac, noShield:1, y:H*0.5});

  // Ships that arrive as an escort and turn. The Hammer of Light joining
  // the convoy and then opening fire is the first of them.
  for(const [spr,cnt] of (plan.turncoats||[]))
    for(let k=0;k<cnt;k++)
      q.push({time:t+200+k*WING_STAGGER, type:'defector', spr:spr,
              y:H*(0.35+0.12*k)});

  return q.sort(function(a,b){ return a.time-b.time; });
}

// ── DEATH ────────────────────────────────────────────────────
// One place where an enemy dies. There were two, and they had already
// drifted apart: the primary bolt path dropped pickups, the secondary path
// did not. Adding the crossfire between hostile factions would have made a
// third copy, so they are folded together here first.
//   award  the player gets the points. False when one enemy kills another.
//   drop   pickups fall. Only from a kill the player earned.
function killEnemy(e, idx, award, drop){
  if(!e || e.dead) return;
  e.dead = true;
  if(e.pickup) cargoLost(e);
  if(award) score += e.pts;
  statKill(e.type);
  if(drop) maybeDropTicket(e);
  triggerExpl(e.x, e.y, e.type, e.faction||'ntf', e);
  if(e.type==='boss'){ bossAlive=false; bossSlain=true; }
  const k = (idx!=null && enemies[idx]===e) ? idx : enemies.indexOf(e);
  if(k>=0) enemies.splice(k,1);
}

// ── WING GATING ──────────────────────────────────────────────
// FreeSpace sends the next wing once the previous one is gone. Everything
// here is the bookkeeping for that; the decision itself sits in the queue
// loop in update().
let gateWings = true;      // false on a crossing, there is no clear field
let gateWing  = 0;         // id of the wing currently allowed out
const GATE_RETRY = 30;     // steps before asking again, a third of a second

// Scenery does not count as work. Without this a standing asteroid field
// would hold the wave open forever, because the end condition asks for an
// empty enemies[] and rocks that do not drift never leave it.
function liveThreatCount(){
  let n=0;
  for(const e of enemies) if(!e.scenery && !e.dead && e.rollT==null) n++;
  return n;
}

// ── DISABLE INSTEAD OF DESTROY ───────────────────────────────
// First Strike asks for a cruiser to be left alive and useless rather than
// destroyed. That needs no new mechanic, only a different question at the
// end of the wave. Subsystems have been in since v40.
let disableTarget = null;
function disableDone(){
  const t = disableTarget;
  if(!t || t.dead) return true;              // destroyed also ends it
  return !subOK(t,'weapons') && !subOK(t,'engines');
}

// ── SCANNING ─────────────────────────────────────────────────
// Proximity plus dwell. No new control: fly close, stay there, a ring
// fills. Taking a hit stops the fill, which is what makes a quiet wave
// tense instead of slow. player.shDelay is set to 90 on any hit and is
// therefore the signal that already exists for "under fire right now".
const SCAN_R    = 110;     // px, a little over two ship lengths
const SCAN_TIME = 210;     // steps at 100 Hz, so 2.1 s of undisturbed dwell
const SCAN_DECAY = 2;      // lost per step when out of range or under fire
// Set by a mission (scanUnderFire) whose targets sit inside an escort's
// fire all the time: there a hit does not stop the fill, only leaving
// the range does. Cleared at every wave start.
let scanUnderFire = false;
function tickScan(){
  if(GS!=='playing') return;
  for(const e of enemies){
    if(!e.scan || e.scanned || e.dead) continue;
    const d = Math.hypot(player.x-e.x, player.y-e.y);
    if(d<=SCAN_R && (scanUnderFire || player.shDelay<=0)){
      e.scanT = (e.scanT||0)+1;
      if(e.scanT>=SCAN_TIME){
        e.scanned = true;
        score += 200;
        if(STATS.scans==null) STATS.scans=0;
        STATS.scans++;
        SUB_MSGS.push({x:e.x, y:e.y, txt:'SCAN COMPLETE',
                       life:200, ml:200, ally:true});
      }
    } else if(e.scanT>0){
      e.scanT = Math.max(0, e.scanT-SCAN_DECAY);
    }
  }
}
// The ring sits at the object, not at the player, so it reads as a
// property of the thing being scanned. Same visual language as the hold
// ring around the player: a soft arc that fills clockwise from the top.
// ── SUBSYSTEM SCAN ───────────────────────────────────────────
// A ship that is read system by system: hold within SUB_SCAN_R of one of
// its subsystems, undisturbed, until its ring fills. The nearest one in
// reach is the one being read. When all five are done, so is the ship.
const SUB_SCAN_R = 60, SUB_SCAN_TIME = 150;
function tickSubScan(){
  if(GS!=='playing') return;
  for(const e of enemies){
    if(!e.scanSubs || e.scanned || e.dead || e.warp>0) continue;
    let best = null, bd = SUB_SCAN_R;
    for(const s of e.subs){
      if(s.scanned) continue;
      const p = subPos(e, s), d = Math.hypot(player.x-p.x, player.y-p.y);
      if(d <= bd){ bd = d; best = s; }
    }
    for(const s of e.subs){
      if(s.scanned) continue;
      if(s===best && player.shDelay<=0) s.scanT++;
      else if(s.scanT>0) s.scanT = Math.max(0, s.scanT-SCAN_DECAY);
      if(s.scanT >= SUB_SCAN_TIME){
        s.scanned = true; score += 100;
        const p = subPos(e, s);
        SUB_MSGS.push({x:p.x, y:p.y-18, txt:s.label+' SCANNED', life:170, ml:170,
                       ally:true, tone:'good'});
      }
    }
    if(e.subs.every(function(s){ return s.scanned; })){
      e.scanned = true; score += 500;
      if(STATS.scans==null) STATS.scans = 0;
      STATS.scans++;
    }
  }
}
function drawSubScan(e){
  const pulse = 0.5 + 0.5*Math.sin(fc*0.10);
  for(const s of e.subs){
    const p = subPos(e, s);
    ctx.save();
    ctx.translate(p.x|0, p.y|0);
    ctx.lineWidth = 1.5;
    if(s.scanned){
      ctx.strokeStyle = 'rgba(77,255,136,0.85)';
      ctx.beginPath(); ctx.arc(0, 0, 11, 0, Math.PI*2); ctx.stroke();
    } else {
      ctx.strokeStyle = 'rgba(127,214,255,'+(0.35+0.35*pulse).toFixed(2)+')';
      ctx.setLineDash([3,3]);
      ctx.beginPath(); ctx.arc(0, 0, 12, 0, Math.PI*2); ctx.stroke();
      ctx.setLineDash([]);
      const t = Math.min(1, (s.scanT||0)/SUB_SCAN_TIME);
      if(t>0){
        ctx.strokeStyle = '#7fd6ff'; ctx.lineWidth = 2.5;
        ctx.beginPath(); ctx.arc(0, 0, 12, -Math.PI/2, -Math.PI/2 + t*Math.PI*2); ctx.stroke();
      }
    }
    ctx.restore();
  }
}
function drawScanRing(e){
  if(e.scanSubs && !e.scanned){ drawSubScan(e); return; }
  if(!e.scan) return;
  const img = IMGS[e.img];
  const r = (img ? Math.max(img.width,img.height)*e.sc*0.62 : 24) + 8;
  ctx.save();
  ctx.translate(e.x|0, e.y|0);
  if(e.scanned){
    ctx.strokeStyle='rgba(90,255,170,0.55)'; ctx.lineWidth=2;
    ctx.beginPath(); ctx.arc(0,0,r,0,Math.PI*2); ctx.stroke();
  } else {
    const t = Math.min(1, (e.scanT||0)/SCAN_TIME);
    ctx.strokeStyle='rgba(110,216,255,0.20)'; ctx.lineWidth=2;
    ctx.beginPath(); ctx.arc(0,0,r,0,Math.PI*2); ctx.stroke();
    if(t>0){
      ctx.strokeStyle='rgba(110,216,255,0.95)'; ctx.lineWidth=3;
      ctx.beginPath();
      ctx.arc(0,0,r,-Math.PI/2,-Math.PI/2+Math.PI*2*t);
      ctx.stroke();
    }
  }
  ctx.restore();
}

// ── DEFECTORS ────────────────────────────────────────────────
// Allies are not protected by a side test. They are protected by living in
// allies[], and the player's bullet loop only ever looks at enemies[]. A
// ship that changes sides therefore has to be handed from one array to the
// other; a flag would change nothing, because nobody would look.
//
// What has to travel with it:
//   pts      mkAllySmall() does not set it. Without it score += e.pts on
//            the kill makes the score NaN for the rest of the run.
//   side     smallFire() reads it every shot, so the bullets swap to the
//            enemy list on their own once it is gone.
//   faction  triggerExpl() takes e.faction||'ntf' for the debris colour,
//            and 'terran' is not one it knows.
// The hand over runs backwards through the array, so the splice cannot
// skip an entry.
// A non-combatant on the friendly side. It sits where it is put and does
// nothing; the point is that it has to survive. guard:true hands it to the
// existing bookkeeping, which already fires GUARD_PENALTY on its death.
// Welcher Typzweig einen Schuetzling traegt. Frachtcontainer bleiben
// Container, alles andere laeuft ueber den Frachterzweig - der Rumpf kommt
// ohnehin aus der Laenge, es geht hier nur um das Verhalten.
function protectType(spr){
  const c = hullClass(spr);
  // Container und Rettungskapseln sind wehrlos und duenn. Ein Frachter
  // haelt etwas aus, eine Kapsel nicht - das ist der Punkt.
  return (c==='fc' || c==='ep') ? 'container' : 'freighter';
}
function spawnProtected(sp){
  const a = mkEnemy(sp.type==='protect' ? protectType(sp.spr) : sp.type, sp.spr, sp.y);
  if(!a) return;
  a.side = 'ally';
  a.uid = sp.uid;
  if(sp.uid) EV_SEEN[sp.uid] = true;
  a.faction = sp.fac || 'terran';
  if(sp.pickup) a.pickup = true;
  a.guard = true;
  a.small = false;
  a.vx = 0; a.vy = 0;
  a.minY = a.y; a.maxY = a.y;      // updateAllies() nudges vy, so pin it
  // Ein Andockauftrag wird hier gesetzt: applySpawnOpts laeuft fuer
  // Schuetzlinge nicht, weil sie ueber diesen Weg entstehen.
  if(sp.dockTo){
    a.dockTo = sp.dockTo;
    // dockHold: seconds she stays docked before the dock counts, and
    // then jumps out instead of flying on.
    if(sp.dockHold) a.dockHold = Math.round(sp.dockHold*TICK_HZ);
    a.crossAfter = sp.cross || 0.38;
    // Die Hoehe darf nicht gepinnt sein, sonst kommt er nie zum
    // Andockpunkt hoch.
    a.minY = HUD_H+20; a.maxY = H-20;
  }
  if(sp.still){ a.vy = 0; a.minY = a.y; a.maxY = a.y; }
  a.warp = 0; a.warpMax = 1;
  a.flip = needsFlip(a.img, false);
  if(sp.x != null) a.x = sp.x;
  if(sp.cross && !sp.dockTo){
    a.crossing = sp.cross;         // Bildpunkte je Schritt
    // Below zero she flies out to the left and faces that way.
    a.flip = needsFlip(a.img, sp.cross < 0);
    if(sp.x == null) a.x = (sp.cross < 0) ? W+40 : -40;
  }
  allies.push(a);
}

function spawnDefector(y, spr){
  const a = mkAllySmall('fighter', 'terran', spr || 'fiapollo', y);
  a.warp = 60; a.warpMax = 60;
  a.defectAt = 420;          // 4.2 s flying as an escort before it turns
  allies.push(a);
}
function defect(a){
  if(!a.small) return defectCap(a);
  const _i = allies.indexOf(a);
  if(_i >= 0) allies.splice(_i, 1);    // sonst steht es in beiden Listen
  a.side = 'enemy';
  a.defectLock = false;      // gewechselt, ab jetzt normal zu toeten
  a.faction = (currentFaction==='hol') ? 'hol' : 'renegade';
  a.pts = (a.type==='bomber') ? 150 : 100;
  a.defectAt = 0;
  a.small = true;
  enemies.push(a);
  SUB_MSGS.push({x:a.x, y:a.y, txt:'TURNING HOSTILE',
                 life:200, ml:200, ally:false});
}
// A capital ship going over. The allied object is built for the allied
// paths and the enemy paths expect other fields, so rather than convert
// it, it is rebuilt as an enemy of the same class exactly the way the
// spawn queue builds one. It keeps its place, its share of hull and its
// mission id, and in the NTF cycle it flies on as the NTF variant.
const DEFECT_MIN_HULL = 0.6;
function defectCap(a){
  const spr = (currentFaction==='ntf' && NTF_HULL[a.img]) || a.img;
  const e = mkEnemy(hullClass(spr) + '_' + FAC_TAG[currentFaction], spr, a.y);
  if(!e) return;
  const _i = allies.indexOf(a);
  if(_i >= 0) allies.splice(_i, 1);
  e.side = 'enemy';
  e.x = a.x; e.y = a.y; e.warpX = a.x; e.warpY = a.y;
  e.warp = 0; e.warpMax = 1;
  e.flip = needsFlip(e.img, true);
  // No assignStation(): that picks a free lane for a ship that arrives,
  // and a ship that changes sides keeps the place she is in.
  initWeapons(e); initSecAmmo(e); initLuciShield(e); initSubsystems(e);
  e.hp = Math.max(1, Math.round(e.maxHp * (a.maxHp ? a.hp/a.maxHp : 1)));
  e.uid = a.uid;
  // She turns with at least DEFECT_MIN_HULL of her hull. Held at the
  // lock's floor until the turn, she would otherwise go over as a wreck
  // that the allied wings finish before the player gets a shot in.
  e.hp = Math.max(e.hp, Math.round(e.maxHp*DEFECT_MIN_HULL));
  // defectRun: after the turn she makes for the right edge, facing where
  // she goes, and jumps out the moment she gets there. The same course
  // as any escaper, so killing her engines stops her.
  if(a.defectRun){
    e.escaping = a.defectRun;
    e.escWarp = true;
    e.noFlee = true;
    const _ri = IMGS[e.img];
    e.targetX = W + (_ri ? _ri.width*e.sc : 120)*2;
    e.vx = 0;
    e.flip = needsFlip(e.img, false);
    escTotal++;
  }
  enemies.push(e);
  SUB_MSGS.push({x:e.x, y:e.y, txt:'TURNING HOSTILE',
                 life:200, ml:200, ally:false});
}
// Waagerechte Fahrt eines Schuetzlings. Verlaesst er rechts das Feld, ist
// er durchgebracht: er wird still entfernt, ohne guardLost zu setzen -
// sonst zaehlte der Erfolg als Verlust.
let crossDone = 0, crossTotal = 0;
// Ist noch ein Schuetzling unterwegs? Abgeschossene stehen nicht mehr in
// allies, die Welle haengt also nicht, wenn einer verloren geht.
// Steht noch ein Ereignis aus, das Schiffe ins Feld bringt oder die Seite
// wechselt? Dann ist die Welle nicht vorbei, auch wenn gerade nichts lebt.
function evPending(){
  for(const e of EV){
    if(e.done) continue;
    // Nachschub abzuschalten haelt keine Welle offen.
    if(e.w!=='einwarpen' && e.w!=='seite') continue;
    // Ein Ausloeser, dessen Ziel nie im Feld war oder schon weg ist, kann
    // nicht mehr feuern. Sonst haengt die Welle fuer immer.
    if(['zerstoert','vernichtet','alleZerstoert','verlaesst','anzahlUnter','rumpfUnter','subsystem'].indexOf(e.t)>=0){
      // Gone does not mean it cannot fire: 'alleZerstoert' fires exactly
      // then. Only a trigger that is not true now can never be again.
      // Checked before the event tick, the wave could end in the very
      // step the last ship died, and the next one never came.
      if(evIds(e.a).every(function(id){ return evSeen(id) && byId(id).length===0; })
         && !evTrig(e)) continue;
    }
    // Ein Andockauftrag, dessen Ziel nicht mehr existiert, kann nicht
    // mehr feuern. Sonst laeuft die Welle endlos weiter.
    if(e.t==='angedockt'){
      const dk = byId(e.a)[0];
      if(!dk) { if(evSeen(e.a)) continue; }
      else if(dk.dockTo && byId(dk.dockTo).length===0 && evSeen(dk.dockTo)) continue;
    }
    return true;
  }
  return false;
}
// Ist noch ein Fluechtling unterwegs? Dann laeuft die Welle, auch wenn
// sonst nichts mehr im Feld steht.
function escPending(){
  for(const e of enemies) if(e.escaping && !e.dead) return true;
  return false;
}
function crossPending(){
  for(const a of allies) if(a.crossing && !a.dead) return true;
  return false;
}
// Gegner mit Fluchtkurs nach rechts. Erreichen sie den Rand, sind sie weg.
let escTotal = 0, escGone = 0;
// Sekundaerexplosionen auf einem sterbenden Grosskampfschiff. Es steht
// noch, es schiesst nicht mehr, und es reisst Stueck fuer Stueck auf.
// Grosskampfschiff auf Rammkurs. Es sucht sich das naechste verbuendete
// Grosskampfschiff, faehrt darauf zu und schlaegt ein.
// Weltkoordinaten des ersten Andockpunkts eines Schiffs.
function dockPoint(o){
  const m = mountsFor(o.img), img = IMGS[o.img];
  if(!m || !m.docks || !m.docks.length || !img) return {x:o.x, y:o.y};
  const d = m.docks[0];
  const s = o.flip ? -1 : 1;
  return {x:o.x + (img.width*o.sc*0.5)*d.dx*s,
          y:o.y + (img.height*o.sc*0.5)*d.dy};
}
// Offset of a ship's first dock point from its centre.
function dockOffset(o){
  const p = dockPoint(o);
  return {x:p.x-o.x, y:p.y-o.y};
}
// Still in one of the two lists and not dead.
function unitAlive(o){
  return !!o && !o.dead && (allies.indexOf(o)>=0 || enemies.indexOf(o)>=0);
}
// Are ships of this id still on their way into the field?
function idPending(id){
  for(const q of spawnQ) if(q.uid===id) return true;
  return !!(EV_HELD[id] && EV_HELD[id].length);
}
// Counts one cargo run as lost, once. Every path that loses cargo goes
// through here, so a container can never be counted twice.
function cargoLost(c){
  if(!c || c.lostCounted) return;
  c.lostCounted = true;
  protLost++; guardLost = true;
}
// One container per freighter. Nearest free one of the id, where free means
// alive, not carried, not left behind and not promised to a living freighter.
// byId() alone always answered with the first ship, which is how two
// freighters ended up fighting over one container.
function claimCargo(e){
  let best = null, bd = 1e18;
  for(const c of byId(e.dockTo)){
    if(c.type!=='container' || c.carried || c.stranded) continue;
    if(c.resBy && c.resBy!==e && unitAlive(c.resBy)) continue;
    const d = (c.x-e.x)*(c.x-e.x) + (c.y-e.y)*(c.y-e.y);
    if(d < bd){ bd = d; best = c; }
  }
  if(best){ best.resBy = e; e.dockRes = best; }
  return best;
}
// Decided: a freighter whose container is gone leaves empty. It does not
// look for another one, and it does not count as a delivery.
function leaveEmpty(e, wasCargo){
  if(e.dockRes && e.dockRes.resBy===e) e.dockRes.resBy = null;
  e.dockRes = null; e.dockTo = null;
  // An enemy transport whose ship is gone has nothing left to do here.
  if(e.side!=='ally' && e.dockHold && !(e.warpOut>0)){
    e.warpOut = e.warpMax = 120; e.warpX = e.x; e.warpY = e.y;
    if(e.uid) EV_LEFT[e.uid] = true;
  }
  if(wasCargo){
    e.emptyRun = true;
    SUB_MSGS.push({x:e.x, y:e.y-28, txt:'NO CARGO', life:150, ml:150,
                   ally:false, tone:'bad'});
  }
  if(e.crossAfter) e.crossing = e.crossAfter;
}
// Is anybody still able to come for this container? A living freighter
// heading for its id without a claim on another one, or one still queued
// or held back for an event.
function cargoStillWanted(c){
  for(const o of enemies.concat(allies))
    if(!o.dead && o.dockTo===c.uid && (!o.dockRes || o.dockRes===c)) return true;
  for(const q of spawnQ) if(q.dockTo===c.uid) return true;
  for(const k in EV_HELD) for(const q of EV_HELD[k]) if(q.dockTo===c.uid) return true;
  return false;
}
// Moves carried cargo so that both dock points meet. Runs after all
// movement in the step, otherwise the cargo trails one step behind.
function carryCargo(e){
  const c = e.dockedTo;
  if(!c) return;
  if(!unitAlive(c)){
    // Shot off the carrier on the way: he arrives with nothing.
    e.dockedTo = null; e.hasCargo = false; e.emptyRun = true;
    cargoLost(c);
    return;
  }
  const p = dockPoint(e), o = dockOffset(c);
  c.x = p.x - o.x; c.y = p.y - o.y;
  c.vx = 0; c.vy = 0; c.warpX = c.x; c.warpY = c.y;
}
// Decided: cargo dies with its carrier. The carrier was already counted
// as lost, the cargo is not counted a second time.
function dropCargo(c){
  if(!c || c.dead) return;
  c.lostCounted = true;
  c.dead = true; c.hp = 0;
  triggerExpl(c.x, c.y, 'container', c.faction || 'vasudan', c);
  let k = allies.indexOf(c);  if(k>=0) allies.splice(k,1);
  k = enemies.indexOf(c);     if(k>=0) enemies.splice(k,1);
}
function tickCarry(){
  for(const e of enemies.concat(allies)) if(e.dockedTo) carryCargo(e);
  for(const c of enemies.concat(allies))
    if(c.carrier && !c.dead && !unitAlive(c.carrier)) dropCargo(c);
}
function tickDocking(){
  const all = enemies.concat(allies);
  // Containers nobody can come for any more. This runs before the wave end
  // test, so an abandoned container never holds the wave open.
  for(const c of all){
    if(!c.pickup || c.carried || c.stranded || c.dead || c.warp>0) continue;
    if(cargoStillWanted(c)) continue;
    c.stranded = true; c.scenery = true; c.guard = false;
    // A freighter that died on its way here was already counted as lost.
    if(c.resBy && c.resBy.dead) c.lostCounted = true;
    else cargoLost(c);
    c.resBy = null;
    SUB_MSGS.push({x:c.x, y:c.y-24, txt:'CARGO LEFT BEHIND', life:170, ml:170,
                   ally:false, tone:'bad'});
  }
  for(const e of all){
    if(!e.dockTo || e.dead || e.warp>0) continue;
    const group = byId(e.dockTo);
    let t = group[0];
    if(t && t.type==='container') e.wantsCargo = true;
    if(!t || t.type==='container'){
      if(e.dockRes){
        // Decided: his container is gone, he does not look for another.
        if(!unitAlive(e.dockRes) || e.dockRes.carried || e.dockRes.stranded){
          leaveEmpty(e, true); continue; }
        t = e.dockRes;
      } else if(t){
        t = claimCargo(e);
      }
      if(!t){
        // Containers of this id may still be arriving - then wait.
        if(idPending(e.dockTo) || !evSeen(e.dockTo)) continue;
        leaveEmpty(e, !!e.wantsCargo);
        continue;
      }
    }
    // Head for the spot where his dock point meets the target's.
    const p = dockPoint(t), o = dockOffset(e);
    const dx = (p.x-o.x) - e.x, dy = (p.y-o.y) - e.y;
    const L = Math.hypot(dx, dy);
    e.vx = 0; e.vy = 0;
    // The field clamp can keep him off the exact spot. If he stops getting
    // closer while near enough, he docks where he is.
    if(e.dockBest==null || L < e.dockBest-0.05){ e.dockBest = L; e.dockStall = 0; }
    else e.dockStall = (e.dockStall||0) + 1;
    if(!(L <= 1 || (L <= DOCK_NEAR && e.dockStall > 60))){
      const sx = DOCK_SPD*1.6, sy = DOCK_SPD;
      e.x += Math.max(-sx, Math.min(sx, dx));
      e.y += Math.max(-sy, Math.min(sy, dy));
      continue;
    }
    // Boarding: she stays on the spot for dockHold steps before the
    // dock counts. Lost in that time, nothing was taken.
    if(e.dockHold>0){
      if(e.holdT==null){
        e.holdT = e.dockHold;
        SUB_MSGS.push({x:e.x, y:e.y-28, txt:'BOARDING', life:e.dockHold, ml:e.dockHold,
                       ally:true, tone:'good'});
      }
      if(--e.holdT > 0) continue;
    }
    // Docked.
    EV_DOCK[e.uid] = true;
    if(!e.dockHold)
      SUB_MSGS.push({x:e.x, y:e.y-28, txt:'DOCKED', life:150, ml:150,
                     ally:true, tone:'good'});
    if(t.type==='container'){
      e.dockedTo = t; t.carrier = e; t.resBy = e;
      t.carried = true; t.guard = false; t.scenery = true;
      e.hasCargo = true;
      carryCargo(e);
    }
    e.dockTo = null; e.dockRes = null;
    // A boarding party leaves with its prize: a jump, not a drive on.
    if(e.dockHold){
      e.warpOut = e.warpMax = 160; e.warpX = e.x; e.warpY = e.y;
      // Left, not lost: 'vernichtet' must not read the jump as a kill.
      if(e.uid) EV_LEFT[e.uid] = true;
      if(e.side==='ally') protSaved++;
      continue;
    }
    // Load first, then leave.
    if(e.crossAfter) e.crossing = e.crossAfter;
  }
}
function tickCapRam(){
  for(let i=enemies.length-1;i>=0;i--){
    const e = enemies[i];
    if(!e.capRam || e.dead || e.warp>0 || e.rollT!=null) continue;
    let t=null, bd=1e9;
    for(const a of allies){
      if(a.dead || a.small) continue;
      const d=(a.x-e.x)*(a.x-e.x)+(a.y-e.y)*(a.y-e.y);
      if(d<bd){ bd=d; t=a; }
    }
    // Ziel weg, waehrend er anflog: ohne Kurs und ohne Fluchterlaubnis
    // haengt er sonst bis zum Wellenende am Rand. Er gibt den Rammkurs auf
    // und verhaelt sich wieder wie ein gewoehnlicher Gegner.
    if(!t){ e.capRam = 0; e.noFlee = false; continue; }
    // Direkter Kurs, ohne Halteposition - er will nicht schiessen.
    e.targetX = null;
    const dx=t.x-e.x, dy=t.y-e.y, L=Math.hypot(dx,dy)||1;
    // capRam ist die Fahrt selbst, nicht mehr ein Anstupser auf die Fahrt
    // eines anderen: tickEnemies() laesst einen Rammkurs jetzt in Ruhe.
    e.x += dx/L*e.capRam;
    // Nie weiter als der Rest, sonst schwingt er ueber die Hoehe hinaus und
    // pendelt daran vorbei.
    const vy = dy/L*e.capRam*CAP_RAM_CLIMB;
    e.y += (Math.abs(vy) > Math.abs(dy)) ? dy : vy;
    if(hullsBite(e, t, CAP_RAM_BITE)){
      t.hp -= Math.max(1, Math.round((t.maxHp||100)*RAM_PCT_CAPITAL));
      hullHit(e.x, e.y);
      triggerExpl(e.x, e.y, 'destroyer', e.faction, e);
      spawnShock(e.x, e.y, 170, 3.0, 0.024);
      SUB_MSGS.push({x:e.x, y:e.y-40, txt:'IMPACT', life:150, ml:150, ally:false});
      e.dead = true; e.hp = 0;
      enemies.splice(i,1);
    }
  }
}
function tickDeathRoll(){
  for(let i=enemies.length-1;i>=0;i--){
    const e = enemies[i];
    if(e.rollT==null) continue;
    e.rollT--;
    if(e.rollT % DEATH_ROLL_GAP === 0){
      const img = IMGS[e.img];
      const hw = img ? img.width*e.sc*0.42 : 40;
      const hh = img ? img.height*e.sc*0.34 : 16;
      const px = e.x + (Math.random()*2-1)*hw;
      const py = e.y + (Math.random()*2-1)*hh;
      triggerExpl(px, py, 'cruiser', e.faction, null);
      addShake(2, 8);
    }
    if(e.rollT <= 0){
      e.rollT = null;
      e.hp = 0;
      spawnShock(e.x, e.y, 150, 2.6, 0.020);
      // Ueber killEnemy, nicht daneben: dort haengen Punkte, Statistik,
      // Ticketwurf und die Bossmarkierung.
      killEnemy(e, i, true, true);
    }
  }
}
function tickEscapers(){
  for(let i=enemies.length-1;i>=0;i--){
    const e = enemies[i];
    if(!e.escaping || e.dead || e.warp>0) continue;
    // Kein Antrieb, keine Fahrt. Das war der Sinn des Subsystems.
    if(hasSubsystems(e) && !subOK(e,'engines')) continue;
    e.x += e.escaping;
    // Erst weg, wenn der Rumpf ganz draussen ist - nicht wenn die Mitte
    // den Rand erreicht und das Heck noch im Bild steht.
    const _ei = IMGS[e.img];
    const _ew = _ei ? _ei.width*e.sc : 120;
    if(e.escWarp && e.x + _ew*0.5 >= W - TRANS_EDGE_PAD){
      e.escaping = 0;
      escGone++;
      EV_LEFT[e.uid] = true;
      e.warpOut = e.warpMax > 1 ? e.warpMax : 160;
      e.warpX = e.x; e.warpY = e.y;
      SUB_MSGS.push({x:W-110, y:e.y, txt:'TARGET ESCAPED', life:170, ml:170,
                     ally:false, tone:'bad'});
      continue;
    }
    // Ganz draussen heisst: die linke Kante hat den rechten Rand passiert.
    if(e.x - _ew*0.5 > W + 8){
      escGone++;
      EV_LEFT[e.uid] = true;
      score = Math.max(0, score - Math.round((e.pts||200)*ESCAPE_PENALTY));
      SUB_MSGS.push({x:W-110, y:e.y, txt:'TARGET ESCAPED', life:170, ml:170,
                     ally:false, tone:'bad'});
      enemies.splice(i,1);
    }
  }
}
function tickCrossGuards(){
  for(const a of allies.slice()){
    if(!a.crossing || a.dead || allies.indexOf(a)<0) continue;
    a.x += a.crossing;
    if(a.crossing > 0 ? a.x > W+60 : a.x < -60){
      if(a.dockedTo){ a.dockedTo.dead = true;
        const _ci = allies.indexOf(a.dockedTo);
        if(_ci>=0) allies.splice(_ci,1);
        const _ce = enemies.indexOf(a.dockedTo);
        if(_ce>=0) enemies.splice(_ce,1); }
      crossDone++; if(!a.emptyRun) protSaved++;
      if(a.uid) EV_LEFT[a.uid] = true;
      { const _fi = allies.indexOf(a); if(_fi>=0) allies.splice(_fi,1); }
      SUB_MSGS.push({x:(a.crossing > 0) ? W-90 : 90, y:a.y,
                     txt: (hullClass(a.img)==='ep') ? 'RESCUED'
                          : (a.emptyRun ? 'LEFT EMPTY' : 'DELIVERED'),
                     life:150, ml:150, ally:true, tone:'good'});
    }
  }
  // Sind alle durch, ist der Auftrag erfuellt und die Welle raeumt nur noch auf.
  if(crossTotal && crossDone >= crossTotal) guardGone = true;
}

// Ein lebendes Fuehrungsschiff mit heilem Funkraum genuegt. Zerstoerte
// zaehlen nicht mehr mit - wer die Typhon mit heilem Funkraum abschiesst,
// waehrend der der Hatshepsut schon hin ist, bekommt trotzdem keinen
// Nachschub mehr.
let commsCut = false;
function enemyRadioAlive(){
  for(const e of enemies){
    if(e.dead || e.warp>0) continue;
    if(!hasSubsystems(e)) continue;
    if(subOK(e,'communication')) return true;
  }
  return false;
}
let commsSeen = false;
// Lebt noch ein Grosskampfschiff? Ohne eines gibt es keinen Funkraum, der
// zerstoert sein koennte - dann ist die Welle vorbei und nicht der Funk.
function enemyCapAlive(){
  for(const e of enemies)
    if(!e.dead && e.warp<=0 && hasSubsystems(e)) return true;
  return false;
}
function tickComms(){
  if(commsCut) return;
  if(enemyRadioAlive()){ commsSeen = true; return; }
  if(!enemyCapAlive()) return;
  // Ohne vorher gesehenen heilen Funkraum gibt es nichts abzuschalten.
  // Einwarpende Schiffe zaehlen dabei nicht, sonst feuert die Meldung in
  // der Luecke zwischen Ankunft und fertigem Warp.
  if(!commsSeen) return;
  commsCut = true;
  // Staffeln, die noch nicht da sind, kommen nicht mehr.
  let weg = 0;
  for(let i=spawnQ.length-1;i>=0;i--){
    const t = spawnQ[i].type;
    if(t && WING_TYPES[t]){ spawnQ.splice(i,1); weg++; }
  }
  notice('ENEMY COMMS DOWN', 'good');
}

function tickDefectors(){
  if(GS!=='playing') return;
  for(let i=allies.length-1;i>=0;i--){
    const a = allies[i];
    if(!a.defectAt || a.dead) continue;
    if(--a.defectAt>0) continue;
    allies.splice(i,1);
    defect(a);
  }
}

// ── STANDING ASTEROID FIELD ──────────────────────────────────
// Rocks that turn but do not travel. Everything mkEnemy('ast') builds
// drifts left and is cleaned up at the edge; these are marked scenery so
// the wave end ignores them, and the clearing beat pushes them off at the
// end like any other loose object.
function seedStaticField(n){
  for(let i=0;i<n;i++){
    const y = HUD_H+40+Math.random()*(H-HUD_H-80);
    const a = mkEnemy('ast', null, y);
    if(!a) continue;
    a.x = 90+Math.random()*(W-180);
    a.vx = 0; a.vy = 0;
    a.rotS = (Math.random()-0.5)*0.02;
    a.scenery = true; a.side='enemy'; a.warpMax = 1;
    enemies.push(a);
  }
}

// ── SPAWN OPTIONS ────────────────────────────────────────────
// Anything a queue entry wants to say about the ship it produces, applied
// in one place after the ship exists. Keeping it here means mkEnemy keeps
// its eleven branches and none of them grow a parameter list.
function applySpawnOpts(e, sp){
  if(!e || !sp) return;
  // Anything already in place when the wave opens: cargo sitting at a
  // depot, a gun platform guarding it. In the test both warped in, which
  // reads as reinforcements arriving rather than as scenery that was
  // always there.
  if(sp.noWarp){ e.warp=0; e.warpMax=1; }
  // A fixed position on the field. Without it the non-combatants keep the
  // spawn x of a ship that is expected to fly in from the right, and a
  // container that never moves simply stays off screen.
  if(sp.x!=null){ e.x=sp.x; e.warpX=sp.x; }
  // A disable job wants the ship to stay put. checkDisarmFlee() starts a
  // twelve second clock the moment the weapons are gone, so in the test
  // the cruiser began its jump out halfway through the task.
  if(sp.scenery) e.scenery = true;
  if(sp.capRam){
    e.capRam = sp.capRam; e.noFlee = true;
    // Volle Hoehe: ein Rammkurs muss steigen und sinken koennen. still
    // gilt nur fuer das Ziel, nicht fuer den Angreifer.
    e.minY = HUD_H+10; e.maxY = H-10;
  }
  if(sp.dockTo) e.dockTo = sp.dockTo;
  if(sp.dockHold) e.dockHold = Math.round(sp.dockHold*TICK_HZ);
  if(sp.pickup) e.pickup = true;
  // Kein Auf und Ab: ein Rammstoss auf ein schwebendes Ziel ist Zufall.
  // still gilt dem Ziel, nicht dem Angreifer - und stand bisher unter der
  // capRam-Zeile, hat ihr also die volle Hoehe wieder weggenommen. Ein
  // Rammkurs traf dadurch nur, wenn er zufaellig auf der Hoehe seines
  // Zieles erschien, und zog sonst am Ziel vorbei bis an den linken Rand.
  // A height the mission gives is kept. assignStation() picks a free
  // lane on its own, which is right for ships that simply arrive. Set
  // before still, which pins the ship to whatever height it has.
  if(sp.fixY && !sp.capRam){ e.y = sp.y; e.warpY = sp.y; }
  if(sp.still){
    e.vy = 0;
    if(!e.capRam){ e.minY = e.y; e.maxY = e.y; }
  }
  // Eine Station, die der Spieler halten soll, ist ein Ort und kein Ziel.
  // Unverwundbar heisst hier: sie nimmt keinen Schaden und zaehlt nicht
  // fuer das Wellenende - sonst waere jede Welle mit ihr unbeendbar.
  if(sp.invuln){ e.invuln = true; e.scenery = true; }
  // Halb ausserhalb des Feldes: eine Arcadia ist groesser als der Schirm,
  // und das soll man sehen.
  if(sp.edge){
    const _ii = IMGS[e.img];
    const _iw = _ii ? _ii.width*e.sc : 400;
    e.x = W + _iw*(sp.edge-0.5); e.warpX = e.x;
  }
  if(sp.escape){
    e.escaping = sp.escape;          // Bildpunkte je Schritt nach rechts
    e.noFlee = true;                 // sie springt nicht, sie faehrt
    // Weit hinter der Wegschwelle: die Fahrt stoppt bei targetX, und wenn
    // targetX davor liegt, parkt das Schiff ausserhalb des Bildes.
    const _si = IMGS[e.img];
    const _sw = _si ? _si.width*e.sc : 120;
    e.targetX = W + _sw*2;
    e.vx = 0; e.vy = 0;    // gefahren wird ueber tickEscapers, nicht ueber vx
    e.flip = needsFlip(e.img, false);
  }
  if(sp.disable) e.noFlee = true;
  // A stationary ship placed with x stays at x. Without this the station
  // drive takes it to the class's usual spot at the right.
  if(sp.still && sp.x!=null && !sp.capRam) e.targetX = sp.x;
  if(sp.noFlak) e.noFlak = true;
  // A jump nobody can stop: there is no navigation subsystem to shoot.
  if(sp.navProof && e.subs) e.subs = e.subs.filter(function(s){ return s.id!=='navigation'; });
  if(sp.fleeFree) e.fleeFree = true;
  // Jumps as soon as it reaches the right edge instead of driving out.
  if(sp.escWarp) e.escWarp = true;
  // To be taken, not destroyed: held above the hull floor until the
  // capture happens or is called off ('kapern', 'freigeben').
  if(sp.capture) e.captureLock = true;
  // Scanned before it may die: the scan is the point of it.
  if(sp.scanFirst) e.scanLock = true;
  // Scanned subsystem by subsystem, see tickSubScan().
  if(sp.scanSubs && e.subs){ e.scanSubs = true; e.noTarget = true;
    for(const s of e.subs){ s.scanT = 0; s.scanned = false; } }
  // Unshielded on purpose. Vasudan fighters carry none in the early part
  // of FS1, and the wave says so rather than the ship class deciding.
  if(sp.noShield){ e.maxSh = 0; e.sh = 0; }
  // A runner is counted, so the wave can tell how many got away.
  if(sp.runner) e.runner = true;
  // A ship that has lost its drive and is only there to be defended.
  if(sp.still){ e.vx = 0; e.vy = 0; e.still = true; }
  // Damaged on arrival. maxHp is deliberately left alone so the hull bar
  // shows the ship as hurt rather than as small.
  if(sp.hpMul){
    e.hp = Math.max(1, Math.round(e.hp*sp.hpMul));
    // Above one the bar has to grow with the hull, or the ship arrives
    // reading as over full. Below one maxHp stays where it is on purpose,
    // so a damaged ship looks damaged rather than small. Subsystems are
    // laid out before this runs and keep their original size either way,
    // which is the point for a disable job: the same 492 points of system
    // work, but more hull to absorb what misses.
    if(sp.hpMul>1) e.maxHp = Math.max(e.maxHp, e.hp);
    // The shield has to come down with it. A fighter carries 48 hull and
    // 30 shield, so leaving the shield at full would make an hpMul of
    // 0.40 mean 63 % of the real toughness rather than 40 %. maxSh is
    // lowered as well, otherwise it simply recharges back to full within
    // three seconds and the whole thing is undone.
    if(e.maxSh){
      e.maxSh = Math.max(1, Math.round(e.maxSh*sp.hpMul));
      e.sh = e.maxSh;
    }
  }
  if(sp.fac) e.faction = sp.fac;
  if(sp.scan){ e.scan = true; e.noTarget = true; }
  // Arrives with only this share of her hull; the bar shows the damage.
  if(sp.hurt) e.hp = Math.max(1, Math.round(e.maxHp*sp.hurt));
  // An installation that fights: its guns fire, and it has subsystems
  // to shoot them out. It never runs, it has nowhere to go.
  if(sp.armed){ e.armed = true; e.subsOn = true; e.noFlee = true; initSubsystems(e); }
  // Stays and fights on with her guns gone instead of running.
  if(sp.noFlee) e.noFlee = true;
  // Tiefenversatz fuer mehrere Grosskampfschiffe derselben Kennung.

  // Eigenes Hoehenband, damit mehrere Schiffe derselben Kennung nicht
  // durch dasselbe Feld wandern und aneinander abprallen.
  // Volle Hoehe fuer alle, aber versetzt gestartet und in wechselnder
  // Richtung: sie schweben aneinander vorbei statt uebereinander.
  // Tiefenversatz aus der eigenen Breite: er muss die Summe der halben
  // Breiten uebersteigen, sonst greift separateCapitals() dauernd ein und
  // die Schiffe schubsen sich gegenseitig aus ihrer Bahn. Teilen sie sich
  // keinen Bildraum, waehlt assignStation() die Hoehe frei - und alle
  // nutzen das ganze Feld.
  if(sp.capIndex){
    const _ci = IMGS[e.img];
    const _cw = _ci ? _ci.width*e.sc : 120;
    e.targetX = (e.targetX!=null ? e.targetX : e.x) - sp.capIndex*(_cw + 16);
  }
  if(sp.disable){
    disableTarget = e;
    e.disableTgt = true; e.disableMet = false;
    // Die Subsysteme stehen zu diesem Zeitpunkt schon, also werden sie
    // nachtraeglich umgesetzt statt initSubsystems zu verzweigen.
    if(e.subs){
      const dh = Math.max(30, Math.round(e.maxHp*DISABLE_SUB_FRAC));
      for(const s of e.subs){ s.hp = dh; s.maxHp = dh; }
    }
  }
}

// ── TEST WAVES ───────────────────────────────────────────────
// Reached with ?test=1 appended to the URL. Three short waves, each
// showing one group of the new systems, so a fault can be placed without
// guessing which of nine changes caused it.
//   1  arrival rule and damaged arrivals
//   2  non-combatants, scanning, standing asteroid field
//   3  defector and a cruiser that has to be disabled
// ?test=1 through ?test=4 all switch test mode on; the number chooses
// which of the four waves the run opens with, so the crossfire in wave 4
// does not have to be reached by playing the three before it.
// Review switches for the interface work, and for nothing else.
// ?ships=N opens N hulls from the start, ?ui=1 puts one ticket of every
// class in hand and ?wpn=1 opens every weapon, so any panel can be looked
// at without playing up to it first. None of them touches a rule the panel
// is being judged on.
const UI_SHIPS_MATCH = /[?&]ships=([1-8])/.exec(location.search);
const UI_SHIPS   = UI_SHIPS_MATCH ? parseInt(UI_SHIPS_MATCH[1],10) : 1;
const UI_TICKETS = /[?&]ui=1/.test(location.search);
// ?wpn=1 opens every weapon whatever the score. Separate from ?ui=1 on
// purpose, so the locked rows can still be looked at with ui alone.
const UI_WEAPONS = /[?&]wpn=1/.test(location.search);

const TEST_MATCH = /[?&]test=([1-4])/.exec(location.search);
const TEST_MODE  = !!TEST_MATCH;
const TEST_FIRST = TEST_MATCH ? parseInt(TEST_MATCH[1],10) : 1;

function testWing(q, t, type, spr, fac, count, wid, hpMul){
  const half=(count-1)*WING_SPACING*0.5;
  const mid=HUD_H+80+Math.random()*(H-HUD_H-160);
  for(let k=0;k<count;k++){
    q.push({time:t+k*WING_STAGGER, type:type, spr:spr, wing:wid, fac:fac,
            hpMul:hpMul||0, y:mid-half+k*WING_SPACING});
  }
}

function buildTestWave(n){
  // Everything getWaveDef normally sets has to be set here too, or the
  // previous wave leaves its state behind.
  currentEra = 'fs2';
  waveFeud = false;
  currentFaction = 'ntf';
  waveLive = 8;
  fleeTotal = 0; fleeEscaped = 0;
  guardWanted = false; guardSpawned = false; guardLost = false;
  guardClass = 'cruiser'; guardFrac = GUARD_HULL_FRAC; guardReward = 'cruiser';
  astAim = false; transitSecs = 0; guardGone = false;
  astStreamCd = AST_STREAM_MEAN;
  empOut = 0; empWarn = 0; empNext = 0;
  BOMB_PORTALS = []; bombRaidLeft = 0; bombRaidCd = 99999;
  reinfAt = 0; reinfDone = true;
  gateWings = true; gateWing = 0;
  disableTarget = null;
  waveMod = MOD_NONE;
  const q = [];

  if(n===1){
    // Eve of Destruction in miniature: four wings of damaged Vasudan
    // fighters, arriving one after the other. Hull runs 30/40/35/50 % so
    // the wave gets harder without a single extra ship.
    testWing(q, 60,  'fi_ntf', 'fianubis', 'vasudan', 2, ++wingSeq, 0.40);
    testWing(q, 200, 'fi_ntf', 'fianubis', 'vasudan', 2, ++wingSeq, 0.30);
    testWing(q, 340, 'fi_ntf', 'fianubis', 'vasudan', 3, ++wingSeq, 0.35);
    testWing(q, 480, 'fi_ntf', 'fianubis', 'vasudan', 3, ++wingSeq, 0.50);
  }
  else if(n===2){
    // Small Deadly Space in miniature. One freighter that runs when hit,
    // three containers to scan, three sentry guns that cannot come to the
    // player, and a standing field to fly through.
    waveMod = 'astfield';
    // The freighter still flies in from the right: it is passing through,
    // which is why catching it is the job. Everything else belongs to the
    // depot and is standing there when the wave opens.
    q.push({time:40, type:'freighter', spr:'frbast', fac:'vasudan', y:H*0.35});
    q.push({time:1, type:'container', spr:'fcvc3', fac:'vasudan',
            x:W*0.62, y:H*0.50, scan:1, noWarp:1});
    q.push({time:1, type:'container', spr:'fcvc3', fac:'vasudan',
            x:W*0.72, y:H*0.66, scan:1, noWarp:1});
    q.push({time:1, type:'container', spr:'fcvc3', fac:'vasudan',
            x:W*0.58, y:H*0.80, scan:1, noWarp:1});
    q.push({time:1, type:'sentry', spr:'sgtrident', fac:'shivan',
            x:W*0.86, y:H*0.30, noWarp:1});
    q.push({time:1, type:'sentry', spr:'sgtrident', fac:'shivan',
            x:W*0.88, y:H*0.58, noWarp:1});
    q.push({time:1, type:'sentry', spr:'sgtrident', fac:'shivan',
            x:W*0.84, y:H*0.82, noWarp:1});
    testWing(q, 500, 'fi_ntf', 'fibasilisk', 'shivan', 2, ++wingSeq, 0);
  }
  else if(n===4){
    // Out of the Dark, Into the Night in miniature, and the only test for
    // the crossfire. Vasudans first, then the unknowns, who go for the
    // Vasudans rather than for the player. FS1 rules are on: the cruiser
    // has no beam, and only the Vasudans fly without a shield.
    currentEra = 'fs1';
    waveFeud = true;
    waveLive = 12;
    testWing(q, 60,  'fi_ntf', 'fianubis', 'vasudan', 3, ++wingSeq, 0);
    testWing(q, 90,  'fi_ntf', 'fihorus',  'vasudan', 3, ++wingSeq, 0);
    testWing(q, 400, 'fi_ntf', 'fibasilisk', 'shivan', 3, ++wingSeq, 0);
    // Gating off for this one: both sides have to be on the field at the
    // same time or there is nothing to watch.
    gateWings = false;
    // Only the Vasudans. The first version stripped the shields from
    // everything already in the queue, the Basilisks included, which turns
    // the whole point of FS1 upside down: Shivan shields are the shock,
    // and the fleet has no answer to them until The Hammer and the Anvil.
    for(const s of q) if(s.fac==='vasudan') s.noShield = 1;
    q.push({time:200, type:'cr_ntf', spr:'craten', fac:'vasudan', y:H*0.5});
  }
  else {
    // First Strike in miniature plus the ruse from The Hammer and the
    // Anvil. The escort turns, and the cruiser has to be left alive and
    // useless rather than destroyed.
    // Hull at 1.6 so there is room to miss. Subsystems keep their own
    // size, so the work is unchanged at 492 points while the hull grows
    // from 1120 to 1792: at half accuracy the Cain now finishes at 59 %
    // instead of 34 %, which is the difference between a task and a test
    // of marksmanship.
    q.push({time:60, type:'cr_ntf', spr:'crcain', fac:'shivan', y:H*0.5,
            disable:1, hpMul:1.6});
    q.push({time:120, type:'defector', y:H*0.4});
    testWing(q, 600, 'fi_ntf', 'fibasilisk', 'shivan', 2, ++wingSeq, 0);
  }
  return q.sort(function(a,b){ return a.time-b.time; });
}

let bossAlive=false,bossSlain=false;
// ── PLAYER SHIPS ─────────────────────────────────────────────
// Unlock order for the Hammer of Light cycle; the first entry is the
// starting ship. unlock is the score at which a hull becomes selectable
// during a run. Values come from the notes in the mount file:
// spd  top speed in px per logic step (fighter default 3.2)
// turn max heading change per logic step (default 0.14)
// hp   hull before cycle scaling, sh shield maximum, sec secondary rounds
// fac decides which hangar hands the hull out. Only Vasudan hulls exist so
// far; a Terran list is added when a cycle needs one.
const PLAYER_SHIPS = [
  {key:'fitoth',    name:'GVF Thoth',   fac:'vasudan', unlock:0,     spd:3.5, turn:0.17, hp:100, sh:100, sec:20},
  {key:'fihorus',   name:'GVF Horus',   fac:'vasudan', unlock:4000,  spd:3.2, turn:0.17, hp:80,  sh:100, sec:20},
  {key:'boosiris',  name:'GVB Osiris',  fac:'vasudan', unlock:9000,  spd:2.5, turn:0.10, hp:140, sh:100, sec:10},
  {key:'fiserapis', name:'GVF Serapis', fac:'vasudan', unlock:15000, spd:3.5, turn:0.17, hp:80,  sh:70,  sec:20},
  {key:'fiseth',    name:'GVF Seth',    fac:'vasudan', unlock:22000, spd:2.5, turn:0.10, hp:125, sh:130, sec:20},
  {key:'bobakha',   name:'GVB Bakha',   fac:'vasudan', unlock:31000, spd:2.5, turn:0.12, hp:100, sh:100, sec:8},
  {key:'fitauret',  name:'GVF Tauret',  fac:'vasudan', unlock:43000, spd:2.9, turn:0.10, hp:100, sh:130, sec:20},
  {key:'bosekhmet', name:'GVB Sekhmet', fac:'vasudan', unlock:58000, spd:2.5, turn:0.12, hp:140, sh:130, sec:12}
];

// ── CYCLES ───────────────────────────────────────────────────
// A run is made of cycles of written missions, and each cycle brings its
// own fleet: the hulls the player flies, the order they open in, and who
// answers a support call. PLAYER_SHIPS above is the Hammer of Light roster
// and stays the one array everything reads - entering a cycle refills it
// in place, so no reader has to know that cycles exist.
//
// Inside a cycle, unlock counts the points scored SINCE the cycle began.
// Every cycle opens its roster from the bottom, whatever the run brought
// into it.
const ROSTER_HOL = PLAYER_SHIPS.slice();
const ROSTER_NTF = [
  {key:'fimyrmidon', name:'GTF Myrmidon',      fac:'terran', unlock:0,     spd:3.4, turn:0.16, hp:100, sh:100, sec:20},
  {key:'fiherc',     name:'GTF Hercules',      fac:'terran', unlock:4000,  spd:3.0, turn:0.14, hp:120, sh:110, sec:20},
  {key:'boartemis',  name:'GTB Artemis',       fac:'terran', unlock:9000,  spd:2.6, turn:0.11, hp:130, sh:100, sec:10},
  {key:'fihercmk2',  name:'GTF Hercules Mk II',fac:'terran', unlock:15000, spd:3.2, turn:0.16, hp:110, sh:120, sec:20},
  {key:'bomedusa',   name:'GTB Medusa',        fac:'terran', unlock:22000, spd:2.4, turn:0.10, hp:150, sh:110, sec:12},
  {key:'fierinyes',  name:'GTF Erinyes',       fac:'terran', unlock:31000, spd:2.8, turn:0.12, hp:130, sh:140, sec:20},
  {key:'boursa',     name:'GTB Ursa',          fac:'terran', unlock:43000, spd:2.3, turn:0.10, hp:170, sh:130, sec:14},
  {key:'fiares',     name:'GTF Ares',          fac:'terran', unlock:58000, spd:3.3, turn:0.15, hp:120, sh:140, sec:20}
];
// first: the first wave of the cycle. call: which support columns answer.
const CYCLES = [
  {first:1,  roster:ROSTER_HOL, call:{terran:false, vasudan:true}},
  {first:31, roster:ROSTER_NTF, call:{terran:true,  vasudan:false}}
];
let cycleNow  = null;   // the CYCLES entry the run is in
let cycleBase = 0;      // score when it began; hull unlocks count from here
function cycleAt(n){
  let c = CYCLES[0];
  for(const x of CYCLES) if(n >= x.first) c = x;
  return c;
}
// Puts the run into a cycle: its roster, its support columns, and its
// first hull, fresh. The hull the player had belongs to the old fleet.
function enterCycle(c){
  cycleNow  = c;
  cycleBase = score;
  PLAYER_SHIPS.length = 0;
  for(const s of c.roster) PLAYER_SHIPS.push(s);
  for(const k in c.call) ALLY_FAC_ON[k] = c.call[k];
  shipUnlocked = Math.max(1, Math.min(UI_SHIPS, PLAYER_SHIPS.length));
  shipSwapWave = -1;
  applyShip(PLAYER_SHIPS[0].key);
}

// ── WAVE ARCHETYPES ──────────────────────────────────────────
// A wave is described by what it is, not by a pile of numbers. fi and bo
// count wings, not ships. live is how many small craft may be up at once
// and pause is the gap between wings, both in the wave rather than in a
// global formula, because a quiet wave and a swarm need opposite values.
// caps lists capital ships in arrival order; flee gives one of them a
// deadline in seconds after which it jumps out.
//
// Twenty wave cycle: nine waves per campaign and a single boss to close
// it, instead of a boss every six waves.
// The Shivan half runs the same shapes one step harder.
const WAVE_LIVE_SHIVAN = 1;   // extra simultaneous small craft
const WAVE_TIER_WINGS = 1;    // extra wings per completed cycle
const WAVE_TIER_LIVE  = 1;    // extra simultaneous per completed cycle

let waveLive = 5;             // cap for the wave being fought
// Von der Komposition angeforderte verbuendete Jaeger. Sie teilen das
// Strahlenfeuer: beamTargets() sammelt fuer einen gegnerischen Kleinstrahl
// den Spieler UND alle kleinen Verbuendeten.
let allyWingWanted = 0;
// Der Auftrag, der gerade gilt. Lag bisher nur als lokale Variable in
// getWaveDef - ein Ereignis muss ihn wechseln koennen.
let waveObj = 'clear';
// Kennung, auf die gegnerische Jaeger es abgesehen haben. Ohne sie zielen
// sie ausschliesslich auf den Spieler, und ein Schuetzling ist nie in
// Gefahr. HUNT_SHARE ist der Anteil der Jaeger, der auf das Ziel geht -
// nicht alle, sonst steht der Spieler unbehelligt daneben.
let waveHunt = '';
// Stehendes Feld: die Brocken drehen sich, aber treiben nicht. Ein Gebiet,
// durch das man fliegt, statt eines Stroms, der vorbeizieht.
let astStill = false;
// Hat der Auftrag in dieser Welle ueberhaupt schon einmal gegolten?
let objSeenOnce = false;
const HUNT_SHARE = 0.5;
let fleeTotal = 0, fleeEscaped = 0;

// ── STATISTIK ─────────────────────────────────────────────────
// Vorbereitung fuer die Medaillen. Bewusst allgemein gehalten: welche
// Errungenschaften es geben wird, steht noch nicht fest, aber diese Zahlen
// lassen sich nachtraeglich nicht rekonstruieren. Sie zaehlen nur
// innerhalb eines Durchgangs; ob sie ihn ueberdauern, ist eine spaetere
// Entscheidung und beruehrt das Zaehlen nicht.
const STATS_ZERO = {
  shots:0, hits:0,          // fuer die Trefferquote
  killFighter:0, killBomber:0, killCruiser:0, killCorvette:0,
  killDestroyer:0, killBoss:0, killAsteroid:0,
  // Counted separately from warships. Several FS1 and FS2 medals hang on
  // what happened to the freighters and the cargo, and a number that was
  // never counted cannot be recovered afterwards.
  killFreighter:0, killContainer:0, killSentry:0,
  scans:0,
  bombsShot:0,              // abgefangene Bomben
  escortsCalled:0,
  livesLost:0,
  subsKilled:0,
  ticketsEarned:0
};
let STATS = Object.assign({}, STATS_ZERO);
function statsReset(){ STATS = Object.assign({}, STATS_ZERO); }
function statKill(type){
  const m = {fighter:'killFighter', bomber:'killBomber', cruiser:'killCruiser',
             corvette:'killCorvette', destroyer:'killDestroyer',
             boss:'killBoss', asteroid:'killAsteroid',
             freighter:'killFreighter', container:'killContainer',
             sentry:'killSentry'};
  const k = m[type];
  if(k) STATS[k]++;
}

// The Iceni gets away in FreeSpace 2, repeatedly, and that is the point of
// her. Every escape here makes the next meeting harder, which turns one
// wave into a thread running through the whole run without a line of text.
const ICENI_HULL = 3500;
const ICENI_GROWTH = 0.15;      // hull added per previous escape
let icenEscapes = 0;

// Laenge der handgesetzten Folge. Muss zu WAVE_SEQ passen; wird nur fuer
// das Huellenwachstum je Zyklus gebraucht (cycleMult).
const WAVE_CYCLE = 20;

// ── DREI ACHSEN STATT EINER ZEILE ────────────────────────────
// Bis v81 stand eine Welle in einer Zeile, und in dieser Zeile steckten
// drei verschiedene Dinge:
//
//   {name:'Asteroid Escort', fi:5, ast:0, caps:[], live:3, pause:520,
//    guard:'destroyer', guardFrac:1.00, astAim:1, transit:50}
//
// fi/bo/ast/caps/live/pause sagen, WER KOMMT. guard und guardFrac sagen,
// WAS ZU TUN IST. astAim und transit sind die Mechanik dieses Auftrags.
// Weil sie verschweisst waren, liessen sich elf Zeilen nicht rekombinieren
// und elf Wellen fuehlten sich an wie eine: alle hatten denselben Auftrag,
// naemlich das Feld leerraeumen.
//
// Getrennt ergeben 17 Kompositionen mal 9 Auftraege 153 Felder, von denen
// rund ein Viertel unvertraeglich ist. Was bleibt, traegt 100 Wellen ohne
// Wiederholung - und Modifikatoren und Fraktionen sind darin noch nicht
// mitgezaehlt.

// ── ACHSE 1: KOMPOSITION ── wer kommt, sonst nichts ──────────
//   fi/bo   Staffeln, nicht Schiffe. Eine Staffel sind drei bis vier.
//   ast     Brocken, Kulisse
//   sg      Sperrgeschuetze. Zaehlen NICHT gegen live (WING_TYPES kennt
//           sie nicht), halten die Welle aber offen, bis sie fallen.
//   live    wie viele Jaeger und Bomber gleichzeitig im Feld stehen
//   pause   Abstand zwischen zwei Staffeln
const COMPOS = {
  patrol:    {name:'Patrol',          fi:2, bo:0, ast:0,  sg:0, caps:[],           live:3, pause:600},
  belt:      {name:'Asteroid Belt',   fi:2, bo:0, ast:10, sg:0, caps:[],           live:4, pause:600},
  bomberrun: {name:'Bomber Run',      fi:1, bo:2, ast:0,  sg:0, caps:[],           live:4, pause:700},
  crpatrol:  {name:'Cruiser Patrol',  fi:2, bo:0, ast:3,  sg:0, caps:['cr'],       live:4, pause:600},
  heavy:     {name:'Heavy Patrol',    fi:5, bo:0, ast:0,  sg:0, caps:[],           live:3, pause:520},
  swarm:     {name:'Swarm',           fi:5, bo:0, ast:0,  sg:0, caps:[],           live:5, pause:300},
  push:      {name:'Push',            fi:2, bo:1, ast:0,  sg:0, caps:['cr','co'],  live:4, pause:600},
  flagship:  {name:'Flagship',        fi:2, bo:0, ast:2,  sg:0, caps:['cr'],       live:4, pause:600, iceni:1},
  siege:     {name:'Siege',           fi:3, bo:2, ast:0,  sg:0, caps:['co','de'],  live:5, pause:500, reinf:2600},
  bomberwing:{name:'Bomber Wing',     fi:1, bo:4, ast:0,  sg:0, caps:[],           live:4, pause:500},
  bosswave:  {name:'Boss',            fi:3, bo:2, ast:0,  sg:0, caps:['boss'],     live:5, pause:600, reinf:3000},

  // ── neu in v82 ──
  // Drei leichte Traeger fuer Grosskampfschiffe. Lahmlegen hatte vorher nur
  // vier Traeger, und drei davon waren schwere Wellen; jetzt sind es sieben
  // mit einer Spanne von 8,9 bis 45 Sekunden statt nur "schwer".
  lonecr:    {name:'Lone Cruiser',    fi:1, bo:0, ast:0,  sg:0, caps:['cr'],       live:3, pause:600},
  loneco:    {name:'Lone Corvette',   fi:1, bo:0, ast:0,  sg:0, caps:['co'],       live:3, pause:600},
  // Die einzige Komposition ohne gegnerische Jaeger. Sie war in der ersten
  // Fassung ein Lebensfresser: das Waffensystem eines Zerstoerers hat
  // 0.10*6500 = 650 Trefferpunkte, also 4,1 s Dauerfeuer auf ein Ziel von
  // 24 px Radius, waehrend zwei Antijaegerstrahlen bei 1,4 je Schritt in
  // 1,43 s Kontakt toeten. Drei Dinge retten sie:
  //   - die Brocken beschaedigen auch Gegner (updateAsteroidImpacts prueft
  //     Spieler, Verbuendete UND Gegner), und astRamDmg rechnet 3,5 bis
  //     7,5 PROZENT von maxHp: dreizehn Volltreffer legen ihn allein um
  //   - capitalFire ruft eSmall mit ang=null und schiesst damit stur nach
  //     links, also in die eigene Fahrtrichtung - von hinten steht man
  //     ausserhalb der Salven
  //   - beamTargets sammelt fuer einen Kleinstrahl den Spieler UND alle
  //     kleinen Verbuendeten, die gerufene Staffel teilt das Feuer wirklich
  crossing:  {name:'Silent Crossing', fi:0, bo:0, ast:14, sg:0, caps:['de'],       live:3, pause:600,
              slowCap:1, allyWing:3},
  // Sperrgeschuetze stehen ausserhalb des live-Deckels: zusaetzlicher Druck
  // ohne Bremse.
  gunline:   {name:'Gun Line',        fi:2, bo:0, ast:0,  sg:6, caps:[],           live:4, pause:600},
  // Ersetzt belt als eigenstaendige Welle. Zehn Brocken allein sind 400 von
  // 946 Trefferpunkten, also 2,5 Sekunden Streu; mit vier Geschuetzen
  // dazwischen werden sie Deckung statt Ziel.
  minefield: {name:'Minefield',       fi:1, bo:0, ast:10, sg:4, caps:[],           live:3, pause:600},
  // Frachter und Container hat der Endlosmodus nie gesehen. Traegt Laeufer
  // abfangen, Fracht scannen und Schuetzling schuetzen auf einmal.
  convoy:    {name:'Convoy',          fi:3, bo:0, ast:0,  sg:0, caps:[],           live:5, pause:520,
              cargo:2}
};

// ── ACHSE 2: AUFTRAG ── was zu tun ist ───────────────────────
// Genau einer je Welle. Der Grund ist die Anzeige und nicht die Mechanik:
// bei rund 90 Sekunden je Welle geht ein zweiter Hinweis unter.
const OBJ = {
  clear:   {t:'[ CLEAR THE FIELD ]'},
  guard:   {t:null, cls:'destroyer'},   // Text kommt aus objectiveText()
  transit: {t:null, cls:'destroyer', secs:50, aim:1},
  runner:  {t:null, flee:40, ships:[['frposeidon',2]]},
  scan:    {t:null, cargo:3},
  disable: {t:null},
  protect: {t:null, ships:[['frposeidon',2]]},
  feud:    {t:'[ THREE WAY FIGHT ]'},
  boss:    {t:null}
};

// ── VERTRAEGLICHKEITSMATRIX ──────────────────────────────────
// 17 Kompositionen mal 9 Auftraege. Jedes Nein hat einen mechanischen
// Grund, keinen Geschmack:
//   - Lahmlegen braucht ein Ziel mit Subsystemen. hasSubsystems() gilt nur
//     fuer Grosskampfschiffe.
//   - Auf einer Querung muss gateWings aus sein, sonst blockiert die erste
//     Staffel sich selbst. Ohne Schleuse kommen die Staffeln nach Uhr, und
//     bei fuenf Staffeln steht dann alles gleichzeitig im Bild.
//   - Laeufer brauchen freie Bahn nach links; zehn stehende Brocken
//     verstopfen sie.
//   - Ein Boss ist das Ereignis der Welle. Ein zweites Kopfthema daneben
//     wird nicht gelesen.
const ALL_K = Object.keys(COMPOS);
const OBJ_OK = {
  clear:   ALL_K,
  guard:   ALL_K.filter(function(k){ return k!=='bosswave'; }),
  transit: ['patrol','belt','bomberrun','crpatrol','push','flagship',
            'bomberwing','lonecr','loneco','gunline','minefield','convoy'],
  runner:  ['patrol','bomberrun','crpatrol','heavy','push','flagship','siege',
            'bomberwing','lonecr','loneco','gunline','convoy'],
  scan:    ['patrol','belt','bomberrun','crpatrol','heavy','push','flagship',
            'bomberwing','lonecr','loneco','gunline','minefield','convoy'],
  disable: ['crpatrol','push','flagship','siege','lonecr','loneco','crossing'],
  protect: ['patrol','belt','bomberrun','crpatrol','heavy','push','flagship',
            'bomberwing','lonecr','loneco','gunline','minefield','convoy'],
  feud:    ['belt','bomberrun','crpatrol','heavy','swarm','push','flagship',
            'siege','bomberwing','gunline','minefield','convoy'],
  boss:    ['bosswave']
};
function objFits(k, o){ return (OBJ_OK[o]||[]).indexOf(k) >= 0; }

// ── HANDGESETZTE FOLGE ───────────────────────────────────────
// Die ersten zwanzig Wellen sind geschrieben und nicht gewuerfelt. Der
// Grund ist nicht technisch: wer zwanzig Minuten hineinschaut, sieht genau
// diesen Abschnitt und sonst nichts, und der soll bei jedem gleich gut
// sein. Ab Welle 21 ist Abwechslung mehr wert als Kontrolle.
//   f: Fraktion. 'hol' ist der Hammer of Light und kommt erst mit v83;
//      bis dahin faellt er auf die NTF zurueck, siehe factionOf().
const WAVE_SEQ = [
  {k:'patrol',    o:'clear',   f:'ntf'},     //  1  Einstieg
  {k:'minefield', o:'clear',   f:'ntf'},     //  2  Wendigkeit
  {k:'bomberrun', o:'guard',   f:'ntf'},     //  3  Tempo
  {k:'lonecr',    o:'runner',  f:'ntf'},     //  4  erstes Grosskampfschiff, als Jagd
  {k:'convoy',    o:'scan',    f:'hol'},     //  5  Verweilen unter Feuer
  {k:'swarm',     o:'feud',    f:'hol'},     //  6  Kurvenkampf
  {k:'gunline',   o:'clear',   f:'shivan'},  //  7  Reichweite, Deckung
  {k:'heavy',     o:'clear',   f:'shivan'},  //  8  Rumpf, Dauerfeuer
  {k:'loneco',    o:'guard',   f:'shivan'},  //  9  Eskorte gegen eine Korvette
  {k:'bomberwing',o:'protect', f:'ntf'},     // 10  vor dem Abwurf abfangen
  {k:'flagship',  o:'runner',  f:'ntf'},     // 11  Burst, 40-Sekunden-Frist
  {k:'belt',      o:'clear',   f:'hol'},     // 12
  {k:'crpatrol',  o:'scan',    f:'hol'},     // 13  neben einem Kreuzer
  {k:'crossing',  o:'disable', f:'shivan'},  // 14  Ausdauer
  {k:'push',      o:'clear',   f:'shivan'},  // 15  gemischt, schwer
  {k:'bosswave',  o:'boss',    f:'ntf'},     // 16  im Fenster 12 bis 18
  {k:'patrol',    o:'clear',   f:'hol'},     // 17  Verschnaufen
  {k:'minefield', o:'protect', f:'hol'},     // 18  Sicht, Naehe
  {k:'siege',     o:'clear',   f:'shivan'},  // 19  Heavy Bomber
  {k:'convoy',    o:'transit', f:'shivan'}   // 20  Platzhalter: wird mit
                                             //     v83 die vasudanische
                                             //     Bosskomposition
];
const SEQ_LEN = WAVE_SEQ.length;

// ── BOSSFENSTER ──────────────────────────────────────────────
// Alle elf Wellen ein Boss ist ein Kalender, kein Ereignis. Der Abstand
// wird stattdessen gewuerfelt: irgendwo zwischen 12 und 18 Wellen nach dem
// letzten. Auf 100 Wellen sind das rund sechs Bosse.
const BOSS_GAP_MIN = 12, BOSS_GAP_MAX = 18;
let lastBossWave = 0, nextBossWave = 0;
function rollNextBoss(from){
  nextBossWave = from + BOSS_GAP_MIN
               + ((Math.random()*(BOSS_GAP_MAX-BOSS_GAP_MIN+1))|0);
}

// Fraktion. Der Hammer of Light kommt mit v83; bis dahin faellt er auf die
// NTF zurueck, damit die Folge schon in ihrer endgueltigen Form dasteht.
function factionOf(f){ return f; }      // hol ist ab v88 eine eigene Fraktion

// Ab Welle 21 gewuerfelt. Eine Komposition und ein Auftrag, die beide zur
// Matrix passen und nicht die der Vorwelle sind.
let lastK = '', lastO = '';
function rollWave(n){
  const bossDue = (n >= nextBossWave);
  if(bossDue){ lastBossWave = n; rollNextBoss(n); return {k:'bosswave', o:'boss'}; }
  const objs = Object.keys(OBJ).filter(function(o){ return o!=='boss' && o!==lastO; });
  for(let tries=0; tries<40; tries++){
    const o = objs[(Math.random()*objs.length)|0];
    const ks = OBJ_OK[o].filter(function(k){ return k!=='bosswave' && k!==lastK; });
    if(!ks.length) continue;
    return {k: ks[(Math.random()*ks.length)|0], o: o};
  }
  return {k:'patrol', o:'clear'};      // Rueckfall, darf nie gebraucht werden
}



// ── HAMMER OF LIGHT ──────────────────────────────────────────
// Zwoelf der dreissig geschriebenen Missionen. Die uebrigen achtzehn
// brauchen Klassen oder Verhalten, die noch nicht gebaut sind:
// Installationen, Frachter mit Ladung, Andocken, Kollisionsangriffe,
// Zielvorliebe, nach rechts entkommende Gegner, Zustand ueber Wellen.
//
// Einheit: {id, c:Kategorie, n:Anzahl (bei fi/bo Staffeln), spr:Rumpf,
//           side:'ally', t:Sekunde, x, y, hp:Faktor, wait:true}
// wait heisst: kommt nur, wenn ein Ereignis es einwarpen laesst.
const SCRIPT_WAVES = {
  1: {name:'Erstkontakt', fac:'hol', o:'clear', live:4, u:[
       {id:'E1', c:'fi', n:3}
     ]},

  2: {name:'Geschuetzstellung', fac:'hol', o:'clear', live:4, u:[
       {id:'G1', c:'sg', n:6, spr:'sgankh'},
       {id:'E1', c:'fi', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'G1', w:'einwarpen', a2:'E1'}
     ]},

  3: {name:'Nachschub', fac:'hol', o:'clear', live:4, u:[
       {id:'E1', c:'fi', n:2},
       {id:'K1', c:'cr', n:1, spr:'craten', wait:true},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'K1'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'K1', w:'nachschub', a2:'aus'}
     ]},

  6: {name:'Begegnung', fac:'hol', o:'guard', live:5, u:[
       {id:'A1', c:'co', n:1, spr:'cosobek', side:'ally'},
       {id:'V1', c:'co', n:1, spr:'cosobek'},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'V1', w:'nachschub', a2:'aus'}
     ]},

  7: {name:'Der Angriff', fac:'hol', o:'guard', live:5, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally'},
       {id:'V1', c:'de', n:1, spr:'detyphon'},
       {id:'E1', c:'fi', n:1},
       {id:'B1', c:'bo', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'subsystem', a:'V1', b:'communication', w:'nachschub', a2:'aus'},
       {t:'zerstoert', a:'V1', w:'nachschub', a2:'aus'}
     ]},

  8: {name:'Der Rueckzug', fac:'hol', o:'guard', live:4, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.88},
       {id:'B1', c:'bo', n:2},
       {id:'B2', c:'bo', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'B2'}
     ]},

  13:{name:'Die Transporter', fac:'hol', o:'protect', live:4, hunt:'T1', stillRocks:true, u:[
       {id:'T1', c:'tr', n:2, spr:'trisis', side:'ally', cross:0.42, x:-40},
       {id:'R1', c:'ast', n:26},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}
     ]},

  14:{name:'Die Tarnung', fac:'hol', o:'clear', live:5, u:[
       {id:'A1', c:'fi', n:2, side:'ally'},
       {id:'E1', c:'fi', n:3}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'meldung', a2:'turning hostile'},
       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A1'}
     ]},

  15:{name:'Der Vorratsspeicher', fac:'hol', o:'clear', live:4, stillRocks:true, u:[
       {id:'C1', c:'fc', n:5, spr:'fcvc3'},
       {id:'G1', c:'sg', n:3, spr:'sgankh'},
       {id:'R1', c:'ast', n:34},
       {id:'E1', c:'fi', n:2, wait:true}
     ], ev:[
       {t:'anzahlUnter', a:'C1', b:3, w:'einwarpen', a2:'E1'}
     ]},

  16:{name:'Die Meuterei', fac:'hol', o:'guard', live:5, u:[
       {id:'A1', c:'cr', n:1, spr:'craten', side:'ally'},
       {id:'A2', c:'fi', n:2, side:'ally'},
       {id:'E1', c:'fi', n:3},
       {id:'E2', c:'fi', n:3, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'meldung', a2:'escort turning hostile'},
       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A2'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'A2', w:'nachschub', a2:'aus'}
     ]},

  4: {name:'Der Ausbrecher', fac:'hol', o:'clear', live:5, u:[
       // Sie ist angeschlagen und faehrt nach rechts. Wer sie ziehen
       // laesst, verliert Punkte - das ist die ganze Uhr dieser Welle.
       {id:'V1', c:'co', n:1, spr:'cosobek', hp:0.55, escape:0.30, x:-40},
       {id:'E1', c:'fi', n:2}
     ]},

  25:{name:'Die Flucht', fac:'hol', o:'clear', live:5, u:[
       {id:'F1', c:'fr', n:2, spr:'frbast', escape:0.55, x:-40},
       {id:'T1', c:'tr', n:1, spr:'trisis', escape:0.62, x:-40},
       {id:'E1', c:'fi', n:2}
     ], ev:[
       {t:'sek', a:2, w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'F1', w:'nachschub', a2:'aus'}
     ]},

  5: {name:'Durch den Guertel', fac:'hol', o:'guard', live:4,
      stillRocks:true, crossEnds:true, u:[
       {id:'A1', c:'co', n:1, spr:'codeimos', side:'ally', crossSecs:55},
       {id:'R1', c:'ast', n:30},
       {id:'G1', c:'sg', n:5, spr:'sgankh'},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'G1', w:'einwarpen', a2:'E2'},
       {t:'alleZerstoert', a:'G1', w:'nachschub', a2:'an'},
       {t:'verlaesst',     a:'A1', w:'nachschub', a2:'aus'}
     ]},

  12:{name:'Die Fracht', fac:'hol', o:'scan', live:5, hunt:'C1', u:[
       {id:'C1', c:'fc', n:4, spr:'fcvc3', scan:true},
       {id:'E1', c:'fi', n:2, wait:true}
     ], ev:[
       // Solange Container stehen, kommt Nachschub. Wer schnell raeumt,
       // hat weniger zu tun - wer zoegert, bekommt mehr.
       {t:'erfuellt',     a:'',   w:'einwarpen', a2:'E1'},
       {t:'erfuellt',     a:'',   w:'nachschub', a2:'an'},
       {t:'erfuellt',     a:'',   w:'auftrag',   a2:'protect'},
       {t:'alleZerstoert',a:'C1', w:'nachschub', a2:'aus'}
     ]},

  17:{name:'Die Tsunami', fac:'hol', o:'clear', live:6, u:[
       {id:'K1', c:'cr', n:1, spr:'craten'},
       {id:'K2', c:'cr', n:1, spr:'crmentu'},
       // n counts wings, not ships: one wing is WING_MIN..WING_MAX
       // fighters, so three wings of three or four is what arrives.
       {id:'E1', c:'fi', n:1},
       {id:'E2', c:'fi', n:1, wait:true},
       {id:'E3', c:'fi', n:1, wait:true},
       {id:'A1', c:'de', n:1, spr:'detyphon', side:'ally', wait:true}
      ], ev:[
        // Three wings, each one called in by the last one falling. Nothing
        // here hangs on the clock.
        {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
        {t:'alleZerstoert', a:'E2', w:'einwarpen', a2:'E3'},
        // The Typhon arrives last, and she is the hangar: only with a
        // Vasudan destroyer on the field can the player take a bomber, and
        // only a bomber cracks the two cruisers in reasonable time.
        {t:'alleZerstoert', a:'E3', w:'einwarpen', a2:'A1'},
        {t:'alleZerstoert', a:'E3', w:'meldung',   a2:'GVD Typhon inbound - hangar open'}
      ]},

  18:{name:'Tenderizer', fac:'hol', o:'guard', live:6,
      ev:[{t:'alleZerstoert', a:'K1', w:'einwarpen', a2:'K2'},
          {t:'alleZerstoert', a:'K1', w:'nachschub', a2:'an'},
          {t:'alleZerstoert', a:'K2', w:'nachschub', a2:'aus'}], u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:1.35},
       {id:'K1', c:'fi', n:3, ram:true},
       {id:'K2', c:'fi', n:3, wait:true, ram:true}
     ]},

  26:{name:'Das Minenfeld', fac:'hol', o:'guard', live:4,
      stillRocks:true, crossEnds:true, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', crossSecs:70, hp:1.5},
       {id:'R1', c:'ast', n:40},
       {id:'G1', c:'sg', n:9, spr:'sgankh'},
       {id:'E1', c:'fi', n:3}
     ], ev:[
       {t:'sek', a:3, w:'nachschub', a2:'an'},
       {t:'verlaesst', a:'A1', w:'nachschub', a2:'aus'}
     ]},

  10:{name:'Die Werft', fac:'hol', o:'guard', live:5, u:[
       // Die Arcadia ist ein Ort, kein Gegner: unverwundbar und zu zwei
       // Dritteln ausserhalb des rechten Randes.
       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.36},
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.80},
       {id:'B1', c:'bo', n:2},
       {id:'E1', c:'fi', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'E1'},
       {t:'alleZerstoert', a:'B1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'aus'}
     ]},

  11:{name:'Der Sturm', fac:'hol', o:'guard', live:5, keepSky:true, u:[
       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.36},
       {id:'V1', c:'de', n:1, spr:'detyphon'},
       {id:'A1', c:'cr', n:1, spr:'craten', side:'ally'},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'zerstoert', a:'V1', w:'ende', a2:''}
     ]},

  19:{name:'Der Tempel', fac:'hol', o:'clear', live:5, u:[
       // Hier ist die Installation das Ziel, also verwundbar.
       {id:'S1', c:'in', n:1, spr:'inarcadia', hp:2.2, x:560},
       {id:'G1', c:'sg', n:8, spr:'sgankh'},
       {id:'E1', c:'fi', n:3},
       {id:'E2', c:'fi', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'rumpfUnter', a:'S1', b:50, w:'nachschub', a2:'an'},
       {t:'zerstoert', a:'S1', w:'nachschub', a2:'aus'}
     ]},

  22:{name:'Der Fluechtling', fac:'hol', o:'clear', live:5, u:[
       // Er faehrt nach rechts und du kommst nicht an ihn heran, solange
       // die Geschuetze stehen. Genau das ist die Mission.
       {id:'V1', c:'de', n:1, spr:'detyphon', escape:0.22, x:-60},
       {id:'G1', c:'sg', n:8, spr:'sgankh'},
       {id:'E1', c:'fi', n:2}
     ]},

  20:{name:'Die Ueberlebenden', fac:'hol', o:'clear', live:6, hunt:'K1', u:[
       // Er steht brennend im Feld und wird bereits beschossen. Zu retten
       // ist er nicht: solange er lebt, kommt Nachschub, und jeder frueh
       // getoetete Jaeger verlaengert nur sein Leben - und damit die Zahl
       // der Kapseln, die es herausschaffen.
       {id:'K1', c:'cr', n:1, spr:'craten', side:'ally', hp:0.22},
       {id:'E1', c:'fi', n:2},
       {id:'P1', c:'ep', n:4, spr:'epra', side:'ally', cross:0.34, wait:true, at:'K1'}
     ], ev:[
       {t:'sek', a:1, w:'nachschub', a2:'an'},
       {t:'zerstoert', a:'K1', w:'nachschub', a2:'aus'},
       {t:'zerstoert', a:'K1', w:'einwarpen', a2:'P1'},
       {t:'zerstoert', a:'K1', w:'meldung', a2:'escape pods away'},
       {t:'zerstoert', a:'K1', w:'auftrag', a2:'protect'},
       {t:'zerstoert', a:'K1', w:'jagd', a2:'P1'}
     ]},

  24:{name:'Der Hinterhalt', fac:'hol', o:'clear', live:6, u:[
       {id:'A1', c:'fi', n:2, side:'ally'},
       {id:'E1', c:'fi', n:3},
       {id:'V1', c:'cr', n:2, spr:'craten', wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'meldung', a2:'escort turning hostile'},
       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A1'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'V1'}
     ]},

  28:{name:'Der Rammstoss', fac:'hol', o:'guard', live:5, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:1.1, still:true},
       {id:'V1', c:'cr', n:1, spr:'crmentu', capRam:0.9, still:true},
       {id:'E1', c:'fi', n:2}
     ], ev:[
       {t:'sek', a:2, w:'meldung', a2:'cruiser on ramming course'}
     ]},

  30:{name:'Der Boss', fac:'hol', o:'clear', live:6, u:[
       // Die Hatshepsut, die du vier Wellen lang beschuetzt hast, steht
       // mit im Feld. Faellt eines der beiden feindlichen Schiffe, kommt
       // die dritte - erst dann ist Platz fuer sie.
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.9},
       {id:'V1', c:'de', n:1, spr:'detyphon'},
       {id:'V2', c:'cr', n:1, spr:'craten'},   // nur sie darf fliehen
       {id:'V3', c:'de', n:1, spr:'dehatshepsut', wait:true},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:2, wait:true}
     ], ev:[
       {t:'zerstoert', a:'V2', w:'einwarpen', a2:'V3'},
       {t:'zerstoert', a:'V1', w:'einwarpen', a2:'V3'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'zerstoert', a:'V3', w:'nachschub', a2:'aus'}
     ]},

  9: {name:'Der Konvoi', fac:'hol', o:'protect', live:6, hunt:'F1', u:[
       // Aten und zwei Frachter queren gemeinsam. Die Container haengen
       // an den Frachtern, sobald sie angedockt haben.
       {id:'A1', c:'cr', n:1, spr:'craten', side:'ally', crossSecs:75},
       {id:'C1', c:'fc', n:2, spr:'fcvc3', side:'ally', x:120},
       {id:'F1', c:'fr', n:2, spr:'frbast', side:'ally', cross:0.38, x:-40,
        dockTo:'C1'},
       {id:'E1', c:'fi', n:3}
     ], ev:[
       {t:'sek', a:2, w:'nachschub', a2:'an'},
       {t:'verlaesst', a:'A1', w:'nachschub', a2:'aus'}
     ]},

  23:{name:'Die Abholung', fac:'hol', o:'scan', live:6, hunt:'C1', u:[
       {id:'C1', c:'fc', n:3, spr:'fcvc3', scan:true, x:200},
       {id:'E1', c:'fi', n:2},
       {id:'F1', c:'fr', n:2, spr:'frbast', side:'ally', cross:0.34, x:-40,
        dockTo:'C1', wait:true}
     ], ev:[
       {t:'erfuellt', a:'', w:'einwarpen', a2:'F1'},
       {t:'erfuellt', a:'', w:'meldung',   a2:'freighters inbound'},
       {t:'erfuellt', a:'', w:'auftrag',   a2:'protect'},
       {t:'erfuellt', a:'', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'F1', w:'nachschub', a2:'aus'}
     ]},

  27:{name:'Die Reparatur', fac:'hol', o:'guard', live:6, u:[
       // Jeder angedockte Transporter setzt den Rumpf ein Viertel hoch.
       // Wer schlecht verteidigt, wartet laenger - das ist die Uhr.
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.30, still:true},
       {id:'T1', c:'tr', n:1, spr:'trisis', side:'ally', x:-40, dockTo:'A1'},
       {id:'T2', c:'tr', n:1, spr:'trisis', side:'ally', x:-40, dockTo:'A1', wait:true},
       {id:'T3', c:'tr', n:1, spr:'trisis', side:'ally', x:-40, dockTo:'A1', wait:true},
       {id:'B1', c:'bo', n:2},
       {id:'B2', c:'bo', n:2, wait:true}
     ], ev:[
       {t:'angedockt', a:'T1', w:'heilen', a2:'A1'},
       {t:'angedockt', a:'T1', w:'einwarpen', a2:'T2'},
       {t:'angedockt', a:'T2', w:'heilen', a2:'A1'},
       {t:'angedockt', a:'T2', w:'einwarpen', a2:'T3'},
       {t:'angedockt', a:'T3', w:'heilen', a2:'A1'},
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'B2'},
       {t:'sek', a:3, w:'nachschub', a2:'an'},
       {t:'angedockt', a:'T3', w:'nachschub', a2:'aus'}
     ]},

  21:{name:'Die Sperre', fac:'hol', o:'clear', live:4, u:[
       {id:'K1', c:'cr', n:3, spr:'craten', lanes:true},
       {id:'E1', c:'fi', n:2}
     ]},

  29:{name:'Die Blockade', fac:'hol', o:'guard', live:5, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:1.1},
       {id:'V1', c:'co', n:2, spr:'cosobek', hp:0.7},
       {id:'E1', c:'fi', n:2}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'V1', w:'nachschub', a2:'aus'}
     ]},

  // ── NTF CYCLE ─────────────────────────────────────────────
  // Waves 31 to 60. The player flies Terran hulls from here on, see
  // CYCLES. The thread through the cycle is the Iceni: 36, 47 and 60.

  31:{name:'Der Aufstand', fac:'ntf', o:'clear', live:4, u:[
       // A patrol with a Leviathan. When the first NTF wing is down, she
       // goes over - as the NTF hull - and has to be taken down as well.
       // Until then she cannot die: the turn is the point of the mission.
       // After the turn she runs for the right edge and jumps out there.
       {id:'A1', c:'cr', n:1, spr:'crleviathan', side:'ally', defectRun:0.25},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'meldung', a2:'GTC Leviathan turning hostile'},
       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A1'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}
     ]},

  32:{name:'Die Frachtroute', fac:'ntf', o:'protect', live:5, hunt:'F1', u:[
       // Two Poseidons cross. Medusa bombers go for them, with fighters
       // along to keep the player busy.
       {id:'F1', c:'fr', n:2, spr:'frposeidon', side:'ally', cross:0.40, x:-40},
       {id:'B1', c:'bo', n:1, spr:'bomedusa'},
       {id:'E1', c:'fi', n:1},
       {id:'B2', c:'bo', n:1, spr:'bomedusa', wait:true},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'B2'},
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'E2'}
     ]},

  33:{name:'Die Relaisstation', fac:'ntf', o:'clear', live:5,
      ziel:'DESTROY THE FAUSTUS RELAY', u:[
       // A Faustus parked as a relay. While she stands, wings keep coming.
       // Weak hull, few guns, no flak - and a big blast when she goes.
       {id:'S1', c:'cr', n:1, spr:'scfaustus', still:true, x:560, y:250,
        hp:0.6, noFlak:true},
       {id:'G1', c:'sg', n:4, spr:'sgcerberus'},
       {id:'E1', c:'fi', n:1}
     ], ev:[
       {t:'sek', a:1, w:'nachschub', a2:'an'},
       {t:'zerstoert', a:'S1', w:'nachschub', a2:'aus'},
       {t:'vernichtet', a:'S1', w:'zielerfuellt', a2:'RELAY DESTROYED'}
     ]},

  34:{name:'Die Flakwand', fac:'ntf', o:'clear', live:5, u:[
       // Two NTF Aeolus throwing flak. Once the first wing is down an
       // Orion arrives, and with her the hangar: a bomber is the answer.
       {id:'K1', c:'cr', n:2, spr:'ntfcraeolus'},
       {id:'E1', c:'fi', n:1},
       {id:'E2', c:'fi', n:1, wait:true},
       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'A1'},
       {t:'alleZerstoert', a:'E1', w:'meldung',   a2:'GTD Orion inbound - hangar open'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}
     ]},

  35:{name:'Der Ueberlaeufer', fac:'ntf', o:'guard', live:5, hunt:'A1',
      crossEnds:true, u:[
       // An NTF Deimos coming over to the GTVA, still in NTF markings.
       // She crosses right to left, away from the NTF side, and her own
       // side keeps coming until she is across. When she jumps, the
       // fight is over: nothing still queued arrives.
       // Half again her hull: with her own side coming the whole way,
       // the standard one did not last the crossing.
       {id:'A1', c:'co', n:1, spr:'ntfcodeimos', side:'ally', crossSecs:55,
        crossDir:'left', hp:1.5},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, spr:'boartemis', wait:true},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       // The first wing hunts her; what follows is a screen for the
       // player to cut through. All of it diving on her was too much.
       {t:'alleZerstoert', a:'E1', w:'jagd', a2:''},
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'E2'},
       {t:'verlaesst', a:'A1', w:'ende', a2:''}
     ]},

  36:{name:'Die Iceni', fac:'ntf', o:'clear', live:5, u:[
       // First meeting. She cannot be had yet: a short deadline and no
       // navigation subsystem to stop the jump. Her getting away costs
       // nothing - but she comes back heavier, as she always does.
       {id:'V1', c:'ic', n:1, flee:25, navProof:true, fleeFree:true},
       {id:'K1', c:'cr', n:1, spr:'ntfcrfenris'},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}
     ]},

  37:{name:'Die Unsichtbaren', fac:'ntf', o:'clear', live:5, u:[
       // Lokis, and more than one lot of them. No missile holds one, so
       // this is a gun fight - they are in plain sight all the same.
       {id:'E1', c:'fi', n:2, spr:'filoki'},
       {id:'E2', c:'fi', n:2, spr:'filoki', wait:true},
       {id:'E3', c:'fi', n:2, spr:'filoki', wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'alleZerstoert', a:'E2', w:'einwarpen', a2:'E3'}
     ]},

  38:{name:'Die Kaperung', fac:'ntf', o:'clear', live:5,
      ziel:'DISABLE THE DEIMOS - ENGINES AND WEAPONS', u:[
       // An NTF Deimos makes for the right edge and jumps there. With
       // her engines AND her weapons down an Elysium comes to take her -
       // with her guns still up it would not live to dock. She keeps a
       // fixed height mid-field, so both subsystems can be reached.
       // Until the Elysium is lost she cannot be destroyed.
       {id:'D1', c:'co', n:1, spr:'ntfcodeimos', x:-60, y:260, escape:0.22,
        escWarp:true, capture:true},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:1, wait:true},
       {id:'T1', c:'tr', n:1, spr:'trelysium', side:'ally', x:-40,
        dockTo:'D1', dockHold:6, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'subsystem', a:'D1', b:'engines+weapons', w:'einwarpen', a2:'T1'},
       {t:'subsystem', a:'D1', b:'engines+weapons', w:'ziel', a2:'COVER THE ELYSIUM'},
       {t:'angedockt', a:'T1', w:'kapern', a2:'D1'},
       {t:'angedockt', a:'T1', w:'zielerfuellt', a2:'DEIMOS CAPTURED'},
       {t:'vernichtet', a:'T1', w:'freigeben', a2:'D1'},
       {t:'vernichtet', a:'T1', w:'zielverfehlt', a2:'ELYSIUM LOST'},
       {t:'verlaesst', a:'D1', w:'zielverfehlt', a2:'THE DEIMOS GOT AWAY'}
     ]},

  39:{name:'Die Gasernte', fac:'ntf', o:'clear', live:5, mod:'nebula', u:[
       // In a gas giant's haze. Three miners run for the right edge under
       // a Fenris. A miner goes up with a very big blast (BIG_BLAST) -
       // it takes the NTF fighters near it along, and the player too.
       // One after the other: a ship placed far off the left edge is
       // cleared away as lost, so they start at the edge, seconds apart.
       {id:'M1', c:'fr', n:1, spr:'gmzephyrus', escape:0.30, x:-60, y:170},
       {id:'M2', c:'fr', n:1, spr:'gmzephyrus', escape:0.30, x:-60, y:300, t:7},
       {id:'M3', c:'fr', n:1, spr:'gmzephyrus', escape:0.30, x:-60, y:420, t:14},
       {id:'K1', c:'cr', n:1, spr:'ntfcrfenris'},
       {id:'E1', c:'fi', n:1},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}
     ]},

  40:{name:'Der Sensorsturm', fac:'ntf', o:'guard', live:5, mod:'emp', u:[
       // An EMP storm, which is a nebula phenomenon: haze, and now and
       // then no lock for anybody. Three rounds of Hercules Mk II and
       // Ursa go for an Orion, with reinforcements until the last
       // bombers are down.
       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', hp:1.2},
       {id:'E1', c:'fi', n:2, spr:'fihercmk2'},
       {id:'B1', c:'bo', n:1, spr:'boursa', wait:true},
       {id:'E2', c:'fi', n:2, spr:'fihercmk2', wait:true},
       {id:'B2', c:'bo', n:1, spr:'boursa', wait:true},
       {id:'E3', c:'fi', n:2, spr:'fihercmk2', wait:true},
       {id:'B3', c:'bo', n:2, spr:'boursa', wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'B2'},
       {t:'alleZerstoert', a:'E2', w:'einwarpen', a2:'E3'},
       {t:'alleZerstoert', a:'B2', w:'einwarpen', a2:'B3'},
       {t:'alleZerstoert', a:'B3', w:'nachschub', a2:'aus'}
     ]},

  41:{name:'Das Lazarett', fac:'ntf', o:'protect', live:5, hunt:'H1', u:[
       // The Hippocrates crosses slowly, and her hull is weak. Medusa
       // and Ursa bombers go for her: the bombs have to be shot down.
       {id:'H1', c:'fr', n:1, spr:'mehippocrates', side:'ally', cross:0.25, x:-80},
       {id:'B1', c:'bo', n:1, spr:'bomedusa'},
       {id:'E1', c:'fi', n:1},
       {id:'B2', c:'bo', n:1, spr:'boursa', wait:true},
       {id:'B3', c:'bo', n:1, spr:'bomedusa', wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'B2'},
       {t:'alleZerstoert', a:'B2', w:'einwarpen', a2:'B3'}
     ]},

  42:{name:'Die Hecate', fac:'ntf', o:'guard', live:5,
      ziel:'DISABLE HECATE WEAPONS', u:[
       // An NTF Hecate against an Orion. Her beams would win that, so her
       // weapons subsystem comes first. Disarmed, she withdraws after the
       // usual deadline unless she is finished before.
       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', hp:1.2},
       {id:'V1', c:'de', n:1, spr:'ntfdehecate'},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, spr:'bomedusa', wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'subsystem', a:'V1', b:'weapons', w:'ziel', a2:'DESTROY THE HECATE'},
       {t:'vernichtet', a:'V1', w:'zielerfuellt', a2:'HECATE DESTROYED'},
       {t:'verlaesst', a:'V1', w:'zielverfehlt', a2:'THE HECATE WITHDREW'},
       {t:'zerstoert', a:'V1', w:'nachschub', a2:'aus'}
     ]},

  43:{name:'Der NTF-Konvoi', fac:'ntf', o:'scan', live:5, scanUnderFire:true,
      ziel:'SCAN THE TRITONS', u:[
       // Three Tritons run for the right edge. They are to be scanned
       // before anything else - until then they cannot be destroyed -
       // and then the convoy is to be stopped for good.
       {id:'T1', c:'fr', n:3, spr:'frtriton', escape:0.18, x:-60, scan:true,
        scanFirst:true},
       // One escort wing, one more once it is down. Being hit does not
       // stop the scan here (scanUnderFire), staying close does.
       {id:'E1', c:'fi', n:1},
       {id:'E2', c:'fi', n:1, wait:true},
       // The convoy calls for help once it knows it has been scanned.
       {id:'K1', c:'cr', n:1, spr:'ntfcraeolus', wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'gescannt', a:'T1', w:'einwarpen', a2:'K1'},
       {t:'gescannt', a:'T1', w:'ziel', a2:'DESTROY THE CONVOY'},
       {t:'vernichtet', a:'T1', w:'zielerfuellt', a2:'CONVOY DESTROYED'},
       {t:'verlaesst', a:'T1', w:'zielverfehlt', a2:'A TRITON GOT AWAY'}
     ]},

  44:{name:'Der Schwarm', fac:'ntf', o:'clear', live:7, u:[
       // Wing after wing - the Tornado's hour. A Deimos to rearm at; one
       // allied wing arrives once the first enemy wing is down.
       // The Deimos launches no wings of her own here (noWings).
       {id:'A1', c:'co', n:1, spr:'codeimos', side:'ally', still:true, hp:1.3,
        noWings:true},
       {id:'W2', c:'fi', n:1, side:'ally', wait:true},
       {id:'E1', c:'fi', n:3},
       {id:'E2', c:'fi', n:3, wait:true},
       {id:'E3', c:'fi', n:3, wait:true},
       {id:'B1', c:'bo', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'W2'},
       {t:'alleZerstoert', a:'E2', w:'einwarpen', a2:'E3'},
       {t:'alleZerstoert', a:'E2', w:'einwarpen', a2:'B1'}
     ]},

  45:{name:'Das Nadeloehr', fac:'ntf', o:'guard', live:5, crossEnds:true,
      noRocks:true,
      ziel:'GET THE ORION THROUGH', u:[
       // Three NTF Fenris hold the line, each in her own lane and
       // holding it. An Orion has to cross the field through them.
       {id:'K1', c:'cr', n:1, spr:'ntfcrfenris', y:150, still:true},
       {id:'K2', c:'cr', n:1, spr:'ntfcrfenris', y:265, still:true},
       {id:'K3', c:'cr', n:1, spr:'ntfcrfenris', y:380, still:true},
       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', crossSecs:70, hp:1.2},
       {id:'E1', c:'fi', n:2}
     ], ev:[
       {t:'sek', a:3, w:'nachschub', a2:'an'},
       {t:'verlaesst', a:'A1', w:'zielerfuellt', a2:'THE ORION IS THROUGH'},
       {t:'verlaesst', a:'A1', w:'ende', a2:''},
       {t:'vernichtet', a:'A1', w:'zielverfehlt', a2:'ORION LOST'},
       {t:'vernichtet', a:'A1', w:'ende', a2:''}
     ]},

  46:{name:'Die Wissenschaftler', fac:'ntf', o:'clear', live:5,
      ziel:'DISABLE THE FAUSTUS - NAVIGATION AND WEAPONS', u:[
       // A Faustus parked under guard. She jumps when her deadline runs
       // out - unless her navigation is gone. With navigation and weapons
       // down an Argo comes to take her; until the Argo is lost she
       // cannot be destroyed.
       {id:'F1', c:'cr', n:1, spr:'scfaustus', still:true, x:560, y:250,
        noFlak:true, capture:true, flee:60},
       {id:'K1', c:'cr', n:1, spr:'ntfcraeolus'},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:1, wait:true},
       {id:'T1', c:'tr', n:1, spr:'trargo', side:'ally', x:-40,
        dockTo:'F1', dockHold:6, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'subsystem', a:'F1', b:'navigation+weapons', w:'einwarpen', a2:'T1'},
       {t:'subsystem', a:'F1', b:'navigation+weapons', w:'ziel', a2:'COVER THE ARGO'},
       {t:'angedockt', a:'T1', w:'kapern', a2:'F1'},
       {t:'angedockt', a:'T1', w:'zielerfuellt', a2:'FAUSTUS CAPTURED'},
       {t:'vernichtet', a:'T1', w:'freigeben', a2:'F1'},
       {t:'vernichtet', a:'T1', w:'zielverfehlt', a2:'ARGO LOST'},
       {t:'verlaesst', a:'F1', w:'zielverfehlt', a2:'THE FAUSTUS GOT AWAY'}
     ]},

  47:{name:'Die zweite Flucht', fac:'ntf', o:'clear', live:6,
      ziel:'DESTROY THE HECATE', u:[
       // A forlorn hope, and nobody on the player's side. The Iceni gets
       // away - forty seconds, and no navigation to shoot - and comes
       // back heavier for it. The Hecate does not have to. Both hold
       // their height: two capitals this size have no room to drift.
       // A fixed run of wings, no endless reinforcement.
       {id:'V1', c:'ic', n:1, flee:40, navProof:true, fleeFree:true,
        still:true, y:150},
       {id:'V2', c:'de', n:1, spr:'ntfdehecate', still:true, y:350, hp:0.8},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, wait:true},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'E2'},
       {t:'vernichtet', a:'V2', w:'zielerfuellt', a2:'HECATE DESTROYED'},
       {t:'verlaesst', a:'V2', w:'zielverfehlt', a2:'THE HECATE WITHDREW'}
     ]},

  48:{name:'Die Aufklaerung', fac:'ntf', o:'clear', live:4, ship:'fipegasus',
      ziel:'SCAN THE NTD ORION - ALL FIVE SUBSYSTEMS', u:[
       // The player flies a Pegasus for this one. Nothing can lock her -
       // not the beams, not the missiles, not the destroyer's guns - but
       // the fighters see her. Each subsystem of the Orion has to be
       // held close until its ring fills. Then the Orion leaves.
       {id:'V1', c:'de', n:1, spr:'ntfdeorion', still:true, x:520, y:260, scanSubs:true,
        fleeFree:true},
       {id:'E1', c:'fi', n:1},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'gescannt', a:'V1', w:'zielerfuellt', a2:'ORION SCANNED'},
       {t:'gescannt', a:'V1', w:'raus', a2:'V1'}
     ]},

  49:{name:'Das Reparaturdock', fac:'ntf', o:'clear', live:5,
      ziel:'DESTROY THE DEIMOS BEFORE HER REPAIRS ARE DONE', u:[
       // In front of the Arcadia the NTF patches up a Deimos. Three
       // transports come one after another; each that docks puts a
       // quarter of her hull back. Whole again, or once the last one
       // has docked, she jumps.
       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.36},
       {id:'D1', c:'co', n:1, spr:'ntfcodeimos', still:true, x:420, y:250,
        hp:1.8, hurt:0.25, noFlee:true},
       {id:'T1', c:'tr', n:1, spr:'trargo', t:4,  x:860, y:120, dockTo:'D1', dockHold:4},
       {id:'T2', c:'tr', n:1, spr:'trargo', t:24, x:860, y:400, dockTo:'D1', dockHold:4},
       {id:'T3', c:'tr', n:1, spr:'trargo', t:44, x:860, y:140, dockTo:'D1', dockHold:4},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'angedockt', a:'T1', w:'heilen', a2:'D1'},
       {t:'angedockt', a:'T2', w:'heilen', a2:'D1'},
       {t:'angedockt', a:'T3', w:'heilen', a2:'D1'},
       // After the last transport she goes, whole or not.
       {t:'angedockt', a:'T3', w:'raus', a2:'D1'},
       {t:'vernichtet', a:'D1', w:'zielerfuellt', a2:'DEIMOS DESTROYED'},
       {t:'vernichtet', a:'D1', w:'ende', a2:''},
       {t:'verlaesst', a:'D1', w:'zielverfehlt', a2:'THE DEIMOS WAS REPAIRED'},
       {t:'verlaesst', a:'D1', w:'ende', a2:''}
     ]},

  50:{name:'Der Durchbruch', fac:'ntf', o:'guard', live:5, crossEnds:true,
      noRocks:true, ziel:'BREAK THE BLOCKADE - DESTROY AN AEOLUS', u:[
       // Two Aeolus and a line of sentry guns hold the field. Once one
       // Aeolus is down, an Orion comes through the gap and has to get
       // across.
       {id:'K1', c:'cr', n:2, spr:'ntfcraeolus', still:true, x:600},
       {id:'G1', c:'sg', n:4, spr:'sgcerberus', x:500},
       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', crossSecs:60, hp:1.2,
        wait:true},
       {id:'E1', c:'fi', n:2}
     ], ev:[
       {t:'sek', a:4, w:'nachschub', a2:'an'},
       {t:'anzahlUnter', a:'K1', b:2, w:'einwarpen', a2:'A1'},
       {t:'anzahlUnter', a:'K1', b:2, w:'ziel', a2:'GET THE ORION THROUGH'},
       {t:'verlaesst', a:'A1', w:'zielerfuellt', a2:'THE ORION IS THROUGH'},
       {t:'verlaesst', a:'A1', w:'ende', a2:''},
       {t:'vernichtet', a:'A1', w:'zielverfehlt', a2:'ORION LOST'},
       {t:'vernichtet', a:'A1', w:'ende', a2:''}
     ]},

  51:{name:'Die Rueckeroberung', fac:'ntf', o:'clear', live:5,
      ziel:'TAKE OUT THE WEAPONS OF THE ARCADIA', u:[
       // The NTF holds the Arcadia and her guns hold the field. With the
       // guns shot out an Elysium comes and boards her; until then she
       // cannot be destroyed. Lose the Elysium and a second one comes,
       // lose both and the NTF keeps her.
       {id:'S1', c:'in', n:1, spr:'inarcadia', x:600, capture:true, armed:true},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:1, wait:true},
       {id:'B1', c:'bo', n:1, wait:true},
       {id:'T1', c:'tr', n:1, spr:'trelysium', side:'ally', x:-40, y:260,
        dockTo:'S1', dockHold:8, wait:true},
       {id:'T2', c:'tr', n:1, spr:'trelysium', side:'ally', x:-40, y:260,
        dockTo:'S1', dockHold:8, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'subsystem', a:'S1', b:'weapons', w:'einwarpen', a2:'T1'},
       {t:'subsystem', a:'S1', b:'weapons', w:'einwarpen', a2:'B1'},
       {t:'subsystem', a:'S1', b:'weapons', w:'ziel', a2:'COVER THE ELYSIUM'},
       {t:'angedockt', a:'T1', w:'kapern', a2:'S1'},
       {t:'angedockt', a:'T1', w:'zielerfuellt', a2:'ARCADIA RETAKEN'},
       {t:'vernichtet', a:'T1', w:'einwarpen', a2:'T2'},
       {t:'vernichtet', a:'T1', w:'meldung', a2:'second elysium inbound'},
       {t:'angedockt', a:'T2', w:'kapern', a2:'S1'},
       {t:'angedockt', a:'T2', w:'zielerfuellt', a2:'ARCADIA RETAKEN'},
       {t:'vernichtet', a:'T2', w:'kulisse', a2:'S1'},
       {t:'vernichtet', a:'T2', w:'zielverfehlt', a2:'BOTH ELYSIUMS LOST'}
     ]},

  52:{name:'Das Artilleriefeuer', fac:'ntf', o:'clear', live:5,
      ziel:'STOP THE NTF SHIPS BEFORE THEY JUMP', u:[
       // A GTVA Mjolnir holds the field with a Deimos beside her. NTF
       // capital ships come one after another, each on a deadline. Kept
       // here long enough, the Mjolnir's beam finds them; shooting out
       // navigation keeps them here. The Hecate at the end is the job.
       // Two Mjolnirs take turns; the Deimos keeps to the bottom edge.
       {id:'M1', c:'cr', n:1, spr:'sgmjolnir', side:'ally', x:70, y:140, callsOk:true},
       {id:'M2', c:'cr', n:1, spr:'sgmjolnir', side:'ally', x:70, y:360, callsOk:true,
        beamDelay:8},
       {id:'A1', c:'co', n:1, spr:'codeimos', side:'ally', still:true, x:200, y:440,
        callsOk:true},
       // Two lanes, one ship at a time in each: never more than two
       // capital ships on the NTF side at once. All hold their height.
       {id:'V1', c:'cr', n:1, spr:'ntfcraeolus',    t:3,  flee:30, y:170, still:true},
       {id:'V3', c:'co', n:1, spr:'ntfcodeimos',          flee:38, y:170, still:true, wait:true},
       {id:'V5', c:'de', n:1, spr:'ntfdehecate',          flee:48, y:170, still:true, wait:true},
       {id:'V2', c:'cr', n:1, spr:'ntfcrfenris',    t:14, flee:30, y:350, still:true},
       {id:'V4', c:'cr', n:1, spr:'ntfcrleviathan',       flee:30, y:350, still:true, wait:true},
       {id:'V6', c:'de', n:1, spr:'ntfdeorion',           flee:48, y:350, still:true, wait:true},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, wait:true},
       {id:'E2', c:'fi', n:1, wait:true},
       {id:'B2', c:'bo', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'V1', w:'einwarpen', a2:'V3'},
       {t:'alleZerstoert', a:'V3', w:'einwarpen', a2:'V5'},
       {t:'alleZerstoert', a:'V2', w:'einwarpen', a2:'V4'},
       {t:'alleZerstoert', a:'V4', w:'einwarpen', a2:'V6'},
       {t:'alleZerstoert', a:'V1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'V2', w:'einwarpen', a2:'E2'},
       {t:'alleZerstoert', a:'V4', w:'einwarpen', a2:'B2'},
       {t:'verlaesst', a:'V1', w:'meldung', a2:'the aeolus got away'},
       {t:'verlaesst', a:'V2', w:'meldung', a2:'the fenris got away'},
       {t:'verlaesst', a:'V3', w:'meldung', a2:'the deimos got away'},
       {t:'verlaesst', a:'V4', w:'meldung', a2:'the leviathan got away'},
       {t:'vernichtet', a:'V5+V6', w:'zielerfuellt', a2:'NTF BATTLE GROUP DESTROYED'},
       {t:'verlaesst', a:'V5', w:'zielverfehlt', a2:'THE HECATE GOT AWAY'},
       {t:'verlaesst', a:'V6', w:'zielverfehlt', a2:'THE ORION GOT AWAY'}
     ]},

  53:{name:'Der Gegenangriff', fac:'ntf', o:'clear', live:6,
      ziel:'COVER THE FLEET', u:[
       // Our Orion and a Deimos. An NTF Hecate and an NTF Orion jump in
       // on top of them, bombers follow. Their loss is a blow, not the
       // end of the mission: the NTF destroyers are the objective.
       // No support call while both are in the field - there is no room
       // for a third ship; once one is lost the call is free.
       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', y:170, hp:1.3,
        noWings:true},
       {id:'A2', c:'co', n:1, spr:'codeimos', side:'ally', y:390},
       {id:'E1', c:'fi', n:2},
       {id:'V1', c:'de', n:1, spr:'ntfdehecate', y:160, noFlee:true, wait:true},
       {id:'V2', c:'de', n:1, spr:'ntfdeorion', y:370, noFlee:true, wait:true},
       {id:'B1', c:'bo', n:2, wait:true}
     ], ev:[
       {t:'sek', a:12, w:'einwarpen', a2:'V1'},
       {t:'sek', a:12, w:'einwarpen', a2:'V2'},
       {t:'sek', a:12, w:'ziel', a2:'DESTROY THE HECATE AND THE ORION'},
       {t:'sek', a:18, w:'einwarpen', a2:'B1'},
       {t:'vernichtet', a:'A1', w:'meldung', a2:'gtd orion lost'},
       {t:'vernichtet', a:'A2', w:'meldung', a2:'gtcv deimos lost'},
       {t:'zerstoert', a:'A1', w:'ruf', a2:'A2'},
       {t:'zerstoert', a:'A2', w:'ruf', a2:'A1'},
       {t:'vernichtet', a:'V1+V2', w:'zielerfuellt', a2:'COUNTERATTACK BROKEN'}
     ]},

  54:{name:'Die Evakuierung', fac:'ntf', o:'protect', live:5, hunt:'T1',
      ziel:'GET THE ELYSIUMS OUT - AT LEAST THREE', u:[
       // Four Elysiums leave the Arcadia one after another and fly out
       // to the left, away from the NTF coming in from the right.
       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.36},
       {id:'T1', c:'tr', n:1, spr:'trelysium', side:'ally', t:2,  x:560, y:170, cross:-0.42},
       {id:'T2', c:'tr', n:1, spr:'trelysium', side:'ally', t:11, x:560, y:330, cross:-0.42},
       {id:'T3', c:'tr', n:1, spr:'trelysium', side:'ally', t:20, x:560, y:220, cross:-0.42},
       {id:'T4', c:'tr', n:1, spr:'trelysium', side:'ally', t:29, x:560, y:390, cross:-0.42},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, wait:true}
     ], ev:[
       {t:'sek', a:6, w:'einwarpen', a2:'B1'},
       {t:'sek', a:8, w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'T1', w:'jagd', a2:'T2'},
       {t:'alleZerstoert', a:'T2', w:'jagd', a2:'T3'},
       {t:'alleZerstoert', a:'T3', w:'jagd', a2:'T4'},
       {t:'verlaesst', a:'T1', w:'meldung', a2:'first elysium is out'},
       {t:'verlaesst', a:'T2', w:'meldung', a2:'second elysium is out'},
       {t:'verlaesst', a:'T3', w:'meldung', a2:'third elysium is out'},
       {t:'verlaesst', a:'T4', w:'meldung', a2:'fourth elysium is out'},
       {t:'gerettet', a:3, w:'zielerfuellt', a2:'EVACUATION COMPLETE'},
       {t:'verloren', a:2, w:'zielverfehlt', a2:'TOO MANY ELYSIUMS LOST'},
       {t:'alleZerstoert', a:'T1+T2+T3+T4', w:'nachschub', a2:'aus'}
     ]}
};
// Die Ereignisliste benutzt a fuer das Ziel des Ausloesers und a2 fuer das
// Ziel der Wirkung. buildScripted() erwartet w/a - hier umbenennen, damit
// die Missionen lesbar bleiben.
for(const k in SCRIPT_WAVES){
  const d = SCRIPT_WAVES[k];
  if(!d.ev) continue;
  for(const e of d.ev){ e.wa = (e.a2!==undefined) ? e.a2 : e.a; }
}

// ── GESCHRIEBENE WELLEN ──────────────────────────────────────
// Der Wellenplan aus v82 wuerfelt aus Komposition, Auftrag und
// Modifikator. Das traegt Abwechslung, aber keine Handlung: eine Staffel,
// die erst ueberlaeuft, nachdem die letzte feindliche gefallen ist, laesst
// sich als Tripel nicht ausdruecken.
//
// Eine geschriebene Welle nennt ihre Schiffe beim Namen, gibt ihnen eine
// Seite, einen Ort und eine Zeit - und eine Folge von Ereignissen. Beide
// Arten laufen nebeneinander: getWaveDef() nimmt eine geschriebene Welle,
// wenn es eine gibt, und wuerfelt sonst weiter wie bisher.
//
// Die acht Ausloeser und sieben Wirkungen sind nicht geraten. Sie sind
// ausgezaehlt aus dreissig geschriebenen Missionen; was dort nicht
// vorkam, steht hier nicht.

// Verbuendete Grosskampfschiffe laufen ueber ALLY_DEFS, nicht ueber
// mkEnemy. Diese Tabelle uebersetzt den Rumpf in die Kennung.
const ALLY_ID = {
  craten:'vas_aten', crmentu:'vas_mentu', cosobek:'vas_sobek',
  detyphon:'vas_typhon', dehatshepsut:'vas_hatshepsut',
  crfenris:'ter_fenris', crleviathan:'ter_leviathan', craeolus:'ter_aeolus',
  codeimos:'ter_deimos', deorionright:'ter_orion', dehecate:'ter_hecate',
  ntfcodeimos:'ntf_deimos', sgmjolnir:'ter_mjolnir'
};
// The NTF variant of a Terran capital hull. A ship that goes over to the
// NTF flies on as this: same class, same size, NTF markings.
const NTF_HULL = {
  crleviathan:'ntfcrleviathan', crfenris:'ntfcrfenris', craeolus:'ntfcraeolus',
  codeimos:'ntfcodeimos', deorionright:'ntfdeorion', deorionleft:'ntfdeorion',
  dehecate:'ntfdehecate'
};
// Kategorien, die keinen Fraktionszusatz tragen.
// ROLES wird vom Packer erzeugt und kennt keine Installationen.
const INSTALLATIONS = ['inarcadia','incommnode','inpharos'];
const CAT_FIX = {sg:'sentry', fc:'container', fr:'freighter', tr:'freighter',
                 ast:'ast', ep:'container', ic:'iceni'};
const CAT_FAC = {fi:1, bo:1, cr:1, co:1, de:1, in:1};

// ── Zustand der benannten Einheiten ──────────────────────────
// Ein Ausloeser wie "X zerstoert" braucht zwei Auskuenfte: war X jemals
// da, und ist es jetzt weg. Ohne das Erste feuert jeder Ausloeser
// sofort, weil zu Wellenbeginn nichts existiert.
let EV = [], EV_HELD = {}, EV_SEEN = {}, EV_LEFT = {}, EV_DOCK = {};
// EV_TAKEN: captured ('kapern'). EV_FLED: jumped out on a deadline.
// Neither is a kill, and 'vernichtet' asks for a kill.
let EV_TAKEN = {}, EV_FLED = {};
// Letzter bekannter Ort je Kennung. Wer nach dem Tod eines Schiffs
// eingewarpt wird, soll dort erscheinen und nicht am Bildrand.
let EV_POS = {};
let evReinf = false, evReinfCd = 0;
const EV_REINF_GAP = 520;      // 5,2 s zwischen zwei Nachschubstaffeln

function evReset(){
  EV = []; EV_HELD = {}; EV_SEEN = {}; EV_LEFT = {}; EV_DOCK = {}; EV_POS = {};
  EV_TAKEN = {}; EV_FLED = {};
  evReinf = false; evReinfCd = 0;
}
function byId(id){
  const out = [];
  for(const e of enemies) if(e.uid===id && !e.dead) out.push(e);
  for(const a of allies)  if(a.uid===id && !a.dead) out.push(a);
  return out;
}
function evSeen(id){ return !!EV_SEEN[id]; }
// A trigger may name several ids joined with '+'.
function evIds(a){ return String(a||'').split('+'); }
// Ist fuer diese Kennung ein Seitenwechsel vorgesehen? Dann bekommt sie
// den Rumpfriegel, sonst haengt die Pointe der Welle am Zufall.
function evWillDefect(id){
  if(!id) return false;
  for(const e of EV) if(e.w==='seite' && (e.wa||e.a)===id) return true;
  return false;
}

// ── Ausloeser ────────────────────────────────────────────────
function evTrig(ev){
  switch(ev.t){
    case 'sek':          return spawnT >= (ev.a||0)*TICK_HZ;
    case 'zerstoert':    return evSeen(ev.a) && byId(ev.a).length===0 && !EV_LEFT[ev.a] && !EV_TAKEN[ev.a];
    // Destroyed and nothing else: not left, not fled on a deadline, not
    // taken. 'zerstoert' stays as it was, because written missions rely
    // on it firing for a ship that jumped out.
    // Several ids joined with '+': every one of them.
    case 'vernichtet':   return evIds(ev.a).every(function(id){
                                return evSeen(id) && byId(id).length===0
                                  && !EV_LEFT[id] && !EV_FLED[id] && !EV_TAKEN[id]; });
    case 'alleZerstoert':return evIds(ev.a).every(function(id){
                                return evSeen(id) && byId(id).length===0; });
    // Protected ships through, and protected ships lost, this wave.
    // Only once nobody is still under way: 'three are out' while a
    // fourth is in the field reads as if she did not count.
    case 'gerettet':     return protSaved >= (ev.a||1) && !crossPending()
                                && !spawnQ.some(function(q){ return q.type==='protect'; });
    case 'verloren':     return protLost  >= (ev.a||1);
    case 'verlaesst':    return !!EV_LEFT[ev.a] || !!EV_FLED[ev.a];
    case 'angedockt':    return !!EV_DOCK[ev.a];
    case 'anzahlUnter':
      // Erst wenn nichts mehr fuer diese Kennung in der Warteschlange
      // steht. Sonst feuert der Ausloeser, waehrend noch eingesetzt wird:
      // der erste Container ist einer, und einer ist weniger als drei.
      if(!evSeen(ev.a)) return false;
      for(const q of spawnQ) if(q.uid===ev.a) return false;
      return byId(ev.a).length < (ev.b||1);
    case 'rumpfUnter': {
      const u = byId(ev.a)[0];
      return !!u && u.maxHp && (u.hp/u.maxHp)*100 < (ev.b||50);
    }
    case 'subsystem': {
      const su = byId(ev.a)[0];
      if(!su || !hasSubsystems(su)) return false;
      // Several may be named, joined with '+': all of them have to be down.
      return String(ev.b || 'communication').split('+')
               .every(function(id){ return !subOK(su, id); });
    }
    case 'gescannt': {
      // Every ship of this id has been scanned - by any kind of scan.
      if(!evSeen(ev.a)) return false;
      for(const q of spawnQ) if(q.uid===ev.a) return false;
      const us = byId(ev.a);
      return us.length>0 && us.every(function(u){ return u.scanned; });
    }
    case 'erfuellt':
      // Zu Wellenbeginn ist noch nichts im Feld, und "nichts zu tun" sieht
      // aus wie "erledigt". Erst wenn der Auftrag einmal bestanden hat.
      if(!objSeenOnce) return false;
      if(spawnQ.length) return false;
      return !objectiveText();
  }
  return false;
}

// ── Wirkungen ────────────────────────────────────────────────
function evFire(ev){
  // Ausloeser und Wirkung koennen verschiedene Ziele haben. wa ist das
  // Ziel der Wirkung, a das des Ausloesers.
  const arg = (ev.wa!==undefined && ev.wa!==null) ? ev.wa : ev.a;
  switch(ev.w){
    case 'einwarpen': {
      const held = EV_HELD[arg];
      // Wer am Ort eines anderen Schiffs starten soll, uebernimmt dessen
      // letzte Position - leicht gestreut, damit sie nicht stapeln.
      const src = (held && held[0] && held[0].at) ? EV_POS[held[0].at] : null;
      if(held){ for(const q of held){
                  q.time = spawnT + (q.delay||0);
                  if(src){ q.x = src[0] + (Math.random()*2-1)*26;
                           q.y = src[1] + (Math.random()*2-1)*22; }
                  spawnQ.push(q); }
                delete EV_HELD[arg];
                spawnQ.sort(function(a,b){ return a.time-b.time; }); }
      break;
    }
    case 'auftrag':
      waveObj = arg;
      // Der Banner liest den Zustand des Feldes; die Erfolgsmeldung des
      // alten Auftrags soll den neuen nicht ueberdecken.
      objWasSet = false; objDoneT = 0; objFailed = false;
      break;
    case 'seite':
      for(const u of byId(arg)) if(u.side!=='enemy') defect(u);
      break;
    case 'raus':
      for(const u of byId(arg)){ u.warpOut = u.warpMax || 100; EV_LEFT[arg] = true; }
      break;
    case 'heilen': {
      // M027: jeder angedockte Transporter setzt den Rumpf ein Stueck
      // hoch. Wer schlecht verteidigt, wartet laenger.
      const ht = byId(arg)[0];
      if(ht){ ht.hp = Math.min(ht.maxHp, ht.hp + ht.maxHp*0.25);
              SUB_MSGS.push({x:ht.x, y:ht.y-40, txt:'HULL REPAIRED',
                             life:150, ml:150, ally:true, tone:'good'});
              if(ht.hp >= ht.maxHp*0.999){
                ht.warpOut = ht.warpMax || 100;
                // An enemy repaired and gone has left, not been destroyed.
                if(ht.side!=='ally' && ht.uid){ EV_FLED[ht.uid] = true; ht.fleeFree = false; }
                SUB_MSGS.push({x:ht.x, y:ht.y-56, txt:'REPAIRS COMPLETE',
                               life:180, ml:180, ally:true, tone:'good'}); } }
      break;
    }
    case 'jagd':
      waveHunt = arg || '';
      // Die Zuweisung gilt fuer neue Schiffe; die im Feld werden
      // nachgezogen, sonst wirkt der Wechsel erst nach der naechsten Welle.
      for(const o of enemies)
        if(o.type==='fighter'||o.type==='bomber') o.hunter = Math.random()<HUNT_SHARE;
      break;
    case 'nachschub':
      evReinf = (arg !== 'aus');
      break;
    case 'meldung':
      notice(String(arg||'').toUpperCase(), 'info');
      break;
    case 'ende':
      for(let i=spawnQ.length-1;i>=0;i--) spawnQ.splice(i,1);
      evReinf = false;
      break;
    case 'kapern':
      // Taken. She stops fighting and jumps away with her captors - no
      // escape penalty, and her points go to the player as for a kill.
      for(const u of byId(arg)){
        if(u.side==='ally') continue;
        // An installation does not jump. Taken, it stays where it is,
        // stops fighting and becomes part of the scenery.
        if(u.type==='station'){
          u.captureLock = false; u.captured = true; u.noFire = true;
          u.invuln = true; u.scenery = true; u.noTarget = true;
          u.faction = 'terran';
          EV_TAKEN[arg] = true;
          score += u.pts || 0;
          SUB_MSGS.push({x:u.x, y:u.y-60, txt:'CAPTURED', life:200, ml:200,
                         ally:true, tone:'good'});
          continue;
        }
        u.captureLock = false; u.captured = true; u.fleeFree = true;
        u.escaping = 0; u.fleeT = 0;
        u.warpOut = u.warpMax > 1 ? u.warpMax : 160;
        u.warpX = u.x; u.warpY = u.y;
        EV_TAKEN[arg] = true;
        score += u.pts || 0;
        SUB_MSGS.push({x:u.x, y:u.y-40, txt:'CAPTURED', life:200, ml:200,
                       ally:true, tone:'good'});
      }
      break;
    case 'ziel':
      // The mission's own objective, in words. Announced by a card and
      // kept in the line under the bar.
      missionObj = String(arg || '').toUpperCase();
      missionObjUsed = true;
      break;
    case 'zielerfuellt':
    case 'zielverfehlt':
      missionObj = '';
      missionObjUsed = true;
      objAnnounce(ev.w==='zielerfuellt' ? 'OBJECTIVE COMPLETE' : 'OBJECTIVE FAILED',
                  String(arg || '').toUpperCase(),
                  ev.w==='zielerfuellt' ? 'done' : 'fail');
      break;
    case 'freigeben':
      // The capture is off - her captors are gone. Now she can die.
      for(const u of byId(arg)) u.captureLock = false;
      break;
    case 'ruf':
      // From now on this ship no longer blocks the support call.
      for(const u of byId(arg)) u.callsOk = true;
      break;
    case 'kulisse':
      // Out of the fight: she stays, but no longer shoots and no longer
      // counts for the end of the wave (the NTF keeps her).
      for(const u of byId(arg)){
        u.captureLock = false; u.noFire = true; u.invuln = true;
        u.scenery = true; u.noTarget = true;
      }
      break;
  }
}

// Ein Schiff im Anflug, das sein Ziel wirklich beruehrt, schlaegt ein.
// Geprueft wird gegen das Ziel, das es sich gesucht hat - nicht gegen
// alles, sonst rammt ein Bomber auf dem Rueckweg seinen eigenen Fluegelmann.
function tickRamming(){
  for(let i=enemies.length-1;i>=0;i--){
    const e = enemies[i];
    if(e.dead || e.warp>0 || e.warpOut>0) continue;
    if(!ramsOnContact(e)) continue;
    if(e.role!=='attack' || e.passT>0) continue;
    const t = smallTarget(e);
    // Nur gegen verbuendete Grosskampfschiffe. Auf den Spieler zu stuerzen
    // waere kein Kamikaze, sondern ein unfairer Treffer ohne Vorwarnung.
    if(!t || t===e || t===player || t.small || t.side!=='ally') continue;
    // Gemessen wurde von Mitte zu Mitte. Ein Zerstoerer ist mehrere hundert
    // Punkte breit, also war der Abstand eines Bombers auf seinem Rumpf zur
    // Mitte des Schiffes nie unter 26 - der Bomber flog hinueber und nichts
    // geschah. Beruehrung heisst Rumpf an Rumpf, waagerecht und senkrecht
    // getrennt geprueft wie beim rammenden Grosskampfschiff.
    if(!hullsTouch(e, t, RAM_OVERLAP)) continue;
    const pct = (e.type==='bomber') ? RAM_PCT_BOMBER : RAM_PCT_FIGHTER;
    if(t===player){
      const dm = Math.max(1, Math.round(player.maxHp*pct));
      if(player.sh>0){ const abs=Math.min(player.sh,dm); player.sh-=abs;
        player.shDelay=90; player.shHit=SH_FLASH; shieldHit(e.x,e.y);
        if(dm>abs){ player.hp-=dm-abs; hullHit(e.x,e.y); } }
      else { player.hp-=dm; hullHit(e.x,e.y); }
      if(player.hp<=0) playerDie();
    } else {
      const dm = Math.max(1, Math.round((t.maxHp||100)*pct));
      t.hp -= dm; hullHit(e.x, e.y);
    }
    ramBlast(e);
    // Vom Feld nehmen, hier und sofort, genau wie tickCapRam() es mit
    // seinem Rammer tut. Die Aufraeumschleife raeumt ihn nicht mehr weg:
    // sie greift nur bei e.hp<=0 UND NICHT e.dead, und ramBlast setzt
    // beides. Blieb er stehen, war er ein Geist - ohne Winkel, nicht
    // abschiessbar, nicht mitgezaehlt, aber weiter fliegend und feuernd.
    enemies.splice(i, 1);
  }
}
// Eigene Explosion: da geht ein Schiff mit Bomben an Bord hoch. Groesser
// als der uebliche Bombertod, mit Ring und heller Mitte.
function ramBlast(e){
  // Korvettenprofil statt Bomberprofil: da geht Munition mit hoch.
  triggerExpl(e.x, e.y, 'corvette', e.faction, e);
  spawnShock(e.x, e.y, 118, 2.0, 0.015);
  addShake(4, 18);
  for(let k=0;k<26;k++){
    const a = Math.random()*Math.PI*2, s = 1.6+Math.random()*3.4;
    PARTS.push({x:e.x, y:e.y, vx:Math.cos(a)*s, vy:Math.sin(a)*s,
                life:(22+Math.random()*22)|0, ml:0, sz:1.4+Math.random()*1.8,
                clr:(k%3===0)?'#ffffff':'#ffcc44'});
  }
  // Beide Marken setzen und das Schiff dem Aufrufer zum Entfernen
  // ueberlassen: wer ramBlast ruft, nimmt es danach selbst aus enemies.
  e.dead = true; e.hp = 0;
}

function tickEvents(){
  // Ort mitschreiben, solange die Schiffe noch da sind.
  for(const e of enemies) if(e.uid) EV_POS[e.uid] = [e.x, e.y];
  for(const a of allies)  if(a.uid) EV_POS[a.uid] = [a.x, a.y];
  if(!EV.length && !evReinf) return;
  for(const ev of EV){
    if(ev.done) continue;
    if(!evTrig(ev)) continue;
    ev.done = true;
    evFire(ev);
  }
  // Nachschub, solange ein Ereignis ihn eingeschaltet hat. Er haengt nicht
  // an der Uhr, sondern an dem Ereignis, das ihn wieder ausschaltet -
  // deshalb kann eine Welle nicht ablaufen, waehrend der Grund dafuer
  // noch im Feld steht.
  if(evReinf){
    if(evReinfCd>0){ evReinfCd--; }
    else if(liveSmallCount() < smallCap()){
      evReinfCd = EV_REINF_GAP;
      const wid = ++wingSeq, sz = WING_MIN + ((Math.random()*(WING_MAX-WING_MIN+1))|0);
      const ty = 'fi_' + FAC_TAG[currentFaction];
      const rp = poolFor(ty);
      const rh = rp ? rnd(rp) : '';     // eine Staffel, ein Rumpf
      const ry = H*(0.22+Math.random()*0.56);
      // Ein Drittel der Staffeln springt mitten ins Feld statt am Rand.
      const rx = (Math.random()<0.34) ? (W*0.45+Math.random()*W*0.4) : null;
      for(let k=0;k<sz;k++)
        spawnQ.push({time:spawnT+k*WING_STAGGER, type:ty, spr:rh, wing:wid,
                     x: rx!=null ? rx+(k-(sz-1)/2)*22 : null,
                     y:ry + (k-(sz-1)/2)*WING_SPACING*0.5});
    }
  }
}

// ── Aus einer geschriebenen Welle eine Warteschlange machen ──
function scriptUnit(u, fac, q){
  const n  = Math.max(1, u.n||1);
  const t0 = (u.t||0)*TICK_HZ + 1;
  const put = function(e){
    e.uid = u.id;
    if(u.hp) e.hpMul = u.hp;
    if(u.wait){ e.delay = e.time - t0; (EV_HELD[u.id]=EV_HELD[u.id]||[]).push(e); }
    else q.push(e);
  };
  const ally = (u.side === 'ally');

  if(CAT_FAC[u.c]){
    const ty = u.c + '_' + FAC_TAG[fac];
    if(u.c==='fi' || u.c==='bo'){
      // n zaehlt Staffeln, nicht Schiffe.
      for(let w=0; w<n; w++){
        const wid = ++wingSeq;
        const sz  = WING_MIN + ((Math.random()*(WING_MAX-WING_MIN+1))|0);
        const yy  = (u.y!=null) ? u.y : H*(0.22+0.5*((w+0.5)/n));
        // Eine Staffel fliegt einen Rumpf. Der Wurf gehoert hierher und
        // nicht in mkEnemy, sonst bekommt jedes Schiff einen eigenen.
        const pool = ally
          ? (fac==='hol' ? ROLES.ally_vas_fighters : ROLES.ally_ter_fighters)
          : poolFor(ty);
        const hull = u.spr || (pool ? rnd(pool) : '');
        // Staffelabstand: 2,6 s waren im Spiel eine Pause, in der nichts
        // passiert. 1,1 s reichen, um sie als getrennte Staffeln zu lesen.
        for(let k=0;k<sz;k++)
          put({time:t0 + w*110 + k*WING_STAGGER,
               type: ally ? 'allyfi' : ty, spr:hull, wing:ally?0:wid,
               y: yy + (k-(sz-1)/2)*WING_SPACING*0.5, x:u.x, rammer:u.ram});
      }
    } else {
      // Mehrere Grosskampfschiffe derselben Kennung stehen sonst
      // uebereinander und blockieren sich. Versetzt in Tiefe und Hoehe:
      // hintereinander gestaffelt, jedes in seinem eigenen Hoehenband.
      for(let i=0;i<n;i++){
        const yy = (u.y!=null) ? u.y : H*(0.28+0.44*((i+0.5)/n));
        put(ally
          ? {time:t0+i*140, type:'ally', allyId:ALLY_ID[u.spr]||'vas_aten', spr:u.spr,
             crossSecs:u.crossSecs, still:u.still,
             crossDir:u.crossDir, defectRun:u.defectRun, noWings:u.noWings,
             x:u.x, y:u.y, callsOk:u.callsOk, beamDelay:u.beamDelay}
          : {time:t0+i*140, type:ty, spr:u.spr||'', y:(u.c==='in'?(u.y!=null?u.y:H*0.5):yy),
             x:u.x, escape:u.escape, invuln:u.invuln, edge:u.edge, capRam:u.capRam,
             escWarp:u.escWarp, capture:u.capture, flee:u.flee, scanSubs:u.scanSubs,
             fleeFree:u.fleeFree, hurt:u.hurt, armed:u.armed, noFlee:u.noFlee,
             still:u.still, noFlak:u.noFlak, fixY:(u.y!=null),
             capIndex:(n>1)? i : 0});
      }
    }
    return;
  }

  if(u.c==='ic'){
    // flee: seconds until she jumps. navProof: no navigation subsystem,
    // so the jump cannot be stopped. fleeFree: her escape costs nothing.
    put({time:t0, type:'iceni', spr:'coiceni',
         y:(u.y!=null) ? u.y : H*0.5, x:u.x,
         flee:u.flee, navProof:u.navProof, fleeFree:u.fleeFree,
         still:u.still, fixY:(u.y!=null)});
    return;
  }
  const fix = CAT_FIX[u.c];
  if(!fix) return;                     // Klasse noch nicht spawnbar
  for(let i=0;i<n;i++){
    // Brocken streuen ueber das ganze Feld, alles andere bleibt rechts.
    const yy = (u.y!=null) ? u.y
             : (fix==='ast' ? HUD_H+24+Math.random()*(H-HUD_H-48)
                            : H*(0.18+0.64*((i+0.5)/n)));
    const xx = (u.x!=null) ? u.x
             : (fix==='ast' ? W*0.18+Math.random()*W*0.78
                            : W*(0.52+0.30*Math.random()));
    // Geschuetze, Container und Brocken stehen seit Wellenbeginn im Feld -
    // sie muessen auch sofort da sein und nicht ueber Sekunden eintropfen.
    const stagger = 0;   // alles steht ab dem ersten Bild da
    if(ally && fix!=='ast')
      put({time:t0+i*70, type:'protect', spr:u.spr,
           fac:(fac==='hol') ? 'vasudan' : 'terran', noWarp:1,
           x:xx, y:yy, cross:u.cross, at:u.at, dockTo:u.dockTo, dockHold:u.dockHold,
           pickup:u.pickup?1:0});
    else
      put({time:t0+i*stagger, type:fix, spr:u.spr||'', fac:fac, noWarp:(fix!=='ast')?1:0,
           x:xx, y:yy, scan:u.scan?1:0, escape:u.escape, scanFirst:u.scanFirst,
           dockTo:u.dockTo, dockHold:u.dockHold,
           scenery:(fix==='ast')?1:0, pickup:u.pickup?1:0});
  }
}

// Freighters follow the containers: one per container, never set by hand.
// Containers someone is sent to fetch are marked as pickups, so one that is
// left behind can be released instead of holding the wave open.
function scriptUnitsResolved(def){
  const us = def.u || [];
  return us.map(function(u){
    const o = Object.assign({}, u);
    const tg = u.dockTo ? us.find(function(x){ return x.id===u.dockTo; }) : null;
    if(tg && tg.c==='fc') o.n = tg.n || 1;
    if(u.c==='fc' && us.some(function(x){ return x.dockTo===u.id; })) o.pickup = true;
    return o;
  });
}

function buildScripted(def){
  const q = [];
  evReset();
  currentFaction = def.fac;
  waveLive  = def.live || 4;
  waveObj   = def.o || 'clear';
  fleeTotal = 0; fleeEscaped = 0;
  guardWanted=false; guardSpawned=false; guardLost=false; guardGone=false;
  // Schleuse an: die naechste Staffel wartet auf ein freies Feld statt auf
  // die Uhr. Auf einer Querung muss sie aus sein, sonst blockiert die
  // erste Staffel sich selbst - dort gibt es kein freies Feld.
  astAim=false; transitSecs=0; gateWings=!def.crossEnds; gateWing=0;
  disableTarget=null; waveFeud=false;
  astStreamCd = AST_STREAM_MEAN;
  waveMod = def.mod || MOD_NONE;
  // A mission that states its objective in words speaks for itself for
  // the whole wave; the automatic result cards then stay quiet.
  missionObj = String(def.ziel || '').toUpperCase();
  if(def.ship) forceShip(def.ship);
  missionObjUsed = !!def.ziel || (def.ev||[]).some(function(e){ return /^ziel/.test(e.w); });
  if(nebulaOn()) nebTint = NEB_TINTS[(Math.random()*NEB_TINTS.length)|0];
  empOut=0; empWarn=0; empNext = waveMod==='emp' ? 1400 : 0;
  BOMB_PORTALS=[]; bombRaidLeft=0; reinfAt=0; reinfDone=true;
  crossDone=0; crossTotal=0; commsCut=false; commsSeen=false;

  escTotal = 0; escGone = 0;
  for(const u of (def.u||[])) if(u.escape) escTotal += (u.n||1);
  waveHunt = def.hunt || '';
  astStill = !!def.stillRocks;
  scanUnderFire = !!def.scanUnderFire;
  // Ein stehendes Feld wird gesetzt, nicht gespeist. Sonst sammeln sich
  // unbewegliche Brocken ausserhalb des rechten Randes.
  // noRocks: a crossing without the belt feeding rocks into it.
  astStreamCd = (astStill || def.noRocks) ? 1e9 : AST_STREAM_MEAN;
  // Eine geschriebene Querung endet, wenn der Schuetzling drueben ist.
  transitSecs = def.crossEnds ? 1 : 0;
  for(const u of scriptUnitsResolved(def)) scriptUnit(u, def.fac, q);
  EV = (def.ev||[]).map(function(e){
    return {t:e.t, a:e.a, b:e.b, w:e.w, wa:e.wa, done:false}; });
  return q.sort(function(a,b){ return a.time-b.time; });
}

function getWaveDef(n){
  // Test mode replaces the wave plan entirely. Without ?test=1 on the URL
  // none of this is reachable and the normal game is untouched.
  if(TEST_MODE) return buildTestWave(((n-2+TEST_FIRST)%4)+1);
  if(FS1_MODE)  return buildFS1Wave(n);
  // Written mission, if there is one for this wave. ?m=36 starts the run
  // at wave 36 (see launchGame) and it carries on from there; the dice
  // take over after the last written one.
  {
    const def = SCRIPT_WAVES[n];
    if(def) return buildScripted(def);
  }

  // The generator is set up on the first wave the run actually plays,
  // which is not wave 1 when ?m= starts it further in.
  if(n===1 || n===SCRIPT_ONE){ lastBossWave = 0; rollNextBoss(Math.max(SEQ_LEN, n));
                              lastK=''; lastO=''; }

  let pick;
  if(n <= SEQ_LEN){
    pick = WAVE_SEQ[n-1];
    if(pick.o==='boss'){ lastBossWave = n; rollNextBoss(n); }
  } else {
    pick = rollWave(n);
  }
  lastK = pick.k; lastO = pick.o;

  const K = COMPOS[pick.k], o = pick.o, spec0 = OBJ[o] || OBJ.clear;
  const tier = Math.floor((n-1)/SEQ_LEN), t = tier;
  const fac = factionOf(pick.f || ((n%2) ? 'ntf' : 'shivan'));
  currentFaction = fac;
  const shivan = (fac === 'shivan');
  const sfx = shivan ? '_sh' : (fac === 'hol' ? '_hol' : '_ntf');

  waveLive = K.live + (shivan?WAVE_LIVE_SHIVAN:0) + t*WAVE_TIER_LIVE;
  fleeTotal = 0; fleeEscaped = 0;

  // ── Auftrag setzt die Flaggen, die Komposition keine davon ──
  guardWanted = (o==='guard' || o==='transit');
  guardSpawned = false; guardLost = false;
  guardClass  = spec0.cls || 'cruiser';
  guardFrac   = GUARD_HULL_FRAC;
  guardReward = guardClass;
  astAim      = !!spec0.aim;
  transitSecs = (o==='transit') ? (spec0.secs||50) : 0;
  // A crossing has no clear field to wait for: the rocks never stop, so
  // gating the wings there would hold back every wing after the first.
  gateWings = !transitSecs;
  gateWing = 0;
  disableTarget = null;
  guardGone   = false;
  astStreamCd = AST_STREAM_MEAN;
  waveFeud    = (o==='feud');
  waveObj     = o;
  waveHunt    = '';
  astStill    = false;
  waveTitle   = 'WAVE '+n+'   '+K.name.toUpperCase();
  titleT      = TITLE_TIME;

  waveMod = rollWaveMod(n);
  if(waveMod!==MOD_NONE) lastMod = waveMod;
  if(nebulaOn()) nebTint = NEB_TINTS[(Math.random()*NEB_TINTS.length)|0];
  empOut = 0; empWarn = 0;
  empNext = waveMod==='emp' ? (1200+((Math.random()*600)|0)-EMP_WARN) : 0;

  // Subraum-Bombenangriffe. Drei Einschraenkungen gegenueber v81:
  //   - nur in Wellen, in denen auch Bomber vorkommen. Sie sind eine
  //     Bomberwaffe und kein Naturereignis.
  //   - hoechstens zwei statt drei je Welle.
  //   - nie im Nebel: fireRange() deckelt dort auf 240, die Bomben kaemen
  //     gar nicht erst an.
  BOMB_PORTALS = [];
  const bombOk = (K.bo > 0) && (n >= BOMB_RAID_FIRST_WAVE) && !nebulaOn();
  bombRaidLeft = bombOk ? ((Math.random()*(BOMB_RAID_MAX+1))|0) : 0;
  bombRaidCd   = BOMB_RAID_FIRST + ((Math.random()*BOMB_RAID_JIT)|0);
  reinfAt = K.reinf || 0; reinfDone = false;

  const spec = {
    name:  K.name,
    fi:    K.fi + (K.fi?t*WAVE_TIER_WINGS:0)
           + ((K.iceni && o==='runner' && !shivan) ? icenEscapes : 0),
    bo:    K.bo + (K.bo?t*WAVE_TIER_WINGS:0),
    ast:   K.ast,
    caps:  K.caps.map(function(c){
      if(c==='cr' && K.iceni && o==='runner' && !shivan) return 'iceni';
      return c==='boss' ? 'boss'+sfx : c+sfx;
    }),
    pause: K.pause,
    flee:  (o==='runner' && K.caps.length) ? (spec0.flee||40) : 0,
    fiType:'fi'+sfx, boType:'bo'+sfx
  };
  const q = buildWave(spec);

  // ── Was die Komposition zusaetzlich ins Feld stellt ──────────
  // Sperrgeschuetze stehen von Anfang an da und warpen nicht ein.
  const sgPool = shivan ? ['sgtrident','sgbelial']
               : (fac==='hol' ? ['sgankh']
                              : ['sgwatchdog','sgcerberus','sgalastor']);
  for(let i=0;i<(K.sg||0);i++)
    q.push({time:1, type:'sentry', spr:sgPool[(Math.random()*sgPool.length)|0],
            fac:fac, noWarp:1,
            x:W*(0.62+0.13*(i%3)), y:H*(0.20+0.13*(i%5))});

  // Container stellt nur noch der Scanauftrag - und der stellt sie einmal.
  // Vorher brachte die Komposition zwei mit und der Auftrag drei dazu:
  // fuenf Stueck, teils hintereinander, und in Eskortenwellen standen sie
  // der Orion in der Bahn.

  // ── Was der Auftrag zusaetzlich ins Feld stellt ──────────────
  if(o==='scan'){
    const nsc = spec0.cargo||3;
    // Links der Mitte und weit auseinander: rechts kommen die Gegner
    // herein, und ein Container mit 69 Trefferpunkten stirbt an einem
    // Streifschuss. Senkrecht mindestens ein Viertel Feldhoehe Abstand,
    // waagerecht versetzt, damit keiner hinter einem anderen verschwindet.
    for(let i=0;i<nsc;i++)
      q.push({time:1, type:'container', spr:'fcvc3', fac:fac, scan:1,
              noWarp:1,
              x:W*(0.30+0.14*i),
              y:H*(0.24+(0.52/Math.max(1,nsc-1))*i)});
  }
  if(o==='protect'){
    // Leicht versetzt, damit zwei Frachter nicht als Block wirken.
    for(const pair of (spec0.ships||[]))
      for(let i=0;i<pair[1];i++){
        q.push({time:1+i*90, type:'protect', spr:pair[0], fac:'terran', noWarp:1,
                cross:PROTECT_CROSS_SPD, x:-40-i*70, y:H*(0.34+0.16*i)});
        crossTotal++;
      }
  }
  if(o==='runner' && !K.caps.length){
    // Ohne Grosskampfschiff traegt die Frist niemand, also fliehen Frachter.
    for(const pair of (spec0.ships||[]))
      for(let i=0;i<pair[1];i++){
        q.push({time:200+i*160, type:'freighter', spr:pair[0], fac:fac,
                runner:1, hpMul:RUNNER_HP_MUL, y:H*(0.30+0.22*i)});
        fleeTotal++;
      }
  }
  if(o==='disable'){
    // Das erste Grosskampfschiff der Welle wird das Ziel. buildWave setzt
    // sie in caps-Reihenfolge ganz nach vorn in die Schlange.
    for(const e of q) if(e.type && CAP_GAP[e.type.split('_')[0]]!==undefined){ e.disable=1; break; }
  }
  // Eine verbuendete Staffel, die das Feuer teilt. Nur wo die Komposition
  // sie ausdruecklich vorsieht - siehe crossing.
  if(K.allyWing) allyWingWanted = K.allyWing;
  else           allyWingWanted = 0;

  return q.sort(function(a,b){ return a.time-b.time; });
}

// Capital ships queue up in order. Small craft no longer inherit their
// timing from that queue: they arrive on the wave's own wing interval.
const SMALL_TYPES = {fi_ntf:1, fi_sh:1, bo_ntf:1, bo_sh:1, ast:1};
const WING_TYPES  = {fi_ntf:1, fi_sh:1, bo_ntf:1, bo_sh:1};

// FreeSpace sends wings, not a random assortment. Three or four of the
// same hull arrive together, stacked vertically, and keep their wing id so
// the live cap can hold back a whole wing instead of splitting it.
const WING_MIN = 3, WING_MAX = 4;
const WING_STAGGER = 14;     // steps between two ships of one wing
const WING_SPACING = 34;     // px between them on arrival
let wingSeq = 0;

// Der Hammer of Light fliegt vasudanische Ruempfe. ROLES wird vom Packer
// erzeugt, deshalb hier als Verweis statt dort als Eintrag - sonst muesste
// der Packer dieselbe Liste ein zweites Mal fuehren.
// Der Ptah ist ein Tarnjaeger. Er fliegt nicht in gewoehnlichen Staffeln,
// weder beim Hammer of Light noch bei den Vasudanern.
ROLES.hol_fighters   = ROLES.ally_vas_fighters.filter(function(k){ return k!=='fiptah'; });
ROLES.hol_bombers    = ROLES.ally_vas_bombers;
ROLES.hol_cruisers   = ROLES.ally_vas_cruisers;
ROLES.hol_corvette   = ROLES.ally_vas_corvette;
ROLES.hol_destroyers = ROLES.ally_vas_destroyers;

const FAC_SFX  = {ntf:'ntf', sh:'shivan', hol:'hol'};
// Rueckrichtung: Fraktion -> Kuerzel im Typnamen. Ohne sie fiel jede
// Stelle, die einen Typ selbst zusammensetzt, auf zwei Faelle zurueck.
const FAC_TAG  = {ntf:'ntf', shivan:'sh', hol:'hol', renegade:'ntf'};
const ROLE_KEY = {fi:'fighters', bo:'bombers', cr:'cruisers',
                  co:'corvette', de:'destroyers', boss:'super'};
function typeRole(t){ const i=t.indexOf('_'); return i<0 ? t : t.slice(0,i); }
function typeFac(t){ const i=t.indexOf('_'); return i<0 ? 'ntf' : (FAC_SFX[t.slice(i+1)]||'ntf'); }
function poolFor(type){
  const k = ROLE_KEY[typeRole(type)];
  return k ? (ROLES[typeFac(type)+'_'+k] || null) : null;
}

// Since small craft stopped leaving to the left, everything that arrives
// stays until it is shot down. The old schedule was written for ships that
// flew past, so it delivered them far too densely.
// The cap is the part that really prevents an overrun, because it responds
// to how the fight is actually going. Anything held back is not dropped,
// only pushed further down the queue. Its value comes from the wave plan.
const LIVE_SMALL_MAX = 14;
const LIVE_SMALL_RETRY = 40;      // steps to wait before trying again

function smallCap(){ return Math.min(LIVE_SMALL_MAX, waveLive); }
// Ships still in their warp vortex count: they are already committed.
function liveSmallCount(){
  let n=0;
  for(const e of enemies) if((e.type==='fighter'||e.type==='bomber') && !e.dead) n++;
  return n;
}

