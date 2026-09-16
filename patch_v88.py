#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FS3  v87 -> v88

  1  Dritte Gegnerfraktion: Hammer of Light
  2  Funkraum schaltet auch die Staffeln des Wellenplans ab, mit Meldung
  3  Iceni sagt, wenn sie nicht mehr springen kann

Nicht enthalten: die vasudanische Bosskomposition. Ihr Ausloeser ist
"Hatshepsut warpt ein, sobald Aten oder Typhon das Feld verlaesst" - das
ist ein Ereignis und gehoert in den Ereignisbau, nicht als Sonderfall
daneben.
"""
import io, os, sys
SRC="hlp_shooter_v87_logic.html"; DST="hlp_shooter_v88_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ─────────────────────────────────────────────────────────────
# 1  Fraktion als Argument statt als Suffix
#
# Bis v87 stand die Fraktion als Suffix im Typ, und jeder Zweig fragte
# beide Faelle einzeln ab: type==='cr_ntf'?ROLES.ntf_cruisers:ROLES.shivan_cruisers.
# Eine dritte Fraktion haette diese Verzweigung ein drittes Mal gebraucht,
# an sechs Stellen. Stattdessen wird der Typ jetzt zerlegt.
# ─────────────────────────────────────────────────────────────
sub("fac-helpers",
"""function poolFor(type){
  if(type==='fi_ntf') return ROLES.ntf_fighters;
  if(type==='fi_sh')  return ROLES.shivan_fighters;
  if(type==='bo_ntf') return ROLES.ntf_bombers;
  if(type==='bo_sh')  return ROLES.shivan_bombers;
  return null;
}""",
"""// Der Hammer of Light fliegt vasudanische Ruempfe. ROLES wird vom Packer
// erzeugt, deshalb hier als Verweis statt dort als Eintrag - sonst muesste
// der Packer dieselbe Liste ein zweites Mal fuehren.
ROLES.hol_fighters   = ROLES.ally_vas_fighters;
ROLES.hol_bombers    = ROLES.ally_vas_bombers;
ROLES.hol_cruisers   = ROLES.ally_vas_cruisers;
ROLES.hol_corvette   = ROLES.ally_vas_corvette;
ROLES.hol_destroyers = ROLES.ally_vas_destroyers;

const FAC_SFX  = {ntf:'ntf', sh:'shivan', hol:'hol'};
const ROLE_KEY = {fi:'fighters', bo:'bombers', cr:'cruisers',
                  co:'corvette', de:'destroyers', boss:'super'};
