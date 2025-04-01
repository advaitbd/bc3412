# utils/logging_utils.py
import logging

def setup_logging(debug=False):
    """Configure logging for the application."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.debug("Logging initialized.")
    return logger
