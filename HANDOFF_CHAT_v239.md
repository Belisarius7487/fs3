# FS3 — Handoff für ein Entwurfsgespräch (Stand v239)

Dieses Dokument ist für ein **Gespräch mit Claude im Chat** gedacht, nicht für
Claude Code. Es ist bewusst vollständig: der Chat sieht das Repository **nicht**
und hat kein Gedächtnis aus früheren Sitzungen. Alles, was hier nicht steht,
ist für ihn nicht vorhanden.

Geschrieben am Ende der Sitzung, die v234 bis v239 gebaut hat.

---

## 1. Was FS3 ist

Ein **Browserspiel** für die HLP-Community (hard-light.net), gebaut im Geist
von FreeSpace. Eine einzige HTML-Datei mit einem Skriptblock, aus Teilen in
`src/` zusammengesetzt. Es läuft auf einem Canvas von **800 × 500** Punkten,
davon oben **54** für die Leiste.

**Silvio** (belisarius) ist kreativer Leiter und entscheidet alles Inhaltliche.
**Claude** baut. Silvio hat **keine Programmiererfahrung**.

Das Spiel ist 2,5D: die Schiffe sind echte 3D-Modelle aus den FreeSpace-
MediaVPs, umgewandelt in ein Webformat, aber die Bewegung ist flach. Der
Spieler fliegt einen Jäger oder Bomber von der Seite gesehen.

**Umfang heute:** 125 Schiffsrümpfe, 80 geschriebene Missionen, 8 + 9
fliegbare Rümpfe in drei Kampagnenabschnitten, 19 Spielerwaffen,
15 Prüfstufen.

---

## 2. Wie gearbeitet wird — und was der Chat hier leistet

Die Arbeitsteilung, die Silvio mit diesem Handoff herstellen will:

- **Im Chat** wird **entworfen**: Missionen, Regeln, Spielgefühl, Dramaturgie.
  Ergebnis ist **Prosa** — eine Beschreibung, die ein Mensch lesen und
  beurteilen kann.
- **In Claude Code** wird **gebaut**: der Entwurf wird in die Datenstrukturen
  des Spiels übersetzt, geprüft und ins Repository geschickt.

Der Chat soll also **keinen Code schreiben**, sondern Entwürfe, die so genau
sind, dass Claude Code sie ohne Rückfragen umsetzen kann. Dazu muss der Chat
die **Sprache** des Spiels kennen — die steht in Abschnitt 6.

### Silvios Arbeitsregeln (gelten unverändert)

- **Normales Deutsch, keine Fachsprache.** Fachbegriffe erklären, wo sie
  unvermeidlich sind.
- **Bei Unklarheit fragen, bevor entworfen wird.** Den Umfang bestimmt Silvio.
- **Sagt Silvio „X geht nicht", ist das der Befund.** Nicht umdeuten in
  „vermutlich fehlt Y". Das hat schon einen kompletten Bauzyklus gekostet.
- **Keine Behauptungen über das Spiel, die nicht in diesem Dokument stehen.**
  Im Zweifel fragen. Falsche Annahmen kosten Bauzyklen.
- **Nicht wiederholt dasselbe vorschlagen.** Abschnitt 9 listet, was Silvio
  schon abgelehnt hat, mit seiner Begründung. Diese Vorschläge sind erledigt.
- **Keine langen Textwände.** Silvio hat das in dieser Sitzung mehrfach
  angemahnt. Kurz, konkret, entscheidungsreif.

---

## 3. Das große Ziel

**Rund 100 Missionen**, gebaut aus den Originalmissionen von FreeSpace 1,
Silent Threat: Reborn und FreeSpace 2. Danach erzeugt ein Zufallsgenerator
weitere Missionen.

Silvios Vorgaben dazu, wörtlich:

