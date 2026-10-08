// ── DRAW ─────────────────────────────────────────────────────
function draw(){
  // The scale transform used to be set once at startup. If the context is
  // lost and restored, or if a frame throws between save and restore, that
  // single setup is gone for good and every later frame draws unscaled into
  // the top left corner while the clear below misses the rest of the buffer.
  // Re-establishing both every frame turns that into one dropped frame.
  // restore() on an empty stack is defined as a no-op, so draining is safe.
  for(let i = 0; i < 8; i++) ctx.restore();
  ctx.setTransform(RES_X, 0, 0, RES_Y, 0, 0);
  if(shakeT>0){
    const k = shakeMag*(shakeT>12?1:shakeT/12);
    ctx.translate((Math.random()-0.5)*k, (Math.random()-0.5)*k);
  }
  // Nuclear reset: jeder Frame startet sauber
  ctx.globalAlpha=1;
  ctx.globalCompositeOperation='source-over';
  ctx.shadowBlur=0;
  ctx.shadowColor='transparent';
  ctx.lineWidth=1;
  ctx.setLineDash([]);
  ctx.fillStyle='#000';ctx.fillRect(0,0,W,H);
  if(GS==='playing' && subspaceOn()) drawSubspace();
  else { drawNebula(); drawBodies(); drawStars(); }

  if(GS==='title'){drawTitle(); if(typeof f3dPreloadBar==='function') try{ f3dPreloadBar(); }catch(ep){} return;}
  if(GS==='gameover'){drawGO();return;}

  const loaded=imgsLoaded+nebsLoaded;
  if(loaded<TOTAL){
    ctx.fillStyle=TH('text');ctx.font=thValue(16, false);
    ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText('Loading... '+loaded+'/'+TOTAL,W/2,H/2);return;}



  for(const b of pBullets){
    if(!b.sec){
      // Laser: the weapon's own colours (v161: every side, every gun),
      // drawn with trail, core and sparks, see drawLaser().
      const rc = raceCol(b.fac);
      const aCore = b.col || (b.ally ? rc.core : '#ccff88');
      const aGlow = b.glow || (b.ally ? rc.glow : 'rgba(180,255,80,0.3)');
      drawLaser(b, aCore, aGlow, hotOf(aCore));
    } else if(b.sec){
      // The race's colour around the ordnance: an escort's by its side,
      // the player's by the hull he flies (Silvio, v161).
      const oc = raceCol(b.ally ? b.fac : shipFac(player.ship));
      if(b.type==='missile'){
        // Missile: metallic body plus engine glow, drawn along its flight
        // direction (Silvio, v187: it always pointed to the right).
        ctx.save();
        ctx.translate(b.x, b.y);
        ctx.rotate(Math.atan2(b.vy, b.vx));
        const hw=b.w/2;
        // Engine glow at the tail, in the race's colour
        ctx.fillStyle=oc.glow;
        ctx.beginPath();ctx.ellipse(-hw,0,7,5,0,0,Math.PI*2);ctx.fill();
        ctx.fillStyle=oc.core;
        ctx.beginPath();ctx.ellipse(-hw,0,3,2,0,0,Math.PI*2);ctx.fill();
        // Body
        ctx.fillStyle='#aabbcc';
        ctx.fillRect(-hw+4,-2,b.w-6,4);
        // Nose
        ctx.fillStyle='#dd4422';
        ctx.beginPath();ctx.moveTo(hw,0);
        ctx.lineTo(hw-6,-2);ctx.lineTo(hw-6,2);
        ctx.closePath();ctx.fill();
        // Fins
        ctx.fillStyle='#8899aa';
        ctx.fillRect(-hw+4,-4,5,2);
        ctx.fillRect(-hw+4,2,5,2);
        ctx.restore();
      } else {
        // Bomb: dark sphere with a pulsing warning glow
        const pulse=0.5+0.5*Math.sin(fc*0.25);
        const br=b.w/2;
        // Outer warning ring, in the race's colour
        ctx.globalAlpha=0.3+pulse*0.5;
        ctx.strokeStyle=oc.core;
        ctx.lineWidth=2;
        ctx.beginPath();ctx.arc(b.x,b.y,br+4+pulse*4,0,Math.PI*2);ctx.stroke();
        ctx.globalAlpha=1;
        // Bomb body
        const grad=ctx.createRadialGradient(b.x-br*0.3,b.y-br*0.3,0,b.x,b.y,br);
        grad.addColorStop(0,'#445566');grad.addColorStop(1,'#111122');
        ctx.fillStyle=grad;
        ctx.beginPath();ctx.arc(b.x,b.y,br,0,Math.PI*2);ctx.fill();
        // Warn-Indikator (blinkt)
        ctx.fillStyle='rgba(255,'+(Math.floor(pulse*80))+',0,'+(0.6+pulse*0.4)+')';
        ctx.beginPath();ctx.arc(b.x,b.y,br*0.35,0,Math.PI*2);ctx.fill();
        ctx.fillStyle='#ffffff';
        ctx.beginPath();ctx.arc(b.x-br*0.25,b.y-br*0.25,br*0.1,0,Math.PI*2);ctx.fill();
      }
    } else {
      }
  }

  for(const b of eBullets){
        const bx=b.x|0, by=b.y|0;
    if(b.kind){
      const ang=Math.atan2(b.vy,b.vx);
      // Missiles and bombs in the colour of the race (Silvio, v161):
      // Shivans red, Terrans - the NTF among them - blue, Vasudans yellow.
      const race=raceOf(b.faction);
      const shiv=race==='shivan', vas=race==='vasudan';
      const body=shiv?'#ffb0a0':(vas?'#ffe2a8':'#c8e4ff');
      const glow=shiv?'rgba(255,60,0,0.5)':(vas?'rgba(255,160,40,0.5)':'rgba(70,160,255,0.5)');

      // Halo underneath the ordnance so it never blends into a nebula.
      // Drawn unrotated and additively, then the body goes on top.
      const halo=(b.kind==='bomb'?2.6:1.9)*b.w*(0.92+0.08*Math.sin(fc*0.5));
      ctx.save();
      ctx.globalCompositeOperation='lighter';
      try{
        const hg=ctx.createRadialGradient(bx,by,0,bx,by,halo);
        hg.addColorStop(0, shiv?'rgba(255,190,150,0.85)':(vas?'rgba(255,225,160,0.85)':'rgba(190,220,255,0.85)'));
        hg.addColorStop(0.30, shiv?'rgba(255,90,40,0.45)':(vas?'rgba(255,150,40,0.45)':'rgba(70,150,255,0.45)'));
        hg.addColorStop(1,'rgba(0,0,0,0)');
        ctx.fillStyle=hg;
        ctx.beginPath(); ctx.arc(bx,by,halo,0,Math.PI*2); ctx.fill();
      }catch(ex){}
      ctx.restore();

      // Glowing sparks shed along the flight path
      if(fc%2===0){
        const sa=ang+Math.PI+(Math.random()-0.5)*0.8;
        const sp=0.6+Math.random()*1.4;
        PARTS.push({x:bx,y:by,vx:Math.cos(sa)*sp,vy:Math.sin(sa)*sp,
          life:(12+Math.random()*12)|0, ml:0,
          sz:(b.kind==='bomb'?2.2:1.5)+Math.random(),
          clr: shiv ? (Math.random()<0.5?'#ffdd99':'#ff7744')
             : vas  ? (Math.random()<0.5?'#ffffff':'#ffc860')
                    : (Math.random()<0.5?'#ffffff':'#88c8ff')});
      }

      ctx.save();
      ctx.translate(bx,by); ctx.rotate(ang);
      // Exhaust plume trailing behind
      ctx.globalAlpha=0.75;
      const fl=ctx.createLinearGradient(0,0,-b.w*1.6,0);
      fl.addColorStop(0,'#ffffff'); fl.addColorStop(0.35,shiv?'#ff8844':(vas?'#ffb040':'#7ab8ff'));
      fl.addColorStop(1,'rgba(0,0,0,0)');
      ctx.fillStyle=fl;
      ctx.beginPath();
      ctx.moveTo(-b.w*0.4,-b.h*0.30);
      ctx.lineTo(-b.w*1.6,0);
      ctx.lineTo(-b.w*0.4, b.h*0.30);
      ctx.closePath(); ctx.fill();
      // Rumpf
      ctx.globalAlpha=0.35; ctx.fillStyle=glow;
      ctx.beginPath(); ctx.ellipse(0,0,b.w*0.95,b.h*0.95,0,0,Math.PI*2); ctx.fill();
      ctx.globalAlpha=1; ctx.fillStyle=body;
      if(b.kind==='bomb'){
        ctx.beginPath(); ctx.arc(0,0,b.w*0.42,0,Math.PI*2); ctx.fill();
        // White hot core so the bomb reads instantly against any background
        ctx.fillStyle='#ffffff';
        ctx.beginPath(); ctx.arc(0,0,b.w*0.20,0,Math.PI*2); ctx.fill();
        ctx.strokeStyle='#ffffff'; ctx.lineWidth=1.6;
        ctx.globalAlpha=0.6+0.4*Math.sin(fc*0.35);
        ctx.beginPath(); ctx.arc(0,0,b.w*0.62,0,Math.PI*2); ctx.stroke();
        // Second, expanding warning ring
        const rr=b.w*(0.62+0.5*((fc%40)/40));
        ctx.globalAlpha=0.38*(1-((fc%40)/40));
        ctx.beginPath(); ctx.arc(0,0,rr,0,Math.PI*2); ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.moveTo(b.w*0.62,0);
        ctx.lineTo(-b.w*0.35,-b.h*0.58);
        ctx.lineTo(-b.w*0.35, b.h*0.58);
        ctx.closePath(); ctx.fill();
        ctx.fillStyle='#ffffff';
        ctx.beginPath();
        ctx.moveTo(b.w*0.34,0);
        ctx.lineTo(-b.w*0.12,-b.h*0.26);
        ctx.lineTo(-b.w*0.12, b.h*0.26);
        ctx.closePath(); ctx.fill();
      }
      ctx.restore(); ctx.globalAlpha=1;
      continue;
    }
    // Bolts: the weapon's colours (v161). A round without any (freighter
    // guns, a hull without a loadout) takes its race's colour.
    const rc=raceCol(b.faction);
    const eCore=b.col||rc.core, eGlow=b.glow||rc.glow;
    drawLaser(b, eCore, eGlow, hotOf(eCore));
  }

  // Warp vortex with a null check and try/catch
  // Sorted by footprint so capital ships sit behind fighters. Residual
  // overlap then reads as depth instead of two hulls clipping.
  const SHIPS_ON_FIELD = (allies.length ? enemies.concat(allies) : enemies.slice())
    .sort(function(a,b){
      const ia=IMGS[a.img], ib=IMGS[b.img];
      const fa=ia?ia.width*a.sc*ia.height*a.sc:0;
      const fb=ib?ib.width*b.sc*ib.height*b.sc:0;
      return fb-fa;
    });
  // Vortices of ships no longer on the field (a portal still closing).
  if(WARP_IMG&&WARP_IMG.complete&&WARP_IMG.naturalWidth>0){
    const _onField = new Set(SHIPS_ON_FIELD);
    try{ drawFsPortals(function(p){ return !_onField.has(p.e); }); }catch(ep){ ctx.restore(); ctx.globalAlpha=1; }
  }

  // Beam rays under every hull: a ship lies on top of the beam that
  // hits it, which reads as the beam running through her.
  for(const e of SHIPS_ON_FIELD){
    try{ drawBeamRays(e); }catch(eb){ ctx.restore(); }
  }
  ctx.globalAlpha=1;

  // Wreckage sits behind the ships: it is scenery that bites, not a unit.
  ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
  drawDebris();

  // State-Reset vor Enemy-Render
  ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
  // v196: capital ships with a 3D model are drawn first and all at once
  // (59_field3d.js), with their vortex and thrusters under them. The loop
  // below then only puts their damage, marks and bars on top.
  let F3D_DONE = null;
  try{ if(typeof f3dFieldPass === 'function') F3D_DONE = f3dFieldPass(SHIPS_ON_FIELD); }catch(e3){ F3D_DONE = null; }
  for(const e of SHIPS_ON_FIELD){
    const _f3 = !!(F3D_DONE && F3D_DONE.has(e));
    if(_f3){
      try{ f3dShipTop(e); }catch(et){ ctx.restore(); ctx.globalAlpha=1; ctx.globalCompositeOperation='source-over'; }
      continue;
    }
    try{ drawVortexOf(e); }catch(ev){ ctx.restore(); ctx.globalAlpha=1; }
    ctx.globalAlpha=1; ctx.globalCompositeOperation='source-over';
    try{
    // Ship only visible once the vortex is fully open (phase 2 and 3)
    // wAlpha carries the fade in from the vortex. It used to be
    // wiped out one line later by globalAlpha=1,
    // which is why ships used to pop in.
    var wAlpha=1;
    // FreeSpace style: the hull slides through the vortex and is cut off
    // where it has not come through yet. Nothing else is drawn until the
    // jump is over.
    fsTrack(e);
    const fgs = fsWarp(e);
    if(fgs){
      if(!fgs.vis) continue;
      ctx.save();
      fsWarpClip(fgs);
      ctx.translate(fgs.dx, fgs.dy);
      drawThrusters(e.img,e.x|0,e.y|0,e.sc,e.flip,e.faction,fgs.out?1:0.6,e.ang||0,e);
      drawShipE(e,e.x|0,e.y|0,e.sc,e.flip,e.ang||0);
      ctx.restore();
      warpBeamOrbs(e, fgs);
      continue;
    }
    if(e.warp>0){
      var mWw=e.warpMax||100;
      var elW=mWw-e.warp;
      if(elW<mWw*0.40) continue;                 // vortex not open yet
      if(elW<mWw*0.60) wAlpha=(elW-mWw*0.40)/(mWw*0.20);
    } else if(e.warpOut>0){
      // Reversed sequence: vortex opens, ship disappears into it
      var mWo=e.warpMax||100;
      var elO=mWo-e.warpOut;
      if(elO>mWo*0.60) continue;                 // ship has gone through
      if(elO>mWo*0.40) wAlpha=1-(elO-mWo*0.40)/(mWo*0.20);
    }
    ctx.globalAlpha=wAlpha;
    // No damage blink. The hull bar already carries that information.
    if(e.type==='asteroid'){
      const r=16*e.sc;
      if(e.tex==null) e.tex=(Math.random()*AST_VARIANTS)|0;
      const t=AST_TEX[e.tex];
      if(t){
        const d=r/t.R*t.S;
        ctx.save();
        ctx.translate(e.x|0,e.y|0); ctx.rotate(e.rot);
        ctx.drawImage(t.c, -d/2, -d/2, d, d);
        ctx.restore();
        drawRockLight(e, r);
      }
    }else{
      drawThrusters(e.img,e.x|0,e.y|0,e.sc,e.flip,e.faction,e.warp>0?0.35:1,e.ang||0,e);
      drawShipE(e,e.x|0,e.y|0,e.sc,e.flip,e.ang||0);
      drawShipTop(e);
    }
    ctx.globalAlpha=1;
    }catch(ee){ctx.restore();ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';}}
  ctx.shadowBlur=0;ctx.shadowColor='transparent';

  try{
    drawHoldRing();
    {
      const _pf=player.flip||false;
      const _js=jumpScale();
      if(_js>=1){
        drawThrusters(player.ship,player.x|0,player.y|0,playerSc(),_pf,'terran',
          playerThrust(),
          player.ang||0);
      }
      // A Ptah nobody can see is drawn faint (v170). Not a Mara in
      // disguise: she is in plain sight, only taken for one of theirs.
      if(player.ship===PTAH_HULL && !playerSeen()) ctx.globalAlpha = 0.45 + 0.1*Math.sin(fc*0.1);
      drawShip(player.ship,player.x|0,player.y|0,playerSc()*_js,_pf,player.ang||0);
      ctx.globalAlpha = 1;
      if(_js>=1) drawPlayerShield();
      drawJumpVortex();
    }
  }catch(ep2){ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';}
  // Fadenkreuz an Mausposition
  const mx=MOUSE.x|0,my=MOUSE.y|0;
  ctx.strokeStyle=MOUSE.down?'rgba(255,255,100,0.9)':'rgba(0,255,136,0.7)';
  ctx.lineWidth=1;
  ctx.beginPath();ctx.moveTo(mx-10,my);ctx.lineTo(mx+10,my);ctx.stroke();
  ctx.beginPath();ctx.moveTo(mx,my-10);ctx.lineTo(mx,my+10);ctx.stroke();
  ctx.beginPath();ctx.arc(mx,my,4,0,Math.PI*2);ctx.stroke();

  try{drawParts();}catch(ep){}

  // Treffer-Flashes
  if(shieldFlash>0){
    ctx.fillStyle='rgba(0,100,255,'+(shieldFlash/8*0.07)+')';
    ctx.fillRect(0,0,W,H); shieldFlash--;
  }
  if(hullFlash>0){
    ctx.fillStyle='rgba(255,80,0,'+(hullFlash/7*0.08)+')';
    ctx.fillRect(0,0,W,H); hullFlash--;
  }

  // HUD IMMER — State garantiert sauber
  ctx.globalAlpha=1;
  ctx.globalCompositeOperation='source-over';
  ctx.shadowBlur=0;
  // Haze and interference sit over ships and wreckage. Pickups and
  // messages go on top of them, so nothing is lost in the murk that the
  // player has no way to shoot at.
  drawBombPortals();
  drawShocks();
  drawNebulaFog();
  try{ drawAwacsRings(); }catch(ea){ ctx.restore(); }
  drawEmpWarn();
  drawEmpFX();
  drawItems();
  drawTicketMsgs();
  drawSubMsgs();
  if(whiteOut>0){ ctx.fillStyle='rgba(255,250,235,'+Math.min(0.85, whiteOut/WHITEOUT_T).toFixed(3)+')';
                  ctx.fillRect(0, HUD_H, W, H-HUD_H); }
  // The shake must not reach the instruments, so the transform is put
  // back before the strip is drawn.
  ctx.setTransform(RES_X, 0, 0, RES_Y, 0, 0);
  drawHUD();
  // Blackout is drawn over the strip rather than skipping it, so the
  // instruments visibly fail instead of quietly disappearing.
  drawEmpHudGlitch();
  drawFleeWarning();
  drawPlogCard();
  drawFieldBanner();
  tickFps();
  drawFps();
  drawObjCount();
  drawWaveTitle();
  drawSettings();
  // Opening the settings pauses the game, so without this the pause
  // notice printed straight across the panel it had just opened.
  if(paused && !settingsOpen) drawPaused();
}

// Everything that goes on a ship after her hull: marks, hull bar, shields,
// subsystems and her own beams. The sprite loop and the 3D ships (v196)
// both use it.
function drawShipTop(e){
  // Dying (v183): no bar, no name, no marks - she is done with, and the
  // player can see at once that it is time for the next target (Silvio).
  const _dying = e.rollT!=null;
  if(!_dying){
  drawHostileMark(e);
  drawTagMark(e);
  drawScorch(e);
  drawShield(e);
  drawScanRing(e);
  }

  // Freighters count too: transports, miners and hospital ships are
  // often what a mission is about, and how much hull they have left is
  // what decides how hard to fight for them.
  if(!_dying && (e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||
     e.type==='boss'||e.type==='station'||e.type==='freighter')){
    const hbImg=IMGS[e.img];if(hbImg){
      var bwMult=(e.type==='boss'?0.75:(e.type==='destroyer'?0.55:
                 (e.type==='freighter'?0.80:0.70)));
      const bw=hbImg.width*e.sc*bwMult;
      const bx=(e.x-bw*.5)|0,by=(e.y-hbImg.height*e.sc*.5-6)|0;
      ctx.globalAlpha=1;
      // While the shield holds, the hull bar would sit at full and say
      // nothing. Show the shield instead, so the bar always tracks what
      // is actually being shot at.
      var showShield=(e.bShield>0);
      var hpRatio=showShield?Math.max(0,e.bShield/e.bShieldMax)
                            :Math.max(0,e.hp/e.maxHp);
      // Fill says condition, outline says side. One meaning per
      // channel, so a glance at the colour is never ambiguous.
      drawHullBlocks(e, bx, by, bw, hpRatio, showShield);
    }}
  ctx.globalAlpha=1;
  if(e.rollT!=null){ /* dying: nothing on her any more */ }
  else if(e.bShield>0){ drawLuciShield(e); drawReactors(e); }
  // In subspace the Lucifer has no shield, only her reactors (v170).
  else if(e.reactorOnly) drawReactors(e);
  // Our own ships carry no subsystem marks: the enemy does not aim at
  // them, and the player has nothing to do with them (Silvio, v166).
  else if(e.side!=='ally') drawSubsystems(e);
  drawBeams(e);
}

// The pause notice: a panel from the kit over a dimmed field.
function drawPaused(){
  ctx.fillStyle='rgba(0,0,8,0.50)'; ctx.fillRect(0,0,W,H);
  const pw=300, ph=92, px=((W-pw)/2)|0, py=((H-ph)/2)|0;
  thPlate(px, py, pw, ph, thRGBA('panelBack', 0.90), 12);
  thGlowPath(px, py, pw, ph, 12, 0.9);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.save();
  ctx.shadowColor='rgba('+TH('glow')+',0.55)'; ctx.shadowBlur=ecoBlur(18);
  ctx.fillStyle=TH('textBright'); ctx.font=thLabel(28);
  ctx.fillText('PAUSED', W/2, py+36);
  ctx.restore();
  ctx.fillStyle=TH('textDim'); ctx.font=thValue(12, false);
  ctx.fillText('Press P or tap to resume', W/2, py+68);
  ctx.textAlign='left'; ctx.textBaseline='top';
}

// The countdown used to live in the HUD bar, in the same strip as the
// escort status panel and only while no escort was deployed, so calling
// support hid the one piece of information with a deadline on it. On the
// top edge of the field it has no competition.
// The ticket grid now fills the whole strip the boss notice used to share,
// so it moves down here alongside the jump out countdown. The two can never
// appear together: only the Runner wave has a deadline and it has no boss.
// Alle 120 Eintraege der Mount-Datei tragen ihren Namen im Feld tags,
// vom GTSC Faustus bis zur VC 3. MOUNTS liegt ohnehin im Build, die
// Zielanzeige braucht also keine zweite Namenstabelle - und keine zweite
// Kopie, die auseinanderlaufen kann.
//
// Neun vasudanische Eintraege fuehren BEIDE Praefixe, weil das Schiff je
// nach Aera anders heisst: zu FS1- und ST:R-Zeiten Parlamentsflotte (PV),
// nach dem Beitritt zur GTVA Gemeinschaftsflotte (GV). Ungefiltert stuende
// im Bild "STOP 2 PVFR OR GVFR MA'AT".
// Betroffen: Osiris, Aten, Typhon, Horus, Seth, Thoth, Ma'at, Satis, Isis.
// Gewaehlt wird nach Praefix und nicht nach Position, damit ein Eintrag in
// der Reihenfolge "GVF or PVF" nicht die falsche Haelfte liefert.
const NAME_ALT = /^([A-Za-z]+) or ([A-Za-z]+) (.+)$/;
function shipName(key, fallback){
  const m = mountsFor(key);
  let t = m && m.tags && m.tags[0];
  if(!t) return (fallback || 'SHIP').toUpperCase();
  const a = NAME_ALT.exec(t);
  if(a){
    const want = (currentEra === 'fs2') ? 'GV' : 'PV';
    const pick = (a[1].indexOf(want) === 0) ? a[1]
               : ((a[2].indexOf(want) === 0) ? a[2] : a[1]);
    t = pick + ' ' + a[3];
  }
  return t.toUpperCase();
}

// Was der Spieler gerade zu tun hat, in der Reihenfolge, in der es
// dringend ist. Gelesen wird der Zustand des Feldes, nicht der Wellenplan:
// ein Ziel, das erledigt ist, verschwindet damit von selbst.
function objectiveText(){
  for(const a of allies)
    if(a.guard && !a.dead)
      return {txt:'[ PROTECT THE '+shipName(a.img, a.label || 'ESCORT')+' ]',
              col:'#ffbb22', ink:'#ffd257'};
  if(disableTarget && !disableTarget.dead && !disableDone())
    return {txt:'[ DISABLE THE '+shipName(disableTarget.img,'TARGET')+' ]',
            col:'#22bbff', ink:'#7fd6ff'};
  let nScan=0, nRun=0;
  for(const e of enemies){
    if(e.dead) continue;
    if(e.scan && !e.scanned) nScan++;
    if(e.runner) nRun++;
  }
  if(nScan)
    return {txt:'[ SCAN '+nScan+' CARGO ]', col:'#22bbff', ink:'#7fd6ff'};
  let nEsc=0;
  for(const e of enemies) if(e.escaping && !e.dead) nEsc++;
  if(nEsc)
    return {txt:'[ STOP '+nEsc+' RUNNER'+(nEsc>1?'S':'')+' ]',
            col:'#ffbb22', ink:'#ffd257'};
  if(nRun)
    return {txt:'[ STOP '+nRun+' FREIGHTER'+(nRun>1?'S':'')+' ]',
            col:'#ffbb22', ink:'#ffd257'};
  return null;
}

// Wie lange nach Erledigung eines Auftrags die Erfolgsmeldung steht.
const OBJ_DONE_TIME = 220;    // 2,2 s
let objWasSet = false, objDoneT = 0, objFailed = false;
// Gerettete und verlorene Schuetzlinge dieser Welle. Daraus entsteht der
// dritte Ausgang zwischen Erfolg und Fehlschlag.
let protSaved = 0, protLost = 0;

// Titel der laufenden Welle. Wird von buildFS1Wave gesetzt und in
// nextWave geleert, damit eine Welle ohne Titel nicht den vorigen erbt.
let waveTitle='', titleT=0;
const TITLE_TIME=300;      // 3 s bei 100 Schritten je Sekunde
function drawWaveTitle(){
  return;   // Wellenueberschrift abgeschaltet, siehe Kommentar oben
  /* eslint-disable no-unreachable */
  if(GS!=='playing' || !waveTitle || titleT<=0) return;
  if(!paused) titleT--;
  // Weicher Ausklang im letzten Drittel, damit er nicht abgeschnitten wirkt.
  const a = Math.min(1, titleT/(TITLE_TIME*0.34));
  ctx.save();
  ctx.globalAlpha = a;
  ctx.font='bold 15px Courier New';
  ctx.textAlign='center'; ctx.textBaseline='top';
  const tw=ctx.measureText(waveTitle).width;
  ctx.globalAlpha=a*0.66; ctx.fillStyle='#000';
  ctx.fillRect(((W-tw)/2-12)|0, (H*0.30)|0, (tw+24)|0, 24);
  ctx.globalAlpha=a;
  ctx.strokeStyle='#00aa44'; ctx.lineWidth=1;
  ctx.strokeRect(((W-tw)/2-12)|0, (H*0.30)|0, (tw+24)|0, 24);
  ctx.fillStyle='#00ee55';
  ctx.fillText(waveTitle, W/2, (H*0.30)|0+5);
  ctx.restore();
  /* eslint-enable no-unreachable */
}

const CHEV_FULL = 120;    // bis hierher voll sichtbar
const CHEV_FADE = 240;    // ab hier gar nicht mehr - Nebelsichtweite
function drawHostileMark(e){
  // SHIPS_ON_FIELD ist enemies.concat(allies) - ohne diese Zeile bekaeme
  // jeder Verbuendete denselben Winkel. Ein Ueberlaeufer hat nach defect()
  // side='enemy' und bekommt ihn dann zu Recht.
  if(e.side === 'ally') return;
  if(e.type!=='fighter' && e.type!=='bomber') return;
  if(e.dead || e.warp>0 || e.warpOut>0) return;
  let a = 1;
  if(nebulaOn()){
    const d = Math.hypot(e.x-player.x, e.y-player.y);
    if(d >= CHEV_FADE) return;
    a = (d <= CHEV_FULL) ? 1 : (CHEV_FADE-d)/(CHEV_FADE-CHEV_FULL);
  }
  const img = IMGS[e.img];
  const h = img ? img.height*e.sc : 30;
  const y = e.y - h*0.5 - 9;
  // Im Anflug ein anderes Zeichen: ein Schiff, das gleich einschlaegt,
  // soll sich von einem unterscheiden, das nur vorbeifliegt. In FreeSpace
  // warnt der Funk davor - hier muss es das Bild tun.
  // Gelb nur, wenn dieser Bomber gerade ein verbuendetes Grosskampfschiff
  // anfliegt - dann lohnt es, ihn vorzuziehen. Ein Anflug auf den Spieler
  // bleibt rot wie jeder andere Gegner.
  let run = false;
  if(ramsOnContact(e) && e.role==='attack' && e.passT<=0){
    const t = smallTarget(e);
    run = !!(t && t!==player && !t.small && t.side==='ally');
  }
  ctx.save();
  ctx.globalAlpha = a;
  ctx.strokeStyle = run ? '#ffcc22' : '#ff2a1a';
  ctx.lineWidth = 2;
  ctx.beginPath();
  if(run){
    // Doppelwinkel, blinkend
    if(fc%24 < 17){
      ctx.moveTo(e.x-7, y-6); ctx.lineTo(e.x, y);   ctx.lineTo(e.x+7, y-6);
      ctx.moveTo(e.x-7, y-11);ctx.lineTo(e.x, y-5); ctx.lineTo(e.x+7, y-11);
    }
  } else {
    ctx.moveTo(e.x-6, y-5); ctx.lineTo(e.x, y); ctx.lineTo(e.x+6, y-5);
  }
  ctx.stroke();
  ctx.restore();
}

// ── OBJECTIVES ───────────────────────────────────────────────
// Two parts. A card comes in at the top of the field whenever there is
// something new to know - a new objective, one met, one failed - and goes
// again after a couple of seconds. A line under the bar, on the left,
// keeps the current objective in view afterwards without covering the
// fight. Nothing blinks: the card arriving is the signal.
const OBJ_CARD_TIME = 230;    // steps a card stays, fades included
const OBJ_CARD_FADE = 18;     // steps to come in, and to go
const OBJ_TONE = {done:'#4dff88', fail:'#ff5533', part:'#ffcc44'};
let objCard = null;           // {head, txt, tone, t0}
let objPinned = '';           // the objective the last card announced
let missionObj = '';          // a mission's own objective, see 'ziel'
let missionObjUsed = false;   // this wave speaks for itself
function objStrip(t){ return String(t||'').replace(/^\[\s*/, '').replace(/\s*\]$/, ''); }
function objAnnounce(head, txt, tone){ objCard = {head:head, txt:txt, tone:tone, t0:fc}; }
// What the player is to do right now, or null. A mission's own words
// come first; otherwise whatever the field says.
function currentObjective(){
  if(missionObj) return {txt:missionObj, col:TH('accentWarm')};
  // A mission that speaks for itself is not talked over by the field:
  // between its own objectives there is nothing automatic to announce.
  if(missionObjUsed) return null;
  const ob = objectiveText();
  return ob ? {txt:objStrip(ob.txt), col:ob.col} : null;
}
function drawFieldBanner(){
  if(GS!=='playing') return;
  const ob = objectiveText();
  const prev = objPinned;
  // Bookkeeping of the automatic objectives, as before: while one stands
  // it counts as set, and when it goes it was met or failed.
  if(ob){ objWasSet = true; objSeenOnce = true; }
  else if(objWasSet){
    objWasSet = false; objDoneT = OBJ_DONE_TIME; objFailed = guardLost;
    if(!missionObjUsed){
      if(objFailed && protSaved>0)
        objAnnounce('PARTIAL SUCCESS', protSaved+' OF '+(protSaved+protLost)+' GOT THROUGH', 'part');
      else objAnnounce(objFailed ? 'OBJECTIVE FAILED' : 'OBJECTIVE COMPLETE',
                       prev || 'OBJECTIVE', objFailed ? 'fail' : 'done');
    }
  }
  if(objDoneT>0 && !paused) objDoneT--;
  const cur = currentObjective();
  if(cur){ if(cur.txt!==objPinned){ objPinned = cur.txt; objAnnounce('NEW OBJECTIVE', cur.txt, 'new'); } }
  else objPinned = '';
  // A card waits for the jump in to finish: nobody reads it in the dark.
  if(objCard && arriveT>0) objCard.t0 = fc;
  // The line: the objective, or failing that what is left to do.
  let pin = cur;
  if(!pin){
    const bossInQ = spawnQ.some(function(s){ return s.type==='boss_ntf'||s.type==='boss_sh'; });
    if(bossInQ || bossAlive) pin = {txt:'BOSS FIGHT', col:'#ff5533'};
    else if(!queueHolds() && liveThreatCount()>0) pin = {txt:'CLEAR THE FIELD', col:'#ff5533'};
  }
  // While the card is announcing this very objective, the line waits.
  const cardAge = objCard ? fc - objCard.t0 : 1e9;
  const cardUp = objCard && cardAge < OBJ_CARD_TIME - OBJ_CARD_FADE;
  const lineUp = pin && arriveT<=0 && !(cardUp && objCard.tone==='new' && objCard.txt===pin.txt);
  if(lineUp) drawObjLine(pin);
  drawNotices(HUD_H + 6 + (lineUp ? 26 : 0));
  drawObjCard();
}
// ── NOTICES ──────────────────────────────────────────────────
// What concerns the whole fight rather than one ship: a hull or weapon
// becoming available, a radio line from the mission, a refit. A small
// column under the objective line, never in the middle of the field.
// Newest on top, at most NOTICE_MAX, each for NOTICE_TIME steps. Steps
// of the game, so a pause holds them.
const NOTICE_TIME = 320, NOTICE_FADE = 40, NOTICE_IN = 10, NOTICE_MAX = 3;
const NOTICE_TONE = {unlock:null, info:'#7fd6ff', good:'#4dff88', bad:'#ff5533'};
let NOTICES = [];
function notice(txt, tone){
  NOTICES.unshift({txt:String(txt), tone:tone||'info', t0:fc});
  if(NOTICES.length > NOTICE_MAX) NOTICES.length = NOTICE_MAX;
}
function drawNotices(y0){
  for(let i=NOTICES.length-1;i>=0;i--) if(fc-NOTICES[i].t0 >= NOTICE_TIME) NOTICES.splice(i,1);
  let y = y0;
  for(const n of NOTICES){
    const age = fc - n.t0;
    let a = 1;
    if(age < NOTICE_IN) a = age/NOTICE_IN;
    else if(age > NOTICE_TIME-NOTICE_FADE) a = (NOTICE_TIME-age)/NOTICE_FADE;
    ctx.save();
    ctx.globalAlpha = Math.max(0, a);
    ctx.font = thValue(11, true);
    const txt = thFit(n.txt, 360);
    const pw = Math.round(ctx.measureText(txt).width + 24), ph = 18;
    thPlate(8, y, pw, ph, thRGBA('panelBack', 0.62), 4);
    // The mark on the left says what kind of news it is.
    ctx.fillStyle = NOTICE_TONE[n.tone] || TH('accentWarm');
    ctx.fillRect(13, y+4, 2, ph-8);
    ctx.fillStyle = TH('text'); ctx.textAlign='left'; ctx.textBaseline='middle';
    ctx.fillText(txt, 20, y+ph/2+1);
    ctx.restore();
    y += ph + 4;
  }
  ctx.textAlign='left'; ctx.textBaseline='top';
}
// The line under the bar: a plate from the kit, a small wedge in the
// objective's colour, the words.
function drawObjLine(pin){
  ctx.save();
  ctx.font = thValue(12, true);
  const txt = thFit(pin.txt, 380);
  const tw = ctx.measureText(txt).width;
  const px = 8, py = HUD_H+6, pw = Math.round(tw+32), ph = 20;
  thPlate(px, py, pw, ph, thRGBA('panelBack', 0.66), 5);
  ctx.fillStyle = pin.col;
  ctx.beginPath(); ctx.moveTo(px+10, py+6); ctx.lineTo(px+16, py+10); ctx.lineTo(px+10, py+14);
  ctx.closePath(); ctx.fill();
  ctx.fillStyle = TH('textBright'); ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  ctx.fillText(txt, px+23, py+ph/2+1);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}
// The card: comes down a few points as it fades in, stands, fades out.
// Below any jump-out countdowns, so the two never overlap.
function drawObjCard(){
  if(!objCard) return;
  const age = fc - objCard.t0;
  if(age >= OBJ_CARD_TIME){ objCard = null; return; }
  let a = 1;
  if(age < OBJ_CARD_FADE) a = age/OBJ_CARD_FADE;
  else if(age > OBJ_CARD_TIME-OBJ_CARD_FADE) a = (OBJ_CARD_TIME-age)/OBJ_CARD_FADE;
  if(arriveT>0) return;
  const col = objCard.tone==='new' ? TH('accentWarm') : OBJ_TONE[objCard.tone];
  ctx.save();
  ctx.font = thValue(16, true);
  const maxW = W-160;
  const txt = thFit(objCard.txt, maxW-40);
  const cw = Math.round(Math.max(280, Math.min(maxW, ctx.measureText(txt).width+56)));
  const ch = 54;
  const rows = Math.min(FLEE_ROWS, fleeingEnemies().length + (missionTimerLeft()>=0 ? 1 : 0));
  const cx = ((W-cw)/2)|0;
  const cy = (HUD_H + 12 + rows*26 - (1-a)*10)|0;
  ctx.globalAlpha = a;
  thPlate(cx, cy, cw, ch, thRGBA('panelBack', 0.80), 8);
  thGlowPath(cx, cy, cw, ch, 8, 0.8);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillStyle = col; ctx.font = thLabel(10);
  ctx.fillText(objCard.head, W/2, cy+15);
  // A short rule in the card's colour under the heading.
  ctx.fillRect(W/2-22, cy+23, 44, 2);
  ctx.fillStyle = TH('textBright'); ctx.font = thValue(16, true);
  ctx.fillText(txt, W/2, cy+38);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}

// Stacked, most urgent at the top. Three at once is already more capital
// ships than any wave fields, so the list is capped there.
// Right aligned under the bar: the objective line and the notices own
// the left side, and a long objective reached into a centred plate.
const FLEE_ROWS = 3;
function drawFleeWarning(){
  if(GS!=='playing') return;
  const list=fleeingEnemies();
  const tmr=missionTimerLeft();
  if(!list.length && tmr<0) return;
  ctx.save();
  ctx.font=thValue(12, true);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  let row=0;
  // The mission's own clock (v169) sits on top, in the cool colour of our
  // side; the enemy jump-outs follow below it.
  if(tmr>=0){
    const sec=Math.ceil(tmr/TICK_HZ);
    const txt=missionTimer.label+'  '+Math.floor(sec/60)+':'+String(sec%60).padStart(2,'0');
    const tw=ctx.measureText(txt).width;
    const bw=(tw+28)|0, bx=(W-8-bw)|0, by=HUD_H+6;
    thPlate(bx, by, bw, 20, thRGBA('panelBack', 0.72), 5);
    ctx.fillStyle=(sec<=10 && fc%40>=28) ? '#ffffff' : '#7fd6ff';
    ctx.fillText(txt, bx+bw/2, by+11);
    row++;
  }
  for(const flr of list){
    if(row>=FLEE_ROWS) break;
    const sec=Math.ceil(flr.fleeT/TICK_HZ);
    const urgent=sec<=10;
    const by=HUD_H+6+row*23;
    row++;
    if(row>FLEE_ROWS) break;
    if(urgent && fc%40>=28) continue;      // blink once it gets tight
    const txt=(flr.label ? flr.label.toUpperCase() : shipName(flr.img, flr.type||'capital ship'))+
              (flr.disarmed?' WITHDRAWING IN ':' JUMPING OUT IN ')+sec+'s';
    const tw=ctx.measureText(txt).width;
    const bw=(tw+28)|0, bx=(W-8-bw)|0;
    thPlate(bx, by, bw, 20, thRGBA('panelBack', 0.72), 5);
    ctx.fillStyle=urgent?'#ff7733':'#ffcc44';
    ctx.fillText(txt, bx+bw/2, by+11);
  }
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}

// A gear, drawn rather than an image, so it needs no asset and scales.
// A speaker, with waves while the sound is on and a cross when it is off.
function drawMuteButton(x, y, w, h, key){
  const hv = hovering(x, y, w, h);
  const st = btnState(true, false, hv);
  thButton(x, y, w, h, st);
  // Muted is a setting, not a locked button: the icon says it (crossed out).
  const col = btnText(st);
  // With its key (the bar, v186) the icon moves up and the letter sits at
  // the foot, like on every other button there.
  const cx = x + w/2 - 3, cy = key ? y + (h-11)/2 + 5.5 : y + h/2, s = Math.min(w, key ? 22 : h)/22;
  if(key){
    ctx.save(); ctx.textAlign='center'; ctx.textBaseline='alphabetic';
    ctx.font=thLabel(8); ctx.fillStyle=col; ctx.fillText(key, x+w/2, y+h-4); ctx.restore();
  }
  ctx.save();
  ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineWidth = 1.4; ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(cx-6*s, cy-2.5*s); ctx.lineTo(cx-3*s, cy-2.5*s); ctx.lineTo(cx+1*s, cy-6*s);
  ctx.lineTo(cx+1*s, cy+6*s); ctx.lineTo(cx-3*s, cy+2.5*s); ctx.lineTo(cx-6*s, cy+2.5*s);
  ctx.closePath(); ctx.fill();
  if(SND.on){
    ctx.beginPath(); ctx.arc(cx+2*s, cy, 4*s, -0.8, 0.8); ctx.stroke();
    ctx.beginPath(); ctx.arc(cx+2*s, cy, 7*s, -0.8, 0.8); ctx.stroke();
  } else {
    ctx.beginPath(); ctx.moveTo(cx+4*s, cy-3.5*s); ctx.lineTo(cx+10*s, cy+3.5*s);
    ctx.moveTo(cx+10*s, cy-3.5*s); ctx.lineTo(cx+4*s, cy+3.5*s); ctx.stroke();
  }
  ctx.restore();
  window._muteRect = {x:x, y:y, w:w, h:h, gs:GS};
}
// A tap on it switches the sound and does nothing else (no shot, no start).
function muteHit(p){
  const r = window._muteRect;
  if(!r || r.gs !== GS || (GS!=='title' && GS!=='playing')) return false;
  if(GS==='playing' && (settingsOpen || callMenu || shipMenu)) return false;
  return p.x>=r.x && p.x<=r.x+r.w && p.y>=r.y && p.y<=r.y+r.h;
}
function drawGear(cx, cy, r, col){
  ctx.save();
  ctx.translate(cx, cy);
  ctx.strokeStyle=col; ctx.fillStyle=col; ctx.lineWidth=1.6;
  for(let i=0;i<6;i++){
    const a=i*Math.PI/3;
    ctx.beginPath();
    ctx.moveTo(Math.cos(a)*r*0.62, Math.sin(a)*r*0.62);
    ctx.lineTo(Math.cos(a)*r*1.25, Math.sin(a)*r*1.25);
    ctx.stroke();
  }
  ctx.beginPath(); ctx.arc(0,0,r*0.68,0,Math.PI*2); ctx.stroke();
  ctx.restore();
}

// ── SETTINGS PANEL ─────────────────────────────────────────
// Only one entry today. It exists as a panel because the alternative is
// to hang each new option off its own button in a bar that is already
// full.
let settingsOpen=false;
let settingsPage=0;          // 0 = Spiel, 1 = Sparmodus
// Wird vom Packer aus dem Dateinamen der Logikdatei gesetzt, damit die
// Nummer nicht von Hand gepflegt werden muss und nicht driften kann.
const GAME_VERSION='dev';
let showFps=false;
let fpsVal=0, fpsFrames=0, fpsLast=0;
function tickFps(){
  fpsFrames++;
  const now = (typeof performance!=='undefined' && performance.now) ? performance.now() : Date.now();
  if(!fpsLast){ fpsLast=now; return; }
  if(now-fpsLast >= 500){
    fpsVal = Math.round(fpsFrames*1000/(now-fpsLast));
    fpsFrames=0; fpsLast=now;
  }
}
// Oben rechts unter der Leiste, wo nichts anderes liegt. Courier ist eine
// Festbreitenschrift, ein Zeichen ist 0.6 mal die Schriftgroesse breit -
// bei 11 px also 6.6 px. 'FPS 120' sind sieben Zeichen und damit 46.2 px,
// der Kasten ist 54 breit.
// A small plate from the kit, right aligned under the bar.
function drawReadout(txt, row, col){
  ctx.save();
  ctx.font = thValue(11, true);
  const tw = ctx.measureText(txt).width;
  const pw = Math.round(tw+16), ph = 16;
  // Below the jump-out countdowns, which share the right edge.
  const fr = (GS==='playing') ? Math.min(FLEE_ROWS, fleeingEnemies().length) : 0;
  const px = W-6-pw, py = HUD_H+6+fr*23+row*20;
  thPlate(px, py, pw, ph, thRGBA('panelBack', 0.66), 4);
  ctx.fillStyle = col; ctx.textAlign='left'; ctx.textBaseline='middle';
  ctx.fillText(txt, px+8, py+ph/2+1);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}
function drawFps(){
  if(!showFps) return;
  drawReadout('FPS '+(fpsVal||'--'), 0, fpsVal && fpsVal<40 ? '#ff9900' : TH('textBright'));
}
// Object counter. Three numbers instead of a sum: a sum says that it
// grows, three say which list grows.
let showObj=false;
function drawObjCount(){
  if(!showObj) return;
  const ships = enemies.length + allies.length;
  const shots = pBullets.length + eBullets.length;
  const junk  = debris.length + PARTS.length + ITEMS.length;
  drawReadout('OBJ '+ships+'/'+shots+'/'+junk, showFps ? 1 : 0, TH('text'));
}

// No need to remember the previous pause any more: closing the panel
// simply drops this panel's own reason to pause, and syncPause() works
// out whether anything else still wants the game held.
function setSettings(v){
  v=!!v;
  settingsOpen=v;
  syncPause();
  if(!v){ settingsPage=0; plogOpen=false; }   // beim naechsten Oeffnen wieder Seite 1
  window._setRects=[];
}

// Eine Zeile des Fensters. Alle Zeilen sehen gleich aus, damit eine neue
// Option nichts weiter braucht als einen Eintrag in der Liste unten.
function setRow(bx, by, bw, bh, label, hint, value, on, act, enabled){
  uiCell(bx, by, bw, bh, {state: enabled ? (on?'ready':null) : 'off',
                          fill: enabled?'#00160c':'#0a0a0a',
                          stroke: enabled?'#4499ff':'#333'});
  ctx.textAlign='left';
  ctx.fillStyle = enabled ? UI('textBright','#7fc4ff') : UI('textDim','#555');
  ctx.font = uiValue(13, true, 'bold 12px Courier New');
  ctx.fillText(label, bx+12, by+7);
  ctx.fillStyle = enabled ? UI('textDim','#007733') : UI('edgeLight','#3a3a3a');
  ctx.font = uiValue(10, false, '9px Courier New');
  ctx.fillText(hint, bx+12, by+24);
  ctx.textAlign='right';
  ctx.fillStyle = on ? UI('accent','#00ee55') : UI('textDim','#666');
  ctx.font = uiValue(13, true, 'bold 12px Courier New');
  ctx.fillText(value, bx+bw-12, by+14);
  if(enabled) window._setRects.push({x:bx,y:by,w:bw,h:bh,act:act});
}

// Zwei Seiten zu vier Zeilen. Acht Zeilen am Stueck waeren 460 von 500
// Bildpunkten Hoehe gewesen.
const SETTINGS_PAGES = 5;
const SETTINGS_TITLES = ['SETTINGS', 'ECONOMY', 'APPEARANCE', 'SOUND', 'CONTROLS'];
const SETTINGS_TABS = ['GENERAL', 'ECONOMY', 'APPEARANCE', 'SOUND', 'CONTROLS'];
const SETTINGS_CONTROLS = 4;   // the page that shows CONTROLS instead of rows

// ── CONTROLS ─────────────────────────────────────────────────
// Every input the game reads, in one list (v185). The title screen and the
// CONTROLS tab of the settings both draw from it, so a new key is added
// here once and shows up in both places.
const CONTROLS = [
  ['MOUSE',              'fly and aim'],
  ['LEFT BUTTON, SPACE', 'fire primary'],
  ['RIGHT BUTTON',       'fire secondary'],
  ['WHEEL UP, Q',        'primary: bank 1, 2, linked'],
  ['WHEEL DOWN, E',      'next secondary bank'],
  ['MIDDLE BUTTON',      'subsystems on / off'],
  ['V',                  'change ship (V again closes)'],
  ['R',                  'rearm (R again closes)'],
  ['C',                  'call support (C again closes)'],
  ['1 - 6, Q - T, G',    'choose in a menu'],
  ['TAB, ARROWS',        'fleet tab in a menu'],
  ['S',                  'settings'],
  ['P, ESC',             'pause'],
  ['M',                  'sound on / off'],
  ['F',                  'full screen']
];
// The list as rows: key on the left in the accent, what it does beside it.
function drawControlsList(x, y, w, rowH, keyW){
  for(let i=0;i<CONTROLS.length;i++){
    const ry = y + i*rowH;
    ctx.textAlign='left'; ctx.textBaseline='middle';
    ctx.fillStyle = TH('accentWarm'); ctx.font = thLabel(10);
    ctx.fillText(thFit(CONTROLS[i][0], keyW-6), x, ry+rowH/2);
    ctx.fillStyle = TH('text'); ctx.font = thValue(11, false);
    ctx.fillText(thFit(CONTROLS[i][1], w-keyW), x+keyW, ry+rowH/2);
  }
}
const SETTINGS_ROWS_MAX = 5;   // the panel keeps one height for every tab
function settingsRows(){
  if(settingsPage===SETTINGS_CONTROLS) return [];
  if(settingsPage===3) return [
    {label:'SOUND', hint:'all sound on or off - also M or the speaker',
     value:SND.on?'ON':'OFF', on:SND.on, act:'sndon', enabled:true},
    {label:'EFFECTS VOLUME', hint:'tap to step through 100 / 75 / 60 / 50 / 25 %',
     value:Math.round(SND.vol*100)+' %', on:SND.on, act:'sndvol', enabled:true},
    {label:'MUSIC VOLUME', hint:'tap to step through 100 / 75 / 50 / 25 % / off',
     value:SND.mus>0 ? Math.round(SND.mus*100)+' %' : 'OFF', on:SND.on && SND.mus>0, act:'musvol', enabled:true}
  ];
  if(settingsPage===2) return [
    {label:'COLOUR SCHEME', hint:'the two schemes of the forum theme',
     value:ECO.scheme==='void'?'VOID':'FIRE', on:true,
     act:'scheme', enabled:true}
  ];
  if(settingsPage===1) return [
    {label:'RESOLUTION', hint:'canvas scale, lower is cooler but softer',
     value:ECO.res+'x', on:ECO.res!==3, act:'res', enabled:true},
    {label:'BEAM GLOW', hint:'blur around beams, priciest canvas op',
     value:ECO.blur?'OFF':'ON', on:!ECO.blur, act:'blur', enabled:true},
    {label:'RIM LIGHT', hint:'light edge on cruisers and larger',
     value:ECO.rim?'OFF':'ON', on:!ECO.rim, act:'rim', enabled:true},
    {label:'METAL GLINT', hint:'baked highlight map per hull',
     value:ECO.glint?'OFF':'ON', on:!ECO.glint, act:'glint', enabled:true}
  ];
  const avail = fullscreenAvailable();
  return [
    {label:'FULLSCREEN',
     hint:avail?'removes the browser bars and the black edges'
               :'not supported by this browser',
     value:isFullscreen()?'ON':'OFF', on:isFullscreen(),
     act:'fullscreen', enabled:avail},
    {label:'PRACTICE MODE',
     hint:'no lives are lost, 10 tickets of each kind every wave',
     value:practiceMode?'ON':'OFF', on:practiceMode,
     act:'practice', enabled:true},
    {label:'PRACTICE LOG', hint:'every wave of this run - copy it for balancing',
     value:'OPEN', on:false, act:'plog', enabled:true},
    {label:'FRAME RATE', hint:'shows the frame rate below the top bar',
     value:showFps?'ON':'OFF', on:showFps, act:'fps', enabled:true},
    {label:'OBJECT COUNT', hint:'ships / shots / debris, below the rate',
     value:showObj?'ON':'OFF', on:showObj, act:'obj', enabled:true}
  ];
}

function drawSettings(){
  if(!settingsOpen) return;
  if(plogOpen){ drawPlog(); return; }
  window._setRects=[];
  // 380 wide since v185: five tabs (CONTROLS added) need the room.
  const bw=380, bh=40, gap=8;
  // The height follows the page, so a shorter page leaves no hole.
  const rows=Math.max(1, settingsRows().length);
  const hintH=22;   // room for the closing hint, which used to land inside
                    // the option box because it was not accounted for
  const verH=16;    // eigene Zeile fuer die Versionsnummer, aus demselben
                    // Grund getrennt gerechnet statt in den Hinweis gequetscht
  const tabH=22;    // the row of tabs under the title
  const rowsH=Math.max(rows, SETTINGS_ROWS_MAX);
  const mw=bw+gap*2, mh=bh*rowsH+gap*(rowsH+1)+30+tabH+hintH+verH;
  const mx=(W-mw)/2, my=(H-mh)/2;
  uiDialog(mx, my, mw, mh, 'rgba(0,14,6,0.96)', '#00aa44');
  ctx.fillStyle=UI('textBright','#00ee55');
  ctx.font=uiLabel(13, 'bold 13px Courier New');
  ctx.textAlign='center'; ctx.textBaseline='top';
  ctx.fillText('SETTINGS', mx+mw/2, my+9);

  const bx=mx+gap;
  // Tabs: one per page, the open one lit. Each as wide as its name
  // needs, sharing out what is left, so APPEARANCE is not cut short.
  ctx.font = thLabel(10);
  const tws=SETTINGS_TABS.map(n => ctx.measureText(n).width + 8);
  const tsum=tws.reduce((a,b)=>a+b, 0), tfree=bw-(SETTINGS_TABS.length-1)*4;
  let tx=bx;
  for(let t=0;t<SETTINGS_TABS.length;t++){
    const tw=tws[t]*tfree/tsum, ty=my+28;
    const on=(t===settingsPage), hv=hovering(tx, ty, tw, tabH);
    uiCell(tx, ty, tw, tabH, {state:on?'on':(hv?'ready':null)});
    ctx.fillStyle = on ? TH('accentWarm') : (hv ? TH('textBright') : TH('text'));
    ctx.font = thLabel(10); ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(thFit(SETTINGS_TABS[t], tw-6), tx+tw/2, ty+tabH/2+1);
    window._setRects.push({x:tx, y:ty, w:tw, h:tabH, act:'tab'+t});
    tx+=tw+4;
  }
  ctx.textAlign='center'; ctx.textBaseline='top';
  if(settingsPage===SETTINGS_CONTROLS){
    // The list in the room the rows would take.
    const top=my+30+tabH+gap, room=bh*rowsH+gap*(rowsH-1);
    drawControlsList(bx+10, top, bw-20, Math.min(19, room/CONTROLS.length), 132);
  }
  const list=settingsRows();
  for(let i=0;i<list.length;i++){
    const r=list[i];
    setRow(bx, my+30+tabH+gap+i*(bh+gap), bw, bh,
           r.label, r.hint, r.value, r.on, r.act, r.enabled);
  }

  ctx.textAlign='center'; ctx.textBaseline='top';
  ctx.fillStyle=UI('edgeLight','#005522'); ctx.font=uiValue(10, false, '9px Courier New');
  ctx.fillText('FS3  '+GAME_VERSION, mx+mw/2, my+mh-hintH-verH+4);
  ctx.fillStyle=UI('textDim','#007733'); ctx.font=uiValue(10, false, '9px Courier New');
  ctx.fillText('tap outside or press S to close', mx+mw/2, my+mh-hintH+6);
  ctx.textAlign='left'; ctx.textBaseline='top';
}

// Returns true when the tap was consumed by the panel.
function settingsClick(mx,my){
  if(!settingsOpen) return false;
  if(plogOpen) return plogClick(mx, my);
  const rs=window._setRects||[];
  for(const r of rs){
    if(mx>=r.x&&mx<=r.x+r.w&&my>=r.y&&my<=r.y+r.h){
      if(r.act==='fullscreen') toggleFullscreen();
      else if(r.act==='fps'){ showFps=!showFps; fpsFrames=0; fpsLast=0; }
      else if(r.act==='obj'){ showObj=!showObj; }
      else if(r.act==='practice'){ practiceMode=!practiceMode; practiceTickets(); }
      else if(r.act==='plog'){ plogOpen=true; plogSel=-1; plogTop=Math.max(0, plogRows().length-PLOG_ROWS); }
      else if(r.act==='pagenext'){ settingsPage=(settingsPage+1)%SETTINGS_PAGES; }
      else if(r.act==='pageprev'){ settingsPage=(settingsPage+SETTINGS_PAGES-1)%SETTINGS_PAGES; }
      else if(r.act==='scheme'){ ECO.scheme=(ECO.scheme==='void')?'fire':'void'; ecoSave(); }
      else if(r.act==='res'){
        const _i=ECO_RES_STEPS.indexOf(ECO.res);
        ecoSetRes(ECO_RES_STEPS[(_i+1)%ECO_RES_STEPS.length]);
      }
      else if(r.act==='blur'){ ECO.blur=!ECO.blur; ecoSave(); }
      else if(r.act==='sndon'){ sndToggleMute(); }
      else if(r.act==='sndvol'){ SND.vol=sndStep(SND_VOL_STEPS, SND.vol); sndApplyVolume(); sndSave(); }
      else if(r.act==='musvol'){ SND.mus=sndStep(MUS_VOL_STEPS, SND.mus); sndApplyVolume(); sndSave(); }
      else if(r.act.indexOf('tab')===0){ settingsPage=+r.act.slice(3); }
      else if(r.act==='rim'){ ECO.rim=!ECO.rim; ecoSave(); }
      else if(r.act==='glint'){ ECO.glint=!ECO.glint; ecoSave(); }
      return true;
    }
  }
  setSettings(false);
  return true;
}

// Symbole statt Text in der Leiste, gezeichnet wie drawGear() und in
// derselben Palette. Keine Emojis: die kaemen in der Systemschrift und
// wuerden neben Courier und den Schiffssymbolen sofort auffallen.
function drawPauseIcon(cx, cy, col, running){
  ctx.fillStyle=col;
  if(running){                      // laeuft -> zwei Balken zum Anhalten
    ctx.fillRect((cx-5)|0,(cy-7)|0,4,14);
    ctx.fillRect((cx+1)|0,(cy-7)|0,4,14);
  } else {                          // steht -> Dreieck zum Weitermachen
    ctx.beginPath();
    ctx.moveTo(cx-4,cy-7); ctx.lineTo(cx+7,cy); ctx.lineTo(cx-4,cy+7);
    ctx.closePath(); ctx.fill();
  }
}

// Schlank, mit Spitze und drei Finnen.
function drawMissileIcon(cx, cy, col){
  ctx.save(); ctx.translate(cx,cy); ctx.fillStyle=col;
  ctx.beginPath();
  ctx.moveTo(9,0); ctx.lineTo(3,-3); ctx.lineTo(-7,-3);
  ctx.lineTo(-7,3); ctx.lineTo(3,3);
  ctx.closePath(); ctx.fill();
  ctx.beginPath();
  ctx.moveTo(-3,-3); ctx.lineTo(-6,-7); ctx.lineTo(-9,-7); ctx.lineTo(-7,-3);
  ctx.closePath(); ctx.fill();
  ctx.beginPath();
  ctx.moveTo(-3,3); ctx.lineTo(-6,7); ctx.lineTo(-9,7); ctx.lineTo(-7,3);
  ctx.closePath(); ctx.fill();
  ctx.restore();
}

// Gedrungen, stumpfe Nase, breites Leitwerk. Auf 34 px Breite muss der
// Unterschied zur Rakete auf einen Blick sitzen, deshalb der dicke Bauch.
function drawBombIcon(cx, cy, col){
  ctx.save(); ctx.translate(cx,cy); ctx.fillStyle=col;
  ctx.beginPath();
  ctx.ellipse(1,0,7.5,5,0,0,Math.PI*2);
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(-4,-5); ctx.lineTo(-10,-8); ctx.lineTo(-10,8); ctx.lineTo(-4,5);
  ctx.closePath(); ctx.fill();
  ctx.restore();
}

// ── BAR PULSE ────────────────────────────────────────────────
// Something in the bar calls attention to itself: soft pulses of the
// kit's glow ring, n of them over t steps. weak: the same, dimmed - a
// pickup that changed nothing. Keys: 'hull', 'lives', 'swap', 'rearm',
// 'ticket:<kind>'. Game steps, so a pause holds them.
const BAR_PULSE_T = 150, BAR_PULSE_N = 3;      // pickups
const BAR_CALL_T  = 240, BAR_CALL_N  = 4;      // a button that can now be used
const BAR_WEAK    = 0.4;
let BAR_PULSE = {};
function barPulse(key, weak, t, n){
  BAR_PULSE[key] = {t0:fc, weak:!!weak, t:t||BAR_PULSE_T, n:n||BAR_PULSE_N};
}
function barPulseLevel(key){
  const p = BAR_PULSE[key];
  if(!p) return 0;
  const age = fc - p.t0;
  if(age >= p.t){ delete BAR_PULSE[key]; return 0; }
  const v = 0.5 - 0.5*Math.cos(age/p.t*Math.PI*2*p.n);
  return v * (p.weak ? BAR_WEAK : 1);
}
// A button becoming usable is news once, when it happens - not every
// step it stays usable.
let barSwapWas = false, barRearmWas = false;
function tickBarAttention(){
  if(GS!=='playing' || FS1_MODE){ barSwapWas = false; barRearmWas = false; return; }
  const s = shipSwapReady(), r = rearmReady();
  if(s && !barSwapWas)  barPulse('swap',  false, BAR_CALL_T, BAR_CALL_N);
  if(r && !barRearmWas) barPulse('rearm', false, BAR_CALL_T, BAR_CALL_N);
  barSwapWas = s; barRearmWas = r;
}
function drawHUD(){
  if(GS!=='playing') return;
  drawHUDHLP();
}

// THE HLP BAR
// Same geometry as the old bar down to the pixel, so every pointer rectangle
// and everything that reads them keeps working. What changed is the surface:
// one palette, a bevel at rest, a glow ring for emphasis, and colour kept
// for meaning - green and amber for the hull, blue for the shield, the
// accent for anything that can be pressed.
function drawHUDHLP(){
  // The bar since v186 (variant A, Silvio): 54 high as before, everything
  // the player needs in one line - score, the three stores, lives, the
  // banks, support, tickets and the five buttons. Nothing on the field.
  var H2=HUD_H, mid=(H2/2)|0;

  thPanel(0, 0, W, H2, TH('barTop'), TH('panelBack'));
  ctx.fillStyle=TH('panelBack'); ctx.fillRect(0, H-8, W, 8);
  ctx.strokeStyle=TH('edgeLight'); ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(0, H2-0.5); ctx.lineTo(W, H2-0.5); ctx.stroke();
  ctx.textBaseline='middle'; ctx.textAlign='left';
  function lab(t, x, y){ ctx.fillStyle=TH('textDim'); ctx.font=thLabel(7); ctx.fillText(t, x, y); }

  // 1  SCORE, WAVE, TIME - one narrow column
  lab('SCORE', 6, 9);
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(13, true);
  ctx.fillText(String(score).padStart(7,'0'), 6, 21);
  lab('WAVE', 6, H2-20);
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(11, true);
  ctx.fillText(String(wave).padStart(3,'0'), 34, H2-20);
  lab('TIME', 6, H2-8);
  ctx.fillStyle=callMenu?TH('textDim'):TH('text'); ctx.font=thValue(10, false);
  ctx.fillText(fmtTime(runTime), 34, H2-8);
  var x=72; thDivider(x, 4, H2-4); x+=6;

  // 2  HULL, SHIELD, ENERGY - three bars, the share at the end
  var bw=74, bh=Math.max(5, (H2-16)/3-6), gap=(H2-8)/3, bx=x+34;
  var hR=Math.max(0, player.hp/player.maxHp);
  var sR=player.maxSh ? Math.max(0, player.sh/player.maxSh) : 0;
  var eR=player.enMax ? Math.max(0, player.en/player.enMax) : 0;
  var rows=[['HULL', hR], ['SHIELD', sR], ['ENERGY', eR]];
  for(var i=0;i<3;i++){
    var y=5+i*gap;
    lab(rows[i][0], x, y+3);
    ctx.fillStyle=TH('edgeDark'); ctx.fillRect(bx, y, bw, bh);
    if(i===0){
      ctx.globalAlpha=(hR<=HULL_CRIT)?(0.55+0.45*Math.sin(fc*0.22)):1;
      ctx.fillStyle=hullCol(hR);
    } else if(i===1) ctx.fillStyle=sR>.5?'#0099ff':'#0055cc';
    else ctx.fillStyle=(player.enEmptyT>0 && fc%8<4) ? '#ff5a44' : '#ffc23a';
    ctx.fillRect(bx, y, (bw*rows[i][1])|0, bh);
    ctx.globalAlpha=1;
    thBevel(bx, y, bw, bh);
    if(i===0){
      var hPl=barPulseLevel('hull');
      if(hPl>0){ ctx.fillStyle='rgba(77,255,136,'+(0.35*hPl).toFixed(3)+')'; ctx.fillRect(bx, y, bw, bh);
                 thGlowPath(bx-3, y-3, bw+6, bh+6, 3, hPl); }
    }
    if(i===1 && player.shDelay===0 && player.sh<player.maxSh && fc%30<15){
      ctx.fillStyle='rgba(0,100,200,0.2)'; ctx.fillRect(bx, y, bw, bh);
    }
    ctx.fillStyle=TH('text'); ctx.font=thValue(8, false); ctx.textAlign='right';
    ctx.fillText(Math.round(rows[i][1]*100)+'%', bx+bw+23, y+bh/2+0.5); ctx.textAlign='left';
  }
  if(player.enEmptyT>0) player.enEmptyT--;
  x=bx+bw+27; thDivider(x, 4, H2-4); x+=6;

  // 3  LIVES - the hull icon back in front of the count (Silvio, v187)
  lab('LIVES', x, 9);
  var lIco=ICONS[isBomberHull(player.ship)?'bomberlives':'fighterlives'], lW=13;
  if(lIco){
    var lh=12; lW=Math.max(1, Math.round(lIco.width*(lh/lIco.height)));
    if(lW>18){ lh=lh*18/lW; lW=18; }
    ctx.drawImage(lIco, x|0, (mid+6-lh/2)|0, lW, lh);
  } else {
    ctx.fillStyle=TH('text'); var ly=mid+3;
    ctx.fillRect(x, ly+2, 11, 3); ctx.fillRect(x+2, ly, 7, 2);
    ctx.fillRect(x+2, ly+5, 7, 2); ctx.fillRect(x+9, ly+2, 4, 3);
  }
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(14, true);
  ctx.fillText(String(lives), x+lW+4, mid+6);
  var lPl=barPulseLevel('lives');
  if(lPl>0) thGlowPath(x-4, 5, 44, H2-10, 4, lPl);
  x+=40; thDivider(x, 4, H2-4); x+=6;

  // 4  PRIMARY: one row per bank, the firing ones lit, linked ones joined
  // by a bracket. A tap on the panel steps the mode, like the wheel.
  var pb=player.pb||[], fire=firingBanks(), prow=(H2-14)/Math.max(2, pb.length);
  var px0=x;
  lab('PRIMARY', x, 7);
  var nM=primaryCount(player.ship);
  for(var pi=0;pi<pb.length;pi++){
    var py=14+pi*prow+prow/2, on=fire.indexOf(pb[pi])>=0;
    var pw=priDefP(pb[pi].key), poor=player.en<pw.en;
    ctx.fillStyle=on?TH('accent'):TH('textDim'); ctx.font=thLabel(7);
    ctx.fillText(String(pi+1), x, py);
    ctx.fillStyle=on?(poor?'#ff5a44':TH('textBright')):TH('textDim'); ctx.font=thValue(9, on);
    ctx.fillText(thFit(weaponName(pw).toUpperCase(), 90), x+9, py);
    var g=(pb.length>=2 && nM>=2) ? Math.ceil((nM-pi)/2) : Math.max(1, nM);
    ctx.fillStyle=TH('textDim'); ctx.font=thValue(8, false); ctx.textAlign='right';
    ctx.fillText(g+'×', x+112, py); ctx.textAlign='left';
  }
  if(fire.length>1){
    ctx.strokeStyle=TH('accent'); ctx.lineWidth=1.2;
    var y0=14+prow*0.5-4, y1=14+prow*(pb.length-0.5)+4;
    ctx.beginPath(); ctx.moveTo(x+117,y0); ctx.lineTo(x+120,y0); ctx.lineTo(x+120,y1); ctx.lineTo(x+117,y1); ctx.stroke();
    ctx.fillStyle=TH('accent'); ctx.font=thLabel(6);
    ctx.save(); ctx.translate(x+126,(y0+y1)/2); ctx.rotate(-Math.PI/2); ctx.textAlign='center'; ctx.fillText('LINK',0,0); ctx.restore();
  }
  window._priRect=(pb.length>=2)?{x:px0-3, y:3, w:132, h:H2-6}:null;
  if(window._priRect && hovering(px0-3, 3, 132, H2-6)) thGlowPath(px0-3, 3, 130, H2-6, 4, 0.35);
  x+=132; thDivider(x, 4, H2-4); x+=6;

  // 5  SECONDARY: one row per bank with its own rack, the chosen one lit.
  // A tap on another row chooses it, on the chosen one it fires (touch).
  var sb=player.sb||[], srow=(H2-14)/Math.max(3, sb.length);
  lab('SECONDARY', x, 7);
  window._secRows=[]; window._secBtnRect=null;
  for(var si=0;si<sb.length;si++){
    var sy=14+si*srow+srow/2, son=(si===player.sSel), sw=secDefP(sb[si].key);
    var rr={x:x-2, y:sy-srow/2+1, w:118, h:srow-2, i:si};
    if(son){
      // The theme's own glow, not a fixed orange (it read red on Void).
      ctx.fillStyle='rgba('+TH('glow')+',0.30)'; ctx.fillRect(rr.x, rr.y, rr.w, rr.h);
      if(player.secTimer>0 && player.secCdMax){
        ctx.fillStyle=TH('accent');
        ctx.fillRect(rr.x, rr.y+rr.h-2, (rr.w*(1-player.secTimer/player.secCdMax))|0, 2);
      }
      window._secBtnRect=rr;
    } else if(hovering(rr.x, rr.y, rr.w, rr.h)){ ctx.fillStyle='rgba(255,255,255,0.05)'; ctx.fillRect(rr.x, rr.y, rr.w, rr.h); }
    ctx.fillStyle=son?TH('accent'):TH('textDim'); ctx.font=thLabel(7); ctx.fillText(String(si+1), x, sy);
    ctx.fillStyle=son?TH('textBright'):(sb[si].ammo?TH('text'):TH('textDim')); ctx.font=thValue(9, son);
    ctx.fillText(thFit(weaponName(sw).toUpperCase(), 78), x+9, sy);
    ctx.fillStyle=sb[si].ammo?(son?TH('textBright'):TH('text')):'#ff5a44'; ctx.font=thValue(9, true); ctx.textAlign='right';
    ctx.fillText(String(sb[si].ammo).padStart(2,'0'), x+112, sy); ctx.textAlign='left';
    window._secRows.push(rr);
  }
  x+=120; thDivider(x, 4, H2-4); x+=5;

  // 6  SUPPORT - a narrow button
  var alX=x, alBW=54, alBH=H2-10, alBY=5;
  var alRdy=allyReady(), alCan=alRdy && anyTicket();
  thButton(alX, alBY, alBW, alBH, btnState(alCan, callMenu, hovering(alX, alBY, alBW, alBH)));
  lab('SUPPORT', alX+4, alBY+7);
  ctx.fillStyle=alCan?TH('accent'):TH('textDim'); ctx.font=thValue(9, true);
  ctx.fillText(thFit(alRdy?(anyTicket()?'READY':'NO TICKET'):(allies.length?'DEPLOYED':'STANDBY'), alBW-8), alX+4, mid+1);
  lab('[C]', alX+4, alBY+alBH-7);
  window._allyBtnRect={x:alX, y:alBY, w:alBW, h:alBH};
  x+=alBW+5;

  // 7  TICKETS, 2 x 2
  {
    var tkX=x, tkY=3, tkW=41, tkH=24;
    for(var ti=0; ti<TICKET_ORDER.length; ti++){
      var tk=TICKET_ORDER[ti], tn=tickets[tk]||0;
      var lit=tn>0;
      var tPl=barPulseLevel('ticket:'+tk);
      var col=(tPl>0.3)?TH('accentWarm'):(lit?TH('accent'):TH('textDim'));
      var tico=ICONS[TICKET_ICON[tk]];
      var tcx=tkX+(ti%2)*tkW, tcy=tkY+((ti/2)|0)*tkH;
      ctx.textAlign='left'; ctx.textBaseline='top';
      ctx.fillStyle=col; ctx.font=thValue(11, true);
      var nt=tn+'x', ntw=ctx.measureText(nt).width;
      ctx.fillText(nt, tcx, tcy+6);
      var icoX=tcx+ntw+2, tih=10, tiw=0, tiMax=tkW-(icoX-tcx)-3;
      if(tico){ tiw=Math.max(1, Math.round(tico.width*(tih/tico.height)));
                if(tiw>tiMax){ tih=Math.max(5, tih*tiMax/tiw); tiw=tiMax; } }
      else { ctx.font=thLabel(8); tiw=ctx.measureText(TICKET_ABBR[tk]).width; }
      if(tPl>0) thGlowPath(tcx-3, tcy+2, (icoX-tcx)+tiw+6, tkH-2, 3, tPl);
      if(tico){
        ctx.globalAlpha=lit?1:0.28;
        ctx.drawImage(tico, icoX, tcy+6+(11-tih)/2, tiw, tih);
        ctx.globalAlpha=1;
      } else {
        ctx.fillStyle=col; ctx.font=thLabel(8);
        ctx.fillText(TICKET_ABBR[tk], icoX, tcy+7);
      }
    }
  }
  ctx.textBaseline='middle';

  // 8  V R M S P - five buttons of one kind, each with its key at the foot
  // (Silvio, v186: the ones without a letter stood lower than the others).
  var bW=22, bG=3, bY=4, bH=H2-8, bX0=W-5*bW-4*bG-4;
  function keyHint(bx, key, c){
    ctx.save(); ctx.textAlign='center'; ctx.textBaseline='alphabetic';
    ctx.font=thLabel(8); ctx.fillStyle=c; ctx.fillText(key, bx+bW/2, bY+bH-4); ctx.restore();
  }
  var icy=bY+(bH-11)/2+5.5;    // the middle of what the letter leaves
  var hideSwap=FS1_MODE;
  // V
  var swX=bX0;
  if(!hideSwap){
    var swSt=btnState(shipSwapReady()||shipMenu, shipMenu, hovering(swX, bY, bW, bH));
    thButton(swX, bY, bW, bH, swSt);
    var swPl=barPulseLevel('swap'); if(swPl>0) thGlowPath(swX-3, bY-2, bW+6, bH+4, 5, swPl);
    var swC=btnText(swSt); drawShipsIcon(swX+bW/2, icy, swC); keyHint(swX, 'V', swC);
    window._shipBtnRect={x:swX, y:bY, w:bW, h:bH};
  } else window._shipBtnRect=null;
  // R
  var rmX=bX0+bW+bG;
  if(!hideSwap){
    var rmSt=btnState(rearmReady()||rearmMenu, rearmMenu, hovering(rmX, bY, bW, bH));
    thButton(rmX, bY, bW, bH, rmSt);
    var rmPl=barPulseLevel('rearm'); if(rmPl>0) thGlowPath(rmX-3, bY-2, bW+6, bH+4, 5, rmPl);
    var rmC=btnText(rmSt); drawMissilesIcon(rmX+bW/2, icy, rmC); keyHint(rmX, 'R', rmC);
    window._rearmBtnRect={x:rmX, y:bY, w:bW, h:bH};
  } else window._rearmBtnRect=null;
  // M
  drawMuteButton(bX0+2*(bW+bG), bY, bW, bH, 'M');
  // S
  var stbX=bX0+3*(bW+bG);
  var stbSt=btnState(true, settingsOpen, hovering(stbX, bY, bW, bH));
  thButton(stbX, bY, bW, bH, stbSt);
  var stbC=btnText(stbSt); drawGearSolid(stbX+bW/2, icy, 5.6, stbC); keyHint(stbX, 'S', stbC);
  window._settingsBtnRect={x:stbX, y:bY, w:bW, h:bH};
  // P
  var pbX=bX0+4*(bW+bG);
  var pbSt=btnState(true, paused, hovering(pbX, bY, bW, bH));
  thButton(pbX, bY, bW, bH, pbSt);
  var pbC=btnText(pbSt); drawPauseIcon(pbX+bW/2, icy, pbC, !paused); keyHint(pbX, 'P', pbC);
  window._pauseBtnRect={x:pbX, y:bY, w:bW, h:bH};

  ctx.textAlign='left'; ctx.textBaseline='top';
}
// The icons of the bar (v186, Silvio: variant 3 and gear B).
// Two fighters seen from above, the upper one filled, the lower in outline.
const ICO_SHIP = [[7,0],[2,-1.4],[-1,-5],[-3.5,-5],[-2.5,-1.6],[-6,-1.6],[-7,-3],[-8,-3],[-7.2,0],[-8,3],[-7,3],[-6,1.6],[-2.5,1.6],[-3.5,5],[-1,5],[2,1.4]];
const ICO_MISSILE = [[7.5,0],[4.5,-1.6],[-4.5,-1.6],[-7,-4],[-7.5,-4],[-6.5,-1.6],[-6.5,1.6],[-7.5,4],[-7,4],[-4.5,1.6],[4.5,1.6]];
function icoShape(P, cx, cy, s, col, fill){
  ctx.beginPath();
  for(let i=0;i<P.length;i++){ const x=cx+P[i][0]*s, y=cy+P[i][1]*s; if(i) ctx.lineTo(x,y); else ctx.moveTo(x,y); }
  ctx.closePath();
  if(fill){ ctx.fillStyle=col; ctx.fill(); } else { ctx.strokeStyle=col; ctx.lineWidth=1.1; ctx.stroke(); }
}
function drawShipsIcon(cx, cy, col){
  icoShape(ICO_SHIP, cx, cy-3.5, 0.55, col, true);
  icoShape(ICO_SHIP, cx, cy+3.5, 0.55, col, false);
}
// Two missiles in the same way.
function drawMissilesIcon(cx, cy, col){
  icoShape(ICO_MISSILE, cx, cy-3.5, 0.7, col, true);
  icoShape(ICO_MISSILE, cx, cy+3.5, 0.7, col, false);
}
// A solid gear with eight teeth and a hole: the thin one read as a sun.
function drawGearSolid(cx, cy, r, col){
  const n=8, ro=r*1.2, ri=r*0.86, hole=r*0.38, tw=Math.PI/n*0.55;
  ctx.beginPath();
  for(let i=0;i<n;i++){
    const a=i*2*Math.PI/n;
    const pts=[[a-tw*1.25,ri],[a-tw*0.8,ro],[a+tw*0.8,ro],[a+tw*1.25,ri]];
    for(let j=0;j<4;j++){ const x=cx+Math.cos(pts[j][0])*pts[j][1], y=cy+Math.sin(pts[j][0])*pts[j][1]; if(i||j) ctx.lineTo(x,y); else ctx.moveTo(x,y); }
    ctx.arc(cx, cy, ri, a+tw*1.25, (i+1)*2*Math.PI/n-tw*1.25);
  }
  ctx.closePath();
  ctx.moveTo(cx+hole, cy); ctx.arc(cx, cy, hole, 0, Math.PI*2, true);
  ctx.fillStyle=col; ctx.fill('evenodd');
}


// Where the mouse is sitting, in game coordinates, whether or not it is
// allowed to steer. MOUSE deliberately stops updating over the bar so the
// ship does not follow a hand reaching for a button; this one keeps
// looking, because the bar needs to know what is being pointed at.
// Off the canvas entirely it goes to -1, which is inside nothing.
const HOVER = {x:-1, y:-1};
function hovering(x, y, w, h){
  return HOVER.x>=x && HOVER.x<=x+w && HOVER.y>=y && HOVER.y<=y+h;
}
// The pointer belongs over the bar and not over the field, where the ship
// is the pointer. It also stays visible whenever the game is not running:
// a panel, a held pause, a manual one, the title, the end of a run.
function syncCursor(){
  const hide = GS==='playing' && !paused && !panelOpen() && HOVER.y>=HUD_H;
  if(hide) document.body.classList.add('nocursor');
  else     document.body.classList.remove('nocursor');
}
// ── CALL MENU ──────────────────────────────────────────────────
// The game pauses while the menu is open, otherwise
// picking on a tablet would be a blind guess mid-fight.
// ── SHIP SWITCH ──────────────────────────────────────────────
// Stats for any hull. Hulls outside PLAYER_SHIPS (the FS1 roster) get the
// old fighter or bomber defaults.
function isBomberHull(key){ return hullClass(key)==='bo'; }
// Faction of a capital hull, read from the key and not from a unit's faction
// field: a defector carries 'hol' or 'renegade' there while still flying the
// hull it always had, and the hull is what has a hangar.
const HULL_FAC = {
  detyphon:'vasudan', dehatshepsut:'vasudan',
  deorionleft:'terran', deorionright:'terran', dehecate:'terran',
  ntfdeorion:'terran', ntfdehecate:'terran',
  sdcolossus:'gtva'
};
function hullFac(key){ return HULL_FAC[key] || ''; }
function shipFac(key){
  for(const s of PLAYER_SHIPS) if(s.key===key) return s.fac || '';
  return '';
}
// A hangar hands out hulls of its own faction. The Colossus is a joint yard
// and serves both.
function hangarServes(hangarFac, shipFac_){
  return hangarFac==='gtva' || (!!hangarFac && hangarFac===shipFac_);
}
// The Colossus counts as a hangar although her class is sd, no other sd hull
// does, and she is the only one that can be on the allied side anyway.
function isHangarShip(a){
  if(!a || a.small || a.dead || a.warpOut) return false;
  return hullClass(a.img)==='de' || a.img==='sdcolossus';
}
// Every friendly hangar out there right now. Two destroyers of different
// factions both count and their lists add up, rather than one winning.
function hangarFacs(){
  const out=[];
  for(const a of allies){
    if(!isHangarShip(a)) continue;
    const f=hullFac(a.img);
    if(f && out.indexOf(f)<0) out.push(f);
  }
  return out;
}
function colossusOnField(){
  for(const a of allies) if(a.colossus && !a.dead && !a.warpOut) return true;
  return false;
}
// Is this hull on offer from anything currently on the field?
function shipOffered(key){
  const sf=shipFac(key);
  const hf=hangarFacs();
  for(let i=0;i<hf.length;i++) if(hangarServes(hf[i], sf)) return true;
  return false;
}
// Hulls a mission can put the player into that no roster offers.
const EXTRA_SHIPS = {
  fipegasus: {key:'fipegasus', name:'GTF Pegasus', fac:'terran', spd:3.6, turn:0.17,
              hp:76, sh:85, sec:20},
  // Vasudan stealth fighter, lent for the reactor scan (M71, v170).
  fiptah:    {key:'fiptah', name:'GVF Ptah', fac:'vasudan', spd:3.5, turn:0.17,
              hp:76, sh:85, sec:20},
  // A captured Shivan fighter, for the flight beyond the second portal
  // (M78, v177). Flown by a Terran pilot it is FreeSpace's "SF Mara
  // (terrans)": 475/700 in the table, far tougher than the AI's (v185).
  fimara:    {key:'fimara', name:'SF Mara', fac:'shivan', spd:3.5, turn:0.18,
              hp:164, sh:179, sec:20}
};
// The player's own hull while a mission lends another, or ''.
let forcedPrev = '';
// sec: the secondary that goes with the hull for this mission.
let forcedSecPrev = '';
// sec: a weapon the mission needs, into the first secondary bank (v186).
function forceShip(key, sec){
  if(!forcedPrev){ forcedPrev = player.ship; }
  applyShip(key);
  if(sec) missionSec(arsenalKey(sec), false);
  notice(shipStats(key).name.toUpperCase()+' ASSIGNED', 'info');
}
// The next wave hands the player's own hull back, refitted with its own
// banks.
function releaseShip(){
  if(!forcedPrev) return;
  const k = forcedPrev; forcedPrev = '';
  forcedSecPrev = '';
  applyShip(k);
}
function shipStats(key){
  for(const s of PLAYER_SHIPS) if(s.key===key) return s;
  if(EXTRA_SHIPS[key]) return EXTRA_SHIPS[key];
  const b = isBomberHull(key);
  const v = SMALL_TBL[key] || [100,100];
  return {key:key, name:key, spd:b?PLAYER_SPD_BOMBER:PLAYER_SPD_FIGHTER, turn:PLAYER_TURN,
          hp:v[0], sh:v[1], sec:b?10:20};
}
// Puts the player into a hull. Without keep everything is refilled. With
// keep - fractions of the old hull, shields and ammo - the state carries
// over in proportion, so a half wrecked fighter stays half wrecked on a
// tougher hull instead of gaining or losing absolute points.
function applyShip(key, keep){
  const s = shipStats(key);
  player.ship   = key;
  player.spd    = s.spd;
  player.mvx = 0; player.mvy = 0;     // a new hull starts at rest
  player.turn   = s.turn;
  player.baseHp = s.hp;
  player.maxHp  = Math.round(s.hp*(player.hullMult||1));
  player.hp     = player.maxHp;
  player.maxSh  = s.sh;
  resetPlayerShield();
  // The banks of the hull (v186): its own store, its own racks.
  const enF = (keep && player.enMax) ? player.en/player.enMax : 1;
  player.en = null;
  applyLoadout(keep ? keep.sec : null);
  if(keep){
    player.hp      = Math.max(1, Math.round(player.maxHp*keep.hp));
    player.sh      = Math.min(player.maxSh, Math.round(player.maxSh*keep.sh));
    player.en      = player.enMax*enF;
  }
}
// Unlocks follow the score within a run. Several thresholds can fall in
// one step, e.g. after a big bonus, so this loops.
function tickShipUnlocks(){
  if(GS!=='playing' || FS1_MODE) return;
  // Counted from the start of the cycle: every cycle opens its own roster.
  if(cycleTabs()){
    // Two fleets, each opening down its own list.
    for(const f of FLEET_TABS){
      const list = facShips(f);
      while((shipUnlockedFac[f]||0) < list.length &&
            score-cycleBase >= PLAYER_SHIPS[list[shipUnlockedFac[f]]].unlock){
        const s = PLAYER_SHIPS[list[shipUnlockedFac[f]]];
        shipUnlockedFac[f] = (shipUnlockedFac[f]||0) + 1;
        notice(s.name.toUpperCase()+' AVAILABLE', 'unlock');
      }
    }
    shipUnlocked = (shipUnlockedFac.terran||0) + (shipUnlockedFac.vasudan||0);
    return;
  }
  while(shipUnlocked < PLAYER_SHIPS.length && score-cycleBase >= PLAYER_SHIPS[shipUnlocked].unlock){
    const s = PLAYER_SHIPS[shipUnlocked++];
    notice(s.name.toUpperCase()+' AVAILABLE', 'unlock');
  }
}
// The switch lands from an allied destroyer's hangar, so one has to be on
// the field. The campaign mode assigns its hulls itself.
function shipSwapReady(){
  if(GS!=='playing' || FS1_MODE || inJump()) return false;
  if(forcedPrev) return false;      // this mission's hull is not negotiable
  if(shipUnlocked<2) return false;
  // One switch per wave, except while the Colossus is on station: her yard
  // stays open, and only the first switch of a wave refits.
  if(shipSwapWave===wave && !colossusOnField()) return false;
  // Something other than the active hull has to be unlocked AND on offer
  // from a hangar that is actually on the field.
  for(let i=0;i<PLAYER_SHIPS.length;i++){
    if(!shipIsOpen(i)) continue;
    const s=PLAYER_SHIPS[i];
    if(s.key!==player.ship && shipOffered(s.key)) return true;
  }
  return false;
}
function setShipMenu(open){
  if(!open && shipMenu) holdResume();
  shipMenu = open;
  if(open) hgShow = null;
  // Two panels at once meant closing one took the pause the other still
  // needed, so opening one closes the other.
  if(open) callMenu = false;
  syncPause();
  if(!open && GS==='playing'){ MOUSE.x = player.x; MOUSE.y = player.y; }
  syncCursor();
}
function toggleShipMenu(){
  if(shipMenu){ setShipMenu(false); return; }
  if(!shipSwapReady()) return;
  if(callMenu) setCallMenu(false);
  // The tab of the hull being flown, if its hangar is here; otherwise
  // the first fleet that has one.
  if(cycleTabs()) hangarTab = pickTab(hangarTabOpen, shipFac(player.ship));
  setShipMenu(true);
}
function swapShip(key){
  if(!shipMenu || key===player.ship) return;
  const i = PLAYER_SHIPS.findIndex(function(s){return s.key===key;});
  if(i<0 || !shipIsOpen(i)) return;
  if(!shipOffered(key)) return;
  // The first switch of a wave arrives fresh. A further one is only reachable
  // at the Colossus and carries the current state over in proportion, so the
  // open yard cannot be used as a repair bay.
  const again = (shipSwapWave===wave);
  const keep  = again ? {hp:  player.maxHp>0  ? player.hp/player.maxHp       : 1,
                         sh:  player.maxSh>0  ? player.sh/player.maxSh       : 0,
                         sec: player.secMax>0 ? player.secAmmo/player.secMax : 0} : null;
  setShipMenu(false);
  applyShip(key, keep);
  shipSwapWave = wave;
  notice(PLAYER_SHIPS[i].name.toUpperCase()+(again?' - NO REFIT':''), 'good');
}
// ── FLEET TABS (v163) ───────────────────────────────────────
// From the Shivan cycle on both fleets serve, each on its own tab, in the
// hangar and in the support menu (Silvio). Hangar: a tab is open while an
// allied destroyer of that fleet is on the field; the Colossus serves both,
// and with no hangar there is no switch at all. Support: the same rule, but
// with no allied destroyer on the field both tabs are open.
const FLEET_TABS = ['terran','vasudan'];
const FLEET_TAB_LABEL = {terran:'TERRAN', vasudan:'VASUDAN'};
const FLEET_TAB_H = 22;
let hangarTab = 'terran', callTab = 'terran';
function hangarTabOpen(fac){
  const hf = hangarFacs();
  return hf.indexOf(fac) >= 0 || hf.indexOf('gtva') >= 0;
}
function callTabOpen(fac){
  if(!allyFacOn(fac)) return false;
  if(!cycleTabs()) return true;
  return !hangarFacs().length || hangarTabOpen(fac);
}
// The preferred tab if it is open, else the first open one.
function pickTab(openFn, prefer){
  if(prefer && openFn(prefer)) return prefer;
  for(const f of FLEET_TABS) if(openFn(f)) return f;
  return prefer || FLEET_TABS[0];
}
// The other tab, if it is open. Tab and the arrow keys come through here.
function nextTab(cur, openFn){
  for(const f of FLEET_TABS) if(f!==cur && openFn(f)) return f;
  return cur;
}
// Two tabs across the panel. A shut one is drawn dark and takes no tap.
function drawFleetTabs(x, y, w, cur, openFn, rects){
  const gap = 4, tw = (w - gap)/2;
  for(let i=0;i<FLEET_TABS.length;i++){
    const f = FLEET_TABS[i], tx = x + i*(tw+gap);
    const open = openFn(f), on = open && f===cur;
    const hv = open && !on && hovering(tx, y, tw, FLEET_TAB_H);
    uiCell(tx, y, tw, FLEET_TAB_H, {state: on ? 'on' : (!open ? 'off' : (hv ? 'ready' : null))});
    ctx.fillStyle = on ? TH('accentWarm') : (open ? (hv ? TH('textBright') : TH('text')) : TH('textDim'));
    ctx.font = thLabel(11); ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(FLEET_TAB_LABEL[f], tx+tw/2, y+FLEET_TAB_H/2+1);
    if(open) rects.push({x:tx, y:y, w:tw, h:FLEET_TAB_H, tab:f});
  }
  ctx.textAlign = 'left';
}
// Two arrows passing each other.
function drawSwapIcon(cx, cy, col){
  ctx.save();
  ctx.strokeStyle=col; ctx.fillStyle=col; ctx.lineWidth=1.5;
  ctx.beginPath(); ctx.moveTo(cx-6,cy-3); ctx.lineTo(cx+3,cy-3); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx+7,cy-3); ctx.lineTo(cx+2,cy-6.5); ctx.lineTo(cx+2,cy+0.5); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(cx+6,cy+3); ctx.lineTo(cx-3,cy+3); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx-7,cy+3); ctx.lineTo(cx-2,cy-0.5); ctx.lineTo(cx-2,cy+6.5); ctx.closePath(); ctx.fill();
  ctx.restore();
}
// Filled pips for a value against its steps, so players compare hulls
// without reading raw numbers.
function statPips(x, y, v, steps, lit){
  // Restores the fill colour it found. Without this the next text drawn
  // inherited the colour of the last pip, which is why the AGI label was
  // bright behind a full speed bar and dark behind an empty one.
  const prevFill = ctx.fillStyle;
  let n = 0; for(const s of steps) if(v>=s-1e-9) n++;
  for(let i=0;i<steps.length;i++){
    ctx.fillStyle = i<n ? lit : '#1c2a22';
    ctx.fillRect(x+i*7, y, 5, 5);
  }
  ctx.fillStyle = prevFill;
}
// Faint hull behind a menu cell, clipped to it, so a row shows the ship it
// offers instead of its name alone. Drawn before the text and at low alpha
// so the labels stay readable. Fitted whole rather than cropped: a long
// destroyer ends up flat and wide, which is what it looks like. Right
// aligned, away from the label column, and always facing right regardless
// of which way the sprite was drawn. A sprite that has not loaded leaves
// the cell untouched.
const MENU_BG_ALPHA     = 0.26;   // unlocked, or affordable
const MENU_BG_ALPHA_OFF = 0.11;   // locked, or out of tickets
const MENU_BG_PAD       = 3;
function drawHullBg(key, x, y, w, h, lit){
  const img = IMGS[key];
  if(!img || !img.width || !img.height) return;
  const p  = MENU_BG_PAD;
  const sc = Math.min((w-p*2)/img.width, (h-p*2)/img.height);
  if(!(sc > 0)) return;
  const dw = img.width*sc, dh = img.height*sc;
  ctx.save();
  ctx.beginPath(); ctx.rect(x+1, y+1, w-2, h-2); ctx.clip();
  ctx.globalAlpha = lit ? MENU_BG_ALPHA : MENU_BG_ALPHA_OFF;
  ctx.translate(x+w-p-dw/2, y+h/2);
  if(spriteFacing(key)==='left') ctx.scale(-1,1);
  ctx.drawImage(img, -dw/2, -dh/2, dw, dh);
  ctx.restore();
}
// How many primary barrels a hull really fires with. Read from the mount
// data the packer injects, not from PLAYER_SHIPS, so this number and the one
// pShoot() uses cannot drift apart. Zero means no mount data: pShoot() then
// uses its two fallback muzzles, which carry no damage figure of their own.
function primaryCount(key){
  const m = mountsFor(key);
  return (m && m.primary && m.primary.length) ? m.primary.length : 0;
}
// volleyDmg() is the damage of a single barrel, which is why more barrels do
// not simply multiply. This is what a whole volley lands.
function volleyTotal(n){ if(!n || n < 1) n = 1; return volleyDmg(n)*n; }
// ── WEAPONS ──────────────────────────────────────────────────
// A weapon is data. Everything that differs between two of them lives in
// these tables, so the next one is a line here rather than a branch inside
// the firing routine.
//
// dmg and rate are factors on the values the game fired with before this
// existed, and the Prometheus carries 1.0 for both. That is what makes the
// standard fit provably unchanged: the numbers are not retyped anywhere.
//
// range is how far a bolt travels before it gives out, in points. 0 means it
// runs to the edge of the field, the way every bolt used to.
const PLAYER_FR_BASE = 28;   // steps between shots at rate 1.0
// Since v186 the player flies the FS2 arsenal (ARSENAL_P / ARSENAL_S in
// 56_banks.js). What stays here are the game's own guns, which the AI flies
// too: the Sidhe and the Dante. wait: steps between volleys, en: energy per
// volley (Silvio: on the scale of the Prometheus S and the Kayser).
const PRIMARIES = [
  // pellets and spread turn one trigger pull into a cone. dmg is the
  // damage of the WHOLE volley, shared out, so a single pellet is slight
  // and a face full of them is not.
  // Named after the primary of Blue Planet: War in Heaven.
  {key:'scatter', name:'Sidhe', unlock:14000,
   dmg:2.60, rate:1.85, spd:8, range:300, pellets:7, spread:0.30, wait:52, en:1.0,
   col:'#ffd08a', glow:'rgba(255,170,70,0.30)',
   note:'a cone of pellets - murder in a crowd, nothing at range'},
  // fuse is the distance at which it bursts of its own accord. That is
  // what makes it more than a round with a bonus: held on the trigger it
  // lays shrapnel across a fixed range and an attack run has to come
  // through it.
  {key:'dante', name:'Dante', unlock:0, fromWave:61,
   dmg:1.10, rate:1.40, spd:7.5, range:420, fuse:300, wait:39, en:1.2,
   shards:9, shardDmg:0.38, shardSpd:3.4, shardRange:70,
   col:'#ffb066', glow:'rgba(255,140,50,0.34)',
   note:'bursts on impact and by itself at range - shrapnel, star shaped'}
];
// The player's secondaries are the FS2 ones; the AI keeps AI_SECONDARIES.
const SECONDARIES = ARSENAL_S;
// Shrapnel, star shaped from a point. Three weapons make it - the Dante on
// impact, the Dante on its fuse, and the Infyrno when it is burst - so it
// is written once and they all call it. The shards are ordinary bolts and
// travel the ordinary way, which is what keeps them cheap.
// ally: shrapnel of an escort's round (no score for the player).
// How the pieces of one burst fly. A perfect star read as drawn with a
// ruler (Silvio, v159), so every burst is a little different: one piece
// more or less now and then, each off its slot in the circle, each with
// its own speed, reach and size. mul keeps the burst's total damage where
// it was whatever the count comes out as.
function shardSpread(n, spd, range){
  const r = Math.random();
  const m = Math.max(3, n + (r < 0.25 ? -1 : (r > 0.75 ? 1 : 0)));
  const off = Math.random()*Math.PI*2, gap = Math.PI*2/m;
  const out = [];
  for(let i=0;i<m;i++){
    const a  = off + i*gap + (Math.random()-0.5)*gap*0.9;
    const s  = spd * (0.72 + Math.random()*0.56);
    const rg = range * (0.65 + Math.random()*0.7);
    const big = Math.random();
    out.push({a:a, spd:s, life:Math.max(1, Math.round(rg/s)),
              w:(5 + big*6)|0, h:big > 0.6 ? 4 : (big > 0.25 ? 3 : 2),
              mul:n/m});
  }
  return out;
}
function shardBurst(x, y, n, dmg, spd, range, col, glow, ally){
  for(const q of shardSpread(n, spd, range)){
    pBullets.push({x:x, y:y, vx:Math.cos(q.a)*q.spd, vy:Math.sin(q.a)*q.spd,
                   w:q.w, h:q.h, dmg:dmg*q.mul, col:col, glow:glow, pLife:q.life,
                   shard:true, ally:!!ally});
  }
  // The fireball sits a touch off the point of burst and varies in size.
  spawnFireball(x + (Math.random()-0.5)*8, y + (Math.random()-0.5)*8,
                18 + Math.random()*10, 14 + Math.random()*8);
  spawnDebris(x, y, 8 + (Math.random()*5|0), 255,190,90, 255,110,0, true);
}
// A warhead that goes for the innards. subHit only touches whatever
// happens to lie under the impact; this looks for the nearest living
// subsystem and puts the whole warhead into that, which is the entire
// point of carrying one.
// What a subsystem warhead puts into the system it finds. At 1 a
// Stiletto took five or six bombs per cruiser system, more than an
// Ursa carries for a single ship. The hull only gets the usual bleed
// of the plain warhead, so this is no way to kill a ship faster.
const SUB_WARHEAD_MUL = 5.5;
function subStrike(e, dmg, hx, hy){
  if(!e.subs || !e.subs.length) return dmg;
  return subStrikeRaw(e, dmg*SUB_WARHEAD_MUL, hx, hy) / SUB_WARHEAD_MUL;
}
function subStrikeRaw(e, dmg, hx, hy){
  let best = null, bd = Infinity;
  for(const s of e.subs){
    if(s.dead) continue;
    const p = subPos(e, s);
    const d = Math.hypot(p.x-hx, p.y-hy);
    if(d < bd){ bd = d; best = s; }
  }
  if(!best) return dmg;
  const p = subPos(e, best);
  return subHit(e, dmg, p.x, p.y);
}
function priDef(key){
  for(const w of ARSENAL_P) if(w.key===key) return w;
  for(const w of PRIMARIES) if(w.key===key) return w;
  // Guns only the AI flies (the Shivan lasers, the old player guns).
  if(typeof AI_PRIMARIES!=='undefined' && AI_PRIMARIES[key]) return AI_PRIMARIES[key];
  return ARSENAL_P[0];
}
// The AI's secondaries first: its rounds carry the old keys, and three of
// them share a name with a FS2 weapon. The player's rounds carry their
// definition along (b.wd) and do not come through here.
function secDef(key){
  for(const w of AI_SECONDARIES) if(w.key===key) return w;
  for(const w of ARSENAL_S) if(w.key===key) return w;
  return AI_SECONDARIES[0];
}
function curPri(){ return priDef(player.pri); }
function curSec(){ return secDefP(player.sec); }
function hullSecCls(key){ return isBomberHull(key) ? 'bomb' : 'missile'; }
// A weapon's name can depend on who is flying it.
function weaponName(w){
  if(w.nameTer && shipFac(player.ship)==='terran') return w.nameTer;
  return w.name;
}
// Unlocks follow the score within a run, the same way the hulls do.
function weaponOpen(w){
  if(FS1_MODE || UI_WEAPONS) return true;
  // fromWave: a weapon handed out with a mission rather than earned with
  // points - the Dante opens with the Shivan cycle (Silvio), and not before
  // it, whatever the score.
  if(w.fromWave) return waveReached(w);
  return score >= (w.unlock||0);
}
function waveReached(w){ return !w.fromWave || wave >= w.fromWave; }
// The one place that puts a fit onto the ship (v186): the banks of the
// hull, as the player set them up this run or as the table has them.
function applyLoadout(keepSec){
  setBanks(player.ship, fitFor(player.ship), keepSec);
}
// A refit fills every rack. This is what makes the panel a rearm rather
// than a swap, and it is the whole reason a corvette on the field is worth
// keeping. The weapon store keeps its charge (v191, Silvio): a refit in the
// middle of a fight was a free recharge.
function rearmFull(){
  applyLoadout();
  player.secTimer = 0;
}
// Rounds of every rack of a hull's default fit, for the hangar.
function secRounds(key){
  const b = shipBanks(key);
  let n = 0;
  for(let i=0;i<Math.min(3, b.s.length);i++) n += bankAmmoMax(key, i, b.s[i]);
  return n;
}
// Newly reached weapons are announced like newly reached hulls, so a
// threshold is something you notice rather than something you find.
const WPN_SEEN = {};
function tickWeaponUnlocks(){
  if(GS!=='playing' || FS1_MODE) return;
  for(const w of ARSENAL_P.concat(PRIMARIES, ARSENAL_S)){
    if((!w.unlock && !w.fromWave) || WPN_SEEN[w.key] || !weaponOpen(w)) continue;
    WPN_SEEN[w.key] = true;
    notice(weaponName(w).toUpperCase()+' AVAILABLE', 'unlock');
  }
}
// A rearm comes off an allied corvette, the way a hull comes out of a
// destroyer's hangar. One has to be on the field and finished warping in.
function corvetteOnField(){
  for(const a of allies)
    if(a.type==='corvette' && !a.dead && !a.warpOut && !(a.warp>0)) return true;
  return false;
}
function rearmReady(){
  if(GS!=='playing' || inJump()) return false;
  return corvetteOnField();
}
let rearmMenu = false;
function setRearmMenu(open){
  if(!open && rearmMenu) holdResume();
  rearmMenu = open;
  if(open){ shipMenu = false; callMenu = false; rmBank = 'p0'; rmShow = null; }
  syncPause();
  if(!open && GS==='playing'){ MOUSE.x = player.x; MOUSE.y = player.y; }
  syncCursor();
}
function toggleRearmMenu(){
  if(rearmMenu){ setRearmMenu(false); return; }
  if(!rearmReady()) return;
  setRearmMenu(true);
}
// The rearm window (v190): pick a bank, then the weapon for it. slot:
// 'p0', 'p1', 's0'..'s2'. key: the weapon to fit; without one the bank
// steps to the next weapon open to it (the old interim list, v186). The
// weapon already in the bank fills it again - a corvette is where you
// reload (Silvio). Every pick fills every rack.
function fitWeapon(slot, key){
  if(!rearmMenu || !slot) return;
  const pri = slot[0]==='p', i = +slot.slice(1);
  const fit = {p:(player.pb||[]).map(function(b){ return b.key; }),
               s:(player.sb||[]).map(function(b){ return b.key; })};
  const list = pri ? fit.p : fit.s;
  if(i >= list.length) return;
  let nk = key;
  if(nk === undefined) nk = nextChoice(player.ship, pri, list[i]);
  else {
    const w = bankChoices(player.ship, pri).find(function(q){ return q.key===nk; });
    if(!w || !weaponOpenFor(w, player.ship)) return;
  }
  const same = (nk === list[i]);
  if(same && key === undefined) return;
  list[i] = nk;
  FITS[player.ship] = fit;
  rearmFull();
  plogRearm();
  notice(same ? 'REARMED'
              : weaponName(pri ? priDefP(nk) : secDefP(nk)).toUpperCase()+' FITTED', 'good');
}

// ── HANGAR LAYOUT ────────────────────────────────────────────
// The hangar is a comparison table, not a wall of tiles. One row per hull
// over the full width, fighters and bombers in groups of their own, and every
// figure in a fixed column so hull sits under hull and two hulls can be read
// against each other at a glance. A locked hull collapses to a thin line:
// something you cannot take should not weigh as much as something you can.
//
// Everything visible here comes out of the SURFACE KIT. No shape is invented
// for this panel.
const HG_W        = 780;    // panel width, of 800 logical points (v192: list + card)
const HG_LIST_W   = 452;    // the list on the left, the info card beside it
const HG_MIN_H    = 420;    // the card needs the room even with two hulls open
let hgShow = null;          // the hull the card is about
const HG_PAD      = 12;     // inner margin, also the left edge of every row
const HG_ROW      = 38;     // a hull that can be taken
const HG_ROW_LOCK = 20;     // a hull that cannot
const HG_ROW_TIGHT = 32;    // a hull that can, when the list is at its longest (v194)
const HG_GAP      = 4;
const HG_HEAD     = 24;     // group heading, its scale and the column titles
const HG_TITLE    = 34;     // header line of the panel
const HG_FOOT     = 18;
const HG_GROUPGAP = 14;     // the air that separates fighters from bombers
const HG_NUM      = 8;      // the keyboard digit, measured from the row's left
const HG_NUM_W    = 16;
const HG_PIC      = 30;     // picture cell
const HG_PIC_W    = 52;
const HG_NAME     = 92;
const HG_PIC_ALPHA     = 0.95;   // it is a portrait now, not a watermark
const HG_PIC_ALPHA_OFF = 0.35;
// Column starts, measured from the row's left edge. The row is
// HG_W - 2*HG_PAD wide, so the last column has to end inside 636.
// v192: guns, volley and racks moved into the card.
const HG_COLS = [
  {k:'hull',   x:232, label:'HULL'},
  {k:'shield', x:282, label:'SHIELD'},
  {k:'spd',    x:336, label:'SPD'},
  {k:'agi',    x:396, label:'AGI'}
];
// Which hull belongs in which group. Read from the hull key, the same way the
// rest of the file decides what a bomber is, so a new hull lands in the right
// group without a second list to keep in step.
function hangarGroups(){
  const fi=[], bo=[];
  for(let i=0;i<PLAYER_SHIPS.length;i++){
    // With tabs only the open tab's fleet is listed.
    if(cycleTabs() && PLAYER_SHIPS[i].fac!==hangarTab) continue;
    (isBomberHull(PLAYER_SHIPS[i].key) ? bo : fi).push(i);
  }
  return [{head:'FIGHTERS', idx:fi}, {head:'BOMBERS', idx:bo}];
}
// Where everything sits, worked out before anything is drawn: the panel grows
// and shrinks with the number of hulls that are open, and both the drawing and
// the tap rectangles read the same plan rather than repeating the arithmetic.
// The order the rows appear in, as roster indices. The groups reorder the
// list, and the keyboard has to agree with what is on screen, so both read
// this and nothing counts rows on its own.
function hangarOrder(){
  const out = [];
  for(const g of hangarGroups()) for(const i of g.idx) out.push(i);
  return out;
}
function hangarLayout(tight){
  // Nine open hulls (the Terran roster since the Perseus, v159) no longer fit
  // the field with the full gaps; then the gaps between rows close up.
  // v194: with the DONE button that is still too tall, so a second step
  // (tight 2) also makes the open rows a little lower.
  tight = tight|0;
  const gap = tight ? 2 : HG_GAP, ggap = tight ? 8 : HG_GROUPGAP;
  const rowH = tight >= 2 ? HG_ROW_TIGHT : HG_ROW;
  const groups = hangarGroups();
  const plan = [];
  let h = HG_TITLE;
  // Room for the fleet tabs under the header.
  const tabY = h;
  if(cycleTabs()) h += FLEET_TAB_H + 8;
  for(const g of groups){
    if(!g.idx.length) continue;
    plan.push({head:g.head, y:h});
    h += HG_HEAD;
    for(const i of g.idx){
      const s = PLAYER_SHIPS[i];
      const cur    = s.key===player.ship;
      const locked = !shipIsOpen(i);
      // Unlocked, but no hangar of its faction on the field: it keeps a full
      // row, because it is yours and its figures still have to be readable.
      const off    = !locked && !cur && !shipOffered(s.key);
      const rh     = locked ? HG_ROW_LOCK : rowH;
      plan.push({i:i, y:h, h:rh, cur:cur, locked:locked, off:off});
      h += rh + gap;
    }
    h += ggap;
  }
  h += DONE_ROOM + HG_FOOT;
  if(tight < 2 && h > H-8) return hangarLayout(tight+1);
  h = Math.max(h, HG_MIN_H);
  return {mx:((W-HG_W)/2)|0, my:((H-h)/2)|0, mw:HG_W, mh:h, plan:plan, tabY:tabY};
}
// The sprite in its own cell, fitted whole and always facing right. Every hull
// is fitted to the same cell rather than to its real length, so the column
// stays a column. A sprite that has not loaded leaves the cell empty instead
// of throwing.
function drawHullCell(key, x, y, w, h, lit){
  const img = IMGS[key];
  if(!img || !img.width || !img.height) return;
  const p  = 3;
  const sc = Math.min((w-p*2)/img.width, (h-p*2)/img.height);
  if(!(sc > 0)) return;
  const dw = img.width*sc, dh = img.height*sc;
  ctx.save();
  ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  ctx.globalAlpha = lit ? HG_PIC_ALPHA : HG_PIC_ALPHA_OFF;
  ctx.translate(x+w/2, y+h/2);
  if(spriteFacing(key)==='left') ctx.scale(-1,1);
  ctx.drawImage(img, -dw/2, -dh/2, dw, dh);
  ctx.restore();
}
// The digit that takes this hull from the keyboard, in a chip of its own. It
// is the shortcut, not decoration, and it counts down the panel as shown:
// fighters 1 to 5, bombers 6 to 8. The key handler reads the same order.
function drawKeyChip(d, x, y, w, h, lit){
  thPlate(x, y, w, h, TH('back'), 3);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillStyle = lit ? TH('text') : TH('textDim');
  ctx.font = thValue(10, true);
  ctx.fillText(String(d), x+w/2, y+h/2+0.5);
  ctx.textAlign='left';
}
// A long name is set smaller rather than cut off (v192: Hercules Mk II).
function hgName(t, x, y){
  const room = HG_COLS[0].x - HG_NAME - 8;
  let sz = 15;
  ctx.font = thValue(sz, true);
  while(sz > 11 && ctx.measureText(t).width > room){ sz--; ctx.font = thValue(sz, true); }
  ctx.fillText(thFit(t, room), x, y);
}
// DONE (v191 in rearm, v194 in hangar and support, Silvio): the windows
// have grown so large that little is left outside them to tap. The line
// under it says what closing means. The tap rectangle goes into the
// window's own list with close:true.
// What closes a window from the keyboard (v194): its own key always; ESC
// only outside full screen, where the browser takes ESC to leave full
// screen and the game never sees it (Silvio).
function closeKeys(k, small){
  const fs = (typeof isFullscreen === 'function') && isFullscreen();
  const t = fs ? k+' closes' : k+' or ESC closes';
  return small ? t : t.toUpperCase();
}
function drawDoneButton(x, y, w, sub, rects){
  const hot = hovering(x, y, w, DONE_H);
  ctx.save();
  ctx.textBaseline = 'middle';
  thButton(x, y, w, DONE_H, 'on');
  if(hot) thGlowPath(x, y, w, DONE_H, 4, 0.9);
  ctx.textAlign='center'; ctx.fillStyle=TH('textBright'); ctx.font=thValue(12, true);
  ctx.fillText('DONE', x+w/2, y+11);
  ctx.fillStyle=TH('accentWarm'); ctx.font=thLabel(7);
  ctx.fillText(sub, x+w/2, y+23);
  ctx.restore();
  if(rects) rects.push({x:x, y:y, w:w, h:DONE_H, close:true});
}
function drawShipMenu(){
  if(!shipMenu) return;
  const L  = hangarLayout();
  const mx = L.mx, my = L.my, rw = HG_LIST_W;
  ctx.save();
  thFrame(mx, my, L.mw, L.mh, HG_TITLE);
  window._shipPanelRect = {x:mx, y:my, w:L.mw, h:L.mh};

  // Header: what this is on the left, on what terms on the right.
  ctx.textBaseline='middle';
  ctx.textAlign='left';
  ctx.fillStyle=TH('textBright'); ctx.font=thLabel(14);
  ctx.fillText('SWITCH SHIP', mx+HG_PAD, my+16);
  ctx.textAlign='right';
  ctx.fillStyle=colossusOnField() ? TH('accentWarm') : TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText(colossusOnField() ? 'COLOSSUS HANGAR OPEN  -  NO REFIT AFTER THE FIRST SWITCH'
                                 : 'ONE SWITCH PER WAVE', mx+L.mw-HG_PAD, my+16);

  const TICKS = HG_COLS.map(function(c){ return c.x; });
  const ORDER = hangarOrder();
  window._shipRects=[];
  if(cycleTabs())
    drawFleetTabs(mx+HG_PAD, my+L.tabY+2, L.mw-HG_PAD*2, hangarTab, hangarTabOpen, window._shipRects);
  for(const p of L.plan){
    const ry = my+p.y;
    // A group heading carries the column titles and the scale under them, so
    // the reading is set up twice on the way down instead of once at the top.
    if(p.head !== undefined){
      ctx.textAlign='left'; ctx.textBaseline='middle';
      ctx.fillStyle=TH('text'); ctx.font=thLabel(11);
      ctx.fillText(p.head, mx+HG_PAD, ry+8);
      ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
      for(const c of HG_COLS) ctx.fillText(c.label, mx+HG_PAD+c.x, ry+9);
      thScale(mx+HG_PAD, ry+15, rw, TICKS, TH('edgeLight'));
      continue;
    }
    const s    = PLAYER_SHIPS[p.i];
    const rx   = mx+HG_PAD;
    const open = !p.locked && !p.off;
    if(hovering(rx, ry, rw, p.h)) hgShow = s.key;

    if(p.locked){
      // Locked: the dark plate every unavailable control carries (v179),
      // the name, and what it costs.
      thPlate(rx, ry, rw, p.h, TH('back'));
      ctx.textAlign='left'; ctx.textBaseline='middle';
      ctx.fillStyle=TH('textDim'); ctx.font=thValue(11, false);
      ctx.fillText(s.name, rx+HG_NAME, ry+p.h/2);
      ctx.fillText('unlocks at '+(cycleBase+s.unlock).toLocaleString('en-US')+' points',
                   rx+HG_COLS[0].x, ry+p.h/2);
      window._shipRects.push({x:rx, y:ry, w:rw, h:p.h, ship:s.key, key:null});
      continue;
    }

    thPlate(rx, ry, rw, p.h,
            p.cur ? TH('raised') : (open ? TH('panelFront') : TH('back')));
    // The pointer on a row that can be taken: half the ring, as on a tab.
    if(open && !p.cur && hovering(rx, ry, rw, p.h)) thGlowPath(rx, ry, rw, p.h, 6, 0.5);
    if(p.cur){
      // Three marks for the one row that is active, and they are the kit's,
      // not this panel's: the ring, the two angles, the bar on the edge.
      thGlowPath(rx, ry, rw, p.h, 6, 1);
      thBrackets(rx, ry, rw, p.h, TH('accentWarm'));
      ctx.fillStyle=TH('accentWarm');
      ctx.fillRect(rx, ry+6, 3, p.h-12);
    }
    drawKeyChip(ORDER.indexOf(p.i)+1, rx+HG_NUM, ry+(p.h-16)/2,
                HG_NUM_W, 16, open || p.cur);
    drawHullCell(s.key, rx+HG_PIC, ry+3, HG_PIC_W, p.h-6, open || p.cur);

    ctx.textAlign='left'; ctx.textBaseline='middle';
    ctx.fillStyle = p.cur ? TH('accentWarm') : (open ? TH('textBright') : TH('textDim'));
    ctx.font=thValue(15, true);
    if(p.off){
      // Two lines only where there is a reason to give: the name, and why the
      // row cannot be taken right now.
      hgName(s.name, rx+HG_NAME, ry+Math.round(p.h*0.34));
      ctx.fillStyle=TH('textDim'); ctx.font=thValue(9, false);
      // v194: short enough to end before the HULL column (v192 moved it left)
      ctx.fillText(thFit('NO '+(s.fac||'').toUpperCase()+' HANGAR HERE', HG_COLS[0].x-HG_NAME-8), rx+HG_NAME, ry+Math.round(p.h*0.71));
    } else {
      hgName(s.name, rx+HG_NAME, ry+p.h/2);
    }

    // The figures. Same column, same font, same baseline on every row.
    const vCol = open ? TH('textBright') : TH('textDim');
    const pCol = open ? TH('accentWarm')  : TH('textDim');
    const cy   = ry+p.h/2;
    ctx.font=thValue(15, false);
    ctx.fillStyle=vCol;
    ctx.fillText(String(s.hp), rx+HG_COLS[0].x, cy);
    ctx.fillText(String(s.sh), rx+HG_COLS[1].x, cy);
    statPips(rx+HG_COLS[2].x, cy-3, s.spd,  [2.2,2.5,2.9,3.2,3.5],      pCol);
    statPips(rx+HG_COLS[3].x, cy-3, s.turn, [0.08,0.10,0.12,0.14,0.17], pCol);

    // Every row swallows its own tap, so a row that cannot be taken cannot
    // close the panel by accident either.
    window._shipRects.push({x:rx, y:ry, w:rw, h:p.h, ship:s.key,
                            key:(open && !p.cur) ? s.key : null});
  }

  // The card: the hull under the pointer, else the one you fly (v192).
  if(!hgShow || !PLAYER_SHIPS.some(function(q){ return q.key === hgShow; })) hgShow = player.ship;
  const cx = mx+HG_PAD+HG_LIST_W+12, cy0 = my+HG_TITLE+(cycleTabs() ? FLEET_TAB_H+8 : 0)+4;
  drawInfoCard(cx, cy0, mx+L.mw-HG_PAD-cx, my+L.mh-26-cy0, hangarCard(hgShow));
  // DONE under the list, its foot on the card's foot (v194).
  drawDoneButton(mx+HG_PAD+((HG_LIST_W-DONE_W)/2|0), my+L.mh-26-DONE_H, DONE_W,
                 'YOUR SHIP IS KEPT', window._shipRects);

  ctx.textAlign='center'; ctx.fillStyle=TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText('DIGIT OR CLICK SWITCHES  -  '+closeKeys('V'), mx+L.mw/2, my+L.mh-11);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}

// A stopped field with nothing on it looks broken, so it says what it is
// waiting for. Quiet, and it pulses rather than blinks, because it is not
// urgent - the fight is not going anywhere.
function drawResumeHint(){
  if(!resumeHold || GS!=='playing' || panelOpen()) return;
  const k = 0.55 + 0.45*Math.sin(fc*0.06);
  ctx.save();
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.globalAlpha = k;
  ctx.fillStyle = TH('textBright'); ctx.font = thLabel(12);
  ctx.fillText('TAP OR PRESS ANY KEY TO RESUME', W/2, H-40);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}
// ── INFO CARD (v192) ─────────────────────────────────────────
// The fixed panel on the right of the hangar and the support window, the
// same build as the rearm info panel: the model (it turns while the pointer
// is on it, the wheel zooms), the name, facts in two fixed rows, bars
// against the best of the list with a white mark for what you have now,
// a few lines of what it means, the keys. Every area keeps its place, so
// nothing below jumps when you go down the list (Silvio).
function drawInfoCard(x, y, w, h, o){
  thPlate(x, y, w, h, TH('panelFront'));
  const px = x+6, pw = w-12, py = y+6;
  ctx.fillStyle = TH('back'); ctx.fillRect(px, py, pw, IC_PIC_H);
  window._infoPicRect = {x:px, y:py, w:pw, h:IC_PIC_H};
  const mk = M3D_ALIAS[o.model] || o.model, hot = hovering(px, py, pw, IC_PIC_H);
  let shown = false;
  if(typeof m3dDraw === 'function' && mk) shown = m3dDraw(mk, px, py, pw, IC_PIC_H, m3dView(mk, hot));
  if(shown){
    ctx.textAlign='right'; ctx.textBaseline='middle';
    ctx.fillStyle = hot ? TH('accent') : TH('textDim'); ctx.font = thLabel(7);
    ctx.fillText(hot ? 'WHEEL: ZOOM' : 'POINT TO TURN', px+pw-6, py+8);
  } else if(o.model) drawHullCell(o.model, px+10, py+6, pw-20, IC_PIC_H-12, true);
  let iy = py + IC_PIC_H + 16;
  ctx.textAlign='left'; ctx.textBaseline='middle';
  ctx.fillStyle = TH('textBright'); ctx.font = thValue(15, true);
  ctx.fillText(thFit(o.title||'', w-20), x+10, iy); iy += 16;
  ctx.fillStyle = o.subCol || TH('textDim'); ctx.font = thLabel(8);
  ctx.fillText(thFit(o.sub||'', w-20), x+10, iy); iy += 18;
  let fx = x+10, row = 0;
  ctx.font = thLabel(7);
  for(const t of (o.facts||[])){
    const tw = ctx.measureText(t).width+12;
    if(fx+tw > x+w-8){ fx = x+10; row++; }
    if(row >= IC_FACT_ROWS) break;
    ctx.strokeStyle=TH('edgeLight'); ctx.lineWidth=1; ctx.strokeRect(fx+0.5, iy+row*18-7.5, tw, 15);
    ctx.fillStyle=TH('textBright'); ctx.fillText(t, fx+6, iy+row*18); fx += tw+5;
  }
  iy += (IC_FACT_ROWS-1)*18 + 20;
  if(o.bars && o.bars.length){
    ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8); ctx.fillText(o.barHead||'', x+10, iy); iy += 14;
    const bx = x+84, bw = w-140;
    for(const r of o.bars){
      ctx.fillStyle=TH('text'); ctx.font=thLabel(8); ctx.fillText(r.l, x+10, iy);
      ctx.fillStyle=TH('edgeDark'); ctx.fillRect(bx, iy-4, bw, 8);
      ctx.fillStyle=TH('accentWarm'); ctx.fillRect(bx, iy-4, Math.max(1, bw*r.v), 8);
      if(r.cur != null){ ctx.fillStyle=TH('textBright'); ctx.fillRect(bx+bw*r.cur-1, iy-6, 2, 12); }
      ctx.textAlign='right'; ctx.font=thValue(9, true);
      if(r.d != null){ ctx.fillStyle = r.d > 0 ? RM_GOOD : (r.d < 0 ? RM_BAD : TH('textDim'));
        ctx.fillText((r.d > 0 ? '+' : '')+r.d+'%', x+w-10, iy); }
      else if(r.txt){ ctx.fillStyle=TH('textBright'); ctx.fillText(r.txt, x+w-10, iy); }
      ctx.textAlign='left';
      iy += 15;
    }
    if(o.barNote){ ctx.fillStyle=TH('textDim'); ctx.font=thValue(8, false); ctx.fillText(thFit(o.barNote, w-20), x+10, iy); }
    iy += 18;
  }
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(10, false);
  for(const t of (o.lines||[])){ if(iy > y+h-34) break; ctx.fillText(thFit(t, w-20), x+10, iy); iy += 15; }
  if(o.hint){
    const cy = y+h-16;
    ctx.fillStyle=TH('back'); ctx.fillRect(x+6, cy-10, w-12, 22);
    ctx.fillStyle=TH('accent'); ctx.font=thLabel(8);
    ctx.fillText(thFit(o.hint, w-24), x+12, cy);
  }
}

