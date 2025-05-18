from flask import Blueprint, render_template, request, redirect, url_for
from firebase_utils import get_shows, get_questions_for_show, set_active_question

admin_bp = Blueprint("admin", __name__, template_folder="admin_panel/templates")

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_panel():
    selected_show = request.form.get("show_id") if request.method == "POST" else None
    question_id = request.form.get("question_id")

    if selected_show and question_id:
        set_active_question(selected_show, question_id)
        return redirect(url_for("admin.admin_panel"))

    shows = get_shows()
    questions = get_questions_for_show(selected_show) if selected_show else []

    return render_template("admin.html", shows=shows, questions=questions, selected_show=selected_show)
