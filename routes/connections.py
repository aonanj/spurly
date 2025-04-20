from flask import Blueprint, request, jsonify, g, current_app
from infrastructure.auth import require_auth
from infrastructure.id_generator import get_null_connection_id
from infrastructure.logger import get_logger
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

logger = get_logger(__name__)

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
    user_id = g.user['user_id']
    result = get_user_connections(user_id)
    return jsonify(result)

@connection_bp.route("/connection/set-active", methods=["POST"])
@require_auth
def set_active_connection():
    data = request.get_json()
    user_id = g.user['user_id']
    if data.get("connection_id"):
        connection_id = data["connection_id"]
    else:
        connection_id = get_null_connection_id(user_id)

    if not user_id or not connection_id:
        err_point = __package__ or __name__ # pragma: no cover
        logger.error(f"Error: {err_point}") # pragma: no cover
        return jsonify({'error': f"[{err_point}] - Error:"}), 400 # pragma: no cover
    result = set_active_connection_firestore(user_id, connection_id)
    return jsonify(result)

@connection_bp.route("/connection/get-active", methods=["GET"])
@require_auth
def get_active_connection():
    user_id = g.user['user_id']
    if not user_id:
        err_point = __package__ or __name__ # pragma: no cover
        logger.error(f"Error: {err_point}") # pragma: no cover
        return jsonify({'error': f"[{err_point}] - Error:"}), 400 # pragma: no cover
    result = get_active_connection_firestore(user_id)
    return jsonify(result)

@connection_bp.route("/connection/clear-active", methods=["DELETE"])
@require_auth
def clear_active_connection():
    user_id = g.user['user_id']
    if not user_id:
        err_point = __package__ or __name__ # pragma: no cover
        logger.error(f"Error: {err_point}") # pragma: no cover
        return jsonify({'error': f"[{err_point}] - Error:"}), 500 # pragma: no cover
    result = clear_active_connection_firestore(user_id)
    return jsonify(result)

@connection_bp.route("/connection/create", methods=["POST"])
@require_auth
def create_connection():
    # Parse multipart/form-data for connection details, images, and links
    data = request.form.to_dict()
    images = request.files.getlist('images')
    # Convert uploaded FileStorage objects to raw bytes
    image_bytes = [img.read() for img in images]
    links = request.form.getlist('links')
    result = create_connection_profile(data, image_bytes, links)
    return jsonify(result)

@connection_bp.route("/connection/fetch-single", methods=["GET"])
@require_auth
def fetch_single_connection():
    user_id = g.user['user_id']
    connection_id = request.args.get("connection_id", "")
    result = get_connection_profile(user_id, connection_id)
    return jsonify(result)

@connection_bp.route("/connection/update", methods=["PATCH"])
@require_auth
def update_connection():
    # Parse multipart/form-data for update details, images, and links
    data = request.form.to_dict()
    images = request.files.getlist('images')
    # Convert uploaded FileStorage objects to raw bytes
    image_bytes = [img.read() for img in images]
    links = request.form.getlist('links')
    user_id = g.user['user_id']
    connection_id = data.get("connection_id")
    if not user_id or not connection_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400
    update_data = {k: v for k, v in data.items() if k not in {"user_id", "connection_id"}}
    result = update_connection_profile(user_id, connection_id, update_data, image_bytes, links)
    return jsonify(result)

@connection_bp.route("/connection/delete", methods=["DELETE"])
@require_auth
def delete_connection():
    data = request.get_json()
    user_id = g.user['user_id']
    connection_id = data.get("connection_id")
    if not user_id or not connection_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400
    result = delete_connection_profile(user_id, connection_id)
    return jsonify(result)