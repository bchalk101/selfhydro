import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import google.cloud.storage
from main import app, get_storage_client
from config import Settings
from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket

@pytest.fixture(autouse=True)
def mock_gcs_client(mocker):
    mock_bucket = MagicMock(spec=Bucket)
    mock_blob = MagicMock(spec=Blob)
    
    mock_bucket.blob.return_value = mock_blob
    mock_bucket.name = "test-bucket"
    
    # Create test image blobs
    test_image_blobs = []
    for i in range(3):
        test_blob = MagicMock(spec=Blob)
        test_blob.name = f"images/capture_20250601_08425{i}.jpg"
        test_image_blobs.append(test_blob)
    
    # Create test sensor blobs
    test_sensor_blobs = []
    for i in range(3):
        test_blob = MagicMock(spec=Blob)
        test_blob.name = f"sensor_data/data_{i}.json"
        test_sensor_blobs.append(test_blob)
    
    # Mock list_blobs to return appropriate blobs based on prefix
    def mock_list_blobs(prefix=None, **kwargs):
        if prefix == "images/":
            return test_image_blobs
        elif prefix == "sensor_data/":
            return test_sensor_blobs
        return []
    
    mock_bucket.list_blobs.side_effect = mock_list_blobs
    
    # Setup mock client behavior
    mock_client = MagicMock(spec=google.cloud.storage.Client)
    mock_client.bucket.return_value = mock_bucket
    
    # Setup mock blob behavior
    def mock_exists():
        return "nonexistent" not in mock_blob.name
    mock_blob.exists.side_effect = mock_exists
    
    def mock_download_as_string():
        return b'{"temperature": 25.5, "humidity": 60.0, "pressure": 1013.25, "timestamp": "2024-01-01T12:00:00Z"}'
    mock_blob.download_as_string.side_effect = mock_download_as_string
    
    # Mock signed URL generation
    def mock_generate_signed_url(**kwargs):
        blob_name = mock_blob.name if hasattr(mock_blob, 'name') else "test.jpg"
        width = kwargs.get('width', '')
        height = kwargs.get('height', '')
        quality = kwargs.get('quality', '')
        params = f"?w={width}&h={height}&q={quality}" if any([width, height, quality]) else ""
        return f"https://storage.googleapis.com/test-bucket/{blob_name}{params}&signed=true"
    
    mock_blob.generate_signed_url.side_effect = mock_generate_signed_url
    
    # Override the FastAPI dependency
    app.dependency_overrides[get_storage_client] = lambda: mock_client
    
    yield {
        'client': mock_client,
        'bucket': mock_bucket,
        'blob': mock_blob,
        'image_blobs': test_image_blobs,
        'sensor_blobs': test_sensor_blobs
    }
    
    # Clean up the override after the test
    app.dependency_overrides.clear()

@pytest.fixture
def test_settings():
    return Settings(
        GCS_BUCKET="test-bucket",
        BASE_URL="http://localhost:8000"
    )

@pytest.fixture
def client():
    yield TestClient(app)

@pytest.fixture
def mock_storage_client(mocker):
    return mocker.patch("google.cloud.storage.Client")

@pytest.fixture
def sample_sensor_data():
    return {
        "temperature": 25.5,
        "humidity": 60.0,
        "pressure": 1013.25,
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture
def sample_image_data():
    return {
        "id": "capture_20240101_120000.jpg",
        "url": "https://storage.googleapis.com/test-bucket/images/capture_20240101_120000.jpg?w=1280&q=85&signed=true",
        "thumbnail_url": "https://storage.googleapis.com/test-bucket/images/capture_20240101_120000.jpg?w=128&q=60&signed=true",
        "timestamp": datetime(2024, 1, 1, 12, 0, 0)
    }