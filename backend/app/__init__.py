from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from config import Config

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    from app import models

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    from app.commands import scrape_command, regeocode_all_command, regeocode_ids_command, backfill_images
    app.cli.add_command(scrape_command)
    app.cli.add_command(regeocode_all_command)
    app.cli.add_command(regeocode_ids_command)
    app.cli.add_command(backfill_images)

    return app