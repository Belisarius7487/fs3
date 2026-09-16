#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v91 -> v92: offene Merkliste plus sechs neue Punkte."""
import io, os, sys
SRC="hlp_shooter_v91_logic.html"; DST="hlp_shooter_v92_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── Fraktionstext raus. Diesmal die richtige Zeile: beim letzten Mal habe
#    ich die Fuellfarbe geaendert und den Text stehen lassen.
sub("fac-text",
"""  ctx.fillText(currentFaction==='ntf'?'NTF':'SHIVAN',138,mid+5);""",
"""  // Fraktionstext entfernt: er kannte zwei Faelle und schrieb bei HoL
  // "SHIVAN". Welche Fraktion dran ist, sagen Rumpfformen und
  // Triebwerksfarben ohnehin besser als ein Wort in der Leiste.""")

# ── Zerstoerer, Korvette und Sperrgeschuetz lasen den genannten Rumpf
#    nicht. Nur der Kreuzerzweig tat es - deshalb wurde aus der Typhon in
#    M007 mal eine Hatshepsut.
sub("co-spr",
"""  if(typeRole(type)==='co'){
    const pool=poolFor(type);
    const spr=rnd(pool);""",
"""  if(typeRole(type)==='co'){
    const pool=poolFor(type);
    const spr=spr0 || rnd(pool);""")
sub("de-spr",
"""  if(typeRole(type)==='de'){
    const pool=poolFor(type);
    const spr=rnd(pool);""",
"""  if(typeRole(type)==='de'){
    const pool=poolFor(type);
    const spr=spr0 || rnd(pool);""")

# ── Kennung beim Schuetzling. Ohne sie greift die Zielvorliebe ins Leere:
#    es gibt kein T1 im Feld, auf das die Jaeger gehen koennten.
sub("protect-uid",
"""  a.side = 'ally';
  a.faction = sp.fac || 'terran';
  a.guard = true;""",
"""  a.side = 'ally';
  a.uid = sp.uid;
  if(sp.uid) EV_SEEN[sp.uid] = true;
  a.faction = sp.fac || 'terran';
  a.guard = true;""")

# ── Leistenschutz auch bei der Zeigerbewegung. Das Schiff flog der Leiste
#    schon entgegen, waehrend man den Zeiger hinbewegte.
sub("mousemove-guard",
"""CVS.addEventListener('mousemove',function(ev){
  var p=toGC(ev.clientX,ev.clientY);
  MOUSE.x=p.x; MOUSE.y=p.y;""",
"""CVS.addEventListener('mousemove',function(ev){
  var p=toGC(ev.clientX,ev.clientY);
  // touchmove hatte diesen Schutz, mousemove nicht.
  if(p.y<HUD_H&&GS==='playing') return;   // Leiste: keine Steuereingabe
  MOUSE.x=p.x; MOUSE.y=p.y;""")

# ── Halteposition symmetrisch. Gegner hielten so weit rechts, dass ihre
#    aeussere Haelfte ausserhalb des Feldes lag; Verbuendete nicht.
# Zwei Vorkommen der Korvettenposition: regulaere Korvette und Iceni.
# Ueber die Folgezeile eindeutig gemacht.
sub("station-co",
"""      // Corvettes sit behind the cruisers now.
      targetX:W-74-Math.random()*34,""",
"""      // Corvettes sit behind the cruisers now. W-74 hiess: die aeussere
      // Haelfte eines 195 Bildpunkte breiten Rumpfs lag ausserhalb des
      // Feldes, waehrend das verbuendete Gegenstueck ganz zu sehen war.
      targetX:W-150-Math.random()*34,""")

sub("station-de",
"""      targetX:W-198-Math.random()*34,""",
"""      targetX:W-230-Math.random()*34,""")

