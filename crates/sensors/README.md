# Sensors

This crate provides implementations for various sensors, including the BME280 temperature, humidity, and pressure sensor.

## BME280 Sensor

The BME280 sensor implementation provides a simple interface to read temperature, humidity, and pressure data using I2C communication.

### Hardware Setup

1. Connect the BME280 sensor to your Raspberry Pi:
   - VCC → 3.3V
   - GND → Ground
   - SCL → I2C SCL (GPIO 3, physical pin 5)
   - SDA → I2C SDA (GPIO 2, physical pin 3)

2. Enable I2C on your Raspberry Pi:
   ```bash
   sudo raspi-config
   # Navigate to Interface Options → I2C → Enable
   ```

3. Install I2C tools (optional but recommended for debugging):
   ```bash
   sudo apt-get install i2c-tools
   ```

### Usage

Add this to your `Cargo.toml`:

```toml
[dependencies]
sensors = { path = "path/to/sensors" }
```

Basic usage example:

```rust
use sensors::BME280Sensor;

fn main() -> anyhow::Result<()> {
    let mut sensor = BME280Sensor::new()?;
    let reading = sensor.read()?;
    
    println!("Temperature: {:.2}°C", reading.temperature);
    println!("Pressure: {:.1} hPa", reading.pressure / 100.0);
    println!("Humidity: {:.1}%", reading.humidity);
    
    Ok(())
}
```

### Running the Example

The crate includes an example that continuously reads and displays sensor data:

```bash
# From the sensors directory
cargo run --example read_bme280
```

### Testing

The crate includes both unit tests and integration tests:

#### Running Tests

```bash
# Run all tests
cargo test

# Run all tests with output
cargo test -- --nocapture

# Run specific test
cargo test test_name

# Run ignored tests
cargo test -- --ignored
```

#### Test Categories

1. Unit Tests
   - Compensation algorithm validation
   - Data structure tests
   - Value range checks

2. Integration Tests
   - Sensor initialization
   - Multiple reading stability
   - Value range validation
   - Accuracy verification (ignored by default)

#### Manual Accuracy Testing

The accuracy test is marked as `ignored` by default as it requires manual verification:

1. Obtain readings from a calibrated reference sensor
2. Update the expected values in `tests/bme280_integration.rs`
3. Run the ignored test:
   ```bash
   cargo test test_sensor_accuracy -- --ignored
   ```

### Troubleshooting

1. If you get a "Permission denied" error:
   ```bash
   sudo usermod -aG i2c $USER
   # Log out and back in for changes to take effect
   ```

2. To verify the sensor is detected:
   ```bash
   i2cdetect -y 1
   ```
   You should see the device at address 0x76 (or 0x77 if you've connected the SDO pin to VCC).

3. If readings seem incorrect:
   - Verify proper power supply (3.3V)
   - Check I2C connections
   - Ensure proper grounding
   - Try reducing the I2C clock speed if using long wires 