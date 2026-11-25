#!/usr/bin/env python3
"""
HLP Space Shooter - Asset Packer
=================================

Baut die Spieldatei neu auf:
  - liest HUD-Icons aus dem Icon-Ordner und ersetzt ICON_DATA
  - liest Planeten und Sonnen und ersetzt PLANET_DATA und SUN_DATA
  - haengt die Mount-Definitionen als MOUNTS an, dazu die Rahmen und
    Umrisse aus den Modellen als OUTLINES (F103)
  - meldet jeden Key, der im Spielcode vorkommt, aber keinen Umriss hat

Aufruf:
    python3 build_game.py --mounts hlp_mounts_final.json \
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
"""

import argparse
import base64
import io
import json
import os
import re
import sys


# --- Output (Silvio, 16.11.2026: the build spelled out every single file;
# he wants the essentials and what changed). Lists go to detail(), which
# only speaks with --laut; the numbers land in STATS and are printed as a
# short block at the end; warnings are collected and always printed. ---
LOUD = False
STATS = {}
WARN = []
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".build_state.json")


def detail(msg):
    """One line of the long list - only with --laut."""
    if LOUD:
        print(msg)


def warn(msg):
    """A warning. Always printed, after the numbers."""
    WARN.append(msg)


def read_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def write_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump(state, fh, separators=(",", ":"), sort_keys=True)
    except Exception as exc:
        warn("WARNUNG: Zustand fuer den Vergleich nicht geschrieben (%s)" % exc)


def _diff_line(label, old, new, limit=6):
    """What came and what went between two name lists, in one line."""
    add, gone = sorted(set(new) - set(old)), sorted(set(old) - set(new))
    if not add and not gone:
        return None
    bits = []
    for word, names in (("neu", add), ("weg", gone)):
        if not names:
            continue
        shown = ", ".join(names[:limit])
        if len(names) > limit:
            shown += " und %d weitere" % (len(names) - limit)
        bits.append("%d %s: %s" % (len(names), word, shown))
    return "    %-9s %s" % (label, "; ".join(bits))


def print_changes(old, new):
    """Changed since the last build - the line Silvio asked for."""
    if not old:
        print("\n  Erster Bau mit dieser Fassung - kein Vergleich moeglich.")
        return
    lines = []
    if old.get("version") != new.get("version"):
        lines.append("    %-9s %s -> %s" % ("Version", old.get("version") or "?", new.get("version")))
    for label, key in (("Modelle", "models"),
                       ("Musik", "music"), ("Planeten", "planets"), ("Sonnen", "suns"),
                       ("Icons", "icons")):
        line = _diff_line(label, old.get(key) or [], new.get(key) or [])
        if line:
            lines.append(line)
    for label, key in (("Sounds", "sounds"), ("Mounts", "mounts"), ("Umrisse", "outlines")):
        a, b = old.get(key), new.get(key)
        if a is not None and b is not None and a != b:
            lines.append("    %-9s %d -> %d" % (label, a, b))
    print("\n  Geaendert seit dem letzten Bau:")
    if lines:
        print("\n".join(lines))
    else:
        print("    nur die Spieldatei selbst - sonst alles unveraendert")


# ── SPRITES, GONE ────────────────────────────────────────────
# F103 stage 4 (v313): the 121 ship sprites and everything that served them
# are no longer here - the filename scheme (te-/ntf- prefix, class, hull),
# the per-hull width cap that shrank an oversized picture, and the reading
# of the sprite folder itself. A hull's frame and silhouette now come from
# her model (tools/pof/mkoutline.py -> hlp_outlines.json), and the hull is
# drawn from the model in the game. The sprite folder on the server is not
# read any more and can go.


# ── PLANETEN UND SONNEN ──────────────────────────────────────
BODY_PX = 512        # Kantenlaenge fuer Planeten und Sonnen
JPEG_Q = 82
CIRCLE_MIN = 0.97    # ab dieser Kreisguete reicht JPEG plus gerechnete Maske

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False


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
        warn("WARNUNG: kein %s-Ordner (%s) - der Hintergrund bleibt leer" % (label, folder))
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
            warn("WARNUNG: %s uebersprungen: %s" % (name, exc))
            continue
        total_raw += os.path.getsize(path)
        total_out += len(url) * 3 // 4
        if url.startswith("data:image/jpeg"):
            n_jpeg += 1
        else:
            n_png += 1
            if not force_png:
                detail("  %s: Alpha ist keine Kreisscheibe (%.3f) - bleibt PNG" % (name, q))
        out[key] = {"src": url, "cx": cx, "cy": cy, "r": r}
    detail("%s: %d Dateien, %d als JPEG mit gerechneter Maske, %d als PNG"
           % (label, len(out), n_jpeg, n_png))
    detail("  %.1f MB Quelle -> %.2f MB eingebettet" % (total_raw / 1048576, total_out / 1048576))
    STATS[label] = len(out)
    STATS["names:" + label] = sorted(out)
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


