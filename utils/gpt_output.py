import json
from .filters import apply_phrase_filter, apply_tone_overrides
from .logger import get_logger
from flask import current_app


def parse_gpt_output(gpt_response: str, user_sketch: dict, poi_sketch: dict) -> dict:
    """
    Parse GPT response into usable SPUR variants with safety filtering and fallbacks.
    """
    try:
        # Step 1: Sanitize and parse JSON-like GPT output
        cleaned = gpt_response.strip('`\n ').replace("```json", "").replace("```", "")
        parsed = json.loads(cleaned)

        # Step 2: Check all expected fields are present
        spur_keys = current_app.config["SPUR_VARIANTS"]
        for key in spur_keys:
            fallback = parsed.get("warm_spur") or parsed.get("spur") or ""
            parsed[key] = fallback

        # Step 3: Apply phrase filter and sanitization
        safe_output = apply_phrase_filter(parsed)
        sanitized_output = apply_tone_overrides(safe_output, user_sketch, poi_sketch)

        warm_fallback = sanitized_output.get("warm_spur")
        fallback_flags = {
            key: warm_fallback and sanitized_output[key] == warm_fallback and key != "warm_spur"
            for key in sanitized_output
        }
        
        get_logger().info({
            "event": "spurly_generation_log",
            "fallback_flags": fallback_flags,
            "input_sketch_summary": {
                "user_tone": user_sketch.get("tone"),
                "poi_flirt": poi_sketch.get("flirt_level"),
                "poi_drinking": poi_sketch.get("drinking"),
            },
            "filter_hits": [k for k, v in fallback_flags.items() if v],
        })

        return sanitized_output

    except (json.JSONDecodeError, TypeError) as e:
        # Log error here
        return {
            "main_spur": "",
            "warm_spur": "",
            "cool_spur": "",
            "playful_spur": ""
        }
