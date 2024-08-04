from pydantic import BaseModel, Field
from datetime import datetime


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
