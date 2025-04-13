from google.cloud import firestore
from google.cloud import vision
from google.oauth2 import service_account
import os
import openai
from flask import current_app

firestore_creds = service_account.Credentials.from_service_account_file(current_app.config['GOOGLE_CLOUD_FIRESTORE_API_KEY'])
db = firestore.Client(credentials=firestore_creds)

vision_creds = service_account.Credentials.from_service_account_file(current_app.config['GOOGLE_CLOUD_VISION_API_KEY'])
vision_client = vision.ImageAnnotatorClient(credentials=vision_creds)  # Initialize Vision client

openai.api_key = current_app.config['OPENAI_API_KEY']
chat_client = openai.chat._client
mod_client = openai.moderation._client


