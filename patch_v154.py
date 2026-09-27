#!/usr/bin/env python3
"""FS3 v154 - the oval FreeSpace warp is the normal one.

    Ships now always come out of a side-on, oval vortex nose first and
    jump out into one, without anything in the address. For comparing,
    ?warp=rund still gives the round vortex and ?warp=alt the old fade in
    at the centre. Ships going through the Knossos keep their own look.

Needs v153. Edits src/20_render.js in place. Run assemble.py afterwards.
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
    "// ?warp=oval or ?warp=rund: ships come out of the vortex as in FreeSpace.\n"
    "const WARP_STYLE = (/[?&]warp=(oval|rund)/.exec(location.search) || [])[1] || '';\n",
    "// Ships come out of the vortex as in FreeSpace, through a side-on oval.\n"
    "// ?warp=rund: the same with a round vortex; ?warp=alt: the old fade in\n"
    "// at the centre of the vortex.\n"
    "const WARP_STYLE = (function(){\n"
    "  const m = /[?&]warp=(oval|rund|alt)/.exec(location.search);\n"
    "  if(!m) return 'oval';\n"
    "  return m[1]==='alt' ? '' : m[1];\n"
    "})();\n",
    "default oval")
open("src/20_render.js", "w", encoding="utf-8").write(rd)
