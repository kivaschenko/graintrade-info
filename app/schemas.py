# Desc: Schemas for the item service

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class CategoryInDB(BaseModel):
    name: str
    description: str | None
    ua_name: str | None
    ua_description: str | None


class CategoryInResponse(CategoryInDB):
    id: int


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


class ItemInResponse(ItemInDB):
    id: int
    uuid: str
    created_at: datetime = Field(alias="created_at")

    @property
    def formatted_created_at(self) -> str:
        return self.created_at.isoformat()

    class ConfigDict:
        from_attributes = True


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
