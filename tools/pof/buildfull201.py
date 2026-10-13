# v201: 'full' level of the capital ships with their moving parts kept
# apart (turret bases and barrels, spinning dishes), gzipped: full.bin.gz.
# The browser unpacks it (DecompressionStream). Textures stay as they are.
import os, sys, gzip, json, re
import pof, webmodel
from buildmodels import HULLS, M, maps
OUT = sys.argv[1]
keys = sys.argv[2].split(',')
for key in keys:
    d, name = HULLS[key]
    src = M + d + '/data/models/' + name + '.pof'
    m = pof.read_pof(src)
    # v202: the debris pieces' maps (dead, damage, debris) count as skin too
    skin = set(t.lower() for t in m['textures'] if t.lower() in maps and
               (webmodel.kind_of(t) == 'tex' or not re.match(r'(invisible|thruster|nameplate)', t.lower())))
    data, nt = webmodel.build_level(m, 0, skin, False, True)
    os.makedirs(os.path.join(OUT, key), exist_ok=True)
    gz = gzip.compress(data, 9, mtime=0)
    open(os.path.join(OUT, key, 'full.bin.gz'), 'wb').write(gz)
    hl = int.from_bytes(data[:4], 'little'); head = json.loads(data[4:4 + hl])
    nodes = head.get('nodes') or []
    kinds = {}
    for n in nodes[1:]: kinds[n['k']] = kinds.get(n['k'], 0) + 1
    print(key, nt, 'tris', len(data) // 1024, 'KB ->', len(gz) // 1024, 'KB gz', 'parts', len(head['parts']), 'nodes', kinds, flush=True)
