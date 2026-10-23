# v275: a side-view sprite (bow to the right, top up) rendered from a POF,
# for a hull that has no drawn sprite - the Phidias repair drone. The game
# keeps the hit mask and the fallback picture (&f3d=0) from the sprite; the
# field shows the 3D model. Flat shading, colour from the diffuse map at
# each triangle's centre, painter's order along the depth axis.
#   python3 mksprite.py <file.pof> <diffuse map> <out.png> [width]
import sys, math
from PIL import Image, ImageDraw
import pof

def main():
    src, tex, out = sys.argv[1], sys.argv[2], sys.argv[3]
    W = int(sys.argv[4]) if len(sys.argv) > 4 else 512
    m = pof.read_pof(src)
    T = Image.open(tex).convert('RGB'); TW, TH = T.size
    subs = {s['num']: s for s in m['subs']}
    def off(n):                     # a submodel's place in the whole model
        x = y = z = 0.0
        while n != -1:
            s = subs[n]; x += s['offset'][0]; y += s['offset'][1]; z += s['offset'][2]; n = s['parent']
        return x, y, z
    keep = set()
    def walk(n):
        keep.add(n)
        for s in m['subs']:
            if s['parent'] == n and not s['name'].lower().startswith(('turret', 'thruster')): walk(s['num'])
    walk(m['details'][0])
    tris = []
    for n in keep:
        s = subs[n]; ox, oy, oz = off(n)
        V = s['verts']
        for tmap, vs in s['tris']:
            P = [(V[v[0]][0]+ox, V[v[0]][1]+oy, V[v[0]][2]+oz) for v in vs]
            u = sum(v[2] for v in vs)/len(vs); w = sum(v[3] for v in vs)/len(vs)
            for k in range(1, len(P)-1): tris.append((P[0], P[k], P[k+1], u, w))
    zs = [p[2] for t in tris for p in t[:3]]; ys = [p[1] for t in tris for p in t[:3]]
    z0, z1, y0, y1 = min(zs), max(zs), min(ys), max(ys)
    k = (W-8)/(z1-z0); H = int((y1-y0)*k)+8
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    L = (0.35, 0.75, 0.0); Ln = math.sqrt(sum(c*c for c in L)); L = [c/Ln for c in L]
    # seen from the side: depth is x; far side first
    tris.sort(key=lambda t: -(t[0][0]+t[1][0]+t[2][0]))
    for a, b, c, u, w in tris:
        ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]; vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
        nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx; nl = math.sqrt(nx*nx+ny*ny+nz*nz) or 1
        lam = 0.35 + 0.65*abs((nx*L[0]+ny*L[1]+nz*L[2])/nl)
        col = T.getpixel((int((u % 1)*(TW-1)), int((w % 1)*(TH-1))))
        f = tuple(int(min(255, ch*lam)) for ch in col) + (255,)
        pts = [((p[2]-z0)*k+4, (y1-p[1])*k+4) for p in (a, b, c)]
        d.polygon(pts, fill=f)
    img.save(out)
    print(out, img.size)

if __name__ == '__main__':
    main()
