import os
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

service_account = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_SYNCPLAY"))
cred = credentials.Certificate(service_account)
firebase_admin.initialize_app(cred)
db = firestore.client()

question = {
    "text": "Cine a furat mingea?",
    "options": ["Câinele", "Pisica", "Vecinul", "Poștașul"],
    "correct": "Pisica"
}

db.collection("shows") \
  .document("detectivul_din_canapea") \
  .collection("questions") \
  .document("q1") \
  .set(question)

print("✅ Întrebare adăugată.")
