from flask import Blueprint, jsonify
import json
import os
import threading
import time

scene_bp = Blueprint('scene_bp', __name__)

# Cache pentru scene
_scene_data_cache = None
_last_cache_update = 0
CACHE_TIMEOUT = 300  # 5 minute

def get_scene_data_with_timeout(timeout=2):
    """Obține datele de scenă cu timeout și caching"""
    global _scene_data_cache, _last_cache_update
    
    # Verifică cache-ul întâi
    current_time = time.time()
    if _scene_data_cache is not None and (current_time - _last_cache_update) < CACHE_TIMEOUT:
        print("💾 Folosind date scenă din cache")
        return _scene_data_cache
    
    result = None
    timeout_occurred = False
    
    def fetch_data():
        nonlocal result
        try:
            path = os.path.join('data', 'scenes.json')
            with open(path, 'r', encoding='utf-8') as f:
                scenes = json.load(f)
            result = scenes[0] if scenes else None
        except Exception as e:
            print(f"❌ Eroare la încărcarea scenelor: {e}")
            result = None
    
    # Pornește thread-ul pentru a încărca datele
    thread = threading.Thread(target=fetch_data)
    thread.daemon = True
    thread.start()
    
    # Așteaptă thread-ul cu timeout
    thread.join(timeout)
    
    if thread.is_alive():
        timeout_occurred = True
        print(f"⚠️ Timeout la încărcarea scenelor după {timeout} secunde")
        
        # Returnează cache-ul vechi dacă există
        if _scene_data_cache is not None:
            print("🔄 Folosind cache-ul vechi pentru scene")
            return _scene_data_cache
        
        # Altfel returnează date statice de fallback
        return {
            "title": "Backstage Exclusive",
            "description": "Acces VIP la o scenă never publicată. Doar pentru tine.",
            "video_url": "https://example.com/exclusive-scene.mp4"
        }
    
    # Verifică rezultatul și actualizează cache-ul dacă este valid
    if result is not None:
        _scene_data_cache = result
        _last_cache_update = current_time
        return result
    
    # Dacă avem eroare dar avem cache vechi, folosește-l
    if _scene_data_cache is not None:
        print("⚠️ Eroare la obținerea scenelor, folosim cache-ul vechi")
        return _scene_data_cache
    
    # Ultimul resort - date statice
    return {
        "title": "Backstage Exclusive",
        "description": "Acces VIP la o scenă never publicată. Doar pentru tine.",
        "video_url": "https://example.com/exclusive-scene.mp4"
    }

@scene_bp.route('/exclusive', methods=['GET'])
def get_exclusive_scene():
    start_time = time.time()
    
    # Obține scenele cu timeout și caching
    scene_data = get_scene_data_with_timeout()
    
    # Calculează timpul de procesare
    processing_time = time.time() - start_time
    print(f"⏱️ Timp procesare scenă: {processing_time:.2f} secunde")
    
    return jsonify(scene_data)
