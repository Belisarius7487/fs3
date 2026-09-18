#!/usr/bin/env python3
"""FS3 v117 - the ramming cruiser, properly this time.

v116 fixed the height band and the test still missed the real cause, because
ramsim only ever ran tickCapRam. In the game a cruiser is also moved by the
ordinary capital ship movement in tickEnemies, and that movement wins:

  - it slides the ship left at 0.8 points a step towards targetX, while the
    ram course can only steer 0.05 a step. So the cruiser crossed the field
    far faster than it could climb, and went past its target at an angle.
  - tickCapRam sets targetX to null to stop the ship holding station. But the
    movement then computes Math.max(null, e.x-0.8), and Math.max(null, ...)
    is Math.max(0, ...). That is the left edge, exactly where it hung.
  - the same branch keeps nudging vy, so the patrol drift fought the ram
    steering in the vertical as well.

A ram course now owns its movement: the station keeping and the patrol drift
are skipped while capRam is set, and capRam is the speed in points per step
rather than a nudge on top of somebody else's movement. Mission 28's value
moves from 0.05 to 0.9, which is what the cruiser was actually travelling at
before, once the drift is taken away.

Second fault, reported in the same breath: ships exploded without their
sprites touching. Both contact tests measured the image rectangle, and an
image carries a transparent margin around the ship inside it. The margins
collided. There is already a pixel mask for hit detection, built once per
sprite, so the visible bounds are read off that and the rectangle is fitted
to the ship instead of to the file.

Reads hlp_shooter_v116_logic.html, writes hlp_shooter_v117_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v116_logic.html", "hlp_shooter_v117_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# ── 1. The visible hull, not the image rectangle ─────────────────────
src = replace_once(
    src,
    "function halfH(o){",
    "// Der sichtbare Teil eines Sprites, ohne den durchsichtigen Rand um das\n"
    "// Schiff herum. Ein Bild ist immer groesser als das Schiff darin, und wer\n"
    "// gegen das Bild prueft, laesst durchsichtige Ecken zusammenstossen - dann\n"
    "// explodiert etwas, das sich auf dem Schirm sichtbar nicht beruehrt hat.\n"
    "// Gerechnet wird aus der Maske, die fuer die Trefferabfrage ohnehin gebaut\n"
    "// wird, und das Ergebnis wird gemerkt: einmal je Sprite, nicht je Schritt.\n"
    "const SPR_BOX = {};\n"
    "function spriteBox(key){\n"
    "  if(SPR_BOX[key] !== undefined) return SPR_BOX[key];\n"
    "  const img = IMGS[key];\n"
    "  if(!img || !img.width) return (SPR_BOX[key] = null);\n"
    "  // Faellt die Maske aus, gilt das ganze Bild - lieber zu grosszuegig als\n"
    "  // gar keine Pruefung.\n"
    "  let box = {cx:0, cy:0, hw:img.width*0.5, hh:img.height*0.5};\n"
    "  const m = getMask(key);\n"
    "  if(m){\n"
    "    let x0=m.w, y0=m.h, x1=-1, y1=-1;\n"
    "    for(let y=0;y<m.h;y++){\n"
    "      for(let x=0;x<m.w;x++){\n"
    "        if(!m.bits[y*m.w+x]) continue;\n"
    "        if(x<x0) x0=x;\n"
    "        if(x>x1) x1=x;\n"
    "        if(y<y0) y0=y;\n"
    "        if(y>y1) y1=y;\n"
    "      }\n"
    "    }\n"
    "    if(x1>=x0 && y1>=y0){\n"
    "      // Die Maske ist verkleinert, also zurueck auf Bildmass rechnen.\n"
    "      const fx = img.width/m.w, fy = img.height/m.h;\n"
    "      const bx0 = x0*fx, bx1 = (x1+1)*fx;\n"
    "      const by0 = y0*fy, by1 = (y1+1)*fy;\n"
    "      box = {cx:(bx0+bx1)/2 - img.width/2,\n"
    "             cy:(by0+by1)/2 - img.height/2,\n"
    "             hw:(bx1-bx0)/2, hh:(by1-by0)/2};\n"
    "    }\n"
    "  }\n"
    "  return (SPR_BOX[key] = box);\n"
    "}\n"
    "// Der sichtbare Rumpf eines Schiffs in Weltkoordinaten. Der Mittelpunkt des\n"
    "// Rumpfes ist nicht der Mittelpunkt des Bildes, deshalb wird er mitgefuehrt.\n"
    "function hullBox(o){\n"
    "  const b = spriteBox(o.img), sc = o.sc || 1;\n"
    "  if(!b) return {cx:o.x, cy:o.y, hw:40*sc, hh:20*sc};\n"
    "  const s = o.flip ? -1 : 1;\n"
    "  return {cx:o.x + b.cx*sc*s, cy:o.y + b.cy*sc, hw:b.hw*sc, hh:b.hh*sc};\n"
    "}\n"
    "// Beruehren sich zwei Rumpfe? Waagerecht und senkrecht getrennt geprueft:\n"
    "// ein Kreis laesst ein Schiff hoch ueber einem anderen explodieren, weil\n"
    "// der Abstand dort auch klein ist. overlap ist, wie tief sie ineinander\n"
    "// stehen muessen, damit es als Treffer gilt und nicht als Streifschuss.\n"
    "function hullsTouch(a, b, overlap){\n"
    "  const A = hullBox(a), B = hullBox(b);\n"
    "  return Math.abs(A.cx-B.cx) < A.hw+B.hw-overlap\n"
    "      && Math.abs(A.cy-B.cy) < A.hh+B.hh-overlap;\n"
    "}\n"
    "function halfH(o){",
    "hull box",
)

src = replace_once(
    src,
    "const RAM_OVERLAP = 6;",
    "const RAM_OVERLAP = 6;\n"
    "// Ein Grosskampfschiff muss tiefer stehen als ein Bomber, sonst zuendet es\n"
    "// schon, wenn sich die Bugspitzen streifen.\n"
    "const CAP_RAM_OVERLAP = 12;\n"
    "// Wie viel zuegiger ein Rammkurs steigt und sinkt als er vorwaerts faehrt.\n"
    "// Ohne das kriecht er die Hoehe hoch und ist laengst da, bevor er auf Hoehe\n"
    "// ist.\n"
    "const CAP_RAM_CLIMB = 3.4;",
    "cap ram constants",
)

src = replace_once(
    src,
    "    if(Math.abs(t.x-e.x) > halfW(t)+halfW(e)-RAM_OVERLAP) continue;\n"
    "    if(Math.abs(t.y-e.y) > halfH(t)+halfH(e)-RAM_OVERLAP) continue;",
    "    if(!hullsTouch(e, t, RAM_OVERLAP)) continue;",
    "bomber contact",
)

# ── 2. A ram course owns its movement ────────────────────────────────
src = replace_once(
    src,
    "    // Senkrecht zuegiger als waagerecht: sonst kriecht er die Hoehe hoch\n"
    "    // und ist laengst da, bevor er auf Hoehe ist.\n"
    "    e.x += dx/L*e.capRam;\n"
    "    e.y += dy/L*e.capRam*3.4;\n"
    "    const ei=IMGS[e.img], ti=IMGS[t.img];\n"
    "    const hwA=(ei?ei.width*e.sc:100)*0.5,  hwB=(ti?ti.width*t.sc:100)*0.5;\n"
    "    const hhA=(ei?ei.height*e.sc:40)*0.5,  hhB=(ti?ti.height*t.sc:40)*0.5;\n"
    "    // Waagerecht und senkrecht getrennt pruefen: ein Kreis laesst ihn\n"
    "    // hoch ueber dem Ziel explodieren, weil der Abstand dort auch klein ist.\n"
    "    if(Math.abs(dx) < (hwA+hwB)*0.62 && Math.abs(dy) < (hhA+hhB)*0.62){",
    "    // capRam ist die Fahrt selbst, nicht mehr ein Anstupser auf die Fahrt\n"
    "    // eines anderen: tickEnemies() laesst einen Rammkurs jetzt in Ruhe.\n"
    "    e.x += dx/L*e.capRam;\n"
    "    // Nie weiter als der Rest, sonst schwingt er ueber die Hoehe hinaus und\n"
    "    // pendelt daran vorbei.\n"
    "    const vy = dy/L*e.capRam*CAP_RAM_CLIMB;\n"
    "    e.y += (Math.abs(vy) > Math.abs(dy)) ? dy : vy;\n"
    "    if(hullsTouch(e, t, CAP_RAM_OVERLAP)){",
    "cap ram movement",
)

# The ordinary capital movement must not fight the ram course.
src = replace_once(
    src,
    "      if(runFlee(e,i)) continue;\n"
    "      // Zu Kampfposition gleiten\n"
    "      if(e.x>e.targetX) e.x=Math.max(e.targetX,e.x-0.8);\n"
    "      if(!subOK(e,'engines')) e.vy=0;\n"
    "      else e.vy=e.vy*0.985+(e.vy>0?1:-1)*0.015*0.6;\n"
    "      e.y+=e.vy;if(e.y<e.minY||e.y>e.maxY)e.vy*=-1;",
    "      if(runFlee(e,i)) continue;\n"
    "      // Ein Rammkurs steuert sich selbst, in tickCapRam(). Die Fahrt zur\n"
    "      // Kampfposition zog ihn unabhaengig davon 0.8 Punkte je Schritt nach\n"
    "      // links, also schneller, als der Rammkurs in der Hoehe nachkam - so\n"
    "      // zog er schraeg am Ziel vorbei. Und weil targetX dabei auf null\n"
    "      // steht und Math.max(null, x) dasselbe ist wie Math.max(0, x), endete\n"
    "      // die Fahrt bei x = 0: der linke Bildrand, an dem er hing.\n"
    "      if(!e.capRam){\n"
    "        // Zu Kampfposition gleiten\n"
    "        if(e.x>e.targetX) e.x=Math.max(e.targetX,e.x-0.8);\n"
    "        if(!subOK(e,'engines')) e.vy=0;\n"
    "        else e.vy=e.vy*0.985+(e.vy>0?1:-1)*0.015*0.6;\n"
    "        e.y+=e.vy;if(e.y<e.minY||e.y>e.maxY)e.vy*=-1;\n"
    "      }",
    "cruiser movement",
)

src = replace_once(
    src,
    "      if(runFlee(e,i)) continue;\n"
    "      if(e.x>e.targetX)e.x=Math.max(e.targetX,e.x-0.6);\n"
    "      if(!subOK(e,'engines')) e.vy=0;\n"
    "      e.y+=e.vy;if(e.y<e.minY||e.y>e.maxY)e.vy*=-1;",
    "      if(runFlee(e,i)) continue;\n"
    "      // Wie beim Kreuzer: ein Rammkurs faehrt seinen eigenen Kurs.\n"
    "      if(!e.capRam){\n"
    "        if(e.x>e.targetX)e.x=Math.max(e.targetX,e.x-0.6);\n"
    "        if(!subOK(e,'engines')) e.vy=0;\n"
    "        e.y+=e.vy;if(e.y<e.minY||e.y>e.maxY)e.vy*=-1;\n"
    "      }",
    "corvette movement",
)

# ── 3. The mission's number now means points per step ────────────────
src = replace_once(
    src,
    "{id:'V1', c:'cr', n:1, spr:'crmentu', capRam:0.05, still:true},",
    "{id:'V1', c:'cr', n:1, spr:'crmentu', capRam:0.9, still:true},",
    "mission 28 speed",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
