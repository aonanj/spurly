from clients import db
import uuid
from flask import current_app
from utils.logger import setup_logger

def create_connection_profile(data):
    user_id = data.get("user_id")
    if not user_id:
        return {"error": "Missing user_id"}, 400

    short_id = uuid.uuid4().hex[:8]
    connection_id = f"{user_id}:{short_id}"
    profile_data = {k: v for k, v in data.items() if k != "user_id"}
    profile_data["connection_id"] = connection_id

    try:
        db.collection("users").document(user_id).collection("connections").document(connection_id).set(profile_data)
        return {
            "status": "connection profile created",
            "connection_id": connection_id,
            "connection_profile": format_connection_profile(connection_id, profile_data)
        }
    except Exception as e:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Create connection profile error: %s", e)
        return {"error": str(e)}, 500

def format_connection_profile(connection_id, profile_data):
    lines = [f"connection_id: {connection_id}"]
    for key in [
        "name", "age", "gender", "pronouns", "school", "job", "drinking", "ethnicity", "hometown"
    ]:
        value = profile_data.get(key)
        if value:
            lines.append(f"{key.capitalize()}: {value}")

    green = profile_data.get("greenlight_topics", [])
    red = profile_data.get("redlight_topics", [])
    if green:
        lines.append(f"Greenlight Topics: {', '.join(green)}")
    if red:
        lines.append(f"Redlight Topics: {', '.join(red)}")

    return "\n".join(lines)

def save_user_profile(data):
    user_id = data.get("user_id")
    if not user_id:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Missing user_id in save_user_profile")
        return {"error": "Missing user_id"}, 400

    try:
        profile_data = {k: v for k, v in data.items() if k != "user_id"}
        db.collection("users").document(user_id).collection("profile").document("profile").set(profile_data)
        return {"status": "user profile saved"}
    except Exception as e:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Error saving user profile: %s", e)
        return {"error": str(e)}, 500

def save_connection_profile(data):
    user_id = data.get("user_id")
    connection_id = data.get("connection_id")
    if not user_id or not connection_id:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Missing user_id or connection_id in save_connection_profile")
        return {"error": "Missing user_id or connection_id"}, 400

    try:
        profile_data = {k: v for k, v in data.items() if k not in ["user_id", "connection_id"]}
        db.collection("users").document(user_id).collection("connections").document(connection_id).set(profile_data)
        return {"status": "connection profile saved"}
    except Exception as e:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Error saving connection profile: %s", e)
        return {"error": str(e)}, 500

def get_user_profile(user_id):
    if not user_id:
        return {"error": "Missing user_id"}, 400

    try:
        doc_ref = db.collection("users").document(user_id).collection("profile").document("profile")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return {"error": "Profile not found"}, 404
    except Exception as e:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Error getting user profile: %s", e)
        return {"error": str(e)}, 500

def get_user_connections(user_id):
    if not user_id:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Missing user_id in get_user_connections")
        return {"error": "Missing user_id"}, 400

    try:
        connections_ref = db.collection("users").document(user_id).collection("connections")
        connections = connections_ref.stream()
        connection_list = []
        for connection in connections:
            connection_data = connection.to_dict()
            connection_data["connection_id"] = connection.id
            connection_list.append(connection_data)

        return {"connections": connection_list}
    except Exception as e:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Error getting user connections: %s", e)
        return {"error": str(e)}, 500

def set_active_connection_firestore(user_id, connection_id):
    try:
        db.collection("users").document(user_id).collection("settings").document("active_connection").set({
            "connection_id": connection_id
        })
        return {"status": "active connection set", "connection_id": connection_id}
    except Exception as e:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Error setting active connection: %s", e)
        return {"error": str(e)}, 500

def get_active_connection_firestore(user_id):
    try:
        doc_ref = db.collection("users").document(user_id).collection("settings").document("active_connection")
        doc = doc_ref.get()
        if doc.exists:
            return {"active_connection_id": doc.to_dict().get("connection_id")}
        else:
            active_connection_id = f"{user_id}:{current_app.config['NULL_connection_id']}"
            set_active_connection_firestore(user_id, active_connection_id)
            return active_connection_id
    except Exception as e:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Error getting active connection: %s", e)
        return {"error": str(e)}, 500

def clear_active_connection_firestore(user_id):
    try:
        db.collection("users").document(user_id).collection("settings").document("active_connection").delete()
        
        active_connection = f"{user_id}:{current_app.config['NULL_connection_id']}"
        set_active_connection_firestore(user_id, active_connection)
        return {"status": "active connection cleared"}
    except Exception as e:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Error clearing active connection: %s", e)
        return {"error": str(e)}, 500

def get_connection_profile(user_id, connection_id):
    if not user_id:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Missing user_id in get_connection_profile")
        return {"error": "Missing user_id"}, 400
    if not connection_id:
        connection_id = f"{user_id}:{current_app.config['NULL_connection_id']}"
        return None
    try:
        doc = db.collection("users").document(user_id).collection("connections").document(connection_id).get()
        if doc.exists:
            connection_data = doc.to_dict()
            connection_data["connection_id"] = connection_id
            return connection_data
        else:
            logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
            logger.error("connection profile not found for user_id: %s, connection_id: %s", user_id, connection_id)
            return {"error": "connection not found"}, 404
    except Exception as e:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Get connection profile error: %s", e)
        return {"error": str(e)}, 500

def update_connection_profile(user_id, connection_id, data):
    generic_connection_id = f"{user_id}:{current_app.config['NULL_connection_id']}"
    if not user_id or connection_id.casefold() != generic_connection_id.casefold():
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Missing user_id or connection_id in update_connection_profile")
        return {"error": "Missing user_id or connection_id"}, 400
    try:
        db.collection("users").document(user_id).collection("connections").document(connection_id).update(data)
        return {"status": "connection profile updated"}
    except Exception as e:
        return {"error": str(e)}, 500

def delete_connection_profile(user_id, connection_id):
    generic_connection_id = f"{user_id}:{current_app.config['NULL_connection_id']}"
    if not user_id or connection_id.casefold() != generic_connection_id.casefold():
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Missing user_id or connection_id in delete_connection_profile")
        return {"error": "Missing user_id or connection_id"}, 400
    try:
        db.collection("users").document(user_id).collection("connections").document(connection_id).delete()
        return {"status": "connection profile deleted"}
    except Exception as e:
        logger = setup_logger(name="connection_profile_log.file", toFile=True, filename="connection_profile.log")
        logger.error("Error deleting connection profile: %s", e)
        return {"error": str(e)}, 500