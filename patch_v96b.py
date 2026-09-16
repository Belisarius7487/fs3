#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v96 Teil B: Missionskorrekturen aus dem Spieltest."""
import io, os, sys
F="hlp_shooter_v96_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# M007: Nachschub, solange die Typhon lebt und funkt.
sub("m007",
"""       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'}
     ]},

  8: {name:'Der Rueckzug',""",
"""       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'subsystem', a:'V1', b:'communication', w:'nachschub', a2:'aus'},
       {t:'zerstoert', a:'V1', w:'nachschub', a2:'aus'}
     ]},

  8: {name:'Der Rueckzug',""")

# M010: die Hatshepsut war bei 45 Prozent gegen zwei Bomberstaffeln plus
# Nachschub nicht zu halten. Und von der Arcadia sah man zu wenig.
sub("m010-hp",
"""       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.45},""",
"""       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.80},""")
sub("m010-edge",
"""       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.66},
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.80},""",
"""       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.36},
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.80},""")
sub("m011-edge",
"""       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.66},
       {id:'V1', c:'de', n:1, spr:'detyphon'},""",
"""       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.36},
       {id:'V1', c:'de', n:1, spr:'detyphon'},""")

# M019: die Arcadia ist hier das Ziel, also ganz im Bild, mit Anzeige und
# deutlich mehr Rumpf - eine Station haelt mehr aus als ein Zerstoerer.
sub("m019",
"""       {id:'S1', c:'in', n:1, spr:'inarcadia', edge:0.55},""",
"""       {id:'S1', c:'in', n:1, spr:'inarcadia', hp:2.2, x:560},""")

# M016: die Aten raeumte die Angreifer allein auf. Mehr Gegner, und der
# Nachschub laeuft, bis der Ueberlaeufer gefallen ist.
sub("m016",
"""       {id:'A2', c:'fi', n:2, side:'ally'},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:2, wait:true}""",
"""       {id:'A2', c:'fi', n:2, side:'ally'},
       {id:'E1', c:'fi', n:3},
       {id:'E2', c:'fi', n:3, wait:true}""")
sub("m016-reinf",
"""       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A2'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}""",
"""       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A2'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'A2', w:'nachschub', a2:'aus'}""")

# M018: die Hatshepsut war zu schnell weg. Sie bleibt laenger und der
# Nachschub hoert erst auf, wenn beide Rammstaffeln gefallen sind.
sub("m018",
"""      ev:[{t:'alleZerstoert', a:'K1', w:'einwarpen', a2:'K2'}], u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally'},""",
"""      ev:[{t:'alleZerstoert', a:'K1', w:'einwarpen', a2:'K2'},
          {t:'alleZerstoert', a:'K1', w:'nachschub', a2:'an'},
          {t:'alleZerstoert', a:'K2', w:'nachschub', a2:'aus'}], u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:1.35},""")

# M021: feste, sich ueberlappende Bahnen statt Startversatz. Alle drei
# nutzen die ganze Hoehe, nur zeitversetzt und in wechselnder Richtung.
sub("m021",
"""  21:{name:'Die Sperre', fac:'hol', o:'clear', live:4, u:[
       {id:'K1', c:'cr', n:3, spr:'craten'},""",
"""  21:{name:'Die Sperre', fac:'hol', o:'clear', live:4, u:[
       {id:'K1', c:'cr', n:3, spr:'craten', lanes:true},""")

# M026 und M029: beide waren an der falschen Stelle zu hart.
sub("m026",
"""       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', crossSecs:70},""",
"""       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', crossSecs:70, hp:1.5},""")
sub("m029",
"""       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.6},
       {id:'V1', c:'co', n:2, spr:'cosobek'},""",
"""       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:1.1},
       {id:'V1', c:'co', n:2, spr:'cosobek', hp:0.7},""")

def main():
    txt=io.open(F,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(F,"w",encoding="utf-8").write(txt)
    print("Teil B geschrieben")
main()
