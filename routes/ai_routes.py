from flask import Blueprint, request, jsonify
from services.gemini_service import ask_gemini

ai_bp = Blueprint('ai_bp', __name__)

@ai_bp.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_question = data.get('question', '')

    if not user_question:
        return jsonify({'error': 'Missing question'}), 400

    try:
        answer = ask_gemini(user_question)
        return jsonify({'response': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

