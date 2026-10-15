# FS1-Strang — Missionsentwürfe

Von Silvio abgesegnete Entwürfe für den Nachbau der FS1-Missionen.
Gebaut wird gesammelt, nicht Mission für Mission. Allgemeine Regeln für
alle Entwürfe (Silvio, 14.10.2026):

- **Höchste Wartezeit 30 Sekunden.** Jede Staffel, die auf den Abschuss
  einer anderen wartet, kommt spätestens nach 30 Sekunden.
- Kein Funkgeplauder, keine Schwierigkeitsstufen-Varianten.
- **Kaperziele** (Silvio, 15.10.2026): Ein feindliches Schiff, das gekapert
  werden soll, wird von Verbündeten nicht beschossen. Im Code v239 schon so:
  `escortSpares()` (`40_world.js`) schont `captureLock` und `disableTgt`,
  und `captureLock`/`keepAlive` verhindern den Tod bei 0 Rumpf. Beim Bau
  für M4, M9 und M10 im Spiel prüfen. Ausnahme M9: die **Shivaner** sollen
  die Ramses zerstören können, sonst fehlt die Gefahr.
- Waffenzeitpunkte: siehe `OFFENE_FEHLER.md`, F21. Nachladen nur beim
  eigenen Trägerschiff (F22).
- **Gebaut (v240):** Missionen 1 bis 3 ersetzen die alten Missionen 1 bis 3
  (Silvio, 15.10.2026). Die Hammer-of-Light-Flotte beginnt seitdem bei 4.
  Im FS1-Strang fliegt der Spieler nur die Apollo, bis eine Mission einen
  weiteren Rumpf bringt.
- **Gebaut (v249):** Missionen 4 bis 6 ersetzen die alten Missionen 4 bis 6
  (Silvio, 15.10.2026: die alten Missionen werden durch die neuen ersetzt).
  Die Hammer-of-Light-Flotte beginnt seitdem bei 7.
- **Gebaut (v253):** Die Originale 7 bis 10 und die neue Mission
  Shieldbreaker ersetzen die alten Missionen 7 bis 13 (Silvio, 15.10.2026).
  Die Hammer-of-Light-Flotte beginnt seitdem bei 14. Nummern im Spiel:

  | FS3 | Mission | Original |
  |---|---|---|
  | 7 | Pandora's Box | 7 |
  | 8 | Shieldbreaker (neu, nicht in FS1) | – (Waffenstand wie 7) |
  | 9 | The Hammer and the Anvil: Breakout | 8 (8A) |
  | 10 | The Hammer and the Anvil: Betrayal | 8 (8B) |
  | 11 | The Darkness and the Light | 9 |
  | 12 | First Strike: Disable | 10 (10A) |
  | 13 | First Strike: Salvage | 10 (10B) |

- **Nur Schiffe aus FS1, auf allen Seiten** (Silvio, 15.10.2026).
- **Wellen der Basilisken** (Silvio, 15.10.2026): in 9A, 9B und 11B zwei
  Wellen zu je 3; die zweite kommt erst, wenn die erste vernichtet ist.
- **Markierung besonderer Ziele** (Silvio, 15.10.2026): pulsierende
  Eckklammern um das ganze Schiff, in seiner üblichen Farbe (rot Feind, grün
  Verbündeter; die Farbe sagt nicht, was zu tun ist). Darunter das Wort
  DISABLE, DESTROY oder PROTECT, aber nur wie beim Namen eines Subsystems:
  wenn das Schiff Ziel ist oder Zeiger bzw. Schiff darauf zeigt. Am unteren
  Rand rückt das Wort hoch. Im Code: Einheit `mark:`, Wirkung `markieren`.

## Übersicht der ersten zehn Originale (abgesegnet)

| Nr. | Original | Teilen? |
|---|---|---|
| 1 | Eve of Destruction | nein |
| 2 | The Field of Battle | nein |
| 3 | Small Deadly Space | nein |
| 4 | Avenging Angels | nein |
| 5 | Out of the Dark, Into the Night | nein (Überraschung durch die Shivaner) |
| 6 | Paving the Way | nein |
| 7 | Pandora's Box | nein, weniger Container |
| 8 | The Hammer and the Anvil | ja: A Evakuierung, B letzte Angriffswellen |
| 9 | The Darkness and the Light | nein |
| 10 | First Strike | ja: A Taranis lahmlegen, B Andocken verteidigen |

