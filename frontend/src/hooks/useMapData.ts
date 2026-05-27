import { useEffect, useState } from 'react';
import type { Property } from '../types/property';

export function useMapData(active: boolean) {
    const [mapProperties, setMapProperties] = useState<Property[]>([]);
    const [mapLoaded, setMapLoaded] = useState(false);

    useEffect(() => {
        if (!active || mapLoaded) return;

        let cancelled = false;

        const load = async () => {
            try {
                const { fetchAllPropertiesForMap } = await import('../services/api');
                const response = await fetchAllPropertiesForMap();
                if (!cancelled) {
                    setMapProperties(response.data);
                    setMapLoaded(true);
                }
            } catch {
                // Map load failed — map simply stays empty
            }
        };

        load();
        return () => { cancelled = true; };
    }, [active, mapLoaded]);

    return { mapProperties, mapLoaded };
}
