#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v99 -> v100: Subsysteme, Andocken, Meldungsfarben, M028."""
import io, os, sys
SRC="hlp_shooter_v99_logic.html"; DST="hlp_shooter_v100_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── Verbuendete Grosskampfschiffe hatten keine Subsysteme ─────────
# Mein Pfad fuer geschriebene Wellen ruft initSubsystems() nicht auf. Der
# Kampagnenpfad tat es, deshalb ist es erst jetzt aufgefallen.
sub("ally-subs",
"""      if(_sp.type==='ally'){
        const _a = mkAlly(_sp.allyId);
        if(_a && _sp.crossSecs){""",
"""      if(_sp.type==='ally'){
        const _a = mkAlly(_sp.allyId);
        // initSubsystems fehlte hier seit v90: verbuendete
        // Grosskampfschiffe in geschriebenen Wellen hatten keine.
        if(_a) initSubsystems(_a);
        if(_a && _sp.still){ _a.vy=0; _a.minY=_a.y; _a.maxY=_a.y; }
        if(_a && _sp.crossSecs){""")

# ── Unverwundbare Ziele werden nicht beschossen ──────────────────
sub("lock-invuln",
"""function canLockOn(o){
  if(!o) return false;""",
"""function canLockOn(o){
  if(!o) return false;
  // Eine unverwundbare Station ist Kulisse. Auf sie zu halten sieht aus
  // wie ein Fehler und ist einer.
  if(o.invuln) return false;""")
sub("beam-invuln",
"""    for(const o of enemies){
      if(o.dead || o.warp>0 || o.type==='asteroid') continue;""",
"""    for(const o of enemies){
      if(o.dead || o.warp>0 || o.type==='asteroid' || o.invuln) continue;""")

# ── Meldungsfarben: Erfolg gruen, Fehlschlag rot, Teilerfolg gelb ─
sub("msg-colour",
"""    ctx.fillStyle=m.ally?'#ffcc44':'#ff8844';""",
"""    ctx.fillStyle = (m.tone==='good') ? '#3ce06a'
                  : (m.tone==='bad')  ? '#ff4a33'
                  : (m.tone==='warn') ? '#ffcc44'
                  : (m.ally?'#ffcc44':'#ff8844');""")
sub("msg-good1",
"""                     txt: (hullClass(a.img)==='ep') ? 'RESCUED' : 'DELIVERED',
                     life:150, ml:150, ally:true});""",
"""                     txt: (hullClass(a.img)==='ep') ? 'RESCUED' : 'DELIVERED',
                     life:150, ml:150, ally:true, tone:'good'});""")
sub("msg-bad1",
"""      SUB_MSGS.push({x:W-110, y:e.y, txt:'TARGET ESCAPED', life:170, ml:170, ally:false});""",
"""      SUB_MSGS.push({x:W-110, y:e.y, txt:'TARGET ESCAPED', life:170, ml:170,
                     ally:false, tone:'bad'});""")

# ── Teilerfolg ───────────────────────────────────────────────────
# Bisher gab es nur Erfolg und Fehlschlag. Wenn zwei von vier Kapseln
# durchkommen, ist beides falsch.
sub("partial-var",
"""let objWasSet = false, objDoneT = 0, objFailed = false;""",
"""let objWasSet = false, objDoneT = 0, objFailed = false;
// Gerettete und verlorene Schuetzlinge dieser Welle. Daraus entsteht der
// dritte Ausgang zwischen Erfolg und Fehlschlag.
let protSaved = 0, protLost = 0;""")
sub("partial-count-save",
"""      crossDone++;""",
"""      crossDone++; protSaved++;""")
sub("partial-count-lost",
"""      if(a.guard){ guardLost = true; guardGone = true; score = Math.max(0, score-GUARD_PENALTY);""",
"""      if(a.guard){ protLost++; guardLost = true; guardGone = true; score = Math.max(0, score-GUARD_PENALTY);""")
sub("partial-text",
"""      if(objFailed){ txt='[ OBJECTIVE FAILED ]'; col='#cc2200'; ink='#ff5533'; }
      else          { txt='[ OBJECTIVE COMPLETE ]'; col='#00cc44'; ink='#4dff88'; }""",
"""      if(objFailed && protSaved>0){
        // Ein Teil ist durchgekommen: weder Erfolg noch Fehlschlag.
        txt='[ PARTIAL SUCCESS  '+protSaved+'/'+(protSaved+protLost)+' ]';
        col='#bb8800'; ink='#ffcc44';
      }
      else if(objFailed){ txt='[ OBJECTIVE FAILED ]'; col='#cc2200'; ink='#ff5533'; }
      else              { txt='[ OBJECTIVE COMPLETE ]'; col='#00cc44'; ink='#4dff88'; }""")
sub("partial-reset",
"""  objWasSet=false; objDoneT=0; objFailed=false; objSeenOnce=false;""",
"""  objWasSet=false; objDoneT=0; objFailed=false; objSeenOnce=false;
  protSaved=0; protLost=0;""")

# ── M028: der Rammkreuzer traf nicht ─────────────────────────────
# Die Trefferschwelle war (Breite a + Breite b) * 0.30 und damit ein
# Kreis von 152 Bildpunkten - er explodierte irgendwo neben dem Ziel.
# Rechteckig gegen die tatsaechlichen Ausmasse ist richtig.
sub("capram-hit",
"""    const ei=IMGS[e.img], ti=IMGS[t.img];
    const need=((ei?ei.width*e.sc:100)+(ti?ti.width*t.sc:100))*0.30;
    if(L < need){""",
"""    const ei=IMGS[e.img], ti=IMGS[t.img];
    const hwA=(ei?ei.width*e.sc:100)*0.5,  hwB=(ti?ti.width*t.sc:100)*0.5;
    const hhA=(ei?ei.height*e.sc:40)*0.5,  hhB=(ti?ti.height*t.sc:40)*0.5;
    // Waagerecht und senkrecht getrennt pruefen: ein Kreis laesst ihn
    // hoch ueber dem Ziel explodieren, weil der Abstand dort auch klein ist.
    if(Math.abs(dx) < (hwA+hwB)*0.62 && Math.abs(dy) < (hhA+hhB)*0.62){""")

# Ein Rammkurs und sein Ziel duerfen nicht auf und ab schweben, sonst
# verfehlen sie sich staendig.
sub("still-flag",
"""  if(sp.capRam){ e.capRam = sp.capRam; e.noFlee = true; }""",
"""  if(sp.capRam){ e.capRam = sp.capRam; e.noFlee = true; }
  // Kein Auf und Ab: ein Rammstoss auf ein schwebendes Ziel ist Zufall.
  if(sp.still){ e.vy = 0; e.minY = e.y; e.maxY = e.y; }""")
sub("still-q",
"""             x:u.x, escape:u.escape, invuln:u.invuln, edge:u.edge, capRam:u.capRam,""",
"""             x:u.x, escape:u.escape, invuln:u.invuln, edge:u.edge, capRam:u.capRam,
             still:u.still,""")
sub("still-allyq",
"""             crossSecs:u.crossSecs}""",
"""             crossSecs:u.crossSecs, still:u.still}""")

def main():
    if not os.path.exists(SRC): sys.exit("FEHLT: "+SRC)
    txt=io.open(SRC,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(DST,"w",encoding="utf-8").write(txt)
    print("Teil A geschrieben")
main()
