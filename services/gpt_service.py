import openai
from utils.gpt_output import parse_gpt_output
from utils.prompt_template import build_prompt
from utils.validation import validate_and_normalize_output, classify_confidence, spurs_to_regenerate
from utils.trait_manager import infer_tone, infer_situation
from infrastructure.clients import chat_client
from flask import current_app
from infrastructure.logger import get_logger
from class_defs.spur_def import Spur
from datetime import datetime
from uuid import uuid4
from services.user_service import get_user_profile
from services.connection_service import get_connection_profile
from services.storage_service import get_conversation
from services.user_service import get_user_profile

logger = get_logger(__name__)

def merge_spurs(original_spurs, regenerated_spurs):
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


def generate_spurs(user_profile, selected_spurs, connection_profile=None, conversation=None, situation="", topic="") -> dict:
    """
    Generates spur responses based on the provided conversation context and profiles.
    
    Parameters:
        user_profile (dict or UserProfile): Data for the user's profile.
        connection_profile (dict or ConnectionProfile or None): Data for the connection's profile.
        conversation (dict or Conversation): The conversation text.
        situation (str): A description of the conversation's context.
        topic (str): A topic associated with the conversation.
        
        
    Returns:
        List of generated Spur objects 
    """

    if conversation and isinstance(conversation, dict) and conversation.get("conversation"):
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

            response = chat_client.completions.create(
                model=current_app.config['AI_MODEL'],
                messages=[{"role": current_app.config['AI_MESSAGES_ROLE_SYSTEM'], "content": current_prompt}],
                temperature=current_app.config['AI_TEMPERATURE_INITIAL'] if attempt == 0 else current_app.config['AI_TEMPERATURE_RETRY'],
                max_tokens=current_app.config['AI_MAX_TOKENS'],
            )

            raw_output = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            gpt_parsed_filtered_output = parse_gpt_output(raw_output)
            validated_output = validate_and_normalize_output(gpt_parsed_filtered_output)
            
            user_id = user_profile["user_id"]

            spur_id_base = str(uuid4().hex[:7])
            spur_objects = []
            variant_keys = current_app.config['SPUR_VARIANT_ID_KEYS']

            for key, suffix in variant_keys.items():
                spur_text = validated_output(key)
                if spur_text:
                    spur_objects.append(Spur(
                        user_id=user_profile.get("user_id", ""),
                        spur_id=f"{user_id}:{spur_id_base}{suffix}",
                        conversation_id=conversation.get("conversation_id", ""),
                        connection_id=connection_profile.get("connection_id", ""),
                        situation=situation or "",
                        topic=topic or "",
                        variant=key,
                        tone=tone or "",
                        text=spur_text,
                        created_at=datetime.utcnow()
                    ))

            return spur_objects

        except Exception as e:
            logger.warning(f"[Attempt {attempt}] GPT generation failed — Error: {e}")
            if attempt == 2:
                logger.error(f"[{__package__ or __name__}] Final GPT attempt failed — returning fallback.")
                return fallback_response
            continue

def get_spurs_for_output(user_id, conversation_id) -> dict:
    """
        Gets spurs that are formatted and content-filtered to send to the frontend. 
        Iterative while loop structure regenerates spurs that fail content filtering
        
            **Args
                user_id: user id in current context 
                    (string)
                conversation_id: conversation id in current context
                    (string)
            **Return
                Tuple[List[Spur], dict]: A tuple where the first element is a list of generated Spur objects and the second element is a dict of fallback flags or additional information.
    """ 
    null_connection_suffix = current_app.config['NULL_CONNECTION_ID']
    connection_profile = None
    conversation = None
    situation = ""
    topic = ""
    
    user_profile = get_user_profile(user_id=user_id)
    conversation = get_conversation(conversation_id=conversation_id)    
    connection_id = conversation["connection_id"]
    if connection_id and not connection_id.endswith(null_connection_suffix):
        connection_profile = get_connection_profile(connection_id=connection_id)
    
    situation = conversation["situation"]
    topic = conversation["topic"]
    
    selected_spurs = user_profile["selected_spurs"]
    
    spurs = generate_spurs(user_profile, selected_spurs, connection_profile, conversation, situation, topic)
    counter = 0
    max_iterations = 10
    
    spurs_to_fix = spurs_to_regenerate(spurs)
    
    while spurs_to_fix:
        if counter >= max_iterations:
            break
        
        counter += 1
    
        fixed_spurs = generate_spurs(user_profile, spurs_to_fix, connection_profile, conversation, situation, topic)
        spurs = merge_spurs(spurs, fixed_spurs)
    
    return spurs