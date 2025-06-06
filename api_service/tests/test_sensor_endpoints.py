import pytest
import json
from unittest.mock import MagicMock
from datetime import datetime

def test_get_latest_sensor_data_success(client, mock_gcs_client, sample_sensor_data, test_settings):
    """Test successful retrieval of latest sensor data"""
    mock_bucket = mock_gcs_client['bucket']
    
    # Create mock sensor data blobs
    mock_sensor_blobs = []
    for i in range(3):
        mock_blob = MagicMock()
        mock_blob.name = f'sensor_data/data_202406{i:02d}_120000.json'
        mock_blob.download_as_string.return_value = json.dumps(sample_sensor_data).encode()
        mock_sensor_blobs.append(mock_blob)
    
    def mock_list_blobs(prefix=None, **kwargs):
        if prefix == "sensor_data/":
            return mock_sensor_blobs
        return []
    
    mock_bucket.list_blobs.side_effect = mock_list_blobs

    response = client.get("/sensor/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["temperature"] == sample_sensor_data["temperature"]
    assert data["humidity"] == sample_sensor_data["humidity"]
    assert data["pressure"] == sample_sensor_data["pressure"]
    assert "timestamp" in data


def test_get_sensor_history_success(client, mock_gcs_client, sample_sensor_data):
    """Test successful retrieval of sensor history"""
    mock_bucket = mock_gcs_client['bucket']
    
    # Create mock sensor data blobs with different timestamps
    mock_sensor_blobs = []
    for i in range(3):
        mock_blob = MagicMock()
        mock_blob.name = f'sensor_data/data_202406{i:02d}_120000.json'
        
        # Create slightly different sensor data for each blob
        sensor_data = sample_sensor_data.copy()
        sensor_data["temperature"] = 25.5 + i
        sensor_data["timestamp"] = f"2024-06-{i+1:02d}T12:00:00Z"
        
        mock_blob.download_as_string.return_value = json.dumps(sensor_data).encode()
        mock_sensor_blobs.append(mock_blob)
    
    def mock_list_blobs(prefix=None, **kwargs):
        if prefix == "sensor_data/":
            return mock_sensor_blobs
        return []
    
    mock_bucket.list_blobs.side_effect = mock_list_blobs

    response = client.get("/sensor/history?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    for entry in data:
        assert "temperature" in entry
        assert "humidity" in entry
        assert "pressure" in entry
        assert "timestamp" in entry
        assert isinstance(entry["temperature"], float)
        assert isinstance(entry["humidity"], float)
        assert isinstance(entry["pressure"], float)

def test_get_sensor_history_empty(client, mock_gcs_client):
    """Test sensor history when no data exists"""
    mock_bucket = mock_gcs_client['bucket']
    
    def mock_list_blobs(prefix=None, **kwargs):
        return []
    
    mock_bucket.list_blobs.side_effect = mock_list_blobs

    response = client.get("/sensor/history")
    assert response.status_code == 200
    assert response.json() == []

def test_get_sensor_history_invalid_limit(client):
    """Test sensor history with invalid limit parameter"""
    response = client.get("/sensor/history?limit=101")
    assert response.status_code == 422  # Validation error

def test_get_sensor_history_malformed_data(client, mock_gcs_client):
    """Test sensor history with malformed JSON data"""
    mock_bucket = mock_gcs_client['bucket']
    
    # Create mock blobs with malformed data
    mock_sensor_blobs = []
    
    # Valid blob
    valid_blob = MagicMock()
    valid_blob.name = 'sensor_data/valid_data.json'
    valid_blob.download_as_string.return_value = json.dumps({
        "temperature": 25.5,
        "humidity": 60.0,
        "pressure": 1013.25,
        "timestamp": "2024-01-01T12:00:00Z"
    }).encode()
    mock_sensor_blobs.append(valid_blob)
    
    # Invalid blob (malformed JSON)
    invalid_blob = MagicMock()
    invalid_blob.name = 'sensor_data/invalid_data.json'
    invalid_blob.download_as_string.return_value = b'{"invalid": json}'
    mock_sensor_blobs.append(invalid_blob)
    
    # Incomplete blob (missing fields)
    incomplete_blob = MagicMock()
    incomplete_blob.name = 'sensor_data/incomplete_data.json'
    incomplete_blob.download_as_string.return_value = json.dumps({
        "temperature": 25.5
        # Missing other required fields
    }).encode()
    mock_sensor_blobs.append(incomplete_blob)
    
    def mock_list_blobs(prefix=None, **kwargs):
        if prefix == "sensor_data/":
            return mock_sensor_blobs
        return []
    
    mock_bucket.list_blobs.side_effect = mock_list_blobs

    response = client.get("/sensor/history")
    assert response.status_code == 200
    data = response.json()
    # Should only return the valid entry
    assert len(data) == 1
    assert data[0]["temperature"] == 25.5

def test_get_sensor_history_with_limit(client, mock_gcs_client, sample_sensor_data):
    """Test sensor history with specific limit"""
    mock_bucket = mock_gcs_client['bucket']
    
    # Create more mock blobs than the limit
    mock_sensor_blobs = []
    for i in range(10):
        mock_blob = MagicMock()
        mock_blob.name = f'sensor_data/data_{i:03d}.json'
        mock_blob.download_as_string.return_value = json.dumps(sample_sensor_data).encode()
        mock_sensor_blobs.append(mock_blob)
    
    def mock_list_blobs(prefix=None, max_results=None, **kwargs):
        if prefix == "sensor_data/":
            return mock_sensor_blobs[:max_results] if max_results else mock_sensor_blobs
        return []
    
    mock_bucket.list_blobs.side_effect = mock_list_blobs

    # Test with limit of 5
    response = client.get("/sensor/history?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5