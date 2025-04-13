from flask import Blueprint, request, jsonify, g, current_app
from services.connection_service import (
     save_connection_profile,
     get_user_connections,
     set_active_connection_firestore,
     get_active_connection_firestore,
     clear_active_connection_firestore,
     create_connection_profile,
     get_connection_profile,
     update_connection_profile,
     delete_connection_profile,
)
from infrastructure.auth import require_auth
from infrastructure.logger import setup_logger

connection_bp = Blueprint("connection", __name__)

@connection_bp.route("/connection/save", methods=["POST"])
@require_auth
def save_connection():
    data = request.get_json()
    result = save_connection_profile(data)
    return jsonify(result)

@connection_bp.route("/connection/fetch-all", methods=["GET"])
@require_auth
def fetch_user_connections():
    user_id = g.user['uid']
    result = get_user_connections(user_id)
    return jsonify(result)

@connection_bp.route("/connection/set-active", methods=["POST"])
@require_auth
def set_active_connection():
    data = request.get_json()
    user_id = g.user['uid']
    if data.get("connection_id"):
        connection_id = data["connection_id"]
    else:
        connection_id = f"{user_id}:{current_app.config['NULL_CONNECTION_ID']}"

    if not user_id or not connection_id:
        logger = setup_logger(name="profiles_log.file", toFile=True, filename="profiles.log")
        logger.error("Error in routes.profiles.set_active_connection: missing ID")
        return jsonify({"error": "Missing user_id or connection_id"}), 400
    result = set_active_connection_firestore(user_id, connection_id)
    return jsonify(result)

@connection_bp.route("/connection/get-active", methods=["GET"])
@require_auth
def get_active_connection():
    user_id = g.user['uid']
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    result = get_active_connection_firestore(user_id)
    return jsonify(result)

@connection_bp.route("/connection/clear-active", methods=["DELETE"])
@require_auth
def clear_active_connection():
    user_id = g.user['uid']
    if not user_id:
        logger = setup_logger(name="profiles_log.file", toFile=True, filename="profiles.log")
        logger.error("Error in routes.profiles.clear_active_connection: missing ID")
        return jsonify({"error": "Missing user_id"}), 400
    result = clear_active_connection_firestore(user_id)
    return jsonify(result)

@connection_bp.route("/connection/create", methods=["POST"])
@require_auth
def create_connection():
    data = request.get_json()
    result = create_connection_profile(data)
    return jsonify(result)

@connection_bp.route("/connection/fetch-single", methods=["GET"])
@require_auth
def fetch_single_connection():
    user_id = g.user['uid']
    connection_id = request.args.get("connection_id")
    result = get_connection_profile(user_id, connection_id)
    return jsonify(result)

@connection_bp.route("/connection/update", methods=["PATCH"])
@require_auth
def update_connection():
    data = request.get_json()
    user_id = g.user['uid']
    connection_id = data.get("connection_id")
    if not user_id or not connection_id:
        logger = setup_logger(name="profiles_log.file", toFile=True, filename="profiles.log")
        logger.error("Error in routes.profiles.update_connection: missing ID")
        return jsonify({"error": "Missing user_id or connection_id"}), 400
    update_data = {k: v for k, v in data.items() if k not in {"user_id", "connection_id"}}
    result = update_connection_profile(user_id, connection_id, update_data)
    return jsonify(result)

@connection_bp.route("/connection/delete", methods=["DELETE"])
@require_auth
def delete_connection():
    data = request.get_json()
    user_id = g.user['uid']
    connection_id = data.get("connection_id")
    if not user_id or not connection_id:
        logger = setup_logger(name="profiles_log.file", toFile=True, filename="profiles.log")
        logger.error("Error in routes.profiles.delete_connection: missing ID")
        return jsonify({"error": "Missing user_id or connection_id"}), 400
    result = delete_connection_profile(user_id, connection_id)
    return jsonify(result)