import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-markercluster';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
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

const UKRAINE_CENTER: [number, number] = [48.5, 31.0];

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

    // Only show properties with REAL coordinates — no fake/generated coords
    const validProperties = React.useMemo(
        () => properties.filter(p => p.lat && p.lng),
        [properties]
    );

    const markers = React.useMemo(
        () => validProperties.map(p => ({ lat: p.lat!, lng: p.lng! })),
        [validProperties]
    );

    return (
        <MapContainer center={UKRAINE_CENTER} zoom={6} scrollWheelZoom={true} className="h-full w-full rounded-xl z-0">
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <FitBounds markers={markers} />

            <MarkerClusterGroup
                chunkedLoading
                maxClusterRadius={50}
                spiderfyOnMaxZoom
                showCoverageOnHover={false}
            >
                {validProperties.map((property) => (
                    <Marker key={property.id} position={[property.lat!, property.lng!]}>
                        <Popup>
                            <div className="min-w-[200px]">
                                <h3 className="font-bold text-sm mb-1">{property.title}</h3>
                                <p className="text-primary font-bold">
                                    {new Intl.NumberFormat('uk-UA', { style: 'currency', currency: property.currency || 'USD', maximumFractionDigits: 0 }).format(property.price)}
                                </p>
                                <div className="text-xs text-gray-500 mt-1">
                                    {property.city}
                                    {property.rooms ? ` • ${property.rooms} ${t('rooms')}` : ''}
                                    {property.area ? ` • ${property.area} ${t('area_unit')}` : ''}
                                </div>
                                <a href={property.source_url} target="_blank" rel="noopener noreferrer" className="block text-center mt-2 text-xs bg-primary text-white py-1 rounded">
                                    {t('more_details')}
                                </a>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MarkerClusterGroup>
        </MapContainer>
    );
};

export default MapComponent;
