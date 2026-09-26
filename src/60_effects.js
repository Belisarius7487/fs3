// ── HIT EFFECTS ──────────────────────────────────────────
let shieldFlash = 0;  // Schild-Hit Overlay-Flash
let hullFlash   = 0;  // hull hit overlay flash

function shieldHit(x, y) {
  shieldFlash = 8;
  // Schild-Funken: blau-cyan, konzentriert um Hitpunkt
  for(var i=0;i<14;i++){
    var a=Math.random()*Math.PI*2, spd=0.5+Math.random()*1.8;
    PARTS.push({x:x,y:y,vx:Math.cos(a)*spd,vy:Math.sin(a)*spd,
      life:45,ml:45,sz:Math.random()<0.4?5:3,
      clr:['#44aaff','#88ccff','#aaddff','#ffffff'][Math.floor(Math.random()*4)]});
  }
}

function hullHit(x, y) {
  hullFlash = 7;
  // Hull sparks: orange yellow, sharp
  for(var i=0;i<14;i++){
    var a=Math.random()*Math.PI*2, spd=0.8+Math.random()*2.5;
    PARTS.push({x:x,y:y,vx:Math.cos(a)*spd,vy:Math.sin(a)*spd,
      life:50,ml:50,sz:Math.random()<0.4?5:3,
      clr:['#ffaa00','#ffdd00','#ff6600','#ffffff'][Math.floor(Math.random()*4)]});
  }
}

function laserHit(x, y) {
  // Laser-Einschlag: helle Funken
  for(var i=0;i<14;i++){
    var a=Math.random()*Math.PI*2, spd=0.8+Math.random()*3.5;
    PARTS.push({x:x,y:y,vx:Math.cos(a)*spd,vy:Math.sin(a)*spd,
      life:35,ml:35,sz:Math.random()<0.35?4:2,
      clr:['#ffffaa','#ffff66','#ffffff','#aaff88'][Math.floor(Math.random()*4)]});
  }
  // Heller Zentralblitz
  PARTS.push({x:x,y:y,vx:0,vy:0,life:12,ml:12,sz:8,clr:'#ffffff'});
}


function secMount(){
  const flip=player.flip||false;
  const pts=mountList(player.ship,player.x,player.y,playerSc(),flip,'secondary',player.ang||0);
  return (pts&&pts.length) ? pts[0] : {x:player.x+28,y:player.y};
}

// The one Infyrno in the air, if there is one.
function liveBurstRound(){
  for(const b of pBullets) if(b.sec && b.burst) return b;
  return null;
}
function burstRound(b){
  const wp=secDef(b.wpn);
  shardBurst(b.x, b.y, wp.shards, wp.shardDmg, wp.shardSpd, wp.shardRange,
             '#ffb066', 'rgba(255,140,50,0.34)');
  spawnRing(b.x, b.y, 54, 24, 3, 255,140,40);
  const i=pBullets.indexOf(b);
  if(i>=0) pBullets.splice(i,1);
}
// Who the missiles of one Tornado salvo go for: the nearest n targets that
// can be locked, one each. With fewer targets than missiles they double
// up from the nearest. Nothing lockable at all gives nulls, and the
// missiles fly straight until something turns up.
function swarmTargets(x, y, n){
  const list = [];
  for(const e of enemies){
    if(e.dead || !canLockOn(e)) continue;
    list.push({e:e, d:Math.hypot(e.x-x, e.y-y)});
  }
  list.sort(function(a,b){ return a.d-b.d; });
  const out = [];
  for(let k=0;k<n;k++) out.push(list.length ? list[k%list.length].e : null);
  return out;
}
// A swarm missile whose target is gone looks again: first for the nearest
// target none of its own salvo is flying at, then for the nearest at all.
function swarmRetarget(b){
  const taken = [];
  for(const o of pBullets)
    if(o!==b && o.salvo===b.salvo && o.target) taken.push(o.target);
  let free=null, fd=Infinity, any=null, ad=Infinity;
  for(const e of enemies){
    if(e.dead || !canLockOn(e)) continue;
    const d = Math.hypot(e.x-b.x, e.y-b.y);
    if(d<ad){ ad=d; any=e; }
    if(taken.indexOf(e)<0 && d<fd){ fd=d; free=e; }
  }
  return free || any;
}
// A target is still worth flying at while it is on the field, alive and
// lockable. The lock rule is the one every seeker uses.
function swarmHolds(t){
  return !!t && !t.dead && enemies.indexOf(t)>=0 && canLockOn(t);
}
let swarmSalvo = 0;
function fireSecondary(){
  // While one is up, the button belongs to it. That is what makes the
  // control unambiguous without a key of its own, and it is why only one
  // may be in the air at a time.
  const up=liveBurstRound();
  if(up){ burstRound(up); return; }
  if(player.secAmmo<=0||player.secTimer>0) return;
  player.secAmmo--;
  // One rail for both kinds: what differs is in the table, not here.
  const wp=curSec(), bomb=(wp.cls==='bomb');
  const sp=secMount(), sa=player.head||0;
  player.secTimer=wp.cd;
  if(wp.swarm){
    const tg=swarmTargets(sp.x, sp.y, wp.swarm), id=++swarmSalvo;
    for(let k=0;k<wp.swarm;k++){
      const a=sa+(wp.swarm>1 ? (k/(wp.swarm-1)-0.5)*wp.fan : 0);
      pBullets.push({x:sp.x, y:sp.y,
        vx:Math.cos(a)*wp.spd, vy:Math.sin(a)*wp.spd,
        w:12, h:4, sec:true, type:'missile', homing:true, life:wp.life,
        target:tg[k], swarm:true, salvo:id, dmg:wp.dmg, wpn:wp.key, burst:false});
    }
    return;
  }
  pBullets.push({x:sp.x, y:sp.y,
    vx:Math.cos(sa)*wp.spd, vy:Math.sin(sa)*wp.spd,
    w:bomb?16:18, h:bomb?16:6, sec:true,
    type:bomb?'bomb':'missile', homing:!!wp.homing, life:wp.life,
    target:null, dmg:wp.dmg, wpn:wp.key, burst:!!wp.burst});
}

