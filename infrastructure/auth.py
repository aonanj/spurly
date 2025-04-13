from functools import wraps
from flask import request, jsonify, current_app, g
import jwt
from .logger import get_logger
from uuid import uuid4

logger = get_logger(__name__)

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
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return (f"[{err_point}] - Error: {str(e)}"), 500


def decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return (f"[{err_point}] - Error: {str(e)}")
    except jwt.InvalidTokenError as e:
        err_point = __package__ or __name__
        logger.error("[%s] Error: %s", err_point, e)
        return (f"[{err_point}] - Error: {str(e)}")

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
                err_point = __package__ or __name__
                logger.error("[%s] Error: %s", err_point, e)
                return jsonify({"error": f"[{err_point}] - Error"}), 401
            
        if not token:
                err_point = __package__ or __name__
                logger.error("[%s] Error: %s", err_point, e)
                return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 401

        try:
            payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            g.user = payload
        except jwt.ExpiredSignatureError as e:
                err_point = __package__ or __name__
                logger.error("[%s] Error: %s", err_point, e)
                return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 401
        except jwt.InvalidTokenError as e:
                err_point = __package__ or __name__
                logger.error("[%s] Error: %s", err_point, e)
                return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 401
        except Exception as e:
                err_point = __package__ or __name__
                logger.error("[%s] Error: %s", err_point, e)
                return jsonify({'error': f"[{err_point}] - Error: {str(e)}"}), 500
        
        return f(*args, **kwargs)
    return decorated
