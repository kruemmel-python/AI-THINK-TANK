import re
import logging
import datetime
import json
import hashlib
import os
import time
import random
from collections import defaultdict
from typing import List, Dict, Tuple, Any, Union
import sqlite3
from jsonschema import validate, ValidationError
from docx import Document
from docx.shared import Inches
import streamlit as st
from google import genai
from google.generativeai.types.generation_types import StopCandidateException
import tornado
import mimetypes

# Konstanten und globale Einstellungen
MODEL_NAME_TEXT = "gemini-2.0-flash-thinking-exp-01-21"  # Für Text
MODEL_NAME_VISION = "gemini-2.0-flash-thinking-exp-01-21"  # Für Bilder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_SLEEP_SECONDS = 60       # Wartezeit zwischen API-Aufrufen
API_MAX_RETRIES = 3          # Maximale Wiederholungsanzahl bei API-Fehlern
SUMMARY_SLEEP_SECONDS = 10  # Pause nach der Zusammenfassung

AUDIT_LOG_FILE = "audit_log.txt"
EXPIRATION_TIME_SECONDS = 300
ROLE_PERMISSIONS = {
    "user": ["REQ", "DATA"],
    "admin": ["REQ", "DATA", "CALC", "IF", "AI"]
}
PRIORITY_MAP = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}

USER_DATA_FILE = "user_data.json"
DISCUSSION_DB_FILE = "discussion_data.db"
RATING_DATA_FILE = "rating_data.json"
AGENT_CONFIG_FILE = "agent_config.json"

USER_DATA_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^[a-zA-Z0-9_-]+$": {
            "type": "object",
            "properties": {
                "password": {"type": "string"}
            },
            "required": ["password"]
        }
    }
}

AGENT_CONFIG_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "personality": {"type": "string", "enum": ["kritisch", "visionär", "konservativ", "neutral"]},
            "description": {"type": "string"}
        },
        "required": ["name", "personality", "description"]
    }
}

def load_json_data(filename: str, schema: dict = None) -> Dict[str, Any]:
    """
    Lädt JSON-Daten aus einer Datei und validiert sie gegen ein gegebenes Schema.

    Args:
        filename (str): Der Name der JSON-Datei.
        schema (dict, optional): Das Schema zur Validierung der JSON-Daten.

    Returns:
        Dict[str, Any]: Die geladenen JSON-Daten.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            if schema:
                validate(instance=data, schema=schema)
            return data
    except FileNotFoundError:
        logging.warning(f"Datei '{filename}' nicht gefunden. Starte mit leeren Daten.")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Fehler beim Lesen von '{filename}': Ungültiges JSON-Format. Details: {e}")
        return {}
    except ValidationError as e:
        logging.error(f"Datei '{filename}' entspricht nicht dem erwarteten Schema: {e}")
        return {}

def save_json_data(data: Dict[str, Any], filename: str) -> None:
    """
    Speichert JSON-Daten in einer Datei.

    Args:
        data (Dict[str, Any]): Die zu speichernden Daten.
        filename (str): Der Name der Datei, in der die Daten gespeichert werden sollen.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        logging.error(f"Fehler beim Schreiben in Datei '{filename}': {e}")

def load_user_data() -> Dict[str, Any]:
    """
    Lädt Benutzerdaten aus einer JSON-Datei.

    Returns:
        Dict[str, Any]: Die geladenen Benutzerdaten.
    """
    return load_json_data(USER_DATA_FILE, USER_DATA_SCHEMA)

def save_user_data(user_data: Dict[str, Any]) -> None:
    """
    Speichert Benutzerdaten in einer JSON-Datei.

    Args:
        user_data (Dict[str, Any]): Die zu speichernden Benutzerdaten.
    """
    save_json_data(user_data, USER_DATA_FILE)

def load_rating_data() -> Dict[str, Any]:
    """
    Lädt Bewertungsdaten aus einer JSON-Datei.

    Returns:
        Dict[str, Any]: Die geladenen Bewertungsdaten.
    """
    return load_json_data(RATING_DATA_FILE)

def save_rating_data(rating_data: Dict[str, Any]) -> None:
    """
    Speichert Bewertungsdaten in einer JSON-Datei.

    Args:
        rating_data (Dict[str, Any]): Die zu speichernden Bewertungsdaten.
    """
    save_json_data(rating_data, RATING_DATA_FILE)

