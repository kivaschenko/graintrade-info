from dataclasses import dataclass


@dataclass(frozen=True)
class TermsDelivery:
    code: str
    description: str

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return self.code

    def __eq__(self, other: "TermsDelivery") -> bool:
        return self.code == other.code

    def __ne__(self, other: "TermsDelivery") -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> str:
        return hash(self.code)
