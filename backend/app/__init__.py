from flask import Flask
from config import Config
from .core.db import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from .api import routes
    app.register_blueprint(routes.bp)

    @app.route('/')
    def index():
        return {"message": "Real Estate Monitor API is running inside Docker!"}

    return app