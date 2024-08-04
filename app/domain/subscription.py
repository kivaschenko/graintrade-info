from pydantic import BaseModel, Field
from datetime import datetime


class SubscriptionInDB(BaseModel):
    user_id: int
    tarif_id: int
    start_date: datetime
    end_date: datetime
    status: str


class SubscriptionInResponse(SubscriptionInDB):
    id: int
    created_at: datetime = Field(alias="created_at")

    @property
    def formatted_created_at(self) -> str:
        return self.created_at.isoformat()

    class ConfigDict:
        from_attributes = True
