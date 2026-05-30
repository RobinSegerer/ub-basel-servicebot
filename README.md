# UB Streamlit Servicebot Wide Crawl

Diese Version crawlt nicht nur eine kleine Allowlist, sondern entdeckt interne Links auf `ub.unibas.ch` rekursiv.

Sie ist für Präsentationen und interne Exploration gedacht, damit Fachgebiete, Standortseiten, Recherche- und Serviceunterseiten deutlich breiter abgedeckt werden.

## Setup

```bash
cd ~/Desktop
unzip ub_streamlit_bot_wide.zip
cd ub_streamlit_bot_wide
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## API-Key

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
nano .streamlit/secrets.toml
```

## Breiten Index erstellen

Empfohlen für Präsentation:

```bash
python ingest.py --reset --max-pages 250
```

Noch breiter, aber langsamer und teurer:

```bash
python ingest.py --reset --max-pages 500
```

Mit News-/Event-nahen Seiten:

```bash
python ingest.py --reset --max-pages 500 --include-low-value
```

## App starten

```bash
streamlit run app.py
```

Falls nötig:

```bash
python -m streamlit run app.py
```

## Was passiert?

1. `ub-basel-bot-wahrheiten.md` wird mit höchster Priorität indexiert.
2. Der Crawler startet bei `seeds.txt`.
3. Er folgt internen Links auf `ub.unibas.ch`.
4. Er speichert die entdeckten URLs in `vectorstore/discovered_urls.txt`.
5. Er extrahiert Text mit `trafilatura`.
6. Er chunked nach Markdown-Headings.
7. Er erstellt OpenAI-Embeddings.
8. Er speichert alles lokal als NumPy-Index.

## Grenzen

- Keine PDFs.
- Keine Login-Seiten.
- Keine persönlichen Kontodaten.
- Kein Live-Scraping bei Nutzerfragen.
- Vor öffentlichem Pilot: Datenschutz/IT/Kommunikation prüfen.

## Nach dem Crawl prüfen

```bash
cat vectorstore/discovered_urls.txt | wc -l
head vectorstore/discovered_urls.txt
```

## Wichtiger Hinweis

Mehr Crawling erhöht Abdeckung, aber auch Rauschen. Für eine Präsentation ist `--max-pages 250` sinnvoll. Für einen Produktivbot sollte danach wieder kuratiert werden.


## Logo

Das AG-AIDA-Logo liegt unter:

```text
assets/ag_aida_logo.png
```

Die App zeigt es automatisch oben im Kopfbereich an.


## UX-Erweiterungen

Diese Version enthält zusätzliche UX-Elemente:

- laientaugliche Sidebar mit Möglichkeiten und Grenzen
- Beispiel-Fragen als Startbuttons
- Admin-Details nur über Toggle
- verständlich benannte Quellen mit 🛡️/🌐 Kennzeichnung
- Triage-Hinweis bei schwachen Treffern
- Feedback-Daumen unter Bot-Antworten
- stärkeres Keyword-/Namensmatching im Retrieval


## Vectorstore-Qualitätsverbesserungen

Diese Version enthält:

- `glossar-und-synonyme.md` für Nutzerbegriffe, Akronyme und bibliothekarische Übersetzungen
- `personen-und-kontakte.md` als kuratierbare Datei für Fachreferate, Zuständigkeiten und Kontaktfragen
- einfache Noise-Filter gegen Navigations-, Footer- und Standardtexte
- feinere Prioritäten: `high`, `medium_high`, `medium`, `low`, `very_low`
- angepasste Quellenlabels in der App

Nach Änderungen an Glossar, Personen/Kontakte oder Bot-Wahrheiten muss der Index neu erstellt werden:

```bash
python ingest.py --reset --max-pages 500
```


## Kuratierte Crawl-Strategie: Fachseiten und Services vor Aktuell

Diese Version ist auf einen Servicebot ausgerichtet:

- Fachgebiete und Fachseiten werden stark priorisiert.
- Service-, Recherche-, Standort-, Kontakt-, Open-Science- und Reglement-Seiten werden bevorzugt.
- `Aktuell`, News, Events, Ausstellungen, Newsletter und Blog werden standardmäßig ausgeschlossen.
- Die Datei `seeds.txt` enthält zentrale Startpunkte aus der Hauptnavigation.

Empfohlener Crawl für eine Präsentation:

```bash
python ingest.py --reset --max-pages 700
```

Wenn danach geprüft werden soll, ob Fachseiten enthalten sind:

```bash
grep -i "Fachgebiete" vectorstore/docs.jsonl | head
grep -i "Psychologie" vectorstore/docs.jsonl | head
grep -i "Fachrefer" vectorstore/docs.jsonl | head
```

Nur wenn bewusst News/Events mitindexiert werden sollen:

```bash
python ingest.py --reset --max-pages 700 --include-low-value
```

Für den Servicebot ist `--include-low-value` normalerweise nicht empfohlen.


## Balanced Crawl: breit erfassen, aber Wichtiges zuerst

Diese Version schließt News, Events, Ausstellungen und Blogbeiträge **nicht mehr grundsätzlich aus**. 
Sie werden nur nachrangig behandelt:

1. Fachseiten, Service, Recherche, Kontakt, Standorte, Open Science, Reglemente zuerst
2. Allgemeine Seiten danach
3. Aktuell, News, Events, Ausstellungen, Blog/Newsletter zuletzt

Damit können Personeninformationen aus Events oder Blogbeiträgen weiterhin gefunden werden, ohne dass diese temporären Inhalte die wichtigsten Serviceinformationen verdrängen.

Empfohlener Crawl für Präsentation:

```bash
python ingest.py --reset --max-pages 1000
```

Schneller, aber weniger vollständig:

```bash
python ingest.py --reset --max-pages 700
```

Sehr breit:

```bash
python ingest.py --reset --max-pages 1500
```

Prüfen:

```bash
wc -l vectorstore/discovered_urls.txt
grep -i "psychologie" vectorstore/docs.jsonl | head
grep -i "fachrefer" vectorstore/docs.jsonl | head
grep -i "personen" vectorstore/discovered_urls.txt | head
```
