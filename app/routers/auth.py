from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Any

from app.database import get_db
from app.models.user import user_entity
from app.schemas.user import UserCreate, UserResponse, LoginRequest, Token
from app.services.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(payload: UserCreate, db: Database = Depends(get_db)):
    users: Collection[dict[str, Any]] = db["users"]

    existing_user = users.find_one(
        {
            "$or": [
                {"email": payload.email},
                {"username": payload.username},
            ]
        }
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    new_user: dict[str, Any] = {
        "email": payload.email,
        "username": payload.username,
        "password": hash_password(payload.password),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }

    result = users.insert_one(new_user)

    created_user = users.find_one({"_id": result.inserted_id})
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed",
        )

    return user_entity(created_user)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Database = Depends(get_db)):
    users: Collection[dict[str, Any]] = db["users"]

    user = users.find_one({"email": payload.email})

    if not user or not verify_password(payload.password, user.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token({"sub": str(user["_id"])})

    return {"access_token": token, "token_type": "bearer"}
