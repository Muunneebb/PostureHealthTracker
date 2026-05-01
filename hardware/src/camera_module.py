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
        # Returns posture metrics: either Hailo-style (is_bad/reason) or MediaPipe metrics
        if not MP_AVAILABLE:
            return {'shoulder_alignment': None, 'neck_angle': None, 'is_bad': False, 'reason': ''}
        
        import cv2
        import mediapipe as mp
        
        mp_pose = mp.solutions.pose
        img = cv2.imread(path) if isinstance(path, str) else path
        if img is None:
            return {'shoulder_alignment': None, 'neck_angle': None, 'is_bad': False, 'reason': ''}
        
        img_height, img_width = img.shape[:2]
        
        with mp_pose.Pose(static_image_mode=True) as pose:
            res = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            if not res.pose_landmarks:
                return {'shoulder_alignment': None, 'neck_angle': None, 'is_bad': False, 'reason': ''}
            
            lm = res.pose_landmarks.landmark
            
            # MediaPipe metrics (for scoring compatibility)
            left_sh = lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_sh = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            nose = lm[mp_pose.PoseLandmark.NOSE.value]
            shoulder_alignment = abs(left_sh.y - right_sh.y)
            neck_angle = nose.y - (left_sh.y + right_sh.y) / 2
            
            # Hailo-style side-view posture checks
            left_ear = lm[mp_pose.PoseLandmark.LEFT_EAR.value]
            right_ear = lm[mp_pose.PoseLandmark.RIGHT_EAR.value]
            left_hip = lm[mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = lm[mp_pose.PoseLandmark.RIGHT_HIP.value]
            
            # Convert normalized coords to pixel coords
            def pt_px(lm_point):
                return (int(lm_point.x * img_width), int(lm_point.y * img_height))
            
            ear = pt_px(left_ear) if left_ear.visibility > 0.5 else (pt_px(right_ear) if right_ear.visibility > 0.5 else None)
            shoulder = pt_px(left_sh) if left_sh.visibility > 0.5 else (pt_px(right_sh) if right_sh.visibility > 0.5 else None)
            hip = pt_px(left_hip) if left_hip.visibility > 0.5 else (pt_px(right_hip) if right_hip.visibility > 0.5 else None)
            
            is_bad = False
            reason = ""
            HEAD_FORWARD_THRESHOLD = 12  # pixels
            SHOULDER_FORWARD_THRESHOLD = 18  # pixels
            
            # Check 1: Head forward (ear forward of shoulder)
            if ear and shoulder:
                head_forward = abs(ear[0] - shoulder[0])
                if head_forward > HEAD_FORWARD_THRESHOLD:
                    is_bad = True
                    reason = "Head forward"
            
            # Check 2: Slouching (shoulder forward of hip)
            if shoulder and hip and not is_bad:
                shoulder_forward = abs(shoulder[0] - hip[0])
                if shoulder_forward > SHOULDER_FORWARD_THRESHOLD:
                    is_bad = True
                    reason = "Slouching"
            
            return {
                'shoulder_alignment': shoulder_alignment,
                'neck_angle': neck_angle,
                'is_bad': is_bad,
                'reason': reason
            }
