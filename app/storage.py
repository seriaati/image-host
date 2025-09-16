from __future__ import annotations

from abc import ABC, abstractmethod
from typing import cast

import aioboto3
import aiofiles
import aiofiles.os
import fastapi
from botocore.exceptions import ClientError

from .config import settings


class StorageProvider(ABC):
    """Abstract base class for storage providers"""

    @abstractmethod
    async def save_file(self, filename: str, content: bytes) -> str:
        """Save file and return the accessible URL/path"""

    @abstractmethod
    async def delete_file(self, filename: str) -> None:
        """Delete a file"""

    @abstractmethod
    async def get_file_url(self, filename: str) -> str:
        """Get the URL to access a file"""

    @abstractmethod
    async def list_files(self) -> dict[str, int]:
        """List all files with their sizes"""

    @abstractmethod
    async def get_file_count(self) -> int:
        """Get total number of files"""

    @abstractmethod
    async def get_total_size(self) -> int:
        """Get total size of all files"""


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider"""

    def __init__(self, base_path: str = "files") -> None:
        self.base_path = base_path

    async def save_file(self, filename: str, content: bytes) -> str:
        file_path = f"{self.base_path}/{filename}"
        async with aiofiles.open(file_path, "wb") as file:
            await file.write(content)
        return filename

    async def delete_file(self, filename: str) -> None:
        try:
            await aiofiles.os.remove(f"{self.base_path}/{filename}")
        except FileNotFoundError as e:
            raise fastapi.HTTPException(status_code=404, detail="File not found") from e

    async def get_file_url(self, filename: str) -> str:
        return f"{self.base_path}/{filename}"

    async def list_files(self) -> dict[str, int]:
        try:
            files = await aiofiles.os.listdir(self.base_path)
        except FileNotFoundError as e:
            raise fastapi.HTTPException(status_code=404, detail="Directory not found") from e

        if ".gitkeep" in files:
            files.remove(".gitkeep")

        file_sizes: dict[str, int] = {}
        for file in files:
            file_path = f"{self.base_path}/{file}"
            size = await aiofiles.os.path.getsize(file_path)
            file_sizes[file] = size

        return file_sizes

    async def get_file_count(self) -> int:
        try:
            files = await aiofiles.os.listdir(self.base_path)
        except FileNotFoundError as e:
            raise fastapi.HTTPException(status_code=404, detail="Directory not found") from e

        if ".gitkeep" in files:
            files.remove(".gitkeep")
        return len(files)

    async def get_total_size(self) -> int:
        try:
            files = await aiofiles.os.listdir(self.base_path)
        except FileNotFoundError as e:
            raise fastapi.HTTPException(status_code=404, detail="Directory not found") from e

        if ".gitkeep" in files:
            files.remove(".gitkeep")

        total_size = 0
        for file in files:
            file_path = f"{self.base_path}/{file}"
            size = await aiofiles.os.path.getsize(file_path)
            total_size += size

        return total_size


class S3StorageProvider(StorageProvider):
    """S3-compatible storage provider (works with AWS S3, Cloudflare R2, etc.)"""

    def __init__(  # noqa: PLR0913
        self,
        *,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        region: str = "auto",
        custom_domain: str | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.bucket_name = bucket_name
        self.region = region
        self.custom_domain = custom_domain

    def _get_s3_session(self) -> aioboto3.Session:
        """Create an async S3 session"""
        return aioboto3.Session()

    async def save_file(self, filename: str, content: bytes) -> str:
        session = self._get_s3_session()
        s3_client = session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
        )
        async with s3_client as s3:  # pyright: ignore[reportGeneralTypeIssues]
            try:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=filename,
                    Body=content,
                    ContentType="image/png",
                )
            except ClientError as e:
                raise fastapi.HTTPException(
                    status_code=500, detail=f"Failed to upload file: {e!s}"
                ) from e
            else:
                return filename

    async def delete_file(self, filename: str) -> None:
        session = self._get_s3_session()
        s3_client = session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
        )
        async with s3_client as s3:  # pyright: ignore[reportGeneralTypeIssues]
            try:
                await s3.delete_object(Bucket=self.bucket_name, Key=filename)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "NoSuchKey":
                    raise fastapi.HTTPException(
                        status_code=404, detail="File not found"
                    ) from e
                raise fastapi.HTTPException(
                    status_code=500, detail=f"Failed to delete file: {e!s}"
                ) from e

    async def get_file_url(self, filename: str) -> str:
        # Use custom domain if provided
        if self.custom_domain:
            # Remove trailing slash if present
            domain = self.custom_domain.rstrip("/")
            return f"{domain}/{filename}"

        # For S3-compatible services, construct the public URL
        if self.endpoint_url:
            # Remove trailing slash if present
            endpoint = self.endpoint_url.rstrip("/")
            return f"{endpoint}/{self.bucket_name}/{filename}"
        # Standard AWS S3 URL format
        return (
            f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
        )

    async def list_files(self) -> dict[str, int]:
        session = self._get_s3_session()
        s3_client = session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
        )
        async with s3_client as s3:  # pyright: ignore[reportGeneralTypeIssues]
            try:
                response = await s3.list_objects_v2(Bucket=self.bucket_name)
            except ClientError as e:
                raise fastapi.HTTPException(
                    status_code=500, detail=f"Failed to list files: {e!s}"
                ) from e

            file_sizes: dict[str, int] = {}
            if "Contents" in response:
                for obj in response["Contents"]:
                    filename = obj["Key"]
                    size = obj["Size"]
                    file_sizes[filename] = size

            return file_sizes

    async def get_file_count(self) -> int:
        files = await self.list_files()
        return len(files)

    async def get_total_size(self) -> int:
        files = await self.list_files()
        return sum(files.values())


def get_storage_provider() -> StorageProvider:
    """Factory function to get the appropriate storage provider"""

    if settings.storage_type.lower() == "s3":
        if not all([
            settings.s3_endpoint_url,
            settings.s3_access_key_id,
            settings.s3_secret_access_key,
            settings.s3_bucket_name,
        ]):
            msg = "S3 storage requires S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, and S3_BUCKET_NAME environment variables"
            raise ValueError(msg)

        # Type assertion since we've checked for None above
        return S3StorageProvider(
            endpoint_url=cast("str", settings.s3_endpoint_url),
            access_key_id=cast("str", settings.s3_access_key_id),
            secret_access_key=cast("str", settings.s3_secret_access_key),
            bucket_name=cast("str", settings.s3_bucket_name),
            region=settings.s3_region,
            custom_domain=settings.s3_custom_domain,
        )
    return LocalStorageProvider()
