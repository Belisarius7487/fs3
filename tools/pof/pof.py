# Minimal reader for FreeSpace POF models (tested with version 2301,
# BSP2 layout: op 7 = sortnorm2, op 6 = tmap2poly, op 1 = defpoints).
# Reads submodels with their triangles, textures and the special points
# (subsystems, turrets, docks, thrusters) the game could use.
import re
import struct

class R:
    def __init__(self, d, p=0): self.d, self.p = d, p
    def i(self): v = struct.unpack_from('<i', self.d, self.p)[0]; self.p += 4; return v
    def f(self): v = struct.unpack_from('<f', self.d, self.p)[0]; self.p += 4; return v
    def v3(self): v = struct.unpack_from('<3f', self.d, self.p); self.p += 12; return list(v)
    def s(self):
        n = self.i(); v = self.d[self.p:self.p+n].split(b'\0')[0].decode('latin1'); self.p += n; return v

def read_bsp(d, base, size):
    """Return (positions, normals, tris) for one submodel's BSP block.
    tris: list of (tmap, [(vert, norm, u, v), ...])."""
    verts, norms, tris = [], [], []
    b, e = base, base + size
    while b + 8 <= e:
        oid, osz = struct.unpack_from('<ii', d, b)
        if oid == 1:                                   # defpoints
            nv, nn, off = struct.unpack_from('<3i', d, b + 8)
            counts = d[b + 20:b + 20 + nv]
            q = b + off
            for k in range(nv):
                verts.append(struct.unpack_from('<3f', d, q)); q += 12
                for _ in range(counts[k]):
                    norms.append(struct.unpack_from('<3f', d, q)); q += 12
            b += osz
        elif oid == 7:                                 # sortnorm2 header only
            b += 40
        elif oid == 6:                                 # tmap2poly
            tmap, n = struct.unpack_from('<2i', d, b + 44)
            q = b + 52; vs = []
            for _ in range(n):
                vs.append(struct.unpack_from('<2i2f', d, q)); q += 16
            tris.append((tmap, vs)); b += osz
        elif oid == 3:                                 # tmappoly (older POFs, v201)
            n, tmap = struct.unpack_from('<2i', d, b + 36)
            q = b + 44; vs = []
            for _ in range(n):
                vi, ni = struct.unpack_from('<2H', d, q); u, v = struct.unpack_from('<2f', d, q + 4)
                vs.append((vi, ni, u, v)); q += 12
            tris.append((tmap, vs)); b += osz
        elif oid == 4:
            # SORTNORM: a BSP node whose polygons sit in its children, right
            # behind its 80-byte header (front/back offsets point there).
            # Skipping it by its size threw the whole subtree away - the PVI
            # Karnak came out with 0 of her 12 MB of polygons (v235). The
            # scan is linear, so stepping over the header alone walks front
            # and back in turn. SORTNORM2 (7) is the newer form of the same
            # thing and was already handled this way.
            b += 80
        elif oid in (2, 5):                            # flatpoly, boundbox
            b += osz
        elif oid == 0:
            b += max(8, osz)
        else:
            raise ValueError('unknown bsp op %d at %d' % (oid, b - base))
    return verts, norms, tris

