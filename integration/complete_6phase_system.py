"""
COMPLETE 6-PHASE FIRE DETECTION SYSTEM
Production-Ready Integration

System Architecture:
Phase-0: Sensor Fusion Engine
Phase-1: Watchdog Layer (Validation)
Phase-2: Fractal Gate (Structure Detection)
Phase-3: Chaos Kernel (Instability Detection)
Phase-4: Vision Mamba (Visual Processing)
Phase-5: Logic Gate (Decision Making)
Phase-6: Communication Layer (Alert Routing)

This is the FINAL integration for deployment.
"""

# Fix Python path to allow imports from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass

# Phase imports
from phases.phase1_watchdog.watchdog_layer import Phase1WatchdogLayer, SensorReading
from phases.phase0_fusion.fusion_engine import Phase0FusionEngine
from phases.phase2_fractal.fractal_gate import Phase2FractalGate
from phases.phase3_chaos.chaos_kernel import Phase3ChaosKernel
from phases.phase4_vision.vision_mamba import Phase4VisionMamba
from phases.phase5_logic.logic_gate import Phase5LogicGate, PhaseInputs
from phases.phase6_communication.communication_layer import (
    Phase6CommunicationLayer,
    GPSCoordinate,
    create_alert_from_phase5
)

# Real sensor interface
try:
    from real_sensor_interface import RealSensorInterface
    HAS_REAL_SENSORS = True
except ImportError:
    HAS_REAL_SENSORS = False
    print("⚠️  Real sensor interface not found - using mock mode")


# ============================================================================
#  SYSTEM CONFIGURATION
# ============================================================================

@dataclass
class SystemConfig:
    """
    Complete system configuration
    
    Attributes:
        node_id: Unique node identifier
        location: GPS coordinates
        enable_phase1: Enable sensor validation
        enable_phase2: Enable fractal analysis
        enable_phase3: Enable chaos analysis
        enable_phase4: Enable vision processing
        enable_phase6: Enable communication
        sample_interval: Base sampling interval (seconds)
    """
    node_id: str
    location: GPSCoordinate
    
    # Phase toggles
    enable_phase1: bool = True
    enable_phase2: bool = True
    enable_phase3: bool = True
    enable_phase4: bool = True
    enable_phase6: bool = True
    
    # Sampling
    sample_interval: int = 10  # seconds
    
    # Communication
    lora_range_meters: float = 500.0
    dying_gasp_temp: float = 100.0


# ============================================================================
#  COMPLETE INTEGRATED SYSTEM
# ============================================================================

