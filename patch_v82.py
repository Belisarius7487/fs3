#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FS3  v81 -> v82   "Fundament"

Baut aus hlp_shooter_v81_logic.html die Datei hlp_shooter_v82_logic.html.
Jeder Suchtext muss GENAU EINMAL vorkommen, sonst bricht das Skript ab.

Umfang:
  1  Wellenstruktur: Komposition x Auftrag x Modifikator statt einer Zeile
  2  Sechs neue Kompositionen
  3  Handgesetzte Folge fuer 20 Wellen, danach gewuerfelt gegen die Matrix
  4  Bossfenster statt fester Zahl
  5  Subraumbomben nur in Bomberwellen, seltener, nicht im Nebel
  6  Sparmodus-Voreinstellung

Nicht enthalten (v83): Vasudaner als dritte Fraktion, vasudanische
Bosskomposition, roter Winkel, Subsystem-Scan, Funkraumregel.
"""

import io, os, sys

SRC = "hlp_shooter_v81_logic.html"
DST = "hlp_shooter_v82_logic.html"

edits = []
def sub(tag, old, new):
    edits.append((tag, old, new))


# ── 1  Sparmodus-Voreinstellung ──────────────────────────────
sub("eco-default",
"""let ECO = {res:3, blur:false, rim:false, glint:false};""",
"""// Voreinstellung sparsam. Auf einem 1280x800-Tablet mit
// Geraetepixelverhaeltnis 2 kostet res 3 eine Flaeche von 3,6 Millionen
// Bildpunkten je Bild und macht das Geraet nach laengeren Sitzungen heiss;
// bei 1.5 sind es 0,9 Millionen. true heisst hier AUS.
// Wer schon einmal gespielt hat, behaelt seine eigene Wahl - der
// gespeicherte Stand ueberschreibt diese Zeile weiter unten.
let ECO = {res:1.5, blur:true, rim:true, glint:true};""")

# ── 2  Subraumbomben ─────────────────────────────────────────
sub("bomb-max",
"""const BOMB_RAID_MAX = 3;            // hoechstens drei Angriffe je Welle""",
"""const BOMB_RAID_MAX = 2;            // hoechstens zwei Angriffe je Welle""")

# ── 3  Der grosse Umbau ──────────────────────────────────────
OLD_START = "const WAVE_PLAN = ["
OLD_END   = """  return buildWave(spec);
}"""

