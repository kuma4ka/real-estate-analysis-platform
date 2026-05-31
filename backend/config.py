import os
import sys
import secrets

from dotenv import load_dotenv

# Load .env from the project root
root_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(root_env_path)

_is_unprotected_env = (
    os.getenv('FLASK_DEBUG') in ('1', 'true', 'True')
    or os.getenv('CI') == 'true'
    or 'pytest' in sys.modules
)


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        if not _is_unprotected_env:
            raise ValueError("SECRET_KEY environment variable is not set!")
        # Generate a random key per process rather than using a hardcoded literal.
        # Tokens won't survive restarts in dev/test, which is acceptable.
        SECRET_KEY = secrets.token_hex(32)

    _DATABASE_URL = os.getenv('DATABASE_URL')
    if not _DATABASE_URL:
        if not _is_unprotected_env:
            raise ValueError("DATABASE_URL environment variable is not set!")
        _DATABASE_URL = 'sqlite:///dev.db'

    SQLALCHEMY_DATABASE_URI = _DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', os.getenv('RATELIMIT_STORAGE_URL', 'memory://'))

    CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache')
    _ratelimit_url = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    CACHE_REDIS_URL = os.getenv(
        'CACHE_REDIS_URL',
        _ratelimit_url if _ratelimit_url.startswith('redis') else 'redis://localhost:6379/0',
    )
    CACHE_DEFAULT_TIMEOUT = 600
    CACHE_KEY_PREFIX = 'reap_'


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CACHE_TYPE = 'SimpleCache'