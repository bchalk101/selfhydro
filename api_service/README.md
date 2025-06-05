# SelfHydro API Service

A FastAPI-based service that provides an API for the SelfHydro iOS app, interfacing with Google Cloud Storage for images and the Rust sensor service for environmental data.

## Features

- Fetch latest sensor data (temperature, humidity, pressure)
- List and retrieve plant images with timestamps
- Time-based image sorting
- CORS support for web clients
- Automatic API documentation

## Requirements

- Python 3.8+
- Google Cloud credentials
- Access to a Google Cloud Storage bucket
- Connection to the Rust sensor service

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Set up Google Cloud credentials:
   - Create a service account in Google Cloud Console
   - Download the JSON credentials file
   - Set the path in GOOGLE_APPLICATION_CREDENTIALS environment variable

## Running the Service

Development mode:
```bash
python main.py
```

Production mode (using Gunicorn):
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## API Endpoints

### GET /sensor/latest
Returns the latest sensor readings:
```json
{
    "temperature": 25.5,
    "humidity": 65.0,
    "pressure": 101325.0,
    "timestamp": "2023-12-01T12:00:00Z"
}
```

### GET /images
Returns a list of plant images:
```json
[
    {
        "id": "images/capture_20231201_120000.jpg",
        "url": "https://your-domain.com/images/capture_20231201_120000.jpg",
        "timestamp": "2023-12-01T12:00:00Z"
    }
]
```

Query parameters:
- `limit`: Number of images to return (default: 24, max: 100)

## Documentation

Once the service is running, visit:
- `/docs` for Swagger UI documentation
- `/redoc` for ReDoc documentation

## Error Handling

The service includes comprehensive error handling:
- Invalid requests return appropriate HTTP status codes
- Service errors are logged
- Client-friendly error messages
- Graceful handling of missing images or sensor data

## Security Notes

For production deployment:
1. Configure specific CORS origins
2. Use HTTPS
3. Implement rate limiting
4. Set up proper monitoring and logging
5. Use secure credential management 