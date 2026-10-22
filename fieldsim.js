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
      // Stand-ins for the backgrounds too (v230). They are fetched from the
      // server now and nothing is served here, so without these NEBS stays
      // empty - and since v229b nebSwap() holds back rather than swap to a
      // picture that has not arrived, no swap would ever run and every
      // check about the sky would pass by doing nothing.
      for(const k of NEB_NAMES){
        const c = document.createElement('canvas');
        c.width = 60; c.height = 30;
        const g = c.getContext('2d'); g.fillStyle = '#122033'; g.fillRect(0, 0, 60, 30);
        NEBS[k] = c;
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
           // v208: a world FIELD_K times larger at the old speeds - every wait
           // may last longer (an upper bound only)
           max *= Math.max(1, Math.min(6, (typeof FIELD_K !== 'undefined' ? FIELD_K : 1)/2));
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
  // v208: the mission area is FIELD_K times the old field, her speed is not
  const t = FS.until(()=>!!EV_LEFT['A1'], 8000*FIELD_K, true);
  r.jumpsAtTheEdge = t>=0 && e.warpOut>0 && e.x < MW;
  r.whileFullyOnScreen = !!e && e.x + IMGS[e.img].width*e.sc*0.5 <= MW;
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
  r.atGivenHeight = !!s && Math.abs(s.y-250*FIELD_K) < 1;
  const x0 = s ? s.x : 0;
  FS.step(1200);
  r.staysPut = !!s && Math.abs(s.x-x0) < 1 && Math.abs(s.y-250*FIELD_K) < 1;
  r.noFlak = !!s && flakHas(s)===false;
  r.guns = enemies.filter(e=>e.uid==='G1').length===4;
  // Reinforcements keep coming while she stands.
  FS.killSmall(); FS.step(900);
  r.reinforced = enemies.some(e=>e.type==='fighter' && !e.uid) || spawnQ.some(q=>!q.uid && /^fi_/.test(q.type));
  const before = SHOCKS.length;
  // Since v170 the big wave follows a short fuse.
  // Since v183 she dies the long way first.
  FS.killId('S1');
  r.bigBlast = FS.until(()=>SHOCKS.some(k=>k.rMax===300), 1500, false) >= 0;
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
  r.comesFromTheRight = !!d && d.x > MW*0.6;
  r.facesLeft = !!d && d.flip===needsFlip('ntfcodeimos', true);
  r.crossing = !!d && d.transit===true;
  r.firstWingHuntsHer = waveHunt==='A1';
  const x0 = d ? d.x : 0; FS.step(200);
  r.headsLeft = !!d && d.x < x0;
  FS.until(()=>!enemies.some(e=>e.uid==='E1') && !spawnQ.some(q=>q.uid==='E1'), 5000, true);
  FS.step(20);
  r.reinforcementsOn = evReinf===true;
  r.followUpsScreen = waveHunt==='';
  // v240 (F22): a passing corvette is no home ship - no rearm from her.
  r.noRearmFromAPassingCorvette = homeShipOnField()===false;
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
  // v208: her real hull is long and her speed old - she takes longer to her station
  FS.until(()=>!i || i.x <= i.targetX + 50, 600*Math.max(1, FIELD_K), false);
  // her station keeps the whole hull inside (she eases into it)
  r.wholeHullOnScreen = !!i && i.targetX + IMGS[i.img].width*i.sc*0.5 <= MW && i.x - i.targetX < 100;
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

// v253: 'M13 both transports on time' retired - M13 is an FS1 mission now.

// The sky may only change where nobody can see it change. Fading it over
// 120 steps from waveCd 62 did not do that: the blackout there is 1.6 per
// cent deep, and half way through the fade the field is 52 per cent dark
// with 27 per cent of the new sky already over it (Silvio, v229 and again
// v230: "wechseln immer noch bevor der Bildschirm verdunkelt wurde").
//
// Measured on the canvas, not from the state: the sky up now is painted
// black and every other one red, so anything red on the screen IS the new
// sky arriving. Red over green cancels the white of the stars and the grey
// of the hulls.
scenario('The sky is swapped in the dark, not while the field is lit', 'm=31', `
  const r = {};
  // Past the arrival first: the mission opens with one, and its own
  // blackout lifting would be read as the changeover.
  FS.step(TRANS_IN + 20);
  r.arrivalOver = arriveT === 0;
  const paint = (col) => { const c = document.createElement('canvas');
    c.width = 64; c.height = 32; const g = c.getContext('2d');
    g.fillStyle = col; g.fillRect(0, 0, 64, 32); return c; };
  for(const n of NEB_NAMES) NEBS[n] = paint('#ff0000');
  const wasCur = nebCur;
  NEBS[wasCur] = paint('#000000');
  // the haze of a nebula mission would tint the sample
  r.noFogHere = !nebulaOn();
  // and nothing of the field's own: no wreck, no round, no explosion whose
  // light would read as a new sky
  enemies = []; eBullets = []; pBullets = []; PARTS = []; FX_ANIMS = []; debris = [];

  // bottom left, well away from the vortex at the player's place
  const sx = Math.round(60*RES_X), sy = Math.round((H-60)*RES_Y);
  const sample = () => { const d = ctx.getImageData(sx, sy, 8, 8).data;
    let rr = 0, gg = 0;
    for(let i = 0; i < d.length; i += 4){ rr += d[i]; gg += d[i+1]; }
    return Math.round((rr-gg)/(d.length/4)); };
  draw();
  r.blackSkyToStart = sample() <= 2;

  // the changeover, as the end of a wave starts it
  waveOver = true; waveCd = TRANS_CLEAR + TRANS_OUT;
  let worstRed = 0, darkFirst = 1, vertex = -1;
  for(let t = 0; t < TRANS_CLEAR + TRANS_OUT + 60 && vertex < 0; t++){
    player.hp = player.maxHp;
    update(); draw();
    const red = sample();
    if(red > 2 && worstRed <= 2) darkFirst = Math.round(jumpDark()*100)/100;
    if(red > worstRed) worstRed = red;
    if(arriveT > 0) vertex = t;
  }
  r.theJumpRan = vertex > 0;
  r.newSkyShowedBeforeTheVertex = worstRed;
  r.darkWhenItFirstShowed = darkFirst;
  // Nothing of the new sky before the vertex. There the blackout is at its
  // deepest and the sky is drawn at nothing, so the cut costs no pixel.
  r.notWhileLit = worstRed <= 2;
  r.swappedThere = nebCur !== wasCur;
  return r;`);

// The one after this one is chosen and fetched a whole wave ahead. Asking
// for it at the moment of the changeover meant asking for 2.75 MB inside a
// window of 120 steps: it arrived part way through and appeared while the
// field was still lit (Silvio, v229).
scenario('The next background is chosen and fetched a wave ahead', 'm=31', `
  const r = {};
  FS.step(30);
  r.oneIsChosenAhead = !!nebNxt && nebNxt !== nebCur;
  r.andAskedFor = !!NEBS[nebNxt] || (typeof NEB_WANTED !== 'undefined' && NEB_WANTED[nebNxt] === true);
  // not there yet: the sky stays as it is rather than be swapped to nothing
  const was = nebCur;
  const keep = NEBS[nebNxt]; delete NEBS[nebNxt];
  if(typeof NEB_WANTED !== 'undefined') NEB_WANTED[nebNxt] = false;
  nebSwap();
  r.noSwapWithoutIt = nebCur === was;
  // there: it is swapped
  NEBS[nebNxt] = keep || 1;
  const to = nebNxt;
  nebSwap();
  r.swapsOnceItIsThere = nebCur === to;
  return r;`);

// The backgrounds are fetched from the server now instead of being built
// into the page, and only the one showing and the one being faded to are
// held. Twelve at 3000x1500 are 33 MB over the wire and about 18 MB of
// memory each once decoded, so holding all of them would cost a fifth of a
// gigabyte for eleven nobody is looking at (Silvio, v228: the backgrounds
// were mushy at 900x450 and 0.038 bytes a pixel).
scenario('The backgrounds are fetched, and at most two are held', '', `
  const r = {};
  r.twelveOfThem = NEB_NAMES.length === 12;
  r.eachHasAFile = NEB_NAMES.every(n => typeof NEB_DATA[n] === 'string'
                                        && /^nebulae\\/neb_.+\\.png$/.test(NEB_DATA[n]));
  r.noneBuiltIn = Object.keys(NEB_DATA).every(k => String(NEB_DATA[k]).indexOf('data:') !== 0
                                                   && String(NEB_DATA[k]).indexOf('@@') < 0);
  // the loading screen waits for the sprites alone
  r.loadingWaitsOnSpritesOnly = TOTAL === Object.keys(SPR_DATA).length;
  // and nothing holds on to the rest
  if(typeof nebDropOthers !== 'function'){ r.hasTheDropper = false; return r; }
  r.hasTheDropper = true;
  for(const k in NEBS) delete NEBS[k];
  NEBS.A = 1; NEBS.B = 2; NEBS.C = 3; NEBS.D = 4;
  nebDropOthers('A', 'B');
  r.heldAfterwards = Object.keys(NEBS).sort().join(',');
  r.atMostTwoHeld = Object.keys(NEBS).length <= 2;
  return r;`, true);

// The last blast of a capital ship used to be one exp20 drawn across 115 per
// cent of her length, and in v228 five across a third of her each. Measured
// in SHARE OF THE HULL that looked like a cure; measured where it is seen it
// was not. A cell of the sheet is 128 px: on a destroyer of 1642 world units
// those five came out at three and a half times the cell, and Silvio read the
// last blast as magnified texture again (v230).
//
// So this is measured in screen pixels a cell, at a REAL destroyer's length -
// not at the 340 fallback the first version of this check used, which is a
// fifth of one and hid the whole thing.
scenario('No part of a capital ship\'s last blast is pulled past its own cell', 'm=31', `
  const r = {};
  FS.step(60);
  r.sheetsReady = FS.until(()=>fxReady(), 6000) >= 0;
  // a real Orion: hullScale puts the stand-in at her true size, 1642 units
  const ship = {img: 'deorionright', sc: hullScale('deorionright'), ang: 0};
  const H = fxHull(ship, 340);
  r.hullLength = Math.round(H.L);
  r.aRealDestroyer = H.L > 1200;
  // Her last blast, really fired, and read back out of the list it is drawn
  // from - not off the calls into it. What a caller asks for and what is
  // drawn are two different numbers now.
  FX_ANIMS.length = 0;
  EXPL_Q.length = 0;
  scheduleExpl(0, 500, 300, H.L*0.08, 'final', null, H.L, H);
  tickExplQueue();
  const sizes = FX_ANIMS.map(f => ({k: f.k, d: f.d}));
  // world units to screen pixels, as the player sees them
  const px = (d) => d*CAM.z*Math.max(1, RES_X);
  // the flash is drawn, not pulled from a sheet, so it has no cell to blow up
  const sheets = sizes.filter(s => !!FX_SHEET_META[s.k]);
  const worst = sheets.reduce((m, s) => Math.max(m, px(s.d)/FX_SHEET_META[s.k].cell), 0);
  const big = sizes.filter(s => s.k === 'exp20');
  r.bigBlasts = big.length;
  r.widestCellDrawnTimesItsOwn = Math.round(worst*100)/100;
  // several of them, together still covering her, and none magnified
  r.severalBlasts = big.length >= 5;
  r.coversHer = big.length ? Math.max.apply(null, big.map(s => s.d))*big.length >= H.L*0.8 : false;
  r.noneMagnified = worst > 0 && worst <= 1.05;
  return r;`);

// A ship caught half way round when the mission ends used to slide into her
// own vortex side on: warpOut returns before capLane() is reached again, so
// the turn froze where it stood - squashed by turnSq, while fsNose() placed
// the vortex by the heading she had BEFORE the turn (Silvio, v216).
//
// Waiting for the turn, as he suggested, is not open to us: nine seconds for
// a destroyer against a changeover of about 220 steps. v227 settled it to
// the nearer heading instead, but in a single frame, and he saw that too:
// "das Schiff snapt auf der Stelle in die Warp-Richtung ohne langsame
// Bewegung" (v230). So the heading is settled at once - it has to be, the
// gate is placed from it at the first tick - and the sweep that is left runs
// off over half the jump. Measured here as the largest change of turnSq in
// any one step.
scenario('A ship caught mid-turn swings out of it instead of snapping', 'm=9', `
  const r = {};
  const cap = () => allies.find(a => !a.small && !a.dead && !(a.warp > 0));
  r.aCapitalShip = FS.until(()=>!!cap(), 20000, true) >= 0;
  const ally = cap();
  if(!ally) return r;

  const putMidTurn = (o, p, flip) => {
    o.flip = flip;
    o._lane = {y: o.y, dir: 1, dir0: 1, home: o.x, t: {p: p, n: 100}};
    o.turnP = p; o.turnC = Math.cos(Math.PI*p);
    o.turnSq = (o.turnC < 0 ? -1 : 1)*Math.max(0.2, Math.abs(o.turnC));
  };
  // Put her mid-turn, send her out, and watch how she comes out of it.
  const run = (o, p, flip) => {
    putMidTurn(o, p, flip);
    o.warpOut = 60; o.warpMax = 60; o.warpX = o.x; o.warpY = o.y;
    const sq = () => (o.turnSq == null ? 1 : Math.abs(o.turnSq));
    let prev = sq(), worst = 0, steps = 0, headAfter = null, headTurns = 0;
    for(let t = 0; t < 70; t++){
      FS.step(1);
      const now = sq();
      worst = Math.max(worst, Math.abs(now - prev));
      prev = now;
      if(headAfter === null) headAfter = o.flip;
      else if(o.flip !== headAfter){ headTurns++; headAfter = o.flip; }
      if(!o._lane || !o._lane.t) break;
      steps++;
    }
    return {flip: o.flip, worst: Math.round(worst*1000)/1000, steps: steps,
            headTurns: headTurns, cleared: !o._lane.t && o.turnSq === null};
  };

  // three quarters round: she is mostly there, so she finishes the flip
  const a = run(ally, 0.7, false);
  r.pastHalf_flipped = a.flip === true;
  r.pastHalf_laneTurned = ally._lane.dir === -1;
  r.pastHalf_turnCleared = a.cleared;
  r.pastHalf_headingSettledAtOnce = a.headTurns === 0;
  r.pastHalf_biggestStep = a.worst;
  r.pastHalf_stepsTaken = a.steps;
  r.pastHalf_noSnap = a.worst <= 0.08;
  r.pastHalf_tookTime = a.steps >= 10;

  // and before half way she keeps the heading she came in with
  const o2 = allies.find(x => !x.small && !x.dead && !(x.warp > 0) && x !== ally) || ally;
  const b = run(o2, 0.2, false);
  r.beforeHalf_keptHeading = b.flip === false;
  r.beforeHalf_turnCleared = b.cleared;
  r.beforeHalf_biggestStep = b.worst;
  r.beforeHalf_noSnap = b.worst <= 0.08;
  return r;`);

// Allied fighters and bombers were the last ships drawn by the rule from
// before v208: a fixed 65 px for every bomber and 60 for every fighter,
// whatever its length, while enemy small craft and the player had long since
// gone to real length. An allied Osiris of 40 m came out at a fraction of
// the enemy one beside her (Silvio, v232).
scenario('An allied bomber is drawn the size an enemy one is', 'm=31', `
  const r = {};
  FS.step(30);
  const lenOf = o => IMGS[o.img].width*o.sc;
  const en = mkEnemy('bo_shivan', 'boosiris', 200);
  const al = mkAllySmall('bomber', 'terran', 'boosiris', 200);
  r.enemyLength = Math.round(lenOf(en));
  r.allyLength = Math.round(lenOf(al));
  r.sameSize = Math.abs(lenOf(en) - lenOf(al)) < 0.5;
  const ef = mkEnemy('fi_shivan', 'fiastaroth', 200);
  const af = mkAllySmall('fighter', 'terran', 'fiastaroth', 200);
  r.sameSizeFighter = Math.abs(lenOf(ef) - lenOf(af)) < 0.5;
  // and her length drives it now: the 40 m Osiris against the 18 m Bakha,
  // which the old fixed number drew exactly alike
  const bk = mkAllySmall('bomber', 'vasudan', 'bobakha', 200);
  r.bakhaLength = Math.round(lenOf(bk));
  r.longerIsBigger = lenOf(al) > lenOf(bk)*1.5;
  return r;`);

// The Dragon is a genuinely short fighter - Silvio checked the figure - and
// at 12.6 m she came out the smallest fighter in the game and too hard to
// hit. His decision: a third larger, through the table that exists for
// exactly this (SIZE_KEY_MUL, where the buoys sit since v166).
scenario('The Dragon is drawn a third larger than her length gives', 'm=31', `
  const r = {};
  const plain = HULL_LEN.fidragon*SIZE_UPM;
  r.plainFromHerLength = Math.round(plain*10)/10;
  r.drawn = Math.round(hullWidth('fidragon')*10)/10;
  r.aThirdLarger = Math.abs(hullWidth('fidragon')/plain - 4/3) < 0.01;
  // and she is not the smallest fighter in the game any more
  const smaller = Object.keys(HULL_LEN)
    .filter(k => k.indexOf('fi') === 0 && hullWidth(k) < hullWidth('fidragon'));
  r.smallerThanHer = smaller.join(',') || '(none)';
  r.notTheSmallestAnyMore = smaller.length > 0;
  return r;`);

// The radar used to show the mission area while the ships fly in the world,
// which is wider and taller; everything out there was clamped onto the
// border. And the world was that much bigger only because it held room for
// a Colossus that could be called but mostly never was - she is 4745 units
// where a double-size mission is 1600 wide (Silvio, v232). Both ends of
// that are measured here: nothing is drawn longer than the field, so the
// world is the mission area and its margin, and the radar shows all of it.
scenario('The radar shows the whole world, and nothing is longer than the field', 'm=31', `
  const r = {};
  FS.step(30);
  const hwIn = (k) => (typeof hullWidthIn === 'function') ? hullWidthIn(k) : hullWidth(k);
  r.fieldK = FIELD_K;
  r.missionArea = Math.round(MW) + 'x' + Math.round(MH - HUD_H);
  r.world = Math.round(WX1 - WX0) + 'x' + Math.round(WY1 - WY0);
  r.colossusPlain = Math.round(hullWidth('sdcolossus'));
  r.colossusDrawn = Math.round(hwIn('sdcolossus'));
  r.noneLongerThanTheField = Object.keys(HULL_LEN).every(k => hwIn(k) <= MW + 0.001);
  // v233 tied the world to the Colossus as she is DRAWN and so shrank it
  // with her: 2888x1784 here where it had been 7118x3968, and 1151x679 in
  // M12. The two lines that stood here asserted exactly that shrinking
  // ("the world is the mission area plus its margin, and no more") - they
  // were written to bless it and are gone with it. The floor is the rule
  // now (Silvio, v234: "Jede Mission braucht exakt die gleich grosse
  // Spielflaeche").
  r.floor = WORLD_W0 + 'x' + Math.round(WORLD_H0);
  r.notBelowTheFloor = (WX1 - WX0) >= WORLD_W0 - 1 && (WY1 - WY0) >= WORLD_H0 - 1;
  r.shareOfTheRadar = Math.round(MW/(WX1 - WX0)*100) + '%x' + Math.round((MH - HUD_H)/(WY1 - WY0)*100) + '%';

  // The icons are data URLs and decode on their own time; nothing is drawn
  // before they are there.
  radarImgs();
  for(let i = 0; i < 60 && !radarIcon('radar-fighter', '#ffffff'); i++)
    await new Promise(res => setTimeout(res, 50));
  r.iconsReady = !!radarIcon('radar-fighter', '#ffffff');

  // Where an icon really lands. One ship in the field and nothing else, so
  // the first translate in drawBarRadar is hers.
  const keepE = enemies, keepA = allies;
  const one = enemies.find(x => !x.dead && x.img && !(x.warp > 0) && !x.scenery)
           || {type:'fighter', side:'enemy', faction:'ntf', img:'fiastaroth', hp:9, maxHp:9,
               dead:false, warp:0, warpOut:0, sc:0.3, x:0, y:0};
  const box = {x: 100, y: 6, w: 80, h: 44};
  const at = (sx, sy) => {
    enemies = [one]; allies = [];
    one.x = sx; one.y = sy;
    const tr = ctx.translate, tp = [];
    ctx.translate = function(tx, ty){ tp.push(tx); return tr.apply(ctx, arguments); };
    try{ drawBarRadar(box.x, box.y, box.w, box.h); } finally { ctx.translate = tr; }
    return tp.length ? tp[0] : null;
  };
  const cy = (HUD_H + MH)/2;
  // two places in the margin, where ships warp in from and where the old
  // radar clamped everything onto one edge
  const p1 = at(-40*FIELD_K, cy), p2 = at(-120*FIELD_K, cy);
  const mid = at(MW/2, cy);
  enemies = keepE; allies = keepA;
  r.iconsDrawn = p1 != null && p2 != null && mid != null;
  if(p1 != null && p2 != null && mid != null){
    r.atMinus40K = Math.round(p1*10)/10;
    r.atMinus120K = Math.round(p2*10)/10;
    // Two ships 80*FIELD_K apart in the margin have to land apart on the
    // radar. Clamped to the mission area's edge they landed on the same
    // pixel, which is the guessing Silvio refused to do.
    r.theMarginIsSpreadOut = Math.abs(p1 - p2) > 0.8;
    // and the middle of the mission is still the middle of the box
    r.middleStaysInTheMiddle = Math.abs(mid - (box.x + box.w/2)) < box.w*0.12;
  }
  return r;`);

// The one thing Silvio asked for in so many words: the same play field in
// every mission. The sweep calls the game's own worldForWave() on every
// written mission's spawn queue and reads the world it sets. On v233 this
// ran from 1151x679 (M12) to 10090x6367 (M55) - 76 of 80 missions below the
// floor - and a mission's play field depended on which hull happened to be
// the longest in it.
scenario('Every mission gets a play field of the same size', 'm=31', `
  const r = {};
  const ms = Object.keys(SCRIPT_WAVES).map(Number).sort((a,b)=>a-b);
  r.missions = ms.length;
  const seen = {}, small = [];
  for(const n of ms){
    worldForWave(getWaveDef(n));
    const key = Math.round(WX1 - WX0) + 'x' + Math.round(WY1 - WY0);
    (seen[key] = seen[key] || []).push(n);
    if((WX1 - WX0) < WORLD_W0 - 1 || (WY1 - WY0) < WORLD_H0 - 1) small.push(n + ':' + key);
  }
  const sizes = Object.keys(seen).sort((a,b)=>seen[b].length - seen[a].length);
  r.theFieldEveryoneGets = sizes[0] + ' in ' + seen[sizes[0]].length + ' of ' + ms.length;
  r.noneBelowTheFloor = small.length === 0;
  if(small.length) r.belowTheFloor = small.slice(0, 8).join(' ') + (small.length > 8 ? ' ...' : '');
  // A mission may need MORE than the floor - its own area plus the margin
  // is larger - but never less, and nothing else may make it differ.
  const bigger = sizes.filter(k => k !== sizes[0])
    .map(k => k + ' in ' + seen[k].length + ' (M' + seen[k].slice(0,4).join(',M') + ')');
  r.largerThanTheFloor = bigger.length ? bigger.join('; ') : '(none)';
  r.everyOneOfThoseIsItsOwnAreaPlusMargin = true;
  for(const n of ms){
    worldForWave(getWaveDef(n));
    const need = Math.max(WORLD_W0, MW + 300*FIELD_K);
    if(Math.abs((WX1 - WX0) - need) > 1.5){ r.everyOneOfThoseIsItsOwnAreaPlusMargin = false;
                                            r.offender = n + ' ' + Math.round(WX1-WX0) + ' vs ' + Math.round(need); break; }
  }
  return r;`);

// The clear pocket in a nebula is drawn on the screen but was centred on
// the player's WORLD position, so with the world of v208 it slid off the
// picture (Silvio, F19). Read off the gradient the drawing actually asks
// for: on the broken version its centre is player.x, which in this mission
// is over a thousand units to the right of the 800 wide screen.
scenario('The clear pocket in a nebula sits on the player, not beside him', 'm=39', `
  const r = {};
  FS.until(()=>!inJump(), 3000, true);
  r.nebulaMission = nebulaOn() === true;
  // Somewhere off the middle, so a centre taken from world coordinates and
  // one taken from screen coordinates cannot come out the same by luck.
  player.x = MW*0.62; player.y = (HUD_H + MH)/2 + 40;
  camSnap(player.x, player.y);
  transFog = 1;
  const calls = [];
  const real = ctx.createRadialGradient.bind(ctx);
  ctx.createRadialGradient = function(x0,y0,r0,x1,y1,r1){
    calls.push({x0,y0,r0,x1,y1,r1}); return real(x0,y0,r0,x1,y1,r1);
  };
  try{ drawNebulaFog(); } finally { delete ctx.createRadialGradient; }
  r.aPocketWasDrawn = calls.length > 0;
  if(!calls.length) return r;
  const c = calls[0];
  const sx = w2sX(player.x), sy = w2sY(player.y);
  r.playerWorldX = Math.round(player.x);
  r.playerScreenX = Math.round(sx);
  r.pocketCentreX = Math.round(c.x0);
  // On the screen, over the player, and sized by the gun range through the
  // zoom - what you cannot see is what cannot see you.
  r.centredOnThePlayerOnScreen = Math.abs(c.x0 - sx) < 1 && Math.abs(c.y0 - sy) < 1;
  r.notOnTheWorldPosition = Math.abs(c.x0 - player.x) > 100;
  r.radiusIsTheGunRangeThroughTheZoom =
      Math.abs(c.r1 - fireRange()*CAM.z*1.45) < 1 &&
      Math.abs(c.r0 - fireRange()*CAM.z*0.25) < 1;
  // and the centre is inside the field it is drawn on
  r.centreOnTheField = c.x0 >= 0 && c.x0 <= W && c.y0 >= HUD_H && c.y0 <= H;
  return r;`);

// FS1 and ST:R have no beams, and a ship that just loses those mounts loses
// its punch (Silvio, v237). A large beam mount becomes a railgun sized to
// the beam it replaces, an anti fighter beam mount becomes Standard Flak.
// The Lucifer keeps her beams in FS1, the Hades hers in ST:R - that
// exception asked for a flag (keepBeams) that nothing ever set, so until
// v237 the Lucifer would have flown an FS1 wave disarmed of her beams.
scenario('Without beams a ship gets railguns and flak, not silent mounts', 'm=31', `
  const r = {};
  const era0 = currentEra;
  const look = (key, era) => { currentEra = era; const m = mountsFor(key);
    return {beams: (m.beams||[]).length, primary: (m.primary||[]).length,
            flak: (m.flak||[]).length, m: m}; };
  const K = 'deorionright';
  const raw = F3D_GUNS[K];
  const bigBeams = raw.beams.filter(q => F3D_WPN[q[6]].large).length;
  const afBeams  = raw.beams.filter(q => !F3D_WPN[q[6]].large).length;
  r.theHullHasBeams = bigBeams > 0 && afBeams > 0;

  const two = look(K, 'fs2');
  const one = look(K, 'fs1');
  r.beamsInFS2 = two.beams;
  r.beamsInFS1 = one.beams;
  r.noBeamsLeftInFS1 = one.beams === 0 && two.beams > 0;
  // every large beam became a gun mount, every anti fighter beam a flak one
  r.gunsGrewByTheBigBeams = one.primary === two.primary + bigBeams;
  r.flakGrewByTheAfBeams  = one.flak === two.flak + afBeams;

  // and each railgun keeps the output of the beam it stands in for
  const dpsOfBeam = (w) => w.dmg*w.fireT/(w.chargeT+w.fireT+w.coolT+BEAM_IDLE_AVG);
  const subbed = (one.m.primary||[]).filter(p => p.wasBeam);
  r.railgunsPlaced = subbed.length === bigBeams;
  let worst = 0, sample = null;
  for(const p of subbed){
    const b = F3D_WPN[p.wasBeam];
    // a gun's output per tick: its damage over its interval. The interval is
    // the class beat (destroyer, 130 ticks on average) times the gun's rate.
    const gun = p.g.dmg/(130*p.g.rate);
    const d = Math.abs(gun - dpsOfBeam(b))/Math.max(1e-9, dpsOfBeam(b));
    if(d > worst){ worst = d; sample = p.wasBeam + ' beam ' + (dpsOfBeam(b)*100).toFixed(1) +
                              '/s vs railgun ' + (gun*100).toFixed(1) + '/s'; }
  }
  r.biggestDeviation = Math.round(worst*1000)/10 + ' %';
  if(sample) r.worstCase = sample;
  r.everyRailgunKeepsItsMountsOutput = worst < 0.05;
  // Silvio set 26 for the beam it was measured against
  const anchored = subbed.find(p => p.wasBeam === 'BGreen' || p.wasBeam === 'Bgreen');
  if(anchored) r.theAnchorIs26 = Math.abs(anchored.g.dmg - 26) < 0.05;

  // the two exceptions
  r.luciferKeepsHerBeamsInFS1 = look('sdlucifer', 'fs1').beams > 0;
  r.hadesKeepsHersInSTR       = look('sdhades', 'str').beams > 0;
  // and the era rule reaches initBeams too, not only the mount lists
  currentEra = 'fs1';
  const luci = {img:'sdlucifer', type:'boss', faction:'shivan'};
  const orion = {img:'deorionright', type:'destroyer', faction:'terran'};
  initBeams(luci); initBeams(orion);
  r.initBeamsArmsTheLucifer = (luci.beams||[]).length > 0;
  r.initBeamsLeavesTheOrion = !orion.beams || orion.beams.length === 0;
  currentEra = era0;
  return r;`);

// A capital ship had no acceleration: she came out of her vortex standing -
// the picture brings an ally out at nothing - and drove at her full cruise
// in the next tick. warpsim saw it thirteen times over the campaign and the
// numbers were exactly her cruise (craten 1.81, cosobek 2.18, hatshepsut
// 1.09). Measured here tick by tick on the real drive.
scenario('A capital ship accelerates instead of being at her cruise at once', 'm=31', `
  const r = {};
  // one that really drives her lane: capMovers() is the game's own list
  r.aShipOnHerLane = FS.until(()=>capMovers().length > 0, 20000, true) >= 0;
  const a = capMovers()[0];
  if(!a) return r;
  r.ship = a.img;
  const cruise = capCruise(a);
  r.cruise = Math.round(cruise*1000)/1000;
  // Standing still, and then let go. Measured as displacement, so it reads
  // the same on a version that has no accelerator at all.
  if('_capV' in a) a._capV = null;
  const step = [];
  for(let t = 0; t < 260; t++){ const x0 = a.x, y0 = a.y; capLane(a, 1);
                                step.push(Math.hypot(a.x - x0, a.y - y0)); }
  let worst = 0;
  for(let i = 1; i < step.length; i++) worst = Math.max(worst, Math.abs(step[i] - step[i-1]));
  r.firstStep = Math.round(step[0]*1000)/1000;
  r.afterTwoSeconds = Math.round(step[200]*1000)/1000;
  r.biggestStepChange = Math.round(worst*1000)/1000;
  // She sets off from a standstill rather than at her cruise, no single
  // tick changes her speed by much - warpsim's limit for a capital is 0.35
  // px/tick - and she does get up to speed.
  r.startsFromRest = step[0] < cruise*0.1;
  r.noJump = worst < 0.05;
  r.getsUpToSpeed = step[200] > cruise*0.6;

  // The other half of it: an ENEMY capital is brought out of her vortex AT
  // her glide speed, not standing - fsExitSpeed() gives 0.8 for a cruiser
  // heading for her station - so the accelerator has to pick up there. The
  // first cut of this started everything at rest, and warpsim read the drop
  // in 37 places: "stop craten/K1 speed 0.80 -> 0.01 px/tick (after jump)".
  const e = {img:'crcain', type:'cruiser', x:900, targetX:300, warp:0, warpOut:0, dead:false};
  r.herExitSpeed = fsExitSpeed(e);
  const first = capAcc(e, 0.8);
  r.firstGlideStep = Math.round(first*1000)/1000;
  r.picksUpWhereTheVortexLeftHer = Math.abs(first - fsExitSpeed(e)) < 0.02;

  // And a ship that was HELD sets off from nothing, not from where she left
  // off. The accelerator's step is her cruise over 2.5 s, so easing the
  // stored value towards zero barely moved it over a hold of a few ticks and
  // she drove off at nearly her full cruise in one tick (warpsim, M53:
  // [0 0 0 0 2.18 0.44] with {lane, capV 2.18}).
  const h = {img:'codeimos', type:'corvette', x:600, y:300, vy:0, dead:false,
             warp:0, warpOut:0, still:true, subs:[], _lane:{y:300, dir:1, dir0:1, home:600, t:null}};
  h._capV = capCruise(h);                 // at her cruise, then held
  capLane(h, 1);
  r.heldSpeedAfter = Math.round((h._capV||0)*1000)/1000;
  r.aHeldShipIsAtRest = (h._capV || 0) === 0;
  // let go again: she accelerates from nothing
  h.still = false;
  const x0 = h.x; capLane(h, 1);
  r.firstStepAfterTheHold = Math.round(Math.abs(h.x - x0)*1000)/1000;
  r.sheSetsOffGently = Math.abs(h.x - x0) < capCruise(h)*0.1;
  return r;`);

// Sentry guns get the corner brackets that fighters and bombers get. They
// had none unless they were the target, which left them to be found among
// the effects by eye (Silvio, v216).
scenario('A sentry gun is bracketed like a fighter', 'm=31', `
  const r = {};
  FS.step(60);
  const mk = (type) => ({type: type, side: 'enemy', faction: 'ntf', img: 'sgtrident',
                         x: player.x + 60, y: player.y, hp: 100, maxHp: 100,
                         dead: false, warp: 0, warpOut: 0, sc: 1});
  const seen = [];
  const fb = fsBrackets;
  fsBrackets = function(){ seen.push(1); };
  const count = (e) => { seen.length = 0; try{ drawHostileMark(e); }catch(err){} return seen.length; };
  r.fighterIsBracketed = count(mk('fighter')) > 0;    // the known good case
  r.sentryIsBracketed  = count(mk('sentry'))  > 0;
  // and an ally still gets none, whatever she is
  const friend = mk('sentry'); friend.side = 'ally';
  r.allyGetsNone = count(friend) === 0;
  fsBrackets = fb;
  return r;`);

// A guard that crosses on a clock (crossSecs) leaves through the transit
// path, while one that crosses at a speed is counted in tickCrossGuards.
// Only the second counted towards protSaved, so the Aten's escape in M9 was
// worth nothing: with both Bast lost the banner read OBJECTIVE FAILED
// although she came through, and the "X OF Y" never had her in either
// number (Silvio, v219).
// v253: on the Galatea of FS1 M6 - M9 is an FS1 mission now.
scenario('M06 a guard that crosses on a clock counts as one who got through', 'm=6', `
  const r = {};
  // Out of her vortex as well: while a.warp runs, updateAllies() skips her
  // before it ever reaches the transit step.
  const aten = () => allies.find(a => a.uid === 'G1' && !a.dead && !(a.warp > 0));
  r.sheArrives = FS.until(()=>!!aten(), 20000, true) >= 0;
  const a = aten();
  if(!a) return r;
  r.onAClock = !!a.transit;
  r.isGuard = !!a.guard;
  const before = protSaved;
  // a step short of the end of her run, so the next few steps take her over
  const v = a.transitV || 0;
  a.x = a.transitEnd - v*2;
  FS.step(8);
  r.sheEngagedHerDrive = (a.warpOut || 0) > 0;
  r.protSavedBefore = before;
  r.protSavedAfter = protSaved;
  r.sheIsCounted = protSaved === before + 1;
  // and not again on every step after it
  FS.step(90);
  r.countedOnce = protSaved === before + 1;
  return r;`);

// The darkness over the changeover belongs to the screen. drawJumpVortex()
// otherwise works in world coordinates on purpose - the vortex sits at the
// player's place in the world - and the darkening was drawn under the camera
// with it, which made it a rectangle of W x (H-HUD_H) world units that moved
// with the view instead of covering the picture. Silvio had been reporting
// that rectangle since v216; three explanations were measured and disproved
// before the read-out on his own machine named this line.
//
// jumpDark() is stubbed rather than waited for: whether a changeover is
// running is timing, and a check that waits for timing reports timing.
scenario('The changeover darkness covers the picture, not a patch of world', 'm=31', `
  const r = {};
  FS.step(60);
  // Three fixtures, because none of this can be waited for here: no warp
  // image is in a logic file (the packer fills it on the server), the
  // changeover is a matter of timing, and drawWarpFrame would then draw
  // from that empty image. None of them touches the line under test.
  const nw = Object.getOwnPropertyDescriptor(WARP_IMG, 'naturalWidth');
  Object.defineProperty(WARP_IMG, 'naturalWidth', {value: 64, configurable: true});
  Object.defineProperty(WARP_IMG, 'complete', {value: true, configurable: true});
  const dwf = drawWarpFrame; drawWarpFrame = function(){};
  const jd = jumpDark; jumpDark = function(){ return 0.8; };
  const at = arriveT; arriveT = Math.max(1, Math.round(TRANS_IN*0.2));

  const hits = [];
  const fr = ctx.fillRect;
  ctx.fillRect = function(x, y, w, h){
    if(String(ctx.fillStyle).replace(/ /g, '').indexOf('rgba(6,9,20') >= 0){
      const m = ctx.getTransform();
      hits.push({k: Math.round(m.a*100)/100, w: Math.round(Math.abs(m.a*w)), h: Math.round(Math.abs(m.d*h))});
    }
    return fr.apply(ctx, arguments);
  };
  try{ camOn(); drawJumpVortex(); }
  catch(e){ r.threw = String(e && e.message || e).slice(0, 60); }
  finally {
    ctx.fillRect = fr; drawWarpFrame = dwf; jumpDark = jd; arriveT = at;
    if(nw) Object.defineProperty(WARP_IMG, 'naturalWidth', nw);
    camScreen();
  }
  r.darknessDrawn = hits.length > 0;
  if(!hits.length) return r;
  const h = hits[0];
  r.scale = h.k;
  r.sizeOnScreen = h.w + 'x' + h.h;
  // Screen space: the scale is RES, and it reaches across the whole canvas.
  // Under the camera it would be CAM.z times that, and a patch of world.
  r.inScreenSpace = Math.abs(h.k - RES_X) < 0.01;
  r.coversTheWidth = h.w >= CVS.width - 1;
  return r;`);

// A round that kills the player reaches playerDie(), and playerDie() hands
// eBullets a NEW empty array. The loop it was called from keeps counting
// down into that empty array, b comes back undefined, and b.hom throws -
// update() ends mid-frame. Silvio's console had 532 of them in one session,
// and a frame that throws is what leaves draw() with the half-set state
// behind the rectangles he sees (v219).
//
// The lethal round goes in LAST so it sits at the top of the list and is
// handled first, leaving rounds below it for the loop to read afterwards.
scenario('A death with rounds still in flight does not end update()', 'm=31', `
  const r = {};
  FS.step(60);
  lives = 5;                       // not the last one: playerDie() runs through
  player.sh = 0; player.shDelay = 0; player.hp = 1;
  const B = pBox(), cx = B[0] + B[2]/2, cy = B[1] + B[3]/2;
  eBullets.length = 0;
  for(let k = 0; k < 4; k++)
    eBullets.push({x: player.x - 500 - k*40, y: player.y, w: 6, h: 6, vx: 0, vy: 0,
                   hom: true, life: 300, dmg: 1, faction: 'shivan'});
  eBullets.push({x: cx, y: cy, w: 24, h: 24, vx: 0, vy: 0,
                 life: 300, dmg: 9999, faction: 'shivan'});
  r.roundsInFlight = eBullets.length;
  let thrown = '';
  try{ update(); }catch(e){ thrown = String(e && e.message || e); }
  r.thrown = thrown || 'nothing';
  r.updateSurvives = thrown === '';
  r.sheDied = lives === 4;
  return r;`);

// One opening, and its mouth faces the ship: it spits her out coming in and
// swallows her going out. So the vortex she LEAVES through has to look back
// at her, against her nose, while the one she arrives from looks the way she
// flies. Both were drawn along her nose, leaving the one on the way out 180
// degrees round (Silvio, v216). warpsim watches the timing and the movement
// of a jump, never which way the vortex looks, so it could not see this.
scenario('M31 the vortex she leaves through faces her', 'm=31', `
  const r = {};
  const pick = () => enemies.find(x=>!x.dead && !(x.warp>0) && IMGS[x.img]);
  r.aShip = FS.until(()=>!!pick(), 20000, true) >= 0;
  const e = pick();
  if(!e) return r;
  // send her out, the way the game does
  e.warpOut = e.warpMax = 160; e.warpX = e.x; e.warpY = e.y; e._fsG = null;
  const nose = fsNose(e), noseAng = Math.atan2(nose.y, nose.x);
  // f3dWarp draws the model and returns true, which would end the call before
  // the angle is ever handed to ctx. Stood aside here so both can be read.
  const f3 = (typeof f3dWarp === 'function') ? f3dWarp : null;
  let model = null;
  if(f3) f3dWarp = function(px, py, fx, fy){ model = Math.atan2(fy, fx); return false; };
  const rot = [];
  const rr = ctx.rotate;
  ctx.rotate = function(a){ rot.push(a); return rr.apply(ctx, arguments); };
  try{ drawOwnVortex(e); } finally { ctx.rotate = rr; if(f3) f3dWarp = f3; }
  const norm = a => Math.atan2(Math.sin(a), Math.cos(a));
  const half = a => Math.abs(Math.abs(norm(a)) - Math.PI) < 0.05;   // about 180 deg
  r.vortexWasDrawn = rot.length > 0;
  if(!rot.length) return r;
  r.turnedFromHerNose = Math.round(norm(rot[0] - noseAng)*100)/100;
  r.mouthLooksBackAtHer = half(rot[0] - noseAng);
  if(model !== null) r.modelLooksBackAtHer = half(model - noseAng);

  // Out through the Knossos she leaves by the TURQUOISE vortex. It is the
  // same code path, so the direction holds for it too - read off here
  // rather than assumed, since from the outside the two look like separate
  // things (Silvio, v232: he could not tell whether the direction fix had
  // reached the turquoise one).
  e.portalOut = true; e._fsG = null; e.warpOut = e.warpMax = 160;
  let kn = null;
  const rot2 = [];
  const dw = drawWarpFrame;
  drawWarpFrame = function(seed, WS, knossos){ kn = !!knossos; };
  if(f3) f3dWarp = function(px, py, fx, fy, WS, wS, al, seed, knossos){
    kn = !!knossos; rot2.push(Math.atan2(fy, fx)); return false; };
  ctx.rotate = function(a){ rot2.push(a); return rr.apply(ctx, arguments); };
  try{ drawOwnVortex(e); } finally { ctx.rotate = rr; drawWarpFrame = dw; if(f3) f3dWarp = f3; }
  r.turquoiseThroughThePortal = kn === true;
  r.andTheTurquoiseLooksBackToo = rot2.length > 0 && half(rot2[0] - noseAng);
  return r;`);

// The rotating parts of a model (f3dNodeMats, nodes of kind 'rot') all
// turned the same way round the model's own axis, and that way was the wrong
// one: the Knossos is two rings of separate elements, the outer turning one
// way and the inner the other, and Silvio reports both reversed (v232). The
// per-part direction does come through - it sits in the axis, or in the sign
// of the period - so what was wrong is the sense of a turn about it, for
// every rotating part at once.
//
// There is no model to read here: the files live on the server, not in the
// repo. So a stand-in node is turned instead and the sense of its turn is
// measured, which is the whole of what changed. Which sense is right is
// Silvio's word, not something this can prove - what it does is hold the
// direction still, so it cannot quietly flip back.
scenario('A rotating part of a model turns one way, and the other one back', 'm=31', `
  const r = {};
  r.theresAFunction = typeof f3dNodeMats === 'function';
  if(!r.theresAFunction) return r;
  const I = new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);
  // Which way a point of the ring goes round, measured in ONE fixed frame
  // (about +z) and not about the part's own axis - about its own axis every
  // part turns the same way by construction, which says nothing.
  const senseZ = (ax) => {
    const e = {}, L = {head:{nodes:[null, {k:'rot', t:20, par:0, ax:ax, pv:[0,0,0]}]}};
    const at = (t) => { const M = f3dNodeMats(e, L, I, 0, 0, t)[1];
                        return [M[0], M[1], M[2]]; };
    const a = at(0), b = at(2.5);
    const cz = a[0]*b[1] - a[1]*b[0];
    return Math.abs(cz) < 1e-6 ? 0 : (cz > 0 ? 1 : -1);
  };
  const outer = senseZ([0, 0, 1]), inner = senseZ([0, 0, -1]);
  r.senseAboutZ = outer;
  r.turnsAtAll = outer !== 0;
  // v232 and before: the other way round.
  r.theOtherWayRound = outer === -1;
  // and the ring whose axis points the other way turns against it - that is
  // how the Knossos keeps its two rings running against each other
  r.theRingsTurnAgainstEachOther = inner === -outer && inner !== 0;
  return r;`);

// The subsystem picked as the target keeps its name, wherever the player is
// and wherever she looks. Before v217 one name was shown, and only within 120
// world units AND 31 degrees of where her nose pointed - so on a hull
// thousands of units long it was mostly absent, and which green bracket was
// which had to be guessed (Silvio, v216).
//
// Set up so that ONLY the new rule can produce a label: she looks the other
// way, stands well off, and the pointer sits in a corner. Under the old rule
// nothing is drawn here.
scenario('M31 the picked subsystem keeps its name', 'm=31', `
  const r = {};
  const withSubs = () => enemies.find(x=>x.subs && x.subs.length && !x.dead && !(x.warp>0));
  r.enemyWithSubs = FS.until(()=>!!withSubs(), 20000, true) >= 0;
  const e = withSubs();
  if(!e) return r;
  subMarksOn = true;
  TGT.e = e; TGT.sub = e.subs.find(s=>!s.dead) || e.subs[0];
  r.picked = !!TGT.sub;
  // off to her left, nose pointing away from her
  player.x = e.x - 600; player.y = e.y; player.head = Math.PI;
  MOUSE.scr = true; MOUSE.sx = 5; MOUSE.sy = 5;      // pointer in a corner
  const seen = [];
  const ft = ctx.fillText;
  ctx.fillText = function(t){ seen.push(String(t)); return ft.apply(ctx, arguments); };
  try{ drawSubsystems(e); } finally { ctx.fillText = ft; }
  r.labelsDrawn = seen.join(',');
  r.pickedNameDrawn = seen.indexOf(TGT.sub.label) >= 0;

  // and the reticle names whatever it is held over, so every bracket can be
  // identified by pointing at it
  const other = e.subs.find(s=>!s.dead && s!==TGT.sub);
  if(other){
    const op = subPos(e, other), ov = hullPt(e, op.x, op.y);
    MOUSE.sx = w2sX(ov.x); MOUSE.sy = w2sY(ov.y);
    const seen2 = [];
    const ft2 = ctx.fillText;
    ctx.fillText = function(t){ seen2.push(String(t)); return ft2.apply(ctx, arguments); };
    try{ drawSubsystems(e); } finally { ctx.fillText = ft2; }
    r.underReticle = seen2.join(',');
    r.reticleNamesIt = seen2.indexOf(other.label) >= 0;
  }
  return r;`);

// A ship driving across the field steers herself: tickCrossGuards() moves her
// by her crossing, and nothing else may. capLane drove a crossing freighter as
// well, at about eighteen times that speed, and turned her round at her lane
// limit - so the Bast freighters in The Convoy flew back and forth instead of
// warping out to the right (Silvio, v216).
//
// "Does she get out" is not the check: whether she does depends on which way
// her lane happens to run, and on v216 she sometimes did. What is measured is
// the one thing that must hold - one step moves her by her crossing, no more.
// v253: on the freighters of M23 - M9 is an FS1 mission now.
scenario('M23 a crossing freighter is driven by her crossing alone', 'm=23', `
  const r = {};
  const f1 = () => allies.filter(a=>a.uid==='F1' && !a.dead);
  // M23's freighters come once the containers are scanned (all: scanned)
  r.sheArrives = FS.until(()=>f1().length>0 && !(f1()[0].warp>0), 20000, true, true) >= 0;
  const a = f1()[0];
  if(!a) return r;
  // Her crossing is started here instead of waiting for the dock: whether
  // she survives the fighters and reaches a container is luck, and a check
  // that depends on luck says nothing. These are the two lines the game
  // itself runs the moment she has docked (30_waves.js, 'Docked.').
  a.dockTo = null; a.dockRes = null;
  a.crossing = a.crossAfter || 0.38;
  const x0 = a.x;
  FS.step(1);
  const moved = a.x - x0;
  r.movedPerStep = Math.round(moved*1000)/1000;
  r.crossingSpeed = Math.round(a.crossing*1000)/1000;
  // The one rule: her crossing is the drive itself, nothing is added to it.
  r.stepIsCrossingOnly = Math.abs(moved - a.crossing) < 0.05;
  // and no lane drives her, so nothing can turn her round mid-field
  r.laneHoldsHer = !a._lane || a._lane.stand === true;
  return r;`);

// Every written mission has to come to an end when its enemies go down,
// with nothing thrown on the way. Enemy ships are cleared every two seconds
// once they are out of their vortex - a player who hits everything.
// Scan missions (23) need the player to fly the scan and are left out.
// 61 ends only when the Aeolus is lost; its own scenario covers that.
// 71 is a scan, flown in its own scenario like 12 and 23.
// v253: 12 is FS1 First Strike now, no longer a scan - it plays like the rest.
for(const m of Array.from({length:80},(_,i)=>i+1)) if(m!==23 && m!==61 && m!==71) scenario('M' + String(m).padStart(2,'0') + ' plays to the end', 'm=' + m, `
  // v208: speeds unchanged in a world FIELD_K times larger - more time
  const t = FS.until(()=>waveOver, 40000*Math.max(1, Math.min(4, FIELD_K/2)), false, true);
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
  // v207: full screen is F8 (the key table)
  document.dispatchEvent(new KeyboardEvent('keydown', {code:'F8'}));
  document.dispatchEvent(new KeyboardEvent('keyup', {code:'F8'}));
  r.fullKeyOnTheTitle = calls===2 && GS==='title';
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
  r.midField = !!d && Math.abs(d.y-260*FIELD_K) < 1;
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
  d.hp = 0; FS.step(300 + deathRollLen(d));     // v183: the long way
  return {freed: freed, failCard: failCard, thenDestroyable: !enemies.includes(d) && !EV_LEFT['D1']};`);

scenario('M38 left alone she jumps at the edge', 'm=38', `
  FS.step(300);
  const d = enemies.find(e=>e.uid==='D1');
  const t = FS.until(()=>!!EV_LEFT['D1'], 8000, true);
  FS.step(2);
  return {jumps: t>=0 && d.warpOut>0 && !d.captured, onScreen: d.x + IMGS[d.img].width*d.sc*0.5 <= MW,
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
  m1.hp = 0; FS.step(3 + BIG_BLAST_FUSE);
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
  r.crossesSlowly = !!h && h.x > x0 && (h.x-x0) < 100*FIELD_K;
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
  const s1 = enemies.find(e=>e.uid==='S1'); s1.hp = 0;
  // v183: the card comes when she has broken up
  const t = FS.until(()=>!!objCard && objCard.head==='OBJECTIVE COMPLETE' && objCard.txt==='RELAY DESTROYED', 1000, false);
  return {saysWhatToDo: ok1, completeCard: t >= 0};`);

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
  // Only the test's own notices: the mission may post one of its own
  // meanwhile (M31: the Leviathan turning hostile).
  r.theyGoAgain = !NOTICES.some(n=>/^N\d$/.test(n.txt));
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
  barPulse('hull'); FS.step(40); draw(); thGlowPath = og;
  r.ringAroundHull = rings.some(g=>g.x===109 && g.w===56);   // the v187 bar (lives icon back); v210: bars 50 wide
  // v202: no ticket cells in the bar any more
  // Its time is up: the pulse is over and gone. (Stepping the game to get
  // there would let loot from the fight light it up again.)
  barPulse('hull'); BAR_PULSE.hull.t0 = fc - BAR_PULSE_T;
  r.andItEnds = barPulseLevel('hull')===0 && !BAR_PULSE.hull;
  r.softNotHard = (()=>{ barPulse('hull'); const a = barPulseLevel('hull'); FS.step(10); const b = barPulseLevel('hull'); return a===0 && b>0 && b<1; })();
  return r;`);

scenario('Mission reward: points (v202, was a ticket)', 'm=35', `
  FS.step(300);
  const d = allies.find(a=>a.uid==='A1');
  d.hp = d.maxHp = 1e7; for(const s of d.subs||[]) s.hp = s.maxHp = 1e7;
  TICKET_MSGS.length = 0; const s0 = score;
  // Rocks and wreckage take a share of the hull rather than points, so a
  // big hull alone does not keep her alive: she is topped up as she goes.
  const t = FS.until(()=>{ if(allies.includes(d)) d.hp = d.maxHp; return waveOver; }, 12000, true);
  const r = {rewarded: t>=0 && score - s0 >= capHull(HULL.cruiser)*0.9, notInTheField: TICKET_MSGS.length===0};
  if(!r.rewarded) r.dbg = {t, gl:guardLost, gw:guardWanted, gs:guardSpawned, keys:Object.keys(BAR_PULSE), wave, fc};
  return r;`);

// v240 (F22): only the mission's home ship rearms. No written mission has
// one yet (the FS1 strand starts without), so the Deimos of M35 is made the
// home ship here - what is checked is the button, not the mission.
scenario('The home ship arrives: REARM calls', 'm=35', `
  BAR_PULSE = {};
  FS.until(()=>allies.some(a=>a.uid==='A1'), 3000, true);
  FS.step(300);
  const noCall = !BAR_PULSE.rearm;
  for(const a of allies) if(a.uid==='A1') a.home = true;
  // The button becomes usable once she is there and the jump in is over.
  const t = FS.until(()=>!!BAR_PULSE.rearm, 3000, true);
  const called = rearmReady();
  const t0 = BAR_PULSE.rearm ? BAR_PULSE.rearm.t0 : -1;
  FS.step(100);
  return {notWhileShesNoHomeShip: noCall, rearmCalls: t>=0 && called, onlyOnceNotEveryStep: !BAR_PULSE.rearm || BAR_PULSE.rearm.t0===t0};`);

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
  for(let i=0;i<6000*Math.max(1, FIELD_K);i++){ if(EV_DOCK['T1']){ got = i; break; } h0 = d.hp; if(i%200===0) FS.killSmall(); FS.step(1); }
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
  r.inPlace = !!m1 && !!m2 && Math.abs(m1.x-70*FIELD_K)<1 && Math.abs(m1.y-140*FIELD_K)<1 && Math.abs(m2.y-360*FIELD_K)<1;
  r.deimosAtTheBottom = allies.some(a=>a.uid==='A1' && a.img==='codeimos' && Math.abs(a.y-440*FIELD_K)<1);
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
    for(const e of caps) if(e.warp<=0 && e.x < MW-60*FIELD_K){ e.hp = 0; }
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
  r.fleetPlaced = !!a1 && !!a2 && Math.abs(a1.y-170*FIELD_K)<60*FIELD_K && Math.abs(a2.y-390*FIELD_K)<60*FIELD_K;
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
  a2.hp = 0; FS.step(300 + deathRollLen(a2));   // v183: the long way
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
  r.leavesTheStation = !!t1 && Math.abs(t1.x-560*FIELD_K) < 15*FIELD_K && t1.crossing < 0 && t1.flip===needsFlip(t1.img, true);
  const x0 = t1.x; FS.step(100);
  r.fliesLeft = t1.x < x0 - 30;
  // Keep them alive; they fly out to the left.
  const keep = ()=>{ for(const a of allies) if(/^T/.test(a.uid||'')) a.hp = a.maxHp = 1e7; };
  const t = FS.until(()=>{ keep(); return protSaved>=1; }, 3000, true);
  r.firstOut = t>=0;
  FS.step(5);
  r.noticeForIt = NOTICES.some(n=>n.txt==='AN ELYSIUM IS OUT - 1 SAFE SO FAR');
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
  r.ownStretchShort = ownHullRun(shooter, shooter.x, shooter.y, 0) > 0 && ownHullRun(shooter, shooter.x, shooter.y, 0) < 1000*FIELD_K;
  return r;`);

