import json
from flask import current_app
from .logger import setup_logger

def build_prompt(selected_spurs: list[str], context_block: str) -> str:
    try:
        """
        Constructs the dynamic GPT prompt using system rules + conversation context.
        """
        system_prompt = open(current_app.config['SPURLY_SYSTEM_PROMPT'].read())

        valid_spurs = [v for v in selected_spurs if v in current_app.config['SPUR_VARIANT_DESCRIPTIONS']]
        if not valid_spurs:
            raise ValueError("No valid SPUR variants selected.")
        
        spur_instructions = "\n".join(
            f"{idx + 1}. {current_app.config['SPUR_VARIANT_DESCRIPTIONS'][v]}"
            for idx, v in enumerate(valid_spurs)
        )

        json_output_structure = "{\n" + ",\n".join(f'  "{v}": "..."' for v in valid_spurs) + "\n}"

        # Final prompt
        return f"""### Instructions
            Please generate SPURs suggested for Party A to say to Party B based on the context below. There should be one spur that reflects each of the following {len(valid_spurs)} tones:

            {spur_instructions}

            Avoid repeating the original messages. Each spur should feel distinct in tone and language, with the tone and language being reflective of the context. Each message should sound as though it naturally came from Party A, given the context below regarding Party A and what is known about Party B.

            Respond in JSON with this format:
            {json_output_structure}

            ### Context
            {context_block}
            """
    except Exception as e:
        logger = setup_logger(name="prompt_template_log.file", toFile=True, filename="prompt_template.log")
        logger.error("tils.prompt_template.build_prompt error: %s", e)  
        raise e
