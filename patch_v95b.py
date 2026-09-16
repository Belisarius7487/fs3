#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v95 Teil B: Installationen als Klasse, Himmel ueber Wellen halten."""
import io, os, sys
F="hlp_shooter_v95_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── Installationen ──────────────────────────────────────────
# Arcadia, Knossos, Comm Node, Pharos: gepflegt in der Mountdatei, bisher
# von nichts erzeugt. Sie stehen, sie warpen nicht, und sie koennen
# unverwundbar sein - eine Station, die der Spieler halten soll, ist ein
# Ort und kein Gegner.
sub("inst-list",
"""const CAT_FIX = {sg:'sentry',""",
"""// ROLES wird vom Packer erzeugt und kennt keine Installationen.
const INSTALLATIONS = ['inarcadia','incommnode','inpharos'];
const CAT_FIX = {sg:'sentry',""")

sub("inst-branch",
"""  if(type==='ast'){""",
"""  if(typeRole(type)==='in'){
    const spr=spr0 || rnd(INSTALLATIONS);
    const img=IMGS[spr];
    const sc=hullScale(spr,1.0);
    const ent={type:'station',img:spr,faction:typeFac(type),
      pts:1500,x:W*0.80,y:H*0.5,warpX:W*0.80,warpY:H*0.5,
      targetX:null,
      hp:capHull(HULL.destroyer*1.6),maxHp:capHull(HULL.destroyer*1.6),
      vx:0,vy:0,minY:H*0.5,maxY:H*0.5,
      fT:90,fR:80,pat:0,dead:false,sc,warp:0,warpMax:1,station:true};
    initSubsystems(ent); initBeams(ent); return ent;
  }
  if(type==='ast'){""")

sub("inst-hull",
"""  boss_sh: 15000,    // vorher 2800""",
"""  boss_sh: 15000,    // vorher 2800
  station: 10400,    // Installation: 1,6 mal ein Zerstoerer""")
sub("inst-hull-use",
"""      hp:capHull(HULL.destroyer*1.6),maxHp:capHull(HULL.destroyer*1.6),""",
"""      hp:capHull(HULL.station),maxHp:capHull(HULL.station),""")

# Subsystemanteil und Waffenprofil, sonst fallen sie auf Rueckfallwerte
sub("inst-subfrac",
"""const SUB_HP_FRAC = {cruiser:0.22, corvette:0.16, destroyer:0.10, boss:0.20};""",
"""const SUB_HP_FRAC = {cruiser:0.22, corvette:0.16, destroyer:0.10, boss:0.20,
                     station:0.09};""")
# Unverwundbar, halb im Bild, Teilnahme am Wellenende
sub("inst-opts",
"""  if(sp.scenery) e.scenery = true;""",
"""  if(sp.scenery) e.scenery = true;
  // Eine Station, die der Spieler halten soll, ist ein Ort und kein Ziel.
  // Unverwundbar heisst hier: sie nimmt keinen Schaden und zaehlt nicht
  // fuer das Wellenende - sonst waere jede Welle mit ihr unbeendbar.
  if(sp.invuln){ e.invuln = true; e.scenery = true; }
  // Halb ausserhalb des Feldes: eine Arcadia ist groesser als der Schirm,
  // und das soll man sehen.
  if(sp.edge){
    const _ii = IMGS[e.img];
    const _iw = _ii ? _ii.width*e.sc : 400;
    e.x = W + _iw*(sp.edge-0.5); e.warpX = e.x;
  }""")
sub("inst-invuln",
"""  e.hp -= dmg;""",
"""  if(e.invuln) return;      // Station, die nicht fallen soll
  e.hp -= dmg;""")

# Kategorie und Verbuendetenseite
sub("inst-cat",
"""const CAT_FIX = {sg:'sentry', fc:'container', fr:'freighter', tr:'freighter', ast:'ast'};
const CAT_FAC = {fi:1, bo:1, cr:1, co:1, de:1};""",
"""const CAT_FIX = {sg:'sentry', fc:'container', fr:'freighter', tr:'freighter', ast:'ast'};
const CAT_FAC = {fi:1, bo:1, cr:1, co:1, de:1, in:1};""")

# Installationen durchreichen: Ort, Rand, Unverwundbarkeit
sub("inst-q",
"""          : {time:t0+i*140, type:ty, spr:u.spr||'', y:yy, x:u.x, escape:u.escape,""",
"""          : {time:t0+i*140, type:ty, spr:u.spr||'', y:(u.c==='in'?(u.y!=null?u.y:H*0.5):yy),
             x:u.x, escape:u.escape, invuln:u.invuln, edge:u.edge,""")

# Kein Himmelpatch: rollBodies() laeuft nur beim Start des Durchgangs,
# der Himmel bleibt also ueber alle Wellen gleich. M010 und M011 teilen ihn
# bereits - ein Wurf je Welle haette das erst kaputtgemacht.

def main():
    txt=io.open(F,encoding="utf-8").read()
    for t,a,b in edits:
        n=txt.count(a)
        if n!=1: sys.exit("ABBRUCH %s: %d Treffer statt 1"%(t,n))
        txt=txt.replace(a,b,1); print("  ok   "+t)
    io.open(F,"w",encoding="utf-8").write(txt)
    print("Teil B geschrieben")
main()
