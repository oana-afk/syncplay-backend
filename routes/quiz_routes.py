from flask import Blueprint, jsonify
from services.data_loader import load_quiz_data
import threading
import time
import os
import json
import random
from firebase_utils import init_firebase

quiz_bp = Blueprint('quiz_bp', __name__)

# Fișier local pentru a citi întrebarea activă
ACTIVE_QUESTION_FILE = "active_questions.json"

# Întrebare activă în memorie, pentru când fișierul este șters între reporniri
_active_questions = {
    "detectivul_din_canapea": "q1"  # Valoare hardcodată pentru a asigura afișarea
}

# Cache pentru quiz-uri
_quiz_data_cache = None
_last_cache_update = 0
CACHE_TIMEOUT = 300  # 5 minute

# Inițializează fișierul active_questions.json la pornire
def initialize_active_questions_file():
    """Creează fișierul active_questions.json dacă nu există"""
    if not os.path.exists(ACTIVE_QUESTION_FILE):
        try:
            with open(ACTIVE_QUESTION_FILE, 'w') as f:
                json.dump(_active_questions, f)
            print(f"✅ Fișierul {ACTIVE_QUESTION_FILE} creat cu succes")
        except Exception as e:
            print(f"❌ Eroare la crearea fișierului {ACTIVE_QUESTION_FILE}: {e}")

# Inițializează fișierul la import
initialize_active_questions_file()

def get_quiz_data_with_timeout(timeout=2):
    """Obține datele quiz cu timeout și caching"""
    global _quiz_data_cache, _last_cache_update

    # Verifică cache-ul întâi
    current_time = time.time()
    # 💣 Dezactivăm complet cache-ul pentru debugging live (temporar sau permanent)
    _quiz_data_cache = None
    _last_cache_update = 0

    result = None
    timeout_occurred = False

    def fetch_data():
        nonlocal result
        try:
            result = load_quiz_data()
        except Exception as e:
            print(f"❌ Eroare la încărcarea quiz-urilor: {e}")
            result = None

    # Pornește thread-ul pentru a încărca datele
    thread = threading.Thread(target=fetch_data)
    thread.daemon = True
    thread.start()

    # Așteaptă thread-ul cu timeout
    thread.join(timeout)

    if thread.is_alive():
        timeout_occurred = True
        print(f"⚠️ Timeout la încărcarea quiz-urilor după {timeout} secunde")

        # Returnează cache-ul vechi dacă există
        if _quiz_data_cache is not None:
            print("🔄 Folosind cache-ul vechi pentru quiz-uri")
            return _quiz_data_cache

        # Altfel returnează date statice de fallback
        return [
            {
                "question": "Care este capitala Franței?",
                "options": ["Paris", "Berlin", "Madrid", "Roma"],
                "correct": "Paris",
                "id": "q1"
            },
            {
                "question": "Ce simbol are fluorul?",
                "options": ["Fl", "F", "Fr", "Fe"],
                "correct": "F",
                "id": "q2"
            },
            {
                "question": "Câte continente are planeta Pământ?",
                "options": ["5", "6", "7", "8"],
                "correct": "7",
                "id": "q3"
            }
        ]

    # Verifică rezultatul și actualizează cache-ul dacă este valid
    if result is not None and not isinstance(result, dict) and "error" not in result:
        _quiz_data_cache = result
        _last_cache_update = current_time
        return result

    if _quiz_data_cache is not None:
        print("⚠️ Eroare la obținerea quiz-urilor, folosim cache-ul vechi")
        return _quiz_data_cache

    return [
        {
            "question": "Care este capitala Franței?",
            "options": ["Paris", "Berlin", "Madrid", "Roma"],
            "correct": "Paris",
            "id": "q1"
        },
        {
            "question": "Ce simbol are fluorul?",
            "options": ["Fl", "F", "Fr", "Fe"],
            "correct": "F",
            "id": "q2"
        },
        {
            "question": "Câte continente are planeta Pământ?",
            "options": ["5", "6", "7", "8"],
            "correct": "7",
            "id": "q3"
        }
    ]

def save_active_question_local(show_id, question_id):
    """Salvează întrebarea activă în fișier și memoria locală"""
    global _active_questions

    # Actualizează dicționarul în memorie
    _active_questions[show_id] = question_id

    # Salvează și în fișier pentru persistență între cereri
    try:
        # Asigură-te că fișierul există înainte de a-l citi
        initialize_active_questions_file()

        # Încearcă să citești conținutul existent dacă există
        try:
            with open(ACTIVE_QUESTION_FILE, 'r') as f:
                active_questions = json.load(f)
        except Exception:
            active_questions = {}

        # Actualizează și salvează înapoi
        active_questions[show_id] = question_id
        with open(ACTIVE_QUESTION_FILE, 'w') as f:
            json.dump(active_questions, f)

        print(f"✅ Întrebare salvată: {question_id} pentru show: {show_id}")
        return True
    except Exception as e:
        print(f"❌ Eroare la salvare: {e}")
        return False

