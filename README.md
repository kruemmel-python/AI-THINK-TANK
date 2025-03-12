# AI-THINK-TANK

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Überblick

AI-THINK-TANK ist eine mehrsprachige Webanwendung, die die Simulation von Konversationen zwischen mehreren KI-Agenten ermöglicht.  Die Anwendung nutzt die Google Gemini-Modelle (sowohl **`gemini-pro` für Text als auch `gemini-pro-vision` für multimodale Eingaben**), um realistische und dynamische Dialoge zu generieren. Benutzer können Agenten mit verschiedenen Persönlichkeiten konfigurieren, ein Diskussionsthema festlegen und optional eine PDF-Datei oder ein Bild (PNG, JPG, JPEG, GIF) als Grundlage für die Konversation hochladen. Die Anwendung bietet Funktionen zur Benutzerverwaltung, zum Speichern von Gesprächen, zur Bewertung von Agentenantworten und zum Exportieren des Chatverlaufs als Word-Dokument.  Die Benutzeroberfläche ist in mehreren Sprachen verfügbar (Deutsch, Englisch, Spanisch, Russisch, Chinesisch und Französisch).

## Funktionen

*   **KI-Agenten-Konversation:** Simulieren Sie Gespräche zwischen mehreren KI-Agenten, die auf den Google Gemini-Modellen basieren.
*   **Konfigurierbare Agenten:** Wählen Sie aus vordefinierten Agenten mit unterschiedlichen Persönlichkeiten (kritisch, visionär, konservativ, neutral).
*   **Themenvorgabe:** Legen Sie ein Diskussionsthema fest.
*   **Multimodale Eingabe:** Laden Sie optional eine PDF-Datei oder ein Bild (PNG, JPG, JPEG, GIF) hoch, um die Konversation zu steuern. Gemini Pro Vision wird für die Bildanalyse verwendet.
*   **Anpassbare Parameter:** Konfigurieren Sie die Anzahl der Gesprächsrunden, das Experten-Level und die Sprache der Konversation und der Benutzeroberfläche.
*   **Zusammenfassungsgenerierung:** Erstellen Sie automatische Zusammenfassungen des Gesprächsverlaufs (sowohl für Text als auch für Bildbeschreibungen).
*   **Benutzerverwaltung:** Registrieren und anmelden Sie Benutzer mit sicherer Passwortverschlüsselung.
*   **Gesprächsspeicherung:** Speichern Sie Konversationen in einer SQLite-Datenbank, um sie später wieder aufrufen zu können.
*   **Bewertungssystem:** Bewerten Sie die Antworten der Agenten mit Upvotes und Downvotes.
*   **Word-Export:** Exportieren Sie den Chatverlauf als formatiertes Word-Dokument (.docx).
*   **Fehlerbehandlung:** Robuste Fehlerbehandlung und Wiederholungsmechanismen für API-Aufrufe, einschließlich spezifischer Fehlermeldungen für fehlende API-Schlüssel.
*   **Protokollierung:** Detaillierte Protokollierung von Ereignissen und Fehlern zur einfachen Fehlerbehebung.
*   **Bildvorschau:** Zeigt hochgeladene Bilder direkt in der Anwendung an.
*   **Mehrsprachigkeit:** Die Benutzeroberfläche ist in mehreren Sprachen verfügbar (Deutsch, Englisch, Spanisch, Russisch, Chinesisch und Französisch). Die Sprache kann über ein Auswahlmenü in der Seitenleiste umgeschaltet werden.

## Installation

