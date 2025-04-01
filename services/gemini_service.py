# services/gemini_service.py
import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from config.settings import GEMINI_MODEL_NAME

def load_config():
    """Load API key configuration."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logging.error("GOOGLE_API_KEY not found in environment variables or .env file.")
        raise ValueError("API Key not configured.")
    logging.info("API Key loaded successfully.")
    return api_key

def configure_gemini(api_key=None):
    """Configure and return the Gemini client."""
    if not api_key:
        api_key = load_config()

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        logging.info(f"Gemini client configured with model: {GEMINI_MODEL_NAME}")
        return model
    except Exception as e:
        logging.error(f"Failed to configure Gemini: {e}")
        raise

def get_gemini_response(prompt, model):
    """Get a response from the Gemini API."""
    try:
        logging.info("Sending request to Gemini...")
        response = model.generate_content(prompt)
        logging.info("Received response from Gemini.")

        # Handle potential safety blocks or empty responses
        if not response.parts:
            logging.warning("Gemini returned no content. Possible safety block or empty generation.")
            return None

        return response.text
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return None
