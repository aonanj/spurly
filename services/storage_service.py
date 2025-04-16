from class_defs.conversation_def import Conversation
from datetime import datetime, timezone, timedelta, date
from flask import current_app
from google.cloud import firestore
from gpt_training.anonymizer import anonymize_conversation
from infrastructure.clients import db
from infrastructure.id_generator import generate_conversation_id, extract_user_id_from_other_id
from infrastructure.logger import get_logger
from uuid import uuid4


logger = get_logger(__name__)

def save_conversation(data: Conversation) -> str:
    
    """
    Saves a conversation with the conversation_id.

    Args
        data: the conversation data associated with the active user to be saved
            Conversation 

    Return
        status: indicates if conversation is saved
            str

    """

    user_id = data.get("user_id", None)
    connection_id = data.get("connection_id", None)
    
    if not user_id:
        logger.error("Error: Failed to save conversation - missing user_id", __name__)
        return {"error": "Missing user_ids"}, 400

    if not conversation_id:
        conversation_id = generate_conversation_id(user_id)
    elif conversation_id.startswith(":"):
        conversation_id = f"{user_id}{conversation_id}"
    else:
        conversation_id = generate_conversation_id(user_id)
        
    spurs = data.get("spurs", None)
    situation = data.get("situation", "")
    topic = data.get("topic", "")
    
    try:
        doc_ref = db.collection("users").document(user_id).collection("conversations").document(conversation_id)

        doc_data = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "conversation": data.get("conversation", []),
            "connection_id": connection_id,
            "situation": situation,
            "topic": topic,
            "spurs": spurs,
            "created_at": datetime.utcnow()
        }

        anonymize_conversation(Conversation.from_dict(doc_data))

        doc_ref.set(doc_data)
        return {"status": "conversation saved", "conversation_id": conversation_id}
    except Exception as e:
        logger.error("[%s] Error: %s Anonymizing conversation failed", __name__, e)
        raise ValueError(f"Anonymizing conversation failed: {e}") from e
        

def get_conversation(conversation_id: str) -> Conversation:
    """
    Gets a conversation by the conversation_id.

    Args
        conversation_id: the unique id for the conversation requested
            str
    Return
        conversation corresponding to the conversation_id
            Conversation object

    """
    
    user_id = extract_user_id_from_other_id(conversation_id)
    
    if not user_id or not conversation_id:
        logger.error("Error: Failed to get conversation - missing user_id or conversation_id ", __name__)
        return {"error": "Missing user_id or conversation_id"}, 400

    doc_ref = db.collection("users").document(user_id).collection("conversations").document(conversation_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        logger.error(f"Error: no conversation exists with conversation_id {conversation_id}", __name__)
        return None

def delete_conversation(conversation_id: str) -> str:
    """
    Deletes a conversation by the conversation_id.

    Args
        conversation_id: the unique id for the conversation requested to be deleted
            str
    Return
        status: confirmation string that conversation corresponding to the conversation_id is deleted
            str

    """
    
    user_id = extract_user_id_from_other_id(conversation_id)
    
    if not user_id or not conversation_id:
        logger.error("Error: Failed to get conversation - missing user_id or conversation_id ", __name__)
        return {"error": "Missing user_id or conversation_id"}, 400

    db.collection("users").document(user_id).collection("conversations").document(conversation_id).delete()
    return {f"status: conversation_id {conversation_id} deleted"}

## TODO: Need to refactor the keyword search using Firebase, Vertex AI, Firestore.
def get_conversations(user_id, filters=None):
    """
    searches for conversations based on filters. searches all of situation, topic, and conversation text.
     1. keyword: searches for keyword in situation, topic, and conversation text
     2. date_from: searches for conversations created after this date
     3. date_to: searches for conversations created before this date
     4. connection_id: searches for conversations with this connection_id

    Args
        user_id: user_id associated with the conversations being searched/sorted
            str
        filters: dict object of the search/sort criteria

    Return
        List of conversation previews: Returns a list of conversation previews matching the search/sort criteria, grouped by connection_id
            List[dict]
    
    """
    if not user_id:
        logger.error("Error: Failed to get conversation - missing user_id or conversation_id ", __name__)
        return {"error": "Missing user_id or conversation_id"}, 400

    try:
        ref = db.collection("users").document(user_id).collection("conversations")

        from_date = filters["date_from"] if filters["date_from"] else datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        to_date = filters["to_date"] if filters["to_date"] else date.today()
        sort_order = filters.get("sort", "desc")

        query = ref.where('created_at', '>=', from_date).where('created_at', '<=', to_date)
        direct = firestore.Query.ASCENDING if sort_order == "asc" else firestore.Query.DESCENDING
        query = query.order_by('created_at', direction=direct)

        convos = ref.stream()
        grouped = {}
        keyword = filters["keyword"]
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
        logger.error(f"[%s] Error: %s Failed to get conversations for user_id {user_id}", __name__, e)
        raise ValueError(f"Failed to get conversations for user_id {user_id}: {e}")