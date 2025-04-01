# data/savers.py
import os
import logging
from utils.file_utils import ensure_directory_exists

def save_enhanced_data(df, output_path):
    """Save the enhanced DataFrame to a CSV file."""
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        ensure_directory_exists(output_dir)

        df.to_csv(output_path, index=False, encoding='utf-8')
        logging.info(f"Enhanced dataset successfully saved to {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving data to {output_path}: {e}")
        raise