class Complete6PhaseFireDetectionSystem:
    """
    Complete 6-phase fire detection system
    
    Data Flow:
    
    Sensors → Phase-1 (Validate) → Phase-0 (Fuse) → 
    Phase-2 (Structure?) → Phase-3 (Chaos?) → 
    Phase-4 (Vision?) → Phase-5 (Decide) → Phase-6 (Alert)
    
    Power-Efficient Gating:
    - Phase-2 activates Phase-4 only when structure detected
    - Phase-4 processes vision only when needed
    - Phase-5 adjusts sampling rate based on risk
    """
    
    def __init__(self, config: SystemConfig):
        """
        Initialize complete system
        
        Args:
            config: System configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"FireDetection.{config.node_id}")
        
        print("\n" + "🔥"*35)
        print("COMPLETE 6-PHASE FIRE DETECTION SYSTEM")
        print("🔥"*35)
        print(f"\nNode ID: {config.node_id}")
        print(f"Location: {config.location.latitude:.4f}, {config.location.longitude:.4f}")
        
        # Initialize phases
        self._initialize_phases()
        
        # Real sensor interface
        if HAS_REAL_SENSORS:
            self.sensor_interface = RealSensorInterface()
            print("✅ Real Sensor Interface: ACTIVE")
        else:
            self.sensor_interface = None
            print("⚠️  Real Sensor Interface: UNAVAILABLE (using mock)")
        
        # System state
        self.iteration = 0
        self.current_sample_interval = config.sample_interval
        self.last_alert_time: Optional[datetime] = None
        
        print("\n" + "="*70 + "\n")
    
    def _initialize_phases(self):
        """Initialize all phases"""
        config = self.config
        
        # Phase-1: Watchdog Layer
        if config.enable_phase1:
            self.phase1 = Phase1WatchdogLayer()
            print("✅ Phase-1 Watchdog Layer: ACTIVE")
        else:
            self.phase1 = None
            print("⚠️  Phase-1 Watchdog Layer: DISABLED")
        
        # Phase-0: Fusion Engine
        self.phase0 = Phase0FusionEngine()
        print("✅ Phase-0 Fusion Engine: ACTIVE")
        
        # Phase-2: Fractal Gate
        if config.enable_phase2:
            self.phase2 = Phase2FractalGate()
            print("✅ Phase-2 Fractal Gate: ACTIVE")
        else:
            self.phase2 = None
            print("⚠️  Phase-2 Fractal Gate: DISABLED")
        
        # Phase-3: Chaos Kernel
        if config.enable_phase3:
            self.phase3 = Phase3ChaosKernel()
            print("✅ Phase-3 Chaos Kernel: ACTIVE")
        else:
            self.phase3 = None
            print("⚠️  Phase-3 Chaos Kernel: DISABLED")
        
        # Phase-4: Vision Mamba
        if config.enable_phase4:
            self.phase4 = Phase4VisionMamba()
            print("✅ Phase-4 Vision Mamba: ACTIVE")
        else:
            self.phase4 = None
            print("⚠️  Phase-4 Vision Mamba: DISABLED")
        
        # Phase-5: Logic Gate
        self.phase5 = Phase5LogicGate()
        print("✅ Phase-5 Logic Gate: ACTIVE")
        
        # Phase-6: Communication Layer
        if config.enable_phase6:
            self.phase6 = Phase6CommunicationLayer(
                node_id=config.node_id,
                location=config.location,
                lora_range_meters=config.lora_range_meters,
                dying_gasp_temp_threshold=config.dying_gasp_temp
            )
            print("✅ Phase-6 Communication Layer: ACTIVE")
        else:
            self.phase6 = None
            print("⚠️  Phase-6 Communication Layer: DISABLED")
    
    def process_cycle(self) -> Dict:
        """
        Execute one complete sensing and decision cycle
        
        Returns:
            Dictionary with cycle results
        """
        self.iteration += 1
        timestamp = datetime.now()
        
        # =====================================================================
        # STEP 1: READ SENSORS
        # =====================================================================
        if self.sensor_interface:
            raw_sensors = self.sensor_interface.read_sensors()
        else:
            # Mock sensor data for testing
            raw_sensors = self._generate_mock_sensors()
        
        # =====================================================================
        # STEP 2: PHASE-1 VALIDATION
        # =====================================================================
        if self.phase1:
            validated_sensors = self._validate_sensors(raw_sensors)
            phase1_stats = self.phase1.get_statistics()
        else:
            # Pass through without validation
            validated_sensors = raw_sensors
            phase1_stats = {'trauma_level': 0.0}
        
        # =====================================================================
        # STEP 3: PHASE-0 FUSION
        # =====================================================================
        environmental_state = self.phase0.fuse(
            validated_sensors,
            phase1_stats=phase1_stats
        )
        
        # =====================================================================
        # STEP 4: PHASE-2 FRACTAL ANALYSIS
        # =====================================================================
        if self.phase2:
            fractal_result = self.phase2.update(
                environmental_state.fire_risk_score,
                timestamp
            )
            has_structure = fractal_result.has_structure
            hurst_exponent = fractal_result.hurst_exponent
        else:
            has_structure = False
            hurst_exponent = 0.5
        
        # =====================================================================
        # STEP 5: PHASE-3 CHAOS ANALYSIS
        # =====================================================================
        if self.phase3:
            # Get temporal trend from Phase-0 if available
            temporal_trend = getattr(environmental_state, 'temporal_metadata', {}).get('chemical_trend', 0.0)
            
            chaos_result = self.phase3.update(
                environmental_state.fire_risk_score,
                temporal_trend,
                timestamp
            )
            is_unstable = chaos_result.is_unstable
            lyapunov_exponent = chaos_result.lyapunov_exponent
        else:
            is_unstable = False
            lyapunov_exponent = 0.0
        
        # =====================================================================
        # STEP 6: PHASE-4 VISION PROCESSING (Power-Gated)
        # =====================================================================
        vision_confidence = 0.0
        smoke_confidence = 0.0
        
        # Only activate vision if Phase-2 detects structure
        if self.phase4 and self.phase2 and self.phase2.should_activate_vision():
            # Get camera data from validated sensors
            camera_data = None
            for sensor_id, sensor in validated_sensors.items():
                if 'CAMERA' in sensor_id.upper():
                    camera_data = getattr(sensor, 'value', None)
                    break
            
            if camera_data is not None:
                vision_result = self.phase4.process_frame(camera_data, timestamp)
                vision_confidence = vision_result.get('confidence', 0.0)
                smoke_confidence = vision_result.get('smoke_confidence', 0.0)
        
        # =====================================================================
        # STEP 7: PHASE-5 DECISION LOGIC
        # =====================================================================
        
        # Consolidate inputs for Phase-5
        phase_inputs = PhaseInputs(
            fire_risk_score=environmental_state.fire_risk_score,
            cross_modal_agreement=environmental_state.cross_modal_agreement,
            temporal_trend=getattr(environmental_state, 'temporal_metadata', {}).get('trend', 'stable'),
            persistence=getattr(environmental_state, 'temporal_metadata', {}).get('persistence', 0.0),
            has_structure=has_structure,
            hurst_exponent=hurst_exponent,
            is_unstable=is_unstable,
            lyapunov_exponent=lyapunov_exponent,
            vision_confidence=vision_confidence,
            camera_healthy=vision_confidence > 0,
            smoke_confidence=smoke_confidence,
            trauma_level=phase1_stats.get('trauma_level', 0.0),
            timestamp=timestamp
        )
        
        # Make decision
        decision = self.phase5.decide(phase_inputs, neighbor_nodes=[])
        
        # =====================================================================
        # STEP 8: PHASE-6 COMMUNICATION
        # =====================================================================
        alert = None
        if self.phase6:
            # Get node temperature from sensors
            node_temp = self._get_node_temperature(validated_sensors)
            battery_level = self._get_battery_level()
            
            # Process alert routing
            alert = self.phase6.process_alert(
                risk_score=decision.risk_score,
                confidence=decision.confidence,
                should_alert=decision.should_alert,
                witnesses=decision.witnesses,
                node_temperature=node_temp,
                battery_level=battery_level,
                metadata={
                    'reasoning': decision.reasoning,
                    'system_state': decision.system_state.value
                }
            )
            
            if alert:
                self.last_alert_time = timestamp
        
        # =====================================================================
        # STEP 9: ADJUST SAMPLING RATE
        # =====================================================================
        self.current_sample_interval = decision.next_sample_interval
        
        # =====================================================================
        # RETURN CYCLE RESULTS
        # =====================================================================
        return {
            'iteration': self.iteration,
            'timestamp': timestamp,
            'environmental_state': environmental_state,
            'fractal_result': fractal_result if self.phase2 else None,
            'chaos_result': chaos_result if self.phase3 else None,
            'vision_confidence': vision_confidence,
            'decision': decision,
            'alert': alert,
            'next_sample_interval': self.current_sample_interval
        }
    
    def _validate_sensors(self, raw_sensors: Dict) -> Dict:
        """
        Validate sensors through Phase-1
        
        Args:
            raw_sensors: Raw sensor readings
        
        Returns:
            Dictionary of validated sensors
        """
        validated = {}
        
        # Get available sensor values for cross-validation
        available = {
            k: v.value for k, v in raw_sensors.items()
            if v is not None and hasattr(v, 'value')
        }
        
        for sensor_id, reading in raw_sensors.items():
            if reading is None:
                continue
            
            result = self.phase1.validate(
                reading=reading,
                sensor_id=sensor_id,
                sensor_type=getattr(reading, 'sensor_type', 'unknown'),
                available_sensors=available
            )
            
            if result.is_valid or result.is_imputed:
                validated[sensor_id] = result
        
        return validated
    
    def _get_node_temperature(self, validated_sensors: Dict) -> float:
        """
        Get node temperature from sensors
        
        Args:
            validated_sensors: Validated sensor data
        
        Returns:
            Temperature in Celsius
        """
        for sensor_id, sensor in validated_sensors.items():
            if 'TEMP' in sensor_id.upper():
                return getattr(sensor, 'value', 25.0)
        
        return 25.0  # Default
    
    def _get_battery_level(self) -> float:
        """
        Get battery level
        
        Returns:
            Battery percentage (0-100)
        """
        # TODO: Read from actual battery monitor
        return 80.0  # Mock value
    
    def _generate_mock_sensors(self) -> Dict:
        """
        Generate mock sensor data for testing
        
        Returns:
            Dictionary of mock sensor readings
        """
        import numpy as np
        
        timestamp = datetime.now()
        
        return {
            'TEMP_001': SensorReading(
                sensor_id='TEMP_001',
                value=25.0 + np.random.randn() * 2.0,
                timestamp=timestamp,
                sensor_type='temperature'
            ),
            'HUM_001': SensorReading(
                sensor_id='HUM_001',
                value=50.0 + np.random.randn() * 10.0,
                timestamp=timestamp,
                sensor_type='humidity'
            ),
            'VOC_001': SensorReading(
                sensor_id='VOC_001',
                value=100.0 + np.random.randn() * 20.0,
                timestamp=timestamp,
                sensor_type='voc'
            )
        }
    
    def print_cycle_status(self, results: Dict):
        """
        Print status of current cycle
        
        Args:
            results: Cycle results dictionary
        """
        decision = results['decision']
        env_state = results['environmental_state']
        
        print(f"\n{'─'*70}")
        print(f"🔄 CYCLE {results['iteration']} - {results['timestamp'].strftime('%H:%M:%S')}")
        print(f"{'─'*70}")
        
        # Environmental state
        print(f"\n🌲 ENVIRONMENTAL STATE:")
        print(f"  Fire Risk: {env_state.fire_risk_score:.0%}")
        print(f"  Agreement: {env_state.cross_modal_agreement:.0%}")
        print(f"  Confidence: {env_state.overall_confidence:.0%}")
        
        # Phase results
        if results['fractal_result']:
            print(f"\n🔬 FRACTAL ANALYSIS:")
            print(f"  Hurst: {results['fractal_result'].hurst_exponent:.3f}")
            print(f"  Structure: {'✅ YES' if results['fractal_result'].has_structure else '❌ NO'}")
        
        if results['chaos_result']:
            print(f"\n⚡ CHAOS ANALYSIS:")
            print(f"  Lyapunov: {results['chaos_result'].lyapunov_exponent:.3f}")
            print(f"  Unstable: {'✅ YES' if results['chaos_result'].is_unstable else '❌ NO'}")
        
        if results['vision_confidence'] > 0:
            print(f"\n👁️  VISION:")
            print(f"  Confidence: {results['vision_confidence']:.0%}")
        
        # Decision
        tier_emoji = {
            'green': '🟢',
            'yellow': '🟡',
            'orange': '🟠',
            'red': '🔴'
        }
        
        print(f"\n🎯 DECISION:")
        print(f"  {tier_emoji.get(decision.risk_tier.value, '⚪')} {decision.risk_tier.value.upper()}")
        print(f"  State: {decision.system_state.value.upper()}")
        print(f"  Alert: {'🚨 YES' if decision.should_alert else '✅ NO'}")
        
        # Alert sent
        if results['alert']:
            alert = results['alert']
            print(f"\n📡 ALERT SENT:")
            print(f"  Priority: P{alert.priority.value}")
            print(f"  Channel: {alert.channel.value}")
            print(f"  ID: {alert.alert_id}")
        
        # Next action
        print(f"\n⏰ Next sample in: {results['next_sample_interval']}s")
    
    def run_continuous_monitoring(self, print_status: bool = True):
        """
        Run continuous monitoring loop
        
        Args:
            print_status: Whether to print status each cycle
        """
        print("\n" + "="*70)
        print("🔄 CONTINUOUS MONITORING MODE")
        print("="*70)
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Execute cycle
                results = self.process_cycle()
                
                # Print status
                if print_status:
                    self.print_cycle_status(results)
                
                # Wait for next cycle
                time.sleep(self.current_sample_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏸️  Monitoring stopped by user")
        
        finally:
            self._shutdown()
    
    def _shutdown(self):
        """Graceful shutdown"""
        print("\n" + "="*70)
        print("📊 FINAL STATISTICS")
        print("="*70)
        
        # Print statistics from all phases
        if self.phase1:
            print("\nPhase-1:")
            self.phase1.print_statistics()
        
        print("\nPhase-0:")
        self.phase0.print_statistics()
        
        if self.phase2:
            print(f"\nPhase-2:")
            stats = self.phase2.get_statistics()
            print(f"  Analyses: {stats['analyses_performed']}")
            print(f"  Structure detected: {stats['structure_detected']}")
        
        if self.phase3:
            print(f"\nPhase-3:")
            stats = self.phase3.get_statistics()
            print(f"  Analyses: {stats['analyses_performed']}")
            print(f"  Instability detected: {stats['instability_detected']}")
        
        if self.phase5:
            print(f"\nPhase-5:")
            stats = self.phase5.get_statistics()
            print(f"  Decisions: {stats['decisions_made']}")
            print(f"  Alerts triggered: {stats['alerts_triggered']}")
        
        if self.phase6:
            print("\nPhase-6:")
            self.phase6.print_statistics()
        
        print("\n✅ System shutdown complete")


# ============================================================================
#  DEPLOYMENT
# ============================================================================

def deploy_production_system(node_id: str = "NODE_001",
                            latitude: float = 37.7749,
                            longitude: float = -122.4194):
    """
    Deploy production fire detection system
    
    Args:
        node_id: Unique node identifier
        latitude: GPS latitude
        longitude: GPS longitude
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'fire_detection_{node_id}.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create configuration
    config = SystemConfig(
        node_id=node_id,
        location=GPSCoordinate(latitude=latitude, longitude=longitude),
        enable_phase1=True,
        enable_phase2=True,
        enable_phase3=True,
        enable_phase4=True,
        enable_phase6=True,
        sample_interval=10
    )
    
    # Initialize system
    system = Complete6PhaseFireDetectionSystem(config)
    
    # Run continuous monitoring
    system.run_continuous_monitoring(print_status=True)


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    node_id = sys.argv[1] if len(sys.argv) > 1 else "NODE_001"
    lat = float(sys.argv[2]) if len(sys.argv) > 2 else 37.7749
    lon = float(sys.argv[3]) if len(sys.argv) > 3 else -122.4194
    
    print("\n" + "🔥"*35)
    print("DEPLOYING PRODUCTION FIRE DETECTION SYSTEM")
    print("🔥"*35)
    print(f"\nNode ID: {node_id}")
    print(f"Location: {lat:.4f}, {lon:.4f}")
    print("\nPress Ctrl+C to stop\n")
    
    # Deploy
    deploy_production_system(node_id, lat, lon)
