from flask import Flask
from flask_cors import CORS
from routes.ocr import ocr_bp
from routes.message_engine import message_bp
from routes.profiles import profiles_bp
from routes.feedback import feedback_bp
from routes.conversations import conversations_bp
from routes.user_sketch import user_sketch_bp
from routes.onboarding import onboarding_bp

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object("config.Config")
    app.register_blueprint(onboarding_bp, url_prefix="/onboarding")
    app.register_blueprint(user_sketch_bp, url_prefix="/user_sketch")
    app.register_blueprint(ocr_bp, url_prefix="/ocr")
    app.register_blueprint(message_bp, url_prefix="/generate")
    app.register_blueprint(profiles_bp, url_prefix="/profile")
    app.register_blueprint(feedback_bp, url_prefix="/message")
    app.register_blueprint(conversations_bp, url_prefix="/conversations")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
