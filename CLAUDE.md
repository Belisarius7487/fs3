# FS3 — Arbeitsregeln

Browserspiel für die HLP-Community. Silvio ist kreativer Leiter, Claude baut.

Diese Datei liest Claude Code am Anfang jeder Sitzung. Sie steht auf Deutsch,
damit Silvio sie lesen und ändern kann. **Kommentare in den Quelldateien
bleiben auf Englisch**, damit englischsprachige Kollegen sie lesen können.

**Silvios Anleitung steht in `ANLEITUNG.md`** — was er wann zu tun hat. Wird
der Ablauf geändert, wird sie mitgeändert. Er hat nur rudimentäre Code- und
GitHub-Erfahrung: Befehle immer fertig zum Kopieren, mit erwarteter Ausgabe
und Abbruchpunkt.

**Offene Fehler stehen in `OFFENE_FEHLER.md`.** Das ist die einzige Quelle,
die eine Cloud-Sitzung dafür hat: sie sieht nur das Repository, keinen
Chatverlauf und kein Gedächtnis aus früheren Sitzungen. **Meldet Silvio einen
Fehler, wird er dort eingetragen, bevor gebaut wird** — mit seinen eigenen
Worten, nicht mit einer Deutung davon. Sonst ist er in der nächsten Sitzung
verloren.

`FS3_HANDOFF_v127.md` beschreibt Erfahrungen aus den Bauzyklen. Es ist von
v127 und **vor der Umstellung von 2D-Sprites auf 3D-Modelle** geschrieben,
also in Teilen überholt — **im Zweifel gilt der Code, nicht das Handoff.**

---

## 1. Wie mit Silvio zu arbeiten ist

Silvio hat **keine Programmiererfahrung.**

- Alles in normalem Deutsch, keine Fachsprache. Fachbegriffe erklären, wo sie
  unvermeidlich sind.
