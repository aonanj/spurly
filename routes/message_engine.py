from flask import Blueprint, request, jsonify
from services.gpt_service import generate_spurs
from services.profile_service import get_active_poi_firestore, get_user_pois
from utils.middleware import enrich_context, validate_sketch, sanitize_topic
from utils.auth import require_auth

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
    poi_sketch = data.get("poi_sketch", {})
    situation = data.get("situation", "")
    topic = data.get("topic", None)

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    # Auto-load POI sketch if not provided
    if not poi_sketch:
        active_poi = get_active_poi_firestore(user_id).get("active_poi")
        if active_poi:
            all_pois = get_user_pois(user_id).get("pois", [])
            match = next((p for p in all_pois if p.get("poi_id") == active_poi), {})
            poi_sketch = match
    
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