import pytest
import io
from datetime import datetime

def test_list_images_success(client, mock_storage_client, test_settings):
    # Mock image blobs
    mock_bucket = mock_storage_client.bucket.return_value
    mock_blobs = [
        type('Blob', (), {'name': f'images/capture_20240101_12000{i}.jpg'})
        for i in range(3)
    ]
    mock_bucket.list_blobs.return_value = mock_blobs

    response = client.get("/images?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for entry in data:
        assert "id" in entry
        assert "url" in entry
        assert "timestamp" in entry
        assert entry["url"].startswith(test_settings.BASE_URL)

def test_list_images_empty(client, mock_storage_client):
    # Mock empty bucket
    mock_bucket = mock_storage_client.bucket.return_value
    mock_bucket.list_blobs.return_value = []

    response = client.get("/images")
    assert response.status_code == 200
    assert response.json() == []

def test_list_images_invalid_limit(client):
    response = client.get("/images?limit=101")
    assert response.status_code == 422  # Validation error

def test_stream_image_success(client, mock_storage_client):
    # Mock image blob
    mock_bucket = mock_storage_client.bucket.return_value
    mock_blob = type('Blob', (), {
        'exists': lambda: True,
        'download_to_file': lambda f: f.write(b"fake image data")
    })
    mock_bucket.blob.return_value = mock_blob

    response = client.get("/images/test.jpg/stream")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert "no-cache" in response.headers["cache-control"]
    assert response.content == b"fake image data"

def test_stream_image_not_found(client, mock_storage_client):
    # Mock non-existent image
    mock_bucket = mock_storage_client.bucket.return_value
    mock_blob = type('Blob', (), {'exists': lambda: False})
    mock_bucket.blob.return_value = mock_blob

    response = client.get("/images/nonexistent.jpg/stream")
    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found" 