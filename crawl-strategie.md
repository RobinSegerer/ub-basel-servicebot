# Balanced Crawl-Strategie für den UB Basel Servicebot

## Ziel

Der Bot soll möglichst vollständig zu Service-, Recherche-, Fachgebiets-, Standort- und Kontaktfragen antworten, aber auch Personeninformationen aus News, Events oder Blogbeiträgen nicht verlieren.

## Priorität 1: zuerst crawlen

- Fachgebiete und Fachseiten
- Fachreferate, Kontakt- und Personeninformationen
- Service: Ausleihe, Öffnungszeiten, Arbeitsplätze, Schulungen, Kopieren/Drucken/Digitalisieren
- Recherche: Kataloge, Datenbanken, E-Journals, E-Books, KI, digitale Sammlungen
- Standorte: Hauptbibliothek, Medizin, Religion, Rosental, Wirtschaft/SWA
- Open Science, Publizieren, Forschungsdaten
- Reglemente und Gebühren

## Priorität 2: danach crawlen

- allgemeine UB-Seiten
- Sammlungen
- Organisation
- historische Bestände

## Priorität 3: zuletzt crawlen, aber nicht ausschließen

- Aktuell
- News
- Veranstaltungen
- Ausstellungen
- Newsletter
- Blog
- temporäre Kampagnenseiten

## Warum nicht vollständig ausschließen?

Personen können über Event- oder Blogseiten sichtbar werden, etwa weil sie einen Beitrag geschrieben, eine Veranstaltung organisiert oder ein Projekt vorgestellt haben.

## Empfohlener Befehl

```bash
python ingest.py --reset --max-pages 1000
```

## Sehr breit

```bash
python ingest.py --reset --max-pages 1500
```

## Schnellere Demo-Version

```bash
python ingest.py --reset --max-pages 700
```
