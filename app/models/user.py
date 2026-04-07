def user_entity(user: dict) -> dict:
    # Convert MongoDB document into API response shape.
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "username": user["username"],
        "is_active": user.get("is_active", True),
    }