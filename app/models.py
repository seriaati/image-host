from __future__ import annotations

from pydantic import BaseModel


class UploadFileData(BaseModel):
    source: str  # URL or base64-encoded data
