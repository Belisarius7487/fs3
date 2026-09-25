#!/usr/bin/env python3
"""FS3 v127 - the mouse pointer exists again over the top bar.

The pointer was hidden over the whole canvas while playing:

    .nocursor canvas{cursor:none}

That is right over the field, where the ship IS the pointer, and wrong over
the bar, where there are four buttons to hit. On a PC you were clicking
blind.

The pointer now shows whenever it is over the bar and hides again when it
goes back to the field. The mousemove handler already told the two apart -
it returns early for the bar so a click there does not steer the ship - so
the switch sits on a branch that was already there.

And the buttons answer to being pointed at. A visible pointer tells you where
you are; a button that lights up tells you that you have it. The rectangles
were already being reported, so this is a lookup, not a new mechanism.

Touch is untouched: there is no pointer to show and nothing hovers.

FIRST PATCH AGAINST THE SPLIT SOURCE. It edits src/70_ui.js in place rather
than writing a new logic file. Run assemble.py afterwards.
"""
import sys

PART = "src/70_ui.js"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(PART, encoding="utf-8").read()

# ── 1. Where the pointer is, and whether it should be seen ───────────
src = replace_once(
    src,
    "// ── CALL MENU ──────────────────────────────────────────────────",
    "// Where the mouse is sitting, in game coordinates, whether or not it is\n"
    "// allowed to steer. MOUSE deliberately stops updating over the bar so the\n"
    "// ship does not follow a hand reaching for a button; this one keeps\n"
    "// looking, because the bar needs to know what is being pointed at.\n"
    "// Off the canvas entirely it goes to -1, which is inside nothing.\n"
    "const HOVER = {x:-1, y:-1};\n"
    "function hovering(x, y, w, h){\n"
    "  return HOVER.x>=x && HOVER.x<=x+w && HOVER.y>=y && HOVER.y<=y+h;\n"
    "}\n"
    "// The pointer belongs over the bar and not over the field, where the ship\n"
    "// is the pointer. It also stays visible whenever the game is not running:\n"
    "// a panel, a held pause, a manual one, the title, the end of a run.\n"
    "function syncCursor(){\n"
    "  const hide = GS==='playing' && !paused && !panelOpen() && HOVER.y>=HUD_H;\n"
    "  if(hide) document.body.classList.add('nocursor');\n"
    "  else     document.body.classList.remove('nocursor');\n"
    "}\n"
    "// ── CALL MENU ──────────────────────────────────────────────────",
    "hover state",
)

src = replace_once(
    src,
    "CVS.addEventListener('mousemove',function(ev){\n"
    "  var p=toGC(ev.clientX,ev.clientY);\n"
    "  // touchmove hatte diesen Schutz, mousemove nicht.\n"
    "  if(p.y<HUD_H&&GS==='playing') return;   // Leiste: keine Steuereingabe\n"
    "  MOUSE.x=p.x; MOUSE.y=p.y;\n"
    "});",
    "CVS.addEventListener('mousemove',function(ev){\n"
    "  var p=toGC(ev.clientX,ev.clientY);\n"
    "  // The bar always knows where the pointer is, even where the ship may not\n"
    "  // follow it.\n"
    "  HOVER.x=p.x; HOVER.y=p.y;\n"
    "  syncCursor();\n"
    "  // touchmove hatte diesen Schutz, mousemove nicht.\n"
    "  if(p.y<HUD_H&&GS==='playing') return;   // Leiste: keine Steuereingabe\n"
    "  MOUSE.x=p.x; MOUSE.y=p.y;\n"
    "});\n"
    "// Off the canvas: nothing is hovered, and the pointer is the browser's\n"
    "// business again.\n"
    "CVS.addEventListener('mouseleave',function(){\n"
    "  HOVER.x=-1; HOVER.y=-1;\n"
    "  document.body.classList.remove('nocursor');\n"
    "});",
    "mousemove",
)