NEW_BLOCK = r"""// ── DREI ACHSEN STATT EINER ZEILE ────────────────────────────
// Bis v81 stand eine Welle in einer Zeile, und in dieser Zeile steckten
// drei verschiedene Dinge:
//
//   {name:'Asteroid Escort', fi:5, ast:0, caps:[], live:3, pause:520,
//    guard:'destroyer', guardFrac:1.00, astAim:1, transit:50}
//
// fi/bo/ast/caps/live/pause sagen, WER KOMMT. guard und guardFrac sagen,
// WAS ZU TUN IST. astAim und transit sind die Mechanik dieses Auftrags.
// Weil sie verschweisst waren, liessen sich elf Zeilen nicht rekombinieren
// und elf Wellen fuehlten sich an wie eine: alle hatten denselben Auftrag,
// naemlich das Feld leerraeumen.
//
// Getrennt ergeben 17 Kompositionen mal 9 Auftraege 153 Felder, von denen
// rund ein Viertel unvertraeglich ist. Was bleibt, traegt 100 Wellen ohne
// Wiederholung - und Modifikatoren und Fraktionen sind darin noch nicht
// mitgezaehlt.

// ── ACHSE 1: KOMPOSITION ── wer kommt, sonst nichts ──────────
//   fi/bo   Staffeln, nicht Schiffe. Eine Staffel sind drei bis vier.
//   ast     Brocken, Kulisse
//   sg      Sperrgeschuetze. Zaehlen NICHT gegen live (WING_TYPES kennt
//           sie nicht), halten die Welle aber offen, bis sie fallen.
//   live    wie viele Jaeger und Bomber gleichzeitig im Feld stehen
//   pause   Abstand zwischen zwei Staffeln
const COMPOS = {
  patrol:    {name:'Patrol',          fi:2, bo:0, ast:0,  sg:0, caps:[],           live:3, pause:600},
  belt:      {name:'Asteroid Belt',   fi:2, bo:0, ast:10, sg:0, caps:[],           live:4, pause:600},
  bomberrun: {name:'Bomber Run',      fi:1, bo:2, ast:0,  sg:0, caps:[],           live:4, pause:700},
  crpatrol:  {name:'Cruiser Patrol',  fi:2, bo:0, ast:3,  sg:0, caps:['cr'],       live:4, pause:600},
  heavy:     {name:'Heavy Patrol',    fi:5, bo:0, ast:0,  sg:0, caps:[],           live:3, pause:520},
  swarm:     {name:'Swarm',           fi:5, bo:0, ast:0,  sg:0, caps:[],           live:5, pause:300},
  push:      {name:'Push',            fi:2, bo:1, ast:0,  sg:0, caps:['cr','co'],  live:4, pause:600},
  flagship:  {name:'Flagship',        fi:2, bo:0, ast:2,  sg:0, caps:['cr'],       live:4, pause:600, iceni:1},
  siege:     {name:'Siege',           fi:3, bo:2, ast:0,  sg:0, caps:['co','de'],  live:5, pause:500, reinf:2600},
  bomberwing:{name:'Bomber Wing',     fi:1, bo:4, ast:0,  sg:0, caps:[],           live:4, pause:500},
  bosswave:  {name:'Boss',            fi:3, bo:2, ast:0,  sg:0, caps:['boss'],     live:5, pause:600, reinf:3000},

  // ── neu in v82 ──
  // Drei leichte Traeger fuer Grosskampfschiffe. Lahmlegen hatte vorher nur
  // vier Traeger, und drei davon waren schwere Wellen; jetzt sind es sieben
  // mit einer Spanne von 8,9 bis 45 Sekunden statt nur "schwer".
  lonecr:    {name:'Lone Cruiser',    fi:1, bo:0, ast:0,  sg:0, caps:['cr'],       live:3, pause:600},
  loneco:    {name:'Lone Corvette',   fi:1, bo:0, ast:0,  sg:0, caps:['co'],       live:3, pause:600},
  // Die einzige Komposition ohne gegnerische Jaeger. Sie war in der ersten
  // Fassung ein Lebensfresser: das Waffensystem eines Zerstoerers hat
  // 0.10*6500 = 650 Trefferpunkte, also 4,1 s Dauerfeuer auf ein Ziel von
  // 24 px Radius, waehrend zwei Antijaegerstrahlen bei 1,4 je Schritt in
  // 1,43 s Kontakt toeten. Drei Dinge retten sie:
  //   - die Brocken beschaedigen auch Gegner (updateAsteroidImpacts prueft
  //     Spieler, Verbuendete UND Gegner), und astRamDmg rechnet 3,5 bis
  //     7,5 PROZENT von maxHp: dreizehn Volltreffer legen ihn allein um
  //   - capitalFire ruft eSmall mit ang=null und schiesst damit stur nach
  //     links, also in die eigene Fahrtrichtung - von hinten steht man
  //     ausserhalb der Salven
  //   - beamTargets sammelt fuer einen Kleinstrahl den Spieler UND alle
  //     kleinen Verbuendeten, die gerufene Staffel teilt das Feuer wirklich
  crossing:  {name:'Silent Crossing', fi:0, bo:0, ast:14, sg:0, caps:['de'],       live:3, pause:600,
              slowCap:1, allyWing:3},
  // Sperrgeschuetze stehen ausserhalb des live-Deckels: zusaetzlicher Druck
  // ohne Bremse.
  gunline:   {name:'Gun Line',        fi:2, bo:0, ast:0,  sg:6, caps:[],           live:4, pause:600},
  // Ersetzt belt als eigenstaendige Welle. Zehn Brocken allein sind 400 von
  // 946 Trefferpunkten, also 2,5 Sekunden Streu; mit vier Geschuetzen
  // dazwischen werden sie Deckung statt Ziel.
  minefield: {name:'Minefield',       fi:1, bo:0, ast:10, sg:4, caps:[],           live:3, pause:600},
  // Frachter und Container hat der Endlosmodus nie gesehen. Traegt Laeufer
  // abfangen, Fracht scannen und Schuetzling schuetzen auf einmal.
  convoy:    {name:'Convoy',          fi:3, bo:0, ast:0,  sg:0, caps:[],           live:5, pause:520,
              cargo:2}
};

// ── ACHSE 2: AUFTRAG ── was zu tun ist ───────────────────────
// Genau einer je Welle. Der Grund ist die Anzeige und nicht die Mechanik:
// bei rund 90 Sekunden je Welle geht ein zweiter Hinweis unter.
const OBJ = {
  clear:   {t:'[ CLEAR THE FIELD ]'},
  guard:   {t:null, cls:'destroyer'},   // Text kommt aus objectiveText()
  transit: {t:null, cls:'destroyer', secs:50, aim:1},
  runner:  {t:null, flee:40, ships:[['frposeidon',2]]},
  scan:    {t:null, cargo:3},
  disable: {t:null},
  protect: {t:null, ships:[['frposeidon',2]]},
  feud:    {t:'[ THREE WAY FIGHT ]'},
  boss:    {t:null}
};

// ── VERTRAEGLICHKEITSMATRIX ──────────────────────────────────
// 17 Kompositionen mal 9 Auftraege. Jedes Nein hat einen mechanischen
// Grund, keinen Geschmack:
//   - Lahmlegen braucht ein Ziel mit Subsystemen. hasSubsystems() gilt nur
//     fuer Grosskampfschiffe.
//   - Auf einer Querung muss gateWings aus sein, sonst blockiert die erste
//     Staffel sich selbst. Ohne Schleuse kommen die Staffeln nach Uhr, und
//     bei fuenf Staffeln steht dann alles gleichzeitig im Bild.
//   - Laeufer brauchen freie Bahn nach links; zehn stehende Brocken
//     verstopfen sie.
//   - Ein Boss ist das Ereignis der Welle. Ein zweites Kopfthema daneben
//     wird nicht gelesen.
const ALL_K = Object.keys(COMPOS);
const OBJ_OK = {
  clear:   ALL_K,
  guard:   ALL_K.filter(function(k){ return k!=='bosswave'; }),
  transit: ['patrol','belt','bomberrun','crpatrol','push','flagship',
            'bomberwing','lonecr','loneco','gunline','minefield','convoy'],
  runner:  ['patrol','bomberrun','crpatrol','heavy','push','flagship','siege',
            'bomberwing','lonecr','loneco','gunline','convoy'],
  scan:    ['patrol','belt','bomberrun','crpatrol','heavy','push','flagship',
            'bomberwing','lonecr','loneco','gunline','minefield','convoy'],
  disable: ['crpatrol','push','flagship','siege','lonecr','loneco','crossing'],
  protect: ['patrol','belt','bomberrun','crpatrol','heavy','push','flagship',
            'bomberwing','lonecr','loneco','gunline','minefield','convoy'],
  feud:    ['belt','bomberrun','crpatrol','heavy','swarm','push','flagship',
            'siege','bomberwing','gunline','minefield','convoy'],
  boss:    ['bosswave']
};
function objFits(k, o){ return (OBJ_OK[o]||[]).indexOf(k) >= 0; }

// ── HANDGESETZTE FOLGE ───────────────────────────────────────
// Die ersten zwanzig Wellen sind geschrieben und nicht gewuerfelt. Der
// Grund ist nicht technisch: wer zwanzig Minuten hineinschaut, sieht genau
// diesen Abschnitt und sonst nichts, und der soll bei jedem gleich gut
// sein. Ab Welle 21 ist Abwechslung mehr wert als Kontrolle.
//   f: Fraktion. 'hol' ist der Hammer of Light und kommt erst mit v83;
//      bis dahin faellt er auf die NTF zurueck, siehe factionOf().
const WAVE_SEQ = [
  {k:'patrol',    o:'clear',   f:'ntf'},     //  1  Einstieg
  {k:'minefield', o:'clear',   f:'ntf'},     //  2  Wendigkeit
  {k:'bomberrun', o:'guard',   f:'ntf'},     //  3  Tempo
  {k:'lonecr',    o:'disable', f:'ntf'},     //  4  erstes Subsystem
  {k:'convoy',    o:'scan',    f:'hol'},     //  5  Verweilen unter Feuer
  {k:'swarm',     o:'feud',    f:'hol'},     //  6  Kurvenkampf
  {k:'gunline',   o:'clear',   f:'shivan'},  //  7  Reichweite, Deckung
  {k:'heavy',     o:'clear',   f:'shivan'},  //  8  Rumpf, Dauerfeuer
  {k:'loneco',    o:'disable', f:'shivan'},  //  9  Sekundaer unter Beschuss
  {k:'bomberwing',o:'protect', f:'ntf'},     // 10  vor dem Abwurf abfangen
  {k:'flagship',  o:'runner',  f:'ntf'},     // 11  Burst, 40-Sekunden-Frist
  {k:'belt',      o:'clear',   f:'hol'},     // 12
  {k:'crpatrol',  o:'scan',    f:'hol'},     // 13  neben einem Kreuzer
  {k:'crossing',  o:'disable', f:'shivan'},  // 14  Ausdauer
  {k:'push',      o:'clear',   f:'shivan'},  // 15  gemischt, schwer
  {k:'bosswave',  o:'boss',    f:'ntf'},     // 16  im Fenster 12 bis 18
  {k:'patrol',    o:'clear',   f:'hol'},     // 17  Verschnaufen
  {k:'minefield', o:'protect', f:'hol'},     // 18  Sicht, Naehe
  {k:'siege',     o:'clear',   f:'shivan'},  // 19  Heavy Bomber
  {k:'convoy',    o:'transit', f:'shivan'}   // 20  Platzhalter: wird mit
                                             //     v83 die vasudanische
                                             //     Bosskomposition
];
const SEQ_LEN = WAVE_SEQ.length;

// ── BOSSFENSTER ──────────────────────────────────────────────
// Alle elf Wellen ein Boss ist ein Kalender, kein Ereignis. Der Abstand
// wird stattdessen gewuerfelt: irgendwo zwischen 12 und 18 Wellen nach dem
// letzten. Auf 100 Wellen sind das rund sechs Bosse.
const BOSS_GAP_MIN = 12, BOSS_GAP_MAX = 18;
let lastBossWave = 0, nextBossWave = 0;
function rollNextBoss(from){
  nextBossWave = from + BOSS_GAP_MIN
               + ((Math.random()*(BOSS_GAP_MAX-BOSS_GAP_MIN+1))|0);
}

// Fraktion. Der Hammer of Light kommt mit v83; bis dahin faellt er auf die
// NTF zurueck, damit die Folge schon in ihrer endgueltigen Form dasteht.
function factionOf(f){ return (f==='hol') ? 'ntf' : f; }

// Ab Welle 21 gewuerfelt. Eine Komposition und ein Auftrag, die beide zur
// Matrix passen und nicht die der Vorwelle sind.
let lastK = '', lastO = '';
function rollWave(n){
  const bossDue = (n >= nextBossWave);
  if(bossDue){ lastBossWave = n; rollNextBoss(n); return {k:'bosswave', o:'boss'}; }
  const objs = Object.keys(OBJ).filter(function(o){ return o!=='boss' && o!==lastO; });
  for(let tries=0; tries<40; tries++){
    const o = objs[(Math.random()*objs.length)|0];
    const ks = OBJ_OK[o].filter(function(k){ return k!=='bosswave' && k!==lastK; });
    if(!ks.length) continue;
    return {k: ks[(Math.random()*ks.length)|0], o: o};
  }
  return {k:'patrol', o:'clear'};      // Rueckfall, darf nie gebraucht werden
}

function getWaveDef(n){
  // Test mode replaces the wave plan entirely. Without ?test=1 on the URL
  // none of this is reachable and the normal game is untouched.
  if(TEST_MODE) return buildTestWave(((n-2+TEST_FIRST)%4)+1);
  if(FS1_MODE)  return buildFS1Wave(n);

  if(n===1){ lastBossWave = 0; rollNextBoss(SEQ_LEN); lastK=''; lastO=''; }

  let pick;
  if(n <= SEQ_LEN){
    pick = WAVE_SEQ[n-1];
    if(pick.o==='boss'){ lastBossWave = n; rollNextBoss(n); }
  } else {
    pick = rollWave(n);
  }
  lastK = pick.k; lastO = pick.o;

  const K = COMPOS[pick.k], o = pick.o, spec0 = OBJ[o] || OBJ.clear;
  const tier = Math.floor((n-1)/SEQ_LEN), t = tier;
  const fac = factionOf(pick.f || ((n%2) ? 'ntf' : 'shivan'));
  currentFaction = fac;
  const shivan = (fac === 'shivan');
  const sfx = shivan ? '_sh' : '_ntf';

  waveLive = K.live + (shivan?WAVE_LIVE_SHIVAN:0) + t*WAVE_TIER_LIVE;
  fleeTotal = 0; fleeEscaped = 0;

  // ── Auftrag setzt die Flaggen, die Komposition keine davon ──
  guardWanted = (o==='guard' || o==='transit');
  guardSpawned = false; guardLost = false;
  guardClass  = spec0.cls || 'cruiser';
  guardFrac   = GUARD_HULL_FRAC;
  guardReward = guardClass;
  astAim      = !!spec0.aim;
  transitSecs = (o==='transit') ? (spec0.secs||50) : 0;
  // A crossing has no clear field to wait for: the rocks never stop, so
  // gating the wings there would hold back every wing after the first.
  gateWings = !transitSecs;
  gateWing = 0;
  disableTarget = null;
  guardGone   = false;
  astStreamCd = AST_STREAM_MEAN;
  waveFeud    = (o==='feud');
  waveTitle   = 'WAVE '+n+'   '+K.name.toUpperCase();
  titleT      = TITLE_TIME;

  waveMod = rollWaveMod(n);
  if(waveMod!==MOD_NONE) lastMod = waveMod;
  if(nebulaOn()) nebTint = NEB_TINTS[(Math.random()*NEB_TINTS.length)|0];
  empOut = 0; empWarn = 0;
  empNext = waveMod==='emp' ? (1200+((Math.random()*600)|0)-EMP_WARN) : 0;

  // Subraum-Bombenangriffe. Drei Einschraenkungen gegenueber v81:
  //   - nur in Wellen, in denen auch Bomber vorkommen. Sie sind eine
  //     Bomberwaffe und kein Naturereignis.
  //   - hoechstens zwei statt drei je Welle.
  //   - nie im Nebel: fireRange() deckelt dort auf 240, die Bomben kaemen
  //     gar nicht erst an.
  BOMB_PORTALS = [];
  const bombOk = (K.bo > 0) && (n >= BOMB_RAID_FIRST_WAVE) && !nebulaOn();
  bombRaidLeft = bombOk ? ((Math.random()*(BOMB_RAID_MAX+1))|0) : 0;
  bombRaidCd   = BOMB_RAID_FIRST + ((Math.random()*BOMB_RAID_JIT)|0);
  reinfAt = K.reinf || 0; reinfDone = false;

  const spec = {
    name:  K.name,
    fi:    K.fi + (K.fi?t*WAVE_TIER_WINGS:0)
           + ((K.iceni && o==='runner' && !shivan) ? icenEscapes : 0),
    bo:    K.bo + (K.bo?t*WAVE_TIER_WINGS:0),
    ast:   K.ast,
    caps:  K.caps.map(function(c){
      if(c==='cr' && K.iceni && o==='runner' && !shivan) return 'iceni';
      return c==='boss' ? 'boss'+sfx : c+sfx;
    }),
    pause: K.pause,
    flee:  (o==='runner' && K.caps.length) ? (spec0.flee||40) : 0,
    fiType:'fi'+sfx, boType:'bo'+sfx
  };
  const q = buildWave(spec);

  // ── Was die Komposition zusaetzlich ins Feld stellt ──────────
  // Sperrgeschuetze stehen von Anfang an da und warpen nicht ein.
  const sgPool = shivan ? ['sgtrident','sgbelial'] : ['sgwatchdog','sgcerberus','sgalastor'];
  for(let i=0;i<(K.sg||0);i++)
    q.push({time:1, type:'sentry', spr:sgPool[(Math.random()*sgPool.length)|0],
            fac:fac, noWarp:1,
            x:W*(0.62+0.13*(i%3)), y:H*(0.20+0.13*(i%5))});

  // Frachtcontainer als Kulisse einer Konvoiwelle. Der Auftrag scan macht
  // sie zu Zielen, sonst stehen sie einfach herum.
  for(let i=0;i<(K.cargo||0);i++)
    q.push({time:1, type:'container', spr:'fcvc3', fac:fac, noWarp:1,
            x:W*(0.55+0.10*i), y:H*(0.34+0.18*i)});

  // ── Was der Auftrag zusaetzlich ins Feld stellt ──────────────
  if(o==='scan'){
    const nsc = spec0.cargo||3;
    for(let i=0;i<nsc;i++)
      q.push({time:1, type:'container', spr:'fcvc3', fac:fac, scan:1,
              noWarp:1, x:W*(0.58+0.09*i), y:H*(0.38+0.16*i)});
  }
  if(o==='protect'){
    for(const pair of (spec0.ships||[]))
      for(let i=0;i<pair[1];i++)
        q.push({time:1, type:'protect', spr:pair[0], fac:'terran', noWarp:1,
                x:W*(0.28+0.10*i), y:H*(0.34+0.18*i)});
  }
  if(o==='runner' && !K.caps.length){
    // Ohne Grosskampfschiff traegt die Frist niemand, also fliehen Frachter.
    for(const pair of (spec0.ships||[]))
      for(let i=0;i<pair[1];i++){
        q.push({time:200+i*160, type:'freighter', spr:pair[0], fac:fac,
                runner:1, hpMul:RUNNER_HP_MUL, y:H*(0.30+0.22*i)});
        fleeTotal++;
      }
  }
  if(o==='disable'){
    // Das erste Grosskampfschiff der Welle wird das Ziel. buildWave setzt
    // sie in caps-Reihenfolge ganz nach vorn in die Schlange.
    for(const e of q) if(e.type && CAP_GAP[e.type.split('_')[0]]!==undefined){ e.disable=1; break; }
  }
  // Eine verbuendete Staffel, die das Feuer teilt. Nur wo die Komposition
  // sie ausdruecklich vorsieht - siehe crossing.
  if(K.allyWing) allyWingWanted = K.allyWing;
  else           allyWingWanted = 0;

  return q.sort(function(a,b){ return a.time-b.time; });
}"""

