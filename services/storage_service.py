from google.cloud import firestore
from datetime import datetime 
import uuid
from gpt_training.anonymizer import anonymize_conversation
from clients import db
from utils.logger import setup_logger


def save_message(user_id, message):
    try:
        if not user_id:
            return {"error": "Missing user_id"}, 400

        doc_ref = db.collection("users").document(user_id).collection("messages").document()
        doc_ref.set({
            "text": message.get("text", ""),
            "variant": message.get("variant", ""),
            "situation": message.get("situation", ""),
            "date_saved": datetime.utcnow()
        })

        return {"status": "message saved", "message_id": doc_ref.id}
    except Exception as e:
        logger = setup_logger(name="storage_service_log.file", toFile=True, filename="storage_service.log")
        logger.error("Error in services.storage_service.save_message: %s", e)
        return {"error": str(e)}, 500

def get_saved_messages(user_id, filters=None):
    if not user_id:
        logger = setup_logger(name="storage_service_log.file", toFile=True, filename="storage_service.log")
        logger.error("Missing user_id in services.storage_service.get_saved_messages: %s", e)
        return {"error": "Missing user_id"}, 400
    try:
        ref = db.collection("users").document(user_id).collection("messages")

        if filters:
            if "variant" in filters:
                ref = ref.where("variant", "==", filters["variant"])
            if "situation" in filters:
                ref = ref.where("situation", "==", filters["situation"])
            if "date_from" in filters:
                ref = ref.where("date_saved", ">=", filters["date_from"])
            if "date_to" in filters:
                ref = ref.where("date_saved", "<=", filters["date_to"])
            sort_order = filters.get("sort", "desc")
            ref = ref.order_by("date_saved", direction=firestore.Query.ASCENDING if sort_order == "asc" else firestore.Query.DESCENDING)

        keyword = filters.get("keyword", "").lower() if filters else ""

        docs = ref.stream()
        result = []
        for doc in docs:
            data = doc.to_dict()
            if keyword and keyword not in data.get("text", "").lower():
                continue  # Skip if keyword not in text

            result.append({
                "message_id": doc.id,
                "variant": data.get("variant"),
                "text": data.get("text"),
                "situation": data.get("situation"),
                "date_saved": data.get("date_saved")
            })

        return result
    except Exception as e:
        logger = setup_logger(name="storage_service_log.file", toFile=True, filename="storage_service.log")
        logger.error("Error in services.storage_service.get_saved_messages: %s", e)
        return {"error": str(e)}, 500


def save_conversation(user_id, data):
    if not user_id:
        logger = setup_logger(name="conversation_log.file", toFile=True, filename="conversation.log")
        logger.error("Missing user_id in /conversations route: save_conversation")
        return {"error": "Missing user_id"}, 400

    cid = data.get("cid")
    if not cid or not cid.startswith(f"{user_id}:"):
        logger = setup_logger(name="conversation_log.file", toFile=True, filename="conversation.log")
        logger.error("Missing cid in /conversations route: save_conversation")
        return {"error": "Invalid or missing cid"}, 400

    try:
        conversation_id = str(uuid.uuid4())
        doc_ref = db.collection("users").document(user_id).collection("conversations").document(conversation_id)

        doc_data = {
            "cid": cid,
            "conversation": data.get("conversation", []),
            "cid": data.get("cid", None),
            "situation": data.get("situation", ""),
            "topic": data.get("topic", ""),
            "spurs": data.get("spurs", {}),
            "created_at": datetime.utcnow()
        }

        anonymize_conversation(
            data.get("conversation", []),
            data.get("user_sketch", {}),
            data.get("poi_sketch", {}),
            data.get("situation", ""),
            data.get("topic", "")
        )

        doc_ref.set(doc_data)
        return {"status": "conversation saved", "conversation_id": conversation_id}
    except Exception as e:
        logger = setup_logger(name="storage_service_log.file", toFile=True, filename="storage_service.log")
        logger.error("Error in services.storage_service.save_conversation: %s", e)
        return {"error": str(e)}, 500

def get_conversation(user_id, conversation_id):
    if not user_id or not conversation_id:
        return {"error": "Missing user_id or conversation_id"}, 400

    doc_ref = db.collection("users").document(user_id).collection("conversations").document(conversation_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        logger = setup_logger(name="storage_service_log.file", toFile=True, filename="storage_service.log")
        logger.error("Error in services.storage_service.get_conversation")
        return {"error": "Conversation not found"}, 404

def delete_conversation(user_id, conversation_id):
    if not user_id or not conversation_id:
        logger = setup_logger(name="storage_service_log.file", toFile=True, filename="storage_service.log")
        logger.error("Error in services.storage_service.delete_conversation: Missing ID")
        return {"error": "Missing user_id or conversation_id"}, 400

    db.collection("users").document(user_id).collection("conversations").document(conversation_id).delete()
    return {"status": "conversation deleted"}

def delete_saved_message(user_id, message_id):
    if not user_id or not message_id:
        logger = setup_logger(name="storage_service_log.file", toFile=True, filename="storage_service.log")
        logger.error("Error in services.storage_service.delete_saved_message: Missing ID")
        return {"error": "Missing user_id or message_id"}, 400

    try:
        doc_ref = db.collection("users").document(user_id).collection("messages").document(message_id)
        doc_ref.delete()
        return {"status": "message deleted"}
    except Exception as e:
        logger = setup_logger(name="storage_service_log.file", toFile=True, filename="storage_service.log")
        logger.error("Error in services.storage_service.delete_conversation: %s", e)
        return {"error": str(e)}, 500

def get_conversations(user_id, filters=None):
    """
    searches for conversations based on filters. searches all of situation, topic, and conversation text.
     1. keyword: searches for keyword in situation, topic, and conversation text
     2. date_from: searches for conversations created after this date
     3. date_to: searches for conversations created before this date
     4. cid: searches for conversations with this cid
    
    """
    if not user_id:
        return {"error": "Missing user_id"}, 400

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
            cid = data.get("cid", "(none)")

            if filters and keyword:
                in_topic = keyword in (data.get("topic", "").lower())
                in_situation = keyword in (data.get("situation", "").lower())
                in_convo_text = any(keyword in m.get("text", "").lower() for m in data.get("conversation", []))
                if not (in_topic or in_situation or in_convo_text):
                    continue  # Skip non-matches

            if cid not in grouped:
                grouped[cid] = []

            grouped[cid].append({
                "conversation_id": convo.id,
                "preview": data.get("conversation", [])[-1]["text"] if data.get("conversation") else "",
                "created_at": data.get("created_at"),
            })

        return grouped
    except Exception as e:
        logger = setup_logger(name="storage_service_log.file", toFile=True, filename="storage_service.log")
        logger.error("Error in services.storage_service.get_conversations: %s", e)
        return {"error": str(e)}, 500