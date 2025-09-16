#!/usr/bin/env python3
"""
Migration utility to move files from local storage to S3.

Usage:
    python migrate_to_s3.py [options]

Options:
    --dry-run                   Show what would be migrated without doing it
    --delete-local             Delete local files after successful upload
    --local-path PATH          Path to local files directory (default: files)
    --concurrent-uploads N     Number of concurrent uploads (default: 10)
    --max-retries N            Maximum retry attempts for failed uploads (default: 3)
    --start-from N             File index to start from (1-based, for resuming migrations)

This script will:
1. Read all files from the local files/ directory
2. Upload them to S3 concurrently using the configured S3 provider
3. Automatically retry failed uploads with exponential backoff
4. Show real-time progress with upload rate and ETA
5. Optionally delete local files after successful upload (with confirmation)

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
import time

import aiofiles

from app.config import settings
from app.storage import LocalStorageProvider, S3StorageProvider, get_storage_provider


async def upload_file_with_retry(
    s3_provider: S3StorageProvider,
    local_path: str,
    filename: str,
    max_retries: int = 3,
) -> tuple[str, bool, str]:
    """
    Upload a single file with retry logic.

    Returns:
        tuple of (filename, success, error_message)
    """
    for attempt in range(max_retries + 1):
        try:
            file_path = f"{local_path}/{filename}"
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()

            await s3_provider.save_file(filename, content)
            return filename, True, ""

        except Exception as e:
            if attempt == max_retries:
                return filename, False, str(e)
            # Wait before retry (exponential backoff)
            await asyncio.sleep(2 ** attempt)

    return filename, False, "Max retries exceeded"


async def migrate_files_to_s3(
    local_path: str = "files",
    delete_local: bool = False,
    dry_run: bool = False,
    concurrent_uploads: int = 10,
    max_retries: int = 3,
    start_from: int = 1,
) -> None:
    """
    Migrate files from local storage to S3.

    Args:
        local_path: Path to local files directory
        delete_local: Whether to delete local files after successful upload
        dry_run: If True, only show what would be migrated without actually doing it
        concurrent_uploads: Number of concurrent uploads (default: 10)
        max_retries: Maximum retry attempts for failed uploads (default: 3)
        start_from: File index to start from (1-based, for resuming interrupted migrations)
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

    # Convert to ordered list for indexing
    file_list = list(local_files.items())

    # Validate start_from parameter
    if start_from < 1:
        print("❌ Error: --start-from must be >= 1")
        return

    if start_from > len(file_list):
        print(f"❌ Error: --start-from ({start_from}) is greater than total files ({len(file_list)})")
        return

    # Calculate subset to process
    files_to_process = file_list[start_from - 1:]  # Convert to 0-based indexing
    skipped_count = start_from - 1

    print(f"📁 Found {len(local_files)} total files")
    if skipped_count > 0:
        print(f"⏭️  Skipping first {skipped_count} files (resuming from #{start_from})")
    print(f"📤 Will process {len(files_to_process)} files")

    total_size = sum(size for _, size in files_to_process)
    print(f"📊 Size to upload: {format_size(total_size)}")
    print(f"🚀 Upload settings: {concurrent_uploads} concurrent, {max_retries} max retries")

    if dry_run:
        print("\n🔍 DRY RUN - Files that would be migrated:")
        for i, (filename, size) in enumerate(files_to_process, start_from):
            print(f"   [{i}] {filename} ({format_size(size)})")
        return

    # Confirm migration
    print(f"\n⚠️  This will upload {len(files_to_process)} files to S3")
    if skipped_count > 0:
        print(f"⚠️  Skipping first {skipped_count} files (already processed)")
    if delete_local:
        print("⚠️  Local files will be DELETED after successful upload")

    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != "y":
        print("❌ Migration cancelled")
        return

    # Start concurrent migration
    successful_uploads = []
    failed_uploads = []
    completed_count = 0
    total_files = len(files_to_process)

    print(f"\n📤 Starting concurrent uploads ({concurrent_uploads} at a time)...")
    start_time = time.time()

    # Create semaphore to limit concurrent uploads
    semaphore = asyncio.Semaphore(concurrent_uploads)

    async def upload_with_progress(filename: str, size: int, file_index: int) -> None:
        nonlocal completed_count

        async with semaphore:
            result_filename, success, error = await upload_file_with_retry(
                s3_provider, local_path, filename, max_retries
            )

            completed_count += 1
            elapsed = time.time() - start_time
            rate = completed_count / elapsed if elapsed > 0 else 0
            eta = (total_files - completed_count) / rate if rate > 0 else 0

            # Show current file index in the original list
            current_overall_index = start_from + completed_count - 1
            total_overall_files = len(file_list)

            if success:
                successful_uploads.append(result_filename)
                print(f"✅ [{current_overall_index}/{total_overall_files}] {filename} ({format_size(size)}) "
                      f"- {rate:.1f}/s - ETA: {format_time(eta)}")
            else:
                failed_uploads.append((result_filename, error))
                print(f"❌ [{current_overall_index}/{total_overall_files}] {filename} FAILED: {error}")

    # Create tasks for all uploads
    tasks = [
        upload_with_progress(filename, size, i)
        for i, (filename, size) in enumerate(files_to_process, start_from)
    ]

    # Execute all uploads concurrently
    await asyncio.gather(*tasks, return_exceptions=True)

    # Calculate final statistics
    end_time = time.time()
    total_time = end_time - start_time
    avg_rate = completed_count / total_time if total_time > 0 else 0

    print(f"\n⏱️  Migration completed in {format_time(total_time)}")
    print(f"📈 Average upload rate: {avg_rate:.1f} files/second")

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


def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


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
    parser.add_argument(
        "--concurrent-uploads",
        type=int,
        default=10,
        help="Number of concurrent uploads (default: 10)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts for failed uploads (default: 3)",
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=1,
        help="File index to start from (1-based, for resuming interrupted migrations)",
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
        local_path=args.local_path,
        delete_local=args.delete_local,
        dry_run=args.dry_run,
        concurrent_uploads=args.concurrent_uploads,
        max_retries=args.max_retries,
        start_from=args.start_from,
    )


if __name__ == "__main__":
    asyncio.run(main())
