# MatchSnapper

Приложение для поиска людей по схожести интересов. Пользователь создаёт «слепок» — набор тегов с весами (S/A/B/C/D), система находит похожих людей через косинусное сходство.

## Быстрый старт

### 1. Инфраструктура

```bash
docker compose up -d
```

Поднимает PostgreSQL (5432) и MinIO (9000 API, 9001 консоль).  
MinIO-консоль: http://localhost:9001 — логин `minioadmin` / `minioadmin`

### 2. Бэкенд

```bash
cd backend

# Скопировать и настроить переменные окружения
cp .env.example .env

# Установить зависимости
uv sync

# Применить миграции
uv run alembic upgrade head

# Загрузить фикстуры (51 тег, 25 пользователей)
uv run python fixtures/load_fixtures.py

# Запустить сервер
uv run uvicorn app.main:app --reload --port 9070
```

API: http://localhost:9070  
Swagger: http://localhost:9070/docs

### 3. Фронтенд

```bash
cd frontend
pnpm install
pnpm dev
```

Приложение: http://localhost:3070

## Стек

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2 (async), PostgreSQL, Alembic, JWT, boto3, numpy, Pillow  
**Frontend:** TypeScript, React 18, Vite, Tailwind CSS, TanStack Query, Zustand, Axios  
**Инфра:** Docker Compose, MinIO (dev) / AWS S3 (prod)

## Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DATABASE_URL` | Строка подключения к PostgreSQL | `postgresql+asyncpg://matchsnapper:matchsnapper@localhost:5432/matchsnapper` |
| `SECRET_KEY` | Секрет для JWT (мин. 32 символа) | — |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | TTL access-токена | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | TTL refresh-токена | `7` |
| `STORAGE_BACKEND` | `minio` или `s3` | `minio` |
| `AWS_ACCESS_KEY_ID` | Ключ MinIO/S3 | `minioadmin` |
| `AWS_SECRET_ACCESS_KEY` | Секрет MinIO/S3 | `minioadmin` |
| `AWS_ENDPOINT_URL` | URL MinIO (для S3 — не задавать) | `http://localhost:9000` |
| `AWS_BUCKET_NAME` | Имя бакета | `matchsnapper` |
| `AWS_REGION` | Регион | `us-east-1` |

## API

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh

GET    /api/v1/users/me
PATCH  /api/v1/users/me
POST   /api/v1/users/me/avatar
DELETE /api/v1/users/me/avatar
GET    /api/v1/users/{id}

GET    /api/v1/tags?q=&category=&page=
POST   /api/v1/tags

GET    /api/v1/snapshots/me
PUT    /api/v1/snapshots/me
PATCH  /api/v1/snapshots/me/items
DELETE /api/v1/snapshots/me/items/{tag_id}

GET    /api/v1/matching?page=1&limit=20
GET    /api/v1/matching/{user_id}

POST   /api/v1/users/{id}/view
DELETE /api/v1/users/{id}/view
POST   /api/v1/users/{id}/contact
```

## Тесты

```bash
cd backend
uv run pytest -v
```
