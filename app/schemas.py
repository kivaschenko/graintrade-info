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
    def created_at(self) -> str:
        return self._created_at.isoformat()

    class Config:
        orm_mode = True
        getter_dict = lambda self: {"created_at": self.created_at, **self.dict()}
