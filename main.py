from dotenv import load_dotenv
import fastapi
import pydantic
import os
import aiofiles
import aiohttp
import string
import base64
import random

load_dotenv()
API_KEY = os.environ["API_KEY"]

app = fastapi.FastAPI()


class UploadFileData(pydantic.BaseModel):
    key: str
    source: str  # URL or base64-encoded data


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

    # Generate random filename
    filename = "".join(random.choices(string.ascii_letters, k=16))

    # Save the file
    async with aiofiles.open(f"files/{filename}.png", "wb") as file:
        await file.write(content)

    return fastapi.responses.JSONResponse(content={"filename": f"{filename}.png"})


@app.get("/{filename}")
async def get_file(filename: str) -> fastapi.responses.FileResponse:
    return fastapi.responses.FileResponse(f"files/{filename}")
