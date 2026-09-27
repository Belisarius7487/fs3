#!/usr/bin/env python3
"""FS3 v150 - FreeSpace warp: big ships come out nose first.

    The nose direction of a ship during the jump was worked out as if
    every picture faced right. Some hulls are drawn facing left (the NTF
    cruisers and destroyers, among them all of M52), and those came out
    of the vortex backwards, stern first, and then flew off forwards.
    The direction now also asks which way the picture faces.

Needs v149. Edits src/20_render.js in place. Run assemble.py afterwards.
"""
import sys


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


rd = open("src/20_render.js", encoding="utf-8").read()
rd = replace_once(
    rd,
    "  // Nose direction: sprites face right, turned by ang, then mirrored.\n"
    "  const s = e.flip ? -1 : 1, a = e.ang||0;\n",
    "  // Nose direction: the way the picture faces, turned by ang, then\n"
    "  // mirrored. Most pictures face right, some big hulls face left.\n"
    "  const s = (e.flip ? -1 : 1) * (spriteFacing(e.img)==='left' ? -1 : 1), a = e.ang||0;\n",
    "facing")
open("src/20_render.js", "w", encoding="utf-8").write(rd)