function typeRole(t){ const i=t.indexOf('_'); return i<0 ? t : t.slice(0,i); }
function typeFac(t){ const i=t.indexOf('_'); return i<0 ? 'ntf' : (FAC_SFX[t.slice(i+1)]||'ntf'); }
function poolFor(type){
  const k = ROLE_KEY[typeRole(type)];
  return k ? (ROLES[typeFac(type)+'_'+k] || null) : null;
}""")

sub("fi-branch",
"""  if(type==='fi_ntf'||type==='fi_sh'){
    const pool=type==='fi_ntf'?ROLES.ntf_fighters:ROLES.shivan_fighters;""",
"""  if(typeRole(type)==='fi'){
    const pool=poolFor(type);""")
sub("fi-fac",
"""    return {type:'fighter',img:spr,faction:type==='fi_ntf'?'ntf':'shivan',""",
"""    return {type:'fighter',img:spr,faction:typeFac(type),""")

sub("bo-branch",
"""  if(type==='bo_ntf'||type==='bo_sh'){
    const pool=type==='bo_ntf'?ROLES.ntf_bombers:ROLES.shivan_bombers;""",
"""  if(typeRole(type)==='bo'){
    const pool=poolFor(type);""")
sub("bo-fac",
"""    return {type:'bomber',img:spr,faction:type==='bo_ntf'?'ntf':'shivan',""",
"""    return {type:'bomber',img:spr,faction:typeFac(type),""")

sub("cr-branch",
"""  if(type==='cr_ntf'||type==='cr_sh'){
    const pool=type==='cr_ntf'?ROLES.ntf_cruisers:ROLES.shivan_cruisers;""",
"""  if(typeRole(type)==='cr'){
    const pool=poolFor(type);""")
sub("cr-fac",
"""    const cr={type:'cruiser',img:spr,faction:type==='cr_ntf'?'ntf':'shivan',""",
"""    const cr={type:'cruiser',img:spr,faction:typeFac(type),""")

sub("co-branch",
"""  if(type==='co_ntf'||type==='co_sh'){
    const pool=type==='co_ntf'?ROLES.ntf_corvette:ROLES.shivan_corvette;""",
"""  if(typeRole(type)==='co'){
    const pool=poolFor(type);""")

sub("de-branch",
"""  if(type==='de_ntf'||type==='de_sh'){
    const pool=type==='de_ntf'?ROLES.ntf_destroyers:ROLES.shivan_destroyers;""",
"""  if(typeRole(type)==='de'){
    const pool=poolFor(type);""")

sub("co-fac",
"""    const ent={type:'corvette',img:spr,faction:type==='co_ntf'?'ntf':'shivan',""",
"""    const ent={type:'corvette',img:spr,faction:typeFac(type),""")

sub("de-fac",
"""    const ent={type:'destroyer',img:spr,faction:type==='de_ntf'?'ntf':'shivan',""",
"""    const ent={type:'destroyer',img:spr,faction:typeFac(type),""")

# Suffix in getWaveDef
sub("sfx",
"""  const shivan = (fac === 'shivan');
  const sfx = shivan ? '_sh' : '_ntf';""",
"""  const shivan = (fac === 'shivan');
  const sfx = shivan ? '_sh' : (fac === 'hol' ? '_hol' : '_ntf');""")

sub("factionof",
"""function factionOf(f){ return (f==='hol') ? 'ntf' : f; }""",
"""function factionOf(f){ return f; }      // hol ist ab v88 eine eigene Fraktion""")

# Triebwerksfarbe
sub("hol-colour",
"""  if(faction === 'renegade') return '#48ffb0';""",
"""  if(faction === 'renegade') return '#48ffb0';
  // Hammer of Light: vasudanische Ruempfe, aber nicht die Gemeinschafts-
  // flotte. Tiefes Orange, klar getrennt vom Bernstein der verbuendeten
  // Vasudaner und vom Rot der Shivaner.
  if(faction === 'hol')      return '#ff7a1c';""")

# Sperrgeschuetzpool
sub("sg-pool",
"""  const sgPool = shivan ? ['sgtrident','sgbelial'] : ['sgwatchdog','sgcerberus','sgalastor'];""",
"""  const sgPool = shivan ? ['sgtrident','sgbelial']
               : (fac==='hol' ? ['sgankh']
                              : ['sgwatchdog','sgcerberus','sgalastor']);""")

# ─────────────────────────────────────────────────────────────
# 2  Funkraum
#
# updateBossCalls() prueft den Funkraum bereits richtig. Was weiterlief,
# waren die Staffeln aus dem Wellenplan - die stehen in spawnQ und haben
# mit dem Funkraum des Bosses nichts zu tun. Vom Spielersitz aus ist das
# nicht zu unterscheiden, also sah es aus, als greife die Mechanik nicht.
#
# Verschieben reicht nicht: die Welle endet bei leerem Feld UND leerer
# Warteschlange, verschobene Eintraege wuerden sie ewig offen halten. Sie
# muessen raus.
# ─────────────────────────────────────────────────────────────
sub("comms-cut",
"""function tickDefectors(){""",
"""// Ein lebendes Fuehrungsschiff mit heilem Funkraum genuegt. Zerstoerte
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
function tickComms(){
  if(commsCut) return;
  // Erst wenn ueberhaupt ein Grosskampfschiff da war, sonst feuert es in
  // jeder Jaegerwelle sofort.
  let anyCap = false;
  for(const e of enemies) if(!e.dead && hasSubsystems(e)) { anyCap = true; break; }
  if(!anyCap || enemyRadioAlive()) return;
  commsCut = true;
  // Staffeln, die noch nicht da sind, kommen nicht mehr.
  let weg = 0;
  for(let i=spawnQ.length-1;i>=0;i--){
    const t = spawnQ[i].type;
    if(t && WING_TYPES[t]){ spawnQ.splice(i,1); weg++; }
  }
  SUB_MSGS.push({x:W/2, y:H*0.42, txt:'ENEMY COMMS DOWN', life:200, ml:200, ally:true});
}

function tickDefectors(){""")

sub("comms-call",
"""  tickDefectors();
  tickCrossGuards();""",
"""  tickDefectors();
  tickCrossGuards();
  tickComms();""")

sub("comms-reset",
"""  crossDone=0; crossTotal=0;""",
"""  crossDone=0; crossTotal=0; commsCut=false;""")

# ─────────────────────────────────────────────────────────────
# 3  Iceni
#
# Ein zerstoerter Navigationsblock verhindert die Flucht - das ist so
# gebaut und soll eine Entdeckung bleiben. Ohne Rueckmeldung merkt aber
# niemand, dass der Treffer etwas bewirkt hat. Die Meldung verraet nichts
# im Voraus, sie erklaert im Moment des Treffers.
# ─────────────────────────────────────────────────────────────
sub("iceni-msg",
"""  if(e.disableTgt && !e.disableMet){""",
"""  // Sprungfaehigkeit gerade verloren? Einmalig melden.
  if(!e.navMsgDone && e.flee && hasSubsystems(e) && !subOK(e,'navigation')){
    e.navMsgDone = true;
    SUB_MSGS.push({x:e.x, y:e.y-30, txt:'TARGET CANNOT JUMP', life:170, ml:170, ally:true});
  }
  if(e.disableTgt && !e.disableMet){""")

def main():
    if not os.path.exists(SRC): sys.exit("FEHLT: "+SRC)
    txt=io.open(SRC,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(DST,"w",encoding="utf-8").write(txt)
    print("\ngeschrieben: %s  (%.2f MB)"%(DST,os.path.getsize(DST)/1048576.0))
main()
