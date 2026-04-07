# FastAPI + MongoDB Project

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure environment

Create a `.env` file in the project root:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=fastapi_db

SECRET_KEY=change_me_to_a_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

If you use MongoDB Atlas, set `MONGODB_URL` to your Atlas connection string.

## 3. Run server

```bash
uvicorn app.main:app --reload
```

## 4. Available auth routes

- `POST /auth/register`
- `POST /auth/login`
- `GET /users/me`
- `GET /users/{user_id}`
