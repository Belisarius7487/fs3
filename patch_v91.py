#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v90 -> v91: zehn Fehler, Rammstoss, Anflugzeichen, Zielvorliebe."""
import io, os, sys
SRC="hlp_shooter_v90_logic.html"; DST="hlp_shooter_v91_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── 1  Eine Staffel, ein Rumpf ───────────────────────────────
# Ich habe je Schiff einen Eintrag mit leerem Rumpf geschoben, und mkEnemy
# wuerfelt dann fuer jedes einzeln. Der Wurf gehoert auf die Staffel.
sub("wing-hull",
"""      for(let w=0; w<n; w++){
        const wid = ++wingSeq;
        const sz  = WING_MIN + ((Math.random()*(WING_MAX-WING_MIN+1))|0);
        const yy  = (u.y!=null) ? u.y : H*(0.22+0.5*((w+0.5)/n));
        for(let k=0;k<sz;k++)
          put({time:t0 + w*260 + k*WING_STAGGER,
               type: ally ? 'allyfi' : ty, spr:u.spr||'', wing:ally?0:wid,
               y: yy + (k-(sz-1)/2)*WING_SPACING*0.5, x:u.x});
      }""",
"""      for(let w=0; w<n; w++){
        const wid = ++wingSeq;
        const sz  = WING_MIN + ((Math.random()*(WING_MAX-WING_MIN+1))|0);
        const yy  = (u.y!=null) ? u.y : H*(0.22+0.5*((w+0.5)/n));
        // Eine Staffel fliegt einen Rumpf. Der Wurf gehoert hierher und
        // nicht in mkEnemy, sonst bekommt jedes Schiff einen eigenen.
        const pool = ally
          ? (fac==='hol' ? ROLES.ally_vas_fighters : ROLES.ally_ter_fighters)
          : poolFor(ty);
        const hull = u.spr || (pool ? rnd(pool) : '');
        // Staffelabstand: 2,6 s waren im Spiel eine Pause, in der nichts
        // passiert. 1,1 s reichen, um sie als getrennte Staffeln zu lesen.
        for(let k=0;k<sz;k++)
          put({time:t0 + w*110 + k*WING_STAGGER,
               type: ally ? 'allyfi' : ty, spr:hull, wing:ally?0:wid,
               y: yy + (k-(sz-1)/2)*WING_SPACING*0.5, x:u.x});
      }""")

# ── 2  Stehendes Zeug steht von Anfang an ────────────────────
sub("static-now",
"""    if(ally && fix!=='ast')
      put({time:t0+i*90, type:'protect', spr:u.spr, fac:'vasudan', noWarp:1,
           x:xx, y:yy, cross:u.cross});
    else
      put({time:t0+i*60, type:fix, spr:u.spr||'', fac:fac, noWarp:(fix!=='ast')?1:0,
           x:xx, y:yy, scan:u.scan?1:0});""",
"""    // Geschuetze, Container und Brocken stehen seit Wellenbeginn im Feld -
    // sie muessen auch sofort da sein und nicht ueber Sekunden eintropfen.
    const stagger = (fix==='ast') ? 10 : 0;
    if(ally && fix!=='ast')
      put({time:t0+i*70, type:'protect', spr:u.spr, fac:'vasudan', noWarp:1,
           x:xx, y:yy, cross:u.cross});
    else
      put({time:t0+i*stagger, type:fix, spr:u.spr||'', fac:fac, noWarp:(fix!=='ast')?1:0,
           x:xx, y:yy, scan:u.scan?1:0});""")

# ── 7  Ueberlaeufer stand in beiden Listen ───────────────────
# defect() schob das Schiff nach enemies, ohne es aus allies zu nehmen.
# Es wurde danach zweimal je Bild bewegt: doppelte Geschwindigkeit und
# zuckendes Flugverhalten. Betrifft jeden Ueberlaeufer, auch den alten.
sub("defect-splice",
"""function defect(a){
  a.side = 'enemy';""",
"""function defect(a){
  const _i = allies.indexOf(a);
  if(_i >= 0) allies.splice(_i, 1);    // sonst steht es in beiden Listen
  a.side = 'enemy';""")

# ── 10  Funkmeldung nur bei zerstoertem Funkraum ─────────────
# enemyRadioAlive() lieferte auch dann "kein Funk", wenn ueberhaupt kein
# Grosskampfschiff mehr lebte - die Meldung kam beim letzten Abschuss.
sub("comms-alive",
"""function tickComms(){
  if(commsCut) return;
  if(enemyRadioAlive()){ commsSeen = true; return; }""",
"""// Lebt noch ein Grosskampfschiff? Ohne eines gibt es keinen Funkraum, der
// zerstoert sein koennte - dann ist die Welle vorbei und nicht der Funk.
function enemyCapAlive(){
  for(const e of enemies)
    if(!e.dead && e.warp<=0 && hasSubsystems(e)) return true;
  return false;
}
function tickComms(){
  if(commsCut) return;
  if(enemyRadioAlive()){ commsSeen = true; return; }
  if(!enemyCapAlive()) return;""")