// What the hangar card says about a hull. Bars against the best hull of the
// list, the white mark is the one you fly.
function hangarCard(key){
  const s = shipStats(key), b = shipBanks(key), cur = shipStats(player.ship);
  const list = PLAYER_SHIPS.filter(function(q){ return !cycleTabs() || q.fac === s.fac; });
  const top = function(f){ let m = 0; for(const q of list) m = Math.max(m, f(q)); return m || 1; };
  const bar = function(l, f){ const t = top(f), a = f(s), c = f(cur);
    return {l:l, v:Math.min(1, a/t), cur:Math.min(1, c/t), d:(key !== player.ship && c > 0) ? Math.round((a/c-1)*100) : null}; };
  const gn = primaryCount(key), fit = fitFor(key);
  const facts = [isBomberHull(key) ? 'BOMBER' : 'FIGHTER'];
  if(gn) facts.push(gn+(gn === 1 ? ' GUN' : ' GUNS')+'  -  VOLLEY '+Math.round(volleyTotal(gn)));
  facts.push(b.p.length+(b.p.length === 1 ? ' GUN BANK' : ' GUN BANKS'));
  facts.push(b.s.length+(b.s.length === 1 ? ' MISSILE BANK' : ' MISSILE BANKS'));
  const i = PLAYER_SHIPS.findIndex(function(q){ return q.key === key; });
  let sub = (s.fac||'').toUpperCase(), subCol = null;
  if(key === player.ship){ sub = 'YOU FLY THIS ONE'; subCol = TH('accentWarm'); }
  else if(i >= 0 && !shipIsOpen(i)) sub = 'UNLOCKS AT '+(cycleBase+s.unlock).toLocaleString('en-US')+' POINTS';
  else if(!shipOffered(key)) sub = 'NO '+(s.fac||'').toUpperCase()+' HANGAR ON THE FIELD';
  const pri = fit.p.map(function(k){ return weaponName(priDefP(k)); }).join(' + ');
  const sec = fit.s.map(function(k, n){ return weaponName(secDefP(k))+' '+bankAmmoMax(key, n, k); }).join(', ');
  return {model:key, title:s.name, sub:sub, subCol:subCol, facts:facts,
          barHead:'AGAINST THE BEST HULL HERE', barNote:'white mark and % = your '+(cur.name||''),
          bars:[bar('HULL', function(q){ return q.hp; }), bar('SHIELDS', function(q){ return q.sh; }),
                bar('SPEED', function(q){ return q.spd; }), bar('AGILITY', function(q){ return q.turn; })],
          lines:['Guns: '+pri, 'Racks: '+sec],
          hint: colossusOnField() ? 'COLOSSUS HANGAR OPEN  -  NO REFIT AFTER THE FIRST SWITCH' : 'DIGIT OR CLICK TO SWITCH  -  ONE SWITCH PER WAVE'};
}

