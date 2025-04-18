from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "spurly-default-key")
    GOOGLE_CLOUD_VISION_API_KEY = os.environ.get("GOOGLE_CLOUD_VISION_API_KEY", "")
    GOOGLE_CLOUD_FIRESTORE_API_KEY = os.environ.get("GOOGLE_CLOUD_FIRESTORE_API_KEY", "")
    GOOGLE_CLOUD_FIREBASE_API_KEY = os.environ.get("GOOGLE_CLOUD_FIREBASE_API_KEY", "")
    GOOGLE_CLOUD_VERTEX_API_KEY = os.environ.get("GOOGLE_CLOUD_VERTEX_API_KEY", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    ## Google Cloud Vertex credentials
    GOOGLE_CLOUD_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT_ID", "") ## Google Cloud project ID
    GOOGLE_VERTEX_AI_LOCATION = os.environ.get("GOOGLE_VERTEX_AI_LOCATION", "") ## Location of the Vertex AI Search App (e.g., "global", "us")
    GOOGLE_VERTEX_AI_DATASTORE_ID = os.environ.get("GOOGLE_VERTEX_AI_DATASTORE_ID") ##ID of Vertex AI Search Data Store indexing conversations


    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") 
    REGION = os.environ.get("VERTEX_AI_REGION", "us-central1") # TODO Change Region
    INDEX_ENDPOINT_ID = os.environ.get("VERTEX_AI_INDEX_ENDPOINT_ID") # Your Vector Search index endpoint ID
    DEPLOYED_INDEX_ID = os.environ.get("VERTEX_AI_DEPLOYED_INDEX_ID") # Your deployed index ID within the endpoint
    EMBEDDING_MODEL_ENDPOINT_ID = os.environ.get("VERTEX_AI_EMBEDDING_ENDPOINT_ID") # Your embedding model endpoint ID (e.g., textembedding-gecko)
    EMBEDDING_DIMENSIONS = 768 # Or the dimension your embedding model outputs

    

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

    ID_DELIMITER = ":"    
    NULL_CONNECTION_ID = "null_connection_id:p"
    ANONYMOUS_ID_INDICATOR = "a"
    USER_ID_INDICATOR = "u"
    CONVERSATION_ID_INDICATOR = "c"   
    CONNECTION_ID_INDICATOR = "p"
    SPUR_ID_INDICATOR = "s"
       

    LOGGER_LEVEL = os.environ.get("LOGGER_LEVEL", "INFO")
    
    AI_MODEL = os.environ.get("GPT_MODEL_NAME", "gpt-4")
    AI_MESSAGES_ROLE_SYSTEM = "system"
    AI_MESSAGES_ROLE_USER = "user"
    AI_TEMPERATURE_INITIAL = 0.9
    AI_TEMPERATURE_RETRY = .65
    AI_MAX_TOKENS = 600
    
    ##Used as part of conversation_id to flag conversations extracted via OCR
    OCR_MARKER = "OCR"
    
    DEFAULT_LOG_LEVEL = 20