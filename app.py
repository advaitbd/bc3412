from web import create_app
from utils.logging_utils import setup_logging

# Set up logging
logger = setup_logging()

# Create Flask app
app = create_app()

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=True)
