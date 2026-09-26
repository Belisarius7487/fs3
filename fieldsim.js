// Field simulation: runs the REAL game in a headless browser.
//
// The other simulations lift single functions out of the logic file. This one
// loads the whole file, starts a real run with ?m=NN and steps the real
// update() - spawn queue, events, allied and enemy flight, the lot. That is
// the part the others cannot see: whether a mission actually plays out.
//
// No sprites are embedded in a logic file, so every hull gets a plain opaque
// stand-in of a fitting shape, and the mount data is put in the way the
// packer puts it in. The player cannot die; the scenarios decide what gets
// shot down, and when.
//
// Needs Playwright with Chromium (it runs where the build is checked, not on
// the server).
// Usage: node fieldsim.js <logic.html> [hlp_mounts_final.json]
const fs = require('fs'), path = require('path'), os = require('os');
const { execSync } = require('child_process');
const PW = path.join(execSync('npm root -g').toString().trim(), 'playwright');
const { chromium } = require(PW);

const logic = process.argv[2];
const mounts = process.argv[3] || 'hlp_mounts_final.json';
let html = fs.readFileSync(logic, 'utf8');
const M = fs.readFileSync(mounts, 'utf8');
// Same shape as build_game.py's render_mounts(), placed first so it exists
// before anything asks for it.
html = html.replace(/<script([^>]*)>/, '<script$1>\nconst MOUNTS=' + JSON.stringify(JSON.parse(M)) + ';\n');
const tmp = path.join(os.tmpdir(), 'fieldsim_' + process.pid + '.html');
fs.writeFileSync(tmp, html);

// In-page helpers. Everything here runs against the game's own globals.
const HELPERS = `
  window.FS = {
    fakeImages(){
      for(const k of Object.keys(HULL_LEN)){
        const small = /^(fi|bo|sg|fc|ep)/.test(k) && HULL_LEN[k] < 80;
        const c = document.createElement('canvas');
        c.width = small ? 60 : 320; c.height = small ? 40 : 90;
        const g = c.getContext('2d'); g.fillStyle = '#888'; g.fillRect(0,0,c.width,c.height);
        IMGS[k] = c;
      }
      // Nothing is really loaded from disk here. Without this draw() stops
      // at its loading screen and none of the field is ever drawn.
      imgsLoaded = TOTAL; nebsLoaded = 0;
    },
    step(n){ for(let i=0;i<n;i++){ player.hp = player.maxHp; player.sh = player.maxSh;
             if(typeof lives!=='undefined') lives = 3; update(); if(i%25===0) draw(); } },
    // Shoot down every enemy fighter and bomber that is out of its vortex,
    // the bombs in flight and rocks closing on an escort - what a player
    // defending one does.
    killSmall(){ for(const e of enemies) if((e.type==='fighter'||e.type==='bomber') && !(e.warp>0)) e.hp = 0;
                 for(let i=eBullets.length-1;i>=0;i--) if(eBullets[i].kind==='bomb') eBullets.splice(i,1);
                 // Loose rocks about to hit an escort as well.
                 for(const e of enemies) if(e.type==='asteroid' && !e.scenery &&
                   allies.some(a=>!a.small && Math.hypot(a.x-e.x, a.y-e.y) < 180)) e.hp = 0; },
    killId(id){ for(const e of enemies) if(e.uid===id && !(e.warp>0)) e.hp = 0; },
    // Sit on a point, undisturbed, for n steps: how a scan is flown.
    hold(x, y, n){ for(let i=0;i<n;i++){ player.x = x; player.y = y; player.shDelay = 0; MOUSE.x = x; MOUSE.y = y; FS.step(1); } },
    // Step until cond() holds, clearing small craft every so often.
    // every: how often the small craft are cleared, in steps (default 200).
    until(cond, max, clear, all, every){ const ev = every || 200;
           for(let t=0;t<max;t+=20){ if(cond()) return t;
             if(clear && t%ev===0) FS.killSmall();
             if(all && t%200===0) for(const e of enemies){
               if(e.warp>0 || e.invuln || e.scenery) continue;
               // A prize is not shot down: its engines are, then it is taken.
               if(e.captureLock){ for(const s of (e.subs||[])) if(s.id==='engines'||s.id==='weapons'||s.id==='navigation'){ s.dead=true; s.hp=0; } continue; }
               // Scan targets are scanned first, as the player would.
               if(e.scanSubs && !e.scanned){ for(const s of e.subs) s.scanT = 1e9; continue; }
               if(e.scanLock && !e.scanned){ e.scanned = true; continue; }
               e.hp = 0; }
             FS.step(20); } return -1; },
    ids(id){ return byId(id); },
    enemyIds(){ return enemies.map(e=>e.uid||e.type); },
    allyIds(){ return allies.map(a=>a.uid||a.type); }
  };`;

const scenarios = [];
function scenario(name, query, body, noLaunch){ scenarios.push({name, query, body, noLaunch}); }

// ── Scenarios ──────────────────────────────────────────────────────────
scenario('M31 Der Aufstand', 'm=31', `
  const r = {};
  r.wave = wave; r.ship = player.ship;
  r.terranCall = ALLY_FAC_ON.terran===true && ALLY_FAC_ON.vasudan===false;
  FS.step(400);
  const a = allies.find(x=>x.uid==='A1');
  r.allyAtStart = !!a && a.img==='crleviathan';
  r.lockSet = !!a && a.defectLock===true;
  // Hammer her while she is still ours: she must not die before the turn.
  if(a){ a.hp = 1; FS.step(5); }
  r.survivesLock = !!allies.find(x=>x.uid==='A1');
  // Step by step up to the turn: where she was last as an ally, and where
  // she is in the first step as an enemy.
  let last = null, first = null;
  for(let k=0;k<8000 && !first;k++){
    if(k%200===0) FS.killSmall();
    const al = allies.find(x=>x.uid==='A1');
    if(al) last = {x:al.x, y:al.y};
    FS.step(1);
    const en = enemies.find(x=>x.uid==='A1');
    if(en) first = {x:en.x, y:en.y};
  }
  r.turnsInPlace = !!last && !!first && Math.abs(first.x-last.x) < 2 && Math.abs(first.y-last.y) < 2;
  const e = enemies.find(x=>x.uid==='A1');
  // From here on the allied wings could shoot her down or hit her engines
  // before she gets anywhere - that is the game - so for the checks below
  // she and her subsystems are made too tough for them.
  if(e){ e.hp = e.maxHp = 1e7; for(const s of e.subs||[]) s.hp = s.maxHp = 1e7; }
  FS.step(40);
  r.turned = !!e && !allies.some(x=>x.uid==='A1');
  r.ntfHull = !!e && e.img==='ntfcrleviathan';
  r.enemyShape = !!e && e.type==='cruiser' && e.side==='enemy' && !e.dead && e.hp>0;
  r.hasSubs = !!e && !!e.subs && e.subs.length===5;
  r.hasGuns = !!e && !!(e.guns||e.mounts||e.wpn||e.beams);
  r.facesWhereSheGoes = !!e && e.flip===needsFlip(e.img, false);
  const x0 = e ? e.x : 0;
  FS.step(200);
  r.waveOpenWhileSheLives = !waveOver;
  r.headsRight = !!e && e.x > x0;
  // Left alone she reaches the edge and jumps.
  const t = FS.until(()=>!!EV_LEFT['A1'], 8000, true);
  r.jumpsAtTheEdge = t>=0 && e.warpOut>0 && e.x < W;
  r.whileFullyOnScreen = !!e && e.x + IMGS[e.img].width*e.sc*0.5 <= W;
  FS.until(()=>!enemies.includes(e), 1000, false);
  r.goneAfterJump = !enemies.includes(e);
  FS.until(()=>waveOver || wave>31, 4000, true);
  r.waveEnds = waveOver || wave>31;
  return r;`);

scenario('M31 engines stop her', 'm=31', `
  FS.step(300);
  FS.until(()=>!enemies.some(e=>e.uid==='E1') && !spawnQ.some(q=>q.uid==='E1'), 6000, true);
  FS.step(40);
  const e = enemies.find(x=>x.uid==='A1');
  for(const s of e.subs) if(s.id==='engines'){ s.dead = true; s.hp = 0; }
  const x0 = e.x; FS.step(600);
  return {stopped: Math.abs(e.x-x0) < 0.01 && !EV_LEFT['A1']};`);

