# F103 stage 2 (v287): frame and outline of every hull, read off her model.
#
# The sprites go (F103, way B). What the game still took from them - the
# box a hull is fitted into and the outline she is hit on - comes from the
# models instead. This writes, per picture key of the game, the side view
# the field draws (same geometry as f3dMat/f3dBuildMask in 59_field3d.js):
#
#   len    width of the hull across the picture, metres (her length from
#          the side; for the F3D_VIEW pictures the turned span, as f3dMat)
#   h      her height, metres (bounding box, centred like the model)
#   d      her depth towards the viewer, metres
#   ratio  h / len - the frame's aspect, replacing IMGS[key].height/width
#   facing which way the bow points in the map ('right' | 'left', from the
#          mount JSON, as spriteFacing() reads it)
#   view   the turn about the vertical (F3D_VIEW), radians, where not 0
#   sprite [W, H] of the old sprite, where there was one (tools/f103/
#          rahmen_v286.csv) - stage 3 needs it to convert the mount offsets
#   map    the outline: w x h cells covering exactly len x h, row 0 at the
#          top; rows[y] is a flat list of runs [x0, x1, x0, x1, ...], x1
#          exclusive. Largest edge MASK_MAX (256) cells, as the game's maps.
#
# The geometry is the field's own: the 'full' level (webmodel.build_level,
# detail 0, moving parts at rest, debris pieces left out), the same
# triangles the game keeps for its hit map (L.cpu).
#
# Usage (MediaVP folders with data/models below each root; several roots
# separated by ':' - MVPS, FSPort, NTF, Blue Planet):
#   python3 mkoutline.py <root[:root...]> <out.json> [key,key,...]
# With keys only those are (re)written, the rest of <out.json> is kept.
import os, sys, re, json, math, csv, struct
import numpy as np
from PIL import Image, ImageDraw
import pof, webmodel
from buildmodels import HULLS

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
MASK_MAX = 256

def js_table(name):
    """A small object literal of 59_field3d.js (F3D_VIEW, F3D_ALIAS), so the
    tool follows the game instead of keeping its own copy."""
    src = open(os.path.join(REPO, 'src', '59_field3d.js'), encoding='utf-8').read()
    m = re.search(r'const ' + name + r' = \{(.*?)\};', src, re.S)
    body = re.sub(r'//[^\n]*', '', m.group(1))
    out = {}
    for k, v in re.findall(r'(\w+)\s*:\s*([^,]+)', body):
        v = v.strip()
        if v.startswith("'"): out[k] = v.strip("'")
        else: out[k] = eval(v.replace('Math.PI', 'math.pi'), {'math': math})
    return out

def find(roots, folder, name):
    """The POF below any root, whatever the case of folder and file names."""
    for root in roots:
        if not os.path.isdir(root): continue
        for f in os.listdir(root):
            if f.lower() != folder.lower(): continue
            md = os.path.join(root, f, 'data', 'models')
            if not os.path.isdir(md): continue
            for g in os.listdir(md):
                if g.lower() == name.lower() + '.pof': return os.path.join(md, g)
    # the NTF texture mod has no MV_ folder: data/models right below its root
    for root in roots:
        md = os.path.join(root, 'data', 'models')
        if folder == 'NTF' and os.path.isdir(md):
            for g in os.listdir(md):
                if g.lower() == name.lower() + '.pof': return os.path.join(md, g)
    return None

def field_mesh(src):
    """Head and triangles (model units, -1..1 of ext) of the field's level."""
    m = pof.read_pof(src)
    data, _ = webmodel.build_level(m, 0, set(), False, True)
    hl = struct.unpack('<I', data[:4])[0]
    head = json.loads(data[4:4 + hl]); blob = data[4 + hl:]
    nodes = head.get('nodes') or []
    tris = []
    for p in head['parts']:
        nd = nodes[p['node']] if p.get('node') and p['node'] < len(nodes) else None
        if nd and nd.get('k') == 'deb': continue
        P = np.frombuffer(blob, '<i2', p['nv'] * 3, p['pos']).reshape(-1, 3).astype(np.float64) / 32767
        I = np.frombuffer(blob, '<u4' if p['big'] else '<u2', p['ni'], p['idx']).astype(np.int64)
        tris.append(P[I.reshape(-1, 3)])
    return head, np.concatenate(tris) if tris else np.zeros((0, 3, 3))