# ── 8  anzahlUnter darf nicht feuern, bevor alles da ist ─────
sub("anzahl-wait",
"""    case 'anzahlUnter':  return evSeen(ev.a) && byId(ev.a).length < (ev.b||1);""",
"""    case 'anzahlUnter':
      // Erst wenn nichts mehr fuer diese Kennung in der Warteschlange
      // steht. Sonst feuert der Ausloeser, waehrend noch eingesetzt wird:
      // der erste Container ist einer, und einer ist weniger als drei.
      if(!evSeen(ev.a)) return false;
      for(const q of spawnQ) if(q.uid===ev.a) return false;
      return byId(ev.a).length < (ev.b||1);""")

# ── 6  Zielvorliebe: Jaeger gehen nicht nur auf den Spieler ──
# smallTarget() endet fuer Gegner mit "return player" - nur Bomber suchen
# sich Verbuendete. In einer Schuetzlingswelle mit reinen Jaegern ist der
# Schuetzling deshalb nie in Gefahr.
sub("hunt-var",
"""let waveObj = 'clear';""",
"""let waveObj = 'clear';
// Kennung, auf die gegnerische Jaeger es abgesehen haben. Ohne sie zielen
// sie ausschliesslich auf den Spieler, und ein Schuetzling ist nie in
// Gefahr. HUNT_SHARE ist der Anteil der Jaeger, der auf das Ziel geht -
// nicht alle, sonst steht der Spieler unbehelligt daneben.
let waveHunt = '';
const HUNT_SHARE = 0.5;""")

sub("hunt-target",
"""  e.focusOn=null;
  return player;
}

// Hands out the attack slots.""",
"""  // Jaeger mit Auftrag gehen auf ihr Ziel, solange es lebt.
  if(waveHunt && e.hunter){
    const h = byId(waveHunt)[0];
    if(h){ e.focusOn=null; return h; }
  }
  e.focusOn=null;
  return player;
}

// Hands out the attack slots.""")

sub("hunt-assign",
"""applySpawnOpts(_e,_sp);_e.uid=_sp.uid;if(_sp.uid)EV_SEEN[_sp.uid]=true;enemies.push(_e);}}""",
"""applySpawnOpts(_e,_sp);_e.uid=_sp.uid;if(_sp.uid)EV_SEEN[_sp.uid]=true;_e.hunter=(waveHunt&&Math.random()<HUNT_SHARE);enemies.push(_e);}}""")

sub("hunt-set",
"""  for(const u of (def.u||[])) scriptUnit(u, def.fac, q);""",
"""  waveHunt = def.hunt || '';
  for(const u of (def.u||[])) scriptUnit(u, def.fac, q);""")

sub("hunt-clear",
"""  waveFeud    = (o==='feud');
  waveObj     = o;""",
"""  waveFeud    = (o==='feud');
  waveObj     = o;
  waveHunt    = '';""")

# ── 4  Rammstoss, Anflugzeichen, eigene Explosion ────────────
# Der Anflug fliegt seit jeher durch das Ziel hindurch - der Kommentar im
# Code nennt den Grund: ueber dem Ziel abzubremsen liess alles verklumpen.
# Das sieht aus wie ein Rammstoss, war aber folgenlos. Jetzt ist es einer.
sub("ram-const",
"""const ATTACK_BREAK = 55;     // distance at which a run counts as delivered""",
"""// Rammstoss. Ein Bomber traegt Bomben, deshalb reisst er ein Loch und
// stirbt dabei selbst. Der Wert ist ein Anteil des Ziels, nicht fest:
// sonst waere derselbe Stoss gegen einen Kreuzer toedlich und gegen einen
// Zerstoerer wirkungslos.
const RAM_PCT_BOMBER  = 0.09;
const RAM_PCT_FIGHTER = 0.04;
const RAM_DIST = 26;         // ab hier gilt es als Treffer, nicht als Anflug
const ATTACK_BREAK = 55;     // distance at which a run counts as delivered""")

