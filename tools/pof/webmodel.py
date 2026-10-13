# Convert a MediaVP POF model into the compact web format the game's 3D
# viewer reads (v191). Per model folder:
#   lo.bin / hi.bin   one detail level each: a JSON header, then int16
#                     positions, int8 normals, uint16 UVs, indices
#   c512 / c1024.webp colour, n512 / n1024.webp normal (x in R, y in G),
#   g512 / g1024.webp glow (only when the skin has one)
# The model is baked into one rigid mesh per texture: every submodel of the
# chosen detail level is moved by its chain of offsets. FreeSpace is
# left-handed; x is mirrored here and the winding reversed, so WebGL gets a
# right-handed model with +z forward (the bow) and +y up.
import json, struct, sys, os, io, re
import pof
from PIL import Image

LO_MIN_TRIS = 3000          # the low level is the smallest one with this many
SKIP = ('invisible', 'damage', 'newdamage', 'debris', 'thruster', 'nameplate')
HI_MAX_TRIS = 60000         # a finer level than this is too heavy for the web

def chain_offset(subs, k):
    x = y = z = 0.0
    while k >= 0:
        o = subs[k]['offset']; x += o[0]; y += o[1]; z += o[2]
        k = subs[k]['parent']
    return (x, y, z)

def subtree(subs, root):
    out = [root]
    for j, s in enumerate(subs):
        if s['parent'] == root: out += subtree(subs, j)
    return out

def tri_count(subs, root):
    return sum(len(subs[k]['tris']) for k in subtree(subs, root))

def kind_of(name):
    n = name.lower()
    if any(n.startswith(s) or n == s for s in SKIP) or n.endswith('-debris') or 'dead' in n: return 'skip'
    if 'glass' in n or n.endswith('-trans'): return 'glass'
    if 'ckpt' in n or 'cockpit' in n or 'tercoc' in n or 'pilot' in n: return 'flat'
    return 'tex'

# v195: FreeSpace keeps turrets, engines, radar dishes and other moving or
# destroyable parts on detail0 only and draws them at every distance; the
# coarser levels hold the hull alone. Those parts are taken from detail0
# for every level. Detail boxes, greebles and 'bits' (Aten) are close-up
# dressing and stay with detail0. A level's own simple turret base (Orion: Turret01b) gives
# way to detail0's full one (Turret01a with its arm).
D0_ONLY = ('detailbox', 'detail_box', 'deyailbox', 'greeb', 'bits', 'nameplate')
SUBSYS_RE = r'(turret|engine|radar|comm|navigation|sensor|weapon|reactor|fighterbay|bridge)'
def _norm(name):
    n = name.lower()
    return re.sub(r'(\d+)[ab]$', r'\1', n)
def level_subs(m, i, d0parts=True):
    subs = m['subs']; det = m['details']
    own = subtree(subs, det[i])
    if i == 0 or not d0parts: return own
    extra = []
    for j, s in enumerate(subs):
        if s['parent'] != det[0]: continue
        n = s['name'].lower()
        if any(t in n for t in D0_ONLY) or n.endswith('-destroyed'): continue
        # 'subsys' (v197, Shivan hulls): only the parts FreeSpace treats as
        # subsystems; their other detail0 dressing (bones, spires, arms) is
        # often merged into the coarse levels already and would double up
        if d0parts == 'subsys' and not re.match(SUBSYS_RE, n): continue
        extra += subtree(subs, j)
    have = {_norm(subs[j]['name']) for j in extra}
    own = [k for k in own if k == det[i] or _norm(subs[k]['name']) not in have]
    return own + extra

