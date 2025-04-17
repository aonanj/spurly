from class_defs.conversation_def import Conversation
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g
from infrastructure.auth import require_auth
from infrastructure.id_generator import get_null_connection_id, generate_conversation_id
from infrastructure.logger import get_logger
from services.ocr_service import process_image

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


    
    user_id = g.user['user_id']
    connection_id = request.headers.get("connection_id", None)
    situation = request.form.get("situation", "").strip()
    topic = request.form.get("topic", "").strip()
    
    
    if not connection_id:
        connection_id = get_null_connection_id()
    
    connection_id.strip()
    
    conversation_id = request.form.get("conversation_id")
    if not conversation_id:
        conversation_id = generate_conversation_id(user_id)

    
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

