from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class DropDownItem(BaseModel):
    """Represents a dropdown option with id, label, and value"""

    id: str
    label: str
    value: str


class AttachmentFile(BaseModel):
    """Represents an image file attachment"""

    uri: str
    fileName: str
    mimeType: Optional[str] = None
    size: Optional[int] = None


class States(BaseModel):
    """Represents a state/province"""

    id: int
    name: str
    country_id: int
    country_code: str  # ISO country code (e.g., "IN", "US")
    iso2: str  # State ISO code (e.g., "MH", "CA")
    type: str = "state"
    latitude: str
    longitude: str


class Cities(BaseModel):
    """Represents a city"""

    id: int
    name: str


class CarDetails(BaseModel):
    """Car brand, model, and variant details"""

    brand: str
    model: str
    variant: str


class CarDetailsFormData(BaseModel):
    """First form: Car specifications"""

    car: CarDetails
    vehicleType: DropDownItem
    fuelType: DropDownItem
    transmission: DropDownItem
    year: str
    kilometersDriven: str
    numberOfOwners: DropDownItem
    adTitle: str
    description: str


class CarDetailsDocumentData(BaseModel):
    """Stored car details returned by read endpoints"""

    car: CarDetails
    vehicleType: Optional[DropDownItem] = None
    fuelType: DropDownItem
    transmission: DropDownItem
    year: str
    kilometersDriven: str
    numberOfOwners: DropDownItem
    adTitle: str
    description: str


class AddPhotosFormData(BaseModel):
    """Second form: Images for the listing"""

    images: List[AttachmentFile]


class Location(BaseModel):
    """Location with state and city"""

    state: Optional[States] = None
    city: Optional[Cities] = None


class AdditionalDetailsFormData(BaseModel):
    """Third form: Price and location"""

    price: str
    location: Location


class CarListingRequest(BaseModel):
    """Complete car listing with all details and photos"""

    carDetails: CarDetailsFormData
    photos: AddPhotosFormData
    additionalDetails: AdditionalDetailsFormData


class CarListingResponse(BaseModel):
    """Response after creating a car listing"""

    id: str
    adTitle: str
    status: str
    createdAt: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class CarListingDocument(BaseModel):
    """Stored car listing returned by read endpoints"""

    id: str
    carDetails: CarDetailsDocumentData
    photos: AddPhotosFormData
    additionalDetails: AdditionalDetailsFormData
    ownerId: str
    ownerEmail: str
    createdAt: datetime
    status: str


class OwnerDetails(BaseModel):
    """Owner profile fields returned with listing details"""

    ownerId: str
    ownerEmail: str
    name: str
    phoneNumber: Optional[str] = None


class CarListingWithOwnerResponse(BaseModel):
    """Listing details enriched with owner contact information"""

    id: str
    carDetails: CarDetailsDocumentData
    photos: AddPhotosFormData
    additionalDetails: AdditionalDetailsFormData
    createdAt: datetime
    status: str
    ownerDetails: OwnerDetails


class CarListingListResponse(BaseModel):
    """Response for listing collection endpoints"""

    count: int
    items: List[CarListingDocument]
