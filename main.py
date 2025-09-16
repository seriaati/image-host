from __future__ import annotations

from typing import TYPE_CHECKING, Any

import fastapi
import uvicorn

from app.routes import (
    count_files,
    delete_file,
    favicon,
    get_file,
    health_check,
    index,
    list_files,
    robots,
    total_size,
    upload_file,
)
from app.storage import get_storage_provider

if TYPE_CHECKING:
    from app.models import UploadFileData

# Initialize storage provider
storage = get_storage_provider()
app = fastapi.FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/")
async def root() -> fastapi.responses.RedirectResponse:
    return index()


@app.get("/favicon.ico")
async def get_favicon() -> fastapi.responses.Response:
    return favicon()


@app.get("/robots.txt")
async def get_robots() -> fastapi.responses.PlainTextResponse:
    return robots()


@app.get("/health")
async def health() -> fastapi.responses.JSONResponse:
    return health_check()


@app.post("/upload")
async def upload(data: UploadFileData) -> fastapi.responses.JSONResponse:
    return await upload_file(data, storage)


@app.get("/files")
async def files() -> fastapi.responses.JSONResponse:
    return await list_files(storage)


@app.get("/files/count")
async def files_count() -> fastapi.responses.JSONResponse:
    return await count_files(storage)


@app.get("/files/size")
async def files_size() -> fastapi.responses.JSONResponse:
    return await total_size(storage)


@app.delete("/{filename}")
async def delete(filename: str) -> fastapi.responses.JSONResponse:
    return await delete_file(filename, storage)


@app.get("/{filename}", response_model=None)
async def file(filename: str) -> Any:
    return await get_file(filename, storage)


if __name__ == "__main__":
    uvicorn.run(app, port=9078)
