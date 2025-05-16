from flask import Blueprint, jsonify
from services.data_loader import load_quiz_data

quiz_bp = Blueprint('quiz_bp', __name__)

@quiz_bp.route('/current', methods=['GET'])
def get_current_quiz():
    quiz = load_quiz_data()
    return jsonify(quiz)
