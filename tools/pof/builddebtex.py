# v202: the maps of the debris pieces (dead, damage, debris textures) for
# every 3D hull, written next to her other maps. Small pieces: 512 pixels,
# under the name the field loads (_1024).
import os, sys, glob
import pof, webmodel
from buildmodels import HULLS, M, maps, SMALL_NEW, PLAYER
# v203: the small craft load their maps at 512 - the pieces' maps under that name too
SMALL = set(SMALL_NEW + PLAYER)
OUT = sys.argv[1]
keys = sys.argv[2].split(',')
for key in keys:
    d, name = HULLS[key]
    m = pof.read_pof(M + d + '/data/models/' + name + '.pof')
    tx = set()
    for s in m['debris']:
        for tm, _ in m['subs'][s]['tris']:
            if tm < len(m['textures']): tx.add(m['textures'][tm].lower())
    made = []
    for t in sorted(tx):
        if t not in maps or t.startswith(('invisible', 'thruster', 'nameplate')): continue
        names = ('1024', '512') if key in SMALL else ('1024',)
        if all(os.path.exists(os.path.join(OUT, key, t + '_c' + z + '.webp')) for z in names): continue
        os.makedirs(os.path.join(OUT, key), exist_ok=True)
        for k, mode in (('c', 'color'), ('g', 'glow'), ('n', 'normal')):
            f = maps[t] if k == 'c' else maps.get(t + ('-glow' if k == 'g' else '-normal'))
            if not f: continue
            w = webmodel.texture(f, 512, mode)
            for z in names: open(os.path.join(OUT, key, '%s_%s%s.webp' % (t, k, z)), 'wb').write(w)
            made.append(t + '_' + k)
    print(key, made, flush=True)
