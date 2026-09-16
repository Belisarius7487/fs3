#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v100 -> v101: Andocken reparieren, Zielwahl, Rammkurs."""
import io, os, sys
SRC="hlp_shooter_v100_logic.html"; DST="hlp_shooter_v101_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── spawnProtected hat die Spawnoptionen ignoriert ───────────────
# Es setzt seine Felder von Hand und ruft applySpawnOpts() nie auf.
# dockTo ging damit verloren - in M009 und M027 -, und minY=maxY liess
# einen Transporter ohne cross fuer immer bei x=-40 stehen.
sub("protect-opts",
"""  a.vx = 0; a.vy = 0;
  a.minY = a.y; a.maxY = a.y;      // updateAllies() nudges vy, so pin it""",
"""  a.vx = 0; a.vy = 0;
  a.minY = a.y; a.maxY = a.y;      // updateAllies() nudges vy, so pin it
  // Ein Andockauftrag wird hier gesetzt: applySpawnOpts laeuft fuer
  // Schuetzlinge nicht, weil sie ueber diesen Weg entstehen.
  if(sp.dockTo){
    a.dockTo = sp.dockTo;
    // Die Hoehe darf nicht gepinnt sein, sonst kommt er nie zum
    // Andockpunkt hoch.
    a.minY = HUD_H+20; a.maxY = H-20;
  }
  if(sp.still){ a.vy = 0; a.minY = a.y; a.maxY = a.y; }""")

# Wer noch andocken muss, quert noch nicht.
sub("protect-cross",
"""  if(sp.cross){
    a.crossing = sp.cross;         // Bildpunkte je Schritt""",
"""  if(sp.cross && !sp.dockTo){
    a.crossing = sp.cross;         // Bildpunkte je Schritt""")
# Nach dem Andocken quert er, wenn die Mission es vorsieht.
sub("dock-then-cross",
"""    e.dockTo = null;""",
"""    e.dockTo = null;
    // Erst laden, dann abfahren.
    if(e.crossAfter) e.crossing = e.crossAfter;""")
sub("crossafter-set",
"""  if(sp.dockTo){
    a.dockTo = sp.dockTo;""",
"""  if(sp.dockTo){
    a.dockTo = sp.dockTo;
    a.crossAfter = sp.cross || 0.38;""")

# ── Zielwahl: unverwundbare und Scanziele auslassen ─────────────
sub("nearest-skip",
"""function nearestEnemy(x, y){
  let best=null, bd=Infinity;
  for(const o of enemies){
    if(o.dead || o.warp>0 || o.type==='asteroid') continue;""",
"""function nearestEnemy(x, y){
  let best=null, bd=Infinity;
  for(const o of enemies){
    if(o.dead || o.warp>0 || o.type==='asteroid') continue;
    // Eine unverwundbare Station ist Kulisse: auf sie zu halten sieht aus
    // wie ein Fehler und haelt die Geschuetze von echten Zielen ab.
    if(o.invuln) continue;
    // Fracht, die gescannt oder abgeholt werden soll, ist kein Ziel -
    // sonst raeumen die eigenen Verbuendeten den Auftrag weg.
    if(o.noTarget) continue;""")
sub("notarget-scan",
"""  if(sp.scan) e.scan = true;""",
"""  if(sp.scan){ e.scan = true; e.noTarget = true; }""")
sub("notarget-beam",
"""      if(o.dead || o.warp>0 || o.type==='asteroid' || o.invuln) continue;""",
"""      if(o.dead || o.warp>0 || o.type==='asteroid' || o.invuln || o.noTarget) continue;""")

# ── Rammkurs: die Hoehe darf nicht eingefroren sein ─────────────
# still setzte minY=maxY auch beim Rammer selbst - er konnte gar nicht
# steigen und traf nur, wenn er zufaellig auf gleicher Hoehe einwarpte.
sub("capram-free",
"""  if(sp.capRam){ e.capRam = sp.capRam; e.noFlee = true; }""",
"""  if(sp.capRam){
    e.capRam = sp.capRam; e.noFlee = true;
    // Volle Hoehe: ein Rammkurs muss steigen und sinken koennen. still
    // gilt nur fuer das Ziel, nicht fuer den Angreifer.
    e.minY = HUD_H+10; e.maxY = H-10;
  }""")
# Und der Anflug soll senkrecht schneller sein als waagerecht, sonst
# schiebt er sich in der Hoehe kaum.
sub("capram-speed",
"""    e.x += dx/L*e.capRam;
    e.y += dy/L*e.capRam;""",
"""    // Senkrecht zuegiger als waagerecht: sonst kriecht er die Hoehe hoch
    // und ist laengst da, bevor er auf Hoehe ist.
    e.x += dx/L*e.capRam;
    e.y += dy/L*e.capRam*3.4;""")

# ── Ein Ereignis, dessen Ziel gestorben ist, blockiert nicht ────
# In M027 haengt alles an "T1 hat angedockt". Stirbt die Hatshepsut, kann
# das nie passieren - die Welle lief endlos.
sub("evpending-dead",
"""    if(['zerstoert','alleZerstoert','verlaesst','anzahlUnter','rumpfUnter','subsystem'].indexOf(e.t)>=0){
      if(evSeen(e.a) && byId(e.a).length===0) continue;
    }""",
"""    if(['zerstoert','alleZerstoert','verlaesst','anzahlUnter','rumpfUnter','subsystem'].indexOf(e.t)>=0){
      if(evSeen(e.a) && byId(e.a).length===0) continue;
    }
    // Ein Andockauftrag, dessen Ziel nicht mehr existiert, kann nicht
    // mehr feuern. Sonst laeuft die Welle endlos weiter.
    if(e.t==='angedockt'){
      const dk = byId(e.a)[0];
      if(!dk) { if(evSeen(e.a)) continue; }
      else if(dk.dockTo && byId(dk.dockTo).length===0 && evSeen(dk.dockTo)) continue;
    }""")

# Die Fracht folgte dem Traeger nicht: tickDocking() steigt bei !e.dockTo
# aus, und beim Andocken wird dockTo auf null gesetzt. Der Mitfuehrteil
# lief damit nie. Gefunden durch Simulation, nicht durch Lesen.
sub("carry-cond",
"""    if(!e.dockTo || e.dead || e.warp>0) continue;""",
"""    if((!e.dockTo && !e.dockedTo) || e.dead || e.warp>0) continue;""")

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
