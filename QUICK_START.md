# 🚀 Quick Start - Auto-Start & Camera Optimization

All improvements are ready! Here's what you need to do:

## Step 1: Enable Auto-Start (One-Time Setup)

Run these commands on your Raspberry Pi:

```bash
# Enable the service to start automatically on boot
systemctl --user enable posturehealthtracker.service

# Enable user-level services to run at boot
sudo loginctl enable-linger pi

# Start the service now
systemctl --user start posturehealthtracker.service
```

That's it! The Pi will now:
- ✅ Start the hardware loop automatically when it boots
- ✅ Automatically restart if it crashes
- ✅ Run in the background without needing manual intervention

## Step 2: Check Status

```bash
# View if the service is running
systemctl --user status posturehealthtracker.service

# View live logs
journalctl --user -u posturehealthtracker.service -f
```

## Step 3: Test the Camera

1. Open the dashboard in your browser
2. Click **"Start Monitoring"**
3. Camera should launch and display live feed **within the website** (no separate window!)
4. Watch the posture score update in real-time
5. Click **"End Monitoring"** to stop and save the session

## What's Been Fixed

### ✅ Auto-Start Service
- Pi loop now starts automatically on boot
- No more manual `python3 src/main.py` needed!
- Auto-restarts if it crashes

### ✅ Camera Stability & Speed
- Reduced image updates from every frame to every 3 frames (~100ms at 30fps)
- Reduced JPEG quality from 72 to 60 (smaller file size, faster transmission)
- Result: Smooth camera feed without lag/freezing

### ✅ Website Display
- Camera now displays **within the website** (not in separate window)
- Responsive layout works on mobile and desktop
- Better visual feedback when starting/stopping

### ✅ End Monitoring Button
- Now works correctly with error handling
- Shows "Stopping..." state while saving session
- Saves to Firestore then stops camera

## Verifying Everything Works

### Option A: Auto-Start (Recommended)
```bash
# Let the service run in background (started automatically)
# Just open the dashboard and test!
```

### Option B: Manual Start (For Testing)
```bash
# If you want to test manually first
cd ~/Documents/PostureHealthTracker/PostureHealthTracker/hardware
python3 src/main.py
```

## Dashboard Testing Checklist

- [ ] Click "Start Monitoring" → Camera preview appears in website
- [ ] Camera feed updates smoothly without lag
- [ ] Posture score updates in real-time
- [ ] Click "End Monitoring" → Session saves to Firestore
- [ ] Session appears in "Session History" table
- [ ] No errors in browser console (F12 to check)

## Still Having Issues?

View the logs to see what's happening:
```bash
journalctl --user -u posturehealthtracker.service -n 100
```

Or manually run to see real-time output:
```bash
cd ~/Documents/PostureHealthTracker/PostureHealthTracker/hardware
python3 src/main.py
```

## Full Details

See `AUTOSTART_SETUP.md` for complete setup guide with troubleshooting.