function updateSecBullets(){
  if(player.secTimer>0) player.secTimer--;
  for(var i=pBullets.length-1;i>=0;i--){
    var b=pBullets[i];
    if(!b.sec) continue;
    b.life--;
    if(b.life<=0){pBullets.splice(i,1);continue;}
    // Missile: mild homing onto the nearest enemy
    if(b.homing){
      var nearest=null,minD=Infinity;
      if(b.swarm){
        if(!swarmHolds(b.target)) b.target=swarmRetarget(b);
        nearest=b.target;
      } else
      for(var j=0;j<enemies.length;j++){
        if(!canLockOn(enemies[j])) continue;   // stealth hulls cannot be held
        if(b.ally && playerOnly(enemies[j])) continue;
        var d=Math.hypot(enemies[j].x-b.x,enemies[j].y-b.y);
        if(d<minD){minD=d;nearest=enemies[j];}
      }
      if(nearest){
        var ang=Math.atan2(nearest.y-b.y,nearest.x-b.x);
        var turnRate=b.type==='missile'?0.18:0.06; // Bombs turn far more slowly
        var maxSpd=b.type==='missile'?5.5:3.0;
        b.vx+=(Math.cos(ang)*turnRate);
        b.vy+=(Math.sin(ang)*turnRate);
        var spd=Math.hypot(b.vx,b.vy);
        if(spd>maxSpd){b.vx=b.vx/spd*maxSpd;b.vy=b.vy/spd*maxSpd;}
      }
    }
    b.x+=b.vx; b.y+=b.vy;
    // Trail-Partikel
    if(b.type==='missile' && fc%2===0){
      PARTS.push({x:b.x-b.vx*2,y:b.y+(Math.random()-0.5)*3,
        vx:-0.5-Math.random()*1.5,vy:(Math.random()-0.5)*0.8,
        life:30,ml:30,sz:Math.random()<0.4?5:3,
        clr:Math.random()<0.5?'#ff6600':'#ffaa33'});
    }
    if(b.burst && fc%2===0){
      PARTS.push({x:b.x-b.vx*2, y:b.y+(Math.random()-0.5)*3,
        vx:-b.vx*0.2, vy:(Math.random()-0.5)*0.5,
        life:22, ml:22, sz:2+Math.random()*2,
        clr:Math.random()<0.5?'#ffb066':'#ff7722'});
    }
    if(b.type==='bomb' && fc%3===0){
      PARTS.push({x:b.x-b.vx*3,y:b.y+(Math.random()-0.5)*5,
        vx:-0.3-Math.random(),vy:(Math.random()-0.5)*0.6,
        life:55,ml:55,sz:6+Math.random()*7,
        clr:Math.random()<0.5?'rgba(80,80,90,0.6)':'rgba(60,60,70,0.4)'});
    }
    if(b.x>W+20||b.x<-20||b.y<-20||b.y>H+20){pBullets.splice(i,1);continue;}
    // Collision
    var hit=false;
    for(var j=enemies.length-1;j>=0;j--){
      var e=enemies[j];
      var er=eBox(e);
      if(overlap(b.x-b.w/2,b.y-b.h/2,b.w,b.h,er[0],er[1],er[2],er[3])){
        if(!bulletOnHull(e,b)) continue;   // impact landed on empty space
        if(b.ally && playerOnly(e)) continue;   // allied fire passes through
        e.shotAt=true;
        // A subsystem warhead spends itself inside and leaves only the
        // bleed for the hull. On a ship with nothing to wreck it behaves
        // like any other bomb rather than being wasted.
        const sw=b.wpn?secDef(b.wpn):null;
        if(sw && sw.subs) damageEnemy(e,subStrike(e,b.dmg,b.x,b.y),b.x,b.y,!b.ally,'sec');
        else              damageEnemy(e,b.dmg,b.x,b.y,!b.ally,'sec');
        if(b.burst){
          burstRound(b);
          hit=true;
          if(e.hp<=0&&!e.dead){ killEnemy(e, j, true, false); }
          break;
        }
        if(b.type==='bomb'){
          spawnFireball(b.x,b.y,45,40);
          spawnRing(b.x,b.y,70,30,4,255,120,0);
          spawnDebris(b.x,b.y,25,255,180,50,200,60,0,true);
          spawnSmoke(b.x,b.y,8);
        } else {
          spawnFireball(b.x,b.y,20,22);
          spawnDebris(b.x,b.y,10,255,220,100,255,100,0,true);
        }
        pBullets.splice(i,1);hit=true;
        if(e.hp<=0&&!e.dead){ killEnemy(e, j, true, false); }
        break;
      }
    }
    if(hit) continue;
  }
}


// ── EXPLOSIONSSYSTEM ─────────────────────────────────────────
const EXPL_Q = []; // Delayed secondary detonations

// Helper: RGB interpolation for gradients
function lerpRGB(r1,g1,b1,r2,g2,b2,t){
  return 'rgb('+Math.round(r1+(r2-r1)*t)+','+
                Math.round(g1+(g2-g1)*t)+','+
                Math.round(b1+(b2-b1)*t)+')';
}

// Erweiterte Partikel: sq=Quadrat, ring=Schockwelle, fb=Fireball-Disc
function spawnFireball(x, y, maxR, dur) {
  PARTS.push({type:'fb', x:x, y:y, r:0, maxR:maxR, life:dur, ml:dur});
}
function spawnRing(x, y, maxR, dur, lw, r1,g1,b1) {
  PARTS.push({type:'ring', x:x, y:y, r:2, maxR:maxR, life:dur, ml:dur,
    lw:lw||2, cr:r1||255, cg:g1||180, cb:b1||50});
}
function spawnDebris(x, y, n, r1,g1,b1, r2,g2,b2, fast) {
  for(var i=0;i<n;i++){
    var a=Math.random()*Math.PI*2;
    var spd=fast?(3+Math.random()*7):(1.5+Math.random()*4);
    var t=Math.random(); // start color variation
    var sr=Math.round(r1+(r2-r1)*t), sg=Math.round(g1+(g2-g1)*t), sb=Math.round(b1+(b2-b1)*t);
    PARTS.push({type:'deb',
      x:x+(Math.random()-0.5)*8, y:y+(Math.random()-0.5)*8,
      vx:Math.cos(a)*spd, vy:Math.sin(a)*spd,
      life:40+Math.random()*60, ml:0,
      sz:1+Math.random()*3,
      sr:sr,sg:sg,sb:sb,          // Startfarbe (hell)
      er:Math.round(r2*0.3),eg:Math.round(g2*0.1),eb:0}); // Endfarbe (dunkel)
  }
}
function spawnSmoke(x, y, n) {
  for(var i=0;i<n;i++){
    var a=Math.random()*Math.PI*2;
    var spd=0.3+Math.random()*1.2;
    PARTS.push({type:'smoke',
      x:x+(Math.random()-0.5)*20, y:y+(Math.random()-0.5)*20,
      vx:Math.cos(a)*spd, vy:Math.sin(a)*spd-0.3,
      life:80+Math.random()*80, ml:0,
      sz:8+Math.random()*14,
      v:40+Math.random()*30}); // Grau-Wert
  }
}

function scheduleExpl(delay, x, y, r, type) {
  EXPL_Q.push({t:fc+delay, x:x, y:y, r:r, type:type});
}

