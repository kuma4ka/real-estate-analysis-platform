import type { PropertiesResponse, PropertyFilters, Property } from '../types/property';

export const API_BASE_URL = '/api/v1';

// Helper to include JWT token
export const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    const token = localStorage.getItem('token');
    const headers = new Headers(options.headers || {});
    
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    return fetch(url, { ...options, headers });
};

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

        const response = await fetchWithAuth(`${API_BASE_URL}/properties?${params.toString()}`);

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
        const response = await fetchWithAuth(`${API_BASE_URL}/properties/map`);
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
    total_active: number;
    avg_price: number;
    avg_area: number;
    avg_price_per_m2: number;
    by_city: { city: string; count: number; avg_price: number; avg_price_per_m2: number }[];
    by_rooms: { rooms: number; count: number; avg_price: number }[];
    by_price_ranges: { range: string; count: number }[];
    price_histogram: { range: string; count: number }[];
    recent_trend: { month: string; count: number; avg_price: number; price_change_pct: number | null }[];
}

export const fetchStats = async (): Promise<StatsData> => {
    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/stats`);
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching stats:', error);
        throw error;
    }
};

export interface ForecastPoint {
    date: string;
    predicted_price: number;
    lower: number;
    upper: number;
}

export interface ForecastHistoricalPoint {
    date: string;
    avg_price: number;
}

export interface ForecastData {
    city: string | null;
    available_cities: string[];
    r_squared: number;
    slope_per_day: number;
    historical: ForecastHistoricalPoint[];
    forecast: ForecastPoint[];
}

export const fetchForecast = async (city?: string): Promise<ForecastData> => {
    try {
        const url = new URL(`${API_BASE_URL}/stats/forecast`);
        if (city) {
            url.searchParams.append('city', city);
        }
        const response = await fetchWithAuth(url.toString());
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching forecast:', error);
        throw error;
    }
};

export const downloadStatsCsv = async (): Promise<void> => {
    try {
        const response = await fetchWithAuth(`${API_BASE_URL}/stats/export`);
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'market_analysis_export.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error downloading CSV:', error);
        throw error;
    }
};