from flask import Flask
from routes.ai_routes import ai_bp
from routes.quiz_routes import quiz_bp
from routes.scene_routes import scene_bp
from flask_cors import CORS
from admin import admin_bp  # dacă admin.py e în root

def create_app(environ=None, start_response=None):
    app = Flask(__name__)
    CORS(app)

    from routes.ai_routes import ai_bp
    from routes.quiz_routes import quiz_bp
    from routes.scene_routes import scene_bp
    from admin import admin_bp

    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
    app.register_blueprint(scene_bp, url_prefix='/api/scene')
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        return {'status': 'SyncPlay backend running 🎬'}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