// r: reach of the wave, pct: share of the player's hull it takes at full
// strength. A destroyer's own wave is 260 and 0.040 for comparison.
const BIG_BLAST = {
  scfaustus:  {r:300, force:5.0, pct:0.070, shake:12},
  incommnode: {r:320, force:5.2, pct:0.080, shake:14},
  gmanuket:   {r:380, force:6.0, pct:0.100, shake:16},
  gmrahu:     {r:380, force:6.0, pct:0.100, shake:16},
  gmzephyrus: {r:400, force:6.4, pct:0.110, shake:16}
};
function triggerExpl(x, y, shipType, faction, src) {
  // The branch chain below has no else. Any type that is not in it dies
  // silently, with no fireball, no ring and no debris - which is what the
  // non-combatants did when they were first added. They borrow the
  // profile that matches their size rather than each getting a copy of
  // the same block. Remapped before spawnWreck so the wreck code sees a
  // type it knows as well.
  if(shipType==='freighter')      shipType='corvette';
  else if(shipType==='sentry')    shipType='bomber';
  else if(shipType==='container') shipType='fighter';
  // Wreckage is spawned here rather than at each of the five death sites,
  // so nothing is forgotten when a sixth one is added.
  if(src) spawnWreck(src, shipType, x, y);
  // Hulls the mount data calls out for a big blast radius. The class
  // profile below still runs; this is the extra wave on top of it.
  if(src && BIG_BLAST[src.img]){
    const bb = BIG_BLAST[src.img];
    spawnShock(x, y, bb.r, bb.force, bb.pct);
    addShake(bb.shake, bb.shake*3);
  }
  var isShiv = faction==='shivan';
  // Fraktions-Farbpalette
  var r1=255,g1=isShiv?80:200,b1=isShiv?0:50;
  var r2=255,g2=isShiv?20:120,b2=0;

  if(shipType==='fighter'||shipType==='asteroid') {
    spawnFireball(x,y,40,50);
    spawnRing(x,y,65,35,3,r1,g1,b1);
    spawnDebris(x,y,22,r1,g1,b1,r2,g2,b2,true);
    spawnSmoke(x,y,7);

  } else if(shipType==='bomber') {
    spawnFireball(x,y,36,45);
    spawnRing(x,y,60,30,3,r1,g1,b1);
    spawnDebris(x,y,28,r1,g1,b1,r2,g2,b2,true);
    spawnSmoke(x,y,8);
    scheduleExpl(12, x+20,y-8,  20,'mini');
    scheduleExpl(22, x-15,y+12, 18,'mini');

  } else if(shipType==='cruiser') {
    spawnFireball(x,y,58,70);
    spawnRing(x,y,95,45,3,r1,g1,b1);
    spawnRing(x,y,60,60,2,r2,g2,b2);
    spawnRing(x,y,150,70,5,255,235,190);
    spawnRing(x,y,210,95,3,255,245,215);
    spawnDebris(x,y,85,r1,g1,b1,r2,g2,b2,true);
    spawnSmoke(x,y,30);
    spawnShock(x,y,165,3.4,0.030);
    addShake(8,32);
    for(var i=0;i<6;i++) {
      scheduleExpl(10+i*20, x+(Math.random()-0.5)*100, y+(Math.random()-0.5)*40,
        22+Math.random()*10, 'mini');
    }
    scheduleExpl(140, x, y, 40, 'final');

  } else if(shipType==='corvette') {
    // Corvettes are much larger than cruisers, so this runs longer
    spawnFireball(x,y,68,80);
    spawnRing(x,y,110,50,4,r1,g1,b1);
    spawnRing(x,y,72,66,3,r2,g2,b2);
    spawnRing(x,y,185,80,6,255,235,190);
    spawnRing(x,y,260,110,4,255,245,215);
    spawnDebris(x,y,100,r1,g1,b1,r2,g2,b2,true);
    spawnSmoke(x,y,36);
    spawnShock(x,y,205,4.0,0.035);
    addShake(10,38);
    for(var i=0;i<8;i++) {
      scheduleExpl(8+i*20, x+(Math.random()-0.5)*150, y+(Math.random()-0.5)*50,
        24+Math.random()*14, i%3===0 ? 'medium' : 'mini');
    }
    scheduleExpl(180, x, y, 52, 'final');

  } else if(shipType==='destroyer') {
    // Destroyers come apart along their whole length
    spawnFireball(x,y,76,88);
    spawnRing(x,y,125,55,4,r1,g1,b1);
    spawnRing(x,y,85,72,3,r2,g2,b2);
    spawnRing(x,y,55,92,2,255,255,200);
    spawnRing(x,y,235,95,7,255,240,205);
    spawnRing(x,y,330,130,5,255,248,225);
    spawnDebris(x,y,120,r1,g1,b1,r2,g2,b2,true);
    spawnSmoke(x,y,44);
    spawnShock(x,y,260,4.8,0.040);
    addShake(13,46);
    for(var i=0;i<11;i++) {
      scheduleExpl(8+i*21, x+(Math.random()-0.5)*260, y+(Math.random()-0.5)*70,
        26+Math.random()*20, i%3===0 ? 'medium' : 'mini');
    }
    scheduleExpl(230, x, y, 58, 'final');

  } else if(shipType==='boss') {
    // Hauptexplosion
    spawnFireball(x,y,80,90);
    spawnRing(x,y,120,55,5,r1,g1,b1);
    spawnRing(x,y,80,75,3,r2,g2,b2);
    spawnRing(x,y,50,95,2,255,255,200);
    spawnRing(x,y,380,150,6,255,250,230);
    spawnDebris(x,y,130,r1,g1,b1,r2,g2,b2,true);
    spawnSmoke(x,y,48);
    spawnShock(x,y,300,5.4,0.045);
    addShake(16,60);
    // Many staggered secondary detonations
    var spread = shipType==='boss' ? 120 : 80;
    for(var i=0;i<8;i++) {
      scheduleExpl(8+i*22,
        x+(Math.random()-0.5)*spread, y+(Math.random()-0.5)*spread*0.5,
        30+Math.random()*25, 'medium');
    }
    // Abschlussexplosion
    scheduleExpl(200, x, y, 60, 'final');
  }
}

function tickExplQueue() {
  for(var i=EXPL_Q.length-1;i>=0;i--) {
    if(fc>=EXPL_Q[i].t) {
      var e=EXPL_Q[i];
      if(e.type==='mini') {
        spawnFireball(e.x,e.y,e.r,22);
        spawnDebris(e.x,e.y,8,255,180,50,200,60,0,true);
      } else if(e.type==='medium') {
        spawnFireball(e.x,e.y,e.r,35);
        spawnRing(e.x,e.y,e.r*2,25,2,255,150,30);
        spawnDebris(e.x,e.y,15,255,180,50,200,60,0,true);
        spawnSmoke(e.x,e.y,5);
      } else if(e.type==='final') {
        spawnFireball(e.x,e.y,e.r*1.5,50);
        spawnRing(e.x,e.y,e.r*3,45,6,255,255,180);
        spawnDebris(e.x,e.y,30,255,255,200,255,100,0,true);
      }
      EXPL_Q.splice(i,1);
    }
  }
}

// ── COLLISION ────────────────────────────────────────────────
function overlap(ax,ay,aw,ah,bx,by,bw,bh){return ax<bx+bw&&ax+aw>bx&&ay<by+bh&&ay+ah>by;}
// A rotated sprite covers more of the screen than its own width and
// height. Both coarse boxes therefore have to grow with the hull angle,
// or a round aimed at a vertical nose is thrown away before the alpha
// mask is ever asked. This box may only ever be too large, never too
// small: it is a filter, the mask decides the actual hit.
function rotExtent(pw, ph, ang){
  if(!ang) return [pw, ph];
  const c=Math.abs(Math.cos(ang)), s=Math.abs(Math.sin(ang));
  return [pw*c+ph*s, pw*s+ph*c];
}
function eBox(e){
  if(e.type==='asteroid'){const r=16*e.sc;return[e.x-r,e.y-r,r*2,r*2];}
  const img=IMGS[e.img];if(!img)return[e.x-20,e.y-20,40,40];
  const bx=rotExtent(img.width*e.sc, img.height*e.sc, e.ang||0);
  return[e.x-bx[0]*.5,e.y-bx[1]*.5,bx[0],bx[1]];}   // full extent, the mask handles the detail
function pBox(){
  const img=IMGS[player.ship];
  if(!img) return[player.x-20,player.y-14,40,28];
  const sc=playerSc();
  const bx=rotExtent(img.width*sc, img.height*sc, player.ang||0);
  return[player.x-bx[0]*.5,player.y-bx[1]*.5,bx[0],bx[1]];}

function playerDie(){STATS.livesLost++;
  triggerExpl(player.x,player.y,'cruiser','terran',{img:player.ship,sc:playerSc()});
  // Im Uebungsmodus kostet der Tod nichts. Die Explosion, der Rueckwurf
  // an den Rand und der Schild laufen unveraendert, damit sich der Fehler
  // trotzdem wie einer anfuehlt.
  if(!(practiceMode && FS1_MODE)){
    if(--lives<=0){GS='gameover';gameOverAt=performance.now();return;}
  }
  player.hp=player.maxHp;player.x=80;player.y=H/2;eBullets=[];
  // Was player.sh=100. In an era without shields that handed back
  // something the player is not supposed to have yet.
  resetPlayerShield();}


