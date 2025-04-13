from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import require_auth

from services.storage_service import (
    get_conversations,
    get_saved_messages,
    save_conversation,
    get_conversation,
    delete_conversation,
    save_message,
    delete_saved_message,
)

conversations_bp = Blueprint("conversations", __name__)

@conversations_bp.route("/conversations", methods=["GET"])
@require_auth
def fetch_conversations():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    filters = {}

    if request.args.get("keyword"):
        filters["keyword"] = request.args.get("keyword")

    for date_field in ["date_from", "date_to"]:
        date_str = request.args.get(date_field)
        if date_str:
            try:
                filters[date_field] = datetime.fromisoformat(date_str)
            except ValueError:
                return jsonify({"error": f"Invalid date format for {date_field}. Use ISO format."}), 400

    result = get_conversations(user_id, filters)
    return jsonify(result)

@conversations_bp.route("/conversations", methods=["POST"])
@require_auth
def store_conversation():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    result = save_conversation(user_id, data)
    return jsonify(result)

@conversations_bp.route("/conversations/<conversation_id>", methods=["GET"])
@require_auth
def fetch_conversation(conversation_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    result = get_conversation(user_id, conversation_id)
    return jsonify(result)

@conversations_bp.route("/conversations/<conversation_id>", methods=["DELETE"])
@require_auth
def remove_conversation(conversation_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    result = delete_conversation(user_id, conversation_id)
    return jsonify(result)

@conversations_bp.route("/saved-messages", methods=["GET"])
@require_auth
def fetch_saved_messages():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

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
            except ValueError:
                return jsonify({"error": f"Invalid date format for {date_field}. Use ISO format."}), 400

    if request.args.get("keyword"):
        filters["keyword"] = request.args.get("keyword")

    sort = request.args.get("sort", "desc")
    if sort in ["asc", "desc"]:
        filters["sort"] = sort

    result = get_saved_messages(user_id, filters)
    return jsonify(result)

@conversations_bp.route("/saved-messages", methods=["POST"])
@require_auth
def store_saved_message():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    result = save_message(user_id, data)
    return jsonify(result)


@conversations_bp.route("/saved-messages/<message_id>", methods=["DELETE"])
@require_auth
def remove_saved_message(message_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    result = delete_saved_message(user_id, message_id)
    return jsonify(result)