def outline(head, T, sg, vw, rl):
    """Side view as the field draws it: picture x = sin(vw)*x + sg*cos(vw)*z,
    up = y*cos(rl) + x*sin(rl) (f3dMat, f3dBuildMask)."""
    sz, ext = head['size'], head['ext']
    span = sz[2] * abs(math.cos(vw)) + sz[0] * abs(math.sin(vw))
    hy = abs(math.cos(rl)) * sz[1] + abs(math.sin(rl)) * sz[0]
    dep = sz[0] * abs(math.cos(vw)) + sz[2] * abs(math.sin(vw))
    f = MASK_MAX / max(span, hy)
    mw, mh = max(1, round(span * f)), max(1, round(hy * f))
    X = (math.sin(vw) * T[..., 0] + sg * math.cos(vw) * T[..., 2]) * ext
    Y = (T[..., 1] * math.cos(rl) + T[..., 0] * math.sin(rl)) * ext
    px = mw / 2 + X * mw / span
    py = mh / 2 - Y * mh / hy
    im = Image.new('1', (mw, mh), 0)
    dr = ImageDraw.Draw(im)
    for a in np.stack([px, py], -1).tolist():
        dr.polygon([tuple(a[0]), tuple(a[1]), tuple(a[2])], fill=1)
    bits = np.array(im, dtype=np.uint8)
    rows = []
    for r in bits:
        d = np.diff(np.concatenate([[0], r, [0]]))
        s, e = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
        rows.append([int(v) for pair in zip(s, e) for v in pair])
    return span, hy, dep, {'w': mw, 'h': mh, 'rows': rows}, bits

def main():
    roots = sys.argv[1].split(':')
    outp = sys.argv[2]
    only = sys.argv[3].split(',') if len(sys.argv) > 3 else None
    view, alias = js_table('F3D_VIEW'), js_table('F3D_ALIAS')
    mounts = json.load(open(os.path.join(REPO, 'hlp_mounts_final.json'), encoding='utf-8'))
    sprites = {}
    with open(os.path.join(REPO, 'tools', 'f103', 'rahmen_v286.csv'), encoding='utf-8') as fh:
        for r in csv.DictReader(fh): sprites[r['key']] = [int(r['W']), int(r['H'])]
    keys = sorted(set(sprites) | set(HULLS))
    out = json.load(open(outp, encoding='utf-8')) if os.path.exists(outp) else {}
    meshes = {}
    missing = []
    for key in keys:
        if only and key not in only: continue
        mk = alias.get(key, key)
        if mk not in HULLS: missing.append(key + ' (no model)'); continue
        if mk not in meshes:
            src = find(roots, *HULLS[mk])
            meshes[mk] = field_mesh(src) if src else None
        if meshes[mk] is None: missing.append(key); continue
        head, T = meshes[mk]
        ent = mounts.get(key) or mounts.get(mk) or {}
        fc = 'left' if ent.get('facing') == 'left' else 'right'
        vw = view.get(key, 0)
        span, hy, dep, mp, bits = outline(head, T, -1 if fc == 'left' else 1, vw, 0)
        e = {'model': mk, 'facing': fc, 'len': round(span, 2), 'h': round(hy, 2), 'd': round(dep, 2),
             'ratio': round(hy / span, 4)}
        if vw: e['view'] = round(vw, 4)
        if key in sprites: e['sprite'] = sprites[key]
        e['map'] = mp
        out[key] = e
        print(key, mk, fc, e['len'], e['h'], 'map %dx%d fill %.2f' % (mp['w'], mp['h'], bits.mean()), flush=True)
    out = {k: out[k] for k in sorted(out)}
    with open(outp, 'w', encoding='utf-8') as fh:
        fh.write('{\n' + ',\n'.join(json.dumps(k) + ': ' + json.dumps(v, separators=(',', ':')) for k, v in out.items()) + '\n}\n')
    if missing: print('not found:', ', '.join(missing))

if __name__ == '__main__':
    main()
