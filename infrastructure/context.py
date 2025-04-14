from flask import g, request, jsonify
from services.user_service import get_user_profile
from flask import Blueprint, request, jsonify
from services.connection_service import get_connection_profile
from infrastructure.context import set_current_connection, get_current_connection, clear_current_connection, get_current_user
from infrastructure.auth import require_auth

def set_current_user(profile):
    g.current_user = profile

def get_current_user():
    return getattr(g, "current_user", None)

def set_current_connection(profile):
    g.current_connection = profile

def get_current_connection():
    return getattr(g, "current_connection", None)

def clear_current_connection():
    g.current_connection = None

def load_user_context():
    """
    Middleware to auto-load the current user's profile from the X-User-ID header.
    """
    user_id = request.headers.get("X-User-ID")
    if user_id:
        profile = get_user_profile(user_id)
        if profile:
            set_current_user(profile)

def require_user_context():
    """
    Middleware that enforces user context must be loaded for protected routes.
    """
    if not get_current_user():
        return jsonify({"error": "Missing user context"}), 401

context_bp = Blueprint("context", __name__)

@context_bp.route("/context/connection", methods=["POST"])
@require_auth
def set_connection_context():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User context not loaded"}), 401

    connection_id = request.json.get("connection_id")
    if not connection_id:
        return jsonify({"error": "Missing connection_id"}), 400

    profile = get_connection_profile(user.user_id, connection_id)
    if not profile:
        return jsonify({"error": "Connection profile not found"}), 404

    set_current_connection(profile)
    return jsonify({"message": "Connection context set successfully."})

@context_bp.route("/context/connection", methods=["DELETE"])
@require_auth
def clear_connection_context():
    clear_current_connection()
    return jsonify({"message": "Connection context cleared."})

@context_bp.route("/context", methods=["GET"])
@require_auth
def get_context():
    user = get_current_user()
    connection = get_current_connection()

    return jsonify({
        "user_profile": user.to_dict() if user else None,
        "connection_profile": connection.to_dict() if connection else None
    })