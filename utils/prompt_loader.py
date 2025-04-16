from flask import current_app
def load_system_prompt() -> str:
	"""
	Gets the system prompt used to prime the model

	Args
		N/A
	Return
		system_prompt: system prompt for model
			str

 	"""

	system_prompt_path = current_app.config['SPURLY_SYSTEM_PROMPT_PATH']

	with open("system_prompt_path", "r") as f:
		return f.read().strip()