from flask import Blueprint, request, jsonify
from utils.auth import require_auth, generate_uid, create_jwt
from services.clients import db

user_sketch_bp = Blueprint("user_sketch", __name__)

@user_sketch_bp.route("/user-sketch", methods=["POST"])
@require_auth
def update_user_sketch_bp():
    data = request.get_json()
    uid = request.uid

    age = data.get("age")
    if age and (not isinstance(age, int) or not (18 <= age <= 99)):
        return jsonify({"error": "You must be over the age of 18"}), 400

    def format_field(key):
        val = data.get(key)
        return f"{key.capitalize()}: {val}" if val else None

    # Build sketch fields
    sketch_fields = [
        f"UID: {uid}",
        format_field("age"),
        format_field("name"),
        format_field("gender"),
        format_field("pronouns"),
        format_field("school"),
        format_field("job"),
        format_field("drinking"),
        format_field("ethnicity"),
        format_field("hometown"),
     #    format_field("tone"),
     #    format_field("humor_style"),
     #    format_field("writing_style"),
     #    format_field("emoji_use"),
     #    format_field("flirt_level"),
     #    format_field("openness"),
     #    format_field("banter"),
    ]

    green = data.get("greenlight_topics", [])
    red = data.get("redlight_topics", [])

    if green:
        sketch_fields.append(f"Greenlight Topics: {', '.join(green)}")
    if red:
        sketch_fields.append(f"Redlight Topics: {', '.join(red)}")

    user_sketch = "\n".join(f for f in sketch_fields if f)

    # Save structured and formatted data to Firestore
    user_ref = db.collection("users").document(uid)
    user_ref.set({
        "uid": uid,
        "sketch_text": user_sketch,
        "fields": {k: v for k, v in data.items() if v is not None}
    })

    return jsonify({
        "uid": uid,
        "user_sketch": user_sketch
    })

@user_sketch_bp.route("/get-user-sketch", methods=["GET"])
@require_auth
def get_user_sketch_bp():
    uid = request.uid
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()

    if not doc.exists:
        return jsonify({"error": "User sketch not found."}), 404

    data = doc.to_dict()
    return jsonify({
        "uid": uid,
        "sketch_text": data.get("sketch_text", ""),
        "fields": data.get("fields", {})
    })