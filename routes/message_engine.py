from flask import Blueprint, request, jsonify, g, current_app
from infrastructure.auth import require_auth
from infrastructure.id_generator import generate_conversation_id
from infrastructure.logger import get_logger
from services.connection_service import get_active_connection_firestore, get_user_connections
from services.gpt_service import generate_spurs
from utils.middleware import enrich_context, validate_profile, sanitize_topic

message_bp = Blueprint("message", __name__)
logger = get_logger(__name__)

@message_bp.route("/spurs", methods=["POST"])
@require_auth
@validate_profile
@enrich_context
@sanitize_topic
def generate():
    data = request.get_json()
    user_id = g.user['user_id']
    conversation = data.get("conversation", "")
    conversation_id = data.get("conversation_id")
    user_profile = data.get("user_profile", {})
    active_connection_id = data.get("connection_id")
    connection_profile = data.get("connection_profile", {})
    situation = data.get("situation", "")
    topic = data.get("topic", None)

    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400

    if not active_connection_id:
        active_connection_id = get_active_connection_firestore(user_id).get("active_connection_id")

    # Auto-load connection profile if not provided
    if not connection_profile:
        if active_connection_id and active_connection_id.casefold() != (f"{user_id}:current_app.config['NULL_CONNECTION_ID']").casefold():
            all_connections = get_user_connections(user_id).get("connections", [])
            match = next((p for p in all_connections if p.get("connection_id") == active_connection_id), {})
            connection_profile = match
        else:
            connection_profile = None
    
    if conversation and not conversation_id:
        conversation_id = generate_conversation_id(user_id)
    
    spurs, fallback_flags = generate_spurs(
        conversation_id=conversation_id,
        conversation=conversation,
        user_profile=user_profile,
        connection_profile=connection_profile,
        situation=situation,
        topic=topic,
    )
    return jsonify({
        "spurs": spurs,
        "fallbacks": fallback_flags,
        "conversation_id": conversation_id
    })