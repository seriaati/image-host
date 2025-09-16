# Contributing to Image Host

Thank you for your interest in contributing to Image Host! This document provides guidelines and information for developers working on the project.

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git

### Getting Started

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/your-username/image-host.git
   cd image-host
   ```

2. **Install dependencies**:
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file
   echo "API_KEY=your-dev-api-key-here" > .env
   ```

4. **Create storage directory** (for local storage):
   ```bash
   mkdir -p files
   ```

5. **Run in development mode**:
   ```bash
   uv run uvicorn main:app --reload --port 9078
   ```

## Project Structure

```plaintext
image-host/
├── main.py              # Application entry point and route definitions
├── app/
│   ├── __init__.py
│   ├── config.py        # Configuration management using pydantic-settings
│   ├── storage.py       # Storage providers (local filesystem and S3-compatible)
│   ├── models.py        # Pydantic models for request/response data
│   └── routes.py        # Route handler functions
├── files/               # Image storage directory (local storage)
├── .env                 # Environment variables
├── pyproject.toml       # Python project configuration
├── pm2.json            # PM2 process configuration
└── requirements.txt     # Python dependencies
```

## Code Quality Tools

We use several tools to maintain code quality:

### Type Checking
```bash
# Uses Pyright with configuration in pyproject.toml
pyright main.py
```

### Linting and Formatting
```bash
# Run ruff linter
ruff check

# Run ruff linter with auto-fix
ruff check --fix

# Format code with ruff
ruff format
```

### Running All Checks
```bash
# Run all quality checks before committing
ruff check --fix && ruff format && pyright main.py
```

## Architecture Overview

### Core Components

- **Modular Application**: Code organized in `app/` package with separate modules
- **FastAPI Framework**: Modern async Python web framework
- **Storage Abstraction**: Pluggable storage providers (local filesystem, S3-compatible)
- **Authentication**: Simple API key-based authentication
- **Configuration Management**: Environment-based configuration using pydantic-settings

### Storage Providers

The application uses an abstract `StorageProvider` base class with two implementations:

1. **LocalStorageProvider**: Stores files in the local `files/` directory
2. **S3StorageProvider**: Stores files in S3-compatible storage (AWS S3, Cloudflare R2, etc.)

### Key Design Decisions

- **PNG Conversion**: All uploaded images are converted to PNG format for consistency
- **Random Filenames**: 16-character random ASCII filenames for privacy and collision avoidance
- **Async Operations**: All file operations use `aiofiles` for non-blocking I/O
- **Error Handling**: Proper HTTP error responses with meaningful messages

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write descriptive docstrings for classes and complex functions
- Keep functions focused and single-purpose

### Testing

Currently, the project doesn't have automated tests. Contributions to add a comprehensive test suite would be welcome!

### Error Handling

- Use FastAPI's `HTTPException` for API errors
- Provide meaningful error messages
- Log errors appropriately for debugging

### Security Considerations

- Never log or expose API keys
- Validate all input data using Pydantic models
- Use secure defaults for configuration
- Be mindful of file upload security (size limits, file type validation)

## Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Run quality checks**:
   ```bash
   ruff check --fix && ruff format && pyright main.py
   ```

4. **Test your changes** manually by running the application

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Deployment

### Development Deployment
```bash
uv run python main.py
```

### Production Deployment

**Using PM2**:
```bash
pm2 start pm2.json
```

**Using Uvicorn directly**:
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 9078
```

## Environment Variables

See the main README.md for complete environment variable documentation.

For development, you typically only need:
```bash
API_KEY=your-dev-api-key
STORAGE_TYPE=local  # or s3 for S3 testing
```

## Common Issues

### Port Already in Use
If port 9078 is already in use, change the port:
```bash
uv run uvicorn main:app --reload --port 8080
```

### File Permission Issues
Ensure the `files/` directory is writable:
```bash
chmod 755 files/
```

### S3 Configuration Issues
When testing S3 storage, ensure all required environment variables are set and the bucket exists.

## Contributing Guidelines

1. **Issues**: Check existing issues before creating new ones
2. **Pull Requests**: Provide clear descriptions of changes
3. **Documentation**: Update documentation for new features
4. **Breaking Changes**: Clearly mark any breaking changes

## Questions?

If you have questions about contributing, please open an issue or start a discussion in the repository.