1.  **Voraussetzungen:**
    *   Python 3.7+
    *   Ein Google Cloud-Konto mit Zugriff auf die Gemini API (und ein entsprechender API-Schlüssel).  [Hier erhalten Sie einen API-Schlüssel](https://aistudio.google.com/apikey).

2.  **Abhängigkeiten installieren:**

    ```bash
    pip install -r requirements.txt
    ```

    **Erstellen Sie eine `requirements.txt`-Datei mit folgendem Inhalt:**

    ```
    streamlit
    google-generativeai
    python-docx
    jsonschema
    tornado
    mimetypes
    ```

3.  **Klonen Sie das Repository:**

    ```bash
    git clone <Repository-URL>
    cd <Repository-Name>
    ```

4.  **Starten der Anwendung:**

    ```bash
    streamlit run streamlit_app.py
    ```
    (Ersetze `streamlit_app.py`, falls deine Hauptdatei anders heißt)

    Die Anwendung sollte nun in Ihrem Webbrowser unter der angegebenen Adresse (normalerweise `http://localhost:8501`) verfügbar sein.

## Konfiguration

### API-Schlüssel

Geben Sie Ihren Gemini API-Schlüssel in das entsprechende Feld in der Seitenleiste der Anwendung ein.  **Wichtig:** Bewahren Sie Ihren API-Schlüssel sicher auf und geben Sie ihn nicht an Dritte weiter.  Es wird *dringend* empfohlen, den API-Schlüssel *nicht* direkt im Code zu speichern, sondern ihn über die *Secrets*-Funktion von Streamlit Cloud bereitzustellen (siehe Abschnitt "Bereitstellung in Streamlit Cloud").

### Agentenkonfiguration

Die Agentenkonfiguration wird in der Datei `agent_config.json` gespeichert.  Diese Datei enthält ein Array von JSON-Objekten, die jeweils einen Agenten definieren.  Jedes Objekt muss die folgenden Felder enthalten:

*   `name`: Der Name des Agenten (String).
*   `personality`: Die Persönlichkeit des Agenten (String, erlaubt sind "kritisch", "visionär", "konservativ", "neutral").
*   `description`: Eine Beschreibung des Agenten (String).

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

### Übersetzungen (Mehrsprachigkeit)

Die Übersetzungen für die Benutzeroberfläche werden in der Datei `streamlit_app.py` (oder wie auch immer deine Hauptdatei heißt) im Dictionary `translations` gespeichert.  Dieses Dictionary enthält für jede unterstützte Sprache (Deutsch, Englisch, Spanisch, usw.) ein Unter-Dictionary mit Schlüssel-Wert-Paaren.  Die Schlüssel sind eindeutige Bezeichner für die Textelemente (z.B. `title`, `login_btn`, `api_key_warning`), und die Werte sind die übersetzten Texte.

**Wichtig:**

*   Stellen Sie sicher, dass *alle* in der Benutzeroberfläche angezeigten Texte im `translations`-Dictionary vorhanden sind.
*   Fügen Sie neue Sprachen hinzu, indem Sie ein neues Unter-Dictionary mit dem entsprechenden Sprachcode (z.B. "fr" für Französisch) erstellen und alle Schlüssel übersetzen.
*   Die `get_translation(lang, key)`-Funktion im Code wird verwendet, um die korrekte Übersetzung basierend auf der ausgewählten Sprache abzurufen.

### Konstanten

Die folgenden Konstanten in `streamlit_app.py` können angepasst werden:

*   `MODEL_NAME_TEXT`: Der Name des Gemini-Modells für Textverarbeitung (z.B. `"gemini-1.5-pro-002"`).  **Verwenden Sie aktuelle Modelle.**
*   `MODEL_NAME_VISION`: Der Name des Gemini-Modells für Bildverarbeitung (z.B. `"gemini-1.5-pro-002"`).  **Verwenden Sie aktuelle Modelle, und stellen sie sicher, dass es sich um ein Vision-Modell handelt.**
*   `API_SLEEP_SECONDS`: Die Wartezeit (in Sekunden) zwischen API-Aufrufen.
*   `API_MAX_RETRIES`: Die maximale Anzahl von Wiederholungsversuchen bei API-Fehlern.
*   `SUMMARY_SLEEP_SECONDS`: Die Wartezeit nach dem Generieren einer Zusammenfassung.
*  `USE_CHAT_HISTORY_FILE`:  Eine boolesche Variable, die steuert, ob der Chatverlauf in einer Textdatei gespeichert wird (`True`) oder nicht (`False`).  Für die Bereitstellung in Streamlit Cloud wird empfohlen, dies auf `False` zu setzen und stattdessen `st.session_state` oder eine externe Datenbank zu verwenden.
*   `AUDIT_LOG_FILE`, `EXPIRATION_TIME_SECONDS`, `ROLE_PERMISSIONS`, `PRIORITY_MAP`, `USER_DATA_FILE`, `DISCUSSION_DB_FILE`, `RATING_DATA_FILE`, `AGENT_CONFIG_FILE`: Diese definieren Dateinamen, Zeiten, Rollen und weitere Konfigurationen. Ändern Sie diese nur, wenn Sie genau wissen, was Sie tun.

## Verwendung

1.  **Sprache auswählen:** Wählen Sie in der Seitenleiste die gewünschte Sprache für die Benutzeroberfläche aus.
2.  **Anmelden/Registrieren:** (Optional) Erstellen Sie ein Konto oder melden Sie sich an, um Ihre Konversationen zu speichern.
3.  **Agenten auswählen:** Wählen Sie die Agenten aus, die an der Konversation teilnehmen sollen.
4.  **Thema eingeben:** Geben Sie ein Diskussionsthema ein.
5.  **Datei hochladen:** Laden Sie optional eine PDF-Datei oder ein Bild (PNG, JPG, JPEG, GIF) hoch, um die Konversation zu unterstützen.
6.  **Parameter anpassen:** Wählen Sie die Anzahl der Gesprächsrunden und das Experten-Level.
7.  **Konversation starten:** Klicken Sie auf "Konversation starten".
8.  **Interagieren:** Beobachten Sie den Verlauf der Konversation und bewerten Sie die Antworten der Agenten.
9.  **Speichern/Exportieren:** Speichern Sie die Konversation in der Datenbank oder exportieren Sie sie als Word-Dokument.

## Bereitstellung in Streamlit Cloud

1.  **Secrets Management:**  *Speichern Sie Ihren API-Schlüssel niemals direkt im Code.* Verwenden Sie stattdessen die Secrets-Funktion von Streamlit Cloud:
    *   Gehen Sie in Ihrem Streamlit Cloud Dashboard zu Ihrer App.
    *   Klicken Sie auf die drei Punkte ("...") und wählen Sie "Edit Secrets".
    *   Fügen Sie eine Variable hinzu, z.B. `GEMINI_API_KEY`, und fügen Sie Ihren API-Schlüssel als Wert ein.
    *   Speichern Sie die Secrets.
    *   Ändern Sie Ihren Code, um den API-Schlüssel aus den Secrets zu lesen:
        ```python
        api_key = st.secrets["GEMINI_API_KEY"]
        if not api_key:
            st.warning(get_translation(lang, "api_key_warning"))
            st.stop()
        ```

2.  **Persistenz:**  Beachten Sie, dass Streamlit Cloud ein *temporäres* Dateisystem verwendet.  Das bedeutet, dass Dateien, die Sie schreiben (z. B. die SQLite-Datenbankdatei oder die `chat_history.txt`), *nicht* dauerhaft gespeichert werden.  Verwenden Sie für persistente Speicherung eine *externe Datenbank* (siehe unten).  Setzen Sie `USE_CHAT_HISTORY_FILE = False`, um das Schreiben in die Textdatei zu deaktivieren.

3.  **Externe Datenbank (empfohlen für Produktion):**  Für eine zuverlässige, dauerhafte Speicherung Ihrer Diskussionsdaten verwenden Sie eine Cloud-basierte Datenbank wie PostgreSQL, MySQL, MongoDB Atlas, Firebase oder Supabase.  Sie müssen Ihren Code anpassen, um eine Verbindung zu der externen Datenbank herzustellen.

## Architektur

Die Anwendung ist in folgende Hauptkomponenten unterteilt:

*   **Benutzeroberfläche (Streamlit):** Verantwortlich für die Interaktion mit dem Benutzer, die Anzeige der Konversation, die Konfiguration der Parameter und die Sprachauswahl.
*   **API-Client (Google GenAI):** Verantwortlich für die Kommunikation mit der Gemini API. Die Anwendung verwendet sowohl `gemini-pro` (für Text) als auch `gemini-pro-vision` (für Bilder).
*   **Konversationslogik:** Steuert den Ablauf der Konversation, ruft die Gemini API auf, generiert Zusammenfassungen und verarbeitet die mehrsprachigen Prompts.
*   **Datenpersistenz (JSON, SQLite):** Verantwortlich für das Speichern und Laden von Benutzerdaten, Agentenkonfigurationen, Bewertungen und Diskussionsdaten (bei Verwendung einer lokalen SQLite-Datenbank; für Streamlit Cloud wird eine externe Datenbank empfohlen).
*   **Hilfsfunktionen:** Enthält Funktionen für Aufgaben wie Passwortverschlüsselung, JSON-Validierung, MIME-Typ-Erkennung, Dateiverarbeitung und das Abrufen von Übersetzungen.

## Fehlerbehebung

*   **API-Fehler:** Wenn bei der Kommunikation mit der Gemini API Fehler auftreten, überprüfen Sie Ihren API-Schlüssel und Ihr API-Kontingent. Stellen Sie sicher, dass Sie das richtige Modell (`gemini-pro-vision` für Bilder, `gemini-pro` für Text) verwenden. Die Anwendung protokolliert detaillierte Fehlermeldungen im Terminal und zeigt entsprechende Warnungen in der Benutzeroberfläche an.
*   **Verbindungsfehler:** Bei Verbindungsfehlern (z. B. `tornado.websocket.WebSocketClosedError`) stellen Sie sicher, dass Ihre Internetverbindung stabil ist. Diese Fehler können auch bei sehr langen Konversationen oder bei Überschreitung des API-Kontingents auftreten.
*   **Fehler beim Laden/Speichern von Daten:** Überprüfen Sie die Protokolldatei (`audit_log.txt`) auf detaillierte Fehlermeldungen. Stellen Sie sicher, dass die Anwendung die erforderlichen Berechtigungen zum Lesen und Schreiben der Dateien/Datenbank hat (bei lokaler Ausführung). Bei Verwendung von Streamlit Cloud und einer externen Datenbank überprüfen Sie die Verbindungseinstellungen und die Datenbankberechtigungen.
*   **Fehler beim Hochladen/Verarbeiten von Dateien:** Überprüfen Sie, ob die Datei (PDF oder Bild) korrekt formatiert ist und den unterstützten Dateitypen entspricht. Fehler werden detailliert protokolliert. Wenn ein nicht unterstützter Dateityp hochgeladen wird, wird eine entsprechende Meldung angezeigt.
* **Fehlende Übersetzungen:** Wenn Texte in der Benutzeroberfläche als "Fehlender Schlüssel: ..." angezeigt werden, überprüfen Sie, ob der entsprechende Schlüssel im `translations`-Dictionary für *alle* unterstützten Sprachen vorhanden ist.  Die `get_translation()`-Funktion gibt Warnungen im Log aus, wenn ein Schlüssel fehlt.
* **Falsche Sprache:** Stellen sie sicher das sie die `language=lang` Variable in der Funktion `joint_conversation_with_selected_agents` übergeben.

## Lizenz

Diese Software ist unter der MIT-Lizenz lizenziert. Siehe die Datei [LICENSE](LICENSE) für weitere Details. (Erstellen Sie eine leere Datei namens `LICENSE` und fügen Sie den MIT-Lizenztext ein).

## Beitrag

Beiträge zu diesem Projekt sind willkommen! Bitte erstellen Sie einen Pull Request mit Ihren Änderungen.

## Haftungsausschluss

Diese Software wird "wie besehen" ohne jegliche Gewährleistung bereitgestellt. Die Autoren übernehmen keine Haftung für Schäden, die durch die Verwendung dieser Software entstehen.  Die Nutzung der Google Gemini API unterliegt den Nutzungsbedingungen von Google.
