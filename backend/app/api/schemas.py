from app import ma
from app.models import Property

class PropertySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Property
        load_instance = True

property_schema = PropertySchema()
properties_schema = PropertySchema(many=True)