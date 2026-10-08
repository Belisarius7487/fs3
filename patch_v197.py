#!/usr/bin/env python3
"""FS3 v197 - the Shivan capital ships in 3D.

    Field      Cain, Lilith, Rakshasa, Moloch, Demon, Ravana, Lucifer and
               Sathanas are drawn from their MediaVP models like the GTVA
               support ships since v196. The models (all detail levels and
               the full one) come in models_v197.zip. Hits, mounts, shields,
               the Lucifer's reactors and the damage logic are unchanged.
               Still sprites: the NTF reskins, the Hades, freighters and
               stations - their models come later.

Needs v196. Edits src/59_field3d.js and fieldsim.js. Run assemble.py
afterwards.
"""
import base64
import os
import sys

if not os.path.exists("src/59_field3d.js"):
    sys.exit("Abbruch: erst v196 einspielen.")
if "'sdsathanas'" in open("src/59_field3d.js", encoding="utf-8").read():
    sys.exit("Abbruch: v197 ist schon eingespielt.")

F = {}
def load(p):
    if p not in F: F[p] = open(p, encoding="utf-8").read()
def rep(p, old, new, count=1):
    load(p)
    n = F[p].count(old)
    if n != count:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet %d.\n%s" % (p, n, count, old[:200]))
    F[p] = F[p].replace(old, new)
rep('src/59_field3d.js',
    "// share one depth buffer, so an overlap is a real overlap.\n// Without WebGL, until a model has loaded, or for a hull without a model\n// (the Shivans and the NTF reskins for now) the sprite is drawn as before.\nconst F3D_KEYS = ['crfenris', 'crleviathan', 'craeolus', 'codeimos', 'deorionright', 'dehecate',\n  'craten', 'crmentu', 'cosobek', 'detyphon', 'dehatshepsut', 'sdcolossus', 'sgmjolnir',\n  'cacharybdis', 'casetekh', 'coiceni'];\nconst F3D_ALIAS = {deorionleft: 'deorionright'};\n",
    "// share one depth buffer, so an overlap is a real overlap.\n// Without WebGL, until a model has loaded, or for a hull without a model\n// (the Shivans and the NTF reskins for now) the sprite is drawn as before.\n// v197: the Shivan capital ships as well (first line)\nconst F3D_KEYS = ['crcain', 'crlilith', 'crrakshasa', 'comoloch', 'dedemon', 'deravana', 'sdlucifer', 'sdsathanas',\n  'crfenris', 'crleviathan', 'craeolus', 'codeimos', 'deorionright', 'dehecate',\n  'craten', 'crmentu', 'cosobek', 'detyphon', 'dehatshepsut', 'sdcolossus', 'sgmjolnir',\n  'cacharybdis', 'casetekh', 'coiceni'];\nconst F3D_ALIAS = {deorionleft: 'deorionright'};\n")
rep('fieldsim.js',
    "\nscenario('v196: 3D capitals - keys, sprite fallback, damage marks alone', 'm=62', `\n  const r = {};\n  r.keys = f3dKey({img:'deorionleft'}) === 'deorionright' && f3dKey({img:'ntfdeorion'}) === null && f3dKey({img:'crcain'}) === null;\n  // no model files here (file://): every ship stays a sprite, nothing breaks\n  const done = f3dFieldPass(enemies.concat(allies));\n  r.fallback = done.size === 0;\n",
    "\nscenario('v196: 3D capitals - keys, sprite fallback, damage marks alone', 'm=62', `\n  const r = {};\n  r.keys = f3dKey({img:'deorionleft'}) === 'deorionright' && f3dKey({img:'ntfdeorion'}) === null && f3dKey({img:'crcain'}) === 'crcain' && f3dKey({img:'sdsathanas'}) === 'sdsathanas';\n  // no model files here (file://): every ship stays a sprite, nothing breaks\n  const done = f3dFieldPass(enemies.concat(allies));\n  r.fallback = done.size === 0;\n")

for p, t in F.items():
    open(p, "w", encoding="utf-8").write(t)
print("v197 eingespielt. Jetzt: python3 assemble.py 197")
