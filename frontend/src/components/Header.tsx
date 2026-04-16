import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';

interface HeaderProps {
    viewMode: 'list' | 'map' | 'analytics';
    tabs: { key: 'list' | 'map' | 'analytics'; label: string }[];
    darkMode: boolean;
    onTabChange: (key: 'list' | 'map' | 'analytics') => void;
    onToggleDark: () => void;
    onToggleLanguage: () => void;
}

export default function Header({
    viewMode,
    tabs,
    darkMode,
    onTabChange,
    onToggleDark,
    onToggleLanguage,
}: HeaderProps) {
    const { t, i18n } = useTranslation();
    const { user, logout } = useAuth();

    return (
        <header className="sticky top-0 z-10 bg-surface border-b border-border">
            <div className="max-w-[1400px] mx-auto px-6 h-16 flex justify-between items-center">
                <Link to="/" onClick={() => onTabChange('list')} className="flex items-center gap-3">
                    <img src="/logo.svg" alt="Logo" className="w-8 h-8 rounded-lg" />
                    <h1 className="text-lg font-semibold text-text-main tracking-tight">
                        {t('app_title')}
                    </h1>
                </Link>

                <div className="flex items-center gap-6">
                    <nav className="flex gap-1">
                        {tabs.map(tab => (
                            <button
                                key={tab.key}
                                onClick={() => onTabChange(tab.key)}
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

                    <div className="flex items-center gap-4">
                        {user ? (
                            <div className="flex items-center gap-3">
                                <Link
                                    to="/profile"
                                    className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface border border-border hover:bg-background hover:border-primary/50 transition-all cursor-pointer group"
                                >
                                    <div className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs">
                                        👤
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-sm font-medium text-text-main group-hover:text-primary transition-colors leading-none">{user.email}</span>
                                        <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider leading-none mt-0.5">{user.role}</span>
                                    </div>
                                </Link>
                                <button
                                    onClick={() => { logout(); window.location.reload(); }}
                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium text-red-500 bg-red-500/10 hover:bg-red-500/20 hover:text-red-600 transition-colors"
                                    title={typeof t('logout') === 'string' ? t('logout') as string : 'Sign Out'}
                                >
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                                    <span className="hidden sm:inline">{t('logout', 'Sign Out')}</span>
                                </button>
                            </div>
                        ) : (
                            <Link
                                to="/login"
                                className="text-sm font-medium bg-primary text-white px-4 py-2 rounded-lg shadow-sm hover:bg-primary-hover transition"
                            >
                                {t('login', 'Sign In')}
                            </Link>
                        )}

                        <button
                            onClick={onToggleDark}
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
                            onClick={onToggleLanguage}
                            className="px-3 py-1.5 rounded-full text-xs font-semibold bg-background border border-border text-text-muted hover:text-primary hover:border-primary transition-colors"
                        >
                            {i18n.language === 'uk' ? '🇺🇦 УКР' : '🇬🇧 ENG'}
                        </button>
                    </div>
                </div>
            </div>
        </header>
    );
}
