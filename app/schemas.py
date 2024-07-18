from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


# Item schema


class ItemInDB(BaseModel):
    title: str
    description: str
    price: float
    currency: str
    amount: int
    measure: str
    terms_delivery: str
    country: str
    region: str
    latitude: float
    longitude: float


class ItemInResponse(ItemInDB):
    id: int
    created_at: datetime = Field(alias="created_at")

    @property
    def formatted_created_at(self) -> str:
        return self.created_at.isoformat()

    class Config:
        from_attributes = True


# User schema


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
    disabled: bool | None = None


class UserInCreate(User):
    password: str


class UserInDB(User):
    hashed_password: str


class UserInResponse(UserInDB):
    id: int
