from flask import Blueprint, jsonify
import os
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore

firebase_diagnostic_bp = Blueprint("firebase_diagnostic", __name__)

@firebase_diagnostic_bp.route("/diagnostic/firebase", methods=["GET"])
def diagnose_firebase():
    result = {
        "status": "running",
        "timestamp": time.time(),
        "steps": {}
    }
    
    # Pas 1: Verifică existența variabilei de mediu
    try:
        firebase_creds = os.getenv("FIREBASE_SERVICE_ACCOUNT_SYNCPLAY")
        result["steps"]["env_var"] = {
            "status": "success" if firebase_creds else "error",
            "message": "Variabila de mediu FIREBASE_SERVICE_ACCOUNT_SYNCPLAY există" if firebase_creds else "Lipsește variabila de mediu"
        }
        
        if not firebase_creds:
            result["status"] = "error"
            return jsonify(result)
            
    except Exception as e:
        result["steps"]["env_var"] = {
            "status": "error",
            "message": str(e)
        }
        result["status"] = "error"
        return jsonify(result)
    
    # Pas 2: Verifică parsarea JSON-ului
    try:
        creds_json = json.loads(firebase_creds)
        result["steps"]["json_parse"] = {
            "status": "success",
            "project_id": creds_json.get("project_id", "N/A"),
            "client_email": creds_json.get("client_email", "N/A")
        }
    except Exception as e:
        result["steps"]["json_parse"] = {
            "status": "error",
            "message": str(e)
        }
        result["status"] = "error"
        return jsonify(result)
    
    # Pas 3: Încearcă să inițializeze Firebase
    try:
        start_time = time.time()
        cred = credentials.Certificate(creds_json)
        
        # Verifică dacă Firebase este deja inițializat
        try:
            app = firebase_admin.get_app()
            result["steps"]["firebase_init"] = {
                "status": "success",
                "message": "Firebase deja inițializat",
                "time_ms": 0
            }
        except ValueError:
            # Inițializează Firebase cu timeout
            app = firebase_admin.initialize_app(cred, {
                'projectId': creds_json.get('project_id'),
            })
            init_time = time.time() - start_time
            result["steps"]["firebase_init"] = {
                "status": "success",
                "message": "Firebase inițializat cu succes",
                "time_ms": round(init_time * 1000)
            }
            
    except Exception as e:
        result["steps"]["firebase_init"] = {
            "status": "error",
            "message": str(e)
        }
        result["status"] = "error"
        return jsonify(result)
    
    # Pas 4: Testează accesul la Firestore
    try:
        start_time = time.time()
        db = firestore.client()
        db_time = time.time() - start_time
        result["steps"]["firestore_client"] = {
            "status": "success",
            "time_ms": round(db_time * 1000)
        }
    except Exception as e:
        result["steps"]["firestore_client"] = {
            "status": "error",
            "message": str(e)
        }
        result["status"] = "error"
        return jsonify(result)
    
    # Pas 5: Listează colecțiile
    try:
        start_time = time.time()
        collections = [col.id for col in db.collections()]
        coll_time = time.time() - start_time
        result["steps"]["list_collections"] = {
            "status": "success",
            "collections": collections,
            "time_ms": round(coll_time * 1000)
        }
    except Exception as e:
        result["steps"]["list_collections"] = {
            "status": "error",
            "message": str(e)
        }
        result["status"] = "partial"
        # Continuă cu următorii pași
    
    # Pas 6: Verifică colecția "shows"
    try:
        start_time = time.time()
        shows_ref = db.collection('shows')
        shows = [doc.id for doc in shows_ref.stream()]
        shows_time = time.time() - start_time
        result["steps"]["shows_collection"] = {
            "status": "success",
            "shows": shows,
            "time_ms": round(shows_time * 1000)
        }
        
        if len(shows) == 0:
            result["steps"]["shows_collection"]["message"] = "Nu există show-uri. Trebuie să populezi colecția."
    except Exception as e:
        result["steps"]["shows_collection"] = {
            "status": "error",
            "message": str(e)
        }
        result["status"] = "partial"
        # Continuă cu următorii pași
    
    # Pas 7: Verifică întrebările pentru primul show (dacă există)
    if "shows" in result["steps"].get("shows_collection", {}) and len(result["steps"]["shows_collection"]["shows"]) > 0:
        try:
            show_id = result["steps"]["shows_collection"]["shows"][0]
            start_time = time.time()
            questions_ref = db.collection('shows').document(show_id).collection('questions')
            questions = [{
                "id": q.id, 
                "data": q.to_dict()
            } for q in questions_ref.stream()]
            q_time = time.time() - start_time
            
            result["steps"]["show_questions"] = {
                "status": "success",
                "show_id": show_id,
                "questions": questions,
                "time_ms": round(q_time * 1000)
            }
            
            if len(questions) == 0:
                result["steps"]["show_questions"]["message"] = f"Nu există întrebări pentru show-ul {show_id}. Trebuie să populezi colecția."
                
        except Exception as e:
            result["steps"]["show_questions"] = {
                "status": "error",
                "message": str(e)
            }
            result["status"] = "partial"
    
    # Pas final: Status general
    if result["status"] == "running":
        result["status"] = "success"  # Totul a mers bine
        
    return jsonify(result)
