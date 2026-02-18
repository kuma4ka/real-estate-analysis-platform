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
            page: 1
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

    const roomOptions = [1, 2, 3];

    return (
        <div className="bg-surface p-5 rounded-xl shadow-card border border-border">
            <h3 className="text-base font-semibold text-text-main mb-5">{t('filters')}</h3>

            {/* City */}
            <div className="mb-4">
                <label className="block text-sm font-medium text-text-muted mb-1.5">{t('city')}</label>
                <input
                    type="text"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    placeholder={t('city')}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background text-text-main text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-colors"
                />
            </div>

            {/* Price Range */}
            <div className="mb-4">
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <label className="block text-sm font-medium text-text-muted mb-1.5">{t('min_price')}</label>
                        <input
                            type="number"
                            value={priceMin}
                            min={0}
                            onChange={(e) => {
                                const val = e.target.value ? parseFloat(e.target.value) : '';
                                setPriceMin(val !== '' && val < 0 ? 0 : val);
                            }}
                            placeholder="0"
                            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-text-main text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-colors"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-text-muted mb-1.5">{t('max_price')}</label>
                        <input
                            type="number"
                            value={priceMax}
                            min={0}
                            onChange={(e) => {
                                const val = e.target.value ? parseFloat(e.target.value) : '';
                                setPriceMax(val !== '' && val < 0 ? 0 : val);
                            }}
                            placeholder="Max"
                            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-text-main text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-colors"
                        />
                    </div>
                </div>
            </div>

            {/* Rooms */}
            <div className="mb-4">
                <label className="block text-sm font-medium text-text-muted mb-2">{t('rooms')}</label>
                <div className="flex gap-2">
                    {roomOptions.map(r => (
                        <button
                            key={r}
                            onClick={() => setRooms(rooms === r ? '' : r)}
                            className={`flex-1 py-1.5 text-sm font-medium rounded-lg border transition-colors ${
                                rooms === r
                                    ? 'bg-primary text-white border-primary'
                                    : 'bg-background border-border text-text-muted hover:border-primary hover:text-primary'
                            }`}
                        >
                            {r}
                        </button>
                    ))}
                    <button
                        onClick={() => setRooms(rooms === 4 ? '' : 4)}
                        className={`flex-1 py-1.5 text-sm font-medium rounded-lg border transition-colors ${
                            rooms === 4
                                ? 'bg-primary text-white border-primary'
                                : 'bg-background border-border text-text-muted hover:border-primary hover:text-primary'
                        }`}
                    >
                        3+
                    </button>
                </div>
            </div>

            {/* Sort */}
            <div className="mb-5">
                <label className="block text-sm font-medium text-text-muted mb-1.5">{t('sort_by')}</label>
                <select
                    value={sort}
                    onChange={(e) => setSort(e.target.value as PropertyFilters['sort'])}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background text-text-main text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-colors"
                >
                    <option value="newest">{t('sort_newest')}</option>
                    <option value="cheapest">{t('sort_cheapest')}</option>
                    <option value="expensive">{t('sort_expensive')}</option>
                </select>
            </div>

            {/* Actions */}
            <button
                onClick={handleApply}
                className="w-full py-2.5 bg-primary text-white rounded-lg font-medium text-sm hover:bg-primary-hover transition-colors shadow-sm mb-2"
            >
                {t('apply')}
            </button>
            <button
                onClick={handleReset}
                className="w-full py-2 text-text-muted text-sm hover:text-primary transition-colors"
            >
                {t('reset')}
            </button>
        </div>
    );
};

export default FilterBar;
