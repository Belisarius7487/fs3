#!/usr/bin/env python3
"""FS3 v128 - the Tornado swarm missile, and the Durchschlag is gone.

TORNADO
One press of the secondary button puts four small seeking missiles into the
air in a fan. Each of them goes for a DIFFERENT target: the nearest four that
can be locked, one each. With fewer targets than missiles they double up, so
a salvo is never wasted on empty space. A missile whose target dies on the
way picks the nearest target no sibling from its salvo is already flying at,
and only if there is none of those, the nearest one at all.

It is a fighter weapon (missile class) and opens at 22,000 points, the slot
the Durchschlag leaves free. One salvo costs one round from the rack; the
rack is half the MX-64's, so a full rack lands a little less than an MX-64
rack does in total - what it buys is spread, not weight.

Like every other seeker it goes dumb in a nebula and in an EMP storm: the
lock rule is canLockOn(), and the Tornado asks it like everything else.

DURCHSCHLAG
Removed on request. The table row goes, and so does the only mechanism that
served it: the pierce counter on player bolts and the hit list in the
collision loop. Nothing else fired piercing bolts. A ship that still had it
fitted falls back to the Prometheus through applyLoadout(), which already
handles an unknown key.

Edits src/50_combat.js, src/60_effects.js and src/70_ui.js in place.
Run assemble.py afterwards.
"""
import sys


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


def load(p):
    return open(p, encoding="utf-8").read()


# All three parts are read and patched first and written only at the end,
# so a search text that does not match leaves every file untouched.
ui = load("src/70_ui.js")
fx = load("src/60_effects.js")
cb = load("src/50_combat.js")

# ── 1. Durchschlag out of the table ───────────────────────────────────
ui = replace_once(
    ui,
    "  // pierce is how many hulls one bolt may take before it gives out. It\n"
    "  // never takes the same ship twice, so a big hull is one hit and not one\n"
    "  // per step of its length.\n"
    "  {key:'pierce', name:'Durchschlag', unlock:22000,\n"
    "   dmg:0.85, rate:1.55, spd:11, range:0, pierce:4,\n"
    "   col:'#e6b9ff', glow:'rgba(200,120,255,0.32)',\n"
    "   note:'takes everything on its line, once each'},\n",
    "",
    "table: Durchschlag")

# ── 2. Tornado into the table ─────────────────────────────────────────
ui = replace_once(
    ui,
    "  // subs: the warhead goes into the innards rather than the hull. A\n",
    "  // swarm: one press lets go this many small seekers in a fan of the\n"
    "  // given width (radians). dmg is per missile. Each one is handed a\n"
    "  // different target at launch, see swarmTargets(). One salvo is one\n"
    "  // round off the rack.\n"
    "  {key:'tornado', name:'Tornado', cls:'missile', unlock:22000,\n"
    "   ammoMul:0.5, dmg:14, cd:60, spd:3.2, life:210, homing:true,\n"
    "   swarm:4, fan:0.9,\n"
    "   note:'four seekers in a fan - each goes for a different target'},\n"
    "  // subs: the warhead goes into the innards rather than the hull. A\n",
    "table: Tornado")

# ── 3. The rearm panel shows a salvo as what it is ────────────────────
ui = replace_once(
    ui,
    "  if(k==='dmg')    return String(w.dmg);\n",
    "  if(k==='dmg')    return w.swarm ? (w.swarm+'\\u00d7'+w.dmg) : String(w.dmg);\n",
    "rearm: salvo damage")

