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
// The cycle tables and the support columns they switch.
const cycleDecl = src.match(/const ROSTER_HOL[\s\S]*?\nlet cycleBase = 0;[^\n]*/)[0];
// The fleet tabs of the Shivan cycle (v163).
const fleetDecl = src.match(/const FLEET_TABS = [\s\S]*?let hangarTab = 'terran', callTab = 'terran';/)[0];
const facOnDecl = src.match(/const ALLY_FAC_ON = \{[^}]*\};/)[0];
const extraDecl = src.match(/const EXTRA_SHIPS = (\{[\s\S]*?\n\});/)[1];
const hullFacDecl = src.match(/const HULL_FAC = \{[\s\S]*?\};/)[0];
const menuBgDecl = src.match(/const MENU_BG_ALPHA[\s\S]*?const MENU_BG_PAD\s*=\s*[\d.]+;/)[0];
const hangarDecl = src.match(/const HG_W[\s\S]*?\n\];/)[0];
const themesDecl = src.match(/const THEMES = \{[\s\S]*?\n\};/)[0];
// The weapon tables and the rearm panel's measurements.
const wpnDecl  = src.match(/const PLAYER_FR_BASE[\s\S]*?\n\];/)[0];
// v186: the FS2 arsenal and the banks (56_banks.js), the AI's old tables.
const smallTbl = src.match(/const SMALL_TBL = \{[\s\S]*?\n\};/)[0];
const wpnDecl2 = (function(){
  const a = src.indexOf('// ── WEAPON BANKS (v186)');
  const b = src.indexOf('\nfunction empBurst(');
  const ai = src.match(/const AI_SECONDARIES = \[[\s\S]*?\n\];/)[0];
  const aip = src.match(/const AI_PRIMARIES = \{[\s\S]*?\n\};/)[0];
  return src.slice(a, b) + '\n' + ai + '\n' + aip + '\nconst SECONDARIES = ARSENAL_S;\n';
})();
const rmDecl   = src.match(/const RM_W[\s\S]*?const RM_BARS = \[[\s\S]*?\n\];/)[0];
// pointerConsumed reaches for the title on a finished run. Starting a run
// is not what these files test, so it is a stub.
const wpnState = 'let rearmMenu = false; let resumeHold = false;'
  // The bar asks where the pointer is sitting; nothing hovers in a test.
  + ' const HOVER = {x:-1, y:-1}; function toTitleOrLaunch(){}; const WPN_SEEN = {}; const UI_WEAPONS = false;';

const volleyDecl = src.match(/const VOLLEY_BASE[\s\S]*?const VOLLEY_PER_EXTRA\s*=\s*[\d.]+;/)[0];
const names = [
  'syncCursor','hovering',
  'panelOpen','holdResume','clearResumeHold','drawResumeHint',
  'applyLoadout','rearmFull','curPri','curSec','priDef','secDef','hullSecCls',
  'weaponName','weaponOpen','waveReached','secRounds','corvetteOnField',
  'rearmReady','setRearmMenu','toggleRearmMenu','fitWeapon','rearmLayout',
  'drawRearmMenu','drawRearmIcon','rmPri','rmDef','rmBankKey','rmDps','rmBankDmg','rmValueOf','rmReach','rmFacts','rmBars','rmShipLines','rmSelectBank','rmStep','drawRearmShip','rmWrap','hgName','drawDoneButton','closeKeys','drawInfoCard','hangarCard','allyCard','allyLabel','tickWeaponUnlocks',
  'thFit','callMenuLayout','drawAllyRow','drawKeyChip','drawHullCell','hullClass','isBomberHull','shipStats','applyShip','tickShipUnlocks','shipSwapReady',
  'setShipMenu','toggleShipMenu','swapShip','drawSwapIcon','statPips','drawShipMenu','pointerConsumed',
  'resetPlayerShield','playerSc','setCallMenu',
  'hullFac','shipFac','hangarServes','isHangarShip','hangarFacs','colossusOnField','shipOffered',
  'mountsFor','spriteFacing','drawHullBg','drawHullCell','volleyDmg','volleyTotal','primaryCount','syncPause',
  'hangarGroups','hangarLayout','drawMissileIcon','drawBombIcon','drawKeyChip',
  'hangarOrder','insidePanel','cycleAt','enterCycle','cycleTabs','facShips','shipIsOpen',
  'hangarTabOpen','callTabOpen','pickTab','nextTab','drawFleetTabs','allyFacOn','titleFsHit','forceShip','releaseShip',
  'thChamferPath','thPlate','thGlowPath','thBrackets','thScale','thFrame','thRGBA','thGloss','thCutGlint',
  'TH','thLabel','thValue','thBevel','thGlow','thPanel','thButton','btnState','btnText','thDivider','drawSwapIcon','UI','uiHLP','uiLabel','uiValue','uiCell','uiDialog'];
// v207: keys go through the key table (BINDS) and inputPress.
const bindDecl = src.slice(src.indexOf('const BINDS = ['), src.indexOf('// The rows as a list (title)'));
const keyHandler = 'function(ev){ inputPress(ev); }';
const downStart = src.indexOf("CVS.addEventListener('mousedown',");
const mouseHandler = src.slice(src.indexOf('function', downStart), blockEnd(src, src.indexOf('function', downStart)));
const launch = fn('launchGame');

