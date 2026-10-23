# FS3 — Ausgelagerte Einzelheiten

Aus `CLAUDE.md` herausgenommen, damit diese nicht bei jeder Sitzung mitgelesen
wird. **Nichts davon ist gestrichen.** Nur bei Bedarf lesen (gezielt suchen).

## A. Prüfstufen im Detail

### `endsim` — kann eine Mission überhaupt enden?

Bei 100 Missionen ist von Hand nicht mehr zu überblicken, ob eine Mission auf
**jedem** Weg ein Ende hat. F13 war genau das: in M68 saß eine Verlustschranke
auf allen drei Ereignissen, die den Nachschub abstellen, und die Mission hatte
überhaupt kein Ende mehr.

`endsim` liest `SCRIPT_WAVES` als Daten und braucht **keinen Browser** — 80
Missionen in einer Sekunde. Es prüft die drei Fälle, in denen die **Daten**
einer Mission das Ende zunageln:

1. Ein Ereignis, das die Welle offenhält (`einwarpen`, `seite`), wartet auf
   eine Kennung, die in keiner Einheit der Mission steht. `evPending()` lässt
   so ein Ereignis nur los, wenn die Einheit **da war** und weg ist — eine
   Einheit, die es nie gab, war nie da. **Ein Tippfehler in einer Kennung
   reicht für eine Mission ohne Ende.**
2. Nachschub angeschaltet und nie abgeschaltet. Der Nachschub ist kein
   Ereignis, er hängt an `evReinf`, also wird `liveThreatCount()` nie null.
3. Eine Uhr gestartet und nie gestoppt. `missionTimerLeft()` gibt nach Ablauf
   **0** zurück, und das Wellenende verlangt kleiner null — eine abgelaufene
   Uhr hält die Welle genauso wie eine laufende.

Dazu eine Prüfung am Quelltext: in `EV_LOST_GUARDS` darf **keine** Wirkung
stehen, die die Welle freigibt. Das ist die F13-Zusicherung.

**Alle Listen liest `endsim` aus dem Code**, nicht aus einer eigenen Kopie:
welche Auslöser auf eine Kennung gehen (die Fälle in `evTrig`, die `byId()`
oder `evSeen()` fragen), was die Welle offenhält (aus `evPending()`), was den
Nachschub abschaltet und was die Uhr stoppt (die Fälle in `evFire`, in deren
Rumpf `evReinf = false` beziehungsweise `missionTimer = {end:0` steht). Die
erste Fassung hatte diese Listen von Hand geschrieben, dabei `ende`
übersehen — das `evReinf = false` setzt wie `abzug` — und meldete M35, M45
und M50 als endlos, obwohl alle drei auf `ende` enden. **Eine von Hand
geschriebene Liste veraltet.**

### `warpsim`: Umfang, Tempo und derselbe Würfel

- **Umfang:** stand fest auf `1-60`, während das Spiel 80 geschriebene
  Missionen hatte — 20 davon wurden nie geprüft, ohne dass es auffiel. Die
  letzte Mission wird jetzt aus `SCRIPT_WAVES` gelesen.
- **Tempo:** die Missionen sind voneinander unabhängig und laufen zu mehreren
  gleichzeitig (`WARPSIM_JOBS`, Standard 6, begrenzt auf die Zahl der Kerne).
- **Derselbe Würfel:** `warpsim` war nicht wiederholbar. Auf v232, Missionen
  1–8, meldeten zwei Läufe 4, 7 und 7 Befunde und verschiedene Schiffe —
  seriell gegen seriell genauso wie seriell gegen parallel. Flugbahnen, die
  Streuung beim Einsprung und die Größe einer Nachschubstaffel kommen aus
  `Math.random()`, also sah jeder Lauf eine andere Schlacht, und „all clean"
  hieß „diesmal sauber". **Das ist auch die Erklärung dafür, dass zwischen
  v232 und v233 eine Familie von 48 Befunden verschwand, ohne dass etwas
  angefasst wurde.** Der Würfel wird jetzt je Mission festgenagelt; drei
  Läufe (zweimal parallel, einmal seriell) kommen byteweise gleich heraus.
  Ein Nachteil, der benannt sein muss: **ein Startwert sieht je Mission
  einen** Flugverlauf, nicht alle. Für ein Tor ist Wiederholbarkeit richtig;
  `WARPSIM_SEED=n` sieht absichtlich einen anderen.

