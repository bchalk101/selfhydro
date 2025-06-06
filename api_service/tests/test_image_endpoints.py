import pytest
from unittest.mock import MagicMock

@pytest.mark.skip
def test_list_images_success(client, mock_gcs_client, test_settings):
    """Test successful image listing with signed URLs"""
    mock_bucket = mock_gcs_client['bucket']
    mock_blob = mock_gcs_client['blob']
    
    # Setup mock blob names for the list_blobs call
    mock_image_blobs = []
    for i in range(3):
        mock_img_blob = MagicMock()
        mock_img_blob.name = f'images/capture_20250601_08425{i}.jpg'
        mock_image_blobs.append(mock_img_blob)
    
    def mock_list_blobs(prefix=None, **kwargs):
        if prefix == "images/":
            return mock_image_blobs
        return []
    
    mock_bucket.list_blobs.side_effect = mock_list_blobs
    
    # Mock blob creation for signed URL generation
    def mock_blob_creation(blob_name):
        mock_new_blob = MagicMock()
        mock_new_blob.name = blob_name
        mock_new_blob.generate_signed_url.return_value = f"https://storage.googleapis.com/test-bucket/{blob_name}?signed=true"
        return mock_new_blob
    
    mock_bucket.blob.side_effect = mock_blob_creation

    response = client.get("/images?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    for entry in data:
        assert "id" in entry
        assert "url" in entry
        assert "thumbnail_url" in entry
        assert "timestamp" in entry
        assert "signed=true" in entry["url"]
        assert "signed=true" in entry["thumbnail_url"]
        assert entry["id"].endswith(".jpg")

@pytest.mark.skip
def test_list_images_empty(client, mock_gcs_client):
    """Test image listing when no images exist"""
    mock_bucket = mock_gcs_client['bucket']
    
    def mock_list_blobs(prefix=None, **kwargs):
        return []
    
    mock_bucket.list_blobs.side_effect = mock_list_blobs

    response = client.get("/images")
    assert response.status_code == 200
    assert response.json() == []

def test_list_images_invalid_limit(client):
    """Test image listing with invalid limit parameter"""
    response = client.get("/images?limit=101")
    assert response.status_code == 422  # Validation error

@pytest.mark.skip
def test_get_image_urls_success(client, mock_gcs_client):
    """Test getting URLs for a specific image"""
    mock_bucket = mock_gcs_client['bucket']
    mock_blob = MagicMock()
    mock_blob.name = "images/test.jpg"
    mock_blob.exists.return_value = True
    
    def mock_generate_signed_url(**kwargs):
        width = kwargs.get('width', '')
        height = kwargs.get('height', '')
        quality = kwargs.get('quality', '')
        params = []
        if width:
            params.append(f"w={width}")
        if height:
            params.append(f"h={height}")
        if quality:
            params.append(f"q={quality}")
        param_str = "&".join(params)
        return f"https://storage.googleapis.com/test-bucket/images/test.jpg?{param_str}&signed=true"
    
    mock_blob.generate_signed_url.side_effect = mock_generate_signed_url
    mock_bucket.blob.return_value = mock_blob

    response = client.get("/images/test.jpg/urls")
    assert response.status_code == 200
    data = response.json()
    
    # Check all expected URL sizes
    expected_sizes = ["original", "large", "medium", "small", "thumbnail"]
    for size in expected_sizes:
        assert size in data
        assert "signed=true" in data[size]

@pytest.mark.skip
def test_get_image_urls_with_custom_params(client, mock_gcs_client):
    """Test getting URLs with custom width/height/quality"""
    mock_bucket = mock_gcs_client['bucket']
    mock_blob = MagicMock()
    mock_blob.name = "images/test.jpg"
    mock_blob.exists.return_value = True
    
    def mock_generate_signed_url(**kwargs):
        width = kwargs.get('width', '')
        quality = kwargs.get('quality', '')
        params = []
        if width:
            params.append(f"w={width}")
        if quality:
            params.append(f"q={quality}")
        param_str = "&".join(params)
        return f"https://storage.googleapis.com/test-bucket/images/test.jpg?{param_str}&signed=true"
    
    mock_blob.generate_signed_url.side_effect = mock_generate_signed_url
    mock_bucket.blob.return_value = mock_blob

    response = client.get("/images/test.jpg/urls?width=500&quality=90")
    assert response.status_code == 200
    data = response.json()
    
    # Should include custom URL
    assert "custom" in data
    assert "w=500" in data["custom"]
    assert "q=90" in data["custom"]
    assert "signed=true" in data["custom"]

def test_get_image_urls_not_found(client, mock_gcs_client):
    """Test getting URLs for non-existent image"""
    mock_bucket = mock_gcs_client['bucket']
    mock_blob = MagicMock()
    mock_blob.exists.return_value = False
    mock_bucket.blob.return_value = mock_blob

    response = client.get("/images/nonexistent.jpg/urls")
    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"

def test_get_image_urls_invalid_params(client):
    """Test getting URLs with invalid parameters"""
    # Test width too large
    response = client.get("/images/test.jpg/urls?width=3000")
    assert response.status_code == 422
    
    # Test quality out of range
    response = client.get("/images/test.jpg/urls?quality=101")
    assert response.status_code == 422