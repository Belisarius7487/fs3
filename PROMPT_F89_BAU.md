# Prompt für den Bau-Chat zu F89 (Texteinblendungen) und F90

Diesen Text in einen **neuen Chat** im Projekt „Browsergame FS3" kopieren.

---

Lade den FS3-Skill und hänge das Repo Belisarius7487/fs3 an (Schreibzugriff,
klonen nach /home/claude/fs3).

**Aufgabe:** Baue die Neugestaltung aller Texteinblendungen (F89) und behebe
F90. Alles ist entschieden. Die vollständige Festlegung steht in
`OFFENE_FEHLER.md` unter **F89** und **F90** — diese beiden Abschnitte ganz
lesen, sonst nur gezielt suchen. Nichts neu entwerfen, nichts dazudichten. Was
dort nicht steht oder unklar ist: mich fragen, eine Frage nach der anderen.

**Grundsatz:** Der Spieler versteht, was los ist, ohne lesen zu müssen. Im
Gefecht keine Texteinblendungen. Das Spielfeld wird nicht zugedeckt, keine neue
Taste, Handys müssen weiter funktionieren. Alles aus dem gemeinsamen
Formenvorrat (CLAUDE.md Abschnitt 6), Tahoma/Segoe UI, jeder Text durch thFit.

**Reihenfolge — je Schritt eine Version, einzeln liefern, ich teste dazwischen:**

1. **Leiste.**
   - Schiffs- und Waffenknopf rücken neben den SUPPORT-Knopf. Rechts vom
     Radar bleiben nur Ton, Einstellungen, Pause.
   - Der Zielbereich wird um die gewonnene Breite größer. In seinen rechten
     Rand (nicht in den Radarkasten) kommen die fünf Subsysteme des
     anvisierten Schiffs als Symbole, eingefärbt wie der HULL-Balken,
     zerstört rot und durchgestrichen.
   - Symbole: Material Symbols outlined (npm `@material-symbols/svg-400`,
     Apache-2.0, Lizenzhinweis ins Repo): Waffen `my_location`, Sensoren
     `radar`, Navigation `explore`, Kommunikation `cell_tower`. Triebwerke:
     die selbst gezeichnete liegende Glockendüse. Vorlage für alles:
     `tools/f89_subsystem_icons_mock.js`.
   - Die Symbolreihe über den Schiffen auf dem Feld entfällt.
   - F90: der Lock-Ring sitzt auf dem anvisierten Subsystem, nicht in der
     Rumpfmitte.

2. **Klammern und Rahmen auf dem Feld.**
   - Innen die Klammern nach Seite: rot Feind, grün eigene, jetzt auch an
     großen Schiffen. Nie an Kulisse (`scenery`).
   - Außen der Auftragsrahmen (der vorhandene pulsierende Missionsrahmen) in
     der Farbe des Auftrags: blau beschützen, rot zerstören, gelb lahmlegen.
     Jede losgeschickte Rettungskapsel ist automatisch ein Schutzobjekt.
     Vorher prüfen und mir sagen, welche Zielschiffe heute noch keinen
     Rahmen bekommen.
   - Boarding: Solange der Transporter anliegt, werden die vier Ecken der
     roten Klammern des Zielschiffs nacheinander grün. Alle vier grün heißt
     gekapert. Betrifft M4, M8, M11 ohne Umbau der Missionen.
   - Flucht und ablaufende Uhr an einem Schiff (auch die Lucifer im
     FS1-Finale): Die Ecken werden nacheinander grau, die Klammern pulsieren,
     schneller je knapper. Ecken außerhalb des Bildes nicht an den Rand
     schieben.

3. **Texte weg, Pausebildschirm.**
   - Es entfallen: die Zielkarte, die Zielzeile oben links, die
     Meldungsspalte, die Countdown-Zeile oben rechts, alle Texte an Schiffen
     (Liste in F89) und die Ticket-Texte.
   - Meldungen über freigeschaltete Waffen und Schiffe entfallen ersatzlos.
   - Der Pausebildschirm bekommt die Auftragsliste mit Stand (offen, erfüllt,
     verfehlt, teilweise), eine laufende Missionsuhr und darunter ein
     kurzes Protokoll: Missionsmeldungen und Ergebnisse wie RESCUED oder
     TARGET ESCAPED.
   - Auf Handygröße prüfen.

**Bilder:** Zeige mir vor jeder Lieferung ein Bildschirmfoto aus dem Spiel
(headless gerendert, keine HTML-Vorschau) von dem, was sich ändert.

**Prüfen:** `./checks.sh --fast` und nur die `fieldsim`-Szenarien der
geänderten Mechaniken. Für jede neue Mechanik ein Szenario, das gegen die
vorige Version fehlschlägt. Nie den vollen Lauf.

**Nicht in diesem Chat:** Phidias-Reparaturdrohnen und die Trainingsmission.
Beide stehen in F89 und kommen später.

Fang mit Schritt 1 an. Sag mir in einem Satz, was du baust, dann bau.
