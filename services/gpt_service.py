from class_defs.conversation_def import Conversation
from class_defs.profile_def import ConnectionProfile, UserProfile
from class_defs.spur_def import Spur
from datetime import datetime, timezone
from flask import current_app
from infrastructure.clients import get_openai_client
from infrastructure.id_generator import generate_spur_id
from infrastructure.logger import get_logger
from services.connection_service import format_connection_profile, get_connection_profile, get_active_connection_firestore
from services.storage_service import get_conversation
from services.user_service import format_user_profile, get_user_profile
from utils.filters import apply_phrase_filter, apply_tone_overrides
from utils.gpt_output import parse_gpt_output
from utils.prompt_loader import load_system_prompt
from utils.prompt_template import build_prompt
from utils.trait_manager import infer_tone, infer_situation
from utils.validation import validate_and_normalize_output, classify_confidence, spurs_to_regenerate
import openai
from typing import Optional

logger = get_logger(__name__)

def merge_spurs(original_spurs: list, regenerated_spurs: list) -> list:
    """
    Replaces spurs in original_spurs with those in regenerated_spurs that share the same variant.

    Args:
        original_spurs (list of Spur): The full list of originally generated spurs.
        regenerated_spurs (list of Spur): The newly generated spurs that failed filtering and were regenerated.

    Returns:
        list of Spur: A combined list where spurs in regenerated_spurs replace matching variants in original_spurs.
    """
    regenerated_by_variant = {spur.variant: spur for spur in regenerated_spurs}
    merged_spurs = []

    for spur in original_spurs:
        if spur.variant in regenerated_by_variant:
            merged_spurs.append(regenerated_by_variant[spur.variant])
        else:
            merged_spurs.append(spur)

    return merged_spurs

