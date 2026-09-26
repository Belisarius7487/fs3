// ── ENEMY FACTORY ────────────────────────────────────────────
// spr and yWant come from the spawn queue for wings, so every ship of one
// wing is the same hull and they arrive stacked.
// ── GROESSE UND ZAEHIGKEIT AUS DER RUMPFLAENGE ───────────────
// Bis v80 wurde die Zielbreite in JEDEM Typzweig fest verdrahtet. Genau
// das war die Ursache dafuer, dass ein 32-Meter-Elysium so breit gezeichnet
// wurde wie ein 320-Meter-Schiff: die Groesse haengt am Typ, und der Typ
// sagt nichts ueber die Ausmasse. Die FreeSpace-Aufnahmen sind alle etwa
// gleich gross, die Bildbreite sagt also ebenfalls nichts.
//
// Neu sind Rumpf, Rolle und Groesse drei getrennte Dinge:
//   welches Sprite  -> der Schluessel
//   welches Verhalten, welche Panzerung -> der Typzweig
//   wie breit, wie zaeh -> diese beiden Kurven, aus der kanonischen Laenge
//
// Breite: 2.880 * Laenge^0.641, Boden 26, Deckel 400.
// Verankert an zwei Werten, die der Autor nach Augenmass gesetzt hatte und
// die dadurch unveraendert bleiben: Fenris 253 m -> 100, Orion 2030 m -> 380.
// Jaeger, Bomber und Rettungskapseln sind ausgenommen. Sie sind bewusst
// mehrfach zu gross gezeichnet, sonst waere auf 800x500 nichts steuerbar;
// eine Kurve, die sie einschliesst, kann es rechnerisch nicht geben.
const HULL_LEN = {boamun:30,boartemis:36,boartemisdh:36,boathena:20,bobakha:18,boboanerges:34,bomedusa:36,bonahema:37.4,bonephilim:53,boosiris:40,bosekhmet:23,boseraphim:57.9,boshaitan:28,botaurvi:30,boursa:41,bozeus:20,cacharybdis:181,casetekh:190,codeimos:717,coiceni:998,comoloch:724,cosobek:608,craeolus:272,craten:230,crcain:190,crfenris:253,crleviathan:253,crlilith:190,crmentu:322,crrakshasa:349,dedemon:2139,dehatshepsut:2126,dehecate:2174,deorionleft:2030,deorionright:2030,deravana:2346,detyphon:2153,ephermes:14,epra:23,fcmeson:372,fcsac3:243,fcsc5:20,fctac1:58,fctc2:35,fctctri:249,fctsc2:35,fcttc1:26,fcvac4:25,fcvac5:53,fcvc3:12,fiaeshma:30,fianubis:23,fiapollo:21,fiares:20,fiastaroth:21,fibasilisk:21.5,fidragon:12.6,fierinyes:17,fiherc:20,fihercmk2:17,fihorus:26,filoki:20,fimanticore:15.5,fimara:17.8,fimyrmidon:16,fipegasus:19,fiperseus:17,fiptah:17,fiscorpion:17.3,fiserapis:14,fiseth:20,fitauret:17.5,fitoth:17,fiulysses:16,fivalyrie:21,frasmodeus:123,frbast:38,frbes:56,frchronos:164,frdis:317,frmaat:56,frmephisto:54,frposeidon:67,frsatis:107,frtriton:313,gmanuket:347,gmrahu:211,gmzephyrus:240,inarcadia:3792,incommnode:748,inknossos45deg:4732,inknossosfront:4732,inpharos:40,mehippocrates:420,ntfcodeimos:717,ntfcraeolus:272,ntfcrfenris:253,ntfcrleviathan:253,ntfdehecate:2174,ntfdeorion:2030,scfaustus:162,sdcolossus:6166,sdhades:3404,sdlucifer:2777,sdsathanas:5978,sgalastor:13,sgankh:10,sgbelial:22,sgcerberus:9,sgmjolnir:108,sgtrident:11,sgwatchdog:9,sucentaur:26,suhygeia:32,sunephthys:34,suscarab:27,trargo:171,trazrael:46,trelysium:32,trisis:27};
// Diese drei Wiki-Seiten fuehren keine Laenge, die Werte sind geschaetzt.
const HULL_LEN_EST = ['gmzephyrus','inpharos','mehippocrates'];

const SIZE_K = 2.880, SIZE_E = 0.641, SIZE_MAX = 400;
// Kreuzer eine Stufe groesser. Bei 100 Bildpunkten Breite trug die
// Rumpfanzeige nur sieben Bloecke; mit dem Zuschlag sind es neun, und
// der Abstand zur Korvette mit 195 bleibt deutlich.
const SIZE_CLASS_MUL = {cr: 1.18};
// Der Boden war 26 und damit falsch. Die Jaeger sind mit 60 Bildpunkten
// von der Kurve ausgenommen, aber die Kurve erreicht 60 erst bei 114 m -
// alles darunter waere KLEINER gezeichnet worden als ein Jaeger. Eine
// 27-Meter-Isis ist laenger als ein 21-Meter-Apollo und war 26 gegen 60.
// Das ist keine Stauchung, das ist verkehrt herum.
// Der Boden folgt deshalb der Jaegergroesse: ein Rumpf von Jaegerlaenge
// (20 m) ist mindestens so breit wie ein Jaeger, kuerzere schrumpfen mit
// derselben Kurve mit, laengere bleiben bei 60, bis die Hauptkurve sie
// bei 114 m ueberholt.
const SIZE_REF_L = 20, SIZE_REF_W = 60;
// Sonderfall. Begrenzt durch die Quelldatei te-sd-colossus-bonus.png mit
// 1670x560; bei MAX_RES 3 waeren 1670/3 = 556 die schaerfste moegliche
// Breite. Achtung: SPRITE_PX["sd"] steht im Packer auf 1152, das
// Eingebettete ist also heruntergerechnet. Volle Schaerfe erst, wenn der
// Deckel auf 1670 steht.
// Die Manticore fuellt bei gleicher Breite mehr Flaeche als die uebrigen
// Jaeger und wirkt dadurch massiger. Zehn Prozent schmaler.
const SIZE_FIXED = {sdcolossus: 556, fimanticore: 50};
const SIZE_CLASS_FIXED = {fi: 60, bo: 65, ep: 60};
// Eigener Boden je Klasse, wo der Jaegerboden nicht passt. Ein
// Geschuetzturm ist kein Schiff und wird nicht mit einem Jaeger verglichen.
const SIZE_CLASS_MIN = {sg: 30};

// Die NTF-Praefixregel schlaegt bis hierher durch: ntfdeorion traegt seine
// Klasse an Stelle 3 bis 5, nicht am Anfang.
function hullClass(key){
  if(!key) return '';
  return (key.indexOf('ntf')===0) ? key.substr(3,2) : key.substr(0,2);
}
function hullWidth(key){
  if(SIZE_FIXED[key]!=null) return SIZE_FIXED[key];
  const c = hullClass(key);
  if(SIZE_CLASS_FIXED[c]!=null) return SIZE_CLASS_FIXED[c];
  const L = HULL_LEN[key];
  if(!L) return 100;                       // unbekannt: Kreuzerbreite
  const curve = SIZE_K*Math.pow(L, SIZE_E);
  const floor = (SIZE_CLASS_MIN[c] != null)
    ? SIZE_CLASS_MIN[c]
    : Math.min(SIZE_REF_W, SIZE_REF_W*Math.pow(L/SIZE_REF_L, SIZE_E));
  const mul = SIZE_CLASS_MUL[c] || 1;
  return Math.round(Math.min(SIZE_MAX, Math.max(floor, curve)*mul));
}
// Zielbreite geteilt durch die tatsaechliche Spritebreite. Kein Deckel
// mehr davor: der Deckel war die fest verdrahtete Zielbreite.
// Breite eines Jaegers oder Bombers. Klassenwert, sofern kein eigener
// Eintrag in SIZE_FIXED steht - dort stehen die Ruempfe, deren Sprite bei
// gleicher Breite mehr Flaeche fuellt als der Rest.
function smallWidth(key, klasse){
  if(SIZE_FIXED[key]!=null) return SIZE_FIXED[key];
  return SIZE_CLASS_FIXED[klasse];
}
function hullScale(key, fallback){
  const img = IMGS[key];
  if(!img || !img.width) return fallback||0.5;
  // Massgeblich ist die groessere Seite. Sonst wird ein Sprite, das hoeher
  // als breit ist, viel zu gross gezeichnet: 30 Bildpunkte Breite sind bei
  // einem hochkant stehenden Geschuetzturm 90 Bildpunkte Hoehe.
  // Bei Schiffen ist die groessere Seite die Breite, dort aendert sich nichts.
  return hullWidth(key)/Math.max(img.width, img.height||img.width);
}

// Zaehigkeit aus derselben Laenge. Verankert an den zwei am besten
// eingespielten Werten des Spiels, Fenris 1120 und Deimos 2500, woraus
// sich 15.73 * Laenge^0.771 ergibt. Gegenprobe an den uebrigen
// Kampfschiffen: Moloch 101 %, Aeolus 106 %, Hecate 90 %, Orion 86 %.
// Die Balance war also laengst laengenbasiert, sie stand nur in einer
// Tabelle aus sechs Klassennamen, in der man das nicht sehen konnte.
// Der Faktor ist die Panzerung und haengt zu Recht an der Rolle: ein
// Frachter und ein Kreuzer gleicher Laenge sind gleich gross, aber nicht
// gleich gepanzert.
const NC_K = 15.73, NC_E = 0.771, NC_ARMOR = 0.65;
function hullPoints(key, fallback){
  const L = HULL_LEN[key];
  if(!L) return fallback;
  return Math.max(40, Math.round(NC_K*Math.pow(L, NC_E)*NC_ARMOR));
}

