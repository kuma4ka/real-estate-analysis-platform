CITIES = {
    'Київ': {
        'lat': 50.4501, 'lng': 30.5234,
        'aliases': ['Киев', 'Kyiv', 'Kiev'],
    },
    'Харків': {
        'lat': 49.9935, 'lng': 36.2304,
        'aliases': ['Харьков', 'Kharkiv', 'Kharkov'],
    },
    'Львів': {
        'lat': 49.8397, 'lng': 24.0297,
        'aliases': ['Львов', 'Lviv', 'Lvov'],
    },
    'Одеса': {
        'lat': 46.4825, 'lng': 30.7233,
        'aliases': ['Одесса', 'Odesa', 'Odessa'],
    },
    'Дніпро': {
        'lat': 48.4647, 'lng': 35.0462,
        'aliases': ['Днепр', 'Dnipro', 'Днепропетровск'],
    },
    'Вінниця': {
        'lat': 49.2331, 'lng': 28.4682,
        'aliases': ['Винница', 'Vinnytsia'],
    },
    'Запоріжжя': {
        'lat': 47.8388, 'lng': 35.1396,
        'aliases': ['Запорожье', 'Zaporizhzhia'],
    },
    'Івано-Франківськ': {
        'lat': 48.9226, 'lng': 24.7111,
        'aliases': ['Ивано-Франковск', 'Ivano-Frankivsk'],
    },
    'Тернопіль': {
        'lat': 49.5535, 'lng': 25.5948,
        'aliases': ['Тернополь', 'Ternopil'],
    },
    'Полтава': {
        'lat': 49.5883, 'lng': 34.5514,
        'aliases': ['Poltava'],
    },
    'Рівне': {
        'lat': 50.6199, 'lng': 26.2516,
        'aliases': ['Ровно', 'Rivne'],
    },
    'Хмельницький': {
        'lat': 49.4230, 'lng': 26.9871,
        'aliases': ['Хмельницкий', 'Khmelnytskyi'],
    },
    'Черкаси': {
        'lat': 49.4444, 'lng': 32.0598,
        'aliases': ['Черкассы', 'Cherkasy'],
    },
    'Чернігів': {
        'lat': 51.4982, 'lng': 31.2893,
        'aliases': ['Чернигов', 'Chernihiv'],
    },
    'Чернівці': {
        'lat': 48.2921, 'lng': 25.9358,
        'aliases': ['Черновцы', 'Chernivtsi'],
    },
    'Житомир': {
        'lat': 50.2547, 'lng': 28.6587,
        'aliases': ['Zhytomyr'],
    },
    'Миколаїв': {
        'lat': 46.9750, 'lng': 31.9946,
        'aliases': ['Николаев', 'Mykolaiv'],
    },
    'Суми': {
        'lat': 50.9077, 'lng': 34.7981,
        'aliases': ['Сумы', 'Sumy'],
    },
    'Херсон': {
        'lat': 46.6354, 'lng': 32.6169,
        'aliases': ['Kherson'],
    },
    'Луцьк': {
        'lat': 50.7472, 'lng': 25.3254,
        'aliases': ['Луцк', 'Lutsk'],
    },
    'Ужгород': {
        'lat': 48.6208, 'lng': 22.2879,
        'aliases': ['Uzhhorod'],
    },
    'Біла Церква': {
        'lat': 49.7953, 'lng': 30.1108,
        'aliases': ['Белая Церковь', 'Bila Tserkva'],
    },
    'Кропивницький': {
        'lat': 48.5079, 'lng': 32.2623,
        'aliases': ['Кировоград', 'Kropyvnytskyi'],
    },
    'Бровари': {
        'lat': 50.5107, 'lng': 30.7938,
        'aliases': ['Бровары', 'Brovary'],
    },
    'Бориспіль': {
        'lat': 50.3533, 'lng': 30.9567,
        'aliases': ['Борисполь', 'Boryspil'],
    },
    'Ірпінь': {
        'lat': 50.5216, 'lng': 30.2509,
        'aliases': ['Ирпень', 'Irpin'],
    },
    'Буча': {
        'lat': 50.5486, 'lng': 30.2212,
        'aliases': ['Bucha'],
    },
    'Вишневе': {
        'lat': 50.3886, 'lng': 30.3720,
        'aliases': ['Вишневое', 'Vyshneve'],
    },
    'Обухів': {
        'lat': 50.1069, 'lng': 30.6226,
        'aliases': ['Обухов', 'Obukhiv'],
    },
    "Кам'янське": {
        'lat': 48.5188, 'lng': 34.6139,
        'aliases': ['Каменское', 'Днепродзержинск', 'Kamianske'],
    },
    'Нікополь': {
        'lat': 47.5723, 'lng': 34.3939,
        'aliases': ['Никополь', 'Nikopol'],
    },
    'Маріуполь': {
        'lat': 47.0958, 'lng': 37.5532,
        'aliases': ['Мариуполь', 'Mariupol'],
    },
    'Кременчук': {
        'lat': 49.0653, 'lng': 33.4106,
        'aliases': ['Кременчуг', 'Kremenchuk'],
    },
}

_ALIAS_MAP: dict[str, str] = {}
for canonical, info in CITIES.items():
    _ALIAS_MAP[canonical.lower()] = canonical
    for alias in info['aliases']:
        _ALIAS_MAP[alias.lower()] = canonical

_CENTER_MAP: dict[str, tuple[float, float]] = {}
for canonical, info in CITIES.items():
    center = (info['lat'], info['lng'])
    _CENTER_MAP[canonical] = center
    for alias in info['aliases']:
        _CENTER_MAP[alias] = center


def normalize_city(name: str) -> str | None:
    if not name:
        return None
    return _ALIAS_MAP.get(name.strip().lower())


def get_center(name: str) -> tuple[float, float] | None:
    if not name:
        return None
    canonical = normalize_city(name)
    if canonical:
        return _CENTER_MAP.get(canonical)
    return _CENTER_MAP.get(name)


def get_all_aliases() -> dict[str, str]:
    return dict(_ALIAS_MAP)


_REGION_SUFFIXES = ['ська', 'ская', 'ський', 'ский', 'ське', 'ское']


def _build_region_map() -> dict[str, str]:
    region_map: dict[str, str] = {}
    for canonical, info in CITIES.items():
        root = canonical.lower()[:5]
        region_map[root] = canonical
        for alias in info['aliases']:
            if len(alias) >= 3:
                alias_root = alias.lower()[:5]
                if alias_root not in region_map:
                    region_map[alias_root] = canonical
    return region_map

_REGION_MAP = _build_region_map()


def get_region_center(region_name: str) -> tuple[tuple[float, float], str] | None:
    if not region_name:
        return None

    cleaned = region_name.lower().replace('область', '').strip()
    for suffix in _REGION_SUFFIXES:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)]
            break

    root = cleaned.strip()[:5]
    if root and root in _REGION_MAP:
        city = _REGION_MAP[root]
        center = get_center(city)
        if center:
            return center, city

    return None
