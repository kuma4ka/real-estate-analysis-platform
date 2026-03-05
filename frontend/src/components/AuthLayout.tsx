import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

interface AuthLayoutProps {
    children: React.ReactNode;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
    const { t, i18n } = useTranslation();
    const [darkMode, setDarkMode] = useState(() => {
        return localStorage.getItem('theme') === 'dark';
    });

    useEffect(() => {
        document.documentElement.classList.toggle('dark', darkMode);
        localStorage.setItem('theme', darkMode ? 'dark' : 'light');
    }, [darkMode]);

    const toggleLanguage = () => {
        const newLang = i18n.language === 'uk' ? 'en' : 'uk';
        i18n.changeLanguage(newLang);
    };

    return (
        <div className="min-h-screen bg-background text-text-main flex flex-col relative">
            <div className="absolute top-6 right-6 flex items-center gap-4 z-10">
                <button
                    onClick={() => setDarkMode(!darkMode)}
                    className="p-2 rounded-full bg-surface border border-border text-text-muted hover:text-primary hover:border-primary transition-colors"
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
                    className="px-3 py-1.5 rounded-full text-xs font-semibold bg-surface border border-border text-text-muted hover:text-primary hover:border-primary transition-colors"
                >
                    {i18n.language?.toUpperCase().substring(0, 2) || 'UK'}
                </button>
            </div>
            
            <Link to="/" className="absolute top-6 left-6 flex items-center gap-2 text-text-muted hover:text-primary transition-colors z-10">
                <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                    <span className="text-lg">🏠</span>
                </div>
                <span className="font-semibold">{t('app_title', 'Real Estate Analyzer')}</span>
            </Link>

            <div className="flex-grow flex items-center justify-center p-4">
               {children}
            </div>
        </div>
    );
};

export default AuthLayout;
