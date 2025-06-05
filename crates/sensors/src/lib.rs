use anyhow::Result;
use rppal::i2c::I2c;
use serde::Serialize;
use chrono::{DateTime, Utc};
use std::thread;
use std::time::Duration;

const BME280_ADDR: u16 = 0x76; // Default I2C address for BME280
const BME280_CHIP_ID: u8 = 0x60;

// Register addresses
const BME280_CHIP_ID_REG: u8 = 0xD0;
const BME280_RESET_REG: u8 = 0xE0;
const BME280_CTRL_HUM_REG: u8 = 0xF2;
const BME280_CTRL_MEAS_REG: u8 = 0xF4;
const BME280_CONFIG_REG: u8 = 0xF5;
const BME280_PRESS_MSB_REG: u8 = 0xF7;
const BME280_CALIB_START: u8 = 0x88;
const BME280_CALIB_HUM_START: u8 = 0xE1;
const BME280_DIG_H1_REG: u8 = 0xA1;  // dig_H1 is stored separately

#[derive(Debug, Serialize, Clone)]
pub struct SensorReading {
    pub temperature: f64,
    pub humidity: f64,
    pub pressure: f64,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug)]
struct CalibrationData {
    dig_t1: u16,
    dig_t2: i16,
    dig_t3: i16,
    dig_p1: u16,
    dig_p2: i16,
    dig_p3: i16,
    dig_p4: i16,
    dig_p5: i16,
    dig_p6: i16,
    dig_p7: i16,
    dig_p8: i16,
    dig_p9: i16,
    dig_h1: u8,
    dig_h2: i16,
    dig_h3: u8,
    dig_h4: i16,
    dig_h5: i16,
    dig_h6: i8,
    t_fine: i32,
}

pub struct BME280Sensor {
    i2c: I2c,
    calib: CalibrationData,
}

impl BME280Sensor {
    pub fn new() -> Result<Self> {
        let mut i2c = I2c::new()?;
        i2c.set_slave_address(BME280_ADDR)?;
        
        // Check chip ID
        let mut chip_id_buf = [0u8; 1];
        i2c.write_read(&[BME280_CHIP_ID_REG], &mut chip_id_buf)?;
        let chip_id = chip_id_buf[0];
        if chip_id != BME280_CHIP_ID {
            return Err(anyhow::anyhow!("Invalid chip ID: expected 0x{:02X}, got 0x{:02X}", BME280_CHIP_ID, chip_id));
        }

        // Reset device
        i2c.write(&[BME280_RESET_REG, 0xB6])?;
        thread::sleep(Duration::from_millis(100));

        // Read temperature and pressure calibration data
        let mut calib_data = [0u8; 26];
        i2c.write_read(&[BME280_CALIB_START], &mut calib_data)?;
        
        // Read dig_H1 separately (it's at 0xA1)
        let mut dig_h1_buf = [0u8; 1];
        i2c.write_read(&[BME280_DIG_H1_REG], &mut dig_h1_buf)?;
        let dig_h1 = dig_h1_buf[0];
        
        // Read humidity calibration data (dig_H2-dig_H6 at 0xE1-0xE7)
        let mut hum_calib_data = [0u8; 7];
        i2c.write_read(&[BME280_CALIB_HUM_START], &mut hum_calib_data)?;

        // Parse humidity calibration parameters according to datasheet
        let dig_h2 = i16::from_le_bytes([hum_calib_data[0], hum_calib_data[1]]);
        let dig_h3 = hum_calib_data[2];
        
        // dig_H4 = (E4[7:4] << 4) | (E5[3:0])
        // hum_calib_data[3] = E4, hum_calib_data[4] = E5
        let dig_h4 = ((hum_calib_data[3] as i16) << 4) | ((hum_calib_data[4] & 0x0F) as i16);
        // Convert to signed 12-bit value
        let dig_h4 = if dig_h4 > 2047 { dig_h4 - 4096 } else { dig_h4 };
        
        // dig_H5 = (E6[7:4] << 4) | (E5[7:4])
        // hum_calib_data[4] = E5, hum_calib_data[5] = E6
        let dig_h5 = ((hum_calib_data[5] as i16) << 4) | ((hum_calib_data[4] >> 4) as i16);
        // Convert to signed 12-bit value
        let dig_h5 = if dig_h5 > 2047 { dig_h5 - 4096 } else { dig_h5 };
        
        let dig_h6 = hum_calib_data[6] as i8;

        let calib = CalibrationData {
            dig_t1: u16::from_le_bytes([calib_data[0], calib_data[1]]),
            dig_t2: i16::from_le_bytes([calib_data[2], calib_data[3]]),
            dig_t3: i16::from_le_bytes([calib_data[4], calib_data[5]]),
            dig_p1: u16::from_le_bytes([calib_data[6], calib_data[7]]),
            dig_p2: i16::from_le_bytes([calib_data[8], calib_data[9]]),
            dig_p3: i16::from_le_bytes([calib_data[10], calib_data[11]]),
            dig_p4: i16::from_le_bytes([calib_data[12], calib_data[13]]),
            dig_p5: i16::from_le_bytes([calib_data[14], calib_data[15]]),
            dig_p6: i16::from_le_bytes([calib_data[16], calib_data[17]]),
            dig_p7: i16::from_le_bytes([calib_data[18], calib_data[19]]),
            dig_p8: i16::from_le_bytes([calib_data[20], calib_data[21]]),
            dig_p9: i16::from_le_bytes([calib_data[22], calib_data[23]]),
            dig_h1,
            dig_h2,
            dig_h3,
            dig_h4,
            dig_h5,
            dig_h6,
            t_fine: 0,
        };

        // Configure sensor - IMPORTANT: Order matters!
        // 1. Set humidity oversampling first
        i2c.write(&[BME280_CTRL_HUM_REG, 0x01])?; // Humidity oversampling x1
        
        // 2. Set temperature and pressure oversampling, and mode
        // This write triggers the humidity setting to take effect
        i2c.write(&[BME280_CTRL_MEAS_REG, 0x27])?; // temp and pressure oversampling x1, normal mode
        
        // 3. Configure filter
        i2c.write(&[BME280_CONFIG_REG, 0x00])?; // Filter off
        
        // Wait for sensor to stabilize
        thread::sleep(Duration::from_millis(100));

        println!("BME280 initialized with calibration data:");
        println!("dig_H1: {}, dig_H2: {}, dig_H3: {}", calib.dig_h1, calib.dig_h2, calib.dig_h3);
        println!("dig_H4: {}, dig_H5: {}, dig_H6: {}", calib.dig_h4, calib.dig_h5, calib.dig_h6);

        Ok(Self { i2c, calib })
    }

