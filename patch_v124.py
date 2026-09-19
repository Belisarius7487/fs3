#!/usr/bin/env python3
"""FS3 v124 - four weapons that behave differently, not four sets of numbers.

  Streuschuss   a cone of pellets from one trigger pull. Devastating against
                a wing that is still flying in formation, useless at any range
                worth the name.
  Durchschlag   a bolt that does not stop at the first hull. It takes
                everything on its line, once each.
  Dante         a flak round. It bursts into shards on impact AND by itself
                after a set distance, so held on the trigger it builds a wall
                of shrapnel at a fixed range that an attack run has to cross.
  Infyrno       fired straight, and the secondary button detonates it in
                flight instead of firing another. Never touched, it detonates
                on impact and gives out at the end of its reach, so the manual
                burst is a skill rather than a chore.
  Stiletto      a bomb that goes for the innards: the whole warhead into the
                nearest living subsystem, and only the bleed into the hull.

Three shapes for the three ways a fight arranges itself: the Streuschuss
serves a CONE, the Durchschlag a LINE, the Dante a VOLUME.

Only one Infyrno may be in the air, which is what keeps the button unambiguous
and is why it needs no key of its own.

Dante on capital ship turrets is deliberately NOT here. Turrets fire through
a different path and that is the place most likely to hold a surprise.

Reads hlp_shooter_v123_logic.html, writes hlp_shooter_v124_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v123_logic.html", "hlp_shooter_v124_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

# ── 1. The table grows ───────────────────────────────────────────────
src = replace_once(
    src,
    "   col:'#bfe9ff', glow:'rgba(120,200,255,0.30)',\n"
    "   note:'quicker and lighter, and it runs out of reach early'}\n"
    "];",
    "   col:'#bfe9ff', glow:'rgba(120,200,255,0.30)',\n"
    "   note:'quicker and lighter, and it runs out of reach early'},\n"
    "  // pellets and spread turn one trigger pull into a cone. dmg is the\n"
    "  // damage of the WHOLE volley, shared out, so a single pellet is slight\n"
    "  // and a face full of them is not.\n"
    "  {key:'scatter', name:'Streuschuss', unlock:14000,\n"
    "   dmg:1.55, rate:1.85, spd:8, range:150, pellets:7, spread:0.30,\n"
    "   col:'#ffd08a', glow:'rgba(255,170,70,0.30)',\n"
    "   note:'a cone of pellets - murder in a crowd, nothing at range'},\n"
    "  // pierce is how many hulls one bolt may take before it gives out. It\n"
    "  // never takes the same ship twice, so a big hull is one hit and not one\n"
    "  // per step of its length.\n"
    "  {key:'pierce', name:'Durchschlag', unlock:22000,\n"
    "   dmg:0.85, rate:1.55, spd:11, range:0, pierce:4,\n"
    "   col:'#e6b9ff', glow:'rgba(200,120,255,0.32)',\n"
    "   note:'takes everything on its line, once each'},\n"
    "  // fuse is the distance at which it bursts of its own accord. That is\n"
    "  // what makes it more than a round with a bonus: held on the trigger it\n"
    "  // lays shrapnel across a fixed range and an attack run has to come\n"
    "  // through it.\n"
    "  {key:'dante', name:'Dante', unlock:32000,\n"
    "   dmg:0.55, rate:1.40, spd:7.5, range:420, fuse:300,\n"
    "   shards:9, shardDmg:0.20, shardSpd:3.4, shardRange:70,\n"
    "   col:'#ffb066', glow:'rgba(255,140,50,0.34)',\n"
    "   note:'bursts on impact and by itself at range - shrapnel, star shaped'}\n"
    "];",
    "primaries",
)

src = replace_once(
    src,
    "  {key:'cyclops', name:'Cyclops', cls:'bomb', unlock:0,\n"
    "   ammoMul:1.0, dmg:80, cd:90, spd:1.5, life:300, homing:true,\n"
    "   note:'slow and heavy, for hulls that cannot dodge'}\n"
    "];",
    "  {key:'cyclops', name:'Cyclops', cls:'bomb', unlock:0,\n"
    "   ammoMul:1.0, dmg:80, cd:90, spd:1.5, life:300, homing:true,\n"
    "   note:'slow and heavy, for hulls that cannot dodge'},\n"
    "  // burst: the secondary button detonates it in flight instead of firing\n"
    "  // another, and only one may be in the air. Straight, no seeking - what\n"
    "  // it asks for is timing, not aim.\n"
    "  {key:'infyrno', name:'Infyrno', cls:'missile', unlock:18000,\n"
    "   ammoMul:0.7, dmg:18, cd:55, spd:4.2, life:200, homing:false,\n"
    "   burst:true, shards:12, shardDmg:14, shardSpd:3.0, shardRange:90,\n"
    "   note:'fired straight - press again to burst it into shrapnel'},\n"
    "  // subs: the warhead goes into the innards rather than the hull. A\n"
    "  // corvette without engines does not leave.\n"
    "  {key:'stiletto', name:'Stiletto', cls:'bomb', unlock:26000,\n"
    "   ammoMul:1.0, dmg:70, cd:95, spd:1.9, life:300, homing:true, subs:true,\n"
    "   note:'into the subsystems, not the hull - stops a ship working'}\n"
    "];",
    "secondaries",
)

# ── 2. Shrapnel, in one place, because three weapons make it ─────────
src = replace_once(
    src,
    "function priDef(key){",
    "// Shrapnel, star shaped from a point. Three weapons make it - the Dante on\n"
    "// impact, the Dante on its fuse, and the Infyrno when it is burst - so it\n"
    "// is written once and they all call it. The shards are ordinary bolts and\n"
    "// travel the ordinary way, which is what keeps them cheap.\n"
    "function shardBurst(x, y, n, dmg, spd, range, col, glow){\n"
    "  const off = Math.random()*Math.PI*2;\n"
    "  const life = Math.max(1, Math.round(range/spd));\n"
    "  for(let i=0;i<n;i++){\n"
    "    const a = off + (i/n)*Math.PI*2;\n"
    "    pBullets.push({x:x, y:y, vx:Math.cos(a)*spd, vy:Math.sin(a)*spd,\n"
    "                   w:8, h:3, dmg:dmg, col:col, glow:glow, pLife:life,\n"
    "                   shard:true});\n"
    "  }\n"
    "  spawnFireball(x, y, 22, 18);\n"
    "  spawnDebris(x, y, 10, 255,190,90, 255,110,0, true);\n"
    "}\n"
    "// A warhead that goes for the innards. subHit only touches whatever\n"
    "// happens to lie under the impact; this looks for the nearest living\n"
    "// subsystem and puts the whole warhead into that, which is the entire\n"
    "// point of carrying one.\n"
    "function subStrike(e, dmg, hx, hy){\n"
    "  if(!e.subs || !e.subs.length) return dmg;\n"
    "  let best = null, bd = Infinity;\n"
    "  for(const s of e.subs){\n"
    "    if(s.dead) continue;\n"
    "    const p = subPos(e, s);\n"
    "    const d = Math.hypot(p.x-hx, p.y-hy);\n"
    "    if(d < bd){ bd = d; best = s; }\n"
    "  }\n"
    "  if(!best) return dmg;\n"
    "  const p = subPos(e, best);\n"
    "  return subHit(e, dmg, p.x, p.y);\n"
    "}\n"
    "function priDef(key){",
    "shard burst",
)

# ── 3. Firing a cone ─────────────────────────────────────────────────
src = replace_once(
    src,
    "  if(pts&&pts.length){\n"
    "    const d=volleyDmg(pts.length)*wp.dmg;\n"
    "    for(const p of pts) pBullets.push({x:p.x,y:p.y,vx:bvx,vy:bvy,w:14,h:3,dmg:d,\n"
    "                                       col:wp.col,glow:wp.glow,pLife:life});\n"
    "    STATS.shots++;\n"
    "    return;\n"
    "  }",
    "  // One bolt per barrel, unless the gun throws a cone - then the volley's\n"
    "  // damage is shared out over the pellets and each barrel throws the lot.\n"
    "  const n=wp.pellets||1;\n"
    "  function throwFrom(px, py, d){\n"
    "    for(let k=0;k<n;k++){\n"
    "      const ja = (n===1) ? a : a + (k/(n-1) - 0.5)*wp.spread\n"
    "                               + (Math.random()-0.5)*(wp.spread/n);\n"
    "      pBullets.push({x:px, y:py, vx:Math.cos(ja)*wp.spd, vy:Math.sin(ja)*wp.spd,\n"
    "                     w:n>1?8:14, h:3, dmg:d/n,\n"
    "                     col:wp.col, glow:wp.glow, pLife:life,\n"
    "                     pierce:wp.pierce||0, fuse:wp.fuse ? Math.max(1, Math.round(wp.fuse/wp.spd)) : 0,\n"
    "                     wpn:wp.key});\n"
    "    }\n"
    "  }\n"
    "  if(pts&&pts.length){\n"
    "    const d=volleyDmg(pts.length)*wp.dmg;\n"
    "    for(const p of pts) throwFrom(p.x, p.y, d);\n"
    "    STATS.shots++;\n"
    "    return;\n"
    "  }",
    "pShoot cone",
)

src = replace_once(
    src,
    "  pBullets.push({x:x+30*nx+4*ny, y:y+30*ny-4*nx, vx:bvx,vy:bvy,w:14,h:3,\n"
    "                 col:wp.col,glow:wp.glow,pLife:life});\n"
    "  pBullets.push({x:x+30*nx-4*ny, y:y+30*ny+4*nx, vx:bvx,vy:bvy,w:14,h:3,\n"
    "                 col:wp.col,glow:wp.glow,pLife:life});",
    "  throwFrom(x+30*nx+4*ny, y+30*ny-4*nx, volleyDmg(2)*wp.dmg);\n"
    "  throwFrom(x+30*nx-4*ny, y+30*ny+4*nx, volleyDmg(2)*wp.dmg);",
    "pShoot fallback cone",
)

# ── 4. The fuse ──────────────────────────────────────────────────────
src = replace_once(
    src,
    "    if(b.pLife){ if(--b.pLife<=0){ pBullets.splice(i,1); continue; } }",
    "    // The fuse comes first: a round that bursts by itself has to do it\n"
    "    // before the reach runs out, or it would simply vanish instead.\n"
    "    if(b.fuse && --b.fuse<=0){\n"
    "      const fw=priDef(b.wpn);\n"
    "      shardBurst(b.x, b.y, fw.shards, b.dmg*fw.shardDmg,\n"
    "                 fw.shardSpd, fw.shardRange, fw.col, fw.glow);\n"
    "      pBullets.splice(i,1); continue;\n"
    "    }\n"
    "    if(b.pLife){ if(--b.pLife<=0){ pBullets.splice(i,1); continue; } }",
    "fuse",
)

# ── 5. Impact: burst, or carry on through ────────────────────────────
src = replace_once(
    src,
    "        laserHit(b.x,b.y);STATS.hits++;e.shotAt=true;damageEnemy(e,(b.dmg||22),b.x,b.y,!b.ally,'bolt');pBullets.splice(i,1);hit=true;\n"
    "        if(e.hp<=0&&!e.dead){ killEnemy(e, j, true, true); }break;}}if(hit)continue;}",
    "        // A bolt that pierces must not take the same hull twice on its way\n"
    "        // through: a long hull would otherwise be hit once per step.\n"
    "        if(b.hitList && b.hitList.indexOf(e)>=0) continue;\n"
    "        laserHit(b.x,b.y);STATS.hits++;e.shotAt=true;damageEnemy(e,(b.dmg||22),b.x,b.y,!b.ally,'bolt');\n"
    "        if(b.fuse!==undefined && b.fuse>0 && b.wpn){\n"
    "          const fw=priDef(b.wpn);\n"
    "          if(fw.shards) shardBurst(b.x, b.y, fw.shards, b.dmg*fw.shardDmg,\n"
    "                                   fw.shardSpd, fw.shardRange, fw.col, fw.glow);\n"
    "          pBullets.splice(i,1); hit=true;\n"
    "        } else if(b.pierce>0){\n"
    "          b.pierce--;\n"
    "          if(!b.hitList) b.hitList=[];\n"
    "          b.hitList.push(e);\n"
    "          hit=false;\n"
    "        } else {\n"
    "          pBullets.splice(i,1); hit=true;\n"
    "        }\n"
    "        if(e.hp<=0&&!e.dead){ killEnemy(e, j, true, true); }\n"
    "        if(hit) break;\n"
    "        continue;}}if(hit)continue;}",
    "impact",
)

# ── 6. The Infyrno: fire, or burst what is already up ────────────────
src = replace_once(
    src,
    "function fireSecondary(){\n"
    "  if(player.secAmmo<=0||player.secTimer>0) return;",
    "// The one Infyrno in the air, if there is one.\n"
    "function liveBurstRound(){\n"
    "  for(const b of pBullets) if(b.sec && b.burst) return b;\n"
    "  return null;\n"
    "}\n"
    "function burstRound(b){\n"
    "  const wp=secDef(b.wpn);\n"
    "  shardBurst(b.x, b.y, wp.shards, wp.shardDmg, wp.shardSpd, wp.shardRange,\n"
    "             '#ffb066', 'rgba(255,140,50,0.34)');\n"
    "  spawnRing(b.x, b.y, 54, 24, 3, 255,140,40);\n"
    "  const i=pBullets.indexOf(b);\n"
    "  if(i>=0) pBullets.splice(i,1);\n"
    "}\n"
    "function fireSecondary(){\n"
    "  // While one is up, the button belongs to it. That is what makes the\n"
    "  // control unambiguous without a key of its own, and it is why only one\n"
    "  // may be in the air at a time.\n"
    "  const up=liveBurstRound();\n"
    "  if(up){ burstRound(up); return; }\n"
    "  if(player.secAmmo<=0||player.secTimer>0) return;",
    "burst control",
)

src = replace_once(
    src,
    "    type:bomb?'bomb':'missile', homing:!!wp.homing, life:wp.life,\n"
    "    target:null, dmg:wp.dmg, wpn:wp.key});",
    "    type:bomb?'bomb':'missile', homing:!!wp.homing, life:wp.life,\n"
    "    target:null, dmg:wp.dmg, wpn:wp.key, burst:!!wp.burst});",
    "burst flag",
)

# It gives out at the end of its reach rather than bursting, so never
# touching the button is a missed chance and not a free area attack.
src = replace_once(
    src,
    "    if(b.type==='bomb' && fc%3===0){",
    "    if(b.burst && fc%2===0){\n"
    "      PARTS.push({x:b.x-b.vx*2, y:b.y+(Math.random()-0.5)*3,\n"
    "        vx:-b.vx*0.2, vy:(Math.random()-0.5)*0.5,\n"
    "        life:22, ml:22, sz:2+Math.random()*2,\n"
    "        clr:Math.random()<0.5?'#ffb066':'#ff7722'});\n"
    "    }\n"
    "    if(b.type==='bomb' && fc%3===0){",
    "burst trail",
)

# ── 7. The Stiletto puts its warhead in the innards ──────────────────
src = replace_once(
    src,
    "        e.shotAt=true;\n"
    "        damageEnemy(e,b.dmg,b.x,b.y,!b.ally,'sec');\n"
    "        if(b.type==='bomb'){",
    "        e.shotAt=true;\n"
    "        // A subsystem warhead spends itself inside and leaves only the\n"
    "        // bleed for the hull. On a ship with nothing to wreck it behaves\n"
    "        // like any other bomb rather than being wasted.\n"
    "        const sw=b.wpn?secDef(b.wpn):null;\n"
    "        if(sw && sw.subs) damageEnemy(e,subStrike(e,b.dmg,b.x,b.y),b.x,b.y,!b.ally,'sec');\n"
    "        else              damageEnemy(e,b.dmg,b.x,b.y,!b.ally,'sec');\n"
    "        if(b.burst){\n"
    "          burstRound(b);\n"
    "          hit=true;\n"
    "          if(e.hp<=0&&!e.dead){ killEnemy(e, j, true, false); }\n"
    "          break;\n"
    "        }\n"
    "        if(b.type==='bomb'){",
    "stiletto",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
