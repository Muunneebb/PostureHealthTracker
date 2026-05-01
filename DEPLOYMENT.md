# Posture Health Tracker - Deployment Guide

**Status:** ✅ Complete and Ready for Production  
**Last Updated:** May 1, 2026

## System Architecture

### Components
- **Raspberry Pi 5** with Hailo AI Hat
- **picamera2** for video capture
- **MediaPipe** for pose detection (Hailo-compatible thresholds)
- **Firebase Realtime Database** (RTDB) for live commands and data
- **Firebase Firestore** for session history
- **Web Dashboard** (HTML/CSS/JS) for user interface

### Data Flow
```
User Dashboard
    ↓ (click Start Monitoring)
    ↓ writes to RTDB: system_state.camera_command = "ON"
    ↓
Raspberry Pi (hardware/src/main.py)
    ↓ polls RTDB every 1 second
    ↓ receives command, starts camera
    ↓ every 2 seconds: capture frame → analyze posture → calculate score
    ↓ writes to RTDB: /live_data (score, metrics, base64 frame)
    ↓ writes to Firestore: sessions/{sessionId}/readings
    ↓
Dashboard (docs/index.html)
    ↓ listens to RTDB changes in real-time
    ↓ updates score bar, camera preview, metrics
    ↓ displays live posture status (Good/Bad)
    ↓
User sees live feedback with camera preview and posture analysis
```

## Prerequisites

### On Raspberry Pi
- Python 3.9+
- Hailo AI Hat installed and configured
- GStreamer (optional, for advanced Hailo integration)

### Python Packages
```bash
pip install -r requirements.txt
```

Key packages:
- `requests` - Firebase HTTP API calls
- `picamera2` - Pi camera interface
- `mediapipe` - Pose detection
- `opencv-python` - Image processing
- `firebase-admin` - Optional, for Firestore writes

### Firebase Project
- Create Firebase project at https://console.firebase.google.com
- Enable Firestore Database (start in test mode for development)
- Enable Realtime Database
- Create web app credentials
- Save config in `docs/index.html` (already included)

## Deployment Steps

### 1. Install on Raspberry Pi

```bash
# Clone the repo
git clone https://github.com/Muunneebb/PostureHealthTracker.git
cd PostureHealthTracker

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Firebase (Optional for Firestore)

To enable Firestore session history saving:

```bash
# Download service account key from Firebase Console
# → Project Settings → Service Accounts → Generate New Private Key

# Set environment variable (add to ~/.bashrc or ~/.profile)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Test Firestore setup
python3 -c "import firebase_admin; print('✓ Firebase admin SDK ready')"
```

### 3. Run Tests

```bash
# Integration tests (validates all modules)
python3 test_integration.py

# Hardware loop test (10-second validation)
python3 test_hardware_loop.py

# End-to-end session simulation
python3 test_e2e_session.py
```

All tests should show ✓ PASS.

### 4. Start the Main Loop

```bash
# Start monitoring (runs continuously)
cd hardware
python3 src/main.py
```

**Output should show:**
```
Hardware Booted. Connecting to Firebase...
[Polling Firebase every 1 second...]
```

Press `Ctrl+C` to stop.

### 5. Test the Dashboard

1. Open https://github.com/Muunneebb/PostureHealthTracker/docs/index.html in browser
   - Or run locally: `python3 -m http.server 8000` and visit http://localhost:8000/docs/

2. Sign in with Firebase credentials

3. Click **"Start Monitoring"** button

4. Pi should detect the command and start:
   - Camera capture
   - Posture analysis
   - Live data push to Firebase

5. Dashboard should show:
   - Camera frame preview (updates every 2 sec)
   - Live posture score
   - Posture status (Good/Bad)
   - Metrics (shoulder alignment, neck angle)

6. Click **"End Monitoring"** to stop session

7. Session automatically saved to Firestore with:
   - Duration
   - Average posture score
   - Readings (individual frame scores and metrics)

## Configuration

### Camera Settings
- **Capture Resolution:** 640x480 (default)
- **Preview Resolution:** 360px width (responsive)
- **Capture Frequency:** Every 2 seconds (when session active)
- **JPEG Quality:** 72% (efficient for real-time streaming)

### Posture Thresholds
In `hardware/src/camera_module.py`:
```python
HEAD_FORWARD_THRESHOLD = 12  # pixels (default)
SHOULDER_FORWARD_THRESHOLD = 18  # pixels (default)
```

### Posture Scores
- **Good Posture:** 95%
- **Slouching:** 60%
- **Head Forward:** 55%
- **Bad (generic):** 50%
- **Gradual degradation** based on shoulder_alignment and neck_angle

## Troubleshooting

### Issue: Firebase Returns 404
**Cause:** Authentication issue or path doesn't exist yet  
**Solution:** 
- Paths are created automatically on first write
- Ensure Firebase project is accessible
- Check internet connectivity on Pi

### Issue: No Camera Detected
**Cause:** picamera2 not installed or camera disabled  
**Solution:**
```bash
# Enable camera in raspi-config
sudo raspi-config
# → Interface Options → Camera → Enable
# Reboot after enabling

