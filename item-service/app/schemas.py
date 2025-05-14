# Desc: Schemas for the item service
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime

# ------------------
# Category schemas


class CategoryInDB(BaseModel):
    name: str
    description: str | None
    ua_name: str | None
    ua_description: str | None


class CategoryInResponse(CategoryInDB):
    id: int


# ------------------------
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
