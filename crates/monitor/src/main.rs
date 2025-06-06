use anyhow::Result;
use dotenv::dotenv;
use google_cloud_storage::{
    client::{Client, ClientConfig},
    http::objects::upload::{Media, UploadObjectRequest, UploadType},
};
use influxdb::{Client as InfluxClient, InfluxDbWriteable};
use log::{error, info};
use serde::Serialize;
use sensors::BME280Sensor;
use std::time::Duration;
use tokio::time;

use selfhydro_camera::{capture_image, generate_image_key};

#[derive(InfluxDbWriteable)]
struct SensorMeasurement {
    time: chrono::DateTime<chrono::Utc>,
    #[influxdb(tag)]
    location: String,
    temperature: f64,
    humidity: f64,
    pressure: f64,
}

async fn upload_to_gcs(client: &Client, bucket: &str, key: &str, data: Vec<u8>) -> Result<()> {
    let upload_type = UploadType::Simple(Media::new(key.to_string()));
    client
        .upload_object(
            &UploadObjectRequest {
                bucket: bucket.to_string(),
                ..Default::default()
            },
            data,
            &upload_type,
        )
        .await?;

    info!("[{}:{}] Successfully uploaded to GCS: {}", file!(), line!(), key);
    Ok(())
}

async fn upload_sensor_data(client: &Client, bucket: &str, reading: sensors::SensorReading) -> Result<()> {
    let sensor_data = SensorData {
        temperature: reading.temperature,
        humidity: reading.humidity,
        pressure: reading.pressure,
        timestamp: reading.timestamp.to_rfc3339(),
    };

    let data = serde_json::to_vec(&sensor_data)?;
    let key = format!(
        "sensor_data/{}.json",
        reading.timestamp.format("%Y%m%d_%H%M%S")
    );

    upload_to_gcs(client, bucket, &key, data).await
}

async fn write_to_influxdb(client: &InfluxClient, reading: &sensors::SensorReading) -> Result<()> {
    let measurement = SensorMeasurement {
        time: reading.timestamp,
        location: "greenhouse".to_string(),
        temperature: reading.temperature,
        humidity: reading.humidity,
        pressure: reading.pressure,
    };

    let write_query = measurement.into_query("environment");
    client.query(write_query).await?;
    
    info!("[{}:{}] Successfully wrote sensor data to InfluxDB", file!(), line!());
    Ok(())
}

#[derive(Serialize)]
struct SensorData {
    temperature: f64,
    humidity: f64,
    pressure: f64,
    timestamp: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    dotenv().ok();
    env_logger::init();

    // Initialize GCS client
    let config = ClientConfig::default().with_auth().await?;
    let gcs_client = Client::new(config);
    let gcs_bucket = std::env::var("GCS_BUCKET").expect("GCS_BUCKET not set");

    // Initialize InfluxDB client
    let influx_host = std::env::var("INFLUX_HOST").expect("INFLUX_HOST not set");
    let influx_db = std::env::var("INFLUX_DB").expect("INFLUX_DB not set");
    let influx_client = InfluxClient::new(influx_host, influx_db);

    // Add authentication if provided
    let influx_client = if let Ok(token) = std::env::var("INFLUX_TOKEN") {
        influx_client.with_token(token)
    } else {
        influx_client
    };

    // Initialize the BME280 sensor
    let mut sensor = BME280Sensor::new()?;

    info!("[{}:{}] Starting combined monitoring service", file!(), line!());

    let mut image_interval = time::interval(Duration::from_secs(30 * 60)); // 30 minutes
    let mut sensor_interval = time::interval(Duration::from_secs(30 * 60)); // 1 minute

    loop {
        tokio::select! {
            _ = image_interval.tick() => {
                match capture_image() {
                    Ok(image_data) => {
                        let key = generate_image_key();
                        if let Err(e) = upload_to_gcs(&gcs_client, &gcs_bucket, &key, image_data).await {
                            error!("[{}:{}] Failed to upload image to GCS: {}", file!(), line!(), e);
                        }
                    }
                    Err(e) => error!("[{}:{}] Failed to capture image: {}", file!(), line!(), e),
                }
            }
            _ = sensor_interval.tick() => {
                match sensor.read() {
                    Ok(reading) => {
                        info!(
                            "[{}:{}] Temperature: {:.1}°C, Humidity: {:.1}%, Pressure: {:.1} hPa",
                            file!(), line!(),
                            reading.temperature,
                            reading.humidity,
                            reading.pressure / 100.0 // Convert Pa to hPa for display
                        );
                        
                        // Upload to both GCS and InfluxDB
                        if let Err(e) = upload_sensor_data(&gcs_client, &gcs_bucket, reading.clone()).await {
                            error!("[{}:{}] Failed to upload sensor data to GCS: {}", file!(), line!(), e);
                        }

                        if let Err(e) = write_to_influxdb(&influx_client, &reading).await {
                            error!("[{}:{}] Failed to write sensor data to InfluxDB: {}", file!(), line!(), e);
                        }
                    }
                    Err(e) => {
                        error!("[{}:{}] Error reading sensor: {}", file!(), line!(), e);
                    }
                }
            }
        }
    }
} 