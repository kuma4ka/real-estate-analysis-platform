from app import ma
from app.models import Property


class PropertySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Property
        load_instance = True
        fields = (
            'id', 'title', 'price', 'currency',
            'address', 'latitude', 'longitude', 'city', 'district',
            'geocode_precision', 'area', 'rooms', 'floor',
            'images', 'source_url', 'is_active', 'created_at',
        )


property_schema = PropertySchema()
properties_schema = PropertySchema(many=True)