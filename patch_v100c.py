#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v100 Teil C: M009, M023, M027 und M028-Anpassung."""
import io, os, sys
F="hlp_shooter_v100_logic.html"
txt=io.open(F,encoding="utf-8").read()

# M028: 70 Prozent langsamer, und weder Kreuzer noch Ziel schweben.
old = """       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:1.1},
       {id:'V1', c:'cr', n:1, spr:'crmentu', capRam:0.16},"""
new = """       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:1.1, still:true},
       {id:'V1', c:'cr', n:1, spr:'crmentu', capRam:0.05, still:true},"""
assert txt.count(old)==1
txt = txt.replace(old,new,1)

BLOCK = r"""  9: {name:'Der Konvoi', fac:'hol', o:'protect', live:6, hunt:'F1', u:[
       // Aten und zwei Frachter queren gemeinsam. Die Container haengen
       // an den Frachtern, sobald sie angedockt haben.
       {id:'A1', c:'cr', n:1, spr:'craten', side:'ally', crossSecs:75},
       {id:'C1', c:'fc', n:2, spr:'fcvc3', side:'ally', x:120},
       {id:'F1', c:'fr', n:2, spr:'frbast', side:'ally', cross:0.38, x:-40,
        dockTo:'C1'},
       {id:'E1', c:'fi', n:3}
     ], ev:[
       {t:'sek', a:2, w:'nachschub', a2:'an'},
       {t:'verlaesst', a:'A1', w:'nachschub', a2:'aus'}
     ]},

  23:{name:'Die Abholung', fac:'hol', o:'scan', live:6, hunt:'C1', u:[
       {id:'C1', c:'fc', n:3, spr:'fcvc3', scan:true, x:200},
       {id:'E1', c:'fi', n:2},
       {id:'F1', c:'fr', n:2, spr:'frbast', side:'ally', cross:0.34, x:-40,
        dockTo:'C1', wait:true}
     ], ev:[
       {t:'erfuellt', a:'', w:'einwarpen', a2:'F1'},
       {t:'erfuellt', a:'', w:'meldung',   a2:'freighters inbound'},
       {t:'erfuellt', a:'', w:'auftrag',   a2:'protect'},
       {t:'erfuellt', a:'', w:'nachschub', a2:'an'},
       {t:'alleZerstoert', a:'F1', w:'nachschub', a2:'aus'}
     ]},

  27:{name:'Die Reparatur', fac:'hol', o:'guard', live:6, u:[
       // Jeder angedockte Transporter setzt den Rumpf ein Viertel hoch.
       // Wer schlecht verteidigt, wartet laenger - das ist die Uhr.
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.30, still:true},
       {id:'T1', c:'tr', n:1, spr:'trisis', side:'ally', x:-40, dockTo:'A1'},
       {id:'T2', c:'tr', n:1, spr:'trisis', side:'ally', x:-40, dockTo:'A1', wait:true},
       {id:'T3', c:'tr', n:1, spr:'trisis', side:'ally', x:-40, dockTo:'A1', wait:true},
       {id:'B1', c:'bo', n:2},
       {id:'B2', c:'bo', n:2, wait:true}
     ], ev:[
       {t:'angedockt', a:'T1', w:'heilen', a2:'A1'},
       {t:'angedockt', a:'T1', w:'einwarpen', a2:'T2'},
       {t:'angedockt', a:'T2', w:'heilen', a2:'A1'},
       {t:'angedockt', a:'T2', w:'einwarpen', a2:'T3'},
       {t:'angedockt', a:'T3', w:'heilen', a2:'A1'},
       {t:'alleZerstoert', a:'B1', w:'einwarpen', a2:'B2'},
       {t:'sek', a:3, w:'nachschub', a2:'an'},
       {t:'angedockt', a:'T3', w:'nachschub', a2:'aus'}
     ]},

"""
anchor = "  21:{name:'Die Sperre',"
assert txt.count(anchor)==1
txt = txt.replace(anchor, BLOCK + anchor, 1)

io.open(F,"w",encoding="utf-8").write(txt)
print("Teil C geschrieben: M009, M023, M027")
