from __future__ import annotations

from typing import Annotated

import fastapi
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

# Bearer token security scheme
security = HTTPBearer(auto_error=False)


def verify_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials | None, fastapi.Depends(security)],
) -> str:
    """Verify the API key from the Authorization Bearer header."""
    if not credentials or credentials.credentials != settings.api_key:
        raise fastapi.HTTPException(
            status_code=403,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