# v201: moving parts. Turret bases, turret barrels and parts that spin on
# their own ($rotate) keep their own node: their triangles go into parts of
# their own, drawn with a turn about the node's pivot. Node 0 is the hull.
# Each node: k (base|gun|rot), ti (turret index in TGUN), par (parent node),
# pv (pivot, same space as the positions), ax (axis), t (seconds per turn).
AXIS = {0: (1, 0, 0), 1: (0, 0, 1), 2: (0, 1, 0)}
def find_nodes(m):
    subs = m['subs']; nodes = [None]; of = {}
    def add(k, nd):
        of[k] = len(nodes); nodes.append(nd)
    for ti, t in enumerate(m.get('turrets', [])):
        if t['sub'] in of: continue
        n = t['normal']
        add(t['sub'], {'k': 'base', 'ti': ti, 'sub': t['sub'], 'ax': (-n[0], n[1], n[2])})
        if t['phys'] != t['sub'] and t['phys'] not in of:
            add(t['phys'], {'k': 'gun', 'ti': ti, 'sub': t['phys'], 'ax': (-n[0], n[1], n[2])})
    for k, sm in enumerate(subs):
        if k in of: continue
        mm = re.search(r'\$rotate(?:_time)?\s*[=:]\s*(-?[\d.]+)', sm['props'])
        if not mm: continue
        t = float(mm.group(1))
        if abs(t) < 0.01: continue
        uv = re.search(r'\$uvec\s*[:=]\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)', sm['props'])
        if uv: a = tuple(float(x) for x in uv.groups())
        else: a = AXIS.get(sm.get('rot_axis'), (0, 1, 0))
        add(k, {'k': 'rot', 'ti': -1, 'sub': k, 'ax': (-a[0], a[1], a[2]), 't': t})
    # parents: the nearest node above in the submodel tree
    for nd in nodes[1:]:
        p = subs[nd['sub']]['parent']; nd['par'] = 0
        while p >= 0:
            if p in of: nd['par'] = of[p]; break
            p = subs[p]['parent']
    return nodes, of
def node_of(subs, of, k):
    while k >= 0:
        if k in of: return of[k]
        k = subs[k]['parent']
    return 0

