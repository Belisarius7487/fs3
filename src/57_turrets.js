
// ── CAPITAL SHIP TURRETS ─────────────────────────────────────
// The guns of cruisers, corvettes and destroyers after FreeSpace (wiki
// data from Silvio, v161). Every mount carries one gun for good instead
// of rolling a light or a heavy round per shot, and keeps its own beat.
//   tt   Terran Turret, the blob turret of Terrans and Vasudans
//   tht  Terran Huge Turret: a third of the beat, three times the punch,
//        slower, and wide of the mark; the Orion fires hers in threes
//   stl  Shivan Turret Laser, the Shivan blob turret
//   mf   Shivan Megafunk Turret, the heaviest turret of all, very slow
// rate: steps between shots against the ship's own rate; spd and dmg are
// the enemy's scale (the player's gun bolt is 4.5 and 8), aspd and admg the
// escorts' scale, which has always been higher. scat widens the aim.
const CAP_GUNS = {
  tt:  {rate:1,   spd:4.5, dmg:8,  aspd:7.5, admg:18, w:8,  h:4,  scat:1,   snd:'wpn_terran_turret'},
  tht: {rate:3,   spd:2.9, dmg:23, aspd:4.8, admg:52, w:12, h:12, scat:3,   snd:'wpn_tht', big:true},
  stl: {rate:1.2, spd:4.1, dmg:11, aspd:6.8, admg:25, w:9,  h:4,  scat:1,   snd:'wpn_shivan_turret'},
  mf:  {rate:3.4, spd:2.0, dmg:36, aspd:3.3, admg:81, w:14, h:14, scat:1.5, snd:'wpn_shivan_turret', big:true}
};
// Classes that carry heavy turrets, on every third mount (agreed with
// Silvio). Cruisers and corvettes have light ones only.
const CAP_HEAVY = {destroyer:1, station:1, boss:1};
// Hulls that fire their heavy turrets in threes.
const CAP_TRIPLE = /orion/;
function capGun(e, i){
  // v199: a hull with a model has the gun of each real turret
  const _m = mountsFor(e.img), _q = _m && _m.primary && _m.primary[i];
  if(_q && _q.g) return _q.g;
  const shiv = e.faction==='shivan';
  const heavy = CAP_HEAVY[e.type] && (i % 3 === 2);
  return CAP_GUNS[shiv ? (heavy ? 'mf' : 'stl') : (heavy ? 'tht' : 'tt')];
}
// The colour of a race: Terrans blue, Vasudans yellow and orange, Shivans
// red (Silvio). The NTF are Terrans.
const RACE_COL = {
  terran:  {core:'#8fcfff', glow:'rgba(80,170,255,0.38)', hot:'#e6f5ff'},
  vasudan: {core:'#ffc24a', glow:'rgba(255,150,40,0.38)', hot:'#fff2c8'},
  shivan:  {core:'#ff4a30', glow:'rgba(255,40,20,0.40)',  hot:'#ffd2c0'}
};
function raceOf(fac){
  if(fac==='shivan') return 'shivan';
  if(fac==='vasudan' || fac==='hol') return 'vasudan';
  return 'terran';
}
function raceCol(fac){ return RACE_COL[raceOf(fac)]; }

// One shot of a capital turret. ally: an escort's gun (player's list).
// pd: fired at a bomb.
// hidE (v201): fired from the far flank of ship hidE - drawn under her
// hull until it is clear of it (drawShots, 70_ui.js)
function capGunShot(e, x, y, ang, g, ally, pd, hidE){
  const rc = raceCol(e.faction);
  // v210: from where her turret is drawn - shots fly in the plane and hit
  // what is drawn there (hullView), so they leave the drawn hull too
  if(typeof hullPt === 'function'){ const vp = hullPt(e, x, y); x = vp.x; y = vp.y; }
  const n = (g.big && CAP_TRIPLE.test(e.img)) ? 3 : 1;
  for(let k=0;k<n;k++){
    const a = ang + (n>1 ? (k-1)*0.07 : 0);
    const sp = pSpd(ally ? g.aspd : g.spd)*TEMPO_K;     // v212: pSpd
    if(ally){
      pBullets.push({x:x, y:y, vx:Math.cos(a)*sp, vy:Math.sin(a)*sp,
        w:g.big?13:11, h:g.big?13:4, dmg:g.admg, ally:true, fac:e.faction, cap:true,
        col:rc.core, glow:rc.glow, big:!!g.big, hidE:hidE||null});
    } else {
      eBullets.push({x:x, y:y, vx:Math.cos(a)*sp, vy:Math.sin(a)*sp,
        w:g.w, h:g.h, big:!!g.big, faction:e.faction||'ntf', dmg:g.dmg,
        col:rc.core, glow:rc.glow, pd:!!pd, hidE:hidE||null});
    }
  }
}

