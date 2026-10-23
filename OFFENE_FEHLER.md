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

Stand: Silvio hat v230 im Browser getestet; v231 liegt zum Test bereit.

---

## Wichtig für die Reihenfolge (Silvio, v225)

**Alle Missionen müssen ohnehin von Grund auf neu gebaut werden.** Nach der
Erweiterung des Spielfelds wurden sie nur **hochskaliert**. Dadurch gibt es
Missionen mit langen Wartezeiten, weil Eskortziele jetzt viel weiter fliegen
müssen.

**Folge für die Arbeit:** Fehler in Missionen und Auftragsauswertung zu
beheben bringt derzeit wenig — diese Missionen verschwinden ohnehin. Vorrang
haben Fehler in der **Mechanik und Darstellung**, die den Neubau überleben.

Der Neubau selbst ist ein eigener, großer Punkt und noch nicht geplant.
Dabei zu bedenken: Flugzeiten und Wartezeiten gehören nicht hochskaliert,
sondern neu bemessen.

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
- **Status: ERLEDIGT.** Silvio auf v219: „Die schwarzen Rechtecke um
  Raketentrails und Explosionsgrafiken sind verschwunden."

### F2 — Subsystemnamen werden nicht immer angezeigt

**Befund (Silvio, 11.10.2026):** „Durch die Umstellung auf 3D Modelle werden
die Namen der Subsysteme auf Schiffen nicht immer angezeigt, wenn der Spieler
sich in deren Nähe befindet und darauf ausrichtet."

**Silvios Nachtrag (auf Nachfrage):** Es betrifft **alle** Großkampfschiffe
bzw. alle Schiffe mit angezeigten Subsystemen. „Nicht immer" bezog sich auf
die **Ausrichtung**: je nachdem, wie er stand, war der Name da oder nicht —
„ich musste raten, welche grüne Klammer auf dem Rumpf welches Subsystem
markiert."

**Ursache (nachgewiesen, nicht vermutet):** `drawSubsystems()` in
`40_world.js` zeigte **immer nur einen einzigen** Namen — das nächstgelegene
Subsystem, das zwei Bedingungen zugleich erfüllte:

- näher als `SUB_NAME_R = 120` **Welteinheiten**, und
- innerhalb eines Kegels von `SUB_NAME_CONE = 0.55` rad (±31°) um die
  Richtung, in die das Spielerschiff zeigt (`player.head`).

Der Kegel ist die Ausrichtungs-Abhängigkeit: ein paar Grad gedreht, und der
Name verschwand. Und die 120 waren ein **absoluter** Wert, der bei der
Feldvergrößerung nie mitskaliert wurde — beide Konstanten wurden nirgends mit
`FIELD_K` multipliziert. Auf einer Ravana (2346 Einheiten lang) liegen die
Subsysteme hunderte Einheiten auseinander, „näher als 120" heißt dort
praktisch „fast im Rumpf". Dass immer nur eines benannt wurde, ist der Rest
des Befunds: die übrigen Klammern blieben namenlos.

**Status: ERLEDIGT.** Silvio auf v220: „Werden korrekt angezeigt, sehe keine
Probleme mehr bei der Anzeige der Namen."

