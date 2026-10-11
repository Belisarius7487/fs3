#!/usr/bin/env python3
"""FS3 - put the parts in src/ back together into one logic file.

  python3 assemble.py 127            ->  hlp_shooter_v127_logic.html
  python3 assemble.py 127 --verify   writes nothing, only says whether the
                                     file on disk is what src/ would make

--verify is what checks.sh asks before it runs a single stage: the commonest
way to check nothing at all is to change a part in src/ and then run the
stages against a logic file assembled before the change. Comparing the text
is exact, unlike comparing file times, which a fresh clone sets all at once.

The parts are joined in the order of their file names, which is what the
numeric prefixes are for. Nothing downstream changes: build.sh, build_game.py
and all eleven simulation stages still see one file with one script block.

Order matters and is the one thing that can go wrong here: a function
declaration may be used before the line it stands on, a top level const may
not. Everything in this game runs from inside functions called after load, so
in practice moving a part is safe - and loadtest.js exists precisely to say so
before a build goes out.
"""
import glob, os, sys


def parts():
    names = sorted(os.path.basename(p) for p in glob.glob("src/*"))
    head = [n for n in names if n.endswith("_head.html")]
    tail = [n for n in names if n.endswith("_tail.html")]
    body = [n for n in names if n.endswith(".js")]
    if len(head) != 1 or len(tail) != 1:
        sys.exit("Abbruch: src/ braucht genau eine head- und eine tail-Datei.")
    if not body:
        sys.exit("Abbruch: keine .js-Teile in src/ gefunden.")
    return head[0], body, tail[0]


def main():
    args = sys.argv[1:]
    verify = "--verify" in args
    args = [a for a in args if a != "--verify"]
    if len(args) != 1 or not args[0].isdigit():
        sys.exit("Aufruf: python3 assemble.py <Version> [--verify]   z.B. python3 assemble.py 127")
    ver = args[0]
    out = "hlp_shooter_v%s_logic.html" % ver

    head, body, tail = parts()
    chunks = [open("src/"+head, encoding="utf-8").read()]
    for n in body:
        chunks.append(open("src/"+n, encoding="utf-8").read())
    chunks.append(open("src/"+tail, encoding="utf-8").read())

    text = "\n".join(chunks)

    if verify:
        if not os.path.exists(out):
            sys.exit("Abbruch: %s fehlt. Erst zusammensetzen: python3 assemble.py %s" % (out, ver))
        if open(out, encoding="utf-8").read() != text:
            sys.exit("Abbruch: %s ist nicht das, was src/ ergibt.\n"
                     "         Erst zusammensetzen: python3 assemble.py %s" % (out, ver))
        print("%s stimmt mit src/ ueberein (%d Teile)." % (out, len(body)))
        return

    open(out, "w", encoding="utf-8").write(text)
    print("%s geschrieben (%d KB) aus %d Teilen:" % (out, len(text.encode("utf-8"))//1024, len(body)))
    for n in body:
        print("   " + n)


if __name__ == "__main__":
    main()
