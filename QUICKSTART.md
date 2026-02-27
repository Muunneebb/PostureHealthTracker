# PostureHealthTracker Web App - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the Web Server
```bash
python web_app.py
```
You'll see:
```
 * Running on http://127.0.0.1:5000
 * Database created: posture_tracker.db
```

### Step 3: Create Your Account
1. Open browser: http://localhost:5000
2. Click "Create Account"
3. Fill in username, email, password
4. Click "Create Account"
5. Login with your credentials

### Step 4: Start a Session
1. Click "Start New Session" on the dashboard
2. Note the Session ID
3. Your sensor system can now send data

## Testing the Web App

### Without Sensors (Demo Mode)

You can test the entire web app without hardware using this Python script:

**File: `test_web_app.py`**

```python
#!/usr/bin/env python3
"""
Test script to simulate sensor data and populate the web application.
Run the Flask app first: python web_app.py
"""

import requests
import time
import random
import math
from datetime import datetime

# Configuration
WEB_APP_URL = 'http://localhost:5000'
USERNAME = 'testuser'
PASSWORD = 'testpass123'

class DemoSession:
    def __init__(self):
        self.session_id = None
        self.start_time = datetime.now()
        
    def login(self):
        """Login to web app"""
        print(f'[*] Logging in as {USERNAME}...')
        resp = requests.post(
            f'{WEB_APP_URL}/login',
            json={'username': USERNAME, 'password': PASSWORD}
        )
        if resp.status_code == 200:
            print('[✓] Login successful')
            return True
        print(f'[✗] Login failed: {resp.json()}')
        return False
    
    def start_session(self):
        """Start a new monitoring session"""
        print('[*] Starting session...')
        resp = requests.post(f'{WEB_APP_URL}/api/start-session')
        if resp.status_code == 201:
            self.session_id = resp.json()['session_id']
            print(f'[✓] Session started: ID {self.session_id}')
            return True
        print(f'[✗] Failed to start session')
        return False
    
    def simulate_readings(self, duration_seconds=60):
        """Send simulated sensor readings"""
        print(f'[*] Simulating {duration_seconds}s of sensor data...')
        
        for i in range(duration_seconds):
            # Simulate realistic sensor data
            time_elapsed = i
            
            # Pitch: varies between 5-30 degrees (sitting posture)
            pitch = 15 + 8 * math.sin(time_elapsed / 20)
            
            # Roll: varies between -10 to 10 degrees
            roll = 5 * math.cos(time_elapsed / 30)
            
            # FSR sensors: simulate seated weight distribution
            base_left = 45000
            base_right = 48000
            base_center = 50000
            fsr_left = int(base_left + random.randint(-2000, 2000))
            fsr_right = int(base_right + random.randint(-2000, 2000))
            fsr_center = int(base_center + random.randint(-1000, 1000))
            
            # Stress score: varies between 0.3-0.7
            stress = 0.5 + 0.2 * math.sin(time_elapsed / 15)
            stress_score = max(0.3, min(0.7, stress))
            
            # Random buzzer trigger (1 in 20 chance)
            buzzer_triggered = random.random() < 0.05
            
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
            
            resp = requests.post(
                f'{WEB_APP_URL}/api/session/{self.session_id}/readings',
                json=reading
            )
            
            if resp.status_code == 201:
                status = '✓' if not buzzer_triggered else '🔔'
                print(f'[{status}] Reading {i+1}: Pitch={pitch:.1f}°, Stress={stress_score:.2f}')
            else:
                print(f'[✗] Failed to send reading: {resp.json()}')
            
            time.sleep(1)
    
    def end_session(self):
        """End the monitoring session"""
        print('[*] Ending session...')
        resp = requests.post(
            f'{WEB_APP_URL}/api/session/{self.session_id}/end'
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f'[✓] Session ended')
            print(f'    Duration: {data["duration"]} seconds')
            return True
        print(f'[✗] Failed to end session')
        return False
    
    def get_stats(self):
        """Get and display session statistics"""
        resp = requests.get(
            f'{WEB_APP_URL}/api/session/{self.session_id}/stats'
        )
        if resp.status_code == 200:
            stats = resp.json()
            print('\n[SESSION STATISTICS]')
            print(f'  Duration: {stats["duration"]//60} min {stats["duration"]%60} sec')
            print(f'  Sitting Time: {stats["sitting_duration"]//60 if stats["sitting_duration"] else 0} min')
            print(f'  Sitting %: {stats["sitting_percentage"]:.1f}%')
            print(f'  Avg Score: {stats["session_score"]:.2f}')
            print(f'  Buzzer Count: {stats["buzzer_count"]}')
            print(f'  Break Alert: {stats["break_alert"]}')
            print(f'  Buzzer Alert: {stats["excessive_buzzer_alert"]}')


def main():
    print('=' * 50)
    print('PostureHealthTracker - Web App Demo')
    print('=' * 50)
    
    session = DemoSession()
    
    # Step 1: Register a test user (if needed)
    print('\n[Step 1] Registering test user...')
    resp = requests.post(
        f'{WEB_APP_URL}/register',
        json={
            'username': USERNAME,
            'email': 'test@example.com',
            'password': PASSWORD,
            'confirm_password': PASSWORD
        }
    )
    if resp.status_code == 201:
        print('[✓] User registered')
    else:
        print('[*] User already exists')
    
    # Step 2: Login
    print('\n[Step 2] Authenticating...')
    if not session.login():
        return
    
    # Step 3: Start session
    print('\n[Step 3] Starting monitoring session...')
    if not session.start_session():
        return
    
    # Step 4: Send simulated data
    print('\n[Step 4] Sending sensor readings...')
    session.simulate_readings(duration_seconds=30)  # 30 seconds demo
    
    # Step 5: End session
    print('\n[Step 5] Ending session...')
    session.end_session()
    
    # Show stats
    print('\n[Step 6] Session statistics:')
    session.get_stats()
    
    print('\n' + '=' * 50)
    print('Demo Complete!')
    print('View your session at: http://localhost:5000/dashboard')
    print('=' * 50)


if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.ConnectionError:
        print('[✗] ERROR: Cannot connect to web app')
        print('    Make sure Flask is running: python web_app.py')
    except KeyboardInterrupt:
        print('\n[*] Demo cancelled')
```

