from class_defs.conversation_def import Conversation
from datetime import datetime, timezone, timedelta
from flask import g, current_app
from google.cloud import firestore
from gpt_training.anonymizer import anonymize_conversation
from infrastructure.clients import db, get_algolia_client
from infrastructure.id_generator import generate_conversation_id
from infrastructure.logger import get_logger
import openai



logger = get_logger(__name__)

def save_conversation(data: Conversation) -> dict:
    
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
    conversation_id = data.conversation_id
    connection_id = data.connection_id
    
    if not user_id:
        logger.error("Error: Failed to save conversation - missing user_id", __name__)
        return {"error": "Missing user_ids"}

    if not conversation_id:
        conversation_id = generate_conversation_id(user_id)
    elif conversation_id.startswith(":"):
        conversation_id = f"{user_id}{conversation_id}"

    # Prepare data for Firestore, ensuring created_at is set
    created_time = data.created_at or datetime.now(timezone.utc)
    # Ensure created_at is a datetime object before conversion
    if isinstance(created_time, str):
        try:
            created_time = datetime.fromisoformat(created_time)
        except ValueError:
            logger.error(f"Invalid created_at format for {conversation_id}. Using current time.", exc_info=True)
            created_time = datetime.now(timezone.utc)

    spurs = data.spurs
    situation = data.situation
    topic = data.topic
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
            "created_at": created_time
        }

        anonymize_conversation(Conversation.from_dict(doc_data))

        doc_ref.set(doc_data)

        # --- Index in Algolia ---
        algolia_client = get_algolia_client()
        aloglia_conversations_index = current_app.config['ALGOLIA_CONVERSATIONS_INDEX']
        if algolia_client and conversation_text: # Only index if Algolia is available and text exists
            try:
                algolia_payload = {
                    "objectID": conversation_id,
                    "user_id": user_id,
                    "text": conversation_text,
                    # Ensure 'created_at' is a Unix timestamp for Algolia filtering/sorting
                    "created_at_timestamp": int(created_time.timestamp()),
                    # Include other filterable attributes if needed
                    "connection_id": connection_id,
                    "situation": situation,
                    "topic": topic,
                }
                # Remove None values if Algolia doesn't handle them well
                algolia_payload = {k: v for k, v in algolia_payload.items() if v is not None}

                res = algolia_client.save_object(aloglia_conversations_index, algolia_payload)
                algolia_client.wait_for_task(index_name=aloglia_conversations_index, task_id=res.task_id)
                logger.info(f"Successfully indexed conversation {conversation_id} in Algolia.")
            except Exception as algolia_error:
                logger.error(f"Failed to index conversation {conversation_id} in Algolia: {algolia_error}", exc_info=True)
                # Continue even if Algolia indexing fails
        
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
        raise RuntimeError("Error Missing user_id or conversation_id")

    doc_ref = db.collection("users").document(user_id).collection("conversations").document(conversation_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        logger.error(f"Error: no conversation exists with conversation_id {conversation_id}", __name__)
        raise RuntimeError("Error Missing user_id or conversation_id")

def delete_conversation(conversation_id: str) -> dict:
    """
    Deletes a conversation by the conversation_id from Firestore and Algolia.

    Args
        conversation_id: the unique id for the conversation requested to be deleted
            str
    Return
        status: confirmation string that conversation corresponding to the conversation_id is deleted
            dict

    """
    user_id = g.user['user_id']

    if not user_id:
        logger.error("Error: Could not extract user_id from conversation_id '%s' for deletion", conversation_id)
        return {"error": "Invalid conversation_id format"}

    if not conversation_id:
        logger.error("Error: Failed to delete conversation - missing conversation_id ", __name__)
        return {"error": "Missing conversation_id"}

    try:
        # --- Delete from Firestore ---
        db.collection("users").document(user_id).collection("conversations").document(conversation_id).delete()
        logger.info(f"Deleted conversation {conversation_id} from Firestore for user {user_id}.")

        # --- Delete from Algolia ---
        algolia_client = get_algolia_client()
        aloglia_conversations_index = current_app.config['ALGOLIA_CONVERSATIONS_INDEX']
        if algolia_client:
            try:
                res = algolia_client.delete_object(index_name=aloglia_conversations_index, object_id=conversation_id)
                algolia_client.wait_for_task(index_name=aloglia_conversations_index, task_id=res.task_id)
                logger.info(f"Deleted conversation {conversation_id} from Algolia index.")
            except Exception as algolia_error:
                # Log error but don't fail the whole operation if Algolia deletion fails
                logger.error(f"Failed to delete conversation {conversation_id} from Algolia: {algolia_error}", exc_info=True)

        return {"status": f"conversation_id {conversation_id} deleted"}

    except Exception as e:
         logger.error(f"Error deleting conversation {conversation_id} for user {user_id}: {e}", exc_info=True)
         raise ValueError(f"Failed to delete conversation {conversation_id}: {e}") from e


## TODO: Need to refactor the keyword search using Firebase, Vertex AI, Firestore.
def get_conversations(user_id: str, filters: dict) -> list[Conversation]:
    """
    Searches for conversations based on filters. Uses Algolia for keyword search
    and Firestore for retrieval and other filtering.

    Args:
        user_id (str): User ID associated with the conversations.
        filters (dict, optional): Search/sort criteria (keyword, date_from, date_to, connection_id, sort). Defaults to None.
        limit (int, optional): Maximum number of conversations to return. Defaults to 20.

    Returns:
        list[Conversation]: A list of Conversation objects matching the criteria.
    """
    if not user_id:
        logger.error("Error: Failed to get conversations - missing user_id", __name__)
        return [] # Return empty list on error

    if filters is None:
        filters = {}

    keyword = filters.get("keyword")
    algolia_client = get_algolia_client()
    aloglia_conversations_index = current_app.config['ALGOLIA_CONVERSATIONS_INDEX']
    aloglia_search_results_limit = current_app.config['ALGOLIA_SEARCH_RESULTS_LIMIT']

    try:
        # --- Use Algolia if keyword is present and client is available ---
        if keyword and algolia_client:
            logger.info(f"Performing Algolia keyword search for user '{user_id}' with keyword: '{keyword}'")

            # Define Algolia search parameters
            search_params = {
                "query": keyword,
                "filters": f"user_id:{user_id}", # Filter by user_id in Algolia
                "hitsPerPage": aloglia_search_results_limit * 5, # Fetch more IDs initially in case some are filtered out later
                "attributesToRetrieve": ["objectID"], # Only need the IDs from Algolia
            }

            # Add connection_id filter if provided
            connection_id_filter = filters.get("connection_id")
            if connection_id_filter:
                search_params["filters"] += f" AND connection_id:{connection_id_filter}"

            # Add date filters (requires timestamp attribute in Algolia)
            # Assuming 'created_at_timestamp' exists in your Algolia records
            date_filter_parts = []
            if "date_from" in filters and isinstance(filters["date_from"], datetime):
                date_filter_parts.append(f"created_at_timestamp >= {int(filters['date_from'].timestamp())}")
            if "date_to" in filters and isinstance(filters["date_to"], datetime):
                 # Adjust to_date to include the full day
                 to_date = filters["date_to"]
                 if to_date.time() == datetime.min.time(): # If time is midnight, include the whole day
                     to_date = to_date + timedelta(days=1) - timedelta(microseconds=1)
                 date_filter_parts.append(f"created_at_timestamp <= {int(to_date.timestamp())}")

            if date_filter_parts:
                 search_params["filters"] += " AND " + " AND ".join(date_filter_parts)


            # Perform the search
            res = algolia_client.search(
                        {
                            "requests": [
                                {
                                    "indexName": aloglia_conversations_index,
                                    "query": search_params
                                }
                            ]
                        })
            conversation_ids = []
            for key, convo_id in res.to_dict():
                conversation_ids.append(convo_id)
            
            if not conversation_ids:
                logger.info(f"No Algolia hits found for keyword '{keyword}' for user '{user_id}'.")
                return []

            logger.info(f"Found {len(res.results)} potential matches in Algolia for keyword '{keyword}'. Fetching from Firestore.")

            # Fetch conversations from Firestore using the IDs from Algolia
            # Firestore 'in' queries support up to 30 elements per query part. Split if necessary.
            # Note: Firestore 'in' query doesn't preserve order from the list. We re-sort later.
            conversation_docs = []
            # Split IDs into chunks for Firestore 'in' query limit (typically 30, but use 10 for safety)
            id_chunks = [conversation_ids[i:i + 10] for i in range(0, len(conversation_ids), 10)]

            for chunk in id_chunks:
                if not chunk: continue
                query = db.collection("users").document(user_id).collection("conversations").where("conversation_id", "in", chunk)
                docs = query.stream()
                conversation_docs.extend([doc.to_dict() for doc in docs])


            # Convert to Conversation objects and filter out potential misses
            convos_map = {convo_data['conversation_id']: Conversation.from_dict(convo_data)
                          for convo_data in conversation_docs if convo_data}

            # Re-order based on Algolia's ranking and apply limit
            ordered_convos = [convos_map[cid] for cid in conversation_ids if cid in convos_map][:aloglia_search_results_limit]

            logger.info(f"Returning {len(ordered_convos)} conversations after keyword search and Firestore fetch.")
            return ordered_convos

        # --- Fallback: No keyword or Algolia unavailable - Use Firestore query ---
        else:
            logger.info(f"No keyword provided or Algolia unavailable. Performing Firestore query for user '{user_id}'.")
            query = db.collection("users").document(user_id).collection("conversations")

            # Apply Firestore filters
            connection_id_filter = filters.get("connection_id")
            if connection_id_filter:
                query = query.where("connection_id", "==", connection_id_filter)

            # Date filtering requires ordering by date first
            sort_field = "created_at" # Assuming you want to sort/filter by creation date
            sort_order_str = filters.get("sort", "desc")
            sort_direction = firestore.Query.DESCENDING if sort_order_str == "desc" else firestore.Query.ASCENDING

            # Apply date range filters
            if "date_from" in filters and isinstance(filters["date_from"], datetime):
                 query = query.where(sort_field, ">=", filters["date_from"])
            if "date_to" in filters and isinstance(filters["date_to"], datetime):
                 # Adjust to_date to include the full day
                 to_date = filters["date_to"]
                 if to_date.time() == datetime.min.time():
                      to_date = to_date + timedelta(days=1) - timedelta(microseconds=1)
                 query = query.where(sort_field, "<=", to_date)


            # Apply sorting and limit
            query = query.order_by(sort_field, direction=sort_direction).limit(aloglia_search_results_limit)

            docs = query.stream()
            firestore_convos = [Conversation.from_dict(doc.to_dict()) for doc in docs]

            logger.info(f"Returning {len(firestore_convos)} conversations from Firestore query.")
            return firestore_convos

    except Exception as e:
        logger.error(f"[%s] Error: {e} Failed to get conversations for user_id {user_id}", __name__, exc_info=True)
        # Add more specific error logging if possible
        if "algolia" in str(e).lower():
             logger.error("Underlying error likely related to Algolia call.")
        elif "firestore" in str(e).lower():
             logger.error("Underlying error likely related to Firestore call.")
        return [] # Return empty list on error