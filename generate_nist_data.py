import csv
import math
import random
import os

def generate_nist_curve(filename="nist_fire_curve.csv", duration_sec=600):
    """
    Generates a fire growth curve based on NIST t^2 alpha-mode.
    Alpha modes: Slow, Medium, Fast, Ultra-Fast.
    We'll use 'Fast' (0.0469 kW/s^2) typically for wood/furniture.
    """
    
    print(f"Generating physics-based fire data to {filename}...")
    
    alpha = 0.0469  # Fast growth
    t_ignition = 60 # Start fire at 60s
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(['timestamp_offset', 'bme680_voc', 'ccs811_tvoc', 'camera_smoke', 'camera_brightness', 'soil_moisture', 'dht_temp'])
        
        for t in range(duration_sec):
            # 1. Physics Model (Heat Release Rate)
            if t < t_ignition:
                Q = 0
            else:
                Q = alpha * ((t - t_ignition) ** 2)
            
            # 2. Map HRR to Sensors (Simulated Transfer Function)
            # Max HRR for this 'sensor saturation' point: 1000 kW (approx small room flashover)
            saturation_point = 1000.0 
            intensity = min(Q / saturation_point, 1.0)
            
            # Noise generator
            noise = lambda amp: random.uniform(-amp, amp)
            
            # Base values
            base_temp = 0.4 # ~25C normalized
            base_voc = 0.1
            base_smoke = 0.0
            
            # --- Sensor Response Simulation ---
            
            # Temperature: Lagged response, proportional to intensity
            # Simple simulation: temp follows intensity with some inertia? 
            # For simplicity, map directly + noise.
            temp_val = base_temp + (intensity * 0.6) + noise(0.01)
            
            # Smoke: Rises sharply once fire starts (smoldering phase simulation)
            # In real life, smoke often precedes significant heat in smoldering.
            # We'll add a 'smoldering' coefficient for 60s-120s
            smolder = 0.0
            if t > t_ignition and t < t_ignition + 60:
                smolder = (t - t_ignition) / 60.0 * 0.3 # Rise to 30% during start
            
            smoke_val = base_smoke + smolder + (intensity * 0.9) + noise(0.02)
            
            # VOC: Sensitive, spikes early
            voc_val = base_voc + smolder * 1.5 + (intensity * 0.8) + noise(0.05)
            
            # Brightness: Only visible when flames appear (later stage)
            # Say flames visible when Q > 50 kW
            flames_visible = Q > 50
            brightness_val = 0.2 + (0.8 * intensity if flames_visible else 0.0) + noise(0.01)
            
            # Soil Moisture: Dries out slowly
            moisture_val = 0.4 - (intensity * 0.1) + noise(0.01)
            
            # Clamp all 0.0 - 1.0
            row = [
                t,
                max(0.0, min(1.0, voc_val)),
                max(0.0, min(1.0, voc_val)), # TVOC similar to VOC
                max(0.0, min(1.0, smoke_val)),
                max(0.0, min(1.0, brightness_val)),
                max(0.0, min(1.0, moisture_val)),
                max(0.0, min(1.0, temp_val))
            ]
            
            writer.writerow(row)
            
    print("✅ Data generation complete.")

if __name__ == "__main__":
    generate_nist_curve()
