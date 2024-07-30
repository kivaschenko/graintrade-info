from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float

    def __str__(self) -> str:
        return f"{self.latitude}, {self.longitude}"

    def __repr__(self) -> str:
        return f"{self.latitude}, {self.longitude}"

    def __eq__(self, other: "Coordinates") -> bool:
        return self.latitude == other.latitude and self.longitude == other.longitude

    def __ne__(self, other: "Coordinates") -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.latitude, self.longitude))
