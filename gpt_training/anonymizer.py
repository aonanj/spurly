from datetime import datetime
import uuid
from infrastructure.clients import db
from infrastructure.logger import get_logger
from flask import current_app

logger = get_logger(__name__)

def anonymize_conversation(convo, user_profile=None, connection_profile=None, situation="", topic=""):
    """
    Replaces speaker labels with generic gender-based labels when available,
    or falls back to 'Person A' and 'Person B' for user and connection respectively.
    Maintains message order and speaker attribution.

    Args:
        Convo (list[dict]): List of dictionaries (messages) in the conversation. JSON format.
        user_profile (dict): User profile containing user information.
        connection_profile (dict): connection profile containing connection information.
        situation (str): Situation description.
        topic (str): Topic description.

    Returns:
        True if anonymoized conversation is saved.
    """
    try:
        if not convo or not isinstance(convo, list):
            raise ValueError("Invalid conversation format. Expected a list of messages.")
        elif user_profile is None or not isinstance(user_profile, dict):
            raise ValueError("Invalid user profile format. Expected a dictionary.")
        elif connection_profile is None or not isinstance(connection_profile, dict):
            raise ValueError("Invalid connection profile format. Expected a dictionary.")   

        if not all("text" in message and "speaker" in message for message in convo):
            raise ValueError("Invalid conversation format. Each message must contain 'text' and 'speaker' keys.")
        
        if not isinstance(user_profile.get("gender"), str):
            user_label = "Person A"
        else:
            user_label = f"{user_profile.get('gender').capitalize()} Speaker"

        if not isinstance(connection_profile.get("gender"), str):
            connection_label = "Person B"
        else:
            connection_label = f"{connection_profile.get('gender').capitalize()} Speaker"

        anonymized_messages = []
        for message in convo:
            original_speaker = message.get("speaker", "").lower()
            text = message.get("text", "")

            if original_speaker == "user":
                speaker_label = user_label
            elif original_speaker == "connection":
                speaker_label = connection_label
            else:
                speaker_label = "Unknown"

            anonymized_messages.append({
                "speaker": speaker_label,
                "text": text
            })
        save_conversation(anonymized_messages, situation, topic)
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error anonymizing conversation: %s", err_point, e)
        raise Exception(f"[{err_point}] - Error anonymizing conversation: {str(e)}")

    return True

def save_conversation(convo, situation="", topic=""):

    conversation_id = str(uuid.uuid4())
    try:
        training_ref = db.collection("training").document("conversations").collection("batch").document()
        
        training_ref.set({
            "conversation_id": conversation_id,
            "anonymized_conversation": convo,
            "situation": situation,
            "topic": topic,
            "created_at": datetime.utcnow(),
        })
        return True
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error anonymizing conversation: %s", err_point, e)
        raise Exception(f"[{err_point}] - Error anonymizing conversation: {str(e)}")
