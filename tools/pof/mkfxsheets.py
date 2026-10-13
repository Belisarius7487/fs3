# v216: the MediaVP 5.0.2 explosion animations (MV_Effects_1/data/effects)
# as sprite sheets for the game: Exp05 (secondaries, fighters), Exp20 (the
# big blast), ParticleSmoke01 (smoke), MissileTrail01 (missile trails).
# Fire frames are premultiplied onto black (drawn additively, 'lighter');
# smoke and trail keep their alpha.
# usage: python3 -I mkfxsheets.py <effects dir> <out dir>
import sys, os, glob, json
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
files = {os.path.basename(p).lower(): p for p in glob.glob(SRC + '/*') if p.lower().endswith('.dds')}

def frame(pre, i):
    return Image.open(files['%s_%04d.dds' % (pre, i)]).convert('RGBA')

def sheet(pre, n, step, cell, cols, name, additive):
    idx = list(range(0, n, step)); rows = (len(idx) + cols - 1)//cols
    sh = Image.new('RGBA', (cols*cell, rows*cell), (0, 0, 0, 0 if not additive else 255))
    for k, i in enumerate(idx):
        im = frame(pre, i).resize((cell, cell), Image.LANCZOS)
        if additive:
            r, g, b, a = im.split()
            black = Image.new('RGBA', im.size, (0, 0, 0, 255))
            im = Image.composite(Image.merge('RGBA', (r, g, b, Image.new('L', im.size, 255))), black, a)
        sh.paste(im, ((k % cols)*cell, (k//cols)*cell))
    if additive: sh = sh.convert('RGB')
    sh.save(OUT + '/' + name + '.webp', quality=86, method=6)
    return {'n': len(idx), 'cols': cols, 'cell': cell, 'fps': 20.0/step}

meta = {
    'exp05': sheet('exp05', 93, 2, 128, 8, 'fx_exp05', True),
    'exp20': sheet('exp20', 75, 2, 128, 8, 'fx_exp20', True),
    'smoke': sheet('particlesmoke01', 54, 3, 128, 6, 'fx_smoke', False),
}
Image.open(files['missiletrail01.dds']).convert('RGBA').save(OUT + '/fx_trail.webp', quality=90, method=6)
print(json.dumps(meta))
for f in sorted(os.listdir(OUT)): print(f, os.path.getsize(OUT + '/' + f))