scenario('M32 Die Frachtroute', 'm=32', `
  const r = {};
  FS.step(300);
  const f = allies.filter(x=>x.uid==='F1');
  r.twoFreighters = f.length===2 && f.every(x=>x.img==='frposeidon');
  r.terranSide = f.every(x=>x.faction==='terran');
  r.medusas = enemies.filter(e=>e.uid==='B1').every(e=>e.img==='bomedusa') && enemies.some(e=>e.uid==='B1');
  r.fighterCover = enemies.some(e=>e.uid==='E1' && e.type==='fighter') || spawnQ.some(q=>q.uid==='E1');
  const x0 = f.length ? f[0].x : 0; FS.step(300);
  r.crossing = f.length>0 && f[0].x > x0;
  FS.until(()=>!enemies.some(e=>e.uid==='B1'), 4000, true);
  FS.step(300);
  r.secondRaid = enemies.some(e=>e.uid==='B2') || spawnQ.some(q=>q.uid==='B2');
  r.endsWhenThrough = FS.until(()=>waveOver, 20000, true) >= 0;
  return r;`);

scenario('M33 Die Relaisstation', 'm=33', `
  const r = {};
  FS.step(300);
  const s = enemies.find(e=>e.uid==='S1');
  r.faustus = !!s && s.img==='scfaustus';
  r.atGivenHeight = !!s && Math.abs(s.y-250) < 1;
  const x0 = s ? s.x : 0;
  FS.step(1200);
  r.staysPut = !!s && Math.abs(s.x-x0) < 1 && Math.abs(s.y-250) < 1;
  r.noFlak = !!s && flakHas(s)===false;
  r.guns = enemies.filter(e=>e.uid==='G1').length===4;
  // Reinforcements keep coming while she stands.
  FS.killSmall(); FS.step(900);
  r.reinforced = enemies.some(e=>e.type==='fighter' && !e.uid) || spawnQ.some(q=>!q.uid && /^fi_/.test(q.type));
  const before = SHOCKS.length;
  FS.killId('S1'); FS.step(3);
  r.bigBlast = SHOCKS.some(k=>k.rMax===300);
  FS.killSmall(); FS.step(1200); FS.killSmall(); FS.step(600);
  r.reinfOff = evReinf===false;
  return r;`);

scenario('M34 Die Flakwand', 'm=34', `
  const r = {};
  score = 20000;   // enough for the Artemis to be open in this cycle
  FS.step(400);
  const k = enemies.filter(e=>e.uid==='K1');
  r.twoAeolus = k.length===2 && k.every(e=>e.img==='ntfcraeolus');
  r.flak = k.every(e=>flakHas(e));
  r.noHangarYet = !allies.some(a=>a.uid==='A1');
  FS.until(()=>!enemies.some(e=>e.uid==='E1') && !spawnQ.some(q=>q.uid==='E1'), 5000, true);
  FS.step(400);
  const o = allies.find(a=>a.uid==='A1');
  r.orion = !!o && o.img==='deorionright';
  tickShipUnlocks();
  r.bomberOffered = shipOffered('boartemis') && shipSwapReady();
  return r;`);

scenario('M35 Der Ueberlaeufer', 'm=35', `
  const r = {};
  FS.step(300);
  const d = allies.find(a=>a.uid==='A1');
  r.ntfDeimos = !!d && d.img==='ntfcodeimos' && d.type==='corvette';
  r.comesFromTheRight = !!d && d.x > W*0.6;
  r.facesLeft = !!d && d.flip===needsFlip('ntfcodeimos', true);
  r.crossing = !!d && d.transit===true;
  r.firstWingHuntsHer = waveHunt==='A1';
  const x0 = d ? d.x : 0; FS.step(200);
  r.headsLeft = !!d && d.x < x0;
  FS.until(()=>!enemies.some(e=>e.uid==='E1') && !spawnQ.some(q=>q.uid==='E1'), 5000, true);
  FS.step(20);
  r.reinforcementsOn = evReinf===true;
  r.followUpsScreen = waveHunt==='';
  r.rearm = corvetteOnField();
  r.notOnCallMenu = ALLY_ORDER.indexOf('ntf_deimos')<0;
  // What is checked here is the crossing, not the balance - Silvio plays
  // that. So she is made too tough to lose on the way.
  d.hp = d.maxHp = 1e7;
  for(const s of d.subs||[]) s.hp = s.maxHp = 1e7;    // engines too: dead engines stop a crossing
  const got = FS.until(()=>{ if(allies.includes(d)) d.hp = d.maxHp; return !allies.some(a=>a.uid==='A1'); }, 9000, true);
  r.getsAcross = got>=0 && !guardLost;
  r.leftCounts = !!EV_LEFT['A1'];
  r.nothingMoreComes = evReinf===false && spawnQ.length===0;
  FS.until(()=>waveOver, 4000, true);
  r.waveEnds = waveOver;
  return r;`);

scenario('M36 Die Iceni', 'm=36', `
  const r = {};
  const s0 = score = 5000;
  FS.step(300);
  const i = enemies.find(e=>e.uid==='V1');
  r.iceni = !!i && i.iceni===true && i.img==='coiceni';
  r.noNavigation = !!i && !!i.subs && i.subs.length===4 && subOK(i,'navigation');
  r.deadline = !!i && i.fleeT>0 && i.fleeT <= 25*TICK_HZ;
  FS.step(600);
  r.wholeHullOnScreen = !!i && i.x + IMGS[i.img].width*i.sc*0.5 <= W;
  const t = FS.until(()=>!enemies.some(e=>e.uid==='V1'), 6000, false);
  r.jumpsOut = t>=0 && icenEscapes===1;
  r.noPenalty = score >= s0;
  r.fenris = enemies.some(e=>e.uid==='K1' && e.img==='ntfcrfenris');
  return r;`);

scenario('Cycle change 30 -> 31', 'm=30', `
  const r = {};
  r.startsVasudan = player.ship==='fitoth' && ALLY_FAC_ON.vasudan===true;
  score = 90000;
  // Clear wave 30 by force and let the jump happen.
  for(let k=0;k<60 && wave===30;k++){ for(const e of enemies) if(!(e.warp>0) && !e.invuln) e.hp=0; FS.step(200); }
  r.wave = wave;
  r.myrmidon = player.ship==='fimyrmidon';
  r.oneHull = shipUnlocked===1 && cycleBase===score - (score-cycleBase);
  r.baseSet = cycleBase >= 90000;
  r.terran = ALLY_FAC_ON.terran===true && ALLY_FAC_ON.vasudan===false;
  return r;`);

scenario('M13 both transports on time', 'm=13', `
  FS.step(300);
  return {bothTransports: allies.filter(a=>a.uid==='T1').length===2};`);

// Every written mission has to come to an end when its enemies go down,
// with nothing thrown on the way. Enemy ships are cleared every two seconds
// once they are out of their vortex - a player who hits everything.
// Scan missions (12, 23) need the player to fly the scan and are left out.
for(let m=1;m<=54;m++) if(m!==12 && m!==23) scenario('M' + String(m).padStart(2,'0') + ' plays to the end', 'm=' + m, `
  const t = FS.until(()=>waveOver, 40000, false, true);
  ITEMS.length = 0;     // pickups hold the jump open until they expire
  const j = FS.until(()=>wave === ${m}+1, 6000, false, false);
  return {ends: t >= 0, nextWave: j >= 0};`);

scenario('Pickups are drawn to the ship', 'm=1', `
  FS.step(200);
  const r = {};
  tickets.cruiser = 0;
  ITEMS.push({x:player.x+100, y:player.y, vx:ITEM_DRIFT, vy:0, kind:'cruiser', life:5000});
  ITEMS.push({x:player.x+400, y:player.y+100, vx:0, vy:0, kind:'repair', life:5000});
  const far = ITEMS[1];
  FS.step(60);
  r.nearOneCollected = tickets.cruiser===1;
  r.farOneLeftAlone = ITEMS.includes(far) && !far.caught;
  // Caught, it keeps following even if the ship pulls away.
  player.x = 100; player.y = 250;
  ITEMS.push({x:210, y:250, vx:0, vy:0, kind:'corvette', life:5000});
  const c = ITEMS[ITEMS.length-1];
  FS.step(1);
  r.caught = c.caught===true;
  let got = false;
  for(let k=0;k<200 && !got;k++){ player.x = 60; player.y = 250; FS.step(1); got = !ITEMS.includes(c); }
  r.followsAndArrives = got;
  return r;`);

