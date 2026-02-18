import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
    en: {
        translation: {
            "app_title": "Real Estate Analysis",
            "filters": "Filters",
            "search_results": "Search Results",
            "city": "City",
            "rooms": "Rooms",
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
            "area": "Area",
            "area_unit": "m²",
            "floor": "Floor",
            "more_details": "More Details",
            "view_list": "List",
            "view_map": "Map",
            "items_count": "{{count}} items",
            "no_image": "No Image",
        }
    },
    uk: {
        translation: {
            "app_title": "Аналіз Нерухомості",
            "filters": "Фільтри",
            "search_results": "Результати пошуку",
            "city": "Місто",
            "rooms": "Кімнат",
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
            "area": "Площа",
            "area_unit": "м²",
            "floor": "Поверх",
            "more_details": "Детальніше",
            "view_list": "Список",
            "view_map": "Карта",
            "items_count": "{{count}} оголошень",
            "no_image": "Без фото",
        }
    }
};

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources,
        fallbackLng: 'uk',
        interpolation: {
            escapeValue: false
        }
    });

export default i18n;