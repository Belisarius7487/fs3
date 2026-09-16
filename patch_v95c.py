#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v95 Teil C: Missionen - Nachschub, Haerte, vier Neue."""
import io, os, sys
F="hlp_shooter_v95_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# M003: Jaeger warpen nach, solange der Kreuzer lebt - einer nach dem anderen.
sub("m003",
"""       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'K1'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}""",
"""       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'K1'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'K1', w:'nachschub', a2:'aus'}""")

# M005: zwei Nachschubschuebe statt eines einzigen Durchmarschs.
sub("m005",
"""       {id:'G1', c:'sg', n:4, spr:'sgankh'},
       {id:'E1', c:'fi', n:2}
     ]},""",
"""       {id:'G1', c:'sg', n:5, spr:'sgankh'},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'G1', w:'einwarpen', a2:'E2'},
       {t:'alleZerstoert', a:'G1', w:'nachschub', a2:'an'},
       {t:'verlaesst',     a:'A1', w:'nachschub', a2:'aus'}
     ]},""")

# M006: nach den ersten Wellen kommt weiterer Nachschub, solange die
# feindliche Korvette lebt.
sub("m006",
"""       {id:'B1', c:'bo', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'}
     ]},""",
"""       {id:'B1', c:'bo', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'V1', w:'nachschub', a2:'aus'}
     ]},""")

# M008: die Hatshepsut war bei 55 Prozent gegen vier Bomberstaffeln nicht
# zu halten. Bomber sind gegen Grosskampfschiffe gebaut.
sub("m008",
"""       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.55},""",
"""       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.88},""")

# M012: die Meldung kam auch dann, wenn die Container nach dem Scannen
# starben - dann sind sie aber nicht verloren, sondern abgearbeitet.
sub("m012",
"""       {t:'alleZerstoert',a:'C1', w:'nachschub', a2:'aus'},
       {t:'alleZerstoert',a:'C1', w:'meldung',   a2:'cargo lost'}""",
"""       {t:'alleZerstoert',a:'C1', w:'nachschub', a2:'aus'}""")

# M025: Nachschub, solange noch ein Fluechtling lebt.
sub("m025",
"""       {id:'T1', c:'tr', n:1, spr:'trisis', escape:0.62, x:-40},
       {id:'E1', c:'fi', n:2}
     ]},""",
"""       {id:'T1', c:'tr', n:1, spr:'trisis', escape:0.62, x:-40},
       {id:'E1', c:'fi', n:2}
     ], ev:[
       {t:'sek', a:2, w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'F1', w:'nachschub', a2:'aus'}
     ]},""")

# M026: ohne Druck kam die Hatshepsut mit 5 bis 10 Prozent durch. Nachschub
# von Beginn an, bis sie drueben ist.
sub("m026",
"""       {id:'G1', c:'sg', n:12, spr:'sgankh'},
       {id:'E1', c:'fi', n:3}
     ]},""",
"""       {id:'G1', c:'sg', n:12, spr:'sgankh'},
       {id:'E1', c:'fi', n:3}
     ], ev:[
       {t:'sek', a:3, w:'nachschub', a2:'an'},
       {t:'verlaesst', a:'A1', w:'nachschub', a2:'aus'}
     ]},""")

# M029: sind die Staffeln weg, sind die Korvetten allein keine Bedrohung.
sub("m029",
"""       {id:'V1', c:'co', n:2, spr:'cosobek'},
       {id:'E1', c:'fi', n:2}
     ]}""",
"""       {id:'V1', c:'co', n:2, spr:'cosobek'},
       {id:'E1', c:'fi', n:2}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'V1', w:'nachschub', a2:'aus'}
     ]}""")

# ── Vier neue Missionen ─────────────────────────────────────
sub("new4",
"""  21:{name:'Die Sperre',""",
"""  10:{name:'Die Werft', fac:'hol', o:'guard', live:5, u:[
       // Die Arcadia ist ein Ort, kein Gegner: unverwundbar und zu zwei
       // Dritteln ausserhalb des rechten Randes.
       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.66},
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.45},
       {id:'B1', c:'bo', n:2},
       {id:'E1', c:'fi', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'E1'},
       {t:'alleZerstoert', a:'B1', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'aus'}
     ]},

  11:{name:'Der Sturm', fac:'hol', o:'guard', live:5, keepSky:true, u:[
       {id:'S1', c:'in', n:1, spr:'inarcadia', invuln:true, edge:0.66},
       {id:'V1', c:'de', n:1, spr:'detyphon'},
       {id:'A1', c:'cr', n:1, spr:'craten', side:'ally'},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'zerstoert', a:'V1', w:'meldung', a2:'station holds'},
       {t:'zerstoert', a:'V1', w:'ende', a2:''}
     ]},

  19:{name:'Der Tempel', fac:'hol', o:'clear', live:5, u:[
       // Hier ist die Installation das Ziel, also verwundbar.
       {id:'S1', c:'in', n:1, spr:'inarcadia', edge:0.55},
       {id:'G1', c:'sg', n:8, spr:'sgankh'},
       {id:'E1', c:'fi', n:3},
       {id:'E2', c:'fi', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'},
       {t:'rumpfUnter', a:'S1', b:50, w:'nachschub', a2:'an'},
       {t:'zerstoert', a:'S1', w:'nachschub', a2:'aus'}
     ]},

  22:{name:'Der Fluechtling', fac:'hol', o:'clear', live:5, u:[
       // Er faehrt nach rechts und du kommst nicht an ihn heran, solange
       // die Geschuetze stehen. Genau das ist die Mission.
       {id:'V1', c:'de', n:1, spr:'detyphon', escape:0.22, x:-60},
       {id:'G1', c:'sg', n:8, spr:'sgankh'},
       {id:'E1', c:'fi', n:2}
     ]},

  21:{name:'Die Sperre',""")

def main():
    txt=io.open(F,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(F,"w",encoding="utf-8").write(txt)
    print("Teil C geschrieben")
main()