function mkEnemy(type, spr0, yWant){
  const y=(yWant!=null)?yWant:(60+Math.random()*(H-120));
  if(typeRole(type)==='fi'){
    const pool=poolFor(type);
    const spr=spr0||rnd(pool);
    const img=IMGS[spr];
    const _fw=smallWidth(spr,'fi');
    const sc=img?Math.min(0.55,_fw/img.width):0.5;
    // One roll only: the vortex and the ship that comes out of it have to
    // agree on where the hole is.
    const ax=ambushX();
    return {type:'fighter',img:spr,faction:typeFac(type),
      pts:100,x:ax,y,warpX:ax,warpY:y,hp:HULL.fighter,maxHp:HULL.fighter,sh:SHIELD.fighter.max,maxSh:SHIELD.fighter.max,shRe:SHIELD.fighter.re,shDelay:0,shHit:0,minY:HUD_H+22,maxY:H-22,
      vx:-(0.9+Math.random()*0.9),vy:0,ang:0,
      head:Math.PI, spd:EFIGHTER_SPD, turn:EFIGHTER_TURN,
      role:'stand', passT:0, orbit:(Math.random()<0.5?-1:1),
      prefD:90+Math.random()*130,
      fT:(60+Math.random()*60)|0,fR:(85+Math.random()*60)|0,
      dead:false,sc,warp:100};}
  if(typeRole(type)==='bo'){
    const pool=poolFor(type);
    const spr=spr0||rnd(pool);
    const img=IMGS[spr];
    const _bw=smallWidth(spr,'bo');
    const sc=img?Math.min(0.55,_bw/img.width):0.5;
    const axb=ambushX();
    return {type:'bomber',img:spr,faction:typeFac(type),
      pts:150,x:axb,y,warpX:axb,warpY:y,hp:HULL.bomber,maxHp:HULL.bomber,sh:SHIELD.bomber.max,maxSh:SHIELD.bomber.max,shRe:SHIELD.bomber.re,shDelay:0,shHit:0,minY:HUD_H+22,maxY:H-22,
      vx:-(0.5+Math.random()*0.6),vy:0,ang:0,
      head:Math.PI, spd:EBOMBER_SPD, turn:EBOMBER_TURN,
      role:'stand', passT:0, orbit:(Math.random()<0.5?-1:1),
      prefD:200+Math.random()*140,
      fT:(15+Math.random()*20)|0,fR:(12+Math.random()*4)|0,
      dead:false,sc,warp:140};}
  if(typeRole(type)==='cr'){
    const pool=poolFor(type);
    // The queue may name the hull. Endless waves pass nothing and keep
    // rolling from the pool as before; a scripted wave needs the Cain the
    // mission actually uses.
    const spr=spr0||rnd(pool);
    const img=IMGS[spr];
    const sc=hullScale(spr,0.7);
    const cr={type:'cruiser',img:spr,faction:typeFac(type),
      // Cruisers screen the heavier ships, so they take the forward band.
      // This used to be the rearmost of the three.
      pts:400,x:W-20,y,warpX:W-20,warpY:y,targetX:W-118-Math.random()*40,hp:capHull(HULL.cruiser),maxHp:capHull(HULL.cruiser),
      vy:(Math.random()<.5?1:-1)*(0.25+Math.random()*0.3),
      minY:HUD_H+60,maxY:H-60,fT:80,fR:70,pat:0,dead:false,sc,warp:190};
    initBeams(cr);return cr;}
  if(typeRole(type)==='co'){
    const pool=poolFor(type);
    const spr=spr0 || rnd(pool);
    const img=IMGS[spr];
    const sc=hullScale(spr,0.9);
    const ent={type:'corvette',img:spr,faction:typeFac(type),
      pts:600,x:W-20,y,warpX:W-20,warpY:y,
      // Corvettes sit behind the cruisers now. W-74 hiess: die aeussere
      // Haelfte eines 195 Bildpunkte breiten Rumpfs lag ausserhalb des
      // Feldes, waehrend das verbuendete Gegenstueck ganz zu sehen war.
      targetX:W-150-Math.random()*34,
      hp:capHull(HULL.corvette),maxHp:capHull(HULL.corvette),
      vy:(Math.random()<.5?1:-1)*(0.2+Math.random()*0.3),
      minY:HUD_H+60,maxY:H-60,fT:80,fR:70,pat:0,dead:false,sc,warp:220};
    initBeams(ent); return ent;
  }
  if(type==='iceni'){
    // Bosch's flagship. Corvette class hull, but a flagship, and the one
    // capital in the game with a name of its own in the HUD.
    const spr='coiceni';
    const img=IMGS[spr];
    const sc=hullScale(spr,0.95);
    const tough=Math.pow(1+ICENI_GROWTH, icenEscapes);
    const hp=capHull(Math.round(ICENI_HULL*tough));
    const ent={type:'corvette',iceni:true,label:'NTF Iceni',img:spr,faction:'ntf',
      pts:900,x:W-20,y,warpX:W-20,warpY:y,
      // From her width, so the whole hull is on screen. A fixed distance
      // from the edge left the stern of a ship this size outside.
      targetX:W-(img ? img.width*sc*0.5 : 150)-12-Math.random()*34,
      hp:hp,maxHp:hp,
      vy:(Math.random()<.5?1:-1)*(0.2+Math.random()*0.3),
      minY:HUD_H+60,maxY:H-60,fT:70,fR:70,pat:0,dead:false,sc,warp:200};
    // Four anti capital and five anti fighter beams, exactly as her mount
    // data states. She is a flagship and outguns any destroyer; the room
    // for that is bought with a longer deadline, not with a smaller
    // battery.
    initBeams(ent);
    return ent;
  }
  if(typeRole(type)==='de'){
    const pool=poolFor(type);
    const spr=spr0 || rnd(pool);
    const img=IMGS[spr];
    const sc=hullScale(spr,2.0);
    const ent={type:'destroyer',img:spr,faction:typeFac(type),
      pts:1200,x:W-80,y,warpX:W-80,warpY:y,
      targetX:W-230-Math.random()*34,
      hp:capHull(HULL.destroyer),maxHp:capHull(HULL.destroyer),
      vy:(Math.random()<.5?1:-1)*(0.15+Math.random()*0.2),
      minY:HUD_H+46,maxY:H-46,fT:100,fR:80,pat:0,dead:false,sc,warp:260};
    initBeams(ent); return ent;
  }
  // ── NON-COMBATANTS ──────────────────────────────────────
  // They live in enemies[] like everything else, so bullets, masks,
  // explosions and wreckage need no special case. What they do not have
  // is subsystems: hasSubsystems() covers cruisers upward, and a hull
  // this small dies long before a system could be shot off it.
  if(type==='freighter'){
    const spr=spr0||'frbast';
    const img=IMGS[spr];
    // Breite und Zaehigkeit kommen jetzt aus der Laenge. Vorher war jeder
    // Frachter 105 Bildpunkte breit und hatte 420 Rumpf, vom 27-Meter-Isis
    // bis zum 313-Meter-Triton.
    const sc=hullScale(spr,0.75);
    const _fh=hullPoints(spr,HULL.freighter);
    return {type:'freighter',img:spr,faction:'vasudan',
      pts:250,x:W+40,y,warpX:W+40,warpY:y,
      hp:_fh,maxHp:_fh,
      // Drifts across at walking pace until it is shot at. FS1 freighters
      // run the moment they take a hit rather than at a hull threshold,
      // so the trigger is damage, not a percentage.
      vx:-0.30,vy:0,ang:0,head:Math.PI,fleeing:false,
      minY:HUD_H+40,maxY:H-40,dead:false,sc,warp:150};
  }
  if(type==='container'){
    const spr=spr0||'fcvc3';
    const img=IMGS[spr];
    const sc=hullScale(spr,0.5);
    const _ch=hullPoints(spr,HULL.container);
    return {type:'container',img:spr,faction:'vasudan',
      pts:40,x:W+30,y,warpX:W+30,warpY:y,
      hp:_ch,maxHp:_ch,
      vx:0,vy:0,ang:0,head:Math.PI,
      dead:false,sc,warp:120};
  }
  if(type==='sentry'){
    const spr=spr0||'sgtrident';
    const img=IMGS[spr];
    // Breite aus der Laenge. Rumpf bewusst NICHT aus der Kurve: ein
    // Sperrgeschuetz feuert, ist also kein Nichtkaempfer, und Welle 7 soll
    // nicht nebenbei leichter werden, solange offen ist, ob sie zu hart ist.
    // Kleine Sperrgeschuetze folgen dem Jaegerboden nach unten.
    const sc=hullScale(spr,0.25);
    return {type:'sentry',img:spr,faction:'shivan',
      pts:180,x:W-60,y,warpX:W-60,warpY:y,
      hp:HULL.sentry,maxHp:HULL.sentry,
      // A gun platform holds station. It has no drive, so vx stays at
      // zero and the update never moves it: the player has to come.
      vx:0,vy:0,ang:0,head:Math.PI,
      fT:(40+Math.random()*40)|0,fR:(70+Math.random()*40)|0,
      dead:false,sc,warp:140};
  }
  if(typeRole(type)==='in'){
    const spr=spr0 || rnd(INSTALLATIONS);
    const img=IMGS[spr];
    const sc=hullScale(spr,1.0);
    const ent={type:'station',img:spr,faction:typeFac(type),
      pts:1500,x:W*0.80,y:H*0.5,warpX:W*0.80,warpY:H*0.5,
      targetX:null,
      hp:capHull(HULL.station),maxHp:capHull(HULL.station),
      vx:0,vy:0,minY:H*0.5,maxY:H*0.5,
      fT:90,fR:80,pat:0,dead:false,sc,warp:0,warpMax:1,station:true};
    initSubsystems(ent); initBeams(ent); return ent;
  }
  if(type==='ast'){
    const sc=0.35+Math.random()*0.3;
    const ast={type:'asteroid',img:null,pts:60,x:W+30,y,hp:HULL.asteroid,maxHp:HULL.asteroid,
      vx:astStill?0:-(1+Math.random()*2.5), vy:astStill?0:(Math.random()-.5)*1.5,
      rot:Math.random()*Math.PI*2,rotS:(Math.random()-.5)*0.06,sc,dead:false};
    // In the escort wave the belt is not scenery, it is the threat. The
    // rocks are put on a course for the ship under protection, otherwise
    // defending her is luck rather than flying.
    if(astAim){
      let g=null;
      for(const o of allies) if(o.guard && !o.dead){ g=o; break; }
      if(g){
        const sp=1.4+Math.random()*1.1;
        const dx=g.x-ast.x, dy=g.y-ast.y, L=Math.hypot(dx,dy)||1;
        ast.vx=dx/L*sp; ast.vy=dy/L*sp;
      }
    }
    return ast;}
  if(type==='boss_ntf'){
    bossAlive=true;
    const spr=rnd(ROLES.ntf_super);
    const img=IMGS[spr];
    const sc=hullScale(spr,1.0);
    const bn={type:'boss',img:spr,faction:'ntf',pts:3000,
      // A ship this size holds station. The drift belonged to a cruiser.
      x:W-80,y:H/2,hp:capHull(HULL.boss_ntf),maxHp:capHull(HULL.boss_ntf),vy:0,minY:HUD_H+100,maxY:H-100,
      fT:120,fR:50,pat:0,phase:1,targetX:W-200,dead:false,sc,warp:300,
      warpX:W-80,warpY:H/2};
    initBeams(bn);return bn;}
  if(type==='boss_sh'){
    bossAlive=true;
    const spr=rnd(ROLES.shivan_super);
    const img=IMGS[spr];
    const sc=hullScale(spr,1.1);
    // Marker used below to find the arms, since only she has them.
    const bs={type:'boss',img:spr,faction:'shivan',pts:4000,
      x:W-80,y:H/2,hp:capHull(HULL.boss_sh),maxHp:capHull(HULL.boss_sh),vy:0,minY:HUD_H+110,maxY:H-110,
      fT:100,fR:45,pat:0,phase:1,targetX:W-220,dead:false,sc,warp:320,
      warpX:W-80,warpY:H/2};
    initBeams(bs);return bs;}
}

// ── DAMAGE ───────────────────────────────────────────────────
// The only path by which an enemy takes damage. Shields absorb first,
// only the remainder reaches the hull.
// fromPlayer records who did the work. Tickets are handed out on the
// player's share of the damage rather than on the killing blow, because a
// destroyer rarely dies to the player's last bolt and a last hit rule
// would make calling an escort actively harmful.
// kind is 'bolt', 'sec' or 'beam' and only matters to the Lucifer's shield.
function damageEnemy(e, dmg, hx, hy, fromPlayer, kind){
  if(!e || e.dead) return;
  if(fromPlayer) e.pDmg = (e.pDmg||0) + dmg;
  if(e.bShield > 0){
    // A reactor is a hole in the shield rather than something under it.
    // Covering its own weak point would make it not a weak point.
    const r = reactorAt(e, hx, hy);
    if(r){
      r.hp -= dmg;
      if(hx!=null) addShieldFlare(e, hx, hy, 1.4);
      if(r.hp <= 0){
        r.dead = true;
        e.bShield = Math.max(0, e.bShield - e.bShieldMax*LUCI_REACTOR_CUT);
        const p = reactorPos(e, r);
        spawnFireball(p.x, p.y, 46, 40);
        spawnDebris(p.x, p.y, 16, 255,220,120, 255,120,0, true);
      }
      return;                       // never reaches the hull
    }
    e.bShield = Math.max(0, e.bShield - dmg*(SHIELD_MULT[kind||'bolt']||0.10));
    if(hx!=null) addShieldFlare(e, hx, hy, 1);
    return;                         // hull is untouchable while it stands
  }
  // Under the shield, or with no shield at all: a hit on a subsystem takes
  // it apart at full rate and still bleeds half into the hull, so working
  // on one is a trade rather than time thrown away.
  if(e.subs) dmg = subHit(e, dmg, hx, hy);
  if(e.sh > 0){
    const pen = shieldPen(e, kind);
    if(pen < 1){
      // Deflected. The shield gives up its fraction and the round carries
      // nothing through, however heavy it was. Without the early return a
      // strong hit would still spill onto the hull and the rule would only
      // slow the fleet down instead of stopping it.
      e.sh = Math.max(0, e.sh - dmg*pen);
      e.shDelay = (e.type==='bomber' ? SHIELD.bomber.delay : SHIELD.fighter.delay);
      e.shHit = SH_FLASH;
      return;
    }
    const absorbed = Math.min(e.sh, dmg);
    e.sh -= absorbed;
    e.shDelay = (e.type==='bomber' ? SHIELD.bomber.delay : SHIELD.fighter.delay);
    e.shHit = SH_FLASH;
    dmg -= absorbed;
    if(dmg <= 0) return;
  }
  if(e.invuln) return;      // Station, die nicht fallen soll
  if(e.rollT!=null) return; // bricht schon auseinander
  e.hp -= dmg;
  if(e.hp <= 0 && !e.dead &&
     (e.type==='destroyer'||e.type==='boss'||e.type==='station')){
    // Sie stirbt nicht sofort: erst die Sekundaerexplosionen.
    e.hp = 1; e.rollT = DEATH_ROLL; e.noFire = true;
    return;
  }
  // Der Riegel. Greift nur, solange der Auftrag noch offen ist - sobald
  // Waffen und Antrieb hin sind, faellt er weg und das Schiff laesst sich
  // normal fertigmachen.
  // Sprungfaehigkeit gerade verloren? Einmalig melden.
  if(!e.navMsgDone && e.flee && hasSubsystems(e) && !subOK(e,'navigation')){
    e.navMsgDone = true;
    SUB_MSGS.push({x:e.x, y:e.y-30, txt:'TARGET CANNOT JUMP', life:170, ml:170, ally:true});
  }
  // Ein Schiff, das ueberlaufen soll, kann vorher nicht sterben - sonst
  // haengt die Pointe der Welle am Zufall des Gefechts.
  if(e.defectLock){
    const dfl = e.maxHp * DISABLE_HULL_FLOOR;
    if(e.hp < dfl) e.hp = dfl;
  }
  if(e.disableTgt && !e.disableMet){
    const floor = e.maxHp * DISABLE_HULL_FLOOR;
    if(e.hp < floor) e.hp = floor;
    if(!subOK(e,'weapons') && !subOK(e,'engines')) e.disableMet = true;
  }
}

// One reading for hull condition everywhere: the player's bar in the HUD
// and every capital ship's bar on the field. Class and faction used to
// decide the colour, which meant a full destroyer and a dying one looked
// identical and only the length differed.
function hullCol(r){
  if(r > 0.60) return '#00dd55';
  if(r > 0.35) return '#d8dd00';
  if(r > 0.15) return '#ff9900';
  return '#ff2a1a';
}
// Below this the bar pulses, because a ship this close to dying is worth
// noticing whether it is yours or theirs.
const HULL_CRIT = 0.15;

// ── SHIELD BUBBLE ───────────────────────────────────────────────
// SH_FLASH is how long one flare lasts, in simulation steps.
// At 100 Hz, 30 steps is roughly a third of a second.
const SH_FLASH = 30;

// Draws a shield bubble around a point. frac is the remaining
// shield strength from 0 to 1, hit the remaining flare time.
function shieldBubble(cx, cy, rx, ry, frac, hit, col, ang){
  if(hit <= 0 || frac <= 0) return;
  const t = hit/SH_FLASH;                 // 1 right after the hit, 0 at the end
  const base = 0.35 + 0.65*frac;          // a weak shield glows dimmer
  const a = ang || 0;                     // the bubble hugs the hull, so it turns with it
  ctx.save();

  // Fill
  const g = ctx.createRadialGradient(cx, cy, Math.min(rx,ry)*0.25, cx, cy, Math.max(rx,ry));
  g.addColorStop(0, 'rgba(255,255,255,0)');
  g.addColorStop(0.72, col.replace('COL', String(0.18*t*base)));
  g.addColorStop(1, col.replace('COL', String(0.55*t*base)));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, a, 0, Math.PI*2); ctx.fill();

  // Glowing rim
  ctx.globalCompositeOperation = 'lighter';
  ctx.lineWidth = 3.5;
  ctx.strokeStyle = col.replace('COL', String(0.95*t*base));
  ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, a, 0, Math.PI*2); ctx.stroke();

  // Bright inner rim right after the hit
  if(t > 0.45){
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = 'rgba(255,255,255,' + (0.9*(t-0.45)/0.55) + ')';
    ctx.beginPath(); ctx.ellipse(cx, cy, rx*0.97, ry*0.97, a, 0, Math.PI*2); ctx.stroke();
  }

  // Outward travelling pressure wave
  const ex = rx*(1 + (1-t)*0.35), ey = ry*(1 + (1-t)*0.35);
  ctx.lineWidth = 2;
  ctx.strokeStyle = col.replace('COL', String(0.5*t*t*base));
  ctx.beginPath(); ctx.ellipse(cx, cy, ex, ey, a, 0, Math.PI*2); ctx.stroke();

  ctx.restore();
}

