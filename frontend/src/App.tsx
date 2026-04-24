import { useTranslation } from 'react-i18next';
import { BrowserRouter as Router, Routes, Route, useNavigate, Outlet, useOutlet } from 'react-router-dom';

import { AuthProvider, useAuth } from './context/AuthContext';
import { useTheme } from './hooks/useTheme';
import { useProperties } from './hooks/useProperties';
import { useMapData } from './hooks/useMapData';
import { useState } from 'react';

import Header from './components/Header';
import Footer from './components/Footer';
import PropertyListView from './components/PropertyListView';
import MapView from './components/MapView';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';

function MainLayout() {
    const { t, i18n } = useTranslation();
    const { user } = useAuth();
    const navigate = useNavigate();
    const outlet = useOutlet();

    const [viewMode, setViewMode] = useState<'list' | 'map' | 'analytics'>('list');

    const { darkMode, toggleDark } = useTheme();
    const { properties, meta, filters, loading, handleFilterChange, handlePageChange } = useProperties();
    const { mapProperties, mapLoaded } = useMapData(viewMode === 'map');

    const tabs: { key: 'list' | 'map' | 'analytics'; label: string }[] = [
        { key: 'list', label: t('view_list') || 'List' },
        { key: 'map', label: t('view_map') || 'Map' },
    ];
    if (user?.role === 'Analyst' || user?.role === 'Admin') {
        tabs.push({ key: 'analytics', label: t('view_analytics') || 'Analytics' });
    }

    const handleTabChange = (key: 'list' | 'map' | 'analytics') => {
        setViewMode(key);
        navigate('/');
    };

    const renderContent = () => {
        if (viewMode === 'analytics') {
            if (user?.role === 'Analyst' || user?.role === 'Admin') {
                return <AnalyticsDashboard />;
            }
            return (
                <div className="text-center py-20 text-text-muted">
                    <p className="text-lg font-semibold">{t('access_denied', 'Access denied')}</p>
                    <p className="text-sm mt-2">{t('analytics_analyst_only', 'Analytics is available for Analyst and Admin roles only.')}</p>
                </div>
            );
        }

        if (viewMode === 'map') {
            return <MapView properties={mapProperties} loaded={mapLoaded} />;
        }

        return (
            <PropertyListView
                properties={properties}
                meta={meta}
                filters={filters}
                loading={loading}
                onFilterChange={handleFilterChange}
                onPageChange={handlePageChange}
            />
        );
    };

    return (
        <div className="min-h-screen bg-background text-text-main">
            <Header
                viewMode={viewMode}
                tabs={tabs}
                darkMode={darkMode}
                onTabChange={handleTabChange}
                onToggleDark={toggleDark}
                onToggleLanguage={() => i18n.changeLanguage(i18n.language === 'uk' ? 'en' : 'uk')}
            />

            <main className="max-w-[1400px] mx-auto flex-grow px-6 py-6 w-full flex flex-col">
                {outlet ? <Outlet /> : renderContent()}
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