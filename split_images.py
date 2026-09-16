#!/usr/bin/env python3
"""Move the remaining embedded images out of the FS3 logic file.

Handles two kinds of embedded images:
  <img id="NAME" src="data:...">     -> images/NAME.<ext>
  const NEB_DATA={ 'KEY':'data:...'  -> nebulae/KEY.<ext>

Each data URI in the logic file is replaced by a token
@@FS3_ASSET:<path>@@, and build_game.py gets a small inline_assets() step
that turns the tokens back into data URIs at build time.

Safety: the game is built twice (old packer + old logic file, new packer +
new logic file). Only if both outputs are byte-identical are the new files
installed; the originals go to backup/. On any failure nothing is changed.

Usage (in /home/belisarius/fs3-build, no sudo needed):
    python3 split_images.py
"""
import base64
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

MIME_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
DATA_URI = re.compile(r"data:([a-z]+/[a-z0-9.+-]+);base64,([A-Za-z0-9+/=]+)")
TOKEN = "@@FS3_ASSET:%s@@"
BUILD_ARGS = ["--sprites", "sprites", "--icons", "icons",
              "--mounts", "hlp_mounts_final.json"]  # mirrors build.sh

PACKER_FUNC = '''
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
        print("Bilddateien eingebettet: %d" % n)
    return html


'''
PACKER_CALL = "    html = inline_assets(html)  # resolve @@FS3_ASSET@@ tokens\n\n"


def newest_logic_file():
    def ver(p):
        m = re.search(r"_v(\d+)_logic\.html$", p)
        return int(m.group(1)) if m else -1
    files = sorted(glob.glob("hlp_shooter_v*_logic.html"), key=ver)
    return files[-1] if files else None


def neb_range(html):
    """Character range of the NEB_DATA block, or (0, 0) if absent."""
    start = html.find("const NEB_DATA=")
    if start < 0:
        return (0, 0)
    end = html.find("};", start)
    return (start, end if end > 0 else len(html))


def classify(html):
    """Return a list of (match, target_path). Aborts on anything unknown."""
    neb = neb_range(html)
    found, unknown = [], []
    for m in DATA_URI.finditer(html):
        line = html.count("\n", 0, m.start()) + 1
        mime, b64 = m.group(1), m.group(2)
        ext = MIME_EXT.get(mime)
        before = html[max(0, m.start() - 400):m.start()]
        tag = before[before.rfind("<"):]
        img = re.match(r'<img\s[^<>]*\bid="([A-Za-z0-9_-]+)"[^<>]*\bsrc="$', tag)
        key = re.search(r"'([A-Za-z0-9_-]+)'\s*:\s*'$", before)
        if img:
            path = "images/%s" % img.group(1)
        elif neb[0] <= m.start() < neb[1] and key:
            path = "nebulae/%s" % key.group(1)
        else:
            unknown.append("Zeile %d: keinem Muster zuzuordnen" % line)
            continue
        if not ext:
            unknown.append("Zeile %d: Bildtyp %s nicht vorgesehen" % (line, mime))
            continue
        raw = base64.b64decode(b64)
        if base64.b64encode(raw).decode("ascii") != b64:
            unknown.append("Zeile %d: Base64 nicht verlustfrei umkehrbar" % line)
            continue
        found.append((m, path + ext, raw))
    if unknown:
        print("\n".join("  " + u for u in unknown))
        sys.exit("Abbruch: nicht alle Bilder zuordenbar - nichts geaendert.")
    paths = [p for _, p, _ in found]
    dupes = sorted({p for p in paths if paths.count(p) > 1})
    if dupes:
        sys.exit("Abbruch: doppelte Zielnamen %s - nichts geaendert." % ", ".join(dupes))
    return found


def patch_packer(src):
    if "def inline_assets(" in src:
        return src  # already patched
    for pattern in (r"^def main\(\):$", r'^    with open\(args\.out, "w", encoding="utf-8"\) as fh:$'):
        n = len(re.findall(pattern, src, re.M))
        if n != 1:
            sys.exit("Abbruch: Suchtext im Packer %d-mal statt einmal gefunden: %s" % (n, pattern))
    src = re.sub(r"^def main\(\):$", lambda m: PACKER_FUNC.lstrip("\n") + m.group(0), src, count=1, flags=re.M)
    src = re.sub(r'^    with open\(args\.out, "w", encoding="utf-8"\) as fh:$',
                 lambda m: PACKER_CALL + m.group(0), src, count=1, flags=re.M)
    return src


