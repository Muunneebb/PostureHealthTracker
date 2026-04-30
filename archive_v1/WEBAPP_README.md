# PostureHealthTracker Web Application

A web application for tracking posture sessions, storing sensor packets, and monitoring posture health in real time.

## Features

- User authentication with registration and login
- Session management with start and manual end controls
- Real-time sensor feed on the dashboard for active sessions
- Real-time session detail updates (new readings appended while session is active)
- Break tracking during sessions:
  - breaks taken count
  - last break time
  - next break due time
- Alert system:
  - take-break alert after 2 hours of continuous sitting
  - take-break alert after 3 buzzer triggers
- Session score starts at 100% and decreases by 1% per buzzer trigger
- Session analytics and historical session table

## Technology Stack

- Backend: Flask + Flask-SQLAlchemy
- Database: SQLite
- Frontend: HTML5, CSS3, JavaScript
- Charts: Chart.js

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   python web_app.py
   ```

3. Open:
   ```
   http://localhost:5000
   ```

## Database Schema

### User
- `id` (PK)
- `username` (unique)
- `password` (hashed)
- `email` (unique)
- `created_at`

### Session
- `id` (PK)
- `user_id` (FK)
- `start_time`
- `end_time`
- `total_duration` (seconds)
- `sitting_duration` (seconds)
- `session_score` (float 0-1, starts at 1.0)
- `buzzer_count`
- `break_count`
- `last_break_time`
- `next_break_time`
- `continuous_sitting_seconds`
- `break_alert_triggered`
- `excessive_buzzer_alert`

### Reading
- `id` (PK)
- `session_id` (FK)
- `timestamp`
- `pitch`
- `roll`
- `fsr_left`
- `fsr_right`
- `fsr_center`
- `stress_score`
- `is_seated`
- `buzzer_triggered`

## API Endpoints

### Authentication
- `POST /register`
- `POST /login`
- `GET /logout`

### Sessions
- `POST /api/start-session`
- `POST /api/session/<id>/end`
- `POST /api/session/<id>/readings`
- `GET /api/session/<id>/stats`
- `GET /api/session/<id>/readings`
- `GET /api/user/sessions`

### Session Readings Query Parameters
For `GET /api/session/<id>/readings`:
- `since_id` (optional): fetch only rows where `reading.id > since_id`
- `limit` (optional): max rows (default 100, max 500)
- `latest` (optional): when true and `since_id` is not provided, returns the latest `limit` readings

### Session Stats Response Highlights
`GET /api/session/<id>/stats` includes:
- break tracker fields (`break_count`, `last_break_time`, `next_break_time`)
- take-break status (`take_break_alert`, `take_break_reasons`)
- reading metadata (`reading_count`, `latest_reading`)

## Frontend Behavior

### Dashboard
- Start and end active session controls
- Break tracker panel (last break, next break, break count)
- Live sensor panel with all sensor fields:
  - pitch, roll
  - fsr left/right/center
  - stress score
  - seated state
  - buzzer-triggered state
- Live sensor packet table updates every few seconds

### Session Detail
- Full reading table includes all sensor values
- Stress and position charts update in real time for active sessions
- Summary stats refresh while session is active

## Alert Conditions

1. Break alert: 2 hours (7200 seconds) of continuous sitting
2. Buzzer alert: 3 or more buzzer activations in the session

## Scoring Rule

- Session score starts at `1.0` (100%)
- Each `buzzer_triggered` event reduces score by `0.01` (1%)
- Score is clamped to a minimum of `0.0`

## Notes

- Existing SQLite databases are upgraded at startup to add new break-tracking session columns.
- Browser notifications require permission.
- Real-time updates currently use polling; WebSocket can be added later if needed.
