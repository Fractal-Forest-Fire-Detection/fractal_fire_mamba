import os
import csv
import random
import shutil

# This script simulates the ingestion of real FLAME/UFFD data.
# In a real deployment, this would parse the complex directory structures of FLAME.
# Here, it sets up a standardized "mission file" that the server can read.

REAL_DATA_DIR = "data/real"
IMAGES_DIR = os.path.join(REAL_DATA_DIR, "images")
MISSION_FILE = os.path.join(REAL_DATA_DIR, "real_fire_mission.csv")

def setup_demo_environment():
    """Effectively 'downloads' or sets up the demo data environment"""
    
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
        
    print(f"📂 Simulation Data Directory: {REAL_DATA_DIR}")
    
    # Check if we have sample images, if not, create placeholders
    # In reality, you would copy FLAME .jpgs here
    if not os.listdir(IMAGES_DIR):
        print("⚠️ No real images found. Creating placeholder assets...")
        # Create a dummy "fire" image (just a red square for now, user can replace)
        # We can't actually generate a complex JPG with python stdlib easily without PIL
        # So we'll just assume the user will drop files or we use the placeholder URL
        pass

    # Generate the Mission CSV (Australian Black Summer 2020)
    # Profile: Extreme Heat (40C+), Eucalyptus Oil Saturation, Pyro-Convective Rise
    MISSION_FILE = os.path.join(REAL_DATA_DIR, "black_summer_mission.csv")
    print(f"📝 Generating Black Summer mission file: {MISSION_FILE}")
    
    with open(MISSION_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp_offset', 'node_id', 'thermal_score', 'visual_score', 'image_filename', 'lat', 'lng'])
        
        # 10 minute mission (600 seconds)
        for t in range(600):
            # 1. Baseline: "Catastrophic" Rating (Before Fire)
            # Ambient Temp: 45C, VOCs: High (Eucalyptus), Wind: High
            
            # T=0-180s: Pre-Fire Stress (Hot/Dry/Windy)
            if t < 180:
                # Thermal already high (0.4 = ~40C ambient)
                thermal = 0.4 + random.uniform(-0.02, 0.02)
                visual = 0.1 # Dust/Haze
                img = ""
                
            # T=180s-400s: The "Mega-Fire" Ignition
            # Exponential rise, faster than NIST standard
            elif t < 400:
                progress = (t - 180) / 220.0
                thermal = 0.4 + (progress * 0.6) # Rises to 1.0 (Saturation)
                visual = 0.1 + (progress * 0.9)  # Smoke fills valley
                
                # Image capture during peak
                if t > 250 and t % 10 == 0:
                    img = f"fire_frame_{t}.jpg" 
                else:
                    img = ""
                    
            # T=400s+: Sensor Saturation / Destruction
            else:
                thermal = 1.0 + random.uniform(-0.05, 0.05)
                visual = 1.0
                img = ""
            
            # NSW South Coast Coordinates (approx Batemans Bay)
            lat = -35.714 + (t * 0.00001) 
            lng = 150.179 + (t * 0.00001)
            
            writer.writerow([t, "NODE-NSW-01", f"{thermal:.2f}", f"{visual:.2f}", img, f"{lat:.6f}", f"{lng:.6f}"])

    print("✅ Black Summer scenario ready.")
    print(f"👉 To complete setup: Drop real fire images into {IMAGES_DIR}")

if __name__ == "__main__":
    setup_demo_environment()
