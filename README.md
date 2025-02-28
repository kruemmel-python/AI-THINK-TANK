# AI-THINK-TANK
AI THINK TANK ist eine revolutionäre, KI-gestützte Diskussionsplattform, die Experten aus verschiedenen Fachbereichen simuliert und lebendige Gespräche führt. 

# Agentenbasierte Konversationsplattform mit Gemini API und Gradio

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?style=flat-square)](https://www.python.org)
[![Gradio](https://img.shields.io/badge/Gradio-4.0+-ff5050.svg?style=flat-square)](https://gradio.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)




## ✨ Projekt-Highlights

Dieses Projekt ist **mehr als nur ein Chatbot** – es ist eine **flexible Plattform für agentenbasierte Konversationen**, die auf der leistungsstarken Gemini API von Google aufbaut und durch Gradio eine benutzerfreundliche Oberfläche erhält.

**Was dieses Projekt besonders macht:**

* **Vielfältige Agenten:** Wähle aus über 40 spezialisierten Agenten aus Bereichen wie Programmierung, Medizin, Recht, Sozialwesen, Wirtschaft, Politik und Energie. Jeder Agent kann eine eigene "Persönlichkeit" (kritisch, visionär, konservativ) haben, um die Diskussionen dynamischer und facettenreicher zu gestalten.
* **Robuste API-Integration:** Nutzt die Gemini API mit intelligenter Fehlerbehandlung (Retries, Backoff) und optimierter Anfrageverwaltung (Rate Limiting), um Zuverlässigkeit und Effizienz zu gewährleisten.
* **Eingebaute Qualitätskontrolle:**  Einfache Bewertung der Agentenantworten und automatisches Retry-System für "schlechte" Antworten, um die Qualität der Konversationen zu verbessern.
* **Benutzerverwaltung und Persistenz:**  Integriertes Benutzerregistrierungs- und Login-System, um Diskussionen zu speichern und später wieder aufzurufen. Ideal für kollaboratives Arbeiten oder zum Nachverfolgen von Gesprächsverläufen.
* **Interaktives Gradio Interface:**  Intuitive Web-Oberfläche für die Auswahl von Agenten, Themen, Gesprächsparametern und zur Echtzeit-Verfolgung der Konversation.
* **Feedback-Mechanismus:**  Integrierte Up- und Downvote-Funktion für Agentenantworten, um die Performance einzelner Agenten zu bewerten und das System kontinuierlich zu verbessern.
* **Anpassbar und Erweiterbar:**  Der modulare Aufbau des Codes ermöglicht eine einfache Anpassung und Erweiterung der Agentenliste, Persönlichkeiten, Bewertungskriterien und weiterer Funktionen.

## 🚀 Schnellstart

### Voraussetzungen

* **Python 3.9+**
* **Pip** (Python Package Installer)
* **Google Gemini API Key:**  Du benötigst einen API Key von Google AI Studio für den Zugriff auf die Gemini API.

### Installation

1. **Clone das Repository:**
   ```bash
   git clone https://github.com/kruemmel-python/AI-THINK-TANK.git
   cd AI-THINK-TANK
   ```

2. **Erstelle eine virtuelle Umgebung (empfohlen):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # oder venv\Scripts\activate unter Windows
   ```

3. **Installiere die benötigten Pakete:**
   ```bash
   pip install -r requirements.txt
   ```
   (Stelle sicher, dass du eine `requirements.txt` Datei im Repository hast. Falls nicht, erstelle sie mit: `pip freeze > requirements.txt` nach der Installation der Pakete `gradio`, `python-dotenv` und `google-generativeai`.)

4. **Konfiguriere die API-Schlüssel:**
   * Erstelle eine `.env` Datei im Hauptverzeichnis des Projekts.
   * Füge deine Gemini API Key in die `.env` Datei ein:
     ```
     API_KEY=DEIN_GEMINI_API_KEY
     ```

### Ausführen der Applikation

```bash
python app.py
```

Öffne dann deinen Browser und gehe zu der angezeigten Adresse (normalerweise `http://127.0.0.1:7860`).

## 🛠️ Nutzung

1. **Login/Registrierung:**  Erstelle ein Benutzerkonto oder logge dich ein, um Diskussionen zu speichern und zu verwalten.
2. **Agenten auswählen:** Wähle aus der Liste die Agenten aus, die an der Konversation teilnehmen sollen. Lege für jeden Agenten eine Persönlichkeit fest (z.B. "kritisch", "visionär").
3. **Parameter festlegen:**  Wähle die Anzahl der Gesprächsrunden, das Expertenlevel und die gewünschte Sprache für die Konversation.
4. **Thema eingeben:**  Gib das Diskussionsthema in das Textfeld ein.
5. **Konversation starten:** Klicke auf "Konversation starten", um die agentenbasierte Diskussion zu beginnen.
6. **Echtzeit-Verfolgung:** Verfolge die Konversation in Echtzeit im Chatbot-Fenster und im formatierten Output-Bereich.
7. **Bewertung:** Bewerte die Antworten der Agenten mit Up- oder Downvotes.
8. **Diskussion speichern:**  Speichere interessante Diskussionen für den späteren Zugriff.
9. **Gespeicherte Diskussionen laden:**  Rufe gespeicherte Diskussionen auf und setze sie fort oder überprüfe sie.

## 🧰 Anpassung und Erweiterung

* **Agentenliste erweitern:**  Füge neue Agenten mit spezifischen Fachgebieten in der `all_agents_list` hinzu.
* **Persönlichkeiten anpassen:**  Definiere weitere Persönlichkeitstypen oder modifiziere die bestehenden in der `joint_conversation_with_selected_agents` Funktion.
* **Bewertungskriterien ändern:** Passe die `evaluate_response` Funktion an, um die automatische Qualitätsbewertung der Agentenantworten zu verbessern oder zu verändern.
* **Prompt-Engineering:**  Experimentiere mit den Prompts in der `joint_conversation_with_selected_agents` Funktion, um das Verhalten der Agenten und die Qualität der Diskussionen zu beeinflussen.
* **Diagramme und Visualisierungen:**  Erweitere die Gradio-Oberfläche um Diagramme oder Visualisierungen, um die Konversationsdaten oder Agenten-Performance darzustellen (wie im Code ursprünglich angedeutet, aber aktuell nicht implementiert).
* **Integration weiterer APIs:**  Integriere weitere APIs (z.B. für Wissensdatenbanken, Faktenchecks, etc.), um die Fähigkeiten der Agenten zu erweitern.

## 📄 Lizenz

Dieses Projekt ist unter der [MIT Lizenz](LICENSE) lizenziert. Siehe die `LICENSE` Datei für Details.

## 🤝 Beitrag

Beiträge sind herzlich willkommen! Wenn du Fehler findest, Verbesserungsvorschläge hast oder neue Funktionen hinzufügen möchtest, erstelle bitte ein Issue oder einen Pull Request.

## 📧 Kontakt

Ralf Krümmel - ralf.kruemmel+python@outlook.de



 # [![Website](https://img.shields.io/badge/Website-lightgrey?style=flat-square&logo=website)](https://ciphercore.de)

---

**Viel Spaß beim Experimentieren mit der agentenbasierten Konversationsplattform!** ✨