# Mapping must match MIME_EXT in split_images.py.
ASSET_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}


def inline_assets(html):
    """Replace @@FS3_ASSET:path@@ tokens with data URIs read from disk.
    Keeps images out of the logic file so it can live in git."""
    def repl(m):
        path = m.group(1)
        ext = os.path.splitext(path)[1].lower()
        if ext not in ASSET_MIME:
            sys.exit("Abbruch: unbekannter Bildtyp: %s" % path)
        if not os.path.isfile(path):
            sys.exit("Abbruch: Bilddatei fehlt: %s" % path)
        with open(path, "rb") as fh:
            data = fh.read()
        return "data:%s;base64,%s" % (ASSET_MIME[ext], base64.b64encode(data).decode("ascii"))
    html, n = re.subn(r"@@FS3_ASSET:([A-Za-z0-9_./-]+)@@", repl, html)
    if n:
        STATS["Bilddateien"] = n
    return inline_sounds(html)


SOUND_MIME = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg"}


def inline_sounds(html):
    """Replace @@FS3_SOUND:path@@ tokens with data URIs. Unlike a picture a
    missing sound does not stop the build: the token becomes an empty
    string and the game leaves that sound silent."""
    missing = []
    def repl(m):
        path = m.group(1)
        ext = os.path.splitext(path)[1].lower()
        if ext not in SOUND_MIME or not os.path.isfile(path):
            missing.append(path)
            return ""
        with open(path, "rb") as fh:
            data = fh.read()
        return "data:%s;base64,%s" % (SOUND_MIME[ext], base64.b64encode(data).decode("ascii"))
    html, n = re.subn(r"@@FS3_SOUND:([A-Za-z0-9_./-]+)@@", repl, html)
    if n:
        STATS["Sounds"] = n - len(missing)
    if missing:
        warn("WARNUNG: Sounds fehlen (bleiben stumm): %s"
             % ", ".join(os.path.basename(p) for p in missing))
    # Music is not put into the page: only the names of the pieces in
    # music/, which build.sh copies next to the page.
    tracks = sorted(n for n in os.listdir("music") if n.lower().endswith(".mp3")) if os.path.isdir("music") else []
    if "@@FS3_MUSIC_LIST@@" in html:
        html = html.replace("@@FS3_MUSIC_LIST@@", ",".join(tracks))
        STATS["Musik"] = len(tracks)
        STATS["names:Musik"] = tracks
    return html


def model_files(root="models"):
    """v201: the files the field needs of every capital ship with a packed
    full model (full.bin.gz and the 1024 px maps), for the loading page:
    [path, bytes, stamp]. The page fetches them with the game."""
    out = []
    if not os.path.isdir(root):
        return out
    for key in sorted(os.listdir(root)):
        d = os.path.join(root, key)
        if not os.path.isfile(os.path.join(d, "full.bin.gz")):
            continue
        # v203: the small craft (fighters, bombers, sentries, support
        # ships, pods, containers) take their 512 px maps on the field
        small = key[:2] in ("fi", "bo", "ep", "fc", "su") or (key[:2] == "sg" and key != "sgmjolnir")
        for fn in sorted(os.listdir(d)):
            if fn == "full.bin.gz" or fn.endswith("512.webp" if small else "1024.webp"):
                st = os.stat(os.path.join(d, fn))
                out.append(["models/%s/%s" % (key, fn), st.st_size, "%d-%d" % (int(st.st_mtime), st.st_size)])
    STATS["Modelldateien"] = len(out)
    STATS["ModellMB"] = sum(f[1] for f in out) / 1048576.0
    STATS["names:Modelle"] = sorted(k for k in os.listdir(root)
                                    if os.path.isfile(os.path.join(root, k, "full.bin.gz")))
    return out


