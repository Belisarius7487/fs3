#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FS3  Packer-Patch fuer v82

Ersetzt die klassenweisen Deckel in build_game.py durch einen Deckel JE
SCHIFF, berechnet aus derselben Rumpflaengentabelle, die das Spiel seit v81
benutzt.

Warum:
  Die Deckel in SPRITE_PX waren klassenweise geschaetzt. Seit v81 steht die
  tatsaechliche Darstellungsbreite jedes Rumpfs auf den Bildpunkt fest, und
  die Schaetzungen liegen in beide Richtungen daneben:

    te-co-deimos      Deckel 448, gebraucht 584   -> 1,31fach hochskaliert
    sh-co-moloch      Deckel 448, gebraucht 588   -> 1,31fach
    ntf-co-iceni      Deckel 448, gebraucht 723   -> 1,61fach
    te-sd-colossus    Deckel 1152, gebraucht 1668 -> 1,45fach
    sh-in-commnode    Deckel 1152, gebraucht 600  -> Ergebnis groesser als
                                                     die Quelle (528->544 KB)
    te-tr-elysium     Deckel 448, gebraucht 180   -> 484 KB fuer ein Sprite
                                                     in Jaegergroesse

  Beides verschwindet, wenn der Deckel die Breite des Schiffes mal MAX_RES
  ist.

Aufruf:  python3 patch_packer_v82.py
Legt vorher build_game.py.vor-v82 als Sicherung an.
"""

import io, os, shutil, sys

SRC = "build_game.py"
BAK = "build_game.py.vor-v82"

OLD_TABLE_HEAD = '''# Hoechstbreite je Klasse. Massgeblich ist, wie gross das Schiff im Spiel
# tatsaechlich gezogen wird, mal MAX_RES 3:'''

NEW_HEAD = '''# ── HOECHSTBREITE JE SCHIFF ──────────────────────────────────
# Bis v82 stand hier ein Deckel je KLASSE, geschaetzt aus der ungefaehren
# Darstellungsgroesse. Seit v81 rechnet das Spiel die Breite jedes Rumpfs
# aus seiner kanonischen Laenge aus, also kann der Packer denselben Wert
# benutzen statt ihn zu raten.
#
# ACHTUNG, ZWEITE KOPIE EINER KURVE: die folgenden fuenf Konstanten muessen
# mit hullWidth() in der Spieldatei uebereinstimmen. Laufen sie
# auseinander, werden Sprites still weich oder still zu gross. Der Packer
# gibt den angewandten Deckel deshalb mit aus.
#
# Die Klassentabelle bleibt als Rueckfall fuer alles, was keine Laenge hat.
HULL_LEN_FILE = "fs3_hull_lengths.json"
SIZE_K, SIZE_E = 2.880, 0.641
SIZE_MAX = 400
SIZE_REF_L, SIZE_REF_W = 20.0, 60.0      # Jaegerlaenge, Jaegerbreite
SIZE_FIXED = {"sdcolossus": 556}
SIZE_CLASS_FIXED = {"fi": 60, "bo": 65, "ep": 60}
MAX_RES = 3                              # Deckel der Zeichenflaeche im Spiel
SPRITE_PX_MIN = 128                      # nichts unter dieser Breite packen

_HULL_LEN = None
def hull_lengths():
    global _HULL_LEN
    if _HULL_LEN is None:
        try:
            with open(HULL_LEN_FILE, "r", encoding="utf-8") as fh:
                _HULL_LEN = json.load(fh)["len"]
        except Exception:
            _HULL_LEN = {}
    return _HULL_LEN

def hull_class(key):
    return key[3:5] if key.startswith("ntf") else key[:2]

def hull_width(key):
    """Muss exakt dasselbe liefern wie hullWidth() in der Spieldatei."""
    if key in SIZE_FIXED:
        return SIZE_FIXED[key]
    c = hull_class(key)
    if c in SIZE_CLASS_FIXED:
        return SIZE_CLASS_FIXED[c]
    L = hull_lengths().get(key)
    if not L:
        return None
    curve = SIZE_K * (L ** SIZE_E)
    floor = min(SIZE_REF_W, SIZE_REF_W * ((L / SIZE_REF_L) ** SIZE_E))
    return int(round(min(SIZE_MAX, max(floor, curve))))

def sprite_limit(key, cls):
    """Deckel fuer dieses eine Sprite. Faellt auf die Klassentabelle
    zurueck, wenn der Rumpf keine Laenge hat."""
    w = hull_width(key)
    if w is None:
        return SPRITE_PX.get(cls, SPRITE_PX_DEFAULT)
    return max(SPRITE_PX_MIN, w * MAX_RES)

# Rueckfalltabelle. Massgeblich ist, wie gross das Schiff im Spiel
# tatsaechlich gezogen wird, mal MAX_RES 3:'''

OLD_LIMIT = '''        cls = split_name(name)[1]
        limit = SPRITE_PX.get(cls, SPRITE_PX_DEFAULT)
        raw, did = shrink_png(raw, limit)'''

NEW_LIMIT = '''        cls = split_name(name)[1]
        limit = sprite_limit(key, cls)
        raw, did = shrink_png(raw, limit)'''


def main():
    if not os.path.exists(SRC):
        sys.exit("FEHLT: " + SRC)
    txt = io.open(SRC, "r", encoding="utf-8").read()

    for tag, old in (("kopf", OLD_TABLE_HEAD), ("deckel", OLD_LIMIT)):
        n = txt.count(old)
        if n != 1:
            sys.exit("ABBRUCH %s: %d Treffer statt 1" % (tag, n))

    if "import json" not in txt:
        sys.exit("ABBRUCH: json wird nicht importiert, Patch passt nicht")

    txt = txt.replace(OLD_TABLE_HEAD, NEW_HEAD, 1)
    print("  ok   kopf     (Deckel je Schiff eingesetzt)")
    txt = txt.replace(OLD_LIMIT, NEW_LIMIT, 1)
    print("  ok   deckel   (sprite_limit statt SPRITE_PX.get)")

    if not os.path.exists(BAK):
        shutil.copy2(SRC, BAK)
        print("  ok   Sicherung: " + BAK)

    io.open(SRC, "w", encoding="utf-8").write(txt)
    print("\ngeschrieben: %s" % SRC)


if __name__ == "__main__":
    main()
