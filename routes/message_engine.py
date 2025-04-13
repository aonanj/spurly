from flask import Blueprint, request, jsonify
from services.gpt_service import generate_spurs
from services.profile_service import get_active_poi_firestore, get_user_pois
from utils.middleware import enrich_context, validate_sketch, sanitize_topic
from utils.auth import require_auth
from utils.logger import setup_logger

message_bp = Blueprint("message", __name__)

@message_bp.route("/generate", methods=["POST"])
@require_auth
@validate_sketch
@enrich_context
@sanitize_topic
def generate():
    data = request.get_json()
    user_id = data.get("user_id")
    conversation = data.get("conversation", "")
    user_sketch = data.get("user_sketch", {})
    active_cid = data.get("cid")
    poi_sketch = data.get("poi_sketch", {})
    situation = data.get("situation", "")
    topic = data.get("topic", None)

    if not user_id:
        logger = setup_logger(name="message_log.file", toFile=True, filename="message.log")
        logger.error("Missing user_id in /generate route")
        return jsonify({"error": "Missing user_id"}), 400

    # Auto-load POI sketch if not provided
    if not poi_sketch:
        active_poi = get_active_poi_firestore(user_id).get("active_poi")
        if active_poi and active_poi.casefold() != (f"{user_id}:current_app.config['NULL_CID']").casefold():
            all_pois = get_user_pois(user_id).get("pois", [])
            match = next((p for p in all_pois if p.get("cid") == active_poi), {})
            poi_sketch = match
        else:
            poi_sketch = None
    
    spurs, fallback_flags = generate_spurs(
        conversation=conversation,
        user_sketch=user_sketch,
        poi_sketch=poi_sketch,
        situation=situation,
        topic=topic,
    )
    return jsonify({
        "spurs": spurs,
        "fallbacks": fallback_flags
    })