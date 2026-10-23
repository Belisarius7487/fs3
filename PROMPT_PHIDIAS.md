Lade den FS3-Skill und hänge das Repo Belisarius7487/fs3 an (Schreibzugriff, klonen nach /home/claude/fs3).

Aufgabe: die Phidias-Reparaturdrohnen. Was dazu schon festgelegt ist, steht in OFFENE_FEHLER.md unter F89, Punkt „Reparatur“ – nur diese Stelle lesen, sonst gezielt suchen. Nichts dazudichten.

Festgelegt ist bisher nur: Ein Transporter schickt Phidias-Drohnen aus, die mit einem Strahl reparieren. Mehr nicht. Bevor gebaut wird, kläre mit mir, was noch offen ist – eine Frage nach der anderen, jeweils höchstens zwei Möglichkeiten mit Empfehlung. Erst nach meinem Ja bauen.

Material auf meinem Rechner (über die Ordnerfreigabe, nur lesen):
- Modell: C:\Desktop Portals\Roots Various Stuff\BPTDWID-999.0.0-DevEnv\bp\data\models\phidias.pof
- Klänge des Strahls im Nachbarordner sounds: repairup.wav, repairloop.wav, repairdown.wav
Die Phidias ist nicht vom Blue-Planet-Team; ihr Ersteller (Mike) hat die Nutzung erlaubt. Wie ein Modell ins Spiel kommt, steht in CLAUDE.md Abschnitt 10. Modelle gehören nicht ins Repo.

Grundsätze wie bei F89: keine Texteinblendungen im Gefecht, das Spielfeld wird nicht zugedeckt, keine neue Taste, Handys müssen weiter funktionieren. Alles aus dem gemeinsamen Formenvorrat (CLAUDE.md Abschnitt 6).

Bilder: Zeig mir vor jeder Lieferung ein Bildschirmfoto aus dem Spiel (tools/shot.js, keine HTML-Vorschau) und leg es mit den Änderungen im Ordner vNNN in fs3-claude-export ab.

Prüfen: ./checks.sh --fast und nur die fieldsim-Szenarien der geänderten Mechanik. Für jede neue Mechanik ein Szenario, das gegen die vorige Version fehlschlägt. Nie den vollen Lauf.

Nicht in diesem Chat: die Trainingsmission, F91 und die Entfernung an den Randpfeilen.

Fang mit der ersten offenen Frage an.
