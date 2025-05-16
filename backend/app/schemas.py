# Desc: Schemas for the item service

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# -------------------------------
# Category schemas


class CategoryInDB(BaseModel):
    name: str
    description: str | None
    ua_name: str | None
    ua_description: str | None


class CategoryInResponse(CategoryInDB):
    id: int


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
    uuid: str
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

    @property
    def formatted_created_at(self) -> str:
        return self.created_at.isoformat()

    class ConfigDict:
        from_attributes = True


# -------------------------------
# Category with Items schema


class CategoryWithItems(BaseModel):
    id: int
    name: str
    description: str | None
    ua_name: str | None
    ua_description: str | None
    items: List[ItemInResponse] = []


# -------------------------------
# User schemas


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []


class User(BaseModel):
    username: str
    email: EmailStr = None
    full_name: str | None = None
    phone: str | None = None
    disabled: bool | None = None


class UserInCreate(User):
    password: str


class UserInDB(User):
    hashed_password: str


class UserInResponse(UserInDB):
    id: int


# -------------------------------
# Notification schemas
class Notification(BaseModel):
    recipient: str
    message: str
    method: str  # 'email', 'sms', 'telegram'


class Recipient(BaseModel):
    email: Optional[str]
    phone: Optional[str]
    telegram_id: Optional[str]
    device_id: Optional[str]
    viber_id: Optional[str]


# -------------------------------
# Subscription schemas


class TarifInDB(BaseModel):
    name: str
    description: str
    price: float
    currency: str
    scope: str  # e.g. "basic", "premium", "enterprise"
    terms: str  # e.g. "monthly", "annual", "yearly"
    items_limit: int = 5
    map_views_limit: int = 10

    class ConfigDict:
        from_attributes = True


class TarifInResponse(TarifInDB):
    id: int

    @property
    def formatted_created_at(self) -> str:
        return self.created_at.isoformat()

    class ConfigDict:
        from_attributes = True


class SubscriptionInDB(BaseModel):
    user_id: int
    tarif_id: int
    start_date: datetime
    end_date: datetime
    status: str


class SubscriptionInResponse(SubscriptionInDB):
    id: int
    created_at: datetime = Field(alias="created_at")
    tarif: TarifInResponse | None = None

    @property
    def formatted_created_at(self) -> str:
        return self.created_at.isoformat()

    class ConfigDict:
        from_attributes = True


class PaymentInDB(BaseModel):
    user_id: int
    tarif_id: int
    amount: float
    currency: str


class PaymentInResponse(PaymentInDB):
    id: int
    created_at: datetime = Field(alias="created_at")

    @property
    def formatted_created_at(self) -> str:
        return self.created_at.isoformat()


class PaymentResponse(BaseModel):
    checkout_url: str
    order_id: str
