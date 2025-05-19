from flask import Blueprint, jsonify
from services.data_loader import load_quiz_data
import threading
import time

quiz_bp = Blueprint('quiz_bp', __name__)

# Cache pentru quiz-uri
_quiz_data_cache = None
_last_cache_update = 0
CACHE_TIMEOUT = 300  # 5 minute

def get_quiz_data_with_timeout(timeout=2):
    """Obține datele quiz cu timeout și caching"""
    global _quiz_data_cache, _last_cache_update
    
    # Verifică cache-ul întâi
    current_time = time.time()
    if _quiz_data_cache is not None and (current_time - _last_cache_update) < CACHE_TIMEOUT:
        print("💾 Folosind date quiz din cache")
        return _quiz_data_cache
    
    result = None
    timeout_occurred = False
    
    def fetch_data():
        nonlocal result
        try:
            result = load_quiz_data()
        except Exception as e:
            print(f"❌ Eroare la încărcarea quiz-urilor: {e}")
            result = None
    
    # Pornește thread-ul pentru a încărca datele
    thread = threading.Thread(target=fetch_data)
    thread.daemon = True
    thread.start()
    
    # Așteaptă thread-ul cu timeout
    thread.join(timeout)
    
    if thread.is_alive():
        timeout_occurred = True
        print(f"⚠️ Timeout la încărcarea quiz-urilor după {timeout} secunde")
        
        # Returnează cache-ul vechi dacă există
        if _quiz_data_cache is not None:
            print("🔄 Folosind cache-ul vechi pentru quiz-uri")
            return _quiz_data_cache
        
        # Altfel returnează date statice de fallback
        return [
            {
                "question": "Care este capitala Franței?",
                "options": ["Paris", "Berlin", "Madrid", "Roma"],
                "correct": "Paris"
            },
            {
                "question": "Ce simbol are fluorul?",
                "options": ["Fl", "F", "Fr", "Fe"],
                "correct": "F"
            },
            {
                "question": "Câte continente are planeta Pământ?",
                "options": ["5", "6", "7", "8"],
                "correct": "7"
            }
        ]
    
    # Verifică rezultatul și actualizează cache-ul dacă este valid
    if result is not None and not isinstance(result, dict) and "error" not in result:
        _quiz_data_cache = result
        _last_cache_update = current_time
        return result
    
    # Dacă avem eroare dar avem cache vechi, folosește-l
    if _quiz_data_cache is not None:
        print("⚠️ Eroare la obținerea quiz-urilor, folosim cache-ul vechi")
        return _quiz_data_cache
    
    # Ultimul resort - date statice
    return [
        {
            "question": "Care este capitala Franței?",
            "options": ["Paris", "Berlin", "Madrid", "Roma"],
            "correct": "Paris"
        },
        {
            "question": "Ce simbol are fluorul?",
            "options": ["Fl", "F", "Fr", "Fe"],
            "correct": "F"
        },
        {
            "question": "Câte continente are planeta Pământ?",
            "options": ["5", "6", "7", "8"],
            "correct": "7"
        }
    ]

@quiz_bp.route('/current', methods=['GET'])
def get_current_quiz():
    start_time = time.time()
    
    # Obține quiz-urile cu timeout și caching
    quiz_data = get_quiz_data_with_timeout()
    
    # Calculează timpul de procesare
    processing_time = time.time() - start_time
    print(f"⏱️ Timp procesare quiz: {processing_time:.2f} secunde")
    
    return jsonify(quiz_data)
