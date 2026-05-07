from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Any
from datetime import datetime, timezone
from bson import ObjectId

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.car_listing import (
    CarListingDocument,
    CarListingListResponse,
    CarListingRequest,
    CarListingResponse,
    CarListingWithOwnerResponse,
)

router = APIRouter(prefix="/car-listings", tags=["Car Listings"])


def _build_listing_document(
    car_details: dict[str, Any],
    photos: dict[str, Any],
    additional_details: dict[str, Any],
    current_user: dict[str, Any],
) -> dict[str, Any]:
    return {
        "carDetails": car_details,
        "photos": photos,
        "additionalDetails": additional_details,
        "ownerId": current_user["id"],
        "ownerEmail": current_user["email"],
        "createdAt": datetime.now(timezone.utc),
        "status": "active",
    }


def _create_listing_response(
    new_listing: dict[str, Any],
    db: Database,
) -> dict[str, str]:
    listings: Collection[dict[str, Any]] = db["car_listings"]
    result = listings.insert_one(new_listing)

    created_listing = listings.find_one({"_id": result.inserted_id})
    if not created_listing:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Listing creation failed",
        )

    return {
        "id": str(created_listing["_id"]),
        "adTitle": created_listing["carDetails"]["adTitle"],
        "status": created_listing["status"],
        "createdAt": created_listing["createdAt"].isoformat(),
        "message": "Listing created successfully",
    }


@router.post(
    "/create",
    response_model=CarListingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_complete_car_listing(
    payload: CarListingRequest,
    db: Database = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Create a complete car listing using grouped carDetails, photos, and additionalDetails
    """
    car_details = payload.carDetails.model_dump()
    photos = payload.photos.model_dump()
    additional_details = payload.additionalDetails.model_dump()

    new_listing = _build_listing_document(
        car_details=car_details,
        photos=photos,
        additional_details=additional_details,
        current_user=current_user,
    )

    return _create_listing_response(new_listing=new_listing, db=db)


@router.get("/me/list", response_model=CarListingListResponse)
def get_my_listings(
    db: Database = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve all car listings created by current authenticated user
    """
    listings: Collection[dict[str, Any]] = db["car_listings"]
    docs = list(listings.find({"ownerId": current_user["id"]}).sort("createdAt", -1))

    response: list[dict[str, Any]] = []
    for listing in docs:
        listing["id"] = str(listing["_id"])
        del listing["_id"]
        response.append(listing)

    return {"count": len(response), "items": response}


@router.get("/others/list", response_model=CarListingListResponse)
def get_other_users_listings(
    db: Database = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve all active car listings created by other users
    """
    listings: Collection[dict[str, Any]] = db["car_listings"]
    docs = list(
        listings.find(
            {
                "ownerId": {"$ne": current_user["id"]},
                "status": "active",
            }
        ).sort("createdAt", -1)
    )

    response: list[dict[str, Any]] = []
    for listing in docs:
        listing["id"] = str(listing["_id"])
        del listing["_id"]
        response.append(listing)

    return {"count": len(response), "items": response}


@router.get("/others/{listing_id}", response_model=CarListingWithOwnerResponse)
def get_other_user_listing_by_id(
    listing_id: str,
    db: Database = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve one active listing by ID created by another user, including owner details.
    """
    listings: Collection[dict[str, Any]] = db["car_listings"]
    users: Collection[dict[str, Any]] = db["users"]

    try:
        listing_obj_id = ObjectId(listing_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid listing ID",
        )

    listing = listings.find_one(
        {
            "_id": listing_obj_id,
            "ownerId": {"$ne": current_user["id"]},
            "status": "active",
        }
    )
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    owner = None
    try:
        owner = users.find_one({"_id": ObjectId(listing["ownerId"])})
    except Exception:
        owner = None

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found",
        )

    listing["id"] = str(listing["_id"])
    del listing["_id"]
    listing["ownerDetails"] = {
        "ownerId": listing["ownerId"],
        "ownerEmail": listing.get("ownerEmail") or owner.get("email", ""),
        "name": owner.get("name") or owner.get("username", ""),
        "phoneNumber": owner.get("phoneNumber"),
    }

    return listing


@router.get("/{listing_id}", response_model=CarListingDocument)
def get_listing(
    listing_id: str,
    db: Database = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve a complete car listing by ID
    """
    listings: Collection[dict[str, Any]] = db["car_listings"]

    try:
        listing_obj_id = ObjectId(listing_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid listing ID",
        )

    listing = listings.find_one({"_id": listing_obj_id, "ownerId": current_user["id"]})
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found for this user",
        )

    listing["id"] = str(listing["_id"])
    del listing["_id"]

    return listing