def build(packer, game, out):
    cmd = [sys.executable, packer] + BUILD_ARGS + ["--game", game, "--out", out]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout[-1500:], res.stderr[-1500:])
        return False
    return True


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def backup(path):
    os.makedirs("backup", exist_ok=True)
    bak = os.path.join("backup", "%s.%s" % (os.path.basename(path), time.strftime("%Y%m%d-%H%M%S")))
    n = 1
    while os.path.exists(bak):  # never overwrite an existing backup
        bak = bak.rsplit(".~", 1)[0] + ".~%d" % n
        n += 1
    shutil.copyfile(path, bak)
    return bak


def main():
    logic = newest_logic_file()
    if not logic or not os.path.exists("build_game.py"):
        sys.exit("Abbruch: Logikdatei oder build_game.py nicht gefunden. Im Ordner fs3-build starten.")
    print("Logikdatei: %s (%.0f KB)" % (logic, os.path.getsize(logic) / 1024))

    with open(logic, encoding="utf-8") as fh:
        html = fh.read()
    found = classify(html)
    if not found:
        print("Nichts zu tun: keine eingebetteten Bilder mehr in der Logikdatei.")
        return

    for _, path, raw in found:
        print("  %-28s %7.1f KB" % (path, len(raw) / 1024))

    # Refuse to clobber different existing files.
    for _, path, raw in found:
        if os.path.exists(path):
            with open(path, "rb") as fh:
                if fh.read() != raw:
                    sys.exit("Abbruch: %s existiert schon mit anderem Inhalt - nichts geaendert." % path)

    tokenized, last = [], 0
    for m, path, _ in found:
        tokenized.append(html[last:m.start()])
        tokenized.append(TOKEN % path)
        last = m.end()
    tokenized.append(html[last:])
    tokenized = "".join(tokenized)

    with open("build_game.py", encoding="utf-8") as fh:
        packer_old = fh.read()
    packer_new = patch_packer(packer_old)

    tmp = tempfile.mkdtemp(prefix="fs3img_")
    created = []
    try:
        new_packer = os.path.join(tmp, "build_game.py")
        new_logic = os.path.join(tmp, os.path.basename(logic))  # same name -> same GAME_VERSION
        with open(new_packer, "w", encoding="utf-8") as fh:
            fh.write(packer_new)
        with open(new_logic, "w", encoding="utf-8") as fh:
            fh.write(tokenized)

        for _, path, raw in found:
            d = os.path.dirname(path)
            if not os.path.isdir(d):
                os.makedirs(d)
                created.append(d)
            if not os.path.exists(path):
                with open(path, "wb") as fh:
                    fh.write(raw)
                created.append(path)

        print("Baue zweimal zum Vergleich ...")
        out_a, out_b = os.path.join(tmp, "a.html"), os.path.join(tmp, "b.html")
        ok = build("build_game.py", logic, out_a) and build(new_packer, new_logic, out_b)
        if not ok or sha(out_a) != sha(out_b):
            raise RuntimeError("Bauen fehlgeschlagen" if not ok else "Bauergebnis unterschiedlich")

        bak_logic, bak_packer = backup(logic), backup("build_game.py")
        shutil.copyfile(new_logic, logic)
        if packer_new != packer_old:
            shutil.copyfile(new_packer, "build_game.py")
    except (RuntimeError, OSError) as exc:
        for path in reversed(created):  # undo only what this run created
            (os.rmdir if os.path.isdir(path) else os.remove)(path)
        sys.exit("\nABBRUCH: %s - nichts geaendert." % exc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    left = len(DATA_URI.findall(tokenized))
    print("\nBauergebnis byteidentisch.")
    print("Logikdatei ersetzt:  %.0f KB, Original in %s" % (os.path.getsize(logic) / 1024, bak_logic))
    print("Packer ergaenzt,     Original in %s" % bak_packer)
    print("Bilder abgelegt in:  images/ und nebulae/")
    print("\nGITHUB: %s" % ("bereit zum Hochladen" if left == 0 else "noch %d Bilder in der Datei" % left))


if __name__ == "__main__":
    main()
