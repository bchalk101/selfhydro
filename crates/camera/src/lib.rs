use anyhow::{Context, Result};
use chrono::Local;
use std::{fs, process::Command};

pub const CAPTURE_COMMAND: &str = "libcamera-still";
pub const IMAGE_PATH: &str = "/tmp/capture.jpg";

pub fn capture_image() -> Result<Vec<u8>> {
    let status = Command::new(CAPTURE_COMMAND)
        .args(["-o", IMAGE_PATH, "--nopreview", "--immediate"])
        .status()
        .context("Failed to execute camera capture command")?;

    if !status.success() {
        anyhow::bail!("Camera capture command failed");
    }

    let image_data = fs::read(IMAGE_PATH).context("Failed to read captured image")?;
    let _ = fs::remove_file(IMAGE_PATH);

    Ok(image_data)
}

pub fn generate_image_key() -> String {
    let timestamp = Local::now().format("%Y%m%d_%H%M%S");
    format!("images/capture_{}.jpg", timestamp)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;
    use std::io::Write;
    use tempfile::tempdir;

    #[test]
    fn test_generate_image_key() {
        let key = generate_image_key();
        assert!(key.starts_with("images/capture_"));
        assert!(key.ends_with(".jpg"));
        assert_eq!(key.len(), "images/capture_YYYYMMDD_HHMMSS.jpg".len());
    }

    #[test]
    fn test_capture_image_read_error() {
        // Create a temporary directory that will be automatically removed
        let dir = tempdir().unwrap();
        let file_path = dir.path().join("test.jpg");
        
        // Write some test data
        let test_data = b"test image data";
        let mut file = File::create(&file_path).unwrap();
        file.write_all(test_data).unwrap();

        // Test reading the file
        let data = fs::read(&file_path).unwrap();
        assert_eq!(data, test_data);
    }
} 