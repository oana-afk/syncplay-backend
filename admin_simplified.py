from flask import Blueprint, render_template, request, redirect, url_for
from firebase_utils import get_shows, get_questions_for_show, set_active_question, init_firebase
import threading
import time

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

def get_shows_with_timeout(timeout=5):
    """Obține lista de show-uri cu timeout strict"""
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
        
    return result, firebase_error, firebase_timeout

def get_questions_with_timeout(show_id, timeout=5):
    """Obține întrebările pentru un show cu timeout strict"""
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
        
    return result, firebase_error, firebase_timeout

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_panel():
    start_time = time.time()
    firebase_error = None
    firebase_timeout = False
    db = init_firebase()
    
    if not db:
        firebase_error = "Nu s-a putut stabili conexiunea cu Firebase"
    
    selected_show = request.form.get("show_id") if request.method == "POST" else None
    question_id = request.form.get("question_id")
    
    # Procesează activarea întrebării dacă este cazul
    if selected_show and question_id:
        try:
            success = set_active_question(selected_show, question_id)
            if success:
                print(f"✅ Întrebare activată: {question_id} pentru show: {selected_show}")
            else:
                firebase_error = "Nu s-a putut activa întrebarea"
        except Exception as e:
            firebase_error = f"Eroare la activarea întrebării: {str(e)}"
        
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
        processing_time=f"{processing_time:.2f}"
    )