scenario('Knossos scene: same sky within a run', 'm=55', `
  const r = {};
  FS.step(50);
  // Make sure there is something in the sky to compare, then write the
  // scene down again from that.
  // The harness has no planet pictures, so two stand-ins.
  bodies = [{key:'testplanet', kind:'planet', meta:{r:0,cx:0.5,cy:0.5}, w:220, x:310, y:190, spd:0.05},
            {key:'testsun', kind:'sun', meta:{r:0,cx:0.5,cy:0.5}, w:120, x:620, y:120, spd:0.04}];
  delete SCENES.knossos; useScene('knossos');
  const neb = nebCur, keys = bodies.map(b=>b.key).join(','), pos = bodies.map(b=>Math.round(b.x)+'/'+Math.round(b.y)).join(','), la = lightAng;
  r.portalThere = enemies.some(e=>e.uid==='P1' && e.img==='inknossos45deg' && e.invuln && e.scenery);
  // To 56: a different place, a fresh roll. nextWave() cuts the sky over
  // itself, in the dark of the jump, so there is nothing to step for it.
  waveOver = false; nextWave(); FS.step(5);
  // On to 58 through 57, the sky cut over each time.
  FS.step(5); nextWave(); FS.step(5);
  FS.step(5); nextWave();
  r.atTheGate = wave===58;
  const placesNow = bodies.map(b=>Math.round(b.x)+'/'+Math.round(b.y)).join(',');
  r.sameBackdrop = nebCur===neb;
  r.sameBodies = bodies.map(b=>b.key).join(',')===keys;
  r.samePlaces = placesNow===pos;
  r.sameLight = lightAng===la;
  // A new run rolls anew: the book is empty.
  launchGame();
  r.newRunForgets = (SCRIPT_ONE===55) ? !!SCENES.knossos && Object.keys(SCENES).length===1 : Object.keys(SCENES).length===0;
  return r;`);

scenario('M55 Der Anflug', 'm=55', `
  const r = {};
  let k = null;
  FS.until(()=>{ k = enemies.find(e=>e.uid==='K1' && !(e.warp>0)); return !!k; }, 2000, true);
  r.cruiserFromTheLeft = !!k && k.x < 100*FIELD_K && k.escaping>0 && k.escWarp;
  k.hp = k.maxHp = 1e7;
  const f = FS.until(()=>{ k.hp = k.maxHp; return k.warpOut>0; }, 6000, true);
  r.jumpsAtThePortal = f>=0 && k.x >= PORTAL_X*FIELD_K && k.x < MW && k.portalWarp===true;
  FS.step(5);
  r.failCard = !!objCard && objCard.txt==='A CRUISER REACHED THE PORTAL';
  return r;`);

scenario('M55 all stopped', 'm=55', `
  const r = {};
  let k = null;
  FS.until(()=>{ k = enemies.find(e=>e.uid==='K1' && !(e.warp>0)); return !!k; }, 2000, true);
  for(const s of k.subs) if(s.id==='engines'){ s.dead = true; s.hp = 0; }
  const x0 = k.x; FS.step(200);
  r.enginesStopHer = Math.abs(k.x-x0) < 0.01;
  const seen = {};
  const t = FS.until(()=>{ for(const e of enemies) if(/^K/.test(e.uid||'') && !(e.warp>0)){ seen[e.uid]=1; e.hp = 0; }
    return !!objCard && objCard.txt==='ALL CRUISERS STOPPED'; }, 12000, true);
  r.completeCard = t>=0 && Object.keys(seen).length===4;
  return r;`);

scenario('M56 Die Verraeter', 'm=56', `
  const r = {};
  FS.step(300);
  const a1 = allies.find(a=>a.uid==='A1');
  r.alliedLeviathan = !!a1 && a1.img==='crleviathan';
  r.deimosToo = allies.some(a=>a.uid==='A2' && a.img==='codeimos');
  FS.until(()=>!allies.includes(a1), 3000, true);
  const t = enemies.find(e=>e.uid==='A1');
  r.goesOver = !!t && t.side==='enemy' && t.img==='ntfcrleviathan';
  // She stays on the left and faces into the field, not the edge behind her.
  r.facesIntoTheField = !!t && t.x < MW*0.5 && t.flip===needsFlip(t.img, false);
  const _tx = t.x; FS.step(200);
  // v211: a warship drives her lane (capLane) - she stands, or she moves
  // the way her bow points, into the field
  r.staysWhereSheIs = Math.abs(t.x-_tx) < 1 || (!!t._lane && !t._lane.stand && (t.x-_tx)*capBow(t) > 0 && t.x < MW*0.75);
  FS.step(3);
  r.newObjective = missionObj==='DESTROY THE LEVIATHAN';
  r.moreComing = enemies.some(e=>e.uid==='E2') || spawnQ.some(q=>q.uid==='E2' || q.uid==='B1') || enemies.some(e=>e.uid==='B1');
  t.hp = 0;
  r.completeCard = FS.until(()=>!!objCard && objCard.txt==='TRAITOR DESTROYED', 1500, false) >= 0;
  return r;`);

scenario('M57 Die Nachhut', 'm=57', `
  const r = {};
  const prevSec = player.sec;
  FS.step(300);
  r.ursaWithStiletto = player.ship==='boursa' && player.sb[0].key==='stiletto2' && player.sSel===0;
  const us = ['K1','K2','D1'].map(id=>enemies.find(e=>e.uid===id));
  r.threeHoldTheRear = us.every(Boolean);
  damageEnemy(us[0], us[0].maxHp*5, us[0].x, us[0].y, true, 'bolt'); FS.step(2);
  r.cannotBeDestroyedYet = enemies.includes(us[0]);
  // A Stiletto II (v186) takes a cruiser's system with one round, a
  // corvette's with at most two.
  const sw = secDefP('stiletto2');
  const bombs = u=>{ const s = u.subs.find(x=>x.id==='engines'); let n = 0;
    while(!s.dead && n<10){ const p = subPos(u, s); subStrikeRaw(u, sw.dmg*sw.f.u, p.x, p.y); n++; } return n; };
  r.oneBombPerCruiserSystem = bombs(us[0])===1;
  r.twoBombsPerCorvetteSystem = bombs(us[2])<=2;
  for(const u of us) for(const s of u.subs) if(s.id==='engines'||s.id==='weapons'){ s.dead = true; s.hp = 0; }
  const c = FS.until(()=>!!objCard && objCard.txt==='REARGUARD DISABLED', 1500, false);
  r.completeCard = c>=0;
  r.leftAsWrecks = us.every(u=>enemies.includes(u) && u.scenery);
  const w = FS.until(()=>wave===58, 9000, true, true);
  r.nextWaveOwnShipBack = w>=0 && player.ship!=='boursa' && !player.sb.some(b=>b.key==='stiletto2' && !shipBanks(player.ship).s.includes('stiletto2'));
  return r;`);

scenario('M58 Das Tor', 'm=58', `
  const r = {};
  FS.step(400);
  r.portalThere = enemies.some(e=>e.uid==='P1' && e.img==='inknossos45deg');
  r.sentryLine = enemies.filter(e=>e.uid==='G1').length===6;
  r.twoCruisers = enemies.some(e=>e.uid==='K1' && e.img==='ntfcrfenris') && enemies.some(e=>e.uid==='K2' && e.img==='ntfcraeolus');
  for(const e of enemies) if(/^(K|G)/.test(e.uid||'')) e.hp = 0;
  r.completeCard = FS.until(()=>!!objCard && objCard.txt==='PORTAL DEFENCE BROKEN', 1500, false) >= 0;
  return r;`);

scenario('M59 Die letzte Sperre', 'm=59', `
  const r = {};
  FS.step(500);
  const v1 = enemies.find(e=>e.uid==='V1'), v2 = enemies.find(e=>e.uid==='V2');
  r.twoDestroyers = !!v1 && !!v2 && v1.img==='ntfdehecate' && v2.img==='ntfdeorion';
  r.inFrontOfThePortal = enemies.some(e=>e.uid==='P1');
  r.fighterCover = allies.filter(a=>a.small && a.uid==='W1').length >= 2;
  v1.hp = 0; FS.step(300);
  r.notYet = !(objCard && objCard.txt==='THE WAY TO THE PORTAL IS OPEN');
  v2.hp = 0;
  r.completeCard = FS.until(()=>!!objCard && objCard.txt==='THE WAY TO THE PORTAL IS OPEN', 3000, false) >= 0;
  return r;`);

scenario('M60 Der Sprung', 'm=60', `
  const r = {};
  score = 3000;
  const esc0 = icenEscapes;
  let v = null;
  FS.until(()=>{ v = enemies.find(e=>e.uid==='V1' && !(e.warp>0)); return !!v; }, 3000, true);
  r.iceniRuns = !!v && v.iceni && v.escaping>0;
  r.nothingToShootOut = !!v && !v.subs.some(s=>s.id==='engines' || s.id==='navigation');
  damageEnemy(v, v.maxHp*5, v.x, v.y, true, 'bolt'); FS.step(2);
  r.cannotBeDestroyed = enemies.includes(v) && v.hp>0;
  const j = FS.until(()=>v.warpOut>0, 9000, true);
  r.throughThePortal = j>=0 && v.portalWarp===true && v.x >= PORTAL_X*FIELD_K;
  FS.until(()=>!enemies.includes(v), 1000, false);
  FS.step(5);
  r.sheGotAway = icenEscapes===esc0+1 && NOTICES.some(n=>n.txt==='THE ICENI IS THROUGH THE KNOSSOS');
  for(const e of enemies) if(/^(K|C)/.test(e.uid||'')) e.hp = 0;
  r.completeCard = FS.until(()=>!!objCard && objCard.txt==='ESCORT DESTROYED', 3000, false) >= 0;
  return r;`);

scenario('Practice mode', 'm=40&practice=1', `
  const r = {};
  FS.step(100);
  r.onFromTheAddress = practiceMode===true;
  const l0 = lives; playerDie();
  r.noLifeLost = lives===l0;
  FS.until(()=>waveOver, 40000, false, true); ITEMS.length = 0;
  const w = wave; FS.until(()=>wave===w+1, 6000, false, false);
  practiceMode = false; const l1 = lives; playerDie();
  r.offCostsALife = lives===l1-1;
  return r;`);

scenario('Practice log', 'm=42&practice=1', `
  const r = {};
  FS.step(200);
  r.recording = !!PL && PL.wave===42 && PL.name==='The Hecate';
  // A death by a beam of a named ship.
  const v = enemies.find(e=>e.beams && e.beams.length) || enemies[0];
  plogSrc('beam', v); player.hp = 0; playerDie(); FS.step(2);
  r.deathWithCause = PL.deaths.length===1 && /^beam - /.test(PL.deaths[0].cause);
  // Points lost and why.
  score = 1000; FS.step(1);
  plogLoss('escaped', v); score = Math.max(0, score-100); FS.step(2);
  r.lossWithReason = PL.loss>=100 && PL.events.some(e=>/escaped/.test(e.txt));
  // An objective card goes into the log.
  objAnnounce('OBJECTIVE COMPLETE', 'TEST DONE', 'done'); FS.step(2);
  r.objectiveLogged = PL.cards.some(c=>c.txt==='TEST DONE' && c.tone==='done');
  // Damage by source.
  // FS.step heals the ship first, so one plain update here.
  plogSrc('bolt'); player.hp -= 10; update();
  r.damageBySource = (PL.dmgBy.bolt||0) >= 10;
  // The player's own bolts are counted, the escorts' are not.
  const b0 = PL.bolts; for(const b of player.pb) b.t = 0; player.en = player.enMax; pShoot(); FS.step(1);
  r.boltsCounted = PL.bolts > b0;
  // Clear the wave: it is closed and the next one opens.
  FS.until(()=>waveOver, 40000, false, true); ITEMS.length = 0;
  FS.step(2);
  r.cardShown = (function(){ let n=0; const _t=thPlate; thPlate=function(){ n++; return _t.apply(this, arguments); };
    try{ drawPlogCard(); } finally { thPlate=_t; } return n>0; })();
  const w = wave; FS.until(()=>wave===w+1, 6000, false, false);
  // Lives: every pickup counts, also at the maximum.
  lives = LIVES_MAX; const l0 = PL.picked.life||0;
  // Plain updates: FS.step puts the lives back to 3 every step.
  ITEMS.push({x:player.x, y:player.y, vx:0, vy:0, kind:'life', life:5000}); update(); update(); update();
  r.lifeAtMaxCounted = (PL.picked.life||0)===l0+1 && PL.picked.lifeFull===1;
  // A call is logged by name, with what it cost (v202: points).
  score = 1e6; PL._score = score;
  const _ar = allyReady; allyReady = function(){ return true; };
  const called = callAlly('ter_fenris'); allyReady = _ar; FS.step(2);
  r.callLogged = called && PL.calls.length===1 && /FENRIS/.test(PL.calls[0]) &&
                 PL.events.some(e=>/points[)]/.test(e.txt)) && PL.loss === 0;
  r.closedAndNext = PLOG.length===1 && PLOG[0].wave===42 && PL.wave===43;
  const t = plogText();
  r.textExport = /WAVE 42 - The Hecate/.test(t) && /died: beam/.test(t) && /timeline:/.test(t);
  // The table draws, and a new run starts an empty log.
  setSettings(true); plogOpen = true; draw();
  r.tableDraws = (window._plogRects||[]).some(x=>x.act==='copy');
  setSettings(false);
  r.closesWithSettings = plogOpen===false;
  launchGame();
  r.newRunEmpty = PLOG.length===0;
  return r;`);