> Ich will ja keine 1zu1 Übersetzung der Freespace-Missionen, denn sowas wie
> Funk haben wir zum Beispiel nicht und möchte ich auch nicht einfügen. Mir
> geht es darum diese Missionen im Browsergame so gut wie möglich nachzubauen,
> aber eben so, dass der Charme unseres Browsergames erhalten bleibt. Wie ich
> früher schon mal sagte, wurden die jetzigen im Browsergame spielbaren
> Missionen bei der Änderung der Spielfläche einfach hochgezogen/hochskaliert,
> was oft zu langen Wartezeiten führt. Zudem sind diese nur eine rudimentäre
> Interpretation mit vielen Änderungen von den originalen Missionen.

> Aufgrund der Anforderung von 100 Missionen insgesamt müssen wir manche ggf.
> aufteilen. Ich hoffe, dass du kreativ genug bist, mir dabei helfen zu können
> ohne Missionen zu bauen, die bei Fehlschlägen oder anderen Ereignissen, dann
> nie mehr enden können.

**Die 80 heute vorhandenen Missionen sind irrelevant** (Silvio, v238) — sie
werden ersetzt. Sie dienen nur als Beispiel für die Sprache und das Maß.

**Die Originalmissionsdateien liegen im Repository** und sind gelesen: 30
FS1-Dateien, 22 ST:R, 35 FS2, dazu die Kampagnendateien. Die Trainingsmissionen
bleiben außen vor. Insgesamt **3844 Schiffe in 142 Klassen**; seit v235 hat
**jede Klasse** einen Rumpf im Spiel.

---

## 4. Maße, Zeit und Spielgefühl

| | |
|---|---|
| Bildschirm | 800 × 500, davon 54 oben für die Leiste |
| Spielfläche (befliegbar) | mindestens **7118 × 3968**, in jeder Mission gleich |
| Missionsgebiet | 800·K × 500·K, K richtet sich nach dem längsten Schiff |
| Takt | 100 Schritte je Sekunde |
| Maßstab | 3,75 Einheiten je Meter, bei großen Schiffen gestaucht |

**Spielfläche und Missionsgebiet sind zwei verschiedene Dinge.** Die
Spielfläche ist, was man befliegen kann und wohin die Kamera darf. Das
Missionsgebiet ist das innere Maß, in dem eine Mission ihre Schiffe hinstellt.
Seit v234 ist die Spielfläche in 66 von 80 Missionen genau gleich groß; die
14 Ausnahmen haben ein sehr großes Bauwerk darin (Knossos-Portal, Sathanas,
Arcadia, Karnak).

**Das ist für den Entwurf wichtig:** Schiffe brauchen Zeit, um Strecken zu
fliegen. Ein Großkampfschiff fährt langsam. Silvios Hauptkritik an den
bestehenden Missionen sind **lange Wartezeiten**, die durch das Hochskalieren
entstanden sind. Ein guter Entwurf sagt deshalb, **wo** etwas steht und
**wie lange** es dauern soll — nicht nur, was passiert.

---

## 5. Die drei Stränge (Ären)

Das Spiel kennt drei Ären, die sich **im Spiel unterschiedlich verhalten**:

| | FS1 | ST:R | FS2 |
|---|---|---|---|
| Beams | nein, außer Lucifer | nein, außer Hades | ja |
| Schilde der Flotte | erst ab Welle 9 | von Anfang an | von Anfang an |
| Shivanische Schilde | halten Primärwaffen fast ab (Faktor 0,25) | normal | normal |
| Avenger-Kanone | ab Welle 8 wirken Primärwaffen normal | – | – |
| Korvetten | **gibt es nicht** | **gibt es nicht** | ja |

**Beams gibt es in FS1 nur auf der Lucifer, in ST:R nur auf der Hades.**
Seit v237 wird in diesen Ären jedes große Beam-Mount durch eine **Railgun**
ersetzt und jedes Antijäger-Beam-Mount durch **Flak**. Die Railgun behält
genau die Wirkung des Beams, den sie ersetzt (Abweichung unter 1,3 %).

