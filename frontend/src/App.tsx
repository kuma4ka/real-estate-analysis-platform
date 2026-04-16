import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { Property, PropertyFilters, PaginationMeta } from './types/property';
import { fetchProperties } from './services/api';
import PropertyCard from './components/PropertyCard';
import FilterBar from './components/FilterBar';
import MapComponent from './components/MapComponent';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import Header from './components/Header';
import Footer from './components/Footer';

import { BrowserRouter as Router, Routes, Route, useNavigate, Outlet, useOutlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import ProtectedRoute from './components/ProtectedRoute';

function MainLayout() {
    const { t, i18n } = useTranslation();
    const { user } = useAuth();
    const navigate = useNavigate();
    const outlet = useOutlet();

    const [properties, setProperties] = useState<Property[]>([]);
    const [meta, setMeta] = useState<PaginationMeta | null>(null);
    const [filters, setFilters] = useState<PropertyFilters>({
        page: 1,
        per_page: 12,
        sort: 'newest'
    });
    const [loading, setLoading] = useState<boolean>(true);
    const [viewMode, setViewMode] = useState<'list' | 'map' | 'analytics'>('list');
    const [darkMode, setDarkMode] = useState(() => localStorage.getItem('theme') === 'dark');

    const [mapProperties, setMapProperties] = useState<Property[]>([]);
    const [mapLoaded, setMapLoaded] = useState(false);

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
                console.error('Failed to load properties', error);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [filters]);

    useEffect(() => {
        if (viewMode === 'map' && !mapLoaded) {
            const loadMapData = async () => {
                try {
                    const { fetchAllPropertiesForMap } = await import('./services/api');
                    const response = await fetchAllPropertiesForMap();
                    setMapProperties(response.data);
                    setMapLoaded(true);
                } catch (error) {
                    console.error('Failed to load map properties', error);
                }
            };
            loadMapData();
        }
    }, [viewMode, mapLoaded]);

    const handleFilterChange = (newFilters: PropertyFilters) => {
        setFilters(prev => ({ ...prev, ...newFilters, page: newFilters.page || 1 }));
    };

    const handlePageChange = (newPage: number) => {
        if (newPage > 0 && meta && newPage <= meta.total_pages) {
            setFilters(prev => ({ ...prev, page: newPage }));
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    const tabs: { key: 'list' | 'map' | 'analytics'; label: string }[] = [
        { key: 'list', label: t('view_list') || 'List' },
        { key: 'map', label: t('view_map') || 'Map' },
    ];
    if (user && (user.role === 'Analyst' || user.role === 'Admin')) {
        tabs.push({ key: 'analytics', label: t('view_analytics') || 'Analytics' });
    }

    const handleTabChange = (key: 'list' | 'map' | 'analytics') => {
        setViewMode(key);
        navigate('/');
    };

    return (
        <div className="min-h-screen bg-background text-text-main">
            <Header
                viewMode={viewMode}
                tabs={tabs}
                darkMode={darkMode}
                onTabChange={handleTabChange}
                onToggleDark={() => setDarkMode(d => !d)}
                onToggleLanguage={() => i18n.changeLanguage(i18n.language === 'uk' ? 'en' : 'uk')}
            />

            <main className="max-w-[1400px] mx-auto flex-grow px-6 py-6 w-full flex flex-col">
                {outlet ? <Outlet /> : (
                    <>
                        {viewMode === 'analytics' ? (
                            user && (user.role === 'Analyst' || user.role === 'Admin') ? (
                                <AnalyticsDashboard />
                            ) : (
                                <div className="text-center py-20 text-text-muted">
                                    <p className="text-lg font-semibold">{t('access_denied', 'Access denied')}</p>
                                    <p className="text-sm mt-2">{t('analytics_analyst_only', 'Analytics is available for Analyst and Admin roles only.')}</p>
                                </div>
                            )
                        ) : viewMode === 'map' ? (
                            <div className="h-[calc(100vh-120px)] w-full rounded-xl overflow-hidden border border-border shadow-card">
                                {mapLoaded
                                    ? <MapComponent properties={mapProperties} />
                                    : (
                                        <div className="flex items-center justify-center h-full bg-surface">
                                            <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent" />
                                        </div>
                                    )
                                }
                            </div>
                        ) : (
                            <>
                                <div className="flex items-center justify-between mb-6">
                                    <h2 className="text-2xl font-bold text-text-main">{t('search_results')}</h2>
                                    <span className="text-sm text-text-muted bg-surface px-3 py-1 rounded-full border border-border">
                                        {t('items_count', { count: meta?.total_items || 0 })}
                                    </span>
                                </div>

                                <div className="flex flex-col lg:flex-row gap-6">
                                    <aside className="w-full lg:w-[260px] lg:flex-shrink-0">
                                        <FilterBar onFilterChange={handleFilterChange} />
                                    </aside>

                                    <div className="flex-grow min-w-0">
                                        {loading ? (
                                            <div className="flex justify-center items-center py-20">
                                                <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent" />
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
                    </>
                )}
            </main>

            <Footer />
        </div>
    );
}

function App() {
    return (
        <AuthProvider>
            <Router>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/" element={<MainLayout />}>
                        <Route path="profile" element={
                            <ProtectedRoute>
                                <Profile />
                            </ProtectedRoute>
                        } />
                    </Route>
                </Routes>
            </Router>
        </AuthProvider>
    );
}

export default App;