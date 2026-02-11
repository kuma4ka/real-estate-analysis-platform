import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { Property } from '../types/property';
import { useTranslation } from 'react-i18next';
import L from 'leaflet';

// Fix for default Leaflet marker icons in React
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

interface MapComponentProps {
    properties: Property[];
}

const MapComponent: React.FC<MapComponentProps> = ({ properties }) => {
    const { t } = useTranslation();
    
    // Default center (Kyiv)
    const position: [number, number] = [50.4501, 30.5234];

    // Filter properties that have valid coordinates (mock logic for now if coordinates aren't real)
    // NOTE: Real implementation needs lat/lng in Property interface. 
    // Assuming for now we might need to mock or use existing fields if hidden.
    // Since current Property interface doesn't have lat/lng, we will skip rendering markers 
    // until backend provides them, OR mock them for demonstration if they are missing.
    
    // TEMPORARY: Mock coordinates for demo purposes based on property ID
    // Using useMemo to ensure stability during re-renders
    const propertiesWithCoords = React.useMemo(() => properties.map(p => {
        // pseudo-random based on id to be deterministic
        const pseudoRandom = (seed: number) => {
            const x = Math.sin(seed++) * 10000;
            return x - Math.floor(x);
        };
        
        return {
            ...p,
            lat: 50.4501 + (pseudoRandom(p.id) - 0.5) * 0.1,
            lng: 30.5234 + (pseudoRandom(p.id + 1000) - 0.5) * 0.1
        };
    }), [properties]);

    return (
        <MapContainer center={position} zoom={11} scrollWheelZoom={false} className="h-full w-full rounded-xl z-0">
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {propertiesWithCoords.map((property) => (
                <Marker key={property.id} position={[property.lat, property.lng]}>
                    <Popup>
                        <div className="min-w-[200px]">
                            <h3 className="font-bold text-sm mb-1">{property.title}</h3>
                            <p className="text-primary font-bold">
                                {new Intl.NumberFormat('uk-UA', { style: 'currency', currency: property.currency || 'USD', maximumFractionDigits: 0 }).format(property.price)}
                            </p>
                            <div className="text-xs text-gray-500 mt-1">
                                {property.rooms} {t('rooms')} • {property.area} м²
                            </div>
                            <a href={property.source_url} target="_blank" rel="noopener noreferrer" className="block text-center mt-2 text-xs bg-primary text-white py-1 rounded">
                                {t('more_details')}
                            </a>
                        </div>
                    </Popup>
                </Marker>
            ))}
        </MapContainer>
    );
};

export default MapComponent;