scenario('Title: fullscreen button', '', `
  const r = {};
  let calls = 0;
  toggleFullscreen = function(){ calls++; };
  draw();
  const b = window._titleFsRect;
  r.shown = !!b && b.x >= 0 && b.x + b.w <= W && b.y >= 0 && b.y + b.h <= H;
  r.clearOfTheTitle = !!b && b.y + b.h < 128 - 54;
  const cr = CVS.getBoundingClientRect();
  const click = (gx, gy)=>{
    const ev = new MouseEvent('mousedown', {button:0, bubbles:true,
      clientX: cr.left + gx*cr.width/W, clientY: cr.top + gy*cr.height/H});
    CVS.dispatchEvent(ev);
    CVS.dispatchEvent(new MouseEvent('mouseup', {button:0, bubbles:true}));
  };
  click(b.x + b.w/2, b.y + b.h/2);
  r.buttonSwitches = calls===1;
  r.andDoesNotStartTheRun = GS==='title';
  document.dispatchEvent(new KeyboardEvent('keydown', {code:'KeyF'}));
  document.dispatchEvent(new KeyboardEvent('keyup', {code:'KeyF'}));
  r.fKeyOnTheTitle = calls===2 && GS==='title';
  click(W/2, H/2);
  r.elsewhereStartsTheRun = GS==='playing' && calls===2;
  return r;`, true);

scenario('M37 Die Unsichtbaren', 'm=37', `
  const r = {};
  FS.step(400);
  const lokis = enemies.filter(e=>e.uid==='E1');
  r.lokis = lokis.length>0 && lokis.every(e=>e.img==='filoki');
  r.noLockOnThem = lokis.length>0 && lokis.every(e=>!canLockOn(e));
  r.inPlainSight = lokis.every(e=>!e.hidden && !e.cloak && e.alpha===undefined);
  // An enemy fighter of any other hull can still be locked.
  const other = {side:'enemy', img:'fiherc'};
  r.othersStillLockable = canLockOn(other);
  // A player Loki later on keeps its own rules: the no-lock is enemy only.
  r.onlyTheEnemySide = canLockOn({side:'ally', img:'filoki'});
  // Clear them lot by lot and note every lot that shows up.
  const seen = {};
  FS.until(()=>{ for(const e of enemies) if(e.uid){ seen[e.uid] = seen[e.uid] || e.img; } return waveOver; }, 20000, true);
  r.threeLotsOfLokis = seen.E1==='filoki' && seen.E2==='filoki' && seen.E3==='filoki';
  return r;`);

scenario('M38 Die Kaperung', 'm=38', `
  const r = {};
  score = 1000;
  FS.step(400);
  const d = enemies.find(e=>e.uid==='D1');
  r.deimos = !!d && d.img==='ntfcodeimos';
  r.midField = !!d && Math.abs(d.y-260) < 1;
  r.headsRight = !!d && d.escaping>0 && d.flip===needsFlip(d.img, false);
  r.saysWhatToDo = missionObj==='DISABLE THE DEIMOS - ENGINES AND WEAPONS';
  damageEnemy(d, d.maxHp*5, d.x, d.y, true, 'bolt'); FS.step(3);
  r.cannotBeDestroyed = enemies.includes(d) && d.hp > 0;
  const kill = id=>{ for(const s of d.subs) if(s.id===id){ s.dead=true; s.hp=0; } };
  kill('engines');
  const x0 = d.x; FS.step(300);
  r.enginesStopHer = Math.abs(d.x-x0) < 0.01;
  r.noElysiumWhileHerGunsWork = !allies.some(a=>a.uid==='T1') && !spawnQ.some(q=>q.uid==='T1');
  kill('weapons'); FS.step(2);
  r.newObjective = missionObj==='COVER THE ELYSIUM';
  FS.step(200);
  r.elysiumComesOnceBothAreDown = allies.some(a=>a.uid==='T1' && a.img==='trelysium') || spawnQ.some(q=>q.uid==='T1') || !!EV_DOCK['T1'];
  const got = FS.until(()=>!!EV_DOCK['T1'], 9000, true);
  FS.step(5);
  r.docks = got>=0;
  r.taken = d.captured===true && !!EV_TAKEN['D1'] && (d.warpOut>0 || !enemies.includes(d));
  r.completeCard = !!objCard && objCard.head==='OBJECTIVE COMPLETE' && objCard.txt==='DEIMOS CAPTURED';
  r.pointsForHer = score >= 1000 + (d.pts||0);
  FS.until(()=>!enemies.includes(d), 1000, false);
  FS.step(50);
  r.noFailureAfterwards = !(objCard && objCard.tone==='fail');
  r.leavesWithoutPenalty = !enemies.includes(d) && score >= 1000 + (d.pts||0);
  return r;`);

scenario('M38 Elysium lost: she can die', 'm=38', `
  FS.step(400);
  const d = enemies.find(e=>e.uid==='D1');
  for(const s of d.subs) if(s.id==='engines'||s.id==='weapons'){ s.dead=true; s.hp=0; }
  FS.until(()=>allies.some(a=>a.uid==='T1'), 2000, true);
  for(const a of allies) if(a.uid==='T1') a.hp = 0;
  FS.step(30);
  const freed = d.captureLock===false;
  const failCard = !!objCard && objCard.tone==='fail' && objCard.txt==='ELYSIUM LOST';
  d.hp = 0; FS.step(300);
  return {freed: freed, failCard: failCard, thenDestroyable: !enemies.includes(d) && !EV_LEFT['D1']};`);

scenario('M38 left alone she jumps at the edge', 'm=38', `
  FS.step(300);
  const d = enemies.find(e=>e.uid==='D1');
  const t = FS.until(()=>!!EV_LEFT['D1'], 8000, true);
  FS.step(2);
  return {jumps: t>=0 && d.warpOut>0 && !d.captured, onScreen: d.x + IMGS[d.img].width*d.sc*0.5 <= W,
          failCard: !!objCard && objCard.tone==='fail' && objCard.txt==='THE DEIMOS GOT AWAY'};`);

scenario('M39 Die Gasernte', 'm=39', `
  const r = {};
  r.nebula = nebulaOn()===true;
  FS.step(1600);
  const m = enemies.filter(e=>/^M/.test(e.uid||''));
  r.threeMiners = m.length===3 && m.every(e=>e.img==='gmzephyrus');
  r.running = m.every(e=>e.escaping>0);
  r.fenris = enemies.some(e=>e.uid==='K1' && e.img==='ntfcrfenris');
  const m1 = enemies.find(e=>e.uid==='M1');
  m1.hp = 0; FS.step(3);
  r.giantBlast = SHOCKS.some(k=>k.rMax===400);
  return r;`);

scenario('M40 Der Sensorsturm', 'm=40', `
  const r = {};
  r.nebula = nebulaOn()===true;
  const seen = {};
  const note = ()=>{ for(const e of enemies) if(e.uid) seen[e.uid]=1; };
  const t = FS.until(()=>{ note(); return empOut>0; }, 6000, true);
  r.stormHits = t>=0;
  r.noLockInTheStorm = !canLockOn({side:'enemy', img:'fihercmk2'});
  r.orion = allies.some(a=>a.uid==='A1' && a.img==='deorionright');
  FS.until(()=>{ note(); return waveOver; }, 40000, true);
  r.threeRounds = ['E1','B1','E2','B2','E3','B3'].every(k=>seen[k]);
  if(!r.threeRounds) r.seen = Object.keys(seen).join() + ' | ' + EV.map(e=>e.a+'>'+e.w+'>'+(e.wa||'')+':'+e.done).join(' ');
  return r;`);

scenario('M41 Das Lazarett', 'm=41', `
  const r = {};
  FS.step(300);
  const h = allies.find(a=>a.uid==='H1');
  r.hippocrates = !!h && h.img==='mehippocrates';
  r.hunted = waveHunt==='H1';
  const x0 = h ? h.x : 0; FS.step(300);
  r.crossesSlowly = !!h && h.x > x0 && (h.x-x0) < 100;
  r.bombers = enemies.some(e=>e.uid==='B1' && e.img==='bomedusa');
  const orig = drawHullBlocks; let barFor = false;
  drawHullBlocks = function(e){ if(e===h) barFor = true; return orig.apply(this, arguments); };
  draw(); drawHullBlocks = orig;
  r.hullBarOnTheHippocrates = barFor;
  const got = FS.until(()=>!allies.includes(h), 9000, true);
  r.getsThrough = got>=0 && !guardLost;
  return r;`);

