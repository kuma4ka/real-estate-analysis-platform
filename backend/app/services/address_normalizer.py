import re
from app.services.cities import normalize_city, get_all_aliases


class AddressNormalizer:
    """
    Heuristic address normalizer that generates geocoding search candidates
    from raw, messy addresses. Handles renamed streets, inverted initials,
    complex separators, and RU→UA translation.
    """

    STREET_MARKERS = [
        'вулиця', 'вул.', 'вул', 'улица', 'ул.', 'ул',
        'проспект', 'просп.', 'просп', 'пр-т',
        'провулок', 'пров.', 'пер.', 'переулок',
        'бульвар', 'бульв.', 'б-р',
        'площа', 'пл.', 'площадь',
        'узвіз', 'спуск',
        'набережна', 'наб.', 'набережная',
        'шосе', 'шоссе',
        'майдан', 'тупик'
    ]

    CITY_MARKERS = ['м.', 'г.', 'місто', 'город']

    STREET_TRANSLATIONS = {
        'улица': 'вулиця', 'ул.': 'вулиця',
        'проспект': 'проспект', 'просп.': 'проспект',
        'переулок': 'провулок', 'пер.': 'провулок',
        'площадь': 'площа',
        'бульвар': 'бульвар',
        'шоссе': 'шосе',
        'набережная': 'набережна',
        'спуск': 'узвіз',
        'тупик': 'тупик',
    }

    STREET_RENAMES = {
        'Челябинская': 'Пантелеймона Куліша',
        'Челябінська': 'Пантелеймона Куліша',
        'Магнитогорская': 'Якова Гніздовського',
        'Азербайджанская': 'Азербайджанська',
        'Карагандинская': 'Холодноярської Бригади',
        'Владимирская': 'Володимирська',
        'Газеты Правда': 'Слобожанський проспект',
        'Правды': 'Слобожанський',
        'Королева': 'Корольова',
        'Ленина': 'вулиця Соборна',
        'Московская': 'Князів Острозьких',
    }

    _ALL_TRANSLATIONS = {}

    @classmethod
    def _get_translations(cls):
        if not cls._ALL_TRANSLATIONS:
            for alias, canonical in get_all_aliases().items():
                cls._ALL_TRANSLATIONS[alias] = canonical

            cls._ALL_TRANSLATIONS.update(cls.STREET_TRANSLATIONS)
            cls._ALL_TRANSLATIONS.update(cls.STREET_RENAMES)
        return cls._ALL_TRANSLATIONS

    @classmethod
    def normalize(cls, address: str) -> list[str]:
        """Returns a prioritized list of search strings for geocoding."""
        if not address:
            return []

        candidates = []
        cleaned = cls._basic_clean(address)

        parts = [p.strip() for p in cleaned.split(',')]
        if len(parts) < 2:
            return [cleaned]

        city = parts[0]
        city_ua = normalize_city(city) or city

        raw_rest = ", ".join(parts[1:])

        if '/' in raw_rest:
            for sp in [p.strip() for p in raw_rest.split('/')]:
                candidates.append(f"{city_ua}, {cls._process_street_part(sp)}")

        if '(' in raw_rest:
            inside = re.search(r'\((.*?)\)', raw_rest)
            if inside:
                street_in = inside.group(1)
                number_match = re.search(r',\s*(\d+[a-zA-Z]?(/[\d\w]+)?)', raw_rest)
                number_suffix = f", {number_match.group(1)}" if number_match else ""
                candidates.insert(0, f"{city_ua}, {cls._process_street_part(street_in)}{number_suffix}")

            outside = re.sub(r'\(.*?\)', '', raw_rest).strip()
            outside = re.sub(r'\s+,\s+', ', ', outside).strip(' ,')
            candidates.append(f"{city_ua}, {cls._process_street_part(outside)}")

        translated_full = cls._translate_full_string(cleaned)
        if translated_full != cleaned:
            candidates.append(translated_full)

        if len(parts) >= 3:
            street_segment = cls._process_street_part(parts[-2])
            candidates.append(f"{city_ua}, {street_segment}, {parts[-1]}")
            candidates.append(f"{city_ua}, {street_segment}")

        if len(raw_rest) > 3:
            candidates.append(f"{city_ua}, {cls._process_street_part(raw_rest)}")

            street_processed = cls._process_street_part(raw_rest)
            has_marker = any(x in street_processed.lower() for x in
                            ['вулиця', 'вул', 'провулок', 'пров', 'площа', 'майдан'])
            if not has_marker:
                candidates.append(f"{city_ua}, вулиця {street_processed}")

        seen = set()
        final = []
        for c in candidates:
            c_clean = re.sub(r'\s+', ' ', c).strip(', ')
            if c_clean and c_clean.lower() not in seen:
                seen.add(c_clean.lower())
                final.append(c_clean)

        return final

    @classmethod
    def _translate_full_string(cls, text: str) -> str:
        translations = cls._get_translations()
        for k, v in translations.items():
            pattern = re.compile(r'\b' + re.escape(k), re.IGNORECASE)
            text = pattern.sub(v, text)
        return text

    @classmethod
    def _basic_clean(cls, text: str) -> str:
        text = re.sub(r'\b[\w-]+\s+(область|район|р-н)\b\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(м-н|ж/м|массив|микрорайон)\b\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'[№#]', '', text)
        return text.strip().strip(', ')

    @classmethod
    def _process_street_part(cls, text: str) -> str:
        """Translates and normalizes a street name part."""
        translations = cls._get_translations()
        words = text.split()
        new_words = []
        for w in words:
            term = w.lower().strip('.,')
            trans = next((v for k, v in translations.items() if k.lower() == term), None)
            new_words.append(trans if trans else w)

        text = " ".join(new_words)

        # Fix inverted initials: "Шевченко Т." → "Т. Шевченко"
        match = re.search(r'([А-Яа-яїієґA-Za-z]+)\s+([А-Яа-яїієґA-Za-z]\.([А-Яа-яїієґA-Za-z]\.)?)', text)
        if match:
            text = text.replace(match.group(0), f"{match.group(2)} {match.group(1)}")

        return text

    @classmethod
    def extract_from_text(cls, text: str) -> str | None:
        """Extract a likely address from a block of text (description)."""
        if not text:
            return None

        markers_pattern = "|".join([re.escape(m) for m in cls.STREET_MARKERS])

        # Pattern: Marker + Name + Number
        pattern_a = re.compile(
            r'(?:' + markers_pattern + r')\s+'
            r'([А-Яа-яїієґA-Z][\w\-\.]+(?:\s+[А-Яа-яїієґA-Z][\w\-\.]+){0,2})'
            r'[\s,]*'
            r'((?:буд\.|д\.)?\s*\d+[а-яА-Яa-zA-Z]?(?:/\d+)?)',
            re.IGNORECASE
        )

        match = pattern_a.search(text)
        if match:
            return cls._basic_clean(match.group(0))

        # Pattern: Name + Marker + Number
        pattern_b = re.compile(
            r'([А-Яа-яїієґA-Z][\w\-\.]+(?:\s+[А-Яа-яїієґA-Z][\w\-\.]+){0,2})\s+'
            r'(?:' + markers_pattern + r')[\s,]*'
            r'((?:буд\.|д\.)?\s*\d+[а-яА-Яa-zA-Z]?(?:/\d+)?)',
            re.IGNORECASE
        )
        match = pattern_b.search(text)
        if match:
            translations = cls._get_translations()
            if match.group(1) in translations or match.group(1) in translations.values():
                return None
            number = re.sub(r'^(буд\.|д\.)\s*', '', match.group(2))
            return f"вулиця {match.group(1)}, {number}"

        return None
