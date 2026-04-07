from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from bson.errors import InvalidId
from app.database import get_db
from app.services.auth import decode_token
from app.models.user import user_entity

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db)
):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        object_id = ObjectId(user_id)
    except (TypeError, InvalidId, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = db["users"].find_one({"_id": object_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_entity(user)