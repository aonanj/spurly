from flask import Blueprint, request, jsonify, current_app
from services.ocr_service import process_image
from infrastructure.auth import require_auth
from infrastructure.logger import get_logger
from class_defs.conversation_def import Conversation
from uuid import uuid4
from datetime import datetime

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


    
    user_id = request.headers.get("X-User-ID", "").strip()
    connection_id = request.headers.get("connection_id", None)
    situation = request.form.get("situation", "").strip()
    topic = request.form.get("topic", "").strip()
    conversation_id=request.form.get("conversation_id", None), 
    
    connection_id_stub = current_app.config['NULL_CONNECTION_ID']
    if not connection_id:
        connection_id = f"{user_id}:{connection_id_stub}"
    
    connection_id.strip()
    
    ocr_marker = current_app.config['OCR_MARKER']
    conversation_id = request.form.get("conversation_id")
    if not conversation_id:
        conversation_id = f"{user_id}:{uuid4().hex[:6]}"
    elif conversation_id.startswith(":") and conversation_id.endswith(ocr_marker):
        conversation_id = f"{user_id}{conversation_id}"
    
    conversation_msgs = {}    
    
    convo_obj = Conversation (
        user_id=user_id, 
        connection_id=connection_id, 
        conversation_id=conversation_id,
        conversation={},
        spurs={},         # Spurs should remain empty unless explicitly supplied or inferred later
        situation=situation,
        topic=topic,
        created_at=datetime.utcnow()
        )
    
    
    try:
        conversation_msgs = process_image(image)
        
        
        if not isinstance(conversation_msgs, dict) or "conversation" not in conversation_msgs:
            err_point = __package__ or __name__
            logger.error(f"[{err_point}] - Invalid conversation object returned")
            return jsonify({"error": f"[{err_point}] - Invalid OCR response"}), 500


        if not convo_obj.user_id or not convo_obj.connection_id:
            err_point = __package__ or __name__
            logger.error(f"[{err_point}] - Missing required fields")
            return jsonify({"error": f"[{err_point}] - Missing user_id or connection_id"}), 400
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return (f"[{err_point}] - Error: {str(e)}"), 500

        
    convo_obj["conversation"] = conversation_msgs
    return jsonify({"conversation": convo_obj.to_dict()}), 200