    pub fn read(&mut self) -> Result<SensorReading> {
        let mut data = [0u8; 8];
        self.i2c.write_read(&[BME280_PRESS_MSB_REG], &mut data)?;

        let pressure_raw = ((data[0] as u32) << 12) | ((data[1] as u32) << 4) | ((data[2] as u32) >> 4);
        let temp_raw = ((data[3] as u32) << 12) | ((data[4] as u32) << 4) | ((data[5] as u32) >> 4);
        let humidity_raw = ((data[6] as u32) << 8) | (data[7] as u32);

        println!("Raw values - Temp: {}, Pressure: {}, Humidity: {}", temp_raw, pressure_raw, humidity_raw);

        let temp = self.compensate_temperature(temp_raw);
        let pressure = self.compensate_pressure(pressure_raw);
        let humidity = self.compensate_humidity(humidity_raw);

        println!("Compensated values - Temp: {:.2}°C, Pressure: {:.2} Pa, Humidity: {:.2}%", temp, pressure, humidity);

        Ok(SensorReading {
            temperature: temp,
            pressure: pressure,
            humidity: humidity,
            timestamp: Utc::now(),
        })
    }

    fn compensate_temperature(&mut self, raw_temp: u32) -> f64 {
        let var1 = ((raw_temp as f64) / 16384.0 - (self.calib.dig_t1 as f64) / 1024.0) 
            * (self.calib.dig_t2 as f64);
        let var2 = ((raw_temp as f64) / 131072.0 - (self.calib.dig_t1 as f64) / 8192.0) 
            * ((raw_temp as f64) / 131072.0 - (self.calib.dig_t1 as f64) / 8192.0)
            * (self.calib.dig_t3 as f64);
        
        self.calib.t_fine = (var1 + var2) as i32;
        
        (var1 + var2) / 5120.0
    }

    fn compensate_pressure(&self, raw_pressure: u32) -> f64 {
        let var1 = (self.calib.t_fine as f64 / 2.0) - 64000.0;
        let var2 = var1 * var1 * (self.calib.dig_p6 as f64) / 32768.0;
        let var2 = var2 + var1 * (self.calib.dig_p5 as f64) * 2.0;
        let var2 = (var2 / 4.0) + ((self.calib.dig_p4 as f64) * 65536.0);
        let var1 = ((self.calib.dig_p3 as f64) * var1 * var1 / 524288.0 
            + (self.calib.dig_p2 as f64) * var1) / 524288.0;
        let var1 = (1.0 + var1 / 32768.0) * (self.calib.dig_p1 as f64);

        if var1 == 0.0 {
            return 0.0;
        }

        let p = 1048576.0 - (raw_pressure as f64);
        let p = ((p - (var2 / 4096.0)) * 6250.0) / var1;
        let var1 = (self.calib.dig_p9 as f64) * p * p / 2147483648.0;
        let var2 = p * (self.calib.dig_p8 as f64) / 32768.0;
        
        p + (var1 + var2 + (self.calib.dig_p7 as f64)) / 16.0
    }

