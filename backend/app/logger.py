import logging
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("app_logger")
log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_name, logging.INFO)
logger.setLevel(log_level)
logger.propagate = False

# Avoid duplicate handlers when modules are reloaded in dev mode.
if logger.handlers:
    logger.handlers.clear()

# Optionally, you can also set up logging to handle both file and console output
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
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
