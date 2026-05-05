# PostureHealthTracker Hardware Service Setup

This guide explains how to set up the hardware monitoring loop to auto-start on the Raspberry Pi using systemd.

## Overview

The hardware loop (`hardware/src/main.py`) continuously:
- Polls Firebase for monitoring commands
- Manages the camera pipeline (Hailo AI or Picamera2)
- Captures and analyzes posture frames
- Pushes real-time data to Firebase

By installing it as a systemd service, it will automatically start on boot and restart if it crashes.

## Installation Steps

### 1. Copy the service file to systemd directory

```bash
sudo cp hardware/systemd/posturehealthtracker-hardware.service /etc/systemd/system/
```

### 2. Reload systemd daemon

```bash
sudo systemctl daemon-reload
```

### 3. Enable the service to auto-start on boot

```bash
sudo systemctl enable posturehealthtracker-hardware.service
```

### 4. Start the service immediately

```bash
sudo systemctl start posturehealthtracker-hardware.service
```

## Common Commands

### Check service status

```bash
sudo systemctl status posturehealthtracker-hardware.service
```

### View real-time logs

```bash
sudo journalctl -u posturehealthtracker-hardware.service -f
```

### View last 100 lines of logs

```bash
sudo journalctl -u posturehealthtracker-hardware.service -n 100
```

### Stop the service

```bash
sudo systemctl stop posturehealthtracker-hardware.service
```

### Restart the service

```bash
sudo systemctl restart posturehealthtracker-hardware.service
```

### Disable auto-start (but keep installed)

```bash
sudo systemctl disable posturehealthtracker-hardware.service
```

### View debug logs from the hardware loop

The hardware loop also writes detailed logs to:
```bash
tail -f /tmp/posturehealthtracker_main.log
```

And Hailo pipeline logs (if applicable):
```bash
tail -f /tmp/posturehealthtracker_hailo.log
```

## Troubleshooting

### Service won't start

1. Check logs:
   ```bash
   sudo journalctl -u posturehealthtracker-hardware.service -n 50
   tail /tmp/posturehealthtracker_main.log
   ```

2. Verify file paths:
   - Service expects project at: `/home/pi/Documents/PostureHealthTracker/PostureHealthTracker`
   - If your project is elsewhere, edit `/etc/systemd/system/posturehealthtracker-hardware.service` and update `WorkingDirectory`

3. Check permissions:
   - Ensure `pi` user owns the project directory
   - Camera device access may require additional groups (usually automatic on Pi OS)

### Python dependencies missing

If the service logs show import errors, install missing packages:

```bash
cd /home/pi/Documents/PostureHealthTracker/PostureHealthTracker
python3 -m pip install -r requirements.txt
```

### Firebase connectivity issues

Check that the Pi can reach Firebase:

```bash
curl -I https://posturehealthtracker-default-rtdb.europe-west1.firebasedatabase.app
```

If the connection fails, check:
- Network connectivity: `ping 8.8.8.8`
- DNS resolution: `nslookup posturehealthtracker-default-rtdb.europe-west1.firebasedatabase.app`

### Camera not detected

Check if camera device is available:

```bash
ls -la /dev/video* || echo "No video devices found"
```

On Raspberry Pi, also verify camera is enabled in `raspi-config`.

## Manual Testing Before Installing Service

To test the hardware loop without systemd:

```bash
cd /home/pi/Documents/PostureHealthTracker/PostureHealthTracker
python3 hardware/src/main.py
```

Watch the output for connection messages and any errors. Press `Ctrl+C` to stop.

## What the Service Does

1. **Starts automatically** on Pi boot after network is available
2. **Restarts automatically** if the process crashes (with 10-second delay between restarts)
3. **Logs to systemd journal** for central logging
4. **Also writes detailed logs** to `/tmp/posturehealthtracker_main.log` and `/tmp/posturehealthtracker_hailo.log`
5. **Runs as user `pi`** with appropriate permissions

## Uninstallation

To completely remove the service:

```bash
sudo systemctl disable posturehealthtracker-hardware.service
sudo systemctl stop posturehealthtracker-hardware.service
sudo rm /etc/systemd/system/posturehealthtracker-hardware.service
sudo systemctl daemon-reload
```

---

For more details on the hardware loop, see [README.md](../../README.md) and [INTEGRATION_SUMMARY.md](../../INTEGRATION_SUMMARY.md).