**Nur Schiffe der Ära kommen vor.** Gemessen an den Originalmissionen:
Sathanas 44 Schiffe in FS2, keines davor. Hecate 4 in FS2, keines davor.
Die Hades nur in ST:R. Fenris, Leviathan, Orion, Aten und Typhon in allen drei.

**Rufbarer Support je Ära** (seit v238/v239):

| | FS1 | ST:R | FS2 |
|---|---|---|---|
| GTC Fenris, GTC Leviathan, GTD Orion, PVC/GVC Aten, PVD/GVD Typhon | ja | ja | ja |
| GTC Aeolus, GTCv Deimos, GTD Hecate, GVC Mentu, GVCv Sobek, GVD Hatshepsut, GTVA Colossus | – | – | ja |

In FS1 und ST:R heißen die vasudanischen Schiffe **PV**, in FS2 **GV** — das
macht das Spiel von selbst.

**Noch nicht gebaut:** Die geschriebenen Missionen **setzen ihre Ära nicht**.
Alles läuft als FS2; die Ära ist nur über den Übungsmodus `?fs1=1` erreichbar.
Eine Mission braucht also ein Feld für ihren Strang. Das ist der nächste
Bauschritt und muss vor der ersten FS1-Mission passieren.

---

## 6. Die Sprache einer Mission

Eine Mission ist **Daten**, keine Programmierung. Sie hat Kopfdaten, eine
Liste von **Einheiten** (`u`) und eine Liste von **Ereignissen** (`ev`).

Ein vollständiges Beispiel — Mission 31, „The Uprising":

```
31: name 'The Uprising', fac 'ntf', o 'clear', live 4
  Einheiten:
    A1  Kreuzer, 1 Stück, Leviathan, verbündet, läuft bei 25 % Rumpf weg
    E1  Jäger, 2 Stück
    E2  Jäger, 1 Stück, wartet (kommt erst auf ein Ereignis)
  Ereignisse:
    wenn alle E1 zerstört  ->  Meldung "GTC Leviathan turning hostile"
    wenn alle E1 zerstört  ->  A1 wechselt die Seite
    wenn alle E1 zerstört  ->  E2 warpt ein
```

**Kopfdaten einer Mission:** `name` (Titel), `fac` (Hauptgegner: ntf, shivan,
hol), `o` (Ziel der Welle, meist `clear`), `live` (wie viele kleine Schiffe
gleichzeitig höchstens im Feld sind), `ziel` (Auftragstext), `hunt` (wen die
Gegner jagen), `mod` (Besonderheit: `nebula`, `emp`, `astfield`, `subspace`),
`scene` (Hintergrund), `portal` (Knossos-Portal im Feld), `fs1` (die
shivanische Flotte ist FS1).

**Eine Einheit** hat: `id` (Kennung), `c` (Klasse), `n` (Anzahl), `spr` (welcher
Rumpf genau, sonst würfelt das Spiel), `side:'ally'` (verbündet), `x`/`y`/`edge`
(wo sie steht), `wait:true` (kommt erst auf ein Ereignis), `still` (bewegt sich
nicht), `invuln` (unverwundbar), `guard` (Schützling — stirbt sie, ist die
Mission gescheitert), `escape` (sie flieht), `cross` (sie durchquert das Feld),
`dockTo` (sie dockt an eine andere an), `scan` (muss gescannt werden), `hp`
(abweichende Panzerung), `capture` (kann gekapert werden), `ram` / `capRam`
(Kamikaze), `noFlee`, `noFire`, `ghost` und etwa dreißig weitere Feinheiten.

**Klassen:** `fi` Jäger, `bo` Bomber, `cr` Kreuzer, `co` Korvette, `de`
Zerstörer, `sd` Superzerstörer, `fr` Frachter, `tr` Transporter, `in`
Installation, `sg` Geschützplattform, `fc` Fracht, `ast` Asteroid, `ep`
Rettungskapsel, `ic` Eis.

