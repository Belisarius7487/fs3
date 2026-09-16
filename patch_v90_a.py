#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v89 -> v90, Teil A: Merkliste abarbeiten."""
import io, os, sys
SRC="hlp_shooter_v89_logic.html"; DST="hlp_shooter_v90_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# 1  Fraktionsanzeige raus. Sie kannte zwei Faelle und schrieb bei HoL
#    "Shivaner". Ersatzlos: welche Fraktion gerade dran ist, sagen
#    Rumpfformen und Triebwerksfarben besser als ein Wort in der Leiste.
sub("hud-faction",
"""  ctx.fillStyle=currentFaction==='ntf'?'#4499ff':'#ff4422';""",
"""  ctx.fillStyle='#4499ff';""")

# 2  Dieselbe Zwei-Faelle-Annahme an drei weiteren Stellen. v88 hat
#    mkEnemy umgestellt, aber nicht die Aufrufer, die Typen selbst
#    zusammensetzen - deshalb standen NTF-Bomber in HoL-Wellen.
sub("capbomb-fac",
"""  const type = currentFaction==='shivan' ? 'bo_sh' : 'bo_ntf';""",
"""  const type = 'bo_' + FAC_TAG[currentFaction];""")
sub("bosscall-fac",
"""    const sfx = e.faction==='shivan' ? '_sh' : '_ntf';""",
"""    const sfx = '_' + FAC_TAG[e.faction];""")
sub("fac-tag",
"""const FAC_SFX  = {ntf:'ntf', sh:'shivan', hol:'hol'};""",
"""const FAC_SFX  = {ntf:'ntf', sh:'shivan', hol:'hol'};
// Rueckrichtung: Fraktion -> Kuerzel im Typnamen. Ohne sie fiel jede
// Stelle, die einen Typ selbst zusammensetzt, auf zwei Faelle zurueck.
const FAC_TAG  = {ntf:'ntf', shivan:'sh', hol:'hol', renegade:'ntf'};""")

# 3  Wellenueberschrift raus. Sie zeigte in v81 die zehn FS1-Missionstitel;
#    "LONE CORVETTE" traegt nichts.
sub("title-off",
"""function drawWaveTitle(){
  if(GS!=='playing' || !waveTitle || titleT<=0) return;""",
"""function drawWaveTitle(){
  return;   // Wellenueberschrift abgeschaltet, siehe Kommentar oben
  /* eslint-disable no-unreachable */
  if(GS!=='playing' || !waveTitle || titleT<=0) return;""")
sub("title-off-end",
"""  ctx.fillText(waveTitle, W/2, (H*0.30)|0+5);
  ctx.restore();
}""",
"""  ctx.fillText(waveTitle, W/2, (H*0.30)|0+5);
  ctx.restore();
  /* eslint-enable no-unreachable */
}""")

# 4  Strahlenfarbe des Hammer of Light. Weiss war der Rueckfall, weil die
#    Farbtabelle die Fraktion nicht kannte. Vasudanische Strahlen sind nie
#    weiss - HoL fliegt vasudanische Ruempfe und bekommt deren Farbe.
#    Die Triebwerke bleiben orange: die tragen die Feind-Freund-Kennung,
#    die Strahlen nicht.
sub("beam-colour",
"""function beamCol(faction, large) {
  if(faction==='ntf' || faction==='terran') return large ? '#00ff55' : '#4499ff';""",
"""function beamCol(faction, large) {
  // Weiss war der Rueckfall, weil die Tabelle den Hammer of Light nicht
  // kannte. Vasudanische Strahlen sind nie weiss, und HoL fliegt
  // vasudanische Ruempfe. Die Triebwerke bleiben orange: die tragen die
  // Feind-Freund-Kennung, die Strahlen nicht.
  if(faction==='hol') faction = 'vasudan';
  if(faction==='ntf' || faction==='terran') return large ? '#00ff55' : '#4499ff';""")

# 5  Lahmlegen erst spaeter. Welle 4 wird eine Jagd, Welle 9 eine Eskorte.
sub("seq-4-9",
"""  {k:'lonecr',    o:'disable', f:'ntf'},     //  4  erstes Subsystem""",
"""  {k:'lonecr',    o:'runner',  f:'ntf'},     //  4  erstes Grosskampfschiff, als Jagd""")
sub("seq-9",
"""  {k:'loneco',    o:'disable', f:'shivan'},  //  9  Sekundaer unter Beschuss""",
"""  {k:'loneco',    o:'guard',   f:'shivan'},  //  9  Eskorte gegen eine Korvette""")

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
