from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from google.cloud import storage
import logging
from dateutil import parser
import json
from urllib.parse import urlencode

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
    allow_origins=["*"],
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
    thumbnail_url: str
    timestamp: datetime

def get_storage_client():
    return storage.Client()

def generate_signed_url(
    bucket_name: str, 
    blob_name: str, 
    storage_client: storage.Client,
    width: Optional[int] = None,
    height: Optional[int] = None,
    quality: Optional[int] = None,
    expiration_hours: int = 24
) -> str:
    """
    Generate a signed URL for GCS blob with optional image transformations
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Create signed URL with longer expiration
        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.utcnow() + timedelta(hours=expiration_hours),
            method="GET",
        )
        
        # Add image transformation parameters if specified
        # Note: This works with GCS + Cloud CDN image optimization
        if width or height or quality:
            params = {}
            if width:
                params['w'] = str(width)
            if height:
                params['h'] = str(height)
            if quality:
                params['q'] = str(quality)
            
            # Add transformation parameters to URL
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}{urlencode(params)}"
        
        return url
        
    except Exception as e:
        logger.error(f"Error generating signed URL for {blob_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate image URL")

@app.get("/sensor/latest", response_model=SensorData)
async def get_latest_sensor_data(
    storage_client: storage.Client = Depends(get_storage_client),
    settings: Settings = Depends(get_settings)
):
    """Fetch the latest sensor data from Google Cloud Storage"""
    try:
        bucket = storage_client.bucket(settings.GCS_BUCKET)
        blobs = list(bucket.list_blobs(prefix="sensor_data/", delimiter="/"))
        
        if not blobs:
            raise HTTPException(status_code=404, detail="No sensor data found")
            
        blobs.sort(key=lambda x: x.name, reverse=True)
        latest_blob = blobs[0]
        
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

@app.get("/images", response_model=List[ImageData])
async def list_images(
    limit: Optional[int] = Query(24, ge=1, le=100),
    storage_client: storage.Client = Depends(get_storage_client),
    settings: Settings = Depends(get_settings)
):
    """
    List images from Google Cloud Storage with signed URLs
    """
    try:
        bucket = storage_client.bucket(settings.GCS_BUCKET)
        blobs = bucket.list_blobs(prefix="images/", max_results=limit)
        
        images = []
        for blob in blobs:
            if not blob.name.endswith('.jpg'):
                continue
                
            try:
                name = blob.name.split('/')[-1]
                timestamp_str = name.split('capture_')[1].split('.jpg')[0]
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                # Generate signed URLs for full image and thumbnail
                full_url = generate_signed_url(
                    settings.GCS_BUCKET, 
                    blob.name, 
                    storage_client,
                    width=1280,  # Max width for full image
                    quality=85
                )
                
                thumbnail_url = generate_signed_url(
                    settings.GCS_BUCKET, 
                    blob.name, 
                    storage_client,
                    width=128,  # Thumbnail size
                    quality=60
                )
                
                images.append(ImageData(
                    id=name,
                    url=full_url,
                    thumbnail_url=thumbnail_url,
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

@app.get("/images/{image_name}/urls")
async def get_image_urls(
    image_name: str,
    width: Optional[int] = Query(None, gt=0, le=2048),
    height: Optional[int] = Query(None, gt=0, le=2048),
    quality: Optional[int] = Query(85, ge=1, le=100),
    storage_client: storage.Client = Depends(get_storage_client),
    settings: Settings = Depends(get_settings)
):
    """
    Get signed URLs for a specific image with different sizes
    """
    try:
        bucket = storage_client.bucket(settings.GCS_BUCKET)
        blob_name = f"images/{image_name}"
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Generate different sized URLs
        urls = {
            "original": generate_signed_url(settings.GCS_BUCKET, blob_name, storage_client),
            "large": generate_signed_url(settings.GCS_BUCKET, blob_name, storage_client, width=1280, quality=85),
            "medium": generate_signed_url(settings.GCS_BUCKET, blob_name, storage_client, width=640, quality=80),
            "small": generate_signed_url(settings.GCS_BUCKET, blob_name, storage_client, width=320, quality=75),
            "thumbnail": generate_signed_url(settings.GCS_BUCKET, blob_name, storage_client, width=128, quality=60),
        }
        
        # Add custom size if requested
        if width or height:
            urls["custom"] = generate_signed_url(
                settings.GCS_BUCKET, 
                blob_name, 
                storage_client, 
                width=width, 
                height=height, 
                quality=quality
            )
        
        return urls
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating URLs for image {image_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate image URLs")

@app.get("/sensor/history", response_model=List[SensorData])
async def get_sensor_history(
    limit: Optional[int] = Query(24, ge=1, le=100),
    storage_client: storage.Client = Depends(get_storage_client),
    settings: Settings = Depends(get_settings)
):
    """Fetch historical sensor data from Google Cloud Storage"""
    try:
        bucket = storage_client.bucket(settings.GCS_BUCKET)
        blobs = list(bucket.list_blobs(prefix="sensor_data/", delimiter="/", max_results=limit))
        
        if not blobs:
            return []
            
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