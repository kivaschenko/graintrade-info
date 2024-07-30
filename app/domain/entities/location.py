from pydantic import BaseModel
from typing import Optional
from ..value_objects.coordinates import Coordinates


class Location(BaseModel):
    id: int
    name: str
    country: Optional[str]
    region: Optional[str]
    address: Optional[str]
    description: Optional[str]
    coordinates: Coordinates

    class Config:
        from_attributes = True
        orm_mode = True
