import time
import os
import json
import shlex
import subprocess
import logging
import traceback
from datetime import datetime
from importlib import import_module
import requests # <-- ADDED: To talk directly to the cloud

# ==========================================
# LOGGING SETUP
# ==========================================
LOG_FILE = "/tmp/posturehealthtracker_main.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
FIREBASE_URL = "https://posturehealthtracker-default-rtdb.europe-west1.firebasedatabase.app"
HAILO_STATUS_FILE = "/tmp/posturehealthtracker_hailo.json"
HAILO_LOG_FILE = "/tmp/posturehealthtracker_hailo.log"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HAILO_EXAMPLES_DIR = os.environ.get("HAILO_EXAMPLES_DIR", os.path.expanduser("~/hailo-rpi5-examples"))

firestore_client = None
hailo_process = None
hailo_log_handle = None


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
        response = requests.put(f"{FIREBASE_URL}/live_data.json", json=payload, timeout=30)
        logger.debug(f"Pushed live_data: score={payload.get('score')}, sessionId={payload.get('activeSessionId')}, status={response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to push live_data: {e}")


def read_hailo_status():
    if not os.path.exists(HAILO_STATUS_FILE):
        return None

    try:
        with open(HAILO_STATUS_FILE, "r", encoding="utf-8") as status_file:
            return json.load(status_file)
    except Exception:
        return None


def start_hailo_process():
    global hailo_process, hailo_log_handle

    if hailo_process and hailo_process.poll() is None:
        return True

    setup_env = os.path.join(HAILO_EXAMPLES_DIR, "setup_env.sh")
    hailo_example = os.path.join(HAILO_EXAMPLES_DIR, "basic_pipelines", "pose_estimation.py")

    if not os.path.exists(setup_env):
        logger.error(f"Hailo setup_env.sh not found at {setup_env}")
        return False

    if not os.path.exists(hailo_example):
        logger.error(f"Hailo example not found at {hailo_example}")
        return False

    command = f"cd {shlex.quote(HAILO_EXAMPLES_DIR)} && source setup_env.sh && python basic_pipelines/pose_estimation.py --input rpi --use-frame"
    logger.info(f"Starting Hailo pipeline with command: {command}")

    try:
        hailo_log_handle = open(HAILO_LOG_FILE, "a", encoding="utf-8")
        hailo_log_handle.write(f"\n=== Starting Hailo pipeline at {datetime.utcnow().isoformat()}Z ===\n")
        hailo_log_handle.flush()
        hailo_process = subprocess.Popen(
            ["bash", "-lc", command],
            stdout=hailo_log_handle,
            stderr=hailo_log_handle,
        )
        logger.info(f"Hailo process started with PID {hailo_process.pid}")
        return True
    except Exception as error:
        logger.error(f"Failed to start Hailo process: {error}\n{traceback.format_exc()}")
        hailo_process = None
        if hailo_log_handle:
            try:
                hailo_log_handle.close()
            except Exception:
                pass
            hailo_log_handle = None
        return False


def stop_hailo_process():
    global hailo_process, hailo_log_handle

    if not hailo_process:
        return

    try:
        if hailo_process.poll() is None:
            logger.info(f"Terminating Hailo process {hailo_process.pid}...")
            hailo_process.terminate()
            try:
                hailo_process.wait(timeout=3)
                logger.info(f"Hailo process terminated gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"Hailo process did not terminate, killing...")
                hailo_process.kill()
                hailo_process.wait(timeout=2)
                logger.info(f"Hailo process killed")
            # Give the OS time to clean up resources (window, etc)
            time.sleep(0.5)
    except Exception as e:
        logger.error(f"Error stopping Hailo process: {e}")
    finally:
        hailo_process = None
        if hailo_log_handle:
            try:
                hailo_log_handle.close()
            except Exception:
                pass
            hailo_log_handle = None


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
    using_hailo_pipeline = False
    session_frame_count = 0
    session_score_total = 0.0
    last_preview_update = 0.0
    last_preview_data_url = None
    last_camera_metrics = {}
    last_frame_score = 100
    last_hailo_update_at = None
    
    logger.info("=" * 70)
    logger.info("Hardware Booted. Connecting to Firebase...")
    logger.info(f"Firebase URL: {FIREBASE_URL}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 70)

    try:
        while True:
            # 2. CHECK THE CLOUD (Did the user click "Start" on the website?)
            try:
                state_resp = requests.get(f"{FIREBASE_URL}/system_state.json", timeout=30)
                state = state_resp.json() or {}
                requested_session_id = state.get('activeSessionId')
                camera_command = state.get('camera_command')
                
                logger.debug(f"Polled system_state: camera_command={camera_command}, activeSessionId={requested_session_id}")
                
                # If Website says "ON", we do the monitoring
                if camera_command == "ON":
                    if requested_session_id and requested_session_id != active_session_id:
                        logger.info(f"New session detected: {requested_session_id}")
                        active_session_id = requested_session_id
                        camera_started_for_session = False
                        using_hailo_pipeline = False
                        session_frame_count = 0
                        session_score_total = 0.0
                        last_preview_update = 0.0
                        last_preview_data_url = None
                        last_camera_metrics = {}
                        last_frame_score = 100
                        last_hailo_update_at = None

                    if not camera_started_for_session:
                        logger.info("Starting camera pipeline...")
                        using_hailo_pipeline = start_hailo_process()
                        if not using_hailo_pipeline:
                            logger.info("Hailo pipeline unavailable; starting Picamera2...")
                            camera_started_for_session = cam.start()
                            logger.info(f"Picamera2 started: {camera_started_for_session}")
                        else:
                            camera_started_for_session = True
                            logger.info("Hailo pipeline started; waiting for live camera frames...")

                    if using_hailo_pipeline:
                        if hailo_process and hailo_process.poll() is not None:
                            logger.warning(f"Hailo pipeline exited with code {hailo_process.returncode}; falling back to Picamera2")
                            stop_hailo_process()
                            using_hailo_pipeline = False
                            camera_started_for_session = cam.start()
                            continue

                        hailo_status = read_hailo_status() or {}
                        hailo_updated_at = hailo_status.get("updatedAt")
                        if hailo_status and hailo_updated_at != last_hailo_update_at:
                            last_hailo_update_at = hailo_updated_at
                            last_preview_data_url = hailo_status.get("cameraFrame", last_preview_data_url)
                            last_camera_metrics = hailo_status.get("cameraMetrics", last_camera_metrics) or {}
                            last_frame_score = score_from_camera_metrics(last_camera_metrics)
                            session_frame_count += 1
                            session_score_total += last_frame_score
                        camera_active = True
                    else:
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

                        camera_active = bool(cam.available and camera_started_for_session)

                    session_score = int(round(session_score_total / session_frame_count)) if session_frame_count else last_frame_score

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
                        stop_hailo_process()
                        camera_started_for_session = False
                        using_hailo_pipeline = False
                        active_session_id = None
                        session_frame_count = 0
                        session_score_total = 0.0
                        last_preview_update = 0.0
                        last_preview_data_url = None
                        last_camera_metrics = {}
                        last_frame_score = 100
                        last_hailo_update_at = None
                    
            except Exception as e:
                logger.error(f"Network/Firebase Error: {e}\n{traceback.format_exc()}")

            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info('Shutting down gracefully...')
        if camera_started_for_session:
            cam.stop()
        stop_hailo_process()
        logger.info('Shutdown complete.')


if __name__ == '__main__':
    main_loop()