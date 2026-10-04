
// ── ARMS OF THE OTHER SHIPS ──────────────────────────────────
// Fighters and bombers of every side but the Shivans carry the weapons of
// the game, chosen by what the hull is for (the notes in the mount data,
// agreed with Silvio). The Vasudans call the Subach the Mekhu. The Shivans
// keep their own guns and missiles.
//
// An AI weapon keeps the character of the player's version - beat, speed,
// reach, spread, shrapnel, guidance - on the AI's own, lower damage scale:
// the damage of a shot is the volley damage the ship always had, times the
// weapon's weight (Prometheus 1).
//
// p: primary, or one per mount (the Myrmidon mixes a Sidhe with two
// Subachs); s: secondary; pair: two bombs at once (heavy bombers).
const LOADOUT = {
  // Interceptors: quick guns, missiles that spread over several targets.
  fiperseus:{p:'hl7', s:'tornado'}, fiserapis:{p:'hl7', s:'tornado'}, fivalyrie:{p:'hl7', s:'tornado'},
  // Light and stealth fighters.
  fianubis:{p:'hl7', s:'mx64'}, fihorus:{p:'hl7', s:'mx64'}, fipegasus:{p:'hl7', s:'mx64'},
  fiptah:{p:'hl7', s:'mx64'}, filoki:{p:'hl7', s:'mx64'},
  // Space superiority.
  fimyrmidon:{p:['scatter', 'hl7', 'hl7'], s:'tornado'},
  fiulysses:{p:'prometheus', s:'tornado'}, fiapollo:{p:'prometheus', s:'tornado'}, fitoth:{p:'prometheus', s:'tornado'},
  // Heavy assault.
  fiherc:{p:'prometheus', s:'infyrno'}, fihercmk2:{p:'prometheus', s:'infyrno'}, fiseth:{p:'prometheus', s:'infyrno'},
  // Heavy fighters with a slow beat.
  fiares:{p:'dante', s:'infyrno'}, fierinyes:{p:'dante', s:'infyrno'}, fitauret:{p:'dante', s:'infyrno'},
  // Light bombers: into the subsystems of capital ships.
  boathena:{p:'hl7', s:'stiletto'}, bozeus:{p:'hl7', s:'stiletto'}, boartemisdh:{p:'hl7', s:'stiletto'},
  // Medium bombers.
  boartemis:{p:'prometheus', s:'cyclops'}, bomedusa:{p:'prometheus', s:'cyclops'}, bobakha:{p:'prometheus', s:'cyclops'},
  // Heavy bombers: two bombs at once.
  boursa:{p:'hl7', s:'cyclops', pair:true}, boboanerges:{p:'hl7', s:'cyclops', pair:true},
  boosiris:{p:'hl7', s:'cyclops', pair:true}, bosekhmet:{p:'hl7', s:'cyclops', pair:true},
  boamun:{p:'hl7', s:'cyclops', pair:true},
  // Shivans (v161, agreed with Silvio): their own lasers, the same
  // missiles and bombs as everyone else, in Shivan red.
  fiaeshma:{p:'shl', s:'mx64'}, fiscorpion:{p:'shl', s:'mx64'},
  fiastaroth:{p:'shl', s:'tornado'}, fidragon:{p:'shl', s:'tornado'},
  fibasilisk:{p:'shh', s:'tornado'}, fimara:{p:'shh', s:'mx64'}, fimanticore:{p:'shh', s:'infyrno'},
  boshaitan:{p:'shh', s:'stiletto'}, bonahema:{p:'shh', s:'cyclops'}, botaurvi:{p:'shh', s:'cyclops'},
  bonephilim:{p:'shm', s:'cyclops', pair:true}, boseraphim:{p:'shm', s:'cyclops', pair:true}
};
// The lasers of Shivan fighters and bombers (wiki data from Silvio), on the
// scale of the player's guns: the Heavy Laser is the Prometheus. The Light
// Laser fires twice as often at half the punch, the Mega Laser twice the
// punch at two thirds of the beat, over a short reach. All red, as in
// FreeSpace. Only the AI flies them; priDef() finds them here.
const AI_PRIMARIES = {
  shl:{key:'shl', name:'Shivan Light Laser', dmg:0.53, rate:0.6, spd:8.5, range:0,
       col:'#ff7a5a', glow:'rgba(255,70,40,0.34)'},
  shh:{key:'shh', name:'Shivan Heavy Laser', dmg:1.00, rate:1.0, spd:9,   range:0,
       col:'#ff4a30', glow:'rgba(255,40,20,0.38)'},
  shm:{key:'shm', name:'Shivan Mega Laser',  dmg:2.00, rate:1.5, spd:7.6, range:420,
       col:'#ff2a14', glow:'rgba(255,30,10,0.46)', heavy:true}
};
function aiLoadout(e){
  if(!e) return null;
  if(e._lo === undefined) e._lo = LOADOUT[e.img] || null;
  return e._lo;
}
// A secondary fires less often the more it carries in one go.
const AI_SEC_RATE = {mx64:1, cyclops:1, stiletto:1.1, infyrno:1.3, tornado:1.6};
// The AI's bolt speed: its own base speed, scaled like the player's gun.
function aiBoltSpd(w){ return EBULLET_SPD * (w.spd || 9) / 9; }