// What the support card says. Counts read from the mount data the ships
// fight with; facts, not a role.
function allyCard(id, keyLabel){
  const d = ALLY_DEFS[id], m = (typeof mountsFor === 'function' && mountsFor(d.spr)) || {};
  const beams = m.beams || [], heavy = beams.filter(function(b){ return b.large; }).length, light = beams.length - heavy;
  const guns = (m.primary||[]).length, mis = (m.secondary||[]).length;
  // The Colossus fights as a destroyer, but she is a juggernaut (Silvio).
  const facts = [d.colossus ? 'JUGGERNAUT' : d.cls.toUpperCase(), 'HULL '+allyHull(d)];
  if(light) facts.push(light+' ANTI-FIGHTER '+(light === 1 ? 'BEAM' : 'BEAMS'));
  facts.push(heavy ? heavy+' HEAVY '+(heavy === 1 ? 'BEAM' : 'BEAMS') : 'NO HEAVY BEAMS');
  if(guns) facts.push(guns+(guns === 1 ? ' TURRET' : ' TURRETS'));
  if(mis) facts.push(mis+' MISSILE '+(mis === 1 ? 'LAUNCHER' : 'LAUNCHERS'));
  // what she does for you
  const lines = [];
  if(d.colossus) lines.push(COLOSSUS_TIME+' s on station, then she jumps out');
  if(d.cls === 'destroyer') lines.push('Launches wings  -  her hangar lets you switch ship (V)');
  if(d.cls === 'corvette') lines.push('Rearms you while she is on the field (R)');
  const rk = allyTicket(id);
  lines.push('In hand: '+(tickets[rk]||0)+(canRefine(rk) ? '  -  '+REFINE_COST+' refine into one of the next class' : ''));
  // v195: no hull bar. It repeated the HULL figure of the facts, and every
  // destroyer and the Colossus filled it to the end (Silvio).
  return {model:d.spr, title:allyLabel(d), sub:(CM_FAC_HEAD[d.fac]||'').toUpperCase(), facts:facts,
          bars:[], lines:lines, hint:'KEY '+keyLabel+' OR CLICK TO CALL'};
}

