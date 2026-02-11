export interface Property {
    id: number;
    title: string;
    price: number;
    currency: string;
    address: string | null;
    city: string | null;
    district: string | null;
    area: number | null;
    rooms: number | null;
    floor: number | null;
    description: string | null;
    images: string[] | null;
    source_url: string;
    created_at: string;
}

export interface PaginationMeta {
    page: number;
    per_page: number;
    total_pages: number;
    total_items: number;
}

export interface PropertiesResponse {
    data: Property[];
    meta: PaginationMeta;
}

export interface PropertyFilters {
    page?: number;
    per_page?: number;
    city?: string;
    rooms?: number | '';
    price_min?: number | '';
    price_max?: number | '';
    sort?: 'newest' | 'cheapest' | 'expensive';
}