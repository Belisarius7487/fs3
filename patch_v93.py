#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v92 -> v93: vier weitere Missionen, zwei Vokabeln dafuer."""
import io, os, sys
SRC="hlp_shooter_v92_logic.html"; DST="hlp_shooter_v93_logic.html"
edits=[]
def sub(t,a,b): edits.append((t,a,b))

# ── Querung fuer verbuendete Grosskampfschiffe aus einer geschriebenen
#    Mission. Die Mechanik gibt es (a.transit / transitV / transitEnd), sie
#    liess sich bisher nur ueber den Wellenplan setzen.
sub("ally-transit",
"""      if(_sp.type==='ally'){
        const _a = mkAlly(_sp.allyId);
        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;""",
"""      if(_sp.type==='ally'){
        const _a = mkAlly(_sp.allyId);
        if(_a && _sp.crossSecs){
          // Fahrt aus der Querungszeit, damit Uhr und Bild dasselbe sagen:
          // ihre Position IST der Fortschrittsbalken.
          _a.guard = true;
          _a.x = -20;  _a.warpX = _a.x;  _a.warp = 0;
          _a.transit = true;
          const _gi = IMGS[_a.img];
          const _gh = _gi ? _gi.width*_a.sc*0.5 : 120;
          _a.transitEnd = W - _gh - TRANS_EDGE_PAD;
          _a.transitV = (_a.transitEnd - _a.x) / (_sp.crossSecs*TICK_HZ);
          _a.flip = needsFlip(_a.img, false);
          guardWanted = true; guardSpawned = true;
        }
        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;""")

sub("ally-transit-q",
"""        put(ally
          ? {time:t0+i*140, type:'ally', allyId:ALLY_ID[u.spr]||'vas_aten', spr:u.spr}""",
"""        put(ally
          ? {time:t0+i*140, type:'ally', allyId:ALLY_ID[u.spr]||'vas_aten', spr:u.spr,
             crossSecs:u.crossSecs}""")

# Die Welle endet, wenn der Querende drueben ist - nicht wenn das Feld leer
# ist. guardGone setzt die vorhandene Mechanik bereits.
sub("script-endcond",
"""  waveHunt = def.hunt || '';
  astStill = !!def.stillRocks;""",
"""  waveHunt = def.hunt || '';
  astStill = !!def.stillRocks;
  // Eine geschriebene Querung endet, wenn der Schuetzling drueben ist.
  transitSecs = def.crossEnds ? 1 : 0;""")

# ── Rammende Jaeger, wo die Mission es sagt. Bomber rammen von selbst,
#    Jaeger nur auf Ansage - sonst wird aus jedem Gefecht ein Wettflug.
sub("rammer-flag",
"""    if(e.type!=='bomber') continue;              // nur Bomber rammen""",
"""    if(e.type!=='bomber' && !e.rammer) continue;  // Jaeger nur auf Ansage""")
sub("rammer-set",
"""_e.hunter=(waveHunt&&Math.random()<HUNT_SHARE);enemies.push(_e);}}""",
"""_e.hunter=(waveHunt&&Math.random()<HUNT_SHARE);_e.rammer=!!_sp.rammer;enemies.push(_e);}}""")
sub("rammer-q",
"""               y: yy + (k-(sz-1)/2)*WING_SPACING*0.5, x:u.x});""",
"""               y: yy + (k-(sz-1)/2)*WING_SPACING*0.5, x:u.x, rammer:u.ram});""")
sub("rammer-mark",
"""  if(e.type==='bomber' && e.role==='attack' && e.passT<=0){""",
"""  if((e.type==='bomber'||e.rammer) && e.role==='attack' && e.passT<=0){""")

# ── Vier Missionen ───────────────────────────────────────────
sub("new-missions",
"""  21:{name:'Die Sperre',""",
"""  5: {name:'Durch den Guertel', fac:'hol', o:'guard', live:4,
      stillRocks:true, crossEnds:true, u:[
       {id:'A1', c:'co', n:1, spr:'codeimos', side:'ally', crossSecs:55},
       {id:'R1', c:'ast', n:30},
       {id:'G1', c:'sg', n:4, spr:'sgankh'},
       {id:'E1', c:'fi', n:2}
     ]},

  12:{name:'Die Fracht', fac:'hol', o:'scan', live:5, hunt:'C1', u:[
       {id:'C1', c:'fc', n:4, spr:'fcvc3', scan:true},
       {id:'E1', c:'fi', n:2, wait:true}
     ], ev:[
       // Solange Container stehen, kommt Nachschub. Wer schnell raeumt,
       // hat weniger zu tun - wer zoegert, bekommt mehr.
       {t:'erfuellt',     a:'',   w:'einwarpen', a2:'E1'},
       {t:'erfuellt',     a:'',   w:'nachschub', a2:'an'},
       {t:'erfuellt',     a:'',   w:'auftrag',   a2:'protect'},
       {t:'alleZerstoert',a:'C1', w:'nachschub', a2:'aus'},
       {t:'alleZerstoert',a:'C1', w:'meldung',   a2:'cargo lost'}
     ]},

  18:{name:'Tenderizer', fac:'hol', o:'guard', live:6, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally'},
       {id:'K1', c:'fi', n:3, ram:true},
       {id:'K2', c:'fi', n:2, t:22, ram:true}
     ]},

  26:{name:'Das Minenfeld', fac:'hol', o:'guard', live:4,
      stillRocks:true, crossEnds:true, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', crossSecs:70},
       {id:'R1', c:'ast', n:40},
       {id:'G1', c:'sg', n:6, spr:'sgankh'},
       {id:'E1', c:'fi', n:2, t:12}
     ]},

  21:{name:'Die Sperre',""")

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