def generate_spurs(
    user_id: str,
    connection_id: str,
    conversation_id: str,
    situation: str,
    topic: str,
    selected_spurs: Optional[list[str]] = None,
    profile_ocr_texts: Optional[list[str]] = None,  # New parameter
    photo_analysis_data: Optional[list[dict]] = None  # New parameter
) -> list:
    """
    Generates spur responses based on the provided conversation context and profiles.

    Args:
        user_id (str): User ID.
        connection_id (str): Connection ID of connection associated with conversation.
        conversation_id (str): Conversation ID.
        situation (str): A description of the conversation's context.
        topic (str): A topic associated with the conversation.
        selected_spurs (list[str], optional): List of spur variants to generate/regenerate.
        profile_ocr_texts (list[str], optional): List of text snippets extracted from connection's profile screenshots.
        photo_analysis_data (list[dict], optional): List of analysis results (e.g., traits) from connection's photos.

    Returns:
        List of generated Spur objects.
    """
    user_profile_dict = UserProfile.to_dict(get_user_profile(user_id)) # Renamed for clarity
    if not selected_spurs:
        selected_spurs = user_profile_dict['selected_spurs']
    
    if connection_id:
        connection_profile = get_connection_profile(user_id, connection_id)
    else:
        # Assuming get_active_connection_firestore returns a connection_id string
        active_connection_id = get_active_connection_firestore(user_id)
        connection_profile = get_connection_profile(user_id, active_connection_id)

    conversation = None
    conversation_text = ""
    if conversation_id:
        conversation_obj = get_conversation(conversation_id) # Renamed to avoid conflict with conversation var above
        if conversation_obj: # Ensure conversation_obj is not None
            conversation_text = conversation_obj.conversation_as_string()
            conversation = conversation_obj.to_dict() # Assuming to_dict() method exists and is appropriate here

    tone = ""
    # Ensure 'conversation' is a dict and has 'conversation' key before accessing
    if conversation and isinstance(conversation, dict) and "conversation" in conversation and conversation["conversation"]:
        tone_info = infer_tone(conversation["conversation"][-1])
        if classify_confidence(tone_info["confidence"]) == "high":
            tone = tone_info["tone"]
        if not situation: # Infer situation only if not provided
            situation_info = infer_situation(conversation.get("conversation", []))
            if classify_confidence(situation_info["confidence"]) == "high":
                situation = situation_info["situation"]

    # Corrected context_block construction
    context_block = "***User Profile:***\n"
    user_profile_instance = UserProfile.from_dict(user_profile_dict) # Create instance for formatting
    user_profile_text = format_user_profile(user_profile_instance)
    context_block += f"{user_profile_text}\n\n"

    context_block += "***Connection Profile:***\n"
    connection_profile_text = format_connection_profile(connection_profile) # connection_profile is already an object
    context_block += f"{connection_profile_text}\n\n"

    # Append OCR'd profile text if available
    if profile_ocr_texts:
        context_block += "***Additional Connection Profile Info (from OCR):***\n"
        for text_snippet in profile_ocr_texts:
            context_block += f"- {text_snippet}\n"
        context_block += "\n"

    # Append photo analysis if available
    if photo_analysis_data:
        context_block += "***Observations from Connection's Photos:***\n"
        for photo_data in photo_analysis_data:
            # Assuming photo_data is like {"type": "photo_analysis", "traits": ["trait1", "trait2"]}
            # And forward_full_image_to_model from utils.photo_forwarder.py returns such a dict
            if photo_data and isinstance(photo_data.get("traits"), list) and photo_data.get("traits"):
                traits_str = ", ".join(photo_data["traits"])
                context_block += f"- Inferred Traits: {traits_str}\n"
            # You could add more structured data from photo_analysis if present
        context_block += "\n"

    context_block += "***Conversation Between User and Connection:***\n"
    context_block += f"{conversation_text}\n\n"

    context_block += f"***Situation:*** {situation}\n" # Added colon for clarity
    context_block += f"***Topic:*** {topic}\n"       # Added colon for clarity
    context_block += f"***Tone:*** {tone}"           # Added colon for clarity
    
    logger.debug(f"Context block for prompt:\n{context_block}")

    prompt = build_prompt(selected_spurs or [], context_block)
    # ... (rest of the GPT call, parsing, and Spur object creation logic remains the same) ...
    # Ensure that when creating Spur objects, conversation_id is correctly retrieved:
    # conversation_id_for_spur = conversation.get("conversation_id", "") if isinstance(conversation, dict) else getattr(conversation_obj, "conversation_id", "")

    # Placeholder for the rest of the function (OpenAI call, parsing, object creation)
    # This part should largely remain the same, but ensure variables like `conversation` 
    # (used for conversation_id in Spur object) are correctly scoped and typed.
    # For example, if `conversation` is now a dict from `conversation_obj.to_dict()`:
    current_conversation_id = ""
    if conversation_obj and hasattr(conversation_obj, 'conversation_id'):
        current_conversation_id = conversation_obj.conversation_id
    elif isinstance(conversation, dict) and "conversation_id" in conversation: # Fallback if conversation_obj wasn't set but dict was
        current_conversation_id = conversation["conversation_id"]


    # ... inside the loop for spur_objects.append(Spur(...))
    # spur_id=generate_spur_id(user_profile_dict.get("user_id","")), # user_profile_dict instead of user_profile
    # conversation_id=current_conversation_id, # Use the carefully determined conversation_id

    # Fallback response and try/except loop for OpenAI API call
    fallback_prompt_suffix = (
        "\nKeep all outputs safe, short, and friendly.\n"
    )
    
    # Fallback response (ensure keys match SPUR_VARIANT_ID_KEYS)
    # This might need to be more dynamic if SPUR_VARIANT_ID_KEYS can change.
    # fallback_response_values = {
    #     key: "We're having trouble generating something right now. Please try your request again."
    #     for key in current_app.config.get('SPUR_VARIANT_ID_KEYS', {}).keys()
    # }


    for attempt in range(3):  # 1 initial + 2 retries
        try:
            current_prompt = prompt + fallback_prompt_suffix if attempt > 0 else prompt
            system_prompt = load_system_prompt()
            openai_client = get_openai_client()
            
            response = openai_client.chat.completions.create(
                model=current_app.config['AI_MODEL'],
                messages=[
                    {"role": current_app.config['AI_MESSAGES_ROLE_SYSTEM'], "content": system_prompt},
                    {"role": current_app.config['AI_MESSAGES_ROLE_USER'], "content": current_prompt}
                ],
                temperature=current_app.config['AI_TEMPERATURE_INITIAL'] if attempt == 0 else current_app.config['AI_TEMPERATURE_RETRY'],
                max_tokens=current_app.config['AI_MAX_TOKENS'],
            )

            raw_output: str = (response.choices[0].message.content or '') if response.choices else ''
            # Pass user_profile_dict to parse_gpt_output
            gpt_parsed_filtered_output = parse_gpt_output(raw_output, user_profile_dict, connection_profile.to_dict())
            validated_output = validate_and_normalize_output(gpt_parsed_filtered_output)
            
            spur_objects = []
            variant_keys = current_app.config.get('SPUR_VARIANT_ID_KEYS', {})

            for variant, _id_key in variant_keys.items():
                spur_text: str = validated_output.get(variant, "")
                if spur_text: # Ensure spur_text is not empty
                    spur_objects.append(
                        Spur(
                            user_id=user_profile_dict.get("user_id", ""), # from dict
                            spur_id=generate_spur_id(user_profile_dict.get("user_id", "")), # from dict
                            conversation_id=current_conversation_id, # Use derived ID
                            connection_id=ConnectionProfile.get_attr_as_str(connection_profile, "connection_id"),
                            situation=situation or "",
                            topic=topic or "",
                            variant=variant,
                            tone=tone or "",
                            text=spur_text,
                            created_at=datetime.now(timezone.utc),
                        )
                    )
            if spur_objects: # If any spurs were successfully created
                return spur_objects

        except openai.APIError as e:
            logger.warning(f"[Attempt {attempt+1}] OpenAI API error during GPT generation for user {user_id}: {e}")
            if attempt == 2:
                 logger.error(f"Final GPT attempt failed for user {user_id} due to API error.", exc_info=True)
        except Exception as e:
            logger.warning(f"[Attempt {attempt+1}] GPT generation failed for user {user_id} — Error: {e}", exc_info=True)
            if attempt == 2:
                logger.error(f"Final GPT attempt failed for user {user_id} — returning fallback.")
    
    logger.error(f"All GPT generation attempts failed for user {user_id}.")
    # Return an empty list or a list of fallback Spur objects if defined
    # For example, create Spur objects from fallback_response_values if it's structured correctly
    return []

