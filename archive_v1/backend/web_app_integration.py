"""
Integration module for connecting the sensor system to the web application.
This module bridges the main sensor loop with the Flask web app.
"""

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebAppIntegration:
    """Bridge between sensor data collection and web application storage"""
    
    def __init__(self, web_app_url: str = 'http://localhost:5000', timeout: int = 5):
        """
        Initialize the integration module.
        
        Args:
            web_app_url: Base URL of the Flask web application
            timeout: Request timeout in seconds
        """
        self.web_app_url = web_app_url
        self.timeout = timeout
        self.session_id = None
        
    def start_session(self, user_id: int = 1):
        """
        Start a new session in the web application.
        
        Args:
            user_id: The ID of the user to assign the session to (defaults to 1)
            
        Returns:
            Session ID if successful, None otherwise
        """
        try:
            # Login barrier removed in backend, direct POST allowed for hardware
            response = requests.post(
                f'{self.web_app_url}/api/start-session',
                json={'user_id': user_id},
                timeout=self.timeout
            )
            if response.status_code == 201:
                self.session_id = response.json()['session_id']
                logger.info(f'Session started with ID: {self.session_id}')
                return self.session_id
            else:
                logger.error(f'Failed to start session: {response.json()}')
                return None
        except Exception as e:
            logger.error(f'Start session request failed: {e}')
            return None
    
    def send_reading(
        self,
        pitch: float,
        roll: float,
        fsr_left: int,
        fsr_right: int,
        fsr_center: int,
        stress_score: float,
        is_seated: bool,
        buzzer_triggered: bool = False
    ) -> bool:
        """
        Send a sensor reading to the web application.
        """
        if not self.session_id:
            logger.error('No active session. Call start_session first.')
            return False
        
        try:
            reading = {
                'pitch': pitch,
                'roll': roll,
                'fsr_left': fsr_left,
                'fsr_right': fsr_right,
                'fsr_center': fsr_center,
                'stress_score': stress_score,
                'is_seated': is_seated,
                'buzzer_triggered': buzzer_triggered
            }
            
            response = requests.post(
                f'{self.web_app_url}/api/session/{self.session_id}/readings',
                json=reading,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                return True
            else:
                logger.error(f'Failed to send reading: {response.json()}')
                return False
        except Exception as e:
            logger.error(f'Send reading request failed: {e}')
            return False
    
    def end_session(self) -> bool:
        """
        End the current session.
        """
        if not self.session_id:
            logger.error('No active session to end.')
            return False
        
        try:
            response = requests.post(
                f'{self.web_app_url}/api/session/{self.session_id}/end',
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f'Session {self.session_id} ended successfully')
                self.session_id = None
                return True
            else:
                logger.error(f'Failed to end session: {response.json()}')
                return False
        except Exception as e:
            logger.error(f'End session request failed: {e}')
            return False

if __name__ == '__main__':
    print('Web App Integration Module Ready')