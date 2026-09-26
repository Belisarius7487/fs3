#!/usr/bin/env python3
"""FS3 v144 - practice log.

    Every wave of a run is recorded: time, points won and points lost (with
    the reason: escape, jump out, protected ship lost, runner), objectives
    completed and failed, deaths with time and cause (bolt, heavy bolt,
    missile, bomb, flak, beam with the ship that fired it, ram, rock,
    debris, blast wave), tickets in and out by kind, lives and repairs
    picked up, hull and shield lost by source, kills by class, subsystems,
    bombs shot down, enemies escaped, allies and protected ships lost or
    brought through, shots and hits, secondaries, rearms, support calls,
    and a timeline of it all.

    Practice mode shows it:
      - a card at the end of every wave with the main numbers
      - PRACTICE LOG in the settings: a table of all waves of the run,
        details and timeline of the selected one, and the buttons
        COPY AS TEXT and SAVE FILE, so the whole log can be sent for
        balancing.

Needs v143. Edits src/30_waves.js, src/40_world.js, src/50_combat.js,
src/60_effects.js and src/70_ui.js in place, and writes the updated
fieldsim.js, docksim.js, shipsim.js and wpnsim.js. Run assemble.py afterwards.
"""
import sys


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def load(p):
    return open(p, encoding="utf-8").read()


wv = load("src/30_waves.js")
wo = load("src/40_world.js")
cb = load("src/50_combat.js")
fx = load("src/60_effects.js")
ui = load("src/70_ui.js")

# ══ Run and wave boundaries ═════════════════════════════════════════════
fx = replace_once(
    fx,
    "currentFaction='ntf';icenEscapes=0;runTime=0;SCENES={};",
    "currentFaction='ntf';icenEscapes=0;runTime=0;SCENES={};PLOG=[];PL=null;plogSel=-1;plogTop=0;",
    "log reset")
fx = replace_once(
    fx,
    "function nextWave(){\n",
    "function nextWave(){\n"
    "  plogEnd();              // the wave that just finished goes into the log\n",
    "log end")
fx = replace_once(
    fx,
    "  for(let i=0;i<allyWingWanted;i++){\n"
    "    const a = mkAllySmall('fighter','terran',\n",
    "  plogStart();\n"
    "  for(let i=0;i<allyWingWanted;i++){\n"
    "    const a = mkAllySmall('fighter','terran',\n",
    "log start")
fx = replace_once(
    fx,
    "  fc++;tickStars();tickParts();tickNebula();\n",
    "  fc++;tickStars();tickParts();tickNebula();\n"
    "  plogTick();\n",
    "log tick")

# ══ Deaths and where the damage came from ══════════════════════════════
fx = replace_once(
    fx,
    "function playerDie(){STATS.livesLost++;\n",
    "function playerDie(){STATS.livesLost++;\n"
    "  plogDeath();\n",
    "log death")
fx = replace_once(
    fx,
    "  player.hp=player.maxHp;player.x=80;player.y=H/2;eBullets=[];\n"
    "  // Was player.sh=100. In an era without shields that handed back\n"
    "  // something the player is not supposed to have yet.\n"
    "  resetPlayerShield();}\n",
    "  player.hp=player.maxHp;player.x=80;player.y=H/2;eBullets=[];\n"
    "  // Was player.sh=100. In an era without shields that handed back\n"
    "  // something the player is not supposed to have yet.\n"
    "  resetPlayerShield();\n"
    "  plogSync();}           // the refill is no repair\n",
    "log death sync")
fx = replace_once(
    fx,
    "        const dmg=b.dmg||(b.big?20:8);\n"
    "        if(player.sh>0){\n",
    "        const dmg=b.dmg||(b.big?20:8);\n"
    "        plogSrc(b.kind || (b.flak ? 'flak' : (b.big ? 'heavy bolt' : 'bolt')));\n"
    "        if(player.sh>0){\n",
    "src bullets")
cb = replace_once(
    cb,
    "            player.hp -= beamDmg(e, b);\n",
    "            plogSrc('beam', e);\n"
    "            player.hp -= beamDmg(e, b);\n",
    "src beam")
cb = replace_once(
    cb,
    "      if(f){ player.hp -= Math.max(1, Math.round(player.maxHp*s.pct*f)); hullHit(player.x,player.y);\n",
    "      if(f){ plogSrc('blast wave');\n"
    "             player.hp -= Math.max(1, Math.round(player.maxHp*s.pct*f)); hullHit(player.x,player.y);\n",
    "src blast")
cb = replace_once(
    cb,
    "        const dm = debRamDmg(d, player.maxHp);\n",
    "        const dm = debRamDmg(d, player.maxHp);\n"
    "        plogSrc('debris');\n",
    "src debris")
wo = replace_once(
    wo,
    "        const d = astRamDmg(a, player.maxHp);\n",
    "        const d = astRamDmg(a, player.maxHp);\n"
    "        plogSrc('rock');\n",
    "src rock")
wv = replace_once(
    wv,
    "      const dm = Math.max(1, Math.round(player.maxHp*pct));\n",
    "      const dm = Math.max(1, Math.round(player.maxHp*pct));\n"
    "      plogSrc('rammed', e);\n",
    "src ram")

# ══ Points lost, and why ════════════════════════════════════════════════
wv = replace_once(
    wv,
    "      score = Math.max(0, score - Math.round((e.pts||200)*ESCAPE_PENALTY));\n",
    "      plogLoss('escaped', e);\n"
    "      score = Math.max(0, score - Math.round((e.pts||200)*ESCAPE_PENALTY));\n",
    "loss escape")
wo = replace_once(
    wo,
    "      score = Math.max(0, score-fleePenalty(e));\n",
    "      plogLoss('jumped out', e);\n"
    "      score = Math.max(0, score-fleePenalty(e));\n",
    "loss flee")
wo = replace_once(
    wo,
    "      if(a.guard){ protLost++; guardLost = true; guardGone = true; score = Math.max(0, score-GUARD_PENALTY);\n",
    "      plogAllyLost(a);\n"
    "      if(a.guard){ plogLoss('protected ship lost', a);\n"
    "        protLost++; guardLost = true; guardGone = true; score = Math.max(0, score-GUARD_PENALTY);\n",
    "loss guard")
fx = replace_once(
    fx,
    "          score = Math.max(0, score - RUNNER_PENALTY);\n",
    "          plogLoss('runner escaped', e);\n"
    "          score = Math.max(0, score - RUNNER_PENALTY);\n",
    "loss runner")
wv = replace_once(
    wv,
    "    if(e.escWarp && _atJump){\n"
    "      if(portalOn) e.portalWarp = true;\n",
    "    if(e.escWarp && _atJump){\n"
    "      plogEvent(plogName(e)+(portalOn ? ' reached the portal' : ' reached the edge'), 'bad');\n"
    "      if(portalOn) e.portalWarp = true;\n",
    "event escape jump")

# ══ Kills, pickups, weapons ═════════════════════════════════════════════
wv = replace_once(
    wv,
    "  if(award) score += e.pts;\n"
    "  statKill(e.type);\n",
    "  if(award) score += e.pts;\n"
    "  statKill(e.type);\n"
    "  plogKill(e);\n",
    "kill 1")
wo = replace_once(
    wo,
    "      e.dead = true; score += e.pts; statKill(e.type);\n",
    "      e.dead = true; score += e.pts; statKill(e.type); plogKill(e);\n",
    "kill 2")
wo = replace_once(
    wo,
    "        if(it.kind==='repair'){\n"
    "          barPulse('hull', player.hp >= player.maxHp);\n",
    "        if(it.kind==='repair'){\n"
    "          plogPick('repair');\n"
    "          barPulse('hull', player.hp >= player.maxHp);\n",
    "pick repair")
fx = replace_once(
    fx,
    "  if(player.secAmmo<=0||player.secTimer>0) return;\n"
    "  player.secAmmo--;\n",
    "  if(player.secAmmo<=0||player.secTimer>0) return;\n"
    "  player.secAmmo--;\n"
    "  plogSec();\n",
    "sec fired")
ui = replace_once(
    ui,
    "  setRearmMenu(false);\n"
    "  rearmFull();\n",
    "  setRearmMenu(false);\n"
    "  rearmFull();\n"
    "  plogRearm();\n",
    "rearm")
wv = replace_once(
    wv,
    "  for(const k of TICKET_ORDER) tickets[k] = Math.max(tickets[k]||0, PRACTICE_TICKETS);\n",
    "  for(const k of TICKET_ORDER) tickets[k] = Math.max(tickets[k]||0, PRACTICE_TICKETS);\n"
    "  // A top-up is no ticket earned.\n"
    "  if(PL) PL._tickets = Object.assign({}, tickets);\n",
    "practice top-up not counted")

fx = replace_once(
    fx,
    "        laserHit(b.x,b.y);STATS.hits++;e.shotAt=true;damageEnemy(e,(b.dmg||22),b.x,b.y,!b.ally,'bolt');\n",
    "        laserHit(b.x,b.y);STATS.hits++;plogHit(b);e.shotAt=true;damageEnemy(e,(b.dmg||22),b.x,b.y,!b.ally,'bolt');\n",
    "hit on hull")
fx = replace_once(
    fx,
    "        STATS.hits++;\n        eBullets.splice(k,1); pBullets.splice(i,1); hit=true; break;\n",
    "        STATS.hits++; plogHit(b);\n        eBullets.splice(k,1); pBullets.splice(i,1); hit=true; break;\n",
    "hit on bomb")

# ══ Showing it ══════════════════════════════════════════════════════════
ui = replace_once(
    ui,
    "  drawFleeWarning();\n",
    "  drawFleeWarning();\n"
    "  drawPlogCard();\n",
    "card in draw")
ui = replace_once(
    ui,
    "     act:'practice', enabled:true},\n",
    "     act:'practice', enabled:true},\n"
    "    {label:'PRACTICE LOG', hint:'every wave of this run - copy it for balancing',\n"
    "     value:'OPEN', on:false, act:'plog', enabled:true},\n",
    "settings row")
ui = replace_once(
    ui,
    "function drawSettings(){\n"
    "  if(!settingsOpen) return;\n",
    "function drawSettings(){\n"
    "  if(!settingsOpen) return;\n"
    "  if(plogOpen){ drawPlog(); return; }\n",
    "settings draws log")
ui = replace_once(
    ui,
    "function settingsClick(mx,my){\n"
    "  if(!settingsOpen) return false;\n",
    "function settingsClick(mx,my){\n"
    "  if(!settingsOpen) return false;\n"
    "  if(plogOpen) return plogClick(mx, my);\n",
    "settings click log")
ui = replace_once(
    ui,
    "      else if(r.act==='practice'){ practiceMode=!practiceMode; practiceTickets(); }\n",
    "      else if(r.act==='practice'){ practiceMode=!practiceMode; practiceTickets(); }\n"
    "      else if(r.act==='plog'){ plogOpen=true; plogSel=-1; plogTop=Math.max(0, plogRows().length-PLOG_ROWS); }\n",
    "settings act log")
ui = replace_once(
    ui,
    "  if(!v) settingsPage=0;     // beim naechsten Oeffnen wieder Seite 1\n",
    "  if(!v){ settingsPage=0; plogOpen=false; }   // beim naechsten Oeffnen wieder Seite 1\n",
    "close log with settings")

# The practice log itself, at the end of the UI part.
PLOG_JS = r'''
// ── PRACTICE LOG ─────────────────────────────────────────────
// One record per wave of the run: points won and lost, objectives, deaths
// and what caused them, tickets in and out, pickups, damage by source,
// kills, losses, weapons and a timeline. Recorded in every run, shown only
// in practice mode - at the end of each wave as a card, and as a table in
// the settings, from where it can be copied or saved for balancing.
let PLOG = [], PL = null;
let plogOpen = false, plogSel = -1, plogTop = 0, plogMsg = '', plogMsgT = 0;
const PLOG_ROWS = 10;
const PLOG_STAT_KEYS = ['shots','hits','killFighter','killBomber','killCruiser','killCorvette',
  'killDestroyer','killBoss','killSentry','killFreighter','killContainer','killAsteroid',
  'subsKilled','bombsShot','scans','escortsCalled'];

function plogTime(steps){
  const s = Math.floor((steps||0)/TICK_HZ);
  return Math.floor(s/60)+':'+String(s%60).padStart(2,'0');
}
function plogName(e){
  if(!e) return '';
  if(e===player) return 'you';
  return String(e.label || (typeof shipName==='function' ? shipName(e.img, e.type||'') : e.type) || '').toUpperCase();
}
function plogEvent(txt, tone){
  if(!PL) return;
  PL.events.push({t:PL.t, txt:txt, tone:tone||'info'});
}
function plogSync(){
  if(!PL) return;
  PL._score = score; PL._lives = lives;
  PL._tickets = Object.assign({}, tickets);
  PL._hp = player.hp; PL._sh = player.sh;
}
// A new wave: the previous one is closed first.
function plogStart(){
  plogEnd();
  const def = (!FS1_MODE && !TEST_MODE && SCRIPT_WAVES[wave]) ? SCRIPT_WAVES[wave] : null;
  PL = {wave:wave, name:def ? def.name : (waveTitle || 'random wave'), scripted:!!def,
        fac:currentFaction, ship:player.ship, t:0, tEnd:null,
        gain:0, loss:0, cards:[], deaths:[], tGot:{}, tUsed:{}, picked:{},
        hull:0, shield:0, dmgBy:{}, stats0:Object.assign({}, STATS), stats:{},
        secFired:0, rearms:0, bolts:0, hits:0, allyLost:0, capLost:[], saved:0, lost:0, escaped:0,
        events:[], src:null, who:''};
  PL._card = objCard;
  plogSync();
}
function plogEnd(){
  if(!PL) return;
  plogFinish(PL);
  PLOG.push(PL);
  PL = null;
}
// The numbers that are read off the game at the end rather than counted.
function plogFinish(r){
  for(const k of PLOG_STAT_KEYS) r.stats[k] = (STATS[k]||0) - (r.stats0[k]||0);
  r.saved = protSaved; r.lost = protLost;
  r.escaped = (escGone||0) + (fleeEscaped||0);
}
// Where the next damage to the player comes from.
function plogSrc(src, who){
  if(!PL) return;
  PL.src = src; PL.who = who ? plogName(who) : '';
}
function plogLoss(why, who){
  if(!PL) return;
  PL._lossWhy = why + (who ? ' - '+plogName(who) : '');
}
function plogKill(e){
  if(!PL || !e) return;
  if(e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||e.type==='boss'||e.type==='station')
    plogEvent(plogName(e)+' destroyed (+'+(e.pts||0)+')', 'good');
}
function plogAllyLost(a){
  if(!PL || !a) return;
  PL.allyLost++;
  if(!a.small){ PL.capLost.push(plogName(a)); plogEvent(plogName(a)+' lost', 'bad'); }
}
function plogPick(kind){
  if(!PL) return;
  if(kind==='repair'){ PL.picked.repair = (PL.picked.repair||0) + 1; plogEvent('repair picked up', 'good'); }
}
function plogHit(b){ if(PL && b && !b.ally && !b.sec && !b.shard) PL.hits++; }
function plogSec(){ if(PL) PL.secFired++; }
function plogRearm(){ if(PL){ PL.rearms++; plogEvent('rearmed', 'info'); } }
function plogDeath(){
  if(!PL) return;
  const dh = PL._hp - Math.max(0, player.hp);
  if(dh>0){ PL.hull += dh; const k = PL.src || 'other'; PL.dmgBy[k] = (PL.dmgBy[k]||0) + dh; }
  const cause = (PL.src || 'unknown') + (PL.who ? ' - '+PL.who : '');
  PL.deaths.push({t:PL.t, cause:cause});
  plogEvent('died: '+cause, 'bad');
  PL.src = null; PL.who = '';
}
// Every step while a wave is played: what changed since the last one.
function plogTick(){
  if(!PL || GS!=='playing') return;
  PL.t++;
  // Bolts the player fired since the last step; secondaries and shards
  // are counted on their own.
  for(const b of pBullets) if(!b.ally && !b._pl){ b._pl = 1; if(!b.sec && !b.shard) PL.bolts++; }
  if(waveOver && PL.tEnd==null){ PL.tEnd = PL.t; plogEvent('wave clear', 'info'); }
  const ds = score - PL._score;
  if(ds>0) PL.gain += ds;
  else if(ds<0){
    PL.loss -= ds;
    plogEvent((PL._lossWhy || 'points lost')+' ('+ds+')', 'bad');
  }
  PL._lossWhy = '';
  for(const k of TICKET_ORDER){
    const d = (tickets[k]||0) - (PL._tickets[k]||0);
    if(d>0){ PL.tGot[k] = (PL.tGot[k]||0) + d; plogEvent('+'+d+' '+k+' ticket', 'good'); }
    else if(d<0){ PL.tUsed[k] = (PL.tUsed[k]||0) - d; plogEvent(d+' '+k+' ticket', 'info'); }
  }
  if(lives > PL._lives){ PL.picked.life = (PL.picked.life||0) + (lives-PL._lives); plogEvent('life picked up', 'good'); }
  const dh = PL._hp - player.hp, dsh = PL._sh - player.sh;
  if(dh>0){ PL.hull += dh; const k = PL.src || 'other'; PL.dmgBy[k] = (PL.dmgBy[k]||0) + dh; }
  if(dsh>0) PL.shield += dsh;
  if(objCard && objCard !== PL._card){
    PL.cards.push({t:PL.t, head:objCard.head, txt:objCard.txt, tone:objCard.tone});
    plogEvent(objCard.head+': '+objCard.txt, objCard.tone==='fail' ? 'bad' : (objCard.tone==='done' ? 'good' : 'info'));
  }
  PL._card = objCard;
  PL.src = null; PL.who = '';
  plogSync();
}
function plogRows(){
  const rows = PLOG.slice();
  if(PL){ const c = Object.assign({}, PL, {stats:{}}); plogFinish(c); c.running = true; rows.push(c); }
  return rows;
}
function plogSum(o){ let n = 0; for(const k in o) n += o[k]; return n; }
function plogObj(r){
  let ok = 0, bad = 0;
  for(const c of r.cards){ if(c.tone==='done') ok++; else if(c.tone==='fail') bad++; }
  return {ok:ok, bad:bad};
}
function plogKills(r){
  const s = r.stats;
  return {small:(s.killFighter||0)+(s.killBomber||0),
          cap:(s.killCruiser||0)+(s.killCorvette||0)+(s.killDestroyer||0)+(s.killBoss||0)};
}

// The whole log as plain text, for copying out of the game.
function plogText(){
  const L = [];
  L.push('FS3 '+GAME_VERSION+' - practice log - '+new Date().toISOString().replace('T',' ').substr(0,16));
  L.push('run score '+score+', lives '+lives+', ship '+player.ship);
  for(const r of plogRows()){
    const o = plogObj(r), k = plogKills(r), s = r.stats;
    L.push('');
    L.push('WAVE '+r.wave+' - '+r.name+(r.scripted?'':' (random)')+' - '+r.fac+' - ship '+r.ship+
           (r.running ? ' - still running' : ''));
    L.push('  time '+plogTime(r.tEnd!=null ? r.tEnd : r.t)+(r.tEnd!=null && r.t>r.tEnd ? ' (+'+plogTime(r.t-r.tEnd)+' until the jump)' : ''));
    L.push('  score +'+r.gain+' / -'+r.loss);
    L.push('  objectives: '+o.ok+' complete, '+o.bad+' failed'+
           (r.cards.length ? '  ['+r.cards.map(c=>c.head+': '+c.txt).join(' | ')+']' : ''));
    L.push('  deaths '+r.deaths.length+(r.deaths.length ? '  ['+r.deaths.map(d=>plogTime(d.t)+' '+d.cause).join(' | ')+']' : ''));
    L.push('  picked up: lives '+(r.picked.life||0)+', repairs '+(r.picked.repair||0));
    L.push('  tickets in '+JSON.stringify(r.tGot)+', out '+JSON.stringify(r.tUsed));
    L.push('  damage taken: hull '+Math.round(r.hull)+', shield '+Math.round(r.shield)+
           '  by source '+Object.keys(r.dmgBy).map(x=>x+' '+Math.round(r.dmgBy[x])).join(', '));
    L.push('  kills: fighters/bombers '+k.small+', capital ships '+k.cap+
           ' (cruiser '+(s.killCruiser||0)+', corvette '+(s.killCorvette||0)+', destroyer '+(s.killDestroyer||0)+
           '), sentries '+(s.killSentry||0)+', freighters '+(s.killFreighter||0)+', subsystems '+(s.subsKilled||0)+
           ', bombs shot down '+(s.bombsShot||0));
    L.push('  losses: allies '+r.allyLost+(r.capLost.length ? ' ['+r.capLost.join(', ')+']' : '')+
           ', protected lost '+r.lost+', protected through '+r.saved+', enemies escaped '+r.escaped);
    L.push('  weapons: bolts '+r.bolts+', hits '+r.hits+
           (r.bolts ? ' ('+Math.round(100*r.hits/r.bolts)+' %)' : '')+
           ', secondaries '+r.secFired+', rearms '+r.rearms+', support calls '+(s.escortsCalled||0));
    L.push('  timeline:');
    for(const ev of r.events) L.push('    '+plogTime(ev.t)+'  '+ev.txt);
  }
  return L.join('\n');
}
function plogCopy(){
  const t = plogText();
  let ok = false;
  try{
    if(navigator.clipboard && window.isSecureContext){ navigator.clipboard.writeText(t); ok = true; }
    else {
      const ta = document.createElement('textarea');
      ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      ok = document.execCommand('copy');
      document.body.removeChild(ta);
    }
  }catch(e){ ok = false; }
  plogMsg = ok ? 'COPIED - PASTE IT INTO THE CHAT' : 'COPY NOT ALLOWED HERE - USE SAVE FILE';
  plogMsgT = 240;
}
function plogSave(){
  try{
    const blob = new Blob([plogText()], {type:'text/plain'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'fs3_practice_log_'+GAME_VERSION+'_'+new Date().toISOString().substr(0,16).replace(/[:T]/g,'-')+'.txt';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function(){ URL.revokeObjectURL(a.href); }, 2000);
    plogMsg = 'SAVED';
  }catch(e){ plogMsg = 'SAVE FAILED'; }
  plogMsgT = 240;
}

// The card at the end of each wave, practice mode only.
function drawPlogCard(){
  if(!practiceMode || !PL || PL.tEnd==null || GS!=='playing') return;
  const r = Object.assign({}, PL, {stats:{}}); plogFinish(r);
  const o = plogObj(r), k = plogKills(r);
  const cw = 420, ch = 104, cx = ((W-cw)/2)|0, cy = H - ch - 14;
  ctx.save();
  thPlate(cx, cy, cw, ch, thRGBA('panelBack', 0.86), 8);
  thGlowPath(cx, cy, cw, ch, 8, 0.6);
  ctx.textAlign = 'left'; ctx.textBaseline = 'top';
  ctx.fillStyle = TH('accentWarm'); ctx.font = thLabel(11);
  ctx.fillText(thFit('WAVE '+r.wave+'  '+String(r.name).toUpperCase()+'  '+plogTime(r.tEnd), cw-24), cx+12, cy+9);
  ctx.font = thValue(11, false); ctx.fillStyle = TH('textBright');
  const col1 = cx+12, col2 = cx+cw/2+6;
  const line = function(x, y, a, b){ ctx.fillStyle = TH('text'); ctx.fillText(a, x, y);
    ctx.fillStyle = TH('textBright'); ctx.fillText(b, x+92, y); };
  line(col1, cy+30, 'SCORE', '+'+r.gain+'  / -'+r.loss);
  line(col1, cy+47, 'OBJECTIVES', o.ok+' done, '+o.bad+' failed');
  line(col1, cy+64, 'DEATHS', String(r.deaths.length));
  line(col1, cy+81, 'HULL LOST', String(Math.round(r.hull)));
  line(col2, cy+30, 'TICKETS', '+'+plogSum(r.tGot)+'  / -'+plogSum(r.tUsed));
  line(col2, cy+47, 'KILLS', k.small+' small, '+k.cap+' capital');
  line(col2, cy+64, 'PICKED UP', (r.picked.life||0)+' lives, '+(r.picked.repair||0)+' repairs');
  line(col2, cy+81, 'LOSSES', r.allyLost+' allies, '+r.lost+' protected');
  ctx.restore();
  ctx.textAlign = 'left'; ctx.textBaseline = 'top';
}

// The table, opened from the settings.
function drawPlog(){
  window._plogRects = [];
  const rows = plogRows();
  if(plogSel < 0 || plogSel >= rows.length) plogSel = rows.length-1;
  const px = 14, py = 14, pw = W-28, ph = H-28;
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,8,0.55)'; ctx.fillRect(0, 0, W, H);
  thPlate(px, py, pw, ph, thRGBA('panelBack', 0.96), 10);
  thGlowPath(px, py, pw, ph, 10, 0.7);
  ctx.textAlign = 'left'; ctx.textBaseline = 'top';
  ctx.fillStyle = TH('accentWarm'); ctx.font = thLabel(13);
  ctx.fillText('PRACTICE LOG', px+14, py+10);
  ctx.fillStyle = TH('textDim'); ctx.font = thValue(10, false);
  ctx.fillText(rows.length+' waves this run  -  tap a row for its details', px+140, py+13);
  // Columns.
  const C = [['WAVE',0],['MISSION',38],['TIME',210],['+SCORE',254],['-SCORE',314],['OBJ',370],
             ['DEATHS',420],['TICKETS',472],['KILLS',540],['HULL',600],['ESC',650],['LOST',700]];
  const tx = px+14, ty = py+34;
  ctx.fillStyle = TH('text'); ctx.font = thLabel(9);
  for(const c of C) ctx.fillText(c[0], tx+c[1], ty);
  if(plogTop > Math.max(0, rows.length-PLOG_ROWS)) plogTop = Math.max(0, rows.length-PLOG_ROWS);
  ctx.font = thValue(10, false);
  for(let i=0; i<PLOG_ROWS; i++){
    const n = plogTop + i; if(n >= rows.length) break;
    const r = rows[n], o = plogObj(r), k = plogKills(r);
    const y = ty + 16 + i*17;
    if(n===plogSel){ ctx.fillStyle = 'rgba(255,160,70,0.16)'; ctx.fillRect(tx-6, y-2, pw-16, 16); }
    const cells = [String(r.wave), thFit(String(r.name), 166)+(r.running?' *':''), plogTime(r.tEnd!=null?r.tEnd:r.t),
                   '+'+r.gain, '-'+r.loss, o.ok+' / '+o.bad, String(r.deaths.length),
                   '+'+plogSum(r.tGot)+' / -'+plogSum(r.tUsed), k.small+' / '+k.cap,
                   String(Math.round(r.hull)), String(r.escaped), String(r.allyLost+r.lost)];
    for(let c=0; c<C.length; c++){
      ctx.fillStyle = (c===5 && o.bad) || (c===6 && r.deaths.length) ? '#ff8866' : TH('textBright');
      ctx.fillText(cells[c], tx+C[c][1], y);
    }
    window._plogRects.push({x:tx-6, y:y-2, w:pw-16, h:16, act:'row', n:n});
  }
  // Scrolling, when there are more waves than rows.
  if(rows.length > PLOG_ROWS){
    const ax = px+pw-40;
    thButton(ax, ty+14, 26, 18, null); thButton(ax, ty+14+PLOG_ROWS*17-18, 26, 18, null);
    ctx.fillStyle = TH('textBright'); ctx.textAlign = 'center';
    ctx.fillText('^', ax+13, ty+17); ctx.fillText('v', ax+13, ty+14+PLOG_ROWS*17-15);
    ctx.textAlign = 'left';
    window._plogRects.push({x:ax, y:ty+14, w:26, h:18, act:'up'});
    window._plogRects.push({x:ax, y:ty+14+PLOG_ROWS*17-18, w:26, h:18, act:'down'});
  }
  // The selected wave in detail: numbers on the left, timeline on the right.
  const dy = ty + 22 + PLOG_ROWS*17;
  ctx.fillStyle = 'rgba(255,160,70,0.45)'; ctx.fillRect(px+10, dy-4, pw-20, 1);
  const r = rows[plogSel];
  if(r){
    const s = r.stats, k = plogKills(r);
    const lines = [
      'WAVE '+r.wave+'  '+String(r.name).toUpperCase()+(r.running?'  (running)':''),
      'damage: hull '+Math.round(r.hull)+', shield '+Math.round(r.shield),
      '  '+(Object.keys(r.dmgBy).map(x=>x+' '+Math.round(r.dmgBy[x])).join(', ') || 'none'),
      'deaths: '+(r.deaths.map(d=>plogTime(d.t)+' '+d.cause).join(', ') || 'none'),
      'kills: '+k.small+' small, cruiser '+(s.killCruiser||0)+', corvette '+(s.killCorvette||0)+
        ', destroyer '+(s.killDestroyer||0)+', sentry '+(s.killSentry||0),
      'subsystems '+(s.subsKilled||0)+', bombs shot down '+(s.bombsShot||0)+', escaped '+r.escaped,
      'bolts '+r.bolts+', hits '+r.hits+(r.bolts?' ('+Math.round(100*r.hits/r.bolts)+' %)':'')+
        ', secondaries '+r.secFired+', rearms '+r.rearms,
      'tickets in '+(Object.keys(r.tGot).map(x=>x+' '+r.tGot[x]).join(', ')||'-')+
        ', out '+(Object.keys(r.tUsed).map(x=>x+' '+r.tUsed[x]).join(', ')||'-'),
      'allies lost '+r.allyLost+', protected lost '+r.lost+' / through '+r.saved
    ];
    ctx.font = thValue(10, false);
    for(let i=0;i<lines.length;i++){
      ctx.fillStyle = i===0 ? TH('accentWarm') : TH('textBright');
      ctx.fillText(thFit(lines[i], 380), px+16, dy+4+i*15);
    }
    const ev = r.events.slice(-9);
    ctx.fillStyle = TH('text'); ctx.font = thLabel(9);
    ctx.fillText('TIMELINE (LAST '+ev.length+' OF '+r.events.length+')', px+410, dy+4);
    ctx.font = thValue(10, false);
    for(let i=0;i<ev.length;i++){
      ctx.fillStyle = ev[i].tone==='bad' ? '#ff8866' : (ev[i].tone==='good' ? '#7fe0a0' : TH('textBright'));
      ctx.fillText(thFit(plogTime(ev[i].t)+'  '+ev[i].txt, 340), px+410, dy+19+i*14);
    }
  }
  // Buttons.
  const by = py+ph-34, bw = 130;
  const btns = [['COPY AS TEXT','copy'],['SAVE FILE','save'],['CLOSE','close']];
  for(let i=0;i<btns.length;i++){
    const bx = px+14+i*(bw+10);
    thButton(bx, by, bw, 24, 'ready');
    ctx.fillStyle = TH('textBright'); ctx.font = thLabel(11); ctx.textAlign = 'center';
    ctx.fillText(btns[i][0], bx+bw/2, by+6);
    ctx.textAlign = 'left';
    window._plogRects.push({x:bx, y:by, w:bw, h:24, act:btns[i][1]});
  }
  if(plogMsgT > 0){
    plogMsgT--;
    ctx.fillStyle = TH('accentWarm'); ctx.font = thLabel(10);
    ctx.fillText(plogMsg, px+14+3*(bw+10)+6, by+7);
  }
  ctx.restore();
  ctx.textAlign = 'left'; ctx.textBaseline = 'top';
}
function plogClick(mx, my){
  const rs = window._plogRects || [];
  for(const r of rs){
    if(mx>=r.x && mx<=r.x+r.w && my>=r.y && my<=r.y+r.h){
      if(r.act==='row') plogSel = r.n;
      else if(r.act==='up') plogTop = Math.max(0, plogTop-1);
      else if(r.act==='down') plogTop = plogTop+1;
      else if(r.act==='copy') plogCopy();
      else if(r.act==='save') plogSave();
      else if(r.act==='close') plogOpen = false;
      return true;
    }
  }
  return true;          // a tap on the panel does not close the settings
}
'''
ui = ui.rstrip("\n") + "\n" + PLOG_JS

open("src/30_waves.js", "w", encoding="utf-8").write(wv)
open("src/40_world.js", "w", encoding="utf-8").write(wo)
open("src/50_combat.js", "w", encoding="utf-8").write(cb)
open("src/60_effects.js", "w", encoding="utf-8").write(fx)
open("src/70_ui.js", "w", encoding="utf-8").write(ui)

# -- Test files ------------------------------------------------------------
# The updated checks travel inside the patch, because .js files cannot be
# downloaded from the chat. Written last.
import base64
TEST_FILES = {
    'fieldsim.js': (
        'Ly8gRmllbGQgc2ltdWxhdGlvbjogcnVucyB0aGUgUkVBTCBnYW1lIGluIGEgaGVhZGxlc3MgYnJv'
        'd3Nlci4KLy8KLy8gVGhlIG90aGVyIHNpbXVsYXRpb25zIGxpZnQgc2luZ2xlIGZ1bmN0aW9ucyBv'
        'dXQgb2YgdGhlIGxvZ2ljIGZpbGUuIFRoaXMgb25lCi8vIGxvYWRzIHRoZSB3aG9sZSBmaWxlLCBz'
        'dGFydHMgYSByZWFsIHJ1biB3aXRoID9tPU5OIGFuZCBzdGVwcyB0aGUgcmVhbAovLyB1cGRhdGUo'
        'KSAtIHNwYXduIHF1ZXVlLCBldmVudHMsIGFsbGllZCBhbmQgZW5lbXkgZmxpZ2h0LCB0aGUgbG90'
        'LiBUaGF0IGlzCi8vIHRoZSBwYXJ0IHRoZSBvdGhlcnMgY2Fubm90IHNlZTogd2hldGhlciBhIG1p'
        'c3Npb24gYWN0dWFsbHkgcGxheXMgb3V0LgovLwovLyBObyBzcHJpdGVzIGFyZSBlbWJlZGRlZCBp'
        'biBhIGxvZ2ljIGZpbGUsIHNvIGV2ZXJ5IGh1bGwgZ2V0cyBhIHBsYWluIG9wYXF1ZQovLyBzdGFu'
        'ZC1pbiBvZiBhIGZpdHRpbmcgc2hhcGUsIGFuZCB0aGUgbW91bnQgZGF0YSBpcyBwdXQgaW4gdGhl'
        'IHdheSB0aGUKLy8gcGFja2VyIHB1dHMgaXQgaW4uIFRoZSBwbGF5ZXIgY2Fubm90IGRpZTsgdGhl'
        'IHNjZW5hcmlvcyBkZWNpZGUgd2hhdCBnZXRzCi8vIHNob3QgZG93biwgYW5kIHdoZW4uCi8vCi8v'
        'IE5lZWRzIFBsYXl3cmlnaHQgd2l0aCBDaHJvbWl1bSAoaXQgcnVucyB3aGVyZSB0aGUgYnVpbGQg'
        'aXMgY2hlY2tlZCwgbm90IG9uCi8vIHRoZSBzZXJ2ZXIpLgovLyBVc2FnZTogbm9kZSBmaWVsZHNp'
        'bS5qcyA8bG9naWMuaHRtbD4gW2hscF9tb3VudHNfZmluYWwuanNvbl0KY29uc3QgZnMgPSByZXF1'
        'aXJlKCdmcycpLCBwYXRoID0gcmVxdWlyZSgncGF0aCcpLCBvcyA9IHJlcXVpcmUoJ29zJyk7CmNv'
        'bnN0IHsgZXhlY1N5bmMgfSA9IHJlcXVpcmUoJ2NoaWxkX3Byb2Nlc3MnKTsKY29uc3QgUFcgPSBw'
        'YXRoLmpvaW4oZXhlY1N5bmMoJ25wbSByb290IC1nJykudG9TdHJpbmcoKS50cmltKCksICdwbGF5'
        'd3JpZ2h0Jyk7CmNvbnN0IHsgY2hyb21pdW0gfSA9IHJlcXVpcmUoUFcpOwoKY29uc3QgbG9naWMg'
        'PSBwcm9jZXNzLmFyZ3ZbMl07CmNvbnN0IG1vdW50cyA9IHByb2Nlc3MuYXJndlszXSB8fCAnaGxw'
        'X21vdW50c19maW5hbC5qc29uJzsKbGV0IGh0bWwgPSBmcy5yZWFkRmlsZVN5bmMobG9naWMsICd1'
        'dGY4Jyk7CmNvbnN0IE0gPSBmcy5yZWFkRmlsZVN5bmMobW91bnRzLCAndXRmOCcpOwovLyBTYW1l'
        'IHNoYXBlIGFzIGJ1aWxkX2dhbWUucHkncyByZW5kZXJfbW91bnRzKCksIHBsYWNlZCBmaXJzdCBz'
        'byBpdCBleGlzdHMKLy8gYmVmb3JlIGFueXRoaW5nIGFza3MgZm9yIGl0LgpodG1sID0gaHRtbC5y'
        'ZXBsYWNlKC88c2NyaXB0KFtePl0qKT4vLCAnPHNjcmlwdCQxPlxuY29uc3QgTU9VTlRTPScgKyBK'
        'U09OLnN0cmluZ2lmeShKU09OLnBhcnNlKE0pKSArICc7XG4nKTsKY29uc3QgdG1wID0gcGF0aC5q'
        'b2luKG9zLnRtcGRpcigpLCAnZmllbGRzaW1fJyArIHByb2Nlc3MucGlkICsgJy5odG1sJyk7CmZz'
        'LndyaXRlRmlsZVN5bmModG1wLCBodG1sKTsKCi8vIEluLXBhZ2UgaGVscGVycy4gRXZlcnl0aGlu'
        'ZyBoZXJlIHJ1bnMgYWdhaW5zdCB0aGUgZ2FtZSdzIG93biBnbG9iYWxzLgpjb25zdCBIRUxQRVJT'
        'ID0gYAogIHdpbmRvdy5GUyA9IHsKICAgIGZha2VJbWFnZXMoKXsKICAgICAgZm9yKGNvbnN0IGsg'
        'b2YgT2JqZWN0LmtleXMoSFVMTF9MRU4pKXsKICAgICAgICBjb25zdCBzbWFsbCA9IC9eKGZpfGJv'
        'fHNnfGZjfGVwKS8udGVzdChrKSAmJiBIVUxMX0xFTltrXSA8IDgwOwogICAgICAgIGNvbnN0IGMg'
        'PSBkb2N1bWVudC5jcmVhdGVFbGVtZW50KCdjYW52YXMnKTsKICAgICAgICBjLndpZHRoID0gc21h'
        'bGwgPyA2MCA6IDMyMDsgYy5oZWlnaHQgPSBzbWFsbCA/IDQwIDogOTA7CiAgICAgICAgY29uc3Qg'
        'ZyA9IGMuZ2V0Q29udGV4dCgnMmQnKTsgZy5maWxsU3R5bGUgPSAnIzg4OCc7IGcuZmlsbFJlY3Qo'
        'MCwwLGMud2lkdGgsYy5oZWlnaHQpOwogICAgICAgIElNR1Nba10gPSBjOwogICAgICB9CiAgICAg'
        'IC8vIE5vdGhpbmcgaXMgcmVhbGx5IGxvYWRlZCBmcm9tIGRpc2sgaGVyZS4gV2l0aG91dCB0aGlz'
        'IGRyYXcoKSBzdG9wcwogICAgICAvLyBhdCBpdHMgbG9hZGluZyBzY3JlZW4gYW5kIG5vbmUgb2Yg'
        'dGhlIGZpZWxkIGlzIGV2ZXIgZHJhd24uCiAgICAgIGltZ3NMb2FkZWQgPSBUT1RBTDsgbmVic0xv'
        'YWRlZCA9IDA7CiAgICB9LAogICAgc3RlcChuKXsgZm9yKGxldCBpPTA7aTxuO2krKyl7IHBsYXll'
        'ci5ocCA9IHBsYXllci5tYXhIcDsgcGxheWVyLnNoID0gcGxheWVyLm1heFNoOwogICAgICAgICAg'
        'ICAgaWYodHlwZW9mIGxpdmVzIT09J3VuZGVmaW5lZCcpIGxpdmVzID0gMzsgdXBkYXRlKCk7IGlm'
        'KGklMjU9PT0wKSBkcmF3KCk7IH0gfSwKICAgIC8vIFNob290IGRvd24gZXZlcnkgZW5lbXkgZmln'
        'aHRlciBhbmQgYm9tYmVyIHRoYXQgaXMgb3V0IG9mIGl0cyB2b3J0ZXgsCiAgICAvLyB0aGUgYm9t'
        'YnMgaW4gZmxpZ2h0IGFuZCByb2NrcyBjbG9zaW5nIG9uIGFuIGVzY29ydCAtIHdoYXQgYSBwbGF5'
        'ZXIKICAgIC8vIGRlZmVuZGluZyBvbmUgZG9lcy4KICAgIGtpbGxTbWFsbCgpeyBmb3IoY29uc3Qg'
        'ZSBvZiBlbmVtaWVzKSBpZigoZS50eXBlPT09J2ZpZ2h0ZXInfHxlLnR5cGU9PT0nYm9tYmVyJykg'
        'JiYgIShlLndhcnA+MCkpIGUuaHAgPSAwOwogICAgICAgICAgICAgICAgIGZvcihsZXQgaT1lQnVs'
        'bGV0cy5sZW5ndGgtMTtpPj0wO2ktLSkgaWYoZUJ1bGxldHNbaV0ua2luZD09PSdib21iJykgZUJ1'
        'bGxldHMuc3BsaWNlKGksMSk7CiAgICAgICAgICAgICAgICAgLy8gTG9vc2Ugcm9ja3MgYWJvdXQg'
        'dG8gaGl0IGFuIGVzY29ydCBhcyB3ZWxsLgogICAgICAgICAgICAgICAgIGZvcihjb25zdCBlIG9m'
        'IGVuZW1pZXMpIGlmKGUudHlwZT09PSdhc3Rlcm9pZCcgJiYgIWUuc2NlbmVyeSAmJgogICAgICAg'
        'ICAgICAgICAgICAgYWxsaWVzLnNvbWUoYT0+IWEuc21hbGwgJiYgTWF0aC5oeXBvdChhLngtZS54'
        'LCBhLnktZS55KSA8IDE4MCkpIGUuaHAgPSAwOyB9LAogICAga2lsbElkKGlkKXsgZm9yKGNvbnN0'
        'IGUgb2YgZW5lbWllcykgaWYoZS51aWQ9PT1pZCAmJiAhKGUud2FycD4wKSkgZS5ocCA9IDA7IH0s'
        'CiAgICAvLyBTaXQgb24gYSBwb2ludCwgdW5kaXN0dXJiZWQsIGZvciBuIHN0ZXBzOiBob3cgYSBz'
        'Y2FuIGlzIGZsb3duLgogICAgaG9sZCh4LCB5LCBuKXsgZm9yKGxldCBpPTA7aTxuO2krKyl7IHBs'
        'YXllci54ID0geDsgcGxheWVyLnkgPSB5OyBwbGF5ZXIuc2hEZWxheSA9IDA7IE1PVVNFLnggPSB4'
        'OyBNT1VTRS55ID0geTsgRlMuc3RlcCgxKTsgfSB9LAogICAgLy8gU3RlcCB1bnRpbCBjb25kKCkg'
        'aG9sZHMsIGNsZWFyaW5nIHNtYWxsIGNyYWZ0IGV2ZXJ5IHNvIG9mdGVuLgogICAgLy8gZXZlcnk6'
        'IGhvdyBvZnRlbiB0aGUgc21hbGwgY3JhZnQgYXJlIGNsZWFyZWQsIGluIHN0ZXBzIChkZWZhdWx0'
        'IDIwMCkuCiAgICB1bnRpbChjb25kLCBtYXgsIGNsZWFyLCBhbGwsIGV2ZXJ5KXsgY29uc3QgZXYg'
        'PSBldmVyeSB8fCAyMDA7CiAgICAgICAgICAgZm9yKGxldCB0PTA7dDxtYXg7dCs9MjApeyBpZihj'
        'b25kKCkpIHJldHVybiB0OwogICAgICAgICAgICAgaWYoY2xlYXIgJiYgdCVldj09PTApIEZTLmtp'
        'bGxTbWFsbCgpOwogICAgICAgICAgICAgaWYoYWxsICYmIHQlMjAwPT09MCkgZm9yKGNvbnN0IGUg'
        'b2YgZW5lbWllcyl7CiAgICAgICAgICAgICAgIGlmKGUud2FycD4wIHx8IGUuaW52dWxuIHx8IGUu'
        'c2NlbmVyeSkgY29udGludWU7CiAgICAgICAgICAgICAgIC8vIEEgcHJpemUgaXMgbm90IHNob3Qg'
        'ZG93bjogaXRzIGVuZ2luZXMgYXJlLCB0aGVuIGl0IGlzIHRha2VuLgogICAgICAgICAgICAgICBp'
        'ZihlLmNhcHR1cmVMb2NrKXsgZm9yKGNvbnN0IHMgb2YgKGUuc3Vic3x8W10pKSBpZihzLmlkPT09'
        'J2VuZ2luZXMnfHxzLmlkPT09J3dlYXBvbnMnfHxzLmlkPT09J25hdmlnYXRpb24nKXsgcy5kZWFk'
        'PXRydWU7IHMuaHA9MDsgfSBjb250aW51ZTsgfQogICAgICAgICAgICAgICAvLyBTY2FuIHRhcmdl'
        'dHMgYXJlIHNjYW5uZWQgZmlyc3QsIGFzIHRoZSBwbGF5ZXIgd291bGQuCiAgICAgICAgICAgICAg'
        'IGlmKGUuc2NhblN1YnMgJiYgIWUuc2Nhbm5lZCl7IGZvcihjb25zdCBzIG9mIGUuc3Vicykgcy5z'
        'Y2FuVCA9IDFlOTsgY29udGludWU7IH0KICAgICAgICAgICAgICAgaWYoZS5zY2FuTG9jayAmJiAh'
        'ZS5zY2FubmVkKXsgZS5zY2FubmVkID0gdHJ1ZTsgY29udGludWU7IH0KICAgICAgICAgICAgICAg'
        'ZS5ocCA9IDA7IH0KICAgICAgICAgICAgIEZTLnN0ZXAoMjApOyB9IHJldHVybiAtMTsgfSwKICAg'
        'IGlkcyhpZCl7IHJldHVybiBieUlkKGlkKTsgfSwKICAgIGVuZW15SWRzKCl7IHJldHVybiBlbmVt'
        'aWVzLm1hcChlPT5lLnVpZHx8ZS50eXBlKTsgfSwKICAgIGFsbHlJZHMoKXsgcmV0dXJuIGFsbGll'
        'cy5tYXAoYT0+YS51aWR8fGEudHlwZSk7IH0KICB9O2A7Cgpjb25zdCBzY2VuYXJpb3MgPSBbXTsK'
        'ZnVuY3Rpb24gc2NlbmFyaW8obmFtZSwgcXVlcnksIGJvZHksIG5vTGF1bmNoKXsgc2NlbmFyaW9z'
        'LnB1c2goe25hbWUsIHF1ZXJ5LCBib2R5LCBub0xhdW5jaH0pOyB9CgovLyDilIDilIAgU2NlbmFy'
        'aW9zIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgApzY2VuYXJpbygnTTMxIERlciBBdWZzdGFuZCcsICdtPTMxJywgYAogIGNvbnN0IHIg'
        'PSB7fTsKICByLndhdmUgPSB3YXZlOyByLnNoaXAgPSBwbGF5ZXIuc2hpcDsKICByLnRlcnJhbkNh'
        'bGwgPSBBTExZX0ZBQ19PTi50ZXJyYW49PT10cnVlICYmIEFMTFlfRkFDX09OLnZhc3VkYW49PT1m'
        'YWxzZTsKICBGUy5zdGVwKDQwMCk7CiAgY29uc3QgYSA9IGFsbGllcy5maW5kKHg9PngudWlkPT09'
        'J0ExJyk7CiAgci5hbGx5QXRTdGFydCA9ICEhYSAmJiBhLmltZz09PSdjcmxldmlhdGhhbic7CiAg'
        'ci5sb2NrU2V0ID0gISFhICYmIGEuZGVmZWN0TG9jaz09PXRydWU7CiAgLy8gSGFtbWVyIGhlciB3'
        'aGlsZSBzaGUgaXMgc3RpbGwgb3Vyczogc2hlIG11c3Qgbm90IGRpZSBiZWZvcmUgdGhlIHR1cm4u'
        'CiAgaWYoYSl7IGEuaHAgPSAxOyBGUy5zdGVwKDUpOyB9CiAgci5zdXJ2aXZlc0xvY2sgPSAhIWFs'
        'bGllcy5maW5kKHg9PngudWlkPT09J0ExJyk7CiAgLy8gU3RlcCBieSBzdGVwIHVwIHRvIHRoZSB0'
        'dXJuOiB3aGVyZSBzaGUgd2FzIGxhc3QgYXMgYW4gYWxseSwgYW5kIHdoZXJlCiAgLy8gc2hlIGlz'
        'IGluIHRoZSBmaXJzdCBzdGVwIGFzIGFuIGVuZW15LgogIGxldCBsYXN0ID0gbnVsbCwgZmlyc3Qg'
        'PSBudWxsOwogIGZvcihsZXQgaz0wO2s8ODAwMCAmJiAhZmlyc3Q7aysrKXsKICAgIGlmKGslMjAw'
        'PT09MCkgRlMua2lsbFNtYWxsKCk7CiAgICBjb25zdCBhbCA9IGFsbGllcy5maW5kKHg9PngudWlk'
        'PT09J0ExJyk7CiAgICBpZihhbCkgbGFzdCA9IHt4OmFsLngsIHk6YWwueX07CiAgICBGUy5zdGVw'
        'KDEpOwogICAgY29uc3QgZW4gPSBlbmVtaWVzLmZpbmQoeD0+eC51aWQ9PT0nQTEnKTsKICAgIGlm'
        'KGVuKSBmaXJzdCA9IHt4OmVuLngsIHk6ZW4ueX07CiAgfQogIHIudHVybnNJblBsYWNlID0gISFs'
        'YXN0ICYmICEhZmlyc3QgJiYgTWF0aC5hYnMoZmlyc3QueC1sYXN0LngpIDwgMiAmJiBNYXRoLmFi'
        'cyhmaXJzdC55LWxhc3QueSkgPCAyOwogIGNvbnN0IGUgPSBlbmVtaWVzLmZpbmQoeD0+eC51aWQ9'
        'PT0nQTEnKTsKICAvLyBGcm9tIGhlcmUgb24gdGhlIGFsbGllZCB3aW5ncyBjb3VsZCBzaG9vdCBo'
        'ZXIgZG93biBvciBoaXQgaGVyIGVuZ2luZXMKICAvLyBiZWZvcmUgc2hlIGdldHMgYW55d2hlcmUg'
        'LSB0aGF0IGlzIHRoZSBnYW1lIC0gc28gZm9yIHRoZSBjaGVja3MgYmVsb3cKICAvLyBzaGUgYW5k'
        'IGhlciBzdWJzeXN0ZW1zIGFyZSBtYWRlIHRvbyB0b3VnaCBmb3IgdGhlbS4KICBpZihlKXsgZS5o'
        'cCA9IGUubWF4SHAgPSAxZTc7IGZvcihjb25zdCBzIG9mIGUuc3Vic3x8W10pIHMuaHAgPSBzLm1h'
        'eEhwID0gMWU3OyB9CiAgRlMuc3RlcCg0MCk7CiAgci50dXJuZWQgPSAhIWUgJiYgIWFsbGllcy5z'
        'b21lKHg9PngudWlkPT09J0ExJyk7CiAgci5udGZIdWxsID0gISFlICYmIGUuaW1nPT09J250ZmNy'
        'bGV2aWF0aGFuJzsKICByLmVuZW15U2hhcGUgPSAhIWUgJiYgZS50eXBlPT09J2NydWlzZXInICYm'
        'IGUuc2lkZT09PSdlbmVteScgJiYgIWUuZGVhZCAmJiBlLmhwPjA7CiAgci5oYXNTdWJzID0gISFl'
        'ICYmICEhZS5zdWJzICYmIGUuc3Vicy5sZW5ndGg9PT01OwogIHIuaGFzR3VucyA9ICEhZSAmJiAh'
        'IShlLmd1bnN8fGUubW91bnRzfHxlLndwbnx8ZS5iZWFtcyk7CiAgci5mYWNlc1doZXJlU2hlR29l'
        'cyA9ICEhZSAmJiBlLmZsaXA9PT1uZWVkc0ZsaXAoZS5pbWcsIGZhbHNlKTsKICBjb25zdCB4MCA9'
        'IGUgPyBlLnggOiAwOwogIEZTLnN0ZXAoMjAwKTsKICByLndhdmVPcGVuV2hpbGVTaGVMaXZlcyA9'
        'ICF3YXZlT3ZlcjsKICByLmhlYWRzUmlnaHQgPSAhIWUgJiYgZS54ID4geDA7CiAgLy8gTGVmdCBh'
        'bG9uZSBzaGUgcmVhY2hlcyB0aGUgZWRnZSBhbmQganVtcHMuCiAgY29uc3QgdCA9IEZTLnVudGls'
        'KCgpPT4hIUVWX0xFRlRbJ0ExJ10sIDgwMDAsIHRydWUpOwogIHIuanVtcHNBdFRoZUVkZ2UgPSB0'
        'Pj0wICYmIGUud2FycE91dD4wICYmIGUueCA8IFc7CiAgci53aGlsZUZ1bGx5T25TY3JlZW4gPSAh'
        'IWUgJiYgZS54ICsgSU1HU1tlLmltZ10ud2lkdGgqZS5zYyowLjUgPD0gVzsKICBGUy51bnRpbCgo'
        'KT0+IWVuZW1pZXMuaW5jbHVkZXMoZSksIDEwMDAsIGZhbHNlKTsKICByLmdvbmVBZnRlckp1bXAg'
        'PSAhZW5lbWllcy5pbmNsdWRlcyhlKTsKICBGUy51bnRpbCgoKT0+d2F2ZU92ZXIgfHwgd2F2ZT4z'
        'MSwgNDAwMCwgdHJ1ZSk7CiAgci53YXZlRW5kcyA9IHdhdmVPdmVyIHx8IHdhdmU+MzE7CiAgcmV0'
        'dXJuIHI7YCk7CgpzY2VuYXJpbygnTTMxIGVuZ2luZXMgc3RvcCBoZXInLCAnbT0zMScsIGAKICBG'
        'Uy5zdGVwKDMwMCk7CiAgRlMudW50aWwoKCk9PiFlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nRTEn'
        'KSAmJiAhc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nRTEnKSwgNjAwMCwgdHJ1ZSk7CiAgRlMuc3Rl'
        'cCg0MCk7CiAgY29uc3QgZSA9IGVuZW1pZXMuZmluZCh4PT54LnVpZD09PSdBMScpOwogIGZvcihj'
        'b25zdCBzIG9mIGUuc3VicykgaWYocy5pZD09PSdlbmdpbmVzJyl7IHMuZGVhZCA9IHRydWU7IHMu'
        'aHAgPSAwOyB9CiAgY29uc3QgeDAgPSBlLng7IEZTLnN0ZXAoNjAwKTsKICByZXR1cm4ge3N0b3Bw'
        'ZWQ6IE1hdGguYWJzKGUueC14MCkgPCAwLjAxICYmICFFVl9MRUZUWydBMSddfTtgKTsKCnNjZW5h'
        'cmlvKCdNMzIgRGllIEZyYWNodHJvdXRlJywgJ209MzInLCBgCiAgY29uc3QgciA9IHt9OwogIEZT'
        'LnN0ZXAoMzAwKTsKICBjb25zdCBmID0gYWxsaWVzLmZpbHRlcih4PT54LnVpZD09PSdGMScpOwog'
        'IHIudHdvRnJlaWdodGVycyA9IGYubGVuZ3RoPT09MiAmJiBmLmV2ZXJ5KHg9PnguaW1nPT09J2Zy'
        'cG9zZWlkb24nKTsKICByLnRlcnJhblNpZGUgPSBmLmV2ZXJ5KHg9PnguZmFjdGlvbj09PSd0ZXJy'
        'YW4nKTsKICByLm1lZHVzYXMgPSBlbmVtaWVzLmZpbHRlcihlPT5lLnVpZD09PSdCMScpLmV2ZXJ5'
        'KGU9PmUuaW1nPT09J2JvbWVkdXNhJykgJiYgZW5lbWllcy5zb21lKGU9PmUudWlkPT09J0IxJyk7'
        'CiAgci5maWdodGVyQ292ZXIgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nRTEnICYmIGUudHlw'
        'ZT09PSdmaWdodGVyJykgfHwgc3Bhd25RLnNvbWUocT0+cS51aWQ9PT0nRTEnKTsKICBjb25zdCB4'
        'MCA9IGYubGVuZ3RoID8gZlswXS54IDogMDsgRlMuc3RlcCgzMDApOwogIHIuY3Jvc3NpbmcgPSBm'
        'Lmxlbmd0aD4wICYmIGZbMF0ueCA+IHgwOwogIEZTLnVudGlsKCgpPT4hZW5lbWllcy5zb21lKGU9'
        'PmUudWlkPT09J0IxJyksIDQwMDAsIHRydWUpOwogIEZTLnN0ZXAoMzAwKTsKICByLnNlY29uZFJh'
        'aWQgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nQjInKSB8fCBzcGF3blEuc29tZShxPT5xLnVp'
        'ZD09PSdCMicpOwogIHIuZW5kc1doZW5UaHJvdWdoID0gRlMudW50aWwoKCk9PndhdmVPdmVyLCAy'
        'MDAwMCwgdHJ1ZSkgPj0gMDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNMzMgRGllIFJlbGFp'
        'c3N0YXRpb24nLCAnbT0zMycsIGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCgzMDApOwogIGNv'
        'bnN0IHMgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nUzEnKTsKICByLmZhdXN0dXMgPSAhIXMg'
        'JiYgcy5pbWc9PT0nc2NmYXVzdHVzJzsKICByLmF0R2l2ZW5IZWlnaHQgPSAhIXMgJiYgTWF0aC5h'
        'YnMocy55LTI1MCkgPCAxOwogIGNvbnN0IHgwID0gcyA/IHMueCA6IDA7CiAgRlMuc3RlcCgxMjAw'
        'KTsKICByLnN0YXlzUHV0ID0gISFzICYmIE1hdGguYWJzKHMueC14MCkgPCAxICYmIE1hdGguYWJz'
        'KHMueS0yNTApIDwgMTsKICByLm5vRmxhayA9ICEhcyAmJiBmbGFrSGFzKHMpPT09ZmFsc2U7CiAg'
        'ci5ndW5zID0gZW5lbWllcy5maWx0ZXIoZT0+ZS51aWQ9PT0nRzEnKS5sZW5ndGg9PT00OwogIC8v'
        'IFJlaW5mb3JjZW1lbnRzIGtlZXAgY29taW5nIHdoaWxlIHNoZSBzdGFuZHMuCiAgRlMua2lsbFNt'
        'YWxsKCk7IEZTLnN0ZXAoOTAwKTsKICByLnJlaW5mb3JjZWQgPSBlbmVtaWVzLnNvbWUoZT0+ZS50'
        'eXBlPT09J2ZpZ2h0ZXInICYmICFlLnVpZCkgfHwgc3Bhd25RLnNvbWUocT0+IXEudWlkICYmIC9e'
        'ZmlfLy50ZXN0KHEudHlwZSkpOwogIGNvbnN0IGJlZm9yZSA9IFNIT0NLUy5sZW5ndGg7CiAgRlMu'
        'a2lsbElkKCdTMScpOyBGUy5zdGVwKDMpOwogIHIuYmlnQmxhc3QgPSBTSE9DS1Muc29tZShrPT5r'
        'LnJNYXg9PT0zMDApOwogIEZTLmtpbGxTbWFsbCgpOyBGUy5zdGVwKDEyMDApOyBGUy5raWxsU21h'
        'bGwoKTsgRlMuc3RlcCg2MDApOwogIHIucmVpbmZPZmYgPSBldlJlaW5mPT09ZmFsc2U7CiAgcmV0'
        'dXJuIHI7YCk7CgpzY2VuYXJpbygnTTM0IERpZSBGbGFrd2FuZCcsICdtPTM0JywgYAogIGNvbnN0'
        'IHIgPSB7fTsKICBzY29yZSA9IDIwMDAwOyAgIC8vIGVub3VnaCBmb3IgdGhlIEFydGVtaXMgdG8g'
        'YmUgb3BlbiBpbiB0aGlzIGN5Y2xlCiAgRlMuc3RlcCg0MDApOwogIGNvbnN0IGsgPSBlbmVtaWVz'
        'LmZpbHRlcihlPT5lLnVpZD09PSdLMScpOwogIHIudHdvQWVvbHVzID0gay5sZW5ndGg9PT0yICYm'
        'IGsuZXZlcnkoZT0+ZS5pbWc9PT0nbnRmY3JhZW9sdXMnKTsKICByLmZsYWsgPSBrLmV2ZXJ5KGU9'
        'PmZsYWtIYXMoZSkpOwogIHIubm9IYW5nYXJZZXQgPSAhYWxsaWVzLnNvbWUoYT0+YS51aWQ9PT0n'
        'QTEnKTsKICBGUy51bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdFMScpICYmICFz'
        'cGF3blEuc29tZShxPT5xLnVpZD09PSdFMScpLCA1MDAwLCB0cnVlKTsKICBGUy5zdGVwKDQwMCk7'
        'CiAgY29uc3QgbyA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J0ExJyk7CiAgci5vcmlvbiA9ICEh'
        'byAmJiBvLmltZz09PSdkZW9yaW9ucmlnaHQnOwogIHRpY2tTaGlwVW5sb2NrcygpOwogIHIuYm9t'
        'YmVyT2ZmZXJlZCA9IHNoaXBPZmZlcmVkKCdib2FydGVtaXMnKSAmJiBzaGlwU3dhcFJlYWR5KCk7'
        'CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTM1IERlciBVZWJlcmxhZXVmZXInLCAnbT0zNScs'
        'IGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IGQgPSBhbGxpZXMuZmlu'
        'ZChhPT5hLnVpZD09PSdBMScpOwogIHIubnRmRGVpbW9zID0gISFkICYmIGQuaW1nPT09J250ZmNv'
        'ZGVpbW9zJyAmJiBkLnR5cGU9PT0nY29ydmV0dGUnOwogIHIuY29tZXNGcm9tVGhlUmlnaHQgPSAh'
        'IWQgJiYgZC54ID4gVyowLjY7CiAgci5mYWNlc0xlZnQgPSAhIWQgJiYgZC5mbGlwPT09bmVlZHNG'
        'bGlwKCdudGZjb2RlaW1vcycsIHRydWUpOwogIHIuY3Jvc3NpbmcgPSAhIWQgJiYgZC50cmFuc2l0'
        'PT09dHJ1ZTsKICByLmZpcnN0V2luZ0h1bnRzSGVyID0gd2F2ZUh1bnQ9PT0nQTEnOwogIGNvbnN0'
        'IHgwID0gZCA/IGQueCA6IDA7IEZTLnN0ZXAoMjAwKTsKICByLmhlYWRzTGVmdCA9ICEhZCAmJiBk'
        'LnggPCB4MDsKICBGUy51bnRpbCgoKT0+IWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdFMScpICYm'
        'ICFzcGF3blEuc29tZShxPT5xLnVpZD09PSdFMScpLCA1MDAwLCB0cnVlKTsKICBGUy5zdGVwKDIw'
        'KTsKICByLnJlaW5mb3JjZW1lbnRzT24gPSBldlJlaW5mPT09dHJ1ZTsKICByLmZvbGxvd1Vwc1Nj'
        'cmVlbiA9IHdhdmVIdW50PT09Jyc7CiAgci5yZWFybSA9IGNvcnZldHRlT25GaWVsZCgpOwogIHIu'
        'bm90T25DYWxsTWVudSA9IEFMTFlfT1JERVIuaW5kZXhPZignbnRmX2RlaW1vcycpPDA7CiAgLy8g'
        'V2hhdCBpcyBjaGVja2VkIGhlcmUgaXMgdGhlIGNyb3NzaW5nLCBub3QgdGhlIGJhbGFuY2UgLSBT'
        'aWx2aW8gcGxheXMKICAvLyB0aGF0LiBTbyBzaGUgaXMgbWFkZSB0b28gdG91Z2ggdG8gbG9zZSBv'
        'biB0aGUgd2F5LgogIGQuaHAgPSBkLm1heEhwID0gMWU3OwogIGZvcihjb25zdCBzIG9mIGQuc3Vi'
        'c3x8W10pIHMuaHAgPSBzLm1heEhwID0gMWU3OyAgICAvLyBlbmdpbmVzIHRvbzogZGVhZCBlbmdp'
        'bmVzIHN0b3AgYSBjcm9zc2luZwogIGNvbnN0IGdvdCA9IEZTLnVudGlsKCgpPT57IGlmKGFsbGll'
        'cy5pbmNsdWRlcyhkKSkgZC5ocCA9IGQubWF4SHA7IHJldHVybiAhYWxsaWVzLnNvbWUoYT0+YS51'
        'aWQ9PT0nQTEnKTsgfSwgOTAwMCwgdHJ1ZSk7CiAgci5nZXRzQWNyb3NzID0gZ290Pj0wICYmICFn'
        'dWFyZExvc3Q7CiAgci5sZWZ0Q291bnRzID0gISFFVl9MRUZUWydBMSddOwogIHIubm90aGluZ01v'
        'cmVDb21lcyA9IGV2UmVpbmY9PT1mYWxzZSAmJiBzcGF3blEubGVuZ3RoPT09MDsKICBGUy51bnRp'
        'bCgoKT0+d2F2ZU92ZXIsIDQwMDAsIHRydWUpOwogIHIud2F2ZUVuZHMgPSB3YXZlT3ZlcjsKICBy'
        'ZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNMzYgRGllIEljZW5pJywgJ209MzYnLCBgCiAgY29uc3Qg'
        'ciA9IHt9OwogIGNvbnN0IHMwID0gc2NvcmUgPSA1MDAwOwogIEZTLnN0ZXAoMzAwKTsKICBjb25z'
        'dCBpID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyk7CiAgci5pY2VuaSA9ICEhaSAmJiBp'
        'LmljZW5pPT09dHJ1ZSAmJiBpLmltZz09PSdjb2ljZW5pJzsKICByLm5vTmF2aWdhdGlvbiA9ICEh'
        'aSAmJiAhIWkuc3VicyAmJiBpLnN1YnMubGVuZ3RoPT09NCAmJiBzdWJPSyhpLCduYXZpZ2F0aW9u'
        'Jyk7CiAgci5kZWFkbGluZSA9ICEhaSAmJiBpLmZsZWVUPjAgJiYgaS5mbGVlVCA8PSAyNSpUSUNL'
        'X0haOwogIEZTLnN0ZXAoNjAwKTsKICByLndob2xlSHVsbE9uU2NyZWVuID0gISFpICYmIGkueCAr'
        'IElNR1NbaS5pbWddLndpZHRoKmkuc2MqMC41IDw9IFc7CiAgY29uc3QgdCA9IEZTLnVudGlsKCgp'
        'PT4hZW5lbWllcy5zb21lKGU9PmUudWlkPT09J1YxJyksIDYwMDAsIGZhbHNlKTsKICByLmp1bXBz'
        'T3V0ID0gdD49MCAmJiBpY2VuRXNjYXBlcz09PTE7CiAgci5ub1BlbmFsdHkgPSBzY29yZSA+PSBz'
        'MDsKICByLmZlbnJpcyA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdLMScgJiYgZS5pbWc9PT0n'
        'bnRmY3JmZW5yaXMnKTsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdDeWNsZSBjaGFuZ2UgMzAg'
        'LT4gMzEnLCAnbT0zMCcsIGAKICBjb25zdCByID0ge307CiAgci5zdGFydHNWYXN1ZGFuID0gcGxh'
        'eWVyLnNoaXA9PT0nZml0b3RoJyAmJiBBTExZX0ZBQ19PTi52YXN1ZGFuPT09dHJ1ZTsKICBzY29y'
        'ZSA9IDkwMDAwOwogIC8vIENsZWFyIHdhdmUgMzAgYnkgZm9yY2UgYW5kIGxldCB0aGUganVtcCBo'
        'YXBwZW4uCiAgZm9yKGxldCBrPTA7azw2MCAmJiB3YXZlPT09MzA7aysrKXsgZm9yKGNvbnN0IGUg'
        'b2YgZW5lbWllcykgaWYoIShlLndhcnA+MCkgJiYgIWUuaW52dWxuKSBlLmhwPTA7IEZTLnN0ZXAo'
        'MjAwKTsgfQogIHIud2F2ZSA9IHdhdmU7CiAgci5teXJtaWRvbiA9IHBsYXllci5zaGlwPT09J2Zp'
        'bXlybWlkb24nOwogIHIub25lSHVsbCA9IHNoaXBVbmxvY2tlZD09PTEgJiYgY3ljbGVCYXNlPT09'
        'c2NvcmUgLSAoc2NvcmUtY3ljbGVCYXNlKTsKICByLmJhc2VTZXQgPSBjeWNsZUJhc2UgPj0gOTAw'
        'MDA7CiAgci50ZXJyYW4gPSBBTExZX0ZBQ19PTi50ZXJyYW49PT10cnVlICYmIEFMTFlfRkFDX09O'
        'LnZhc3VkYW49PT1mYWxzZTsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNMTMgYm90aCB0cmFu'
        'c3BvcnRzIG9uIHRpbWUnLCAnbT0xMycsIGAKICBGUy5zdGVwKDMwMCk7CiAgcmV0dXJuIHtib3Ro'
        'VHJhbnNwb3J0czogYWxsaWVzLmZpbHRlcihhPT5hLnVpZD09PSdUMScpLmxlbmd0aD09PTJ9O2Ap'
        'OwoKLy8gRXZlcnkgd3JpdHRlbiBtaXNzaW9uIGhhcyB0byBjb21lIHRvIGFuIGVuZCB3aGVuIGl0'
        'cyBlbmVtaWVzIGdvIGRvd24sCi8vIHdpdGggbm90aGluZyB0aHJvd24gb24gdGhlIHdheS4gRW5l'
        'bXkgc2hpcHMgYXJlIGNsZWFyZWQgZXZlcnkgdHdvIHNlY29uZHMKLy8gb25jZSB0aGV5IGFyZSBv'
        'dXQgb2YgdGhlaXIgdm9ydGV4IC0gYSBwbGF5ZXIgd2hvIGhpdHMgZXZlcnl0aGluZy4KLy8gU2Nh'
        'biBtaXNzaW9ucyAoMTIsIDIzKSBuZWVkIHRoZSBwbGF5ZXIgdG8gZmx5IHRoZSBzY2FuIGFuZCBh'
        'cmUgbGVmdCBvdXQuCmZvcihsZXQgbT0xO208PTYwO20rKykgaWYobSE9PTEyICYmIG0hPT0yMykg'
        'c2NlbmFyaW8oJ00nICsgU3RyaW5nKG0pLnBhZFN0YXJ0KDIsJzAnKSArICcgcGxheXMgdG8gdGhl'
        'IGVuZCcsICdtPScgKyBtLCBgCiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT53YXZlT3ZlciwgNDAw'
        'MDAsIGZhbHNlLCB0cnVlKTsKICBJVEVNUy5sZW5ndGggPSAwOyAgICAgLy8gcGlja3VwcyBob2xk'
        'IHRoZSBqdW1wIG9wZW4gdW50aWwgdGhleSBleHBpcmUKICBjb25zdCBqID0gRlMudW50aWwoKCk9'
        'PndhdmUgPT09ICR7bX0rMSwgNjAwMCwgZmFsc2UsIGZhbHNlKTsKICByZXR1cm4ge2VuZHM6IHQg'
        'Pj0gMCwgbmV4dFdhdmU6IGogPj0gMH07YCk7CgpzY2VuYXJpbygnUGlja3VwcyBhcmUgZHJhd24g'
        'dG8gdGhlIHNoaXAnLCAnbT0xJywgYAogIEZTLnN0ZXAoMjAwKTsKICBjb25zdCByID0ge307CiAg'
        'dGlja2V0cy5jcnVpc2VyID0gMDsKICBJVEVNUy5wdXNoKHt4OnBsYXllci54KzEwMCwgeTpwbGF5'
        'ZXIueSwgdng6SVRFTV9EUklGVCwgdnk6MCwga2luZDonY3J1aXNlcicsIGxpZmU6NTAwMH0pOwog'
        'IElURU1TLnB1c2goe3g6cGxheWVyLngrNDAwLCB5OnBsYXllci55KzEwMCwgdng6MCwgdnk6MCwg'
        'a2luZDoncmVwYWlyJywgbGlmZTo1MDAwfSk7CiAgY29uc3QgZmFyID0gSVRFTVNbMV07CiAgRlMu'
        'c3RlcCg2MCk7CiAgci5uZWFyT25lQ29sbGVjdGVkID0gdGlja2V0cy5jcnVpc2VyPT09MTsKICBy'
        'LmZhck9uZUxlZnRBbG9uZSA9IElURU1TLmluY2x1ZGVzKGZhcikgJiYgIWZhci5jYXVnaHQ7CiAg'
        'Ly8gQ2F1Z2h0LCBpdCBrZWVwcyBmb2xsb3dpbmcgZXZlbiBpZiB0aGUgc2hpcCBwdWxscyBhd2F5'
        'LgogIHBsYXllci54ID0gMTAwOyBwbGF5ZXIueSA9IDI1MDsKICBJVEVNUy5wdXNoKHt4OjIxMCwg'
        'eToyNTAsIHZ4OjAsIHZ5OjAsIGtpbmQ6J2NvcnZldHRlJywgbGlmZTo1MDAwfSk7CiAgY29uc3Qg'
        'YyA9IElURU1TW0lURU1TLmxlbmd0aC0xXTsKICBGUy5zdGVwKDEpOwogIHIuY2F1Z2h0ID0gYy5j'
        'YXVnaHQ9PT10cnVlOwogIGxldCBnb3QgPSBmYWxzZTsKICBmb3IobGV0IGs9MDtrPDIwMCAmJiAh'
        'Z290O2srKyl7IHBsYXllci54ID0gNjA7IHBsYXllci55ID0gMjUwOyBGUy5zdGVwKDEpOyBnb3Qg'
        'PSAhSVRFTVMuaW5jbHVkZXMoYyk7IH0KICByLmZvbGxvd3NBbmRBcnJpdmVzID0gZ290OwogIHJl'
        'dHVybiByO2ApOwoKc2NlbmFyaW8oJ1RpdGxlOiBmdWxsc2NyZWVuIGJ1dHRvbicsICcnLCBgCiAg'
        'Y29uc3QgciA9IHt9OwogIGxldCBjYWxscyA9IDA7CiAgdG9nZ2xlRnVsbHNjcmVlbiA9IGZ1bmN0'
        'aW9uKCl7IGNhbGxzKys7IH07CiAgZHJhdygpOwogIGNvbnN0IGIgPSB3aW5kb3cuX3RpdGxlRnNS'
        'ZWN0OwogIHIuc2hvd24gPSAhIWIgJiYgYi54ID49IDAgJiYgYi54ICsgYi53IDw9IFcgJiYgYi55'
        'ID49IDAgJiYgYi55ICsgYi5oIDw9IEg7CiAgci5jbGVhck9mVGhlVGl0bGUgPSAhIWIgJiYgYi55'
        'ICsgYi5oIDwgMTI4IC0gNTQ7CiAgY29uc3QgY3IgPSBDVlMuZ2V0Qm91bmRpbmdDbGllbnRSZWN0'
        'KCk7CiAgY29uc3QgY2xpY2sgPSAoZ3gsIGd5KT0+ewogICAgY29uc3QgZXYgPSBuZXcgTW91c2VF'
        'dmVudCgnbW91c2Vkb3duJywge2J1dHRvbjowLCBidWJibGVzOnRydWUsCiAgICAgIGNsaWVudFg6'
        'IGNyLmxlZnQgKyBneCpjci53aWR0aC9XLCBjbGllbnRZOiBjci50b3AgKyBneSpjci5oZWlnaHQv'
        'SH0pOwogICAgQ1ZTLmRpc3BhdGNoRXZlbnQoZXYpOwogICAgQ1ZTLmRpc3BhdGNoRXZlbnQobmV3'
        'IE1vdXNlRXZlbnQoJ21vdXNldXAnLCB7YnV0dG9uOjAsIGJ1YmJsZXM6dHJ1ZX0pKTsKICB9Owog'
        'IGNsaWNrKGIueCArIGIudy8yLCBiLnkgKyBiLmgvMik7CiAgci5idXR0b25Td2l0Y2hlcyA9IGNh'
        'bGxzPT09MTsKICByLmFuZERvZXNOb3RTdGFydFRoZVJ1biA9IEdTPT09J3RpdGxlJzsKICBkb2N1'
        'bWVudC5kaXNwYXRjaEV2ZW50KG5ldyBLZXlib2FyZEV2ZW50KCdrZXlkb3duJywge2NvZGU6J0tl'
        'eUYnfSkpOwogIGRvY3VtZW50LmRpc3BhdGNoRXZlbnQobmV3IEtleWJvYXJkRXZlbnQoJ2tleXVw'
        'Jywge2NvZGU6J0tleUYnfSkpOwogIHIuZktleU9uVGhlVGl0bGUgPSBjYWxscz09PTIgJiYgR1M9'
        'PT0ndGl0bGUnOwogIGNsaWNrKFcvMiwgSC8yKTsKICByLmVsc2V3aGVyZVN0YXJ0c1RoZVJ1biA9'
        'IEdTPT09J3BsYXlpbmcnICYmIGNhbGxzPT09MjsKICByZXR1cm4gcjtgLCB0cnVlKTsKCnNjZW5h'
        'cmlvKCdNMzcgRGllIFVuc2ljaHRiYXJlbicsICdtPTM3JywgYAogIGNvbnN0IHIgPSB7fTsKICBG'
        'Uy5zdGVwKDQwMCk7CiAgY29uc3QgbG9raXMgPSBlbmVtaWVzLmZpbHRlcihlPT5lLnVpZD09PSdF'
        'MScpOwogIHIubG9raXMgPSBsb2tpcy5sZW5ndGg+MCAmJiBsb2tpcy5ldmVyeShlPT5lLmltZz09'
        'PSdmaWxva2knKTsKICByLm5vTG9ja09uVGhlbSA9IGxva2lzLmxlbmd0aD4wICYmIGxva2lzLmV2'
        'ZXJ5KGU9PiFjYW5Mb2NrT24oZSkpOwogIHIuaW5QbGFpblNpZ2h0ID0gbG9raXMuZXZlcnkoZT0+'
        'IWUuaGlkZGVuICYmICFlLmNsb2FrICYmIGUuYWxwaGE9PT11bmRlZmluZWQpOwogIC8vIEFuIGVu'
        'ZW15IGZpZ2h0ZXIgb2YgYW55IG90aGVyIGh1bGwgY2FuIHN0aWxsIGJlIGxvY2tlZC4KICBjb25z'
        'dCBvdGhlciA9IHtzaWRlOidlbmVteScsIGltZzonZmloZXJjJ307CiAgci5vdGhlcnNTdGlsbExv'
        'Y2thYmxlID0gY2FuTG9ja09uKG90aGVyKTsKICAvLyBBIHBsYXllciBMb2tpIGxhdGVyIG9uIGtl'
        'ZXBzIGl0cyBvd24gcnVsZXM6IHRoZSBuby1sb2NrIGlzIGVuZW15IG9ubHkuCiAgci5vbmx5VGhl'
        'RW5lbXlTaWRlID0gY2FuTG9ja09uKHtzaWRlOidhbGx5JywgaW1nOidmaWxva2knfSk7CiAgLy8g'
        'Q2xlYXIgdGhlbSBsb3QgYnkgbG90IGFuZCBub3RlIGV2ZXJ5IGxvdCB0aGF0IHNob3dzIHVwLgog'
        'IGNvbnN0IHNlZW4gPSB7fTsKICBGUy51bnRpbCgoKT0+eyBmb3IoY29uc3QgZSBvZiBlbmVtaWVz'
        'KSBpZihlLnVpZCl7IHNlZW5bZS51aWRdID0gc2VlbltlLnVpZF0gfHwgZS5pbWc7IH0gcmV0dXJu'
        'IHdhdmVPdmVyOyB9LCAyMDAwMCwgdHJ1ZSk7CiAgci50aHJlZUxvdHNPZkxva2lzID0gc2Vlbi5F'
        'MT09PSdmaWxva2knICYmIHNlZW4uRTI9PT0nZmlsb2tpJyAmJiBzZWVuLkUzPT09J2ZpbG9raSc7'
        'CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTM4IERpZSBLYXBlcnVuZycsICdtPTM4JywgYAog'
        'IGNvbnN0IHIgPSB7fTsKICBzY29yZSA9IDEwMDA7CiAgRlMuc3RlcCg0MDApOwogIGNvbnN0IGQg'
        'PSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nRDEnKTsKICByLmRlaW1vcyA9ICEhZCAmJiBkLmlt'
        'Zz09PSdudGZjb2RlaW1vcyc7CiAgci5taWRGaWVsZCA9ICEhZCAmJiBNYXRoLmFicyhkLnktMjYw'
        'KSA8IDE7CiAgci5oZWFkc1JpZ2h0ID0gISFkICYmIGQuZXNjYXBpbmc+MCAmJiBkLmZsaXA9PT1u'
        'ZWVkc0ZsaXAoZC5pbWcsIGZhbHNlKTsKICByLnNheXNXaGF0VG9EbyA9IG1pc3Npb25PYmo9PT0n'
        'RElTQUJMRSBUSEUgREVJTU9TIC0gRU5HSU5FUyBBTkQgV0VBUE9OUyc7CiAgZGFtYWdlRW5lbXko'
        'ZCwgZC5tYXhIcCo1LCBkLngsIGQueSwgdHJ1ZSwgJ2JvbHQnKTsgRlMuc3RlcCgzKTsKICByLmNh'
        'bm5vdEJlRGVzdHJveWVkID0gZW5lbWllcy5pbmNsdWRlcyhkKSAmJiBkLmhwID4gMDsKICBjb25z'
        'dCBraWxsID0gaWQ9PnsgZm9yKGNvbnN0IHMgb2YgZC5zdWJzKSBpZihzLmlkPT09aWQpeyBzLmRl'
        'YWQ9dHJ1ZTsgcy5ocD0wOyB9IH07CiAga2lsbCgnZW5naW5lcycpOwogIGNvbnN0IHgwID0gZC54'
        'OyBGUy5zdGVwKDMwMCk7CiAgci5lbmdpbmVzU3RvcEhlciA9IE1hdGguYWJzKGQueC14MCkgPCAw'
        'LjAxOwogIHIubm9FbHlzaXVtV2hpbGVIZXJHdW5zV29yayA9ICFhbGxpZXMuc29tZShhPT5hLnVp'
        'ZD09PSdUMScpICYmICFzcGF3blEuc29tZShxPT5xLnVpZD09PSdUMScpOwogIGtpbGwoJ3dlYXBv'
        'bnMnKTsgRlMuc3RlcCgyKTsKICByLm5ld09iamVjdGl2ZSA9IG1pc3Npb25PYmo9PT0nQ09WRVIg'
        'VEhFIEVMWVNJVU0nOwogIEZTLnN0ZXAoMjAwKTsKICByLmVseXNpdW1Db21lc09uY2VCb3RoQXJl'
        'RG93biA9IGFsbGllcy5zb21lKGE9PmEudWlkPT09J1QxJyAmJiBhLmltZz09PSd0cmVseXNpdW0n'
        'KSB8fCBzcGF3blEuc29tZShxPT5xLnVpZD09PSdUMScpIHx8ICEhRVZfRE9DS1snVDEnXTsKICBj'
        'b25zdCBnb3QgPSBGUy51bnRpbCgoKT0+ISFFVl9ET0NLWydUMSddLCA5MDAwLCB0cnVlKTsKICBG'
        'Uy5zdGVwKDUpOwogIHIuZG9ja3MgPSBnb3Q+PTA7CiAgci50YWtlbiA9IGQuY2FwdHVyZWQ9PT10'
        'cnVlICYmICEhRVZfVEFLRU5bJ0QxJ10gJiYgKGQud2FycE91dD4wIHx8ICFlbmVtaWVzLmluY2x1'
        'ZGVzKGQpKTsKICByLmNvbXBsZXRlQ2FyZCA9ICEhb2JqQ2FyZCAmJiBvYmpDYXJkLmhlYWQ9PT0n'
        'T0JKRUNUSVZFIENPTVBMRVRFJyAmJiBvYmpDYXJkLnR4dD09PSdERUlNT1MgQ0FQVFVSRUQnOwog'
        'IHIucG9pbnRzRm9ySGVyID0gc2NvcmUgPj0gMTAwMCArIChkLnB0c3x8MCk7CiAgRlMudW50aWwo'
        'KCk9PiFlbmVtaWVzLmluY2x1ZGVzKGQpLCAxMDAwLCBmYWxzZSk7CiAgRlMuc3RlcCg1MCk7CiAg'
        'ci5ub0ZhaWx1cmVBZnRlcndhcmRzID0gIShvYmpDYXJkICYmIG9iakNhcmQudG9uZT09PSdmYWls'
        'Jyk7CiAgci5sZWF2ZXNXaXRob3V0UGVuYWx0eSA9ICFlbmVtaWVzLmluY2x1ZGVzKGQpICYmIHNj'
        'b3JlID49IDEwMDAgKyAoZC5wdHN8fDApOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ00zOCBF'
        'bHlzaXVtIGxvc3Q6IHNoZSBjYW4gZGllJywgJ209MzgnLCBgCiAgRlMuc3RlcCg0MDApOwogIGNv'
        'bnN0IGQgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nRDEnKTsKICBmb3IoY29uc3QgcyBvZiBk'
        'LnN1YnMpIGlmKHMuaWQ9PT0nZW5naW5lcyd8fHMuaWQ9PT0nd2VhcG9ucycpeyBzLmRlYWQ9dHJ1'
        'ZTsgcy5ocD0wOyB9CiAgRlMudW50aWwoKCk9PmFsbGllcy5zb21lKGE9PmEudWlkPT09J1QxJyks'
        'IDIwMDAsIHRydWUpOwogIGZvcihjb25zdCBhIG9mIGFsbGllcykgaWYoYS51aWQ9PT0nVDEnKSBh'
        'LmhwID0gMDsKICBGUy5zdGVwKDMwKTsKICBjb25zdCBmcmVlZCA9IGQuY2FwdHVyZUxvY2s9PT1m'
        'YWxzZTsKICBjb25zdCBmYWlsQ2FyZCA9ICEhb2JqQ2FyZCAmJiBvYmpDYXJkLnRvbmU9PT0nZmFp'
        'bCcgJiYgb2JqQ2FyZC50eHQ9PT0nRUxZU0lVTSBMT1NUJzsKICBkLmhwID0gMDsgRlMuc3RlcCgz'
        'MDApOwogIHJldHVybiB7ZnJlZWQ6IGZyZWVkLCBmYWlsQ2FyZDogZmFpbENhcmQsIHRoZW5EZXN0'
        'cm95YWJsZTogIWVuZW1pZXMuaW5jbHVkZXMoZCkgJiYgIUVWX0xFRlRbJ0QxJ119O2ApOwoKc2Nl'
        'bmFyaW8oJ00zOCBsZWZ0IGFsb25lIHNoZSBqdW1wcyBhdCB0aGUgZWRnZScsICdtPTM4JywgYAog'
        'IEZTLnN0ZXAoMzAwKTsKICBjb25zdCBkID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J0QxJyk7'
        'CiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT4hIUVWX0xFRlRbJ0QxJ10sIDgwMDAsIHRydWUpOwog'
        'IEZTLnN0ZXAoMik7CiAgcmV0dXJuIHtqdW1wczogdD49MCAmJiBkLndhcnBPdXQ+MCAmJiAhZC5j'
        'YXB0dXJlZCwgb25TY3JlZW46IGQueCArIElNR1NbZC5pbWddLndpZHRoKmQuc2MqMC41IDw9IFcs'
        'CiAgICAgICAgICBmYWlsQ2FyZDogISFvYmpDYXJkICYmIG9iakNhcmQudG9uZT09PSdmYWlsJyAm'
        'JiBvYmpDYXJkLnR4dD09PSdUSEUgREVJTU9TIEdPVCBBV0FZJ307YCk7CgpzY2VuYXJpbygnTTM5'
        'IERpZSBHYXNlcm50ZScsICdtPTM5JywgYAogIGNvbnN0IHIgPSB7fTsKICByLm5lYnVsYSA9IG5l'
        'YnVsYU9uKCk9PT10cnVlOwogIEZTLnN0ZXAoMTYwMCk7CiAgY29uc3QgbSA9IGVuZW1pZXMuZmls'
        'dGVyKGU9Pi9eTS8udGVzdChlLnVpZHx8JycpKTsKICByLnRocmVlTWluZXJzID0gbS5sZW5ndGg9'
        'PT0zICYmIG0uZXZlcnkoZT0+ZS5pbWc9PT0nZ216ZXBoeXJ1cycpOwogIHIucnVubmluZyA9IG0u'
        'ZXZlcnkoZT0+ZS5lc2NhcGluZz4wKTsKICByLmZlbnJpcyA9IGVuZW1pZXMuc29tZShlPT5lLnVp'
        'ZD09PSdLMScgJiYgZS5pbWc9PT0nbnRmY3JmZW5yaXMnKTsKICBjb25zdCBtMSA9IGVuZW1pZXMu'
        'ZmluZChlPT5lLnVpZD09PSdNMScpOwogIG0xLmhwID0gMDsgRlMuc3RlcCgzKTsKICByLmdpYW50'
        'Qmxhc3QgPSBTSE9DS1Muc29tZShrPT5rLnJNYXg9PT00MDApOwogIHJldHVybiByO2ApOwoKc2Nl'
        'bmFyaW8oJ000MCBEZXIgU2Vuc29yc3R1cm0nLCAnbT00MCcsIGAKICBjb25zdCByID0ge307CiAg'
        'ci5uZWJ1bGEgPSBuZWJ1bGFPbigpPT09dHJ1ZTsKICBjb25zdCBzZWVuID0ge307CiAgY29uc3Qg'
        'bm90ZSA9ICgpPT57IGZvcihjb25zdCBlIG9mIGVuZW1pZXMpIGlmKGUudWlkKSBzZWVuW2UudWlk'
        'XT0xOyB9OwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+eyBub3RlKCk7IHJldHVybiBlbXBPdXQ+'
        'MDsgfSwgNjAwMCwgdHJ1ZSk7CiAgci5zdG9ybUhpdHMgPSB0Pj0wOwogIHIubm9Mb2NrSW5UaGVT'
        'dG9ybSA9ICFjYW5Mb2NrT24oe3NpZGU6J2VuZW15JywgaW1nOidmaWhlcmNtazInfSk7CiAgci5v'
        'cmlvbiA9IGFsbGllcy5zb21lKGE9PmEudWlkPT09J0ExJyAmJiBhLmltZz09PSdkZW9yaW9ucmln'
        'aHQnKTsKICBGUy51bnRpbCgoKT0+eyBub3RlKCk7IHJldHVybiB3YXZlT3ZlcjsgfSwgNDAwMDAs'
        'IHRydWUpOwogIHIudGhyZWVSb3VuZHMgPSBbJ0UxJywnQjEnLCdFMicsJ0IyJywnRTMnLCdCMydd'
        'LmV2ZXJ5KGs9PnNlZW5ba10pOwogIGlmKCFyLnRocmVlUm91bmRzKSByLnNlZW4gPSBPYmplY3Qu'
        'a2V5cyhzZWVuKS5qb2luKCkgKyAnIHwgJyArIEVWLm1hcChlPT5lLmErJz4nK2UudysnPicrKGUu'
        'd2F8fCcnKSsnOicrZS5kb25lKS5qb2luKCcgJyk7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygn'
        'TTQxIERhcyBMYXphcmV0dCcsICdtPTQxJywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDMw'
        'MCk7CiAgY29uc3QgaCA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J0gxJyk7CiAgci5oaXBwb2Ny'
        'YXRlcyA9ICEhaCAmJiBoLmltZz09PSdtZWhpcHBvY3JhdGVzJzsKICByLmh1bnRlZCA9IHdhdmVI'
        'dW50PT09J0gxJzsKICBjb25zdCB4MCA9IGggPyBoLnggOiAwOyBGUy5zdGVwKDMwMCk7CiAgci5j'
        'cm9zc2VzU2xvd2x5ID0gISFoICYmIGgueCA+IHgwICYmIChoLngteDApIDwgMTAwOwogIHIuYm9t'
        'YmVycyA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdCMScgJiYgZS5pbWc9PT0nYm9tZWR1c2En'
        'KTsKICBjb25zdCBvcmlnID0gZHJhd0h1bGxCbG9ja3M7IGxldCBiYXJGb3IgPSBmYWxzZTsKICBk'
        'cmF3SHVsbEJsb2NrcyA9IGZ1bmN0aW9uKGUpeyBpZihlPT09aCkgYmFyRm9yID0gdHJ1ZTsgcmV0'
        'dXJuIG9yaWcuYXBwbHkodGhpcywgYXJndW1lbnRzKTsgfTsKICBkcmF3KCk7IGRyYXdIdWxsQmxv'
        'Y2tzID0gb3JpZzsKICByLmh1bGxCYXJPblRoZUhpcHBvY3JhdGVzID0gYmFyRm9yOwogIGNvbnN0'
        'IGdvdCA9IEZTLnVudGlsKCgpPT4hYWxsaWVzLmluY2x1ZGVzKGgpLCA5MDAwLCB0cnVlKTsKICBy'
        'LmdldHNUaHJvdWdoID0gZ290Pj0wICYmICFndWFyZExvc3Q7CiAgcmV0dXJuIHI7YCk7CgpzY2Vu'
        'YXJpbygnTTQyIERpZSBIZWNhdGUnLCAnbT00MicsIGAKICBjb25zdCByID0ge307CiAgRlMuc3Rl'
        'cCg0MDApOyBkcmF3KCk7CiAgci5zYXlzV2hhdFRvRG8gPSBtaXNzaW9uT2JqPT09J0RJU0FCTEUg'
        'SEVDQVRFIFdFQVBPTlMnICYmIG9ialBpbm5lZD09PSdESVNBQkxFIEhFQ0FURSBXRUFQT05TJzsK'
        'ICBjb25zdCB2ID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyk7CiAgci5oZWNhdGUgPSAh'
        'IXYgJiYgdi5pbWc9PT0nbnRmZGVoZWNhdGUnOwogIHIub3Jpb24gPSBhbGxpZXMuc29tZShhPT5h'
        'LnVpZD09PSdBMScpOwogIEZTLnVudGlsKCgpPT4hZW5lbWllcy5zb21lKGU9PmUudWlkPT09J0Ux'
        'JykgJiYgIXNwYXduUS5zb21lKHE9PnEudWlkPT09J0UxJyksIDUwMDAsIHRydWUpOwogIEZTLnN0'
        'ZXAoMjApOwogIHIucmVpbmZvcmNlbWVudHNPbiA9IGV2UmVpbmY9PT10cnVlOwogIGZvcihjb25z'
        'dCBzIG9mIHYuc3VicykgaWYocy5pZD09PSd3ZWFwb25zJyl7IHMuZGVhZD10cnVlOyBzLmhwPTA7'
        'IH0KICBGUy5zdGVwKDIwKTsgZHJhdygpOwogIHIubmV4dFN0ZXAgPSBtaXNzaW9uT2JqPT09J0RF'
        'U1RST1kgVEhFIEhFQ0FURScgJiYgISFvYmpDYXJkICYmIG9iakNhcmQuaGVhZD09PSdORVcgT0JK'
        'RUNUSVZFJyAmJiBvYmpDYXJkLnR4dD09PSdERVNUUk9ZIFRIRSBIRUNBVEUnOwogIHIuZGlzYXJt'
        'ZWRXaXRoZHJhd3MgPSB2LmZsZWVUPjA7CiAgLy8gQSBkZXN0cm95ZXIgZ29lcyBkb3duIGluIGEg'
        'ZGVhdGggcm9sbCB0aGF0IHRha2VzIGEgd2hpbGUuCiAgdi5ocCA9IDA7CiAgci5jb21wbGV0ZUNh'
        'cmQgPSBGUy51bnRpbCgoKT0+eyBkcmF3KCk7IHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC5o'
        'ZWFkPT09J09CSkVDVElWRSBDT01QTEVURScKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg'
        'ICAgICAgICAgICAgJiYgb2JqQ2FyZC50eHQ9PT0nSEVDQVRFIERFU1RST1lFRCc7IH0sIDIwMDAs'
        'IGZhbHNlKSA+PSAwOwogIEZTLnN0ZXAoMzAwKTsKICByLnJlaW5mb3JjZW1lbnRzT2ZmV2hlblNo'
        'ZXNHb25lID0gZXZSZWluZj09PWZhbHNlOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000MiBz'
        'aGUgd2l0aGRyYXdzOiBmYWlsZWQnLCAnbT00MicsIGAKICBGUy5zdGVwKDQwMCk7CiAgY29uc3Qg'
        'diA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdWMScpOwogIC8vIFRvbyB0b3VnaCBmb3IgdGhl'
        'IE9yaW9uIGFuZCBoZXIgd2luZ3MsIGFuZCBoZXIgbmF2aWdhdGlvbiB3aXRoIGl0IC0KICAvLyB3'
        'aXRoIHRoYXQgc2hvdCBvdXQgc2hlIGNvdWxkIG5vdCBqdW1wIGF0IGFsbC4KICB2LmhwID0gdi5t'
        'YXhIcCA9IDFlNzsKICBmb3IoY29uc3QgcyBvZiB2LnN1YnMpeyBpZihzLmlkPT09J3dlYXBvbnMn'
        'KXsgcy5kZWFkPXRydWU7IHMuaHA9MDsgfSBlbHNlIHMuaHAgPSBzLm1heEhwID0gMWU3OyB9CiAg'
        'Y29uc3QgdCA9IEZTLnVudGlsKCgpPT4hIW9iakNhcmQgJiYgb2JqQ2FyZC50b25lPT09J2ZhaWwn'
        'LCA2MDAwLCB0cnVlKTsKICBjb25zdCByID0ge2ZhaWxDYXJkOiB0Pj0wICYmIG9iakNhcmQudHh0'
        'PT09J1RIRSBIRUNBVEUgV0lUSERSRVcnLCBub3RDb21wbGV0ZTogIShvYmpDYXJkICYmIG9iakNh'
        'cmQudG9uZT09PSdkb25lJyl9OwogIEZTLnVudGlsKCgpPT4hZW5lbWllcy5pbmNsdWRlcyh2KSwg'
        'MTAwMCwgZmFsc2UpOyBGUy5zdGVwKDUwKTsKICByLnJlaW5mT2ZmID0gZXZSZWluZj09PWZhbHNl'
        'OwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ00zMyBzYXlzIHdoYXQgdG8gZG8nLCAnbT0zMycs'
        'IGAKICBGUy5zdGVwKDMwMCk7CiAgY29uc3Qgb2sxID0gbWlzc2lvbk9iaj09PSdERVNUUk9ZIFRI'
        'RSBGQVVTVFVTIFJFTEFZJzsKICBjb25zdCBzMSA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdT'
        'MScpOyBzMS5ocCA9IDA7IEZTLnN0ZXAoNSk7CiAgcmV0dXJuIHtzYXlzV2hhdFRvRG86IG9rMSwg'
        'Y29tcGxldGVDYXJkOiAhIW9iakNhcmQgJiYgb2JqQ2FyZC5oZWFkPT09J09CSkVDVElWRSBDT01Q'
        'TEVURScgJiYgb2JqQ2FyZC50eHQ9PT0nUkVMQVkgREVTVFJPWUVEJ307YCk7CgpzY2VuYXJpbygn'
        'QXV0b21hdGljIG9iamVjdGl2ZXM6IGNhcmQsIHRoZW4gdGhlIGxpbmUnLCAnbT0zNScsIGAKICAv'
        'LyBNMzUgc3RhdGVzIG5vIG9iamVjdGl2ZSBvZiBpdHMgb3duOyBQUk9URUNUIFRIRSAuLi4gY29t'
        'ZXMgZnJvbSB0aGUgZmllbGQuCiAgY29uc3QgciA9IHt9OwogIGNvbnN0IHQgPSBGUy51bnRpbCgo'
        'KT0+eyBkcmF3KCk7IHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC5oZWFkPT09J05FVyBPQkpF'
        'Q1RJVkUnOyB9LCAxNTAwLCBmYWxzZSk7CiAgci5jYXJkRm9yVGhlTmV3T2JqZWN0aXZlID0gdD49'
        'MCAmJiAvXlBST1RFQ1QgVEhFIC8udGVzdChvYmpDYXJkLnR4dCk7CiAgLy8gSXRzIGNsb2NrIHN0'
        'YXJ0cyBvbmNlIHRoZSBqdW1wIGluIGlzIG92ZXIsIHNvIHdhaXQgZm9yIGl0IHJhdGhlciB0aGFu'
        'CiAgLy8gY291bnQgc3RlcHMuCiAgci5jYXJkR29lc0FnYWluID0gRlMudW50aWwoKCk9PnsgZHJh'
        'dygpOyByZXR1cm4gb2JqQ2FyZD09PW51bGw7IH0sIE9CSl9DQVJEX1RJTUUqMywgZmFsc2UpID49'
        'IDA7CiAgci5saW5lS2VlcHNJdCA9IC9eUFJPVEVDVCBUSEUgLy50ZXN0KG9ialBpbm5lZCk7CiAg'
        'cmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTmV3IGxvb2s6IG5vIENvdXJpZXIgbGVmdCBpbiB0aGVz'
        'ZScsICdtPTM2JywgYAogIEZTLnN0ZXAoNzAwKTsKICBzaG93RnBzID0gdHJ1ZTsgc2hvd09iaiA9'
        'IHRydWU7CiAgY29uc3QgdXNlZCA9IFtdOyBjb25zdCBvZiA9IGN0eC5maWxsVGV4dDsKICBsZXQg'
        'aW5zaWRlID0gMDsKICBjb25zdCB3cmFwID0gbmFtZT0+eyBjb25zdCBmID0gd2luZG93W25hbWVd'
        'OyB3aW5kb3dbbmFtZV0gPSBmdW5jdGlvbigpeyBpbnNpZGUrKzsgdHJ5eyByZXR1cm4gZi5hcHBs'
        'eSh0aGlzLCBhcmd1bWVudHMpOyB9IGZpbmFsbHl7IGluc2lkZS0tOyB9IH07IH07CiAgWydkcmF3'
        'RmllbGRCYW5uZXInLCdkcmF3RmxlZVdhcm5pbmcnLCdkcmF3RnBzJywnZHJhd09iakNvdW50Jywn'
        'ZHJhd1BhdXNlZCcsCiAgICdkcmF3U3ViTXNncycsJ2RyYXdUaWNrZXRNc2dzJywnZHJhd0l0ZW1z'
        'JywnZHJhd0h1bGxCbG9ja3MnLCdkcmF3U3Vic3lzdGVtcyddLmZvckVhY2god3JhcCk7CiAgLy8g'
        'U29tZXRoaW5nIGluIGVhY2ggb2YgdGhlbSB0byBkcmF3LgogIGNvbnN0IGNhcCA9IGVuZW1pZXMu'
        'ZmluZChlPT5lLnR5cGU9PT0nY3J1aXNlcid8fGUudHlwZT09PSdjb3J2ZXR0ZScpIHx8IGVuZW1p'
        'ZXNbMF07CiAgU1VCX01TR1MucHVzaCh7eDozMDAsIHk6MjUwLCB0eHQ6J0RPQ0tFRCcsIGxpZmU6'
        'MTUwLCBtbDoxNTAsIGFsbHk6dHJ1ZSwgdG9uZTonZ29vZCd9KTsKICBUSUNLRVRfTVNHUy5wdXNo'
        'KHt4OjMyMCwgeToyNjAsIGtpbmQ6J2NydWlzZXInLCBsaWZlOjE1MCwgbWw6MTUwLCByZXA6ZmFs'
        'c2V9KTsKICBJVEVNUy5wdXNoKHt4OjM0MCwgeToyNzAsIHZ4OjAsIHZ5OjAsIGtpbmQ6J2xpZmUn'
        'LCBsaWZlOjUwMH0pOwogIElURU1TLnB1c2goe3g6MzYwLCB5OjI3MCwgdng6MCwgdnk6MCwga2lu'
        'ZDonY29ydmV0dGUnLCBsaWZlOjUwMH0pOwogIG5vdGljZSgnVEVTVCBOT1RJQ0UnLCAnaW5mbycp'
        'OwogIGN0eC5maWxsVGV4dCA9IGZ1bmN0aW9uKCl7IGlmKGluc2lkZSkgdXNlZC5wdXNoKGN0eC5m'
        'b250KTsgcmV0dXJuIG9mLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07CiAgb2JqQW5ub3VuY2Uo'
        'J05FVyBPQkpFQ1RJVkUnLCAnVEVTVCcsICduZXcnKTsgb2JqQ2FyZC50MCA9IGZjIC0gNDA7CiAg'
        'ZHJhdygpOwogIHVzZXJQYXVzZWQgPSB0cnVlOyBzeW5jUGF1c2UoKTsgZHJhdygpOwogIGN0eC5m'
        'aWxsVGV4dCA9IG9mOwogIHJldHVybiB7c29tZXRoaW5nRHJhd246IHVzZWQubGVuZ3RoPj00LCBm'
        'bGVlU2hvd246IGZsZWVpbmdFbmVtaWVzKCkubGVuZ3RoPjAsIG5vQ291cmllcjogdXNlZC5ldmVy'
        'eShmPT4hL0NvdXJpZXIvLnRlc3QoZikpfTtgKTsKCnNjZW5hcmlvKCdOb3RpY2VzOiBhIGNvbHVt'
        'biwgbm90IHRoZSBmaWVsZCcsICdtPTMxJywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDMw'
        'MCk7CiAgc2NvcmUgPSBjeWNsZUJhc2UgKyA0MDAwOyB0aWNrU2hpcFVubG9ja3MoKTsKICByLnVu'
        'bG9ja0lzQU5vdGljZSA9IE5PVElDRVMubGVuZ3RoPjAgJiYgTk9USUNFU1swXS50eHQ9PT0nR1RG'
        'IEhFUkNVTEVTIEFWQUlMQUJMRScgJiYgTk9USUNFU1swXS50b25lPT09J3VubG9jayc7CiAgci5u'
        'b3RJblRoZUZpZWxkID0gIVNVQl9NU0dTLnNvbWUobT0+L0FWQUlMQUJMRS8udGVzdChtLnR4dCkp'
        'OwogIGNvbnN0IHBsYXRlcyA9IFtdOyBjb25zdCBvcCA9IHRoUGxhdGU7CiAgdGhQbGF0ZSA9IGZ1'
        'bmN0aW9uKHgseSx3LGgpeyBwbGF0ZXMucHVzaCh7eCx5LHcsaH0pOyByZXR1cm4gb3AuYXBwbHko'
        'dGhpcywgYXJndW1lbnRzKTsgfTsKICBkcmF3KCk7IHRoUGxhdGUgPSBvcDsKICByLm9uVGhlTGVm'
        'dFVuZGVyVGhlQmFyID0gcGxhdGVzLnNvbWUocD0+cC54PT09OCAmJiBwLnk+PUhVRF9IKzYgJiYg'
        'cC5oPT09MTgpOwogIGZvcihsZXQgaT0wO2k8NTtpKyspIG5vdGljZSgnTicraSwgJ2luZm8nKTsK'
        'ICByLmF0TW9zdFRocmVlTmV3ZXN0Rmlyc3QgPSBOT1RJQ0VTLmxlbmd0aD09PTMgJiYgTk9USUNF'
        'U1swXS50eHQ9PT0nTjQnICYmIE5PVElDRVNbMl0udHh0PT09J04yJzsKICBGUy5zdGVwKE5PVElD'
        'RV9USU1FKzMwKTsgZHJhdygpOwogIHIudGhleUdvQWdhaW4gPSBOT1RJQ0VTLmxlbmd0aD09PTA7'
        'CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTm90aWNlczogcmFkaW8gbGluZXMgb2YgYSBtaXNz'
        'aW9uJywgJ209MzQnLCBgCiAgRlMuc3RlcCg0MDApOwogIEZTLnVudGlsKCgpPT5OT1RJQ0VTLnNv'
        'bWUobj0+L09SSU9OIElOQk9VTkQvLnRlc3Qobi50eHQpKSwgNjAwMCwgdHJ1ZSk7CiAgcmV0dXJu'
        'IHtvcmlvbkluYm91bmQ6IE5PVElDRVMuc29tZShuPT5uLnR4dD09PSdHVEQgT1JJT04gSU5CT1VO'
        'RCAtIEhBTkdBUiBPUEVOJyAmJiBuLnRvbmU9PT0naW5mbycpLAogICAgICAgICAgbm90SW5UaGVG'
        'aWVsZDogIVNVQl9NU0dTLnNvbWUobT0+L0lOQk9VTkQvaS50ZXN0KG0udHh0KSl9O2ApOwoKc2Nl'
        'bmFyaW8oJ0h1bGwgYmFuZDogY2FsbSwgbGl0IGJ5IGEgaGl0LCBmdWxsIHdoZW4gbmVhcmx5IGRl'
        'YWQnLCAnbT00MicsIGAKICBGUy5zdGVwKDQwMCk7CiAgY29uc3QgdiA9IGVuZW1pZXMuZmluZChl'
        'PT5lLnVpZD09PSdWMScpOwogIGNvbnN0IHIgPSB7fTsKICB2Ll9oYkhpdCA9IGZjIC0gSEJfSE9U'
        'IC0gMTsgdi5faGJMYXN0ID0gdi5ocDsgZHJhdygpOwogIHIuY2FsbUlzSGFsZiA9IE1hdGguYWJz'
        'KHYuX2hiQWxwaGEgLSBIQl9DQUxNKSA8IDFlLTk7CiAgdi5faGJMYXN0ID0gdi5ocCArIDEwOyBk'
        'cmF3KCk7CiAgci5hSGl0TGlnaHRzSXRVcCA9IE1hdGguYWJzKHYuX2hiQWxwaGEgLSAxKSA8IDFl'
        'LTk7CiAgdi5faGJIaXQgPSBmYyAtIEhCX0hPVC8yOyB2Ll9oYkxhc3QgPSB2LmhwOyBkcmF3KCk7'
        'CiAgci5hbmRJdFNldHRsZXMgPSB2Ll9oYkFscGhhID4gSEJfQ0FMTSAmJiB2Ll9oYkFscGhhIDwg'
        'MTsKICB2Ll9oYkhpdCA9IGZjIC0gSEJfSE9UIC0gMTsgdi5ocCA9IHYubWF4SHAqMC4xOyB2Ll9o'
        'Ykxhc3QgPSB2LmhwOyBkcmF3KCk7CiAgci5uZWFybHlEZWFkU3RheXNGdWxsID0gTWF0aC5hYnMo'
        'di5faGJBbHBoYSAtIDEpIDwgMWUtOTsKICByLmNvbG91clJ1bnNTbW9vdGhseSA9IGh1bGxCYW5k'
        'Q29sKDEpPT09J3JnYig2MCwyMjQsMTA2KScgJiYgaHVsbEJhbmRDb2woMC41KT09PSdyZ2IoMjU1'
        'LDIwNCw2OCknCiAgICAgICAgICAgICAgICAgICAgICAmJiBodWxsQmFuZENvbCgwKT09PSdyZ2Io'
        'MjU1LDc0LDUxKScgJiYgaHVsbEJhbmRDb2woMC43NSkhPT1odWxsQmFuZENvbCgwLjgpOwogIHJl'
        'dHVybiByO2ApOwoKc2NlbmFyaW8oJ1BpY2t1cHMgbGlnaHQgdXAgdGhlIGJhciwgbm90IHRoZSBm'
        'aWVsZCcsICdtPTMxJywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDMwMCk7CiAgY29uc3Qg'
        'dGFrZSA9IChraW5kKT0+eyBJVEVNUy5wdXNoKHt4OnBsYXllci54KzUsIHk6cGxheWVyLnksIHZ4'
        'OjAsIHZ5OjAsIGtpbmQ6a2luZCwgbGlmZTo1MDB9KTsgRlMuc3RlcCgzKTsgfTsKICBUSUNLRVRf'
        'TVNHUy5sZW5ndGggPSAwOyBCQVJfUFVMU0UgPSB7fTsKICB0YWtlKCdjcnVpc2VyJyk7CiAgci50'
        'aWNrZXRMaWdodHNJdHNTeW1ib2wgPSAhIUJBUl9QVUxTRVsndGlja2V0OmNydWlzZXInXSAmJiAh'
        'QkFSX1BVTFNFWyd0aWNrZXQ6Y3J1aXNlciddLndlYWs7CiAgci5ub1dvcmRzSW5UaGVGaWVsZCA9'
        'IFRJQ0tFVF9NU0dTLmxlbmd0aD09PTA7CiAgLy8gVGhlIGhhcm5lc3MgcHV0cyB0aGUgaHVsbCBi'
        'YWNrIHRvIGZ1bGwgZXZlcnkgc3RlcCwgc28gdGhlc2UgdHdvIHRha2UKICAvLyB0aGUgcGlja3Vw'
        'IHN0cmFpZ2h0IHRocm91Z2ggdXBkYXRlSXRlbXMoKS4KICBjb25zdCB0YWtlTm93ID0gKGtpbmQp'
        'PT57IElURU1TLnB1c2goe3g6cGxheWVyLngrNSwgeTpwbGF5ZXIueSwgdng6MCwgdnk6MCwga2lu'
        'ZDpraW5kLCBsaWZlOjUwMH0pOyB1cGRhdGVJdGVtcygpOyB9OwogIHBsYXllci5ocCA9IHBsYXll'
        'ci5tYXhIcCowLjU7IHRha2VOb3coJ3JlcGFpcicpOwogIHIucmVwYWlyTGlnaHRzVGhlSHVsbCA9'
        'ICEhQkFSX1BVTFNFLmh1bGwgJiYgIUJBUl9QVUxTRS5odWxsLndlYWs7CiAgLy8gVGhlIGhhcm5l'
        'c3Mga2VlcHMgdGhlIGh1bGwgYXQgZnVsbCwgc28gdGhpcyBvbmUgY2hhbmdlcyBub3RoaW5nLgog'
        'IGRlbGV0ZSBCQVJfUFVMU0UuaHVsbDsgdGFrZSgncmVwYWlyJyk7CiAgci5yZXBhaXJBdEZ1bGxJ'
        'c0RpbW1lZCA9ICEhQkFSX1BVTFNFLmh1bGwgJiYgQkFSX1BVTFNFLmh1bGwud2VhazsKICBsaXZl'
        'cyA9IExJVkVTX01BWCAtIDE7IHRha2UoJ2xpZmUnKTsKICByLmxpZmVMaWdodHNMaXZlcyA9ICEh'
        'QkFSX1BVTFNFLmxpdmVzICYmICFCQVJfUFVMU0UubGl2ZXMud2VhazsKICBsaXZlcyA9IExJVkVT'
        'X01BWDsgZGVsZXRlIEJBUl9QVUxTRS5saXZlczsgdGFrZU5vdygnbGlmZScpOwogIHIubGlmZUF0'
        'TWF4SXNEaW1tZWQgPSAhIUJBUl9QVUxTRS5saXZlcyAmJiBCQVJfUFVMU0UubGl2ZXMud2VhazsK'
        'ICAvLyBEcmF3bjogdGhlIGdsb3cgcmluZyBnb2VzIHJvdW5kIHRoZSBodWxsIGJhciBhbmQgdGhl'
        'IHRpY2tldCBjZWxsLgogIGNvbnN0IHJpbmdzID0gW107IGNvbnN0IG9nID0gdGhHbG93UGF0aDsK'
        'ICB0aEdsb3dQYXRoID0gZnVuY3Rpb24oeCx5LHcsaCl7IHJpbmdzLnB1c2goe3gseSx3LGh9KTsg'
        'cmV0dXJuIG9nLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07CiAgYmFyUHVsc2UoJ2h1bGwnKTsg'
        'YmFyUHVsc2UoJ3RpY2tldDpjcnVpc2VyJyk7IEZTLnN0ZXAoNDApOyBkcmF3KCk7IHRoR2xvd1Bh'
        'dGggPSBvZzsKICByLnJpbmdBcm91bmRIdWxsID0gcmluZ3Muc29tZShnPT5nLng9PT0xODEgJiYg'
        'Zy53PT09MTE2KTsKICByLnJpbmdBcm91bmRUaWNrZXQgPSByaW5ncy5zb21lKGc9PmcueD09PTUz'
        'MyAmJiBnLnc9PT01OCk7CiAgLy8gSXRzIHRpbWUgaXMgdXA6IHRoZSBwdWxzZSBpcyBvdmVyIGFu'
        'ZCBnb25lLiAoU3RlcHBpbmcgdGhlIGdhbWUgdG8gZ2V0CiAgLy8gdGhlcmUgd291bGQgbGV0IGxv'
        'b3QgZnJvbSB0aGUgZmlnaHQgbGlnaHQgaXQgdXAgYWdhaW4uKQogIGJhclB1bHNlKCdodWxsJyk7'
        'IEJBUl9QVUxTRS5odWxsLnQwID0gZmMgLSBCQVJfUFVMU0VfVDsKICByLmFuZEl0RW5kcyA9IGJh'
        'clB1bHNlTGV2ZWwoJ2h1bGwnKT09PTAgJiYgIUJBUl9QVUxTRS5odWxsOwogIHIuc29mdE5vdEhh'
        'cmQgPSAoKCk9PnsgYmFyUHVsc2UoJ2h1bGwnKTsgY29uc3QgYSA9IGJhclB1bHNlTGV2ZWwoJ2h1'
        'bGwnKTsgRlMuc3RlcCgxMCk7IGNvbnN0IGIgPSBiYXJQdWxzZUxldmVsKCdodWxsJyk7IHJldHVy'
        'biBhPT09MCAmJiBiPjAgJiYgYjwxOyB9KSgpOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ01p'
        'c3Npb24gcmV3YXJkIHRpY2tldDogaW4gdGhlIGJhcicsICdtPTM1JywgYAogIEZTLnN0ZXAoMzAw'
        'KTsKICBjb25zdCBkID0gYWxsaWVzLmZpbmQoYT0+YS51aWQ9PT0nQTEnKTsKICBkLmhwID0gZC5t'
        'YXhIcCA9IDFlNzsgZm9yKGNvbnN0IHMgb2YgZC5zdWJzfHxbXSkgcy5ocCA9IHMubWF4SHAgPSAx'
        'ZTc7CiAgVElDS0VUX01TR1MubGVuZ3RoID0gMDsKICAvLyBSb2NrcyBhbmQgd3JlY2thZ2UgdGFr'
        'ZSBhIHNoYXJlIG9mIHRoZSBodWxsIHJhdGhlciB0aGFuIHBvaW50cywgc28gYQogIC8vIGJpZyBo'
        'dWxsIGFsb25lIGRvZXMgbm90IGtlZXAgaGVyIGFsaXZlOiBzaGUgaXMgdG9wcGVkIHVwIGFzIHNo'
        'ZSBnb2VzLgogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+eyBpZihhbGxpZXMuaW5jbHVkZXMoZCkp'
        'IGQuaHAgPSBkLm1heEhwOyByZXR1cm4gd2F2ZU92ZXI7IH0sIDEyMDAwLCB0cnVlKTsKICBjb25z'
        'dCBrID0gT2JqZWN0LmtleXMoQkFSX1BVTFNFKS5maW5kKHg9Pi9edGlja2V0Oi8udGVzdCh4KSk7'
        'CiAgY29uc3QgciA9IHtyZXdhcmRlZDogdD49MCAmJiAhIWssIG5vdEluVGhlRmllbGQ6IFRJQ0tF'
        'VF9NU0dTLmxlbmd0aD09PTB9OwogIGlmKCFyLnJld2FyZGVkKSByLmRiZyA9IHt0LCBnbDpndWFy'
        'ZExvc3QsIGd3Omd1YXJkV2FudGVkLCBnczpndWFyZFNwYXduZWQsIGtleXM6T2JqZWN0LmtleXMo'
        'QkFSX1BVTFNFKSwgd2F2ZSwgZmN9OwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ0EgY29ydmV0'
        'dGUgYXJyaXZlczogUkVBUk0gY2FsbHMnLCAnbT0zNScsIGAKICBCQVJfUFVMU0UgPSB7fTsKICAv'
        'LyBUaGUgYnV0dG9uIGJlY29tZXMgdXNhYmxlIG9uY2Ugc2hlIGlzIHRoZXJlIGFuZCB0aGUganVt'
        'cCBpbiBpcyBvdmVyLgogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+ISFCQVJfUFVMU0UucmVhcm0s'
        'IDMwMDAsIHRydWUpOwogIGNvbnN0IGNhbGxlZCA9IHJlYXJtUmVhZHkoKTsKICBjb25zdCB0MCA9'
        'IEJBUl9QVUxTRS5yZWFybSA/IEJBUl9QVUxTRS5yZWFybS50MCA6IC0xOwogIEZTLnN0ZXAoMTAw'
        'KTsKICByZXR1cm4ge3JlYXJtQ2FsbHM6IHQ+PTAgJiYgY2FsbGVkLCBvbmx5T25jZU5vdEV2ZXJ5'
        'U3RlcDogIUJBUl9QVUxTRS5yZWFybSB8fCBCQVJfUFVMU0UucmVhcm0udDA9PT10MH07YCk7Cgpz'
        'Y2VuYXJpbygnQSBkZXN0cm95ZXIgYXJyaXZlczogU0hJUCBTV0lUQ0ggY2FsbHMnLCAnbT0zNCZz'
        'aGlwcz04JywgYAogIEJBUl9QVUxTRSA9IHt9OwogIEZTLnN0ZXAoMzAwKTsKICBjb25zdCBiZWZv'
        'cmUgPSAhIUJBUl9QVUxTRS5zd2FwOwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+c2hpcFN3YXBS'
        'ZWFkeSgpLCA2MDAwLCB0cnVlKTsKICBGUy5zdGVwKDIpOwogIHJldHVybiB7bm90QmVmb3JlVGhl'
        'T3Jpb246ICFiZWZvcmUsIHN3YXBDYWxsczogdD49MCAmJiAhIUJBUl9QVUxTRS5zd2FwfTtgKTsK'
        'CnNjZW5hcmlvKCdNNDkgRGFzIFJlcGFyYXR1cmRvY2snLCAnbT00OScsIGAKICBjb25zdCByID0g'
        'e307CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IGQgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0n'
        'RDEnKTsKICByLmFyY2FkaWFCZWhpbmQgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nUzEnICYm'
        'IGUuaW1nPT09J2luYXJjYWRpYScgJiYgZS5pbnZ1bG4pOwogIHIuZGVpbW9zSHVydCA9ICEhZCAm'
        'JiBNYXRoLmFicyhkLmhwL2QubWF4SHAgLSAwLjI1KSA8IDAuMDI7CiAgci5zYXlzV2hhdCA9IG1p'
        'c3Npb25PYmo9PT0nREVTVFJPWSBUSEUgREVJTU9TIEJFRk9SRSBIRVIgUkVQQUlSUyBBUkUgRE9O'
        'RSc7CiAgbGV0IHQxID0gbnVsbDsKICBGUy51bnRpbCgoKT0+eyB0MSA9IGVuZW1pZXMuZmluZChl'
        'PT5lLnVpZD09PSdUMScpOyByZXR1cm4gISF0MTsgfSwgMjAwMCwgdHJ1ZSk7CiAgci50cmFuc3Bv'
        'cnRDb21lcyA9ICEhdDEgJiYgdDEuaW1nPT09J3RyYXJnbyc7CiAgLy8gSHVsbCBqdXN0IGJlZm9y'
        'ZSB0aGUgZG9jaywgc3RlcHBlZCBzaW5nbHkgc28gbm90aGluZyBlbHNlIGdldHMgaW4uCiAgbGV0'
        'IGgwID0gZC5ocCwgZ290ID0gLTE7CiAgZm9yKGxldCBpPTA7aTw2MDAwO2krKyl7IGlmKEVWX0RP'
        'Q0tbJ1QxJ10peyBnb3QgPSBpOyBicmVhazsgfSBoMCA9IGQuaHA7IGlmKGklMjAwPT09MCkgRlMu'
        'a2lsbFNtYWxsKCk7IEZTLnN0ZXAoMSk7IH0KICByLmRvY2tSZXBhaXJzQVF1YXJ0ZXIgPSBnb3Q+'
        'PTAgJiYgTWF0aC5hYnMoKGQuaHAtaDApL2QubWF4SHAgLSAwLjI1KSA8IDAuMDM7CiAgci50cmFu'
        'c3BvcnRKdW1wc091dCA9IHQxLndhcnBPdXQ+MCB8fCAhZW5lbWllcy5pbmNsdWRlcyh0MSk7CiAg'
        'Ly8gQWxsIHRocmVlIHRocm91Z2g6IHNoZSBpcyB3aG9sZSBhbmQganVtcHMuIFRoYXQgaXMgYSBm'
        'YWlsdXJlLgogIGZvcihjb25zdCBlIG9mIGVuZW1pZXMpIGlmKGUudHlwZT09PSdmaWdodGVyJ3x8'
        'ZS50eXBlPT09J2JvbWJlcicpIGUuaHAgPSAwOwogIGNvbnN0IGYgPSBGUy51bnRpbCgoKT0+ISFv'
        'YmpDYXJkICYmIG9iakNhcmQudG9uZT09PSdmYWlsJywgOTAwMCwgdHJ1ZSk7CiAgci5yZXBhaXJl'
        'ZFNoZUp1bXBzID0gZj49MCAmJiBvYmpDYXJkLnR4dD09PSdUSEUgREVJTU9TIFdBUyBSRVBBSVJF'
        'RCcgJiYgISFFVl9ET0NLWydUMyddOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ000OSBkZXN0'
        'cm95ZWQgaW4gdGltZScsICdtPTQ5JywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDcwMCk7'
        'CiAgY29uc3QgZCA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdEMScpOwogIGQuaHAgPSAwOwog'
        'IGNvbnN0IGMgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J0RFSU1P'
        'UyBERVNUUk9ZRUQnLCAxNTAwLCBmYWxzZSk7CiAgci5jb21wbGV0ZUNhcmQgPSBjPj0wOwogIHIu'
        'bm9Nb3JlVHJhbnNwb3J0cyA9ICFzcGF3blEuc29tZShxPT4vXlQvLnRlc3QocS51aWR8fCcnKSk7'
        'CiAgLy8gT25lIGFscmVhZHkgb24gaXRzIHdheSBoYXMgbm90aGluZyBsZWZ0IHRvIGRvY2sgd2l0'
        'aCBhbmQgbGVhdmVzLgogIGNvbnN0IHQgPSBlbmVtaWVzLmZpbmQoZT0+L15ULy50ZXN0KGUudWlk'
        'fHwnJykpOwogIGlmKHQpeyBGUy5zdGVwKDMwMCk7IHIuc3RyYXlMZWF2ZXMgPSAhZW5lbWllcy5p'
        'bmNsdWRlcyh0KSB8fCB0LndhcnBPdXQ+MDsgfSBlbHNlIHIuc3RyYXlMZWF2ZXMgPSB0cnVlOwog'
        'IHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001MCBEZXIgRHVyY2hicnVjaCcsICdtPTUwJywgYAog'
        'IGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDUwMCk7CiAgY29uc3QgayA9IGVuZW1pZXMuZmlsdGVy'
        'KGU9PmUudWlkPT09J0sxJyk7CiAgci50d29BZW9sdXMgPSBrLmxlbmd0aD09PTIgJiYgay5ldmVy'
        'eShlPT5lLmltZz09PSdudGZjcmFlb2x1cycpOwogIHIuc2VudHJ5TGluZSA9IGVuZW1pZXMuZmls'
        'dGVyKGU9PmUudWlkPT09J0cxJyAmJiBlLnR5cGU9PT0nc2VudHJ5JykubGVuZ3RoPT09NDsKICBy'
        'Lm5vT3Jpb25ZZXQgPSAhYWxsaWVzLnNvbWUoYT0+YS51aWQ9PT0nQTEnKTsKICByLnNheXNCcmVh'
        'ayA9IG1pc3Npb25PYmo9PT0nQlJFQUsgVEhFIEJMT0NLQURFIC0gREVTVFJPWSBBTiBBRU9MVVMn'
        'OwogIGtbMF0uaHAgPSAwOwogIGxldCBvID0gbnVsbDsKICBGUy51bnRpbCgoKT0+eyBvID0gYWxs'
        'aWVzLmZpbmQoYT0+YS51aWQ9PT0nQTEnKTsgcmV0dXJuICEhbzsgfSwgMjAwMCwgdHJ1ZSk7CiAg'
        'ci5vcmlvblRocm91Z2hUaGVHYXAgPSAhIW8gJiYgby50cmFuc2l0PT09dHJ1ZTsKICAvLyBTaGUg'
        'd2FycHMgaW4gb24gc2NyZWVuIGluc3RlYWQgb2YgcG9wcGluZyB1cCBhdCB0aGUgZWRnZS4KICBj'
        'b25zdCBfb2kgPSBJTUdTW28uaW1nXSwgX29oID0gX29pID8gX29pLndpZHRoKm8uc2MqMC41IDog'
        'MDsKICByLm9yaW9uV2FycHNJbiA9IG8ud2FycD4wICYmIG8ueCAtIF9vaCA+PSAwOwogIEZTLnN0'
        'ZXAoMik7CiAgci5uZXdPYmplY3RpdmUgPSBtaXNzaW9uT2JqPT09J0dFVCBUSEUgT1JJT04gVEhS'
        'T1VHSCc7CiAgby5ocCA9IG8ubWF4SHAgPSAxZTc7IGZvcihjb25zdCBzIG9mIG8uc3Vic3x8W10p'
        'IHMuaHAgPSBzLm1heEhwID0gMWU3OwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+eyBpZihhbGxp'
        'ZXMuaW5jbHVkZXMobykpIG8uaHAgPSBvLm1heEhwOyByZXR1cm4gISFvYmpDYXJkICYmIG9iakNh'
        'cmQudHh0PT09J1RIRSBPUklPTiBJUyBUSFJPVUdIJzsgfSwgOTAwMCwgdHJ1ZSk7CiAgci50aHJv'
        'dWdoQ2FyZCA9IHQ+PTA7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygnTTUxIERpZSBSdWVja2Vy'
        'b2JlcnVuZycsICdtPTUxJywgYAogIGNvbnN0IHIgPSB7fTsKICBzY29yZSA9IDEwMDA7CiAgRlMu'
        'c3RlcCgzMDApOwogIGNvbnN0IHMgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nUzEnKTsKICBy'
        'LmFybWVkQXJjYWRpYSA9ICEhcyAmJiBzLnR5cGU9PT0nc3RhdGlvbicgJiYgcy5hcm1lZCAmJiAh'
        'IXMuc3VicyAmJiBzLnN1YnMuc29tZSh4PT54LmlkPT09J3dlYXBvbnMnKTsKICByLm5vRW5naW5l'
        'c05vTmF2aWdhdGlvbiA9ICEhcyAmJiAhcy5zdWJzLnNvbWUoeD0+eC5pZD09PSdlbmdpbmVzJyB8'
        'fCB4LmlkPT09J25hdmlnYXRpb24nKTsKICAvLyBIZXIgZ3VucyBmaXJlLgogIEZTLmtpbGxTbWFs'
        'bCgpOyBlQnVsbGV0cy5sZW5ndGggPSAwOwogIGxldCBzaG90cyA9IDA7CiAgZm9yKGxldCBpPTA7'
        'aTw0MDA7aSsrKXsgRlMua2lsbFNtYWxsKCk7IGNvbnN0IG4wID0gZUJ1bGxldHMubGVuZ3RoOyBG'
        'Uy5zdGVwKDEpOyBzaG90cyArPSBNYXRoLm1heCgwLCBlQnVsbGV0cy5sZW5ndGgtbjApOyB9CiAg'
        'ci5ndW5zRmlyZSA9IHNob3RzID4gMDsKICBkYW1hZ2VFbmVteShzLCBzLm1heEhwKjUsIHMueCwg'
        'cy55LCB0cnVlLCAnYm9sdCcpOyBGUy5zdGVwKDMpOwogIHIuY2Fubm90QmVEZXN0cm95ZWQgPSBl'
        'bmVtaWVzLmluY2x1ZGVzKHMpICYmIHMucm9sbFQ9PW51bGwgJiYgcy5ocD4wOwogIHIubm9FbHlz'
        'aXVtWWV0ID0gIWFsbGllcy5zb21lKGE9PmEudWlkPT09J1QxJyk7CiAgZm9yKGNvbnN0IHggb2Yg'
        'cy5zdWJzKSBpZih4LmlkPT09J3dlYXBvbnMnKXsgeC5kZWFkID0gdHJ1ZTsgeC5ocCA9IDA7IH0K'
        'ICBGUy5zdGVwKDMpOwogIHIuY292ZXJUaGVFbHlzaXVtID0gbWlzc2lvbk9iaj09PSdDT1ZFUiBU'
        'SEUgRUxZU0lVTSc7CiAgLy8gR3VucyBvdXQ6IHNoZSBmYWxscyBzaWxlbnQuCiAgc2hvdHMgPSAw'
        'OwogIGZvcihsZXQgaT0wO2k8MzAwO2krKyl7IEZTLmtpbGxTbWFsbCgpOyBjb25zdCBuMCA9IGVC'
        'dWxsZXRzLmxlbmd0aDsgRlMuc3RlcCgxKTsgc2hvdHMgKz0gTWF0aC5tYXgoMCwgZUJ1bGxldHMu'
        'bGVuZ3RoLW4wKTsgfQogIHIuc2lsZW50V2l0aG91dEd1bnMgPSBzaG90cz09PTA7CiAgbGV0IGVs'
        'ID0gbnVsbDsKICBGUy51bnRpbCgoKT0+eyBlbCA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J1Qx'
        'Jyk7IHJldHVybiAhIWVsOyB9LCAzMDAwLCB0cnVlKTsKICBlbC5ocCA9IGVsLm1heEhwID0gMWU3'
        'OwogIGNvbnN0IGhvbGQgPSBGUy51bnRpbCgoKT0+eyBlbC5ocCA9IGVsLm1heEhwOyByZXR1cm4g'
        'ZWwuaG9sZFQhPW51bGw7IH0sIDkwMDAsIHRydWUpOwogIEZTLnN0ZXAoNDAwKTsKICByLmJvYXJk'
        'aW5nVGFrZXNUaW1lID0gaG9sZD49MCAmJiAhcy5jYXB0dXJlZDsKICBjb25zdCBnb3QgPSBGUy51'
        'bnRpbCgoKT0+eyBpZihhbGxpZXMuaW5jbHVkZXMoZWwpKSBlbC5ocCA9IGVsLm1heEhwOyByZXR1'
        'cm4gISFFVl9ET0NLWydUMSddOyB9LCAzMDAwLCB0cnVlKTsKICBGUy5zdGVwKDMpOwogIHIudGFr'
        'ZW5BbmRTdGF5cyA9IGdvdD49MCAmJiBzLmNhcHR1cmVkPT09dHJ1ZSAmJiBlbmVtaWVzLmluY2x1'
        'ZGVzKHMpICYmICEocy53YXJwT3V0PjApICYmIHMuc2NlbmVyeT09PXRydWU7CiAgci5jb21wbGV0'
        'ZUNhcmQgPSAhIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nQVJDQURJQSBSRVRBS0VOJzsKICBj'
        'b25zdCB3ID0gRlMudW50aWwoKCk9PndhdmVPdmVyLCA2MDAwLCB0cnVlKTsKICByLndhdmVFbmRz'
        'ID0gdz49MDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNTEgYm90aCBFbHlzaXVtcyBsb3N0'
        'OiBmYWlsZWQnLCAnbT01MScsIGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCgzMDApOwogIGNv'
        'bnN0IHMgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nUzEnKTsKICBmb3IoY29uc3QgeCBvZiBz'
        'LnN1YnMpIGlmKHguaWQ9PT0nd2VhcG9ucycpeyB4LmRlYWQgPSB0cnVlOyB4LmhwID0gMDsgfQog'
        'IGxldCBlbCA9IG51bGw7CiAgRlMudW50aWwoKCk9PnsgZWwgPSBhbGxpZXMuZmluZChhPT5hLnVp'
        'ZD09PSdUMScpOyByZXR1cm4gISFlbDsgfSwgMzAwMCwgdHJ1ZSk7CiAgZWwuaHAgPSAwOwogIGxl'
        'dCBlMiA9IG51bGw7CiAgRlMudW50aWwoKCk9PnsgZTIgPSBhbGxpZXMuZmluZChhPT5hLnVpZD09'
        'PSdUMicpOyByZXR1cm4gISFlMjsgfSwgMzAwMCwgdHJ1ZSk7CiAgci5zZWNvbmRDb21lcyA9ICEh'
        'ZTI7CiAgZTIuaHAgPSAwOwogIGNvbnN0IGYgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9i'
        'akNhcmQudG9uZT09PSdmYWlsJywgMTUwMCwgZmFsc2UpOwogIHIuZmFpbENhcmQgPSBmPj0wICYm'
        'IG9iakNhcmQudHh0PT09J0JPVEggRUxZU0lVTVMgTE9TVCc7CiAgci5udGZLZWVwc0hlciA9IGVu'
        'ZW1pZXMuaW5jbHVkZXMocykgJiYgcy5zY2VuZXJ5PT09dHJ1ZSAmJiAhcy5jYXB0dXJlZDsKICBj'
        'b25zdCB3ID0gRlMudW50aWwoKCk9PndhdmVPdmVyLCA2MDAwLCB0cnVlLCB0cnVlKTsKICByLndh'
        'dmVFbmRzID0gdz49MDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNTIgRGFzIEFydGlsbGVy'
        'aWVmZXVlcicsICdtPTUyJywgYAogIGNvbnN0IHIgPSB7fTsKICB0aWNrZXRzLmNydWlzZXIgPSAx'
        'OwogIEZTLnN0ZXAoNDAwKTsKICBjb25zdCBtcyA9IGFsbGllcy5maWx0ZXIoYT0+YS51aWQ9PT0n'
        'TTEnIHx8IGEudWlkPT09J00yJyk7CiAgci50d29Nam9sbmlycyA9IG1zLmxlbmd0aD09PTIgJiYg'
        'bXMuZXZlcnkobT0+bS5pbWc9PT0nc2dtam9sbmlyJyAmJiBtLnBsYXRmb3JtICYmICFtLnN1YnMg'
        'JiYgbS5iZWFtcyAmJiBtLmJlYW1zLnNvbWUoYj0+Yi5sYXJnZSkpOwogIGNvbnN0IG0xID0gbXMu'
        'ZmluZChtPT5tLnVpZD09PSdNMScpLCBtMiA9IG1zLmZpbmQobT0+bS51aWQ9PT0nTTInKTsKICBy'
        'LmluUGxhY2UgPSAhIW0xICYmICEhbTIgJiYgTWF0aC5hYnMobTEueC03MCk8MSAmJiBNYXRoLmFi'
        'cyhtMS55LTE0MCk8MSAmJiBNYXRoLmFicyhtMi55LTM2MCk8MTsKICByLmRlaW1vc0F0VGhlQm90'
        'dG9tID0gYWxsaWVzLnNvbWUoYT0+YS51aWQ9PT0nQTEnICYmIGEuaW1nPT09J2NvZGVpbW9zJyAm'
        'JiBNYXRoLmFicyhhLnktNDQwKTwxKTsKICByLnN1cHBvcnRTdGlsbENhbGxhYmxlID0gYWxseVJl'
        'YWR5KCk7CiAgY29uc3QgX3YxID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyk7CiAgci5z'
        'aG9ydGVyRGVhZGxpbmUgPSAhIV92MSAmJiBfdjEuZmxlZVQ+MCAmJiBfdjEuZmxlZVQgPD0gMzAq'
        'VElDS19IWjsKICAvLyBUaGV5IHRha2UgdHVybnM6IG5ldmVyIGJvdGggZWFybHkgaW4gdGhlaXIg'
        'Y2hhcmdlIHRvZ2V0aGVyLgogIGxldCB0b2dldGhlciA9IDAsIGNoYXJnZWQgPSB7TTE6MCwgTTI6'
        'MH07CiAgZm9yKGxldCBpPTA7aTw0MDAwO2krPTEwKXsgRlMua2lsbFNtYWxsKCk7IGZvcihjb25z'
        'dCBlIG9mIGVuZW1pZXMpIGlmKGUuZmxlZVQ+MCkgZS5mbGVlVCA9IDFlNjsKICAgIEZTLnN0ZXAo'
        'MTApOwogICAgY29uc3QgZWFybHkgPSBtcy5maWx0ZXIobT0+bS5iZWFtcy5zb21lKGI9PmIuc3Rh'
        'dGU9PT0nY2hhcmdpbmcnICYmIChiLmNoYXJnZU1heCAtIGIudGltZXIpIDwgYi5jaGFyZ2VNYXgq'
        'MC40KSk7CiAgICBpZihlYXJseS5sZW5ndGg9PT0yKSB0b2dldGhlcisrOwogICAgZm9yKGNvbnN0'
        'IG0gb2YgbXMpIGlmKG0uYmVhbXMuc29tZShiPT5iLnN0YXRlPT09J2ZpcmluZycpKSBjaGFyZ2Vk'
        'W20udWlkXSsrOyB9CiAgci50YWtlVHVybnMgPSB0b2dldGhlcj09PTAgJiYgY2hhcmdlZC5NMT4w'
        'ICYmIGNoYXJnZWQuTTI+MDsKICAvLyBUd28gbGFuZXMsIG5ldmVyIG1vcmUgdGhhbiB0d28gTlRG'
        'IGNhcGl0YWwgc2hpcHMgYXQgb25jZS4KICBsZXQgbW9zdCA9IDA7IGNvbnN0IHNlZW4gPSB7fTsK'
        'ICBGUy51bnRpbCgoKT0+eyBjb25zdCBjYXBzID0gZW5lbWllcy5maWx0ZXIoZT0+L15WLy50ZXN0'
        'KGUudWlkfHwnJykgJiYgIShlLndhcnA+MCkpOwogICAgbW9zdCA9IE1hdGgubWF4KG1vc3QsIGNh'
        'cHMubGVuZ3RoKTsgZm9yKGNvbnN0IGUgb2YgY2Fwcykgc2VlbltlLnVpZF0gPSBlOwogICAgZm9y'
        'KGNvbnN0IGUgb2YgY2FwcykgaWYoZS53YXJwPD0wICYmIGUueCA8IFctNjApeyBlLmhwID0gMDsg'
        'fQogICAgcmV0dXJuIFsnVjEnLCdWMicsJ1YzJywnVjQnLCdWNScsJ1Y2J10uZXZlcnkoaz0+RVZf'
        'U0VFTltrXSkgJiYgIWJ5SWQoJ1Y1JykubGVuZ3RoICYmICFieUlkKCdWNicpLmxlbmd0aDsgfSwg'
        'MjAwMDAsIHRydWUpOwogIHIuYWxsU2l4Q29tZSA9IHdhdmU9PT01MiAmJiBbJ1YxJywnVjInLCdW'
        'MycsJ1Y0JywnVjUnLCdWNiddLmV2ZXJ5KGs9PkVWX1NFRU5ba10pOwogIHIubmV2ZXJNb3JlVGhh'
        'blR3byA9IG1vc3Q8PTI7CiAgci5jb21wbGV0ZUNhcmQgPSBGUy51bnRpbCgoKT0+ISFvYmpDYXJk'
        'ICYmIG9iakNhcmQudHh0PT09J05URiBCQVRUTEUgR1JPVVAgREVTVFJPWUVEJywgMzAwLCBmYWxz'
        'ZSkgPj0gMDsKICAvLyBObyBqdW1wIGRyaXZlOiB0aGUgTWpvbG5pcnMgc3RheSB1bnRpbCB0aGUg'
        'ZmllbGQgZ29lcyBkYXJrLgogIEZTLnVudGlsKCgpPT53YXZlT3ZlciwgNjAwMCwgdHJ1ZSwgdHJ1'
        'ZSk7CiAgRlMuc3RlcCg2MCk7CiAgci5tam9sbmlyc1N0YXkgPSBhbGxpZXMuaW5jbHVkZXMobTEp'
        'ICYmICEobTEud2FycE91dD4wKSAmJiBhbGxpZXMuaW5jbHVkZXMobTIpOwogIHJldHVybiByO2Ap'
        'OwoKc2NlbmFyaW8oJ001MyBEZXIgR2VnZW5hbmdyaWZmJywgJ209NTMnLCBgCiAgY29uc3QgciA9'
        'IHt9OwogIHRpY2tldHMuY3J1aXNlciA9IDE7CiAgRlMuc3RlcCgzMDApOwogIGNvbnN0IGExID0g'
        'YWxsaWVzLmZpbmQoYT0+YS51aWQ9PT0nQTEnKSwgYTIgPSBhbGxpZXMuZmluZChhPT5hLnVpZD09'
        'PSdBMicpOwogIHIuZmxlZXRQbGFjZWQgPSAhIWExICYmICEhYTIgJiYgTWF0aC5hYnMoYTEueS0x'
        'NzApPDYwICYmIE1hdGguYWJzKGEyLnktMzkwKTw2MDsKICByLm5vQ2FsbFdoaWxlQm90aFN0YW5k'
        'ID0gIWFsbHlSZWFkeSgpOwogIHIubm9FbmVteURlc3Ryb3llcnNZZXQgPSAhZW5lbWllcy5zb21l'
        'KGU9PmUudWlkPT09J1YxJ3x8ZS51aWQ9PT0nVjInKTsKICBGUy51bnRpbCgoKT0+ZW5lbWllcy5z'
        'b21lKGU9PmUudWlkPT09J1YxJykgJiYgZW5lbWllcy5zb21lKGU9PmUudWlkPT09J1YyJyksIDIw'
        'MDAsIHRydWUpOwogIHIudGhleUp1bXBJbiA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdWMScg'
        'JiYgZS5pbWc9PT0nbnRmZGVoZWNhdGUnKSAmJiBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nVjIn'
        'ICYmIGUuaW1nPT09J250ZmRlb3Jpb24nKTsKICBGUy5zdGVwKDIpOwogIHIubmV3T2JqZWN0aXZl'
        'ID0gbWlzc2lvbk9iaj09PSdERVNUUk9ZIFRIRSBIRUNBVEUgQU5EIFRIRSBPUklPTic7CiAgY29u'
        'c3QgdjEgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0nVjEnKTsgdjEuaHAgPSAwOwogIEZTLnN0'
        'ZXAoNDAwKTsKICByLm5vdERvbmVXaXRoT25lID0gIShvYmpDYXJkICYmIG9iakNhcmQudHh0PT09'
        'J0NPVU5URVJBVFRBQ0sgQlJPS0VOJyk7CiAgLy8gT25lIG9mIG91cnMgbG9zdDogbm93IHRoZSBj'
        'YWxsIGlzIGZyZWUuCiAgYTIuaHAgPSAwOyBGUy5zdGVwKDMwMCk7CiAgci5jYWxsRnJlZUFmdGVy'
        'QUxvc3MgPSBhbGx5UmVhZHkoKTsKICBjb25zdCB2MiA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09'
        'PSdWMicpOyBpZih2MikgdjIuaHAgPSAwOwogIHIuY29tcGxldGVDYXJkID0gRlMudW50aWwoKCk9'
        'PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdDT1VOVEVSQVRUQUNLIEJST0tFTicsIDMwMDAs'
        'IGZhbHNlKSA+PSAwOwogIC8vIE91ciBzaGlwcyBqdW1wIG91dCBhdCB0aGUgZW5kIG9mIHRoZSB3'
        'YXZlOiB0aGF0IGlzIG5vdCBhIGxvc3MuCiAgY29uc3Qgc2FpZCA9IG5ldyBTZXQoKTsKICBGUy51'
        'bnRpbCgoKT0+eyBmb3IoY29uc3QgbiBvZiBOT1RJQ0VTKSBzYWlkLmFkZChuLnR4dCk7IHJldHVy'
        'biB3YXZlPT09NTQ7IH0sIDkwMDAsIHRydWUsIHRydWUpOwogIHIuanVtcElzTm9Mb3NzID0gIXNh'
        'aWQuaGFzKCdHVEQgT1JJT04gTE9TVCcpOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001NCBE'
        'aWUgRXZha3VpZXJ1bmcnLCAnbT01NCcsIGAKICBjb25zdCByID0ge307CiAgbGV0IHQxID0gbnVs'
        'bDsKICBGUy51bnRpbCgoKT0+eyB0MSA9IGFsbGllcy5maW5kKGE9PmEudWlkPT09J1QxJyk7IHJl'
        'dHVybiAhIXQxOyB9LCAxMDAwLCBmYWxzZSk7CiAgci5sZWF2ZXNUaGVTdGF0aW9uID0gISF0MSAm'
        'JiBNYXRoLmFicyh0MS54LTU2MCkgPCAxNSAmJiB0MS5jcm9zc2luZyA8IDAgJiYgdDEuZmxpcD09'
        'PW5lZWRzRmxpcCh0MS5pbWcsIHRydWUpOwogIGNvbnN0IHgwID0gdDEueDsgRlMuc3RlcCgxMDAp'
        'OwogIHIuZmxpZXNMZWZ0ID0gdDEueCA8IHgwIC0gMzA7CiAgLy8gS2VlcCB0aGVtIGFsaXZlOyB0'
        'aGV5IGZseSBvdXQgdG8gdGhlIGxlZnQuCiAgY29uc3Qga2VlcCA9ICgpPT57IGZvcihjb25zdCBh'
        'IG9mIGFsbGllcykgaWYoL15ULy50ZXN0KGEudWlkfHwnJykpIGEuaHAgPSBhLm1heEhwID0gMWU3'
        'OyB9OwogIGNvbnN0IHQgPSBGUy51bnRpbCgoKT0+eyBrZWVwKCk7IHJldHVybiBwcm90U2F2ZWQ+'
        'PTE7IH0sIDMwMDAsIHRydWUpOwogIHIuZmlyc3RPdXQgPSB0Pj0wOwogIEZTLnN0ZXAoNSk7CiAg'
        'ci5ub3RpY2VGb3JJdCA9IE5PVElDRVMuc29tZShuPT5uLnR4dD09PSdGSVJTVCBFTFlTSVVNIElT'
        'IE9VVCcpOwogIC8vIFRocmVlIG91dCB3aGlsZSB0aGUgZm91cnRoIGlzIHN0aWxsIGZseWluZzog'
        'bm90IHlldCBjb21wbGV0ZS4KICBGUy51bnRpbCgoKT0+eyBrZWVwKCk7IHJldHVybiBwcm90U2F2'
        'ZWQ+PTM7IH0sIDkwMDAsIHRydWUpOwogIGNvbnN0IHQ0ID0gYWxsaWVzLmZpbmQoYT0+YS51aWQ9'
        'PT0nVDQnKTsKICByLm5vdENvbXBsZXRlV2hpbGVPbmVGbGllcyA9ICEhdDQgJiYgIShvYmpDYXJk'
        'ICYmIG9iakNhcmQudHh0PT09J0VWQUNVQVRJT04gQ09NUExFVEUnKTsKICBjb25zdCBjID0gRlMu'
        'dW50aWwoKCk9Pnsga2VlcCgpOyByZXR1cm4gISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J0VW'
        'QUNVQVRJT04gQ09NUExFVEUnOyB9LCA5MDAwLCB0cnVlKTsKICByLnRocmVlT3V0Q29tcGxldGUg'
        'PSBjPj0wICYmIHByb3RTYXZlZD49MzsKICBjb25zdCB3ID0gRlMudW50aWwoKCk9Pnsga2VlcCgp'
        'OyByZXR1cm4gd2F2ZU92ZXI7IH0sIDkwMDAsIHRydWUsIHRydWUpOwogIHIud2F2ZUVuZHMgPSB3'
        'Pj0wOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001NCB0d28gbG9zdDogZmFpbGVkJywgJ209'
        'NTQnLCBgCiAgY29uc3QgciA9IHt9OwogIGxldCBuID0gMDsKICBjb25zdCBmID0gRlMudW50aWwo'
        'KCk9PnsgZm9yKGNvbnN0IGEgb2YgYWxsaWVzKSBpZigvXlRbMTJdJC8udGVzdChhLnVpZHx8Jycp'
        'KSBhLmhwID0gMDsKICAgIHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC50b25lPT09J2ZhaWwn'
        'OyB9LCAzMDAwLCB0cnVlKTsKICByLmZhaWxDYXJkID0gZj49MCAmJiBvYmpDYXJkLnR4dD09PSdU'
        'T08gTUFOWSBFTFlTSVVNUyBMT1NUJzsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdCZWFtcyBy'
        'dW4gdW5kZXIgdGhlIGh1bGxzJywgJ209NDInLCBgCiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAo'
        'MzAwKTsKICBjb25zdCBzaG9vdGVyID0gYWxsaWVzLmNvbmNhdChlbmVtaWVzKS5maW5kKG89Pm8u'
        'YmVhbXMgJiYgby5iZWFtcy5sZW5ndGgpOwogIGNvbnN0IGIgPSBzaG9vdGVyLmJlYW1zWzBdOwog'
        'IGIuc3RhdGUgPSAnZmlyaW5nJzsgYi50aW1lciA9IDFlNjsgYi5hbmdsZSA9IDA7IGIuY3VyQW5n'
        'bGUgPSAwOwogIGNvbnN0IG9yZGVyID0gW107CiAgY29uc3QgX3IgPSBkcmF3QmVhbVJheXMsIF9z'
        'ID0gZHJhd1NoaXA7CiAgZHJhd0JlYW1SYXlzID0gZnVuY3Rpb24oZSwgb3duKXsgaWYoZS5iZWFt'
        'cyAmJiBlLmJlYW1zLnNvbWUoeD0+eC5zdGF0ZT09PSdmaXJpbmcnKSkgb3JkZXIucHVzaChvd24g'
        'PyAnb3duJyA6ICdyYXknKTsgcmV0dXJuIF9yLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07CiAg'
        'ZHJhd1NoaXAgPSBmdW5jdGlvbihpbWcpeyBvcmRlci5wdXNoKGltZz09PXNob290ZXIuaW1nID8g'
        'J3Nob290ZXInIDogJ3NoaXAnKTsgcmV0dXJuIF9zLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH07'
        'CiAgdHJ5IHsgZHJhdygpOyB9IGZpbmFsbHkgeyBkcmF3QmVhbVJheXMgPSBfcjsgZHJhd1NoaXAg'
        'PSBfczsgfQogIGNvbnN0IGxhc3RSYXkgPSBvcmRlci5sYXN0SW5kZXhPZigncmF5JyksIGZpcnN0'
        'U2hpcCA9IE1hdGgubWluKC4uLlsnc2hpcCcsJ3Nob290ZXInXS5tYXAoaz0+b3JkZXIuaW5kZXhP'
        'ZihrKSkuZmlsdGVyKGk9Pmk+PTApKTsKICByLnJheURyYXduID0gbGFzdFJheT49MDsKICAvLyBV'
        'bmRlciB0aGUgc2hpcHMgaXQgaGl0cy4uLgogIHIudW5kZXJUaGVUYXJnZXRzID0gbGFzdFJheT49'
        'MCAmJiBmaXJzdFNoaXA+bGFzdFJheTsKICAvLyAuLi5idXQgb24gdG9wIG9mIHRoZSBzaGlwIHRo'
        'YXQgZmlyZXMgaXQuCiAgY29uc3Qgc2ggPSBvcmRlci5pbmRleE9mKCdzaG9vdGVyJyksIG93biA9'
        'IG9yZGVyLmluZGV4T2YoJ293bicpOwogIHIub25Ub3BPZlRoZVNob290ZXIgPSBzaD49MCAmJiBv'
        'd24+c2g7CiAgci5vd25TdHJldGNoU2hvcnQgPSBvd25IdWxsUnVuKHNob290ZXIsIHNob290ZXIu'
        'eCwgc2hvb3Rlci55LCAwKSA+IDAgJiYgb3duSHVsbFJ1bihzaG9vdGVyLCBzaG9vdGVyLngsIHNo'
        'b290ZXIueSwgMCkgPCAxMDAwOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ0tub3Nzb3Mgc2Nl'
        'bmU6IHNhbWUgc2t5IHdpdGhpbiBhIHJ1bicsICdtPTU1JywgYAogIGNvbnN0IHIgPSB7fTsKICBG'
        'Uy5zdGVwKDUwKTsKICAvLyBNYWtlIHN1cmUgdGhlcmUgaXMgc29tZXRoaW5nIGluIHRoZSBza3kg'
        'dG8gY29tcGFyZSwgdGhlbiB3cml0ZSB0aGUKICAvLyBzY2VuZSBkb3duIGFnYWluIGZyb20gdGhh'
        'dC4KICAvLyBUaGUgaGFybmVzcyBoYXMgbm8gcGxhbmV0IHBpY3R1cmVzLCBzbyB0d28gc3RhbmQt'
        'aW5zLgogIGJvZGllcyA9IFt7a2V5Oid0ZXN0cGxhbmV0Jywga2luZDoncGxhbmV0JywgbWV0YTp7'
        'cjowLGN4OjAuNSxjeTowLjV9LCB3OjIyMCwgeDozMTAsIHk6MTkwLCBzcGQ6MC4wNX0sCiAgICAg'
        'ICAgICAgIHtrZXk6J3Rlc3RzdW4nLCBraW5kOidzdW4nLCBtZXRhOntyOjAsY3g6MC41LGN5OjAu'
        'NX0sIHc6MTIwLCB4OjYyMCwgeToxMjAsIHNwZDowLjA0fV07CiAgZGVsZXRlIFNDRU5FUy5rbm9z'
        'c29zOyB1c2VTY2VuZSgna25vc3NvcycpOwogIGNvbnN0IG5lYiA9IG5lYkN1ciwga2V5cyA9IGJv'
        'ZGllcy5tYXAoYj0+Yi5rZXkpLmpvaW4oJywnKSwgcG9zID0gYm9kaWVzLm1hcChiPT5NYXRoLnJv'
        'dW5kKGIueCkrJy8nK01hdGgucm91bmQoYi55KSkuam9pbignLCcpLCBsYSA9IGxpZ2h0QW5nOwog'
        'IHIucG9ydGFsVGhlcmUgPSBlbmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nUDEnICYmIGUuaW1nPT09'
        'J2lua25vc3NvczQ1ZGVnJyAmJiBlLmludnVsbiAmJiBlLnNjZW5lcnkpOwogIC8vIFRvIDU2OiBh'
        'IGRpZmZlcmVudCBwbGFjZSwgYSBmcmVzaCByb2xsLgogIHN0YXJ0TmViRmFkZSgpOyBmb3IobGV0'
        'IGk9MDtpPDIwMDtpKyspIHRpY2tOZWJ1bGEoKTsKICB3YXZlT3ZlciA9IGZhbHNlOyBuZXh0V2F2'
        'ZSgpOyBGUy5zdGVwKDUpOwogIC8vIE9uIHRvIDU4IHRocm91Z2ggNTcsIHdpdGggdGhlIGJhY2tk'
        'cm9wIGZhZGluZyBvdmVyIGVhY2ggdGltZS4KICBzdGFydE5lYkZhZGUoKTsgRlMuc3RlcCg1KTsg'
        'bmV4dFdhdmUoKTsgRlMuc3RlcCg1KTsKICBzdGFydE5lYkZhZGUoKTsgRlMuc3RlcCg1KTsgbmV4'
        'dFdhdmUoKTsKICByLmF0VGhlR2F0ZSA9IHdhdmU9PT01ODsKICBjb25zdCBwbGFjZXNOb3cgPSBi'
        'b2RpZXMubWFwKGI9Pk1hdGgucm91bmQoYi54KSsnLycrTWF0aC5yb3VuZChiLnkpKS5qb2luKCcs'
        'Jyk7CiAgZm9yKGxldCBpPTA7aTwyMDA7aSsrKSB0aWNrTmVidWxhKCk7CiAgci5zYW1lQmFja2Ry'
        'b3AgPSBuZWJDdXI9PT1uZWI7CiAgci5zYW1lQm9kaWVzID0gYm9kaWVzLm1hcChiPT5iLmtleSku'
        'am9pbignLCcpPT09a2V5czsKICByLnNhbWVQbGFjZXMgPSBwbGFjZXNOb3c9PT1wb3M7CiAgci5z'
        'YW1lTGlnaHQgPSBsaWdodEFuZz09PWxhOwogIC8vIEEgbmV3IHJ1biByb2xscyBhbmV3OiB0aGUg'
        'Ym9vayBpcyBlbXB0eS4KICBsYXVuY2hHYW1lKCk7CiAgci5uZXdSdW5Gb3JnZXRzID0gKFNDUklQ'
        'VF9PTkU9PT01NSkgPyAhIVNDRU5FUy5rbm9zc29zICYmIE9iamVjdC5rZXlzKFNDRU5FUykubGVu'
        'Z3RoPT09MSA6IE9iamVjdC5rZXlzKFNDRU5FUykubGVuZ3RoPT09MDsKICByZXR1cm4gcjtgKTsK'
        'CnNjZW5hcmlvKCdNNTUgRGVyIEFuZmx1ZycsICdtPTU1JywgYAogIGNvbnN0IHIgPSB7fTsKICBs'
        'ZXQgayA9IG51bGw7CiAgRlMudW50aWwoKCk9PnsgayA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09'
        'PSdLMScgJiYgIShlLndhcnA+MCkpOyByZXR1cm4gISFrOyB9LCAyMDAwLCB0cnVlKTsKICByLmNy'
        'dWlzZXJGcm9tVGhlTGVmdCA9ICEhayAmJiBrLnggPCAxMDAgJiYgay5lc2NhcGluZz4wICYmIGsu'
        'ZXNjV2FycDsKICBrLmhwID0gay5tYXhIcCA9IDFlNzsKICBjb25zdCBmID0gRlMudW50aWwoKCk9'
        'Pnsgay5ocCA9IGsubWF4SHA7IHJldHVybiBrLndhcnBPdXQ+MDsgfSwgNjAwMCwgdHJ1ZSk7CiAg'
        'ci5qdW1wc0F0VGhlUG9ydGFsID0gZj49MCAmJiBrLnggPj0gUE9SVEFMX1ggJiYgay54IDwgVyAm'
        'JiBrLnBvcnRhbFdhcnA9PT10cnVlOwogIEZTLnN0ZXAoNSk7CiAgci5mYWlsQ2FyZCA9ICEhb2Jq'
        'Q2FyZCAmJiBvYmpDYXJkLnR4dD09PSdBIENSVUlTRVIgUkVBQ0hFRCBUSEUgUE9SVEFMJzsKICBy'
        'ZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNTUgYWxsIHN0b3BwZWQnLCAnbT01NScsIGAKICBjb25z'
        'dCByID0ge307CiAgbGV0IGsgPSBudWxsOwogIEZTLnVudGlsKCgpPT57IGsgPSBlbmVtaWVzLmZp'
        'bmQoZT0+ZS51aWQ9PT0nSzEnICYmICEoZS53YXJwPjApKTsgcmV0dXJuICEhazsgfSwgMjAwMCwg'
        'dHJ1ZSk7CiAgZm9yKGNvbnN0IHMgb2Ygay5zdWJzKSBpZihzLmlkPT09J2VuZ2luZXMnKXsgcy5k'
        'ZWFkID0gdHJ1ZTsgcy5ocCA9IDA7IH0KICBjb25zdCB4MCA9IGsueDsgRlMuc3RlcCgyMDApOwog'
        'IHIuZW5naW5lc1N0b3BIZXIgPSBNYXRoLmFicyhrLngteDApIDwgMC4wMTsKICBjb25zdCBzZWVu'
        'ID0ge307CiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT57IGZvcihjb25zdCBlIG9mIGVuZW1pZXMp'
        'IGlmKC9eSy8udGVzdChlLnVpZHx8JycpICYmICEoZS53YXJwPjApKXsgc2VlbltlLnVpZF09MTsg'
        'ZS5ocCA9IDA7IH0KICAgIHJldHVybiAhIW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nQUxMIENS'
        'VUlTRVJTIFNUT1BQRUQnOyB9LCAxMjAwMCwgdHJ1ZSk7CiAgci5jb21wbGV0ZUNhcmQgPSB0Pj0w'
        'ICYmIE9iamVjdC5rZXlzKHNlZW4pLmxlbmd0aD09PTQ7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJp'
        'bygnTTU2IERpZSBWZXJyYWV0ZXInLCAnbT01NicsIGAKICBjb25zdCByID0ge307CiAgRlMuc3Rl'
        'cCgzMDApOwogIGNvbnN0IGExID0gYWxsaWVzLmZpbmQoYT0+YS51aWQ9PT0nQTEnKTsKICByLmFs'
        'bGllZExldmlhdGhhbiA9ICEhYTEgJiYgYTEuaW1nPT09J2NybGV2aWF0aGFuJzsKICByLmRlaW1v'
        'c1RvbyA9IGFsbGllcy5zb21lKGE9PmEudWlkPT09J0EyJyAmJiBhLmltZz09PSdjb2RlaW1vcycp'
        'OwogIEZTLnVudGlsKCgpPT4hYWxsaWVzLmluY2x1ZGVzKGExKSwgMzAwMCwgdHJ1ZSk7CiAgY29u'
        'c3QgdCA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdBMScpOwogIHIuZ29lc092ZXIgPSAhIXQg'
        'JiYgdC5zaWRlPT09J2VuZW15JyAmJiB0LmltZz09PSdudGZjcmxldmlhdGhhbic7CiAgLy8gU2hl'
        'IHN0YXlzIG9uIHRoZSBsZWZ0IGFuZCBmYWNlcyBpbnRvIHRoZSBmaWVsZCwgbm90IHRoZSBlZGdl'
        'IGJlaGluZCBoZXIuCiAgci5mYWNlc0ludG9UaGVGaWVsZCA9ICEhdCAmJiB0LnggPCBXKjAuNSAm'
        'JiB0LmZsaXA9PT1uZWVkc0ZsaXAodC5pbWcsIGZhbHNlKTsKICBjb25zdCBfdHggPSB0Lng7IEZT'
        'LnN0ZXAoMjAwKTsKICByLnN0YXlzV2hlcmVTaGVJcyA9IE1hdGguYWJzKHQueC1fdHgpIDwgMTsK'
        'ICBGUy5zdGVwKDMpOwogIHIubmV3T2JqZWN0aXZlID0gbWlzc2lvbk9iaj09PSdERVNUUk9ZIFRI'
        'RSBMRVZJQVRIQU4nOwogIHIubW9yZUNvbWluZyA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdF'
        'MicpIHx8IHNwYXduUS5zb21lKHE9PnEudWlkPT09J0UyJyB8fCBxLnVpZD09PSdCMScpIHx8IGVu'
        'ZW1pZXMuc29tZShlPT5lLnVpZD09PSdCMScpOwogIHQuaHAgPSAwOwogIHIuY29tcGxldGVDYXJk'
        'ID0gRlMudW50aWwoKCk9PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdUUkFJVE9SIERFU1RS'
        'T1lFRCcsIDE1MDAsIGZhbHNlKSA+PSAwOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001NyBE'
        'aWUgTmFjaGh1dCcsICdtPTU3JywgYAogIGNvbnN0IHIgPSB7fTsKICBjb25zdCBwcmV2U2VjID0g'
        'cGxheWVyLnNlYzsKICBGUy5zdGVwKDMwMCk7CiAgci51cnNhV2l0aFN0aWxldHRvID0gcGxheWVy'
        'LnNoaXA9PT0nYm91cnNhJyAmJiBwbGF5ZXIuc2VjPT09J3N0aWxldHRvJzsKICBjb25zdCB1cyA9'
        'IFsnSzEnLCdLMicsJ0QxJ10ubWFwKGlkPT5lbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT1pZCkpOwog'
        'IHIudGhyZWVIb2xkVGhlUmVhciA9IHVzLmV2ZXJ5KEJvb2xlYW4pOwogIGRhbWFnZUVuZW15KHVz'
        'WzBdLCB1c1swXS5tYXhIcCo1LCB1c1swXS54LCB1c1swXS55LCB0cnVlLCAnYm9sdCcpOyBGUy5z'
        'dGVwKDIpOwogIHIuY2Fubm90QmVEZXN0cm95ZWRZZXQgPSBlbmVtaWVzLmluY2x1ZGVzKHVzWzBd'
        'KTsKICAvLyBBIFN0aWxldHRvIHRha2VzIGEgY3J1aXNlcidzIHN5c3RlbSB3aXRoIG9uZSBib21i'
        'LCBhIGNvcnZldHRlJ3Mgd2l0aCB0d28uCiAgY29uc3QgYm9tYnMgPSB1PT57IGNvbnN0IHMgPSB1'
        'LnN1YnMuZmluZCh4PT54LmlkPT09J2VuZ2luZXMnKTsgbGV0IG4gPSAwOwogICAgd2hpbGUoIXMu'
        'ZGVhZCAmJiBuPDEwKXsgY29uc3QgcCA9IHN1YlBvcyh1LCBzKTsgc3ViU3RyaWtlKHUsIHNlY0Rl'
        'Zignc3RpbGV0dG8nKS5kbWcsIHAueCwgcC55KTsgbisrOyB9IHJldHVybiBuOyB9OwogIHIub25l'
        'Qm9tYlBlckNydWlzZXJTeXN0ZW0gPSBib21icyh1c1swXSk9PT0xOwogIHIudHdvQm9tYnNQZXJD'
        'b3J2ZXR0ZVN5c3RlbSA9IGJvbWJzKHVzWzJdKT09PTI7CiAgZm9yKGNvbnN0IHUgb2YgdXMpIGZv'
        'cihjb25zdCBzIG9mIHUuc3VicykgaWYocy5pZD09PSdlbmdpbmVzJ3x8cy5pZD09PSd3ZWFwb25z'
        'Jyl7IHMuZGVhZCA9IHRydWU7IHMuaHAgPSAwOyB9CiAgY29uc3QgYyA9IEZTLnVudGlsKCgpPT4h'
        'IW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nUkVBUkdVQVJEIERJU0FCTEVEJywgMTUwMCwgZmFs'
        'c2UpOwogIHIuY29tcGxldGVDYXJkID0gYz49MDsKICByLmxlZnRBc1dyZWNrcyA9IHVzLmV2ZXJ5'
        'KHU9PmVuZW1pZXMuaW5jbHVkZXModSkgJiYgdS5zY2VuZXJ5KTsKICBjb25zdCB3ID0gRlMudW50'
        'aWwoKCk9PndhdmU9PT01OCwgOTAwMCwgdHJ1ZSwgdHJ1ZSk7CiAgci5uZXh0V2F2ZU93blNoaXBC'
        'YWNrID0gdz49MCAmJiBwbGF5ZXIuc2hpcCE9PSdib3Vyc2EnICYmIHBsYXllci5zZWMhPT0nc3Rp'
        'bGV0dG8nOwogIHJldHVybiByO2ApOwoKc2NlbmFyaW8oJ001OCBEYXMgVG9yJywgJ209NTgnLCBg'
        'CiAgY29uc3QgciA9IHt9OwogIEZTLnN0ZXAoNDAwKTsKICByLnBvcnRhbFRoZXJlID0gZW5lbWll'
        'cy5zb21lKGU9PmUudWlkPT09J1AxJyAmJiBlLmltZz09PSdpbmtub3Nzb3M0NWRlZycpOwogIHIu'
        'c2VudHJ5TGluZSA9IGVuZW1pZXMuZmlsdGVyKGU9PmUudWlkPT09J0cxJykubGVuZ3RoPT09NjsK'
        'ICByLnR3b0NydWlzZXJzID0gZW5lbWllcy5zb21lKGU9PmUudWlkPT09J0sxJyAmJiBlLmltZz09'
        'PSdudGZjcmZlbnJpcycpICYmIGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdLMicgJiYgZS5pbWc9'
        'PT0nbnRmY3JhZW9sdXMnKTsKICBmb3IoY29uc3QgZSBvZiBlbmVtaWVzKSBpZigvXihLfEcpLy50'
        'ZXN0KGUudWlkfHwnJykpIGUuaHAgPSAwOwogIHIuY29tcGxldGVDYXJkID0gRlMudW50aWwoKCk9'
        'PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdQT1JUQUwgREVGRU5DRSBCUk9LRU4nLCAxNTAw'
        'LCBmYWxzZSkgPj0gMDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNTkgRGllIGxldHp0ZSBT'
        'cGVycmUnLCAnbT01OScsIGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCg1MDApOwogIGNvbnN0'
        'IHYxID0gZW5lbWllcy5maW5kKGU9PmUudWlkPT09J1YxJyksIHYyID0gZW5lbWllcy5maW5kKGU9'
        'PmUudWlkPT09J1YyJyk7CiAgci50d29EZXN0cm95ZXJzID0gISF2MSAmJiAhIXYyICYmIHYxLmlt'
        'Zz09PSdudGZkZWhlY2F0ZScgJiYgdjIuaW1nPT09J250ZmRlb3Jpb24nOwogIHIuaW5Gcm9udE9m'
        'VGhlUG9ydGFsID0gZW5lbWllcy5zb21lKGU9PmUudWlkPT09J1AxJyk7CiAgci5maWdodGVyQ292'
        'ZXIgPSBhbGxpZXMuZmlsdGVyKGE9PmEuc21hbGwgJiYgYS51aWQ9PT0nVzEnKS5sZW5ndGggPj0g'
        'MjsKICB2MS5ocCA9IDA7IEZTLnN0ZXAoMzAwKTsKICByLm5vdFlldCA9ICEob2JqQ2FyZCAmJiBv'
        'YmpDYXJkLnR4dD09PSdUSEUgV0FZIFRPIFRIRSBQT1JUQUwgSVMgT1BFTicpOwogIHYyLmhwID0g'
        'MDsKICByLmNvbXBsZXRlQ2FyZCA9IEZTLnVudGlsKCgpPT4hIW9iakNhcmQgJiYgb2JqQ2FyZC50'
        'eHQ9PT0nVEhFIFdBWSBUTyBUSEUgUE9SVEFMIElTIE9QRU4nLCAzMDAwLCBmYWxzZSkgPj0gMDsK'
        'ICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNjAgRGVyIFNwcnVuZycsICdtPTYwJywgYAogIGNv'
        'bnN0IHIgPSB7fTsKICBzY29yZSA9IDMwMDA7CiAgY29uc3QgZXNjMCA9IGljZW5Fc2NhcGVzOwog'
        'IGxldCB2ID0gbnVsbDsKICBGUy51bnRpbCgoKT0+eyB2ID0gZW5lbWllcy5maW5kKGU9PmUudWlk'
        'PT09J1YxJyAmJiAhKGUud2FycD4wKSk7IHJldHVybiAhIXY7IH0sIDMwMDAsIHRydWUpOwogIHIu'
        'aWNlbmlSdW5zID0gISF2ICYmIHYuaWNlbmkgJiYgdi5lc2NhcGluZz4wOwogIHIubm90aGluZ1Rv'
        'U2hvb3RPdXQgPSAhIXYgJiYgIXYuc3Vicy5zb21lKHM9PnMuaWQ9PT0nZW5naW5lcycgfHwgcy5p'
        'ZD09PSduYXZpZ2F0aW9uJyk7CiAgZGFtYWdlRW5lbXkodiwgdi5tYXhIcCo1LCB2LngsIHYueSwg'
        'dHJ1ZSwgJ2JvbHQnKTsgRlMuc3RlcCgyKTsKICByLmNhbm5vdEJlRGVzdHJveWVkID0gZW5lbWll'
        'cy5pbmNsdWRlcyh2KSAmJiB2LmhwPjA7CiAgY29uc3QgaiA9IEZTLnVudGlsKCgpPT52LndhcnBP'
        'dXQ+MCwgOTAwMCwgdHJ1ZSk7CiAgci50aHJvdWdoVGhlUG9ydGFsID0gaj49MCAmJiB2LnBvcnRh'
        'bFdhcnA9PT10cnVlICYmIHYueCA+PSBQT1JUQUxfWDsKICBGUy51bnRpbCgoKT0+IWVuZW1pZXMu'
        'aW5jbHVkZXModiksIDEwMDAsIGZhbHNlKTsKICBGUy5zdGVwKDUpOwogIHIuc2hlR290QXdheSA9'
        'IGljZW5Fc2NhcGVzPT09ZXNjMCsxICYmIE5PVElDRVMuc29tZShuPT5uLnR4dD09PSdUSEUgSUNF'
        'TkkgSVMgVEhST1VHSCBUSEUgS05PU1NPUycpOwogIGZvcihjb25zdCBlIG9mIGVuZW1pZXMpIGlm'
        'KC9eKEt8QykvLnRlc3QoZS51aWR8fCcnKSkgZS5ocCA9IDA7CiAgci5jb21wbGV0ZUNhcmQgPSBG'
        'Uy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J0VTQ09SVCBERVNUUk9ZRUQn'
        'LCAzMDAwLCBmYWxzZSkgPj0gMDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdQcmFjdGljZSBt'
        'b2RlJywgJ209NDAmcHJhY3RpY2U9MScsIGAKICBjb25zdCByID0ge307CiAgRlMuc3RlcCgxMDAp'
        'OwogIHIub25Gcm9tVGhlQWRkcmVzcyA9IHByYWN0aWNlTW9kZT09PXRydWU7CiAgci50ZW5PZkVh'
        'Y2ggPSBUSUNLRVRfT1JERVIuZXZlcnkoaz0+dGlja2V0c1trXT49MTApOwogIGNvbnN0IGwwID0g'
        'bGl2ZXM7IHBsYXllckRpZSgpOwogIHIubm9MaWZlTG9zdCA9IGxpdmVzPT09bDA7CiAgdGlja2V0'
        'cy5jcnVpc2VyID0gMjsKICBGUy51bnRpbCgoKT0+d2F2ZU92ZXIsIDQwMDAwLCBmYWxzZSwgdHJ1'
        'ZSk7IElURU1TLmxlbmd0aCA9IDA7CiAgY29uc3QgdyA9IHdhdmU7IEZTLnVudGlsKCgpPT53YXZl'
        'PT09dysxLCA2MDAwLCBmYWxzZSwgZmFsc2UpOwogIHIudG9wcGVkVXBOZXh0V2F2ZSA9IHRpY2tl'
        'dHMuY3J1aXNlcj49MTA7CiAgcHJhY3RpY2VNb2RlID0gZmFsc2U7IGNvbnN0IGwxID0gbGl2ZXM7'
        'IHBsYXllckRpZSgpOwogIHIub2ZmQ29zdHNBTGlmZSA9IGxpdmVzPT09bDEtMTsKICByZXR1cm4g'
        'cjtgKTsKCnNjZW5hcmlvKCdQcmFjdGljZSBsb2cnLCAnbT00MiZwcmFjdGljZT0xJywgYAogIGNv'
        'bnN0IHIgPSB7fTsKICBGUy5zdGVwKDIwMCk7CiAgci5yZWNvcmRpbmcgPSAhIVBMICYmIFBMLndh'
        'dmU9PT00MiAmJiBQTC5uYW1lPT09J0RpZSBIZWNhdGUnOwogIC8vIEEgZGVhdGggYnkgYSBiZWFt'
        'IG9mIGEgbmFtZWQgc2hpcC4KICBjb25zdCB2ID0gZW5lbWllcy5maW5kKGU9PmUuYmVhbXMgJiYg'
        'ZS5iZWFtcy5sZW5ndGgpIHx8IGVuZW1pZXNbMF07CiAgcGxvZ1NyYygnYmVhbScsIHYpOyBwbGF5'
        'ZXIuaHAgPSAwOyBwbGF5ZXJEaWUoKTsgRlMuc3RlcCgyKTsKICByLmRlYXRoV2l0aENhdXNlID0g'
        'UEwuZGVhdGhzLmxlbmd0aD09PTEgJiYgL15iZWFtIC0gLy50ZXN0KFBMLmRlYXRoc1swXS5jYXVz'
        'ZSk7CiAgLy8gUG9pbnRzIGxvc3QgYW5kIHdoeS4KICBzY29yZSA9IDEwMDA7IEZTLnN0ZXAoMSk7'
        'CiAgcGxvZ0xvc3MoJ2VzY2FwZWQnLCB2KTsgc2NvcmUgPSBNYXRoLm1heCgwLCBzY29yZS0xMDAp'
        'OyBGUy5zdGVwKDIpOwogIHIubG9zc1dpdGhSZWFzb24gPSBQTC5sb3NzPj0xMDAgJiYgUEwuZXZl'
        'bnRzLnNvbWUoZT0+L2VzY2FwZWQvLnRlc3QoZS50eHQpKTsKICAvLyBUaWNrZXRzIHVzZWQgYXJl'
        'IGNvdW50ZWQsIHRoZSBwcmFjdGljZSB0b3AtdXAgaXMgbm90IGNvdW50ZWQgYXMgZWFybmVkLgog'
        'IGNvbnN0IGdvdDAgPSBwbG9nU3VtKFBMLnRHb3QpOwogIHRpY2tldHMuY3J1aXNlci0tOyBGUy5z'
        'dGVwKDIpOwogIHIudGlja2V0VXNlZCA9IFBMLnRVc2VkLmNydWlzZXI9PT0xOwogIHByYWN0aWNl'
        'VGlja2V0cygpOyBGUy5zdGVwKDIpOwogIHIudG9wVXBOb3RFYXJuZWQgPSBwbG9nU3VtKFBMLnRH'
        'b3QpPT09Z290MDsKICAvLyBBbiBvYmplY3RpdmUgY2FyZCBnb2VzIGludG8gdGhlIGxvZy4KICBv'
        'YmpBbm5vdW5jZSgnT0JKRUNUSVZFIENPTVBMRVRFJywgJ1RFU1QgRE9ORScsICdkb25lJyk7IEZT'
        'LnN0ZXAoMik7CiAgci5vYmplY3RpdmVMb2dnZWQgPSBQTC5jYXJkcy5zb21lKGM9PmMudHh0PT09'
        'J1RFU1QgRE9ORScgJiYgYy50b25lPT09J2RvbmUnKTsKICAvLyBEYW1hZ2UgYnkgc291cmNlLgog'
        'IC8vIEZTLnN0ZXAgaGVhbHMgdGhlIHNoaXAgZmlyc3QsIHNvIG9uZSBwbGFpbiB1cGRhdGUgaGVy'
        'ZS4KICBwbG9nU3JjKCdib2x0Jyk7IHBsYXllci5ocCAtPSAxMDsgdXBkYXRlKCk7CiAgci5kYW1h'
        'Z2VCeVNvdXJjZSA9IChQTC5kbWdCeS5ib2x0fHwwKSA+PSAxMDsKICAvLyBUaGUgcGxheWVyJ3Mg'
        'b3duIGJvbHRzIGFyZSBjb3VudGVkLCB0aGUgZXNjb3J0cycgYXJlIG5vdC4KICBjb25zdCBiMCA9'
        'IFBMLmJvbHRzOyBwbGF5ZXIuZlQgPSAwOyBwU2hvb3QoKTsgRlMuc3RlcCgxKTsKICByLmJvbHRz'
        'Q291bnRlZCA9IFBMLmJvbHRzID4gYjA7CiAgLy8gQ2xlYXIgdGhlIHdhdmU6IGl0IGlzIGNsb3Nl'
        'ZCBhbmQgdGhlIG5leHQgb25lIG9wZW5zLgogIEZTLnVudGlsKCgpPT53YXZlT3ZlciwgNDAwMDAs'
        'IGZhbHNlLCB0cnVlKTsgSVRFTVMubGVuZ3RoID0gMDsKICBGUy5zdGVwKDIpOwogIHIuY2FyZFNo'
        'b3duID0gKGZ1bmN0aW9uKCl7IGxldCBuPTA7IGNvbnN0IF90PXRoUGxhdGU7IHRoUGxhdGU9ZnVu'
        'Y3Rpb24oKXsgbisrOyByZXR1cm4gX3QuYXBwbHkodGhpcywgYXJndW1lbnRzKTsgfTsKICAgIHRy'
        'eXsgZHJhd1Bsb2dDYXJkKCk7IH0gZmluYWxseSB7IHRoUGxhdGU9X3Q7IH0gcmV0dXJuIG4+MDsg'
        'fSkoKTsKICBjb25zdCB3ID0gd2F2ZTsgRlMudW50aWwoKCk9PndhdmU9PT13KzEsIDYwMDAsIGZh'
        'bHNlLCBmYWxzZSk7CiAgci5jbG9zZWRBbmROZXh0ID0gUExPRy5sZW5ndGg9PT0xICYmIFBMT0db'
        'MF0ud2F2ZT09PTQyICYmIFBMLndhdmU9PT00MzsKICBjb25zdCB0ID0gcGxvZ1RleHQoKTsKICBy'
        'LnRleHRFeHBvcnQgPSAvV0FWRSA0MiAtIERpZSBIZWNhdGUvLnRlc3QodCkgJiYgL2RpZWQ6IGJl'
        'YW0vLnRlc3QodCkgJiYgL3RpbWVsaW5lOi8udGVzdCh0KTsKICAvLyBUaGUgdGFibGUgZHJhd3Ms'
        'IGFuZCBhIG5ldyBydW4gc3RhcnRzIGFuIGVtcHR5IGxvZy4KICBzZXRTZXR0aW5ncyh0cnVlKTsg'
        'cGxvZ09wZW4gPSB0cnVlOyBkcmF3KCk7CiAgci50YWJsZURyYXdzID0gKHdpbmRvdy5fcGxvZ1Jl'
        'Y3RzfHxbXSkuc29tZSh4PT54LmFjdD09PSdjb3B5Jyk7CiAgc2V0U2V0dGluZ3MoZmFsc2UpOwog'
        'IHIuY2xvc2VzV2l0aFNldHRpbmdzID0gcGxvZ09wZW49PT1mYWxzZTsKICBsYXVuY2hHYW1lKCk7'
        'CiAgci5uZXdSdW5FbXB0eSA9IFBMT0cubGVuZ3RoPT09MDsKICByZXR1cm4gcjtgKTsKCnNjZW5h'
        'cmlvKCdhbGxpZWQgY3JhZnQgaG9sZCBmaXJlIHdpdGggbm90aGluZyB0byBzaG9vdCcsICdtPTQ0'
        'JywgYAogIGNvbnN0IHIgPSB7fTsKICBGUy5zdGVwKDMwMCk7CiAgY29uc3QgZmkgPSBta0FsbHlT'
        'bWFsbCgnZmlnaHRlcicsICd0ZXJyYW4nLCAnZmloZXJjJywgSCowLjUpOwogIGNvbnN0IGJvID0g'
        'bWtBbGx5U21hbGwoJ2JvbWJlcicsICd0ZXJyYW4nLCAnYm9hcnRlbWlzJywgSCowLjYpOwogIGZp'
        'LndhcnAgPSAwOyBiby53YXJwID0gMDsgYWxsaWVzLnB1c2goZmksIGJvKTsKICAvLyBPbmx5IHRo'
        'aW5ncyBhbiBlc2NvcnQgaGFzIG5vIGJ1c2luZXNzIHNob290aW5nIGF0OiBub3RoaW5nLCBhbmQg'
        'YW4KICAvLyBpbnZ1bG5lcmFibGUgc3RhdGlvbiBhdCB0aGUgcmlnaHQgZWRnZS4KICBjb25zdCBr'
        'ZWVwID0gZW5lbWllczsgZW5lbWllcyA9IFtdOwogIGNvbnN0IHN0ID0gbWtFbmVteSgnY3JfbnRm'
        'JywgJ250ZmNyYWVvbHVzJywgSCowLjUpOyBzdC54ID0gVy00MDsgc3Qud2FycCA9IDA7CiAgc3Qu'
        'aW52dWxuID0gdHJ1ZTsgc3Quc2NlbmVyeSA9IHRydWU7CiAgY29uc3Qgc2hvdHMgPSAoKT0+cEJ1'
        'bGxldHMuZmlsdGVyKGI9PmIuYWxseSkubGVuZ3RoOwogIGxldCBuID0gMDsKICBmb3IoY29uc3Qg'
        'bGlzdCBvZiBbW10sIFtzdF1dKXsKICAgIGVuZW1pZXMgPSBsaXN0OwogICAgZm9yKGNvbnN0IGEg'
        'b2YgW2ZpLCBib10pewogICAgICBhLmhlYWQgPSAwOyBhLnggPSBXKjAuNDsKICAgICAgZm9yKGxl'
        'dCBrPTA7azw0MDtrKyspewogICAgICAgIGNvbnN0IGIwID0gc2hvdHMoKTsKICAgICAgICBhLmZU'
        'ID0gMDsgc21hbGxGaXJlKGEsIHNtYWxsVGFyZ2V0KGEpKTsKICAgICAgICBpZihhLnNlY1QpIGZv'
        'cihsZXQgaT0wO2k8YS5zZWNULmxlbmd0aDtpKyspIGEuc2VjVFtpXSA9IDA7CiAgICAgICAgZmly'
        'ZVNlY29uZGFyaWVzKGEsIFdQTlthLnR5cGVdKTsKICAgICAgICBuICs9IHNob3RzKCktYjA7CiAg'
        'ICAgIH0KICAgIH0KICB9CiAgZW5lbWllcyA9IGtlZXA7CiAgci5ub1Nob3RzQXROb3RoaW5nID0g'
        'bj09PTA7CiAgci5fbiA9IG47CiAgLy8gV2l0aCBhIHJlYWwgZW5lbXkgaW4gcmVhY2ggdGhleSBz'
        'dGlsbCBmaXJlLgogIGNvbnN0IGZvZSA9IGVuZW1pZXMuZmluZChlPT5lLnR5cGU9PT0nZmlnaHRl'
        'cicgJiYgIShlLndhcnA+MCkpIHx8IGVuZW1pZXMuZmluZChlPT4hKGUud2FycD4wKSAmJiAhZS5p'
        'bnZ1bG4pOwogIGxldCBtID0gMDsKICBpZihmb2UpeyBmaS54ID0gZm9lLngtODA7IGZpLnkgPSBm'
        'b2UueTsgZmkuaGVhZCA9IDA7CiAgICBmb3IobGV0IGs9MDtrPDU7aysrKXsgY29uc3QgYjAgPSBz'
        'aG90cygpOyBmaS5mVCA9IDA7IHNtYWxsRmlyZShmaSwgZm9lKTsgbSArPSBzaG90cygpLWIwOyB9'
        'IH0KICByLnN0aWxsRmlyZUF0RW5lbWllcyA9IG0+MDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlv'
        'KCdNNDMgRGVyIE5URi1Lb252b2knLCAnbT00MycsIGAKICBjb25zdCByID0ge307CiAgRlMuc3Rl'
        'cCg2MDApOwogIGNvbnN0IHQgPSBlbmVtaWVzLmZpbHRlcihlPT5lLnVpZD09PSdUMScpOwogIHIu'
        'dGhyZWVUcml0b25zID0gdC5sZW5ndGg9PT0zICYmIHQuZXZlcnkoZT0+ZS5pbWc9PT0nZnJ0cml0'
        'b24nICYmIGUuZXNjYXBpbmc+MCk7CiAgci5zYXlzU2NhbkZpcnN0ID0gbWlzc2lvbk9iaj09PSdT'
        'Q0FOIFRIRSBUUklUT05TJzsKICBkYW1hZ2VFbmVteSh0WzBdLCB0WzBdLm1heEhwKjUsIHRbMF0u'
        'eCwgdFswXS55LCB0cnVlLCAnYm9sdCcpOyBGUy5zdGVwKDIpOwogIHIuY2Fubm90RGllVW5zY2Fu'
        'bmVkID0gZW5lbWllcy5pbmNsdWRlcyh0WzBdKTsKICByLm5vQWVvbHVzID0gIWVuZW1pZXMuc29t'
        'ZShlPT5lLnVpZD09PSdLMScpICYmICFzcGF3blEuc29tZShxPT5xLnVpZD09PSdLMScpOwogIC8v'
        'IFVuZGVyIGZpcmUgdGhlIHdob2xlIHRpbWU6IGluIHRoaXMgbWlzc2lvbiB0aGUgc2NhbiBzdGls'
        'bCBmaWxscy4KICBmb3IoY29uc3QgZSBvZiB0KSBmb3IobGV0IGk9MDtpPFNDQU5fVElNRSsyMDtp'
        'KyspewogICAgcGxheWVyLnggPSBlLng7IHBsYXllci55ID0gZS55OyBNT1VTRS54ID0gZS54OyBN'
        'T1VTRS55ID0gZS55OwogICAgcGxheWVyLnNoRGVsYXkgPSA5MDsgcGxheWVyLmhwID0gcGxheWVy'
        'Lm1heEhwOyBGUy5zdGVwKDEpOyB9CiAgci5hbGxTY2FubmVkID0gdC5ldmVyeShlPT5lLnNjYW5u'
        'ZWQpOwogIEZTLnN0ZXAoMik7CiAgci50aGVuRGVzdHJveSA9IG1pc3Npb25PYmo9PT0nREVTVFJP'
        'WSBUSEUgQ09OVk9ZJzsKICBGUy5zdGVwKDIwMCk7CiAgci5hZW9sdXNBZnRlclRoZVNjYW4gPSBl'
        'bmVtaWVzLnNvbWUoZT0+ZS51aWQ9PT0nSzEnICYmIGUuaW1nPT09J250ZmNyYWVvbHVzJyk7CiAg'
        'Zm9yKGNvbnN0IGUgb2YgdCkgZS5ocCA9IDA7CiAgY29uc3QgZG9uZSA9IEZTLnVudGlsKCgpPT4h'
        'IW9iakNhcmQgJiYgb2JqQ2FyZC50eHQ9PT0nQ09OVk9ZIERFU1RST1lFRCcsIDE1MDAsIGZhbHNl'
        'KTsKICByLmNvbXBsZXRlQ2FyZCA9IGRvbmU+PTA7CiAgcmV0dXJuIHI7YCk7CgpzY2VuYXJpbygn'
        'TTQzIGEgVHJpdG9uIGdldHMgYXdheTogZmFpbGVkJywgJ209NDMnLCBgCiAgRlMuc3RlcCgzMDAp'
        'OwogIGNvbnN0IHQgPSBlbmVtaWVzLmZpbHRlcihlPT5lLnVpZD09PSdUMScpOwogIGZvcihjb25z'
        'dCBlIG9mIHQpeyBlLnNjYW5uZWQgPSB0cnVlOyBlLmVzY2FwaW5nID0gMzsgfQogIGNvbnN0IGYg'
        'PSBGUy51bnRpbCgoKT0+ISFvYmpDYXJkICYmIG9iakNhcmQudG9uZT09PSdmYWlsJywgMzAwMCwg'
        'ZmFsc2UpOwogIHJldHVybiB7ZmFpbENhcmQ6IGY+PTAgJiYgb2JqQ2FyZC50eHQ9PT0nQSBUUklU'
        'T04gR09UIEFXQVknfTtgKTsKCnNjZW5hcmlvKCdNNDQgRGVyIFNjaHdhcm0nLCAnbT00NCcsIGAK'
        'ICBjb25zdCByID0ge307CiAgRlMuc3RlcCg0MDApOwogIHIubm9BbGx5V2luZ0F0U3RhcnQgPSAh'
        'YWxsaWVzLnNvbWUoYT0+YS5zbWFsbCk7CiAgci5kZWltb3NUb1JlYXJtID0gYWxsaWVzLnNvbWUo'
        'YT0+YS51aWQ9PT0nQTEnICYmIGEuaW1nPT09J2NvZGVpbW9zJyk7CiAgY29uc3Qgc2VlbiA9IHt9'
        'OwogIGxldCBtYXhXaW5nID0gMCwgc3RyYXkgPSAwOwogIEZTLnVudGlsKCgpPT57IGZvcihjb25z'
        'dCBlIG9mIGVuZW1pZXMpIGlmKGUudWlkKSBzZWVuW2UudWlkXT0xOyBmb3IoY29uc3QgYSBvZiBh'
        'bGxpZXMpIGlmKGEudWlkKSBzZWVuW2EudWlkXT0xOwogICAgY29uc3Qgc20gPSBhbGxpZXMuZmls'
        'dGVyKGE9PmEuc21hbGwgJiYgIWEuZGVhZCk7IG1heFdpbmcgPSBNYXRoLm1heChtYXhXaW5nLCBz'
        'bS5sZW5ndGgpOwogICAgaWYoc20uc29tZShhPT5hLnVpZCE9PSdXMicpKSBzdHJheSsrOyByZXR1'
        'cm4gd2F2ZU92ZXI7IH0sIDMwMDAwLCB0cnVlKTsKICAvLyBPbmUgYWxsaWVkIHdpbmcsIHRoZSBv'
        'bmUgdGhlIG1pc3Npb24gc2VuZHM7IHRoZSBEZWltb3MgYWRkcyBub25lLgogIHIub25lQWxseVdp'
        'bmdPbmx5ID0gbWF4V2luZz4wICYmIG1heFdpbmc8PTQgJiYgc3RyYXk9PT0wOwogIHIuYWxsVGhl'
        'V2luZ3MgPSBbJ0UxJywnRTInLCdFMycsJ0IxJywnVzInXS5ldmVyeShrPT5zZWVuW2tdKTsKICBy'
        'ZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNDUgRGFzIE5hZGVsb2VocicsICdtPTQ1JywgYAogIGNv'
        'bnN0IHIgPSB7fTsKICBGUy5zdGVwKDUwMCk7CiAgY29uc3QgayA9IGVuZW1pZXMuZmlsdGVyKGU9'
        'Pi9eS1sxMjNdJC8udGVzdChlLnVpZHx8JycpKTsKICByLnRocmVlRmVucmlzID0gay5sZW5ndGg9'
        'PT0zICYmIGsuZXZlcnkoZT0+ZS5pbWc9PT0nbnRmY3JmZW5yaXMnKTsKICBjb25zdCB5cyA9IGsu'
        'bWFwKGU9PmUueSkuc29ydCgoYSxiKT0+YS1iKTsKICByLmluU2VwYXJhdGVMYW5lcyA9IHlzLmxl'
        'bmd0aD09PTMgJiYgeXNbMV0teXNbMF0gPiA0MCAmJiB5c1syXS15c1sxXSA+IDQwOwogIGNvbnN0'
        'IG8gPSBhbGxpZXMuZmluZChhPT5hLnVpZD09PSdBMScpOwogIHIub3Jpb25Dcm9zc2VzID0gISFv'
        'ICYmIG8udHJhbnNpdD09PXRydWU7CiAgby5ocCA9IG8ubWF4SHAgPSAxZTc7IGZvcihjb25zdCBz'
        'IG9mIG8uc3Vic3x8W10pIHMuaHAgPSBzLm1heEhwID0gMWU3OwogIGxldCByb2NrcyA9IDA7CiAg'
        'Y29uc3QgdCA9IEZTLnVudGlsKCgpPT57IGlmKGFsbGllcy5pbmNsdWRlcyhvKSkgby5ocCA9IG8u'
        'bWF4SHA7CiAgICBpZihlbmVtaWVzLnNvbWUoZT0+ZS50eXBlPT09J2FzdGVyb2lkJykpIHJvY2tz'
        'Kys7CiAgICByZXR1cm4gISFvYmpDYXJkICYmIG9iakNhcmQudHh0PT09J1RIRSBPUklPTiBJUyBU'
        'SFJPVUdIJzsgfSwgOTAwMCwgdHJ1ZSk7CiAgci50aHJvdWdoQ2FyZCA9IHQ+PTA7CiAgci5ub0Fz'
        'dGVyb2lkcyA9IHJvY2tzPT09MDsKICBGUy51bnRpbCgoKT0+d2F2ZU92ZXIgfHwgd2F2ZT40NSwg'
        'MzAwMCwgdHJ1ZSk7CiAgci53YXZlRW5kcyA9IHdhdmVPdmVyIHx8IHdhdmU+NDU7CiAgcmV0dXJu'
        'IHI7YCk7CgpzY2VuYXJpbygnTTQ2IERpZSBXaXNzZW5zY2hhZnRsZXInLCAnbT00NicsIGAKICBj'
        'b25zdCByID0ge307CiAgc2NvcmUgPSAxMDAwOwogIEZTLnN0ZXAoNDAwKTsKICBjb25zdCBmID0g'
        'ZW5lbWllcy5maW5kKGU9PmUudWlkPT09J0YxJyk7CiAgci5mYXVzdHVzUGFya2VkID0gISFmICYm'
        'IE1hdGguYWJzKGYueS0yNTApIDwgMTsKICByLm9uQURlYWRsaW5lID0gISFmICYmIGYuZmxlZVQ+'
        'MDsKICAvLyBUaGUgY291bnRkb3duIHNpdHMgYXQgdGhlIHJpZ2h0IGVkZ2UsIGNsZWFyIG9mIHRo'
        'ZSBvYmplY3RpdmUgbGluZS4KICBjb25zdCBfZnQgPSBbXSwgX3BsID0gW107CiAgY29uc3QgX2Z4'
        'ID0gY3R4LmZpbGxUZXh0LCBfdHAgPSB0aFBsYXRlOwogIGN0eC5maWxsVGV4dCA9IGZ1bmN0aW9u'
        'KHQsIHgsIHkpeyBfZnQucHVzaCh7dDpTdHJpbmcodCksIHgsIHl9KTsgcmV0dXJuIF9meC5hcHBs'
        'eSh0aGlzLCBhcmd1bWVudHMpOyB9OwogIHRoUGxhdGUgPSBmdW5jdGlvbih4LCB5LCB3LCBoKXsg'
        'X3BsLnB1c2goe3gsIHksIHcsIGh9KTsgcmV0dXJuIF90cC5hcHBseSh0aGlzLCBhcmd1bWVudHMp'
        'OyB9OwogIHRyeSB7IGRyYXdPYmpMaW5lKHt0eHQ6bWlzc2lvbk9iaiwgY29sOicjZmZmJ30pOyBk'
        'cmF3RmxlZVdhcm5pbmcoKTsgfQogIGZpbmFsbHkgeyBjdHguZmlsbFRleHQgPSBfZng7IHRoUGxh'
        'dGUgPSBfdHA7IH0KICBjb25zdCBfZncgPSBfZnQuZmluZChvPT4vSlVNUElORyBPVVQgSU4vLnRl'
        'c3Qoby50KSk7CiAgci5jb3VudGRvd25OYW1lc1NoaXAgPSAhIV9mdyAmJiAvRkFVU1RVUy8udGVz'
        'dChfZncudCk7CiAgY29uc3QgX29sID0gX3BsWzBdLCBfY2QgPSBfcGxbX3BsLmxlbmd0aC0xXTsK'
        'ICByLmNvdW50ZG93bkNsZWFyT2ZPYmplY3RpdmUgPSAhIV9vbCAmJiAhIV9jZCAmJiBfcGwubGVu'
        'Z3RoPj0yICYmCiAgICAoX29sLngrX29sLncgPCBfY2QueCkgJiYgKF9jZC54K19jZC53IDw9IFcp'
        'OwogIGRhbWFnZUVuZW15KGYsIGYubWF4SHAqNSwgZi54LCBmLnksIHRydWUsICdib2x0Jyk7IEZT'
        'LnN0ZXAoMik7CiAgci5jYW5ub3RCZURlc3Ryb3llZCA9IGVuZW1pZXMuaW5jbHVkZXMoZik7CiAg'
        'Y29uc3Qga2lsbCA9IGlkPT57IGZvcihjb25zdCBzIG9mIGYuc3VicykgaWYocy5pZD09PWlkKXsg'
        'cy5kZWFkPXRydWU7IHMuaHA9MDsgfSB9OwogIGtpbGwoJ25hdmlnYXRpb24nKTsgRlMuc3RlcCgy'
        'KTsKICBjb25zdCBmdCA9IGYuZmxlZVQ7IEZTLnN0ZXAoMjAwKTsKICByLm5vTmF2aWdhdGlvbk5v'
        'SnVtcCA9IGYuZmxlZVQ9PT1mdDsKICByLm5vQXJnb1lldCA9ICFhbGxpZXMuc29tZShhPT5hLnVp'
        'ZD09PSdUMScpICYmICFzcGF3blEuc29tZShxPT5xLnVpZD09PSdUMScpOwogIGtpbGwoJ3dlYXBv'
        'bnMnKTsgRlMuc3RlcCgyKTsKICByLmNvdmVyVGhlQXJnbyA9IG1pc3Npb25PYmo9PT0nQ09WRVIg'
        'VEhFIEFSR08nOwogIGxldCBhcmdvID0gbnVsbDsKICBjb25zdCBhdCA9IEZTLnVudGlsKCgpPT57'
        'IGFyZ28gPSBhbGxpZXMuZmluZChhPT5hLnVpZD09PSdUMScpOyByZXR1cm4gISFhcmdvICYmIGFy'
        'Z28uaG9sZFQhPW51bGw7IH0sIDkwMDAsIHRydWUpOwogIC8vIEJvYXJkaW5nIHRha2VzIGl0cyB0'
        'aW1lOiBzaGUgc3RheXMgb24gdGhlIEZhdXN0dXMsIG5vdGhpbmcgaXMgdGFrZW4geWV0LgogIGNv'
        'bnN0IGF4ID0gYXJnbyAmJiBhcmdvLng7CiAgRlMuc3RlcCg0MDApOwogIHIuYm9hcmRpbmdIb2xk'
        'cyA9IGF0Pj0wICYmICFFVl9ET0NLWydUMSddICYmICFmLmNhcHR1cmVkICYmIE1hdGguYWJzKGFy'
        'Z28ueC1heCkgPCAxICYmIGVuZW1pZXMuaW5jbHVkZXMoZik7CiAgY29uc3QgZ290ID0gRlMudW50'
        'aWwoKCk9PiEhRVZfRE9DS1snVDEnXSwgOTAwMCwgdHJ1ZSk7CiAgRlMuc3RlcCg1KTsKICByLmRv'
        'Y2tzQW5kVGFrZXMgPSBnb3Q+PTAgJiYgZi5jYXB0dXJlZD09PXRydWU7CiAgLy8gQW5kIHRoZW4g'
        'Ym90aCBqdW1wIC0gdGhlIEFyZ28gZG9lcyBub3QgZmx5IG9uIHRvIHRoZSByaWdodC4KICByLmFy'
        'Z29KdW1wc091dCA9ICEhYXJnbyAmJiBhcmdvLndhcnBPdXQ+MCAmJiAhYXJnby5jcm9zc2luZzsK'
        'ICByLmNvbXBsZXRlQ2FyZCA9ICEhb2JqQ2FyZCAmJiBvYmpDYXJkLnR4dD09PSdGQVVTVFVTIENB'
        'UFRVUkVEJzsKICBGUy5zdGVwKDMwMCk7CiAgci5ub0ZhaWx1cmVBZnRlcndhcmRzID0gIWFsbGll'
        'cy5pbmNsdWRlcyhhcmdvKSAmJiAhKG9iakNhcmQgJiYgb2JqQ2FyZC50b25lPT09J2ZhaWwnKTsK'
        'ICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNDYgbGVmdCBhbG9uZSBzaGUganVtcHM6IGZhaWxl'
        'ZCcsICdtPTQ2JywgYAogIEZTLnN0ZXAoMzAwKTsKICBjb25zdCBmID0gZW5lbWllcy5maW5kKGU9'
        'PmUudWlkPT09J0YxJyk7CiAgZm9yKGNvbnN0IHMgb2YgZi5zdWJzKSBzLmhwID0gcy5tYXhIcCA9'
        'IDFlNzsKICBjb25zdCB0ID0gRlMudW50aWwoKCk9PiEhb2JqQ2FyZCAmJiBvYmpDYXJkLnRvbmU9'
        'PT0nZmFpbCcsIDkwMDAsIHRydWUpOwogIHJldHVybiB7ZmFpbENhcmQ6IHQ+PTAgJiYgb2JqQ2Fy'
        'ZC50eHQ9PT0nVEhFIEZBVVNUVVMgR09UIEFXQVknfTtgKTsKCnNjZW5hcmlvKCdNNDcgRGllIHp3'
        'ZWl0ZSBGbHVjaHQnLCAnbT00NycsIGAKICBjb25zdCByID0ge307CiAgc2NvcmUgPSA1MDAwOwog'
        'IEZTLnN0ZXAoNDAwKTsKICByLmljZW5pID0gZW5lbWllcy5zb21lKGU9PmUudWlkPT09J1YxJyAm'
        'JiBlLmljZW5pKTsKICByLmhlY2F0ZSA9IGVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdWMicgJiYg'
        'ZS5pbWc9PT0nbnRmZGVoZWNhdGUnKTsKICByLm5vQWxsaWVzID0gIWFsbGllcy5zb21lKGE9PiFh'
        'LnNtYWxsKTsKICByLm5vQWVvbHVzID0gIWVuZW1pZXMuc29tZShlPT5lLnVpZD09PSdLMScpOwog'
        'IGNvbnN0IF92MSA9IGVuZW1pZXMuZmluZChlPT5lLnVpZD09PSdWMScpLCBfdjIgPSBlbmVtaWVz'
        'LmZpbmQoZT0+ZS51aWQ9PT0nVjInKTsKICBjb25zdCBfeTEgPSBfdjEgJiYgX3YxLnksIF95MiA9'
        'IF92MiAmJiBfdjIueTsKICBGUy5zdGVwKDMwMCk7CiAgci5zaGlwc0hvbGRIZWlnaHQgPSAhIV92'
        'MSAmJiAhIV92MiAmJiBNYXRoLmFicyhfdjEueS1feTEpPDAuNSAmJiBNYXRoLmFicyhfdjIueS1f'
        'eTIpPDAuNSAmJgogICAgTWF0aC5hYnMoX3YxLnktMTUwKTwxICYmIE1hdGguYWJzKF92Mi55LTM1'
        'MCk8MTsKICByLmljZW5pRm9ydHlTZWNvbmRzID0gISFfdjEgJiYgX3YxLmZsZWVUPjAgJiYgX3Yx'
        'LmZsZWVUIDw9IDQwKlRJQ0tfSFo7CiAgci5ub0VuZGxlc3NSZWluZm9yY2VtZW50ID0gIWV2UmVp'
        'bmY7CiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT4hZW5lbWllcy5zb21lKGU9PmUudWlkPT09J1Yx'
        'JyksIDkwMDAsIHRydWUpOwogIHIuaWNlbmlHZXRzQXdheSA9IHQ+PTAgJiYgaWNlbkVzY2FwZXM9'
        'PT0xICYmIHNjb3JlPj01MDAwOwogIGNvbnN0IHYgPSBlbmVtaWVzLmZpbmQoZT0+ZS51aWQ9PT0n'
        'VjInKTsgaWYodikgdi5ocCA9IDA7CiAgci5jb21wbGV0ZUNhcmQgPSBGUy51bnRpbCgoKT0+ISFv'
        'YmpDYXJkICYmIG9iakNhcmQudHh0PT09J0hFQ0FURSBERVNUUk9ZRUQnLCAzMDAwLCBmYWxzZSkg'
        'Pj0gMDsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdNNDggRGllIEF1ZmtsYWVydW5nJywgJ209'
        'NDgnLCBgCiAgY29uc3QgciA9IHt9OwogIHNjb3JlID0gMjAwMDsKICByLmFubm91bmNlZCA9IE5P'
        'VElDRVMuc29tZShuPT5uLnR4dD09PSdHVEYgUEVHQVNVUyBBU1NJR05FRCcpOwogIEZTLnN0ZXAo'
        'NDAwKTsKICByLmZseWluZ0FQZWdhc3VzID0gcGxheWVyLnNoaXA9PT0nZmlwZWdhc3VzJzsKICBy'
        'Lm5vdGhpbmdMb2Nrc0hlciA9ICFjYW5Mb2NrT24ocGxheWVyKTsKICBjb25zdCB2ID0gZW5lbWll'
        'cy5maW5kKGU9PmUudWlkPT09J1YxJyk7CiAgci5ndW5zSG9sZEZpcmUgPSBjYXBHdW5UYXJnZXQo'
        'dik9PT1udWxsOwogIHIubm9CZWFtT25IZXIgPSAhYmVhbVRhcmdldHModiwgZmFsc2UpLmluY2x1'
        'ZGVzKHBsYXllcik7CiAgci5ub0hhbmdhciA9IHNoaXBTd2FwUmVhZHkoKT09PWZhbHNlOwogIHIu'
        'cmluZ3NTaG93biA9ICEhdiAmJiB2LnNjYW5TdWJzPT09dHJ1ZSAmJiB2LnN1YnMuZXZlcnkocz0+'
        'IXMuc2Nhbm5lZCk7CiAgZm9yKGNvbnN0IHMgb2Ygdi5zdWJzKXsgY29uc3QgcCA9IHN1YlBvcyh2'
        'LCBzKTsgRlMuaG9sZChwLngsIHAueSwgU1VCX1NDQU5fVElNRSArIDIwKTsgfQogIHIuYWxsRml2'
        'ZVNjYW5uZWQgPSB2LnN1YnMuZXZlcnkocz0+cy5zY2FubmVkKSAmJiB2LnNjYW5uZWQ9PT10cnVl'
        'OwogIEZTLnN0ZXAoMyk7CiAgci5jb21wbGV0ZUNhcmQgPSAhIW9iakNhcmQgJiYgb2JqQ2FyZC50'
        'eHQ9PT0nT1JJT04gU0NBTk5FRCc7CiAgY29uc3QgdCA9IEZTLnVudGlsKCgpPT4hZW5lbWllcy5p'
        'bmNsdWRlcyh2KSwgMTUwMCwgZmFsc2UpOwogIHIub3Jpb25MZWF2ZXNXaXRob3V0UGVuYWx0eSA9'
        'IHQ+PTAgJiYgc2NvcmUgPj0gMjAwMDsKICBGUy51bnRpbCgoKT0+d2F2ZT40OCwgMzAwMDAsIHRy'
        'dWUpOwogIHIub3duSHVsbEJhY2tOZXh0V2F2ZSA9IHdhdmU9PT00OSAmJiBwbGF5ZXIuc2hpcD09'
        'PSdmaW15cm1pZG9uJzsKICByZXR1cm4gcjtgKTsKCnNjZW5hcmlvKCdDb2xvc3N1cyBiZWFtcyBh'
        'cmUgVGVycmFuJywgJycsIGAKICByZXR1cm4ge21haW46IGJlYW1Db2woJ2d0dmEnLCB0cnVlKT09'
        'PScjMDBmZjU1JywgYW50aUZpZ2h0ZXI6IGJlYW1Db2woJ2d0dmEnLCBmYWxzZSk9PT0nIzQ0OTlm'
        'Zid9O2AsIHRydWUpOwoKc2NlbmFyaW8oJ0hvTCBzdGFydCB1bmNoYW5nZWQnLCAnbT0xJywgYAog'
        'IHJldHVybiB7d2F2ZTogd2F2ZSwgdGhvdGg6IHBsYXllci5zaGlwPT09J2ZpdG90aCcsIHZhc3Vk'
        'YW5DYWxsOiBBTExZX0ZBQ19PTi52YXN1ZGFuPT09dHJ1ZSAmJiBBTExZX0ZBQ19PTi50ZXJyYW49'
        'PT1mYWxzZX07YCk7CgovLyDilIDilIAgUnVubmVyIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgAooYXN5bmMoKT0+ewog'
        'IGNvbnN0IGJyb3dzZXIgPSBhd2FpdCBjaHJvbWl1bS5sYXVuY2goKTsKICBsZXQgZmFpbHMgPSAw'
        'OwogIGNvbnN0IG9ubHkgPSBwcm9jZXNzLmFyZ3ZbNF07CiAgZm9yKGNvbnN0IHNjIG9mIHNjZW5h'
        'cmlvcyl7CiAgICBpZihvbmx5ICYmIHNjLm5hbWUuaW5kZXhPZihvbmx5KTwwKSBjb250aW51ZTsK'
        'ICAgIGNvbnN0IHBhZ2UgPSBhd2FpdCBicm93c2VyLm5ld1BhZ2UoKTsKICAgIGNvbnN0IGVycnMg'
        'PSBbXTsKICAgIHBhZ2Uub24oJ3BhZ2VlcnJvcicsIGU9PmVycnMucHVzaChTdHJpbmcoZS5tZXNz'
        'YWdlfHxlKSkpOwogICAgYXdhaXQgcGFnZS5nb3RvKCdmaWxlOi8vJyArIHRtcCArICc/JyArIHNj'
        'LnF1ZXJ5KTsKICAgIGF3YWl0IHBhZ2Uud2FpdEZvclRpbWVvdXQoMzAwKTsKICAgIGxldCByZXM7'
        'CiAgICB0cnl7CiAgICAgIHJlcyA9IGF3YWl0IHBhZ2UuZXZhbHVhdGUoSEVMUEVSUyArIGBcbkZT'
        'LmZha2VJbWFnZXMoKTtgICsgKHNjLm5vTGF1bmNoID8gJycgOiAnIGxhdW5jaEdhbWUoKTsnKSAr'
        'IGBcbihmdW5jdGlvbigpeyR7c2MuYm9keX19KSgpYCk7CiAgICB9Y2F0Y2goZSl7IHJlcyA9IG51'
        'bGw7IGVycnMucHVzaChTdHJpbmcoZS5tZXNzYWdlfHxlKSk7IH0KICAgIGNvbnNvbGUubG9nKHNj'
        'Lm5hbWUgKyAnICAoPycgKyBzYy5xdWVyeSArICcpJyk7CiAgICBpZihyZXMpIGZvcihjb25zdCBb'
        'ayx2XSBvZiBPYmplY3QuZW50cmllcyhyZXMpKXsKICAgICAgY29uc3QgZ29vZCA9ICh0eXBlb2Yg'
        'dj09PSdib29sZWFuJykgPyB2IDogdHJ1ZTsKICAgICAgaWYoIWdvb2QpIGZhaWxzKys7CiAgICAg'
        'IGNvbnNvbGUubG9nKChnb29kID8gJyAgb2sgICAgJyA6ICcgIEZBSUwgICcpICsgayArICh0eXBl'
        'b2Ygdj09PSdib29sZWFuJyA/ICcnIDogJyA9ICcgKyBKU09OLnN0cmluZ2lmeSh2KSkpOwogICAg'
        'fQogICAgaWYoZXJycy5sZW5ndGgpeyBmYWlscysrOyBjb25zb2xlLmxvZygnICBGQUlMICBwYWdl'
        'IGVycm9yczpcbiAgICAnICsgZXJycy5zbGljZSgwLDQpLmpvaW4oJ1xuICAgICcpKTsgfQogICAg'
        'YXdhaXQgcGFnZS5jbG9zZSgpOwogIH0KICBhd2FpdCBicm93c2VyLmNsb3NlKCk7CiAgZnMudW5s'
        'aW5rU3luYyh0bXApOwogIGNvbnNvbGUubG9nKCdcbicgKyAoZmFpbHMgPyBmYWlscyArICcgRkFJ'
        'TEVEJyA6ICdhbGwgcGFzc2VkJykpOwogIHByb2Nlc3MuZXhpdChmYWlscyA/IDEgOiAwKTsKfSko'
        'KTsK'
    ),
    'docksim.js': (
        'Ly8gRG9ja2luZyBzaW11bGF0aW9uLiBQdWxscyB0aGUgUkVBTCBmdW5jdGlvbnMgb3V0IG9mIHRo'
        'ZSBsb2dpYyBmaWxlIGFuZAovLyBydW5zIHRoZW0gYWdhaW5zdCBhIG1pbmltYWwgd29ybGQuIE9u'
        'bHkgdGhlIHNoaXAgb2JqZWN0cywgdGhlIGRlYXRoIG9mIGFuCi8vIGFsbHkgYW5kIHRoZSB0aWNr'
        'IG9yZGVyIGFyZSBzdGFuZC1pbnM7IGV2ZXJ5IGRvY2tpbmcgcnVsZSBpcyB0aGUgZ2FtZSdzLgov'
        'LyBVc2FnZTogbm9kZSBkb2Nrc2ltLmpzIGhscF9zaG9vdGVyX3YxMDJfbG9naWMuaHRtbCBobHBf'
        'bW91bnRzX2ZpbmFsLmpzb24KY29uc3QgZnMgPSByZXF1aXJlKCdmcycpOwpjb25zdCBodG1sID0g'
        'ZnMucmVhZEZpbGVTeW5jKHByb2Nlc3MuYXJndlsyXSB8fCAnaGxwX3Nob290ZXJfdjEwMl9sb2dp'
        'Yy5odG1sJywgJ3V0ZjgnKTsKY29uc3Qgc3JjID0gaHRtbC5tYXRjaCgvPHNjcmlwdFtePl0qPihb'
        'XHNcU10qKTxcL3NjcmlwdD4vKVsxXTsKY29uc3QgTU9VTlRTID0gSlNPTi5wYXJzZShmcy5yZWFk'
        'RmlsZVN5bmMocHJvY2Vzcy5hcmd2WzNdIHx8ICdobHBfbW91bnRzX2ZpbmFsLmpzb24nLCAndXRm'
        'OCcpKTsKCi8vIEJyYWNlIG1hdGNoaW5nIHRoYXQgc2tpcHMgc3RyaW5ncyBhbmQgY29tbWVudHMu'
        'CmZ1bmN0aW9uIGJsb2NrKGZyb20pewogIGxldCBpID0gc3JjLmluZGV4T2YoJ3snLCBmcm9tKSwg'
        'ZCA9IDA7CiAgZm9yKDsgaSA8IHNyYy5sZW5ndGg7IGkrKyl7CiAgICBjb25zdCBjaCA9IHNyY1tp'
        'XSwgbnggPSBzcmNbaSsxXTsKICAgIGlmKGNoID09PSAnLycgJiYgbnggPT09ICcvJyl7IGkgPSBz'
        'cmMuaW5kZXhPZignXG4nLCBpKTsgY29udGludWU7IH0KICAgIGlmKGNoID09PSAnLycgJiYgbngg'
        'PT09ICcqJyl7IGkgPSBzcmMuaW5kZXhPZignKi8nLCBpKSArIDE7IGNvbnRpbnVlOyB9CiAgICBp'
        'ZihjaCA9PT0gJyInIHx8IGNoID09PSAiJyIgfHwgY2ggPT09ICdgJyl7CiAgICAgIGNvbnN0IHEg'
        'PSBjaDsgaSsrOwogICAgICB3aGlsZShzcmNbaV0gIT09IHEpeyBpZihzcmNbaV0gPT09ICdcXCcp'
        'IGkrKzsgaSsrOyB9CiAgICAgIGNvbnRpbnVlOwogICAgfQogICAgaWYoY2ggPT09ICd7JykgZCsr'
        'OwogICAgZWxzZSBpZihjaCA9PT0gJ30nKXsgZC0tOyBpZihkID09PSAwKSByZXR1cm4gaSArIDE7'
        'IH0KICB9CiAgdGhyb3cgbmV3IEVycm9yKCd1bmJhbGFuY2VkIGF0ICcgKyBmcm9tKTsKfQpmdW5j'
        'dGlvbiBmbihuYW1lKXsKICBjb25zdCBhdCA9IHNyYy5pbmRleE9mKCdmdW5jdGlvbiAnICsgbmFt'
        'ZSArICcoJyk7CiAgaWYoYXQgPCAwKSB0aHJvdyBuZXcgRXJyb3IoJ21pc3NpbmcgZnVuY3Rpb24g'
        'JyArIG5hbWUpOwogIHJldHVybiBzcmMuc2xpY2UoYXQsIGJsb2NrKGF0KSk7Cn0KZnVuY3Rpb24g'
        'Y29uc3RPYmoobmFtZSl7CiAgY29uc3QgYXQgPSBzcmMuaW5kZXhPZignY29uc3QgJyArIG5hbWUg'
        'KyAnID0nKTsKICByZXR1cm4gc3JjLnNsaWNlKGF0LCBibG9jayhhdCkpICsgJzsnOwp9Cgpjb25z'
        'dCBOQU1FUyA9IFsnZG9ja1BvaW50JywnZG9ja09mZnNldCcsJ3VuaXRBbGl2ZScsJ2lkUGVuZGlu'
        'ZycsJ2NhcmdvTG9zdCcsJ2NsYWltQ2FyZ28nLAogICdsZWF2ZUVtcHR5JywnY2FyZ29TdGlsbFdh'
        'bnRlZCcsJ2NhcnJ5Q2FyZ28nLCdkcm9wQ2FyZ28nLCd0aWNrQ2FycnknLCd0aWNrRG9ja2luZycs'
        'CiAgJ3RpY2tDcm9zc0d1YXJkcycsJ2tpbGxFbmVteScsJ2J5SWQnLCdldlNlZW4nLCdtb3VudHNG'
        'b3InLCdodWxsQ2xhc3MnLAogICdsaXZlVGhyZWF0Q291bnQnLCdzY3JpcHRVbml0c1Jlc29sdmVk'
        'J107Cgpjb25zdCB3b3JsZCA9IGAKbGV0IGVuZW1pZXM9W10sIGFsbGllcz1bXSwgU1VCX01TR1M9'
        'W10sIEVWX0RPQ0s9e30sIEVWX1NFRU49e30sIEVWX0hFTEQ9e30sIEVWX0xFRlQ9e30sIHNwYXdu'
        'UT1bXTsKbGV0IHByb3RTYXZlZD0wLCBwcm90TG9zdD0wLCBndWFyZExvc3Q9ZmFsc2UsIGd1YXJk'
        'R29uZT1mYWxzZSwgY3Jvc3NEb25lPTAsIGNyb3NzVG90YWw9MDsKbGV0IHNjb3JlPTAsIGJvc3NB'
        'bGl2ZT1mYWxzZSwgYm9zc1NsYWluPWZhbHNlLCBleHBsPTA7CmNvbnN0IFc9ODAwLCBIPTUwMCwg'
        'SFVEX0g9NDQsIERPQ0tfU1BEPTAuNTUsIERPQ0tfTkVBUj0yMjsKY29uc3QgTU9VTlRTID0gJHtK'
        'U09OLnN0cmluZ2lmeShNT1VOVFMpfTsKY29uc3QgSU1HUyA9IHsgZnJiYXN0Ont3aWR0aDo2MCxo'
        'ZWlnaHQ6MjZ9LCBmY3ZjMzp7d2lkdGg6MzAsaGVpZ2h0OjIyfSwKICB0cmlzaXM6e3dpZHRoOjYw'
        'LGhlaWdodDoyNH0sIGRlaGF0c2hlcHN1dDp7d2lkdGg6MzkxLGhlaWdodDoxNTB9IH07CmZ1bmN0'
        'aW9uIHN0YXRLaWxsKCl7fSBmdW5jdGlvbiBtYXliZURyb3BUaWNrZXQoKXt9Ci8vIFRoZSBwcmFj'
        'dGljZSBsb2cgaXMgbm90IHdoYXQgaXMgdGVzdGVkIGhlcmUuCmZ1bmN0aW9uIHBsb2dLaWxsKCl7'
        'fSBmdW5jdGlvbiBwbG9nUmVhcm0oKXt9IGZ1bmN0aW9uIHBsb2dTZWMoKXt9IGZ1bmN0aW9uIHBs'
        'b2dIaXQoKXt9IGZ1bmN0aW9uIHBsb2dQaWNrKCl7fSBmdW5jdGlvbiBwbG9nU3JjKCl7fSBmdW5j'
        'dGlvbiBwbG9nTG9zcygpe30gZnVuY3Rpb24gcGxvZ0V2ZW50KCl7fSBmdW5jdGlvbiBwbG9nTmFt'
        'ZSgpeyByZXR1cm4gJyc7IH0gZnVuY3Rpb24gcGxvZ0FsbHlMb3N0KCl7fSBmdW5jdGlvbiBwbG9n'
        'RGVhdGgoKXt9IGZ1bmN0aW9uIHBsb2dTeW5jKCl7fQpmdW5jdGlvbiB0cmlnZ2VyRXhwbCgpeyBl'
        'eHBsKys7IH0KJHtOQU1FUy5tYXAoZm4pLmpvaW4oJ1xuJyl9CiR7Y29uc3RPYmooJ1NDUklQVF9X'
        'QVZFUycpfQpgOwpjb25zdCBUSUNLX0haID0gMTAwOwpjb25zdCBhcGkgPSBuZXcgRnVuY3Rpb24o'
        'J1RJQ0tfSFonLCB3b3JsZCArIGAKcmV0dXJuIHsgZ2V0IGVuZW1pZXMoKXtyZXR1cm4gZW5lbWll'
        'czt9LCBzZXQgZW5lbWllcyh2KXtlbmVtaWVzPXY7fSwKICBnZXQgYWxsaWVzKCl7cmV0dXJuIGFs'
        'bGllczt9LCBzZXQgYWxsaWVzKHYpe2FsbGllcz12O30sCiAgZ2V0IHByb3RTYXZlZCgpe3JldHVy'
        'biBwcm90U2F2ZWQ7fSwgZ2V0IHByb3RMb3N0KCl7cmV0dXJuIHByb3RMb3N0O30sCiAgZ2V0IGV4'
        'cGwoKXtyZXR1cm4gZXhwbDt9LCBTVUJfTVNHUywgRVZfU0VFTiwgRVZfSEVMRCwgc3Bhd25RLAog'
        'IHJlc2V0KCl7IGVuZW1pZXM9W107IGFsbGllcz1bXTsgU1VCX01TR1MubGVuZ3RoPTA7IGZvcihj'
        'b25zdCBrIGluIEVWX0RPQ0spIGRlbGV0ZSBFVl9ET0NLW2tdOwogICAgZm9yKGNvbnN0IGsgaW4g'
        'RVZfU0VFTikgZGVsZXRlIEVWX1NFRU5ba107IGZvcihjb25zdCBrIGluIEVWX0hFTEQpIGRlbGV0'
        'ZSBFVl9IRUxEW2tdOwogICAgc3Bhd25RLmxlbmd0aD0wOyBwcm90U2F2ZWQ9MDsgcHJvdExvc3Q9'
        'MDsgZ3VhcmRMb3N0PWZhbHNlOyBleHBsPTA7IH0sCiAgdGlja0RvY2tpbmcsIHRpY2tDcm9zc0d1'
        'YXJkcywgdGlja0NhcnJ5LCBraWxsRW5lbXksIGRvY2tQb2ludCwgbGl2ZVRocmVhdENvdW50LAog'
        'IHNjcmlwdFVuaXRzUmVzb2x2ZWQsIFNDUklQVF9XQVZFUyB9O2ApKFRJQ0tfSFopOwoKLy8g4pSA'
        '4pSAIFN0YW5kLWlucyDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKbGV0IHVpZGMg'
        'PSAwOwpmdW5jdGlvbiBmcmVpZ2h0ZXIodWlkLCB4LCB5LCBkb2NrVG8sIHNpZGUpewogIGNvbnN0'
        'IG8gPSB7dWlkLCB0eXBlOidmcmVpZ2h0ZXInLCBpbWc6J2ZyYmFzdCcsIHgsIHksIHNjOjEsIGZs'
        'aXA6ZmFsc2UsIHdhcnA6MCwgZGVhZDpmYWxzZSwKICAgIGd1YXJkOnRydWUsIGRvY2tUbywgY3Jv'
        'c3NBZnRlcjowLjM4LCBocDoxMDAsIG1heEhwOjEwMCwgX246Kyt1aWRjfTsKICBhcGkuRVZfU0VF'
        'Tlt1aWRdID0gdHJ1ZTsKICAoc2lkZSA9PT0gJ2VuZW15JyA/IGFwaS5lbmVtaWVzIDogYXBpLmFs'
        'bGllcykucHVzaChvKTsgcmV0dXJuIG87Cn0KZnVuY3Rpb24gY29udGFpbmVyKHVpZCwgeCwgeSwg'
        'c2lkZSl7CiAgY29uc3QgbyA9IHt1aWQsIHR5cGU6J2NvbnRhaW5lcicsIGltZzonZmN2YzMnLCB4'
        'LCB5LCBzYzoxLCBmbGlwOnNpZGU9PT0nZW5lbXknLCB3YXJwOjAsCiAgICBkZWFkOmZhbHNlLCBn'
        'dWFyZDpzaWRlIT09J2VuZW15JywgcGlja3VwOnRydWUsIGhwOjYwLCBtYXhIcDo2MCwgcHRzOjQw'
        'LCBfbjorK3VpZGN9OwogIGFwaS5FVl9TRUVOW3VpZF0gPSB0cnVlOwogIChzaWRlID09PSAnZW5l'
        'bXknID8gYXBpLmVuZW1pZXMgOiBhcGkuYWxsaWVzKS5wdXNoKG8pOyByZXR1cm4gbzsKfQovLyBN'
        'aXJyb3JzIHRoZSBkZWF0aCBicmFuY2ggb2YgdXBkYXRlQWxsaWVzKCk6IHNwbGljZSwgYW5kIGNv'
        'dW50IGEgZ3VhcmQuCmZ1bmN0aW9uIGFsbHlEaWVzKGEpewogIGEuZGVhZCA9IHRydWU7IGEuaHAg'
        'PSAwOwogIGNvbnN0IGkgPSBhcGkuYWxsaWVzLmluZGV4T2YoYSk7IGlmKGkgPj0gMCkgYXBpLmFs'
        'bGllcy5zcGxpY2UoaSwgMSk7CiAgaWYoYS5ndWFyZCl7IC8qIHVwZGF0ZUFsbGllczogcHJvdExv'
        'c3QrKyAqLyBhcGkuX2xvc3RCeUd1YXJkID0gKGFwaS5fbG9zdEJ5R3VhcmR8fDApICsgMTsgfQp9'
        'Ci8vIHRpY2sgb3JkZXIgYXMgaW4gdXBkYXRlKCk6IGRvY2tpbmcgLi4uIGNyb3NzaW5nIC4uLiBt'
        'b3ZlbWVudCwgdGhlbiBjYXJyeQpsZXQgc2hhcmVkID0gMCwgbGFnID0gMDsKZnVuY3Rpb24gc3Rl'
        'cCgpewogIGFwaS50aWNrRG9ja2luZygpOwogIGFwaS50aWNrQ3Jvc3NHdWFyZHMoKTsKICBhcGku'
        'dGlja0NhcnJ5KCk7CiAgLy8gbm8gdHdvIGZyZWlnaHRlcnMgb24gb25lIGNvbnRhaW5lciwgZXZl'
        'cgogIGNvbnN0IHNlZW4gPSBuZXcgTWFwKCk7CiAgZm9yKGNvbnN0IGYgb2YgYXBpLmVuZW1pZXMu'
        'Y29uY2F0KGFwaS5hbGxpZXMpKXsKICAgIGNvbnN0IGMgPSBmLmRvY2tlZFRvIHx8IGYuZG9ja1Jl'
        'czsKICAgIGlmKCFjKSBjb250aW51ZTsKICAgIGlmKHNlZW4uaGFzKGMpKSBzaGFyZWQrKzsKICAg'
        'IHNlZW4uc2V0KGMsIGYpOwogIH0KICAvLyBjYXJyaWVkIGNhcmdvOiBib3RoIGRvY2sgcG9pbnRz'
        'IG1lZXQsIHdpdGggbm8gbGFnIGFmdGVyIG1vdmluZwogIGZvcihjb25zdCBmIG9mIGFwaS5hbGxp'
        'ZXMpIGlmKGYuZG9ja2VkVG8gJiYgIWYuZG9ja2VkVG8uZGVhZCl7CiAgICBjb25zdCBhID0gYXBp'
        'LmRvY2tQb2ludChmKSwgYiA9IGFwaS5kb2NrUG9pbnQoZi5kb2NrZWRUbyk7CiAgICBsYWcgPSBN'
        'YXRoLm1heChsYWcsIE1hdGguaHlwb3QoYS54LWIueCwgYS55LWIueSkpOwogIH0KfQpmdW5jdGlv'
        'biBydW4obiwgaG9vayl7IGZvcihsZXQgdCA9IDA7IHQgPCBuOyB0KyspeyBpZihob29rKSBob29r'
        'KHQpOyBzdGVwKCk7IH0gfQpjb25zdCBsb3N0ID0gKCkgPT4gYXBpLnByb3RMb3N0ICsgKGFwaS5f'
        'bG9zdEJ5R3VhcmR8fDApOwpsZXQgcGFzcyA9IDAsIGZhaWwgPSAwOwpmdW5jdGlvbiBjaGVjayhu'
        'YW1lLCBvaywgaW5mbyl7CiAgY29uc29sZS5sb2coKG9rID8gJyAgb2sgICAgJyA6ICcgIEZBSUwg'
        'ICcpICsgbmFtZSArIChpbmZvID8gJyAgICgnICsgaW5mbyArICcpJyA6ICcnKSk7CiAgb2sgPyBw'
        'YXNzKysgOiBmYWlsKys7Cn0KZnVuY3Rpb24gYmVnaW4odGl0bGUpeyBhcGkucmVzZXQoKTsgYXBp'
        'Ll9sb3N0QnlHdWFyZCA9IDA7IHNoYXJlZCA9IDA7IGxhZyA9IDA7IGNvbnNvbGUubG9nKCdcbicg'
        'KyB0aXRsZSk7IH0KY29uc3QgbXNncyA9IHQgPT4gYXBpLlNVQl9NU0dTLmZpbHRlcihtID0+IG0u'
        'dHh0ID09PSB0KS5sZW5ndGg7CgovLyDilIDilIAgMS4gRXF1YWwgbnVtYmVycyDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIAKYmVnaW4oJzEgIHR3byBmcmVpZ2h0ZXJzLCB0d28gY29udGFpbmVycycpOwpjb250YWluZXIo'
        'J0MxJywgMTUwLCAxODApOyBjb250YWluZXIoJ0MxJywgMTcwLCAzMjApOwpmcmVpZ2h0ZXIoJ0Yx'
        'JywgLTQwLCAyMDAsICdDMScpOyBmcmVpZ2h0ZXIoJ0YxJywgLTQwLCAzMDAsICdDMScpOwpydW4o'
        'NjAwMCk7CmNoZWNrKCdib3RoIGRlbGl2ZXJlZCcsIGFwaS5wcm90U2F2ZWQgPT09IDIgJiYgbXNn'
        'cygnREVMSVZFUkVEJykgPT09IDIsICdzYXZlZCAnICsgYXBpLnByb3RTYXZlZCk7CmNoZWNrKCdu'
        'b3RoaW5nIGxvc3QnLCBsb3N0KCkgPT09IDApOwpjaGVjaygnbmV2ZXIgdHdvIG9uIG9uZSBjb250'
        'YWluZXInLCBzaGFyZWQgPT09IDApOwpjaGVjaygnY2FyZ28gc2l0cyBleGFjdGx5IG9uIHRoZSBk'
        'b2NrIHBvaW50JywgbGFnIDwgMC4wMSwgJ21heCBnYXAgJyArIGxhZy50b0ZpeGVkKDQpICsgJyBw'
        'eCcpOwoKLy8g4pSA4pSAIDIuIE1vcmUgZnJlaWdodGVycyB0aGFuIGNvbnRhaW5lcnMg4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSACmJlZ2luKCcyICB0aHJlZSBmcmVpZ2h0ZXJzLCB0d28gY29udGFpbmVycycpOwpj'
        'b250YWluZXIoJ0MxJywgMTUwLCAxODApOyBjb250YWluZXIoJ0MxJywgMTcwLCAzMjApOwpmcmVp'
        'Z2h0ZXIoJ0YxJywgLTQwLCAyMDAsICdDMScpOyBmcmVpZ2h0ZXIoJ0YxJywgLTYwLCAyNTAsICdD'
        'MScpOyBmcmVpZ2h0ZXIoJ0YxJywgLTgwLCAzMDAsICdDMScpOwpydW4oNjAwMCk7CmNoZWNrKCd0'
        'd28gZGVsaXZlcmVkLCBvbmUgbGVmdCBlbXB0eScsIGFwaS5wcm90U2F2ZWQgPT09IDIgJiYgbXNn'
        'cygnTEVGVCBFTVBUWScpID09PSAxLAogICAgICAnc2F2ZWQgJyArIGFwaS5wcm90U2F2ZWQgKyAn'
        'LCBlbXB0eSAnICsgbXNncygnTEVGVCBFTVBUWScpKTsKY2hlY2soJ25ldmVyIHR3byBvbiBvbmUg'
        'Y29udGFpbmVyJywgc2hhcmVkID09PSAwKTsKY2hlY2soJ3dhdmUgbm90IGhlbGQgKG5vIGZyZWln'
        'aHRlciBsZWZ0KScsIGFwaS5hbGxpZXMubGVuZ3RoID09PSAwLCBhcGkuYWxsaWVzLmxlbmd0aCAr'
        'ICcgbGVmdCcpOwoKLy8g4pSA4pSAIDMuIE1vcmUgY29udGFpbmVycyB0aGFuIGZyZWlnaHRlcnMg'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSACmJlZ2luKCczICB0d28gZnJlaWdodGVycywgdGhyZWUgY29udGFpbmVy'
        'cyAocmF3LCB3aXRob3V0IHRoZSBjb3VudCBmaXgpJyk7CmNvbnRhaW5lcignQzEnLCAxNTAsIDE1'
        'MCk7IGNvbnRhaW5lcignQzEnLCAxNzAsIDI1MCk7IGNvbnRhaW5lcignQzEnLCAxOTAsIDM1MCk7'
        'CmZyZWlnaHRlcignRjEnLCAtNDAsIDIwMCwgJ0MxJyk7IGZyZWlnaHRlcignRjEnLCAtNDAsIDMw'
        'MCwgJ0MxJyk7CnJ1big2MDAwKTsKY2hlY2soJ3R3byBkZWxpdmVyZWQnLCBhcGkucHJvdFNhdmVk'
        'ID09PSAyKTsKY2hlY2soJ3RoaXJkIG9uZSBsZWZ0IGJlaGluZCBhbmQgY291bnRlZCBvbmNlJywg'
        'bXNncygnQ0FSR08gTEVGVCBCRUhJTkQnKSA9PT0gMSAmJiBsb3N0KCkgPT09IDEpOwpjaGVjaygn'
        'bGVmdC1iZWhpbmQgY29udGFpbmVyIGlzIHNjZW5lcnksIG5vIGxvbmdlciBhIGd1YXJkJywKICAg'
        'ICAgYXBpLmFsbGllcy5ldmVyeShjID0+IGMuc2NlbmVyeSAmJiAhYy5ndWFyZCkpOwpjaGVjaygn'
        'cmVzdWx0IHdvdWxkIHJlYWQgUEFSVElBTCAyLzMnLCBhcGkucHJvdFNhdmVkID09PSAyICYmIGxv'
        'c3QoKSA9PT0gMSk7CgovLyDilIDilIAgNC4gQ2FycmllciBkaWVzIHdpdGggY2FyZ28g4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSACmJlZ2luKCc0ICBjYXJyaWVyIGRlc3Ry'
        'b3llZCB3aGlsZSBjYXJyeWluZycpOwpjb25zdCBjNCA9IGNvbnRhaW5lcignQzEnLCAxNTAsIDIw'
        'MCk7IGNvbnN0IGY0ID0gZnJlaWdodGVyKCdGMScsIC00MCwgMjUwLCAnQzEnKTsKcnVuKDYwMDAs'
        'IHQgPT4geyBpZihmNC5kb2NrZWRUbyAmJiBmNC54ID4gNDAwICYmICFmNC5kZWFkKSBhbGx5RGll'
        'cyhmNCk7IH0pOwpjaGVjaygnY2FyZ28gZGVzdHJveWVkIHdpdGggaXQnLCBjNC5kZWFkICYmIGFw'
        'aS5hbGxpZXMuaW5kZXhPZihjNCkgPCAwICYmIGFwaS5leHBsID09PSAxKTsKY2hlY2soJ2NvdW50'
        'ZWQgb25jZSAodGhlIGZyZWlnaHRlciksIG5vdCB0d2ljZScsIGxvc3QoKSA9PT0gMSwgJ2xvc3Qg'
        'JyArIGxvc3QoKSk7CmNoZWNrKCdub3QgcmVwb3J0ZWQgYXMgbGVmdCBiZWhpbmQnLCBtc2dzKCdD'
        'QVJHTyBMRUZUIEJFSElORCcpID09PSAwKTsKCi8vIOKUgOKUgCA1LiBDYXJnbyBkaWVzIGJlZm9y'
        'ZSBkb2NraW5nIChhbGxpZWQgY29udGFpbmVyKSDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIAKYmVnaW4oJzUgIGFsbGllZCBjb250YWluZXIgZGVzdHJveWVkIGJlZm9yZSBkb2NraW5n'
        'Jyk7CmNvbnN0IGM1ID0gY29udGFpbmVyKCdDMScsIDMwMCwgMTgwKTsgY29udGFpbmVyKCdDMScs'
        'IDMyMCwgMzIwKTsKY29uc3QgZjUgPSBmcmVpZ2h0ZXIoJ0YxJywgLTQwLCAyMDAsICdDMScpOyBm'
        'cmVpZ2h0ZXIoJ0YxJywgLTQwLCAzMDAsICdDMScpOwpydW4oNjAwMCwgdCA9PiB7IGlmKHQgPT09'
        'IDEwMCkgYWxseURpZXMoZjUuZG9ja1Jlcyk7IH0pOwpjaGVjaygnaXRzIGZyZWlnaHRlciBsZWF2'
        'ZXMgZW1wdHksIGRvZXMgbm90IHRha2UgdGhlIG90aGVyJywgbXNncygnTEVGVCBFTVBUWScpID09'
        'PSAxICYmIGFwaS5wcm90U2F2ZWQgPT09IDEsCiAgICAgICdzYXZlZCAnICsgYXBpLnByb3RTYXZl'
        'ZCk7CmNoZWNrKCduZXZlciB0d28gb24gb25lIGNvbnRhaW5lcicsIHNoYXJlZCA9PT0gMCk7CmNo'
        'ZWNrKCdjb3VudGVkIG9uY2UnLCBsb3N0KCkgPT09IDEsICdsb3N0ICcgKyBsb3N0KCkpOwoKLy8g'
        '4pSA4pSAIDViLiBFbmVteSBjb250YWluZXIgc2hvdCBieSB0aGUgcGxheWVyIChNMDIzKSDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKYmVnaW4oJzViIHNjYW5uZWQgZW5l'
        'bXkgY29udGFpbmVyIHNob3QgYmVmb3JlIHBpY2t1cCcpOwpjb25zdCBjNWIgPSBjb250YWluZXIo'
        'J0MxJywgMzAwLCAyMDAsICdlbmVteScpOyBjb250YWluZXIoJ0MxJywgMzIwLCAzMzAsICdlbmVt'
        'eScpOwpmcmVpZ2h0ZXIoJ0YxJywgLTQwLCAyMDAsICdDMScpOyBmcmVpZ2h0ZXIoJ0YxJywgLTQw'
        'LCAzMDAsICdDMScpOwpydW4oNjAwMCwgdCA9PiB7IGlmKHQgPT09IDEwMCkgYXBpLmtpbGxFbmVt'
        'eShjNWIsIG51bGwsIHRydWUsIGZhbHNlKTsgfSk7CmNoZWNrKCdvbmUgZGVsaXZlcmVkLCBvbmUg'
        'ZW1wdHknLCBhcGkucHJvdFNhdmVkID09PSAxICYmIG1zZ3MoJ0xFRlQgRU1QVFknKSA9PT0gMSk7'
        'CmNoZWNrKCdjb3VudGVkIG9uY2UnLCBsb3N0KCkgPT09IDEsICdsb3N0ICcgKyBsb3N0KCkpOwpj'
        'aGVjaygnbm8gZW5lbXkgY29udGFpbmVyIGhvbGRzIHRoZSB3YXZlJywgYXBpLmxpdmVUaHJlYXRD'
        'b3VudCgpID09PSAwLCAndGhyZWF0cyAnICsgYXBpLmxpdmVUaHJlYXRDb3VudCgpKTsKCi8vIOKU'
        'gOKUgCA2LiBGcmVpZ2h0ZXIgZGllcyBvbiB0aGUgd2F5IOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU'
        'gOKUgOKUgOKUgApiZWdpbignNiAgZnJlaWdodGVyIGRlc3Ryb3llZCBiZWZvcmUgZG9ja2luZycp'
        'Owpjb250YWluZXIoJ0MxJywgMzAwLCAyMDApOyBjb25zdCBmNiA9IGZyZWlnaHRlcignRjEnLCAt'
        'NDAsIDI1MCwgJ0MxJyk7CnJ1big2MDAwLCB0ID0+IHsgaWYodCA9PT0gMTAwKSBhbGx5RGllcyhm'
        'Nik7IH0pOwpjaGVjaygnY29udGFpbmVyIHJlbGVhc2VkIGFzIGxlZnQgYmVoaW5kJywgbXNncygn'
        'Q0FSR08gTEVGVCBCRUhJTkQnKSA9PT0gMSk7CmNoZWNrKCdjb3VudGVkIG9uY2UgKHRoZSBmcmVp'
        'Z2h0ZXIpLCBub3QgdHdpY2UnLCBsb3N0KCkgPT09IDEsICdsb3N0ICcgKyBsb3N0KCkpOwoKLy8g'
        '4pSA4pSAIDcuIEZyZWlnaHRlciBhcnJpdmVzIGJlZm9yZSBpdHMgY29udGFpbmVyIOKUgOKUgOKU'
        'gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgApiZWdpbignNyAgZnJl'
        'aWdodGVyIGluIHRoZSBmaWVsZCwgY29udGFpbmVyIHN0aWxsIHF1ZXVlZCcpOwpmcmVpZ2h0ZXIo'
        'J0YxJywgLTQwLCAyNTAsICdDMScpOyBhcGkuRVZfU0VFTlsnQzEnXSA9IHRydWU7CmFwaS5zcGF3'
        'blEucHVzaCh7dWlkOidDMScsIHR5cGU6J3Byb3RlY3QnLCBzcHI6J2ZjdmMzJ30pOwpydW4oNTAp'
        'OwpjaGVjaygnd2FpdHMgaW5zdGVhZCBvZiBsZWF2aW5nIGVtcHR5JywgbXNncygnTEVGVCBFTVBU'
        'WScpID09PSAwICYmIG1zZ3MoJ05PIENBUkdPJykgPT09IDApOwoKLy8g4pSA4pSAIDguIEZyZWln'
        'aHRlcnMgaGVsZCBiYWNrIGZvciBhbiBldmVudCAoTTAyMykg4pSA4pSA4pSA4pSA4pSA4pSA4pSA'
        '4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSACmJlZ2luKCc4ICBmcmVpZ2h0ZXJzIGhlbGQgZm9yIGFu'
        'IGV2ZW50Jyk7CmNvbnRhaW5lcignQzEnLCAzMDAsIDIwMCwgJ2VuZW15Jyk7CmFwaS5FVl9IRUxE'
        'WydGMSddID0gW3t1aWQ6J0YxJywgdHlwZToncHJvdGVjdCcsIGRvY2tUbzonQzEnfV07CnJ1big1'
        'MCk7CmNoZWNrKCdjb250YWluZXIgaXMgbm90IGRlY2xhcmVkIGxlZnQgYmVoaW5kJywgbXNncygn'
        'Q0FSR08gTEVGVCBCRUhJTkQnKSA9PT0gMCk7CgovLyDilIDilIAgOS4gTTAyNzogdGhyZWUgdHJh'
        'bnNwb3J0cywgb25lIGRlc3Ryb3llciDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIAKYmVnaW4oJzkgIHRyYW5zcG9ydHMgZG9ja2luZyBhdCBhIGRl'
        'c3Ryb3llciBvbmUgYWZ0ZXIgYW5vdGhlcicpOwpjb25zdCBkOSA9IHt1aWQ6J0ExJywgdHlwZTon'
        'ZGVzdHJveWVyJywgaW1nOidkZWhhdHNoZXBzdXQnLCB4OjUyMCwgeTozMDAsIHNjOjEsIGZsaXA6'
        'ZmFsc2UsCiAgICAgICAgICAgIHdhcnA6MCwgZGVhZDpmYWxzZSwgaHA6MjAwMCwgbWF4SHA6NjUw'
        'MH07CmFwaS5hbGxpZXMucHVzaChkOSk7IGFwaS5FVl9TRUVOWydBMSddID0gdHJ1ZTsKY29uc3Qg'
        'dHMgPSBbXTsKbGV0IGRvY2tzID0gMCwgZ2FwID0gMDsKcnVuKDkwMDAsIHQgPT4gewogIGlmKHQg'
        'PT09IDAgfHwgKHRzLmxlbmd0aCAmJiB0cy5sZW5ndGggPCAzICYmIHRzW3RzLmxlbmd0aC0xXS5j'
        'cm9zc2luZyAmJiB0cy5sZW5ndGggPT09IGRvY2tzKSkKICAgIHRzLnB1c2goT2JqZWN0LmFzc2ln'
        'bihmcmVpZ2h0ZXIoJ1QnICsgKHRzLmxlbmd0aCsxKSwgLTQwLCAyMDAsICdBMScpLCB7aW1nOid0'
        'cmlzaXMnLCBndWFyZDp0cnVlfSkpOwogIGNvbnN0IGxhc3QgPSB0c1t0cy5sZW5ndGgtMV07CiAg'
        'aWYobGFzdCAmJiBsYXN0LmNyb3NzaW5nICYmICFsYXN0Ll9jKXsgbGFzdC5fYyA9IDE7IGRvY2tz'
        'Kys7CiAgICBjb25zdCBhID0gYXBpLmRvY2tQb2ludChsYXN0KSwgYiA9IGFwaS5kb2NrUG9pbnQo'
        'ZDkpOyBnYXAgPSBNYXRoLm1heChnYXAsIE1hdGguaHlwb3QoYS54LWIueCwgYS55LWIueSkpOyB9'
        'Cn0pOwpjaGVjaygnYWxsIHRocmVlIGRvY2tlZCcsIGRvY2tzID09PSAzLCBkb2NrcyArICcgZG9j'
        'a2VkJyk7CmNoZWNrKCdkb2NrIHBvaW50cyBtZWV0JywgZ2FwIDw9IDEuMDEsICdnYXAgJyArIGdh'
        'cC50b0ZpeGVkKDIpICsgJyBweCcpOwpjaGVjaygnbm90aGluZyByZXBvcnRlZCBhcyBjYXJnbycs'
        'IG1zZ3MoJ05PIENBUkdPJykgPT09IDAgJiYgbXNncygnTEVGVCBFTVBUWScpID09PSAwKTsKCi8v'
        'IOKUgOKUgCAxMC4gRnJlaWdodGVyIGNvdW50IGZyb20gdGhlIG1pc3Npb24gZGF0YSDilIDilIDi'
        'lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKYmVnaW4oJzEwIGZy'
        'ZWlnaHRlciBjb3VudCBmb2xsb3dzIHRoZSBjb250YWluZXJzJyk7CmNvbnN0IGNudCA9IChtLCBp'
        'ZCkgPT4gYXBpLnNjcmlwdFVuaXRzUmVzb2x2ZWQoYXBpLlNDUklQVF9XQVZFU1ttXSkuZmluZCh1'
        'ID0+IHUuaWQgPT09IGlkKTsKY2hlY2soJ00wMDk6IHR3byBjb250YWluZXJzLCB0d28gZnJlaWdo'
        'dGVycycsIGNudCg5LCAnRjEnKS5uID09PSAyICYmIGNudCg5LCAnQzEnKS5waWNrdXApOwpjaGVj'
        'aygnTTAyMzogdGhyZWUgY29udGFpbmVycywgbm93IHRocmVlIGZyZWlnaHRlcnMnLCBjbnQoMjMs'
        'ICdGMScpLm4gPT09IDMgJiYgY250KDIzLCAnQzEnKS5waWNrdXAsCiAgICAgICd3YXMgJyArIGFw'
        'aS5TQ1JJUFRfV0FWRVNbMjNdLnUuZmluZCh1ID0+IHUuaWQgPT09ICdGMScpLm4pOwpjaGVjaygn'
        'TTAyNzogdHJhbnNwb3J0cyB1bmNoYW5nZWQnLCBjbnQoMjcsICdUMScpLm4gPT09IDEgJiYgIWNu'
        'dCgyNywgJ0ExJykucGlja3VwKTsKY2hlY2soJ21pc3Npb24gZGF0YSBpdHNlbGYgdW50b3VjaGVk'
        'JywgYXBpLlNDUklQVF9XQVZFU1syM10udS5maW5kKHUgPT4gdS5pZCA9PT0gJ0YxJykubiA9PT0g'
        'Mik7Cgpjb25zb2xlLmxvZygnXG4nICsgcGFzcyArICcgcGFzc2VkLCAnICsgZmFpbCArICcgZmFp'
        'bGVkJyk7CnByb2Nlc3MuZXhpdChmYWlsID8gMSA6IDApOwo='
    ),
    'shipsim.js': (
        'Ly8gU2hpcCBzd2l0Y2ggc2ltdWxhdGlvbi4gUHVsbHMgdGhlIFJFQUwgZnVuY3Rpb25zIG91dCBv'
        'ZiB0aGUgbG9naWMgZmlsZSBhbmQKLy8gcnVucyB0aGVtIGFnYWluc3Qgc3RhbmQtaW5zIGZvciB0'
        'aGUgd29ybGQuIFVzYWdlOiBub2RlIHNoaXBzaW0uanMgPGxvZ2ljLmh0bWw+CmNvbnN0IGZzID0g'
        'cmVxdWlyZSgnZnMnKTsKY29uc3QgaHRtbCA9IGZzLnJlYWRGaWxlU3luYyhwcm9jZXNzLmFyZ3Zb'
        'Ml0sICd1dGY4Jyk7CmNvbnN0IHNyYyA9IGh0bWwubWF0Y2goLzxzY3JpcHRbXj5dKj4oW1xzXFNd'
        'Kik8XC9zY3JpcHQ+LylbMV07CgpmdW5jdGlvbiBibG9ja0VuZChzLCBpKXsKICBpID0gcy5pbmRl'
        'eE9mKCd7JywgaSk7IGxldCBkID0gMDsKICBmb3IoOyBpIDwgcy5sZW5ndGg7IGkrKyl7CiAgICBj'
        'b25zdCBjID0gc1tpXTsKICAgIGlmKGM9PT0iJyJ8fGM9PT0nIid8fGM9PT0nYCcpeyBjb25zdCBx'
        'PWM7IGkrKzsgd2hpbGUoaTxzLmxlbmd0aCAmJiBzW2ldIT09cSl7IGlmKHNbaV09PT0nXFwnKSBp'
        'Kys7IGkrKzsgfSB9CiAgICBlbHNlIGlmKHMuc3RhcnRzV2l0aCgnLy8nLCBpKSkgaSA9IHMuaW5k'
        'ZXhPZignXG4nLCBpKTsKICAgIGVsc2UgaWYocy5zdGFydHNXaXRoKCcvKicsIGkpKSBpID0gcy5p'
        'bmRleE9mKCcqLycsIGkpICsgMTsKICAgIGVsc2UgaWYoYz09PSd7JykgZCsrOwogICAgZWxzZSBp'
        'ZihjPT09J30nKXsgZC0tOyBpZihkPT09MCkgcmV0dXJuIGkrMTsgfQogIH0KICB0aHJvdyBuZXcg'
        'RXJyb3IoJ25vIGJsb2NrIGVuZCcpOwp9CmZ1bmN0aW9uIGZuKG5hbWUpewogIGNvbnN0IGkgPSBz'
        'cmMuaW5kZXhPZignXG5mdW5jdGlvbiAnK25hbWUrJygnKTsKICBpZihpPDApIHRocm93IG5ldyBF'
        'cnJvcignbWlzc2luZyBmdW5jdGlvbiAnK25hbWUpOwogIHJldHVybiBzcmMuc2xpY2UoaSsxLCBi'
        'bG9ja0VuZChzcmMsIGkpKTsKfQpmdW5jdGlvbiBiZXR3ZWVuKHN0YXJ0VGV4dCl7CiAgY29uc3Qg'
        'aSA9IHNyYy5pbmRleE9mKHN0YXJ0VGV4dCk7IGlmKGk8MCkgdGhyb3cgbmV3IEVycm9yKCdtaXNz'
        'aW5nICcrc3RhcnRUZXh0KTsKICBjb25zdCBqID0gc3JjLmluZGV4T2YoJ2Z1bmN0aW9uJywgaSk7'
        'CiAgcmV0dXJuIHNyYy5zbGljZShqLCBibG9ja0VuZChzcmMsIGopKTsKfQpjb25zdCBzaGlwc0Rl'
        'Y2wgPSBzcmMubWF0Y2goL2NvbnN0IFBMQVlFUl9TSElQUyA9IFxbW1xzXFNdKj9cXTsvKVswXTsK'
        'Ly8gVGhlIGN5Y2xlIHRhYmxlcyBhbmQgdGhlIHN1cHBvcnQgY29sdW1ucyB0aGV5IHN3aXRjaC4K'
        'Y29uc3QgY3ljbGVEZWNsID0gc3JjLm1hdGNoKC9jb25zdCBST1NURVJfSE9MW1xzXFNdKj9cbmxl'
        'dCBjeWNsZUJhc2UgPSAwO1teXG5dKi8pWzBdOwpjb25zdCBmYWNPbkRlY2wgPSBzcmMubWF0Y2go'
        'L2NvbnN0IEFMTFlfRkFDX09OID0gXHtbXn1dKlx9Oy8pWzBdOwpjb25zdCBleHRyYURlY2wgPSBz'
        'cmMubWF0Y2goL2NvbnN0IEVYVFJBX1NISVBTID0gKFx7W1xzXFNdKj9cblx9KTsvKVsxXTsKY29u'
        'c3QgaHVsbEZhY0RlY2wgPSBzcmMubWF0Y2goL2NvbnN0IEhVTExfRkFDID0gXHtbXHNcU10qP1x9'
        'Oy8pWzBdOwpjb25zdCBtZW51QmdEZWNsID0gc3JjLm1hdGNoKC9jb25zdCBNRU5VX0JHX0FMUEhB'
        'W1xzXFNdKj9jb25zdCBNRU5VX0JHX1BBRFxzKj1ccypbXGQuXSs7LylbMF07CmNvbnN0IGhhbmdh'
        'ckRlY2wgPSBzcmMubWF0Y2goL2NvbnN0IEhHX1dbXHNcU10qP1xuXF07LylbMF07CmNvbnN0IHRo'
        'ZW1lc0RlY2wgPSBzcmMubWF0Y2goL2NvbnN0IFRIRU1FUyA9IFx7W1xzXFNdKj9cblx9Oy8pWzBd'
        'OwovLyBUaGUgd2VhcG9uIHRhYmxlcyBhbmQgdGhlIHJlYXJtIHBhbmVsJ3MgbWVhc3VyZW1lbnRz'
        'Lgpjb25zdCB3cG5EZWNsICA9IHNyYy5tYXRjaCgvY29uc3QgUExBWUVSX0ZSX0JBU0VbXHNcU10q'
        'P1xuXF07LylbMF07CmNvbnN0IHdwbkRlY2wyID0gc3JjLm1hdGNoKC9jb25zdCBTRUNPTkRBUklF'
        'UyA9IFxbW1xzXFNdKj9cblxdOy8pWzBdOwpjb25zdCBybURlY2wgICA9IHNyYy5tYXRjaCgvY29u'
        'c3QgUk1fV1tcc1xTXSo/Y29uc3QgUk1fQ09MU19TRUMgPSBcW1tcc1xTXSo/XG5cXTsvKVswXTsK'
        'Ly8gcG9pbnRlckNvbnN1bWVkIHJlYWNoZXMgZm9yIHRoZSB0aXRsZSBvbiBhIGZpbmlzaGVkIHJ1'
        'bi4gU3RhcnRpbmcgYSBydW4KLy8gaXMgbm90IHdoYXQgdGhlc2UgZmlsZXMgdGVzdCwgc28gaXQg'
        'aXMgYSBzdHViLgpjb25zdCB3cG5TdGF0ZSA9ICdsZXQgcmVhcm1NZW51ID0gZmFsc2U7IGxldCBy'
        'ZXN1bWVIb2xkID0gZmFsc2U7JwogIC8vIFRoZSBiYXIgYXNrcyB3aGVyZSB0aGUgcG9pbnRlciBp'
        'cyBzaXR0aW5nOyBub3RoaW5nIGhvdmVycyBpbiBhIHRlc3QuCiAgKyAnIGNvbnN0IEhPVkVSID0g'
        'e3g6LTEsIHk6LTF9OyBmdW5jdGlvbiB0b1RpdGxlT3JMYXVuY2goKXt9OyBjb25zdCBXUE5fU0VF'
        'TiA9IHt9OyBjb25zdCBVSV9XRUFQT05TID0gZmFsc2U7JzsKCmNvbnN0IHZvbGxleURlY2wgPSBz'
        'cmMubWF0Y2goL2NvbnN0IFZPTExFWV9CQVNFW1xzXFNdKj9jb25zdCBWT0xMRVlfUEVSX0VYVFJB'
        'XHMqPVxzKltcZC5dKzsvKVswXTsKY29uc3QgbmFtZXMgPSBbCiAgJ3N5bmNDdXJzb3InLCdob3Zl'
        'cmluZycsCiAgJ3BhbmVsT3BlbicsJ2hvbGRSZXN1bWUnLCdjbGVhclJlc3VtZUhvbGQnLCdkcmF3'
        'UmVzdW1lSGludCcsCiAgJ2FwcGx5TG9hZG91dCcsJ3JlYXJtRnVsbCcsJ2N1clByaScsJ2N1clNl'
        'YycsJ3ByaURlZicsJ3NlY0RlZicsJ2h1bGxTZWNDbHMnLAogICd3ZWFwb25OYW1lJywnd2VhcG9u'
        'T3BlbicsJ3NlY29uZGFyaWVzRm9yJywnZGVmYXVsdFNlYycsJ2NvcnZldHRlT25GaWVsZCcsCiAg'
        'J3JlYXJtUmVhZHknLCdzZXRSZWFybU1lbnUnLCd0b2dnbGVSZWFybU1lbnUnLCdmaXRXZWFwb24n'
        'LCdyZWFybUxheW91dCcsCiAgJ2RyYXdSZWFybU1lbnUnLCdkcmF3UmVhcm1JY29uJywncmVhcm1H'
        'cm91cHMnLCdybVZhbHVlJywndGlja1dlYXBvblVubG9ja3MnLAogICd0aEZpdCcsJ2NhbGxNZW51'
        'TGF5b3V0JywnZHJhd0FsbHlSb3cnLCdkcmF3S2V5Q2hpcCcsJ2RyYXdIdWxsQ2VsbCcsJ2h1bGxD'
        'bGFzcycsJ2lzQm9tYmVySHVsbCcsJ3NoaXBTdGF0cycsJ2FwcGx5U2hpcCcsJ3RpY2tTaGlwVW5s'
        'b2NrcycsJ3NoaXBTd2FwUmVhZHknLAogICdzZXRTaGlwTWVudScsJ3RvZ2dsZVNoaXBNZW51Jywn'
        'c3dhcFNoaXAnLCdkcmF3U3dhcEljb24nLCdzdGF0UGlwcycsJ2RyYXdTaGlwTWVudScsJ3BvaW50'
        'ZXJDb25zdW1lZCcsCiAgJ3Jlc2V0UGxheWVyU2hpZWxkJywncGxheWVyU2MnLCdzZXRDYWxsTWVu'
        'dScsCiAgJ2h1bGxGYWMnLCdzaGlwRmFjJywnaGFuZ2FyU2VydmVzJywnaXNIYW5nYXJTaGlwJywn'
        'aGFuZ2FyRmFjcycsJ2NvbG9zc3VzT25GaWVsZCcsJ3NoaXBPZmZlcmVkJywKICAnbW91bnRzRm9y'
        'Jywnc3ByaXRlRmFjaW5nJywnZHJhd0h1bGxCZycsJ2RyYXdIdWxsQ2VsbCcsJ3ZvbGxleURtZycs'
        'J3ZvbGxleVRvdGFsJywncHJpbWFyeUNvdW50Jywnc3luY1BhdXNlJywKICAnaGFuZ2FyR3JvdXBz'
        'JywnaGFuZ2FyTGF5b3V0JywnZHJhd01pc3NpbGVJY29uJywnZHJhd0JvbWJJY29uJywnZHJhd0tl'
        'eUNoaXAnLAogICdoYW5nYXJPcmRlcicsJ2luc2lkZVBhbmVsJywnY3ljbGVBdCcsJ2VudGVyQ3lj'
        'bGUnLCd0aXRsZUZzSGl0JywnZm9yY2VTaGlwJywncmVsZWFzZVNoaXAnLAogICd0aENoYW1mZXJQ'
        'YXRoJywndGhQbGF0ZScsJ3RoR2xvd1BhdGgnLCd0aEJyYWNrZXRzJywndGhTY2FsZScsJ3RoRnJh'
        'bWUnLCd0aFJHQkEnLCd0aEdsb3NzJywndGhDdXRHbGludCcsCiAgJ1RIJywndGhMYWJlbCcsJ3Ro'
        'VmFsdWUnLCd0aEJldmVsJywndGhHbG93JywndGhQYW5lbCcsJ3RoQnV0dG9uJywndGhEaXZpZGVy'
        'JywnZHJhd1N3YXBJY29uJywnVUknLCd1aUhMUCcsJ3VpTGFiZWwnLCd1aVZhbHVlJywndWlDZWxs'
        'JywndWlEaWFsb2cnXTsKY29uc3Qga2V5SGFuZGxlciA9IGJldHdlZW4oImRvY3VtZW50LmFkZEV2'
        'ZW50TGlzdGVuZXIoJ2tleWRvd24nLGZ1bmN0aW9uKGV2KXtcbiAgaWYoR1MhPT0ncGxheWluZycp'
        'IHJldHVybjsiKTsKY29uc3QgZG93blN0YXJ0ID0gc3JjLmluZGV4T2YoIkNWUy5hZGRFdmVudExp'
        'c3RlbmVyKCdtb3VzZWRvd24nLCIpOwpjb25zdCBtb3VzZUhhbmRsZXIgPSBzcmMuc2xpY2Uoc3Jj'
        'LmluZGV4T2YoJ2Z1bmN0aW9uJywgZG93blN0YXJ0KSwgYmxvY2tFbmQoc3JjLCBzcmMuaW5kZXhP'
        'ZignZnVuY3Rpb24nLCBkb3duU3RhcnQpKSk7CmNvbnN0IGxhdW5jaCA9IGZuKCdsYXVuY2hHYW1l'
        'Jyk7Cgpjb25zdCBDQUxMUyA9IFtdOwpjb25zdCBjdHhTdHViID0gbmV3IFByb3h5KHt9LCB7CiAg'
        'Z2V0Oih0LGspPT4gayBpbiB0ID8gdFtrXSA6IGZ1bmN0aW9uKCl7CiAgICBDQUxMUy5wdXNoKHtm'
        'bjpTdHJpbmcoayksIGFyZ3M6W10uc2xpY2UuY2FsbChhcmd1bWVudHMpfSk7CiAgICAvLyBjcmVh'
        'dGVMaW5lYXJHcmFkaWVudCBoYXMgdG8gaGFuZCBiYWNrIHNvbWV0aGluZyB3aXRoIGFkZENvbG9y'
        'U3RvcC4KICAgIGlmKGs9PT0nY3JlYXRlTGluZWFyR3JhZGllbnQnKSByZXR1cm4ge2FkZENvbG9y'
        'U3RvcDpmdW5jdGlvbigpe319OwogICAgLy8gdGhGaXQgbWVhc3VyZXMgYmVmb3JlIGl0IGN1dHMs'
        'IHNvIHRoZSBzdHViIGhhcyB0byBhbnN3ZXIgd2l0aCBhIHdpZHRoLgogICAgLy8gUm91Z2hseSAw'
        'LjU1IG9mIHRoZSBzZXQgcG9pbnQgc2l6ZSBwZXIgY2hhcmFjdGVyIGlzIGNsb3NlIGVub3VnaCBm'
        'b3IKICAgIC8vIHRoZSBsYXlvdXQgZGVjaXNpb25zIGJlaW5nIGNoZWNrZWQgaGVyZS4KICAgIGlm'
        'KGs9PT0nbWVhc3VyZVRleHQnKXsKICAgICAgY29uc3QgcHggPSBwYXJzZUZsb2F0KFN0cmluZyh0'
        'LmZvbnR8fCcxMHB4JykucmVwbGFjZSgvXmJvbGRccysvLCcnKSkgfHwgMTA7CiAgICAgIHJldHVy'
        'biB7d2lkdGg6IFN0cmluZyhhcmd1bWVudHNbMF18fCcnKS5sZW5ndGggKiBweCAqIDAuNTV9Owog'
        'ICAgfQogIH0sCiAgc2V0Oih0LGssdik9PnsgQ0FMTFMucHVzaCh7Zm46J3NldCAnK1N0cmluZyhr'
        'KSwgYXJnczpbdl19KTsgdFtrXT12OyByZXR1cm4gdHJ1ZTsgfQp9KTsKLy8gSGVscGVycyBvdmVy'
        'IHRoZSByZWNvcmRlZCBkcmF3aW5nIGNhbGxzLgpjb25zdCBDTFIgICAgPSAoKT0+eyBDQUxMUy5s'
        'ZW5ndGggPSAwOyB9Owpjb25zdCBkcmF3cyAgPSAoKT0+IENBTExTLmZpbHRlcihjPT5jLmZuPT09'
        'J2RyYXdJbWFnZScpOwpjb25zdCBjbGlwcyAgPSAoKT0+IENBTExTLmZpbHRlcihjPT5jLmZuPT09'
        'J2NsaXAnKTsKY29uc3QgYWxwaGFzID0gKCk9PiBDQUxMUy5maWx0ZXIoYz0+Yy5mbj09PSdzZXQg'
        'Z2xvYmFsQWxwaGEnKS5tYXAoYz0+Yy5hcmdzWzBdKTsKLy8gRXZlcnkgc3ByaXRlIGhhcyB0byBz'
        'aXQgaW5zaWRlIGEgc2F2ZS9yZXN0b3JlIHBhaXIsIG90aGVyd2lzZSBpdHMgY2xpcCBhbmQKLy8g'
        'aXRzIGFscGhhIGxlYWsgaW50byB3aGF0ZXZlciBpcyBkcmF3biBuZXh0LgpmdW5jdGlvbiBiYWxh'
        'bmNlZCgpewogIGxldCBkID0gMCwgb2tBbGwgPSB0cnVlOwogIGZvcihjb25zdCBjIG9mIENBTExT'
        'KXsKICAgIGlmKGMuZm49PT0nc2F2ZScpIGQrKzsKICAgIGVsc2UgaWYoYy5mbj09PSdyZXN0b3Jl'
        'Jyl7IGQtLTsgaWYoZDwwKSBva0FsbD1mYWxzZTsgfQogICAgZWxzZSBpZigoYy5mbj09PSdkcmF3'
        'SW1hZ2UnIHx8IGMuZm49PT0nY2xpcCcpICYmIGQ8MSkgb2tBbGw9ZmFsc2U7CiAgfQogIHJldHVy'
        'biBva0FsbCAmJiBkPT09MDsKfQoKY29uc3Qgd29ybGQgPSBgCiAgY29uc3QgVz04MDAsSD01MDAs'
        'SFVEX0g9NTQsIFBMQVlFUl9TUERfRklHSFRFUj0zLjIsIFBMQVlFUl9TUERfQk9NQkVSPTIuNCwg'
        'UExBWUVSX1RVUk49MC4xNDsKICBsZXQgRlMxX01PREU9ZmFsc2UsIEdTPSdwbGF5aW5nJywgcGF1'
        'c2VkPWZhbHNlLCBjYWxsTWVudT1mYWxzZSwgd2F2ZT0xLCBzY29yZT0wLCBhbGxpZXM9W10sIGp1'
        'bXA9ZmFsc2U7CiAgbGV0IHNldHRpbmdzT3Blbj1mYWxzZSwgdXNlclBhdXNlZD1mYWxzZTsKICBs'
        'ZXQgU1VCX01TR1M9W10sIE1PVVNFPXt4OjAseTowfSwgbGl2ZXM9MywgcGxheWVyPXt4OjEwMCx5'
        'OjIwMCxodWxsTXVsdDoxfTsKICAvLyBOb3RpY2VzIGdvIHRvIHRoZSBjb2x1bW4gdW5kZXIgdGhl'
        'IG9iamVjdGl2ZSBsaW5lOyB0aGUgY29sdW1uIGl0c2VsZgogIC8vIGlzIG5vdCB1bmRlciB0ZXN0'
        'IGhlcmUsIG9ubHkgd2hhdCBpcyBhbm5vdW5jZWQuCiAgbGV0IE5PVElDRV9MT0c9W107IGZ1bmN0'
        'aW9uIG5vdGljZSh0LCB0b25lKXsgTk9USUNFX0xPRy5wdXNoKHt0eHQ6dCwgdG9uZTp0b25lfSk7'
        'IH0KICAvLyBUaGUgYmFyJ3MgYXR0ZW50aW9uIHB1bHNlcyBhcmUgdGhlIGZpZWxkIHNpbXVsYXRp'
        'b24ncyBidXNpbmVzcy4KICBsZXQgQkFSX1BVTFNFPXt9OyBmdW5jdGlvbiBiYXJQdWxzZUxldmVs'
        'KCl7IHJldHVybiAwOyB9IGZ1bmN0aW9uIGJhclB1bHNlKCl7fQogIC8vIFRoZSBwcmFjdGljZSBs'
        'b2cgaXMgbm90IHdoYXQgaXMgdGVzdGVkIGhlcmUuCiAgZnVuY3Rpb24gcGxvZ1JlYXJtKCl7fSBm'
        'dW5jdGlvbiBwbG9nU2VjKCl7fSBmdW5jdGlvbiBwbG9nU3luYygpe30gZnVuY3Rpb24gcGxvZ0V2'
        'ZW50KCl7fQogIC8vIEEgaHVsbCBsZW50IGJ5IGEgbWlzc2lvbiAoc2VlIGZvcmNlU2hpcCkuCiAg'
        'bGV0IGZvcmNlZFByZXY9Jyc7CiAgbGV0IGVyYU9mZj1mYWxzZSwgSU1HUz17fSwgaXNGaXJpbmc9'
        'ZmFsc2UsIGxhdW5jaGVkPTA7CiAgY29uc3QgY3R4PUNUWCwgZG9jdW1lbnQ9e2JvZHk6e2NsYXNz'
        'TGlzdDp7YWRkKCl7fSxyZW1vdmUoKXt9fX0sIGdldEVsZW1lbnRCeUlkKCl7cmV0dXJuIHtzdHls'
        'ZTp7fX07fX07CiAgY29uc3Qgd2luZG93PXt9OwogIGZ1bmN0aW9uIGluSnVtcCgpe3JldHVybiBq'
        'dW1wO30gZnVuY3Rpb24gZXJhU2hpZWxkc09mZigpe3JldHVybiBlcmFPZmY7fQogIGZ1bmN0aW9u'
        'IHNldFNldHRpbmdzKCl7fSBmdW5jdGlvbiB0b2dnbGVGdWxsc2NyZWVuKCl7fSBmdW5jdGlvbiBy'
        'ZWZpbmVUaWNrZXQoKXt9IGZ1bmN0aW9uIGNhbGxBbGx5KCl7fQogIGZ1bmN0aW9uIGFsbHlSZWFk'
        'eSgpe3JldHVybiB0cnVlO30gZnVuY3Rpb24gdG9nZ2xlQ2FsbE1lbnUoKXt9IGZ1bmN0aW9uIHRv'
        'R0MoeCx5KXtyZXR1cm4ge3g6eCx5Onl9O30KICBsZXQgc2hpcFVubG9ja2VkPTEsIHNoaXBTd2Fw'
        'V2F2ZT0tMSwgc2hpcE1lbnU9ZmFsc2UsIGdhbWVPdmVyQXQ9MDsKICBjb25zdCBBTExZX0tFWVM9'
        'W10sIEFMTFlfT1JERVI9W10sIEFMTFlfU1BFQ0lBTD0neCcsIEFMTFlfU1BFQ0lBTF9LRVk9J1En'
        'OwogICR7aHVsbEZhY0RlY2x9CiAgJHt3cG5EZWNsfQogICR7d3BuRGVjbDJ9CiAgJHtybURlY2x9'
        'CiAgJHt3cG5TdGF0ZX0KICAke3RoZW1lc0RlY2x9CiAgbGV0IEVDTz17aHVkOidobHAnLCBzY2hl'
        'bWU6J2ZpcmUnfTsKICAke21lbnVCZ0RlY2x9CiAgJHtoYW5nYXJEZWNsfQogICR7dm9sbGV5RGVj'
        'bH0KICBsZXQgTU9VTlRTPXt9OwogICR7c2hpcHNEZWNsfQogIGxldCBVSV9TSElQUz0xOwogIGNv'
        'bnN0IEVYVFJBX1NISVBTID0gJHtleHRyYURlY2x9OwogICR7ZmFjT25EZWNsfQogICR7Y3ljbGVE'
        'ZWNsfQogICR7bmFtZXMubWFwKGZuKS5qb2luKCdcbicpfQogIGNvbnN0IG9uS2V5ID0gJHtrZXlI'
        'YW5kbGVyfTsKICBjb25zdCBvbkRvd24gPSAke21vdXNlSGFuZGxlcn07CiAgcmV0dXJuIHsKICAg'
        'IGdldDooayk9PmV2YWwoayksIHNldDooayx2KT0+ZXZhbChrKyc9dicpLCBydW46KGNvZGUpPT5l'
        'dmFsKGNvZGUpCiAgfTtgOwpjb25zdCBXID0gbmV3IEZ1bmN0aW9uKCdDVFgnLCB3b3JsZCkoY3R4'
        'U3R1Yik7CmxldCBmYWlscyA9IDA7CmZ1bmN0aW9uIG9rKGxhYmVsLCBjb25kKXsgY29uc29sZS5s'
        'b2coKGNvbmQ/JyAgb2sgICAgJzonICBGQUlMICAnKStsYWJlbCk7IGlmKCFjb25kKSBmYWlscysr'
        'OyB9CmNvbnN0IFAgPSAoKT0+Vy5nZXQoJ3BsYXllcicpOwpjb25zdCByZXNldCA9ICgpPT57IFcu'
        'cnVuKCJHUz0ncGxheWluZyc7cGF1c2VkPWZhbHNlO3Jlc3VtZUhvbGQ9ZmFsc2U7Y2FsbE1lbnU9'
        'ZmFsc2U7c2hpcE1lbnU9ZmFsc2U7d2F2ZT0xO3Njb3JlPTA7YWxsaWVzPVtdO2p1bXA9ZmFsc2U7'
        'RlMxX01PREU9ZmFsc2U7c2hpcFVubG9ja2VkPTE7c2hpcFN3YXBXYXZlPS0xO1NVQl9NU0dTPVtd'
        'O05PVElDRV9MT0c9W107cGxheWVyPXt4OjEwMCx5OjIwMCxodWxsTXVsdDoxfTthcHBseVNoaXAo'
        'UExBWUVSX1NISVBTWzBdLmtleSkiKTsgfTsKY29uc3QgZGVzdHJveWVyID0gKG8pPT5PYmplY3Qu'
        'YXNzaWduKHtpbWc6J2RlaGF0c2hlcHN1dCcsIHNtYWxsOmZhbHNlLCBkZWFkOmZhbHNlLCB3YXJw'
        'T3V0OmZhbHNlfSwgb3x8e30pOwoKY29uc29sZS5sb2coJ1N0YXJ0IHNoaXAnKTsKcmVzZXQoKTsK'
        'b2soJ3N0YXJ0cyBpbiB0aGUgVGhvdGgnLCBQKCkuc2hpcD09PSdmaXRvdGgnKTsKb2soJ1Rob3Ro'
        'IHN0YXRzIDMuNSAvIDAuMTcgLyAxMDAgLyAxMDAgLyAyMCBtaXNzaWxlcycsIFAoKS5zcGQ9PT0z'
        'LjUgJiYgUCgpLnR1cm49PT0wLjE3ICYmIFAoKS5tYXhIcD09PTEwMCAmJiBQKCkubWF4U2g9PT0x'
        'MDAgJiYgUCgpLnNlY01heD09PTIwICYmIFAoKS5zZWNUeXBlPT09J21pc3NpbGUnKTsKCmNvbnNv'
        'bGUubG9nKCdVbmxvY2tzJyk7CnJlc2V0KCk7ClcucnVuKCJzY29yZT0zOTk5OyB0aWNrU2hpcFVu'
        'bG9ja3MoKSIpOyBvaygnMzk5OSBwb2ludHM6IG5vdGhpbmcgdW5sb2NrZWQnLCBXLmdldCgnc2hp'
        'cFVubG9ja2VkJyk9PT0xKTsKVy5ydW4oInNjb3JlPTQwMDA7IHRpY2tTaGlwVW5sb2NrcygpIik7'
        'IG9rKCc0MDAwIHBvaW50czogSG9ydXMgdW5sb2NrZWQsIG9uZSBtZXNzYWdlJywgVy5nZXQoJ3No'
        'aXBVbmxvY2tlZCcpPT09MiAmJiBXLmdldCgnTk9USUNFX0xPRycpLmxlbmd0aD09PTEgJiYgL0hP'
        'UlVTLy50ZXN0KFcuZ2V0KCdOT1RJQ0VfTE9HJylbMF0udHh0KSk7ClcucnVuKCJzY29yZT0yMzAw'
        'MDsgdGlja1NoaXBVbmxvY2tzKCkiKTsgb2soJ2p1bXAgdG8gMjMwMDA6IE9zaXJpcywgU2VyYXBp'
        'cywgU2V0aCBhdCBvbmNlJywgVy5nZXQoJ3NoaXBVbmxvY2tlZCcpPT09NSAmJiBXLmdldCgnTk9U'
        'SUNFX0xPRycpLmxlbmd0aD09PTQpOwpXLnJ1bigic2NvcmU9OTk5OTk5OyB0aWNrU2hpcFVubG9j'
        'a3MoKSIpOyBvaygnbmV2ZXIgcGFzdCB0aGUgZW5kIG9mIHRoZSBsaXN0JywgVy5nZXQoJ3NoaXBV'
        'bmxvY2tlZCcpPT09OCk7ClcucnVuKCJ0aWNrU2hpcFVubG9ja3MoKSIpOyBvaygnc2V2ZW4gdW5s'
        'b2NrIG1lc3NhZ2VzIGluIHRvdGFsLCBub25lIHJlcGVhdGVkJywgVy5nZXQoJ05PVElDRV9MT0cn'
        'KS5sZW5ndGg9PT03KTsKcmVzZXQoKTsgVy5ydW4oIkZTMV9NT0RFPXRydWU7IHNjb3JlPTk5OTk5'
        'OyB0aWNrU2hpcFVubG9ja3MoKSIpOyBvaygnRlMxIG1vZGU6IG5vIHVubG9ja3MnLCBXLmdldCgn'
        'c2hpcFVubG9ja2VkJyk9PT0xKTsKcmVzZXQoKTsgVy5ydW4oIkdTPSdnYW1lb3Zlcic7IHNjb3Jl'
        'PTk5OTk5OyB0aWNrU2hpcFVubG9ja3MoKSIpOyBvaygnbm90IG91dHNpZGUgcGxheScsIFcuZ2V0'
        'KCdzaGlwVW5sb2NrZWQnKT09PTEpOwoKY29uc29sZS5sb2coJ1doZW4gdGhlIHN3aXRjaCBpcyBh'
        'dmFpbGFibGUnKTsKY29uc3QgcmVhZHkgPSAoc2V0dXApPT57IHJlc2V0KCk7IFcucnVuKCJzaGlw'
        'VW5sb2NrZWQ9MyIpOyBzZXR1cCgpOyByZXR1cm4gVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpOyB9'
        'Owpvaygnbm8gZGVzdHJveWVyOiBub3QgcmVhZHknLCByZWFkeSgoKT0+e30pPT09ZmFsc2UpOwpv'
        'aygnYWxsaWVkIFZhc3VkYW4gZGVzdHJveWVyOiByZWFkeScsIHJlYWR5KCgpPT5XLnNldCgnYWxs'
        'aWVzJyxbZGVzdHJveWVyKCldKSk9PT10cnVlKTsKb2soJ05URiBodWxsIChudGZkZWhlY2F0ZSkg'
        'aXMgVGVycmFuLCBubyBUZXJyYW4gaHVsbHMgZXhpc3Q6IG5vdCByZWFkeScsCiAgIHJlYWR5KCgp'
        'PT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKHtpbWc6J250ZmRlaGVjYXRlJ30pXSkpPT09ZmFs'
        'c2UpOwpvaygnY3J1aXNlciBvbmx5OiBub3QgcmVhZHknLCByZWFkeSgoKT0+Vy5zZXQoJ2FsbGll'
        'cycsW2Rlc3Ryb3llcih7aW1nOidjcm1lbnR1J30pXSkpPT09ZmFsc2UpOwpvaygnQ29sb3NzdXMg'
        'YWxvbmUgaXMgYSBqb2ludCB5YXJkOiByZWFkeScsCiAgIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVz'
        'JyxbZGVzdHJveWVyKHtpbWc6J3NkY29sb3NzdXMnLCBjb2xvc3N1czp0cnVlfSldKSk9PT10cnVl'
        'KTsKb2soJ2RlYWQgZGVzdHJveWVyOiBub3QgcmVhZHknLCByZWFkeSgoKT0+Vy5zZXQoJ2FsbGll'
        'cycsW2Rlc3Ryb3llcih7ZGVhZDp0cnVlfSldKSk9PT1mYWxzZSk7Cm9rKCdkZXN0cm95ZXIgd2Fy'
        'cGluZyBvdXQ6IG5vdCByZWFkeScsIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVzJyxbZGVzdHJveWVy'
        'KHt3YXJwT3V0OnRydWV9KV0pKT09PWZhbHNlKTsKb2soJ29ubHkgdGhlIHN0YXJ0IHNoaXAgdW5s'
        'b2NrZWQ6IG5vdCByZWFkeScsIHJlYWR5KCgpPT57IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIo'
        'KV0pOyBXLnJ1bignc2hpcFVubG9ja2VkPTEnKTsgfSk9PT1mYWxzZSk7Cm9rKCdkdXJpbmcgYSBq'
        'dW1wOiBub3QgcmVhZHknLCByZWFkeSgoKT0+eyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCld'
        'KTsgVy5ydW4oJ2p1bXA9dHJ1ZScpOyB9KT09PWZhbHNlKTsKb2soJ0ZTMSBtb2RlOiBub3QgcmVh'
        'ZHknLCByZWFkeSgoKT0+eyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ0ZT'
        'MV9NT0RFPXRydWUnKTsgfSk9PT1mYWxzZSk7Cgpjb25zb2xlLmxvZygnU3dpdGNoaW5nJyk7CnJl'
        'c2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MzsgcGxheWVyLmhwPTEyOyBwbGF5ZXIuc2g9NTsg'
        'cGxheWVyLnNlY0FtbW89MSIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKVy5ydW4o'
        'J3RvZ2dsZVNoaXBNZW51KCknKTsgb2soJ2J1dHRvbiBvcGVucyB0aGUgbWVudSBhbmQgcGF1c2Vz'
        'JywgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlICYmIFcuZ2V0KCdwYXVzZWQnKT09PXRydWUpOwpX'
        'LnJ1bigic3dhcFNoaXAoJ2Zpc2VyYXBpcycpIik7IG9rKCdsb2NrZWQgaHVsbCAoU2VyYXBpcykg'
        'cmVmdXNlZCcsIFAoKS5zaGlwPT09J2ZpdG90aCcgJiYgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVl'
        'KTsKVy5ydW4oInN3YXBTaGlwKCdmaXRvdGgnKSIpOyBvaygnY3VycmVudCBodWxsIHJlZnVzZWQn'
        'LCBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUgJiYgVy5nZXQoJ3NoaXBTd2FwV2F2ZScpPT09LTEp'
        'OwpXLnJ1bigic3dhcFNoaXAoJ2Jvb3NpcmlzJykiKTsKLy8gVGhlIHBhbmVsIGNsb3NlcywgYnV0'
        'IHRoZSBnYW1lIHN0YXlzIHN0b3BwZWQ6IGNvbWluZyBiYWNrIGludG8gdGhlCi8vIGZpZ2h0IGlz'
        'IHRoZSBwbGF5ZXIncyB0byB0aW1lIG5vdywgd2hhdGV2ZXIgdGhlIHBhbmVsIGFuZCBob3dldmVy'
        'IGl0Ci8vIHdhcyBsZWZ0LgpvaygnT3NpcmlzIHRha2VuIGFuZCB0aGUgbWVudSBjbG9zZWQnLCBQ'
        'KCkuc2hpcD09PSdib29zaXJpcycgJiYgVy5nZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7Cm9rKCdi'
        'dXQgdGhlIGdhbWUgaXMgc3RpbGwgaGVsZCcsIFcuZ2V0KCdwYXVzZWQnKT09PXRydWUgJiYgVy5n'
        'ZXQoJ3Jlc3VtZUhvbGQnKT09PXRydWUpOwpXLnJ1bigncG9pbnRlckNvbnN1bWVkKHt4OjQwMCx5'
        'OjMwMH0pJyk7Cm9rKCdhbmQgb25lIHRhcCBwdXRzIHlvdSBiYWNrIGluIGl0JywgVy5nZXQoJ3Bh'
        'dXNlZCcpPT09ZmFsc2UgJiYgVy5nZXQoJ3Jlc3VtZUhvbGQnKT09PWZhbHNlKTsKb2soJ09zaXJp'
        'cyBzdGF0cyAyLjUgLyAwLjEwIC8gMTQwIC8gMTAwIC8gMTAgYm9tYnMnLCBQKCkuc3BkPT09Mi41'
        'ICYmIFAoKS50dXJuPT09MC4xMCAmJiBQKCkubWF4SHA9PT0xNDAgJiYgUCgpLm1heFNoPT09MTAw'
        'ICYmIFAoKS5zZWNNYXg9PT0xMCAmJiBQKCkuc2VjVHlwZT09PSdib21iJyk7Cm9rKCdyZWZpbGxl'
        'ZDogaHVsbCAxNDAsIHNoaWVsZHMgMTAwLCAxMCBib21icycsIFAoKS5ocD09PTE0MCAmJiBQKCku'
        'c2g9PT0xMDAgJiYgUCgpLnNlY0FtbW89PT0xMCk7Cm9rKCdzd2l0Y2ggc3BlbnQgZm9yIHRoaXMg'
        'd2F2ZScsIFcucnVuKCdzaGlwU3dhcFJlYWR5KCknKT09PWZhbHNlKTsKVy5ydW4oJ3RvZ2dsZVNo'
        'aXBNZW51KCknKTsgb2soJ21lbnUgZG9lcyBub3Qgb3BlbiBhZ2FpbiB0aGlzIHdhdmUnLCBXLmdl'
        'dCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKVy5ydW4oJ3dhdmU9MicpOyBvaygnbmV4dCB3YXZlOiBh'
        'dmFpbGFibGUgYWdhaW4nLCBXLnJ1bignc2hpcFN3YXBSZWFkeSgpJyk9PT10cnVlKTsKCmNvbnNv'
        'bGUubG9nKCdDeWNsZSBzY2FsaW5nIGFuZCBzaGllbGRzJyk7CnJlc2V0KCk7IFcucnVuKCJwbGF5'
        'ZXIuaHVsbE11bHQ9MS41OyBzaGlwVW5sb2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJv'
        'eWVyKCldKTsKVy5ydW4oInRvZ2dsZVNoaXBNZW51KCk7IHN3YXBTaGlwKCdib3Nla2htZXQnKSIp'
        'OyBvaygnU2VraG1ldCBhdCBjeWNsZSB4MS41OiBodWxsIDIxMCcsIFAoKS5tYXhIcD09PTIxMCAm'
        'JiBQKCkuaHA9PT0yMTApOwpyZXNldCgpOyBXLnJ1bigiZXJhT2ZmPXRydWU7IHNoaXBVbmxvY2tl'
        'ZD0yIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1l'
        'bnUoKTsgc3dhcFNoaXAoJ2ZpaG9ydXMnKSIpOyBvaygnZXJhIHdpdGhvdXQgc2hpZWxkczogc2hp'
        'ZWxkcyBzdGF5IDAnLCBQKCkuc2g9PT0wICYmIFAoKS5tYXhTaD09PTEwMCk7ClcucnVuKCdlcmFP'
        'ZmY9ZmFsc2UnKTsKCmNvbnNvbGUubG9nKCdDYWxsIG1lbnUgYW5kIHN3aXRjaCBtZW51IGV4Y2x1'
        'ZGUgZWFjaCBvdGhlcicpOwpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTI7IGNhbGxNZW51'
        'PXRydWU7IHBhdXNlZD10cnVlIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOwpXLnJ1'
        'bigndG9nZ2xlU2hpcE1lbnUoKScpOyBvaygnb3BlbmluZyB0aGUgc3dpdGNoIGNsb3NlcyB0aGUg'
        'Y2FsbCBtZW51JywgVy5nZXQoJ2NhbGxNZW51Jyk9PT1mYWxzZSAmJiBXLmdldCgnc2hpcE1lbnUn'
        'KT09PXRydWUpOwoKY29uc29sZS5sb2coJ01lbnUgZHJhd2luZyBhbmQgdGFwcycpOwpyZXNldCgp'
        'OyBXLnJ1bigic2hpcFVubG9ja2VkPTMiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7'
        'IFcucnVuKCd0b2dnbGVTaGlwTWVudSgpOyBkcmF3U2hpcE1lbnUoKScpOwpjb25zdCByZWN0cyA9'
        'IFcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycpOwpjb25zdCByb3dPZiA9IChrZXkpPT5XLnJ1bign'
        'd2luZG93Ll9zaGlwUmVjdHMnKS5maW5kKHI9PnIuc2hpcD09PWtleSk7Cm9rKCdlaWdodCByb3dz'
        'IGRyYXduJywgcmVjdHMubGVuZ3RoPT09OCk7Cm9rKCdtZW51IGZpdHMgb24gdGhlIDgwMHg1MDAg'
        'ZmllbGQnLCByZWN0cy5ldmVyeShyPT5yLng+PTAgJiYgci55Pj0wICYmIHIueCtyLnc8PTgwMCAm'
        'JiByLnkrci5oPD01MDApKTsKb2soJ2ZpZ2h0ZXJzIGZpcnN0LCB0aGVuIGJvbWJlcnMnLAogICBy'
        'ZWN0cy5tYXAocj0+ci5zaGlwKS5qb2luKCk9PT0nZml0b3RoLGZpaG9ydXMsZmlzZXJhcGlzLGZp'
        'c2V0aCxmaXRhdXJldCxib29zaXJpcyxib2Jha2hhLGJvc2VraG1ldCcpOwpvaygnZXZlcnkgcm93'
        'IGlzIGZ1bGwgd2lkdGggYW5kIHRoZXkgZG8gbm90IG92ZXJsYXAnLAogICByZWN0cy5ldmVyeShy'
        'PT5yLnc9PT1yZWN0c1swXS53KSAmJgogICByZWN0cy5ldmVyeSgocixpKT0+aT09PTAgfHwgci55'
        'ID49IHJlY3RzW2ktMV0ueStyZWN0c1tpLTFdLmgpKTsKb2soJ2EgbG9ja2VkIHJvdyBpcyB0aGlu'
        'bmVyIHRoYW4gb25lIHRoYXQgY2FuIGJlIHRha2VuJywKICAgcm93T2YoJ2JvYmFraGEnKS5oIDwg'
        'cm93T2YoJ2ZpaG9ydXMnKS5oKTsKb2soJ29ubHkgSG9ydXMgYW5kIE9zaXJpcyBhcmUgdGFwcGFi'
        'bGUnLCByZWN0cy5maWx0ZXIocj0+ci5rZXkpLm1hcChyPT5yLmtleSkuam9pbigpPT09J2ZpaG9y'
        'dXMsYm9vc2lyaXMnKTsKY29uc3QgbG9ja2VkID0gcm93T2YoJ2JvYmFraGEnKTsKVy5ydW4oYHBv'
        'aW50ZXJDb25zdW1lZCh7eDoke2xvY2tlZC54KzV9LHk6JHtsb2NrZWQueSs1fX0pYCk7IG9rKCd0'
        'YXAgb24gbG9ja2VkIEJha2hhIGtlZXBzIHRoZSBtZW51IG9wZW4nLCBXLmdldCgnc2hpcE1lbnUn'
        'KT09PXRydWUgJiYgUCgpLnNoaXA9PT0nZml0b3RoJyk7CmNvbnN0IGhvcnVzID0gcm93T2YoJ2Zp'
        'aG9ydXMnKTsKVy5ydW4oYHBvaW50ZXJDb25zdW1lZCh7eDoke2hvcnVzLngrNX0seToke2hvcnVz'
        'LnkrNX19KWApOyBvaygndGFwIG9uIEhvcnVzIHN3aXRjaGVzJywgUCgpLnNoaXA9PT0nZmlob3J1'
        'cycgJiYgVy5nZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5s'
        'b2NrZWQ9MyIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ3RvZ2dsZVNo'
        'aXBNZW51KCknKTsKVy5ydW4oJ3BvaW50ZXJDb25zdW1lZCh7eDoyLHk6Mn0pJyk7IG9rKCd0YXAg'
        'b3V0c2lkZSBjbG9zZXMgd2l0aG91dCBzd2l0Y2hpbmcnLCBXLmdldCgnc2hpcE1lbnUnKT09PWZh'
        'bHNlICYmIFAoKS5zaGlwPT09J2ZpdG90aCcgJiYgVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpPT09'
        'dHJ1ZSk7Cm9rKCdjYW5jZWxsaW5nIGhvbGRzIHRoZSBwYXVzZSBqdXN0IHRoZSBzYW1lJywgVy5n'
        'ZXQoJ3Jlc3VtZUhvbGQnKT09PXRydWUpOwpXLnJ1bignY2xlYXJSZXN1bWVIb2xkKCknKTsKVy5y'
        'dW4oIndpbmRvdy5fc2hpcEJ0blJlY3Q9e3g6Njk1LHk6NCx3OjIyLGg6MjB9OyBwb2ludGVyQ29u'
        'c3VtZWQoe3g6NzAwLHk6MTB9KSIpOyBvaygndGFwIG9uIHRoZSBiYXIgYnV0dG9uIG9wZW5zIHRo'
        'ZSBtZW51JywgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlKTsKCmNvbnNvbGUubG9nKCdUaGUgcGFu'
        'ZWwgc3dhbGxvd3MgaXRzIG93biBjbGlja3MnKTsKewogIHJlc2V0KCk7IFcucnVuKCJzaGlwVW5s'
        'b2NrZWQ9OCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKICBXLnJ1bigndG9nZ2xl'
        'U2hpcE1lbnUoKScpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKICBjb25zdCBwciA9IFcucnVu'
        'KCd3aW5kb3cuX3NoaXBQYW5lbFJlY3QnKTsKICBvaygndGhlIHBhbmVsIHJlcG9ydHMgaXRzIG91'
        'dGxpbmUnLCBwciAmJiBwci53PjAgJiYgcHIuaD4wKTsKICAvLyBUaGUgaGVhZGVyIGxpbmU6IGlu'
        'c2lkZSB0aGUgcGFuZWwsIG9uIG5vIHJvdyBhdCBhbGwuCiAgVy5ydW4oYHBvaW50ZXJDb25zdW1l'
        'ZCh7eDoke3ByLngrNDB9LHk6JHtwci55KzZ9fSlgKTsKICBvaygnYSBjbGljayBvbiB0aGUgaGVh'
        'ZGVyIGtlZXBzIHRoZSBwYW5lbCBvcGVuJywgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlKTsKICAv'
        'LyBBIGdhcCBiZXR3ZWVuIHR3byByb3dzLgogIGNvbnN0IHJzID0gVy5ydW4oJ3dpbmRvdy5fc2hp'
        'cFJlY3RzJyk7CiAgY29uc3QgZ2FwWSA9IHJzWzBdLnkgKyByc1swXS5oICsgMjsKICBXLnJ1bihg'
        'cG9pbnRlckNvbnN1bWVkKHt4OiR7cnNbMF0ueCs0MH0seToke2dhcFl9fSlgKTsKICBvaygnYSBj'
        'bGljayBpbiB0aGUgZ2FwIGJldHdlZW4gcm93cyBrZWVwcyBpdCBvcGVuIHRvbycsIFcuZ2V0KCdz'
        'aGlwTWVudScpPT09dHJ1ZSk7CiAgLy8gVGhlIGZvb3Rlci4KICBXLnJ1bihgcG9pbnRlckNvbnN1'
        'bWVkKHt4OiR7cHIueCtwci53LzJ9LHk6JHtwci55K3ByLmgtNn19KWApOwogIG9rKCdhbmQgb25l'
        'IG9uIHRoZSBmb290ZXInLCBXLmdldCgnc2hpcE1lbnUnKT09PXRydWUpOwogIG9rKCdub25lIG9m'
        'IHRoZW0gc3dpdGNoZWQgdGhlIHNoaXAnLCBQKCkuc2hpcD09PSdmaXRvdGgnKTsKICAvLyBPdXRz'
        'aWRlIHRoZSBvdXRsaW5lIGlzIHN0aWxsIG91dHNpZGUuCiAgVy5ydW4oYHBvaW50ZXJDb25zdW1l'
        'ZCh7eDoke3ByLngtMTJ9LHk6JHtwci55K3ByLmgvMn19KWApOwogIG9rKCdhIGNsaWNrIGJlc2lk'
        'ZSB0aGUgcGFuZWwgY2xvc2VzIGl0JywgVy5nZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7Cn0KCmNv'
        'bnNvbGUubG9nKCdLZXlib2FyZCcpOwpjb25zdCBrZXkgPSAoY29kZSk9PlcucnVuKGBvbktleSh7'
        'Y29kZTonJHtjb2RlfScsIHByZXZlbnREZWZhdWx0KCl7fX0pYCk7CnJlc2V0KCk7IFcucnVuKCJz'
        'aGlwVW5sb2NrZWQ9NCIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKa2V5KCdLZXlW'
        'Jyk7IG9rKCdWIG9wZW5zJywgVy5nZXQoJ3NoaXBNZW51Jyk9PT10cnVlKTsKLy8gRm91ciBodWxs'
        'cyBvcGVuOiByb3N0ZXIgMCB0byAzLiBUaGUgZGlnaXRzIGZvbGxvdyB0aGUgcGFuZWwsIHNvIDQg'
        'aXMgdGhlCi8vIFNldGgsIHdoaWNoIGlzIHN0aWxsIGxvY2tlZCwgYW5kIDYgaXMgdGhlIGZpcnN0'
        'IGJvbWJlci4Ka2V5KCdEaWdpdDQnKTsgb2soJzQgKHRoZSBTZXRoLCBub3QgdW5sb2NrZWQgeWV0'
        'KSBkb2VzIG5vdGhpbmcnLAogICAgICAgICAgICAgICAgICBXLmdldCgnc2hpcE1lbnUnKT09PXRy'
        'dWUgJiYgUCgpLnNoaXA9PT0nZml0b3RoJyk7CmtleSgnRGlnaXQ2Jyk7IG9rKCc2IHRha2VzIHRo'
        'ZSBPc2lyaXMsIGZpcnN0IHJvdyBvZiB0aGUgYm9tYmVycycsCiAgICAgICAgICAgICAgICAgIFAo'
        'KS5zaGlwPT09J2Jvb3NpcmlzJyAmJiBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKcmVzZXQo'
        'KTsgVy5ydW4oInNoaXBVbmxvY2tlZD00Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0p'
        'OyBrZXkoJ0tleVYnKTsKa2V5KCdEaWdpdDMnKTsgb2soJzMgdGFrZXMgdGhlIFNlcmFwaXMsIHRo'
        'aXJkIHJvdyBkb3duJywKICAgICAgICAgICAgICAgICAgUCgpLnNoaXA9PT0nZmlzZXJhcGlzJyAm'
        'JiBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tl'
        'ZD00Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBrZXkoJ0tleVYnKTsga2V5KCdF'
        'c2NhcGUnKTsKb2soJ0VzY2FwZSBjbG9zZXMnLCBXLmdldCgnc2hpcE1lbnUnKT09PWZhbHNlKTsK'
        'b2soJ2FuZCBob2xkcyB0aGUgcGF1c2UsIGxpa2UgZXZlcnkgb3RoZXIgd2F5IG9mIGxlYXZpbmcg'
        'YSBwYW5lbCcsCiAgIFcuZ2V0KCdwYXVzZWQnKT09PXRydWUgJiYgVy5nZXQoJ3Jlc3VtZUhvbGQn'
        'KT09PXRydWUpOwpXLnJ1bignY2xlYXJSZXN1bWVIb2xkKCknKTsKb2soJ2FmdGVyIHRoZSB0YXAg'
        'dGhlIGdhbWUgcnVucyBhZ2FpbicsIFcuZ2V0KCdwYXVzZWQnKT09PWZhbHNlKTsKcmVzZXQoKTsg'
        'a2V5KCdLZXlWJyk7IG9rKCdWIHdpdGhvdXQgYSBkZXN0cm95ZXIgZG9lcyBub3RoaW5nJywgVy5n'
        'ZXQoJ3NoaXBNZW51Jyk9PT1mYWxzZSk7Cgpjb25zb2xlLmxvZygnUmVzdGFydCBndWFyZCcpOwpX'
        'LnJ1bigibGF1bmNoR2FtZT1mdW5jdGlvbigpe2xhdW5jaGVkKyt9Iik7Ci8vIFRoZSB0aXRsZSBh'
        'bmQgdGhlIGdhbWUgb3ZlciBzY3JlZW4gYm90aCBnbyB0aHJvdWdoIHRvVGl0bGVPckxhdW5jaCBu'
        'b3csCi8vIHNvIHRoYXQgaXMgd2hhdCBoYXMgdG8gYmUgaW4gcGxhY2UgZm9yIHRoZSByZXN0YXJ0'
        'IGd1YXJkIHRvIGJlIHRlc3RlZC4KVy5ydW4oInRvVGl0bGVPckxhdW5jaD1mdW5jdGlvbigpeyBp'
        'ZihHUz09PSdnYW1lb3ZlcicpeyBHUz0ndGl0bGUnOyByZXR1cm47IH0gbGF1bmNoR2FtZSgpOyB9'
        'Iik7CmNvbnN0IGRvd24gPSAoKT0+Vy5ydW4oIm9uRG93bih7YnV0dG9uOjAsIGNsaWVudFg6NDAw'
        'LCBjbGllbnRZOjMwMH0pIik7ClcucnVuKCJHUz0ndGl0bGUnOyBsYXVuY2hlZD0wIik7IGRvd24o'
        'KTsgb2soJ3RhcCBvbiB0aXRsZSBzdGFydHMgYXQgb25jZScsIFcuZ2V0KCdsYXVuY2hlZCcpPT09'
        'MSk7ClcucnVuKCJHUz0nZ2FtZW92ZXInOyBnYW1lT3ZlckF0PXBlcmZvcm1hbmNlLm5vdygpOyBs'
        'YXVuY2hlZD0wIik7IGRvd24oKTsgb2soJ3RhcCByaWdodCBhZnRlciBkeWluZyBkb2VzIG5vdCBy'
        'ZXN0YXJ0JywgVy5nZXQoJ2xhdW5jaGVkJyk9PT0wKTsKVy5ydW4oImdhbWVPdmVyQXQ9cGVyZm9y'
        'bWFuY2Uubm93KCktMjAwMCIpOyBkb3duKCk7Cm9rKCd0YXAgYWZ0ZXIgMiBzIGdvZXMgYmFjayB0'
        'byB0aGUgdGl0bGUsIG5vdCBpbnRvIHRoZSBuZXh0IHJ1bicsCiAgIFcuZ2V0KCdsYXVuY2hlZCcp'
        'PT09MCAmJiBXLmdldCgnR1MnKT09PSd0aXRsZScpOwoKCmNvbnNvbGUubG9nKCdIYW5nYXJzIGJ5'
        'IGZhY3Rpb24nKTsKY29uc3QgY29sb3NzdXMgPSAobyk9Pk9iamVjdC5hc3NpZ24oe2ltZzonc2Rj'
        'b2xvc3N1cycsIGNvbG9zc3VzOnRydWUsIHNtYWxsOmZhbHNlLCBkZWFkOmZhbHNlLCB3YXJwT3V0'
        'OmZhbHNlfSwgb3x8e30pOwpvaygnaHVsbCBmYWN0aW9uIGNvbWVzIGZyb20gdGhlIGtleScsIFcu'
        'cnVuKCJodWxsRmFjKCdkZWhhdHNoZXBzdXQnKSIpPT09J3Zhc3VkYW4nCiAgICYmIFcucnVuKCJo'
        'dWxsRmFjKCdkZW9yaW9ucmlnaHQnKSIpPT09J3RlcnJhbicgJiYgVy5ydW4oImh1bGxGYWMoJ3Nk'
        'Y29sb3NzdXMnKSIpPT09J2d0dmEnKTsKb2soJ2EgZGVmZWN0ZWQgSGFtbWVyIG9mIExpZ2h0IFR5'
        'cGhvbiBzdGlsbCBjb3VudHMgYXMgVmFzdWRhbicsCiAgIHJlYWR5KCgpPT5XLnNldCgnYWxsaWVz'
        'JyxbZGVzdHJveWVyKHtpbWc6J2RldHlwaG9uJywgZmFjdGlvbjonaG9sJ30pXSkpPT09dHJ1ZSk7'
        'Cm9rKCdhIHJlbmVnYWRlIEhhdHNoZXBzdXQgdG9vJywKICAgcmVhZHkoKCk9Plcuc2V0KCdhbGxp'
        'ZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVoYXRzaGVwc3V0JywgZmFjdGlvbjoncmVuZWdhZGUnfSld'
        'KSk9PT10cnVlKTsKb2soJ1RlcnJhbiBPcmlvbiBvbmx5OiBub3QgcmVhZHknLCByZWFkeSgoKT0+'
        'Vy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7aW1nOidkZW9yaW9ucmlnaHQnfSldKSk9PT1mYWxz'
        'ZSk7Cm9rKCdUZXJyYW4gSGVjYXRlIG9ubHk6IG5vdCByZWFkeScsIHJlYWR5KCgpPT5XLnNldCgn'
        'YWxsaWVzJyxbZGVzdHJveWVyKHtpbWc6J2RlaGVjYXRlJ30pXSkpPT09ZmFsc2UpOwpvaygnT3Jp'
        'b24gcGx1cyBUeXBob246IHJlYWR5LCB0aGUgbGlzdHMgYWRkIHVwJywKICAgcmVhZHkoKCk9Plcu'
        'c2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVvcmlvbnJpZ2h0J30pLCBkZXN0cm95ZXIo'
        'e2ltZzonZGV0eXBob24nfSldKSk9PT10cnVlKTsKb2soJ3Vua25vd24gY2FwaXRhbCBodWxsOiBu'
        'b3QgcmVhZHknLCByZWFkeSgoKT0+Vy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcih7aW1nOidkZWRl'
        'bW9uJ30pXSkpPT09ZmFsc2UpOwoKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcu'
        'c2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVvcmlvbnJpZ2h0J30pXSk7Cm9rKCdWYXN1'
        'ZGFuIGh1bGwgbm90IG9mZmVyZWQgYnkgYSBUZXJyYW4gaGFuZ2FyJywgVy5ydW4oInNoaXBPZmZl'
        'cmVkKCdmaWhvcnVzJykiKT09PWZhbHNlKTsKVy5ydW4oInNoaXBNZW51PXRydWU7IHN3YXBTaGlw'
        'KCdmaWhvcnVzJykiKTsKb2soJ2FuZCBhIGZvcmNlZCBzd2l0Y2ggaXMgcmVmdXNlZCcsIFAoKS5z'
        'aGlwPT09J2ZpdG90aCcgJiYgVy5nZXQoJ3NoaXBTd2FwV2F2ZScpPT09LTEpOwpXLnNldCgnYWxs'
        'aWVzJyxbY29sb3NzdXMoKV0pOwpvaygndGhlIENvbG9zc3VzIG9mZmVycyB0aGUgVmFzdWRhbiBo'
        'dWxsJywgVy5ydW4oInNoaXBPZmZlcmVkKCdmaWhvcnVzJykiKT09PXRydWUpOwoKcmVzZXQoKTsg'
        'Vy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzon'
        'ZGVvcmlvbnJpZ2h0J30pXSk7ClcucnVuKCd0b2dnbGVTaGlwTWVudSgpJyk7IG9rKCdUZXJyYW4g'
        'aGFuZ2FyIG9ubHk6IHRoZSBtZW51IHN0YXlzIHNodXQnLCBXLmdldCgnc2hpcE1lbnUnKT09PWZh'
        'bHNlKTsKVy5ydW4oInNoaXBNZW51PXRydWU7IGRyYXdTaGlwTWVudSgpIik7Cm9rKCdubyBjZWxs'
        'IGlzIHRhcHBhYmxlIGluIHRoYXQgc3RhdGUnLCBXLnJ1bignd2luZG93Ll9zaGlwUmVjdHMnKS5l'
        'dmVyeShyPT4hci5rZXkpKTsKCmNvbnNvbGUubG9nKCdDb2xvc3N1cyBsaWZ0cyB0aGUgb25jZSBw'
        'ZXIgd2F2ZSBsaW1pdCcpOwpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTMiKTsgVy5zZXQo'
        'J2FsbGllcycsW2Rlc3Ryb3llcigpXSk7ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBzd2FwU2hp'
        'cCgnZmlob3J1cycpIik7Cm9rKCdmaXJzdCBzd2l0Y2ggb2YgdGhlIHdhdmUgcmVmaXRzJywgUCgp'
        'LnNoaXA9PT0nZmlob3J1cycgJiYgUCgpLmhwPT09ODAgJiYgUCgpLnNoPT09MTAwICYmIFAoKS5z'
        'ZWNBbW1vPT09MjApOwpvaygnbm8gQ29sb3NzdXM6IHNwZW50IGZvciB0aGlzIHdhdmUnLCBXLnJ1'
        'bignc2hpcFN3YXBSZWFkeSgpJyk9PT1mYWxzZSk7Clcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIo'
        'KSwgY29sb3NzdXMoKV0pOwpvaygnQ29sb3NzdXMgYXJyaXZlczogYXZhaWxhYmxlIGFnYWluIGlu'
        'IHRoZSBzYW1lIHdhdmUnLCBXLnJ1bignc2hpcFN3YXBSZWFkeSgpJyk9PT10cnVlKTsKVy5ydW4o'
        'InBsYXllci5ocD00MDsgcGxheWVyLnNoPTUwOyBwbGF5ZXIuc2VjQW1tbz0xMCIpOwpXLnJ1bigi'
        'dG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAoJ2Jvb3NpcmlzJykiKTsKb2soJ3NlY29uZCBzd2l0'
        'Y2ggaGFwcGVucycsIFAoKS5zaGlwPT09J2Jvb3NpcmlzJyk7Cm9rKCdodWxsIGNhcnJpZXMgb3Zl'
        'ciBhcyBhIGZyYWN0aW9uLCA0MC84MCBvZiAxNDAgPSA3MCcsIFAoKS5ocD09PTcwKTsKb2soJ3No'
        'aWVsZHMgY2Fycnkgb3ZlciwgNTAvMTAwIG9mIDEwMCA9IDUwJywgUCgpLnNoPT09NTApOwpvaygn'
        'YW1tbyBjYXJyaWVzIG92ZXIsIDEwLzIwIG9mIDEwIGJvbWJzID0gNScsIFAoKS5zZWNBbW1vPT09'
        'NSk7Cm9rKCdubyByZWZpdDogbm90IGZ1bGwnLCBQKCkuaHA8UCgpLm1heEhwICYmIFAoKS5zZWNB'
        'bW1vPFAoKS5zZWNNYXgpOwoKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0zIik7IFcuc2V0'
        'KCdhbGxpZXMnLFtkZXN0cm95ZXIoKSwgY29sb3NzdXMoKV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1l'
        'bnUoKTsgc3dhcFNoaXAoJ2ZpaG9ydXMnKSIpOwpvaygnd2l0aCB0aGUgQ29sb3NzdXMgdGhlcmUg'
        'dGhlIGZpcnN0IHN3aXRjaCBzdGlsbCByZWZpdHMnLCBQKCkuaHA9PT04MCAmJiBQKCkuc2VjQW1t'
        'bz09PTIwKTsKVy5ydW4oInBsYXllci5ocD0xIik7ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBz'
        'd2FwU2hpcCgnYm9vc2lyaXMnKSIpOwpvaygnYSBuZWFybHkgZGVhZCBodWxsIHN0YXlzIGFsaXZl'
        'IGFmdGVyIGNhcnJ5aW5nIG92ZXInLCBQKCkuaHA+PTEgJiYgUCgpLmhwPD0zKTsKCnJlc2V0KCk7'
        'IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCksIGNv'
        'bG9zc3VzKHtkZWFkOnRydWV9KV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAo'
        'J2ZpaG9ydXMnKSIpOwpvaygnZGVhZCBDb2xvc3N1cyBncmFudHMgbm90aGluZycsIFcucnVuKCdz'
        'aGlwU3dhcFJlYWR5KCknKT09PWZhbHNlKTsKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD0z'
        'Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKSwgY29sb3NzdXMoe3dhcnBPdXQ6dHJ1ZX0p'
        'XSk7ClcucnVuKCJ0b2dnbGVTaGlwTWVudSgpOyBzd2FwU2hpcCgnZmlob3J1cycpIik7Cm9rKCdD'
        'b2xvc3N1cyB3YXJwaW5nIG91dCBncmFudHMgbm90aGluZycsIFcucnVuKCdzaGlwU3dhcFJlYWR5'
        'KCknKT09PWZhbHNlKTsKCnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBXLnNldCgn'
        'YWxsaWVzJyxbY29sb3NzdXMoKV0pOwpXLnJ1bigidG9nZ2xlU2hpcE1lbnUoKTsgc3dhcFNoaXAo'
        'J2ZpaG9ydXMnKSIpOyBXLnJ1bigicGxheWVyLmhwPTIwIik7ClcucnVuKCJ0b2dnbGVTaGlwTWVu'
        'dSgpOyBzd2FwU2hpcCgnZml0b3RoJykiKTsKb2soJ2JhY2sgb250byB0aGUgc3RhcnQgaHVsbCBh'
        'dCB0aGUgQ29sb3NzdXMsIDIwLzgwIG9mIDEwMCA9IDI1JywgUCgpLnNoaXA9PT0nZml0b3RoJyAm'
        'JiBQKCkuaHA9PT0yNSk7ClcucnVuKCd3YXZlPTInKTsKb2soJ25ldyB3YXZlIHdpdGggdGhlIENv'
        'bG9zc3VzIHN0aWxsIHRoZXJlOiByZWZpdHMgYWdhaW4nLCBXLnJ1bignc2hpcFN3YXBSZWFkeSgp'
        'Jyk9PT10cnVlKTsKVy5ydW4oInRvZ2dsZVNoaXBNZW51KCk7IHN3YXBTaGlwKCdmaWhvcnVzJyki'
        'KTsgb2soJ2FuZCBpdCBpcyBhIGZ1bGwgaHVsbCcsIFAoKS5ocD09PTgwKTsKCmNvbnNvbGUubG9n'
        'KCdDeWNsZXM6IGVhY2ggYnJpbmdzIGl0cyBvd24gZmxlZXQnKTsKewogIGNvbnN0IGhvbCA9IFcu'
        'cnVuKCdjeWNsZUF0KDEpJyksIG50ZiA9IFcucnVuKCdjeWNsZUF0KDMxKScpOwogIG9rKCd3YXZl'
        'cyAxIHRvIDMwIGFyZSB0aGUgSGFtbWVyIG9mIExpZ2h0IGN5Y2xlJywgVy5ydW4oJ2N5Y2xlQXQo'
        'MzApJyk9PT1ob2wgJiYgaG9sLmZpcnN0PT09MSk7CiAgb2soJ3dhdmUgMzEgb3BlbnMgdGhlIE5U'
        'RiBjeWNsZSwgYW5kIGl0IGhvbGRzIGFmdGVyIHRoYXQnLCBudGYuZmlyc3Q9PT0zMSAmJiBXLnJ1'
        'bignY3ljbGVBdCg1OSknKT09PW50ZiAmJiBXLnJ1bignY3ljbGVBdCgxNDApJyk9PT1udGYpOwog'
        'IHJlc2V0KCk7CiAgVy5ydW4oInNjb3JlPTk1MDAwOyBlbnRlckN5Y2xlKGN5Y2xlQXQoMzEpKSIp'
        'OwogIG9rKCdlbnRlcmluZyBpdCBwdXRzIHRoZSBwbGF5ZXIgaW4gYSBNeXJtaWRvbiwgZnJlc2gn'
        'LCBQKCkuc2hpcD09PSdmaW15cm1pZG9uJyAmJiBQKCkuaHA9PT1QKCkubWF4SHApOwogIG9rKCd0'
        'aGUgcm9zdGVyIGlzIHRoZSBUZXJyYW4gb25lLCBlaWdodCBodWxscycsCiAgICAgVy5ydW4oJ1BM'
        'QVlFUl9TSElQUy5sZW5ndGgnKT09PTggJiYgVy5ydW4oIlBMQVlFUl9TSElQUy5ldmVyeShzPT5z'
        'LmZhYz09PSd0ZXJyYW4nKSIpKTsKICBvaygnaW4gdGhlIGFncmVlZCBvcmRlcicsCiAgICAgVy5y'
        'dW4oIlBMQVlFUl9TSElQUy5tYXAocz0+cy5rZXkpLmpvaW4oKSIpPT09J2ZpbXlybWlkb24sZmlo'
        'ZXJjLGJvYXJ0ZW1pcyxmaWhlcmNtazIsYm9tZWR1c2EsZmllcmlueWVzLGJvdXJzYSxmaWFyZXMn'
        'KTsKICBvaygnb25seSB0aGUgZmlyc3QgaHVsbCBpcyBvcGVuJywgVy5nZXQoJ3NoaXBVbmxvY2tl'
        'ZCcpPT09MSk7CiAgVy5ydW4oInNjb3JlPTk1MDAwKzM5OTk7IHRpY2tTaGlwVW5sb2NrcygpIik7'
        'CiAgb2soJ3RoZSBwb2ludHMgYnJvdWdodCBpbnRvIHRoZSBjeWNsZSBkbyBub3QgY291bnQnLCBX'
        'LmdldCgnc2hpcFVubG9ja2VkJyk9PT0xKTsKICBXLnJ1bigic2NvcmU9OTUwMDArNDAwMDsgdGlj'
        'a1NoaXBVbmxvY2tzKCkiKTsKICBvaygnNDAwMCBwb2ludHMgc2NvcmVkIElOIHRoZSBjeWNsZSBv'
        'cGVuIHRoZSBIZXJjdWxlcycsIFcuZ2V0KCdzaGlwVW5sb2NrZWQnKT09PTIgJiYgL0hFUkNVTEVT'
        'Ly50ZXN0KFcuZ2V0KCdOT1RJQ0VfTE9HJykuc2xpY2UoLTEpWzBdLnR4dCkpOwogIG9rKCd0aGUg'
        'VGVycmFuIHN1cHBvcnQgY29sdW1uIGFuc3dlcnMsIHRoZSBWYXN1ZGFuIG9uZSBkb2VzIG5vdCcs'
        'CiAgICAgVy5ydW4oJ0FMTFlfRkFDX09OLnRlcnJhbicpPT09dHJ1ZSAmJiBXLnJ1bignQUxMWV9G'
        'QUNfT04udmFzdWRhbicpPT09ZmFsc2UpOwogIC8vIFRoZSBoYW5nYXIgZm9sbG93cyB0aGUgaHVs'
        'bCwgc28gdGhlIFRlcnJhbiByb3N0ZXIgbmVlZHMgYSBUZXJyYW4gZGVzdHJveWVyLgogIFcuc2V0'
        'KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVvcmlvbnJpZ2h0J30pXSk7CiAgb2soJ2EgVGVy'
        'cmFuIGRlc3Ryb3llciBvZmZlcnMgdGhlIEhlcmN1bGVzJywgVy5ydW4oInNoaXBPZmZlcmVkKCdm'
        'aWhlcmMnKSIpPT09dHJ1ZSAmJiBXLnJ1bignc2hpcFN3YXBSZWFkeSgpJyk9PT10cnVlKTsKICBX'
        'LnNldCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsKICBvaygnYSBWYXN1ZGFuIG9uZSBkb2VzIG5v'
        'dCcsIFcucnVuKCJzaGlwT2ZmZXJlZCgnZmloZXJjJykiKT09PWZhbHNlICYmIFcucnVuKCdzaGlw'
        'U3dhcFJlYWR5KCknKT09PWZhbHNlKTsKICBXLnJ1bigiZW50ZXJDeWNsZShjeWNsZUF0KDEpKSIp'
        'OwogIG9rKCdhbmQgYmFjazogdGhlIFZhc3VkYW4gcm9zdGVyIGFuZCBjb2x1bW4nLCBQKCkuc2hp'
        'cD09PSdmaXRvdGgnICYmCiAgICAgVy5ydW4oJ0FMTFlfRkFDX09OLnRlcnJhbicpPT09ZmFsc2Ug'
        'JiYgVy5ydW4oJ0FMTFlfRkFDX09OLnZhc3VkYW4nKT09PXRydWUpOwp9Cm9rKCd0aGUgcnVuIHN0'
        'YXJ0cyBpbiB0aGUgY3ljbGUgb2YgaXRzIGZpcnN0IHdhdmUnLAogICAvZWxzZSBlbnRlckN5Y2xl'
        'XChjeWNsZUF0XCh3YXZlXCsxXClcKTsvLnRlc3QoZm4oJ2xhdW5jaEdhbWUnKSkpOwpvaygnY3Jv'
        'c3NpbmcgaW50byBhIG5ldyBjeWNsZSBoYW5kcyBvdmVyIHRoZSBmbGVldCcsCiAgIC9pZlwoX2Mh'
        'PT1jeWNsZU5vd1wpIGVudGVyQ3ljbGVcKF9jXCk7Ly50ZXN0KGZuKCduZXh0V2F2ZScpKSk7Cm9r'
        'KCc/bT0gc3RhcnRzIHRoZSBydW4gYXQgdGhhdCB3YXZlIGluc3RlYWQgb2YgcmVwZWF0aW5nIGl0'
        'JywKICAgL1NDUklQVF9PTkVcP1NDUklQVF9PTkUtMTowLy50ZXN0KGZuKCdsYXVuY2hHYW1lJykp'
        'ICYmICEvU0NSSVBUX09ORSBcPyBTQ1JJUFRfT05FIDogbi8udGVzdChzcmMpKTsKCmNvbnNvbGUu'
        'bG9nKCdBIG1pc3Npb24gY2FuIGxlbmQgYSBodWxsJyk7CnsKICByZXNldCgpOyBXLnJ1bigic2Nv'
        'cmU9OTUwMDA7IGVudGVyQ3ljbGUoY3ljbGVBdCgzMSkpOyBzaGlwVW5sb2NrZWQ9OCIpOwogIFcu'
        'c2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoe2ltZzonZGVvcmlvbnJpZ2h0J30pXSk7CiAgb2soJ2Jl'
        'Zm9yZTogYSBUZXJyYW4gZGVzdHJveWVyIG9mZmVycyBhIHN3aXRjaCcsIFcucnVuKCdzaGlwU3dh'
        'cFJlYWR5KCknKT09PXRydWUpOwogIFcucnVuKCJmb3JjZVNoaXAoJ2ZpcGVnYXN1cycpIik7CiAg'
        'b2soJ3RoZSBwbGF5ZXIgZmxpZXMgdGhlIGxlbnQgaHVsbCcsIFAoKS5zaGlwPT09J2ZpcGVnYXN1'
        'cycpOwogIG9rKCd3aXRoIGl0cyBvd24gZmlndXJlcywgbm90IHRoZSBmaWdodGVyIGRlZmF1bHRz'
        'JywKICAgICBQKCkubWF4U2g9PT04MCAmJiBQKCkuc3BkPT09My42ICYmIFcucnVuKCJzaGlwU3Rh'
        'dHMoJ2ZpcGVnYXN1cycpLm5hbWUiKT09PSdHVEYgUGVnYXN1cycpOwogIG9rKCdhbmQgdGhlIGhh'
        'bmdhciBpcyBjbG9zZWQgZm9yIHRoaXMgbWlzc2lvbicsIFcucnVuKCdzaGlwU3dhcFJlYWR5KCkn'
        'KT09PWZhbHNlKTsKICBvaygnaXQgaXMgYW5ub3VuY2VkIGluIHRoZSBjb2x1bW4nLCBXLmdldCgn'
        'Tk9USUNFX0xPRycpLnNvbWUobj0+L1BFR0FTVVMgQVNTSUdORUQvLnRlc3Qobi50eHQpKSk7CiAg'
        'Vy5ydW4oInBsYXllci5ocD0xMDsgcmVsZWFzZVNoaXAoKSIpOwogIG9rKCd0aGUgbmV4dCB3YXZl'
        'IGhhbmRzIHRoZSBvd24gaHVsbCBiYWNrLCByZWZpdHRlZCcsIFAoKS5zaGlwPT09J2ZpbXlybWlk'
        'b24nICYmIFAoKS5ocD09PVAoKS5tYXhIcCk7CiAgb2soJ2FuZCB0aGUgaGFuZ2FyIG9wZW5zIGFn'
        'YWluJywgVy5ydW4oJ3NoaXBTd2FwUmVhZHkoKScpPT09dHJ1ZSk7CiAgVy5ydW4oInJlbGVhc2VT'
        'aGlwKCkiKTsKICBvaygncmVsZWFzaW5nIHR3aWNlIGNoYW5nZXMgbm90aGluZycsIFAoKS5zaGlw'
        'PT09J2ZpbXlybWlkb24nKTsKICBXLnJ1bigiZW50ZXJDeWNsZShjeWNsZUF0KDEpKSIpOyAgIC8v'
        'IHRoZSB0ZXN0cyBiZWxvdyBleHBlY3QgdGhlIGZpcnN0IGZsZWV0Cn0Kb2soJ3RoZSBuZXh0IHdh'
        'dmUgcmVsZWFzZXMgYSBsZW50IGh1bGwgYmVmb3JlIGFueXRoaW5nIGVsc2UnLAogICAvcmVsZWFz'
        'ZVNoaXBcKFwpO1tcc1xTXXswLDIwMH1lbnRlckN5Y2xlLy50ZXN0KGZuKCduZXh0V2F2ZScpKSk7'
        'Cgpjb25zb2xlLmxvZygnU3VwcG9ydCBjYWxscyBieSBmYWN0aW9uJyk7Cm9rKCd0aGUgVGVycmFu'
        'IGNvbHVtbiBpcyBvZmYgaW4gdGhpcyBjeWNsZScsIHNyYy5pbmNsdWRlcygiY29uc3QgQUxMWV9G'
        'QUNfT04gPSB7dGVycmFuOmZhbHNlLCB2YXN1ZGFuOnRydWUsIGd0dmE6dHJ1ZX07IikpOwpvaygn'
        'dGhlIGNhbGwgaXMgZ2F0ZWQgaW5zaWRlIGNhbGxBbGx5LCBub3Qgb25seSBpbiB0aGUgbWVudScs'
        'CiAgIC9mdW5jdGlvbiBjYWxsQWxseVwoaWRcKVx7W1xzXFNdezAsNDAwfWFsbHlGYWNPblwoY2Rl'
        'ZlwuZmFjXCkvLnRlc3Qoc3JjKSk7Cm9rKCd0aGUgbWVudSBubyBsb25nZXIgdXNlcyB0aGUgZml4'
        'ZWQgdHdvIGNvbHVtbiBzcGxpdCcsICFzcmMuaW5jbHVkZXMoJ0FMTFlfVEVSX04/MDoxJykpOwpv'
        'aygndGhlIENvbG9zc3VzIGlzIGEgR1RWQSBzaGlwIG5vdycsIC9jb2xvc3N1czpccypce2Nsczon'
        'ZGVzdHJveWVyJywgZmFjOidndHZhJy8udGVzdChzcmMpKTsKCmNvbnNvbGUubG9nKCdIdWxsIHBp'
        'Y3R1cmVzIGluIHRoZWlyIG93biBjZWxsJyk7CmNvbnN0IElNRyA9ICh3LGgpPT4oe3dpZHRoOncs'
        'IGhlaWdodDpofSk7CmNvbnN0IEFMTF9JTUdTID0ge2ZpdG90aDpJTUcoMTIwLDkwKSwgZmlob3J1'
        'czpJTUcoMTIwLDkwKSwgYm9vc2lyaXM6SU1HKDE1MCwxMTApLAogICAgICAgICAgICAgICAgICBm'
        'aXNlcmFwaXM6SU1HKDEyMCw5MCksIGZpc2V0aDpJTUcoMTIwLDkwKSwgYm9iYWtoYTpJTUcoMTUw'
        'LDExMCksCiAgICAgICAgICAgICAgICAgIGZpdGF1cmV0OklNRygxMjAsOTApLCBib3Nla2htZXQ6'
        'SU1HKDE1MCwxMTApfTsKY29uc3QgUElDVyA9IFcucnVuKCdIR19QSUNfVycpLCBQSUNIID0gVy5y'
        'dW4oJ0hHX1JPVycpLTY7CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9OCIpOyBXLnNldCgn'
        'YWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsKVy5zZXQo'
        'J0lNR1MnLCB7fSk7CkNMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKb2soJ25vdGhpbmcg'
        'bG9hZGVkIHlldDogbm8gcGljdHVyZSwgbm8gY3Jhc2gsIHJvd3Mgc3RpbGwgdGhlcmUnLAogICBk'
        'cmF3cygpLmxlbmd0aD09PTAgJiYgVy5ydW4oJ3dpbmRvdy5fc2hpcFJlY3RzJykubGVuZ3RoPT09'
        'OCk7Clcuc2V0KCdJTUdTJywgQUxMX0lNR1MpOwpDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgp'
        'Jyk7Cm9rKCdvbmUgaHVsbCBkcmF3biBwZXIgb3BlbiByb3cnLCBkcmF3cygpLmxlbmd0aD09PTgp'
        'OwovLyBUaGUgZ2xvc3Mgb24gZWFjaCBwbGF0ZSBjbGlwcyBhcyB3ZWxsLCBzbyB0aGlzIGNvdW50'
        'cyBhdCBsZWFzdCBvbmUgY2xpcAovLyBwZXIgcGljdHVyZSByYXRoZXIgdGhhbiBleGFjdGx5IG9u'
        'ZSBpbiB0b3RhbC4Kb2soJ2VhY2ggb25lIGNsaXBwZWQgdG8gaXRzIG93biBjZWxsIGZpcnN0Jywg'
        'Y2xpcHMoKS5sZW5ndGg+PTgpOwpvaygnZWFjaCBvbmUgZml0cyBpbnNpZGUgdGhlIHBpY3R1cmUg'
        'Y2VsbCcsCiAgIGRyYXdzKCkuZXZlcnkoZD0+ZC5hcmdzWzNdPD1QSUNXLTUgJiYgZC5hcmdzWzRd'
        'PD1QSUNILTUgJiYgZC5hcmdzWzNdPjAgJiYgZC5hcmdzWzRdPjApKTsKb2soJ2FzcGVjdCByYXRp'
        'byBrZXB0JywgZHJhd3MoKS5ldmVyeShkPT5NYXRoLmFicygoZC5hcmdzWzNdL2QuYXJnc1s0XSkg'
        'LSAoMTIwLzkwKSk8MC4wMQogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHx8'
        'IE1hdGguYWJzKChkLmFyZ3NbM10vZC5hcmdzWzRdKSAtICgxNTAvMTEwKSk8MC4wMSkpOwpvaygn'
        'c2F2ZSBhbmQgcmVzdG9yZSBzdGF5IGJhbGFuY2VkLCBubyBsZWFraW5nIGNsaXAgb3IgYWxwaGEn'
        'LCBiYWxhbmNlZCgpKTsKb2soJ2EgcGljdHVyZSBpcyBhIHBpY3R1cmUgbm93LCBub3QgYSB3YXRl'
        'cm1hcmsnLCBhbHBoYXMoKS5ldmVyeShhPT5hPjAuOSAmJiBhPD0xKSk7CnsKICAvLyBUaHJlZSBv'
        'cGVuLCBmaXZlIGxvY2tlZDogYSBsb2NrZWQgaHVsbCBoYXMgbm8gcm93IHRhbGwgZW5vdWdoIGZv'
        'ciBhCiAgLy8gcGljdHVyZSwgc28gaXQgZ2V0cyBub25lIGF0IGFsbC4KICByZXNldCgpOyBXLnJ1'
        'bigic2hpcFVubG9ja2VkPTMiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7IFcucnVu'
        'KCd0b2dnbGVTaGlwTWVudSgpJyk7CiAgVy5zZXQoJ0lNR1MnLCBBTExfSU1HUyk7IENMUigpOyBX'
        'LnJ1bignZHJhd1NoaXBNZW51KCknKTsKICBvaygnYSBsb2NrZWQgaHVsbCBzaG93cyBubyBwaWN0'
        'dXJlJywgZHJhd3MoKS5sZW5ndGg9PT0zKTsKfQpyZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2Vk'
        'PTgiKTsgVy5zZXQoJ2FsbGllcycsW2Rlc3Ryb3llcigpXSk7IFcucnVuKCd0b2dnbGVTaGlwTWVu'
        'dSgpJyk7Clcuc2V0KCdJTUdTJywge2ZpdG90aDpJTUcoMCwwKX0pOwpDTFIoKTsgVy5ydW4oJ2Ry'
        'YXdTaGlwTWVudSgpJyk7Cm9rKCdhIHplcm8gc2l6ZWQgc3ByaXRlIGlzIHNraXBwZWQgaW5zdGVh'
        'ZCBvZiBkaXZpZGluZyBieSB6ZXJvJywgZHJhd3MoKS5sZW5ndGg9PT0wKTsKVy5zZXQoJ0lNR1Mn'
        'LCB7fSk7Cgpjb25zb2xlLmxvZygnQmFycmVscyBhbmQgdm9sbGV5IGRhbWFnZSwgaW4gdGhlaXIg'
        'b3duIGNvbHVtbnMnKTsKY29uc3QgdGV4dHMgPSAoKT0+IENBTExTLmZpbHRlcihjPT5jLmZuPT09'
        'J2ZpbGxUZXh0JykubWFwKGM9Pih7czpTdHJpbmcoYy5hcmdzWzBdKSwgeDpjLmFyZ3NbMV0sIHk6'
        'Yy5hcmdzWzJdfSkpOwovLyBBIGNvbHVtbiBpcyBjaGVja2VkIGJ5IHdoZXJlIGl0IGFjdHVhbGx5'
        'IGxhbmRzOiB0aGUgeCBvZiB0aGUgY29sdW1uIGluIHRoZQovLyBsYXlvdXQsIGFkZGVkIHRvIHRo'
        'ZSB4IG9mIGEgcm93IHRoZSBtZW51IGl0c2VsZiByZXBvcnRlZC4KY29uc3QgY29sWCA9IChrKT0+'
        'IFcucnVuKCdIR19DT0xTJykuZmluZChjPT5jLms9PT1rKS54OwovLyBUaGUgY29sdW1uIHRpdGxl'
        'cyBzaXQgb24gdGhlIHNhbWUgeCwgc28gYSB2YWx1ZSBvbmx5IGNvdW50cyB3aGVuIGl0IGFsc28K'
        'Ly8gc2l0cyBpbnNpZGUgYSByb3cuCmNvbnN0IGluQ29sID0gKGspPT57CiAgY29uc3QgeDAgPSBj'
        'b2xYKGspLCBycyA9IFcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycpOwogIHJldHVybiB0ZXh0cygp'
        'LmZpbHRlcih0PT4gcnMuc29tZShyPT4gdC54ID09PSByLnggKyB4MCAmJiB0LnkgPj0gci55ICYm'
        'IHQueSA8PSByLnkgKyByLmgpKTsKfTsKcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD04Iik7'
        'IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUoKScp'
        'OwpXLnNldCgnTU9VTlRTJywge30pOwpDTFIoKTsgVy5ydW4oJ2RyYXdTaGlwTWVudSgpJyk7Cm9r'
        'KCdubyBtb3VudCBkYXRhOiBubyBjbGFpbSBhYm91dCBndW5zIG9yIHZvbGxleSBhdCBhbGwnLAog'
        'ICBpbkNvbCgnZ3VucycpLmxlbmd0aD09PTAgJiYgaW5Db2woJ3ZvbGxleScpLmxlbmd0aD09PTAp'
        'OwpXLnNldCgnTU9VTlRTJywge2ZpdG90aDp7cHJpbWFyeTpbMSwxXX0sIGZpaG9ydXM6e3ByaW1h'
        'cnk6WzEsMV19LCBib29zaXJpczp7cHJpbWFyeTpbMSwxXX0sCiAgICAgICAgICAgICAgICAgZmlz'
        'ZXJhcGlzOntwcmltYXJ5OlsxLDFdfSwgZmlzZXRoOntwcmltYXJ5OlsxLDFdfSwgYm9iYWtoYTp7'
        'cHJpbWFyeTpbMSwxXX0sCiAgICAgICAgICAgICAgICAgZml0YXVyZXQ6e3ByaW1hcnk6WzEsMSwx'
        'XX0sIGJvc2VraG1ldDp7cHJpbWFyeTpbMSwxXX19KTsKQ0xSKCk7IFcucnVuKCdkcmF3U2hpcE1l'
        'bnUoKScpOwpvaygnYSBmaWd1cmUgb24gZXZlcnkgb25lIG9mIHRoZSBlaWdodCByb3dzJywKICAg'
        'aW5Db2woJ2d1bnMnKS5sZW5ndGg9PT04ICYmIGluQ29sKCd2b2xsZXknKS5sZW5ndGg9PT04KTsK'
        'b2soJ3RoZSBzZXZlbiB0d28gYmFycmVsIGh1bGxzIHJlYWQgMiBhbmQgNTEnLAogICBpbkNvbCgn'
        'Z3VucycpLmZpbHRlcih0PT50LnM9PT0nMicpLmxlbmd0aD09PTcgJiYKICAgaW5Db2woJ3ZvbGxl'
        'eScpLmZpbHRlcih0PT50LnM9PT0nNTEnKS5sZW5ndGg9PT03KTsKb2soJ3RoZSBUYXVyZXQgcmVh'
        'ZHMgMyBhbmQgNTcnLAogICBpbkNvbCgnZ3VucycpLmZpbHRlcih0PT50LnM9PT0nMycpLmxlbmd0'
        'aD09PTEgJiYKICAgaW5Db2woJ3ZvbGxleScpLmZpbHRlcih0PT50LnM9PT0nNTcnKS5sZW5ndGg9'
        'PT0xKTsKb2soJ3RoZSBmaWd1cmUgbWF0Y2hlcyB3aGF0IHZvbGxleURtZyBhY3R1YWxseSBkb2Vz'
        'JywKICAgTWF0aC5yb3VuZChXLnJ1bigndm9sbGV5VG90YWwoMiknKSk9PT01MSAmJiBNYXRoLnJv'
        'dW5kKFcucnVuKCd2b2xsZXlUb3RhbCgzKScpKT09PTU3CiAgICYmIE1hdGgucm91bmQoVy5ydW4o'
        'J3ZvbGxleVRvdGFsKDEpJykpPT09NDQpOwpvaygnb25lIGJhcnJlbCBpcyB0aGUgZmFsbGJhY2sg'
        'b2YgdGhlIGZvcm11bGEsIG5vdCBhIGNyYXNoJywgVy5ydW4oJ3ZvbGxleVRvdGFsKDApJyk9PT00'
        'NCk7CnsKICAvLyBUaGUgcG9pbnQgb2YgdGhlIGNvbHVtbnM6IGh1bGwgc2l0cyB1bmRlciBodWxs'
        'IG9uIGV2ZXJ5IHJvdy4KICBjb25zdCBodWxscyA9IGluQ29sKCdodWxsJykubWFwKHQ9PnQucyku'
        'am9pbigpOwogIG9rKCd0aGUgaHVsbCBjb2x1bW4gcmVhZHMgZG93biB0aGUgbGlzdCBpbiBvcmRl'
        'cicsIGh1bGxzPT09JzEwMCw4MCw4MCwxMjUsMTAwLDE0MCwxMDAsMTQwJyk7CiAgY29uc3Qgc2hp'
        'ZWxkcyA9IGluQ29sKCdzaGllbGQnKS5tYXAodD0+dC5zKS5qb2luKCk7CiAgb2soJ3RoZSBzaGll'
        'bGQgY29sdW1uIHRvbycsIHNoaWVsZHM9PT0nMTAwLDEwMCw3MCwxMzAsMTMwLDEwMCwxMDAsMTMw'
        'Jyk7CiAgb2soJ2V2ZXJ5IHZhbHVlIGluIGEgY29sdW1uIHNoYXJlcyBvbmUgeCcsCiAgICAgbmV3'
        'IFNldChpbkNvbCgnaHVsbCcpLm1hcCh0PT50LngpKS5zaXplPT09MSk7Cn0KewogIC8vIFR3byB1'
        'bmxvY2tlZCBvZiBlaWdodDogdGhlIG1lbnUgbmVlZHMgdHdvIHRvIG9wZW4gYXQgYWxsLgogIHJl'
        'c2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MiIpOyBXLnNldCgnYWxsaWVzJyxbZGVzdHJveWVy'
        'KCldKTsKICBXLnNldCgnTU9VTlRTJywge2ZpdG90aDp7cHJpbWFyeTpbMSwxXX0sIGZpaG9ydXM6'
        'e3ByaW1hcnk6WzEsMV19LCBmaXRhdXJldDp7cHJpbWFyeTpbMSwxLDFdfX0pOwogIFcucnVuKCd0'
        'b2dnbGVTaGlwTWVudSgpJyk7IENMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKICBvaygn'
        'b25seSB0aGUgdHdvIHVubG9ja2VkIHJvd3MgbWFrZSBhIGNsYWltJywgaW5Db2woJ2d1bnMnKS5s'
        'ZW5ndGg9PT0yKTsKICBvaygndGhlIGxvY2tlZCBUYXVyZXQgc3RheXMgc2lsZW50IGV2ZW4gd2l0'
        'aCBtb3VudCBkYXRhJywKICAgICBpbkNvbCgndm9sbGV5JykuZXZlcnkodD0+dC5zIT09JzU3Jykp'
        'Owp9Clcuc2V0KCdNT1VOVFMnLCB7fSk7Cgpjb25zb2xlLmxvZygnT25lIGxvb2ssIGFuZCBpdCBp'
        'cyB0aGUgZm9ydW0gb25lJyk7CnJlc2V0KCk7IFcucnVuKCJzaGlwVW5sb2NrZWQ9MyIpOyBXLnNl'
        'dCgnYWxsaWVzJyxbZGVzdHJveWVyKCldKTsgVy5ydW4oJ3RvZ2dsZVNoaXBNZW51KCknKTsKQ0xS'
        'KCk7IFcucnVuKCdkcmF3U2hpcE1lbnUoKScpOwpjb25zdCBobHBGb250cyA9IENBTExTLmZpbHRl'
        'cihjPT5jLmZuPT09J3NldCBmb250JykubWFwKGM9PlN0cmluZyhjLmFyZ3NbMF0pKTsKY29uc3Qg'
        'aGxwQ2VsbHMgPSBXLnJ1bignd2luZG93Ll9zaGlwUmVjdHMnKS5tYXAocj0+ci54KycsJytyLnkr'
        'JywnK3IudysnLCcrci5oKS5qb2luKCd8Jyk7Cm9rKCdubyBDb3VyaWVyIGxlZnQgaW4gdGhlIGhh'
        'bmdhcicsIGhscEZvbnRzLmV2ZXJ5KGY9PmYuaW5kZXhPZignQ291cmllcicpPDApKTsKb2soJ2l0'
        'IHVzZXMgdGhlIGZvcnVtIGZhY2VzJywgaGxwRm9udHMuc29tZShmPT5mLmluZGV4T2YoJ1RhaG9t'
        'YScpPj0wKSAmJiBobHBGb250cy5zb21lKGY9PmYuaW5kZXhPZignU2Vnb2UgVUknKT49MCkpOwpv'
        'aygndmFsdWVzIGFyZSBubyBsb25nZXIgc2V0IGluIDggYW5kIDkgcGl4ZWxzJywKICAgaGxwRm9u'
        'dHMuZmlsdGVyKGY9Pi9TZWdvZSBVSS8udGVzdChmKSkuc29tZShmPT4vMVs0LTldcHgvLnRlc3Qo'
        'ZikpKTsKb2soJ3RoZSBhY3RpdmUgcm93IGdldHMgYSBnbG93IHJpbmcnLCBDQUxMUy5zb21lKGM9'
        'PmMuZm49PT0nc2V0IHNoYWRvd0JsdXInKSk7Cm9rKCdubyByaW5nIGxlYWtzIG91dCBvZiBpdHMg'
        'c2F2ZS9yZXN0b3JlJywgYmFsYW5jZWQoKSk7Cm9rKCdub3RoaW5nIGNob29zZXMgYmV0d2VlbiB0'
        'd28gbG9va3MgYW55IG1vcmUnLCAhL0VDT1xcLmh1ZC8udGVzdChzcmMpKTsKVy5ydW4oIkVDTy5z'
        'Y2hlbWU9J3ZvaWQnIik7IENMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKb2soJ3RoZSBo'
        'YW5nYXIgZHJhd3MgaW4gVm9pZCB0b28nLCBDQUxMUy5sZW5ndGg+NTApOwpvaygnYW5kIHRoZSBy'
        'b3dzIGRpZCBub3QgbW92ZScsCiAgIFcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycpLm1hcChyPT5y'
        'LngrJywnK3IueSsnLCcrci53KycsJytyLmgpLmpvaW4oJ3wnKT09PWhscENlbGxzKTsKVy5ydW4o'
        'IkVDTy5zY2hlbWU9J2ZpcmUnIik7Cgpjb25zb2xlLmxvZygnRXZlcnl0aGluZyBpcyBkcmF3biBm'
        'cm9tIHRoZSBzdXJmYWNlIGtpdCcpOwp7CiAgcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxvY2tlZD04'
        'Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9nZ2xlU2hpcE1lbnUo'
        'KScpOwogIENMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCknKTsKICAvLyBHcmFkaWVudHMgYXJl'
        'IGFsbG93ZWQgYWdhaW4sIGJ1dCBvbmx5IGFzIGdsb3NzOiBhIHNob3J0IGZhbGwgb2YgbGlnaHQK'
        'ICAvLyBvdmVyIHRoZSB0b3Agb2YgYSBwbGF0ZS4gTm9uZSBtYXkgcnVuIHRoZSBoZWlnaHQgb2Yg'
        'YSBwYW5lbCB0aGUgd2F5IHRoZQogIC8vIG9sZCBib3ggZ3JhZGllbnQgZGlkLgogIGNvbnN0IGdy'
        'YWRzID0gQ0FMTFMuZmlsdGVyKGM9PmMuZm49PT0nY3JlYXRlTGluZWFyR3JhZGllbnQnKTsKICBv'
        'aygnZXZlcnkgZ3JhZGllbnQgaXMgYSBnbG9zcywgbm90IGEgZnVsbCBoZWlnaHQgZmlsbCcsCiAg'
        'ICAgZ3JhZHMubGVuZ3RoPjAgJiYgZ3JhZHMuZXZlcnkoZz0+KGcuYXJnc1szXS1nLmFyZ3NbMV0p'
        'PD0yMDApKTsKICAvLyBBIGNoYW1mZXJlZCBvdXRsaW5lIGlzIHNpeCBjb3JuZXJzLiBBIHJlY3Rh'
        'bmdsZSB3b3VsZCBiZSBmb3VyLgogIGNvbnN0IGNsb3NlcyA9IENBTExTLmZpbHRlcihjPT5jLmZu'
        'PT09J2Nsb3NlUGF0aCcpLmxlbmd0aDsKICBvaygndGhlIHBhbmVsIGFuZCBldmVyeSBwbGF0ZSBh'
        'cmUgY2hhbWZlcmVkLCBub3QgcmVjdGFuZ2xlcycsIGNsb3Nlcz49OSk7CiAgb2soJ29uZSBzY2Fs'
        'ZSB1bmRlciBlYWNoIG9mIHRoZSB0d28gZ3JvdXAgaGVhZGluZ3MnLAogICAgIENBTExTLmZpbHRl'
        'cihjPT5jLmZuPT09J3NldCBsaW5lV2lkdGgnICYmIGMuYXJnc1swXT09PTEpLmxlbmd0aD4wICYm'
        'IGNsb3Nlcz49OSk7CiAgb2soJ2EgcmluZyBpcyBkcmF3biwgYW5kIG9ubHkgYXJvdW5kIHRoZSBh'
        'Y3RpdmUgcm93JywKICAgICBDQUxMUy5maWx0ZXIoYz0+Yy5mbj09PSdzZXQgc2hhZG93Qmx1cicg'
        'JiYgYy5hcmdzWzBdPT09NikubGVuZ3RoPT09Mik7CiAgb2soJ25vdGhpbmcgbGVha3Mgb3V0IG9m'
        'IGEgc2F2ZS9yZXN0b3JlJywgYmFsYW5jZWQoKSk7Cn0KewogIC8vIFRoZSBraXQgaXMgc2hhcmVk'
        'LCBzbyB0aGUgaGFuZ2FyIG11c3Qgbm90IHJlYWNoIHBhc3QgaXQgZm9yIGEgc2hhcGUgb2YKICAv'
        'LyBpdHMgb3duLiB0aEJldmVsIGFuZCB0aFBhbmVsIGJlbG9uZyB0byB0aGUgc2NyZWVucyBub3Qg'
        'eWV0IHJlYnVpbHQuCiAgY29uc3QgYSA9IHNyYy5pbmRleE9mKCdmdW5jdGlvbiBkcmF3U2hpcE1l'
        'bnUoKScpOwogIGNvbnN0IGJvZHkgPSBzcmMuc2xpY2UoYSwgc3JjLmluZGV4T2YoJ2Z1bmN0aW9u'
        'IGRyYXdDYWxsTWVudSgpJykpOwogIG9rKCd0aGUgaGFuZ2FyIHVzZXMgbm8gYmV2ZWwgYW5kIG5v'
        'IGdyYWRpZW50IHBhbmVsJywKICAgICBib2R5LmluZGV4T2YoJ3RoQmV2ZWwnKTwwICYmIGJvZHku'
        'aW5kZXhPZigndGhQYW5lbCcpPDApOwogIG9rKCdhbmQgbm8gZGlhbG9nIGZyYW1lIG9mIGl0cyBv'
        'd24nLCBib2R5LmluZGV4T2YoJ3VpRGlhbG9nJyk8MCk7Cn0KewogIC8vIFRoZSBkaWdpdCBpcyB0'
        'aGUga2V5Ym9hcmQgc2hvcnRjdXQsIHNvIGl0IGhhcyB0byBmb2xsb3cgdGhlIGh1bGwgdGhyb3Vn'
        'aAogIC8vIHRoZSByZWdyb3VwaW5nIHJhdGhlciB0aGFuIGNvdW50IHJvd3MuCiAgcmVzZXQoKTsg'
        'Vy5ydW4oInNoaXBVbmxvY2tlZD04Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBX'
        'LnJ1bigndG9nZ2xlU2hpcE1lbnUoKScpOwogIENMUigpOyBXLnJ1bignZHJhd1NoaXBNZW51KCkn'
        'KTsKICBjb25zdCBycyA9IFcucnVuKCd3aW5kb3cuX3NoaXBSZWN0cycpOwogIGNvbnN0IGNoaXBY'
        'ID0gVy5ydW4oJ0hHX05VTScpICsgVy5ydW4oJ0hHX05VTV9XJykvMjsKICBjb25zdCBjaGlwID0g'
        'KGtleSk9PnsgY29uc3Qgcj1ycy5maW5kKHI9PnIuc2hpcD09PWtleSk7CiAgICByZXR1cm4gdGV4'
        'dHMoKS5maW5kKHQ9PiB0Lng9PT1yLngrY2hpcFggJiYgdC55Pj1yLnkgJiYgdC55PD1yLnkrci5o'
        'KTsgfTsKICBvaygndGhlIE9zaXJpcyBzaG93cyA2OiBmaXJzdCBib21iZXIsIHNpeHRoIHJvdycs'
        'CiAgICAgY2hpcCgnYm9vc2lyaXMnKSAmJiBjaGlwKCdib29zaXJpcycpLnM9PT0nNicpOwogIG9r'
        'KCdhbmQgdGhlIEJha2hhIHNob3dzIDcnLCBjaGlwKCdib2Jha2hhJykgJiYgY2hpcCgnYm9iYWto'
        'YScpLnM9PT0nNycpOwogIG9rKCd0aGUgZGlnaXRzIHJ1biAxIHRvIDggc3RyYWlnaHQgZG93biB0'
        'aGUgcGFuZWwnLAogICAgIHJzLm1hcChyPT5jaGlwKHIuc2hpcCkucykuam9pbigpPT09JzEsMiwz'
        'LDQsNSw2LDcsOCcpOwp9Cgpjb25zb2xlLmxvZygnVGhlIHBhbmVsIGdyb3dzIHdpdGggd2hhdCBp'
        'cyBvcGVuJyk7CnsKICBjb25zdCBoZWlnaHQgPSAoKT0+eyBjb25zdCByPVcucnVuKCd3aW5kb3cu'
        'X3NoaXBSZWN0cycpOyByZXR1cm4gcltyLmxlbmd0aC0xXS55K3Jbci5sZW5ndGgtMV0uaCAtIHJb'
        'MF0ueTsgfTsKICByZXNldCgpOyBXLnJ1bigic2hpcFVubG9ja2VkPTIiKTsgVy5zZXQoJ2FsbGll'
        'cycsW2Rlc3Ryb3llcigpXSk7IFcucnVuKCd0b2dnbGVTaGlwTWVudSgpOyBkcmF3U2hpcE1lbnUo'
        'KScpOwogIGNvbnN0IHNtYWxsID0gaGVpZ2h0KCk7CiAgcmVzZXQoKTsgVy5ydW4oInNoaXBVbmxv'
        'Y2tlZD04Iik7IFcuc2V0KCdhbGxpZXMnLFtkZXN0cm95ZXIoKV0pOyBXLnJ1bigndG9nZ2xlU2hp'
        'cE1lbnUoKTsgZHJhd1NoaXBNZW51KCknKTsKICBjb25zdCBiaWcgPSBoZWlnaHQoKTsKICBvaygn'
        'ZWlnaHQgb3BlbiBodWxscyBuZWVkIG1vcmUgcm9vbSB0aGFuIHR3bycsIGJpZyA+IHNtYWxsKTsK'
        'ICBvaygnYW5kIGl0IHN0aWxsIGZpdHMgb24gdGhlIGZpZWxkJywKICAgICBXLnJ1bignd2luZG93'
        'Ll9zaGlwUmVjdHMnKS5ldmVyeShyPT5yLnk+PTAgJiYgci55K3IuaDw9NTAwKSk7Cn0KCmNvbnNv'
        'bGUubG9nKCdSZWFybSBuZWVkcyBhIGNvcnZldHRlLCBub3QgYW55IHNoaXAgYXQgYWxsJyk7CnsK'
        'ICBjb25zdCBjb3J2ZXR0ZSA9ICgpPT4oe3R5cGU6J2NvcnZldHRlJywgc2lkZTonYWxseScsIGRl'
        'YWQ6ZmFsc2UsIHdhcnBPdXQ6MCwgd2FycDowfSk7CiAgcmVzZXQoKTsgVy5zZXQoJ2FsbGllcycs'
        'IFtdKTsKICBvaygnbm90aGluZyBvbiB0aGUgZmllbGQsIG5vIHJlYXJtJywgVy5ydW4oJ3JlYXJt'
        'UmVhZHkoKScpPT09ZmFsc2UpOwogIFcuc2V0KCdhbGxpZXMnLCBbZGVzdHJveWVyKCldKTsKICBv'
        'aygnYSBkZXN0cm95ZXIgaXMgYSBoYW5nYXIsIG5vdCBhbiBhcm1vdXJ5JywgVy5ydW4oJ3JlYXJt'
        'UmVhZHkoKScpPT09ZmFsc2UpOwogIFcuc2V0KCdhbGxpZXMnLCBbY29ydmV0dGUoKV0pOwogIG9r'
        'KCdhIGNvcnZldHRlIG9wZW5zIGl0JywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09dHJ1ZSk7CiAg'
        'Y29uc3Qgd2FycGluZyA9IGNvcnZldHRlKCk7IHdhcnBpbmcud2FycCA9IDQwOwogIFcuc2V0KCdh'
        'bGxpZXMnLCBbd2FycGluZ10pOwogIG9rKCdvbmUgc3RpbGwgY29taW5nIG91dCBvZiB0aGUgdm9y'
        'dGV4IGRvZXMgbm90JywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09ZmFsc2UpOwogIGNvbnN0IGRl'
        'YWQgPSBjb3J2ZXR0ZSgpOyBkZWFkLmRlYWQgPSB0cnVlOwogIFcuc2V0KCdhbGxpZXMnLCBbZGVh'
        'ZF0pOwogIG9rKCdub3IgZG9lcyBhIHdyZWNrJywgVy5ydW4oJ3JlYXJtUmVhZHkoKScpPT09ZmFs'
        'c2UpOwogIFcuc2V0KCdhbGxpZXMnLCBbY29ydmV0dGUoKV0pOwogIFcuc2V0KCdhbGxpZXMnLCBb'
        'Y29ydmV0dGUoKV0pOyAgIC8vIGEgbGl2ZSBvbmUgYWdhaW4sIGFmdGVyIHRoZSB3cmVjayBhYm92'
        'ZQogIFcucnVuKCdjbGVhclJlc3VtZUhvbGQoKScpOyAgICAgIC8vIGFuZCBubyBob2xkIGxlZnQg'
        'b3ZlciBmcm9tIGVhcmxpZXIKICAvLyBQcmVzcyB0aGUgcmVjdGFuZ2xlIHRoZSBiYXIgcmVwb3J0'
        'cywgdGhlIHdheSBhIHBsYXllciBkb2VzLiBDYWxsaW5nCiAgLy8gdG9nZ2xlUmVhcm1NZW51KCkg'
        'aGVyZSB0ZXN0ZWQgdGhlIHBhbmVsIGFuZCBub3QgdGhlIGJ1dHRvbiwgd2hpY2ggaXMgaG93CiAg'
        'Ly8gYSBidXR0b24gdGhhdCB3YXMgbmV2ZXIgd2lyZWQgdG8gYW55dGhpbmcgcGFzc2VkLgogIC8v'
        'IENsZWFyIHRoZSBzaGlwIGJ1dHRvbiBmaXJzdDogYW4gZWFybGllciBjYXNlIGxlZnQgYSByZWN0'
        'YW5nbGUgc3RhbmRpbmcKICAvLyB0aGF0IGNvdmVycyB0aGlzIHNwb3QsIGFuZCBwb2ludGVyQ29u'
        'c3VtZWQgYXNrcyBhYm91dCBpdCBvbmUgbGluZSBzb29uZXIuCiAgVy5ydW4oIndpbmRvdy5fc2hp'
        'cEJ0blJlY3Q9bnVsbDsgd2luZG93Ll9yZWFybUJ0blJlY3Q9e3g6NzA5LHk6NCx3OjIyLGg6NDZ9'
        'OyIKICAgICAgKyAiIHBvaW50ZXJDb25zdW1lZCh7eDo3MTQseToxMn0pIik7CiAgb2soJ3ByZXNz'
        'aW5nIHRoZSBidXR0b24gaW4gdGhlIGJhciBvcGVucyB0aGUgcGFuZWwnLCBXLmdldCgncmVhcm1N'
        'ZW51Jyk9PT10cnVlKTsKICBXLnJ1bigicG9pbnRlckNvbnN1bWVkKHt4OjcxNCx5OjEyfSkiKTsK'
        'ICBvaygnYW5kIHByZXNzaW5nIGl0IGFnYWluIGNsb3NlcyBpdCcsIFcuZ2V0KCdyZWFybU1lbnUn'
        'KT09PWZhbHNlKTsKICBXLnJ1bignc2V0UmVhcm1NZW51KGZhbHNlKScpOwp9Cgpjb25zb2xlLmxv'
        'ZygnVGhlIHN0YW5kYXJkIGZpdCBpcyBwcm92YWJseSB0aGUgZ3VuIHRoZSBnYW1lIGhhZCcpOwp7'
        'CiAgY29uc3QgcCA9IFcucnVuKCJwcmlEZWYoJ3Byb21ldGhldXMnKSIpOwogIG9rKCd0aGUgUHJv'
        'bWV0aGV1cyBjYXJyaWVzIG5vIGZhY3RvcnMgYXQgYWxsJywgcC5kbWc9PT0xICYmIHAucmF0ZT09'
        'PTEpOwogIG9rKCdhbmQgbm8gbGltaXQgb24gaXRzIHJlYWNoJywgcC5yYW5nZT09PTApOwogIHJl'
        'c2V0KCk7IFcucnVuKCJwbGF5ZXIucHJpPSdwcm9tZXRoZXVzJzsgYXBwbHlMb2Fkb3V0KCkiKTsK'
        'ICBvaygnc28gdGhlIHJhdGUgb2YgZmlyZSBpcyB0aGUgb2xkIDI4IHN0ZXBzJywgVy5nZXQoJ3Bs'
        'YXllcicpLmZSPT09MjgpOwogIGNvbnN0IG0gPSBXLnJ1bigic2VjRGVmKCdteDY0JykiKTsKICBv'
        'aygndGhlIE1YLTY0IGlzIHRoZSBvbGQgbWlzc2lsZSwgdG8gdGhlIG51bWJlcicsCiAgICAgbS5k'
        'bWc9PT0zNSAmJiBtLmNkPT09NDUgJiYgbS5zcGQ9PT0zLjUgJiYgbS5saWZlPT09MjIwICYmIG0u'
        'aG9taW5nPT09dHJ1ZSk7CiAgY29uc3QgYyA9IFcucnVuKCJzZWNEZWYoJ2N5Y2xvcHMnKSIpOwog'
        'IG9rKCdhbmQgdGhlIEN5Y2xvcHMgdGhlIG9sZCBib21iJywKICAgICBjLmRtZz09PTgwICYmIGMu'
        'Y2Q9PT05MCAmJiBjLnNwZD09PTEuNSAmJiBjLmxpZmU9PT0zMDApOwp9Cgpjb25zb2xlLmxvZygn'
        'QSBodWxsIGNhbiBvbmx5IGNhcnJ5IHdoYXQgaXQgY2FuIGNhcnJ5Jyk7CnsKICByZXNldCgpOyBX'
        'LnJ1bigiYXBwbHlTaGlwKCdmaXRvdGgnKSIpOwogIG9rKCdhIGZpZ2h0ZXIgaXMgZ2l2ZW4gYSBt'
        'aXNzaWxlJywgVy5ydW4oImN1clNlYygpLmNscyIpPT09J21pc3NpbGUnKTsKICBvaygnYW5kIHRo'
        'ZSBiYXIgaXMgdG9sZCBzbycsIFcuZ2V0KCdwbGF5ZXInKS5zZWNUeXBlPT09J21pc3NpbGUnKTsK'
        'ICBXLnJ1bigiYXBwbHlTaGlwKCdib29zaXJpcycpIik7CiAgb2soJ2EgYm9tYmVyIGNhbm5vdCBr'
        'ZWVwIGl0LCBhbmQgZ2V0cyBhIGJvbWInLCBXLnJ1bigiY3VyU2VjKCkuY2xzIik9PT0nYm9tYicp'
        'OwogIG9rKCdhbmQgdGhlIGJhciBhZ2FpbicsIFcuZ2V0KCdwbGF5ZXInKS5zZWNUeXBlPT09J2Jv'
        'bWInKTsKICBvaygnb25seSBib21icyBhcmUgb2ZmZXJlZCB0byBpdCcsCiAgICAgVy5ydW4oInNl'
        'Y29uZGFyaWVzRm9yKCdib29zaXJpcycpIikuZXZlcnkodz0+dy5jbHM9PT0nYm9tYicpKTsKICBv'
        'aygnYW5kIG9ubHkgbWlzc2lsZXMgdG8gYSBmaWdodGVyJywKICAgICBXLnJ1bigic2Vjb25kYXJp'
        'ZXNGb3IoJ2ZpdG90aCcpIikuZXZlcnkodz0+dy5jbHM9PT0nbWlzc2lsZScpKTsKICBvaygndGhl'
        'IHJhY2sgc2l6ZSBzdGlsbCBjb21lcyBmcm9tIHRoZSBodWxsJywKICAgICBXLmdldCgncGxheWVy'
        'Jykuc2VjTWF4ID09PSBXLnJ1bigic2hpcFN0YXRzKCdib29zaXJpcycpLnNlYyIpKTsKfQoKY29u'
        'c29sZS5sb2coJ0EgcmVmaXQgZmlsbHMgdGhlIHJhY2sgLSB0aGF0IGlzIHdoYXQgbWFrZXMgaXQg'
        'YSByZWFybScpOwp7CiAgY29uc3QgY29ydmV0dGUgPSAoKT0+KHt0eXBlOidjb3J2ZXR0ZScsIHNp'
        'ZGU6J2FsbHknLCBkZWFkOmZhbHNlLCB3YXJwT3V0OjAsIHdhcnA6MH0pOwogIHJlc2V0KCk7IFcu'
        'cnVuKCJhcHBseVNoaXAoJ2ZpdG90aCcpOyBzY29yZT0wIik7IFcuc2V0KCdhbGxpZXMnLCBbY29y'
        'dmV0dGUoKV0pOwogIFcucnVuKCdwbGF5ZXIuc2VjQW1tbz0zJyk7CiAgVy5ydW4oJ3RvZ2dsZVJl'
        'YXJtTWVudSgpJyk7CiAgVy5ydW4oImZpdFdlYXBvbignbXg2NCcpIik7CiAgb2soJ2ZpdHRpbmcg'
        'd2hhdCBpcyBhbHJlYWR5IGZpdHRlZCB0b3BzIHRoZSByYWNrIHVwJywKICAgICBXLmdldCgncGxh'
        'eWVyJykuc2VjQW1tbyA9PT0gVy5nZXQoJ3BsYXllcicpLnNlY01heCk7CiAgb2soJ2FuZCBjbG9z'
        'ZXMgdGhlIHBhbmVsJywgVy5nZXQoJ3JlYXJtTWVudScpPT09ZmFsc2UpOwogIC8vIExvY2tlZCB3'
        'ZWFwb25zIGNhbm5vdCBiZSB0YWtlbiwgaG93ZXZlciB0aGV5IGFyZSByZWFjaGVkLgogIFcucnVu'
        'KCdwbGF5ZXIuc2VjQW1tbz0zOyB0b2dnbGVSZWFybU1lbnUoKScpOwogIFcucnVuKCJmaXRXZWFw'
        'b24oJ2hsNycpIik7CiAgb2soJ2Egd2VhcG9uIGFib3ZlIHRoZSBzY29yZSBjYW5ub3QgYmUgZml0'
        'dGVkJywgVy5nZXQoJ3BsYXllcicpLnByaT09PSdwcm9tZXRoZXVzJyk7CiAgb2soJ2FuZCB0aGUg'
        'cGFuZWwgc3RheXMgb3BlbicsIFcuZ2V0KCdyZWFybU1lbnUnKT09PXRydWUpOwogIFcucnVuKCdz'
        'Y29yZT02MDAwJyk7CiAgVy5ydW4oImZpdFdlYXBvbignaGw3JykiKTsKICBvaygncGFzdCB0aGUg'
        'dGhyZXNob2xkIGl0IGNhbicsIFcuZ2V0KCdwbGF5ZXInKS5wcmk9PT0naGw3Jyk7CiAgb2soJ2Fu'
        'ZCB0aGUgcmF0ZSBvZiBmaXJlIGZvbGxvd3MgdGhlIHdlYXBvbicsIFcuZ2V0KCdwbGF5ZXInKS5m'
        'Uj09PTE3KTsKICBXLnJ1bignc2NvcmU9MDsgcGxheWVyLnByaT0icHJvbWV0aGV1cyI7IGFwcGx5'
        'TG9hZG91dCgpJyk7Cn0KCmNvbnNvbGUubG9nKCdUaGUgcmVhcm0gcGFuZWwnKTsKewogIGNvbnN0'
        'IGNvcnZldHRlID0gKCk9Pih7dHlwZTonY29ydmV0dGUnLCBzaWRlOidhbGx5JywgZGVhZDpmYWxz'
        'ZSwgd2FycE91dDowLCB3YXJwOjB9KTsKICByZXNldCgpOyBXLnJ1bigiYXBwbHlTaGlwKCdmaXRv'
        'dGgnKTsgc2NvcmU9OTAwMCIpOyBXLnNldCgnYWxsaWVzJywgW2NvcnZldHRlKCldKTsKICBXLnJ1'
        'bigndG9nZ2xlUmVhcm1NZW51KCknKTsKICBDTFIoKTsgVy5ydW4oJ2RyYXdSZWFybU1lbnUoKScp'
        'OwogIGNvbnN0IHJzID0gVy5ydW4oJ3dpbmRvdy5fcmVhcm1SZWN0cycpOwogIGNvbnN0IHByID0g'
        'Vy5ydW4oJ3dpbmRvdy5fcmVhcm1QYW5lbFJlY3QnKTsKICAvLyBPbmUgcm93IHBlciB3ZWFwb24g'
        'dGhhdCBleGlzdHMsIG9wZW4gb3Igbm90OiBhIGxvY2tlZCBvbmUgaXMgYSB0aGluCiAgLy8gbGlu'
        'ZSwgYW5kIGl0IGlzIHN0aWxsIGEgcm93LiBUaGUgY291bnQgZm9sbG93cyB0aGUgdGFibGVzIHNv'
        'IGEgbmV3CiAgLy8gd2VhcG9uIGRvZXMgbm90IG1ha2UgdGhpcyBmYWlsIGZvciBubyByZWFzb24u'
        'CiAgY29uc3Qgb2ZmZXJlZCA9IFcucnVuKCdQUklNQVJJRVMnKS5sZW5ndGggKyBXLnJ1bigic2Vj'
        'b25kYXJpZXNGb3IoJ2ZpdG90aCcpIikubGVuZ3RoOwogIG9rKCdvbmUgcm93IHBlciB3ZWFwb24g'
        'b24gb2ZmZXInLCBycy5sZW5ndGg9PT1vZmZlcmVkKTsKICBvaygnZXZlcnkgcm93IGlzIGluc2lk'
        'ZSB0aGUgcGFuZWwnLAogICAgIHJzLmV2ZXJ5KHI9PnIueD49cHIueCAmJiByLngrci53PD1wci54'
        'K3ByLncgJiYgci55Pj1wci55ICYmIHIueStyLmg8PXByLnkrcHIuaCkpOwogIG9rKCd0aGUgcGFu'
        'ZWwgZml0cyBvbiB0aGUgZmllbGQnLCBwci55Pj0wICYmIHByLnkrcHIuaDw9NTAwICYmIHByLng+'
        'PTAgJiYgcHIueCtwci53PD04MDApOwogIG9rKCdubyBDb3VyaWVyIGFueXdoZXJlJywKICAgICBD'
        'QUxMUy5maWx0ZXIoYz0+Yy5mbj09PSdzZXQgZm9udCcpLmV2ZXJ5KGM9PlN0cmluZyhjLmFyZ3Nb'
        'MF0pLmluZGV4T2YoJ0NvdXJpZXInKTwwKSk7CiAgb2soJ3RoZSBmaXR0ZWQgd2VhcG9uIGdldHMg'
        'dGhlIHJpbmcnLCBDQUxMUy5zb21lKGM9PmMuZm49PT0nc2V0IHNoYWRvd0JsdXInKSk7CiAgb2so'
        'J25vdGhpbmcgbGVha3Mgb3V0IG9mIGEgc2F2ZS9yZXN0b3JlJywgYmFsYW5jZWQoKSk7CiAgLy8g'
        'QSBjbGljayBpbnNpZGUgdGhlIHBhbmVsIHRoYXQgaGl0IG5vIHJvdyBtdXN0IG5vdCBjbG9zZSBp'
        'dCwgdGhlIHNhbWUKICAvLyBydWxlIHRoZSBoYW5nYXIgYW5kIHRoZSBzdXBwb3J0IG1lbnUgZm9s'
        'bG93LgogIFcucnVuKGBwb2ludGVyQ29uc3VtZWQoe3g6JHtwci54KzQwfSx5OiR7cHIueSs2fX0p'
        'YCk7CiAgb2soJ2EgY2xpY2sgb24gdGhlIGhlYWRlciBrZWVwcyBpdCBvcGVuJywgVy5nZXQoJ3Jl'
        'YXJtTWVudScpPT09dHJ1ZSk7CiAgVy5ydW4oYHBvaW50ZXJDb25zdW1lZCh7eDoke3ByLngtMTJ9'
        'LHk6JHtwci55K3ByLmgvMn19KWApOwogIG9rKCdhIGNsaWNrIGJlc2lkZSBpdCBjbG9zZXMgaXQn'
        'LCBXLmdldCgncmVhcm1NZW51Jyk9PT1mYWxzZSk7Cn0KewogIC8vIEJlbG93IHRoZSB0aHJlc2hv'
        'bGQgdGhlIEhMLTcgaXMgYSB0aGluIGxpbmUsIG5vdCBhIHJvdyB0aGF0IGNhbiBiZSB0YWtlbi4K'
        'ICBjb25zdCBjb3J2ZXR0ZSA9ICgpPT4oe3R5cGU6J2NvcnZldHRlJywgc2lkZTonYWxseScsIGRl'
        'YWQ6ZmFsc2UsIHdhcnBPdXQ6MCwgd2FycDowfSk7CiAgcmVzZXQoKTsgVy5ydW4oImFwcGx5U2hp'
        'cCgnZml0b3RoJyk7IHNjb3JlPTAiKTsgVy5zZXQoJ2FsbGllcycsIFtjb3J2ZXR0ZSgpXSk7CiAg'
        'Vy5ydW4oJ3RvZ2dsZVJlYXJtTWVudSgpOyBkcmF3UmVhcm1NZW51KCknKTsKICBjb25zdCBycyA9'
        'IFcucnVuKCd3aW5kb3cuX3JlYXJtUmVjdHMnKTsKICBvaygnYSBsb2NrZWQgd2VhcG9uIHJlcG9y'
        'dHMgbm8ga2V5JywgcnMuc29tZShyPT5yLmtleT09PW51bGwpKTsKICBvaygnYW5kIGl0cyBsaW5l'
        'IGlzIHRoaW5uZXIgdGhhbiBhIHJvdyB0aGF0IGNhbiBiZSB0YWtlbicsCiAgICAgTWF0aC5taW4o'
        'Li4ucnMubWFwKHI9PnIuaCkpIDwgTWF0aC5tYXgoLi4ucnMubWFwKHI9PnIuaCkpKTsKICBXLnJ1'
        'bignc2V0UmVhcm1NZW51KGZhbHNlKTsgc2NvcmU9MCcpOwp9Cgpjb25zb2xlLmxvZygnVGhlIHRp'
        'dGxlIHNjcmVlbicpOwovLyBkcmF3VGl0bGUgaXMgdG9vIHRhbmdsZWQgdXAgd2l0aCB0aGUgYmFj'
        'a2Ryb3AgdG8gcnVuIGhlcmUsIHNvIHdoYXQgaXMKLy8gY2hlY2tlZCBpcyB0aGUgdHdvIHRoaW5n'
        'cyB0aGF0IG1hZGUgaXQgbG9vayB0aGUgd2F5IGl0IGRpZC4Kb2soJ25vIG9wYXF1ZSBzaGVldCBv'
        'dmVyIHRoZSBza3kgYW55IG1vcmUnLCAhL2ZpbGxTdHlsZT0ncmdiYVwoMCwwLDgsMFwuNzhcKSc7'
        'Y3R4XC5maWxsUmVjdFwoMCwwLFcsSFwpLy50ZXN0KHNyYykpOwpvaygnd2hhdCBpcyBsZWZ0IGlz'
        'IGEgZ3JhZGllbnQsIHNvIHRoZSBiYWNrZHJvcCBzaG93cyB0aHJvdWdoIHRoZSB0b3AnLAogICAv'
        'Y3JlYXRlTGluZWFyR3JhZGllbnRcKDAsIDAsIDAsIEhcKVtcc1xTXXswLDI2MH0/cmdiYVwoMCww'
        'LDgsMFwuMjBcKS8udGVzdChzcmMpKTsKb2soJ3RoZSBwYXN0ZWQgbG9nbyBhbmQgaXRzIDMgYXJl'
        'IGdvbmUnLAogICAhL19sb2dvUHJvY2Vzc2VkLy50ZXN0KHNyYykgJiYgIS9mc19sb2dvLy50ZXN0'
        'KHNyYykpOwpvaygndGhlIHRpdGxlIGlzIHNldCBpbiB0aGUgdGhlbWUgZmFjZSBpbnN0ZWFkJywg'
        'L0ZSRUVTUEFDRS8udGVzdChzcmMpICYmIC90aExhYmVsXCg1NFwpLy50ZXN0KHNyYykpOwpvaygn'
        'YSBmcmVzaCBiYWNrZHJvcCBpcyByb2xsZWQgZXZlcnkgdGltZSB0aGUgdGl0bGUgY29tZXMgdXAn'
        'LAogICAvZnVuY3Rpb24gZW50ZXJUaXRsZVwoXClce1tcc1xTXXswLDMwMH0/bmViQ3VyID0gTkVC'
        'X05BTUVTW1xzXFNdezAsMTIwfT9yb2xsQm9kaWVzXChcKS8udGVzdChzcmMpKTsKb2soJ2FuZCBh'
        'IGJvZHkgdGhhdCBsZWF2ZXMgdGhlIHRpdGxlIGlzIHJlcGxhY2VkLCBub3Qgd3JhcHBlZCByb3Vu'
        'ZCcsCiAgIC9pZlwoR1M9PT0ndGl0bGUnXClceyByb2xsQm9kaWVzXChcKTsgcmV0dXJuOyBcfS8u'
        'dGVzdChzcmMpKTsKb2soJ3RoZSB0aXRsZSBrZWVwcyBtb3Zpbmcgd2hpbGUgaXQgc2l0cyB0aGVy'
        'ZScsCiAgIC9pZlwoR1M9PT0ndGl0bGUnXClceyBmY1wrXCs7IHRpY2tTdGFyc1woXCk7IHRpY2tO'
        'ZWJ1bGFcKFwpOyByZXR1cm47IFx9Ly50ZXN0KHNyYykpOwpvaygnVHJ5IEFnYWluIGdvZXMgYmFj'
        'ayB0byB0aGUgdGl0bGUgcmF0aGVyIHRoYW4gaW50byB0aGUgbmV4dCBydW4nLAogICAvZnVuY3Rp'
        'b24gdG9UaXRsZU9yTGF1bmNoXChcKVx7W1xzXFNdezAsMTYwfT9HUz09PSdnYW1lb3ZlcidcKXsg'
        'ZW50ZXJUaXRsZVwoXCkvLnRlc3Qoc3JjKSk7Cm9rKCdhbmQgbm90aGluZyBjYWxscyBsYXVuY2hH'
        'YW1lIHN0cmFpZ2h0IGZyb20gdGhlIGdhbWUgb3ZlciBzY3JlZW4nLAogICAhL2dhbWVPdmVyQXQ+'
        'MTUwMFwpIGxhdW5jaEdhbWVcKFwpLy50ZXN0KHNyYykpOwoKY29uc29sZS5sb2coJ0JhciBidXR0'
        'b24gcGxhY2VtZW50Jyk7CnsKICAvLyBUaGUgc2hpcCBzd2l0Y2ggYW5kIHRoZSByZWFybSBidXR0'
        'b24gYXJlIGRyYXduIGFzIG9uZSBwYWlyIG5vdywgc28gdGhlCiAgLy8gc25pcHBldCBjb3ZlcnMg'
        'Ym90aCBhbmQgYm90aCBhcmUgY2hlY2tlZC4KICBjb25zdCBhID0gc3JjLmluZGV4T2YoJyAgLy8g'
        'U0hJUCBTV0lUQ0ggYW5kIFJFQVJNJyksIGIgPSBzcmMuaW5kZXhPZignICAvLyBTRVRUSU5HUyBh'
        'bmQgUEFVU0UnKTsKICBjb25zdCBzbmlwID0gc3JjLnNsaWNlKGEsIGIpOwogIFcucnVuKCJ2YXIg'
        'SDI9NTQ7IHNoaXBNZW51PWZhbHNlOyByZWFybU1lbnU9ZmFsc2U7IGFsbGllcz1bXTsiCiAgICAg'
        'ICsgIiB3aW5kb3cuX3NoaXBCdG5SZWN0PXVuZGVmaW5lZDsgd2luZG93Ll9yZWFybUJ0blJlY3Q9'
        'dW5kZWZpbmVkOyAiICsgc25pcCk7CiAgY29uc3QgciA9IFcucnVuKCd3aW5kb3cuX3NoaXBCdG5S'
        'ZWN0JyksIHJtID0gVy5ydW4oJ3dpbmRvdy5fcmVhcm1CdG5SZWN0Jyk7CiAgb2soJ3RoZSBzaGlw'
        'IGJ1dHRvbiBzaXRzIGJldHdlZW4gdGlja2V0cyAoNjY1KSBhbmQgZ2VhciAoNzQ4KScsIHIgJiYg'
        'ci54PjY2NSAmJiByLngrci53PDc0OCk7CiAgb2soJ3RoZSByZWFybSBidXR0b24gc2l0cyBiZXNp'
        'ZGUgaXQsIGFsc28gY2xlYXIgb2YgdGhlIGdlYXInLAogICAgIHJtICYmIHJtLnggPj0gci54K3Iu'
        'dyAmJiBybS54K3JtLncgPCA3NDgpOwogIG9rKCd0aGV5IGRvIG5vdCBvdmVybGFwJywgcm0gJiYg'
        'cm0ueCA+PSByLnggKyByLncpOwogIFcucnVuKCJGUzFfTU9ERT10cnVlOyAiICsgc25pcCk7CiAg'
        'b2soJ25laXRoZXIgYnV0dG9uIGluIEZTMSBtb2RlJywKICAgICBXLnJ1bignd2luZG93Ll9zaGlw'
        'QnRuUmVjdCcpPT09bnVsbCAmJiBXLnJ1bignd2luZG93Ll9yZWFybUJ0blJlY3QnKT09PW51bGwp'
        'OwogIFcucnVuKCdGUzFfTU9ERT1mYWxzZScpOwp9CmNvbnNvbGUubG9nKCdDeWNsZSBzY2FsaW5n'
        'IGtlZXBzIHRoZSBodWxsJyk7Cm9rKCduZXh0V2F2ZSBzY2FsZXMgZnJvbSB0aGUgaHVsbCBiYXNl'
        'LCBub3QgZnJvbSAxMDAnLCBzcmMuaW5jbHVkZXMoJ3BsYXllci5tYXhIcD1NYXRoLnJvdW5kKChw'
        'bGF5ZXIuYmFzZUhwfHwxMDApKnBtKTsnKSk7Cm9rKCdyZXNwYXduIHJlc3RvcmVzIHRoZSBmdWxs'
        'IGh1bGwnLCBzcmMuaW5jbHVkZXMoJ3BsYXllci5ocD1wbGF5ZXIubWF4SHA7cGxheWVyLng9ODA7'
        'JykpOwoKY29uc29sZS5sb2coJ1xuJyArIChmYWlscyA/IGZhaWxzKycgRkFJTEVEJyA6ICdhbGwg'
        'cGFzc2VkJykpOwpwcm9jZXNzLmV4aXQoZmFpbHM/MTowKTsK'
    ),
    'wpnsim.js': (
        'Ly8gV2VhcG9uIHNpbXVsYXRpb24uIFB1bGxzIHRoZSBSRUFMIGZpcmluZyByb3V0aW5lcyBvdXQg'
        'b2YgdGhlIGxvZ2ljIGZpbGUgYW5kCi8vIHJ1bnMgdGhlbSBhZ2FpbnN0IHN0YW5kLWlucyBmb3Ig'
        'dGhlIHdvcmxkLgovLwovLyBXaGF0IGl0IGlzIGZvcjogc2V2ZXJhbCBvZiB0aGUgd2VhcG9ucyBk'
        'byBzb21ldGhpbmcgcmF0aGVyIHRoYW4gbWVyZWx5Ci8vIHdlaWdoIHNvbWV0aGluZyAtIGEgY29u'
        'ZSwgYSByb3VuZCB0aGF0IGJ1cnN0cywgYSB3YXJoZWFkIHRoYXQgZ29lcyBmb3IgdGhlCi8vIGlu'
        'bmFyZHMsIGEgc2Fsdm8gdGhhdCBzcGxpdHMgb3ZlciBzZXZlcmFsIHRhcmdldHMuIE51bWJlcnMg'
        'Y2FuIGJlIHJlYWQgb2ZmIHRoZSB0YWJsZTsKLy8gYmVoYXZpb3VyIGNhbm5vdC4KLy8KLy8gVXNh'
        'Z2U6IG5vZGUgd3Buc2ltLmpzIDxsb2dpYy5odG1sPgpjb25zdCBmcyA9IHJlcXVpcmUoJ2ZzJyk7'
        'CmNvbnN0IGh0bWwgPSBmcy5yZWFkRmlsZVN5bmMocHJvY2Vzcy5hcmd2WzJdLCAndXRmOCcpOwpj'
        'b25zdCBzcmMgPSBodG1sLm1hdGNoKC88c2NyaXB0W14+XSo+KFtcc1xTXSopPFwvc2NyaXB0Pi8p'
        'WzFdOwoKZnVuY3Rpb24gYmxvY2tFbmQocywgaSl7CiAgbGV0IGogPSBzLmluZGV4T2YoJ3snLCBp'
        'KSwgZGVwdGggPSAwOwogIGZvcig7IGogPCBzLmxlbmd0aDsgaisrKXsKICAgIGNvbnN0IGMgPSBz'
        'W2pdOwogICAgaWYoYyA9PT0gJ3snKSBkZXB0aCsrOwogICAgZWxzZSBpZihjID09PSAnfScpeyBk'
        'ZXB0aC0tOyBpZighZGVwdGgpIHJldHVybiBqICsgMTsgfQogICAgZWxzZSBpZihjID09PSAiJyIg'
        'fHwgYyA9PT0gJyInIHx8IGMgPT09ICdgJyl7IGNvbnN0IHEgPSBjOyBqKys7IHdoaWxlKGogPCBz'
        'Lmxlbmd0aCAmJiBzW2pdICE9PSBxKSBqICs9IChzW2pdID09PSAnXFwnKSA/IDIgOiAxOyB9CiAg'
        'ICBlbHNlIGlmKHMuc3RhcnRzV2l0aCgnLy8nLCBqKSkgaiA9IHMuaW5kZXhPZignXG4nLCBqKTsK'
        'ICAgIGVsc2UgaWYocy5zdGFydHNXaXRoKCcvKicsIGopKSBqID0gcy5pbmRleE9mKCcqLycsIGop'
        'ICsgMTsKICB9CiAgdGhyb3cgbmV3IEVycm9yKCd1bmJhbGFuY2VkJyk7Cn0KZnVuY3Rpb24gZm4o'
        'bmFtZSl7CiAgY29uc3QgaSA9IHNyYy5pbmRleE9mKCdcbmZ1bmN0aW9uICcgKyBuYW1lICsgJygn'
        'KTsKICBpZihpIDwgMCkgdGhyb3cgbmV3IEVycm9yKCdtaXNzaW5nIGZ1bmN0aW9uICcgKyBuYW1l'
        'KTsKICByZXR1cm4gc3JjLnNsaWNlKGkgKyAxLCBibG9ja0VuZChzcmMsIGkpKTsKfQpmdW5jdGlv'
        'biBkZWNsKHJlKXsKICBjb25zdCBtID0gc3JjLm1hdGNoKHJlKTsKICBpZighbSkgdGhyb3cgbmV3'
        'IEVycm9yKCdtaXNzaW5nIGRlY2xhcmF0aW9uICcgKyByZSk7CiAgcmV0dXJuIG1bMF07Cn0KCmNv'
        'bnN0IG5hbWVzID0gWydwcmlEZWYnLCdzZWNEZWYnLCdjdXJQcmknLCdjdXJTZWMnLCdodWxsU2Vj'
        'Q2xzJywnd2VhcG9uTmFtZScsJ3dlYXBvbk9wZW4nLAogICAgICAgICAgICAgICAnc2Vjb25kYXJp'
        'ZXNGb3InLCdkZWZhdWx0U2VjJywnYXBwbHlMb2Fkb3V0JywncmVhcm1GdWxsJywKICAgICAgICAg'
        'ICAgICAgJ3NoYXJkQnVyc3QnLCdzdWJTdHJpa2UnLCdzdWJTdHJpa2VSYXcnLCdwU2hvb3QnLCdm'
        'aXJlU2Vjb25kYXJ5JywKICAgICAgICAgICAgICAgJ2xpdmVCdXJzdFJvdW5kJywnYnVyc3RSb3Vu'
        'ZCcsJ3ZvbGxleURtZycsJ3ZvbGxleVRvdGFsJywncHJpbWFyeUNvdW50JywKICAgICAgICAgICAg'
        'ICAgJ2ZsYWtIYXMnLCdmbGFrQnVyc3QnLCdmbGFrUmVhY2gnLCdmbGFrRmlyZScsCiAgICAgICAg'
        'ICAgICAgICdzd2FybVRhcmdldHMnLCdzd2FybVJldGFyZ2V0Jywnc3dhcm1Ib2xkcycsJ3VwZGF0'
        'ZVNlY0J1bGxldHMnLCdybVZhbHVlJ107CmNvbnN0IGNvbnN0cyA9IFsKICBkZWNsKC9jb25zdCBQ'
        'TEFZRVJfRlJfQkFTRVtcc1xTXSo/XG5cXTsvKSwKICBkZWNsKC9jb25zdCBTRUNPTkRBUklFUyA9'
        'IFxbW1xzXFNdKj9cblxdOy8pLAogIGRlY2woL2NvbnN0IFNVQl9XQVJIRUFEX01VTCA9IFteO10q'
        'Oy8pLAogIGRlY2woL2NvbnN0IFZPTExFWV9CQVNFXHMqPVxzKltcZC5dKzsvKSwKICBkZWNsKC9j'
        'b25zdCBWT0xMRVlfUEVSX0VYVFJBXHMqPVxzKltcZC5dKzsvKSwKICBkZWNsKC9jb25zdCBGTEFL'
        'X1RZUEVTW1xzXFNdKj9jb25zdCBGTEFLX1NIQVJEX1JBTkdFID0gXGQrOy8pLAogIGRlY2woL2xl'
        'dCBzd2FybVNhbHZvID0gMDsvKQpdOwoKY29uc3QgV09STEQgPSBgCmNvbnN0IFcgPSA4MDAsIEgg'
        'PSA1MDAsIEhVRF9IID0gNTQ7CnZhciBwQnVsbGV0cyA9IFtdLCBlQnVsbGV0cyA9IFtdLCBQQVJU'
        'UyA9IFtdLCBTVUJfTVNHUyA9IFtdLCBlbmVtaWVzID0gW10sIGFsbGllcyA9IFtdOwp2YXIgZmMg'
        'PSAwLCBzY29yZSA9IDAsIEZTMV9NT0RFID0gZmFsc2UsIFVJX1dFQVBPTlMgPSBmYWxzZTsKY29u'
        'c3QgVUlfVElDS0VUUyA9IGZhbHNlOwpjb25zdCBTVEFUUyA9IHtzaG90czowLCBoaXRzOjAsIHN1'
        'YnNLaWxsZWQ6MH07CnZhciBwbGF5ZXIgPSB7eDoxMDAsIHk6MjUwLCBoZWFkOjAsIGFuZzowLCBm'
        'bGlwOmZhbHNlLCBzaGlwOidmaXRvdGgnLAogICAgICAgICAgICAgIGZSOjI4LCBzZWNBbW1vOjIw'
        'LCBzZWNNYXg6MjAsIHNlY1RpbWVyOjAsIHNlY1R5cGU6J21pc3NpbGUnLAogICAgICAgICAgICAg'
        'IHByaToncHJvbWV0aGV1cycsIHNlYzonbXg2NCd9OwovLyBNb3VudHMgYXJlIHRoZSBodWxsJ3Mg'
        'YnVzaW5lc3MsIG5vdCB0aGUgd2VhcG9uJ3MuIFR3byBiYXJyZWxzLCBmaXhlZCwgc28gYQovLyBj'
        'aGFuZ2UgaW4gdGhlIHZvbGxleSBjYW4gb25seSBjb21lIGZyb20gdGhlIGd1bi4KZnVuY3Rpb24g'
        'bW91bnRMaXN0KCl7IHJldHVybiBbe3g6MTIwLCB5OjI0Nn0sIHt4OjEyMCwgeToyNTR9XTsgfQpm'
        'dW5jdGlvbiBwbGF5ZXJTYygpeyByZXR1cm4gMTsgfQpmdW5jdGlvbiBpc0JvbWJlckh1bGwoayl7'
        'IHJldHVybiBrLmluZGV4T2YoJ2JvJyk9PT0wOyB9CmZ1bmN0aW9uIHNoaXBGYWMoayl7IHJldHVy'
        'biAndmFzdWRhbic7IH0KZnVuY3Rpb24gc2hpcFN0YXRzKGspeyByZXR1cm4ge3NlYzogaXNCb21i'
        'ZXJIdWxsKGspID8gMTAgOiAyMH07IH0KZnVuY3Rpb24gc3Bhd25GaXJlYmFsbCgpe30gCi8vIFRo'
        'ZSBwcmFjdGljZSBsb2cgaXMgbm90IHdoYXQgaXMgdGVzdGVkIGhlcmUuCmZ1bmN0aW9uIHBsb2dL'
        'aWxsKCl7fSBmdW5jdGlvbiBwbG9nUmVhcm0oKXt9IGZ1bmN0aW9uIHBsb2dTZWMoKXt9IGZ1bmN0'
        'aW9uIHBsb2dIaXQoKXt9IGZ1bmN0aW9uIHBsb2dQaWNrKCl7fSBmdW5jdGlvbiBwbG9nU3JjKCl7'
        'fSBmdW5jdGlvbiBwbG9nTG9zcygpe30gZnVuY3Rpb24gcGxvZ0V2ZW50KCl7fSBmdW5jdGlvbiBw'
        'bG9nTmFtZSgpeyByZXR1cm4gJyc7IH0gZnVuY3Rpb24gcGxvZ0FsbHlMb3N0KCl7fSBmdW5jdGlv'
        'biBwbG9nRGVhdGgoKXt9IGZ1bmN0aW9uIHBsb2dTeW5jKCl7fQpmdW5jdGlvbiBzcGF3bkRlYnJp'
        'cygpe30KZnVuY3Rpb24gc3Bhd25SaW5nKCl7fQpmdW5jdGlvbiBzcGF3blNtb2tlKCl7fQpmdW5j'
        'dGlvbiBzZWNNb3VudCgpeyByZXR1cm4ge3g6cGxheWVyLngrMjAsIHk6cGxheWVyLnl9OyB9Ci8v'
        'IENhcGl0YWxzOiBvbmUgbW91bnQsIGEgZml4ZWQgdGFyZ2V0LCBzbyB3aGF0IGlzIHVuZGVyIHRl'
        'c3QgaXMgd2hlcmUgdGhlCi8vIHdhbGwgZW5kcyB1cCBhbmQgbm90IGhvdyBhIHR1cnJldCBwaWNr'
        'cyBhIHNoaXAuCnZhciBGTEFLX1RBUkdFVCA9IG51bGw7CmZ1bmN0aW9uIGVudE1vdW50cyhlKXsg'
        'cmV0dXJuIFt7eDplLngsIHk6ZS55fV07IH0KZnVuY3Rpb24gbmVhcmVzdEVuZW15KCl7IHJldHVy'
        'biBGTEFLX1RBUkdFVDsgfQpmdW5jdGlvbiBjYXBHdW5UYXJnZXQoKXsgcmV0dXJuIEZMQUtfVEFS'
        'R0VUOyB9CmZ1bmN0aW9uIHN1Yk9LKCl7IHJldHVybiB0cnVlOyB9CmZ1bmN0aW9uIHJuZFIocil7'
        'IHJldHVybiAoclswXStyWzFdKS8yOyB9Ci8vIExvY2tpbmcgYW5kIGltcGFjdC4gTE9DS19PSyBz'
        'dGFuZHMgZm9yIHRoZSBuZWJ1bGEgYW5kIHRoZSBFTVAgc3Rvcm06IG9mZiwKLy8gbm90aGluZyBj'
        'YW4gYmUgaGVsZC4gRXZlcnkgc2hpcCBpcyBhIDMwIHBvaW50IHNxdWFyZSwgYW5kIGEgaGl0IGlz'
        'Ci8vIHdyaXR0ZW4gZG93biBwZXIgc2hpcCBzbyB0aGUgdGVzdCBjYW4gYXNrIHdobyB3YXMgc3Ry'
        'dWNrLgp2YXIgTE9DS19PSyA9IHRydWUsIEhJVFMgPSBbXTsKZnVuY3Rpb24gY2FuTG9ja09uKG8p'
        'eyByZXR1cm4gTE9DS19PSyAmJiAhIW87IH0KZnVuY3Rpb24gZUJveChlKXsgcmV0dXJuIFtlLngt'
        'MTUsIGUueS0xNSwgMzAsIDMwXTsgfQpmdW5jdGlvbiBvdmVybGFwKGF4LGF5LGF3LGFoLGJ4LGJ5'
        'LGJ3LGJoKXsgcmV0dXJuIGF4PGJ4K2J3ICYmIGF4K2F3PmJ4ICYmIGF5PGJ5K2JoICYmIGF5K2Fo'
        'PmJ5OyB9CmZ1bmN0aW9uIGJ1bGxldE9uSHVsbCgpeyByZXR1cm4gdHJ1ZTsgfQpmdW5jdGlvbiBw'
        'bGF5ZXJPbmx5KCl7IHJldHVybiBmYWxzZTsgfQpmdW5jdGlvbiBkYW1hZ2VFbmVteShlLCBkKXsg'
        'ZS5ocCAtPSBkOyBISVRTLnB1c2goe2U6ZSwgZDpkfSk7IH0KZnVuY3Rpb24ga2lsbEVuZW15KGUs'
        'IGopeyBlLmRlYWQgPSB0cnVlOyBlbmVtaWVzLnNwbGljZShqLCAxKTsgfQovLyBTdWJzeXN0ZW1z'
        'OiBzdWJIaXQgaXMgdGhlIHJlYWwgb25lLCB0aGUgZ2VvbWV0cnkgYXJvdW5kIGl0IGlzIG5vdCB3'
        'aGF0IGlzCi8vIHVuZGVyIHRlc3QgaGVyZS4KZnVuY3Rpb24gc3ViUG9zKGUsIHMpeyByZXR1cm4g'
        'e3g6ZS54K3Mub3gsIHk6ZS55fTsgfQpmdW5jdGlvbiBzdWJBdChlLCBoeCwgaHkpewogIGxldCBi'
        'ZXN0PW51bGwsIGJkPUluZmluaXR5OwogIGZvcihjb25zdCBzIG9mIChlLnN1YnN8fFtdKSl7CiAg'
        'ICBpZihzLmRlYWQpIGNvbnRpbnVlOwogICAgY29uc3QgZD1NYXRoLmFicygoZS54K3Mub3gpLWh4'
        'KTsKICAgIGlmKGQ8YmQpeyBiZD1kOyBiZXN0PXM7IH0KICB9CiAgcmV0dXJuIChiZDw9MSkgPyBi'
        'ZXN0IDogbnVsbDsKfQpjb25zdCBTVUJfSFVMTF9CTEVFRCA9IDAuMjU7CiR7Y29uc3RzLmpvaW4o'
        'J1xuJyl9CiR7bmFtZXMubWFwKGZuKS5qb2luKCdcbicpfQoke2ZuKCdzdWJIaXQnKX0KYDsKCmNv'
        'bnN0IHZtID0gcmVxdWlyZSgndm0nKTsKY29uc3QgY3R4T2JqID0ge2NvbnNvbGUsIE1hdGgsIElu'
        'ZmluaXR5fTsKdm0uY3JlYXRlQ29udGV4dChjdHhPYmopOwp2bS5ydW5JbkNvbnRleHQoV09STEQs'
        'IGN0eE9iaik7CmNvbnN0IHJ1biA9IChjb2RlKT0+dm0ucnVuSW5Db250ZXh0KGNvZGUsIGN0eE9i'
        'aik7CmNvbnN0IGdldCA9IChuYW1lKT0+dm0ucnVuSW5Db250ZXh0KG5hbWUsIGN0eE9iaik7CmNv'
        'bnN0IHNldCA9IChuYW1lLCB2KT0+eyBjdHhPYmpbbmFtZV0gPSB2OyB9OwoKbGV0IGZhaWxzID0g'
        'MDsKZnVuY3Rpb24gb2sobGFiZWwsIGNvbmQpeyBjb25zb2xlLmxvZygoY29uZD8nICBvayAgICAn'
        'OicgIEZBSUwgICcpK2xhYmVsKTsgaWYoIWNvbmQpIGZhaWxzKys7IH0KY29uc3QgYnVsbGV0cyA9'
        'ICgpPT5nZXQoJ3BCdWxsZXRzJyk7CmNvbnN0IGNsZWFyID0gKCk9PnsgY3R4T2JqLnBCdWxsZXRz'
        'Lmxlbmd0aCA9IDA7IH07CmNvbnN0IGZpcmUgPSAoa2V5KT0+eyBydW4oInBsYXllci5wcmk9JyIr'
        'a2V5KyInOyBhcHBseUxvYWRvdXQoKSIpOyBjbGVhcigpOyBydW4oJ3BTaG9vdCgpJyk7IH07Cgpj'
        'b25zb2xlLmxvZygnVGhlIHN0YW5kYXJkIGd1biBpcyB0aGUgZ3VuIHRoZSBnYW1lIGhhZCcpOwpm'
        'aXJlKCdwcm9tZXRoZXVzJyk7CnsKICBjb25zdCBiID0gYnVsbGV0cygpOwogIG9rKCd0d28gYmFy'
        'cmVscywgdHdvIGJvbHRzJywgYi5sZW5ndGg9PT0yKTsKICBvaygnZWFjaCBjYXJyaWVzIHRoZSBm'
        'dWxsIHNoYXJlIG9mIHRoZSB2b2xsZXknLAogICAgIE1hdGguYWJzKGJbMF0uZG1nIC0gcnVuKCd2'
        'b2xsZXlEbWcoMiknKSkgPCAwLjAwMSk7CiAgb2soJ2FuZCBpdCBydW5zIHRvIHRoZSBlZGdlIG9m'
        'IHRoZSBmaWVsZCcsICFiWzBdLnBMaWZlKTsKICBvaygnaXQgbmVpdGhlciBwaWVyY2VzIG5vciBi'
        'dXJzdHMnLCAhYlswXS5waWVyY2UgJiYgIWJbMF0uZnVzZSk7Cn0KCmNvbnNvbGUubG9nKCdcblN0'
        'cmV1c2NodXNzOiBhIGNvbmUgZnJvbSBvbmUgdHJpZ2dlciBwdWxsJyk7CmZpcmUoJ3NjYXR0ZXIn'
        'KTsKewogIGNvbnN0IGIgPSBidWxsZXRzKCksIHcgPSBydW4oInByaURlZignc2NhdHRlcicpIik7'
        'CiAgb2soJ3NldmVuIHBlbGxldHMgcGVyIGJhcnJlbCcsIGIubGVuZ3RoID09PSAyKncucGVsbGV0'
        'cyk7CiAgY29uc3QgdG90YWwgPSBiLnJlZHVjZSgocyx4KT0+cyt4LmRtZywgMCk7CiAgb2soJ3Ro'
        'ZSB2b2xsZXkgaXMgc2hhcmVkIG91dCwgbm90IG11bHRpcGxpZWQnLAogICAgIE1hdGguYWJzKHRv'
        'dGFsIC0gcnVuKCd2b2xsZXlEbWcoMiknKSoyKncuZG1nKSA8IDAuMDEpOwogIC8vIFNsaWdodCBh'
        'Z2FpbnN0IHRoZSB2b2xsZXkgb2YgYSBzaW5nbGUgYmFycmVsLCB3aGljaCBpcyB3aGF0IGEgcGVs'
        'bGV0CiAgLy8gaGFzIHRvIGJlIGZvciB0aGUgY29uZSB0byBtZWFuIGFueXRoaW5nLgogIG9rKCdv'
        'bmUgcGVsbGV0IG9uIGl0cyBvd24gaXMgc2xpZ2h0JywgYlswXS5kbWcgPCBydW4oJ3ZvbGxleURt'
        'ZygyKScpKTsKICAvLyBBbmdsZXM6IHRoZSBjb25lIGhhcyB0byBiZSBhIGNvbmUsIGFuZCBpdCBo'
        'YXMgdG8gcG9pbnQgZm9yd2FyZC4KICBjb25zdCBhbmcgPSBiLm1hcCh4PT5NYXRoLmF0YW4yKHgu'
        'dnksIHgudngpKTsKICBjb25zdCBzcHJlYWQgPSBNYXRoLm1heCguLi5hbmcpIC0gTWF0aC5taW4o'
        'Li4uYW5nKTsKICBvaygndGhleSBsZWF2ZSBpbiBhIHNwcmVhZCwgbm90IGluIGEgbGluZScsIHNw'
        'cmVhZCA+IHcuc3ByZWFkKjAuNSk7CiAgb2soJ2FuZCB0aGUgc3ByZWFkIHN0YXlzIGluc2lkZSB3'
        'aGF0IHRoZSB0YWJsZSBhbGxvd3MnLCBzcHJlYWQgPD0gdy5zcHJlYWQqMS42KTsKICBvaygnYWxs'
        'IG9mIHRoZW0gc3RpbGwgZ28gZm9yd2FyZCcsIGFuZy5ldmVyeShhPT5NYXRoLmFicyhhKSA8IE1h'
        'dGguUEkvMikpOwogIC8vIHBMaWZlIGlzIHdob2xlIHN0ZXBzLCBzbyB0aGUgcmVhY2ggbGFuZHMg'
        'd2l0aGluIG9uZSBzdGVwIG9mIHRoZSB0YWJsZS4KICBvaygndGhlIHJlYWNoIGlzIHNob3J0Jywg'
        'YlswXS5wTGlmZT4wICYmIGJbMF0ucExpZmUqdy5zcGQgPD0gdy5yYW5nZSt3LnNwZCk7Cn0KCmNv'
        'bnNvbGUubG9nKCdcbkR1cmNoc2NobGFnIGlzIGdvbmUnKTsKewogIG9rKCdpdCBpcyBubyBsb25n'
        'ZXIgaW4gdGhlIHRhYmxlJywgcnVuKCdQUklNQVJJRVMnKS5ldmVyeSh3PT53LmtleSE9PSdwaWVy'
        'Y2UnKSk7CiAgcnVuKCJwbGF5ZXIucHJpPSdwaWVyY2UnOyBhcHBseUxvYWRvdXQoKSIpOwogIG9r'
        'KCdhIHNoaXAgdGhhdCBzdGlsbCBoYWQgaXQgZml0dGVkIGZhbGxzIGJhY2sgdG8gdGhlIFByb21l'
        'dGhldXMnLAogICAgIGdldCgncGxheWVyJykucHJpPT09J3Byb21ldGhldXMnKTsKICBvaygnYW5k'
        'IG5vdGhpbmcgaXMgbGVmdCBvZiB0aGUgcGllcmNpbmcgbWVjaGFuaXNtJywKICAgICAhL2JcLnBp'
        'ZXJjZS8udGVzdChzcmMpICYmICEvaGl0TGlzdC8udGVzdChzcmMpKTsKfQoKY29uc29sZS5sb2co'
        'J1xuVG9ybmFkbzogb25lIHByZXNzLCBmb3VyIHNlZWtlcnMsIGZvdXIgdGFyZ2V0cycpOwovLyBB'
        'IGZyZXNoIGZpZWxkOiBmb3VyIGVuZW1pZXMgYWhlYWQgb2YgdGhlIHNoaXAsIHNwcmVhZCB0b3Ag'
        'dG8gYm90dG9tLgpmdW5jdGlvbiBmaWVsZCh5cyl7CiAgcnVuKCdlbmVtaWVzLmxlbmd0aD0wOyBI'
        'SVRTLmxlbmd0aD0wOyBwQnVsbGV0cy5sZW5ndGg9MDsgTE9DS19PSz10cnVlJyk7CiAgZm9yKGNv'
        'bnN0IHkgb2YgeXMpIHJ1bignZW5lbWllcy5wdXNoKHt4OjUwMCwgeTonK3krJywgaHA6MTAwLCBk'
        'ZWFkOmZhbHNlfSknKTsKICBydW4oInBsYXllci5wcmk9J3Byb21ldGhldXMnOyBwbGF5ZXIuc2Vj'
        'PSd0b3JuYWRvJzsgcGxheWVyLnNoaXA9J2ZpdG90aCc7IGFwcGx5TG9hZG91dCgpOyBwbGF5ZXIu'
        'c2VjQW1tbz1wbGF5ZXIuc2VjTWF4OyBwbGF5ZXIuc2VjVGltZXI9MCIpOwp9Ci8vIFJ1bnMgdGhl'
        'IHJlYWwgZmxpZ2h0IGFuZCBpbXBhY3Qgcm91dGluZSwgdGhlIG9uZSB0aGUgZ2FtZSBydW5zIGV2'
        'ZXJ5IHN0ZXAuCmZ1bmN0aW9uIGZseShzdGVwcyl7IGZvcihsZXQgaT0wO2k8c3RlcHM7aSsrKXsg'
        'cnVuKCdmYysrJyk7IHJ1bigndXBkYXRlU2VjQnVsbGV0cygpJyk7IH0gfQp7CiAgY29uc3QgdyA9'
        'IHJ1bigic2VjRGVmKCd0b3JuYWRvJykiKTsKICBvaygnaXQgaXMgaW4gdGhlIHRhYmxlIGFzIGEg'
        'bWlzc2lsZScsICEhdyAmJiB3LmtleT09PSd0b3JuYWRvJyAmJiB3LmNscz09PSdtaXNzaWxlJyk7'
        'CiAgb2soJ2l0IG9wZW5zIGF0IDIyLDAwMCwgd2hlcmUgdGhlIER1cmNoc2NobGFnIHdhcycsIHcu'
        'dW5sb2NrPT09MjIwMDApOwogIG9rKCdhIGZpZ2h0ZXIgaXMgb2ZmZXJlZCBpdCcsIHJ1bigic2Vj'
        'b25kYXJpZXNGb3IoJ2ZpdG90aCcpIikuc29tZSh4PT54LmtleT09PSd0b3JuYWRvJykpOwogIG9r'
        'KCdhIGJvbWJlciBpcyBub3QnLCBydW4oInNlY29uZGFyaWVzRm9yKCdib29zaXJpcycpIikuZXZl'
        'cnkoeD0+eC5rZXkhPT0ndG9ybmFkbycpKTsKICBvaygndGhlIHJlYXJtIHBhbmVsIHNob3dzIHRo'
        'ZSBzYWx2bywgbm90IG9uZSBtaXNzaWxlJywKICAgICBydW4oInJtVmFsdWUoc2VjRGVmKCd0b3Ju'
        'YWRvJyksICdkbWcnLCBmYWxzZSkiKT09PXcuc3dhcm0rJ1x1MDBkNycrdy5kbWcpOwp9CnsKICBm'
        'aWVsZChbMTUwLCAyMjAsIDI5MCwgMzYwXSk7CiAgY29uc3QgYmVmb3JlID0gZ2V0KCdwbGF5ZXIn'
        'KS5zZWNBbW1vOwogIHJ1bignZmlyZVNlY29uZGFyeSgpJyk7CiAgY29uc3QgYiA9IGJ1bGxldHMo'
        'KS5maWx0ZXIoeD0+eC5zZWMpOwogIG9rKCdmb3VyIG1pc3NpbGVzIGxlYXZlJywgYi5sZW5ndGg9'
        'PT00KTsKICBvaygnYW5kIHRoZXkgY29zdCBvbmUgcm91bmQsIG5vdCBmb3VyJywgZ2V0KCdwbGF5'
        'ZXInKS5zZWNBbW1vPT09YmVmb3JlLTEpOwogIG9rKCdldmVyeSBvbmUgb2YgdGhlbSBzZWVrcycs'
        'IGIuZXZlcnkoeD0+eC5ob21pbmcpKTsKICBvaygnZWFjaCBoYXMgYSBkaWZmZXJlbnQgdGFyZ2V0'
        'JywgbmV3IFNldChiLm1hcCh4PT54LnRhcmdldCkpLnNpemU9PT00KTsKICBjb25zdCBhbmcgPSBi'
        'Lm1hcCh4PT5NYXRoLmF0YW4yKHgudnksIHgudngpKTsKICBvaygndGhleSBsZWF2ZSBpbiBhIGZh'
        'biwgbm90IGluIGEgbGluZScsIE1hdGgubWF4KC4uLmFuZyktTWF0aC5taW4oLi4uYW5nKSA+IDAu'
        'NSk7CiAgZmx5KDIwMCk7CiAgY29uc3Qgc3RydWNrID0gbmV3IFNldChnZXQoJ0hJVFMnKS5tYXAo'
        'aD0+aC5lLnkpKTsKICBvaygnaW4gZmxpZ2h0LCBhbGwgZm91ciB0YXJnZXRzIGFyZSBzdHJ1Y2sg'
        'LSBub3QgdGhlIG5lYXJlc3Qgb25lIGZvdXIgdGltZXMnLAogICAgIHN0cnVjay5zaXplPT09NCk7'
        'CiAgb2soJ2ZvdXIgaW1wYWN0cywgZWFjaCBjYXJyeWluZyBvbmUgbWlzc2lsZVwncyBkYW1hZ2Un'
        'LAogICAgIGdldCgnSElUUycpLmxlbmd0aD09PTQgJiYgZ2V0KCdISVRTJykuZXZlcnkoaD0+aC5k'
        'PT09cnVuKCJzZWNEZWYoJ3Rvcm5hZG8nKS5kbWciKSkpOwp9CnsKICBmaWVsZChbMjAwLCAzMDBd'
        'KTsKICBydW4oJ2ZpcmVTZWNvbmRhcnkoKScpOwogIGZseSgyMDApOwogIGNvbnN0IHlzID0gZ2V0'
        'KCdISVRTJykubWFwKGg9PmguZS55KTsKICBvaygndHdvIHRhcmdldHM6IHRoZSBzYWx2byBzcGxp'
        'dHMgb3ZlciBib3RoIGluc3RlYWQgb2YgZHJvcHBpbmcgbWlzc2lsZXMnLAogICAgIHlzLmZpbHRl'
        'cih5PT55PT09MjAwKS5sZW5ndGg9PT0yICYmIHlzLmZpbHRlcih5PT55PT09MzAwKS5sZW5ndGg9'
        'PT0yKTsKfQp7CiAgLy8gQSB0YXJnZXQgdGhhdCBkaWVzIG9uIHRoZSB3YXk6IGl0cyBtaXNzaWxl'
        'IGhhcyB0byBmaW5kIGEgZnJlZSBvbmUuCiAgZmllbGQoWzE1MCwgMjUwLCAzNTBdKTsKICBydW4o'
        'InBsYXllci5zZWNUaW1lcj0wIik7CiAgcnVuKCdmaXJlU2Vjb25kYXJ5KCknKTsKICBjb25zdCBs'
        'b3N0ID0gcnVuKCdlbmVtaWVzWzBdJyk7CiAgZmx5KDMpOwogIHJ1bignZW5lbWllc1swXS5kZWFk'
        'PXRydWU7IGVuZW1pZXMuc3BsaWNlKDAsMSknKTsKICBmbHkoMjAwKTsKICBvaygnYSBtaXNzaWxl'
        'IHdob3NlIHRhcmdldCBpcyBnb25lIGRvZXMgbm90IGZseSBvbiBpbnRvIG5vdGhpbmcnLAogICAg'
        'IGdldCgnSElUUycpLmxlbmd0aD09PTQpOwogIG9rKCdhbmQgaXQgbmV2ZXIgc3RyaWtlcyB0aGUg'
        'ZGVhZCBvbmUnLCBnZXQoJ0hJVFMnKS5ldmVyeShoPT5oLmUhPT1sb3N0KSk7Cn0KewogIC8vIE5v'
        'IGxvY2sgaW4gYSBuZWJ1bGEgb3IgYSBzdG9ybTogc3RyYWlnaHQgZmxpZ2h0LCBsaWtlIGV2ZXJ5'
        'IG90aGVyIHNlZWtlci4KICBmaWVsZChbMTUwLCAyNTAsIDM1MCwgNDUwXSk7CiAgcnVuKCdMT0NL'
        'X09LPWZhbHNlJyk7CiAgcnVuKCdmaXJlU2Vjb25kYXJ5KCknKTsKICBjb25zdCBiID0gYnVsbGV0'
        'cygpLmZpbHRlcih4PT54LnNlYyk7CiAgb2soJ3dpdGhvdXQgYSBsb2NrIHRoZSBtaXNzaWxlcyBs'
        'ZWF2ZSB3aXRoIG5vIHRhcmdldCcsIGIuZXZlcnkoeD0+eC50YXJnZXQ9PT1udWxsKSk7CiAgY29u'
        'c3QgdjAgPSBiLm1hcCh4PT54LnZ5KTsKICBmbHkoMTApOwogIG9rKCdhbmQgdGhleSBrZWVwIHRo'
        'ZWlyIGhlYWRpbmcnLCBidWxsZXRzKCkuZmlsdGVyKHg9Pnguc2VjKS5ldmVyeSgoeCxpKT0+TWF0'
        'aC5hYnMoeC52eS12MFtpXSk8MWUtOSkpOwp9CnsKICAvLyBPdGhlciBzZWVrZXJzIGFyZSB1bmNo'
        'YW5nZWQ6IHRoZSBNWC02NCBzdGlsbCBnb2VzIGZvciB0aGUgbmVhcmVzdC4KICBmaWVsZChbMjQw'
        'LCA0MDBdKTsKICBydW4oInBsYXllci5zZWM9J214NjQnOyBhcHBseUxvYWRvdXQoKTsgcGxheWVy'
        'LnNlY0FtbW89NTsgcGxheWVyLnNlY1RpbWVyPTAiKTsKICBydW4oJ2ZpcmVTZWNvbmRhcnkoKScp'
        'OwogIG9rKCd0aGUgTVgtNjQgc3RpbGwgZmlyZXMgYSBzaW5nbGUgbWlzc2lsZScsIGJ1bGxldHMo'
        'KS5maWx0ZXIoeD0+eC5zZWMpLmxlbmd0aD09PTEpOwogIGZseSgyMDApOwogIG9rKCdhbmQgaXQg'
        'c3RpbGwgdGFrZXMgdGhlIG5lYXJlc3QnLCBnZXQoJ0hJVFMnKS5sZW5ndGg9PT0xICYmIGdldCgn'
        'SElUUycpWzBdLmUueT09PTI0MCk7Cn0KCmNvbnNvbGUubG9nKCdcbkRhbnRlOiBhIGJ1cnN0IG9u'
        'IGltcGFjdCBhbmQgYSBidXJzdCBieSBpdHNlbGYnKTsKZmlyZSgnZGFudGUnKTsKewogIGNvbnN0'
        'IGIgPSBidWxsZXRzKCksIHcgPSBydW4oInByaURlZignZGFudGUnKSIpOwogIG9rKCdpdCBjYXJy'
        'aWVzIGEgZnVzZScsIGJbMF0uZnVzZSA+IDApOwogIG9rKCd0aGUgZnVzZSBpcyB0aGUgZGlzdGFu'
        'Y2UgdHVybmVkIGludG8gc3RlcHMnLAogICAgIE1hdGguYWJzKGJbMF0uZnVzZSAtIE1hdGgucm91'
        'bmQody5mdXNlL3cuc3BkKSkgPD0gMSk7CiAgb2soJ3RoZSBmdXNlIGdvZXMgb2ZmIGJlZm9yZSB0'
        'aGUgcmVhY2ggcnVucyBvdXQnLAogICAgIGJbMF0uZnVzZSA8IGJbMF0ucExpZmUgfHwgIWJbMF0u'
        'cExpZmUpOwogIG9rKCd0aGUgcm91bmQga25vd3Mgd2hpY2ggd2VhcG9uIG1hZGUgaXQsIHNvIHRo'
        'ZSBidXJzdCBjYW4gYmUgbG9va2VkIHVwJywKICAgICBiWzBdLndwbj09PSdkYW50ZScpOwogIG9r'
        'KCd0aGUgZnVzZSBpcyBjb3VudGVkIGRvd24gYW5kIGJ1cnN0IHdoZXJlIGl0IHN0YW5kcycsCiAg'
        'ICAgL2lmXChiXC5mdXNlICYmIC0tYlwuZnVzZTw9MFwpLy50ZXN0KHNyYykpOwp9CnsKICAvLyBU'
        'aGUgYnVyc3QgaXRzZWxmLgogIGNsZWFyKCk7CiAgcnVuKCJzaGFyZEJ1cnN0KDQwMCwgMjUwLCA5'
        'LCA1LCAzLjQsIDcwLCAnI2ZmZicsICdyZ2JhKDAsMCwwLDApJykiKTsKICBjb25zdCBzID0gYnVs'
        'bGV0cygpOwogIG9rKCduaW5lIHNoYXJkcyBsZWF2ZSB0aGUgcG9pbnQnLCBzLmxlbmd0aD09PTkp'
        'OwogIG9rKCdldmVyeSBvbmUgb2YgdGhlbSBjYXJyaWVzIHRoZSBkYW1hZ2UgaXQgd2FzIGdpdmVu'
        'Jywgcy5ldmVyeSh4PT54LmRtZz09PTUpKTsKICBvaygnYWxsIGF0IHRoZSBzYW1lIHNwZWVkJywg'
        'cy5ldmVyeSh4PT5NYXRoLmFicyhNYXRoLmh5cG90KHgudngseC52eSktMy40KTwwLjAwMSkpOwog'
        'IG9rKCdhbmQgdGhleSBhcmUgc2hvcnQgbGl2ZWQnLCBzLmV2ZXJ5KHg9PngucExpZmU+MCAmJiB4'
        'LnBMaWZlPD1NYXRoLmNlaWwoNzAvMy40KSkpOwogIC8vIFN0YXIgc2hhcGVkIG1lYW5zIHRoZSBk'
        'aXJlY3Rpb25zIGNhbmNlbCBvdXQuIEEgY29uZSB3b3VsZCBub3QuCiAgY29uc3Qgc3ggPSBzLnJl'
        'ZHVjZSgoYSx4KT0+YSt4LnZ4LCAwKSwgc3kgPSBzLnJlZHVjZSgoYSx4KT0+YSt4LnZ5LCAwKTsK'
        'ICBvaygnc3RhciBzaGFwZWQsIG5vdCB0aHJvd24gb25lIHdheScsIE1hdGguYWJzKHN4KTwwLjAw'
        'MSAmJiBNYXRoLmFicyhzeSk8MC4wMDEpOwogIG9rKCd0aGV5IGFsbCBzdGFydCB3aGVyZSB0aGUg'
        'cm91bmQgd2FzJywgcy5ldmVyeSh4PT54Lng9PT00MDAgJiYgeC55PT09MjUwKSk7Cn0KCmNvbnNv'
        'bGUubG9nKCdcbkluZnlybm86IHRoZSBidXR0b24gYmVsb25ncyB0byB0aGUgcm91bmQgaW4gdGhl'
        'IGFpcicpOwp7CiAgcnVuKCJwbGF5ZXIucHJpPSdwcm9tZXRoZXVzJzsgcGxheWVyLnNlYz0naW5m'
        'eXJubyc7IGFwcGx5TG9hZG91dCgpOyBwbGF5ZXIuc2VjQW1tbz02OyBwbGF5ZXIuc2VjVGltZXI9'
        'MCIpOwogIGNsZWFyKCk7CiAgcnVuKCdmaXJlU2Vjb25kYXJ5KCknKTsKICBvaygnb25lIHJvdW5k'
        'IGxlYXZlcycsIGJ1bGxldHMoKS5sZW5ndGg9PT0xKTsKICBvaygnaXQgaXMgZmxhZ2dlZCBhcyBv'
        'bmUgdGhhdCBjYW4gYmUgYnVyc3QnLCBidWxsZXRzKClbMF0uYnVyc3Q9PT10cnVlKTsKICBvaygn'
        'YW5kIGl0IGRvZXMgbm90IHNlZWsnLCBidWxsZXRzKClbMF0uaG9taW5nPT09ZmFsc2UpOwogIG9r'
        'KCdhIHJvdW5kIHdhcyB0YWtlbiBmcm9tIHRoZSByYWNrJywgZ2V0KCdwbGF5ZXInKS5zZWNBbW1v'
        'PT09NSk7CiAgLy8gUHJlc3NpbmcgYWdhaW4gbXVzdCBidXJzdCBpdCwgbm90IGZpcmUgYW5vdGhl'
        'ci4KICBydW4oJ3BsYXllci5zZWNUaW1lcj0wJyk7CiAgcnVuKCdmaXJlU2Vjb25kYXJ5KCknKTsK'
        'ICBjb25zdCBhZnRlciA9IGJ1bGxldHMoKTsKICBvaygndGhlIHNlY29uZCBwcmVzcyBkb2VzIG5v'
        'dCBmaXJlIGFub3RoZXInLAogICAgIGFmdGVyLmV2ZXJ5KGI9PiFiLnNlYykgKTsKICBvaygnaXQg'
        'YnVyc3RzIGludG8gc2hyYXBuZWwgaW5zdGVhZCcsIGFmdGVyLmxlbmd0aD09PXJ1bigic2VjRGVm'
        'KCdpbmZ5cm5vJykuc2hhcmRzIikpOwogIG9rKCdhbmQgY29zdHMgbm8gc2Vjb25kIHJvdW5kJywg'
        'Z2V0KCdwbGF5ZXInKS5zZWNBbW1vPT09NSk7CiAgb2soJ3dpdGggb25lIGdvbmUsIHRoZSBidXR0'
        'b24gZmlyZXMgYWdhaW4nLCBydW4oJ2xpdmVCdXJzdFJvdW5kKCknKT09PW51bGwpOwp9CnsKICAv'
        'LyBOZXZlciBwcmVzc2VkOiBpdCBoYXMgdG8gZ2l2ZSBvdXQgcmF0aGVyIHRoYW4gYnVyc3QgZm9y'
        'IGZyZWUuCiAgcnVuKCJwbGF5ZXIuc2VjQW1tbz02OyBwbGF5ZXIuc2VjVGltZXI9MCIpOwogIGNs'
        'ZWFyKCk7CiAgcnVuKCdmaXJlU2Vjb25kYXJ5KCknKTsKICBjb25zdCBiID0gYnVsbGV0cygpWzBd'
        'OwogIG9rKCdpdCBjYXJyaWVzIGEgZmluaXRlIHJlYWNoJywgYi5saWZlPjApOwogIG9rKCd3aGlj'
        'aCBpcyB0aGUgdGFibGUgdmFsdWUnLCBiLmxpZmU9PT1ydW4oInNlY0RlZignaW5meXJubycpLmxp'
        'ZmUiKSk7Cn0KCmNvbnNvbGUubG9nKCdcblN0aWxldHRvOiB0aGUgd2FyaGVhZCBnb2VzIGluc2lk'
        'ZScpOwp7CiAgY29uc3Qgc3ViID0gKGxhYmVsLCBveCwgaHApPT4oe2xhYmVsOmxhYmVsLCBveDpv'
        'eCwgaHA6aHAsIGRlYWQ6ZmFsc2V9KTsKICBjb25zdCBzaGlwID0ge3g6NDAwLCB5OjI1MCwgc2lk'
        'ZTonZW5lbXknLAogICAgICAgICAgICAgICAgc3Viczpbc3ViKCdFTkdJTkVTJywgLTQwLCAzMCks'
        'IHN1YignTkFWSUdBVElPTicsIDQwLCAzMCldfTsKICAvLyBJbXBhY3QgbmVhciB0aGUgYm93LCBl'
        'bmdpbmVzIGFyZSBhdCB0aGUgc3Rlcm46IGEgd2FyaGVhZCB0aGF0IG9ubHkgaGl0CiAgLy8gd2hh'
        'dCBsYXkgdW5kZXIgaXQgd291bGQgd2FzdGUgaXRzZWxmIG9uIHRoZSBodWxsLgogIHNldCgnX2Un'
        'LCBzaGlwKTsKICBjb25zdCBibGVlZCA9IHJ1bigic3ViU3RyaWtlKF9lLCA3MCwgNDYwLCAyNTAp'
        'Iik7CiAgb2soJ3RoZSBuZWFyZXN0IGxpdmluZyBzdWJzeXN0ZW0gdGFrZXMgaXQnLCBzaGlwLnN1'
        'YnNbMV0uaHAgPD0gMCB8fCBzaGlwLnN1YnNbMV0uZGVhZCk7CiAgb2soJ2FuZCBpdCBpcyB0aGUg'
        'b25lIG5lYXJlc3QgdGhlIGltcGFjdCcsIHNoaXAuc3Vic1swXS5ocCA9PT0gMzApOwogIG9rKCdv'
        'bmx5IHRoZSBibGVlZCBpcyBsZWZ0IGZvciB0aGUgaHVsbCcsIGJsZWVkIDwgNzAgJiYgYmxlZWQg'
        'PiAwKTsKfQp7CiAgY29uc3Qgc2hpcCA9IHt4OjQwMCwgeToyNTAsIHNpZGU6J2VuZW15JywKICAg'
        'ICAgICAgICAgICAgIHN1YnM6W3tsYWJlbDonRU5HSU5FUycsIG94Oi00MCwgaHA6MzAsIGRlYWQ6'
        'dHJ1ZX1dfTsKICBzZXQoJ19lJywgc2hpcCk7CiAgb2soJ25vdGhpbmcgbGVmdCB0byB3cmVjazog'
        'dGhlIGZ1bGwgd2FyaGVhZCBnb2VzIHRvIHRoZSBodWxsJywKICAgICBydW4oInN1YlN0cmlrZShf'
        'ZSwgNzAsIDQwMCwgMjUwKSIpPT09NzApOwogIHNldCgnX2UnLCB7eDo0MDAsIHk6MjUwLCBzaWRl'
        'OidlbmVteSd9KTsKICBvaygnYSBzaGlwIHdpdGggbm8gc3Vic3lzdGVtcyBhdCBhbGwgaXMgdGhl'
        'IHNhbWUnLAogICAgIHJ1bigic3ViU3RyaWtlKF9lLCA3MCwgNDAwLCAyNTApIik9PT03MCk7Cn0K'
        'ewogIC8vIEludG8gYSBzeXN0ZW0gaXQgaGl0cyA1LjUgdGltZXMgYXMgaGFyZDogb25lIGJvbWIs'
        'IG9uZSBjcnVpc2VyIHN5c3RlbS4KICBjb25zdCBzaGlwID0ge3g6NDAwLCB5OjI1MCwgc2lkZTon'
        'ZW5lbXknLCBzdWJzOlt7bGFiZWw6J0VOR0lORVMnLCBveDowLCBocDozNzAsIGRlYWQ6ZmFsc2V9'
        'XX07CiAgc2V0KCdfZScsIHNoaXApOwogIGNvbnN0IGJsZWVkID0gcnVuKCJzdWJTdHJpa2UoX2Us'
        'IDcwLCA0MDAsIDI1MCkiKTsKICBvaygnb25lIFN0aWxldHRvIHRha2VzIGEgMzcwIHBvaW50IHN5'
        'c3RlbScsIHNoaXAuc3Vic1swXS5kZWFkID09PSB0cnVlKTsKICBvaygndGhlIGh1bGwgc3RpbGwg'
        'Z2V0cyBvbmx5IHRoZSBwbGFpbiBibGVlZCcsIE1hdGguYWJzKGJsZWVkIC0gNzAqMC4yNSkgPCAx'
        'ZS05KTsKfQpvaygndGhlIHNlY29uZGFyeSBpbXBhY3QgYXNrcyB0aGUgd2VhcG9uLCBub3QgdGhl'
        'IHByb2plY3RpbGUgc2hhcGUnLAogICAvc3cgJiYgc3dcLnN1YnNcKSBkYW1hZ2VFbmVteVwoZSxz'
        'dWJTdHJpa2UvLnRlc3Qoc3JjKSk7Cgpjb25zb2xlLmxvZygnXG5XaGF0IGEgaHVsbCBtYXkgY2Fy'
        'cnkgaXMgdW5jaGFuZ2VkJyk7CnsKICBydW4oInBsYXllci5zaGlwPSdmaXRvdGgnOyBhcHBseUxv'
        'YWRvdXQoKSIpOwogIG9rKCdhIGZpZ2h0ZXIgaXMgb2ZmZXJlZCB0aGUgSW5meXJubyBidXQgbm90'
        'IHRoZSBTdGlsZXR0bycsCiAgICAgcnVuKCJzZWNvbmRhcmllc0ZvcignZml0b3RoJykiKS5zb21l'
        'KHc9Pncua2V5PT09J2luZnlybm8nKSAmJgogICAgIHJ1bigic2Vjb25kYXJpZXNGb3IoJ2ZpdG90'
        'aCcpIikuZXZlcnkodz0+dy5rZXkhPT0nc3RpbGV0dG8nKSk7CiAgb2soJ2FuZCBhIGJvbWJlciB0'
        'aGUgb3RoZXIgd2F5IHJvdW5kJywKICAgICBydW4oInNlY29uZGFyaWVzRm9yKCdib29zaXJpcycp'
        'Iikuc29tZSh3PT53LmtleT09PSdzdGlsZXR0bycpICYmCiAgICAgcnVuKCJzZWNvbmRhcmllc0Zv'
        'cignYm9vc2lyaXMnKSIpLmV2ZXJ5KHc9Pncua2V5IT09J2luZnlybm8nKSk7Cn0KCmNvbnNvbGUu'
        'bG9nKCdcbkNhcGl0YWwgZmxhazogYSB3YWxsLCBub3QgYSBzaG90Jyk7CnsKICBvaygnYSBjcnVp'
        'c2VyIGNhcnJpZXMgb25lJywgcnVuKCJmbGFrSGFzKHt0eXBlOidjcnVpc2VyJ30pIik9PT10cnVl'
        'KTsKICBvaygnc28gZG8gY29ydmV0dGVzIGFuZCBkZXN0cm95ZXJzJywKICAgICBydW4oImZsYWtI'
        'YXMoe3R5cGU6J2NvcnZldHRlJ30pIik9PT10cnVlICYmIHJ1bigiZmxha0hhcyh7dHlwZTonZGVz'
        'dHJveWVyJ30pIik9PT10cnVlKTsKICBvaygnYSBmaWdodGVyIGRvZXMgbm90JywgcnVuKCJmbGFr'
        'SGFzKHt0eXBlOidmaWdodGVyJ30pIik9PT1mYWxzZSk7CiAgb2soJ25vciBhIGJvbWJlciBvciBh'
        'IGZyZWlnaHRlcicsCiAgICAgcnVuKCJmbGFrSGFzKHt0eXBlOidib21iZXInfSkiKT09PWZhbHNl'
        'ICYmIHJ1bigiZmxha0hhcyh7dHlwZTonZnJlaWdodGVyJ30pIik9PT1mYWxzZSk7Cn0KewogIC8v'
        'IFRoZSB3YWxsIG11c3Qgc3RhbmQgb3V0IGluIGZyb250LCBub3Qgb24gdGhlIGd1biBhbmQgbm90'
        'IG9mZiB0aGUgZmFyIGVkZ2UuCiAgY29uc3QgTUlOID0gcnVuKCdGTEFLX01JTicpLCBNQVggPSBy'
        'dW4oJ0ZMQUtfRElTVCcpLCBLRUVQID0gcnVuKCdGTEFLX0VER0VfS0VFUCcpOwogIG9rKCdhIHRh'
        'cmdldCBmdXJ0aGVyIHRoYW4gdGhlIGd1biByZWFjaGVzOiB0aGUgd2FsbCBzdG9wcyBhdCBpdHMg'
        'bGltaXQnLAogICAgIHJ1bignZmxha1JlYWNoKDcwMCwgMjUwLCBNYXRoLlBJLCA5MDApJykgPT09'
        'IE1BWCk7CiAgb2soJ2EgdGFyZ2V0IHNpdHRpbmcgb24gdGhlIG11enpsZTogaXQgbmV2ZXIgYnVy'
        'c3RzIG5lYXJlciB0aGFuIHRoZSBtaW5pbXVtJywKICAgICBydW4oJ2ZsYWtSZWFjaCg3MDAsIDI1'
        'MCwgTWF0aC5QSSwgNSknKSA9PT0gTUlOKTsKICAvLyBGaXJpbmcgbGVmdCBmcm9tIHg9NzAwIGF0'
        'IGZ1bGwgcmVhY2ggd291bGQgYnVyc3QgYXQgNDAwLCB3aGljaCBpcyBmaW5lLgogIC8vIEZpcmlu'
        'ZyBsZWZ0IGZyb20geD0zMDAgd291bGQgYnVyc3QgYXQgMCAtIG9mZiB0aGUgZmllbGQuIEl0IGhh'
        'cyB0byBwdWxsIGluLgogIGNvbnN0IGQgPSBydW4oJ2ZsYWtSZWFjaCgzMDAsIDI1MCwgTWF0aC5Q'
        'SSwgOTAwKScpOwogIG9rKCdhIGd1biBjbG9zZSB0byB0aGUgZmFyIGVkZ2UgcHVsbHMgaXRzIHdh'
        'bGwgaW4nLCBkIDwgTUFYKTsKICBvaygnYW5kIHRoZSBidXJzdCBsYW5kcyBpbnNpZGUgdGhlIGZp'
        'ZWxkIHdpdGggcm9vbSB0byBzcGFyZScsCiAgICAgMzAwIC0gZCA+PSBLRUVQIC0gMjIpOwp9CnsK'
        'ICAvLyBTaHJhcG5lbCwgb24gdGhlIHJpZ2h0IHNpZGUgb2YgdGhlIGZpZ2h0LgogIHNldCgnRkxB'
        'S19UQVJHRVQnLCB7eDoxMDAsIHk6MjUwfSk7CiAgcnVuKCdwQnVsbGV0cy5sZW5ndGg9MDsgZUJ1'
        'bGxldHMubGVuZ3RoPTAnKTsKICBydW4oImZsYWtCdXJzdCg0MDAsIDI1MCwgdHJ1ZSwgJ3Zhc3Vk'
        'YW4nKSIpOwogIGNvbnN0IHAgPSBnZXQoJ3BCdWxsZXRzJyk7CiAgb2soJ2FuIGFsbGllZCBndW4g'
        'dGhyb3dzIGl0cyBzaHJhcG5lbCBhdCB0aGUgZW5lbWllcycsCiAgICAgcC5sZW5ndGg9PT1ydW4o'
        'J0ZMQUtfU0hBUkRTJykgJiYgcC5ldmVyeShiPT5iLmFsbHk9PT10cnVlKSAmJiBnZXQoJ2VCdWxs'
        'ZXRzJykubGVuZ3RoPT09MCk7CiAgY29uc3Qgc3ggPSBwLnJlZHVjZSgoYSxiKT0+YStiLnZ4LDAp'
        'LCBzeSA9IHAucmVkdWNlKChhLGIpPT5hK2IudnksMCk7CiAgb2soJ3N0YXIgc2hhcGVkLCBub3Qg'
        'dGhyb3duIG9uZSB3YXknLCBNYXRoLmFicyhzeCk8MC4wMDEgJiYgTWF0aC5hYnMoc3kpPDAuMDAx'
        'KTsKICBvaygnYW5kIGl0IGdpdmVzIG91dCByYXRoZXIgdGhhbiBmbHlpbmcgdG8gdGhlIGVkZ2Un'
        'LCBwLmV2ZXJ5KGI9PmIucExpZmU+MCkpOwogIHJ1bigncEJ1bGxldHMubGVuZ3RoPTA7IGVCdWxs'
        'ZXRzLmxlbmd0aD0wJyk7CiAgcnVuKCJmbGFrQnVyc3QoNDAwLCAyNTAsIGZhbHNlLCAnc2hpdmFu'
        'JykiKTsKICBvaygnYW4gZW5lbXkgZ3VuIHRoZSBvdGhlciB3YXkgcm91bmQnLAogICAgIGdldCgn'
        'ZUJ1bGxldHMnKS5sZW5ndGg9PT1ydW4oJ0ZMQUtfU0hBUkRTJykgJiYgZ2V0KCdwQnVsbGV0cycp'
        'Lmxlbmd0aD09PTApOwogIG9rKCd3aXRoIGEgbGlmZSBvZiBpdHMgb3duIHRvbycsIGdldCgnZUJ1'
        'bGxldHMnKS5ldmVyeShiPT5iLmVMaWZlPjApKTsKfQp7CiAgLy8gVGhlIGd1biBpdHNlbGY6IG9u'
        'ZSByb3VuZCwgb24gYSBmdXNlLCBmcm9tIHRoZSBtb3VudC4KICBzZXQoJ0ZMQUtfVEFSR0VUJywg'
        'e3g6MTAwLCB5OjI1MH0pOwogIHJ1bigncEJ1bGxldHMubGVuZ3RoPTA7IGVCdWxsZXRzLmxlbmd0'
        'aD0wJyk7CiAgY29uc3QgY3J1aXNlciA9IHt0eXBlOidjcnVpc2VyJywgeDo2MDAsIHk6MjUwLCBm'
        'YWN0aW9uOid2YXN1ZGFuJywgZGVhZDpmYWxzZSwgd2FycDowLCB3YXJwT3V0OjB9OwogIHNldCgn'
        'X2MnLCBjcnVpc2VyKTsKICBydW4oJ19jLmZsYWtUID0gMTsgZmxha0ZpcmUoX2MsIHRydWUpJyk7'
        'CiAgY29uc3QgYiA9IGdldCgncEJ1bGxldHMnKTsKICBvaygnb25lIHJvdW5kIGxlYXZlcywgbm90'
        'IGEgYnVyc3QgYXQgdGhlIG11enpsZScsIGIubGVuZ3RoPT09MSk7CiAgb2soJ2l0IGNhcnJpZXMg'
        'YSBmdXNlJywgYlswXS5mdXNlID4gMCk7CiAgb2soJ2l0IGlzIGZsYWdnZWQgYXMgZmxhayBzbyB0'
        'aGUgZnVzZSBrbm93cyB3aGF0IHRvIGRvJywgYlswXS5mbGFrPT09dHJ1ZSk7CiAgb2soJ2FuZCBp'
        'dCB0cmF2ZWxzIHRvd2FyZHMgdGhlIHRhcmdldCcsIGJbMF0udnggPCAwKTsKICBvaygndGhlIGNs'
        'b2NrIGlzIHJlc2V0IHJhdGhlciB0aGFuIGZpcmluZyBldmVyeSBzdGVwJywgY3J1aXNlci5mbGFr'
        'VCA+IDEpOwogIHJ1bigncEJ1bGxldHMubGVuZ3RoPTAnKTsKICBydW4oJ2ZsYWtGaXJlKF9jLCB0'
        'cnVlKScpOwogIG9rKCdhbmQgaXQgZG9lcyBub3QgZmlyZSBhZ2FpbiBvbiB0aGUgbmV4dCBzdGVw'
        'JywgZ2V0KCdwQnVsbGV0cycpLmxlbmd0aD09PTApOwp9CnsKICAvLyBBIHdyZWNrIG9yIGEgc2hp'
        'cCBzdGlsbCBpbiB0aGUgdm9ydGV4IGRvZXMgbm90IHNob290LgogIHNldCgnRkxBS19UQVJHRVQn'
        'LCB7eDoxMDAsIHk6MjUwfSk7CiAgcnVuKCdwQnVsbGV0cy5sZW5ndGg9MCcpOwogIHNldCgnX2Mn'
        'LCB7dHlwZTonY3J1aXNlcicsIHg6NjAwLCB5OjI1MCwgZmFjdGlvbjondmFzdWRhbicsIGRlYWQ6'
        'dHJ1ZSwgd2FycDowLCB3YXJwT3V0OjAsIGZsYWtUOjF9KTsKICBydW4oJ2ZsYWtGaXJlKF9jLCB0'
        'cnVlKScpOwogIHNldCgnX2MnLCB7dHlwZTonY3J1aXNlcicsIHg6NjAwLCB5OjI1MCwgZmFjdGlv'
        'bjondmFzdWRhbicsIGRlYWQ6ZmFsc2UsIHdhcnA6MzAsIHdhcnBPdXQ6MCwgZmxha1Q6MX0pOwog'
        'IHJ1bignZmxha0ZpcmUoX2MsIHRydWUpJyk7CiAgb2soJ25laXRoZXIgYSB3cmVjayBub3IgYSBz'
        'aGlwIHN0aWxsIHdhcnBpbmcgaW4gZmlyZXMnLCBnZXQoJ3BCdWxsZXRzJykubGVuZ3RoPT09MCk7'
        'CiAgc2V0KCdfYycsIHt0eXBlOidmaWdodGVyJywgeDo2MDAsIHk6MjUwLCBmYWN0aW9uOid2YXN1'
        'ZGFuJywgZGVhZDpmYWxzZSwgd2FycDowLCB3YXJwT3V0OjAsIGZsYWtUOjF9KTsKICBydW4oJ2Zs'
        'YWtGaXJlKF9jLCB0cnVlKScpOwogIG9rKCdhbmQgYSBmaWdodGVyIGhhcyBubyBmbGFrIGd1biB0'
        'byBmaXJlJywgZ2V0KCdwQnVsbGV0cycpLmxlbmd0aD09PTApOwp9Cm9rKCdib3RoIHNpZGVzIHJ1'
        'biB0aGUgZ3VuJywgL2ZsYWtGaXJlXChlLCBmYWxzZVwpLy50ZXN0KHNyYykgJiYgL2ZsYWtGaXJl'
        'XChhLCB0cnVlXCkvLnRlc3Qoc3JjKSk7Cm9rKCd0aGUgZW5lbXkgZnVzZSBidXJzdHMgd2hlcmUg'
        'aXQgcnVucyBvdXQnLAogICAvaWZcKGJcLmZ1c2UgJiYgLS1iXC5mdXNlPD0wXClce1xuXHMqZmxh'
        'a0J1cnN0XChiXC54LCBiXC55LCBmYWxzZSwgYlwuZmFjdGlvblwpLy50ZXN0KHNyYykpOwoKY29u'
        'c29sZS5sb2coJ1xuRXZlcnkgd2VhcG9uIGlzIHJlYWNoYWJsZSBhbmQgbm9uZSBvZiB0aGVtIGlz'
        'IGZyZWUnKTsKewogIGNvbnN0IGFsbCA9IHJ1bignUFJJTUFSSUVTJykuY29uY2F0KHJ1bignU0VD'
        'T05EQVJJRVMnKSk7CiAgb2soJ2VhY2ggb25lIGhhcyBhIG5hbWUnLCBhbGwuZXZlcnkodz0+ISF3'
        'Lm5hbWUpKTsKICBvaygnZWFjaCBvbmUgaGFzIGEgbm90ZSB0aGF0IHNheXMgd2hhdCBpdCBpcyBm'
        'b3InLCBhbGwuZXZlcnkodz0+ISF3Lm5vdGUpKTsKICBvaygndGhlIHRocmVzaG9sZHMgcmlzZSBy'
        'YXRoZXIgdGhhbiByZXBlYXQnLAogICAgIG5ldyBTZXQoYWxsLm1hcCh3PT53LnVubG9jaykpLnNp'
        'emUgPj0gYWxsLmxlbmd0aC0yKTsKICBvaygndGhlIHN0YW5kYXJkIGZpdCBpcyB0aGUgb25seSBm'
        'cmVlIGd1bicsCiAgICAgcnVuKCdQUklNQVJJRVMnKS5maWx0ZXIodz0+IXcudW5sb2NrKS5sZW5n'
        'dGg9PT0xKTsKfQoKY29uc29sZS5sb2coJ1xuJyArIChmYWlscyA/IGZhaWxzKycgRkFJTEVEJyA6'
        'ICdhbGwgcGFzc2VkJykpOwpwcm9jZXNzLmV4aXQoZmFpbHM/MTowKTsK'
    ),
}
for name, data in TEST_FILES.items():
    open(name, 'wb').write(base64.b64decode(data))
print("v144 applied: practice log, checks updated. Now run: python3 assemble.py 144")
