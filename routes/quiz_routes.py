from flask import Blueprint, jsonify
from services.data_loader import load_quiz_data
import threading
import time
import os
import json
import random

quiz_bp = Blueprint('quiz_bp', __name__)

# Fișier local pentru a citi întrebarea activă
ACTIVE_QUESTION_FILE = "active_questions.json"

# Cache pentru quiz-uri
_quiz_data_cache = None
_last_cache_update = 0
CACHE_TIMEOUT = 300  # 5 minute


def get_quiz_data_with_timeout(timeout=2):
    """Obține datele quiz cu timeout și caching"""
    global _quiz_data_cache, _last_cache_update

    # Verifică cache-ul întâi
    current_time = time.time()
    if _quiz_data_cache is not None and (current_time - _last_cache_update) < CACHE_TIMEOUT:
        print("💾 Folosind date quiz din cache")
        return _quiz_data_cache

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

    # Dacă avem eroare dar avem cache vechi, folosește-l
    if _quiz_data_cache is not None:
        print("⚠️ Eroare la obținerea quiz-urilor, folosim cache-ul vechi")
        return _quiz_data_cache

    # Ultimul resort - date statice
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


def get_active_question_local(show_id="detectivul_din_canapea"):
    """Obține întrebarea activă din fișierul local"""
    if not os.path.exists(ACTIVE_QUESTION_FILE):
        return None

    try:
        with open(ACTIVE_QUESTION_FILE, 'r') as f:
            active_questions = json.load(f)
            return active_questions.get(show_id)
    except Exception as e:
        print(f"❌ Eroare la citirea din fișierul local: {e}")
        return None


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

@quiz_bp.route('/current', methods=['GET'])
def get_current_quiz():
    start_time = time.time()

    # Obține quiz-urile cu timeout și caching
    all_questions = get_quiz_data_with_timeout()

    # Verifică dacă există o întrebare activă
    active_question_id = get_active_question_local()
    print(f"🔍 Întrebare activă: {active_question_id}")

    # Reordonează întrebările pentru a pune întrebarea activă prima
    # Acest lucru asigură că API-ul va returna array-ul complet, dar că
    # selectorul aleatoriu din aplicație are șanse mari să selecteze prima
    # întrebare - care va fi cea activă
    if active_question_id:
        all_questions = reorder_questions_with_active_first(all_questions, active_question_id)

    # Calculează timpul de procesare
    processing_time = time.time() - start_time
    print(f"⏱️ Timp procesare quiz: {processing_time:.2f} secunde")

    # Returnează lista completă de întrebări, cu cea activă prima
    return jsonify(all_questions)