Zehn Originale ergeben zwölf FS3-Missionen.

## Mission 1 — Eve of Destruction (abgesegnet, gebaut v240)

Vorlage `fs1/sm1-01a.fs2`.

- Start: Spieler (Apollo), Alpha 2 (Apollo, verbündet), Kreuzer Orff
  (Fenris, verbündet, Rumpfbalken) in Feldmitte.
- Nach 5 s Staffel 1: 2 Anubis.
- Staffel 2 (2 Anubis): sobald Staffel 1 vernichtet, spätestens nach 30 s.
- Staffel 3 (3 Anubis): genauso nach Staffel 2.
- Staffel 4 (3 Anubis): 3 s nach Vernichtung von Staffel 3, spätestens 30 s.
- Aufträge: „Orff beschützen", „alle Angreifer vernichten".
- Bewaffnung: ML-16, MX-50, Fury als Alternative. Kein Trägerschiff, kein
  Nachladen.
- Ende: alle vier Staffeln vernichtet → Erfolg. Orff zerstört →
  Fehlschlag, sofortiges Ende.
- Weggelassen: Funk, Zusatzstaffel auf „schwer", terranische Verstärkung
  am Schluss.

## Mission 2 — The Field of Battle (abgesegnet, gebaut v240)

Vorlage `fs1/sm1-02a.fs2`.

- Stehendes Asteroidenfeld als Kulisse.
- Start: Spieler und drei Apollo (verbündet).
- Nach 5 s Staffeln 1 und 2 (je 3 Anubis) von zwei Seiten.
- Staffel 3 (3 Anubis): sobald Staffel 1 oder 2 vernichtet, spätestens
  nach 30 s. Staffel 4 (3 Anubis): sobald die nächste fällt, spätestens
  nach 30 s.
- Sind nur noch drei Gegner übrig: das Ass (Seth) springt ein und jagt den
  Spieler. Es kommt **immer** (im Original nur bei gesundem Spieler).
- Aufträge: „alle Vasudaner vernichten", Bonus „das Ass abschießen".
- Kein Trägerschiff, kein Nachladen.
- Ende: alle Staffeln und das Ass weg → Erfolg.
- Weggelassen: Verstecken der Staffeln bis zur Annäherung (gibt es im
  Spiel nicht), Funk.

## Mission 3 — Small Deadly Space (abgesegnet, gebaut v240)

Vorlage `fs1/sm1-03a.fs2`.

- Start: Spieler und drei Apollo (verbündet), fünf vasudanische Container,
  3 + 2 Anubis.
