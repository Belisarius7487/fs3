// Ship switch simulation. Pulls the REAL functions out of the logic file and
// runs them against stand-ins for the world. Usage: node shipsim.js <logic.html>
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const src = html.match(/<script[^>]*>([\s\S]*)<\/script>/)[1];

function blockEnd(s, i){
  i = s.indexOf('{', i); let d = 0;
  for(; i < s.length; i++){
    const c = s[i];
    if(c==="'"||c==='"'||c==='`'){ const q=c; i++; while(i<s.length && s[i]!==q){ if(s[i]==='\\') i++; i++; } }
    else if(s.startsWith('//', i)) i = s.indexOf('\n', i);
    else if(s.startsWith('/*', i)) i = s.indexOf('*/', i) + 1;
    else if(c==='{') d++;
    else if(c==='}'){ d--; if(d===0) return i+1; }
  }
  throw new Error('no block end');
}
function fn(name){
  const i = src.indexOf('\nfunction '+name+'(');
  if(i<0) throw new Error('missing function '+name);
  return src.slice(i+1, blockEnd(src, i));
}
function between(startText){
  const i = src.indexOf(startText); if(i<0) throw new Error('missing '+startText);
  const j = src.indexOf('function', i);
  return src.slice(j, blockEnd(src, j));
}
const shipsDecl = src.match(/const PLAYER_SHIPS = \[[\s\S]*?\];/)[0];
const hullFacDecl = src.match(/const HULL_FAC = \{[\s\S]*?\};/)[0];
const names = ['hullClass','isBomberHull','shipStats','applyShip','tickShipUnlocks','shipSwapReady',
  'setShipMenu','toggleShipMenu','swapShip','drawSwapIcon','statPips','drawShipMenu','pointerConsumed',
  'resetPlayerShield','playerSc','setCallMenu',
  'hullFac','shipFac','hangarServes','isHangarShip','hangarFacs','colossusOnField','shipOffered'];
const keyHandler = between("document.addEventListener('keydown',function(ev){\n  if(GS!=='playing') return;");
const downStart = src.indexOf("CVS.addEventListener('mousedown',");
const mouseHandler = src.slice(src.indexOf('function', downStart), blockEnd(src, src.indexOf('function', downStart)));
const launch = fn('launchGame');

const ctxStub = new Proxy({}, {get:(t,k)=> k in t ? t[k] : ()=>{}, set:(t,k,v)=>{t[k]=v; return true;}});
const world = `
  const W=800,H=500,HUD_H=54, PLAYER_SPD_FIGHTER=3.2, PLAYER_SPD_BOMBER=2.4, PLAYER_TURN=0.14;
  let FS1_MODE=false, GS='playing', paused=false, callMenu=false, wave=1, score=0, allies=[], jump=false;
  let SUB_MSGS=[], MOUSE={x:0,y:0}, lives=3, player={x:100,y:200,hullMult:1};
  let eraOff=false, IMGS={}, isFiring=false, launched=0;
  const ctx=CTX, document={body:{classList:{add(){},remove(){}}}, getElementById(){return {style:{}};}};
  const window={};
  function inJump(){return jump;} function eraShieldsOff(){return eraOff;}
  function setSettings(){} function toggleFullscreen(){} function refineTicket(){} function callAlly(){}
  function allyReady(){return true;} function toggleCallMenu(){} function toGC(x,y){return {x:x,y:y};}
  let shipUnlocked=1, shipSwapWave=-1, shipMenu=false, gameOverAt=0;
  const ALLY_KEYS=[], ALLY_ORDER=[], ALLY_SPECIAL='x', ALLY_SPECIAL_KEY='Q';
  ${hullFacDecl}
  ${shipsDecl}
  ${names.map(fn).join('\n')}
  const onKey = ${keyHandler};
  const onDown = ${mouseHandler};
  return {
    get:(k)=>eval(k), set:(k,v)=>eval(k+'=v'), run:(code)=>eval(code)
  };`;
const W = new Function('CTX', world)(ctxStub);
let fails = 0;
function ok(label, cond){ console.log((cond?'  ok    ':'  FAIL  ')+label); if(!cond) fails++; }
const P = ()=>W.get('player');
const reset = ()=>{ W.run("GS='playing';paused=false;callMenu=false;shipMenu=false;wave=1;score=0;allies=[];jump=false;FS1_MODE=false;shipUnlocked=1;shipSwapWave=-1;SUB_MSGS=[];player={x:100,y:200,hullMult:1};applyShip(PLAYER_SHIPS[0].key)"); };
const destroyer = (o)=>Object.assign({img:'dehatshepsut', small:false, dead:false, warpOut:false}, o||{});

