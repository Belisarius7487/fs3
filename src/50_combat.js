// ── ASTEROIDEN ────────────────────────────────────────────────
// Vorher war jeder Brocken dasselbe fest verdrahtete Elfeck in einem
// flachen Braun, nur anders gedreht und skaliert. Jetzt werden beim Laden
// ein Dutzend Varianten in Offscreen-Canvases gebacken, mit ausgewuerfelter
// Silhouette, Kratern und Koernung. Jeder Brocken zieht eine davon und
// dreht sie, das ist ein drawImage. Das Licht kommt getrennt darueber und
// dreht nicht mit.
const AST_VARIANTS = 12;
const AST_BAKE_PX = 96;
const AST_RIM = 0.42;
const AST_TEX = [];

function buildAsteroids(){
  const S = AST_BAKE_PX, cx = S/2, cy = S/2, R = S*0.46;
  for(let v=0; v<AST_VARIANTS; v++){
    const c = document.createElement('canvas');
    c.width = S; c.height = S;
    const g = c.getContext('2d');
    const n = 9+((Math.random()*5)|0);
    const pts = [];
    for(let i=0;i<n;i++){
      const a = i/n*Math.PI*2 + (Math.random()-0.5)*0.18;
      const r = R*(0.62+Math.random()*0.38);
      pts.push([cx+Math.cos(a)*r, cy+Math.sin(a)*r]);
    }
    const path = function(gg){
      gg.beginPath();
      gg.moveTo(pts[0][0], pts[0][1]);
      for(let i=1;i<n;i++) gg.lineTo(pts[i][0], pts[i][1]);
      gg.closePath();
    };
    path(g);
    g.fillStyle = '#6b5a46';
    g.fill();
    g.save();
    path(g); g.clip();
    // Grossflaechige Tonwertunterschiede zuerst. Ohne die bleibt der
    // Brocken auch mit Kratern eine einfarbige Flaeche.
    for(let bl=0; bl<5; bl++){
      const a = Math.random()*Math.PI*2, dd = R*Math.sqrt(Math.random())*0.9;
      const br = R*(0.30+Math.random()*0.45);
      const bx = cx+Math.cos(a)*dd, by = cy+Math.sin(a)*dd;
      const gr = g.createRadialGradient(bx,by,0,bx,by,br);
      const up = Math.random()<0.5;
      gr.addColorStop(0, up ? 'rgba(140,122,96,0.30)' : 'rgba(52,42,31,0.30)');
      gr.addColorStop(1, up ? 'rgba(140,122,96,0)'    : 'rgba(52,42,31,0)');
      g.fillStyle = gr;
      g.fillRect(bx-br, by-br, br*2, br*2);
    }
    // Krater: dunkle Mulde mit hellerem Wall auf einer Seite.
    const nc = 3+((Math.random()*4)|0);
    for(let k=0;k<nc;k++){
      // sqrt, sonst haeufen sich die Krater in der Mitte: gleichmaessig
      // ueber den Radius ist nicht gleichmaessig ueber die Flaeche.
      const a = Math.random()*Math.PI*2, dd = R*Math.sqrt(Math.random())*0.72;
      const kx = cx+Math.cos(a)*dd, ky = cy+Math.sin(a)*dd;
      const kr = R*(0.10+Math.random()*0.17);
      g.fillStyle = 'rgba(56,45,33,0.72)';
      g.beginPath();
      g.ellipse(kx, ky, kr, kr*(0.68+Math.random()*0.32), Math.random()*Math.PI, 0, Math.PI*2);
      g.fill();
      g.strokeStyle = 'rgba(154,136,110,0.48)';
      g.lineWidth = Math.max(1, kr*0.16);
      g.beginPath(); g.arc(kx, ky, kr, -2.5, -0.5); g.stroke();
    }
    // Koernung. Ohne die bleibt auch ein Krater nur ein Fleck.
    for(let sp=0; sp<150; sp++){
      const a = Math.random()*Math.PI*2, dd = R*Math.sqrt(Math.random());
      g.fillStyle = (Math.random()<0.45) ? 'rgba(172,154,124,0.32)'
                                         : 'rgba(44,35,26,0.38)';
      const ss = 0.6+Math.random()*1.7;
      g.fillRect(cx+Math.cos(a)*dd, cy+Math.sin(a)*dd, ss, ss);
    }
    g.restore();
    g.strokeStyle = '#3a2e22';
    g.lineWidth = 1.4;
    path(g); g.stroke();
    AST_TEX.push({c:c, pts:pts, R:R, S:S});
  }
}
buildAsteroids();

// Randlicht in Bildschirmkoordinaten. Auf die gedrehte Silhouette
// beschnitten, damit der Bogen bei den Einbuchtungen nicht danebenliegt,
// aber selbst nicht mitgedreht - der Brocken taumelt, das Licht steht.
function drawRockLight(e, r){
  const t = AST_TEX[e.tex||0];
  if(!t) return;
  const la = lightAngleAt(e.x, e.y);
  const k = r/t.R;
  ctx.save();
  ctx.translate(e.x, e.y);
  ctx.rotate(e.rot);
  ctx.beginPath();
  ctx.moveTo((t.pts[0][0]-t.S/2)*k, (t.pts[0][1]-t.S/2)*k);
  for(let i=1;i<t.pts.length;i++) ctx.lineTo((t.pts[i][0]-t.S/2)*k, (t.pts[i][1]-t.S/2)*k);
  ctx.closePath();
  ctx.clip();
  ctx.rotate(-e.rot);
  ctx.translate(-e.x, -e.y);
  // Dunkler Terminator auf der Schattenseite.
  ctx.strokeStyle = 'rgba(16,13,10,0.50)';
  ctx.lineWidth = r*0.34;
  ctx.beginPath(); ctx.arc(e.x, e.y, r*0.88, la-1.05, la+1.05); ctx.stroke();
  // Heller Saum auf der Lichtseite.
  ctx.globalCompositeOperation = 'lighter';
  ctx.strokeStyle = 'rgba(212,196,164,'+AST_RIM+')';
  ctx.lineWidth = Math.max(1.4, r*0.20);
  ctx.beginPath(); ctx.arc(e.x, e.y, r*0.86, la+Math.PI-1.0, la+Math.PI+1.0); ctx.stroke();
  ctx.restore();
}

function debSpan(d){ return Math.max(d.sw, d.sh)*d.sc; }

function debRamDmg(d, maxHp){
  const t = Math.max(0, Math.min(1, (debSpan(d)-12)/48));
  return Math.max(1, Math.round((maxHp||100)*(DEB_PCT_MIN+(DEB_PCT_MAX-DEB_PCT_MIN)*t)));
}

// Rotation safe coarse box: a piece tumbles, so the long side is used on
// both axes. Same rule as everywhere else, the box may only be too big.
function debBox(d){
  const s = Math.max(d.sw, d.sh)*d.sc;
  return [d.x-s*0.5, d.y-s*0.5, s, s];
}

// Mask lookup restricted to one cut out. The parent mask is reused with
// the source rectangle folded into the mapping, so a piece keeps the
// exact silhouette it had while it was still part of the ship.
function onDebris(d, wx, wy){
  const img = IMGS[d.key];  if(!img) return true;
  const m = getMask(d.key); if(!m)   return true;
  const pw = d.sw*d.sc, ph = d.sh*d.sc;
  let ox = wx-d.x, oy = wy-d.y;
  if(d.ang){
    const ca=Math.cos(-d.ang), sa=Math.sin(-d.ang);
    const rx=ox*ca-oy*sa, ry=ox*sa+oy*ca; ox=rx; oy=ry;
  }
  const lx = ox/pw+0.5, ly = oy/ph+0.5;
  if(lx<0||lx>=1||ly<0||ly>=1) return false;
  // Outside the torn edge there is nothing to hit, whatever the parent
  // mask says: the clip path and the hit test have to agree.
  if(d.out && !inOutline(d.out, lx-0.5, ly-0.5)) return false;
  const mx = (((d.sx+lx*d.sw)/img.width)*m.w)|0;
  const my = (((d.sy+ly*d.sh)/img.height)*m.h)|0;
  if(mx<0||mx>=m.w||my<0||my>=m.h) return false;
  return m.bits[my*m.w+mx]===1;
}

function pushDebris(p){
  debris.push(p);
  if(debris.length>DEBRIS_MAX) debris.splice(0, debris.length-DEBRIS_MAX);
}

// A rectangular cut reads as a rectangle, which is the one thing a torn
// hull never looks like. Each piece therefore carries an irregular
// outline in its own normalised space, used both to clip the drawing and
// to answer collision, so what is seen and what is hit stay the same
// shape.
function tornOutline(){
  const n = 7+((Math.random()*4)|0);
  const pts = [];
  for(let i=0;i<n;i++){
    const a = (i/n)*Math.PI*2 + (Math.random()-0.5)*0.28;
    const r = 0.30+Math.random()*0.20;      // 0.30..0.50 of the cut box
    pts.push([Math.cos(a)*r, Math.sin(a)*r]);
  }
  return pts;
}

function inOutline(pts, nx, ny){
  let inside = false;
  for(let i=0, j=pts.length-1; i<pts.length; j=i++){
    const xi=pts[i][0], yi=pts[i][1], xj=pts[j][0], yj=pts[j][1];
    if(((yi>ny)!==(yj>ny)) && (nx < (xj-xi)*(ny-yi)/((yj-yi)||1e-9)+xi)) inside=!inside;
  }
  return inside;
}

const DEB_AMB_VX = -0.25;      // ambient drift once the blast has bled off
const DEB_DRAG   = 0.985;

// The biggest ships are the ones whose pieces looked wrong: a share of a
// 900 pixel hull is a slab. The cut is capped at a real on screen size
// instead, so a destroyer sheds many plates rather than a few doors.
const DEB_MAX_PX = 38;

// How much solid hull sits inside a candidate rectangle. A rectangle over
// a transparent corner of the sprite produced a piece that was nothing
// but a scorched outline around empty space, which is the bug this
// answers. Sampled rather than counted, because this runs on every death.
function cutCoverage(key, sx, sy, sw, sh){
  const m = getMask(key); if(!m) return 1;
  const img = IMGS[key];
  let hit=0;
  for(let i=0;i<64;i++){
    const fx=(sx+Math.random()*sw)/img.width, fy=(sy+Math.random()*sh)/img.height;
    const mx=(fx*m.w)|0, my=(fy*m.h)|0;
    if(mx>=0&&mx<m.w&&my>=0&&my<m.h&&m.bits[my*m.w+mx]===1) hit++;
  }
  return hit/64;
}

function cutPiece(key, sc, gen, wFrac, hFrac, hp){
  const img = IMGS[key]; if(!img) return null;
  let sw = Math.max(8, Math.round(img.width *wFrac));
  let sh = Math.max(8, Math.round(img.height*hFrac));
  // Cap the piece at a sensible size on screen, keeping its proportions.
  const span = Math.max(sw,sh)*sc;
  if(span > DEB_MAX_PX){
    const k = DEB_MAX_PX/span;
    sw = Math.max(8, Math.round(sw*k));
    sh = Math.max(8, Math.round(sh*k));
  }
  // Look for a cut that is mostly hull. Keep the best of a few tries
  // rather than insisting, so this always terminates.
  let bx=0, by=0, best=-1;
  for(let t=0;t<10;t++){
    const cx=Math.floor(Math.random()*Math.max(1,img.width -sw));
    const cy=Math.floor(Math.random()*Math.max(1,img.height-sh));
    const cov=cutCoverage(key,cx,cy,sw,sh);
    if(cov>best){ best=cov; bx=cx; by=cy; }
    if(cov>=0.62) break;
  }
  if(best < 0.30) return null;      // nothing solid here, no piece at all
  return {key:key, sc:sc, gen:gen, sw:sw, sh:sh, sx:bx, sy:by,
    hp:hp, maxHp:hp, ang:Math.random()*Math.PI*2,
    rotS:(Math.random()-0.5)*0.02, x:0, y:0, vx:0, vy:0,
    out:tornOutline(), heat:1, ember:0};
}

// Fed from triggerExpl, so every death path leaves a wreck without each
// call site having to remember to do it.
function spawnWreck(src, type, x, y){
  if(!src || !src.img || !IMGS[src.img]) return;
  const sc = src.sc || 0.3;
  let n = 2;
  if(type==='cruiser'||type==='corvette') n = 4;
  else if(type==='destroyer'||type==='boss') n = 6;
  for(let i=0;i<n;i++){
    const p = cutPiece(src.img, sc, 0, 0.18+Math.random()*0.17,
                       0.30+Math.random()*0.35, DEBRIS_HP);
    if(!p) continue;
    // Thrown by the blast, not released into a drift. Heavier pieces come
    // off slower, so a fighter scatters and a destroyer sheds slabs.
    const mass = Math.max(0, Math.min(1, (debSpan(p)-12)/48));
    const spd  = (2.4+Math.random()*3.0)*(1-0.5*mass);
    const a    = Math.random()*Math.PI*2;
    p.x = x+(Math.random()-0.5)*p.sw*sc;
    p.y = y+(Math.random()-0.5)*p.sh*sc;
    p.vx = Math.cos(a)*spd + DEB_AMB_VX; p.vy = Math.sin(a)*spd;
    p.rotS *= 3.5+Math.random()*2.5;
    pushDebris(p);
  }
}

// A field that was fought over before the player ever arrived.
function seedWreckField(n, keys, sc){
  for(let i=0;i<n;i++){
    const p = cutPiece(keys[(Math.random()*keys.length)|0], sc, 0,
                       0.16+Math.random()*0.18, 0.28+Math.random()*0.34, DEBRIS_HP);
    if(!p) continue;
    p.x = W+40+Math.random()*W;
    p.y = HUD_H+20+Math.random()*(H-HUD_H-40);
    p.vx = -(0.5+Math.random()*0.9); p.vy = (Math.random()-0.5)*0.5;
    pushDebris(p);
  }
}

function breakDebris(i){
  const d = debris[i];
  spawnFireball(d.x, d.y, debSpan(d)*0.5+8, 22);
  spawnDebris(d.x, d.y, 8, 200,190,175, 110,95,80, false);
  debris.splice(i,1);
  // A large piece comes apart instead of vanishing. One generation only,
  // otherwise a dying destroyer fills the screen with confetti.
  if(d.gen===0 && debSpan(d)>DEB_SMALL_PX){
    const hp = Math.round(DEBRIS_HP*0.55);
    for(let k=0;k<2;k++){
      const a=Math.random()*Math.PI*2, spd=0.4+Math.random()*0.8;
      const nsx=d.sx+(k?Math.floor(d.sw/2):0);
      const nsw=Math.max(6,Math.floor(d.sw/2)), nsh=Math.max(6,Math.floor(d.sh*0.7));
      if(cutCoverage(d.key, nsx, d.sy, nsw, nsh) < 0.30) continue;
      pushDebris({key:d.key, sc:d.sc, gen:1,
        sx:nsx, sy:d.sy, sw:nsw, sh:nsh,
        hp:hp, maxHp:hp, ang:d.ang, rotS:(Math.random()-0.5)*0.08,
        x:d.x, y:d.y, vx:d.vx+Math.cos(a)*spd, vy:d.vy+Math.sin(a)*spd,
        out:tornOutline(), heat:Math.max(d.heat,0.75), ember:0});
    }
  }
}

