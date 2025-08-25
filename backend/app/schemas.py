# Desc: Schemas for the item service

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


# -------------------------------
# Category schemas


class CategoryInDB(BaseModel):
    name: str
    description: str | None
    ua_name: str | None
    ua_description: str | None


class CategoryInResponse(CategoryInDB):
    id: int
    parent_category: Optional[str]
    parent_category_ua: Optional[str]


# -------------------------------
# Item schemas


class ItemInDB(BaseModel):
    category_id: int
    offer_type: str
    title: str
    description: str | None
    price: float
    currency: str
    amount: int
    measure: str
    terms_delivery: str
    country: str
    region: str | None
    latitude: float
    longitude: float


class ItemInResponse(BaseModel):
    id: int
    uuid: UUID
    category_id: int
    offer_type: str
    title: str
    description: str | None
    price: float
    currency: str
    amount: int
    measure: str
    terms_delivery: str
    country: str
    region: str | None
    latitude: float
    longitude: float
    created_at: datetime = Field(alias="created_at")
    owner_id: Optional[str] = None
    category: Optional[CategoryInResponse] = None
    user_id: Optional[int] = None
    category_name: Optional[str] = None
    category_ua_name: Optional[str] = None

    @property
    def formatted_created_at(self) -> str:
        return self.created_at.isoformat()

    class ConfigDict:
        from_attributes = True


class ItemsByUserResponse(BaseModel):
    items: List[ItemInResponse]
    total_items: int


# -------------------------------
# Category with Items schema


class CategoryWithItems(BaseModel):
    id: int
    name: str
    description: Optional[str]
    ua_name: Optional[str]
    ua_description: Optional[str]
    items: List[ItemInResponse]


# -------------------------------
# User schemas


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    scopes: list[str] = []


class User(BaseModel):
    username: str
    email: EmailStr = ""
    full_name: str | None
    phone: str | None = None
    disabled: bool | None = None


class UserInCreate(User):
    password: str


class UserInUpdate(User):
    id: int
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class UserInDB(User):
    hashed_password: str


class UserInResponse(UserInDB):
    id: int


# -------------------------------
# Subscription schemas


class TarifInDB(BaseModel):
    name: str
    description: str
    price: float
    currency: str
    scope: str  # e.g. "basic", "premium", "enterprise"
    terms: str  # e.g. "monthly", "annual", "yearly"
    ua_name: Optional[str] = None
    ua_description: Optional[str] = None
    ua_terms: Optional[str] = None

    class ConfigDict:
        from_attributes = True


class TarifInResponse(TarifInDB):
    id: int
    items_limit: int
    map_views_limit: int
    geo_search_limit: int
    navigation_limit: int
    notify_new_messages: bool = True
    notify_new_items: bool = True
    created_at: datetime | None

    @property
    def formatted_created_at(self) -> str:
        return self.created_at.isoformat()  # type: ignore

    class ConfigDict:
        from_attributes = True


class SubscriptionInDB(BaseModel):
    user_id: int
    tarif_id: int
    order_id: Optional[str] = None
    provider: str = "fondy"  # Default to Fondy payment provider
    provider_payment_token: Optional[str] = None  # Token for Fondy payment
    start_date: date | None
    end_date: date | None
    status: SubscriptionStatus = SubscriptionStatus.INACTIVE
    provider: str = "fondy"  # Payment provider name
    provider_payment_token: Optional[str] = None  # Token for payment provider


class SubscriptionInResponse(BaseModel):
    id: int
    user_id: int
    tarif_id: int
    order_id: str
    provider: str
    provider_payment_token: Optional[str] = None  # Token for Fondy payment
    start_date: date
    end_date: date
    status: SubscriptionStatus
    created_at: datetime = Field(alias="created_at")
    tarif: TarifInResponse | None = None

    @property
    def formatted_created_at(self) -> str:
        return self.created_at.isoformat()

    class ConfigDict:
        from_attributes = True


# -------------------------------
# Payment schemas


# class PaymentInDB(BaseModel):
#     """Payment data model based on Fondy payment response"""

#     id: Optional[int] = None
#     payment_id: int
#     order_id: str
#     order_status: str
#     currency: str
#     amount: int  # Amount in cents
#     card_type: str
#     card_bin: int
#     masked_card: str
#     payment_system: str
#     sender_email: str
#     sender_cell_phone: Optional[str] = None
#     approval_code: str
#     response_status: str
#     tran_type: str
#     eci: Optional[str] = None
#     settlement_amount: Optional[str] = None
#     actual_amount: str
#     order_time: datetime
#     additional_info: Dict[str, Any] = Field(
#         default_factory=dict
#     )  # JSON field for extra data
#     created_at: datetime = Field(default_factory=datetime.now)

#     class Config:
#         from_attributes = True


class GeoSearchRequest(BaseModel):
    query: str


class DirectionsRequest(BaseModel):
    origin: List[float]  # [longitude, latitude]
    destination: List[float]  # [longitude, latitude]


# -------------------------------
# Notification schemas


class PreferencesUpdateSchema(BaseModel):
    notify_new_messages: Optional[bool] = True
    notify_new_items: Optional[bool] = True
    interested_categories: Optional[List[str]] = []
    country: Optional[str]  # Default to Ukraine if not set
