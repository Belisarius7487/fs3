#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v99 Teil B: Missionsanpassungen."""
import io, os, sys
F="hlp_shooter_v99_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# M011: die Station ist Kulisse, ihr Ueberleben braucht keine Meldung.
sub("m011",
"""       {t:'zerstoert', a:'V1', w:'meldung', a2:'station holds'},
       {t:'zerstoert', a:'V1', w:'ende', a2:''}""",
"""       {t:'zerstoert', a:'V1', w:'ende', a2:''}""")

# M020: Kapseln starten an der Aten, und die Gegner gehen erst auf sie,
# dann auf die Kapseln.
sub("m020-at",
"""       {id:'P1', c:'ep', n:4, spr:'epra', side:'ally', cross:0.34, wait:true}""",
"""       {id:'P1', c:'ep', n:4, spr:'epra', side:'ally', cross:0.34, wait:true, at:'K1'}""")
sub("m020-hunt",
"""  20:{name:'Die Ueberlebenden', fac:'hol', o:'clear', live:6, hunt:'P1', u:[""",
"""  20:{name:'Die Ueberlebenden', fac:'hol', o:'clear', live:6, hunt:'K1', u:[""")
sub("m020-jagd",
"""       {t:'zerstoert', a:'K1', w:'auftrag', a2:'protect'}""",
"""       {t:'zerstoert', a:'K1', w:'auftrag', a2:'protect'},
       {t:'zerstoert', a:'K1', w:'jagd', a2:'P1'}""")

# M026: drei Sperrgeschuetze weniger, sonst kommt sie nicht durch.
sub("m026",
"""       {id:'G1', c:'sg', n:12, spr:'sgankh'},""",
"""       {id:'G1', c:'sg', n:9, spr:'sgankh'},""")

# M028: der Kreuzer war zu schnell zum Abfangen.
sub("m028",
"""       {id:'V1', c:'cr', n:1, spr:'crmentu', capRam:0.55},""",
"""       {id:'V1', c:'cr', n:1, spr:'crmentu', capRam:0.16},""")

# M030: der Abschluss des Zyklus. Die Hatshepsut mit im Feld zu haben ist
# das Bild, ihr Ueberleben aber keine Bedingung - drei Grosskampfschiffe
# gleichzeitig von ihr fernzuhalten ist nicht leistbar.
sub("m030",
"""  30:{name:'Der Boss', fac:'hol', o:'guard', live:6, u:[""",
"""  30:{name:'Der Boss', fac:'hol', o:'clear', live:6, u:[""")

def main():
    txt=io.open(F,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(F,"w",encoding="utf-8").write(txt)
    print("Teil B geschrieben")
main()
