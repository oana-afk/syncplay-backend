from flask import Blueprint, render_template, request, redirect, url_for
import os
import json

admin_bp = Blueprint("admin", __name__, template_folder="admin_panel/templates")

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_panel():
    # Verifică dacă Firebase este configurat
    firebase_status = "NECONFIGURAT"
    firebase_error = None
    
    try:
        # Verifică doar existența variabilei de mediu
        firebase_creds = os.getenv("FIREBASE_SERVICE_ACCOUNT_SYNCPLAY")
        if firebase_creds:
            # Încearcă să parseze JSON-ul
            json.loads(firebase_creds)
            firebase_status = "CONFIGURAT"
        else:
            firebase_error = "Lipsesc credențialele Firebase"
    except json.JSONDecodeError:
        firebase_error = "Eroare la parsarea credențialelor Firebase (JSON invalid)"
    except Exception as e:
        firebase_error = f"Eroare: {str(e)}"
    
    return render_template(
        "admin_debug.html", 
        firebase_status=firebase_status,
        firebase_error=firebase_error
    )
