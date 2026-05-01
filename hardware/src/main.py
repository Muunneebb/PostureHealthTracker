import time
import os
from datetime import datetime
from importlib import import_module
import requests # <-- ADDED: To talk directly to the cloud

if __package__ in (None, ""):
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src import camera_module
else:
    from . import camera_module

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
    try:
        requests.put(f"{FIREBASE_URL}/live_data.json", json=payload, timeout=30)
    except:
        pass  # Silently skip failed writes


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


def score_from_camera_metrics(camera_metrics):
    if not camera_metrics:
        return 100

    # If using Hailo/side-view posture detection (is_bad flag present)
    if 'is_bad' in camera_metrics:
        if camera_metrics['is_bad']:
            # Bad posture detected → lower score based on reason
            reason = camera_metrics.get('reason', 'Bad posture')
            if 'slouch' in reason.lower():
                return 60  # Slouching is moderate issue
            elif 'head' in reason.lower():
                return 55  # Head forward is more serious
            else:
                return 50  # Generic bad posture
        else:
            return 95  # Good posture detected
    
    # Fallback: MediaPipe-style metrics (shoulder_alignment + neck_angle)
    score = 100.0
    shoulder_alignment = camera_metrics.get('shoulder_alignment')
    neck_angle = camera_metrics.get('neck_angle')

    if shoulder_alignment is not None:
        score -= min(abs(shoulder_alignment) * 250.0, 25.0)
    if neck_angle is not None:
        score -= min(abs(neck_angle) * 250.0, 40.0)

    return int(max(0, min(100, round(score))))

def main_loop():
    cam = camera_module.CameraModule()

    active_session_id = None
    camera_started_for_session = False
    session_frame_count = 0
    session_score_total = 0.0
    last_preview_update = 0.0
    last_preview_data_url = None
    last_camera_metrics = {}
    last_frame_score = 100
    
    print("Hardware Booted. Connecting to Firebase...")

    try:
        while True:
            # 2. CHECK THE CLOUD (Did the user click "Start" on the website?)
            try:
                state_resp = requests.get(f"{FIREBASE_URL}/system_state.json", timeout=30)
                state = state_resp.json() or {}
                requested_session_id = state.get('activeSessionId')
                
                # If Website says "ON", we do the monitoring
                if state.get('camera_command') == "ON":
                    if requested_session_id and requested_session_id != active_session_id:
                        active_session_id = requested_session_id
                        camera_started_for_session = False
                        session_frame_count = 0
                        session_score_total = 0.0
                        last_preview_update = 0.0
                        last_preview_data_url = None
                        last_camera_metrics = {}
                        last_frame_score = 100

                    if not camera_started_for_session:
                        camera_started_for_session = cam.start()

                    now = time.time()
                    if cam.available and (now - last_preview_update) >= 2.0:
                        overlay_lines = [
                            "Posture Tracking Live",
                            f"Frame Score: {last_frame_score}%",
                            f"Session Score: {int(round(session_score_total / session_frame_count)) if session_frame_count else 100}%"
                        ]
                        preview_data_url, camera_metrics = cam.capture_preview_and_metrics(overlay_lines=overlay_lines)
                        last_preview_update = now
                        if camera_metrics:
                            last_camera_metrics = camera_metrics
                            last_frame_score = score_from_camera_metrics(camera_metrics)
                            session_frame_count += 1
                            session_score_total += last_frame_score
                            last_preview_data_url = preview_data_url

                            save_reading(active_session_id, {
                                "timestamp": datetime.utcnow(),
                                "frameScore": last_frame_score,
                                "sessionScore": round(session_score_total / session_frame_count, 2),
                                "cameraMetrics": last_camera_metrics,
                                "postureStatus": "Good" if not last_camera_metrics.get('is_bad') else "Bad",
                                "postureReason": last_camera_metrics.get('reason', '')
                            })

                    session_score = int(round(session_score_total / session_frame_count)) if session_frame_count else last_frame_score

                    camera_active = bool(cam.available and camera_started_for_session)

                    # Extract posture status if available (Hailo detection)
                    posture_status = "Good" if not last_camera_metrics.get('is_bad') else "Bad"
                    posture_reason = last_camera_metrics.get('reason', '')

                    live_payload = {
                        "score": session_score,
                        "frameScore": last_frame_score,
                        "sessionScore": session_score,
                        "activeSessionId": active_session_id,
                        "cameraActive": camera_active,
                        "cameraMetrics": last_camera_metrics,
                        "postureStatus": posture_status,
                        "postureReason": posture_reason,
                        "cameraFrame": last_preview_data_url,
                        "updatedAt": int(time.time())
                    }
                    push_live_data(live_payload)

                else:
                    # Website says "OFF", so we just standby quietly
                    if camera_started_for_session:
                        cam.stop()
                        camera_started_for_session = False
                        active_session_id = None
                        session_frame_count = 0
                        session_score_total = 0.0
                        last_preview_update = 0.0
                        last_preview_data_url = None
                        last_camera_metrics = {}
                        last_frame_score = 100
                    
            except Exception as e:
                print(f"Network Error: {e}")

            time.sleep(1)
            
    except KeyboardInterrupt:
        print('Shutting down...')
        if camera_started_for_session:
            cam.stop()

if __name__ == '__main__':
    main_loop()