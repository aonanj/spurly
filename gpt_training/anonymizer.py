from datetime import datetime
from uuid import uuid4
from infrastructure.clients import db
from infrastructure.logger import get_logger
from flask import current_app
from class_defs.conversation_def import Conversation

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
            logger.error("Invalid conversation format. List of messages expected.")
            raise TypeError("Invalid conversation format. List of messages expected.")
        elif user_profile is None or not isinstance(user_profile, dict):
            logger.error("Invalid user profile format. Dictionary expected.")
            raise TypeError("Invalid user profile format. Dictionary expected.")
        elif connection_profile is None or not isinstance(connection_profile, dict):
            logger.error("Invalid connection profile format. Dictionary expected.")   
            raise TypeError("Invalid connection profile format. Dictionary expected.")   

        if not all("text" in message and "speaker" in message for message in convo):
            logger.error("Invalid conversation format. Keys 'text' and 'speaker' expected.")
            raise ValueError("Invalid conversation format. Keys 'text' and 'speaker' expected.")
        
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
        save_anonymized_conversation(anonymized_messages, situation, topic)
    except Exception as e:
        logger.error("[%s] Error: %s Anonymizing conversation failed", __name__, e)
        raise ValueError(f"Anonymizing conversation failed: {e}") from e

    return True

def save_anonymized_conversation(convo, situation="", topic=""):
    """
    Saves an anonymized conversation for training the AI model underlying the app.

    Args:
        Convo (list[dict]): List of dictionaries (messages) in the conversation. JSON format.
        situation (str): Situation description.
        topic (str): Topic description.

    Returns:
        True if anonymoized conversation is saved.
    """
    
    anonymized_conversation_id = str(f"ac{uuid4().hex[:12]}")
    try:
        training_ref = db.collection("training").document("conversations").collection("batch").document()
        
        training_ref.set({
            "anonymized_conversation_id": anonymized_conversation_id,
            "anonymized_conversation": convo,
            "situation": situation,
            "topic": topic,
            "created_at": datetime.utcnow(),
        })
        return True
    except Exception as e:
        logger.error("[%s] Error: %s Save anonymized conversation failed", __name__, e)
        raise ValueError(f"Save anonymized conversation failed: {e}") from e
