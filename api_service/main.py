from fastapi import FastAPI, HTTPException, Query, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import os
from google.cloud import storage
import aiohttp
import logging
from dateutil import parser
import io
import json

from config import Settings, get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SelfHydro API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SensorData(BaseModel):
    temperature: float
    humidity: float
    pressure: float
    timestamp: datetime

class ImageData(BaseModel):
    id: str
    url: str
    timestamp: datetime

# Initialize Google Cloud Storage client
storage_client = storage.Client()

@app.get("/sensor/latest", response_model=SensorData)
async def get_latest_sensor_data(settings: Settings = Depends(get_settings)):
    """
    Fetch the latest sensor data from Google Cloud Storage
    """
    try:
        bucket = storage_client.bucket(settings.GCS_BUCKET)
        # List all sensor data files, sorted by timestamp (newest first)
        blobs = list(bucket.list_blobs(prefix="sensor_data/", delimiter="/"))
        
        if not blobs:
            raise HTTPException(status_code=404, detail="No sensor data found")
            
        # Sort blobs by name (which contains timestamp) in descending order
        blobs.sort(key=lambda x: x.name, reverse=True)
        latest_blob = blobs[0]
        
        # Download and parse the latest sensor data
        data = json.loads(latest_blob.download_as_string())
        
        return SensorData(
            temperature=data["temperature"],
            humidity=data["humidity"],
            pressure=data["pressure"],
            timestamp=parser.parse(data["timestamp"])
        )
    except Exception as e:
        logger.error(f"Error fetching sensor data from GCS: {e}")
        raise HTTPException(status_code=503, detail="Failed to fetch sensor data")

@app.get("/images/{image_name}/stream")
async def stream_image(
    image_name: str,
    settings: Settings = Depends(get_settings)
):
    """
    Stream an image directly from Google Cloud Storage
    """
    try:
        bucket = storage_client.bucket(settings.GCS_BUCKET)
        blob = bucket.blob(f"images/{image_name}")
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Image not found")
            
        # Download the image into memory
        image_data = io.BytesIO()
        blob.download_to_file(image_data)
        image_data.seek(0)
        
        return StreamingResponse(
            content=image_data,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        logger.error(f"Error streaming image: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream image")

@app.get("/images", response_model=List[ImageData])
async def list_images(
    limit: Optional[int] = Query(24, ge=1, le=100),
    settings: Settings = Depends(get_settings)
):
    """
    List images from Google Cloud Storage
    """
    try:
        bucket = storage_client.bucket(settings.GCS_BUCKET)
        blobs = bucket.list_blobs(prefix="images/", max_results=limit)
        
        images = []
        for blob in blobs:
            if not blob.name.endswith('.jpg'):
                continue
                
            try:
                # Parse timestamp from filename (format: capture_YYYYMMDD_HHMMSS.jpg)
                name = blob.name.split('/')[-1]  # Get just the filename
                timestamp_str = name.split('capture_')[1].split('.jpg')[0]
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                images.append(ImageData(
                    id=name,
                    url=f"{settings.BASE_URL}/images/{name}/stream",  # Updated to use streaming endpoint
                    timestamp=timestamp
                ))
            except (IndexError, ValueError) as e:
                logger.warning(f"Failed to parse timestamp for image {blob.name}: {e}")
                continue
        
        # Sort by timestamp descending (newest first)
        images.sort(key=lambda x: x.timestamp, reverse=True)
        return images[:limit]
        
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        raise HTTPException(status_code=500, detail="Failed to list images")

@app.get("/sensor/history", response_model=List[SensorData])
async def get_sensor_history(
    limit: Optional[int] = Query(24, ge=1, le=100),
    settings: Settings = Depends(get_settings)
):
    """
    Fetch historical sensor data from Google Cloud Storage
    """
    try:
        bucket = storage_client.bucket(settings.GCS_BUCKET)
        # List all sensor data files
        blobs = list(bucket.list_blobs(prefix="sensor_data/", delimiter="/", max_results=limit))
        
        if not blobs:
            return []
            
        # Sort blobs by name (which contains timestamp) in descending order
        blobs.sort(key=lambda x: x.name, reverse=True)
        
        sensor_data = []
        for blob in blobs[:limit]:
            try:
                data = json.loads(blob.download_as_string())
                sensor_data.append(SensorData(
                    temperature=data["temperature"],
                    humidity=data["humidity"],
                    pressure=data["pressure"],
                    timestamp=parser.parse(data["timestamp"])
                ))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse sensor data from {blob.name}: {e}")
                continue
                
        return sensor_data
        
    except Exception as e:
        logger.error(f"Error fetching sensor history from GCS: {e}")
        raise HTTPException(status_code=503, detail="Failed to fetch sensor history")

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENV == "development"
    ) 