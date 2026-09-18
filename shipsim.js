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
const menuBgDecl = src.match(/const MENU_BG_ALPHA[\s\S]*?const MENU_BG_PAD\s*=\s*[\d.]+;/)[0];
const hangarDecl = src.match(/const HG_W[\s\S]*?\n\];/)[0];
const themesDecl = src.match(/const THEMES = \{[\s\S]*?\n\};/)[0];
const volleyDecl = src.match(/const VOLLEY_BASE[\s\S]*?const VOLLEY_PER_EXTRA\s*=\s*[\d.]+;/)[0];
const names = ['hullClass','isBomberHull','shipStats','applyShip','tickShipUnlocks','shipSwapReady',
  'setShipMenu','toggleShipMenu','swapShip','drawSwapIcon','statPips','drawShipMenu','pointerConsumed',
  'resetPlayerShield','playerSc','setCallMenu',
  'hullFac','shipFac','hangarServes','isHangarShip','hangarFacs','colossusOnField','shipOffered',
  'mountsFor','spriteFacing','drawHullBg','drawHullCell','volleyDmg','volleyTotal','primaryCount','syncPause',
  'hangarGroups','hangarLayout','drawMissileIcon','drawBombIcon','drawKeyChip',
  'hangarOrder','insidePanel',
  'thChamferPath','thPlate','thGlowPath','thBrackets','thScale','thFrame','thRGBA','thGloss','thCutGlint',
  'TH','thLabel','thValue','thBevel','thGlow','thPanel','thButton','thDivider','drawSwapIcon','UI','uiHLP','uiLabel','uiValue','uiCell','uiDialog'];
const keyHandler = between("document.addEventListener('keydown',function(ev){\n  if(GS!=='playing') return;");
const downStart = src.indexOf("CVS.addEventListener('mousedown',");
const mouseHandler = src.slice(src.indexOf('function', downStart), blockEnd(src, src.indexOf('function', downStart)));
const launch = fn('launchGame');

const CALLS = [];
const ctxStub = new Proxy({}, {
  get:(t,k)=> k in t ? t[k] : function(){
    CALLS.push({fn:String(k), args:[].slice.call(arguments)});
    // createLinearGradient has to hand back something with addColorStop.
    if(k==='createLinearGradient') return {addColorStop:function(){}};
  },
  set:(t,k,v)=>{ CALLS.push({fn:'set '+String(k), args:[v]}); t[k]=v; return true; }
});
// Helpers over the recorded drawing calls.
const CLR    = ()=>{ CALLS.length = 0; };
const draws  = ()=> CALLS.filter(c=>c.fn==='drawImage');
const clips  = ()=> CALLS.filter(c=>c.fn==='clip');
const alphas = ()=> CALLS.filter(c=>c.fn==='set globalAlpha').map(c=>c.args[0]);
// Every sprite has to sit inside a save/restore pair, otherwise its clip and
// its alpha leak into whatever is drawn next.
function balanced(){
  let d = 0, okAll = true;
  for(const c of CALLS){
    if(c.fn==='save') d++;
    else if(c.fn==='restore'){ d--; if(d<0) okAll=false; }
    else if((c.fn==='drawImage' || c.fn==='clip') && d<1) okAll=false;
  }
  return okAll && d===0;
}

