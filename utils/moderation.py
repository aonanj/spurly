import re
import openai
from services.clients import mod_client
from .logger import setup_logger

# Static hard-block list (expandable)
BANNED_PHRASES = [
    "kill yourself", "go die", "white power", "lynch", 
    " fag", " faggot", "nigger", "darkie", "slant eyed", "wetback"
]

GIBBERISH_PATTERN = re.compile(r"[^a-zA-Z0-9\s,.!?()'\"-]{3,}")
TOO_MUCH_EMOJI = re.compile(r"[\U0001F600-\U0001F64F]{3,}")

def moderate_topic(text: str) -> dict:
    """
    Evaluates a quick topic string for safety.
    Returns a dict with `safe: bool` and optionally `reason: str`.
    """
    if not text or not isinstance(text, str):
        return {"safe": False, "reason": "invalid_or_blank"}

    normalized = text.strip().lower()

    # Check static banned list
    for phrase in BANNED_PHRASES:
        if phrase in normalized:
            return {"safe": False, "reason": "banned_phrase"}

    # Check gibberish / emoji spam
    if GIBBERISH_PATTERN.search(text) or TOO_MUCH_EMOJI.search(text):
        return {"safe": False, "reason": "gibberish_or_emoji"}

    # ✅ (Optional): Plug in ML moderation here later
    # if classifier_score(text) > threshold:
    #     return {"safe": False, "reason": "ml_flagged"}

    return {"safe": True}

def moderate_with_openai(text):
    try:
        response = mod_client.create(input=text)
        flagged = response["results"][0]["flagged"]
        return {"safe": True} if not flagged else {"safe": False, "reason": "openai_moderation"}  
    except Exception as e:
        logger = setup_logger(name="moderation_log.file", toFile=True, filename="moderation.log")
        logger.error("tils.moderation.moderate_with_openai error: %s", e)