// The shield is the ship's own outline, not an ellipse laid over it. The
// sprite is drawn into an offscreen canvas, filled with the shield colour
// through source-in so only its solid pixels survive, then blurred outward
// in a few passes. Built once per hull and kept, because blurring a sprite
// this size every frame would not hold sixty frames on a tablet.
const SHIELD_SKINS = {};
const SHIELD_PAD = 14;
function shieldSkin(key){
  if(SHIELD_SKINS[key]) return SHIELD_SKINS[key];
  const img = IMGS[key];
  if(!img) return null;
  const w = img.width + SHIELD_PAD*2, h = img.height + SHIELD_PAD*2;
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h;
  const c = cv.getContext('2d');
  c.drawImage(img, SHIELD_PAD, SHIELD_PAD);
  c.globalCompositeOperation = 'source-in';
  c.fillStyle = '#6fd8ff';
  c.fillRect(0,0,w,h);
  c.globalCompositeOperation = 'source-over';
  // Spread the silhouette outwards so the skin sits around the hull
  // rather than exactly on it.
  const sp = document.createElement('canvas');
  sp.width = w; sp.height = h;
  const s = sp.getContext('2d');
  s.shadowColor = '#6fd8ff';
  s.shadowOffsetX = 0; s.shadowOffsetY = 0;
  for(let p=0;p<3;p++){
    s.shadowBlur = 4 + p*4;
    s.drawImage(cv, 0, 0);
  }
  SHIELD_SKINS[key] = {cv:sp, pad:SHIELD_PAD, w:w, h:h};
  return SHIELD_SKINS[key];
}

function addShieldFlare(e, x, y, str){
  if(!e.shieldFlares) e.shieldFlares = [];
  if(e.shieldFlares.length > 14) e.shieldFlares.shift();
  // Stored relative to the hull so the flare travels with the ship.
  e.shieldFlares.push({lx:x-e.x, ly:y-e.y, life:34, ml:34, str:str||1});
}

// Small scratch canvas for the flares. One flare is a piece of the skin cut
// to a soft circle, so the flash stays inside the silhouette instead of
// sitting on top of it as a disc.
const FL_SIZE = 120;
let FL_CV = null;
function flareCanvas(){
  if(!FL_CV){ FL_CV = document.createElement('canvas'); FL_CV.width = FL_SIZE; FL_CV.height = FL_SIZE; }
  return FL_CV;
}

function drawLuciShield(e){
  if(!(e.bShield > 0)) return;
  const skin = shieldSkin(e.img);
  if(!skin) return;
  const frac = e.bShield/e.bShieldMax;
  const pulse = 0.5 + 0.5*Math.sin(fc*0.045);
  // A weakening shield thins out, which doubles as the readout for which
  // phase of the fight this is.
  const base = (0.14 + 0.34*frac) * (0.82 + 0.18*pulse);
  const sc = e.sc;
  const dw = skin.w*sc, dh = skin.h*sc;
  ctx.save();
  ctx.translate(e.x, e.y);
  if(e.ang) ctx.rotate(e.ang);
  if(e.flip) ctx.scale(-1,1);
  ctx.globalCompositeOperation = 'lighter';
  ctx.globalAlpha = base;
  ctx.drawImage(skin.cv, -dw/2, -dh/2, dw, dh);
  ctx.restore();
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';

  if(!e.shieldFlares || !e.shieldFlares.length) return;
  const fcv = flareCanvas();
  const fx = fcv.getContext('2d');
  for(let i=e.shieldFlares.length-1;i>=0;i--){
    const f = e.shieldFlares[i];
    if(--f.life <= 0){ e.shieldFlares.splice(i,1); continue; }
    const t = f.life/f.ml;
    const wx = e.x+f.lx, wy = e.y+f.ly;
    fx.setTransform(1,0,0,1,0,0);
    fx.clearRect(0,0,FL_SIZE,FL_SIZE);
    // Copy the piece of skin that lies under the impact.
    fx.save();
    fx.translate(FL_SIZE/2, FL_SIZE/2);
    fx.translate(-f.lx, -f.ly);
    if(e.ang) fx.rotate(e.ang);
    if(e.flip) fx.scale(-1,1);
    fx.drawImage(skin.cv, -dw/2, -dh/2, dw, dh);
    fx.restore();
    // Cut it to a soft circle.
    fx.globalCompositeOperation = 'destination-in';
    const g = fx.createRadialGradient(FL_SIZE/2,FL_SIZE/2,0,FL_SIZE/2,FL_SIZE/2,FL_SIZE/2);
    g.addColorStop(0,'rgba(255,255,255,1)');
    g.addColorStop(0.45,'rgba(255,255,255,0.55)');
    g.addColorStop(1,'rgba(255,255,255,0)');
    fx.fillStyle = g;
    fx.fillRect(0,0,FL_SIZE,FL_SIZE);
    fx.globalCompositeOperation = 'source-over';
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = Math.min(1, t*1.5) * 0.85 * f.str;
    ctx.drawImage(fcv, wx-FL_SIZE/2, wy-FL_SIZE/2);
    ctx.restore();
    ctx.globalAlpha = 1;
  }
}

// Reactors are only worth marking while the shield is up, since after that
// there is nothing left for them to do.
function drawReactors(e){
  if(!e.reactors || !(e.bShield > 0)) return;
  const pulse = 0.5 + 0.5*Math.sin(fc*0.16);
  for(const r of e.reactors){
    if(r.dead) continue;
    const p = reactorPos(e, r);
    const hr = Math.max(0, r.hp/r.maxHp);
    ctx.save();
    ctx.translate(p.x|0, p.y|0);
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = 0.55 + 0.45*pulse;
    ctx.strokeStyle = hullCol(hr);
    ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.arc(0,0,9,0,Math.PI*2); ctx.stroke();
    ctx.beginPath(); ctx.arc(0,0,4,0,Math.PI*2); ctx.stroke();
    ctx.globalAlpha = 1;
    ctx.restore();
  }
}

// One glyph per system, so five of them can be told apart without a word
// on screen. They are learned in a wave or two and cost no space at all.
// ── RUMPFANZEIGE ─────────────────────────────────────────────
// Drei Zeilen dicht am Rumpf: Name, Bloecke, Subsysteme. Die Blockzahl
// haengt an der Breite des Schiffs - ein Aten traegt keine acht Bloecke
// plus fuenf Symbole, ohne breiter zu werden als er selbst.
const HB_SEG_W = 12, HB_SEG_GAP = 3, HB_SEG_H = 5;
function hullSegCount(bw){
  const n = Math.floor((bw + HB_SEG_GAP) / (HB_SEG_W + HB_SEG_GAP));
  return Math.max(3, Math.min(10, n));
}
function drawHullBlocks(e, bx, by, bw, ratio, showShield){
  if(e.invuln) return;
  const n = hullSegCount(bw);
  const full = n*HB_SEG_W + (n-1)*HB_SEG_GAP;
  const x0 = (e.x - full*0.5)|0;
  const lit = Math.max(0, Math.min(n, Math.ceil(ratio*n)));
  const col = showShield ? '#6fd8ff' : hullCol(ratio);
  const crit = (ratio<=HULL_CRIT && !showShield);
  for(let i=0;i<n;i++){
    const sx = x0 + i*(HB_SEG_W+HB_SEG_GAP);
    ctx.globalAlpha = 1;
    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.fillRect(sx, by, HB_SEG_W, HB_SEG_H);
    if(i < lit){
      // Nur der letzte verbleibende Block pulsiert, nicht die ganze Reihe.
      ctx.globalAlpha = (crit && i===lit-1) ? (0.45+0.55*Math.sin(fc*0.22)) : 1;
      ctx.fillStyle = col;
      ctx.fillRect(sx, by, HB_SEG_W, HB_SEG_H);
    }
  }
  ctx.globalAlpha = 1;
  ctx.strokeStyle = (e.side==='ally') ? 'rgba(120,190,255,0.75)' : 'rgba(255,110,90,0.75)';
  ctx.lineWidth = 1;
  ctx.strokeRect(x0-1.5, by-1.5, full+3, HB_SEG_H+3);
  ctx.globalAlpha = 1;

  // Subsysteme, dieselben Symbole wie auf dem Rumpf - aber OBERHALB des
  // Balkens, sonst liegen sie auf dem Schiff.
  if(e.subs && e.subs.length){
    const sr = 4, sg = 4;
    const sw = e.subs.length*(sr*2) + (e.subs.length-1)*sg;
    let sx = e.x - sw*0.5 + sr;
    const sy = by - 8;
    for(const s of e.subs){
      const ok = s.hp > 0;
      ctx.save();
      ctx.translate(sx|0, sy|0);
      // Keine eigene Farbe: hell heisst heil, rot heisst hin. Das UI hat
      // genug Farben.
      ctx.globalAlpha = ok ? 0.75 : 0.9;
      ctx.strokeStyle = ok ? '#cfcfc8' : '#ff5a44';
      ctx.fillStyle   = ok ? '#cfcfc8' : '#ff5a44';
      ctx.lineWidth = 1;
      drawSubGlyph(s.id, sr*1.7);
      if(!ok){
        ctx.beginPath();
        ctx.moveTo(-sr,-sr); ctx.lineTo(sr,sr);
        ctx.moveTo(sr,-sr);  ctx.lineTo(-sr,sr);
        ctx.stroke();
      }
      ctx.restore();
      sx += sr*2 + sg;
    }
  }

  // Name. Aus derselben Quelle wie die Auftragszeile.
  const nm = e.label || shipName(e.img, '');
  if(nm){
    ctx.save();
    ctx.font = 'bold 9px Courier New';
    ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
    ctx.globalAlpha = 0.85;
    ctx.fillStyle = (e.side==='ally') ? '#9fd0ff' : '#ffb0a0';
    ctx.fillText(nm, e.x|0, by-19);
    ctx.restore();
  }
}

function drawSubGlyph(id, r){
  ctx.beginPath();
  if(id==='weapons'){ ctx.arc(0,0,r*0.42,0,Math.PI*2); ctx.fill(); return; }
  if(id==='engines'){
    ctx.moveTo(-r*0.5,-r*0.45); ctx.lineTo(r*0.15,0); ctx.lineTo(-r*0.5,r*0.45);
    ctx.moveTo(r*0.05,-r*0.45); ctx.lineTo(r*0.6,0); ctx.lineTo(r*0.05,r*0.45);
    ctx.stroke(); return;
  }
  if(id==='navigation'){
    ctx.arc(0,0,r*0.45,0,Math.PI*2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-r*0.62,0); ctx.lineTo(r*0.62,0); ctx.stroke(); return;
  }
  if(id==='sensors'){
    ctx.moveTo(-r*0.6,0); ctx.lineTo(r*0.6,0);
    ctx.moveTo(0,-r*0.6); ctx.lineTo(0,r*0.6); ctx.stroke();
    ctx.beginPath(); ctx.arc(0,0,r*0.28,0,Math.PI*2); ctx.stroke(); return;
  }
  // communication: three rising arcs
  for(let i=1;i<=3;i++){
    ctx.beginPath();
    ctx.arc(-r*0.15, r*0.35, r*0.28*i, -Math.PI*0.85, -Math.PI*0.15);
    ctx.stroke();
  }
}

// The name is spelled out only for the one the player is lining up on.
// Anything more would paper the field over with labels.
function drawSubsystems(e){
  if(!e.subs) return;
  const pulse=0.5+0.5*Math.sin(fc*0.14);
  let near=null, nearD=SUB_NAME_R*SUB_NAME_R, nearP=null;
  const pa=player.head||0, cs=Math.cos(pa), sn=Math.sin(pa);
  for(const s of e.subs){
    if(s.dead) continue;                    // gone is gone, nothing is drawn
    const p=subPos(e,s);
    const hr=Math.max(0,s.hp/s.maxHp);
    ctx.save();
    ctx.translate(p.x|0,p.y|0);
    ctx.globalCompositeOperation='lighter';
    ctx.globalAlpha=0.5+0.4*pulse;
    ctx.strokeStyle=hullCol(hr); ctx.fillStyle=hullCol(hr); ctx.lineWidth=1.5;
    // Die Marke folgt der tatsaechlichen Trefferflaeche, sonst zeigt sie
    // bei einem von Hand vergroesserten Subsystem etwas Falsches an.
    const rr=Math.max(7, Math.min(20, subRadius(e, s)*0.55));
    ctx.beginPath(); ctx.arc(0,0,rr,0,Math.PI*2); ctx.stroke();
    drawSubGlyph(s.id, rr);
    ctx.restore();
    ctx.globalAlpha=1;
    if(GS==='playing'){
      const dx=p.x-player.x, dy=p.y-player.y;
      const d2=dx*dx+dy*dy;
      if(d2<nearD){
        const proj=(dx*cs+dy*sn)/Math.max(1,Math.sqrt(d2));
        if(proj>Math.cos(SUB_NAME_CONE)){ nearD=d2; near=s; nearP=p; }
      }
    }
  }
  if(near){
    ctx.save();
    ctx.font='bold 9px Courier New';
    ctx.textAlign='center'; ctx.textBaseline='bottom';
    const tw=ctx.measureText(near.label).width;
    ctx.globalAlpha=0.7; ctx.fillStyle='#000';
    ctx.fillRect((nearP.x-tw/2-4)|0,(nearP.y-25)|0,(tw+8)|0,13);
    ctx.globalAlpha=1;
    ctx.fillStyle=hullCol(near.hp/near.maxHp);
    ctx.fillText(near.label,nearP.x,nearP.y-13);
    ctx.restore();
    ctx.textAlign='left'; ctx.textBaseline='top';
  }
}

function drawSubMsgs(){
  for(let i=SUB_MSGS.length-1;i>=0;i--){
    const m=SUB_MSGS[i];
    if(--m.life<=0){ SUB_MSGS.splice(i,1); continue; }
    const t=m.life/m.ml;
    ctx.save();
    // Fades only over the last quarter, so the three seconds are readable
    // rather than three seconds of fading.
    ctx.globalAlpha=Math.min(1,t*4);
    ctx.font='bold 10px Courier New';
    ctx.textAlign='center'; ctx.textBaseline='middle';
    const y=m.y-(1-t)*30;
    const tw=ctx.measureText(m.txt).width;
    ctx.fillStyle='#100600';
    ctx.fillRect((m.x-tw/2-5)|0,(y-8)|0,(tw+10)|0,16);
    ctx.fillStyle = (m.tone==='good') ? '#3ce06a'
                  : (m.tone==='bad')  ? '#ff4a33'
                  : (m.tone==='warn') ? '#ffcc44'
                  : (m.ally?'#ffcc44':'#ff8844');
    ctx.fillText(m.txt,m.x,y);
    ctx.restore();
  }
  ctx.textAlign='left'; ctx.textBaseline='top';
}