// ── POINT DEFENCE ──
// The blob turrets are the best defence against bombs there is: a bomb on
// its way in is shot at before anything else. Both sides do it (Silvio),
// the enemy ships at the player's bombs and the escorts' too.
const PD_RANGE = 240*TEMPO_K;     // v209: reach as in v207 on the screen
function pdTarget(e, p, ally){
  let best = null, bd = PD_RANGE*PD_RANGE;
  if(ally){
    for(const b of eBullets){
      if(b.kind!=='bomb') continue;
      const d = (b.x-p.x)**2 + (b.y-p.y)**2;
      if(d < bd){ bd = d; best = b; }
    }
  } else {
    for(const b of pBullets){
      if(!b.sec || b.type!=='bomb') continue;
      const d = (b.x-p.x)**2 + (b.y-p.y)**2;
      if(d < bd){ bd = d; best = b; }
    }
  }
  return best;
}
// An enemy point defence round meeting a bomb of ours. true: both gone.
// (The escorts' rounds are in the player's list and already stop enemy
// bombs, see the bomb check in the bolt loop.)
function pdHit(b){
  if(!b.pd) return false;
  for(let k=pBullets.length-1;k>=0;k--){
    const q = pBullets[k];
    if(!q.sec || q.type!=='bomb') continue;
    if(Math.abs(q.x-b.x) > (q.w+b.w)/2 || Math.abs(q.y-b.y) > (q.h+b.h)/2) continue;
    pBullets.splice(k,1);
    spawnFireball(q.x, q.y, 18, 20);
    spawnDebris(q.x, q.y, 8, 255,200,80, 255,120,0, true);
    sndPlay('sec_cyclops_hit', q.x, 0.6);
    return true;
  }
  return false;
}

