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
    const [darkMode, setDarkMode] = useState(() => {
        return localStorage.getItem('theme') === 'dark';
    });

    useEffect(() => {
        document.documentElement.classList.toggle('dark', darkMode);
        localStorage.setItem('theme', darkMode ? 'dark' : 'light');
    }, [darkMode]);

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

    const tabs = [
        { key: 'list' as const, label: t('view_list') },
        { key: 'map' as const, label: t('view_map') },
        { key: 'analytics' as const, label: t('view_analytics') },
    ];

    return (
        <div className="min-h-screen bg-background text-text-main">
            {/* Header */}
            <header className="sticky top-0 z-10 bg-surface border-b border-border">
                <div className="max-w-[1400px] mx-auto px-6 h-16 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                            <span className="text-lg">🏠</span>
                        </div>
                        <h1 className="text-lg font-semibold text-text-main tracking-tight">
                            {t('app_title')}
                        </h1>
                    </div>

                    <div className="flex items-center gap-6">
                        <nav className="flex gap-1">
                            {tabs.map(tab => (
                                <button
                                    key={tab.key}
                                    onClick={() => setViewMode(tab.key)}
                                    className={`px-4 py-4 text-sm font-medium border-b-2 transition-colors ${
                                        viewMode === tab.key
                                            ? 'border-primary text-primary'
                                            : 'border-transparent text-text-muted hover:text-text-main'
                                    }`}
                                >
                                    {tab.label}
                                </button>
                            ))}
                        </nav>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setDarkMode(!darkMode)}
                                className="p-2 rounded-full bg-background border border-border text-text-muted hover:text-primary hover:border-primary transition-colors"
                                title={darkMode ? 'Light mode' : 'Dark mode'}
                            >
                                {darkMode ? (
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                                    </svg>
                                ) : (
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                                    </svg>
                                )}
                            </button>
                            <button
                                onClick={toggleLanguage}
                                className="px-3 py-1.5 rounded-full text-xs font-semibold bg-background border border-border text-text-muted hover:text-primary hover:border-primary transition-colors"
                            >
                                {i18n.language?.toUpperCase().substring(0, 2) || 'UK'}
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-[1400px] mx-auto px-6 py-6">
                {viewMode === 'analytics' ? (
                    <AnalyticsDashboard />
                ) : viewMode === 'map' ? (
                    <div className="h-[calc(100vh-120px)] w-full rounded-xl overflow-hidden border border-border shadow-card">
                        <MapComponent properties={mapProperties.length > 0 ? mapProperties : properties} />
                    </div>
                ) : (
                    <>
                        {/* List Header */}
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-2xl font-bold text-text-main">
                                {t('search_results')}
                            </h2>
                            <span className="text-sm text-text-muted bg-surface px-3 py-1 rounded-full border border-border">
                                {t('items_count', { count: meta?.total_items || 0 })}
                            </span>
                        </div>

                        {/* Sidebar + Cards Layout */}
                        <div className="flex gap-6">
                            {/* Sidebar Filters */}
                            <aside className="w-[260px] flex-shrink-0 hidden lg:block">
                                <FilterBar onFilterChange={handleFilterChange} />
                            </aside>

                            {/* Cards Area */}
                            <div className="flex-grow min-w-0">
                                {/* Mobile Filters */}
                                <div className="lg:hidden mb-4">
                                    <FilterBar onFilterChange={handleFilterChange} />
                                </div>

                                {loading ? (
                                    <div className="flex justify-center items-center py-20">
                                        <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent"></div>
                                    </div>
                                ) : properties.length === 0 ? (
                                    <div className="text-center py-20 bg-surface rounded-xl border border-dashed border-border">
                                        <p className="text-lg text-text-muted">{t('no_results')}</p>
                                        <button
                                            onClick={() => handleFilterChange({})}
                                            className="mt-3 text-primary hover:underline text-sm"
                                        >
                                            {t('reset')}
                                        </button>
                                    </div>
                                ) : (
                                    <>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
                                            {properties.map((prop) => (
                                                <PropertyCard key={prop.id} property={prop} />
                                            ))}
                                        </div>

                                        {meta && meta.total_pages > 1 && (
                                            <div className="py-8 flex justify-center items-center gap-3">
                                                <button
                                                    onClick={() => handlePageChange(filters.page! - 1)}
                                                    disabled={filters.page === 1}
                                                    className="px-4 py-2 bg-surface border border-border rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:border-primary hover:text-primary transition-colors"
                                                >
                                                    ←
                                                </button>
                                                <span className="text-sm font-medium text-text-muted px-2">
                                                    {filters.page} / {meta.total_pages}
                                                </span>
                                                <button
                                                    onClick={() => handlePageChange(filters.page! + 1)}
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
                )}
            </main>

            {/* Footer */}
            <footer className="border-t border-border bg-surface mt-auto">
                <div className="max-w-[1400px] mx-auto px-6 py-5 flex flex-col sm:flex-row justify-between items-center gap-3">
                    <p className="text-sm text-text-muted">
                        © {new Date().getFullYear()} — {t('app_title')}. Made by <span className="font-medium text-text-main">Prokopenko Dmytro</span>
                    </p>
                    <div className="flex items-center gap-4">
                        <a
                            href="https://github.com/kuma4ka"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-text-muted hover:text-primary transition-colors flex items-center gap-1.5 text-sm"
                        >
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                            GitHub
                        </a>
                        <a
                            href="https://www.linkedin.com/in/dmytro-prokopenko-dev/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-text-muted hover:text-primary transition-colors flex items-center gap-1.5 text-sm"
                        >
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                            LinkedIn
                        </a>
                    </div>
                </div>
            </footer>
        </div>
    );
}

export default App;