function updateDebris(){
  for(let i=debris.length-1;i>=0;i--){
    const d = debris[i];
    // The blast component bleeds off toward the ambient drift, the spin
    // settles with it. Without this a piece keeps its ejection speed for
    // ever and leaves the field before it can matter.
    d.vx = (d.vx-DEB_AMB_VX)*DEB_DRAG + DEB_AMB_VX;
    d.vy *= DEB_DRAG;
    d.rotS *= 0.995;
    d.x += d.vx; d.y += d.vy; d.ang += d.rotS;
    if(d.heat>0){
      d.heat -= 0.0022;                      // glowing to cold over ~7 s
      if(d.heat<0) d.heat = 0;
    }
    // Embers off the trailing edge while the metal is still hot.
    if(d.heat>0.08 && --d.ember<=0){
      d.ember = 2+((Math.random()*4)|0);
      const s0 = debSpan(d)*0.42;
      const a0 = Math.random()*Math.PI*2;
      const hot = d.heat;
      PARTS.push({x:d.x+Math.cos(a0)*s0, y:d.y+Math.sin(a0)*s0,
        vx:d.vx*0.35+(Math.random()-0.5)*0.5,
        vy:d.vy*0.35+(Math.random()-0.5)*0.5,
        life:(14+Math.random()*22)|0, ml:0, sz:0.8+Math.random()*1.4,
        clr: hot>0.6 ? '#ffd27f' : (hot>0.3 ? '#ff9a3c' : '#c4521e')});
    }
    const s = debSpan(d);
    if(d.x<-80-s || d.x>W+260+s || d.y<-80-s || d.y>H+80+s){ debris.splice(i,1); continue; }
    if(d.hp<=0){ breakDebris(i); continue; }

    const b = debBox(d);
    const probe = {x:d.x, y:d.y, w:s, h:s, vx:d.vx, vy:d.vy};
    let struck = false;

    if(GS==='playing' && player.hp>0){
      const pb = pBox();
      if(overlap(b[0],b[1],b[2],b[3],pb[0],pb[1],pb[2],pb[3]) && bulletOnPlayer(probe)){
        const dm = debRamDmg(d, player.maxHp);
        if(player.sh>0){
          const abs=Math.min(player.sh,dm);
          player.sh-=abs; player.shDelay=90; player.shHit=SH_FLASH; shieldHit(d.x,d.y);
          if(dm>abs){ player.hp-=dm-abs; hullHit(d.x,d.y); }
        } else { player.hp-=dm; hullHit(d.x,d.y); }
        struck = true;
        if(player.hp<=0) playerDie();
      }
    }
    if(!struck) for(const t of allies){
      if(t.dead||t.warp>0||t.warpOut>0) continue;
      const tb=eBox(t);
      if(overlap(b[0],b[1],b[2],b[3],tb[0],tb[1],tb[2],tb[3]) && bulletOnHull(t,probe)){
        t.hp -= debRamDmg(d,t.maxHp); hullHit(d.x,d.y); struck=true; break;
      }
    }
    if(!struck) for(const t of enemies){
      if(t.dead||t.type==='asteroid'||t.warp>0) continue;
      const tb=eBox(t);
      if(overlap(b[0],b[1],b[2],b[3],tb[0],tb[1],tb[2],tb[3]) && bulletOnHull(t,probe)){
        damageEnemy(t, debRamDmg(d,t.maxHp), d.x, d.y, false, 'bolt'); struck=true; break;
      }
    }
    if(struck) breakDebris(i);
  }
}

// Bolts from either side stop at wreckage. It is cover, and it is cover
// for whoever happens to be behind it.
function debrisEatsBolt(b){
  for(let i=debris.length-1;i>=0;i--){
    const d = debris[i];
    const bx = debBox(d);
    if(!overlap(b.x-b.w/2, b.y-b.h/2, b.w, b.h, bx[0],bx[1],bx[2],bx[3])) continue;
    if(!onDebris(d, b.x, b.y)) continue;
    d.hp -= (b.dmg||8);
    spawnFireball(b.x, b.y, 7, 10);
    if(d.hp<=0) breakDebris(i);
    return true;
  }
  return false;
}

function outlinePath(d, w, h){
  ctx.beginPath();
  ctx.moveTo(d.out[0][0]*w, d.out[0][1]*h);
  for(let i=1;i<d.out.length;i++) ctx.lineTo(d.out[i][0]*w, d.out[i][1]*h);
  ctx.closePath();
}

// The nebula is drawn as a haze that thickens with distance from the
// player, using the same range the guns use. What you cannot see is
// exactly what cannot see you, so the picture and the rule are one thing.
// The storm garbles the instruments rather than switching them off. The
// already rendered strip is torn into slices and shifted, so what breaks
// up is the actual readout. The clock and the two buttons are left
// untouched: a pilot who cannot pause or reach the settings during a
// three second outage is being punished by the interface, not the storm.
// Everything on the strip is garbled except three things. The clock is
// spared because a pilot has to be able to read it, and the two buttons
// because losing pause and settings for three seconds is the interface
// punishing the player, not the storm. SCORE sits directly above TIME in
// the same column, so the protection is a row band, not a column: rows
// below TIME_Y keep their left edge, everything above is torn from x=4.
const EMP_RIGHT_KEEP = 82;         // measured back from the right edge
const EMP_TIME_Y     = 36;         // top of the clock row
const EMP_TIME_X     = 80;         // right edge of the clock readout
function drawEmpHudGlitch(){
  if(empOut<=0) return;
  const x1 = W-EMP_RIGHT_KEEP;
  ctx.save();
  ctx.beginPath(); ctx.rect(0,0,x1,HUD_H); ctx.clip();
  for(let y=0;y<HUD_H;y+=3){
    const x0 = (y+3>EMP_TIME_Y) ? EMP_TIME_X : 4;
    const gw = x1-x0;
    if(gw<=0) continue;
    const off = ((Math.sin(fc*0.33+y*0.62)*4.5) + (Math.random()-0.5)*5)|0;
    if(!off) continue;
    try{
      ctx.drawImage(CVS,
        Math.round(x0*RES_X), Math.round(y*RES_Y),
        Math.round(gw*RES_X), Math.round(3*RES_Y),
        x0+off, y, gw, 3);
    }catch(err){}
  }
  // Colour fringe and dropped rows on top of the tearing.
  ctx.globalCompositeOperation='lighter';
  ctx.fillStyle='rgba(0,120,150,0.10)';
  ctx.fillRect(2,0,x1-4,EMP_TIME_Y);
  ctx.fillRect(EMP_TIME_X,EMP_TIME_Y,x1-EMP_TIME_X,HUD_H-EMP_TIME_Y);
  ctx.globalCompositeOperation='source-over';
  ctx.fillStyle='rgba(0,0,6,0.55)';
  for(let k=0;k<3;k++){
    const y=((fc*(3+k*4)+k*23)%HUD_H)|0;
    const x0=(y+2>EMP_TIME_Y)?EMP_TIME_X:4;
    ctx.fillRect(x0,y,x1-x0,2);
  }
  if(fc%40<14){
    ctx.fillStyle='#ffdd44'; ctx.font=thLabel(9);
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText('SENSOR FAULT', (EMP_TIME_X+x1)/2, (HUD_H/2)|0);
    ctx.textAlign='left'; ctx.textBaseline='top';
  }
  ctx.restore();
}

// The player's own vortex, driven by the beat that is running. Same
// sheet, same frame indexing as every other warp in the game, so it is
// the animation the player already recognises and not a second effect.
// A capital ship coming apart moves the air, so to speak. The wave is a
// ring that expands once, shoves whatever small it passes through and
// scorches it lightly. Capitals are not moved and not hurt by it: they
// are too massive for the shove to read, and an escort already taking
// fire from three directions does not need a fourth.
const SHOCKS = [];
// Raised from 0.90. Total travel is impulse/(1-decay), so 0.93 turns the
// same impulse into roughly half again as much distance: the shove was
// technically there before and simply too small to read.
const SHOCK_DECAY = 0.93;

// Screen shake. The game had none at all, which is most of the reason a
// capital ship coming apart landed as quietly as it did.
let shakeT = 0, shakeMag = 0;
// Bildschirmwackeln abgeschaltet. Bei jeder Explosion zu wackeln ist auf
// Dauer eher stoerend als wirkungsvoll. Eine Zeile statt neun Aufrufen,
// damit es sich mit einem Schnitt zurueckholen laesst.
const SHAKE_ON = false;
function addShake(mag, dur){
  if(!SHAKE_ON) return;
  shakeMag = Math.max(shakeMag, mag);
  shakeT   = Math.max(shakeT, dur);
}

// Every bomb detonation, wherever it happens. This used to be written out
// inside the branch that hits an escort, so a bomb landing on the player
// or shot down in flight produced nothing at all, and that is the only
// kind of bomb detonation most of a run contains.
function bombBlast(x, y){
  spawnFireball(x,y,52,44);
  spawnRing(x,y,86,36,4,255,225,170);
  spawnRing(x,y,52,52,2,255,255,215);
  spawnDebris(x,y,24,255,200,80,255,120,0,true);
  spawnSmoke(x,y,11);
  spawnShock(x,y,86,2.4,0.018);
  addShake(5,22);
}

// 46 Schritte waren 0.46 s. Zusammen mit einer Deckkraft von (1-t)^2 war
// die Welle schon halb durchsichtig, bevor der Ring ueberhaupt Groesse
// hatte - daher der weiche Eindruck. 66 Schritte und eine Kurve, die das
// erste Viertel auf voller Helligkeit haelt, geben ihr die Wucht.
const SHOCK_LIFE = 66;
const SHOCK_SPARK_PER = 12;   // ein Funke je 12 px Endradius

function spawnShock(x, y, rMax, force, pct){
  // Die Funken werden einmal beim Entstehen ausgewuerfelt und reiten
  // dann auf der Front mit, statt jedes Bild neu gestreut zu werden.
  const n = Math.max(5, (rMax/SHOCK_SPARK_PER)|0);
  const sparks = [];
  for(let i=0;i<n;i++){
    sparks.push({a: Math.random()*Math.PI*2,
                 o: 0.86+Math.random()*0.26,      // Versatz zur Front
                 l: 5+Math.random()*13,           // Strichlaenge
                 w: 0.8+Math.random()*1.4});
  }
  SHOCKS.push({x:x, y:y, r:0, rMax:rMax, force:force, pct:pct,
               spd:rMax/SHOCK_LIFE, hit:[], sparks:sparks});
}

function shockPush(o, s, mass){
  if(s.hit.indexOf(o)>=0) return;
  const dx=o.x-s.x, dy=o.y-s.y;
  const d=Math.hypot(dx,dy)||1;
  if(d>s.r || d<s.r-34) return;          // only the passing band
  s.hit.push(o);
  const fall = 1-Math.min(1, d/s.rMax);
  const p = s.force*fall/mass;
  o.pvx = (o.pvx||0)+dx/d*p;
  o.pvy = (o.pvy||0)+dy/d*p;
  return fall;
}

function updateShocks(){
  for(let i=SHOCKS.length-1;i>=0;i--){
    const s=SHOCKS[i];
    s.r += s.spd;
    if(GS==='playing' && player.hp>0 && !inJump()){
      const f=shockPush(player, s, 1);
      if(f){ player.hp -= Math.max(1, Math.round(player.maxHp*s.pct*f)); hullHit(player.x,player.y);
             if(player.hp<=0) playerDie(); }
    }
    for(const e of enemies){
      if(e.dead||e.warp>0) continue;
      if(e.type==='asteroid'){ shockPush(e, s, 1.6); continue; }
      if(e.type!=='fighter'&&e.type!=='bomber') continue;
      const f=shockPush(e, s, 1);
      if(f) damageEnemy(e, Math.max(1,Math.round(e.maxHp*s.pct*f)), e.x, e.y, false, 'bolt');
    }
    for(const a of allies){ if(a.small && !a.dead) shockPush(a, s, 1); }
    for(const d of debris) shockPush(d, s, 0.8);
    if(s.r>=s.rMax) SHOCKS.splice(i,1);
  }
}

// The shove itself: a decaying offset, so the push reads as being thrown
// and then recovering rather than as a teleport.
function applyPush(o){
  if(!o.pvx && !o.pvy) return;
  o.x += o.pvx; o.y += o.pvy;
  o.pvx *= SHOCK_DECAY; o.pvy *= SHOCK_DECAY;
  if(Math.abs(o.pvx)<0.02 && Math.abs(o.pvy)<0.02){ o.pvx=0; o.pvy=0; }
}
function updatePushes(){
  applyPush(player);
  for(const e of enemies) applyPush(e);
  for(const a of allies) if(a.small) applyPush(a);
  for(const d of debris) applyPush(d);
}

// The wave was only ever a rule before: it pushed things and did damage
// but drew nothing of its own, so the one visible trace was a particle
// ring that had already faded by the time the front arrived.
function drawShocks(){
  for(const s of SHOCKS){
    const t = Math.min(1, s.r/s.rMax);
    // Volle Helligkeit im ersten Viertel, danach zuegig weg.
    const a = t<0.25 ? 1 : Math.pow(1-(t-0.25)/0.75, 1.6);
    ctx.save();
    ctx.globalCompositeOperation='lighter';

    // Zentralblitz. Nur die ersten Schritte, dafuer hell.
    if(t<0.10){
      const f=1-t/0.10;
      const g=ctx.createRadialGradient(s.x,s.y,0, s.x,s.y,s.rMax*0.42);
      g.addColorStop(0,'rgba(255,252,238,'+(0.85*f).toFixed(3)+')');
      g.addColorStop(0.45,'rgba(255,205,130,'+(0.35*f).toFixed(3)+')');
      g.addColorStop(1,'rgba(255,150,40,0)');
      ctx.fillStyle=g;
      ctx.fillRect(s.x-s.rMax*0.45, s.y-s.rMax*0.45, s.rMax*0.9, s.rMax*0.9);
    }

    // Breiter warmer Schimmer hinter der Front.
    ctx.strokeStyle='rgba(255,'+((205-80*t)|0)+','+((140-105*t)|0)+','+(a*0.55).toFixed(3)+')';
    ctx.lineWidth=Math.max(2, 13*(1-t));
    ctx.beginPath(); ctx.arc(s.x,s.y,Math.max(1,s.r-5),0,Math.PI*2); ctx.stroke();

    // Der harte Vorderrand. Duenn, fast weiss, und er bleibt duenn -
    // genau das hat vorher gefehlt.
    ctx.strokeStyle='rgba(255,253,244,'+(a*0.95).toFixed(3)+')';
    ctx.lineWidth=t<0.5?2.6:2.0;
    ctx.beginPath(); ctx.arc(s.x,s.y,s.r,0,Math.PI*2); ctx.stroke();

    // Funkenwurf auf der Front.
    ctx.lineCap='round';
    for(const p of s.sparks){
      const rr=s.r*p.o;
      if(rr<2) continue;
      const ca=Math.cos(p.a), sa=Math.sin(p.a);
      const len=p.l*(0.4+0.6*(1-t));
      ctx.strokeStyle='rgba(255,'+((240-60*t)|0)+','+((190-140*t)|0)+','+(a*0.8).toFixed(3)+')';
      ctx.lineWidth=p.w;
      ctx.beginPath();
      ctx.moveTo(s.x+ca*rr, s.y+sa*rr);
      ctx.lineTo(s.x+ca*(rr+len), s.y+sa*(rr+len));
      ctx.stroke();
    }
    ctx.restore();
  }
}

