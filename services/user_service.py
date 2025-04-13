from clients import db
import uuid
from flask import current_app, jsonify
from utils.logger import setup_logger

def format_user_profile(user_id, profile_data):
    lines = [f"user_id: {user_id}"]
    for key in [
        "name", "age", "gender", "pronouns", "school", "job", "drinking", "ethnicity", "hometown"
    ]:
        value = profile_data.get(key)
        if value:
            lines.append(f"{key.capitalize()}: {value}")

    green = profile_data.get("greenlight_topics", [])
    red = profile_data.get("redlight_topics", [])
    if green:
        lines.append(f"Greenlight Topics: {', '.join(green)}")
    if red:
        lines.append(f"Redlight Topics: {', '.join(red)}")

    return "\n".join(lines)

def save_user_profile(data):
    user_id = data.get("user_id")
    if not user_id:
        logger = setup_logger(name="user_profile_log.file", toFile=True, filename="user_profile.log")
        logger.error("Missing user_id in save_user_profile")
        return {"error": "Missing user_id"}, 400

    try:
        profile_data = {k: v for k, v in data.items() if k != "user_id"}
        format_user_profile(user_id, profile_data)
        db.collection("users").document(user_id).collection("profile").document("profile").set(profile_data)
        return {"status": "user profile saved"}
    except Exception as e:
        logger = setup_logger(name="user_profile_log.file", toFile=True, filename="user_profile.log")
        logger.error("Error saving user profile: %s", e)
        return {"error": str(e)}, 500

def get_user_profile(user_id):
    if not user_id:
        return {"error": "Missing user_id"}, 400

    try:
        doc_ref = db.collection("users").document(user_id).collection("profile").document("profile")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return {"error": "Profile not found"}, 404
    except Exception as e:
        logger = setup_logger(name="user_profile_log.file", toFile=True, filename="user_profile.log")
        logger.error("Error getting user profile: %s", e)
        return {"error": str(e)}, 500

def update_user_profile(user_id, profile_data):
    try:
        data = profile_data
        uid = user_id

        def format_field(key):
            val = data.get(key)
            return f"{key.capitalize()}: {val}" if val else None

        # Build profile fields
        profile_fields = [
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
            profile_fields.append(f"Greenlight Topics: {', '.join(green)}")
        if red:
            profile_fields.append(f"Redlight Topics: {', '.join(red)}")

        user_profile = "\n".join(f for f in profile_fields if f)

        # Save structured and formatted data to Firestore
        
        user_ref = db.collection("users").document(uid)
        user_ref.set({
            "uid": uid,
            "profile_text": user_profile,
            "fields": {k: v for k, v in data.items() if v is not None}
        })
        
        return jsonify({
            "uid": uid,
            "user_profile": user_profile
        })
    except Exception as e:
        logger = setup_logger(name="user_service_log.file", toFile=True, filename="user_service.log")
        logger.error("User service error: %s", e)
        return jsonify({"error": str(e)}), 500