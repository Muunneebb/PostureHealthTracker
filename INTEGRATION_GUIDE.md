# PostureHealthTracker Web Application Integration Guide

## Overview

This project now includes a complete web application built with Flask that allows users to:
- Create accounts and login securely
- Monitor posture sessions in real-time
- View detailed session analytics and history
- Receive alerts for excessive sitting (2+ hours) and posture issues (5+ buzzer activations)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Hardware Sensors (Raspberry Pi)             │
│  - IMU (MPU6050): Pitch, Roll angles                   │
│  - FSR Sensors: Left, Right, Center pressure          │
│  - Heart Rate Monitor (MAX30102): HR, HRV             │
│  - GSR Sensor: Stress levels                           │
│  - Buzzer: Posture alerts                              │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│         Main Sensor Loop (main.py)                      │
│  - Collects sensor readings                            │
│  - Computes posture status & stress scores             │
│  - Logs data locally (CSV)                             │
│  - Triggers buzzer alerts                              │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│      Web App Integration (web_app_integration.py)      │
│  - Sends readings to web server                        │
│  - Manages session lifecycle                           │
│  - Handles authentication                              │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│         Web Application Server (web_app.py)            │
│  - Flask REST API                                      │
│  - SQLite Database (user sessions, readings)          │
│  - User authentication & session management           │
│  - Alert logic (2hr break, 5x buzzer)                 │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│          Web Browser Interface                          │
│  - Login & Registration                                │
│  - Dashboard with statistics                           │
│  - Session details & analytics                         │
│  - Real-time monitoring (future)                       │
└─────────────────────────────────────────────────────────┘
```

## File Structure

```
PostureHealthTracker/
├── src/
│   ├── main.py                 # Sensor data collection loop
│   ├── sensors.py              # Hardware sensor drivers
│   ├── buzzer.py               # Buzzer control
│   ├── camera_module.py        # Camera operations
│   ├── display.py              # OLED display
│   ├── config.py              # Configuration
│   └── utils.py               # Utility functions
├── web_app.py                  # Flask web application
├── web_app_integration.py     # Integration bridge
├── templates/                  # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── session_detail.html
├── static/                     # CSS & JavaScript
│   ├── css/style.css
│   └── js/session-monitor.js
├── posture_tracker.db         # SQLite database (auto-created)
├── requirements.txt           # Python dependencies
└── WEBAPP_README.md           # Web app documentation
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Web Application

```bash
# Terminal 1: Start Flask server
python web_app.py
```

The server will run on `http://localhost:5000` and create a SQLite database automatically.

### 3. Create Initial User Account

Open your browser and go to `http://localhost:5000/register` to create an account.

### 4. Integrate Sensors with Web App

#### Option A: Run Sensors with Web App Integration

Modify your `main.py` to use the integration module:

```python
import time
import threading
from src import sensors, display, buzzer, camera_module, utils, config
from web_app_integration import WebAppIntegration

# Initialize web app integration
web_integration = WebAppIntegration('http://localhost:5000')

# Login with sensor system credentials
USERNAME = 'your_username'
PASSWORD = 'your_password'

if not web_integration.login(USERNAME, PASSWORD):
    print('Failed to authenticate with web app')
    exit(1)

if not web_integration.start_session():
    print('Failed to start web session')
    exit(1)

# In your main loop, after computing readings:
def main_loop():
    imu = sensors.IMU()
    ads = sensors.ADSInputs()
    max3 = sensors.MAX30102Sensor()
    oled = display.OLED()
    bz = buzzer.Buzzer()
    cam = camera_module.CameraModule()
    
    rr_history = []
    buzzer_count = 0
    
    try:
        while True:
            imu_read = imu.read_tilt()
            ads_read = ads
            
            posture = compute_posture_status(imu_read, ads_read)
            
            hr, rr = max3.read()
            if rr:
                rr_history.extend(rr)
                rr_history = rr_history[-60:]
            
            gsr = ads.read_gsr()
            stress_score, stress_parts = compute_stress_score(hr, rr_history, gsr)
            
            # Track buzzer activation
            is_buzzer_triggered = posture['torso_slouch'] or posture['forward_lean']
            if is_buzzer_triggered:
                buzzer_count += 1
                bz.beep(times=1, duration=0.12)
            
            # Send reading to web app
            web_integration.send_reading(
                pitch=posture['pitch'],
                roll=posture['roll'],
                fsr_left=posture['fsr_left'],
                fsr_right=posture['fsr_right'],
                fsr_center=posture['fsr_center'],
                stress_score=stress_score,
                is_seated=posture['seated'],
                buzzer_triggered=is_buzzer_triggered
            )
            
            # Display on OLED
            lines = [
                f"Posture: {'Seated' if posture['seated'] else 'Away'}",
                f"Pitch:{posture['pitch']:.1f}° Score:{stress_score:.2f}",
                f"Web: Session Active",
            ]
            oled.show_status(lines)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print('Shutting down...')
        web_integration.end_session()
        bz.cleanup()

if __name__ == '__main__':
    main_loop()
```