// ── LASERS ──
// Every bolt of every side gets the same treatment (Silvio: "fancier",
// with particles): a trail of fading glow behind it, a hot core, sparks
// shed now and then, a flash where it leaves the gun. The sparks are
// capped, a full screen of bolts must not bury the frame rate.
const LASER_SPARK_CAP = 450;
function drawLaser(b, core, glow, hot){
  const ang = Math.atan2(b.vy, b.vx), bx = b.x, by = b.y;
  if(b._ls == null){
    b._ls = (Math.random()*6)|0;
    // Muzzle flash: the first time it is seen. Not for a round from a far
    // flank (v201): the flash would sit on top of the hull that hides it.
    if(PARTS.length < LASER_SPARK_CAP && !b.hidE){
      PARTS.push({x:bx, y:by, vx:0, vy:0, life:5, ml:0, sz:Math.min(b.w, 21)*0.45+1.5, clr:hot});   // v209: sz is drawn times fxG()
      for(let k=0;k<1;k++){
        const a = ang + (Math.random()-0.5)*1.2, s = 0.8 + Math.random()*1.4;
        PARTS.push({x:bx, y:by, vx:Math.cos(a)*s, vy:Math.sin(a)*s,
                    life:(6+Math.random()*6)|0, ml:0, sz:0.8+Math.random()*0.8, clr:core});
      }
    }
  }
  // v209: at least its v207 length on the screen, as thick as in v207
  // (fxG). v210: the bolt flies at its v208 pace again, so the length is
  // its box times G (as long as v209 drew it), not its flight per step
  const G = fxG();
  const len = Math.max(b.w*G, 6*G), wid = Math.max(b.h, 3)*G;
  // v213 (Silvio: the glows were visible rims of light): soft sprites
  // only (glowAt, 61_glow.js) - a fading trail, the glowing body, a
  // white-hot core - no filled ellipse with an edge
  ctx.save();
  ctx.translate(bx, by);
  ctx.rotate(ang);
  // v215: two trail glows (three before), less to fill on the graphics card
  for(let k=2;k>=1;k--) glowAt(-len*0.6*k, 0, len*0.8, wid*0.9, glow, 0.32*(3-k)/2, 0);
  glowAt(0, 0, len*0.95, wid*1.7, glow, 0.95, 0);
  glowAt(0, 0, len*0.62, wid*0.85, core, 1, 0.5);
  glowAt(len*0.08, 0, len*0.34, wid*0.42, hot, 1, 1);
  ctx.restore();
  // A spark now and then, thrown back off the bolt.
  if((fc + b._ls) % 6 === 0 && PARTS.length < LASER_SPARK_CAP){
    const a = ang + Math.PI + (Math.random()-0.5)*0.9, s = 0.4 + Math.random()*0.9;
    PARTS.push({x:bx - Math.cos(ang)*len*0.5, y:by - Math.sin(ang)*len*0.5,
                vx:Math.cos(a)*s, vy:Math.sin(a)*s,
                life:(8+Math.random()*8)|0, ml:0, sz:0.7+Math.random()*0.9,
                clr:Math.random()<0.5 ? hot : core});
  }
}
// Where a bolt strikes: a small spray in its own colour.
function laserSpark(x, y, core){
  if(PARTS.length >= LASER_SPARK_CAP) return;
  for(let k=0;k<4;k++){
    const a = Math.random()*Math.PI*2, s = 0.6 + Math.random()*1.6;
    PARTS.push({x:x, y:y, vx:Math.cos(a)*s, vy:Math.sin(a)*s,
                life:(6+Math.random()*8)|0, ml:0, sz:0.8+Math.random(), clr:core || '#ffffff'});
  }
}
// White hot centre that goes with a colour, for bolts that bring only
// their core and glow.
function hotOf(col){
  if(!col || col[0]!=='#' || col.length<7) return '#ffffff';
  const m = (i) => Math.min(255, (parseInt(col.substr(i,2),16) + 255*2)/3|0);
  return 'rgb('+m(1)+','+m(3)+','+m(5)+')';
}

// ── CAPITAL SHIP DRIFT ──
// Capital ships patrol up and down. Their drift used to flip at the edge of
// the lane from one step to the next; now it turns round ahead of the edge
// and eases into the new direction (Silvio, v162). _dv is the patrol speed,
// _dd the direction it is heading for. mul: faster drift (a boss in rage).
function capDrift(o, mul){
  if(!subOK(o,'engines')){ o.vy=0; return; }     // dead in the water
  if(o._dv==null){ o._dv=Math.abs(o.vy||0); o._dd=(o.vy||0)<0?-1:1; }
  if(!o._dv) return;                             // a ship that holds still
  const lo=o.minY, hi=o.maxY;
  if(lo!=null && hi!=null && hi-lo>4){
    const m=Math.min(40, (hi-lo)*0.25);
    if(o.y>hi-m && o._dd>0) o._dd=-1;
    else if(o.y<lo+m && o._dd<0) o._dd=1;
  }
  const tgt=o._dd*o._dv, ra=o._dv*0.03;
  o.vy+=Math.max(-ra, Math.min(ra, tgt-o.vy));
  o.y+=o.vy*(mul||1);
}
// Turn a capital ship's drift towards a side (+1 down, -1 up). v211: a
// ship on a lane keeps it - the lanes are apart already (laneInit).
function capSteer(o, dir){
  if(o._lane && !o._lane.stand) return;
  if(o._dv==null){ o._dv=Math.abs(o.vy||0); o._dd=(o.vy||0)<0?-1:1; }
  o._dd=dir<0?-1:1;
}

