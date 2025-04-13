from functools import wraps
from flask import request, jsonify
import utils.trait_manager as trait_manager
from .moderation import moderate_topic
from infrastructure.logger import setup_logger

def sanitize_topic(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        context = getattr(request, "context", request.get_json() or {})
        topic = context.get("topic", "")
        filtered = False

        if isinstance(topic, str):
            topic = topic.strip()[:75]

        result = moderate_topic(topic)
        if not result["safe"]:
            topic = ""
            filtered = True

        context["topic"] = topic
        context["quick_topic_filtered"] = filtered
        request.context = context

        return f(*args, **kwargs)
    return wrapper


def validate_profile(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        data = request.get_json() or {}
        user_profile = data.get("user_profile", {})
        connection_profile = data.get("connection_profile", {})
        
        # Validate age field exists and is an integer >= 18
        try:
            age = int(user_profile.get("age", 0))
            if age < 18:
                logger = setup_logger(name="middleware_log.file", toFile=True, filename="middleware.log")
                logger.error("utils.middleware.validate_profile error: age verification failure")
                raise ValueError
        except (ValueError, TypeError):

            return jsonify({"error": "User age must be at least 18"}), 400

        if "age" in connection_profile:
            try:
                connection_age = int(connection_profile["age"])
                if connection_age < 18:
                    raise ValueError
            except (ValueError, TypeError):
                logger = setup_logger(name="middleware_log.file", toFile=True, filename="middleware.log")
                logger.error("utils.middleware.validate_profile error: age verification failure")
                return jsonify({"error": "connection age must be at least 18 if provided"}), 400

        return f(*args, **kwargs)
    return wrapper

def enrich_context(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        data = request.get_json() or {}
        conversation = data.get("conversation", [])
        
        if not data.get("situation"):
            try:
                inferred = trait_manager.infer_situation(conversation)
            except Exception as e:
                logger = setup_logger(name="middleware_log.file", toFile=True, filename="middleware.log")
                logger.error("tils.middleware.enrich_context error: %s", e)
                inferred = {"situation": "cold_open", "confidence": "low"}
            data["situation"] = inferred.get("situation", "cold_open")
            data["situation_confidence"] = inferred.get("confidence", "low")
        
        # Attach enriched data to request context
        
        request.context = data
        
        return f(*args, **kwargs)
    
    return wrapper