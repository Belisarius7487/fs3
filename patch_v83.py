#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FS3  v82 -> v83   Fehlerbau

  1  Ein Lahmlege-Ziel kann nicht mehr durch Rumpfschaden sterben.
  2  Die Auftragszeile bleibt stehen, wenn ein Auftrag erledigt ist.

Kein neuer Umfang.
"""

import io, os, sys

SRC = "hlp_shooter_v82_logic.html"
DST = "hlp_shooter_v83_logic.html"

edits = []
def sub(tag, old, new):
    edits.append((tag, old, new))


# ─────────────────────────────────────────────────────────────
# 1  Lahmlegen
#
# Gemessen am Leviathan in Welle 4:
#   Rumpf 1120, Subsystem 0.22*1120 = 246 TP, Trefferradius SECHS Bildpunkte
#   (8.5 % der Schiffsbreite, und die Untergrenze greift). Groesser geht
#   nicht: beim Fenris liegen die zwei naechsten Subsysteme 13 px
#   auseinander, ein Radius ueber 7 wuerde sie verschmelzen.
#   disableDone() verlangt ausserdem BEIDE, Waffen und Antrieb.
#
# Damit gehen realistisch neun von zehn Schuessen in den Rumpf. 1120 sind
# 7,1 s Spielerfeuer, die Subsysteme braeuchten 16 - das Schiff explodiert
# zwangslaeufig zuerst. An den Zahlen zu drehen macht das nur seltener,
# nicht unmoeglich: der Rumpf muesste das Zwanzigfache haben.
#
# Deshalb der Riegel statt der Stellschraube: ein Lahmlege-Ziel nimmt
# Rumpfschaden nur bis zu einem Rest. Es kann nicht explodieren, solange
# der Auftrag laeuft. So funktionieren Lahmlege-Missionen in FreeSpace
# auch, und der Spieler sieht es am Rumpfbalken, der stehenbleibt.
# ─────────────────────────────────────────────────────────────
sub("disable-floor-const",
"""const SUB_HP_FRAC = {cruiser:0.22, corvette:0.16, destroyer:0.10, boss:0.20};""",
"""const SUB_HP_FRAC = {cruiser:0.22, corvette:0.16, destroyer:0.10, boss:0.20};
// Rest, unter den ein Lahmlege-Ziel nicht fallen kann, solange der Auftrag
// laeuft. 15 % ist derselbe Wert wie HULL_CRIT: der Balken steht genau
// dort, wo er ohnehin schon pulsiert.
const DISABLE_HULL_FLOOR = 0.15;
// Duennere Subsysteme nur beim Lahmlege-Ziel. Ohne das dauert es bei einer
// Trefferquote von 10 % auf einen 6-px-Punkt rund 17 s je Subsystem, und
// es sind zwei. Mit 0.12 sind es 8,5 s bei 20 % und 17 s bei 10 %.
const DISABLE_SUB_FRAC = 0.12;""")

sub("disable-floor-apply",
"""  e.hp -= dmg;
}""",
"""  e.hp -= dmg;
  // Der Riegel. Greift nur, solange der Auftrag noch offen ist - sobald
  // Waffen und Antrieb hin sind, faellt er weg und das Schiff laesst sich
  // normal fertigmachen.
  if(e.disableTgt && !e.disableMet){
    const floor = e.maxHp * DISABLE_HULL_FLOOR;
    if(e.hp < floor) e.hp = floor;
    if(!subOK(e,'weapons') && !subOK(e,'engines')) e.disableMet = true;
  }
}""")

sub("disable-subhp",
"""  if(sp.disable) disableTarget = e;""",
"""  if(sp.disable){
    disableTarget = e;
    e.disableTgt = true; e.disableMet = false;
    // Die Subsysteme stehen zu diesem Zeitpunkt schon, also werden sie
    // nachtraeglich umgesetzt statt initSubsystems zu verzweigen.
    if(e.subs){
      const dh = Math.max(30, Math.round(e.maxHp*DISABLE_SUB_FRAC));
      for(const s of e.subs){ s.hp = dh; s.maxHp = dh; }
    }
  }""")

# ─────────────────────────────────────────────────────────────
# 2  Auftragszeile
#
# objectiveText() liest den Zustand des Feldes. Sind die Container
# gescannt, findet sie nichts mehr und gibt null zurueck - das Banner
# verschwindet, obwohl die Welle weiterlaeuft. Der Spieler weiss dann
# nicht, dass jetzt nur noch aufgeraeumt werden muss.
# ─────────────────────────────────────────────────────────────
sub("obj-fallback",
"""  if(nRun)
    return {txt:'[ STOP '+nRun+' FREIGHTER'+(nRun>1?'S':'')+' ]',
            col:'#ffbb22', ink:'#ffd257'};
  return null;
}""",
"""  if(nRun)
    return {txt:'[ STOP '+nRun+' FREIGHTER'+(nRun>1?'S':'')+' ]',
            col:'#ffbb22', ink:'#ffd257'};
  return null;
}

