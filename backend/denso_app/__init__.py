from flask import Flask

from .config import Config
from .api import register_blueprints


def create_app() -> Flask:
    """
    Application factory for DENSO Forecast Suite backend.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )
    app.config.from_object(Config)
    register_blueprints(app)
    return app
