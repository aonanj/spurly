from infrastructure.clients import db
from uuid import uuid4
from flask import current_app
from infrastructure.logger import get_logger
from flask import jsonify
from class_defs.profile_def import ConnectionProfile
from dataclasses import fields

logger = get_logger(__name__)

def create_connection_profile(data):
    user_id = data.get("user_id")
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return False

    profile = ConnectionProfile.from_dict(data)
    short_id = str(uuid4().hex[:5])
    connection_id = f"{user_id}:{short_id}"
    profile_data = profile.to_dict()
    profile_data["connection_id"] = connection_id

    try:
        db.collection("users").document(user_id).collection("connections").document(connection_id).set(profile_data)
        return {
            "status": "connection profile created",
            "connection_id": connection_id,
            "connection_profile": format_connection_profile(connection_id, profile_data)
        }
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return False

def format_connection_profile(connection_id, profile_data):
    """
    Converts a ConnectionProfile object into a formatted string for human-readable display.

    Args:
        connection_id (str): The unique ID of the connection.
        profile_data (dict): Dictionary representation of the ConnectionProfile.

    Returns:
        str: A multiline formatted string summarizing the profile contents.
    """
    profile = ConnectionProfile.from_dict(profile_data)
    lines = [f"connection_id: {connection_id}"]

    for field in fields(ConnectionProfile):
        key = field.name
        value = getattr(profile, key)

        if key == "user_id" or value is None:
            continue

        if isinstance(value, list):
            if value:
                label = "Greenlight Topics" if key == "greenlights" else (
                        "Redlight Topics" if key == "redlights" else key.capitalize())
                lines.append(f"{label}: {', '.join(value)}")
        else:
            lines.append(f"{key.capitalize()}: {value}")

    return "\n".join(lines)

def save_connection_profile(data):
    user_id = data.get("user_id")
    connection_id = data.get("connection_id")
    if not user_id or not connection_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400

    profile = ConnectionProfile.from_dict(data)
    profile_data = profile.to_dict()
    try:
        db.collection("users").document(user_id).collection("connections").document(connection_id).set(profile_data)
        return {"status": "connection profile saved"}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500

def get_user_connections(user_id):
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400

    try:
        connections_ref = db.collection("users").document(user_id).collection("connections")
        connections = connections_ref.stream()
        connection_list = []
        for connection in connections:
            connection_data = connection.to_dict()
            profile = ConnectionProfile.from_dict(connection_data)
            connection_list.append(profile.to_dict())

        return {"connections": connection_list}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500

def set_active_connection_firestore(user_id, connection_id):
    try:
        db.collection("users").document(user_id).collection("settings").document("active_connection").set({
            "connection_id": connection_id
        })
        return {"status": "active connection set", "connection_id": connection_id}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500

def get_active_connection_firestore(user_id):
    try:
        doc_ref = db.collection("users").document(user_id).collection("settings").document("active_connection")
        doc = doc_ref.get()
        if doc.exists:
            return {"active_connection_id": doc.to_dict().get("connection_id")}
        else:
            active_connection_id = f"{user_id}:{current_app.config['NULL_CONNECTION_ID']}"
            set_active_connection_firestore(user_id, active_connection_id)
            return active_connection_id
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500

def clear_active_connection_firestore(user_id):
    try:
        db.collection("users").document(user_id).collection("settings").document("active_connection").delete()
        
        active_connection = f"{user_id}:{current_app.config['NULL_CONNECTION_ID']}"
        set_active_connection_firestore(user_id, active_connection)
        return {"status": "active connection cleared"}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500

def get_connection_profile(user_id, connection_id):
    if not user_id:
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400
    if not connection_id:
        connection_id = f"{user_id}:{current_app.config['NULL_CONNECTION_ID']}"
        return None
    try:
        doc = db.collection("users").document(user_id).collection("connections").document(connection_id).get()
        if doc.exists:
            connection_data = doc.to_dict()
            profile = ConnectionProfile.from_dict(connection_data)
            return profile.to_dict()
        else:
            err_point = __package__ or __name__
            logger.error(f"Error: {err_point}")
            return jsonify({'error': f"[{err_point}] - Error:"}), 404
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500

def update_connection_profile(user_id, connection_id, data):
    generic_connection_id = f"{user_id}:{current_app.config['NULL_CONNECTION_ID']}"
    if not user_id or connection_id.casefold() != generic_connection_id.casefold():
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400
    try:
        db.collection("users").document(user_id).collection("connections").document(connection_id).update(data)
        return {"status": "connection profile updated"}
    except Exception as e:
        return {"error": str(e)}, 500

def delete_connection_profile(user_id, connection_id):
    generic_connection_id = f"{user_id}:{current_app.config['NULL_CONNECTION_ID']}"
    if not user_id or connection_id.casefold() == generic_connection_id.casefold():
        err_point = __package__ or __name__
        logger.error(f"Error: {err_point}")
        return jsonify({'error': f"[{err_point}] - Error:"}), 400
    try:
        db.collection("users").document(user_id).collection("connections").document(connection_id).delete()
        return {"status": "connection profile deleted"}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500