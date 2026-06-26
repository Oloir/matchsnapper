# MatchSnapper — MVP: план проекта (v2)

> Приложение для поиска людей по схожести интересов («слепков»)

---

## 1. Концепция и требования MVP

### Что делает приложение
Пользователь создаёт **«слепок»** — набор тегов интересов с весами (S/A/B/C/D).
Система находит других пользователей, чьи слепки наиболее близки.

### Ключевые сущности
| Сущность | Описание |
|---|---|
| **User** | Аккаунт + профиль (аватар, bio) |
| **Tag** | Тег интереса (футбол, музыка, …) |
| **SnapshotItem** | Пара tag + weight в профиле пользователя |
| **ProfileView** | Факт просмотра одним пользователем другого |
| **ContactRequest** | Заглушка для будущего чата |

### Веса
```
S = 5  A = 4  B = 3  C = 2  D = 1
```

### Теги
- Базовый набор загружается из фикстуры (`fixtures/tags.json`)
- Любой авторизованный пользователь может добавить новый тег
- Модерация — вне MVP (добавляется отдельным модулем позже)

---

## 2. Алгоритм схожести — Cosine Similarity

Для двух пользователей строятся векторы по **объединению всех тегов**:

```
User A: { футбол:S, сериалы:A, музыка:B }  → [5, 4, 3, 0, 0]
User B: { футбол:S, музыка:A, чтение:C }   → [5, 0, 4, 3, 0]

similarity = dot(A, B) / (|A| * |B|)
           = (25 + 12) / (sqrt(50) * sqrt(50)) ≈ 0.74
```

### Сортировка в выдаче матчинга
```
непросмотренные пользователи  → по score DESC
        +
просмотренные пользователи    → по score DESC
        ↓
пагинация по этому объединённому списку
```

**Для MVP:** считается в Python/numpy.
**Масштабирование:** pgvector — без изменения API.

---

## 3. Технологический стек

### Backend
| Библиотека | Роль |
|---|---|
| **FastAPI** | Web framework (async, автодокументация) |
| **SQLAlchemy 2.x** | ORM |
| **Alembic** | Миграции БД |
| **PostgreSQL** | БД |
| **python-jose** | JWT токены |
| **passlib[bcrypt]** | Хэширование паролей |
| **boto3** | S3 / MinIO (хранение аватаров) |
| **numpy** | Cosine similarity |
| **Pillow** | Ресайз аватара перед загрузкой |
| **pytest + httpx** | Тесты |

### Frontend
| Библиотека | Роль |
|---|---|
| **React 18 + TypeScript** | UI |
| **Vite** | Bundler |
| **React Router v6** | Routing |
| **TanStack Query** | Серверный стейт, кэш |
| **Axios** | HTTP клиент + интерцепторы токенов |
| **Tailwind CSS** | Стили |
| **Zustand** | Клиентский стейт (auth) |

### Инфраструктура
| Инструмент | Роль |
|---|---|
| **Docker Compose** | PostgreSQL + MinIO для локальной разработки |
| **MinIO** | S3-совместимое хранилище (локально) |
| **AWS S3** | Хранилище в production |
| **pnpm** | Пакетный менеджер фронта |

---

## 4. Хранилище файлов (S3 / MinIO)

### Принцип: один код для dev и prod

```python
# config.py
STORAGE_BACKEND: str = "minio"         # "minio" | "s3"
AWS_ACCESS_KEY_ID: str = "minioadmin"
AWS_SECRET_ACCESS_KEY: str = "minioadmin"
AWS_ENDPOINT_URL: str | None = "http://localhost:9000"  # None → real S3
AWS_BUCKET_NAME: str = "matchsnapper"
AWS_REGION: str = "us-east-1"
```

boto3 использует `endpoint_url=None` для реального S3 и `endpoint_url="http://..."` для MinIO — **код не меняется**, только конфиг.

### Флоу загрузки аватара
```
Client → POST /api/v1/users/me/avatar (multipart/form-data)
       ↓
Backend: Pillow resize → 256×256px JPEG
       ↓
boto3 upload → MinIO/S3: avatars/{user_id}.jpg
       ↓
Сохранить avatar_url в users.avatar_url
       ↓
Response: { avatar_url: "https://..." }
```