function drawShield(e){
  if(!e.maxSh || e.shHit <= 0 || e.sh <= 0) return;
  const img = IMGS[e.img]; if(!img) return;
  const col = e.faction==='shivan' ? 'rgba(255,110,70,COL)' : 'rgba(90,190,255,COL)';
  shieldBubble(e.x, e.y, img.width*e.sc*0.66, img.height*e.sc*0.78,
               e.sh/e.maxSh, e.shHit, col, e.ang||0);
}

// The player's own hull is one small sprite among dozens once a wave is
// running. This ring makes it findable. It sits at the hold radius, so it
// also tells the truth about where pointer movement starts, and the bright
// arc marks the nose so heading is readable without studying the sprite.
function drawHoldRing(){
  const r = player.holdR || HOLD_R_MIN;
  const pulse = 0.5 + 0.5*Math.sin(fc*0.06);
  ctx.save();
  ctx.translate(player.x|0, player.y|0);
  ctx.globalCompositeOperation = 'lighter';
  // Soft halo underneath, so the ring survives a bright nebula.
  const g = ctx.createRadialGradient(0,0,r*0.70,0,0,r*1.14);
  g.addColorStop(0,   'rgba(120,215,255,0)');
  g.addColorStop(0.65,'rgba(120,215,255,'+(0.10+0.06*pulse).toFixed(3)+')');
  g.addColorStop(1,   'rgba(120,215,255,0)');
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.arc(0,0,r*1.14,0,Math.PI*2); ctx.fill();
  // Dashed and slowly rotating, so it never reads as a shield bubble.
  ctx.lineWidth = 1.6;
  ctx.strokeStyle = 'rgba(150,225,255,'+(0.55+0.25*pulse).toFixed(3)+')';
  ctx.setLineDash([7,6]);
  ctx.lineDashOffset = -fc*0.25;
  ctx.beginPath(); ctx.arc(0,0,r,0,Math.PI*2); ctx.stroke();
  ctx.setLineDash([]);
  ctx.rotate(player.head||0);
  ctx.lineWidth = 2.6;
  ctx.strokeStyle = 'rgba(215,245,255,0.95)';
  ctx.beginPath(); ctx.arc(0,0,r,-0.30,0.30); ctx.stroke();
  ctx.restore();
}

function drawPlayerShield(){
  if(player.shHit <= 0 || player.sh <= 0) return;
  const img = IMGS[player.ship]; if(!img) return;
  const sc = playerSc();
  shieldBubble(player.x, player.y, img.width*sc*0.72, img.height*sc*0.85,
               player.sh/player.maxSh, player.shHit, 'rgba(120,215,255,COL)', player.ang||0);
}

// ── STATION KEEPING ───────────────────────────────────────────
// Capital ships are wide. A destroyer covers almost half the play field,
// so two of them picking a random height will overlap most of the time.
// On arrival each one claims the emptiest lane it can find, and while on
// station a weak force keeps them from drifting into one another.

const CAPITAL_GAP = 1.15;   // required clearance as a multiple of half heights
const SEPARATE_FORCE = 0.10;

// Nothing should ever slide off the top or bottom edge. The old per class
// margins were fixed numbers that ignored how tall a sprite actually is,
// so large hulls hung into the HUD or off the bottom.
function clampToField(o, half){
  const hh = (half != null) ? half : halfH(o);
  const top = HUD_H + hh, bot = H - hh;
  if(top >= bot){ o.y = (HUD_H + H)*0.5; return; }   // taller than the field
  if(o.y < top){ o.y = top; if(o.vy < 0) o.vy = -o.vy; }
  else if(o.y > bot){ o.y = bot; if(o.vy > 0) o.vy = -o.vy; }
}

function isCapital(o){
  return o.type==='cruiser' || o.type==='corvette'
      || o.type==='destroyer' || o.type==='boss';
}

// Half the rendered height, used as the ship's vertical footprint.
// Der sichtbare Teil eines Sprites, ohne den durchsichtigen Rand um das
// Schiff herum. Ein Bild ist immer groesser als das Schiff darin, und wer
// gegen das Bild prueft, laesst durchsichtige Ecken zusammenstossen - dann
// explodiert etwas, das sich auf dem Schirm sichtbar nicht beruehrt hat.
// Gerechnet wird aus der Maske, die fuer die Trefferabfrage ohnehin gebaut
// wird, und das Ergebnis wird gemerkt: einmal je Sprite, nicht je Schritt.
const SPR_BOX = {};
function spriteBox(key){
  if(SPR_BOX[key] !== undefined) return SPR_BOX[key];
  const img = IMGS[key];
  if(!img || !img.width) return (SPR_BOX[key] = null);
  // Faellt die Maske aus, gilt das ganze Bild - lieber zu grosszuegig als
  // gar keine Pruefung.
  let box = {cx:0, cy:0, hw:img.width*0.5, hh:img.height*0.5};
  const m = getMask(key);
  if(m){
    let x0=m.w, y0=m.h, x1=-1, y1=-1;
    for(let y=0;y<m.h;y++){
      for(let x=0;x<m.w;x++){
        if(!m.bits[y*m.w+x]) continue;
        if(x<x0) x0=x;
        if(x>x1) x1=x;
        if(y<y0) y0=y;
        if(y>y1) y1=y;
      }
    }
    if(x1>=x0 && y1>=y0){
      // Die Maske ist verkleinert, also zurueck auf Bildmass rechnen.
      const fx = img.width/m.w, fy = img.height/m.h;
      const bx0 = x0*fx, bx1 = (x1+1)*fx;
      const by0 = y0*fy, by1 = (y1+1)*fy;
      box = {cx:(bx0+bx1)/2 - img.width/2,
             cy:(by0+by1)/2 - img.height/2,
             hw:(bx1-bx0)/2, hh:(by1-by0)/2};
    }
  }
  return (SPR_BOX[key] = box);
}
// Der sichtbare Rumpf eines Schiffs in Weltkoordinaten. Der Mittelpunkt des
// Rumpfes ist nicht der Mittelpunkt des Bildes, deshalb wird er mitgefuehrt.
function hullBox(o){
  const b = spriteBox(o.img), sc = o.sc || 1;
  if(!b) return {cx:o.x, cy:o.y, hw:40*sc, hh:20*sc};
  const s = o.flip ? -1 : 1;
  return {cx:o.x + b.cx*sc*s, cy:o.y + b.cy*sc, hw:b.hw*sc, hh:b.hh*sc};
}
// Beruehren sich zwei Rumpfe? Waagerecht und senkrecht getrennt geprueft:
// ein Kreis laesst ein Schiff hoch ueber einem anderen explodieren, weil
// der Abstand dort auch klein ist. overlap ist, wie tief sie ineinander
// stehen muessen, damit es als Treffer gilt und nicht als Streifschuss.
function hullsTouch(a, b, overlap){
  const A = hullBox(a), B = hullBox(b);
  return Math.abs(A.cx-B.cx) < A.hw+B.hw-overlap
      && Math.abs(A.cy-B.cy) < A.hh+B.hh-overlap;
}
// Wie tief zwei Rumpfe ineinander stehen, in Punkten, je Achse. Negativ
// heisst: sie stehen auseinander.
function hullDepth(a, b){
  const A = hullBox(a), B = hullBox(b);
  return {x:A.hw+B.hw - Math.abs(A.cx-B.cx),
          y:A.hh+B.hh - Math.abs(A.cy-B.cy),
          hw:A.hw, hh:A.hh};
}
// Steckt a wirklich in b? Ein Rechteck um ein Schiff, das nicht
// rechteckig ist, stoesst mit seinen Ecken zusammen, lange bevor die
// Schiffe sich beruehren - fuer einen Rammstoss ist Beruehrung deshalb die
// falsche Frage. Gemessen wird an der Groesse des Angreifers: share=1 heisst,
// er muss um seine eigene halbe Laenge im Ziel stehen.
function hullsBite(a, b, share){
  const d = hullDepth(a, b);
  return d.x > d.hw*share && d.y > d.hh*share;
}
function halfH(o){
  const img = IMGS[o.img];
  return img ? img.height*o.sc*0.5 : 30;
}
function halfW(o){
  const img = IMGS[o.img];
  return img ? img.width*o.sc*0.5 : 40;
}

// Every capital ship currently on the field, both sides.
// Two capitals sharing screen space must keep at least this much vertical
// distance regardless of how small they are.
const CAPITAL_MIN_GAP = 70;

function capitalsOnField(exclude){
  const out=[];
  for(const o of enemies) if(o!==exclude && !o.dead && isCapital(o)) out.push(o);
  for(const o of allies)  if(o!==exclude && !o.dead && isCapital(o)) out.push(o);
  return out;
}

// Pick the height with the largest clearance to everyone else.
function assignStation(e){
  if(!isCapital(e)) return;
  const others = capitalsOnField(e);
  const hh = halfH(e);
  const lo = Math.max(e.minY!=null ? e.minY : HUD_H+60, HUD_H+hh);
  const hi = Math.min(e.maxY!=null ? e.maxY : H-60,     H-hh);
  if(lo >= hi){ e.y = (HUD_H+H)*0.5; e.warpY = e.y; return; }
  if(!others.length){ e.y = lo + Math.random()*(hi-lo); e.warpY = e.y; return; }

  let bestY = e.y, bestScore = -Infinity;
  const steps = 24;
  for(let i=0;i<=steps;i++){
    const cy = lo + (hi-lo)*(i/steps);
    let worst = Infinity;
    for(const o of others){
      // horizontal overlap only matters if they share screen space
      const dxNeed = halfW(e)+halfW(o);
      const dxHave = Math.abs((e.targetX!=null?e.targetX:e.x) - o.x);
      const overlapX = Math.max(0, 1 - dxHave/dxNeed);
      if(overlapX <= 0) continue;
      // A hard floor on top of the proportional gap, so two ships whose
      // bands nearly touch still end up in clearly separate lanes instead
      // of one hovering permanently in front of the other.
      const need = Math.max((halfH(e)+halfH(o))*CAPITAL_GAP, CAPITAL_MIN_GAP);
      worst = Math.min(worst, Math.abs(cy-o.y) - need*overlapX);
    }
    if(worst === Infinity) worst = 1000;      // nobody in the way at all
    // a little noise so repeated waves do not always use the same lane
    const score = worst + Math.random()*6;
    if(score > bestScore){ bestScore = score; bestY = cy; }
  }
  e.y = bestY; e.warpY = bestY;
}

// Gentle mutual push so drifting ships do not slide into each other.
function separateCapitals(){
  const list = capitalsOnField(null);
  for(let i=0;i<list.length;i++){
    for(let j=i+1;j<list.length;j++){
      const a=list[i], b=list[j];
      if(a.warp>0 || b.warp>0 || a.warpOut>0 || b.warpOut>0) continue;
      if(a.colossus || b.colossus) continue;   // she does not give way
      // Ein Rammkurs weicht nicht aus, und sein Ziel darf nicht
      // weggedrueckt werden - der Aufprall ist der Sinn der Sache.
      if(a.capRam || b.capRam) continue;

      const needX = halfW(a)+halfW(b);
      if(Math.abs(a.x-b.x) > needX) continue;      // not sharing screen space

      const needY = (halfH(a)+halfH(b))*CAPITAL_GAP;
      let dy = b.y-a.y;
      if(Math.abs(dy) >= needY) continue;
      if(dy === 0) dy = (Math.random()<0.5?-1:1)*0.1;

      const push = (needY-Math.abs(dy))*SEPARATE_FORCE*0.5;
      const dir = dy>0 ? 1 : -1;
      // heavier ships give way less
      const wa = halfH(a), wb = halfH(b);
      const tot = wa+wb;
      a.y -= push*dir*(wb/tot)*2;
      b.y += push*dir*(wa/tot)*2;

      if(a.minY!=null) a.y = Math.max(a.minY, Math.min(a.maxY, a.y));
      if(b.minY!=null) b.y = Math.max(b.minY, Math.min(b.maxY, b.y));

      // steer their patrol away from each other as well
      if(a.vy*(-dir) < 0) a.vy *= -1;
      if(b.vy*( dir) < 0) b.vy *= -1;
    }
  }
}

// ── VASUDAN PRESENCE ──────────────────────────────────────
// They were only ever visible if the player called them. Two ways in that
// do not require making them enemies, which would make no sense: an escort
// job, and unprompted reinforcement in the two hardest waves.
let guardWanted = false, guardSpawned = false, guardLost = false;
let reinfAt = 0, reinfDone = false;
// Sie kommt angeschlagen an, aber nicht halbtot: 0.45 waren 2925 von 6500
// gegen zwei Bomberstaffeln, und Bomber sind gegen Grosskampfschiffe
// gebaut. 0.70 sind 4550 und damit eine Aufgabe statt einer Verlustmeldung.
const GUARD_HULL_FRAC = 0.70;
const GUARD_PENALTY = 900;
// Ein entkommener Gegner kostet, was er wert gewesen waere, noch einmal.
const ESCAPE_PENALTY = 1.0;
// Fahrt eines querenden Schuetzlings, Bildpunkte je Schritt. Bei 100
// Schritten je Sekunde sind 0.42 rund 42 px/s, also gut 20 Sekunden fuer
// die 880 Bildpunkte von links aussen bis rechts hinaus. Lange genug, um
// ihn verlieren zu koennen, kurz genug, um nicht zu warten.
const PROTECT_CROSS_SPD = 0.42;
// Set per wave, so one escort job can differ from the next.
let guardClass = 'cruiser', guardFrac = GUARD_HULL_FRAC, guardReward = 'cruiser';
let astAim = false;
// An escort that crosses a belt rather than holding a station. The wave
// ends when she is through, not when the field is empty, so there is no
// pile of rocks left to count down.
// She used to run to x=860, sixty pixels past the right edge, and a
// destroyer is wide: her bow left the field long before that and she kept
// taking hits out there where nothing could be done about it. The end of
// the crossing is now derived from her own width, so she jumps out while
// she is still whole on screen.
const TRANS_EDGE_PAD = 12;
const AST_STREAM_MEAN = 110;     // steps between rocks, on average
const AST_STREAM_JIT  = 30;
let transitSecs = 0, guardGone = false, astStreamCd = 0;

