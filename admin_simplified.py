from flask import Blueprint, render_template, request, redirect, url_for

admin_bp = Blueprint("admin", __name__, template_folder="admin_panel/templates")

# Date statice - fără Firebase
SHOWS = ["detectivul_din_canapea", "master_chef", "vocea_romaniei"]
QUESTIONS = {
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

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_panel():
    selected_show = request.form.get("show_id") if request.method == "POST" else None
    question_id = request.form.get("question_id")
    
    if selected_show and question_id:
        # Simulează activarea întrebării
        print(f"Activare întrebare: {question_id} pentru show: {selected_show}")
        return redirect(url_for("admin.admin_panel"))
    
    # Obține întrebări pentru show-ul selectat
    questions = QUESTIONS.get(selected_show, []) if selected_show else []
    
    return render_template(
        "admin_static.html", 
        shows=SHOWS, 
        questions=questions, 
        selected_show=selected_show
    )
