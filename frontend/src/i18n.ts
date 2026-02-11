import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
    en: {
        translation: {
            "app_title": "Real Estate Analysis",
            "search": "Search",
            "filters": "Filters",
            "search_results": "Search Results",
            "city": "City",
            "rooms": "Rooms",
            "price_range": "Price Range",
            "min_price": "Min",
            "max_price": "Max",
            "sort_by": "Sort by",
            "sort_newest": "Newest",
            "sort_cheapest": "Price: Low to High",
            "sort_expensive": "Price: High to Low",
            "apply": "Apply",
            "reset": "Reset",
            "loading": "Loading...",
            "no_results": "No properties found",
            "price": "Price",
            "area": "Area",
            "floor": "Floor",
            "more_details": "More Details",
            "source": "Source",
            "currency_usd": "$",
            "currency_uah": "₴",
        }
    },
    uk: {
        translation: {
            "app_title": "Аналіз Нерухомості",
            "search": "Пошук",
            "filters": "Фільтри",
            "search_results": "Результати пошуку",
            "city": "Місто",
            "rooms": "Кімнат",
            "price_range": "Діапазон цін",
            "min_price": "Мін",
            "max_price": "Макс",
            "sort_by": "Сортування",
            "sort_newest": "Найновіші",
            "sort_cheapest": "Від дешевих",
            "sort_expensive": "Від дорогих",
            "apply": "Застосувати",
            "reset": "Скинути",
            "loading": "Завантаження...",
            "no_results": "Оголошень не знайдено",
            "price": "Ціна",
            "area": "Площа",
            "floor": "Поверх",
            "more_details": "Детальніше",
            "source": "Джерело",
            "currency_usd": "$",
            "currency_uah": "₴",
        }
    }
};

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources,
        fallbackLng: 'uk', // User seems to be Ukrainian based on request language
        interpolation: {
            escapeValue: false
        }
    });

export default i18n;