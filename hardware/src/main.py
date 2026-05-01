import time
import threading
import os
from importlib import import_module
import requests # <-- ADDED: To talk directly to the cloud
from src import sensors, display, buzzer, camera_module, utils, config

LOG_PATH = 'posture_stress_log.csv'

# ==========================================
# FIREBASE CLOUD LINK
# ==========================================
# This connects your Pi directly to the website without Flask
FIREBASE_URL = "https://posturehealthtracker-default-rtdb.firebaseio.com"

firestore_client = None


def get_firestore_client():
    global firestore_client

    if firestore_client is not None:
        return firestore_client

    cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not cred_path or not os.path.exists(cred_path):
        return None

    try:
        firebase_admin_module = import_module("firebase_admin")
        credentials_module = import_module("firebase_admin.credentials")
        firestore_module = import_module("firebase_admin.firestore")

        if not firebase_admin_module._apps:
            firebase_admin_module.initialize_app(credentials_module.Certificate(cred_path))
        firestore_client = firestore_module.client()
    except Exception as error:
        print(f"Firestore admin init failed: {error}")
        firestore_client = None

    return firestore_client


def push_live_data(payload):
    requests.put(f"{FIREBASE_URL}/live_data.json", json=payload, timeout=2)


def save_reading(session_id, payload):
    client = get_firestore_client()
    if not client or not session_id:
        return

    session_ref = client.collection('sessions').document(session_id)
    session_ref.collection('readings').add(payload)
    session_ref.set({
        'lastReadingAt': payload.get('timestamp'),
        'lastLiveScore': payload.get('score'),
        'status': 'active'
    }, merge=True)

def compute_posture_status(imu_read, ads):
    pitch = imu_read.get('pitch', 0)
    roll = imu_read.get('roll', 0)
    left = ads.read_fsr_left()
    right = ads.read_fsr_right()
    center = ads.read_fsr_center()

    torso_slouch = abs(pitch) > config.SLOUCH_ANGLE_ALERT_DEG
    forward_lean = pitch > config.FORWARD_LEAN_ALERT_DEG
    weight_imbalance = abs(left - right) > config.FSR_PRESSURE_THRESHOLD
    seated = center > config.FSR_PRESSURE_THRESHOLD

    return {
        'pitch': pitch,
        'roll': roll,
        'torso_slouch': torso_slouch,
        'forward_lean': forward_lean,
        'weight_imbalance': weight_imbalance,
        'seated': seated,
        'fsr_left': left,
        'fsr_right': right,
        'fsr_center': center
    }

def compute_stress_score(hr, rr_list, gsr_raw):
    gsr_norm = gsr_raw / 65535.0 if gsr_raw else 0
    hrv = utils.rmssd(rr_list)
    hrv_norm = 0
    if hrv:
        hrv_norm = utils.clamp(1 - (hrv / 100.0), 0, 1)
    score = 0.6 * gsr_norm + 0.4 * hrv_norm
    return score, {'gsr_norm': gsr_norm, 'hrv': hrv}

def main_loop():
    imu = sensors.IMU()
    ads = sensors.ADSInputs()
    max3 = sensors.MAX30102Sensor()
    oled = display.OLED()
    bz = buzzer.Buzzer()
    cam = camera_module.CameraModule()

    rr_history = []
    active_session_id = None
    camera_started_for_session = False
    
    print("Hardware Booted. Connecting to Firebase...")

    try:
        while True:
            # 1. READ SENSORS
            imu_read = imu.read_tilt()
            ads_read = ads
            posture = compute_posture_status(imu_read, ads_read)

            hr, rr = max3.read()
            if rr:
                rr_history.extend(rr)
                rr_history = rr_history[-60:]

            gsr = ads.read_gsr()
            stress_score, stress_parts = compute_stress_score(hr, rr_history, gsr)
            
            # Calculate a basic 0-100 score for the website UI
            ui_score = 100
            if posture['torso_slouch'] or posture['forward_lean']: ui_score -= 30
            if posture['weight_imbalance']: ui_score -= 20
            ui_score = max(0, ui_score) # Prevent negative numbers

            # 2. CHECK THE CLOUD (Did the user click "Start" on the website?)
            try:
                state_resp = requests.get(f"{FIREBASE_URL}/system_state.json", timeout=2)
                state = state_resp.json() or {}
                requested_session_id = state.get('activeSessionId')
                
                # If Website says "ON", we do the monitoring
                if state.get('camera_command') == "ON":
                    if requested_session_id and requested_session_id != active_session_id:
                        active_session_id = requested_session_id
                        camera_started_for_session = False

                    if not camera_started_for_session:
                        cam.start()
                        camera_started_for_session = True

                    camera_metrics = {}

                    # -- Camera Analysis --
                    if cam.available and int(time.time()) % 60 == 0:
                        path = cam.capture()
                        if path:
                            camera_metrics = cam.analyze_posture(path) or {}

                    
                    # -- Update the Website Live Data --
                    live_payload = {
                        "pitch": round(posture['pitch'], 1),
                        "roll": round(posture['roll'], 1),
                        "stress": round(stress_score, 2),
                        "score": ui_score,
                        "activeSessionId": active_session_id,
                        "cameraActive": True,
                        "cameraMetrics": camera_metrics,
                        "updatedAt": int(time.time())
                    }
                    push_live_data(live_payload)

                    save_reading(active_session_id, {
                        "timestamp": int(time.time()),
                        "pitch": round(posture['pitch'], 1),
                        "roll": round(posture['roll'], 1),
                        "score": ui_score,
                        "stress": round(stress_score, 2),
                        "seated": posture['seated'],
                        "torso_slouch": posture['torso_slouch'],
                        "forward_lean": posture['forward_lean'],
                        "weight_imbalance": posture['weight_imbalance'],
                        "cameraMetrics": camera_metrics
                    })
                    
                    # -- Update Hardware OLED --
                    lines = [
                        f"Status: ACTIVE",
                        f"Score:  {ui_score}%",
                        f"Pitch:  {posture['pitch']:.1f}",
                        f"Stress: {stress_score:.2f}",
                    ]
                    oled.show_status(lines)

                    # -- Hardware Alerts --
                    if posture['torso_slouch'] or posture['forward_lean']:
                        bz.beep(times=1, duration=0.12)
                    if stress_score >= config.STRESS_SCORE_ALERT:
                        bz.beep(times=2, duration=0.12)

                else:
                    # Website says "OFF", so we just standby quietly
                    if camera_started_for_session:
                        cam.stop()
                        camera_started_for_session = False
                        active_session_id = None
                    oled.show_status(["Device Ready", "Waiting for", "Start button", "on website..."])
                    
            except Exception as e:
                print(f"Network Error: {e}")
                oled.show_status(["Network Error", "Check WiFi..."])

            time.sleep(1)
            
    except KeyboardInterrupt:
        print('Shutting down...')
        bz.cleanup()

if __name__ == '__main__':
    main_loop()