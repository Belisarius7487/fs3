# F99 (v283): export the dock points of the models into the mount data, as
# FreeSpace has them: name, position (also in depth), the way the dock
# faces, the approach path - and, from the real hull shapes, how far a
# docking partner must stand off before it slides in, and how large a
# container may be, and where it touches, without going through the hull.
#
# Decided by Silvio (24.10.2026): docking is never solved per mission. It
# runs for every mission on these data.
#
# Coordinates (the game's side view, same frame the 3D field draws in):
#   x  along her length, + towards the bow as the sprite faces
#      (mounts 'facing' left flips it, like the bay paths in mkbays.py)
#   y  up/down, + is down on the screen
#   d  across her beam, + towards the viewer
# Everything is a share of HALF THE MODEL'S LENGTH (detail0 bounding box,
# the same box the web model is centred and scaled on, webmodel.py). In the
# game half the length is img.width*sc/2, so one factor serves x, y and d
# - the model is drawn with one scale, not stretched to the sprite.
#
# Per dock (list 'docks' of a hull, replacing the hand-placed dx/dy/ang):
#   n      name ('cargo dock', 'topside dock', ...)
#   p      [x, y, d]   middle of the dock's two points
#   v      [x, y, d]   unit vector the dock faces (out of the hull)
#   path   [[x, y, d], ...]  approach path from outside to the dock
#   clear  how far the hull reaches out beyond the dock's plane in the
#          way the dock faces: a partner coming in must hold at least
#          this far off before it slides in
#   hm     height map of the hull around the dock (height_map below): how
#          far the hull reaches out, cell by cell. From it the game takes
#          where a partner touches (a container between the Poseidon's arms,
#          on the Bast's deck) and how far off it must hold before it
#          slides in (the Chronos' end blocks, the Poseidon's arms)
# Per hull also 'm3d': {'len': model length in metres, 'size': [l, h, w]}.
#
# Usage: python3 -I mkdocks.py <MVPS root> <hlp_mounts_final.json> [keys]
import json, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # run with -I
import numpy as np
import pof, webmodel, mkbays
from buildmodels import HULLS

# A dock is a cargo dock by its name, as FreeSpace models name them.
def is_cargo(name):
    return 'cargo' in name.lower()

def find(root, folder, name):
    """The POF, whatever the case of the folder and file names."""
    for f in os.listdir(root):
        if f.lower() != folder.lower(): continue
        md = os.path.join(root, f, 'data', 'models')
        if not os.path.isdir(md): continue
        for g in os.listdir(md):
            if g.lower() == name.lower() + '.pof': return os.path.join(md, g)
    return None

def hull_points(m, step=0.6):
    """Points on every drawn triangle of detail0, at most step metres
    apart, in the web model's frame (x mirrored as webmodel.build_level
    does). Also the drawn bounding box."""
    subs, tex = m['subs'], m['textures']
    tris = []
    for k in webmodel.level_subs(m, 0, False):
        sm = subs[k]
        if sm['name'].lower().endswith('-destroyed') or not sm['tris']: continue
        ox, oy, oz = webmodel.chain_offset(subs, k)
        for tmap, vs in sm['tris']:
            kind = webmodel.kind_of(tex[tmap]) if tmap < len(tex) else 'skip'
            if kind == 'skip': continue
            q = [(-(sm['verts'][vi][0] + ox), sm['verts'][vi][1] + oy, sm['verts'][vi][2] + oz) for vi, _n, _u, _v in vs]
            for j in range(1, len(q) - 1):
                tris.append((q[0], q[j], q[j + 1]))
    T = np.array(tris, dtype=np.float64)                 # (n, 3, 3)
    lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    pts = [T.reshape(-1, 3)]
    # fill each triangle with a barycentric grid fine enough for 'step'
    e = np.maximum(np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 0], axis=1))
    nseg = np.clip(np.ceil(e / step).astype(int), 1, 60)
    for ns in np.unique(nseg):
        sel = T[nseg == ns]
        ab = [(a / ns, b / ns) for a in range(ns + 1) for b in range(ns + 1 - a)]
        A = np.array(ab)
        P = sel[:, None, 0] + A[None, :, 0, None]*(sel[:, None, 1] - sel[:, None, 0]) + A[None, :, 1, None]*(sel[:, None, 2] - sel[:, None, 0])
        pts.append(P.reshape(-1, 3))
    return np.concatenate(pts), lo, hi

def dock_frame(dk, P=None):
    """Middle, outward normal and the axis along the two dock points
    (POF frame, x mirrored like the web model). With the hull points P the
    middle is moved out along the normal onto the hull's surface if the
    model has it inside the hull (the Bast's cargo dock lies 8 m under her
    deck): a partner can only touch her where her skin is."""
    (a, na), (b, nb) = dk['points'][0], dk['points'][1]
    mir = lambda v: np.array([-v[0], v[1], v[2]], dtype=np.float64)
    a, b, n = mir(a), mir(b), mir(na)
    p = (a + b) / 2
    n = n / (np.linalg.norm(n) or 1)
    ax = a - b
    ax = ax - n*np.dot(ax, n)
    ax = ax / (np.linalg.norm(ax) or 1)
    if P is not None:
        ua, un, us = local(P, p, n, ax)
        near = (np.abs(ua) < SURF_R) & (np.abs(us) < SURF_R) & (un > 0)
        if near.any(): p = p + n*float(un[near].max())
    return p, n, ax