- **Zeichnen nur beim Sprung (v250):** ein gezeichnetes Bild kostet in der
  Cloud rund 40 ms (keine Grafikkarte), die Spiellogik 0,2 ms. `warpsim`
  zeichnete jeden der bis zu 40000 Schritte — eine halbe Stunde je Mission.
  Jetzt zeichnet es nur, solange ein Schiff springt oder ein Wirbel offen
  ist, und 40 Schritte danach: Mission 4 in 40 s statt über 30 min.
  Gegenprobe: `WARPSIM_DRAW=all` zeichnet wieder jedes Bild; mit
  `WARPSIM_MAXT=4000` kamen beide Arten auf M4 byteweise gleich heraus.

### Warnung zu `mechsim`

`mechsim.js` enthält eine **von Hand abgeschriebene Kopie** von `tickCapRam`.
Sie meldete „7 von 7 Starthöhen getroffen", während der Rammkreuzer im Spiel
sichtbar danebenflog — die Kopie konnte den Fehler nicht sehen. `ramsim.js`
ersetzt diesen Teil und liest das Original. Der veraltete Rammteil in
`mechsim` sollte bei Gelegenheit raus, damit er kein falsches Vertrauen
stiftet.

### Was Simulationen können und was nicht

Mehrfach hat eine Prüfung etwas bestanden, das im Spiel kaputt war. Immer aus
demselben Grund: **Die Prüfung ließ nur den Teil laufen, der geändert wurde.**

- `ramsim` rief nur `tickCapRam()`. Im Spiel bewegt `tickEnemies()`
  Großkampfschiffe **auch** — und stärker. Der Rammkurs wurde überfahren.
- `shipsim` öffnete das Rearm-Fenster über `toggleRearmMenu()`. Damit prüft
  man das Fenster, nicht den Knopf. Der Knopf war nie angeschlossen.
- `nctest` zählte, dass die Sicherung in **zwei** Trefferschleifen steht. Das
  Spiel wuchs auf vier; die Stufe blieb grün und hätte eine fünfte ungesicherte
  Schleife nie gesehen. Jetzt wird die Sicherung **an jede** Trefferschleife
  gebunden, die es gibt.

**Daraus die Regel:** Eine neue oder geänderte Prüfung immer **gegen die
kaputte Fassung stellen**. Fällt sie dort nicht durch, prüft sie das Falsche.
Praktisch: die Logikdatei in den Arbeitsordner kopieren, die Sicherung von
Hand herausnehmen, Prüfung laufen lassen — sie muss rot werden.

Wo eine Funktion zu verflochten ist, um sie laufen zu lassen (`tickEnemies`,
`flySmall`, `drawTitle`), wird **am Quelltext geprüft** — etwa, dass eine
Absicherung an der richtigen Stelle steht. Schwächer als ein Verhaltenstest,
aber besser als nichts.

---


## B. Missionssprache — was seit v240 dazukam

Geschriebene Missionen stehen als Daten in `SCRIPT_WAVES` (`30_waves.js`),
mit Einheiten (`u`) und Ereignissen (`ev`). `swtest` prüft sie gegen die
bekannten Auslöser und Wirkungen und nennt beide Listen am Ende seiner
Ausgabe.

**Strang (seit v240):** `era:'fs1'` und `orig:N` (Nummer des Originals in
der FS1-Kampagne) machen eine Mission zur FS1-Mission: FS1-Regeln,
FS1-Waffen nach ihren Freischaltzeitpunkten (F21), die Staffeln ohne
Schleuse. Ohne `era` ist eine Mission FS2. Dazu seit v240: Auslöser `da`
(Einheit ist im Feld oder war es; mit `d:30` „spätestens 30 s nach ihrer
Ankunft"), `anzahlUnter` mit mehreren Kennungen (`E1+E2`), `label` (Name
eines Schiffs), `warpIn` (ein Schützling springt ein), `home` (Trägerschiff).

Seit v249 (FS1 M4 bis M6): Auslöser `beschossen` (Schiff hat einen Treffer
abbekommen), Wirkung `zielteil` (Teilerfolg, gelbe Karte). Einheiten:
`escHit` (fährt erst los, wenn beschossen; `escDelay` = spätestens dann),
`subs` (Transporter mit Subsystemen zum Lahmlegen). Verbündetes Feuer geht
durch Kaperziele hindurch, wie durch Fracht.

