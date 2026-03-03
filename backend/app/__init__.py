from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    limiter.init_app(app)



    # Ensure models are loaded for Alembic/SQLAlchemy
    __import__('app.models')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

    from app.api.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')

    from app.commands import (
        scrape_meget_command, 
        scrape_bon_ua_command, 
        regeocode_all_command, 
        regeocode_ids_command, 
        backfill_images,
        convert_currencies_command,
        rescrape_duplicates_command,
        seed_users_command
    )
    app.cli.add_command(scrape_meget_command)
    app.cli.add_command(scrape_bon_ua_command)
    app.cli.add_command(regeocode_all_command)
    app.cli.add_command(regeocode_ids_command)
    app.cli.add_command(backfill_images)
    app.cli.add_command(convert_currencies_command)
    app.cli.add_command(rescrape_duplicates_command)
    app.cli.add_command(seed_users_command)

    return app