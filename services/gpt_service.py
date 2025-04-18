from class_defs.spur_def import Spur
from datetime import datetime, timezone
from flask import current_app
from infrastructure.clients import get_openai_client
from infrastructure.id_generator import generate_spur_id
from infrastructure.logger import get_logger
from services.connection_service import get_connection_profile, get_active_connection_firestore
from services.storage_service import get_conversation
from services.user_service import get_user_profile
from utils.gpt_output import parse_gpt_output
from utils.prompt_loader import get_system_prompt
from utils.prompt_template import build_prompt
from utils.trait_manager import infer_tone, infer_situation
from utils.validation import validate_and_normalize_output, classify_confidence, spurs_to_regenerate
import openai

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


def generate_spurs(user_id, connection_id, conversation_id, situation="", topic="", selected_spurs=None) -> list:
    """
    Generates spur responses based on the provided conversation context and profiles.
    
    Args:
        user_id: user ID
            str
        connection_ID: connection ID of connection associated with conversation.
            str
        conversation_id: conversation ID
            str
        situation: A description of the conversation's context
            str
        topic: A topic associated with the conversation
            str
        selected_spurs: list of spurs to be regenerated
            List(str)

    Returns:
        List of generated Spur objects 
    """
    user_profile = get_user_profile(user_id)
    if not selected_spurs:
        selected_spurs = user_profile['selected_spurs']
    if connection_id:
        connection_profile = get_connection_profile(user_id, connection_id)
    else:
        connection_profile = get_active_connection_firestore(user_id, connection_id)

    if conversation_id:
        conversation = get_conversation(conversation_id)
    
    if conversation and isinstance(conversation, dict):
        tone_info = infer_tone(conversation["conversation"][-1])
        if classify_confidence(tone_info["confidence"]) == "high":
            tone = tone_info["tone"]
        if not situation:
            situation_info = infer_situation(conversation.get("conversation", []))
            if classify_confidence(situation_info["confidence"]) == "high":
                situation = situation_info["situation"]

    context_block = (
        conversation,
        user_profile,
        connection_profile,
        situation,
        topic,
        tone
    )

    prompt = build_prompt(selected_spurs, *context_block)
    fallback_prompt_suffix = (
        "\nKeep all outputs safe, short, and friendly.\n"
    )
    
    fallback_response = {
        key: "We're having trouble generating something right now. Please try your request again."
        for key in current_app.config['SPUR_VARIANT_ID_KEYS'].keys()
    }
    
    for attempt in range(3):  # 1 initial + 2 retries
        try:
            current_prompt = prompt + fallback_prompt_suffix if attempt > 0 else prompt
            system_prompt = get_system_prompt()

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

            raw_output = response.choices[0].message.content if response.choices else ''
            gpt_parsed_filtered_output = parse_gpt_output(raw_output)
            validated_output = validate_and_normalize_output(gpt_parsed_filtered_output)
            
            user_id = user_profile["user_id"]

            spur_objects = []
            variant_keys = current_app.config['SPUR_VARIANT_ID_KEYS']

            for key in variant_keys.items():
                spur_text = validated_output(key)
                if spur_text:
                    spur_objects.append(Spur(
                        user_id=user_profile.get("user_id", ""),
                        spur_id=generate_spur_id(user_id),
                        conversation_id=conversation.get("conversation_id", ""),
                        connection_id=connection_profile.get("connection_id", ""),
                        situation=situation or "",
                        topic=topic or "",
                        variant=key,
                        tone=tone or "",
                        text=spur_text,
                        created_at=datetime.now(timezone.utc)
                    ))

            return spur_objects

        except openai.APIError as e: # Catch specific OpenAI errors
            logger.warning(f"[Attempt {attempt+1}] OpenAI API error during GPT generation: {e}")
            # Handle specific API errors (rate limits, auth issues) if needed
            if attempt == 2:
                 logger.error("Final GPT attempt failed due to API error.", exc_info=True)
                 # Return fallback
        except Exception as e:
            logger.warning(f"[Attempt {attempt+1}] GPT generation failed — Error: {e}", exc_info=True)
            if attempt == 2:
                logger.error("Final GPT attempt failed — returning fallback.")
                # Return fallback response (ensure fallback_response is defined)
                # return fallback_response # Example
            # continue # Go to next attempt

    # Ensure a return path if the loop finishes without success
    logger.error("All GPT generation attempts failed.")

def get_spurs_for_output(user_id: str, conversation_id: str, connection_id: str, situation: str, topic: str) -> list:
    """
        Gets spurs that are formatted and content-filtered to send to the frontend. 
        Iterative while loop structure regenerates spurs that fail content filtering
        
        **Args
            user_id: user ID
                str
            connection_ID: connection ID of connection associated with conversation.
                str
            conversation_id: conversation ID
                str
            situation: A description of the conversation's context
                str
            topic: A topic associated with the conversation
                str

        **Return
            List[Spur]: A list of generated Spur objects
    """ 
    
    user_profile = get_user_profile(user_id=user_id)
    selected_spurs = user_profile["selected_spurs"]

    spurs = generate_spurs(user_id, connection_id, conversation_id, situation, topic, selected_spurs)
    counter = 0
    max_iterations = 10

    selected_spurs = spurs_to_regenerate(spurs)

    while selected_spurs and len(selected_spurs) > 0:
        if counter >= max_iterations:
            break

        counter += 1

        fixed_spurs = generate_spurs(user_id, connection_id, conversation_id, situation, topic, selected_spurs)
        spurs = merge_spurs(spurs, fixed_spurs)
        selected_spurs = spurs_to_regenerate(spurs)

    return spurs