def read_pof(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'PSPO'
    out = {'version': struct.unpack_from('<i', d, 4)[0], 'subs': [], 'textures': [],
           'special': [], 'turrets': [], 'docks': [], 'thrusters': [], 'eyes': []}
    p = 8
    while p + 8 <= len(d):
        cid = d[p:p+4].decode('latin1'); ln = struct.unpack_from('<i', d, p+4)[0]
        r = R(d, p + 8)
        if cid == 'HDR2':
            out['radius'] = r.f(); r.i(); r.i()
            out['bbox'] = [r.v3(), r.v3()]
            out['details'] = [r.i() for _ in range(r.i())]
            out['debris'] = [r.i() for _ in range(r.i())]
        elif cid == 'OBJ2':
            sm = {'num': r.i(), 'rad': r.f(), 'parent': r.i(), 'offset': r.v3(),
                  'center': r.v3(), 'min': r.v3(), 'max': r.v3()}
            sm['name'] = r.s(); sm['props'] = r.s()
            # rotation type and axis (0 x, 1 z, 2 y as FreeSpace counts),
            # translation, reserved (v201: moving parts)
            sm['rot_type'] = r.i(); sm['rot_axis'] = r.i()
            r.p += 12 if out['version'] >= 2301 else 4
            bsz = r.i()
            sm['verts'], sm['norms'], sm['tris'] = read_bsp(d, r.p, bsz)
            out['subs'].append(sm)
        elif cid == 'TXTR':
            out['textures'] = [r.s() for _ in range(r.i())]
        elif cid == 'SPCL':
            for _ in range(r.i()):
                out['special'].append({'name': r.s(), 'props': r.s(), 'pos': r.v3(), 'rad': r.f()})
        elif cid == 'TGUN':
            for _ in range(r.i()):
                t = {'sub': r.i(), 'phys': r.i(), 'normal': r.v3()}
                t['points'] = [r.v3() for _ in range(r.i())]
                out['turrets'].append(t)
        elif cid == 'DOCK':
            for _ in range(r.i()):
                dk = {'props': r.s()}
                dk['paths'] = [r.i() for _ in range(r.i())]
                dk['points'] = [[r.v3(), r.v3()] for _ in range(r.i())]
                out['docks'].append(dk)
        elif cid == 'FUEL':
            for _ in range(r.i()):
                n = r.i(); props = r.s()
                out['thrusters'].append({'props': props,
                    'glows': [{'pos': r.v3(), 'normal': r.v3(), 'rad': r.f()} for _ in range(n)]})
        p += 8 + ln
    # Submodels may be stored out of their number's order (Ma'at, v202);
    # parents, details and debris refer to the numbers, so the list is put
    # in number order.
    if sorted(s['num'] for s in out['subs']) == list(range(len(out['subs']))):
        out['subs'].sort(key=lambda s: s['num'])
    import os
    rx = REORIENT.get(os.path.basename(path).lower())
    if rx: reorient(out, rx)
    return out

# Models whose long axis is not the bow (+z). v202: the Mjolnir's barrel
# lies along +y; turned so it points ahead like a ship's bow.
REORIENT = {'mjolnir.pof': 'y2z'}
# FreeSpace axis ids (0 x, 1 z, 2 y) after the turn
_AX_Y2Z = {0: 0, 1: 2, 2: 1}
def reorient(m, how):
    """Turn every position and direction of a read model in place."""
    if how != 'y2z': raise ValueError(how)
    f = lambda v: [v[0], -v[2], v[1]]          # +y -> +z, +z -> -y
    for sm in m['subs']:
        for k in ('offset', 'center'): sm[k] = f(sm[k])
        a, b = f(sm['min']), f(sm['max'])
        sm['min'] = [min(a[i], b[i]) for i in range(3)]; sm['max'] = [max(a[i], b[i]) for i in range(3)]
        sm['verts'] = [tuple(f(v)) for v in sm['verts']]
        sm['norms'] = [tuple(f(v)) for v in sm['norms']]
        sm['rot_axis'] = _AX_Y2Z.get(sm['rot_axis'], sm['rot_axis'])
        def uv(mm):
            v = f([float(x) for x in mm.groups()])
            return '$uvec=%g,%g,%g' % tuple(v)
        sm['props'] = re.sub(r'\$uvec\s*[:=]\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)', uv, sm['props'])
    if 'bbox' in m:
        a, b = f(m['bbox'][0]), f(m['bbox'][1])
        m['bbox'] = [[min(a[i], b[i]) for i in range(3)], [max(a[i], b[i]) for i in range(3)]]
    for s in m['special']: s['pos'] = f(s['pos'])
    for t in m['turrets']:
        t['normal'] = f(t['normal']); t['points'] = [f(v) for v in t['points']]
    for dk in m['docks']: dk['points'] = [[f(a), f(b)] for a, b in dk['points']]
    for th in m['thrusters']:
        for g in th['glows']: g['pos'] = f(g['pos']); g['normal'] = f(g['normal'])

def world_offset(subs, k):
    """Sum of offsets from submodel k up to its root."""
    o = [0.0, 0.0, 0.0]
    while k >= 0:
        sm = subs[k]
        o = [o[0] + sm['offset'][0], o[1] + sm['offset'][1], o[2] + sm['offset'][2]]
        k = sm['parent']
    return o
