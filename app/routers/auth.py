from fastapi import APIRouter, Depends, HTTPException, Response, status
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Any

from app.database import get_db
from app.models.user import user_entity
from app.schemas.user import LoginRequest, RefreshTokenRequest, Token, UserCreate, UserResponse
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_refresh_token_expiry,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _issue_tokens(user_id: str, refresh_tokens: Collection[dict[str, Any]]) -> dict[str, str]:
    access_token = create_access_token({"sub": user_id})
    refresh_token = create_refresh_token({"sub": user_id})

    refresh_tokens.insert_one(
        {
            "userId": user_id,
            "tokenHash": hash_token(refresh_token),
            "createdAt": datetime.now(timezone.utc),
            "expiresAt": get_refresh_token_expiry(),
        }
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(payload: UserCreate, db: Database = Depends(get_db)):
    users: Collection[dict[str, Any]] = db["users"]
    normalized_email = _normalize_email(str(payload.email))

    existing_user = users.find_one(
        {
            "$or": [
                {"email_normalized": normalized_email},
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
        "email": normalized_email,
        "email_normalized": normalized_email,
        "name": payload.username,
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
    refresh_tokens: Collection[dict[str, Any]] = db["refresh_tokens"]
    normalized_email = _normalize_email(str(payload.email))

    user = users.find_one({"email_normalized": normalized_email})

    if not user or not verify_password(payload.password, user.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return _issue_tokens(str(user["_id"]), refresh_tokens)


@router.post("/refresh", response_model=Token)
def refresh_token(payload: RefreshTokenRequest, db: Database = Depends(get_db)):
    users: Collection[dict[str, Any]] = db["users"]
    refresh_tokens: Collection[dict[str, Any]] = db["refresh_tokens"]

    try:
        token_payload = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = token_payload.get("sub")
        object_id = ObjectId(user_id)
    except (TypeError, InvalidId, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    stored_token = refresh_tokens.find_one(
        {
            "userId": user_id,
            "tokenHash": hash_token(payload.refresh_token),
        }
    )
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = users.find_one({"_id": object_id})
    if not user:
        refresh_tokens.delete_one({"_id": stored_token["_id"]})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    refresh_tokens.delete_one({"_id": stored_token["_id"]})
    return _issue_tokens(user_id, refresh_tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshTokenRequest, db: Database = Depends(get_db)) -> Response:
    refresh_tokens: Collection[dict[str, Any]] = db["refresh_tokens"]

    try:
        token_payload = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = token_payload.get("sub")
    except ValueError:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    refresh_tokens.delete_one(
        {
            "userId": user_id,
            "tokenHash": hash_token(payload.refresh_token),
        }
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
