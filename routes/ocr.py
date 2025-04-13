from flask import Blueprint, request, jsonify
from services.ocr_service import process_image
from utils.auth import require_auth

ocr_bp = Blueprint("ocr", __name__)

@ocr_bp.route("/upload", methods=["POST"])
@require_auth
def upload_image():
    image = request.files.get("image")
    if not image:
        return jsonify({"error": "Image file is required"}), 400
    try:
        conversation = process_image(image)
        return jsonify({"conversation": conversation.get("final_text", [])}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