scenario('M42 Die Hecate', 'm=42', `
  const r = {};
  FS.step(400); draw();
  r.saysWhatToDo = missionObj==='DISABLE HECATE WEAPONS' && objPinned==='DISABLE HECATE WEAPONS';
  const v = enemies.find(e=>e.uid==='V1');
  r.hecate = !!v && v.img==='ntfdehecate';
  r.orion = allies.some(a=>a.uid==='A1');
  FS.until(()=>!enemies.some(e=>e.uid==='E1') && !spawnQ.some(q=>q.uid==='E1'), 5000, true);
  FS.step(20);
  r.reinforcementsOn = evReinf===true;
  for(const s of v.subs) if(s.id==='weapons'){ s.dead=true; s.hp=0; }
  FS.step(20); draw();
  r.nextStep = missionObj==='DESTROY THE HECATE' && !!objCard && objCard.head==='NEW OBJECTIVE' && objCard.txt==='DESTROY THE HECATE';
  r.disarmedWithdraws = v.fleeT>0;
  // A destroyer goes down in a death roll that takes a while.
  v.hp = 0;
  r.completeCard = FS.until(()=>{ draw(); return !!objCard && objCard.head==='OBJECTIVE COMPLETE'
                                          && objCard.txt==='HECATE DESTROYED'; }, 2000, false) >= 0;
  FS.step(300);
  r.reinforcementsOffWhenShesGone = evReinf===false;
  return r;`);

scenario('M42 she withdraws: failed', 'm=42', `
  FS.step(400);
  const v = enemies.find(e=>e.uid==='V1');
  // Too tough for the Orion and her wings, and her navigation with it -
  // with that shot out she could not jump at all.
  v.hp = v.maxHp = 1e7;
  for(const s of v.subs){ if(s.id==='weapons'){ s.dead=true; s.hp=0; } else s.hp = s.maxHp = 1e7; }
  const t = FS.until(()=>!!objCard && objCard.tone==='fail', 6000, true);
  const r = {failCard: t>=0 && objCard.txt==='THE HECATE WITHDREW', notComplete: !(objCard && objCard.tone==='done')};
  FS.until(()=>!enemies.includes(v), 1000, false); FS.step(50);
  r.reinfOff = evReinf===false;
  return r;`);

scenario('M33 says what to do', 'm=33', `
  FS.step(300);
  const ok1 = missionObj==='DESTROY THE FAUSTUS RELAY';
  const s1 = enemies.find(e=>e.uid==='S1'); s1.hp = 0; FS.step(5);
  return {saysWhatToDo: ok1, completeCard: !!objCard && objCard.head==='OBJECTIVE COMPLETE' && objCard.txt==='RELAY DESTROYED'};`);

scenario('Automatic objectives: card, then the line', 'm=35', `
  // M35 states no objective of its own; PROTECT THE ... comes from the field.
  const r = {};
  const t = FS.until(()=>{ draw(); return !!objCard && objCard.head==='NEW OBJECTIVE'; }, 1500, false);
  r.cardForTheNewObjective = t>=0 && /^PROTECT THE /.test(objCard.txt);
  // Its clock starts once the jump in is over, so wait for it rather than
  // count steps.
  r.cardGoesAgain = FS.until(()=>{ draw(); return objCard===null; }, OBJ_CARD_TIME*3, false) >= 0;
  r.lineKeepsIt = /^PROTECT THE /.test(objPinned);
  return r;`);

scenario('New look: no Courier left in these', 'm=36', `
  FS.step(700);
  showFps = true; showObj = true;
  const used = []; const of = ctx.fillText;
  let inside = 0;
  const wrap = name=>{ const f = window[name]; window[name] = function(){ inside++; try{ return f.apply(this, arguments); } finally{ inside--; } }; };
  ['drawFieldBanner','drawFleeWarning','drawFps','drawObjCount','drawPaused',
   'drawSubMsgs','drawTicketMsgs','drawItems','drawHullBlocks','drawSubsystems'].forEach(wrap);
  // Something in each of them to draw.
  const cap = enemies.find(e=>e.type==='cruiser'||e.type==='corvette') || enemies[0];
  SUB_MSGS.push({x:300, y:250, txt:'DOCKED', life:150, ml:150, ally:true, tone:'good'});
  TICKET_MSGS.push({x:320, y:260, kind:'cruiser', life:150, ml:150, rep:false});
  ITEMS.push({x:340, y:270, vx:0, vy:0, kind:'life', life:500});
  ITEMS.push({x:360, y:270, vx:0, vy:0, kind:'corvette', life:500});
  notice('TEST NOTICE', 'info');
  ctx.fillText = function(){ if(inside) used.push(ctx.font); return of.apply(this, arguments); };
  objAnnounce('NEW OBJECTIVE', 'TEST', 'new'); objCard.t0 = fc - 40;
  draw();
  userPaused = true; syncPause(); draw();
  ctx.fillText = of;
  return {somethingDrawn: used.length>=4, fleeShown: fleeingEnemies().length>0, noCourier: used.every(f=>!/Courier/.test(f))};`);

scenario('Notices: a column, not the field', 'm=31', `
  const r = {};
  FS.step(300);
  score = cycleBase + 4000; tickShipUnlocks();
  r.unlockIsANotice = NOTICES.length>0 && NOTICES[0].txt==='GTF HERCULES AVAILABLE' && NOTICES[0].tone==='unlock';
  r.notInTheField = !SUB_MSGS.some(m=>/AVAILABLE/.test(m.txt));
  const plates = []; const op = thPlate;
  thPlate = function(x,y,w,h){ plates.push({x,y,w,h}); return op.apply(this, arguments); };
  draw(); thPlate = op;
  r.onTheLeftUnderTheBar = plates.some(p=>p.x===8 && p.y>=HUD_H+6 && p.h===18);
  for(let i=0;i<5;i++) notice('N'+i, 'info');
  r.atMostThreeNewestFirst = NOTICES.length===3 && NOTICES[0].txt==='N4' && NOTICES[2].txt==='N2';
  FS.step(NOTICE_TIME+30); draw();
  r.theyGoAgain = NOTICES.length===0;
  return r;`);

scenario('Notices: radio lines of a mission', 'm=34', `
  FS.step(400);
  FS.until(()=>NOTICES.some(n=>/ORION INBOUND/.test(n.txt)), 6000, true);
  return {orionInbound: NOTICES.some(n=>n.txt==='GTD ORION INBOUND - HANGAR OPEN' && n.tone==='info'),
          notInTheField: !SUB_MSGS.some(m=>/INBOUND/i.test(m.txt))};`);

scenario('Hull band: calm, lit by a hit, full when nearly dead', 'm=42', `
  FS.step(400);
  const v = enemies.find(e=>e.uid==='V1');
  const r = {};
  v._hbHit = fc - HB_HOT - 1; v._hbLast = v.hp; draw();
  r.calmIsHalf = Math.abs(v._hbAlpha - HB_CALM) < 1e-9;
  v._hbLast = v.hp + 10; draw();
  r.aHitLightsItUp = Math.abs(v._hbAlpha - 1) < 1e-9;
  v._hbHit = fc - HB_HOT/2; v._hbLast = v.hp; draw();
  r.andItSettles = v._hbAlpha > HB_CALM && v._hbAlpha < 1;
  v._hbHit = fc - HB_HOT - 1; v.hp = v.maxHp*0.1; v._hbLast = v.hp; draw();
  r.nearlyDeadStaysFull = Math.abs(v._hbAlpha - 1) < 1e-9;
  r.colourRunsSmoothly = hullBandCol(1)==='rgb(60,224,106)' && hullBandCol(0.5)==='rgb(255,204,68)'
                      && hullBandCol(0)==='rgb(255,74,51)' && hullBandCol(0.75)!==hullBandCol(0.8);
  return r;`);

