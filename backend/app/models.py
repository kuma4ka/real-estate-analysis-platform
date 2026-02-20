from datetime import datetime
from app import db


class Property(db.Model):
    __tablename__ = 'properties'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), default="USD")

    address = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    geocode_precision = db.Column(db.String(20), nullable=True)

    area = db.Column(db.Float, nullable=True)
    rooms = db.Column(db.Integer, nullable=True)
    floor = db.Column(db.Integer, nullable=True)

    source_url = db.Column(db.Text, unique=True, nullable=False)
    source_website = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=True)
    images = db.Column(db.JSON, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Property {self.id} - {self.title[:20]}...>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'address': self.address,
            'lat': self.latitude,
            'lng': self.longitude,
            'area': self.area,
            'rooms': self.rooms,
            'url': self.source_url,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }