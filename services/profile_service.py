from clients import db

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