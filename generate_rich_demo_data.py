import csv
import random
import math

def generate_rich_scenario(filename="full_demo_scenario.csv", duration_sec=600):
    print(f"Generating rich multi-node scenario to {filename}...")
    
    # Node Definitions
    nodes = [
        {"id": "NODE-FIRE-01", "type": "FIRE", "lat": 37.7749, "lng": -122.4194},
        {"id": "NODE-DEAD-02", "type": "DEATH", "lat": 37.7800, "lng": -122.4200},
        {"id": "NODE-SAFE-03", "type": "SAFE",  "lat": 37.7700, "lng": -122.4100}
    ]
    
    # Physics constants
    alpha = 0.0469 # Fast fire growth
    t_ignition = 120 # Fire starts at 2 minutes
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp_now', 'node_id', 'lat', 'lng', 'battery', 'voc', 'smoke', 'temp', 'image_url'])
        
        for t in range(duration_sec):
            # Simulation time
            
            for node in nodes:
                # Base drift (GPS noise)
                lat = node['lat'] + random.uniform(-0.0001, 0.0001)
                lng = node['lng'] + random.uniform(-0.0001, 0.0001)
                
                # --- SENSOR SIMULATION ---
                voc = 0.1
                smoke = 0.0
                temp = 0.5
                image_url = ""
                battery = 100.0
                
                if node['type'] == "FIRE":
                    # NIST Fire Curve Logic
                    if t > t_ignition:
                        Q = alpha * ((t - t_ignition) ** 2)
                        intensity = min(Q / 1000.0, 1.0)
                        
                        voc = 0.1 + (intensity * 0.9)
                        smoke = 0.0 + (intensity * 1.0)
                        temp = 0.5 + (intensity * 0.5)
                        
                        # Generate "Image" event every 30s during fire
                        if intensity > 0.3 and (t % 30 == 0):
                            # In a real app these would be paths to assets
                            image_url = f"/assets/fire_detection_{t}.jpg"
                    
                elif node['type'] == "DEATH":
                    # Rapid battery drain
                    # Dies at t=300
                    if t < 300:
                        battery = 100 - (t / 300.0 * 100)
                    else:
                        battery = 0
                        # Node stops transmitting? 
                        # For CSV simplicity, we record 0 battery rows to signify "Last known state"
                        
                elif node['type'] == "SAFE":
                    # Just noise
                    voc = 0.1 + random.uniform(-0.05, 0.05)
                    smoke = 0.0
                    temp = 0.5 + random.uniform(-0.02, 0.02)
                
                # Clamp
                voc = max(0.0, min(1.0, voc))
                smoke = max(0.0, min(1.0, smoke))
                temp = max(0.0, min(1.0, temp))
                
                row = [
                    t,
                    node['id'],
                    lat, lng,
                    f"{battery:.1f}",
                    f"{voc:.3f}",
                    f"{smoke:.3f}",
                    f"{temp:.3f}",
                    image_url
                ]
                writer.writerow(row)
                
    print("✅ Rich scenario generation complete.")

if __name__ == "__main__":
    generate_rich_scenario()