const world = `
  const W=800,H=500,HUD_H=54, PLAYER_SPD_FIGHTER=3.2, PLAYER_SPD_BOMBER=2.4, PLAYER_TURN=0.14;
  let FS1_MODE=false, GS='playing', paused=false, callMenu=false, wave=1, score=0, allies=[], jump=false;
  let settingsOpen=false, userPaused=false;
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
  ${themesDecl}
  let ECO={hud:'hlp', scheme:'fire'};
  ${menuBgDecl}
  ${hangarDecl}
  ${volleyDecl}
  let MOUNTS={};
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
const rowOf = (key)=>W.run('window._shipRects').find(r=>r.ship===key);
ok('eight rows drawn', rects.length===8);
ok('menu fits on the 800x500 field', rects.every(r=>r.x>=0 && r.y>=0 && r.x+r.w<=800 && r.y+r.h<=500));
ok('fighters first, then bombers',
   rects.map(r=>r.ship).join()==='fitoth,fihorus,fiserapis,fiseth,fitauret,boosiris,bobakha,bosekhmet');
ok('every row is full width and they do not overlap',
   rects.every(r=>r.w===rects[0].w) &&
   rects.every((r,i)=>i===0 || r.y >= rects[i-1].y+rects[i-1].h));
ok('a locked row is thinner than one that can be taken',
   rowOf('bobakha').h < rowOf('fihorus').h);
ok('only Horus and Osiris are tappable', rects.filter(r=>r.key).map(r=>r.key).join()==='fihorus,boosiris');
const locked = rowOf('bobakha');
W.run(`pointerConsumed({x:${locked.x+5},y:${locked.y+5}})`); ok('tap on locked Bakha keeps the menu open', W.get('shipMenu')===true && P().ship==='fitoth');
const horus = rowOf('fihorus');
W.run(`pointerConsumed({x:${horus.x+5},y:${horus.y+5}})`); ok('tap on Horus switches', P().ship==='fihorus' && W.get('shipMenu')===false);
reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
W.run('pointerConsumed({x:2,y:2})'); ok('tap outside closes without switching', W.get('shipMenu')===false && P().ship==='fitoth' && W.run('shipSwapReady()')===true);
W.run("window._shipBtnRect={x:695,y:4,w:22,h:20}; pointerConsumed({x:700,y:10})"); ok('tap on the bar button opens the menu', W.get('shipMenu')===true);

console.log('The panel swallows its own clicks');
{
  reset(); W.run("shipUnlocked=8"); W.set('allies',[destroyer()]);
  W.run('toggleShipMenu()'); W.run('drawShipMenu()');
  const pr = W.run('window._shipPanelRect');
  ok('the panel reports its outline', pr && pr.w>0 && pr.h>0);
  // The header line: inside the panel, on no row at all.
  W.run(`pointerConsumed({x:${pr.x+40},y:${pr.y+6}})`);
  ok('a click on the header keeps the panel open', W.get('shipMenu')===true);
  // A gap between two rows.
  const rs = W.run('window._shipRects');
  const gapY = rs[0].y + rs[0].h + 2;
  W.run(`pointerConsumed({x:${rs[0].x+40},y:${gapY}})`);
  ok('a click in the gap between rows keeps it open too', W.get('shipMenu')===true);
  // The footer.
  W.run(`pointerConsumed({x:${pr.x+pr.w/2},y:${pr.y+pr.h-6}})`);
  ok('and one on the footer', W.get('shipMenu')===true);
  ok('none of them switched the ship', P().ship==='fitoth');
  // Outside the outline is still outside.
  W.run(`pointerConsumed({x:${pr.x-12},y:${pr.y+pr.h/2}})`);
  ok('a click beside the panel closes it', W.get('shipMenu')===false);
}

console.log('Keyboard');
const key = (code)=>W.run(`onKey({code:'${code}', preventDefault(){}})`);
reset(); W.run("shipUnlocked=4"); W.set('allies',[destroyer()]);
key('KeyV'); ok('V opens', W.get('shipMenu')===true);
// Four hulls open: roster 0 to 3. The digits follow the panel, so 4 is the
// Seth, which is still locked, and 6 is the first bomber.
key('Digit4'); ok('4 (the Seth, not unlocked yet) does nothing',
                  W.get('shipMenu')===true && P().ship==='fitoth');
key('Digit6'); ok('6 takes the Osiris, first row of the bombers',
                  P().ship==='boosiris' && W.get('shipMenu')===false);
reset(); W.run("shipUnlocked=4"); W.set('allies',[destroyer()]); key('KeyV');
key('Digit3'); ok('3 takes the Serapis, third row down',
                  P().ship==='fiserapis' && W.get('shipMenu')===false);
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

console.log('Hull pictures in their own cell');
const IMG = (w,h)=>({width:w, height:h});
const ALL_IMGS = {fitoth:IMG(120,90), fihorus:IMG(120,90), boosiris:IMG(150,110),
                  fiserapis:IMG(120,90), fiseth:IMG(120,90), bobakha:IMG(150,110),
                  fitauret:IMG(120,90), bosekhmet:IMG(150,110)};
const PICW = W.run('HG_PIC_W'), PICH = W.run('HG_ROW')-6;
reset(); W.run("shipUnlocked=8"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
W.set('IMGS', {});
CLR(); W.run('drawShipMenu()');
ok('nothing loaded yet: no picture, no crash, rows still there',
   draws().length===0 && W.run('window._shipRects').length===8);
W.set('IMGS', ALL_IMGS);
CLR(); W.run('drawShipMenu()');
ok('one hull drawn per open row', draws().length===8);
// The gloss on each plate clips as well, so this counts at least one clip
// per picture rather than exactly one in total.
ok('each one clipped to its own cell first', clips().length>=8);
ok('each one fits inside the picture cell',
   draws().every(d=>d.args[3]<=PICW-5 && d.args[4]<=PICH-5 && d.args[3]>0 && d.args[4]>0));
ok('aspect ratio kept', draws().every(d=>Math.abs((d.args[3]/d.args[4]) - (120/90))<0.01
                                      || Math.abs((d.args[3]/d.args[4]) - (150/110))<0.01));
ok('save and restore stay balanced, no leaking clip or alpha', balanced());
ok('a picture is a picture now, not a watermark', alphas().every(a=>a>0.9 && a<=1));
{
  // Three open, five locked: a locked hull has no row tall enough for a
  // picture, so it gets none at all.
  reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
  W.set('IMGS', ALL_IMGS); CLR(); W.run('drawShipMenu()');
  ok('a locked hull shows no picture', draws().length===3);
}
reset(); W.run("shipUnlocked=8"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
W.set('IMGS', {fitoth:IMG(0,0)});
CLR(); W.run('drawShipMenu()');
ok('a zero sized sprite is skipped instead of dividing by zero', draws().length===0);
W.set('IMGS', {});

console.log('Barrels and volley damage, in their own columns');
const texts = ()=> CALLS.filter(c=>c.fn==='fillText').map(c=>({s:String(c.args[0]), x:c.args[1], y:c.args[2]}));
// A column is checked by where it actually lands: the x of the column in the
// layout, added to the x of a row the menu itself reported.
const colX = (k)=> W.run('HG_COLS').find(c=>c.k===k).x;
// The column titles sit on the same x, so a value only counts when it also
// sits inside a row.
const inCol = (k)=>{
  const x0 = colX(k), rs = W.run('window._shipRects');
  return texts().filter(t=> rs.some(r=> t.x === r.x + x0 && t.y >= r.y && t.y <= r.y + r.h));
};
reset(); W.run("shipUnlocked=8"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
W.set('MOUNTS', {});
CLR(); W.run('drawShipMenu()');
ok('no mount data: no claim about guns or volley at all',
   inCol('guns').length===0 && inCol('volley').length===0);
W.set('MOUNTS', {fitoth:{primary:[1,1]}, fihorus:{primary:[1,1]}, boosiris:{primary:[1,1]},
                 fiserapis:{primary:[1,1]}, fiseth:{primary:[1,1]}, bobakha:{primary:[1,1]},
                 fitauret:{primary:[1,1,1]}, bosekhmet:{primary:[1,1]}});
CLR(); W.run('drawShipMenu()');
ok('a figure on every one of the eight rows',
   inCol('guns').length===8 && inCol('volley').length===8);
ok('the seven two barrel hulls read 2 and 51',
   inCol('guns').filter(t=>t.s==='2').length===7 &&
   inCol('volley').filter(t=>t.s==='51').length===7);
ok('the Tauret reads 3 and 57',
   inCol('guns').filter(t=>t.s==='3').length===1 &&
   inCol('volley').filter(t=>t.s==='57').length===1);
ok('the figure matches what volleyDmg actually does',
   Math.round(W.run('volleyTotal(2)'))===51 && Math.round(W.run('volleyTotal(3)'))===57
   && Math.round(W.run('volleyTotal(1)'))===44);
ok('one barrel is the fallback of the formula, not a crash', W.run('volleyTotal(0)')===44);
{
  // The point of the columns: hull sits under hull on every row.
  const hulls = inCol('hull').map(t=>t.s).join();
  ok('the hull column reads down the list in order', hulls==='100,80,80,125,100,140,100,140');
  const shields = inCol('shield').map(t=>t.s).join();
  ok('the shield column too', shields==='100,100,70,130,130,100,100,130');
  ok('every value in a column shares one x',
     new Set(inCol('hull').map(t=>t.x)).size===1);
}
{
  // Two unlocked of eight: the menu needs two to open at all.
  reset(); W.run("shipUnlocked=2"); W.set('allies',[destroyer()]);
  W.set('MOUNTS', {fitoth:{primary:[1,1]}, fihorus:{primary:[1,1]}, fitauret:{primary:[1,1,1]}});
  W.run('toggleShipMenu()'); CLR(); W.run('drawShipMenu()');
  ok('only the two unlocked rows make a claim', inCol('guns').length===2);
  ok('the locked Tauret stays silent even with mount data',
     inCol('volley').every(t=>t.s!=='57'));
}
W.set('MOUNTS', {});

console.log('One look, and it is the forum one');
reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
CLR(); W.run('drawShipMenu()');
const hlpFonts = CALLS.filter(c=>c.fn==='set font').map(c=>String(c.args[0]));
const hlpCells = W.run('window._shipRects').map(r=>r.x+','+r.y+','+r.w+','+r.h).join('|');
ok('no Courier left in the hangar', hlpFonts.every(f=>f.indexOf('Courier')<0));
ok('it uses the forum faces', hlpFonts.some(f=>f.indexOf('Tahoma')>=0) && hlpFonts.some(f=>f.indexOf('Segoe UI')>=0));
ok('values are no longer set in 8 and 9 pixels',
   hlpFonts.filter(f=>/Segoe UI/.test(f)).some(f=>/1[4-9]px/.test(f)));
ok('the active row gets a glow ring', CALLS.some(c=>c.fn==='set shadowBlur'));
ok('no ring leaks out of its save/restore', balanced());
ok('nothing chooses between two looks any more', !/ECO\\.hud/.test(src));
W.run("ECO.scheme='void'"); CLR(); W.run('drawShipMenu()');
ok('the hangar draws in Void too', CALLS.length>50);
ok('and the rows did not move',
   W.run('window._shipRects').map(r=>r.x+','+r.y+','+r.w+','+r.h).join('|')===hlpCells);
W.run("ECO.scheme='fire'");

console.log('Everything is drawn from the surface kit');
{
  reset(); W.run("shipUnlocked=8"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
  CLR(); W.run('drawShipMenu()');
  // Gradients are allowed again, but only as gloss: a short fall of light
  // over the top of a plate. None may run the height of a panel the way the
  // old box gradient did.
  const grads = CALLS.filter(c=>c.fn==='createLinearGradient');
  ok('every gradient is a gloss, not a full height fill',
     grads.length>0 && grads.every(g=>(g.args[3]-g.args[1])<=200));
  // A chamfered outline is six corners. A rectangle would be four.
  const closes = CALLS.filter(c=>c.fn==='closePath').length;
  ok('the panel and every plate are chamfered, not rectangles', closes>=9);
  ok('one scale under each of the two group headings',
     CALLS.filter(c=>c.fn==='set lineWidth' && c.args[0]===1).length>0 && closes>=9);
  ok('a ring is drawn, and only around the active row',
     CALLS.filter(c=>c.fn==='set shadowBlur' && c.args[0]===6).length===2);
  ok('nothing leaks out of a save/restore', balanced());
}
{
  // The kit is shared, so the hangar must not reach past it for a shape of
  // its own. thBevel and thPanel belong to the screens not yet rebuilt.
  const a = src.indexOf('function drawShipMenu()');
  const body = src.slice(a, src.indexOf('function drawCallMenu()'));
  ok('the hangar uses no bevel and no gradient panel',
     body.indexOf('thBevel')<0 && body.indexOf('thPanel')<0);
  ok('and no dialog frame of its own', body.indexOf('uiDialog')<0);
}
{
  // The digit is the keyboard shortcut, so it has to follow the hull through
  // the regrouping rather than count rows.
  reset(); W.run("shipUnlocked=8"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
  CLR(); W.run('drawShipMenu()');
  const rs = W.run('window._shipRects');
  const chipX = W.run('HG_NUM') + W.run('HG_NUM_W')/2;
  const chip = (key)=>{ const r=rs.find(r=>r.ship===key);
    return texts().find(t=> t.x===r.x+chipX && t.y>=r.y && t.y<=r.y+r.h); };
  ok('the Osiris shows 6: first bomber, sixth row',
     chip('boosiris') && chip('boosiris').s==='6');
  ok('and the Bakha shows 7', chip('bobakha') && chip('bobakha').s==='7');
  ok('the digits run 1 to 8 straight down the panel',
     rs.map(r=>chip(r.ship).s).join()==='1,2,3,4,5,6,7,8');
}

console.log('The panel grows with what is open');
{
  const height = ()=>{ const r=W.run('window._shipRects'); return r[r.length-1].y+r[r.length-1].h - r[0].y; };
  reset(); W.run("shipUnlocked=2"); W.set('allies',[destroyer()]); W.run('toggleShipMenu(); drawShipMenu()');
  const small = height();
  reset(); W.run("shipUnlocked=8"); W.set('allies',[destroyer()]); W.run('toggleShipMenu(); drawShipMenu()');
  const big = height();
  ok('eight open hulls need more room than two', big > small);
  ok('and it still fits on the field',
     W.run('window._shipRects').every(r=>r.y>=0 && r.y+r.h<=500));
}

console.log('Bar button placement');
{
  const a = src.indexOf('  // SHIP SWITCH\n'), b = src.indexOf('  // SETTINGS and PAUSE');
  const snip = src.slice(a, b);
  W.run("var H2=54; shipMenu=false; window._shipBtnRect=undefined; " + snip);
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
