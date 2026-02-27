import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posture_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sessions = db.relationship('Session', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_duration = db.Column(db.Integer)  # in seconds
    sitting_duration = db.Column(db.Integer)  # in seconds
    session_score = db.Column(db.Float)  # score based on sensor readings
    buzzer_count = db.Column(db.Integer, default=0)
    break_alert_triggered = db.Column(db.Boolean, default=False)
    excessive_buzzer_alert = db.Column(db.Boolean, default=False)
    readings = db.relationship('Reading', backref='session', lazy=True, cascade='all, delete-orphan')

    def get_duration(self):
        """Get session duration in seconds"""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return int((datetime.utcnow() - self.start_time).total_seconds())

    def get_sitting_percentage(self):
        """Get percentage of time sitting"""
        duration = self.get_duration()
        if duration == 0:
            return 0
        return (self.sitting_duration / duration) * 100


class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    pitch = db.Column(db.Float)
    roll = db.Column(db.Float)
    fsr_left = db.Column(db.Integer)
    fsr_right = db.Column(db.Integer)
    fsr_center = db.Column(db.Integer)
    stress_score = db.Column(db.Float)
    is_seated = db.Column(db.Boolean)
    buzzer_triggered = db.Column(db.Boolean, default=False)


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not username or not email or not password:
            return jsonify({'error': 'Missing required fields'}), 400

        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Registration successful. Please login.'}), 201

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True, 'redirect': url_for('dashboard')}), 200

        return jsonify({'error': 'Invalid username or password'}), 401

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    sessions = Session.query.filter_by(user_id=user_id).order_by(Session.start_time.desc()).all()
    
    stats = {
        'total_sessions': len(sessions),
        'total_sitting_time': sum(s.sitting_duration or 0 for s in sessions),
        'avg_session_score': sum(s.session_score or 0 for s in sessions) / max(len(sessions), 1),
        'break_alerts': sum(1 for s in sessions if s.break_alert_triggered),
        'buzzer_alerts': sum(1 for s in sessions if s.excessive_buzzer_alert),
    }

    return render_template('dashboard.html', sessions=sessions, stats=stats)


@app.route('/session/<int:session_id>')
@login_required
def view_session(session_id):
    user_id = session['user_id']
    sess = Session.query.filter_by(id=session_id, user_id=user_id).first()

    if not sess:
        return redirect(url_for('dashboard'))

    readings = Reading.query.filter_by(session_id=session_id).order_by(Reading.timestamp).all()

    session_data = {
        'id': sess.id,
        'start_time': sess.start_time.isoformat(),
        'end_time': sess.end_time.isoformat() if sess.end_time else None,
        'duration': sess.get_duration(),
        'sitting_duration': sess.sitting_duration,
        'sitting_percentage': sess.get_sitting_percentage(),
        'session_score': sess.session_score,
        'buzzer_count': sess.buzzer_count,
        'break_alert': sess.break_alert_triggered,
        'excessive_buzzer_alert': sess.excessive_buzzer_alert,
        'readings': [{
            'timestamp': r.timestamp.isoformat(),
            'pitch': r.pitch,
            'roll': r.roll,
            'fsr_left': r.fsr_left,
            'fsr_right': r.fsr_right,
            'fsr_center': r.fsr_center,
            'stress_score': r.stress_score,
            'is_seated': r.is_seated,
            'buzzer_triggered': r.buzzer_triggered,
        } for r in readings]
    }

    return render_template('session_detail.html', session=session_data)


@app.route('/api/start-session', methods=['POST'])
@login_required
def start_session():
    user_id = session['user_id']
    
    # End any existing active session
    active = Session.query.filter_by(user_id=user_id, end_time=None).first()
    if active:
        active.end_time = datetime.utcnow()
    
    new_session = Session(user_id=user_id)
    db.session.add(new_session)
    db.session.commit()

    return jsonify({
        'success': True,
        'session_id': new_session.id,
        'start_time': new_session.start_time.isoformat()
    }), 201


@app.route('/api/session/<int:session_id>/readings', methods=['POST'])
@login_required
def add_reading(session_id):
    user_id = session['user_id']
    sess = Session.query.filter_by(id=session_id, user_id=user_id).first()

    if not sess:
        return jsonify({'error': 'Session not found'}), 404

    data = request.get_json()

    reading = Reading(
        session_id=session_id,
        pitch=data.get('pitch'),
        roll=data.get('roll'),
        fsr_left=data.get('fsr_left'),
        fsr_right=data.get('fsr_right'),
        fsr_center=data.get('fsr_center'),
        stress_score=data.get('stress_score'),
        is_seated=data.get('is_seated', False),
        buzzer_triggered=data.get('buzzer_triggered', False)
    )

    # Update session sitting duration
    if data.get('is_seated'):
        sess.sitting_duration = (sess.sitting_duration or 0) + 1

    # Update buzzer count
    if data.get('buzzer_triggered'):
        sess.buzzer_count = (sess.buzzer_count or 0) + 1
        
        # Alert if buzzer triggered 5 times
        if sess.buzzer_count >= 5:
            sess.excessive_buzzer_alert = True

    # Update session score
    if data.get('stress_score') is not None:
        scores = [r.stress_score for r in sess.readings if r.stress_score is not None]
        scores.append(data.get('stress_score'))
        sess.session_score = sum(scores) / len(scores) if scores else 0

    # Check for 2 hour break alert (7200 seconds)
    duration = (datetime.utcnow() - sess.start_time).total_seconds()
    if duration > 7200 and not sess.break_alert_triggered:
        sess.break_alert_triggered = True

    db.session.add(reading)
    db.session.commit()

    return jsonify({'success': True}), 201


@app.route('/api/session/<int:session_id>/end', methods=['POST'])
@login_required
def end_session(session_id):
    user_id = session['user_id']
    sess = Session.query.filter_by(id=session_id, user_id=user_id).first()

    if not sess:
        return jsonify({'error': 'Session not found'}), 404

    sess.end_time = datetime.utcnow()
    sess.total_duration = sess.get_duration()

    db.session.commit()

    return jsonify({
        'success': True,
        'end_time': sess.end_time.isoformat(),
        'duration': sess.total_duration
    }), 200


@app.route('/api/session/<int:session_id>/stats', methods=['GET'])
@login_required
def get_session_stats(session_id):
    user_id = session['user_id']
    sess = Session.query.filter_by(id=session_id, user_id=user_id).first()

    if not sess:
        return jsonify({'error': 'Session not found'}), 404

    return jsonify({
        'id': sess.id,
        'duration': sess.get_duration(),
        'sitting_duration': sess.sitting_duration,
        'sitting_percentage': sess.get_sitting_percentage(),
        'session_score': sess.session_score,
        'buzzer_count': sess.buzzer_count,
        'break_alert': sess.break_alert_triggered,
        'excessive_buzzer_alert': sess.excessive_buzzer_alert
    }), 200


@app.route('/api/user/sessions', methods=['GET'])
@login_required
def get_user_sessions():
    user_id = session['user_id']
    sessions = Session.query.filter_by(user_id=user_id).order_by(Session.start_time.desc()).all()

    return jsonify({
        'sessions': [{
            'id': s.id,
            'start_time': s.start_time.isoformat(),
            'end_time': s.end_time.isoformat() if s.end_time else None,
            'duration': s.get_duration(),
            'sitting_duration': s.sitting_duration,
            'session_score': s.session_score,
            'buzzer_count': s.buzzer_count,
            'break_alert': s.break_alert_triggered,
            'excessive_buzzer_alert': s.excessive_buzzer_alert
        } for s in sessions]
    }), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