**Eine Kennung steht für eine Gruppe**, nicht für ein Schiff. Mehrere Einheiten
dürfen dieselbe Kennung tragen, damit **ein** Auslöser für alle gilt. Ein
Auslöser darf mehrere Kennungen mit `+` nennen.

### Die 15 Auslöser

`sek` (nach N Sekunden) · `zeit` (die Missionsuhr läuft ab) · `zerstoert` ·
`vernichtet` · `alleZerstoert` · `gerettet` · `verloren` · `verlaesst` (sie
verlässt das Feld) · `angedockt` · `anzahlUnter` (weniger als N übrig) ·
`rumpfUnter` (Rumpf unter N Prozent) · `subsystem` (ein Subsystem ist hin) ·
`entkommen` · `gescannt` · `erfuellt`

### Die 22 Wirkungen

`einwarpen` (eine wartende Einheit kommt) · `auftrag` · `seite` (Seitenwechsel) ·
`raus` · `heilen` · `jagd` · `nachschub` (an/aus) · `meldung` (Text einblenden) ·
`ende` · `kapern` · `ziel` (Auftragstext setzen) · `zielerfuellt` ·
`zielverfehlt` · `freigeben` · `ruf` · `timer` (Uhr starten) · `neuerAnlauf` ·
`zerstoeren` · `timerStopp` · `mehr` (der Gegner eskaliert) · `abzug` (der
Gegner zieht ab) · `kulisse`

### Drei Fallen, die eine Mission unspielbar machen

Eine Prüfstufe (`endsim`) fängt sie ab, aber **ein Entwurf sollte sie von
vornherein vermeiden**:

1. **Ein Ereignis wartet auf eine Kennung, die keine Einheit trägt.** Dann
   wartet es für immer und die Mission endet nie. Ein Tippfehler reicht.
2. **Nachschub angeschaltet und nie abgeschaltet.** Der Strom der Gegner endet
   nie, die Mission auch nicht.
3. **Eine Uhr gestartet und nie gestoppt.** Eine abgelaufene Uhr hält die
   Mission genauso offen wie eine laufende.

**Jede Mission muss auf jedem Weg enden können** — auch nach einem Fehlschlag,
auch wenn ein Schützling stirbt. Das ist genau die Sorge, die Silvio in
Abschnitt 3 geäußert hat, und sie hat schon einmal eine Mission zerstört
(M68, der Verlust eines Schiffes sperrte alle drei Ereignisse, die die Mission
beenden konnten).

---

## 7. Was der Spieler fliegt

Drei Abschnitte, jeder mit eigener Flotte:

| Abschnitt | ab Welle | Flotte | Rufbar |
|---|---|---|---|
| 1 | 1 | Hammer of Light, 8 vasudanische Rümpfe | vasudanisch |
| 2 | 31 | NTF, 9 terranische Rümpfe | terranisch |
| 3 | 61 | beide, in Reitern getrennt | beide |

Die Rümpfe schalten sich über Punkte frei. Die Bewaffnung wird im
**Rearm-Fenster** gewechselt; der Wechsel **füllt auf**, auch auf dieselbe
Waffe — daher der Name.

**19 Spielerwaffen** (9 primär, 10 sekundär), alle aus FS2: Prometheus R,
Subach HL-7, Mekhu HL-7, Akheton SDG, Morning Star, Prometheus S, UD-8 Kayser,
Circe, Maxim — Harpoon, Rockeye, Tempest, Tornado, EMP Adv., Infyrno,
Trebuchet, Stiletto II, TAG-C, Cyclops. Dazu zwei Eigenbauten: **Sidhe** (ein
Schrotkegel) und **Dante** (Geschosse mit Zeitzünder).

