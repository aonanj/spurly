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
import uuid
from services.user_service import get_user_profile
from services.connection_service import get_connection_profile
from services.storage_service import get_conversation

logger = get_logger(__name__)

def generate_spurs(spur_objects: list[Spur]) -> dict:
    if not spur_objects:
        return {}

    # Assume all spur_objects share the same metadata
    seed_spur = spur_objects[0]

    user_id = seed_spur.user_id
    connection_id = seed_spur.connection_id
    conversation_id = seed_spur.conversation_id

    user_profile = get_user_profile(user_id)
    connection_profile = get_connection_profile(user_id, connection_id) if connection_id else {}
    conversation = get_conversation(user_id, conversation_id) if conversation_id else {}

    situation = seed_spur.situation
    topic = seed_spur.topic

    tone = None
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

    prompt = build_prompt(*context_block)
    fallback_prompt_suffix = (
        "\nKeep all outputs safe, short, and friendly.\n"
    )
    
    fallback_response = {
        key: "We're having trouble generating something right now. Please try your request again."
        for key in current_app.config["SPUR_VARIANT_ID_KEYS"].keys()
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

            spur_id_base = str(uuid.uuid4())
            spur_objects = []
            variant_keys = current_app.config['SPUR_VARIANT_ID_KEYS']

            for key, prefix in variant_keys.items():
                spur_text = gpt_parsed_filtered_output.get(key)
                if spur_text:
                    spur_objects.append(Spur(
                        user_id=user_profile.get("user_id", ""),
                        spur_id=f"{prefix}-{spur_id_base}",
                        conversation_id=conversation.get("conversation_id", ""),
                        connection_id=connection_profile.get("connection_id", ""),
                        situation=situation or "",
                        topic=topic or "",
                        variant=key,
                        tone=tone or "",
                        text=spur_text,
                        created_at=datetime.utcnow()
                    ))
            
            # Backfill text field for older spur entries if missing
            for spur in spur_objects:
                if not spur.text:
                    spur.text = gpt_parsed_filtered_output.get(spur.variant, "")

            spur_redos = spurs_to_regenerate(spur_objects)

            if spur_redos:
                regenerated_output = generate_spurs(spur_redos)
                gpt_parsed_filtered_output.update(regenerated_output)

            validated_output, fallback_flags = validate_and_normalize_output(gpt_parsed_filtered_output)
            return validated_output, fallback_flags

        except Exception as e:
            logger.warning(f"[Attempt {attempt}] GPT generation failed for user {user_id} — Error: {e}")
            if attempt == 2:
                logger.error(f"[{__package__ or __name__}] Final GPT attempt failed — returning fallback.")
                return fallback_response
            continue