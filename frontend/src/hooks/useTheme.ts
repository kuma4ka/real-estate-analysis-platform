import { useEffect, useState } from 'react';

export function useTheme() {
    const [darkMode, setDarkMode] = useState(() => localStorage.getItem('theme') === 'dark');

    useEffect(() => {
        document.documentElement.classList.toggle('dark', darkMode);
        localStorage.setItem('theme', darkMode ? 'dark' : 'light');
    }, [darkMode]);

    const toggleDark = () => setDarkMode(d => !d);

    return { darkMode, toggleDark };
}
