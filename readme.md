# Contacts API

REST API для управління контактами, автентифікації користувачів, скидання пароля та роботи з аватарками через Cloudinary.

## Опис проєкту

Цей проєкт реалізує бекенд-сервіс на FastAPI для роботи з контактами користувача. Основні функції:

- реєстрація та логін користувачів;
- підтвердження email через токен;
- JWT-автентифікація;
- CRUD для контактів;
- пошук та фільтрація контактів;
- перевірка днів до ДР;
- скидання пароля через Redis-токени;
- завантаження та збереження аватара в Cloudinary;
- rate limiting для захисту endpoint;
- контейнеризація через Docker Compose.

## Технології

- Python 3.13+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- JWT (PyJWT)
- Cloudinary
- SlowAPI
- Docker / Docker Compose
- Pytest

## Структура проєкту

```text
.
├── app/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── contacts.py
│   │   └── users.py
│   ├── crud.py
│   ├── database.py
│   ├── dependencies.py
│   ├── email_service.py
│   ├── email_verification.py
│   ├── limiter.py
│   ├── main.py
│   ├── models.py
│   ├── password_reset.py
│   ├── schemas.py
│   ├── security.py
│   └── __init__.py
├── docs/
├── tests/
├── compose.yaml
├── create_tables.py
├── Dockerfile
├── pyproject.toml
├── readme.md
└── .env
```

## Передумови

Перед запуском переконайтеся, що встановлено:

- Python 3.13+
- Poetry
- Docker та Docker Compose
- PostgreSQL (якщо запускаєте без контейнера)

## Налаштування середовища

Створіть файл `.env` у корені проєкту на основі такого шаблону:

```env
POSTGRES_USER=contacts_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=contacts_db

DATABASE_URL=postgresql+psycopg://contacts_user:your_secure_password@localhost:5432/contacts_db

JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

REDIS_HOST=localhost
REDIS_PORT=6379

MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_FROM=your_email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
MAIL_FROM_NAME=Contacts API

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

> Для Docker Compose змінні `POSTGRES_USER`, `POSTGRES_PASSWORD` та `POSTGRES_DB` також використовуються у файлі `compose.yaml`.

## Запуск локально

1. Встановіть залежності:

```bash
poetry install
```

2. Активуйте віртуальне середовище:

```bash
poetry shell
```

3. Запустіть сервер FastAPI:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

4. Відкрийте Swagger UI:

```text
http://127.0.0.1:8080/docs
```

## Запуск через Docker Compose

1. Переконайтеся, що у корені є файл `.env`.
2. Запустіть контейнеризацію:

```bash
docker compose up --build
```

3. API буде доступне за адресою:

```text
http://localhost:8080/docs
```

4. Для зупинки:

```bash
docker compose down
```

## Основні API endpoint

### Аутентифікація

- `POST /auth/register` — реєстрація користувача
- `GET /auth/verify-email?token=...` — підтвердження email
- `POST /auth/login` — логін і отримання JWT
- `POST /auth/password-reset` — запит на скидання пароля
- `POST /auth/password-reset/confirm` — підтвердження скидання пароля

### Користувачі

- `GET /users/me` — отримати поточного користувача
- `PATCH /users/avatar` — оновити аватар

### Контакти

- `GET /contacts/` — список контактів користувача
- `GET /contacts/{contact_id}` — отримати контакт за ID
- `POST /contacts/` — створити контакт
- `PUT /contacts/{contact_id}` — оновити контакт
- `DELETE /contacts/{contact_id}` — видалити контакт
- `GET /contacts/search` — пошук контактів
- `GET /contacts/birthdays` — контакти з найближчими днями народження

## Ролі та доступ

- Звичайний користувач може:
  - реєструватися;
  - логінитися;
  - керувати власними контактами;
  - переглядати власний профіль.
- Адміністратор може оновлювати аватар користувача через endpoint `/users/avatar`.

## Обмеження швидкості

Для endpoint `/users/me` використовується rate limiting:

```text
10 requests / minute
```

## Тести

Для запуску тестів використовуйте:

```bash
pytest
```

Або з покриттям:

```bash
pytest --cov=app
```


