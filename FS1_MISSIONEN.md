# FS1-Strang — Missionsentwürfe

Von Silvio abgesegnete Entwürfe für den Nachbau der FS1-Missionen.
Gebaut wird gesammelt, nicht Mission für Mission. Allgemeine Regeln für
alle Entwürfe (Silvio, 14.10.2026):

- **Höchste Wartezeit 30 Sekunden.** Jede Staffel, die auf den Abschuss
  einer anderen wartet, kommt spätestens nach 30 Sekunden.
- Kein Funkgeplauder, keine Schwierigkeitsstufen-Varianten.
- Waffenzeitpunkte: siehe `OFFENE_FEHLER.md`, F21. Nachladen nur beim
  eigenen Trägerschiff (F22).

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

## Mission 1 — Eve of Destruction (abgesegnet)

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

## Mission 2 — The Field of Battle (abgesegnet)

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

## Mission 3 — Small Deadly Space (abgesegnet)

Vorlage `fs1/sm1-03a.fs2`.

- Start: Spieler und drei Apollo (verbündet), fünf vasudanische Container,
  3 + 2 Anubis.
- Zwei Vasudaner-Frachter (Bast, Ma'at) docken an je einen Container und
  fliehen damit. Auftrag: abfangen.
- Sobald ein Frachter weg oder zerstört ist: 2 weitere Anubis.
- Sind alle Gegner weg: Transporter McCarthy (Elysium, verbündet,
  Rumpfbalken) springt ein, dockt an den vereinbarten Container, bleibt
  20 s, fliegt ab. Während er angedockt ist: zwei Wellen mit je 3 Anubis.
- Bonus: ein Container trägt den Waffenprototyp, Scannen erfüllt das Ziel.
- Ende: McCarthy springt ab → Erfolg. McCarthy zerstört → Fehlschlag.
  Frachter entkommen → Teilerfolg. Vereinbarter Container vorher zerstört
  → McCarthy fliegt leer ab.
- Schutz des Containers (Silvios Sorge, 14.10.2026): Gegner dürfen ihn nicht
  gezielt beschießen. Im Code v239 gilt das schon: Container stehen bei den
  Gegnern (`playerOnly()`), gegnerisches Feuer gilt nur dem Spieler und den
  Verbündeten, verbündetes geht hindurch. Nur der Spieler kann ihn treffen.
  Beim Bau im Spiel prüfen.

## Mission 4 — Avenging Angels (abgesegnet)

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