scenario('Pickups light up the bar, not the field', 'm=31', `
  const r = {};
  FS.step(300);
  const take = (kind)=>{ ITEMS.push({x:player.x+5, y:player.y, vx:0, vy:0, kind:kind, life:500}); FS.step(3); };
  TICKET_MSGS.length = 0; BAR_PULSE = {};
  take('cruiser');
  r.ticketLightsItsSymbol = !!BAR_PULSE['ticket:cruiser'] && !BAR_PULSE['ticket:cruiser'].weak;
  r.noWordsInTheField = TICKET_MSGS.length===0;
  // The harness puts the hull back to full every step, so these two take
  // the pickup straight through updateItems().
  const takeNow = (kind)=>{ ITEMS.push({x:player.x+5, y:player.y, vx:0, vy:0, kind:kind, life:500}); updateItems(); };
  player.hp = player.maxHp*0.5; takeNow('repair');
  r.repairLightsTheHull = !!BAR_PULSE.hull && !BAR_PULSE.hull.weak;
  // The harness keeps the hull at full, so this one changes nothing.
  delete BAR_PULSE.hull; take('repair');
  r.repairAtFullIsDimmed = !!BAR_PULSE.hull && BAR_PULSE.hull.weak;
  lives = LIVES_MAX - 1; take('life');
  r.lifeLightsLives = !!BAR_PULSE.lives && !BAR_PULSE.lives.weak;
  lives = LIVES_MAX; delete BAR_PULSE.lives; takeNow('life');
  r.lifeAtMaxIsDimmed = !!BAR_PULSE.lives && BAR_PULSE.lives.weak;
  // Drawn: the glow ring goes round the hull bar and the ticket cell.
  const rings = []; const og = thGlowPath;
  thGlowPath = function(x,y,w,h){ rings.push({x,y,w,h}); return og.apply(this, arguments); };
  barPulse('hull'); barPulse('ticket:cruiser'); FS.step(40); draw(); thGlowPath = og;
  r.ringAroundHull = rings.some(g=>g.x===181 && g.w===116);
  r.ringAroundTicket = rings.some(g=>g.x===533 && g.w===58);
  // Its time is up: the pulse is over and gone. (Stepping the game to get
  // there would let loot from the fight light it up again.)
  barPulse('hull'); BAR_PULSE.hull.t0 = fc - BAR_PULSE_T;
  r.andItEnds = barPulseLevel('hull')===0 && !BAR_PULSE.hull;
  r.softNotHard = (()=>{ barPulse('hull'); const a = barPulseLevel('hull'); FS.step(10); const b = barPulseLevel('hull'); return a===0 && b>0 && b<1; })();
  return r;`);

scenario('Mission reward ticket: in the bar', 'm=35', `
  FS.step(300);
  const d = allies.find(a=>a.uid==='A1');
  d.hp = d.maxHp = 1e7; for(const s of d.subs||[]) s.hp = s.maxHp = 1e7;
  TICKET_MSGS.length = 0;
  // Rocks and wreckage take a share of the hull rather than points, so a
  // big hull alone does not keep her alive: she is topped up as she goes.
  const t = FS.until(()=>{ if(allies.includes(d)) d.hp = d.maxHp; return waveOver; }, 12000, true);
  const k = Object.keys(BAR_PULSE).find(x=>/^ticket:/.test(x));
  const r = {rewarded: t>=0 && !!k, notInTheField: TICKET_MSGS.length===0};
  if(!r.rewarded) r.dbg = {t, gl:guardLost, gw:guardWanted, gs:guardSpawned, keys:Object.keys(BAR_PULSE), wave, fc};
  return r;`);

scenario('A corvette arrives: REARM calls', 'm=35', `
  BAR_PULSE = {};
  // The button becomes usable once she is there and the jump in is over.
  const t = FS.until(()=>!!BAR_PULSE.rearm, 3000, true);
  const called = rearmReady();
  const t0 = BAR_PULSE.rearm ? BAR_PULSE.rearm.t0 : -1;
  FS.step(100);
  return {rearmCalls: t>=0 && called, onlyOnceNotEveryStep: !BAR_PULSE.rearm || BAR_PULSE.rearm.t0===t0};`);

scenario('A destroyer arrives: SHIP SWITCH calls', 'm=34&ships=8', `
  BAR_PULSE = {};
  FS.step(300);
  const before = !!BAR_PULSE.swap;
  const t = FS.until(()=>shipSwapReady(), 6000, true);
  FS.step(2);
  return {notBeforeTheOrion: !before, swapCalls: t>=0 && !!BAR_PULSE.swap};`);

scenario('M49 Das Reparaturdock', 'm=49', `
  const r = {};
  FS.step(300);
  const d = enemies.find(e=>e.uid==='D1');
  r.arcadiaBehind = enemies.some(e=>e.uid==='S1' && e.img==='inarcadia' && e.invuln);
  r.deimosHurt = !!d && Math.abs(d.hp/d.maxHp - 0.25) < 0.02;
  r.saysWhat = missionObj==='DESTROY THE DEIMOS BEFORE HER REPAIRS ARE DONE';
  let t1 = null;
  FS.until(()=>{ t1 = enemies.find(e=>e.uid==='T1'); return !!t1; }, 2000, true);
  r.transportComes = !!t1 && t1.img==='trargo';
  // Hull just before the dock, stepped singly so nothing else gets in.
  let h0 = d.hp, got = -1;
  for(let i=0;i<6000;i++){ if(EV_DOCK['T1']){ got = i; break; } h0 = d.hp; if(i%200===0) FS.killSmall(); FS.step(1); }
  r.dockRepairsAQuarter = got>=0 && Math.abs((d.hp-h0)/d.maxHp - 0.25) < 0.03;
  r.transportJumpsOut = t1.warpOut>0 || !enemies.includes(t1);
  // All three through: she is whole and jumps. That is a failure.
  for(const e of enemies) if(e.type==='fighter'||e.type==='bomber') e.hp = 0;
  const f = FS.until(()=>!!objCard && objCard.tone==='fail', 9000, true);
  r.repairedSheJumps = f>=0 && objCard.txt==='THE DEIMOS WAS REPAIRED' && !!EV_DOCK['T3'];
  return r;`);

scenario('M49 destroyed in time', 'm=49', `
  const r = {};
  FS.step(700);
  const d = enemies.find(e=>e.uid==='D1');
  d.hp = 0;
  const c = FS.until(()=>!!objCard && objCard.txt==='DEIMOS DESTROYED', 1500, false);
  r.completeCard = c>=0;
  r.noMoreTransports = !spawnQ.some(q=>/^T/.test(q.uid||''));
  // One already on its way has nothing left to dock with and leaves.
  const t = enemies.find(e=>/^T/.test(e.uid||''));
  if(t){ FS.step(300); r.strayLeaves = !enemies.includes(t) || t.warpOut>0; } else r.strayLeaves = true;
  return r;`);

scenario('M50 Der Durchbruch', 'm=50', `
  const r = {};
  FS.step(500);
  const k = enemies.filter(e=>e.uid==='K1');
  r.twoAeolus = k.length===2 && k.every(e=>e.img==='ntfcraeolus');
  r.sentryLine = enemies.filter(e=>e.uid==='G1' && e.type==='sentry').length===4;
  r.noOrionYet = !allies.some(a=>a.uid==='A1');
  r.saysBreak = missionObj==='BREAK THE BLOCKADE - DESTROY AN AEOLUS';
  k[0].hp = 0;
  let o = null;
  FS.until(()=>{ o = allies.find(a=>a.uid==='A1'); return !!o; }, 2000, true);
  r.orionThroughTheGap = !!o && o.transit===true;
  // She warps in on screen instead of popping up at the edge.
  const _oi = IMGS[o.img], _oh = _oi ? _oi.width*o.sc*0.5 : 0;
  r.orionWarpsIn = o.warp>0 && o.x - _oh >= 0;
  FS.step(2);
  r.newObjective = missionObj==='GET THE ORION THROUGH';
  o.hp = o.maxHp = 1e7; for(const s of o.subs||[]) s.hp = s.maxHp = 1e7;
  const t = FS.until(()=>{ if(allies.includes(o)) o.hp = o.maxHp; return !!objCard && objCard.txt==='THE ORION IS THROUGH'; }, 9000, true);
  r.throughCard = t>=0;
  return r;`);