# ── 2. The buttons answer to being pointed at ────────────────────────
src = replace_once(
    src,
    "    var swOn=shipSwapReady()||shipMenu;\n"
    "    thButton(swX, swY, swW, swH, shipMenu?'on':(swOn?'ready':null));\n"
    "    drawSwapIcon(swX+swW/2, swY+swH/2, swOn?TH('accentWarm'):TH('textDim'));\n"
    "    window._shipBtnRect={x:swX, y:swY, w:swW, h:swH};\n"
    "    var rmOn=rearmReady()||rearmMenu;\n"
    "    thButton(rmX, swY, swW, swH, rearmMenu?'on':(rmOn?'ready':null));\n"
    "    drawRearmIcon(rmX+swW/2, swY+swH/2, rmOn?TH('accentWarm'):TH('textDim'));\n"
    "    window._rearmBtnRect={x:rmX, y:swY, w:swW, h:swH};",
    "    var swOn=shipSwapReady()||shipMenu;\n"
    "    var swHv=hovering(swX, swY, swW, swH);\n"
    "    thButton(swX, swY, swW, swH, (shipMenu||swHv)?'on':(swOn?'ready':null));\n"
    "    drawSwapIcon(swX+swW/2, swY+swH/2,\n"
    "                 swOn?TH('accentWarm'):(swHv?TH('text'):TH('textDim')));\n"
    "    window._shipBtnRect={x:swX, y:swY, w:swW, h:swH};\n"
    "    var rmOn=rearmReady()||rearmMenu;\n"
    "    var rmHv=hovering(rmX, swY, swW, swH);\n"
    "    thButton(rmX, swY, swW, swH, (rearmMenu||rmHv)?'on':(rmOn?'ready':null));\n"
    "    drawRearmIcon(rmX+swW/2, swY+swH/2,\n"
    "                  rmOn?TH('accentWarm'):(rmHv?TH('text'):TH('textDim')));\n"
    "    window._rearmBtnRect={x:rmX, y:swY, w:swW, h:swH};",
    "swap and rearm hover",
)

src = replace_once(
    src,
    "  thButton(stbX, stbY, stbW, stbH, settingsOpen?'on':null);\n"
    "  drawGear(stbX+stbW/2, stbY+stbH/2, 7, settingsOpen?TH('textBright'):TH('text'));",
    "  var stbHv=hovering(stbX, stbY, stbW, stbH);\n"
    "  thButton(stbX, stbY, stbW, stbH, (settingsOpen||stbHv)?'on':null);\n"
    "  drawGear(stbX+stbW/2, stbY+stbH/2, 7,\n"
    "           (settingsOpen||stbHv)?TH('textBright'):TH('text'));",
    "gear hover",
)

src = replace_once(
    src,
    "  thButton(pbX, pbY, pbW, pbH, paused?'on':null);\n"
    "  drawPauseIcon(pbX+pbW/2, pbY+pbH/2, paused?TH('textBright'):TH('text'), !paused);",
    "  var pbHv=hovering(pbX, pbY, pbW, pbH);\n"
    "  thButton(pbX, pbY, pbW, pbH, (paused||pbHv)?'on':null);\n"
    "  drawPauseIcon(pbX+pbW/2, pbY+pbH/2,\n"
    "                (paused||pbHv)?TH('textBright'):TH('text'), !paused);",
    "pause hover",
)

# ── 3. Panels and pauses go through one place now ────────────────────
# Every panel used to add and remove the class itself. With the pointer also
# depending on where it is sitting, that is two opinions about one thing.
src = src.replace(
    "  if(open){\n"
    "    document.body.classList.remove('nocursor');\n"
    "  } else if(GS==='playing'){\n"
    "    MOUSE.x = player.x; MOUSE.y = player.y;\n"
    "    document.body.classList.add('nocursor');\n"
    "  }",
    "  if(!open && GS==='playing'){ MOUSE.x = player.x; MOUSE.y = player.y; }\n"
    "  syncCursor();")

src = replace_once(
    src,
    "  if(open){\n"
    "    document.body.classList.remove('nocursor');\n"
    "  } else {\n"
    "    if(GS==='playing'){\n"
    "      MOUSE.x = player.x; MOUSE.y = player.y;\n"
    "      document.body.classList.add('nocursor');\n"
    "    }\n"
    "  }",
    "  if(!open && GS==='playing'){ MOUSE.x = player.x; MOUSE.y = player.y; }\n"
    "  syncCursor();",
    "call menu cursor",
)

open(PART, "w", encoding="utf-8").write(src)
print("%s geaendert (%d KB)." % (PART, len(src.encode("utf-8"))//1024))

# ── 4. And the one that sits elsewhere ───────────────────────────────
# syncPause() and clearResumeHold() live in src/20_render.js, because that is
# where they happened to stand when the file was cut into contiguous pieces.
# The cut could not move them without giving up the byte for byte proof. Worth
# tidying later; for now the patch simply goes where the code is.
OTHER = "src/20_render.js"
other = open(OTHER, encoding="utf-8").read()
other = replace_once(
    other,
    "  resumeHold = false;\n"
    "  syncPause();\n"
    "  if(GS==='playing'){\n"
    "    MOUSE.x = player.x; MOUSE.y = player.y;\n"
    "    document.body.classList.add('nocursor');\n"
    "  }\n"
    "  return true;",
    "  resumeHold = false;\n"
    "  syncPause();\n"
    "  if(GS==='playing'){ MOUSE.x = player.x; MOUSE.y = player.y; }\n"
    "  syncCursor();\n"
    "  return true;",
    "resume cursor",
)
open(OTHER, "w", encoding="utf-8").write(other)
print("%s geaendert (%d KB)." % (OTHER, len(other.encode("utf-8"))//1024))
print("Jetzt: python3 assemble.py 127")
