import os
import logging
from google import genai
from google.genai import types
from config.settings import GEMINI_MODEL_NAME

def configure_gemini(api_key=None):
    """
    Configure the Gemini client using the new google.genai package.
    Returns a tuple (client, model) for use throughout the application.
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY not provided in environment.")
        raise ValueError("Missing GEMINI_API_KEY.")
    client = genai.Client(api_key=api_key)
    model = GEMINI_MODEL_NAME
    logging.info(f"Configured Gemini client with model: {model}")
    return client, model

def get_gemini_response(prompt, client, model):
    """
    Generate a structured response from Gemini using the new streaming API.
    The response is streamed in JSON format.
    """
    try:
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        ]
        config = types.GenerateContentConfig(temperature=0,response_mime_type="application/json")
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config,
        ):
            response_text += chunk.text
        logging.info("Received response from Gemini.")
        return response_text
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return None