# ── Geschuetze zielen. capitalFire schoss stur nach links; ein querender
#    Zerstoerer feuerte damit in seine eigene Fahrtrichtung.
sub("guns-aim",
"""        if(Math.random() < cfg.big) eBig(pts[i].x, pts[i].y, e.faction);
        else                        eSmall(pts[i].x, pts[i].y, e.faction, null, null, null, eScat);""",
"""        // Zielen statt geradeaus. Die Streuung waechst mit zerstoerten
        // Sensoren, wie vorher - nur wirkt sie jetzt um die Zielrichtung
        // herum und nicht um die Waagerechte.
        const gt = capGunTarget(e);
        const ga = Math.atan2(gt.y-pts[i].y, gt.x-pts[i].x)
                 + (Math.random()-0.5)*0.10*eScat;
        if(Math.random() < cfg.big) eBig(pts[i].x, pts[i].y, e.faction);
        else                        eSmall(pts[i].x, pts[i].y, e.faction, ga);""")

sub("guns-target",
"""function capitalFire(e){""",
"""// Worauf ein Grosskampfschiff haelt. Verbuendete Grosskampfschiffe zuerst:
// dafuer sind die Geschuetze gebaut. Sonst der Spieler.
function capGunTarget(e){
  let best=null, bd=1e9;
  for(const a of allies){
    if(a.dead || a.small) continue;
    const d=(a.x-e.x)*(a.x-e.x)+(a.y-e.y)*(a.y-e.y);
    if(d<bd){ bd=d; best=a; }
  }
  return best || player;
}

function capitalFire(e){""")

# ── Ptah ist ein Tarnjaeger wie die Pegasus und gehoert nicht in
#    regulaere Staffeln.
sub("ptah-out",
"""ROLES.hol_fighters   = ROLES.ally_vas_fighters;""",
"""// Der Ptah ist ein Tarnjaeger. Er fliegt nicht in gewoehnlichen Staffeln,
// weder beim Hammer of Light noch bei den Vasudanern.
ROLES.hol_fighters   = ROLES.ally_vas_fighters.filter(function(k){ return k!=='fiptah'; });""")

# ── Anflugzeichen und Rammstoss nur gegen verbuendete Grosskampfschiffe.
#    Ein Bomber, der auf den Spieler zufliegt, braucht kein Sonderzeichen.
sub("ram-only-cap",
"""    if(e.type!=='fighter' && e.type!=='bomber') continue;
    if(e.role!=='attack' || e.passT>0) continue;
    const t = smallTarget(e);
    if(!t || t===e) continue;""",
"""    if(e.type!=='bomber') continue;              // nur Bomber rammen
    if(e.role!=='attack' || e.passT>0) continue;
    const t = smallTarget(e);
    // Nur gegen verbuendete Grosskampfschiffe. Auf den Spieler zu stuerzen
    // waere kein Kamikaze, sondern ein unfairer Treffer ohne Vorwarnung.
    if(!t || t===e || t===player || t.small || t.side!=='ally') continue;""")

sub("ram-pct",
"""const RAM_PCT_BOMBER  = 0.09;
const RAM_PCT_FIGHTER = 0.04;""",
"""const RAM_PCT_BOMBER  = 0.04;
const RAM_PCT_FIGHTER = 0.02;""")

sub("mark-only-cap",
"""  const run = (e.role==='attack' && e.passT<=0);""",
"""  // Gelb nur, wenn dieser Bomber gerade ein verbuendetes Grosskampfschiff
  // anfliegt - dann lohnt es, ihn vorzuziehen. Ein Anflug auf den Spieler
  // bleibt rot wie jeder andere Gegner.
  let run = false;
  if(e.type==='bomber' && e.role==='attack' && e.passT<=0){
    const t = smallTarget(e);
    run = !!(t && t!==player && !t.small && t.side==='ally');
  }""")

# ── Stehendes Asteroidenfeld. Bisher trieben die Brocken nach links und
#    waren nach ein paar Sekunden weg.
sub("ast-still",
"""    const ast={type:'asteroid',img:null,pts:60,x:W+30,y,hp:HULL.asteroid,maxHp:HULL.asteroid,
      vx:-(1+Math.random()*2.5),vy:(Math.random()-.5)*1.5,""",
"""    const ast={type:'asteroid',img:null,pts:60,x:W+30,y,hp:HULL.asteroid,maxHp:HULL.asteroid,
      vx:astStill?0:-(1+Math.random()*2.5), vy:astStill?0:(Math.random()-.5)*1.5,""")
