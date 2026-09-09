#!/usr/bin/env python3
"""
HLP Space Shooter - Asset Packer
=================================

Baut die Spieldatei neu auf:
  - liest alle Sprites aus dem Sprite-Ordner und ersetzt SPR_DATA
  - liest HUD-Icons aus dem Icon-Ordner und ersetzt ICON_DATA
  - liest Planeten und Sonnen und ersetzt PLANET_DATA und SUN_DATA
  - haengt die Mount-Definitionen als MOUNTS an
  - meldet jeden Key, der im Spielcode vorkommt aber kein Sprite mehr hat

Aufruf:
    python3 build_game.py --sprites ./sprites --mounts hlp_mounts_final.json \
                          --game hlp_shooter_v3.html --out hlp_shooter_v4.html

Kurzform, wenn alles im selben Ordner liegt und Standardnamen hat:
    python3 build_game.py

Neu gegenueber der Fassung von v68:
  - Die Fraktion war bisher reine Deko im Dateinamen. te-cr-aeolus.png und
    ntf-cr-aeolus.png ergaben beide den Key 'craeolus', die zweite Datei
    waere kommentarlos verworfen worden und die NTF-Lackierung waere auf
    beiden Seiten aufgetaucht. NTF-Dateien bekommen jetzt ein Praefix,
    aber nur dann, wenn es zu demselben Rumpf eine te-Datei gibt.
    ntf-bo-zeus, ntf-fi-loki, ntf-co-iceni und ntf-sd-hades behalten damit
    ihre bisherigen Keys, weil es keine terranischen Gegenstuecke gibt.
  - Planeten und Sonnen. DDS wird gelesen, auf BODY_PX gebracht und
    eingebettet. Planeten, deren Alphakanal eine Kreisscheibe ist, gehen
    als JPEG rein und das Spiel rechnet die Maske; das spart rund 90 %.
    Alles andere, etwa der Ringplanet und die Sonnen mit ihrer weichen
    Korona, bleibt PNG.
  - Uebergrosse Sprites werden auf SPRITE_PX heruntergerechnet. Ein
    Kreuzer wird im Spiel auf 100 px gezogen, ein Sprite mit 1100 px
    Breite kostet nur Platz.
"""

import argparse
import base64
import io
import json
import os
import re
import sys

# 'an' sind die Ancients. Der Knossos gehoert weder den Terranern noch den
# Shivanern; ihn unter eine bestehende Fraktion zu zwingen waere eine
# Notluege, die spaeter jemand fuer einen Fehler haelt.
FACTIONS = {"te", "ntf", "va", "sh", "an"}

# Kampfschiffe, dann Hilfsschiffe, dann Unbewegliches. Muss mit CLS_NAME im
# Mount-Editor uebereinstimmen - laufen die beiden auseinander, passen die
# Mounts nachher nicht mehr zu den Sprites.
CLASSES = {
    "fi", "bo", "cr", "co", "de", "sd",          # Kampfschiffe
    "fr", "tr", "ca", "sc", "me", "gm", "su", "ep",   # Hilfsschiffe
    "sg", "in", "fc",                            # unbeweglich
}

# Hoechstbreite je Klasse. Massgeblich ist, wie gross das Schiff im Spiel
# tatsaechlich gezogen wird, mal MAX_RES 3:
#   Jaeger/Bomber 58-65 -> 195   Kreuzer 100 -> 300
#   Korvette 130-140    -> 420   Zerstoerer 380 -> 1140   Boss 320-360 -> 1080
# Eine pauschale Grenze von 400 px hat die Zerstoerer und den Boss knapp
# dreifach hochskaliert und sichtbar weich gemacht.
SPRITE_PX = {
    "fi": 256, "bo": 256, "cr": 320, "co": 448, "de": 1152, "sd": 1152,
    # Die Hilfsschiffe werden noch nicht gerendert, es gibt also keine
    # gemessene Darstellungsgroesse. 448 ist die Korvettengrenze und damit
    # eine Schaetzung nach oben; nachziehen, sobald sie im Spiel stehen.
    "fr": 448, "tr": 448, "ca": 448, "sc": 448, "me": 448,
    "gm": 448, "su": 320, "ep": 256,
    "sg": 256, "fc": 256,
    "in": 1152,      # Arcadia und Knossos sind riesig
}
SPRITE_PX_DEFAULT = 448
BODY_PX = 512        # Kantenlaenge fuer Planeten und Sonnen
JPEG_Q = 82
CIRCLE_MIN = 0.97    # ab dieser Kreisguete reicht JPEG plus gerechnete Maske

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


