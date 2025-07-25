from dotenv import load_dotenv
import fastapi
from pydantic import BaseModel
import os
import aiofiles
import aiofiles.os
import aiohttp
import string
import base64
import random
import uvicorn

load_dotenv()
REPO_URL = "https://github.com/seriaati/image-host"
API_KEY = os.environ["API_KEY"]
FILESIZE_LIMIT = 20 * 1024 * 1024  # 20 MB

app = fastapi.FastAPI()


class UploadFileData(BaseModel):
    key: str
    source: str  # URL or base64-encoded data


@app.get("/")
async def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse(REPO_URL)


@app.get("/favicon.ico")
async def favicon() -> fastapi.responses.Response:
    return fastapi.responses.Response(status_code=204)


@app.get("/robots.txt")
async def robots() -> fastapi.responses.PlainTextResponse:
    return fastapi.responses.PlainTextResponse("User-agent: *\nDisallow: /")

@app.get("/health")
async def health_check() -> fastapi.responses.JSONResponse:
    return fastapi.responses.JSONResponse(content={"status": "ok"})

@app.post("/upload")
async def upload_file(data: UploadFileData) -> fastapi.responses.JSONResponse:
    if data.key != API_KEY:
        raise fastapi.HTTPException(status_code=403, detail="Invalid API key")

    # Determine if the source is a URL or base64-encoded data
    if data.source.startswith("http"):
        async with aiohttp.ClientSession() as session:
            async with session.get(data.source) as response:
                response.raise_for_status()
                content = await response.read()
    else:
        content = base64.b64decode(data.source)

    # Check file size
    if len(content) > FILESIZE_LIMIT:
        raise fastapi.HTTPException(status_code=413, detail="File size exceeds limit")

    # Generate random filename
    filename = "".join(random.choices(string.ascii_letters, k=16))

    # Save the file
    async with aiofiles.open(f"files/{filename}.png", "wb") as file:
        await file.write(content)

    return fastapi.responses.JSONResponse(content={"filename": f"{filename}.png"})


@app.get("/files")
async def list_files() -> fastapi.responses.JSONResponse:
    try:
        files = await aiofiles.os.listdir("files")
    except FileNotFoundError:
        raise fastapi.HTTPException(status_code=404, detail="Directory not found")

    files.remove(".gitkeep")

    file_sizes: dict[str, int] = {}
    for file in files:
        file_path = f"files/{file}"
        size = await aiofiles.os.path.getsize(file_path)
        file_sizes[file] = size

    return fastapi.responses.JSONResponse(content=file_sizes)


@app.get("/files/count")
async def count_files() -> fastapi.responses.JSONResponse:
    try:
        files = await aiofiles.os.listdir("files")
    except FileNotFoundError:
        raise fastapi.HTTPException(status_code=404, detail="Directory not found")

    files.remove(".gitkeep")
    return fastapi.responses.JSONResponse(content={"count": len(files)})


@app.get("/files/size")
async def total_size() -> fastapi.responses.JSONResponse:
    try:
        files = await aiofiles.os.listdir("files")
    except FileNotFoundError:
        raise fastapi.HTTPException(status_code=404, detail="Directory not found")

    files.remove(".gitkeep")
    total_size = 0
    for file in files:
        file_path = f"files/{file}"
        size = await aiofiles.os.path.getsize(file_path)
        total_size += size

    return fastapi.responses.JSONResponse(content={"total_size": total_size})


@app.delete("/{filename}")
async def delete_file(filename: str) -> fastapi.responses.JSONResponse:
    try:
        await aiofiles.os.remove(f"files/{filename}")
    except FileNotFoundError:
        raise fastapi.HTTPException(status_code=404, detail="File not found")

    return fastapi.responses.JSONResponse(content={"message": "File deleted"})


@app.get("/{filename}")
async def get_file(filename: str) -> fastapi.responses.FileResponse:
    try:
        return fastapi.responses.FileResponse(f"files/{filename}")
    except FileNotFoundError:
        raise fastapi.HTTPException(status_code=404, detail="File not found")


if __name__ == "__main__":
    uvicorn.run(app, port=9078)