**Offen (F21):** Die Waffen haben **kein Ära-Feld**. In einer FS1-Mission
trägt die GTF Apollo heute Prometheus R, Subach und Harpoon — alles FS2. In
FS1 müsste sie **Avenger + ML-16 Laser** und **MX-50** tragen; das steht in
FSPorts Tabelle für 704 Rümpfe und ist damit belegt, nicht zu erfinden. FS1s
Primärwaffen: ML-16 Laser, Vasudan Light Laser, VLL-9, Disruptor, D-Advanced,
Akheton SDG, Avenger, Flail, Prometheus, Banshee, Railgun, S-Breaker, Leech
Cannon, UD-1 Volz. Sekundär: MX-50, Fury, Interceptor, Hornet, Phoenix V,
D-Missile, Havoc, Synaptic, Cluster Bomb, Stiletto, EM Pulse, Barracuda,
Tsunami, Serkr, Harbinger.

Silvio dazu: „Wir brauchen für jeden Arc vermutlich eigene Waffen. Für den
Random Arc kommen weitere hinzu wie jetzt schon die Dante und die Sidhe." und
„Für die neuen Waffen braucht es zudem neue Einträge für unsere bisherigen
Waffen."

Regeln, die für Waffen gelten: **Bomben nur für Bomber, Raketen nur für
Jäger.** Der Munitionsvorrat gehört zum Rumpf, die Waffe skaliert ihn.

---

## 8. Die Prüfungen

15 Stufen. 13 laufen in Sekunden, zwei spielen echte Missionen in einem
Browser ohne Fenster (Minuten). Für den Entwurf sind drei wichtig:

- **`swtest`** prüft jede Mission gegen die bekannten Auslöser und Wirkungen.
  Ein erfundener Auslöser fällt sofort auf.
- **`endsim`** prüft, dass jede Mission enden kann (die drei Fallen oben).
- **`fieldsim`** spielt die Missionen wirklich durch.

**Eine Regel, die teuer erkämpft ist:** Eine neue oder geänderte Prüfung wird
immer **gegen die kaputte Fassung gestellt**. Fällt sie dort nicht durch,
prüft sie das Falsche. Und: eine Prüfung muss **die Stelle prüfen, die etwas
benutzt**, nicht die Aussage selbst. In dieser Sitzung ist genau dieser Fehler
zweimal passiert.

---

## 9. Was Silvio abgelehnt hat — nicht wieder vorschlagen

### Das Rearm-Fenster hängt an einer Korvette, und FS1 hat keine

Das ist die **offene Frage**, an der die Sitzung endete. Heute gilt: das
Rearm-Fenster ist nur erreichbar, wenn eine **verbündete Korvette** im Feld
ist. In FS1 und ST:R gibt es keine Korvetten, das Fenster wäre dort nie
erreichbar.

Vier Vorschläge wurden gemacht, **Silvio hat alle vier verworfen**, wörtlich:

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

Der vierte Vorschlag (Rearm immer verfügbar) verliert die taktische Bedeutung
und ist damit auch abgelehnt.

**Die Anforderungen an jede weitere Lösung:**

1. **Kein Stillstehen.** Im Spiel ist es kaum möglich ruhig zu stehen; ein
   Andockvorgang fällt damit weg.
2. **Dieselbe Bedingung in jeder Ära.** Eine andere Klasse je Ära ändert den
   Preis des Rearms und verwirrt den Spieler.
3. **Nicht beliebig leicht zu erfüllen.**
4. **Nicht immer verfügbar.**

Zwei weitere Vorschläge lagen Silvio am Ende der Sitzung vor und sind **noch
nicht beantwortet**: ein **begrenzter Vorrat an Nachladungen je Mission**, oder
die Bindung an das **eigene Trägerschiff der Mission**.

### Weitere Festlegungen

- **Keine HTML-Vorschauen.** Es wird direkt ins Spiel gebaut und dort
  angesehen. Vorschauen sind zweimal gescheitert.
- **Kein Funk.** Silvio will ihn ausdrücklich nicht.
- **Der Spieler wird nie plötzlich umgesetzt.** Silvio: „Wie sieht das denn
  bitte aus, wenn der Spieler plötzlich umgesetzt wird? Nee sorry. Du denkst
  völlig am Spielprinzip vorbei."