def loader_bodies(folder, planets, suns):
    """The planets and suns for the loading page. They are written beside it
    as files, not embedded: the page has to appear at once, and this way it
    can roll a different sky on every reload, the way the game does. The
    pictures are the same ones the game carries, already re-encoded."""
    out = []
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    for src, kind in ((planets, "planet"), (suns, "sun")):
        for key in sorted(src or {}):
            b = src[key]
            head, _, b64 = b["src"].partition(",")
            ext = ".jpg" if "jpeg" in head else ".png"
            name = kind + "_" + re.sub(r"[^A-Za-z0-9_.-]", "_", key) + ext
            with open(os.path.join(folder, name), "wb") as fh:
                fh.write(base64.b64decode(b64))
            out.append({"key": key, "kind": kind, "file": name,
                        "cx": b["cx"], "cy": b["cy"], "r": b["r"]})
    return out


def write_loader(path, game, planets=None, suns=None):
    """The loading page: shows at once and fetches the game with a progress
    bar. It needs the game's file name (beside it), its size in bytes (the
    server sends none with gzip) and a stamp against a stale cache."""
    if not os.path.isfile("loader.html"):
        sys.exit("Abbruch: loader.html fehlt.")
    tpl = open("loader.html", encoding="utf-8").read()
    st = os.stat(game)
    stamp = "%d-%d" % (int(st.st_mtime), st.st_size)
    page = (tpl.replace("@@GAME_FILE@@", os.path.basename(game))
               .replace("@@GAME_BYTES@@", str(st.st_size))
               .replace("@@STAMP@@", stamp)
               .replace("@@MODELS@@", json.dumps(model_files()))
               .replace("@@PLANETS@@", json.dumps(
                   loader_bodies(os.path.join(os.path.dirname(os.path.abspath(path)), "bodies"),
                                 planets or {}, suns or {}))))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    STATS["Ladeseite"] = path


