from flask import current_app
from infrastructure.clients import get_openai_client
from infrastructure.logger import get_logger
from utils.prompt_loader import get_system_prompt
import json
import openai


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
        system_prompt = get_system_prompt()

        chat_client=get_openai_client()
        response = chat_client.chat.completions.create(
            model=current_app.config['AI_MODEL'],
            messages=[
                {"role": current_app.config['AI_MESSAGES_ROLE_SYSTEM'], "content": system_prompt},
                {"role": current_app.config['AI_MESSAGES_ROLE_USER'], "content": prompt}
                ], temperature=current_app.config['AI_TEMPERATURE_RETRY'],
        )
        output = response.choices[0].message.content.strip()
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
        output = response.choices[0].message.content.strip()
        return json.loads(output)
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return {"tone": "neutral", "confidence": 0.0}