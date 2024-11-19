# Desc: Schemas for the item service

from typing import Optional
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

    # add example json response
    # {
    # "amount": 360,
    # "category_id": 1,
    # "country": "Ukraine",
    # "created_at": "2024-11-13T13:08:31.158762",
    # "currency": "USD",
    # "description": "protein 45%",
    # "id": 3,
    # "latitude": 49.305825,
    # "longitude": 31.946946,
    # "measure": "metric ton",
    # "offer_type": "sell",
    # "price": 234.58,
    # "region": "Cherkasy Oblast",
    # "terms_delivery": "FCA",
    # "title": "Sell wheat 2 grade",
    # "uuid": "e73fec4b-0ec5-4ca1-b174-c03b47983cc6"
    # }


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


class TarifInResponse(TarifInDB):
    id: int
    created_at: datetime = Field(alias="created_at")

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
    tarif: TarifInResponse

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
