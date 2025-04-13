from clients import db
import uuid
from flask import current_app
from utils.logger import setup_logger

def create_poi_profile(data):
    user_id = data.get("user_id")
    if not user_id:
        return {"error": "Missing user_id"}, 400

    short_id = uuid.uuid4().hex[:8]
    cid = f"{user_id}:{short_id}"
    profile_data = {k: v for k, v in data.items() if k != "user_id"}
    profile_data["cid"] = cid

    try:
        db.collection("users").document(user_id).collection("pois").document(cid).set(profile_data)
        return {
            "status": "POI profile created",
            "cid": cid,
            "poi_sketch": format_poi_sketch(cid, profile_data)
        }
    except Exception as e:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Create POI profile error: %s", e)
        return {"error": str(e)}, 500

def format_poi_sketch(cid, profile_data):
    lines = [f"CID: {cid}"]
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
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Missing user_id in save_user_profile")
        return {"error": "Missing user_id"}, 400

    try:
        profile_data = {k: v for k, v in data.items() if k != "user_id"}
        db.collection("users").document(user_id).collection("profile").document("sketch").set(profile_data)
        return {"status": "user profile saved"}
    except Exception as e:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Error saving user profile: %s", e)
        return {"error": str(e)}, 500

def save_poi_profile(data):
    user_id = data.get("user_id")
    cid = data.get("cid")
    if not user_id or not cid:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Missing user_id or cid in save_poi_profile")
        return {"error": "Missing user_id or cid"}, 400

    try:
        profile_data = {k: v for k, v in data.items() if k not in ["user_id", "cid"]}
        db.collection("users").document(user_id).collection("pois").document(cid).set(profile_data)
        return {"status": "POI profile saved"}
    except Exception as e:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Error saving POI profile: %s", e)
        return {"error": str(e)}, 500

def get_user_profile(user_id):
    if not user_id:
        return {"error": "Missing user_id"}, 400

    try:
        doc_ref = db.collection("users").document(user_id).collection("profile").document("sketch")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return {"error": "Profile not found"}, 404
    except Exception as e:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Error getting user profile: %s", e)
        return {"error": str(e)}, 500

def get_user_pois(user_id):
    if not user_id:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Missing user_id in get_user_pois")
        return {"error": "Missing user_id"}, 400

    try:
        pois_ref = db.collection("users").document(user_id).collection("pois")
        pois = pois_ref.stream()
        poi_list = []
        for poi in pois:
            poi_data = poi.to_dict()
            poi_data["cid"] = poi.id
            poi_list.append(poi_data)

        return {"pois": poi_list}
    except Exception as e:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Error getting user POIs: %s", e)
        return {"error": str(e)}, 500

def set_active_poi_firestore(user_id, cid):
    try:
        db.collection("users").document(user_id).collection("settings").document("active_poi").set({
            "cid": cid
        })
        return {"status": "active POI set", "cid": cid}
    except Exception as e:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Error setting active POI: %s", e)
        return {"error": str(e)}, 500

def get_active_poi_firestore(user_id):
    try:
        doc_ref = db.collection("users").document(user_id).collection("settings").document("active_poi")
        doc = doc_ref.get()
        if doc.exists:
            return {"active_poi": doc.to_dict().get("cid")}
        else:
            active_poi = f"{user_id}:{current_app.config['NULL_CID']}"
            set_active_poi_firestore(user_id, active_poi)
            return active_poi
    except Exception as e:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Error getting active POI: %s", e)
        return {"error": str(e)}, 500

def clear_active_poi_firestore(user_id):
    try:
        db.collection("users").document(user_id).collection("settings").document("active_poi").delete()
        
        active_poi = f"{user_id}:{current_app.config['NULL_CID']}"
        set_active_poi_firestore(user_id, active_poi)
        return {"status": "active POI cleared"}
    except Exception as e:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Error clearing active POI: %s", e)
        return {"error": str(e)}, 500

def get_poi_profile(user_id, cid):
    if not user_id:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Missing user_id in get_poi_profile")
        return {"error": "Missing user_id"}, 400
    if not cid:
        cid = f"{user_id}:{current_app.config['NULL_CID']}"
        return None
    try:
        doc = db.collection("users").document(user_id).collection("pois").document(cid).get()
        if doc.exists:
            poi_data = doc.to_dict()
            poi_data["cid"] = cid
            return poi_data
        else:
            logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
            logger.error("POI profile not found for user_id: %s, cid: %s", user_id, cid)
            return {"error": "POI not found"}, 404
    except Exception as e:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Get POI profile error: %s", e)
        return {"error": str(e)}, 500

def update_poi_profile(user_id, cid, data):
    generic_cid = f"{user_id}:{current_app.config['NULL_CID']}"
    if not user_id or cid.casefold() != generic_cid.casefold():
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Missing user_id or cid in update_poi_profile")
        return {"error": "Missing user_id or cid"}, 400
    try:
        db.collection("users").document(user_id).collection("pois").document(cid).update(data)
        return {"status": "POI profile updated"}
    except Exception as e:
        return {"error": str(e)}, 500

def delete_poi_profile(user_id, cid):
    generic_cid = f"{user_id}:{current_app.config['NULL_CID']}"
    if not user_id or cid.casefold() != generic_cid.casefold():
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Missing user_id or cid in delete_poi_profile")
        return {"error": "Missing user_id or cid"}, 400
    try:
        db.collection("users").document(user_id).collection("pois").document(cid).delete()
        return {"status": "POI profile deleted"}
    except Exception as e:
        logger = setup_logger(name="poi_profile_log.file", toFile=True, filename="poi_profile.log")
        logger.error("Error deleting POI profile: %s", e)
        return {"error": str(e)}, 500