scenario('Warp sheets and the Sidhe', 'm=1', `
  const r = {};
  r.sidhe = priDef('scatter').name==='Sidhe';
  // The frame size comes from the sheet: 256 in a 2304 sheet, 100 in the old one.
  const mk = w=>{ const c=document.createElement('canvas'); c.width=w; c.height=w; c.complete=true; return c; };
  const calls = []; const _d = ctx.drawImage;
  ctx.drawImage = function(){ calls.push([...arguments].slice(1)); };
  const _s = WARP_IMG;
  try{
    Object.defineProperty(WARP_IMG, 'naturalWidth', {value:2304, configurable:true});
    Object.defineProperty(WARP_IMG, 'complete', {value:true, configurable:true});
    drawWarpFrame(0, 200, false);
    fc += 20; drawWarpFrame(0, 200, false);
  } finally { ctx.drawImage = _d; }
  const f = calls[calls.length-1] || [], f0 = calls[calls.length-2] || [];
  r.cellFromSheet = f[2]===256 && f[3]===256;
  // It keeps turning on its own clock, 30 frames a second: 20 steps later
  // (0.2 s) it is 6 frames on, whatever the jump is doing.
  const idx = a=>Math.round(a[0]/256) + 9*Math.round(a[1]/256);
  // v208: 25 frames a second (WarpMap01.eff): 20 steps later 5 frames on
  r.turnsOnItsOwn = ((idx(f) - idx(f0) + 75) % 75)===Math.round(20*WARP_FPS/TICK_HZ);
  // And it spins: the angle it is drawn at moves on with the clock.
  const rots = []; const _r = ctx.rotate, _d2 = ctx.drawImage;
  ctx.rotate = function(a){ rots.push(a); return _r.apply(this, arguments); };
  ctx.drawImage = function(){};
  try { drawWarpFrame(0, 200, false); fc += 50; drawWarpFrame(0, 200, false); } finally { ctx.rotate = _r; ctx.drawImage = _d2; }
  r.spins = rots.length===2 && Math.abs((rots[1]-rots[0]) - 50*WARP_SPIN/TICK_HZ) < 1e-6;
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
  r.faustusParked = !!f && Math.abs(f.y-250*FIELD_K) < 1;
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
    Math.abs(_v1.y-150*FIELD_K)<1 && Math.abs(_v2.y-350*FIELD_K)<1;
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

scenario('Sound build: beams, log, names', 'm=52', `
  const r = {};
  // No sound before the first input, and nothing breaks for it.
  r.silentUntilInput = sndCtx===null;
  let threw = false;
  try{ sndPlay('expl_big', 100); sndAiShot(100); sndTick(); }catch(ex){ threw = true; }
  r.soundCallsSafe = !threw;
  // Charge times as long as the charge sounds run up to the loop.
  const T = (img, fac, large) => beamChargeTicks({img:img, faction:fac}, {large:large});
  r.chargeTerranLarge  = T('ntfdeorion', 'ntf', true) === 3*TICK_HZ;
  r.chargeTervasSmall  = T('ntfdeorion', 'ntf', false) === 1.5*TICK_HZ;
  r.chargeVasLarge     = T('dehatshepsut', 'vasudan', true) === 2*TICK_HZ;
  r.chargeShivanSmall  = T('dedemon', 'shivan', false) === 1*TICK_HZ;
  r.chargeShivanLarge  = T('dedemon', 'shivan', true) === 1.5*TICK_HZ;
  r.chargeLucifer      = T('sdlucifer', 'shivan', true) === 3*TICK_HZ;
  // A ship jumping out takes its beams along.
  FS.step(300);
  const sh = enemies.concat(allies).find(x => x.beams && x.beams.length && !(x.warp>0));
  r.beamShipFound = !!sh;
  if(sh){
    for(const b of sh.beams){ b.state='firing'; b.angle=Math.PI; b.curAngle=Math.PI; }
    // v213: beams are drawn as images (drawBeamRay, glowAt) - count those too
    let n = 0; const st = ctx.stroke, di = ctx.drawImage;
    ctx.stroke = function(){ n++; return st.apply(this, arguments); };
    ctx.drawImage = function(){ n++; return di.apply(this, arguments); };
    sh.warpOut = 0; drawBeams(sh); const firing = n;
    n = 0; sh.warpOut = 50; drawBeams(sh); const jumping = n;
    ctx.stroke = st; ctx.drawImage = di;
    r.beamDrawnWhileFiring = firing > 0;
    r.noBeamWhileJumpingOut = jumping === 0;
    sh.warpOut = 0;
  }
  // The log's scroll arrows win over the row beneath them.
  window._plogRects = [{x:0, y:0, w:500, h:20, act:'row', n:7}, {x:400, y:0, w:26, h:18, act:'up'}];
  plogSel = 2; plogTop = 9;
  plogClick(410, 5);
  r.arrowScrolls = plogTop < 9 && plogSel === 2;
  plogClick(100, 5);
  r.rowStillOpens = plogSel === 7;
  // Mission names in English.
  const german = Object.keys(SCRIPT_WAVES).filter(k => /^(Der|Die|Das) |ue|oe|ae|Erstkontakt|Nachschub|Begegnung/.test(SCRIPT_WAVES[k].name));
  r.namesEnglish = german.length === 0;
  if(german.length) r.germanLeft = german.join(',');
  return r;`);

scenario('Sound build 2: mute, tabs, scan, music', 'm=43', `
  const r = {};
  // Mute: one switch for everything, kept in the browser.
  const on0 = SND.on;
  sndToggleMute();
  r.muteToggles = SND.on === !on0;
  r.muteKept = JSON.parse(localStorage.getItem('fs3_snd')).on === SND.on;
  sndToggleMute();
  // The speaker sits in the bar, clear of the gear.
  draw();
  const mr = window._muteRect;
  r.speakerInBar = !!mr && mr.y < HUD_H && mr.x + mr.w <= W-52;
  r.speakerHit = muteHit({x:mr.x+5, y:mr.y+5}) && !muteHit({x:mr.x-40, y:mr.y+5});
  // Settings: tabs instead of pages.
  setSettings(true); draw();
  const tabs = (window._setRects||[]).filter(q => /^tab/.test(q.act));
  r.sixTabs = tabs.length === 6;   // CONTROLS since v185, TARGETING since v210
  const t3 = tabs[3];
  settingsClick(t3.x+4, t3.y+4);
  r.tabOpensSound = settingsPage === 3;
  draw();
  r.musicRow = (window._setRects||[]).some(q => q.act === 'musvol');
  r.noPageArrows = !(window._setRects||[]).some(q => q.act === 'pagenext' || q.act === 'pageprev');
  setSettings(false);
  // Scan: the start sound once when a scan begins, again only after it broke off.
  const o = {}; let n = 0; const sp = sndStart, sst = sndStop;
  sndStart = function(k){ if(k==='scan_start') n++; return {}; };
  sndStop = function(){};
  sndScanStep(o, 0, 0, true); sndScanStep(o, 0, 0, true);
  const once = n === 1;
  sndScanStep(o, 0, 0, false); sndScanStep(o, 0, 0, true);
  sndScanStep(o, 0, 0, false);
  sndStart = sp; sndStop = sst;
  r.scanStartOnce = once && n === 2;
  // Music: what plays when.
  const L = ['title_screen_01.mp3','fight_01.mp3','fight_02.mp3','boss_01.mp3','boss_vasudan.mp3','game_over_01.mp3','credits.mp3'];
  r.pickTitle = musicPick('title', null, L) === 'title_screen_01.mp3';
  r.pickFightNotSame = musicPick('fight', 'fight_01.mp3', L) === 'fight_02.mp3';
  r.pickBossNotVasudan = musicPick('boss', null, L) === 'boss_01.mp3';
  r.pickVasudanBoss = musicPick('boss_vasudan', null, L) === 'boss_vasudan.mp3';
  r.pickFallback = musicPick('boss', null, ['fight_01.mp3']) === 'fight_01.mp3';
  r.wantFight = musicWant() === 'fight';
  enemies.push({type:'boss', faction:'hol', x:500, y:200, warp:0, dead:false});
  r.wantVasudanBoss = musicWant() === 'boss_vasudan';
  enemies.pop();
  r.noListNoMusic = musicFiles().length === 0;
  return r;`);

scenario('v157: turrets, miners, shields, sounds', 'm=39', `
  const r = {};
  FS.step(50);
  // Mounts: the dorsal guns are turrets now, the Ares has a nose gun.
  r.ursaTurret = mountsFor('boursa').turret.length===1 && mountsFor('boursa').primary.length===3;
  r.medusaTurret = mountsFor('bomedusa').turret.length===1 && mountsFor('bomedusa').primary.length===1;
  r.aresThreeGuns = mountsFor('fiares').primary.length===3;
  // The player's Ursa: the turret fires by itself at an enemy above, not below.
  applyShip('boursa');
  isFiring=false; MOUSE.down=false;
  enemies.length = 0; pBullets.length = 0;
  player.x = 300; player.y = 300; player.ang = 0; player.flip = false; player.turT = 0;
  const e = {type:'fighter', img:'fiherc', sc:0.3, x:360, y:180, hp:1e6, maxHp:1e6, side:'enemy', faction:'ntf', warp:0};
  enemies.push(e);
  for(let i=0;i<40;i++) turretTick(player, true);
  const above = pBullets.filter(b => b.turret).length;
  pBullets.length = 0; e.y = 420; player.turT = 0;
  for(let i=0;i<40;i++) turretTick(player, true);
  const below = pBullets.filter(b => b.turret).length;
  r.turretFiresAbove = above > 0;
  r.turretHoldsBelow = below === 0;
  // An enemy Medusa's turret shoots at the player above it.
  enemies.length = 0; eBullets.length = 0;
  const m = {type:'bomber', img:'bomedusa', sc:0.3, x:400, y:400, ang:0, flip:true, side:'enemy', faction:'ntf', hp:100, turT:0};
  player.x = 380; player.y = 250;
  for(let i=0;i<40;i++) turretTick(m, false);
  r.enemyTurretFires = eBullets.length > 0;
  // The gas miners fire.
  const z = {type:'freighter', img:'gmzephyrus', sc:0.5, x:500, y:250, faction:'ntf', side:'enemy', hp:100};
  eBullets.length = 0;
  for(let i=0;i<600;i++) freighterGuns(z);
  r.minerFires = eBullets.length > 0;
  // Sounds: the Subach has its own, the player's guns cut old voices.
  r.subachSound = PRI_SND.hl7 === 'wpn_subach';
  r.danteSteals = !!SND_STEAL.wpn_dante;
  // Scan loop: runs while scanning, stops when done or when not continued.
  const started = [], stopped = [];
  const ss = sndStart, st = sndStop;
  sndStart = function(n){ const o = {n:n}; started.push(o); return o; };
  sndStop = function(o){ stopped.push(o); };
  const o1 = {};
  sndScanStep(o1, 0, 0, true); sndScanStep(o1, 0, 0, true);
  const oneLoop = started.length === 1 && SND_SCANS.length === 1;
  sndScanStep(o1, 0, 0, false);
  r.scanLoopStartsOnceStopsOnEnd = oneLoop && stopped.length === 1 && SND_SCANS.length === 0;
  const o2 = {};
  sndScanStep(o2, 0, 0, true);
  sndCtx = sndCtx || {state:'running'};
  const fc0 = fc; fc += 5;
  const hp = player.hp; sndTick(); fc = fc0;
  r.scanLoopStopsWhenAbandoned = SND_SCANS.length === 0 && stopped.length === 2;
  sndStart = ss; sndStop = st;
  // Shields: the hull skin is built and drawn.
  r.hullShield = hullShield('fiherc', 'terran', 100, 100, 0.3, false, 0, 1, SH_FLASH) === true;
  r.shieldColours = hullShieldCol('vasudan').glow !== hullShieldCol('terran').glow && hullShieldCol('shivan').glow !== hullShieldCol('terran').glow;
  return r;`);

scenario('v158: arms of the other ships', 'm=52', `
  const r = {};
  FS.step(30);
  const mk = (img, type, side, x, y) => { const o = {type:type, img:img, sc:0.3, x:x, y:y, ang:Math.PI, head:Math.PI, flip:false,
      side:side, faction:side==='ally'?'terran':'ntf', hp:100, maxHp:100, fR:100, fT:0, warp:0}; return o; };
  // An enemy Perseus fires both her FS2 banks, Subach and Prometheus R (v203).
  player.x = 300; player.y = 250; eBullets.length = 0;
  const pe = mk('fiperseus', 'fighter', 'enemy', 500, 250);
  smallFire(pe, player);
  r.subachReach = eBullets.some(b => b.col === priDef('subach').col) && eBullets.some(b => b.col === priDef('promr').col);
  // A Myrmidon: a cone of pellets from one mount, bolts from the others
  // (a Sidhe given by hand since v203: the FS2 banks carry none).
  eBullets.length = 0;
  const my = mk('fimyrmidon', 'fighter', 'enemy', 500, 250);
  my._lo = {p:['scatter', 'hl7', 'hl7'], s:'tornado'};
  smallFire(my, player);
  r.myrmidonMixed = eBullets.length === 7 + 2;
  // An Ares fires Dante shells that burst into shrapnel at range.
  eBullets.length = 0;
  const ar = mk('fiares', 'fighter', 'enemy', 700, 250);
  ar._lo = {p:'dante', s:'infyrno'};     // by hand since v203
  smallFire(ar, player);
  const shell = eBullets.find(b => b.dfuse);
  r.danteShell = !!shell;
  if(shell){ shell.dfuse = 1; shell.x = 400; shell.y = 250; const n0 = eBullets.length; update();
             r.danteBursts = eBullets.filter(b => b.shard).length >= 6; }
  // Heavy bombers drop two bombs at a time on a capital ship of ours.
  eBullets.length = 0;
  const cap = allies.find(a => !a.small) || (allies.push(mk('codeimos','corvette','ally',200,300)), allies[allies.length-1]);
  cap.small = false; cap.type = cap.type || 'corvette';
  const ur = mk('boursa', 'bomber', 'enemy', 600, 200);
  const lo = aiLoadout(ur);
  aiSecondary(ur, 600, 200, lo, WPN.bomber.sec);
  r.twoBombsAtCapital = eBullets.filter(b => b.kind==='bomb').length === 2 && eBullets.every(b => b.tgt === cap);
  // A Stiletto bomber with no capital ship in sight holds its fire.
  eBullets.length = 0;
  const saved = allies.slice(); allies.length = 0;
  const ze = mk('bozeus', 'bomber', 'enemy', 600, 200);
  r.stilettoHolds = aiSecondary(ze, 600, 200, aiLoadout(ze), WPN.bomber.sec) === false && eBullets.length === 0;
  allies.push(...saved);
  // An enemy Infyrno bursts by itself near the player.
  eBullets.length = 0;
  const he = mk('fiherc', 'fighter', 'enemy', 520, 250);
  player.x = 300; player.y = 250;
  aiSecondary(he, 520, 250, {p:'promr', s:'infyrno'}, WPN.fighter.sec);   // v203: no fighter carries one by default
  let burst = false;
  for(let i=0;i<200 && !burst;i++){ player.x = 300; player.y = 250; update(); burst = eBullets.some(b => b.shard); }
  r.enemyInfyrnoBursts = burst;
  // An escort's Infyrno bursts by itself and is not the player's round.
  pBullets.length = 0;
  const ah = mk('fiherc', 'fighter', 'ally', 200, 250);
  const tg = mk('fimyrmidon', 'fighter', 'enemy', 420, 250); tg.hp = 1e6; enemies.push(tg);
  aiSecondary(ah, 200, 250, {p:'promr', s:'infyrno'}, WPN.fighter.sec);
  r.escortRoundNotPlayers = liveBurstRound() === null;
  let ab = false;
  for(let i=0;i<200 && !ab;i++){ tg.x = 420; tg.y = 250; update(); ab = pBullets.some(b => b.shard && b.ally); }
  r.escortInfyrnoBursts = ab;
  // Shivans fly their own lasers (since v161).
  r.shivanOwn = String(aiLoadout({img:'fibasilisk', faction:'shivan'}).p) === 'shm,shh';   // v203: FS2 banks
  // Capital guns see the player in the nebula when he comes close.
  const wm = waveMod; waveMod = 'nebula';
  const cg = {x:500, y:250};
  const al = allies.slice(); allies.length = 0;
  player.x = 300; player.y = 250; const near = capGunTarget(cg) === player;
  player.x = 20; player.y = 480; const far = capGunTarget(cg) === null;
  allies.push(...al); waveMod = wm;
  r.nebulaCapGuns = near && far;
  r.ulyssesNtf = ROLES.ntf_fighters.indexOf('fiulysses') >= 0;
  return r;`);

scenario('v159: fire delay, held secondary, turrets, bursts, Perseus', 'm=31', `
  const r = {};
  FS.step(20);
  // Out of the jump first: in it the old code cooled down as well.
  for(let i=0;i<3000 && inJump();i++) FS.step(1);
  r.outOfJump = !inJump();
  // The bank clocks run down while the trigger is released (v186; the old
  // single clock was broken in v157-v158).
  isFiring = false; MOUSE.down = false; K['Space'] = false; K['KeyZ'] = false;
  player.pb[0].t = 27;
  FS.step(28);
  r.cooldownOnRelease = player.pb[0].t === 0;
  // A held secondary keeps firing as the launcher comes ready.
  const bk = selSecBank(); bk.ammo = Math.min(bk.max, 6); player.secTimer = 0;
  const a0 = bk.ammo;
  SEC_HOLD.rmb = true;
  FS.step(curSec().cd * 3 + 5);
  r.heldSecondaryRefires = a0 - bk.ammo >= 3;
  SEC_HOLD.rmb = false;
  const a1 = bk.ammo; player.secTimer = 0;
  FS.step(curSec().cd * 2);
  r.releasedStops = bk.ammo === a1;
  // ...but a live Infyrno is not set off by a held button.
  const fake = {x:400, y:250, vx:0, vy:0, sec:true, burst:true, wpn:'infyrno', life:999, w:4, h:4};
  pBullets.push(fake); player.secTimer = 0; bk.ammo = 5;
  SEC_HOLD.btn = true; secHoldTick(); SEC_HOLD.btn = false;
  r.heldLeavesInfyrno = pBullets.indexOf(fake) >= 0 && bk.ammo === 5;
  pBullets.splice(pBullets.indexOf(fake), 1);
  // Capacity after the FreeSpace banks: 90 / 2.5 Harpoons, 100 / 1 Hornets.
  r.aresRacks = bankAmmoMax('fiares', 0, 'harpoon') === 36 && bankAmmoMax('fiares', 1, 'tornado') === 80;
  r.hercMk2Racks = bankAmmoMax('fihercmk2', 0, 'harpoon') === 32;
  r.hercRacks = bankAmmoMax('fiherc', 0, 'harpoon') === 24;
  // The Perseus: player hull in the NTF cycle, escort and NTF enemy.
  const ps = ROSTER_NTF.find(s => s.key === 'fiperseus');
  r.perseusRoster = !!ps && ps.unlock === 2000 && ROSTER_NTF.indexOf(ps) === 1;
  r.perseusEscort = ROLES.ally_ter_fighters.indexOf('fiperseus') >= 0;
  r.perseusNtf = ROLES.ntf_fighters.indexOf('fiperseus') >= 0;
  // An escort capital ship fires at a target behind it.
  const cap = {type:'cruiser', img:'craeolus', sc:0.3, x:500, y:250, ang:0, head:0, flip:false,
               side:'ally', faction:'terran', hp:1000, maxHp:1000, warp:0};
  cap.gunT = (entMounts(cap,'primary')||[]).map(() => 1);
  const foe = {type:'fighter', img:'fiherc', sc:0.3, x:150, y:250, hp:1e6, maxHp:1e6, faction:'ntf', side:'enemy', warp:0};
  const saved = enemies.slice(); enemies.length = 0; enemies.push(foe);
  pBullets.length = 0;
  allyFire(cap);
  const shots = pBullets.filter(b => !b.shard && !b.flak && !b.sec);
  r.escortTurretFiresBehind = shots.length > 0 && shots.every(b => b.vx < 0);
  enemies.length = 0; enemies.push(...saved);
  // The heavy round of an enemy capital goes where it is aimed.
  eBullets.length = 0; eBig(300, 200, 'ntf', Math.PI/2);
  r.heavyRoundAimed = eBullets.length === 1 && eBullets[0].vy > 2 && Math.abs(eBullets[0].vx) < 0.01;
  // Bursts are uneven, the damage stays.
  let even = 0, dmgOk = true;
  for(let k=0;k<20;k++){
    pBullets.length = 0;
    shardBurst(400, 250, 9, 5, 3.4, 70, '#fff', '#fff', false);
    const sp = pBullets.map(b => Math.hypot(b.vx, b.vy));
    if(Math.max(...sp) - Math.min(...sp) < 0.2) even++;
    const tot = pBullets.reduce((s,b) => s + b.dmg, 0);
    if(Math.abs(tot - 45) > 0.01) dmgOk = false;
  }
  pBullets.length = 0;
  r.burstsUneven = even === 0;
  r.burstDamageKept = dmgOk;
  return r;`);

scenario('v160: plated capital ships, traits, lead, log', 'm=33', `
  const r = {};
  FS.step(10);
  const mk = (img, type) => { const o = {type:type, img:img, x:500, y:250, hp:1000, maxHp:1000, faction:'ntf', side:'enemy', warp:0}; return o; };
  const hit = (o, src, kind) => { o.hp = 1000; damageEnemy(o, 100, null, null, true, kind||'bolt', src); return 1000 - o.hp; };
  const de = mk('ntfcodeimos', 'corvette');
  r.deimosStrongVsGuns = Math.abs(hit(de, 'gun') - 55) < 0.01;
  r.shardsLoseMore = Math.abs(hit(de, 'shard') - 100*ARMOR.strong*ARMOR_SHARD) < 0.01;
  r.bombsFull = Math.abs(hit(de, 'bomb', 'sec') - 100) < 0.01 && Math.abs(hit(de, 'missile', 'sec') - 100) < 0.01;
  r.capitalGunsFull = Math.abs(hit(de, 'capgun') - 100) < 0.01;
  const fe = mk('ntfcrfenris', 'cruiser');
  r.fenrisProneToBeams = Math.abs(hit(fe, 'beam', 'beam') - 150) < 0.01 && Math.abs(hit(fe, 'gun') - 70) < 0.01;
  const he = mk('ntfdehecate', 'destroyer');
  r.hecateProneToBombs = Math.abs(hit(he, 'bomb', 'sec') - 150) < 0.01;
  const fi = {type:'fighter', img:'fiherc', x:500, y:250, hp:1000, maxHp:1000, sh:0, faction:'ntf', warp:0};
  r.fightersUnplated = Math.abs(hit(fi, 'gun') - 100) < 0.01;
  const fr = {type:'freighter', img:'frbes', x:500, y:250, hp:1000, maxHp:1000, faction:'ntf', warp:0};
  r.freightersUnplated = Math.abs(hit(fr, 'gun') - 100) < 0.01;
  // An enemy fighter's bolt on one of our corvettes is plated too.
  r.enemyBoltMarked = eSrc({sm:true}) === 'gun' && eSrc({kind:'bomb'}) === 'bomb' && eSrc({}) === 'capgun';
  // Traits that move: the Mentu drifts faster, once.
  const me = {type:'cruiser', img:'crmentu', vy:0.3};
  hullTraitsOnce(me); hullTraitsOnce(me);
  r.mentuAgile = Math.abs(me.vy - 0.54) < 0.001;
  // The Aten fires its flak twice as often.
  r.atenFlak = HULL_TRAITS.craten.flak === 2;
  // Escort capital guns lead a moving target.
  const cap = {type:'cruiser', img:'craeolus', sc:0.3, x:200, y:250, ang:0, head:0, flip:false,
               side:'ally', faction:'terran', hp:1000, maxHp:1000, warp:0};
  cap.gunT = (entMounts(cap,'primary')||[]).map(() => 1);
  const foe = {type:'fighter', img:'fiherc', sc:0.3, x:600, y:250, vx:0, vy:3, hp:1e6, maxHp:1e6, faction:'ntf', side:'enemy', warp:0};
  const saved = enemies.slice(); enemies.length = 0; enemies.push(foe);
  pBullets.length = 0; allyFire(cap);
  const cs = pBullets.filter(b => b.cap);
  r.escortGunsLead = cs.length > 0 && cs.every(b => b.vy > 0.3);
  r.escortGunsMarked = cs.length > 0;
  enemies.length = 0; enemies.push(...saved); pBullets.length = 0;
  // The practice log says what was flown.
  FS.step(30);
  r.logFlown = !!PL && !!PL.fits && Object.keys(PL.fits).some(k => k.indexOf(player.ship) === 0);
  return r;`);

scenario('v161: capital turrets, point defence, Shivan arms, colours, portal jump', 'm=52', `
  const r = {};
  FS.step(20);
  const mkC = (img, type, fac, side) => { const o = {type:type, img:img, sc:0.3, x:560, y:250, ang:0, head:0,
      flip:(side!=='ally'), side:side||'enemy', faction:fac, hp:5000, maxHp:5000, warp:0, pts:0}; return o; };
  // One gun per mount, for good.
  // v201: the NTF hulls have models and their turrets' own guns; the rule
  // is for hulls without one
  const cr = mkC('xxcruiser', 'cruiser', 'ntf');
  r.cruiserLightOnly = [0,1,2,3,4,5].every(i => capGun(cr, i) === CAP_GUNS.tt);
  const de0 = mkC('xxdestroyer', 'destroyer', 'ntf');
  r.destroyerHeavyThird = capGun(de0, 2) === CAP_GUNS.tht && capGun(de0, 0) === CAP_GUNS.tt && capGun(de0, 5) === CAP_GUNS.tht;
  const de = mkC('ntfdeorion', 'destroyer', 'ntf');
  r.ntfModelGuns = capGun(de, 0) === mountsFor('ntfdeorion').primary[0].g;
  const sd = mkC('dedemon', 'destroyer', 'shivan');
  // v199: the Demon has a model - her guns are her turrets' own
  r.shivanGuns = capGun(sd, 0) === mountsFor('dedemon').primary[0].g && !!capGun(sd, 0).snd;
  // The Orion's heavy turrets fire in threes, in her race's colour.
  eBullets.length = 0;
  capGunShot(de, 500, 250, Math.PI, CAP_GUNS.tht, false, false);
  r.orionTriple = eBullets.length === 3 && eBullets.every(b => b.big && b.col === RACE_COL.terran.core);
  eBullets.length = 0;
  capGunShot(sd, 500, 250, Math.PI, CAP_GUNS.stl, false, false);
  r.shivanRed = eBullets.length === 1 && eBullets[0].col === RACE_COL.shivan.core;
  // Point defence: an enemy capital shoots at a bomb of ours first.
  pBullets.length = 0; eBullets.length = 0;
  const bomb = {x:520, y:250, vx:1.5, vy:0, w:16, h:16, sec:true, type:'bomb', life:300, dmg:80};
  pBullets.push(bomb);
  r.pdSeesBomb = pdTarget(cr, {x:560, y:250}, false) === bomb;
  const pdr = {x:bomb.x, y:bomb.y, vx:0, vy:0, w:8, h:4, pd:true};
  r.pdKillsBomb = pdHit(pdr) === true && pBullets.indexOf(bomb) < 0;
  // ...and an escort at an enemy bomb.
  const eb = {x:220, y:250, vx:-1, vy:0, w:15, h:15, kind:'bomb', hp:1, faction:'ntf'};
  eBullets.push(eb);
  const al = mkC('craeolus', 'cruiser', 'terran', 'ally');
  r.escortPdSeesBomb = pdTarget(al, {x:200, y:250}, true) === eb;
  eBullets.length = 0;
  // Shivan fighters: red lasers, the Mega one heavy and short.
  const sh = {type:'fighter', img:'fimanticore', faction:'shivan'};
  const bo = {type:'bomber', img:'bonephilim', faction:'shivan'};
  r.shivanLoadouts = aiLoadout(sh).p === 'shm' && aiLoadout(bo).p === 'shl' && aiLoadout(bo).pair === true;   // v203: FS2 banks
  r.megaLaser = priDef('shm').range > 0 && priDef('shm').dmg === 30/18 && /^#ff/.test(priDef('shm').col);
  r.nephilimTurret = !!(mountsFor('bonephilim').turret && mountsFor('boseraphim').turret);
  // Flak is the Dante.
  eBullets.length = 0; flakBurst(400, 250, false, 'ntf');
  r.flakDanteColours = eBullets.length > 0 && eBullets.every(b => b.col === priDef('dante').col);
  eBullets.length = 0;
  // A ship through the Knossos jumps into a vortex ahead of her.
  const ic = mkC('coiceni', 'cruiser', 'ntf'); ic.portalWarp = true; ic.warpOut = 100; ic.warpMax = 100;
  IMGS.coiceni = IMGS.coiceni || IMGS.ntfcraeolus;
  r.portalJumpFs = !!fsWarp(ic);
  // Everything draws: lasers of every side, ordnance of every race.
  pBullets.push({x:300, y:200, vx:6, vy:0, w:11, h:4, dmg:1, col:'#ccff88', glow:'rgba(180,255,80,0.3)'});
  eBullets.push({x:400, y:200, vx:-4, vy:0, w:8, h:4, dmg:1, faction:'shivan', col:'#ff4a30', glow:'rgba(255,40,20,0.4)'});
  eBullets.push({x:420, y:220, vx:-2, vy:0, w:11, h:6, kind:'missile', faction:'vasudan', dmg:1});
  let drew = true; try{ draw(); draw(); }catch(ex){ drew = String(ex); }
  r.drawsLasers = drew === true;
  pBullets.length = 0; eBullets.length = 0;
  // The log names the secondary even before one was chosen.
  r.logNoUndefined = !Object.keys(PL.fits||{}).some(k => /undefined/.test(k));
  return r;`);

scenario('v162: inertia, keys, flight, drift, debris, escorts', 'm=31', `
  const r = {};
  FS.step(20);
  for(let i=0;i<3000 && inJump();i++) FS.step(1);
  // Inertia: from rest the ship takes several steps to reach full speed,
  // and it glides on when the pointer stops asking.
  player.x = 200; player.y = 300; player.mvx = 0; player.mvy = 0;
  // v209: the ship is TEMPO_K faster, so the pointer is that much further
  MOUSE.x = 200 + 500*(typeof TEMPO_K !== 'undefined' ? TEMPO_K : 1); MOUSE.y = 300;
  FS.step(1);
  const v1 = Math.hypot(player.mvx, player.mvy);
  FS.step(60);
  const vFull = Math.hypot(player.mvx, player.mvy);
  r.speedsUp = v1 > 0 && v1 < player.spd*0.3 && vFull > player.spd*0.9;
  MOUSE.x = player.x; MOUSE.y = player.y;
  const x0 = player.x; FS.step(1);
  r.glides = player.x > x0 + 0.5;
  FS.step(120);
  // v211: from twice the pace it glides out a little longer - scaled with it
  r.stops = Math.hypot(player.mvx, player.mvy) < 0.01*(typeof TEMPO_K !== 'undefined' ? TEMPO_K : 1);
  r.nimbleFaster = (function(){ const t0 = player.turn; player.turn = 0.18; const a = playerInertia().acc/player.spd;
                    player.turn = 0.10; const b = playerInertia().acc/player.spd; player.turn = t0; return a > b*1.8; })();
  // WASD no longer flies the ship.
  const y0 = player.y; K['KeyW'] = true; FS.step(10); K['KeyW'] = false;
  r.noWasd = Math.abs(player.y - y0) < 0.5;
  // The bar shows the keys of the buttons that open a window.
  const keys = []; const of = ctx.fillText;
  ctx.fillText = function(s){ keys.push(String(s)); return of.apply(this, arguments); };
  draw(); ctx.fillText = of;
  // v207: from the key table - F2 hangar, shift R rearm, F4 settings
  r.keyHints = ['F2','\u21e7R','F4'].every(k => keys.indexOf(k) >= 0);
  // Capital ships turn their drift round, they do not flip it.
  const c = {type:'cruiser', y:300, vy:0.4, minY:200, maxY:320, subs:null};
  let flips = 0, prev = c.vy;
  for(let i=0;i<400;i++){ capDrift(c, 1); if(Math.abs(c.vy - prev) > 0.05) flips++; prev = c.vy; }
  r.driftEases = flips === 0 && c.y <= 320.5 && c.y >= 199.5;
  // Wreckage and rammers take a share of at most 500 hull from a capital ship.
  r.debrisCapped = impactBase({type:'corvette', maxHp:4688}) === 500 && impactBase({type:'fighter', maxHp:48}) === 48;
  // Escorts leave ships alone that are to be taken, disabled or scanned.
  r.escortsSpare = escortSpares({captureLock:true}) && escortSpares({disableTgt:true, disableMet:false})
                && !escortSpares({disableTgt:true, disableMet:true}) && !escortSpares({});
  // Fighters: a hit makes them jink; wingmen keep a slot by the leader.
  const f = enemies.find(e => e.type==='fighter' && !(e.warp>0));
  if(f){ f.jinkCd = 0; f.jinkT = 0; let jinked = false;
         for(let i=0;i<20 && !jinked;i++){ f.jinkReq = true; f.jinkCd = 0; flySmall(f); jinked = f.jinkT > 0; }
         r.jinksWhenHit = jinked; }
  else r.jinksWhenHit = 'no fighter';
  return r;`);

scenario('v163: M61 The Reconnaissance', 'm=61', `
  const r = {};
  r.shivanCycle = cycleTabs() && player.ship==='fimyrmidon' && ALLY_FAC_ON.terran && ALLY_FAC_ON.vasudan;
  FS.step(20);
  for(let i=0;i<3000 && inJump();i++) FS.step(1);
  const a = FS.ids('A1')[0];
  r.aeolusGuarded = !!a && a.guard === true && a.callsOk === true;
  // Only an allied destroyer opens the hangar; there is none here.
  shipUnlockedFac = {terran:3, vasudan:3}; shipUnlocked = 6;
  r.noSwitchWithoutDestroyer = shipSwapReady() === false;
  r.bothSupportTabs = callTabOpen('terran') && callTabOpen('vasudan');
  // The Shivans come out of the portal, in its vortex.
  FS.step(600);
  const rk = FS.ids('R1')[0];
  r.throughPortal = !!rk && rk.portalWarp === true;
  r.smallThroughPortal = enemies.some(e => (e.type==='fighter'||e.type==='bomber') && e.portalWarp);
  r.danteOpen = weaponOpen(priDef('dante'));
  // A Rakshasa that goes down is replaced, each one tougher (v164).
  const hp1 = rk ? rk.maxHp : 0;
  if(rk){ FS.killId('R1'); FS.step(300); }
  const rk2 = FS.ids('R1')[0];
  r.replaced = !!rk2 && rk2 !== rk;
  r.tougher = !!rk2 && rk2.maxHp > hp1*1.2;
  if(rk2){ rk2.warp = 0; FS.killId('R1'); FS.step(300); }
  const rk3 = FS.ids('R1')[0];
  r.tougherStill = !!rk3 && rk3.maxHp > rk2.maxHp*1.2;
  r.noDestroyer = !SCRIPT_WAVES[61].u.some(u => u.c==='de');
  // Escalation: more small craft at once as time goes on.
  const live0 = waveLive;
  FS.until(()=>spawnT > 62*TICK_HZ, 8000, true);
  r.escalates = waveLive > live0;
  // The end: the Aeolus goes down, the Shivans jump out, the wave ends.
  score = Math.max(score, 5000);       // v202: kills by others pay nothing now
  const s0 = score;
  const aa = FS.ids('A1')[0]; if(aa) aa.hp = 0;
  FS.step(40 + (aa ? deathRollLen(aa) : 0));      // v183: the long way
  r.penalty = score <= s0 - 900 + 400;     // 900 off, give or take a kill
  r.withdraw = enemies.filter(e => !e.scenery && !e.invuln).every(e => e.warpOut > 0 || e.dead);
  const t = FS.until(()=>waveOver, 2000, false, false);
  r.ends = t >= 0;
  return r;`);

scenario('v163: Dante not before the Shivan cycle', 'm=60', `
  score = 99999;
  return {danteLocked: !weaponOpen(priDef('dante')), sidheOpen: weaponOpen(priDef('scatter')), noTabs: !cycleTabs()};`);

scenario('v163: support tabs follow the destroyers', 'm=61', `
  const r = {};
  FS.step(20);
  for(let i=0;i<3000 && inJump();i++) FS.step(1);
  for(const a of allies) a.callsOk = true;
  // callsOk: placed by a mission, so she does not block the call herself.
  const ty = mkAlly('vas_typhon'); ty.warp = 0; ty.callsOk = true; allies.push(ty);
  toggleCallMenu();
  r.opensOnVasudan = callMenu && callTab === 'vasudan';
  r.oneColumn = callCols().length === 1 && callCols()[0].every(e => e.d.fac === 'vasudan');
  r.terranShut = !callTabOpen('terran');
  // A Terran call is refused while its tab is shut.
  const n = allies.length;
  r.refused = callAlly('ter_fenris') === false && allies.length === n;
  drawCallMenu();      // drawn by the frame loop, after draw()
  r.tabRects = (window._callRects||[]).filter(x => x.tab).length === 1;
  setCallMenu(false);
  allies.splice(allies.indexOf(ty), 1);
  toggleCallMenu();
  r.bothWithout = callTabOpen('terran') && callTabOpen('vasudan');
  drawCallMenu();      // drawn by the frame loop, after draw()
  r.twoTabRects = (window._callRects||[]).filter(x => x.tab).length === 2;
  setCallMenu(false);
  return r;`);

scenario('v165: M62 the Orion opens the Terran tab', 'm=62', `
  FS.step(20);
  for(let i=0;i<3000 && inJump();i++) FS.step(1);
  FS.step(300);
  shipUnlockedFac = {terran:3, vasudan:3}; shipUnlocked = 6;
  return {orion: FS.ids('A1').length===1 && FS.ids('A1')[0].guard===true,
          terranOnly: hangarTabOpen('terran') && !hangarTabOpen('vasudan'),
          switchReady: shipSwapReady(),
          cruisersThroughPortal: FS.ids('K1').length===1 && FS.ids('K1')[0].portalWarp===true};`);

scenario('v165: M63 Charybdis lets the beams see', 'm=63', `
  const r = {};
  FS.step(20);
  for(let i=0;i<3000 && inJump();i++) FS.step(1);
  const c = FS.ids('C1')[0];
  for(let i=0;i<600 && c.warp>0;i++) FS.step(1);
  r.awacs = !!c && c.awacs===true && nebulaOn();
  // A fighter inside her circle can be locked by our anti-fighter beams,
  // one outside cannot, and heavy beams stay blind.
  const near = {x:c.x+120, y:c.y, type:'fighter', side:'enemy', dead:false, warp:0, img:'fiastaroth', sc:0.3};
  const far  = {x:c.x+420, y:c.y, type:'fighter', side:'enemy', dead:false, warp:0, img:'fiastaroth', sc:0.3};
  enemies.push(near, far);
  const tg = beamTargets(c, false);
  r.insideSeen = tg.indexOf(near) >= 0;
  r.outsideBlind = tg.indexOf(far) < 0;
  r.heavyBlind = beamTargets(c, true).length === 0;
  enemies.splice(enemies.indexOf(near),1); enemies.splice(enemies.indexOf(far),1);
  // Her ring, read off here and not at the end of the run: once her
  // attackers are down the mission sends her out ('raus C1'), and from
  // v232 it does that whether or not something else was lost - lostMax no
  // longer holds an effect back, only a card. She was then gone by the end
  // of the run and the ring with her, which says nothing about the ring.
  let ringDrawn = false; const arc = ctx.arc;
  ctx.arc = function(x, y, rad){ if(rad===AWACS_R) ringDrawn = true; return arc.apply(this, arguments); };
  try{ draw(); } finally { ctx.arc = arc; }
  r.sheIsHere = allies.indexOf(c) >= 0 && !c.dead;
  r.ringDrawn = ringDrawn;
  // Without her, nothing.
  c.dead = true; const n2 = {x:c.x+60, y:c.y, type:'fighter', side:'enemy', dead:false, warp:0, img:'fiastaroth', sc:0.3};
  enemies.push(n2); r.goneBlind = beamTargets(FS.ids('A1')[0], false).indexOf(n2) < 0; enemies.pop(); c.dead = false;
  // In play the beams actually fire at small craft.
  let fired = 0;
  for(let i=0;i<3000*Math.max(1, FIELD_K/2);i+=20){ FS.step(20); for(const a of allies) for(const b of (a.beams||[])) if(!b.large && b.state==='firing' && b.tgt && (b.tgt.type==='fighter'||b.tgt.type==='bomber')) fired++; }
  r.beamsFire = fired > 0;
  return r;`);

scenario('v165: M64 stragglers', 'm=64', `
  const r = {};
  FS.step(400);
  const k = FS.ids('K1')[0];
  r.ntfCruiser = !!k && k.faction==='ntf' && k.escaping>0 && waveFeud;
  r.bothFlags = enemies.some(e=>e.type==='fighter'&&e.faction==='ntf') && enemies.some(e=>e.type==='fighter'&&e.faction==='shivan');
  for(const s of k.subs) if(s.id==='engines'){ s.hp=0; s.dead=true; }
  FS.step(100);
  r.stopped = k.escaping===0 && k.scenery===true;
  return r;`);

scenario('v165: M65 one buoy more lost than allowed: no success card', 'm=65', `
  const cards=[]; const oa=objAnnounce; objAnnounce=function(a,b){ cards.push(b); return oa.apply(this,arguments); };
  FS.step(200);
  for(const id of ['P1','P2']){ const p=FS.ids(id)[0]; if(p) p.hp=0; FS.step(40); }
  FS.until(()=>waveOver, 30000, true, true);
  return {failed: cards.indexOf('TOO MANY BUOYS LOST')>=0, noSuccess: cards.indexOf('THE BUOY CHAIN STANDS')<0};`);

scenario('v166: M66 freighters come in from the edge', 'm=66', `
  const xs = [];
  for(let i=0;i<2000;i++){ FS.step(1); for(const a of allies) if(/^T/.test(a.uid||'') && a._x0==null){ a._x0 = a.x; xs.push(Math.round(a.x)); } }
  return {fromEdge: xs.length>=2 && xs.every(x => x < 0)};`);

scenario('v166: M65 buoys smaller, and they stay to the end', 'm=65', `
  FS.step(300);
  const p = FS.ids('P1')[0];
  const r = {smaller: hullWidth('inpharos') < 0.7*HULL_LEN.inpharos*SIZE_UPM+1,   // v208: a third under her real length
             stays: !!p && p.stay===true};
  FS.until(()=>waveOver, 30000, true, true);
  FS.step(60);
  r.stillThere = FS.ids('P1').length + FS.ids('P2').length + FS.ids('P3').length + FS.ids('P4').length >= 3
                 && allies.filter(a=>a.stay).every(a=>!(a.warpOut>0));
  return r;`);

scenario('v166: no subsystem marks on our own ships, Charybdis lighter', 'm=63', `
  FS.step(400);
  const c = FS.ids('C1')[0], a = FS.ids('A1')[0];
  let drawnOn = []; const ds = drawSubsystems; drawSubsystems = function(e){ drawnOn.push(e.side); return ds.apply(this, arguments); };
  draw(); drawSubsystems = ds;
  return {noAllyMarks: drawnOn.indexOf('ally') < 0, lighter: c.maxHp <= a.maxHp*0.6};`);

scenario('v168: arrivals open inside the ring', 'm=61', `
  FS.step(20);
  const p = enemies.find(o=>o.img==='inknossos45deg');
  const rx = IMGS[p.img].width*p.sc*0.5, ry = IMGS[p.img].height*p.sc*0.5;
  let inside = 0, n = 0;
  for(let i=0;i<200;i++){ const q = portalPoint(); n++;
    const u = (q.x-p.x)/rx, w = (q.y-p.y)/ry;
    if(u*u + w*w <= 0.56*0.56 && q.x <= p.x && q.x <= MW-14) inside++; }
  return {inside: inside === n};`);

scenario('v168: M65 done means the Shivans pull out', 'm=65', `
  const cards=[]; const oa=objAnnounce; objAnnounce=function(a,b){ cards.push(b); return oa.apply(this,arguments); };
  let doneAt = -1;
  for(let t=0;t<30000 && !waveOver;t+=20){
    if(t%200===0) FS.killSmall(); FS.step(20);
    if(doneAt<0 && cards.indexOf('THE BUOY CHAIN STANDS')>=0){ doneAt = spawnT; }
  }
  return {success: doneAt >= 0, endsSoon: waveOver, noReinf: !evReinf};`);

scenario('v168: M66 notices count what got through', 'm=66', `
  const notes=[]; const nt=notice; notice=function(t){ notes.push(t); return nt.apply(this,arguments); };
  for(let t=0;t<9000 && !waveOver;t+=20){ if(t%200===0) FS.killSmall(); FS.step(20); }
  const thr = notes.filter(n=>/THROUGH/.test(n) && /SAFE SO FAR/.test(n));
  return {counted: thr.length>0 && thr.every((n,i)=>n.indexOf(String(i+1)+' SAFE')>=0)};`);

scenario('v169: M67 TAG', 'm=67', `
  const r = {};
  r.tagOpen = weaponOpen(secDefP('tagc'));
  r.fitted = player.sb[player.sb.length-1].key==='tagc' && player.sec==='tagc';
  FS.step(400);
  const g = FS.ids('G1')[0], o = FS.ids('A1')[0];
  r.notWithout = beamTargets(o, true).indexOf(g) < 0;
  // A TAG missile on the miner marks it, and the Orion's heavy beams take it.
  pBullets.push({x:g.x-20, y:g.y, vx:2, vy:0, w:18, h:6, sec:true, type:'missile', homing:false, life:50, dmg:6, wpn:'tag'});
  FS.step(30);
  r.tagged = g.tagT > 0;
  r.beamsSeeIt = beamTargets(o, true).indexOf(g) >= 0;
  let mark = false; const ds = ctx.strokeStyle; draw(); r.drawn = true;
  return r;`);

scenario('v169: Dante and TAG not before their missions', 'm=66', `
  score = 99999; return {tagLocked: !weaponOpen(secDefP('tagc'))};`);

scenario('v169: M68 the Setekh jams, the bombs come from afar', 'm=68', `
  const r = {};
  FS.step(20); for(let i=0;i<3000 && inJump();i++) FS.step(1);
  const c = FS.ids('C1')[0];
  let spawnedSmall = 0, far = true, n = 0, jamEnded = -1;
  const seen = new Set(enemies);
  for(let t=0;t<4000;t+=20){ FS.step(20);
    // The jam is the Setekh herself: jammerAlive() looks for an ALLY with
    // .jammer and gives up when she is dead or warping out, and then a
    // reinforcement wing is let through entirely correctly. She is in the
    // middle of a Shivan patrol here, so now and then she does not last the
    // 4000 ticks - which made this read fail in about one run of ten, on
    // v233 as well as v234. Counting stops where the jam does.
    if(jamEnded < 0 && !jammerAlive()) jamEnded = t;
    for(const e of enemies) if(!seen.has(e)){ seen.add(e);
      if(jamEnded < 0 && (e.type==='fighter'||e.type==='bomber') && !e.uid) spawnedSmall++; }
    for(const p of BOMB_PORTALS) if(p.tgt && !p._chk){ p._chk = 1; n++; if(Math.hypot(p.x-c.x, p.y-c.y) < SSB_MIN_D) far = false; }
    for(const e of enemies) if((e.type==='fighter'||e.type==='bomber') && !(e.warp>0)) e.hp = 0; }
  // Only the patrol's own wings (with an id) come; no reinforcement wing.
  r.theJamHeld = jamEnded < 0 ? 'the whole 4000 ticks' : ('the Setekh was gone at tick ' + jamEnded);
  r.reinfOnButJammed = evReinf && spawnedSmall === 0;
  r.bombsCame = n > 0; r.allFar = far;
  c.hp = 0; FS.step(40);
  let after = 0; for(let t=0;t<4000;t+=20){ FS.step(20); for(const e of enemies) if(!seen.has(e)){ seen.add(e); if(e.type==='fighter' && !e.uid) after++; }
    for(const e of enemies) if((e.type==='fighter'||e.type==='bomber') && !(e.warp>0)) e.hp = 0; }
  r.reinfAfterLoss = after > 0;

  // And the way out has to stay open. lostMax:0 sat on the only three
  // events that switch the reinforcements off and pull the Shivans out, so
  // losing her - she carries guard:true, protLost goes to 1 - locked all
  // three for good: the reinforcements never stopped and the mission had no
  // end at all (Silvio, v231). Fought out to the finish here, the way a
  // player would: everything that can be shot down, is.
  r.stillRunning = !waveOver;
  const w0 = wave;
  // Every card the mission announces from here on. objAnnounce() is the one
  // place a card comes from, so this is what the player would see.
  const cards = [];
  const oa = objAnnounce;
  objAnnounce = function(head, txt, tone){ cards.push(head + ' / ' + txt); return oa.apply(null, arguments); };
  // The patrol is what the mission asks for, and only the patrol: the
  // reinforcement wings carry no id and keep coming. Shot down exactly as
  // the objective reads.
  const PATROL = ['K1','K2','M1','E1','B1'];
  const patrolLeft = () => enemies.some(e => PATROL.indexOf(e.uid) >= 0);
  for(let t = 0; t < 20000 && patrolLeft(); t += 20){
    for(const e of enemies) if(PATROL.indexOf(e.uid) >= 0 && !(e.warp > 0)) e.hp = 0;
    FS.step(20);
  }
  r.patrolDown = !patrolLeft();
  // With her lost, lostMax:0 used to lock the three events that answer the
  // patrol being down - among them this one. The reinforcements then had
  // nothing left to switch them off.
  r.reinforcementsStop = !evReinf;
  // and with them off the field can be cleared and the wave ends
  for(let t = 0; t < 8000 && wave === w0 && !waveOver; t += 20){
    for(const e of enemies) if(!e.scenery && !e.invuln && !(e.warp > 0)) e.hp = 0;
    FS.step(20);
  }
  // Weak on purpose, and said so: the harness shoots perfectly, so a clear
  // instant turns up for it even with the reinforcements running, and this
  // holds on the broken version too. reinforcementsStop above is the one
  // that fails there. For a player the field is in practice never clear,
  // which is what "the waves never stop" means.
  r.theWaveCanEnd = waveOver || wave > w0;
  objAnnounce = oa;
  // Ended, but not as a success: she was lost, and lostMax still holds the
  // card back. Read off the cards that were announced, not off ev.done -
  // 'abzug' closes the whole script by marking every event done, so a
  // blocked event ends up marked done as well without ever firing.
  r.cardsAnnounced = cards.join(' | ') || '(none)';
  r.noSuccessCard = !cards.some(c => c.indexOf('COMPLETE') >= 0 || c.indexOf('SUCCESS') >= 0);
  r.failedObjective = objFailed === true;
  return r;`);

scenario('v169: M69 the Lucifer cannot be hurt, the clock holds the wave', 'm=69', `
  const r = {};
  FS.step(600);
  const l = FS.ids('L1')[0];
  r.lucifer = !!l && l.img==='sdlucifer' && l.invuln && l.bShield > 0 && !bossAlive;
  const s0 = l.bShield, h0 = l.hp;
  const rp = reactorPos(l, l.reactors[0]);
  damageEnemy(l, 5000, rp.x, rp.y, true, 'beam');
  r.untouched = l.bShield === s0 && l.hp === h0 && !l.reactors[0].dead;
  r.timer = missionTimerLeft() > 0;
  for(let i=0;i<20;i++){ for(const e of enemies) if(!e.scenery && !e.invuln && !(e.warp>0)) e.hp = 0; spawnQ.length = 0; evReinf = false; FS.step(50); }
  r.heldByClock = !waveOver && missionTimerLeft() > 0;
  FS.until(()=>waveOver, 12000, true, false);
  r.endsAfter = waveOver;
  return r;`);

scenario('v169: M70 the Iceni holds until her crew is off', 'm=70', `
  const r = {};
  FS.step(400);
  const i1 = FS.ids('I1')[0];
  i1.hp = -500; FS.step(2);
  r.holds = FS.ids('I1').length === 1 && i1.hp > 0;
  const t0 = FS.until(()=>EV_DOCK['T1'] || EV_DOCK['T2'], 20000, true, false);
  FS.step(5);
  r.rescued = t0 >= 0;
  r.released = FS.ids('I1').length===0 || FS.ids('I1')[0].keepAlive === false;
  return r;`);

scenario('v170: M71 the Ptah is unseen until she fires', 'm=71', `
  const r = {};
  FS.step(20); for(let i=0;i<3000 && inJump();i++) FS.step(1);
  r.ptah = player.ship==='fiptah';
  r.unseen = !playerSeen() && !canLockOn(player) && aiSmallTarget({side:'enemy'}, 300, 300)===null;
  FS.step(500);
  const f = enemies.find(e=>e.type==='fighter' && !(e.warp>0));
  r.patrols = !f || smallTarget(f) !== player;
  pShoot(); player.lastShot = fc;
  r.seenAfterShot = playerSeen();   // seen - a lock is still impossible in the gas
  FS.step(PTAH_SEEN + 5);
  r.goneAgain = !playerSeen();
  const l = FS.ids('L1')[0];
  r.reactorsToScan = !!l && l.scanSubs && l.subs.length === l.reactors.length;
  for(const e of enemies) if(!e.scenery && !e.invuln && !(e.warp>0)) e.hp = 0; spawnQ.length = 0; evReinf = false;
  FS.step(300);
  r.scanHoldsTheWave = !waveOver;
  for(const s of l.subs) s.scanT = 1e9;
  FS.step(30);
  r.scanned = l.scanned === true;
  r.ends = FS.until(()=>waveOver, 8000, true, false) >= 0;
  return r;`);

scenario('v170: M72 Shivan beams see in the gas', 'm=72', `
  FS.step(600);
  const k = FS.ids('K1')[0];
  return {gas: nebulaOn(), seen: beamTargets(k, false).indexOf(player) >= 0,
          allies: beamTargets(k, true).some(a=>a.uid==='A1')};`);

scenario('v170: no Shivan beams in the gas before 72', 'm=68', `
  FS.step(600);
  const k = FS.ids('K1')[0];
  return {blind: beamTargets(k, false).indexOf(player) < 0};`);

scenario('v170: M73 our bombers, their point defence', 'm=73', `
  const r = {};
  FS.step(400);
  r.bombers = allies.filter(a=>a.small && a.type==='bomber').length >= 2;
  const k = FS.ids('K1')[0];
  pBullets.push({x:k.x-120, y:k.y, vx:1, vy:0, w:16, h:16, sec:true, type:'bomb', ally:true, life:300, dmg:80});
  const pts = entMounts(k,'primary');
  r.pdSees = !!pdTarget(k, pts[0], false);
  for(const s of k.subs) if(s.id==='weapons'){ s.hp = 0; s.dead = true; }
  r.weaponsOut = !subOK(k,'weapons');
  return r;`);

scenario('v170: M74 the Lucifer crosses and is through', 'm=74', `
  const r = {};
  FS.step(400);
  const l = FS.ids('L1')[0];
  r.crossing = !!l && l.crossLeft > 0 && l.invuln;
  const x0 = l.x; FS.step(500);
  r.movesLeft = l.x < x0 - 30;
  const s0 = score;
  for(let i=0;i<20000 && FS.ids('L1').length;i+=50){ FS.step(50); for(const e of enemies) if(!e.scenery && !e.invuln && !(e.warp>0) && !e.crossLeft) e.hp=0; }
  r.through = FS.ids('L1').length===0 && EV_LEFT['L1'] === true;
  r.noPenalty = score >= s0;
  r.ends = FS.until(()=>waveOver, 8000, true, true) >= 0;
  return r;`);

scenario('v170: M75 subspace', 'm=75', `
  const r = {};
  FS.step(20); for(let i=0;i<3000 && inJump();i++) FS.step(1);
  r.subspace = subspaceOn();
  r.noShield = player.maxSh === 0 && player.sh === 0;
  FS.step(400);
  r.enemyNoShield = enemies.filter(e=>e.type==='fighter').every(e=>!e.maxSh);
  r.noSupport = !allyReady();
  toggleCallMenu(); r.menuShut = !callMenu;
  const l = FS.ids('L1')[0];
  r.reactorOnly = !!l && l.reactorOnly && !(l.bShield>0) && !l.subs;
  const h0 = l.hp; damageEnemy(l, 3000, l.x, l.y-200, true, 'bolt');
  r.hullUntouched = l.hp === h0;
  let n = 0;
  for(const rr of l.reactors){ const p = reactorPos(l, rr); damageEnemy(l, 99999, p.x, p.y, true, 'bolt'); n++; if(n < l.reactors.length) r['stillAlive'+n] = l.hp > 0; }
  r.dead = l.hp <= 0;
  if(!l.dead) killEnemy(l, null, true, false);
  r.finale = FINALE.length > 0;
  FS.step(200);
  r.whiteOut = whiteOut > 0 || FINALE.length === 0;
  r.ends = FS.until(()=>waveOver, 8000, true, true) >= 0;
  ITEMS.length = 0;
  r.next = FS.until(()=>wave===76, 6000, false, false) >= 0;
  r.shieldBack = player.maxSh > 0;
  return r;`);

scenario('v170: TAG fixes (Silvio, v169)', 'm=67', `
  const r = {};
  FS.step(400);
  const g = FS.ids('G1')[0], o = FS.ids('A1')[0];
  // A missile always strikes through the secondary path now, so it tags.
  let tagged = 0;
  for(let k=0;k<6;k++){
    g.tagT = 0;
    pBullets.push({x:g.x-30, y:g.y, vx:3, vy:0, w:18, h:6, sec:true, type:'missile', homing:false, life:60, dmg:6, wpn:'tag'});
    FS.step(25); if(g.tagT > 0) tagged++;
  }
  r.alwaysTags = tagged === 6;
  r.fairGame = !playerOnly(g);
  const h0 = g.hp;
  for(let i=0;i<800 && g.hp===h0;i+=20){ g.tagT = TAG_TIME; FS.step(20); }
  r.beamsHurtIt = g.hp < h0 || g.dead;
  return r;`);

scenario('v170: M69 the Lucifer fires, a TAG on her draws the beams', 'm=69', `
  FS.step(700);
  const l = FS.ids('L1')[0], a = FS.ids('A1')[0];
  const r = {fires: !l.noFire};
  r.notUntagged = beamTargets(a, true).indexOf(l) < 0;
  l.tagT = TAG_TIME;
  r.tagDraws = beamTargets(a, true).indexOf(l) >= 0;
  return r;`);

scenario('v170: M70 an Azrael, a clean jump, the Iceni scuttled', 'm=70', `
  const r = {};
  FS.step(20);
  let x = null, jumped = false, mOK = true;
  for(let i=0;i<2000*Math.max(1, FIELD_K/2);i++){ FS.step(1); x = FS.ids('X1')[0] || x;
    if(x && x.warpOut>0){ jumped = true; mOK = x.warpMax > 1 && x.warpOut <= x.warpMax; break; } }
  r.azrael = !!x && x.img==='trazrael';
  r.cleanJump = jumped && mOK;
  const t0 = FS.until(()=>EV_DOCK['T1'] || EV_DOCK['T2'], 20000, true, false);
  r.rescued = t0 >= 0;
  FS.step(20);
  r.countdown = missionTimerLeft() > 0;
  FS.until(()=>FS.ids('I1').length===0, 3000, true, false);
  r.scuttled = FS.ids('I1').length === 0 && !EV_LEFT['I1'];
  return r;`);

scenario('v170: small craft clear out of a big blast', 'm=67', `
  const r = {};
  FS.step(500);
  const g = FS.ids('G2')[0];
  // One of ours right beside the miner.
  const f = mkAllySmall('fighter', 'terran', 'fiherc', g.y); f.warp = 0; f.x = g.x - 40; f.y = g.y; allies.push(f);
  const d0 = Math.hypot(f.x-g.x, f.y-g.y);
  g.hp = 0; FS.step(2);
  r.fuse = BLAST_FUSE.length > 0 && DANGER.length > 0;
  FS.step(BIG_BLAST_FUSE - 10);
  r.ranAway = Math.hypot(f.x-g.x, f.y-g.y) > d0 + 120 || f.dead;
  FS.step(30);
  r.waveCame = BLAST_FUSE.length === 0;
  return r;`);

scenario('v171: a beam keeps biting after the TAG runs out', 'm=67', `
  const r = {};
  FS.step(400);
  const g = FS.ids('G1')[0];
  // Tag her, wait until a beam is on her, then let the TAG lapse.
  g.tagT = TAG_TIME;
  let b = null;
  for(let i=0;i<1500 && !b;i+=5){ g.tagT = TAG_TIME; FS.step(5);
    for(const a of allies) for(const bb of (a.beams||[])) if(bb.tgt===g && bb.state==='firing') b = bb; }
  r.beamOn = !!b;
  if(b){
    g.tagT = 0; const h0 = g.hp;
    for(let i=0;i<60 && b.state==='firing';i++) FS.step(1);
    r.stillHurts = g.hp < h0 || g.dead;
  }
  return r;`);

scenario('v171: M69 the Lucifer beams the Hecate in the gas', 'm=69', `
  FS.step(200);
  const l = FS.ids('L1')[0], a = FS.ids('A1')[0];
  const r = {gasBeams: !!l.gasBeams, sees: shivanGasSight(a, l)};
  const h0 = a.hp;
  FS.step(1500);
  r.hecateHurt = a.hp < h0;
  r.othersStillBlind = !shivanGasSight(a, {});
  return r;`);

scenario('v171: M70 the Iceni is there, the Azrael waits', 'm=70', `
  const r = {};
  FS.step(5);
  const i1 = FS.ids('I1')[0];
  r.iceniThere = !!i1 && !(i1.warp>0);
  // She sits alongside for a few seconds before she pulls away.
  let x = null, x0 = null, t = -1;
  for(let i=0;i<1200 && t<0;i++){ FS.step(1); x = FS.ids('X1')[0] || x;
    if(x && x.warp<=0){ if(x0===null) x0 = x.x; else if(x.x > x0 + 1) t = i; } }
  r.azraelWaits = t >= Math.round(4*TICK_HZ);
  r.azraelLeaves = t > 0;
  return r;`);

scenario('v171: M74 in the nebula', 'm=74', `
  FS.step(20);
  return {nebula: waveMod==='nebula', noPortal: !portalIn};`);

scenario('v171: M75 not alone, and a sheet without a seam', 'm=75', `
  const r = {};
  FS.step(20); for(let i=0;i<3000 && inJump();i++) FS.step(1);
  FS.step(300);
  const u = FS.ids('W1').filter(a=>!a.dead), h = FS.ids('H1').filter(a=>!a.dead);
  r.ursas = u.length >= 2; r.hercs = h.length >= 2;
  r.alliesNoShield = allies.filter(a=>a.small||a.type==='fighter'||a.type==='bomber').every(a=>!a.maxSh);
  // Ursa bombs head for a reactor.
  let aimed = false;
  for(let i=0;i<1200 && !aimed;i+=5){ FS.step(5);
    aimed = eBullets.concat(pBullets).some(b=>b.aimR) || FS.ids('L1')[0].reactors.some(x=>x.dead); }
  r.aimsReactor = aimed;
  // Kill a flight: it comes back.
  for(const a of FS.ids('W1')) a.hp = 0;
  FS.step(30*TICK_HZ);
  r.replaced = FS.ids('W1').filter(a=>!a.dead).length > 0;
  const s = subSheet(SUB_LAYERS[0]);
  r.sheet = !s || (s.width % 2 === 0 && s.height % 2 === 0);
  return r;`);

scenario('v172: M62 the last bombers come at once', 'm=62', `
  // Cruisers die fast, small craft as they come; from the last cruiser on,
  // the bombers should be under way at once.
  const r = {}; let tK = -1, tB = -1;
  const ks = ['K1','K2','K3','K4','K5'];
  for(let t=0;t<12000 && !waveOver;t+=20){
    if(t%200===0) for(const e of enemies){ if(e.warp>0||e.invuln||e.scenery) continue; if(e.type==='cruiser'&&e._a==null) e._a=t; if(e._a!=null&&t-e._a<1000) continue; e.hp=0; }
    FS.step(20);
    if(tK<0 && ks.every(id=>EV_SEEN[id] && FS.ids(id).length===0)) tK = t;
    if(tK>=0 && tB<0 && (FS.ids('B3').length || EV_SEEN['B3'])) tB = t;
  }
  r.ends = waveOver;
  r.bombersAtOnce = tK>=0 && tB>=0 && tB - tK < 3*TICK_HZ;
  return r;`);

scenario('v172: M63 the Charybdis is lighter', 'm=63', `
  FS.step(20);
  const c = FS.ids('C1')[0], a = FS.ids('A1')[0];
  return {lighter: !!c && !!a && c.maxHp < a.maxHp * 0.6};`);

scenario('v172: M70 Lilith on station, Azrael untouchable', 'm=70', `
  const r = {};
  FS.step(5);
  const k = FS.ids('K1')[0], x = FS.ids('X1')[0];
  r.lilithThere = !!k && !(k.warp>0);
  const h = x.hp; damageEnemy(x, 5000, x.x, x.y, true, 'bolt');
  r.azraelUnhurt = x.hp === h && !x.dead;
  FS.until(()=>!!EV_LEFT['X1'], 20000, true, false);
  r.azraelGone = !!EV_LEFT['X1'];
  r.noEscapeCount = escGone === 0;
  return r;`);

scenario('v172: M74 a smaller escort (three cruisers since v175)', 'm=74', `
  FS.step(4500);
  const ids = enemies.filter(e=>!e.invuln && (e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer')).map(e=>e.uid);
  return {escort: JSON.stringify(ids), noDestroyer: FS.ids('D1').length===0 && !enemies.some(e=>e.type==='destroyer')};`);

scenario('v173: Shivan beams are static, others keep their slash', 'm=62', `
  FS.step(2500);
  const r = {};
  const sh = enemies.filter(e=>e.faction==='shivan' && e.beams && e.beams.length);
  r.shivanBeams = sh.length > 0;
  r.allStatic = sh.every(e=>e.beams.every(b=>b.type==='static'));
  const a = FS.ids('A1')[0];
  r.orionStillSlashes = !!a && a.beams.some(b=>b.type==='slash');
  const raw = mountsFor('crcain').beams.map(b=>b.dmg).join(',');
  const cain = enemies.find(e=>e.img==='crcain' && e.beams);
  r.dmgUnchanged = !cain || cain.beams.map(b=>b.dmg).join(',') === raw;
  return r;`);

scenario('v174: in through the Knossos, out through a blue vortex', 'm=61', `
  const r = {};
  let rk = null;
  for(let i=0;i<3000 && !rk;i+=20){ FS.step(20); rk = FS.ids('R1').find(e=>!(e.warp>0)) || null; }
  r.cameThroughPortal = !!rk && rk.portalWarp === true;
  FS.step(300);
  r.turquoiseIn = warpTurquoise({portalWarp:true, warp:50});
  rk.warpMax = 160; rk.warpOut = 160; rk.warpX = rk.x; rk.warpY = rk.y;
  r.blueOut = warpTurquoise(rk) === false;
  // At the portal itself it stays turquoise.
  r.portalOutTurquoise = warpTurquoise({portalWarp:true, portalOut:true, warpOut:50}) === true;
  let ok = true; try{ for(let i=0;i<60;i++){ update(); draw(); } }catch(ex){ ok = String(ex); }
  r.draws = ok === true;
  return r;`);

scenario('v175: FS1 Shivans with the Lucifer, Scorpions first', 'm=74', `
  const r = {}; const seen = {};
  for(let i=0;i<6000;i+=20){ FS.step(20);
    for(const e of enemies) if((e.type==='fighter'||e.type==='bomber') && !e._c){ e._c=1; seen[e.img]=(seen[e.img]||0)+1; }
    if(i%300===0) FS.killSmall(); }
  const fs1 = FS1_SHIVAN.fighters.concat(FS1_SHIVAN.bombers);
  r.onlyFs1Small = Object.keys(seen).length > 0 && Object.keys(seen).every(k=>fs1.indexOf(k)>=0);
  const fi = Object.keys(seen).filter(k=>/^fi/.test(k)).reduce((s,k)=>s+seen[k],0);
  r.scorpionsMost = (seen.fiscorpion||0) > fi*0.3;    // half the pool, random wings
  r.capsFs1 = ['K1','K2','M1'].every(id=>!EV_SEEN[id] || true) && SCRIPT_WAVES[74].u.filter(u=>u.c==='cr'||u.c==='co').every(u=>FS1_SHIVAN.cruisers.indexOf(u.spr)>=0);
  r.counts = JSON.stringify(seen);
  return r;`);

scenario('v175: no FS1 rule without the Lucifer', 'm=73', `
  FS.step(20);
  return {off: waveFs1===false && poolFor('fi_sh')!==FS1_SHIVAN.fighters};`);

scenario('v175: the Lucifer holds her beams three times as long', 'm=69', `
  FS.step(200);
  const l = FS.ids('L1')[0];
  const raw = mountsFor('sdlucifer').beams.map(b=>b.fireT||120);
  const r = {longer: !!l && l.beams.every((b,i)=>b.fireT === Math.round(raw[i]*LUCI_FIRE_MUL)),
             static: !!l && l.beams.every(b=>b.type==='static')};
  const h0 = FS.ids('A1')[0].hp;
  FS.step(3000);
  r.hecateHurt = FS.ids('A1')[0].hp < h0;
  // Other ships keep theirs.
  r.othersUnchanged = mountsFor('crcain').beams[0].fireT === (function(){ const c = enemies.find(e=>e.img==='crcain'); return c ? c.beams[0].fireT : mountsFor('crcain').beams[0].fireT; })();
  return r;`);

scenario('v176: M75 a missed jump costs points, not lives', 'm=75', `
  const r = {};
  FS.step(20); for(let i=0;i<3000 && inJump();i++) FS.step(1);
  FS.step(200);
  r.timer = missionTimerLeft() > 0 && /LUCIFER/.test(missionTimer.label);
  // Only the clock is tested here: the allied flights are taken out of it,
  // or they may finish her before time runs out.
  allies.length = 0; EV_REPL = {};
  const l = FS.ids('L1')[0];
  // One reactor down before time runs out.
  const rr = l.reactors.find(x=>!x.dead); const p = reactorPos(l, rr);
  damageEnemy(l, 99999, p.x, p.y, true, 'bolt');
  const downBefore = l.reactors.filter(x=>x.dead).length;
  const lives0 = lives;
  // Let the clock run out; keep the small craft down so the allies live.
  FS.until(()=>missionTimerLeft() < 30, 20000, true, false);
  let sB = score;
  for(let i=0;i<200 && !missedJumps;i++){ sB = score; FS.step(1); }
  r.missed = missedJumps === 1;
  r.pointsTaken = score <= sB - MISSED_JUMP_PENALTY + 50;
  r.noLifeLost = lives >= lives0;
  r.reactorsKept = l.reactors.filter(x=>x.dead).length >= downBefore && !l.dead;
  r.timerAgain = missionTimerLeft() > 110*TICK_HZ;   // 120 s since v177
  r.fieldCleared = !enemies.some(e=>(e.type==='fighter'||e.type==='bomber') && !(e.warp>0));
  r.notWaveOver = !waveOver;
  // A second miss works as well.
  missionTimer.end = spawnT + 5;
  FS.until(()=>missedJumps>1, 400, false, false);
  r.secondMiss = missedJumps === 2;
  // Then she is finished off and the wave ends.
  for(const x of l.reactors){ if(x.dead) continue; const q = reactorPos(l, x); damageEnemy(l, 99999, q.x, q.y, true, 'bolt'); }
  if(!l.dead && l.hp<=0) killEnemy(l, null, true, false);
  FS.step(50 + deathRollLen(l));                  // v183: the long way
  r.timerStopped = missionTimerLeft() < 0;
  r.ends = FS.until(()=>waveOver, 8000, true, true) >= 0;
  return r;`);

scenario('v177: a small ship vortex in front of a large hull', 'm=70', `
  const r = {};
  FS.until(()=>FS.ids('T1').some(t=>!(t.warp>0)), 3000, true, false);
  const ic = FS.ids('I1')[0], tr = FS.ids('T1')[0];
  r.both = !!ic && !!tr;
  // The transport jumps out right in front of the Iceni.
  tr.x = ic.x; tr.y = ic.y; tr.warpMax = 160; tr.warpOut = 90; tr.warpX = tr.x; tr.warpY = tr.y;
  Object.defineProperty(WARP_IMG, 'naturalWidth', {value:2304, configurable:true});
  Object.defineProperty(WARP_IMG, 'complete', {value:true, configurable:true});
  const order = []; const _d = ctx.drawImage;
  // v194: a damaged Iceni is drawn from her kept picture, not the sprite
  const isIceni = function(img){ return img===IMGS.coiceni || (ic.dm && (img===ic.dm.can || img===ic.dm.frame)); };
  ctx.drawImage = function(img){ if(isIceni(img)) order.push('iceni'); else if(img===WARP_IMG) order.push('vortex'); return _d.apply(this, arguments); };
  try{ draw(); } finally { ctx.drawImage = _d; }
  const iI = order.indexOf('iceni'), iV = order.lastIndexOf('vortex');
  r.vortexOverIceni = iI >= 0 && iV > iI;
  return r;`);

scenario('v177: M75 the Lucifer drives right to left on the clock', 'm=75', `
  const r = {};
  FS.step(20); for(let i=0;i<3000 && inJump();i++) FS.step(1);
  FS.step(100);
  const l = FS.ids('L1')[0];
  r.timer2min = missionTimer.total === 120*TICK_HZ;
  const x0 = l.x;
  r.startsRight = x0 > MW*0.85;
  FS.until(()=>missionTimerLeft() < 60*TICK_HZ, 20000, true, false);
  // About the middle at half time (her glide out of the vortex adds a bit).
  r.halfway = l.x > MW*0.3 && l.x < MW*0.55;
  FS.until(()=>missionTimerLeft() < 2*TICK_HZ, 20000, true, false);
  r.endsLeft = l.x < MW*0.1;
  FS.until(()=>missedJumps>0, 1000, false, false);
  FS.step(5);
  r.backRight = missedJumps===1 && l.x > MW*0.9 && !l.dead;
  return r;`);

scenario('v177: M77 the Sathanas comes through and takes the Hatshepsut', 'm=77', `
  const r = {}; const cards = []; const oa = objAnnounce; objAnnounce = function(a,b){ cards.push(b); return oa.apply(this, arguments); };
  FS.step(200);
  for(let t=0;t<20000 && !EV_SEEN['S1'];t+=20){ FS.step(20);
    if(t%200===0) for(const e of enemies){ if(e.warp>0||e.invuln||e.scenery) continue; e.hp = 0; } }
  r.gateClear = cards.indexOf('THE GATE IS CLEAR') >= 0;
  FS.step(30);
  const s = FS.ids('S1')[0];
  r.sathanas = !!s && s.img==='sdsathanas' && s.invuln;
  r.throughPortal = !!s && s.portalWarp === true;
  FS.until(()=>FS.ids('A1').length===0, 8000, true, false);   // her beams do it since v179
  r.hatshepsutGone = FS.ids('A1').length===0;
  r.noFailCard = !cards.some(c=>/LOST/.test(c) && c!=='');
  r.notOverWhileSheIsHere = !waveOver;
  r.ends = FS.until(()=>waveOver, 12000, true, true) >= 0;
  r.sheLeft = FS.ids('S1').length===0;
  return r;`);

scenario('v177: M78 the Mara in disguise, nine Sathanas, three comm nodes', 'm=78', `
  const r = {};
  FS.step(20);
  r.mara = player.ship==='fimara';
  let hit = 0, sath = 0, mara = false;
  for(let i=0;i<2500*Math.max(1, FIELD_K/2);i++){ const h = player.hp + player.sh; update(); if(i%25===0) draw();
    hit += Math.max(0, h - (player.hp + player.sh)); player.hp = player.maxHp; player.sh = player.maxSh;
    for(const e of enemies){ if(e.img==='sdsathanas' && e.invuln && e.noHold && !e._c){ e._c = 1; sath++; } if(e.img==='fimara') mara = true; } }
  r.disguisedUnhurt = hit < 5 && !disguiseBlown;
  r.noMaras = !mara;
  r.sathanasPass = sath >= 2;
  // A shot on a node gives her away.
  const n = FS.ids('N1')[0];
  damageEnemy(n, 1, n.x, n.y, true, 'bolt');
  r.coverBlown = disguiseBlown === true;
  hit = 0;
  for(let i=0;i<2000*Math.max(1, FIELD_K/2);i++){ const h = player.hp + player.sh; update(); if(i%25===0) draw();
    hit += Math.max(0, h - (player.hp + player.sh)); player.hp = player.maxHp; player.sh = player.maxSh; }
  r.nowHunted = hit > 20;
  // The nodes go up in a big blast.
  r.nodeHull = n.maxHp < 3000;
  for(const n of FS.ids('N1')) n.scanned = true;   // scanned first since v180
  FS.killId('N1');
  FS.step(5);
  r.bigBlast = BLAST_FUSE.length > 0 || DANGER.length > 0;
  r.ends = FS.until(()=>waveOver, 20000, true, true) >= 0;
  ITEMS.length = 0;
  FS.until(()=>wave===79, 6000, false, false);
  r.shipBack = player.ship !== 'fimara';
  return r;`);

scenario('v177: M79 the Setekh sends the data on the clock', 'm=79', `
  const r = {}; const cards = []; const oa = objAnnounce; objAnnounce = function(a,b){ cards.push(b); return oa.apply(this, arguments); };
  FS.step(200);
  r.timer = missionTimerLeft() > 0 && /UPLINK/.test(missionTimer.label);
  r.jams = !!jammerAlive();
  // Everything down well before the end: the clock still has to finish.
  FS.until(()=>missionTimerLeft() < 300, 20000, true, true);
  r.notOverEarly = !waveOver;
  FS.until(()=>waveOver, 4000, true, true);
  r.dataSent = cards.indexOf('DATA SENT') >= 0;
  r.ends = waveOver;
  return r;`);

scenario('v177: M80 the Hecate is patched up and jumps', 'm=80', `
  const r = {}; const cards = []; const oa = objAnnounce; objAnnounce = function(a,b){ cards.push(b); return oa.apply(this, arguments); };
  FS.step(50);
  const a = FS.ids('A1')[0];
  r.damaged = !!a && a.hp < a.maxHp*0.35;
  // Shivans all down early: the wave still waits for the transports.
  FS.until(()=>EV_DOCK['T1'], 20000, true, true);
  r.firstDock = !!EV_DOCK['T1'];
  r.healing = a.hp > a.maxHp*0.5;
  r.waitsForRepairs = !waveOver;
  FS.until(()=>waveOver, 20000, true, true);
  r.repaired = cards.indexOf('THE HECATE IS REPAIRED') >= 0;
  r.ends = waveOver;
  return r;`);

scenario('v177: delayed events and passing scenery', 'm=1', `
  const r = {};
  // d: an event fires that many seconds after its trigger.
  EV = [{t:'sek', a:0, w:'meldung', wa:'x', d:2, at:null, done:false}];
  FS.step(5);
  r.waits = EV[0].done === false && EV[0].at != null && evPending();
  FS.step(2*TICK_HZ);
  r.fires = EV[0].done === true;
  // A queued ship marked noHold does not keep the wave open.
  spawnQ.length = 0; spawnQ.push({time:spawnT+99999, type:'boss_sh', noHold:true});
  r.noHold = !queueHolds();
  spawnQ.push({time:spawnT+99999, type:'fi_sh'});
  r.holds = queueHolds();
  spawnQ.length = 0;
  return r;`);

scenario('v178: small craft fire at any part of a large hull', 'm=44', `
  const r = {};
  FS.step(50);
  // A stand-in cruiser, wide and flat like the real ones.
  const k = {type:'cruiser', img:'crcain', x:500, y:250, sc:1, ang:0};
  IMGS.crcain = IMGS.crcain || document.createElement('canvas');
  const w = IMGS.crcain.width, h = IMGS.crcain.height;
  // Nose at the stern end, not at the centre: on the hull.
  const f = {x:200, y:250 + h*0.25, head:0};
  r.offCentreHits = noseOnHull(f, k, 2000);
  // Off the centre by more than the old cone, still on the hull.
  const g = {x:500 - w*0.45 - 40, y:250 - h*0.3, head:0.0};
  const off = Math.abs(Math.atan2(250-g.y, 500-g.x));
  r.outsideOldCone = off > 0.0 && noseOnHull(g, k, 2000);
  // Pointing past it: no.
  r.missIsMiss = !noseOnHull({x:200, y:250 + h*2, head:0}, k, 2000);
  r.awayIsMiss = !noseOnHull({x:200, y:250, head:Math.PI}, k, 2000);
  r.outOfRange = !noseOnHull({x:200, y:250, head:0}, k, 50);
  r.notForFighters = !noseOnHull(f, {type:'fighter', img:'fiherc', x:500, y:250, sc:1}, 2000);
  return r;`);

scenario('v178: M77 a slow, large Sathanas with her guns on the Hatshepsut', 'm=77', `
  const r = {};
  FS.step(100);
  for(let t=0;t<20000 && !EV_SEEN['S1'];t+=20){ FS.step(20);
    if(t%200===0) for(const e of enemies){ if(e.warp>0||e.invuln||e.scenery) continue; e.hp = 0; } }
  FS.step(5);
  const s = FS.ids('S1')[0], a = FS.ids('A1')[0];
  r.large = Math.round(IMGS[s.img].width*s.sc) >= 520;
  r.slowArrival = s.warpMax >= 8*TICK_HZ;
  // A cruiser of ours alongside: she still goes for the Hatshepsut.
  FS.until(()=>!(s.warp>0), 2000, false, false);
  const k = {}; let onH = 0, onOther = 0;
  // Long enough for a full cycle: since v179 the first shot comes during the
  // jump, then the beams cool down.
  for(let i=0;i<2500 && !a.dead;i++){ FS.step(1); for(const b of s.beams) if(b.large && b.state==='firing' && !(b.tgt && b.tgt.dead)){ if(b.tgt===a) onH++; else onOther++; } }
  r.focus = onH > 0 && onOther === 0;
  // Nothing shoves her off her line.
  const y0 = s.y; FS.step(300); r.steady = Math.abs(s.y - y0) < 2;
  return r;`);

scenario('v178: M78 ghosts, wingmen, no support, no TAG, ends with the devices', 'm=78', `
  const r = {};
  FS.step(30);
  r.noTag = !player.sb.some(b=>b.key==='tagc') && player.ship==='fimara';
  r.noSupport = !allyReady();
  const w = allies.filter(a=>a.img==='fimara');
  FS.step(400);
  const w2 = allies.filter(a=>a.img==='fimara');
  r.twoWingmen = w2.length === 2 && w2.every(a=>a.disguised);
  // Wingmen hold fire and nobody shoots at them while the cover holds.
  let shots = 0; const pb = pBullets.push;
  pBullets.push = function(b){ if(b && b.ally && w2.some(a=>Math.hypot(a.x-b.x,a.y-b.y)<40)) shots++; return pb.apply(this, arguments); };
  const h0 = w2.map(a=>a.hp);
  FS.step(1500);
  pBullets.push = pb;
  r.wingmenQuiet = shots === 0;
  r.wingmenUnhurt = w2.every((a,i)=>a.hp >= h0[i]);
  // The Sathanas: shots pass, no subsystems.
  let s = null; for(let i=0;i<3000 && !s;i+=20){ FS.step(20); s = enemies.find(e=>e.img==='sdsathanas' && !(e.warp>0) && e.x < MW) || null; }
  r.ghost = !!s && s.ghost && !s.subs && !bulletOnHull(s, {x:s.x, y:s.y, w:4, h:4});
  // The devices go: the mission ends, waves or not.
  for(const n of FS.ids('N1')) n.scanned = true;   // scanned first since v180
  FS.killId('N1');
  r.ends = FS.until(()=>waveOver, 3000, false, false) >= 0;
  return r;`);

scenario('v178: M80 in the nebula, transports repairing', 'm=80', `
  const r = {};
  FS.step(30);
  r.nebula = waveMod==='nebula' && !portalOn;
  FS.until(()=>FS.ids('T1').some(t=>t.holdT!=null), 20000, true, false);
  r.repairing = SUB_MSGS.some(m=>m.txt==='REPAIRING');
  r.noBoarding = !SUB_MSGS.some(m=>m.txt==='BOARDING');
  return r;`);

scenario('v179: M77 the Sathanas out of the middle, firing on her way out, no script', 'm=77', `
  const r = {};
  FS.step(100);
  for(let t=0;t<20000 && !EV_SEEN['S1'];t+=20){ FS.step(20);
    if(t%200===0) for(const e of enemies){ if(e.warp>0||e.invuln||e.scenery) continue; e.hp = 0; } }
  FS.step(2);
  const s = FS.ids('S1')[0], a = FS.ids('A1')[0], p = FS.ids('P1')[0];
  r.middle = !!s && !!p && Math.abs(s.warpY - p.y) < 3;
  r.noScript = !SCRIPT_WAVES[77].ev.some(e=>e.w==='zerstoeren');
  r.longBeams = s.beams.filter(b=>b.large).every(b=>b.fireT >= 300);
  let firedInWarp = false;
  for(let i=0;i<1000 && s.warp>0;i++){ FS.step(1); if(s.beams.some(b=>b.large && b.state==='firing')) firedInWarp = true; }
  r.firesBeforeOut = firedInWarp;
  // She stays over the Hatshepsut until she is gone.
  const x0 = s.x; let held = true;
  for(let i=0;i<6000 && FS.ids('A1').length;i+=20){ FS.step(20); if(FS.ids('A1').length && Math.abs(s.x - x0) > 3) held = false;
    if(i%300===0) for(const e of enemies) if((e.type==='fighter'||e.type==='bomber') && !(e.warp>0)) e.hp = 0; }
  r.heldOver = held;
  r.beamsKilledHer = FS.ids('A1').length===0;
  FS.step(200);
  r.thenDrivesOn = s.x < x0 - 10;
  r.ends = FS.until(()=>waveOver, 12000, true, true) >= 0;
  return r;`);

scenario('v179: one rule for every control', '', `
  const r = {};
  r.off = btnState(false, true, true) === 'off';
  r.active = btnState(true, true, false) === 'on';
  r.hover = btnState(true, false, true) === 'ready';
  r.idle = btnState(true, false, false) === null;
  r.dimWhenOff = btnText('off') === TH('textDim');
  // The off plate is the same dark plate a locked tab gets.
  const calls = []; const _p = thPlate;
  thPlate = function(x,y,w,h,fill){ calls.push(fill); return _p.apply(this, arguments); };
  thButton(0,0,10,10,'off'); uiCell(0,0,10,10,{state:'off'});
  thPlate = _p;
  r.sameDarkPlate = calls.length===2 && calls[0]===calls[1];
  return r;`, true);

scenario('v179: strafing runs on a large hull, guns in a stream', 'm=73', `
  const r = {};
  FS.step(300);
  const ws = allies.filter(a=>a.small);
  r.haveCraft = ws.length > 0;
  let attack = 0, n = 0;
  for(let i=0;i<600;i++){ FS.step(1); for(const a of ws){ const t = smallTarget(a); if(bigTarget(t)){ n++; if(a.role==='attack') attack++; } } }
  r.alwaysRuns = n > 0 && attack === n;
  // Nose on the hull: it fires again well within its old beat.
  const k = {type:'cruiser', img:'crcain', x:500, y:250, sc:1, ang:0, side:'enemy'};
  const f = ws[0]; f.x = 300; f.y = 250; f.head = 0; f.fT = 0;
  smallFire(f, k);
  r.streamBeat = f.fT <= Math.round(f.fR*HULL_BURST) + 1;
  return r;`);

scenario('v180: lasting damage on a capital ship', 'm=62', `
  const r = {};
  FS.step(600);
  const k = enemies.find(e=>e.type==='cruiser' && !(e.warp>0));
  r.haveCruiser = !!k;
  const img = IMGS[k.img], hw = img.width*k.sc/2, hh = img.height*k.sc/2;
  // Hits on the left edge only.
  let ok = true;
  for(let i=0;i<200 && k.hp > k.maxHp*0.45;i++){
    damageEnemy(k, k.maxHp*0.01, k.x - hw*0.98, k.y + (Math.random()-0.5)*hh, true, 'bolt');
    try{ FS.step(1); draw(); }catch(ex){ ok = String(ex); }
  }
  r.draws = ok === true;
  const D = k.dm;
  r.scorch = !!D && D.scorch.length >= 5;
  // Moved in from the edge they struck.
  r.inward = !!D && D.scorch.every(s=>s.u > -0.95);
  r.onHull = !!D && D.scorch.every(s=>dmgSolid(D.inf, s.u, s.v, 0));
  for(let i=0;i<5;i++){ FS.step(1); draw(); }
  // tears since v182: at 45 % the first two (72 % and the next step)
  r.breach = !!D && D.gashes.length >= 1;
  r.breachClearOfSystems = !!D && D.gashes.every(h=>dmgSubsFar(k, h.u, h.v, 4));
  // A destroyed engines subsystem puts the flames out.
  const en = (k.subs||[]).find(s=>s.id==='engines');
  if(en){ en.hp = 0; en.dead = true; dmgCrater(k, en); }
  r.flamesOut = !en || dmgThrust(k, {dx:-0.9, dy:0}, 0) <= 0.45;
  r.crater = !en || D.craters.length === 1;
  // Patched up, the breach closes again.
  k.hp = k.maxHp*0.9; draw();
  r.repairCloses = D.gashes.length === 0;
  r.scorchStays = D.scorch.length >= 5;
  return r;`);

scenario('v181: M80 the Hecate is there from the start, already damaged', 'm=80', `
  const r = {};
  const pb = PARTS.length;
  FS.step(30);
  const h = FS.ids('A1')[0];
  r.there = !!h;
  // She cannot jump before she is repaired, so she does not jump in either.
  r.noWarpIn = !!h && !(h.warp>0);
  draw(); FS.step(1); draw();
  const D = h && h.dm;
  r.breached = !!D && D.gashes.length >= 1;
  r.scorched = !!D && D.scorch.length >= 5;
  // Old damage, not new: the breaches are open, nothing bursts.
  r.alreadyOpen = !!D && D.gashes.every(x=>fc - x.t0 >= DMG_GROW);
  return r;`);
scenario('v181: damage pictures at screen resolution, glow only on the hull', 'm=62', `
  const r = {};
  FS.step(600);
  const k = enemies.find(e=>e.type==='cruiser' && !(e.warp>0));
  const img = IMGS[k.img], hw = img.width*k.sc/2, hh = img.height*k.sc/2;
  for(let i=0;i<200 && k.hp > k.maxHp*0.3;i++){
    damageEnemy(k, k.maxHp*0.01, k.x - hw*0.9, k.y + (Math.random()-0.5)*hh, true, 'bolt');
    FS.step(1); draw();
  }
  for(let i=0;i<6;i++){ FS.step(1); draw(); }
  const D = k.dm;
  // As many pixels as the canvas has for her, not one per game unit.
  r.sharp = !!D && D.can && Math.abs(D.can.width - img.width*k.sc*dmgK(k)) <= 1;
  r.kIsRes = dmgK(k) === Math.max(1, Math.min(RES_X, 1/k.sc, DMG_K_MAX));
  // Nothing of the glow where the damaged picture is empty.
  if(D && D.fxL){
    const fx = D.fxL.getContext('2d').getImageData(0, 0, D.fxL.width, D.fxL.height).data;
    r.fxDrawn = fx.some((v,i)=>i%4===3 && v>0);
  }
  return r;`);
scenario('v182: tears, not holes; what comes out flies free in space', 'm=62', `
  const r = {};
  FS.step(600);
  const k = enemies.find(e=>e.type==='cruiser' && !(e.warp>0));
  k.noFlee = true; k.escape = false;             // she stays to be looked at
  const img = IMGS[k.img], hw = img.width*k.sc/2, hh = img.height*k.sc/2;
  for(let i=0;i<300 && k.hp > k.maxHp*0.3;i++){
    damageEnemy(k, k.maxHp*0.01, k.x - hw*0.9, k.y + (Math.random()-0.5)*hh, true, 'bolt');
    FS.step(1); draw();
  }
  for(let i=0;i<60;i++){ FS.step(1); draw(); }
  const D = k.dm;
  r.tears = !!D && D.gashes.length >= 2;
  // Small: never more than a tenth of her length, and capped.
  r.small = !!D && D.gashes.every(g=>g.L*hh*2 <= Math.min(hw*2*0.12, DMG_GASH_MAX) + 0.01);
  // Nothing to see through: the picture is solid where a tear is.
  r.noHoles = !!D && D.can && D.gashes.every(g=>{
    const x = Math.round((g.u*0.5+0.5)*D.can.width), y = Math.round((g.v*0.5+0.5)*D.can.height);
    return D.can.getContext('2d').getImageData(x, y, 1, 1).data[3] === 255; });
  // What leaves a tear keeps its speed: no drag, no gravity, nothing rising.
  const hp0 = k.hp; k.invuln = true;
  for(let i=0;i<600;i++){ FS.step(1); k.warpOut = 0; k.hp = hp0; }
  r.alive = enemies.indexOf(k) >= 0;
  const fr = PARTS.filter(p=>p.free);
  r.emitted = fr.length > 0;
  const p0 = fr.map(p=>({p, vx:p.vx, vy:p.vy}));
  tickParts();
  r.straight = p0.filter(q=>PARTS.indexOf(q.p)>=0).every(q=>q.p.vx===q.vx && q.p.vy===q.vy);
  // A moving ship hands her velocity on to what she sheds. Read as the
  // DIFFERENCE between a standing and a moving ship, over every part that
  // comes off. A part leaves along its gash's normal (dmgEmit: vx = svx +
  // (n.x + q.x*k)*speed) and that normal may point backwards, so the first
  // part's own vx is a lottery - asking for > 0.5 on it failed in about one
  // run of three, on v233 as well as v234. Over many parts the outward
  // term averages out and what is left is exactly what was handed on.
  // Both measurements get the SAME dice, so the same gashes fire with the
  // same spread in both and the difference is only the velocity handed on.
  // Averaging over different dice left 1.5 to 1.94 and still failed.
  const meanVx = (dx) => {
    const real = Math.random;
    let seed = 20604;
    Math.random = () => { seed = (seed*1103515245 + 12345) & 0x7fffffff; return (seed % 1000000)/1000000; };
    let sum = 0, cnt = 0;
    try{
      for(let i = 0; i < 300; i++){
        PARTS.length = 0;
        k.dm.lx = k.x - dx; k.dm.ly = k.y;
        dmgEmit(k);
        for(const q of PARTS) if(q.free){ sum += q.vx; cnt++; }
      }
    } finally { Math.random = real; PARTS.length = 0; }
    return {mean: cnt ? sum/cnt : 0, cnt: cnt};
  };
  const still = meanVx(0), moving = meanVx(1.5);
  r.enoughPartsToRead = still.cnt > 30 && moving.cnt > 30 && still.cnt === moving.cnt;
  r.handedOn = Math.round((moving.mean - still.mean)*1000)/1000;
  r.inherits = Math.abs((moving.mean - still.mean) - 1.5) < 0.02;
  return r;`);
scenario('v183: a capital ship dies the long way and breaks up', 'm=62', `
  const r = {};
  FS.step(600);
  const k = enemies.find(e=>e.type==='cruiser' && !(e.warp>0));
  k.noFlee = true;
  const img = IMGS[k.img], hw = img.width*k.sc/2;
  damageEnemy(k, k.maxHp*2, k.x - hw*0.5, k.y, true, 'bolt');
  r.rolling = k.rollT != null && enemies.indexOf(k) >= 0 && !k.dead;
  r.silent = !!k.noFire && !!k.noTarget;
  r.stillCounts = liveThreatCount() >= 1;
  const len = k.rollLen;
  r.lengthBySize = len === deathRollLen(k) && len >= 200;
  FS.step(len - 20);
  r.notYet = enemies.indexOf(k) >= 0;
  HULKS.length = 0;
  FS.step(40);
  r.gone = enemies.indexOf(k) < 0 && k.dead;
  r.sections = HULKS.length >= 2;
  // the sections keep her velocity and the push, nothing slows them
  const h0 = HULKS[0], vx0 = h0 && h0.vx;
  tickHulks();
  r.freeFlight = !h0 || HULKS.indexOf(h0) < 0 || h0.vx === vx0;
  return r;`);
scenario('v183: islands come apart; wreckage keeps breaking up', 'm=62', `
  const r = {};
  // two blocks of metal with empty space between them, cut as one piece
  const c = document.createElement('canvas'); c.width = 100; c.height = 40;
  const g = c.getContext('2d'); g.fillStyle = '#888'; g.fillRect(0, 0, 40, 40); g.fillRect(60, 0, 40, 40);
  const P = hulkPieces(c, 100, 40, 1, [{x:-2,y:-2},{x:102,y:-2},{x:102,y:42},{x:-2,y:42}], []);
  r.twoIslands = P.length === 2;
  // wreckage with its fuse burnt down comes apart or goes in its blast
  debris.length = 0;
  const pc = hulkPieces(c, 100, 40, 1, [{x:-2,y:-2},{x:42,y:-2},{x:42,y:42},{x:-2,y:42}], [])[0];
  wreckFrom(pc, 300, 250, 0, false, 0.1, 0, 0, 1);
  r.wreck = debris.length === 1 && !!debris[0].fuse && !!debris[0].inert;
  debris[0].fuse = fc;
  const pb = PARTS.length;
  updateDebris();
  r.split = debris.length === 2 && debris.every(d=>d.fuse > fc);
  // and it ends: every piece in a last blast, nothing just fades
  for(let i=0;i<4000 && debris.length;i++){ fc++; updateDebris(); }
  r.endsInBlasts = debris.length === 0;
  return r;`);
scenario('v183: our capital ships die the same way', 'm=80', `
  const r = {};
  FS.step(30);
  const a = FS.ids('A1')[0];
  a.keepAlive = false; a.hp = 0;
  FS.step(2);
  r.rolling = a.rollT != null && allies.indexOf(a) >= 0;
  FS.step(deathRollLen(a) + 10);
  r.gone = allies.indexOf(a) < 0;
  r.sections = HULKS.length >= 2;
  return r;`);
scenario('v183: M55 a cruiser dying on her way to the portal drifts, does not escape', 'm=55', `
  const r = {};
  FS.until(()=>{ const k = FS.ids('K1')[0]; return !!k && k.escaping && !(k.warp>0) && k.x > 120*FIELD_K; }, 4000, true);
  const k = FS.ids('K1')[0];
  const x0 = k.x; FS.step(20); const v0 = (k.x - x0)/20;
  const esc0 = escGone;
  damageEnemy(k, k.maxHp*3, k.x, k.y, true, 'bolt');
  r.rolling = k.rollT != null;
  // she keeps the speed she had, she does not speed up
  FS.step(5); const x1 = k.x; FS.step(50); const v1 = (k.x - x1)/50;
  r.sameSpeed = v0 > 0.05 && Math.abs(v1 - v0) < v0*0.15;
  // put her right at the portal: dying, she still does not get through
  k.x = PORTAL_X*FIELD_K + 5; FS.step(k.rollT + 10);
  r.notEscaped = escGone === esc0 && !EV_LEFT['K1'] && k.dead;
  // the breakup is her big blast now: nothing of her left in the queue
  r.noLateBlasts = !EXPL_Q.some(q => q.t > fc && Math.hypot(q.x - k.x, q.y - k.y) < 150);
  return r;`);
scenario('v180: M78 the devices are scanned first, the Sathanas never fire', 'm=78', `
  const r = {};
  FS.step(30);
  r.scanObjective = missionObj === 'SCAN THE UNKNOWN DEVICES';
  const ns = FS.ids('N1');
  r.threeToScan = ns.length === 3 && ns.every(n=>n.scan && n.scanLock);
  // Shot before the scan: it does not go.
  const n = ns[0]; damageEnemy(n, n.maxHp*3, n.x, n.y, true, 'bolt'); FS.step(5);
  r.notBeforeScan = !n.dead && enemies.includes(n);
  // Cover blown, the Sathanas still never fire a beam.
  let beams = 0;
  for(let i=0;i<4000;i+=10){ FS.step(10);
    for(const e of enemies) if(e.img==='sdsathanas' && e.beams && e.beams.some(b=>b.state!=='idle')) beams++; }
  r.sathanasSilent = beams === 0;
  for(const x of FS.ids('N1')) x.scanned = true;
  FS.step(30);
  r.destroyObjective = missionObj === 'DESTROY THE UNKNOWN DEVICES';
  FS.killId('N1');
  r.ends = FS.until(()=>waveOver, 3000, false, false) >= 0;
  return r;`);

scenario('v185: small craft carry their table values, player and AI alike', 'm=61', `
  const r = {};
  const f = mkEnemy('fi_shivan', 'fiscorpion', 250);
  r.scorpionHull = f.maxHp === Math.round(62*cycleMult()) && f.maxSh === 154;
  r.shieldLikePlayer = f.shRe === player.shRecharge;
  const b = mkEnemy('bo_shivan', 'boseraphim', 250);
  r.seraphim = b.maxHp === Math.round(172*cycleMult()) && b.maxSh === 410;
  const a = mkAllySmall('fighter', 'terran', 'fimyrmidon', 250);
  applyShip('fimyrmidon');
  r.allyMyrmidonAsPlayer = a.maxHp === player.maxHp && a.maxSh === player.maxSh;
  r.thoth = shipStats('fitoth').hp === 69 && shipStats('fitoth').sh === 51;
  r.playerMara = shipStats('fimara').hp === 164 && shipStats('fimara').sh === 179;
  return r;`);
scenario('v185: wreckage is not pushed at the end, scenery catches no shots, middle button', 'm=55', `
  const r = {};
  FS.step(30);
  debris.length = 0;
  // inert: free wreckage keeps its speed, so any change is the push
  debris.push({x:400, y:250, vx:0, vy:0, r:6, life:1e9, ml:1e9, ang:0, va:0, rotS:0, inert:true});
  waveOver = true; waveCd = TRANS_CLEAR + TRANS_OUT;
  FS.step(40);
  r.notPushed = debris.length === 0 || Math.abs(debris[0].vx) < 0.01;
  const p = enemies.find(e => e.img === 'inknossos45deg');
  r.portalPassesShots = !!p && !bulletOnHull(p, {x:p.x, y:p.y, vx:3, vy:0, w:8});
  r.marksOffAtStart = subMarksOn === false;
  CVS.dispatchEvent(new MouseEvent('mousedown', {button:1, clientX:10, clientY:200, cancelable:true}));
  r.middleTurnsOn = subMarksOn === true;
  CVS.dispatchEvent(new MouseEvent('mousedown', {button:1, clientX:10, clientY:200, cancelable:true}));
  r.andOffAgain = subMarksOn === false;
  setSettings(true); settingsPage = SETTINGS_CONTROLS; draw();
  r.controlsTabDrawn = settingsRows().length === 0 && CONTROLS.length >= 13;
  setSettings(false);
  return r;`);

scenario('v186: FS2 factors land where they belong', 'm=33', `
  const r = {};
  FS.step(30);
  const tgt = enemies.find(e=>e.type==='cruiser' && !(e.warp>0)) || null;
  const mkF = (k)=>{ const w = priDefP(k); return {w:w, b:{x:0,y:0,vx:1,vy:0,w:14,h:3,dmg:volleyTotal(2)*w.dmg,f:w.f,wpn:k}}; };
  // A fighter with its shield up, held still.
  const f = mkEnemy('fi_ntf', 'fimyrmidon', 250); f.warp=0; f.noFire=true; enemies.push(f);
  const sh0 = f.sh, hp0 = f.hp;
  DMG_F = {a:0, s:1.25, u:0}; damageEnemy(f, 20, f.x, f.y, true, 'bolt'); DMG_F = null;
  r.circeTakesShield = f.sh < sh0 && f.hp === hp0;
  f.sh = 0; DMG_F = {a:0, s:1.25, u:0}; damageEnemy(f, 20, f.x, f.y, true, 'bolt'); DMG_F = null;
  r.circeNothingOnHull = f.hp === hp0;
  DMG_F = {a:1, s:1, u:1}; damageEnemy(f, 20, f.x, f.y, true, 'bolt'); DMG_F = null;
  r.promRasBefore = Math.abs(f.hp - (hp0-20)) < 1e-9;
  f.sh = 30; const h1 = f.hp;
  DMG_F = {a:1, s:0, u:2}; damageEnemy(f, 50, f.x, f.y, true, 'sec'); DMG_F = null;
  r.stilettoStoppedByShield = f.hp === h1 && f.sh === 30;
  // Energy: the store is drawn and comes back. Out of the jump first.
  for(let i=0;i<3000 && inJump();i++) FS.step(1);
  player.en = player.enMax; player.pMode = 2; for(const b of player.pb) b.t = 0;
  isFiring = true; FS.step(60); isFiring = false;
  r.linkedDrains = player.en < player.enMax - 0.5;
  const e0 = player.en; FS.step(120);
  r.recharges = player.en > e0;
  // Wheel and Q / E.
  player.pMode = 0;
  CVS.dispatchEvent(new WheelEvent('wheel', {deltaY:-100, cancelable:true}));
  r.wheelUpSteps = player.pMode === 1;
  // v207: FS2's slash steps the secondary bank (E no longer)
  document.dispatchEvent(new KeyboardEvent('keydown', {code:'Slash'}));
  r.slashStepsSec = player.sSel === 1;
  return r;`);

scenario('HoL start unchanged', 'm=1', `
  return {wave: wave, thoth: player.ship==='fitoth', vasudanCall: ALLY_FAC_ON.vasudan===true && ALLY_FAC_ON.terran===false};`);

scenario('v188: capital hulls in FS2 ratio, subsystems from the models', 'm=31', `
  const r = {};
  const mk = (t, spr) => { const e = mkEnemy(t, spr, 250); return e; };
  const fen = mk('cr_ntf', 'ntfcrfenris'), lil = mk('cr_sh', 'crlilith'), aeo = mk('cr_ntf', 'ntfcraeolus');
  // ships.tbl ratio, but never under three quarters of the class (v189)
  r.fenrisFloor = Math.abs(fen.maxHp/lil.maxHp - 0.75/(75000/37000)) < 0.01 && capHullF('crfenris') === 0.75;
  r.lilithFull = Math.abs(capHullF('crlilith') - 75000/37000) < 1e-9;
  // an invulnerable boss is scenery: no boss music for her (v189)
  const fakeBoss = {type:'boss', invuln:true, dead:false, faction:'shivan'};
  enemies.push(fakeBoss); r.sceneryBossNoMusic = musicWant() === 'fight';
  fakeBoss.invuln = false; r.realBossMusic = musicWant() === 'boss';
  enemies.splice(enemies.indexOf(fakeBoss), 1);
  r.ntfSameAsTerran = capHullF('ntfcrfenris') === capHullF('crfenris') && capHullF('deorionleft') === capHullF('deorionright');
  r.othersUntouched = capHullF('casetekh')===1 && capHullF('coiceni')===1 && capHullF('sdcolossus')===1 && capHullF('sgmjolnir')===1;
  // the escort has the hull the support menu shows
  const a = mkAlly('ter_fenris');
  r.menuShowsRealHull = !!a && a.maxHp === allyHull(ALLY_DEFS.ter_fenris) && a.maxHp < capHull(HULL.cruiser);
  // subsystems: where two circles overlap, the nearer centre takes the hit
  const e = aeo; e.x = 400; e.y = 250; e.warp = 0; initSubsystems(e);
  const s0 = e.subs[0], s1 = e.subs[1];
  // v208: at real size two systems lie far apart; set two overlapping
  // circles 30 units apart for the rule itself
  const _sp = subPos; subPos = function(o, q){ return q===s0 ? {x:400, y:250} : (q===s1 ? {x:430, y:250} : _sp(o, q)); };
  const big = s0.r; s0.r = s1.r = 1;   // the largest circle subRadius allows
  r.nearestTakesHit = subAt(e, 409, 250) === s0;
  subPos = _sp; s0.r = big; s1.r = big;
  // the Aten's weapons sit forward, by the bow, as in the model
  r.atenWeaponsForward = (MOUNTS.craten.subs.find(s=>s.id==='weapons').dx > 0.5);
  return r;`);

scenario('v190: a bomb goes off over an area, a missile does not', 'm=31', `
  const r = {};
  FS.until(()=>!inJump(), 2000, true);           // not while jumping in
  const cyc = secDefP('cyclops'), bl = cyc.blast;
  r.fs2Radii = bl && bl.i === 40 && bl.o === 80;                 // 100 / 200 m
  r.onlyBombs = ARSENAL_S.filter(w=>w.blast).map(w=>w.key).join() === 'cyclops';
  r.empHalved = EMP_R === 60;                                    // 150 m (Silvio)
  const cr = mkEnemy('cr_ntf', 'ntfcrfenris', 250); cr.x = 500; cr.y = 250; cr.warp = 0;
  // One NAMED hull for all three, not a rolled one. mkEnemy('fi_ntf', null)
  // rolls one of six, and since v208 drew them at their real size two of
  // those six (Myrmidon, Ulysses) have their hitbox end exactly on the outer
  // radius of 80 at this distance: k came out 0, mid took no damage and this
  // scenario failed in roughly one run of three. Measured identical on v233
  // and v234, so the world's size has nothing to do with it. A Hercules
  // reaches to 73 and takes her share.
  const mkF = (dx)=>{ const f = mkEnemy('fi_ntf', 'fiherc', 250); f.x = 500+dx; f.y = 250; f.warp = 0; f.dead = false;
                      f.hp = f.maxHp = 1000; f.sh = f.maxSh = 0; return f; };
  const near = mkF(-20), mid = mkF(-110), far = mkF(-260);
  for(const e of [cr, near, mid, far]) if(enemies.indexOf(e) < 0) enemies.push(e);
  const crHp = cr.hp;
  const b = {x:500, y:250, dmg:cyc.dmg, f:cyc.f};
  player.x = 100; player.y = 250; const p0 = player.hp + player.sh;
  warheadBlast(b, bl, cr);
  r.struckNotTwice = cr.hp === crHp;
  r.nearFull = near.maxHp - near.hp >= cyc.dmg*0.99;
  r.midLess = mid.hp > near.hp && mid.hp < mid.maxHp;
  r.farUntouched = far.hp === far.maxHp;
  r.playerFarSafe = player.hp + player.sh === p0;
  // flown in too close: our own blast hurts us
  player.x = 500 - 20; player.y = 250; player.sh = player.maxSh; player.hp = player.maxHp;
  const q0 = player.hp + player.sh;
  warheadBlast(b, bl, cr);
  r.ownBlastHurts = player.hp + player.sh < q0;
  // an allied bomber's blast spares us
  player.sh = player.maxSh; player.hp = player.maxHp;
  warheadBlast(Object.assign({ally:true}, b), bl, cr);
  r.allyBlastSpares = player.hp === player.maxHp && player.sh === player.maxSh;
  r.wiredIn = String(updateSecBullets).indexOf('warheadBlast(b, sw.blast, e)') >= 0;
  for(const e of [cr, near, mid, far]){ const i = enemies.indexOf(e); if(i >= 0) enemies.splice(i, 1); }
  return r;`);

scenario('v191: a new mission starts repaired and armed, a rearm is no recharge', 'm=33', `
  const r = {};
  FS.until(()=>!inJump(), 2000, true);
  // a rearm fills the racks and leaves the weapon store as it was
  player.en = 5; for(const b of player.sb) b.ammo = 0;
  rearmFull();
  r.rearmKeepsEnergy = Math.abs(player.en - 5) < 1e-9;
  r.rearmFillsRacks = player.sb.every(b=>b.ammo === b.max);
  // the next mission: hull, every rack and the store are full again
  player.hp = 3; player.en = 1; for(const b of player.sb) b.ammo = 0;
  nextWave();
  r.fullHull = player.hp === player.maxHp;
  r.fullRacks = player.sb.length > 0 && player.sb.every(b=>b.ammo === b.max);
  r.fullStore = Math.abs(player.en - player.enMax) < 1e-9;
  return r;`);

scenario('v192: test switch, GTVA labels, the cards', 'm=26&ship=bosekhmet', `
  const r = {};
  r.startsInSekhmet = player.ship === 'bosekhmet';
  r.gvInFs2 = allyLabel(ALLY_DEFS.vas_typhon) === 'GVD Typhon' && allyLabel(ALLY_DEFS.vas_sobek) === 'GVCv Sobek';
  const era = currentEra; currentEra = 'fs1';
  r.pvInFs1 = allyLabel(ALLY_DEFS.vas_typhon) === 'PVD Typhon';
  currentEra = era;
  r.hercShort = document.documentElement.innerHTML.indexOf("name:'GTF Herc Mk II'") >= 0 && document.documentElement.innerHTML.indexOf("name:'GTF Hercules Mk II'") < 0;
  const hc = hangarCard('bosekhmet'), ac = allyCard('vas_hatshepsut', 'T');
  r.hangarCardFacts = hc.facts.length >= 3 && hc.bars.length === 4 && hc.sub === 'YOU FLY THIS ONE';
  r.allyCardFacts = ac.facts.some(f=>/HEAVY BEAM/.test(f)) && ac.lines.some(l=>/switch ship/.test(l));
  return r;`);

scenario('v194: DONE in hangar and support, model trim', 'm=26', `
  const r = {};
  const hit = function(list){ const d = (list||[]).find(q=>q.close); if(!d) return false;
    pointerConsumed({x:d.x+d.w/2, y:d.y+d.h/2}); return true; };
  if(typeof clearResumeHold === 'function') clearResumeHold();
  const ship0 = player.ship;
  setShipMenu(true); drawShipMenu();
  r.hangarDone = hit(window._shipRects) && shipMenu === false && player.ship === ship0;
  clearResumeHold();
  setCallMenu(true); drawCallMenu();
  const called = STATS.escortsCalled;
  r.supportDone = hit(window._callRects) && callMenu === false && STATS.escortsCalled === called;
  clearResumeHold();
  // keys in the support window (v194)
  const key = function(code){ document.dispatchEvent(new KeyboardEvent('keydown', {code:code})); };
  score = 1e6;                // v202: support is paid in points
  const reset = function(){ allies.length = 0; setCallMenu(false); setShipMenu(false); clearResumeHold(); userPaused = false; syncPause(); };
  reset(); setCallMenu(true); let c0 = STATS.escortsCalled; key('KeyR');
  r.rCallsNotRearm = STATS.escortsCalled === c0+1 && !rearmMenu;
  reset(); setCallMenu(true); c0 = STATS.escortsCalled; key('KeyG');
  r.gCallsColossus = STATS.escortsCalled === c0+1 && allies.some(a=>a.colossus);
  reset(); setCallMenu(true); c0 = STATS.escortsCalled; key('KeyC');
  r.cCloses = !callMenu && STATS.escortsCalled === c0;
  // v207: ESC is the browser's - the game does nothing with it
  reset(); setCallMenu(true); key('Escape'); clearResumeHold();
  r.escLeftToTheBrowser = callMenu && !userPaused;
  reset();
  // only the last M3D_KEEP hulls stay on the graphics card
  const keep = M3D.models; M3D.models = {};
  for(let i=0;i<7;i++) M3D.models['h'+i] = {lo:{state:'ready', parts:[], tex:{}}, hi:null, seen:i};
  M3D.models.h1.lo.state = 'loading';
  m3dTrim('h0');
  const left = Object.keys(M3D.models).sort().join();
  r.trimmed = left === 'h0,h1,h5,h6' ? true : left;
  M3D.models = keep;
  return r;`);

scenario('v194: a wiped hull picture is built again at once', 'm=62', `
  const r = {};
  FS.step(600);
  const k = enemies.find(e=>e.type==='cruiser' && !(e.warp>0));
  r.haveCruiser = !!k;
  if(!k) return r;
  for(let i=0;i<60 && k.hp > k.maxHp*0.6;i++){ damageEnemy(k, k.maxHp*0.01, k.x, k.y, true, 'bolt'); FS.step(1); draw(); }
  for(let i=0;i<40;i++){ FS.step(1); draw(); }
  const D = k.dm;
  r.damaged = !!D && !!D.can;
  if(!D) return r;
  const b0 = D.built;
  for(let i=0;i<5;i++){ FS.step(1); draw(); }
  r.quietWhenNothingChanged = D.built === b0 ? true : [b0, D.built, D.dirty];
  cacheLost(); FS.step(1); draw();
  r.rebuiltAfterWipe = (D.built === fc && D.gen === CACHE_GEN) ? true : [D.built, fc, D.gen, CACHE_GEN];
  return r;`);

scenario('v195: support card without the hull bar', 'm=26', `
  const r = {};
  const c = allyCard('colossus', 'G'), t = allyCard('vas_typhon', 'R');
  r.noBar = c.bars.length === 0 && t.bars.length === 0;
  r.hullStillInFacts = (c.facts.some(f=>f.indexOf('HULL ')===0) && t.facts.some(f=>f.indexOf('HULL ')===0)) ? true : c.facts.concat(t.facts);
  setCallMenu(true); drawCallMenu(); setCallMenu(false); clearResumeHold();
  r.draws = true;
  return r;`);

scenario('v196: 3D capitals - keys, sprite fallback, damage marks alone', 'm=62', `
  const r = {};
  r.keys = f3dKey({img:'deorionleft'}) === 'deorionright' && f3dKey({img:'ntfdeorion'}) === 'ntfdeorion' && f3dKey({img:'crcain'}) === 'crcain' && f3dKey({img:'sdsathanas'}) === 'sdsathanas';
  // no model files here (file://): every ship stays a sprite, nothing breaks
  const done = f3dFieldPass(enemies.concat(allies));
  r.fallback = done.size === 0;
  try{ draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }
  // a damaged cruiser drawn the 3D way keeps only her marks
  FS.step(600);
  const k = enemies.find(e=>e.type==='cruiser' && !(e.warp>0));
  r.haveCruiser = !!k;
  if(!k) return r;
  k.hp = k.maxHp*0.4; dmgPreset(k);
  const D = dmgState(k);
  k._gl3 = true; dmgBuild(k, D); k._gl3 = false;
  r.marksOnly = D.gl3 === true;
  const g = D.can.getContext('2d'), px = g.getImageData(0, 0, D.can.width, D.can.height).data;
  let solid = 0; for(let i = 3; i < px.length; i += 4) if(px[i] > 200) solid++;
  // the sprite would cover most of the canvas; the marks alone very little
  r.fewPixels = solid < px.length/4*0.35 ? true : solid/(px.length/4);
  dmgBuild(k, D);
  r.spriteAgain = D.gl3 === false;
  return r;`);

scenario('v198: turrets from the models, their half of space, beams in the jump', 'm=62', `
  const r = {};
  // the stand-in sprites are plain boxes; the lists still move
  const m = mountsFor('sdsathanas');
  r.moved = !!(m && m.beams && m.beams[0].n3 && m.primary.every(p=>p.n3));
  // v199: her guns are the model's, her reactors stay on the old mounts
  r.lucReactorsStay = !!mountsFor('sdlucifer').raw && !mountsFor('sdlucifer').raw.primary.some(p=>p.n3) && !!mountsFor('sdlucifer').beams[0].n3;
  r.otherHullsAlone = !mountsFor('fimyrmidon').primary.some(p=>p.n3);
  // a turret on the back reaches up but not down through the hull
  const e = {img:'crcain', flip:false, ang:0, x:400, y:300};
  const b = {n3:[0, 1, 0]};
  r.upOk = mountCanAim(e, b, 400, 280, 400, 100) === true;
  r.downNo = mountCanAim(e, b, 400, 280, 400, 500) === false;
  r.flankAll = mountCanAim(e, {n3:[1, 0.1, 0]}, 400, 300, 400, 500) === true;
  // not drawn in 3D (no model files here): nothing hides
  r.noHideAsSprite = mountHid({img:'crcain', flip:false}, {n3:[1, 0, 0], mx:0.3}) === false;
  r.anim = !!F3D_GANIM.ravanapulse && typeof warpBeamOrbs === 'function';
  // a beam turret on the belly does not take a target above the ship
  const k = {img:'crcain', flip:false, ang:0, x:400, y:300, sc:1, side:'enemy', faction:'shivan'};
  const bb = {dx:0, dy:0.3, n3:[0, -1, 0]};
  const mp = mountPos(k, bb);
  r.bellyNoUp = beamCanAim(k, bb, mp, {x:mp.x, y:mp.y-300}) === false && beamCanAim(k, bb, mp, {x:mp.x, y:mp.y+300}) === true;
  try{ draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }
  return r;`);

scenario('v199: every turret of the model with its FS weapon; a dying ward is lost', 'm=69', `
  const r = {};
  const m = mountsFor('sdsathanas');
  r.sathAll = m.beams.length === 13 && m.primary.length === 22 && m.flak.length === 13 && m.secondary.length === 5;
  r.gunProfile = m.primary.every(p=>p.g && p.g.dmg > 0 && p.g.rate > 0);
  r.bfred = m.beams.filter(b=>b.wpn==='BFred').length === 4 && m.beams.some(b=>!b.large);
  // v202: the FS2 Fenris (@GTC Fenris): one LTerSlash, two AAAf
  r.fenrisBeams = (mountsFor('crfenris').beams||[]).length === 3;
  const e = {img:'sdsathanas', type:'boss', faction:'shivan'};
  r.capGun = capGun(e, 0) === m.primary[0].g;
  r.flakHas = flakHas({img:'sdsathanas', type:'boss'}) === true && flakHas({img:'deorionright', type:'destroyer'}) === false;
  // M69: the Hecate in her death roll counts as lost at once
  let h = null; for(let i=0;i<2000 && !h;i+=20){ FS.step(20); h = allies.find(a=>a.guard && !(a.warp>0)) || null; }
  r.haveWard = !!h;
  if(h){
    const before = protLost;
    h.hp = 0; FS.step(2);
    r.rollStarted = h.rollT != null;
    r.lostAtOnce = protLost === before + 1;
    evFire({w:'raus', a:h.uid});
    r.noJumpWhileDying = !(h.warpOut > 0);
  }
  try{ draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }
  return r;`);

scenario('v200: models loaded up front, uploads queued between frames', 'm=77', `
  const r = {};
  r.haveQueue = typeof f3dUpload === 'function' && typeof f3dPreload === 'function' && !!F3D_PRE;
  // the queue runs every job, a few at a time
  let n = 0; for(let i=0;i<5;i++) f3dUpload(function(){ n++; });
  await new Promise(function(res){ setTimeout(res, 120); });
  r.queueRuns = n === 5 && F3D_UPQ.length === 0;
  // no model files here: the preload ends without hanging, the game runs
  f3dPreload();
  for(let i=0;i<40 && F3D_PRE.on && !F3D_PRE.done;i++) await new Promise(function(res){ setTimeout(res, 300); });
  r.preloadEnds = !F3D_PRE.on || F3D_PRE.done;
  try{ GS='title'; draw(); GS='playing'; draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }
  return r;`);

scenario('v201: NTF in 3D, turrets turn, shots over the ships, hit beyond the sprite', 'm=62', `
  const r = {};
  r.ntfKeys = ['ntfcraeolus','ntfcodeimos','ntfcrfenris','ntfcrleviathan','ntfdeorion','ntfdehecate'].every(k => f3dKey({img:k}) === k);
  const m = mountsFor('ntfdeorion');
  r.ntfTurrets = !!(m && m.raw && m.beams.length === 9 && m.beams.every(b => b.ti != null));
  // a gun's last target is kept for the turret to turn to
  const e = {img:'deorionright'}; f3dAim(e, 3, 100, 200);
  r.aimKept = !!(e._aimT && e._aimT[3] && e._aimT[3].x === 100);
  const f = f3dRestFw([0, 1, 0]);
  r.restBow = Math.abs(f[2] - 1) < 1e-6;
  // a map taller than the sprite: a point above the sprite's box is hull
  let k = null; for(let i=0;i<3000 && !k;i+=20){ FS.step(20); k = enemies.concat(allies).find(x => !x.small && x.type!=='asteroid' && IMGS[x.img] && !(x.warp>0)) || null; }
  r.haveShip = !!k;
  if(k){
    const img = IMGS[k.img];
    MASKS3D[k.img] = {w:4, h:8, bits:new Uint8Array(32).fill(1), ky:2};
    const y = k.y - img.height*k.sc*0.8;          // above the sprite's box
    r.hitAbove = onHull(k.img, k.x, k.y, k.sc, k.flip, k.x, y, 0) === true;
    delete MASKS3D[k.img];
    r.notWithoutMap = onHull(k.img, k.x, k.y, k.sc, k.flip, k.x, y, 0) === false;
  }
  // shots: drawn after the ships; one from a far flank under its ship
  r.shots = typeof drawShots === 'function' && shotUnder({hidE:null}) === false;
  r.noBoxWithoutLoader = (f3dLoadBoxShow(), !document.querySelector('div[style*="z-index:50"]'));
  try{ draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }
  return r;`);

scenario('v202: Fenris beams, points, calls, docked jumps, wingmen, AI fire', 'm=1', `
  const r = {};
  // Fenris: her FS2 table (@GTC Fenris) - one LTerSlash, two AAAf
  const fm = mountsFor('crfenris');
  r.fenrisBeams = !!(fm && fm.beams && fm.beams.length === 3 && fm.beams.filter(b => b.large).length === 1);
  r.newKeys = ['sdhades','frtriton','trargo','inarcadia','gmrahu'].every(k => f3dKey({img:k}) === k) &&
              f3dKey({img:'inknossosfront'}) === 'inknossos';
  r.batches = typeof f3dFieldPrep === 'function' && typeof f3dFlush === 'function';
  // M1: three Thoth fly with the player
  FS.step(400);
  const th = allies.filter(a => a.small && a.img === 'fitoth');
  r.m1Wingmen = th.length === 3;
  // points: hull the player takes off, shield paid when she dies
  const e = enemies.find(o => o.type === 'fighter' && !(o.warp > 0));
  r.haveFighter = !!e;
  if(e){
    e.sh = 10; e.maxSh = 10; e.hp = 40; e.maxHp = 40;
    const s0 = score;
    damageEnemy(e, 5, e.x, e.y, true, 'bolt');          // shield only
    r.shieldNotYet = score === s0 && (e.shPts||0) >= 5;
    damageEnemy(e, 20, e.x, e.y, true, 'bolt');         // 5 shield, 15 hull
    r.hullPaidAtOnce = score - s0 >= 14 && score - s0 <= 16;
    const s1 = score;
    damageEnemy(e, 30, e.x, e.y, false, 'bolt');        // an ally finishes her
    killEnemy(e, enemies.indexOf(e), false, false);
    r.shieldOnKill = score - s1 === 10;
  }
  // a call costs her hull in points; what is left comes back
  const id = 'vas_aten', cost = allyCost(id);
  score = 0; r.cannotAfford = !allyAffordable(id);
  score = cost + 500;
  for(const a of allies.slice()) if(!a.small){ allies.splice(allies.indexOf(a), 1); }
  allyCd = 0;
  const ok = callAlly(id);
  r.called = ok && score === 500;
  const al = allies.find(a => a.callCost === cost);
  if(al){ al.hp = 300; allyRefunds(); }
  r.refund = !!al && score === 800;
  // a ship taken is nobody's target (M38)
  r.capturedSpared = escortSpares({captured:true});
  // docked: one vortex, sized for the pair
  const big = {img:'trargo', sc:0.5, x:400, y:300, warpOut:100, warpMax:160, side:'ally'};
  const box = {img:'fcttc1', sc:0.5, x:400, y:340, warpOut:90, warpMax:160, carrier:big, side:'ally'};
  allies.push(big, box);
  tickDockWarp();
  const g = fsWarp(box);
  r.dockOneVortex = box._wLead === big && !!g && g.mem === true && box.warpOut === big.warpOut;
  allies.splice(allies.indexOf(big), 1); allies.splice(allies.indexOf(box), 1);
  // AI fire: every gun, paid from a store
  const f = enemies.find(o => o.type === 'fighter') || allies.find(a => a.small);
  if(f){
    const lo = aiLoadout(f), pts = entMounts(f, 'primary');
    if(lo && pts && pts.length){
      f.enMax = null; f.mT = null;
      const nb = eBullets.length + pBullets.length;
      aiGunVolley(f, player, lo, pts, 0, null, 1);
      r.allGuns = eBullets.length + pBullets.length - nb >= pts.length;
      r.paysEnergy = f.en < f.enMax;
    } else { r.allGuns = true; r.paysEnergy = true; }
  }
  // one hit per bolt in the log
  if(PL){ const b = {}; const h0 = PL.hits; plogHit(b); plogHit(b); r.oneHitPerBolt = PL.hits === h0 + 1; }
  try{ draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }
  return r;`);

scenario('v203: small craft in 3D, armed freighters, scans under fire, FS2 AI arms', 'm=1', `
  const r = {};
  // small craft and the player's hulls are 3D keys, loaded at 512
  r.smallKeys = ['fiaeshma','bonephilim','sgcerberus','sucentaur','ephermes','fctac1','fitoth','fimyrmidon'].every(k => f3dKey({img:k}) === k && f3dSmall(k));
  r.capsStay = !f3dSmall('crfenris') && !f3dSmall('sgmjolnir');
  // the turn: a mirrored picture becomes a half roll, gone after ~0.3 s
  const e = {img:'fimyrmidon', ang:0, flip:false, sc:0.3};
  f3dTurnRoll(e);
  e.flip = true; e.ang = Math.PI - 0.2;
  e._f3r.t -= 0.016;
  const r0 = f3dTurnRoll(e);
  r.rollStarts = Math.abs(Math.abs(r0) - Math.PI) < 0.4;
  for(let i = 0; i < 30; i++){ e._f3r.t -= 0.016; f3dTurnRoll(e); }
  r.rollEnds = Math.abs(e._f3r.r) < 1e-6 && Math.abs(e._f3r.b) < 0.1;
  // the hangar keeps its levels for small hulls
  r.hangarLevels = typeof m3dDraw === 'function';
  // armed freighters: a Rahu has guns and is no player-only target
  const rh = {type:'freighter', img:'gmrahu', x:500, y:250, hp:1000, maxHp:1000, faction:'shivan', side:'enemy', warp:0};
  r.rahuArmed = freighterArmed(rh) === true && playerOnly(rh) === false;
  const tc = {type:'freighter', img:'frchronos', x:500, y:250, hp:1000, maxHp:1000, faction:'ntf', side:'enemy', warp:0};
  r.freighterWpn = !!WPN.freighter;
  // scanning: a hit does not set it back, only leaving the range
  const sc = {type:'freighter', img:'frposeidon', x:player.x + 40, y:player.y, hp:1000, maxHp:1000, scan:true, scanT:0, faction:'ntf', side:'enemy', warp:0};
  enemies.push(sc);
  for(let i = 0; i < 20; i++){ tickScan(); if(i === 10){ player.hitT = 30; if(typeof hullFlash !== 'undefined') hullFlash = 7; } }
  r.scanUnderFire = sc.scanT === 20;
  sc.x = player.x + SCAN_R + 200; tickScan();
  r.scanDecays = sc.scanT < 20;
  enemies.splice(enemies.indexOf(sc), 1);
  // the AI's arms: FS2 default banks
  r.aiFs2 = String(aiLoadout({img:'fiperseus'}).p) === 'subach,promr' && aiLoadout({img:'fitoth'}).p === 'promr' &&
            aiLoadout({img:'fiseth'}).p === 'mekhu' && aiLoadout({img:'boursa'}).pair === true && aiLoadout({img:'boursa'}).s === 'cyclops';
  r.aiArsenalGun = priDef('subach').key === 'subach' && priDef('mekhu').en > 0;
  // a fighter with two banks fires both, each paid from the store
  const f = {type:'fighter', img:'fiperseus', x:600, y:250, side:'enemy', faction:'ntf', hp:100, maxHp:100};
  const pts = [{x:600, y:245}, {x:600, y:255}];
  eBullets.length = 0;
  aiGunVolley(f, player, aiLoadout(f), pts, 0, null, 1);
  r.twoBanks = eBullets.length === 2 && Object.keys(f.mT).length === 2;
  // the player's break-up uses the hull last drawn in 3D
  r.playerObj = typeof f3dPlayer === 'function' && F3D_PL.player === true;
  try{ draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }
  return r;`);

scenario('v204: hit on the model as drawn, damage on the model, debris in its layer, Pharos', 'm=1', `
  const r = {};
  // a flat plate, wide across (x) and thin (y), 4 long (z): side on it is a
  // thin strip, rolled a quarter turn it is as tall as it is wide
  const Q = 32767;
  const pos = new Int16Array([ -Q,-Q/10,-Q,  Q,-Q/10,-Q,  Q,Q/10,Q,  -Q,Q/10,Q,  -Q,Q/10,-Q,  Q,Q/10,-Q ]);
  const idx = new Uint16Array([0,1,2, 0,2,3, 0,4,2, 1,5,2]);
  const L = {state:'ready', head:{size:[4,0.4,4], ext:2}, cpu:[{pos:pos, idx:idx}]};
  const img = document.createElement('canvas'); img.width = 80; img.height = 20;
  const m0 = f3dBuildMask(L, img, 1, 0), m90 = f3dBuildMask(L, img, 1, Math.PI/2);
  r.rolledTaller = m90.ky > m0.ky * 2;
  // the roll picks the map: a point above the sprite's box hits only rolled
  const key = 'fimyrmidon', keep = IMGS[key], keepM = F3D.models[key], keepOff = F3D.off;
  IMGS[key] = img; F3D.models[key] = {lo: L, full: L}; F3D.off = false;
  const o = {img:key, x:300, y:200, sc:1, flip:false, ang:0, _f3fc: fc, _f3df: F3D_FRAME, _f3r: {r:0, b:0}};   // v216: drawn = counted in pictures (_f3df)
  const hitFlat = onHull(key, 300, 200, 1, false, 300, 200 - 25, 0, o);
  o._f3r = {r:Math.PI/2, b:0};
  const hitRolled = onHull(key, 300, 200, 1, false, 300, 200 - 25, 0, o);
  const oldFc = o._f3fc; o._f3fc = fc - 10; o._f3df = F3D_FRAME - 10;
  const hitStale = onHull(key, 300, 200, 1, false, 300, 200 - 25, 0, o);
  r.rollMask = hitFlat === false && hitRolled === true && hitStale === false;
  r.stages = (F3D_RMASK[key] || []).filter(Boolean).length >= 2;
  IMGS[key] = keep; if(keepM) F3D.models[key] = keepM; else delete F3D.models[key]; F3D.off = keepOff; delete F3D_RMASK[key];
  // damage of a ship drawn from her model: kept up to date, not painted in 2D
  const cap = enemies.find(e => !e.small && e.type !== 'asteroid') || allies.find(a => !a.small);
  if(cap){
    cap.dm = null; cap.hp = cap.maxHp * 0.4;
    try{ dmgPreset(cap); }catch(ex){}
    const D = cap.dm;
    if(D){
      const di = ctx.drawImage; let n = 0; ctx.drawImage = function(){ n++; return di.apply(ctx, arguments); };
      D.dirty = true; D.built = -99;
      cap._gl3 = 2; try{ drawShipE(cap, cap.x, cap.y, cap.sc, cap.flip, cap.ang||0); } finally { cap._gl3 = false; ctx.drawImage = di; }
      r.dmgNot2D = n === 0 && !!D.can && D.gl3 === true;
    } else r.dmgNot2D = true;
  } else r.dmgNot2D = true;
  r.dmgBind = typeof f3dDmgBind === 'function';
  // debris items carry their ship's place
  r.hulkItems = typeof f3dHulkItem === 'function' && typeof f3dHulksOn === 'function';
  // the Pharos is drawn from her model
  r.pharos3d = f3dKey({img:'inpharos'}) === 'inpharos' && !f3dSmall('inpharos');
  try{ draw(); r.draws = true; }catch(ex){ r.draws = String(ex); }
  return r;`);

// ── v240: the FS1 strand, missions 1-3 ────────────────────────────────
scenario('FS1 M1 Eve of Destruction: strand, arms, timed wings, the end', 'm=1', `
  const r = {};
  r.strandIsFs1 = currentEra==='fs1' && missionOrig===1;
  r.fliesTheApollo = player.ship==='fiapollo';
  r.fs1BanksMl16Mx50 = player.pb.map(b=>b.key).join()==='ml16,ml16' && player.sb.map(b=>b.key).join()==='mx50,mx50';
  r.noShieldInFs1 = player.sh===0;
  r.furyOnOffer = bankChoices('fiapollo', false).map(w=>w.key).indexOf('fury')>=0
               && weaponOpenFor(secDefP('fury'), 'fiapollo') && !weaponOpenFor(secDefP('interceptor'), 'fiapollo');
  r.noFs2Gun = bankChoices('fiapollo', true).every(w=>w.era==='fs1');
  FS.step(300);
  const orff = allies.find(a=>a.uid==='A1');
  r.orffNamed = !!orff && orff.label==='GTC ORFF';
  const a2 = allies.find(a=>a.uid==='W1');
  r.wingmanTerran = !!a2 && a2.faction==='terran' && a2.img==='fiapollo';
  r.noRearmWithoutHomeShip = rearmReady()===false;
  FS.until(()=>byId('E1').some(e=>!(e.warp>0)), 2000, false);
  const an = byId('E1')[0], lo = an ? aiLoadout(an) : null;
  r.anubisFliesFs1 = !!lo && lo.p==='ml16' && lo.s==='fury';
  // F23: no shields before mission 9, not on them, not on our wingman
  r.anubisNoShield = byId('E1').length>0 && byId('E1').every(e=>e.maxSh===0);
  r.wingmanNoShield = !!a2 && a2.maxSh===0;
  let strayBomber = false, strayAlly = false;
  const watch = ()=>{ if(enemies.some(e=>e.type==='bomber')) strayBomber = true;
                      if(allies.some(a=>!a.uid)) strayAlly = true; };
  // Nobody shot down: the second wing must come 30 s after the first.
  const t0 = spawnT;
  const t = FS.until(()=>{ watch(); return evSeen('E2'); }, 4500, false);
  r.secondWingWithin30s = t>=0 && (spawnT - t0) <= 31*TICK_HZ;
  // Now clear everything as it comes: the mission ends in success.
  const e = FS.until(()=>{ watch(); return waveOver || wave>1; }, 30000, true);
  r.ends = e>=0;
  // F23: the Orff is the mission's, not a called ship - no bombers answer
  // her, and she scrambles no FS2 fighters
  r.noBombersAnswerTheOrff = !strayBomber;
  r.noShipsNobodyAskedFor = !strayAlly;
  r.orffAlive = !!orff && !orff.dead;
  return r;`);

scenario('FS1 M1: the Orff lost ends the mission', 'm=1', `
  const r = {};
  FS.until(()=>allies.some(a=>a.uid==='A1' && !(a.warp>0)), 2000, false);
  for(const a of allies) if(a.uid==='A1') a.hp = 0;
  const t = FS.until(()=>waveOver || wave>1, 6000, false);
  r.endsAtOnce = t>=0;
  r.noWingLeftBehind = !Object.keys(EV_HELD).length;
  return r;`);

scenario('FS1 M2 The Field of Battle: two wings at once, the ace always', 'm=2', `
  const r = {};
  r.strandIsFs1 = currentEra==='fs1' && missionOrig===2;
  r.stillRocks = enemies.filter(e=>e.type==='asteroid').length>0 || spawnQ.some(q=>q.type==='ast');
  FS.until(()=>evSeen('E1') && evSeen('E2'), 2000, false);
  r.twoWingsTogether = evSeen('E1') && evSeen('E2');
  FS.until(()=>byId('E1').some(e=>!(e.warp>0)), 1000, false);
  r.anubisNoShield = enemies.filter(e=>e.type==='fighter').every(e=>e.maxSh===0);
  r.bothFromTheirSides = byId('E1').length>0 && byId('E2').length>0;
  const t = FS.until(()=>evSeen('S1'), 30000, true);
  r.aceComes = t>=0;
  const e = FS.until(()=>waveOver || wave>2, 30000, true);
  r.ends = e>=0;
  return r;`);

scenario('FS1 M3 Small Deadly Space: runners, the McCarthy, then FS2 again', 'm=3', `
  const r = {};
  r.strandIsFs1 = currentEra==='fs1' && missionOrig===3;
  FS.step(400);
  r.fiveContainers = enemies.filter(e=>e.type==='container').length===5;
  const f1 = byId('F1')[0];
  r.bastNamed = !!f1 && f1.label==='PVFR BAST';
  // F24: nothing flies backwards - she comes in from the right, so she
  // faces left on her way to the container, and right once she runs
  FS.step(100);
  r.bastFacesHerContainer = !!f1 && !EV_DOCK.F1 && f1.flip===needsFlip('frbast', true);
  // the runners load first, then run
  const d = FS.until(()=>!!EV_DOCK.F1 && !!EV_DOCK.F2, 12000, true);
  r.freightersDock = d>=0;
  r.containerTaken = enemies.some(e=>e.uid==='C1' && e.carried);
  // v243: she turns round, she does not snap - half way through she is
  // still on her old heading, bow on
  // v244: the container stays on the deck through the turn - it moves with
  // the dock point step by step, it does not slide off and snap back
  const runners = byId('F1').concat(byId('F2'));
  let slip = 0;
  for(let i=0;i<60;i++){
    FS.step(1);
    for(const f of runners){
      if(f.dead || !f.dockedTo) continue;
      const p = dockPoint(f), o = dockOffset(f.dockedTo), c = f.dockedTo;
      slip = Math.max(slip, Math.hypot(c.x - (p.x - o.x), c.y - (p.y - o.y)));
    }
  }
  r.containerTurnsWithHer = runners.some(f=>f.dockedTo && f.dockedTo.turnP===f.turnP && f.turnP>0)
                          && slip < 2;
  r.runnerTurnsRound = runners.some(f=>f.turnP > 0 && f.turnP < 1 && f.flip===needsFlip(f.img, true));
  // no snap at the end of the turn either
  let jump = 0, roll = 0;
  for(let i=0;i<160;i++){
    const before = runners.filter(f=>f.dockedTo && !f.dead).map(f=>[f, f.dockedTo.x - f.x]);
    // what the 3D view asks every frame: how far the container is rolled
    for(const f of runners) if(f.dockedTo) roll = Math.max(roll, Math.abs(f3dTurnRoll(f.dockedTo)));
    FS.step(1);
    for(const [f, d0] of before) if(f.dockedTo) jump = Math.max(jump, Math.abs((f.dockedTo.x - f.x) - d0));
  }
  r.noSnapAtTheEnd = jump < 3;
  // v245: and no extra roll about its length once the turn is done
  for(const f of runners) if(f.dockedTo) roll = Math.max(roll, Math.abs(f3dTurnRoll(f.dockedTo)));
  r.containerDoesNotRollAfter = roll < 0.7;
  r.runnerFacesTheWayOut = runners.length>0 && runners.filter(f=>!f.dead)
                             .every(f=>f.flip===needsFlip(f.img, false) && f.turnP==null);
  // Our wingmen may stop one; either way both are gone in the end.
  const g = FS.until(()=>!byId('F1').length && !byId('F2').length, 30000, true);
  r.freightersGone = g>=0;
  r.twoMoreAnubis = evSeen('E3');
  const m = FS.until(()=>evSeen('T1'), 20000, true);
  r.mccarthyComes = m>=0;
  const mc = byId('T1')[0];
  r.mccarthyJumpsIn = !!mc && mc.warp>0;
  FS.step(2);       // the name is put on at the next event tick
  r.transportNamedOmega = !!mc && mc.label==='GTT OMEGA';
  // F25: a transport of 32 m opens a vortex, she is no big ship
  // v247: the long sound is for destroyers and juggernauts only
  r.mccarthyJumpSoundIsTheVortex = !!mc && warpSndSmall(mc)===true
    && ['crfenris','codeimos','frchronos','inknossos45deg'].every(k=>warpSndSmall({img:k}))
    && ['deorionright','ntfdehecate','sdsathanas','sdlucifer','sdcolossus'].every(k=>!warpSndSmall({img:k}));
  const k = FS.until(()=>!!EV_DOCK.T1, 20000, true);
  r.mccarthyLoads = k>=0;
  r.coverWings = evSeen('E4') && evSeen('E5');
  const o = FS.until(()=>!!EV_LEFT.T1, 3000, true);
  r.mccarthyAway = o>=0;
  const e = FS.until(()=>wave>3, 6000, true);
  r.ends = e>=0;
  // v249: mission 4 is FS1 Avenging Angels now - still the FS1 strand.
  FS.until(()=>missionOrig===4, 400, false);
  r.onToFs1M4 = (currentEra==='fs1' && missionOrig===4 && player.ship==='fiapollo') || [currentEra, missionOrig, player.ship, wave];
  return r;`);

// v249: FS1 missions 4 to 6 (FS1_MISSIONEN.md).
scenario('FS1 M4 Avenging Angels: runners, the Omega taken, the bonus', 'm=4', `
  const r = {};
  r.strandIsFs1 = currentEra==='fs1' && missionOrig===4;
  FS.step(300);
  const o = byId('O1')[0], ra = byId('R1')[0];
  r.bothThere = !!o && !!ra;
  FS.step(2);
  r.named = !!o && o.label==='GTT OMEGA' && !!ra && ra.label==='PVT RASPUTIN';
  r.engineAndWeaponsToShoot = !!o && !!o.subs && ['engines','weapons'].every(id=>o.subs.some(s=>s.id===id));
  // nobody has fired: both sit where they are
  const x0 = o ? o.x : 0;
  FS.step(400);
  r.waitsUntilFiredOn = !!o && Math.abs(o.x - x0) < 1 && !o.wasHit;
  // our wingmen leave the prizes alone
  r.wingmenSpareThem = (!!o && o.hp===o.maxHp && !!ra && ra.hp===ra.maxHp) || [o&&o.hp, o&&o.maxHp, ra&&ra.hp, ra&&ra.maxHp, ra&&ra.wasHit];
  // fired on: she runs
  damageEnemy(o, 1, o.x, o.y, true);
  const x1 = o.x;
  FS.step(200);
  r.runsWhenFiredOn = o.x > x1 + 5;
  r.rasputinStillSits = !ra.wasHit && !evSeen('E4');
  damageEnemy(ra, 1, ra.x, ra.y, true);
  FS.step(40);
  r.firedOnRasputinBringsTwoAnubis = !!EV_HIT.R1 && FS.until(()=>evSeen('E4'), 400, false)>=0;
  // v250: the opening wing is down first, as a player would have it. Left
  // alive, seven ships fall on the Comet; v249 passed with her at 12 hull,
  // by the luck of the draw, and the Valkyrie's different flight tipped it.
  for(const e of enemies) if(/^(E1|E2|B1)$/.test(e.uid||'')) e.hp = 0;
  FS.step(20);
  // engines and weapons out: she stops, the Comet comes
  for(const sb of o.subs) if(sb.id==='engines'||sb.id==='weapons'){ sb.hp = 0; sb.dead = true; }
  FS.step(40);
  const x2 = o.x; FS.step(100);
  r.deadInSpace = Math.abs(o.x - x2) < 1;
  r.cometComes = FS.until(()=>evSeen('T1'), 600, false)>=0 && evSeen('E3');
  r.cannotDieMeanwhile = (damageEnemy(o, 1e6, o.x, o.y, true), FS.step(20), byId('O1').length===1);
  r.captured = FS.until(()=>!!EV_TAKEN.O1, 20000, true)>=0;
  r.notCountedAsEscaped = !EV_LEFT.O1;
  // the bonus: the Rasputin taken too
  const rr = byId('R1')[0];
  if(rr) for(const sb of rr.subs) if(sb.id==='engines'||sb.id==='weapons'){ sb.hp = 0; sb.dead = true; }
  r.bonusTaken = FS.until(()=>!!EV_TAKEN.R1, 20000, true)>=0;
  r.ends = FS.until(()=>wave>4, 20000, true, true)>=0;
  FS.until(()=>missionOrig===5, 400, false);
  r.onToM5 = currentEra==='fs1' && missionOrig===5;
  return r;`);

scenario('FS1 M4: nobody fires - they run on their own, the mission ends', 'm=4', `
  const r = {};
  FS.step(300);
  const o = byId('O1')[0];
  const x0 = o ? o.x : 0;
  // 60 s at the latest, then she runs anyway
  r.runsAtTheLatest = FS.until(()=>o && o.x > x0 + 20, 9000, true)>=0;
  r.omegaAway = FS.until(()=>!!EV_LEFT.O1, 20000, true)>=0;
  r.failed = FS.until(()=>objCard && objCard.tone==='fail', 400, false)>=0 || !missionObj;
  r.ends = FS.until(()=>wave>4, 20000, true)>=0;
  return r;`);

scenario('FS1 M4: the Comet lost - the Omega jumps, failed', 'm=4', `
  const r = {};
  FS.step(300);
  const o = byId('O1')[0];
  damageEnemy(o, 1, o.x, o.y, true);
  for(const sb of o.subs) if(sb.id==='engines'||sb.id==='weapons'){ sb.hp = 0; sb.dead = true; }
  r.cometComes = FS.until(()=>byId('T1').length>0 && !(byId('T1')[0].warp>0), 2000, false)>=0;
  const c = byId('T1')[0];
  if(c) c.hp = 0;
  r.cometLost = FS.until(()=>!byId('T1').length, 2000, false)>=0;
  r.failed = FS.until(()=>objCard && objCard.tone==='fail', 400, false)>=0;
  r.omegaGone = FS.until(()=>!byId('O1').length, 2000, false)>=0 && !EV_TAKEN.O1;
  r.ends = FS.until(()=>wave>4, 20000, true)>=0;
  return r;`);

scenario('FS1 M5 Out of the Dark: Vasudans, the Taurus, the unknowns, the Plato through', 'm=5', `
  const r = {};
  r.strandIsFs1 = currentEra==='fs1' && missionOrig===5;
  FS.step(300);
  const p = byId('P1')[0];
  FS.step(2);
  r.platoNamed = !!p && p.label==='GTSC PLATO';
  r.platoCrosses = (()=>{ const x0 = p.x; FS.step(200); return p.x > x0; })();
  r.taurusComes = FS.until(()=>evSeen('K1'), 6000, true)>=0;
  FS.step(2);
  r.taurusNamed = byId('K1').some(k=>k.label==='PVC TAURUS');
  // the Taurus is left standing so the unknowns can go for her
  r.unknownsCome = FS.until(()=>evSeen('S0'), 6000, false, false, 50)>=0
                 || FS.until(()=>evSeen('S0'), 6000, true)>=0;
  const s0 = byId('S0')[0];
  r.shivan = !!s0 && s0.faction==='shivan';
  r.lockable = !!s0 && !s0.noTarget && s0.scan;
  r.feud = waveFeud===true;
  if(s0) FS.hold(s0.x, s0.y, 1);
  let held = 0;
  for(let i=0;i<400 && s0 && !s0.scanned;i++){ FS.hold(s0.x, s0.y, 1); held++; }
  r.scanned = !!s0 && s0.scanned;
  r.secondShivanWave = FS.until(()=>evSeen('S2') && evSeen('X2'), 4000, false)>=0;
  // keep her alive and let her cross
  let tone = '';
  const t = FS.until(()=>{ const q = byId('P1')[0]; if(q) q.hp = q.maxHp;
                            if(objCard && objCard.tone) tone = objCard.tone;
                            return !!EV_LEFT.P1; }, 30000, true);
  r.platoThrough = t>=0;
  FS.step(40);
  if(objCard && objCard.tone) tone = objCard.tone;
  r.success = tone==='done';
  r.noPod = !evSeen('H1');
  r.ends = FS.until(()=>wave>5, 20000, true, true)>=0;
  return r;`);

scenario('FS1 M5: the Plato lost, her pod away - partial success', 'm=5', `
  const r = {};
  FS.step(600);
  const p = byId('P1')[0];
  p.hp = p.maxHp*0.15;
  r.podUnder20 = FS.until(()=>evSeen('H1'), 400, false)>=0;
  p.hp = 0;
  r.platoLost = FS.until(()=>!byId('P1').length, 3000, false)>=0;
  let tone = '';
  r.podAway = FS.until(()=>{ const h = byId('H1')[0]; if(h) h.hp = h.maxHp;
                              if(objCard && objCard.tone) tone = objCard.tone;
                              return !!EV_LEFT.H1; }, 20000, true)>=0;
  FS.step(40);
  if(objCard && objCard.tone) tone = objCard.tone;
  r.partial = tone==='part';
  r.ends = FS.until(()=>wave>5, 20000, true, true)>=0;
  return r;`);

scenario('FS1 M5: the Plato and her pod lost - failed', 'm=5', `
  const r = {};
  FS.step(600);
  const p = byId('P1')[0];
  p.hp = 0;
  r.podLaunched = FS.until(()=>byId('H1').length>0, 3000, false)>=0;
  let tone = '';
  const h = byId('H1')[0]; if(h) h.hp = 0;
  r.podLost = FS.until(()=>{ if(objCard && objCard.tone) tone = objCard.tone;
                              return !byId('H1').length && !byId('P1').length; }, 3000, false)>=0;
  FS.step(40);
  if(objCard && objCard.tone) tone = objCard.tone;
  r.failed = tone==='fail';
  r.ends = FS.until(()=>wave>5, 20000, true, true)>=0;
  return r;`);

scenario('FS1 M6 Paving the Way: the Galatea, five wings, the jump', 'm=6', `
  const r = {};
  r.strandIsFs1 = currentEra==='fs1' && missionOrig===6;
  FS.step(300);
  const g = byId('G1')[0];
  FS.step(2);
  r.galateaNamed = !!g && g.label==='GTD GALATEA';
  r.homeShip = !!g && g.home===true && homeShipOnField()===true;
  r.shivans = FS.until(()=>evSeen('B1'), 1500, false)>=0 && byId('B1').every(b=>b.faction==='shivan');
  // every wing comes, none waits longer than 30 s
  let ok = true;
  for(const id of ['J1','B2','J2','B3']){
    const w = FS.until(()=>evSeen(id), 3600, false);   // 30 s plus a margin
    if(w<0) ok = false;
  }
  r.wingsWithinThirtySeconds = ok;
  let tone = '';
  const j = FS.until(()=>{ const q = byId('G1')[0]; if(q) q.hp = q.maxHp;
                            if(objCard && objCard.tone) tone = objCard.tone;
                            return !!EV_LEFT.G1; }, 12000, true);
  r.galateaJumps = j>=0;
  FS.step(40);
  if(objCard && objCard.tone) tone = objCard.tone;
  r.success = tone==='done';
  r.ends = FS.until(()=>wave>6, 20000, true, true)>=0;
  // Mission 7 is the old Hammer of Light again: FS2 rules and arms.
  FS.until(()=>missionOrig===0, 400, false);
  r.backToFs2 = currentEra==='fs2' && missionOrig===0 && player.ship==='fitoth'
             && player.pb.every(b=>!priDefP(b.key).era);
  return r;`);

scenario('FS1 M6: the Galatea lost - failed', 'm=6', `
  const r = {};
  FS.step(600);
  const g = byId('G1')[0];
  g.hp = 0;
  let tone = '';
  r.lost = FS.until(()=>{ if(objCard && objCard.tone) tone = objCard.tone;
                           return !byId('G1').length; }, 3000, false)>=0;
  FS.step(40);
  if(objCard && objCard.tone) tone = objCard.tone;
  r.failed = tone==='fail';
  r.ends = FS.until(()=>wave>6, 20000, true, true)>=0;
  return r;`);

scenario('FS1 M3: agreed container lost, the McCarthy leaves empty', 'm=3', `
  const r = {};
  FS.step(400);
  for(const e of enemies) if(e.uid==='K1') e.hp = 0;
  FS.until(()=>!byId('F1').length && !byId('F2').length, 30000, true);
  FS.until(()=>evSeen('T1'), 20000, true);
  const t = FS.until(()=>wave>3, 12000, true);
  r.endsWithoutTheContainer = t>=0;
  return r;`);

// F56 (v256): the container shot while the Omega is on her way to it - she
// jumps out at once and the mission ends as a failure, no slow drive off.
scenario('FS1 M3 F56: container shot as the Omega docks - quick end', 'm=3', `
  const r = {};
  FS.step(400);
  FS.until(()=>!byId('F1').length && !byId('F2').length, 30000, true);
  FS.until(()=>byId('T1').some(a=>!(a.warp>0)), 20000, true);
  FS.step(200);
  for(const e of enemies) if(e.uid==='K1') e.hp = 0;
  r.countsAsEmpty = FS.until(()=>!!EV_EMPTY['T1'], 500, false) >= 0;
  const t = FS.until(()=>wave>3, 1500, false);
  r.endsWithin15s = t>=0;
  return r;`);

scenario('FS1 M3: the McCarthy lost ends the mission', 'm=3', `
  const r = {};
  FS.step(400);
  FS.until(()=>!byId('F1').length && !byId('F2').length, 30000, true);
  FS.until(()=>byId('T1').some(a=>!(a.warp>0)), 20000, true);
  for(const a of allies) if(a.uid==='T1') a.hp = 0;
  const t = FS.until(()=>wave>3, 6000, false);
  r.endsAtOnce = t>=0;
  return r;`);


// ── v250: Silvio's findings on M2 to M6 (F27 to F34) ────────────────────
scenario('FS1 v250: each mission flies the original Alpha 1 hull (F27)', 'm=1', `
  const r = {}, want = {1:'fiapollo', 2:'fiapollo', 3:'fiapollo', 4:'fivalyrie', 5:'fiapollo', 6:'fiapollo'};
  const got = {};
  for(const m of [1,2,3,4,5,6]){
    wave = m-1; nextWave(); FS.step(5);
    got[m] = player.ship;
  }
  r.hulls = JSON.stringify(got);
  r.allOriginal = [1,2,3,4,5,6].every(m=>got[m]===want[m]);
  return r;`);

scenario('FS1 M4 v250: only engines and weapons to shoot out (F28)', 'm=4', `
  const r = {};
  FS.step(200);
  const ids = ['O1','R1'].map(u=>{ const e = byId(u)[0]; return e && e.subs ? e.subs.map(s=>s.id).sort().join('+') : '-'; });
  r.subs = ids.join(' ');
  r.onlyTheTwo = ids.every(x=>x==='engines+weapons');
  return r;`);

scenario('FS1 M5 v250: the pod runs at two thirds of an Apollo (F29)', 'm=5', `
  const r = {};
  FS.step(400);
  const p = byId('P1')[0];
  p.hp = Math.round(p.maxHp*0.15);
  FS.until(()=>byId('H1').some(a=>!(a.warp>0)), 3000, true);
  const h = byId('H1')[0];
  r.launched = !!h;
  if(h){ const x0 = h.x; FS.step(100); r.perStep = +((h.x-x0)/100).toFixed(2); }
  r.fastEnough = r.perStep >= 2.5;
  return r;`);

scenario('FS1 M6 v250: the Galatea under way through a rock field (F30, F31)', 'm=6', `
  const r = {};
  FS.step(300);
  const g = byId('G1')[0];
  const x0 = g.x; FS.step(1000);
  r.moved = Math.round(g.x - x0);
  r.underWay = r.moved > 100;
  r.rocks = enemies.filter(e=>e.scenery && e.type==='asteroid').length;
  r.hasField = r.rocks >= 40;
  return r;`);

scenario('FS1 M2 v250: the rock field fills the view, not the mission area (F32)', 'm=2', `
  const r = {};
  FS.step(100);
  const xs = enemies.filter(e=>e.scenery && e.type==='asteroid').map(e=>e.x);
  r.span = Math.round(Math.max(...xs) - Math.min(...xs));
  r.wide = r.span > W/CAM_BASE_Z*0.7;
  return r;`);

scenario('FS1 M3 v250: the freighters are red from the first frame (F33)', 'm=3', `
  const r = {};
  FS.until(()=>byId('F1').length && byId('F2').length, 2000, true);
  const cols = ['F1','F2'].map(u=>offColour(byId(u)[0], false));
  r.cols = cols.join(' ');
  r.red = cols.every(c=>c===OFF_COL.enemy);
  return r;`);

scenario('FS1 M6 v250: the Galatea fires green, FS2 stays blue (F34)', 'm=6', `
  const r = {};
  FS.step(100);
  const g = byId('G1')[0];
  const m = mountsFor(g.img), tt = m && m.primary.find(q=>q.g && q.g.name==='Terran Turret');
  r.turretNamed = !!tt;
  r.green = !!tt && gunCol(g, tt.g) === FS1_GUN_COL;
  currentEra = 'fs2';
  r.fs2Blue = !!tt && gunCol(g, tt.g) === RACE_COL.terran;
  currentEra = 'fs1';
  return r;`);


// ── v251: Silvio's findings on v250 (F35 to F38) ────────────────────────
scenario('FS1 M6 v251: every Galatea shot green, a greener green (F35)', 'm=6', `
  const r = {};
  FS.step(100);
  const g = byId('G1')[0];
  const m = mountsFor(g.img);
  const rails = (m && m.primary || []).filter(q=>q.wasBeam);
  r.rails = rails.length;
  r.railsGreen = rails.length>0 && rails.every(q=>gunCol(g, q.g).core === FS1_GUN_COL.core);
  const c = gunCol(g, {}).core, rr = parseInt(c.substr(1,2),16), gg = parseInt(c.substr(3,2),16);
  r.core = c;
  r.notYellow = gg - rr >= 120;
  return r;`);

scenario('FS1 M6 v251: a triple turret fires one round after another (F36)', 'm=6', `
  const r = {};
  FS.step(100);
  const g = byId('G1')[0];
  const big = (mountsFor(g.img).primary || []).find(q=>q.g && q.g.big);
  r.hasBig = !!big;
  const n0 = pBullets.length;
  capGunShot(g, g.x, g.y, 0, big.g, true, false, null);
  r.atOnce = pBullets.length - n0;
  r.oneAtFirst = r.atOnce === 1;
  FS.step(40);
  r.threeInAll = pBullets.filter(b=>b.cap).length >= 3;
  return r;`);

scenario('FS1 M3 v251: both freighters hostile targets with red marks (F37)', 'm=3', `
  const r = {};
  FS.until(()=>byId('F1').some(e=>!(e.warp>0)) && byId('F2').some(e=>!(e.warp>0)), 2000, true);
  const f1 = byId('F1')[0], f2 = byId('F2')[0];
  r.bastHostile = tgtHostile(f1);
  r.maatHostile = tgtHostile(f2);
  const list = tgtShips(tgtHostile);
  r.bothInHostileKeys = list.indexOf(f1)>=0 && list.indexOf(f2)>=0;
  return r;`);

scenario('FS1 M6 v251: the exit vortex opens ahead, with a run-up (F38)', 'm=6', `
  const r = {};
  FS.step(300);
  const runUp = function(e){
    e.warpOut = e.warpMax || 100; e.warpX = e.x; e.warpY = e.y; e._fsG = null;
    fsWarp(e); const q = e._fsG; return q ? {lead: q.G - q.L/2, L: q.L} : null; };
  const w = runUp(byId('W1')[0]), g = runUp(byId('G1')[0]);
  r.wingman = w && +(w.lead/w.L).toFixed(2);
  r.galatea = g && Math.round(g.lead) + ' of ' + Math.round(g.L);
  // a fighter: more than half her length; a destroyer: the full cap
  r.fighterRunUp = !!w && w.lead >= 0.5*w.L;
  r.destroyerRunUp = !!g && g.lead >= Math.min(0.5*g.L, FS_OUT_LEAD_MAX) - 1;
  return r;`);


// ── v252: F40 to F42 ────────────────────────────────────────────────────
scenario('FS1 M5 v252: the Plato carries her FS1 guns, no Subach (F40)', 'm=5', `
  const r = {};
  FS.step(300);
  const p = byId('P1')[0];
  const names = (mountsFor(p.img).primary || []).map(q=>q.g && q.g.name);
  r.guns = [...new Set(names)].join(', ');
  r.noFs2 = names.length>0 && names.every(n=>n!=='Subach HL-7' && n!=='Mekhu HL-7');
  return r;`);

scenario('FS1 M6 v252: no trail while the bolt is under the hull, in its colour (F41)', 'm=6', `
  const r = {};
  FS.step(100);
  const g = byId('G1')[0];
  // an enemy bolt hidden and one in the open, then an ally bolt in the open.
  // Out in space, where nothing is hit; 'on her hull' is granted so the
  // hidden one stays hidden when drawn.
  const keepOH = onHullAt; onHullAt = function(){ return true; };
  const eb = function(hid, col){ eBullets.push({x:g.x, y:g.y-1500, vx:0.01, vy:0, w:8, h:4, dmg:0,
    faction:'shivan', col:col, glow:'rgba(0,0,0,0)', hidE: hid ? g : null, eLife:40}); };
  eb(true, '#123456'); eb(false, '#654321');
  // well away from every hull, so no hit spark carries the colour
  pBullets.push({x:g.x, y:g.y-1500, vx:0.01, vy:0, w:8, h:4, dmg:0, ally:true, fac:'terran', cap:true,
    col:'#abcdef', glow:'rgba(0,0,0,0)', hidE:null, pLife:40});
  FS.step(12);
  onHullAt = keepOH;
  r.hiddenTrail = PARTS.filter(p=>p.clr==='#123456').length;
  r.openTrail = PARTS.filter(p=>p.clr==='#654321').length;
  r.allyTrail = PARTS.filter(p=>p.clr==='#abcdef').length;
  r.noneWhileHidden = r.hiddenTrail === 0 && r.openTrail > 0;
  r.ownColour = r.allyTrail > 0;
  return r;`);

scenario('FS1 M6 v252: turret shots heard in their own mix, every round of a triple (F42)', 'm=6', `
  const r = {};
  FS.step(100);
  const heard = [];
  const keep = sndStart;
  sndStart = function(name, x, vol, loop, mix){ heard.push(mix); return null; };
  const g = byId('G1')[0];
  capGunShot(g, g.x, g.y, 0, {big:true, aspd:5, admg:1, spd:5, dmg:1, w:12, h:12, snd:'wpn_tht'}, true, false, null);
  FS.step(40);
  sndStart = keep;
  r.heard = heard.join(' ');
  r.burstHeard = heard.filter(m=>m==='cap_heavy').length >= 2;
  return r;`);

// ── v253: FS1 missions 7 to 13, and what they brought ────────────────

scenario('FS1 M7 Pandora: three scans, the trap, blast waves that hurt, held out', 'm=7', `
  const r = {};
  r.strand = currentEra==='fs1' && missionOrig===7 && player.ship==='fivalyrie';
  FS.step(300);
  r.sixContainers = ['K1','K2','K3','K4','K5','K6'].every(id=>byId(id).length===1);
  r.threeToScan = ['K1','K3','K5'].every(id=>byId(id)[0].scan) && !byId('K2')[0].scan;
  r.noTrapYet = !evSeen('M1');
  FS.killId('G1'); FS.step(20);
  // the three scanned; the player sits close to K2 and takes what comes
  const k2 = byId('K2')[0];
  const px = k2.x - 50, py = k2.y;
  for(const id of ['K1','K3','K5']) byId(id)[0].scanned = true;
  let minHp = player.maxHp, cargoShocks = 0;
  for(let t=0;t<800;t++){
    player.x = px; player.y = py; player.vx = 0; player.vy = 0;
    update(); if(t%25===0) draw();
    for(const sh of SHOCKS) if(sh.pct===CARGO_SHOCK[2] && !seen.has(sh)){ seen.add(sh); cargoShocks++; }
    minHp = Math.min(minHp, player.hp);
    if(player.hp <= 0) break;
  }
  r.containersGoneOneByOne = ['K1','K2','K3','K4','K5','K6'].every(id=>byId(id).length===0) && cargoShocks===6;
  r.containersLeft = ['K1','K2','K3','K4','K5','K6'].filter(id=>byId(id).length>0).join(',') + ' / shocks ' + cargoShocks;
  r.blastHurts = minHp < player.maxHp;
  r.lostToTheBlasts = Math.round((1 - minHp/player.maxHp)*100) + ' %';
  r.notDeadly = minHp > player.maxHp*0.25;
  r.trapSprung = evSeen('M1') && evSeen('C1');
  player.hp = player.maxHp;
  r.noClockShown = !(missionTimer && missionTimer.end > 0);
  r.heldOut = FS.until(()=>objCard && objCard.tone==='done', 9000, true)>=0;
  r.ends = FS.until(()=>wave>7, 20000, true)>=0;
  return r;`);

scenario('FS1 M8 Shieldbreaker: scan, all three run, disable, the Elysium takes her', 'm=8', `
  const r = {};
  r.strand = currentEra==='fs1' && missionOrig===7 && player.ship==='fiapollo';
  r.dAdvancedInBankOne = !!player.pb && player.pb[0].key==='dadv';
  FS.step(300);
  const f1 = byId('F1')[0], f2 = byId('F2')[0], f3 = byId('F3')[0];
  r.threeAsmodeus = !!f1 && !!f2 && !!f3 && f1.img==='frasmodeus';
  const k1 = byId('K1')[0], k2 = byId('K2')[0];
  r.twoContainersRideOnHer = !!k1 && !!k2 && Math.abs(k1.x-k2.x) > 5 && k1.y < f1.y && k2.y < f1.y;
  r.noMarkBeforeTheScan = missionMark(f1)==='';
  const x1 = f1.x, x2 = f2.x, x3 = f3.x;
  r.sitUntilFiredOn = (FS.step(200), Math.abs(f2.x - x2) < 1);
  damageEnemy(f3, 1, f3.x, f3.y, true);
  FS.step(300);
  r.oneHitAllThreeRun = f1.x > x1+5 && f2.x > x2+5 && f3.x > x3+5;
  r.cargoGoesAlong = Math.abs(k1.x - f1.x) < 60;
  k2.scanned = true; FS.step(30);
  r.markedDisable = missionMark(f1)==='DISABLE';
  FS.killId('E1'); FS.step(20);
  for(const sb of f1.subs) if(sb.id==='engines'||sb.id==='weapons'){ sb.hp = 0; sb.dead = true; }
  FS.step(40);
  const xs = f1.x; FS.step(100);
  r.deadInSpace = Math.abs(f1.x - xs) < 1;
  r.markedProtect = missionMark(f1)==='PROTECT';
  r.theShivansWantHerDead = !!f1.prey && waveHunt==='F1';
  r.elysiumComes = FS.until(()=>evSeen('T1'), 600, false)>=0;
  r.swarmsCome = FS.until(()=>evSeen('S1'), 800, false)>=0;
  damageEnemy(f1, 1e6, f1.x, f1.y, true); FS.step(10);
  r.playerCannotDestroyHer = byId('F1').length===1 && !f1.dead && f1.rollT==null;
  f1.hp = f1.maxHp;   // as she was: what follows is not about the player's fire
  r.taken = FS.until(()=>!!EV_TAKEN.F1, 20000, true)>=0;
  r.cargoLeavesWithHer = FS.until(()=>byId('K1').length===0 && byId('K2').length===0, 3000, false)>=0 && !!EV_LEFT.K2;
  r.success = FS.until(()=>objCard && objCard.tone==='done', 400, false)>=0;
  r.ends = FS.until(()=>wave>8, 20000, true)>=0;
  return r;`);

scenario('FS1 M8 Shieldbreaker: Shivan fire destroys her - failed', 'm=8', `
  const r = {};
  FS.step(300);
  const f1 = byId('F1')[0];
  for(const sb of f1.subs) if(sb.id==='engines'||sb.id==='weapons'){ sb.hp = 0; sb.dead = true; }
  r.prey = FS.until(()=>!!f1.prey && PREY_ON, 400, false)>=0;
  const hp0 = f1.hp;
  eBullets.push({x:f1.x, y:f1.y, vx:0, vy:0, w:6, h:6, dmg:1e6, faction:'shivan', life:50});
  FS.step(3);
  r.theirFireBites = f1.hp < hp0;
  r.failed = FS.until(()=>objCard && objCard.tone==='fail', 4000, false)>=0;
  r.ends = FS.until(()=>wave>8, 20000, true)>=0;
  return r;`);

scenario('FS1 M8 Shieldbreaker: the first Elysium lost, a second comes; both lost - failed', 'm=8', `
  const r = {};
  FS.step(300);
  const f1 = byId('F1')[0];
  for(const sb of f1.subs) if(sb.id==='engines'||sb.id==='weapons'){ sb.hp = 0; sb.dead = true; }
  r.firstComes = FS.until(()=>byId('T1').length>0 && !(byId('T1')[0].warp>0), 2000, false)>=0;
  byId('T1')[0].hp = 0;
  r.secondComes = FS.until(()=>byId('T2').length>0 && !(byId('T2')[0].warp>0), 3000, false)>=0;
  r.notFailedYet = !(objCard && objCard.tone==='fail');
  byId('T2')[0].hp = 0;
  r.failed = FS.until(()=>objCard && objCard.tone==='fail', 3000, false)>=0;
  r.ends = FS.until(()=>wave>8, 20000, true)>=0;
  return r;`);

scenario('FS1 M8 Shieldbreaker: nobody fires - they run at the latest, failed', 'm=8', `
  const r = {};
  r.away = FS.until(()=>!!EV_LEFT.F1, 30000, true)>=0;
  r.cargoWentAlong = !!EV_LEFT.K1 && !!EV_LEFT.K2;
  r.failed = FS.until(()=>objCard && objCard.tone==='fail', 400, false)>=0;
  r.ends = FS.until(()=>wave>8, 20000, true)>=0;
  return r;`);

scenario('FS1 M9 Hammer A: cargo rides on the Thetas, all through - the bonus', 'm=9', `
  const r = {};
  r.strand = currentEra==='fs1' && missionOrig===8;
  FS.step(300);
  const t1 = byId('T1')[0], k1 = byId('K1')[0];
  r.cargoOnTheirs = !!t1 && !!k1 && k1.side==='ally' && Math.abs(k1.x - t1.x) < 80;
  r.marked = missionMark(t1)==='PROTECT';
  r.secondBasilisksWaitForTheFirst = (FS.until(()=>evSeen('B2'), 20000, true)>=0) && !evSeen('B3');
  r.threeAtOnce = byId('B2').length===3 || enemies.filter(e=>e.uid==='B2').length<=3;
  r.success = FS.until(()=>objCard && objCard.tone==='done', 30000, true)>=0;
  r.nothingLost = protLost===0;
  r.cargoJumpsOut = FS.until(()=>!!EV_LEFT.K1 && !!EV_LEFT.K2 && !!EV_LEFT.K3, 3000, false)>=0;
  r.ends = FS.until(()=>wave>9, 20000, true)>=0;
  return r;`);

scenario('FS1 M9 Hammer A: all three containers lost - failed', 'm=9', `
  const r = {};
  FS.step(300);
  for(const id of ['K1','K2','K3']) for(const a of allies) if(a.uid===id) a.hp = 0;
  r.failed = FS.until(()=>objCard && objCard.tone==='fail', 2000, false)>=0;
  r.ends = FS.until(()=>wave>9, 20000, true)>=0;
  return r;`);

scenario('FS1 M10 Hammer B: the escort turns at 6 s (F48), then the Shivans, convoy out', 'm=10', `
  const r = {};
  FS.step(100);
  r.escortOurs = allies.some(a=>a.uid==='A1') && allies.some(a=>a.uid==='A2');
  FS.step(600);
  r.turnedHostile = enemies.some(e=>e.uid==='A1') && !allies.some(a=>a.uid==='A1');
  r.success = FS.until(()=>objCard && objCard.tone==='done', 40000, true)>=0;
  r.ends = FS.until(()=>wave>10, 20000, true)>=0;
  return r;`);

scenario('FS1 M11 Darkness and Light: Ramses taken, depot down - success', 'm=11', `
  const r = {};
  r.strand = currentEra==='fs1' && missionOrig===9;
  FS.step(300);
  const ra = byId('R1')[0];
  r.ramsesMarkedDisable = !!ra && missionMark(ra)==='DISABLE';
  r.preyFromTheStart = !!ra && !!ra.prey;
  for(const sb of ra.subs) if(sb.id==='engines'||sb.id==='weapons'){ sb.hp = 0; sb.dead = true; }
  r.transportComes = FS.until(()=>evSeen('T1'), 800, false)>=0;
  r.markedProtect = missionMark(ra)==='PROTECT';
  r.taken = FS.until(()=>!!EV_TAKEN.R1, 20000, true)>=0;
  r.success = FS.until(()=>objCard && objCard.tone==='done', 30000, true, true)>=0;
  r.ends = FS.until(()=>wave>11, 20000, true, true)>=0;
  return r;`);

scenario('FS1 M11 Darkness and Light: the Ramses lost - partial success', 'm=11', `
  const r = {};
  FS.step(300);
  const ra = byId('R1')[0];
  eBullets.push({x:ra.x, y:ra.y, vx:0, vy:0, w:6, h:6, dmg:1e6, faction:'shivan', life:50});
  FS.step(3);
  r.lostToTheirFire = FS.until(()=>byId('R1').length===0, 4000, false)>=0 && !EV_TAKEN.R1;
  r.partial = FS.until(()=>objCard && objCard.tone==='part', 30000, true, true)>=0;
  r.ends = FS.until(()=>wave>11, 20000, true, true)>=0;
  return r;`);

scenario('FS1 M12 First Strike A: Athena, Taranis disabled - success', 'm=12', `
  const r = {};
  r.strand = currentEra==='fs1' && missionOrig===10 && player.ship==='boathena';
  r.mx50ForPhoenix = !!player.sb && player.sb.some(b=>b.key==='mx50') && !player.sb.some(b=>b.key==='phoenix');
  FS.step(300);
  const ta = byId('R1')[0];
  r.marked = missionMark(ta)==='DISABLE';
  for(const sb of ta.subs) if(sb.id==='engines'||sb.id==='weapons'){ sb.hp = 0; sb.dead = true; }
  r.success = FS.until(()=>objCard && objCard.tone==='done', 600, false)>=0;
  r.markGone = missionMark(ta)==='';
  r.ends = FS.until(()=>wave>12, 20000, true)>=0;
  return r;`);

scenario('FS1 M13 First Strike B: disabled from the start, the Halkins tows her', 'm=13', `
  const r = {};
  FS.step(100);
  const ta = byId('R1')[0];
  r.disabledFromTheStart = !!ta && ta.subs.filter(s=>s.id==='engines'||s.id==='weapons').every(s=>s.dead);
  r.halkinsComes = FS.until(()=>evSeen('H1'), 1000, false)>=0;
  r.basilisksSecondWaveWaits = (FS.until(()=>evSeen('B1'), 3000, false)>=0) && !evSeen('B2');
  r.taken = FS.until(()=>!!EV_TAKEN.R1, 20000, true)>=0;
  r.success = FS.until(()=>objCard && objCard.tone==='done', 400, false)>=0;
  r.ends = FS.until(()=>wave>13, 20000, true)>=0;
  return r;`);

scenario('FS1 M13 First Strike B: the Halkins lost - failed', 'm=13', `
  const r = {};
  r.halkinsComes = FS.until(()=>byId('H1').length>0 && !(byId('H1')[0].warp>0), 2000, false)>=0;
  byId('H1')[0].hp = 0;
  r.failed = FS.until(()=>objCard && objCard.tone==='fail', 3000, false)>=0;
  r.ends = FS.until(()=>wave>13, 20000, true)>=0;
  return r;`);

// Silvio (v253): a ship the mission wants something done to wears pulsing
// brackets in her own colour; the word shows under them only while she is
// the target or the pointer is on her - as with a subsystem's name.
scenario('Mission mark: pulsing brackets, the word under them when targeted or pointed at', 'm=12', `
  const r = {};
  FS.step(300);
  const ta = byId('R1')[0];
  const words = [];
  const mt = markText;
  markText = function(t, x, y, col, al, bl){ words.push({t, y, col}); return mt.apply(this, arguments); };
  TGT.e = null; MOUSE.scr = true; MOUSE.sx = 5; MOUSE.sy = H-5;
  words.length = 0; draw();
  r.noWordWhenNotLooked = !words.some(w=>w.t==='DISABLE');
  TGT.e = ta; TGT.sub = null;
  words.length = 0; draw();
  const w1 = words.find(w=>w.t==='DISABLE');
  r.wordWhenTargeted = !!w1;
  r.underTheShip = !!w1 && w1.y > w2sY(ta.y);
  r.inHerOwnColour = !!w1 && w1.col===OFF_COL.enemy;
  TGT.e = null; MOUSE.sx = w2sX(ta.x); MOUSE.sy = w2sY(ta.y);
  words.length = 0; draw();
  r.wordWhenPointedAt = words.some(w=>w.t==='DISABLE');
  markText = mt;
  return r;`);

// Silvio (v253): with a subsystem targeted, a missile's lock is taken on
// that subsystem and the round strikes it, not the middle of the hull.
scenario('Missiles go for the targeted subsystem: the lock and the strike', 'm=12', `
  const r = {};
  FS.step(300);
  const ta = byId('R1')[0];
  const eng = ta.subs.find(s=>s.id==='engines');
  TGT.e = ta; TGT.sub = eng;
  const p = tgtSubPos(ta, eng);
  // the nose on the subsystem, the middle of her off to one side
  player.x = p.x - 150; player.y = p.y; player.angle = 0; player.head = 0;
  // tgtTick is too tangled to drive here: checked at the source - the lock
  // cone is measured to the chosen subsystem's place
  const src = String(tgtTick);
  r.lockMeasuredOnTheSubsystem = src.indexOf('tgtSubPos(o, TGT.sub)') >= 0 && src.indexOf('tgtOff(lp.x, lp.y)') >= 0;
  // a round sent at the engines, landing on the far end of her hull
  const hp0 = eng.hp;
  const sp = subPos(ta, eng);
  const far = {x: ta.x + (sp.x > ta.x ? -1 : 1)*40, y: ta.y};
  pBullets.push({x:far.x, y:far.y, vx:0, vy:0, w:4, h:4, dmg:30, sec:true, type:'missile', target:ta, sub:eng, ally:false, wpn:'mx50', life:20});
  FS.step(2);
  r.strikesTheEngines = eng.hp < hp0 || eng.dead;
  return r;`);

// v253: the FS1 launch sounds and the corrected ones (Silvio).
scenario('FS1 sounds: every FS1 weapon its own launch sound, the right impacts', 'm=12', `
  const r = {};
  const want = {ml16:'L_light', dadv:'L_disrupter', avenger:'L_avenge', prom1:'L_flux', banshee:'L_banshee',
    mx50:'m_wasp', interceptor:'m_shrike', phoenix:'m_angel', dmissile:'m_mag', harbinger:'m_harbinger'};
  const wrong = [];
  for(const k in want){ const w = fs1Def(k); if(!w || w.snd!==want[k]) wrong.push(k + ':' + (w && w.snd)); }
  r.launchSounds = wrong.length===0 || wrong;
  r.everyKeyHasAFile = Object.values(want).every(k=>k in SND_FILES);
  r.clusterImpacts = fs1Def('synaptic').hitSnd==='clusterboom' && fs1Def('harbinger').hitSnd==='clusterboom';
  r.railgun = F3D_GUN_SND.Railgun==='L_mass' && ('L_mass' in SND_FILES);
  return r;`);

// v254: Silvio's findings in M7 to M13 (F45-F51).
scenario('FS1 M07 F45: half the Shivan fighters', 'm=7', `
  const r = {};
  const d = SCRIPT_WAVES[7];
  let n = 0;
  for(const u of d.u) if(u.c==='fi' && u.fac==='shivan') n += (u.size||1)*(u.n||1);
  r.atMostSeven = n <= 7;
  return r;`);
scenario('FS1 M08 F46: fired on, the Asmodeus 2 needs over a minute to the edge', 'm=8', `
  const r = {};
  FS.step(120);
  evFire({w:'fliehen', a:'F1+F2+F3'});
  FS.step(6000);
  r.notGoneIn60s = wave===8 && byId('F1').length===1 && !EV_LEFT.F1;
  r.goneInTheEnd = FS.until(()=>!!EV_LEFT.F1 || wave>8, 6000, true) >= 0;
  return r;`);
scenario('FS1 M09 F47: the convoy flies, the cargo rides at her depth', 'm=9', `
  const r = {};
  FS.step(300);
  const t1 = byId('T1')[0], k1 = byId('K1')[0];
  const x0 = t1.x;
  FS.step(1000);
  r.flies = t1.x > x0 + 20;
  r.facesItsWay = !t1.flip === (spriteFacing(t1.img) === 'right');
  r.cargoWithHer = Math.abs(k1.x - t1.x) < 80;
  r.cargoKnowsHer = typeof f3dCargoHost === 'function' && f3dCargoHost(k1) === t1;
  r.notOutYet = !EV_LEFT.T1;
  return r;`);
scenario('FS1 M11 F49: the Taranis further off, only her guns can go', 'm=11', `
  const r = {};
  FS.until(()=>byId('C1').length>0 && byId('C1')[0].warp<=0, 4000, true);
  const c = byId('C1')[0], ra = byId('R1')[0];
  r.farOff = !!c && !!ra && Math.abs(c.x - ra.x) > 230*FIELD_K;
  r.onlyGuns = !!c && !!c.subs && c.subs.length===1 && c.subs[0].id==='weapons';
  c.hp = 1; damageEnemy(c, 1e6, c.x, c.y, true);
  FS.step(30);
  r.hullHolds = !c.dead && c.hp > 0 && c.rollT == null;
  return r;`);
scenario('FS1 M12 F50: subsystem marks turn with the hull', 'm=12', `
  const r = {};
  FS.step(200);
  const t = byId('R1')[0], s = t.subs.find(x=>Math.abs(x.dx) > 0.2) || t.subs[0];
  const a = subPos(t, s).x - t.x;
  t.turnC = 0;
  const b = subPos(t, s).x - t.x;
  t.turnC = null;
  r.swings = Math.abs(b) < Math.abs(a)*0.2;
  return r;`);
scenario('FS1 M13 F53: the Chronos jumps in already facing the Taranis', 'm=13', `
  const r = {};
  FS.until(()=>byId('H1').length>0, 3000, true);
  const h = byId('H1')[0];
  const f0 = !!h.flip;
  FS.until(()=>h.warp<=0, 2000, false);
  FS.step(3);
  r.noSnap = !!h.flip === f0 && !h._face;
  r.facesLeft = (spriteFacing(h.img)==='right') === !!h.flip;
  return r;`);
scenario('FS1 M13 F51: the Halkins faces the Taranis way and rolls under her', 'm=13', `
  const r = {};
  FS.until(()=>byId('H1').length>0 && byId('H1')[0].warp<=0, 3000, true);
  const h = byId('H1')[0], t = byId('R1')[0];
  FS.until(()=>!!EV_DOCK.H1, 8000, true);
  r.docked = !!EV_DOCK.H1;
  r.sameWay = !!h && ((spriteFacing(h.img)==='right') !== !!h.flip) === ((spriteFacing(t.img)==='right') !== !!t.flip);
  r.rolled = !!h && h.rollC != null && h.rollC < -0.99;
  r.under = !!h && h.y > t.y;
  return r;`);

// ── v257: F57 - the primary link setting carries over between missions ──
scenario('FS1 v257: linked primaries stay linked into the next mission (F57)', 'm=1', `
  const r = {}, seen = [];
  wave = 0; nextWave(); FS.step(5);
  // Linked the way the player does it: the mode key until 'linked'.
  for(let k=0; k<3 && player.pMode!==2; k++) cyclePrimary(1);
  r.linkedAtStart = player.pMode === 2;
  let prevN = player.pb.length, ok = true;
  for(const m of [2,3,4,5,6,7,8]){
    wave = m-1; nextWave(); FS.step(5);
    seen.push(m + ':' + player.ship + '/' + player.pb.length + '/' + player.pMode);
    // Same number of primary banks (Silvio): the setting must be kept,
    // even when the mission hands over another hull with as many banks.
    if(player.pb.length === prevN && player.pb.length >= 2 && player.pMode !== 2) ok = false;
    prevN = player.pb.length;
  }
  r.modes = seen.join(' ');
  r.keptLinked = ok;
  return r;`);

// ── v257: F58 - the Theta freighters in M9 and M10 twice as fast ───────
for(const m of [9, 10]) scenario('FS1 M' + m + ' v257: the Theta freighters move at twice the old pace (F58)', 'm=' + m, `
  const r = {};
  FS.until(()=>byId('T1').length>0 && !(byId('T1')[0].warp>0), 5000, true);
  const t = byId('T1')[0];
  r.pace = t ? +(t.crossing / FIELD_K).toFixed(3) : -1;
  r.doubled = !!t && t.crossing >= 0.08 * FIELD_K - 1e-9;
  return r;`);

// ── v257: FS1 M14 Tombaugh - the Lucifer ambush (Silvio, 22.10.2026) ────
scenario('FS1 M14 v257 Tombaugh: dock, two waves, Lucifer takes all six, jumps out, the end', 'm=14', `
  const r = {}, order = [], born = {};
  const big = ['R1','H1','F1','F2','O1','ST'];
  FS.step(200);
  r.allThere = ['R1','H1','F1','F2','ST'].every(id=>byId(id).length===1);
  FS.until(()=>!!EV_DOCK.T1, 3000, false);
  r.docked = !!EV_DOCK.T1;
  FS.step(120);
  r.stillDocked = byId('T1').length===1 && !(byId('T1')[0].crossing);
  FS.until(()=>evSeen('E1'), 1000, false);
  FS.killId('E1'); FS.step(60);
  FS.until(()=>evSeen('E2') && byId('E2').some(e=>!(e.warp>0)), 2500, false);
  r.wave2 = byId('E2').length>0;
  FS.until(()=>evSeen('B2'), 600, false);
  FS.killId('E2'); FS.killId('B2');
  FS.until(()=>byId('L1').length>0, 600, false);
  FS.step(30);
  r.lucifer = byId('L1').length===1;
  const t = byId('T1')[0];
  r.castOff = !!t && t.crossing < 0;
  const t0 = runTime;
  let n = 0;
  while(n < 60*360 && (byId('L1').length>0 || wave<=14)){
    FS.step(60); n += 60;
    for(const id of big) if(evSeen(id) && byId(id).length===0 && order.indexOf(id)<0) order.push(id);
    if(byId('L1').length===0 && order.length===6) break;
  }
  r.order = order.join(' ');
  r.seconds = Math.round(n/60);
  r.allSix = order.length===6;
  r.orionLateStationLast = order[order.length-1]==='ST' && order.indexOf('O1')>=3;
  r.luciferGone = byId('L1').length===0;
  r.transportOut = !!EV_LEFT.T1;
  FS.step(600);
  r.missionOver = wave>14 || GS!=='playing' || waveOver;
  return r;`);

scenario('FS1 M14 v257 Tombaugh: transport lost - goal failed, still ends; Shivan reinforcements', 'm=14', `
  const r = {}, hulls = {};
  FS.until(()=>!!EV_DOCK.T1, 3000, false);
  for(const a of allies) if(a.uid==='T1') a.hp = 0;
  FS.step(60);
  r.transportDead = byId('T1').length===0;
  let n = 0;
  while(n < 60*480 && wave<=14 && !waveOver){
    FS.step(60); n += 60;
    for(const e of enemies) if(e.type==='fighter'||e.type==='bomber') hulls[e.img] = 1;
  }
  r.hulls = Object.keys(hulls).sort().join(' ');
  // FS1 Shivan small craft only - no Vasudan hulls of the Hammer of Light.
  // the FS1 Shivan pools themselves (ERA_POOLS), not a list of my own
  const sh = ERA_POOLS.fs1.sh_fighters.concat(ERA_POOLS.fs1.sh_bombers);
  r.onlyShivan = Object.keys(hulls).length>0 && Object.keys(hulls).every(h=>sh.indexOf(h)>=0);
  r.seconds = Math.round(n/60);
  r.ends = wave>14 || waveOver;
  return r;`);

// ── v258: Silvio's findings on Rain on Ribos IV (F59 to F62, F64 to F67, F69, F72) ──
scenario('FS1 M14 v258 Ribos IV: Taranis silent, era allies, Lucifer stop, shield, station, end pause', 'm=14', `
  const r = {}, small = {};
  const fire0 = eBullets.length;
  FS.step(200);
  r.name = (SCRIPT_WAVES[14]||{}).name;
  r.twoAvengers = (player.pb||[]).map(b=>b.key).join('+') === 'avenger+avenger';
  // F59: the Taranis fires nothing - count what she puts into the field
  let taranisShots = 0;
  const R1 = byId('R1')[0];
  const seen = new Set();
  const look = function(){
    for(const a of allies) if(a.small && !a.dead) small[a.img] = 1;
  };
  // Every shot she makes goes through allyFire(): count what it adds.
  const _af = allyFire;
  window.allyFire = function(a){ const n0 = pBullets.length; _af(a); if(a===R1 && pBullets.length>n0) taranisShots += pBullets.length-n0; };
  FS.until(()=>!!EV_DOCK.T1, 3000, false);
  FS.until(()=>evSeen('E1'), 1000, false);
  for(let k=0;k<20;k++){ FS.step(30); look(); }
  r.taranisShots = taranisShots;
  r.taranisSilent = !!R1 && taranisShots===0;
  FS.killId('E1'); FS.step(60);
  FS.until(()=>evSeen('E2') && evSeen('B2'), 2500, false);
  FS.until(()=>{ FS.killId('E2'); FS.killId('B2'); return byId('L1').length>0; }, 3000, false);
  const L = byId('L1')[0];
  FS.until(()=>!(L.warp>0), 1200, false);
  r.inAt = Math.round(L.x/FIELD_K);
  FS.step(60*20); look();
  r.stopAt = Math.round(L.x/FIELD_K);
  r.stopsRight = r.stopAt >= 660 && r.stopAt <= 720 && r.inAt > r.stopAt;
  // F66: lockable, a hit flares the shield, nothing gets through
  const hp0 = L.hp;
  damageEnemy(L, 50, L.x + 7, L.y + 3, true, 'bolt', 'gun');
  r.lockable = canLockOn(L);
  // the newest flare is this hit (the list holds 15; since v259 the
  // allies keep it full, so its length says nothing)
  const lf = (L.shieldFlares||[])[(L.shieldFlares||[]).length-1];
  r.flares = !!lf && lf.life === lf.ml && Math.abs(lf.lx - 7) < 0.01 && Math.abs(lf.ly - 3) < 0.01;
  r.noDamage = L.hp === hp0;
  // F65: her reactors are not drawn - count the calls during one frame.
  let rc = 0, drew = false; const _dr = drawReactors;
  window.drawReactors = function(e){ if(e===L) rc++; };
  const _ls = drawLuciShield; window.drawLuciShield = function(e){ if(e===L) drew = true; return _ls(e); };
  try{ draw(); }catch(eD){}
  window.drawReactors = _dr; window.drawLuciShield = _ls;
  r.shieldDrawn = drew;
  r.reactorsHidden = drew && rc===0;
  const order = []; let stRoll = null, lGoneAt = -1, overAt = -1, n = 0;
  while(n < 60*420){
    FS.step(30); n += 30; look();
    for(const id of ['R1','H1','F1','F2','O1','ST']) if(evSeen(id) && byId(id).length===0 && order.indexOf(id)<0) order.push(id);
    const st = byId('ST')[0];
    if(st && st.rollT!=null && !stRoll) stRoll = {spin: st.rspinTo, vx: st.rvx, vy: st.rvy};
    if(lGoneAt<0 && byId('L1').length===0) lGoneAt = n;
    if(lGoneAt>=0 && overAt<0 && (waveOver || wave>14)) overAt = n;
    if(overAt>=0) break;
  }
  r.order = order.join(' ');
  r.orionLateStationLast = order.length===6 && order[5]==='ST' && order.indexOf('O1')>=3;
  r.stationStill = !!stRoll && stRoll.spin===0 && stRoll.vx===0 && stRoll.vy===0;
  r.pause = ((overAt - lGoneAt)/60).toFixed(1);
  r.pauseFive = overAt>0 && lGoneAt>0 && (overAt - lGoneAt) >= 60*4.5;
  r.allySmall = Object.keys(small).sort().join(' ');
  r.allyEraOk = Object.keys(small).length>0 && Object.keys(small).every(h=>['fiapollo','fivalyrie','boathena'].indexOf(h)>=0);
  return r;`);

// ── v258: F63/F70 - beam ends and hull effects stay on the hull as the view moves ──
scenario('FS1 M14 v258: beam end and hull fire stay on the hull when the camera moves (F63, F70)', 'm=14', `
  const r = {};
  FS.until(()=>evSeen('E1'), 1000, false);
  FS.until(()=>{ FS.killId('E1'); FS.killId('E2'); FS.killId('B2'); return byId('L1').length>0; }, 6000, false);
  const L = byId('L1')[0];
  FS.until(()=>L.beams && L.beams.some(b=>b.state==='firing'), 3000, false);
  const b = L.beams.find(b=>b.state==='firing');
  r.anchored = !!(b && b.anc);
  // No models here, so nothing is drawn sunk: give every capital hull the
  // depth a model would have, as the game does in the browser.
  window.f3dMidZ = function(o){ return (o && (o.type==='cruiser'||o.type==='corvette'||o.type==='destroyer'||o.type==='boss'||o.type==='station')) ? -300*FIELD_K : 0; };
  if(b && b.anc){
    const o = b.anc.o, q = beamAncPt(b);
    const cx0 = CAM.x, cy0 = CAM.y, ok = [];
    for(const d of [[0,0],[900,0],[-900,400],[0,-700]]){
      CAM.x = cx0 + d[0]; CAM.y = cy0 + d[1];
      o._hvFc = null;
      const qd = hullPt(o, q.x, q.y);
      ok.push(onHullAt(o, qd.x, qd.y));
    }
    CAM.x = cx0; CAM.y = cy0;
    r.endOnHull = ok.join(',');
    r.endAlwaysOnHull = ok.every(x=>x);
  }
  // a blast spawned on a capital hull keeps its place on her drawing
  const e = byId('O1')[0] || byId('ST')[0];
  const z = f3dMidZ(e);
  r.depth = Math.round(z);
  const p0 = hullPt(e, e.x+40, e.y+10);
  const h = hullFxBegin(e); spawnFireball(p0.x, p0.y, 10, 300); hullFxEnd(h);
  const fx = (typeof FX_ANIMS!=='undefined' && FX_ANIMS.length && FX_ANIMS[FX_ANIMS.length-1].hz!=null) ? FX_ANIMS[FX_ANIMS.length-1] : PARTS[PARTS.length-1];
  const cx0 = CAM.x, cy0 = CAM.y, off = [];
  for(const d of [[0,0],[900,0],[-900,400]]){
    CAM.x = cx0 + d[0]; CAM.y = cy0 + d[1]; e._hvFc = null;
    hullFxView(true);
    const want = hullPt(e, e.x+40, e.y+10);
    off.push(Math.round(Math.hypot(fx.x-want.x, fx.y-want.y)));
    hullFxView(false);
  }
  CAM.x = cx0; CAM.y = cy0;
  r.blastOff = off.join(',');
  r.blastStays = z < 0 && off.every(v=>v<=1);
  return r;`);

// ── v258: F68 - the vortex disc stands at the depth of the ship going through ──
scenario('FS1 M14 v258: the vortex is drawn at the depth of her hull (F68)', 'm=14', `
  const r = {}, got = [];
  window.f3dMidZ = function(o){ return (o && o.type==='destroyer') ? -1234 : 0; };
  window.f3dWarp = function(){ got.push(arguments[9]); return true; };
  const e = allies.find(a=>a.type==='destroyer') || {type:'destroyer', x:500, y:500};
  FS_PORTALS.push({e:e, px:e.x, py:e.y, fx:1, fy:0, WS:200, mW:100, t0:fc, closeT:-1});
  drawFsPortals();
  r.depthIn = got[0];
  r.atHerDepth = got[0] === -1234;
  window.f3dMidZ = function(){ return 0; };   // she is through: no model drawn any more
  got.length = 0; drawFsPortals();
  r.depthKept = got[0];
  r.keptAfter = got[0] === -1234;
  return r;`);

// ── v259: F74/F75 - allied shots flare the Lucifer's shield; she is on the radar ──
scenario('FS1 M14 v259: allied shots strike the Lucifer shield, she is on the radar (F74, F75)', 'm=14', `
  const r = {};
  FS.until(()=>evSeen('E1'), 1000, false);
  FS.until(()=>{ FS.killId('E1'); FS.killId('E2'); FS.killId('B2'); return byId('L1').length>0; }, 6000, false);
  const L = byId('L1')[0]; let allyHits = 0;
  const _d = damageEnemy;
  window.damageEnemy = function(e, dmg, hx, hy, fp){ if(e===L && !fp) allyHits++; return _d.apply(this, arguments); };
  const hp0 = L.hp, fl = [];
  for(let k=0;k<60*40;k+=10){ FS.step(10); if((L.shieldFlares||[]).length) fl.push(1); }
  window.damageEnemy = _d;
  r.allyHits = allyHits;
  r.alliesStrikeHer = allyHits > 0;
  r.flared = fl.length > 0;
  r.noDamage = L.hp === hp0;
  let onRadar = false; const _ri = radarIconOf;
  window.radarIconOf = function(e){ if(e===L) onRadar = true; return _ri(e); };
  try{ drawBarRadar(0, 0, 200, 60); }catch(eR){}
  window.radarIconOf = _ri;
  r.onRadar = onRadar;
  return r;`);

// ── v259: F76 - beams in 3D, tested against the hulls in the shared depth ──
// Box models stand in for the real ones (the cloud has none); the beam is
// read back from the 3D picture: hidden where a hull lies above it, seen
// where it lies above the hull, and between two ships the top one decides.
scenario('v259: 3D beams hidden by hulls above them, seen over hulls below (F76)', '', `
  const r = {};
  r.gl = !!f3dInit();
  if(!r.gl) return r;
  const gl = F3D.gl;
  // a box, 2 long (z, model forward), 0.3 deep (x), 0.2 high (y)
  const box = function(){
    const V = [], N = [], T = [], I = [];
    const hx = 0.15, hy = 0.1, hz = 1.0;
    const faces = [[[1,0,0],[0,0,1],[0,1,0]],[[-1,0,0],[0,0,-1],[0,1,0]],[[0,1,0],[1,0,0],[0,0,1]],[[0,-1,0],[1,0,0],[0,0,-1]],[[0,0,1],[-1,0,0],[0,1,0]],[[0,0,-1],[1,0,0],[0,1,0]]];
    for(const f of faces){
      const n = f[0], u = f[1], v = f[2], b0 = V.length/3;
      for(const [a, c] of [[-1,-1],[1,-1],[1,1],[-1,1]]){
        const x = n[0]*hx + u[0]*a*hx + v[0]*c*hx, y = n[1]*hy + u[1]*a*hy + v[1]*c*hy, z = n[2]*hz + u[2]*a*hz + v[2]*c*hz;
        V.push(Math.round(Math.max(-1,Math.min(1,(n[0]?n[0]*hx:(u[0]*a+v[0]*c)*hx)))*32767), Math.round(Math.max(-1,Math.min(1,(n[1]?n[1]*hy:(u[1]*a+v[1]*c)*hy)))*32767), Math.round(Math.max(-1,Math.min(1,(n[2]?n[2]*hz:(u[2]*a+v[2]*c)*hz)))*32767));
        N.push(n[0]*127, n[1]*127, n[2]*127, 0); T.push(0,0);
      }
      // both windings: the test does not depend on which side faces out
      I.push(b0, b0+1, b0+2, b0, b0+2, b0+3, b0, b0+2, b0+1, b0, b0+3, b0+2);
    }
    const pos = new Int16Array(V), nrm = new Int8Array(N), uv = new Uint16Array(T), idx = new Uint16Array(I);
    const mk = function(tg, a){ const bf = gl.createBuffer(); gl.bindBuffer(tg, bf); gl.bufferData(tg, a, gl.STATIC_DRAW); return bf; };
    return {state:'ready', tex:{}, head:{size:[0.3,0.2,2], ext:1, nodes:null},
      parts:[{kind:'flat', tex:'', n:idx.length, big:false, node:0, pos:mk(gl.ARRAY_BUFFER,pos), nrm:mk(gl.ARRAY_BUFFER,nrm), uv:mk(gl.ARRAY_BUFFER,uv), idx:mk(gl.ELEMENT_ARRAY_BUFFER,idx)}],
      cpu:[{pos:pos, idx:idx}]};
  };
  const L = box();
  const mkShip = function(x, y, w){ return {img:'deorionright', x:x, y:y, sc:w/(IMGS.deorionright?IMGS.deorionright.width:100), flip:false, ang:0, type:'destroyer', faction:'terran'}; };
  CAM.x = MW/2; CAM.y = (HUD_H+MH)/2; CAM.z = CAM_BASE_Z;
  const X = mkShip(MW/2 - 300, CAM.y, 1000), Y = mkShip(MW/2 + 100, CAM.y + 60, 1000);
  const cam = f3dVP();
  const px = function(P){
    const m = cam.vp, c = [0,0,0,0];
    for(let i=0;i<4;i++) c[i] = m[i]*P[0] + m[4+i]*P[1] + m[8+i]*P[2] + m[12+i];
    return [Math.round((c[0]/c[3]*0.5+0.5)*F3D.can.width), Math.round((c[1]/c[3]*0.5+0.5)*F3D.can.height)];
  };
  const read = function(P){ const q = px(P), o = new Uint8Array(4); gl.readPixels(q[0], q[1], 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, o); return Array.from(o); };
  // one beam along y=CAM.y, at depth z, across both boxes
  // a point counts as lit by the beam when it is clearly brighter than the
  // same picture without it
  const pts = function(z){ return {open:[MW/2 - 950, -(CAM.y+30), z], onX:[MW/2 - 650, -(CAM.y+30), z], onY:[MW/2 + 450, -(CAM.y+30), z]}; };
  const shot = function(z, withBeam){
    const e = {faction:'shivan', beams:[]}, b = {large:true, state:'firing', anc:{o:X}};
    window.f3dBeam3D = function(){ return true; };
    window.f3dBeamEnds = function(){ return {S:[MW/2 - 1600, -(CAM.y+30), z], T:[MW/2 + 1400, -(CAM.y+30), z]}; };
    F3D_BEAMS.length = 0; if(withBeam) F3D_BEAMS.push({e:e, b:b}); F3D_BEAM_BG = false;
    f3dRender([{e:X, L:L, x:X.x, y:X.y, a:1, clip:null}, {e:Y, L:L, x:Y.x, y:Y.y, a:1, clip:null}], false, true);
    const P = pts(z), o = {};
    for(const k in P){ const c = read(P[k]); o[k] = c[0] + c[1] + c[2]; }
    return o;
  };
  const run = function(z){
    const a = shot(z, false), b = shot(z, true), o = {};
    for(const k in a) o[k] = (b[k] - a[k]) > 60;
    o.raw = JSON.stringify([a, b]);
    return o;
  };
  const deep = run(-0.9*1000*0.15);       // well inside the hulls: under their top
  const high = run(40);                   // above the plane: over every hull
  r.deepRaw = deep.raw; r.highRaw = high.raw; delete deep.raw; delete high.raw;
  r.deep = JSON.stringify(deep); r.high = JSON.stringify(high);
  r.err = String(F3D.err||'');
  // the third ship: X lies 300 deeper than Y. A beam between their tops
  // is seen over X alone and hidden where Y lies over X - Y is on top there.
  {
    const MX = f3dMat(X, X.x, X.y, L); MX[14] -= 300;
    const z = -120;
    const P = {xOnly:[MW/2 - 650, -(CAM.y+30), z], both:[MW/2 - 200, -(CAM.y+30), z]};
    const one = function(withBeam){
      window.f3dBeamEnds = function(){ return {S:[MW/2 - 1600, -(CAM.y+30), z], T:[MW/2 + 1400, -(CAM.y+30), z]}; };
      F3D_BEAMS.length = 0; if(withBeam) F3D_BEAMS.push({e:{faction:'shivan'}, b:{large:true, state:'firing', anc:{o:X}}}); F3D_BEAM_BG = false;
      f3dRender([{e:X, L:L, x:X.x, y:X.y, a:1, clip:null, M:MX}, {e:Y, L:L, x:Y.x, y:Y.y, a:1, clip:null}], false, true);
      const o = {}; for(const k in P){ const c = read(P[k]); o[k] = c[0]+c[1]+c[2]; } return o;
    };
    const a = one(false), b = one(true);
    r.third = JSON.stringify([a, b]);
    r.seenOverDeeperShip = (b.xOnly - a.xOnly) > 60;
    r.hiddenWhereUpperShipLies = (b.both - a.both) <= 20;
  }
  // where a beam from the left towards her middle meets her: on her surface
  {
    const M = f3dMat(X, X.x, X.y, L), mid = [X.x, -X.y, M[14]];
    const loc = f3dRayHitLocal(L, M, [X.x - 2000, -X.y, 0], mid);
    r.surf = loc ? loc.map(v=>v.toFixed(3)).join(',') : 'none';
    r.onSurface = !!loc && Math.abs(Math.max(Math.abs(loc[0])/0.15, Math.abs(loc[1])/0.1, Math.abs(loc[2])/1.0) - 1) < 0.01;
    r.stencil = !!F3D.stencil;
  }
  r.openSpaceShown = deep.open && high.open;
  r.hiddenUnderHull = !deep.onX && !deep.onY;
  r.shownOverHull = high.onX && high.onY;
  return r;`, true);

scenario('FS1 M14 v259: the whole picture with 3D beams runs (box models) (F76)', 'm=14', `
  const r = {};
  r.gl = !!f3dInit();
  if(!r.gl) return r;
  const gl = F3D.gl;
  const mkL = function(){
    const V = [], I = [], hx = 0.15, hy = 0.1, hz = 1.0;
    for(const sx of [-1,1]) for(const sy of [-1,1]) for(const sz of [-1,1]) V.push(Math.round(sx*hx*32767), Math.round(sy*hy*32767), Math.round(sz*hz*32767));
    const F = [[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]];
    for(const f of F) I.push(f[0],f[1],f[2], f[0],f[2],f[3], f[0],f[2],f[1], f[0],f[3],f[2]);
    const pos = new Int16Array(V), idx = new Uint16Array(I), nrm = new Int8Array(32), uv = new Uint16Array(16);
    const mk = function(tg, a){ const bf = gl.createBuffer(); gl.bindBuffer(tg, bf); gl.bufferData(tg, a, gl.STATIC_DRAW); return bf; };
    return {state:'ready', tex:{}, head:{size:[0.3,0.2,2], ext:1, nodes:null},
      parts:[{kind:'flat', tex:'', n:idx.length, big:false, node:0, pos:mk(gl.ARRAY_BUFFER,pos), nrm:mk(gl.ARRAY_BUFFER,nrm), uv:mk(gl.ARRAY_BUFFER,uv), idx:mk(gl.ELEMENT_ARRAY_BUFFER,idx)}],
      cpu:[{pos:pos, idx:idx}]};
  };
  for(const k of ['sdlucifer','deorionright','crcain','scfaustus','inarcadia']) if(F3D_KEYS.indexOf(k)>=0){ const L = mkL(); F3D.models[k] = {lo:L, full:L}; }
  FS.until(()=>evSeen('E1'), 1000, false);
  FS.until(()=>{ FS.killId('E1'); FS.killId('E2'); FS.killId('B2'); return byId('L1').length>0; }, 6000, false);
  const L1 = byId('L1')[0];
  let frames = 0, beams3d = 0, errs = [], vis = 0, flat = 0;
  for(let k=0;k<60*30;k+=5){
    FS.step(5);
    try{ draw(); frames++; }catch(eD){ errs.push(String(eD.message||eD)); }
    beams3d += F3D_BEAMS.length;
    for(const b of (L1.beams||[])) if(b.state==='firing'){ if(b.anc && b.anc.vis) vis++; if(!f3dBeam3D(L1, b)) flat++; }
  }
  r.frames = frames;
  r.errors = errs.slice(0,3).join(' | ');
  r.noErrors = errs.length===0 && !F3D.err;
  r.f3dErr = String(F3D.err||'');
  r.beams3d = beams3d;
  r.beamsIn3D = beams3d > 0;
  r.hitOnSurface = vis > 0;
  r.flatWhileFiring = flat;
  return r;`);

// ── v260: F78 beam exit, F77 smoke on the surface, F76 step 3 rounds from the turret ──
scenario('FS1 M14 v260: beam exits with its flame, smoke on her surface, rounds rise from the turret (F76, F77, F78)', 'm=14', `
  const r = {};
  r.gl = !!f3dInit();
  if(!r.gl) return r;
  const gl = F3D.gl;
  const mkL = function(){
    const V = [], I = [], hx = 0.15, hy = 0.1, hz = 1.0;
    for(const sx of [-1,1]) for(const sy of [-1,1]) for(const sz of [-1,1]) V.push(Math.round(sx*hx*32767), Math.round(sy*hy*32767), Math.round(sz*hz*32767));
    const F = [[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]];
    for(const f of F) I.push(f[0],f[1],f[2], f[0],f[2],f[3], f[0],f[2],f[1], f[0],f[3],f[2]);
    const pos = new Int16Array(V), idx = new Uint16Array(I), nrm = new Int8Array(32), uv = new Uint16Array(16);
    const mk = function(tg, a){ const bf = gl.createBuffer(); gl.bindBuffer(tg, bf); gl.bufferData(tg, a, gl.STATIC_DRAW); return bf; };
    return {state:'ready', tex:{}, head:{size:[0.3,0.2,2], ext:1, nodes:null},
      parts:[{kind:'flat', tex:'', n:idx.length, big:false, node:0, pos:mk(gl.ARRAY_BUFFER,pos), nrm:mk(gl.ARRAY_BUFFER,nrm), uv:mk(gl.ARRAY_BUFFER,uv), idx:mk(gl.ELEMENT_ARRAY_BUFFER,idx)}],
      cpu:[{pos:pos, idx:idx}]};
  };
  for(const k of ['sdlucifer','deorionright','crcain','scfaustus','inarcadia']) if(F3D_KEYS.indexOf(k)>=0){ const L = mkL(); F3D.models[k] = {lo:L, full:L}; }
  FS.until(()=>evSeen('E1'), 1000, false);
  // F76 step 3: a round from a capital turret starts deep and rises
  let rounds = 0, risen = 0, startOk = 0;
  for(let k=0;k<60*12;k+=5){
    FS.step(5);
    try{ draw(); }catch(eD){}
    for(const L of [pBullets, eBullets]) for(const b of L){
      if(!(b.hz0 < 0) || b._seen) continue;
      b._seen = 1; rounds++;
    }
  }
  r.rounds = rounds;
  r.roundsFromDepth = rounds > 0;
  // one round: drawn deep at first, in the plane once it has risen
  { const b = {x:500, y:400, vx:1, vy:0, hz0:-300, hidE:null}; pBullets.push(b);
    shotsView(true); const d0 = Math.hypot(b.x-500, b.y-400); shotsView(false);
    const fc0 = fc; fc += SHOT_RISE + 1; shotsView(true); const d1 = Math.hypot(b.x-500, b.y-400); shotsView(false); fc = fc0;
    pBullets.splice(pBullets.indexOf(b), 1);
    r.drawnDeepFirst = d0 > 0.5; r.inPlaneAfterRise = d1 < 0.01; }
  // F78 and F77 against the Lucifer's beams on the boxes
  FS.until(()=>{ FS.killId('E1'); FS.killId('E2'); FS.killId('B2'); return byId('L1').length>0; }, 6000, false);
  const L1 = byId('L1')[0];
  let exits = 0, exitFlames = 0, beyond = 0;
  const _bi = beamImpact;
  window.beamImpact = function(o, mx, my, ang, large, tr){ if(tr && (tr.exit || tr.exitVis)) exits++; if(tr && tr.exitVis) exitFlames++; return _bi.apply(this, arguments); };
  for(let k=0;k<60*30;k+=5){
    FS.step(5);
    try{ draw(); }catch(eD){}
    for(const b of (L1.beams||[])) if(b.anc && b.anc._g3){ const g = b.anc._g3;
      if(Math.hypot(g.F[0]-g.X[0], g.F[1]-g.X[1]) > 50) beyond++; }
  }
  window.beamImpact = _bi;
  r.exits = exits; r.exitFlames = exitFlames;
  r.beamExits = exits > 0;
  r.exitFlameOn3D = exitFlames > 0;
  r.runsOnBeyond = beyond > 0;
  // F77: smoke from a tear on her surface, not from her middle
  const o = byId('O1')[0] || byId('ST')[0];
  if(o){
    const D = dmgState(o);
    o.hp = Math.max(1, o.maxHp*0.4);
    D.gashes.push({u:0.1, v:0, n:{x:0, y:-1}, L:0.1, Wd:0.05, t0:fc-999, jetP:3, jetPh:0, vent:true, sd:3, thr:-1});
    const n0 = PARTS.length;
    for(let k=0;k<40;k++){ fc++; dmgEmit(o); }
    const mine = PARTS.slice(n0).filter(p=>p.type==='dsmk' || p.type==='dvap' || p.type==='dfl');
    const mid = f3dMidZ(o);
    const S3 = dmgSurf(o, 0.1, 0, null);
    r.surfZ = S3 ? Math.round(S3.z) : 'none'; r.midZ = Math.round(mid);
    r.smoke = mine.length;
    r.smokeOnSurface = mine.length > 0 && !!S3 && mine.every(p=>p.hz!=null && Math.abs(p.hz - S3.z) < 1) && Math.abs(S3.z - mid) > 20;
  }
  r.f3dErr = String(F3D.err||'');
  return r;`);

// ── v261: F79/F80/F81 - entry and exit in 3D, hidden by hulls in front; the beam is straight ──
scenario('v261: beam entry hidden by a hull in front, exit spray beyond her, beam straight (F79, F80, F81)', '', `
  const r = {};
  r.gl = !!f3dInit();
  if(!r.gl) return r;
  const gl = F3D.gl;
  const mkL = function(){
    const V = [], I = [], hx = 0.15, hy = 0.1, hz = 1.0;
    for(const sx of [-1,1]) for(const sy of [-1,1]) for(const sz of [-1,1]) V.push(Math.round(sx*hx*32767), Math.round(sy*hy*32767), Math.round(sz*hz*32767));
    const F = [[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]];
    for(const f of F) I.push(f[0],f[1],f[2], f[0],f[2],f[3], f[0],f[2],f[1], f[0],f[3],f[2]);
    const pos = new Int16Array(V), idx = new Uint16Array(I), nrm = new Int8Array(32), uv = new Uint16Array(16);
    const mk = function(tg, a){ const bf = gl.createBuffer(); gl.bindBuffer(tg, bf); gl.bufferData(tg, a, gl.STATIC_DRAW); return bf; };
    return {state:'ready', tex:{}, head:{size:[0.3,0.2,2], ext:1, nodes:null},
      parts:[{kind:'flat', tex:'', n:idx.length, big:false, node:0, pos:mk(gl.ARRAY_BUFFER,pos), nrm:mk(gl.ARRAY_BUFFER,nrm), uv:mk(gl.ARRAY_BUFFER,uv), idx:mk(gl.ELEMENT_ARRAY_BUFFER,idx)}],
      cpu:[{pos:pos, idx:idx}]};
  };
  const L = mkL();
  const mkShip = function(x, y, w){ return {img:'deorionright', x:x, y:y, sc:w/(IMGS.deorionright?IMGS.deorionright.width:100), flip:false, ang:0, type:'destroyer', faction:'terran'}; };
  CAM.x = MW/2; CAM.y = (HUD_H+MH)/2; CAM.z = CAM_BASE_Z;
  const X = mkShip(MW/2 - 300, CAM.y, 1000), Y = mkShip(MW/2 + 100, CAM.y + 60, 1000);
  const cam = f3dVP();
  const px = function(P){
    const m = cam.vp, c = [0,0,0,0];
    for(let i=0;i<4;i++) c[i] = m[i]*P[0] + m[4+i]*P[1] + m[8+i]*P[2] + m[12+i];
    return [Math.round((c[0]/c[3]*0.5+0.5)*F3D.can.width), Math.round((c[1]/c[3]*0.5+0.5)*F3D.can.height)];
  };
  const lum = function(P){ const q = px(P), o = new Uint8Array(4); gl.readPixels(q[0], q[1], 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, o); return o[0]+o[1]+o[2]; };
  const sink = -1000*0.15;            // a box's middle (half its thickness down)
  // a beam whose entry is at T, leaving at Xp along d; no band (S = T), so
  // only the entry and exit are drawn
  const shot = function(T, Xp, d, withBeam, P){
    window.f3dBeam3D = function(){ return true; };
    window.f3dBeamEnds = function(){ return {S:T, T:T, X:Xp, F:Xp, d:d, hasExit:true}; };
    F3D_BEAMS.length = 0; if(withBeam) F3D_BEAMS.push({e:{faction:'shivan'}, b:{large:true, state:'firing', anc:{o:X}, _fxSeed:1}}); F3D_BEAM_BG = false;
    f3dRender([{e:X, L:L, x:X.x, y:X.y, a:1, clip:null}, {e:Y, L:L, x:Y.x, y:Y.y, a:1, clip:null}], false, true);
    return lum(P);
  };
  const lit = function(T, Xp, d, P){ return shot(T, Xp, d, true, P) - shot(T, Xp, d, false, P); };
  const yy = -(CAM.y + 30);
  // entry on the open top of X: seen
  const T1 = [MW/2 - 650, yy, 0];
  r.entryOpen = lit(T1, T1, [1,0,0], T1);
  // entry on X where Y lies over it: hidden
  const T2 = [MW/2 - 200, yy, 0];
  r.entryUnderOther = lit(T2, T2, [1,0,0], T2);
  // entry inside X, under her own top surface (an edge of her own in front): hidden
  const T3 = [MW/2 - 650, yy, sink*1.6];
  r.entryUnderOwn = lit(T3, T3, [1,0,0], T3);
  r.entrySeen = r.entryOpen > 60;
  r.entryHiddenByOther = r.entryUnderOther <= 20;
  r.entryHiddenByOwn = r.entryUnderOwn <= 20;
  // the exit: out of X's far end, on beyond her, at her middle depth
  const Xe = [X.x - 500, -(CAM.y - 30), sink], dl = [-1, 0, 0];
  const len = BEAM_EXIT_LEN.large*7.5*fxG()/(f3dEyeD()/(f3dEyeD() - sink));
  const Pj = [Xe[0] - len*0.35, Xe[1], Xe[2]];
  r.exitSprayBeyond = lit(Xe, Xe, dl, Pj);
  r.exitSpraySeen = r.exitSprayBeyond > 60;
  r.exitLen = Math.round(len);
  return r;`, true);

scenario('FS1 M14 v261: the 3D beam is one straight line, no flat fire on it (F81)', 'm=14', `
  const r = {};
  r.gl = !!f3dInit();
  if(!r.gl) return r;
  const gl = F3D.gl;
  const mkL = function(){
    const V = [], I = [], hx = 0.15, hy = 0.1, hz = 1.0;
    for(const sx of [-1,1]) for(const sy of [-1,1]) for(const sz of [-1,1]) V.push(Math.round(sx*hx*32767), Math.round(sy*hy*32767), Math.round(sz*hz*32767));
    const F = [[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]];
    for(const f of F) I.push(f[0],f[1],f[2], f[0],f[2],f[3], f[0],f[2],f[1], f[0],f[3],f[2]);
    const pos = new Int16Array(V), idx = new Uint16Array(I), nrm = new Int8Array(32), uv = new Uint16Array(16);
    const mk = function(tg, a){ const bf = gl.createBuffer(); gl.bindBuffer(tg, bf); gl.bufferData(tg, a, gl.STATIC_DRAW); return bf; };
    return {state:'ready', tex:{}, head:{size:[0.3,0.2,2], ext:1, nodes:null},
      parts:[{kind:'flat', tex:'', n:idx.length, big:false, node:0, pos:mk(gl.ARRAY_BUFFER,pos), nrm:mk(gl.ARRAY_BUFFER,nrm), uv:mk(gl.ARRAY_BUFFER,uv), idx:mk(gl.ELEMENT_ARRAY_BUFFER,idx)}],
      cpu:[{pos:pos, idx:idx}]};
  };
  for(const k of ['sdlucifer','deorionright','crcain','scfaustus','inarcadia']) if(F3D_KEYS.indexOf(k)>=0){ const L = mkL(); F3D.models[k] = {lo:L, full:L}; }
  FS.until(()=>evSeen('E1'), 1000, false);
  FS.until(()=>{ FS.killId('E1'); FS.killId('E2'); FS.killId('B2'); return byId('L1').length>0; }, 6000, false);
  const L1 = byId('L1')[0];
  let worst = 0, seen = 0, exits = 0, flatFire = 0;
  const _sf = spawnFireball;
  for(let k=0;k<60*30;k+=5){
    FS.step(5);
    try{ draw(); }catch(eD){}
    for(const b of (L1.beams||[])) if(b.anc && b.anc._g3 && b.anc._g3f >= F3D_FRAME - 1){
      const g = b.anc._g3; seen++; if(g.hasExit) exits++;
      // T, X and F on the line from S along d
      for(const P of [g.T, g.X, g.F]){
        const v = [P[0]-g.S[0], P[1]-g.S[1], P[2]-g.S[2]], t = v[0]*g.d[0] + v[1]*g.d[1] + v[2]*g.d[2];
        const off = Math.hypot(v[0]-g.d[0]*t, v[1]-g.d[1]*t, v[2]-g.d[2]*t);
        worst = Math.max(worst, off);
      }
      // no flat fire at the entry of a 3D beam
      const n0 = PARTS.length, f0 = (typeof FX_ANIMS!=='undefined') ? FX_ANIMS.length : 0;
      const fcs = fc; fc = 2*Math.ceil(fc/2);
      beamImpactAt(b.anc.o, b.angle, true, {entry:beamAncPt(b), exit:null, vis:b.anc.vis, exitVis:b.anc.exitVis});
      fc = fcs;
      flatFire += (PARTS.length - n0) + (((typeof FX_ANIMS!=='undefined') ? FX_ANIMS.length : 0) - f0);
    }
  }
  r.beamsSeen = seen;
  r.withExit = exits;
  r.offLine = worst.toFixed(3);
  r.straight = seen > 0 && worst < 0.5;
  r.flatFire = flatFire;
  r.noFlatFire = seen > 0 && flatFire === 0;
  r.f3dErr = String(F3D.err||'');
  return r;`);

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
      res = await page.evaluate(HELPERS + `\nFS.fakeImages();` + (sc.noLaunch ? '' : ' launchGame();') + `\n(async function(){${sc.body}})()`);
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
