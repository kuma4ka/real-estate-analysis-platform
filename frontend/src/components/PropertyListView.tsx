import { useTranslation } from 'react-i18next';
import type { Property, PropertyFilters, PaginationMeta } from '../types/property';
import PropertyCard from './PropertyCard';
import FilterBar from './FilterBar';

interface PropertyListViewProps {
    properties: Property[];
    meta: PaginationMeta | null;
    filters: PropertyFilters;
    loading: boolean;
    onFilterChange: (filters: PropertyFilters) => void;
    onPageChange: (page: number) => void;
}

const Spinner = () => (
    <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent" />
    </div>
);

export default function PropertyListView({
    properties,
    meta,
    filters,
    loading,
    onFilterChange,
    onPageChange,
}: PropertyListViewProps) {
    const { t } = useTranslation();

    return (
        <>
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-text-main">{t('search_results')}</h2>
                <span className="text-sm text-text-muted bg-surface px-3 py-1 rounded-full border border-border">
                    {t('items_count', { count: meta?.total_items ?? 0 })}
                </span>
            </div>

            <div className="flex flex-col lg:flex-row gap-6">
                <aside className="w-full lg:w-[260px] lg:flex-shrink-0">
                    <FilterBar onFilterChange={onFilterChange} />
                </aside>

                <div className="flex-grow min-w-0">
                    {loading ? (
                        <Spinner />
                    ) : properties.length === 0 ? (
                        <div className="text-center py-20 bg-surface rounded-xl border border-dashed border-border">
                            <p className="text-lg text-text-muted">{t('no_results')}</p>
                            <button
                                onClick={() => onFilterChange({})}
                                className="mt-3 text-primary hover:underline text-sm"
                            >
                                {t('reset')}
                            </button>
                        </div>
                    ) : (
                        <>
                            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
                                {properties.map(prop => (
                                    <PropertyCard key={prop.id} property={prop} />
                                ))}
                            </div>

                            {meta && meta.total_pages > 1 && (
                                <div className="py-8 flex justify-center items-center gap-3">
                                    <button
                                        onClick={() => onPageChange(filters.page! - 1)}
                                        disabled={filters.page === 1}
                                        className="px-4 py-2 bg-surface border border-border rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:border-primary hover:text-primary transition-colors"
                                    >
                                        ←
                                    </button>
                                    <span className="text-sm font-medium text-text-muted px-2">
                                        {filters.page} / {meta.total_pages}
                                    </span>
                                    <button
                                        onClick={() => onPageChange(filters.page! + 1)}
                                        disabled={filters.page === meta.total_pages}
                                        className="px-4 py-2 bg-surface border border-border rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:border-primary hover:text-primary transition-colors"
                                    >
                                        →
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </>
    );
}
