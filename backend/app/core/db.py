from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Ініціалізація об'єкта DB
db = SQLAlchemy(model_class=Base)