function drawJumpVortex(){
  if(!WARP_IMG || !WARP_IMG.complete || !WARP_IMG.naturalWidth) return;
  let t = -1;
  if(arriveT>0) t = 1-(arriveT/TRANS_IN);                 // opening, ship out
  else if(waveOver && waveCd>0 && waveCd<=TRANS_OUT) t = 1-(waveCd/TRANS_OUT);
  if(t<0) return;
  const pImg = IMGS[player.ship];
  let WS = 150;
  if(pImg) WS = Math.max(130, pImg.height*playerSc()*2.4);
  // Out: the vortex swells as the ship shrinks. In: it shuts behind him.
  const grow = (arriveT>0) ? (1-t) : t;
  const wS = 0.15+0.95*Math.min(1, grow*1.35);
  let wF = Math.floor(t*WARP_FRAMES);
  if(wF<0) wF=0; if(wF>WARP_FRAMES-1) wF=WARP_FRAMES-1;
  ctx.save();
  ctx.globalAlpha = Math.min(1, grow*2.2);
  ctx.translate(player.x|0, player.y|0);
  ctx.scale(wS, wS);
  ctx.drawImage(WARP_IMG,
    (wF%WARP_COLS)*WARP_CELL, ((wF/WARP_COLS)|0)*WARP_CELL,
    WARP_CELL, WARP_CELL, -WS/2, -WS/2, WS, WS);
  ctx.restore();
  ctx.globalAlpha = 1;
  // One darkness, sitting exactly on the changeover. The outbound half
  // used waveCd directly, which runs from full down to zero, so the field
  // went dark at the *start* of the jump and again at the start of the
  // arrival: two events instead of one. Both halves now measure how close
  // they are to the boundary itself, so the darkness deepens into it and
  // lifts out of it as a single fade, with the background swap inside.
  const k = jumpDark();
  if(k>0){
    ctx.fillStyle='rgba(6,9,20,'+(k*0.92).toFixed(3)+')';
    ctx.fillRect(0,HUD_H,W,H-HUD_H);
  }
}

function drawNebulaFog(){
  if(!nebulaOn()) return;
  const r = fireRange();
  if(transFog<=0.01) return;
  const T = nebTint;
  ctx.save();
  ctx.globalAlpha = transFog;
  ctx.beginPath(); ctx.rect(0,HUD_H,W,H-HUD_H); ctx.clip();
  // The clear pocket is deliberately tight: it is a hole you fly inside,
  // not a room you sit in.
  const g = ctx.createRadialGradient(player.x,player.y,r*0.25,
                                     player.x,player.y,r*1.45);
  g.addColorStop(0,   'rgba('+T.core+',0)');
  g.addColorStop(0.50,'rgba('+T.core+',0.54)');
  g.addColorStop(1,   'rgba('+T.edge+',0.90)');
  ctx.fillStyle=g; ctx.fillRect(0,HUD_H,W,H-HUD_H);
  // Banks drifting across, so the haze is not just a disc glued to the ship.
  for(let i=0;i<5;i++){
    const px = W+220-((fc*0.28+i*300)%(W+440));
    const py = HUD_H+70+i*82;
    const rg = ctx.createRadialGradient(px,py,12,px,py,155);
    rg.addColorStop(0,'rgba('+T.bank+',0.17)');
    rg.addColorStop(1,'rgba('+T.bank+',0)');
    ctx.fillStyle=rg; ctx.fillRect(px-160,py-160,320,320);
  }
  ctx.restore();
}

// Ein Bogen. Die Richtung wird frei ueber den vollen Kreis gewuerfelt und
// dann als Irrfahrt fortgeschrieben, statt wie bisher immer nach rechts zu
// marschieren - das war der Grund, warum alle Blitze waagerecht lagen und
// nur leicht gewellt aussahen.
function makeEmpBolt(){
  const segs = 5+((Math.random()*5)|0);
  let ang = Math.random()*Math.PI*2;
  let x = Math.random()*W, y = HUD_H+Math.random()*(H-HUD_H);
  const pts = [{x:x,y:y}];
  for(let i=0;i<segs;i++){
    ang += (Math.random()-0.5)*1.1;
    const len = 12+Math.random()*26;
    x += Math.cos(ang)*len; y += Math.sin(ang)*len;
    pts.push({x:x,y:y});
  }
  // Ein bis zwei Abzweige an zufaelligen Knicken. Ohne die sieht ein
  // Blitz wie ein Kabel aus.
  const forks = [];
  const nf = 1+((Math.random()*2)|0);
  for(let f=0;f<nf;f++){
    const j = 1+((Math.random()*(pts.length-2))|0);
    let fa = Math.atan2(pts[j].y-pts[j-1].y, pts[j].x-pts[j-1].x)
           + (Math.random()<0.5?-1:1)*(0.5+Math.random()*0.6);
    let fx = pts[j].x, fy = pts[j].y;
    const fp = [{x:fx,y:fy}];
    const fs = 2+((Math.random()*3)|0);
    for(let i=0;i<fs;i++){
      fa += (Math.random()-0.5)*1.0;
      const len = 8+Math.random()*16;
      fx += Math.cos(fa)*len; fy += Math.sin(fa)*len;
      fp.push({x:fx,y:fy});
    }
    forks.push(fp);
  }
  return {pts:pts, forks:forks, life:2+((Math.random()*4)|0), max:5,
          warm: Math.random()<0.5};
}

function tickEmpBolts(){
  const p = 1-(empWarn/EMP_WARN);
  for(let i=empBolts.length-1;i>=0;i--){
    if(--empBolts[i].life<=0) empBolts.splice(i,1);
  }
  // Je naeher der Schlag, desto dichter die Entladungen.
  const want = 1+((p*4)|0);
  while(empBolts.length < want && Math.random()<0.55) empBolts.push(makeEmpBolt());
}

// Announcement. Yellow-orange discharges run through the haze for
// EMP_WARN steps and get busier as the strike closes, so the blackout can
// be prepared for instead of merely suffered. Deliberately warm: the
// storm itself flashes cold, and the contrast is what marks the moment.
function drawEmpWarn(){
  if(empWarn<=0) return;
  const p = 1-(empWarn/EMP_WARN);      // 0 beim ersten Bogen, 1 beim Schlag
  ctx.save();
  ctx.beginPath(); ctx.rect(0,HUD_H,W,H-HUD_H); ctx.clip();
  ctx.globalCompositeOperation='lighter';
  ctx.lineCap='round'; ctx.lineJoin='round';
  ctx.fillStyle='rgba(150,80,10,'+(0.04+0.14*p).toFixed(3)+')';
  ctx.fillRect(0,HUD_H,W,H-HUD_H);
  for(const b of empBolts){
    // Frisch geborene Boegen sind am hellsten und verloeschen dann.
    const f = b.life/b.max;
    const warm = b.warm;
    const glow = (0.16+0.30*p)*f;
    const core = (0.45+0.50*p)*f;
    const line = function(pts){
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      for(let i=1;i<pts.length;i++) ctx.lineTo(pts[i].x, pts[i].y);
      ctx.stroke();
    };
    // Breiter Schimmer, darueber ein duenner heller Kern. Das ist der
    // Unterschied zwischen einem Strich und einem Blitz.
    ctx.strokeStyle = warm ? 'rgba(255,150,30,'+glow.toFixed(3)+')'
                           : 'rgba(255,110,15,'+glow.toFixed(3)+')';
    ctx.lineWidth = 5.5;
    line(b.pts);
    for(const fk of b.forks) line(fk);
    ctx.strokeStyle = warm ? 'rgba(255,225,140,'+core.toFixed(3)+')'
                           : 'rgba(255,195,90,'+core.toFixed(3)+')';
    ctx.lineWidth = 1.6;
    line(b.pts);
    ctx.lineWidth = 1.0;
    for(const fk of b.forks) line(fk);
  }
  ctx.restore();
}

// The storm is visible on the glass as well as in the instruments: a
// discharge, then interference until the sensors come back.
function drawEmpFX(){
  if(empOut<=0) return;
  ctx.save();
  ctx.beginPath(); ctx.rect(0,HUD_H,W,H-HUD_H); ctx.clip();
  if(empOut>270){                       // the first thirty steps: the flash
    ctx.fillStyle='rgba(198,230,255,'+(((empOut-270)/30)*0.55).toFixed(3)+')';
    ctx.fillRect(0,HUD_H,W,H-HUD_H);
  }
  ctx.strokeStyle='rgba(96,158,196,0.09)'; ctx.lineWidth=1;
  for(let y=HUD_H+(fc%3); y<H; y+=3){
    ctx.beginPath(); ctx.moveTo(0,y+0.5); ctx.lineTo(W,y+0.5); ctx.stroke();
  }
  for(let k=0;k<5;k++){                 // rolling interference bands
    const y = HUD_H+((fc*(2+k*3)+k*131)%(H-HUD_H));
    ctx.fillStyle='rgba(150,215,255,0.055)';
    ctx.fillRect(0,y,W,3+k*2);
  }
  if(fc%9<3){                           // occasional whole field flicker
    ctx.fillStyle='rgba(150,200,240,0.05)';
    ctx.fillRect(0,HUD_H,W,H-HUD_H);
  }
  ctx.restore();
}

function drawDebris(){
  for(const d of debris){
    const img = IMGS[d.key]; if(!img) continue;
    const w = d.sw*d.sc, h = d.sh*d.sc;
    ctx.save();
    ctx.translate(d.x|0, d.y|0);
    ctx.rotate(d.ang);
    if(d.out){
      ctx.save();
      outlinePath(d, w, h);
      ctx.clip();
      try{ ctx.drawImage(img, d.sx, d.sy, d.sw, d.sh, -w/2, -h/2, w, h); }catch(err){}
      ctx.restore();
      // Charred rim, then a hot line on top of it while the piece is
      // still cooling. The tear is where the metal burned through.
      outlinePath(d, w, h);
      ctx.strokeStyle='rgba(18,12,8,0.85)'; ctx.lineWidth=2.2; ctx.stroke();
      ctx.strokeStyle='rgba(60,44,32,0.55)'; ctx.lineWidth=0.9; ctx.stroke();
      if(d.heat>0.05){
        ctx.globalAlpha = Math.min(0.85, d.heat);
        ctx.strokeStyle = d.heat>0.5 ? '#ff9a3c' : '#a8431a';
        ctx.lineWidth = 1.1; ctx.stroke();
        ctx.globalAlpha = 1;
      }
    } else {
      try{ ctx.drawImage(img, d.sx, d.sy, d.sw, d.sh, -w/2, -h/2, w, h); }catch(err){}
    }
    ctx.restore();
  }
}

// ── SHOOTING ─────────────────────────────────────────────────
function pShoot(){
  const flip=player.flip||false;
  const a=player.head||0;      // shots leave along the nose, not the draw angle
  const nx=Math.cos(a), ny=Math.sin(a);
  // Speed, damage, colour and reach all come off the fitted gun now.
  const wp=curPri();
  const bvx=nx*wp.spd, bvy=ny*wp.spd;
  // range is a distance, the bullet counts steps, so one is turned into
  // the other here rather than at every place that makes a bullet.
  const life=wp.range ? Math.max(1, Math.round(wp.range/wp.spd)) : 0;
  const pts=mountList(player.ship,player.x,player.y,playerSc(),flip,'primary',player.ang||0);
  // One bolt per barrel, unless the gun throws a cone - then the volley's
  // damage is shared out over the pellets and each barrel throws the lot.
  const n=wp.pellets||1;
  function throwFrom(px, py, d){
    for(let k=0;k<n;k++){
      const ja = (n===1) ? a : a + (k/(n-1) - 0.5)*wp.spread
                               + (Math.random()-0.5)*(wp.spread/n);
      pBullets.push({x:px, y:py, vx:Math.cos(ja)*wp.spd, vy:Math.sin(ja)*wp.spd,
                     w:n>1?8:14, h:3, dmg:d/n,
                     col:wp.col, glow:wp.glow, pLife:life,
                     fuse:wp.fuse ? Math.max(1, Math.round(wp.fuse/wp.spd)) : 0,
                     wpn:wp.key});
    }
  }
  if(pts&&pts.length){
    const d=volleyDmg(pts.length)*wp.dmg;
    for(const p of pts) throwFrom(p.x, p.y, d);
    STATS.shots++;
    return;
  }
  // No mounts for this hull: two muzzles offset in sprite space, turned
  // with the ship so the fallback lines up with the nose as well.
  const {x,y}=player;
  throwFrom(x+30*nx+4*ny, y+30*ny-4*nx, volleyDmg(2)*wp.dmg);
  throwFrom(x+30*nx-4*ny, y+30*ny+4*nx, volleyDmg(2)*wp.dmg);
  STATS.shots++;}
// With no angle given this behaves as before, which is what capital ship
// turrets still rely on. Small ships pass a direction. scatter widens the
// spread and is what a ship with its sensors shot out fires like.
function eSmall(ex,ey,fac,ang,spd,dmg,scatter){
  const s=spd||EBULLET_SPD;
  const sc=scatter||1;
  if(ang==null){
    eBullets.push({x:ex,y:ey,vx:-s,vy:(Math.random()-.5)*1.8*sc,w:8,h:4,big:false,faction:fac||'ntf',dmg:dmg});
    return;
  }
  eBullets.push({x:ex,y:ey,vx:Math.cos(ang)*s,vy:Math.sin(ang)*s,w:8,h:4,big:false,faction:fac||'ntf',dmg:dmg});}
function eBig(ex,ey,fac){
  eBullets.push({x:ex,y:ey,vx:-2.5,vy:(Math.random()-.5)*1.2,w:12,h:12,big:true,faction:fac||'ntf'});}
function eSpread(ex,ey,fac){const base=Math.atan2(player.y-ey,player.x-ex);
  for(const da of[-0.35,-0.175,0,0.175,0.35]){const a=base+da;
    eBullets.push({x:ex,y:ey,vx:Math.cos(a)*2.2,vy:Math.sin(a)*2.2,w:6,h:6,big:false,
      faction:fac||'ntf'});}}


// ── SMALL SHIP FLIGHT ────────────────────────────────────────
// Fighters and bombers fly by heading: they turn towards where they want
// to go and always move along their nose. They no longer run off the left
// edge, so a wave now ends when it is destroyed, not when it has driven
// past. To stop the whole wave piling onto one point, only a few are ever
// cleared to run in. The rest hold their own preferred distance and shoot
// from there.
function isSmallEnemy(e){
  return (e.type==='fighter'||e.type==='bomber') && !e.dead && !(e.warp>0);
}
// Own side, used for separation and for handing out attack slots.
function sideOf(e){ return e.side==='ally' ? allies : enemies; }

// Nearest enemy ship of a different faction. Only asked while waveFeud is
// on, and it deliberately ignores non-combatants: a Shivan wing tearing
// into a Vasudan freighter instead of the Vasudan fighters would read as
// confusion rather than as a second war.
function nearestFoe(e){
  let best=null, bd=Infinity;
  for(const o of enemies){
    if(o===e || o.dead || o.warp>0 || o.warpOut>0) continue;
    if(o.type!=='fighter' && o.type!=='bomber' && !isLargeShip(o)) continue;
    if(!o.faction || o.faction===e.faction) continue;
    const d=(o.x-e.x)*(o.x-e.x)+(o.y-e.y)*(o.y-e.y);
    if(d<bd){ bd=d; best=o; }
  }
  return best;
}

