from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from config import Config

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
limiter = Limiter(key_func=get_remote_address)
cache = Cache()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # Before Request Hook for metrics
    from app.core.metrics import record_request
    @app.before_request
    def before_request_hook():
        record_request()

    # Ensure models are loaded for Alembic/SQLAlchemy
    __import__('app.models')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

    from app.api.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')

    from app.cli import (
        scrape_meget_command,
        scrape_bon_ua_command,
        regeocode_all_command,
        regeocode_ids_command,
        backfill_images,
        convert_currencies_command,
        rescrape_duplicates_command,
        purge_stale_command,
        purge_tokens_command,
        seed_users_command
    )
    app.cli.add_command(scrape_meget_command)
    app.cli.add_command(scrape_bon_ua_command)
    app.cli.add_command(regeocode_all_command)
    app.cli.add_command(regeocode_ids_command)
    app.cli.add_command(backfill_images)
    app.cli.add_command(convert_currencies_command)
    app.cli.add_command(rescrape_duplicates_command)
    app.cli.add_command(purge_stale_command)
    app.cli.add_command(purge_tokens_command)
    app.cli.add_command(seed_users_command)

    return app