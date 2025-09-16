# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based image hosting service (similar to Imgur) built with FastAPI. It's a modular application that accepts image uploads via URL or base64 data, stores them locally or in S3-compatible storage, and serves them back through HTTP endpoints.

## Development Commands

### Environment Setup

```bash
# Install dependencies using uv (ultra-fast Python package manager)
uv sync

# Run in development mode
uv run uvicorn main:app --reload --port 9078

# Run directly with Python
uv run python main.py
```

### Production Deployment

```bash
# Using PM2 (process manager)
pm2 start pm2.json
pm2 stop image-host
pm2 restart image-host
pm2 logs image-host
```

### Type Checking

```bash
# Uses Pyright with configuration in pyproject.toml
pyright main.py
```

### Code Linting and Formatting

```bash
# Run ruff linter
ruff check

# Run ruff linter with auto-fix
ruff check --fix

# Format code with ruff
ruff format
```

## Architecture

### Core Structure

- **Modular application**: Code organized in `app/` package with separate modules
  - `main.py`: Application entry point and route definitions
  - `app/config.py`: Configuration management using pydantic-settings
  - `app/storage.py`: Storage providers (local filesystem and S3-compatible)
  - `app/models.py`: Pydantic models for request/response data
  - `app/routes.py`: Route handler functions
- **FastAPI framework**: Modern async Python web framework
- **File storage**: Local filesystem under `files/` directory or S3-compatible storage
- **Authentication**: Simple API key-based authentication via environment variable

### Key Components

**Environment Configuration**:

- `API_KEY`: Required environment variable for upload authentication
- `FILESIZE_LIMIT`: 20MB maximum file size

**Core Endpoints**:

- `POST /upload`: Upload images via URL or base64 data (requires API key)
- `GET /{filename}`: Serve uploaded images
- `DELETE /{filename}`: Delete specific image
- `GET /files`: List all files with their sizes
- `GET /files/count`: Get total file count
- `GET /files/size`: Get total storage size used
- `GET /health`: Health check endpoint

**File Handling**:

- Random 16-character filename generation using ASCII letters
- All files saved as `.png` regardless of input format
- Async file operations using `aiofiles`

### Dependencies

- **FastAPI**: Web framework and API routing
- **uvicorn**: ASGI server for running the application
- **aiofiles**: Async file operations
- **aiohttp**: HTTP client for downloading from URLs
- **python-dotenv**: Environment variable loading

### Storage Structure

```plaintext
files/
├── .gitkeep          # Keeps directory in version control
└── [random].png      # Uploaded images with random filenames
```

## Development Notes

- The application expects a `files/` directory to exist for storage
- API key must be set in environment variables or `.env` file
- All uploaded files are converted to PNG format regardless of input
- The application redirects root requests to the GitHub repository
- PM2 configuration assumes a virtual environment at `./.venv/`
