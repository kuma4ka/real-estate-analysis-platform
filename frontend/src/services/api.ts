import type { PropertiesResponse, PropertyFilters, Property } from '../types/property';

const API_BASE_URL = '/api/v1';

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

export const fetchAllPropertiesForMap = async (): Promise<{ data: Property[], count: number }> => {
    try {
        const response = await fetch(`${API_BASE_URL}/properties/map`);
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching map properties:', error);
        throw error;
    }
};

export interface StatsData {
    total_listings: number;
    avg_price_usd: number;
    avg_area: number;
    avg_price_per_m2: number;
    by_city: { city: string; count: number; avg_price: number; avg_price_per_m2: number }[];
    by_rooms: { rooms: number; count: number; avg_price: number }[];
    price_histogram: { range: string; count: number }[];
    recent_trend: { date: string; count: number; avg_price: number; price_change_pct: number | null }[];
}

export const fetchStats = async (): Promise<StatsData> => {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching stats:', error);
        throw error;
    }
};