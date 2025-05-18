import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Înlocuiește cu cheia ta dacă vrei să o încarci din fișier local:
# with open("firebase_key.json") as f:
#     service_account = json.load(f)

# Sau încarcă din variabilă de mediu, dacă e setată local:
service_account = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_SYNCPLAY"))

cred = credentials.Certificate(service_account)
firebase_admin.initialize_app(cred)
db = firestore.client()

question_data = {
    "text": "Cine a furat mingea?",
    "options": ["Câinele", "Pisica", "Vecinul", "Poștașul"],
    "correct": "Pisica"
}

db.collection("shows") \
  .document("detectivul_din_canapea") \
  .collection("questions") \
  .document("q1") \
  .set(question_data)

print("✅ Întrebare adăugată în Firestore.")
