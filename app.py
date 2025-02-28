import re
import logging
import datetime
import gradio as gr
import json
import hashlib
import io
import os
import time
from collections import defaultdict
from typing import List, Dict, Tuple, Any

from dotenv import load_dotenv
from google import genai

# ---------------------------
# 1) Konfiguration und Setup
# ---------------------------
load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL_NAME = "gemini-2.0-flash-thinking-exp-01-21"

if not API_KEY:
    raise ValueError("API_KEY nicht in .env gefunden!")

client = genai.Client(api_key=API_KEY)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_SLEEP_SECONDS = 10      # Wartezeit nach jedem Request
API_MAX_RETRIES = 2         # Wie oft bei 503 nochmal probieren

AUDIT_LOG_FILE = "audit_log.txt"
EXPIRATION_TIME_SECONDS = 300
ROLE_PERMISSIONS = {
    "user": ["REQ", "DATA"],
    "admin": ["REQ", "DATA", "CALC", "IF", "AI"]
}
PRIORITY_MAP = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}

# ---------------------------
# 2) Nutzer-Login-System (als JSON)
# ---------------------------
USER_DATA_FILE = "user_data.json"
DISCUSSION_DATA_FILE = "discussion_data.json"
RATING_DATA_FILE = "rating_data.json"

def load_user_data() -> Dict[str, Any]:
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_data(user_data: Dict[str, Any]) -> None:
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=4)

