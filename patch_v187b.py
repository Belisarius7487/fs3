#!/usr/bin/env python3
"""FS3 v187b - seekers come round again.

    Missiles    A seeker turns as fast as its FS2 turn time says, whatever
                its speed. Until now the turn did not grow with the speed,
                so the faster FS2 missiles - the Harpoon first of all -
                swung wide and sailed past what they chased (Silvio: "my
                Harpoon only flies straight"). Bombs keep their slow turn.

Needs v187. Edits src/56_banks.js and wpnsim.js in place. Run assemble.py
afterwards.
"""
import base64
import os
import sys

if "CLUSTER_CHILD" not in open("src/60_effects.js", encoding="utf-8").read():
    sys.exit("Abbruch: erst v187 einspielen.")
if "v187b" in open("src/56_banks.js", encoding="utf-8").read():
    sys.exit("Abbruch: v187b ist schon eingespielt.")

F = {}
def load(p):
    if p not in F: F[p] = open(p, encoding="utf-8").read()
def rep(p, old, new, count=1):
    load(p)
    n = F[p].count(old)
    if n != count:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet %d.\n%s" % (p, n, count, old[:200]))
    F[p] = F[p].replace(old, new)
rep('src/56_banks.js',
    "    w.cd   = Math.max(6, Math.round(f.w*60));\n    w.spd  = f.v*MPS_TO_PX;\n    w.life = Math.round(f.l*60);\n    w.turn = ((w.cls==='bomb') ? 0.06 : 0.18) / (f.turn||1);\n    w.cargo = f.cargo;\n    if(f.child){            // spawned warheads, same anchor as the round\n      w.childDmg  = f.child.d * anc.game / anc.d;\n",
    "    w.cd   = Math.max(6, Math.round(f.w*60));\n    w.spd  = f.v*MPS_TO_PX;\n    w.life = Math.round(f.l*60);\n    // Turn: FS2's $Turn Time is the time for a half circle, whatever the\n    // speed. A missile steers by adding turn to its velocity each step, so\n    // a faster one needs more of it to come round as quickly (v187b: the\n    // Harpoon is faster than the old MX-64 and sailed past what it chased).\n    // Bombs keep their slow fixed rate.\n    w.turn = (w.cls==='bomb') ? 0.06 / (f.turn||1)\n                              : w.spd * Math.PI / (60 * (f.turn||1));\n    w.cargo = f.cargo;\n    if(f.child){            // spawned warheads, same anchor as the round\n      w.childDmg  = f.child.d * anc.game / anc.d;\n")
rep('wpnsim.js',
    "  clear();\n}\n\nconsole.log('\\nv187: Lamprey, Hornet, Piranha, Helios are out');\n{\n  const gone = ['lamprey','hornet','piranha','helios'];\n",
    '  clear();\n}\n\nconsole.log(\'\\nv187b: a seeker comes round in its FS2 turn time, whatever its speed\');\n{\n  const h = run("secDefP(\'harpoon\')"), r = run("secDefP(\'rockeye\')");\n  const halfCircle = w => Math.PI / (w.turn / w.spd) / 60;   // seconds for 180 degrees\n  ok(\'Harpoon: 1.0 s\', Math.abs(halfCircle(h)-1.0) < 1e-9);\n  ok(\'Rockeye: 0.85 s\', Math.abs(halfCircle(r)-0.85) < 1e-9);\n  // Fired straight down at a fighter well off to the side (65 degrees off\n  // the nose, 300 points away): it comes round and gets there. Closer in\n  // than its turning circle it would orbit, as in FS2.\n  const e = {x:600, y:390, hp:1e6, maxHp:1e6, dead:false, type:\'fighter\', img:\'fidragon\', w:30, h:12};\n  run(\'enemies.length=0\'); run(\'enemies\').push(e);\n  fitShip(\'fitoth\', [\'promr\'], [\'harpoon\']);\n  run(\'player.x=300; player.y=250; player.head=Math.PI/2; player.secTimer=0; fireSecondary()\');\n  const m = bullets().find(x=>x.sec);\n  let best = 1e9;\n  for(let i=0;i<150 && bullets().indexOf(m)>=0;i++){ run(\'updateSecBullets()\'); best = Math.min(best, Math.hypot(m.x-e.x, m.y-e.y)); }\n  ok(\'a Harpoon launched sideways still reaches its target (closest \'+Math.round(best)+\')\', best < 12 || bullets().indexOf(m)<0);\n  run(\'enemies.length=0\'); clear();\n}\n\nconsole.log(\'\\nv187: Lamprey, Hornet, Piranha, Helios are out\');\n{\n  const gone = [\'lamprey\',\'hornet\',\'piranha\',\'helios\'];\n')

for p, t in F.items():
    open(p, "w", encoding="utf-8").write(t)
print("v187b eingespielt. Jetzt: python3 assemble.py 187")
