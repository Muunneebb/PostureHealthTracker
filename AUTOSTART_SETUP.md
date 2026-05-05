# PostureHealthTracker Auto-Start Setup Guide

## Enable Auto-Start on Pi Boot

The Pi hardware loop can now start automatically on boot using systemd. Follow these steps:

### 1. Enable the Systemd Service

Run these commands on your Raspberry Pi:

```bash
# Enable the service to start on boot
systemctl --user enable posturehealthtracker.service

# Optionally: Check if the service is enabled
systemctl --user status posturehealthtracker.service
```

### 2. Enable User Services on Boot (Important!)

For user-level systemd services to start on boot, you need to enable lingering:

```bash
# Enable lingering for the pi user (allows services to run at boot without login)
sudo loginctl enable-linger pi

# Verify it's enabled
sudo loginctl show-user pi | grep Linger
```

### 3. Start the Service Now

```bash
# Start the service immediately
systemctl --user start posturehealthtracker.service

# Check status
systemctl --user status posturehealthtracker.service

# View logs
journalctl --user -u posturehealthtracker.service -f
```

### 4. Verify on Next Boot

After enabling, the service will:
- Automatically start when the Pi boots
- Automatically restart if it crashes (up to 5 retries with 5-second delays)
- Log all output to systemd journal (check with `journalctl`)

## Optional: Manual Start (If Not Using Auto-Start)

If you prefer to start the service manually, use:

```bash
cd ~/Documents/PostureHealthTracker/PostureHealthTracker/hardware
python3 src/main.py
```

## Service Details

- **Service File**: `~/.config/systemd/user/posturehealthtracker.service`
- **Working Directory**: `/home/pi/Documents/PostureHealthTracker/PostureHealthTracker/hardware`
- **Environment Variables**: 
  - `PYTHONUNBUFFERED=1` (unbuffered Python output)
  - `HAILO_EXAMPLES_DIR=/home/pi/hailo-rpi5-examples`
- **Restart Policy**: Always restart on failure (5-second delay between restarts)

## Monitoring the Service

View live logs:
```bash
journalctl --user -u posturehealthtracker.service -f
```

View recent logs:
```bash
journalctl --user -u posturehealthtracker.service -n 50
```

Check service is running:
```bash
systemctl --user is-active posturehealthtracker.service
```

## Troubleshooting

If the service fails to start:

1. **Check logs**: `journalctl --user -u posturehealthtracker.service`
2. **Verify file exists**: `ls ~/Documents/PostureHealthTracker/PostureHealthTracker/hardware/src/main.py`
3. **Manually test**: `python3 ~/Documents/PostureHealthTracker/PostureHealthTracker/hardware/src/main.py`
4. **Check lingering**: `sudo loginctl show-user pi | grep Linger` (should be `Linger=yes`)

## Stopping the Service

```bash
systemctl --user stop posturehealthtracker.service
```

## Disabling Auto-Start

If you want to disable auto-start:

```bash
systemctl --user disable posturehealthtracker.service
```

Note: The service will no longer start automatically on boot, but the systemd file will remain.
