from flask import Blueprint, request, jsonify
from services.ocr_service import process_image
from infrastructure.auth import require_auth
from infrastructure.logger import get_logger

ocr_bp = Blueprint("ocr", __name__)
logger = get_logger(__name__)

@ocr_bp.route("/upload", methods=["POST"])
@require_auth
def upload_image():
    image = request.files.get("image")
    if not image:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({"error": f"[{err_point}] - Error"}), 400
    try:
        conversation = process_image(image)
        return jsonify({"conversation": conversation.get("final_text", [])}), 200
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return (f"[{err_point}] - Error: {str(e)}"), 500
