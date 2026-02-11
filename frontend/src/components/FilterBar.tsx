import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { PropertyFilters } from '../types/property';

interface FilterBarProps {
    onFilterChange: (filters: PropertyFilters) => void;
}

const FilterBar: React.FC<FilterBarProps> = ({ onFilterChange }) => {
    const { t } = useTranslation();
    const [city, setCity] = useState('');
    const [rooms, setRooms] = useState<number | ''>('');
    const [priceMin, setPriceMin] = useState<number | ''>('');
    const [priceMax, setPriceMax] = useState<number | ''>('');
    const [sort, setSort] = useState<PropertyFilters['sort']>('newest');

    const handleApply = () => {
        onFilterChange({
            city,
            rooms,
            price_min: priceMin,
            price_max: priceMax,
            sort,
            page: 1 // Reset to first page on filter change
        });
    };

    const handleReset = () => {
        setCity('');
        setRooms('');
        setPriceMin('');
        setPriceMax('');
        setSort('newest');
        onFilterChange({ page: 1 });
    };

    return (
        <div className="bg-surface p-4 rounded-lg shadow-sm border border-border mb-6">
            <h2 className="text-lg font-semibold text-text-main mb-4">{t('filters')}</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                {/* City */}
                <div>
                    <label className="block text-sm font-medium text-text-muted mb-1">{t('city')}</label>
                    <input
                        type="text"
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
                        className="w-full px-3 py-2 border border-border rounded-md bg-background text-text-main focus:outline-none focus:ring-2 focus:ring-primary"
                        placeholder="Kyiv"
                    />
                </div>

                {/* Rooms */}
                <div>
                    <label className="block text-sm font-medium text-text-muted mb-1">{t('rooms')}</label>
                    <input
                        type="number"
                        value={rooms}
                        onChange={(e) => setRooms(e.target.value ? parseInt(e.target.value) : '')}
                        className="w-full px-3 py-2 border border-border rounded-md bg-background text-text-main focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>

                {/* Price Min */}
                <div>
                    <label className="block text-sm font-medium text-text-muted mb-1">{t('min_price')}</label>
                    <input
                        type="number"
                        value={priceMin}
                        onChange={(e) => setPriceMin(e.target.value ? parseFloat(e.target.value) : '')}
                        className="w-full px-3 py-2 border border-border rounded-md bg-background text-text-main focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>

                {/* Price Max */}
                <div>
                    <label className="block text-sm font-medium text-text-muted mb-1">{t('max_price')}</label>
                    <input
                        type="number"
                        value={priceMax}
                        onChange={(e) => setPriceMax(e.target.value ? parseFloat(e.target.value) : '')}
                        className="w-full px-3 py-2 border border-border rounded-md bg-background text-text-main focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
            </div>

            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                {/* Sort */}
                <div className="flex items-center gap-2 w-full md:w-auto">
                    <label className="text-sm font-medium text-text-muted whitespace-nowrap">{t('sort_by')}:</label>
                    <select
                        value={sort}
                        onChange={(e) => setSort(e.target.value as PropertyFilters['sort'])}
                        className="px-3 py-2 border border-border rounded-md bg-background text-text-main focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                        <option value="newest">{t('sort_newest')}</option>
                        <option value="cheapest">{t('sort_cheapest')}</option>
                        <option value="expensive">{t('sort_expensive')}</option>
                    </select>
                </div>

                {/* Actions */}
                <div className="flex gap-2 w-full md:w-auto">
                    <button
                        onClick={handleReset}
                        className="flex-1 md:flex-none px-4 py-2 border border-border text-text-main rounded-md hover:bg-background transition-colors"
                    >
                        {t('reset')}
                    </button>
                    <button
                        onClick={handleApply}
                        className="flex-1 md:flex-none px-6 py-2 bg-primary text-white rounded-md hover:bg-primary-hover transition-colors font-medium shadow-sm"
                    >
                        {t('apply')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default FilterBar;
