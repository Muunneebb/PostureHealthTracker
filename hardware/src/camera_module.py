import time
import base64
from . import config

try:
    from picamera2 import Picamera2
    import cv2
    import numpy as np
    HW = True
except Exception:
    HW = False

try:
    import mediapipe as mp
    MP_AVAILABLE = True
except Exception:
    MP_AVAILABLE = False


class CameraModule:
    def __init__(self):
        self.available = False
        self.picam2 = None

    def start(self):
        if not HW or self.available:
            return self.available
        try:
            self.picam2 = Picamera2()
            camera_config = self.picam2.create_still_configuration()
            self.picam2.configure(camera_config)
            self.picam2.start()
            self.available = True
        except Exception:
            self.available = False
            self.picam2 = None
        return self.available

    def stop(self):
        if not self.available or self.picam2 is None:
            return
        try:
            self.picam2.stop()
        except Exception:
            pass
        self.available = False

    def capture(self, path=config.CAMERA_CAPTURE_PATH):
        if not self.available and not self.start():
            return None
        img = self.picam2.capture_array()
        import cv2
        cv2.imwrite(path, img)
        return path

    def capture_preview_and_metrics(self, overlay_lines=None):
        if not self.available and not self.start():
            return None, {}

        import cv2

        frame = self.picam2.capture_array()
        metrics = self.analyze_posture(frame)

        preview = frame
        if preview is not None and len(preview.shape) == 3 and preview.shape[1] > 400:
            height, width = preview.shape[:2]
            target_width = 360
            target_height = int(height * (target_width / width))
            preview = cv2.resize(preview, (target_width, target_height))

        if preview is not None and overlay_lines:
            y = 22
            for line in overlay_lines:
                cv2.putText(preview, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
                y += 22

        ok, buffer = cv2.imencode('.jpg', preview, [int(cv2.IMWRITE_JPEG_QUALITY), 72])
        if not ok:
            return None, metrics or {}

        preview_data_url = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('ascii')
        return preview_data_url, metrics or {}

    def analyze_posture(self, path):
        # If mediapipe available, run pose detection for shoulder/neck alignment
        if not MP_AVAILABLE:
            return {'shoulder_alignment': None, 'neck_angle': None}
        import cv2
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        img = cv2.imread(path) if isinstance(path, str) else path
        if img is None:
            return {'shoulder_alignment': None, 'neck_angle': None}
        with mp_pose.Pose(static_image_mode=True) as pose:
            res = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            if not res.pose_landmarks:
                return {'shoulder_alignment': None, 'neck_angle': None}
            lm = res.pose_landmarks.landmark
            # use shoulders and nose for simple angles
            left_sh = lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_sh = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            nose = lm[mp_pose.PoseLandmark.NOSE.value]
            shoulder_angle = abs(left_sh.y - right_sh.y)
            neck_angle = nose.y - (left_sh.y+right_sh.y)/2
            return {'shoulder_alignment': shoulder_angle, 'neck_angle': neck_angle}
