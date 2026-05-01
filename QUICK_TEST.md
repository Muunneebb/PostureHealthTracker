# Quick Test - Getting Camera Running NOW

**Follow these steps to test if your camera connects and tracks**

## Step 1: Verify Camera Hardware

```bash
# On Raspberry Pi
python3 -c "from picamera2 import Picamera2; print('✓ Camera detected')"
```

Expected: `✓ Camera detected` (no error)

## Step 2: Test Camera Module

```bash
cd /home/pi/Documents/PostureHealthTracker/PostureHealthTracker

python3 -c "
from hardware.src import camera_module
cam = camera_module.CameraModule()
if cam.start():
    print('✓ Camera started successfully')
    cam.stop()
    print('✓ Camera stopped')
else:
    print('✗ Camera failed to start')
"
```

Expected output:
```
✓ Camera started successfully
✓ Camera stopped
```

## Step 3: Test Firebase Connection

```bash
# Check internet
ping -c 2 8.8.8.8

# Check Firebase access
curl -s "https://posturehealthtracker-default-rtdb.firebaseio.com/test.json" | head -c 50
```

Expected: Should not error (404 is OK - means Firebase is reachable)

## Step 4: Run Hardware Loop (5 second test)

```bash
cd /home/pi/Documents/PostureHealthTracker/PostureHealthTracker

timeout 5 python3 hardware/src/main.py
```

Expected output:
```
[Pi] Hardware Booted. Connecting to Firebase...
[Pi] Waiting for camera_command from dashboard...
```

No errors = good!

## Step 5: Test Dashboard

1. Open: https://muunneebb.github.io/PostureHealthTracker/docs/index.html
2. Sign in (create account or use `test@example.com`)
3. Click **"Start Monitoring"**
4. Open browser console (F12 → Console)
5. Look for: `[toggleSession] STARTING session:`

## Step 6: Monitor Pi Output

While dashboard running, on Pi terminal:

```bash
timeout 10 python3 hardware/src/main.py
```

You should see:
```
[Pi] Hardware Booted. Connecting to Firebase...
[Pi] Waiting for camera_command from dashboard...
[Pi] ✓ START command received. Session: session_1234567
[Pi] New session: session_1234567
[Pi] Attempting to start camera...
[Pi] ✓ Camera is ready
```

If you see this → **CAMERA IS WORKING!**

## Step 7: Check Dashboard Updates

Back in browser, you should see:
- Camera preview image appears
- "Camera active" status
- Score bar with position
- Metrics updating (every 2 seconds)

## Troubleshooting

### Step 1 fails: "No module named 'picamera2'"
```bash
pip install picamera2
```

### Step 2 fails: "Camera failed to start"
```bash
# Check if camera is enabled
vcgencmd get_camera

# Output should contain: supported=1 detected=1
# If detected=0, enable in raspi-config:
sudo raspi-config  # Interface Options → Camera → Enable
```

### Step 4 shows "Network Error"
- Network is slow (this is OK - timeouts handle it)
- Or Firebase is unreachable
- Check: `curl -I https://posturehealthtracker-default-rtdb.firebaseio.com`

### Step 6: "✗ Camera failed to start"
- Check Step 2 above
- Ensure no other process using camera
- Reboot: `sudo reboot`

### Dashboard doesn't show "STARTING session"
- Not signed in (should redirect to login)
- Firebase config wrong (check it matches your project)
- Check browser console for errors

### Pi doesn't receive START command
- Firebase rules not configured (see [FIREBASE_SETUP.md](FIREBASE_SETUP.md))
- Dashboard RTDB write failed (browser console will show error)
- Session ID not being sent

## Full End-to-End Test (5 minutes)

```bash
# Terminal 1: Run Pi loop
cd /home/pi/Documents/PostureHealthTracker/PostureHealthTracker
timeout 60 python3 hardware/src/main.py

# Terminal 2: Monitor Firebase writes
watch -n 1 'curl -s "https://posturehealthtracker-default-rtdb.firebaseio.com/live_data.json" | python3 -m json.tool | head -20'
```

Sequence:
1. Pi starts, polls Firebase
2. You click "Start Monitoring" in dashboard
3. Pi receives command: "✓ START command received"
4. Pi starts camera: "✓ Camera is ready"
5. Pi captures frame every 2 seconds
6. Dashboard updates with live camera preview
7. Terminal 2 shows live_data updating
8. You click "Stop Monitoring"
9. Pi sees "STOP command"
10. Session saved to Firestore

## Success Checklist

- [x] Camera hardware detected
- [x] Camera module starts/stops cleanly
- [x] Firebase is reachable  
- [x] Hardware loop runs without errors
- [x] Dashboard shows camera active
- [x] Score bar moves with live data
- [x] Session saved after stop

If all green → **You're ready to go!** 🎉

---

**Next:** See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