function nearestOf(list, e, want){
  let best=null, bd=Infinity;
  for(const o of list){
    if(o.dead || o.warp>0 || o.warpOut>0 || o.type==='asteroid') continue;
    if(want==='large' && !isLargeShip(o)) continue;
    if(want==='small' && !isSmallShip(o)) continue;
    if(want==='bomber' && o.type!=='bomber') continue;
    if(list===enemies && playerOnly(o)) continue;
    // The same things nearestEnemy() leaves alone: scenery that cannot
    // be hurt, and ships that are only there to be scanned or taken.
    if(list===enemies && (o.invuln || o.noTarget)) continue;
    const d=(o.x-e.x)*(o.x-e.x)+(o.y-e.y)*(o.y-e.y);
    if(d<bd){bd=d;best=o;}
  }
  return best;
}

// How many small craft may work the same capital ship. Without this every
// bomber in the wave picks the one escort and stacks on it, which is what
// made a called cruiser evaporate. Applies to both sides, so an allied
// bomber wing spreads across enemy capitals in the same way.
const FOCUS_MAX = 2;
function focusCount(target, side, self){
  let n=0;
  const list = side==='ally' ? allies : enemies;
  for(const o of list){
    if(o===self || o.dead) continue;
    if(o.type!=='fighter' && o.type!=='bomber') continue;
    if(o.focusOn===target) n++;
  }
  return n;
}
// Picks target unless it is already crowded, in which case the next best
// from the same list is used.
function claimTarget(e, first, list, want){
  if(first && focusCount(first, e.side, e) < FOCUS_MAX){ e.focusOn=first; return first; }
  let best=null, bd=Infinity;
  for(const o of list){
    if(o===first || o.dead || o.warp>0 || o.warpOut>0 || o.type==='asteroid') continue;
    if(want==='large' && !isLargeShip(o)) continue;
    if(focusCount(o, e.side, e) >= FOCUS_MAX) continue;
    const d=(o.x-e.x)*(o.x-e.x)+(o.y-e.y)*(o.y-e.y);
    if(d<bd){bd=d;best=o;}
  }
  if(best){ e.focusOn=best; return best; }
  // Nothing free. Returning first anyway would defeat the whole limit, which
  // is exactly what happens when there is only one escort on the field, so
  // the caller sends this one somewhere else instead.
  e.focusOn=null; return null;
}

// Enemy bombers go for escorts, enemy fighters for the player. Escort
// bombers go for enemy capital ships, escort fighters for whatever is
// threatening the player, nearest first.
function smallTarget(e){
  if(e.side==='ally'){
    if(e.type==='bomber'){
      const big = nearestOf(enemies, e, 'large');
      if(big){
        const got = claimTarget(e, big, enemies, 'large');
        if(got) return got;
      }
      e.focusOn=null;
      return nearestOf(enemies, e, 'small') || e;
    }
    // A scrambled screen goes for the bombers it was scrambled against,
    // otherwise it latches onto the nearest fighter and the bombers get
    // their run in unopposed.
    if(e.intercept){
      const bmb = nearestOf(enemies, e, 'bomber');
      if(bmb) return bmb;
    }
    return nearestOf(enemies, e, 'small') || nearestOf(enemies, e, 'any') || e;
  }
  // Hostile factions at each other's throats. Out of the Dark, Into the
  // Night is the first of them: the unknowns cut into the Vasudans before
  // they ever look at the player. Off by default, so nothing changes in
  // the endless mode.
  if(waveFeud){
    const foe = nearestFoe(e);
    if(foe){ e.focusOn=null; return foe; }
  }
  if(e.type==='bomber' && allies.length){
    const best = nearestOf(allies, e, 'large');
    if(best){
      const got = claimTarget(e, best, allies, 'large');
      if(got) return got;
      // Escort already has its two attackers: this one goes for the player
      // rather than joining the queue.
      e.focusOn=null;
      return player;
    }
    const any = nearestOf(allies, e, 'any');
    if(any){ e.focusOn=null; return any; }
  }
  // Jaeger mit Auftrag gehen auf ihr Ziel, solange es lebt.
  if(waveHunt && e.hunter){
    const h = byId(waveHunt)[0];
    if(h){ e.focusOn=null; return h; }
  }
  e.focusOn=null;
  return player;
}

// Hands out the attack slots. Whoever is closest to its target gets to go
// in, which keeps the runs coming from a sensible direction.
function assignAttackRoles(list){
  const smalls=[];
  for(const e of (list||enemies)) if(isSmallEnemy(e)) smalls.push(e);
  let n=0;
  for(const e of smalls) if(e.role==='attack') n++;
  if(n>=ATTACK_QUOTA) return;
  const cand=[];
  for(const e of smalls){
    if(e.role==='attack') continue;
    const t=smallTarget(e);
    cand.push({e:e, d:(t.x-e.x)*(t.x-e.x)+(t.y-e.y)*(t.y-e.y)});
  }
  cand.sort(function(a,b){return a.d-b.d;});
  for(let i=0;i<cand.length && n<ATTACK_QUOTA;i++){
    cand[i].e.role='attack'; cand[i].e.passT=0; n++;
  }
}

// One step of flight for one small ship. Returns nothing, edits in place.
function flySmall(e){
  const t=smallTarget(e);
  const dx=t.x-e.x, dy=t.y-e.y;
  const d=Math.sqrt(dx*dx+dy*dy)||0.001;
  let wx, wy;                       // where it wants to go, unnormalised
  if(e.role==='attack'){
    if(e.passT>0){
      // Flying through after a run. Braking on top of the target is what
      // made everything cluster, so it keeps going and comes back around.
      e.passT--;
      wx=Math.cos(e.head); wy=Math.sin(e.head);
      if(e.passT===0) e.role='stand';
    } else if(d<ATTACK_BREAK && !ramsOnContact(e)){
      // Ein Rammkurs bricht nicht ab. Der Durchflug ist richtig fuer einen
      // Bomber, der seine Last los ist, und falsch fuer einen, dessen
      // ganzer Zweck der Aufprall ist: sowohl die Aufprallpruefung als auch
      // der gelbe Doppelwinkel verlangen passT gleich null, also verschwand
      // die Warnung genau in dem Augenblick, in dem er ueber dem Rumpf war.
      e.passT=ATTACK_PASS;
      wx=Math.cos(e.head); wy=Math.sin(e.head);
    } else {
      wx=dx/d; wy=dy/d;
    }
  } else {
    // Holding station: close in or back off until the preferred distance
    // is reached, and drift sideways around the target while there.
    const rx=dx/d, ry=dy/d;
    const k=Math.max(-1,Math.min(1,(d-e.prefD)/STAND_BAND));
    const tang=1-Math.abs(k)*0.6;
    wx=rx*k - ry*e.orbit*tang;
    wy=ry*k + rx*e.orbit*tang;
  }
  // Separation, so two ships with the same idea do not end up in the same
  // pixel. Same principle as separateCapitals, smaller radius.
  let spx=0, spy=0;
  for(const o of sideOf(e)){
    if(o===e || !isSmallEnemy(o)) continue;
    const sx=e.x-o.x, sy=e.y-o.y;
    const s2=sx*sx+sy*sy;
    if(s2>0.01 && s2<SEP_R*SEP_R){
      const sd=Math.sqrt(s2), f=(1-sd/SEP_R)*SEP_F;
      wx+=sx/sd*f; wy+=sy/sd*f;
      spx+=sx/sd*f; spy+=sy/sd*f;
    }
  }
  // Normalise first. Adding the edge to a wish of arbitrary length was
  // what let the two cancel out at the boundary.
  const wl=Math.sqrt(wx*wx+wy*wy);
  if(wl>0.0001){ wx/=wl; wy/=wl; } else { wx=0; wy=0; }
  // Edge pressure on a square ramp: gentle at the margin, overwhelming at
  // the boundary itself.
  if(e.x<EDGE_M){ const u=1-e.x/EDGE_M; wx += u*u*EDGE_F; }
  else if(e.x>W-EDGE_M){ const u=1-(W-e.x)/EDGE_M; wx -= u*u*EDGE_F; }
  if(e.y<HUD_H+EDGE_M){ const u=1-(e.y-HUD_H)/EDGE_M; wy += u*u*EDGE_F; }
  else if(e.y>H-EDGE_M){ const u=1-(H-e.y)/EDGE_M; wy -= u*u*EDGE_F; }
  // Nothing sensible left to want: head for the middle rather than freeze.
  if(wx*wx+wy*wy < 0.0004){ wx=W*0.5-e.x; wy=(HUD_H+H)*0.5-e.y; }
  // Turn towards the wish, then move along the nose.
  if(wx*wx+wy*wy > 0.0001){
    let df=Math.atan2(wy,wx)-e.head;
    while(df> Math.PI) df-=Math.PI*2;
    while(df<-Math.PI) df+=Math.PI*2;
    e.head+=Math.max(-e.turn,Math.min(e.turn,df));
    if(e.head> Math.PI) e.head-=Math.PI*2;
    else if(e.head<-Math.PI) e.head+=Math.PI*2;
  }
  e.vx=Math.cos(e.head)*e.spd; e.vy=Math.sin(e.head)*e.spd;
  // Drop thrust that only pushes into the clamp. The component along the
  // boundary is kept, so a ship that arrives nose first slides clear
  // while its turn comes round instead of grinding against the glass.
  const bnd=shipBound(e);
  if(e.x<=bnd && e.vx<0) e.vx=0;
  else if(e.x>=W-bnd && e.vx>0) e.vx=0;
  if(e.y<=HUD_H+bnd && e.vy<0) e.vy=0;
  else if(e.y>=H-bnd && e.vy>0) e.vy=0;
  // Direct sidestep, capped. Two ships closing head on cover more ground
  // in one step than either can steer away, so steering alone lets them
  // pass straight through one another.
  const sl=Math.sqrt(spx*spx+spy*spy);
  if(sl>0.001){ const c=Math.min(SEP_PUSH,sl)/sl; e.x+=spx*c; e.y+=spy*c; }
  e.x+=e.vx; e.y+=e.vy;
  e.x=Math.max(bnd,Math.min(W-bnd,e.x));
  e.y=Math.max(HUD_H+bnd,Math.min(H-bnd,e.y));
  const pose=poseFor(e.head, e.flip);
  e.ang=pose.ang; e.flip=pose.flip;
  return t;
}

// Guns only bear within a cone ahead, and the further out the target sits
// the wider the shot scatters.
function smallFire(e, t){
  // No target: smallTarget() then hands back the ship itself, and a
  // lead angle onto its own position reads as dead ahead.
  if(!t || t===e){ e.fT=12; return; }
  const d=Math.hypot(t.x-e.x, t.y-e.y);
  if(d>fireRange()){ e.fT=12; return; }
  const aim=leadAngle(e.x, e.y, t, EBULLET_SPD);
  let off=aim-e.head;
  while(off> Math.PI) off-=Math.PI*2;
  while(off<-Math.PI) off+=Math.PI*2;
  if(Math.abs(off)>EFIRE_CONE){ e.fT=12; return; }   // no bearing, check again soon
  const spread=ESPREAD_NEAR+(ESPREAD_FAR-ESPREAD_NEAR)*Math.min(1,d/fireRange());
  // Escort bolts go into the player's list so they hit enemies, enemy
  // bolts into theirs. Otherwise the geometry is identical.
  const shot = e.side==='ally'
    ? function(x,y,a,d){ pBullets.push({x:x,y:y,vx:Math.cos(a)*EBULLET_SPD,vy:Math.sin(a)*EBULLET_SPD,
        w:11,h:4,dmg:d*2,ally:true,fac:e.faction}); }
    : function(x,y,a,d){
        // Ohne uebergebenen Winkel auf das naechste Ziel halten statt
        // stur nach links.
        if(a==null){
          const _t = (e.side==='ally') ? nearestEnemy(x,y) : capGunTarget(e);
          if(!_t) return;
          a = Math.atan2(_t.y-y, _t.x-x);
        }
        eSmall(x,y,e.faction,a,null,d);
      };
  const pts=entMounts(e,'primary');
  if(pts&&pts.length){
    const dpb=eVolleyDmg(pts.length);
    for(const p of pts) shot(p.x,p.y, aim+(Math.random()*2-1)*spread, dpb);
  } else {
    const dpb=eVolleyDmg(e.type==='bomber'?2:1);
    shot(e.x,e.y, aim+(Math.random()*2-1)*spread, dpb);
    if(e.type==='bomber') shot(e.x,e.y, aim+(Math.random()*2-1)*spread, dpb);
  }
  e.fT=e.fR;
}

// ── TARGETING ────────────────────────────────────────────────
// Every ship belongs to a side. Until escorts exist,
// allies is empty and the player is the only unit on his side.
let allies = [];

// Transitional switch. true matches the design: a large turret
// holds fire when no capital ship is in range. Set to false
// it falls back to targeting the player, as it did before.
const LARGE_BEAM_HOLDS_FIRE = true;

function isSmallShip(o){
  return o.type==='fighter' || o.type==='bomber' || o.type==='sentry';
}
function isLargeShip(o){
  return o.type==='cruiser' || o.type==='corvette'
      || o.type==='destroyer' || o.type==='boss'
      // Eine Station ist ein Ziel fuer schwere Strahlen - unverwundbare
      // nehmen ohnehin keinen Schaden, aber beschossen werden sie.
      || o.type==='station';
}

// How large is the target for a beam hit test?
function targetRadius(o){
  if(o === player){
    const img=IMGS[player.ship];
    return img ? Math.max(14, img.height*playerSc()*0.38) : 18;
  }
  const img=IMGS[o.img];
  return img ? Math.max(16, img.height*o.sc*0.38) : 20;
}

// The Pegasus is a stealth fighter, so no targeting system can hold it.
// This covers everything that needs a lock: beam turrets, missiles and
// bombs. Ordinary bolts are aimed by eye and still hit, and guided rounds
// may still be launched in its direction, they simply fly straight after
// that. The hull is hard to pin down, not invulnerable.
const STEALTH_HULL = 'fipegasus';
function canLockOn(o){
  if(!o) return false;
  // Eine unverwundbare Station ist Kulisse. Auf sie zu halten sieht aus
  // wie ein Fehler und ist einer.
  if(o.invuln) return false;
  // Neither side gets a lock in a nebula, and nobody gets one while the
  // storm has the sensors down. Guided rounds fall back to dumbfire.
  if(nebulaOn()) return false;
  if(empOut>0) return false;
  if(o === player) return player.ship !== STEALTH_HULL;
  // The NTF flies the Loki as a stealth fighter: nothing holds a lock on
  // one. Only on the enemy side - and only the lock. It stays in plain
  // sight; FreeSpace has no visual cloak and neither does this game.
  if(o.side==='enemy' && LOCKLESS_HULLS[o.img]) return false;
  return o.img !== STEALTH_HULL;
}
const LOCKLESS_HULLS = {filoki:true};

