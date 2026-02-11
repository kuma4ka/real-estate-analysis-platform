import type { PropertiesResponse, PropertyFilters } from '../types/property';

const API_BASE_URL = '/api/v1'; // Based on backend/app/__init__.py: url_prefix='/api/v1'

export const fetchProperties = async (filters: PropertyFilters = {}): Promise<PropertiesResponse> => {
    try {
        const params = new URLSearchParams();
        
        if (filters.page) params.append('page', filters.page.toString());
        if (filters.per_page) params.append('per_page', filters.per_page.toString());
        if (filters.city) params.append('city', filters.city);
        if (filters.rooms !== undefined && filters.rooms !== '') params.append('rooms', filters.rooms.toString());
        if (filters.price_min !== undefined && filters.price_min !== '') params.append('price_min', filters.price_min.toString());
        if (filters.price_max !== undefined && filters.price_max !== '') params.append('price_max', filters.price_max.toString());
        if (filters.sort) params.append('sort', filters.sort);

        const response = await fetch(`${API_BASE_URL}/properties?${params.toString()}`);

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        const data: PropertiesResponse = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching properties:', error);
        throw error;
    }
};