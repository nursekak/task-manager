# Task Manager API

RESTful API для управления задачами: регистрация/логин (JWT), CRUD задач, фильтры, пагинация, rate limiting, асинхронные email-уведомления при смене статуса (Celery + Redis).

## Стек

- **Backend:** FastAPI
- **БД:** PostgreSQL + SQLAlchemy (ORM)
- **Кэш/очереди:** Redis + Celery
- **Контейнеризация:** Docker + docker-compose
- **Прочее:** JWT (python-jose), Pydantic, Alembic

## Требования

- Python 3.12
- Docker и docker-compose (для полного стека)

## Запуск через Docker (рекомендуется)

```bash
docker-compose up --build
```

Сервисы:

- **API:** http://localhost:8000
- **Swagger (документация):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **PostgreSQL:** localhost:5432 (user: taskmanager, db: taskmanager_db)
- **Redis:** localhost:6379

Перед первым запросом примените миграции (внутри контейнера или с хоста при подключённом PostgreSQL):

```bash
docker-compose exec app alembic upgrade head
```

## Локальный запуск (без Docker)

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Запустите PostgreSQL и Redis (например, локально или в Docker только для БД и Redis).

3. Создайте `.env` или задайте переменные:

```env
DATABASE_URL=postgresql://taskmanager:taskmanager_secret@localhost:5432/taskmanager_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key-change-in-production
```

4. Примените миграции:

```bash
alembic upgrade head
```

5. Запустите API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. В отдельном терминале запустите воркер Celery:

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

## API (кратко)

- **POST /v1/auth/register** — регистрация (email, password).
- **POST /v1/auth/login** — логин, в ответе JWT `access_token`.
- **GET /v1/tasks/** — список задач (авторизация: Bearer token). Параметры: `status`, `created_after`, `created_before`, `page`, `limit`.
- **POST /v1/tasks/** — создание задачи.
- **GET /v1/tasks/{id}** — одна задача.
- **PATCH /v1/tasks/{id}** — обновление (при смене статуса отправляется email-уведомление через Celery).
- **DELETE /v1/tasks/{id}** — удаление.

Полная документация: http://localhost:8000/docs после запуска приложения.

## Тесты

```bash
pytest
```

В тестах используется SQLite и отключён rate limit (Redis не требуется для прогона тестов).

## Структура проекта

```
app/
├── __init__.py
├── main.py          # FastAPI app
├── models.py        # SQLAlchemy модели (User, Task)
├── schemas.py       # Pydantic схемы
├── crud.py          # Бизнес-логика
├── db.py            # Сессия БД, Base
├── api/
│   ├── deps.py      # get_current_user, rate_limit
│   └── v1/
│       ├── auth.py  # /v1/auth
│       └── tasks.py # /v1/tasks
├── core/
│   ├── config.py    # Настройки
│   └── security.py # JWT, хэш паролей
└── tasks/
    ├── celery_app.py
    └── notifications.py  # send_notification(task_id)
tests/
migrations/          # Alembic
docker-compose.yml
Dockerfile
requirements.txt
```

## Версии (из requirements.txt)

- Python 3.12
- fastapi==0.134.0, uvicorn[standard]==0.32.0
- sqlalchemy==2.0.35, alembic==1.15.2, psycopg2-binary==2.9.9
- redis==5.2.1, celery[redis]==5.4.0
- python-jose[cryptography]==3.3.0, pydantic==2.9.2, passlib[bcrypt]==1.7.4
- pytest==8.3.3, httpx==0.27.2
