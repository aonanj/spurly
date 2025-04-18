from class_defs.conversation_def import Conversation
from datetime import datetime, timezone, date, timedelta
from flask import g, current_app
from google.cloud import aiplatform, firestore
from google.cloud.aiplatform.matching_engine import MatchingEngineIndexEndpoint
from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import Namespace, N
from google.protobuf import struct_pb2
from gpt_training.anonymizer import anonymize_conversation
from infrastructure.clients import db
from infrastructure.id_generator import generate_conversation_id
from infrastructure.logger import get_logger
import openai



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

    user_id = g.user['user_id']
    connection_id = data.get("connection_id", None)
    
    if not user_id:
        logger.error("Error: Failed to save conversation - missing user_id", __name__)
        return {"error": "Missing user_ids"}, 400

    if not conversation_id:
        conversation_id = generate_conversation_id(user_id)
    elif conversation_id.startswith(":"):
        conversation_id = f"{user_id}{conversation_id}"

    spurs = data.get("spurs", None)
    situation = data.get("situation", "")
    topic = data.get("topic", "")
    conversation = get_conversation(conversation_id)
    conversation_text = Conversation.conversation_as_string(conversation)
    
    try:
        doc_ref = db.collection("users").document(user_id).collection("conversations").document(conversation_id)
        doc = doc_ref.get()
        if doc.exists:
            conversation = Conversation.from_dict(doc.to_dict())


        doc_data = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "conversation": conversation,
            "connection_id": connection_id,
            "situation": situation,
            "topic": topic,
            "spurs": spurs,
            "created_at": datetime.now(timezone.utc)
        }

        anonymize_conversation(Conversation.from_dict(doc_data))

        doc_ref.set(doc_data)
        return {"status": "conversation saved", "conversation_id": conversation_id}
    except firestore.ReadAfterWriteError as e:
        logger.error("[%s] Error: %s Save conversation failed", __name__, e)
        raise firestore.ReadAfterWriteError(f"Save conversation failed: {e}") from e
    except Exception as e:
        logger.error("[%s] Error: %s Save conversation failed", __name__, e)
        raise ValueError(f"Save conversation failed: {e}") from e
        

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
    
    user_id = g.user['user_id']
    
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

def delete_conversation(conversation_id: str) -> dict:
    """
    Deletes a conversation by the conversation_id.

    Args
        conversation_id: the unique id for the conversation requested to be deleted
            str
    Return
        status: confirmation string that conversation corresponding to the conversation_id is deleted
            dict

    """
    
    user_id = g.user['user_id']
    
    if not user_id or not conversation_id:
        logger.error("Error: Failed to get conversation - missing user_id or conversation_id ", __name__)
        return {"error": "Missing user_id or conversation_id"}, 400

    db.collection("users").document(user_id).collection("conversations").document(conversation_id).delete()
    #TODO Remove corresponding entries from Vector Search index
    return {"status": f"conversation_id {conversation_id} deleted"}


## TODO: Need to refactor the keyword search using Firebase, Vertex AI, Firestore.
def get_conversations(user_id, filters=None):
    """
    Searches for conversations based on filters. Uses Vertex AI Vector Search for keyword search
    and Firestore for date/connection_id filtering.

    Args
        user_id: user_id associated with the conversations being searched/sorted
            str
        filters: dict object of the search/sort criteria (keyword, date_from, date_to, connection_id, sort)
            dict

    Return
        List of conversation previews: Returns a list of conversation previews matching the criteria.
            List[dict]
    """
    if not user_id: #
        logger.error("Error: Failed to get conversations - missing user_id", __name__) #
        return {"error": "Missing user_id"}, 400 #

    if filters is None:
        filters = {}

        
    keyword = filters.get("keyword")
    connection_id_filter = filters.get("connection_id")
    from_date = filters.get("date_from") or datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    # Ensure to_date includes the whole day if it's just a date
    to_date_input = filters.get("date_to") or datetime.now(timezone.utc)
    if isinstance(to_date_input, date) and not isinstance(to_date_input, datetime):
         to_date = datetime.combine(to_date_input, datetime.max.time(), tzinfo=timezone.utc)
    else:
         # Add a small delta to ensure end of day is included if time is 00:00:00
         if to_date_input.time() == datetime.min.time().replace(tzinfo=timezone.utc):
              to_date = to_date_input + timedelta(days=1) - timedelta(microseconds=1)
         else:
              to_date = to_date_input


    sort_order = filters.get("sort", "desc")
    direct = firestore.Query.DESCENDING if sort_order == "desc" else firestore.Query.ASCENDING

    conversation_ids_to_fetch = []
    results_from_vector_search = False
    final_previews = []

    try:
        # --- If KEYWORD provided: Use Vector Search with filtering ---
   

        logger.info(f"Returning {len(final_previews)} conversation previews.")
        return final_previews

    except Exception as e:
        logger.error(f"[%s] Error: {e} Failed to get conversations for user_id {user_id}", __name__)
        # Add more specific error logging if possible
        if "aiplatform" in str(e).lower():
             logger.error("Underlying error likely related to Vertex AI call.")
        elif "firestore" in str(e).lower():
             logger.error("Underlying error likely related to Firestore call.")
        raise ValueError(f"Failed to get conversations for user_id {user_id}: {e}") from e
