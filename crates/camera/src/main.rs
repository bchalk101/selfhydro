use anyhow::Result;
use dotenv::dotenv;
use google_cloud_storage::{
    client::{Client, ClientConfig},
    http::objects::upload::{Media, UploadObjectRequest, UploadType},
};
use log::{error, info};
use std::{thread, time::Duration};

use selfhydro_camera::{capture_image, generate_image_key};

async fn upload_to_gcs(client: Client, bucket: &str, key: &str, data: Vec<u8>) -> Result<()> {
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

    info!("Successfully uploaded image to GCS: {}", key);
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    dotenv().ok();
    env_logger::init();

    let config = ClientConfig::default().with_auth().await?;
    let gcs_client = Client::new(config);
    let bucket = std::env::var("GCS_BUCKET").expect("GCS_BUCKET not set");

    info!("Starting camera capture service");

    loop {
        let client = gcs_client.clone();
        match capture_image() {
            Ok(image_data) => {
                let key = generate_image_key();

                if let Err(e) = upload_to_gcs(client, &bucket, &key, image_data).await {
                    error!("Failed to upload image to GCS: {}", e);
                }
            }
            Err(e) => error!("Failed to capture image: {}", e),
        }

        thread::sleep(Duration::from_secs(30 * 60));
    }
}
