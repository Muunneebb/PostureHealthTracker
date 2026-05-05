from pathlib import Path
import base64
import json
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os, sys, signal, math, time
import numpy as np
import cv2
import hailo
from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad, get_numpy_from_buffer
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.apps.pose_estimation.pose_estimation_pipeline import GStreamerPoseEstimationApp

STATUS_FILE = Path('/tmp/posturehealthtracker_hailo.json')

# ── Side view thresholds ────────────────────────
HEAD_FORWARD_THRESHOLD     = 12 # pixels — how far ear is in front of shoulder
SHOULDER_FORWARD_THRESHOLD = 18  # pixels — how far shoulder is in front of hip
BAD_POSTURE_SECONDS        = 2

bad_start = None
alerting  = False

def quit_handler(signum=None, frame=None):
    print("\nClosing...")
    os._exit(0)

signal.signal(signal.SIGINT, quit_handler)

def check_posture_side(kps, w, h):
    def pt(n):
        p = kps.get(n)
        if p is None: return None
        return (int(p[0]*w), int(p[1]*h))

    # Use whichever side is more visible (use both, prefer the visible one)
    l_ear = pt('left_ear');     r_ear = pt('right_ear')
    l_sh  = pt('left_shoulder'); r_sh = pt('right_shoulder')
    l_hip = pt('left_hip');     r_hip = pt('right_hip')

    ear      = l_ear or r_ear
    shoulder = l_sh  or r_sh
    hip      = l_hip or r_hip

    bad = False
    reason = ""

    # Check 1: Head forward (ear forward of shoulder horizontally)
    if ear and shoulder:
        head_forward = abs(ear[0] - shoulder[0])
        if head_forward > HEAD_FORWARD_THRESHOLD:
            bad = True
            reason = "Head forward"

    # Check 2: Shoulder forward / slouching (shoulder forward of hip)
    if shoulder and hip:
        shoulder_forward = abs(shoulder[0] - hip[0])
        if shoulder_forward > SHOULDER_FORWARD_THRESHOLD:
            bad = True
            reason = "Slouching"

    return bad, reason

def draw_ui(frame, is_bad, alert, reason, w, h):
    color = (0, 0, 220) if is_bad else (50, 205, 50)
    label = "BAD POSTURE" if is_bad else "GOOD POSTURE"
    cv2.rectangle(frame, (0, 0), (w, 80), (20, 20, 20), -1)
    tw = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 1.8, 3)[0][0]
    cv2.putText(frame, label, ((w-tw)//2, 58),
                cv2.FONT_HERSHEY_DUPLEX, 1.8, color, 3)
    if reason and is_bad:
        cv2.putText(frame, reason, (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,165,255), 2)
    cv2.putText(frame, "Press Ctrl+C in terminal to quit", (w-380, h-15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
    if alert:
        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (w,h), (0,0,180), -1)
        cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
        msg = "! SIT UP STRAIGHT !"
        mw = cv2.getTextSize(msg, cv2.FONT_HERSHEY_DUPLEX, 1.4, 3)[0][0]
        cv2.putText(frame, msg, ((w-mw)//2, h-50),
                    cv2.FONT_HERSHEY_DUPLEX, 1.4, (0,0,255), 4)
        cv2.putText(frame, msg, ((w-mw)//2, h-50),
                    cv2.FONT_HERSHEY_DUPLEX, 1.4, (255,255,255), 2)

def publish_status(frame, is_bad, reason, w, h):
    preview = frame
    if preview is not None and len(preview.shape) == 3:
        height, width = preview.shape[:2]
        # Use a smaller preview to reduce bandwidth and improve responsiveness
        target_width = 300
        if width > target_width:
            target_height = int(height * (target_width / width))
            preview = cv2.resize(preview, (target_width, target_height))

    if preview is None:
        return

    ok, buffer = cv2.imencode('.jpg', preview, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
    if not ok:
        return

    payload = {
        'score': 95 if not is_bad else 55,
        'frameScore': 95 if not is_bad else 55,
        'sessionScore': 95 if not is_bad else 55,
        'cameraActive': True,
        'cameraFrame': 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('ascii'),
        'cameraMetrics': {
            'is_bad': is_bad,
            'reason': reason,
        },
        'postureStatus': 'Good' if not is_bad else 'Bad',
        'postureReason': reason,
        'updatedAt': int(time.time())
    }

    try:
        STATUS_FILE.write_text(json.dumps(payload))
    except Exception:
        pass

    # Also write a compact binary JPEG for local serving (faster than base64 over RTDB)
    try:
        with open('/tmp/posturehealthtracker_frame.jpg', 'wb') as f:
            f.write(buffer.tobytes())
    except Exception:
        pass

def get_keypoints():
    return {
        'nose': 0,
        'left_eye': 1, 'right_eye': 2,
        'left_ear': 3, 'right_ear': 4,
        'left_shoulder': 5, 'right_shoulder': 6,
        'left_elbow': 7, 'right_elbow': 8,
        'left_wrist': 9, 'right_wrist': 10,
        'left_hip': 11, 'right_hip': 12,
        'left_knee': 13, 'right_knee': 14,
        'left_ankle': 15, 'right_ankle': 16,
    }

class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.use_frame = True
        self.frame_count = 0
        # Publish status every 2 frames to improve perceived responsiveness
        self.publish_interval = 2

def app_callback(pad, info, user_data):
    global bad_start, alerting
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK

    user_data.increment()
    format, width, height = get_caps_from_pad(pad)
    frame = None
    if user_data.use_frame and format and width and height:
        frame = get_numpy_from_buffer(buffer, format, width, height)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    roi        = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    kp_map     = get_keypoints()
    now        = time.time()
    found      = False

    for detection in detections:
        if detection.get_label() != "person":
            continue
        bbox      = detection.get_bbox()
        landmarks = detection.get_objects_typed(hailo.HAILO_LANDMARKS)
        if not landmarks:
            continue
        found  = True
        points = landmarks[0].get_points()
        kps    = {}
        for name, idx in kp_map.items():
            if idx < len(points):
                p = points[idx]
                kps[name] = (
                    p.x() * bbox.width()  + bbox.xmin(),
                    p.y() * bbox.height() + bbox.ymin()
                )

        is_bad, reason = check_posture_side(kps, width, height)
        if is_bad:
            if bad_start is None:
                bad_start = now
            alerting = (now - bad_start) >= BAD_POSTURE_SECONDS
        else:
            bad_start = None
            alerting  = False

        if frame is not None:
            draw_ui(frame, is_bad, alerting, reason, width, height)
            # Only publish status every N frames to reduce I/O and lag
            user_data.frame_count += 1
            if user_data.frame_count % user_data.publish_interval == 0:
                publish_status(frame, is_bad, reason, width, height)
        break

    if not found and frame is not None:
        bad_start = None
        alerting  = False
        cv2.putText(frame, "No person detected", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,165,255), 2)
        publish_status(frame, False, 'No person detected', width, height)

    if frame is not None:
        user_data.set_frame(frame)

    return Gst.PadProbeReturn.OK

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    env_file     = project_root / ".env"
    os.environ["HAILO_ENV_FILE"] = str(env_file)
    user_data = user_app_callback_class()
    app = GStreamerPoseEstimationApp(app_callback, user_data)
    try:
        app.run()
    except KeyboardInterrupt:
        os._exit(0)