def load_discussion_data() -> Dict[str, Any]:
    try:
        with open(DISCUSSION_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_discussion_data(discussion_data: Dict[str, Any]) -> None:
    with open(DISCUSSION_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(discussion_data, f, indent=4)

def load_rating_data() -> Dict[str, Any]:
    try:
        with open(RATING_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_rating_data(rating_data: Dict[str, Any]) -> None:
    with open(RATING_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(rating_data, f, indent=4)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password

def register_user(username: str, password: str) -> str:
    user_data = load_user_data()
    if username in user_data:
        return "Nutzername bereits vergeben."
    user_data[username] = {"password": hash_password(password)}
    save_user_data(user_data)
    return "Registrierung erfolgreich."

def login_user(username: str, password: str) -> Tuple[str, str]:
    """ Gibt (Meldung, username_oder_None) zurück """
    user_data = load_user_data()
    if username in user_data and verify_password(password, user_data[username]["password"]):
        return "Login erfolgreich.", username
    return "Login fehlgeschlagen.", None

# ---------------------------
# 3) Bewertung der Antwort
# ---------------------------
def evaluate_response(response: str) -> str:
    resp_l = response.lower()
    if "wiederhole mich" in resp_l:
        return "schlechte antwort"
    elif "neue perspektive" in resp_l:
        return "gute antwort"
    else:
        return "neutral"

# ---------------------------
# 4) Up-/Downvotes
# ---------------------------
discussion_ratings = defaultdict(lambda: defaultdict(dict), load_rating_data())

def rate_agent_response(discussion_id: str, iteration: int, agent_name: str, rating_type: str) -> None:
    """
    Verhindert KeyError, indem wir (discussion_id, iteration, agent_name) bei Bedarf anlegen.
    """
    global discussion_ratings
    if agent_name not in discussion_ratings[discussion_id][iteration]:
        discussion_ratings[discussion_id][iteration][agent_name] = {"upvotes": 0, "downvotes": 0}

    if rating_type == "upvote":
        discussion_ratings[discussion_id][iteration][agent_name]["upvotes"] += 1
    elif rating_type == "downvote":
        discussion_ratings[discussion_id][iteration][agent_name]["downvotes"] += 1

    save_rating_data(discussion_ratings)

# ---------------------------
# 5) Gemini-API mit Retry und Wartezeit
# ---------------------------
def call_gemini_api(prompt: str) -> Dict[str, str]:
    """
    Ruft die Gemini-API mit bis zu API_MAX_RETRIES Retries auf,
    schläft nach jedem Aufruf API_SLEEP_SECONDS Sekunden.
    """
    for attempt in range(API_MAX_RETRIES + 1):
        try:
            logging.info(f"[{attempt+1}/{API_MAX_RETRIES+1}] Sende Prompt an Gemini: {prompt[:100]}...")
            response = client.models.generate_content(model=MODEL_NAME, contents=[prompt])

            # Warte 10 Sekunden
            time.sleep(API_SLEEP_SECONDS)

            if not hasattr(response, "text") or not response.text:
                msg = "Leere Antwort von Gemini API."
                logging.warning(msg)
                return {"response": msg}

            return {"response": response.text}

        except Exception as e:
            err_s = str(e)
            logging.error(f"Fehler bei Gemini API Aufruf (Versuch {attempt+1}): {err_s}")
            # Wenn 503 Overloaded -> warte und Retry
            if "503 UNAVAILABLE" in err_s and attempt < API_MAX_RETRIES:
                logging.info("Überlastet, warte weitere 10s und versuche erneut.")
                time.sleep(API_SLEEP_SECONDS)
                continue
            # Sonst Abbruch
            return {"response": f"Fehler bei Gemini API Aufruf: {err_s}"}

    # Falls alle Versuche scheitern
    return {"response": "Unbekannter Fehler nach mehreren Versuchen."}

# ---------------------------
# 6) Generator-Funktion (Alle Agenten, kein Diagramm)
# ---------------------------
def joint_conversation_with_selected_agents(
    conversation_topic: str,
    selected_agents: List[Dict[str, str]],
    iterations: int,
    expertise_level: str,
    language: str,
    chat_history: List[Dict[str, str]],
    user_state: str,
    discussion_id: str = None
):
    """
    user_state: der eingeloggte Nutzername (oder None).
    """
    if discussion_id is None:
        discussion_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    active_agents_names = [sa["name"] for sa in selected_agents]
    num_agents = len(active_agents_names)
    agent_outputs = [""] * num_agents
    topic_changed = False

    logging.info(f"Konversation gestartet: {active_agents_names}, iters={iterations}, level={expertise_level}, lang={language}")

    for i in range(iterations):
        agent_idx = i % num_agents
        current_agent_name = active_agents_names[agent_idx]
        current_personality = next((a["personality"] for a in selected_agents if a["name"] == current_agent_name), "neutral")

        prev_agent_name = active_agents_names[(agent_idx - 1) % num_agents]
        prev_output = agent_outputs[(agent_idx - 1) % num_agents]

        prompt_txt = (
            f"Wir führen eine Konversation über: '{conversation_topic}'.\n"
            f"Iteration {i+1}: Agent {current_agent_name} (Spezialist für **{current_agent_name}**) antwortet Agent {prev_agent_name}.\n" # HIER IST DIE ÄNDERUNG!
            f"Agent {prev_agent_name} sagte: {prev_output}\n"
        )

        # Persönlichkeit
        if current_personality == "kritisch":
            prompt_txt += "\nSei kritisch und hinterfrage Annahmen."
        elif current_personality == "visionär":
            prompt_txt += "\nSei visionär und denke groß."
        elif current_personality == "konservativ":
            prompt_txt += "\nSei konservativ und bleibe bei Bewährtem."

        # Sprache
        if language == "Deutsch":
            prompt_txt += "\n\nAntworte auf Deutsch."
        elif language == "Englisch":
            prompt_txt += "\n\nRespond in English."
        elif language == "Französisch":
            prompt_txt += "\n\nRépondez en français."
        elif language == "Spanisch":
            prompt_txt += "\n\nResponde en español."

        chat_history.append({
            "role": "user",
            "content": f"Agent {current_agent_name} (Iteration {i+1}): Thema {conversation_topic}, vorheriger: {prev_agent_name}: {prev_output}"
        })

        api_resp = call_gemini_api(prompt_txt)
        agent_output = api_resp.get("response", f"Keine Antwort von {current_agent_name}")
        agent_outputs[agent_idx] = agent_output

        # Bewertungscheck
        qual = evaluate_response(agent_output)
        if qual == "schlechte antwort":
            logging.info(f"{current_agent_name} => 'schlechte antwort', retry ...")
            retry_resp = call_gemini_api("Versuche eine kreativere Antwort.")
            retry_output = retry_resp.get("response", f"Keine Retry-Antwort von {current_agent_name}")
            if "Fehler bei Gemini API Aufruf" not in retry_output:
                agent_output = retry_output
            agent_outputs[agent_idx] = agent_output

        # Chat-Historie (assistant)
        chat_history.append({
            "role": "assistant",
            "content": f"Antwort von Agent {current_agent_name} (Iteration {i+1}):\n{agent_output}"
        })
        logging.info(f"Antwort Agent {current_agent_name} (i={i+1}): {agent_output}")

        formatted_output_chunk = (
            f"**Iteration {i+1}: Agent {current_agent_name} ({current_personality})**\n\n"
            f"{agent_output}\n\n"
            "---\n\n"
        )

        # yield 5 Werte (keine Diagramme!)
        yield chat_history, formatted_output_chunk, discussion_id, (i+1), current_agent_name

        # Thema wechseln
        if i > (iterations * 0.6) and agent_output == agent_outputs[(agent_idx - 1) % num_agents] and not topic_changed:
            new_topic = "Neues Thema: KI-Trends 2026"
            agent_outputs = [new_topic] * num_agents
            topic_changed = True

    # Zusammenfassung
    sum_prompt = f"Fasse die gesamte Diskussion über '{conversation_topic}' zusammen."
    sum_resp = call_gemini_api(sum_prompt)
    sum_text = sum_resp.get("response", "Keine Zusammenfassung generiert.")
    chat_history.append({
        "role": "assistant",
        "content": f"**Zusammenfassung**:\n{sum_text}"
    })

    # Speichern in Diskussionsdaten, falls eingeloggt
    if user_state:  # user_state != None => eingeloggt
        ddata = load_discussion_data()
        ddata[discussion_id] = {
            "topic": conversation_topic,
            "agents": active_agents_names,
            "chat_history": chat_history,
            "summary": sum_text,
            "user": user_state
        }
        save_discussion_data(ddata)
        logging.info(f"Diskussion {discussion_id} für {user_state} gespeichert.")
    else:
        logging.info("Keine Speicherung, kein Benutzer eingeloggt.")

    final_text = agent_outputs[-1]
    chat_history.append({
        "role": "assistant",
        "content": f"Finale Aussage:\n{final_text}"
    })

    logging.info(f"Finale Aussage: {final_text}")

    # Letzter yield, 5 Werte
    yield chat_history, sum_text, discussion_id, None, None

# ---------------------------
# 7) Gradio App ohne Diagramm
# ---------------------------
with gr.Blocks() as demo:
    gr.Markdown("## Verbessertes Beispiel: 10s Delay, 2 Retries, Alle Agenten, Kein Diagramm, Persistenter Login via gr.State")

    # State für user_name
    user_state = gr.State(value=None)  # Hier speichern wir den aktuell eingeloggten Nutzer

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Login")
            username_login = gr.Textbox(label="Nutzername")
            password_login = gr.Textbox(label="Passwort", type="password")
            login_btn = gr.Button("Login")
            login_status_label = gr.Label(label="Login-Status")

        with gr.Column():
            gr.Markdown("### Registrierung")
            username_register = gr.Textbox(label="Nutzername")
            password_register = gr.Textbox(label="Passwort", type="password")
            register_btn = gr.Button("Registrieren")
            register_status_label = gr.Label(label="Registrierungs-Status")

    def login_event(u_name, u_pass, current_usr):
        msg, logged_in_user = login_user(u_name, u_pass)
        if logged_in_user:
            return msg, logged_in_user
        else:
            return msg, current_usr  # bleibt None

    def register_event(u_name, u_pass):
        return register_user(u_name, u_pass)

    login_btn.click(
        fn=login_event,
        inputs=[username_login, password_login, user_state],
        outputs=[login_status_label, user_state]
    )

    register_btn.click(
        fn=register_event,
        inputs=[username_register, password_register],
        outputs=[register_status_label]
    )

    gr.Markdown("---")

    # Agenten-Liste
    all_agents_list = [
        # Programmierung
        "Webentwicklung", "Datenwissenschaft", "Machine Learning", "Scripting und Automation",
        "Backend Entwicklung und APIs", "Testing und Qualitätssicherung", "Code Generierung und Integration",
        # Medizin
        "Neurologie", "Kardiologie", "Virologie", "Onkologie", "Radiologie", "Pädiatrie",
        # Recht
        "Strafrecht", "EU-Datenschutz (GDPR, AI Act)", "Arbeitsrecht", "Vertragsrecht", "Immobilienrecht", "Urheberrecht",
        # Soziales
        "Sozialarbeit", "Psychologie", "Bildung", "Gemeinschaftsentwicklung", "Sozialpolitik", "Kulturelle Studien",
        # Wirtschaft
        "Finanzmärkte", "Startups & Innovation", "Marketing", "HR-Management", "Unternehmensführung", "Nachhaltigkeit",
        # Politik
        "Internationale Beziehungen", "Umweltpolitik", "Wirtschaftspolitik", "Sozialpolitik", "Bildungspolitik", "Gesundheitspolitik",
        # Energie
        "Erneuerbare Energien", "Kernfusion", "Energieeffizienz", "Energiespeicherung", "Energiepolitik", "Nachhaltige Energie"
    ]

    agent_checkboxes = []
    agent_personalities_radios = []

    gr.Markdown("### Wähle Agenten und deren Persönlichkeit:")
    with gr.Column():
        for a_name in all_agents_list:
            with gr.Row():
                cbox = gr.Checkbox(label=a_name)
                radio = gr.Radio(["kritisch", "visionär", "konservativ"], value="kritisch", label="Persönlichkeit")
                agent_checkboxes.append(cbox)
                agent_personalities_radios.append(radio)

    iteration_slider = gr.Slider(20, 100, value=10, step=1, label="Anzahl Gesprächsrunden")
    level_radio = gr.Radio(["Beginner", "Fortgeschritten", "Experte"], value="Experte", label="Experten-Level")
    lang_radio = gr.Radio(["Deutsch", "Englisch", "Französisch", "Spanisch"], value="Deutsch", label="Sprache")

    topic_input = gr.Textbox(label="Diskussionsthema")

    # Gespeicherte Diskussionen ansehen
    with gr.Accordion("Gespeicherte Diskussionen"):
        saved_disc_label = gr.JSON()
        load_disc_btn = gr.Button("Diskussionen laden")

        def load_discs(current_usr):
            disc_data = load_discussion_data()
            if current_usr:
                # Nur die, die zum User passen
                filtered = {k: v for k, v in disc_data.items() if v.get("user") == current_usr}
                return filtered
            else:
                return {"Warnung": "Niemand eingeloggt."}

        load_disc_btn.click(
            fn=load_discs,
            inputs=[user_state],
            outputs=[saved_disc_label]
        )

    # Chatbot
    chatbot = gr.Chatbot(label="Agenten-Konversation", type="messages")
    formatted_output_md = gr.Markdown(label="Formatierter Output")

    rating_row = gr.Row(visible=False)
    with rating_row:
        upvote_btn = gr.Button("👍")
        downvote_btn = gr.Button("👎")
        rating_label = gr.Label("Bewertung: Nicht bewertet")
        rating_info = gr.State({})

    with gr.Row():
        start_btn = gr.Button("Konversation starten")
        save_btn = gr.Button("Diskussion speichern")

    def process_input_custom_agents(
        user_topic, chat_history, rating_state, current_usr_state,
        *args
    ):
        """
        Diese Funktion ruft joint_conversation_with_selected_agents(...) auf
        und yieldet Zwischenergebnisse an Gradio.
        """
        total = len(all_agents_list)
        cbox_vals = args[:total]              # Checkbox booleans
        pers_vals = args[total:2*total]       # Radios (kritisch, visionär, etc.)
        iters = args[2*total]                # iteration_slider
        level = args[2*total + 1]            # level_radio
        lang = args[2*total + 2]             # lang_radio
        discussion_id_state = args[2*total + 3]

        # Sammle ausgewählte Agenten
        selected_agents = []
        for i, agn in enumerate(all_agents_list):
            if cbox_vals[i]:
                selected_agents.append({"name": agn, "personality": pers_vals[i]})

        if not selected_agents:
            yield ("Keine Agenten ausgewählt!", "", discussion_id_state, gr.update(visible=False), rating_state)
            return

        if discussion_id_state is None:
            discussion_id_state = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        agent_convo = joint_conversation_with_selected_agents(
            conversation_topic=user_topic,
            selected_agents=selected_agents,
            iterations=iters,
            expertise_level=level,
            language=lang,
            chat_history=chat_history,
            user_state=current_usr_state,  # Hier übergeben wir den eingeloggten Nutzer
            discussion_id=discussion_id_state
        )

        formatted_output_text = ""
        for updated_hist, chunk_text, disc_id, iteration_num, agent_n in agent_convo:
            formatted_output_text += chunk_text
            rating_state["discussion_id"] = disc_id
            rating_state["iteration"] = iteration_num
            rating_state["agent_name"] = agent_n

            # 5 Outputs: chat_history, formatted_str, discussion_id_state, rating_row.update(visible), rating_state
            yield (
                updated_hist,
                formatted_output_text,
                disc_id,
                gr.update(visible=True),
                rating_state
            )

    def save_discussion_manually(
        history, user_topic, dummy_state, fmt_output, discussion_id_in, user_state_in
    ):
        """ Speichert die Diskussion. """
        if user_state_in:
            data = load_discussion_data()
            data[discussion_id_in] = {
                "topic": user_topic,
                "chat_history": history,
                "summary": "Siehe formatierten Output",
                "user": user_state_in
            }
            save_discussion_data(data)
            return "Diskussion gespeichert."
        else:
            return "Bitte zuerst einloggen."

    def upvote_event(r_state: dict):
        did = r_state.get("discussion_id")
        itn = r_state.get("iteration")
        agn = r_state.get("agent_name")
        if did and itn and agn:
            rate_agent_response(did, itn, agn, "upvote")
            return "👍 Upvote gegeben"
        return "Fehler beim Upvote (fehlende Daten)."

    def downvote_event(r_state: dict):
        did = r_state.get("discussion_id")
        itn = r_state.get("iteration")
        agn = r_state.get("agent_name")
        if did and itn and agn:
            rate_agent_response(did, itn, agn, "downvote")
            return "👎 Downvote gegeben"
        return "Fehler beim Downvote (fehlende Daten)."

    # Klick auf "Konversation starten"
    start_btn.click(
        fn=process_input_custom_agents,
        inputs=[
            topic_input,           # user_topic
            chatbot,               # chat_history
            rating_info,           # rating_state
            user_state,            # current_usr_state
            *agent_checkboxes,     # 43 Checkboxes
            *agent_personalities_radios,  # 43 Radios
            iteration_slider,
            level_radio,
            lang_radio,
            gr.State(None)         # discussion_id
        ],
        outputs=[
            chatbot,               # (chat_history)
            formatted_output_md,   # (formatted_output_text)
            gr.State(),            # (discussion_id)
            rating_row,            # (visible=True)
            rating_info            # rating_state
        ]
    )

    # Klick auf "Diskussion speichern"
    save_btn.click(
        fn=save_discussion_manually,
        inputs=[
            chatbot,               # chat_history
            topic_input,           # user_topic
            gr.State(None),        # dummy
            formatted_output_md,   # fmt_output
            gr.State(),            # discussion_id_in
            user_state             # user_state_in
        ],
        outputs=[register_status_label]  # Z. B. in dasselbe Label wie "Registrierungs-Status"
    )

    upvote_btn.click(upvote_event, inputs=[rating_info], outputs=[rating_label])
    downvote_btn.click(downvote_event, inputs=[rating_info], outputs=[rating_label])

demo.launch(share=True)