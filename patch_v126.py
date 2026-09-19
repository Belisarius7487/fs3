#!/usr/bin/env python3
"""FS3 v126 - the Dante goes on the turrets.

Every capital from a cruiser up now carries one flak gun, off a primary mount
it already has. It is not aimed at a hull: it throws a round that bursts at a
set distance and leaves a wall of shrapnel where an attack run has to come
through. That is the point of flak - it does not hit things, it makes closing
expensive.

Both sides get it. A weapon only one side has is not a weapon, it is a
handicap. For an allied cruiser it finally gives the escort a defence the
player can watch working; for an enemy one it turns a run at a corvette into
a decision rather than a formality.

Two clamps on where the wall stands:
  - never further out than FLAK_DIST and never nearer than FLAK_MIN, so a gun
    cannot drop a burst on its own hull;
  - and pulled back until the burst sits FLAK_EDGE_KEEP inside the field, so a
    gun on the right does not build its wall off the left of the screen.

The round travels as an ordinary bolt and bursts on its fuse or on impact,
whichever comes first - the same machinery the player's Dante uses.

Reads hlp_shooter_v125_logic.html, writes hlp_shooter_v126_logic.html.
Every search text must occur exactly once, otherwise nothing is written.
"""
import sys

SRC, DST = "hlp_shooter_v125_logic.html", "hlp_shooter_v126_logic.html"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("Abbruch (%s): Suchtext %d-mal gefunden, erwartet einmal." % (label, n))
    return text.replace(old, new)


src = open(SRC, encoding="utf-8").read()

FLAK = r"""// -- CAPITAL FLAK ---------------------------------------------
// One flak gun on every capital from a cruiser up, firing off a primary mount
// the ship already carries. No new mount data, and a hull that grows a mount
// later grows a flak position with it.
const FLAK_TYPES       = {cruiser:1, corvette:1, destroyer:1, boss:1};
const FLAK_RATE        = [115, 205];  // steps between rounds, rolled each time
const FLAK_SPD         = 6.0;
const FLAK_DIST        = 300;         // how far out the wall stands
const FLAK_MIN         = 110;         // and no nearer, or it bursts on itself
// A gun on the right must not build its wall off the left of the screen. The
// burst point is pulled back until it sits this far inside the field.
const FLAK_EDGE_KEEP   = 130;
const FLAK_SHARDS      = 8;
const FLAK_SHARD_DMG   = 3;
const FLAK_SHARD_SPD   = 2.6;
const FLAK_SHARD_RANGE = 62;
function flakHas(e){ return !!FLAK_TYPES[e.type]; }
// The shrapnel. An allied gun throws it into the player's list so it bites
// enemies; an enemy gun into the enemy list so it bites the player and the
// escorts. Same star shape either way.
function flakBurst(x, y, ally, fac){
  const off  = Math.random()*Math.PI*2;
  const life = Math.max(1, Math.round(FLAK_SHARD_RANGE/FLAK_SHARD_SPD));
  for(let i=0;i<FLAK_SHARDS;i++){
    const a  = off + (i/FLAK_SHARDS)*Math.PI*2;
    const vx = Math.cos(a)*FLAK_SHARD_SPD, vy = Math.sin(a)*FLAK_SHARD_SPD;
    if(ally) pBullets.push({x:x, y:y, vx:vx, vy:vy, w:7, h:3,
                            dmg:FLAK_SHARD_DMG, ally:true, fac:fac,
                            pLife:life, shard:true});
    else     eBullets.push({x:x, y:y, vx:vx, vy:vy, w:7, h:3,
                            dmg:FLAK_SHARD_DMG, faction:fac, big:false,
                            eLife:life, shard:true});
  }
  spawnFireball(x, y, 20, 16);
}
// Where the wall stands: as far out as the target, inside the two limits, and
// pulled back again if that would put the burst off the far side.
function flakReach(px, py, ang, want){
  let d = Math.max(FLAK_MIN, Math.min(FLAK_DIST, want));
  const cx = Math.cos(ang), cy = Math.sin(ang);
  for(let k=0;k<12;k++){
    const bx = px + cx*d, by = py + cy*d;
    if(bx >= FLAK_EDGE_KEEP && bx <= W-FLAK_EDGE_KEEP && by >= 0 && by <= H) break;
    d -= 22;
    if(d <= FLAK_MIN){ d = FLAK_MIN; break; }
  }
  return d;
}
function flakFire(e, ally){
  if(!flakHas(e) || e.dead || e.warp>0 || e.warpOut>0) return;
  if(e.noFire || !subOK(e,'weapons')) return;
  if(e.flakT===undefined) e.flakT = rndR(FLAK_RATE)|0;
  if(--e.flakT > 0) return;
  e.flakT = rndR(FLAK_RATE)|0;
  const pts = entMounts(e,'primary');
  if(!pts || !pts.length) return;
  const p  = pts[(Math.random()*pts.length)|0];
  const tg = ally ? nearestEnemy(p.x, p.y) : capGunTarget(e);
  if(!tg) return;
  const ang  = Math.atan2(tg.y-p.y, tg.x-p.x);
  const want = Math.hypot(tg.x-p.x, tg.y-p.y);
  const d    = flakReach(p.x, p.y, ang, want);
  const fuse = Math.max(1, Math.round(d/FLAK_SPD));
  const vx = Math.cos(ang)*FLAK_SPD, vy = Math.sin(ang)*FLAK_SPD;
  if(ally) pBullets.push({x:p.x, y:p.y, vx:vx, vy:vy, w:9, h:5,
                          dmg:FLAK_SHARD_DMG, ally:true, fac:e.faction,
                          flak:true, fuse:fuse});
  else     eBullets.push({x:p.x, y:p.y, vx:vx, vy:vy, w:9, h:5,
                          dmg:FLAK_SHARD_DMG, faction:e.faction, big:false,
                          flak:true, fuse:fuse});
}

"""

