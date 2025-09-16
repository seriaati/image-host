from __future__ import annotations

import base64
import random
import string
from typing import TYPE_CHECKING, Any

import aiohttp
import fastapi

from .config import settings
from .storage import LocalStorageProvider, StorageProvider

if TYPE_CHECKING:
    from .models import UploadFileData


def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse(settings.repo_url)


def favicon() -> fastapi.responses.Response:
    return fastapi.responses.Response(status_code=204)


def robots() -> fastapi.responses.PlainTextResponse:
    return fastapi.responses.PlainTextResponse("User-agent: *\nDisallow: /")


def health_check() -> fastapi.responses.JSONResponse:
    return fastapi.responses.JSONResponse(content={"status": "ok"})


async def upload_file(data: UploadFileData, storage: StorageProvider) -> fastapi.responses.JSONResponse:
    if not settings.uploads_enabled:
        raise fastapi.HTTPException(status_code=503, detail="Uploads are temporarily disabled")

    if data.key != settings.api_key:
        raise fastapi.HTTPException(status_code=403, detail="Invalid API key")

    # Determine if the source is a URL or base64-encoded data
    if data.source.startswith("http"):
        async with aiohttp.ClientSession() as session, session.get(data.source) as response:
            response.raise_for_status()
            content = await response.read()
    else:
        content = base64.b64decode(data.source)

    # Check file size
    if len(content) > settings.filesize_limit:
        raise fastapi.HTTPException(status_code=413, detail="File size exceeds limit")

    # Generate random filename
    filename = "".join(random.choices(string.ascii_letters, k=16)) + ".png"

    # Save the file using storage provider
    await storage.save_file(filename, content)

    return fastapi.responses.JSONResponse(content={"filename": filename})


async def list_files(storage: StorageProvider) -> fastapi.responses.JSONResponse:
    file_sizes = await storage.list_files()
    return fastapi.responses.JSONResponse(content=file_sizes)


async def count_files(storage: StorageProvider) -> fastapi.responses.JSONResponse:
    count = await storage.get_file_count()
    return fastapi.responses.JSONResponse(content={"count": count})


async def total_size(storage: StorageProvider) -> fastapi.responses.JSONResponse:
    total = await storage.get_total_size()
    return fastapi.responses.JSONResponse(content={"total_size": total})


async def delete_file(filename: str, storage: StorageProvider) -> fastapi.responses.JSONResponse:
    await storage.delete_file(filename)
    return fastapi.responses.JSONResponse(content={"message": "File deleted"})


async def get_file(filename: str, storage: StorageProvider) -> Any:
    if isinstance(storage, LocalStorageProvider):
        # For local storage, serve the file directly
        try:
            file_path = await storage.get_file_url(filename)
            return fastapi.responses.FileResponse(file_path)
        except FileNotFoundError as e:
            raise fastapi.HTTPException(status_code=404, detail="File not found") from e
    else:
        # For S3 storage, redirect to the public URL
        file_url = await storage.get_file_url(filename)
        return fastapi.responses.RedirectResponse(url=file_url, status_code=302)
