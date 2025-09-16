from __future__ import annotations

from typing import Annotated, Any

import fastapi
import uvicorn

from app import routes
from app.models import UploadFileData
from app.security import verify_api_key
from app.storage import get_storage_provider

# Initialize storage provider
storage = get_storage_provider()
app = fastapi.FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/")
async def root() -> fastapi.responses.RedirectResponse:
    return routes.index()


@app.get("/favicon.ico")
async def get_favicon() -> fastapi.responses.Response:
    return routes.favicon()


@app.get("/robots.txt")
async def get_robots() -> fastapi.responses.PlainTextResponse:
    return routes.robots()


@app.get("/health")
async def health() -> fastapi.responses.JSONResponse:
    return routes.health_check()


@app.post("/upload")
async def upload(
    data: UploadFileData, _: Annotated[str, fastapi.Depends(verify_api_key)]
) -> fastapi.responses.JSONResponse:
    return await routes.upload_file(data, storage)


@app.get("/files")
async def files() -> fastapi.responses.JSONResponse:
    return await routes.list_files(storage)


@app.get("/files/count")
async def files_count() -> fastapi.responses.JSONResponse:
    return await routes.count_files(storage)


@app.get("/files/size")
async def files_size() -> fastapi.responses.JSONResponse:
    return await routes.total_size(storage)


@app.delete("/{filename}")
async def delete(
    filename: str, _: Annotated[str, fastapi.Depends(verify_api_key)]
) -> fastapi.responses.JSONResponse:
    return await routes.delete_file(filename, storage)


@app.get("/{filename}", response_model=None)
async def file(filename: str) -> Any:
    return await routes.get_file(filename, storage)


if __name__ == "__main__":
    uvicorn.run(app, port=9078)
