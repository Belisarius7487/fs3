// Top bar simulation. Pulls the REAL bar functions and the theme tokens out
// of the logic file and draws both variants against a recording canvas.
// What matters most: the pointer rectangles must be identical between the
// old bar and the new one, or every tap moves.
// Usage: node hudsim.js <logic.html>
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const src = html.match(/<script[^>]*>([\s\S]*)<\/script>/)[1];

function blockEnd(s, i){
  let j = s.indexOf('{', i), depth = 0;
  for(; j < s.length; j++){
    const c = s[j];
    if(c === '{') depth++;
    else if(c === '}'){ depth--; if(!depth) return j + 1; }
    else if(c === "'" || c === '"' || c === '`'){ const q = c; j++; while(j < s.length && s[j] !== q) j += (s[j] === '\\') ? 2 : 1; }
    else if(s.startsWith('//', j)) j = s.indexOf('\n', j);
    else if(s.startsWith('/*', j)) j = s.indexOf('*/', j) + 1;
  }
  throw new Error('unbalanced');
}
function fn(name){
  const i = src.indexOf('\nfunction ' + name + '(');
  if(i < 0) throw new Error('missing function ' + name);
  return src.slice(i + 1, blockEnd(src, i));
}
function decl(re){
  const m = src.match(re);
  if(!m) throw new Error('missing declaration ' + re);
  return m[0];
}

const themes = decl(/const THEMES = \{[\s\S]*?\n\};/);
const names = ['drawHUD', 'drawHUDHLP', 'drawHUDClassic', 'TH', 'thLabel', 'thValue',
               'thBevel', 'thGlow', 'thPanel', 'thDivider', 'thButton'];

const CALLS = [];
const ctxStub = new Proxy({}, {
  get:(t,k)=> k in t ? t[k] : function(){
    CALLS.push({fn:String(k), args:[].slice.call(arguments)});
    // createLinearGradient has to hand back something with addColorStop.
    if(k === 'createLinearGradient') return {addColorStop:function(){}};
  },
  set:(t,k,v)=>{ CALLS.push({fn:'set '+String(k), args:[v]}); t[k]=v; return true; }
});
const CLR = ()=>{ CALLS.length = 0; };
const fonts = ()=> CALLS.filter(c=>c.fn==='set font').map(c=>String(c.args[0]));

const world = `
  const W=800, H=500, HUD_H=54;
  const ctx=CTX; const window={};
  let GS='playing', score=29910, wave=10, runTime=361, lives=8, fc=7;
  let callMenu=false, shipMenu=false, settingsOpen=false, paused=false;
  let FS1_MODE=false, allies=[], ticketFlash=0, ticketFlashKind='';
  let player={hp:64, maxHp:100, sh:100, maxSh:100, shDelay:0,
              secType:'missile', secTimer:0, secAmmo:20, ship:'fitoth'};
  let tickets={cruiser:6, corvette:2, destroyer:1, colossus:0};
  const TICKET_ORDER=['cruiser','corvette','destroyer','colossus'];
  const TICKET_ICON={cruiser:'c1', corvette:'c2', destroyer:'c3', colossus:'c4'};
  const TICKET_ABBR={cruiser:'CR', corvette:'CO', destroyer:'DE', colossus:'SD'};
  const ICONS={};
  const HULL_CRIT=0.25;
  let ECO={res:1.5, blur:true, rim:true, glint:true, hud:'hlp', scheme:'fire'};
  function fmtTime(t){ return '06:01'; }
  function hullCol(r){ return r>0.5 ? '#00ee55' : '#ffaa00'; }
  function isBomberHull(){ return false; }
  function allyReady(){ return true; }
  function anyTicket(){ return true; }
  function shipSwapReady(){ return true; }
  function drawSwapIcon(){}
  function drawGear(){}
  function drawPauseIcon(){}
  function drawMissileIcon(){}
  function drawBombIcon(){}
  ${themes}
  ${names.map(fn).join('\n')}
  return {get:(k)=>eval(k), set:(k,v)=>eval(k+'=v'), run:(code)=>eval(code)};`;

const W = new Function('CTX', world)(ctxStub);
let fails = 0;
function ok(label, cond){ console.log((cond ? '  ok    ' : '  FAIL  ') + label); if(!cond) fails++; }