- Zwei Vasudaner-Frachter (Bast, Ma'at) docken an je einen Container und
  fliehen damit. Auftrag: abfangen.
- Sobald ein Frachter weg oder zerstört ist: 2 weitere Anubis.
- Sind alle Gegner weg: Transporter Omega (GTT Elysium, verbündet,
  Rumpfbalken) springt ein, dockt an den vereinbarten Container, bleibt
  20 s, fliegt ab. Während er angedockt ist: zwei Wellen mit je 3 Anubis.
- Bonus: ein Container trägt den Waffenprototyp, Scannen erfüllt das Ziel.
- Ende: Omega springt ab → Erfolg. Omega zerstört → Fehlschlag.
  Frachter entkommen → Teilerfolg. Vereinbarter Container vorher zerstört
  → Omega fliegt leer ab.
- Schutz des Containers (Silvios Sorge, 14.10.2026): Gegner dürfen ihn nicht
  gezielt beschießen. Im Code v239 gilt das schon: Container stehen bei den
  Gegnern (`playerOnly()`), gegnerisches Feuer gilt nur dem Spieler und den
  Verbündeten, verbündetes geht hindurch. Nur der Spieler kann ihn treffen.
  Beim Bau im Spiel prüfen.

## Mission 4 — Avenging Angels (abgesegnet, gebaut v249)

Vorlage `fs1/sm1-04a.fs2`.

- Start: Spieler und drei Apollo (verbündet). In Feldmitte Omega (Elysium,
  terranische Verräter) und Rasputin (Isis, Vasudaner), begleitet von
  4 Verräter-Apollos, 2 Horus, 1 Osiris.
- Beide Transporter fliehen, sobald sie beschossen werden.
- Antrieb und Waffen der Omega zerstört → Comet (Elysium, verbündet,
  Rumpfbalken) springt ein, dockt an, kapert sie (Muster wie die
  Deimos-Kaperung: `subsystem` engines+weapons → `einwarpen`, `angedockt`
  → `kapern`). Gleichzeitig 2 Anubis.
- Bonus: Antrieb und Waffen der Rasputin zerstört → zweiter Transporter
  (Geheimdienst, Elysium) springt ein und kapert sie.
- Rasputin wird beschossen → 2 weitere Anubis.
- Lahmgelegte Transporter werden von Verbündeten nicht beschossen.
- Ende: Omega gekapert → Erfolg. Omega entkommen oder zerstört →
  Fehlschlag. Comet zerstört → Omega frei (`freigeben`), flieht →
  Fehlschlag. Rasputin nur Bonus.
- Weggelassen: die terranischen Verstärkungsstaffeln Delta und Epsilon.

## Mission 5 — Out of the Dark, Into the Night (abgesegnet, gebaut v249)

Vorlage `fs1/sm1-05a.fs2`. Erste Begegnung mit den Shivanern.

- Start: Spieler und drei Apollo, Plato (Faustus, verbündet, Rumpfbalken)
  quert langsam das Feld.
- Sofort 3 Anubis + 1 Osiris. Danach (spätestens 30 s) noch einmal
  3 Anubis + 1 Osiris zusammen mit dem Kreuzer Taurus (Aten, Vasudaner).
- Zweite Staffel weg → 3 Scorpion + 1 Shaitan springen ein, zerstören
  zuerst die Taurus, dann Angriff auf die Plato. Kurz darauf
  2 Scorpion + 2 Shaitan.
- Auftrag: die Unbekannten scannen. Bonus: einen abschießen (FS1-Regel:
  Primärwaffen gegen Shivaner-Schilde anfangs fast wirkungslos).
- **Die Plato ist zu retten** (Silvio, 14.10.2026: „Es muss schwer sein,
  aber möglich"). Im Original stirbt sie per Drehbuch immer — das gibt es
  bei uns nicht.
- Plato unter 20 % Rumpf → Rettungskapsel (Hermes, Rumpfbalken) startet und
  versucht, das Feld zu verlassen.
- Ende: Plato überlebt → Erfolg. Plato verloren, Kapsel entkommt →
  Teilerfolg (gelb). Beide verloren → Fehlschlag.

## Mission 6 — Paving the Way (abgesegnet, gebaut v249)

Vorlage `fs1/sm1-06a.fs2`.

- Start: Spieler und Alpha 2 (Apollo), Galatea (Orion, verbündet,
  Rumpfbalken, ihre Geschütze feuern mit) nahe am Feldrand Richtung
  Sprungpunkt.
- Abwechselnd, jede Staffel sobald die vorige weg ist, spätestens nach
  30 s: Bomber 1 (2 Shaitan), Jäger 1 (3 Scorpion), Bomber 2 (2 Shaitan),
  Jäger 2 (3 Scorpion), Bomber 3 (2 Shaitan). Erste Staffel nach 5 s.
- Alle Staffeln weg → Galatea springt ab.
- Auftrag: Galatea beschützen. Bonus: Galatea behält mehr als die Hälfte
  ihres Rumpfs.
- **Galatea ist das Trägerschiff** → erste Mission mit Nachladen.
- Ende: Galatea springt ab → Erfolg. Galatea zerstört → Fehlschlag.
- Schwierigkeit (Silvio, 14.10.2026): soll schwer sein. Gewählt wurde die
  mittlere Fassung; Silvios volle Fassung (je 4 Bomber, 3 Jägerstaffeln zu
  4) wurde wegen der schwachen FS1-Waffen gegen Shivaner-Schilde
  zurückgestellt. Nach dem ersten Test im Spiel ggf. hochschrauben.
- Weggelassen: der lange, leere Anflug.

## Mission 7 — Pandora's Box (abgesegnet, gebaut v253)

Vorlage `fs1/sm1-07a.fs2`.

- Start: Spieler und drei Flügelmänner, 6 Shivaner-Container (statt 29),
  3 Wachgeschütze Trident (statt 6).
- Auftrag: 3 Container scannen. Bonus: die Wachgeschütze zerstören.
- Nach dem dritten Scan: Container explodieren nacheinander (Falle),
  2 Staffeln zu je 3 Manticore und Kreuzer Taranis (Cain) springen ein,
  dazu laufend Scorpion-Nachschub.
- Neuer Auftrag: **60 s durchhalten** statt Entkommen (der Spieler wird nie
  aus dem Feld gesetzt). Nach 30 s zusätzlich 2 Dragons.
- **Ohne angezeigte Uhr** (Silvio, 14.10.2026). Die heutige Missionsuhr
  (`timer`/`zeit`) wird immer in der Leiste gezeigt — beim Bau braucht es
  eine unsichtbare Variante.
- Uhr abgelaufen → Nachschub aus, Uhr gestoppt, Shivaner ziehen ab →
  Erfolg.
- Verlorene Leben: wie überall, Mission läuft weiter bis Game Over.
- **Schockwellen** (Silvio, 15.10.2026, „spürbar"): jeder Container geht mit
  einer Schockwelle hoch, die stößt und schadet — nah dran etwa ein Zehntel
  der Hülle, alle sechs zusammen rund die Hälfte. Trifft auch Shivaner.

## Mission 8 (neu) — Shieldbreaker (abgesegnet, gebaut v253)

Nicht in FS1. Die Nachbesprechung von Pandora's Box und das Briefing von
The Hammer and the Anvil sagen, ein Stoßtrupp der 5. Flotte habe im
Ikeya-System Shivaner-Schildprototypen erbeutet. Das ist dieser Einsatz.

- Start: Spieler in einer Apollo mit **D-Advanced** in der ersten Bank,
  zwei Apollo-Begleiter. Drei Asmodeus-Frachter mit **je 2** Shivaner-
  Containern (die Asmodeus hat nur zwei Andockstellen), 2 Scorpions als
  Wache. Waffenstand wie Original 7.
- Auftrag 1: Container scannen, bis der richtige gefunden ist (fest: der
  zweite auf Asmodeus 2). Ab dem ersten Schuss auf einen Frachter fliehen
  alle drei; spätestens nach 90 s ohnehin. Die Begleiter schießen nicht auf
  die Frachter, bevor jemand anderes es tut.
- Auftrag 2: Antrieb und Waffen dieses Frachters zerstören. Vom Spieler
  zerstören lässt er sich nicht.
- Danach: eine Elysium springt nah ein, dockt an (12 s) und kapert ihn.
  Gleichzeitig Scorpion-Schwärme (4 × 2), die gezielt auf den Frachter
  gehen; deren Feuer kann ihn zerstören.
- Erste Elysium zerstört → zweite springt ein. Auch die zerstört →
  Fehlschlag.
- Frachter entkommen oder zerstört → Fehlschlag. Gekapert → Erfolg.
- Bonus: die beiden anderen Frachter zerstören.

## Mission 8 — The Hammer and the Anvil, geteilt in 8A und 8B (abgesegnet, gebaut v253 als 9 und 10)

Vorlage `fs1/sm1-08a.fs2`. Drei langsame Poseidon-Frachter (Theta) bringen
Schildtechnik aus der Station Cygni. **Jeder Frachter trägt einen
Frachtcontainer** (Silvio, 14.10.2026; im Original Cargo Alpha/Beta/Gamma,
TSC 2). Frachter zerstört → Container mit zerstört (bestehende Regel).
Gegner zielen auf Frachter und Container — anders als in M3 sind diese
Container **verbündet und angreifbar**; beim Bau prüfen, dass
`playerOnly()` (Container sonst nur vom Spieler treffbar) das nicht
verhindert.

**8A — Der Ausbruch**

- Start: Spieler und zwei Flügelmänner, Station Cygni (Arcadia) als Kulisse
  am Rand, drei Frachter mit Containern (Rumpfbalken) fliegen los.
- Sofort 2 Basilisk, danach 4 feindliche Vasudaner (2 Anubis, 2 Seth),
  dann 4 Basilisk, die gezielt auf die Frachter gehen. Jeweils spätestens
  nach 30 s.
- Alle Gegner weg → Frachter springen ab.

**8B — Der Verrat**

- Start: Spieler, zwei Flügelmänner, drei Frachter mit Containern,
  verbündete Vasudaner-Begleitung (3 Anubis, 2 Seth).
- Nach 15 s wechselt die Begleitung die Seite (`seite`): Hammer of Light,
  Angriff auf die Frachter.
- Danach Shivaner: 3 Scorpion, 2 Basilisk, 4 Basilisk (je spätestens 30 s).

**Abweichungen beim Bau (v253):** Die Station Cygni fehlt — im Spiel gibt es
keine verbündete Station als bloße Kulisse; eine Arcadia würde als Gegner
oder als Vasudaner-Kreuzer erscheinen. Die Container reiten auf den
Frachtern (`ride`) und sind verbündet und angreifbar.
- Alle Gegner weg → Frachter springen ab.

**Beide:** Ein Frachter mit Container entkommt → Erfolg. Alle drei →
Bonus. Alle verloren → Fehlschlag. Je etwa 2,5 Minuten.

## Mission 9 — The Darkness and the Light (abgesegnet, „schwer, aber probieren wir")

Gebaut v253 als Mission 11.

Vorlage `fs1/sm1-09a.fs2`.

- Start: Spieler und drei Flügelmänner, 6 Container des Hammer of Light
  (statt 16), Kreuzer Ramses (Aten, HoL), 2 Frachter Satis (statt 4),
  3 Seth als Wache.
- Nach 30 s oder sobald die Seth weg sind: 2 Anubis.
- Antrieb und Waffen der Ramses zerstört → terranischer Transporter springt
  ein, dockt an, kapert sie.
- Kurz nach Beginn: Shivaner-Kreuzer Taranis (Cain) mit 2 Scorpion springt
  ein und greift die Ramses an. Die Kaperung ist **schwer, aber möglich**
  (im Original per Drehbuch unmöglich).
- Depot zerstört → 2 Shaitan, kurz darauf 2 weitere.
- Frachter fliehen. Bonus: einen zerstören.
- Ende: Depot zerstört, Ramses gekapert oder verloren, Shivaner-Jäger weg →
  Taranis springt ab (`abzug`). Depot + Ramses gekapert → Erfolg. Ramses
  verloren → Teilerfolg.

## Mission 10 — First Strike, geteilt in 10A und 10B (abgesegnet, gebaut v253 als 12 und 13)

Vorlage `fs1/sm1-10a.fs2`. Spieler fliegt einen **Athena-Bomber mit
Stiletto** (vorgegebenes Schiff).

**10A — Lahmlegen**

- Start: Spieler (Athena), drei Athena, vier Valkyrie als Begleitschutz.
  Taranis (Cain) mit 3 Shaitan und 2 Scorpion.
- Auftrag: Antrieb und Waffen der Taranis zerstören, nicht den Kreuzer.
- Nach 30 s oder sobald die erste Gruppe weg ist: 4 Scorpion.
- Lahmgelegt und entwaffnet → Erfolg, Verbündete stellen das Feuer ein.
  Taranis zerstört → Fehlschlag.

**10B — Die Bergung**

- Start: dieselbe Aufstellung, Taranis bereits lahm und entwaffnet.
- Frachter Halkins (Chronos, Rumpfbalken) springt ein, dockt an, 25 s,
  dann `kapern`, beide springen ab. Die zwei gescheiterten Transporter des
  Originals fallen weg.
- Während des Andockens: 4 Basilisk, 2 Scorpion, 4 Basilisk.
- Ende: Taranis gekapert → Erfolg. Halkins zerstört → Fehlschlag,
  Shivaner ziehen ab. Taranis vom Spieler zerstört → Fehlschlag.

Je etwa 2 bis 2,5 Minuten.

Korrektur (Silvio, 15.10.2026): Der Transporter heißt im Original **Omega**
(GTT Elysium); McCarthy ist nur der Name eines Funkspruchs. Umgesetzt in v248.
