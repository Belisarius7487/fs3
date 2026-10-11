# FS3 — offene Fehler und offene Punkte

**Warum diese Datei existiert:** Eine Cloud-Sitzung sieht **nur das
Repository**. Kein Chatverlauf, kein Gedächtnis aus früheren Sitzungen. Was
nur im Chat gemeldet wurde, ist für die nächste Sitzung verloren.

Deshalb: **Was hier nicht steht, weiß ich nicht.** Silvio meldet einen Fehler
im Chat, Claude trägt ihn hier ein — mit Silvios eigenen Worten, nicht mit
einer Deutung davon.

**Regel für Einträge:** Der Befund steht so da, wie Silvio ihn beschrieben
hat. Eine Vermutung über die Ursache steht getrennt darunter und ist als
Vermutung erkennbar, bis sie im Code nachgewiesen ist. Das hat einen Grund:
Ein Bauzyklus ging schon verloren, weil „der Rearm-Knopf reagiert nicht" in
„vermutlich fehlt eine Korvette" umgedeutet wurde. Der Knopf war nie
angeschlossen.

Stand: v216 ist die spielbare Fassung.

---

## Offen

### F1 — Dunkles Rechteck um Explosionen und Raketentrails

**Befund (Silvio, 11.10.2026):** „Die neu hinzugekommenen Explosionseffekte
und Raketentrails haben alle ein dunkles halbtransparentes Rechteck um sich."

Betrifft die Effekte, die mit v216 hinzukamen (MediaVP-Animationen Exp05,
Exp20, ParticleSmoke01, MissileTrail01 in `src/63_fxanim.js`).

**Ursache (nachgewiesen, nicht vermutet):** Alle vier Bildbögen in
`63_fxanim.js` sind verlustbehaftetes WebP **ohne Alphakanal** — an den
Bilddaten geprüft: Modus `RGB`, die Ecken deckend schwarz. Jede Zelle ist
also vollflächig deckend, mit Schwarz dort, wo sie durchsichtig sein müsste.

Beide gemeldeten Symptome kommen aus derselben Stelle: `drawFxSmoke()`
zeichnet mit `source-over` bei 30–55 % Deckkraft. Ohne Alphakanal ist das
genau ein dunkles halbtransparentes Rechteck. Explosionen erzeugen Rauch
(`spawnSmoke`), Raketentrails auch (`trailFeed` legt Rauchwölkchen ab) —
darum zeigen beide es. Feuer (`drawFxAnims`) und die Trail-Linie selbst
(`drawTrail`) werden mit `lighter` gezeichnet, wo Schwarz nichts beiträgt;
die waren nie betroffen.

Die Originalbilder (MediaVP-PNGs, `fx/mkfxsheets.py`) liegen **nicht** im
Repo, die Bögen lassen sich hier also nicht mit Alpha neu bauen.

- Behoben in: v217 — das Alpha wird beim Laden aus der Helligkeit
  zurückgewonnen (schwarz wird durchsichtig)
- Status: gebaut, wartet auf Silvios Test im Browser

### F2 — Subsystemnamen werden nicht immer angezeigt

**Befund (Silvio, 11.10.2026):** „Durch die Umstellung auf 3D Modelle werden
die Namen der Subsysteme auf Schiffen nicht immer angezeigt, wenn der Spieler
sich in deren Nähe befindet und darauf ausrichtet."

„Nicht immer" heißt: es passiert, aber nicht bei jedem Schiff oder nicht in
jeder Lage. Welche Schiffe und welche Lage, ist noch zu klären — **bei Silvio
nachfragen, nicht raten.**

- Ursache: noch nicht untersucht
- Status: offen

### F3 — Bast-Frachter sind nicht mehr zu beschützen

**Befund (Silvio, 11.10.2026):** „Durch das vergrößerte Spielfeld und das
neue Verhalten der Schiffe nach links und rechts zu fliegen, sind die
Bast-Frachter in der Mission, in der sie beschützt werden sollen, nicht mehr
zu beschützen, da sie hin und her fliegen, statt rechts aus dem Bild zu
warpen."

Silvio nennt hier selbst zwei Änderungen als Ursache: das vergrößerte
Spielfeld und das neue Links-Rechts-Flugverhalten. Beide treffen zu.

**Die Mission:** M9 „The Convoy" (Auftrag `protect`, zwei Bast mit
`cross:0.38`, `dockTo:'C1'`). M23 „The Pickup" hat dieselbe Konstruktion und
war damit genauso betroffen.

**Ursache (nachgewiesen, nicht vermutet):**

- `30_waves.js:887` setzt beim Andocken `dockTo = null`.
- `30_waves.js:897` beginnt im selben Moment das Queren (`crossing`).
- `capHolds()` in `57_turrets.js` nahm `still`, `capRam`, `transit`,
  `dockTo`, `fleeing`, `escaping` aus — **aber nicht `crossing`**.

