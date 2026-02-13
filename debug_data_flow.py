import sys
import os
import time
import csv
from datetime import datetime

# Mimic the server setup
class MockReading:
    def __init__(self, val, reliability=0.9, extra=None):
        self.value = float(val)
        self.is_valid = True
        self.is_imputed = False
        self.reliability_score = reliability
        self.extra_metadata = extra or {}

class RealDataInterface:
    def __init__(self, mission_file="data/real/black_summer_mission.csv"):
        self.data_rows = []
        self.current_idx = 0
        try:
            print(f"DEBUG: Opening file {mission_file}...")
            with open(mission_file, 'r') as f:
                reader = csv.DictReader(f)
                self.data_rows = list(reader)
            print(f"✅ Loaded {len(self.data_rows)} frames of BLACK SUMMER MEGA-FIRE data.")
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            self.data_rows = []

    def read_sensors(self):
        if not self.data_rows:
            print("DEBUG: No data rows available.")
            return {}

        row = self.data_rows[self.current_idx]
        print(f"DEBUG: Processing row {self.current_idx}/{len(self.data_rows)}")
        self.current_idx = (self.current_idx + 1) % len(self.data_rows)
        
        thermal_val = float(row['thermal_score'])
        visual_val = float(row['visual_score'])
        
        return {
            'camera_smoke': MockReading(visual_val),
            'dht_temp': MockReading(0.5 + (thermal_val * 0.5)),
        }

if __name__ == "__main__":
    print("Starting debug data flow test...")
    try:
        interface = RealDataInterface()
        for i in range(5):
            print(f"\n--- Iteration {i+1} ---")
            sensors = interface.read_sensors()
            print(f"Sensors read: {sensors}")
            if sensors:
                 print(f"Smoke: {sensors['camera_smoke'].value}")
    except Exception as e:
        print(f"CRITICAL FAIL: {e}")