// One volley of the primaries. Each mount keeps its own clock, so mixed
// guns fire at their own beat. Returns the steps until the next one is due.
function aiGunVolley(e, t, lo, pts, spread){
  const n = pts.length, dpb = eVolleyDmg(n);
  if(!e.mT) e.mT = [];
  let next = Infinity, heard = {};
  for(let i=0;i<n;i++){
    const w = priDef(Array.isArray(lo.p) ? lo.p[i % lo.p.length] : lo.p);
    const beat = Math.max(8, Math.round((e.fR || 120) * (w.rate || 1)));
    if(e.mT[i] && e.mT[i] > fc){ next = Math.min(next, e.mT[i] - fc); continue; }
    e.mT[i] = fc + beat; next = Math.min(next, beat);
    const spd = aiBoltSpd(w);
    const aim = leadAngle(pts[i].x, pts[i].y, t, spd);
    const life = w.range ? Math.max(1, Math.round(w.range/spd)) : 0;
    const k = w.pellets || 1, d = dpb * (w.dmg || 1);
    for(let j=0;j<k;j++){
      const a = (k===1 ? aim : aim + (j/(k-1) - 0.5)*w.spread + (Math.random()-0.5)*(w.spread/k))
              + (Math.random()*2 - 1)*spread;
      aiBolt(e, pts[i].x, pts[i].y, a, spd, d/k, life, w);
    }
    if(!heard[w.key]){ heard[w.key] = 1; sndStart(PRI_SND[w.key] || 'wpn_prometheus', pts[i].x, 1, false, 'ai_fire', pts[i].y); }
  }
  return next === Infinity ? 12 : next;
}
// One bolt. Allied bolts go into the player's list, enemy bolts into theirs.
function aiBolt(e, x, y, a, spd, d, life, w){
  const vx = Math.cos(a)*spd, vy = Math.sin(a)*spd;
  const fuse = w.fuse ? Math.max(1, Math.round(w.fuse/spd)) : 0;
  if(e.side === 'ally'){
    pBullets.push({x:x, y:y, vx:vx, vy:vy, w:w.pellets ? 8 : 11, h:4, dmg:d*2, ally:true, fac:e.faction,
                   pLife:life, fuse:fuse, wpn:fuse ? w.key : undefined,
                   col:w.col, glow:w.glow});
  } else {
    const b = {x:x, y:y, vx:vx, vy:vy, w:w.shards ? 11 : (w.pellets ? 6 : (w.heavy ? 12 : 8)), h:w.heavy ? 5 : 4,
               big:false, faction:e.faction, dmg:d, eLife:life, sm:true,
               col:w.col, glow:w.glow};     // the weapon's colours, not the side's
    // A Dante bursts on its own at range, and where it strikes.
    if(w.shards){ b.dfuse = fuse; b.sh = {n:w.shards, dmg:d*w.shardDmg, spd:w.shardSpd*spd/w.spd, range:w.shardRange}; }
    eBullets.push(b);
  }
}
// Enemy shrapnel: a star of short lived bolts (Dante, Infyrno).
function eShards(x, y, sh, fac){
  // Uneven like the player's bursts, see shardSpread().
  for(const q of shardSpread(sh.n, sh.spd, sh.range)){
    eBullets.push({x:x, y:y, vx:Math.cos(q.a)*q.spd, vy:Math.sin(q.a)*q.spd, w:q.w, h:q.h,
                   dmg:sh.dmg*q.mul, faction:fac, big:false, eLife:q.life, shard:true});
  }
  spawnFireball(x + (Math.random()-0.5)*8, y + (Math.random()-0.5)*8,
                18 + Math.random()*10, 14 + Math.random()*8);
}

