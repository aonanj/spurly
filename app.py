from flask import Flask, current_app
from flask_cors import CORS
from routes.ocr import ocr_bp
from routes.message_engine import message_bp
from routes.connections import connection_bp
from routes.feedback import feedback_bp
from routes.conversations import conversations_bp
from routes.user_management import user_management_bp
from routes.onboarding import onboarding_bp
from routes.context_route import context_bp
from infrastructure.logger import setup_logger
from infrastructure.clients import init_clients


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object("config.Config")
    app.register_blueprint(onboarding_bp, url_prefix="/onboarding")
    app.register_blueprint(ocr_bp, url_prefix="/ocr")
    app.register_blueprint(message_bp, url_prefix="/generate")
    app.register_blueprint(connection_bp, url_prefix="/connection")
    app.register_blueprint(feedback_bp, url_prefix="/spur")
    app.register_blueprint(conversations_bp, url_prefix="/conversations")
    app.register_blueprint(user_management_bp, url_prefix="/user")
    app.register_blueprint(context_bp, url_prefix="/context")
    
    level = app.config.get("LOGGER_LEVEL", "INFO")
    setup_logger(name="spurly", toFile=True, filename="spurly.log", level=level)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
    init_clients(app)
