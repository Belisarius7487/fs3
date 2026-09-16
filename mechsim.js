
// ── Attrappe ──
let enemies=[], allies=[], SUB_MSGS=[], EV_DOCK={};
const W=800,H=500,HUD_H=44;
const RAM_PCT_CAPITAL=0.34, DOCK_SPD=0.55, DOCK_NEAR=22;
const IMGS={
  crmentu:{width:116,height:44}, dehatshepsut:{width:391,height:150},
  frbast:{width:60,height:26}, fcvc3:{width:30,height:22},
  trisis:{width:60,height:24}, craten:{width:111,height:40}
};
const MOUNTS={ fcvc3:{docks:[{dx:0.0,dy:-0.9}]}, dehatshepsut:{docks:[{dx:0.2,dy:-0.7}]} };
function mountsFor(k){ return MOUNTS[k]||null; }
function byId(id){ const o=[]; for(const e of enemies) if(e.uid===id&&!e.dead) o.push(e);
  for(const a of allies) if(a.uid===id&&!a.dead) o.push(a); return o; }
function hullHit(){} function triggerExpl(){} function spawnShock(){}
let impact=false;
function dockPoint(o){
  const m = mountsFor(o.img), img = IMGS[o.img];
  if(!m || !m.docks || !m.docks.length || !img) return {x:o.x, y:o.y};
  const d = m.docks[0];
  const s = o.flip ? -1 : 1;
  return {x:o.x + (img.width*o.sc*0.5)*d.dx*s,
          y:o.y + (img.height*o.sc*0.5)*d.dy};
}
function tickDocking(){
  const all = enemies.concat(allies);
  for(const e of all){
    if((!e.dockTo && !e.dockedTo) || e.dead || e.warp>0) continue;
    if(e.dockedTo){
      // Angedockt: die Fracht faehrt mit.
      const c = e.dockedTo;
      if(c.dead){ e.dockedTo=null; continue; }
      c.x = e.x + (e.cargoDX||0);
      c.y = e.y + (e.cargoDY||0);
      continue;
    }
    const t = byId(e.dockTo)[0];
    if(!t) continue;
    const p = dockPoint(t);
    const dx = p.x-e.x, dy = p.y-e.y, L = Math.hypot(dx,dy)||1;
    if(L > DOCK_NEAR){
      e.x += dx/L*DOCK_SPD*1.6;
      e.y += dy/L*DOCK_SPD;
      e.vx = 0; e.vy = 0;
      continue;
    }
    // Angedockt.
    EV_DOCK[e.uid] = true;
    SUB_MSGS.push({x:e.x, y:e.y-28, txt:'DOCKED', life:150, ml:150,
                   ally:true, tone:'good'});
    if(t.type==='container'){
      // Die Fracht haengt ab jetzt am Traeger.
      e.dockedTo = t; e.cargoDX = 0; e.cargoDY = 26;
      t.carried = true; t.guard = false; t.scenery = true;
      e.hasCargo = true;
    }
    e.dockTo = null;
    // Erst laden, dann abfahren.
    if(e.crossAfter) e.crossing = e.crossAfter;
  }
}
function tickCapRam(){
  for(let i=enemies.length-1;i>=0;i--){
    const e = enemies[i];
    if(!e.capRam || e.dead || e.warp>0 || e.rollT!=null) continue;
    let t=null, bd=1e9;
    for(const a of allies){
      if(a.dead || a.small) continue;
      const d=(a.x-e.x)*(a.x-e.x)+(a.y-e.y)*(a.y-e.y);
      if(d<bd){ bd=d; t=a; }
    }
    if(!t) continue;
    // Direkter Kurs, ohne Halteposition - er will nicht schiessen.
    e.targetX = null;
    const dx=t.x-e.x, dy=t.y-e.y, L=Math.hypot(dx,dy)||1;
    // Senkrecht zuegiger als waagerecht: sonst kriecht er die Hoehe hoch
    // und ist laengst da, bevor er auf Hoehe ist.
    e.x += dx/L*e.capRam;
    e.y += dy/L*e.capRam*3.4;
    const ei=IMGS[e.img], ti=IMGS[t.img];
    const hwA=(ei?ei.width*e.sc:100)*0.5,  hwB=(ti?ti.width*t.sc:100)*0.5;
    const hhA=(ei?ei.height*e.sc:40)*0.5,  hhB=(ti?ti.height*t.sc:40)*0.5;
    // Waagerecht und senkrecht getrennt pruefen: ein Kreis laesst ihn
    // hoch ueber dem Ziel explodieren, weil der Abstand dort auch klein ist.
    if(Math.abs(dx) < (hwA+hwB)*0.62 && Math.abs(dy) < (hhA+hhB)*0.62){
      t.hp -= Math.max(1, Math.round((t.maxHp||100)*RAM_PCT_CAPITAL));
      hullHit(e.x, e.y);
      triggerExpl(e.x, e.y, 'destroyer', e.faction, e);
      spawnShock(e.x, e.y, 170, 3.0, 0.024);
      SUB_MSGS.push({x:e.x, y:e.y-40, txt:'IMPACT', life:150, ml:150, ally:false});
      e.dead = true; e.hp = 0;
      enemies.splice(i,1);
    }
  }
}
// ── Test 1: Rammkreuzer trifft aus jeder Starthoehe ──
let ok=0, fail=[];
for(const startY of [60,120,180,250,320,400,460]){
  enemies=[{uid:'V1',img:'crmentu',x:820,y:startY,sc:1,capRam:0.05,dead:false,warp:0,
            minY:HUD_H+10,maxY:H-10,rollT:null}];
  allies=[{uid:'A1',img:'dehatshepsut',x:560,y:250,sc:1,small:false,dead:false,
           hp:6500,maxHp:6500,vy:0,minY:250,maxY:250}];
  let hit=false;
  for(let f=0; f<9000 && !hit; f++){
    tickCapRam();
    if(enemies.length===0) hit=true;
  }
  if(hit && allies[0].hp < 6500) ok++;
  else fail.push(startY);
}
console.log('Rammkreuzer trifft aus 7 Starthoehen:', ok+'/7', fail.length?('daneben bei y='+fail.join(', ')):'');