// ── REARM PANEL (v190) ───────────────────────────────────────
// Three columns: the ship and its banks, the weapons the chosen bank may
// carry, and a fixed info panel for the weapon under the pointer (Silvio:
// no tooltips, facts not verdicts, values for your own ship, compared with
// what the bank holds now). Everything is read from the tables the game
// fights with - ARSENAL_P/S, SHIP_BANKS, the energy store - never by hand.
const RM_W        = 700;
const RM_TITLE    = 34;
const RM_H        = 420;
const RM_PAD      = 16;
const RM_C1_W     = 200;    // ship and banks
const RM_C2_W     = 180;    // weapons of the chosen bank
const RM_GAP_COL  = 14;
const RM_PIC_H    = 92;
const RM_BANK_H   = 34;
const RM_ROW_H    = 26;
const RM_ROW_GAP  = 2;
const RM_GOOD     = '#7fe08a';
const RM_BAD      = '#ff7a66';
// DONE button size, and the room a window adds below its list for it (v194).
const DONE_W = 180, DONE_H = 30;
const DONE_ROOM = DONE_H + 14;
// The info card of the hangar and the support window (v192).
const IC_PIC_H   = 112;
const IC_FACT_ROWS = 2;
// Some hulls share a model with another key.
const M3D_ALIAS = {ntfcodeimos:'codeimos', ntfcrfenris:'crfenris', ntfcrleviathan:'crleviathan',
                   ntfcraeolus:'craeolus', deorion:'deorionright', deorionleft:'deorionright',
                   ntfdeorion:'deorionright', ntfdehecate:'dehecate'};
