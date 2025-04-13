from flask import Blueprint, request, jsonify
from services.storage_service import save_feedback
from infrastructure.auth import require_auth

feedback_bp = Blueprint("feedback", __name__)

@feedback_bp.route("/feedback", methods=["POST"])
@require_auth
def feedback():
    data = request.json
    return jsonify(save_feedback(data))
