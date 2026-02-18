/** @type {import('tailwindcss').Config} */
export default {
    darkMode: 'class',
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: 'var(--color-primary)',
                'primary-hover': 'var(--color-primary-hover)',
                secondary: 'var(--color-secondary)',
                accent: 'var(--color-accent)',
                'accent-alt': 'var(--color-accent-alt)',
                cta: 'var(--color-cta)',
                'cta-hover': 'var(--color-cta-hover)',
                success: 'var(--color-success)',
                warning: 'var(--color-warning)',
                error: 'var(--color-error)',
                background: 'var(--color-bg-base)',
                surface: 'var(--color-bg-surface)',
                'text-main': 'var(--color-text-main)',
                'text-muted': 'var(--color-text-muted)',
                border: 'var(--color-border)',
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
            },
            boxShadow: {
                'card': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
                'card-hover': '0 4px 12px rgba(0,0,0,0.08)',
            }
        },
    },
    plugins: [],
}