- **Jede Mission hat dieselbe Spielfläche.** Nicht die Fläche an etwas
  anpassen, sondern umgekehrt.
- **Die Colossus wird nur so groß gezeichnet wie das Spielfeld breit ist** —
  sie ist ein Juggernaut, muss aber nicht größer als nötig dargestellt werden.
- **Jumpnodes** (die runde Gittergrafik, die in FreeSpace die Ein- und
  Aussprungpunkte markiert): **entschieden ja, zurückgestellt.** Silvio hat
  darum gebeten, daran erinnert zu werden, wenn die ersten Missionen stehen.
  Reine Anzeige, kein physisches Objekt.

---

## 10. Was als nächstes zu tun ist

In dieser Reihenfolge, so wie die Sitzung endete:

1. **Das Rearm-Tor entscheiden** (Abschnitt 9). Blockiert jede FS1-Mission.
2. **Die Ära an die Mission hängen.** Ohne das läuft jede Mission als FS2 und
   die ganze FS1-Mechanik bleibt unerreichbar.
3. **Die Waffen je Ära** (F21). Die FS1-Werte sind belegt.
4. **Die erste Mission entwerfen:** `sm1-01a` aus FS1, die erste richtige
   Mission der Kampagne (die drei `btm`-Dateien sind Trainingsmissionen und
   bleiben außen vor).
5. **Jumpnodes**, wenn die ersten Missionen stehen.

### Eigenheiten, die beim Nachbau zu beachten sind

- **FS1 beginnt ohne Schilde** für Jäger und Bomber. In den Originaldateien
  steht `no-shields` pro Schiff und **durchgehend**, nicht nur am Anfang: 19
  Schiffe in der ersten Mission, 40 in SM1-07, noch 23 in SM3-09.
- **In FS2s zweiter Mission versteckt sich die Iceni in der Boadicea** — einem
  Asteroiden, der unter Beschuss langsam auseinanderfällt, wodurch die Iceni
  zum Vorschein kommt und flieht. Das Modell ist dasselbe wie die Terran
  Asteroid Base.
- **Der Nebel** hat um das Schiff des Spielers eine kleine Tasche freier Sicht,
  die so groß ist wie die Waffenreichweite: was man nicht sieht, sieht einen
  auch nicht.
- **Kamikaze ist die Doktrin des Hammer of Light** und an einer Stelle
  geregelt.
- **Sechs Missionen** der Originale brauchen Rümpfe, die es seit v235 gibt:
  str02, str05, str13, str15, str16 und FS2 SM1-02. Mission str16 wird
  umgestaltet, weil der Karnak-Reaktor **innen** in der Station liegt und man
  in Stationen nicht hineinfliegen kann.

---

## 11. Offene Fehler, die noch im Spiel sind

Kurz, damit ein Entwurf nicht darauf baut:

- **F1** Dunkles Rechteck um Explosionen und Raketentrails.
- **F2** Subsystemnamen werden nicht immer angezeigt.
- **F3** Bast-Frachter sind nicht mehr zu beschützen.
- **F4** Halbtransparente Rechtecke am Anfang und Ende von Missionen.
- **F7** Sentryguns haben keine Markierung.
- **F8** M9: die Aten entkommt, wird aber als Fehlschlag gewertet (Silvio:
  „irrelevant").
- **F9** Bildschirm flackert auch ohne Treffer.
- **F21** Die Spielerbewaffnung kennt keine Ära (Abschnitt 7).
- **F22** Das Rearm-Fenster hängt an einer Korvette (Abschnitt 9).

Dazu zwei Dinge, die ich selbst gefunden habe und die für Entwürfe zählen:

- Die Prüfung der Sprünge (`warpsim`) war **nicht wiederholbar** — jeder Lauf
  sah eine andere Schlacht, weil Flugbahnen gewürfelt werden. Seit v236 ist
  der Würfel festgenagelt. Ein Startwert sieht aber nur **einen** Flugverlauf.
- Die Sterne gehen beim Wellenwechsel nicht mit der Blende weg.
