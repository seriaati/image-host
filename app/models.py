from __future__ import annotations

from pydantic import BaseModel


class UploadFileData(BaseModel):
    key: str
    source: str  # URL or base64-encoded data