scenario('M51 Die Rueckeroberung', 'm=51', `
  const r = {};
  score = 1000;
  FS.step(300);
  const s = enemies.find(e=>e.uid==='S1');
  r.armedArcadia = !!s && s.type==='station' && s.armed && !!s.subs && s.subs.some(x=>x.id==='weapons');
  r.noEnginesNoNavigation = !!s && !s.subs.some(x=>x.id==='engines' || x.id==='navigation');
  // Her guns fire.
  FS.killSmall(); eBullets.length = 0;
  let shots = 0;
  for(let i=0;i<400;i++){ FS.killSmall(); const n0 = eBullets.length; FS.step(1); shots += Math.max(0, eBullets.length-n0); }
  r.gunsFire = shots > 0;
  damageEnemy(s, s.maxHp*5, s.x, s.y, true, 'bolt'); FS.step(3);
  r.cannotBeDestroyed = enemies.includes(s) && s.rollT==null && s.hp>0;
  r.noElysiumYet = !allies.some(a=>a.uid==='T1');
  for(const x of s.subs) if(x.id==='weapons'){ x.dead = true; x.hp = 0; }
  FS.step(3);
  r.coverTheElysium = missionObj==='COVER THE ELYSIUM';
  // Guns out: she falls silent.
  shots = 0;
  for(let i=0;i<300;i++){ FS.killSmall(); const n0 = eBullets.length; FS.step(1); shots += Math.max(0, eBullets.length-n0); }
  r.silentWithoutGuns = shots===0;
  let el = null;
  FS.until(()=>{ el = allies.find(a=>a.uid==='T1'); return !!el; }, 3000, true);
  el.hp = el.maxHp = 1e7;
  const hold = FS.until(()=>{ el.hp = el.maxHp; return el.holdT!=null; }, 9000, true);
  FS.step(400);
  r.boardingTakesTime = hold>=0 && !s.captured;
  const got = FS.until(()=>{ if(allies.includes(el)) el.hp = el.maxHp; return !!EV_DOCK['T1']; }, 3000, true);
  FS.step(3);
  r.takenAndStays = got>=0 && s.captured===true && enemies.includes(s) && !(s.warpOut>0) && s.scenery===true;
  r.completeCard = !!objCard && objCard.txt==='ARCADIA RETAKEN';
  const w = FS.until(()=>waveOver, 6000, true);
  r.waveEnds = w>=0;
  return r;`);

scenario('M51 both Elysiums lost: failed', 'm=51', `
  const r = {};
  FS.step(300);
  const s = enemies.find(e=>e.uid==='S1');
  for(const x of s.subs) if(x.id==='weapons'){ x.dead = true; x.hp = 0; }
  let el = null;
  FS.until(()=>{ el = allies.find(a=>a.uid==='T1'); return !!el; }, 3000, true);
  el.hp = 0;
  let e2 = null;
  FS.until(()=>{ e2 = allies.find(a=>a.uid==='T2'); return !!e2; }, 3000, true);
  r.secondComes = !!e2;
  e2.hp = 0;
  const f = FS.until(()=>!!objCard && objCard.tone==='fail', 1500, false);
  r.failCard = f>=0 && objCard.txt==='BOTH ELYSIUMS LOST';
  r.ntfKeepsHer = enemies.includes(s) && s.scenery===true && !s.captured;
  const w = FS.until(()=>waveOver, 6000, true, true);
  r.waveEnds = w>=0;
  return r;`);

scenario('M52 Das Artilleriefeuer', 'm=52', `
  const r = {};
  tickets.cruiser = 1;
  FS.step(400);
  const ms = allies.filter(a=>a.uid==='M1' || a.uid==='M2');
  r.twoMjolnirs = ms.length===2 && ms.every(m=>m.img==='sgmjolnir' && m.platform && !m.subs && m.beams && m.beams.some(b=>b.large));
  const m1 = ms.find(m=>m.uid==='M1'), m2 = ms.find(m=>m.uid==='M2');
  r.inPlace = !!m1 && !!m2 && Math.abs(m1.x-70)<1 && Math.abs(m1.y-140)<1 && Math.abs(m2.y-360)<1;
  r.deimosAtTheBottom = allies.some(a=>a.uid==='A1' && a.img==='codeimos' && Math.abs(a.y-440)<1);
  r.supportStillCallable = allyReady();
  const _v1 = enemies.find(e=>e.uid==='V1');
  r.shorterDeadline = !!_v1 && _v1.fleeT>0 && _v1.fleeT <= 30*TICK_HZ;
  // They take turns: never both early in their charge together.
  let together = 0, charged = {M1:0, M2:0};
  for(let i=0;i<4000;i+=10){ FS.killSmall(); for(const e of enemies) if(e.fleeT>0) e.fleeT = 1e6;
    FS.step(10);
    const early = ms.filter(m=>m.beams.some(b=>b.state==='charging' && (b.chargeMax - b.timer) < b.chargeMax*0.4));
    if(early.length===2) together++;
    for(const m of ms) if(m.beams.some(b=>b.state==='firing')) charged[m.uid]++; }
  r.takeTurns = together===0 && charged.M1>0 && charged.M2>0;
  // Two lanes, never more than two NTF capital ships at once.
  let most = 0; const seen = {};
  FS.until(()=>{ const caps = enemies.filter(e=>/^V/.test(e.uid||'') && !(e.warp>0));
    most = Math.max(most, caps.length); for(const e of caps) seen[e.uid] = e;
    for(const e of caps) if(e.warp<=0 && e.x < W-60){ e.hp = 0; }
    return ['V1','V2','V3','V4','V5','V6'].every(k=>EV_SEEN[k]) && !byId('V5').length && !byId('V6').length; }, 20000, true);
  r.allSixCome = wave===52 && ['V1','V2','V3','V4','V5','V6'].every(k=>EV_SEEN[k]);
  r.neverMoreThanTwo = most<=2;
  r.completeCard = FS.until(()=>!!objCard && objCard.txt==='NTF BATTLE GROUP DESTROYED', 300, false) >= 0;
  // No jump drive: the Mjolnirs stay until the field goes dark.
  FS.until(()=>waveOver, 6000, true, true);
  FS.step(60);
  r.mjolnirsStay = allies.includes(m1) && !(m1.warpOut>0) && allies.includes(m2);
  return r;`);

scenario('M53 Der Gegenangriff', 'm=53', `
  const r = {};
  tickets.cruiser = 1;
  FS.step(300);
  const a1 = allies.find(a=>a.uid==='A1'), a2 = allies.find(a=>a.uid==='A2');
  r.fleetPlaced = !!a1 && !!a2 && Math.abs(a1.y-170)<60 && Math.abs(a2.y-390)<60;
  r.noCallWhileBothStand = !allyReady();
  r.noEnemyDestroyersYet = !enemies.some(e=>e.uid==='V1'||e.uid==='V2');
  FS.until(()=>enemies.some(e=>e.uid==='V1') && enemies.some(e=>e.uid==='V2'), 2000, true);
  r.theyJumpIn = enemies.some(e=>e.uid==='V1' && e.img==='ntfdehecate') && enemies.some(e=>e.uid==='V2' && e.img==='ntfdeorion');
  FS.step(2);
  r.newObjective = missionObj==='DESTROY THE HECATE AND THE ORION';
  const v1 = enemies.find(e=>e.uid==='V1'); v1.hp = 0;
  FS.step(400);
  r.notDoneWithOne = !(objCard && objCard.txt==='COUNTERATTACK BROKEN');
  // One of ours lost: now the call is free.
  a2.hp = 0; FS.step(300);
  r.callFreeAfterALoss = allyReady();
  const v2 = enemies.find(e=>e.uid==='V2'); if(v2) v2.hp = 0;
  r.completeCard = FS.until(()=>!!objCard && objCard.txt==='COUNTERATTACK BROKEN', 3000, false) >= 0;
  // Our ships jump out at the end of the wave: that is not a loss.
  const said = new Set();
  FS.until(()=>{ for(const n of NOTICES) said.add(n.txt); return wave===54; }, 9000, true, true);
  r.jumpIsNoLoss = !said.has('GTD ORION LOST');
  return r;`);

