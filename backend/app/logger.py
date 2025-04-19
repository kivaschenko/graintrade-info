import logging
from logging.handlers import RotatingFileHandler

# Configure logging to write to a file
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels of messages

# Optionally, you can also set up logging to handle both file and console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

info_handler = RotatingFileHandler("app_info.log", maxBytes=1048576, backupCount=5)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

warning_handler = RotatingFileHandler(
    "app_warning.log", maxBytes=1048576, backupCount=5
)
warning_handler.setLevel(logging.WARNING)
warning_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

error_handler = RotatingFileHandler("app_error.log", maxBytes=1048576, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(info_handler)
logger.addHandler(warning_handler)
logger.addHandler(error_handler)