def get_active_question_live(show_id):
    """Obține întrebarea activă din Firebase metadata/status"""
    try:
        db = init_firebase()
        if not db:
            print("⚠️ Firebase indisponibil, fallback pe local")
            return get_active_question_local(show_id)

        doc_ref = db.collection('shows').document(show_id).collection('metadata').document('status')
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data.get("current_question_id", "q1")
        else:
            print("⚠️ Documentul status nu există")
    except Exception as e:
        print(f"🔥 Eroare la citirea întrebării active din Firebase: {e}")

    return get_active_question_local(show_id)

def get_active_question_local(show_id):
    """Obține întrebarea activă din fișierul local"""
    try:
        with open(ACTIVE_QUESTION_FILE, 'r') as f:
            active_questions = json.load(f)
            return active_questions.get(show_id, "q1")
    except Exception as e:
        print(f"⚠️ Eroare la citirea fișierului local: {e}")
        return _active_questions.get(show_id, "q1")

def reorder_questions_with_active_first(questions, active_id):
    """Reordonează întrebările pentru a pune întrebarea activă prima"""
    if not active_id:
        print("⚠️ Nu există întrebare activă, nu reordonăm")
        return questions

    print(f"🔍 Căutăm întrebarea activă cu ID: {active_id} în {len(questions)} întrebări")

    # Logăm toate ID-urile pentru a vedea ce avem
    question_ids = []
    for q in questions:
        q_id = q.get("id", "MISSING_ID")
        question_ids.append(q_id)

    print(f"📋 ID-uri disponibile: {question_ids}")

    active_question = None
    other_questions = []

    for q in questions:
        # Verificăm fiecare întrebare pentru potrivire ID
        q_id = q.get("id", "MISSING_ID")
        if q_id == active_id:
            print(f"✅ Am găsit întrebarea activă: {q_id}")
            active_question = q
        else:
            other_questions.append(q)

    if active_question:
        print(f"✅ Punem întrebarea activă ({active_id}) prima în listă")
        return [active_question] + other_questions
    else:
        print(f"❌ Întrebarea activă cu ID {active_id} nu a fost găsită în lista de întrebări!")

    return questions

def get_show_title(show_id):
    """Obține titlul emisiunii din Firebase (fallback: formatat din show_id)"""
    try:
        db = init_firebase()
        doc = db.collection("shows").document(show_id).get()
        if doc.exists:
            return doc.to_dict().get("title", show_id.replace("_", " ").title())
    except Exception as e:
        print(f"⚠️ Eroare la citirea titlului pentru {show_id}: {e}")
    return show_id.replace("_", " ").title()

@quiz_bp.route('/debug', methods=['GET'])
def debug_quiz():
    """Endpoint de debug pentru a inspecta toate datele relevante"""
    all_questions = get_quiz_data_with_timeout()
    active_question_id = get_active_question_live("detectivul_din_canapea")

    # Verifică dacă întrebarea activă există în lista de întrebări
    active_found = False
    question_ids = []

    for q in all_questions:
        q_id = q.get("id", "MISSING_ID")
        question_ids.append(q_id)
        if q_id == active_question_id:
            active_found = True

    # Returnează toate informațiile pentru debugging
    debug_info = {
        "active_question_id": active_question_id,
        "active_found_in_questions": active_found,
        "question_ids": question_ids,
        "questions_count": len(all_questions),
        "active_questions_file_exists": os.path.exists(ACTIVE_QUESTION_FILE),
        "active_questions_in_memory": _active_questions
    }

    # Adaugă conținutul fișierului active_questions.json dacă există
    if os.path.exists(ACTIVE_QUESTION_FILE):
        try:
            with open(ACTIVE_QUESTION_FILE, 'r') as f:
                debug_info["active_questions_file_content"] = json.load(f)
        except Exception as e:
            debug_info["active_questions_file_error"] = str(e)

    return jsonify(debug_info)

@quiz_bp.route('/current', methods=['GET'])
def get_current_quiz():
    start_time = time.time()

    # Obține quiz-urile cu timeout și caching
    all_questions = get_quiz_data_with_timeout()

    # Verifică dacă există o întrebare activă
    active_question_id = get_active_question_live("detectivul_din_canapea")
    print(f"🔍 Întrebare activă: {active_question_id}")

    # Reordonează întrebările pentru a pune întrebarea activă prima
    if active_question_id:
        all_questions = reorder_questions_with_active_first(all_questions, active_question_id)

    # Calculează timpul de procesare
    processing_time = time.time() - start_time
    print(f"⏱️ Timp procesare quiz: {processing_time:.2f} secunde")

    # Returnează lista completă de întrebări, cu cea activă prima
    return jsonify(all_questions)

@quiz_bp.route("/current_question/<show_id>")
def get_current_question(show_id):
    # Citim întrebarea activă
    active_question_id = get_active_question_live(show_id)

    # Încărcăm toate întrebările
    questions = get_quiz_data_with_timeout()

    # Căutăm întrebarea activă în listă
    active_question = next((q for q in questions if q["id"] == active_question_id), None)

    if not active_question:
        return jsonify({"error": "Întrebare activă nu a fost găsită"}), 404

    return jsonify({
        "show_id": show_id,
        "show_title": get_show_title(show_id),
        "question": active_question["question"],
        "options": active_question["options"],
        "correct": active_question["correct"],
        "id": active_question["id"]
    })
