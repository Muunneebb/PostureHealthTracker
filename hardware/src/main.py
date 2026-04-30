import time
import threading
import requests # <-- ADDED: To talk directly to the cloud
from src import sensors, display, buzzer, camera_module, utils, config

LOG_PATH = 'posture_stress_log.csv'

# ==========================================
# FIREBASE CLOUD LINK
# ==========================================
# This connects your Pi directly to the website without Flask
FIREBASE_URL = "https://posturehealthtracker-default-rtdb.firebaseio.com"

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
                
                # If Website says "ON", we do the monitoring
                if state.get('camera_command') == "ON":
                    
                    # -- Update the Website Live Data --
                    live_payload = {
                        "pitch": round(posture['pitch'], 1),
                        "roll": round(posture['roll'], 1),
                        "stress": round(stress_score, 2),
                        "score": ui_score
                    }
                    requests.put(f"{FIREBASE_URL}/live_data.json", json=live_payload, timeout=2)
                    
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

                    # -- Camera Analysis --
                    if cam.available and int(time.time()) % 60 == 0:
                        path = cam.capture()
                        if path:
                            cam.analyze_posture(path)
                            
                else:
                    # Website says "OFF", so we just standby quietly
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