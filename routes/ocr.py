from flask import Blueprint, request, jsonify
from services.ocr_service import process_image
from infrastructure.auth import require_auth
from infrastructure.logger import get_logger
from class_defs.conversation_def import Conversation

ocr_bp = Blueprint("ocr", __name__)
logger = get_logger(__name__)

@ocr_bp.route("/upload", methods=["POST"])
@require_auth
def upload_image():
    image = request.files.get("image")
    if not image:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({"error": f"[{err_point}] - Error"}), 400
    try:
        conversation = process_image(image)
        
        if not isinstance(conversation, dict) or "conversation" not in conversation:
            err_point = __package__ or __name__
            logger.error(f"[{err_point}] - Invalid conversation object returned")
            return jsonify({"error": f"[{err_point}] - Invalid OCR response"}), 500

        convo_obj = Conversation.from_dict(conversation["conversation"])

        # Fill in missing fields with validation
        convo_obj.user_id = request.headers.get("X-User-ID", "").strip()
        convo_obj.connection_id = request.form.get("connection_id", "").strip()
        convo_obj.situation = request.form.get("situation", "").strip()
        convo_obj.topic = request.form.get("topic", "").strip()

        if not convo_obj.user_id or not convo_obj.connection_id:
            err_point = __package__ or __name__
            logger.error(f"[{err_point}] - Missing required fields")
            return jsonify({"error": f"[{err_point}] - Missing user_id or connection_id"}), 400

        # Spurs should remain empty unless explicitly supplied or inferred later
        convo_obj.spurs = {}

        return jsonify({"conversation": convo_obj.to_dict()}), 200
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return (f"[{err_point}] - Error: {str(e)}"), 500
