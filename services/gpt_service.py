import openai
from utils.gpt_output import parse_gpt_output
from utils.prompt_template import build_prompt, build_regeneration_prompt
from utils.validation import validate_and_normalize_output, classify_confidence, spurs_to_regenerate
from utils.trait_manager import infer_tone, infer_situation
from .clients import chat_client
from flask import current_app
from utils.logger import setup_logger




def generate_spurs(valid_spurs, conversation, user_profile, connection_profile, situation=None, topic=None):
    """
    Main GPT call wrapper: builds prompt, validates output, applies filters.
    Includes retry logic with safety fallback.
    """
    tone = None
    tone_info = infer_tone(conversation[-1]) 
    tone_confidence = classify_confidence(tone_info["confidence"])
    if tone_confidence in ["high"]:
        tone = tone_info["tone"]
    
    if situation is None:
        situation_info = infer_situation(conversation)
        situation_confidence = classify_confidence(situation_info["confidence"])
        if situation_confidence in ["high"]:
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
    
    fallback_response = "\n".join(
        f"{idx + 1}. {current_app.config['SPUR_VARIANTS'][v]}: We're having trouble generating something right now. Please try your request again."
        for idx, v in enumerate(valid_spurs)
    )
    
    for attempt in range(3):  # 1 initial + 2 retries
        try:
            current_prompt = prompt + fallback_prompt_suffix if attempt > 0 else prompt

            response = chat_client.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": current_prompt}],
                temperature=0.75 if attempt == 0 else 0.6,
                max_tokens=600,
            )

            raw_output = response.get('choices', [{}])[0].get('message', {}).get('content','')
            gpt_parsed_filtered_output = parse_gpt_output(raw_output)
            
            spur_redos = spurs_to_regenerate(gpt_parsed_filtered_output)

            if spur_redos:
                regenerated_output=generate_spurs(spur_redos, conversation, user_profile, connection_profile, situation, topic)
                gpt_parsed_filtered_output.update(regenerated_output)

            
            validated_output, fallback_flags = validate_and_normalize_output(gpt_parsed_filtered_output)
            return validated_output, fallback_flags

        except Exception as e:
            logger = setup_logger(name="gpt_service_log.file", toFile=True, filename="gpt_service.log")
            logger.error("GPT generation failed: %s", str(e))
            if attempt == 2:
                return fallback_response
            continue


            