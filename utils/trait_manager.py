import openai
import json
from validation import classify_confidence
from services.clients import chat_client
from utils.logger import setup_logger

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
        response = chat_client.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        output = response.choices[0].message.content.strip()
        return json.loads(output)
    except Exception as e:
        logger = setup_logger(name="trait_manager_log.file", toFile=True, filename="trait_manager.log")
        logger.error("Situation inference error: %s", e)
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
        response = chat_client.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        output = response.choices[0].message.content.strip()
        return json.loads(output)
    except Exception as e:
        logger = setup_logger(name="trait_manager_log.file", toFile=True, filename="trait_manager.log")
        logger.error("Tone inference error: %s", e)
        return {"tone": "neutral", "confidence": 0.0}