const RM_NOTE_LINES = 2, RM_NOTE_LH = 13, RM_FACT_ROWS = 2;
// Word wrap into at most n lines; the last one is cut with an ellipsis
// only if the text is longer than the space.
function rmWrap(text, maxW, n){
  const words = String(text).split(' '), out = [];
  let line = '';
  for(let i=0;i<words.length;i++){
    const t = line ? line+' '+words[i] : words[i];
    if(ctx.measureText(t).width <= maxW || !line){ line = t; continue; }
    out.push(line); line = words[i];
    if(out.length === n-1){ line = words.slice(i).join(' '); break; }
  }
  if(line) out.push(out.length === n-1 ? thFit(line, maxW) : line);
  return out.slice(0, n);
}
// The bank picked and the weapon the info panel is about.
let rmBank = 'p0', rmShow = null;
// The bars of the info panel, the armour factor each one reads.
const RM_BARS = [
  ['HULL', 'a'], ['SHIELDS', 's'], ['SUBSYSTEMS', 'u']
];

function rmPri(slot){ return slot[0]==='p'; }
function rmDef(key, pri){ return pri ? priDefP(key) : secDefP(key); }
function rmBankKey(slot){
  const i = +slot.slice(1), b = rmPri(slot) ? player.pb : player.sb;
  return (b && b[i]) ? b[i].key : null;
}
// Damage per second of a gun, or of a whole bank of rounds, against one
// kind of target. A bank compares fairly where a round would not: five
// Trebuchets against 160 Tempests (v189 draft).
function rmDps(w, k){
  const f = w.f || {a:1, s:1, u:1};
  return w.dmg*(w.pellets||1)*60/Math.max(1, w.wait||28)*f[k];
}
function rmBankDmg(w, k, slot){
  const f = w.f || {a:1, s:1, u:1};
  const round = w.children ? w.children*(w.childDmg||w.dmg) : w.dmg*(w.swarm||1);
  return round*f[k]*bankAmmoMax(player.ship, +slot.slice(1), w.key);
}
function rmValueOf(w, k, slot){ return rmPri(slot) ? rmDps(w, k) : rmBankDmg(w, k, slot); }
// How far a round gets, in screen widths: the game has no metres on show
// (Silvio, v189 draft).
function rmReach(w, pri){
  const px = (pri && w.range > 0) ? w.range : (w.spd||0)*(w.life||0);
  const s = px / W;
  if(s >= 3) return 'REACH '+Math.round(s)+' SCREENS';
  const r = Math.round(s*10)/10;
  return 'REACH '+r+(r > 1 ? ' SCREENS' : ' SCREEN');
}
// Facts, never verdicts.
function rmFacts(w, pri){
  const f = [], ff = w.f || {a:1, s:1, u:1};
  if(pri){
    f.push((Math.round(600/Math.max(4, w.wait||28))/10)+' SHOTS/S');
    f.push('ENERGY '+(Math.round((w.en||0)*10)/10)+' A SHOT');
    f.push(rmReach(w, true));
    if(w.pellets) f.push(w.pellets+' PELLETS A SHOT');
    if(w.shards) f.push('BURSTS INTO '+w.shards+' SHARDS');
    if(ff.a === 0) f.push('NO HULL DAMAGE');
    else if(ff.s < 0.5) f.push('WEAK ON SHIELDS');
  } else {
    f.push(w.homing==='heat' ? 'SEEKS NEAREST' : (w.homing==='aspect' ? 'LOCKS AT LAUNCH' : 'FLIES STRAIGHT'));
    f.push(rmReach(w, false));
    if((w.fs && w.fs.turn || 1) >= 2) f.push('TURNS SLOWLY');
    if(w.bigFirst) f.push('PREFERS CAPITAL SHIPS');
    if(w.swarm) f.push(w.swarm+' MISSILES A SHOT');
    if(w.children) f.push('PRESS AGAIN: '+w.children+' SEEKERS');
    if(w.subs) f.push('SUBSYSTEMS ONLY');
    if(w.emp) f.push('FIGHTERS NEAR IT STOP FIRING '+Math.round(EMP_T/60)+' S');
    if(w.tag) f.push('MARKS FOR OUR BEAMS');
    if(w.blast) f.push('ITS BLAST HITS YOU TOO');
  }
  return f;
}
// Bars against the strongest weapon this bank may carry; the mark and the
// per cent are the weapon in the bank now.
function rmBars(w, slot){
  const pri = rmPri(slot), cur = rmDef(rmBankKey(slot), pri);
  const all = bankChoices(player.ship, pri);
  return RM_BARS.map(function(r){
    const k = r[1];
    let top = 0;
    for(const q of all) top = Math.max(top, rmValueOf(q, k, slot));
    const a = rmValueOf(w, k, slot), b = rmValueOf(cur, k, slot);
    top = top || 1;
    return {l:r[0], v:Math.min(1, a/top), cur:Math.min(1, b/top),
            d:(b > 0 && w.key !== cur.key) ? Math.round((a/b-1)*100) : null};
  });
}
// What it means on the hull you fly.
function rmShipLines(w, slot){
  if(rmPri(slot)){
    const regen = (player.enRe||0)*60, drain = (w.en||0)*60/Math.max(1, w.wait||28);
    const last = function(d){ return d <= regen ? 'never runs dry' : 'store lasts '+Math.round((player.enMax||0)/(d-regen))+' s'; };
    const out = ['Alone: '+last(drain)];
    const i = +slot.slice(1), o = (player.pb||[])[1-i];
    if(o){ const ow = priDefP(o.key); out.push('Linked with '+weaponName(ow)+': '+last(drain + (ow.en||0)*60/Math.max(1, ow.wait||28))); }
    return out;
  }
  const n = bankAmmoMax(player.ship, +slot.slice(1), w.key);
  const round = w.children ? w.children*(w.childDmg||w.dmg) : w.dmg*(w.swarm||1);
  return [n+(n === 1 ? ' round fits' : ' rounds fit')+' in this bank',
          Math.round(round*(w.f ? w.f.a : 1))+' hull damage a round',
          'Reload '+(Math.round(w.cd/6)/10)+' s between rounds'];
}
function rmSelectBank(slot){
  if(!rmBankKey(slot)) return;
  rmBank = slot; rmShow = null;
}
// Up / down through the weapons of the bank, the way the pointer would.
function rmStep(d){
  const list = bankChoices(player.ship, rmPri(rmBank));
  if(!list.length) return;
  let i = list.findIndex(function(w){ return w.key === (rmShow || rmBankKey(rmBank)); });
  i = (i + d + list.length) % list.length;
  rmShow = list[i].key;
}
function rearmLayout(){
  const mx = ((W-RM_W)/2)|0, my = (HUD_H + (H-HUD_H-RM_H)/2)|0;
  const c1 = mx+RM_PAD, c2 = c1+RM_C1_W+RM_GAP_COL, c3 = c2+RM_C2_W+RM_GAP_COL;
  const banks = [];
  let y = my+180, n = 0;
  (player.pb||[]).forEach(function(b, i){ banks.push({slot:'p'+i, label:'PRIMARY '+(i+1), key:b.key, x:c1, y:y, w:RM_C1_W, h:RM_BANK_H, num:++n}); y += RM_BANK_H+4; });
  (player.sb||[]).forEach(function(b, i){ banks.push({slot:'s'+i, label:'SECONDARY '+(i+1), key:b.key, ammo:b.max, x:c1, y:y, w:RM_C1_W, h:RM_BANK_H, num:++n}); y += RM_BANK_H+4; });
  if(!rmBankKey(rmBank)) rmBank = banks.length ? banks[0].slot : 'p0';
  const pri = rmPri(rmBank), cur = rmBankKey(rmBank);
  const list = [], choices = bankChoices(player.ship, pri);
  // A longer list closes up its rows rather than running into the DONE
  // button (v191, Silvio): today's longest is 10 and still fits as it is.
  const step = Math.min(RM_ROW_H+RM_ROW_GAP, Math.floor((RM_H-58-8-60)/Math.max(1, choices.length)));
  y = my+60;
  for(const w of choices){
    list.push({key:w.key, w:w, open:weaponOpenFor(w, player.ship), cur:w.key===cur,
               x:c2, y:y, wd:RM_C2_W, h:step-RM_ROW_GAP});
    y += step;
  }
  return {mx:mx, my:my, mw:RM_W, mh:RM_H, c1:c1, c2:c2, c3:c3, c3w:mx+RM_W-RM_PAD-c3,
          banks:banks, list:list, pri:pri};
}
function drawRearmShip(x, y, w, h){
  const key = player.ship, img = IMGS[key];
  ctx.fillStyle = TH('back'); ctx.fillRect(x, y, w, h);
  window._rearmShipRect = {x:x, y:y, w:w, h:h};
  // The real model when it is there (v191): it turns while the pointer is
  // on it, the wheel zooms in and brings the finer model. The sprite
  // stands in while it loads and wherever WebGL is missing.
  const hot = hovering(x, y, w, h);
  if(typeof m3dDraw === 'function' && m3dDraw(key, x, y, w, h, m3dView(key, hot))){
    ctx.textAlign='right'; ctx.textBaseline='middle';
    ctx.fillStyle = hot ? TH('accent') : TH('textDim'); ctx.font = thLabel(7);
    ctx.fillText(hot ? 'WHEEL: ZOOM' : 'POINT TO TURN', x+w-6, y+8);
    ctx.textAlign='left';
    return;
  }
  if(!img || !img.width || !img.height) return;
  const sc = Math.min((w-20)/img.width, (h-12)/img.height);
  if(!(sc > 0)) return;
  ctx.save();
  ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  ctx.translate(x+w/2, y+h/2);
  if(spriteFacing(key)==='left') ctx.scale(-1, 1);
  ctx.drawImage(img, -img.width*sc/2, -img.height*sc/2, img.width*sc, img.height*sc);
  ctx.restore();
}
function drawRearmMenu(){
  if(!rearmMenu) return;
  const L = rearmLayout(), mx = L.mx, my = L.my;
  ctx.save();
  thFrame(mx, my, L.mw, L.mh, RM_TITLE);
  window._rearmPanelRect = {x:mx, y:my, w:L.mw, h:L.mh};
  window._rearmRects = [];
  ctx.textBaseline='middle'; ctx.textAlign='left';
  ctx.fillStyle=TH('textBright'); ctx.font=thLabel(14);
  ctx.fillText('REARM', mx+RM_PAD, my+16);
  ctx.textAlign='right'; ctx.fillStyle=TH('accentWarm'); ctx.font=thValue(10, false);
  ctx.fillText('PICK A BANK, THEN A WEAPON  -  A REFIT FILLS EVERY RACK', mx+L.mw-RM_PAD, my+16);
  ctx.textAlign='left';
  const lab = function(t, x, y){ ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8); ctx.fillText(t, x, y); };

  // ── the ship and its banks ──
  lab('YOUR SHIP', L.c1, my+50);
  drawRearmShip(L.c1, my+58, RM_C1_W, RM_PIC_H);
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(12, true);
  ctx.fillText(thFit(shipStats(player.ship).name || player.ship, RM_C1_W), L.c1, my+164);
  for(const b of L.banks){
    const sel = b.slot===rmBank, w = rmDef(b.key, b.slot[0]==='p');
    thButton(b.x, b.y, b.w, b.h, sel ? 'on' : null);
    if(sel){ ctx.fillStyle='rgba('+TH('glow')+',0.30)'; ctx.fillRect(b.x+2, b.y+2, b.w-4, b.h-4); }
    else if(hovering(b.x, b.y, b.w, b.h)) thGlowPath(b.x, b.y, b.w, b.h, 4, 0.45);
    ctx.fillStyle = sel ? TH('accentWarm') : TH('textDim'); ctx.font=thLabel(7);
    ctx.fillText(b.num+'  '+b.label, b.x+8, b.y+10);
    ctx.fillStyle = sel ? TH('textBright') : TH('text'); ctx.font=thValue(11, true);
    ctx.fillText(thFit(weaponName(w), b.w-50), b.x+8, b.y+23);
    if(b.ammo != null){ ctx.textAlign='right'; ctx.fillStyle=TH('text'); ctx.font=thValue(10, true);
      ctx.fillText(String(b.ammo), b.x+b.w-8, b.y+23); ctx.textAlign='left'; }
    window._rearmRects.push({x:b.x, y:b.y, w:b.w, h:b.h, bank:b.slot});
  }

  // ── what this bank may carry ──
  lab((L.pri ? 'PRIMARY ' : 'SECONDARY ')+(+rmBank.slice(1)+1)+'  -  '+L.list.length+' WEAPONS FIT', L.c2, my+50);
  for(const r of L.list) if(hovering(r.x, r.y, r.wd, r.h)) rmShow = r.key;
  if(!rmShow || !L.list.some(function(r){ return r.key===rmShow; })) rmShow = rmBankKey(rmBank);
  for(const r of L.list){
    const show = r.key===rmShow, iy = r.y+r.h/2;
    if(show){ ctx.fillStyle='rgba(255,255,255,0.07)'; ctx.fillRect(r.x, r.y, r.wd, r.h); thGlowPath(r.x, r.y, r.wd, r.h, 3, 0.45); }
    if(r.cur){ ctx.fillStyle='rgba('+TH('glow')+',0.30)'; ctx.fillRect(r.x, r.y, r.wd, r.h); }
    ctx.fillStyle = r.open ? ((r.cur || show) ? TH('textBright') : TH('text')) : TH('textDim');
    ctx.font = thValue(11, r.cur);
    ctx.fillText(thFit(weaponName(r.w), r.wd-90), r.x+8, iy);
    // the info mark: what the panel on the right is about
    ctx.strokeStyle = show ? TH('accentWarm') : TH('textDim'); ctx.lineWidth=1;
    ctx.beginPath(); ctx.arc(r.x+r.wd-12, iy, 6, 0, Math.PI*2); ctx.stroke();
    ctx.fillStyle = show ? TH('accentWarm') : TH('textDim'); ctx.font='bold 9px Georgia, serif';
    ctx.textAlign='center'; ctx.fillText('i', r.x+r.wd-12, iy+0.5);
    ctx.textAlign='right'; ctx.font=thLabel(7);
    if(!r.open){ ctx.fillStyle=TH('textDim');
      ctx.fillText(r.w.fromWave ? 'LATER' : (r.w.unlock||0).toLocaleString('en-US')+' PTS', r.x+r.wd-24, iy); }
    else if(r.cur){ ctx.fillStyle=TH('accentWarm'); ctx.fillText('IN BANK', r.x+r.wd-24, iy); }
    ctx.textAlign='left';
    window._rearmRects.push({x:r.x, y:r.y, w:r.wd, h:r.h, key:r.key, open:r.open});
  }

  // ── the info panel ──
  const w = rmDef(rmShow, L.pri), C3 = L.c3, C3W = L.c3w, top = my+44, ph = RM_H-60;
  thPlate(C3, top, C3W, ph, TH('panelFront'));
  // Fixed areas (v192, Silvio): the note wraps into two lines and the
  // facts into two rows, so nothing below moves while you go through the
  // list.
  let iy = top+16;
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(15, true); ctx.fillText(thFit(weaponName(w), C3W-20), C3+10, iy); iy += 18;
  ctx.fillStyle=TH('text'); ctx.font=thValue(10, false);
  const nl = rmWrap(w.note||'', C3W-20, RM_NOTE_LINES);
  for(let i=0;i<nl.length;i++) ctx.fillText(nl[i], C3+10, iy + i*RM_NOTE_LH);
  iy += RM_NOTE_LINES*RM_NOTE_LH + 8;
  let fx = C3+10, row = 0;
  ctx.font=thLabel(7);
  for(const t of rmFacts(w, L.pri)){
    const tw = ctx.measureText(t).width+12;
    if(fx+tw > C3+C3W-8){ fx = C3+10; row++; }
    if(row >= RM_FACT_ROWS) break;
    ctx.strokeStyle=TH('edgeLight'); ctx.lineWidth=1; ctx.strokeRect(fx+0.5, iy+row*18-7.5, tw, 15);
    ctx.fillStyle=TH('textBright'); ctx.fillText(t, fx+6, iy+row*18); fx += tw+5;
  }
  iy += (RM_FACT_ROWS-1)*18 + 22;
  lab(L.pri ? 'DAMAGE PER SECOND AGAINST' : 'DAMAGE OF A FULL BANK AGAINST', C3+10, iy); iy += 14;
  const bx = C3+92, bw = C3W-150;
  for(const r of rmBars(w, rmBank)){
    ctx.fillStyle=TH('text'); ctx.font=thLabel(8); ctx.fillText(r.l, C3+10, iy);
    ctx.fillStyle=TH('edgeDark'); ctx.fillRect(bx, iy-4, bw, 8);
    // the skin's warm accent, so the white mark of the bank stands out
    // on Fire and on Void alike (Silvio, v189 draft)
    ctx.fillStyle=TH('accentWarm'); ctx.fillRect(bx, iy-4, Math.max(1, bw*r.v), 8);
    ctx.fillStyle=TH('textBright'); ctx.fillRect(bx+bw*r.cur-1, iy-6, 2, 12);
    if(r.d != null){
      ctx.textAlign='right'; ctx.fillStyle = r.d > 0 ? RM_GOOD : (r.d < 0 ? RM_BAD : TH('textDim')); ctx.font=thValue(9, true);
      ctx.fillText((r.d > 0 ? '+' : '')+r.d+'%', C3+C3W-10, iy); ctx.textAlign='left';
    }
    iy += 16;
  }
  ctx.fillStyle=TH('textDim'); ctx.font=thValue(8, false);
  ctx.fillText(thFit('white mark and % = against '+weaponName(rmDef(rmBankKey(rmBank), L.pri))+' in this bank', C3W-20), C3+10, iy); iy += 20;
  lab(thFit('ON YOUR '+(shipStats(player.ship).name || '').toUpperCase(), C3W-20), C3+10, iy); iy += 15;
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(10, false);
  for(const t of rmShipLines(w, rmBank)){ ctx.fillText(thFit(t, C3W-20), C3+10, iy); iy += 15; }
  // the keys that matter in the fight
  const cy = top+ph-16;
  ctx.fillStyle=TH('back'); ctx.fillRect(C3+6, cy-10, C3W-12, 22);
  ctx.fillStyle=TH('accent'); ctx.font=thLabel(8);
  ctx.fillText(L.pri ? ((player.pb||[]).length > 1 ? 'WHEEL UP / Q  -  bank 1, bank 2, linked' : 'ONE PRIMARY BANK')
                     : 'WHEEL DOWN / E  -  next missile bank', C3+12, cy);

  // Close (v191, Silvio): every pick is fitted the moment it is made, so
  // the button says that closing keeps it.
  drawDoneButton(L.c2, my+RM_H-58, RM_C2_W, 'YOUR FIT IS KEPT', window._rearmRects);
  ctx.textAlign='center'; ctx.fillStyle=TH('textDim'); ctx.font=thValue(9, false);
  ctx.fillText('1-'+L.banks.length+' bank  -  UP / DOWN and ENTER weapon  -  every pick is fitted at once  -  '+closeKeys('R', true), mx+L.mw/2, my+L.mh-10);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}
