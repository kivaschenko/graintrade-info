# Desc: Schemas for the item service

from pydantic import BaseModel, Field
from datetime import datetime


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

    class ConfigDict:
        from_attributes = True