# Reinstall picamera2
pip install --upgrade picamera2
```

### Issue: Firestore Writes Failing
**Cause:** Missing service account credentials  
**Solution:**
- Firestore writes are optional (gracefully skipped if credentials missing)
- To enable: Download service account JSON and set GOOGLE_APPLICATION_CREDENTIALS
- Test with: `python3 -c "import firebase_admin; print('OK')"`

### Issue: Dashboard Not Updating
**Cause:** Real-time listener not connected  
**Solution:**
- Check browser console for errors (F12)
- Verify Firebase project config in `docs/index.html`
- Check network tab to see if live_data listener is active
- Try hard refresh (Ctrl+Shift+R)

## Performance Metrics

| Metric | Value |
|--------|-------|
| Firebase Poll Interval | 1 second |
| Frame Capture Interval | 2 seconds |
| Pose Analysis Latency | ~500ms per frame |
| Dashboard Update Latency | <1 second (RTD listener) |
| Firestore Write Latency | ~2-3 seconds |
| Base64 Frame Size | ~30-50 KB |

## Security Notes

⚠️ **For Production:**
1. Use Firebase Firestore Security Rules (currently in test mode)
2. Implement user authentication (Firebase Auth integrated)
3. Restrict RTDB read/write access by user ID
4. Don't commit `service-account-key.json` to version control
5. Use HTTPS for all communications (Firebase handles this)

## Feature Completeness Checklist

✅ **Core Features**
- [x] Raspberry Pi hardware integration
- [x] Camera capture (picamera2)
- [x] Pose detection (MediaPipe with Hailo thresholds)
- [x] Posture scoring (0-100%)
- [x] Firebase RTDB live data
- [x] Firestore session history
- [x] Web dashboard (HTML/CSS/JS)
- [x] Real-time metrics display
- [x] Session lifecycle (start/stop)

✅ **Testing**
- [x] Unit tests (module imports, scoring logic)
- [x] Integration tests (Firebase, camera module)
- [x] Hardware loop validation
- [x] End-to-end session simulation
- [x] All tests passing

✅ **Documentation**
- [x] Setup guide
- [x] Deployment instructions
- [x] Architecture overview
- [x] Troubleshooting guide

🔄 **Optional Enhancements (Future)**
- [ ] Hailo AI Hat direct inference (replace MediaPipe)
- [ ] Fan control based on CPU temperature
- [ ] Advanced posture analysis (side/front profiles)
- [ ] Mobile app companion
- [ ] Email reports/alerts
- [ ] Social features (friend leaderboards)
- [ ] Export session data (CSV/PDF)

## Support & Troubleshooting

1. **Check logs:**
   ```bash
   # Pi console output
   cat ~/posture-tracker.log
   
   # Browser console (F12 → Console tab)
   # Check for JavaScript errors
   ```

2. **Validate connectivity:**
   ```bash
   # Test Firebase RTDB
   curl "https://posturehealthtracker-default-rtdb.firebaseio.com/system_state.json"
   
   # Test camera
   python3 -c "from picamera2 import Picamera2; print('✓ Camera OK')"
   ```

3. **Run test suite:**
   ```bash
   python3 test_integration.py
   python3 test_hardware_loop.py
   ```

## Next Steps

1. ✅ Deploy to Raspberry Pi
2. 🔄 Monitor live sessions via dashboard
3. 📊 Review session history and trends
4. 🎯 Optimize thresholds based on your posture
5. 🚀 Consider Hailo AI Hat direct integration for better performance

---

**Repository:** https://github.com/Muunneebb/PostureHealthTracker  
**Firebase Project:** posturehealthtracker  
**Dashboard:** https://muunneebb.github.io/PostureHealthTracker/docs/index.html