#### Option B: Manual REST API Calls

Send readings directly to the web API:

```bash
# Start session
curl -X POST http://localhost:5000/api/start-session

# Send a reading
curl -X POST http://localhost:5000/api/session/1/readings \
  -H "Content-Type: application/json" \
  -d '{
    "pitch": 15.2,
    "roll": 5.1,
    "fsr_left": 45000,
    "fsr_right": 48000,
    "fsr_center": 50000,
    "stress_score": 0.65,
    "is_seated": true,
    "buzzer_triggered": false
  }'

# End session
curl -X POST http://localhost:5000/api/session/1/end
```

## Web Application Features

### 1. User Authentication
- Secure registration with email and password
- Password hashing using Werkzeug
- Session-based authentication

### 2. Dashboard
Shows overall statistics:
- Total sessions count
- Total sitting time (hours)
- Average session score
- Break alerts triggered
- Buzzer alerts triggered

Recent sessions table with:
- Date and time
- Session duration
- Sitting time
- Session score
- Buzzer count
- Alert status
- View details link

### 3. Session Details Page
Detailed view of each session:
- Basic statistics (duration, sitting time, percentage, average score)
- Alert summary
- Two interactive charts:
  - **Stress Score:** Over-time graph showing stress levels
  - **Body Position:** Pitch and Roll angles over time
- Complete reading table with all sensor values

### 4. Alert System

#### Break Alert
- Triggered after 2 hours (7200 seconds) of continuous sitting
- Browser notification (if permitted)
- Visible in session detail view

#### Buzzer Alert
- Triggered when buzzer activates 5+ times in a session
- Indicates excessive posture issues
- Recorded in session data

## API Endpoints Reference

### Authentication
```
POST /login
POST /register
GET /logout
```

### Session Management
```
POST /api/start-session
POST /api/session/<id>/end
POST /api/session/<id>/readings
GET /api/session/<id>/stats
GET /api/user/sessions
```

### Pages
```
GET /dashboard
GET /session/<id>
```

## Database Schema

### Users Table
```sql
CREATE TABLE user (
  id INTEGER PRIMARY KEY,
  username VARCHAR(80) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  email VARCHAR(120) UNIQUE NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Sessions Table
```sql
CREATE TABLE session (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  end_time DATETIME,
  total_duration INTEGER,
  sitting_duration INTEGER,
  session_score FLOAT,
  buzzer_count INTEGER DEFAULT 0,
  break_alert_triggered BOOLEAN DEFAULT 0,
  excessive_buzzer_alert BOOLEAN DEFAULT 0,
  FOREIGN KEY(user_id) REFERENCES user(id)
);
```

### Readings Table
```sql
CREATE TABLE reading (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  pitch FLOAT,
  roll FLOAT,
  fsr_left INTEGER,
  fsr_right INTEGER,
  fsr_center INTEGER,
  stress_score FLOAT,
  is_seated BOOLEAN,
  buzzer_triggered BOOLEAN DEFAULT 0,
  FOREIGN KEY(session_id) REFERENCES session(id)
);
```

## Configuration

Edit `web_app.py` to change:

```python
# Secret key for sessions (CHANGE IN PRODUCTION)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Database location
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posture_tracker.db'
```

## Running Both Systems

### Terminal 1: Start Web App
```bash
python web_app.py
```

### Terminal 2: Start Sensor System (with integration)
```bash
python src/main.py
```

Access the web interface at `http://localhost:5000`

## Troubleshooting

### Connection Issues
- Ensure Flask server is running on port 5000
- Check firewall settings
- Verify `web_app_url` in integration module matches your setup

### Database Issues
- Delete `posture_tracker.db` to reset and recreate
- Check file permissions in the working directory

### Authentication Issues
- Create a user account via `/register` first
- Use correct username and password in integration

### Missing Data
- Ensure sensors are working (check OLED display and logs)
- Verify integration credentials are correct
- Check network connectivity between systems

## Future Enhancements

- WebSocket integration for real-time dashboard updates
- CSRF protection for production
- Email notifications for alerts
- Data export to CSV/Excel
- Mobile app frontend
- Advanced analytics and machine learning
- Multi-device synchronization
- Offline mode with sync

## Support

For issues or questions, refer to:
- `WEBAPP_README.md` - Web app API documentation
- `web_app.py` - Source code comments
- `web_app_integration.py` - Integration module documentation
