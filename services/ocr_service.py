from google.cloud import vision
import cv2
import numpy as np
from flask import jsonify
from utils.ocr_utils import extract_chat_messages, crop_top_bottom_cv
from clients import vision_client

client = vision_client

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
def process_image(image_file):
    # Save the file temporarily to process it
    image_byte = image_file.read()

    np_arr = np.frombuffer(image_byte, np.uint8)
    image_array = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if image_array is None:
        return {"error": "Could not read processed image"}

    cropped_img = crop_top_bottom_cv(image_array)
    
    success, encoded_image = cv2.imencode('.png', cropped_img)
    if not success:
        return {"error": "Could not encode cropped image"}
    
    content = encoded_image.tobytes()
    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)

    if response.error.message:
        return {"error": response.error.message}
    
    structured_messages = extract_chat_messages(response.full_text_annotation.pages[0])
    
    if structured_messages:
        return {"final_text": structured_messages}
    else:
        return {"error": "No text detected in the image."}
