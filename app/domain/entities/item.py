from __future__ import annotations
import json
import random
from datetime import datetime, timezone, timedelta, date


class Item:
    def __init__(
        self,
        title: str,
        description: str,
        price: float,
        currency: str,
        amount: int,
        measure: str,
        terms_delivery: str,
        country: str,
        region: str,
        latitude: float,
        longitude: float,
    ):
        self.title = title
        self.description = description
        self.price = price
        self.currency = currency
        self.amount = amount
        self.measure = measure
        self.terms_delivery = terms_delivery
        self.country = country
        self.region = region
        self.latitude = latitude
        self.longitude = longitude

    def __eq__(self, other: Item) -> bool:
        return self.__dict__ == other.__dict__

    def __repr__(self) -> str:
        return f"Item({self.__dict__})"

    def __str__(self) -> str:
        return f"{self.title} - {self.price} {self.currency} - {self.amount} {self.measure} - {self.terms_delivery} - {self.country} - {self.region}"

    def __hash__(self) -> int:
        return hash(self.__dict__)

    def to_dict(self) -> dict:
        return self.__dict__

    @classmethod
    def from_dict(cls, adict: dict) -> Item:
        return cls(**adict)

    @classmethod
    def from_json(cls, json: str) -> Item:
        return cls.from_dict(json.loads(json))

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @property
    def is_available(self) -> bool:
        return self.amount > 0

    def decrease_amount(self, amount: int) -> None:
        self.amount -= amount

    @property
    def is_near(self) -> bool:
        return self.distance <= 100 * 1000

    @property
    def id(self) -> int:
        return random.randint(1, 1000)

    @property
    def created_at(self) -> datetime:
        kyiv_tz = timezone(timedelta(hours=3))
        return date.today(timezone=kyiv_tz) - timedelta(days=random.randint(0, 365))
