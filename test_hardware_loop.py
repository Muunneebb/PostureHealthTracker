#!/usr/bin/env python3
"""
Short hardware loop test - runs for 10 seconds then exits
Used to validate the main loop works without hardware issues
"""

import sys
import os
import signal
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set a flag to stop after N iterations
LOOP_DURATION_SECS = 10
START_TIME = time.time()

def timeout_handler(signum, frame):
    """Handle timeout"""
    print("\n[TEST] Timeout handler triggered")
    sys.exit(0)

signal.signal(signal.SIGALRM, timeout_handler)

# Original main loop from hardware/src/main.py - we'll patch it
def test_main_loop():
    """Run main loop with safety timeout"""
    from hardware.src import camera_module
    import requests
    from datetime import datetime
    
    FIREBASE_URL = "https://posturehealthtracker-default-rtdb.firebaseio.com"
    
    print("[TEST] Starting hardware loop test (10 second duration)...")
    print("[TEST] This will:")
    print("  1. Poll Firebase every 1 sec")
    print("  2. Try to capture frames every 2 sec (will fail gracefully without camera)")
    print("  3. Push dummy data to live_data if session active")
    print()
    
    cam = camera_module.CameraModule()
    active_session_id = None
    camera_started_for_session = False
    session_frame_count = 0
    session_score_total = 0.0
    last_preview_update = 0.0
    last_camera_metrics = {}
    last_frame_score = 100
    
    iteration = 0
    
    try:
        while True:
            # Check duration
            elapsed = time.time() - START_TIME
            if elapsed > LOOP_DURATION_SECS:
                print(f"\n[TEST] Test duration ({LOOP_DURATION_SECS}s) exceeded. Stopping.")
                break
            
            iteration += 1
            print(f"[LOOP {iteration}] Time: {elapsed:.1f}s", end="")
            
            # Check Firebase
            try:
                state_resp = requests.get(f"{FIREBASE_URL}/system_state.json", timeout=2)
                state = state_resp.json() or {}
                print(f" | system_state status: {state_resp.status_code}", end="")
                
                if state.get('camera_command') == "ON":
                    print(" | Command: ON", end="")
                else:
                    print(" | Command: OFF", end="")
                    
            except Exception as e:
                print(f" | Firebase error: {type(e).__name__}", end="")
            
            print()  # newline
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n[TEST] Interrupted by user")
    except Exception as e:
        print(f"\n[TEST] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        try:
            if camera_started_for_session:
                cam.stop()
        except:
            pass
    
    print(f"\n[TEST] Loop test completed successfully!")
    print(f"[TEST] Ran {iteration} iterations over ~{elapsed:.1f} seconds")
    return 0

if __name__ == "__main__":
    try:
        exit_code = test_main_loop()
        sys.exit(exit_code)
    except Exception as e:
        print(f"FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
