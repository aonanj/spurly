from google.cloud import firestore
from datetime import datetime 
from uuid import uuid4
from gpt_training.anonymizer import anonymize_conversation
from infrastructure.clients import db
from infrastructure.logger import get_logger
from flask import current_app


logger = get_logger(__name__)

def save_conversation(user_id, data):
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return f"error - {err_point} - Error:", 400

    connection_id = data.get("connection_id", None)
    
    ocr_marker = current_app.config['OCR_MARKER']
    conversation_id = data.get("conversation_id")
    if not conversation_id:
        conversation_id = f"{user_id}:{str(uuid4().hex[:6])}"
    elif conversation_id.startswith(":") and conversation_id.endswith(ocr_marker):
        conversation_id = f"{user_id}{conversation_id}"
    else:
        conversation_id = f"{user_id}:{str(uuid4().hex[:6])}"
        
    spurs = data.get("spurs", None)
    situation = data.get("situation", "")
    topic = data.get("topic", "")
    
    try:
        doc_ref = db.collection("users").document(user_id).collection("conversations").document(conversation_id)

        doc_data = {
            "conversation_id": conversation_id,
            "conversation": data.get("conversation", []),
            "connection_id": data.get("connection_id", None),
            "situation": situation,
            "topic": topic,
            "spurs": spurs,
            "created_at": datetime.utcnow()
        }

        anonymize_conversation(
            data.get("conversation", []),
            data.get("user_profile", {}),
            data.get("connection_profile", {}),
            data.get("situation", ""),
            data.get("topic", "")
        )

        doc_ref.set(doc_data)
        return {"status": "conversation saved", "conversation_id": conversation_id}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return f"error - {err_point} - Error: {str(e)}", 500

def get_conversation(user_id, conversation_id):
    if not user_id or not conversation_id:
        return {"error": "Missing user_id or conversation_id"}, 400

    doc_ref = db.collection("users").document(user_id).collection("conversations").document(conversation_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return f"error - {err_point} - Error:", 404

def delete_conversation(user_id, conversation_id):
    if not user_id or not conversation_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return f"error - {err_point} - Error:", 400

    db.collection("users").document(user_id).collection("conversations").document(conversation_id).delete()
    return {"status": "conversation deleted"}

def get_conversations(user_id, filters=None):
    """
    searches for conversations based on filters. searches all of situation, topic, and conversation text.
     1. keyword: searches for keyword in situation, topic, and conversation text
     2. date_from: searches for conversations created after this date
     3. date_to: searches for conversations created before this date
     4. connection_id: searches for conversations with this connection_id
    
    """
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return f"error - [{err_point}] - Error:", 400

    try:
        ref = db.collection("users").document(user_id).collection("conversations")

        if filters:
            keyword = filters.get("keyword", "").lower()
            if "date_from" in filters:
                ref = ref.where("created_at", ">=", filters["date_from"])
            if "date_to" in filters:
                ref = ref.where("created_at", "<=", filters["date_to"])

        convos = ref.stream()
        grouped = {}

        for convo in convos:
            data = convo.to_dict()
            connection_id = data.get("connection_id", "(none)")

            if filters and keyword:
                in_topic = keyword in (data.get("topic", "").lower())
                in_situation = keyword in (data.get("situation", "").lower())
                in_convo_text = any(keyword in m.get("text", "").lower() for m in data.get("conversation", []))
                if not (in_topic or in_situation or in_convo_text):
                    continue  # Skip non-matches

            if connection_id not in grouped:
                grouped[connection_id] = []

            grouped[connection_id].append({
                "conversation_id": convo.id,
                "preview": data.get("conversation", [])[-1]["text"] if data.get("conversation") else "",
                "created_at": data.get("created_at"),
            })

        return grouped
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return f"error - {err_point} - Error: {str(e)}", 500