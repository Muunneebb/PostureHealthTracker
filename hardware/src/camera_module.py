import time
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
        if not HW:
            return
        try:
            self.picam2 = Picamera2()
            config = self.picam2.create_still_configuration()
            self.picam2.configure(config)
            self.picam2.start()
            self.available = True
        except Exception:
            self.available = False

    def capture(self, path=config.CAMERA_CAPTURE_PATH):
        if not self.available:
            return None
        img = self.picam2.capture_array()
        import cv2
        cv2.imwrite(path, img)
        return path

    def analyze_posture(self, path):
        # If mediapipe available, run pose detection for shoulder/neck alignment
        if not MP_AVAILABLE:
            return {'shoulder_alignment': None, 'neck_angle': None}
        import cv2
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        img = cv2.imread(path)
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
