import { useEffect, useState } from 'react';
import type { Property, PropertyFilters, PaginationMeta } from '../types/property';
import { fetchProperties } from '../services/api';

const DEFAULT_FILTERS: PropertyFilters = {
    page: 1,
    per_page: 12,
    sort: 'newest',
};

export function useProperties() {
    const [properties, setProperties] = useState<Property[]>([]);
    const [meta, setMeta] = useState<PaginationMeta | null>(null);
    const [filters, setFilters] = useState<PropertyFilters>(DEFAULT_FILTERS);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        const load = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await fetchProperties(filters);
                if (!cancelled) {
                    setProperties(response.data);
                    setMeta(response.meta);
                }
            } catch (err) {
                if (!cancelled) {
                    setError('Failed to load listings. Please try again.');
                    setProperties([]);
                    setMeta(null);
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        };

        load();
        return () => { cancelled = true; };
    }, [filters]);

    const handleFilterChange = (newFilters: PropertyFilters) => {
        setFilters(prev => ({ ...prev, ...newFilters, page: newFilters.page ?? 1 }));
    };

    const handlePageChange = (newPage: number) => {
        if (meta && newPage > 0 && newPage <= meta.total_pages) {
            setFilters(prev => ({ ...prev, page: newPage }));
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    return { properties, meta, filters, loading, error, handleFilterChange, handlePageChange };
}
