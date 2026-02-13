"""
INTEGRATED FIRE DETECTION SYSTEM
Complete 4-Phase Architecture

Phase-1: Watchdog Layer (Trust Validation)
Phase-0: Sensor Fusion + Mamba SSM (Temporal Intelligence)
Phase-2: Fractal Gate (Structure Detection)
Phase-3: Chaos Kernel (Instability Detection)

NO SIMULATED DATA - Production-ready system for real hardware deployment
"""

import time
from datetime import datetime
from typing import Dict, Optional
import logging

# Phase imports
from phase1_watchdog_layer import Phase1WatchdogLayer, SensorReading
from phase0_fusion_with_mamba_clean import Phase0FusionEngineWithMamba
from phase2_fractal_gate import Phase2FractalGate, print_fractal_analysis
from phase3_chaos_kernel import Phase3ChaosKernel, print_chaos_analysis
from environmental_state import EnvironmentalState


class IntegratedFireDetectionSystem:
    """
    Complete 4-Phase Fire Detection System
    
    Architecture Flow:
    1. Raw Sensors → Phase-1 (Validation)
    2. Validated Sensors → Phase-0 (Fusion + Temporal Analysis)
    3. Risk Scores → Phase-2 (Fractal Structure Detection)
    4. Risk + Trends → Phase-3 (Chaos/Instability Detection)
    5. Final Decision → Alert or Continue Monitoring
    
    Power Efficiency:
    - Phases 0-3 run continuously (low power)
    - Vision only activates when Phase-2 detects structure
    - This saves significant battery power
    """
    
    def __init__(self, enable_phase1: bool = True):
        """
        Initialize integrated system
        
        Args:
            enable_phase1: Whether to use Phase-1 watchdog validation
        """
        self.logger = logging.getLogger(__name__)
        
        print("\n" + "🔥"*35)
        print("INTEGRATED 4-PHASE FIRE DETECTION SYSTEM")
        print("🔥"*35)
        
        # Phase-1: Watchdog Layer
        self.enable_phase1 = enable_phase1
        if enable_phase1:
            self.phase1_watchdog = Phase1WatchdogLayer()
            print("✅ Phase-1: Watchdog Layer (Trust Validation)")
        else:
            self.phase1_watchdog = None
            print("⚠️  Phase-1: Disabled")
        
        # Phase-0: Fusion Engine with Mamba SSM
        self.phase0_fusion = Phase0FusionEngineWithMamba()
        print("✅ Phase-0: Fusion Engine + Mamba SSM (Temporal Intelligence)")
        
        # Phase-2: Fractal Gate
        self.phase2_fractal = Phase2FractalGate(
            hurst_threshold=1.1,
            min_window_size=30
        )
        print("✅ Phase-2: Fractal Gate (Structure Detection)")
        
        # Phase-3: Chaos Kernel
        self.phase3_chaos = Phase3ChaosKernel(
            lyapunov_threshold=0.0,
            min_window_size=40
        )
        print("✅ Phase-3: Chaos Kernel (Instability Detection)")
        
        # System state
        self.vision_active = False
        self.suspicion_state = False
        self.alert_history = []
        
        # Statistics
        self.processing_count = 0
        self.vision_activations = 0
        self.alerts_triggered = 0
        
        print("="*70 + "\n")
    
    def process_sensor_data(self, raw_sensors: Dict) -> Dict:
        """
        Process sensor data through all 4 phases
        
        Args:
            raw_sensors: Dict of raw sensor readings
        
        Returns:
            Complete system state with decisions from all phases
        """
        timestamp = datetime.now()
        
        # =====================================================================
        # PHASE-1: VALIDATE SENSORS
        # =====================================================================
        if self.enable_phase1:
            validated_sensors = {}
            for sensor_id, reading in raw_sensors.items():
                if reading is None:
                    continue
                
                result = self.phase1_watchdog.validate(
                    reading=reading,
                    sensor_id=sensor_id,
                    sensor_type=reading.sensor_type if hasattr(reading, 'sensor_type') else None,
                    available_sensors={
                        k: v.value for k, v in raw_sensors.items()
                        if v is not None and hasattr(v, 'value')
                    }
                )
                
                if result.is_valid:
                    validated_sensors[sensor_id] = result
            
            phase1_stats = self.phase1_watchdog.get_statistics()
        else:
            # No Phase-1: pass through
            validated_sensors = raw_sensors
            phase1_stats = {'trauma_level': 0.0}
        
        # =====================================================================
        # PHASE-0: FUSE SENSORS + TEMPORAL ANALYSIS
        # =====================================================================
        phase0_state = self.phase0_fusion.fuse(
            validated_sensors,
            phase1_stats=phase1_stats
        )
        
        # Extract temporal metadata
        temporal_metadata = getattr(phase0_state, 'temporal_metadata', {})
        risk_score = phase0_state.fire_risk_score
        
        # Get temporal trend for Phase-3
        if temporal_metadata:
            if temporal_metadata['trend'] == 'rising':
                temporal_trend = temporal_metadata.get('chemical_trend', 0.0)
            elif temporal_metadata['trend'] == 'falling':
                temporal_trend = -abs(temporal_metadata.get('chemical_trend', 0.0))
            else:
                temporal_trend = 0.0
        else:
            temporal_trend = 0.0
        
        # =====================================================================
        # PHASE-2: FRACTAL STRUCTURE DETECTION
        # =====================================================================
        phase2_result = self.phase2_fractal.update(
            risk_score=risk_score,
            timestamp=timestamp
        )
        
        # Decision: Should we activate vision?
        should_activate_vision = self.phase2_fractal.should_activate_vision()
        
        if should_activate_vision and not self.vision_active:
            self.vision_active = True
            self.vision_activations += 1
            self.logger.info("🎥 VISION ACTIVATED - Fractal structure detected")
        
        # =====================================================================
        # PHASE-3: CHAOS/INSTABILITY DETECTION
        # =====================================================================
        phase3_result = self.phase3_chaos.update(
            risk_score=risk_score,
            temporal_trend=temporal_trend,
            timestamp=timestamp
        )
        
        # Decision: Enter suspicion state?
        if phase3_result.is_unstable:
            if not self.suspicion_state:
                self.suspicion_state = True
                self.logger.warning("⚡ SUSPICION STATE - Instability detected")
        else:
            self.suspicion_state = False
        
        # =====================================================================
        # FINAL DECISION: COMBINE ALL PHASES
        # =====================================================================
        final_decision = self._make_final_decision(
            phase0_state,
            phase2_result,
            phase3_result
        )
        
        # Update statistics
        self.processing_count += 1
        
        # Return complete system state
        return {
            'timestamp': timestamp,
            'phase0_state': phase0_state,
            'phase2_fractal': phase2_result,
            'phase3_chaos': phase3_result,
            'vision_active': self.vision_active,
            'suspicion_state': self.suspicion_state,
            'final_decision': final_decision,
            'should_alert': final_decision['should_alert']
        }
    
    def _make_final_decision(self,
                            phase0_state: EnvironmentalState,
                            phase2_result,
                            phase3_result) -> Dict:
        """
        Make final fire detection decision by combining all phases
        
        Decision Logic:
        1. Phase-0 detects fire + Phase-2 confirms structure + Phase-3 confirms instability
           → HIGH CONFIDENCE ALERT
        
        2. Phase-0 detects fire + Phase-2 confirms structure
           → MEDIUM CONFIDENCE ALERT (early warning)
        
        3. Phase-3 detects instability but Phase-0 low risk
           → SUSPICION (monitor closely, no alert yet)
        
        4. Phase-2 detects structure but low risk
           → MONITORING (power up vision)
        
        Args:
            phase0_state: Environmental state from Phase-0
            phase2_result: Fractal analysis result from Phase-2
            phase3_result: Chaos analysis result from Phase-3
        
        Returns:
            Final decision dict
        """
        decision = {
            'alert_level': 'SAFE',
            'confidence': 0.0,
            'should_alert': False,
            'reasoning': []
        }
        
        # Rule 1: All phases agree - HIGHEST CONFIDENCE
        if (phase0_state.fire_detected and 
            phase2_result.has_structure and 
            phase3_result.is_unstable):
            
            decision['alert_level'] = 'CRITICAL'
            decision['confidence'] = 0.95
            decision['should_alert'] = True
            decision['reasoning'] = [
                "Phase-0: Fire detected",
                "Phase-2: Fractal structure confirmed",
                "Phase-3: Explosive instability confirmed",
                "All phases agree: HIGH CONFIDENCE FIRE"
            ]
        
        # Rule 2: Phase-0 + Phase-2 agree - EARLY WARNING
        elif phase0_state.fire_detected and phase2_result.has_structure:
            decision['alert_level'] = 'HIGH'
            decision['confidence'] = 0.80
            decision['should_alert'] = True
            decision['reasoning'] = [
                "Phase-0: Fire detected",
                "Phase-2: Fractal structure confirmed",
                "Early warning: Fire with structured pattern"
            ]
        
        # Rule 3: Phase-0 alone - MODERATE CONFIDENCE
        elif phase0_state.fire_detected:
            decision['alert_level'] = 'MEDIUM'
            decision['confidence'] = 0.60
            decision['should_alert'] = phase0_state.should_alert()
            decision['reasoning'] = [
                "Phase-0: Fire detected",
                "Waiting for Phase-2/3 confirmation"
            ]
        
        # Rule 4: Phase-3 detects instability - SUSPICION
        elif phase3_result.is_unstable:
            decision['alert_level'] = 'SUSPICIOUS'
            decision['confidence'] = 0.50
            decision['should_alert'] = False
            decision['reasoning'] = [
                "Phase-3: Instability detected",
                "Phase-0: No fire yet",
                "Suspicion state: Monitor closely"
            ]
        
        # Rule 5: Phase-2 detects structure - MONITORING
        elif phase2_result.has_structure:
            decision['alert_level'] = 'MONITORING'
            decision['confidence'] = 0.30
            decision['should_alert'] = False
            decision['reasoning'] = [
                "Phase-2: Structure detected",
                "Vision activated",
                "Monitoring for fire signature"
            ]
        
        # Rule 6: Normal conditions
        else:
            decision['alert_level'] = 'SAFE'
            decision['confidence'] = phase0_state.overall_confidence
            decision['should_alert'] = False
            decision['reasoning'] = ["All phases normal"]
        
        return decision
    
    def trigger_alert(self, system_state: Dict):
        """
        Trigger fire alert
        
        Args:
            system_state: Complete system state
        """
        alert = {
            'timestamp': system_state['timestamp'],
            'alert_level': system_state['final_decision']['alert_level'],
            'confidence': system_state['final_decision']['confidence'],
            'reasoning': system_state['final_decision']['reasoning']
        }
        
        self.alert_history.append(alert)
        self.alerts_triggered += 1
        
        print("\n" + "🚨"*35)
        print("FIRE ALERT TRIGGERED!")
        print("🚨"*35)
        print(f"Time: {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Alert Level: {alert['alert_level']}")
        print(f"Confidence: {alert['confidence']:.0%}")
        print("\nReasoning:")
        for reason in alert['reasoning']:
            print(f"  • {reason}")
        
        self.logger.critical(f"FIRE ALERT: {alert['alert_level']} (confidence={alert['confidence']:.0%})")
        
        # TODO: Implement actual alert mechanisms
        # self._send_alert_to_rangers(alert)
        # self._activate_suppression(alert)
        # self._capture_evidence(alert)
    
    def print_system_status(self, system_state: Dict, iteration: int):
        """
        Print comprehensive system status
        
        Args:
            system_state: Complete system state
            iteration: Iteration number
        """
        phase0 = system_state['phase0_state']
        phase2 = system_state['phase2_fractal']
        phase3 = system_state['phase3_chaos']
        decision = system_state['final_decision']
        
        print(f"\n{'='*70}")
        print(f"📊 ITERATION {iteration} - {system_state['timestamp'].strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        # Phase-0 Summary
        print(f"\n🧠 PHASE-0: SENSOR FUSION + TEMPORAL INTELLIGENCE")
        print(f"  Fire Risk: {phase0.get_risk_level()} ({phase0.fire_risk_score:.0%})")
        print(f"  Agreement: {phase0.cross_modal_agreement:.0%}")
        print(f"  Confidence: {phase0.overall_confidence:.0%}")
        
        if hasattr(phase0, 'temporal_metadata'):
            tm = phase0.temporal_metadata
            print(f"  Trend: {tm['trend']}")
            print(f"  Persistence: {tm['persistence']:.0%}")
        
        # Phase-2 Summary
        print(f"\n🔬 PHASE-2: FRACTAL GATE")
        print(f"  Hurst Exponent: {phase2.hurst_exponent:.3f}")
        print(f"  Structure Detected: {'YES' if phase2.has_structure else 'NO'}")
        print(f"  Vision Active: {'YES' if system_state['vision_active'] else 'NO'}")
        
        # Phase-3 Summary
        print(f"\n⚡ PHASE-3: CHAOS KERNEL")
        print(f"  Lyapunov Exponent: {phase3.lyapunov_exponent:.3f}")
        print(f"  Unstable: {'YES' if phase3.is_unstable else 'NO'}")
        print(f"  Suspicion Level: {phase3.suspicion_level:.0%}")
        print(f"  Suspicion State: {'ACTIVE' if system_state['suspicion_state'] else 'INACTIVE'}")
        
        # Final Decision
        print(f"\n🎯 FINAL DECISION:")
        print(f"  Alert Level: {decision['alert_level']}")
        print(f"  Confidence: {decision['confidence']:.0%}")
        print(f"  Should Alert: {'YES' if decision['should_alert'] else 'NO'}")
        
        print(f"\n{'='*70}")
    
    def run_continuous_monitoring(self, 
                                   sensor_reader,
                                   check_interval: int = 5,
                                   print_status: bool = True):
        """
        Run continuous monitoring loop
        
        Args:
            sensor_reader: Object with read_sensors() method
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
                
                # Read sensors
                raw_sensors = sensor_reader.read_sensors()
                
                # Process through all phases
                system_state = self.process_sensor_data(raw_sensors)
                
                # Print status if requested
                if print_status:
                    self.print_system_status(system_state, iteration)
                
                # Check for alert
                if system_state['should_alert']:
                    self.trigger_alert(system_state)
                
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
        
        print(f"\n🔄 Processing:")
        print(f"  Total iterations: {self.processing_count}")
        print(f"  Vision activations: {self.vision_activations}")
        print(f"  Alerts triggered: {self.alerts_triggered}")
        
        print(f"\n🧠 Phase-0:")
        self.phase0_fusion.print_statistics()
        
        print(f"\n🔬 Phase-2:")
        stats2 = self.phase2_fractal.get_statistics()
        for key, value in stats2.items():
            print(f"  {key}: {value}")
        
        print(f"\n⚡ Phase-3:")
        stats3 = self.phase3_chaos.get_statistics()
        for key, value in stats3.items():
            print(f"  {key}: {value}")
        
        if self.alert_history:
            print(f"\n🚨 ALERT HISTORY ({len(self.alert_history)} total):")
            for alert in self.alert_history[-5:]:  # Show last 5
                print(f"  - {alert['timestamp'].strftime('%H:%M:%S')}: "
                      f"{alert['alert_level']} (confidence={alert['confidence']:.0%})")
        
        print("\n✅ System shutdown complete")


if __name__ == "__main__":
    print("\n🔥 Integrated 4-Phase Fire Detection System - Production Ready")
    print("=" * 70)
    print("\nNOTE: This system requires REAL sensor hardware.")
    print("      Connect to: RealSensorInterface or compatible sensor reader")
    print("\nUsage:")
    print("  from real_sensor_interface import RealSensorInterface")
    print("  sensor_reader = RealSensorInterface()")
    print("  system = IntegratedFireDetectionSystem()")
    print("  system.run_continuous_monitoring(sensor_reader)")
    print("=" * 70)
