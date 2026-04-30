import time
import threading
from src import sensors, display, buzzer, camera_module, utils, config

LOG_PATH = 'posture_stress_log.csv'


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
    # normalize GSR raw (0-65535 for ADS1115 16-bit)
    gsr_norm = gsr_raw / 65535.0 if gsr_raw else 0
    hrv = utils.rmssd(rr_list)
    hrv_norm = 0
    if hrv:
        # lower HRV indicates stress; typical RMSSD range ~ 10-100
        hrv_norm = utils.clamp(1 - (hrv / 100.0), 0, 1)
    # combine: weights can be tuned
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

    try:
        while True:
            imu_read = imu.read_tilt()
            ads_read = ads

            posture = compute_posture_status(imu_read, ads_read)

            hr, rr = max3.read()
            if rr:
                rr_history.extend(rr)
                # keep last 60 intervals
                rr_history = rr_history[-60:]

            gsr = ads.read_gsr()
            stress_score, stress_parts = compute_stress_score(hr, rr_history, gsr)

            lines = [
                f"Posture: {'Seated' if posture['seated'] else 'Away'}",
                f"Pitch:{posture['pitch']:.1f} Fwd:{posture['forward_lean']}",
                f"Slouch:{posture['torso_slouch']} Imbal:{posture['weight_imbalance']}",
                f"Stress:{stress_score:.2f} HRV:{stress_parts.get('hrv')}",
            ]
            oled.show_status(lines)

            # Alerts
            if posture['torso_slouch'] or posture['forward_lean']:
                bz.beep(times=1, duration=0.12)

            if stress_score >= config.STRESS_SCORE_ALERT:
                bz.beep(times=2, duration=0.12)

            # occasional camera validation every 60s
            if cam.available and int(time.time()) % 60 == 0:
                path = cam.capture()
                if path:
                    analysis = cam.analyze_posture(path)
                    print('Camera analysis', analysis)

            # log
            utils.log_row(LOG_PATH, [time.time(), posture['pitch'], posture['roll'], posture['fsr_left'], posture['fsr_right'], posture['fsr_center'], stress_score], header=['ts','pitch','roll','fsr_l','fsr_r','fsr_c','stress'])

            time.sleep(1)
    except KeyboardInterrupt:
        print('Shutting down...')
        bz.cleanup()


if __name__ == '__main__':
    main_loop()
