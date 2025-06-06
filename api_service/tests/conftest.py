import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import MagicMock
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
    
    test_blobs = []
    for i in range(3):
        test_blob = MagicMock(spec=Blob)
        test_blob.name = f"capture_20250601_08425{i}.jpg"
        test_blobs.append(test_blob)
    mock_bucket.list_blobs.return_value = test_blobs
    
    # Setup mock client behavior
    mock_client = MagicMock(spec=google.cloud.storage.Client)
    mock_client.bucket.return_value = mock_bucket
    
    # Setup mock blob behavior with conditional responses
    def mock_exists():
        return "nonexistent" not in mock_blob.name
    mock_blob.exists.side_effect = mock_exists
    
    def mock_download_as_string():
        if "sensor" in mock_blob.name:
            return b'{"temperature": 25.5, "humidity": 60.0, "pressure": 1013.25, "timestamp": "2024-01-01T12:00:00Z"}'
        return b""
    mock_blob.download_as_string.side_effect = mock_download_as_string
    
    def mock_download_as_bytes():
        if "nonexistent" not in mock_blob.name:
            return b"fake image data"
        raise google.cloud.exceptions.NotFound("Blob not found")
    mock_blob.download_as_bytes.side_effect = mock_download_as_bytes
    
    # Set blob name for streaming
    def mock_get_name():
        return mock_blob._mock_name if hasattr(mock_blob, '_mock_name') else "test.jpg"
    mock_blob.__getattribute__ = lambda self, name: mock_get_name() if name == 'name' else super(MagicMock, self).__getattribute__(name)
    
    mock_blob.upload_from_string.return_value = None
    
    # Override the FastAPI dependency
    app.dependency_overrides[get_storage_client] = lambda: mock_client
    
    yield {
        'client': mock_client,
        'bucket': mock_bucket,
        'blob': mock_blob
    }
    
    # Clean up the override after the test
    app.dependency_overrides.clear()

@pytest.fixture
def test_settings():
    return Settings(
        GCS_BUCKET="test-bucket",
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
        "url": "http://test/images/capture_20240101_120000.jpg/stream",
        "timestamp": datetime(2024, 1, 1, 12, 0, 0)
    } 