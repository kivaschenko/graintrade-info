from typing import Protocol, runtime_checkable
from pandas import DataFrame

@runtime_checkable
class BaseTransformer(Protocol):
    def transform(self, data: DataFrame) -> DataFrame:
        ...