function launchGame(){
  var btn=document.getElementById('launchBtn');
  if(btn) btn.style.display='none';
  document.body.classList.add('nocursor');
  shipUnlocked=UI_SHIPS; shipSwapWave=-1; shipMenu=false;
  score=0;lives=LIVES_START;wave=(FS1_MODE?fs1First()-1:(SCRIPT_ONE?SCRIPT_ONE-1:0));fc=0;currentFaction='ntf';icenEscapes=0;runTime=0;
  statsReset();
  // Tickets are cleared here and nowhere else: they survive losing a life
  // and are lost on game over.
  tickets={cruiser:TICKET_START.cruiser, corvette:TICKET_START.corvette,
           destroyer:TICKET_START.destroyer, colossus:TICKET_START.colossus};
  // One of every class: the hangar needs a destroyer, the rearm panel a
  // corvette, and the Colossus changes what both of them say.
  if(UI_TICKETS){
    tickets.cruiser+=1; tickets.corvette+=1;
    tickets.destroyer+=1; tickets.colossus+=1;
  }
  ITEMS=[];ticketFlash=0;TICKET_MSGS=[];SUB_MSGS=[];
  player={x:80,y:H/2,ang:0,head:0,aimAng:0,flip:false,vx:0,vy:0,
          hp:100,maxHp:100,sh:100,maxSh:100,
          shRecharge:0.22,shDelay:0,
          fT:0,fR:28,
          spd:PLAYER_SPD_FIGHTER, turn:PLAYER_TURN, baseHp:100,
          // The player scales too, otherwise a later cycle is only longer
          // rather than harder.
          hullMult:1,
          ship:PLAYER_SHIPS[0].key,
          secAmmo:0,secMax:0,
          secTimer:0,secType:'missile'};
  // The cycle of the first wave decides the fleet. FS1 has its own.
  if(FS1_MODE || TEST_MODE) applyShip(PLAYER_SHIPS[0].key);
  else enterCycle(cycleAt(wave+1));
  // Without this the ship would set off towards wherever the launch button
  // was pressed, which since the speed cap is a visible drive across the field.
  MOUSE.x=player.x; MOUSE.y=player.y;
  runTime=0;
  pBullets=[];eBullets=[];enemies=[];allies=[];allyCd=0;callMenu=false;shipMenu=false;userPaused=false;paused=false;PARTS=[];ITEMS=[];
  resumeHold=false;
  bossAlive=false;bossSlain=false;shakeT=0;shakeMag=0;campReset();rollBodies();nextWave();GS='playing';
}
window.launchGame=launchGame;

function nextWave(){
  wave++;waveOver=false;waveCd=0;bossAlive=false;bossSlain=false;
  // Crossing into the next cycle hands over the fleet.
  if(!FS1_MODE && !TEST_MODE){ const _c = cycleAt(wave); if(_c!==cycleNow) enterCycle(_c); }
  // Die verbuendete Staffel wird nach dem Wellenaufbau gestellt, weil
  // getWaveDef ihre Zahl erst dort setzt.
  window._allyWingDue = true;
  // Scheitel der Dunkelheit: near = 1, Schwaerzung 92 %. Zusammen mit der
  // Deckkraft in drawBodies() bleibt vom Wechsel nichts uebrig.
  rollBodies();
  // Second half of the jump: the ship comes out at the field edge.
  arriveT = TRANS_IN; transFog = 0;
  player.x = 80; player.y = H/2; MOUSE.x = player.x; MOUSE.y = player.y;
  // Leeren VOR getWaveDef, damit eine Welle ohne eigenen Titel nicht den
  // der vorigen erbt. buildFS1Wave setzt ihn gleich danach.
  waveTitle=''; titleT=0;
  objWasSet=false; objDoneT=0; objFailed=false; objSeenOnce=false;
  protSaved=0; protLost=0;
  crossDone=0; crossTotal=0; commsCut=false; commsSeen=false;
  enemies=[];eBullets=[];allies=[];debris=[];empOut=0;allyCd=0;callMenu=false;shipMenu=false;userPaused=false;paused=false;spawnQ=getWaveDef(wave);spawnT=0;
  for(let i=0;i<allyWingWanted;i++){
    const a = mkAllySmall('fighter','terran',
                          rnd(ROLES.ally_ter_fighters||ROLES.ter_fighters||['fiherc']),
                          H*(0.34+0.14*i));
    if(a) allies.push(a);
  }
  // Tickets carry over, the pickups on the field do not.
  ITEMS=[];
  // Ordnance was only ever set at launch, so after the first boss there
  // was nothing left for the rest of the run. Hull is deliberately not
  // restored here: that is what the repair pickups are for.
  // In the campaign the roster grows as the briefings hand it over; the
  // newest unlocked hull is assigned and the switch button stays hidden.
  if(FS1_MODE){
    const un = fs1ShipsUpTo(wave);
    if(un.length && player.ship!==un[un.length-1]) applyShip(un[un.length-1]);
  }
  player.secAmmo=player.secMax;
  // Before the prototypes come through, nobody in the fleet has a shield.
  // maxSh is left standing so the HUD bar keeps its geometry and simply
  // reads empty, which is the correct picture rather than a missing one.
  resetPlayerShield();
  // Keep the player level with the capital ships as the cycles go up.
  const pm=cycleMult();
  if(pm!==player.hullMult){
    const frac=player.hp/player.maxHp;
    player.maxHp=Math.round((player.baseHp||100)*pm);
    player.hp=Math.round(player.maxHp*frac);
    player.hullMult=pm;
  }
  capBomberLeft=CAP_BOMBER_WAVES;capBomberCd=0;}