console.log('Start ship');
reset();
ok('starts in the Thoth', P().ship==='fitoth');
ok('Thoth stats 3.5 / 0.17 / 100 / 100 / 20 missiles', P().spd===3.5 && P().turn===0.17 && P().maxHp===100 && P().maxSh===100 && P().secMax===20 && P().secType==='missile');

console.log('Unlocks');
reset();
W.run("score=3999; tickShipUnlocks()"); ok('3999 points: nothing unlocked', W.get('shipUnlocked')===1);
W.run("score=4000; tickShipUnlocks()"); ok('4000 points: Horus unlocked, one message', W.get('shipUnlocked')===2 && W.get('SUB_MSGS').length===1 && /HORUS/.test(W.get('SUB_MSGS')[0].txt));
W.run("score=23000; tickShipUnlocks()"); ok('jump to 23000: Osiris, Serapis, Seth at once', W.get('shipUnlocked')===5 && W.get('SUB_MSGS').length===4);
W.run("score=999999; tickShipUnlocks()"); ok('never past the end of the list', W.get('shipUnlocked')===8);
W.run("tickShipUnlocks()"); ok('seven unlock messages in total, none repeated', W.get('SUB_MSGS').length===7);
reset(); W.run("FS1_MODE=true; score=99999; tickShipUnlocks()"); ok('FS1 mode: no unlocks', W.get('shipUnlocked')===1);
reset(); W.run("GS='gameover'; score=99999; tickShipUnlocks()"); ok('not outside play', W.get('shipUnlocked')===1);

console.log('When the switch is available');
const ready = (setup)=>{ reset(); W.run("shipUnlocked=3"); setup(); return W.run('shipSwapReady()'); };
ok('no destroyer: not ready', ready(()=>{})===false);
ok('allied Vasudan destroyer: ready', ready(()=>W.set('allies',[destroyer()]))===true);
ok('NTF hull (ntfdehecate) is Terran, no Terran hulls exist: not ready',
   ready(()=>W.set('allies',[destroyer({img:'ntfdehecate'})]))===false);
ok('cruiser only: not ready', ready(()=>W.set('allies',[destroyer({img:'crmentu'})]))===false);
ok('Colossus alone is a joint yard: ready',
   ready(()=>W.set('allies',[destroyer({img:'sdcolossus', colossus:true})]))===true);
ok('dead destroyer: not ready', ready(()=>W.set('allies',[destroyer({dead:true})]))===false);
ok('destroyer warping out: not ready', ready(()=>W.set('allies',[destroyer({warpOut:true})]))===false);
ok('only the start ship unlocked: not ready', ready(()=>{ W.set('allies',[destroyer()]); W.run('shipUnlocked=1'); })===false);
ok('during a jump: not ready', ready(()=>{ W.set('allies',[destroyer()]); W.run('jump=true'); })===false);
ok('FS1 mode: not ready', ready(()=>{ W.set('allies',[destroyer()]); W.run('FS1_MODE=true'); })===false);

console.log('Switching');
reset(); W.run("shipUnlocked=3; player.hp=12; player.sh=5; player.secAmmo=1"); W.set('allies',[destroyer()]);
W.run('toggleShipMenu()'); ok('button opens the menu and pauses', W.get('shipMenu')===true && W.get('paused')===true);
W.run("swapShip('fiserapis')"); ok('locked hull (Serapis) refused', P().ship==='fitoth' && W.get('shipMenu')===true);
W.run("swapShip('fitoth')"); ok('current hull refused', W.get('shipMenu')===true && W.get('shipSwapWave')===-1);
W.run("swapShip('boosiris')");
ok('Osiris taken: menu closed, unpaused', P().ship==='boosiris' && W.get('shipMenu')===false && W.get('paused')===false);
ok('Osiris stats 2.5 / 0.10 / 140 / 100 / 10 bombs', P().spd===2.5 && P().turn===0.10 && P().maxHp===140 && P().maxSh===100 && P().secMax===10 && P().secType==='bomb');
ok('refilled: hull 140, shields 100, 10 bombs', P().hp===140 && P().sh===100 && P().secAmmo===10);
ok('switch spent for this wave', W.run('shipSwapReady()')===false);
W.run('toggleShipMenu()'); ok('menu does not open again this wave', W.get('shipMenu')===false);
W.run('wave=2'); ok('next wave: available again', W.run('shipSwapReady()')===true);

console.log('Cycle scaling and shields');
reset(); W.run("player.hullMult=1.5; shipUnlocked=8"); W.set('allies',[destroyer()]);
W.run("toggleShipMenu(); swapShip('bosekhmet')"); ok('Sekhmet at cycle x1.5: hull 210', P().maxHp===210 && P().hp===210);
reset(); W.run("eraOff=true; shipUnlocked=2"); W.set('allies',[destroyer()]);
W.run("toggleShipMenu(); swapShip('fihorus')"); ok('era without shields: shields stay 0', P().sh===0 && P().maxSh===100);
W.run('eraOff=false');

