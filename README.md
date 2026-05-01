# PostureHealthTracker

**Status:** ✅ **Production Ready** (May 1, 2026)

Real-time posture monitoring using Raspberry Pi 5 + Hailo AI Hat with Firebase live dashboard.

## Quick Start

### Prerequisites
- Raspberry Pi 5 with Hailo AI Hat
- Python 3.9+
- `pip install -r requirements.txt`

### Run
```bash
# Test integration (optional)
python3 test_integration.py
python3 test_e2e_session.py

# Start monitoring
cd hardware
python3 src/main.py
```

### Dashboard
Visit: https://muunneebb.github.io/PostureHealthTracker/docs/index.html

Click **"Start Monitoring"** to begin a session.

## Architecture

**Pi Hardware Loop** → captures camera frames → analyzes posture with MediaPipe (Hailo thresholds) → **Firebase RTDB** (live_data) → **Web Dashboard** (real-time updates) → User sees live camera + posture score + status

**Session Lifecycle** → Start/Stop on dashboard → stored in Firestore → historical data with metrics

## Features

✅ Live camera preview with posture overlay  
✅ Real-time posture scoring (0-100%)  
✅ Posture status detection (Good/Bad posture alerts)  
✅ Session history with Firestore  
✅ Firebase live updates (< 1 second latency)  
✅ Hailo AI thresholds integrated (head forward, slouching)  

## Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Setup & deployment guide
- [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) - What was built today
- [Test Suite](test_integration.py) - Validation tests

## Test Results

✅ All core modules working  
✅ Hardware loop validated (10-second test successful)  
✅ Posture scoring: Good=95%, Slouching=60%, Head Forward=55%  
✅ End-to-end session simulation passed  

## Next Steps

1. Deploy to Raspberry Pi
2. Monitor live sessions via web dashboard
3. Review session history and trends
4. Consider direct Hailo AI inference for 10x speed improvement

---

Repository: https://github.com/Muunneebb/PostureHealthTracker