# how close around the dock point the hull counts as 'the surface it sits on'
SURF_R = 1.5

def local(P, p, n, ax):
    """Hull points in the dock's frame: along the dock axis, out along the
    normal, and across."""
    side = np.cross(n, ax)
    R = P - p
    return R @ ax, R @ n, R @ side

def clearance(P, dk):
    """How far the hull reaches out beyond the dock plane (metres)."""
    p, n, ax = dock_frame(dk, P)
    _ua, un, _us = local(P, p, n, ax)
    return float(max(0.0, un.max()))

# cells per half length of the hull in a height map
HM_CELLS = 24

def height_map(P, p, n, half, sg):
    """The hull's surface around a dock, as seen from the dock: for each
    cell of a grid laid across the dock's plane, how far the hull reaches
    out (along the way the dock faces) - metres beyond the plane are +,
    a surface that falls away behind the plane is -, a cell with no hull
    is None. Two hulls docked face to face touch nowhere if, cell by cell,
    their two heights add up to no more than the gap between their dock
    points; the game takes the gap from these maps (docks.js).
    Grid axes: u in the picture's plane across the normal, w across her
    beam (depth); row by row (w), u within a row. Heights in shares of her
    half length times 1000."""
    D = np.array([1.0, 0.0, 0.0]); D = D - n*np.dot(D, n)
    if np.linalg.norm(D) < 1e-6: D = np.array([0.0, 0.0, 1.0]) - n*n[2]
    D = D / np.linalg.norm(D)
    U = np.cross(n, D); U = U / np.linalg.norm(U)
    ux, uy = sg*U[2], -U[1]
    if ux < -1e-6 or (abs(ux) <= 1e-6 and uy < 0): U = -U; ux, uy = -ux, -uy
    R = P - p
    u, w, h = R @ U, R @ D, R @ n
    c = half / HM_CELLS
    iu = np.floor(u / c + 0.5).astype(int); iw = np.floor(w / c + 0.5).astype(int)
    u0, w0 = int(iu.min()), int(iw.min())
    nu, nw = int(iu.max()) - u0 + 1, int(iw.max()) - w0 + 1
    g = np.full(nu*nw, -np.inf)
    np.maximum.at(g, (iw - w0)*nu + (iu - u0), h)
    # one string, cells comma separated, empty for no hull: keeps the mount
    # file readable (a list would put every number on a line of its own)
    out = ','.join('' if not np.isfinite(v) else str(int(round(v / half * 1000))) for v in g)
    return {'c': round(1.0 / HM_CELLS, 6), 'u0': u0, 'w0': w0, 'nu': nu, 'nw': nw,
            'uv': [round(float(ux), 4), round(float(uy), 4)], 'wd': round(float(D[0]), 4), 'g': out}

def main():
    root, mpath = sys.argv[1], sys.argv[2]
    only = sys.argv[3].split(',') if len(sys.argv) > 3 else None
    mounts = json.load(open(mpath, encoding='utf-8'))
    models = {}
    for key, (folder, name) in HULLS.items():
        if only and key not in only: continue
        src = find(root, folder, name)
        if not src: continue
        m = pof.read_pof(src)
        if not m['docks']: continue
        P, lo, hi = hull_points(m)
        # pof.read_pof does not keep the PATH chunk; mkbays reads it
        models[key] = (m, P, lo, hi, mkbays.read_paths(src)[1])
    for key, (m, P, lo, hi, pl) in models.items():
        ent = mounts.setdefault(key, {})
        sg = -1 if ent.get('facing') == 'left' else 1
        c = (lo + hi) / 2
        half = (hi[2] - lo[2]) / 2
        # model frame -> side view: x along length (z), y down (-y), d towards
        # the viewer (x, as the bay paths count it)
        tov = lambda v: [round(float(sg*(v[2] - c[2]) / half), 4), round(float(-(v[1] - c[1]) / half), 4),
                         round(float((v[0] - c[0]) / half), 4)]
        tod = lambda v: [round(float(sg*v[2]), 4), round(float(-v[1]), 4), round(float(v[0]), 4)]
        # replaces what was there: the old entries (dx, dy, ang) were placed by
        # hand on the sprites and are not the models' (the Aten's dock was on
        # her top, FreeSpace has it under her keel)
        out = []
        for i, dk in enumerate(m['docks']):
            name = dk['props'].split('$name=')[-1].strip().split('\n')[0] if '$name=' in dk['props'] else ''
            p, n, ax = dock_frame(dk, P)
            d = {'n': name}
            d['p'] = tov(p)
            d['v'] = tod(n)
            path = []
            for pi in dk['paths']:
                if 0 <= pi < len(pl):
                    path = [tov(np.array([-x, y, z])) for x, y, z in pl[pi][1]]
                    break
            d['path'] = path
            d['clear'] = round(clearance(P, dk) / half, 4)
            d['hm'] = height_map(P, p, n, half, sg)
            out.append(d)
        ent['docks'] = out
        ent['m3d'] = {'len': round(float(hi[2] - lo[2]), 2),
                      'size': [round(float(hi[2] - lo[2]), 2), round(float(hi[1] - lo[1]), 2), round(float(hi[0] - lo[0]), 2)]}
        print(key, [(o['n'], o['p'], o['v'], o['clear'], (o['hm']['nu'], o['hm']['nw'])) for o in out])
    with open(mpath, 'w', encoding='utf-8') as fh:
        json.dump(mounts, fh, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()
