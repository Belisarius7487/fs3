# v208: export the engine glow points (POF chunk FUEL) of every FS3 hull, in
# the same mirrored model space webmodel.py writes (-x, y, z), so the game
# normalises them with the model head's centre and ext (like the shields).
# Usage: python3 -I mkthrusters.py <pof tools dir> <out.json>
# Per hull: list of [x, y, z, nx, ny, nz, radius] (one per glow point).
import sys, json, os
sys.path.insert(0, sys.argv[1])
import poflite, pof
src_b = open(os.path.join(sys.argv[1], 'buildmodels.py')).read().split('import pof\nif __name__')[0]
src_b = src_b.replace('import webmodel', '').replace("for f in glob.glob(M + '*/data/maps/*'):", 'for f in []:')
ns = {'__file__': 'buildmodels.py'}; sys.argv_save = sys.argv; exec(src_b, ns)
HULLS, M = ns['HULLS'], ns['M']
NTF = '/mnt/user-data/uploads/fs3-claude-export/NTF_Ship_Textures-2.1.2/data/models/'
out, miss = {}, []
for key, (d, name) in sorted(HULLS.items()):
    src = (NTF if d == 'NTF' else M + d + '/data/models/') + name + '.pof'
    if not os.path.exists(src): miss.append(key); continue
    m = poflite.read(src)
    y2z = pof.REORIENT.get(os.path.basename(src).lower()) == 'y2z'
    g = []
    for t in m['thrusters']:
        for p in t['glows']:
            P, N = p['pos'], p['normal']
            if y2z: P, N = [P[0], -P[2], P[1]], [N[0], -N[2], N[1]]
            g.append([round(-P[0], 2), round(P[1], 2), round(P[2], 2),
                      round(-N[0], 3), round(N[1], 3), round(N[2], 3), round(p['rad'], 2)])
    if g: out[key] = g
json.dump(out, open(sys.argv[2], 'w'), separators=(',', ':'))
print(len(out), 'hulls with thrusters,', sum(len(v) for v in out.values()), 'glows; missing POF:', miss)
print('without FUEL:', sorted(set(HULLS) - set(out) - set(miss)))