# ── 4. Firing: a fan of seekers, each with its own target ─────────────
fx = replace_once(
    fx,
    "function fireSecondary(){\n",
    "// Who the missiles of one Tornado salvo go for: the nearest n targets that\n"
    "// can be locked, one each. With fewer targets than missiles they double\n"
    "// up from the nearest. Nothing lockable at all gives nulls, and the\n"
    "// missiles fly straight until something turns up.\n"
    "function swarmTargets(x, y, n){\n"
    "  const list = [];\n"
    "  for(const e of enemies){\n"
    "    if(e.dead || !canLockOn(e)) continue;\n"
    "    list.push({e:e, d:Math.hypot(e.x-x, e.y-y)});\n"
    "  }\n"
    "  list.sort(function(a,b){ return a.d-b.d; });\n"
    "  const out = [];\n"
    "  for(let k=0;k<n;k++) out.push(list.length ? list[k%list.length].e : null);\n"
    "  return out;\n"
    "}\n"
    "// A swarm missile whose target is gone looks again: first for the nearest\n"
    "// target none of its own salvo is flying at, then for the nearest at all.\n"
    "function swarmRetarget(b){\n"
    "  const taken = [];\n"
    "  for(const o of pBullets)\n"
    "    if(o!==b && o.salvo===b.salvo && o.target) taken.push(o.target);\n"
    "  let free=null, fd=Infinity, any=null, ad=Infinity;\n"
    "  for(const e of enemies){\n"
    "    if(e.dead || !canLockOn(e)) continue;\n"
    "    const d = Math.hypot(e.x-b.x, e.y-b.y);\n"
    "    if(d<ad){ ad=d; any=e; }\n"
    "    if(taken.indexOf(e)<0 && d<fd){ fd=d; free=e; }\n"
    "  }\n"
    "  return free || any;\n"
    "}\n"
    "// A target is still worth flying at while it is on the field, alive and\n"
    "// lockable. The lock rule is the one every seeker uses.\n"
    "function swarmHolds(t){\n"
    "  return !!t && !t.dead && enemies.indexOf(t)>=0 && canLockOn(t);\n"
    "}\n"
    "let swarmSalvo = 0;\n"
    "function fireSecondary(){\n",
    "fire: swarm helpers")

fx = replace_once(
    fx,
    "  player.secTimer=wp.cd;\n"
    "  pBullets.push({x:sp.x, y:sp.y,\n",
    "  player.secTimer=wp.cd;\n"
    "  if(wp.swarm){\n"
    "    const tg=swarmTargets(sp.x, sp.y, wp.swarm), id=++swarmSalvo;\n"
    "    for(let k=0;k<wp.swarm;k++){\n"
    "      const a=sa+(wp.swarm>1 ? (k/(wp.swarm-1)-0.5)*wp.fan : 0);\n"
    "      pBullets.push({x:sp.x, y:sp.y,\n"
    "        vx:Math.cos(a)*wp.spd, vy:Math.sin(a)*wp.spd,\n"
    "        w:12, h:4, sec:true, type:'missile', homing:true, life:wp.life,\n"
    "        target:tg[k], swarm:true, salvo:id, dmg:wp.dmg, wpn:wp.key, burst:false});\n"
    "    }\n"
    "    return;\n"
    "  }\n"
    "  pBullets.push({x:sp.x, y:sp.y,\n",
    "fire: swarm salvo")

# ── 5. Homing: a swarm missile flies at its own target ────────────────
fx = replace_once(
    fx,
    "    if(b.homing){\n"
    "      var nearest=null,minD=Infinity;\n"
    "      for(var j=0;j<enemies.length;j++){\n",
    "    if(b.homing){\n"
    "      var nearest=null,minD=Infinity;\n"
    "      if(b.swarm){\n"
    "        if(!swarmHolds(b.target)) b.target=swarmRetarget(b);\n"
    "        nearest=b.target;\n"
    "      } else\n"
    "      for(var j=0;j<enemies.length;j++){\n",
    "homing: swarm")

# ── 6. The pierce mechanism goes with the Durchschlag ─────────────────
cb = replace_once(
    cb,
    "                     pierce:wp.pierce||0, fuse:wp.fuse ?",
    "                     fuse:wp.fuse ?",
    "bolt: pierce field")

fx = replace_once(
    fx,
    "        // A bolt that pierces must not take the same hull twice on its way\n"
    "        // through: a long hull would otherwise be hit once per step.\n"
    "        if(b.hitList && b.hitList.indexOf(e)>=0) continue;\n",
    "",
    "collision: hit list")

fx = replace_once(
    fx,
    "        } else if(b.pierce>0){\n"
    "          b.pierce--;\n"
    "          if(!b.hitList) b.hitList=[];\n"
    "          b.hitList.push(e);\n"
    "          hit=false;\n"
    "        } else {\n",
    "        } else {\n",
    "collision: pierce branch")

open("src/70_ui.js", "w", encoding="utf-8").write(ui)
open("src/60_effects.js", "w", encoding="utf-8").write(fx)
open("src/50_combat.js", "w", encoding="utf-8").write(cb)
print("v128 applied: Tornado added, Durchschlag removed. Now run: python3 assemble.py 128")
