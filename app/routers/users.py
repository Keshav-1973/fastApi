from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.database import Database
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.user import ProfileResponse, ProfileUpdateRequest, UserResponse
from app.models.user import user_entity

router = APIRouter(prefix="/users", tags=["Users"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _profile_entity(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name") or user.get("username", ""),
        "email": user["email"],
        "phoneNumber": user.get("phoneNumber"),
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    users: Collection[dict] = db["users"]

    try:
        object_id = ObjectId(current_user["id"])
    except (InvalidId, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    user = users.find_one({"_id": object_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return _profile_entity(user)


@router.patch("/profile", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    users: Collection[dict] = db["users"]

    try:
        object_id = ObjectId(current_user["id"])
    except (InvalidId, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required",
        )

    if "name" in updates:
        name = (updates["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name cannot be empty")
        updates["name"] = name
        updates["username"] = name

    if "phoneNumber" in updates and updates["phoneNumber"] is not None:
        updates["phoneNumber"] = updates["phoneNumber"].strip()

    if "email" in updates and updates["email"] is not None:
        normalized_email = _normalize_email(str(updates["email"]))
        existing_user = users.find_one(
            {
                "email_normalized": normalized_email,
                "_id": {"$ne": object_id},
            }
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        updates["email"] = normalized_email
        updates["email_normalized"] = normalized_email

    users.update_one({"_id": object_id}, {"$set": updates})

    user = users.find_one({"_id": object_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return _profile_entity(user)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    user = db["users"].find_one({"_id": object_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user_entity(user)