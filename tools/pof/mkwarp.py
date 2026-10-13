# v208: the warp model of MediaVP 5.0.2 (MV_Effects_1/data/models/Warp.pof,
# sub-object warp01a, the finest detail level) for the game: positions,
# texture coordinates and triangles of the disc, scaled to radius 1.
# Usage: python3 -I mkwarp.py <pof tools dir> <Warp.pof> <out.json>
import sys, json, struct
sys.path.insert(0, sys.argv[1])
import pof
d = open(sys.argv[2], 'rb').read()
ver = struct.unpack_from('<i', d, 4)[0]
p = 8; best = None
while p + 8 <= len(d):
    cid = d[p:p+4].decode('latin1'); ln = struct.unpack_from('<i', d, p+4)[0]
    if cid == 'OBJ2':
        r = pof.R(d, p + 8)
        r.i(); rad = r.f(); r.i(); r.v3(); r.v3(); r.v3(); r.v3(); name = r.s(); r.s(); r.i(); r.i()
        r.p += 12 if ver >= 2301 else 4
        bsz = r.i()
        if name.lower() == 'warp01a': best = (r.p, bsz, rad)
    p += 8 + ln
b, size, rad = best; e = b + size
verts, tris = [], []
def walk(b):
    # one chain of BSP ops from b; a sortnorm branches into its children
    while b + 8 <= e:
        oid, osz = struct.unpack_from('<ii', d, b)
        if oid == 0: return
        if oid == 1:
            nv, nn, off = struct.unpack_from('<3i', d, b + 8)
            counts = d[b + 20:b + 20 + nv]; q = b + off
            for k in range(nv):
                verts.append(struct.unpack_from('<3f', d, q)); q += 12 + 12*counts[k]
        elif oid == 4:
            for o in struct.unpack_from('<5i', d, b + 36):
                if o: walk(b + o)
            return
        elif oid == 3:
            n, tmap = struct.unpack_from('<2i', d, b + 36); q = b + 44; vs = []
            for _ in range(n):
                vi, ni = struct.unpack_from('<2H', d, q); u, v = struct.unpack_from('<2f', d, q + 4); vs.append((vi, u, v)); q += 12
            tris.append(vs)
        elif oid == 6:
            tmap, n = struct.unpack_from('<2i', d, b + 44); q = b + 52; vs = []
            for _ in range(n):
                vi, ni, u, v = struct.unpack_from('<2i2f', d, q); vs.append((vi, u, v)); q += 16
            tris.append(vs)
        b += osz
walk(b)
# unshared vertices (position + uv), fan-triangulated polygons
P, T, I = [], [], []
R = max(max(abs(v[0]), abs(v[1])) for v in verts) or 1
for poly in tris:
    base = len(P)//3
    for vi, u, v in poly:
        x, y, z = verts[vi]; P += [round(x/R, 4), round(y/R, 4), round(z/R, 4)]; T += [round(u, 4), round(v, 4)]
    for k in range(1, len(poly) - 1): I += [base, base + k, base + k + 1]
json.dump({'p': P, 't': T, 'i': I}, open(sys.argv[3], 'w'), separators=(',', ':'))
print(len(verts), 'points', len(tris), 'polygons', len(P)//3, 'vertices', len(I)//3, 'triangles, radius', R)