# ── 4  Verweise auf die geloeschte Tabelle ──────────────────
# WAVES_PER_SIDE und WAVE_CYCLE standen im erhaltenen Mittelteil und lasen
# WAVE_PLAN.length. Die Tabelle gibt es nicht mehr - das ist ein
# ReferenceError beim Laden, und der killt das ganze Skript, also schwarzer
# Bildschirm. node --check findet so etwas nicht.
# Bewusst Literale: SEQ_LEN wird erst weiter unten deklariert, ein Zugriff
# darauf waere derselbe Fehler noch einmal.
sub("wave-cycle",
"""const WAVES_PER_SIDE = WAVE_PLAN.length;      // eleven
const WAVE_CYCLE     = WAVES_PER_SIDE*2;      // twenty two""",
"""// Laenge der handgesetzten Folge. Muss zu WAVE_SEQ passen; wird nur fuer
// das Huellenwachstum je Zyklus gebraucht (cycleMult).
const WAVE_CYCLE = 20;""")

# ── 5  Verbuendete Staffel, die crossing traegt ──────────────
sub("allywing-var",
"""let waveLive = 5;             // cap for the wave being fought""",
"""let waveLive = 5;             // cap for the wave being fought
// Von der Komposition angeforderte verbuendete Jaeger. Sie teilen das
// Strahlenfeuer: beamTargets() sammelt fuer einen gegnerischen Kleinstrahl
// den Spieler UND alle kleinen Verbuendeten.
let allyWingWanted = 0;""")

