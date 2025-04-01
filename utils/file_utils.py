# utils/file_utils.py
import os
import logging

def ensure_directory_exists(directory_path):
    """Ensure that a directory exists, creating it if necessary."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logging.info(f"Created directory: {directory_path}")
        return True
    return False

def save_text_to_file(text, file_path):
    """Save text content to a file, ensuring the directory exists."""
    directory = os.path.dirname(file_path)
    ensure_directory_exists(directory)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        logging.info(f"Text saved to: {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving text to {file_path}: {e}")
        return False

# Add this new function to utils/file_utils.py

def extract_json_from_text(text):
    """
    Extract JSON from text that might contain other content.
    Looks for content within curly braces {} that forms valid JSON.
    """
    import re
    import json

    # Try to find JSON-like structures (text between matching curly braces)
    json_pattern = r'({[\s\S]*?})'
    json_candidates = re.findall(json_pattern, text)

    # Try each candidate, from longest to shortest (assuming more complete JSON is longer)
    for candidate in sorted(json_candidates, key=len, reverse=True):
        try:
            # Attempt to parse as JSON
            json_obj = json.loads(candidate)
            return json_obj
        except json.JSONDecodeError:
            continue

    # If we need to be more aggressive, try to find the outermost curly braces
    try:
        first_brace = text.find('{')
        if first_brace >= 0:
            # Find the matching closing brace
            brace_count = 1
            for i in range(first_brace + 1, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # We found the matching brace
                        json_candidate = text[first_brace:i+1]
                        return json.loads(json_candidate)
    except:
        pass

    return None
