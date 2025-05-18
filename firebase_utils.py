import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Inițializare Firestore o singură dată
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
    db = init_firebase()
    shows_ref = db.collection('shows')
    return [doc.id for doc in shows_ref.stream()]

def get_questions_for_show(show_id):
    db = init_firebase()
    questions_ref = db.collection('shows').document(show_id).collection('questions')
    return [{**q.to_dict(), 'id': q.id} for q in questions_ref.stream()]

def set_active_question(show_id, question_id):
    db = init_firebase()
    metadata_ref = db.collection('shows').document(show_id).collection('metadata').document('status')
    metadata_ref.set({'current_question_id': question_id})