// All valid targets for one turret on ship e.
function beamTargets(e, wantLarge){
  const out=[];
  if(e.side === 'ally'){
    for(const o of enemies){
      if(o.dead || o.warp>0 || o.type==='asteroid' || o.invuln || o.noTarget) continue;
      if(!canLockOn(o)) continue;
      if(wantLarge ? isLargeShip(o) : isSmallShip(o)) out.push(o);
    }
  } else {
    if(!wantLarge && GS==='playing' && player.hp>0 && canLockOn(player)) out.push(player);
    for(const o of allies){
      if(o.dead || o.warp>0) continue;
      if(!canLockOn(o)) continue;
      if(wantLarge ? isLargeShip(o) : isSmallShip(o)) out.push(o);
    }
  }
  return out;
}

// Nearest target to the turret position.
function pickBeamTarget(e, b){
  const list = beamTargets(e, !!b.large);
  if(!list.length) return null;
  const mp = mountPos(e, b);
  let best=null, bd=Infinity;
  for(const o of list){
    const d=(o.x-mp.x)**2 + (o.y-mp.y)**2;
    if(d<bd){ bd=d; best=o; }
  }
  return best;
}

function targetAlive(e, o){
  if(!o) return false;
  if(o === player) return GS==='playing' && player.hp>0;
  if(o.dead) return false;
  return (e.side==='ally' ? enemies : allies).indexOf(o) >= 0;
}

// Is a point close enough to the beam line?
function beamHits(mx, my, ang, tx, ty, rad){
  const ux=Math.cos(ang), uy=Math.sin(ang);
  const proj=(tx-mx)*ux + (ty-my)*uy;
  if(proj < 0 || proj > 2400) return false;
  const cx=mx+ux*proj, cy=my+uy*proj;
  return ((tx-cx)**2 + (ty-cy)**2) < rad*rad;
}

// ── SUBSYSTEMS ─────────────────────────────────────────────
// Five per capital ship, on both sides. Their positions are read off the
// sprite's alpha mask, which exists for hit detection anyway: a ray is
// cast out from the centre, the last solid pixel found, and the point set
// a little inside that edge. Every hull therefore gets sensible mountings
// without a single manual entry.
// A flat share does not work across a range from 1120 to 15000 hull: on a
// cruiser eight percent is 90 points, which is under half a second of
// fire. Smaller ships get a larger share so their systems are worth
// aiming at at all.
// boss stand auf 0.08. Bei 15000 Grundrumpf waren das 1200 Punkte, die
// man nebenbei wegschiesst, ohne es zu wollen - eine Sathanas ist breit
// genug, dass Streufeuer diesen Punkt zwangslaeufig irgendwann findet.
// Auf 0.20 ist es eine Entscheidung statt eines Nebenprodukts.
const SUB_HP_FRAC = {cruiser:0.22, corvette:0.16, destroyer:0.10, boss:0.20,
                     station:0.09};
// Rest, unter den ein Lahmlege-Ziel nicht fallen kann, solange der Auftrag
// laeuft. 15 % ist derselbe Wert wie HULL_CRIT: der Balken steht genau
// dort, wo er ohnehin schon pulsiert.
const DISABLE_HULL_FLOOR = 0.15;
// Grosse Schiffe brechen nicht in einem Bild. DEATH_ROLL ist die Dauer
// der Sekundaerexplosionen, danach kommt die eigentliche.
// Andocken. Der Frachter faehrt den Andockpunkt seines Ziels an; ist er
// nah genug, gilt es als angedockt. Danach haengt die Fracht an ihm:
// sie wird mitgezeichnet, mitgetroffen und stirbt mit ihm.
const DOCK_SPD = 0.55;           // Bildpunkte je Schritt
const DOCK_NEAR = 22;            // ab hier angedockt
const DEATH_ROLL = 110;          // 1,1 s
const DEATH_ROLL_GAP = 11;       // alle 0,11 s ein Treffer irgendwo im Rumpf
// Duennere Subsysteme nur beim Lahmlege-Ziel. Ohne das dauert es bei einer
// Trefferquote von 10 % auf einen 6-px-Punkt rund 17 s je Subsystem, und
// es sind zwei. Mit 0.12 sind es 8,5 s bei 20 % und 17 s bei 10 %.
const DISABLE_SUB_FRAC = 0.12;
const SUB_HULL_BLEED = 0.5;   // share of a subsystem hit that also hits the hull
// The hit radius has to follow the ship. A fixed twenty pixels is wider
// than the gap between two systems on a cruiser, which would make them
// impossible to tell apart by aim.
// Ohne eigenen Radius bleibt alles wie bisher: 8.5 % der Schiffsbreite,
// begrenzt auf 9 bis 24 Bildschirmpixel. Ein von Hand gesetzter Wert darf
// weiter gehen - ein Antriebsblock auf einer Sathanas ist ein groesseres
// Ziel als eine Funkanlage auf einem Fenris, und die alte Obergrenze von
// 24 px haette das eingeebnet.
function subRadius(e, s){
  const img = IMGS[e.img];
  if(!img) return 12;
  const w = img.width*e.sc;
  if(s && s.r) return Math.max(6, Math.min(40, w*s.r));
  return Math.max(9, Math.min(24, w*0.085));
}
const SUB_NAME_R = 120;       // how close before the name is spelled out
const SUB_NAME_CONE = 0.55;   // and how far off the nose it may be

// Angles in sprite space, 0 pointing forward along the hull.
const SUB_DEFS = [
  {id:'weapons',       label:'WEAPONS',       ang: 0.00},
  {id:'sensors',       label:'SENSORS',       ang:-1.00},
  {id:'navigation',    label:'NAVIGATION',    ang: 1.00},
  {id:'communication', label:'COMMUNICATION', ang:-2.40},
  {id:'engines',       label:'ENGINES',       ang: 2.40}
];
const SUB_POS = {};

// Centre of mass of the visible pixels. The middle of the bounding box is
// not necessarily on the ship at all: on a Hecate it falls in the gap
// between the upper and lower halves, and every ray then started outside
// the hull.
const MASK_MID = {};
function maskCentre(key){
  if(MASK_MID[key]) return MASK_MID[key];
  const m = getMask(key);
  if(!m) return null;
  let sx=0, sy=0, n=0;
  for(let y=0;y<m.h;y++) for(let x=0;x<m.w;x++){
    if(m.bits[y*m.w+x]){ sx+=x; sy+=y; n++; }
  }
  const c = n ? {x:sx/n, y:sy/n} : {x:m.w/2, y:m.h/2};
  MASK_MID[key] = c;
  return c;
}

function maskSolid(m, x, y){
  const ix = Math.round(x), iy = Math.round(y);
  if(ix<0||iy<0||ix>=m.w||iy>=m.h) return false;
  return !!m.bits[iy*m.w+ix];
}

// Outermost solid pixel along a ray, then stepped back inwards until the
// point is provably on the hull. Accepting the stepped back point without
// checking is what put the Hecate's navigation below the ship.
function hullRay(key, ang){
  const m = getMask(key);
  if(!m) return null;
  const c = maskCentre(key);
  const ux = Math.cos(ang), uy = Math.sin(ang);
  const maxR = Math.max(m.w, m.h);
  let last = 0;
  for(let r=1; r<maxR; r++){
    if(!maskSolid(m, c.x+ux*r, c.y+uy*r)){
      if(c.x+ux*r<0||c.y+uy*r<0||c.x+ux*r>=m.w||c.y+uy*r>=m.h) break;
      continue;
    }
    last = r;
  }
  if(last <= 0) return null;
  // Step back from the rim, then recover outwards. last is solid by
  // construction, walking inwards instead dragged every point towards the
  // centre of mass, where all five ended up on top of one another.
  let r = Math.max(1, last - Math.max(2, m.w*0.05));
  while(r < last && !maskSolid(m, c.x+ux*r, c.y+uy*r)) r += 1;
  if(!maskSolid(m, c.x+ux*r, c.y+uy*r)) return null;
  return {dx:(c.x+ux*r - m.w/2)/(m.w/2), dy:(c.y+uy*r - m.h/2)/(m.h/2)};
}

// Tries the wanted angle first, then a fan around it, so a hull with a notch
// exactly where a system belongs still gets a valid mounting. taken holds the
// points already placed: two systems within one hit radius of each other
// would be ambiguous to shoot at, and on a narrow hull the rays converge
// enough for that to happen.
// Five points on a narrow hull cannot always be held a fixed distance apart,
// so the requirement is relaxed in steps rather than abandoned: the first
// spacing that can actually be met is the one used.
const SUB_SEP_LEVELS = [0.20, 0.15, 0.11, 0.08, 0];
const SUB_FAN = 48;

// Ranks every point on the rim by how close it lies to the wanted direction,
// then takes the best one that keeps its distance from those already placed.
function hullRayNear(key, ang, taken){
  const m = getMask(key);
  if(!m) return null;
  const cands = [];
  for(let i=0;i<SUB_FAN;i++){
    const a = -Math.PI + 2*Math.PI*i/SUB_FAN;
    const p = hullRay(key, a);
    if(!p) continue;
    let dd = a - ang;
    while(dd >  Math.PI) dd -= Math.PI*2;
    while(dd < -Math.PI) dd += Math.PI*2;
    cands.push({d:Math.abs(dd), p:p});
  }
  if(!cands.length) return null;
  cands.sort(function(x,y){ return x.d-y.d; });
  for(const lvl of SUB_SEP_LEVELS){
    const minD = m.w*lvl;
    for(const c of cands){
      const px=(c.p.dx+1)*m.w/2, py=(c.p.dy+1)*m.h/2;
      let ok=true;
      for(const q of (taken||[])){
        const qx=(q.dx+1)*m.w/2, qy=(q.dy+1)*m.h/2;
        if((px-qx)*(px-qx)+(py-qy)*(py-qy) < minD*minD){ ok=false; break; }
      }
      if(ok) return c.p;
    }
  }
  return cands[0].p;
}

function subPositions(key){
  if(SUB_POS[key]) return SUB_POS[key];
  const m = mountsFor(key);
  // Von Hand gesetzte Positionen aus dem Mount-Editor haben Vorrang. Nur
  // wenn alle fuenf da sind - bei einem Teilsatz waere im Spiel nicht mehr
  // zu sehen, welcher Punkt gesetzt und welcher geraten ist.
  if(m && Array.isArray(m.subs) && m.subs.length === SUB_DEFS.length){
    const byId = {};
    for(const x of m.subs) byId[x.id] = x;
    if(SUB_DEFS.every(function(d){ return byId[d.id]; })){
      SUB_POS[key] = SUB_DEFS.map(function(d){
        const x = byId[d.id];
        return {id:d.id, label:d.label, dx:+x.dx, dy:+x.dy,
                r: x.r != null ? +x.r : null};
      });
      return SUB_POS[key];
    }
  }
  const out = [];
  const taken = [];
  for(const d of SUB_DEFS){
    let p = null;
    if(d.id==='engines' && m && m.thrusters && m.thrusters.length){
      // Engines belong at the drive plumes, not at some point on the rim.
      let sx=0, sy=0;
      for(const t of m.thrusters){ sx+=t.dx; sy+=t.dy; }
      const cand = {dx:sx/m.thrusters.length*0.82, dy:sy/m.thrusters.length*0.82};
      // Thruster mounts sit on the nozzle, which can be a spar sticking
      // out into nothing. Only keep it if it lands on solid hull.
      const mk = getMask(key);
      if(mk && maskSolid(mk, (cand.dx+1)*mk.w/2, (cand.dy+1)*mk.h/2)) p = cand;
      else p = hullRayNear(key, Math.atan2(cand.dy, cand.dx), taken);
    }
    if(!p) p = hullRayNear(key, d.ang, taken);
    if(!p) p = {dx:Math.cos(d.ang)*0.35, dy:Math.sin(d.ang)*0.35};
    out.push({id:d.id, label:d.label, dx:p.dx, dy:p.dy});
    taken.push(p);
  }
  SUB_POS[key] = out;
  return out;
}

function hasSubsystems(e){
  return e && (e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||e.type==='boss');
}
function initSubsystems(e){
  if(!hasSubsystems(e)) return;
  const hp = Math.max(30, Math.round(e.maxHp*(SUB_HP_FRAC[e.type]||0.10)));
  e.subs = subPositions(e.img).map(function(p){
    return {id:p.id, label:p.label, dx:p.dx, dy:p.dy, r:p.r || null,
            hp:hp, maxHp:hp, dead:false};
  });
}
// True while the named system is still alive. Ships without subsystems
// answer true, so small craft are unaffected by any of this.
// Granted once, whether one or both are gone, and only on the guns. Two
// separate bonuses stacking would put a destroyer above a boss, and a
// beam battery at this rate would cut down an escort before it arrived.
const CORNERED_RATE = 0.667;     // multiplier on the reload, so half again as fast
function corneredMult(e){
  if(!e || !e.subs) return 1;
  return (subOK(e,'navigation') && subOK(e,'communication')) ? 1 : CORNERED_RATE;
}

function subOK(e, id){
  if(!e || !e.subs) return true;
  for(const s of e.subs) if(s.id===id) return !s.dead;
  return true;
}

function subPos(e, s){
  const img = IMGS[e.img];
  if(!img) return {x:e.x, y:e.y};
  const hw = img.width*e.sc/2, hh = img.height*e.sc/2, sgn = e.flip ? -1 : 1;
  const px = hw*s.dx*sgn, py = hh*s.dy;
  const a = e.ang || 0;
  if(!a) return {x:e.x+px, y:e.y+py};
  const ca=Math.cos(a), sa=Math.sin(a);
  return {x:e.x+px*ca-py*sa, y:e.y+px*sa+py*ca};
}

function subAt(e, hx, hy){
  if(!e.subs || hx==null) return null;
  for(const s of e.subs){
    if(s.dead) continue;
    const p = subPos(e, s);
    const dx = hx-p.x, dy = hy-p.y;
    const rr = subRadius(e, s);
    if(dx*dx+dy*dy <= rr*rr) return s;
  }
  return null;
}

// Applies a hit that may have landed on a subsystem. Returns the damage
// that should still go to the hull.
function subHit(e, dmg, hx, hy){
  const s = subAt(e, hx, hy);
  if(!s) return dmg;
  s.hp -= dmg;
  if(s.hp <= 0){
    s.dead = true;
    if(e.side!=='ally') STATS.subsKilled++;
    const p = subPos(e, s);
    spawnFireball(p.x, p.y, 34, 28);
    spawnDebris(p.x, p.y, 10, 255,210,110, 255,120,0, true);
    SUB_MSGS.push({x:p.x, y:p.y, txt:s.label+' DESTROYED', life:300, ml:300,
                   ally:(e.side==='ally')});
  }
  return dmg*SUB_HULL_BLEED;
}
let SUB_MSGS = [];

// ── LUCIFER SHIELD ─────────────────────────────────────────
// A pool of its own that never recharges. While it stands the hull takes
// nothing at all, and what gets through is decided by weapon type: beams
// cut it, gunfire barely scratches it, ordnance sits in between. Shooting
// it down with bolts alone would take minutes under a boss's guns, which
// is the point: it is possible, but the reactors are the way in.
const LUCI_HULL = 'sdlucifer';
const LUCI_SHIELD = 6000;
// She carries only two beams, so once the shield is gone the second half
// of the fight was weaker than the first. Now the reverse.
const LUCI_BEAM_UNSHIELDED = 2.6;
// The Sathanas' arm beams are her main armament and were rated no higher
// than an ordinary heavy turret.
const SATH_ARM_MULT = 2.0;
const SATH_ARMS = 2;              // the two mounted furthest forward

