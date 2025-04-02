# analysis/parser.py
import json
import logging

def parse_gemini_output(response_text):
    """
    Parse the structured JSON output from Gemini.
    If the output is not valid JSON, log an error and return an empty dictionary.
    Also, flatten the "Action Classifications" nested dictionary into top-level keys
    and include justifications.
    """

    print(response_text)

    try:
        data = json.loads(response_text)
        logging.info("Successfully parsed Gemini output as JSON.")

        # Check for action classifications and flatten them into top-level keys.
        if "Action Classifications" in data:
            action_classifications = data.pop("Action Classifications")
            for action, classification in action_classifications.items():
                # If classification is a string, convert it to a boolean:
                if isinstance(classification, str):
                    data[action] = classification.strip().upper() == "TRUE"
                else:
                    data[action] = bool(classification)
            logging.debug(f"Flattened action classifications: { {k: data[k] for k in action_classifications} }")
        else:
            logging.warning("No 'Action Classifications' key found in Gemini output.")

        # Process action justifications if available
        if "Action Justifications" in data:
            action_justifications = data.pop("Action Justifications")
            for action_justification, text in action_justifications.items():
                # Add justification text to the data dictionary
                data[action_justification] = text
            logging.debug(f"Added action justifications to data dictionary")
        else:
            logging.warning("No 'Action Justifications' key found in Gemini output.")

        return data
    except json.JSONDecodeError as e:
        logging.error("JSONDecodeError while parsing Gemini response: %s", e)
        return {}
    except Exception as e:
        logging.error("Unexpected error while parsing Gemini response: %s", e)
        return {}
