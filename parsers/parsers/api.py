import os
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, FileResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from parsers.csv_parser import CSVParser, ALLOWED_EXTENSIONS

import tempfile
from pathlib import Path

app = FastAPI(title="File Parser API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store uploaded/downloaded files
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)
API_TOKEN = os.getenv("API_TOKEN", "your_default_token_here")


# Upload items endpoint (csv/xls/xlsx)
@app.post("/items/upload/")
async def upload_items(
    file: UploadFile = File(...), token: Optional[str] = Query(None)
):
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in {"csv", "xls", "xlsx"}:
        raise HTTPException(
            status_code=400, detail="Only .csv, .xls and .xlsx files are supported."
        )
    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        parser = CSVParser(tmp_path)
        items = parser.parse()
    finally:
        os.remove(tmp_path)
    return {"items": items, "count": len(items)}


# Download items endpoint (csv/xls)
@app.get("/items/download/")
async def download_items(format: str = Query("csv", enum=["csv", "xls"])):
    # For demo, use the sample file as data source
    sample_csv = RESULTS_DIR / "sample_items.csv"
    sample_xls = RESULTS_DIR / "sample_items.xls"
    if format == "csv":
        if not sample_csv.exists():
            raise HTTPException(status_code=404, detail="Sample CSV not found.")
        return FileResponse(
            str(sample_csv), media_type="text/csv", filename="items.csv"
        )
    elif format == "xls":
        if not sample_xls.exists():
            raise HTTPException(status_code=404, detail="Sample XLS not found.")
        return FileResponse(
            str(sample_xls), media_type="application/vnd.ms-excel", filename="items.xls"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format.")


# Download template xls for items
@app.get("/items/template/")
async def download_items_template():
    template_xls = RESULTS_DIR / "items_template.xls"
    if not template_xls.exists():
        raise HTTPException(status_code=404, detail="Template XLS not found.")
    return FileResponse(
        str(template_xls),
        media_type="application/vnd.ms-excel",
        filename="items_template.xls",
    )


@app.post("/parse-file/")
async def parse_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    save_to_disk: Optional[bool] = False,
):
    if not file.filename:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="No file uploaded")

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: {file_ext}",
        )

    try:
        contents = await file.read()
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(contents)

        parser = CSVParser(temp_file_path)
        results = parser.parse()

        if save_to_disk:
            output_path = f"/tmp/parsed_{file.filename}"
            parser.save_results(results, output_path)
            background_tasks.add_task(os.remove, output_path)

        background_tasks.add_task(os.remove, temp_file_path)
        return JSONResponse(content={"results": results})

    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}",
        )


@app.get("/health/")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8077)
