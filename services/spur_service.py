from google.cloud import firestore
from datetime import datetime 
from gpt_training.anonymizer import anonymize_spur
from infrastructure.clients import db
from infrastructure.logger import get_logger


logger = get_logger(__name__)

def save_spur(user_id, spur):
    try:
        if not user_id:
            err_point = __package__ or __name__
            logger.error(f"error - {err_point} - No user_id in context")
            return f"error - {err_point} - No user_id in context"

        doc_ref = db.collection("users").document(user_id).collection("spurs").document()
        doc_ref.set({
            "text": spur.get("text", ""),
            "variant": spur.get("variant", ""),
            "situation": spur.get("situation", ""),
            "date_saved": datetime.utcnow()
        })

        return {"status": "spur saved", "spur_id": doc_ref.id}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return f"error: {err_point} - Error: {str(e)}", 500

def get_saved_spurs(user_id, filters=None):
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return f"error - {err_point} - Error:", 400
    try:
        ref = db.collection("users").document(user_id).collection("spurs")
        query = ref

        if filters:
            if "variant" in filters:
                query = query.where("variant", "==", filters["variant"])
            if "situation" in filters:
                query = query.where("situation", "==", filters["situation"])
            if "date_from" in filters:
                query = query.where("date_saved", ">=", filters["date_from"])
            if "date_to" in filters:
                query = query.where("date_saved", "<=", filters["date_to"])
            sort_order = filters.get("sort", "desc")
            direct = firestore.Query.ASCENDING if sort_order == "asc" else firestore.Query.DESCENDING
            query = query.order_by("date_saved", direction=direct)

        keyword = filters.get("keyword", "").lower() if filters else ""

        docs = query.stream()
        result = []
        for doc in docs:
            data = doc.to_dict()
            if keyword and keyword not in data.get("text", "").lower():
                continue  # Skip if keyword not in text

            result.append({
                "spur_id": doc.id,
                "variant": data.get("variant"),
                "text": data.get("text"),
                "situation": data.get("situation"),
                "date_saved": data.get("date_saved")
            })

        return result
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return f"error - {err_point} - Error: {str(e)}", 500


def delete_saved_spur(user_id, spur_id):
    if not user_id or not spur_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return f"error - {err_point} - Error:", 400

    try:
        doc_ref = db.collection("users").document(user_id).collection("spurs").document(spur_id)
        doc_ref.delete()
        return {"status": "spur deleted"}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return f"error - {err_point} - Error: {str(e)}", 500

def get_spur(user_id, spur_id):
    if not user_id or not spur_id:
        return {"error": "Missing user_id or spur_id"}, 400

    doc_ref = db.collection("users").document(user_id).collection("spurs").document(spur_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return f"error - {err_point} - Error:", 404