scenario('M54 Die Evakuierung', 'm=54', `
  const r = {};
  let t1 = null;
  FS.until(()=>{ t1 = allies.find(a=>a.uid==='T1'); return !!t1; }, 1000, false);
  r.leavesTheStation = !!t1 && Math.abs(t1.x-560) < 15 && t1.crossing < 0 && t1.flip===needsFlip(t1.img, true);
  const x0 = t1.x; FS.step(100);
  r.fliesLeft = t1.x < x0 - 30;
  // Keep them alive; they fly out to the left.
  const keep = ()=>{ for(const a of allies) if(/^T/.test(a.uid||'')) a.hp = a.maxHp = 1e7; };
  const t = FS.until(()=>{ keep(); return protSaved>=1; }, 3000, true);
  r.firstOut = t>=0;
  FS.step(5);
  r.noticeForIt = NOTICES.some(n=>n.txt==='FIRST ELYSIUM IS OUT');
  // Three out while the fourth is still flying: not yet complete.
  FS.until(()=>{ keep(); return protSaved>=3; }, 9000, true);
  const t4 = allies.find(a=>a.uid==='T4');
  r.notCompleteWhileOneFlies = !!t4 && !(objCard && objCard.txt==='EVACUATION COMPLETE');
  const c = FS.until(()=>{ keep(); return !!objCard && objCard.txt==='EVACUATION COMPLETE'; }, 9000, true);
  r.threeOutComplete = c>=0 && protSaved>=3;
  const w = FS.until(()=>{ keep(); return waveOver; }, 9000, true, true);
  r.waveEnds = w>=0;
  return r;`);

scenario('M54 two lost: failed', 'm=54', `
  const r = {};
  let n = 0;
  const f = FS.until(()=>{ for(const a of allies) if(/^T[12]$/.test(a.uid||'')) a.hp = 0;
    return !!objCard && objCard.tone==='fail'; }, 3000, true);
  r.failCard = f>=0 && objCard.txt==='TOO MANY ELYSIUMS LOST';
  return r;`);

scenario('Beams run under the hulls', 'm=42', `
  const r = {};
  FS.step(300);
  const shooter = allies.concat(enemies).find(o=>o.beams && o.beams.length);
  const b = shooter.beams[0];
  b.state = 'firing'; b.timer = 1e6; b.angle = 0; b.curAngle = 0;
  const order = [];
  const _r = drawBeamRays, _s = drawShip;
  drawBeamRays = function(e, own){ if(e.beams && e.beams.some(x=>x.state==='firing')) order.push(own ? 'own' : 'ray'); return _r.apply(this, arguments); };
  drawShip = function(img){ order.push(img===shooter.img ? 'shooter' : 'ship'); return _s.apply(this, arguments); };
  try { draw(); } finally { drawBeamRays = _r; drawShip = _s; }
  const lastRay = order.lastIndexOf('ray'), firstShip = Math.min(...['ship','shooter'].map(k=>order.indexOf(k)).filter(i=>i>=0));
  r.rayDrawn = lastRay>=0;
  // Under the ships it hits...
  r.underTheTargets = lastRay>=0 && firstShip>lastRay;
  // ...but on top of the ship that fires it.
  const sh = order.indexOf('shooter'), own = order.indexOf('own');
  r.onTopOfTheShooter = sh>=0 && own>sh;
  r.ownStretchShort = ownHullRun(shooter, shooter.x, shooter.y, 0) > 0 && ownHullRun(shooter, shooter.x, shooter.y, 0) < 1000;
  return r;`);

scenario('allied craft hold fire with nothing to shoot', 'm=44', `
  const r = {};
  FS.step(300);
  const fi = mkAllySmall('fighter', 'terran', 'fiherc', H*0.5);
  const bo = mkAllySmall('bomber', 'terran', 'boartemis', H*0.6);
  fi.warp = 0; bo.warp = 0; allies.push(fi, bo);
  // Only things an escort has no business shooting at: nothing, and an
  // invulnerable station at the right edge.
  const keep = enemies; enemies = [];
  const st = mkEnemy('cr_ntf', 'ntfcraeolus', H*0.5); st.x = W-40; st.warp = 0;
  st.invuln = true; st.scenery = true;
  const shots = ()=>pBullets.filter(b=>b.ally).length;
  let n = 0;
  for(const list of [[], [st]]){
    enemies = list;
    for(const a of [fi, bo]){
      a.head = 0; a.x = W*0.4;
      for(let k=0;k<40;k++){
        const b0 = shots();
        a.fT = 0; smallFire(a, smallTarget(a));
        if(a.secT) for(let i=0;i<a.secT.length;i++) a.secT[i] = 0;
        fireSecondaries(a, WPN[a.type]);
        n += shots()-b0;
      }
    }
  }
  enemies = keep;
  r.noShotsAtNothing = n===0;
  r._n = n;
  // With a real enemy in reach they still fire.
  const foe = enemies.find(e=>e.type==='fighter' && !(e.warp>0)) || enemies.find(e=>!(e.warp>0) && !e.invuln);
  let m = 0;
  if(foe){ fi.x = foe.x-80; fi.y = foe.y; fi.head = 0;
    for(let k=0;k<5;k++){ const b0 = shots(); fi.fT = 0; smallFire(fi, foe); m += shots()-b0; } }
  r.stillFireAtEnemies = m>0;
  return r;`);

scenario('M43 Der NTF-Konvoi', 'm=43', `
  const r = {};
  FS.step(600);
  const t = enemies.filter(e=>e.uid==='T1');
  r.threeTritons = t.length===3 && t.every(e=>e.img==='frtriton' && e.escaping>0);
  r.saysScanFirst = missionObj==='SCAN THE TRITONS';
  damageEnemy(t[0], t[0].maxHp*5, t[0].x, t[0].y, true, 'bolt'); FS.step(2);
  r.cannotDieUnscanned = enemies.includes(t[0]);
  r.noAeolus = !enemies.some(e=>e.uid==='K1') && !spawnQ.some(q=>q.uid==='K1');
  // Under fire the whole time: in this mission the scan still fills.
  for(const e of t) for(let i=0;i<SCAN_TIME+20;i++){
    player.x = e.x; player.y = e.y; MOUSE.x = e.x; MOUSE.y = e.y;
    player.shDelay = 90; player.hp = player.maxHp; FS.step(1); }
  r.allScanned = t.every(e=>e.scanned);
  FS.step(2);
  r.thenDestroy = missionObj==='DESTROY THE CONVOY';
  FS.step(200);
  r.aeolusAfterTheScan = enemies.some(e=>e.uid==='K1' && e.img==='ntfcraeolus');
  for(const e of t) e.hp = 0;
  const done = FS.until(()=>!!objCard && objCard.txt==='CONVOY DESTROYED', 1500, false);
  r.completeCard = done>=0;
  return r;`);

scenario('M43 a Triton gets away: failed', 'm=43', `
  FS.step(300);
  const t = enemies.filter(e=>e.uid==='T1');
  for(const e of t){ e.scanned = true; e.escaping = 3; }
  const f = FS.until(()=>!!objCard && objCard.tone==='fail', 3000, false);
  return {failCard: f>=0 && objCard.txt==='A TRITON GOT AWAY'};`);

scenario('M44 Der Schwarm', 'm=44', `
  const r = {};
  FS.step(400);
  r.noAllyWingAtStart = !allies.some(a=>a.small);
  r.deimosToRearm = allies.some(a=>a.uid==='A1' && a.img==='codeimos');
  const seen = {};
  let maxWing = 0, stray = 0;
  FS.until(()=>{ for(const e of enemies) if(e.uid) seen[e.uid]=1; for(const a of allies) if(a.uid) seen[a.uid]=1;
    const sm = allies.filter(a=>a.small && !a.dead); maxWing = Math.max(maxWing, sm.length);
    if(sm.some(a=>a.uid!=='W2')) stray++; return waveOver; }, 30000, true);
  // One allied wing, the one the mission sends; the Deimos adds none.
  r.oneAllyWingOnly = maxWing>0 && maxWing<=4 && stray===0;
  r.allTheWings = ['E1','E2','E3','B1','W2'].every(k=>seen[k]);
  return r;`);

scenario('M45 Das Nadeloehr', 'm=45', `
  const r = {};
  FS.step(500);
  const k = enemies.filter(e=>/^K[123]$/.test(e.uid||''));
  r.threeFenris = k.length===3 && k.every(e=>e.img==='ntfcrfenris');
  const ys = k.map(e=>e.y).sort((a,b)=>a-b);
  r.inSeparateLanes = ys.length===3 && ys[1]-ys[0] > 40 && ys[2]-ys[1] > 40;
  const o = allies.find(a=>a.uid==='A1');
  r.orionCrosses = !!o && o.transit===true;
  o.hp = o.maxHp = 1e7; for(const s of o.subs||[]) s.hp = s.maxHp = 1e7;
  let rocks = 0;
  const t = FS.until(()=>{ if(allies.includes(o)) o.hp = o.maxHp;
    if(enemies.some(e=>e.type==='asteroid')) rocks++;
    return !!objCard && objCard.txt==='THE ORION IS THROUGH'; }, 9000, true);
  r.throughCard = t>=0;
  r.noAsteroids = rocks===0;
  FS.until(()=>waveOver || wave>45, 3000, true);
  r.waveEnds = waveOver || wave>45;
  return r;`);

