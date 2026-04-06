<div align="center">

# 🏢 Real Estate Analysis Platform

**Платформа для аналізу та моніторингу ринку нерухомості України**

[![CI Pipeline](https://github.com/kuma4ka/real-estate-analysis-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/kuma4ka/real-estate-analysis-platform/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey?logo=flask)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📖 Зміст

- [Про проєкт](#-про-проєкт)
- [Ключові можливості](#-ключові-можливості)
- [Стек технологій](#-стек-технологій)
- [Архітектура](#-архітектура)
- [Структура проєкту](#-структура-проєкту)
- [Швидкий старт (Docker)](#-швидкий-старт-docker)
- [Локальний розвиток](#-локальний-розвиток)
- [Змінні середовища](#-змінні-середовища)
- [CLI-команди (парсинг та імпорт)](#-cli-команди-парсинг-та-імпорт)
- [API Довідник](#-api-довідник)
- [Тестування](#-тестування)
- [Система ролей та безпека](#-система-ролей-та-безпека)

---

## 🎯 Про проєкт

**Real Estate Analysis Platform** — це повноцінний веб-застосунок для збору, зберігання та аналізу даних про оголошення нерухомості в Україні. Система автоматично збирає дані з відкритих джерел (парсери), нормалізує адреси, геокодує об'єкти та надає аналітичний дашборд із прогнозуванням цін на основі лінійної регресії.

**Мета проєкту** — надати покупцям, рієлторам та аналітикам зручний інструмент для моніторингу ринку нерухомості з функціями: пошуку за фільтрами на карті, перегляду статистики по містах та кімнатності, а також 30-денного прогнозу цін.

---

## ✨ Ключові можливості

| Функція | Опис |
|---|---|
| 🕷️ **Автопарсинг** | Збір оголошень з website Meget.ua та Bon.ua через Cron-задачі у фоновому режимі |
| 🗺️ **Геокодування** | Конвертація текстових адрес у GPS-координати для відображення на карті (Leaflet) |
| 🏙️ **Нормалізація адрес** | Евристичний `AddressNormalizer` обробляє перейменовані вулиці, транслітерацію, двокрапки |
| 💱 **Конвертація валют** | Автоматичний перерахунок UAH/EUR → USD через офіційний API НБУ (кешується на 12 годин) |
| 📊 **Аналітика** | Статистика по містах, кімнатності, ціновим діапазонам із підтримкою фільтрів |
| 📈 **Прогнозування** | Лінійна регресія (NumPy `polyfit`) для 30-денного прогнозу середніх цін з довірчими інтервалами |
| 🔒 **RBAC** | Рольова модель доступу: Guest → User → Analyst → Admin |
| 🌐 **i18n** | Підтримка двох мов: Українська / English (react-i18next) |
| 📤 **Експорт** | Завантаження аналітичної звітності у форматі CSV та PDF (jsPDF) |

---

## 🛠 Стек технологій

### Backend

| Категорія | Технологія |
|---|---|
| Мова / Фреймворк | Python 3.11, Flask 3.1 |
| База даних | PostgreSQL 15 (prod), SQLite (тести) |
| ORM / Міграції | SQLAlchemy 2.0, Flask-Migrate (Alembic) |
| Аутентифікація | PyJWT (HS256), Flask-Limiter (Rate Limiting) |
| Серіалізація | Flask-Marshmallow |
| Парсинг | BeautifulSoup4, cloudscraper, requests |
| Аналітика | Pandas, NumPy |
| Геокодування | geopy |
| Кешування | cachetools TTLCache |
| Валідація даних | Marshmallow schemas |

### Frontend

| Категорія | Технологія |
|---|---|
| UI-фреймворк | React 19, TypeScript 5.9 |
| Збірник | Vite 7 |
| Стилізація | Tailwind CSS 3 |
| Маршрутизація | React Router DOM 7 |
| Карти | Leaflet + react-leaflet, MarkerCluster |
| Графіки | Recharts 3 |
| Інтернаціоналізація | react-i18next |
| PDF/Звіти | jsPDF, html2canvas |

### Infrastructure & Tooling

| Категорія | Технологія |
|---|---|
| Контейнеризація | Docker, Docker Compose |
| Web-сервер (prod) | Nginx (фронтенд) |
| Планувальник задач | Linux Cron (у Docker) |
| CI/CD | GitHub Actions |
| Тестування (backend) | Pytest |
| Тестування (frontend unit) | Vitest, Testing Library |
| Тестування (E2E/UAT) | Cypress 15 |
| Лінтинг (backend) | Flake8, Ruff |
| Лінтинг (frontend) | ESLint |

---

## 🏗 Архітектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        DOCKER COMPOSE                           │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │   Frontend   │    │   Backend    │    │    PostgreSQL    │   │
│  │  React/Vite  │◄──►│  Flask API   │◄──►│      DB :5432    │   │
│  │  Nginx :3000 │    │   :5000      │    │                  │   │
│  └──────────────┘    └──────┬───────┘    └──────────────────┘   │
│                             │                                   │
│                      ┌──────▼───────┐                           │
│                      │ Cron Worker  │                           │
│                      │(Auto-scraper)│                           │
│                      └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### Шари Backend (Services Layer)

```
app/
├── api/           # REST endpoints (Blueprint-и)
│   ├── auth.py    # /auth/* — реєстрація, логін, профіль
│   ├── properties.py  # /properties, /properties/map
│   ├── stats.py   # /stats, /stats/forecast (Analyst+)
│   └── admin.py   # /admin/system (Admin only)
├── core/
│   ├── auth.py    # JWT generate/decode, @require_role decorator
│   └── metrics.py # Uptime, request counter
├── models.py      # SQLAlchemy: User, Property, Source
└── services/
    ├── address_normalizer.py  # Евристична нормалізація адрес
    ├── cities.py              # Каталог міст UA з координатами
    ├── currency.py            # Конвертер валют (NBU API)
    ├── listing_validator.py   # Валідатор якості оголошень
    ├── meget/                 # Парсер Meget.ua
    └── bon_ua/                # Парсер Bon.ua
```

---

## 📁 Структура проєкту

```
real-estate-analysis-platform/
├── .github/
│   └── workflows/ci.yml       # GitHub Actions CI (lint + tests)
├── backend/
│   ├── app/                   # Flask application
│   ├── migrations/            # Alembic DB migrations
│   ├── tests/                 # Pytest test suite (152 tests)
│   ├── config.py              # Config classes
│   ├── run.py                 # Entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # React компоненти
│   │   ├── context/           # AuthContext (React Context API)
│   │   ├── pages/             # Login, Register, Profile
│   │   ├── services/api.ts    # Fetch-обгортки для API
│   │   └── types/             # TypeScript interfaces
│   ├── cypress/e2e/           # UAT тести (Cypress)
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Швидкий старт (Docker)

**Єдиний спосіб запустити весь стек за 3 команди:**

```bash
# 1. Клонуємо репозиторій
git clone https://github.com/kuma4ka/real-estate-analysis-platform.git
cd real-estate-analysis-platform

# 2. Створюємо .env файл зі своїми значеннями
cp .env.example .env
# Відредагуйте .env — замініть значення паролів та SECRET_KEY

# 3. Запускаємо всі сервіси
docker compose up --build -d
```

Після успішного запуску:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000/api/v1/health

```bash
# Перший запуск — застосовуємо міграції БД
docker compose exec backend flask db upgrade

# (Опціонально) Додаємо тестових користувачів
docker compose exec backend flask seed-users
```

---

## 💻 Локальний запуск

### Передумови

- Python 3.11+
- Node.js 20+
- PostgreSQL 15 (або використовуйте Docker лише для БД)

### Backend

```bash
cd backend

# Створюємо та активуємо virtual environment
python -m venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate     # macOS/Linux

# Встановлюємо залежності
pip install -r requirements.txt

# Налаштовуємо змінні середовища
cp .env.example .env
# Відредагуйте DATABASE_URL у .env

# Застосовуємо міграції
flask db upgrade

# Запускаємо сервер розробки
flask run --debug
```

Backend буде доступний за адресою: http://localhost:5000

### Frontend

```bash
cd frontend

# Встановлюємо залежності
npm install

# Запускаємо dev-сервер
npm run dev
```

Frontend буде доступний за адресою: http://localhost:5173

---

## 🔧 Змінні середовища

Скопіюйте `.env.example` у `.env` і заповніть значення:

| Змінна | Опис | Приклад |
|---|---|---|
| `POSTGRES_USER` | Логін PostgreSQL | `postgres` |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | `strongpassword` |
| `POSTGRES_DB` | Назва бази даних | `real_estate_data` |
| `POSTGRES_PORT` | Порт PostgreSQL | `5432` |
| `DATABASE_URL` | Повний URI підключення до БД | `postgresql://user:pass@localhost:5432/db` |
| `SECRET_KEY` | Секретний ключ для підпису JWT | Довгий рандомний рядок |
| `FLASK_APP` | Entry point Flask | `run.py` |
| `FLASK_DEBUG` | Режим налагодження (0/1) | `0` (prod), `1` (dev) |

> ⚠️ **Ніколи не комітьте `.env` файл!** Він вже доданий до `.gitignore`.

---

## ⚡ CLI-команди (парсинг та імпорт)

Ці команди запускаються від імені Flask (`flask <команда>`) і призначені для ручного або планованого збору/обробки даних.

```bash
# Запуск парсера Meget.ua (основне джерело)
flask scrape-meget

# Запуск парсера Bon.ua
flask scrape-bon-ua

# Геокодування всіх об'єктів без координат
flask regeocode-all

# Геокодування конкретних об'єктів за їх ID
flask regeocode-ids 1 2 3 42

# Конвертація цін з UAH/EUR у USD через API НБУ
flask convert-currencies

# Повторне парсингу дублікатів (з виправленими адресами)
flask rescrape-duplicates

# Завантаження зображень для оголошень без фото
flask backfill-images

# Додання тестових користувачів (User, Analyst, Admin)
flask seed-users

# Ініціалізація таблиці джерел
flask seed-sources
```

---

## 📡 API Довідник

Всі endpoints мають префікс `/api/v1`.

### Auth — `/auth`

| Метод | Endpoint | Доступ | Опис |
|---|---|---|---|
| `POST` | `/auth/register` | Public | Реєстрація (ліміт: 5/день) |
| `POST` | `/auth/login` | Public | Логін, повертає JWT-токен (ліміт: 10/хв) |
| `GET` | `/auth/me` | 🔒 Auth | Профіль поточного користувача |
| `PUT` | `/auth/me/password` | 🔒 Auth | Зміна пароля (ліміт: 5/год) |

**Приклад: Реєстрація**
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "Secure123!"}'
```

**Вимоги до пароля:** мін. 8 символів, 1 велика літера, 1 цифра, 1 спецсимвол.

---

### Properties — `/properties`

| Метод | Endpoint | Доступ | Опис |
|---|---|---|---|
| `GET` | `/properties` | Public\* | Список оголошень з пагінацією та фільтрами |
| `GET` | `/properties/<id>` | Public\* | Деталі конкретного оголошення |
| `GET` | `/properties/map` | Public\* | Геодані для карти (лише з координатами) |
| `GET` | `/health` | Public | Health check сервісу |

\* *Гостям (`source_url` приховано). Авторизовані бачать повні дані.*

**Query параметри для `/properties`:**

| Параметр | Тип | Опис | Приклад |
|---|---|---|---|
| `page` | int | Номер сторінки (default: 1) | `?page=2` |
| `per_page` | int | Записів на сторінку (default: 20) | `?per_page=12` |
| `city` | string | Місто (UA або EN назва) | `?city=Kyiv` або `?city=Київ` |
| `rooms` | int | Кількість кімнат | `?rooms=2` |
| `price_min` | float | Мінімальна ціна (USD) | `?price_min=30000` |
| `price_max` | float | Максимальна ціна (USD) | `?price_max=100000` |
| `sort` | string | Сортування: `newest`, `cheapest`, `expensive` | `?sort=cheapest` |
| `search` | string | Пошук за назвою/адресою | `?search=центр` |

---

### Statistics — `/stats`

| Метод | Endpoint | Доступ | Опис |
|---|---|---|---|
| `GET` | `/stats` | 🔒 Analyst+ | Зведена статистика ринку (кешується 10 хв) |
| `GET` | `/stats/forecast` | 🔒 Analyst+ | 30-денний прогноз цін (лінійна регресія) |
| `GET` | `/stats/export` | 🔒 Analyst+ | Експорт статистики у CSV |

**Параметр `/stats/forecast`:**

| Параметр | Опис |
|---|---|
| `city` | (необов'язково) Фільтр по місту для прогнозу |

**Відповідь прогнозу:**
```json
{
  "city": "Київ",
  "r_squared": 0.87,
  "slope_per_day": 12.5,
  "historical": [{"date": "2025-01-01", "avg_price": 48000}],
  "forecast": [{"date": "2025-02-01", "predicted_price": 49000, "lower": 47000, "upper": 51000}]
}
```

---

### Admin — `/admin`

| Метод | Endpoint | Доступ | Опис |
|---|---|---|---|
| `GET` | `/admin/system` | 🔒 Admin | Системні метрики: кількість користувачів, uptime, статус БД |

---

## 🧪 Тестування

Проєкт має повну піраміду тестування:

```
        ╔═══════════════════╗
        ║  UAT (Cypress)    ║  ← 9 E2E сценаріїв (TC_001-TC_011)
        ╠═══════════════════╣
        ║  System Tests     ║  ← 10 тестів (TC_013-TC_022)
        ╠═══════════════════╣
        ║  Integration      ║  ← ~80 тестів (Auth, Properties, Stats, Admin)
        ╠═══════════════════╣
        ║  Unit Tests       ║  ← ~60 тестів (Models, Services, Parsers)
        ╚═══════════════════╝
```

### Запуск Backend тестів (Pytest)

```bash
cd backend
source .venv/Scripts/activate  # Windows
# або: source .venv/bin/activate  # macOS/Linux

# Всі тести (152 тести)
pytest -v

# Тільки unit тести
pytest tests/test_models.py tests/test_currency.py tests/test_address_normalizer.py -v

# Тільки integration тести
pytest tests/test_auth.py tests/test_properties_integration.py tests/test_stats_api.py -v

# Тільки system тести
pytest tests/test_system_e2e.py -v

# З покриттям (потрібен pytest-cov)
pytest --cov=app --cov-report=html
```

### Запуск Frontend Unit тестів (Vitest)

```bash
cd frontend

# Одноразовий запуск (CI-режим)
npm run test:run

# Watch-режим (розробка)
npm run test
```

### Запуск UAT тестів (Cypress)

```bash
cd frontend

# Термінал 1: запускаємо frontend dev-сервер
npm run dev

# Термінал 2: запускаємо Cypress в headless-режимі
npx cypress run

# Або відкриваємо інтерактивний UI Cypress
npx cypress open
```

### Поточний стан тестів

| Рівень | Інструмент | Тестів | Статус |
|---|---|---|---|
| Unit (backend) | Pytest | ~60 | ✅ Pass |
| Integration (backend) | Pytest | ~82 | ✅ Pass |
| System (backend) | Pytest | 10 | ✅ Pass |
| Unit (frontend) | Vitest | 47 | ✅ Pass |
| UAT (E2E) | Cypress | 9 | ✅ Pass |
| **Загалом** | | **208** | **✅ All Pass** |

---

## 🔐 Система ролей та безпека

### Ролі користувачів

| Роль | Доступ |
|---|---|
| **Guest** (неавтор.) | Перегляд оголошень без `source_url` |
| **User** | Повні дані оголошень + зміна пароля |
| **Analyst** | User + доступ до статистики та прогнозів + CSV-експорт |
| **Admin** | Analyst + системні метрики (`/admin/system`) |

### Заходи безпеки

- **Rate Limiting:** Реєстрація — 5/день, Логін — 10/хв, Зміна пароля — 5/год
- **Account Lockout:** Після 5 невдалих спроб входу — блокування на 15 хвилин
- **JWT Authentication:** Токени HS256, строк дії налаштовується через `SECRET_KEY`
- **Input Validation:** Marshmallow-схеми для всіх вхідних даних
- **Password Policy:** Мін. 8 символів, uppercase, цифра, спецсимвол

---

## 📄 Ліцензія

Цей проєкт розповсюджується під ліцензією [MIT](LICENSE).

---

<div align="center">
  <sub>Розроблено як дипломний проєкт бакалавра</sub>
</div>