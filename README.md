# UB Basel Servicebot – Starterpaket

Dieses Paket enthält eine direkt verwendbare Grundstruktur für einen schnellen, RAG-basierten Service-Chatbot der Universitätsbibliothek Basel.

## Dateien

- `ub-basel-bot-wahrheiten.md`  
  Kuratierte Wissensbasis als Single Source of Truth.

- `systemprompts-dify-flowise.md`  
  Sprachrouter, deutscher und englischer Systemprompt, Prompt-Injection-Guardrails, Datenschutz-Hinweis.

- `implementationscheckliste.md`  
  Ablauf für Woche 1–4.

- `testset-ub-basel-servicebot.csv`  
  Start-Testset zur Qualitätssicherung.

## Empfohlene Nutzung

1. `ub-basel-bot-wahrheiten.md` fachlich prüfen und ergänzen.
2. Datei in Dify oder Flowise als Knowledge Base importieren.
3. Prompts aus `systemprompts-dify-flowise.md` übernehmen.
4. Testfragen aus `testset-ub-basel-servicebot.csv` gegen den Bot laufen lassen.
5. Falsche Antworten zuerst durch Präzisierung der Wissensbasis korrigieren, nicht primär durch Prompt-Tuning.

## Wichtig

Die Starterfassung enthält bewusst keine ungeprüften Detailregeln zu Gebühren, VPN, E-Medien-Zugriff, Fernleihe oder Kontoaktionen. Diese Bereiche müssen vor einem öffentlichen Pilot durch UB-Fachpersonen ergänzt werden.


## Urheberschaft

Konzept und initiale Umsetzung: Dr. Robin Segerer.  
Erstellt als MVP-Starterpaket für einen RAG-basierten Service-Chatbot der Universitätsbibliothek Basel.
