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

Stand: v216 ist die spielbare Fassung; v218 liegt zum Test bereit.

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

- Status: gebaut, wartet auf Silvios Test im Browser

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

Lösungsrichtung: größere Quellbilder. Das vergrößert die gebaute
`game.html` (derzeit 28,8 MB), also ist abzuwägen.

- Status: offen, nicht dringend — erst nach dem seitlichen Auswarpen (F6)

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