def get_spurs_for_output(user_id: str, conversation_id: str, connection_id: str, situation: str, topic: str,
                         profile_ocr_texts: 'Optional[list[str]]' = None, # New parameter
                         photo_analysis_data: 'Optional[list[dict]]' = None # New parameter
                         ) -> list:
    """
    Gets spurs that are formatted and content-filtered to send to the frontend. 
    Iterative while loop structure regenerates spurs that fail content filtering.
    """ 
    user_profile = get_user_profile(user_id=user_id)
    selected_spurs_from_profile = user_profile.to_dict().get("selected_spurs", []) # Ensure it's a list

    # Initial generation
    spurs = generate_spurs(user_id, connection_id, conversation_id, situation, topic, selected_spurs_from_profile,
                           profile_ocr_texts=profile_ocr_texts, # Pass through
                           photo_analysis_data=photo_analysis_data) # Pass through
    
    counter = 0
    max_iterations = 10 # Consider making this configurable

    # Iterative regeneration for spurs that fail validation/filtering
    spurs_needing_regeneration = spurs_to_regenerate(spurs) # This function returns list of variants (strings)

    while spurs_needing_regeneration and counter < max_iterations:
        counter += 1
        logger.info(f"Regeneration attempt {counter} for user {user_id}, variants: {spurs_needing_regeneration}")
        
        fixed_spurs = generate_spurs(user_id, connection_id, conversation_id, situation, topic, spurs_needing_regeneration, # Pass only variants to regenerate
                                     profile_ocr_texts=profile_ocr_texts, # Pass context again
                                     photo_analysis_data=photo_analysis_data)
        spurs = merge_spurs(spurs, fixed_spurs)
        spurs_needing_regeneration = spurs_to_regenerate(spurs)

    if counter >= max_iterations and spurs_needing_regeneration:
        logger.warning(f"Max regeneration attempts reached for user {user_id}. Some spurs may not meet quality standards.")

    return spurs