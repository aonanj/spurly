import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "spurly-default-key")
    GOOGLE_CLOUD_VISION_API_KEY = os.environ.get("GOOGLE_CLOUD_VISION_API_KEY", "")
    GOOGLE_CLOUD_FIRESTORE_API_KEY = os.environ.get("GOOGLE_CLOUD_FIRESTORE_API_KEY", "")
    GOOGLE_CLOUD_FIREBASE_API_KEY = os.environ.get("GOOGLE_CLOUD_FIREBASE_API_KEY", "")
    GOOGLE_CLOUD_VERTEX_API_KEY = os.environ.get("GOOGLE_CLOUD_VERTEX_API_KEY", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    ENABLE_AUTH = os.environ.get("ENABLE_AUTH", "True").lower() == "true"
    
    SPURLY_SYSTEM_PROMPT_PATH = os.environ.get("SPURLY_SYSTEM_PROMPT_PATH", "resources/spurly_system_prompt.txt")

    SPUR_VARIANTS = (
        "main_spur",
        "warm_spur",
        "cool_spur",
        "playful_spur"
    )

    SPUR_VARIANT_DESCRIPTIONS = {
        "main_spur": "Friendly (emotionally open, upbeat, optimistic, receptive, engaging)",
        "warm_spur": "Warm (lighthearted, kind, empathetic, sincere, thoughtful)",
        "cool_spur": "Cool (carefree, casual, cool and calm, dry, occasionally sarcastic)",
        "playful_spur": "Playful (humorous, joking, good-natured teasing, occasionally flirty)",
    }
    
    SPUR_VARIANT_ID_KEYS = {
        "main_spur": "S",
        "warm_spur": "W",
        "cool_spur": "C",
        "playful_spur": "P"
        }

    JWT_EXPIRATION = 60 * 60 * 24 * 7  # 1 week

    NULL_CONNECTION_ID = "generic_connection_id"
    
    LOGGER_LEVEL = os.environ.get("LOGGER_LEVEL", "INFO")
    
    AI_MODEL = os.environ.get("GPT_MODEL_NAME", "gpt-4")
    AI_MESSAGES_ROLE_SYSTEM = "system"
    AI_MESSAGES_ROLE_USER = "user"
    AI_TEMPERATURE_INITIAL = 0.9
    AI_TEMPERATURE_RETRY = .65
    AI_MAX_TOKENS = 600