// The jump between waves. Nothing used to leave the field, it was simply
// deleted on the frame the next wave began. Three beats replace that:
// the field empties itself, the player jumps out, the player arrives.
// The vortex is the same 75 frame sheet every other ship warps through.
const TRANS_CLEAR = 80;    // rocks and wreckage clear the field
const TRANS_OUT   = 140;   // vortex opens, the ship goes into it
const TRANS_IN    = 130;   // vortex opens again, the ship comes out
let arriveT = 0;           // counts down through the arrival beat
let transFog = 1;          // modifier haze fades with the background

// True while the player is in the middle of a jump and not flying.
function inJump(){
  return arriveT>0 || (waveOver && waveCd>0 && waveCd<=TRANS_OUT);
}
// Scale multiplier for the hull as it goes into or comes out of a vortex.
// Wie dunkel das Feld gerade ist, 0 bis 1. Die Blende selbst und der
// Modifikator-Dunst lesen beide hier, damit die zwei nicht wieder
// auseinanderlaufen koennen.
function jumpDark(){
  if(!(arriveT>0 || (waveOver && waveCd>0 && waveCd<=TRANS_OUT))) return 0;
  const near = (arriveT>0) ? (arriveT/TRANS_IN) : (1-(waveCd/TRANS_OUT));
  return near>0.55 ? (near-0.55)/0.45 : 0;
}

function jumpScale(){
  if(arriveT>0)  return Math.max(0.05, 1-(arriveT/TRANS_IN));
  if(waveOver && waveCd>0 && waveCd<=TRANS_OUT) return Math.max(0.05, waveCd/TRANS_OUT);
  return 1;
}
const REINF_SIZE = 3;

function spawnGuardShip(){
  let a;
  if(guardClass==='destroyer'){
    a = mkAlly('ter_orion');
  } else if(guardClass==='corvette'){
    a = Math.random()<0.5 ? mkAlly('vas_sobek') : mkAlly('ter_deimos');
  } else {
    a = mkAlly('vas_aten') || mkAlly('vas_mentu');
  }
  if(!a) return;
  a.guard = true;
  initSubsystems(a);
  a.hp = Math.round(a.maxHp*guardFrac);
  assignStation(a);
  if(transitSecs>0){
    // Speed is derived from the crossing time, so the clock and what the
    // player sees are the same thing: her position is the progress bar.
    a.transit  = true;
    const gImg = IMGS[a.img];
    const gHalf = gImg ? gImg.width*a.sc*0.5 : 120;
    a.transitEnd = W - gHalf - TRANS_EDGE_PAD;
    a.transitV = (a.transitEnd - a.x) / (transitSecs*TICK_HZ);
  }
  allies.push(a);
  guardSpawned = true;
}

function spawnVasReinforcement(){
  const pool = ROLES.ally_vas_fighters;
  if(!pool || !pool.length) return;
  const spr = pool[(Math.random()*pool.length)|0];
  const mid = HUD_H+80 + Math.random()*(H-HUD_H-160);
  for(let i=0;i<REINF_SIZE;i++){
    const y = Math.max(HUD_H+26, Math.min(H-26, mid + (i-1)*WING_SPACING));
    const a = mkAllySmall('fighter', 'vasudan', spr, y);
    a.warp = 70 + i*WING_STAGGER; a.warpMax = a.warp;
    allies.push(a);
  }
}

function updateVasudan(){
  if(guardWanted && !guardSpawned && spawnT > 40) spawnGuardShip();

  // The field was fought over before the player got here. Wrecks of the
  // faction he is about to meet, drifting in from the right.
  // No fixed allotment: while the escort is under way the belt keeps
  // feeding rocks at an irregular interval, so there is never a last one
  // to count towards.
  if(transitSecs>0 && !waveOver && guardSpawned && !guardGone){
    if(--astStreamCd<=0){
      astStreamCd = AST_STREAM_MEAN + ((Math.random()*2-1)*AST_STREAM_JIT)|0;
      const _a = mkEnemy('ast', null, HUD_H+30+Math.random()*(H-HUD_H-60));
      if(_a){ _a.side='enemy'; _a.warpMax=1; enemies.push(_a); }
    }
  }

  if(waveMod==='astfield' && spawnT===30) seedStaticField(10);

  if(waveMod==='wreckfield' && spawnT===30){
    const pool = (currentFaction==='shivan')
      ? ROLES.shivan_fighters.concat(ROLES.shivan_bombers)
      : ROLES.ntf_fighters.concat(ROLES.ntf_bombers);
    seedWreckField(14, pool, 0.30);
  }

  // The storm comes in bursts. Between them the sensors are fine, which
  // is what makes the blackout worth reacting to rather than enduring.
  if(waveMod==='emp'){
    if(empOut>0){ empOut--; }
    else if(empWarn>0){
      // Der Sturm kuendigt sich an: 1.5 s bernsteinfarbene Entladungen im
      // Dunst. Ohne sie war der Ausfall reines Pech.
      if(--empWarn<=0){
        empOut = 300; empNext = 1200+((Math.random()*600)|0)-EMP_WARN;
        // No radio through the storm. A menu left open would let the call
        // go out anyway, so it is shut on the spot.
        if(callMenu) setCallMenu(false);
      }
    }
    else if(--empNext<=0){ empWarn = EMP_WARN; }
    if(empWarn>0) tickEmpBolts();
    else if(empBolts.length) empBolts.length = 0;
  }
  if(reinfAt && !reinfDone && spawnT > reinfAt){ reinfDone = true; spawnVasReinforcement(); }
}

// ── SUPPORT TICKETS ───────────────────────────────────────
// A ticket is a class ticket, not a named ship: holding a destroyer
// ticket lets you pick any of the destroyers in the menu. Tickets survive
// losing a life and are cleared on game over.
let tickets = {cruiser:0, corvette:0, destroyer:0, colossus:0};
const TICKET_START = {cruiser:1, corvette:0, destroyer:0, colossus:0};
const TICKET_ORDER = ['cruiser','corvette','destroyer','colossus'];
const TICKET_ABBR  = {cruiser:'CR', corvette:'CV', destroyer:'DE', colossus:'CO'};
// Icons are looked up first and the letters are the fallback, the same way
// the lives symbols work. Drop ticket_cruiser.png and friends into the
// icons folder and they appear without a code change.
const TICKET_ICON  = {cruiser:'ticket_cruiser', corvette:'ticket_corvette',
                      destroyer:'ticket_destroyer', colossus:'ticket_colossus',
                      repair:'item_repair'};
// Repair is not a ticket and never appears in the counters, it only needs
// to be drawn and named on the field.
const REPAIR_COL = '#44ff88';

// Share of a hull the player has to have removed personally.
const TICKET_SHARE = {cruiser:0.40, corvette:0.30, destroyer:0.20, boss:0.20};
// Five of ten waves carry no capital ship at all, so bombers cover the gap.
const BOMBER_TICKET_CHANCE = 0.08;

// Hull repair. Calling a support ship and holding still for it works in
// FreeSpace because there are quiet minutes between events. There are none
// here, so repair is a pickup: the cost is flying to it under fire.
const REPAIR_DROP_BOMBER = 0.25;
const REPAIR_DROP_FIGHTER = 0.10;
const REPAIR_PCT = 0.20;      // share of maximum hull restored

// Extra lives. Raised once the grace window came out and a single wave
// could take a life in seconds. Measured across the eleven blueprints
// this is one spare roughly every three waves, against one every five
// and a half before.
const LIFE_DROP_BOMBER = 0.05;
const LIFE_DROP_FIGHTER = 0.016;
const LIVES_MAX = 20;

let ITEMS = [];
const ITEM_LIFE = 20*100;      // twenty seconds before it is gone
const ITEM_DRIFT = -0.45;
const ITEM_R = 15;             // pickup radius on top of the ship's own size
// The magnet. Within MAGNET_R of the ship a pickup is caught and from then
// on flies to it, gaining MAGNET_PULL per step up to MAGNET_MAX - faster
// than any hull flies, so a caught pickup always arrives.
const MAGNET_R    = 120;
const MAGNET_PULL = 0.45;
const MAGNET_MAX  = 7.5;
// Pickups used to drift off the left edge and vanish long before their
// timer ran out, so one dropped on the left was often unreachable through
// no fault of the player. They now bounce inside the field and disappear
// on the timer alone.
const ITEM_MARGIN = 20;

function spawnTicket(x, y, kind){
  ITEMS.push({x:x, y:y, kind:kind, life:ITEM_LIFE, ml:ITEM_LIFE,
              vy:(Math.random()-0.5)*0.35});
}

// Called the moment an enemy dies, from both kill paths.
function maybeDropTicket(e){
  if(!e) return;
  if(e.type==='fighter'){
    if(Math.random() < REPAIR_DROP_FIGHTER) spawnTicket(e.x, e.y, 'repair');
    // Independent roll, as it already is for bombers. Chaining it behind
    // the repair roll quietly cost it a tenth of its chance.
    if(Math.random() < LIFE_DROP_FIGHTER) spawnTicket(e.x, e.y, 'life');
    return;
  }
  if(e.type==='bomber'){
    // Independent rolls: a bomber is the best source of repairs and the
    // only source of tickets in the waves without capital ships. The life
    // roll is separate again so it is not crowded out by the others.
    if(Math.random() < REPAIR_DROP_BOMBER) spawnTicket(e.x, e.y, 'repair');
    if(Math.random() < BOMBER_TICKET_CHANCE) spawnTicket(e.x, e.y, 'cruiser');
    if(Math.random() < LIFE_DROP_BOMBER) spawnTicket(e.x, e.y, 'life');
    return;
  }
  const share = TICKET_SHARE[e.type];
  if(share == null) return;
  if((e.pDmg||0) < e.maxHp*share) return;
  // The boss pays in Colossus, which is why her ticket always arrives one
  // campaign before she is needed.
  // She is the heaviest thing reachable outside a boss wave and pays
  // accordingly.
  const kind = e.iceni ? 'destroyer' : (e.type==='boss' ? 'colossus' : e.type);
  spawnTicket(e.x, e.y, kind);
}

function updateItems(){
  const pr = (IMGS[player.ship] ? IMGS[player.ship].height*playerSc()*0.5 : 16) + ITEM_R;
  for(let i=ITEMS.length-1;i>=0;i--){
    const it=ITEMS[i];
    if(it.vx==null) it.vx=ITEM_DRIFT;
    if(GS==='playing' && player.hp>0){
      const mdx=player.x-it.x, mdy=player.y-it.y, md=Math.hypot(mdx,mdy);
      if(md < MAGNET_R) it.caught = true;
      if(it.caught && md > 0){
        it.vx += mdx/md*MAGNET_PULL; it.vy += mdy/md*MAGNET_PULL;
        const ms=Math.hypot(it.vx, it.vy);
        if(ms > MAGNET_MAX){ it.vx=it.vx/ms*MAGNET_MAX; it.vy=it.vy/ms*MAGNET_MAX; }
      }
    }
    it.x += it.vx; it.y += it.vy;
    if(it.x<ITEM_MARGIN){ it.x=ITEM_MARGIN; it.vx=Math.abs(it.vx); }
    else if(it.x>W-ITEM_MARGIN){ it.x=W-ITEM_MARGIN; it.vx=-Math.abs(it.vx); }
    if(it.y<HUD_H+16){ it.y=HUD_H+16; it.vy=Math.abs(it.vy); }
    else if(it.y>H-16){ it.y=H-16; it.vy=-Math.abs(it.vy); }
    if(--it.life<=0){ ITEMS.splice(i,1); continue; }
    if(GS==='playing' && player.hp>0){
      const dx=it.x-player.x, dy=it.y-player.y;
      if(dx*dx+dy*dy < pr*pr){
        if(it.kind==='repair'){
          player.hp = Math.min(player.maxHp, player.hp + player.maxHp*REPAIR_PCT);
        } else if(it.kind==='life'){
          lives = Math.min(LIVES_MAX, lives+1);
        } else {
          tickets[it.kind] = (tickets[it.kind]||0) + 1;
          STATS.ticketsEarned++;
          ticketFlash = 90; ticketFlashKind = it.kind;
        }
        // Say what was collected, in words. A row of two letter
        // abbreviations is not enough to tell CV from DE at a glance.
        TICKET_MSGS.push({x:it.x, y:it.y, kind:it.kind, life:150, ml:150,
                          rep:(it.kind==='repair'||it.kind==='life')});
        ITEMS.splice(i,1);
      }
    }
  }
}
let ticketFlash = 0, ticketFlashKind = null;
let TICKET_MSGS = [];
const TICKET_NAME = {cruiser:'CRUISER TICKET', corvette:'CORVETTE TICKET',
                     destroyer:'DESTROYER TICKET', colossus:'COLOSSUS TICKET',
                     repair:'HULL REPAIR', life:'EXTRA LIFE'};

function drawTicketMsgs(){
  for(let i=TICKET_MSGS.length-1;i>=0;i--){
    const m=TICKET_MSGS[i];
    if(--m.life<=0){ TICKET_MSGS.splice(i,1); continue; }
    const t=m.life/m.ml;
    ctx.save();
    ctx.globalAlpha=Math.min(1, t*2.2);
    ctx.font='bold 11px Courier New';
    ctx.textAlign='center'; ctx.textBaseline='middle';
    const y=m.y-(1-t)*34;
    ctx.fillStyle='#001018';
    const w=ctx.measureText('+1 '+(TICKET_NAME[m.kind]||'')).width;
    ctx.fillRect((m.x-w/2-6)|0,(y-9)|0,(w+12)|0,18);
    ctx.fillStyle=m.rep?REPAIR_COL:'#8fe4ff';
    ctx.fillText((m.kind==='repair'?'+':'+1 ')+(TICKET_NAME[m.kind]||''), m.x, y);
    ctx.restore();
  }
  ctx.textAlign='left'; ctx.textBaseline='top';
}


// Traces the sprite's own alpha edge instead of drawing a box around it.
// The shadow follows the silhouette, so repeated draws build a rim that
// sits on the visible outline and leaves the transparent area alone.
function drawGlowIcon(ico, x, y, w, h, col, strength){
  ctx.save();
  ctx.shadowColor = col;
  ctx.shadowOffsetX = 0; ctx.shadowOffsetY = 0;
  for(let p=0;p<3;p++){
    ctx.shadowBlur = ecoBlur((3 + p*3) * strength);
    ctx.drawImage(ico, x, y, w, h);
  }
  ctx.shadowBlur = 0;
  ctx.drawImage(ico, x, y, w, h);      // clean copy on top
  ctx.restore();
}