const CALLS = [];
const ctxStub = new Proxy({}, {
  get:(t,k)=> k in t ? t[k] : function(){
    CALLS.push({fn:String(k), args:[].slice.call(arguments)});
    // createLinearGradient has to hand back something with addColorStop.
    if(k==='createLinearGradient') return {addColorStop:function(){}};
    // thFit measures before it cuts, so the stub has to answer with a width.
    // Roughly 0.55 of the set point size per character is close enough for
    // the layout decisions being checked here.
    if(k==='measureText'){
      const px = parseFloat(String(t.font||'10px').replace(/^bold\s+/,'')) || 10;
      return {width: String(arguments[0]||'').length * px * 0.55};
    }
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
  // Notices go to the column under the objective line; the column itself
  // is not under test here, only what is announced.
  let NOTICE_LOG=[]; function notice(t, tone){ NOTICE_LOG.push({txt:t, tone:tone}); }
  // The bar's attention pulses are the field simulation's business.
  let BAR_PULSE={}; function barPulseLevel(){ return 0; } function barPulse(){}
  // The practice log is not what is tested here.
  function plogRearm(){} function plogSec(){} function plogSync(){} function plogEvent(){}
  function muteHit(){ return false; } function sndToggleMute(){}
  // A hull lent by a mission (see forceShip).
  let forcedPrev='';
  let eraOff=false, IMGS={}, isFiring=false, launched=0;
  const ctx=CTX, document={body:{classList:{add(){},remove(){}}}, getElementById(){return {style:{}};}};
  const window={};
  function inJump(){return jump;} function eraShieldsOff(){return eraOff;}
  function setSettings(){} function toggleFullscreen(){} function refineTicket(){} function callAlly(){}
  function allyReady(){return true;} function toggleCallMenu(){} function toGC(x,y){return {x:x,y:y};}
  let shipUnlocked=1, shipSwapWave=-1, shipMenu=false, gameOverAt=0;
  const ALLY_KEYS=[], ALLY_ORDER=[], ALLY_SPECIAL='x', ALLY_SPECIAL_KEY='Q';
  ${hullFacDecl}
  ${wpnDecl}
  ${smallTbl}
  if(typeof sndPlay==='undefined') var sndPlay=function(){};
  ${wpnDecl2}
  ${rmDecl}
  ${wpnState}
  ${themesDecl}
  let ECO={hud:'hlp', scheme:'fire'};
  ${menuBgDecl}
  ${hangarDecl}
  ${volleyDecl}
  let MOUNTS={};
  ${shipsDecl}
  let UI_SHIPS=1;
  const EXTRA_SHIPS = ${extraDecl};
  ${facOnDecl}
  ${cycleDecl}
  let shipUnlockedFac = {terran:1, vasudan:1};
  ${fleetDecl}
  ${names.map(fn).join('\n')}
  let K = {}; const SEC_HOLD = {};
  ${bindDecl}
  ${['windowOpen','closeWindow','inputPress','windowKey'].map(fn).join('\n')}
  const onKey = ${keyHandler};
  const onDown = ${mouseHandler};
  return {
    get:(k)=>eval(k), set:(k,v)=>eval(k+'=v'), run:(code)=>eval(code)
  };`;
const W = new Function('CTX', world)(ctxStub);
let fails = 0;
function ok(label, cond){ console.log((cond?'  ok    ':'  FAIL  ')+label); if(!cond) fails++; }
const P = ()=>W.get('player');
const reset = ()=>{ W.run("GS='playing';paused=false;resumeHold=false;callMenu=false;shipMenu=false;wave=1;score=0;allies=[];jump=false;FS1_MODE=false;shipUnlocked=1;shipSwapWave=-1;SUB_MSGS=[];NOTICE_LOG=[];player={x:100,y:200,hullMult:1};applyShip(PLAYER_SHIPS[0].key)"); };
const destroyer = (o)=>Object.assign({img:'dehatshepsut', small:false, dead:false, warpOut:false}, o||{});

console.log('Start ship');
reset();
ok('starts in the Thoth', P().ship==='fitoth');
ok('Thoth stats 3.5 / 0.17 / 69 / 51 / 32 Harpoons', P().spd===3.5 && P().turn===0.17 && P().maxHp===69 && P().maxSh===51 && P().secMax===32 && P().secType==='missile');

console.log('Unlocks');
reset();
W.run("score=3999; tickShipUnlocks()"); ok('3999 points: nothing unlocked', W.get('shipUnlocked')===1);
W.run("score=4000; tickShipUnlocks()"); ok('4000 points: Horus unlocked, one message', W.get('shipUnlocked')===2 && W.get('NOTICE_LOG').length===1 && /HORUS/.test(W.get('NOTICE_LOG')[0].txt));
W.run("score=23000; tickShipUnlocks()"); ok('jump to 23000: Osiris, Serapis, Seth at once', W.get('shipUnlocked')===5 && W.get('NOTICE_LOG').length===4);
W.run("score=999999; tickShipUnlocks()"); ok('never past the end of the list', W.get('shipUnlocked')===8);
W.run("tickShipUnlocks()"); ok('seven unlock messages in total, none repeated', W.get('NOTICE_LOG').length===7);
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
// The panel closes, but the game stays stopped: coming back into the
// fight is the player's to time now, whatever the panel and however it
// was left.
ok('Osiris taken and the menu closed', P().ship==='boosiris' && W.get('shipMenu')===false);
ok('but the game is still held', W.get('paused')===true && W.get('resumeHold')===true);
W.run('pointerConsumed({x:400,y:300})');
ok('and one tap puts you back in it', W.get('paused')===false && W.get('resumeHold')===false);
ok('Osiris stats 2.5 / 0.10 / 207 / 154 / 4 Infyrnos in bank 1', P().spd===2.5 && P().turn===0.10 && P().maxHp===207 && P().maxSh===154 && P().secMax===4 && P().sec==='infyrno');
ok('refilled: hull 207, shields 154, every rack full', P().hp===207 && P().sh===154 && P().sb.every(b=>b.ammo===b.max));
ok('switch spent for this wave', W.run('shipSwapReady()')===false);
W.run('toggleShipMenu()'); ok('menu does not open again this wave', W.get('shipMenu')===false);
W.run('wave=2'); ok('next wave: available again', W.run('shipSwapReady()')===true);

console.log('Cycle scaling and shields');
reset(); W.run("player.hullMult=1.5; shipUnlocked=8"); W.set('allies',[destroyer()]);
W.run("toggleShipMenu(); swapShip('bosekhmet')"); ok('Sekhmet at cycle x1.5: hull 258', P().maxHp===258 && P().hp===258);
reset(); W.run("eraOff=true; shipUnlocked=2"); W.set('allies',[destroyer()]);
W.run("toggleShipMenu(); swapShip('fihorus')"); ok('era without shields: shields stay 0', P().sh===0 && P().maxSh===59);
W.run('eraOff=false');

console.log('Call menu and switch menu exclude each other');
reset(); W.run("shipUnlocked=2; callMenu=true; paused=true"); W.set('allies',[destroyer()]);
W.run('toggleShipMenu()'); ok('opening the switch closes the call menu', W.get('callMenu')===false && W.get('shipMenu')===true);

console.log('Menu drawing and taps');
reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer()]); W.run('toggleShipMenu(); drawShipMenu()');
const rects = W.run('window._shipRects').filter(r=>r.ship);
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
ok('cancelling holds the pause just the same', W.get('resumeHold')===true);
W.run('clearResumeHold()');
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
  const rs = W.run('window._shipRects').filter(r=>r.ship);
  const gapY = rs[0].y + rs[0].h + 1;
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

console.log('DONE (v194)');
{
  reset(); W.run("shipUnlocked=8"); W.set('allies',[destroyer()]);
  W.run('toggleShipMenu()'); W.run('drawShipMenu()');
  const all = W.run('window._shipRects'), done = all.filter(r=>r.close);
  const rows = all.filter(r=>r.ship), pr = W.run('window._shipPanelRect');
  ok('one DONE button', done.length===1);
  const d = done[0];
  ok('inside the panel, below every row',
     d.x>=pr.x && d.x+d.w<=pr.x+pr.w && d.y+d.h<=pr.y+pr.h && rows.every(r=>r.y+r.h <= d.y-4));
  W.run(`pointerConsumed({x:${d.x+d.w/2},y:${d.y+d.h/2}})`);
  ok('DONE closes without switching', W.get('shipMenu')===false && P().ship==='fitoth' && W.run('shipSwapReady()')===true);
  ok('and holds the pause like ESC', W.get('resumeHold')===true);
  W.run('clearResumeHold()');
  // the longest list: every hull open, the tight layout
  reset(); W.run("shipUnlocked=99"); W.set('allies',[destroyer()]);
  W.run('toggleShipMenu()'); W.run('drawShipMenu()');
  const a2 = W.run('window._shipRects'), d2 = a2.find(r=>r.close), p2 = W.run('window._shipPanelRect');
  ok('with every hull open DONE still clears the rows and the panel fits',
     !!d2 && a2.filter(r=>r.ship).every(r=>r.y+r.h <= d2.y-4) && p2.y>=0 && p2.y+p2.h<=500);
  W.run('setShipMenu(false); clearResumeHold()');
}

console.log('Keyboard');
const key = (code)=>W.run(`onKey({code:'${code}', preventDefault(){}})`);
reset(); W.run("shipUnlocked=4"); W.set('allies',[destroyer()]);
key('F2'); ok('F2 (hangar) opens', W.get('shipMenu')===true);
// Four hulls open: roster 0 to 3. The digits follow the panel, so 4 is the
// Seth, which is still locked, and 6 is the first bomber.
key('Digit4'); ok('4 (the Seth, not unlocked yet) does nothing',
                  W.get('shipMenu')===true && P().ship==='fitoth');
key('Digit6'); ok('6 takes the Osiris, first row of the bombers',
                  P().ship==='boosiris' && W.get('shipMenu')===false);
reset(); W.run("shipUnlocked=4"); W.set('allies',[destroyer()]); key('F2');
key('Digit3'); ok('3 takes the Serapis, third row down',
                  P().ship==='fiserapis' && W.get('shipMenu')===false);
reset(); W.run("shipUnlocked=4"); W.set('allies',[destroyer()]); key('F2'); key('F2');
ok('its own key (F2) closes', W.get('shipMenu')===false);
ok('and holds the pause, like every other way of leaving a panel',
   W.get('paused')===true && W.get('resumeHold')===true);
W.run('clearResumeHold()');
ok('after the tap the game runs again', W.get('paused')===false);
reset(); key('F2'); ok('F2 without a destroyer does nothing', W.get('shipMenu')===false);

console.log('Restart guard');
W.run("launchGame=function(){launched++}");
// The title and the game over screen both go through toTitleOrLaunch now,
// so that is what has to be in place for the restart guard to be tested.
W.run("toTitleOrLaunch=function(){ if(GS==='gameover'){ GS='title'; return; } launchGame(); }");
const down = ()=>W.run("onDown({button:0, clientX:400, clientY:300})");
W.run("GS='title'; launched=0"); down(); ok('tap on title starts at once', W.get('launched')===1);
W.run("GS='gameover'; gameOverAt=performance.now(); launched=0"); down(); ok('tap right after dying does not restart', W.get('launched')===0);
W.run("gameOverAt=performance.now()-2000"); down();
ok('tap after 2 s goes back to the title, not into the next run',
   W.get('launched')===0 && W.get('GS')==='title');


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
ok('first switch of the wave refits', P().ship==='fihorus' && P().hp===59 && P().sh===59 && P().secAmmo===10);
ok('no Colossus: spent for this wave', W.run('shipSwapReady()')===false);
W.set('allies',[destroyer(), colossus()]);
ok('Colossus arrives: available again in the same wave', W.run('shipSwapReady()')===true);
W.run("player.hp=40; player.sh=50; player.sb[0].ammo=5; syncLegacyWeapons()");
W.run("toggleShipMenu(); swapShip('boosiris')");
ok('second switch happens', P().ship==='boosiris');
ok('hull carries over as a fraction, 40/59 of 207 = 140', P().hp===140);
ok('shields carry over, 50/59 of 154 = 131', P().sh===131);
ok('ammo carries over, half a rack: 2 of 3 Piranhas', P().secAmmo===2);
ok('no refit: not full', P().hp<P().maxHp && P().secAmmo<P().secMax);

reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer(), colossus()]);
W.run("toggleShipMenu(); swapShip('fihorus')");
ok('with the Colossus there the first switch still refits', P().hp===59 && P().secAmmo===10);
W.run("player.hp=1");
W.run("toggleShipMenu(); swapShip('boosiris')");
ok('a nearly dead hull stays alive after carrying over', P().hp>=1 && P().hp<=4);

reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer(), colossus({dead:true})]);
W.run("toggleShipMenu(); swapShip('fihorus')");
ok('dead Colossus grants nothing', W.run('shipSwapReady()')===false);
reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer(), colossus({warpOut:true})]);
W.run("toggleShipMenu(); swapShip('fihorus')");
ok('Colossus warping out grants nothing', W.run('shipSwapReady()')===false);

reset(); W.run("shipUnlocked=3"); W.set('allies',[colossus()]);
W.run("toggleShipMenu(); swapShip('fihorus')"); W.run("player.hp=20");
W.run("toggleShipMenu(); swapShip('fitoth')");
ok('back onto the start hull at the Colossus, 20/59 of 69 = 23', P().ship==='fitoth' && P().hp===23);
W.run('wave=2');
ok('new wave with the Colossus still there: refits again', W.run('shipSwapReady()')===true);
W.run("toggleShipMenu(); swapShip('fihorus')"); ok('and it is a full hull', P().hp===59);

console.log('Cycles: each brings its own fleet');
{
  const hol = W.run('cycleAt(1)'), ntf = W.run('cycleAt(31)');
  ok('waves 1 to 30 are the Hammer of Light cycle', W.run('cycleAt(30)')===hol && hol.first===1);
  ok('wave 31 opens the NTF cycle, and it holds to 60', ntf.first===31 && W.run('cycleAt(59)')===ntf && W.run('cycleAt(60)')===ntf);
  ok('wave 61 opens the Shivan cycle, and it holds after that',
     W.run('cycleAt(61)').first===61 && W.run('cycleAt(140)')===W.run('cycleAt(61)'));
  reset();
  W.run("score=95000; enterCycle(cycleAt(31))");
  ok('entering it puts the player in a Myrmidon, fresh', P().ship==='fimyrmidon' && P().hp===P().maxHp);
  ok('the roster is the Terran one, nine hulls',
     W.run('PLAYER_SHIPS.length')===9 && W.run("PLAYER_SHIPS.every(s=>s.fac==='terran')"));
  ok('in the agreed order (the Perseus second, v159)',
     W.run("PLAYER_SHIPS.map(s=>s.key).join()")==='fimyrmidon,fiperseus,fiherc,boartemis,fihercmk2,bomedusa,fierinyes,boursa,fiares');
  ok('only the first hull is open', W.get('shipUnlocked')===1);
  W.run("score=95000+1999; tickShipUnlocks()");
  ok('the points brought into the cycle do not count', W.get('shipUnlocked')===1);
  W.run("score=95000+2000; tickShipUnlocks()");
  ok('2000 points scored IN the cycle open the Perseus', W.get('shipUnlocked')===2 && /PERSEUS/.test(W.get('NOTICE_LOG').slice(-1)[0].txt));
  W.run("score=95000+4000; tickShipUnlocks()");
  ok('4000 open the Hercules', W.get('shipUnlocked')===3 && /HERCULES/.test(W.get('NOTICE_LOG').slice(-1)[0].txt));
  ok('the Terran support column answers, the Vasudan one does not',
     W.run('ALLY_FAC_ON.terran')===true && W.run('ALLY_FAC_ON.vasudan')===false);
  // The hangar follows the hull, so the Terran roster needs a Terran destroyer.
  W.set('allies',[destroyer({img:'deorionright'})]);
  ok('a Terran destroyer offers the Hercules', W.run("shipOffered('fiherc')")===true && W.run('shipSwapReady()')===true);
  W.set('allies',[destroyer()]);
  ok('a Vasudan one does not', W.run("shipOffered('fiherc')")===false && W.run('shipSwapReady()')===false);
  W.run("enterCycle(cycleAt(1))");
  ok('and back: the Vasudan roster and column', P().ship==='fitoth' &&
     W.run('ALLY_FAC_ON.terran')===false && W.run('ALLY_FAC_ON.vasudan')===true);
}
ok('the run starts in the cycle of its first wave',
   /else enterCycle\(cycleAt\(wave\+1\)\);/.test(fn('launchGame')));
ok('crossing into a new cycle hands over the fleet',
   /if\(_c!==cycleNow\) enterCycle\(_c\);/.test(fn('nextWave')));
ok('?m= starts the run at that wave instead of repeating it',
   /SCRIPT_ONE\?SCRIPT_ONE-1:0/.test(fn('launchGame')) && !/SCRIPT_ONE \? SCRIPT_ONE : n/.test(src));

console.log('Shivan cycle: both fleets, each on its own tab (v163)');
{
  reset(); W.run("score=200000; enterCycle(cycleAt(61))");
  ok('tabs are on', W.run('cycleTabs()')===true);
  ok('the roster holds both fleets, Terran first',
     W.run("PLAYER_SHIPS.filter(s=>s.fac==='terran').length")===9 && W.run("PLAYER_SHIPS.filter(s=>s.fac==='vasudan').length")===8
     && W.run('PLAYER_SHIPS[0].key')==='fimyrmidon');
  ok('the player starts in a Myrmidon', P().ship==='fimyrmidon');
  ok('the first hull of each fleet is open, nothing more',
     W.run('shipUnlockedFac.terran')===1 && W.run('shipUnlockedFac.vasudan')===1 && W.get('shipUnlocked')===2
     && W.run("shipIsOpen(PLAYER_SHIPS.findIndex(s=>s.key==='fitoth'))")===true
     && W.run("shipIsOpen(PLAYER_SHIPS.findIndex(s=>s.key==='fiperseus'))")===false);
  W.run("score=200000+4000; tickShipUnlocks()");
  ok('points in the cycle open each fleet down its own list (Perseus, Hercules, Horus)',
     W.run('shipUnlockedFac.terran')===3 && W.run('shipUnlockedFac.vasudan')===2 && W.get('shipUnlocked')===5);
  ok('both support fleets answer', W.run('ALLY_FAC_ON.terran')===true && W.run('ALLY_FAC_ON.vasudan')===true);
  W.set('allies',[]);
  ok('no allied destroyer: no switch at all', W.run('shipSwapReady()')===false);
  ok('no allied destroyer: both support tabs open', W.run("callTabOpen('terran') && callTabOpen('vasudan')")===true);
  W.set('allies',[destroyer({img:'detyphon'})]);
  ok('a Vasudan destroyer: the Vasudan hangar tab is open, the Terran one shut',
     W.run("hangarTabOpen('vasudan')")===true && W.run("hangarTabOpen('terran')")===false);
  ok('and the support tabs follow it', W.run("callTabOpen('vasudan')")===true && W.run("callTabOpen('terran')")===false);
  ok('a switch is on offer (Thoth, Horus)', W.run('shipSwapReady()')===true);
  W.run('toggleShipMenu()');
  ok('the menu opens on the open tab', W.get('shipMenu')===true && W.get('hangarTab')==='vasudan');
  ok('it lists only that fleet', W.run("hangarOrder().every(i=>PLAYER_SHIPS[i].fac==='vasudan')"));
  W.run("hangarTab = nextTab(hangarTab, hangarTabOpen)");
  ok('a shut tab cannot be switched to', W.get('hangarTab')==='vasudan');
  W.run('setShipMenu(false)');
  W.set('allies',[destroyer({img:'detyphon'}), destroyer({img:'deorionright'})]);
  ok('destroyers of both fleets: both tabs open',
     W.run("hangarTabOpen('terran') && hangarTabOpen('vasudan') && callTabOpen('terran') && callTabOpen('vasudan')")===true);
  W.run('toggleShipMenu()');
  ok('the menu opens on the fleet of the hull being flown', W.get('hangarTab')==='terran');
  W.run("hangarTab = nextTab(hangarTab, hangarTabOpen)");
  ok('and switches to the other', W.get('hangarTab')==='vasudan');
  W.run('setShipMenu(false)');
  W.set('allies',[colossus()]);
  ok('the Colossus serves both', W.run("hangarTabOpen('terran') && hangarTabOpen('vasudan')")===true);
  reset(); W.run("score=95000; enterCycle(cycleAt(31))");
  ok('the NTF cycle has no tabs', W.run('cycleTabs()')===false);
}

console.log('A mission can lend a hull');
{
  reset(); W.run("score=95000; enterCycle(cycleAt(31)); shipUnlocked=8");
  W.set('allies',[destroyer({img:'deorionright'})]);
  ok('before: a Terran destroyer offers a switch', W.run('shipSwapReady()')===true);
  W.run("forceShip('fipegasus')");
  ok('the player flies the lent hull', P().ship==='fipegasus');
  ok('with its own figures, not the fighter defaults',
     P().maxSh===85 && P().spd===3.6 && W.run("shipStats('fipegasus').name")==='GTF Pegasus');
  ok('and the hangar is closed for this mission', W.run('shipSwapReady()')===false);
  ok('it is announced in the column', W.get('NOTICE_LOG').some(n=>/PEGASUS ASSIGNED/.test(n.txt)));
  W.run("player.hp=10; releaseShip()");
  ok('the next wave hands the own hull back, refitted', P().ship==='fimyrmidon' && P().hp===P().maxHp);
  ok('and the hangar opens again', W.run('shipSwapReady()')===true);
  W.run("releaseShip()");
  ok('releasing twice changes nothing', P().ship==='fimyrmidon');
  W.run("enterCycle(cycleAt(1))");   // the tests below expect the first fleet
}
ok('the next wave releases a lent hull before anything else',
   /releaseShip\(\);[\s\S]{0,200}enterCycle/.test(fn('nextWave')));

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
   draws().length===0 && W.run('window._shipRects').filter(r=>r.ship).length===8);
W.set('IMGS', ALL_IMGS);
CLR(); W.run('drawShipMenu()');
// v192: the info card adds one bigger picture of the hull it is about.
const rowDraws = ()=> draws().filter(d=>d.args[3]<=PICW-5);
ok('one hull drawn per open row, and one in the card', rowDraws().length===8 && draws().length===9);
// The gloss on each plate clips as well, so this counts at least one clip
// per picture rather than exactly one in total.
ok('each one clipped to its own cell first', clips().length>=8);
ok('each one fits inside the picture cell',
   rowDraws().every(d=>d.args[3]<=PICW-5 && d.args[4]<=PICH-5 && d.args[3]>0 && d.args[4]>0));
ok('aspect ratio kept', draws().every(d=>Math.abs((d.args[3]/d.args[4]) - (120/90))<0.01
                                      || Math.abs((d.args[3]/d.args[4]) - (150/110))<0.01));
ok('save and restore stay balanced, no leaking clip or alpha', balanced());
ok('a picture is a picture now, not a watermark', alphas().every(a=>a>0.9 && a<=1));
{
  // Three open, five locked: a locked hull has no row tall enough for a
  // picture, so it gets none at all.
  reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
  W.set('IMGS', ALL_IMGS); CLR(); W.run('drawShipMenu()');
  ok('a locked hull shows no picture', rowDraws().length===3);
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
  const x0 = colX(k), rs = W.run('window._shipRects').filter(r=>r.ship);
  return texts().filter(t=> rs.some(r=> t.x === r.x + x0 && t.y >= r.y && t.y <= r.y + r.h));
};
// v192: guns and volley moved from the list into the info card.
reset(); W.run("shipUnlocked=8"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
W.set('MOUNTS', {});
ok('no mount data: no claim about guns or volley at all',
   W.run("hangarCard('fitoth').facts.join()").indexOf('GUN')<0 || W.run("hangarCard('fitoth').facts.join()").indexOf('VOLLEY')<0);
W.set('MOUNTS', {fitoth:{primary:[1,1]}, fihorus:{primary:[1,1]}, boosiris:{primary:[1,1]},
                 fiserapis:{primary:[1,1]}, fiseth:{primary:[1,1]}, bobakha:{primary:[1,1]},
                 fitauret:{primary:[1,1,1]}, bosekhmet:{primary:[1,1]}});
ok('the card of a two barrel hull reads 2 guns and 51',
   W.run("hangarCard('fihorus').facts.join()").indexOf('2 GUNS  -  VOLLEY 51')>=0);
ok('the Tauret reads 3 and 57', W.run("hangarCard('fitauret').facts.join()").indexOf('3 GUNS  -  VOLLEY 57')>=0);
ok('the figure matches what volleyDmg actually does',
   Math.round(W.run('volleyTotal(2)'))===51 && Math.round(W.run('volleyTotal(3)'))===57
   && Math.round(W.run('volleyTotal(1)'))===44);
ok('one barrel is the fallback of the formula, not a crash', W.run('volleyTotal(0)')===44);
CLR(); W.run('drawShipMenu()');
{
  // The point of the columns: hull sits under hull on every row.
  const hulls = inCol('hull').map(t=>t.s).join();
  ok('the hull column reads down the list in order', hulls==='69,59,76,97,103,207,152,172');
  const shields = inCol('shield').map(t=>t.s).join();
  ok('the shield column too', shields==='51,59,51,149,136,154,159,218');
  ok('every value in a column shares one x',
     new Set(inCol('hull').map(t=>t.x)).size===1);
}
W.set('MOUNTS', {});

console.log('One look, and it is the forum one');
reset(); W.run("shipUnlocked=3"); W.set('allies',[destroyer()]); W.run('toggleShipMenu()');
CLR(); W.run('drawShipMenu()');
const hlpFonts = CALLS.filter(c=>c.fn==='set font').map(c=>String(c.args[0]));
const hlpCells = W.run('window._shipRects').filter(r=>r.ship).map(r=>r.x+','+r.y+','+r.w+','+r.h).join('|');
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
   W.run('window._shipRects').filter(r=>r.ship).map(r=>r.x+','+r.y+','+r.w+','+r.h).join('|')===hlpCells);
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
     grads.length>0 && grads.every(g=>(g.args[3]-g.args[1])<=W.run('window._shipPanelRect').h*0.45));
  // A chamfered outline is six corners. A rectangle would be four.
  const closes = CALLS.filter(c=>c.fn==='closePath').length;
  ok('the panel and every plate are chamfered, not rectangles', closes>=9);
  ok('one scale under each of the two group headings',
     CALLS.filter(c=>c.fn==='set lineWidth' && c.args[0]===1).length>0 && closes>=9);
  // v194: plus the DONE button, lit like the one in the rearm window
  ok('a ring is drawn, and only around the active row and DONE',
     CALLS.filter(c=>c.fn==='set shadowBlur' && c.args[0]===6).length===3);
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
  const rs = W.run('window._shipRects').filter(r=>r.ship);
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
  const height = ()=>{ const r=W.run('window._shipRects').filter(q=>q.ship); return r[r.length-1].y+r[r.length-1].h - r[0].y; };
  reset(); W.run("shipUnlocked=2"); W.set('allies',[destroyer()]); W.run('toggleShipMenu(); drawShipMenu()');
  const small = height();
  reset(); W.run("shipUnlocked=8"); W.set('allies',[destroyer()]); W.run('toggleShipMenu(); drawShipMenu()');
  const big = height();
  ok('eight open hulls need more room than two', big > small);
  ok('and it still fits on the field',
     W.run('window._shipRects').filter(r=>r.ship).every(r=>r.y>=0 && r.y+r.h<=500));
}

console.log('Rearm needs a corvette, not any ship at all');
{
  const corvette = ()=>({type:'corvette', side:'ally', dead:false, warpOut:0, warp:0});
  reset(); W.set('allies', []);
  ok('nothing on the field, no rearm', W.run('rearmReady()')===false);
  W.set('allies', [destroyer()]);
  ok('a destroyer is a hangar, not an armoury', W.run('rearmReady()')===false);
  W.set('allies', [corvette()]);
  ok('a corvette opens it', W.run('rearmReady()')===true);
  const warping = corvette(); warping.warp = 40;
  W.set('allies', [warping]);
  ok('one still coming out of the vortex does not', W.run('rearmReady()')===false);
  const dead = corvette(); dead.dead = true;
  W.set('allies', [dead]);
  ok('nor does a wreck', W.run('rearmReady()')===false);
  W.set('allies', [corvette()]);
  W.set('allies', [corvette()]);   // a live one again, after the wreck above
  W.run('clearResumeHold()');      // and no hold left over from earlier
  // Press the rectangle the bar reports, the way a player does. Calling
  // toggleRearmMenu() here tested the panel and not the button, which is how
  // a button that was never wired to anything passed.
  // Clear the ship button first: an earlier case left a rectangle standing
  // that covers this spot, and pointerConsumed asks about it one line sooner.
  W.run("window._shipBtnRect=null; window._rearmBtnRect={x:709,y:4,w:22,h:46};"
      + " pointerConsumed({x:714,y:12})");
  ok('pressing the button in the bar opens the panel', W.get('rearmMenu')===true);
  W.run("pointerConsumed({x:714,y:12})");
  ok('and pressing it again closes it', W.get('rearmMenu')===false);
  W.run('setRearmMenu(false)');
}

console.log('The standard fit is provably the gun the game had');
{
  // v186: the FS2 arsenal, anchored on the old weapons.
  const p = W.run("priDefP('promr')");
  ok('the Prometheus R is the old Prometheus: no factors at all', p.dmg===1 && p.f.a===1 && p.f.s===1 && p.f.u===1);
  ok('and its FS2 wait of 0.45 s is 27 steps, the old beat was 28', p.wait===27);
  const sb = W.run("priDefP('subach')");
  ok('the Subach keeps its FS2 ratio: 15/18 a shot, 5 shots a second',
     Math.abs(sb.dmg-15/18)<1e-9 && sb.wait===12 && Math.abs(sb.f.a-0.9/1.1)<1e-9);
  const h = W.run("secDefP('harpoon')");
  ok('the Harpoon is the old MX-64 to the number', h.dmg===35 && h.f.a===1 && h.f.s===1);
  const c = W.run("secDefP('cyclops')");
  ok('and the Cyclops the old bomb', c.dmg===80);
  const t = W.run("secDefP('tempest')");
  ok('the rest keep their FS2 ratio (Tempest 45/100 of a Harpoon)', Math.abs(t.dmg-15.75)<1e-9);
}

console.log('Banks: what a hull carries comes from ships.tbl');
{
  reset(); W.run("applyShip('fimyrmidon')");
  ok('the Myrmidon: Prometheus R and Subach', P().pb.map(b=>b.key).join()==='promr,subach');
  ok('Rockeye, Tornado, Tempest', P().sb.map(b=>b.key).join()==='rockeye,tornado,tempest');
  ok('racks from capacity and cargo size: 5, 16, 160', P().sb.map(b=>b.max).join()==='5,16,160');
  ok('the store: 10, recharging at 1.33 a second',
     Math.abs(P().enMax-10)<1e-9 && Math.abs(P().enRe*60-2.4*0.5556)<1e-9);
  W.run("applyShip('boosiris')");
  ok('a bomber gets its own fit, three secondary banks', P().sb.length===3 && P().pb.length===1);
  ok('every bank holds what the hull may carry',
     W.run("player.sb.every(b=>shipBanks('boosiris').sa.indexOf(b.key)>=0 || shipBanks('boosiris').s.indexOf(b.key)>=0)"));
}

console.log('Modes: bank 1, bank 2, linked');
{
  reset(); W.run("applyShip('fimyrmidon')");
  ok('it starts on bank 1', P().pMode===0 && W.run('firingBanks().length')===1);
  W.run('cyclePrimary()'); ok('then bank 2', P().pMode===1 && W.run('firingBanks()[0].key')==='subach');
  W.run('cyclePrimary()'); ok('then both, linked', P().pMode===2 && W.run('firingBanks().length')===2);
  W.run('cyclePrimary()'); ok('and round again', P().pMode===0);
  W.run('cycleSecondary()'); ok('the wheel down steps the secondary bank', P().sSel===1 && P().sec==='tornado');
  W.run("applyShip('fitoth')"); W.run('cyclePrimary()');
  ok('one bank: nothing to step', P().pMode===0);
}

console.log('A refit fills every rack - that is what makes it a rearm');
{
  const corvette = ()=>({type:'corvette', side:'ally', dead:false, warpOut:0, warp:0});
  reset(); W.run("FITS={}; applyShip('fitoth'); score=0"); W.set('allies', [corvette()]);
  W.run('player.sb[0].ammo=3; syncLegacyWeapons()');
  W.run('toggleRearmMenu()');
  W.run("fitWeapon('s0')");
  ok('a bank switches to the next weapon open to it (Harpoon -> Rockeye)', P().sb[0].key==='rockeye');
  ok('and the rack is full', P().sb[0].ammo===P().sb[0].max && P().sb[0].max===20);
  ok('the panel stays open for the next bank', W.get('rearmMenu')===true);
  W.run("fitWeapon('p0')");
  ok('a weapon above the score is skipped (Prometheus R -> Mekhu, not Akheton)', P().pb[0].key==='mekhu');
  W.run("fitWeapon('p0')");
  ok('and round again', P().pb[0].key==='promr');
  W.run('score=4000'); W.run("fitWeapon('p0'); fitWeapon('p0')");
  ok('past the threshold it is offered', P().pb[0].key==='akheton');
  ok('the hull keeps its fit for the run', W.run("fitFor('fitoth').p[0]")==='akheton');
  W.run('setRearmMenu(false); score=0; FITS={}');
}

console.log('The rearm panel');
{
  const corvette = ()=>({type:'corvette', side:'ally', dead:false, warpOut:0, warp:0});
  reset(); W.run("applyShip('fimyrmidon'); score=9000"); W.set('allies', [corvette()]);
  W.run('toggleRearmMenu()');
  CLR(); W.run('drawRearmMenu()');
  const rs = W.run('window._rearmRects');
  const pr = W.run('window._rearmPanelRect');
  const bk = rs.filter(r=>r.bank), wr = rs.filter(r=>r.key);
  ok('one button per bank', bk.length===5 && bk.map(r=>r.bank).join()==='p0,p1,s0,s1,s2');
  ok('and one row per weapon the first bank may carry (v190)',
     wr.map(r=>r.key).join()===W.run("bankChoices('fimyrmidon', true).map(w=>w.key).join()"));
  ok('a weapon above the score is shown but not open', wr.some(r=>!r.open));
  ok('every row is inside the panel',
     rs.every(r=>r.x>=pr.x && r.x+r.w<=pr.x+pr.w && r.y>=pr.y && r.y+r.h<=pr.y+pr.h));
  ok('the panel fits on the field', pr.y>=0 && pr.y+pr.h<=500 && pr.x>=0 && pr.x+pr.w<=800);
  ok('no Courier anywhere',
     CALLS.filter(c=>c.fn==='set font').every(c=>String(c.args[0]).indexOf('Courier')<0));
  ok('nothing leaks out of a save/restore', balanced());
  // v190: a bank button picks the bank, a weapon row fits that weapon.
  const s1 = bk.find(r=>r.bank==='s1');
  W.run(`pointerConsumed({x:${s1.x+5},y:${s1.y+5}})`);
  ok('a click on a bank picks it', W.get('rmBank')==='s1' && W.get('rearmMenu')===true);
  CLR(); W.run('drawRearmMenu()');
  const tr = W.run('window._rearmRects').find(r=>r.key==='tempest');
  W.run(`pointerConsumed({x:${tr.x+5},y:${tr.y+5}})`);
  ok('a click on a weapon fits it to that bank', P().sb[1].key==='tempest' && P().sb[1].ammo===P().sb[1].max);
  W.run('score=0'); CLR(); W.run('drawRearmMenu()');
  const lk = W.run('window._rearmRects').find(r=>r.key && !r.open);
  W.run(`pointerConsumed({x:${lk.x+5},y:${lk.y+5}})`);
  ok('a locked one is only shown, not fitted', P().sb[1].key==='tempest' && W.get('rmShow')===lk.key);
  W.run('score=9000; player.sb[1].ammo=1'); W.run("fitWeapon('s1','tempest')");
  ok('the weapon already in the bank fills it again', P().sb[1].ammo===P().sb[1].max);
  W.run("rmSelectBank('p0')");
  ok('the info panel says reach in screens, never metres',
     ['proms','promr'].every(k=>W.run(`rmFacts(priDefP('${k}'), true).join()`).indexOf(' M')<0) &&
     W.run("rmFacts(secDefP('trebuchet'), false).join()").indexOf('SCREENS')>=0);
  ok('bars compare a whole bank for missiles: 5 Trebuchets lose to 40 Tempests',
     W.run("rmBars(secDefP('trebuchet'), 's1')[0].d") < 0);
  W.run(`pointerConsumed({x:${pr.x+40},y:${pr.y+6}})`);
  ok('a click on the header keeps it open', W.get('rearmMenu')===true);
  W.run(`pointerConsumed({x:${pr.x-12},y:${pr.y+pr.h/2}})`);
  ok('a click beside it closes it', W.get('rearmMenu')===false);
  W.run('clearResumeHold(); toggleRearmMenu()');
  CLR(); W.run('drawRearmMenu()');
  const dn = W.run('window._rearmRects').find(r=>r.close);
  ok('a DONE button inside the panel (v191)', !!dn && dn.x>=pr.x && dn.y+dn.h<=pr.y+pr.h);
  W.run(`pointerConsumed({x:${dn.x+5},y:${dn.y+5}})`);
  ok('DONE closes it and the fit stays', W.get('rearmMenu')===false && P().sb[1].key==='tempest');
}

console.log('The title screen');
// drawTitle is too tangled up with the backdrop to run here, so what is
// checked is the two things that made it look the way it did.
ok('no opaque sheet over the sky any more', !/fillStyle='rgba\(0,0,8,0\.78\)';ctx\.fillRect\(0,0,W,H\)/.test(src));
ok('what is left is a gradient, so the backdrop shows through the top',
   /createLinearGradient\(0, 0, 0, H\)[\s\S]{0,260}?rgba\(0,0,8,0\.20\)/.test(src));
ok('the pasted logo and its 3 are gone',
   !/_logoProcessed/.test(src) && !/fs_logo/.test(src));
ok('the title is set in the theme face instead', /FREESPACE/.test(src) && /thLabel\(54\)/.test(src));
ok('a fresh backdrop is rolled every time the title comes up',
   /function enterTitle\(\)\{[\s\S]{0,300}?nebCur = NEB_NAMES[\s\S]{0,120}?rollBodies\(\)/.test(src));
ok('and a body that leaves the title is replaced, not wrapped round',
   /if\(GS==='title'\)\{ rollBodies\(\); return; \}/.test(src));
ok('the title keeps moving while it sits there',
   /if\(GS==='title'\)\{ fc\+\+; tickStars\(\); tickNebula\(\); return; \}/.test(src));
ok('Try Again goes back to the title rather than into the next run',
   /function toTitleOrLaunch\(\)\{[\s\S]{0,160}?GS==='gameover'\){ enterTitle\(\)/.test(src));
ok('and nothing calls launchGame straight from the game over screen',
   !/gameOverAt>1500\) launchGame\(\)/.test(src));

// Bar button placement: since v186 the whole bar is checked in hudsim.js.
console.log('Cycle scaling keeps the hull');
ok('nextWave scales from the hull base, not from 100', src.includes('player.maxHp=Math.round((player.baseHp||100)*pm);'));
ok('respawn restores the full hull', src.includes('player.hp=player.maxHp;player.x=80;'));

console.log('\n' + (fails ? fails+' FAILED' : 'all passed'));
process.exit(fails?1:0);
