from flask import Blueprint, request, jsonify, g
from datetime import datetime
from infrastructure.auth import require_auth
from infrastructure.logger import get_logger

from services.storage_service import (
    get_conversations,
    get_saved_messages,
    save_conversation,
    get_conversation,
    delete_conversation,
    save_message,
    delete_saved_message,
)

logger = get_logger(__name__)

conversations_bp = Blueprint("conversations", __name__)

@conversations_bp.route("/conversations", methods=["GET"])
@require_auth
def get_conversations_bp():
    user_id = g.user['user_id']
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400

    filters = {}

    if request.args.get("keyword"):
        filters["keyword"] = request.args.get("keyword")

    for date_field in ["date_from", "date_to"]:
        date_str = request.args.get(date_field)
        if date_str:
            try:
                filters[date_field] = datetime.fromisoformat(date_str)
            except ValueError as e:
                err_point = __package__ or __name__
                logger.error("[%s] Error: %s", err_point, e)
                return jsonify({'error': f"{err_point} - Error: {str(e)}"}), 400

    result = get_conversations(user_id, filters)
    return jsonify(result)

@conversations_bp.route("/conversations", methods=["POST"])
@require_auth
def save_conversation_bp():
    data = request.get_json()
    user_id = g.user['user_id']
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400
    result = save_conversation(user_id, data)
    return jsonify(result)

@conversations_bp.route("/conversations/<conversation_id>", methods=["GET"])
@require_auth
def get_conversation_bp(conversation_id):
    user_id = g.user['user_id']
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"{err_point} - Error:"}), 400
    result = get_conversation(user_id, conversation_id)
    return jsonify(result)

@conversations_bp.route("/conversations/<conversation_id>", methods=["DELETE"])
@require_auth
def delete_conversation_bp(conversation_id):
    user_id = request.args.get("user_id")
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400
    result = delete_conversation(user_id, conversation_id)
    return jsonify(result)

@conversations_bp.route("/saved-messages", methods=["GET"])
@require_auth
def fetch_saved_messages_bp():
    user_id = request.args.get("user_id")
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400

    filters = {}
    for field in ["variant", "situation"]:
        value = request.args.get(field)
        if value:
            filters[field] = value

    for date_field in ["date_from", "date_to"]:
        date_str = request.args.get(date_field)
        if date_str:
            try:
                filters[date_field] = datetime.fromisoformat(date_str)
            except ValueError as e:
                err_point = __package__ or __name__
                logger.error(f"Error: {err_point}")
                return jsonify({'error': f"[{err_point}] - Error:"}), 400

    if request.args.get("keyword"):
        filters["keyword"] = request.args.get("keyword")

    sort = request.args.get("sort", "desc")
    if sort in ["asc", "desc"]:
        filters["sort"] = sort

    result = get_saved_messages(user_id, filters)
    return jsonify(result)

@conversations_bp.route("/saved-messages", methods=["POST"])
@require_auth
def save_message_bp():
    data = request.get_json()
    user_id = g.user['user_id']
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400

    result = save_message(user_id, data)
    return jsonify(result)


@conversations_bp.route("/saved-messages/<message_id>", methods=["DELETE"])
@require_auth
def delete_saved_message_bp(message_id):
    user_id = g.user['user_id']
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400

    result = delete_saved_message(user_id, message_id)
    return jsonify(result)