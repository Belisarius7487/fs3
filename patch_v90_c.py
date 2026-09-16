#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FS3 v90 Teil C: die zwoelf sofort spielbaren HoL-Missionen."""
import io, os, sys
F="hlp_shooter_v90_logic.html"

BLOCK = r"""
// ── HAMMER OF LIGHT ──────────────────────────────────────────
// Zwoelf der dreissig geschriebenen Missionen. Die uebrigen achtzehn
// brauchen Klassen oder Verhalten, die noch nicht gebaut sind:
// Installationen, Frachter mit Ladung, Andocken, Kollisionsangriffe,
// Zielvorliebe, nach rechts entkommende Gegner, Zustand ueber Wellen.
//
// Einheit: {id, c:Kategorie, n:Anzahl (bei fi/bo Staffeln), spr:Rumpf,
//           side:'ally', t:Sekunde, x, y, hp:Faktor, wait:true}
// wait heisst: kommt nur, wenn ein Ereignis es einwarpen laesst.
const SCRIPT_WAVES = {
  1: {name:'Erstkontakt', fac:'hol', o:'clear', live:4, u:[
       {id:'E1', c:'fi', n:3}
     ]},

  2: {name:'Geschuetzstellung', fac:'hol', o:'clear', live:4, u:[
       {id:'G1', c:'sg', n:6, spr:'sgankh'},
       {id:'E1', c:'fi', n:2, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'G1', w:'einwarpen', a2:'E1'}
     ]},

  3: {name:'Nachschub', fac:'hol', o:'clear', live:4, u:[
       {id:'E1', c:'fi', n:2},
       {id:'K1', c:'cr', n:1, spr:'craten', wait:true},
       {id:'E2', c:'fi', n:1, wait:true}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'K1'},
       {t:'alleZerstoert', a:'E1', w:'einwarpen', a2:'E2'}
     ]},

  6: {name:'Begegnung', fac:'hol', o:'guard', live:5, u:[
       {id:'A1', c:'co', n:1, spr:'cosobek', side:'ally'},
       {id:'V1', c:'co', n:1, spr:'cosobek'},
       {id:'E1', c:'fi', n:2},
       {id:'B1', c:'bo', n:1, t:40}
     ]},

  7: {name:'Der Angriff', fac:'hol', o:'guard', live:5, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally'},
       {id:'V1', c:'de', n:1, spr:'detyphon'},
       {id:'E1', c:'fi', n:1},
       {id:'B1', c:'bo', n:2, t:15}
     ]},

  8: {name:'Der Rueckzug', fac:'hol', o:'guard', live:4, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.55},
       {id:'B1', c:'bo', n:2},
       {id:'B2', c:'bo', n:2, t:35}
     ]},

  13:{name:'Die Transporter', fac:'hol', o:'protect', live:4, u:[
       {id:'T1', c:'tr', n:2, spr:'trisis', side:'ally', cross:0.42, x:-40},
       {id:'R1', c:'ast', n:10},
       {id:'E1', c:'fi', n:2},
       {id:'E2', c:'fi', n:1, t:30}
     ]},

  14:{name:'Die Tarnung', fac:'hol', o:'clear', live:5, u:[
       {id:'A1', c:'fi', n:2, side:'ally'},
       {id:'E1', c:'fi', n:3}
     ], ev:[
       {t:'alleZerstoert', a:'E1', w:'meldung', a2:'turning hostile'},
       {t:'alleZerstoert', a:'E1', w:'seite', a2:'A1'}
     ]},

  15:{name:'Der Vorratsspeicher', fac:'hol', o:'clear', live:4, u:[
       {id:'C1', c:'fc', n:5, spr:'fcvc3'},
       {id:'G1', c:'sg', n:3, spr:'sgankh'},
       {id:'R1', c:'ast', n:8},
       {id:'E1', c:'fi', n:2, wait:true}
     ], ev:[
       {t:'anzahlUnter', a:'C1', b:3, w:'einwarpen', a2:'E1'}
     ]},

  16:{name:'Die Meuterei', fac:'hol', o:'guard', live:5, u:[
       {id:'A1', c:'cr', n:1, spr:'craten', side:'ally'},
       {id:'A2', c:'fi', n:2, side:'ally'},
       {id:'E1', c:'fi', n:2}
     ], ev:[
       {t:'sek', a:35, w:'meldung', a2:'escort turning hostile'},
       {t:'sek', a:35, w:'seite', a2:'A2'}
     ]},

  21:{name:'Die Sperre', fac:'hol', o:'clear', live:4, u:[
       {id:'K1', c:'cr', n:3, spr:'craten'},
       {id:'E1', c:'fi', n:2}
     ]},

  29:{name:'Die Blockade', fac:'hol', o:'guard', live:5, u:[
       {id:'A1', c:'de', n:1, spr:'dehatshepsut', side:'ally', hp:0.6},
       {id:'V1', c:'co', n:2, spr:'cosobek'},
       {id:'E1', c:'fi', n:2}
     ]}
};
// Die Ereignisliste benutzt a fuer das Ziel des Ausloesers und a2 fuer das
// Ziel der Wirkung. buildScripted() erwartet w/a - hier umbenennen, damit
// die Missionen lesbar bleiben.
for(const k in SCRIPT_WAVES){
  const d = SCRIPT_WAVES[k];
  if(!d.ev) continue;
  for(const e of d.ev){ e.wa = (e.a2!==undefined) ? e.a2 : e.a; }
}
"""

