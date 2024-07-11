from pydantic import BaseModel
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
    _created_at: datetime  # Add this line
    created_at: str  # Add this line

    @property
    def created_at(self) -> str:
        return self._created_at.isoformat()

    @created_at.setter
    def created_at(self, value: str) -> None:
        self._created_at = datetime.fromisoformat(value)
