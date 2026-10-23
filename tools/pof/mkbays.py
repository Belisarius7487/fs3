# F89 (v269): export the fighter bay approach paths ($bayNN, POF chunk PATH)
# of every destroyer into the mount data, as the game's side view sees them.
#
# Each path is a list of points from outside the ship to inside the bay, in
# the order FreeSpace flies them on arrival. A point is [dx, dy, depth]:
#   dx     along her length, -1 stern .. +1 bow, as the sprite faces
#          (mounts 'facing' left flips it)
#   dy     up/down, -1 top .. +1 bottom (screen down is +)
#   depth  across her beam, toward the viewer is + (kept for the last step:
#          a bay in her side is entered by going "into" the picture)
# All three are shares of the half extent of the model's bounding box, the
# same normalisation the dock and thruster points use.
#
# Usage: python3 -I mkbays.py <MVPS root> <hlp_mounts_final.json>
import json, os, struct, sys

# game key -> (MediaVP folder, POF name); same pairs as buildmodels.py HULLS
DESTROYERS = {
    'deorionright': ('mv_assets_t_2', 'Orion_FS2'),
    'deorionleft':  ('mv_assets_t_2', 'Orion_FS2'),
    'dehecate':     ('mv_assets_t_2', 'Hecate'),
    'detyphon':     ('mv_assets_v',   'Typhon'),
    'dehatshepsut': ('mv_assets_v',   'Capital2V-01'),
    'dedemon':      ('mv_assets_s',   'Demon'),
    'deravana':     ('mv_assets_s',   'Ravana'),
}

def _str(d, p):
    n = struct.unpack_from('<i', d, p)[0]
    return d[p+4:p+4+n].split(b'\0')[0].decode('latin1'), p + 4 + n

def read_paths(path):
    """Bounding box and named paths of a POF; nothing else is parsed."""
    d = open(path, 'rb').read()
    assert d[:4] == b'PSPO'
    p, bbox, paths = 8, None, []
    while p + 8 <= len(d):
        cid = d[p:p+4]; ln = struct.unpack_from('<i', d, p+4)[0]; q = p + 8
        if cid == b'HDR2':
            q += 12        # radius, object flags, number of submodels
            bbox = [struct.unpack_from('<3f', d, q), struct.unpack_from('<3f', d, q+12)]
        elif cid == b'PATH':
            n = struct.unpack_from('<i', d, q)[0]; q += 4
            for _ in range(n):
                name, q = _str(d, q); _parent, q = _str(d, q)
                nv = struct.unpack_from('<i', d, q)[0]; q += 4
                pts = []
                for _ in range(nv):
                    x, y, z, _r = struct.unpack_from('<4f', d, q); q += 16
                    nt = struct.unpack_from('<i', d, q)[0]; q += 4 + 4*nt
                    pts.append((x, y, z))
                paths.append((name.strip(), pts))
        p += 8 + ln
    return bbox, paths

def find(root, folder, name):
    """The POF, whatever the case of the folder and file names."""
    for f in os.listdir(root):
        if f.lower() != folder.lower(): continue
        md = os.path.join(root, f, 'data', 'models')
        for g in os.listdir(md):
            if g.lower() == name.lower() + '.pof': return os.path.join(md, g)
    return None

def main():
    root, mounts_path = sys.argv[1], sys.argv[2]
    mounts = json.load(open(mounts_path, encoding='utf-8'))
    for key, (folder, name) in DESTROYERS.items():
        src = find(root, folder, name)
        if not src or key not in mounts:
            print(key, 'skipped (no POF or no mount entry)'); continue
        (x0, y0, z0), (x1, y1, z1) = read_paths(src)[0]
        cx, cy, cz = (x0+x1)/2, (y0+y1)/2, (z0+z1)/2
        hx, hy, hz = (x1-x0)/2, (y1-y0)/2, (z1-z0)/2
        sg = -1 if mounts[key].get('facing') == 'left' else 1
        bays = []
        for pname, pts in sorted(read_paths(src)[1]):
            if not pname.lower().startswith('$bay') or len(pts) < 2: continue
            bays.append([[round(sg*(z-cz)/hz, 3), round(-(y-cy)/hy, 3), round((x-cx)/hx, 3)]
                         for x, y, z in pts])
        mounts[key]['bays'] = bays
        print(key, len(bays), 'bay paths')
    with open(mounts_path, 'w', encoding='utf-8') as fh:
        json.dump(mounts, fh, indent=2, ensure_ascii=False)   # the file's own layout

if __name__ == '__main__':
    main()
