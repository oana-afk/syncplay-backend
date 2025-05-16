from flask import Blueprint, jsonify
import json
import os

scene_bp = Blueprint('scene_bp', __name__)

@scene_bp.route('/exclusive', methods=['GET'])
def get_exclusive_scene():
    try:
        path = os.path.join('data', 'scenes.json')
        with open(path, 'r', encoding='utf-8') as f:
            scenes = json.load(f)
        return jsonify(scenes[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