const RECTS = ['_secBtnRect', '_allyBtnRect', '_shipBtnRect', '_settingsBtnRect', '_pauseBtnRect'];
function rects(){
  const out = {};
  for(const r of RECTS) out[r] = W.run('window.' + r);
  return out;
}

console.log('Both bars draw');
W.run("ECO.hud='classic'"); CLR(); W.run('drawHUD()');
const classicRects = rects(), classicCalls = CALLS.length;
ok('the old bar still draws', classicCalls > 50);
W.run("ECO.hud='hlp'"); CLR(); W.run('drawHUD()');
const hlpRects = rects(), hlpCalls = CALLS.length;
ok('the new bar draws', hlpCalls > 50);

console.log('\nEvery tap stays where it was');
for(const r of RECTS){
  const a = classicRects[r], b = hlpRects[r];
  ok(r.replace('_','').replace('Rect','') + ' is in the same place',
     !!a && !!b && a.x===b.x && a.y===b.y && a.w===b.w && a.h===b.h);
}

console.log('\nType comes from the theme, not from Courier');
W.run("ECO.hud='hlp'"); CLR(); W.run('drawHUD()');
ok('no Courier anywhere in the new bar', fonts().every(f=>f.indexOf('Courier')<0));
ok('Tahoma leads the label font stack', fonts().some(f=>/bold \d+px Tahoma/.test(f)));
ok('Segoe UI is used for values', fonts().some(f=>f.indexOf('Segoe UI')>=0));
W.run("ECO.hud='classic'"); CLR(); W.run('drawHUD()');
ok('the old bar still uses Courier', fonts().some(f=>f.indexOf('Courier')>=0));

console.log('\nBoth schemes resolve');
W.run("ECO.hud='hlp'; ECO.scheme='fire'");
ok('Fire glow is the forum red', W.run("TH('glow')")==='160,58,35');
W.run("ECO.scheme='void'");
ok('Void glow is the forum violet', W.run("TH('glow')")==='155,48,225');
CLR(); W.run('drawHUD()');
ok('the bar draws in Void as well', CALLS.length > 50);
ok('and its taps did not move', (()=>{
  const v = rects();
  return RECTS.every(r=>{ const a=hlpRects[r], b=v[r];
    return !!a && !!b && a.x===b.x && a.y===b.y && a.w===b.w && a.h===b.h; });
})());
W.run("ECO.scheme='fire'");
W.run("ECO.scheme='nonsense'");
ok('an unknown scheme falls back to Fire instead of breaking',
   W.run("TH('glow')")==='160,58,35');
W.run("ECO.scheme='fire'");

console.log('\nThe glow ring is the emphasis device');
CLR(); W.run("settingsOpen=false; paused=false; drawHUD()");
const calmBlur = CALLS.filter(c=>c.fn==='set shadowBlur').length;
CLR(); W.run("settingsOpen=true; paused=true; drawHUD()");
const loudBlur = CALLS.filter(c=>c.fn==='set shadowBlur').length;
ok('opening a panel adds glow rings rather than changing a border', loudBlur > calmBlur);
ok('every ring is drawn inside save/restore so its blur cannot leak', (()=>{
  let d=0, okAll=true;
  for(const c of CALLS){
    if(c.fn==='save') d++;
    else if(c.fn==='restore'){ d--; if(d<0) okAll=false; }
    else if(c.fn==='set shadowBlur' && d<1) okAll=false;
  }
  return okAll && d===0;
})());
W.run("settingsOpen=false; paused=false");

console.log('\nState colours are kept for state');
CLR(); W.run("player.hp=90; drawHUD()");
const healthy = CALLS.filter(c=>c.fn==='set fillStyle').map(c=>String(c.args[0]));
CLR(); W.run("player.hp=15; drawHUD()");
const hurt = CALLS.filter(c=>c.fn==='set fillStyle').map(c=>String(c.args[0]));
ok('a healthy hull and a critical one are not the same colour',
   healthy.indexOf('#00ee55')>=0 && hurt.indexOf('#ffaa00')>=0);
ok('the shield keeps its blue', hurt.indexOf('#0099ff')>=0);
W.run('player.hp=64');

console.log('\nNo hull icon loaded');
W.run("ECO.hud='hlp'"); CLR(); W.run('drawHUD()');
ok('the fallback life symbol is drawn instead of crashing', CALLS.length > 50);

console.log('\n' + (fails ? fails + ' FAILED' : 'all passed'));
process.exit(fails ? 1 : 0);
