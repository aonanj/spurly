import cv2
import numpy as np
from flask import Blueprint, request, jsonify, g
import logging

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # Default to 10MB, place in config.py

from services.classifiers import classify_image
from services.ocr_service import process_image # Expects (user_id, image_bytes)
from utils.extract_profile_snippet import extract_profile_snippet # Expects (image_bytes)
from utils.photo_forwarder import forward_full_image_to_model # Expects (image_bytes)
from infrastructure.auth import require_auth # Assuming @require_auth is here
from infrastructure.logger import get_logger # Using your logger

# Initialize logger using your get_logger utility
logger = get_logger(__name__)

# Define the Blueprint
ocr_bp = Blueprint('ocr', __name__)

@ocr_bp.route('/scan', methods=['POST']) # Changed route slightly to avoid potential conflict if /ocr is globally used
@require_auth # Apply the authentication decorator
def ocr_scan(): # Renamed function to avoid conflict with any potential top-level ocr name
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            # This case should ideally be handled by @require_auth
            # if it's properly enforcing authentication and setting g.user_id.
            logger.error("User ID not found in g after @require_auth.")
            return jsonify({"error": "Authentication error: User ID not available."}), 401

        file = request.files.get('image')
        if file is None:
            logger.error("No image file provided in request for user_id: %s", user_id)
            return jsonify({"error": "Missing 'image' file in request"}), 400

        file.seek(0, 2)  # move to end of file
        size = file.tell()
        if size == 0:
            logger.error("Empty image file provided by user_id: %s", user_id)
            return jsonify({"error": "Empty 'image' file provided"}), 400
        if size > MAX_IMAGE_SIZE_BYTES:
            logger.error("Uploaded image too large: %d bytes for user_id: %s. Limit is %d bytes.",
                         size, user_id, MAX_IMAGE_SIZE_BYTES)
            return jsonify({"error": f"Image size exceeds limit of {MAX_IMAGE_SIZE_BYTES // (1024*1024)}MB"}), 413
        file.seek(0)  # reset pointer to the beginning of the file

        image_bytes = file.read()
        if not image_bytes: # Double check after read, though size > 0 should cover this
            logger.error("Failed to read image bytes, or image is empty for user_id: %s", user_id)
            return jsonify({"error": "Invalid or empty image data after read"}), 400
            
        nparr = np.frombuffer(image_bytes, np.uint8)
        image_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image_cv2 is None:
            logger.error("Failed to decode image for user_id: %s. The image data may be corrupt or not a supported format.", user_id)
            return jsonify({"error": "Invalid or corrupt image data"}), 400

        # Image Classification
        category = classify_image(image_cv2) # classify_image from services.classifiers
        logger.info("Image classified as '%s' for user_id: %s", category, user_id)

        data = None
        if category == 'conversation':
            # process_image from ocr_service expects user_id and image_bytes
            data = process_image(user_id=user_id, image_file=image_bytes)
        elif category == 'profile_snippet':
            # extract_profile_snippet from utils.extract_profile_snippet expects image_bytes
            data = extract_profile_snippet(image=image_bytes)
        elif category == 'photo': # Assuming 'photo' is a category from your classifier
            # forward_full_image_to_model from utils.photo_forwarder expects image_bytes
            data = forward_full_image_to_model(image_bytes=image_bytes)
        else:
            logger.warning("Image from user_id: %s classified into an unhandled category: '%s'. Defaulting to 'photo' processing.",
                           user_id, category)
            # Fallback or specific handling for unknown categories
            data = forward_full_image_to_model(image_bytes=image_bytes) 

        if data is None:
            logger.error("Processing failed to return data for category '%s', user_id: %s", category, user_id)
            return jsonify({"error": "Failed to process image for the determined category."}), 500
            
        return jsonify(data)

    except Exception as e:
        # Log the full exception for debugging
        logger.exception("Unhandled exception in /ocr/scan for user_id: %s. Error: %s", getattr(g, 'user_id', 'Unknown'), e)
        return jsonify({"error": "An internal server error occurred while processing the image."}), 500