// The capital ship a bomb is meant for: the nearest one of the other side.
function aiCapTarget(e, x, y){
  let best = null, bd = Infinity;
  const list = (e.side === 'ally') ? enemies : allies;
  for(const o of list){
    if(o.dead || o.warp>0 || o.warpOut>0 || o.small || o.invuln || o.scenery) continue;
    if(!(o.type==='cruiser' || o.type==='corvette' || o.type==='destroyer' || o.type==='boss' ||
         o.type==='station' || o.type==='freighter')) continue;
    if(e.side === 'ally' && (playerOnly(o) || escortSpares(o))) continue;
    const d = (o.x-x)**2 + (o.y-y)**2;
    if(d < bd){ bd = d; best = o; }
  }
  return best;
}
// The nearest target of the other side for a missile.
function aiSmallTarget(e, x, y){
  if(e.side === 'ally') return nearestEnemy(x, y);
  // A Ptah out of sight is not a target (v170).
  let best = (GS==='playing' && playerSeen()) ? player : null;
  let bd = best ? (player.x-x)**2 + (player.y-y)**2 : Infinity;
  for(const a of allies){
    if(a.dead || a.warp>0 || a.warpOut>0) continue;
    const d = (a.x-x)**2 + (a.y-y)**2;
    if(d < bd){ bd = d; best = a; }
  }
  return best;
}

// One launch of the secondary. false: nothing worth it in sight (a
// Stiletto without a capital ship), the launcher waits and tries again.
function aiSecondary(e, x, y, lo, sec){
  const key = lo.s, w = secDef(key), ally = (e.side === 'ally');
  let tgt;
  if(key==='stiletto') tgt = aiCapTarget(e, x, y);
  else if(key==='cyclops') tgt = aiCapTarget(e, x, y) || aiSmallTarget(e, x, y);
  else tgt = aiSmallTarget(e, x, y);
  if(!tgt) return false;
  const bomb = (w.cls === 'bomb');
  sndStart('sec_'+key, x, 1, false, 'ai_sec', y);
  const n = w.swarm || (lo.pair && bomb ? 2 : 1);
  const base = Math.atan2(tgt.y-y, tgt.x-x);
  const salvo = w.swarm ? ++swarmSalvo : 0;   // a swarm shares its targets out
  for(let k=0;k<n;k++){
    // A pair drops side by side; a swarm leaves in a fan.
    const off = n===1 ? 0 : (k/(n-1) - 0.5);
    const a = base + (w.swarm ? off*w.fan : 0);
    const px = x + (lo.pair && bomb ? -Math.sin(base)*off*16 : 0);
    const py = y + (lo.pair && bomb ? Math.cos(base)*off*16 : 0);
    if(ally){
      pBullets.push({x:px, y:py, vx:Math.cos(a)*w.spd, vy:Math.sin(a)*w.spd,
        w:bomb?16:(w.swarm?12:18), h:bomb?16:(w.swarm?4:6), sec:true, type:bomb?'bomb':'missile',
        homing:!!w.homing, life:w.life, target:tgt, swarm:!!w.swarm, ally:true, fac:e.faction,
        dmg:w.dmg, wpn:key, burst:!!w.burst, auto:!!w.burst, salvo:salvo});
    } else {
      // The enemy's own scale: its old launcher damage, weighted like the
      // player's version against the MX-64.
      const d = sec.dmg * (key==='tornado' ? 0.4 : (bomb ? (key==='stiletto' ? 1.0 : 1.2) : (key==='infyrno' ? 0.8 : 1)));
      const spd = bomb ? Math.min(sec.spd, w.spd) : sec.spd * (key==='infyrno' ? 1.3 : 1);
      const b = {x:px, y:py, vx:Math.cos(a)*spd, vy:Math.sin(a)*spd,
        w:bomb?15:(w.swarm?8:11), h:bomb?15:(w.swarm?4:6), big:false, faction:e.faction||'ntf',
        kind:bomb?'bomb':'missile', dmg:d, hom:!!w.homing, turn:sec.turn*(w.swarm?1.4:1), spd:spd,
        life:bomb?560:440, hp:bomb?1:0, tgt:tgt, wpn:key, subs:!!w.subs};
      if(w.burst){
        b.hom = false; b.bst = {n:w.shards, dmg:sec.dmg*0.5, spd:w.shardSpd, range:w.shardRange};
        // Straight, with lead onto the target.
        const la = leadAngle(px, py, tgt, spd);
        b.vx = Math.cos(la)*spd; b.vy = Math.sin(la)*spd;
      }
      eBullets.push(b);
    }
  }
  return true;
}
// An AI Infyrno sets itself off: in shrapnel reach of its target, or the
// moment it passes it and the distance grows again. true: it burst.
const AI_BURST_REACH = 0.8;
function aiBurstCheck(b, x, y, range){
  const t = b.tgt || b.target;
  if(!t || t.dead) return false;
  const d = Math.hypot(t.x-x, t.y-y);
  const go = d < range*AI_BURST_REACH || (b._bd != null && d > b._bd + 0.3 && b._bd < range*2.5);
  b._bd = d;
  return go;
}

