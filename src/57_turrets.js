
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
  const n = (g.big && CAP_TRIPLE.test(e.img)) ? 3 : 1;
  for(let k=0;k<n;k++){
    const a = ang + (n>1 ? (k-1)*0.07 : 0);
    const sp = (ally ? g.aspd : g.spd)*TEMPO_K;     // v209: TEMPO_K
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
  // v209: as long as it flies (its box already is, see pShootWith), at
  // least its v207 length on the screen; as thick as in v207 (fxG)
  const G = fxG(), spd = Math.hypot(b.vx, b.vy);
  const len = Math.max(b.w, Math.min(b.w*G, spd*1.4), 6*G), wid = Math.max(b.h, 3)*G;
  ctx.save();
  ctx.translate(bx|0, by|0);
  ctx.rotate(ang);
  ctx.globalCompositeOperation = 'lighter';
  // The trail: three glows falling back along the path.
  for(let k=3;k>=1;k--){
    ctx.globalAlpha = 0.16*(4-k)/3;
    ctx.fillStyle = glow;
    ctx.beginPath(); ctx.ellipse(-len*0.55*k, 0, len*0.55, wid*0.55, 0, 0, Math.PI*2); ctx.fill();
  }
  ctx.globalAlpha = 0.9;
  ctx.fillStyle = glow;
  ctx.beginPath(); ctx.ellipse(0, 0, len*0.75, wid*1.1, 0, 0, Math.PI*2); ctx.fill();
  ctx.globalCompositeOperation = 'source-over';
  ctx.globalAlpha = 1;
  ctx.fillStyle = core;
  ctx.beginPath(); ctx.ellipse(0, 0, len*0.45, wid*0.55, 0, 0, Math.PI*2); ctx.fill();
  ctx.fillStyle = hot;
  ctx.beginPath(); ctx.ellipse(len*0.08, 0, len*0.22, wid*0.26, 0, 0, Math.PI*2); ctx.fill();
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
// Turn a capital ship's drift towards a side (+1 down, -1 up).
function capSteer(o, dir){
  if(o._dv==null){ o._dv=Math.abs(o.vy||0); o._dd=(o.vy||0)<0?-1:1; }
  o._dd=dir<0?-1:1;
}
