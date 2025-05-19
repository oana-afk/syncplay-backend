from flask import Blueprint, render_template, request, redirect, url_for
from firebase_utils import get_shows, get_questions_for_show, set_active_question, init_firebase

admin_bp = Blueprint("admin", __name__, template_folder="admin_panel/templates")

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_panel():
    firebase_error = None
    db = init_firebase()
    
    if not db:
        firebase_error = "Nu s-a putut stabili conexiunea cu Firebase"
    
    selected_show = request.form.get("show_id") if request.method == "POST" else None
    question_id = request.form.get("question_id")
    
    # Procesează activarea întrebării dacă este cazul
    if selected_show and question_id:
        success = set_active_question(selected_show, question_id)
        if success:
            print(f"✅ Întrebare activată: {question_id} pentru show: {selected_show}")
        else:
            firebase_error = "Nu s-a putut activa întrebarea"
        return redirect(url_for("admin.admin_panel", show_id=selected_show))
    
    # Obține show-uri și întrebări din Firebase
    shows = []
    questions = []
    
    if db:  # Doar dacă Firebase este conectat
        shows = get_shows()
        if selected_show:
            questions = get_questions_for_show(selected_show)
    
    return render_template(
        "admin.html",  # Folosim template-ul admin.html
        shows=shows,
        questions=questions,
        selected_show=selected_show,
        firebase_error=firebase_error
    )