src = replace_once(src, "function capitalFire(e){", FLAK + "function capitalFire(e){", "flak gun")

src = replace_once(
    src,
    "  fireSecondaries(e, cfg);\n}",
    "  fireSecondaries(e, cfg);\n  flakFire(e, false);\n}",
    "enemy flak",
)

src = replace_once(
    src,
    "function allyFire(a){\n  if(!subOK(a,'weapons')) return;",
    "function allyFire(a){\n"
    "  // The flak gun is its own gun on its own clock, not one of the barrels\n"
    "  // taking a turn, so it fires whether or not the main guns have a target.\n"
    "  flakFire(a, true);\n"
    "  if(!subOK(a,'weapons')) return;",
    "ally flak",
)

src = replace_once(
    src,
    "    if(b.fuse && --b.fuse<=0){\n"
    "      const fw=priDef(b.wpn);\n"
    "      shardBurst(b.x, b.y, fw.shards, b.dmg*fw.shardDmg,\n"
    "                 fw.shardSpd, fw.shardRange, fw.col, fw.glow);\n"
    "      pBullets.splice(i,1); continue;\n"
    "    }",
    "    if(b.fuse && --b.fuse<=0){\n"
    "      if(b.flak) flakBurst(b.x, b.y, true, b.fac);\n"
    "      else {\n"
    "        const fw=priDef(b.wpn);\n"
    "        shardBurst(b.x, b.y, fw.shards, b.dmg*fw.shardDmg,\n"
    "                   fw.shardSpd, fw.shardRange, fw.col, fw.glow);\n"
    "      }\n"
    "      pBullets.splice(i,1); continue;\n"
    "    }",
    "ally fuse",
)

src = replace_once(
    src,
    "    b.x+=b.vx;b.y+=b.vy;\n"
    "    if(debrisEatsBolt(b)){ eBullets.splice(i,1); continue; }\n"
    "    if(b.x<-60||b.x>W+60||b.y<-60||b.y>H+60){eBullets.splice(i,1);continue;}",
    "    b.x+=b.vx;b.y+=b.vy;\n"
    "    // A flak round bursts where its fuse runs out, and the shrapnel it\n"
    "    // leaves is what the run has to cross.\n"
    "    if(b.fuse && --b.fuse<=0){\n"
    "      flakBurst(b.x, b.y, false, b.faction);\n"
    "      eBullets.splice(i,1); continue;\n"
    "    }\n"
    "    // Shrapnel gives out on its own rather than flying to the edge.\n"
    "    if(b.eLife && --b.eLife<=0){ eBullets.splice(i,1); continue; }\n"
    "    if(debrisEatsBolt(b)){ eBullets.splice(i,1); continue; }\n"
    "    if(b.x<-60||b.x>W+60||b.y<-60||b.y>H+60){eBullets.splice(i,1);continue;}",
    "enemy fuse",
)

src = replace_once(
    src,
    "        if(b.fuse!==undefined && b.fuse>0 && b.wpn){",
    "        if(b.flak){\n"
    "          flakBurst(b.x, b.y, true, b.fac);\n"
    "          pBullets.splice(i,1); hit=true;\n"
    "        } else if(b.fuse!==undefined && b.fuse>0 && b.wpn){",
    "ally flak impact",
)

open(DST, "w", encoding="utf-8").write(src)
print("%s geschrieben (%d KB)." % (DST, len(src.encode("utf-8")) // 1024))
