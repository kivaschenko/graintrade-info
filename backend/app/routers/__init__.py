import os
import logging

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "Avy8XuxvccZkogNVOi7DSeKIb+VxTc1Wwspits6rs0I7cUFTYngnwlC1xJioUVyX6bP7xVf/VQkp0Cal8mJhJA==",
)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRES_IN", 60)
MAP_VIEW_LIMIT = 100

logging.info("Initializing user router...")
logging.info(f"JWT_SECRET: {JWT_SECRET}")
logging.info(f"ALGORITHM: {ALGORITHM}")
logging.info(f"ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")
