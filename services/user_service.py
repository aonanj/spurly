from infrastructure.clients import db
from flask import jsonify
from firebase_admin import auth
from infrastructure.logger import get_logger
from class_defs.profile_def import Profile
from dataclasses import fields

logger = get_logger(__name__)

def format_user_profile(profile: Profile) -> str:
    lines = [f"user_id: {profile.user_id}"]

    for field in fields(Profile):
        key = field.name
        value = getattr(profile, key)

        if key == "user_id" or value is None:
            continue

        if isinstance(value, list):
            if value:
                label = "Greenlight Topics" if key == "greenlights" else (
                        "Redlight Topics" if key == "redlights" else key.capitalize())
                lines.append(f"{label}: {', '.join(value)}")
        else:
            lines.append(f"{key.capitalize()}: {value}")

    return "\n".join(lines)

def save_user_profile(data):
    user_id = data.get("user_id")
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return f"error - {err_point} - Error:", 400

    try:
        profile = Profile.from_dict(data)
        profile_doc = format_user_profile(profile)
        user_ref = db.collection("users").document(user_id)
        user_ref.set({
            "user_id": user_id,
            "profile_entries": profile_doc,
            "fields": profile.to_dict()
        })
        return {"status": "user profile saved"}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return f"error - {err_point} - Error: {str(e)}", 500

def get_user_profile(user_id):
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return f"error - {err_point} - Error:", 404

    try:
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()

        if not doc.exists:
            err_point = __package__ or __name__
            logger.error(f"Error: {err_point}")
            return jsonify({"error": f"[{err_point}] - User not found"}), 404

        data = doc.to_dict()
        profile = Profile.from_dict(data.get("fields", {}))
        return jsonify({
            "user_id": user_id,
            "profile_entries": data.get("profile_entries", ""),
            "fields": profile.to_dict()
        })
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500

def update_user_profile(user_id, profile_data):
    try:
        data = profile_data
        profile = Profile.from_dict({"user_id": user_id, **data})
        user_ref = db.collection("users").document(user_id)
        user_ref.set({
            "user_id": user_id,
            "profile_entries": format_user_profile(profile),
            "fields": profile.to_dict()
        })
        return jsonify({
            "user_id": user_id,
            "user_profile": profile.to_dict()
        })
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return f"error - {err_point} - Error: {str(e)}", 500

def delete_user_profile(user_id):
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return False
    try:
        user_ref = db.collection("users").document(user_id)

        # Optional: Load and log profile before deletion
        doc = user_ref.get()
        if doc.exists:
            profile_data = doc.to_dict().get("fields", {})
            profile = Profile.from_dict(profile_data)
            logger.info(f"Deleting user profile: {profile.to_dict()}")

        def delete_subcollections(parent_ref, subcollection_names):
            for name in subcollection_names:
                sub_ref = parent_ref.collection(name)
                docs = sub_ref.stream()
                for doc in docs:
                    doc.reference.delete()

        delete_subcollections(user_ref, ["connections", "messages", "conversations"])

        user_ref.delete()
        auth.delete_user(user_id)
        return True
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return False