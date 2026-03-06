from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseParser(ABC):
    @abstractmethod
    def parse(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_results(
        self, results: List[Dict[str, Any]], filepath: str, file_ext: str = "json"
    ) -> None:
        pass