### docker-compose.yml (dev)
```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: matchsnapper
      POSTGRES_USER: matchsnapper
      POSTGRES_PASSWORD: matchsnapper
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

  minio:
    image: minio/minio
    ports:
      - "9000:9000"   # API
      - "9001:9001"   # Web Console → http://localhost:9001
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes: [minio_data:/data]

volumes:
  postgres_data:
  minio_data:
```

---

## 5. База данных — схема

```sql
-- Пользователи
CREATE TABLE users (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email            VARCHAR(255) UNIQUE NOT NULL,
    username         VARCHAR(100) UNIQUE NOT NULL,
    hashed_password  VARCHAR(255) NOT NULL,
    avatar_url       VARCHAR(500),
    bio              TEXT,                        -- короткое "о себе"
    is_active        BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMP DEFAULT now()
);

-- Теги интересов (глобальный справочник)
CREATE TABLE tags (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name      VARCHAR(100) UNIQUE NOT NULL,       -- 'футбол', 'музыка', …
    category  VARCHAR(100),                       -- 'спорт', 'культура', …
    created_by UUID REFERENCES users(id),         -- NULL = из фикстуры
    created_at TIMESTAMP DEFAULT now()
);

-- Слепок: позиции интереса пользователя
CREATE TABLE snapshot_items (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tag_id   UUID NOT NULL REFERENCES tags(id),
    weight   SMALLINT NOT NULL CHECK (weight BETWEEN 1 AND 5),
    -- 1=D, 2=C, 3=B, 4=A, 5=S
    UNIQUE (user_id, tag_id)
);

-- Просмотренные профили
CREATE TABLE profile_views (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    viewer_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    viewed_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (viewer_id, viewed_id)
);

-- Будущий чат — заглушка (таблица создаётся сейчас, логика — позже)
CREATE TABLE contact_requests (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_user_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status       VARCHAR(20) DEFAULT 'pending',  -- pending / accepted / declined
    created_at   TIMESTAMP DEFAULT now(),
    UNIQUE (from_user_id, to_user_id)
);

-- Индексы
CREATE INDEX idx_snapshot_user    ON snapshot_items(user_id);
CREATE INDEX idx_snapshot_tag     ON snapshot_items(tag_id);
CREATE INDEX idx_views_viewer     ON profile_views(viewer_id);
CREATE INDEX idx_views_viewed     ON profile_views(viewed_id);
CREATE INDEX idx_contact_from     ON contact_requests(from_user_id);
CREATE INDEX idx_contact_to       ON contact_requests(to_user_id);
```

---

## 6. API эндпоинты

```
# Auth
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh

# Профиль
GET    /api/v1/users/me
PATCH  /api/v1/users/me                       # обновить bio
POST   /api/v1/users/me/avatar                # загрузить аватар (multipart)
DELETE /api/v1/users/me/avatar                # удалить аватар
GET    /api/v1/users/{id}                     # публичный профиль

# Теги
GET    /api/v1/tags?q=&category=&page=        # поиск тегов
POST   /api/v1/tags                           # создать новый тег (любой юзер)

# Слепок
GET    /api/v1/snapshots/me
PUT    /api/v1/snapshots/me                   # полная замена [{tag_id, weight}, …]
PATCH  /api/v1/snapshots/me/items             # добавить/обновить один тег
DELETE /api/v1/snapshots/me/items/{tag_id}    # удалить тег

# Матчинг
GET    /api/v1/matching?page=1&limit=20       # список похожих (с пагинацией)
GET    /api/v1/matching/{user_id}             # схожесть с конкретным

# Взаимодействия
POST   /api/v1/users/{id}/view                # отметить как просмотренный
DELETE /api/v1/users/{id}/view                # снять отметку

# Контакт (MVP: создаёт запись, фронт показывает статус)
POST   /api/v1/users/{id}/contact             # отправить "запрос на контакт"
```

### Ответ матчинга с пагинацией
```json
{
  "results": [
    {
      "user": {
        "id": "...",
        "username": "alex",
        "avatar_url": "https://...",
        "bio": "Люблю футбол и кино"
      },
      "score": 0.87,
      "is_viewed": false,
      "common_tags": [
        { "tag": "футбол",  "weight_mine": "S", "weight_theirs": "S" },
        { "tag": "музыка",  "weight_mine": "B", "weight_theirs": "A" }
      ]
    }
  ],
  "total": 142,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

---

## 7. Модуль авторизации — расширяемость

```python
# app/auth/base.py
from abc import ABC, abstractmethod