- Befehle **fertig zum Kopieren**, mit der Angabe, **was als Ausgabe zu
  erwarten** ist, und mit **Abbruchpunkten** („kommt X, dann stopp").
- **Bei Unklarheit fragen, bevor gebaut wird.** Den Umfang bestimmt Silvio.
- **Keine HTML-Vorschauen.** Es wird direkt ins Spiel gebaut und dort
  angesehen. Vorschauen sind zweimal gescheitert.
- **Aussagen über den Code vorher im Code nachlesen, nicht vermuten.**
  `grep -rn "name" src/` kostet nichts, eine falsche Behauptung einen
  Bauzyklus.
- Missionen beschreibt Silvio in Prosa, Claude setzt sie um.
- Bei jeder Lieferung die **vollständige Test-URL** mitgeben, mit Versions-
  und nötigen Modusparametern.

**Wenn Silvio sagt „X geht nicht", ist das der Befund.** Nicht umdeuten in
„vermutlich fehlt Y". Das hat schon einen kompletten Bauzyklus gekostet: Er
meldete, der Rearm-Knopf reagiere nicht; die Antwort war, ihm fehle eine
Korvette. Tatsächlich war der Knopf nie an die Klickauswertung angeschlossen.

---

## 2. Ablauf einer Änderung

In der Cloud hat Claude Code das Repo selbst. **Patch-Skripte werden nicht
mehr geschrieben**: geändert wird direkt in `src/`.

```
1. grep -rn "name" src/          wo liegt es wirklich
2. Änderung in src/              NIE in hlp_shooter_v*_logic.html
3. python3 assemble.py NNN       NNN = höchste vorhandene Version + 1
4. python3 codemap.py            Index in CODEMAP.md nachziehen
5. ./checks.sh                   alle Prüfstufen
6. commit + push                 NUR wenn alles grün ist
```

Danach Silvio auf dem Server `hlp-dev-01`:

```
cd /home/belisarius/fs3-build
git pull
sudo ./build.sh
```

Dann die Test-URL nennen, und Silvio sieht es sich im Browser an.

**Ist eine Prüfstufe rot, wird nichts hochgeschoben.** Dann melden, was rot
ist und warum. Nie eine Prüfung abschalten, überspringen oder ihre Erwartung
dem kaputten Ergebnis anpassen, damit sie grün wird.

Gearbeitet und hochgeschoben wird auf dem Zweig, der für die Sitzung genannt
ist (`claude/...`), **nicht auf `main`**. Auf `main` kommt es erst, wenn
Silvio die Version im Browser abgenommen hat.

### Die alten Patch-Skripte

`patch_v82.py` bis `patch_v216.py` sind die Historie. Sie bleiben liegen,
werden **nicht mehr ausgeführt und nicht mehr geändert**. Was eine Version
geändert hat, steht ab v217 im Commit.

`split_source.py`, `split_assets.py`, `split_images.py` sind ebenfalls Reste
zur Nachvollziehbarkeit und werden nicht ausgeführt.

`save.sh` und `build.sh` laufen **auf Silvios Server** und haben dessen Pfade
(`/home/belisarius/fs3-build`, `/var/www/html/fs3`) fest eingebaut. In der
Cloud laufen sie nicht und werden dort nicht aufgerufen.

---

## 3. Aufbau der Quelle

Die Quelle liegt in `src/`. `assemble.py NNN` setzt die Teile in der
Reihenfolge ihrer Namen zu `hlp_shooter_vNNN_logic.html` zusammen — einer
Datei mit einem Skriptblock, wie alles flussabwärts sie erwartet.

| Datei | Zeilen | Inhalt |
|---|---|---|
| `00_head.html` | 44 | HTML-Hülle, CSS |
| `10_core.js` | 363 | Canvas, Kamera, Welt, Auflösung, Palette, Schriften |
| `12_audio.js` | 576 | Klang: Dateien, Mischung, Entfernung, Stummschaltung |
| `20_render.js` | 2543 | Formenvorrat, Sprites, Masken, Nebel, Planeten, Sterne, Partikel |
| `30_waves.js` | 4417 | Ären, Kampagne, Spawn, Wellenplan, geschriebene Wellen, Spielerschiffe |
| `40_world.js` | 2687 | Gegnerfabrik, Schaden, Schilde, Tickets, Eskorten, `playerOnly` |
| `50_combat.js` | 3377 | Asteroiden, Flug, Zielerfassung, Subsysteme, Beams, Mounts |
| `55_arms.js` | 342 | Bewaffnung |
| `56_banks.js` | 405 | Waffenbänke, Sprengköpfe |
| `57_turrets.js` | 387 | Geschütztürme |
| `58_model3d.js` | 291 | Modelldaten |
| `59_field3d.js` | 1775 | 3D-Darstellung der Schiffe im Feld |
| `60_effects.js` | 1626 | Treffer, Explosionen, Kollision, `update()` |
| `61_glow.js` | 232 | Leuchten |
| `62_perf.js` | 66 | Leistungsmessung |
| `63_fxanim.js` | 222 | Effektbilder (FreeSpace-Animationen, base64) |
| `70_ui.js` | 4450 | `draw()`, Leiste, alle Fenster, Titel, Waffentabellen |
| `71_radar_icons.js` | 30 | Radarsymbole |
| `72_target.js` | 439 | Zielerfassung, Zielkasten |
| `99_tail.html` | 2 | Abschluss der Hülle |

**Die Datei war nie thematisch sortiert.** Geschnitten wurde an
zusammenhängenden Zeilengrenzen, damit byteweise dasselbe herauskam wie
vorher. Manches liegt deshalb in einem Teil, dessen Name nicht passt:

- `syncPause()`, `panelOpen()`, `holdResume()`, `thFit()`, `thChamferPath()`
  liegen in `20_render.js`, nicht in `70_ui.js`.
- `shardBurst()` und die Waffentabelle `PRIMARIES` liegen in `70_ui.js`.
- `PLAYER_SHIPS` liegt in `30_waves.js`.
- `ramsOnContact()` liegt in `50_combat.js`.

**Also vor dem Ändern suchen, nicht raten.**

`CODEMAP.md` hat oben einen handgeschriebenen Wegweiser und darunter einen
Index, den `codemap.py` aus der neuesten Logikdatei erzeugt. Der Index wird
**nicht von Hand** geändert.

---

## 4. Die Prüfstufen

```
./checks.sh              die neueste Logikdatei, alle Stufen
./checks.sh 217          eine bestimmte Version
./checks.sh --fast       ohne die zwei Browserstufen (beim Zwischenstand)
```

`checks.sh` hält von selbst an, wenn die Logikdatei **nicht** das ist, was
`src/` ergibt — sonst prüft man eine Fassung von vorher. Die ausführliche
Ausgabe jeder Stufe steht danach in `checks.log` (nicht im Repo).

| Stufe | prüft | Dauer |
|---|---|---|
| `syntax` | `node --check` auf dem Skript | Sekunden |
| `loadtest` | jede Anweisung auf oberster Ebene läuft durch | Sekunden |
| `swtest` | alle geschriebenen Missionen gegen Auslöser und Wirkungen | Sekunden |
| `docksim` | Andockfälle | Sekunden |
| `mechsim` | Mechanik — **siehe Warnung unten** | Sekunden |
| `shipsim` | Hangar, Leiste, Rearm-Fenster, Titel, Tastatur, Pausenregeln | Sekunden |
| `callsim` | Rufmenü, Textüberlauf | Sekunden |
| `pausesim` | Pausenlogik | Sekunden |
| `hudsim` | obere Leiste, Zeiger, Hover | Sekunden |
| `ramsim` | Rammmechanik | Sekunden |
| `wpnsim` | Waffen, Splitter, Subsystemtreffer, Flak | Sekunden |
| `nctest` | Nichtkämpfer: verbündetes Feuer geht durch Fracht hindurch | Sekunden |
| `fieldsim` | **spielt echte Missionen** in einem Browser ohne Fenster | Minuten |
| `warpsim` | jeden Ein- und Aussprung in jeder Mission | Minuten |

`fieldsim` und `warpsim` brauchen Playwright mit Chromium. In der Cloud ist
beides vorhanden; auf Silvios Server laufen sie nicht.

Die meisten Stufen ziehen die **echten** Funktionen mit regulären Ausdrücken
aus der Logikdatei und lassen sie gegen Attrappen laufen. **Ruft eine
geprüfte Funktion eine neue auf, muss die neue in die Namensliste der
betroffenen Stufe** — sonst bricht die Stufe mit „x is not defined" ab. Genau
das war bei `nctest` passiert: `playerOnly()` rief seit v203 `freighterArmed()`
auf, und die Stufe lief seitdem nicht mehr durch.

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

## 5. Ansichtsschalter für Tests

An die URL anhängen. Geprüft gegen den Code in v216:

| Schalter | Wirkung |
|---|---|
| `?v=NNN` | nur zum Umgehen des Browser-Zwischenspeichers |
| `&ui=1` | ein Ticket jeder Klasse: Kreuzer, Korvette, Zerstörer, Colossus |
| `&ships=N` | N Schiffe (1–9) sofort freigeschaltet |
| `&wpn=1` | alle Waffen sofort verfügbar |
| `&m=NN` | direkt in geschriebene Mission NN |
| `&test=1..5` | Testwellen |
| `&ship=name` | ein bestimmter Rumpf zum Testen |
| `&fs1=N` | Übungsmodus (Rest der verworfenen FS1-Kampagne) |
| `&practice=1` | Übungsmodus |
| `&warp=oval\|rund\|alt` | Form des Sprungtors |
| `&f3d=0` | jedes Schiff als Sprite statt als Modell, zum Vergleichen |

Übliche Testadresse:
`http://dev.hard-light.org/fs3/?v=217&ui=1&ships=9&wpn=1`

**Das Rearm-Fenster braucht eine verbündete KORVETTE** im Feld, nicht
irgendein Großkampfschiff. Der Hangar braucht einen **Zerstörer**.

---

## 6. Oberfläche: ein gemeinsamer Formenvorrat

Alle Bildschirme werden aus **einem** Satz Formen gebaut, in `20_render.js`
(`thChamferPath`, `thPlate`, `thGloss`, `thCutGlint`, `thGlowPath`,
`thBrackets`, `thScale`, `thFrame`, `thFit`, `thRGBA`). Ein Bildschirm nimmt
daraus und erfindet nichts Eigenes.

- Der **Leuchtring und die Winkel gehören dem aktiven Zustand.** Was bloß
  verfügbar ist, bekommt nichts.
- **Kein Courier** in neuen Bildschirmen. Tahoma (`thLabel`) für
  Beschriftungen, Segoe UI (`thValue`) für Werte.
- **Jeder Text durch `thFit`**, mit der Breite seiner Zelle. Sonst laufen
  Beschriftungen aus Knöpfen heraus.
- `UI()`, `uiLabel()`, `uiValue()`, `uiHLP()`, `thPanel()`, `thBevel()` sind
  Reste und verschwinden mit dem Umbau der Bildschirme, die sie noch nutzen.

### Pausen- und Fensterregeln

- `panelOpen()` fragt, ob **irgendein** Fenster offen ist. Ein neues Fenster
  trägt sich **dort** ein und sonst nirgends.
- **Nach dem Schließen bleibt das Spiel stehen**, bis einmal getippt wird.
  Dieser Tipp wird verbraucht und löst nichts anderes aus.
- **Jedes Fenster meldet sein Rechteck** (`window._*PanelRect`) und schluckt
  Klicks darauf. Nur außerhalb wird geschlossen.
- `syncCursor()` entscheidet als **einzige** Stelle über den Mauszeiger.

---

## 7. Waffen

Waffen sind **Daten**, keine Verzweigungen: `PRIMARIES` und die Sekundärliste
in `70_ui.js`. Eine neue Waffe ist eine Zeile.

- **Bomben nur für Bomber, Raketen nur für Jäger.**
- Der Munitionsvorrat gehört zum **Rumpf** (`PLAYER_SHIPS.sec`), die Waffe
  skaliert ihn mit `ammoMul`.
- Der Wechsel **füllt auf**, auch auf dieselbe Waffe — daher der Name REARM.
- `shardBurst()` ist **einmal** geschrieben; Dante, Infyrno und die Flak rufen
  alle sie.
- Die Prometheus trägt Schadens- und Ratenfaktor **1,0**; daran ist
  nachweisbar, dass die Standardbewaffnung unverändert ist.

---

## 8. Missionen

Geschriebene Missionen stehen als Daten in `SCRIPT_WAVES` (`30_waves.js`),
mit Einheiten (`u`) und Ereignissen (`ev`). `swtest` prüft sie gegen die
bekannten Auslöser und Wirkungen und nennt beide Listen am Ende seiner
Ausgabe.

Eine **Kennung steht für eine Gruppe**, nicht für ein Schiff: `byId()` gibt
jede Einheit zurück, die sie trägt, und ein Auslöser darf mehrere mit `+`
nennen. Mission 78 gibt ihren drei Geräten dieselbe Kennung, damit **ein**
Scan-Auslöser für alle drei gilt. Das ist Absicht, kein Fehler.

---

## 9. Rammmechanik — teuer erkämpfte Regeln

1. **Berührung heißt Rumpf an Rumpf, nicht Mitte an Mitte.**
2. **Gemessen wird am sichtbaren Rumpf** (`spriteBox()`), nicht am
   Bildrechteck: Sprites haben durchsichtige Ränder, und die kollidierten.
3. **Ein Rammkurs steuert sich selbst.** Die normale Stationsfahrt in
   `tickEnemies()` muss für `capRam` übersprungen werden.
4. **Wer `ramBlast()` ruft, nimmt das Schiff danach selbst aus `enemies`** —
   sonst bleibt es als Geist stehen: nicht abschießbar, aber weiter fliegend
   und feuernd.
5. **Kamikaze ist die Doktrin des Hammer of Light**, geregelt an einer Stelle:
   `ramsOnContact()`. Aufprallprüfung und gelber Doppelwinkel lesen sie beide,
   damit Warnung und Verhalten nicht auseinanderlaufen.

---

## 10. Was nicht angefasst wird

- `hlp_shooter_v*_logic.html` — wird von `assemble.py` erzeugt. Änderungen
  gehören in `src/`.
- Der Bereich zwischen `<!-- AUTO:START -->` und `<!-- AUTO:END -->` in
  `CODEMAP.md` — erzeugt `codemap.py`.
- `patch_v*.py`, `split_*.py` — Historie.
- Bilddaten: `SPR_DATA`, `ICON_DATA`, `PLANET_DATA`, `SUN_DATA`, `MOUNTS`
  bleiben in der Logikdatei **leer**. Der Packer `build_game.py` füllt sie
  beim Bauen aus den Ordnern auf dem Server.
- Logikdateien älterer Versionen — sie bleiben als Stand liegen. Beim Suchen
  im Code also `src/` durchsuchen, nicht das Verzeichnis: `grep -rn "x" src/`.
