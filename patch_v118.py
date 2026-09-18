#!/usr/bin/env python3
"""FS3 v118 - two corrections to the ramming.

1. The cruiser goes off too early. A hull box is a rectangle around a ship
   that is not rectangular, so the corners of two boxes meet well before the
   ships do. Touching is the wrong question for a ram: it has to be buried.
   hullsBite asks how deep the two boxes actually overlap and measures that
   against the attacker's own size, so the cruiser has to stand in the hull
   rather than brush past its edge.

2. A ram course broke off its own attack run. flySmall sets passT once it is
   within ATTACK_BREAK of its target and then flies straight through, which
   is right for a bomber that has dropped its load and wrong for one whose
   whole purpose is the impact. Both the contact test and the yellow double
   chevron require passT to be zero, so during the pass - exactly the moment
   it is over the hull - the marking disappeared and the impact could not be
   registered. A ram course now holds its aim all the way in.

Reads hlp_shooter_v117_logic.html, writes hlp_shooter_v118_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v117_logic.html", "hlp_shooter_v118_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# ── 1. Buried, not brushed ───────────────────────────────────────────
src = replace_once(
    src,
    "function hullsTouch(a, b, overlap){\n"
    "  const A = hullBox(a), B = hullBox(b);\n"
    "  return Math.abs(A.cx-B.cx) < A.hw+B.hw-overlap\n"
    "      && Math.abs(A.cy-B.cy) < A.hh+B.hh-overlap;\n"
    "}",
    "function hullsTouch(a, b, overlap){\n"
    "  const A = hullBox(a), B = hullBox(b);\n"
    "  return Math.abs(A.cx-B.cx) < A.hw+B.hw-overlap\n"
    "      && Math.abs(A.cy-B.cy) < A.hh+B.hh-overlap;\n"
    "}\n"
    "// Wie tief zwei Rumpfe ineinander stehen, in Punkten, je Achse. Negativ\n"
    "// heisst: sie stehen auseinander.\n"
    "function hullDepth(a, b){\n"
    "  const A = hullBox(a), B = hullBox(b);\n"
    "  return {x:A.hw+B.hw - Math.abs(A.cx-B.cx),\n"
    "          y:A.hh+B.hh - Math.abs(A.cy-B.cy),\n"
    "          hw:A.hw, hh:A.hh};\n"
    "}\n"
    "// Steckt a wirklich in b? Ein Rechteck um ein Schiff, das nicht\n"
    "// rechteckig ist, stoesst mit seinen Ecken zusammen, lange bevor die\n"
    "// Schiffe sich beruehren - fuer einen Rammstoss ist Beruehrung deshalb die\n"
    "// falsche Frage. Gemessen wird an der Groesse des Angreifers: share=1 heisst,\n"
    "// er muss um seine eigene halbe Laenge im Ziel stehen.\n"
    "function hullsBite(a, b, share){\n"
    "  const d = hullDepth(a, b);\n"
    "  return d.x > d.hw*share && d.y > d.hh*share;\n"
    "}",
    "hullsBite",
)

src = replace_once(
    src,
    "// Ein Grosskampfschiff muss tiefer stehen als ein Bomber, sonst zuendet es\n"
    "// schon, wenn sich die Bugspitzen streifen.\n"
    "const CAP_RAM_OVERLAP = 12;",
    "// Wie tief ein rammendes Grosskampfschiff im Ziel stehen muss, gemessen an\n"
    "// seiner eigenen halben Groesse. Eine Zahl zum Drehen: hoeher heisst, er\n"
    "// faehrt weiter hinein, bevor es ihn zerreisst.\n"
    "const CAP_RAM_BITE = 0.85;",
    "cap ram bite",
)

src = replace_once(
    src,
    "    if(hullsTouch(e, t, CAP_RAM_OVERLAP)){",
    "    if(hullsBite(e, t, CAP_RAM_BITE)){",
    "cap ram contact",
)

# ── 2. A ram course does not break off ───────────────────────────────
src = replace_once(
    src,
    "    } else if(d<ATTACK_BREAK){\n"
    "      e.passT=ATTACK_PASS;\n"
    "      wx=Math.cos(e.head); wy=Math.sin(e.head);",
    "    } else if(d<ATTACK_BREAK && !ramsOnContact(e)){\n"
    "      // Ein Rammkurs bricht nicht ab. Der Durchflug ist richtig fuer einen\n"
    "      // Bomber, der seine Last los ist, und falsch fuer einen, dessen\n"
    "      // ganzer Zweck der Aufprall ist: sowohl die Aufprallpruefung als auch\n"
    "      // der gelbe Doppelwinkel verlangen passT gleich null, also verschwand\n"
    "      // die Warnung genau in dem Augenblick, in dem er ueber dem Rumpf war.\n"
    "      e.passT=ATTACK_PASS;\n"
    "      wx=Math.cos(e.head); wy=Math.sin(e.head);",
    "no break off",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
