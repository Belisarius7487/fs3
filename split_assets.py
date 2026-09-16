#!/usr/bin/env python3
"""Strip embedded image data from the FS3 logic file.

build_game.py rebuilds SPR_DATA, ICON_DATA, PLANET_DATA, SUN_DATA and MOUNTS
from the folders on every run, so the copies inside the logic file are dead
weight. This script empties those blocks, then builds the game twice (original
and stripped logic file) and only replaces the logic file if both outputs are
byte-identical. The original is kept under backup/.

Usage (in /home/belisarius/fs3-build, no sudo needed):
    python3 split_assets.py            # newest hlp_shooter_v*_logic.html
    python3 split_assets.py FILE       # a specific logic file
"""
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_game import find_block  # same block parser as the packer

DATA_BLOCKS = ("SPR_DATA", "ICON_DATA", "PLANET_DATA", "SUN_DATA")
BUILD_ARGS = ["--sprites", "sprites", "--icons", "icons",
              "--mounts", "hlp_mounts_final.json"]  # mirrors build.sh


def newest_logic_file():
    def ver(p):
        m = re.search(r"_v(\d+)_logic\.html$", p)
        return int(m.group(1)) if m else -1
    files = sorted(glob.glob("hlp_shooter_v*_logic.html"), key=ver)
    return files[-1] if files else None


def strip(html):
    """Return (stripped_html, report). Aborts on ambiguous declarations."""
    report = []
    for name in DATA_BLOCKS:
        decl = "const %s=" % name
        count = html.count(decl)
        if count > 1:
            sys.exit("Abbruch: '%s' kommt %d-mal vor, erwartet hoechstens einmal." % (decl, count))
        if count == 0:
            report.append("  %-11s nicht vorhanden" % name)
            continue
        block = find_block(html, decl)
        if not block:
            sys.exit("Abbruch: Block '%s' laesst sich nicht abgrenzen." % name)
        size = block[1] - block[0]
        html = html[:block[0]] + "const %s={};" % name + html[block[1]:]
        report.append("  %-11s %8.1f KB entfernt" % (name, size / 1024))

    # Remove every stale MOUNTS block; the packer inserts a fresh one.
    removed = 0
    while True:
        block = find_block(html, "const MOUNTS=")
        if not block:
            break
        removed += block[1] - block[0]
        html = html[:block[0]] + html[block[1]:]
    report.append("  %-11s %8.1f KB entfernt" % ("MOUNTS", removed / 1024))
    return html, report


def leftover_data_uris(html):
    """Group remaining data: URIs by the nearest preceding 'const NAME'."""
    groups = {}
    for m in re.finditer(r"data:[a-z]+/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=]+", html):
        head = html.rfind("const ", 0, m.start())
        owner = re.match(r"const\s+([A-Za-z0-9_$]+)", html[head:head + 80]) if head >= 0 else None
        key = owner.group(1) if owner else "(unbekannt)"
        n, size = groups.get(key, (0, 0))
        groups[key] = (n + 1, size + len(m.group(0)))
    return groups


def build(game_path, out_path):
    cmd = [sys.executable, "build_game.py"] + BUILD_ARGS + ["--game", game_path, "--out", out_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout[-2000:], res.stderr[-2000:])
        sys.exit("Abbruch: Bauen mit %s ist fehlgeschlagen." % game_path)


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def first_difference(a, b):
    with open(a, "rb") as fa, open(b, "rb") as fb:
        x, y = fa.read(), fb.read()
    i = next((k for k in range(min(len(x), len(y))) if x[k] != y[k]), min(len(x), len(y)))
    # Short, printable context only - never dump base64 blobs.
    ctx = lambda s: s[max(0, i - 60):i + 60].decode("utf-8", "replace")[:120]
    return i, ctx(x), ctx(y)


def main():
    logic = sys.argv[1] if len(sys.argv) > 1 else newest_logic_file()
    if not logic or not os.path.exists(logic):
        sys.exit("Abbruch: keine Logikdatei gefunden.")
    print("Logikdatei: %s (%.1f MB)" % (logic, os.path.getsize(logic) / 1048576))

    with open(logic, encoding="utf-8") as fh:
        original = fh.read()
    stripped, report = strip(original)
    print("\n".join(report))
    if stripped == original:
        print("Nichts zu tun: die Datei ist bereits getrennt.")
        return

    tmp = tempfile.mkdtemp(prefix="fs3split_")
    # Same basename in the temp dir, so GAME_VERSION comes out identical.
    cand = os.path.join(tmp, os.path.basename(logic))
    with open(cand, "w", encoding="utf-8") as fh:
        fh.write(stripped)

    print("Baue zweimal zum Vergleich ...")
    out_a, out_b = os.path.join(tmp, "a.html"), os.path.join(tmp, "b.html")
    build(logic, out_a)
    build(cand, out_b)

    if sha(out_a) != sha(out_b):
        pos, ctx_a, ctx_b = first_difference(out_a, out_b)
        keep = logic + ".split-candidate"
        shutil.copyfile(cand, keep)
        print("\nERGEBNIS UNTERSCHIEDLICH ab Byte %d - nichts ersetzt." % pos)
        print("  alt: %r\n  neu: %r" % (ctx_a, ctx_b))
        print("Kandidat liegt zur Ansicht unter %s" % keep)
        sys.exit(1)

    os.makedirs("backup", exist_ok=True)
    bak = os.path.join("backup", "%s.%s" % (os.path.basename(logic), time.strftime("%Y%m%d-%H%M%S")))
    n = 1
    while os.path.exists(bak):  # never overwrite an existing backup
        bak = bak.rsplit(".~", 1)[0] + ".~%d" % n
        n += 1
    shutil.copyfile(logic, bak)
    shutil.copyfile(cand, logic)
    shutil.rmtree(tmp, ignore_errors=True)

    print("\nBauergebnis byteidentisch. Logikdatei ersetzt, Original in %s" % bak)
    print("Neue Groesse: %.0f KB" % (os.path.getsize(logic) / 1024))

    left = leftover_data_uris(stripped)
    total = sum(s for _, s in left.values())
    if left:
        print("\nNoch eingebettete Bilder ausserhalb der Packerbloecke:")
        for key, (n, s) in sorted(left.items(), key=lambda kv: -kv[1][1]):
            print("  %-20s %3d Stueck %8.1f KB" % (key, n, s / 1024))
    print("\nGITHUB: %s" % ("bereit zum Hochladen" if total < 200 * 1024
                            else "noch zu gross (%.0f KB Bilddaten) - erst klaeren" % (total / 1024)))


if __name__ == "__main__":
    main()