// Wie lange nach Erledigung eines Auftrags die Erfolgsmeldung steht.
const OBJ_DONE_TIME = 220;    // 2,2 s
let objWasSet = false, objDoneT = 0;""")

sub("banner-fallback",
"""  let txt=null, col='#ff2200', ink='#ff4422';
  const ob=objectiveText();
  if(ob){ txt=ob.txt; col=ob.col; ink=ob.ink; }
  else {
    const bossInQ=spawnQ.some(function(s){return s.type==='boss_ntf'||s.type==='boss_sh';});
    if(bossInQ||bossAlive) txt='[ BOSS FIGHT ]';
  }""",
"""  let txt=null, col='#ff2200', ink='#ff4422';
  const ob=objectiveText();
  if(ob){
    txt=ob.txt; col=ob.col; ink=ob.ink;
    objWasSet = true;
  } else {
    // Gab es einen Auftrag und ist er jetzt weg, war er erledigt. Ohne
    // diese Meldung verschwindet die Zeile stumm und der Spieler weiss
    // nicht, ob er fertig ist oder etwas uebersehen hat.
    if(objWasSet){ objWasSet = false; objDoneT = OBJ_DONE_TIME; }
    const bossInQ=spawnQ.some(function(s){return s.type==='boss_ntf'||s.type==='boss_sh';});
    if(objDoneT>0){
      if(!paused) objDoneT--;
      txt='[ OBJECTIVE COMPLETE ]'; col='#00cc44'; ink='#4dff88';
    }
    else if(bossInQ||bossAlive) txt='[ BOSS FIGHT ]';
    // Sonst: aufraeumen. Die Zeile bleibt stehen, solange noch etwas im
    // Feld oder in der Warteschlange steht.
    else if(liveThreatCount()>0 || spawnQ.length)
      { txt='[ CLEAR THE FIELD ]'; col='#ff2200'; ink='#ff4422'; }
  }""")

sub("obj-reset",
"""  waveTitle=''; titleT=0;""",
"""  waveTitle=''; titleT=0;
  objWasSet=false; objDoneT=0;""")


def main():
    if not os.path.exists(SRC):
        sys.exit("FEHLT: " + SRC)
    txt = io.open(SRC, "r", encoding="utf-8").read()
    for tag, old, new in edits:
        n = txt.count(old)
        if n != 1:
            sys.exit("ABBRUCH %s: %d Treffer statt 1" % (tag, n))
        txt = txt.replace(old, new, 1)
        print("  ok   " + tag)
    io.open(DST, "w", encoding="utf-8").write(txt)
    print("\ngeschrieben: %s  (%.2f MB)" % (DST, os.path.getsize(DST)/1048576.0))


if __name__ == "__main__":
    main()
