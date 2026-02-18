import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { Property, PropertyFilters, PaginationMeta } from './types/property';
import { fetchProperties } from './services/api';
import PropertyCard from './components/PropertyCard';
import FilterBar from './components/FilterBar';
import MapComponent from './components/MapComponent';
import AnalyticsDashboard from './components/AnalyticsDashboard';

function App() {
    const { t, i18n } = useTranslation();
    const [properties, setProperties] = useState<Property[]>([]);
    const [meta, setMeta] = useState<PaginationMeta | null>(null);
    const [filters, setFilters] = useState<PropertyFilters>({
        page: 1,
        per_page: 12,
        sort: 'newest'
    });
    const [loading, setLoading] = useState<boolean>(true);
    const [viewMode, setViewMode] = useState<'list' | 'map' | 'analytics'>('list');

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                const response = await fetchProperties(filters);
                setProperties(response.data);
                setMeta(response.meta);
            } catch (error) {
                console.error("Failed to load properties", error);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, [filters]);

    const [mapProperties, setMapProperties] = useState<Property[]>([]);
    const [mapLoaded, setMapLoaded] = useState(false);

    useEffect(() => {
        if (viewMode === 'map' && !mapLoaded) {
            const loadMapData = async () => {
                try {
                    const { fetchAllPropertiesForMap } = await import('./services/api');
                    const response = await fetchAllPropertiesForMap();
                    setMapProperties(response.data);
                    setMapLoaded(true);
                } catch (error) {
                    console.error("Failed to load map properties", error);
                }
            };
            loadMapData();
        }
    }, [viewMode, mapLoaded]);

    const handleFilterChange = (newFilters: PropertyFilters) => {
        setFilters(prev => ({
            ...prev,
            ...newFilters,
            page: newFilters.page || 1
        }));
    };

    const handlePageChange = (newPage: number) => {
        if (newPage > 0 && meta && newPage <= meta.total_pages) {
            setFilters(prev => ({ ...prev, page: newPage }));
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    const toggleLanguage = () => {
        const newLang = i18n.language === 'uk' ? 'en' : 'uk';
        i18n.changeLanguage(newLang);
    };

    return (
        <div className="min-h-screen bg-background text-text-main transition-colors duration-300">
            <header className="sticky top-0 z-10 bg-surface/80 backdrop-blur-md border-b border-border shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">🏙️</span>
                        <h1 className="text-xl font-bold text-primary tracking-tight">
                            {t('app_title')}
                        </h1>
                    </div>

                    <button
                        onClick={toggleLanguage}
                        className="px-3 py-1 rounded-full bg-background border border-border text-sm font-medium hover:border-primary hover:text-primary transition-colors"
                    >
                        {i18n.language?.toUpperCase().substring(0, 2) || 'UK'}
                    </button>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col h-[calc(100vh-64px)]">

                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                    <div className="w-full md:w-auto flex-grow">
                         <FilterBar onFilterChange={handleFilterChange} />
                    </div>

                    <div className="flex bg-surface rounded-lg border border-border p-1">
                        <button
                            onClick={() => setViewMode('list')}
                            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${viewMode === 'list' ? 'bg-primary text-white' : 'text-text-muted hover:text-text-main'}`}
                        >
                            {t('view_list')}
                        </button>
                        <button
                            onClick={() => setViewMode('map')}
                            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${viewMode === 'map' ? 'bg-primary text-white' : 'text-text-muted hover:text-text-main'}`}
                        >
                            {t('view_map')}
                        </button>
                        <button
                            onClick={() => setViewMode('analytics')}
                            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${viewMode === 'analytics' ? 'bg-primary text-white' : 'text-text-muted hover:text-text-main'}`}
                        >
                            {t('view_analytics')}
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center items-center py-20">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                    </div>
                ) : (
                    <>
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-semibold text-text-main">
                                {t('search_results')}
                            </h2>
                            <span className="text-text-muted text-sm bg-surface px-3 py-1 rounded-full border border-border">
                                {t('items_count', { count: meta?.total_items || 0 })}
                            </span>
                        </div>

                        {properties.length === 0 ? (
                            <div className="text-center py-20 bg-surface rounded-xl border border-dashed border-border">
                                <p className="text-xl text-text-muted">{t('no_results')}</p>
                                <button
                                    onClick={() => handleFilterChange({})}
                                    className="mt-4 text-primary hover:underline"
                                >
                                    {t('reset')}
                                </button>
                            </div>
                        ) : (
                            <div className="flex-grow relative min-h-[500px]">
                                {viewMode === 'list' ? (
                                    <>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 pb-8">
                                            {properties.map((prop) => (
                                                <PropertyCard key={prop.id} property={prop} />
                                            ))}
                                        </div>

                                        {meta && meta.total_pages > 1 && (
                                            <div className="py-8 flex justify-center items-center gap-2">
                                                <button
                                                    onClick={() => handlePageChange(filters.page! - 1)}
                                                    disabled={filters.page === 1}
                                                    className="px-4 py-2 border border-border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface transition-colors"
                                                >
                                                    ←
                                                </button>
                                                <span className="text-sm font-medium px-4">
                                                    {filters.page} / {meta.total_pages}
                                                </span>
                                                <button
                                                    onClick={() => handlePageChange(filters.page! + 1)}
                                                    disabled={filters.page === meta.total_pages}
                                                    className="px-4 py-2 border border-border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface transition-colors"
                                                >
                                                    →
                                                </button>
                                            </div>
                                        )}
                                    </>
                                ) : viewMode === 'map' ? (
                                    <div className="h-full w-full min-h-[600px] rounded-xl overflow-hidden border border-border">
                                        <MapComponent properties={mapProperties.length > 0 ? mapProperties : properties} />
                                    </div>
                                ) : (
                                    <AnalyticsDashboard />
                                )}
                            </div>
                        )}
                    </>
                )}
            </main>
        </div>
    );
}

export default App;