// ── HULLS: armour and traits of the capital ships ────────────
// Capital ships used to take every hit in full, so a fighter's guns took
// a destroyer apart in twenty seconds (practice run v159). Now the plating
// soaks up part of what fighters' guns put into the hull, after the notes
// in the mount data (weak / medium / strong / ultra strong hull). Missiles,
// bombs, beams and the guns of other capital ships go through in full.
// Shrapnel spreads its force over the plating and loses more. Subsystems
// are not armoured: disabling a ship takes as long as it did.
const ARMOR = {weak:0.85, medium:0.7, strong:0.55, ultra:0.4};
// Shrapnel keeps this share of the gun factor. 0.6 in v160 still let the
// Dante take capital ships apart; 0.3 since v161 (Silvio).
const ARMOR_SHARD = 0.3;
const HULL_ARMOR = {
  // weak hull / light armour / poorly armed support hulls
  cacharybdis:'weak', casetekh:'weak', mehippocrates:'weak', scfaustus:'weak', crcain:'weak',
  // cruisers
  craeolus:'medium', ntfcraeolus:'medium', crfenris:'medium', ntfcrfenris:'medium',
  crleviathan:'medium', ntfcrleviathan:'medium', craten:'medium', crmentu:'medium',
  crrakshasa:'medium', crlilith:'strong', coiceni:'medium',
  // corvettes
  codeimos:'strong', ntfcodeimos:'strong', comoloch:'strong', cosobek:'medium',
  // destroyers; the Hecate is the soft one of the class
  deorionleft:'strong', deorionright:'strong', ntfdeorion:'strong',
  dehecate:'medium', ntfdehecate:'medium',
  dedemon:'strong', deravana:'strong', detyphon:'strong', dehatshepsut:'strong',
  inarcadia:'strong',
  // superdestroyers and the Colossus
  sdhades:'ultra', sdlucifer:'ultra', sdsathanas:'ultra', sdcolossus:'ultra'
};
// A hull without an entry gets the plating of its class.
const ARMOR_BY_TYPE = {cruiser:'medium', corvette:'strong', destroyer:'strong', boss:'ultra', station:'strong'};
// What the notes say beyond the plating.
//   beam  more damage from beams ("prone to beam fire")
//   bomb  more damage from bombs ("prone to bombs")
//   flak  flak gun fires this much more often ("anti fighter platform")
//   agile drifts this much faster ("agile cruiser")
const HULL_TRAITS = {
  crfenris:{beam:1.5}, ntfcrfenris:{beam:1.5}, crleviathan:{beam:1.5}, ntfcrleviathan:{beam:1.5},
  dehecate:{bomb:1.5}, ntfdehecate:{bomb:1.5},
  craten:{flak:2}, crmentu:{agile:1.8}
};
function armorClass(e){
  const t = ARMOR_BY_TYPE[e.type];
  return t ? (HULL_ARMOR[e.img] || t) : null;
}
// The share of a hit that reaches the hull. src: 'gun' (a fighter's or
// bomber's primary), 'shard', 'bomb', 'missile', 'beam', 'capgun' (the guns
// of a capital ship); anything else goes through in full.
function hullMul(e, src){
  const tr = HULL_TRAITS[e.img];
  if(src==='beam') return (tr && tr.beam) || 1;
  if(src==='bomb') return (tr && tr.bomb) || 1;
  if(src!=='gun' && src!=='shard') return 1;
  const c = armorClass(e);
  if(!c) return 1;
  return src==='shard' ? ARMOR[c]*ARMOR_SHARD : ARMOR[c];
}
// Where an enemy round came from, for hullMul().
function eSrc(b){
  if(b.kind==='bomb') return 'bomb';
  if(b.kind==='missile') return 'missile';
  if(b.shard) return 'shard';
  return b.sm ? 'gun' : 'capgun';
}
// Traits that change how a ship moves, applied once.
function hullTraitsOnce(e){
  if(e._tr) return;
  e._tr = 1;
  const tr = HULL_TRAITS[e.img];
  if(tr && tr.agile){ if(e.vy) e.vy *= tr.agile; if(e._dv) e._dv *= tr.agile; }
}
