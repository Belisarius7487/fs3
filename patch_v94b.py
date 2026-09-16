#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v94 Teil B: Missionen ereignisgesteuert statt zeitgesteuert, plus M004 und M025."""
import io, os, sys
F="hlp_shooter_v94_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# Folgestaffeln haengen an der Vernichtung der vorigen, nicht an der Uhr.
sub("m006-ev",
"""       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, t:14}
     ]},""",
"""       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'}
     ]},""")

sub("m008-ev",
"""       {id:'B1', c:'bo', n:2},
       {id:'B2', c:'bo', n:2, t:16}
     ]},""",
"""       {id:'B1', c:'bo', n:2},
       {id:'B2', c:'bo', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'B2'}
     ]},""")

sub("m013-ev",
"""       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:1, t:18}
     ]},""",
"""       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}
     ]},""")

sub("m016-ev",
"""       {id:'E2', c:'fi', n:2, t:26}""",
"""       {id:'E2', c:'fi', n:2, wait:true}""")
sub("m016-ev2",
"""       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A2'}""",
"""       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A2'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}""")

sub("m018-ev",
"""       {id:'K1', c:'fi', n:3, ram:true},
       {id:'K2', c:'fi', n:2, t:22, ram:true}""",
"""       {id:'K1', c:'fi', n:3, ram:true},
       {id:'K2', c:'fi', n:3, wait:true, ram:true}""")
sub("m018-ev2",
"""  18:{name:'Tenderizer', fac:'hol', o:'guard', live:6, u:[""",
"""  18:{name:'Tenderizer', fac:'hol', o:'guard', live:6,
      ev:[{t:'alleZerstoert', a:'K1', w:'einwarpen', a2:'K2'}], u:[""")

sub("m026-ev",
"""       {id:'G1', c:'sg', n:6, spr:'sgankh'},
       {id:'E1', c:'fi', n:2, t:12}""",
"""       {id:'G1', c:'sg', n:12, spr:'sgankh'},
       {id:'E1', c:'fi', n:3}""")

# ── M004 und M025: Gegner, die nach rechts entkommen ────────
sub("escape-missions",
"""  5: {name:'Durch den Guertel',""",
"""  4: {name:'Der Ausbrecher', fac:'hol', o:'clear', live:5, u:[
       // Sie ist angeschlagen und faehrt nach rechts. Wer sie ziehen
       // laesst, verliert Punkte - das ist die ganze Uhr dieser Welle.
       {id:'V1', c:'co', n:1, spr:'cosobek', hp:0.55, escape:0.30, x:-40},
       {id:'E1', c:'fi', n:2}
     ]},

  25:{name:'Die Flucht', fac:'hol', o:'clear', live:5, u:[
       {id:'F1', c:'fr', n:2, spr:'frbast', escape:0.55, x:-40},
       {id:'T1', c:'tr', n:1, spr:'trisis', escape:0.62, x:-40},
       {id:'E1', c:'fi', n:2}
     ]},

  5: {name:'Durch den Guertel',""")

sub("m007-ev",
"""       {id:'E1', c:'fi', n:1},
       {id:'B1', c:'bo', n:2, t:15}
     ]},""",
"""       {id:'E1', c:'fi', n:1},
       {id:'B1', c:'bo', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'}
     ]},""")

def main():
    txt=io.open(F,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(F,"w",encoding="utf-8").write(txt)
    print("Teil B geschrieben")
main()