    fn compensate_humidity(&self, raw_humidity: u32) -> f64 {
        let temp_scaled = (self.calib.t_fine as f64) - 76800.0;
        
        let mut h = raw_humidity as f64;
        
        // First term calculation
        let h4_term = (self.calib.dig_h4 as f64) * 64.0;
        let h5_term = (self.calib.dig_h5 as f64) * temp_scaled / 16384.0;
        h -= h4_term + h5_term;
        
        // Second term calculation
        let h2_term = (self.calib.dig_h2 as f64) / 65536.0;
        let h6_term = 1.0 + (self.calib.dig_h6 as f64) * temp_scaled / 67108864.0;
        let h3_term = 1.0 + (self.calib.dig_h3 as f64) * temp_scaled / 67108864.0;
        
        h *= h2_term * h6_term * h3_term;
        
        // Final adjustment
        let h1_term = 1.0 - (self.calib.dig_h1 as f64) / 524288.0 * h;
        h *= h1_term;
        
        // Clamp to valid range
        h = h.max(0.0).min(100.0);
        
        h
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sensor_reading_creation() {
        let reading = SensorReading {
            temperature: 25.5,
            humidity: 45.7,
            pressure: 101325.0,
            timestamp: Utc::now(),
        };

        assert_eq!(reading.temperature, 25.5);
        assert_eq!(reading.humidity, 45.7);
        assert_eq!(reading.pressure, 101325.0);
    }

    #[test]
    fn test_temperature_compensation() {
        let calib = CalibrationData {
            dig_t1: 27504,
            dig_t2: 26435,
            dig_t3: -1000,
            dig_p1: 36477,
            dig_p2: -10685,
            dig_p3: 3024,
            dig_p4: 2855,
            dig_p5: 140,
            dig_p6: -7,
            dig_p7: 15500,
            dig_p8: -14600,
            dig_p9: 6000,
            dig_h1: 75,
            dig_h2: 374,
            dig_h3: 0,
            dig_h4: 250,
            dig_h5: 50,
            dig_h6: 30,
            t_fine: 0,
        };

        let mut sensor = BME280Sensor {
            i2c: I2c::new().unwrap(),
            calib,
        };

        // Test with known raw value that should give around 25°C
        let temp = sensor.compensate_temperature(519888);
        assert!((temp - 25.0).abs() < 1.0, "Temperature: {}", temp); // Within 1 degree of expected
    }

    #[test]
    fn test_humidity_compensation() {
        let calib = CalibrationData {
            dig_t1: 27504,
            dig_t2: 26435,
            dig_t3: -1000,
            dig_p1: 36477,
            dig_p2: -10685,
            dig_p3: 3024,
            dig_p4: 2855,
            dig_p5: 140,
            dig_p6: -7,
            dig_p7: 15500,
            dig_p8: -14600,
            dig_p9: 6000,
            dig_h1: 75,
            dig_h2: 357,
            dig_h3: 0,
            dig_h4: 332,
            dig_h5: 0,
            dig_h6: 30,
            t_fine: 117743,
        };

        let sensor = BME280Sensor {
            i2c: I2c::new().unwrap(),
            calib,
        };

        // Test with a raw humidity value that should give around 50% RH
        let raw_humidity = 32768; // Adjusted to match the calibration values
        let humidity = sensor.compensate_humidity(raw_humidity);
        
        println!("Raw humidity: {}", raw_humidity);
        println!("Calibration values:");
        println!("  dig_h1: {}", sensor.calib.dig_h1);
        println!("  dig_h2: {}", sensor.calib.dig_h2);
        println!("  dig_h3: {}", sensor.calib.dig_h3);
        println!("  dig_h4: {}", sensor.calib.dig_h4);
        println!("  dig_h5: {}", sensor.calib.dig_h5);
        println!("  dig_h6: {}", sensor.calib.dig_h6);
        println!("  t_fine: {}", sensor.calib.t_fine);
        println!("Compensated humidity: {}", humidity);

        assert!(humidity >= 0.0 && humidity <= 100.0, "Humidity {} is outside valid range 0-100%", humidity);
        assert!((humidity - 50.0).abs() < 20.0, "Humidity {} is not within expected range of 50% ± 20%", humidity);
    }

    #[test]
    fn test_pressure_compensation() {
        let calib = CalibrationData {
            dig_t1: 27504,
            dig_t2: 26435,
            dig_t3: -1000,
            dig_p1: 36477,
            dig_p2: -10685,
            dig_p3: 3024,
            dig_p4: 2855,
            dig_p5: 140,
            dig_p6: -7,
            dig_p7: 15500,
            dig_p8: -14600,
            dig_p9: 6000,
            dig_h1: 75,
            dig_h2: 374,
            dig_h3: 0,
            dig_h4: 250,
            dig_h5: 50,
            dig_h6: 30,
            t_fine: 100000, // Set a reasonable t_fine value
        };

        let sensor = BME280Sensor {
            i2c: I2c::new().unwrap(),
            calib,
        };

        // Test with known raw value that should give around 1000 hPa
        let pressure = sensor.compensate_pressure(415148);
        assert!(pressure > 95000.0 && pressure < 105000.0); // Within reasonable atmospheric pressure range
    }
} 