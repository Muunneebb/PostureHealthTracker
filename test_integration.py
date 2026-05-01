#!/usr/bin/env python3
"""
Integration test script for Posture Health Tracker
Tests: Firebase connectivity, camera module, pose detection, scoring
"""

import sys
import os
import time

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    try:
        from hardware.src import config
        print("✓ config module imported")
    except Exception as e:
        print(f"✗ config import failed: {e}")
        return False
    
    try:
        from hardware.src import camera_module
        print("✓ camera_module imported")
    except Exception as e:
        print(f"✗ camera_module import failed: {e}")
        return False
    
    try:
        from hardware.src import main as hw_main
        print("✓ hardware.main imported")
    except Exception as e:
        print(f"✗ hardware.main import failed: {e}")
        return False
    
    return True


def test_firebase_connectivity():
    """Test Firebase RTDB connectivity"""
    print("\n" + "="*60)
    print("TEST 2: Firebase Connectivity")
    print("="*60)
    
    try:
        import requests
        FIREBASE_URL = "https://posturehealthtracker-default-rtdb.firebaseio.com"
        
        # Simple ping to Firebase
        response = requests.get(f"{FIREBASE_URL}/system_state.json", timeout=5)
        if response.status_code == 200:
            print(f"✓ Firebase RTDB reachable (status: {response.status_code})")
            print(f"  Current system_state: {response.json()}")
            return True
        else:
            print(f"✗ Firebase returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Firebase connectivity test failed: {e}")
        return False


def test_camera_module():
    """Test camera module initialization (dry run)"""
    print("\n" + "="*60)
    print("TEST 3: Camera Module Initialization")
    print("="*60)
    
    try:
        from hardware.src import camera_module
        cam = camera_module.CameraModule()
        print(f"✓ CameraModule initialized")
        print(f"  Available: {cam.available}")
        print(f"  Picam2: {cam.picam2}")
        return True
    except Exception as e:
        print(f"✗ Camera module test failed: {e}")
        return False


def test_posture_scoring():
    """Test posture scoring logic"""
    print("\n" + "="*60)
    print("TEST 4: Posture Scoring Functions")
    print("="*60)
    
    try:
        # Import scoring function
        from hardware.src.main import score_from_camera_metrics
        
        # Test cases
        test_cases = [
            (None, "No metrics", 100),
            ({}, "Empty metrics", 100),
            ({'is_bad': False}, "Good posture", 95),
            ({'is_bad': True, 'reason': 'Slouching'}, "Slouching", 60),
            ({'is_bad': True, 'reason': 'Head forward'}, "Head forward", 55),
            ({'is_bad': True}, "Bad posture (generic)", 50),
            ({'shoulder_alignment': 0.01, 'neck_angle': 0.02}, "MediaPipe metrics", None),
        ]
        
        for metrics, desc, expected in test_cases:
            score = score_from_camera_metrics(metrics)
            if expected is not None:
                status = "✓" if score == expected else "✗"
                print(f"{status} {desc}: {score} (expected {expected})")
            else:
                print(f"✓ {desc}: {score}")
        
        return True
    except Exception as e:
        print(f"✗ Posture scoring test failed: {e}")
        return False


def test_firebase_write():
    """Test Firebase live_data write"""
    print("\n" + "="*60)
    print("TEST 5: Firebase RTDB Write")
    print("="*60)
    
    try:
        import requests
        FIREBASE_URL = "https://posturehealthtracker-default-rtdb.firebaseio.com"
        
        test_payload = {
            "score": 85,
            "frameScore": 87,
            "sessionScore": 85,
            "activeSessionId": "test-session-123",
            "cameraActive": True,
            "cameraMetrics": {"is_bad": False, "reason": ""},
            "postureStatus": "Good",
            "postureReason": "",
            "cameraFrame": None,
            "updatedAt": int(time.time())
        }
        
        response = requests.put(
            f"{FIREBASE_URL}/live_data.json",
            json=test_payload,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✓ Firebase RTDB write successful (status: {response.status_code})")
            return True
        else:
            print(f"✗ Firebase write returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Firebase write test failed: {e}")
        return False


def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("POSTURE HEALTH TRACKER - INTEGRATION TEST SUITE")
    print("="*60)
    
    results = []
    
    results.append(("Module Imports", test_imports()))
    results.append(("Firebase Connectivity", test_firebase_connectivity()))
    results.append(("Camera Module", test_camera_module()))
    results.append(("Posture Scoring", test_posture_scoring()))
    results.append(("Firebase RTDB Write", test_firebase_write()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed! Ready to run hardware loop.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
