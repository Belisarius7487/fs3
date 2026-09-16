#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v98 Teil B: vier weitere Missionen."""
import io, os, sys
F="hlp_shooter_v98_logic.html"
txt=io.open(F,encoding="utf-8").read()

BLOCK = r"""  20:{name:'Die Ueberlebenden', fac:'hol', o:'clear', live:6, hunt:'P1', u:[
       // Er steht brennend im Feld und wird bereits beschossen. Zu retten
       // ist er nicht: solange er lebt, kommt Nachschub, und jeder frueh
       // getoetete Jaeger verlaengert nur sein Leben - und damit die Zahl
       // der Kapseln, die es herausschaffen.
       {id:'K1', c:'cr', n:1, spr:'craten', side:'ally', hp:0.22},
       {id:'E1', c:'fi', n:2},
       {id:'P1', c:'ep', n:4, spr:'epra', side:'ally', cross:0.34, wait:true}
     ], ev:[
       {t:'sek', a:1, w:'nachschub', a2:'an'},
       {t:'zerstoert', a:'K1', w:'nachschub', a2:'aus'},
       {t:'zerstoert', a:'K1', w:'einwarpen', a2:'P1'},
       {t:'zerstoert', a:'K1', w:'meldung', a2:'escape pods away'},
       {t:'zerstoert', a:'K1', w:'auftrag', a2:'protect'}
     ]},

  24:{name:'Der Hinterhalt', fac:'hol', o:'clear', live:6, u:[
       {id:'A1', c:'fi', n:2, side:'ally'},
       {id:'E1', c:'fi', n:3},
       {id:'V1', c:'cr', n:2, spr:'craten', wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'meldung', a2:'escort turning hostile'},
       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A1'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'V1'}
     ]},

  28:{name:'Der Rammstoss', fac:'hol', o:'guard', live:5, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:1.1},
       {id:'V1', c:'cr', n:1, spr:'crmentu', capRam:0.55},
       {id:'E1', c:'fi', n:2}
     ], ev:[
       {t:'sek', a:2, w:'meldung', a2:'cruiser on ramming course'}
     ]},

  30:{name:'Der Boss', fac:'hol', o:'guard', live:6, u:[
       // Die Hatshepsut, die du vier Wellen lang beschuetzt hast, steht
       // mit im Feld. Faellt eines der beiden feindlichen Schiffe, kommt
       // die dritte - erst dann ist Platz fuer sie.
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.9},
       {id:'V1', c:'de', n:1, spr:'detyphon'},
       {id:'V2', c:'cr', n:1, spr:'craten'},
       {id:'V3', c:'de', n:1, spr:'dehatshepsut', wait:true},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:2, wait:true}
     ], ev:[
       {t:'zerstoert', a:'V2', w:'einwarpen', a2:'V3'},
       {t:'zerstoert', a:'V1', w:'einwarpen', a2:'V3'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'B1'},
       {t:'alleZerstoert', a:'E1', w:'nachschub', a2:'an'},
       {t:'zerstoert', a:'V3', w:'nachschub', a2:'aus'}
     ]},

"""
anchor = "  21:{name:'Die Sperre',"
assert txt.count(anchor)==1
txt = txt.replace(anchor, BLOCK + anchor, 1)

# Nur die Aten darf fliehen, die Zerstoerer nicht - deine Regel von damals.
old = """       {id:'V2', c:'cr', n:1, spr:'craten'},"""
new = """       {id:'V2', c:'cr', n:1, spr:'craten'},   // nur sie darf fliehen"""
txt = txt.replace(old,new,1)

io.open(F,"w",encoding="utf-8").write(txt)
print("Teil B geschrieben: M020, M024, M028, M030")