**Behoben in v218**, nach Silvios Wahl (Variante „Ziel immer benannt"):

- Das als Ziel gewählte Subsystem (Taste S, Shift+S, V) trägt seinen Namen
  **immer**, unabhängig von Entfernung und Ausrichtung.
- Zusätzlich benennt das **Zielkreuz**, worüber es steht — gemessen in
  Bildschirmpixeln (`SUB_NAME_PX = 70`) statt in Welteinheiten, damit es bei
  jeder Zoomstufe und jeder Feldgröße gleich wirkt. Der Kegel um die
  Schiffsnase ist weg.
- Die beiden alten Konstanten sind ersetzt, keine Reste im Code.

Neue Prüfung in `fieldsim.js` („M31 the picked subsystem keeps its name"):
das Schiff sieht weg, steht 600 Einheiten entfernt, der Zeiger in der Ecke —
nur die neue Regel kann dort einen Namen erzeugen. Gegen v217 gestellt: es
wird **gar kein** Name gezeichnet, die Prüfung fällt durch. Auf v218:
`"WEAPONS"` für das Ziel und `"WEAPONS,SENSORS"`, sobald das Zielkreuz über
der zweiten Klammer steht.

- Status: gebaut, wartet auf Silvios Test im Browser

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

**Silvios Nachtrag (er testet noch v216):** M23 und M27 zeigen dasselbe. In
M27 fliegt die Isis nach einigen Links-Rechts-Fahrten sogar **rückwärts nach
rechts**. Er vermutet, es betreffe weitere Missionen.

Beides bestätigt und von derselben Zeile erledigt:

- **M23** „The Pickup": Bast-Frachter mit `cross:0.34`, `dockTo:'C1'` —
  dieselbe Konstruktion wie M9.
- **M27** „The Repair": die Isis-Transporter haben `dockTo:'A1'` und **kein**
  eigenes `cross`, bekommen also den Vorgabewert `0.38` aus
  `30_waves.js:522` und laufen danach durch dieselbe Stelle. `trisis` ist
  Typ `transport`, der steht wie `freighter` in `CAP_VEL_TYPE`.
- **Das Rückwärtsfliegen** ist `capTurnStep` (`57_turrets.js:318`):
  `o.x += L.dir*v*0.3*c` mit `c = cos(π·p)`. In der zweiten Hälfte der Kehre
  wird `c` negativ — das Schiff gleitet rückwärts, während das Queren weiter
  nach rechts drückt.

Weil die Behebung in `capHolds()` sitzt — der einen Stelle, die entscheidet,
welche Schiffe sich selbst steuern — wirkt sie in **allen** Missionen
zugleich, nicht Mission für Mission.

- **Status: ERLEDIGT.** Silvio hat alle drei gemeldeten Missionen geprüft:
  M9 („Die Bast fliegen nicht mehr hin und her"), M23 („funktioniert, Bast
  drehen nicht mehr hin und her") und M27 („ebenfalls keine drehenden Isis
  mehr"). Damit ist auch das Rückwärtsfliegen der Isis weg, das dieselbe
  Ursache hatte.

  Auch in der Prüfung sichtbar: `warpsim` meldete für M23 auf v216
  `(wave did not end)` — die Welle endete nicht, weil die Frachter nie
  hinausquerten. Ab v217 endet sie.

### F4 — Halbtransparente Rechtecke am Anfang und Ende von Missionen

**Befund (Silvio, v216, mit Screenshot):** „In vielen Situationen anfangs und
am Ende einer Mission habe ich seit einigen Patches semitransparente
Rechtecke im Bild, die beim Übergang in eine neue Mission dann verschwinden
und deren Ursache ich nicht benennen kann."

Auf dem Screenshot: ein dunkelblaues, achsenparalleles Rechteck über der
Szene; die Sterne darin bleiben sichtbar, der rote Nebel darunter ist
abgedunkelt. Unten rechts steht das PAUSE-Fenster.

**Ursache (starker Verdacht, noch nicht gegengeprüft):** `W` und `H` sind
feste Werte — `10_core.js:29`: `const W=800,H=500`. Zehn Stellen legen damit
einen vollflächigen Schleier über das Bild:

```
20_render.js:133   thFrame      rgba(0,0,0,0.62)   der Schleier jedes Fensters
20_render.js:1116  Hintergrund  rgba(4,6,12,…)
20_render.js:904/922  drawSubspace
70_ui.js:25,198,202,471,3411,4152
```

`camScreen()` (`10_core.js:130`) setzt die Darstellung aber auf
`setTransform(RES_X, 0, 0, RES_Y, CAM_SHX*RES_X, CAM_SHY*RES_Y)` — seit dem
größeren Spielfeld also **skaliert und verschoben**. Ein Rechteck von fest
800×500 deckt den sichtbaren Bereich damit nicht mehr ab, sondern steht als
verschobenes Rechteck darin.

`70_ui.js:471` benutzt `rgba(0,0,8,0.50)`, ein dunkles Blauschwarz bei 50 % —
über einem roten Nebel ergibt das genau das Navy auf dem Screenshot.

Dass es am Anfang und Ende einer Mission auftritt, passt: dann gehen Fenster
auf, und beim Übergang schließen sie wieder.

**Diese Vermutung ist widerlegt.** Im Browser gemessen: `W×H` = 800×500,
Canvas = 1152×720, `RES` = 1,44, `CAM_SHX/CAM_SHY` = 0, und
`fillRect(0,0,W,H)` deckt nach `camScreen()` **1152×720 ab 0,0** ab, also den
ganzen Canvas. `applyResolution()` setzt den Canvas immer auf exakt
`W*RES_X × H*RES_Y`; die Ränder macht CSS. Auch `drawNebFit` ist sauber
(Cover-Zuschnitt, im Bildschirm-System gezeichnet).

**Silvios Nachtrag:** Die Rechtecke tauchen **beim Übergang in eine neue
Mission** auf und verschwinden, **sobald der Warp-In abgeschlossen ist**.
Direkt nach dem Startbildschirm. Er spielt im **Vollbild**. Er kann sich
nicht schnell genug bewegen, um zu sagen, ob es mit der Kamera wandert.

**Wo es jetzt steht:** `draw()` leert zu Beginn jedes Bildes bewusst den
Zustandsstapel (`for(let i = 0; i < 8; i++) ctx.restore();`) und setzt
`camScreen()` neu. Der Kommentar darüber beschreibt Silvios Symptom wörtlich:

> If the context is lost and restored, or if a frame throws between save and
> restore, that single setup is gone for good and every later frame draws
> unscaled into the top left corner while the clear below misses the rest of
> the buffer.

Gemessen: am Missionsanfang stehen 8 Ausschnitte (`clip`) und 8 `restore()`
je Bild — das ist genau dieses gewollte Leeren, **kein** Fehler. Kein Bild
hinterlässt in der Prüfumgebung einen Überhang.

Der Unterschied ist Silvios Umgebung: Vollbild, echte Grafikkarte, echtes 3D.
Beide im Kommentar genannten Auslöser — ein verlorener Grafikkontext, eine
Ausnahme mitten im Bild — lassen sich dort nicht erzeugen.

**Nächster Schritt:** Silvio schaut bei Auftreten in die Browser-Konsole
(F12, Reiter „Console") nach roten Fehlermeldungen. Eine Ausnahme mitten im
Bild wäre dort zu sehen und wäre die Ursache.

Unabhängig davon ist das Leeren auf feste 8 Stufen begrenzt; bleiben mehr
übrig, greift es nicht. Das zu härten ist billig, behebt aber nur dann
etwas, wenn der Überhang die Ursache ist — ungeprüft nicht bauen.

**Die Vermutung „F10 ist die Ursache" ist WIDERLEGT.** Silvio auf v220:
„Leider immer noch präsent" — und gleichzeitig keine Konsolenfehler mehr.
Der Absturz war es also nicht.

**Was aus seinen zwei Screenshots folgt:** Auf dem ersten sitzt das Rechteck
oben links, auf dem zweiten mitten im Bild, ohne offenes Fenster. Es ist also
**nicht am Bildrand verankert, sondern wandert** — das spricht dafür, dass es
in *Welt*-Koordinaten gezeichnet wird statt in Bildschirm-Koordinaten. Ein
`fillRect(0,0,W,H)` unter der Kamera-Transformation wäre ein Rechteck von
800×500 **Welteinheiten** am Weltursprung, das sich mit der Kamera bewegt.

**Bisher widerlegt:**
1. feste `W/H`-Schleier decken den Canvas nicht ab → gemessen, sie decken ihn
2. Stapel-Unwucht in `draw()` → das Leeren ist Absicht, kein Fehler
3. der `update()`-Absturz (F10) → behoben, Rechtecke bleiben

**Nächster Schritt:** beim **Wellenübergang** messen statt mitten im Spiel.
Genau dann tritt es auf, und genau dann wurde nie gemessen.

**GEFUNDEN — mit Silvios eigener Messung.** Er hat das Rechteck rot
markiert und mit `&diag=2` den Detektor mitlaufen lassen. Dessen Ausgabe,
in drei Bildern gleich:

```
fill 766,332  605x337  k0.76  rgba(6, 9, 20, 0.54)
fill 788,403  605x337  k0.76  rgba(6, 9, 20, 0.682)
fill 800,438  605x337  k0.76  rgba(6, 9, 20, 0.573)
```

- `k0.76` = seine `CAM.z` 0,35 × `RES` 2,16 → **unter der Kamera gezeichnet**
- `605x337` ÷ 0,756 = **800 × 446** = `W` × (`H` − `HUD_H`)
- Position wandert mit der Kamera, Größe nicht
- Farbe `rgba(6,9,20, …)` mit gerechneter Deckkraft

**Ursache:** `50_combat.js:699` in `drawJumpVortex()`:

```js
const k = jumpDark();
if(k>0){
  ctx.fillStyle='rgba(6,9,20,'+(k*0.92).toFixed(3)+')';
  ctx.fillRect(0,HUD_H,W,H-HUD_H);
}
```

Das ist die Abdunklung beim **Missionswechsel** („One darkness, sitting
exactly on the changeover"). `drawJumpVortex()` arbeitet absichtlich in
Weltkoordinaten — der Strudel sitzt an der Position des Spielerschiffs,
`ctx.translate(player.x, player.y)`. Diese eine Abdunklung gehört aber auf
den **Bildschirm**: sie soll alles Sichtbare verdunkeln, nicht ein 800×446
großes Stück Weltall.

**Behoben in v224:** die Abdunklung läuft jetzt in `ctx.save()` /
`camScreen()` / `ctx.restore()`.

Neue Prüfung in `fieldsim.js` („The changeover darkness covers the picture,
not a patch of world"). Gegen v223: Maßstab 0,5, Größe 403×225 — fällt
durch. Auf v224: Maßstab 1,44 (= `RES`) und 1152×642, volle Canvasbreite.

**Vorher widerlegt** (alle drei gemessen, nicht bloß verworfen):
1. feste `W/H`-Schleier decken den Canvas nicht ab → sie decken ihn
2. Stapel-Unwucht in `draw()` → das Leeren ist Absicht
3. der `update()`-Absturz (F10) → behoben, Rechtecke blieben

- **Status: ERLEDIGT.** Silvio auf v224: „Ich bestätige das Rechteck als
  behoben. Es tauchte in keiner der getesteten Missionen zum Missionsanfang
  mehr auf."

**Lehre für die nächste Suche:** Vier Erklärungen wurden aus dem Code
hergeleitet, alle plausibel, alle falsch. Gefunden hat es keine Lektüre,
sondern eine Messung **auf der Maschine, auf der der Fehler auftritt**.
Tritt ein Fehler in der Prüfumgebung nicht auf, ist das selbst der Befund —
dann gehört das Messwerkzeug ins Spiel (`&diag=1`, `&diag=2`), statt weiter
zu lesen.

### F5 — Das Sprungtor steht beim Auswarpen 180 Grad verkehrt

**Befund (Silvio, v216):** „Wenn Schiffe einwarpen, ist die Warpanimation
richtig herum, wenn sie herauswarpen ist sie um 180 Grad falsch herum."

Auf Rückfrage präzisiert: **Das Tor** steht verkehrt herum — das Schiff
fliegt richtig, mit der Nase voran, hinein, aber der Trichter öffnet sich in
die falsche Richtung.

Silvios eigene Deutung, die zutrifft: „Die Öffnung, die Schiffe ausspuckt,
ist auch die Öffnung, die sie wieder einsaugt." Das Tor hat keine Richtung,
die von der Flugrichtung abhängt.

**Ursache (nachgewiesen):** Beide Zeichenwege drehen das Tor nach der
**Nasenrichtung des Schiffes** (`fsNose`):

- Einwarpen: `20_render.js:516`, `ctx.rotate(Math.atan2(p.fy, p.fx))`
- Auswarpen: `drawOwnVortex` in `70_ui.js`, `ctx.rotate(Math.atan2(fg.fy, fg.fx))`

Das Tor steht aber auf verschiedenen Seiten des Schiffes — `fsWarp()` setzt
`const sg = out ? 1 : -1`, also davor beim Hinausfliegen, dahinter beim
Hereinkommen. Die Mündung muss **zum Schiff** zeigen: beim Einwarpen spuckt
sie es nach vorn aus (Mündung in Nasenrichtung, richtig), beim Auswarpen
verschluckt sie es (Mündung **entgegen** der Nase). Genommen wird aber beide
Male die Nasenrichtung.

`fsWarpClip()` kennt den Unterschied längst (`const sg = g.out ? -1 : 1`) —
deshalb fliegt das Schiff korrekt hinein, während nur der Trichter falsch
steht.

Sichtbar wird es erst durch den unsymmetrischen Inhalt: ein reines Oval sähe
um 180 Grad gedreht gleich aus. Seit v208 wird das MediaVP-Warpmodell in 3D
gezeichnet (`f3dWarp`), und das hat eine Vorder- und eine Rückseite.

**Warum keine Prüfstufe das fand:** `warpsim` prüft Zeitpunkte und
Bewegungsabläufe der Sprünge — ob etwas ruckt, zu früh schließt, die
Schnittebene nicht passt. Die **Blickrichtung** des Tors prüft es nicht.

- Behoben in: v219
- **Status: ERLEDIGT.** Silvio auf v220: „Ist jetzt richtig herum soweit ich
  überall sehen konnte."

### F6 — Ein Schiff in der Kehre warpt seitlich in den Strudel

**Befund (Silvio, schon in früheren Chats gemeldet):** „Wenn ein Schiff sich
gerade in einer Wende befindet und die Mission beendet ist, fliegt es
seitlich in den Warpstrudel."

Sein Vorschlag: entweder warten, bis die Wende vollzogen ist, und es erst
dann warpen lassen — und sicherstellen, dass es in die richtige Richtung
herauswarpt.

**Ursache (nachgewiesen):** Sobald `warpOut` gesetzt ist, greift im
Ablauf (`40_world.js`) wenige Zeilen weiter ein `continue`. Damit wird
`capLane()` nie wieder erreicht, und die Kehre **friert auf halbem Weg
ein**: `turnSq` hält den Rumpf quer gestaucht, während `fsNose()` das Tor
nach der Nasenrichtung setzt, die das Schiff **vor** der Kehre hatte. Es
gleitet seitlich in den eigenen Strudel.

**Warum nicht gewartet wird, wie Silvio vorschlug:** Eine Kehre dauert
`CAP_TURN_S × 60` Schritte — beim Zerstörer **540**. Der ganze Übergang ist
`TRANS_CLEAR + TRANS_OUT` = 80 + 140 = rund **220**. Auf die Kehre zu warten
hieße also meistens, dass das Schiff gar nicht mehr wegkommt und von der
nächsten Welle weggeräumt wird — schlimmer als der Fehler.

**Behoben in v227:** neue Funktion `capTurnSettle()` in `57_turrets.js`. Sie
löst die Kehre zu der Richtung auf, der das Schiff gerade **näher** ist:
`turnC` ist `cos(π·p)`, in der ersten Hälfte positiv (es zeigt noch
überwiegend in die alte Richtung, also bleibt es dabei), in der zweiten
negativ (es ist fast herum, also wird die Drehung vollendet, wie
`capTurnStep` es getan hätte). So oder so wird es ganz gezeichnet, zeigt in
eine wirkliche Richtung, und das Tor wird danach gesetzt.

Aufgerufen an **zwei** Stellen, damit keine Sprungart ausgelassen wird:
`40_world.js:2245` (Verbündete) und `:2361` (gegnerische Großkampfschiffe).
Die übrigen vier Auswarp-Stellen betreffen Jäger und Frachter, die keine
Bahn fahren.

Neue Prüfung in `fieldsim.js` („A ship caught mid-turn settles before she
jumps out") mit beiden Hälften: kurz vor der Mitte behält das Schiff seine
Richtung, kurz dahinter vollendet es die Drehung und die Bahn dreht mit.
Gegen v226: vier von fünf fallen durch. Auf v227: alle grün.

**Nachtrag v231 (Silvio auf v230):** „Das Schiff snapt auf der Stelle in die
Warp-Richtung ohne langsame Bewegung."

Das ist richtig und war mein Fehler: `capTurnSettle()` loeste die Kehre in
**einem einzigen Bild** auf. Die Richtung stimmte danach, das Tor stand
richtig — aber der Weg dorthin fehlte.

**Behoben in v231.** Die Kehre wird jetzt **ueber die Schritte des Sprungs
abgefahren**, nicht in einem Bild aufgelöst:

- Die **Richtung** wird weiterhin sofort entschieden (ein einziges Mal, im
  ersten Bild des Sprungs). Das muss so sein: `fsWarp()` legt Ort und
  Richtung des Tors im **ersten** Tick fest (`_fsG`), und ein Tor, das einer
  Richtung nachläuft, die das Schiff noch nicht hat, ist genau der
  ursprüngliche Fehler.
- Ist sie über die Hälfte, wird sie wie bisher gewendet (`flip`), und die
  **restliche Kehre wird mit ihr gespiegelt**: `T.p` wird zu `1 - T.p`. Das
  ergibt dasselbe Bild — ein gewendeter Rumpf mit `+|c|` sieht aus wie ein
  ungewendeter mit `-|c|` —, nur liegt die Kehre danach in ihrer ersten
  Hälfte und läuft von dort auf Null aus.
- Diese Restkehre wird über die **halbe Sprungdauer** abgefahren
  (`warpOut/2`, beim Zerstörer 80 Schritte, 1,3 s). Sie dreht damit schneller
  als im Flug, aber **sichtbar und zusammenhängend**, und steht lange vor dem
  Verschwinden ganz.

Die Prüfung misst jetzt die **größte Änderung von `turnSq` je Schritt**.
Gegen v230 (Sprung von der Stauchung direkt auf den ganzen Rumpf): fällt
durch. Auf v231: unter 0,05 je Schritt.

- Status: gebaut, wartet auf Silvios Test im Browser

### F7 — Sentryguns haben keine Markierung

**Befund (Silvio, schon in früheren Chats gemeldet):** „Sentryguns haben
keine Markierung um sich herum wie sie bspw. gegnerische Jäger und Bomber
haben. Sie haben nur dann eine Markierung, wenn sie als Ziel aufgeschaltet
wurden."

**Ursache (nachgewiesen):** `drawHostileMark()` in `70_ui.js` stieg in der
zweiten Zeile aus:

```js
if(e.type!=='fighter' && e.type!=='bomber') return;
```

Sentryguns haben `type === 'sentry'` und fielen damit heraus. Aufgeschaltet
bekamen sie eine Markierung, weil die aus `drawTargetMarks()` kommt — ein
anderer Weg.

**Behoben in v226:** `'sentry'` steht jetzt mit in der Liste. Großkampf-
schiffe bleiben bewusst draußen — die sind groß genug, um sie ohne Hilfe zu
finden.

Neue Prüfung in `fieldsim.js` („A sentry gun is bracketed like a fighter")
mit zwei Gegenproben: ein Jäger bekommt Winkel (der bekannte gute Fall), ein
**verbündetes** Schiff bekommt keine. Gegen v225: Sentry fällt durch, die
beiden anderen bestehen. Auf v226: alle drei grün.

- Status: gebaut, wartet auf Silvios Test im Browser

### F8 — M9: die Aten entkommt, wird aber als Fehlschlag gewertet

**Befund (Silvio, v219):** „In M9 entkommt die Aten erfolgreich, wird aber
als Fehlschlag gewertet, vermutlich, weil ich die beiden Bast zuvor verloren
habe."

**Ursache (nachgewiesen):** Es gibt **zwei** Wege, auf denen ein beschütztes
Schiff das Feld verlässt:

- `cross:` — eine Geschwindigkeit, abgewickelt in `tickCrossGuards()`
  (`30_waves.js:1053`): dort steht `crossDone++; if(!a.emptyRun) protSaved++;`
- `crossSecs:` — eine Uhr, abgewickelt über den `transit`-Weg in
  `updateAllies()` (`40_world.js:2273`): dort wurden `EV_LEFT` und
  `guardGone` gesetzt, **aber `protSaved` nicht**.

Die Aten in M9 hat `crossSecs:75`, läuft also über den zweiten Weg. Ihr
Entkommen zählte für niemanden. Die Anzeige liest aber genau diesen Wert:
`objFailed = guardLost`, und dann

```js
if(objFailed && protSaved>0)
  objAnnounce('PARTIAL SUCCESS', protSaved+' OF '+(protSaved+protLost)+' GOT THROUGH');
else objAnnounce('OBJECTIVE FAILED', …);
```

Mit beiden verlorenen Bast war `protLost` 2 und `protSaved` 0 — also
„OBJECTIVE FAILED" statt „PARTIAL SUCCESS — 1 OF 3 GOT THROUGH". Und die
Zahlen hatten die Aten in keiner von beiden.

Betrifft sechs weitere Missionen mit `crossSecs` (M25, M26, M30, M35, M45,
M50).

**Behoben in v225:** der `transit`-Weg zählt sie jetzt mit, über dieselbe
Markierung `protCounted`, die der Verlustweg benutzt — damit kann ein Schiff
weder doppelt noch auf beiden Seiten gezählt werden.

**Vorher geprüft, ob das Auslöser verschiebt:** `gerettet` (liest
`protSaved`) steht nur in M54 und M66, beide benutzen `cross:`, nicht
`crossSecs:`. Ebenso der Platzhalter `{saved}` (nur M54). Keine der sechs
`crossSecs`-Missionen hat einen solchen Auslöser.

Neue Prüfung in `fieldsim.js` („M09 a guard that crosses on a clock counts
as one who got through"). Gegen v224: `protSaved` bleibt 0 — fällt durch.
Auf v225: geht auf 1 und bleibt dort. In beiden Fällen legt die Aten ihren
Sprung ein, der Unterschied ist allein die Zählung.

**Was sich dadurch NICHT ändert:** Zwei verlorene Frachter bleiben ein
Verlust. Die Mission zeigt jetzt „PARTIAL SUCCESS — 1 OF 3 GOT THROUGH"
statt „OBJECTIVE FAILED". Wenn Silvio etwas anderes erwartet, ist das eine
Spielentscheidung und keine Fehlerbehebung.

**Nachtrag v231 (Silvio auf v230):** „Gilt weiterhin als Fehlschlag, aber ist
irrelevant."

Also **offen und zurückgestellt**, auf Silvios eigene Einordnung. Die Zählung
ist behoben; was M9 am Ende anzeigt, ist eine Missionsfrage, und die
Missionen werden neu gebaut (siehe „Wichtig für die Reihenfolge" oben).
Nicht weiter untersucht, bis die Missionen dran sind.

- Status: zurückgestellt (Silvio: irrelevant)

### F9 — Bildschirm flackert auch ohne Treffer

**Befund (Silvio, schon früher gemeldet):** „Selbst wenn ich keine Treffer
abbekomme, habe ich ein Flackern des Bildschirms." Sein Rat: „dieses
Flackern oder Aufleuchten ganz raus zu nehmen."

**Ursache (nachgewiesen):** `hullHit()` und `shieldHit()` in `60_effects.js`
machten zwei Dinge auf einmal — die Funken an der Trefferstelle **und** ein
vollflächiges Aufleuchten (`hullFlash = 7`, `shieldFlash = 8`). Die Funken
werden überall gebraucht, wo etwas getroffen wird: ein Gegner, ein rammender
Asteroid, der Spieler. Also leuchtete der Bildschirm auf, wenn Silvio
**traf** — nicht nur, wenn er getroffen wurde.

Auf die Frage, ob das Aufleuchten für eigene Treffer erhalten bleiben soll,
entschied er: ganz raus.

**Behoben in v221:** beide vollflächigen Aufheller entfernt, keine Reste im
Code. Was einen Treffer weiterhin zeigt: die Balken oben, die Funken an der
Trefferstelle, und das Schildaufleuchten am eigenen Rumpf (`player.shHit`,
etwas anderes, unangetastet).

- **Status: ERLEDIGT.** Silvio auf v224: „Ist auch erfolgreich behoben,
  bzw. endlich raus."

### F10 — `update()` stürzt ab, sobald der Spieler mit Geschossen im Feld stirbt

**Befund (Silvio, v219, Browser-Konsole, 532 Fehler):**

```
Update error: TypeError: Cannot read properties of undefined (reading 'hom')
    at update (...)
    at stepUpdate (...)
    at loop (...)
```

**Ursache (nachgewiesen):** `60_effects.js:1126` läuft über die
Gegnergeschosse:

```js
for(let i=eBullets.length-1;i>=0;i--){
  const b=eBullets[i];
  if(b.hom){
```

In derselben Schleife steht bei `60_effects.js:1268`:

```js
eBullets.splice(i,1); if(player.hp<=0) playerDie();
```

und `playerDie()` setzt bei `60_effects.js:676` **`eBullets=[]`** — ein
*neues*, leeres Array. Die Schleife läuft mit ihrem alten Zähler weiter,
liest aus dem neuen Array ins Leere, `b` ist `undefined`, und `b.hom` wirft.
Dasselbe gilt für `30_waves.js:3799` (`eBullets.length = 0` beim verpassten
Lucifer-Sprung).

Es trifft also **jeden Tod, bei dem noch Geschosse unterwegs sind** — und
das ist der Normalfall.

**Zusammenhang mit F4:** `update()` bricht dadurch mitten im Bild ab. Der
Kommentar über dem Stapel-Leeren in `draw()` nennt genau das als Auslöser:
„if a frame throws between save and restore … every later frame draws
unscaled into the top left corner while the clear below misses the rest of
the buffer." Das ist Silvios Rechteck.

Nicht von den Änderungen in v217–v219 verursacht — die Schleife und
`playerDie()` sind älter.

- Behoben in: v220
- **Status: ERLEDIGT.** Silvio auf v220: „Bisher keine neue Fehlermeldung in
  der Console gehabt."

### F11 — Hintergründe sehen hochskaliert matschig aus

**Befund (Silvio, v226):** „Durch das Hochskalieren des Spielfeldes wurden
auch die Hintergründe hochskaliert, was sie jetzt leider recht unansehnlich
und matschig macht."

**Zahlen dazu stehen schon fest**, aus Silvios eigener Diagnose-Tafel
(`&diag=1`) auf seinem Vollbild:

```
canvas  1728x1080
neb     cur Aldebaran 900x450   nxt AlphaCentauri 900x450
```

Die Nebelbilder sind also **900×450** und werden von `drawNebFit()` mit
einem Cover-Zuschnitt auf 1728×1080 gezogen — knapp **das Doppelte** in
jeder Richtung. Das ist die Matschigkeit, und sie ist kein Darstellungs-
fehler, sondern schlicht zu wenig Bildmaterial.

**Die Obergrenze steht im Code fest:** `W=800, H=500`, die höchste
Auflösungsstufe ist `ECO_RES_STEPS[0] = 3`, und `drawNebFit` zieht das Bild
über die **Höhe**. Mehr als `500 × 3 = 1500` Pixel Höhe kann das Spiel nie
zeigen — bei 2:1 also **3000×1500**. Alles darüber ist verschenkt.

**Behoben in v229.** Silvio hat zwölf neue Hintergründe in 3000×1500 geliefert
(`nebulae/neb_<Name>.png`, zusammen 33 MB). Umgestellt auf Auslieferung als
Dateien, wie Musik und 3D-Modelle es schon tun:

- `NEB_DATA` enthält Adressen statt `@@FS3_ASSET@@`-Token — der Packer
  bettet also nichts mehr ein, `game.html` bleibt bei 28,8 MB
- `build.sh` kopiert `nebulae/` nach `/var/www/html/fs3/nebulae/`
- `NEB_NAMES` kennt die zwölf Namen (neu: Antares, darkspace, Fomalhaut)
- **Geladen wird bei Bedarf**, nicht alles auf einmal: ein Bild dieser Größe
  belegt entpackt rund **18 MB Arbeitsspeicher**, zwölf also über 200 MB für
  elf, die niemand ansieht. Gehalten werden nur das gezeigte und das, auf das
  gerade überblendet wird (`nebLoad`, `nebDropOthers`)
- Die Ladeanzeige wartet nur noch auf die Sprites

**Achtung, das hätte den Bau angehalten:** `inline_assets()` im Packer bricht
hart ab, wenn eine Bilddatei fehlt. Silvio hatte die alten neun gelöscht, die
Token standen aber noch im Code — der nächste `build.sh` wäre mit „Abbruch:
Bilddatei fehlt: nebulae/Aldebaran.jpg" gescheitert.

**Noch offen, Silvios Entscheidung:** Die Dateien sind PNG. Für Fotografisches
ist das verlustfrei und damit groß — als JPEG bei Qualität 85 wären es rund
**8 MB statt 33**, also 650 KB statt 2,75 MB je Welle, ohne sichtbaren
Unterschied bei einem Nebel. Es funktioniert so wie es ist; es ist nur viermal
mehr Verkehr als nötig.

**Nachtrag v230 (Silvio auf v229):** „Die PNG-Hintergründe laden problemlos,
nur zu schnell, denn die werden schon getauscht noch bevor der Bildschirm
beim Sprung zur nächsten Mission komplett verdunkelt wurde."

Das war mein Entwurfsfehler: `nebLoad(nebNxt)` stand **in** `startNebFade()`,
der Download von 2,75 MB begann also genau mit der Überblendung und kam
mitten in der Blende an — im noch hellen Bild. Jetzt wird der nächste
Hintergrund **eine ganze Welle im Voraus** gewählt und geladen
(`nebPickNext`), und `startNebFade()` beginnt **gar nicht**, wenn er noch
nicht da ist: dann behält die Welle ihren Himmel und gewechselt wird eine
Welle später. Ein Hintergrund, der mitten in der Blende im Hellen auftaucht,
ist schlimmer als einer, der später wechselt.

**Dabei beinahe eine Prüfung entwertet:** In der Prüfumgebung gibt es keine
Nebeldateien, also hätte die neue Sperre dort **jede** Überblendung
verhindert — und die Prüfung „Knossos scene: same sky within a run" wäre
trivial grün geworden, ohne noch etwas zu prüfen. `fieldsim` legt jetzt
Ersatz-Hintergründe an, so wie es das für Planeten schon tut.

**Nachtrag v231 (Silvio auf v230):** „Wechseln immer noch bevor der
Bildschirm verdunkelt wurde."

**Damit war meine Ursache falsch.** Das Vorladen war richtig, aber nicht das
Problem. Nachgemessen am Code, nicht vermutet:

- Die Überblendung startet bei `waveCd < TRANS_OUT*0.45`, also bei
  `waveCd = 62`. Die Schwärzung dort: `jumpDark()` gibt
  `(0.557-0.55)/0.45 = 0.016` — **1,6 %**. Der Bildschirm ist also praktisch
  **voll hell**, wenn die Blende anspringt.
- Die Überblendung dauert `1/0.0084 = 120` Schritte. In der Mitte davon
  (`waveCd ≈ 30`) ist der Bildschirm zu **52 %** verdunkelt und der neue
  Himmel bereits mit **27 %** darüber. Genau das sieht Silvio.
- Der Kommentar in der Quelle („das dunkle Fenster ist 121 Schritte breit")
  zählte das Fenster, in dem die Schwärzung **größer als Null** ist. Das ist
  nicht dasselbe wie dunkel. Über **80 %** verdunkelt ist nur ein Fenster von
  rund **25 Schritten** (0,4 s) um den Scheitel.

**Behoben in v231 — mit dem Verfahren, das für die Planeten längst dasteht.**
`drawBodies()` hat genau dieses Problem schon gelöst: „Die verbleibenden 8 %,
die die Blende offen lässt, würden den Wechsel immer noch durchblitzen
lassen. Also gehen die Körper mit der Blende ganz weg und kommen dahinter
neu wieder." Der Hintergrund macht es jetzt ebenso:

- `drawNebula()` zeichnet den Himmel mit `1 - jumpDark()`. Im Scheitel ist er
  damit **ganz weg** — der Bildschirm wird wirklich schwarz, wie Silvio es
  erwartet, und nicht nur zu 92 %.
- Der Wechsel ist **ein harter Schnitt im Scheitel**, in `nextWave()`, direkt
  neben `rollBodies()`, das dort aus demselben Grund steht. Keine
  Überblendung mehr: `NEB_FADE_SPEED`, `nebAlpha` und `nebFading` fallen weg.
- Das Vorladen aus v230 bleibt. Ist der nächste Himmel noch nicht da, behält
  die Welle ihren.

- Status: gebaut, wartet auf Silvios Test im Browser

### F12 — Die MediaVP-Explosionen sind veraltet

**Befund (Silvio, v226):** „Die Explosionseffekte aus den MediaVPs … werden
nicht durch das Spielfeld hochskaliert, sondern sind einfach seit Jahren vom
FSO-Team nicht mehr aktualisiert worden, weshalb sie leider auch nicht mehr
sonderlich schön und modern aussehen. Ein Zerstörer explodiert zum Beispiel
auch sehr matschig."

**Ein anderer Fall als F11**, ausdrücklich: hier skaliert nicht das
Spielfeld, hier ist das Ausgangsmaterial alt.

Was im Spiel steckt (`src/63_fxanim.js`): `exp05` 47 Bilder à 128 px,
`exp20` 38 Bilder à 128 px, `smoke` 18 Bilder à 128 px.

**Ursache (nachgemessen):** Die Nachzünder entlang des Rumpfes sind
**5–9 %** der Rumpflänge (`H.L*rnd(0.05, 0.09)`) — die sind scharf. Der
Abschluss war **eine** Explosion über **115 %**:

```js
fxFire('exp20', e.x, e.y, e.L*1.15, 210);
```

Eine 128-px-Zelle auf die volle Länge eines Zerstörers. Genau der eine
Bildteil, den Silvio als matschig sieht.

**Silvios Vorschlag** — mit dem vorhandenen Material mehrere kleinere
Explosionen auf dem Rumpf verteilen — trifft die Sache, und die Maschinerie
dafür stand schon (`fxOnHull`, von den Nachzündern benutzt).

**Behoben in v228:** Der Abschluss besteht jetzt aus **fünf** Explosionen zu
je 30–40 % der Rumpflänge, entlang des Rumpfes verteilt, plus drei kleineren
für die Übergänge. Zusammen decken sie die Länge weiterhin ab, aber keine
Zelle wird mehr als etwa ein Drittel so weit gezogen wie vorher.
`scheduleExpl` trägt dafür die Rumpfachse mit (`H`) — beim Abschluss ist das
Schiff nicht mehr da, um sie zu erfragen.

**Blitz und Ring bleiben groß.** Sie werden gezeichnet, nicht aus Bildern
gezogen, skalieren also verlustfrei und tragen den „großen" Eindruck.

Neue Prüfung in `fieldsim.js`. Gegen v227: eine Explosion, 1,15 der
Rumpflänge — fällt durch. Auf v228: fünf, größte 0,40.

**Nachtrag v231 (Silvio auf v230):** „Bei der Explosion von Zerstörern kommt
am Schluss immer noch eine große Explosionsflamme, die leider sehr verwaschen
aussieht aufgrund der Größe." Auf die Frage, ob es eine weiche Leuchtkugel
oder vergrößerte Bildstruktur sei: **„vergrößerte Bildstruktur."**

**Damit ist es das Bildmaterial, und die Prüfung maß das Falsche.** Sie
rechnete in **Anteilen der Rumpflänge** („keine über 0,5") — aber ob eine
Zelle verwaschen aussieht, hängt nicht am Rumpf, sondern daran, auf wie viele
**Bildschirmpunkte** ihre 128 px gezogen werden. Nachgerechnet mit Silvios
eigenen Zahlen (`canvas 1728x1080`, also `RES 2.16`, `CAM.z 0.35`):

| | Weltbreite | Bildschirm | Zelle 128 px |
|---|---|---|---|
| Rumpf eines Orion | 1643 | 1242 px | — |
| Nachzünder (Radius 0,07 · 2,6) | 299 | 226 px | 1,8× |
| Feuerball des Abschlusses | 512 | 387 px | 3,0× |
| Abschluss v228 (0,35 der Länge) | 575 | 435 px | **3,4× — vergrößert** |
| Abschluss v216 (1,15 der Länge) | 1889 | 1428 px | 11,2× |

(Die Nachzünder bekommen ihren Radius mit `FX_FB_K = 2,6` auf einen
Durchmesser gebracht, deshalb stehen sie höher, als ihr Anteil an der Länge
vermuten lässt.)

v228 hat also von 11× auf 3,4× verbessert und damit einen guten Teil des
Weges gemacht, aber nicht genug: scharf ist erst **1,0×**, und das sind beim
Orion **10 %** seiner Länge.

**Behoben in v231.** Die Größe einer Zelle wird nicht mehr am Rumpf
bemessen, sondern am Bildschirm. Neu `fxCellWorld(sheet)` in
`63_fxanim.js`: wie breit eine Zelle in Welteinheiten sein darf, damit sie
nicht vergrößert wird — `Zelle / (CAM.z · RES_X)`. Auf Silvios Bildschirm
sind das **169** Welteinheiten.

Zwei Dinge daraus:

1. **Die Grenze gilt an einer Stelle für alles.** `fxFire()` begrenzt jede
   Bildfolge auf ihre eigene Zelle. Dort und nicht bei jedem Aufrufer, damit
   keiner vergessen werden kann. Blitz und Ring kommen aus keiner Bildfolge
   und bleiben unverändert groß — sie werden gezeichnet und tragen den
   „großen" Eindruck.
2. **Der Abschluss braucht entsprechend mehr Stücke.** Nicht mehr fünf zu je
   einem Drittel, sondern so viele, wie ihre Länge bei einer Zelle Breite
   braucht: beim Orion **neun**, beim Kreuzer weiterhin fünf (dort war die
   Zelle nie die Grenze, höchstens ein Drittel der Länge).

**Was sich dadurch noch ändert, und das soll Silvio wissen:** Die Grenze in
`fxFire()` fasst auch die **Nachzünder** und den **Feuerball** des
Abschlusses an. Nachgemessen auf seinem Bildschirm: Nachzünder lagen bei
**1,3 bis 2,3** Zellen (ihr Radius wird mit `FX_FB_K = 2,6` auf einen
Durchmesser gebracht — das hatte ich oben in der Tabelle noch zu klein
gerechnet), der Feuerball des Abschlusses bei **2,0**. Sie werden jetzt auf
eine Zelle begrenzt, sind also **schärfer und kleiner als vorher**. Wenn
Silvio sie lieber groß hätte, auch wenn sie dann weich aussehen, ist das eine
Zeile zurück.

Die Prüfung misst jetzt in **Bildschirmpunkten je Zelle** statt in Anteilen
der Rumpflänge, an einem **echten** Zerstörerrumpf (1643 Einheiten) statt am
Notwert 340 — und sie liest die Größen **aus der Zeichenliste**, nicht aus
den Aufrufen. Was ein Aufrufer verlangt und was gezeichnet wird, sind seit
der Grenze zwei verschiedene Zahlen. Gegen v230: 2,56 Zellen — fällt durch.
Auf v231: 1,00.

- Status: gebaut, wartet auf Silvios Test im Browser

### F13 — M68: nach dem Verlust der Setekh endet die Mission nie

**Befund (Silvio, v231):** „Ein Hinweis zu einer der Missionen, ich glaube es
ist M68, oder auf jeden Fall die Mission mit der Setekh, diese ist verbuggt,
denn wenn die Setekh zerstört wird, hören die gegnerischen Wellen niemals
auf, weil es kein Missionsende gibt."

**Es ist M68 „Radio Silence"** — die zweite Setekh-Mission ist M79 „Data
Uplink", und die ist in Ordnung (sie hat `{t:'vernichtet', a:'C1',
w:'abzug'}`, also ein Ende für den Verlustfall).

**Ursache (nachgewiesen):** Nicht die Missionsdaten allein, sondern ein
allgemeiner Mechanikfehler, der jede Mission treffen kann.

M68 hat genau **einen** Weg, den Nachschub wieder abzuschalten:

```js
{t:'alleZerstoert', a:'K1+K2+M1+E1+B1', w:'nachschub', a2:'aus', lostMax:0},
{t:'alleZerstoert', a:'K1+K2+M1+E1+B1', w:'abzug',     a2:'',    lostMax:0},
```

`lostMax` prüft in `tickEvents()`:

```js
if(ev.lostMax!=null && protLost > ev.lostMax) continue;
```

Die Setekh trägt `guard:true`, ist also ein beschütztes Schiff. Geht sie
verloren, steht `protLost` auf 1 — und damit sind **alle drei** Ereignisse
mit `lostMax:0` für den Rest der Mission gesperrt. Der Nachschub bleibt
ewig an, und `o:'clear'` wartet auf ein leeres Feld, das praktisch nie
eintritt.

**Genau genommen** endet die Welle, wenn das Feld einen einzigen Augenblick
leer ist — abschalten muss den Nachschub dafür niemand. Nur kommt dieser
Augenblick bei laufendem Nachschub praktisch nicht, weil die nächste Staffel
da ist, bevor die letzte weg ist. **Deshalb hat es auch keine Prüfung
gesehen:** die Prüfumgebung schießt alles in jedem Schritt ab und trifft
diesen Augenblick, ein Spieler nicht. Die neue Prüfung greift deshalb den
Nachschub selbst, nicht das Wellenende.

**Der Sinn von `lostMax` ist ein anderer**, er steht als Kommentar daneben:
„a success card must not follow a failure (M65)" — eine **Erfolgsmeldung**
soll nicht nach einem Fehlschlag kommen. Es soll nicht das Missionsende
blockieren. Die Sperre gilt jetzt nur noch für die Meldungen
(`zielerfuellt`, `meldung`) und nicht mehr für die Wirkungen, die eine Welle
beenden (`nachschub`, `abzug`, `raus`).

**Behoben in v232.** Eine Stelle, und sie gilt für alle Missionen — auch für
die, die noch gebaut werden. Nachgesehen, wer sonst betroffen war: **M63**
(`raus`), **M65** (`abzug`), **M68** (`nachschub`, `abzug`), **M69**
(`raus`, `abzug`), **M79** (`raus`, `abzug`), **M80** (`raus`, `nachschub`,
`abzug`). In M79 und M80 gibt es noch einen anderen Weg zum Ende, in M68
nicht — deshalb fällt es dort auf.

**Was dadurch in M68 passiert:** Der Nachschub nach ihrem Verlust bleibt —
das ist Absicht und wird auch geprüft („then the Shivans call for help
again"). Aber der Weg heraus steht wieder offen: wer die Patrouille
(K1, K2, M1) niederkämpft, schaltet den Nachschub ab und die Mission endet —
mit verfehltem Auftrag, denn die Setekh ist verloren. Kein Erfolgskärtchen.

**Offene Spielentscheidung für Silvio:** M79 macht es anders — dort ist die
Mission in dem Moment vorbei, in dem die Setekh stirbt (`abzug`). Soll M68
das auch so halten, statt dich herauskämpfen zu lassen? Das ist eine
Designfrage, keine Fehlerbehebung, und deshalb nicht mitgebaut.

- Status: gebaut, wartet auf Silvios Test im Browser

### F14 — Das Knossos-Portal rotiert in die falsche Richtung

**Befund (Silvio, v231):** „Das Knossos-Portal rotiert in die falsche
Richtung."

**Präzisierung (Silvio, v232):** „Es geht um das Modell, nicht die
Warp-Animation darin. Das Modell besteht aus zwei Ringen, die sich aus
einzelnen voneinander getrennten Elementen bilden. Der äußere Elemente-Ring
rotiert in die eine Richtung, der innere in die entgegengesetzte Richtung. In
FS3 drehen beide in die jeweils falsche Richtung, was vermutlich eine
fehlerhafte Interpretation aus dem Lesen der Modelleigenschaften ist.

**Ursache (so weit sie von hier aus nachweisbar ist):** Die drehenden Teile
eines Modells sind Knoten der Art `rot` in `f3dNodeMats()`
(`59_field3d.js`), und ihr Winkel lief:

```js
ang = (2*Math.PI*now/(nd.t || 20)) % (2*Math.PI);
```

Immer positiv, für **jedes** drehende Teil jedes Modells. Dass die beiden
Ringe des Knossos trotzdem gegeneinander laufen, heißt: die Richtung je Teil
kommt sehr wohl aus den Modelldaten — sie steckt in der Achse oder im
Vorzeichen der Umlaufzeit. Falsch ist also nicht der Unterschied zwischen
den Ringen, sondern **der Drehsinn um die Achse, und zwar bei allen Teilen
gleichzeitig.** Genau das sagt Silvios „beide in die jeweils falsche
Richtung".

**Nachgerechnet, dass es nicht die Darstellung ist:** `f3dMat()` ist
`verschieben × rotZ × rotY × skalieren` mit **positivem** Faktor, die
Determinante also `s³ > 0` — keine Spiegelung. Und ein gewendeter Rumpf wird
um 180 Grad gedreht, nicht gespiegelt. Eine Umkehrung, die das ganze Modell
betrifft, kann dann nur aus dem Lesen der Modelldaten kommen. Da, wo Silvio
sie vermutet hat.

**Behoben in v232:** ein Minuszeichen, mit der Begründung im Quelltext.
**Es betrifft alle drehenden Teile**, nicht nur das Knossos — die drehenden
Schüsseln der Gasminen (`gmrahu`, `gmanuket`) zum Beispiel. Die liefen unter
derselben Regel und drehen jetzt ebenfalls herum. **Silvio sollte beim Test
auch darauf schauen.**

Neue Prüfung in `fieldsim.js` („A rotating part of a model turns one way, and
the other one back"). Die Modelldateien liegen auf dem Server, nicht im Repo
— geprüft wird deshalb an einem **Ersatzknoten**, und gemessen wird in einem
festen Bezug (um +z), nicht um die eigene Achse des Teils: um die eigene
Achse dreht jedes Teil per Konstruktion gleich, das sagt nichts. Gegen v232
vor der Änderung: Drehsinn +1, fällt durch. Danach: −1. Zweite Zusicherung:
ein Teil mit umgekehrter Achse dreht weiterhin dagegen — die Ringe laufen
also weiter gegeneinander.

**Was die Prüfung nicht kann:** beweisen, welche Richtung die richtige ist.
Das ist Silvios Aussage. Sie hält die Richtung nur fest, damit sie nicht
unbemerkt zurückkippt.

### Dazu Silvios zweite Anmerkung: der türkise Strudel

„Im Knossos-Portal ist der Warpstrudel nicht blau, sondern türkis. … Ob
deine Änderung an der Richtung … bei herauswarpenden Schiffen auch für den
türkisen Knossos-Warpstrudel übernommen wurde, weiß ich aber nicht."

**Nachgesehen und nachgemessen: ja.** Es ist **ein** Weg, keine zwei.
`drawOwnVortex()` (`70_ui.js:4405–4414`) berechnet die Richtung der
Trichtermündung (`mx, my`) und gibt die Farbe als Flagge daneben mit:
`warpTurquoise(e)` an `f3dWarp()` und an `drawWarpFrame()`. Türkis ist also
nur ein anderes Bildblatt an derselben Geometrie — die Richtung aus F5 gilt
für beide.

`warpTurquoise()` (`20_render.js:571`) liest beim Hinausspringen
`e.portalOut`, und das setzt `30_waves.js:1017` für jedes Schiff, das in
einer Portalmission rechts hinausfliegt. Ein Schiff, das durchs Portal
hereinkam und **irgendwo anders** hinausspringt, bekommt bewusst den
normalen blauen Strudel (steht als Kommentar daneben, Silvios Befund aus
v173 zur Rakshasa in M61).

Die Prüfung „M31 the vortex she leaves through faces her" hat jetzt zwei
Zusicherungen mehr: durchs Portal ist das Blatt das türkise, **und** die
Mündung schaut auch dort um 180 Grad zurück auf das Schiff.

- Status: gebaut, wartet auf Silvios Test im Browser

### F15 — Das Radar in der Leiste zeigt nicht das ganze Spielfeld

**Befund (Silvio, v232):** „Ich hab übrigens noch einen Fehler beim Radar
oben in der Leiste entdeckt. Das Radar zeigt scheinbar nur den gerade auf dem
Bildschirm sichtbaren Bildausschnitt und nicht das tatsächliche Spielfeld, was
zu seltsamen Anzeigen der Radar-Icons führt."

**Im Code nachgelesen — der Befund stimmt, die Erklärung nicht ganz.** Das
Radar hängt **nicht** an der Kamera: `drawBarRadar()` (`72_target.js:332`)
rechnet ausdrücklich

```js
const ax0 = 0, ax1 = MW, ay0 = HUD_H, ay1 = MH;
```

also das **Missionsgebiet**, nicht den Bildausschnitt. `CAM` kommt in der
ganzen Funktion nicht vor. Was er sieht, hat eine andere Ursache — und sie
führt zum selben Eindruck:

**Die Welt ist größer als das Missionsgebiet, und alles außerhalb wird auf den
Rand geklemmt.** `worldSet()` (`10_core.js:165`) legt beides an:

| | Breite | Höhe |
|---|---|---|
| Missionsgebiet (was das Radar zeigt) | `MW` = 800·K | `MH − HUD_H` = 500·K − 54 |
| Welt (wo Schiffe fliegen) | mindestens `MW + 300·K` | mindestens `MH + 200·K − HUD_H` |

Bei `FIELD_K = 4` also **3200 × 1946** gezeigt gegen mindestens
**4400 × 2746** geflogen. Rund ein Viertel der Breite und zwei Fünftel der
Höhe liegen außerhalb des Radars — und `drawBarRadar` klemmt sie mit
`Math.max(ax0, Math.min(ax1, v))` auf die Kante. Dort sammeln sie sich.

Dazu kommt, dass die Welt noch viel weiter reicht, wenn ein sehr langes Schiff
dazukommen kann (`need`): beim Colossus wird sie breiter als das
Missionsgebiet mal zwei.

**Zweiter Beitrag: die Symbole sind groß im Verhältnis zum Kasten.** Der
Radarkasten ist etwa 74 × 44 Bildpunkte; ein Großkampfschiff-Symbol ist bei
`RADAR_ICO_K = 0.36` rund 11 Punkte breit, das des Colossus 23. Mehrere
geklemmte Symbole an der Kante werden damit schnell zu einem Klumpen.

**Mein Vorschlag war:** Missionsgebiet samt Rand zeigen und das
Missionsgebiet darin als feinen Rahmen markieren.

**Silvio hat entschieden, v232:** „Ich will keinen Rand im Radar angezeigt
bekommen. Ich will dass das Radar das gesamte Spielfeld berücksichtigt.
Ansonsten brauch ich kein Radar, wenn ich raten muss, an welcher Position
sich bestimmte Schiffe befinden."

**Damit gilt:** Das Radar zeigt die **ganze Welt** (`WX0..WX1`,
`WY0..WY1`), kein Rahmen, und **nichts wird geklemmt**. Jedes Schiff steht an
seinem wirklichen Platz. Das ist die Zusicherung, auf die die Prüfung geht.

**Die eine Folge, nachgemessen, damit sie nicht überrascht:** In Missionen,
in denen der **Colossus** gerufen werden kann, hält `worldForWave()` Platz
für ihn frei, ob er kommt oder nicht — `need·1.5` bei 4745 Einheiten Länge
ergibt eine Welt von **7118 × 3968** gegen ein Missionsgebiet von
**3200 × 1946**. Die Schiffe sitzen dann in den mittleren **45 %** des
Radars. Der Kasten selbst bleibt praktisch gleich groß (das
Seitenverhältnis ändert sich kaum), es wird nur alles kleiner.

Wenn Silvio das zu gedrängt findet, ist der nächste Schritt, den Platz für
den Colossus erst freizuhalten, **wenn er wirklich im Feld ist** — das ist
ein Eingriff in die Kameragrenzen und die Schiffsplatzierung, also deutlich
mehr als eine Radaränderung. Deshalb zuerst die einfache Fassung zum Ansehen.

- Status: entschieden, wird in v233 gebaut

### F16 — Verbündete Jäger und Bomber sind viel kleiner als gegnerische

**Befund (Silvio, v232):** „Etwas das mir im Test auch gerade auffällt ist,
dass das Spiel gegnerische und verbündete Jäger/Bomber unterschiedlich groß
darzustellen scheint. Gegnerische Osiris Bomber sind relativ groß wohingegen
verbündete Osisris Bomber lächerlich klein zu sein scheinen."

**Ursache (nachgewiesen):** Verbündete Jäger und Bomber sind die **einzigen
Schiffe im Spiel**, die noch nach der Regel von vor v208 gezeichnet werden.
Drei Wege, drei Maßstäbe:

```js
// Gegner (40_world.js:156 und 174)
const _bw = smallWidth(spr,'bo');                  // = hullWidth: Laenge x 3,75
const sc  = _bw/Math.max(img.width, img.height);

// Spieler (50_combat.js:2880)
return hullScale(k, 0.28);                         // dasselbe

// Verbuendete (40_world.js:1934)
const sc = Math.min(0.55, (kind==='bomber'?65:60)/img.width);
```

Die letzte Zeile ist der Stand von **vor** v208: feste 65 Bildpunkte für
jeden Bomber, 60 für jeden Jäger, unabhängig von der Länge. Bei der
Umstellung auf echte Größen wurde sie übersehen.

**Für die Osiris:** 40 m → **150** Einheiten beim Gegner, **65** beim
Verbündeten. Faktor **2,3**. Und weil die alte Regel eine feste Zahl ist,
ist eine verbündete Osiris (40 m) genauso groß wie eine verbündete Bakha
(18 m), während der Gegner die eine doppelt so groß zeichnet wie die andere.

**Behoben in v233:** derselbe Weg wie beim Gegner und beim Spieler.

### F17 — Die SF Dragon ist zu klein, um sie zu treffen

**Befund (Silvio, v232):** „Ich habe festgestellt, dass die SF Dragon im
Vergleich zu anderen Shivanischen Jägern sehr klein wirkt." Und auf die
Frage, ob die Länge aus der Wiki falsch sei: „Die aus der Wiki gezogenen
Daten sind schon korrekt, also ja, die Dragon ist ein relativ kleiner Jäger.
Das Problem ist halt, dass sie im Browsergame zu klein ist. Ihr Maßstab wird
korrekt sein, nur ist sie so halt sehr schwer zu treffen, daher sollte sie
etwa ein Drittel größer werden."

**Also kein Datenfehler, sondern eine Spielentscheidung.** Die Zahlen, die
dazu geführt haben:

| | Länge | gezeichnet |
|---|---|---|
| SF Dragon | 12,6 m | **47** |
| SF Manticore | 15,5 m | 58 |
| GTF Myrmidon | 16,0 m | 60 |
| GTF Perseus | 17,0 m | 64 |
| GTF Hercules | 20,0 m | 75 |
| SF Astaroth | 21,0 m | 79 |
| SF Aeshma | 30,0 m | 113 |

Die Dragon ist damit der kleinste Jäger im Spiel. Bis v208 bekam **jeder**
Jäger feste 60 Einheiten (`SIZE_CLASS_FIXED fi: 60`), da fiel es nicht auf.

**Behoben in v233:** `SIZE_KEY_MUL` bekommt `fidragon: 1.33` — dieselbe
Tabelle, die Silvio in v166 für die Bojen entschieden hat („Drawn smaller
than its length gives"). Sie wird damit **63** Einheiten groß, liegt also
zwischen Myrmidon und Perseus. Die Längentabelle bleibt richtig, die Ausnahme
steht als Ausnahme da.

**Dabei aufgefallen, noch offen:** In v208 sind zwei weitere Einträge
derselben Art stillschweigend wirkungslos geworden, weil `hullWidth()`
`SIZE_FIXED` nicht mehr liest: die **Manticore** war bewusst 10 % schmaler
(`fimanticore: 50`, heute 58) und die **Sathanas** hatte 540 als Deckel
(heute 4604). Der Kommentar über `HULL_LEN` beschreibt außerdem noch die
alte Regel („Jäger, Bomber und Rettungskapseln sind ausgenommen"). Nicht
angefasst, bis Silvio es entscheidet.

### F18 — Die Spielfläche war in v233 geschrumpft (von mir verursacht)

**Befund (Silvio, v233):** „hast du jetzt einfach das Spielfeld
verkleinert?" — „Wann und wo habe ich gesagt, dass du das machen sollst? Ich
glaub du spinnst!" — „Du sagst mir erstmal was du an meinen Anweisungen nicht
verstanden hast. Wir hatten eine wunderschöne große Fläche auf der genug
Platz für einige Großschiffe war und du machst das einfach kaputt. Bei der
Reparatur des Radars ging es darum dafür zu sorgen, dass sich das Radar auf
die gesamte bespielbare Fläche ausweitet und nicht, dass du die bespielbare
Fläche auf einen vergrößerten Radarbereich schrumpfst. Jede Mission braucht
exakt die gleich große Spielfläche und nicht diesen lächerlich winzigen
Ausschnitt, den du jetzt davon übrig gelassen hast."

**Der Befund stimmt, und die Ursache war meine.** Ich habe in v233 in
`worldSet()` (`10_core.js`) die Rechnung für die Welt geändert, von

```js
const ww = Math.max(MW, (need || 0)*1.5)           // v232
const ww = Math.max(MW, (need || 0) + 300*FIELD_K) // v233, von mir
```

Dazu kam, dass `need` seit v233 die Colossus nur noch so lang zählt, wie sie
**gezeichnet** wird (Silvios eigener Vorschlag zu ihrer Größe, F15) statt mit
ihren vollen 4745 Einheiten. Beides zusammen hat die Welt an das
Missionsgebiet gefesselt. **Für die zweite Änderung hatte ich um ein
ausdrückliches Ja gebeten und nie eines bekommen; ich habe sie trotzdem
gebaut. Das war falsch.**

**Nachgemessen über alle 80 geschriebenen Missionen:**

| | v232 | v233 |
|---|---|---|
| kleinste Welt | 7118 × 3968 | **1151 × 679** (M12) |
| größte Welt | 10090 × 6367 | 10090 × 6367 |
| verschiedene Größen | 14 | **30** |
| Missionen unter 7118 breit | 0 | **76 von 80** |
| Kameraweg M31 | 4831 | **602** |

Das **Missionsgebiet** (`MW × MH`) war nie betroffen und ist in v233 genau so
groß wie in v232. Geschrumpft ist die **Welt** (`WX0..WX1`, `WY0..WY1`) — das,
was man befliegen kann und wohin die Kamera darf. Das ist die Fläche, die
Silvio meint.

**Warum sie in v232 überall gleich groß war:** nicht weil es irgendwo
festgelegt war, sondern als Nebenwirkung. Der Platz, der für eine rufbare
Colossus freigehalten wurde (4745 Einheiten und die Hälfte dazu = 7118), war
in fast jeder Mission der größte Posten der Rechnung und bestimmte damit das
Ergebnis.

**Behoben in v234:** Die Untergrenze steht jetzt als Zahl im Code
(`WORLD_W0 = 7118`, `WORLD_H0 = 3968`) und hängt an keinem Schiff mehr. Die
Welt ist in **66 von 80** Missionen genau 7118 × 3968; in den 14 übrigen ist
sie größer, weil deren **eigenes Missionsgebiet** mehr braucht (M55, M58–M62,
M77: 10090 × 6367; M10/11/19/49/51/54: 8151 × 5133; M78: 9378 × 5914).
Kleiner wird sie nirgends mehr.

**Was noch nicht erfüllt ist, und warum:** „exakt die gleich große
Spielfläche" ist damit **noch nicht** erreicht — 14 Missionen sind größer.
Deren Missionsgebiet richtet sich über `FIELD_K` nach dem **längsten Schiff
der Mission** (M12: Faktor 1,05 → 837 breit; M55: Faktor 9,17 → 7338 breit).
Solange `FIELD_K` je Mission anders ist, ist auch die Spielfläche je Mission
anders. Ein einziger gemeinsamer Wert wäre möglich, verschiebt aber in allen
80 Missionen die Standplätze aller Schiffe — und damit genau die Flug- und
Wartezeiten, über die Silvio sich beschwert hat. **Das gehört in den geplanten
Neubau der Missionen aus den FreeSpace-Originalen, nicht in eine
Einzeländerung.** Entscheidung steht bei Silvio.

**Zweite offene Folge:** Weil die Welt wieder größer ist als das
Missionsgebiet, zeigt das Radar in M31 nur **30 % × 32 %** davon als
belegten Bereich. Das ist derselbe „Rand", den Silvio nicht sehen will — nur
dass es diesmal kein gezeichneter Rahmen ist, sondern wirklich befliegbare
Fläche. Auch das löst sich erst mit einem gemeinsamen `FIELD_K`.

**Prüfung:** `fieldsim`-Szenario „Every mission gets a play field of the same
size" ruft `worldForWave()` für jede geschriebene Mission auf und liest die
Welt. Gegen eine Kopie von v234, in der nur diese zwei Zeilen auf den
v233-Stand zurückgedreht sind, meldet es **30 verschiedene Größen und 76
Missionen unter der Untergrenze**. Die zwei Zusicherungen, die im
Radar-Szenario die Schrumpfung festgeschrieben hatten
(`worldIsMissionPlusMargin`, `mostOfTheRadar`), sind entfernt — sie waren
geschrieben worden, um sie zu segnen.

- Status: behoben in v234; die Frage nach einem gemeinsamen `FIELD_K` offen

### F19 — Der freie Sichtradius im Nebel verschiebt sich

**Befund (Silvio, v234):** „Wichtig für die Nebelmissionen später: Durch das
Hochskalieren ist die Nebeldarstellung leicht kaputt gegangen. Normalerweise
hat der Spieler um sein Schiff herum einen kleinen Radius mit freier Sicht.
Seit der Hochskalierung verschiebt sich dieser Radius. Das muss bis zur
Erstellung der ersten Nebelmission noch gefixt werden."

**Im Code nachgelesen — der Befund stimmt, und die Ursache ist eine Zeile.**
`drawNebulaFog()` (`50_combat.js`) zeichnet die freie Tasche als Farbverlauf
um `player.x` / `player.y`:

```js
const g = ctx.createRadialGradient(player.x,player.y,r*0.25,
                                   player.x,player.y,r*1.45);
ctx.fillRect(0,HUD_H,W,H-HUD_H);
```

Gefüllt wird in **Bildschirmkoordinaten** (0 bis W), zentriert wurde auf
**Weltkoordinaten**. Solange das Spielfeld der Bildschirm war, war beides
dasselbe. Seit v208 steht der Spieler bei Welt-x von einigen Tausend —
nachgemessen in M39: Welt-x **1534**, Bildschirm-x **400**. Die Tasche lag
also mehr als eine Bildschirmbreite rechts neben dem Bild.

**Behoben in v236:** Mittelpunkt `w2sX(player.x)` / `w2sY(player.y)`, Radius
`fireRange()*CAM.z`. Damit sitzt die Tasche auf dem Spieler und ist so groß
wie die Waffenreichweite durch den Kamerazoom — was man nicht sieht, sieht
auch einen nicht, und das war die Absicht hinter dem Maß.

**Silvio hat entschieden, v235, gegen meinen Vorschlag es aufzuschieben:**
„Hintergrund ist der, dass wir ja eh Zusatzmissionen, vielleicht auch pro
Ark, planen müssen und vielleicht spielt eine davon mal in einem Nebel."

**Prüfung:** `fieldsim`-Szenario „The clear pocket in a nebula sits on the
player, not beside him" fängt den Aufruf von `createRadialGradient` ab und
liest den Mittelpunkt, den das Zeichnen wirklich verlangt. Gegen die Fassung
vor der Behebung meldet es Mittelpunkt 1534 statt 400 und vier rote
Zusicherungen.

- Status: behoben in v236

## Eigenheiten der Missionsstränge (Silvio, v234)

Zu beachten beim Nachbau der FS1-, ST:R- und FS2-Missionen. **Die
Missionsdateien dienen nur zur Orientierung** — keine 1:1-Übersetzung, kein
Funk.

**Silvios Worte:**

> Wir brauchen für jeden Arc vermutlich eigene Waffen. Für den Random Arc
> kommen weitere hinzu wie jetzt schon die Dante und die Sidhe.
>
> Im FS1-Arc gibt es anfangs keine Schilde für Jäger und Bomber. Details dazu
> sollten sich in den Missionsfiles finden.
>
> In FS2 in der zweiten Mission versteckt sich die Iceni innerhalb der
> Boadicea. Die Boadicea fällt durch Beschuss langsam auseinander, wodurch
> die Iceni zum Vorschein kommt und dann flieht.
>
> Aufgrund der Anforderung von 100 Missionen insgesamt müssen wir manche ggf.
> aufteilen. Ich hoffe, dass du kreativ genug bist, mir dabei helfen zu
> können ohne Missionen zu bauen, die bei Fehlschlägen oder anderen
> Ereignissen, dann nie mehr enden können.

**In den Dateien nachgelesen, Stand v234:**

| Eigenheit | Befund in den Dateien |
|---|---|
| Waffen je Strang | Die Missionsdateien nennen die Bewaffnung jedes Schiffes selbst (`+Primary Banks:`). FS1: „ML-16 Laser", „Vasudan Light Laser". FS2: „Subach HL-7". Die Waffenliste eines Strangs ist also **aus den Missionen ablesbar** — eine `weapons.tbl` ist dafür nicht nötig. |
| keine Schilde (FS1) | `no-shields` steht pro Schiff, nicht pro Mission, und **durchgehend** — nicht nur anfangs: SM1-01 19 Schiffe, SM1-07 40, SM2-01 13, SM3-08 2, SM3-09 23. Es nimmt ab, verschwindet aber nie. Welche Klassen betroffen sind, ist noch nicht ausgewertet. |
| Iceni in der Boadicea | Steht in `fs2/SM1-02.fs2` — die einzige FS2-Datei, in der „Boadicea" vorkommt. |

**Das Modell der Boadicea** ist einer der acht noch fehlenden Rümpfe.

- Status: eingetragen, noch nicht umgesetzt

### Waffen und Beams je Strang — noch nichts gebaut

**Silvio, v235:** „Wir brauchen für jeden Arc vermutlich eigene Waffen. Für
den Random Arc kommen weitere hinzu wie jetzt schon die Dante und die Sidhe."
— „Für die neuen Waffen braucht es zudem neue Einträge für unsere bisherigen
Waffen." — „Beams existieren in FS1 nur auf der Lucifer. In STR nur auf der
Hades. Hast du das mit berücksichtigt bei den Waffenmounts für die FS1 und
STR-Arks?"

**Antwort: nein, nichts davon ist berücksichtigt.** Es gibt bisher überhaupt
nichts strangabhängiges im Spiel.

- **Waffen** stehen in `PRIMARIES` und der Sekundärliste (`70_ui.js`) als
  **eine** Liste, ohne ein Feld dafür, in welchem Strang eine Waffe
  verfügbar ist. Die bisherigen Einträge brauchen also ein solches Feld, bevor
  strangeigene Waffen dazukommen können — genau Silvios Punkt.
- **Beams — hier hatte ich mich geirrt, und die Berichtigung ist wichtig.**
  Ich hatte Silvio gesagt, eine Regel pro Strang gebe es nicht. **Es gibt
  sie.** `ERA_RULES` (`30_waves.js`) kennt genau das:

  ```js
  fs1: {noBeams:true, shieldWave:9, avengerWave:8, shivanShieldPen:0.25},
  str: {noBeams:true, shieldWave:0},
  fs2: {noBeams:false, shieldWave:0}
  ```

  und `initBeams()` (`50_combat.js:3028`) liest sie:
  `if(eraRule('noBeams') && !e.keepBeams) return;`

  Auch Silvios zweiter Punkt steht schon da: `shieldWave:9` heißt, dass die
  Flotte in FS1 erst ab Welle 9 Schilde hat — „Im FS1-Arc gibt es anfangs
  keine Schilde für Jäger und Bomber."

  **Behoben in v237** (siehe unten). **Drei Lücken, Stand v236:**

  1. **`keepBeams` wird nirgends gesetzt** — nur gelesen. Die Ausnahme für die
     Lucifer steht im Kommentar und in der Bedingung, aber **kein Schiff
     bekommt sie je.** In einer FS1-Welle hätte die Lucifer also keine Beams.
     `grep -rn "keepBeams" src/` gibt genau zwei Treffer, beide in derselben
     Funktion.
  2. **Für ST:R fehlt die Hades-Ausnahme.** `str` hat `noBeams:true` ohne
     jede Ausnahme; Silvio: „In STR nur auf der Hades."
  3. **Die geschriebenen Missionen setzen keine Ära.** `currentEra` steht auf
     `'fs2'` und wird nur im Übungsmodus (`?fs1=`) auf `'fs1'` gesetzt. Alle
     80 Missionen laufen damit als FS2 — die ganze Maschinerie liegt brach.
     Eine Mission braucht also ein Feld für ihren Strang.

**Die Waffentabellen liegen jetzt im Repo:** FSPort in
`fs1/tables/tables/weapons.tbl`, FS2-Retail in
`fs2/tables/weapons_retail.tbl`, dazu die Änderungstabellen von ST:R
(`str/tables/str-shivan-wep.tbm`) und der MediaVPs. Welche Waffe in welchem
Strang vorkommt, lässt sich aber auch direkt aus den Missionsdateien ablesen
(`+Primary Banks:`), was genauer ist als die Tabelle: es sagt, was wirklich
geflogen wird.

- Status: eingetragen, nichts gebaut. Gehört zum Nachbau der Missionen.

### FS1-Bewaffnung: Railguns statt Beams (gebaut in v237)

**Silvio, v237:** „Was wir jetzt erstmal brauchen sind die Waffendaten für die
Schiffe, die alle in FS1 und STR vorkommen, denn diese sollen, mit kleineren
Ausnahmen, auch die FS1 Waffen bekommen. Strahlenwaffen waren in FS1 bei den
Terranern und Vasudanern meistens nur Terran (Huge) Turrets, bei den
Vasudanern halt nur gelb eingefärbt. Viele Mods für FS1 machen es aber so,
dass sie diese Mounts stattdessen mit Railguns ersetzen, damit die großen
Schiffe ihren Punch nicht verlieren und immer noch ordentlich austeilen
können." — „Antijägerbeams brauchen einen Ersatz, der gut gegen Jäger/Bomber
geeignet ist."

**Was schon da war:** `CAP_GUNS` ist aus den FS1-Zahlen gebaut, die Takte
stimmen genau (Terran Turret 1,0 s, Huge Turret 3,0 s, Shivan Turret Laser
1,2 s, Megafunk 3,4 s). Dazu gibt es in `59_field3d.js` eine Tabelle
(`F3D_WPN`, 41 Einträge), die **FreeSpace-Waffennamen** auf FS3-Werte
abbildet, und die Mount-Daten jedes Rumpfes nennen pro Geschütz den
Waffennamen. „Terran Huge Turret" und „Vasudan Huge Turret" haben identische
Werte — nur die Farbe trennt sie (`RACE_COL`, Vasudaner gelb), genau wie
Silvio sagt.

**Nachgemessen, was ein Mount austeilt** (Schaden je Sekunde):

| | |
|---|---|
| großer Beam BGreen | 9,9 |
| Terran Huge Turret | 5,9 |
| Terran Turret | 6,2 |
| Antijägerbeam AAAf | 2,8 |
| Standard Flak | ~15, als Wand aus 8 Splittern |

Ein Huge Turret statt eines Beams verliert also **40 %** der Wirkung dieses
Mounts — Silvios „Punch"-Einwand ist damit belegt.

**Seine Entscheidungen:** Railgun-Schaden **26**, Geschoss sichtbar und eher
etwas langsamer („wenn es etwas langsamer fliegt, wird der Nachteil gegenüber
späteren Beams auch deutlich, weshalb diese später dann auf Großkampfschiffe
gemountet wurden"), Streuung **1,5** als Mitte zwischen Huge Turret (3) und
der Präzision einer Railgun.

**Was ich dabei gefunden habe und was es geändert hat:** Die Beams sind nicht
**eine** Waffe. Über die Tabelle gemessen reichen sie von **1,0** Schaden je
Sekunde (LTerSlash) bis **35,8** (BFred) — Faktor 36. Eine einzige Railgun für
alle hätte ein schwaches Streichbeam-Mount auf das Vierfache gehoben und ein
schweres auf ein Viertel gesenkt. Silvios 26 sind deshalb der **Anker** (sie
waren am BGreen gemessen), und jedes Mount behält seinen **eigenen** Wert: der
Schaden skaliert mit dem Schaden je Sekunde des Beams, den die Railgun
ersetzt. Grösste Abweichung über alle Mounts: **1,2 %**.

**Gebaut:**

- `F3D_WPN.Railgun`: Takt 2,0 s (der Fire Wait der FS1-Railgun), Schaden 26
  am Anker, Geschosstempo **5,5** (schneller als jeder FS1-Turm mit 4,5,
  deutlich langsamer als das Bordgeschütz des Spielers mit 8, mit sichtbarer
  Flugzeit), Streuung 1,5, schweres Geschoss.
- In einer Ära ohne Beams wird jedes **große** Beam-Mount zu einer Railgun und
  jedes **Antijäger**-Beam-Mount zu Standard Flak — der FS1-Antwort auf Jäger.
- `ERA_BEAM_KEEP = {fs1: ['sdlucifer'], str: ['sdhades']}` und
  `eraKeepsBeams()`. Damit greift die Ausnahme wirklich: `keepBeams` wurde in
  `initBeams()` gelesen und **nirgends gesetzt**.
- Der Mount-Zwischenspeicher trägt jetzt die Ära im Schlüssel, sonst würden
  die Listen der ersten Mission für alle späteren ausgegeben.

**Prüfung:** `fieldsim`-Szenario „Without beams a ship gets railguns and flak,
not silent mounts". Gegen eine Kopie ohne die Ersetzung vier rote
Zusicherungen, gegen eine Kopie mit der alten toten Flag-Prüfung meldet es,
dass die Lucifer in FS1 ohne Beams dastünde.

**Offen, bewusst nicht entschieden:** Standard Flak teilt etwa **fünfmal** so
viel aus wie der Antijägerbeam, den sie ersetzt — aber als Splitterwand, die
treffen muss, nicht als sicher treffender Strahl. Ob das sich richtig
anfühlt, ist eine Frage für den Browser, nicht für eine Zahl. Silvio sieht es
sich an.

### Nur Schiffe der Ära — auch im rufbaren Support (gebaut in v238)

**Silvio, v238:** „Im FS1-Block kommen auch nur FS1-Ära Schiffe vor. Die
Sathanas und Hecate zum Beispiel existieren da noch gar nicht. Das ist auch
wichtig für den rufbaren Support dann."

**Nachgelesen, Stand v237:** `ALLY_DEFS` hatte **kein** Ära-Feld. In einer
FS1-Mission hätte das Rufmenü Hecate, Aeolus, Deimos, Sobek, Hatshepsut und
die Colossus angeboten — alle FS2. Dazu: `eraPool()` war definiert und wurde
**nirgends aufgerufen**; `ERA_POOLS.fs1` lag seit seiner Entstehung brach,
weil `ROLES` nach Fraktion benannt ist (`ntf_fighters`) und `ERA_POOLS` nach
Rasse (`ter_fighters`) — die zwei Benennungen trafen nie aufeinander. Dasselbe
Muster wie bei `keepBeams`.

**Aus den Originalmissionen gemessen**, Zahl der Schiffe in den Missionen des
Strangs (Klassennamen ohne `#Name`-Zusatz, PV- und GV-Schreibweise
zusammengeführt):

| rufbar | FS1 | ST:R | FS2 |
|---|---|---|---|
| GTC Fenris | 4 | 15 | 7 |
| GTC Leviathan | 1 | 17 | 8 |
| GTD Orion | 7 | 13 | 6 |
| PVC/GVC Aten | 8 | 11 | – |
| PVD/GVD Typhon | 6 | 3 | 1 |
| GTC Aeolus | – | – | 16 |
| GTCv Deimos | – | – | 18 |
| GTD Hecate | – | – | 4 |
| GVC Mentu | – | – | 5 |
| GVCv Sobek | – | – | 11 |
| GVD Hatshepsut | – | – | 3 |
| GTVA Colossus | – | – | 6 |

Silvios Beispiele bestätigt: **Sathanas 44 Schiffe in FS2, keines in FS1 oder
ST:R. Hecate 4 in FS2, keines davor. Die Hades nur in ST:R** (6 Schiffe).

**Zwei Vorbehalte, die benannt sein müssen:**

1. Die Liste sagt, **was die Missionen eines Strangs benutzen**, nicht was in
   der Ära existiert. Für FS1 ist das dasselbe — was es nicht gibt, kann nicht
   vorkommen. Für FS2 nicht: die **Aten** kommt in FS2-Missionen **gar nicht**
   vor, existiert dort aber. Deshalb filtert FS2 nichts.
2. Die **GVC Mentu** ist ein Entwurf der FS1-Zeit, kommt aber nur in
   FS2-Missionen vor. Sie steht daher auf `fs2`. Wenn sie in FS1 rufbar sein
   soll, ist das eine Entscheidung für Silvio, keine Messung.

**Gebaut:**

- `ALLY_DEFS` trägt je Eintrag ein `era`-Feld, `eraAllows()` prüft es. Kein
  Feld heißt jede Ära. Der Filter greift im Rufmenü (`callCols`) **und** bei
  der Platzreservierung der Welt — sonst hielte eine FS1-Mission Platz für
  eine Colossus frei, die es nicht gibt.
- `eraPool()` ist angeschlossen: `poolFor()` fragt zuerst die Ära.
  `ERA_POOL_FAC` bildet die Fraktionsnamen auf die Rassennamen ab. In FS1 und
  ST:R ist der terranisch markierte Gegner die GTI-Rebellion in terranischen
  Rümpfen, also zeigt der NTF-Pool auf den terranischen.
- `ERA_POOLS.fs1` um die **GTF Loki** ergänzt (sie kommt in FS1 vor und
  fehlte), Zerstörer- und Super-Listen dazu, und ein **neuer `str`-Pool**:
  Seraphim, Zeus und die GTF Angel kommen dort dazu. **Die str-Listen sind
  nicht die fs1-Listen plus Zusätze** — die Lucifer ist am Ende von FS1
  zerstört und steht deshalb nicht darin.

**Prüfung:** `callsim`, Abschnitt „Support per era". Gegen eine Kopie ohne den
Filter drei rote Zusicherungen. Dabei kam heraus, dass `callsim` in einem
Überlauftest das Etikett der Aten überschrieb und danach den **falschen** Wert
zurückschrieb (`PVC Aten` statt `GVC Aten`) — behoben, und die neue Prüfung
hängt an den Kennungen, nicht an Etiketten.

### F20 — Colossus stand im FS1-Rufmenü (von mir verursacht, behoben in v239)

**Befund (Silvio, v238):** „Das Rufmenü zeigt die PVC Aten, die PVD Typhon
und die GTVA Colossus."

Aten und Typhon sind richtig — beide gibt es in FS1, und die Namen stehen
korrekt als PV. **Die Colossus war mein Fehler.** Sie wird **außerhalb** der
Spalten auf ihrer eigenen Taste G gezeichnet, und mein Filter in v238 saß nur
in `callCols()` und bei der Platzreservierung.

**Schlimmer ist, wie die Prüfung das durchgelassen hat.** Ich hatte in
`callsim` geschrieben:

```js
ok('no Colossus in FS1', !W.run("eraAllows(ALLY_DEFS[ALLY_SPECIAL])"));
```

Das prüft die **Aussage**, nicht die **Stelle, die sie benutzt** — genau der
Fehler, der in `CLAUDE.md` unter „Was Simulationen können und was nicht"
steht: `shipsim` öffnete das Rearm-Fenster über die Funktion statt über den
Knopf, und der Knopf war nie angeschlossen. Ich habe denselben Fehler
wiederholt, zwei Tage nachdem ich ihn dort gelesen habe.

**Behoben in v239:** `callAlly()` prüft die Ära — dort, wo schon im Kommentar
stand „Gated here rather than in the menu: the key handler and any future
caller come through this function too" — und `showCol` in `70_ui.js` prüft
sie für ihre eigene Zeile. Die Prüfung liest jetzt das **gezeichnete Menü**
(die Rechtecke mit Kennung) und ruft `callAlly()` wirklich auf. Gegen den
Stand v238 drei rote Zusicherungen.

- Status: behoben in v239

### F21 — Die Spielerbewaffnung kennt keine Ära

**Befund (Silvio, v238):** „Mein Apollo-Jäger trägt Prometheus R, Subach und
Harpoon."

**Stimmt, und es ist alles FS2.** Die Arsenale in `56_banks.js` haben **kein**
Ära-Feld: `ARSENAL_P` hat 9 Primärwaffen (Prometheus R, Subach HL-7, Mekhu
HL-7, Akheton SDG, Morning Star, Prometheus S, UD-8 Kayser, Circe, Maxim) und
`ARSENAL_S` 10 Sekundärwaffen (Harpoon, Rockeye, Tempest, Tornado, EMP Adv.,
Infyrno, Trebuchet, Stiletto II, TAG-C, Cyclops). Davon gibt es in FS1 nur die
**Akheton SDG**; die Prometheus existiert in FS1, aber nicht als R- oder
S-Variante.

`BANKS` gibt je Rumpf die Startbänke und die erlaubten — für die Apollo
`p:['promr','subach'], s:['harpoon','harpoon']`. Auch ohne Ära.

**Die FS1-Werte sind belegt, nicht zu erfinden:** FSPorts `ships.tbl` hat
`$Default PBanks` und `$Default SBanks` für **704 Einträge**. Die GTF Apollo
steht dort mit `( "Avenger" "ML-16 Laser" )` und `( "MX-50" "MX-50" )`.
FS1s Primärwaffen aus `weapons.tbl`: ML-16 Laser, Vasudan Light Laser, VLL-9,
Disruptor, D-Advanced, Akheton SDG, Avenger, Flail, Prometheus, Banshee,
Railgun, S-Breaker, Leech Cannon, UD-1 Volz. Sekundär: MX-50, Fury,
Interceptor, Hornet, Phoenix V, D-Missile, Havoc, Synaptic, Cluster Bomb,
Stiletto, EM Pulse, Barracuda, Tsunami, Serkr, Harbinger.

Das ist genau der Punkt, den Silvio vorausgesagt hat: „Für die neuen Waffen
braucht es zudem neue Einträge für unsere bisherigen Waffen."

- Status: eingetragen, nichts gebaut. Umfang bei Silvio.

**Entschieden (Silvio, 14.10.2026) — FS1-Waffen:**

- Grundstock sind die **echten FS1-Waffen** (Namen und Rolle wie im
  Original, Werte an FS3 angepasst). Eigene Erfindungen höchstens später
  als Ergänzung.
- **Spielerauswahl:** Primär ML-16, D-Advanced, Avenger, Prometheus,
  Banshee. Raketen (nur Jäger) MX-50, Fury, Interceptor, Phoenix V, Hornet.
  Bomben (nur Bomber) D-Missile, Synaptic, Stiletto, Tsunami, Harbinger
  (D-Missile wie in FS1 als Bombe, Silvio 14.10.2026).
- **Disruptor und Flail entfallen ganz**, auch bei Computerschiffen
  („waren in FS1 einfach scheiße"). Ersetzt durch D-Advanced bzw. Avenger;
  vor dem Zeitpunkt des D-Advanced (Mission 17) durch den Avenger.
- **Shivaner:** behalten ihre Laser (Light, Heavy, Mega). Ihre Raketen sind
  die terranischen in Shivaner-Optik. Unknown Bomb/Megabomb werden ersetzt
  durch **Tsunami und Harbinger in Shivaner-Rot**.
- Waffen, die in FS1 nur in einer einzigen Mission angeboten werden (Leech
  Cannon, EM Pulse, Cluster Bomb, S-Breaker, Fang, Barracuda), gibt es
  nicht für den Spieler.
- **Ab wann** (Nummer der Original-FS1-Mission in Kampagnenreihenfolge,
  gezählt mit `+Weaponry Pool` für den Spieler und den Schiffseinträgen für
  Computerschiffe; die FS3-Mission übernimmt den Zeitpunkt ihrer Vorlage):

  | Waffe | Spieler | Computer |
  |---|---|---|
  | ML-16, Fury | 1 | 1 |
  | MX-50 | 1 | 2 |
  | Avenger | 8 | 2 |
  | Stiletto | 10 | 10 |
  | Interceptor | 11 | 8 |
  | Phoenix V | 13 | 5 |
  | Tsunami | 13 | 13 |
  | Synaptic | 15 | 13 |
  | Prometheus | 16 | 17 |
  | D-Advanced | 17 | 17 |
  | Hornet | 18 | 21 |
  | Banshee | 21 | 21 |
  | D-Missile | 24 | 29 |
  | Harbinger | 26 | 26 |

- **Werte (abgesegnet 14.10.2026):** die FS1-Rohwerte aus FSPorts
  `weapons.tbl`, umgerechnet wie die FS2-Waffen in `56_banks.js`
  (`PRI_ANCHOR`, `MIS_ANCHOR`, `BOMB_ANCHOR`) — also im FS1-Verhältnis
  zueinander, gemessen an Prometheus R / Harpoon / Cyclops. Rohwerte
  (d, v, w, l, e, a, s, u, cargo, Explosionsradius innen/außen):

  ```
  ML-16 Laser   5  450 0.2  2   0.2  1    0.1  0.3
  D-Advanced    25 575 0.6  1.5 0.75 0    1    1     puncture
  Avenger       16 525 0.25 1.9 0.3  1.25 0.85 0.35
  Prometheus    20 450 0.3  2   0.4  1.3  0.7  0.35
  Banshee       26 650 0.4  1.5 1.6  0.7  1.2  0.35
  MX-50         25   150 0.75 10 a1 s0.4  u1   cargo4  r20/40   heat
  Fury          30   300 0.3  3  a1 s0.5  u0.6 cargo0.5          dumbfire
  Interceptor   150  250 2    5  a1 s0.8  u0.5 cargo4            aspect
  Phoenix V     350  175 5    10 a1 s0.5  u0.8 cargo8  r10/30   aspect
  Hornet        25   190 2    7  a2 s1    u0.3 cargo1  r10/20   aspect
  D-Missile     1    80  5    15 a0 s0    u1   cargo8  r10/400  aspect, Electronics
  Synaptic      60   90  5    2.5 a1 s0.75 u1  cargo15 r50/100  15 cluster babies
  Stiletto      775  150 2    15 a0.01 s0 u1   cargo8            heat, puncture
  Tsunami       1500 60  20   25 a1 s0.02 u2   cargo15 r50/150  aspect
  Harbinger     3200 50  30   30 a1 s0.01 u16  cargo40 r100/250 aspect
  Shivan Light  8  450 0.3  2   0.3  1 1   1
  Shivan Heavy  15 475 0.5  2   0.4  1 1   1
  Shivan Mega   30 400 0.75 1.5 0.9  1 0.6 1
  ```

- Status: **gebaut in v240.** Die FS1-Waffen stehen in `56_banks.js`
  (`era:'fs1'`, `fs1:{p,c}`), die Standardbänke je Rumpf aus FSPorts
  `ships.tbl` in `FS1_FITS`. Noch nicht drin, weil die Werte fehlen: die
  15 Splitter der Synaptic und der Schwarm der Hornet.

### F22 — Das Rearm-Fenster hängt an einer Korvette, und FS1 hat keine

**Befund (Silvio, v238):** „gibt es in FS1 keine Korvetten. Das Rearm-Menü
hängt aber daran ob Korvetten im Feld sind. Lösungsvorschläge?"

**Stimmt.** `rearmReady()` in `70_ui.js` ist genau eine Zeile:
`return corvetteOnField();` — und `corvetteOnField()` sucht einen
Verbündeten mit `type==='corvette'`. In FS1 und ST:R kommt keine Korvette vor
(gemessen: GTCv Deimos und GVCv Sobek nur in FS2-Missionen), das Rearm-Fenster
wäre dort also **nie** erreichbar.

#### Vier Wege, die Silvio ABGELEHNT hat — nicht wieder vorschlagen

Ich hatte sie ihm vorgelegt, er hat alle vier mit Begründung verworfen. Seine
Worte, v239, wörtlich:

> **Versorgungsschiff: Nein** und das habe ich schon ein mal begründet. Mir
> geht es wirklich auf den Sack, dass ich alles 10 mal erklären muss und es
> trotzdem später wieder zur Debatte wird. Versorgungsschiff geht nicht, weil
> es in unserem Spiel kaum möglich ist ruhig stehen zu bleiben und eine
> Wieder-/Neubewaffnung vorzunehmen.
>
> **Kreuzer:** Es in der FS1-Ära an einen Kreuzer zu hängen und später dann an
> eine Korvette macht auch keinen Sinn, weil es das Rearm später verteuert und
> den Spieler nur verwirrt.
>
> **Jedes GKS:** Macht es zu einfach.

Und zum vierten (Rearm immer verfügbar) hatte ich selbst geschrieben, dass es
die taktische Bedeutung verliert — das war damit auch abgelehnt.

**Daraus die Anforderungen an jede weitere Lösung:**

1. **Kein Stillstehen.** Im Spiel ist es kaum möglich, ruhig zu stehen; ein
   Andockvorgang fällt damit weg. **Das hatte Silvio schon vor v239 einmal
   begründet** — es stand nur nirgends geschrieben, deshalb kam es wieder.
2. **Dieselbe Bedingung in jeder Ära.** Eine andere Klasse je Ära ändert den
   Preis des Rearms und verwirrt den Spieler.
3. **Nicht beliebig leicht zu erfüllen.** „Irgendein Großkampfschiff" reicht
   nicht.
4. **Nicht immer verfügbar.** Sonst verliert es seine taktische Bedeutung.

- Status: eingetragen, Entscheidung offen — aber die vier Wege oben sind
  **erledigt und abgelehnt**

**Entschieden (Silvio, 14.10.2026):** Nachladen gibt es **nur beim eigenen
Trägerschiff** der Mission. Trägerschiff ist **das Schiff, von dem der
Spieler in der Originalmission startet** (z. B. Galatea oder Bastion in FS1,
Aquitaine in FS2) — immer genau ein Schiff, in jeder Ära dieselbe Bedingung.
Es steht nur in den Missionen im Feld, in denen es auch im Original beim
Gefecht dabei ist; in allen anderen Missionen gibt es **kein Nachladen**.
Abgelehnt dagegen: fester Vorrat an Nachladungen je Mission.

- Status: **gebaut in v240.** Nachladen nur bei einer verbündeten Einheit
  mit `home:true`. Die Missionen 1 bis 3 haben kein Trägerschiff, also kein
  Nachladen. Jede Mission des FS1-Strangs startet voll bewaffnet.

### F23 — FS1 M1/M2: fremde Bomber, FS2-Verbündete, Anubis mit Schilden (v240)

**Befund (Silvio, v240):** „Mission 1: Da kommen auch Osiris und Amun-Bomber
drin vor. Von denen hattest du nichts gesagt, aber ich vermute, dass ist eine
automatische Antwort des Games darauf, wenn Kreuzer, Korvetten und/oder
Zerstörer im Feld sind. Zudem sind auf verbündeter Seite FS2-Ära Schiffe mit
reingesprungen auf verbündeter Seite. Teile der Anubis, wenn nicht sogar
alle, haben Schilde." — „Mission 2: Die Anubis haben Schilde was sie nicht
haben dürften, denn zu diesem Zeitpunkt gibt es noch keine."

**Stimmt, alle drei.** `updateCapResponse()` (`40_world.js`) schickt
gegnerische Bomber, sobald irgendein verbündetes Großkampfschiff im Feld
steht — auch die Orff der Mission —, und das Großkampfschiff schickt dann
Abfangjäger aus dem FS2-Vorrat (`sendInterceptors()`, `ROLES`). Und die
Ära-Regel „keine Schilde vor Mission 9" galt nur für den Spieler; Gegner und
Flügelleute bekamen ihre Schilde aus der Rumpftabelle.

- Status: behoben in v241. Im FS1-Strang lösen nur selbst gerufene
  Großkampfschiffe die Bomberantwort aus; Abfangjäger kommen aus dem
  Vorrat der Ära; vor Mission 9 haben Jäger und Bomber außer den
  Shivanern keine Schilde.

### F24 — M3: die Bast fliegt rückwärts an den Container (v241)

**Befund (Silvio, v241):** „Mission 3: Wieso fliegt die Bast rückwärts an den
Frachtcontainer?" — „Natürlich schaut ein Schiff immer in die Richtung in die
es fährt. Es gibt keine rückwärts fliegenden Schiffe in Freespace."

**Stimmt.** Als Fluchtschiff bekommt sie beim Start die Nase nach rechts
(`escape` in `applySpawnOpts`), und `tickDocking()` drehte ein andockendes
Schiff nie um. Sie startet rechts vom Container und fuhr also rückwärts.

- Regel: **Ein Schiff schaut immer in die Richtung, in die es fährt.**
- Status: behoben in v242. Beim Anfahren schaut das Schiff zum Container,
  danach in die Richtung, in die es weiterfährt.
- **Nachtrag (Silvio, v242):** „Die Flugrichtung der Frachter stimmt jetzt,
  aber sie drehen sich nicht, sondern ändern schlagartig ihre Ausrichtung
  sobald sie die Frachtkisten aufgenommen haben." Stimmt: v242 setzte die
  Richtung um, statt zu drehen. Behoben in v243: das Schiff dreht sich in
  1,5 s um, wie ein Großkampfschiff in seiner Bahn (`faceTurn()`).
- **Nachtrag (Silvio, v243):** „Während der Drehung verrutscht der
  Frachtcontainer auf beiden Schiffen und snappt bei Abschluss der Drehung
  wieder an seine richtige Position. Richtiger wäre es, wenn der
  Frachtcontainer auf der Ladefläche physikalisch korrekt mitdrehen würde."
  Stimmt: der Andockpunkt kannte nur „links" oder „rechts", nicht die
  Drehung dazwischen. Behoben in v244: der Andockpunkt dreht mit dem Rumpf
  (`dockPoint()` liest `turnC`), und der Container dreht dieselbe Drehung
  mit.
- **Nachtrag (Silvio, v244):** „Die Frachtcontainer drehen sich jetzt mit dem
  Schiff, was soweit richtig ist, aber so wie die Drehung abgeschlossen ist,
  drehen sie sich nochmal um ihre Längsachse." Stimmt: ein kleiner Rumpf,
  dessen Bild die Seite wechselt, rollt im 3D-Bild eine halbe Drehung um
  seine Länge (`f3dTurnRoll()`, gedacht für Jäger). Behoben in v245: nach
  der Mitdrehung beginnt der Container ohne diese Rolle.

### F25 — M3: die Elysium spielt beim Einsprung den Großschiff-Sound (v245)

**Befund (Silvio, v245):** „Wenn die Elysium reinwarpt, kommt neben dem Sound
für den sich öffnenden Subraumwirbel auch der Sound für hereinwarpende
Großschiffe, was nicht sein sollte."

**Stimmt.** `sndTick()` (`12_audio.js`) gab den langen Großschiff-Sound
jedem Schiff, das kein Jäger, Bomber, Geschütz oder Container ist — also auch
Transportern und Frachtern von 30 bis 60 Metern.

- Status: behoben in v246. Schiffe unter 100 m Länge (`HULL_LEN`) bekommen
  nur den Sound des sich öffnenden Wirbels (`warpSndSmall()`).
- **Präzisiert (Silvio, v246):** „Außer bei Zerstörern und Juggernauts sollte
  dieser Sound nirgendwo auftreten." Umgesetzt in v247: den langen Sound
  haben nur Zerstörer und Superzerstörer (Rümpfe `de…`, `sd…`, auch NTF).

### F26 — M3: der Transporter heißt nicht McCarthy (v247)

**Befund (Silvio, v247):** „Die Elysium heißt nicht GTT McCarthy in FS1."

**Stimmt.** In `fs1/sm1-03a.fs2` heißt sie **Omega** (GTT Elysium);
„McCarthy here" ist nur der Name eines Funkspruchs. Mein Fehler im Entwurf.

- Status: behoben in v248. Name und Auftragstexte sagen Omega.

### F27 — M4: der Spieler fliegt einen vasudanischen Jäger (v249)

**Befund (Silvio, v249):** „Ich fliege einen vasudanischen Jäger, was falsch
ist. In den im Repo liegenden Missionsfiles sollte stehen, welchen Jäger der
Spieler fliegen sollte."

- Status: behoben in v250. Jede FS1-Mission gibt dem Spieler den Rumpf von
  Alpha 1 aus der Originaldatei: M1–M3, M5, M6 Apollo, M4 Valkyrie
  (`ship:` in der Mission, ohne Einblendung). Vorher flog man den ersten
  Rumpf der Liste, die Thoth.

### F28 — Deaktivierziele: nur die Subsysteme zeigen, die lahmgelegt werden sollen (v249)

**Befund (Silvio, v249):** „Bei zu deaktivierenden Schiffen wäre es am besten
nur die Subsysteme anzeigen zu lassen, die deaktiviert werden sollen, sonst
wird das bei Schiffen wie der Omega zu unübersichtlich. Bitte beachte, dass
die jetzigen Missionen 7 - 80 dabei nicht beachtet werden brauchen, weil wir
die ja gerade alle nach und nach ersetzen."

- Status: behoben in v250. `subs:'engines+weapons'` an der Einheit lässt nur
  diese Subsysteme stehen. Nur die FS1-Missionen nutzen das.

### F29 — M5: die Rettungskapsel der Plato flieht zu langsam (v249)

**Befund (Silvio, v249):** „Die Rettungskapsel der Plato flieht zu langsam.
So ist es unmöglich sie zu beschützen."

- Status: behoben in v250. Die Kapsel fliegt 2,9 statt 0,45 je Schritt —
  zwei Drittel einer Apollo, wie Hermes (40 m/s) zu Apollo (60 m/s) in FS1.
  Dabei gefunden: ein Schiff im Todestrudel rollte über den Rand und zählte
  als gerettet. Das ist jetzt ausgeschlossen.

### F30 — M6: die Galatea steht still (v249)

**Befund (Silvio, v249):** „Die Galatea scheint still zu stehen statt
vorwärts zu fliegen."

- Status: behoben in v250. Die Galatea fährt in 170 s über das Feld
  (`crossSecs`) und springt am Ende; sind vorher alle Shivaner weg,
  springt sie sofort.

### F31 — M6: das Asteroidenfeld fehlt (v249)

**Befund (Silvio, v249):** „In FS1 fliegt sie zudem durch ein
Asteroidenfeld, was in dieser Mission fehlt."

- Status: behoben in v250. 60 stehende Asteroiden auf ihrem Weg.

### F32 — M2: das Asteroidenfeld ist zu klein (v249)

**Befund (Silvio, v249):** „Das Asteroidenfeld ist nur ein winzig kleiner
Cluster im Spielfeld. Es sollte größer sein."

- Status: behoben in v250. Die Brocken lagen nur im Missionsbereich, einem
  Drittel der Bildbreite. Mit `spread:1` füllen sie die ganze Kamerasicht
  (70 statt 26 Brocken), mit Abstand zum Startpunkt des Spielers.

### F33 — M3: die Frachter erscheinen beim Einsprung kurz als neutral (v249)

**Befund (Silvio, v249):** „Wenn man reinwarpt, sieht man am Bildrand
kurzzeitig zwei rosane Marker als wenn die Frachter neutral wären. Eine
Sekunde darauf werden sie erst rot."

- Status: behoben in v250. Zwei Ursachen: Frachter ohne Waffen galten als
  „nur für den Spieler" und waren rosa; und bis das 3D-Modell geladen war,
  las die Ma'at sich als unbewaffnet. Im FS1-Strang ist ein Frachter jetzt
  von Anfang an rot; die Waffen liest das Spiel aus dem Modell, nicht aus
  dem, was gerade gezeichnet ist.

### F34 — Die Orion feuert in den falschen Farben (v249)

**Befund (Silvio, v249):** „Die Waffenfarben der Orion stimmen nicht. Ihre
Projektilfarben müssten grün-weiß statt blau-weiß sein." Silvio bietet
Bildmaterial aus den FreeSpace-Dateien an, wenn Farben unklar sind.

- Status: behoben in v250. Laut FS1-Waffentabelle feuern die Terran-Türme
  grün (Laser Color 20,150,20). Im FS1-Strang jetzt grün-weiß; die Railguns,
  die dort die Beams ersetzen, bleiben blau-weiß (in FS1 150,150,250). Der
  FS2-Strang bleibt bei Blau.

### F35 — Die Orion feuert noch teils blau-weiß, das Grün ist zu gelb (v250)

**Befund (Silvio, v250):** „Die Orion hat immer noch teilweise Projektile die
blau-weiß statt grün-weiß sind. Zudem sollte das Grün etwas grüner sein. Das
jetzige geht zu sehr ins Gelbe."

- Status: behoben in v251. Im FS1-Strang ist jeder Terran-Schuss ohne eigene
  Farbe grün, auch die Railguns anstelle der Beams; das Grün ist kräftiger
  (`#5cff5c` statt `#a6ffa0`).

### F36 — Die Dreifachgeschütze der Orion feuern die Salve auf einmal (v250)

**Befund (Silvio, v250):** „Die Trippelgeschütze der Orion feuern ihre
Dreiersalven auf einmal anstatt hintereinander."

- Status: behoben in v251. Die drei Schüsse folgen im Abstand von 12
  Schritten aus demselben Rohr, statt als Fächer auf einmal.

### F37 — M3: nur die Ma'at ist erfassbar, keine roten Markierungen (v250)

**Befund (Silvio, v250):** „In Mission 3 ist nur die Ma'at als Ziel
erfassbar und beide Frachter haben keine rote Markierung wie andere
Gegnerschiffe sie haben."

- Status: behoben in v251. Im FS1-Strang zählen Frachter als Gegner:
  mit der Gegner-Taste erfassbar, rote Winkel wie die Jäger (`neutralLike`).
  Die Bast war ohne Waffen „nur für den Spieler" und fiel aus beidem heraus.

### F38 — Der Wirbel beim Aussprung öffnet sich direkt vor der Nase (v250)

**Befund (Silvio, v250):** „Subraumwirbel bei allen Schiffen öffnen sich
unmittelbar vor deren Nase beim Herauswarpen (wichtig, gilt nur erstmal fürs
Herauswarpen) anstatt ihnen etwas Anfahrtsweg zu lassen wie es in Freespace
der Fall ist."

- Status: behoben in v251. Der Wirbel öffnet 0,6 Längen vor dem Bug, höchstens
  500 Welteinheiten (sonst schoss die Galatea mit 29 px je Schritt hinein).
  Gilt für alle Aussprünge; der Einsprung ist unverändert.

### F39 — Die Ersatzwaffen für die Beams im FS1-Strang (v251)

**Befund (Silvio, v251):** „Was mich aber verwirrt sind die Waffeneffekte der
Waffen, die im FS1Ark die Beams ersetzen. Die scheinen weder Sounds noch
richtige Visuals zu besitzen."

Im Code nachgesehen: Die Railgun (statt großer Beams) hat kein eigenes Bild
und keinen eigenen Klang. Sie wird genau wie der Schuss des schweren Turms
gezeichnet (runde Leuchtkugel, 13 × 13) und soll dessen Klang `wpn_tht`
spielen. Kleine Beams werden zu Standard-Flak.

- Status: geklärt (Silvio, v251): die Railgun ist bewusst unser Ersatz. Was
  er sah, waren die Schweife (F41) und der fehlende Klang (F42).

### F40 — FS2-Waffen auf den Türmen im FS1-Strang (v251)

**Befund (Silvio, v251):** „Jetzt stellt sich aber die Folgefrage wieso die
Plato im FS1-Ark Subachs trägst, die es erst in FS2 gibt? Und haben dieses
Problem auch andere Schiffe? Das betrifft nicht nur die Subach sondern alle
FS2-Ära Waffen."

- Status: behoben in v252. Im FS1-Strang tauscht `fs1Gun()` die FS2-Waffen
  der MediaVP-Modelle gegen die der FS1-Schiffstabelle: Subach und Mekhu
  werden zum Avenger (Elysium und Faustus: ML-16), Shivan Standard Flak
  zum Shivan-Turm-Laser. Betroffen waren Faustus, Elysium, Chronos,
  Poseidon, Aten, Ma'at, Isis, Demon, Asmodeus.

### F41 — Schweife verdeckter Schüsse liegen vorne auf dem Schiff (v251)

**Befund (Silvio, v251):** „Die Trails von Projektilen tauchen auch auf der
Vorderseite des abschießenden Schiffes auf obwohl sie von der vom Spieler
abgewanden Seite verschossen werden." — „Ich rede nur von den Trails der
Schüsse, nicht von den Projektilen."

- Status: behoben in v252. Die Leuchtpunkte des Schweifs wurden über allen
  Schiffen gezeichnet; jetzt entstehen keine, solange der Schuss unter dem
  Rumpf liegt. Dazu haben die Schweife verbündeter Schüsse die Farbe ihres
  Schusses statt immer Hellblau.

### F42 — Turmschüsse sind kaum zu hören (v251)

**Befund (Silvio, v251):** „Das Tripplegeschütz feuert jetzt richtigerweise 3
mal hintereinander, aber der Sound erklingt nur ein mal." — die Plato „scheint
nämlich unter einem ähnlichen Problem zu leiden".

- Status: behoben in v252. Alle Türme teilten sich mit den Jägern einen
  gedrosselten Klang (leise, zwei auf einmal, bei Betrieb weggelassen).
  Großkampfschiff-Türme haben jetzt einen eigenen, lauteren Klang, die
  schweren noch lauter; jeder Schuss der Dreiersalve klingt.


### F43 — Die neuen FS1-Waffen haben keine eigenen Sounds (v252)

**Befund (Silvio, 15.10.2026):** neue Sounds für die neu hinzugekommenen
Waffen, welche fehlen?

Im Code nachgesehen: alle FS1-Waffen liehen sich FS2-Sounds. Nach der FS1-
Soundtabelle fehlten 8 Dateien (L_light, L_disrupter, l_avenge, l_flux,
L_banshee, l_mass, m_mag, m_harbinger); MX-50, Interceptor und Phoenix V
hatten ihre Sounds vertauscht; Synaptic und Harbinger schlagen in FS1 mit
`clusterboom` ein. Silvio hat die Dateien als MP3 auf den Server gelegt.

- Status: behoben in v253 (`12_audio.js`, `56_banks.js`, Railgun in
  `59_field3d.js`; `hitSnd` am Sprengkopf).

### F44 — Raketen gehen auf den Rumpf statt aufs Subsystem (v252)

**Befund (Silvio, 15.10.2026):** „Wenn explizit Subsysteme als Ziel
aufgeschaltet sind, sollten Raketen auch diese anvisieren und nicht wie
bisher den gesamten Rumpf. Bei Raketen, die einen Aspect Lock brauchen, muss
dieser Lock auf das Subsystem gehen, wenn dieses als Ziel anvisiert ist."
Gilt überall bei Subsystemen.

Im Code: die Aufschaltung maß den Winkel zur Schiffsmitte, und eine Rakete
traf das Subsystem nur, wenn sie zufällig dort aufschlug.

- Status: behoben in v253. Die Aufschaltung misst zum gewählten Subsystem
  (`tgtTick`), und eine Rakete mit gewähltem Subsystem trifft dieses
  (`60_effects.js`).

### F45 — Mission 7 (Pandora's Box): zu viele Gegnerjäger (v253)

**Befund (Silvio, 15.10.2026):** „Deutlich zu viele Gegnerjäger. Bitte
halbieren." (Practice-Log: 15 Tode in 1:37.)

- Status: behoben in v254. Statt 14 nur noch 7 Shivan-Jäger (M2 und J3
  gestrichen, Manticore- und Dragon-Staffel kleiner).

### F46 — Mission 8 (Shieldbreaker): Zeitfenster viel zu kurz (v253)

**Befund (Silvio, 15.10.2026):** „Das Zeitfenster die Frachtkisten zu
scannen, den Frachter zu disablen und sich gleichzeitig gegen die Gegner zu
erwehren ist deutlich zu gering. Daher unmöglich zu testen was getestet
werden muss." (Practice-Log: Asmodeus nach 18 s am Rand, kein Schuss
abgegeben.)

- Status: behoben in v254. Die Frachter fliehen nur noch mit einem Viertel
  der Fahrt: die Asmodeus 2 braucht nach dem ersten Treffer rund 75 s bis
  zum Rand statt 19 s, die beiden anderen rund 50 s.

### F47 — Mission 9 und 10 (Hammer and Anvil): Frachter und Container (v253)

**Befund (Silvio, 15.10.2026):** „Die Poseidon-Frachter und die
Frachtcontainer stehen hintereinander anstatt angedockt zu sein. Nur wirklich
ersichtlich dadurch, dass man den Blickwinkel ändert, wenn man sich bewegt.
Die Arme der Poseidon müssten den Frachtcontainer eigentlich auf beiden
Seiten greifen und festhalten. Zudem stehen die Frachter einfach still statt
zu fliegen. Außerdem sind Frachter und Container etwas zu groß im Vergleich
zum Spieler." Mission 10: „Genau dasselbe wie Mission 9."

- Status: teilweise behoben in v254. Die Frachter fliegen langsam nach
  rechts (rund drei Minuten bis zum Rand). Fracht auf einem Frachter liegt
  jetzt in derselben Tiefe wie er und wird direkt nach ihm in seinem
  Tiefenpuffer gezeichnet (`f3dCargoHost`, `59_field3d.js`), damit sie bei
  Kamerabewegung nicht mehr verrutscht und die Arme davor liegen können.
  Die Größe hängt an F52 und ist noch offen.

### F48 — Mission 10: Vasudaner werden zu spät feindlich (v253)

**Befund (Silvio, 15.10.2026):** „Zudem ist die Dauer, bis die Vasudaner
feindlich werden zu lang."

- Status: behoben in v254. Der Seitenwechsel kommt nach 6 s statt 15 s.

### F49 — Mission 11: Taranis zu nah an der Ramses und zerstörbar (v253)

**Befund (Silvio, 15.10.2026):** „Die Taranis ist hier zum einen zu nah an
der Ramses und die Taranis sollte nicht zerstörbar sein, sondern nur ihr
Waffensubsystem. Andernfalls zerstört die Taranis die Ramses zu leicht."

- Status: behoben in v254. Die Taranis springt weiter rechts ein
  (x 760 statt zufällig neben der Ramses), hat nur noch das Waffen-
  subsystem, und ihr Rumpf hält (`noKill`).

### F50 — Subsystem-Markierungen hängen beim Drehen nach (v253)

**Befund (Silvio, 15.10.2026, Mission 12):** „Wenn sich ein Schiff in eine
andere Richtung dreht, bleiben die Markierungen für Subsysteme auf der alten
Position und gleichen sich erst an die neue Schiffsposition an, wenn dieses
seine Drehung vollendet hat. Wahrscheinlich kein missionsspezifisches
Problem."

- Status: behoben in v254. `subPos` dreht mit `turnC` mit, wie die
  Geschütze (`mountPos`).

### F51 — Mission 13 (First Strike: Salvage): Frachter dockt falsch an (v253)

**Befund (Silvio, 15.10.2026):** „Zudem dockt der Frachter immer in der
falschen Richtung an. Die Taranis schaut nach links, der Frachter nach
rechts. Außerdem sollte der Frachter unten am Kreuzer andocken und müsste
dafür eine 180 Grad Fassrolle um seine Längsachse nach dem Einwarpen
machen."

- Status: behoben in v254. Die Halkins springt rechts der Taranis ein,
  fliegt also mit derselben Blickrichtung an, macht eine halbe Fassrolle
  (`dockBelly`, `rollC`/`rollV`, 2,2 s) und dockt unter ihr an. Andockpunkt,
  Geschütze und Trefferumriss drehen mit.

### F52 — Größe der Frachter gegenüber Kreuzern (v253) — behoben in v256

**Befund (Silvio, 15.10.2026, Mission 13):** „Der Frachter ist deutlich zu
groß im Vergleich zur Taranis. 1 zu 1 Proportionen wie in Freespace sind
nicht einwandfrei umsetzbar, das weiß ich, aber das hier fällt schon extrem
auf. Vasudanische Frachter sind dagegen nicht so groß. Shivanische schon.
Hier muss ein Gleichgewicht gefunden werden. Das besprechen wir noch, da es
auch deren Frachtcontainergrößen beeinflusst."

- Silvio, 22.10.2026: „bevor du etwas baust, solltest du dir auch die
  Frachtergrößen in den folgenden Missionen ansehen, denn diese sind,
  zusammen mit ihren Frachtcontainern, zu groß dargestellt" — gilt also
  für die FS1-Missionen nach M3, Frachter **und** Container.
- Status: offen — erst besprechen, dann bauen.
- **Behoben in v256 (Möglichkeit 1, Silvio 22.10.2026):** Frachter und
  Frachtcontainer werden auf 70 % gezeichnet, alle anderen Schiffe bleiben.
  Die Spielfläche der Missionen ändert sich dadurch nicht. Wert im Spiel
  prüfen, bei Bedarf nachstellen.


### F53 — Mission 13: die Chronos springt verkehrt herum ein (v254)

**Befund (Silvio, 15.10.2026):** „Einziger großer Bug ist die Chronos, die
die Taranis kapert. Sie warpt nach rechts schauend ein und snapt instantly
nach links statt einfach umzuschwenken wie es Großkampfschiffe zum Beispiel
schon machen."

- Status: behoben in v255. Ein Schiff, das zum Andocken einspringt, kommt
  schon mit Blick auf sein Ziel aus dem Wirbel (`spawnProtected`).

### F54 — „Try Again" erscheint beim Laden in Chrome (v255) — behoben in v256

**Befund (Silvio, 16.10.2026):** „Zuerst kam während des anfänglichen
Ladebalkens ein Try Again, das ich mehrere Male betätigen musste." — „Ist
einfach nur graue Schrift mit weißer Hintergrundmarkierung. Wenn ich es
einige Sekunden stehen lasse und nichts mache lädt dann der Startbildschirm."
Nur in Chrome, nicht in Brave.

- Vermutete Ursache (im Code nachgesehen, im Browser noch nicht bestätigt):
  `loader.html` übergibt seine Gestaltung mit
  `document.querySelector('style')` — also der **ersten** `<style>` der
  Seite. Schiebt eine Chrome-Erweiterung eine eigene davor, bekommt
  `f3dLoadBoxShow()` (`59_field3d.js`) die falsche, `#retry{display:none}`
  fehlt, und der Knopf steht ungestaltet da, bis die Schiffe bereit sind.
- Reparatur: der `<style>` in `loader.html` eine Kennung geben und gezielt
  diese nehmen. Silvio: ja, mit der nächsten Spieländerung bündeln.
- Nebenbefund, harmlos: die 404 auf `*_n512.webp` sind Texturen ohne
  Reliefbild im Original; das Spiel fragt c/n/g blind an.
- **Behoben in v256:** die Gestaltung des Ladebildschirms trägt eine
  eigene Kennung und wird gezielt übergeben.


### F55 — FS1-Strang: Unterstützung kommt auch als vasudanische Schiffe (v255) — behoben in v256

**Befund (Silvio, 16.10.2026):** „Mission 5: Ich kann statt terranischer,
vasudanische Schiffe zur Unterstützung rufen, was falsch ist. Der komplette
FS1 Ark darf keine vasudanischen Schiffe zur Unterstützung bereitstellen.
Immer nur terranische."

- Silvio, 16.10.2026: „Mission 6: Dasselbe Problem" und „Scheint alle neuen
  Missionen ab Mission 7 bis 13 zu betreffen" — also M5 bis M13, das sind
  alle bisher gebauten FS1-Missionen ab M4/M5.
- Status: offen, wird mit dem nächsten Bau gebündelt. Gilt für **alle**
  Missionen mit `era:'fs1'`, nicht nur M5 und M6.
- **Behoben in v256:** im ganzen FS1-Strang stehen nur terranische Schiffe
  im Rufmenü (eine Stelle für alle Missionen).


### F56 — Mission 3: Omega fährt ins Leere, wenn der Container beim Andocken stirbt (v255) — behoben in v256

**Befund (Silvio, 21.10.2026):** „Mission 3: Wenn der Frachtcontainer, den die
Omega aufnehmen soll zerstört wird, während sie gerade dran andocken will,
beginnt die Omega eine langsame Fahrt zum rechten Bildrand in der ansonsten
absolut nichts passiert."

- Silvio, 21.10.2026 (Berichtigung): Die Mission steht **nicht** fest. Sie
  endet, sobald die Omega rechts aus dem Spielfeld geflogen ist. Das Problem
  ist die **Wartezeit**, in der nichts passiert (Hauptärgernis, siehe
  Missionsentwurf: Wartezeit vermeiden).
- Silvio, 22.10.2026: Möglichkeit 1 — zerstörter Container: die Omega
  springt sofort aus, Ziel verfehlt („Container lost"), Mission endet.
- Status: offen, wird mit dem nächsten Bau gebündelt.
- **Behoben in v256:** die Omega springt sofort aus, „Container lost",
  Ziel verfehlt, die Mission endet gleich danach.


### F57 — Die Waffenkopplung wird nicht von Mission zu Mission behalten (v256) — behoben in v257

**Befund (Silvio, 22.10.2026):** „Die Missionen merken sich nicht, ob ich
meine Waffen gekoppelt habe oder nicht. In jeder neuen Mission muss ich die
Waffeneinstellung wieder neu vornehmen. Solange sich das Schiff bzw. die
Anzahl Primärbänke nicht ändern, sollte die vom Spieler getroffene
Voreinstellung beibehalten werden."

- Ursache (im Code nachgewiesen): beim Missionswechsel steigt der Spieler
  kurz in den Rumpf vor der Mission zurück (`releaseShip`), der nur eine
  Primärbank hat; dabei fiel die Einstellung auf Bank 1 zurück.
- **Behoben in v257:** die zuletzt gewählte Einstellung wird mit der Zahl
  der Primärbänke gemerkt (`PMODE_PREF`) und wieder gesetzt, sobald das
  Schiff gleich viele Bänke hat. Neues Spiel setzt sie zurück.
  Prüfung: `fieldsim` „F57".

### F58 — Mission 9 und 10: die Frachter fahren viel zu langsam (v256) — behoben in v257

**Befund (Silvio, 22.10.2026):** „In Mission 9 und 10 fliegen die Frachter
schon extrem langsam. Das kann man mindestens mal verdoppeln."

- **Behoben in v257:** die drei Theta-Frachter fahren in beiden Missionen
  doppelt so schnell (0,04 → 0,08). Prüfung: `fieldsim` „F58".

### F59 — Mission 14: die Taranis schießt (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Die Taranis sollte deaktiviert sein,
schießt jetzt aber auf die Shivaner mit grünen Projektilen. Sie sollte
einfach nur da stehen und nichts tun."

- **Behoben in v258:** die Taranis feuert nichts mehr, auch keine Flak (`allyFire` beachtet `noFire`). Prüfung: `fieldsim` „Ribos IV“.

### F60 — FS2-Jäger und -Bomber bei den Verbündeten (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Ich habe FS2 Ära Jäger und Bomber bei den
Verbündeten Schiffen."

- Gemeldet beim Test von Mission 14 (Tombaugh).
- **Behoben in v258:** verbündete Jäger und Bomber kommen im FS1-Strang nur aus der FS1-Liste (`allySmallPool`), überall: Missionsstaffeln, Staffeln der Großkampfschiffe, Abfangjäger, Flügelleute.

### F61 — Mission 14: der Spieler springt gleichzeitig mit der Lucifer aus (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Der Warpout des Spielers passiert direkt
als die Lucifer herauswarpt. Es sollten 5 Sekunden dazwischen liegen, damit
der Schock über das Geschehene noch kurz nachhallen kann."

- **Behoben in v258:** die Mission endet 6 s nach dem Aussprung der Lucifer; im Test 5,5 s zwischen ihrem Verschwinden und dem Ende.

### F62 — FS1-Jäger und -Bomber, die noch nicht vorgestellt wurden (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Es kommen auch FS1-Ära Bomber und Jäger
vor, die zu diesem Zeitpunkt noch nicht vorgestellt wurden"

- Gemeldet beim Test von Mission 14 (Tombaugh), direkt nach F60.
- Silvio, 22.10.2026: „Bisher nur Verbündete." Er macht noch weitere
  Testläufe.
- **Behoben in v258:** nur Rümpfe, die in den FS1-Originalen bis zu dieser Mission auf unserer Seite fliegen (`FS1_ALLY_INTRO`, aus den Missionsdateien gelesen): bis Original 10 Apollo, Valkyrie, Athena (Anubis, Seth bei den Vasudanern). In Mission 14 fliegen die Verbündeten Valkyries statt Hercules.

### F63 — Beam-Treffer wandern mit dem Blickwinkel des Spielers (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Wir nutzen ja 2,5D für unser Spiel und
wenn ich mich bewege, verschieben sich die Beam-Treffer ausgehend von meinem
Blickwinkel aufs Spielfeld. Es sollte aber so sein, dass Beams einen
Schiffskörper an bestimmten Stellen treffen und ich das sehe egal wo ich
mich auf dem Spielfeld befinde."

- Silvio nennt ihn „sehr tiefgreifend". Gilt nicht nur für eine Mission.
- Gewünscht: der Treffpunkt sitzt fest an einer Stelle des Rumpfs und
  bleibt dort, wie auch immer sich die Ansicht durch die Bewegung des
  Spielers verschiebt.
- Silvio, 22.10.2026, Ergänzung: „Je nach dem wie ich mich bewege,
  verrutscht der Beamstrahl sogar vom getroffenen Rumpf weg ins Freie und
  das ‚getroffene' Schiff nimmt dann trotzdem noch Schaden, obwohl der Beam
  sichtbar ins Nirgendwo schießt."
- **Behoben in v258:** ein Beam merkt sich die Stelle, an der er ihren Rumpf zuerst trifft, in ihrem eigenen Bezug (`beamAnchor`). Er wird bis zu dieser Stelle gezeichnet, wie die Kamera sie gerade zeigt, und macht nur dort Schaden; ist das Ziel weg, hört er auf. Prüfung: `fieldsim` „F63, F70“ (mit simulierter Rumpftiefe, weil die Cloud keine Modelle hat).

### F64 — Mission 14: die Lucifer kommt der Taranis zu nah (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Die Lucifer fliegt zu nah an die Taranis
heran, sodass sie sie teilweise eigentlich gar nicht treffen können dürfte.
Lass sie einfach etwas weiter rechts hereinwarpen und langsam zum Stehen
kommen."

- **Behoben in v258:** die Lucifer springt bei x 790 ein und kommt bei 690 langsam zum Stehen (`stopX`); Zielreihenfolge im Test weiter richtig.
- Beim Bau beachten: Die Turmreichweite der Lucifer hängt an ihrer Lage.
  Die Reihenfolge ihrer Ziele (Orion vorletzte, Station letzte) muss danach
  im Test wieder stimmen.

### F65 — Mission 14: die Reaktoren der Lucifer werden angezeigt (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Es ist unnötig die Reaktoren der Lucifer
anzeigen zu lassen."

- **Behoben in v258:** hinter einem unverwundbaren Schild werden die Reaktoren nicht mehr gezeichnet.

### F66 — Mission 14: die Lucifer soll treffbar sein, mit Schildeffekt (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Außerdem sollte die Lucifer vom Spieler
und den verbündeten Schiffen getroffen werden können, damit man den coolen
Schildeffekt sieht, den sie eigentlich hat."

- Silvio, 22.10.2026, bestätigt: „Sie sollen nur den Schild aufflackern
  lassen. Durchgehen tun sie nicht." Also: Treffer lassen den Schild
  aufflackern, Schaden nimmt sie keinen.
- **Behoben in v258:** die Lucifer (`shieldShow`) ist erfassbar, Spieler und Verbündete schießen auf sie, jeder Treffer lässt den Schild aufflackern, Schaden nimmt sie keinen.

### F67 — Eine Station trudelt, wenn sie explodiert (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Es macht übrigens keinen Sinn, dass eine
Station anfängt zu trudeln, wenn sie explodiert."

- Gesehen in Mission 14 (Tombaugh). Gilt für Stationen allgemein.
- **Behoben in v258:** eine Station (auch eine verbündete, Klasse Zerstörer) dreht und treibt beim Zerbrechen nicht mehr.

### F68 — Ein Schiff ist beim Aussprung noch hinter dem Wirbel zu sehen (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Wenn die Lucifer in ihren Warpstrudel
fliegt, kann ich sie links davon immer noch sehen als würde sie erst hinter
dem Strudel entmaterialisieren. Ich weiß nicht was der technische Grund
dafür ist und ich weiß nicht wie ich es besser beschreiben soll. Vermutlich
betrifft das alle Schiffe und fällt nur je nach Blickwinkel auf den Warpin
und Warpout auf."

- Gesehen in Mission 14 (Tombaugh). Silvio dachte, das sei schon behoben;
  ein eigener Eintrag dazu steht in dieser Datei nicht.
- Silvios Vermutung (nicht nachgeprüft): betrifft alle Schiffe, beim Ein-
  und Aussprung, je nach Blickwinkel.
- Silvio, 22.10.2026, Bildschirmfoto im Chat: der Wirbel steht fast von der
  Kante her gesehen als senkrechte helle Linie mit blauem Schleier rechts
  davon. Der Bug der Lucifer ragt links aus dem Wirbel heraus und ist voll
  gezeichnet, obwohl er schon durch den Wirbel hindurch ist.
- **Behoben in v258:** Ursache gefunden: das Schiffsmodell liegt unter der Spielebene versenkt, der Wirbel wurde aber in der Ebene gezeichnet. Von der Seite gesehen lag der Schnitt am Rumpf deshalb woanders als die Scheibe. Der Wirbel steht jetzt in der Tiefe des Schiffs (`f3dWarp` mit `pz`). Im Browser ansehen, die Cloud kann WebGL nicht zeigen.

### F69 — Mission 14: neuer Name und ein Planet hinter der Station (Wunsch, v257) — behoben in v258

**Wunsch (Silvio, 22.10.2026):** „Nenne die Mission ‚Rain on Ribos IV' und
bau hinter der Station noch einen Planeten ein. Eine Fan-Kampagne hatte
diese Mission aufgegriffen und aufgrund der herabstürzenden Stationstrümmer
auf Ribos 4 so genannt."

- **Behoben in v258:** Mission 14 heißt „Rain on Ribos IV“; ein großer Planet steht hinter der Station (`planet:` an der Mission, `placePlanet`).

### F70 — Schadenseffekte wandern mit dem Blickwinkel (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Ich stelle gerade bei genauerem Hinsehen
auch fest, dass Schadenseffekte wie der austretende Dampf oder Rauch aus
Hüllenbrüchen je nach Blickwinkel wandern."

- Vermutung (nicht nachgeprüft): dieselbe Ursache wie F63 (Beam-Treffer
  wandern mit dem Blickwinkel). Beim Bau zusammen ansehen.
- **Behoben in v258:** Rauch, Dampf, Flammen und Trefferfeuer an einem Großkampfschiff liegen jetzt in ihrer Tiefe und werden jedes Bild durch die aktuelle Kamera gezeichnet (`hullFxBegin`/`hullFxEnd`/`hullFxView`). Gilt für Lecks, Todesrollen, Beam- und Geschosstreffer.

### F71 — Das Avenger-Geschoss ist blau-weiß statt orange-weiß (v257) — behoben in v258

**Befund (Silvio, 22.10.2026):** „Das Projektil der Avenger sollte
Orange/weiß sein, nicht blau/weiß."

- **Behoben in v258:** Avenger-Geschoss orange-weiß.

### F72 — Mission 14: mit zwei Avenger starten (Wunsch, v257) — behoben in v258

**Wunsch (Silvio, 22.10.2026):** „In dieser Mission sollte man, wenn es die
Waffenkompatibilität der Valkyrie zulässt, mit zwei Avengers starten."

- Vor dem Bau prüfen: darf die Valkyrie in beiden Primärbänken die Avenger
  tragen, und ist die Avenger zu diesem Zeitpunkt (orig 10) schon frei?
- **Behoben in v258:** Mission 14 startet mit zwei Avenger (die Valkyrie darf sie laut FS1-Tabelle tragen, frei ab Original 8).

### F73 — Der Beam verschwindet hinter der Nase der Orion, der Treffer sitzt vorn (v258) — behoben in v259

**Befund (Silvio, 22.10.2026):** „Im Screenshot siehst du, dass der
Beamstrahl hinter der Nase der Orion verschwindet, der Treffereffekt aber
direkt an der Nase erscheint."

- Bildschirmfoto im Chat: roter Lucifer-Beam von rechts, er endet unter der
  Nase der Orion, das Trefferfeuer leuchtet vorn auf der Nase.
- Silvio vermutet denselben Grund wie F76.
- **Behoben in v259:** siehe F76: der Strahl endet jetzt dort, wo er die Oberfläche trifft (auf ihrem Modell gesucht), und das Trefferfeuer sitzt an genau diesem Punkt.

### F74 — Verbündete Geschosse treffen die Lucifer nicht, kein Schildeffekt (v258) — behoben in v259

**Befund (Silvio, 22.10.2026):** „Die Lucifer wird von verbündeten
Projektilen nicht getroffen, entsprechend sieht man ihren Schildeffekt
nicht."

- Gehört zu F66 (in v258 als behoben eingetragen; für verbündete Geschosse
  wirkt es nicht).
- **Behoben in v259:** Geschosse prallen am Schild einer unverwundbaren Einheit mit `shieldShow` ab (`bulletOnHull` ließ „Kulisse“ bisher durch). Im Test 109 verbündete Treffer in 40 s, Schild flackert, kein Schaden.

### F75 — Die Lucifer fehlt auf dem Radar (v258) — behoben in v259

**Befund (Silvio, 22.10.2026):** „Die Lucifer sollte auch auf dem Radar zu
sehen sein."

- **Behoben in v259:** das Radar zeigt auch ein unverwundbares Superschiff (Typ `boss`), das sonst als Kulisse gilt.

### F76 — Beams verschwinden hinter dem eigenen Schiff und tauchen wieder auf (v258)

**Befund (Silvio, 22.10.2026):** „Im zweiten Screenshot siehst du, dass der
Beamstrahl, der vom vorne liegenden Arm der Lucifer abgefeuert wird, hinter
ihrer Nase verschwindet und dahinter wieder auftaucht. Ich befürchte hier
müssen wir die grundlegende Art ändern wie Beams von Schiffen ausgehend
gezeichnet werden, weil evtl. alter Code von der 2D Sprite-Zeit
hineinfunkt. Mein Eindruck ist, dass sich alles was Objekte und ihre Waffen
betrifft noch zu 2dimensional verhält."

- Silvio: F73 und F76 hängen vermutlich zusammen.
- Im Code nachgesehen (v258): Ein Beam ist eine flache Linie auf der
  2D-Leinwand, gezeichnet **unter allen Schiffen** (`draw()` in
  `70_ui.js`, „Beam rays under every hull"), dazu ein Stück **über** dem
  feuernden Schiff, abgeschätzt an dessen 2D-Umriss (`ownRunSmooth`).
  Jedes Modell wird in `f3dRender` mit eigenem, frisch geleertem
  Tiefenpuffer gezeichnet (`gl.clear(gl.DEPTH_BUFFER_BIT)` je Schiff) und
  als fertiges Bild auf die Leinwand gelegt. Ein Beam kennt also keine
  Tiefe: ob er vor oder hinter einem Rumpfteil liegt, entscheidet nur die
  Zeichenreihenfolge.
- **Entschieden (Silvio, 22.10.2026): gemeinsame 3D-Szene für alles außer
  Spieler und Jäger.** Noch nicht gebaut. Plan:
  1. Jedes Großkampfschiff bekommt eine feste eigene Tiefe („Stockwerk"),
     so dass sich überlappende Schiffe nicht ineinanderschieben (der Grund
     für das Leeren des Tiefenpuffers je Schiff, v203: M11, M38, M54, M78).
     Alle Schiffe in einem 3D-Bild mit gemeinsamem Tiefenpuffer.
     **Tiefere Schiffe behalten ihre heutige Bildschirmgröße** (Silvio):
     um die Perspektive ausgleichend vergrößern; Tiefe zeigt sich dann
     beim Schwenken. Die Tiefe hängt an `f3dMidZ`/`f3dMat` (tz); Treffer
     (`hullUnPt`), Wirbel (`f3dWarp pz`) und Rumpfeffekte (`hullFx…`)
     rechnen schon damit. Andocken (`f3dCargoZ`) mitziehen.
  2. Beams als echte räumliche Strahlen in diesem Bild, mit Tiefentest:
     vom 3D-Ort des Turms bis zur Oberfläche des Ziels. Die Sonderregel für
     abgewandte Türme (`mountHid`, „Weg 3") fällt dann weg; `mountCanAim`
     (Halbraum des Turms) bleibt. Löst F73 und F76, auch mit drittem Schiff.
  3. Danach Geschosse der Großkampfschiffe: Start am 3D-Ort des Turms,
     Aufstieg zur Spielebene schnell genug, dass ein Treffer auf einen Jäger
     dort sitzt, wo man ihn sieht; zwischen Großkampfschiffen von Rumpf zu
     Rumpf. Spieler- und Jägergeschosse bleiben in der Ebene (über allen
     Rümpfen).
  - F74 (verbündete Geschosse auf die Lucifer) und F75 (Lucifer auf dem
    Radar) kommen in den ersten Bau.
- **Gebaut in v259 (Schritte 1 und 2), mit einer Änderung am Weg:** Statt
  echter Stockwerke (jedes Schiff tiefer versenkt) bekommt jedes Schiff eine
  eigene **Scheibe im gemeinsamen Tiefenpuffer** (`gl.depthRange`), in der
  Reihenfolge des Spielfelds, und der Stencil merkt sich, welches Schiff an
  jedem Bildpunkt oben liegt. Wirkung wie Stockwerke — Rümpfe schneiden
  sich nie, alle Schiffe in einem 3D-Bild —, aber jedes Schiff bleibt genau
  so groß und genau dort, wo es heute ist (Silvio wollte die heutige
  Größe); echte Stockwerke hätten Lage und Mitschwenken jedes Schiffs
  verändert.
  Beams (`f3dBeamPass`): ein Band im Raum vom 3D-Ort des Turms bis zum
  Punkt, an dem der Strahl ihren Rumpf trifft (`f3dRayHitLocal` auf dem
  Modell, einmal je Schuss, dann mit ihr mitgeführt). Gezeichnet in jeder
  Scheibe gegen den Rumpf, der dort oben liegt, und einmal im freien Raum.
  Die Sonderregel „Weg 3“ für den Strahl entfällt (das Leuchten am
  abgewandten Turm bleibt). Fallback auf den flachen Strahl, wenn eines
  der Schiffe nicht als Modell gezeichnet wird oder das Gerät keinen
  Stencil hat.
  Prüfung mit echtem WebGL im Browser ohne Fenster (Kisten statt Modelle,
  die Cloud hat keine): `fieldsim` „3D beams hidden“ (Strahl unter einem
  Rumpf verdeckt, darüber sichtbar, drittes Schiff entscheidet, Treffer auf
  der Oberfläche) und „whole picture with 3D beams“ (Mission 14 komplett
  gezeichnet, ohne Fehler). Wie es mit den echten Modellen aussieht, kann
  nur Silvio im Browser sehen.
- **Schritt 3 gebaut in v260:** Geschosse und Flak der Großkampfschiffe
  starten am Turm in dessen Tiefe (`capShotZ`) und steigen in `SHOT_RISE`
  (10) Schritten zur Spielebene auf (`shotsView`, beim Zeichnen). Aus einem
  abgewandten Turm steigen sie erst, wenn sie unter dem Rumpf hervor sind.
  Treffer auf Großkampfschiffe brauchen keine Sonderregel: deren dem
  Spieler zugewandte Seite liegt in der Spielebene. Rest: ein Geschoss im
  Aufstieg wird über allen Rümpfen gezeichnet, also nicht von einem
  fremden Schiff verdeckt, das darüber liegt (selten, sehr kurz).

### F77 — Rauch auf der Orion wandert noch mit dem Blickwinkel (v259) — behoben in v260

**Befund (Silvio, 22.10.2026):** „Der Rauch bei Schadenseffekten auf der
Orion wandert immer noch je nach Blickwinkel. Es fällt nur auf, wenn man
wirklich drauf achtet, dennoch sieht es nicht schön aus."

- Gehört zu F70 (in v258 als behoben eingetragen; beim Rauch wirkt es noch
  nicht ganz).
- Bestätigt von Silvio: Beamstrahl und Treffereffekt bleiben in v259
  zusammen (F73/F76).
- **Behoben in v260:** Ursache: Rauch, Dampf und Flammen kamen aus der Tiefe der Schiffsmitte, also aus dem Inneren des Rumpfs, und verschoben sich beim Schwenken gegen die sichtbare Oberfläche. Jetzt wird die Stelle auf der Oberfläche des Modells gesucht (`dmgSurf`/`hullSurfPt`, einmal je Riss oder Krater, dann mitgeführt) und der Rauch in deren Tiefe gezeichnet. Ebenso die Explosionen der Todesrolle und das Trefferfeuer der Beams.

### F78 — Der Beam tritt nicht mehr mit Flammenstrahl auf der anderen Seite aus (v259) — behoben in v260

**Befund (Silvio, 22.10.2026):** „Was aber leider nicht mehr passiert, ist
dass der Beam auf der anderen Seite des Schiffsrumpfs zusammen mit einem
Flammenstrahl austritt."

- Von mir verursacht (im Code nachgesehen): seit v258 (F63) hält ein Beam
  an einer Stelle des Rumpfs fest, und dort wird das Trefferfeuer nur noch
  für den Eintritt gerufen (`beamImpact(..., {entry:q, exit:null})`). Der
  Austritt mit Flammenstrahl fällt damit weg.
- **Behoben in v260:** der 3D-Beam läuft wieder durch das Schiff hindurch (verdeckt vom Rumpf), tritt an der anderen Seite aus (auf dem Modell gesucht) und läuft dahinter weiter wie früher der flache Strahl; dort sitzen wieder die Austrittswunde und der Flammenstrahl. Der flache Strahl (ohne Modell) läuft ebenfalls wieder durch.

### F79 — Ein- und Austrittseffekt der Beams bleiben sichtbar, wenn der Rumpf davor liegt (v260) — behoben in v261

**Befund (Silvio, 22.10.2026):** „Der Eintrittseffekt der Beams passt immer
noch nicht ganz. Wenn ich mich bewege und die vorn liegende Kante der
Orionnase sich damit vor die Nasenfläche schiebt, bleibt der
Eintrittseffekt sichtbar, obwohl ich die Stelle, wo der Beam einschlägt gar
nicht mehr sehen kann. Genauso beim Austrittseffekt." — „Das mit dem 3D für
den Beam passt also noch nicht und muss deutlich besser werden, damit es
perspektivisch Sinn macht." — „Es muss doch möglich sein, das so real wie
im 3dimensionalen Raum darstellen lassen zu können."

- Im Code nachgesehen (v260): Der Strahl selbst liegt im 3D-Bild und wird
  verdeckt. Das Trefferfeuer (Feuerbälle, Funken) ist aber weiter ein
  flaches Bild, gezeichnet **über allen Schiffen** (`drawParts`,
  `drawFxAnims` nach den Rümpfen). Es sitzt an der richtigen Stelle, kennt
  aber keine Tiefe und wird darum nie verdeckt.
- **Behoben in v261:** Ein- und Austritt eines 3D-Beams werden nicht mehr als flaches Bild über die Schiffe gemalt, sondern im 3D-Bild mit dem Strahl (`f3dBeamHitFx`), mit Tiefentest: eine Kante des eigenen Rumpfs davor verdeckt sie, und sie gehören zum getroffenen Schiff, liegen also auch unter jedem Schiff, das über ihm liegt. Prüfung mit echtem WebGL: `fieldsim` „v261: beam entry hidden“.

### F80 — Der Austrittseffekt der Beams ist viel zu dezent (v260) — behoben in v261

**Befund (Silvio, 22.10.2026):** „Der Austrittseffekt [ist] übrigens viel
zu dezent." Dazu ein Bildschirmfoto aus FreeSpace 2 (vor 14 Jahren): ein
gelber Beam einer vasudanischen Hatshepsut trifft ein kleines Schiff. Am
Eintritt ein heller Lichtfleck, auf der anderen Seite tritt ein langer,
breiter, glühender Strahl aus Funken und Flammen aus, der dem Beam auf
mehreren Schiffslängen folgt und sich dabei etwas auffächert.

- Silvio, 22.10.2026: „Der Austrittseffekt sollte sich nicht an der
  Schiffslänge orientieren." Meine Annahme dazu: eine feste Länge je Beam,
  bei schweren Beams länger als bei den kleinen gegen Jäger, unabhängig von
  der Größe des getroffenen Schiffs.
- **Behoben in v261:** der Austritt ist jetzt ein langer, heller Strahl aus Flammen (zwei Lagen im Beam-Profil, orange und weißgelb), der dem Beam folgt, sich um das 2,6-Fache auffächert und dabei verblasst, dazu 30 Funken, die ihn entlanglaufen, und ein Licht am Austrittspunkt. Länge fest je Beam (`BEAM_EXIT_LEN`: 30 Beam-Breiten bei schweren, 18 bei kleinen), nicht nach dem getroffenen Schiff. Am Eintritt ein Licht, etwas Feuer und Funken zurück zum Turm.

### F84 — Raketenaufschaltung reißt ständig ab, Klänge fehlen (v263) — gebaut in v264

**Befund (Silvio, 22.10.2026):** „Ich glaube allerdings dass wir nochmal an
der Raketenaufschaltung arbeiten müssen, denn Ziele bewegen sich zu
schnell, um eine dauerhafte Aufschaltung zu gewährleisten. Dazu fehlt auch
der Sound der angibt, dass die Aufschaltung noch sucht und der
Einrastsound."

**Silvios Festlegung:** „könnten wir es so machen, dass der Suchlauf
startet egal wo sich das als Ziel erfasste Schiff befindet, solange es im
für den Spieler gerade sichtbaren Spielbereich befindet. Wenn das Zielschiff
beim Raketenabschuss hinter dem Spieler befindet, fliegt die Rakete eh eine
riesen Kurve und wird kaum treffen."

- Klänge aus FS1 `sounds.tbl`: `trk-loop.wav` (Suchlauf, Schleife) und
  `lock.wav` (eingerastet, einmal). Im Spiel `sounds/lock_seek.wav` und
  `sounds/lock_on.wav`.
- **Gebaut in v264:** die Aufschaltung baut sich auf, solange das Ziel im
  sichtbaren Bildausschnitt ist (`camSees`), Kegel und Reichweite fallen
  weg. `sndLock` spielt den Suchton in Schleife und einmal den Einrastton.

### F85 — Standardbewaffnung wächst mit (v263) — gebaut in v264

**Festlegung (Silvio, 22.10.2026):** „Die ML-16 Laser kannst du komplett
durch Avengers ersetzen, sobald sie ingame verfügbar wird und die Apollo
zwei davon tragen kann. Es macht keinen Sinn eine wirkungslose Waffe
mitzuschleppen." Auch für NPC-Schiffe: „Gib ihnen doch einfach auch 2
Avengers sobald sie verfügbar wird und sie sie tragen können." Ebenso
Interceptor statt MX-50, sobald sie da ist („Fände ich gut, ja").

### F88 — Mission 17: die Galatea warpt durch ein Trümmerstück (v266) — gebaut in v267

**Befund (Silvio, 23.10.2026):** „Das passt optisch sehr gut. Was mir nur
aufgefallen ist, war dass die Galatea durch eines der Trümmer hindurch
rausgewarpt ist."

- Gebaut in v267: die Trümmer halten Abstand zu allen Großkampfschiffen
  der Mission mit fester Position (Galatea, Lilith, Cain).

### F97 — M18: vergrößerter Container verdeckt die Poseidon (v279)

**Befund (Silvio, 23.10.2026):** Bildschirmfoto der GTFr Kappa 3 mit
angedocktem Container: „Was soll das?"

- Silvio, 23.10.2026: „Die Poseidon hat unter ihrem Rumpf extra 2 Arme, mit
  denen sie Frachtcontainer halten kann und du hast sie einfach gedankenlos
  hinter den Frachtcontainer geschoben". Die Größe des Containers stimmt.
- Ursache: F92 (v276). Container stehen in der Liste der Kleinschiffe
  (`F3D_SMALL`), also bekamen sie einen eigenen Zeichenstapel nach den
  Großkampfschiffen — damit lagen sie nicht mehr im Tiefenpuffer ihres
  Frachters (F47) und vor ihm statt zwischen seinen Armen.
- Gebaut in v280: nach vorn kommen nur noch Jäger, Bomber und
  Rettungskapseln, nie Fracht und nie etwas, das an einem Schiff hängt.
  Dazu wird Fracht, die ein Schiff hält, immer direkt nach ihm gezeichnet —
  der vergrößerte Container war sonst vor die kleinere Poseidon sortiert.
  Szenario „v280 F97" (schlägt gegen v279 fehl).
- **Nicht behoben in v280** (Silvio, Bildschirmfoto: „du willst mich doch
  verarschen"). Erst mit den echten Modellen headless gerendert gesehen: der
  Container saß mit seinem eigenen Andockpunkt (beim VC3 auf seiner
  Unterseite) auf dem der Poseidon und ragte so nach oben in ihren Rumpf.
  In FreeSpace zeigt ihr Andockpunkt nach unten (POF: Normale -y, unter dem
  Rumpf bei den Armen); der Container wird dazu umgedreht und hängt darunter.
- Gebaut in v281: gehaltene Container sitzen wie mitfliegende Fracht
  (`tickRiders`) außen an ihrem Andockpunkt, unter dem Kiel oder oben drauf,
  je nach Richtung des Andockpunkts (`cargoSeat`); der Frachter fährt beim
  Andocken die passende Seite des Containers an. Im 3D-Bild ist ein
  gehaltener Container höchstens so dick, dass er zwischen ihre Arme passt
  (`f3dHeldThin`), damit der vordere Arm vor ihm liegt. Geprüft per Bild mit
  den echten Modellen von Poseidon, Chronos und Ma'at. `docksim` misst jetzt
  den Sitz statt das Aufeinandertreffen der beiden Andockpunkte. Szenario
  „v281 F97" (schlägt gegen v280 fehl).

### F96 — M18: Taurus springen nach rechts ein und schnappen nach links um (v278)

**Befund (Silvio, 23.10.2026):** „Die Taurus Frachter warpen nach rechts
gerichtet ein, snappen nach dem Warp in aber instant nach links um. Ich
dachte das wäre längst schon bei allen Schiffen behoben? Es nervt diesen
Fehler immer wieder beheben zu müssen. Schiffe sollen sich ganz normal
drehen und nicht instant die Richtung wechseln."

- Nachgelesen: F53 (v254) hatte das nur für eigene Schiffe gelöst. Ein
  feindliches Schiff, das zum Andocken einspringt, wurde im ersten Schritt
  ohne Wende umgesetzt.
- Gebaut in v279, für alle Schiffe: wer zum Andocken einspringt, kommt schon
  zum Ziel gewandt aus dem Wirbel; ohne Wende umgesetzt wird nur noch ein
  Schiff, das von Anfang an ohne Sprung im Feld steht (unsichtbar, erstes
  Bild). Szenario „FS1 M18 v279 F96" (schlägt gegen v278 fehl).

### F94 — M18: Container zu klein für die verbündeten Frachter (v276)

**Befund (Silvio, 23.10.2026):** „Die Frachtkisten sind zudem zu klein für
die ankommenden verbündeten Frachter"

- Entschieden (Silvio, 23.10.2026): die Container in dieser Mission größer
  zeichnen, passend zu den Frachtern (statt alle als VAC 4).
- Gebaut in v278: Einheit `big:N` vergrößert ein feindliches Schiff um den
  Faktor N; in M18 VC 3 ×3 und VAC 4 ×1,4.

### F95 — M18: Container docken falsch an der Satis an (v276)

**Befund (Silvio, 23.10.2026):** „die Frachtcontainer [docken] an den
Satis-Frachtern fehlerhaft an." Die Satis konnte im Original keine Container
aufnehmen (sie ist eher ein Transporter): „Daher würde ich empfehlen, die
Satis durch Ma'at Frachter zu ersetzen."

- Gebaut in v278: der Satis-Frachter der Taurus ist eine Ma'at. Die Satis
  der Gemini bleibt — sie nimmt keinen Container auf, sondern flieht nur.

### F93 — M18: Taurus-Frachter erscheinen ohne Sprung (v276)

**Befund (Silvio, 23.10.2026):** „Die Taurus Frachter sind bei mir gerade
ohne Warp-Animation ins Bild gesprungen."

- Nachgelesen: feindliche Frachter, Transporter, Container und Geschütze
  (`CAT_FIX`) stehen immer ohne Sprung im Feld (`noWarp`), auch wenn sie
  erst später kommen. Eigene Schiffe haben dafür `warpIn`.
- Gebaut in v277: `warpIn` gilt jetzt auch für diese feindlichen Einheiten;
  die Taurus tragen es. Szenario „FS1 M18 v277 F93" (schlägt gegen v276 fehl).

### F92 — Wirbel von Kleinschiffen liegt hinter einem Großkampfschiff (v275)

**Befund (Silvio, 23.10.2026):** „Subraumwirbel [werden] nicht immer auf
derselben Ebene gezeichnet wie die Schiffe, die aus ihnen herauskommen.
Hatte gerade eine Mission mit der Galatea. Bomber sind an der Position
eingewarpt wo die Galatea stand und die Bomber sind aufgetaucht, aber der
Subraumwirbel lag hinter der Galatea, was nicht sein darf. Kleinschiffe und
ihre Warptunnel müssen immer im Vordergrund liegen."

- Nachgelesen: Großkampfschiffe und Jäger mit Modell werden in einem
  gemeinsamen Stapel gezeichnet — erst alle Wirbel, dann alle Rümpfe. Der
  Wirbel eines Bombers lag so unter dem Rumpf der Galatea, der Bomber
  selbst davor.
- Gebaut in v276: ein Kleinschiff beginnt einen eigenen Stapel nach den
  Großkampfschiffen (`f3dFront`); auch die Wirbel schon verschwundener
  Kleinschiffe kommen nach den Rümpfen. Szenario „v276 F92" (schlägt
  gegen v275 fehl). Im Browser ansehen, die Cloud kann WebGL nicht zeigen.

### F91 — M8: Elysium kriecht nach zerstörtem Transporter an den Rand (v274)

**Befund (Silvio, 23.10.2026):** „In Mission 8, wenn der Transporter
zerstört wird und die Elysium bereits im Feld ist, fliegt die Elysium dann im
Schneckentempo an den rechten Bildrand und die Mission geht vermutlich erst
weiter, wenn sie herausgewarpt ist."

- Nachgelesen: „der Transporter" ist die Asmodeus 2 (F1). Ist sie weg,
  verliert die Elysium ihr Andockziel. Eine verbündete Elysium sprang dann
  nicht, sondern fuhr leer an den Rand (`leaveEmpty`), und die Mission
  wartete auf sie. Die Omega in M3 hatte dafür schon `jumpIfEmpty` (F56).
- Gebaut in v275: beide Elysium in M8 mit `jumpIfEmpty` — sie springen
  sofort. Szenario „FS1 M8 F91" (schlägt gegen v274 fehl).
- **Abgenommen (Silvio, 23.10.2026):** „In Mission 8 warpt die Elysium raus,
  wenn der Transporter zerstört wurde."

### F90 — Aspect-Lock zeigt auf die Rumpfmitte statt aufs Subsystem (v270)

**Befund (Silvio, 23.10.2026):** „Wenn der Spieler ein Subsystem anvisiert,
sollte der Aspect-Lock einer Rakete auch aufs Subsystem gehen und nicht auf
den Mittelpunkt des Schiffsrumpfes." Früher schon gemeldet (F44), „aber
vergessen wurde umzusetzen".

- Nachgelesen: Seit v253 (F44) misst `tgtTick` die Aufschaltung am
  Subsystem, und die Rakete fliegt es an (`60_effects.js`). Der Lock-Ring
  (`drawTargetMarks`, 72_target.js) wird aber weiter in der Mitte des
  Zielkastens gezeichnet — F44 war nur halb behoben.
- Status: offen, kommt mit dem nächsten Bau.

### F89 — Missionsziele und Meldungen sind unschön dargestellt (v266)

**Befund (Silvio, 23.10.2026):** „Was mir auch auffällt und mich schon seit
längerem stört ist wie Missionsziele und Meldungen dargestellt werden. Die
Galatea bei über 50% zu halten steht schon da bevor sie überhaupt im Feld ist
und überhaupt sind solche Objective-Meldungen unschön gelöst."

Weiter (Silvio, 23.10.2026): „Ich erhalte zum Beispiel mehrmals die
Aufforderung Clear the field, obwohl einfach nur eine neue Gegnerwelle
eingesprungen ist. Dann kommen noch Meldungen zu verfügbar gewordenen Waffen
und Schiffen hinzu. All das ist problematisch. Hinzu kommt noch, dass
Objectives nur oben links angezeigt werden, ich aber nicht weiß wie man das
verbessern kann, sodass man das Objective auch auf dem Spielfeld sieht."

Vorschlag (Ziel nur einmal ansagen, kein automatisches „Clear the field",
Marken an den Schiffen, Freischaltungen ans Missionsende) — **abgelehnt**:
„Nein, das ist nicht die Lösung." Begründung: „Ich finde die
Texteinblendungen generell unschön gelöst. Das passt einfach nicht zum Rest
des Designs. Das betrifft auch nicht nur diese eine Mission, sondern das
gesamte Spiel."

- Es geht also um das **Aussehen aller Texteinblendungen im ganzen Spiel**
  (Zielkarte, Zielzeile, Meldungsspalte), die nicht zum übrigen Design
  passen. Eigenes Thema, eigener Chat.

**Gestaltungsgespräch (Silvio, 23.10.2026):**

- Abgelehnt: größere Tafeln mit Überschrift über Wert („nur noch mehr
  Platzverschwendung auf der Spielfläche"), ebenso eine Textzeile in einer
  höheren oberen Leiste.
- Ziel: „ein einheitliches UI, bei dem der Spieler versteht was los ist,
  ohne es erst lesen zu müssen."
- **Meldungen über verfügbare Waffen und Schiffe entfallen ganz.** Auch kein
  Punkt am Knopf: ohne Trägerschiff kann man ohnehin nicht nachsehen.
- „Wird feindlich" zeigt das Spiel schon über Farbe; kein Text nötig.
- Ein zweiter Balken am Schiff (Countdown) ist neben dem HP-Balken nicht zu
  deuten. Verworfen.
- **Subsysteme:** eindeutige Symbole in den Zielbereich der Leiste, im
  Rand rechts neben dem Radar (nicht im Radarkasten selbst). Zustand per
  Farbe wie der HULL-Balken, zerstört rot und durchgestrichen. Gewählt:
  Waffen = Fadenkreuz (`my_location`), Sensoren = Radar (`radar`),
  Navigation = Kompass (`explore`), Kommunikation = Funkmast
  (`cell_tower`), alle aus Material Symbols (Apache-2.0, npm
  `@material-symbols/svg-400`, outlined). Triebwerke = eigene liegende
  Glockendüse im selben Linienstil (Vorlage `tools/f89_subsystem_icons_mock.js`).
  Abgelehnt für Triebwerke: Flamme, Rakete, Tacho, Doppelpfeil,
  Turbinensymbol.
- **Knöpfe:** Rechts neben dem Radar nur noch Systemknöpfe (Ton,
  Einstellungen, Pause). Schiffs- und Waffenwechsel rücken neben den
  SUPPORT-Knopf; der Zielbereich wird um diese Breite größer.
- **Symbolreihe über den Schiffen** (Subsystem-Symbole unter dem Namen)
  entfällt auf dem Feld; der Zustand steht in der Leiste, sobald man das
  Schiff anvisiert.
- **Ziel auf dem Feld:** Innen die Klammern nach Seite (rot Feind, grün
  eigene) — künftig auch an großen Schiffen. Außen herum ein zweiter Rahmen
  in der Farbe des Auftrags: **Blau = Protect, Rot = Destroy, Gelb =
  Disable** (der bestehende pulsierende Missionsrahmen, `drawMissionMark`,
  nur nach Auftrag gefärbt). Kulisse (`scenery`) bekommt weder Klammern noch
  Rahmen.
- **Boarding, Andocken, Evakuieren** (Silvio: „Der Spieler weiß nicht was
  gerade passiert"; Lichtpunkte allein abgelehnt):
  - Andocken ist nie Selbstzweck (z. B. Abschleppen) — keine eigene
    Darstellung.
  - Evakuieren: Rettungskapseln (Hermes, vasudanisch Ra) fliegen sichtbar in
    ein Schiff mit Hangar; Transporter haben keinen. Wird beim Missionsentwurf
    dazugestellt. **Testmission 90 gebaut (v268)**, Kapseln fliegen Kurven
    wie Jäger und unter dem Rumpf in den Hangar. Silvio prüft.
    Silvio (23.10.2026): „Die Orion hat eine Fighterbay, in der auch
    Hermes-Kapseln in Freespace hineinpassen“ — das gilt für alle Zerstörer.
    **v269:** Die Kapseln fliegen die echten Anflugwege aus den Modellen
    (`$bay`, alle sieben Zerstörer-Rümpfe, `tools/pof/mkbays.py`).
    Befund v269 (Silvio): „Die Kapseln müssten sich dieselbe Ebene wie die
    Orion teilen, auf der langen Landebahn entlang in die Öffnung für die
    Fighterbay fliegen. Im Moment fliegen sie einfach davor und werden dann
    halt kleiner." **v270:** Auf dem Anflugweg fliegen sie in der Tiefe des
    Zerstörers (Tiefe aus dem `$bay`-Weg), am Ende weiter durch die Öffnung
    hinein statt zu schrumpfen.
    **Abgenommen (Silvio, 23.10.2026):** „Punktlandung. Der Anflug ist
    korrekt, der Flug auf der Landebahn ist korrekt und der Einflug in die
    Fighterbay ist auch korrekt. Aus mehreren Blickwinkeln getestet."
  - Reparatur: Phidias-Reparaturdrohnen, die der Transporter aussendet und
    die mit einem Strahl reparieren. Nicht im MVPS-Paket. Modell
    `phidias.pof` liegt bei Silvio unter
    `C:\Desktop Portals\Roots Various Stuff\BPTDWID-999.0.0-DevEnv\bp\data\models`,
    Klänge des Reparaturstrahls im Nachbarordner `sounds`
    (`repairup.wav`, `repairloop.wav`, `repairdown.wav`). Silvio: gebaut für
    eine FS2-Cutscene, nicht vom Blue-Planet-Team; der Ersteller (Mike) hat
    sein OK gegeben. Die eigenen Strahlklänge gehören dazu. Eigener
    Baustein, noch zu bauen.
    **Entschieden (Silvio, 23.10.2026):** Die Drohnen reparieren nur große
    Schiffe (Kreuzer, Zerstörer u. ä.), nicht den Spieler. Sie ersetzen das
    bisherige Anlegen des Transporters zur Reparatur.
    **Entschieden (Silvio, 23.10.2026):** „Man kann die Drohnen und den
    Transporter, dem aus sie gesteuert werden, abschießen. Schießt man den
    Transporter ab, fliehen die Drohnen an den nächstgelegenen Bildrand rechts
    oder links. Schießt man auf die Drohnen machen sie weiter bis entweder alle
    zerstört wurden oder die Reparatur abgeschlossen ist. Ist die Reparatur
    abgeschlossen, fliegen sie zurück zum Transporter und der warpt dann raus."
    **Entschieden (Silvio, 23.10.2026):** Die Reparatur ist abgeschlossen, wenn
    der Rumpf wieder voll ist; das Tempo legt die Mission fest. Den Fortschritt
    zeigt der Rumpfbalken.
    **Entschieden (Silvio, 23.10.2026):** Immer dieselbe Menge, 10 Drohnen. „Die
    Drohnen fliegen den Rumpf des zu reparierenden Schiffes ab, vorzugsweise
    die Stellen, die Schadenszeichnungen haben."
    **Entschieden (Silvio, 23.10.2026):** Eine Schadenszeichnung verblasst unter
    dem Strahl, bis sie verschwunden ist; dann fliegt die Drohne zur nächsten.
    „Die Drohnen sollten dasselbe Flugverhalten wie Jäger und Bomber haben,
    damit ihre Bewegungen realistisch aussehen."
    **Entschieden (Silvio, 23.10.2026):** Strahl und Effekte aus den fertigen
    Bildern unter `bp\data\effects\phidias` (RepairCore, RepairGlow, RepairHaze,
    Particle_Repair …; goldgelb).
    **Entschieden (Silvio, 23.10.2026):** Mikes Bilder kommen wie die Modelle
    nicht ins (öffentliche) Repo, sondern als ZIP auf den Server. Modell in
    `bp\data\models`, Texturen in `bp\data\maps\phidias`.
    **Entschieden (Silvio, 23.10.2026):** Sind alle zehn Drohnen abgeschossen,
    bevor die Reparatur fertig ist, springt der Transporter weg; die Reparatur
    gilt als gescheitert, die Mission kann darauf reagieren.
    **Entschieden (Silvio, 23.10.2026):** Nur der Rumpf wird repariert, keine
    Subsysteme; ein lahmgelegtes Schiff bleibt lahmgelegt.
    **Entschieden (Silvio, 23.10.2026):** „Die Drohnen [sind] nicht größer als
    Jäger … Sie sollten höchstens ein Drittel so groß sein wie Jäger."
    Gilt nur, falls die Originalgröße nicht kleiner als ein Jäger ist. Gemessen
    (phidias.pof): rund 16,5 m lang, so groß wie eine Ulysses (16 m). Also gilt
    die Drittel-Regel. **Silvio danach: 10 Meter, „sonst wirds evtl zu klein".**
    - Gebaut in v275 (`64_repair.js`, Testmission 91). Einheit
      `repair:'A1', repPct:N` am Transporter, Auslöser `repariert` und
      `reparaturGescheitert`. Der Strahl kommt aus der Nase der Drohne.
      Modell, Bilder und Klänge als ZIP für den Server.
      **Abgenommen (Silvio, 23.10.2026):** „Sieht sehr gut aus. Die Phidias
      reparieren den Kreuzer, der Sound spielt korrekt ab und sie fliegen
      auch realistisch."
  - Boarding: Lichter-Idee verworfen (Elysium und Isis haben keine sichtbaren
    Lichter). **Entschieden (Silvio: „Das ist genial"):** Solange der
    Transporter anliegt, wechseln die vier Ecken der roten Feindklammern des
    Zielschiffs nacheinander auf Grün — jede Ecke ein Viertel; alle vier grün
    = gekapert. Gehört ins Boarding selbst (M4, M8, M11 enden alle mit
    `kapern`), kein Umbau der Missionen.
- **Auftragsliste** (Silvio: in FreeSpace links im HUD; aber kein Platz im
  Gefecht und keine eigene Taste, das Spiel wird mit der Maus gespielt):
  **entschieden** — die Liste aller Aufträge mit Stand (offen, erfüllt,
  verfehlt) steht im **Pausebildschirm**. Im Gefecht sprechen die Rahmen an
  den Schiffen. **Die Zielzeile oben links entfällt ganz** (Silvio: „Ja,
  macht Sinn. Zudem sieht man Gegner in der Regel ja auch auf dem Radar.").
  Aufträge ohne Schiff (alle Gegner vernichten) brauchen im Gefecht keine
  Anzeige: die Gegner tragen ihre Klammern und stehen auf dem Radar.
- Idee für später (Silvio): eine Trainingsmission, die dem Spieler alle
  diese Feinheiten zeigt.
  **Zurückgestellt (Silvio, 23.10.2026):** „Die Trainingsmission kommt erst,
  wenn der FS1, STR und FS2-Ark komplett sind."
- **Flucht/Absprung:** Sprungwirbel vorab verworfen (widerspricht der
  FreeSpace-Mechanik). **Entschieden** (Silvio): wie beim Boarding — die vier
  Ecken der Klammern des fliehenden Schiffs werden nacheinander **grau**,
  alle vier grau = sie springt. Die Klammern **pulsieren**, schneller je
  knapper, damit es nicht übersehen wird. Ersetzt die Countdown-Zeile oben
  rechts. (Hinweis: das Grau für zerstörte, anvisierte Subsysteme in
  `drawTargetMarks` erscheint praktisch nie, weil `tgtTick` die Auswahl im
  selben Moment löscht.)
- **Missionsuhren:** heute nur in den alten Missionen 69, 70, 75, 79, aber
  das FS1-Finale (Lucifer im Subraum) braucht eine. **Entschieden:** eine
  Uhr, die an einem Schiff hängt (die Lucifer verlässt den Subraum), zeigt
  sich wie eine Flucht — graue, pulsierende Ecken an diesem Schiff. Ecken
  außerhalb des Bildes werden **nicht** an den Rand verschoben (Silvio: „Man
  muss nicht alle Ecken sehen"; Gesamtansicht mit Z oder Y). Eine laufende
  Uhr steht zusätzlich in der Auftragsliste im Pausebildschirm.
- Subsystem zerstört: der Text „… DESTROYED" am Schiff entfällt; der Zustand
  steht in der Leiste (Symbole oben).
- Ebenfalls abgelehnt: Ring, der sich beim Boarding füllt; nur Lichtpunkte
  für Boarding/Evakuieren; Symbole Schild/Explosion/Stecker für die Aufträge;
  Sprungwirbel vor dem Absprung; „die Mission schreibt es in ihr Ziel" (es
  gibt keine Missionsbesprechungen, und lange Formulierungen sollen weg).
- Beim Abgleich am 23.10.2026 gefunden und danach entschieden:
  1. ~~Rückmeldung bei erfülltem/verfehltem Auftrag~~ — **entschieden:** der
     Stand (erfüllt, verfehlt, teilweise) steht in der Auftragsliste im
     Pausebildschirm; auf dem Feld erlischt der Auftragsrahmen, sonst
     nichts. Die Zielkarte entfällt.
  2. ~~Missionsmeldungen~~ — **entschieden:** Wirkung `meldung` und die
     übrigen Spalten-Meldungen (ENEMY COMMS DOWN, YOUR COVER IS BLOWN, BOSS
     DISARMED, „… FITTED", „… ASSIGNED", Refit) erscheinen nur noch als
     Protokoll unter der Auftragsliste im Pausebildschirm; die Meldungsspalte
     entfällt. Dazu (Silvio): **jede losgeschickte Rettungskapsel ist
     automatisch ein Schutzobjekt** und trägt den blauen Rahmen.
  3. ~~Die übrigen Texte am Schiff~~ — **entschieden:** alle entfallen.
     Sichtbar ohnehin: SCAN COMPLETE (Scanring), TAGGED (gelbe Markierung),
     IMPACT und REACTOR DESTROYED (Explosion), HULL REPAIRED/REPAIRS
     COMPLETE (Rumpfbalken), TARGET CANNOT JUMP (Kompass in der Leiste rot).
     Ins Protokoll im Pausebildschirm: RESCUED, DELIVERED, LEFT EMPTY, CARGO
     LEFT BEHIND, TARGET ESCAPED, NO CARGO. Punkte („+1 …", „+N RETURNED"):
     der Stand steht im Punkte-Kasten der Leiste.
- **Alle Punkte entschieden (23.10.2026).** Nächster Schritt: bauen.
- **Breite des Zielbereichs (Silvio, 23.10.2026, beim Bau von Schritt 1):**
  Die zwei Knöpfe brauchen neben SUPPORT so viel Platz, wie sie rechts frei
  machen; der Zielbereich wurde dadurch nicht breiter. Entschieden (B): die
  Waffennamen in PRIMARY und SECONDARY eine Spur kleiner, beide Felder etwas
  schmaler, kein Name wird gekürzt; die gewonnene Breite geht an den
  Zielbereich. Abgelehnt (A): je 25 Punkte schmaler, weil dann z. B.
  Prometheus R und S gleich aussehen („PROME…").
- **Auftragsrahmen in den Missionen (Silvio, 23.10.2026):** nur M1 bis M17
  bekommen sie, alles danach wird ersetzt. Zu scannende Ziele (M7) brauchen
  keinen Rahmen: der Scanring zeigt sie. **v273:** Rahmen ergänzt in M1
  (Orff), M3 (Bast, Ma'at, Omega), M4 (Omega gelb bis lahmgelegt, Comet,
  Intelligence 1), M5 (Plato), M6 (Galatea), M9/M10 (Cargo Alpha, Beta,
  Gamma), M11 (Depot-Container), M16 (Asimov), M17 (Galatea).
- **v273 (Schritt 2) gebaut:** Klammern an jedem Schiff (rot Feind, grün
  eigene, nie Kulisse), Rahmen in Auftragsfarbe, Kapseln automatisch blau,
  Boarding-Ecken grün, Flucht-Ecken grau und pulsierend — auch für Schiffe,
  die zum Rand fliehen und dort springen (Bast, Ma'at, Omega, Asmodeus), und
  für eine Uhr an einem Schiff (Wirkung `timer` mit `Sekunden|Text|Kennung`).
- **Neutrale Container (Silvio, 23.10.2026):** behalten ihre rosa Klammern
  (die FreeSpace-Farbe für Neutrale). Testlauf M4 bis M17 mit v273: „sieht
  alles sehr gut aus".
- **Beschriftungen am Schiff (Silvio, 23.10.2026, vor Schritt 3):**
  - der Schiffsname bleibt
  - die Entfernung am Ziel fällt weg
  - der Name des Subsystems fällt weg; stattdessen zeigt eine Klammer oben
    im Radarbereich der Leiste, welches Subsystem anvisiert ist
  - DISABLE / PROTECT / DESTROY bleiben vorerst
  - LOCKED fällt weg („man sieht ja dass es locked ist, wenn der Ring sich
    nicht mehr bewegt")
- **v274 (Schritt 3) gebaut:** Zielkarte, Zielzeile, Meldungsspalte,
  Countdown-Zeile, Texte an Schiffen und Ticket-Texte sind weg; Meldungen
  über freie Waffen und Schiffe entfallen ersatzlos. Der Pausebildschirm
  zeigt die Aufträge mit Stand, die Missionszeit, eine laufende Uhr und das
  Protokoll. Annahmen: ein neuer Auftrag, während der vorige noch offen ist,
  zählt den vorigen als erfüllt (M4: „Disable the Omega" → „Cover the
  Comet"); der Waffenwechsel wird nicht mehr angesagt (die Leiste zeigt
  ihn). Die Entfernung neben den Randpfeilen eines Ziels außerhalb des
  Bildes **bleibt** (Silvio, 23.10.2026: „Die Entfernungsangabe bei den
  Randmarkierungen bleibt, da hatte ich den alten Chat falsch verstanden.").

### F87 — Mission 17: Stationstrümmer aus dem Karnak-Modell (v264) — gebaut in v265

**Wunsch (Silvio, 23.10.2026):** „Ebenso sollten Trümmer einer
vasudanischen Station herumtreiben" — „Können wir nicht einfach
Stationstrümmer nehmen? Wir haben doch das Karnak-Modell". Dazu: „wir
nutzen Modelle, nicht Sprites" und „Trümmerteile [haben] eine andere
Textur als intakte Modelle".

- Gebaut: eine Mission kann mit `wreck3d:{key, n}` ein Trümmerfeld aus den
  echten Trümmerteilen eines Modells verlangen (mit Trümmertextur wie beim
  Zerbrechen). Sie treiben langsam, liegen hinter allen Schiffen und
  explodieren nicht. Mission 17 nimmt 12 Teile der Karnak.
- v265 auf dem Server: das Karnak-Modell fehlte ganz (FSPort-MediaVPs,
  nie umgewandelt). Als ZIP nachgeliefert.
- **Befund (Silvio, 23.10.2026):** „es hat keine Trümmertexturen, sondern
  seine normalen Texturen. Hinzukommt, dass es zuviele Trümmer sind, die
  zwar herumschweben, aufgrund ihrer Menge aber wild ineinander schweben."
  Die Karnak-Trümmerteile tragen schon im FSPort-Modell die Stationstextur.
  Gewählt: im Spiel verbrannt einfärben — „die Trümmer [sind] recht groß
  und ich [möchte] nicht, dass es unecht oder verwaschen aussieht".
- **Gebaut in v266:** verbrannt (dunkler, rußig, ungleichmäßig, Lichter
  aus, Detail und Licht bleiben); jedes Stück höchstens einmal, höchstens
  5, mit Abstand, jedes in eigener Tiefe, gemeinsame Drift — sie ziehen
  hintereinander vorbei, nie durcheinander.

### F86 — Mission 16: die Shivaner ignorieren die Asimov (v263) — gebaut in v264

**Befund (Silvio, 22.10.2026):** „sollte die Asimov nicht von den
Shivanern zerstört werden? Die Handvoll Jäger ignorieren sie
größtenteils." Dazu: „ich würde dennoch ein paar mehr Gegner einbauen,
denn du musst bedenken, dass unser Balancing nicht 1 zu 1 dem von
Freespace entspricht."

- Abgesprochen: 3 Scorpion und 2 Shaitan nach 3 s, 15 s später 2 Scorpion
  und 2 Shaitan, alle auf die Asimov; 10 s nach der Spomer 3 Scorpion auf
  die Spomer und 3 Shaitan auf die Asimov.
- **Gebaut in v264:** Mission-Feld `huntShare:1` schickt alle Jäger auf
  das Jagdziel (sonst die Hälfte, `HUNT_SHARE`).

### F83 — Antwort auf Verstärkung kommt von der falschen Seite (v262) — behoben in v263

**Befund (Silvio, 22.10.2026):** „Wenn ich in Mission 15 Verstärkung rufe,
kommen als Antwort vasudanische Hammer of Light Gegner und ich frage mich,
ob in Leveln, in denen es hauptsächlich um Shivaner geht, bzw. Shivaner die
Gegner sind, nicht eher Shivaner als Antwort reinwarpen sollten."

- Nachgelesen: Die Gegenbomber auf ein gerufenes Großkampfschiff
  (`sendCapBombers`) kommen immer aus der Fraktion der Mission
  (`currentFaction`), im FS1-Strang also Hammer of Light.
- Vorschlag: Die Antwort kommt von der Seite, die in der Mission die
  Gegner stellt (aus den feindlichen Einheiten der Mission gezählt).
- **Gebaut in v263:** `scriptFoe` zählt die feindlichen Schiffe der
  Mission, `sendCapBombers` nimmt deren Fraktion. Gilt für jede
  geschriebene Mission.

### F82 — Geschosse der Pinnacle schlagen einen Haken (v262) — behoben in v263

**Befund (Silvio, 22.10.2026):** „Waffenprojektile der Pinnacle fliegen
kurz nach rechts und machen dann einen Haken nach links. Ich vermute mal,
dass liegt an der neuen 3D-Darstellung wenn die Projektile die Ebene
wechseln."

- Nachgelesen: Seit v260 (F76 Schritt 3) startet ein Geschoss am Turm in
  dessen Tiefe und steigt in 10 Schritten zur Spielebene auf
  (`shotsView`). Gezielt wird aber vom Turm in der Spielebene aus, nicht
  von dort, wo man ihn sieht. Je tiefer das Schiff und je weiter am Rand,
  desto weiter liegen beide auseinander; beim Aufstieg wandert das
  Geschoss im Bild nach außen, dann fliegt es zum Ziel. Die Pinnacle steht
  rechts und ist groß, daher der Haken nach rechts.
- Vorschlag: Geschoss startet dort, wo man den Turm sieht, schon in der
  Spielebene, und fliegt gerade.
- **Gebaut in v263:** Geschosse und Flak aller Großkampfschiffe starten,
  wo der Turm zu sehen ist (`capSeenPt`), und werden von dort gezielt.
  Der Aufstieg aus der Tiefe (v260, F76 Schritt 3) entfällt.

### F81 — Mission 14: zweiter Lucifer-Beam ohne Austritt, der Strahl wirkt abgeknickt (v260) — behoben in v261

**Befund (Silvio, 22.10.2026):** „Ich habe in Mission 14 noch etwas
festgestellt und zwar schaltet die Lucifer manchmal auf den gerade
inaktiven Beam um, aber nur einer wird mit Austrittseffekt am getroffenen
Objekt dargestellt, was dazu führt, dass der Beam abgeknickt wirkt sobald
er sein Ziel trifft."

- Vermutung (aus dem Code von v260, nicht im Bild nachgewiesen): Hinter dem
  Eintritt läuft der 3D-Strahl waagerecht in der Tiefe des Eintritts weiter
  (`f3dBeamEnds`: X und F mit derselben Tiefe), davor aber schräg vom Turm
  herab. Zwei Stücke mit verschiedener Neigung sehen im Bild wie ein Knick
  aus. Findet der zweite Strahl keinen Austritt am Modell, fehlt bei ihm
  auch die Austrittswunde.
- Mit F79/F80 zusammen bauen.
- **Behoben in v261:** Vermutung bestätigt. Der Strahl ist jetzt eine gerade Linie im Raum vom Turm durch das Schiff und weiter. Die Dicke des Schiffs an der Stelle wird einmal je Schuss gemessen und der Austritt jedes Bild auf diese Linie gesetzt, so dass auch sich bewegende Schiffe keinen Knick erzeugen. Jeder Beam hat seinen eigenen Ein- und Austritt. Prüfung: `fieldsim` „straight line“ (Abweichung 0).

- Silvio, 22.10.2026, nach dem Test von v261 (F79 bis F81): „Das sah jetzt
  richtig gut aus."

### Jumpnodes — Silvio erinnern, wenn es soweit ist

**Silvio, v237:** „Ich frage mich, ob wir die Freespace-typischen Jumpnodes
(runde Gittergrafik im HUD) einfügen sollen? Das sind keine physischen
Objekte, sondern wurden in Freespace immer nur angezeigt, um zu signalisieren
wo die System-Ein- und -aussprungpunkte sind." — **„Einverstanden. Erinnere
mich später bitte nochmal dran, wenn es dann soweit ist."**

Also: **entschieden ja, zurückgestellt.** Reine Anzeige, ein Gitterring im
Feld an den Ein- und Aussprungstellen, kein Modell und kein physisches
Objekt. Dran denken, wenn die ersten Missionen stehen — Silvio hat
ausdrücklich darum gebeten, erinnert zu werden.

### Missionen müssen auf jedem Weg enden können

Silvios Sorge, und sie ist berechtigt: **F13 war genau dieser Fehler.** In M68
saß eine Verlustschranke (`lostMax:0`) auf allen drei Ereignissen, die den
Nachschub abstellen und die Shivaner abziehen. Der Verlust der Setekh sperrte
damit alle drei dauerhaft — der Nachschub hörte nie auf und die Mission hatte
überhaupt kein Ende mehr.

Bei 100 Missionen ist das von Hand nicht mehr zu überblicken. Es braucht eine
Prüfung, die für **jede** Mission nachweist, dass von jedem erreichbaren
Zustand aus ein Ende erreichbar bleibt — auch nach einem Fehlschlag, auch nach
dem Verlust eines Schützlings. Die Prüfung liest `SCRIPT_WAVES` als Daten und
braucht **keinen Browser**, läuft also in Sekunden statt in Stunden.

- Status: vorgeschlagen, Silvios Entscheidung

### Die drei Familien der `warpsim`-Befunde

`warpsim` war **nie** ganz sauber. Auf v232 waren es 84 Befunde über alle 60
Missionen, und sie zerfielen in genau drei Familien. Silvio hat auf Vorlage
hin **alle drei** zur Behebung freigegeben (v232).

**Familie 1 — „pop" nach dem Sprung (23 Befunde, nur Jäger).** Ein Messfehler
der Prüfung, nicht des Spiels. `pop` verglich die Änderung des sichtbaren
Rumpfes mit der Geschwindigkeit **entlang der Nase** — und rechnete damit
weder die **Drehung** noch den **Bildrand** mit. Ein Jäger dreht sofort nach
der Ankunft, und am Bildrand ändert seitliches Ziehen sehr schnell, wie viel
von ihm im Bild liegt.

**Behoben in v233** (in `warpsim.js`, also ohne Spieländerung): gemessen wird
jetzt nur noch, **was der Trichterschnitt verdeckt** (`visCut`), gegen die
**eigene Bewegung des Schiffes quer zum Schnitt**. Der Bildrand spielt keine
Rolle mehr.

Dabei zwei Dinge gelernt, die festgehalten gehören:

- Meine erste Fassung berechnete die Toleranz aus dem **Abstand zum
  Schnitt** — und der springt mit, wenn der Schnitt springt. Die Prüfung
  hätte sich selbst entschuldigt. Aufgefallen nur, weil sie gegen eine
  absichtlich kaputte Kopie gestellt wurde (Schnitt springt 60 Punkte).
- **Nach** dem Sprung gibt es überhaupt keinen Schnitt: `fsPostClip()`
  existiert im Spiel nicht, `warpsim` hat nur vorsichtshalber danach
  gefragt. Alle 23 Befunde „after jump in" waren also ausnahmslos Bildrand
  und Drehung — nichts.

**Familie 3 — „stop" aus dem Stand (13 Befunde, Großkampfschiffe).** Ein
echter Fehler: keine Beschleunigung. Die Zahlen waren genau ihre
Marschgeschwindigkeit (`craten` 1,81 = 25 × `SMALL_SPD_ANCHOR` × `TEMPO_K`,
`cosobek` 2,18, `dehatshepsut` 1,09). Dazu passt, dass `fsExitSpeed()` für
einen Verbündeten **0** zurückgibt: das Bild bringt sie stehend aus dem
Strudel, und die Fahrt setzte sie im nächsten Bild auf voll.

**Behoben in v233:** neu `capAcc(o, want)` in `57_turrets.js`, 2,5 Sekunden
von 0 auf Marsch und ebenso zurück. **Alles**, womit ein Großkampfschiff
fährt, geht dadurch — die Fahrt zur Station, die Bahn, das Nachlaufen in der
Kehre —, damit nicht zwei Stellen verschiedene Geschwindigkeiten haben. Der
Schritt ist ihre eigene Marschgeschwindigkeit geteilt durch die Zeit, also
beschleunigt ein langsamer Rumpf sanft und ein schneller zügig, und beide
brauchen dieselben Sekunden.

Gemessen: erster Schritt 0,003 statt 0,725 (volle Marschgeschwindigkeit),
größte Änderung je Schritt 0,003 gegen die Grenze 0,35 von `warpsim`.

**Familie 4 — „pop" am Weltrand (1 Befund, v233) — geklärt, kein Spielfehler.**
Nach der kleineren Welt aus v233 meldete `warpsim` in M22:

```
pop  detyphon/V1  +524px of hull at once (1211 -> 1735) (after jump in)
```

**Nachgemessen, nicht vermutet** (`probe_world.js`, beide Fassungen, dieselbe
Mission):

| | v232 | v233 |
|---|---|---|
| `WX0` (linker Weltrand) | −1797 | **−660** |
| Typhon landet bei x | −181 | −181 |
| ihre Länge | 1735 | 1735 |

Ihr Trichter steht **0,6 ihrer Länge hinter ihr**, also bei −1222. Und
`fsWarp()` klemmt ihn in die Welt:

```js
const px = Math.max(WX0, Math.min(WX1, at.x + sg*f.x*G));
```

Auf v232 lag −1222 noch innerhalb der Welt — **und zwar nur zufällig**, weil
die Welt damals Platz für den Colossus freihielt. Auf v233 wird der Trichter
auf −660 gezogen, der Schnitt liegt 562 Einheiten zu nah an ihr, und so viel
Rumpf bleibt bis zum Ende des Sprungs dahinter liegen. Das sind die 524.

**Es ist aber nichts, was ein Spieler sehen kann, und das ist beweisbar:**
Der Schnitt wird höchstens auf den **Weltrand** gezogen. Der Rumpf, den er
dadurch zusätzlich verdeckt, liegt damit immer **jenseits des Weltrandes** —
und `camClamp()` hält `CAM.x` mindestens `WX0 + camHalfW`, der linkeste je
sichtbare Punkt ist also genau `WX0`. Die Klemmung kann nur Rumpf verstecken,
der ohnehin außer Sicht ist.

**Folge für die Prüfung, nicht für das Spiel:** `warpsim` meldet keinen „pop"
mehr, wenn der Schnitt am Weltrand hängt — mit der Begründung oben im
Quelltext. Das ist bewusst eine **enge, begründete Ausnahme** und keine
angehobene Schwelle. Gegengeprüft an der kaputten Kopie (Schnitt springt 60
Punkte mitten im Feld): die fällt weiter durch.

**Nebenbefund für den Missionsneubau:** Die Typhon in M22 landet **außerhalb
des Missionsgebiets** (x = −181) und ragt mit 1735 Einheiten weit über den
Weltrand hinaus. Das ist einer der hochskalierten Platzwerte — in einem Feld
von 800 Breite hieß x = −40 „gleich links draußen", bei vierfachem Feld sind
es −181. Beim Neubau gehört sie ins Feld.

**Familie 5 — der eine Befund, der auf v233 übrig blieb (M53) — behoben.**
`warpsim` meldete über alle 60 Missionen genau einen:

```
stop  codeimos/A2   speed 2.18 -> 0.44 px/tick (jump out)
      [0 0 0 0 2.18 0.44]  {lane, capV 2.18}
```

**Zwei Reproduktionsversuche von Hand waren glatt** — die Deimos auf
Marschfahrt (2,176 → 2,177 → 2,178 → … → 2,22) und stehend (0 → 0 → 0,01 →
0,02) —, also musste die Prüfung selbst sagen, was vorher war. Sie schreibt
jetzt den **Anlauf** (die letzten sechs Geschwindigkeiten) und bei
Großkampfschiffen **womit das Schiff beschäftigt war** neben den Befund. Das
gab die Antwort in einem Lauf: vier Takte still, ein Takt mit genau ihrer
Marschgeschwindigkeit, und dabei `{lane, capV 2.18}`.

**Ursache, und sie war in dem, was ich gerade gebaut hatte:** Bei einem
Halt rief `capLane()` `capAcc(o, 0)` — die Geschwindigkeit sollte
auslaufen. Der Schritt des Beschleunigers ist aber ihre Marschgeschwindigkeit
geteilt durch 2,5 Sekunden, also 0,0087 je Takt. Über einen Halt von vier
Takten bewegt das **nichts**: `capV` stand noch bei 2,17, und in dem Moment,
in dem die Bahn frei wurde, fuhr sie in **einem** Takt mit fast voller
Marschgeschwindigkeit los. Danach begann ihr Sprung hinaus, und dessen
Verlauf startet bei der **geglätteten** Geschwindigkeit (`_fvx`), die nach
vier Takten Stillstand noch bei 0,44 lag — das ist der gemeldete Sprung.

**Behoben in v233:** neu `capHalt(o)`. Steht ein Großkampfschiff, hält es
oder hat es keine Bahn, dann ist seine Geschwindigkeit **null** — nicht „läuft
langsam aus". Es ist die ehrliche Buchführung: Das Spiel bewegt es in diesen
Takten gar nicht. Beim Losfahren beschleunigt es dann aus dem Stand.

Gegengeprüft an einer Kopie mit dem alten Auslaufen: dort hält sie 2,167 und
fährt mit 2,176 in einem Takt los — der Befund. Mit `capHalt`: 0 und 0,009.

**Der abrupte Halt selbst bleibt**, wie das Spiel ihn immer gemacht hat: ein
Halt setzt ein Großkampfschiff auf der Stelle still, statt es zu bremsen. Das
ist eine eigene Sache und keine, die man beim Richtigstellen der Buchführung
mitändert.

**Familie 2 — „stop" beim Übergang (48 Befunde, nur Jäger) — offen, und auf
v233 nicht mehr zu sehen.** Auf v233 melden alle 60 Missionen keinen einzigen
davon mehr, **obwohl ich sie nicht angefasst habe.** Vermutlich hat die
Beschleunigungsrampe der Großkampfschiffe auch die Jäger beruhigt, die hinter
ihnen aus dem Strudel kommen — **sicher ist das nicht**, und deshalb bleibt
der Punkt offen, bis er gemessen ist. Eine Zahl, die besser aussieht, ist
keine Erklärung.

Der alte Text dazu, weil er die Lage beschreibt:
Beim Verlassen des Strudels geht der Jäger vom Bremsverlauf des Sprungs auf
das Flugmodell über, und dabei gibt es einen Knick: erlaubt sind 0,6
Bildpunkte je Takt Änderung, gemessen werden **0,71**.

**Warum nicht in v233 mitgebaut:** Es ist ein Zehntel Bildpunkt je Takt, und
die Ursache sitzt in einer Kurve, die sich **absichtlich in jedem Takt neu
anpasst** — `fsWarp()` rechnet `drift` aus der bisher geflogenen Strecke und
leitet daraus `v`, `Dk` und `c` ab, damit das Schiff am Ende des Sprungs
„ohne Halt weiterfliegt". Daran zu drehen, ohne vorher gemessen zu haben,
wie der Verlauf wirklich aussieht, riskiert das Aussehen jedes Einsprungs im
Spiel für ein Zehntel Bildpunkt. **Deshalb zuerst messen, dann bauen** — und
die Schwelle wird dabei nicht angehoben, das wäre das Anpassen einer
Erwartung an ein kaputtes Ergebnis.

**Und der eigentliche Schutz fehlt noch:** eine **Grundlinie** der
akzeptierten Befunde, je Eintrag mit Begründung, gegen die `warpsim` selbst
vergleicht. Solange die nicht steht, muss ein Mensch nach jedem Lauf
entscheiden, ob ein Befund neu ist — und genau so rutscht einer durch. Sie
wird erst angelegt, **wenn Familie 2 behoben ist**: eine Grundlinie, die
Rauschen festschreibt, das gleich darauf verschwindet, wäre schon beim
Anlegen veraltet.

---

### `warpsim`-Befunde in FS1 M1 bis M4 (gefunden v250, schon in v249)

Mit dem schnelleren `warpsim` erstmals gesehen, auf v249 und v250 dieselben:
- M1, M2, M3: der Flügelmann W1 bremst im Moment des Aussprungs ab.
- M3: die Omega steht nach dem Einsprung still, bevor sie anfährt.
- M14 (v257): ebenso der Transporter Ptolemy nach dem Einsprung, bevor er
  zum Andocken anfährt. Dieselbe Art wie bei der Omega, nicht neu.
- M14 (v258): die verbündeten Jäger (Valkyrie, Apollo) bremsen im Moment
  des Aussprungs am Missionsende — dieselbe Art wie W1 in M1 bis M3. In
  v257 sah `warpsim` das nicht, weil die Welle dort in seinem Lauf nicht
  endete.
- M4: Comet und Intelligence 1 stehen nach dem Einsprung still, bevor sie
  zum Andocken anfahren; dazu „wave did not end" (die Prüfung schießt die
  Subsysteme anders ab als ein Spieler — noch nicht untersucht).

Nicht von v250 verursacht. Silvio hat keinen davon gemeldet.
- Status: offen, zu prüfen

## Rümpfe, die FS3 für die Originalmissionen noch fehlen

Beim Lesen der Originalmissionen (`missions_read.py --klassen`): von den
**3844 Schiffen** in den 83 Missionen der drei Stränge sind **99 %** von
einer Klasse, die FS3 schon zeichnet. Silvio hat die zwölf offenen Klassen
alle entschieden (v233). Drei brauchen gar kein Modell, eine brauchen wir
nicht:

| Klasse | Entscheidung |
|---|---|
| SAC 2 | die SAC 3 steht dafür ein |
| SSG Rahu | „Das ist die SG Rahu. Volition hat hierbei einen Klassifizierungsfehler begangen und nie behoben. Das hab ich für FS3 gemacht, weil es ein Gasminer ist und keine Sentry Gun." → `gmrahu` |
| GTDr Amazon Advanced | „Ist das gleiche Modell wie die GTFr Chronos." |
| Karnak Reactor | liegt **innen** in der PVI Karnak, und in Stationen fliegen wir nicht hinein. **Mission str16 wird umgestaltet** statt der Rumpf gebaut. |

**Acht Rümpfe fehlen wirklich.** Silvio zieht die Modelle; bis sie da sind,
können die betroffenen Missionen nicht nachgebaut werden:

| Rumpf | Schiffe | gebraucht für | Quelle |
|---|---|---|---|
| GTI Polaris Extension | 23 | str13, str15 | ST:R |
| GTF Angel | 4 | str05 | ST:R |
| GTI Polaris Pylon | 3 | str13, str15 | ST:R |
| PVSC Imhotep | 1 | str02 | ST:R |
| PVI Karnak | 1 | str16 | ST:R |
| Terran Asteroid Base | 1 | str05 | ST:R |
| Vasudan Asteroid Base | 1 | str02 | ST:R |
| NTF Boadicea | 1 | FS2 SM1-02 | FS2 |

Die Boadicea ist der **Asteroid, in dem sich die Iceni versteckt** (zweite
FS2-Mission). Silvio: „Das Modell heißt Boadicea, wobei der Name ingame nie
fällt."

**Betroffen sind damit sechs Missionen** — str02, str05, str13, str15, str16
und FS2 SM1-02. Alle anderen 77 können aus dem heutigen Bestand gebaut
werden.

### Die Modelldateien der acht Rümpfe — aufgelöst (v234)

Silvio hat die FSPort-Grundtabelle nachgeliefert (`fs1/tables/tables/ships.tbl`,
128 Einträge). Damit sind **sieben der acht** Rümpfe auf eine Modelldatei
zurückgeführt — nicht geraten, sondern aus der Zeile `$POF file:` des
jeweiligen Eintrags gelesen:

| Rumpf | Modelldatei | Paket |
|---|---|---|
| GTF Angel | `Angel.pof` | `fsport-mediavps-4.7.2/mv_fsport_47x/data/models` |
| PVSC Imhotep | `imhotep.pof` | dasselbe |
| PVI Karnak | `karnak.pof` | dasselbe |
| GTI Polaris Extension | `dock01-terran.pof` | dasselbe |
| GTI Polaris Pylon | `dock02-terran.pof` | dasselbe |
| Vasudan Asteroid Base | `cheops.pof` | dasselbe |
| Terran Asteroid Base | `Base2R-01.pof` | **`MVPS-473/MV_Assets_T_2/data/models`** |
| NTF Boadicea | noch offen | braucht die FS2-Grundtabelle |

**Zwei Berichtigungen meiner früheren Aussagen:**

- Die fünf FS1-Rümpfe kommen **nicht aus ST:R**, wie oben in der Quellenspalte
  steht, sondern aus **FSPort**. Der entpackte ST:R-Ordner enthält nur Wracks,
  die Shivaner-Leiche und einen unsichtbaren Marker — keine Stationen. ST:R
  benutzt FSPorts Modelle mit.
- Die Terran Asteroid Base ist ein **FS2**-Modell (`Base2R-01`), nicht ein
  FS1-Modell. Ich hatte sie vorher fälschlich `navbuoy-terran.pof` zugeordnet;
  das war ein Lesefehler — jene Zeile gehört zum Terran NavBuoy.

**Ein Widerspruch, der Silvios Entscheidung braucht:** Die Tabelle gibt der
**GTDr Amazon Advanced** das Modell `Drone02.pof`. Silvio hatte gesagt, sie
sei „das gleiche Modell wie die GTFr Chronos" (das wäre `Chronos.pof`
beziehungsweise `freighter03`). Da sie eine *Drohne* ist (GTDr), passt
`Drone02.pof` zur Tabelle. Ein Modell wird für sie so oder so nicht neu
gebaut — es geht nur darum, welches Aussehen sie bekommt.

**Mechanismus, der vorher nicht festgehalten war:** MediaVPs ersetzen
Modelle **unter demselben Dateinamen**. Die Grundtabelle liefert also nur den
Namen; welche Fassung man bekommt, entscheidet der Ordner, in dem gesucht
wird. Belegt an den 118 vorhandenen Rümpfen: `HULLS` in `buildmodels.py`
nennt Retail-Namen (`Capital2V-01`, `Capital02`, `Corvette2R-01`,
`Fighter2V-03`) und holt sie aus `MV_Assets_V` beziehungsweise
`MV_Assets_S`. Silvios Sorge, über die Retail-Tabelle Retail-Modelle zu
bekommen, trifft daher nicht zu.

**Für neue Rümpfe bleibt es bei MVPS 4.7.3.** Silvio hat inzwischen auch
MVPS 5.0.2, davon ist aber nur `MV_Effects_1` entpackt — und die 118
vorhandenen Rümpfe stammen aus 4.7.3. Mischen würde heißen, dass die neuen
anders aussehen als die alten.

Die Zuordnung steht in der Tabelle `HULL` in `missions_read.py`, mit Silvios
Begründung je Zeile. Das Skript prüft **jeden** Rumpfnamen gegen `HULL_LEN`
im Spiel und schlägt an, wenn einer fehlt — die Tabelle kann also nicht
veralten, und ein neu dazukommender Rumpf wird dort eingetragen, nicht
geraten.

---

## Von mir bemerkt, nicht von Silvio gemeldet

Damit es nicht verloren geht. Nichts davon ist dringend.

### `warpsim`: verbündete Jäger bremsen beim Aussprung (v264)

Befunde der Art „stop … speed 5,85 -> 2,63 (jump out)" bei verbündeten
Jägern und Bombern, schon in v264 auf M14 und M15, in v265 auch auf M17.
Nicht von Mission 17 verursacht; noch nicht untersucht.

### Die Sterne gehen beim Wellenwechsel nicht mit der Blende weg (v231)

Seit v231 sind im Scheitel der Dunkelheit Hintergrund **und** Planeten ganz
weg (`drawNebula`, `drawBodies`). Die **Sterne** nicht — sie stehen dort als
einziges noch mit den 8 %, die die Blende offen lässt. Und weil `camSnap()`
die Kamera in `nextWave()` auf den neuen Spielerplatz setzt, verschiebt sich
ihre Ebene in diesem Bild.

Nachgerechnet, wie groß das ist: die Parallaxe der Sterne ist
`CAM_BASE_Z · par · STAR_PAR` = höchstens `0.35 · 1 · 0.05` = **1,75 %** des
Kamerawegs. Ein Sprung von 1000 Welteinheiten verschiebt sie also um 17
Bildpunkte, bei 8 % Helligkeit. Vermutlich nicht zu sehen, deshalb nicht
angefasst — eine Zeile wäre es (dieselbe wie in `drawBodies`).

### Drei Prüfungen in `fieldsim` hingen am Würfel (behoben in v234)

Beim Prüfen von v234 fiel `fieldsim` in drei aufeinanderfolgenden Durchläufen
**je an einer anderen Stelle** durch. Alle drei waren Schwächen der Prüfung,
nicht Fehler im Spiel — jeweils auf v233 **und** v234 gleich gemessen, hängen
also nicht an der Weltgröße:

**1. „v190: a bomb goes off over an area" — `midLess`.** Die Prüfung würfelte
einen von sechs NTF-Jägern. Seit v208 werden sie in echter Größe gezeichnet,
und bei zwei davon (Myrmidon, Ulysses) endet der Trefferkasten in 110
Einheiten Abstand **genau** auf dem äußeren Blastradius 80 — Abschwächung 0,
kein Schaden. Durchfallquote also etwa ein Drittel. Jetzt ein benannter Rumpf
(Hercules, reicht bis 73) statt eines gewürfelten.

**2. „v182: tears, not holes" — `inherits.`** Gelesen wurde die
Geschwindigkeit des **ersten** freien Teils und `vx > 0.5` verlangt. Ein Teil
verlässt den Riss aber entlang dessen Normale (`dmgEmit`:
`vx = svx + (n.x + q.x*k)*speed`), und die kann nach hinten zeigen — der
Wert war Glückssache, Durchfallquote etwa ein Drittel. Jetzt als
**Differenz** der mittleren `vx` zwischen stehendem und fahrendem Schiff über
300 Ausstöße, mit **demselben Würfel** für beide Messungen: der Ausstoßanteil
fällt heraus, übrig bleibt genau die weitergegebene Geschwindigkeit. Ergibt in
vier Läufen exakt 1,5. (Nur zu mitteln reichte nicht — über verschiedene
Würfel kamen 1,5 bis 1,94 heraus, weil in beiden Messungen andere Risse
feuerten.)

**3. „v169: M68 the Setekh jams" — `reinfOnButJammed`.** Verlangt wurde, dass
**nie** eine Nachschubstaffel kommt. Die Störung ist aber die Setekh selbst:
`jammerAlive()` sucht ein **verbündetes** Schiff mit `.jammer` und gibt auf,
sobald es tot ist oder auswarpt — dann kommt Nachschub völlig zu Recht. Sie
steht mitten in einer shivanischen Patrouille und hält die 4000 Ticks nicht
immer durch. Jetzt wird nur gezählt, **solange die Störung steht**, und der
Zeitpunkt ihres Endes mit ausgegeben (`theJamHeld`).

Alle drei sind gegen eine kaputte Kopie gestellt und fallen dort weiter durch:
ohne Abschwächung nach außen (1), ohne Weitergabe von `svx` (2), ohne die
Störsender-Sperre in `tickEvents` (3).

**Was daraus zu lernen ist:** eine Prüfung, die einen Rumpf, einen Zeitpunkt
oder eine Richtung **würfelt**, ist keine Prüfung, sondern eine Münze. Sie
wird irgendwann grün, wenn man sie oft genug laufen lässt — und genau das
untergräbt die Regel, dass bei roter Stufe nichts hochgeschoben wird. Wo
gewürfelt werden muss, gehört der Würfel festgenagelt oder über genug
Ausstöße herausgemittelt.

### `warpsim` war nicht wiederholbar — und das erklärt die verschwundene Familie 2

Beim Parallelisieren von `warpsim` (v236) nachgemessen, v232, Missionen 1–8:

| Lauf | Befunde |
|---|---|
| seriell | 4 |
| parallel | 7 |
| parallel, zweiter Lauf | 7, aber andere Schiffe |

Auch **zwei Läufe im selben Modus** unterscheiden sich. Es lag also nie an der
Parallelisierung: Flugbahnen, die Streuung beim Einsprung und die Größe einer
Nachschubstaffel kommen aus `Math.random()`, und jeder Lauf sah eine andere
Schlacht.

**Damit ist die „unerklärt verschwundene" Familie 2 erklärt** — die 48
Knicke bei der Übergabe von Jägern, die zwischen v232 und v233 weg waren,
obwohl nichts daran geändert wurde. Es war Streuung, kein Erfolg. Das war
hier als offen und ausdrücklich nicht als Erfolg eingetragen; die Vorsicht
war berechtigt.

**Behoben in v236:** der Würfel wird je Mission festgenagelt
(`WARPSIM_SEED`, Standard 1). Drei Läufe — zweimal parallel, einmal
seriell — kommen byteweise gleich heraus.

**Was dabei nicht gelöst ist:** ein Startwert sieht je Mission **einen**
Flugverlauf. Die Befunde, die nur bei anderen Zufallszahlen auftreten, sieht
`warpsim` jetzt nicht mehr — vorher sah es sie zufällig und unzuverlässig.
Wer breiter prüfen will, lässt es mit mehreren Startwerten laufen.

### `queueHolds()` steht zweimal da

In `30_waves.js` ist `queueHolds()` **zweimal** definiert (Zeile 665 und
671), mit demselben Inhalt. Die zweite gewinnt, es ist also harmlos — aber
eine der beiden ist ein Rest und sollte weg. Nicht in dieser Version
angefasst, weil sie an der Fehlerstelle lag und jede Änderung dort einen
vollen Prüflauf kostet.

### `warpsim` meldet bei M20 „wave did not end" — Eigenart der Prüfung

Steht auf v232 wie auf v233, ist also nichts Neues, und es ist **kein
Spielfehler**: In M20 „The Survivors" steht die Aten (K1) als **verbündetes**
Schiff brennend im Feld, und solange sie lebt, kommt Nachschub
(`zerstoert K1 → nachschub aus`). `warpsim` schießt aber nur **Gegner** ab —
Verbündete lässt es in Ruhe. Also stirbt die Aten dort nie, der Nachschub
hört nie auf, und die Welle endet nicht.

Im Spiel ist genau das die Aufgabe: sie ist nicht zu retten, und je länger
sie lebt, desto mehr Rettungskapseln kommen heraus. Das steht als Kommentar
an der Mission. Nicht zu verwechseln mit M68 (F13), wo die Welle **im Spiel**
kein Ende hatte.

### Weitere Bildfolgen ohne Grenze

`drawFxSmoke()` zeichnet den Rauch mit `fxFrame(...)` direkt, nicht über
`fxFire()`, und ist damit von der Zellengrenze aus F12 **nicht** erfasst.
Rauch ist eine weiche Struktur, bei der Vergrößerung weniger auffällt. Falls
Silvio bei großen Schiffen matschigen Rauch sieht, liegt es daran.

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