def build_level(m, i, skin, d0parts=False, moving=False):
    subs = m['subs']; tex = m['textures']
    groups = {}                      # (node, tmap) -> (P, N, T, I, key)
    nodes, of = find_nodes(m) if moving else ([None], {})
    lo = [1e9] * 3; hi = [-1e9] * 3
    # v202: the debris pieces of the model (HDR2 debris list) go into the
    # full level as nodes of their own (k 'deb'). The field does not draw
    # them; a ship that breaks up flies them apart. They do not count for
    # the model's size.
    deb = []
    if moving and i == 0:
        for k in m.get('debris', []):
            if 0 <= k < len(subs) and subs[k]['tris'] and k not in of:
                of[k] = len(nodes); nodes.append({'k': 'deb', 'ti': -1, 'sub': k, 'ax': (0, 1, 0), 'par': 0})
                deb.append(k)
    for k in list(level_subs(m, i, d0parts)) + deb:
        sm = subs[k]
        isdeb = k in deb
        if not isdeb and (sm['name'].lower().endswith('-destroyed') or not sm['tris']): continue
        ox, oy, oz = chain_offset(subs, k)
        nd = node_of(subs, of, k) if moving else 0
        for tmap, vs in sm['tris']:
            kind = kind_of(tex[tmap]) if tmap < len(tex) else 'skip'
            # a debris piece carries her 'dead' and debris maps and the
            # generic damage maps: drawn, not skipped (still not what is
            # meant to be invisible)
            if kind == 'skip' and isdeb and tmap < len(tex) and not re.match(r'(invisible|thruster|nameplate)', tex[tmap].lower()):
                kind = 'tex'
            if kind == 'skip': continue
            g = groups.setdefault((nd, tmap), ([], [], [], [], {}))
            P, N, T, I, key = g
            idx = []
            for (vi, ni, u, v) in vs:
                kk = (k, vi, ni, round(u, 5), round(v, 5))
                if kk not in key:
                    key[kk] = len(P)
                    p = sm['verts'][vi]; n = sm['norms'][ni] if ni < len(sm['norms']) else (0, 1, 0)
                    q = (-(p[0] + ox), p[1] + oy, p[2] + oz)
                    if not isdeb:
                        for a in range(3): lo[a] = min(lo[a], q[a]); hi[a] = max(hi[a], q[a])
                    else:
                        dc = nodes[nd].setdefault('dlo', [1e9] * 3), nodes[nd].setdefault('dhi', [-1e9] * 3)
                        for a in range(3): dc[0][a] = min(dc[0][a], q[a]); dc[1][a] = max(dc[1][a], q[a])
                    P.append(q); N.append((-n[0], n[1], n[2])); T.append((u, v))
                idx.append(key[kk])
            for j in range(1, len(idx) - 1):
                I += [idx[0], idx[j + 1], idx[j]]
    centre = [(lo[a] + hi[a]) / 2 for a in range(3)]
    ext = max((hi[a] - lo[a]) / 2 for a in range(3)) * 1.001 or 1
    blob = bytearray(); parts = []
    for (nd, tmap), (P, N, T, I, key) in sorted(groups.items()):
        if not I: continue
        big = len(P) > 65535
        def al(): blob.extend(b'\0' * (-len(blob) % 4))
        op = len(blob)
        for p in P: blob.extend(struct.pack('<3h', *[max(-32767, min(32767, int(round((p[a] - centre[a]) / ext * 32767)))) for a in range(3)]))
        al(); on = len(blob)
        for n in N:
            l = (n[0] ** 2 + n[1] ** 2 + n[2] ** 2) ** 0.5 or 1
            q8 = [max(-127, min(127, int(round(c / l * 127)))) for c in n]
            blob.extend(struct.pack('<4b', q8[0], q8[1], q8[2], 0))
        al(); ou = len(blob)
        for (u, v) in T:
            blob.extend(struct.pack('<2H', max(0, min(65535, int(round(u * 16384 + 16384)))),
                                            max(0, min(65535, int(round(v * 16384 + 16384))))))
        al(); oi = len(blob)
        blob.extend(struct.pack('<%d%s' % (len(I), 'I' if big else 'H'), *I))
        al()
        name = m['textures'][tmap]
        kd = kind_of(name)
        if kd == 'skip': kd = 'tex'                  # debris faces (v202), see above
        parts.append({'tex': name, 'kind': kd if name.lower() in skin else ('flat' if kd == 'tex' else kd),
                      'nv': len(P), 'ni': len(I), 'big': big, 'pos': op, 'nrm': on, 'uv': ou, 'idx': oi})
        if nd: parts[-1]['node'] = nd
    head = {'v': 1, 'centre': centre, 'ext': ext, 'size': [hi[a] - lo[a] for a in range(3)], 'parts': parts}
    if moving:
        used = {p.get('node', 0) for p in parts}
        # a node with no triangles of its own still carries its children
        for nd in list(used):
            while nd and nodes[nd]['par']: nd = nodes[nd]['par']; used.add(nd)
        out = []
        for j, nd in enumerate(nodes):
            if j == 0: out.append(None); continue
            o = chain_offset(subs, nd['sub'])
            q = (-o[0], o[1], o[2])
            # a debris piece turns about its own middle; r: its half size
            if nd['k'] == 'deb' and 'dlo' in nd:
                q = tuple((nd['dlo'][a] + nd['dhi'][a]) / 2 for a in range(3))
            pv = [round((q[a] - centre[a]) / ext, 5) for a in range(3)]
            l = sum(c * c for c in nd['ax']) ** 0.5 or 1
            e = {'k': nd['k'], 'ti': nd['ti'], 'par': nd['par'], 'pv': pv,
                 'ax': [round(c / l, 4) for c in nd['ax']]}
            if 't' in nd: e['t'] = nd['t']
            if nd['k'] == 'deb' and 'dlo' in nd:
                e['r'] = round(max(nd['dhi'][a] - nd['dlo'][a] for a in range(3)) / 2 / ext, 4)
            # which way the part points at rest: from the pivot to the middle
            # of its own triangles, across the axis (barrels, v201)
            if nd['k'] in ('gun', 'base'):
                acc = [0.0, 0.0, 0.0]; cnt = 0
                for kk in subtree(subs, nd['sub']):
                    if node_of(subs, of, kk) != j: continue
                    oo = chain_offset(subs, kk)
                    for v in subs[kk]['verts']:
                        w = (-(v[0] + oo[0]) - q[0], v[1] + oo[1] - q[1], v[2] + oo[2] - q[2])
                        for a in range(3): acc[a] += w[a]
                        cnt += 1
                if cnt:
                    ax = e['ax']; dv = [acc[a] / cnt for a in range(3)]
                    dn = sum(dv[a] * ax[a] for a in range(3))
                    pl = [dv[a] - dn * ax[a] for a in range(3)]
                    lp = sum(c * c for c in pl) ** 0.5
                    if lp > 1e-6 * ext: e['fw'] = [round(c / lp, 4) for c in pl]
            if j not in used: e['empty'] = 1
            out.append(e)
        head['nodes'] = out
    hj = json.dumps(head, separators=(',', ':')).encode()
    hj += b' ' * (-len(hj) % 4)
    return struct.pack('<I', len(hj)) + hj + bytes(blob), sum(p['ni'] for p in parts) // 3

