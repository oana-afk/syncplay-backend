import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

firebase_app = None
db = None

def init_firebase():
    global firebase_app, db
    if not firebase_app:
        service_account_info = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_SYNCPLAY"))
        cred = credentials.Certificate(service_account_info)
        firebase_app = firebase_admin.initialize_app(cred)
        db = firestore.client()
    return db

def get_shows():
    try:
        db = init_firebase()
        shows_ref = db.collection('shows')
        docs = list(shows_ref.stream())
        return [doc.id for doc in docs]
    except Exception as e:
        print(f"🔥 Eroare la get_shows: {e}")
        return []

def get_questions_for_show(show_id):
    try:
        db = init_firebase()
        questions_ref = db.collection('shows').document(show_id).collection('questions')
        docs = list(questions_ref.stream())
        return [{**q.to_dict(), 'id': q.id} for q in docs]
    except Exception as e:
        print(f"🔥 Eroare la get_questions: {e}")
        return []

def set_active_question(show_id, question_id):
    db = init_firebase()
    metadata_ref = db.collection('shows').document(show_id).collection('metadata').document('status')
    metadata_ref.set({'current_question_id': question_id})