// Three rounds stacked, the way a rack is loaded.
function drawRearmIcon(cx, cy, col){
  ctx.save();
  ctx.fillStyle=col; ctx.strokeStyle=col; ctx.lineWidth=1.2;
  for(let i=-1;i<=1;i++){
    const y = cy + i*4.5;
    ctx.beginPath();
    ctx.moveTo(cx-6, y-1.4);
    ctx.lineTo(cx+3, y-1.4);
    ctx.lineTo(cx+6, y);
    ctx.lineTo(cx+3, y+1.4);
    ctx.lineTo(cx-6, y+1.4);
    ctx.closePath();
    ctx.fill();
  }
  ctx.restore();
}

// ── SUPPORT MENU LAYOUT ──────────────────────────────────────
// Built like the hangar: a fixed panel width, one plate per ship, the figures
// in their places. The width is fixed on purpose. It used to follow the number
// of faction columns, which meant that with a single faction on call the panel
// became narrower than the Colossus line of text that had to sit inside it.
const CM_W        = 780;    // v192: list + card
const CM_LIST_W   = 452;
const CM_MIN_H    = 420;
let cmShow = null;          // the ship the card is about
const CM_PAD      = 12;
const CM_ROW      = 38;
const CM_GAP      = 4;
const CM_HEAD     = 22;
const CM_TITLE    = 34;
const CM_FOOT     = 18;
const CM_GROUPGAP = 12;
const CM_NUM      = 6;    // key chip, measured from the row's left edge
const CM_NUM_W    = 16;
const CM_PIC      = 28;   // picture cell
const CM_PIC_W    = 44;
const CM_NAME     = 78;
const CM_REFINE_W = 46;   // refining keeps its own ground on the right
const CM_TICKET_W = 34;   // and the count in hand sits beside it
// Where everything sits, before anything is drawn. Both the drawing and the
// tap rectangles read this rather than working it out twice.
function callMenuLayout(){
  const COLS = callCols();
  const n    = Math.max(1, COLS.length);
  const colw = ((CM_LIST_W - CM_PAD*(n-1))/n)|0;
  let rows = 1;
  for(const c of COLS) rows = Math.max(rows, c.length);
  const showCol = allyFacOn(ALLY_DEFS[ALLY_SPECIAL].fac);
  let y = CM_TITLE;
  // Room for the fleet tabs under the header.
  const tabs = cycleTabs(), tabY = y;
  if(tabs) y += FLEET_TAB_H + 8;
  const headY = y; y += CM_HEAD;
  const rowY  = y; y += rows*(CM_ROW+CM_GAP);
  let colHeadY = 0, colRowY = 0;
  if(showCol){
    y += CM_GROUPGAP;
    colHeadY = y; y += CM_HEAD;
    colRowY  = y; y += CM_ROW + CM_GAP;
  }
  y += DONE_ROOM + CM_FOOT;
  y = Math.max(y, CM_MIN_H);
  return {mx:((W-CM_W)/2)|0, my:((H-y)/2)|0, mw:CM_W, mh:y,
          COLS:COLS, colw:colw, showCol:showCol, tabs:tabs, tabY:tabY,
          headY:headY, rowY:rowY, colHeadY:colHeadY, colRowY:colRowY};
}
const CM_FAC_HEAD = {terran:'TERRAN FLEET', vasudan:'VASUDAN FLEET', gtva:'JOINT COMMAND'};
// One ship, on its own plate. Same parts and the same order as a hangar row,
// because they are the same kind of object: something you can take, with
// figures that let you decide whether to.
function drawAllyRow(x, y, w, id, d, keyLabel, hot){
  const ok  = allyAffordable(id);
  const rk  = allyTicket(id);
  const ref = canRefine(rk);
  thPlate(x, y, w, CM_ROW,
          (hot && ok) ? TH('raised') : (ok ? TH('panelFront') : TH('back')));
  // The Colossus is the rarest thing in the menu, so she is the one row that
  // carries the active marks.
  if(hot && ok){
    thGlowPath(x, y, w, CM_ROW, 6, 1);
    thBrackets(x, y, w, CM_ROW, TH('accentWarm'));
  } else if(ok && hovering(x, y, w, CM_ROW)) thGlowPath(x, y, w, CM_ROW, 6, 0.5);
  if(hovering(x, y, w, CM_ROW)) cmShow = id;
  drawKeyChip(keyLabel, x+CM_NUM, y+(CM_ROW-16)/2, CM_NUM_W, 16, ok);
  // A narrow column leaves the picture to the card (v192).
  const pic = w >= 300, nameX = pic ? CM_NAME : CM_NUM+CM_NUM_W+8;
  if(pic) drawHullCell(d.spr, x+CM_PIC, y+3, CM_PIC_W, CM_ROW-6, ok);

  // What is left for the name once the count and the refine button have had
  // their share. thFit gets told this number, so nothing can run past it.
  const rightKeep = CM_TICKET_W + (ref ? CM_REFINE_W + 4 : 0) + 8;
  const textW = w - nameX - rightKeep;

  ctx.textAlign='left'; ctx.textBaseline='middle';
  ctx.fillStyle = ok ? TH('textBright') : TH('textDim');
  ctx.font = thValue(13, true);
  ctx.fillText(thFit(allyLabel(d), textW), x+nameX, y+13);

  let sub;
  if(d.colossus)                sub = 'JUGGERNAUT  -  '+COLOSSUS_TIME+' S ON STATION';
  // The hull the ship will really have (v188: FS2 ratio within the class).
  else if(d.cls==='destroyer')  sub = 'DESTROYER  -  HULL '+allyHull(d)+'  -  WINGS';
  else                          sub = d.cls.toUpperCase()+'  -  HULL '+allyHull(d);
  ctx.fillStyle = TH('textDim'); ctx.font = thValue(9, false);
  ctx.fillText(thFit(sub, textW), x+nameX, y+27);

  // How many are in hand, not merely whether one can be afforded.
  ctx.textAlign='right';
  ctx.fillStyle = ok ? TH('accent') : TH('textDim');
  ctx.font = thValue(14, true);
  ctx.fillText((tickets[rk]||0)+'x', x+w-(ref ? CM_REFINE_W+8 : 10), y+CM_ROW/2);
  ctx.textAlign='left';

  // Refining sits on its own generous button. A narrow one against a call
  // button is how a destroyer gets spent by accident.
  if(ref){
    const rx = x+w-CM_REFINE_W-2, ry = y+2, rh = CM_ROW-4;
    thPlate(rx, ry, CM_REFINE_W, rh, TH('panelBack'), 4);
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillStyle = TH('accentWarm'); ctx.font = thValue(13, true);
    ctx.fillText(REFINE_COST+'\u2192', rx+CM_REFINE_W/2, ry+rh/2-5);
    ctx.fillStyle = TH('textDim'); ctx.font = thLabel(7);
    ctx.fillText('REFINE', rx+CM_REFINE_W/2, ry+rh/2+8);
    ctx.textAlign='left';
    window._callRects.push({x:rx, y:ry, w:CM_REFINE_W, h:rh, refine:rk});
    if(ok) window._callRects.push({x:x, y:y, w:w-CM_REFINE_W-4, h:CM_ROW, id:id});
  } else if(ok){
    window._callRects.push({x:x, y:y, w:w, h:CM_ROW, id:id});
  }
}
function drawCallMenu(){
  if(!callMenu) return;
  const L  = callMenuLayout();
  const mx = L.mx, my = L.my;
  ctx.save();
  thFrame(mx, my, L.mw, L.mh, CM_TITLE);
  window._callPanelRect = {x:mx, y:my, w:L.mw, h:L.mh};

  ctx.textBaseline='middle'; ctx.textAlign='left';
  ctx.fillStyle=TH('textBright'); ctx.font=thLabel(14);
  ctx.fillText('REQUEST SUPPORT', mx+CM_PAD, my+16);
  ctx.textAlign='right';
  ctx.fillStyle=TH('textDim'); ctx.font=thValue(10, false);
  ctx.fillText('THREE OF A CLASS REFINE INTO ONE OF THE NEXT', mx+L.mw-CM_PAD, my+16);

  window._callRects=[];
  if(L.tabs)
    drawFleetTabs(mx+CM_PAD, my+L.tabY+2, L.mw-CM_PAD*2, callTab, callTabOpen, window._callRects);
  for(let ci=0;ci<L.COLS.length;ci++){
    const col = L.COLS[ci];
    const cx  = mx + CM_PAD + ci*(L.colw + CM_PAD);
    ctx.textAlign='left';
    ctx.fillStyle=TH('text'); ctx.font=thLabel(11);
    ctx.fillText(CM_FAC_HEAD[col[0].d.fac] || '', cx, my+L.headY+7);
    thScale(cx, my+L.headY+14, L.colw, [CM_PIC, CM_NAME], TH('edgeLight'));
    for(let ri=0;ri<col.length;ri++){
      drawAllyRow(cx, my+L.rowY+ri*(CM_ROW+CM_GAP), L.colw,
                  col[ri].id, col[ri].d, col[ri].key, false);
    }
  }

  if(L.showCol){
    const cd = ALLY_DEFS[ALLY_SPECIAL];
    if(!cmShow) cmShow = ALLY_SPECIAL;
    const cx = mx + CM_PAD, cw = CM_LIST_W;
    ctx.textAlign='left';
    ctx.fillStyle=TH('text'); ctx.font=thLabel(11);
    ctx.fillText(CM_FAC_HEAD.gtva, cx, my+L.colHeadY+7);
    thScale(cx, my+L.colHeadY+14, cw, [CM_PIC, CM_NAME], TH('edgeLight'));
    drawAllyRow(cx, my+L.colRowY, cw, ALLY_SPECIAL, cd, ALLY_SPECIAL_KEY, true);
  }

  // The card: the ship under the pointer, else the first in the list (v192).
  let keyOf = null;
  for(const col of L.COLS) for(const r of col){ if(!cmShow) cmShow = r.id; if(r.id === cmShow) keyOf = r.key; }
  if(cmShow === ALLY_SPECIAL) keyOf = ALLY_SPECIAL_KEY;
  if(cmShow && ALLY_DEFS[cmShow]){
    const cx = mx+CM_PAD+CM_LIST_W+12, cy0 = my+CM_TITLE+(L.tabs ? FLEET_TAB_H+8 : 0)+4;
    drawInfoCard(cx, cy0, mx+L.mw-CM_PAD-cx, my+L.mh-26-cy0, allyCard(cmShow, keyOf || '?'));
  }
  drawDoneButton(mx+CM_PAD+((CM_LIST_W-DONE_W)/2|0), my+L.mh-26-DONE_H, DONE_W,
                 'NOTHING IS CALLED', window._callRects);

  ctx.textAlign='center'; ctx.fillStyle=TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText('KEY OR CLICK CALLS  -  '+closeKeys('C'), mx+L.mw/2, my+L.mh-11);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}