# ── NAMENSSCHEMA ─────────────────────────────────────────────

def split_name(filename):
    """te-fi-hercmk2.png -> ('te','fi',['hercmk2'])  |  None wenn unpassend."""
    base = os.path.splitext(filename)[0].lower()
    parts = [p for p in base.split("-") if p]
    if len(parts) < 3:
        return None
    faction, cls = parts[0], parts[1]
    if faction not in FACTIONS or cls not in CLASSES:
        return None
    rest = [p for p in parts[2:] if p != "bonus"]
    if not rest:
        return None
    return faction, cls, rest


def hull_id(filename):
    """Rumpfkennung ohne Fraktion: Klasse plus erster Namensteil.
    te-de-orion-left.png und ntf-de-orion.png ergeben beide ('de','orion'),
    obwohl ihre Keys sich unterscheiden. Genau darum geht es."""
    p = split_name(filename)
    return None if p is None else (p[1], p[2][0])


def key_from_filename(filename, te_hulls=frozenset()):
    """te-fi-hercmk2.png -> fihercmk2 | te-de-orion-left.png -> deorionleft
    ntf-cr-aeolus.png -> ntfcraeolus, weil te-cr-aeolus.png existiert
    ntf-fi-loki.png   -> filoki,      weil es keine te-fi-loki.png gibt"""
    p = split_name(filename)
    if p is None:
        return None
    faction, cls, rest = p
    key = cls + "".join(rest)
    if faction == "ntf" and hull_id(filename) in te_hulls:
        return "ntf" + key
    return key


# ── SPRITES ──────────────────────────────────────────────────