def texture(path, size, mode):
    im = Image.open(path); im.load(); im = im.convert('RGBA')
    if im.size[0] > size: im = im.resize((size, size), Image.LANCZOS)
    if mode == 'normal':
        r, g, b, a = im.split()
        # MediaVP normal maps keep x in alpha when alpha carries data
        ax = a.getextrema()
        x = a if ax[1] - ax[0] > 32 else r
        im = Image.merge('RGB', (x, g, Image.new('L', im.size, 0)))
        q = 88
    elif mode == 'glow':
        im = im.convert('RGB'); q = 80
    else:
        im = im.convert('RGB'); q = 82
    buf = io.BytesIO(); im.save(buf, 'WEBP', quality=q, method=6)
    return buf.getvalue()

def convert(src, skinfiles, outdir, d0parts=False, moving=False):
    # d0parts: capital ships (v195), see level_subs
    """skinfiles: {texname_lower: {'c': path, 'n': path|None, 'g': path|None}}"""
    m = pof.read_pof(src)
    det = m['details']; subs = m['subs']
    counts = [tri_count(subs, d) for d in det]
    skinl = set(skinfiles)
    def textured(root):
        # share of a level's triangles that carry the skin; some models map
        # their coarse levels to another texture (Sekhmet: the pilot)
        n = t = 0
        for k in subtree(subs, root):
            for tmap, vs in subs[k]['tris']:
                n += 1
                if tmap < len(m['textures']) and m['textures'][tmap].lower() in skinl: t += 1
        return t / max(1, n)
    lo_i = 0
    for i in range(len(det) - 1, -1, -1):
        if counts[i] >= LO_MIN_TRIS and textured(det[i]) >= 0.6: lo_i = i; break
    os.makedirs(outdir, exist_ok=True)
    skin = set(skinfiles)
    info = {'lod': {}}
    hi_i = 0
    while hi_i < lo_i and counts[hi_i] > HI_MAX_TRIS: hi_i += 1
    for tag, i in (('lo', lo_i), ('hi', hi_i)):
        data, nt = build_level(m, i, skin, d0parts, moving)
        open(os.path.join(outdir, tag + '.bin'), 'wb').write(data)
        info['lod'][tag] = {'detail': i, 'tris': nt, 'bytes': len(data)}
    texs = {}
    for name, f in skinfiles.items():
        for size in (512, 1024):
            for k, mode in (('c', 'color'), ('n', 'normal'), ('g', 'glow')):
                if not f.get(k): continue
                fn = '%s_%s%d.webp' % (name, k, size)
                open(os.path.join(outdir, fn), 'wb').write(texture(f[k], size, mode))
                texs.setdefault(name, set()).add(k)
    info['tex'] = {k: sorted(v) for k, v in texs.items()}
    return info

if __name__ == '__main__':
    print(json.dumps(convert(sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]), indent=1))
