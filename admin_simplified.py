from flask import Blueprint, render_template, request, redirect, url_for
import os
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore

admin_bp = Blueprint("admin", __name__, template_folder="admin_panel/templates")

# Funcții Firebase optimizate
firebase_app = None
db = None

def init_firebase():
    global firebase_app, db
    if not firebase_app:
        try:
            firebase_creds = os.getenv("FIREBASE_SERVICE_ACCOUNT_SYNCPLAY")
            if not firebase_creds:
                print("⚠️ Lipsesc credențialele Firebase!")
                return None
                
            service_account_info = json.loads(firebase_creds)
            
            # Verifică dacă aplicația este deja inițializată
            try:
                firebase_app = firebase_admin.get_app()
            except ValueError:
                cred = credentials.Certificate(service_account_info)
                firebase_app = firebase_admin.initialize_app(cred)
                
            db = firestore.client()
            return db
        except Exception as e:
            print(f"🔥 Eroare la inițializarea Firebase: {e}")
            return None
    return db

def get_shows(timeout=5):
    try:
        start_time = time.time()
        db = init_firebase()
        if not db:
            # Returnează date simulate dacă Firebase nu este disponibil
            return ["detectivul_din_canapea", "master_chef", "vocea_romaniei"]
            
        shows_ref = db.collection('shows')
        shows = []
        
        # Implementare cu timeout manual
        for doc in shows_ref.stream():
            shows.append(doc.id)
            if time.time() - start_time > timeout:
                print(f"⚠️ Timeout la obținerea show-urilor după {len(shows)} rezultate")
                break
                
        return shows if shows else ["detectivul_din_canapea", "master_chef", "vocea_romaniei"]
    except Exception as e:
        print(f"🔥 Eroare la get_shows: {e}")
        return ["detectivul_din_canapea", "master_chef", "vocea_romaniei"]

def get_questions_for_show(show_id, timeout=5):
    try:
        start_time = time.time()
        db = init_firebase()
        if not db:
            # Returnează date simulate dacă Firebase nu este disponibil
            return [
                {"id": "q1", "text": "Cine a furat mingea?", "correct": "Pisica"},
                {"id": "q2", "text": "Care este capitala Franței?", "correct": "Paris"},
                {"id": "q3", "text": "Câte continente are planeta Pământ?", "correct": "7"}
            ]
            
        questions_ref = db.collection('shows').document(show_id).collection('questions')
        questions = []
        
        # Implementare cu timeout manual
        for q in questions_ref.stream():
            data = q.to_dict()
            questions.append({
                'id': q.id, 
                'text': data.get('text', ''), 
                'options': data.get('options', []), 
                'correct': data.get('correct', '')
            })
            
            if time.time() - start_time > timeout:
                print(f"⚠️ Timeout la obținerea întrebărilor după {len(questions)} rezultate")
                break
                
        # Dacă nu găsim nimic în Firebase, returnăm date simulate
        if not questions:
            return [
                {"id": "q1", "text": "Cine a furat mingea?", "correct": "Pisica"},
                {"id": "q2", "text": "Care este capitala Franței?", "correct": "Paris"},
                {"id": "q3", "text": "Câte continente are planeta Pământ?", "correct": "7"}
            ]
        return questions
    except Exception as e:
        print(f"🔥 Eroare la get_questions: {e}")
        return [
            {"id": "q1", "text": "Cine a furat mingea?", "correct": "Pisica"},
            {"id": "q2", "text": "Care este capitala Franței?", "correct": "Paris"},
            {"id": "q3", "text": "Câte continente are planeta Pământ?", "correct": "7"}
        ]

def set_active_question(show_id, question_id):
    try:
        db = init_firebase()
        if not db:
            # Simulăm activarea
            print(f"Simulare activare întrebare: {question_id} pentru show: {show_id}")
            return True
            
        metadata_ref = db.collection('shows').document(show_id).collection('metadata').document('status')
        metadata_ref.set({'current_question_id': question_id})
        return True
    except Exception as e:
        print(f"🔥 Eroare la set_active_question: {e}")
        return False

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_panel():
    firebase_error = None
    selected_show = request.form.get("show_id") if request.method == "POST" else request.args.get("show_id")
    question_id = request.form.get("question_id")
    
    # Procesează activarea întrebării dacă este cazul
    if selected_show and question_id:
        success = set_active_question(selected_show, question_id)
        if not success:
            firebase_error = "Nu s-a putut seta întrebarea activă"
        return redirect(url_for("admin.admin_panel", show_id=selected_show))

    # Obține show-uri
    shows = get_shows()
    
    # Obține întrebări pentru show-ul selectat
    questions = []
    if selected_show:
        questions = get_questions_for_show(selected_show)
    
    return render_template(
        "admin_simple.html", 
        shows=shows, 
        questions=questions, 
        selected_show=selected_show,
        firebase_error=firebase_error
    )
