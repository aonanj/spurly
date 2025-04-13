from functools import wraps
from flask import request, jsonify, current_app, g
import jwt
from .logger import setup_logger
from uuid import uuid4

def generate_uid() -> str:
    return f"u{uuid4().hex[:8]}"

def create_jwt(uid:str) -> str:
    try:
        payload = {
            "uid": uid,
            "exp": current_app.config["JWT_EXPIRATION"],
        }
        token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
        return token
    except Exception as e:
        logger = setup_logger(name="auth_log.file", toFile=True, filename="auth.log")
        logger.error("Error in utils.auth.create_jwt: %s", e)
        return {"error": str(e)}, 500


def decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError as e:
        logger = setup_logger(name="auth_log.file", toFile=True, filename="auth.log")
        logger.error("Expired Token: %s", e)
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError as e:
        logger = setup_logger(name="auth_log.file", toFile=True, filename="auth.log")
        logger.error("Invalid token: %s", e)
        return {"error": "Invalid token"}

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            parts = auth_header.split()

            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
            else:
                logger = setup_logger(name="auth_log.file", toFile=True, filename="auth.log")
                logger.warning("Invalid authorization header format")
                return jsonify({"error": "Invalid authorization header"}), 401
            
        if not token:
            logger = setup_logger(name="auth_log.file", toFile=True, filename="auth.log")
            logger.warning("Token not provided")
            return jsonify({"error": "Token not provided"}), 401

        try:
            payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            g.user = payload
        except jwt.ExpiredSignatureError as e:
            logger = setup_logger(name="auth_log.file", toFile=True, filename="auth.log")
            logger.error("Expired Token: %s", e)
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
            logger = setup_logger(name="auth_log.file", toFile=True, filename="auth.log")
            logger.error("Invalid Token: %s", e)
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            logger = setup_logger(name="auth_log.file", toFile=True, filename="auth.log")
            logger.error(f"Authentication error: {e}")
            return jsonify({"error": "Authentication error"}), 500
        
        return f(*args, **kwargs)
    return decorated
