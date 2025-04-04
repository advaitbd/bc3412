# analysis/parser.py
import json
import logging
import re # Keep re for boolean cleaning

def parse_gemini_output(response_text):
    """
    Parse the structured JSON output from Gemini.
    Handles new target fields and flattens Action Classifications/Justifications.
    """
    if not response_text or not response_text.strip():
         logging.warning("Received empty response text for parsing.")
         # Return a dictionary with expected keys but default "Not Mentioned" or None values
         # This helps ensure the dataframe has consistent columns later
         return {
             "Executive Summary": "Not Mentioned",
             "Strategic Priorities (Energy Transition)": "Not Mentioned",
             "Financial Commitments (Energy Transition)": "Not Mentioned",
             "Identified Risks (Physical and Transition)": "Not Mentioned",
             "Emission targets": "Not Mentioned", # Default value for new field
             "Target Year": "Not Mentioned",     # Default value for new field
             "Scope coverage": "Not Mentioned",  # Default value for new field
             "Base Year": "Not Mentioned",       # Default value for new field
             "Interim Targets": "Not Mentioned", # Default value for new field
             "Countries of Operation": "Not Mentioned",
             "Renewables": False,
             "Energy Efficiency": False,
             "Electrification": False,
             "Bioenergy": False,
             "CCUS": False,
             "Hydrogen Fuel": False,
             "Behavioral Changes": False,
             # Add default empty strings for justifications
             "Renewables_Justification": "",
             "Energy Efficiency_Justification": "",
             "Electrification_Justification": "",
             "Bioenergy_Justification": "",
             "CCUS_Justification": "",
             "Hydrogen Fuel_Justification": "",
             "Behavioral Changes_Justification": "",
         }

    # --- Attempt to extract JSON even if surrounded by other text ---
    # Simple extraction: find first '{' and last '}'
    json_start = response_text.find('{')
    json_end = response_text.rfind('}')
    if json_start != -1 and json_end != -1 and json_end > json_start:
        json_str = response_text[json_start : json_end + 1]
    else:
        # Fallback: maybe the whole thing is JSON?
        json_str = response_text.strip()
        # Basic check if it looks like JSON before attempting parse
        if not (json_str.startswith('{') and json_str.endswith('}')):
             logging.error("Response does not appear to be JSON: %s", response_text[:200] + "...")
             return parse_gemini_output("") # Return default structure on format error


    try:
        # Use strict=False maybe? No, better to fail on invalid JSON.
        data = json.loads(json_str)
        logging.info("Successfully parsed Gemini output as JSON.")

        # --- Flatten Action Classifications ---
        if "Action Classifications" in data and isinstance(data["Action Classifications"], dict):
            action_classifications = data.pop("Action Classifications")
            for action, classification in action_classifications.items():
                # Robust boolean conversion
                clean_value = str(classification).strip().upper().replace('[','').replace(']','')
                data[action] = clean_value == "TRUE"
            logging.debug(f"Flattened action classifications.")
        else:
            logging.warning("No 'Action Classifications' dict found in Gemini output. Action booleans might be missing.")
            # Add default False values if missing
            from config.settings import ACTION_CATEGORIES
            for action in ACTION_CATEGORIES:
                 if action not in data: data[action] = False


        # --- Flatten Action Justifications ---
        if "Action Justifications" in data and isinstance(data["Action Justifications"], dict):
            action_justifications = data.pop("Action Justifications")
            for justification_key, text in action_justifications.items():
                 # Ensure justification text is stored, even if empty
                 data[justification_key] = str(text) if text else "" # Store as string
            logging.debug(f"Flattened action justifications.")
        else:
            logging.warning("No 'Action Justifications' dict found in Gemini output.")
             # Add default empty strings if missing
            from config.settings import ACTION_CATEGORIES
            for action in ACTION_CATEGORIES:
                 j_key = f"{action}_Justification"
                 if j_key not in data: data[j_key] = ""


        # --- Ensure new target fields exist (with default if missing from JSON) ---
        # This handles cases where Gemini might omit a field entirely if "Not Mentioned"
        target_fields = ["Emission targets", "Target Year", "Scope coverage", "Base Year", "Interim Targets"]
        for field in target_fields:
            if field not in data:
                logging.warning(f"Field '{field}' missing in Gemini JSON output, defaulting to 'Not Mentioned'.")
                data[field] = "Not Mentioned"
            elif data[field] is None: # Handle explicit nulls
                 data[field] = "Not Mentioned"


        return data

    except json.JSONDecodeError as e:
        logging.error("JSONDecodeError while parsing Gemini response: %s", e)
        logging.error("Problematic text snippet: %s", json_str[:500] + "...") # Log part of the text that failed
        return parse_gemini_output("") # Return default structure on parse error
    except Exception as e:
        logging.error("Unexpected error while parsing Gemini response: %s", e, exc_info=True)
        return parse_gemini_output("") # Return default structure on other errors
