from flask import Flask, render_template
from flask_cors import CORS
from app.routes import api_bp
from app.config.config import Config


def create_app():
    """
    Create Flask app instance
    :return: Flask
    """
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    CORS(app)  # enable CORS
    app.config.from_object(Config)
    app.register_blueprint(api_bp, url_prefix='/api')

    # 添加主页面路由
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
