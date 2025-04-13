from flask import Blueprint, request, jsonify
from services.gpt_service import generate_spurs
from services.connection_service import get_active_connection_firestore, get_user_connections
from utils.middleware import enrich_context, validate_profile, sanitize_topic
from utils.auth import require_auth
from utils.logger import setup_logger

message_bp = Blueprint("message", __name__)

@message_bp.route("/generate", methods=["POST"])
@require_auth
@validate_profile
@enrich_context
@sanitize_topic
def generate():
    data = request.get_json()
    user_id = data.get("user_id")
    conversation = data.get("conversation", "")
    user_profile = data.get("user_profile", {})
    active_connection_id = data.get("connection_id")
    connection_profile = data.get("connection_profile", {})
    situation = data.get("situation", "")
    topic = data.get("topic", None)

    if not user_id:
        logger = setup_logger(name="message_log.file", toFile=True, filename="message.log")
        logger.error("Missing user_id in /generate route")
        return jsonify({"error": "Missing user_id"}), 400

    if not active_connection_id:
        active_connection_id = get_active_connection_firestore(user_id).get("active_connection_id")

    # Auto-load connection profile if not provided
    if not connection_profile:
        if active_connection_id and active_connection_id.casefold() != (f"{user_id}:current_app.config['NULL_connection_id']").casefold():
            all_connections = get_user_connections(user_id).get("connections", [])
            match = next((p for p in all_connections if p.get("connection_id") == active_connection_id), {})
            connection_profile = match
        else:
            connection_profile = None
    
    spurs, fallback_flags = generate_spurs(
        conversation=conversation,
        user_profile=user_profile,
        connection_profile=connection_profile,
        situation=situation,
        topic=topic,
    )
    return jsonify({
        "spurs": spurs,
        "fallbacks": fallback_flags
    })