def main():
    ap = argparse.ArgumentParser(description="Packt Mounts, Umrisse, Icons und Hintergrundkoerper in die Spieldatei.")
    ap.add_argument("--icons", default="icons", help="Ordner mit HUD-Icons (optional)")
    ap.add_argument("--planets", default="planets", help="Ordner mit Planeten (optional)")
    ap.add_argument("--suns", default="suns", help="Ordner mit Sonnen (optional)")
    ap.add_argument("--mounts", default="hlp_mounts_final.json", help="Mount-JSON aus dem Editor")
    ap.add_argument("--outlines", default="hlp_outlines.json", help="Rahmen und Umrisse aus den Modellen (F103)")
    ap.add_argument("--game", default="hlp_shooter_v3.html", help="Eingabe-Spieldatei")
    ap.add_argument("--out", default="hlp_shooter_v4.html", help="Ausgabe-Spieldatei")
    ap.add_argument("--loader", default=None,
                    help="Ladeseite (index.html), die die Spieldatei mit Fortschrittsbalken laedt")
    ap.add_argument("--laut", action="store_true",
                    help="die alte, ausfuehrliche Ausgabe: jede Datei einzeln")
    ap.add_argument("--hz", type=int, default=None,
                    help="Spieltempo in Logikschritten pro Sekunde (ueberschreibt TICK_HZ, Standard 100)")
    args = ap.parse_args()
    global LOUD
    LOUD = args.laut

    for path, label in ((args.mounts, "Mount-JSON"), (args.game, "Spieldatei")):
        if not os.path.exists(path):
            sys.exit("Abbruch: %s nicht gefunden: %s" % (label, path))

    icons = collect_icons(args.icons)
    if icons:
        STATS["Icons"] = len(icons)
        STATS["names:Icons"] = sorted(icons)
    else:
        warn("WARNUNG: keine Icons gefunden (%s) - das Spiel nutzt die gezeichneten Symbole" % args.icons)

    planets = collect_bodies(args.planets, "Planeten")
    suns = collect_bodies(args.suns, "Sonnen", force_png=True)

    with open(args.mounts, encoding="utf-8") as fh:
        mounts = json.load(fh)
    STATS["Mounts"] = len(mounts)
    # F103: frames and outlines from the models (tools/pof/mkoutline.py)
    outlines = {}
    if os.path.exists(args.outlines):
        with open(args.outlines, encoding="utf-8") as fh:
            outlines = json.load(fh)
    STATS["Umrisse"] = len(outlines)

    with open(args.game, encoding="utf-8") as fh:
        html = fh.read()

    # --- Abgleich Spielcode <-> Umrisse (F103 stage 4) ---
    # The sprites are gone; a hull's frame and silhouette come from her
    # model (tools/pof/mkoutline.py -> hlp_outlines.json). A key the game
    # names but no model covers would have no frame at all, so it is
    # worth saying.
    for key in sorted(set(mounts) - set(outlines)):
        warn("WARNUNG: Mounts fuer '%s' vorhanden, aber kein Umriss aus dem Modell" % key)
    dangling = sorted(referenced_keys(html) - set(outlines))
    if dangling:
        warn("WARNUNG: diese Keys stehen im Spielcode, haben aber keinen Umriss: %s"
             % ", ".join(dangling) + " (ROLES und BEAM_DEFS anpassen)")

    # --- SPR_DATA ersetzen ---
    block = find_block(html, "const SPR_DATA=")
    if not block:
        sys.exit("Abbruch: SPR_DATA nicht in der Spieldatei gefunden.")
    # F103 stage 4: MOUNTS and OUTLINES take the place the 121 sprites used
    # to hold (13.8 of 31 MB). Both are made from the models.
    html = (html[:block[0]] + render_mounts(mounts)
            + "\nconst OUTLINES=" + json.dumps(outlines, separators=(",", ":"), sort_keys=True) + ";"
            + html[block[1]:])

    # --- ICON_DATA ersetzen, falls der Platzhalter in der Spieldatei steht ---
    block = find_block(html, "const ICON_DATA=")
    if block:
        html = html[:block[0]] + render_icons(icons) + html[block[1]:]
    elif icons:
        warn("WARNUNG: ICON_DATA nicht in der Spieldatei gefunden, Icons wurden nicht eingebaut")

    # --- PLANET_DATA und SUN_DATA ersetzen ---
    for name, data in (("PLANET_DATA", planets), ("SUN_DATA", suns)):
        block = find_block(html, "const %s=" % name)
        if block:
            html = html[:block[0]] + render_bodies(name, data) + html[block[1]:]
        elif data:
            warn("WARNUNG: %s nicht in der Spieldatei gefunden, %d Bilder wurden nicht eingebaut"
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
        STATS["Version"] = ver
        if not n:
            warn("WARNUNG: GAME_VERSION nicht in der Spieldatei gefunden!")
    else:
        warn("WARNUNG: aus '%s' laesst sich keine Version lesen, es bleibt bei 'dev'"
             % os.path.basename(args.game))

    # --- Spieltempo ueberschreiben ---
    if args.hz is not None:
        hz = max(30, min(200, args.hz))
        html, n = re.subn(r"const TICK_HZ = \d+", "const TICK_HZ = %d" % hz, html, count=1)
        if n:
            STATS["Hz"] = hz
        else:
            warn("WARNUNG: TICK_HZ nicht gefunden, --hz wurde ignoriert")

    html = inline_assets(html)  # resolve @@FS3_ASSET@@ tokens

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)

    size = os.path.getsize(args.out) / (1024 * 1024)
    if args.loader:
        write_loader(args.loader, args.out, planets, suns)

    # --- the short report (Silvio, 16.11.2026) ---
    print("\nFS3 build %s" % STATS.get("Version", "ohne Versionsnummer"))
    print("")
    print("  %-9s %d Planeten, %d Sonnen, %d Icons, %d Dateien"
          % ("Bilder", STATS.get("Planeten", 0), STATS.get("Sonnen", 0),
             STATS.get("Icons", 0), STATS.get("Bilddateien", 0)))
    print("  %-9s %d Sounds, %d Musikstuecke"
          % ("Klaenge", STATS.get("Sounds", 0), STATS.get("Musik", 0)))
    print("  %-9s %d Schiffe, %d Dateien, %.0f MB"
          % ("Modelle", len(STATS.get("names:Modelle", [])),
             STATS.get("Modelldateien", 0), STATS.get("ModellMB", 0.0)))
    print("  %-9s %d Mounts, %d Umrisse"
          % ("Daten", STATS.get("Mounts", 0), STATS.get("Umrisse", 0)))
    if "Hz" in STATS:
        print("  %-9s %d Hz" % ("Tempo", STATS["Hz"]))

    if WARN:
        print("")
        for line in WARN:
            print("  " + line)

    state = {"version": STATS.get("Version"),
             "models": STATS.get("names:Modelle", []),
             "music": STATS.get("names:Musik", []),
             "planets": STATS.get("names:Planeten", []),
             "suns": STATS.get("names:Sonnen", []),
             "icons": STATS.get("names:Icons", []),
             "sounds": STATS.get("Sounds"), "mounts": STATS.get("Mounts"),
             "outlines": STATS.get("Umrisse")}
    print_changes(read_state(), state)
    write_state(state)

    print("\n  Fertig: %s (%.1f MB)%s"
          % (args.out, size, ", Ladeseite geschrieben" if STATS.get("Ladeseite") else ""))


if __name__ == "__main__":
    main()
