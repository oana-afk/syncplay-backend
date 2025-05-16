from flask import Flask
from routes.ai_routes import ai_bp
from routes.quiz_routes import quiz_bp
from routes.scene_routes import scene_bp
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app) 

    # Register blueprint routes modular
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
    app.register_blueprint(scene_bp, url_prefix='/api/scene')

    @app.route('/')
    def index():
        return {'status': 'SyncPlay backend running 🎬'}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
