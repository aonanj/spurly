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

    SPUR_VARIANTS = (
        "main_spur",
        "warm_spur"
        "cool_spur",
        "playful_spur"
    )

    SPUR_VARIANT_DESCRIPTIONS = {
        "main": "Friendly (emotionally open, upbeat, optimistic, receptive, engaging)",
        "warm": "Warm (lighthearted, kind, empathetic, sincere, thoughtful)",
        "cool": "Cool (carefree, casual, cool and calm, dry, occasionally sarcastic)",
        "playful": "Playful (humorous, joking, good-natured teasing, occasionally flirty)",
    }

    JWT_EXPIRATION = 60 * 60 * 24 * 7  # 1 week

    NULL_CID = "generic_cid"
