#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v90 Teil B: geschriebene Wellen mit Ereignissen."""
import io, os, sys
F="hlp_shooter_v90_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

BLOCK = r"""
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
  codeimos:'ter_deimos', deorionright:'ter_orion', dehecate:'ter_hecate'
};
// Kategorien, die keinen Fraktionszusatz tragen.
const CAT_FIX = {sg:'sentry', fc:'container', fr:'freighter', tr:'freighter', ast:'ast'};
const CAT_FAC = {fi:1, bo:1, cr:1, co:1, de:1};

// ── Zustand der benannten Einheiten ──────────────────────────
// Ein Ausloeser wie "X zerstoert" braucht zwei Auskuenfte: war X jemals
// da, und ist es jetzt weg. Ohne das Erste feuert jeder Ausloeser
// sofort, weil zu Wellenbeginn nichts existiert.
let EV = [], EV_HELD = {}, EV_SEEN = {}, EV_LEFT = {}, EV_DOCK = {};
let evReinf = false, evReinfCd = 0;
const EV_REINF_GAP = 520;      // 5,2 s zwischen zwei Nachschubstaffeln

function evReset(){
  EV = []; EV_HELD = {}; EV_SEEN = {}; EV_LEFT = {}; EV_DOCK = {};
  evReinf = false; evReinfCd = 0;
}
function byId(id){
  const out = [];
  for(const e of enemies) if(e.uid===id && !e.dead) out.push(e);
  for(const a of allies)  if(a.uid===id && !a.dead) out.push(a);
  return out;
}
function evSeen(id){ return !!EV_SEEN[id]; }

// ── Ausloeser ────────────────────────────────────────────────
function evTrig(ev){
  switch(ev.t){
    case 'sek':          return spawnT >= (ev.a||0)*TICK_HZ;
    case 'zerstoert':    return evSeen(ev.a) && byId(ev.a).length===0 && !EV_LEFT[ev.a];
    case 'alleZerstoert':return evSeen(ev.a) && byId(ev.a).length===0;
    case 'verlaesst':    return !!EV_LEFT[ev.a];
    case 'angedockt':    return !!EV_DOCK[ev.a];
    case 'anzahlUnter':  return evSeen(ev.a) && byId(ev.a).length < (ev.b||1);
    case 'rumpfUnter': {
      const u = byId(ev.a)[0];
      return !!u && u.maxHp && (u.hp/u.maxHp)*100 < (ev.b||50);
    }
    case 'erfuellt':     return !objectiveText();
  }
  return false;
}

// ── Wirkungen ────────────────────────────────────────────────
function evFire(ev){
  switch(ev.w){
    case 'einwarpen': {
      const held = EV_HELD[ev.a];
      if(held){ for(const q of held){ q.time = spawnT + (q.delay||0); spawnQ.push(q); }
                delete EV_HELD[ev.a];
                spawnQ.sort(function(a,b){ return a.time-b.time; }); }
      break;
    }
    case 'auftrag':
      waveObj = ev.a;
      // Der Banner liest den Zustand des Feldes; die Erfolgsmeldung des
      // alten Auftrags soll den neuen nicht ueberdecken.
      objWasSet = false; objDoneT = 0; objFailed = false;
      break;
    case 'seite':
      for(const u of byId(ev.a)) if(u.side!=='enemy') defect(u);
      break;
    case 'raus':
      for(const u of byId(ev.a)){ u.warpOut = u.warpMax || 100; EV_LEFT[ev.a] = true; }
      break;
    case 'nachschub':
      evReinf = (ev.a !== 'aus');
      break;
    case 'meldung':
      SUB_MSGS.push({x:W/2, y:H*0.40, txt:String(ev.a||'').toUpperCase(),
                     life:200, ml:200, ally:true});
      break;
    case 'ende':
      for(let i=spawnQ.length-1;i>=0;i--) spawnQ.splice(i,1);
      evReinf = false;
      break;
  }
}

function tickEvents(){
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
      for(let k=0;k<sz;k++)
        spawnQ.push({time:spawnT+k*WING_STAGGER, type:ty, wing:wid,
                     y:H*(0.22+Math.random()*0.56)});
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
        for(let k=0;k<sz;k++)
          put({time:t0 + w*260 + k*WING_STAGGER,
               type: ally ? 'allyfi' : ty, spr:u.spr||'', wing:ally?0:wid,
               y: yy + (k-(sz-1)/2)*WING_SPACING*0.5, x:u.x});
      }
    } else {
      for(let i=0;i<n;i++)
        put(ally
          ? {time:t0+i*140, type:'ally', allyId:ALLY_ID[u.spr]||'vas_aten', spr:u.spr}
          : {time:t0+i*140, type:ty, spr:u.spr||'', y:u.y, x:u.x});
    }
    return;
  }

  const fix = CAT_FIX[u.c];
  if(!fix) return;                     // Klasse noch nicht spawnbar
  for(let i=0;i<n;i++){
    const yy = (u.y!=null) ? u.y : H*(0.20+0.60*((i+0.5)/n));
    const xx = (u.x!=null) ? u.x : W*(0.55+0.12*(i%3));
    if(ally && fix!=='ast')
      put({time:t0+i*90, type:'protect', spr:u.spr, fac:'vasudan', noWarp:1,
           x:xx, y:yy, cross:u.cross});
    else
      put({time:t0+i*60, type:fix, spr:u.spr||'', fac:fac, noWarp:(fix!=='ast')?1:0,
           x:xx, y:yy, scan:u.scan?1:0});
  }
}

function buildScripted(def){
  const q = [];
  evReset();
  currentFaction = def.fac;
  waveLive  = def.live || 4;
  waveObj   = def.o || 'clear';
  fleeTotal = 0; fleeEscaped = 0;
  guardWanted=false; guardSpawned=false; guardLost=false; guardGone=false;
  astAim=false; transitSecs=0; gateWings=false; gateWing=0;
  disableTarget=null; waveFeud=false;
  astStreamCd = AST_STREAM_MEAN;
  waveMod = def.mod || MOD_NONE;
  if(nebulaOn()) nebTint = NEB_TINTS[(Math.random()*NEB_TINTS.length)|0];
  empOut=0; empWarn=0; empNext = waveMod==='emp' ? 1400 : 0;
  BOMB_PORTALS=[]; bombRaidLeft=0; reinfAt=0; reinfDone=true;
  crossDone=0; crossTotal=0; commsCut=false; commsSeen=false;

  for(const u of (def.u||[])) scriptUnit(u, def.fac, q);
  EV = (def.ev||[]).map(function(e){ return {t:e.t,a:e.a,b:e.b,w:e.w,done:false}; });
  return q.sort(function(a,b){ return a.time-b.time; });
}
"""

