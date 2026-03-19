import os

from app.storage_services.base_storage import BaseStorageService
from app.logger import logger


class LocalStorageService(BaseStorageService):
    def upload_file(self, data: str, file_path: str) -> None:
        """
        Save data to a local file.

        :param data: Data to be saved.
        :param file_path: Path to the local file.
        """
        logger.info("Saving data to local file: %s", file_path)
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(data)
            logger.info("Data saved successfully to: %s", file_path)
        except Exception as e:
            logger.error("Error saving data to local file %s: %s", file_path, e)
            raise e

    def download_file(self, file_path: str) -> str:
        """
        Read data from a local file.

        :param file_path: Path to the local file.
        :return: Data read from the file.
        """
        logger.info("Reading data from local file: %s", file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = file.read()
            logger.info("Data read successfully from: %s", file_path)
            return data
        except Exception as e:
            logger.error("Error reading data from local file %s: %s", file_path, e)
            raise e
        
    def list_files(self, directory_path: str) -> list:
        """
        List all files in a local directory.

        :param directory_path: Path to the local directory.
        :return: List of file names in the directory.
        """
        logger.info("Listing files in local directory: %s", directory_path)
        try:
            files = os.listdir(directory_path)
            logger.info("Files listed successfully in: %s", directory_path)
            return files
        except Exception as e:
            logger.error("Error listing files in local directory %s: %s", directory_path, e)
            raise e
    
    def delete_file(self, file_path: str) -> None:
        """
        Delete a local file.

        :param file_path: Path to the local file.
        """
        logger.info("Deleting local file: %s", file_path)
        try:
            os.remove(file_path)
            logger.info("File deleted successfully: %s", file_path)
        except Exception as e:
            logger.error("Error deleting local file %s: %s", file_path, e)
            raise e