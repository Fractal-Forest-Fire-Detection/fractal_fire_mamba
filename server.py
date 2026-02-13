
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, RedirectResponse
import sys
import os
import random
import time
from datetime import datetime
from threading import Thread
from typing import Dict, Any

# Ensure we can import from core/phases
sys.path.append(os.getcwd())

print("DEBUG: importing Phase0FusionEngineWithMamba...")
try:
    from phases.phase0_fusion.fusion_with_mamba import Phase0FusionEngineWithMamba
    print("DEBUG: importing Phase2FractalGate...")
    from phases.phase2_fractal.fractal_gate import Phase2FractalGate
    print("DEBUG: importing Phase3ChaosKernel...")
    from phases.phase3_chaos.chaos_kernel import Phase3ChaosKernel
    print("DEBUG: importing EnvironmentalState...")
    from core.environmental_state import EnvironmentalState
except ImportError as e:
    print(f"❌ Error importing model components: {e}")
    print("Please verify your python path includes the project root.")
    # Fallback
    Phase0FusionEngineWithMamba = None
    Phase2FractalGate = None
    Phase3ChaosKernel = None

print("DEBUG: initializing FastAPI app...")
app = FastAPI(title="Fractal Fire Mamba API")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# REAL DATA INTERFACE (FLAME/UFFD Ingestion)
# ============================================================================
import csv

# Helper Class for validation format
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
        # Start closer to the event for demo (skip first ~4 mins of low risk)
        self.current_idx = 230 
        try:
            with open(mission_file, 'r') as f:
                reader = csv.DictReader(f)
                self.data_rows = list(reader)
            print(f"✅ Loaded {len(self.data_rows)} frames of BLACK SUMMER MEGA-FIRE data.")
        except FileNotFoundError:
            print(f"⚠️  Mission file {mission_file} not found. Running setup script...")
            # Fallback: generating on the fly if missing
            self.data_rows = []

        # Fallback if file load failed
        if not self.data_rows:
            print("⚠️  No data loaded. System will run in IDLE mode.")
            self.fallback = None
        else:
            self.fallback = None

    def read_sensors(self) -> Dict:
        """Stream next row from Real Data CSV"""
        if not self.data_rows:
            # Safe default if no data
            return {
                'VOC': None,
                'SMOKE': None,
                'TEMPERATURE': None,
                'CAMERA_BRIGHTNESS': None
            }

        row = self.data_rows[self.current_idx]
        
        # Advance index (loop back to start for booth demo)
        self.current_idx = (self.current_idx + 1) % len(self.data_rows)
        
        # Parse Real Values
        thermal_val = float(row['thermal_score'])
        visual_val = float(row['visual_score'])
        lat_val = float(row.get('lat', -35.714)) # Default to first row if missing
        lng_val = float(row.get('lng', 150.179))
        


        # Construct image URL if present
        img_url = ""
        if row['image_filename']:
            # Points to the static file server route
            img_url = f"/api/images/{row['image_filename']}"

        return {
            # Normalize keys to match Processor expectations
            'VOC': MockReading(100.0 + (thermal_val * 400.0)), # Scale to 100-500 PPM
            'TERPENE': MockReading(50.0 + (thermal_val * 250.0)), # Scale to 50-300 PPM
            
            # Smoke presence from Visual Score
            'SMOKE': MockReading(visual_val),
            
            # Brightness tracks thermal intensity
            'CAMERA_BRIGHTNESS': MockReading(thermal_val),
            
            'SOIL_MOISTURE': MockReading(30.0 - (thermal_val * 20.0)), # 30% -> 10% (Critical)
            'TEMPERATURE': MockReading(25.0 + (thermal_val * 50.0)), # Map 0-1 score to 25-75C range
            'HUMIDITY': MockReading(50.0 - (thermal_val * 40.0)), # Map to 50-10% humidity
            
            # Pass image URL through a hidden channel (state metadata)
            '_image_url': img_url,
            '_location': {'latitude': lat_val, 'longitude': lng_val}
        }

# Global System State
class SystemState:
    def __init__(self):
        self.fusion_engine = Phase0FusionEngineWithMamba() if Phase0FusionEngineWithMamba else None
        self.fractal_gate = Phase2FractalGate() if Phase2FractalGate else None
        self.chaos_kernel = Phase3ChaosKernel() if Phase3ChaosKernel else None
        
        # Use Real Data Interface
        self.sensor_interface = RealDataInterface()
        
        self.history = []
        self.latest_state = None
        self.latest_location = {"latitude": -35.714, "longitude": 150.179} # Default Australia (Black Summer)
        self.latest_image = None
        self.latest_fractal = None
        self.latest_chaos = None
        self.running = False

system = SystemState()