// Effective beam damage. Kept as a function rather than baked in because
// the Lucifer's depends on whether her shield is still standing.
function beamDmg(e, b){
  let d = b.dmg;
  if(e.img===LUCI_HULL && !(e.bShield>0)) d *= LUCI_BEAM_UNSHIELDED;
  return d;
}
const LUCI_REACTORS = 5;
const LUCI_REACTOR_HP = 500;
const LUCI_REACTOR_CUT = 0.20;      // share of the pool each one takes with it
const LUCI_REACTOR_R = 22;          // hit radius around a reactor, in screen px
// Which mount positions carry a reactor. Spread across the hull so they
// cannot all be worked from one approach.
const LUCI_REACTOR_MOUNTS = [0,2,3,4,6];
const SHIELD_MULT = {beam:1.0, sec:0.25, bolt:0.10};

function initLuciShield(e){
  if(e.img !== LUCI_HULL) return;
  e.bShield = LUCI_SHIELD;
  e.bShieldMax = LUCI_SHIELD;
  e.reactors = [];
  const m = mountsFor(e.img);
  const list = (m && m.primary) ? m.primary : [];
  for(let i=0;i<LUCI_REACTOR_MOUNTS.length;i++){
    const p = list[LUCI_REACTOR_MOUNTS[i]];
    if(!p) continue;
    e.reactors.push({dx:p.dx, dy:p.dy, hp:LUCI_REACTOR_HP, maxHp:LUCI_REACTOR_HP, dead:false});
  }
  e.shieldFlares = [];
}

// World position of a reactor, following the hull the same way mounts do.
function reactorPos(e, r){
  const img = IMGS[e.img];
  if(!img) return {x:e.x, y:e.y};
  const hw = img.width*e.sc/2, hh = img.height*e.sc/2, s = e.flip ? -1 : 1;
  const px = hw*r.dx*s, py = hh*r.dy;
  const a = e.ang || 0;
  if(!a) return {x:e.x+px, y:e.y+py};
  const ca=Math.cos(a), sa=Math.sin(a);
  return {x:e.x+px*ca-py*sa, y:e.y+px*sa+py*ca};
}

// Returns the reactor an impact landed on, or null.
function reactorAt(e, hx, hy){
  if(!e.reactors || hx==null) return null;
  for(const r of e.reactors){
    if(r.dead) continue;
    const p = reactorPos(e, r);
    const dx = hx-p.x, dy = hy-p.y;
    if(dx*dx+dy*dy <= LUCI_REACTOR_R*LUCI_REACTOR_R) return r;
  }
  return null;
}

// ── BEAM IMPACTS ───────────────────────────────────────────
// A beam strikes the hull, passes through and exits on the
// far side as a flame jet. Entry and exit points
// come from the alpha masks already built for hit detection
// angelegt wurden.

const SCORCH_MAX = 14;     // scorch marks per ship
const SCORCH_LIFE = 110;   // Lebensdauer in Logikschritten

function hasMask(key){ return !!(MASKS[key] && MASKS[key] !== false); }

// Walks the beam and finds the first and last hull point.
function hullTrace(o, mx, my, ang){
  const img = IMGS[o.img];
  if(!img || !hasMask(o.img)) return null;
  const pw = img.width*o.sc, ph = img.height*o.sc;
  const R = Math.sqrt(pw*pw + ph*ph)/2;
  const ux = Math.cos(ang), uy = Math.sin(ang);
  const proj = (o.x-mx)*ux + (o.y-my)*uy;
  const from = Math.max(0, proj-R), to = proj+R;
  const step = Math.max(2, R/55);
  let entry = null, exit = null;
  for(let t=from; t<=to; t+=step){
    const px = mx+ux*t, py = my+uy*t;
    if(onHull(o.img, o.x, o.y, o.sc, o.flip, px, py, o.ang || 0)){
      if(!entry) entry = {x:px, y:py};
      exit = {x:px, y:py};
    }
  }
  return entry ? {entry:entry, exit:exit} : null;
}

// Store the scorch in sprite coordinates so it sticks to the hull.
function addScorch(o, wx, wy){
  const img = IMGS[o.img]; if(!img) return;
  const pw = img.width*o.sc, ph = img.height*o.sc, s = o.flip ? -1 : 1;
  const a = o.ang || 0;
  let ox = wx-o.x, oy = wy-o.y;
  if(a){
    const ca = Math.cos(-a), sa = Math.sin(-a);
    const rx = ox*ca - oy*sa, ry = ox*sa + oy*ca;
    ox = rx; oy = ry;
  }
  const lx = (ox/(pw/2))*s, ly = oy/(ph/2);
  if(!o.scorch) o.scorch = [];
  for(const sc of o.scorch){
    if(Math.abs(sc.lx-lx)<0.035 && Math.abs(sc.ly-ly)<0.075){
      sc.life = SCORCH_LIFE;
      sc.r = Math.min(sc.r*1.05, 9);
      return;                       // adjacent hits merge
    }
  }
  o.scorch.push({lx:lx, ly:ly, r:2.5+Math.random()*2, life:SCORCH_LIFE, ml:SCORCH_LIFE});
  if(o.scorch.length > SCORCH_MAX) o.scorch.shift();
}

function tickScorch(list){
  for(const o of list){
    if(!o.scorch) continue;
    for(let i=o.scorch.length-1;i>=0;i--){
      if(--o.scorch[i].life <= 0) o.scorch.splice(i,1);
    }
  }
}

// Glowing metal cools down: white hot, then orange, then dark red.
// The colour deliberately does not depend on who fired.
function heatColor(t, a){
  // t = 1 freshly hit, 0 fully cooled
  let r, g, b;
  if(t > 0.75){                       // white hot
    const k = (t-0.75)/0.25;
    r = 255; g = 235 - 45*(1-k); b = 190 - 120*(1-k);
  } else if(t > 0.35){                // orange
    const k = (t-0.35)/0.40;
    r = 255; g = 90 + 100*k; b = 20 + 50*k;
  } else {                            // dark red
    const k = t/0.35;
    r = 120 + 135*k; g = 10 + 80*k; b = 8 + 12*k;
  }
  return 'rgba('+(r|0)+','+(g|0)+','+(b|0)+','+a+')';
}

