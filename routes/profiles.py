from flask import Blueprint, request, jsonify
from services.profile_service import (
     save_user_profile, 
     save_poi_profile,
     get_user_pois,
     get_user_profile,
     set_active_poi_firestore,
     get_active_poi_firestore,
     clear_active_poi_firestore,
     create_poi_profile,
     get_poi_profile,
     update_poi_profile,
     delete_poi_profile,
)
from utils.auth import require_auth

profiles_bp = Blueprint("profiles", __name__)

@profiles_bp.route("/user-sketch", methods=["POST"])
@require_auth
def save_user():
    data = request.get_json()
    result = save_user_profile(data)
    return jsonify(result)

@profiles_bp.route("/poi-sketch", methods=["POST"])
@require_auth
def save_poi():
    data = request.get_json()
    result = save_poi_profile(data)
    return jsonify(result)

@profiles_bp.route("/user-sketch", methods=["GET"])
@require_auth
def fetch_user_profile():
    user_id = request.args.get("user_id")
    result = get_user_profile(user_id)
    return jsonify(result)

@profiles_bp.route("/poi-sketch", methods=["GET"])
@require_auth
def fetch_user_pois():
    user_id = request.args.get("user_id")
    result = get_user_pois(user_id)
    return jsonify(result)

@profiles_bp.route("/poi-active", methods=["POST"])
@require_auth
def set_active_poi():
    data = request.get_json()
    user_id = data.get("user_id")
    poi_id = data.get("poi_id")
    if not user_id or not poi_id:
        return jsonify({"error": "Missing user_id or poi_id"}), 400
    result = set_active_poi_firestore(user_id, poi_id)
    return jsonify(result)

@profiles_bp.route("/poi-active", methods=["GET"])
@require_auth
def get_active_poi():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    result = get_active_poi_firestore(user_id)
    return jsonify(result)

@profiles_bp.route("/poi-active", methods=["DELETE"])
@require_auth
def clear_active_poi():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    result = clear_active_poi_firestore(user_id)
    return jsonify(result)

@profiles_bp.route("/poi-create", methods=["POST"])
@require_auth
def create_poi():
    data = request.get_json()
    result = create_poi_profile(data)
    return jsonify(result)

@profiles_bp.route("/poi-sketch/single", methods=["GET"])
@require_auth
def fetch_single_poi():
    user_id = request.args.get("user_id")
    cid = request.args.get("cid")
    result = get_poi_profile(user_id, cid)
    return jsonify(result)

@profiles_bp.route("/poi-sketch", methods=["PATCH"])
@require_auth
def update_poi():
    data = request.get_json()
    user_id = data.get("user_id")
    cid = data.get("cid")
    if not user_id or not cid:
        return jsonify({"error": "Missing user_id or cid"}), 400
    update_data = {k: v for k, v in data.items() if k not in {"user_id", "cid"}}
    result = update_poi_profile(user_id, cid, update_data)
    return jsonify(result)

@profiles_bp.route("/poi-sketch", methods=["DELETE"])
@require_auth
def delete_poi():
    data = request.get_json()
    user_id = data.get("user_id")
    cid = data.get("cid")
    if not user_id or not cid:
        return jsonify({"error": "Missing user_id or cid"}), 400
    result = delete_poi_profile(user_id, cid)
    return jsonify(result)