function drawItems(){
  for(const it of ITEMS){
    const t=it.life/it.ml;
    // Blink out over the last three seconds so an expiring ticket is
    // obviously about to be lost.
    if(it.life<300 && fc%20<8) continue;
    const pulse=0.6+0.4*Math.sin(fc*0.12);
    ctx.save();
    ctx.translate(it.x|0, it.y|0);
    ctx.globalCompositeOperation='lighter';
    try{
      const rep=(it.kind==='repair');
      const g=ctx.createRadialGradient(0,0,0,0,0,20);
      g.addColorStop(0,(rep?'rgba(70,255,140,':'rgba(120,235,255,')+(0.55*pulse).toFixed(2)+')');
      g.addColorStop(1,rep?'rgba(70,255,140,0)':'rgba(120,235,255,0)');
      ctx.fillStyle=g; ctx.beginPath(); ctx.arc(0,0,20,0,Math.PI*2); ctx.fill();
    }catch(ex){}
    ctx.restore();
    ctx.save();
    ctx.translate(it.x|0, it.y|0);
    // A life pickup wears the same symbol as the lives counter.
    let icoKey=TICKET_ICON[it.kind];
    if(it.kind==='life'){
      icoKey = isBomberHull(player.ship)
               ? 'bomberlives' : 'fighterlives';
    }
    const ico=ICONS[icoKey];
    if(ico){
      const hh=18, ww=Math.max(1,Math.round(ico.width*(hh/ico.height)));
      drawGlowIcon(ico, -ww/2, -hh/2, ww, hh, REPAIR_COL, 0.55+0.75*pulse);
    } else if(it.kind==='life'){
      ctx.strokeStyle='rgba(90,255,160,'+(0.75+0.25*pulse).toFixed(2)+')';
      ctx.lineWidth=1.6;
      ctx.strokeRect(-10,-8,20,16);
      ctx.fillStyle=REPAIR_COL;
      ctx.font='bold 10px Courier New';
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText('1UP',0,1);
    } else if(it.kind==='repair'){
      // A cross rather than letters: it has to be told apart from the
      // tickets at a glance while something is shooting at you.
      ctx.strokeStyle='rgba(90,255,160,'+(0.75+0.25*pulse).toFixed(2)+')';
      ctx.lineWidth=1.6;
      ctx.strokeRect(-10,-10,20,20);
      ctx.fillStyle=REPAIR_COL;
      ctx.fillRect(-6,-2,12,4);
      ctx.fillRect(-2,-6,4,12);
    } else {
      ctx.strokeStyle='rgba(150,235,255,'+(0.7+0.3*pulse).toFixed(2)+')';
      ctx.lineWidth=1.6;
      ctx.strokeRect(-11,-8,22,16);
      ctx.fillStyle='#bfefff';
      ctx.font='bold 10px Courier New';
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(TICKET_ABBR[it.kind]||'??',0,1);
    }
    ctx.restore();
    ctx.textAlign='left'; ctx.textBaseline='top';
  }
}

// ── ESCORTS ───────────────────────────────────────────────
// At most one escort is ever deployed. The next call only
// unlocks once the current ship has been destroyed.

// One entry per actual ship class. Picking at random from a pool meant you
// never knew what you were calling, and the Hecate could never turn up at
// all because the escort pool only held the Orion.
const ALLY_DEFS = {
  ter_fenris:     {cls:'cruiser',   fac:'terran',  spr:'crfenris',     label:'GTC Fenris'},
  ter_leviathan:  {cls:'cruiser',   fac:'terran',  spr:'crleviathan',  label:'GTC Leviathan'},
  ter_aeolus:     {cls:'cruiser',   fac:'terran',  spr:'craeolus',     label:'GTC Aeolus'},
  ter_deimos:     {cls:'corvette',  fac:'terran',  spr:'codeimos',     label:'GTCv Deimos'},
  ter_orion:      {cls:'destroyer', fac:'terran',  spr:'deorionright', label:'GTD Orion'},
  ter_hecate:     {cls:'destroyer', fac:'terran',  spr:'dehecate',     label:'GTD Hecate'},
  vas_aten:       {cls:'cruiser',   fac:'vasudan', spr:'craten',       label:'PVC Aten'},
  vas_mentu:      {cls:'cruiser',   fac:'vasudan', spr:'crmentu',      label:'PVC Mentu'},
  vas_sobek:      {cls:'corvette',  fac:'vasudan', spr:'cosobek',      label:'PVCv Sobek'},
  vas_typhon:     {cls:'destroyer', fac:'vasudan', spr:'detyphon',     label:'PVD Typhon'},
  vas_hatshepsut: {cls:'destroyer', fac:'vasudan', spr:'dehatshepsut', label:'PVD Hatshepsut'},
  // Kept as class destroyer on purpose: hull, weapons, targeting and
  // explosions all key off the class, and she needs none of that changed.
  // Only her placement and her deadline are special.
  // Joint Terran and Vasudan project, so she belongs to neither column.
  colossus:       {cls:'destroyer', fac:'gtva',    spr:'sdcolossus',   label:'GTVA Colossus',
                   ticket:'colossus', colossus:true},
  // Mission use only, never on the call menu (not in ALLY_ORDER): an NTF
  // Deimos coming over, still in NTF markings.
  ntf_deimos:     {cls:'corvette',  fac:'terran',  spr:'ntfcodeimos',  label:'NTF Deimos'}
};
const COLOSSUS_TIME = 60;     // seconds on station before she jumps out
const COLOSSUS_HULL_MULT = 3; // she is not meant to be destructible in a minute
// Terran down the left column, Vasudan down the right.
const ALLY_ORDER = ['ter_fenris','ter_leviathan','ter_aeolus','ter_deimos','ter_orion','ter_hecate',
                    'vas_aten','vas_mentu','vas_sobek','vas_typhon','vas_hatshepsut'];
const ALLY_KEYS  = ['1','2','3','4','5','6','Q','W','E','R','T'];
const ALLY_TER_N = 6;      // how many entries fill the left column
// The Colossus sits on her own full width row below the two columns.
const ALLY_SPECIAL = 'colossus';
const ALLY_SPECIAL_KEY = 'C';
// Which support factions answer in the current cycle. The Hammer of Light
// cycle is fought on the Vasudan side, so no Terran fleet is on call. A
// later cycle switches its own factions back on by setting these.
const ALLY_FAC_ON = {terran:false, vasudan:true, gtva:true};
function allyFacOn(fac){ return ALLY_FAC_ON[fac] !== false; }
// One column per active faction, in ALLY_ORDER order. With a single
// faction on call the menu is one column wide instead of leaving a gap.
function callCols(){
  const cols=[];
  for(const fac of ['terran','vasudan']){
    if(!allyFacOn(fac)) continue;
    const col=[];
    for(let i=0;i<ALLY_ORDER.length;i++){
      const d=ALLY_DEFS[ALLY_ORDER[i]];
      if(d && d.fac===fac) col.push({id:ALLY_ORDER[i], d:d, key:ALLY_KEYS[i]});
    }
    if(col.length) cols.push(col);
  }
  return cols;
}

// Which ticket a menu entry spends.
function allyTicket(id){
  const d=ALLY_DEFS[id]; if(!d) return null;
  return d.ticket || d.cls;
}
// Three of a class make one of the next. Over a long run the cruiser
// tickets pile up far faster than they can be spent, and this gives the
// surplus somewhere to go instead of sitting in the counter.
const REFINE_COST = 3;
const REFINE_UP = {cruiser:'corvette', corvette:'destroyer', destroyer:'colossus'};
function canRefine(kind){
  return !!REFINE_UP[kind] && (tickets[kind]||0) >= REFINE_COST;
}
function refineTicket(kind){
  if(!canRefine(kind)) return false;
  tickets[kind] -= REFINE_COST;
  const up = REFINE_UP[kind];
  tickets[up] = (tickets[up]||0) + 1;
  ticketFlash = 90; ticketFlashKind = up;
  return true;
}

function allyAffordable(id){
  const k=allyTicket(id);
  return !!k && (tickets[k]||0) > 0;
}

let allyCd = 0;            // lockout after losing an escort
let callMenu = false;      // is the call menu open?

// Only capital escorts count towards the one at a time rule. Fighter and
// bomber wings launched by a destroyer are not a called escort.
function allyReady(){
  if(GS!=='playing' || allyCd>0) return false;
  // The guarded cruiser is not a called escort. Blocking the call would
  // stop the player defending the very ship the wave is about.
  for(const a of allies) if(!a.small && !a.guard) return false;
  return true;
}
// Anything at all to spend?
function anyTicket(){
  for(const k of TICKET_ORDER) if(tickets[k]>0) return true;
  return false;
}

function mkAlly(id){
  const d = ALLY_DEFS[id]; if(!d) return null;
  const spr = d.spr; if(!spr) return null;
  const img = IMGS[spr];
  const geo = {
    cruiser:  {w:100, tx:120, warp:190, mar:60},
    corvette: {w:130, tx:145, warp:220, mar:60},
    destroyer:{w:380, tx:210, warp:260, mar:80}
  }[d.cls];
  // War dieselbe fest verdrahtete Tabelle wie in mkEnemy. Zwei Kopien
  // derselben Kurve laufen auseinander, siehe Handoff Abschnitt 11.
  const sc = hullScale(spr, 0.8);
  let y = HUD_H + geo.mar + Math.random()*(H-HUD_H-geo.mar*2);
  // The Colossus spans the whole field and hugs the top edge, so neither
  // the random height nor the class scale apply to her.
  let cx = geo.tx, colSc = sc;
  if(d.colossus && img){
    // War W/img.width, also volle Feldbreite von 800 Bildpunkten. Bei
    // einer eingebetteten Breite von 1152 sind das 2,08fache
    // Hochskalierung - der Colossus war damit das weichste Objekt im
    // Spiel. 556 ist schaerfer UND kleiner.
    colSc = hullWidth('sdcolossus')/img.width;
    y = HUD_H + img.height*colSc*0.5 + 6;
    cx = W/2;
  }
  const a = {
    type:d.cls, side:'ally', id:id, label:d.label,
    img:spr, faction:d.fac,
    x:cx, y:y, warpX:cx, warpY:y, targetX:cx,
    hp:capHull(HULL[d.cls]*(d.colossus?COLOSSUS_HULL_MULT:1)),
    maxHp:capHull(HULL[d.cls]*(d.colossus?COLOSSUS_HULL_MULT:1)),
    vy:d.colossus?0:(Math.random()<.5?1:-1)*(0.2+Math.random()*0.25),
    minY:d.colossus?y:HUD_H+geo.mar, maxY:d.colossus?y:H-geo.mar,
    fT:60, fR:70, pat:0, dead:false, sc:colSc, ang:0,
    warp:geo.warp, warpMax:geo.warp,
    colossus:!!d.colossus,
    lifeT:d.colossus?COLOSSUS_TIME*TICK_HZ:0,
    flip: needsFlip(spr, false)     // escorts face right
  };
  initBeams(a);
  initWeapons(a);
  return a;
}

// Escorts that are fighters or bombers live in the same list as the
// capital ships, so beams, bolts and the draw order pick them up without
// changes. The small flag keeps them out of the escort bookkeeping.
const ALLY_WING_SIZE = 3;
const ALLY_WING_MAX  = 2;      // wings a destroyer keeps in the air at once
const ALLY_WING_CD   = 900;    // steps between launches

// Enemy answer to a called capital ship. Not endless: a fixed number of
// bomber wings per wave, and only while fewer than two are already up.
// Cut back twice over. Three wings of three was nine extra bombers drawn
// by a single support call, and a cruiser cannot survive that however the
// focus limit spreads them.
const CAP_BOMBER_WAVES = 2;
const CAP_BOMBER_SIZE  = 2;
const CAP_BOMBER_DELAY = 700;
let capBomberLeft = CAP_BOMBER_WAVES;
let capBomberCd = 0;

function countAllySmall(){
  let n=0; for(const a of allies) if(a.small && !a.dead) n++; return n;
}
function countEnemyBombers(){
  let n=0; for(const e of enemies) if(e.type==='bomber' && !e.dead) n++; return n;
}
function hasAllyCapital(){
  for(const a of allies) if(!a.small && !a.dead && !a.warpOut) return true;
  return false;
}

// One escort fighter or bomber. Same flight model as the enemy small
// craft, only the side differs.
function mkAllySmall(kind, fac, spr, y){
  const img = IMGS[spr];
  const sc = img ? Math.min(0.55, (kind==='bomber'?65:60)/img.width) : 0.5;
  const bomber = kind==='bomber';
  const a = {
    type:kind, side:'ally', small:true, img:spr, faction:fac,
    x:-10, y:y, warpX:-10, warpY:y,
    hp:HULL[kind], maxHp:HULL[kind],
    sh:SHIELD[kind].max, maxSh:SHIELD[kind].max, shRe:SHIELD[kind].re,
    shDelay:0, shHit:0, minY:HUD_H+22, maxY:H-22,
    vx:0, vy:0, ang:0, head:0,
    spd: bomber?EBOMBER_SPD:EFIGHTER_SPD,
    turn: bomber?EBOMBER_TURN:EFIGHTER_TURN,
    role:'stand', passT:0, orbit:(Math.random()<0.5?-1:1),
    prefD: bomber?(200+Math.random()*140):(90+Math.random()*130),
    fT:(40+Math.random()*40)|0, fR:(85+Math.random()*60)|0,
    dead:false, sc:sc, flip:false, warp:90, warpMax:90
  };
  const p = poseFor(a.head, a.flip); a.ang=p.ang; a.flip=p.flip;
  initWeapons(a);
  initSecAmmo(a);
  return a;
}

// A destroyer launches fighters to cover the player and bombers to go
// after enemy capital ships.
function launchAllyWing(host){
  const vas = host.faction==='vasudan';
  const wantBomber = enemies.some(isLargeShip);
  const pool = wantBomber
    ? ROLES[vas?'ally_vas_bombers':'ally_ter_bombers']
    : ROLES[vas?'ally_vas_fighters':'ally_ter_fighters'];
  if(!pool || !pool.length) return;
  const spr = pool[(Math.random()*pool.length)|0];
  const mid = Math.max(HUD_H+60, Math.min(H-60, host.y));
  for(let i=0;i<ALLY_WING_SIZE;i++){
    const y = Math.max(HUD_H+26, Math.min(H-26, mid + (i-1)*WING_SPACING));
    const a = mkAllySmall(wantBomber?'bomber':'fighter', host.faction, spr, y);
    a.warp = 60 + i*WING_STAGGER; a.warpMax = a.warp;
    allies.push(a);
  }
}

