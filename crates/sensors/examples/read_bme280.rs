use anyhow::Result;
use sensors::BME280Sensor;
use std::{thread, time::Duration};

fn main() -> Result<()> {
    // Create a new BME280 sensor instance
    println!("Initializing BME280 sensor...");
    let mut sensor = BME280Sensor::new()?;
    
    println!("Starting continuous reading...");
    println!("Press Ctrl+C to exit");
    
    // Continuously read sensor data every second
    loop {
        match sensor.read() {
            Ok(reading) => {
                println!("\nTimestamp: {}", reading.timestamp);
                println!("Temperature: {:.2}°C", reading.temperature);
                println!("Pressure: {:.1} hPa", reading.pressure / 100.0); // Convert Pa to hPa
                println!("Humidity: {:.1}%", reading.humidity);
            }
            Err(e) => {
                eprintln!("Error reading sensor: {}", e);
            }
        }
        
        // Wait for a second before next reading
        thread::sleep(Duration::from_secs(1));
    }
} 