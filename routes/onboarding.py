from flask import Blueprint, request, jsonify
from infrastructure.auth import generate_user_id, create_jwt
from infrastructure.logger import get_logger
from services.user_service import save_user_profile

onboarding_bp = Blueprint("onboarding", __name__)
logger = get_logger(__name__)

@onboarding_bp.route("/onboarding", methods=["POST"])
def onboarding():
    try:
        data = request.get_json()
        age = data.get("age")
        if not isinstance(age, int) or not (18 <= age <= 99):
                err_point = __package__ or __name__
                logger.error("[%s] Error: %s", err_point, e)
                return jsonify({"error": f"[{err_point}] - Error"}), 401
        
        user_id = generate_user_id()
        token = create_jwt(user_id)

        def format_field(key):
            val = data.get(key)
            return f"{key.capitalize()}: {val}" if val else None
        
        profile_fields = [
            f"UID: {user_id}",
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
            profile_fields.append(f"Greenlight Topics: {', '.join(green)}")
        if red:
            profile_fields.append(f"Redlight Topics: {', '.join(red)}")

        user_profile = "\n".join(f for f in profile_fields if f)

        # Save structured and formatted data to Firestore
        save_user_profile(user_id, user_profile)

        return jsonify({
            "user_id": user_id,
            "user_profile": user_profile
        })
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return f"error: {err_point} - Error"