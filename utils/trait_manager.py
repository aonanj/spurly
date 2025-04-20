from flask import current_app
from infrastructure.clients import get_openai_client
from infrastructure.logger import get_logger
from utils.prompt_loader import load_system_prompt
import json
import openai
import base64
import os
from typing import List, Dict


logger = get_logger(__name__)

def infer_situation(conversation):
    """
    Uses GPT to infer the messaging situation from a list of conversation turns.

    Args:
        conversation (list): [{"speaker": "user"|"other", "text": "..."}, ...]

    Returns:
        dict: {"situation": "cta_setup", "confidence": 0.89}
    """

    prompt = f"""You're a messaging assistant. Analyze the situation of the conversation below.
Respond ONLY with a JSON object like this:
{{"situation": "cta_setup", "confidence": 0.85}}

Valid situations:
- cold_open
- recovery
- follow_up_no_response
- cta_setup
- cta_response
- message_refinement
- topic_pivot
- re_engagement

Conversation:
{json.dumps(conversation, indent=2)}
"""

    try:
        system_prompt = load_system_prompt()
        chat_client=get_openai_client()
        response = chat_client.chat.completions.create(
            model=current_app.config['AI_MODEL'],
            messages=[
                {"role": current_app.config['AI_MESSAGES_ROLE_SYSTEM'], "content": system_prompt},
                {"role": current_app.config['AI_MESSAGES_ROLE_USER'], "content": prompt}
                ], temperature=current_app.config['AI_TEMPERATURE_RETRY'],
        )

        output = (response.choices[0].message.content or "").strip()
        return json.loads(output)
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return {"situation": "cold_open", "confidence": 0.0}


def infer_tone(message):
    """
    Uses GPT to infer the tone of a single message with a confidence score.

    Args:
        message (str): The message to analyze.

    Returns:
        dict: {"tone": "warm", "confidence": 0.82}
    """
    prompt = f"""Analyze the tone of the message below. Respond only with a JSON object like:
{{"tone": "playful", "confidence": 0.84}}

Message:
{message}"""

    try:
        chat_client = get_openai_client()
        response = chat_client.chat.completions.create(
            model=current_app.config['AI_MODEL'],
            messages=[{"role": current_app.config['AI_MESSAGES_ROLE_USER'], "content": prompt}], temperature=current_app.config['AI_TEMPERATURE_RETRY'],
        )
        output = (response.choices[0].message.content or "").strip()
        return json.loads(output)
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return {"tone": "neutral", "confidence": 0.0}

def infer_personality_traits_from_pics(image_data: List[bytes]) -> List[Dict[str, float]]:
    """
    Infer personality traits from one or more pictures of a connection.

    Expected callers:
        - create_connection()
        - update_connection()

    Args:
        image_data (List[bytes]): A list of raw image byte blobs (e.g., JPEG/PNG)
            for the connection whose personality traits we want to infer.

    Returns:
        List[Dict[str, float]]: A mapping from inferred personality trait names
            to confidence scores (0.0–1.0).
    """
    # 1) Base64‑encode each image so it can be sent in a text prompt
    encoded_imgs = [base64.b64encode(img).decode("utf-8") for img in image_data]

    # 2) Build a prompt asking the model to analyze the images
    prompt_file = os.path.join(current_app.root_path, 'resources', 'spurly_inference_intro_prompt.txt')
    with open(prompt_file, 'r') as f:
        prompt_template = f.read().strip()
    image_prompt_appendix = "\nThe following images are Base64-ended. There is one person commonly shown in all images. You should infer personality traits about that one person. "
    f"\n\nImages: \n{json.dumps(encoded_imgs)}"
    prompt = prompt_template.join(image_prompt_appendix)

    # 3) Call the OpenAI ChatCompletion API
    chat_client = get_openai_client()
    resp = chat_client.chat.completions.create(
        model=current_app.config['AI_MODEL'], 
        messages=[{"role": current_app.config['AI_MESSAGES_ROLE_USER'], "content": prompt}], 
        temperature=current_app.config['AI_TEMPERATURE_RETRY'],
    )
    

    # 4) Parse the JSON response
    content = (resp.choices[0].message.content or "").strip()
    traits: List[Dict[str, float]] = json.loads(content)
    return traits


def infer_personality_traits_from_links(
    links: List[str]
) -> List[Dict[str, float]]:
    """
    Infer personality traits from a connection's social media profiles.

    Expected callers:
        - create_connection()
        - update_connection()

    Args:
        links (List[str]): A list of social media profile URLs (e.g., Facebook,
            Instagram, LinkedIn) for the connection.

    Returns:
        List[Dict[str, float]]: A mapping from inferred personality trait names
            to confidence scores (0.0–1.0).
    """
    # 1) Build a prompt asking the model to analyze the profile URLs.
    prompt_file = os.path.join(current_app.root_path, 'resources', 'spurly_inference_intro_prompt.txt')
    with open(prompt_file, 'r') as f:
        prompt_template = f.read().strip()
    links_prompt_appendix = "\nThe following URLs are all associated with the same person. You should visit each of the URLs and review the available images, posts, text, and other accessible information. You should infer personality traits about that person. "
    f"\n\nURLs: \n{json.dumps(links)}"
    prompt = prompt_template.join(links_prompt_appendix)

    # 2) Call the OpenAI ChatCompletion API
    chat_client = get_openai_client()
    resp = chat_client.chat.completions.create(
        model=current_app.config['AI_MODEL'], 
        messages=[{"role": current_app.config['AI_MESSAGES_ROLE_USER'], "content": prompt}], 
        temperature=current_app.config['AI_TEMPERATURE_RETRY'],
    )

    # 3) Parse the JSON response
    content = (resp.choices[0].message.content or "").strip()
    traits: List[Dict[str, float]] = json.loads(content)
    return traits