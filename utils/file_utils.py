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