sub("script-block", """function getWaveDef(n){""", BLOCK + """
function getWaveDef(n){""")

# waveObj: der Auftrag, der gerade gilt. Bisher lag er nur lokal in
# getWaveDef; ein Ereignis muss ihn aendern koennen.
sub("waveobj-var", """let allyWingWanted = 0;""",
"""let allyWingWanted = 0;
// Der Auftrag, der gerade gilt. Lag bisher nur als lokale Variable in
// getWaveDef - ein Ereignis muss ihn wechseln koennen.
let waveObj = 'clear';""")

# getWaveDef nimmt eine geschriebene Welle, wenn es eine gibt
sub("getwave-hook",
"""  if(TEST_MODE) return buildTestWave(((n-2+TEST_FIRST)%4)+1);
  if(FS1_MODE)  return buildFS1Wave(n);""",
"""  if(TEST_MODE) return buildTestWave(((n-2+TEST_FIRST)%4)+1);
  if(FS1_MODE)  return buildFS1Wave(n);
  // Geschriebene Welle, falls vorhanden. Mit ?m=3 laesst sich eine
  // einzelne zum Pruefen anspringen; ohne den Parameter laufen sie der
  // Reihe nach und der Wuerfel uebernimmt erst danach.
  {
    const sk = SCRIPT_ONE ? SCRIPT_ONE : n;
    const def = SCRIPT_WAVES[sk];
    if(def) return buildScripted(def);
  }""")

sub("script-param",
"""const FS1_MATCH = /[?&]fs1=(\\d+)/.exec(location.search);""",
"""const SCRIPT_MATCH = /[?&]m=(\\d+)/.exec(location.search);
const SCRIPT_ONE = SCRIPT_MATCH ? (parseInt(SCRIPT_MATCH[1],10)||0) : 0;
const FS1_MATCH = /[?&]fs1=(\\d+)/.exec(location.search);""")

# Der Banner liest jetzt waveObj mit, damit ein gewechselter Auftrag wirkt
sub("obj-uses-waveobj",
"""  waveObj    = ...;""" if False else
"""  waveFeud    = (o==='feud');""",
"""  waveFeud    = (o==='feud');
  waveObj     = o;""")

# Spawnschleife: Kennung mitgeben, Verbuendete erzeugen
sub("spawn-uid",
"""      if(_sp.type==='protect'){ spawnProtected(_sp); continue; }""",
"""      if(_sp.type==='protect'){ spawnProtected(_sp); continue; }
      // Verbuendetes Grosskampfschiff aus ALLY_DEFS.
      if(_sp.type==='ally'){
        const _a = mkAlly(_sp.allyId);
        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;
                if(_sp.hpMul) { _a.hp=Math.round(_a.hp*_sp.hpMul); _a.maxHp=Math.max(_a.maxHp,_a.hp); }
                allies.push(_a); }
        continue;
      }
      // Verbuendeter Jaeger.
      if(_sp.type==='allyfi'){
        const _a = mkAllySmall('fighter', currentFaction==='hol'?'vasudan':'terran',
                               _sp.spr || rnd(ROLES.ally_vas_fighters), _sp.y);
        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true; allies.push(_a); }
        continue;
      }""")

sub("spawn-uid2",
"""applySpawnOpts(_e,_sp);enemies.push(_e);}}""",
"""applySpawnOpts(_e,_sp);_e.uid=_sp.uid;if(_sp.uid)EV_SEEN[_sp.uid]=true;enemies.push(_e);}}""")

sub("ev-call",
"""  tickDefectors();
  tickCrossGuards();
  tickComms();""",
"""  tickDefectors();
  tickCrossGuards();
  tickComms();
  tickEvents();""")

# Ein Schiff, das ueberlaufen soll, kann vorher nicht sterben.
sub("defect-lock",
"""  if(e.disableTgt && !e.disableMet){""",
"""  // Ein Schiff, das ueberlaufen soll, kann vorher nicht sterben - sonst
  // haengt die Pointe der Welle am Zufall des Gefechts.
  if(e.defectLock){
    const dfl = e.maxHp * DISABLE_HULL_FLOOR;
    if(e.hp < dfl) e.hp = dfl;
  }
  if(e.disableTgt && !e.disableMet){""")

sub("defect-clear",
"""  a.faction = 'renegade';""",
"""  a.defectLock = false;      // gewechselt, ab jetzt normal zu toeten
  a.faction = 'renegade';""")

def main():
    if not os.path.exists(F): sys.exit("FEHLT: "+F)
    txt=io.open(F,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(F,"w",encoding="utf-8").write(txt)
    print("Teil B geschrieben")
main()
