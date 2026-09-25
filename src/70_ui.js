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
  drawNebula();
  drawBodies();
  drawStars();

  if(GS==='title'){drawTitle();return;}
  if(GS==='gameover'){drawGO();return;}

  const loaded=imgsLoaded+nebsLoaded;
  if(loaded<TOTAL){
    ctx.fillStyle='#00ff88';ctx.font='16px Courier New';
    ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText('Loading... '+loaded+'/'+TOTAL,W/2,H/2);return;}



  for(const b of pBullets){
    if(!b.sec){
      // Laser: leuchtender Bolt
      const ang=Math.atan2(b.vy,b.vx);
      ctx.save();
      ctx.translate(b.x|0,b.y|0);
      ctx.rotate(ang);
      ctx.globalAlpha=0.85;
      const aGlow = b.ally ? (b.fac==='vasudan'?'rgba(255,200,60,0.32)':'rgba(90,180,255,0.32)')
                           : (b.glow||'rgba(180,255,80,0.3)');
      const aCore = b.ally ? (b.fac==='vasudan'?'#ffd257':'#7fc4ff') : (b.col||'#ccff88');
      ctx.fillStyle=aGlow;
      ctx.beginPath();ctx.ellipse(0,0,b.w*.55,b.h*.9,0,0,Math.PI*2);ctx.fill();
      ctx.fillStyle=aCore;
      ctx.beginPath();ctx.ellipse(0,0,b.w*.38,b.h*.6,0,0,Math.PI*2);ctx.fill();
      ctx.fillStyle='#ffffff';
      ctx.beginPath();ctx.ellipse(0,0,b.w*.15,b.h*.25,0,0,Math.PI*2);ctx.fill();
      ctx.globalAlpha=1;
      ctx.restore();
    } else if(b.sec){
      if(b.type==='missile'){
        // Missile: metallic body plus engine glow
        const mx=(b.x)|0, my=(b.y)|0;
        // Triebwerk-Glow (hinten)
        ctx.fillStyle='rgba(255,120,0,0.5)';
        ctx.beginPath();ctx.ellipse(mx-b.w/2,my,6,4,0,0,Math.PI*2);ctx.fill();
        ctx.fillStyle='rgba(255,200,50,0.8)';
        ctx.beginPath();ctx.ellipse(mx-b.w/2,my,3,2,0,0,Math.PI*2);ctx.fill();
        // Rumpf
        ctx.fillStyle='#aabbcc';
        ctx.fillRect(mx-b.w/2+4,my-2,b.w-6,4);
        // Nase (spitz, vorne)
        ctx.fillStyle='#dd4422';
        ctx.beginPath();ctx.moveTo(mx+b.w/2,my);
        ctx.lineTo(mx+b.w/2-6,my-2);ctx.lineTo(mx+b.w/2-6,my+2);
        ctx.closePath();ctx.fill();
        // Finnen
        ctx.fillStyle='#8899aa';
        ctx.fillRect(mx-b.w/2+4,my-4,5,2);
        ctx.fillRect(mx-b.w/2+4,my+2,5,2);
      } else {
        // Bomb: dark sphere with a pulsing warning glow
        const pulse=0.5+0.5*Math.sin(fc*0.25);
        const br=b.w/2;
        // Outer warning ring
        ctx.strokeStyle='rgba(255,50,0,'+(0.3+pulse*0.5)+')';
        ctx.lineWidth=2;
        ctx.beginPath();ctx.arc(b.x,b.y,br+4+pulse*4,0,Math.PI*2);ctx.stroke();
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
      const shiv=b.faction==='shivan';
      // NTF ordnance is violet, matching their drives. Without it their
      // missiles look exactly like everyone else's Terran hardware.
      const ntf=b.faction==='ntf';
      const body=shiv?'#ffb0a0':(ntf?'#e0c8ff':'#c8ffe0');
      const glow=shiv?'rgba(255,60,0,0.5)':(ntf?'rgba(160,107,255,0.5)':'rgba(60,255,140,0.5)');

      // Halo underneath the ordnance so it never blends into a nebula.
      // Drawn unrotated and additively, then the body goes on top.
      const halo=(b.kind==='bomb'?2.6:1.9)*b.w*(0.92+0.08*Math.sin(fc*0.5));
      ctx.save();
      ctx.globalCompositeOperation='lighter';
      try{
        const hg=ctx.createRadialGradient(bx,by,0,bx,by,halo);
        hg.addColorStop(0, shiv?'rgba(255,190,150,0.85)':(ntf?'rgba(220,190,255,0.85)':'rgba(190,255,220,0.85)'));
        hg.addColorStop(0.30, shiv?'rgba(255,90,40,0.45)':(ntf?'rgba(150,80,255,0.45)':'rgba(70,255,160,0.45)'));
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
             : ntf  ? (Math.random()<0.5?'#ffffff':'#c8a0ff')
                    : (Math.random()<0.5?'#ffffff':'#88ffcc')});
      }

      ctx.save();
      ctx.translate(bx,by); ctx.rotate(ang);
      // Exhaust plume trailing behind
      ctx.globalAlpha=0.75;
      const fl=ctx.createLinearGradient(0,0,-b.w*1.6,0);
      fl.addColorStop(0,'#ffffff'); fl.addColorStop(0.35,shiv?'#ff8844':(ntf?'#b98cff':'#ffcc66'));
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
    const bShiv=b.faction==='shivan';
    const bC1=bShiv?'rgba(255,30,0,0.35)' :'rgba(0,200,60,0.35)';
    const bC2=bShiv?'#ff4422'             :'#00dd44';
    const bC3=bShiv?'#ffaa88'             :'#aaffaa';
    const bG1=bShiv?'rgba(255,100,0,0.35)':'rgba(0,230,80,0.35)';
    const bG2=bShiv?'#ffaa00'             :'#44ff88';
    if(b.big){
      ctx.globalAlpha=0.9;
      ctx.fillStyle=bG1;
      ctx.beginPath();ctx.ellipse(bx,by,b.w*.65,b.h*.65,0,0,Math.PI*2);ctx.fill();
      ctx.fillStyle=bG2;
      ctx.beginPath();ctx.ellipse(bx,by,b.w*.4,b.h*.4,0,0,Math.PI*2);ctx.fill();
      ctx.fillStyle='#ffffff';
      ctx.beginPath();ctx.ellipse(bx,by,b.w*.18,b.h*.18,0,0,Math.PI*2);ctx.fill();
    }else{
      // Bolts are no longer horizontal, so the elongated glow has to turn
      // with the flight path or a shot upwards reads as a round blob.
      const bAng=Math.atan2(b.vy,b.vx);
      ctx.globalAlpha=0.3;
      ctx.fillStyle=bC1;
      ctx.beginPath();ctx.ellipse(bx,by,b.w*.9,b.h*.9,bAng,0,Math.PI*2);ctx.fill();
      ctx.globalAlpha=0.9;
      ctx.fillStyle=bC2;
      ctx.beginPath();ctx.ellipse(bx,by,b.w*.5,b.h*.5,bAng,0,Math.PI*2);ctx.fill();
      ctx.globalAlpha=1;
      ctx.fillStyle=bC3;
      ctx.beginPath();ctx.ellipse(bx,by,b.w*.2,b.h*.2,bAng,0,Math.PI*2);ctx.fill();
    }}

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
  if(WARP_IMG&&WARP_IMG.complete&&WARP_IMG.naturalWidth>0){
    for(const e of SHIPS_ON_FIELD){
      if(e.warp>0 || e.warpOut>0){
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
          ctx.drawImage(WARP_IMG,
            (wF%WARP_COLS)*WARP_CELL, ((wF/WARP_COLS)|0)*WARP_CELL,
            WARP_CELL, WARP_CELL,
            -WS/2,-WS/2,WS,WS);
          ctx.restore();
          ctx.globalAlpha=1;
        }catch(ew){ctx.restore();ctx.globalAlpha=1;}
      }
    }
  }

  // Wreckage sits behind the ships: it is scenery that bites, not a unit.
  ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
  drawDebris();

  // State-Reset vor Enemy-Render
  ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
  for(const e of SHIPS_ON_FIELD){
    try{
    // Ship only visible once the vortex is fully open (phase 2 and 3)
    // wAlpha carries the fade in from the vortex. It used to be
    // wiped out one line later by globalAlpha=1,
    // which is why ships used to pop in.
    var wAlpha=1;
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
      drawThrusters(e.img,e.x|0,e.y|0,e.sc,e.flip,e.faction,e.warp>0?0.35:1,e.ang||0);
      drawShip(e.img,e.x|0,e.y|0,e.sc,e.flip,e.ang||0);
      drawHostileMark(e);
      drawScorch(e);
      drawShield(e);
      drawScanRing(e);

      if(e.type==='cruiser'||e.type==='corvette'||e.type==='destroyer'||
         e.type==='boss'||e.type==='station'){
        const hbImg=IMGS[e.img];if(hbImg){
          var bwMult=(e.type==='boss'?0.75:(e.type==='destroyer'?0.55:0.70));
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
        }}}
    ctx.globalAlpha=1;
    if(e.bShield>0){ drawLuciShield(e); drawReactors(e); }
    else drawSubsystems(e);
    drawBeams(e);
    }catch(ee){ctx.restore();ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';}}
  ctx.shadowBlur=0;ctx.shadowColor='transparent';

  try{
    drawHoldRing();
    {
      const _pf=player.flip||false;
      const _js=jumpScale();
      if(_js>=1){
        drawThrusters(player.ship,player.x|0,player.y|0,playerSc(),_pf,'terran',
          (K['ArrowRight']||K['d']||K['D'])?1.35:((K['ArrowLeft']||K['a']||K['A'])?0.45:1),
          player.ang||0);
      }
      drawShip(player.ship,player.x|0,player.y|0,playerSc()*_js,_pf,player.ang||0);
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
  drawEmpWarn();
  drawEmpFX();
  drawItems();
  drawTicketMsgs();
  drawSubMsgs();
  // The shake must not reach the instruments, so the transform is put
  // back before the strip is drawn.
  ctx.setTransform(RES_X, 0, 0, RES_Y, 0, 0);
  drawHUD();
  // Blackout is drawn over the strip rather than skipping it, so the
  // instruments visibly fail instead of quietly disappearing.
  drawEmpHudGlitch();
  drawFleeWarning();
  drawFieldBanner();
  tickFps();
  drawFps();
  drawObjCount();
  drawWaveTitle();
  drawSettings();
  // Opening the settings pauses the game, so without this the pause
  // notice printed straight across the panel it had just opened.
  if(paused && !settingsOpen){
    ctx.fillStyle='rgba(0,0,0,0.55)';ctx.fillRect(0,0,W,H);
    ctx.fillStyle='#ffffff';ctx.font='bold 32px Courier New';
    ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText('PAUSED',W/2,H/2-20);
    ctx.font='14px Courier New';ctx.fillStyle='#aaaaaa';
    ctx.fillText('Press P or tap to resume',W/2,H/2+20);
    ctx.textAlign='left';ctx.textBaseline='top';
  }
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

function drawFieldBanner(){
  if(GS!=='playing') return;
  // The countdowns no longer suppress it, they just push it down a row.
  let txt=null, col='#ff2200', ink='#ff4422';
  const ob=objectiveText();
  if(ob){
    txt=ob.txt; col=ob.col; ink=ob.ink;
    objWasSet = true; objSeenOnce = true;
  } else {
    // Gab es einen Auftrag und ist er jetzt weg, war er erledigt. Ohne
    // diese Meldung verschwindet die Zeile stumm und der Spieler weiss
    // nicht, ob er fertig ist oder etwas uebersehen hat.
    if(objWasSet){ objWasSet = false; objDoneT = OBJ_DONE_TIME; objFailed = guardLost; }
    const bossInQ=spawnQ.some(function(s){return s.type==='boss_ntf'||s.type==='boss_sh';});
    if(objDoneT>0){
      if(!paused) objDoneT--;
      if(objFailed && protSaved>0){
        // Ein Teil ist durchgekommen: weder Erfolg noch Fehlschlag.
        txt='[ PARTIAL SUCCESS  '+protSaved+'/'+(protSaved+protLost)+' ]';
        col='#bb8800'; ink='#ffcc44';
      }
      else if(objFailed){ txt='[ OBJECTIVE FAILED ]'; col='#cc2200'; ink='#ff5533'; }
      else              { txt='[ OBJECTIVE COMPLETE ]'; col='#00cc44'; ink='#4dff88'; }
    }
    else if(bossInQ||bossAlive) txt='[ BOSS FIGHT ]';
    // Sonst: aufraeumen. Die Zeile bleibt stehen, solange noch etwas im
    // Feld oder in der Warteschlange steht.
    else if(!spawnQ.length && liveThreatCount()>0)
      { txt='[ CLEAR THE FIELD ]'; col='#ff2200'; ink='#ff4422'; }
  }
  if(!txt) return;
  if(fc%60>=42) return;
  ctx.save();
  ctx.font='bold 12px Courier New';
  ctx.textAlign='center'; ctx.textBaseline='top';
  // Pushed below whatever countdowns are running.
  const rows=Math.min(FLEE_ROWS, fleeingEnemies().length);
  const tw=ctx.measureText(txt).width;
  const bx=((W-tw)/2-10)|0, by=HUD_H+6+rows*23;
  ctx.globalAlpha=0.72; ctx.fillStyle='#000';
  ctx.fillRect(bx,by,(tw+20)|0,20);
  ctx.globalAlpha=1;
  ctx.strokeStyle=col; ctx.lineWidth=1;
  ctx.strokeRect(bx,by,(tw+20)|0,20);
  ctx.fillStyle=ink;
  ctx.fillText(txt,W/2,by+5);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}

// Stacked, most urgent at the top. Three at once is already more capital
// ships than any wave fields, so the list is capped there.
const FLEE_ROWS = 3;
function drawFleeWarning(){
  if(GS!=='playing') return;
  const list=fleeingEnemies();
  if(!list.length) return;
  ctx.save();
  ctx.font='bold 12px Courier New';
  ctx.textAlign='center'; ctx.textBaseline='top';
  let row=0;
  for(const flr of list){
    if(row>=FLEE_ROWS) break;
    const sec=Math.ceil(flr.fleeT/TICK_HZ);
    const urgent=sec<=10;
    const by=HUD_H+6+row*23;
    row++;
    if(urgent && fc%40>=28) continue;      // blink once it gets tight
    const txt=(flr.label||(flr.type||'CAPITAL SHIP').toUpperCase())+
              (flr.disarmed?' WITHDRAWING IN ':' JUMPING OUT IN ')+sec+'s';
    const tw=ctx.measureText(txt).width;
    const bx=((W-tw)/2-10)|0;
    ctx.globalAlpha=0.72;
    ctx.fillStyle='#000';
    ctx.fillRect(bx, by, (tw+20)|0, 20);
    ctx.globalAlpha=1;
    ctx.strokeStyle=urgent?'#ff5500':'#ffbb22'; ctx.lineWidth=1;
    ctx.strokeRect(bx, by, (tw+20)|0, 20);
    ctx.fillStyle=urgent?'#ff7733':'#ffcc44';
    ctx.fillText(txt, W/2, by+5);
  }
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}

// A gear, drawn rather than an image, so it needs no asset and scales.
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
function drawFps(){
  if(!showFps) return;
  const txt='FPS '+(fpsVal||'--');
  ctx.save();
  ctx.font='bold 11px Courier New';
  ctx.textAlign='left'; ctx.textBaseline='top';
  ctx.globalAlpha=0.72; ctx.fillStyle='#000';
  ctx.fillRect(W-60, HUD_H+4, 54, 15);
  ctx.globalAlpha=1;
  ctx.fillStyle = fpsVal && fpsVal<40 ? '#ff9900' : '#00ee55';
  ctx.fillText(txt, W-56, HUD_H+6);
  ctx.restore();
}
// Objektzaehler. Drei Zahlen statt einer Summe: eine Summe sagt, dass es
// waechst, drei sagen welche Liste waechst. Courier ist eine
// Festbreitenschrift, ein Zeichen ist 0.6 mal die Schriftgroesse breit -
// bei 11 px also 6.6. Der laengste denkbare Text 'OBJ 999/9999/999' hat
// 16 Zeichen und damit 105.6 px, der Kasten ist 112 breit.
let showObj=false;
function drawObjCount(){
  if(!showObj) return;
  const ships = enemies.length + allies.length;
  const shots = pBullets.length + eBullets.length;
  const junk  = debris.length + PARTS.length + ITEMS.length;
  const txt = 'OBJ '+ships+'/'+shots+'/'+junk;
  ctx.save();
  ctx.font='bold 11px Courier New';
  ctx.textAlign='left'; ctx.textBaseline='top';
  ctx.globalAlpha=0.72; ctx.fillStyle='#000';
  ctx.fillRect(W-118, HUD_H+22, 112, 15);
  ctx.globalAlpha=1;
  ctx.fillStyle='#66ccff';
  ctx.fillText(txt, W-114, HUD_H+24);
  ctx.restore();
}

// No need to remember the previous pause any more: closing the panel
// simply drops this panel's own reason to pause, and syncPause() works
// out whether anything else still wants the game held.
function setSettings(v){
  v=!!v;
  settingsOpen=v;
  syncPause();
  if(!v) settingsPage=0;     // beim naechsten Oeffnen wieder Seite 1
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
const SETTINGS_PAGES = 3;
const SETTINGS_TITLES = ['SETTINGS', 'ECONOMY', 'APPEARANCE'];
function settingsRows(){
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
     hint:FS1_MODE?'no lives are lost, campaign only'
                  :'campaign only, start with ?fs1=1',
     value:practiceMode?'ON':'OFF', on:practiceMode,
     act:'practice', enabled:FS1_MODE},
    {label:'FRAME RATE', hint:'shows the frame rate below the top bar',
     value:showFps?'ON':'OFF', on:showFps, act:'fps', enabled:true},
    {label:'OBJECT COUNT', hint:'ships / shots / debris, below the rate',
     value:showObj?'ON':'OFF', on:showObj, act:'obj', enabled:true}
  ];
}

function drawSettings(){
  if(!settingsOpen) return;
  window._setRects=[];
  const bw=300, bh=40, gap=8;
  // The height follows the page, so a shorter page leaves no hole.
  const rows=Math.max(1, settingsRows().length);
  const hintH=22;   // room for the closing hint, which used to land inside
                    // the option box because it was not accounted for
  const verH=16;    // eigene Zeile fuer die Versionsnummer, aus demselben
                    // Grund getrennt gerechnet statt in den Hinweis gequetscht
  const navH=24;    // Blaetterzeile, ebenso
  const mw=bw+gap*2, mh=bh*rows+gap*(rows+1)+30+navH+hintH+verH;
  const mx=(W-mw)/2, my=(H-mh)/2;
  uiDialog(mx, my, mw, mh, 'rgba(0,14,6,0.96)', '#00aa44');
  ctx.fillStyle=UI('textBright','#00ee55');
  ctx.font=uiLabel(13, 'bold 13px Courier New');
  ctx.textAlign='center'; ctx.textBaseline='top';
  ctx.fillText(SETTINGS_TITLES[settingsPage]||'SETTINGS', mx+mw/2, my+9);

  const bx=mx+gap;
  const list=settingsRows();
  for(let i=0;i<list.length;i++){
    const r=list[i];
    setRow(bx, my+30+gap+i*(bh+gap), bw, bh,
           r.label, r.hint, r.value, r.on, r.act, r.enabled);
  }

  // Blaetterzeile. Zwei Pfeilfelder und die Seitenzahl dazwischen.
  const ny = my+30+gap+rows*(bh+gap);
  ctx.textAlign='center'; ctx.textBaseline='top';
  uiCell(bx, ny, 40, 18, {state:'ready', fill:'#00160c', stroke:'#4499ff'});
  uiCell(bx+bw-40, ny, 40, 18, {state:'ready', fill:'#00160c', stroke:'#4499ff'});
  ctx.fillStyle=UI('accent','#7fc4ff');
  ctx.font=uiValue(13, true, 'bold 12px Courier New');
  ctx.fillText('<', bx+20, ny+3);
  ctx.fillText('>', bx+bw-20, ny+3);
  ctx.fillStyle=UI('textDim','#007733'); ctx.font=uiValue(10, false, '9px Courier New');
  ctx.fillText('PAGE '+(settingsPage+1)+'/'+SETTINGS_PAGES, mx+mw/2, ny+5);
  // Separate actions: with three pages one toggle cannot reach them all.
  window._setRects.push({x:bx, y:ny, w:40, h:18, act:'pageprev'});
  window._setRects.push({x:bx+bw-40, y:ny, w:40, h:18, act:'pagenext'});

  ctx.fillStyle=UI('edgeLight','#005522'); ctx.font=uiValue(10, false, '9px Courier New');
  ctx.fillText('FS3  '+GAME_VERSION, mx+mw/2, my+mh-hintH-verH+4);
  ctx.fillStyle=UI('textDim','#007733'); ctx.font=uiValue(10, false, '9px Courier New');
  ctx.fillText('tap outside or press S to close', mx+mw/2, my+mh-hintH+6);
  ctx.textAlign='left'; ctx.textBaseline='top';
}

// Returns true when the tap was consumed by the panel.
function settingsClick(mx,my){
  if(!settingsOpen) return false;
  const rs=window._setRects||[];
  for(const r of rs){
    if(mx>=r.x&&mx<=r.x+r.w&&my>=r.y&&my<=r.y+r.h){
      if(r.act==='fullscreen') toggleFullscreen();
      else if(r.act==='fps'){ showFps=!showFps; fpsFrames=0; fpsLast=0; }
      else if(r.act==='obj'){ showObj=!showObj; }
      else if(r.act==='practice'){ practiceMode=!practiceMode; }
      else if(r.act==='pagenext'){ settingsPage=(settingsPage+1)%SETTINGS_PAGES; }
      else if(r.act==='pageprev'){ settingsPage=(settingsPage+SETTINGS_PAGES-1)%SETTINGS_PAGES; }
      else if(r.act==='scheme'){ ECO.scheme=(ECO.scheme==='void')?'fire':'void'; ecoSave(); }
      else if(r.act==='res'){
        const _i=ECO_RES_STEPS.indexOf(ECO.res);
        ecoSetRes(ECO_RES_STEPS[(_i+1)%ECO_RES_STEPS.length]);
      }
      else if(r.act==='blur'){ ECO.blur=!ECO.blur; ecoSave(); }
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
  var H2=HUD_H, mid=(H2/2)|0;

  thPanel(0, 0, W, H2, TH('barTop'), TH('panelBack'));
  ctx.fillStyle=TH('panelBack'); ctx.fillRect(0, H-8, W, 8);
  ctx.strokeStyle=TH('edgeLight'); ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(0, H2-0.5); ctx.lineTo(W, H2-0.5); ctx.stroke();

  ctx.textBaseline='middle'; ctx.textAlign='left';

  // SCORE, WAVE, TIME
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('SCORE', 8, mid-9);
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(16, true);
  ctx.fillText(String(score).padStart(7,'0'), 8, mid+5);
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('TIME', 8, mid+19);
  ctx.fillStyle=callMenu?TH('textDim'):TH('text'); ctx.font=thValue(11, false);
  ctx.fillText(fmtTime(runTime), 34, mid+19);

  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('WAVE', 98, mid-9);
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(16, true);
  ctx.fillText(String(wave).padStart(3,'0'), 98, mid+5);

  thDivider(178, 4, H2-4);

  // HULL and SHIELD. The bars keep their own colours: those carry state.
  var hx=184, hw=110, hy=7, hh=9;
  var hR=player.hp/player.maxHp;
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('HULL', hx, hy+4);
  ctx.fillStyle=TH('edgeDark'); ctx.fillRect(hx, hy+11, hw, hh);
  ctx.globalAlpha=(hR<=HULL_CRIT)?(0.55+0.45*Math.sin(fc*0.22)):1;
  ctx.fillStyle=hullCol(hR);
  ctx.fillRect(hx, hy+11, (hw*hR)|0, hh);
  ctx.globalAlpha=1;
  thBevel(hx, hy+11, hw, hh);

  var sy=hy+24;
  var sR=player.sh/player.maxSh;
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('SHIELD', hx, sy+4);
  ctx.fillStyle=TH('edgeDark'); ctx.fillRect(hx, sy+11, hw, hh);
  ctx.fillStyle=sR>.5?'#0099ff':'#0055cc';
  ctx.fillRect(hx, sy+11, (hw*sR)|0, hh);
  thBevel(hx, sy+11, hw, hh);
  if(player.shDelay===0 && player.sh<player.maxSh && fc%30<15){
    ctx.fillStyle='rgba(0,100,200,0.2)'; ctx.fillRect(hx, sy+11, hw, hh);
  }

  thDivider(306, 4, H2-4);

  // LIVES
  var lx=312;
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('LIVES', lx, mid-9);
  var lIsB=isBomberHull(player.ship);
  var lIco=ICONS[lIsB?'bomberlives':'fighterlives'];
  var lsy=(mid+2)|0, usedW;
  if(lIco){
    var lh=15, lw=Math.max(1, Math.round(lIco.width*(lh/lIco.height)));
    ctx.drawImage(lIco, lx|0, (lsy-5)|0, lw, lh);
    usedW=lw;
  } else {
    ctx.fillStyle=TH('text');
    ctx.fillRect(lx, lsy+2, 11, 3); ctx.fillRect(lx+2, lsy, 7, 2);
    ctx.fillRect(lx+2, lsy+5, 7, 2); ctx.fillRect(lx+9, lsy+2, 4, 3);
    usedW=13;
  }
  ctx.fillStyle=TH('textBright'); ctx.font=thValue(15, true);
  ctx.fillText(String(lives), lx+usedW+7, lsy+2);

  thDivider(406, 4, H2-4);

  // SECONDARY WEAPON
  var secX=412, secBW=34, secBH=H2-10, secBY=5;
  var isMissile=player.secType==='missile';
  var secRdy=player.secTimer===0 && player.secAmmo>0;
  var secClr=isMissile?'#ff8800':'#cc2200';
  thButton(secX, secBY, secBW, secBH, secRdy?'ready':null);
  if(isMissile) drawMissileIcon(secX+secBW/2, secBY+13, secRdy?secClr:TH('textDim'));
  else          drawBombIcon(secX+secBW/2, secBY+13, secRdy?secClr:TH('textDim'));
  ctx.fillStyle=secRdy?TH('textBright'):TH('textDim'); ctx.font=thValue(13, true);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillText(String(player.secAmmo).padStart(2,'0'), secX+secBW/2, secBY+31);
  if(player.secTimer>0){
    var cdMax=isMissile?45:90, cdW=secBW-8;
    ctx.fillStyle=TH('edgeDark'); ctx.fillRect(secX+4, secBY+secBH-6, cdW, 3);
    ctx.fillStyle=secClr;
    ctx.fillRect(secX+4, secBY+secBH-6, (cdW*(1-player.secTimer/cdMax))|0, 3);
  }
  ctx.textAlign='left'; ctx.textBaseline='middle';
  window._secBtnRect={x:secX, y:secBY, w:secBW, h:secBH};

  thDivider(449, 4, H2-4);

  // SUPPORT
  var alX=455, alBW=76, alBH=H2-10, alBY=5;
  var alRdy=allyReady(), alCan=alRdy && anyTicket();
  thButton(alX, alBY, alBW, alBH, alCan?'ready':null);
  ctx.textAlign='left';
  ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
  ctx.fillText('SUPPORT', alX+5, alBY+9);
  ctx.fillStyle=alCan?TH('accent'):TH('textDim'); ctx.font=thValue(11, true);
  ctx.fillText(alRdy?(anyTicket()?'READY':'NO TICKET'):(allies.length?'DEPLOYED':'STANDBY'),
               alX+5, alBY+26);
  ctx.fillStyle=TH('textDim'); ctx.font=thValue(8, false);
  ctx.fillText('TAP / [C]', alX+5, alBY+alBH-7);
  window._allyBtnRect={x:alX, y:alBY, w:alBW, h:alBH};

  // TICKETS
  {
    var tkX=537, tkY=3, tkW=64, tkH=24;
    for(var ti=0; ti<TICKET_ORDER.length; ti++){
      var tk=TICKET_ORDER[ti], tn=tickets[tk]||0;
      var lit=tn>0;
      var fresh=(ticketFlash>0 && ticketFlashKind===tk && fc%16<10);
      var col=fresh?TH('accentWarm'):(lit?TH('accent'):TH('textDim'));
      var tico=ICONS[TICKET_ICON[tk]];
      var tcx=tkX+(ti%2)*tkW, tcy=tkY+((ti/2)|0)*tkH;
      ctx.textAlign='left'; ctx.textBaseline='top';
      ctx.fillStyle=col; ctx.font=thValue(13, true);
      ctx.fillText(tn+'x', tcx, tcy+5);
      var icoX=tcx+21;
      if(tico){
        ctx.globalAlpha=lit?1:0.28;
        var tih=11, tiw=Math.max(1, Math.round(tico.width*(tih/tico.height)));
        ctx.drawImage(tico, icoX, tcy+5, tiw, tih);
        ctx.globalAlpha=1;
      } else {
        ctx.fillStyle=col; ctx.font=thLabel(10);
        ctx.fillText(TICKET_ABBR[tk], icoX, tcy+6);
      }
    }
  }
  ctx.textBaseline='middle';

  // SHIP SWITCH and REARM, as a pair. Two buttons that both open a panel
  // over the field belong together, so they are centred as one group in
  // the gap between the tickets and the gear.
  if(!FS1_MODE){
    var swW=22, swH=H2-8, swY=4, swGap=4;
    var grpX=Math.round((665+W-52)/2-(swW*2+swGap)/2);
    var swX=grpX, rmX=grpX+swW+swGap;
    var swOn=shipSwapReady()||shipMenu;
    var swHv=hovering(swX, swY, swW, swH);
    thButton(swX, swY, swW, swH, (shipMenu||swHv)?'on':(swOn?'ready':null));
    drawSwapIcon(swX+swW/2, swY+swH/2,
                 swOn?TH('accentWarm'):(swHv?TH('text'):TH('textDim')));
    window._shipBtnRect={x:swX, y:swY, w:swW, h:swH};
    var rmOn=rearmReady()||rearmMenu;
    var rmHv=hovering(rmX, swY, swW, swH);
    thButton(rmX, swY, swW, swH, (rearmMenu||rmHv)?'on':(rmOn?'ready':null));
    drawRearmIcon(rmX+swW/2, swY+swH/2,
                  rmOn?TH('accentWarm'):(rmHv?TH('text'):TH('textDim')));
    window._rearmBtnRect={x:rmX, y:swY, w:swW, h:swH};
  } else { window._shipBtnRect=null; window._rearmBtnRect=null; }

  // SETTINGS and PAUSE
  var stbX=W-52, stbY=4, stbW=22, stbH=H2-8;
  var stbHv=hovering(stbX, stbY, stbW, stbH);
  thButton(stbX, stbY, stbW, stbH, (settingsOpen||stbHv)?'on':null);
  drawGear(stbX+stbW/2, stbY+stbH/2, 7,
           (settingsOpen||stbHv)?TH('textBright'):TH('text'));
  window._settingsBtnRect={x:stbX, y:stbY, w:stbW, h:stbH};

  var pbX=W-26, pbY=4, pbW=22, pbH=H2-8;
  var pbHv=hovering(pbX, pbY, pbW, pbH);
  thButton(pbX, pbY, pbW, pbH, (paused||pbHv)?'on':null);
  drawPauseIcon(pbX+pbW/2, pbY+pbH/2,
                (paused||pbHv)?TH('textBright'):TH('text'), !paused);
  window._pauseBtnRect={x:pbX, y:pbY, w:pbW, h:pbH};

  ctx.textAlign='left'; ctx.textBaseline='top';
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
function shipStats(key){
  for(const s of PLAYER_SHIPS) if(s.key===key) return s;
  const b = isBomberHull(key);
  return {key:key, name:key, spd:b?PLAYER_SPD_BOMBER:PLAYER_SPD_FIGHTER, turn:PLAYER_TURN,
          hp:100, sh:100, sec:b?10:20};
}
// Puts the player into a hull. Without keep everything is refilled. With
// keep - fractions of the old hull, shields and ammo - the state carries
// over in proportion, so a half wrecked fighter stays half wrecked on a
// tougher hull instead of gaining or losing absolute points.
function applyShip(key, keep){
  const s = shipStats(key);
  player.ship   = key;
  player.spd    = s.spd;
  player.turn   = s.turn;
  player.baseHp = s.hp;
  player.maxHp  = Math.round(s.hp*(player.hullMult||1));
  player.hp     = player.maxHp;
  player.maxSh  = s.sh;
  resetPlayerShield();
  // The hull still sets the size of the rack; the weapon scales it. A
  // bomber carrying ten and a fighter twenty is part of what tells them
  // apart, so that stays a property of the hull.
  applyLoadout();
  player.secAmmo= player.secMax;
  if(keep){
    player.hp      = Math.max(1, Math.round(player.maxHp*keep.hp));
    player.sh      = Math.min(player.maxSh, Math.round(player.maxSh*keep.sh));
    player.secAmmo = Math.min(player.secMax, Math.round(player.secMax*keep.sec));
  }
}
// Unlocks follow the score within a run. Several thresholds can fall in
// one step, e.g. after a big bonus, so this loops.
function tickShipUnlocks(){
  if(GS!=='playing' || FS1_MODE) return;
  while(shipUnlocked < PLAYER_SHIPS.length && score >= PLAYER_SHIPS[shipUnlocked].unlock){
    const s = PLAYER_SHIPS[shipUnlocked++];
    SUB_MSGS.push({x:W/2, y:H*0.34, txt:s.name.toUpperCase()+' AVAILABLE', life:260, ml:260, ally:true});
  }
}
// The switch lands from an allied destroyer's hangar, so one has to be on
// the field. The campaign mode assigns its hulls itself.
function shipSwapReady(){
  if(GS!=='playing' || FS1_MODE || inJump()) return false;
  if(shipUnlocked<2) return false;
  // One switch per wave, except while the Colossus is on station: her yard
  // stays open, and only the first switch of a wave refits.
  if(shipSwapWave===wave && !colossusOnField()) return false;
  // Something other than the active hull has to be unlocked AND on offer
  // from a hangar that is actually on the field.
  for(let i=0;i<shipUnlocked && i<PLAYER_SHIPS.length;i++){
    const s=PLAYER_SHIPS[i];
    if(s.key!==player.ship && shipOffered(s.key)) return true;
  }
  return false;
}
function setShipMenu(open){
  if(!open && shipMenu) holdResume();
  shipMenu = open;
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
  setShipMenu(true);
}
function swapShip(key){
  if(!shipMenu || key===player.ship) return;
  const i = PLAYER_SHIPS.findIndex(function(s){return s.key===key;});
  if(i<0 || i>=shipUnlocked) return;
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
  SUB_MSGS.push({x:player.x+60, y:player.y-30,
                 txt:PLAYER_SHIPS[i].name.toUpperCase()+(again?'  NO REFIT':''),
                 life:170, ml:170, ally:true});
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
const PRIMARIES = [
  {key:'prometheus', name:'Prometheus', unlock:0,
   dmg:1.00, rate:1.00, spd:9, range:0,
   col:'#ccff88', glow:'rgba(180,255,80,0.30)',
   note:'standard fit, and the longest reach of any gun'},
  // The same gun under two names: the Vasudan fleet calls it Mekhu, the
  // Terran one Subach. The game already renames hulls by era, so a weapon
  // with two names costs nothing but the second string.
  {key:'hl7', name:'Mekhu HL-7', nameTer:'Subach HL-7', unlock:6000,
   dmg:0.62, rate:0.60, spd:10.5, range:330,
   col:'#bfe9ff', glow:'rgba(120,200,255,0.30)',
   note:'quicker and lighter, and it runs out of reach early'},
  // pellets and spread turn one trigger pull into a cone. dmg is the
  // damage of the WHOLE volley, shared out, so a single pellet is slight
  // and a face full of them is not.
  {key:'scatter', name:'Streuschuss', unlock:14000,
   dmg:2.60, rate:1.85, spd:8, range:300, pellets:7, spread:0.30,
   col:'#ffd08a', glow:'rgba(255,170,70,0.30)',
   note:'a cone of pellets - murder in a crowd, nothing at range'},
  // pierce is how many hulls one bolt may take before it gives out. It
  // never takes the same ship twice, so a big hull is one hit and not one
  // per step of its length.
  {key:'pierce', name:'Durchschlag', unlock:22000,
   dmg:0.85, rate:1.55, spd:11, range:0, pierce:4,
   col:'#e6b9ff', glow:'rgba(200,120,255,0.32)',
   note:'takes everything on its line, once each'},
  // fuse is the distance at which it bursts of its own accord. That is
  // what makes it more than a round with a bonus: held on the trigger it
  // lays shrapnel across a fixed range and an attack run has to come
  // through it.
  {key:'dante', name:'Dante', unlock:32000,
   dmg:1.10, rate:1.40, spd:7.5, range:420, fuse:300,
   shards:9, shardDmg:0.38, shardSpd:3.4, shardRange:70,
   col:'#ffb066', glow:'rgba(255,140,50,0.34)',
   note:'bursts on impact and by itself at range - shrapnel, star shaped'}
];
// cls decides which hull may carry it: a fighter takes missiles, a bomber
// takes bombs, and neither takes the other's.
const SECONDARIES = [
  {key:'mx64', name:'MX-64', cls:'missile', unlock:0,
   ammoMul:1.0, dmg:35, cd:45, spd:3.5, life:220, homing:true,
   note:'light homing, quick off the rail'},
  {key:'cyclops', name:'Cyclops', cls:'bomb', unlock:0,
   ammoMul:1.0, dmg:80, cd:90, spd:1.5, life:300, homing:true,
   note:'slow and heavy, for hulls that cannot dodge'},
  // burst: the secondary button detonates it in flight instead of firing
  // another, and only one may be in the air. Straight, no seeking - what
  // it asks for is timing, not aim.
  {key:'infyrno', name:'Infyrno', cls:'missile', unlock:18000,
   ammoMul:0.7, dmg:40, cd:55, spd:4.2, life:200, homing:false,
   burst:true, shards:12, shardDmg:30, shardSpd:3.0, shardRange:90,
   note:'fired straight - press again to burst it into shrapnel'},
  // subs: the warhead goes into the innards rather than the hull. A
  // corvette without engines does not leave.
  {key:'stiletto', name:'Stiletto', cls:'bomb', unlock:26000,
   ammoMul:1.0, dmg:70, cd:95, spd:2.8, life:300, homing:true, subs:true,
   note:'into the subsystems, not the hull - stops a ship working'}
];
// Shrapnel, star shaped from a point. Three weapons make it - the Dante on
// impact, the Dante on its fuse, and the Infyrno when it is burst - so it
// is written once and they all call it. The shards are ordinary bolts and
// travel the ordinary way, which is what keeps them cheap.
function shardBurst(x, y, n, dmg, spd, range, col, glow){
  const off = Math.random()*Math.PI*2;
  const life = Math.max(1, Math.round(range/spd));
  for(let i=0;i<n;i++){
    const a = off + (i/n)*Math.PI*2;
    pBullets.push({x:x, y:y, vx:Math.cos(a)*spd, vy:Math.sin(a)*spd,
                   w:8, h:3, dmg:dmg, col:col, glow:glow, pLife:life,
                   shard:true});
  }
  spawnFireball(x, y, 22, 18);
  spawnDebris(x, y, 10, 255,190,90, 255,110,0, true);
}
// A warhead that goes for the innards. subHit only touches whatever
// happens to lie under the impact; this looks for the nearest living
// subsystem and puts the whole warhead into that, which is the entire
// point of carrying one.
function subStrike(e, dmg, hx, hy){
  if(!e.subs || !e.subs.length) return dmg;
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
  for(const w of PRIMARIES) if(w.key===key) return w;
  return PRIMARIES[0];
}
function secDef(key){
  for(const w of SECONDARIES) if(w.key===key) return w;
  return SECONDARIES[0];
}
function curPri(){ return priDef(player.pri); }
function curSec(){ return secDef(player.sec); }
function hullSecCls(key){ return isBomberHull(key) ? 'bomb' : 'missile'; }
// A weapon's name can depend on who is flying it.
function weaponName(w){
  if(w.nameTer && shipFac(player.ship)==='terran') return w.nameTer;
  return w.name;
}
// Unlocks follow the score within a run, the same way the hulls do.
function weaponOpen(w){ return FS1_MODE || UI_WEAPONS || score >= (w.unlock||0); }
function secondariesFor(shipKey){
  const c = hullSecCls(shipKey), out = [];
  for(const w of SECONDARIES) if(w.cls===c) out.push(w);
  return out;
}
// The default rack for a hull, used when a switch of hull makes the fitted
// secondary impossible - a bomber cannot carry what a fighter carried.
function defaultSec(shipKey){
  const list = secondariesFor(shipKey);
  return list.length ? list[0].key : SECONDARIES[0].key;
}
// The one place that puts a choice onto the ship. The firing routines read
// the weapon, never the other way round.
function applyLoadout(){
  if(!priDef(player.pri) || curPri().key!==player.pri) player.pri = PRIMARIES[0].key;
  if(curSec().cls !== hullSecCls(player.ship)) player.sec = defaultSec(player.ship);
  player.fR = Math.max(5, Math.round(PLAYER_FR_BASE*curPri().rate));
  const s = shipStats(player.ship);
  player.secType = curSec().cls==='bomb' ? 'bomb' : 'missile';
  player.secMax  = Math.max(1, Math.round((s.sec||0)*curSec().ammoMul));
}
// A refit fills the rack. This is what makes the panel a rearm rather than a
// swap, and it is the whole reason a corvette on the field is worth keeping.
function rearmFull(){
  applyLoadout();
  player.secAmmo = player.secMax;
  player.secTimer = 0;
}
// Newly reached weapons are announced like newly reached hulls, so a
// threshold is something you notice rather than something you find.
const WPN_SEEN = {};
function tickWeaponUnlocks(){
  if(GS!=='playing' || FS1_MODE) return;
  for(const w of PRIMARIES.concat(SECONDARIES)){
    if(!w.unlock || WPN_SEEN[w.key] || score < w.unlock) continue;
    WPN_SEEN[w.key] = true;
    SUB_MSGS.push({x:W/2, y:H*0.40, txt:weaponName(w).toUpperCase()+' AVAILABLE',
                   life:260, ml:260, ally:true});
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
  if(open){ shipMenu = false; callMenu = false; }
  syncPause();
  if(!open && GS==='playing'){ MOUSE.x = player.x; MOUSE.y = player.y; }
  syncCursor();
}
function toggleRearmMenu(){
  if(rearmMenu){ setRearmMenu(false); return; }
  if(!rearmReady()) return;
  setRearmMenu(true);
}
// Fitting a weapon. Both kinds go through here so the refill rule lives in
// one place, including the case of choosing what is already fitted.
function fitWeapon(key){
  if(!rearmMenu) return;
  let w = null, kind = '';
  for(const p of PRIMARIES)   if(p.key===key){ w = p; kind = 'pri'; }
  for(const s of SECONDARIES) if(s.key===key){ w = s; kind = 'sec'; }
  if(!w || !weaponOpen(w)) return;
  if(kind==='sec' && w.cls!==hullSecCls(player.ship)) return;
  if(kind==='pri') player.pri = w.key; else player.sec = w.key;
  setRearmMenu(false);
  rearmFull();
  SUB_MSGS.push({x:player.x+60, y:player.y-30, txt:weaponName(w).toUpperCase()+'  REARMED',
                 life:170, ml:170, ally:true});
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
const HG_W        = 660;    // panel width, of 800 logical points
const HG_PAD      = 12;     // inner margin, also the left edge of every row
const HG_ROW      = 38;     // a hull that can be taken
const HG_ROW_LOCK = 20;     // a hull that cannot
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
const HG_COLS = [
  {k:'hull',   x:232, label:'HULL'},
  {k:'shield', x:292, label:'SHIELD'},
  {k:'spd',    x:356, label:'SPD'},
  {k:'agi',    x:420, label:'AGI'},
  {k:'guns',   x:484, label:'GUNS'},
  {k:'volley', x:530, label:'VOLLEY'},
  {k:'sec',    x:586, label:'SEC'}
];
// Which hull belongs in which group. Read from the hull key, the same way the
// rest of the file decides what a bomber is, so a new hull lands in the right
// group without a second list to keep in step.
function hangarGroups(){
  const fi=[], bo=[];
  for(let i=0;i<PLAYER_SHIPS.length;i++)
    (isBomberHull(PLAYER_SHIPS[i].key) ? bo : fi).push(i);
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
function hangarLayout(){
  const groups = hangarGroups();
  const plan = [];
  let h = HG_TITLE;
  for(const g of groups){
    if(!g.idx.length) continue;
    plan.push({head:g.head, y:h});
    h += HG_HEAD;
    for(const i of g.idx){
      const s = PLAYER_SHIPS[i];
      const cur    = s.key===player.ship;
      const locked = i>=shipUnlocked;
      // Unlocked, but no hangar of its faction on the field: it keeps a full
      // row, because it is yours and its figures still have to be readable.
      const off    = !locked && !cur && !shipOffered(s.key);
      const rh     = locked ? HG_ROW_LOCK : HG_ROW;
      plan.push({i:i, y:h, h:rh, cur:cur, locked:locked, off:off});
      h += rh + HG_GAP;
    }
    h += HG_GROUPGAP;
  }
  h += HG_FOOT;
  return {mx:((W-HG_W)/2)|0, my:((H-h)/2)|0, mw:HG_W, mh:h, plan:plan};
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
function drawShipMenu(){
  if(!shipMenu) return;
  const L  = hangarLayout();
  const mx = L.mx, my = L.my, rw = L.mw - HG_PAD*2;
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

    if(p.locked){
      // A thin line with no plate under it: the name, and what it costs.
      ctx.textAlign='left'; ctx.textBaseline='middle';
      ctx.fillStyle=TH('textDim'); ctx.font=thValue(11, false);
      ctx.fillText(s.name, rx+HG_NAME, ry+p.h/2);
      ctx.fillText('unlocks at '+s.unlock.toLocaleString('en-US')+' points',
                   rx+HG_COLS[0].x, ry+p.h/2);
      window._shipRects.push({x:rx, y:ry, w:rw, h:p.h, ship:s.key, key:null});
      continue;
    }

    thPlate(rx, ry, rw, p.h,
            p.cur ? TH('raised') : (open ? TH('panelFront') : TH('back')));
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
      ctx.fillText(s.name, rx+HG_NAME, ry+13);
      ctx.fillStyle=TH('textDim'); ctx.font=thValue(9, false);
      ctx.fillText('NO '+(s.fac||'').toUpperCase()+' HANGAR ON THE FIELD', rx+HG_NAME, ry+27);
    } else {
      ctx.fillText(s.name, rx+HG_NAME, ry+p.h/2);
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
    // Barrels and volley are read from the mount data. No mount data means no
    // claim about either, rather than a made up one.
    const gn = primaryCount(s.key);
    if(gn){
      ctx.fillStyle=vCol;
      ctx.fillText(String(gn), rx+HG_COLS[4].x, cy);
      ctx.fillText(String(Math.round(volleyTotal(gn))), rx+HG_COLS[5].x, cy);
    }
    const secX = rx+HG_COLS[6].x;
    if(isBomberHull(s.key)) drawBombIcon(secX+10, cy, pCol);
    else                    drawMissileIcon(secX+10, cy, pCol);
    ctx.fillStyle=vCol; ctx.font=thValue(15, false);
    ctx.fillText(String(s.sec), secX+24, cy);

    // Every row swallows its own tap, so a row that cannot be taken cannot
    // close the panel by accident either.
    window._shipRects.push({x:rx, y:ry, w:rw, h:p.h, ship:s.key,
                            key:(open && !p.cur) ? s.key : null});
  }

  ctx.textAlign='center'; ctx.fillStyle=TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText('ESC or tap outside to cancel', mx+L.mw/2, my+L.mh-11);
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
// ── REARM PANEL ──────────────────────────────────────────────
// Same shape as the hangar, because it is the same kind of decision: a list
// of things you may take, with the figures that let you choose between them.
// Built entirely from the surface kit; nothing here invents a shape.
const RM_W        = 660;
const RM_PAD      = 12;
const RM_ROW      = 38;
const RM_ROW_LOCK = 20;
const RM_GAP      = 4;
const RM_HEAD     = 24;
const RM_TITLE    = 34;
const RM_FOOT     = 18;
const RM_GROUPGAP = 14;
const RM_NUM      = 8;
const RM_NUM_W    = 16;
const RM_NAME     = 30;
// Two kinds of weapon, two sets of columns. Both are measured from the row's
// left edge, and the row is RM_W - 2*RM_PAD wide.
const RM_COLS_PRI = [
  {k:'dmg',   x:300, label:'VOLLEY'},
  {k:'rate',  x:366, label:'ROF'},
  {k:'spd',   x:432, label:'SPEED'},
  {k:'range', x:504, label:'REACH'}
];
const RM_COLS_SEC = [
  {k:'dmg',    x:300, label:'DAMAGE'},
  {k:'ammo',   x:366, label:'RACK'},
  {k:'reload', x:432, label:'RELOAD'},
  {k:'spd',    x:504, label:'SPEED'},
  {k:'seek',   x:566, label:'SEEKING'}
];
// What each column actually says for a weapon. Kept beside the columns so a
// new figure is added in one place rather than two.
function rmValue(w, k, pri){
  if(pri){
    if(k==='dmg')   return String(Math.round(VOLLEY_BASE*w.dmg));
    if(k==='rate')  return (Math.round(600/Math.max(5, Math.round(PLAYER_FR_BASE*w.rate)))/10).toFixed(1)+'/s';
    if(k==='spd')   return String(w.spd);
    if(k==='range') return w.range ? String(w.range) : 'FULL';
    return '';
  }
  if(k==='dmg')    return String(w.dmg);
  if(k==='ammo')   return String(Math.max(1, Math.round((shipStats(player.ship).sec||0)*w.ammoMul)));
  if(k==='reload') return (Math.round(w.cd/6)/10).toFixed(1)+'s';
  if(k==='spd')    return String(w.spd);
  if(k==='seek')   return w.homing ? 'YES' : 'NO';
  return '';
}
function rearmGroups(){
  return [{head:'PRIMARY', pri:true,  cols:RM_COLS_PRI, list:PRIMARIES},
          {head:(hullSecCls(player.ship)==='bomb') ? 'BOMBS' : 'MISSILES',
           pri:false, cols:RM_COLS_SEC, list:secondariesFor(player.ship)}];
}
function rearmLayout(){
  const plan = [];
  let h = RM_TITLE, n = 0;
  for(const g of rearmGroups()){
    if(!g.list.length) continue;
    plan.push({head:g.head, y:h, cols:g.cols});
    h += RM_HEAD;
    for(const w of g.list){
      const open = weaponOpen(w);
      const cur  = g.pri ? (w.key===player.pri) : (w.key===player.sec);
      const rh   = open ? RM_ROW : RM_ROW_LOCK;
      plan.push({w:w, y:h, h:rh, cur:cur, open:open, pri:g.pri, cols:g.cols,
                 num:++n});
      h += rh + RM_GAP;
    }
    h += RM_GROUPGAP;
  }
  h += RM_FOOT;
  return {mx:((W-RM_W)/2)|0, my:((H-h)/2)|0, mw:RM_W, mh:h, plan:plan};
}
function drawRearmMenu(){
  if(!rearmMenu) return;
  const L = rearmLayout(), mx = L.mx, my = L.my, rw = L.mw - RM_PAD*2;
  ctx.save();
  thFrame(mx, my, L.mw, L.mh, RM_TITLE);
  window._rearmPanelRect = {x:mx, y:my, w:L.mw, h:L.mh};

  ctx.textBaseline='middle'; ctx.textAlign='left';
  ctx.fillStyle=TH('textBright'); ctx.font=thLabel(14);
  ctx.fillText('REARM', mx+RM_PAD, my+16);
  ctx.textAlign='right';
  ctx.fillStyle=TH('accentWarm'); ctx.font=thValue(10, false);
  ctx.fillText('CORVETTE ON STATION  -  A REFIT FILLS THE RACK',
               mx+L.mw-RM_PAD, my+16);

  window._rearmRects=[];
  for(const p of L.plan){
    const ry = my+p.y, rx = mx+RM_PAD;
    if(p.head !== undefined){
      ctx.textAlign='left';
      ctx.fillStyle=TH('text'); ctx.font=thLabel(11);
      ctx.fillText(p.head, rx, ry+8);
      ctx.fillStyle=TH('textDim'); ctx.font=thLabel(8);
      for(const c of p.cols) ctx.fillText(c.label, rx+c.x, ry+9);
      thScale(rx, ry+15, rw, p.cols.map(function(c){ return c.x; }), TH('edgeLight'));
      continue;
    }
    const w = p.w;
    if(!p.open){
      ctx.textAlign='left'; ctx.fillStyle=TH('textDim'); ctx.font=thValue(11, false);
      ctx.fillText(thFit(weaponName(w), 240), rx+RM_NAME, ry+p.h/2);
      ctx.fillText('unlocks at '+w.unlock.toLocaleString('en-US')+' points',
                   rx+p.cols[0].x, ry+p.h/2);
      window._rearmRects.push({x:rx, y:ry, w:rw, h:p.h, key:null});
      continue;
    }

    thPlate(rx, ry, rw, p.h, p.cur ? TH('raised') : TH('panelFront'));
    if(p.cur){
      thGlowPath(rx, ry, rw, p.h, 6, 1);
      thBrackets(rx, ry, rw, p.h, TH('accentWarm'));
      ctx.fillStyle=TH('accentWarm');
      ctx.fillRect(rx, ry+6, 3, p.h-12);
    }
    drawKeyChip(p.num, rx+RM_NUM, ry+(p.h-16)/2, RM_NUM_W, 16, true);

    // Name on top, what it is for underneath. The note is the part that
    // explains a choice the figures alone would not.
    const textW = p.cols[0].x - RM_NAME - 10;
    ctx.textAlign='left';
    ctx.fillStyle = p.cur ? TH('accentWarm') : TH('textBright');
    ctx.font=thValue(14, true);
    ctx.fillText(thFit(weaponName(w), textW), rx+RM_NAME, ry+13);
    ctx.fillStyle=TH('textDim'); ctx.font=thValue(9, false);
    ctx.fillText(thFit(w.note, textW), rx+RM_NAME, ry+27);

    ctx.fillStyle=TH('textBright'); ctx.font=thValue(15, false);
    for(const c of p.cols) ctx.fillText(rmValue(w, c.k, p.pri), rx+c.x, ry+p.h/2);

    window._rearmRects.push({x:rx, y:ry, w:rw, h:p.h, key:w.key});
  }

  ctx.textAlign='center'; ctx.fillStyle=TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText('ESC or tap outside to cancel', mx+L.mw/2, my+L.mh-11);
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
const CM_W        = 636;
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
  const colw = ((CM_W - CM_PAD*(n+1))/n)|0;
  let rows = 1;
  for(const c of COLS) rows = Math.max(rows, c.length);
  const showCol = allyFacOn(ALLY_DEFS[ALLY_SPECIAL].fac);
  let y = CM_TITLE;
  const headY = y; y += CM_HEAD;
  const rowY  = y; y += rows*(CM_ROW+CM_GAP);
  let colHeadY = 0, colRowY = 0;
  if(showCol){
    y += CM_GROUPGAP;
    colHeadY = y; y += CM_HEAD;
    colRowY  = y; y += CM_ROW + CM_GAP;
  }
  y += CM_FOOT;
  return {mx:((W-CM_W)/2)|0, my:((H-y)/2)|0, mw:CM_W, mh:y,
          COLS:COLS, colw:colw, showCol:showCol,
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
  }
  drawKeyChip(keyLabel, x+CM_NUM, y+(CM_ROW-16)/2, CM_NUM_W, 16, ok);
  drawHullCell(d.spr, x+CM_PIC, y+3, CM_PIC_W, CM_ROW-6, ok);

  // What is left for the name once the count and the refine button have had
  // their share. thFit gets told this number, so nothing can run past it.
  const rightKeep = CM_TICKET_W + (ref ? CM_REFINE_W + 4 : 0) + 8;
  const textW = w - CM_NAME - rightKeep;

  ctx.textAlign='left'; ctx.textBaseline='middle';
  ctx.fillStyle = ok ? TH('textBright') : TH('textDim');
  ctx.font = thValue(13, true);
  ctx.fillText(thFit(d.label, textW), x+CM_NAME, y+13);

  let sub;
  if(d.colossus)                sub = COLOSSUS_TIME+' s on station, then she jumps out';
  else if(d.cls==='destroyer')  sub = 'DESTROYER  -  HULL '+capHull(HULL[d.cls])+'  -  WINGS';
  else                          sub = d.cls.toUpperCase()+'  -  HULL '+capHull(HULL[d.cls]);
  ctx.fillStyle = TH('textDim'); ctx.font = thValue(9, false);
  ctx.fillText(thFit(sub, textW), x+CM_NAME, y+27);

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
    const cx = mx + CM_PAD, cw = L.mw - CM_PAD*2;
    ctx.textAlign='left';
    ctx.fillStyle=TH('text'); ctx.font=thLabel(11);
    ctx.fillText(CM_FAC_HEAD.gtva, cx, my+L.colHeadY+7);
    thScale(cx, my+L.colHeadY+14, cw, [CM_PIC, CM_NAME], TH('edgeLight'));
    drawAllyRow(cx, my+L.colRowY, cw, ALLY_SPECIAL, cd, ALLY_SPECIAL_KEY, true);
  }

  ctx.textAlign='center'; ctx.fillStyle=TH('textDim');
  ctx.font=thValue(10, false);
  ctx.fillText('ESC or tap outside to cancel', mx+L.mw/2, my+L.mh-11);
  ctx.restore();
  ctx.textAlign='left'; ctx.textBaseline='top';
}


function setCallMenu(open){
  if(!open && callMenu) holdResume();
  callMenu = open;
  if(open) shipMenu = false;
  syncPause();
  if(!open && GS==='playing'){ MOUSE.x = player.x; MOUSE.y = player.y; }
  syncCursor();
}

function toggleCallMenu(){
  if(callMenu){ setCallMenu(false); return; }
  if(empOut>0) return;              // the storm has the radio
  if(!allyReady()) return;
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
      if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){ if(r.key) fitWeapon(r.key); return true; }
    if(insidePanel(window._rearmPanelRect, p)) return true;
    setRearmMenu(false); return true;
  }
  if(shipMenu){
    for(const r of (window._shipRects||[]))
      if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){ if(r.key) swapShip(r.key); return true; }
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
          if(cr.refine){ refineTicket(cr.refine); return true; }
          callAlly(cr.id); return true;
        }
      }
    }
    if(insidePanel(window._callPanelRect, p)) return true;
    setCallMenu(false); return true;
  }
  var ra=window._allyBtnRect;
  if(ra&&p.x>=ra.x&&p.x<=ra.x+ra.w&&p.y>=ra.y&&p.y<=ra.y+ra.h){ toggleCallMenu(); return true; }
  return false;
}





// From the title a run starts; from a finished run you go back to the
// title first. Reading your score and then being dropped into the next
// wave in the same breath left no moment to stop.
function toTitleOrLaunch(){
  if(GS==='gameover'){ enterTitle(); return; }
  launchGame();
}
// A fresh sky every time the title comes up: another backdrop, another
// set of bodies.
function enterTitle(){
  GS='title';
  resumeHold=false; userPaused=false; paused=false;
  nebCur = NEB_NAMES[(Math.random()*NEB_NAMES.length)|0];
  nebFading = false; nebAlpha = 1.0;
  rollBodies();
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
  if(ev.button===0&&GS==='playing'){
    var p=toGC(ev.clientX,ev.clientY);
    if(pointerConsumed(p)) return;
    // The settings panel eats the tap before anything else can react to it,
    // or opening it would also fire a weapon underneath.
    if(settingsOpen){ settingsClick(p.x,p.y); return; }
    if(window._settingsBtnRect){var rs=window._settingsBtnRect;if(p.x>=rs.x&&p.x<=rs.x+rs.w&&p.y>=rs.y&&p.y<=rs.y+rs.h){setSettings(true);return;}}
    if(window._pauseBtnRect){var r=window._pauseBtnRect;if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){userPaused=!userPaused;syncPause();return;}}
    if(window._secBtnRect){var r2=window._secBtnRect;if(p.x>=r2.x&&p.x<=r2.x+r2.w&&p.y>=r2.y&&p.y<=r2.y+r2.h){fireSecondary();return;}}
    if(p.y<HUD_H) return; // HUD area, no movement input
  }
  if(ev.button!==0&&ev.button!==2) return;
  var p=toGC(ev.clientX,ev.clientY);
  MOUSE.x=p.x; MOUSE.y=p.y;
  if(ev.button===0){
    isFiring=true; MOUSE.down=true;
    if(GS==='title'||GS==='gameover'){ if(GS==='title'||performance.now()-gameOverAt>1500) toTitleOrLaunch(); }
  }
  if(ev.button===2&&GS==='playing') fireSecondary();
});
CVS.addEventListener('mouseup',function(ev){
  if(ev.button===0){isFiring=false;MOUSE.down=false;}
});
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
  if(pointerConsumed(p)) return;
  // HUD area: button check only, no movement input
  if(p.y<HUD_H&&GS==='playing'){
    // The settings panel eats the tap before anything else can react to it,
    // or opening it would also fire a weapon underneath.
    if(settingsOpen){ settingsClick(p.x,p.y); return; }
    if(window._settingsBtnRect){var rs=window._settingsBtnRect;if(p.x>=rs.x&&p.x<=rs.x+rs.w&&p.y>=rs.y&&p.y<=rs.y+rs.h){setSettings(true);return;}}
    if(window._pauseBtnRect){var r=window._pauseBtnRect;if(p.x>=r.x&&p.x<=r.x+r.w&&p.y>=r.y&&p.y<=r.y+r.h){userPaused=!userPaused;syncPause();return;}}
    if(window._secBtnRect){var r2=window._secBtnRect;if(p.x>=r2.x&&p.x<=r2.x+r2.w&&p.y>=r2.y&&p.y<=r2.y+r2.h){fireSecondary();return;}}
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
    if(window._secBtnRect){var r2=window._secBtnRect;if(p.x>=r2.x&&p.x<=r2.x+r2.w&&p.y>=r2.y&&p.y<=r2.y+r2.h){fireSecondary();return;}}
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
},{passive:false});