// ── UPDATE ───────────────────────────────────────────────────
function update(){
  // The title screen is not a still picture: the stars and the bodies keep
  // moving there, so that much of the update runs before anything else.
  if(GS==='title'){ fc++; tickStars(); tickNebula(); return; }
  if(paused) return;                  // covers the settings panel too
  fc++;tickStars();tickParts();tickNebula();
  // Der Abbau stand unter "if(GS!=='playing')return;". Nach einem Game
  // Over lief update() also nie mehr bis dorthin, waehrend draw() den
  // Versatz weiter anlegte: der Schirm ruettelte bis zum naechsten Start.
  // Hier oben laeuft der Ruettler der Todesexplosion sauber aus.
  if(shakeT>0 && --shakeT<=0) shakeMag=0;
  tickScan();
  tickDefectors();
  tickDocking();
  tickCapRam();
  tickDeathRoll();
  tickEscapers();
  tickCrossGuards();
  tickComms();
  tickRamming();
  tickEvents();
  tickShipUnlocks();
  tickWeaponUnlocks();
  if(arriveT>0) arriveT--;
  // Clearing beat: everything loose is pushed off the field under its own
  // power. Der Dunst wird hier NICHT mehr angefasst.
  if(waveOver && waveCd>TRANS_OUT){
    for(const e of enemies) if(e.type==='asteroid'){ e.vx-=0.055; e.vy*=0.99; }
    for(const d of debris){ d.vx-=0.055; d.vy*=0.99; }
  }
  // Der Dunst fiel mit 0.018 je Schritt durch den Raeumtakt und war damit
  // rund 1.6 s vor der Blende weg: der Nebel loeste sich bei vollem Licht
  // auf. Jetzt haengt er an der Blende - soviel Dunst wie Licht. Es ist
  // dieselbe Kurve, aus der die Dunkelheit gezeichnet wird.
  if(waveOver || arriveT>0){
    transFog = Math.min(transFog+0.05, 1-jumpDark());
    // Die Ueberblendung des Hintergrunds startet mit der Dunkelheit, nicht
    // am Wellenende, damit der Wechsel dort liegt wo ihn niemand sieht.
    if(waveOver && waveCd<TRANS_OUT*0.45) startNebFade();
  } else {
    transFog = Math.min(1, transFog+0.05);
  }
  if(GS!=='playing')return;
  if(!callMenu) runTime++;
  // Locked: the ship is committed to the jump. Everything else on the
  // field keeps running, so a wave still finishes cleanly around it.
  if(inJump()){
    player.fT = Math.max(player.fT, 4);
    MOUSE.x = player.x; MOUSE.y = player.y;
  }
  // The pointer is destination and aiming reference at once: the ship
  // flies towards it and the nose points at it. The whole field is open,
  // because enemy fighters do not stay on their half either.
  const pImg=IMGS[player.ship];
  // A hull that can rotate needs a margin that survives any heading, so
  // the wider of the two sprite extents counts, not the height alone.
  const pHalf=pImg ? Math.max(pImg.width,pImg.height)*playerSc()*0.5 : 16;
  const xMin=pHalf, xMax=W-pHalf;
  const yTop=HUD_H+pHalf, yBot=H-pHalf;
  if(inJump()){ player.vx=0; player.vy=0; }
  const targetX=Math.max(xMin,Math.min(xMax,MOUSE.x));
  const targetY=Math.max(yTop,Math.min(yBot,MOUSE.y));
  // Hold radius: inside it the pointer only turns the ship. Past it the
  // speed ramps up over HOLD_BAND instead of switching on at full, and
  // because the ship never closes the gap the offset vector below is
  // always well defined. That is what replaced the pointer speed tracking.
  const pPrevX=player.x, pPrevY=player.y;
  const holdR=Math.max(HOLD_R_MIN, pHalf*HOLD_R_MULT);
  player.holdR=holdR;          // drawn as a ring, so it has to leave update()
  const toX=targetX-player.x, toY=targetY-player.y;
  const toD=Math.sqrt(toX*toX+toY*toY);
  if(toD>holdR){
    const over=toD-holdR;
    const stepLen=Math.min(over, player.spd*Math.min(1, over/HOLD_BAND));
    player.x+=toX/toD*stepLen;
    player.y+=toY/toD*stepLen;
  }
  // Fallback: still support the keyboard
  if(K['ArrowUp']||K['KeyW'])player.y-=player.spd;
  if(K['ArrowDown']||K['KeyS'])player.y+=player.spd;
  if(K['ArrowLeft']||K['KeyA'])player.x-=player.spd;
  if(K['ArrowRight']||K['KeyD'])player.x+=player.spd;
  player.x=Math.max(xMin,Math.min(xMax,player.x));
  player.y=Math.max(yTop,Math.min(yBot,player.y));
  // Movement record, used by enemy gunners to lead their shots.
  player.vx=player.x-pPrevX; player.vy=player.y-pPrevY;
  // Heading: at the pointer while there is a pointer to speak of, else
  // along the keyboard course. Failing both the last commanded direction
  // is kept, so a turn always runs to the end.
  const aimDX=MOUSE.x-player.x, aimDY=MOUSE.y-player.y;
  if(aimDX*aimDX+aimDY*aimDY > AIM_DEAD*AIM_DEAD){
    player.aimAng=Math.atan2(aimDY,aimDX);
  } else if(K['ArrowUp']||K['KeyW']||K['ArrowDown']||K['KeyS']||
            K['ArrowLeft']||K['KeyA']||K['ArrowRight']||K['KeyD']){
    const mvX=player.vx, mvY=player.vy;
    if(mvX*mvX+mvY*mvY > 0.25) player.aimAng=Math.atan2(mvY,mvX);
  }
  let dAng=player.aimAng-player.head;
  while(dAng> Math.PI) dAng-=Math.PI*2;
  while(dAng<-Math.PI) dAng+=Math.PI*2;
  player.head+=Math.max(-(player.turn||PLAYER_TURN),Math.min(player.turn||PLAYER_TURN,dAng));
  if(player.head> Math.PI) player.head-=Math.PI*2;
  else if(player.head<-Math.PI) player.head+=Math.PI*2;
  // head is where the ship points and shoots, ang and flip are only how it
  // gets drawn. Everything downstream reads ang and flip.
  const pPose=poseFor(player.head, player.flip);
  player.ang=pPose.ang; player.flip=pPose.flip;
  if(!inJump()&&(isFiring||MOUSE.down||K['Space']||K['KeyZ'])&&--player.fT<=0){pShoot();player.fT=player.fR;}
  else if(!isFiring&&!MOUSE.down&&!K['Space']&&!K['KeyZ']){if(player.fT>0)player.fT--;}
  // Schild-Aufladung
  if(player.shHit>0){player.shHit--;}
  if(player.shDelay>0){player.shDelay--;}
  else if(!eraShieldsOff() && player.sh<player.maxSh){
    player.sh=Math.min(player.maxSh,player.sh+player.shRecharge);
  }

  updateAllies();
  separateCapitals();
  for(const o of enemies) if(o.img) clampToField(o);
  for(const o of allies)  if(o.img) clampToField(o);
  tickCarry();
  reapEnemies();
  updateAsteroidImpacts();
  updateDebris();
  updateShocks();
  updatePushes();
  updateBombPortals();
  tickScorch(enemies);
  if(allies.length) tickScorch(allies);
  updateSecBullets();
  tickExplQueue();
  if(!waveOver){
    spawnT++;
    while(spawnQ.length&&spawnQ[0].time<=spawnT){
      // Hold back fighters and bombers while the field is already full.
      // Asteroids and capital ships are never delayed: the first are
      // scenery, the second set the shape of the engagement.
      const _nx=spawnQ[0];
      // Wings wait for an empty field instead of for a clock. The old
      // schedule released them on spec.pause regardless of what was still
      // alive, so a slow fight stacked three wings and a fast one left the
      // player waiting at an empty screen. Members of the wing that is
      // already out share its id and are let through, otherwise a
      // formation would block itself after its own first ship.
      if(WING_TYPES[_nx.type] && gateWings && _nx.wing && _nx.wing!==gateWing
         && liveSmallCount()>0){
        for(const s of spawnQ) if(s.wing===_nx.wing) s.time=spawnT+GATE_RETRY;
        spawnQ.sort(function(a,b){ return a.time-b.time; });
        continue;
      }
      if(WING_TYPES[_nx.type] && liveSmallCount()>=smallCap()){
        // Defer the whole wing, not just its leader, or a formation would
        // arrive in pieces once the cap bites.
        if(_nx.wing){
          for(const s of spawnQ) if(s.wing===_nx.wing) s.time=spawnT+LIVE_SMALL_RETRY;
        } else { _nx.time=spawnT+LIVE_SMALL_RETRY; }
        spawnQ.sort(function(a,b){ return a.time-b.time; });
        continue;
      }
      const _sp=spawnQ.shift();
      if(WING_TYPES[_sp.type] && _sp.wing) gateWing=_sp.wing;
      // A defector is not an enemy yet, so it never goes through mkEnemy.
      if(_sp.type==='defector'){ spawnDefector(_sp.y, _sp.spr); continue; }
      // A protected non-combatant goes into allies, not enemies. Same hull
      // out of mkEnemy, but from there the ally paths handle it: enemy
      // bolts already test against allies, and updateAllies() already
      // charges GUARD_PENALTY when something carrying guard dies.
      if(_sp.type==='protect'){ spawnProtected(_sp); continue; }
      // Verbuendetes Grosskampfschiff aus ALLY_DEFS.
      if(_sp.type==='ally'){
        const _a = mkAlly(_sp.allyId);
        // initSubsystems fehlte hier seit v90: verbuendete
        // Grosskampfschiffe in geschriebenen Wellen hatten keine.
        if(_a) initSubsystems(_a);
        if(_a && _sp.still){ _a.vy=0; _a.minY=_a.y; _a.maxY=_a.y; }
        if(_a && _sp.crossSecs){
          // Fahrt aus der Querungszeit, damit Uhr und Bild dasselbe sagen:
          // ihre Position IST der Fortschrittsbalken.
          _a.guard = true;
          _a.transit = true;
          const _gi = IMGS[_a.img];
          const _gh = _gi ? _gi.width*_a.sc*0.5 : 120;
          // crossDir 'left': in from the right edge, out on the left.
          const _toLeft = (_sp.crossDir === 'left');
          _a.x = _toLeft ? W + 20 : -20;  _a.warpX = _a.x;  _a.warp = 0;
          _a.transitEnd = _toLeft ? _gh + TRANS_EDGE_PAD : W - _gh - TRANS_EDGE_PAD;
          _a.transitV = (_a.transitEnd - _a.x) / (_sp.crossSecs*TICK_HZ);
          _a.flip = needsFlip(_a.img, _toLeft);
          guardWanted = true; guardSpawned = true;
        }
        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;
                _a.defectLock = evWillDefect(_sp.uid);
                if(_sp.defectRun) _a.defectRun = _sp.defectRun;
                if(_sp.hpMul) { _a.hp=Math.round(_a.hp*_sp.hpMul); _a.maxHp=Math.max(_a.maxHp,_a.hp); }
                allies.push(_a); }
        continue;
      }
      // Verbuendeter Jaeger.
      if(_sp.type==='allyfi'){
        const _a = mkAllySmall('fighter', currentFaction==='hol'?'vasudan':'terran',
                               _sp.spr || rnd(ROLES.ally_vas_fighters), _sp.y);
        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;
                // Wer eine Korvette durchbringt, bekommt kein Kreuzerticket.
                guardReward = (_a.type==='destroyer') ? 'destroyer'
                            : (_a.type==='corvette') ? 'corvette' : 'cruiser';
                _a.defectLock = evWillDefect(_sp.uid); allies.push(_a); }
        continue;
      }
      const _e=mkEnemy(_sp.type, _sp.spr, _sp.y);
      if(_e && _sp.flee) _e.fleeT = _sp.flee*TICK_HZ;if(_e){_e.side='enemy';_e.flip=needsFlip(_e.img,true);if(_e.type==='fighter'||_e.type==='bomber'){const _p=poseFor(_e.head,_e.flip);_e.ang=_p.ang;_e.flip=_p.flip;}_e.warpMax=_e.warp||1;initWeapons(_e);initSecAmmo(_e);initLuciShield(_e);initSubsystems(_e);assignStation(_e);applySpawnOpts(_e,_sp);_e.uid=_sp.uid;if(_sp.uid)EV_SEEN[_sp.uid]=true;_e.hunter=(waveHunt&&Math.random()<HUNT_SHARE);_e.rammer=!!_sp.rammer;enemies.push(_e);}}
    // With a boss calling for more, the queue is never empty for long, but
    // the wave still ends the moment the boss itself dies, because its
    // calls stop with it.
    // On a crossing the rocks never stop, so an empty field is never
    // reached. The escort being through is the whole condition.
    // Three ways a wave can end now. A crossing ends when the escort is
    // through, a disable job when weapons and engines are gone, and
    // everything else when the field is clear. Scenery does not count as
    // clearing work: a standing asteroid field never leaves on its own and
    // would hold the wave open forever.
    if(transitSecs>0 ? guardGone
       : (disableTarget ? disableDone()
          : (!spawnQ.length && !liveThreatCount() && !crossPending() && !evPending() && !escPending()))){
      // She made it: that is the whole objective of the wave.
      if(guardWanted && guardSpawned && !guardLost){
        guardWanted=false;
        tickets[guardReward]=(tickets[guardReward]||0)+1;
        ticketFlash=120; ticketFlashKind=guardReward;
        TICKET_MSGS.push({x:W/2,y:H/2,kind:guardReward,life:190,ml:190,rep:false});
      }
      waveOver=true;
      // The clearing beat stretches if escorts are still jumping out, the
      // jump itself always gets its full TRANS_OUT.
      waveCd=Math.max(TRANS_CLEAR+TRANS_OUT, allies.length?(allies[0].warpMax+TRANS_OUT):0);
      // startNebFade() stand hier, volle 1.6 s bevor das Feld dunkel
      // wurde: der Hintergrund loeste sich sichtbar auf waehrend der
      // Spieler noch flog. Gestartet wird jetzt aus der Dunkelheit.
      }
  }else{
    // Do not pull the player out from under a ticket he can still reach.
    // The clearing beat holds while anything is left on the field; the
    // pickups expire on their own, so this cannot stall.
    if(ITEMS.length>0 && waveCd<=TRANS_OUT+1) waveCd = TRANS_OUT+2;
    else if(--waveCd<=0) nextWave();
  }

  if(eBullets.length>120)eBullets.splice(0,eBullets.length-120);
  for(let i=eBullets.length-1;i>=0;i--){
    const b=eBullets[i];
    if(b.hom){
      if(--b.life<=0){ spawnFireball(b.x,b.y,12,16); eBullets.splice(i,1); continue; }
      // Guided rounds pick whichever friendly target is closest, so an
      // escort cannot simply be flown past. A Pegasus is not on the list:
      // with nothing to lock the round keeps its launch heading and
      // becomes an unguided shot.
      let tx=0, ty=0, bd=Infinity;
      if(canLockOn(player)){
        tx=player.x; ty=player.y;
        bd=(player.x-b.x)**2+(player.y-b.y)**2;
      }
      for(const a of allies){
        if(a.dead || a.warp>0 || a.warpOut>0) continue;
        if(!canLockOn(a)) continue;
        const d=(a.x-b.x)**2+(a.y-b.y)**2;
        if(d<bd){ bd=d; tx=a.x; ty=a.y; }
      }
      // With nothing to lock the round keeps its launch heading and
      // becomes an unguided shot. Only the steering is skipped here.
      // Skipping the rest of the loop as well used to make it a phantom:
      // it passed through every hull, which is what a Pegasus pilot saw.
      if(bd<Infinity){
        const want=Math.atan2(ty-b.y, tx-b.x);
        let cur=Math.atan2(b.vy, b.vx);
        let d=want-cur;
        while(d> Math.PI) d-=Math.PI*2;
        while(d<-Math.PI) d+=Math.PI*2;
        cur += Math.max(-b.turn, Math.min(b.turn, d));
        b.vx=Math.cos(cur)*b.spd; b.vy=Math.sin(cur)*b.spd;
      }
      if(fc%3===0) spawnSmoke(b.x,b.y,1);
    }
    b.x+=b.vx;b.y+=b.vy;
    // A flak round bursts where its fuse runs out, and the shrapnel it
    // leaves is what the run has to cross.
    if(b.fuse && --b.fuse<=0){
      flakBurst(b.x, b.y, false, b.faction);
      eBullets.splice(i,1); continue;
    }
    // Shrapnel gives out on its own rather than flying to the edge.
    if(b.eLife && --b.eLife<=0){ eBullets.splice(i,1); continue; }
    if(debrisEatsBolt(b)){ eBullets.splice(i,1); continue; }
    if(b.x<-60||b.x>W+60||b.y<-60||b.y>H+60){eBullets.splice(i,1);continue;}
    if(!b.kind && fc%4===0){
      PARTS.push({x:b.x-b.vx*0.5, y:b.y-b.vy*0.5,
        vx:-b.vx*0.10, vy:-b.vy*0.10+(Math.random()-0.5)*0.2,
        life:(6+Math.random()*6)|0, ml:0, sz:0.8+Math.random(),
        clr: b.faction==='shivan' ? '#ff8866' : '#88ffaa'});
    }
    // Crossfire between hostile factions. Same structural point as the
    // defector: a bolt can only hit what its loop actually looks at, and
    // this loop looked at the escorts and the player. The faction on the
    // bolt decides, so a Shivan round passes through Shivan hulls and
    // bites into Vasudan ones.
    if(waveFeud && b.faction){
      let eaten=false;
      for(let fi=enemies.length-1;fi>=0;fi--){
        const o=enemies[fi];
        if(o.dead || o.warp>0 || o.warpOut>0 || o.scenery) continue;
        if(o.type==='asteroid' || playerOnly(o)) continue;
        if(!o.faction || o.faction===b.faction) continue;
        const[ox,oy,ow,oh]=eBox(o);
        if(!overlap(b.x-b.w/2,b.y-b.h/2,b.w,b.h,ox,oy,ow,oh)) continue;
        if(!bulletOnHull(o,b)) continue;
        damageEnemy(o, b.dmg||(b.big?20:8), b.x, b.y, false, 'bolt');
        hullHit(b.x,b.y);
        if(b.kind==='bomb') bombBlast(b.x,b.y);
        // No points and no pickups: the player did not earn this one.
        if(o.hp<=0 && !o.dead) killEnemy(o, fi, false, false);
        eBullets.splice(i,1);
        eaten=true;
        break;
      }
      if(eaten) continue;
    }

    // Escorts are legitimate targets too. Without this an enemy bolt flies
    // straight through a friendly cruiser and only the player can be hit,
    // which made escorts effectively invulnerable to gunfire.
    if(allies.length){
      let consumed=false;
      for(let ai=allies.length-1;ai>=0;ai--){
        const a=allies[ai];
        if(a.dead || a.warp>0 || a.warpOut>0) continue;
        const[ax,ay,aw,ah]=eBox(a);
        if(!overlap(b.x-b.w/2,b.y-b.h/2,b.w,b.h,ax,ay,aw,ah)) continue;
        if(!bulletOnHull(a,b)) continue;      // impact landed on empty space
        let adm=b.dmg||(b.big?20:8);
        if(a.subs) adm=subHit(a, adm, b.x, b.y);   // escorts have them too
        a.hp-=adm;
        hullHit(b.x,b.y);
        if(b.kind==='bomb') bombBlast(b.x,b.y);
        eBullets.splice(i,1);
        consumed=true;
        break;
      }
      if(consumed) continue;
    }

    {
      const[px,py,pw,ph]=pBox();
      if(overlap(b.x-b.w/2,b.y-b.h/2,b.w,b.h,px,py,pw,ph)){
        if(!bulletOnPlayer(b)) continue;   // impact landed on empty space
        const dmg=b.dmg||(b.big?20:8);
        if(player.sh>0){
          const absorbed=Math.min(player.sh,dmg);
          player.sh-=absorbed; player.shDelay=90; player.shHit=SH_FLASH;
          shieldHit(b.x,b.y);
          if(dmg>absorbed){player.hp-=dmg-absorbed;hullHit(b.x,b.y);}
        } else {
          player.hp-=dmg; hullHit(b.x,b.y);
        }
        if(b.kind==='bomb') bombBlast(b.x,b.y);
        eBullets.splice(i,1);if(player.hp<=0)playerDie();}}}

  for(let i=pBullets.length-1;i>=0;i--){
    const b=pBullets[i];b.x+=b.vx; if(b.vy) b.y+=b.vy;
    // A gun with a limited reach: the bolt gives out on its own. Without
    // pLife it runs to the edge, which is what every bolt used to do.
    // The fuse comes first: a round that bursts by itself has to do it
    // before the reach runs out, or it would simply vanish instead.
    if(b.fuse && --b.fuse<=0){
      if(b.flak) flakBurst(b.x, b.y, true, b.fac);
      else {
        const fw=priDef(b.wpn);
        shardBurst(b.x, b.y, fw.shards, b.dmg*fw.shardDmg,
                   fw.shardSpd, fw.shardRange, fw.col, fw.glow);
      }
      pBullets.splice(i,1); continue;
    }
    if(b.pLife){ if(--b.pLife<=0){ pBullets.splice(i,1); continue; } }
    if(debrisEatsBolt(b)){ pBullets.splice(i,1); continue; }
    // Bolts can now travel in any direction, so the left edge needs a
    // bound too. Without it a shot fired backwards is never cleaned up.
    if(b.x>W+40||b.x<-40||b.y<-40||b.y>H+40){pBullets.splice(i,1);continue;}
    // Faint glowing trail behind every laser bolt
    if(!b.sec && fc%3===0){
      PARTS.push({x:b.x-b.vx*0.6, y:b.y-b.vy*0.6,
        vx:-b.vx*0.10, vy:-b.vy*0.10+(Math.random()-0.5)*0.25,
        life:(7+Math.random()*7)|0, ml:0, sz:0.9+Math.random()*1.1,
        clr: b.ally ? (b.fac==='vasudan'?'#ffd257':'#7fc4ff') : (b.col||'#ccff88')});
    }
    let hit=false;
    // Incoming bombs can be shot down
    for(let k=eBullets.length-1;k>=0;k--){
      const eb=eBullets[k];
      if(!eb.hp) continue;
      if(overlap(b.x-b.w/2,b.y-b.h/2,b.w,b.h,eb.x-eb.w/2,eb.y-eb.h/2,eb.w,eb.h)){
        if(eb.kind==='bomb'){ bombBlast(eb.x,eb.y); STATS.bombsShot++; }
        else { spawnFireball(eb.x,eb.y,18,20);
               spawnDebris(eb.x,eb.y,8,255,200,80,255,120,0,true); }
        STATS.hits++;
        eBullets.splice(k,1); pBullets.splice(i,1); hit=true; break;
      }
    }
    if(hit) continue;
    for(let j=enemies.length-1;j>=0;j--){
      const e=enemies[j];const[ex,ey,ew,eh]=eBox(e);
      if(overlap(b.x-b.w/2,b.y-b.h/2,b.w,b.h,ex,ey,ew,eh)){
        if(!bulletOnHull(e,b)) continue;   // impact landed on empty space
        if(b.ally && playerOnly(e)) continue;   // allied fire passes through
        laserHit(b.x,b.y);STATS.hits++;e.shotAt=true;damageEnemy(e,(b.dmg||22),b.x,b.y,!b.ally,'bolt');
        if(b.flak){
          flakBurst(b.x, b.y, true, b.fac);
          pBullets.splice(i,1); hit=true;
        } else if(b.fuse!==undefined && b.fuse>0 && b.wpn){
          const fw=priDef(b.wpn);
          if(fw.shards) shardBurst(b.x, b.y, fw.shards, b.dmg*fw.shardDmg,
                                   fw.shardSpd, fw.shardRange, fw.col, fw.glow);
          pBullets.splice(i,1); hit=true;
        } else {
          pBullets.splice(i,1); hit=true;
        }
        if(e.hp<=0&&!e.dead){ killEnemy(e, j, true, true); }
        if(hit) break;
        continue;}}if(hit)continue;}

  assignAttackRoles(enemies);
  assignAttackRoles(allies);
  for(let i=enemies.length-1;i>=0;i--){
    const e=enemies[i];
    if(e.type==='fighter'||e.type==='bomber'){
      if(e.warp>0){
        e.warp--;
        e.x-=0.4;
        const wb=shipBound(e);
        e.y=Math.max(HUD_H+wb,Math.min(H-wb,e.y));
        const wp=poseFor(e.head, e.flip);
        e.ang=wp.ang; e.flip=wp.flip;
        continue;
      }
      if(e.shHit>0) e.shHit--;
      if(e.shDelay>0) e.shDelay--;
      else if(e.maxSh && e.sh<e.maxSh) e.sh=Math.min(e.maxSh,e.sh+e.shRe);
      const tgt=flySmall(e);
      if(--e.fT<=0) smallFire(e,tgt);
      fireSecondaries(e, WPN[e.type]);
      // No exit to the left any more. They stay until they are destroyed.
    }
    else if(e.type==='freighter'){
      if(e.warp>0){ e.warp--; e.x-=0.3; continue; }
      // Being shot at, not damage, is what sends it running. The first
      // version asked whether the hull was below maximum, which a drifting
      // asteroid answers just as well as a laser: in the test the freighter
      // bolted every time it clipped a rock. shotAt is set only where a
      // bullet actually strikes.
      if(!e.fleeing && e.shotAt && !e.escaping){ e.fleeing=true; e.vx=-1.9; }
      e.x+=e.vx;
      if(e.x<-140){
        // It got away. The briefing for Small Deadly Space is explicit
        // that this is a defeat, so it is charged like one.
        if(e.runner){
          fleeEscaped++;
          score = Math.max(0, score - RUNNER_PENALTY);
          if(STATS.runnersEscaped==null) STATS.runnersEscaped = 0;
          STATS.runnersEscaped++;
        }
        enemies.splice(i,1); continue;
      }
    }
    else if(e.type==='container'){
      if(e.warp>0){ e.warp--; continue; }
      // Nothing. A container drifts with the field and waits.
    }
    else if(e.type==='sentry'){
      if(e.warp>0){ e.warp--; continue; }
      // The platform cannot move, but it can turn. Facing the player is
      // what lets smallFire() clear its own bearing cone.
      e.head=Math.atan2(player.y-e.y, player.x-e.x);
      if(--e.fT<=0) smallFire(e, player);
    }
    else if(e.type==='asteroid'){
      e.x+=e.vx;e.y+=e.vy;e.rot+=e.rotS;
      if(e.y<20||e.y>H-20)e.vy*=-1;
      if(e.x<-60){enemies.splice(i,1);continue;}}
    else if(e.type==='corvette'||e.type==='destroyer'){
      if(e.warp>0){e.warp--;e.x-=0.2;continue;}
      if(runFlee(e,i)) continue;
      // Wie beim Kreuzer: ein Rammkurs faehrt seinen eigenen Kurs.
      if(!e.capRam){
        if(e.x>e.targetX)e.x=Math.max(e.targetX,e.x-0.6);
        if(!subOK(e,'engines')) e.vy=0;
        e.y+=e.vy;if(e.y<e.minY||e.y>e.maxY)e.vy*=-1;
      }
      e.y=Math.max(HUD_H+18,Math.min(H-18,e.y));
      if(e.x<-300){enemies.splice(i,1);continue;}
      e.y=Math.max(e.minY,Math.min(e.maxY,e.y));
      capitalFire(e);
    }
    else if(e.type==='cruiser'){
      if(e.warp>0){
        e.warp--;
        e.x-=0.3;
        continue;
      }
      if(runFlee(e,i)) continue;
      // Ein Rammkurs steuert sich selbst, in tickCapRam(). Die Fahrt zur
      // Kampfposition zog ihn unabhaengig davon 0.8 Punkte je Schritt nach
      // links, also schneller, als der Rammkurs in der Hoehe nachkam - so
      // zog er schraeg am Ziel vorbei. Und weil targetX dabei auf null
      // steht und Math.max(null, x) dasselbe ist wie Math.max(0, x), endete
      // die Fahrt bei x = 0: der linke Bildrand, an dem er hing.
      if(!e.capRam){
        // Zu Kampfposition gleiten
        if(e.x>e.targetX) e.x=Math.max(e.targetX,e.x-0.8);
        if(!subOK(e,'engines')) e.vy=0;
        else e.vy=e.vy*0.985+(e.vy>0?1:-1)*0.015*0.6;
        e.y+=e.vy;if(e.y<e.minY||e.y>e.maxY)e.vy*=-1;
      }
      e.y=Math.max(HUD_H+18,Math.min(H-18,e.y));
      if(e.x<-200){enemies.splice(i,1);continue;}
      e.y=Math.max(e.minY,Math.min(e.maxY,e.y));
      if(e.x>W+200){enemies.splice(i,1);continue;}
      capitalFire(e);}
    else if(e.type==='boss'){
      if(e.warp>0){
        e.warp--;
        e.x-=0.3;
        continue;
      }
      // Failsafe only while the boss is still stuck off screen right.
      // This counter used to run all the time and zeroed the hull in the
      // middle of a fight: 1800 steps was 30 seconds at 60 Hz,
      // seconds, but only 18 at 100 Hz.
      if(e.x > W+20){
        e.stuckTimer = (e.stuckTimer||0) + 1;
        if(e.stuckTimer > 900) e.x = e.targetX;   // place it instead of destroying it
      } else e.stuckTimer = 0;

      // Approach. The step needs a floor, otherwise the boss only
      // approaches its station asymptotically and never arrives.
      if(e.x - e.targetX > 1.5){
        e.x = Math.max(e.targetX, e.x - Math.max(0.25, Math.min(1.5,(e.x-e.targetX)*0.04)));
      } else {
        e.x = e.targetX;
      }

      // Bosses had no reason to consult this before, since nothing gave
      // them a deadline. Losing their guns does.
      if(runFlee(e,i)) continue;
      if(e.hp<e.maxHp*.5&&e.phase===1){ e.phase=2; e.fireBoost=0.62; }
      if(!subOK(e,'engines')) e.vy=0;
      e.y+=e.vy*(e.phase===2?1.3:1.0);
      if(e.y<e.minY||e.y>e.maxY)e.vy*=-1;
      e.y=Math.max(e.minY,Math.min(e.maxY,e.y));

      // Fire as soon as the boss is on screen. This call used to sit in the
      // else branch of the approach and was therefore never reached.
      if(e.x < W+40) capitalFire(e);}
    updateBeams(e);
    // Ramming no longer costs anything, in either direction. Hulls pass
    // through one another, weapons are the only thing that does damage.
  }
  // Cleanup: ships that have escaped the play field
  for(let ci=enemies.length-1;ci>=0;ci--){
    const ce=enemies[ci];
    if(ce.x < -400 || ce.x > W+600 || ce.y < -400 || ce.y > H+400){
      enemies.splice(ci,1);
    }
  }

}
