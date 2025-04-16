from flask import jsonify
from google.cloud import vision
from infrastructure.clients import vision_client
from infrastructure.logger import get_logger
from utils.ocr_utils import extract_conversation, crop_top_bottom_cv
import cv2
import numpy as np

client = vision_client
logger = get_logger(__name__)


def process_image(image_file) -> dict:
    """""
        Accepts a file_name as an arg, file should be a screen shot of a messaging conversation. 
        file should be in request.files. Perform error check before calling ocr(...) -->
                
                if 'file' not in request.files:
                    return jsonify({"error": "No file part"})
                    
                file = request.files['file']
                
                if file.filename == '':
                    return jsonify({"error": "No selected file"})
        
        Will need to import Flask and request to use this error check. 
    """""
    try:
        # Save the file temporarily to process it
        image_byte = image_file.read()

        np_arr = np.frombuffer(image_byte, np.uint8)
        image_array = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if image_array is None:
            err_point = __package__ or __name__
            logger.error(f"Error: {err_point}")
            return jsonify({'error': f"[{err_point}] - Error:"})

        cropped_img = crop_top_bottom_cv(image_array)
        
        success, encoded_image = cv2.imencode('.png', cropped_img)
        if not success:
            err_point = __package__ or __name__
            logger.error(f"Error: {err_point}")
            return jsonify({'error': f"[{err_point}] - Error:"})
        
        content = encoded_image.tobytes()
        image = vision.Image(content=content)

        response = client.document_text_detection(image=image)

        if response.error.message:
            err_point = __package__ or __name__
            logger.error(f"Error: {err_point}: {response.error.message}")
            return jsonify({'error': f"[{err_point}] - Error - {response.error.messasge}"})
        
        conversation_msgs = extract_conversation(response.full_text_annotation.pages[0])

        if conversation_msgs:
            return conversation_msgs
        else:
            err_point = __package__ or __name__
            logger.error(f"Error: {err_point}")
            return f"error: {err_point} - Error:"
    except Exception as e:
                err_point = __package__ or __name__
                logger.error("[%s] Error: %s", err_point, e)
                return f"error: [{err_point}] - Error: {str(e)}"
