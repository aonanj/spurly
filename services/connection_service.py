from class_defs.profile_def import ConnectionProfile
from dataclasses import fields
from flask import current_app, jsonify, g
from infrastructure.clients import db
from infrastructure.id_generator import generate_connection_id, get_null_connection_id
from infrastructure.logger import get_logger

logger = get_logger(__name__)

def create_connection_profile(data: dict) -> dict:
    """
    Creates a ConnectionProfile with data received from the frontend.

    Args:
        data: Dictionary representation of the connection information 
            dict

    Returns:
        status: status of creating a connection profile.
    """
    user_id = g.user['user_id']
    if not user_id:
        logger.error("Error: Cannot create connection profile - missing user ID")
        raise TypeError("Error: Cannot create connection profile - missing user ID")

    profile = ConnectionProfile.from_dict(data)
    connection_id = generate_connection_id(user_id)
    
    profile_data = profile.to_dict()
    profile_data["connection_id"] = connection_id

    try:
        db.collection("users").document(user_id).collection("connections").document(connection_id).set(profile_data)
        return {
            "status": "connection profile created",
            "connection_id": connection_id,
            "connection_profile": format_connection_profile(profile)
        }
    except Exception as e:
        logger.error("[%s] Error: %s", "cannot create connection profile", e)
        return {"error": f"cannot create connection profile: {str(e)}"}

def format_connection_profile(connection_profile: ConnectionProfile) -> str:
    """
    Converts a ConnectionProfile object into a formatted string for human-readable display.

    Args:
        connection_id (str): The unique ID of the connection.
        profile_data (dict): Dictionary representation of the ConnectionProfile.

    Returns:
        str: A multiline formatted string summarizing the profile contents.
    """
    profile = ConnectionProfile.to_dict(connection_profile)
    connection_id = profile.get('connection_id')
    lines = [f"connection_id: {connection_id}"]

    for field in fields(ConnectionProfile):
        key = field.name
        value = getattr(profile, key)

        if key == "user_id" or value is None:
            continue
        if key == "connection_id" or value is None:
            continue

        if isinstance(value, list):
            if value:
                label = "Greenlight Topics" if key == "greenlights" else (
                        "Redlight Topics" if key == "redlights" else key.capitalize())
                lines.append(f"{label}: {', '.join(value)}")
        else:
            lines.append(f"{key.capitalize()}: {value}")

    return "\n".join(lines)

def save_connection_profile(connection_profile: ConnectionProfile) -> dict:
    """
    Saves the profile of a connection 

    Args
        data: profile data to be saved for a connection
            dict
    Return
        status: status indicating whether connection profile is saved
            dict
    """
    connection_profile_dict = ConnectionProfile.to_dict(connection_profile)
    user_id = connection_profile_dict.get("user_id")
    connection_id = connection_profile_dict.get("connection_id")
    if not connection_profile or not user_id or not connection_id or connection_id.endswith(current_app.config['NULL_CONNECTION_ID']):
        logger.error("Error: Cannot save connection profile - missing user ID or connection ID")
        raise TypeError("Error: Cannot save connection profile - missing user ID or connection ID")

    try:
        db.collection("users").document(user_id).collection("connections").document(connection_id).set(connection_profile_dict)
        return {"status": "connection profile saved"}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error saving connection profile:  %s", err_point, e)
        return {'error': f"[{err_point}] - Error: {str(e)}"}

def get_user_connections(user_id:str) -> list:
    """
    Gets the connections associated with the user_id

    Args
        user_id: User ID
            str

    Return
        connections: List of connections associated with the user_id
            List[ConnectionProfile]
    """
    if not user_id:
        logger.error("Error: Cannot get connections - missing user ID")
        raise TypeError("Error: Cannot get connections - missing user ID")

    try:
        connections_ref = db.collection("users").document(user_id).collection("connections")
        connections = connections_ref.stream()
        connection_list = []
        for connection in connections:
            connection_data = connection.to_dict()
            profile = ConnectionProfile.from_dict(connection_data)
            connection_list.append(profile)

        return connection_list
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return []

def set_active_connection_firestore(user_id: str, connection_id: str) -> dict:
    """
    Sets the connection id of the connection that is active in the context

    Args
        user_id: User ID
            str
        connection_id: Connection ID of active connection
            str
    Return
        status: status indicating connection ID is set as active
            dict
    """
    if not user_id:
        logger.error("Error: Cannot set active connection - missing user ID")
        raise TypeError("Error: Cannot set active connection - missing user ID")
    if not connection_id:
        logger.log(current_app.config['DEFAULT_LOG_LEVEL'], "Null connection active in context")
        connection_id = get_null_connection_id(user_id)
    try:
        db.collection("users").document(user_id).collection("settings").document("active_connection").set({
            "connection_id": connection_id
        })
        return {"status": "active connection set", "connection_id": connection_id}
    except Exception as e:
        logger.error(f"Error: Cannot set active connection - {e}")
        return {"Error": str(e)}


