#!/usr/bin/env python3
"""FS3 v125 - every panel behaves the same, and the title screen is rebuilt.

1. The rearm panel did not pause the game. The cause is worth naming, because
   it is the kind that comes back: syncPause() listed the panels one by one.

       paused = !!(shipMenu || callMenu || settingsOpen || userPaused);

   A new panel had to be added to that line by hand, and I did not. It now
   asks whether ANY panel is open, off a list the panels themselves are in,
   so the next one cannot be forgotten.

2. Closing a panel no longer drops you straight back into the fight. Whatever
   the panel and however it was closed - a choice, ESC, a tap outside - the
   game stays paused until one further tap. Six panels behaving six ways is
   only confusing.

3. Try Again goes back to the title screen rather than straight into the next
   run.

4. The title screen. It was drawing the nebula and the drifting bodies all
   along and then painting a 78 percent black sheet over them, which is why it
   looked like one flat image dropped in behind a logo. The sheet goes, the
   backdrop is rolled fresh every time the title appears, bodies drift across
   it and a body that leaves is replaced by a new one rather than wrapping
   round, so a long wait keeps producing new sky. The logo and its pasted-on
   3 give way to set type.

5. Weapon numbers, from playing it: the Streuschuss reaches twice as far and
   all three of the new guns hit considerably harder. The Stiletto is quicker
   off the rail.

Reads hlp_shooter_v124_logic.html, writes hlp_shooter_v125_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v124_logic.html", "hlp_shooter_v125_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def cut_between(text, start, end, new, label):
    if text.count(start) != 1:
        sys.exit("Abbruch (%s): Startmarke %d-mal gefunden, erwartet einmal." % (label, text.count(start)))
    if text.count(end) != 1:
        sys.exit("Abbruch (%s): Endmarke %d-mal gefunden, erwartet einmal." % (label, text.count(end)))
    i, j = text.index(start), text.index(end)
    if j <= i:
        sys.exit("Abbruch (%s): Endmarke steht vor der Startmarke." % label)
    return text[:i] + new + text[j:]


src = open(SRC, encoding="utf-8").read()

# ── 1. One question instead of a list to keep up to date ─────────────
src = replace_once(
    src,
    "function syncPause(){\n"
    "  paused = !!(shipMenu || callMenu || settingsOpen || userPaused);\n"
    "}",
    "// Every panel that covers the field, by name. A panel adds itself here and\n"
    "// nowhere else.\n"
    "//\n"
    "// This used to be one line that named the panels one by one, and a new\n"
    "// panel had to be written into it by hand. The rearm panel was not, so it\n"
    "// opened over a game that carried on running underneath it. Asking whether\n"
    "// ANY of them is open cannot be forgotten in the same way.\n"
    "function panelOpen(){\n"
    "  return !!(shipMenu || callMenu || rearmMenu || settingsOpen);\n"
    "}\n"
    "// After a panel closes the game stays stopped until one more tap. However\n"
    "// the panel was left - a choice made, ESC, a tap outside - the return to\n"
    "// the fight is the player's to time, not the panel's.\n"
    "let resumeHold = false;\n"
    "function syncPause(){\n"
    "  paused = !!(panelOpen() || resumeHold || userPaused);\n"
    "}\n"
    "// Called by every panel as it closes.\n"
    "function holdResume(){\n"
    "  if(GS==='playing') resumeHold = true;\n"
    "  syncPause();\n"
    "}\n"
    "// Any tap or key lifts it, and that input does nothing else.\n"
    "function clearResumeHold(){\n"
    "  if(!resumeHold) return false;\n"
    "  resumeHold = false;\n"
    "  syncPause();\n"
    "  if(GS==='playing'){\n"
    "    MOUSE.x = player.x; MOUSE.y = player.y;\n"
    "    document.body.classList.add('nocursor');\n"
    "  }\n"
    "  return true;\n"
    "}",
    "syncPause",
)

# Each panel holds the pause as it closes.
for name, label in [("setShipMenu", "ship hold"),
                    ("setCallMenu", "call hold"),
                    ("setRearmMenu", "rearm hold")]:
    src = replace_once(
        src,
        "function "+name+"(open){",
        "function "+name+"(open){\n"
        "  if(!open && "+("shipMenu" if name=="setShipMenu" else
                          "callMenu" if name=="setCallMenu" else "rearmMenu")+") holdResume();",
        label,
    )

# ── 2. The tap that lifts the hold does nothing else ─────────────────
src = replace_once(
    src,
    "function pointerConsumed(p){",
    "function pointerConsumed(p){\n"
    "  // The tap that puts you back in the fight is spent on that and nothing\n"
    "  // else - it must not also fire, steer or open a panel.\n"
    "  if(clearResumeHold()) return true;",
    "pointer hold",
)

src = replace_once(
    src,
    "  if(ev.code==='KeyV'){ toggleShipMenu(); ev.preventDefault(); return; }",
    "  if(resumeHold){ clearResumeHold(); ev.preventDefault(); return; }\n"
    "  if(ev.code==='KeyV'){ toggleShipMenu(); ev.preventDefault(); return; }",
    "key hold",
)

# The hint, so a stopped field does not read as a frozen one.
src = replace_once(
    src,
    "  try{drawRearmMenu();}catch(e){}",
    "  try{drawRearmMenu();}catch(e){}\n"
    "  try{drawResumeHint();}catch(e){}",
    "hint draw",
)

src = replace_once(
    src,
    "// ── REARM PANEL ──────────────────────────────────────────────",
    "// A stopped field with nothing on it looks broken, so it says what it is\n"
    "// waiting for. Quiet, and it pulses rather than blinks, because it is not\n"
    "// urgent - the fight is not going anywhere.\n"
    "function drawResumeHint(){\n"
    "  if(!resumeHold || GS!=='playing' || panelOpen()) return;\n"
    "  const k = 0.55 + 0.45*Math.sin(fc*0.06);\n"
    "  ctx.save();\n"
    "  ctx.textAlign='center'; ctx.textBaseline='middle';\n"
    "  ctx.globalAlpha = k;\n"
    "  ctx.fillStyle = TH('textBright'); ctx.font = thLabel(12);\n"
    "  ctx.fillText('TAP OR PRESS ANY KEY TO RESUME', W/2, H-40);\n"
    "  ctx.restore();\n"
    "  ctx.textAlign='left'; ctx.textBaseline='top';\n"
    "}\n"
    "// ── REARM PANEL ──────────────────────────────────────────────",
    "resume hint",
)

# Starting or restarting a run must not begin held.
src = replace_once(
    src,
    "  bossAlive=false;bossSlain=false;shakeT=0;shakeMag=0;campReset();rollBodies();nextWave();GS='playing';",
    "  resumeHold=false;\n"
    "  bossAlive=false;bossSlain=false;shakeT=0;shakeMag=0;campReset();rollBodies();nextWave();GS='playing';",
    "launch hold",
)

# ── 3. Try Again goes back to the title ──────────────────────────────
for old, label in [
    ("    if(GS==='title'||GS==='gameover'){ if(GS==='title'||performance.now()-gameOverAt>1500) launchGame(); }",
     "over to title 1"),
    ("  if(GS==='title'||GS==='gameover'){ if(GS==='title'||performance.now()-gameOverAt>1500) launchGame(); }",
     "over to title 2")]:
    src = replace_once(
        src, old,
        old.replace("launchGame(); }", "toTitleOrLaunch(); }"),
        label,
    )

src = replace_once(
    src,
    "  if((GS==='title'||GS==='gameover')&&(ev.code==='Space'||ev.code==='Enter')){ if(GS==='title'||performance.now()-gameOverAt>1500) launchGame(); }",
    "  if((GS==='title'||GS==='gameover')&&(ev.code==='Space'||ev.code==='Enter')){ if(GS==='title'||performance.now()-gameOverAt>1500) toTitleOrLaunch(); }",
    "over to title 3",
)

src = replace_once(
    src,
    "function drawTitle(){",
    "// From the title a run starts; from a finished run you go back to the\n"
    "// title first. Reading your score and then being dropped into the next\n"
    "// wave in the same breath left no moment to stop.\n"
    "function toTitleOrLaunch(){\n"
    "  if(GS==='gameover'){ enterTitle(); return; }\n"
    "  launchGame();\n"
    "}\n"
    "// A fresh sky every time the title comes up: another backdrop, another\n"
    "// set of bodies.\n"
    "function enterTitle(){\n"
    "  GS='title';\n"
    "  resumeHold=false; userPaused=false; paused=false;\n"
    "  nebCur = NEB_NAMES[(Math.random()*NEB_NAMES.length)|0];\n"
    "  nebFading = false; nebAlpha = 1.0;\n"
    "  rollBodies();\n"
    "}\n"
    "function drawTitle(){",
    "enterTitle",
)

# The title has to keep moving, and the body that leaves is replaced.
src = replace_once(
    src,
    "function update(){\n"
    "  if(paused) return;                  // covers the settings panel too\n"
    "  fc++;tickStars();tickParts();tickNebula();",
    "function update(){\n"
    "  // The title screen is not a still picture: the stars and the bodies keep\n"
    "  // moving there, so that much of the update runs before anything else.\n"
    "  if(GS==='title'){ fc++; tickStars(); tickNebula(); return; }\n"
    "  if(paused) return;                  // covers the settings panel too\n"
    "  fc++;tickStars();tickParts();tickNebula();",
    "title tick",
)

src = replace_once(
    src,
    "function tickBodies(){\n"
    "  for(const b of bodies){\n"
    "    b.x -= b.spd;\n"
    "    if(b.x + b.w < -40) b.x = W + b.w*0.5 + Math.random()*200;\n"
    "  }\n"
    "}",
    "function tickBodies(){\n"
    "  for(const b of bodies){\n"
    "    b.x -= b.spd;\n"
    "    if(b.x + b.w < -40){\n"
    "      // In a wave the set is fixed and a body that leaves comes back round.\n"
    "      // On the title there is no wave to end, so the same two planets would\n"
    "      // circle for as long as anyone waits. There they are rolled anew.\n"
    "      if(GS==='title'){ rollBodies(); return; }\n"
    "      b.x = W + b.w*0.5 + Math.random()*200;\n"
    "    }\n"
    "  }\n"
    "}",
    "title bodies",
)

# ── 4. The title screen itself ───────────────────────────────────────
NEW_TITLE = r"""function drawTitle(){
  // The backdrop and the bodies are already on the canvas by the time this
  // runs. What used to happen here was a 78 percent black sheet over the lot,
  // which is why a whole sky looked like one flat picture. What is left is a
  // gradient that darkens the lower half just enough to read type over.
  const veil = ctx.createLinearGradient(0, 0, 0, H);
  veil.addColorStop(0.00, 'rgba(0,0,8,0.20)');
  veil.addColorStop(0.45, 'rgba(0,0,8,0.42)');
  veil.addColorStop(1.00, 'rgba(0,0,8,0.78)');
  ctx.fillStyle = veil; ctx.fillRect(0, 0, W, H);

  ctx.textAlign='center';

  // The title, set rather than pasted. FREESPACE in the forum's own face,
  // widely tracked; the 3 in the accent, on the same line and on the same
  // baseline instead of leaning against it.
  const ty = 128;
  const main = 'FREESPACE';
  ctx.textBaseline='alphabetic';
  ctx.font = thLabel(54);
  // Canvas has no tracking, so the letters are set one at a time. At this
  // size the air between them is most of the effect.
  const track = 10;
  let wMain = 0;
  for(const ch of main) wMain += ctx.measureText(ch).width + track;
  wMain -= track;
  ctx.font = thLabel(54);
  const w3 = ctx.measureText('3').width;
  const gap = 18;
  let cx = (W - (wMain + gap + w3))/2;

  ctx.save();
  ctx.shadowColor = 'rgba('+TH('glow')+',0.55)';
  ctx.shadowBlur = 26;
  ctx.textAlign='left';
  ctx.fillStyle = TH('textBright');
  ctx.font = thLabel(54);
  for(const ch of main){
    ctx.fillText(ch, cx, ty);
    cx += ctx.measureText(ch).width + track;
  }
  cx += gap - track;
  ctx.fillStyle = TH('accentWarm');
  ctx.fillText('3', cx, ty);
  ctx.restore();

  // One rule under the title, in the kit's two weights, stopping short on the
  // right the way every panel header does.
  const rw = wMain + gap + w3;
  const rx = (W - rw)/2;
  ctx.lineWidth = 2; ctx.strokeStyle = TH('accentWarm');
  ctx.beginPath(); ctx.moveTo(rx, ty+16); ctx.lineTo(rx+rw*0.34, ty+16); ctx.stroke();
  ctx.lineWidth = 1; ctx.strokeStyle = TH('edgeLight');
  ctx.beginPath(); ctx.moveTo(rx+rw*0.34+10, ty+16.5); ctx.lineTo(rx+rw, ty+16.5); ctx.stroke();

  ctx.textAlign='center'; ctx.textBaseline='top';
  ctx.fillStyle = TH('textDim'); ctx.font = thValue(12, false);
  ctx.fillText('A Hard Light Productions Mini-Game', W/2, ty+30);

  // The controls, as a block of its own on a plate, so they read as reference
  // rather than as more title.
  const bw = 420, bh = 72, bx = (W-bw)/2, by = H-152;
  thPlate(bx, by, bw, bh, thRGBA('panelBack', 0.72));
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillStyle = TH('text'); ctx.font = thValue(12, false);
  ctx.fillText('Move the mouse to steer   -   hold to fire', W/2, by+24);
  ctx.fillStyle = TH('textDim'); ctx.font = thValue(11, false);
  ctx.fillText('Right click for the secondary   -   on touch, the SEC button', W/2, by+46);

  // The one thing to do. It pulses rather than blinks: a blink says hurry.
  const k = 0.55 + 0.45*Math.sin(fc*0.05);
  ctx.save();
  ctx.globalAlpha = k;
  ctx.fillStyle = TH('textBright'); ctx.font = thLabel(13);
  ctx.fillText('PRESS SPACE OR ENTER', W/2, H-52);
  ctx.restore();

  ctx.textAlign='left'; ctx.textBaseline='top';
}
"""

src = cut_between(src, "function drawTitle(){", "\n\n// Shown at the end as well", NEW_TITLE, "drawTitle")

# ── 5. Numbers, from playing it ──────────────────────────────────────
src = replace_once(
    src,
    "   dmg:1.55, rate:1.85, spd:8, range:150, pellets:7, spread:0.30,",
    "   dmg:2.60, rate:1.85, spd:8, range:300, pellets:7, spread:0.30,",
    "scatter numbers",
)

src = replace_once(
    src,
    "   dmg:0.55, rate:1.40, spd:7.5, range:420, fuse:300,\n"
    "   shards:9, shardDmg:0.20, shardSpd:3.4, shardRange:70,",
    "   dmg:1.10, rate:1.40, spd:7.5, range:420, fuse:300,\n"
    "   shards:9, shardDmg:0.38, shardSpd:3.4, shardRange:70,",
    "dante numbers",
)

src = replace_once(
    src,
    "   ammoMul:0.7, dmg:18, cd:55, spd:4.2, life:200, homing:false,\n"
    "   burst:true, shards:12, shardDmg:14, shardSpd:3.0, shardRange:90,",
    "   ammoMul:0.7, dmg:40, cd:55, spd:4.2, life:200, homing:false,\n"
    "   burst:true, shards:12, shardDmg:30, shardSpd:3.0, shardRange:90,",
    "infyrno numbers",
)

src = replace_once(
    src,
    "   ammoMul:1.0, dmg:70, cd:95, spd:1.9, life:300, homing:true, subs:true,",
    "   ammoMul:1.0, dmg:70, cd:95, spd:2.8, life:300, homing:true, subs:true,",
    "stiletto speed",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
