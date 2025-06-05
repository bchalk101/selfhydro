import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import MagicMock
import google.cloud.storage
from main import app
from config import Settings

# Mock the Google Cloud Storage client before importing main
@pytest.fixture(autouse=True)
def mock_gcs_client(monkeypatch):
    mock_client = MagicMock()
    monkeypatch.setattr(google.cloud.storage, "Client", MagicMock(return_value=mock_client))
    return mock_client

@pytest.fixture
def test_settings():
    return Settings(
        GCS_BUCKET="test-bucket",
        BASE_URL="http://test",
        SENSOR_URL="http://test-sensor",
        PORT=8000,
        ENV="test"
    )

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_storage_client(mocker):
    return mocker.patch("main.storage_client")

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