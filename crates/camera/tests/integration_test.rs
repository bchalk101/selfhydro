use selfhydro_camera::{capture_image, generate_image_key};
use std::path::Path;

#[test]
fn test_image_key_format() {
    let key = generate_image_key();
    let path = Path::new(&key);
    
    assert!(path.is_relative());
    assert_eq!(path.extension().unwrap(), "jpg");
    assert!(path.to_string_lossy().contains("images/capture_"));
}

#[test]
#[cfg(target_os = "linux")]
fn test_camera_integration() {
    // This test only runs on Linux (Raspberry Pi)
    // and when the camera is available
    if Path::new("/dev/video0").exists() {
        let result = capture_image();
        assert!(result.is_ok());
        assert!(!result.unwrap().is_empty());
    }
} 