sub("ast-still-var",
"""let waveHunt = '';""",
"""let waveHunt = '';
// Stehendes Feld: die Brocken drehen sich, aber treiben nicht. Ein Gebiet,
// durch das man fliegt, statt eines Stroms, der vorbeizieht.
let astStill = false;""")
sub("ast-still-set",
"""  waveHunt = def.hunt || '';""",
"""  waveHunt = def.hunt || '';
  astStill = !!def.stillRocks;""")
sub("ast-still-clear",
"""  waveHunt    = '';""",
"""  waveHunt    = '';
  astStill    = false;""")

# ── Grosskampfschiffe derselben Kennung hintereinander statt nebeneinander
sub("cap-stagger",
"""      for(let i=0;i<n;i++)
        put(ally
          ? {time:t0+i*140, type:'ally', allyId:ALLY_ID[u.spr]||'vas_aten', spr:u.spr}
          : {time:t0+i*140, type:ty, spr:u.spr||'', y:u.y, x:u.x});""",
"""      // Mehrere Grosskampfschiffe derselben Kennung stehen sonst
      // uebereinander und blockieren sich. Versetzt in Tiefe und Hoehe:
      // hintereinander gestaffelt, jedes in seinem eigenen Hoehenband.
      for(let i=0;i<n;i++){
        const yy = (u.y!=null) ? u.y : H*(0.28+0.44*((i+0.5)/n));
        put(ally
          ? {time:t0+i*140, type:'ally', allyId:ALLY_ID[u.spr]||'vas_aten', spr:u.spr}
          : {time:t0+i*140, type:ty, spr:u.spr||'', y:yy, x:u.x,
             capBack:(n>1)? i*86 : 0});
      }""")
sub("cap-back",
"""  if(sp.disable){""",
"""  // Tiefenversatz fuer mehrere Grosskampfschiffe derselben Kennung.
  if(sp.capBack && e.targetX!=null) e.targetX -= sp.capBack;
  if(sp.disable){""")

# ── Missionen ────────────────────────────────────────────────
sub("m015-rocks",
"""  15:{name:'Der Vorratsspeicher', fac:'hol', o:'clear', live:4, u:[""",
"""  15:{name:'Der Vorratsspeicher', fac:'hol', o:'clear', live:4, stillRocks:true, u:[""")
sub("m015-count",
"""       {id:'R1', c:'ast', n:8},""",
"""       {id:'R1', c:'ast', n:34},""")
sub("m013-rocks",
"""  13:{name:'Die Transporter', fac:'hol', o:'protect', live:4, hunt:'T1', u:[""",
"""  13:{name:'Die Transporter', fac:'hol', o:'protect', live:4, hunt:'T1', stillRocks:true, u:[""")
sub("m013-count",
"""       {id:'R1', c:'ast', n:10},""",
"""       {id:'R1', c:'ast', n:26},""")

# M016: der Wechsel kam nach vier Abschuessen, die Welle war sofort vorbei.
# Jetzt faellt er, wenn die erste Staffelwelle durch ist - und die zweite
# steht noch aus.
sub("m016-rework",
"""       {id:'E1', c:'fi', n:2}
     ], ev:[
       {t:'anzahlUnter', a:'E1', b:4, w:'meldung', a2:'escort turning hostile'},
       {t:'anzahlUnter', a:'E1', b:4, w:'seite', a2:'A2'}""",
"""       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:2, t:26}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'meldung', a2:'escort turning hostile'},
       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A2'}""")

def main():
    if not os.path.exists(SRC): sys.exit("FEHLT: "+SRC)
    txt=io.open(SRC,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(DST,"w",encoding="utf-8").write(txt)
    print("geschrieben: "+DST)
main()
