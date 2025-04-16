from firebase_admin import credentials, firestore
from flask import current_app
from google.cloud import firestore
from google.cloud import vision
from google.oauth2 import service_account
from infrastructure.logger import get_logger
import firebase_admin
import openai


db = None
vision_client = None
chat_client = None
mod_client = None

def init_clients(app):
    """
    
    Initializes API clients, including AI model, Google Cloud services; sets global environment constants 
    
    Args
        app: Flask app using the clients and variables initialized here
            Flask object
    
    Return
        N/A
    
    """
    global db, vision_client, chat_client, mod_client

    logger = get_logger(__name__)

    # Firebase
    if not firebase_admin._apps:
        cred_path = app.config['GOOGLE_CLOUD_FIREBASE_API_KEY']
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    # Firestore
    firestore_cred_path = app.config['GOOGLE_CLOUD_FIRESTORE_API_KEY']
    firestore_creds = service_account.Credentials.from_service_account_file(firestore_cred_path)
    db = firestore.Client(credentials=firestore_creds, project=firebase_admin.get_app().project_id) # Specify project if needed

    # Vision
    vision_cred_path = app.config['GOOGLE_CLOUD_VISION_API_KEY']
    vision_creds = service_account.Credentials.from_service_account_file(vision_cred_path)
    vision_client = vision.ImageAnnotatorClient(credentials=vision_creds)

    # OpenAI
    openai.api_key = app.config['OPENAI_API_KEY']
    # Use the documented way to get clients if possible, e.g., directly using openai.ChatCompletion etc.
    # If direct client access is necessary, keep as is but be aware of potential breakage.
    
    try:
        prompt_path = current_app.config['SPURLY_SYSTEM_PROMPT']
        with open(prompt_path, 'r') as f:
            system_prompt = f.read()
    except Exception as e:
        logger.error("[%s] Error: %s System prompt not found", __name__, e)
        raise e
    chat_client = openai.chat.completions # Example if using v1.0+ structure
    mod_client = openai.moderations # Example if using v1.0+ structure

    # In app.py, call init_clients(app) after app creation


