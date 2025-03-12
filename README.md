# AI-THINK-TANK

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Überblick

AI-THINK-TANK ist eine Webanwendung, die die Simulation von Konversationen zwischen mehreren KI-Agenten ermöglicht.  Die Anwendung nutzt die Google Gemini-Modelle (**sowohl `gemini-2.0-flash-thinking-exp-01-21` für Text als auch gemini-2.0-flash-thinking-exp-01-21` für multimodale Eingaben**), um realistische und dynamische Dialoge zu generieren. Benutzer können Agenten mit verschiedenen Persönlichkeiten konfigurieren, ein Diskussionsthema festlegen und **optional eine PDF-Datei *oder* ein Bild (PNG, JPG, JPEG, GIF) als Grundlage für die Konversation hochladen**. Die Anwendung bietet Funktionen zur Benutzerverwaltung, zum Speichern von Gesprächen, zur Bewertung von Agentenantworten und zum Exportieren des Chatverlaufs als Word-Dokument.

## Funktionen

*   **KI-Agenten-Konversation:** Simulieren Sie Gespräche zwischen mehreren KI-Agenten, die auf den Google Gemini-Modellen basieren.
*   **Konfigurierbare Agenten:**  Wählen Sie aus vordefinierten Agenten mit unterschiedlichen Persönlichkeiten (kritisch, visionär, konservativ, neutral).
*   **Themenvorgabe:**  Legen Sie ein Diskussionsthema fest.
*   **Multimodale Eingabe:** Laden Sie **optional eine PDF-Datei *oder* ein Bild (PNG, JPG, JPEG, GIF) hoch**, um die Konversation zu steuern. Gemini Pro Vision wird für die Bildanalyse verwendet.
*   **Anpassbare Parameter:**  Konfigurieren Sie die Anzahl der Gesprächsrunden, das Experten-Level und die Sprache der Konversation.
*   **Zusammenfassungsgenerierung:**  Erstellen Sie automatische Zusammenfassungen des Gesprächsverlaufs (sowohl für Text als auch für Bildbeschreibungen).
*   **Benutzerverwaltung:**  Registrieren und anmelden Sie Benutzer mit sicherer Passwortverschlüsselung.
*   **Gesprächsspeicherung:**  Speichern Sie Konversationen in einer SQLite-Datenbank, um sie später wieder aufrufen zu können.
*   **Bewertungssystem:**  Bewerten Sie die Antworten der Agenten mit Upvotes und Downvotes.
*   **Word-Export:**  Exportieren Sie den Chatverlauf als formatiertes Word-Dokument (.docx).
*   **Fehlerbehandlung:**  Robuste Fehlerbehandlung und Wiederholungsmechanismen für API-Aufrufe.
*   **Protokollierung:**  Detaillierte Protokollierung von Ereignissen und Fehlern zur einfachen Fehlerbehebung.
*    **Bildvorschau:** Zeigt hochgeladene Bilder direkt in der Anwendung an.

## Installation

1.  **Voraussetzungen:**
    *   Python 3.7+
    *   Ein Google Cloud-Konto mit Zugriff auf die Gemini API (und ein entsprechender API-Schlüssel).

2.  **Abhängigkeiten installieren:**

    ```bash
    pip install -r requirements.txt
    ```
    **Erstellen Sie eine `requirements.txt`-Datei mit folgendem Inhalt (unverändert):**

    ```
    streamlit
    google-generativeai
    python-docx
    jsonschema
    tornado
    mimetypes # Stellen Sie sicher, dass mimetypes enthalten ist!
    ```

3. **Klonen Sie das Repository**

    ```bash
    git clone <Repository-URL>
    cd <Repository-Name>
    ```

4.  **Starten der Anwendung:**

    ```bash
    streamlit run tester.py
    ```

    Die Anwendung sollte nun in Ihrem Webbrowser unter der angegebenen Adresse (normalerweise `http://localhost:8501`) verfügbar sein.

## Konfiguration

### API-Schlüssel

Geben Sie Ihren Gemini API-Schlüssel in das entsprechende Feld in der Seitenleiste der Anwendung ein.  **Wichtig:**  Bewahren Sie Ihren API-Schlüssel sicher auf und geben Sie ihn nicht an Dritte weiter.  Es wird dringend empfohlen, den API-Schlüssel *nicht* direkt im Code zu speichern, sondern ihn über eine Umgebungsvariable oder eine separate, sichere Konfigurationsdatei bereitzustellen.

### Agentenkonfiguration

Die Agentenkonfiguration wird in der Datei `agent_config.json` gespeichert.  Diese Datei enthält ein Array von JSON-Objekten, die jeweils einen Agenten definieren.  Jedes Objekt muss die folgenden Felder enthalten:

*   `name`:  Der Name des Agenten (String).
*   `personality`:  Die Persönlichkeit des Agenten (String, erlaubt sind "kritisch", "visionär", "konservativ", "neutral").
*   `description`:  Eine Beschreibung des Agenten (String).

Beispiel:

```json
[
    {
        "name": "AgentA",
        "personality": "kritisch",
        "description": "Ein kritischer Denker, der Argumente hinterfragt."
    },
    {
        "name": "AgentB",
        "personality": "visionär",
        "description": "Ein Visionär, der neue Ideen und Perspektiven einbringt."
    }
]
```

Sie können die Datei `agent_config.json` bearbeiten, um Agenten hinzuzufügen, zu entfernen oder zu ändern.

### Konstanten

Die folgenden Konstanten in `tester.py` können angepasst werden:

*   `MODEL_NAME_TEXT`:  Der Name des Gemini-Modells für Textverarbeitung (z.B. "gemini-2.0-pro-exp-02-05").
*   `MODEL_NAME_VISION`: Der Name des Gemini-Modells für Bildverarbeitung (z.B., "gemini-pro-vision").  **Wichtig: Verwenden Sie `gemini-pro-vision` für Bilder.**
*   `API_SLEEP_SECONDS`:  Die Wartezeit (in Sekunden) zwischen API-Aufrufen.
*   `API_MAX_RETRIES`:  Die maximale Anzahl von Wiederholungsversuchen bei API-Fehlern.
*   `SUMMARY_SLEEP_SECONDS`: Die Wartezeit nach dem Generieren einer Zusammenfassung.
*   `AUDIT_LOG_FILE`, `EXPIRATION_TIME_SECONDS`, `ROLE_PERMISSIONS`, `PRIORITY_MAP`, `USER_DATA_FILE`, `DISCUSSION_DB_FILE`, `RATING_DATA_FILE`, `AGENT_CONFIG_FILE`: Diese definieren Dateinamen, Zeiten, Rollen und weitere Konfigurationen. Ändere diese nur, wenn du genau weißt, was du tust.

## Verwendung

1.  **Anmelden/Registrieren:** (Optional) Erstellen Sie ein Konto oder melden Sie sich an, um Ihre Konversationen zu speichern.
2.  **Agenten auswählen:** Wählen Sie die Agenten aus, die an der Konversation teilnehmen sollen.
3.  **Thema eingeben:** Geben Sie ein Diskussionsthema ein.
4.  **Datei hochladen:** Laden Sie **entweder eine PDF-Datei *oder* ein Bild (PNG, JPG, JPEG, GIF)** hoch, um die Konversation zu unterstützen.
5.  **Parameter anpassen:**  Wählen Sie die Anzahl der Gesprächsrunden, das Experten-Level und die Sprache.
6.  **Konversation starten:**  Klicken Sie auf "Konversation starten".
7.  **Interagieren:**  Beobachten Sie den Verlauf der Konversation und bewerten Sie die Antworten der Agenten.
8.  **Speichern/Exportieren:**  Speichern Sie die Konversation in der Datenbank oder exportieren Sie sie als Word-Dokument.

## Architektur

Die Anwendung ist in folgende Hauptkomponenten unterteilt:

*   **Benutzeroberfläche (Streamlit):**  Verantwortlich für die Interaktion mit dem Benutzer, die Anzeige der Konversation und die Konfiguration der Parameter.
*   **API-Client (Google GenAI):**  Verantwortlich für die Kommunikation mit der Gemini API.  Die Anwendung verwendet jetzt sowohl `gemini-pro` (für Text) als auch `gemini-pro-vision` (für Bilder).
*   **Konversationslogik:**  Steuert den Ablauf der Konversation, ruft die Gemini API auf und generiert Zusammenfassungen. Es gibt separate Funktionen für die Verarbeitung von Text und Bildern.
*   **Datenpersistenz (JSON, SQLite):**  Verantwortlich für das Speichern und Laden von Benutzerdaten, Agentenkonfigurationen, Bewertungen und Diskussionsdaten.
*   **Hilfsfunktionen:**  Enthält Funktionen für Aufgaben wie Passwortverschlüsselung, JSON-Validierung, MIME-Typ-Erkennung und Dateiverarbeitung.

## Fehlerbehebung

*   **API-Fehler:** Wenn bei der Kommunikation mit der Gemini API Fehler auftreten, überprüfen Sie Ihren API-Schlüssel und Ihr API-Kontingent.  Die Anwendung protokolliert detaillierte Fehlermeldungen im Terminal. Stellen Sie sicher, dass Sie das richtige Modell (`gemini-pro-vision` für Bilder, `gemini-pro` für Text) verwenden.
*   **Verbindungsfehler:**  Bei Verbindungsfehlern (z. B. `tornado.websocket.WebSocketClosedError`) stellen Sie sicher, dass Ihre Internetverbindung stabil ist.  Diese Fehler können auch bei sehr langen Konversationen auftreten.
*   **Fehler beim Laden/Speichern von Daten:**  Überprüfen Sie die Protokolldatei (`audit_log.txt`) auf detaillierte Fehlermeldungen. Stellen Sie sicher, dass die Anwendung die erforderlichen Berechtigungen zum Lesen und Schreiben der Dateien hat.
*   **Fehler beim Hochladen/Verarbeiten von Dateien:** Überprüfen Sie, ob die Datei (PDF oder Bild) korrekt formatiert ist und den unterstützten Dateitypen entspricht. Fehler werden detailliert protokolliert. Wenn ein nicht unterstützter Dateityp hochgeladen wird, wird eine entsprechende Meldung angezeigt.

## Lizenz

Diese Software ist unter der MIT-Lizenz lizenziert. Siehe die Datei [LICENSE](LICENSE) für weitere Details.  (Erstelle eine leere Datei namens `LICENSE` und füge den MIT-Lizenztext ein).

## Beitrag

Beiträge zu diesem Projekt sind willkommen! Bitte erstellen Sie einen Pull Request mit Ihren Änderungen.

## Haftungsausschluss

Diese Software wird "wie besehen" ohne jegliche Gewährleistung bereitgestellt. Die Autoren übernehmen keine Haftung für Schäden, die durch die Verwendung dieser Software entstehen.
