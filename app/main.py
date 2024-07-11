from fastapi import FastAPI
from app.routers import item

app = FastAPI()

app.include_router(item.router)