Seit v250: `subs:'engines+weapons'` lässt nur die genannten Subsysteme
stehen (F28). `spread:1` an einer Asteroideneinheit verteilt die Brocken über
die ganze Kamerasicht statt nur den Missionsbereich (F32). Jede FS1-Mission
setzt mit `ship:` den Rumpf von Alpha 1 aus der Originaldatei (F27).

Seit v253 (FS1 M7 bis M13): Einheiten `ride:'F1', slot:n` (Fracht sitzt
von Anfang an auf Andockstelle n eines Frachters, fährt, springt und stirbt
mit ihm), `shock` (geht mit schadender Schockwelle hoch, `CARGO_SHOCK`),
`mark:'disable'|'destroy'|'protect'` (pulsierende Klammern, Wort darunter),
`subsDown` (Subsysteme schon zerstört), `spare` (Begleiter schonen sie, bis
jemand auf sie schießt), `fac` auch an Fracht und Geschützen. Kaperziele
(`capture`) fliehen nicht mehr, wenn ihre Waffen fallen. Mission: `pri`
(Primärwaffe in Bank 1, etwa die D-Advanced). Wirkungen: `markieren`
(`a2:'F1:protect'`, `'F1:'` nimmt sie weg), `fliehen` (`'F1+F2'` laufen los
wie beschossen), `opfer` (die eigene Seite will sie tot; deren Feuer kommt
an der Kapersperre vorbei). Auslöser: `genommen` (gekapert); `gescannt` und
`verlaesst` nehmen mehrere Kennungen mit `+`. Ereignisfeld `wenn:{t,a}`: eine
zweite Bedingung, die zugleich gelten muss.

Seit v254: `dockBelly` an einem Andockenden (er rollt nach dem Sprung
halb um seine Längsachse und dockt unter dem Ziel an; `rollC` dreht
Andockpunkt, Geschütze, Subsysteme und Trefferumriss mit). Fracht auf einem
Frachter (`ride` oder angedockt) liegt im 3D-Bild in seiner Tiefe
(`f3dCargoHost`). Subsystem-Markierungen drehen bei einer Wende mit
(`turnC` in `subPos`).

Eine **Kennung steht für eine Gruppe**, nicht für ein Schiff: `byId()` gibt
jede Einheit zurück, die sie trägt, und ein Auslöser darf mehrere mit `+`
nennen. Mission 78 gibt ihren drei Geräten dieselbe Kennung, damit **ein**
Scan-Auslöser für alle drei gilt. Das ist Absicht, kein Fehler.

---


### Seit v257 (Mission 14, Tombaugh)

- Einheit `ally:'ter_…'`: ein verbündetes Großkampfschiff nimmt diesen
  Eintrag aus `ALLY_DEFS` statt des aus dem Bild abgeleiteten. Nur für
  Missionen: `ter_taranis` (Cain, feuert nicht), `ter_halkins` (Chronos,
  Kreuzerklasse, damit die schweren Beams sie nehmen), `ter_tombaugh`
  (Station, bleibt stehen, springt am Ende nicht).
- Einheit `dockStay:true`: bleibt angedockt, bis die Wirkung `abdocken` sie
  löst; dann fährt sie mit `cross` davon.
- `beamFocus:'R1>H1>O1'`: eine Reihenfolge — der erste noch lebende, den
  der Turm erreichen kann. Erreicht er keinen, nimmt er wie sonst den
  nächsten.
- `beamMul` auf einem Supergroßkampfschiff: ihre Beams treffen so viel
  härter.
- `fac` auf einer `sd`-Einheit: die Lucifer in einer Mission unter `hol`.
- Ereignis `hold:true`: hält die Welle offen, bis es gefeuert hat (sonst
  endet die Mission, sobald nur die unverwundbare Lucifer übrig ist).
- `nachschub` mit einer Fraktion statt `an` (`'shivan'`): der Nachschub
  kommt aus deren Pool, nicht aus dem der Welle.

### Seit v258

- `stopX` auf einer `sd`-Einheit: springt bei `x` ein und kommt bei `stopX`
  langsam zum Stehen.
