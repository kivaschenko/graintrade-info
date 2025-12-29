from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseStorageService(ABC):
    @abstractmethod
    def upload_file(self, file_path: str, destination_path: str) -> None:
        pass

    @abstractmethod
    def download_file(self, source_path: str, destination_path: str) -> None:
        pass

    @abstractmethod
    def list_files(self, directory_path: str) -> List[str]:
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        pass