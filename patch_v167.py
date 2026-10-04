#!/usr/bin/env python3
"""FS3 v167 - M62 without its own hull surcharge.

    M62       the Shivan cruisers lose the extra hull they had (+30 %, the
              last one +50 %). The general step every 20 waves stays as it
              is (x1.75 from wave 61, x2.0 from 81) - Silvio: it is meant
              to get harder.

Needs v166. Edits src/30_waves.js in place. Run assemble.py afterwards.
"""
import base64
import os
import sys

if "ATTACK_PASS_FI" not in open("src/50_combat.js", encoding="utf-8").read():
    sys.exit("Abbruch: erst v166 einspielen.")
if "No extra hull of their own" in open("src/30_waves.js", encoding="utf-8").read():
    sys.exit("Abbruch: v167 ist schon eingespielt.")

F = {}
def load(p):
    if p not in F: F[p] = open(p, encoding="utf-8").read()
def rep(p, old, new, count=1):
    load(p)
    n = F[p].count(old)
    if n != count:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet %d.\n%s" % (p, n, count, old[:200]))
    F[p] = F[p].replace(old, new)

rep('src/30_waves.js',
    "       {id:'P1', c:'in', n:1, spr:'inknossos45deg', invuln:true, edge:0.5, y:275},\n       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', x:150, y:270, still:true,\n        guard:true, callsOk:true},\n       {id:'K1', c:'cr', n:1, spr:'crcain',     t:3,  noFlee:true, hp:1.3},\n       {id:'K2', c:'cr', n:1, spr:'crlilith',   t:14, noFlee:true, hp:1.3},\n       {id:'K3', c:'cr', n:1, spr:'crrakshasa', wait:true, noFlee:true, hp:1.3},\n       {id:'K4', c:'cr', n:1, spr:'crcain',     wait:true, noFlee:true, hp:1.3},\n       {id:'K5', c:'cr', n:1, spr:'crrakshasa', wait:true, noFlee:true, hp:1.5},\n       {id:'E1', c:'fi', n:2},\n       {id:'B1', c:'bo', n:1, wait:true},\n       {id:'B2', c:'bo', n:2, wait:true},\n",
    "       {id:'P1', c:'in', n:1, spr:'inknossos45deg', invuln:true, edge:0.5, y:275},\n       {id:'A1', c:'de', n:1, spr:'deorionright', side:'ally', x:150, y:270, still:true,\n        guard:true, callsOk:true},\n       // No extra hull of their own (Silvio, v167): the step every 20 waves\n       // (x1.75 from 61) is hard enough.\n       {id:'K1', c:'cr', n:1, spr:'crcain',     t:3,  noFlee:true},\n       {id:'K2', c:'cr', n:1, spr:'crlilith',   t:14, noFlee:true},\n       {id:'K3', c:'cr', n:1, spr:'crrakshasa', wait:true, noFlee:true},\n       {id:'K4', c:'cr', n:1, spr:'crcain',     wait:true, noFlee:true},\n       {id:'K5', c:'cr', n:1, spr:'crrakshasa', wait:true, noFlee:true},\n       {id:'E1', c:'fi', n:2},\n       {id:'B1', c:'bo', n:1, wait:true},\n       {id:'B2', c:'bo', n:2, wait:true},\n")

for p, t in F.items():
    open(p, "w", encoding="utf-8").write(t)
print("v167 eingespielt. Jetzt: python3 assemble.py 167")
