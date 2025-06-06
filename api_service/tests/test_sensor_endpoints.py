import pytest
import json
from fastapi import HTTPException
from datetime import datetime

def test_get_latest_sensor_data_success(client, mock_gcs_client, sample_sensor_data, test_settings):
    mock_bucket = mock_gcs_client['bucket']
    mock_blobs = [
        type('Blob', (), {'name': 'sensor_data/latest.json', 'download_as_string': lambda: json.dumps(sample_sensor_data)})
    ]
    mock_bucket.list_blobs.return_value = mock_blobs

    response = client.get("/sensor/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["temperature"] == sample_sensor_data["temperature"]
    assert data["humidity"] == sample_sensor_data["humidity"]
    assert data["pressure"] == sample_sensor_data["pressure"]

def test_get_sensor_history_success(client, mock_gcs_client, sample_sensor_data):
    mock_bucket = mock_gcs_client['bucket']
    mock_blobs = [
        type('Blob', (), {
            'name': f'sensor_data/data_{i}.json',
            'download_as_string': lambda: json.dumps(sample_sensor_data)
        })
        for i in range(3)
    ]
    mock_bucket.list_blobs.return_value = mock_blobs

    response = client.get("/sensor/history?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for entry in data:
        assert "temperature" in entry
        assert "humidity" in entry
        assert "pressure" in entry
        assert "timestamp" in entry

def test_get_sensor_history_empty(client, mock_gcs_client):
    mock_bucket = mock_gcs_client['bucket']
    mock_bucket.list_blobs.return_value = []

    response = client.get("/sensor/history")
    assert response.status_code == 200
    assert response.json() == []

def test_get_sensor_history_invalid_limit(client):
    response = client.get("/sensor/history?limit=101")
    assert response.status_code == 422  # Validation error 