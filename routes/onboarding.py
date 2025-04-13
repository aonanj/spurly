from flask import Blueprint, request, jsonify
from utils.auth import require_auth, generate_uid, create_jwt
from services.clients import db
from utils.logger import setup_logger

onboarding_bp = Blueprint("onboarding", __name__)

@onboarding_bp.route("/onboarding", methods=["POST"])
def onboarding():
    try:
        data = request.get_json()
        age = data.get("age")
        if not isinstance(age, int) or not (18 <= age <= 99):
            setup_logger(name="onboarding_log.file", toFile=True, fileName="onboarding.log").error("routes.onboarding.onboarding: Age verification failure")
            return jsonify({"error": "You must be over the age of 18"}), 400
        
        uid = generate_uid()
        token = create_jwt(uid)

        def format_field(key):
            val = data.get(key)
            return f"{key.capitalize()}: {val}" if val else None
        
        sketch_fields = [
            f"UID: {uid}",
            f"Age: {age}",
            format_field("name"),
            format_field("gender"),
            format_field("pronouns"),
            format_field("school"),
            format_field("job"),
            format_field("drinking"),
            format_field("ethnicity"),
            format_field("hometown"),
            #format_field("tone"),
            #format_field("humor_style"),
            #format_field("writing_style"),
            #format_field("emoji_use"),
            #format_field("flirt_level"),
            #format_field("openness"),
            #format_field("banter"),
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
    except Exception as e:
        setup_logger(name="onboarding_log.file", toFile=True, filename="onboarding.log").error(f"Error onboarding: {e}")
        return {"error": str(e)}