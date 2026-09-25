# FS3 — Handoff, Stand v127

Browserspiel für die HLP-Community. Silvio ist kreativer Leiter, Claude baut.
Veröffentlichung an die Community zum **1. April**.

Dieses Dokument enthält, was zum Weiterarbeiten nötig ist. Was an
Gestaltungs- und Spielentscheidungen früher festgelegt wurde, steht in Claudes
Gedächtnis unter `/areas/fs3.md` und wird hier **nicht** wiederholt — dieses
Handoff beschreibt den **technischen Stand, den Arbeitsablauf und die offenen
Punkte**.

---

## 1. Wie mit mir zu arbeiten ist

Silvio hat **keine Programmiererfahrung.**

- Alles in normalem Deutsch, keine Fachsprache. Fachbegriffe erklären, wo sie
  unvermeidlich sind.
- Befehle **fertig zum Kopieren**, mit der Angabe, **was als Ausgabe zu
  erwarten** ist, und mit **Abbruchpunkten** („kommt X, dann stopp und melde
  dich").
- **Kommentare in Dateien auf Englisch**, damit englischsprachige Kollegen sie
  lesen können. Antworten im Chat auf Deutsch.
- **Bei Unklarheit fragen, bevor gebaut wird.** Den Umfang bestimmt Silvio.
- **Keine HTML-Vorschauen.** Es wird direkt ins Spiel gebaut und dort
  angesehen. Vorschauen sind in Vorgesprächen zweimal gescheitert.
- **Aussagen über den Code vorher im Code nachlesen, nicht vermuten.**
- Missionen beschreibt Silvio in Prosa, Claude setzt sie um.
- Bei jeder Lieferung die **vollständige Test-URL** mitgeben, inklusive
  Versions- und nötiger Modusparameter.

**Wichtigste Lehre aus den bisherigen Sitzungen:** Wenn Silvio sagt „X geht
nicht", ist das der Befund. Nicht umdeuten in „vermutlich fehlt Y". Das hat
schon einmal einen kompletten Bauzyklus gekostet: Er meldete, der
Rearm-Knopf reagiere nicht; ich erklärte ihm stattdessen, ihm fehle eine
Korvette. Tatsächlich war der Knopf nie an die Klickauswertung angeschlossen.

---

## 2. Arbeitsablauf

**Server:** `hlp-dev-01`, Verzeichnis `/home/belisarius/fs3-build`
**Repo:** `github.com/Belisarius7487/fs3` (Silvio lädt über die GitHub-Weboberfläche hoch)
**Test-URL:** `http://dev.hard-light.org/fs3/?v=NNN`

### Der Ablauf pro Änderung

1. Claude liefert `patch_vNNN.py` (und geänderte Simulationen) im Chat.
2. Silvio lädt sie über GitHub hoch — **unten auf „Commit changes" drücken**,
   sonst passiert nichts. Das ist schon zweimal schiefgegangen.
3. Auf dem Server:

```
cd /home/belisarius/fs3-build
git pull
python3 patch_vNNN.py
python3 assemble.py NNN
sudo ./build.sh
```

4. Silvio sieht es sich im Browser an und meldet zurück.
5. **Erst nach erfolgreichem Test** sichern:

```
bash save.sh NNN "kurze Beschreibung"
```

`save.sh` aktualisiert die CODEMAP, nimmt alles mit, was noch nicht im Repo
ist, und schiebt es hoch.

### Patches

Ein Patch ist ein Python-Skript, das **exakten Text sucht und ersetzt**. Jede
Ersetzung muss **genau einmal** passen, sonst bricht das Skript ab und
schreibt nichts. Das ist die Sicherung: Ein Patch, der nicht passt, richtet
keinen Schaden an.

Patches fassen seit v127 **Teildateien in `src/`** an, nicht mehr die
zusammengesetzte Logikdatei. Danach muss `assemble.py` laufen.

---

## 3. Aufbau der Quelle

Seit v127 liegt die Quelle in **`src/`**, in sieben Teilen plus Hülle.
`assemble.py NNN` setzt sie zu `hlp_shooter_vNNN_logic.html` zusammen. Alles
flussabwärts — `build.sh`, `build_game.py`, alle elf Prüfstufen — sieht
weiterhin **eine** Datei mit **einem** Skriptblock.

| Datei | Zeilen | Inhalt |
|---|---|---|
| `00_head.html` | 40 | HTML-Hülle, CSS |
| `10_core.js` | 197 | Canvas, Auflösung, gespeicherte Einstellungen, Palette, Schriften |
| `20_render.js` | 986 | Formenvorrat, Sprites, Masken, Nebel, Planeten, Sterne, Partikel |
| `30_waves.js` | 2302 | Ären, Kampagne, Spawn-Optionen, Wellenplan, geschriebene Wellen |
| `40_world.js` | 2171 | Gegnerfabrik, Schaden, Schilde, Stationsfahrt, Tickets, Eskorten |
| `50_combat.js` | 2525 | Asteroiden, Flug, Zielerfassung, Subsysteme, Beams, Bewaffnung |
| `60_effects.js` | 1044 | Treffereffekte, Explosionen, Kollision, `update()` |
| `70_ui.js` | 2509 | `draw()`, Leiste, alle Fenster, Titel, Abschluss, Eingabe |
| `99_tail.html` | 3 | Abschluss der Hülle |

**Der Schnitt war beweisbar korrekt:** Aus den Teilen zusammengesetzt kam
byteweise dieselbe Datei heraus wie vorher. Deshalb wurde an
**zusammenhängenden** Zeilengrenzen geschnitten statt thematisch umsortiert.

**Folge davon, die man kennen muss:** Die Datei war nie thematisch sortiert.
Manches liegt in einem Teil, dessen Name nicht passt. Bekanntester Fall:
`syncPause()`, `panelOpen()`, `holdResume()` und `clearResumeHold()` liegen in
`20_render.js`, nicht in `70_ui.js`. **Vor dem Patchen also suchen, nicht
raten**, zum Beispiel mit `grep -rn "funktionsname" src/`.

`split_source.py` liegt zur Nachvollziehbarkeit im Repo und wird **nicht mehr
ausgeführt**.

---

## 4. Die elf Prüfstufen

Neue Mechanik ohne Simulation gilt als **ungeprüft**. Vor jeder Lieferung
laufen alle elf durch.

```
# Skript aus der Logikdatei ziehen (loadtest erwartet es als v82.js)
python3 - <<'EOF'
import re
s=open('hlp_shooter_v127_logic.html',encoding='utf-8').read()
open('v82.js','w',encoding='utf-8').write(re.search(r'<script[^>]*>([\s\S]*)</script>',s).group(1))
EOF

node --check v82.js
node loadtest.js
node swtest.js   hlp_shooter_v127_logic.html
node docksim.js  hlp_shooter_v127_logic.html hlp_mounts_final.json
node mechsim.js
node shipsim.js  hlp_shooter_v127_logic.html
node callsim.js  hlp_shooter_v127_logic.html
node pausesim.js hlp_shooter_v127_logic.html
node hudsim.js   hlp_shooter_v127_logic.html
node ramsim.js   hlp_shooter_v127_logic.html
node wpnsim.js   hlp_shooter_v127_logic.html
```

| Stufe | prüft |
|---|---|
| `node --check` | Syntax |
| `loadtest` | alle Anweisungen auf oberster Ebene laufen durch (fängt falsche Reihenfolge nach einem Umbau) |
| `swtest` | 30 geschriebene Missionen gegen die bekannten Auslöser und Wirkungen |
| `docksim` | 31 Andockfälle |
| `mechsim` | Mechanik, **aber siehe Warnung unten** |
| `shipsim` | Hangar, Leiste, Rearm-Fenster, Titel, Tastatur, Pausenregeln |
| `callsim` | Rufmenü, Textüberlauf |
| `pausesim` | Pausenlogik |
| `hudsim` | obere Leiste, Zeiger und Hover |
| `ramsim` | Rammmechanik (Bomber und Großkampfschiff) |
| `wpnsim` | Waffen, Splitter, Subsystemtreffer, Flak |

`shipsim`, `callsim`, `pausesim`, `hudsim`, `ramsim` und `wpnsim` ziehen die
**echten** Funktionen mit regulären Ausdrücken aus der Logikdatei und lassen
sie gegen Attrappen laufen. Wird eine Funktion umbenannt oder eine neue
eingeführt, die eine geprüfte aufruft, muss sie in die `names`-Liste der
betroffenen Simulation.

### Warnung zu `mechsim`

`mechsim.js` enthält eine **von Hand abgeschriebene Kopie** von `tickCapRam`.
Sie meldete „7 von 7 Starthöhen getroffen", während der Rammkreuzer im Spiel
sichtbar danebenflog — die Kopie konnte den Fehler nicht sehen, weil er
woanders saß. `ramsim.js` ersetzt diesen Teil und liest das Original.
**Der veraltete Rammteil in `mechsim` sollte bei Gelegenheit raus**, damit er
kein falsches Vertrauen stiftet.

### Was Simulationen gut können und was nicht

Mehrfach hat eine Prüfung etwas bestanden, das im Spiel kaputt war. Immer aus
demselben Grund: **Die Prüfung ließ nur den Teil laufen, der geändert wurde.**

- `ramsim` rief nur `tickCapRam()`. Im Spiel bewegt `tickEnemies()`
  Großkampfschiffe **auch** — und stärker. Der Rammkurs wurde überfahren.
- `shipsim` öffnete das Rearm-Fenster über `toggleRearmMenu()`. Damit prüft man
  das Fenster, nicht den Knopf. Der Knopf war nie angeschlossen.

**Daraus die Regel:** Eine neue Prüfung immer **gegen die kaputte Vorversion
stellen**. Wenn sie dort nicht fehlschlägt, prüft sie das Falsche. Das ist
inzwischen fester Bestandteil des Ablaufs und hat mehrfach etwas gefunden.

Wo eine Funktion zu verflochten ist, um sie in der Simulation laufen zu lassen
(`tickEnemies`, `flySmall`, `drawTitle`), wird **am Quelltext geprüft** — etwa,
dass eine Absicherung an der richtigen Stelle steht. Schwächer als ein
Verhaltenstest, aber besser als nichts, und es hätte die Fehler gefunden.

---

## 5. Ansichtsschalter für Tests

An die URL anhängen:

| Schalter | Wirkung |
|---|---|
| `?v=NNN` | nur zum Umgehen des Browser-Zwischenspeichers |
| `&ui=1` | ein Ticket jeder Klasse: Kreuzer, Korvette, Zerstörer, Colossus |
| `&ships=N` | N Schiffe (1–8) sofort freigeschaltet |
| `&wpn=1` | alle Waffen sofort verfügbar |
| `&m=NN` | direkt in geschriebene Mission NN |
| `&test=1..4` | Testwellen |
| `&fs1=N` | Übungsmodus (Rest der verworfenen FS1-Kampagne) |

Übliche Testadresse:
`http://dev.hard-light.org/fs3/?v=127&ui=1&ships=8&wpn=1`

Wichtig: **Das Rearm-Fenster braucht eine verbündete KORVETTE** im Feld, nicht
irgendein Großkampfschiff. Der Hangar braucht einen **Zerstörer**.

---

## 6. Die Oberfläche: ein gemeinsamer Formenvorrat

Alle Bildschirme werden aus **einem** Satz Formen gebaut. Ein Bildschirm nimmt
daraus und erfindet nichts Eigenes — nur das hält sechs Fenster wie eine
Oberfläche aussehend. Der Vorrat steht in `20_render.js`:

| Funktion | was sie ist |
|---|---|
| `thChamferPath` | die Signatur: Ecke oben links und unten rechts auf 45° abgeschnitten |
| `thPlate` | flache Fläche, dunkle Umrisslinie, helle Haarlinie oben, Glanz, Kantenlicht |
| `thGloss` | flacher Lichtabfall über dem oberen Drittel, auf die Plattenform beschnitten |
| `thCutGlint` | die beiden Schnittflächen der Schräge, hell |
| `thGlowPath` | der Leuchtring des Themes entlang der Schräge |
| `thBrackets` | zwei Winkel an den zwei Ecken, die die Schräge stehen lässt — **nur für den aktiven Zustand** |
| `thScale` | Haarlinie mit Teilstrichen an den Spalten |
| `thFrame` | Fenster: Schleier, Platte, Ring, Kopfzeilenregel in zwei Stärken |
| `thFit` | Text, der seine Zelle nicht verlassen kann — **immer benutzen** |
| `thRGBA` | Themefarbe mit Alpha |

**Regeln, die nicht gebrochen werden dürfen:**

- Der **Leuchtring und die Winkel gehören dem aktiven Zustand.** Was bloß
  verfügbar ist, ist der Normalfall und bekommt nichts.
- **Kein Courier** mehr in neuen Bildschirmen. Tahoma (`thLabel`) für
  Beschriftungen, Segoe UI (`thValue`) für Werte.
- **Jeder Text durch `thFit`**, mit der Breite seiner Zelle. Sonst laufen
  Beschriftungen aus Knöpfen heraus — genau das war der Fehler im alten
  Rufmenü.
- Die alten Helfer `UI()`, `uiLabel()`, `uiValue()`, `uiHLP()`, `thPanel()`,
  `thBevel()` sind **Reste**. Sie stehen noch in Bildschirmen, die noch nicht
  umgebaut sind, und verschwinden mit deren Umbau.

### Pausen- und Fensterregeln

- `panelOpen()` fragt, ob **irgendein** Fenster offen ist. Ein neues Fenster
  trägt sich **dort** ein und sonst nirgends. (Vorher zählte `syncPause()` die
  Fenster einzeln auf — und ein neues wurde prompt vergessen, weshalb das
  Rearm-Fenster das Spiel nicht anhielt.)
- **Nach dem Schließen bleibt das Spiel stehen**, bis einmal getippt wird. Für
  jedes Fenster und jeden Weg hinaus: Auswahl getroffen, ESC, danebengetippt.
  Der Tipp, der zurückholt, wird dafür verbraucht und löst nichts anderes aus.
- **Jedes Fenster meldet sein Rechteck** (`window._*PanelRect`) und schluckt
  Klicks darauf. Nur außerhalb wird geschlossen.
- `syncCursor()` entscheidet als **einzige** Stelle über den Mauszeiger:
  sichtbar über der Leiste, sichtbar wenn das Spiel nicht läuft, unsichtbar
  über dem Feld.

---

## 7. Waffen

Waffen sind **Daten**, keine Verzweigungen. Tabellen `PRIMARIES` und
`SECONDARIES` in `70_ui.js`. Eine neue Waffe ist eine Zeile.

Die Prometheus trägt als Schadens- und Ratenfaktor jeweils **1,0** — dadurch
ist nachweisbar, dass die Standardbewaffnung unverändert ist. Die Prüfung hält
das fest.

| Waffe | Art | ab Punkten | Eigenheit |
|---|---|---|---|
| Prometheus | primär | 0 | Standard, unbegrenzte Reichweite |
| Mekhu / Subach HL-7 | primär | 6.000 | schneller, leichter, Reichweite 330 |
| Streuschuss | primär | 14.000 | Kegel aus 7 Schroten je Lauf |
| Durchschlag | primär | 22.000 | nimmt 4 Rümpfe auf seiner Linie, jeden einmal |
| Dante | primär | 32.000 | zündet beim Aufprall **und** nach 300 Punkten |
| MX-64 | Rakete | 0 | Standard |
| Infyrno | Rakete | 18.000 | Sekundärknopf zündet die fliegende |
| Cyclops | Bombe | 0 | Standard |
| Stiletto | Bombe | 26.000 | ganzer Sprengkopf ins nächste lebende Subsystem |

- **Bomben nur für Bomber, Raketen nur für Jäger.**
- Munitionsvorrat gehört zum **Rumpf** (`PLAYER_SHIPS.sec`), die Waffe skaliert
  ihn mit `ammoMul`.
- Der Wechsel **füllt auf**, auch auf dieselbe Waffe. Deshalb heißt das Fenster
  REARM.
- `shardBurst()` ist **einmal** geschrieben; Dante, Infyrno und die Flak rufen
  sie alle.

**Flak auf Großkampfschiffen** (ab Kreuzer, beide Seiten): eigene Uhr, feuert
von einem vorhandenen Primärmount. Die Wand steht dort, wo das Ziel ist,
höchstens `FLAK_DIST` (300) draußen, mindestens `FLAK_MIN` (110), und wird
zurückgezogen, bis der Zündpunkt `FLAK_EDGE_KEEP` (130) innerhalb des Feldes
liegt.

---

## 8. Rammmechanik — teuer erkämpfte Regeln

Vier Fehler hintereinander, alle mit derselben Form: **etwas wurde an der
falschen Stelle gemessen oder gesetzt.** Wer hier etwas ändert, sollte sie
kennen:

1. **Berührung heißt Rumpf an Rumpf, nicht Mitte an Mitte.** Ein Zerstörer ist
   mehrere hundert Punkte breit; ein Abstandsvergleich zur Mitte kann nie
   auslösen.
2. **Gemessen wird am sichtbaren Rumpf**, nicht am Bildrechteck. Sprites haben
   durchsichtige Ränder, und die kollidierten. `spriteBox()` liest die Grenzen
   aus der vorhandenen Pixelmaske.
3. **Ein Rammkurs steuert sich selbst.** Die normale Stationsfahrt in
   `tickEnemies()` muss für `capRam` übersprungen werden, sonst überfährt sie
   den Kurs. `capRam` ist die Fahrt selbst, nicht ein Zuschlag auf fremde
   Fahrt.
4. **Wer `ramBlast()` ruft, nimmt das Schiff danach selbst aus `enemies`.** Die
   Aufräumschleife greift nur bei `hp<=0 && !dead`, und `ramBlast` setzt beides
   — ein Schiff, das dort ankommt, bleibt sonst als Geist stehen: ohne Winkel,
   nicht abschießbar, nicht mitgezählt, aber weiter fliegend und feuernd.
5. **Kamikaze ist die Doktrin des Hammer of Light**, geregelt an einer Stelle:
   `ramsOnContact()`. Sowohl die Aufprallprüfung als auch der gelbe
   Doppelwinkel lesen sie, damit Warnung und Verhalten nicht auseinanderlaufen
   können. Ein Rammkurs bricht seinen Anflug **nicht** ab.

---

## 9. Offene Punkte

In der Reihenfolge, in der ich sie angehen würde:

1. **Fehler, die Silvio noch benennen muss.** Er hat erwähnt, es seien noch
   welche drin; sie wurden nie beschrieben. **Zuerst danach fragen.**
2. **Der Auftragsbanner** — der letzte Bildschirmteil in Courier, zusammen mit
   der OBJ- und der FPS-Anzeige. Der letzte Punkt aus der ursprünglichen
   Reihenfolge des Oberflächenumbaus. Sitzt in `70_ui.js`.
3. **Aufräumen.** Elf nie aufgerufene Funktionen: `boom`, `drawHullBg`,
   `eraPool`, `fleeingEnemy`, `objFits`, `secBtnDown`, `secBtnUp`, `thGlow`,
   `uiHLP`, `updateSecBtn`, `volley`. Dazu die Frage, ob die Ären- und
   FS1-Blöcke ganz rausfliegen — die Kampagnenidee ist verworfen. Auch die
   Zeile PRACTICE MODE in den Einstellungen bietet noch etwas an, was es nicht
   mehr geben soll. **Entscheidet Silvio.**
4. **Fraktionsabschnitte im Würfel.** Ab Welle 31 würfelt der Generator jede
   Welle die Fraktion neu, sodass auf eine NTF-Welle direkt eine Shivaner-Welle
   folgen kann. Vorschlag: nicht je Welle würfeln, sondern einen **Abschnitt**
   von drei bis fünf Wellen an derselben Front; innerhalb davon würfelt es
   weiter frei. **Begründung ist taktisch, nicht erzählerisch:** Schiffs- und
   Waffenwahl sollen länger als eine Welle gültig bleiben. Es darf **kein**
   zusätzlicher Text auf den Bildschirm. Sitzt in `30_waves.js` (`rollWave()`).
   Offen: Soll die Abfolge der Fronten zufällig sein oder eine feste Ordnung
   haben?
5. **TAG-A-Rakete**, samt einer Testmission dafür. Idee: fast kein Schaden,
   markiert ein Ziel für einige Sekunden — im Nebel aufschaltbar, verbündete
   Großkampfschiffe schießen bevorzugt darauf.
6. **Mehr geschriebene Missionen.** Geschrieben sind **21** (Wellen 10–30); ab
   31 übernimmt der Generator. Ein Durchlauf von Silvio erreichte Welle 131 in
   knapp zwei Stunden. Vorschlag: **nicht** den geschriebenen Block
   verlängern, sondern **jede zehnte Welle** ab 31 schreiben — bis Welle 100
   sind das sieben statt siebzig.
7. **Aufräumen der Teildateien.** `syncPause()` und Verwandte liegen in
   `20_render.js`, weil sie dort standen. Erst angehen, wenn es wirklich
   stört.

---

## 10. Stand der Technik

- **Aktuell: v127.** Logikdatei 497 KB, gebautes `index.html` 20,3 MB
  (Sprites, Planeten und Sonnen eingebettet).
- Leistung geprüft: Welle 131, fast zwei Stunden Laufzeit, **stabile 60
  Bilder/s**. Keine Ansammlung von Trümmern oder Geschossen über Wellen
  hinweg.
- 446 Funktionen auf oberster Ebene, 11.734 Zeilen in `src/`.
- Alle elf Prüfstufen laufen durch.
