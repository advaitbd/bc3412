from flask import Flask
import os
from pathlib import Path

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['UPLOAD_FOLDER'] = os.path.join(Path(__file__).parent.parent, 'annual_reports')
    app.config['OUTPUT_FOLDER'] = os.path.join(Path(__file__).parent.parent, 'outputs')

    # Ensure directories exist
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        os.makedirs(folder, exist_ok=True)

    # Register routes
    from web.routes import main_bp
    app.register_blueprint(main_bp)

    return app
