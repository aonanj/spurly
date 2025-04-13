from datetime import datetime
import uuid
from services.clients import db
from utils.logger import setup_logger


def anonymize_conversation(convo, user_sketch=None, poi_sketch=None, situation="", topic=""):
    """
    Replaces speaker labels with generic gender-based labels when available,
    or falls back to 'Person A' and 'Person B' for user and POI respectively.
    Maintains message order and speaker attribution.

    Args:
        Convo (list[dict]): List of dictionaries (messages) in the conversation. JSON format.
        user_sketch (dict): User sketch containing user information.
        poi_sketch (dict): POI sketch containing POI information.
        situation (str): Situation description.
        topic (str): Topic description.

    Returns:
        True if anonymoized conversation is saved.
    """
    try:
        if not convo or not isinstance(convo, list):
            raise ValueError("Invalid conversation format. Expected a list of messages.")
        elif user_sketch is None or not isinstance(user_sketch, dict):
            raise ValueError("Invalid user sketch format. Expected a dictionary.")
        elif poi_sketch is None or not isinstance(poi_sketch, dict):
            raise ValueError("Invalid POI sketch format. Expected a dictionary.")   

        if not all("text" in message and "speaker" in message for message in convo):
            raise ValueError("Invalid conversation format. Each message must contain 'text' and 'speaker' keys.")
        
        if not isinstance(user_sketch.get("gender"), str):
            user_label = "Person A"
        else:
            user_label = f"{user_sketch.get("gender").capitalize()} Speaker"

        if not isinstance(poi_sketch.get("gender"), str):
            poi_label = "Person B"
        else:
            poi_label = f"{poi_sketch.get("gender").capitalize()} Speaker"

        anonymized_messages = []
        for message in convo:
            original_speaker = message.get("speaker", "").lower()
            text = message.get("text", "")

            if original_speaker == "user":
                speaker_label = user_label
            elif original_speaker == "poi":
                speaker_label = poi_label
            else:
                speaker_label = "Unknown"

            anonymized_messages.append({
                "speaker": speaker_label,
                "text": text
            })
        save_conversation(anonymized_messages, situation, topic)
    except Exception as e:
        logger = setup_logger(name="anonymizer_log.file", toFile=True, filename="anonymizer.log")
        logger.error("Error anonymizing conversation: %s", e)
        raise Exception(f"Error anonymizing conversation: {str(e)}")

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
        logger = setup_logger(name="anonymizer_log.file", toFile=True, filename="anonymizer.log")
        logger.error("Error anonymizing conversation: %s", e)
        raise Exception(f"Error anonymizing conversation: {str(e)}")
