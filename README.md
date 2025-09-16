# Image Host

An image hosting service built with FastAPI. Upload images via URL or base64 data and serve them through simple HTTP endpoints.

This is made for [Hoyo Buddy](https://github.com/seriaati/hoyo-buddy).

## Features

- **Multiple Upload Methods**: Upload via URL or base64 encoded data
- **Flexible Storage**: Local filesystem or S3-compatible storage (AWS S3, Cloudflare R2, etc.)
- **Simple API**: RESTful endpoints with JSON responses
- **File Management**: List, count, and get total size of uploaded files
- **Health Monitoring**: Built-in health check endpoint
- **Secure**: API key authentication for uploads
- **Format Conversion**: All uploads converted to PNG format
- **Random Filenames**: 16-character random filenames for privacy

## API Endpoints

### Upload Image

```
POST /upload
```

**Authentication**: Requires `X-API-Key` header

**Request Body** (JSON):

```json
{
  "url": "https://example.com/image.jpg"
}
```

OR

```json
{
  "data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
}
```

**Response**:

```json
{
  "message": "File uploaded successfully",
  "filename": "abcdef1234567890.png",
  "url": "http://localhost:9078/abcdef1234567890.png"
}
```

### Get Image

```
GET /{filename}
```

Serves the uploaded image file directly.

### Delete Image

```
DELETE /{filename}
```

**Authentication**: Requires `X-API-Key` header

### List Files

```
GET /files
```

Returns list of all files with their sizes.

### File Statistics

```
GET /files/count  # Get total file count
GET /files/size   # Get total storage size
```

### Health Check

```
GET /health
```

Returns service health status.

## Self-Hosting Instructions

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone the repository**:

   ```bash
   git clone <your-repo-url>
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
   echo "API_KEY=your-secret-api-key-here" > .env
   ```

4. **Create storage directory** (for local storage only):

   ```bash
   mkdir -p files
   ```

### Running the Service

#### Development Mode

```bash
# Using uv
uv run uvicorn main:app --reload --port 9078

# Or directly
uv run python main.py
```

#### Production Mode

**Option 1: Using PM2** (recommended)

```bash
# Install PM2 globally
npm install -g pm2

# Start the service
pm2 start pm2.json

# Monitor logs
pm2 logs image-host

# Stop/restart
pm2 stop image-host
pm2 restart image-host
```

**Option 2: Using Uvicorn directly**

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 9078
```

### Configuration

Environment variables (set in `.env` file):

**Required**:

- `API_KEY`: Secret key for upload authentication

**Optional**:

- `FILESIZE_LIMIT`: Maximum file size in bytes (default: 20MB)

**Storage Configuration**:

- `STORAGE_TYPE`: Storage backend - "local" (default) or "s3"

**S3 Storage (required when STORAGE_TYPE=s3)**:

- `S3_ENDPOINT_URL`: S3 endpoint URL (e.g., <https://s3.amazonaws.com> for AWS, https://[account-id].r2.cloudflarestorage.com for Cloudflare R2)
- `S3_ACCESS_KEY_ID`: S3 access key ID
- `S3_SECRET_ACCESS_KEY`: S3 secret access key
- `S3_BUCKET_NAME`: S3 bucket name
- `S3_REGION`: S3 region (default: "auto")
- `S3_CUSTOM_DOMAIN`: Custom domain for file URLs (optional, e.g., <https://cdn.example.com>)

### Storage Options

#### Local Storage (Default)

Files are stored in the `files/` directory on the local filesystem.

#### S3-Compatible Storage

Supports AWS S3, Cloudflare R2, and other S3-compatible services. Configure using environment variables:

```bash
# Example for AWS S3
STORAGE_TYPE=s3
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1

# Example for Cloudflare R2
STORAGE_TYPE=s3
S3_ENDPOINT_URL=https://[account-id].r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=your-r2-access-key
S3_SECRET_ACCESS_KEY=your-r2-secret-key
S3_BUCKET_NAME=your-r2-bucket
S3_REGION=auto
S3_CUSTOM_DOMAIN=https://your-r2-custom-domain.com
```

All uploaded images are converted to PNG format with randomly generated 16-character filenames regardless of storage backend.

## Usage Examples

### Upload via URL

```bash
curl -X POST "http://localhost:9078/upload" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/image.jpg"}'
```

### Upload via base64

```bash
curl -X POST "http://localhost:9078/upload" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"data": "data:image/jpeg;base64,/9j/4AAQ..."}'
```

### Get file statistics

```bash
curl "http://localhost:9078/files/count"
curl "http://localhost:9078/files/size"
```

## Security Notes

- Set a strong, unique `API_KEY` in production
- Consider running behind a reverse proxy (nginx, Cloudflare)
- Monitor file storage usage to prevent disk space issues
- Implement rate limiting for production deployments

## Contributing

For development setup, code style guidelines, and contribution instructions, see [CONTRIBUTING.md](CONTRIBUTING.md).