- `shieldShow` auf einer unverwundbaren Einheit mit Schild: erfassbar und
  beschießbar, jeder Treffer lässt den Schild aufflackern.
- Mission `planet:{x, y, w}`: ein fester Planet an dieser Stelle des
  Bildschirms (Mitte), statt der gewürfelten.
- Mission `pri:['avenger','avenger']`: eine Liste setzt jede Primärbank.
- Im FS1-Strang fliegen verbündete Jäger und Bomber nur Rümpfe aus
  `FS1_ALLY_INTRO`, die bis `orig` eingeführt sind (`allySmallPool`).
- Beams auf ein Schiff (nicht `slash`, nicht auf den Spieler) haften an
  einer Rumpfstelle (`beamAnchor`, `beamAncPt`) und treffen nur dort.
- Effekte an einem Großkampfschiff: zwischen `hullFxBegin(e)` und
  `hullFxEnd(h)` erzeugt, liegen sie in ihrer Tiefe (`hz`) und bleiben beim
  Kameraschwenk auf dem Rumpf.
- `f3dWarp(..., pz)`: der Wirbel in der Tiefe des Schiffs.

### Seit v259

- `f3dRender(items, warm, beams)`: ein Tiefenpuffer für den ganzen Stapel,
  jedes Schiff in seiner Scheibe (`gl.depthRange`), Stencil = Nummer des
  obersten Schiffs. `beams` nur aus `f3dFlush`.
- Beams zwischen zwei Modellen: `drawBeamRays` sammelt sie in `F3D_BEAMS`
  (`f3dBeam3D`), `f3dBeamPass` zeichnet sie; `f3dBeamEnds` (Turm, Treffpunkt
  auf der Oberfläche, `b.anc.surf`, `b.anc.vis`).
- `shieldShow`-Einheiten fangen auch Geschosse ab (`bulletOnHull`).
- Radar: `boss`-Kulisse wird gezeigt.

### Seit v260

- `hullFxBegin(e, z)`: Effekte in einer eigenen Tiefe (Oberflächenpunkt).
- `dmgSurf(e, u, v, cache)` / `hullSurfPt`: der sichtbare Punkt der
  Rumpfoberfläche zu einer Stelle der Seitenansicht, im Schiff mitgeführt.
- `f3dRayHitsLocal`: nächster und fernster Schnitt mit dem Modell.
  `f3dBeamEnds` liefert S (Turm), T (Eintritt), X (Austritt), F (dahinter).
- Großkampf-Geschosse: `hz0` (Starttiefe), steigen beim Zeichnen
  (`shotsView`); `capGunShot(..., m)` braucht den Turm.

### Seit v261

- 3D-Beam: eine Gerade S → T → X → F (`f3dBeamEnds`, `d`, `exitDist`).
- Ein- und Austritt im 3D-Bild (`f3dBeamHitFx`), nur in der Scheibe des
  getroffenen Schiffs und im freien Raum gezeichnet (Scheiben merken sich
  ihre Schiffe, `slices[i].ships`). Länge des Austritts: `BEAM_EXIT_LEN`.
  Für 3D-Beams kein flaches Trefferfeuer mehr in `beamImpactAt`.

### Seit v268 (F89)

- Einheit `land:'GA'` an einer Rettungskapsel (`c:'ep'`, `side:'ally'`):
  sie fliegt mit Jägerkurven (`podFly`, `POD_SPEED`, `POD_TURN`) unter den
  Rumpf von GA, um dessen nächstes Ende herum statt quer darüber, und wird
  in den Hangar gezogen (`POD_IN_T`). Danach gilt sie als gerettet
  (`EV_LEFT`, `protSaved`). `bay:[u, v]` setzt die Hangaröffnung als Anteil
  des Rumpfkastens, `u` vom Bug aus (Vorgabe `POD_BAY`, Bauchmitte).
- Mission 90 ist eine reine Testmission (`&m=90`), nicht Teil der Kampagne.

## C. Werkzeuge im Detail

### `tools/pof/` — der POF-Umwandler

Macht aus den FreeSpace-Modellen (POF) das Format, das das Spiel aus
`models/<rumpf>/` lädt: `lo.bin`, `hi.bin` beziehungsweise `full.bin.gz`
und die Texturen als `c/n/g512.webp` und `c/n/g1024.webp`. Python 3 mit
Pillow; in der Cloud ist beides vorhanden (geprüft: Pillow 12.3, WebP ja).

