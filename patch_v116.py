#!/usr/bin/env python3
"""FS3 v116 - three faults in the ramming, all with the same shape: something
was measured or set in the wrong place.

1. A bomber flew over its target and nothing happened. The contact test
   measured centre to centre against RAM_DIST, 26 points. A Hatshepsut is
   several hundred points wide, so the distance from a bomber sitting on her
   hull to her centre is never under 26. The test could not fire. Contact is
   now hull against hull, the same way tickCapRam already does it.

2. Every bomber of every faction rammed, and the double chevron showed over
   all of them. The rule was 'is a bomber'. It is now a doctrine: the Hammer
   of Light, plus whatever a mission hands out by name through rammer.
   NTF and Shivan bombers fly their run and pull away.

3. The ramming cruiser in 'Der Rammstoss' mostly missed and then hung on the
   left edge. applySpawnOpts gives a ram course the full height of the field
   and then, four lines later, still pins minY and maxY to the spawn height.
   still was applied last, so it won. The cruiser could only ever connect if
   it happened to spawn at the Hatshepsut's exact height. still now leaves a
   ram course alone, which is what the comment above it already claimed.
   And a ram course whose target is gone gives up its course instead of
   drifting into the edge forever.

Reads hlp_shooter_v115_logic.html, writes hlp_shooter_v116_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v115_logic.html", "hlp_shooter_v116_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# ── 1. Who rams, in one place ────────────────────────────────────────
src = replace_once(
    src,
    "const RAM_PCT_CAPITAL = 0.34;",
    "// Kamikaze is the Hammer of Light's doctrine and nobody else's. Under the\n"
    "// old rule every bomber on the field rammed, so once the cycle moved on the\n"
    "// NTF and the Shivans inherited a tactic that was never theirs. rammer is\n"
    "// the exception a mission hands out by name, for a wing briefed to do it.\n"
    "// Both the contact test and the double chevron over the ship read this, so\n"
    "// the warning and the behaviour cannot drift apart.\n"
    "function ramsOnContact(e){\n"
    "  return !!e.rammer || (e.type==='bomber' && e.faction==='hol');\n"
    "}\n"
    "const RAM_PCT_CAPITAL = 0.34;",
    "ramsOnContact",
)

src = replace_once(
    src,
    "const RAM_DIST = 26;         // ab hier gilt es als Treffer, nicht als Anflug",
    "// Wie tief die Rumpfe ineinander stehen muessen, damit es als Treffer gilt\n"
    "// und nicht als knapper Vorbeiflug.\n"
    "const RAM_OVERLAP = 6;",
    "RAM_OVERLAP",
)

src = replace_once(
    src,
    "    if(e.type!=='bomber' && !e.rammer) continue;  // Jaeger nur auf Ansage",
    "    if(!ramsOnContact(e)) continue;",
    "who rams",
)

src = replace_once(
    src,
    "    const d = Math.hypot(t.x-e.x, t.y-e.y);\n"
    "    if(d > RAM_DIST) continue;",
    "    // Gemessen wurde von Mitte zu Mitte. Ein Zerstoerer ist mehrere hundert\n"
    "    // Punkte breit, also war der Abstand eines Bombers auf seinem Rumpf zur\n"
    "    // Mitte des Schiffes nie unter 26 - der Bomber flog hinueber und nichts\n"
    "    // geschah. Beruehrung heisst Rumpf an Rumpf, waagerecht und senkrecht\n"
    "    // getrennt geprueft wie beim rammenden Grosskampfschiff.\n"
    "    if(Math.abs(t.x-e.x) > halfW(t)+halfW(e)-RAM_OVERLAP) continue;\n"
    "    if(Math.abs(t.y-e.y) > halfH(t)+halfH(e)-RAM_OVERLAP) continue;",
    "contact test",
)

src = replace_once(
    src,
    "  if((e.type==='bomber'||e.rammer) && e.role==='attack' && e.passT<=0){",
    "  if(ramsOnContact(e) && e.role==='attack' && e.passT<=0){",
    "marker rule",
)

# ── 2. still must not pin a ram course ───────────────────────────────
src = replace_once(
    src,
    "  // Kein Auf und Ab: ein Rammstoss auf ein schwebendes Ziel ist Zufall.\n"
    "  if(sp.still){ e.vy = 0; e.minY = e.y; e.maxY = e.y; }",
    "  // Kein Auf und Ab: ein Rammstoss auf ein schwebendes Ziel ist Zufall.\n"
    "  // still gilt dem Ziel, nicht dem Angreifer - und stand bisher unter der\n"
    "  // capRam-Zeile, hat ihr also die volle Hoehe wieder weggenommen. Ein\n"
    "  // Rammkurs traf dadurch nur, wenn er zufaellig auf der Hoehe seines\n"
    "  // Zieles erschien, und zog sonst am Ziel vorbei bis an den linken Rand.\n"
    "  if(sp.still){\n"
    "    e.vy = 0;\n"
    "    if(!e.capRam){ e.minY = e.y; e.maxY = e.y; }\n"
    "  }",
    "still vs capRam",
)

# ── 3. A ram course with nothing left to hit ─────────────────────────
src = replace_once(
    src,
    "    if(!t) continue;\n"
    "    // Direkter Kurs, ohne Halteposition - er will nicht schiessen.",
    "    // Ziel weg, waehrend er anflog: ohne Kurs und ohne Fluchterlaubnis\n"
    "    // haengt er sonst bis zum Wellenende am Rand. Er gibt den Rammkurs auf\n"
    "    // und verhaelt sich wieder wie ein gewoehnlicher Gegner.\n"
    "    if(!t){ e.capRam = 0; e.noFlee = false; continue; }\n"
    "    // Direkter Kurs, ohne Halteposition - er will nicht schiessen.",
    "ram course lost target",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
