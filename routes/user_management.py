from flask import Blueprint, request, jsonify, g
from infrastructure.auth import require_auth
from infrastructure.clients import db
from infrastructure.logger import get_logger
from firebase_admin import auth
from services.user_service import update_user_profile

user_management_bp = Blueprint("user_management", __name__)
logger = get_logger(__name__)

@user_management_bp.route("/user", methods=["POST"])
@require_auth
def update_user_bp():
    try:
        data = request.get_json()
        uid = g.user['uid']

        age = data.get("age")
        if age and (not isinstance(age, int) or not (18 <= age <= 99)):
            err_point = __package__ or __name__
            logger.error(f"Error: {err_point}")
            return jsonify({"error": f"[{err_point}] - Error"}), 400

        json_user_profile = update_user_profile(uid, data)

        return json_user_profile
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({"error": f"[{err_point}] - Error"}), 401

@user_management_bp.route("/user", methods=["GET"])
@require_auth
def get_user_bp():
    try:
        uid = g.user['uid']
        user_ref = db.collection("users").document(uid)
        doc = user_ref.get()

        if not doc.exists:
            err_point = __package__ or __name__
            logger.error(f"Error: {err_point}")
            return jsonify({"error": f"[{err_point}] - Error"}), 404

        data = doc.to_dict()
        return jsonify({
            "uid": uid,
            "profile_text": data.get("profile_text", ""),
            "fields": data.get("fields", {})
        })
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500

@user_management_bp.route("/user", methods=["DELETE"])
@require_auth
def delete_user_bp():
    try:
        uid = g.user['uid']
        user_ref = db.collection("users").document(uid)

        def delete_subcollections(parent_ref, subcollection_names):
            for name in subcollection_names:
                sub_ref = parent_ref.collection(name)
                docs = sub_ref.stream()
                for doc in docs:
                    doc.reference.delete()

        delete_subcollections(user_ref, ["connections", "messages", "conversations"])

        user_ref.delete()

        auth.delete_user(uid)

        return jsonify({"message": "User profile deleted successfully."}), 200
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500