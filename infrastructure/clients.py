# infrastructure/clients.py

# --- Imports ---
# Standard library imports
import os

# Third-party imports
from firebase_admin import credentials, initialize_app, get_app
from google.cloud import firestore, vision
from google.oauth2 import service_account
from openai import OpenAI # Import the main OpenAI class
import firebase_admin

# Local application imports
from .logger import get_logger # Use relative import if logger is in the same directory

# --- Global Client Variables ---
# Initialize clients to None initially
db = None
vision_client = None
openai_client = None 


# --- Initialization Function ---
def init_clients(app):
    """
    Initializes API clients, including OpenAI, Google Cloud services;
    sets global environment constants based on Flask app config.

    Args:
        app: Flask app object providing configuration.
    """
    global db, vision_client, openai_client # Declare modification of global variables

    logger = get_logger(__name__)
    logger.info("Initializing external clients...")

    # --- Firebase Admin ---
    try:
        if not firebase_admin._apps:
            cred_path = app.config['GOOGLE_CLOUD_FIREBASE_API_KEY']
            if not cred_path or not os.path.exists(cred_path):
                 raise FileNotFoundError(f"Firebase Admin key file not found at: {cred_path}")
            cred = credentials.Certificate(cred_path)
            initialize_app(cred)
            logger.info("Firebase Admin initialized.")
        else:
             logger.info("Firebase Admin already initialized.")
    except Exception as e:
        logger.error("Failed to initialize Firebase Admin: %s", e, exc_info=True)
        raise # Stop app initialization if critical components fail

    # --- Firestore Client ---
    try:
        firestore_cred_path = app.config['GOOGLE_CLOUD_FIRESTORE_API_KEY']
        if not firestore_cred_path or not os.path.exists(firestore_cred_path):
             raise FileNotFoundError(f"Firestore key file not found at: {firestore_cred_path}")
        firestore_creds = service_account.Credentials.from_service_account_file(firestore_cred_path)
        # Ensure project_id is correctly inferred or explicitly provided
        project_id = get_app().project_id if firebase_admin._apps else app.config.get('GOOGLE_CLOUD_PROJECT_ID')
        if not project_id:
            raise ValueError("Google Cloud Project ID could not be determined.")
        db = firestore.Client(credentials=firestore_creds, project=project_id)
        logger.info("Firestore client initialized for project: %s", project_id)
    except Exception as e:
        logger.error("Failed to initialize Firestore client: %s", e, exc_info=True)
        raise

    # --- Google Cloud Vision Client ---
    try:
        vision_cred_path = app.config['GOOGLE_CLOUD_VISION_API_KEY']
        if not vision_cred_path or not os.path.exists(vision_cred_path):
             raise FileNotFoundError(f"Vision API key file not found at: {vision_cred_path}")
        vision_creds = service_account.Credentials.from_service_account_file(vision_cred_path)
        vision_client = vision.ImageAnnotatorClient(credentials=vision_creds)
        logger.info("Google Cloud Vision client initialized.")
    except Exception as e:
        logger.error("Failed to initialize Google Cloud Vision client: %s", e, exc_info=True)
        raise

    # --- OpenAI Client ---
    try:
        api_key = app.config['OPENAI_API_KEY']
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in configuration.")
        # Initialize the main OpenAI client object
        openai_client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized.")
        # If you were using separate clients before, you now access methods via this client:
        # e.g., openai_client.chat.completions.create(...)
        # e.g., openai_client.moderations.create(...)
    except Exception as e:
        logger.error("Failed to initialize OpenAI client: %s", e, exc_info=True)
        raise

    logger.info("All external clients initialized successfully.")


def get_openai_client() -> OpenAI:
    """ Safely returns the initialized OpenAI client instance. """
    if openai_client is None:
        # This indicates an issue with the application startup order
        raise RuntimeError("OpenAI client has not been initialized. Ensure init_clients() is called.")
    return openai_client