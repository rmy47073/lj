from flask import Flask
from flask_cors import CORS
from app.routes import api_bp
from app.config.config import Config


def create_app():
    """
    Create Flask app instance
    :return: Flask
    """
    app = Flask(__name__)
    CORS(app)  # enable CORS
    app.config.from_object(Config)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app