function secBtnDown(ev){if(ev)ev.preventDefault();if(GS==='playing')fireSecondary();}
function secBtnUp(ev){if(ev)ev.preventDefault();}
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
  // S opens and closes the panel, Escape closes it before it reaches pause.
  if(ev.code==='KeyS' && !callMenu && !shipMenu && GS==='playing'){
    setSettings(!settingsOpen); ev.preventDefault(); return;
  }
  if(settingsOpen && ev.code==='Escape'){ setSettings(false); ev.preventDefault(); return; }
  if(ev.code==='KeyF' && GS==='playing'){
    toggleFullscreen(); ev.preventDefault(); return;
  }
  if((ev.code==='KeyP'||ev.code==='Escape')&&GS==='playing'){
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
  if(ev.code==='KeyR'){ toggleRearmMenu(); ev.preventDefault(); return; }
  if(rearmMenu){
    if(ev.code==='Escape'){ setRearmMenu(false); ev.preventDefault(); return; }
    var rd = ev.code.indexOf('Digit')===0 ? ev.code.slice(5)
           : (ev.code.indexOf('Numpad')===0 ? ev.code.slice(6) : '');
    var ri = parseInt(rd,10);
    // The panel numbers its rows straight down, so the digit beside a
    // weapon is the digit that fits it.
    if(ri>=1){
      for(const q of rearmLayout().plan)
        if(q.num===ri && q.open){ fitWeapon(q.w.key); break; }
      ev.preventDefault();
    }
    return;
  }
  if(shipMenu){
    if(ev.code==='Escape'){ setShipMenu(false); ev.preventDefault(); return; }
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
  try{drawResumeHint();}catch(e){}
  try{drawCtxNotice();}catch(e){}
})();