function setCallMenu(open){
  if(!open && callMenu) holdResume();
  callMenu = open;
  if(open){ shipMenu = false; cmShow = null; }
  syncPause();
  if(!open && GS==='playing'){ MOUSE.x = player.x; MOUSE.y = player.y; }
  syncCursor();
}

function toggleCallMenu(){
  if(callMenu){ setCallMenu(false); return; }
  if(empOut>0) return;              // the storm has the radio
  if(subspaceOn()) return;          // nothing answers in subspace (Silvio)
  if(waveNoSupport) return;         // nor beyond the second portal (v178)
  if(!allyReady()) return;
  if(cycleTabs()) callTab = pickTab(callTabOpen, callTab);
  setCallMenu(true);
}

// Shared handling for mouse and touch. Returns true when the
// pointer was handled and the caller should stop.
// A panel outline, as reported by whatever drew it last. Anything landing
// on it belongs to that panel, whether or not it hit something usable.
function insidePanel(r, p){
  return !!r && p.x>=r.x && p.x<=r.x+r.w && p.y>=r.y && p.y<=r.y+r.h;
}
function pointerConsumed(p){
  // The tap that puts you back in the fight is spent on that and nothing
  // else - it must not also fire, steer or open a panel.
  if(clearResumeHold()) return true;
  if(GS!=='playing') return false;
  if(rearmMenu){
    for(const r of (window._rearmRects||[]))
      if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){
        if(r.close){ setRearmMenu(false); return true; }
        if(r.bank) rmSelectBank(r.bank);
        else if(r.key){ rmShow = r.key; if(r.open) fitWeapon(rmBank, r.key); }
        return true; }
    if(insidePanel(window._rearmPanelRect, p)) return true;
    setRearmMenu(false); return true;
  }
  if(shipMenu){
    for(const r of (window._shipRects||[]))
      if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){
        if(r.close){ setShipMenu(false); return true; }
        if(r.tab){ hangarTab = r.tab; return true; }
        if(r.key) swapShip(r.key); return true; }
    // Inside the panel but on no row: the header, a group heading, a gap
    // between rows or the footer. That is still the panel, so it swallows
    // the click. Only outside the outline does the panel close.
    if(insidePanel(window._shipPanelRect, p)) return true;
    setShipMenu(false); return true;
  }
  var rsw=window._shipBtnRect;
  if(rsw&&p.x>=rsw.x&&p.x<=rsw.x+rsw.w&&p.y>=rsw.y&&p.y<=rsw.y+rsw.h){ toggleShipMenu(); return true; }
  // The rearm button sits beside it and was drawn without ever being
  // asked about here, so it lit up and did nothing.
  var rrm=window._rearmBtnRect;
  if(rrm&&p.x>=rrm.x&&p.x<=rrm.x+rrm.w&&p.y>=rrm.y&&p.y<=rrm.y+rrm.h){ toggleRearmMenu(); return true; }
  if(callMenu){
    if(window._callRects){
      for(var ci=0;ci<window._callRects.length;ci++){
        var cr=window._callRects[ci];
        if(p.x>=cr.x&&p.x<=cr.x+cr.w&&p.y>=cr.y&&p.y<=cr.y+cr.h){
          // The menu stays open after refining, so several can be done in
          // a row without reopening it each time.
          if(cr.close){ setCallMenu(false); return true; }
          if(cr.refine){ refineTicket(cr.refine); return true; }
          if(cr.tab){ callTab = cr.tab; return true; }
          callAlly(cr.id); return true;
        }
      }
    }
    if(insidePanel(window._callPanelRect, p)) return true;
    setCallMenu(false); return true;
  }
  var ra=window._allyBtnRect;
  if(ra&&p.x>=ra.x&&p.x<=ra.x+ra.w&&p.y>=ra.y&&p.y<=ra.y+ra.h){ toggleCallMenu(); return true; }
  // The banks in the bar (v186): the primary panel steps the mode, a
  // secondary row that is not chosen gets chosen. The chosen row fires
  // (the old SEC button, _secBtnRect).
  var rp=window._priRect;
  if(rp&&p.x>=rp.x&&p.x<=rp.x+rp.w&&p.y>=rp.y&&p.y<=rp.y+rp.h){ cyclePrimary(); return true; }
  for(const sr of (window._secRows||[])){
    if(sr.i!==player.sSel && p.x>=sr.x&&p.x<=sr.x+sr.w&&p.y>=sr.y&&p.y<=sr.y+sr.h){
      player.sSel=sr.i; syncLegacyWeapons(); return true; }
  }
  return false;
}





// From the title a run starts; from a finished run you go back to the
// title first. Reading your score and then being dropped into the next
// wave in the same breath left no moment to stop.
function toTitleOrLaunch(){
  NOTICES = [];
  if(GS==='gameover'){ enterTitle(); return; }
  launchGame();
}
// A fresh sky every time the title comes up: another backdrop, another
// set of bodies.
function enterTitle(){
  GS='title'; sndAllOff();
  resumeHold=false; userPaused=false; paused=false;
  nebCur = NEB_NAMES[(Math.random()*NEB_NAMES.length)|0];
  nebFading = false; nebAlpha = 1.0;
  rollBodies();
}
// Full screen from the title. The settings panel has the same switch, but
// it only opens during a run, and on a PC the full screen is wanted
// before the first wave, not after it. Built from the kit like the
// buttons in the bar: lit while pointed at, nothing otherwise.
const TFS_W = 136, TFS_H = 26, TFS_PAD = 14;
function titleFsRect(){
  if(!fullscreenAvailable()) return null;
  return {x:W-TFS_W-TFS_PAD, y:TFS_PAD, w:TFS_W, h:TFS_H};
}
function drawTitleFullscreen(){
  const r = titleFsRect();
  window._titleFsRect = r;
  const ms = TFS_H;
  const mx = r ? r.x - 8 - ms : W - TFS_PAD - ms;
  drawMuteButton(mx, TFS_PAD, ms, ms);
  if(!r) return;
  const hv = hovering(r.x, r.y, r.w, r.h);
  const st = btnState(true, false, hv);
  thButton(r.x, r.y, r.w, r.h, st);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillStyle = btnText(st);
  ctx.font = thLabel(11);
  ctx.fillText(thFit(isFullscreen() ? 'EXIT FULLSCREEN' : 'FULLSCREEN', r.w-16),
               r.x+r.w/2, r.y+r.h/2+1);
}
// A click on the button switches full screen and does nothing else - it
// must not also start the run the rest of the title starts.
function titleFsHit(p){
  if(GS!=='title') return false;
  const r = window._titleFsRect;
  return !!r && p.x>=r.x && p.x<=r.x+r.w && p.y>=r.y && p.y<=r.y+r.h;
}
function drawTitle(){
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
  // rather than as more title. The whole list, in two columns, and where to
  // find it again during a run (v185, Silvio).
  const half = Math.ceil(CONTROLS.length/2), rowH = 15;
  const bw = 600, bh = half*rowH + 46, bx = (W-bw)/2, by = H-70-bh;
  thPlate(bx, by, bw, bh, thRGBA('panelBack', 0.72));
  ctx.textAlign='left'; ctx.textBaseline='middle';
  ctx.fillStyle = TH('textDim'); ctx.font = thLabel(9);
  ctx.fillText('CONTROLS', bx+16, by+12);
  const all = CONTROLS;
  for(let c=0;c<2;c++){
    const part = all.slice(c*half, (c+1)*half);
    for(let i=0;i<part.length;i++){
      const ry = by+24+i*rowH, cx0 = bx+16+c*(bw/2);
      ctx.fillStyle = TH('accentWarm'); ctx.font = thLabel(10);
      ctx.fillText(thFit(part[i][0], 128), cx0, ry+rowH/2);
      ctx.fillStyle = TH('text'); ctx.font = thValue(11, false);
      ctx.fillText(thFit(part[i][1], bw/2-150), cx0+134, ry+rowH/2);
    }
  }
  ctx.textAlign='center';
  ctx.fillStyle = TH('textDim'); ctx.font = thValue(10, false);
  ctx.fillText('also in the game: S - SETTINGS - CONTROLS', W/2, by+bh-9);

  // The one thing to do. It pulses rather than blinks: a blink says hurry.
  const k = 0.55 + 0.45*Math.sin(fc*0.05);
  ctx.save();
  ctx.globalAlpha = k;
  ctx.fillStyle = TH('textBright'); ctx.font = thLabel(13);
  ctx.fillText('PRESS SPACE OR ENTER', W/2, H-44);
  ctx.restore();

  drawTitleFullscreen();
  ctx.textAlign='left'; ctx.textBaseline='top';
}


// Shown at the end as well, since that is the number a ranking would use.
function drawGO(){
  // A panel like every other panel, and the figures read as a list: label on
  // the left, value on the right, a hairline between. The run is over, so
  // there is nothing to do here but read it and decide to go again.
  const PW = 380, PH = 252;
  const px = ((W-PW)/2)|0, py = ((H-PH)/2)|0;
  thFrame(px, py, PW, PH, 54);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.save();
  ctx.shadowColor = 'rgba('+TH('glow')+',0.60)'; ctx.shadowBlur = 20;
  ctx.fillStyle = TH('textBright'); ctx.font = thLabel(30);
  ctx.fillText('GAME OVER', px+PW/2, py+28);
  ctx.restore();

  const rows = [['SCORE', String(score).padStart(7,'0')],
                ['WAVE',  String(wave).padStart(3,'0')],
                ['TIME',  fmtTime(runTime)]];
  for(let i=0;i<rows.length;i++){
    const ry = py+82+i*38;
    ctx.textAlign='left';
    ctx.fillStyle = TH('textDim'); ctx.font = thLabel(9);
    ctx.fillText(rows[i][0], px+30, ry);
    ctx.textAlign='right';
    ctx.fillStyle = TH('textBright'); ctx.font = thValue(21, false);
    ctx.fillText(rows[i][1], px+PW-30, ry);
    if(i < rows.length-1){
      ctx.strokeStyle = TH('edgeDark'); ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(px+30, ry+19.5); ctx.lineTo(px+PW-30, ry+19.5);
      ctx.stroke();
    }
  }

  // The one thing that can be done, as a button rather than a blinking line
  // of text. The ring is what pulses; the button itself stays put.
  const bw = 250, bh = 32;
  const bx = px+((PW-bw)/2|0), by = py+PH-50;
  thButton(bx, by, bw, bh, (fc%60<42) ? 'on' : 'ready');
  ctx.textAlign='center';
  ctx.fillStyle = TH('textBright'); ctx.font = thLabel(11);
  ctx.fillText('SPACE / ENTER  -  TRY AGAIN', bx+bw/2, by+bh/2+1);

  ctx.textAlign='left'; ctx.textBaseline='top';
}


// ── TOUCH & MAUS STEUERUNG ───────────────────────────────────
var isFiring = false;

function toGC(clientX, clientY) {
  var r = CVS.getBoundingClientRect();
  return { x:(clientX-r.left)*(W/r.width), y:(clientY-r.top)*(H/r.height) };
}


// Maus
CVS.addEventListener('mousedown',function(ev){
  // Middle button: subsystem marks on / off. preventDefault keeps the
  // browser from starting its scroll mode on the same press.
  if(ev.button===1){ ev.preventDefault(); toggleSubMarks(); return; }
  if(ev.button===0 && muteHit(toGC(ev.clientX,ev.clientY))){ sndToggleMute(); return; }
  if(ev.button===0 && titleFsHit(toGC(ev.clientX,ev.clientY))){ toggleFullscreen(); return; }
  if(ev.button===0&&GS==='playing'){
    var p=toGC(ev.clientX,ev.clientY);
    if(pointerConsumed(p)) return;
    // The settings panel eats the tap before anything else can react to it,
    // or opening it would also fire a weapon underneath.
    if(settingsOpen){ settingsClick(p.x,p.y); return; }
    if(window._settingsBtnRect){var rs=window._settingsBtnRect;if(p.x>=rs.x&&p.x<=rs.x+rs.w&&p.y>=rs.y&&p.y<=rs.y+rs.h){setSettings(true);return;}}
    if(window._pauseBtnRect){var r=window._pauseBtnRect;if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){userPaused=!userPaused;syncPause();return;}}
    if(window._secBtnRect){var r2=window._secBtnRect;if(p.x>=r2.x&&p.x<=r2.x+r2.w&&p.y>=r2.y&&p.y<=r2.y+r2.h){SEC_HOLD.btn=true;fireSecondary();return;}}
    if(p.y<HUD_H) return; // HUD area, no movement input
  }
  if(ev.button!==0&&ev.button!==2) return;
  var p=toGC(ev.clientX,ev.clientY);
  MOUSE.x=p.x; MOUSE.y=p.y;
  if(ev.button===0){
    isFiring=true; MOUSE.down=true;
    if(GS==='title'||GS==='gameover'){ if(GS==='title'||performance.now()-gameOverAt>1500) toTitleOrLaunch(); }
  }
  if(ev.button===2&&GS==='playing'){ SEC_HOLD.rmb=true; fireSecondary(); }
});
// The wheel (v186, Silvio): up steps the primary banks (1, 2, linked),
// down the secondary bank. A trackpad sends a stream of small steps, so
// one change per 160 ms.
let wheelT = 0;
CVS.addEventListener('wheel',function(ev){
  // Over the ship in the rearm window the wheel zooms the model (v191).
  if(GS==='playing' && rearmMenu){
    ev.preventDefault();
    const r = window._rearmShipRect, p = toGC(ev.clientX, ev.clientY);
    if(r && ev.deltaY && p.x>=r.x && p.x<=r.x+r.w && p.y>=r.y && p.y<=r.y+r.h && typeof m3dWheel === 'function') m3dWheel(ev.deltaY);
    return;
  }
  // Over the card of the hangar or the support window it zooms too (v192).
  if(GS==='playing' && (shipMenu || callMenu)){
    ev.preventDefault();
    const r = window._infoPicRect, p = toGC(ev.clientX, ev.clientY);
    if(r && ev.deltaY && p.x>=r.x && p.x<=r.x+r.w && p.y>=r.y && p.y<=r.y+r.h && typeof m3dWheel === 'function') m3dWheel(ev.deltaY);
    return;
  }
  if(GS!=='playing' || callMenu || shipMenu || rearmMenu || settingsOpen) return;
  ev.preventDefault();
  const now = performance.now();
  if(now - wheelT < 160 || !ev.deltaY) return;
  wheelT = now;
  if(ev.deltaY < 0) cyclePrimary(); else cycleSecondary();
},{passive:false});
// Linux pastes on a middle click; nothing to paste into here.
CVS.addEventListener('auxclick',function(ev){ if(ev.button===1) ev.preventDefault(); });
CVS.addEventListener('mouseup',function(ev){
  if(ev.button===0){isFiring=false;MOUSE.down=false;SEC_HOLD.btn=false;}
  if(ev.button===2) SEC_HOLD.rmb=false;
});
// A button let go outside the canvas never reports back here.
window.addEventListener('mouseup',function(ev){
  if(ev.button===0) SEC_HOLD.btn=false;
  if(ev.button===2) SEC_HOLD.rmb=false;
});
window.addEventListener('blur',function(){ SEC_HOLD.rmb=false; SEC_HOLD.btn=false; });
CVS.addEventListener('mousemove',function(ev){
  var p=toGC(ev.clientX,ev.clientY);
  // The bar always knows where the pointer is, even where the ship may not
  // follow it.
  HOVER.x=p.x; HOVER.y=p.y;
  syncCursor();
  // touchmove hatte diesen Schutz, mousemove nicht.
  if(p.y<HUD_H&&GS==='playing') return;   // Leiste: keine Steuereingabe
  MOUSE.x=p.x; MOUSE.y=p.y;
});
// Off the canvas: nothing is hovered, and the pointer is the browser's
// business again.
CVS.addEventListener('mouseleave',function(){
  HOVER.x=-1; HOVER.y=-1;
  document.body.classList.remove('nocursor');
});
CVS.addEventListener('contextmenu',function(ev){ev.preventDefault();});

// Touch
CVS.addEventListener('touchstart',function(ev){
  ev.preventDefault();
  if(!ev.touches.length) return;
  var t=ev.touches[0];
  var p=toGC(t.clientX,t.clientY);
  if(muteHit(p)){ sndToggleMute(); return; }
  if(titleFsHit(p)){ toggleFullscreen(); return; }
  if(pointerConsumed(p)) return;
  // HUD area: button check only, no movement input
  if(p.y<HUD_H&&GS==='playing'){
    // The settings panel eats the tap before anything else can react to it,
    // or opening it would also fire a weapon underneath.
    if(settingsOpen){ settingsClick(p.x,p.y); return; }
    if(window._settingsBtnRect){var rs=window._settingsBtnRect;if(p.x>=rs.x&&p.x<=rs.x+rs.w&&p.y>=rs.y&&p.y<=rs.y+rs.h){setSettings(true);return;}}
    if(window._pauseBtnRect){var r=window._pauseBtnRect;if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){userPaused=!userPaused;syncPause();return;}}
    if(window._secBtnRect){var r2=window._secBtnRect;if(p.x>=r2.x&&p.x<=r2.x+r2.w&&p.y>=r2.y&&p.y<=r2.y+r2.h){SEC_HOLD.btn=true;fireSecondary();return;}}
    return; // sonstiger HUD-Touch → ignorieren
  }
  MOUSE.x=p.x; MOUSE.y=p.y;
  isFiring=true; MOUSE.down=true;
  if(GS==='title'||GS==='gameover'){ if(GS==='title'||performance.now()-gameOverAt>1500) toTitleOrLaunch(); }
  // Pause-Button Tap
  if(GS==='playing'){
    // The settings panel eats the tap before anything else can react to it,
    // or opening it would also fire a weapon underneath.
    if(settingsOpen){ settingsClick(p.x,p.y); return; }
    if(window._settingsBtnRect){var rs=window._settingsBtnRect;if(p.x>=rs.x&&p.x<=rs.x+rs.w&&p.y>=rs.y&&p.y<=rs.y+rs.h){setSettings(true);return;}}
    if(window._pauseBtnRect){var r=window._pauseBtnRect;if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){userPaused=!userPaused;syncPause();return;}}
    if(window._secBtnRect){var r2=window._secBtnRect;if(p.x>=r2.x&&p.x<=r2.x+r2.w&&p.y>=r2.y&&p.y<=r2.y+r2.h){SEC_HOLD.btn=true;fireSecondary();return;}}
    // Tapping the field resumes, but only from a pause the player set;
    // a panel keeps its own hold.
    if(userPaused){ userPaused=false; syncPause(); }
  }
},{passive:false});

CVS.addEventListener('touchmove',function(ev){
  ev.preventDefault();
  if(!ev.touches.length) return;
  var t=ev.touches[0];
  var p=toGC(t.clientX,t.clientY);
  if(callMenu||shipMenu) return;
  if(p.y<HUD_H&&GS==='playing') return; // HUD area, no movement input
  MOUSE.x=p.x; MOUSE.y=p.y;
  isFiring=true; MOUSE.down=true;
},{passive:false});

CVS.addEventListener('touchend',function(ev){
  ev.preventDefault();
  isFiring=false; MOUSE.down=false;
  // The SEC button stays held only while a finger is still on it.
  SEC_HOLD.btn=false;
  var r2=window._secBtnRect;
  if(r2) for(var i=0;i<ev.touches.length;i++){
    var q=toGC(ev.touches[i].clientX,ev.touches[i].clientY);
    if(q.x>=r2.x&&q.x<=r2.x+r2.w&&q.y>=r2.y&&q.y<=r2.y+r2.h){ SEC_HOLD.btn=true; break; }
  }
},{passive:false});

function secBtnDown(ev){if(ev)ev.preventDefault();if(GS==='playing'){SEC_HOLD.btn=true;fireSecondary();}}
function secBtnUp(ev){if(ev)ev.preventDefault();SEC_HOLD.btn=false;}
window.secBtnDown=secBtnDown; window.secBtnUp=secBtnUp;

function updateSecBtn(){
  var btn=document.getElementById('secBtn');
  if(btn) btn.style.display='none'; // now on canvas
  if(GS!=='playing') return;
  btn.style.alignItems='center'; btn.style.justifyContent='center';
  var rdy=player.secTimer===0&&player.secAmmo>0;
  btn.style.opacity=rdy?'1':'0.4';
  btn.style.background=rdy?(player.secType==='missile'?'rgba(180,60,0,0.9)':'rgba(120,0,0,0.9)'):'rgba(50,50,50,0.7)';
}

// Keyboard
document.addEventListener('keydown',function(ev){
  K[ev.code]=true;
  // M: all sound off or on, anywhere.
  if(ev.code==='KeyM'){ sndToggleMute(); ev.preventDefault(); return; }
  // S opens and closes the panel, Escape closes it before it reaches pause.
  if(ev.code==='KeyS' && !callMenu && !shipMenu && GS==='playing'){
    setSettings(!settingsOpen); ev.preventDefault(); return;
  }
  if(settingsOpen && ev.code==='Escape'){ setSettings(false); ev.preventDefault(); return; }
  if(ev.code==='KeyF' && (GS==='playing'||GS==='title'||GS==='gameover')){
    toggleFullscreen(); ev.preventDefault(); return;
  }
  // v194: ESC that closes a window only closes it. It used to switch the
  // pause on as well, so the game stayed PAUSED after the resume tap.
  const escMenu = ev.code==='Escape' && (callMenu || shipMenu || rearmMenu);
  if((ev.code==='KeyP'||(ev.code==='Escape' && !escMenu))&&GS==='playing'){
    userPaused=!userPaused; syncPause(); ev.preventDefault();
  }
  if((GS==='title'||GS==='gameover')&&(ev.code==='Space'||ev.code==='Enter')){ if(GS==='title'||performance.now()-gameOverAt>1500) toTitleOrLaunch(); }
});
document.addEventListener('keyup',function(ev){K[ev.code]=false;});

// Request support
document.addEventListener('keydown',function(ev){
  if(GS!=='playing') return;
  if(resumeHold){ clearResumeHold(); ev.preventDefault(); return; }
  if(ev.code==='KeyV'){ toggleShipMenu(); ev.preventDefault(); return; }
  // v194: in the support window R is a call key (the sixth Vasudan row),
  // not the rearm window.
  if(ev.code==='KeyR' && !callMenu){ toggleRearmMenu(); ev.preventDefault(); return; }
  // Q / E: the same as the wheel (v186).
  if(!callMenu && !shipMenu && !rearmMenu){
    if(ev.code==='KeyQ'){ cyclePrimary(); ev.preventDefault(); return; }
    if(ev.code==='KeyE'){ cycleSecondary(); ev.preventDefault(); return; }
  }
  if(rearmMenu){
    if(ev.code==='Escape'){ setRearmMenu(false); ev.preventDefault(); return; }
    var rd = ev.code.indexOf('Digit')===0 ? ev.code.slice(5)
           : (ev.code.indexOf('Numpad')===0 ? ev.code.slice(6) : '');
    var ri = parseInt(rd,10);
    // The digit beside a bank picks it; up and down walk its weapons and
    // Enter fits the one shown (v190).
    if(ri>=1){
      for(const q of rearmLayout().banks)
        if(q.num===ri){ rmSelectBank(q.slot); break; }
      ev.preventDefault();
    }
    if(ev.code==='ArrowUp'||ev.code==='ArrowDown'){ rmStep(ev.code==='ArrowUp' ? -1 : 1); ev.preventDefault(); }
    if(ev.code==='Enter'||ev.code==='NumpadEnter'){ fitWeapon(rmBank, rmShow || rmBankKey(rmBank)); ev.preventDefault(); }
    return;
  }
  if(shipMenu){
    if(ev.code==='Escape'){ setShipMenu(false); ev.preventDefault(); return; }
    if(cycleTabs() && (ev.code==='Tab'||ev.code==='ArrowLeft'||ev.code==='ArrowRight')){
      hangarTab = nextTab(hangarTab, hangarTabOpen); ev.preventDefault(); return; }
    var sd = ev.code.indexOf('Digit')===0 ? ev.code.slice(5) : (ev.code.indexOf('Numpad')===0 ? ev.code.slice(6) : '');
    var si = parseInt(sd,10);
    // The same order the panel shows, so the digit beside a hull is the
    // digit that takes it.
    var ord = hangarOrder();
    if(si>=1 && si<=ord.length){ swapShip(PLAYER_SHIPS[ord[si-1]].key); ev.preventDefault(); }
    return;
  }
  if(ev.code==='KeyC'){ toggleCallMenu(); ev.preventDefault(); return; }
  if(ev.code==='Escape' && callMenu){ setCallMenu(false); ev.preventDefault(); return; }
  if(callMenu && cycleTabs() && (ev.code==='Tab'||ev.code==='ArrowLeft'||ev.code==='ArrowRight')){
    callTab = nextTab(callTab, callTabOpen); ev.preventDefault(); return; }
  if(callMenu){
    // Eleven entries no longer fit on the number row alone, so the second
    // column sits on the keys directly above it.
    var ch='';
    if(ev.code.indexOf('Digit')===0)  ch=ev.code.slice(5);
    else if(ev.code.indexOf('Numpad')===0) ch=ev.code.slice(6);
    else if(ev.code.indexOf('Key')===0)    ch=ev.code.slice(3);
    if(ch===ALLY_SPECIAL_KEY){ callAlly(ALLY_SPECIAL); ev.preventDefault(); return; }
    const ki=ALLY_KEYS.indexOf(ch);
    if(ki>=0){ callAlly(ALLY_ORDER[ki]); ev.preventDefault(); }
  }
});


let lastErr='';

// ── FIXED TIME STEP ───────────────────────────────────────────
// update() counts in whole frames. Without a cap the game runs on a
// 144 Hz display runs 2.4x faster than on 60 Hz, so the simulation is
// pinned to a fixed step rate, while drawing still happens as often
// as the display allows.
// Game speed. Every velocity, fire rate and beam timing in the game
// count in whole simulation steps, so TICK_HZ is the single dial for
// overall pace. 100 tested best.
// build_game.py can override this value with --hz.
const TICK_HZ = 100;
const TICK_MS = 1000/TICK_HZ;
const MAX_CATCHUP = 6;     // catch up at most 6 steps per frame
let _acc = 0, _prev = 0;

function stepUpdate(){
  try{update();}
  catch(e){if(e.message!==lastErr){console.error('Update error:',e);lastErr=e.message;}}
}

(function loop(now){
  requestAnimationFrame(loop);
  try{ musicTick(); }catch(ex){}
  if(typeof now !== 'number') now = (typeof performance !== 'undefined' ? performance.now() : Date.now());
  if(!_prev){ _prev = now; stepUpdate(); }
  else {
    let dt = now - _prev;
    _prev = now;
    // After a tab switch or sleep, do not catch up for minutes
    if(dt > 250) dt = TICK_MS;
    _acc += dt;
    let steps = 0;
    while(_acc >= TICK_MS && steps < MAX_CATCHUP){
      stepUpdate();
      _acc -= TICK_MS;
      steps++;
    }
    if(steps >= MAX_CATCHUP) _acc = 0;
  }
  try{draw();}catch(e){if(e.message!==lastErr){console.error('Draw error:',e);lastErr=e.message;}}
  try{drawCallMenu();}catch(e){}
  try{drawShipMenu();}catch(e){}
  try{drawRearmMenu();}catch(e){}
  try{ if(typeof m3dEndFrame === 'function') m3dEndFrame(); }catch(e){}
  try{drawResumeHint();}catch(e){}
  try{drawCtxNotice();}catch(e){}
})();

