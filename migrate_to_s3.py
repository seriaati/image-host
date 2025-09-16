#!/usr/bin/env python3
"""
Migration utility to move files from local storage to S3.

Usage:
    python migrate_to_s3.py

This script will:
1. Read all files from the local files/ directory
2. Upload them to S3 using the configured S3 provider
3. Optionally delete local files after successful upload (with confirmation)

Environment variables required for S3:
- STORAGE_TYPE=s3
- S3_ENDPOINT_URL
- S3_ACCESS_KEY_ID
- S3_SECRET_ACCESS_KEY
- S3_BUCKET_NAME
- S3_REGION (optional, defaults to "auto")
- S3_CUSTOM_DOMAIN (optional)
"""

import asyncio
import sys

import aiofiles

from app.config import settings
from app.storage import LocalStorageProvider, S3StorageProvider, get_storage_provider


async def migrate_files_to_s3(
    local_path: str = "files", delete_local: bool = False, dry_run: bool = False
) -> None:
    """
    Migrate files from local storage to S3.

    Args:
        local_path: Path to local files directory
        delete_local: Whether to delete local files after successful upload
        dry_run: If True, only show what would be migrated without actually doing it
    """
    print("🚀 Starting migration from local storage to S3...")

    # Validate S3 configuration
    if settings.storage_type.lower() != "s3":
        print("❌ Error: STORAGE_TYPE must be set to 's3' for migration")
        print("   Please set the environment variable: STORAGE_TYPE=s3")
        return

    try:
        s3_provider = get_storage_provider()
        if not isinstance(s3_provider, S3StorageProvider):
            print("❌ Error: S3 storage provider not configured properly")
            return
    except ValueError as e:
        print(f"❌ Error: {e}")
        return

    # Initialize local storage provider
    local_provider = LocalStorageProvider(local_path)

    # Get list of local files
    try:
        local_files = await local_provider.list_files()
    except Exception as e:
        print(f"❌ Error reading local files: {e}")
        return

    if not local_files:
        print("ℹ️  No files found in local storage to migrate")
        return

    print(f"📁 Found {len(local_files)} files to migrate")
    total_size = sum(local_files.values())
    print(f"📊 Total size: {format_size(total_size)}")

    if dry_run:
        print("\n🔍 DRY RUN - Files that would be migrated:")
        for filename, size in local_files.items():
            print(f"   • {filename} ({format_size(size)})")
        return

    # Confirm migration
    print(f"\n⚠️  This will upload {len(local_files)} files to S3")
    if delete_local:
        print("⚠️  Local files will be DELETED after successful upload")

    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != "y":
        print("❌ Migration cancelled")
        return

    # Start migration
    successful_uploads = []
    failed_uploads = []

    print("\n📤 Starting file uploads...")

    for i, (filename, size) in enumerate(local_files.items(), 1):
        print(f"[{i}/{len(local_files)}] Uploading {filename} ({format_size(size)})...")

        try:
            # Read local file
            file_path = f"{local_path}/{filename}"
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()

            # Upload to S3
            await s3_provider.save_file(filename, content)
            successful_uploads.append(filename)
            print(f"   ✅ Successfully uploaded {filename}")

        except Exception as e:
            failed_uploads.append((filename, str(e)))
            print(f"   ❌ Failed to upload {filename}: {e}")

    # Report results
    print(f"\n📊 Migration completed:")
    print(f"   ✅ Successful uploads: {len(successful_uploads)}")
    print(f"   ❌ Failed uploads: {len(failed_uploads)}")

    if failed_uploads:
        print("\n❌ Failed uploads:")
        for filename, error in failed_uploads:
            print(f"   • {filename}: {error}")

    # Delete local files if requested and all uploads succeeded
    if delete_local and not failed_uploads:
        print(f"\n🗑️  Deleting {len(successful_uploads)} local files...")

        for filename in successful_uploads:
            try:
                await local_provider.delete_file(filename)
                print(f"   ✅ Deleted local file: {filename}")
            except Exception as e:
                print(f"   ⚠️  Failed to delete local file {filename}: {e}")

    elif delete_local and failed_uploads:
        print("\n⚠️  Not deleting local files due to upload failures")

    print("\n🎉 Migration process completed!")


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


async def verify_s3_connection() -> bool:
    """Verify S3 connection and bucket access."""
    try:
        s3_provider = get_storage_provider()
        if not isinstance(s3_provider, S3StorageProvider):
            return False

        # Try to list files to verify connection
        await s3_provider.list_files()
        return True
    except Exception as e:
        print(f"❌ S3 connection test failed: {e}")
        return False


async def main() -> None:
    """Main entry point for the migration script."""
    print("🔧 Image Host Migration Utility")
    print("===============================")

    # Check command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Migrate files from local storage to S3")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be migrated without doing it"
    )
    parser.add_argument(
        "--delete-local", action="store_true", help="Delete local files after successful upload"
    )
    parser.add_argument(
        "--local-path", default="files", help="Path to local files directory (default: files)"
    )
    args = parser.parse_args()

    # Verify S3 connection first
    print("🔍 Testing S3 connection...")
    if not await verify_s3_connection():
        print("❌ Cannot connect to S3. Please check your configuration.")
        sys.exit(1)
    print("✅ S3 connection successful")

    # Run migration
    await migrate_files_to_s3(
        local_path=args.local_path, delete_local=args.delete_local, dry_run=args.dry_run
    )


if __name__ == "__main__":
    asyncio.run(main())