**Das ist der Weg, auf dem alle über hundert Rümpfe entstanden sind.** Er lag
lange außerhalb des Repos und war damit für eine Cloud-Sitzung nicht
vorhanden; Silvio hat ihn in v233 nachgeliefert. Die eigene Anleitung steht
in `tools/pof/README.md`.

**Ein neuer Rumpf:** eine Zeile in `HULLS` in `buildmodels.py`
(`'schluessel': ('MV_Assets_T_1', 'PofName')`) und das Skript für diesen
Schlüssel laufen lassen. `HULLS` ist zugleich die Liste, welcher Spielrumpf
aus welchem MediaVP-Modell kommt — die einzige, die es gibt.

```
export FS3_MVPS=/pfad/zu/MVPS-473
python3 -I tools/pof/buildmodels.py models fimyrmidon,codeimos
```

**Die Modelle gehören nicht ins Repo** (`models/` ist gesperrt). Sie gehen
als ZIP mit Pfaden `models/<schluessel>/…` auf Silvios Server, wo `build.sh`
sie ins Web-Verzeichnis kopiert.

Dazu im selben Ordner: `mkwarp.py` (die Sprungtor-Scheibe), `mkfxsheets.py`
(die Explosions- und Rauchbilder aus den MediaVP-Effekten), `mkthrusters.py`,
`builddebtex.py`.

### `missions_read.py` — die Originalmissionen lesen

Liest die FreeSpace-Missionsdateien in `fs1/`, `str/`, `fs2/` samt ihren
Kampagnendateien. **Keine 1:1-Übersetzung** — eine FreeSpace-Mission hat 35
bis 65 Schiffe und 30 bis 54 Ereignisse, eine FS3-Mission eine Handvoll
Einheiten. Genommen wird daraus, **was in einer Mission passiert**.

`--klassen` sagt, welche Schiffsklassen vorkommen und welchen FS3-Rumpf jede
bekommt. Die Tabelle `HULL` darin ist ausgeschrieben, nicht geraten (FS3
kürzt Namen ab und trägt einen alten Schreibfehler), und wird gegen
`HULL_LEN` im Spiel geprüft.

---

### Seit v262 (Mission 15, The Aftermath)

- Einheit `dockBeside:dy` (zusammen mit `dockTo`): sie dockt nicht an,
  sondern fährt neben das zugewandte Ende des Ziels, `dy` über (-) oder
  unter (+) seiner Mitte, hält dort (`dockHold`) und springt aus. So stehen
  mehrere Transporter an einem Zerstörer nebeneinander statt übereinander.
- Ein Dockauftrag, dessen Ziel noch nicht eingesprungen ist, wartet an Ort
  und Stelle (war schon so, wird in M15 genutzt).
- Das Radar zeigt Aufsammelbares als blinkenden Punkt (grün Reparatur,
  blau Leben).

### Seit v263 (Mission 16, The Big Bang; F82, F83)

- Verbündetes Großkampfschiff: `hurt:0.92` (startet mit diesem Anteil des
  Rumpfs), `bigBang:true` (ihr Ende ist eine große Druckwelle `BIG_BANG`,
  die Jäger, Bomber und den Spieler trifft).
- Geschosse und Flak der Großkampfschiffe starten am sichtbaren Turm in
  der Spielebene (`capSeenPt`); der Aufstieg aus der Tiefe ist weg (F82).
- Die Antwort auf ein gerufenes Großkampfschiff kommt von der Fraktion der
  Gegner der Mission (`missionFoe`, `scriptFoe`), nicht vom Zyklus (F83).

### Seit v264 (F84, F85, F86)

- Mission `huntShare:1`: dieser Anteil der Jäger geht auf das Jagdziel
  (`jagd`/`hunt`); sonst `HUNT_SHARE` (die Hälfte).
- FS1-Standardbewaffnung wächst mit (`fs1Grown`): ab Avenger keine ML-16
  mehr, ab Interceptor keine MX-50, für Spieler und Computer. Die ML-16
  verschwindet dann auch aus der Auswahl.
- Raketenaufschaltung: solange das Ziel im sichtbaren Ausschnitt ist; Klänge
  `lock_seek` (Schleife) und `lock_on` (`sndLock`).
