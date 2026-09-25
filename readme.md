# Contacts API

REST API для керування контактами, автентифікації користувачів і завантаження аватара через Cloudinary.

## Запуск

1. Встановіть залежності:

```powershell
poetry install
```

2. Створіть файл `.env` у корені проєкту та додайте налаштування бази даних, JWT і Cloudinary:

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/contacts
JWT_SECRET_KEY=change_me
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

3. Запустіть сервер:

```powershell
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Swagger-документація доступна за адресою:

```text
http://127.0.0.1:8080/docs
```

## Основні можливості

- реєстрація та автентифікація користувачів;
- JWT-захист приватних endpoint;
- CRUD-операції з контактами;
- отримання даних поточного користувача через `GET /users/me`;
- обмеження `GET /users/me` до 10 запитів на хвилину;
- оновлення аватара через `PATCH /users/avatar`;
- збереження URL аватара Cloudinary у профілі користувача;
- CORS для frontend на `http://localhost:3000`.
- Оновлення аватару