// Enemy bombers sent in answer to a called capital ship.
function sendCapBombers(){
  const type = 'bo_' + FAC_TAG[currentFaction];
  const pool = poolFor(type);
  if(!pool || !pool.length) return;
  const spr = pool[(Math.random()*pool.length)|0];
  const wid = ++wingSeq;
  const mid = HUD_H+60 + Math.random()*(H-HUD_H-120);
  for(let i=0;i<CAP_BOMBER_SIZE;i++){
    spawnQ.push({time: spawnT + 30 + i*WING_STAGGER, type: type, spr: spr, wing: wid,
                 y: Math.max(HUD_H+26, Math.min(H-26, mid + (i-1)*WING_SPACING))});
  }
  spawnQ.sort(function(a,b){ return a.time-b.time; });
}

// The enemy answer to a called capital ship used to be a pure addition:
// the player paid a ticket and got extra bombers for it, while the enemy
// paid nothing for having capital ships. Rather than take the enemy
// reinforcement away, the defender now scrambles as well. Both sides
// escalate, which is also what a fleet would actually do about bombers
// closing on a warship.
const INTERCEPT_SIZE = 3;
const INTERCEPT_DELAY = 90;     // scramble time, so the bombers are seen first

function sendInterceptors(host){
  const vas = host.faction==='vasudan';
  const pool = ROLES[vas?'ally_vas_fighters':'ally_ter_fighters'];
  if(!pool || !pool.length) return;
  const spr = pool[(Math.random()*pool.length)|0];
  const mid = Math.max(HUD_H+60, Math.min(H-60, host.y));
  for(let i=0;i<INTERCEPT_SIZE;i++){
    const y = Math.max(HUD_H+26, Math.min(H-26, mid + (i-1)*WING_SPACING));
    const a = mkAllySmall('fighter', host.faction, spr, y);
    a.warp = INTERCEPT_DELAY + i*WING_STAGGER; a.warpMax = a.warp;
    // Scrambled against bombers, so that is what they go after first.
    a.intercept = true;
    allies.push(a);
  }
}

// A boss with a working radio is never left alone for long. The wing is
// pushed through the ordinary spawn queue, so the wave's own cap on
// simultaneous small craft still applies and the field cannot be flooded.
const BOSS_CALL_GAP = 260;        // pause after the last of them dies
const BOSS_CALL_FI = 4;
const BOSS_CALL_BO = 3;

function liveEnemySmall(){
  let n=0;
  for(const e of enemies) if((e.type==='fighter'||e.type==='bomber') && !e.dead) n++;
  for(const s of spawnQ) if(WING_TYPES[s.type]) n++;   // queued counts as called
  return n;
}

function bossCallWing(boss, type, size){
  const pool = poolFor(type);
  if(!pool || !pool.length) return;
  const spr = pool[(Math.random()*pool.length)|0];
  const wid = ++wingSeq;
  const half = (size-1)*WING_SPACING*0.5;
  const lo = HUD_H+26+half, hi = H-26-half;
  const mid = (lo>=hi) ? (HUD_H+H)/2 : lo + Math.random()*(hi-lo);
  for(let k=0;k<size;k++){
    spawnQ.push({time: spawnT + 20 + k*WING_STAGGER, type: type, spr: spr, wing: wid,
                 y: mid - half + k*WING_SPACING});
  }
  spawnQ.sort(function(a,b){ return a.time-b.time; });
}

function updateBossCalls(){
  for(const e of enemies){
    if(e.type!=='boss' || e.dead || e.warp>0 || e.warpOut>0) continue;
    if(!subOK(e,'communication')) continue;      // the radio room is the way out
    if(e.callCd>0){ e.callCd--; continue; }
    if(liveEnemySmall()>0) continue;             // the last wing is still up
    const sfx = '_' + FAC_TAG[e.faction];
    bossCallWing(e, 'fi'+sfx, BOSS_CALL_FI);
    // Bombers only when there is something worth sending them against.
    if(hasAllyCapital()) bossCallWing(e, 'bo'+sfx, BOSS_CALL_BO);
    e.callCd = BOSS_CALL_GAP;
  }
}

function updateCapResponse(){
  if(capBomberCd>0){ capBomberCd--; return; }
  if(capBomberLeft<=0) return;
  if(!hasAllyCapital()) return;
  if(countEnemyBombers()>=2) return;
  // Somebody has to make the call. With a capital ship on the field it is
  // theirs, and a wrecked radio room ends the answer.
  let anyCap=false, anyRadio=false;
  for(const o of enemies){
    if(!hasSubsystems(o) || o.dead || o.warp>0) continue;
    anyCap=true;
    if(subOK(o,'communication')) anyRadio=true;
  }
  if(anyCap && !anyRadio) return;
  sendCapBombers();
  // Whoever was called is the one that scrambles the screen.
  for(const a of allies){
    if(!a.small && !a.dead && !a.warpOut && subOK(a,'communication')){ sendInterceptors(a); break; }
  }
  capBomberLeft--;
  capBomberCd = CAP_BOMBER_DELAY;
}

function callAlly(id){
  if(!allyReady()) return false;
  // Gated here rather than in the menu: the key handler and any future
  // caller come through this function too.
  const cdef = ALLY_DEFS[id];
  if(!cdef || !allyFacOn(cdef.fac)) return false;
  if(!allyAffordable(id)) return false;
  const a = mkAlly(id);
  if(!a) return false;
  initSubsystems(a);
  tickets[allyTicket(id)]--;
  STATS.escortsCalled++;
  if(!a.colossus) assignStation(a);   // she has one station and it is the top
  allies.push(a);
  setCallMenu(false);
  // The enemy notices. First answer comes after a short delay rather than
  // on the same step, so the escort is at least through its jump in.
  capBomberCd = Math.max(capBomberCd, CAP_BOMBER_DELAY);
  return true;
}

// Escorts fire to the right. Their shots live in the same
// list as the player's, so they hit the same targets.
// Closest worthwhile target for a turret.
// Non-combatants: cargo containers, escape pods (both spawn as type
// container) and freighters. Freighters have no entry in WPN and never fire;
// should one ever get guns, it drops out of this rule on its own.
// Only the player may damage these. Allied weapons never pick them as a
// target and allied fire passes through them.
function playerOnly(o){
  if(!o) return false;
  if(o.type==='container') return true;
  return o.type==='freighter' && !WPN[o.type];
}

function nearestEnemy(x, y){
  let best=null, bd=Infinity;
  for(const o of enemies){
    if(o.dead || o.warp>0 || o.type==='asteroid') continue;
    // Eine unverwundbare Station ist Kulisse: auf sie zu halten sieht aus
    // wie ein Fehler und haelt die Geschuetze von echten Zielen ab.
    if(o.invuln) continue;
    // Fracht, die gescannt oder abgeholt werden soll, ist kein Ziel -
    // sonst raeumen die eigenen Verbuendeten den Auftrag weg.
    if(o.noTarget || playerOnly(o)) continue;
    const d=(o.x-x)**2 + (o.y-y)**2;
    if(d<bd){ bd=d; best=o; }
  }
  return best;
}

function allyFire(a){
  // The flak gun is its own gun on its own clock, not one of the barrels
  // taking a turn, so it fires whether or not the main guns have a target.
  flakFire(a, true);
  if(!subOK(a,'weapons')) return;
  const aScat = subOK(a,'sensors') ? 1 : 4;
  const cfg = WPN[a.type] || WPN.cruiser;
  const pts = entMounts(a,'primary');
  if(!pts || !pts.length || !a.gunT) return;
  for(let i=0;i<pts.length && i<a.gunT.length;i++){
    if(--a.gunT[i] <= 0){
      a.gunT[i] = (rndR(cfg.rate) * corneredMult(a))|0;
      const big = Math.random() < cfg.big;
      const spd = big ? 5.5 : 7.5;
      // Turrets traverse onto a target instead of firing straight ahead.
      // Fighters and bombers keep their fixed forward guns later on.
      const tg = nearestEnemy(pts[i].x, pts[i].y);
      if(!tg) continue;                 // kein Ziel, kein Schuss
      let ang = 0;
      if(tg){
        ang = Math.atan2(tg.y-pts[i].y, tg.x-pts[i].x);
        ang += (Math.random()-0.5)*0.06*aScat;    // slight spread, wide when blind
        ang = Math.max(-1.15, Math.min(1.15, ang)); // never fire backwards
      }
      pBullets.push({x:pts[i].x, y:pts[i].y,
        vx: Math.cos(ang)*spd, vy: Math.sin(ang)*spd,
        w: big?13:11, h: big?13:4,
        dmg: big?34:18, ally:true, fac:a.faction});
    }
  }
}

function updateAllies(){
  if(allyCd>0) allyCd--;
  for(let i=allies.length-1;i>=0;i--){
    const a = allies[i];
    // An ally that is due to go over cannot die first. Enemy fire on
    // allies does not pass through damageEnemy(), so the lock that sits
    // there never reached them.
    if(a.defectLock){
      const dfl = a.maxHp * DISABLE_HULL_FLOOR;
      if(a.hp < dfl) a.hp = dfl;
    }
    if(a.hp<=0 && !a.dead){
      a.dead = true;
      triggerExpl(a.x, a.y, a.type, a.faction==='vasudan' ? 'vasudan' : 'terran', a);
      allies.splice(i,1);
      if(a.guard){ protLost++; guardLost = true; guardGone = true; score = Math.max(0, score-GUARD_PENALTY);
        // The Orff coming through decides whether the Vasudan ace shows up
        // in the wave after this one.
        if(FS1_MODE && wave===1) CAMP.orffOk = false; }
      // Losing a wing member must not lock out the next escort call.
      else if(!a.small) allyCd = 240;   // roughly two seconds of lockout
      continue;
    }
    if(a.warp>0){
      a.warp--;
      if(a.small){ const wp=poseFor(a.head,a.flip); a.ang=wp.ang; a.flip=wp.flip; }
      continue;
    }

    // Once the wave is over the escort jumps out in good order
    // instead of simply vanishing.
    if(waveOver && !a.warpOut){ a.warpOut = a.warpMax; a.warpX = a.x; a.warpY = a.y; }
    if(a.warpOut > 0){
      a.warpOut--;
      if(a.warpOut <= 0){ if(a.guard) guardGone = true; allies.splice(i,1); }
      continue;                       // no firing while jumping out
    }

    if(a.small){
      // Same flight model as the enemy small craft.
      const tg = flySmall(a);
      if(--a.fT<=0) smallFire(a, tg);
      fireSecondaries(a, WPN[a.type]);
      continue;
    }
    // Her deadline runs whatever happens. A ship of that class does not
    // loiter in a skirmish, and left standing she would simply erase the
    // rest of the campaign.
    if(a.colossus && a.lifeT>0 && --a.lifeT<=0 && !a.warpOut){
      a.warpOut=a.warpMax; a.warpX=a.x; a.warpY=a.y;
    }
    if(a.transit && subOK(a,'engines')){
      a.x += a.transitV;
      // transitV is negative on a crossing to the left.
      const _there = (a.transitV >= 0) ? (a.x >= a.transitEnd) : (a.x <= a.transitEnd);
      if(_there && !a.warpOut){
        a.warpOut = a.warpMax; a.warpX = a.x; a.warpY = a.y;
        // She has left, as far as the mission's events are concerned.
        if(a.uid) EV_LEFT[a.uid] = true;
        // The job is done the moment she engages her drive. The belt stops
        // feeding rocks at her while she is on her way out.
        if(a.guard) guardGone = true;
      }
    }
    if(!subOK(a,'engines')) a.vy = 0;       // dead in the water
    a.y += a.vy;
    if(a.y<a.minY || a.y>a.maxY) a.vy *= -1;
    a.y = Math.max(a.minY, Math.min(a.maxY, a.y));
    allyFire(a);
    updateBeams(a);
    // Destroyers put wings into the fight of their own accord.
    if(a.type==='destroyer'){
      if(a.wingCd==null) a.wingCd = 120;
      if(a.wingCd>0) a.wingCd--;
      else if(countAllySmall() < ALLY_WING_MAX*ALLY_WING_SIZE && subOK(a,'communication')){
        launchAllyWing(a); a.wingCd = ALLY_WING_CD;
      }
    }
  }
  updateCapResponse();
  updateBossCalls();
  updateVasudan();
  updateItems();
  if(ticketFlash>0) ticketFlash--;
}

// A capital ship with a deadline. It fights normally until the clock runs
// out, then jumps out and is gone. Letting one go costs score and nothing
// else: tying a life to a timer would punish the player for being pinned
// down by fighters at the wrong moment.
// Losing a capital ship that was almost dead has to hurt more than a few
// asteroids can repair. A cruiser is worth 400 on the kill, so 1000 lost
// is a clear net loss rather than an inconvenience.
const FLEE_PENALTY = {cruiser:1000, corvette:2000, destroyer:4000, boss:8000};
function fleePenalty(e){
  if(e && e.fleeFree) return 0;      // an escape the mission intends
  return (e && FLEE_PENALTY[e.type]) || 1000;
}

// How long a ship keeps station once its guns are gone, before it gives up
// and jumps. Bigger ships are slower to decide and cost more when they go.
// Der Boss stand hier mit 35 Sekunden drin. Damit konnte eine Sathanas
// verschwinden, weil Streufeuer nebenbei ihr Geschuetzleitsystem erwischt
// hatte - aus Sicht des Spielers verschwand sie mit halb vollem Balken,
// und das war keine Entscheidung, sondern ein Unfall. Ein Boss ist der
// Hoehepunkt des Durchgangs und bleibt jetzt, bis er zerstoert ist.
const DISARM_FLEE = {cruiser:12, corvette:18, destroyer:25};
// Weapons gone means the ship has no reason left to stay. The clock only
// starts once, and an existing deadline is never overwritten: a Runner
// wave ship keeps the shorter of the two.
function checkDisarmFlee(e){
  // noFlee is set on the target of a disable job. Fleeing when disarmed is
  // right for a warship that has lost its guns; it is wrong when losing
  // the guns is half of what the player was asked to do.
  if(!e.subs || e.fleeT>0 || e.warpOut>0 || e.disarmed || e.noFlee) return;
  if(subOK(e,'weapons')) return;
  e.disarmed = true;
  if(e.type==='boss'){
    // Ohne Fluchtuhr waere die Entwaffnung eines Bosses unsichtbar: er
    // hoert einfach auf zu schiessen. Die Meldung macht aus einem
    // Nebeneffekt eine sichtbare Leistung.
    SUB_MSGS.push({x:e.x, y:e.y-40, txt:'BOSS DISARMED', life:420, ml:420, ally:false});
    return;
  }
  e.fleeT = (DISARM_FLEE[e.type]||15)*TICK_HZ;
}

