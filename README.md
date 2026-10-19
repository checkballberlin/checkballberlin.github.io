# Checkball Berlin

3x3 Basketball in Berlin: Turniere, Open Gyms und News an einem Ort. Jeden Morgen gecheckt.

Das ist die offene Web-Version der Checkball-App. Sie läuft ohne Login über GitHub Pages
und lässt sich auf dem Handy wie eine App auf den Startbildschirm legen.

## Was wo liegt

| Datei | Inhalt |
| --- | --- |
| `index.html` | die App, gebaut aus `src/app.html` |
| `data/items.json` | alle öffentlichen Einträge im Feed |
| `data/meta.json` | Stand des letzten Agenten-Laufs |
| `src/app.html` | Quelltext der App, dieselbe Seite wie im claude.ai-Projekt |
| `tools/` | Skripte zum Bauen und für den Datenexport |
| `fonts/`, `icons/` | Schriften und App-Icons, lokal eingebunden (keine Anfragen an Google) |
| `manifest.webmanifest`, `sw.js` | Startbildschirm und Offline-Ansicht |
| `impressum.html`, `datenschutz.html`, `legal.css` | Impressum (Ambition Baller) und Datenschutzerklärung |

## Wie die Daten aktuell bleiben

Der Checkball-Agent (Claude, geplanter Lauf jeden Morgen um 05:54) prüft die Quellen,
schreibt neue Termine in die App-Datenbank und exportiert danach die öffentlichen Einträge:

```
python3 tools/export_data.py <Datenbank-Export> .
```

Grundregel: Checkball zeigt nur öffentlich angekündigte Termine. Nichts aus internen oder
geschützten Unterlagen. Öffentlich erscheint ein Eintrag nur mit öffentlicher Quelle
(`sourceUrl` oder `regUrl`) oder wenn der Betreiber ihn freigegeben hat (`"public": true`).

## „Ich bin dabei“ bei Open Gyms

Besucherinnen und Besucher können für den nächsten Termin eines Open Gyms zusagen; die App zeigt,
wie viele dabei sind. Die Zusagen liegen in Firebase (Cloud Firestore, anonyme Anmeldung, keine Namen).
Eingeschaltet wird das mit einer Datei `config.json` neben `index.html`:

```
{ "firebase": { "apiKey": "…", "projectId": "…" } }
```

Ohne diese Datei bleibt die Funktion aus. Die Sicherheitsregeln stehen in `firebase/firestore.rules`.
Vor dem Einschalten die Datenschutzerklärung um Firebase ergänzen.

## Die App ändern

Änderungen passieren in `src/app.html`. Danach:

```
python3 tools/build_index.py
```

Meldungen aus der Community kommen per Mail an ambitioncheckball@gmail.com
oder per Instagram-DM an @checkball.berlin.

Schriften: Barlow Condensed, Figtree und JetBrains Mono unter der SIL Open Font License (siehe `fonts/`).