// ── PRACTICE LOG ─────────────────────────────────────────────
// One record per wave of the run: points won and lost, objectives, deaths
// and what caused them, tickets in and out, pickups, damage by source,
// kills, losses, weapons and a timeline. Recorded in every run, shown only
// in practice mode - at the end of each wave as a card, and as a table in
// the settings, from where it can be copied or saved for balancing.
let PLOG = [], PL = null;
let plogOpen = false, plogSel = -1, plogTop = 0, plogMsg = '', plogMsgT = 0;
const PLOG_ROWS = 10;
const PLOG_STAT_KEYS = ['shots','hits','killFighter','killBomber','killCruiser','killCorvette',
  'killDestroyer','killBoss','killSentry','killFreighter','killContainer','killAsteroid',
  'subsKilled','bombsShot','scans','escortsCalled'];

function plogTime(steps){
  const s = Math.floor((steps||0)/TICK_HZ);
  return Math.floor(s/60)+':'+String(s%60).padStart(2,'0');
}
function plogName(e){
  if(!e) return '';
  if(e===player) return 'you';
  return String(e.label || (typeof shipName==='function' ? shipName(e.img, e.type||'') : e.type) || '').toUpperCase();
}
function plogEvent(txt, tone){
  if(!PL) return;
  PL.events.push({t:PL.t, txt:txt, tone:tone||'info'});
}
function plogSync(){
  if(!PL) return;
  PL._score = score; PL._lives = lives;
  PL._tickets = Object.assign({}, tickets);
  PL._hp = player.hp; PL._sh = player.sh;
}
// A new wave: the previous one is closed first.
function plogStart(){
  plogEnd();
  const def = (!FS1_MODE && !TEST_MODE && SCRIPT_WAVES[wave]) ? SCRIPT_WAVES[wave] : null;
  PL = {wave:wave, name:def ? def.name : (waveTitle || 'random wave'), scripted:!!def,
        fac:currentFaction, ship:player.ship, t:0, tEnd:null,
        gain:0, loss:0, cards:[], deaths:[], tGot:{}, tUsed:{}, picked:{},
        hull:0, shield:0, dmgBy:{}, stats0:Object.assign({}, STATS), stats:{},
        secFired:0, rearms:0, bolts:0, hits:0, allyLost:0, capLost:[], saved:0, lost:0, escaped:0,
        calls:[], refined:[],
        events:[], src:null, who:''};
  PL._card = objCard;
  plogSync();
}
function plogEnd(){
  if(!PL) return;
  plogFinish(PL);
  PLOG.push(PL);
  PL = null;
}
// The numbers that are read off the game at the end rather than counted.
function plogFinish(r){
  for(const k of PLOG_STAT_KEYS) r.stats[k] = (STATS[k]||0) - (r.stats0[k]||0);
  r.saved = protSaved; r.lost = protLost;
  r.escaped = (escGone||0) + (fleeEscaped||0);
}
// Where the next damage to the player comes from.
function plogSrc(src, who){
  if(!PL) return;
  PL.src = src; PL.who = who ? plogName(who) : '';
}
function plogLoss(why, who){
  if(!PL) return;
  PL._lossWhy = why + (who ? ' - '+plogName(who) : '');
}
function plogKill(e){
  if(!PL || !e) return;
  if(e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||e.type==='boss'||e.type==='station')
    plogEvent(plogName(e)+' destroyed (+'+(e.pts||0)+')', 'good');
}
function plogAllyLost(a){
  if(!PL || !a) return;
  PL.allyLost++;
  if(!a.small){ PL.capLost.push(plogName(a)); plogEvent(plogName(a)+' lost', 'bad'); }
}
// full: the pickup changed nothing (lives already at their maximum).
function plogPick(kind, full){
  if(!PL) return;
  if(kind==='repair'){ PL.picked.repair = (PL.picked.repair||0) + 1; plogEvent('repair picked up', 'good'); }
  if(kind==='life'){
    PL.picked.life = (PL.picked.life||0) + 1;
    if(full) PL.picked.lifeFull = (PL.picked.lifeFull||0) + 1;
    plogEvent(full ? 'life picked up (already at maximum)' : 'life picked up', 'good');
  }
}
// A support call, with what it cost.
function plogCall(a, kind){
  if(!PL || !a) return;
  PL.calls.push(plogName(a));
  PL.tUsed[kind] = (PL.tUsed[kind]||0) + 1;
  plogEvent('called '+plogName(a)+' (-1 '+kind+' ticket)', 'info');
  PL._tickets = Object.assign({}, tickets);
}
// Tickets turned into a bigger one: neither used nor earned.
function plogRefine(kind, n, up){
  if(!PL) return;
  PL.refined.push(n+' '+kind+' -> 1 '+up);
  plogEvent('refined '+n+' '+kind+' -> 1 '+up, 'info');
  PL._tickets = Object.assign({}, tickets);
}
function plogHit(b){ if(PL && b && !b.ally && !b.sec && !b.shard) PL.hits++; }
function plogSec(){ if(PL) PL.secFired++; }
function plogRearm(){ if(PL){ PL.rearms++; plogEvent('rearmed', 'info'); } }
function plogDeath(){
  if(!PL) return;
  const dh = PL._hp - Math.max(0, player.hp);
  if(dh>0){ PL.hull += dh; const k = PL.src || 'other'; PL.dmgBy[k] = (PL.dmgBy[k]||0) + dh; }
  const cause = (PL.src || 'unknown') + (PL.who ? ' - '+PL.who : '');
  PL.deaths.push({t:PL.t, cause:cause});
  plogEvent('died: '+cause, 'bad');
  PL.src = null; PL.who = '';
}
// Every step while a wave is played: what changed since the last one.
function plogTick(){
  if(!PL || GS!=='playing') return;
  PL.t++;
  // What was flown, and for how long: hull, primary / secondary.
  // curPri()/curSec(): the fitted weapon, also while none was chosen yet.
  const fk = player.ship+' '+curPri().key+' / '+curSec().key;
  PL.fits = PL.fits || {};
  PL.fits[fk] = (PL.fits[fk]||0) + 1;
  // Bolts the player fired since the last step; secondaries and shards
  // are counted on their own.
  for(const b of pBullets) if(!b.ally && !b._pl){ b._pl = 1; if(!b.sec && !b.shard) PL.bolts++; }
  if(waveOver && PL.tEnd==null){ PL.tEnd = PL.t; plogEvent('wave clear', 'info'); }
  const ds = score - PL._score;
  if(ds>0) PL.gain += ds;
  else if(ds<0){
    PL.loss -= ds;
    plogEvent((PL._lossWhy || 'points lost')+' ('+ds+')', 'bad');
  }
  PL._lossWhy = '';
  for(const k of TICKET_ORDER){
    const d = (tickets[k]||0) - (PL._tickets[k]||0);
    if(d>0){ PL.tGot[k] = (PL.tGot[k]||0) + d; plogEvent('+'+d+' '+k+' ticket', 'good'); }
    else if(d<0){ PL.tUsed[k] = (PL.tUsed[k]||0) - d; plogEvent(d+' '+k+' ticket', 'info'); }
  }
  const dh = PL._hp - player.hp, dsh = PL._sh - player.sh;
  if(dh>0){ PL.hull += dh; const k = PL.src || 'other'; PL.dmgBy[k] = (PL.dmgBy[k]||0) + dh; }
  if(dsh>0) PL.shield += dsh;
  if(objCard && objCard !== PL._card){
    PL.cards.push({t:PL.t, head:objCard.head, txt:objCard.txt, tone:objCard.tone});
    plogEvent(objCard.head+': '+objCard.txt, objCard.tone==='fail' ? 'bad' : (objCard.tone==='done' ? 'good' : 'info'));
  }
  PL._card = objCard;
  PL.src = null; PL.who = '';
  plogSync();
}
function plogRows(){
  const rows = PLOG.slice();
  if(PL){ const c = Object.assign({}, PL, {stats:{}}); plogFinish(c); c.running = true; rows.push(c); }
  return rows;
}
function plogSum(o){ let n = 0; for(const k in o) n += o[k]; return n; }
function plogObj(r){
  let ok = 0, bad = 0;
  for(const c of r.cards){ if(c.tone==='done') ok++; else if(c.tone==='fail') bad++; }
  return {ok:ok, bad:bad};
}
function plogKills(r){
  const s = r.stats;
  return {small:(s.killFighter||0)+(s.killBomber||0),
          cap:(s.killCruiser||0)+(s.killCorvette||0)+(s.killDestroyer||0)+(s.killBoss||0)};
}

// The whole log as plain text, for copying out of the game.
function plogText(){
  const L = [];
  L.push('FS3 '+GAME_VERSION+' - practice log - '+new Date().toISOString().replace('T',' ').substr(0,16));
  L.push('run score '+score+', lives '+lives+', ship '+player.ship);
  for(const r of plogRows()){
    const o = plogObj(r), k = plogKills(r), s = r.stats;
    L.push('');
    L.push('WAVE '+r.wave+' - '+r.name+(r.scripted?'':' (random)')+' - '+r.fac+' - ship '+r.ship+
           (r.running ? ' - still running' : ''));
    L.push('  time '+plogTime(r.tEnd!=null ? r.tEnd : r.t)+(r.tEnd!=null && r.t>r.tEnd ? ' (+'+plogTime(r.t-r.tEnd)+' until the jump)' : ''));
    if(r.fits){
      const ft = Object.values(r.fits).reduce((a,b)=>a+b, 0) || 1;
      L.push('  flown: '+Object.entries(r.fits).sort((a,b)=>b[1]-a[1])
             .map(([k,v])=>k+' ('+Math.round(v*100/ft)+' %)').join(', '));
    }
    L.push('  score +'+r.gain+' / -'+r.loss);
    L.push('  objectives: '+o.ok+' complete, '+o.bad+' failed'+
           (r.cards.length ? '  ['+r.cards.map(c=>c.head+': '+c.txt).join(' | ')+']' : ''));
    L.push('  deaths '+r.deaths.length+(r.deaths.length ? '  ['+r.deaths.map(d=>plogTime(d.t)+' '+d.cause).join(' | ')+']' : ''));
    L.push('  picked up: lives '+(r.picked.life||0)+
           (r.picked.lifeFull ? ' ('+r.picked.lifeFull+' at the maximum)' : '')+
           ', repairs '+(r.picked.repair||0));
    L.push('  tickets in '+JSON.stringify(r.tGot)+', out '+JSON.stringify(r.tUsed)+
           (r.calls.length ? '  calls ['+r.calls.join(', ')+']' : '')+
           (r.refined.length ? '  refined ['+r.refined.join(', ')+']' : ''));
    L.push('  damage taken: hull '+Math.round(r.hull)+', shield '+Math.round(r.shield)+
           '  by source '+Object.keys(r.dmgBy).map(x=>x+' '+Math.round(r.dmgBy[x])).join(', '));
    L.push('  kills: fighters/bombers '+k.small+', capital ships '+k.cap+
           ' (cruiser '+(s.killCruiser||0)+', corvette '+(s.killCorvette||0)+', destroyer '+(s.killDestroyer||0)+
           '), sentries '+(s.killSentry||0)+', freighters '+(s.killFreighter||0)+', subsystems '+(s.subsKilled||0)+
           ', bombs shot down '+(s.bombsShot||0));
    L.push('  losses: allies '+r.allyLost+(r.capLost.length ? ' ['+r.capLost.join(', ')+']' : '')+
           ', protected lost '+r.lost+', protected through '+r.saved+', enemies escaped '+r.escaped);
    L.push('  weapons: bolts '+r.bolts+', hits '+r.hits+
           (r.bolts ? ' ('+Math.round(100*r.hits/r.bolts)+' %)' : '')+
           ', secondaries '+r.secFired+', rearms '+r.rearms+', support calls '+(s.escortsCalled||0));
    L.push('  timeline:');
    for(const ev of r.events) L.push('    '+plogTime(ev.t)+'  '+ev.txt);
  }
  return L.join('\n');
}
function plogCopy(){
  const t = plogText();
  let ok = false;
  try{
    if(navigator.clipboard && window.isSecureContext){ navigator.clipboard.writeText(t); ok = true; }
    else {
      const ta = document.createElement('textarea');
      ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      ok = document.execCommand('copy');
      document.body.removeChild(ta);
    }
  }catch(e){ ok = false; }
  plogMsg = ok ? 'COPIED - PASTE IT INTO THE CHAT' : 'COPY NOT ALLOWED HERE - USE SAVE FILE';
  plogMsgT = 240;
}
function plogSave(){
  try{
    const blob = new Blob([plogText()], {type:'text/plain'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'fs3_practice_log_'+GAME_VERSION+'_'+new Date().toISOString().substr(0,16).replace(/[:T]/g,'-')+'.txt';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function(){ URL.revokeObjectURL(a.href); }, 2000);
    plogMsg = 'SAVED';
  }catch(e){ plogMsg = 'SAVE FAILED'; }
  plogMsgT = 240;
}

// The card at the end of each wave, practice mode only.
function drawPlogCard(){
  if(!practiceMode || !PL || PL.tEnd==null || GS!=='playing') return;
  const r = Object.assign({}, PL, {stats:{}}); plogFinish(r);
  const o = plogObj(r), k = plogKills(r);
  const cw = 420, ch = 104, cx = ((W-cw)/2)|0, cy = H - ch - 14;
  ctx.save();
  thPlate(cx, cy, cw, ch, thRGBA('panelBack', 0.86), 8);
  thGlowPath(cx, cy, cw, ch, 8, 0.6);
  ctx.textAlign = 'left'; ctx.textBaseline = 'top';
  ctx.fillStyle = TH('accentWarm'); ctx.font = thLabel(11);
  ctx.fillText(thFit('WAVE '+r.wave+'  '+String(r.name).toUpperCase()+'  '+plogTime(r.tEnd), cw-24), cx+12, cy+9);
  ctx.font = thValue(11, false); ctx.fillStyle = TH('textBright');
  const col1 = cx+12, col2 = cx+cw/2+6;
  const line = function(x, y, a, b){ ctx.fillStyle = TH('text'); ctx.fillText(a, x, y);
    ctx.fillStyle = TH('textBright'); ctx.fillText(b, x+92, y); };
  line(col1, cy+30, 'SCORE', '+'+r.gain+'  / -'+r.loss);
  line(col1, cy+47, 'OBJECTIVES', o.ok+' done, '+o.bad+' failed');
  line(col1, cy+64, 'DEATHS', String(r.deaths.length));
  line(col1, cy+81, 'HULL LOST', String(Math.round(r.hull)));
  line(col2, cy+30, 'TICKETS', '+'+plogSum(r.tGot)+'  / -'+plogSum(r.tUsed));
  line(col2, cy+47, 'KILLS', k.small+' small, '+k.cap+' capital');
  line(col2, cy+64, 'PICKED UP', (r.picked.life||0)+' lives, '+(r.picked.repair||0)+' repairs');
  line(col2, cy+81, 'LOSSES', r.allyLost+' allies, '+r.lost+' protected');
  ctx.restore();
  ctx.textAlign = 'left'; ctx.textBaseline = 'top';
}

// The table, opened from the settings.
function drawPlog(){
  window._plogRects = [];
  const rows = plogRows();
  if(plogSel < 0 || plogSel >= rows.length) plogSel = rows.length-1;
  const px = 14, py = 14, pw = W-28, ph = H-28;
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,8,0.55)'; ctx.fillRect(0, 0, W, H);
  thPlate(px, py, pw, ph, thRGBA('panelBack', 0.96), 10);
  thGlowPath(px, py, pw, ph, 10, 0.7);
  ctx.textAlign = 'left'; ctx.textBaseline = 'top';
  ctx.fillStyle = TH('accentWarm'); ctx.font = thLabel(13);
  ctx.fillText('PRACTICE LOG', px+14, py+10);
  ctx.fillStyle = TH('textDim'); ctx.font = thValue(10, false);
  ctx.fillText(rows.length+' waves this run  -  tap a row for its details', px+140, py+13);
  // Columns.
  const C = [['WAVE',0],['MISSION',38],['TIME',210],['+SCORE',254],['-SCORE',314],['OBJ',370],
             ['DEATHS',420],['TICKETS',472],['KILLS',540],['HULL',600],['ESC',650],['LOST',700]];
  const tx = px+14, ty = py+34;
  ctx.fillStyle = TH('text'); ctx.font = thLabel(9);
  for(const c of C) ctx.fillText(c[0], tx+c[1], ty);
  if(plogTop > Math.max(0, rows.length-PLOG_ROWS)) plogTop = Math.max(0, rows.length-PLOG_ROWS);
  ctx.font = thValue(10, false);
  for(let i=0; i<PLOG_ROWS; i++){
    const n = plogTop + i; if(n >= rows.length) break;
    const r = rows[n], o = plogObj(r), k = plogKills(r);
    const y = ty + 16 + i*17;
    if(n===plogSel){ ctx.fillStyle = 'rgba(255,160,70,0.16)'; ctx.fillRect(tx-6, y-2, pw-16, 16); }
    const cells = [String(r.wave), thFit(String(r.name), 166)+(r.running?' *':''), plogTime(r.tEnd!=null?r.tEnd:r.t),
                   '+'+r.gain, '-'+r.loss, o.ok+' / '+o.bad, String(r.deaths.length),
                   '+'+plogSum(r.tGot)+' / -'+plogSum(r.tUsed), k.small+' / '+k.cap,
                   String(Math.round(r.hull)), String(r.escaped), String(r.allyLost+r.lost)];
    for(let c=0; c<C.length; c++){
      ctx.fillStyle = (c===5 && o.bad) || (c===6 && r.deaths.length) ? '#ff8866' : TH('textBright');
      ctx.fillText(cells[c], tx+C[c][1], y);
    }
    window._plogRects.push({x:tx-6, y:y-2, w:pw-16, h:16, act:'row', n:n});
  }
  // Scrolling, when there are more waves than rows.
  if(rows.length > PLOG_ROWS){
    const ax = px+pw-40, ayU = ty+14, ayD = ty+14+PLOG_ROWS*17-18;
    const canUp = plogTop > 0, canDn = plogTop < rows.length-PLOG_ROWS;
    const stU = btnState(canUp, false, hovering(ax, ayU, 26, 18));
    const stD = btnState(canDn, false, hovering(ax, ayD, 26, 18));
    thButton(ax, ayU, 26, 18, stU); thButton(ax, ayD, 26, 18, stD);
    ctx.textAlign = 'center';
    ctx.fillStyle = btnText(stU); ctx.fillText('^', ax+13, ty+17);
    ctx.fillStyle = btnText(stD); ctx.fillText('v', ax+13, ty+14+PLOG_ROWS*17-15);
    ctx.textAlign = 'left';
    if(canUp) window._plogRects.push({x:ax, y:ayU, w:26, h:18, act:'up'});
    if(canDn) window._plogRects.push({x:ax, y:ayD, w:26, h:18, act:'down'});
  }
  // The selected wave in detail: numbers on the left, timeline on the right.
  const dy = ty + 22 + PLOG_ROWS*17;
  ctx.fillStyle = 'rgba(255,160,70,0.45)'; ctx.fillRect(px+10, dy-4, pw-20, 1);
  const r = rows[plogSel];
  if(r){
    const s = r.stats, k = plogKills(r);
    const lines = [
      'WAVE '+r.wave+'  '+String(r.name).toUpperCase()+(r.running?'  (running)':''),
      'damage: hull '+Math.round(r.hull)+', shield '+Math.round(r.shield),
      '  '+(Object.keys(r.dmgBy).map(x=>x+' '+Math.round(r.dmgBy[x])).join(', ') || 'none'),
      'deaths: '+(r.deaths.map(d=>plogTime(d.t)+' '+d.cause).join(', ') || 'none'),
      'kills: '+k.small+' small, cruiser '+(s.killCruiser||0)+', corvette '+(s.killCorvette||0)+
        ', destroyer '+(s.killDestroyer||0)+', sentry '+(s.killSentry||0),
      'subsystems '+(s.subsKilled||0)+', bombs shot down '+(s.bombsShot||0)+', escaped '+r.escaped,
      'bolts '+r.bolts+', hits '+r.hits+(r.bolts?' ('+Math.round(100*r.hits/r.bolts)+' %)':'')+
        ', secondaries '+r.secFired+', rearms '+r.rearms,
      'tickets in '+(Object.keys(r.tGot).map(x=>x+' '+r.tGot[x]).join(', ')||'-')+
        ', out '+(Object.keys(r.tUsed).map(x=>x+' '+r.tUsed[x]).join(', ')||'-')+
        (r.refined.length ? ', refined '+r.refined.length+'x' : ''),
      'lives picked up '+(r.picked.life||0)+(r.picked.lifeFull ? ' ('+r.picked.lifeFull+' at max)' : '')+
        ', repairs '+(r.picked.repair||0)+', calls '+(r.calls.join(', ')||'-'),
      'allies lost '+r.allyLost+', protected lost '+r.lost+' / through '+r.saved
    ];
    ctx.font = thValue(10, false);
    for(let i=0;i<lines.length;i++){
      ctx.fillStyle = i===0 ? TH('accentWarm') : TH('textBright');
      ctx.fillText(thFit(lines[i], 380), px+16, dy+4+i*15);
    }
    const ev = r.events.slice(-9);
    ctx.fillStyle = TH('text'); ctx.font = thLabel(9);
    ctx.fillText('TIMELINE (LAST '+ev.length+' OF '+r.events.length+')', px+410, dy+4);
    ctx.font = thValue(10, false);
    for(let i=0;i<ev.length;i++){
      ctx.fillStyle = ev[i].tone==='bad' ? '#ff8866' : (ev[i].tone==='good' ? '#7fe0a0' : TH('textBright'));
      ctx.fillText(thFit(plogTime(ev[i].t)+'  '+ev[i].txt, 340), px+410, dy+19+i*14);
    }
  }
  // Buttons.
  const by = py+ph-34, bw = 130;
  const btns = [['COPY AS TEXT','copy'],['SAVE FILE','save'],['CLOSE','close']];
  for(let i=0;i<btns.length;i++){
    const bx = px+14+i*(bw+10);
    const st = btnState(true, false, hovering(bx, by, bw, 24));
    thButton(bx, by, bw, 24, st);
    ctx.fillStyle = btnText(st); ctx.font = thLabel(11); ctx.textAlign = 'center';
    ctx.fillText(btns[i][0], bx+bw/2, by+6);
    ctx.textAlign = 'left';
    window._plogRects.push({x:bx, y:by, w:bw, h:24, act:btns[i][1]});
  }
  if(plogMsgT > 0){
    plogMsgT--;
    ctx.fillStyle = TH('accentWarm'); ctx.font = thLabel(10);
    ctx.fillText(plogMsg, px+14+3*(bw+10)+6, by+7);
  }
  ctx.restore();
  ctx.textAlign = 'left'; ctx.textBaseline = 'top';
}
const PLOG_STEP = 3;      // rows moved per tap on an arrow
function plogClick(mx, my){
  const rs = window._plogRects || [];
  // Latest first: the scroll arrows are drawn over the rows and have to
  // win the tap, otherwise it opened the row underneath.
  for(let q=rs.length-1; q>=0; q--){
    const r = rs[q];
    if(mx>=r.x && mx<=r.x+r.w && my>=r.y && my<=r.y+r.h){
      if(r.act==='row') plogSel = r.n;
      else if(r.act==='up') plogTop = Math.max(0, plogTop-PLOG_STEP);
      else if(r.act==='down') plogTop = plogTop+PLOG_STEP;
      else if(r.act==='copy') plogCopy();
      else if(r.act==='save') plogSave();
      else if(r.act==='close') plogOpen = false;
      return true;
    }
  }
  return true;          // a tap on the panel does not close the settings
}

// The vortex of one ship. Drawn just before that ship, not in a pass
// before all of them: a small ship's vortex in front of a large one
// was hidden behind the large hull and the small one seemed to vanish
// into nothing (Silvio, the Elysium at the Iceni in M70).
function drawVortexOf(e){
  if(!(WARP_IMG&&WARP_IMG.complete&&WARP_IMG.naturalWidth>0)) return;
  drawOwnVortex(e);
  // Her arrival portal (FreeSpace style), still open or closing.
  try{ drawFsPortals(function(p){ return p.e===e; }); }catch(ep){ ctx.restore(); ctx.globalAlpha=1; }
}
function drawOwnVortex(e){
  if(e.warp>0 || e.warpOut>0){
    // FreeSpace style: the vortex stands across the flight path.
    const fg = fsWarp(e);
    if(fg){
      try{
        let WSf = 120; const fImg = IMGS[e.img];
        if(fImg) WSf = Math.max(100, fImg.height*e.sc*1.9, fImg.width*e.sc*0.62);
        // Coming in: the vortex is drawn by drawFsPortals() after this.
        if(!fg.out){ fsPortalOpen(e, fg, WSf); return; }
        ctx.save();
        ctx.globalAlpha = fg.wA;
        ctx.translate(fg.px|0, fg.py|0);
        if(WARP_STYLE==='oval'){ ctx.rotate(Math.atan2(fg.fy, fg.fx)); ctx.scale(WARP_OVAL*fg.wS, fg.wS); }
        else ctx.scale(fg.wS, fg.wS);
        drawWarpFrame(warpSeed(e), WSf, warpTurquoise(e));
        ctx.restore(); ctx.globalAlpha = 1;
      }catch(ef){ ctx.restore(); ctx.globalAlpha = 1; }
      return;
    }
    try{
      // The same duration that drives the ship's visibility.
      var mW=e.warpMax||100;
      var elapsed=e.warpOut>0 ? (mW-e.warpOut) : (mW-e.warp);
      var p1=mW*0.40,p2=mW*0.60;   // opening / open / closing
      var wS,wA;
      if(elapsed<p1){
        var t1=elapsed/p1; wS=0.05+0.95*t1; wA=t1;
      } else if(elapsed<p2){
        wS=1.0; wA=1.0;
      } else {
        var t3=(elapsed-p2)/(mW-p2); wS=1.0-t3; wA=Math.max(0,1.0-t3);
      }
      const wx2=(e.warpX||W-20)|0,wy2=(e.warpY||e.y)|0;
      ctx.save();
      ctx.globalAlpha=wA;
      ctx.translate(wx2,wy2);
      ctx.scale(wS,wS);
      // The vortex has to match the ship coming through it.
      // These used to be fixed per class, matching the old,
      // kleineren Sprites gehoerten.
      var WS=120;
      var wImg=IMGS[e.img];
      if(wImg) WS=Math.max(100, wImg.height*e.sc*1.9, wImg.width*e.sc*0.62);
      var wF=Math.floor(elapsed/mW*WARP_FRAMES);
      if(wF<0) wF=0; if(wF>WARP_FRAMES-1) wF=WARP_FRAMES-1;
      drawWarpFrame(warpSeed(e), WS, warpTurquoise(e));
      ctx.restore();
      ctx.globalAlpha=1;
    }catch(ew){ctx.restore();ctx.globalAlpha=1;}
  }
}