sub("allywing-spawn",
"""  wave++;waveOver=false;waveCd=0;bossAlive=false;bossSlain=false;""",
"""  wave++;waveOver=false;waveCd=0;bossAlive=false;bossSlain=false;
  // Die verbuendete Staffel wird nach dem Wellenaufbau gestellt, weil
  // getWaveDef ihre Zahl erst dort setzt.
  window._allyWingDue = true;""")

sub("allywing-place",
"""  enemies=[];eBullets=[];allies=[];debris=[];empOut=0;allyCd=0;callMenu=false;paused=false;spawnQ=getWaveDef(wave);spawnT=0;""",
"""  enemies=[];eBullets=[];allies=[];debris=[];empOut=0;allyCd=0;callMenu=false;paused=false;spawnQ=getWaveDef(wave);spawnT=0;
  for(let i=0;i<allyWingWanted;i++){
    const a = mkAllySmall('fighter','terran',
                          rnd(ROLES.ally_ter_fighters||ROLES.ter_fighters||['fiherc']),
                          H*(0.34+0.14*i));
    if(a) allies.push(a);
  }""")


def main():
    if not os.path.exists(SRC):
        sys.exit("FEHLT: " + SRC)
    txt = io.open(SRC, "r", encoding="utf-8").read()

    i = txt.find(OLD_START)
    if i < 0 or txt.count(OLD_START) != 1:
        sys.exit("ABBRUCH wave-plan-start: %d Treffer" % txt.count(OLD_START))
    j = txt.find(OLD_END, i)
    if j < 0:
        sys.exit("ABBRUCH wave-plan-end nicht gefunden")
    j += len(OLD_END)
    # Alles zwischen WAVE_PLAN und dem Ende von getWaveDef wird ersetzt.
    # Die Bloecke dazwischen (STATS, ICENI, WAVE_LIVE_SHIVAN) muessen
    # erhalten bleiben, also herausschneiden und wieder anhaengen.
    middle = txt[i:j]
    keep_from = middle.find("// The Shivan half runs the same shapes one step harder.")
    keep_to   = middle.find("function getWaveDef(n){")
    if keep_from < 0 or keep_to < 0:
        sys.exit("ABBRUCH Mittelteil nicht gefunden")
    keep = middle[keep_from:keep_to]
    txt = txt[:i] + keep + NEW_BLOCK + txt[j:]
    print("  ok   wave-axes   (%d Zeichen ersetzt, %d erhalten)" % (j-i, len(keep)))

    for tag, old, new in edits:
        n = txt.count(old)
        if n != 1:
            sys.exit("ABBRUCH %s: %d Treffer statt 1" % (tag, n))
        txt = txt.replace(old, new, 1)
        print("  ok   " + tag)

    io.open(DST, "w", encoding="utf-8").write(txt)
    print("\ngeschrieben: %s  (%.2f MB)" % (DST, os.path.getsize(DST)/1048576.0))


if __name__ == "__main__":
    main()