function runFlee(e, i){
  checkDisarmFlee(e);
  if(e.warpOut>0){
    e.warpOut--;
    if(e.warpOut<=0){
      score = Math.max(0, score-fleePenalty(e));
      fleeEscaped++;
      if(e.iceni) icenEscapes++;      // she will be back, and heavier
      enemies.splice(i,1);
    }
    return true;                    // no firing while jumping out
  }
  if(e.fleeT>0){
    // With the jump drive gone the clock keeps running and buys nothing.
    if(!subOK(e,'navigation')) return false;
    e.fleeT--;
    if(e.fleeT<=0){
      e.warpOut = e.warpMax || 160;
      e.warpX = e.x; e.warpY = e.y;
    }
  }
  return false;
}

// Every capital ship still counting down. Two can run at once, and one
// notice drawn over another is worse than none.
function fleeingEnemies(){
  const out=[];
  for(const e of enemies) if(e.fleeT>0 && !e.dead && !(e.warp>0)) out.push(e);
  out.sort(function(a,b){ return a.fleeT-b.fleeT; });   // most urgent on top
  return out;
}
function fleeingEnemy(){
  const l=fleeingEnemies();
  return l.length ? l[0] : null;
}

// Safety net: enemies killed by escort beams are not
// are not picked up by the projectile loops.
function reapEnemies(){
  for(let i=enemies.length-1;i>=0;i--){
    const e = enemies[i];
    if(e.hp<=0 && !e.dead){
      e.dead = true; score += e.pts; statKill(e.type);
      maybeDropTicket(e);
      triggerExpl(e.x, e.y, e.type, e.faction||'ntf', e);
      if(e.type==='boss'){ bossAlive=false; bossSlain=true; }
      enemies.splice(i,1);
    }
  }
}

// ── ASTEROID IMPACTS ─────────────────────────────────────────
// A rock is neither friend nor foe, it is terrain in motion. It damages
// whatever it touches on every side and breaks apart doing so, which is
// why it needs no grace window: one impact, one payment, gone.
// The damage is a share of the target's own hull rather than a flat
// figure. That keeps a collision survivable for a fighter, as it is in
// FreeSpace, while a steady stream still wears a capital ship down.
const AST_SC_MIN = 0.35, AST_SC_MAX = 0.65;    // as rolled in mkEnemy
const AST_PCT_MIN = 0.035, AST_PCT_MAX = 0.075;

function astRamDmg(a, maxHp){
  const t = Math.max(0, Math.min(1, (a.sc-AST_SC_MIN)/(AST_SC_MAX-AST_SC_MIN)));
  return Math.max(1, Math.round((maxHp||100)*(AST_PCT_MIN+(AST_PCT_MAX-AST_PCT_MIN)*t)));
}

function astBreaks(a){
  spawnFireball(a.x, a.y, 26*a.sc+14, 26);
  spawnDebris(a.x, a.y, 10, 190,175,150, 120,100,80, false);
}

function updateAsteroidImpacts(){
  for(let i=enemies.length-1;i>=0;i--){
    const a = enemies[i];
    if(a.type!=='asteroid' || a.dead) continue;
    const r = 16*a.sc;
    const probe = {x:a.x, y:a.y, w:r*2, h:r*2, vx:a.vx, vy:a.vy};
    let struck = false;

    if(GS==='playing' && player.hp>0){
      const pb = pBox();
      if(overlap(a.x-r,a.y-r,r*2,r*2,pb[0],pb[1],pb[2],pb[3]) && bulletOnPlayer(probe)){
        const d = astRamDmg(a, player.maxHp);
        if(player.sh>0){
          const abs = Math.min(player.sh, d);
          player.sh -= abs; player.shDelay = 90; player.shHit = SH_FLASH;
          shieldHit(a.x, a.y);
          if(d>abs){ player.hp -= d-abs; hullHit(a.x, a.y); }
        } else { player.hp -= d; hullHit(a.x, a.y); }
        struck = true;
        if(player.hp<=0) playerDie();
      }
    }
    if(!struck) for(const t of allies){
      if(t.dead || t.warp>0 || t.warpOut>0) continue;
      const tb = eBox(t);
      if(overlap(a.x-r,a.y-r,r*2,r*2,tb[0],tb[1],tb[2],tb[3]) && bulletOnHull(t, probe)){
        t.hp -= astRamDmg(a, t.maxHp); hullHit(a.x, a.y);
        struck = true; break;
      }
    }
    if(!struck) for(const t of enemies){
      if(t===a || t.type==='asteroid' || t.dead || t.warp>0) continue;
      const tb = eBox(t);
      if(overlap(a.x-r,a.y-r,r*2,r*2,tb[0],tb[1],tb[2],tb[3]) && bulletOnHull(t, probe)){
        damageEnemy(t, astRamDmg(a, t.maxHp), a.x, a.y, false, 'bolt');
        struck = true; break;
      }
    }
    if(struck){ astBreaks(a); enemies.splice(i,1); }
  }
}

// ── WRECKAGE ─────────────────────────────────────────────────
// Debris is not rock. Every piece is a real cut out of the hull it came
// from, drawn from the parent sprite with a source rectangle, so no new
// artwork is needed and a Shivan wreck still looks Shivan.
// Pieces live in their own list, never in enemies: a wave ends on
// !spawnQ.length && !enemies.length, and wreckage must not hold that up.
// A modifier is a condition laid over an existing archetype, not a new
// wave. Eleven blueprints times five states is what keeps the second
// cycle from being the first one again with bigger numbers.
const MOD_NONE = '';
const MOD_LIST = ['nebula','wreckfield','emp','ambush','astfield'];
const MOD_LABEL = {nebula:'NEBULA', wreckfield:'DEBRIS FIELD',
                   emp:'EMP STORM', ambush:'AMBUSH',
                   astfield:'ASTEROID FIELD'};
const MOD_FIRST_WAVE = 6;      // nothing before this, the player needs a base
const MOD_CHANCE = 0.45;
// Not every cloud is the same cloud. A tint is drawn with the modifier so
// two nebula waves in one run do not look like the same place twice.
const NEB_TINTS = [
  {core:'38,52,78',  edge:'26,38,62',  bank:'74,96,140'},   // blue grey
  {core:'62,40,72',  edge:'44,26,54',  bank:'126,84,146'},  // violet
  {core:'70,52,34',  edge:'50,36,22',  bank:'150,112,66'},  // ochre
  {core:'30,62,58',  edge:'19,44,42',  bank:'70,140,128'},  // green teal
  {core:'74,38,38',  edge:'52,24,24',  bank:'150,76,72'},   // rust
  {core:'44,44,52',  edge:'30,30,38',  bank:'104,104,120'}  // ash
];
let nebTint = NEB_TINTS[0];
let waveMod = MOD_NONE, lastMod = MOD_NONE;
let empOut = 0, empNext = 0;   // blackout left, and ticks to the next one
const EMP_WARN = 150;          // 1.5 s Lichtbogen, bevor die Sensoren gehen
let empWarn = 0;
// Jeder Bogen hat seine eigene Lebensdauer. Vorher haben alle an einer
// gemeinsamen Uhr (fc/6) gehangen und im Gleichtakt gewechselt, was den
// statischen Eindruck gemacht hat.
let empBolts = [];

function rollWaveMod(n){
  if(n < MOD_FIRST_WAVE) return MOD_NONE;
  if(Math.random() >= MOD_CHANCE) return MOD_NONE;
  // Never the same one twice running, or it reads as a permanent rule.
  const pool = MOD_LIST.filter(function(m){ return m!==lastMod; });
  return pool[(Math.random()*pool.length)|0];
}

// An EMP storm no longer happens in clear space: it is a nebula
// phenomenon, so the emp modifier brings the haze with it. Everything
// that used to ask for the nebula by name asks this instead.
function nebulaOn(){ return waveMod==='nebula' || waveMod==='emp'; }

// Sight and lock range. The nebula is the reason this is a function.
function fireRange(){ return nebulaOn() ? 240 : EFIRE_RANGE; }

let debris = [];
const DEBRIS_MAX = 44;
const DEBRIS_HP  = 70;                      // metal, not stone
const DEB_PCT_MIN = 0.025, DEB_PCT_MAX = 0.08;
const DEB_SMALL_PX = 30;                    // below this a piece stops splitting

// Normally small craft arrive at the right edge. Under an ambush a share
// of them tears a hole well inside the field instead, which the
// Reference Bible describes: a subspace hole opens in front of the pilot
// and ships come out of it. The vortex animation already covers it.
function ambushX(){
  if(waveMod==='ambush' && Math.random()<0.40) return W*(0.30+Math.random()*0.28);
  return W-10;
}

// ── SUBSPACE BOMB RAIDS ───────────────────────────────────────
// Vortices open in empty space and ordnance comes out of them with no ship
// attached. The reference material has it that bombs cannot carry a
// subspace drive of their own, only ships can. That rule is dropped here
// on purpose and on the owner's call, and both sides can do it.
let BOMB_PORTALS = [];
let bombRaidLeft = 0, bombRaidCd = 0;
const BOMB_RAID_MAX = 2;            // hoechstens zwei Angriffe je Welle
const BOMB_RAID_FIRST_WAVE = 3;     // die ersten zwei Wellen bleiben sauber
const BOMB_RAID_FIRST = 400;        // fruehester Angriff, in Schritten
const BOMB_RAID_JIT = 500;
const BOMB_RAID_GAP = 700, BOMB_RAID_GAP_JIT = 700;
// Waren 120 Schritte, bei Auswurf nach 60 % also nur 0.72 s Vorlauf - eher
// Blitzlicht als Warnung. 300 bei 65 % ergibt 1.95 s offenes Loch, bevor
// die erste Bombe kommt, und gut eine Sekunde zum Schliessen danach.
const PORTAL_LIFE = 300;
const PORTAL_BOMBS = 2;             // je Loch
const PORTAL_MIN = 2, PORTAL_MAX = 3;
const PORTAL_X_MIN = 0.55, PORTAL_X_MAX = 0.75;
const PORTAL_STAGGER = 22;          // Versatz zwischen zwei Loechern

function launchBombRaid(){
  const holes = PORTAL_MIN + ((Math.random()*(PORTAL_MAX-PORTAL_MIN+1))|0);
  for(let i=0;i<holes;i++){
    BOMB_PORTALS.push({
      x: W*(PORTAL_X_MIN+Math.random()*(PORTAL_X_MAX-PORTAL_X_MIN)),
      y: HUD_H+50+Math.random()*(H-HUD_H-100),
      // Versetzt, damit die Salve rollt statt als eine Wand anzukommen,
      // die man entweder ganz raeumt oder gar nicht.
      t: -i*PORTAL_STAGGER, max: PORTAL_LIFE, fired:false
    });
  }
  bombRaidLeft--;
  bombRaidCd = BOMB_RAID_GAP + ((Math.random()*BOMB_RAID_GAP_JIT)|0);
}

// Gleiche Werte wie eine abgefeuerte Bombe: 26 Schaden, 1 Trefferpunkt,
// also mit einem Schuss zu raeumen, und langsam genug zum Ausweichen.
function portalBomb(x, y, ang){
  eBullets.push({
    x:x, y:y,
    vx:Math.cos(ang)*1.7, vy:Math.sin(ang)*1.7,
    w:15, h:15, big:false, faction:currentFaction,
    kind:'bomb', dmg:26, hom:true, turn:0.013, spd:1.7,
    life:560, hp:1
  });
}

function updateBombPortals(){
  // Kein Angriff waehrend des Uebergangs und nicht im Raeumtakt: eine
  // uebrige Bombe wuerde dem Spieler durch den Sprung folgen.
  if(bombRaidLeft>0 && !waveOver && !inJump()){
    if(--bombRaidCd<=0) launchBombRaid();
  }
  for(let i=BOMB_PORTALS.length-1;i>=0;i--){
    const p=BOMB_PORTALS[i];
    p.t++;
    if(p.t<0) continue;
    // Die Last kommt durch, wenn das Loch am weitesten offen ist, nicht
    // waehrend es sich noch oeffnet.
    if(!p.fired && p.t>=p.max*0.65){
      p.fired=true;
      for(let b=0;b<PORTAL_BOMBS;b++){
        const ang = Math.atan2(player.y-p.y, player.x-p.x)
                  + (b-(PORTAL_BOMBS-1)/2)*0.22;
        portalBomb(p.x, p.y, ang);
      }
    }
    if(p.t>=p.max) BOMB_PORTALS.splice(i,1);
  }
}

// Dasselbe Frame-Blatt und dieselbe Auf/Halte/Zu-Kurve wie beim Wirbel
// eines Schiffs, auf etwa halber Groesse: was durchkommt ist Munition,
// kein Rumpf.
function drawBombPortals(){
  if(!BOMB_PORTALS.length) return;
  if(!WARP_IMG || !WARP_IMG.complete || !WARP_IMG.naturalWidth) return;
  for(const p of BOMB_PORTALS){
    if(p.t<0) continue;
    const el=p.t, mW=p.max, p1=mW*0.40, p2=mW*0.60;
    let wS, wA;
    if(el<p1){ const t1=el/p1; wS=0.05+0.95*t1; wA=t1; }
    else if(el<p2){ wS=1.0; wA=1.0; }
    else { const t3=(el-p2)/(mW-p2); wS=1.0-t3*0.85; wA=Math.max(0,1.0-t3); }
    let wF=Math.floor(el/mW*WARP_FRAMES);
    if(wF<0) wF=0; if(wF>WARP_FRAMES-1) wF=WARP_FRAMES-1;
    const WS=70;
    ctx.save();
    ctx.globalAlpha=wA;
    ctx.translate(p.x|0,p.y|0);
    ctx.scale(wS,wS);
    ctx.drawImage(WARP_IMG,
      (wF%WARP_COLS)*WARP_CELL, ((wF/WARP_COLS)|0)*WARP_CELL,
      WARP_CELL, WARP_CELL, -WS/2, -WS/2, WS, WS);
    ctx.restore();
    ctx.globalAlpha=1;
  }
}
