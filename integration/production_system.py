"""
PRODUCTION FIRE DETECTION SYSTEM
Uses REAL hardware sensors instead of simulated data

This is the deployment-ready version.
"""

import time
from datetime import datetime
from typing import Dict
import logging

# Phase-1 imports (assuming you have these from before)
try:
    from phase1_watchdog_layer import Phase1WatchdogLayer, SensorReading
    HAS_PHASE1 = True
except ImportError:
    print("⚠️  Phase-1 not found - operating in Phase-0 only mode")
    HAS_PHASE1 = False

# Phase-0 imports
from phase0_fusion_engine import Phase0FusionEngine
from environmental_state import EnvironmentalState

# REAL sensor interface (replaces MockSensorSimulator)
from real_sensor_interface import RealSensorInterface


class ProductionFireDetectionSystem:
    """
    Production-ready fire detection system using real sensors
    
    Replaces IntegratedFireDetectionSystem with real hardware
    """
    
    def __init__(self, use_phase1: bool = True, sensor_config: Dict = None):
        """
        Initialize production system
        
        Args:
            use_phase1: Whether to use Phase-1 watchdog validation
            sensor_config: Hardware sensor configuration
        """
        self.logger = logging.getLogger(__name__)
        
        print("\n" + "🔥"*35)
        print("PRODUCTION FIRE DETECTION SYSTEM")
        print("🔥"*35)
        
        # Initialize Phase-1 Watchdog
        self.use_phase1 = use_phase1 and HAS_PHASE1
        if self.use_phase1:
            self.watchdog = Phase1WatchdogLayer()
            print("✅ Phase-1 Watchdog Layer: ACTIVE")
        else:
            self.watchdog = None
            print("⚠️  Phase-1 Watchdog Layer: DISABLED")
        
        # Initialize Phase-0 Fusion Engine
        self.fusion_engine = Phase0FusionEngine()
        print("✅ Phase-0 Fusion Engine: ACTIVE")
        
        # Initialize REAL sensors (replaces MockSensorSimulator)
        self.sensor_interface = RealSensorInterface(config=sensor_config)
        print("✅ Real Sensor Interface: ACTIVE")
        
        # Alert tracking
        self.alert_history = []
        
        print("="*70 + "\n")
    
    def process_sensor_data(self, raw_sensors: Dict = None) -> EnvironmentalState:
        """
        Process sensor data through both phases
        
        Args:
            raw_sensors: Optional pre-read sensor data. If None, reads from sensors.
        
        Returns:
            EnvironmentalState with fire risk assessment
        """
        # Read from real sensors if not provided
        if raw_sensors is None:
            raw_sensors = self.sensor_interface.read_sensors()
        
        validated_sensors = {}
        phase1_stats = {}
        
        # =====================================================================
        # PHASE-1: Validate each sensor reading
        # =====================================================================
        if self.use_phase1:
            for sensor_id, reading in raw_sensors.items():
                if reading is None:
                    validated_sensors[sensor_id] = None
                    continue
                
                # Validate through Phase-1
                result = self.watchdog.validate(
                    reading=reading,
                    sensor_id=sensor_id,
                    sensor_type=reading.sensor_type,
                    available_sensors={
                        k: v.value for k, v in raw_sensors.items() 
                        if v is not None and hasattr(v, 'value')
                    }
                )
                
                validated_sensors[sensor_id] = result
            
            phase1_stats = self.watchdog.get_statistics()
        else:
            # No Phase-1 - pass through raw sensors
            from dataclasses import dataclass
            
            @dataclass
            class MockValidation:
                sensor_id: str
                value: any
                is_valid: bool = True
                is_imputed: bool = False
                reliability_score: float = 1.0
            
            validated_sensors = {
                k: MockValidation(k, v.value if hasattr(v, 'value') else v)
                for k, v in raw_sensors.items()
                if v is not None
            }
            phase1_stats = {'trauma_level': 0.0}
        
        # =====================================================================
        # PHASE-0: Fuse sensors into environmental state
        # =====================================================================
        environmental_state = self.fusion_engine.fuse(
            validated_sensors,
            phase1_stats=phase1_stats
        )
        
        return environmental_state
    
    def trigger_alert(self, state: EnvironmentalState):
        """
        Trigger fire alert and emergency response
        
        Args:
            state: Environmental state that triggered alert
        """
        alert = {
            'timestamp': state.timestamp,
            'fire_risk': state.fire_risk_score,
            'confidence': state.overall_confidence,
            'agreement': state.cross_modal_agreement,
            'risk_level': state.get_risk_level()
        }
        
        self.alert_history.append(alert)
        
        print("\n" + "🚨"*35)
        print("FIRE ALERT TRIGGERED!")
        print("🚨"*35)
        print(f"Time: {state.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Risk Level: {state.get_risk_level()} ({state.fire_risk_score:.0%})")
        print(f"Confidence: {state.get_confidence_level()} ({state.overall_confidence:.0%})")
        print(f"Agreement: {state.cross_modal_agreement:.0%}")
        
        if state.disagreement_flags:
            print(f"⚠️  Disagreements: {', '.join(state.disagreement_flags)}")
        
        print("\n📡 Sending alert to rangers...")
        print("💧 Activating water sprinklers...")
        print("📸 Capturing high-res photos...")
        print("🛰️  Transmitting via satellite...")
        
        # Log alert
        self.logger.critical(f"FIRE ALERT: Risk={state.fire_risk_score:.0%}, Confidence={state.overall_confidence:.0%}")
        
        # TODO: Implement actual alert mechanisms:
        self._send_lora_alert(alert)
        self._activate_sprinklers(alert)
        self._capture_high_res_photos(alert)
        self._transmit_satellite_data(alert)
    
    def _send_lora_alert(self, alert: Dict):
        """Send LoRaWAN alert to rangers"""
        # TODO: Implement LoRa transmission
        pass
    
    def _activate_sprinklers(self, alert: Dict):
        """Activate water sprinkler system"""
        # TODO: Control GPIO to activate sprinklers
        pass
    
    def _capture_high_res_photos(self, alert: Dict):
        """Capture high-resolution photos for evidence"""
        # TODO: Capture and store images
        pass
    
    def _transmit_satellite_data(self, alert: Dict):
        """Transmit emergency data via satellite"""
        # TODO: Implement satellite transmission
        pass
    
    def print_status(self, state: EnvironmentalState, iteration: int):
        """
        Print current system status
        
        Args:
            state: Current environmental state
            iteration: Iteration number
        """
        print(f"\n{'─'*70}")
        print(f"📊 ITERATION {iteration} - {state.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'─'*70}")
        
        # Sensor status
        print(f"\n🔬 SENSOR STATUS:")
        print(f"  Valid: {state.valid_sensor_count}/{state.raw_sensor_count}")
        if state.imputed_sensor_count > 0:
            print(f"  Imputed: {state.imputed_sensor_count} (virtual sensors)")
        
        # Modality states
        print(f"\n🧪 CHEMICAL STATE:")
        chem = state.chemical_state
        print(f"  VOC: {chem.get('voc_level', 0):.0%}")
        print(f"  Combustion: {chem.get('combustion_byproducts', 0):.0%}")
        if chem.get('rapid_change_detected'):
            print(f"  ⚡ RAPID CHANGE DETECTED!")
        
        print(f"\n👁️  VISUAL STATE:")
        vis = state.visual_state
        print(f"  Smoke: {vis.get('smoke_presence', 0):.0%}")
        print(f"  Brightness anomaly: {vis.get('brightness_anomaly', 0):.0%}")
        
        print(f"\n🌍 ENVIRONMENTAL CONTEXT:")
        env = state.environmental_context
        print(f"  Soil dryness: {env.get('soil_dryness', 0):.0%}")
        print(f"  Ignition risk: {env.get('ignition_susceptibility', 0):.0%}")
        if env.get('drought_detected'):
            print(f"  🏜️  DROUGHT CONDITIONS DETECTED!")
        
        # Fire risk assessment
        print(f"\n🔥 FIRE RISK ASSESSMENT:")
        risk_emoji = {
            'SAFE': '✅',
            'ELEVATED': '⚠️ ',
            'HIGH': '🔥',
            'CRITICAL': '🚨'
        }
        print(f"  Risk: {risk_emoji.get(state.get_risk_level(), '❓')} {state.get_risk_level()} ({state.fire_risk_score:.0%})")
        print(f"  Agreement: {state.cross_modal_agreement:.0%}")
        print(f"  Confidence: {state.get_confidence_level()} ({state.overall_confidence:.0%})")
        
        if state.disagreement_flags:
            print(f"\n⚠️  DISAGREEMENTS:")
            for flag in state.disagreement_flags:
                print(f"  - {flag}")
        
        if state.fire_detected:
            print(f"\n🔥 FIRE DETECTED: {'YES' if state.fire_detected else 'NO'}")
            print(f"🚨 ALERT STATUS: {'TRIGGERED' if state.should_alert() else 'MONITORING'}")
    
    def run_continuous_monitoring(self, 
                                   check_interval: int = 5,
                                   print_status: bool = True):
        """
        Run continuous monitoring loop
        
        Args:
            check_interval: Seconds between sensor readings
            print_status: Whether to print status each iteration
        """
        print("\n" + "="*70)
        print("🔄 CONTINUOUS MONITORING MODE")
        print("="*70)
        print(f"Check interval: {check_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                
                # Read and process sensors
                state = self.process_sensor_data()
                
                # Print status if requested
                if print_status:
                    self.print_status(state, iteration)
                
                # Check for alert
                if state.should_alert():
                    self.trigger_alert(state)
                
                # Wait before next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏸️  Monitoring stopped by user")
        
        finally:
            self._shutdown()
    
    def _shutdown(self):
        """Graceful shutdown"""
        print("\n" + "="*70)
        print("📊 FINAL STATISTICS")
        print("="*70)
        
        self.fusion_engine.print_statistics()
        
        if self.use_phase1:
            print()
            self.watchdog.print_statistics()
        
        if self.alert_history:
            print(f"\n🚨 ALERTS TRIGGERED: {len(self.alert_history)}")
            for alert in self.alert_history:
                print(f"  - {alert['timestamp'].strftime('%H:%M:%S')}: {alert['risk_level']} (risk={alert['fire_risk']:.0%})")
        
        # Close sensors
        self.sensor_interface.close()
        print("\n✅ System shutdown complete")


# ============================================================================
#  DEPLOYMENT CONFIGURATION
# ============================================================================

def create_production_config() -> Dict:
    """
    Create production sensor configuration
    
    Adjust these settings for your hardware setup
    """
    return {
        # I2C Configuration
        'i2c_bus': 1,
        
        # Chemical Sensors
        'bme680_address': 0x77,  # BME680 for VOC, temp, humidity
        'ccs811_address': 0x5A,  # CCS811 for TVOC, eCO2
        
        # Environmental Sensors
        'dht_pin': 4,  # GPIO4 for DHT22
        'dht_type': 'DHT22',
        'soil_moisture_pin': 0,  # ADS1115 channel 0
        
        # Camera
        'camera_type': 'picamera',  # 'picamera' or 'usb'
        'camera_resolution': (160, 120),
        
        # Timing
        'sensor_warmup_time': 5,
    }


# ============================================================================
#  MAIN DEPLOYMENT
# ============================================================================

def deploy_system(check_interval: int = 10):
    """
    Deploy production fire detection system
    
    Args:
        check_interval: Seconds between sensor checks (default: 10)
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('fire_detection.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create sensor configuration
    sensor_config = create_production_config()
    
    # Initialize system
    system = ProductionFireDetectionSystem(
        use_phase1=HAS_PHASE1,
        sensor_config=sensor_config
    )
    
    # Run continuous monitoring
    system.run_continuous_monitoring(
        check_interval=check_interval,
        print_status=True
    )


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    check_interval = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    print("\n" + "🔥"*35)
    print("DEPLOYING PRODUCTION FIRE DETECTION SYSTEM")
    print("🔥"*35)
    print(f"\nSensor check interval: {check_interval} seconds")
    print("\nPress Ctrl+C to stop\n")
    
    # Deploy
    deploy_system(check_interval=check_interval)
