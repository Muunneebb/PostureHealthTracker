#!/usr/bin/env python3
import sys
import os

# Add parent directory to path so we can import hardware modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the hardware main loop
from hardware.src import main as hardware_main

if __name__ == "__main__":
    print("Starting Posture Health Tracker...")
    hardware_main.main_loop()

