from clients import db
import uuid

def create_poi_profile(data):
    user_id = data.get("user_id")
    if not user_id:
        return {"error": "Missing user_id"}, 400

    short_id = uuid.uuid4().hex[:8]
    poi_id = f"{user_id}:{short_id}"
    profile_data = {k: v for k, v in data.items() if k != "user_id"}
    profile_data["cid"] = poi_id

    try:
        db.collection("users").document(user_id).collection("pois").document(poi_id).set(profile_data)
        return {
            "status": "POI profile created",
            "cid": poi_id,
            "poi_sketch": format_poi_sketch(poi_id, profile_data)
        }
    except Exception as e:
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
        return {"error": "Missing user_id"}, 400

    profile_data = {k: v for k, v in data.items() if k != "user_id"}
    db.collection("users").document(user_id).collection("profile").document("sketch").set(profile_data)
    return {"status": "user profile saved"}

def save_poi_profile(data):
    user_id = data.get("user_id")
    poi_id = data.get("poi_id")
    if not user_id or not poi_id:
        return {"error": "Missing user_id or poi_id"}, 400

    profile_data = {k: v for k, v in data.items() if k not in ["user_id", "poi_id"]}
    db.collection("users").document(user_id).collection("pois").document(poi_id).set(profile_data)
    return {"status": "POI profile saved"}

def get_user_profile(user_id):
    if not user_id:
        return {"error": "Missing user_id"}, 400

    doc_ref = db.collection("users").document(user_id).collection("profile").document("sketch")
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return {"error": "Profile not found"}, 404

def get_user_pois(user_id):
    if not user_id:
        return {"error": "Missing user_id"}, 400

    pois_ref = db.collection("users").document(user_id).collection("pois")
    pois = pois_ref.stream()
    poi_list = []
    for poi in pois:
        poi_data = poi.to_dict()
        poi_data["poi_id"] = poi.id
        poi_list.append(poi_data)

    return {"pois": poi_list}

def set_active_poi_firestore(user_id, poi_id):
    try:
        db.collection("users").document(user_id).collection("settings").document("active_poi").set({
            "poi_id": poi_id
        })
        return {"status": "active POI set", "poi_id": poi_id}
    except Exception as e:
        return {"error": str(e)}, 500

def get_active_poi_firestore(user_id):
    try:
        doc_ref = db.collection("users").document(user_id).collection("settings").document("active_poi")
        doc = doc_ref.get()
        if doc.exists:
            return {"active_poi": doc.to_dict().get("poi_id")}
        else:
            return {"active_poi": None}
    except Exception as e:
        return {"error": str(e)}, 500

def clear_active_poi_firestore(user_id):
    try:
        db.collection("users").document(user_id).collection("settings").document("active_poi").delete()
        return {"status": "active POI cleared"}
    except Exception as e:
        return {"error": str(e)}, 500

def get_poi_profile(user_id, cid):
    if not user_id or not cid:
        return {"error": "Missing user_id or cid"}, 400
    try:
        doc = db.collection("users").document(user_id).collection("pois").document(cid).get()
        if doc.exists:
            poi_data = doc.to_dict()
            poi_data["poi_id"] = cid
            return poi_data
        else:
            return {"error": "POI not found"}, 404
    except Exception as e:
        return {"error": str(e)}, 500

def update_poi_profile(user_id, cid, data):
    if not user_id or not cid:
        return {"error": "Missing user_id or cid"}, 400
    try:
        db.collection("users").document(user_id).collection("pois").document(cid).update(data)
        return {"status": "POI profile updated"}
    except Exception as e:
        return {"error": str(e)}, 500

def delete_poi_profile(user_id, cid):
    if not user_id or not cid:
        return {"error": "Missing user_id or cid"}, 400
    try:
        db.collection("users").document(user_id).collection("pois").document(cid).delete()
        return {"status": "POI profile deleted"}
    except Exception as e:
        return {"error": str(e)}, 500