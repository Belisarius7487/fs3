#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3  v88 -> v89   Sechs Fehler aus dem Spieltest."""
import io, os, sys
SRC="hlp_shooter_v88_logic.html"; DST="hlp_shooter_v89_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# 1  ENEMY COMMS DOWN feuerte beim Einwarpen
#    anyCap zaehlte einwarpende Schiffe mit, enemyRadioAlive() nicht: waehrend
#    des Warps war also "es gibt ein Grosskampfschiff" wahr und "es hat Funk"
#    falsch. Jetzt muss erst einmal ein heiler Funkraum gesehen worden sein.
sub("comms-warp",
"""function tickComms(){
  if(commsCut) return;
  // Erst wenn ueberhaupt ein Grosskampfschiff da war, sonst feuert es in
  // jeder Jaegerwelle sofort.
  let anyCap = false;
  for(const e of enemies) if(!e.dead && hasSubsystems(e)) { anyCap = true; break; }
  if(!anyCap || enemyRadioAlive()) return;""",
"""let commsSeen = false;
function tickComms(){
  if(commsCut) return;
  if(enemyRadioAlive()){ commsSeen = true; return; }
  // Ohne vorher gesehenen heilen Funkraum gibt es nichts abzuschalten.
  // Einwarpende Schiffe zaehlen dabei nicht, sonst feuert die Meldung in
  // der Luecke zwischen Ankunft und fertigem Warp.
  if(!commsSeen) return;""")
sub("comms-reset2","""crossDone=0; crossTotal=0; commsCut=false;""",
"""crossDone=0; crossTotal=0; commsCut=false; commsSeen=false;""")

# 2  Fehlschlag sah aus wie Erfolg
sub("obj-failed",
"""    if(objWasSet){ objWasSet = false; objDoneT = OBJ_DONE_TIME; }""",
"""    if(objWasSet){ objWasSet = false; objDoneT = OBJ_DONE_TIME; objFailed = guardLost; }""")
sub("obj-failed-var",
"""let objWasSet = false, objDoneT = 0;""",
"""let objWasSet = false, objDoneT = 0, objFailed = false;""")
sub("obj-failed-txt",
"""      txt='[ OBJECTIVE COMPLETE ]'; col='#00cc44'; ink='#4dff88';""",
"""      if(objFailed){ txt='[ OBJECTIVE FAILED ]'; col='#cc2200'; ink='#ff5533'; }
      else          { txt='[ OBJECTIVE COMPLETE ]'; col='#00cc44'; ink='#4dff88'; }""")
sub("obj-failed-reset",
"""  objWasSet=false; objDoneT=0;""",
"""  objWasSet=false; objDoneT=0; objFailed=false;""")

# 3  Am Wellenanfang stand CLEAR THE FIELD, weil das Ziel noch in der
#    Warteschlange steckt. Solange dort etwas wartet, ist das Feld nicht
#    "zu raeumen" - dann steht lieber nichts.
sub("banner-wait",
"""    else if(liveThreatCount()>0 || spawnQ.length)
      { txt='[ CLEAR THE FIELD ]'; col='#ff2200'; ink='#ff4422'; }""",
"""    else if(!spawnQ.length && liveThreatCount()>0)
      { txt='[ CLEAR THE FIELD ]'; col='#ff2200'; ink='#ff4422'; }""")

# 4  Eskorte
#    Die Orion kam mit 45 Prozent Rumpf an, also 2925 von 6500, gegen zwei
#    Bomberstaffeln. Und die Komposition stellte ihr Frachtkisten in die Bahn.
sub("guard-frac",
"""const GUARD_HULL_FRAC = 0.45;     // default: she arrives already shot up""",
"""// Sie kommt angeschlagen an, aber nicht halbtot: 0.45 waren 2925 von 6500
// gegen zwei Bomberstaffeln, und Bomber sind gegen Grosskampfschiffe
// gebaut. 0.70 sind 4550 und damit eine Aufgabe statt einer Verlustmeldung.
const GUARD_HULL_FRAC = 0.70;""")

# 4+6  Container nur noch, wo sie gebraucht werden, und ordentlich verteilt
sub("cargo-once",
"""  // Frachtcontainer als Kulisse einer Konvoiwelle. Der Auftrag scan macht
  // sie zu Zielen, sonst stehen sie einfach herum.
  for(let i=0;i<(K.cargo||0);i++)
    q.push({time:1, type:'container', spr:'fcvc3', fac:fac, noWarp:1,
            x:W*(0.55+0.10*i), y:H*(0.34+0.18*i)});""",
"""  // Container stellt nur noch der Scanauftrag - und der stellt sie einmal.
  // Vorher brachte die Komposition zwei mit und der Auftrag drei dazu:
  // fuenf Stueck, teils hintereinander, und in Eskortenwellen standen sie
  // der Orion in der Bahn.""")

sub("scan-place",
"""  if(o==='scan'){
    const nsc = spec0.cargo||3;
    for(let i=0;i<nsc;i++)
      q.push({time:1, type:'container', spr:'fcvc3', fac:fac, scan:1,
              noWarp:1, x:W*(0.58+0.09*i), y:H*(0.38+0.16*i)});
  }""",
"""  if(o==='scan'){
    const nsc = spec0.cargo||3;
    // Links der Mitte und weit auseinander: rechts kommen die Gegner
    // herein, und ein Container mit 69 Trefferpunkten stirbt an einem
    // Streifschuss. Senkrecht mindestens ein Viertel Feldhoehe Abstand,
    // waagerecht versetzt, damit keiner hinter einem anderen verschwindet.
    for(let i=0;i<nsc;i++)
      q.push({time:1, type:'container', spr:'fcvc3', fac:fac, scan:1,
              noWarp:1,
              x:W*(0.30+0.14*i),
              y:H*(0.24+(0.52/Math.max(1,nsc-1))*i)});
  }""")

# 5  Manticore noch etwas kleiner
sub("manticore",
"""const SIZE_FIXED = {sdcolossus: 556, fimanticore: 54};""",
"""const SIZE_FIXED = {sdcolossus: 556, fimanticore: 50};""")

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