console.log('Call menu and switch menu exclude each other');
reset(); W.run("shipUnlocked=2; callMenu=true; paused=true"); W.set('allies',[destroyer()]);
W.run('toggleShipMenu()'); ok('opening the switch closes the call menu', W.get('callMenu')===false && W.get('shipMenu')===true);

console.log('Menu drawing and taps');
reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer()]); W.run('toggleShipMenu(); drawShipMenu()');
const rects = W.run('window._shipRects');
ok('eight cells drawn', rects.length===8);
ok('menu fits on the 800x500 field', rects.every(r=>r.x>=0 && r.y>=0 && r.x+r.w<=800 && r.y+r.h<=500));
ok('only Horus and Osiris are tappable', rects.filter(r=>r.key).map(r=>r.key).join()==='fihorus,boosiris');
const locked = rects[5];
W.run(`pointerConsumed({x:${locked.x+5},y:${locked.y+5}})`); ok('tap on locked Bakha keeps the menu open', W.get('shipMenu')===true && P().ship==='fitoth');
const horus = rects[1];
W.run(`pointerConsumed({x:${horus.x+5},y:${horus.y+5}})`); ok('tap on Horus switches', P().ship==='fihorus' && W.get('shipMenu')===false);
reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
W.run('pointerConsumed({x:2,y:2})'); ok('tap outside closes without switching', W.get('shipMenu')===false && P().ship==='fitoth' && W.run('shipSwapReady()')===true);
W.run("window._shipBtnRect={x:695,y:4,w:22,h:20}; pointerConsumed({x:700,y:10})"); ok('tap on the bar button opens the menu', W.get('shipMenu')===true);

console.log('Keyboard');
const key = (code)=>W.run(`onKey({code:'${code}', preventDefault(){}})`);
reset(); W.run("shipUnlocked=4"); W.set('allies',[destroyer()]);
key('KeyV'); ok('V opens', W.get('shipMenu')===true);
key('Digit6'); ok('6 (locked Bakha) does nothing', W.get('shipMenu')===true && P().ship==='fitoth');
key('Digit4'); ok('4 takes the Serapis', P().ship==='fiserapis' && W.get('shipMenu')===false);
reset(); W.run("shipUnlocked=4"); W.set('allies',[destroyer()]); key('KeyV'); key('Escape');
ok('Escape closes', W.get('shipMenu')===false && W.get('paused')===false);
reset(); key('KeyV'); ok('V without a destroyer does nothing', W.get('shipMenu')===false);

console.log('Restart guard');
W.run("launchGame=function(){launched++}");
const down = ()=>W.run("onDown({button:0, clientX:400, clientY:300})");
W.run("GS='title'; launched=0"); down(); ok('tap on title starts at once', W.get('launched')===1);
W.run("GS='gameover'; gameOverAt=performance.now(); launched=0"); down(); ok('tap right after dying does not restart', W.get('launched')===0);
W.run("gameOverAt=performance.now()-2000"); down(); ok('tap after 2 s restarts', W.get('launched')===1);


console.log('Hangars by faction');
const colossus = (o)=>Object.assign({img:'sdcolossus', colossus:true, small:false, dead:false, warpOut:false}, o||{});
ok('hull faction comes from the key', W.run("hullFac('dehatshepsut')")==='vasudan'
   && W.run("hullFac('deorionright')")==='terran' && W.run("hullFac('sdcolossus')")==='gtva');
ok('a defected Hammer of Light Typhon still counts as Vasudan',
   ready(()=>W.set('allies',[destroyer({img:'detyphon', faction:'hol'})]))===true);
ok('a renegade Hatshepsut too',
   ready(()=>W.set('allies',[destroyer({img:'dehatshepsut', faction:'renegade'})]))===true);
ok('Terran Orion only: not ready', ready(()=>W.set('allies',[destroyer({img:'deorionright'})]))===false);
ok('Terran Hecate only: not ready', ready(()=>W.set('allies',[destroyer({img:'dehecate'})]))===false);
ok('Orion plus Typhon: ready, the lists add up',
   ready(()=>W.set('allies',[destroyer({img:'deorionright'}), destroyer({img:'detyphon'})]))===true);
ok('unknown capital hull: not ready', ready(()=>W.set('allies',[destroyer({img:'dedemon'})]))===false);

reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer({img:'deorionright'})]);
ok('Vasudan hull not offered by a Terran hangar', W.run("shipOffered('fihorus')")===false);
W.run("shipMenu=true; swapShip('fihorus')");
ok('and a forced switch is refused', P().ship==='fitoth' && W.get('shipSwapWave')===-1);
W.set('allies',[colossus()]);
ok('the Colossus offers the Vasudan hull', W.run("shipOffered('fihorus')")===true);

reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer({img:'deorionright'})]);
W.run('toggleShipMenu()'); ok('Terran hangar only: the menu stays shut', W.get('shipMenu')===false);
W.run("shipMenu=true; drawShipMenu()");
ok('no cell is tappable in that state', W.run('window._shipRects').every(r=>!r.key));

console.log('Colossus lifts the once per wave limit');
reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer()]);
W.run("toggleShipMenu(); swapShip('fihorus')");
ok('first switch of the wave refits', P().ship==='fihorus' && P().hp===80 && P().sh===100 && P().secAmmo===20);
ok('no Colossus: spent for this wave', W.run('shipSwapReady()')===false);
W.set('allies',[destroyer(), colossus()]);
ok('Colossus arrives: available again in the same wave', W.run('shipSwapReady()')===true);
W.run("player.hp=40; player.sh=50; player.secAmmo=10");
W.run("toggleShipMenu(); swapShip('boosiris')");
ok('second switch happens', P().ship==='boosiris');
ok('hull carries over as a fraction, 40/80 of 140 = 70', P().hp===70);
ok('shields carry over, 50/100 of 100 = 50', P().sh===50);
ok('ammo carries over, 10/20 of 10 bombs = 5', P().secAmmo===5);
ok('no refit: not full', P().hp<P().maxHp && P().secAmmo<P().secMax);

reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer(), colossus()]);
W.run("toggleShipMenu(); swapShip('fihorus')");
ok('with the Colossus there the first switch still refits', P().hp===80 && P().secAmmo===20);
W.run("player.hp=1");
W.run("toggleShipMenu(); swapShip('boosiris')");
ok('a nearly dead hull stays alive after carrying over', P().hp>=1 && P().hp<=3);

reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer(), colossus({dead:true})]);
W.run("toggleShipMenu(); swapShip('fihorus')");
ok('dead Colossus grants nothing', W.run('shipSwapReady()')===false);
reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer(), colossus({warpOut:true})]);
W.run("toggleShipMenu(); swapShip('fihorus')");
ok('Colossus warping out grants nothing', W.run('shipSwapReady()')===false);

reset(); W.run("shipUnlocked=3"); W.set('allies',[colossus()]);
W.run("toggleShipMenu(); swapShip('fihorus')"); W.run("player.hp=20");
W.run("toggleShipMenu(); swapShip('fitoth')");
ok('back onto the start hull at the Colossus, 20/80 of 100 = 25', P().ship==='fitoth' && P().hp===25);
W.run('wave=2');
ok('new wave with the Colossus still there: refits again', W.run('shipSwapReady()')===true);
W.run("toggleShipMenu(); swapShip('fihorus')"); ok('and it is a full hull', P().hp===80);

console.log('Support calls by faction');
ok('the Terran column is off in this cycle', src.includes("const ALLY_FAC_ON = {terran:false, vasudan:true, gtva:true};"));
ok('the call is gated inside callAlly, not only in the menu',
   /function callAlly\(id\)\{[\s\S]{0,400}allyFacOn\(cdef\.fac\)/.test(src));
ok('the menu no longer uses the fixed two column split', !src.includes('ALLY_TER_N?0:1'));
ok('the Colossus is a GTVA ship now', /colossus:\s*\{cls:'destroyer', fac:'gtva'/.test(src));

console.log('Bar button placement');
{
  const a = src.indexOf('// ── SHIP SWITCH BUTTON'), b = src.indexOf('// ── PAUSE BUTTON');
  const snip = src.slice(a, b);
  W.run("var H2=44; shipMenu=false; window._shipBtnRect=undefined; " + JSON.stringify(snip).slice(1,-1).replace(/\\n/g,'\n').replace(/\\'/g,"'").replace(/\\"/g,'"'));
  const r = W.run('window._shipBtnRect');
  ok('button sits between tickets (665) and gear (748)', r && r.x>665 && r.x+r.w<748);
  W.run("FS1_MODE=true; " + snip); ok('no button in FS1 mode', W.run('window._shipBtnRect')===null);
  W.run('FS1_MODE=false');
}
console.log('Cycle scaling keeps the hull');
ok('nextWave scales from the hull base, not from 100', src.includes('player.maxHp=Math.round((player.baseHp||100)*pm);'));
ok('respawn restores the full hull', src.includes('player.hp=player.maxHp;player.x=80;'));

console.log('\n' + (fails ? fails+' FAILED' : 'all passed'));
process.exit(fails?1:0);