class AuthProvider(ABC):
    @abstractmethod
    async def authenticate(self, credentials: dict) -> User | None: ...
    @abstractmethod
    async def create_user(self, data: dict) -> User: ...

# app/auth/jwt_provider.py  ← MVP
class JWTAuthProvider(AuthProvider):
    async def authenticate(self, credentials):
        # email + password → JWT
        ...

# app/auth/oauth_provider.py  ← будущий Google/VK (заглушка)
class OAuthProvider(AuthProvider):
    def __init__(self, provider_name: str):  # 'google', 'vk', 'github'
        ...
```

---

## 8. Структура проекта

```
matchsnapper/
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, роутеры
│   │   ├── config.py                # Settings (pydantic-settings)
│   │   ├── database.py              # Async SQLAlchemy session
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── tag.py
│   │   │   ├── snapshot.py
│   │   │   └── interactions.py      # ProfileView, ContactRequest
│   │   │
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── auth.py
│   │   │   ├── tag.py
│   │   │   ├── snapshot.py
│   │   │   └── matching.py
│   │   │
│   │   ├── api/v1/
│   │   │   ├── router.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── tags.py
│   │   │   ├── snapshots.py
│   │   │   ├── matching.py
│   │   │   └── interactions.py
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── snapshot_service.py
│   │   │   ├── matching_service.py  # cosine similarity
│   │   │   └── storage_service.py   # S3 / MinIO upload
│   │   │
│   │   └── auth/
│   │       ├── base.py
│   │       ├── jwt_provider.py
│   │       └── oauth_provider.py    # заглушка
│   │
│   ├── alembic/versions/
│   ├── fixtures/
│   │   ├── tags.json
│   │   ├── users.json
│   │   └── load_fixtures.py
│   ├── tests/
│   ├── pyproject.toml           # зависимости (uv)
│   ├── uv.lock
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── users.ts
│   │   │   ├── snapshots.ts
│   │   │   └── matching.ts
│   │   │
│   │   ├── store/
│   │   │   └── authStore.ts
│   │   │
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── ProfilePage.tsx
│   │   │   ├── SnapshotEditorPage.tsx
│   │   │   └── MatchesPage.tsx
│   │   │
│   │   └── components/
│   │       ├── SnapshotEditor/
│   │       │   ├── TagSearch.tsx       # autocomplete + создание нового тега
│   │       │   ├── WeightSelector.tsx  # S/A/B/C/D пикер
│   │       │   └── SnapshotItem.tsx
│   │       ├── MatchCard.tsx           # score + common tags + кнопки
│   │       ├── AvatarUpload.tsx
│   │       └── Layout.tsx
│   │
│   └── package.json
│
├── docker-compose.yml
├── CLAUDE.md
└── README.md
```

---

## 9. Фикстуры

### `fixtures/tags.json` (~50 тегов)
```json
[
  {"name": "футбол",            "category": "спорт"},
  {"name": "баскетбол",         "category": "спорт"},
  {"name": "программирование",  "category": "технологии"},
  {"name": "дизайн",            "category": "творчество"},
  {"name": "музыка",            "category": "культура"},
  {"name": "кино",              "category": "культура"},
  {"name": "сериалы",           "category": "культура"},
  {"name": "чтение",            "category": "культура"},
  {"name": "путешествия",       "category": "хобби"},
  ...
]
```

### `fixtures/users.json` (~25 пользователей)
```json
[
  {
    "email": "alex@test.com",
    "username": "alex",
    "password": "testpass123",
    "bio": "Обожаю футбол и технологии",
    "snapshot": [
      {"tag": "футбол",           "weight": "S"},
      {"tag": "программирование", "weight": "A"},
      {"tag": "сериалы",          "weight": "B"}
    ]
  }
]
```

Пользователи должны **разнообразно** покрывать комбинации тегов — чтобы алгоритм матчинга давал осмысленные результаты при тестировании.

---

## 10. CLAUDE.md

```markdown
# MatchSnapper — Claude Code Context

