from flask import Blueprint, request, jsonify, current_app
from infrastructure.auth import generate_user_id, create_jwt
from infrastructure.logger import get_logger
from services.user_service import save_user_profile
from typing import Dict, Union


onboarding_bp = Blueprint("onboarding", __name__)
logger = get_logger(__name__)

@onboarding_bp.route("/onboarding", methods=["POST"])
def onboarding() -> Union[Dict, str]:
    """
    
    Onboarding route for initial login. User information stored in persisntent memory. User ID generated. 
    
    Args:
        none
        
    Return: 
        Dictionary, key is user ID and entry is user profile. 
    
    """
    
    try:
        data = request.get_json()
        age = data.get("age")
        if not isinstance(age, int) or not (18 <= age <= 99):
                err_point = __package__ or __name__
                logger.error("[%s] Error: %s", err_point, e)
                return jsonify({"error": f"[{err_point}] - Error"}), 401
        
        user_id = generate_user_id()
        token = create_jwt(user_id)
        
        ### selected_spurs are the spur variants generated for this user. Default is all variants in global constant SPUR_VARIANTS. 
        ### User is able to select a subset to be generated, and that selected subset persists until the user changes it. 
        if not data.get("selected_spurs"):
            selected_spurs = current_app.config['SPUR_VARIANTS']

        def format_field(key):
            val = data.get(key)
            return f"{key.capitalize()}: {val}" if val else None
        
        profile_fields = [
            f"user_id: {user_id}",
            f"selected_spurs: {selected_spurs}"
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