from contextlib import asynccontextmanager
from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.infrastructure.persistence.database import Database
from app.presentation.routes import user_routes
from app.presentation.routes import item_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.init()
    await Database.create_tables()
    try:
        yield
    finally:
        await Database._pool.close()


app = FastAPI(lifespan=lifespan)

app.include_router(item_routes.router)
app.include_router(user_routes.router)

app.mount("/static", StaticFiles(directory="app/presentation/static"), name="static")
templates = Jinja2Templates(directory="app/presentation/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/favicon.ico")
async def favicon():
    file_name = "favicon.ico"
    file_path = "./static/" + file_name
    return FileResponse(
        path=file_path, headers={"mimetype": "image/vnd.microsoft.icon"}
    )


@app.post("/hello", response_class=HTMLResponse)
async def hello(request: Request, name: str = Form(...)):
    if name:
        return templates.TemplateResponse(
            "hello.html", {"request": request, "name": name}
        )
    else:
        return RedirectResponse(
            request.url_for("index"), status_code=status.HTTP_302_FOUND
        )
