use anyhow::Result;
use sensors::BME280Sensor;
use std::thread;
use std::time::Duration;

#[test]
fn test_sensor_initialization() -> Result<()> {
    let _sensor = BME280Sensor::new()?;
    Ok(())
}

#[test]
fn test_multiple_readings() -> Result<()> {
    let mut sensor = BME280Sensor::new()?;
    
    // Take 3 readings with small delays
    for _ in 0..3 {
        let reading = sensor.read()?;
        
        // Check if readings are within reasonable ranges
        assert!(reading.temperature >= -40.0 && reading.temperature <= 85.0,
                "Temperature out of range: {}", reading.temperature);
        
        assert!(reading.humidity >= 0.0 && reading.humidity <= 100.0,
                "Humidity out of range: {}", reading.humidity);
        
        // Typical atmospheric pressure range at sea level (approximately)
        assert!(reading.pressure >= 90000.0 && reading.pressure <= 110000.0,
                "Pressure out of range: {}", reading.pressure);
        
        thread::sleep(Duration::from_millis(100));
    }
    
    Ok(())
}

#[test]
fn test_reading_stability() -> Result<()> {
    let mut sensor = BME280Sensor::new()?;
    
    // Take two consecutive readings
    let reading1 = sensor.read()?;
    thread::sleep(Duration::from_millis(100));
    let reading2 = sensor.read()?;
    
    // Check that consecutive readings don't differ too much
    // (assuming stable environment during test)
    assert!((reading1.temperature - reading2.temperature).abs() < 1.0,
            "Temperature changed too rapidly");
    
    assert!((reading1.humidity - reading2.humidity).abs() < 5.0,
            "Humidity changed too rapidly");
    
    assert!((reading1.pressure - reading2.pressure).abs() < 100.0,
            "Pressure changed too rapidly");
    
    Ok(())
}

// This test is ignored by default as it requires manual verification
#[test]
#[ignore]
fn test_sensor_accuracy() -> Result<()> {
    let mut sensor = BME280Sensor::new()?;
    let reading = sensor.read()?;
    
    // These values should be adjusted based on known good values
    // from a calibrated reference sensor
    const EXPECTED_TEMP: f64 = 25.0;
    const EXPECTED_HUMIDITY: f64 = 45.0;
    const EXPECTED_PRESSURE: f64 = 101325.0;
    
    const TEMP_TOLERANCE: f64 = 1.0;
    const HUMIDITY_TOLERANCE: f64 = 3.0;
    const PRESSURE_TOLERANCE: f64 = 100.0;
    
    assert!((reading.temperature - EXPECTED_TEMP).abs() < TEMP_TOLERANCE,
            "Temperature accuracy out of tolerance");
    
    assert!((reading.humidity - EXPECTED_HUMIDITY).abs() < HUMIDITY_TOLERANCE,
            "Humidity accuracy out of tolerance");
    
    assert!((reading.pressure - EXPECTED_PRESSURE).abs() < PRESSURE_TOLERANCE,
            "Pressure accuracy out of tolerance");
    
    Ok(())
} 