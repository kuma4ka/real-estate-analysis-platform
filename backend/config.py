import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        import sys
        # Bypass check in debug, CI, or local pytest environments
        if os.getenv('FLASK_DEBUG') not in ('1', 'true', 'True') and os.getenv('CI') != 'true' and "pytest" not in sys.modules:
            raise ValueError("SECRET_KEY environment variable is not set!")
        SECRET_KEY = 'default-dev-key'

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'