# Anleitung für Silvio

Was du wann zu tun hast. Mehr als das Folgende brauchst du nicht — alles
andere mache ich.

**Die kurze Fassung:** Du tust nur drei Dinge. Eine neue Fassung auf dem
Server bauen, sie im Browser ansehen, und mir sagen was du siehst. GitHub
musst du nicht mehr anfassen.

---

## Drei Begriffe, einmal erklärt

**Repository (kurz Repo)** — der Ablageort auf GitHub, in dem das ganze
Spiel liegt. Davon gibt es eine Kopie auf deinem Server.

**Zweig (englisch „branch")** — eine Nebenspur im Repo. Ich arbeite immer auf
einer Nebenspur, nicht auf der Hauptspur. So kann nichts Ungetestetes in die
Hauptspur geraten. Die Hauptspur heißt `main`.

**Version** — eine durchnummerierte Fassung des Spiels, z. B. v217. Jede
neue Änderung bekommt die nächste Nummer.

---

## 1. Wenn ich sage „v218 liegt bereit"

### Einmalig, beim allerersten Mal

Die Nebenspur muss auf deinem Server einmal bekannt gemacht werden. Melde
dich auf `hlp-dev-01` an und gib ein:

```
cd /home/belisarius/fs3-build
git fetch origin
git checkout claude/festive-ramanujan-dedgw3
```

**Erwartete Ausgabe:** zuletzt eine Zeile wie
`Switched to a new branch 'claude/festive-ramanujan-dedgw3'`.

**Stopp-Punkt:** Steht dort stattdessen irgendwo das Wort `error` oder
`conflict`, **brich ab und schick mir die ganze Ausgabe.** Dann hat dein
Server noch eigene Änderungen liegen, die ich erst einsortieren muss.
Nichts weiter tun, nichts löschen.

### Jedes Mal

```
cd /home/belisarius/fs3-build
git pull
sudo ./build.sh
```

**Erwartete Ausgabe:** `git pull` nennt die geänderten Dateien. `build.sh`
läuft ein bis zwei Minuten und endet ohne das Wort `error`.

**Stopp-Punkt:** Kommt bei `git pull` das Wort `conflict`, **abbrechen und
mir die Ausgabe schicken.** Nicht weitermachen.

Danach schaust du dir das Spiel an, unter der Adresse, die ich dir mitgebe.
Sie sieht so aus:

```
http://dev.hard-light.org/fs3/?v=218&ui=1&ships=9&wpn=1
```

Die Nummer hinter `v=` ist nur dafür da, dass dein Browser nicht die alte
Fassung aus seinem Zwischenspeicher zeigt. Sie muss zur neuen Version passen.
Die Zahl wächst mit jeder Version — ich gebe dir die Adresse jedes Mal
vollständig mit, du musst sie nicht selbst bauen.

---

## 2. Wenn du etwas siehst, das falsch ist

**Sag es mir einfach so, wie du es siehst.** Das ist alles. Keine Fachsprache,
keine Vermutung über die Ursache nötig — die suche ich.

Hilfreich ist, wenn du dazusagst:

- **Was** du siehst („ein dunkles Rechteck um die Explosionen")
- **Wo** („bei allen Explosionen" oder „nur bei den großen Schiffen")
- **Wann** („sobald eine Rakete fliegt", „in Mission 9")

Was du **nicht** tun musst: eine Ursache nennen, in den Code schauen, oder
dich kurz fassen. Schreib ruhig lang.

Ich trage jeden gemeldeten Fehler in `OFFENE_FEHLER.md` ein. **Das ist
wichtig:** Eine Cloud-Sitzung sieht nur das Repo, nicht unseren Chat. Was
dort nicht steht, weiß ich in der nächsten Sitzung nicht mehr. Wenn du also
unsicher bist, ob ein Fehler noch bekannt ist — schau in diese Datei oder
frag mich, und melde ihn im Zweifel noch einmal. Doppelt gemeldet ist
harmlos, vergessen nicht.

---

## 3. Wenn eine Version gut ist

Sag mir einfach: **„v218 ist gut."**

Dann bringe ich sie in die Hauptspur `main`. Du musst dafür nichts auf GitHub
klicken. Danach steht sie dauerhaft und ist der neue Ausgangspunkt.

Wenn du danach wieder auf die Hauptspur willst, auf dem Server:

```
cd /home/belisarius/fs3-build
git checkout main
git pull
```

---

## 4. Wenn du Dateien ins Repo legen sollst

Zum Beispiel die FreeSpace-Missionsdateien. Das geht im Browser, dein Server
wird dafür nicht gebraucht.

1. `https://github.com/Belisarius7487/fs3` öffnen
2. **Oben links im Zweig-Auswahlfeld** (es steht `main` darin)
   `claude/festive-ramanujan-dedgw3` auswählen.
   **Das ist wichtig** — in `main` kommt nichts, bevor du eine Version
   abgenommen hast.
3. Rechts auf `Add file` → `Upload files`
4. Die **Ordner** vom Rechner ins Fenster ziehen. Namen am besten so:

   ```
   fs1/         die FS1-Missionen
   str/         Silent Threat: Reborn
   fs2/         die FS2-Missionen
   kampagne/    die .fc2-Dateien (Reihenfolge und Verzweigungen)
   ```

   Heißen deine Ordner anders, ist das kein Problem — ich sortiere sie
   danach ein. Wichtig ist nur, dass man am Ordnernamen erkennt, aus
   welchem Spiel die Dateien stammen.
5. Unten steht **„Commit directly to the claude/festive-ramanujan-dedgw3
   branch"**. Das muss ausgewählt sein. Dann auf `Commit changes`.

**Erwartete Ausgabe:** GitHub zeigt die Dateien danach im Zweig an.

**Stopp-Punkte:**

| Was du siehst | Was du tust |
|---|---|
| „Yowza, that's a lot of files" | In zwei oder drei Portionen hochladen, etwa 100 Dateien je Portion |
| Im Zweig-Feld steht noch `main` | Abbrechen, Zweig umstellen, neu anfangen |
| Eine Datei fehlt hinterher | Mir sagen, welche — manche Dateiendungen werden absichtlich nicht ins Repo gelassen (Bilder, Musik, Modelle) |

**Sag mir Bescheid, wenn du fertig bist.** Ich hole die Dateien dann zu mir
herüber. Solange du hochlädst, halte ich mich mit eigenen Änderungen zurück,
damit wir uns nicht in die Quere kommen.

---

## 5. Was du nicht mehr tun musst

- **Keine Dateien über die GitHub-Weboberfläche hochladen.** Ich habe das
  Repo in der Cloud selbst und schiebe fertig hoch.
- **Kein `python3 patch_vNNN.py` mehr.** Es gibt keine Patch-Skripte mehr;
  ich ändere die Quelldateien direkt.
- **Kein `python3 assemble.py` mehr.** Das mache ich, bevor ich hochschiebe.
- **Kein `bash save.sh` mehr.** Das würde den Stand deines Servers ins Repo
  schieben und meinen überschreiben. Benutze es nicht mehr.

Übrig bleiben für dich: `git pull` und `sudo ./build.sh`.

---

## 6. Wenn etwas klemmt

| Was du siehst | Was es heißt | Was du tust |
|---|---|---|
| `conflict` bei `git pull` | Server und Repo haben sich auseinanderentwickelt | Abbrechen, Ausgabe an mich |
| `error` bei `build.sh` | Der Bau ist gescheitert | Ganze Ausgabe an mich |
| Das Spiel zeigt die alte Fassung | Browser-Zwischenspeicher | Die `?v=` Nummer prüfen; sonst Seite mit Strg+F5 neu laden |
| Weißer Bildschirm | Das Spiel bricht beim Start ab | Mir sagen; dazu, falls du es findest, was in der Browser-Konsole steht (F12 drücken, Reiter „Console") |
| Du weißt nicht, wo du bist | — | `git status` eingeben und mir die Ausgabe schicken |

**Grundregel bei allem, was unklar ist:** nichts löschen, nichts erzwingen,
Ausgabe kopieren und mir schicken. Es geht nichts verloren — alles liegt auf
GitHub.

---

## 7. Was ich mache, bevor ich dir etwas gebe

Damit du weißt, worauf du dich verlassen kannst:

1. Ich lese im Code nach, statt zu vermuten.
2. Ich ändere die Quelldateien und setze die Spieldatei zusammen.
3. Ich lasse **alle** Prüfstufen laufen (`./checks.sh`) — vierzehn Stück,
   zwei davon spielen echte Missionen in einem Browser ohne Fenster.
4. **Nur wenn alle grün sind**, schiebe ich hoch und sage dir Bescheid.
   Ist eine rot, schiebe ich nichts hoch und melde mich stattdessen.
5. Bei einem behobenen Fehler stelle ich die neue Prüfung gegen die kaputte
   Fassung. Fällt sie dort nicht durch, prüft sie das Falsche.

Was ich **nicht** kann: im Browser sehen, ob es gut aussieht. Das ist dein
Teil, und deshalb geht keine Version ohne deinen Blick in die Hauptspur.
