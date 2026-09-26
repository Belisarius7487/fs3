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
    // Step until cond() holds, clearing small craft every so often.
    until(cond, max, clear, all){ for(let t=0;t<max;t+=20){ if(cond()) return t;
             if(clear && t%200===0) FS.killSmall();
             if(all && t%200===0) for(const e of enemies) if(!(e.warp>0) && !e.invuln && !e.scenery) e.hp = 0;
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
  FS.step(40);
  const e = enemies.find(x=>x.uid==='A1');
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
  FS.until(()=>waveOver, 4000, true);
  r.waveEnds = waveOver;
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
  const got = FS.until(()=>!allies.some(a=>a.uid==='A1'), 9000, true);
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
for(let m=1;m<=36;m++) if(m!==12 && m!==23) scenario('M' + String(m).padStart(2,'0') + ' plays to the end', 'm=' + m, `
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