// ── Test 2: Frachter dockt am Container an und traegt ihn ──
enemies=[];
allies=[
  {uid:'C1',img:'fcvc3',x:120,y:250,sc:1,type:'container',dead:false,warp:0},
  {uid:'F1',img:'frbast',x:-40,y:300,sc:1,dead:false,warp:0,dockTo:'C1',crossAfter:0.38}
];
let docked=false;
for(let f=0;f<9000 && !docked;f++){ tickDocking(); if(EV_DOCK['F1']) docked=true; }
const f1=allies[1];
console.log('Frachter dockt an:', docked?'ja':'NEIN',
            '| traegt Fracht:', f1.dockedTo?'ja':'NEIN',
            '| faehrt danach ab:', f1.crossing?'ja':'NEIN');
// Fracht folgt dem Traeger
if(f1.dockedTo){ f1.x+=100; tickDocking();
  console.log('Fracht folgt:', Math.abs(allies[0].x-(f1.x+(f1.cargoDX||0)))<0.5?'ja':'NEIN'); }

// ── Test 3: Transporter dockt an einem Zerstoerer an ──
enemies=[];
allies=[
  {uid:'A1',img:'dehatshepsut',x:520,y:250,sc:1,type:'destroyer',dead:false,warp:0},
  {uid:'T1',img:'trisis',x:-40,y:180,sc:1,dead:false,warp:0,dockTo:'A1'}
];
EV_DOCK={}; docked=false;
for(let f=0;f<9000 && !docked;f++){ tickDocking(); if(EV_DOCK['T1']) docked=true; }
console.log('Transporter dockt am Zerstoerer an:', docked?'ja':'NEIN',
            '| traegt nichts:', allies[1].dockedTo?'FEHLER':'richtig');