scenario('M46 Die Wissenschaftler', 'm=46', `
  const r = {};
  score = 1000;
  FS.step(400);
  const f = enemies.find(e=>e.uid==='F1');
  r.faustusParked = !!f && Math.abs(f.y-250) < 1;
  r.onADeadline = !!f && f.fleeT>0;
  // The countdown sits at the right edge, clear of the objective line.
  const _ft = [], _pl = [];
  const _fx = ctx.fillText, _tp = thPlate;
  ctx.fillText = function(t, x, y){ _ft.push({t:String(t), x, y}); return _fx.apply(this, arguments); };
  thPlate = function(x, y, w, h){ _pl.push({x, y, w, h}); return _tp.apply(this, arguments); };
  try { drawObjLine({txt:missionObj, col:'#fff'}); drawFleeWarning(); }
  finally { ctx.fillText = _fx; thPlate = _tp; }
  const _fw = _ft.find(o=>/JUMPING OUT IN/.test(o.t));
  r.countdownNamesShip = !!_fw && /FAUSTUS/.test(_fw.t);
  const _ol = _pl[0], _cd = _pl[_pl.length-1];
  r.countdownClearOfObjective = !!_ol && !!_cd && _pl.length>=2 &&
    (_ol.x+_ol.w < _cd.x) && (_cd.x+_cd.w <= W);
  damageEnemy(f, f.maxHp*5, f.x, f.y, true, 'bolt'); FS.step(2);
  r.cannotBeDestroyed = enemies.includes(f);
  const kill = id=>{ for(const s of f.subs) if(s.id===id){ s.dead=true; s.hp=0; } };
  kill('navigation'); FS.step(2);
  const ft = f.fleeT; FS.step(200);
  r.noNavigationNoJump = f.fleeT===ft;
  r.noArgoYet = !allies.some(a=>a.uid==='T1') && !spawnQ.some(q=>q.uid==='T1');
  kill('weapons'); FS.step(2);
  r.coverTheArgo = missionObj==='COVER THE ARGO';
  let argo = null;
  const at = FS.until(()=>{ argo = allies.find(a=>a.uid==='T1'); return !!argo && argo.holdT!=null; }, 9000, true);
  // Boarding takes its time: she stays on the Faustus, nothing is taken yet.
  const ax = argo && argo.x;
  FS.step(400);
  r.boardingHolds = at>=0 && !EV_DOCK['T1'] && !f.captured && Math.abs(argo.x-ax) < 1 && enemies.includes(f);
  const got = FS.until(()=>!!EV_DOCK['T1'], 9000, true);
  FS.step(5);
  r.docksAndTakes = got>=0 && f.captured===true;
  // And then both jump - the Argo does not fly on to the right.
  r.argoJumpsOut = !!argo && argo.warpOut>0 && !argo.crossing;
  r.completeCard = !!objCard && objCard.txt==='FAUSTUS CAPTURED';
  FS.step(300);
  r.noFailureAfterwards = !allies.includes(argo) && !(objCard && objCard.tone==='fail');
  return r;`);

scenario('M46 left alone she jumps: failed', 'm=46', `
  FS.step(300);
  const f = enemies.find(e=>e.uid==='F1');
  for(const s of f.subs) s.hp = s.maxHp = 1e7;
  const t = FS.until(()=>!!objCard && objCard.tone==='fail', 9000, true);
  return {failCard: t>=0 && objCard.txt==='THE FAUSTUS GOT AWAY'};`);

scenario('M47 Die zweite Flucht', 'm=47', `
  const r = {};
  score = 5000;
  FS.step(400);
  r.iceni = enemies.some(e=>e.uid==='V1' && e.iceni);
  r.hecate = enemies.some(e=>e.uid==='V2' && e.img==='ntfdehecate');
  r.noAllies = !allies.some(a=>!a.small);
  r.noAeolus = !enemies.some(e=>e.uid==='K1');
  const _v1 = enemies.find(e=>e.uid==='V1'), _v2 = enemies.find(e=>e.uid==='V2');
  const _y1 = _v1 && _v1.y, _y2 = _v2 && _v2.y;
  FS.step(300);
  r.shipsHoldHeight = !!_v1 && !!_v2 && Math.abs(_v1.y-_y1)<0.5 && Math.abs(_v2.y-_y2)<0.5 &&
    Math.abs(_v1.y-150)<1 && Math.abs(_v2.y-350)<1;
  r.iceniFortySeconds = !!_v1 && _v1.fleeT>0 && _v1.fleeT <= 40*TICK_HZ;
  r.noEndlessReinforcement = !evReinf;
  const t = FS.until(()=>!enemies.some(e=>e.uid==='V1'), 9000, true);
  r.iceniGetsAway = t>=0 && icenEscapes===1 && score>=5000;
  const v = enemies.find(e=>e.uid==='V2'); if(v) v.hp = 0;
  r.completeCard = FS.until(()=>!!objCard && objCard.txt==='HECATE DESTROYED', 3000, false) >= 0;
  return r;`);

scenario('M48 Die Aufklaerung', 'm=48', `
  const r = {};
  score = 2000;
  r.announced = NOTICES.some(n=>n.txt==='GTF PEGASUS ASSIGNED');
  FS.step(400);
  r.flyingAPegasus = player.ship==='fipegasus';
  r.nothingLocksHer = !canLockOn(player);
  const v = enemies.find(e=>e.uid==='V1');
  r.gunsHoldFire = capGunTarget(v)===null;
  r.noBeamOnHer = !beamTargets(v, false).includes(player);
  r.noHangar = shipSwapReady()===false;
  r.ringsShown = !!v && v.scanSubs===true && v.subs.every(s=>!s.scanned);
  for(const s of v.subs){ const p = subPos(v, s); FS.hold(p.x, p.y, SUB_SCAN_TIME + 20); }
  r.allFiveScanned = v.subs.every(s=>s.scanned) && v.scanned===true;
  FS.step(3);
  r.completeCard = !!objCard && objCard.txt==='ORION SCANNED';
  const t = FS.until(()=>!enemies.includes(v), 1500, false);
  r.orionLeavesWithoutPenalty = t>=0 && score >= 2000;
  FS.until(()=>wave>48, 30000, true);
  r.ownHullBackNextWave = wave===49 && player.ship==='fimyrmidon';
  return r;`);

scenario('Colossus beams are Terran', '', `
  return {main: beamCol('gtva', true)==='#00ff55', antiFighter: beamCol('gtva', false)==='#4499ff'};`, true);

scenario('HoL start unchanged', 'm=1', `
  return {wave: wave, thoth: player.ship==='fitoth', vasudanCall: ALLY_FAC_ON.vasudan===true && ALLY_FAC_ON.terran===false};`);

// ── Runner ─────────────────────────────────────────────────────────────
(async()=>{
  const browser = await chromium.launch();
  let fails = 0;
  const only = process.argv[4];
  for(const sc of scenarios){
    if(only && sc.name.indexOf(only)<0) continue;
    const page = await browser.newPage();
    const errs = [];
    page.on('pageerror', e=>errs.push(String(e.message||e)));
    await page.goto('file://' + tmp + '?' + sc.query);
    await page.waitForTimeout(300);
    let res;
    try{
      res = await page.evaluate(HELPERS + `\nFS.fakeImages();` + (sc.noLaunch ? '' : ' launchGame();') + `\n(function(){${sc.body}})()`);
    }catch(e){ res = null; errs.push(String(e.message||e)); }
    console.log(sc.name + '  (?' + sc.query + ')');
    if(res) for(const [k,v] of Object.entries(res)){
      const good = (typeof v==='boolean') ? v : true;
      if(!good) fails++;
      console.log((good ? '  ok    ' : '  FAIL  ') + k + (typeof v==='boolean' ? '' : ' = ' + JSON.stringify(v)));
    }
    if(errs.length){ fails++; console.log('  FAIL  page errors:\n    ' + errs.slice(0,4).join('\n    ')); }
    await page.close();
  }
  await browser.close();
  fs.unlinkSync(tmp);
  console.log('\n' + (fails ? fails + ' FAILED' : 'all passed'));
  process.exit(fails ? 1 : 0);
})();
