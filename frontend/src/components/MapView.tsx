import type { Property } from '../types/property';
import MapComponent from './MapComponent';

interface MapViewProps {
    properties: Property[];
    loaded: boolean;
}

const Spinner = () => (
    <div className="flex items-center justify-center h-full bg-surface">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent" />
    </div>
);

export default function MapView({ properties, loaded }: MapViewProps) {
    return (
        <div className="h-[calc(100vh-120px)] w-full rounded-xl overflow-hidden border border-border shadow-card">
            {loaded ? <MapComponent properties={properties} /> : <Spinner />}
        </div>
    );
}
