import json
import os

def load_quiz_data():
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'quiz.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {'error': f'Could not load quiz data: {str(e)}'}

