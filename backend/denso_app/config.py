import os


class Config:
    """Basic config; can be extended for Dev/Prod."""

    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "denso_forecast")
    DB_USER = os.getenv("DB_USER", "denso")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
