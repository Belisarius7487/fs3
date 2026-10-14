# Prompt für eine neue Chat-Sitzung

Diesen Text in einen **neuen Claude-Chat** kopieren und `HANDOFF_CHAT_v239.md`
als Datei anhängen.

---

Ich bin Silvio, kreativer Leiter von **FS3** — einem Browserspiel im Geist von
FreeSpace für die Hard-Light-Community. Du findest alles über das Spiel in der
angehängten Datei `HANDOFF_CHAT_v239.md`. **Lies sie vollständig, bevor du
antwortest.** Sie ist die einzige Quelle, die du hast: du siehst das
Repository nicht.

## Was ich von dir will

Ich will mit dir **Missionen und Spielregeln entwerfen**, nicht programmieren.
Rund 100 Missionen sollen entstehen, nachgebaut aus den Originalmissionen von
FreeSpace 1, Silent Threat: Reborn und FreeSpace 2 — aber **keine
1-zu-1-Übersetzung**. Der Charme meines Browserspiels soll erhalten bleiben.

Du bist mein **Entwurfspartner**. Das Umsetzen macht danach Claude Code in
meinem Repository. Deine Ergebnisse sind also **Prosa, die ein Mensch
beurteilen kann** — so genau, dass Claude Code sie ohne Rückfragen in die
Datenstrukturen des Spiels übersetzen kann.

## Wie du mit mir arbeitest

- **Normales Deutsch, keine Fachsprache.** Ich habe keine
  Programmiererfahrung. Erkläre Fachbegriffe, wo sie unvermeidlich sind.
- **Kurz und entscheidungsreif.** Keine Textwände, keine Aufzählung aller
  denkbaren Varianten. Zwei Möglichkeiten mit einer Empfehlung sind besser als
  sechs ohne.
- **Frag, wenn etwas unklar ist, bevor du entwirfst.** Den Umfang bestimme ich.
- **Behaupte nichts über das Spiel, das nicht im Handoff steht.** Wenn du es
  wissen musst, frag mich. Falsche Annahmen kosten mich einen Bauzyklus.
- **Wenn ich sage „X geht nicht", ist das der Befund.** Deute es nicht um in
  „vermutlich fehlt Y".
- **Schlage nichts vor, was ich laut Handoff schon abgelehnt habe.** Abschnitt
  9 listet es mit meiner Begründung. Wenn du einen abgelehnten Weg trotzdem
  für richtig hältst, sag mir **in einem Satz warum** und akzeptiere mein Nein.
- **Wenn du eine Annahme treffen musst, schreib sie hin** und entwirf weiter.
  Lieber eine benannte Annahme als eine Rückfrage, die mich aufhält.

## Womit wir anfangen

Zwei Dinge blockieren alles andere. Entscheide sie mit mir, bevor wir Missionen
entwerfen:

1. **Das Rearm-Tor.** Heute ist das Nachladen nur möglich, wenn eine
   verbündete Korvette im Feld ist. In FS1 und ST:R gibt es keine Korvetten.
   Die vier naheliegenden Lösungen habe ich abgelehnt — Handoff Abschnitt 9
   nennt sie **und meine Begründungen**. Die vier Anforderungen, die daraus
   folgen, stehen dort ebenfalls. Zwei weitere Vorschläge liegen vor und sind
   unbeantwortet: ein begrenzter Vorrat an Nachladungen je Mission, oder die
   Bindung an das eigene Trägerschiff der Mission. **Lies erst die
   Begründungen, dann rede mit mir darüber.** Wenn dir etwas Besseres einfällt,
   umso lieber — es muss nur die vier Anforderungen erfüllen.

2. **Die Bewaffnung je Strang.** In FS1 trägt mein Jäger heute FS2-Waffen. Die
   richtigen FS1-Werte sind belegt (Handoff Abschnitt 7). Hier geht es um die
   Frage, **welche** Waffen der Spieler in welchem Strang bekommen soll und
   wie sie sich freischalten — nicht um Zahlen, die stehen schon.

Danach die erste Mission: **`sm1-01a`**, die erste richtige Mission der
FS1-Kampagne.

## Wie ein Missionsentwurf aussehen soll

Für jede Mission will ich von dir:

1. **Was in der Originalmission passiert** — kurz, in Prosa.
2. **Was davon bei uns übrig bleibt** und was wegfällt. Eine
   FreeSpace-Mission hat 35 bis 65 Schiffe, eine FS3-Mission eine Handvoll.
3. **Der Entwurf**: welche Einheiten, wo stehen sie, wer ist verbündet, wer
   kommt später, was löst was aus. In der Sprache aus Handoff Abschnitt 6 —
   also mit den echten Auslösern und Wirkungen, aber als Fließtext oder
   Tabelle, nicht als Code.
4. **Wie lange sie dauern soll** und wo Wartezeit entsteht. Lange Wartezeiten
   sind mein Hauptärgernis an den bestehenden Missionen.
5. **Der Nachweis, dass sie enden kann** — auf jedem Weg, auch wenn ich
   verliere oder ein Schützling stirbt. Die drei Fallen stehen im Handoff.
6. **Ob sie geteilt werden sollte.** Ich brauche rund 100 Missionen aus
   87 Originalen, manche muss ich also aufteilen.

## Was du nicht tun sollst

- Keinen Code schreiben. Ich setze das nicht selbst um.
- Keine HTML-Vorschauen oder Artefakte bauen. Das ist bei mir zweimal
  gescheitert; wir sehen uns alles direkt im Spiel an.
- Nicht die 80 Missionen verteidigen, die heute im Spiel sind. Die sind
  irrelevant und werden ersetzt.

Bestätige mir zuerst in **fünf Sätzen**, was du aus dem Handoff verstanden
hast — besonders, was das Spiel von FreeSpace unterscheidet. Dann fangen wir
mit dem Rearm-Tor an.