function drawScorch(o){
  if(!o.scorch || !o.scorch.length) return;
  const img = IMGS[o.img]; if(!img) return;
  const pw = img.width*o.sc, ph = img.height*o.sc, s = o.flip ? -1 : 1;
  const a = o.ang || 0, ca = Math.cos(a), sa = Math.sin(a);
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for(const sc of o.scorch){
    const t = sc.life/sc.ml;
    const mx0 = (pw/2)*sc.lx*s, my0 = (ph/2)*sc.ly;
    const x = o.x + (a ? mx0*ca - my0*sa : mx0);
    const y = o.y + (a ? mx0*sa + my0*ca : my0);
    const r = sc.r*(0.7+0.3*t);
    // slight flicker so the ember feels alive
    const fl = 0.88 + 0.12*Math.sin(fc*0.4 + sc.lx*40);
    try{
      const g = ctx.createRadialGradient(x,y,0,x,y,r*2.4);
      g.addColorStop(0,    heatColor(Math.min(1,t+0.25), 0.90*t*fl));
      g.addColorStop(0.38, heatColor(t,                  0.62*t*fl));
      g.addColorStop(1,    'rgba(0,0,0,0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(x,y,r*2.4,0,Math.PI*2); ctx.fill();
    }catch(err){}
  }
  ctx.restore();
}

// Der sichtbare Einschlag: Blitz vorn, Flammenstrahl hinten.
function beamImpact(o, mx, my, ang, large, tr){
  if(tr===undefined) tr = hullTrace(o, mx, my, ang);
  const scale = large ? 1.0 : 0.55;

  // Entry
  const ex = tr ? tr.entry.x : o.x, ey = tr ? tr.entry.y : o.y;
  addScorch(o, ex, ey);
  if(fc%2===0){
    spawnFireball(ex, ey, (large?15:9), (large?16:11));
    for(let i=0;i<(large?4:2);i++){
      const a = ang + Math.PI + (Math.random()-0.5)*2.2;
      const sp = 1.2+Math.random()*2.6;
      PARTS.push({x:ex, y:ey, vx:Math.cos(a)*sp, vy:Math.sin(a)*sp,
        life:16+Math.random()*14, ml:0, sz:1+Math.random()*2*scale,
        clr: Math.random()<0.5 ? '#ffffff' : '#ffcc66'});
    }
  }

  // Exit wound on the far side, with a flame jet along the beam
  if(tr && tr.exit){
    const dx = tr.exit.x-tr.entry.x, dy = tr.exit.y-tr.entry.y;
    if(dx*dx+dy*dy > 100){          // only when the beam really passes through
      addScorch(o, tr.exit.x, tr.exit.y);
      if(fc%2===0){
        spawnFireball(tr.exit.x, tr.exit.y, (large?18:10), (large?20:12));
        for(let i=0;i<(large?7:3);i++){
          const a = ang + (Math.random()-0.5)*0.55;
          const sp = 2.2+Math.random()*4.5;
          PARTS.push({x:tr.exit.x, y:tr.exit.y,
            vx:Math.cos(a)*sp, vy:Math.sin(a)*sp,
            life:20+Math.random()*22, ml:0,
            sz:(2+Math.random()*3)*scale,
            clr:['#ffffff','#ffdd88','#ff8822','#ff5511'][(Math.random()*4)|0]});
        }
      }
    }
  }
}

// ── BEAM SYSTEM ───────────────────────────────────────────────

// Colours by faction and beam type
function beamCol(faction, large) {
  // Weiss war der Rueckfall, weil die Tabelle den Hammer of Light nicht
  // kannte. Vasudanische Strahlen sind nie weiss, und HoL fliegt
  // vasudanische Ruempfe. Die Triebwerke bleiben orange: die tragen die
  // Feind-Freund-Kennung, die Strahlen nicht.
  if(faction==='hol') faction = 'vasudan';
  // The Colossus belongs to no side's column any more ('gtva'), but she
  // is a Terran-built ship and fires Terran beams.
  if(faction==='gtva') faction = 'terran';
  if(faction==='ntf' || faction==='terran') return large ? '#00ff55' : '#4499ff';
  if(faction==='shivan') return large ? '#ff2200' : '#ff4422';
  if(faction==='vasudan')return large ? '#ffcc00' : '#ffaa00';
  return '#ffffff';
}

// Beam-Mount-Definitionen pro Klasse
// dx/dy = fraction of half the sprite extent from the centre
// type: 'static' | 'slash'
// large: true = main gun, false = anti fighter
// ── MOUNT SYSTEM ──────────────────────────────────────────────
// MOUNTS is injected by the packer (build_game.py) right after SPR_DATA.
// Per ship: {facing, thrusters:[{dx,dy,len,w,dir}], primary:[{dx,dy}],
//                    secondary:[{dx,dy}], beams:[{dx,dy,large,type,...}]}
// dx/dy are fractions of half the sprite extent, measured in sprite space.

// The player used to be fixed at 0.28 scale. With the new, much
// larger sprites that produced a ship bigger than a destroyer.
// It is now normalised to a target width, the same way enemies are.
// ── BALANCE ───────────────────────────────────────────────────
// Every hull and shield value in one place. Tune here and
// you never have to hunt through the code.
// Nothing ever got tougher: a Hades in wave 10 and in wave 50 had the same
// twelve thousand. Only the number of attackers grew, and the player's
// ticket reserve grew faster than that.
const CYCLE_HULL_GROWTH = 0.25;   // je vollendetem Zyklus, Laenge siehe WAVE_CYCLE
function cycleMult(){
  return 1 + Math.floor((wave-1)/WAVE_CYCLE)*CYCLE_HULL_GROWTH;
}
// Small craft are deliberately left out: they die to one burst either way
// and scaling them would only lengthen every wave.
function capHull(v){ return Math.round(v*cycleMult()); }

const HULL = {
  fighter:   48,     // vorher 24
  bomber:   100,     // vorher 40
  cruiser: 1120,     // vorher 560
  corvette:2500,     // vorher 700
  destroyer:6500,    // vorher 1600
  boss_ntf:12000,    // vorher 2000
  boss_sh: 15000,    // vorher 2800
  station: 10400,    // Installation: 1,6 mal ein Zerstoerer
  asteroid:  40,
  // Non-combatants. A freighter is meant to be caught before it runs, not
  // to be a fight: 420 is a little under three seconds of player fire, so
  // catching it is a question of getting there rather than of damage.
  // A container dies to a stray shot, which is the point of missions that
  // ask for them to survive. A sentry gun has to be worth flying to.
  freighter: 420,
  container:  60,
  sentry:    260
};

// Shields for fighters and bombers only. Capital ships have none.
// re = recharge per step, delay = quiet time after a hit.
const SHIELD = {
  fighter: {max:30, re:0.10, delay:120},
  bomber:  {max:55, re:0.08, delay:150}
};

// ── ENEMY ARMAMENT ────────────────────────────────────
// rate = reload time per individual turret in simulation steps, as a range.
// Capital ships fire each turret independently, fighters and bombers
// dagegen als Salve, weil ihre Laeufe fest gekoppelt sind.
// big = Wahrscheinlichkeit, dass ein Schuss ein schweres Geschoss ist.
const WPN = {
  fighter:   {rate:[85,150],  big:0,
              sec:{type:'missile', rate:[520,900], dmg:12, spd:2.9, turn:0.030}},
  bomber:    {rate:[110,180], big:0,
              sec:{type:'bomb',    rate:[520,860], dmg:26, spd:1.7, turn:0.013}},
  cruiser:   {rate:[110,190], big:0.22,
              sec:{type:'missile', rate:[460,760], dmg:14, spd:2.6, turn:0.026}},
  corvette:  {rate:[100,175], big:0.28,
              sec:{type:'missile', rate:[400,660], dmg:16, spd:2.6, turn:0.026}},
  destroyer: {rate:[95,165],  big:0.32,
              sec:{type:'missile', rate:[340,580], dmg:18, spd:2.7, turn:0.026}},
  boss:      {rate:[80,140],  big:0.38,
              sec:{type:'missile', rate:[280,470], dmg:20, spd:2.8, turn:0.028}}
};

function rndR(r){ return (r[0] + Math.random()*(r[1]-r[0]))|0; }

// Gives every mount its own timer, randomly offset.
function initWeapons(e){
  const cfg = WPN[e.type]; if(!cfg) return;
  const m = mountsFor(e.img); if(!m) return;
  if(m.primary && m.primary.length)
    e.gunT = m.primary.map(function(){ return rndR(cfg.rate); });
  if(cfg.sec && m.secondary && m.secondary.length)
    e.secT = m.secondary.map(function(){ return (rndR(cfg.sec.rate)*Math.random())|0; });
  e.spreadT = 200 + (Math.random()*260|0);
}

// Sluggish but homing secondary weapon.
function eSecondary(x, y, fac, s){
  const ang = Math.atan2(player.y-y, player.x-x);
  const isBomb = (s.type === 'bomb');
  eBullets.push({
    x:x, y:y,
    vx:Math.cos(ang)*s.spd, vy:Math.sin(ang)*s.spd,
    w:isBomb?15:11, h:isBomb?15:6,
    big:false, faction:fac||'ntf',
    kind:s.type, dmg:s.dmg, hom:true, turn:s.turn, spd:s.spd,
    life:isBomb?560:440,
    hp:isBomb?1:0            // hp>0 means it can be shot down
  });
}

// Small craft carry the same load as the player: twenty missiles on a
// fighter, ten bombs on a bomber. Capital ships keep firing forever, they
// have magazines aboard. secAmmo of null means unlimited.
const SEC_AMMO_FIGHTER = 20, SEC_AMMO_BOMBER = 10;
function initSecAmmo(e){
  if(e.type==='fighter') e.secAmmo = SEC_AMMO_FIGHTER;
  else if(e.type==='bomber') e.secAmmo = SEC_AMMO_BOMBER;
  else e.secAmmo = null;
}

// Fire secondaries, each launcher on its own clock.
function fireSecondaries(e, cfg){
  if(!cfg || !cfg.sec || !e.secT) return;
  if(e.secAmmo!=null && e.secAmmo<=0) return;   // out of ordnance, guns only
  const pts = entMounts(e,'secondary');
  if(!pts || !pts.length) return;
  // An escort launches only when there is something to launch at.
  // Without this the load went out on the clock, straight to the right.
  const atg = (e.side==='ally') ? nearestEnemy(e.x, e.y) : null;
  if(e.side==='ally' && !atg){
    for(let i=0;i<e.secT.length;i++) if(e.secT[i]<30) e.secT[i]=30;
    return;
  }
  for(let i=0;i<pts.length && i<e.secT.length;i++){
    if(--e.secT[i] <= 0){
      e.secT[i] = (rndR(cfg.sec.rate) * (e.fireBoost||1))|0;
      if(e.secAmmo!=null){
        if(e.secAmmo<=0) return;
        e.secAmmo--;
      }
      if(e.side==='ally') aSecondary(pts[i].x, pts[i].y, e.faction, cfg.sec);
      else                eSecondary(pts[i].x, pts[i].y, e.faction, cfg.sec);
    }
  }
}

// The escort version. Same ordnance, but it goes into the player's bullet
// list and homes on enemies, otherwise an escort bomber would be carrying
// bombs it can never use against a capital ship.
function aSecondary(x, y, fac, s){
  const tg = nearestEnemy(x, y);
  const ang = tg ? Math.atan2(tg.y-y, tg.x-x) : 0;
  const isBomb = (s.type === 'bomb');
  pBullets.push({
    x:x, y:y,
    vx:Math.cos(ang)*s.spd, vy:Math.sin(ang)*s.spd,
    w:isBomb?16:18, h:isBomb?16:6,
    sec:true, type:s.type, homing:true, life:isBomb?300:220,
    ally:true, fac:fac, dmg:isBomb?80:35
  });
}

// Capital ships: every turret reloads on its own clock.
// Worauf ein Grosskampfschiff haelt. Verbuendete Grosskampfschiffe zuerst:
// dafuer sind die Geschuetze gebaut. Sonst der Spieler.
function capGunTarget(e){
  let best=null, bd=1e9;
  for(const a of allies){
    if(a.dead || a.small) continue;
    const d=(a.x-e.x)*(a.x-e.x)+(a.y-e.y)*(a.y-e.y);
    if(d<bd){ bd=d; best=a; }
  }
  // A ship that cannot be locked (the Pegasus) is not a target for the
  // guns either; with nothing else in reach they hold fire.
  return best || (canLockOn(player) ? player : null);
}

// -- CAPITAL FLAK ---------------------------------------------
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
function flakHas(e){ return !!FLAK_TYPES[e.type] && !e.noFlak; }
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

function capitalFire(e){
  if(e.noFire) return;
  if(!subOK(e,'weapons')) return;          // guns are out
  const cfg = WPN[e.type] || WPN.cruiser;
  const pts = entMounts(e,'primary');
  if(pts && pts.length && e.gunT){
    for(let i=0;i<pts.length && i<e.gunT.length;i++){
      if(--e.gunT[i] <= 0){
        e.gunT[i] = (rndR(cfg.rate) * (e.fireBoost||1) * corneredMult(e))|0;
        const eScat = subOK(e,'sensors') ? 1 : 4;   // blind gunnery sprays
        // Zielen statt geradeaus. Die Streuung waechst mit zerstoerten
        // Sensoren, wie vorher - nur wirkt sie jetzt um die Zielrichtung
        // herum und nicht um die Waagerechte.
        const gt = capGunTarget(e);
        if(!gt) continue;
        const ga = Math.atan2(gt.y-pts[i].y, gt.x-pts[i].x)
                 + (Math.random()-0.5)*0.10*eScat;
        if(Math.random() < cfg.big) eBig(pts[i].x, pts[i].y, e.faction);
        else                        eSmall(pts[i].x, pts[i].y, e.faction, ga);
      }
    }
    // Bosses also throw out a spread pattern
    if(e.type==='boss' && --e.spreadT <= 0){
      e.spreadT = 260 + (Math.random()*280|0);
      const p = pts[(Math.random()*pts.length)|0];
      eSpread(p.x, p.y, e.faction);
    }
  } else if(--e.fT <= 0){
    // Fallback in case a ship has no primary mounts
    e.pat++;
    if(e.pat%3===0) eBig(e.x,e.y,e.faction);
    else { eSmall(e.x,e.y,e.faction); eSmall(e.x,e.y-20,e.faction); eSmall(e.x,e.y+20,e.faction); }
    e.fT = e.fR;
  }
  fireSecondaries(e, cfg);
  flakFire(e, false);
}

// Damage of one primary volley. A ship with four barrels should
// beat one with a single barrel, but not by a factor of four,
// otherwise mount count alone decides the game.
// Small craft use the same principle as the player: a hull with four
// barrels fires four bolts, but the volley is worth about one and a half
// single barrels rather than four. Without this the Ursa hit for twice
// what any other bomber did purely because of its mount count.
// Lowered from 8. With the old grace window only one bolt of a salvo ever
// reached the player, so the figure was never actually paid in full. Now
// it is, from every attacker at once, which turned five DPS into fifty.
const E_VOLLEY_BASE = 5;        // total volley damage at one barrel
const E_VOLLEY_PER_EXTRA = 0.18;
function eVolleyDmg(n){
  if(!n || n < 1) n = 1;
  return (E_VOLLEY_BASE * (1 + (n-1)*E_VOLLEY_PER_EXTRA)) / n;
}

const VOLLEY_BASE = 44;
const VOLLEY_PER_EXTRA = 0.15;
function volleyDmg(n){
  if(!n || n < 1) n = 1;
  return (VOLLEY_BASE * (1 + (n-1)*VOLLEY_PER_EXTRA)) / n;
}

const PLAYER_W_FIGHTER = 58;   // target width in pixels
const PLAYER_W_BOMBER  = 66;

// Player flight. Top speed is a hard cap in pixels per logic step, not a
// fraction of the remaining distance. That is what keeps a tap from
// reading as a teleport, and the resulting lag behind the finger is also
// what the nose aims along.
const PLAYER_SPD_FIGHTER = 3.2;   // 320 px per second, field crossed in ~2.5 s
const PLAYER_SPD_BOMBER  = 2.4;
const AIM_DEAD = 4;          // pointer distance in px below which the aim holds
const PLAYER_TURN = 0.14;    // max heading change per logic step, half turn in ~0.22 s
// Inside the hold radius the pointer only turns the ship. Past it speed
// ramps up across a band rather than switching on hard, so small
// corrections stay fine grained. The radius follows the hull size, since
// a fixed number would sit inside the sprite of a large bomber.
const HOLD_R_MULT = 1.2;     // multiple of the half sprite extent
const HOLD_R_MIN  = 26;
const HOLD_BAND   = 45;      // px over which speed climbs from zero to full

// Enemy small ship flight.
const EFIGHTER_SPD = 2.2, EBOMBER_SPD = 1.5;      // player does 3.2, so he can disengage
const EFIGHTER_TURN = 0.050, EBOMBER_TURN = 0.032;
const ATTACK_QUOTA = 3;      // how many may run in at the same time
// Rammstoss. Ein Bomber traegt Bomben, deshalb reisst er ein Loch und
// stirbt dabei selbst. Der Wert ist ein Anteil des Ziels, nicht fest:
// sonst waere derselbe Stoss gegen einen Kreuzer toedlich und gegen einen
// Zerstoerer wirkungslos.
// Ein Kreuzer, der rammt, nimmt sein Ziel zu einem Drittel mit. Er ist
// kein Jaeger: das soll den Kampf entscheiden, nicht anknabbern.
// Kamikaze is the Hammer of Light's doctrine and nobody else's. Under the
// old rule every bomber on the field rammed, so once the cycle moved on the
// NTF and the Shivans inherited a tactic that was never theirs. rammer is
// the exception a mission hands out by name, for a wing briefed to do it.
// Both the contact test and the double chevron over the ship read this, so
// the warning and the behaviour cannot drift apart.
function ramsOnContact(e){
  return !!e.rammer || (e.type==='bomber' && e.faction==='hol');
}
const RAM_PCT_CAPITAL = 0.34;
const RAM_PCT_BOMBER  = 0.04;
const RAM_PCT_FIGHTER = 0.02;
// Wie tief die Rumpfe ineinander stehen muessen, damit es als Treffer gilt
// und nicht als knapper Vorbeiflug.
const RAM_OVERLAP = 6;
// Wie tief ein rammendes Grosskampfschiff im Ziel stehen muss, gemessen an
// seiner eigenen halben Groesse. Eine Zahl zum Drehen: hoeher heisst, er
// faehrt weiter hinein, bevor es ihn zerreisst.
const CAP_RAM_BITE = 0.85;
// Wie viel zuegiger ein Rammkurs steigt und sinkt als er vorwaerts faehrt.
// Ohne das kriecht er die Hoehe hoch und ist laengst da, bevor er auf Hoehe
// ist.
const CAP_RAM_CLIMB = 3.4;
const ATTACK_BREAK = 55;     // distance at which a run counts as delivered
const ATTACK_PASS  = 70;     // steps of flying straight through afterwards
const STAND_BAND   = 30;     // tolerance around the preferred distance
// Separation has to start early: a fighter turns at 0.05 rad per step
// and moves at 2.2, so its turning circle is about 44 px. Reacting only
// at that range leaves no room to steer clear. The small direct nudge
// on top handles head on passes, which steering alone cannot.
const SEP_R = 100, SEP_F = 1.4;  // separation radius and strength
const SEP_PUSH = 0.35;           // max px per step of direct sidestep
// Wide enough to act in: a fighter at 2.2 px per step turning 0.05 rad per
// step needs about 44 px just to come round, so the old 55 left no room.
const EDGE_M = 90;           // margin inside which the field edge pushes back
// The edge has to be able to outweigh a target sitting straight behind it.
// At equal strength the two cancelled and the ship stopped steering.
const EDGE_F = 3.0;
// A rotating hull is as tall as it is wide when it stands on its nose, so
// a fixed margin cannot hold it. Same rule the player has had since v26:
// keep half of the larger sprite extent clear.
const BOUND_MIN = 14;
function shipBound(e){
  const img = IMGS[e.img];
  if(!img) return BOUND_MIN;
  return Math.max(BOUND_MIN, Math.max(img.width, img.height)*e.sc*0.5);
}
const EFIRE_CONE = 0.42;     // half angle in rad within which they will shoot
const EFIRE_RANGE = 430;
const EBULLET_SPD = 4.5;
// Fire from a distance has to be inaccurate, otherwise standing off is
// simply better than closing in and the player gets picked apart from
// behind with no counterplay.
const ESPREAD_NEAR = 0.02, ESPREAD_FAR = 0.17;

// A side view sprite rotated past the vertical ends up on its back:
// cockpit down, gear up. Mirroring instead keeps it readable, at the cost
// of a flip at the crossing. The heading is a full 360 degrees either way,
// this only decides how it is drawn. Set to false for true rotation.
const KEEP_UPRIGHT = true;
const FLIP_HYST = 0.12;      // dead band so a hull hovering near vertical cannot flicker

// Turns a heading into a draw angle and a mirror flag. curFlip is the
// ship's current flag, which is what gives the crossing its hysteresis.
function poseFor(h, curFlip){
  let a = h;
  while(a >  Math.PI) a -= Math.PI*2;
  while(a < -Math.PI) a += Math.PI*2;
  if(!KEEP_UPRIGHT) return {ang:a, flip:false};
  const c = Math.cos(a);
  const left = curFlip ? (c < FLIP_HYST) : (c < -FLIP_HYST);
  if(!left) return {ang:a, flip:false};
  // Mirrored first, then rotated by a-PI, the nose still points along h
  // and the hull stays the right way up.
  let b = a - Math.PI;
  while(b >  Math.PI) b -= Math.PI*2;
  while(b < -Math.PI) b += Math.PI*2;
  return {ang:b, flip:true};
}

// Where to shoot so a moving target and the bolt arrive together.
function leadAngle(ex, ey, t, bs){
  const d = Math.hypot(t.x-ex, t.y-ey);
  const tof = d / (bs || EBULLET_SPD);
  return Math.atan2(t.y + (t.vy||0)*tof - ey, t.x + (t.vx||0)*tof - ex);
}

function playerSc(key){
  const img = IMGS[key || player.ship];
  if(!img || !img.width) return 0.28;
  const isBomber = isBomberHull(key || player.ship);
  const target = isBomber ? PLAYER_W_BOMBER : PLAYER_W_FIGHTER;
  return Math.min(0.6, target/img.width);
}

function mountsFor(key){
  return (typeof MOUNTS !== 'undefined' && key && MOUNTS[key]) ? MOUNTS[key] : null;
}
function spriteFacing(key){
  const m = mountsFor(key);
  return (m && m.facing === 'left') ? 'left' : 'right';
}
// Does the sprite need mirroring to face the direction we want?
// wantLeft = true for enemies, false for the player and escorts.
function needsFlip(key, wantLeft){
  if(!key) return false;
  return spriteFacing(key) !== (wantLeft ? 'left' : 'right');
}
// Returns world coordinates for every mount of one category.
function mountList(key, cx, cy, sc, flip, kind, ang){
  const m = mountsFor(key), img = IMGS[key];
  if(!m || !img || !m[kind] || !m[kind].length) return null;
  const hw = img.width*sc/2, hh = img.height*sc/2, s = flip ? -1 : 1;
  if(!ang) return m[kind].map(p => ({x: cx + hw*p.dx*s, y: cy + hh*p.dy}));
  const ca = Math.cos(ang), sa = Math.sin(ang);
  return m[kind].map(p => {
    const px = hw*p.dx*s, py = hh*p.dy;
    return {x: cx + px*ca - py*sa, y: cy + px*sa + py*ca};
  });
}
function entMounts(e, kind){
  return mountList(e.img, e.x, e.y, e.sc, e.flip, kind, e.ang || 0);
}
// Picks n points from a mount list, rotating across fire cycles.
function volley(pts, pat, n){
  const out = [];
  const c = Math.min(n, pts.length);
  for(let i=0;i<c;i++) out.push(pts[(pat*c+i) % pts.length]);
  return out;
}

// ── ENGINE PLUMES ──────────────────────────────────────────
// White at the core, faction colour outside.
function thrusterCol(faction){
  if(faction === 'vasudan') return '#ffbb22';
  if(faction === 'shivan')  return '#ff3322';
  // The NTF flies Terran hulls, and so do the escorts. Since escorts now
  // put fighters of their own into the fight, the two sides have to be
  // told apart in the middle of a dogfight. The drive plume is part of
  // the ship rather than a symbol pasted over it, and violet sits clear
  // of Terran blue, Vasudan amber and Shivan red.
  if(faction === 'ntf')     return '#a06bff';
  // Renegade Terrans fly standard Terran hulls, exactly as the GTI did in
  // Silent Threat and the Traitors wings do in Avenging Angels. There is
  // no separate paint scheme to give them, so the drive plume carries the
  // IFF: mint green sits clear of Terran blue, NTF violet, Vasudan amber
  // and Shivan red.
  if(faction === 'renegade') return '#48ffb0';
  // Hammer of Light: vasudanische Ruempfe, aber nicht die Gemeinschafts-
  // flotte. Tiefes Orange, klar getrennt vom Bernstein der verbuendeten
  // Vasudaner und vom Rot der Shivaner.
  if(faction === 'hol')      return '#ff7a1c';
  return '#4aa8ff';
}

function drawThrusters(key, cx, cy, sc, flip, faction, intensity, ang){
  const m = mountsFor(key), img = IMGS[key];
  if(!m || !img || !m.thrusters || !m.thrusters.length) return;
  const hw = img.width*sc/2, hh = img.height*sc/2, s = flip ? -1 : 1;
  const col = thrusterCol(faction);
  const amp = (intensity == null ? 1 : intensity) * (0.84 + 0.16*Math.sin(fc*0.7 + cx*0.05));
  if(amp <= 0.02) return;
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  // The plumes are built along the sprite x axis. Instead of rotating
  // every gradient by hand the whole frame is rotated, so the mount
  // points below are local to the ship centre.
  ctx.translate(cx, cy);
  if(ang) ctx.rotate(ang);
  for(const t of m.thrusters){
    const px = hw*t.dx*s, py = hh*t.dy;
    const dir = (t.dir || -1) * s;
    const len = Math.abs(t.len) * hw * amp;
    const th  = Math.abs(t.w) * hh;
    if(len < 0.6 || th < 0.6) continue;
    const tip = px + dir*len;
    try {
      const g = ctx.createLinearGradient(px, 0, tip, 0);
      g.addColorStop(0, col); g.addColorStop(0.45, col); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.globalAlpha = 0.5;
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.moveTo(px, py - th/2);
      ctx.lineTo(tip, py - th*0.08);
      ctx.lineTo(tip, py + th*0.08);
      ctx.lineTo(px, py + th/2);
      ctx.closePath(); ctx.fill();

      const gi = ctx.createLinearGradient(px, 0, px + dir*len*0.6, 0);
      gi.addColorStop(0, '#ffffff'); gi.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.globalAlpha = 0.85;
      ctx.fillStyle = gi;
      ctx.beginPath();
      ctx.moveTo(px, py - th*0.3);
      ctx.lineTo(px + dir*len*0.6, py);
      ctx.lineTo(px, py + th*0.3);
      ctx.closePath(); ctx.fill();
    } catch(ex) {}
  }
  ctx.restore();
}


// The two beams mounted furthest forward on a Sathanas sit at the tips of
// her arms, which is the pair the player sees reaching out to the left of
// the screen. Applied here so it survives any later change to her mounts.
function boostSathanasArms(e){
  if(e.img!=='sdsathanas' || !e.beams) return;
  const arms = e.beams.filter(function(b){ return b.large; })
                      .sort(function(a,b){ return b.dx-a.dx; })
                      .slice(0, SATH_ARMS);
  for(const b of arms) b.dmg *= SATH_ARM_MULT;
}

// Antijaegerstrahlen: kuerzere Ladezeit, kuerzere Pause. Die schweren
// Strahlen bleiben unangetastet - die sind gegen Grosskampfschiffe
// ausgelegt und halten gegen Jaeger ohnehin das Feuer.
const AF_CHARGE_MUL = 0.55, AF_COOL_MUL = 0.60;
function initBeams(e){
  // Nothing in FS1 carries a beam except the Lucifer, and she asks for it
  // with keepBeams. The ship is not left toothless: capitalFire() works
  // off the gun mounts and is untouched by this.
  if(eraRule('noBeams') && !e.keepBeams) return;
  const m = mountsFor(e.img);
  const def = (m && m.beams && m.beams.length) ? m.beams : null;
  if(!def) return;
  e.beams = def.map((d,i) => {
    // jit stretches or compresses this beam's cycle permanently,
    // so two turrets do not stay locked in step forever
    const jit = 0.72 + Math.random()*0.62;
    // Antijaegerstrahlen laden kuerzer und pausieren kuerzer. Bei einem
    // Zyklus von ueber fuenfzehn Sekunden nimmt ein Jaeger sie kaum als
    // Bedrohung wahr.
    const af = !d.large;
    return {
      ...d,
      chargeT: Math.round((d.chargeT||400) * (af?AF_CHARGE_MUL:1)),
      coolT:   Math.round((d.coolT||400)   * (af?AF_COOL_MUL:1)),
      state:'idle',
      jit: jit,
      // start point spread freely across the whole cycle
      timer: 20 + Math.random()*((d.chargeT||400) + (d.coolT||400)),
      angle:0, curAngle:0, sweepDir:1,
    };
  });
  boostSathanasArms(e);
}

function mountPos(e, beam) {
  const img=IMGS[e.img]; if(!img) return {x:e.x,y:e.y};
  const pw=img.width*e.sc, ph=img.height*e.sc;
  const s = e.flip ? -1 : 1;   // drawn mirrored, so flip dx
  const px = (pw/2)*beam.dx*s, py = (ph/2)*beam.dy;
  const a = e.ang || 0;
  if(!a) return {x: e.x + px, y: e.y + py};
  const ca = Math.cos(a), sa = Math.sin(a);
  return {
    x: e.x + px*ca - py*sa,
    y: e.y + px*sa + py*ca
  };
}

function updateBeams(e) {
  if(!e.beams||e.warp>0) return;
  if(!subOK(e,'weapons')){
    // Returning here left a beam that happened to be firing stuck in that
    // state forever, harmless but drawn across the screen until the ship
    // died. The battery has to be put down properly instead.
    for(const b of e.beams){
      if(b.state!=='idle'){ b.state='idle'; b.timer=1e9; b.target=null; }
    }
    return;
  }

  for(const b of e.beams) {
    b.timer--;
    if(b.state==='idle') {
      if(b.timer<=0) {
        // Find a target first. With no target it will not charge, the
        // turret holds fire and retries shortly after.
        let tgt = pickBeamTarget(e,b);
        if(!tgt && b.large && !LARGE_BEAM_HOLDS_FIRE) tgt = player;
        if(!tgt){ b.timer = 45 + Math.random()*45; }
        else {
          b.tgt = tgt;
          b.state='charging';
          b.chargeMax = b.chargeT*(b.jit||1);
          b.timer = b.chargeMax;
        }
      }
    } else if(b.state==='charging') {
      // If the turret loses its target while charging, it aborts.
      if(!targetAlive(e,b.tgt)){
        const alt = pickBeamTarget(e,b);
        if(alt) b.tgt = alt;
        else { b.state='idle'; b.timer=45+Math.random()*45; continue; }
      }
      if(b.timer<=0) {
        b.state='firing'; b.timer=b.fireT;
        const mp=mountPos(e,b);
        const tg=b.tgt;
        b.angle=Math.atan2(tg.y-mp.y, tg.x-mp.x);
        if(b.type==='slash') {
          b.sweepDir=Math.random()<0.5?1:-1;
          const arc=b.sweepArc||0.6;
          b.curAngle=b.angle - b.sweepDir*arc*0.5;
          b._arc=arc;
        } else {
          b.curAngle=b.angle;
        }
      }
    } else if(b.state==='firing') {
      if(b.type==='slash') {
        const arc=b._arc||0.6;
        b.curAngle += b.sweepDir * (arc/b.fireT);
      }
      // Damage everything on the beam line that belongs to
      // this turret's target class.
      {
        const mp=mountPos(e,b);
        const ang = b.type==='slash' ? b.curAngle : b.angle;
        for(const o of beamTargets(e, !!b.large)){
          if(!beamHits(mp.x, mp.y, ang, o.x, o.y, targetRadius(o))) continue;
          if(o === player){
            // Beams cut straight through shields, this is deliberate.
            // The damage lands on every step, exactly as it does on any
            // other hull the beam holds. Anti fighter beams are the only
            // ones that ever take the player as a target, large beams do
            // not carry him in their list at all.
            player.hp -= beamDmg(e, b);
            hullHit(player.x, player.y);
            if(fc%2===0) spawnFireball(player.x, player.y, 10, 12);
            if(player.hp<=0) playerDie();
          } else {
            // mp ist die Geschuetzposition des SCHUETZEN. Die ging bisher
            // auch an damageEnemy, und damit fragte subAt() ab, ob ein
            // Subsystem des Ziels innerhalb von hoechstens 24 Pixeln um
            // den Schuetzen liegt - der steht immer weit weg. Ergebnis:
            // Beams konnten ueberhaupt kein Subsystem und keinen Reaktor
            // der Lucifer treffen, und der Schildreflex erschien am
            // Schuetzen. Die Spur wird einmal gerechnet und an beide
            // Aufrufe gegeben, damit sie nicht doppelt anfaellt.
            const btr = hullTrace(o, mp.x, mp.y, ang);
            const hx = btr ? btr.entry.x : o.x;
            const hy = btr ? btr.entry.y : o.y;
            damageEnemy(o, beamDmg(e, b), hx, hy, false, 'beam');
            beamImpact(o, mp.x, mp.y, ang, !!b.large, btr);
          }
        }
      }
      if(b.timer<=0) { b.state='cooldown'; b.timer=b.coolT*(b.jit||1); }
    } else if(b.state==='cooldown') {
      if(b.timer<=0) { b.state='idle'; b.timer=(50+Math.random()*260)*(b.jit||1); }
    }
  }
}

function drawBeams(e) {
  if(!e.beams) return;
  for(const b of e.beams) {
    const mp=mountPos(e,b);
    const col=beamCol(e.faction, b.large);
    const cMax=b.chargeMax||b.chargeT;
    const chargeProg=Math.max(0,Math.min(1,(cMax-b.timer)/cMax));

    if(b.state==='charging') {
      const mpC=mountPos(e,b);
      const pulse=0.6+0.4*Math.sin(fc*0.5);
      const cr=Math.max(1,(b.large?14:8)*chargeProg);
      ctx.save();
      ctx.globalAlpha=0.2*pulse*chargeProg;
      ctx.shadowColor=col; ctx.shadowBlur=ecoBlur(b.large?35:18);
      ctx.fillStyle=col;
      ctx.beginPath(); ctx.arc(mpC.x,mpC.y,cr*2.8,0,Math.PI*2); ctx.fill();
      ctx.globalAlpha=chargeProg;
      try {
        var cg=ctx.createRadialGradient(mpC.x,mpC.y,0,mpC.x,mpC.y,Math.max(1,cr*1.6));
        cg.addColorStop(0,'rgba(255,255,255,1)');
        cg.addColorStop(0.3,'rgba(255,255,255,0.85)');
        var cBase=col.indexOf('rgb(')>=0?col.replace('rgb(','rgba(').replace(')',',0.6)'):col;
        cg.addColorStop(0.6,cBase);
        cg.addColorStop(1,'rgba(0,0,0,0)');
        ctx.fillStyle=cg;
      } catch(ex){ ctx.fillStyle=col; }
      ctx.beginPath(); ctx.arc(mpC.x,mpC.y,Math.max(1,cr*1.6),0,Math.PI*2); ctx.fill();
      ctx.shadowBlur=0;
      if(chargeProg>0.15&&fc%3===0){
        var ang=Math.random()*Math.PI*2;
        var dist=18+Math.random()*(b.large?40:22);
        PARTS.push({type:'mag',
          x:mpC.x+Math.cos(ang)*dist, y:mpC.y+Math.sin(ang)*dist,
          tx:mpC.x, ty:mpC.y,
          life:(10+Math.random()*8)|0, ml:0,
          sz:b.large?2.5:1.5, clr:col});
      }
      ctx.restore();
    } else if(b.state==='firing') {
      const ang = b.type==='slash' ? b.curAngle : b.angle;
      const mpF=mountPos(e,b);
      const len=2000;
      const ex=mpF.x+Math.cos(ang)*len, ey=mpF.y+Math.sin(ang)*len;
      const flicker=0.85+0.15*Math.sin(fc*0.8);
      ctx.save();
      // Outer glow
      ctx.globalAlpha=0.15*flicker;
      ctx.strokeStyle=col; ctx.lineWidth=b.large?22:10;
      ctx.shadowColor=col; ctx.shadowBlur=ecoBlur(30);
      ctx.beginPath(); ctx.moveTo(mpF.x,mpF.y); ctx.lineTo(ex,ey); ctx.stroke();
      // Mid glow
      ctx.globalAlpha=0.35*flicker;
      ctx.lineWidth=b.large?10:5;
      ctx.beginPath(); ctx.moveTo(mpF.x,mpF.y); ctx.lineTo(ex,ey); ctx.stroke();
      // Core
      ctx.globalAlpha=0.95*flicker;
      ctx.strokeStyle='#ffffff';
      ctx.lineWidth=b.large?2.5:1.5;
      ctx.shadowBlur=ecoBlur(6);
      ctx.beginPath(); ctx.moveTo(mpF.x,mpF.y); ctx.lineTo(ex,ey); ctx.stroke();
      // Muzzle orb. This is the same sphere that builds up while charging,
      // held at full size for the whole discharge. Only the inrushing
      // magnetic particles stop, the glow itself does not collapse into
      // the flat disc it used to be.
      const orbR = (b.large?14:8) * (1.0 + 0.10*Math.sin(fc*0.55));
      ctx.shadowColor=col; ctx.shadowBlur=ecoBlur(b.large?38:20);
      ctx.globalAlpha=0.24*flicker;
      ctx.fillStyle=col;
      ctx.beginPath(); ctx.arc(mpF.x,mpF.y,orbR*2.9,0,Math.PI*2); ctx.fill();
      ctx.globalAlpha=1;
      try{
        const fg=ctx.createRadialGradient(mpF.x,mpF.y,0,mpF.x,mpF.y,Math.max(1,orbR*1.7));
        fg.addColorStop(0,'rgba(255,255,255,1)');
        fg.addColorStop(0.32,'rgba(255,255,255,0.9)');
        const fBase=col.indexOf('rgb(')>=0?col.replace('rgb(','rgba(').replace(')',',0.65)'):col;
        fg.addColorStop(0.62,fBase);
        fg.addColorStop(1,'rgba(0,0,0,0)');
        ctx.fillStyle=fg;
      }catch(ex){ ctx.fillStyle=col; }
      ctx.beginPath(); ctx.arc(mpF.x,mpF.y,Math.max(1,orbR*1.7),0,Math.PI*2); ctx.fill();
      ctx.shadowBlur=0;

      // Sparks thrown forward out of the muzzle
      if(fc%2===0){
        for(let s=0;s<(b.large?2:1);s++){
          const sa=ang+(Math.random()-0.5)*0.5;
          const sp=2+Math.random()*4;
          PARTS.push({x:mpF.x,y:mpF.y,vx:Math.cos(sa)*sp,vy:Math.sin(sa)*sp,
            life:(9+Math.random()*9)|0, ml:0,
            sz:(b.large?2:1.2)+Math.random(), clr:Math.random()<0.5?'#ffffff':col});
        }
      }
      ctx.restore();
    }
  }
}

