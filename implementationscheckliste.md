# UB Basel Servicebot – Implementationscheckliste

Konzept und initiale Umsetzung: Dr. Robin Segerer

## Ziel

Interner MVP-Pilot eines RAG-basierten Service-Chatbots für öffentliche Servicefragen zur UB Basel.

Nicht im MVP:

- keine Kontoanmeldung,
- keine swisscovery-API-Integration,
- keine Gebührenberechnung im Einzelfall,
- keine Reservationen oder Verlängerungen,
- keine personenbezogene Beratung,
- keine Fachrechercheberatung als Ersatz für Bibliothekspersonal.

---

## Woche 1: Wissensbasis

### Aufgaben

1. 30–50 häufige Servicefragen sammeln.
2. Offizielle UB-Quellen identifizieren.
3. Antworten redaktionell in `ub-basel-bot-wahrheiten.md` eintragen.
4. Alle Links vollqualifiziert eintragen.
5. Kritische Themen mit Fallback-Antworten versehen.
6. Datenschutz-Hinweis formulieren.
7. Fachliche Prüfung durch Serviceverantwortliche.

### Ergebnis

- `ub-basel-bot-wahrheiten.md`
- erste Linkliste
- erste Fallback-Regeln
- erste Liste nicht unterstützter Anwendungsfälle

---

## Woche 2: Dify/Flowise-Prototyp

### Dify-Empfehlung

1. Neue Chatbot-App anlegen.
2. Knowledge Base erstellen.
3. `ub-basel-bot-wahrheiten.md` importieren.
4. Chunking nach Überschriften testen.
5. Retrieval Top-K zunächst 3–5.
6. Temperatur niedrig setzen: 0.1–0.3.
7. Sprachrouter vorschalten:
   - DE
   - EN
   - OTHER
8. Je nach Label deutschen oder englischen Systemprompt verwenden.
9. Chat-Widget nur intern einbetten.
10. Logging datenschutzarm konfigurieren.

### Flowise-Empfehlung

1. Chatflow anlegen.
2. Markdown-Datei als Document Loader einbinden.
3. Textsplitter nach Markdown-Headings bevorzugen.
4. Vector Store konfigurieren.
5. Retriever Top-K 3–5.
6. LLM-Chain mit Systemprompt verbinden.
7. Simple Router Node oder vorgeschaltete Klassifikation verwenden.
8. Chat-Widget intern testen.

---

## Woche 3: Testset

### Qualitätskriterien

- korrekte Antwort,
- keine erfundenen Links,
- keine erfundenen Öffnungszeiten,
- keine individuellen Kontoaussagen,
- korrekte swisscovery-Abgrenzung,
- korrektes Englisch bei deutschen Quellen,
- saubere Datenschutzreaktion,
- Fallback statt Halluzination.

### Ziel vor Pilot

- mindestens 85–90 Prozent brauchbare Antworten,
- null kritische Halluzinationen bei Konto, Gebühren, Öffnungszeiten, Datenschutz und Zuständigkeiten.

---

## Woche 4: Interner Pilot

### Ablauf

1. Interne Testgruppe definieren.
2. Bot auf nicht öffentlicher Testseite bereitstellen.
3. Feedbackbutton ergänzen:
   - hilfreich,
   - teilweise hilfreich,
   - falsch,
   - gefährlich/irreführend.
4. Wöchentlich 30–50 Chats prüfen.
5. Wissensbasis nachpflegen.
6. Datenschutz-/IT-Security-Review vorbereiten.
7. Go/No-Go für öffentlichen Pilot entscheiden.

---

## Betriebsregel

Nicht zuerst den Prompt verbessern, sondern zuerst die Wissensbasis verbessern.

Wenn der Bot falsch antwortet, prüfen:

1. Steht die korrekte Information überhaupt in der Wissensbasis?
2. Ist sie eindeutig formuliert?
3. Ist sie in einem eigenen Abschnitt?
4. Ist der Link vollqualifiziert?
5. Braucht es eine explizite Fallback-Regel?
6. Erst danach den Prompt anpassen.