def get_active_connection_firestore(user_id: str) -> str:
    """
    Gets the connection id of the connection that is active in the context

    Args
        user_id: User ID
            str

    Return
        connection_id: Connection ID of active connection
            str
    """
    if not user_id:
        logger.error("Error: Cannot get active connection - missing user ID")
        raise TypeError("Error: Cannot get active connection - missing user ID")
    
    try:
        doc_ref = db.collection("users").document(user_id).collection("settings").document("active_connection")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("connection_id")
        else:
            active_connection_id = get_null_connection_id(user_id)
            set_active_connection_firestore(user_id, active_connection_id)
            return active_connection_id
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return f"Error {e}: Cannot get active connection"

def clear_active_connection_firestore(user_id: str) -> dict:
    """
    Clears the connection id of the connection that is active in the context

    Args
        user_id: User ID
            str
    Return
        status: status indicating connection ID is set as active
            dict
    """
    if not user_id:
        logger.error("Error: Cannot clear active connection - missing user ID")
        raise TypeError("Error: Cannot clear active connection - missing user ID")
    
    try:
        db.collection("users").document(user_id).collection("settings").document("active_connection").delete()
        
        active_connection_id = get_null_connection_id(user_id)
        set_active_connection_firestore(user_id, active_connection_id)
        return {"status": "active connection cleared"}
    except Exception as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return {'error': {str(e)}}

def get_connection_profile(user_id: str, connection_id: str) -> ConnectionProfile:
    """
    Gets the connection profile corresponding to the connection_id

    Args
        user_id: User ID
            str
        connection_id: Connection ID corresponding to the profile
            str
    Return
        connection_profile: profile of the connection corresponding to the connection_id
            ConnectionProfile

    """
    if not user_id or not connection_id or connection_id.endswith(current_app.config['NULL_CONNECTION_ID']):
        logger.error("Error: Cannot get connection profile - missing user ID or connection ID")
        raise TypeError("Error: Cannot get connection profile - missing user ID or connection ID")
    try:
        doc = db.collection("users").document(user_id).collection("connections").document(connection_id).get()
        if doc.exists:
            connection_data = doc.to_dict()
            profile = ConnectionProfile.from_dict(connection_data)
            return profile
        else:
            logger.error(f"Error: Cannot get connection profile")
            raise ValueError("error: cannot get connection profile")
    except Exception as e:
        logger.error("[%s] Error: %s", "cannot get connection profile", e)
        raise TypeError(f"error{e}: cannot get connection profile")

def update_connection_profile(user_id, connection_id, data) -> dict:
    """
    Updates the profile of a connection with data

    Args
        user_id: User ID
            str
        connection_id: Connection ID
            str
        data: Data to add to profile corresponding to connection ID
            dict
    Return
        status: status indicating whether connection profile is updated
            dict
    """

    if not user_id or not connection_id or connection_id.endswith(current_app.config['NULL_CONNECTION_ID']):
        logger.error("Error: Cannot update connection profile - missing user ID or connection ID")
        raise TypeError("Error: Cannot update connection profile - missing user ID or connection ID")
    else:
        try:
            db.collection("users").document(user_id).collection("connections").document(connection_id).update(data)
            return {"status": "connection profile updated"}
        except Exception as e:
            logger.error(f"Error: Cannot update connection profile - {e}")
            return {"error": str(e)}

def delete_connection_profile(user_id: str, connection_id:str) -> dict:
    """
    Deletes the profile of a connection 

    Args
        user_id: User ID
            str
        connection_id: Connection ID of profile to be deleted
            str
    Return
        status: status indicating whether connection profile is deleted
            dict
    """
    if not user_id or not connection_id or connection_id.endswith(current_app.config['NULL_CONNECTION_ID']):
        logger.error("Error: Cannot delete connection profile - missing user ID or connection ID")
        raise TypeError("Error: Cannot delete connection profile - missing user ID or connection ID")
    try:
        db.collection("users").document(user_id).collection("connections").document(connection_id).delete()
        return {"status": "connection profile deleted"}
    except Exception as e:
        logger.error(f"Error: Cannot delete connection profile - {e}")
        return {"error": str(e)}