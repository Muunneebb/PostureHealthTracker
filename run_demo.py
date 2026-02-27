#!/usr/bin/env python3
"""
Complete demo script to test the PostureHealthTracker web app.
This will:
1. Create a test user account
2. Login
3. Generate realistic fake sensor data
4. Populate the dashboard
"""

import requests
import time
import random
import math
from datetime import datetime

WEB_APP_URL = 'http://localhost:5000'
TEST_USERNAME = 'demouser'
TEST_EMAIL = 'demo@posture.local'
TEST_PASSWORD = 'DemoPass123!'

# Use a session to maintain cookies across requests
session = requests.Session()

print("=" * 70)
print("PostureHealthTracker - Complete Demo Setup")
print("=" * 70)

# Step 1: Register User
print("\n[STEP 1] Creating test user account...")
print(f"Username: {TEST_USERNAME}")
print(f"Email: {TEST_EMAIL}")

resp = session.post(
    f'{WEB_APP_URL}/register',
    json={
        'username': TEST_USERNAME,
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'confirm_password': TEST_PASSWORD
    }
)

if resp.status_code == 201:
    print("✓ User account created successfully!")
elif 'already exists' in resp.text:
    print("✓ User already exists (will use existing account)")
else:
    print(f"✗ Error: {resp.json().get('error', 'Unknown error')}")
    print(f"Response: {resp.text}")
    exit(1)

# Step 2: Login
print("\n[STEP 2] Logging in...")

resp = session.post(
    f'{WEB_APP_URL}/login',
    json={'username': TEST_USERNAME, 'password': TEST_PASSWORD}
)

if resp.status_code == 200:
    print("✓ Login successful!")
else:
    print(f"✗ Login failed: {resp.json()}")
    print(f"Response: {resp.text}")
    exit(1)

# Step 3: Start Session
print("\n[STEP 3] Starting new monitoring session...")

resp = session.post(f'{WEB_APP_URL}/api/start-session')

if resp.status_code == 201:
    session_id = resp.json()['session_id']
    print(f"✓ Session started (ID: {session_id})")
else:
    print(f"✗ Failed to start session")
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    exit(1)

# Step 4: Generate Realistic Sensor Data
print("\n[STEP 4] Generating 60 seconds of sensor data...")
print("(This simulates real posture tracking)")

for i in range(60):
    # Simulate posture patterns
    time_elapsed = i
    
    # Pitch: normal sitting posture varies 10-25 degrees
    base_pitch = 15
    pitch_variation = 5 * math.sin(time_elapsed / 20)
    pitch = base_pitch + pitch_variation
    
    # Roll: should be mostly balanced ±5 degrees
    roll = 3 * math.cos(time_elapsed / 25)
    
    # FSR sensors: weight distribution should be relatively balanced
    fsr_left = 45000 + random.randint(-3000, 3000)
    fsr_right = 48000 + random.randint(-3000, 3000)
    fsr_center = 50000 + random.randint(-2000, 2000)
    
    # Stress score: varies throughout session (0.2-0.8)
    base_stress = 0.5
    stress_variation = 0.25 * math.sin(time_elapsed / 15)
    stress_score = max(0.2, min(0.8, base_stress + stress_variation))
    
    # Buzzer: triggered occasionally (10% chance) for posture correction
    buzzer_triggered = random.random() < 0.10
    
    # Send reading
    reading = {
        'pitch': round(pitch, 2),
        'roll': round(roll, 2),
        'fsr_left': fsr_left,
        'fsr_right': fsr_right,
        'fsr_center': fsr_center,
        'stress_score': round(stress_score, 2),
        'is_seated': True,
        'buzzer_triggered': buzzer_triggered
    }
    
    resp = session.post(
        f'{WEB_APP_URL}/api/session/{session_id}/readings',
        json=reading
    )
    
    if resp.status_code == 201:
        indicator = "🔔" if buzzer_triggered else "✓"
        print(f"  [{indicator}] Reading {i+1:02d}: Pitch={pitch:6.1f}°, "
              f"Roll={roll:5.1f}°, Stress={stress_score:.2f}")
    else:
        print(f"  [✗] Failed to send reading {i+1}")
        break
    
    time.sleep(0.5)  # Small delay between readings

# Step 5: End Session
print("\n[STEP 5] Ending session...")

resp = session.post(f'{WEB_APP_URL}/api/session/{session_id}/end')

if resp.status_code == 200:
    data = resp.json()
    duration_min = data['duration'] // 60
    duration_sec = data['duration'] % 60
    print(f"✓ Session ended successfully")
    print(f"  Duration: {duration_min}m {duration_sec}s")
else:
    print(f"✗ Failed to end session")

# Step 6: Get and Display Statistics
print("\n[STEP 6] Session Statistics:")

resp = session.get(f'{WEB_APP_URL}/api/session/{session_id}/stats')

if resp.status_code == 200:
    stats = resp.json()
    print(f"  ├─ Total Duration: {stats['duration']//60}m {stats['duration']%60}s")
    print(f"  ├─ Sitting Time: {stats['sitting_duration']//60 if stats['sitting_duration'] else 0}m")
    print(f"  ├─ Sitting Percentage: {stats['sitting_percentage']:.1f}%")
    print(f"  ├─ Average Score: {stats['session_score']:.2f}")
    print(f"  ├─ Buzzer Count: {stats['buzzer_count']}")
    print(f"  ├─ Break Alert: {'YES (sat 2+ hours)' if stats['break_alert'] else 'No'}")
    print(f"  └─ Buzzer Alert: {'YES (5+ activations)' if stats['excessive_buzzer_alert'] else 'No'}")

print("\n" + "=" * 70)
print("✓ DEMO COMPLETE!")
print("=" * 70)
print("\n📊 View your dashboard at: http://localhost:5000/dashboard")
print(f"\n🔐 Login with:")
print(f"   Username: {TEST_USERNAME}")
print(f"   Password: {TEST_PASSWORD}")
print("\n" + "=" * 70)
