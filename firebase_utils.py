import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
import time

firebase_app = None
db = None

def init_firebase():
    global firebase_app, db
    if not firebase_app:
        try:
            print("🔄 Inițializare Firebase...")
            start_time = time.time()
            
            service_account_info = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_SYNCPLAY"))
            cred = credentials.Certificate(service_account_info)
            
            # Opțiuni de inițializare pentru a reduce memoria utilizată
            firebase_app = firebase_admin.initialize_app(cred, {
                'projectId': service_account_info.get('project_id'),
            })
            
            db = firestore.client()
            
            # Măsoară timpul de inițializare
            print(f"✅ Firebase inițializat în {time.time() - start_time:.2f} secunde")
            return db
        except Exception as e:
            print(f"🔥 Eroare la inițializarea Firebase: {str(e)}")
            return None
    return db

def get_shows(max_timeout=5):
    """Obține lista de show-uri cu timeout limitat"""
    try:
        start_time = time.time()
        print("🔄 Obținere shows...")
        
        db = init_firebase()
        if not db:
            return []
            
        # Setează un timeout pentru operațiune
        shows_ref = db.collection('shows')
        docs = list(shows_ref.stream())
        
        # Verifică dacă a durat prea mult
        elapsed = time.time() - start_time
        print(f"✅ Shows obținute în {elapsed:.2f} secunde")
        
        if elapsed > max_timeout:
            print(f"⚠️ Obținerea shows a durat prea mult: {elapsed:.2f} secunde")
            
        return [doc.id for doc in docs]
    except Exception as e:
        print(f"🔥 Eroare la get_shows: {e}")
        return []

def get_questions_for_show(show_id, max_timeout=5):
    """Obține întrebările pentru un show cu timeout limitat"""
    try:
        start_time = time.time()
        print(f"🔄 Obținere întrebări pentru {show_id}...")
        
        db = init_firebase()
        if not db:
            return []
            
        # Setează un timeout pentru operațiune
        questions_ref = db.collection('shows').document(show_id).collection('questions')
        docs = list(questions_ref.stream())
        
        # Verifică dacă a durat prea mult
        elapsed = time.time() - start_time
        print(f"✅ Întrebări obținute în {elapsed:.2f} secunde")
        
        if elapsed > max_timeout:
            print(f"⚠️ Obținerea întrebărilor a durat prea mult: {elapsed:.2f} secunde")
            
        return [{**q.to_dict(), 'id': q.id} for q in docs]
    except Exception as e:
        print(f"🔥 Eroare la get_questions: {e}")
        return []

def set_active_question(show_id, question_id):
    try:
        db = init_firebase()
        if not db:
            return False
            
        metadata_ref = db.collection('shows').document(show_id).collection('metadata').document('status')
        metadata_ref.set({'current_question_id': question_id})

        # 🔁 Salvăm și local în active_questions.json
        try:
            with open("active_questions.json", "w", encoding="utf-8") as f:
                json.dump({show_id: question_id}, f, ensure_ascii=False, indent=2)
            print(f"✅ Întrebarea activă a fost salvată și local în active_questions.json")
        except Exception as e:
            print(f"⚠️ Eroare la salvarea locală a întrebării active: {e}")

        return True
    except Exception as e:
        print(f"🔥 Eroare la set_active_question: {e}")
        return False