sub("ram-tick",
"""function tickEvents(){""",
"""// Ein Schiff im Anflug, das sein Ziel wirklich beruehrt, schlaegt ein.
// Geprueft wird gegen das Ziel, das es sich gesucht hat - nicht gegen
// alles, sonst rammt ein Bomber auf dem Rueckweg seinen eigenen Fluegelmann.
function tickRamming(){
  for(let i=enemies.length-1;i>=0;i--){
    const e = enemies[i];
    if(e.dead || e.warp>0 || e.warpOut>0) continue;
    if(e.type!=='fighter' && e.type!=='bomber') continue;
    if(e.role!=='attack' || e.passT>0) continue;
    const t = smallTarget(e);
    if(!t || t===e) continue;
    const d = Math.hypot(t.x-e.x, t.y-e.y);
    if(d > RAM_DIST) continue;
    const pct = (e.type==='bomber') ? RAM_PCT_BOMBER : RAM_PCT_FIGHTER;
    if(t===player){
      const dm = Math.max(1, Math.round(player.maxHp*pct));
      if(player.sh>0){ const abs=Math.min(player.sh,dm); player.sh-=abs;
        player.shDelay=90; player.shHit=SH_FLASH; shieldHit(e.x,e.y);
        if(dm>abs){ player.hp-=dm-abs; hullHit(e.x,e.y); } }
      else { player.hp-=dm; hullHit(e.x,e.y); }
      if(player.hp<=0) playerDie();
    } else {
      const dm = Math.max(1, Math.round((t.maxHp||100)*pct));
      t.hp -= dm; hullHit(e.x, e.y);
    }
    ramBlast(e);
  }
}
// Eigene Explosion: da geht ein Schiff mit Bomben an Bord hoch. Groesser
// als der uebliche Bombertod, mit Ring und heller Mitte.
function ramBlast(e){
  // Korvettenprofil statt Bomberprofil: da geht Munition mit hoch.
  triggerExpl(e.x, e.y, 'corvette', e.faction, e);
  spawnShock(e.x, e.y, 118, 2.0, 0.015);
  addShake(4, 18);
  for(let k=0;k<26;k++){
    const a = Math.random()*Math.PI*2, s = 1.6+Math.random()*3.4;
    PARTS.push({x:e.x, y:e.y, vx:Math.cos(a)*s, vy:Math.sin(a)*s,
                life:(22+Math.random()*22)|0, ml:0, sz:1.4+Math.random()*1.8,
                clr:(k%3===0)?'#ffffff':'#ffcc44'});
  }
  e.dead = true; e.hp = 0;
}

function tickEvents(){""")

sub("ram-call",
"""  tickComms();
  tickEvents();""",
"""  tickComms();
  tickRamming();
  tickEvents();""")

# Anflugzeichen statt des roten Winkels, solange ein Schiff im Anflug ist
sub("attack-mark",
"""  const img = IMGS[e.img];
  const h = img ? img.height*e.sc : 30;
  const y = e.y - h*0.5 - 9;
  ctx.save();
  ctx.globalAlpha = a;
  ctx.strokeStyle = '#ff2a1a';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(e.x-6, y-5); ctx.lineTo(e.x, y); ctx.lineTo(e.x+6, y-5);
  ctx.stroke();
  ctx.restore();""",
"""  const img = IMGS[e.img];
  const h = img ? img.height*e.sc : 30;
  const y = e.y - h*0.5 - 9;
  // Im Anflug ein anderes Zeichen: ein Schiff, das gleich einschlaegt,
  // soll sich von einem unterscheiden, das nur vorbeifliegt. In FreeSpace
  // warnt der Funk davor - hier muss es das Bild tun.
  const run = (e.role==='attack' && e.passT<=0);
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
  ctx.restore();""")

# ── 3, 5, 9  Missionszeiten und Ausloeser ────────────────────
sub("m006-time","""       {id:'B1', c:'bo', n:1, t:40}""","""       {id:'B1', c:'bo', n:1, t:14}""")
sub("m008-time","""       {id:'B2', c:'bo', n:2, t:35}""","""       {id:'B2', c:'bo', n:2, t:16}""")
sub("m013-time","""       {id:'E2', c:'fi', n:1, t:30}""","""       {id:'E2', c:'fi', n:1, t:18}""")
# M016: der Seitenwechsel hing an Sekunde 35, die Welle war nach zehn
# vorbei. Er gehoert an das Gefecht - wenn die Haelfte der Gegner faellt.
sub("m016-trigger",
"""       {t:'sek', a:35, w:'meldung', a2:'escort turning hostile'},
       {t:'sek', a:35, w:'seite', a2:'A2'}""",
"""       {t:'anzahlUnter', a:'E1', b:4, w:'meldung', a2:'escort turning hostile'},
       {t:'anzahlUnter', a:'E1', b:4, w:'seite', a2:'A2'}""")
# M013 bekommt die Zielvorliebe: ohne sie sind die Transporter nie in Gefahr.
sub("m013-hunt","""  13:{name:'Die Transporter', fac:'hol', o:'protect', live:4, u:[""",
"""  13:{name:'Die Transporter', fac:'hol', o:'protect', live:4, hunt:'T1', u:[""")

def main():
    if not os.path.exists(SRC): sys.exit("FEHLT: "+SRC)
    txt=io.open(SRC,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(DST,"w",encoding="utf-8").write(txt)
    print("geschrieben: "+DST)
main()