# Background Task for Continuous Monitoring
def background_monitor():
    print("Starting background monitoring loop...")
    while system.running and system.fusion_engine:
        try:
            # 1. Read Sensors
            raw_sensors = system.sensor_interface.read_sensors()
            
            # Skip if no data
            if not raw_sensors or raw_sensors.get('SMOKE') is None:
                time.sleep(1.0)
                continue
            
            # Extract hidden image URL if present
            if '_image_url' in raw_sensors:
                img_url = raw_sensors.pop('_image_url')
                if img_url:
                    system.latest_image = {
                        "id": int(time.time()),
                        "timestamp": datetime.now().isoformat(),
                        "confidence": 0.95, 
                        "image_url": img_url,
                    }
            
            # Extract Location if present
            if '_location' in raw_sensors:
                loc = raw_sensors.pop('_location')
                if loc:
                     system.latest_location = loc
                     # Also update image location if just captured
                     if system.latest_image:
                         system.latest_image["location"] = loc

            # 2. Fuse (Phase-0 with Mamba)
            state = system.fusion_engine.fuse(
                validated_sensors=raw_sensors,
                phase1_stats={'trauma_level': 0.0}
            )
            # Update Global State
            system.latest_state = state

            # 3. Phase-2: Fractal Gate
            if system.fractal_gate:
                fractal_result = system.fractal_gate.update(
                    risk_score=state.fire_risk_score,
                    timestamp=state.timestamp,
                    trauma_level=0.0
                )
                system.latest_fractal = fractal_result
            
            # 4. Phase-3: Chaos Kernel
            if system.chaos_kernel:
                chaos_result = system.chaos_kernel.update(
                    risk_score=state.fire_risk_score,
                    temporal_trend=state.temporal_metadata.get('chemical_trend', 0.0), # Use trend from Mamba
                    timestamp=state.timestamp
                )
                system.latest_chaos = chaos_result

            # 5. Store History
            # Extract raw values for CSV (since state might normalized them or omit them)
            raw_temp = raw_sensors.get('TEMPERATURE', object()).value if 'TEMPERATURE' in raw_sensors else 0.0
            
            history_point = {
                'timestamp': state.timestamp.isoformat(),
                'fused_score': state.fire_risk_score,
                'chemical': state.chemical_state.get('voc_level', 0),
                'visual': state.visual_state.get('smoke_presence', 0),
                'temp': raw_temp, 
                'env_score': state.environmental_context.get('ignition_susceptibility', 0),
                'hurst': float(system.latest_fractal.hurst_exponent) if system.latest_fractal else 0.5,
                'lyapunov': float(system.latest_chaos.lyapunov_exponent) if system.latest_chaos else 0.0
            }
            system.history.append(history_point)
            if len(system.history) > 100:
                system.history.pop(0)
                
            time.sleep(1.0)
            
        except Exception as e:
            print(f"Error in monitor loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1.0)

# Lifecycle Events
@app.on_event("startup")
async def startup_event():
    if not system.fusion_engine:
        print("⚠️  Warning: Fusion engine failed to load.")
        return
    system.running = True
    thread = Thread(target=background_monitor, daemon=True)
    thread.start()

@app.on_event("shutdown")
async def shutdown_event():
    system.running = False

# API Endpoints

@app.get("/api/status")
async def get_status():
    """Get current system status enriched with Fractal and Chaos metrics"""
    if not system.latest_state:

        return {
            "node_id": "Initializing...", 
            "risk_tier": "WAITING", 
            "mamba_ssm": {}, 
            "fractal": {}, 
            "chaos": {},
            "vision": {
                "visual_score": 0.0,
                "vision_mode": "—",
                "camera_health": {"health_score": "—"}
            },
            "components": {},
            "system_status": None
        }
    
    s = system.latest_state
    mamba_meta = getattr(s, 'temporal_metadata', {})
    
    # Calculate component scores for breakdown
    # (Assuming simple 0-1 range from state dicts)
    chem_score = s.chemical_state.get('voc_level', 0.0)
    vis_score = s.visual_state.get('smoke_presence', 0.0)
    env_score = s.environmental_context.get('ignition_susceptibility', 0.0)
    
    
    # Determine Active Phase and Weights for Explainability
    active_phase = "Phase-0: Watchdog"
    weights = {"visual": 30, "thermal": 30, "chemical": 40} # Default monitoring
    
    if s.fire_detected:
         active_phase = "Phase-6: EVACUATE"
    elif system.latest_image: # Camera woke up
         active_phase = "Phase-4: Vision Confirmation"
         weights = {"visual": 50, "thermal": 30, "chemical": 20} # User requested weights
    elif system.latest_chaos and system.latest_chaos.is_unstable:
         active_phase = "Phase-3: Chaos Kernel"
    elif system.latest_fractal and system.latest_fractal.has_structure:
         active_phase = "Phase-2: Fractal Gate"

    response = {
        "node_id": "NODE-001",
        "timestamp": s.timestamp.isoformat(),
        "risk_tier": s.get_risk_level(),
        "fire_detected": s.fire_detected,
        "location": system.latest_location,
        
        # NEW: System Status for UI
        "system_status": {
            "phase": active_phase,
            "final_risk": float(f"{s.fire_risk_score:.2f}"),
            "weights": weights
        },
        
        # Phase-0: Mamba Fusion
        "mamba_ssm": {
            "fused_score": float(f"{s.fire_risk_score:.2f}"),
            "temporal_confidence": f"{mamba_meta.get('confidence', s.overall_confidence):.0%}",
            "cross_modal_lag": float(f"{mamba_meta.get('cross_modal_lag', 0.0):.1f}"),
            "chemical_trend": float(f"{mamba_meta.get('chemical_trend', 0.0):.2f}"),
            "visual_trend": float(f"{mamba_meta.get('visual_trend', 0.0):.2f}"),
            "persistence": f"{mamba_meta.get('persistence', 0.0):.0%}",
        },
        
        # Phase-2: Fractal Gate
        "fractal": {
            "hurst": float(f"{system.latest_fractal.hurst_exponent:.2f}") if system.latest_fractal else 0.5,
            "has_structure": bool(system.latest_fractal.has_structure) if system.latest_fractal else False,
            "status": "STRUCTURED" if (system.latest_fractal and system.latest_fractal.has_structure) else "RANDOM",
            "val": float(f"{system.latest_fractal.hurst_exponent:.2f}") if system.latest_fractal else 0.5
        },
        
        # Phase-3: Chaos Kernel
        "chaos": {
            "lyapunov": float(f"{system.latest_chaos.lyapunov_exponent:.2f}") if system.latest_chaos else 0.0,
            "is_unstable": bool(system.latest_chaos.is_unstable) if system.latest_chaos else False,
            "status": "UNSTABLE" if (system.latest_chaos and system.latest_chaos.is_unstable) else "STABLE",
            "val": float(f"{system.latest_chaos.lyapunov_exponent:.2f}") if system.latest_chaos else 0.0
        },
        
        # Component Breakdown
        "components": {
            "chemical": float(f"{chem_score:.2f}"),
            "visual": float(f"{vis_score:.2f}"),
            "environmental": float(f"{env_score:.2f}")
        },
        
        "vision": {
            "vision_mode": "day",
            "camera_health": {"health_score": "100%"},
            "visual_score": float(vis_score)
        },
        "chemical": s.chemical_state,
        "environmental": s.environmental_context,
        "agreement": float(f"{s.cross_modal_agreement:.2f}")
    }
    return response

@app.get("/api/history")
async def get_history():
    return {"series": system.history}

@app.get("/api/alerts")
async def get_alerts():
    """Phase-5: Logical Gate (Witness Protocol) & Phase-6: Communication"""
    alerts = []
    # DIAGRAM LOGIC: "Trigger: Risk > 90%"
    if system.latest_state and system.latest_state.fire_risk_score > 0.8: # Using 0.8 as orange/red threshold
        # Jitter location slightly to simulate different detections or GPS noise
        lat = getattr(system, 'current_location', {}).get('latitude', 37.7749) + random.uniform(-0.005, 0.005)
        lng = getattr(system, 'current_location', {}).get('longitude', -122.4194) + random.uniform(-0.005, 0.005)
        
        alerts.append({
            "id": int(time.time()),
            "level": "RED" if system.latest_state.fire_risk_score > 0.9 else "ORANGE",
            "message": "Phase-5 CONFIRMED: Fire signature detected",
            "timestamp": system.latest_state.timestamp.isoformat(),
            "score": f"{system.latest_state.fire_risk_score:.2f}",
            "node_id": "NODE-001",
            "location": {"latitude": lat, "longitude": lng}
        })
    return {"alerts": alerts}

@app.get("/api/death_vectors")
async def get_death_vectors():
    return {"vectors": []}

@app.get("/api/detections")
async def get_detections():
    """Return latest visual detection if available"""
    # In a real system, we'd return a list of recent detections
    # For this demo, we return the current frame if it's "interesting" (has fire)
    dets = []
    if system.latest_image and system.latest_state and system.latest_state.fire_risk_score > 0.4:
        # Only show detection if risk is elevated (syncs with fire video)
        dets.append(system.latest_image)
    return {"detections": dets}

# Serve Frontend
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
# Serve Real Images
app.mount("/api/images", StaticFiles(directory="data/real/images"), name="real_images")

@app.get("/")
async def read_root():
    return RedirectResponse(url="/frontend/index.html")

if __name__ == "__main__":
    print(f"Server starting at http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