def shrink_png(raw, max_px):
    """Verkleinert ein PNG, wenn es breiter als max_px ist. Ohne Pillow
    bleibt die Datei wie sie ist, der Build wird dann nur groesser."""
    if not HAVE_PIL:
        return raw, False
    im = Image.open(io.BytesIO(raw))
    if im.width <= max_px:
        return raw, False
    h = max(1, round(im.height * max_px / im.width))
    im = im.convert("RGBA").resize((max_px, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue(), True


def collect_sprites(folder):
    """Liest alle PNGs ein und gibt {key: (dataurl, dateiname)} zurueck."""
    names = [n for n in sorted(os.listdir(folder)) if n.lower().endswith(".png")]
    te_hulls = {hull_id(n) for n in names if n.startswith("te-") and hull_id(n)}

    sprites, skipped, collisions, shrunk = {}, [], [], []
    for name in names:
        key = key_from_filename(name, te_hulls)
        if key is None:
            skipped.append(name)
            continue
        if key in sprites:
            collisions.append((key, sprites[key][1], name))
            continue
        with open(os.path.join(folder, name), "rb") as fh:
            raw = fh.read()
        before = len(raw)
        cls = split_name(name)[1]
        limit = SPRITE_PX.get(cls, SPRITE_PX_DEFAULT)
        raw, did = shrink_png(raw, limit)
        if did:
            shrunk.append((name, limit, before, len(raw)))
        b64 = base64.b64encode(raw).decode("ascii")
        sprites[key] = ("data:image/png;base64," + b64, name)
    return sprites, skipped, collisions, shrunk


# ── PLANETEN UND SONNEN ──────────────────────────────────────

def circle_of(alpha):
    """Mittelpunkt, Radius und Guete der Alphascheibe, alles normiert.
    Bewusst ohne numpy: auf dem Server steht nur python3-pil, und
    ImageChops rechnet das in C statt in einer Python-Schleife."""
    from PIL import ImageChops, ImageDraw
    w, h = alpha.size
    mask = alpha.point(lambda v: 255 if v > 128 else 0)
    hist = mask.histogram()
    area = hist[255]
    if area == 0:
        return None
    bb = mask.getbbox()
    cx, cy = (bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0
    r = (area / 3.141592653589793) ** 0.5

    disc = Image.new("L", (w, h), 0)
    ImageDraw.Draw(disc).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    inter = ImageChops.darker(mask, disc).histogram()[255]
    union = ImageChops.lighter(mask, disc).histogram()[255]
    return cx / w, cy / h, r / w, (inter / union if union else 0.0)


def encode_body(path, force_png=False):
    """Gibt (dataurl, cx, cy, r, guete) zurueck. r == 0 heisst: echter
    Alphakanal, das Spiel schneidet nichts aus."""
    im = Image.open(path).convert("RGBA")
    im.thumbnail((BODY_PX, BODY_PX), Image.LANCZOS)
    alpha = im.split()[3]
    circ = circle_of(alpha)

    if not force_png and circ and circ[3] >= CIRCLE_MIN:
        cx, cy, r, q = circ
        # Ausserhalb der Scheibe schwarz faerben. Das komprimiert besser
        # und haelt Farbschlieren aus dem Rand heraus, die sonst als
        # heller Saum unter der gerechneten Maske hervorsehen wuerden.
        mask = alpha.point(lambda v: 255 if v > 128 else 0)
        rgb = Image.composite(im.convert("RGB"), Image.new("RGB", im.size, (0, 0, 0)), mask)
        buf = io.BytesIO()
        rgb.save(buf, "JPEG", quality=JPEG_Q, optimize=True)
        return ("data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii"),
                round(cx, 4), round(cy, 4), round(r, 4), q)

    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    q = circ[3] if circ else 0.0
    return ("data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii"),
            0.5, 0.5, 0.0, q)


def collect_bodies(folder, label, force_png=False):
    """Planeten oder Sonnen. Fehlt der Ordner, gibt es eben keine."""
    out = {}
    if not folder or not os.path.isdir(folder):
        print("Kein %s-Ordner (%s) - der Hintergrund bleibt leer" % (label, folder))
        return out
    if not HAVE_PIL:
        sys.exit("Abbruch: fuer %s wird Pillow gebraucht. sudo apt install python3-pil" % label)
    exts = (".dds", ".png", ".jpg", ".jpeg", ".tga", ".bmp")
    names = [n for n in sorted(os.listdir(folder)) if n.lower().endswith(exts)]
    total_raw = total_out = 0
    n_jpeg = n_png = 0
    for name in names:
        path = os.path.join(folder, name)
        key = os.path.splitext(name)[0]
        try:
            url, cx, cy, r, q = encode_body(path, force_png)
        except Exception as exc:
            print("  UEBERSPRUNGEN %s: %s" % (name, exc))
            continue
        total_raw += os.path.getsize(path)
        total_out += len(url) * 3 // 4
        if url.startswith("data:image/jpeg"):
            n_jpeg += 1
        else:
            n_png += 1
            if not force_png:
                print("  %s: Alpha ist keine Kreisscheibe (%.3f) - bleibt PNG" % (name, q))
        out[key] = {"src": url, "cx": cx, "cy": cy, "r": r}
    print("%s: %d Dateien, %d als JPEG mit gerechneter Maske, %d als PNG"
          % (label, len(out), n_jpeg, n_png))
    print("  %.1f MB Quelle -> %.2f MB eingebettet" % (total_raw / 1048576, total_out / 1048576))
    return out


def render_bodies(name, bodies):
    if not bodies:
        return "const %s={};" % name
    lines = ["const %s={" % name]
    for key in sorted(bodies):
        b = bodies[key]
        lines.append("  '%s':{src:'%s',cx:%s,cy:%s,r:%s},"
                     % (key, b["src"], b["cx"], b["cy"], b["r"]))
    lines[-1] = lines[-1].rstrip(",")
    lines.append("};")
    return "\n".join(lines)


# ── ICONS UND MOUNTS ─────────────────────────────────────────

def collect_icons(folder):
    """HUD-Icons. Anders als Sprites brauchen die kein Namensschema, der
    Dateiname ohne Endung ist der Key. Fehlt der Ordner, gibt es keine
    Icons und das Spiel faellt auf die gezeichneten Symbole zurueck."""
    icons = {}
    if not folder or not os.path.isdir(folder):
        return icons
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith(".png"):
            continue
        key = os.path.splitext(name)[0].lower()
        with open(os.path.join(folder, name), "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        icons[key] = "data:image/png;base64," + b64
    return icons


def render_icons(icons):
    if not icons:
        return "const ICON_DATA={};"
    lines = ["const ICON_DATA={"]
    for key in sorted(icons):
        lines.append("  '%s':'%s'," % (key, icons[key]))
    lines[-1] = lines[-1].rstrip(",")
    lines.append("};")
    return "\n".join(lines)


def find_block(html, declaration):
    """Findet 'const NAME={ ... };' und gibt (start, ende) zurueck."""
    start = html.find(declaration)
    if start < 0:
        return None
    i = html.find("{", start)
    if i < 0:
        return None
    depth, j = 0, i
    while j < len(html):
        c = html[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    else:
        return None
    end = html.find(";", j)
    return (start, end + 1) if end > 0 else None


def render_sprites(sprites):
    lines = ["const SPR_DATA={"]
    for key in sorted(sprites):
        lines.append("  '%s':'%s'," % (key, sprites[key][0]))
    lines[-1] = lines[-1].rstrip(",")
    lines.append("};")
    return "\n".join(lines)


def render_mounts(mounts):
    return "const MOUNTS=" + json.dumps(mounts, separators=(",", ":"), sort_keys=True) + ";"


def referenced_keys(html):
    """Sammelt alle Schiffs-Keys, die in ROLES und BEAM_DEFS auftauchen."""
    keys = set()
    block = find_block(html, "const ROLES=")
    if block:
        keys |= set(re.findall(r'"([a-z0-9]+)"', html[block[0]:block[1]]))
    block = find_block(html, "const BEAM_DEFS")
    if block:
        for m in re.finditer(r'^\s{2}([a-z0-9_]+)\s*:\s*\[', html[block[0]:block[1]], re.M):
            keys.add(m.group(1))
    return keys


def version_from(path):
    """v71 aus hlp_shooter_v71_logic.html. Von Hand gepflegt wuerde die
    Nummer irgendwann vergessen und dann dauerhaft etwas Falsches anzeigen,
    was schlimmer ist als gar keine Anzeige."""
    m = re.search(r"_v(\d+)_", os.path.basename(path))
    return ("v" + m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser(description="Packt Sprites, Mounts und Hintergrundkoerper in die Spieldatei.")
    ap.add_argument("--sprites", default="sprites", help="Ordner mit den PNG-Dateien")
    ap.add_argument("--icons", default="icons", help="Ordner mit HUD-Icons (optional)")
    ap.add_argument("--planets", default="planets", help="Ordner mit Planeten (optional)")
    ap.add_argument("--suns", default="suns", help="Ordner mit Sonnen (optional)")
    ap.add_argument("--mounts", default="hlp_mounts_final.json", help="Mount-JSON aus dem Editor")
    ap.add_argument("--game", default="hlp_shooter_v3.html", help="Eingabe-Spieldatei")
    ap.add_argument("--out", default="hlp_shooter_v4.html", help="Ausgabe-Spieldatei")
    ap.add_argument("--hz", type=int, default=None,
                    help="Spieltempo in Logikschritten pro Sekunde (ueberschreibt TICK_HZ, Standard 100)")
    args = ap.parse_args()

    for path, label in ((args.sprites, "Sprite-Ordner"), (args.mounts, "Mount-JSON"), (args.game, "Spieldatei")):
        if not os.path.exists(path):
            sys.exit("Abbruch: %s nicht gefunden: %s" % (label, path))

    print("Sprites lesen aus %s ..." % args.sprites)
    sprites, skipped, collisions, shrunk = collect_sprites(args.sprites)
    if not sprites:
        sys.exit("Abbruch: keine gueltigen Sprites gefunden.")
    print("  %d Sprites eingelesen" % len(sprites))
    for name in skipped:
        print("  uebersprungen (Namensschema passt nicht): %s" % name)
    for key, first, second in collisions:
        print("  KOLLISION: %s und %s ergeben beide den Key '%s' - zweite Datei ignoriert" % (first, second, key))
    for name, limit, a, b in shrunk:
        print("  verkleinert auf %4d px: %-26s %5.0f KB -> %4.0f KB" % (limit, name, a / 1024, b / 1024))
    for name in sorted(n for n in os.listdir(args.sprites) if n.startswith("ntf-")):
        k = key_from_filename(name, {hull_id(x) for x in os.listdir(args.sprites)
                                     if x.startswith("te-") and hull_id(x)})
        print("  NTF: %-24s -> %s" % (name, k))

    icons = collect_icons(args.icons)
    if icons:
        print("Icons gelesen: %d aus %s" % (len(icons), args.icons))
    else:
        print("Keine Icons gefunden (%s) - das Spiel nutzt die gezeichneten Symbole" % args.icons)

    planets = collect_bodies(args.planets, "Planeten")
    suns = collect_bodies(args.suns, "Sonnen", force_png=True)

    with open(args.mounts, encoding="utf-8") as fh:
        mounts = json.load(fh)
    print("Mounts gelesen: %d Schiffe" % len(mounts))

    with open(args.game, encoding="utf-8") as fh:
        html = fh.read()

    # --- Abgleich Sprites <-> Mounts ---
    only_sprite = sorted(set(sprites) - set(mounts))
    only_mount = sorted(set(mounts) - set(sprites))
    for key in only_sprite:
        print("  WARNUNG: Sprite '%s' (%s) hat keine Mounts" % (key, sprites[key][1]))
    for key in only_mount:
        print("  WARNUNG: Mounts fuer '%s' vorhanden, aber kein Sprite" % key)

    # --- Abgleich Spielcode <-> Sprites ---
    dangling = sorted(referenced_keys(html) - set(sprites))
    if dangling:
        print("\n  Diese Keys stehen noch im Spielcode, es gibt aber kein Sprite dazu:")
        for key in dangling:
            print("    %s" % key)
        print("  (ROLES und BEAM_DEFS muessen darauf angepasst werden.)")

    # --- SPR_DATA ersetzen ---
    block = find_block(html, "const SPR_DATA=")
    if not block:
        sys.exit("Abbruch: SPR_DATA nicht in der Spieldatei gefunden.")
    html = html[:block[0]] + render_sprites(sprites) + "\n\n" + render_mounts(mounts) + html[block[1]:]

    # --- ICON_DATA ersetzen, falls der Platzhalter in der Spieldatei steht ---
    block = find_block(html, "const ICON_DATA=")
    if block:
        html = html[:block[0]] + render_icons(icons) + html[block[1]:]
    elif icons:
        print("  WARNUNG: ICON_DATA nicht in der Spieldatei gefunden, Icons wurden nicht eingebaut")

    # --- PLANET_DATA und SUN_DATA ersetzen ---
    for name, data in (("PLANET_DATA", planets), ("SUN_DATA", suns)):
        block = find_block(html, "const %s=" % name)
        if block:
            html = html[:block[0]] + render_bodies(name, data) + html[block[1]:]
        elif data:
            print("  WARNUNG: %s nicht in der Spieldatei gefunden, %d Bilder wurden nicht eingebaut"
                  % (name, len(data)))

    # --- vorhandenen MOUNTS-Block aus einem frueheren Lauf entfernen ---
    tail = html.find("const MOUNTS=", html.find("const MOUNTS=") + 1)
    if tail > 0:
        block = find_block(html[tail:], "const MOUNTS=")
        if block:
            html = html[:tail + block[0]] + html[tail + block[1]:]

    # --- Versionsnummer aus dem Dateinamen setzen ---
    ver = version_from(args.game)
    if ver:
        html, n = re.subn(r"const GAME_VERSION='[^']*'",
                          "const GAME_VERSION='%s'" % ver, html, count=1)
        print("Version: %s%s" % (ver, "" if n else "  (GAME_VERSION nicht gefunden!)"))
    else:
        print("  WARNUNG: aus '%s' laesst sich keine Version lesen, es bleibt bei 'dev'"
              % os.path.basename(args.game))

    # --- Spieltempo ueberschreiben ---
    if args.hz is not None:
        hz = max(30, min(200, args.hz))
        html, n = re.subn(r"const TICK_HZ = \d+", "const TICK_HZ = %d" % hz, html, count=1)
        if n:
            print("Spieltempo auf %d Hz gesetzt" % hz)
        else:
            print("  WARNUNG: TICK_HZ nicht gefunden, --hz wurde ignoriert")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)

    size = os.path.getsize(args.out) / (1024 * 1024)
    print("\nGeschrieben: %s (%.1f MB)" % (args.out, size))


if __name__ == "__main__":
    main()
