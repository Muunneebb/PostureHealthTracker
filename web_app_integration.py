"""
Integration module for connecting the sensor system to the web application.
This module bridges the main sensor loop with the Flask web app.
"""

import requests
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
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
        self.session_id: Optional[int] = None
        self.session_token: Optional[str] = None
        
    def login(self, username: str, password: str) -> bool:
        """
        Login to the web application.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            response = requests.post(
                f'{self.web_app_url}/login',
                json={'username': username, 'password': password},
                timeout=self.timeout
            )
            if response.status_code == 200:
                logger.info(f'Login successful for user: {username}')
                return True
            else:
                logger.error(f'Login failed: {response.json().get("error")}')
                return False
        except Exception as e:
            logger.error(f'Login request failed: {e}')
            return False
    
    def start_session(self, session_token: str) -> Optional[int]:
        """
        Start a new session in the web application.
        
        Args:
            session_token: Session token from authentication
            
        Returns:
            Session ID if successful, None otherwise
        """
        try:
            response = requests.post(
                f'{self.web_app_url}/api/start-session',
                timeout=self.timeout,
                cookies={'session': session_token}
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
        buzzer_triggered: bool = False,
        session_token: str = None
    ) -> bool:
        """
        Send a sensor reading to the web application.
        
        Args:
            pitch: Pitch angle in degrees
            roll: Roll angle in degrees
            fsr_left: Left FSR sensor value
            fsr_right: Right FSR sensor value
            fsr_center: Center FSR sensor value
            stress_score: Calculated stress score (0-1)
            is_seated: Whether the user is seated
            buzzer_triggered: Whether buzzer triggered this reading
            session_token: Session token for authentication
            
        Returns:
            True if successful, False otherwise
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
            
            cookies = {'session': session_token} if session_token else {}
            
            response = requests.post(
                f'{self.web_app_url}/api/session/{self.session_id}/readings',
                json=reading,
                timeout=self.timeout,
                cookies=cookies
            )
            
            if response.status_code == 201:
                return True
            else:
                logger.error(f'Failed to send reading: {response.json()}')
                return False
        except Exception as e:
            logger.error(f'Send reading request failed: {e}')
            return False
    
    def end_session(self, session_token: str = None) -> bool:
        """
        End the current session.
        
        Args:
            session_token: Session token for authentication
            
        Returns:
            True if successful, False otherwise
        """
        if not self.session_id:
            logger.error('No active session to end.')
            return False
        
        try:
            cookies = {'session': session_token} if session_token else {}
            
            response = requests.post(
                f'{self.web_app_url}/api/session/{self.session_id}/end',
                timeout=self.timeout,
                cookies=cookies
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
    
    def get_session_stats(self, session_token: str = None) -> Optional[Dict[str, Any]]:
        """
        Get current session statistics.
        
        Args:
            session_token: Session token for authentication
            
        Returns:
            Dictionary with session stats or None if failed
        """
        if not self.session_id:
            logger.error('No active session.')
            return None
        
        try:
            cookies = {'session': session_token} if session_token else {}
            
            response = requests.get(
                f'{self.web_app_url}/api/session/{self.session_id}/stats',
                timeout=self.timeout,
                cookies=cookies
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f'Failed to get stats: {response.json()}')
                return None
        except Exception as e:
            logger.error(f'Get stats request failed: {e}')
            return None


# Example usage in main sensor loop
def integrate_with_sensor_loop(
    sensor_loop_function,
    web_app_url: str = 'http://localhost:5000',
    username: str = 'test_user',
    password: str = 'test_password'
):
    """
    Example function showing how to integrate the web app with sensor loop.
    
    Args:
        sensor_loop_function: The main sensor loop function from main.py
        web_app_url: Base URL of the Flask web application
        username: Username for web app login
        password: Password for web app login
    """
    integration = WebAppIntegration(web_app_url)
    
    # Login to web app
    if not integration.login(username, password):
        logger.error('Failed to login to web app')
        return
    
    # Start a session
    if not integration.start_session():
        logger.error('Failed to start web session')
        return
    
    logger.info('Web app integration initialized successfully')
    
    # Note: In your actual main_loop(), you would call:
    # integration.send_reading(pitch, roll, fsr_left, fsr_right, fsr_center, stress_score, seated, buzzer_triggered)
    # At the end: integration.end_session()


if __name__ == '__main__':
    # Test the integration
    print('Web App Integration Module')
    print('=' * 50)
    print('This module provides integration between the sensor')
    print('data collection system and the Flask web application.')
    print('')
    print('Usage in main.py:')
    print('  from web_app_integration import WebAppIntegration')
    print('  integration = WebAppIntegration("http://localhost:5000")')
    print('  integration.login("username", "password")')
    print('  integration.start_session()')
    print('  # In sensor loop:')
    print('  integration.send_reading(...)')
    print('  integration.end_session()')
