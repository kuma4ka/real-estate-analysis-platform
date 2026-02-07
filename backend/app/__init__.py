from flask import Flask
from sqlalchemy import text
from config import Config
from .core.db import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    from .api import routes
    app.register_blueprint(routes.bp)

    @app.route('/')
    def index():
        return {"message": "Real Estate Monitor API is running"}

    @app.route('/db-test')
    def db_test():
        try:
            return {"database_url_configured": bool(app.config['SQLALCHEMY_DATABASE_URI'])}
        except Exception as e:
            return {"error": str(e)}, 500

    return app