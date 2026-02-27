# PostureHealthTracker Web Application

A comprehensive web application for tracking posture health, monitor sensor readings, and manage user sessions.

## Features

- **User Authentication**: Secure login and registration system
- **Session Management**: Track posture sessions with start/end times
- **Real-time Monitoring**: Monitor sensor data in real-time
- **Session Analytics**: View detailed session statistics and data visualization
- **Alert System**:
  - Break alert after 2 hours of continuous sitting
  - Excessive buzzer alert when buzzer triggers 5 times
- **User History**: View all past sessions with detailed metrics
- **Dashboard**: Overview of stats and recent sessions

## Technology Stack

- **Backend**: Flask with Flask-SQLAlchemy
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Charts**: Chart.js for data visualization

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python web_app.py
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Database Schema

### User Table
- id (Primary Key)
- username (Unique)
- password (Hashed)
- email (Unique)
- created_at (DateTime)

### Session Table
- id (Primary Key)
- user_id (Foreign Key)
- start_time (DateTime)
- end_time (DateTime)
- total_duration (Integer - seconds)
- sitting_duration (Integer - seconds)
- session_score (Float - 0-1)
- buzzer_count (Integer)
- break_alert_triggered (Boolean)
- excessive_buzzer_alert (Boolean)

### Reading Table
- id (Primary Key)
- session_id (Foreign Key)
- timestamp (DateTime)
- pitch (Float - degrees)
- roll (Float - degrees)
- fsr_left (Integer - ADC value)
- fsr_right (Integer - ADC value)
- fsr_center (Integer - ADC value)
- stress_score (Float - 0-1)
- is_seated (Boolean)
- buzzer_triggered (Boolean)

## API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /login` - Login user
- `GET /logout` - Logout user

### Sessions
- `POST /api/start-session` - Start a new session
- `POST /api/session/<id>/end` - End a session
- `POST /api/session/<id>/readings` - Add sensor reading
- `GET /api/session/<id>/stats` - Get session statistics
- `GET /api/user/sessions` - Get all user sessions

### Pages
- `GET /dashboard` - Main dashboard
- `GET /session/<id>` - View session details

## Frontend Components

### Dashboard
- Statistics cards showing total sessions, sitting time, average score, alerts
- Table of recent sessions with sortable columns
- Quick action to start new session

### Session Detail
- Overview statistics
- Alert notifications
- Sensor reading graphs (stress score, pitch, roll)
- Detailed reading table

### Authentication Pages
- Login page with form validation
- Registration page with password confirmation
- Error handling and user feedback

## Configuration

Edit the Flask app configuration in `web_app.py`:
```python
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posture_tracker.db'
```

## Alert Conditions

1. **Break Alert**: Triggered when a session exceeds 2 hours (7200 seconds) of continuous sitting
2. **Buzzer Alert**: Triggered when the buzzer has been activated 5 or more times during a session

## Data Visualization

- **Stress Score Chart**: Line graph showing stress levels over time
- **Position Chart**: Dual-line graph showing pitch and roll angles over time

## Notes

- Session data is stored locally in SQLite database
- Password hashing uses Werkzeug's security functions
- CSRF protection should be added for production use
- WebSocket integration could be added for real-time updates
- Browser notifications require user permission
