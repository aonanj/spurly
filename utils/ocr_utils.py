import cv2
import numpy as np
import re

def get_text_from_element(element):
    """Extracts text from a Vision API element (Block, Paragraph, Word)."""
    block_text = ""
    for paragraph in getattr(element, 'paragraphs', []):
        para_text = ""
        for word in getattr(paragraph, 'words', []):
            word_text = "".join([symbol.text for symbol in getattr(word, 'symbols', [])])
            para_text += word_text + " " # Add space after each word (cleaned later)
        block_text += para_text.strip()
    if not block_text.strip() and hasattr(element, 'text'):
         block_text = element.text
    return block_text.strip()

def crop_top_bottom_cv(img):
    """
    Crops the top and bottom rows off an image.

    Args:
        img: A NumPy array containing the image file content.

    Returns:
        cropped_image: A byte string containing the cropped image file content.
    """
    # Define the crop percentages
     # 10% from the top and 15% from the bottom
    top_crop_percent = 0.10
    bottom_crop_percent = 0.15
    
    # Read the image
    if img is None:
        raise ValueError("Unable to open image.")
        
    height, width = img.shape[:2]

    if height == 0 or width == 0:
        print(f"Error: Invalid image dimensions (height={height}, width={width}).")
        return None

    # Calculate the number of pixels to remove from the top (10%)
    top_crop_pixels = int(height * top_crop_percent)

    # Calculate the number of pixels to remove from the bottom (15%)
    bottom_crop_pixels = int(height * bottom_crop_percent)

    # Determine the starting row index (inclusive)
    start_row = top_crop_pixels

    # Determine the ending row index (exclusive)
    # End index = Total height - pixels to remove from bottom
    end_row = height - bottom_crop_pixels

    if start_row >= end_row:
        return None # Cannot perform a valid crop

    # Perform Cropping using NumPy slicing
    # Slicing format: image[start_row:end_row, start_col:end_col]
    # want all columns, so use ':' for the column slice
    cropped_image = img[start_row:end_row, :]

    return cropped_image

def extract_chat_messages(page, confidence_threshold=0.80):
    """
    Detects text blocks, filters metadata/UI elements using refined logic
    (full match for some, looser content+position for headers), identifies speaker,
    orders messages, and cleans up punctuation spacing.
    Version 11 adjusts filtering strategy again.

    Args:
        image_bytes: A byte string containing the image file content.
        confidence_threshold (float): Minimum confidence for a block to be considered.

    Returns:
        A tuple containing:
        - A list of structured messages [{'speaker': 'A/B', 'text': '...'}, ...]
    """
    image_width = page.width
    image_height = page.height
    image_center_x = image_width / 2

    structured_messages = []
    block_data_for_sorting = []

    # --- Define patterns for filtering ---
    # Patterns requiring a FULL match (timestamps, statuses, exact labels)
    fullmatch_patterns = [
        r"^\s*Chat\s*$",
        r"^\s*Profile\s*$",
        r"^\s*Send a message\s*$",
        r"^\s*Sent\s*$",
        r"^\s*GIF\s*$",
        r"^\s*Delivered\s*$",
        # Timestamps (check full match)
        r"^\s*Tue\s*,?\s*Apr\s*\d{1,2}\s*,?\s*\d{1,2}:\d{2}\s*AM\s*$",
        r"^\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s*,?\s*\d{4}\s+at\s+\d{1,2}:\d{2}\s*(AM|PM)\s*$",
        r"^\s*(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)\s+\d{1,2}:\d{2}\s*(AM|PM)\s*$",
        r"^\s*$", # Empty strings
    ]
    # Patterns indicating a Header element IF near top (check content using re.search)
    header_content_patterns = [
        r"\d{1,2}\s*[:\s-]\s*\d{2}",  # Time like 10:12 or 4:38 (anywhere in string)
        r"<",                         # Back arrow character

    ]
    compiled_fullmatch_patterns = [re.compile(p, re.IGNORECASE) for p in fullmatch_patterns]
    compiled_header_content_patterns = [re.compile(p, re.IGNORECASE) for p in header_content_patterns]

    for i, block in enumerate(page.blocks):
        if not block.bounding_box or not block.bounding_box.vertices or len(block.bounding_box.vertices) != 4:  ##Skip invalid/missing bounding box
                continue
        if block.confidence < confidence_threshold: ##Skip low confidence bounding box
                continue

        vertices = block.bounding_box.vertices
        ## verts_str = ", ".join([f"({v.x},{v.y})" for v in vertices])
        y_position = min(v.y for v in vertices)
        x_positions = [v.x for v in vertices]
        min_x = min(x_positions)
        max_x = max(x_positions)

        # --- Speaker Assignment (Midpoint Heuristic) ---
        block_mid_x = (min_x + max_x) / 2
        speaker = "Party B" if block_mid_x < image_center_x else "Party A"
        block_text = ""
        for paragraph in block.paragraphs:
            words = [symbol for word in paragraph.words for symbol in word.symbols]
            confidences = [symbol.confidence for symbol in words if hasattr(symbol, 'confidence')]
            low_conf_count = sum(1 for c in confidences if c < confidence_threshold)
            total_conf_count = len(confidences)

            if total_conf_count > 0 and (low_conf_count / total_conf_count) > 0.5:
                block_data_for_sorting.append({
                    "speaker": speaker,
                    "text": " ",
                    "unreadable": True,
                    "y_pos": y_position
                })
                is_non_message = True
            else:
                block_text = get_text_from_element(block)
                is_non_message = False

        # --- Filtering ---
        if not block_text:
            is_non_message = True
        else:
            # 1. Check for full matches (timestamps, specific labels, etc.)
            for pattern in compiled_fullmatch_patterns:
                if pattern.fullmatch(block_text):
                    is_non_message = True
                    break
            # 2. If not filtered yet, check for header content *if* block is near the top
            if not is_non_message and y_position < image_height * 0.15: # Check top 15%
                for pattern in compiled_header_content_patterns:
                    # Use re.search to find the pattern anywhere in the block text
                    if pattern.search(block_text):
                        is_non_message = True
                        break
        if is_non_message:
            continue # Skip this block if filtered

        # --- Text Cleanup (Punctuation, Quotes, Spacing) ---
        cleaned_text = re.sub(r'\s+([.,?!;:])', r'\1', block_text)
        cleaned_text = re.sub(r'(")\s+', r'\1', cleaned_text)
        cleaned_text = re.sub(r'\s+(")', r'\1', cleaned_text)
        cleaned_text = re.sub(r'\s+(\'\w+)', r'\1', cleaned_text)
        cleaned_text = re.sub(r'([.?!])(\w)', r'\1 \2', cleaned_text)
        cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text).strip()

        block_data_for_sorting.append({
            "speaker": speaker,
            "text": cleaned_text,
            "y_pos": y_position
        })

    block_data_for_sorting.sort(key=lambda msg: msg['y_pos'])
    structured_messages = [
        {
            "speaker": msg["speaker"], 
            "text": msg["text"],
            **({"unreadable": True} if msg.get("unreadable") else{})
        }
        for msg in block_data_for_sorting
    ]

    return structured_messages