## Tech Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy 2 (async), PostgreSQL, Alembic
- Frontend: TypeScript, React 18, Vite, TailwindCSS, TanStack Query, Zustand
- Storage: MinIO (dev) / AWS S3 (prod) via boto3

## Commands
### Backend
cd backend
uv sync                                  # установить зависимости из uv.lock
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 9070
uv run pytest -v
uv run python fixtures/load_fixtures.py

# Добавить зависимость:
uv add fastapi
uv add --dev pytest httpx

### Frontend
cd frontend
pnpm install
pnpm dev        # порт 3070, proxy → localhost:9070

### Infra
docker compose up -d    # PostgreSQL + MinIO
# MinIO console: http://localhost:9001 (minioadmin / minioadmin)

## Env
DATABASE_URL=postgresql+asyncpg://matchsnapper:matchsnapper@localhost:5432/matchsnapper
SECRET_KEY=<random_32_bytes>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
STORAGE_BACKEND=minio
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_ENDPOINT_URL=http://localhost:9000
AWS_BUCKET_NAME=matchsnapper
AWS_REGION=us-east-1

## Architecture
- Auth: JWTAuthProvider implements AuthProvider ABC → позже OAuthProvider
- Matching: cosine similarity (numpy), sort: unviewed first, then viewed
- Weights: S=5, A=4, B=3, C=2, D=1
- File upload: Pillow resize 256×256 → boto3 → MinIO/S3
- All IDs: UUID
- Pagination: page + limit на всех list-эндпоинтах

## Conventions
- Роутеры тонкие — вся логика в services/
- Pydantic v2 для всех схем I/O
- Async везде в бэке
- contact_requests — таблица создана, эндпоинт есть, UI — кнопка-заглушка
```

---

## 11. Роадмап разработки

### Фаза 0 — Инфраструктура
- [ ] Структура папок + git init
- [ ] `docker-compose.yml` (Postgres + MinIO)
- [ ] Backend: FastAPI skeleton, config, database.py
- [ ] Frontend: Vite + React + Tailwind scaffold
- [ ] `CLAUDE.md`

### Фаза 1 — Модели и БД
- [ ] SQLAlchemy модели: User, Tag, SnapshotItem, ProfileView, ContactRequest
- [ ] Alembic: первая миграция
- [ ] Pydantic v2 схемы

### Фаза 2 — Авторизация
- [ ] AuthProvider ABC + JWTAuthProvider
- [ ] Эндпоинты: register, login, refresh
- [ ] Dependency `get_current_user`
- [ ] Тесты

### Фаза 3 — Профиль и аватар
- [ ] StorageService (boto3, MinIO/S3)
- [ ] Эндпоинты: GET/PATCH /users/me, POST/DELETE /users/me/avatar
- [ ] Pillow ресайз
- [ ] Тесты

### Фаза 4 — Теги и слепок
- [ ] CRUD теги + эндпоинты (с поиском)
- [ ] CRUD слепок + эндпоинты
- [ ] Тесты

### Фаза 5 — Матчинг и взаимодействия
- [ ] MatchingService: cosine similarity + сортировка с учётом просмотров
- [ ] Эндпоинты: /matching, /users/{id}/view, /users/{id}/contact
- [ ] Тесты с фикстурными данными

### Фаза 6 — Фикстуры
- [ ] `fixtures/tags.json` (~50 тегов, 8-10 категорий)
- [ ] `fixtures/users.json` (~25 пользователей с разными слепками)
- [ ] `load_fixtures.py`
- [ ] Проверка качества матчинга на фикстурах

### Фаза 7 — Frontend
- [ ] Axios client + auth интерцепторы + refresh token rotation
- [ ] Auth store (Zustand): login / logout / persist
- [ ] Pages: Login, Register
- [ ] Pages: ProfilePage + AvatarUpload + bio
- [ ] Pages: SnapshotEditorPage (TagSearch с autocomplete, WeightSelector)
- [ ] Pages: MatchesPage (список + пагинация + MatchCard)
- [ ] MatchCard: score, аватар, bio, common tags, кнопки «Просмотрен» и «Написать»

### Фаза 8 — Интеграция и полировка
- [ ] Vite proxy → FastAPI (dev)
- [ ] CORS настройка
- [ ] End-to-end проверка всех флоу
- [ ] README с инструкцией запуска