Genau ab dem Andocken übernahm also `capLane()` (seit v211 ausdrücklich auch
für Frachter: `CAP_VEL_TYPE.freighter = 40`) das Ruder und schob das Schiff
auf seiner Bahn, **zusätzlich** zum Queren — und dreht am Bahnende um.
`laneLimit()` zieht dieses Ende vor jedes andere Schiff in derselben Bahn,
in M9 also vor die Aten. Im Feld gemessen: 4,628 Einheiten je Schritt statt
der vorgesehenen 1,001.

Dieselbe Fehlerform wie bei der Ramme (Handoff, Punkt 8.3): ein
selbststeuernder Kurs, über den die normale Fahrt hinwegfährt. Ein Queren
**ist** die Fahrt, nicht ein Zuschlag auf fremde Fahrt.

Warum es nicht immer auffiel: ob das Schiff trotzdem herauskommt, hängt
davon ab, wohin seine Bahn zufällig läuft (`laneInit` nimmt die Bugrichtung)
und ob die Kehre es vorher erwischt. `fieldsim` bestand M9 deshalb weiterhin.

**Behoben in v217:** `crossing` steht jetzt in `capHolds()`. Neue Prüfung in
`fieldsim.js` („M09 a crossing freighter is driven by her crossing alone"):
sie stellt den Zustand selbst her, statt von Kampfglück abzuhängen, und
misst die eine Regel — ein Schritt bewegt das Schiff um genau sein
`crossing`. Gegen v216 gestellt: fällt durch (4,628 statt 1,001). Auf v217:
grün (1,001).

- Status: gebaut, wartet auf Silvios Test im Browser

---

## Früher berichtet, hier noch nicht eingetragen

Silvio hat in früheren Sitzungen Fehler gemeldet, die nur im Chat stehen.
**Die sind in einer Cloud-Sitzung nicht sichtbar.** Was davon noch offen ist,
muss einmal neu benannt werden und kommt dann hierher.

---

## Erledigt

### Prüfstufe `nctest` lief seit v203 nicht mehr (behoben vor v217)

`playerOnly()` rief seit v203 `freighterArmed()` auf, das die Prüfung nicht
mit aus der Logikdatei zog. Die Stufe brach jedes Mal mit „freighterArmed is
not defined" ab, ohne dass es auffiel. Dabei zeigte sich, dass ihre letzte
Prüfung nur zählte, ob die Sicherung in zwei Trefferschleifen steht — das
Spiel hat vier.

### `swtest` meldete einen Fehler, der keiner ist (behoben vor v217)

Mission 78 gibt ihren drei Geräten absichtlich dieselbe Kennung, damit ein
Scan-Auslöser für alle drei gilt. `swtest` zählte das als Problem und hätte
damit jeden Push blockiert.

---

## Offene Punkte aus dem Handoff (v127) — Gültigkeit unklar

`FS3_HANDOFF_v127.md` ist von v127 und **vor der Umstellung von 2D-Sprites
auf 3D-Modelle** geschrieben. Seine Punkt-9-Liste ist entsprechend alt. Ob
diese Punkte noch gelten, entscheidet Silvio:

1. **Auftragsbanner** — letzter Bildschirmteil in Courier, zusammen mit OBJ-
   und FPS-Anzeige (`70_ui.js`).
2. **Aufräumen** — nie aufgerufene Funktionen; Frage, ob Ären- und FS1-Blöcke
   ganz rausfliegen, da die Kampagnenidee verworfen ist.
3. **Fraktionsabschnitte im Würfel** — ab Welle 31 würfelt der Generator jede
   Welle die Fraktion neu. Vorschlag war: einen Abschnitt von drei bis fünf
   Wellen an derselben Front. Offen war: feste Ordnung der Fronten oder
   zufällig? (`30_waves.js`, `rollWave()`)
4. **TAG-A-Rakete** samt Testmission. (TAG-C gibt es inzwischen — `wpnsim`
   prüft sie in Mission 67. Also womöglich schon erledigt oder überholt.)
5. **Mehr geschriebene Missionen** — Vorschlag war, ab Welle 31 jede zehnte
   zu schreiben statt den geschriebenen Block zu verlängern. Inzwischen
   prüft `swtest` **80** Missionen, das Handoff sprach von 21. Der Punkt ist
   also in Arbeit oder erledigt.
6. **Veralteter Rammteil in `mechsim`** — enthält eine von Hand
   abgeschriebene Kopie von `tickCapRam`, die einen Fehler nicht sehen
   konnte, den das Spiel zeigte. `ramsim.js` liest das Original. Die Kopie
   sollte raus, damit sie kein falsches Vertrauen stiftet.