### Run the Demo

1. **Terminal 1**: Start the web app
   ```bash
   python web_app.py
   ```

2. **Terminal 2**: Run the demo
   ```bash
   python test_web_app.py
   ```

3. **Browser**: View results at `http://localhost:5000/dashboard`

## Integrating Real Sensors

To connect your actual sensor hardware:

1. **Add integration import** to your sensor's main loop:
   ```python
   from web_app_integration import WebAppIntegration
   
   integration = WebAppIntegration('http://localhost:5000')
   integration.login('your_username', 'your_password')
   integration.start_session()
   ```

2. **Send readings in the loop**:
   ```python
   integration.send_reading(
       pitch=imu_data['pitch'],
       roll=imu_data['roll'],
       fsr_left=ads.read_fsr_left(),
       fsr_right=ads.read_fsr_right(),
       fsr_center=ads.read_fsr_center(),
       stress_score=calculated_stress,
       is_seated=is_seated,
       buzzer_triggered=buzzer_signal
   )
   ```

3. **Cleanup on exit**:
   ```python
   integration.end_session()
   ```

## Dashboard Features

### Statistics Cards
- **Total Sessions**: Count of all sessions
- **Total Sitting Time**: Aggregated hours
- **Avg Session Score**: Average stress score
- **Break Alerts**: Times user exceeded 2 hours
- **Buzzer Alerts**: Times buzzer triggered 5+ times

### Session Table
Click "View" on any session to see:
- Interactive stress score graph
- Body position (pitch/roll) graph
- Complete sensor reading table
- Alert summary

## URL Reference

| Page | URL |
|------|-----|
| Login | http://localhost:5000/login |
| Register | http://localhost:5000/register |
| Dashboard | http://localhost:5000/dashboard |
| Session Detail | http://localhost:5000/session/1 |

## Common Tasks

### View All Sessions
```bash
curl http://localhost:5000/api/user/sessions | python -m json.tool
```

### Get Session Stats
```bash
curl http://localhost:5000/api/session/1/stats | python -m json.tool
```

### Check Database
```bash
sqlite3 posture_tracker.db
sqlite> SELECT * FROM session;
sqlite> SELECT COUNT(*) FROM reading;
```

## Troubleshooting

**Port 5000 already in use?**
```bash
# Change port in web_app.py:
app.run(debug=True, host='0.0.0.0', port=5001)
```

**Database corrupted?**
```bash
rm posture_tracker.db
python web_app.py  # Creates new database
```

**Login not working?**
```bash
# Check users table
sqlite3 posture_tracker.db "SELECT username FROM user;"
```

## Next Steps

- ✅ Start the web app
- ✅ Create an account
- ✅ Test with demo data
- ⭕ Integrate real sensors
- ⭕ Monitor sessions in real-time
- ⭕ Review analytics and alerts

For detailed integration instructions, see `INTEGRATION_GUIDE.md`
