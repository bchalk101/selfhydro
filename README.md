# SelfHydro

An automated hydroponics system that monitors and manages plant growth. The system uses:
- Computer vision to track growth rates and plant health
- Sensor arrays for environmental monitoring (temperature, humidity, pH, EC)
- Automated harvesting for cherry tomatoes
- Machine learning for yield prediction and optimization

## Project Structure

```
selfhydro/
├── Cargo.toml           # Workspace manifest
├── crates/             
│   └── camera/         # Camera monitoring service
├── deploy/
│   └── selfhydro.service  # Systemd service
└── deploy.sh           # Deployment script
```

## Prerequisites

- Raspberry Pi 5 or newer
- Camera Module 3
- Rust toolchain
- Google Cloud Platform account
- SSH access to Raspberry Pi

## SSH Setup

1. Generate SSH key pair (if you don't have one):
   ```bash
   # Generate a new ED25519 key pair
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. Copy your public key to the Raspberry Pi:
   ```bash
   # Replace 'base@selfhydro.local' with your Pi's username and hostname
   ssh-copy-id base@selfhydro.local
   ```

3. Test the connection:
   ```bash
   # Should connect without password
   ssh base@selfhydro.local
   ```

4. Optional: Configure SSH client for easier access:
   ```bash
   # Add to ~/.ssh/config
   cat >> ~/.ssh/config << EOL
   Host selfhydro
       HostName selfhydro.local
       User base
       IdentityFile ~/.ssh/id_ed25519
   EOL
   
   # Now you can connect with just:
   ssh selfhydro
   ```

## Development

     ```bash
# Build all crates
cargo build --workspace

# Run tests
cargo test --workspace

# Build for release
cargo build --release --workspace
   ```

## Deployment

1. Configure environment:
   ```bash
   # Create .env file
   cat > .env << EOL
   GCS_BUCKET=your-bucket-name
   EOL

   # Add GCP credentials
   cp /path/to/credentials.json .
   ```

2. Deploy to Raspberry Pi:
   ```bash
   ./deploy.sh
   ```

The deployment script will:
- Build all components in release mode
- Copy binaries and configuration to the Pi
- Set up and start the systemd service

## Monitoring

```bash
# Check service status
sudo systemctl status selfhydro

# View logs
journalctl -u selfhydro -f
```

## Components

### Camera Service (`crates/camera`)
- Captures images every 30 minutes
- Uploads to Google Cloud Storage
- Tracks plant growth over time

### Planned Components
- Environmental monitoring (temp, humidity, pH, EC)
- Automated harvesting system
- Growth analysis and yield prediction
- Nutrient management

## Troubleshooting

### Camera Issues
   ```bash
# Enable camera interface
sudo raspi-config  # Navigate to Interface Options > Camera

# Test camera
libcamera-still -o test.jpg
```

### Google Cloud Storage
- Verify `credentials.json` exists and has correct permissions
- Test GCS access:
   ```bash
  GOOGLE_APPLICATION_CREDENTIALS=./credentials.json gsutil ls gs://your-bucket-name
  ```

### Service Issues
```bash
# Check service status and logs
sudo systemctl status selfhydro
journalctl -u selfhydro -f

# Restart service
sudo systemctl restart selfhydro
``` 