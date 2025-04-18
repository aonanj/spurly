from class_defs.spur_def import Spur
from flask import Blueprint, request, jsonify, g
from infrastructure.auth import require_auth
from infrastructure.logger import get_logger
from services.connection_service import get_active_connection_firestore
from services.gpt_service import get_spurs_for_output
from utils.middleware import enrich_context, validate_profile, sanitize_topic

message_bp = Blueprint("message", __name__)
logger = get_logger(__name__)

@message_bp.route("/spurs", methods=["POST"])
@require_auth
@validate_profile
@enrich_context
@sanitize_topic
def generate():
    """
    POST /generate-message

    Receives conversation context and user/POI sketches, sends to GPT engine for Spur generation.

    Expected JSON fields:
    - conversation_id (str)
    - conversation (list of dicts)
    - user_profile (dict)
    - connection_profile (dict)
    - situation (str)
    - topic (str)

    Returns:
    - dict: Spurs by tone or error message
    """

    data = request.get_json()
    user_id = g.user['user_id']
    conversation_id = data.get("conversation_id", "")
    connection_id = data.get("connection_id", "")
    situation = data.get("situation", "")
    topic = data.get("topic", "")

    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400

    if not connection_id:
        connection_id = get_active_connection_firestore(user_id).get("connection_id")
    
    spurs = get_spurs_for_output(
        user_id=user_id, 
        connection_id=connection_id, 
        conversation_id=conversation_id, 
        situation=situation, 
        topic=topic,                                       
    )
    return jsonify({
        "user_id": user_id,
        "spurs": Spur.to_dict(spurs),
    })