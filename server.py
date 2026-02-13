
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, RedirectResponse
import sys
import os
import random
import time
import warnings
from datetime import datetime
from threading import Thread
from typing import Dict, Any

# Suppress harmless numpy corrcoef division-by-zero when sensor data is constant
warnings.filterwarnings('ignore', message='invalid value encountered in divide')

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

# The Hive: Mesh Network imports
try:
    from phases.phase6_communication.communication_layer import (
        MeshNetwork, RoleAwareCommunicationLayer, GPSCoordinate
    )
    HAS_MESH = True
    print("DEBUG: 🐝 Hive mesh network loaded.")
except ImportError as e:
    HAS_MESH = False
    print(f"⚠️  Mesh network not available: {e}")

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
        lat_val = float(row.get('lat', -35.72)) # Deua National Park (Black Summer bushland)
        lng_val = float(row.get('lng', 150.10))
        # Offset coordinates ~7km WNW into Deua National Park bushland
        # (CSV originals are near Batemans Bay township / coastal water)
        lat_val = lat_val + 0.01   # shift slightly south
        lng_val = lng_val - 0.08   # shift ~7km west into national park
        


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
        self.latest_location = {"latitude": -35.72, "longitude": 150.10} # Deua National Park, NSW (Black Summer)
        self.latest_image = None
        self.latest_fractal = None
        self.latest_chaos = None
        self.running = False
        
        # THE HIVE: Mesh Network (Multiple Queens + Drones)
        self.mesh_network = None
        self.queen_comms = {}   # queen_id → RoleAwareCommunicationLayer
        self.queen_comm = None  # primary queen (backward compat)
        self.drone_comms = {}   # node_id → RoleAwareCommunicationLayer
        self.latest_mesh_alert = None
        self._init_mesh_network()
    
    def _init_mesh_network(self):
        """Initialize The Hive mesh with 3 Queens × 3 Drones each = 12 nodes"""
        if not HAS_MESH:
            print("⚠️  Skipping mesh init — module not available")
            return
        
        self.mesh_network = MeshNetwork(lora_range_meters=5000.0)
        
        # === 3 QUEEN NODES — Real Australian bushfire regions ===
        queen_configs = [
            # Deua National Park, NSW (Black Summer epicenter)
            ("QUEEN_DEUA", -35.7200, 150.1000, "Deua National Park, NSW"),
            # Blue Mountains, NSW (major fire corridor)
            ("QUEEN_BLUE", -33.7170, 150.3120, "Blue Mountains, NSW"),
            # Kangaroo Island, SA (isolated island fires)
            ("QUEEN_KI",   -35.8000, 137.2150, "Kangaroo Island, SA"),
        ]
        
        for queen_id, lat, lon, label in queen_configs:
            queen_loc = GPSCoordinate(latitude=lat, longitude=lon)
            comm = RoleAwareCommunicationLayer(
                node_id=queen_id,
                role="QUEEN",
                location=queen_loc,
                mesh_network=self.mesh_network,
                has_satellite=True
            )
            self.queen_comms[queen_id] = comm
            # Tag label for dropdown/API
            self.mesh_network.nodes[queen_id]['label'] = label
        
        # Primary queen for backward compat
        self.queen_comm = self.queen_comms.get("QUEEN_DEUA")
        
        # === DRONE NODES — 3 per Queen ===
        drone_configs = {
            "QUEEN_DEUA": [
                ("D_DEUA_01", -35.7180, 150.0970, "Deua NW Sector"),
                ("D_DEUA_02", -35.7220, 150.1030, "Deua SE Sector"),
                ("D_DEUA_03", -35.7190, 150.1050, "Deua NE Sector"),
            ],
            "QUEEN_BLUE": [
                ("D_BLUE_01", -33.7150, 150.3080, "Blue Mts West"),
                ("D_BLUE_02", -33.7190, 150.3160, "Blue Mts East"),
                ("D_BLUE_03", -33.7140, 150.3150, "Blue Mts North"),
            ],
            "QUEEN_KI": [
                ("D_KI_01",   -35.7980, 137.2100, "KI West End"),
                ("D_KI_02",   -35.8020, 137.2200, "KI Flinders Chase"),
                ("D_KI_03",   -35.7970, 137.2180, "KI North Coast"),
            ],
        }
        
        for queen_id, drones in drone_configs.items():
            for node_id, lat, lon, label in drones:
                loc = GPSCoordinate(latitude=lat, longitude=lon)
                comm = RoleAwareCommunicationLayer(
                    node_id=node_id,
                    role="DRONE",
                    location=loc,
                    mesh_network=self.mesh_network,
                    queen_node_id=queen_id,
                    has_satellite=False
                )
                self.drone_comms[node_id] = comm
                self.mesh_network.nodes[node_id]['label'] = label
                self.mesh_network.nodes[node_id]['queen_id'] = queen_id
        
        total_queens = len(self.queen_comms)
        total_drones = len(self.drone_comms)
        print(f"🐝 THE HIVE initialized: {total_queens} Queens + {total_drones} Drones = {total_queens + total_drones} nodes")

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
            
            # 6. THE HIVE: Route alert through mesh (Drones → Queen → Satellite)
            if system.mesh_network and system.queen_comms and state.fire_risk_score > 0.3:
                # Simulate drones detecting and relaying to their Queen
                for drone_id, drone_comm in system.drone_comms.items():
                    drone_risk = min(1.0, state.fire_risk_score + random.uniform(-0.05, 0.05))
                    drone_result = drone_comm.process_alert(
                        risk_score=drone_risk,
                        confidence=state.overall_confidence,
                        should_alert=(drone_risk > 0.5),
                        witnesses=2,
                        battery_level=random.uniform(60, 100)
                    )
                    
                    # Route to the correct Queen for this drone
                    if drone_result:
                        queen_id = system.mesh_network.nodes.get(drone_id, {}).get('queen_id')
                        queen_comm = system.queen_comms.get(queen_id) if queen_id else system.queen_comm
                        if queen_comm:
                            queen_result = queen_comm.receive_drone_alert(drone_result)
                            if queen_result and queen_result.get('escalated'):
                                system.latest_mesh_alert = queen_result
                
                # Periodic heartbeats (every ~10 cycles ≈ 10s for demo)
                if len(system.history) % 10 == 0:
                    for drone_comm in system.drone_comms.values():
                        drone_comm.send_heartbeat()
                
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

    # Mesh/Hive info
    mesh_info = {}
    if system.mesh_network:
        mesh_stats = system.mesh_network.get_statistics()
        mesh_info = {
            "queen_count": len(system.queen_comms),
            "queen_ids": list(system.queen_comms.keys()),
            "connected_drones": mesh_stats.get('online_drones', 0),
            "total_nodes": mesh_stats.get('total_nodes', 0),
            "messages_routed": mesh_stats.get('messages_routed', 0),
            "satellite_uplinks": mesh_stats.get('queen_to_satellite', 0),
            "alerts_aggregated": mesh_stats.get('alerts_aggregated', 0)
        }
    
    response = {
        "node_id": "QUEEN_001",
        "timestamp": s.timestamp.isoformat(),
        "risk_tier": s.get_risk_level(),
        "fire_detected": s.fire_detected,
        "location": system.latest_location,
        
        # THE HIVE: Mesh Network Status
        "mesh": mesh_info,
        
        # System Status for UI
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
    """Phase-5 + Phase-6: Alerts with mesh relay paths"""
    alerts = []
    if system.latest_state and system.latest_state.fire_risk_score > 0.8:
        base_lat = system.latest_location.get('latitude', -35.72) if system.latest_location else -35.72
        base_lng = system.latest_location.get('longitude', 150.10) if system.latest_location else 150.10
        lat = base_lat + random.uniform(-0.003, 0.003)
        lng = base_lng + random.uniform(-0.003, 0.003)
        
        # Build relay path from mesh if available
        relay_path = "DRONE_001 → QUEEN_001 → 🛰️"
        if system.latest_mesh_alert:
            relay_path = system.latest_mesh_alert.get('relay_path_display', relay_path)
        
        alerts.append({
            "id": int(time.time()),
            "level": "RED" if system.latest_state.fire_risk_score > 0.9 else "ORANGE",
            "message": "Phase-5 CONFIRMED: Fire signature detected",
            "timestamp": system.latest_state.timestamp.isoformat(),
            "score": f"{system.latest_state.fire_risk_score:.2f}",
            "node_id": "QUEEN_001",
            "location": {"latitude": lat, "longitude": lng},
            "relay_path": relay_path,
            "escalated": bool(system.latest_mesh_alert and system.latest_mesh_alert.get('escalated'))
        })
    return {"alerts": alerts}

@app.get("/api/mesh")
async def get_mesh():
    """THE HIVE: Mesh network topology and relay status"""
    if not system.mesh_network:
        return {"error": "Mesh network not initialized", "nodes": [], "links": []}
    return system.mesh_network.get_topology()

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

@app.get("/api/velocity")
async def get_velocity():
    """Compute fire spread velocity from recent location/risk history."""
    if len(system.history) < 2:
        return {"velocity_kmh": 0.0, "direction_deg": 0, "direction": "N/A"}
    
    # Use change in risk over time as proxy for fire velocity
    recent = system.history[-5:]
    risk_delta = abs(recent[-1]['fused_score'] - recent[0]['fused_score'])
    avg_risk = sum(p['fused_score'] for p in recent) / len(recent)
    
    # Simulated velocity based on risk dynamics
    velocity = risk_delta * 15.0 + avg_risk * 3.0  # km/h
    
    return {
        "velocity_kmh": round(velocity, 2),
        "direction_deg": 0,
        "direction": "N/A",
        "avg_risk": round(avg_risk, 3),
        "samples": len(recent)
    }

from pydantic import BaseModel

class CommandRequest(BaseModel):
    command: str

@app.post("/api/command")
async def handle_command(req: CommandRequest):
    """Process operator commands from the Command Terminal."""
    cmd = req.command.strip().upper()
    parts = cmd.split()
    
    if parts[0] == "DEPLOY" and len(parts) > 1:
        return {
            "response": [
                f"[SYS] DEPLOY command received for {parts[1]}.",
                f"[SYS] Dispatching UAV to sector {parts[1]}...",
                "[OK] Deployment order queued."
            ],
            "level": "sys"
        }
    elif parts[0] == "EVACUATE" and len(parts) > 1:
        return {
            "response": [
                f"[WARN] EVACUATE order issued for {parts[1]}!",
                "[WARN] Alerting all personnel in zone.",
                "[SYS] Emergency services notified."
            ],
            "level": "warn"
        }
    elif parts[0] == "PING":
        return {
            "response": [
                f"[OK] PONG — Server uptime: {int(time.time() - system.history[0].get('_start', time.time()) if system.history else 0)}s",
                f"[SYS] History buffer: {len(system.history)} samples"
            ],
            "level": "ok"
        }
    elif parts[0] == "REPORT":
        if system.latest_state:
            return {
                "response": [
                    "[SYS] === FULL SYSTEM REPORT ===",
                    f"  Risk Score:  {system.latest_state.fire_risk_score:.4f}",
                    f"  Fire Detected: {system.latest_state.fire_detected}",
                    f"  Confidence:  {system.latest_state.overall_confidence:.2%}",
                    f"  Fractal H:   {system.latest_fractal.hurst_exponent:.4f}" if system.latest_fractal else "  Fractal: N/A",
                    f"  Lyapunov λ:  {system.latest_chaos.lyapunov_exponent:.4f}" if system.latest_chaos else "  Chaos: N/A",
                    f"  Location:    {system.latest_location}",
                    f"  History Pts: {len(system.history)}",
                    "[SYS] === END REPORT ==="
                ],
                "level": "sys"
            }
        return {"response": ["[WARN] System not yet initialized."], "level": "warn"}
    else:
        return {"response": None}

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
