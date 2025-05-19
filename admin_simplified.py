from flask import Blueprint, render_template, request, redirect, url_for
from firebase_utils import get_shows, get_questions_for_show, set_active_question, init_firebase
import threading
import time
import os
import json

admin_bp = Blueprint("admin", __name__, template_folder="admin_panel/templates")

# Date statice pentru fallback
FALLBACK_SHOWS = ["detectivul_din_canapea", "master_chef", "vocea_romaniei"]
FALLBACK_QUESTIONS = {
    "detectivul_din_canapea": [
        {"id": "q1", "text": "Cine a furat mingea?", "correct": "Pisica"},
        {"id": "q2", "text": "Cine este detectivul?", "correct": "Tu"},
    ],
    "master_chef": [
        {"id": "q1", "text": "Câte ouă folosim la omletă?", "correct": "2"},
        {"id": "q2", "text": "Care este ingredientul secret?", "correct": "Dragostea"},
    ],
    "vocea_romaniei": [
        {"id": "q1", "text": "Cine a câștigat sezonul trecut?", "correct": "Concurentul X"},
        {"id": "q2", "text": "Câți jurați sunt?", "correct": "4"},
    ]
}

# Fișier local pentru a stoca întrebarea activă când Firebase eșuează
ACTIVE_QUESTION_FILE = "active_questions.json"

# Variabilă în memorie pentru întrebările active
_active_questions_memory = {}

# Rezultate cache pentru a evita apeluri Firebase repetate
_shows_cache = None
_questions_cache = {}
_last_cache_update = 0
CACHE_TIMEOUT = 300  # 5 minute

# Inițializează fișierul active_questions.json la pornire
def initialize_active_questions_file():
    """Creează fișierul active_questions.json dacă nu există"""
    if not os.path.exists(ACTIVE_QUESTION_FILE):
        try:
            with open(ACTIVE_QUESTION_FILE, 'w') as f:
                json.dump(_active_questions_memory, f)
            print(f"✅ Fișierul {ACTIVE_QUESTION_FILE} creat cu succes")
        except Exception as e:
            print(f"❌ Eroare la crearea fișierului {ACTIVE_QUESTION_FILE}: {e}")

# Inițializează fișierul la import
initialize_active_questions_file()

def get_shows_with_timeout(timeout=2):
    """Obține lista de show-uri cu timeout strict"""
    global _shows_cache, _last_cache_update
    
    # Folosește cache dacă este disponibil și încă valid
    current_time = time.time()
    if _shows_cache is not None and (current_time - _last_cache_update) < CACHE_TIMEOUT:
        print("💾 Folosind show-uri din cache")
        return _shows_cache, None, False
    
    result = []
    firebase_error = None
    firebase_timeout = False
    
    def fetch_data():
        nonlocal result
        try:
            db = init_firebase()
            if db:
                result = get_shows()
            else:
                firebase_error = "Nu s-a putut inițializa Firebase"
        except Exception as e:
            firebase_error = str(e)
    
    # Pornește operația într-un thread separat
    thread = threading.Thread(target=fetch_data)
    thread.daemon = True
    thread.start()
    
    # Așteaptă thread-ul să termine sau timeout
    thread.join(timeout)
    
    if thread.is_alive():
        # Timeout - thread-ul încă rulează după timeout
        print(f"⚠️ Timeout la obținerea show-urilor după {timeout} secunde")
        firebase_timeout = True
        return [], "Timeout la obținerea datelor din Firebase", True
    
    if not result and not firebase_error:
        firebase_error = "Nu s-au găsit show-uri în Firebase"
    
    if result:
        # Actualizează cache-ul
        _shows_cache = result
        _last_cache_update = current_time
        
    return result, firebase_error, firebase_timeout

def get_questions_with_timeout(show_id, timeout=2):
    """Obține întrebările pentru un show cu timeout strict"""
    global _questions_cache, _last_cache_update
    
    # Folosește cache dacă este disponibil și încă valid
    current_time = time.time()
    if show_id in _questions_cache and (current_time - _last_cache_update) < CACHE_TIMEOUT:
        print(f"💾 Folosind întrebări din cache pentru {show_id}")
        return _questions_cache[show_id], None, False
    
    result = []
    firebase_error = None
    firebase_timeout = False
    
    def fetch_data():
        nonlocal result
        try:
            result = get_questions_for_show(show_id)
        except Exception as e:
            firebase_error = str(e)
    
    # Pornește operația într-un thread separat
    thread = threading.Thread(target=fetch_data)
    thread.daemon = True
    thread.start()
    
    # Așteaptă thread-ul să termine sau timeout
    thread.join(timeout)
    
    if thread.is_alive():
        # Timeout - thread-ul încă rulează după timeout
        print(f"⚠️ Timeout la obținerea întrebărilor după {timeout} secunde")
        firebase_timeout = True
        return [], "Timeout la obținerea întrebărilor din Firebase", True
    
    if result:
        # Actualizează cache-ul
        _questions_cache[show_id] = result
        _last_cache_update = current_time
        
    return result, firebase_error, firebase_timeout