// ── CAPITAL SHIP LANES (v211, Silvio) ──
// The up and down patrol (capDrift) was left over from the side scroller.
// Now a capital ship drives along her own lane, towards the other side,
// and turns round - before the edge of the mission area, and before a ship
// or installation that stands still in her lane - then back to where she
// took station, and turns again. Lanes are kept apart: no two ships that
// drive share a band, so they pass each other. Ships held by a task stand
// (still, transit, docking, ramming, fleeing, dead engines); stations and
// the bosses of the missions stand as well.
// Speed: FS $Max Velocity (m/s) in the ratio of the small craft
// (SMALL_SPD_ANCHOR, TEMPO_K).
const CAP_VEL = {
  cacharybdis:20, casetekh:20, codeimos:30, coiceni:35, comoloch:30, cosobek:30,
  craeolus:30, craten:25, crcain:30, crfenris:20, crleviathan:10, crlilith:20, crmentu:35,
  crrakshasa:20, scfaustus:25, mehippocrates:20,
  dedemon:20, dehatshepsut:15, dehecate:15, deorionleft:15, deorionright:15, deorion:15,
  deravana:20, detyphon:15, sdhades:15, sdlucifer:15, sdsathanas:25, sdcolossus:25,
  frasmodeus:50, frbast:50, frbes:50, frchronos:40, frdis:50, frmaat:50, frmephisto:50,
  frposeidon:50, frsatis:50, frtriton:30, trargo:30, trazrael:55, trelysium:40, trisis:35
};
const CAP_VEL_TYPE = {cruiser:25, corvette:30, destroyer:15, freighter:40, transport:40};
// seconds for the half turn (Claude: FS has no rotation time for them here)
const CAP_TURN_S = {cruiser:4, corvette:6, destroyer:9};
const LANE_GAP  = 40;     // world units between two lanes, and before a ship that stands
const LANE_EDGE = 60;     // and before the edge of the mission area
const LANE_SQ_MIN = 0.2;  // her width seen bow on, of her length
const LANE_MIN = 500;     // the shortest stretch worth driving between two turns
function capCruise(o){
  const k = String(o.img || '').replace(/^ntf/, '');
  return (CAP_VEL[k] || CAP_VEL_TYPE[o.type] || 20)*SMALL_SPD_ANCHOR*TEMPO_K;
}
// Seconds from a standstill to her cruise, and the same the other way.
// A capital ship had no acceleration at all: she came out of her vortex
// standing - fsExitSpeed() returns 0 for an ally, so the picture brings her
// out at nothing - and was at her full cruise in the very next tick.
// warpsim saw it in thirteen places and the numbers are exactly her cruise:
// "stop craten/A1 speed 0.00 -> 1.81 px/tick (after jump)" against
// 25 x SMALL_SPD_ANCHOR x TEMPO_K = 1.81, cosobek 30 -> 2.18,
// dehatshepsut 15 -> 1.09 (Silvio, v232: accepted as a real fault).
//
// EVERYTHING a capital ship drives with goes through here - her glide to
// her station, her lane, her coast through a turn - so that no two of them
// can disagree about how fast she is. The step is her own cruise over the
// time, so a slow hull accelerates gently and a fast one briskly, and both
// take the same seconds to get there.
const CAP_ACC_S = 2.5;
function capAcc(o, want){
  const step = capCruise(o)/(CAP_ACC_S*TICK_HZ);
  const v = (o._capV == null) ? 0 : o._capV;
  o._capV = v + Math.max(-step, Math.min(step, want - v));
  return o._capV;
}
function capBow(o){ return ((spriteFacing(o.img) === 'right') !== !!o.flip) ? 1 : -1; }
// held where she is by her task in the mission
function capHolds(o){
  // a ship someone is coming to dock with waits for them (M80, the Hecate
  // patched up by transports) - cargoStillWanted(), 30_waves.js
  if(o.uid && typeof cargoStillWanted === 'function' && cargoStillWanted(o)) return true;
  // crossing: a ship driving across the field steers herself, like capRam.
  // tickCrossGuards() moves her by o.crossing - 1.0 a step for a freighter -
  // and takes her out past the right edge. Without her here, capLane drove
  // her as well, at capCruise (about 18 a step for a freighter), and turned
  // her round at her lane limit, which laneLimit pulls in front of whatever
  // else stands in that lane - the Aten in M9. So the Bast freighters flew
  // back and forth instead of warping out to the right, and could not be
  // protected (Silvio, v216). A crossing is the drive itself, not something
  // added to another drive.
  return !!(o.still || o.capRam || o.crossing || o.transit || o.dockTo || o.fleeing || o.escaping || o.platform
            || o.colossus || (o.minY != null && o.maxY != null && o.maxY - o.minY < 1));
}
function capMovers(){
  const out = [];
  for(const o of enemies) if(o._lane && !o._lane.stand && !o.dead) out.push(o);
  for(const o of allies)  if(o._lane && !o._lane.stand && !o.dead) out.push(o);
  return out;
}
// big things that stand: a ship or installation she must turn before
function laneBlockers(o){
  const out = [];
  const add = b => {
    if(b === o || b.dead || b.small || (b._lane && !b._lane.stand) || b.scenery || b.ghost) return;
    if(b.type === 'fighter' || b.type === 'bomber' || b.type === 'asteroid' || b.type === 'sentry' || b.type === 'container') return;
    if(b.warp > 0) return;
    if(b.type === 'freighter' && Math.abs(b.vx || 0) > 0.05) return;   // crossing, not standing
    out.push(b);
  };
  for(const b of enemies) add(b);
  for(const b of allies) add(b);
  return out;
}
// Her lane is the band she is in when she takes station - no sliding
// sideways through the others. If that band is taken by a ship that
// already drives (the clearance the hulls keep anyway, CAPITAL_GAP), she
// stands where she is, and the others turn before her.
function laneHalf(o){ return (typeof halfH === 'function') ? halfH(o) : hullBox(o).hh; }
function laneInit(o){
  const hh = laneHalf(o);
  const free = capMovers().every(m => Math.abs(m._lane.y - o.y) >= (hh + laneHalf(m))*CAPITAL_GAP + 4);
  if(!free){ o._lane = {stand: true}; return; }
  o._lane = {y: o.y, dir: capBow(o), dir0: capBow(o), home: o.x, t: null};
}
// where her middle has to stop going in direction d
function laneLimit(o, L, d){
  const B = hullBox(o), hw = B.hw;
  let lim = d > 0 ? MW - LANE_EDGE - hw : LANE_EDGE + hw;
  // back towards her station: no further than where she took it
  if(d !== L.dir0) lim = d > 0 ? Math.min(lim, L.home) : Math.max(lim, L.home);
  for(const b of laneBlockers(o)){
    const C = hullBox(b);
    // not in her lane: as far apart as the hulls keep anyway (CAPITAL_GAP)
    if(Math.abs(b.y - o.y) >= (laneHalf(o) + laneHalf(b))*CAPITAL_GAP) continue;
    if(d > 0 && C.cx > o.x) lim = Math.min(lim, C.cx - C.hw - LANE_GAP - hw);
    if(d < 0 && C.cx < o.x) lim = Math.max(lim, C.cx + C.hw + LANE_GAP + hw);
  }
  return lim;
}
function capLane(o, mul){
  if(!subOK(o, 'engines')){ o.vy = 0; capAcc(o, 0); return; }   // dead in the water
  if(o._lane && o._lane.t){
    // a turn once begun is finished - and one that is already opening out
    // for a jump is not turned back into a turn
    if(o._lane.t.settle != null) capTurnSettle(o); else capTurnStep(o, mul);
    return;
  }
  // Held, standing, or no room: she runs down rather than stops dead, and
  // sets off again from nothing when she is let go.
  if(capHolds(o)){ o.vy = 0; capAcc(o, 0); return; }
  if(!o._lane) laneInit(o);
  if(o._lane.stand){ o.vy = 0; capAcc(o, 0); return; }
  const L = o._lane, v = capAcc(o, capCruise(o)*(mul || 1));
  // back into her lane if something pushed her out of it
  const dy = L.y - o.y; o.vy = Math.max(-v*0.4, Math.min(v*0.4, dy*0.02)); o.y += o.vy;
  const lim = laneLimit(o, L, L.dir), ahead = L.dir > 0 ? lim - o.x : o.x - lim;
  // too little room between her two turns: she holds in her lane until
  // there is more
  const back = laneLimit(o, L, -L.dir);
  L.hold = Math.abs(lim - back) < Math.max(LANE_MIN, hullBox(o).hw*3);
  if(L.hold){ o.vy = 0; capAcc(o, 0); return; }
  if(ahead <= 0){
    L.t = {p: 0, n: Math.round((CAP_TURN_S[o.type] || 6)*60)};
    capTurnStep(o, mul); return;
  }
  // slows down over the last two seconds before the turn
  o.x += L.dir*v*Math.max(0.3, Math.min(1, ahead/(v*120)));
}
// The half turn: she swings round about her middle (her model yaws, seen
// bow on half way), coasting on slowly. turnSq is her length across the
// picture, signed - mounts, outline and hits follow it.
// A jump out freezes a turn where it stands: once warpOut runs, the ship's
// branch returns before capLane() is reached again, so turnSq keeps her
// squashed side on while the vortex is placed by fsNose(), which reads the
// heading she had BEFORE the turn. She slid into her own vortex sideways
// (Silvio, v216).
//
// Waiting for the turn to finish, which is what he suggested, is not open to
// us: a turn is CAP_TURN_S seconds - nine for a destroyer, 540 steps - while
// the whole changeover is TRANS_CLEAR + TRANS_OUT, about 220. She would be
// cleared away by the next wave instead of leaving at all.
//
// So the turn is settled to whichever heading she is nearer to. turnC is
// cos(pi*p): positive in the first half, where she still mostly faces the
// way she came from, negative in the second, where she is mostly round. Past
// half way she is flipped as capTurnStep would have flipped her; before it
// she keeps the heading she had. Either way she is drawn whole, facing
// somewhere real, and her vortex is placed by that.
//
// v227 did all of that in ONE frame, and that is what Silvio then saw: "das
// Schiff snapt auf der Stelle in die Warp-Richtung ohne langsame Bewegung"
// (v230). The heading cannot be eased into - fsWarp() fixes where the
// vortex stands and which way it faces at the FIRST tick of the jump
// (_fsG), and a gate chasing a heading she has not reached yet is the very
// fault this function exists for. The SWEEP can: it is mirrored along with
// her, so that after the first tick she is in the first half of a turn that
// simply opens back out, and that is run off over half the jump.
function capTurnSettle(o){
  const L = o && o._lane;
  if(!L || !L.t) return;
  const T = L.t;
  if(T.settle == null){
    // Flipped as capTurnStep would have flipped her, and the sweep that is
    // left mirrored with her: p becomes 1 - p. The picture is the same -
    // a flipped hull at +|c| looks exactly like an unflipped one at -|c| -
    // but the heading is now final and the sweep is back in its first half.
    if(o.turnC < 0){ o.flip = !o.flip; L.dir = -L.dir; T.p = 1 - T.p; }
    // Half the jump to open out: she is whole and steady well before she is
    // inside the vortex, and a destroyer's 80 steps are a swing, not a snap.
    T.settle = Math.max(1, Math.round((o.warpOut > 0 ? o.warpOut : 60)*0.5));
    T.sstep = T.p/T.settle;
  }
  T.p = Math.max(0, T.p - T.sstep);
  const c = Math.cos(Math.PI*T.p);
  o.turnP = T.p; o.turnSq = (c < 0 ? -1 : 1)*Math.max(LANE_SQ_MIN, Math.abs(c));
  o.turnC = c;
  if(T.p <= 0){ L.t = null; o.turnP = null; o.turnSq = null; o.turnC = null; }
}
function capTurnStep(o, mul){
  const L = o._lane, T = L.t, v = capAcc(o, capCruise(o)*(mul || 1));
  T.p = Math.min(1, T.p + 1/T.n);
  const c = Math.cos(Math.PI*T.p);
  o.x += L.dir*v*0.3*c;
  o.turnP = T.p; o.turnSq = (c < 0 ? -1 : 1)*Math.max(LANE_SQ_MIN, Math.abs(c));
  // v214: the mounts follow c itself, through the middle - with turnSq
  // they jumped from one side to the other half way (Silvio: beams jumping)
  o.turnC = c;
  if(T.p >= 1){
    o.flip = !o.flip; L.dir = -L.dir; L.t = null; o.turnP = null; o.turnSq = null; o.turnC = null;
  }
}
