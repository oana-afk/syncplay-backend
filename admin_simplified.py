from flask import Blueprint, render_template, request, redirect, url_for
import os
import json
import time

admin_bp = Blueprint("admin", __name__, template_folder="admin_panel/templates")

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_panel():
    # Simulează datele pentru interfață
    shows = ["detectivul_din_canapea", "master_chef", "vocea_romaniei"]
    questions = [
        {"id": "q1", "text": "Cine a furat mingea?"},
        {"id": "q2", "text": "Care este capitala Franței?"},
        {"id": "q3", "text": "Câte continente are planeta Pământ?"}
    ]
    
    selected_show = request.form.get("show_id") if request.method == "POST" else None
    question_id = request.form.get("question_id")
    
    if selected_show and question_id:
        # Simulăm activarea întrebării - de fapt, doar afișăm un mesaj
        print(f"Activare întrebare: {question_id} pentru show: {selected_show}")
        return redirect(url_for("admin.admin_panel"))
    
    return render_template(
        "admin_simple.html", 
        shows=shows, 
        questions=questions, 
        selected_show=selected_show
    )
