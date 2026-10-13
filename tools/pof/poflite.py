# Header-only POF reader: bbox, submodel names/offsets, special points,
# turrets, docks, thrusters. Skips the geometry, so it is fast on big models.
import struct, sys, json, glob, os
from pof import R
def read(path):
    d = open(path,'rb').read()
    out = {'file': os.path.basename(path), 'version': struct.unpack_from('<i', d, 4)[0],
           'subs': [], 'special': [], 'turrets': [], 'docks': [], 'thrusters': []}
    p = 8
    while p + 8 <= len(d):
        cid = d[p:p+4].decode('latin1'); ln = struct.unpack_from('<i', d, p+4)[0]; r = R(d, p+8)
        if cid == 'HDR2':
            out['radius'] = r.f(); r.i(); r.i(); out['bbox'] = [r.v3(), r.v3()]
            out['details'] = [r.i() for _ in range(r.i())]
        elif cid == 'OBJ2':
            sm = {'num': r.i(), 'rad': r.f(), 'parent': r.i(), 'offset': r.v3()}
            r.v3(); sm['min'] = r.v3(); sm['max'] = r.v3(); sm['name'] = r.s(); sm['props'] = r.s()
            out['subs'].append(sm)
        elif cid == 'SPCL':
            for _ in range(r.i()):
                out['special'].append({'name': r.s(), 'props': r.s(), 'pos': r.v3(), 'rad': r.f()})
        elif cid == 'TGUN':
            for _ in range(r.i()):
                t = {'sub': r.i(), 'phys': r.i(), 'normal': r.v3()}; t['points'] = [r.v3() for _ in range(r.i())]
                out['turrets'].append(t)
        elif cid == 'DOCK':
            for _ in range(r.i()):
                dk = {'props': r.s()}; dk['paths'] = [r.i() for _ in range(r.i())]
                dk['points'] = [[r.v3(), r.v3()] for _ in range(r.i())]; out['docks'].append(dk)
        elif cid == 'FUEL':
            for _ in range(r.i()):
                n = r.i(); props = r.s() if out['version'] >= 2117 else ''
                out['thrusters'].append({'props': props, 'glows': [{'pos': r.v3(), 'normal': r.v3(), 'rad': r.f()} for _ in range(n)]})
        p += 8 + ln
    return out
if __name__ == '__main__':
    res = {}
    for f in sorted(glob.glob('/mnt/user-data/uploads/MVPS-473/*/data/models/*.pof')):
        try: res[os.path.basename(f)] = read(f)
        except Exception as e: print('ERR', f, e)
    json.dump(res, open('pofmeta.json', 'w'))
    for k, m in res.items():
        subs = [s['name'] + ('/' + s['props'].split('$name=')[-1].split('\n')[0] if '$name=' in s['props'] else '') for s in m['subs'] if 'subsystem' in s['props']]
        print(k, m['version'], 'bbox', [round(x) for x in m['bbox'][0]+m['bbox'][1]], '\n   SPCL', [s['name'] for s in m['special'] if 'subsystem' in s['props']], '\n   sub-objs', len(subs), subs[:8])