def load_agent_config() -> List[Dict[str, str]]:
    """
    Lädt die Agentenkonfiguration aus einer JSON-Datei.

    Returns:
        List[Dict[str, str]]: Die geladene Agentenkonfiguration.
    """
    config = load_json_data(AGENT_CONFIG_FILE, AGENT_CONFIG_SCHEMA)
    if not isinstance(config, list):
        logging.error(f"Agentenkonfiguration in '{AGENT_CONFIG_FILE}' ist ungültig oder leer.")
        return []
    return config

def hash_password(password: str) -> str:
    """
    Hasht ein Passwort mit SHA-256.

    Args:
        password (str): Das zu hashende Passwort.

    Returns:
        str: Der gehashte Passwort-String.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Überprüft, ob ein Passwort mit dem gehashten Passwort übereinstimmt.

    Args:
        password (str): Das zu überprüfende Passwort.
        hashed_password (str): Der gehashte Passwort-String.

    Returns:
        bool: True, wenn das Passwort übereinstimmt, sonst False.
    """
    return hash_password(password) == hashed_password

def register_user(username: str, password: str) -> str:
    """
    Registriert einen neuen Benutzer.

    Args:
        username (str): Der Benutzername des neuen Benutzers.
        password (str): Das Passwort des neuen Benutzers.

    Returns:
        str: Eine Nachricht, die den Status der Registrierung angibt.
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return "Ungültiger Nutzername. Nur Buchstaben, Zahlen, '-', '_' erlaubt."
    if len(password) < 8:
        return "Passwort muss mindestens 8 Zeichen lang sein."
    user_data = load_user_data()
    if username in user_data:
        return "Nutzername bereits vergeben."
    user_data[username] = {"password": hash_password(password)}
    save_user_data(user_data)
    return "Registrierung erfolgreich."

def login_user(username: str, password: str) -> Tuple[str, str]:
    """
    Loggt einen Benutzer ein.

    Args:
        username (str): Der Benutzername des Benutzers.
        password (str): Das Passwort des Benutzers.

    Returns:
        Tuple[str, str]: Eine Nachricht, die den Status des Logins angibt, und den Benutzernamen bei Erfolg.
    """
    user_data = load_user_data()
    if username in user_data and verify_password(password, user_data[username]["password"]):
        return "Login erfolgreich.", username
    return "Login fehlgeschlagen.", None

def create_discussion_table():
    """
    Erstellt die Diskussionstabelle in der SQLite-Datenbank, falls sie nicht existiert.
    """
    conn = sqlite3.connect(DISCUSSION_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discussions (
            discussion_id TEXT PRIMARY KEY,
            topic TEXT,
            agents TEXT,
            chat_history TEXT,
            summary TEXT,
            user TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

create_discussion_table()

def save_discussion_data_db(discussion_id: str, topic: str, agents: List[str], chat_history: List[Dict], summary: str, user: str = None) -> None:
    """
    Speichert Diskussionsdaten in der SQLite-Datenbank.

    Args:
        discussion_id (str): Die ID der Diskussion.
        topic (str): Das Thema der Diskussion.
        agents (List[str]): Die Liste der beteiligten Agenten.
        chat_history (List[Dict]): Der Chatverlauf der Diskussion.
        summary (str): Die Zusammenfassung der Diskussion.
        user (str, optional): Der Benutzer, der die Diskussion gestartet hat.
    """
    conn = sqlite3.connect(DISCUSSION_DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO discussions (discussion_id, topic, agents, chat_history, summary, user)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (discussion_id, topic, json.dumps(agents), json.dumps(chat_history), summary, user))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Datenbankfehler beim Speichern der Diskussion '{discussion_id}': {e}")
        conn.rollback()
    finally:
        conn.close()

def load_discussion_data_db(user: str = None) -> Dict[str, Any]:
    """
    Lädt Diskussionsdaten aus der SQLite-Datenbank.

    Args:
        user (str, optional): Der Benutzer, dessen Diskussionen geladen werden sollen.

    Returns:
        Dict[str, Any]: Die geladenen Diskussionsdaten.
    """
    conn = sqlite3.connect(DISCUSSION_DB_FILE)
    cursor = conn.cursor()
    discussions = {}
    try:
        if user:
            cursor.execute("SELECT * FROM discussions WHERE user = ?", (user,))
        else:
            cursor.execute("SELECT * FROM discussions")
        rows = cursor.fetchall()
        for row in rows:
            disc_id, topic, agents_json, chat_history_json, summary, user_name, timestamp = row
            agents = json.loads(agents_json) if agents_json else []
            chat_history = json.loads(chat_history_json) if chat_history_json else []
            discussions[disc_id] = {
                "topic": topic,
                "agents": agents,
                "chat_history": chat_history,
                "summary": summary,
                "user": user_name,
                "timestamp": timestamp
            }
    except sqlite3.Error as e:
        logging.error(f"Datenbankfehler beim Laden der Diskussionen: {e}")
    finally:
        conn.close()
    return discussions

def evaluate_response(response: str) -> str:
    """
    Bewertet eine Antwort basierend auf bestimmten Schlüsselwörtern.

    Args:
        response (str): Die zu bewertende Antwort.

    Returns:
        str: Die Bewertung der Antwort ("schlechte antwort", "gute antwort", "neutral").
    """
    resp_l = response.lower()
    if "wiederhole mich" in resp_l:
        return "schlechte antwort"
    elif "neue perspektive" in resp_l:
        return "gute antwort"
    else:
        return "neutral"

discussion_ratings = defaultdict(lambda: defaultdict(dict), load_rating_data())

def rate_agent_response(discussion_id: str, iteration: int, agent_name: str, rating_type: str) -> None:
    """
    Bewertet die Antwort eines Agenten.

    Args:
        discussion_id (str): Die ID der Diskussion.
        iteration (int): Die Iteration der Antwort.
        agent_name (str): Der Name des Agenten.
        rating_type (str): Der Typ der Bewertung ("upvote" oder "downvote").
    """
    global discussion_ratings
    if agent_name not in discussion_ratings[discussion_id][iteration]:
        discussion_ratings[discussion_id][iteration][agent_name] = {"upvotes": 0, "downvotes": 0}
    if rating_type == "upvote":
        discussion_ratings[discussion_id][iteration][agent_name]["upvotes"] += 1
    elif rating_type == "downvote":
        discussion_ratings[discussion_id][iteration][agent_name]["downvotes"] += 1
    save_rating_data(discussion_ratings)

def generate_pdf_summary_from_bytes(file_bytes: bytes, api_key: str) -> str:
    """
    Generiert eine Zusammenfassung aus PDF-Bytes.

    Args:
        file_bytes (bytes): Die Bytes der PDF-Datei.
        api_key (str): Der API-Schlüssel für den Gemini-Dienst.

    Returns:
        str: Die generierte Zusammenfassung.
    """
    try:
        mime_type = "application/pdf"
        prompt = "Fasse den Inhalt der PDF zusammen. Achte darauf, dass wichtige Daten nicht verloren gehen!"
        contents = [prompt, genai.types.Part.from_bytes(data=file_bytes, mime_type=mime_type)]
        response = call_gemini_api(contents, api_key, model=MODEL_NAME_TEXT)  # Textmodell für PDF
        return response.get("response", "Start der Konversation.")
    except Exception as e:
        logging.error("Fehler beim Generieren der PDF-Zusammenfassung:", exc_info=e)
        return "Fehler beim Verarbeiten der PDF."

def generate_image_summary_from_bytes(file_bytes: bytes, mime_type: str, api_key: str) -> str:
    """
    Generiert eine Beschreibung/Analyse aus Bild-Bytes.

    Args:
        file_bytes (bytes): Die Bytes der Bilddatei.
        mime_type (str): Der MIME-Typ der Bilddatei.
        api_key (str): Der API-Schlüssel für den Gemini-Dienst.

    Returns:
        str: Die generierte Beschreibung/Analyse.
    """
    try:
        prompt = "Beschreibe den Inhalt des Bildes detailliert. Was sind die Hauptelemente, die Stimmung, und mögliche Interpretationen?"
        contents = [prompt, genai.types.Part.from_bytes(data=file_bytes, mime_type=mime_type)]
        response = call_gemini_api(contents, api_key, model=MODEL_NAME_VISION)  # Vision-Modell für Bilder
        return response.get("response", "Start der Konversation.")
    except Exception as e:
        logging.error("Fehler beim Generieren der Bildbeschreibung:", exc_info=e)
        return "Fehler beim Verarbeiten des Bildes."

def call_gemini_api(contents: list, api_key: str, model: str) -> Dict[str, str]:
    """
    Ruft die Gemini API auf, mit Modell-Auswahl.

    Args:
        contents (list): Die Inhalte, die an die API gesendet werden sollen.
        api_key (str): Der API-Schlüssel für den Gemini-Dienst.
        model (str): Das Modell, das verwendet werden soll.

    Returns:
        Dict[str, str]: Die Antwort von der API.
    """
    client = genai.Client(api_key=api_key)
    retries = 0
    wait_time = 1
    max_wait_time = 60
    while retries < API_MAX_RETRIES:
        try:
            logging.info(f"Sende Anfrage an Gemini ({model}): {str(contents)[:100]}... (Versuch {retries + 1})")
            response = client.models.generate_content(model=model, contents=contents)  # Modell wird übergeben
            if not hasattr(response, "text") or not response.text:
                msg = "Leere Antwort von Gemini API."
                logging.warning(msg)
                return {"response": msg}
            return {"response": response.text}
        except Exception as e:
            err_s = str(e)
            logging.error(f"Gemini API Fehler: {err_s}")
            if "429" in err_s:
                retries += 1
                if retries >= API_MAX_RETRIES:
                    return {"response": f"Fehler: Maximale Anzahl an Versuchen erreicht. API-Kontingent wahrscheinlich erschöpft."}
                wait_time = min(wait_time * 2, max_wait_time)
                jitter = random.uniform(0.5, 1.5)
                actual_wait_time = wait_time * jitter
                logging.warning(f"API-Kontingent erschöpft. Warte {actual_wait_time:.2f} Sekunden...")
                time.sleep(actual_wait_time)
            else:
                return {"response": f"Fehler bei Gemini API Aufruf: {err_s}"}
    return {"response": f"Fehler: Maximale Anzahl an Versuchen erreicht ({API_MAX_RETRIES})."}

def generate_summary(text: str, api_key: str) -> str:
    """
    Generiert eine Textzusammenfassung.

    Args:
        text (str): Der zu zusammenfassende Text.
        api_key (str): Der API-Schlüssel für den Gemini-Dienst.

    Returns:
        str: Die generierte Zusammenfassung.
    """
    prompt = f"Fasse den folgenden Text prägnant zusammen:\n\n{text}"
    result = call_gemini_api([prompt], api_key, model=MODEL_NAME_TEXT)  # Textmodell
    if SUMMARY_SLEEP_SECONDS > 0:
        time.sleep(SUMMARY_SLEEP_SECONDS)
    return result.get("response", "Fehler: Keine Zusammenfassung generiert.")

def process_uploaded_file(uploaded_file, api_key: str) -> str:
    """
    Verarbeitet die hochgeladene Datei und gibt eine Zusammenfassung/Beschreibung zurück.

    Args:
        uploaded_file: Die hochgeladene Datei.
        api_key (str): Der API-Schlüssel für den Gemini-Dienst.

    Returns:
        str: Die generierte Zusammenfassung/Beschreibung.
    """
    if uploaded_file is None:
        return "Start der Konversation."

    try:
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)  # Wichtig: Zurücksetzen des Dateizeigers
        mime_type = uploaded_file.type  # MIME-Type direkt aus Streamlit-Objekt

        if mime_type == "application/pdf":
            return generate_pdf_summary_from_bytes(file_bytes, api_key)
        elif mime_type.startswith("image"):
            return generate_image_summary_from_bytes(file_bytes, mime_type, api_key)
        else:
            logging.warning(f"Nicht unterstützter Dateityp: {mime_type}")
            return f"Nicht unterstützter Dateityp: {mime_type}"

    except Exception as e:
        logging.error(f"Fehler beim Verarbeiten der Datei: {e}", exc_info=e)
        return "Fehler beim Verarbeiten der Datei."

def joint_conversation_with_selected_agents(
    conversation_topic: str,
    selected_agents: List[Dict[str, str]],
    iterations: int,
    expertise_level: str,
    language: str,
    chat_history: List[Dict[str, str]],
    user_state: str,
    discussion_id: str = None,
    api_key: str = None,
    uploaded_file=None
):
    """
    Führt eine Konversation mit ausgewählten Agenten durch.

    Args:
        conversation_topic (str): Das Thema der Konversation.
        selected_agents (List[Dict[str, str]]): Die Liste der ausgewählten Agenten.
        iterations (int): Die Anzahl der Gesprächsrunden.
        expertise_level (str): Das Experten-Level der Agenten.
        language (str): Die Sprache der Konversation.
        chat_history (List[Dict[str, str]]): Der Chatverlauf.
        user_state (str): Der Zustand des Benutzers.
        discussion_id (str, optional): Die ID der Diskussion.
        api_key (str, optional): Der API-Schlüssel für den Gemini-Dienst.
        uploaded_file: Die hochgeladene Datei.

    Yields:
        Tuple: Aktualisierter Chatverlauf, formatierter Textabschnitt, Diskussions-ID, Iterationsnummer, Agentenname.
    """
    if discussion_id is None:
        discussion_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    chat_history_filename = f"chat_history_{discussion_id}.txt"
    active_agents_names = [sa["name"] for sa in selected_agents]
    num_agents = len(active_agents_names)
    agent_outputs = [""] * num_agents
    topic_changed = False
    logging.info(f"Konversation gestartet: {active_agents_names}, iters={iterations}, level={expertise_level}, lang={language}, Diskussions-ID: {discussion_id}, Datei: {uploaded_file is not None}")

    # Dateiinhalt verarbeiten: Zusammenfassung/Beschreibung generieren
    initial_summary = process_uploaded_file(uploaded_file, api_key)
    current_summary = initial_summary

    for i in range(iterations):
        agent_idx = i % num_agents
        current_agent_name = active_agents_names[agent_idx]
        current_agent_config = next((a for a in selected_agents if a["name"] == current_agent_name), None)
        current_personality = current_agent_config.get("personality", "neutral")
        current_instruction = current_agent_config.get("instruction", "")

        prompt_text = (
            f"Wir führen eine Konversation über: '{conversation_topic}'.\n"
            + (f"Zusätzliche Informationen sind in der angehängten Datei verfügbar.\n" if uploaded_file is not None else "")
            + f"Hier ist die Zusammenfassung der bisherigen Diskussion:\n{current_summary}\n\n"
            + f"Iteration {i+1}: Agent {current_agent_name}, bitte antworte. {current_instruction}\n"
        )
        if i > 0:
            prompt_text += f"Der vorherige Agent sagte: {agent_outputs[(agent_idx - 1) % num_agents]}\n"
        if current_personality == "kritisch":
            prompt_text += "\nSei kritisch."
        elif current_personality == "visionär":
            prompt_text += "\nSei visionär."
        elif current_personality == "konservativ":
            prompt_text += "\nSei konservativ."
        prompt_text += f"\n\nAntworte auf {language}."

        # Inhalte vorbereiten: Datei-Part anhängen, falls vorhanden.
        contents = [prompt_text]
        if uploaded_file is not None:
            try:
                file_bytes = uploaded_file.read()  # Bytes erneut lesen, falls benötigt
                uploaded_file.seek(0)
                mime_type = uploaded_file.type
                contents = [prompt_text, genai.types.Part.from_bytes(data=file_bytes, mime_type=mime_type)]
            except Exception as e:
                logging.error(f"Fehler beim Lesen der Datei für Iteration {i+1}: {e}", exc_info=e)
                yield chat_history, f"Fehler beim Lesen der Datei in Iteration {i+1}.", discussion_id, (i + 1), current_agent_name  # Fehler melden
                continue  # Nächste Iteration

        api_resp = call_gemini_api(contents, api_key, model=MODEL_NAME_TEXT)  # Immer Textmodell in der Konversation
        agent_output = api_resp.get("response", f"Keine Antwort von {current_agent_name}")
        agent_outputs[agent_idx] = agent_output

        chat_history.append({
            "role": "user",
            "content": f"Agent {current_agent_name} (Iteration {i + 1}): Thema {conversation_topic}, Zusammenfassung bis Runde {i}: {current_summary}, Datei: {'vorhanden' if uploaded_file is not None else 'nicht vorhanden'}"
        })
        chat_history.append({
            "role": "assistant",
            "content": f"Antwort von Agent {current_agent_name} (Iteration {i+1}):\n{agent_output}"
        })

        try:
            with open(chat_history_filename, "w", encoding="utf-8") as f:
                for message in chat_history:
                    f.write(f"{message['role']}: {message['content']}\n")
        except IOError as e:
            logging.error(f"Fehler beim Schreiben in Chatverlauf-Datei '{chat_history_filename}': {e}")

        new_summary_input = f"Bisherige Zusammenfassung:\n{current_summary}\n\nNeue Antwort von {current_agent_name}:\n{agent_output}"
        current_summary = generate_summary(new_summary_input, api_key)
        time.sleep(API_SLEEP_SECONDS)

        qual = evaluate_response(agent_output)
        if qual == "schlechte antwort":
            logging.info(f"{current_agent_name} => 'schlechte antwort', retry ...")
            # Retry-Logik mit korrekter Behandlung der Datei
            retry_contents = ["Versuche eine kreativere Antwort."]
            if uploaded_file is not None:
                try:
                    file_bytes = uploaded_file.read()  # Bytes für Retry erneut lesen
                    uploaded_file.seek(0)
                    mime_type = uploaded_file.type
                    retry_contents = [genai.types.Part.from_bytes(data=file_bytes, mime_type=mime_type), "Versuche eine kreativere Antwort."]
                except Exception as e:
                    logging.error(f"Fehler beim Lesen der Datei für Retry: {e}", exc_info=e)
                    yield chat_history, "Fehler beim Lesen der Datei während des Retrys.", discussion_id, (i + 1), current_agent_name
                    continue
            retry_resp = call_gemini_api(retry_contents, api_key, model=MODEL_NAME_TEXT)  # Textmodell
            retry_output = retry_resp.get("response", f"Keine Retry-Antwort von {current_agent_name}")
            if "Fehler bei Gemini API Aufruf" not in retry_output:
                agent_output = retry_output
            agent_outputs[agent_idx] = agent_output

        # WICHTIG: rating_info VOR dem Yield aktualisieren
        st.session_state['rating_info']["discussion_id"] = discussion_id
        st.session_state['rating_info']["iteration"] = i + 1  # Korrekte Iterationsnummer
        st.session_state['rating_info']["agent_name"] = current_agent_name

        logging.info(f"Antwort Agent {current_agent_name} (i={i+1}): {agent_output[:50]}...")
        formatted_output_chunk = (
            f"**Iteration {i+1}: Agent {current_agent_name} ({current_personality})**\n\n"
            f"{agent_output}\n\n"
            "---\n\n"
        )
        yield chat_history, formatted_output_chunk, discussion_id, (i + 1), current_agent_name

        if i > iterations * 0.6 and agent_output == agent_outputs[(agent_idx - 1) % num_agents] and not topic_changed:
            new_topic = "Neues Thema: KI-Trends 2026"
            contents = [new_topic]
            # Neue Themenlogik mit korrekter Behandlung der Datei
            if uploaded_file is not None:
                try:
                    file_bytes = uploaded_file.read()  # Bytes erneut lesen
                    uploaded_file.seek(0)
                    mime_type = uploaded_file.type
                    contents = [new_topic, genai.types.Part.from_bytes(data=file_bytes, mime_type=mime_type)]
                except Exception as e:
                    logging.error(f"Fehler beim Lesen der Datei für neues Thema: {e}", exc_info=e)
                    yield chat_history, "Fehler beim Lesen der Datei beim Themenwechsel.", discussion_id, (i + 1), current_agent_name
                    continue

            agent_outputs = [new_topic] * num_agents
            topic_changed = True

    final_summary_input = "Gesamter Chatverlauf:\n" + "\n".join(
        [f"{m['role']}: {m['content']}" for m in chat_history]
    )
    final_summary = generate_summary(final_summary_input, api_key)
    chat_history.append({
        "role": "assistant",
        "content": f"**Gesamtzusammenfassung**:\n{final_summary}"
    })

    if user_state:
        save_discussion_data_db(discussion_id, conversation_topic, active_agents_names, chat_history, final_summary, user_state)
        logging.info(f"Diskussion {discussion_id} für {user_state} in Datenbank gespeichert.")
    else:
        logging.info("Keine Speicherung in Datenbank, kein Benutzer eingeloggt.")

    final_text = agent_outputs[-1]
    chat_history.append({
        "role": "assistant",
        "content": f"Finale Aussage:\n{final_text}"
    })
    logging.info(f"Finale Aussage: {final_text}")
    yield chat_history, final_summary, discussion_id, None, None

def save_chat_as_word(chat_history: List[Dict], discussion_id: str) -> str:
    """
    Speichert den Chatverlauf als Word-Dokument.

    Args:
        chat_history (List[Dict]): Der Chatverlauf.
        discussion_id (str): Die ID der Diskussion.

    Returns:
        str: Der Dateiname des gespeicherten Word-Dokuments.
    """
    document = Document()
    document.add_heading(f'CipherCore Agenten-Diskussion: {discussion_id}', level=1)
    for message in chat_history:
        role = message['role']
        content = message['content']
        if role == 'user':
            document.add_paragraph("Nutzer:", style='List Bullet').add_run(f" {content}").bold = True
        elif role == 'assistant':
            agent_name_match = re.search(r'Agent (.*?)\s', content)
            agent_name = agent_name_match.group(1) if agent_name_match else "Agent"
            p = document.add_paragraph(f"{agent_name}:", style='List Bullet')
            p.add_run(f" {content.split(':\n', 1)[1] if ':\n' in content else content}")
    filename = f"CipherCore_Diskussion_{discussion_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    try:
        document.save(filename)
        logging.info(f"Word-Datei '{filename}' erfolgreich gespeichert.")
        return filename
    except Exception as e:
        logging.error(f"Fehler beim Speichern der Word-Datei: {e}")
        return None

def main():
    """
    Hauptfunktion der Streamlit-Anwendung.
    """
    st.title("CipherCore Agenten-Konversation")
    st.markdown("AI-THINK-TANK – Die KI-Plattform für bahnbrechende Innovationen.")
    st.markdown("Ein Bild, eine Idee – und in Minuten entsteht eine visionäre Lösung. Von Software über Städteplanung bis hin zu neuen Geschäftsmodellen – du gibst den Impuls, die KI erschafft das Konzept! ")

    if 'user_state' not in st.session_state:
        st.session_state['user_state'] = None
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'discussion_id' not in st.session_state:
        st.session_state['discussion_id'] = None
    if 'rating_info' not in st.session_state:
        st.session_state['rating_info'] = {}
    if 'formatted_output_text' not in st.session_state:
        st.session_state['formatted_output_text'] = ""
    if 'api_key' not in st.session_state:
        st.session_state['api_key'] = None
    if 'uploaded_file' not in st.session_state:
        st.session_state['uploaded_file'] = None

    st.sidebar.header("API-Schlüssel")
    api_key = st.sidebar.text_input("Geben Sie Ihren Gemini API-Schlüssel ein:", type="password")
    if not api_key:
        st.warning("Bitte geben Sie einen API-Schlüssel ein, um die Anwendung zu nutzen.")
        return
    else:
        st.session_state['api_key'] = api_key

    with st.expander("Login / Registrierung", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Login")
            username_login = st.text_input("Nutzername", key="username_login")
            password_login = st.text_input("Passwort", type="password", key="password_login")
            login_btn = st.button("Login")
            login_status = st.empty()
            if login_btn:
                msg, logged_in_user = login_user(username_login, password_login)
                if logged_in_user:
                    st.session_state['user_state'] = logged_in_user
                    login_status.success(msg)
                    st.rerun()
                else:
                    login_status.error(msg)
        with col2:
            st.subheader("Registrierung")
            username_register = st.text_input("Nutzername", key="username_register")
            password_register = st.text_input("Passwort", type="password", key="password_register")
            register_btn = st.button("Registrieren")
            register_status = st.empty()
            if register_btn:
                msg = register_user(username_register, password_register)
                register_status.info(msg)

    st.markdown("---")
    agent_config_data = load_agent_config()
    agent_selections = {}
    st.subheader("Agenten Auswahl")
    with st.expander("Agenten Auswahl (auf-/zuklappbar)", expanded=False):
        for agent_data in agent_config_data:
            agent_selections[agent_data["name"]] = {
                "selected": st.checkbox(agent_data["name"]),
                "personality": st.radio(
                    f"Persönlichkeit für {agent_data['name']}",
                    ["kritisch", "visionär", "konservativ", "neutral"],
                    horizontal=True,
                    key=f"personality_{agent_data['name']}"
                )
            }

    topic_input = st.text_input("Diskussionsthema")
    iteration_slider = st.slider("Anzahl Gesprächsrunden", 1, 50, value=10, step=1)
    level_radio = st.radio("Experten-Level", ["Beginner", "Fortgeschritten", "Experte"], horizontal=True)
    lang_radio = st.radio("Sprache", ["Deutsch", "Englisch", "Französisch", "Spanisch"], horizontal=True)

    st.subheader("Datei hochladen (optional)")
    uploaded_file = st.file_uploader("Wählen Sie eine Datei aus (PDF, PNG, JPG, JPEG, GIF)", type=["pdf", "png", "jpg", "jpeg", "gif"])

    if uploaded_file is not None:
        st.session_state['uploaded_file'] = uploaded_file
        file_type = uploaded_file.type
        st.write(f"Hochgeladener Dateityp: {file_type}")

        if file_type.startswith("image"):
            st.image(uploaded_file)
        elif file_type == "application/pdf":
            st.write("PDF-Datei hochgeladen (Vorschau nicht unterstützt)")
        else:
            st.write("Datei hochgeladen")

    with st.expander("Gespeicherte Diskussionen", expanded=False):
        load_disc_btn = st.button("Diskussionen laden")
        saved_discussions = st.empty()
        if load_disc_btn:
            if st.session_state['user_state']:
                disc_data = load_discussion_data_db(st.session_state['user_state'])
                saved_discussions.json(disc_data)
            else:
                saved_discussions.warning("Bitte zuerst einloggen.")

    start_btn = st.button("Konversation starten")

    st.subheader("Agenten-Konversation")
    for message in st.session_state['chat_history']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    st.subheader("Formatierter Output")
    st.markdown(st.session_state['formatted_output_text'])

    rating_col1, rating_col2, rating_col3 = st.columns([1, 1, 3])
    if st.session_state['rating_info'].get("iteration") is not None:
        with rating_col1:
            upvote_btn = st.button("👍 Upvote")
        with rating_col2:
            downvote_btn = st.button("👎 Downvote")
        with rating_col3:
            rating_label = st.empty()

        if upvote_btn:
            did = st.session_state['rating_info'].get("discussion_id")
            itn = st.session_state['rating_info'].get("iteration")
            agn = st.session_state['rating_info'].get("agent_name")
            if did and itn and agn:
                rate_agent_response(did, itn, agn, "upvote")
                rating_label.success("👍 Upvote gegeben")
            else:
                rating_label.error("Fehler beim Upvote (fehlende Daten).")
        if downvote_btn:
            did = st.session_state['rating_info'].get("discussion_id")
            itn = st.session_state['rating_info'].get("iteration")
            agn = st.session_state['rating_info'].get("agent_name")
            if did and itn and agn:
                rate_agent_response(did, itn, agn, "downvote")
                rating_label.success("👎 Downvote gegeben")
            else:
                rating_label.error("Fehler beim Downvote (fehlende Daten).")

    save_col1, save_col2 = st.columns(2)
    with save_col1:
        save_btn = st.button("Diskussion speichern")
        save_status = st.empty()
        if save_btn:
            if st.session_state['user_state']:
                active_agents_names = [agent['name'] for agent in agent_config_data if agent_selections[agent['name']]['selected']]
                save_discussion_data_db(st.session_state['discussion_id'], topic_input, active_agents_names, st.session_state['chat_history'], "Manuell gespeichert", st.session_state['user_state'])
                save_status.success("Diskussion in Datenbank gespeichert.")
            else:
                save_status.warning("Bitte zuerst einloggen.")
    with save_col2:
        word_save_btn = st.button("Chat als Word speichern")
        if word_save_btn:
            if st.session_state['discussion_id']:
                word_filename = save_chat_as_word(st.session_state['chat_history'], st.session_state['discussion_id'])
                if word_filename:
                    with open(word_filename, "rb") as file:
                        st.download_button(
                            label="Word-Datei herunterladen",
                            data=file,
                            file_name=word_filename,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                else:
                    st.error("Fehler beim Erstellen der Word-Datei.")
            else:
                st.warning("Diskussions-ID fehlt. Starten Sie zuerst eine Konversation.")

    if start_btn:
        selected_agents = [
            {"name": agent, "personality": agent_selections[agent]["personality"], "instruction": next((a["description"] for a in agent_config_data if a["name"] == agent), "")}
            for agent in agent_selections if agent_selections[agent]["selected"]
        ]
        if not selected_agents:
            st.warning("Bitte wähle mindestens einen Agenten aus.")
        else:
            st.session_state['chat_history'] = []
            st.session_state['formatted_output_text'] = ""
            st.session_state['discussion_id'] = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            st.session_state['rating_info'] = {}
            try:
                with st.spinner("Konversation wird gestartet..."):
                    agent_convo = joint_conversation_with_selected_agents(
                        conversation_topic=topic_input,
                        selected_agents=selected_agents,
                        iterations=iteration_slider,
                        expertise_level=level_radio,
                        language=lang_radio,
                        chat_history=[],
                        user_state=st.session_state['user_state'],
                        discussion_id=st.session_state['discussion_id'],
                        api_key=st.session_state['api_key'],
                        uploaded_file=st.session_state.get('uploaded_file')
                    )
                    for updated_hist, chunk_text, disc_id, iteration_num, agent_n in agent_convo:
                        st.session_state['discussion_id'] = disc_id
                        st.session_state['rating_info']["discussion_id"] = disc_id
                        st.session_state['rating_info']["iteration"] = iteration_num
                        st.session_state['rating_info']["agent_name"] = agent_n

                        if updated_hist and len(updated_hist) > len(st.session_state['chat_history']):
                            new_messages = updated_hist[len(st.session_state['chat_history']):]
                            for message in new_messages:
                                st.session_state['chat_history'].append(message)
                                with st.chat_message(message["role"]):
                                    st.markdown(message["content"])
                            st.session_state['formatted_output_text'] += chunk_text

            except (tornado.websocket.WebSocketClosedError, tornado.iostream.StreamClosedError) as e:
                st.error(f"Verbindungsfehler: {e}. Bitte versuche es später erneut. Möglicherweise ist die Konversation zu lang oder das Netzwerk ist instabil.")
            except StopCandidateException as e:
                st.error(f"Die Konversation wurde unerwartet beendet: {e}")
            except Exception as e:
                st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    main()