txt=io.open(F,encoding="utf-8").read()
anchor = "// ── GESCHRIEBENE WELLEN ──────────────────────────────────────"
assert txt.count(anchor)==1
txt = txt.replace(anchor, BLOCK + "\n" + anchor, 1)

# evFire nutzt ev.a fuer die Wirkung; wir haben wa. Beides zulassen.
old = """function evFire(ev){
  switch(ev.w){"""
new = """function evFire(ev){
  // Ausloeser und Wirkung koennen verschiedene Ziele haben. wa ist das
  // Ziel der Wirkung, a das des Ausloesers.
  const arg = (ev.wa!==undefined && ev.wa!==null) ? ev.wa : ev.a;
  switch(ev.w){"""
assert txt.count(old)==1
txt = txt.replace(old,new,1)
for a,b in [("const held = EV_HELD[ev.a];","const held = EV_HELD[arg];"),
            ("delete EV_HELD[ev.a];","delete EV_HELD[arg];"),
            ("      waveObj = ev.a;","      waveObj = arg;"),
            ("for(const u of byId(ev.a)) if(u.side!=='enemy') defect(u);",
             "for(const u of byId(arg)) if(u.side!=='enemy') defect(u);"),
            ("for(const u of byId(ev.a)){ u.warpOut = u.warpMax || 100; EV_LEFT[ev.a] = true; }",
             "for(const u of byId(arg)){ u.warpOut = u.warpMax || 100; EV_LEFT[arg] = true; }"),
            ("      evReinf = (ev.a !== 'aus');","      evReinf = (arg !== 'aus');"),
            ("SUB_MSGS.push({x:W/2, y:H*0.40, txt:String(ev.a||'').toUpperCase(),",
             "SUB_MSGS.push({x:W/2, y:H*0.40, txt:String(arg||'').toUpperCase(),")]:
    assert txt.count(a)==1, a
    txt=txt.replace(a,b,1)

old2 = """  EV = (def.ev||[]).map(function(e){ return {t:e.t,a:e.a,b:e.b,w:e.w,done:false}; });"""
new2 = """  EV = (def.ev||[]).map(function(e){
    return {t:e.t, a:e.a, b:e.b, w:e.w, wa:e.wa, done:false}; });"""
assert txt.count(old2)==1
txt=txt.replace(old2,new2,1)

# Ueberlaeufer-Riegel setzen, wo ein Ereignis sie vorsieht
old3 = """        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true; allies.push(_a); }"""
new3 = """        if(_a){ _a.uid=_sp.uid; if(_sp.uid) EV_SEEN[_sp.uid]=true;
                _a.defectLock = evWillDefect(_sp.uid); allies.push(_a); }"""
assert txt.count(old3)==1
txt=txt.replace(old3,new3,1)

old4 = """function evSeen(id){ return !!EV_SEEN[id]; }"""
new4 = """function evSeen(id){ return !!EV_SEEN[id]; }
// Ist fuer diese Kennung ein Seitenwechsel vorgesehen? Dann bekommt sie
// den Rumpfriegel, sonst haengt die Pointe der Welle am Zufall.
function evWillDefect(id){
  if(!id) return false;
  for(const e of EV) if(e.w==='seite' && (e.wa||e.a)===id) return true;
  return false;
}"""
assert txt.count(old4)==1
txt=txt.replace(old4,new4,1)

io.open(F,"w",encoding="utf-8").write(txt)
print("Teil C geschrieben")
