import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { Property } from '../types/property';
import { useTranslation } from 'react-i18next';
import L from 'leaflet';

import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const CITY_COORDINATES: Record<string, [number, number]> = {
    'Київ': [50.4501, 30.5234],
    'Kyiv': [50.4501, 30.5234],
    'Львів': [49.8397, 24.0297],
    'Lviv': [49.8397, 24.0297],
    'Одеса': [46.4825, 30.7233],
    'Odesa': [46.4825, 30.7233],
    'Харків': [49.9935, 36.2304],
    'Kharkiv': [49.9935, 36.2304],
    'Дніпро': [48.4647, 35.0462],
    'Dnipro': [48.4647, 35.0462],
    'Default': [50.4501, 30.5234]
};

// Component to fit bounds to markers
const FitBounds: React.FC<{ markers: { lat: number; lng: number }[] }> = ({ markers }) => {
    const map = useMap();

    useEffect(() => {
        if (markers.length > 0) {
            const bounds = L.latLngBounds(markers.map(m => [m.lat, m.lng]));
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [map, markers]);

    return null;
};

interface MapComponentProps {
    properties: Property[];
}

const MapComponent: React.FC<MapComponentProps> = ({ properties }) => {
    const { t } = useTranslation();
    
    // Mock coordinates based on City
    const propertiesWithCoords = React.useMemo(() => properties.map(p => {
        // pseudo-random based on id to be deterministic
        const pseudoRandom = (seed: number) => {
            const x = Math.sin(seed++) * 10000;
            return x - Math.floor(x);
        };
        
        const cityKey = Object.keys(CITY_COORDINATES).find(key => 
            p.city && p.city.includes(key)
        ) || 'Default';

        const [baseLat, baseLng] = CITY_COORDINATES[cityKey];

        return {
            ...p,
            lat: baseLat + (pseudoRandom(p.id) - 0.5) * 0.1,
            lng: baseLng + (pseudoRandom(p.id + 1000) - 0.5) * 0.1
        };
    }), [properties]);

    return (
        <MapContainer center={CITY_COORDINATES['Kyiv']} zoom={6} scrollWheelZoom={true} className="h-full w-full rounded-xl z-0">
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            <FitBounds markers={propertiesWithCoords} />

            {propertiesWithCoords.map((property) => (
                <Marker key={property.id} position={[property.lat, property.lng]}>
                    <Popup>
                        <div className="min-w-[200px]">
                            <h3 className="font-bold text-sm mb-1">{property.title}</h3>
                            <p className="text-primary font-bold">
                                {new Intl.NumberFormat('uk-UA', { style: 'currency', currency: property.currency || 'USD', maximumFractionDigits: 0 }).format(property.price)}
                            </p>
                            <div className="text-xs text-gray-500 mt-1">
                                {property.city}
                                {property.rooms ? ` • ${property.rooms} ${t('rooms')}` : ''}
                                {property.area ? ` • ${property.area} м²` : ''}
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