def set_active_question_safe(show_id, question_id, timeout=3):
    """Versiune mai sigură a funcției set_active_question cu timeout și fallback local"""
    activation_success = [False]  # Folosim o listă pentru a putea modifica din thread
    activation_error = [None]
    
    def activate_question():
        try:
            # Încearcă să activeze întrebarea în Firebase
            result = set_active_question(show_id, question_id)
            activation_success[0] = result
        except Exception as e:
            activation_error[0] = str(e)
            print(f"🔥 Eroare la set_active_question: {e}")
    
    # Pornește un thread pentru operația de activare
    thread = threading.Thread(target=activate_question)
    thread.daemon = True
    thread.start()
    
    # Așteaptă maxim 'timeout' secunde
    thread.join(timeout)
    
    if thread.is_alive():
        # Thread-ul încă rulează, scriem în fișierul local și memoria locală
        save_active_question_local(show_id, question_id)
        return False, f"Timeout la activarea întrebării după {timeout} secunde. Salvată local."
    
    if not activation_success[0] or activation_error[0]:
        # Firebase a eșuat, salvăm întrebarea local
        save_active_question_local(show_id, question_id)
        error_msg = activation_error[0] or "Eroare necunoscută"
        return False, f"Eroare Firebase: {error_msg}. Întrebare salvată local."
    
    # Firebase a reușit, sincronizăm și stocarea locală
    save_active_question_local(show_id, question_id)
    return True, None

def save_active_question_local(show_id, question_id):
    """Salvează întrebarea activă în memoria locală și fișier"""
    global _active_questions_memory
    
    # Actualizează memoria
    _active_questions_memory[show_id] = question_id
    
    # Salvează în fișier pentru persistență între request-uri (dar nu între reporniri)
    try:
        # Inițializează fișierul dacă nu există
        initialize_active_questions_file()
        
        # Încearcă să citească conținutul existent
        try:
            with open(ACTIVE_QUESTION_FILE, 'r') as f:
                active_questions = json.load(f)
        except Exception:
            active_questions = {}
        
        # Actualizează și salvează
        active_questions[show_id] = question_id
        with open(ACTIVE_QUESTION_FILE, 'w') as f:
            json.dump(active_questions, f)
            
        print(f"✅ Întrebare salvată local: {question_id} pentru show: {show_id}")
        return True
    except Exception as e:
        print(f"❌ Eroare la salvarea locală: {e}")
        return False

def get_active_question_local(show_id):
    """Obține întrebarea activă din memoria locală sau fișier"""
    global _active_questions_memory
    
    # Încearcă întâi din memorie
    if show_id in _active_questions_memory:
        return _active_questions_memory[show_id]
    
    # Apoi încearcă din fișier dacă există
    if os.path.exists(ACTIVE_QUESTION_FILE):
        try:
            with open(ACTIVE_QUESTION_FILE, 'r') as f:
                active_questions = json.load(f)
                # Actualizează memoria cu valorile din fișier
                _active_questions_memory.update(active_questions)
                return active_questions.get(show_id)
        except Exception as e:
            print(f"❌ Eroare la citirea din fișierul local: {e}")
    
    # Returnează q1 pentru a forța afișarea întrebării 1
    return "q1"

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_panel():
    start_time = time.time()
    firebase_error = None
    firebase_timeout = False
    
    db = init_firebase()
    if not db:
        firebase_error = "Nu s-a putut stabili conexiunea cu Firebase"
    
    selected_show = request.form.get("show_id") if request.method == "POST" else request.args.get("show_id")
    question_id = request.form.get("question_id")
        print(f"🎯 Admin a trimis: show_id={selected_show}, question_id={question_id}")

    
    # Procesează activarea întrebării dacă este cazul
    if selected_show and question_id and request.method == "POST":
        success, error_message = set_active_question_safe(selected_show, question_id)
        
        if success:
            print(f"✅ Întrebare activată: {question_id} pentru show: {selected_show}")
        else:
            firebase_error = error_message
            
        return redirect(url_for("admin.admin_panel", show_id=selected_show))
    
    # Obține show-uri din Firebase cu timeout
    shows, shows_error, shows_timeout = get_shows_with_timeout()
    if shows_error:
        firebase_error = shows_error
    if shows_timeout:
        firebase_timeout = True
    
    # Dacă nu am obținut show-uri, folosim datele statice
    if not shows:
        print("⚠️ Folosind lista de show-uri statice")
        shows = FALLBACK_SHOWS
    
    # Obține întrebări pentru show-ul selectat
    questions = []
    if selected_show:
        if firebase_timeout:
            # Dacă am avut timeout la show-uri, folosim direct datele statice
            questions = FALLBACK_QUESTIONS.get(selected_show, [])
            print(f"⚠️ Folosind întrebări statice pentru {selected_show}")
        else:
            # Altfel încercăm să obținem întrebările din Firebase
            questions, questions_error, questions_timeout = get_questions_with_timeout(selected_show)
            
            if questions_error:
                firebase_error = questions_error
            if questions_timeout:
                firebase_timeout = True
                
            # Dacă nu am obținut întrebări, folosim datele statice
            if not questions:
                print(f"⚠️ Folosind întrebări statice pentru {selected_show}")
                questions = FALLBACK_QUESTIONS.get(selected_show, [])
    
    # Obține întrebarea activă pentru show-ul selectat (din memorie sau local)
    active_question_id = None
    if selected_show:
        active_question_id = get_active_question_local(selected_show)
    
    # Calculează timpul total de procesare
    processing_time = time.time() - start_time
    print(f"⏱️ Timp total procesare admin: {processing_time:.2f} secunde")
    
    return render_template(
        "admin.html",
        shows=shows,
        questions=questions,
        selected_show=selected_show,
        firebase_error=firebase_error,
        firebase_timeout=firebase_timeout,
        active_question_id=active_question_id,
        processing_time=f"{processing_time:.2f}"
    )
