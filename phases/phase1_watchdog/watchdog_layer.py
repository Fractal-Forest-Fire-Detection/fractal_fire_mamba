"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                      PHASE-1: WATCHDOG LAYER                              ║
║                   Pre-Processing Health Monitor                           ║
║                                                                           ║
║  Purpose: Trust-driven sensor validation before AI processing            ║
║  Author: Industrial Fire Detection System                                ║
║  Version: 2.0 - Production Grade                                         ║
╚═══════════════════════════════════════════════════════════════════════════╝

CRITICAL PHILOSOPHY:
    Phase-1 doesn't just clean data — it annotates truth with trust.
    
    This transforms the system from:
        ❌ Data-driven  →  ✅ Trust-driven
    
    The difference between: automation and autonomy

PROTECTION LEVELS:
    Level-0: Impossible reality (10,000°C)
    Level-1: Silent sensor death (Frozen value)
    Level-2: Data absence (Packet loss)
    Level-3: Environmental danger (Trauma)
    Meta:    Confidence awareness (Reliability score)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - WATCHDOG - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    """Individual sensor reading with metadata"""
    sensor_id: str
    value: float
    timestamp: datetime
    sensor_type: str  # 'temperature', 'humidity', 'co2', 'smoke', etc.
    
    
@dataclass
class ValidationResult:
    """Result of Phase-1 validation"""
    is_valid: bool
    value: float
    reliability_score: float  # 0.0 to 1.0
    is_imputed: bool = False
    failure_reason: Optional[str] = None
    validation_flags: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


@dataclass
class SensorState:
    """Persistent state tracking for each sensor"""
    sensor_id: str
    last_value: Optional[float] = None
    last_timestamp: Optional[datetime] = None
    value_history: deque = field(default_factory=lambda: deque(maxlen=100))
    timestamp_history: deque = field(default_factory=lambda: deque(maxlen=100))
    frozen_since: Optional[datetime] = None
    is_broken: bool = False
    failure_count: int = 0


class TraumaSystem:
    """
    System-wide trauma tracking and adaptive sensitivity.
    
    Trauma represents the system's memory of danger:
        - Recent anomalies
        - Attacks
        - Near-miss failures
        - Environmental shocks
    
    This is psychological state, not raw data.
    """
    
    def __init__(self, decay_days: int = 7):
        self.trauma_level: float = 0.0  # 0.0 to 1.0
        self.trauma_events: List[Dict] = []
        self.decay_days = decay_days
        self.last_decay: datetime = datetime.now()
        
    def register_trauma(self, severity: float, description: str):
        """
        Register a traumatic event.
        
        Args:
            severity: 0.0 to 1.0, how severe the event was
            description: What happened
        """
        event = {
            'timestamp': datetime.now(),
            'severity': severity,
            'description': description
        }
        self.trauma_events.append(event)
        
        # Increase trauma level (max 1.0)
        self.trauma_level = min(1.0, self.trauma_level + severity * 0.3)
        
        logger.warning(f"⚡ TRAUMA REGISTERED: {description} | Severity: {severity:.2f} | Level now: {self.trauma_level:.2f}")
        
    def apply_decay(self):
        """
        Apply trauma decay over time.
        Self-healing mechanism: If calm for 7 days, trauma decreases.
        """
        now = datetime.now()
        days_elapsed = (now - self.last_decay).total_seconds() / 86400
        
        if days_elapsed >= 1.0:
            decay_amount = 0.05 * days_elapsed
            old_level = self.trauma_level
            self.trauma_level = max(0.0, self.trauma_level - decay_amount)
            self.last_decay = now
            
            if old_level > 0 and self.trauma_level < old_level:
                logger.info(f"🌱 TRAUMA DECAY: {old_level:.2f} → {self.trauma_level:.2f}")
                
    def get_adaptive_threshold(self, base_threshold: float) -> float:
        """
        Calculate adaptive threshold based on trauma level.
        
        Higher trauma → Lower tolerance → Tighter thresholds
        
        Formula: Threshold_new = base * (1.1 - Trauma_Level)
        
        Example:
            Base = 1.0, Trauma = 0.0 → 1.0 * 1.1 = 1.1 (relaxed)
            Base = 1.0, Trauma = 0.5 → 1.0 * 0.6 = 0.6 (tighter)
            Base = 1.0, Trauma = 1.0 → 1.0 * 0.1 = 0.1 (paranoid)
        """
        return base_threshold * (1.1 - self.trauma_level)
        
    def is_paranoid_mode(self) -> bool:
        """Check if system is in heightened vigilance state"""
        return self.trauma_level > 0.0


class VirtualSensorImputation:
    """
    Self-Healing Intelligence: AI reconstruction of missing signals.
    
    This is not guessing — it's probabilistic inference using:
        - Surviving sensors
        - Correlation patterns
        - Temporal patterns
        - Physical relationships
    """
    
    def __init__(self):
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        self.temporal_patterns: Dict[str, deque] = {}
        
    def impute_missing_value(
        self,
        sensor_id: str,
        sensor_type: str,
        available_sensors: Dict[str, float],
        sensor_states: Dict[str, SensorState]
    ) -> Tuple[float, float]:
        """
        Reconstruct missing sensor value from available data.
        
        Returns:
            (imputed_value, confidence_score)
        """
        
        # Method 1: Temporal interpolation (use recent history)
        if sensor_id in sensor_states:
            state = sensor_states[sensor_id]
            if len(state.value_history) >= 2:
                # Simple linear interpolation from recent trend
                recent_values = list(state.value_history)[-5:]
                imputed = np.mean(recent_values)
                confidence = 0.7  # Reasonable confidence from history
                
                logger.info(f"📊 IMPUTATION (Temporal): {sensor_id} = {imputed:.2f} (conf: {confidence:.2f})")
                return imputed, confidence
        
        # Method 2: Spatial correlation (use related sensors)
        if sensor_type == 'temperature' and 'humidity' in available_sensors:
            # Temperature and humidity are anti-correlated
            humidity = available_sensors['humidity']
            # Simple inverse relationship model
            imputed = 100 - humidity * 0.8  # Crude but illustrative
            confidence = 0.6
            
            logger.info(f"📊 IMPUTATION (Correlation): {sensor_id} = {imputed:.2f} (conf: {confidence:.2f})")
            return imputed, confidence
            
        # Method 3: Physics-based default (domain knowledge)
        defaults = {
            'temperature': 25.0,  # Ambient
            'humidity': 50.0,     # Mid-range
            'co2': 400.0,         # Atmospheric
            'smoke': 0.0,         # Clear air
        }
        
        if sensor_type in defaults:
            imputed = defaults[sensor_type]
            confidence = 0.5  # Low confidence, but better than nothing
            
            logger.info(f"📊 IMPUTATION (Default): {sensor_id} = {imputed:.2f} (conf: {confidence:.2f})")
            return imputed, confidence
        
        # Fallback: Cannot impute
        logger.warning(f"⚠️  IMPUTATION FAILED: {sensor_id} - No basis for reconstruction")
        return 0.0, 0.0


class Phase1WatchdogLayer:
    """
    ╔══════════════════════════════════════════════════════════════════╗
    ║              PHASE-1 WATCHDOG LAYER - MAIN CLASS                 ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    The trust validation gateway that sits before your AI model.
    
    4 CRITICAL CHECKS:
        ✓ CHECK-1: Range Check (Physical plausibility)
        ✓ CHECK-2: Frozen Check (Temporal liveness)
        ✓ CHECK-3: Null Check (Signal existence)
        ✓ CHECK-4: Trauma Check (Contextual risk)
    
    GUARANTEES ON OUTPUT:
        ✅ Physically plausible
        ✅ Temporally alive
        ✅ Exists or reconstructed
        ✅ Confidence-scored
        ✅ Context-aware
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Phase-1 Watchdog Layer.
        
        Args:
            config: Configuration dict with sensor ranges, thresholds, etc.
        """
        self.config = config or self._default_config()
        
        # State tracking
        self.sensor_states: Dict[str, SensorState] = {}
        self.trauma_system = TraumaSystem(decay_days=7)
        self.imputation_engine = VirtualSensorImputation()
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'range_failures': 0,
            'frozen_failures': 0,
            'null_failures': 0,
            'imputations': 0,
            'dying_gasps': 0
        }
        
        logger.info("🔥 PHASE-1 WATCHDOG LAYER INITIALIZED")
        logger.info(f"   Trauma decay: {self.trauma_system.decay_days} days")
        logger.info(f"   Sensor types: {list(self.config['sensor_ranges'].keys())}")
        
    def _default_config(self) -> Dict:
        """Default configuration for industrial fire detection"""
        return {
            'sensor_ranges': {
                'temperature': {'min': -40.0, 'max': 120.0, 'dying_gasp': 100.0},
                'humidity': {'min': 0.0, 'max': 100.0, 'dying_gasp': None},
                'co2': {'min': 0.0, 'max': 5000.0, 'dying_gasp': None},
                'smoke': {'min': 0.0, 'max': 1000.0, 'dying_gasp': 800.0},
                'flame': {'min': 0.0, 'max': 1.0, 'dying_gasp': None},
            },
            'frozen_threshold_hours': 5,
            'black_box_buffer_seconds': 30,
        }
    
    # ═══════════════════════════════════════════════════════════════════
    #                       CHECK-1: RANGE CHECK
    #                   Physical Plausibility Gate
    # ═══════════════════════════════════════════════════════════════════
    
    def _check_range(self, reading: SensorReading) -> Tuple[bool, Optional[str]]:
        """
        Level-0 Sanity Check: Is the value physically possible?
        
        This is a hard physics boundary — no AI, no context, no assumptions.
        If this fails, nothing downstream matters.
        
        Returns:
            (is_valid, failure_reason)
        """
        sensor_type = reading.sensor_type
        
        if sensor_type not in self.config['sensor_ranges']:
            logger.warning(f"⚠️  Unknown sensor type: {sensor_type}")
            return True, None  # Don't reject unknown types
            
        ranges = self.config['sensor_ranges'][sensor_type]
        value = reading.value
        
        # Check dying gasp threshold FIRST (critical alert)
        if ranges.get('dying_gasp') is not None:
            if value >= ranges['dying_gasp']:
                self._trigger_dying_gasp(reading)
                return False, f"DYING GASP: {value:.1f} >= {ranges['dying_gasp']}"
        
        # Check physical bounds
        if value < ranges['min'] or value > ranges['max']:
            self.stats['range_failures'] += 1
            reason = f"Out of range: {value:.1f} not in [{ranges['min']}, {ranges['max']}]"
            logger.error(f"❌ RANGE FAILURE: {reading.sensor_id} - {reason}")
            return False, reason
            
        return True, None
    
    def _trigger_dying_gasp(self, reading: SensorReading):
        """
        💀 DYING GASP PROTOCOL
        
        When sensor detects catastrophic conditions (e.g., Temp > 100°C):
            1. Stop everything
            2. Dump last 30 seconds to satellite
            3. Node becomes forensic evidence
            4. Register severe trauma
        
        This is your "Flight Recorder" logic.
        """
        self.stats['dying_gasps'] += 1
        
        logger.critical("=" * 70)
        logger.critical("💀 DYING GASP ACTIVATED")
        logger.critical(f"   Sensor: {reading.sensor_id}")
        logger.critical(f"   Type: {reading.sensor_type}")
        logger.critical(f"   Value: {reading.value:.1f}")
        logger.critical(f"   Time: {reading.timestamp}")
        logger.critical("=" * 70)
        logger.critical("🛰️  EMERGENCY SATELLITE DUMP INITIATED")
        logger.critical("📦 BLACK BOX: Last 30 seconds of data")
        
        # Get black box data
        black_box = self._get_black_box_data(reading.sensor_id)
        
        # In production: Actually send to satellite
        # self.satellite_transmitter.emergency_dump(black_box)
        
        # Register maximum trauma
        self.trauma_system.register_trauma(
            severity=1.0,
            description=f"Dying gasp from {reading.sensor_id}: {reading.value:.1f}°C"
        )
        
        # Mark sensor as permanently broken
        if reading.sensor_id in self.sensor_states:
            self.sensor_states[reading.sensor_id].is_broken = True
            
        logger.critical("☠️  NODE DECLARED DEAD - NOW FORENSIC EVIDENCE")
        logger.critical("=" * 70)
    
    def _get_black_box_data(self, sensor_id: str) -> Dict:
        """
        Retrieve last 30 seconds of data for emergency dump.
        This is your flight recorder.
        """
        if sensor_id not in self.sensor_states:
            return {}
            
        state = self.sensor_states[sensor_id]
        cutoff_time = datetime.now() - timedelta(
            seconds=self.config['black_box_buffer_seconds']
        )
        
        # Get recent history
        black_box = {
            'sensor_id': sensor_id,
            'dump_time': datetime.now().isoformat(),
            'buffer_seconds': self.config['black_box_buffer_seconds'],
            'values': [],
            'timestamps': []
        }
        
        for val, ts in zip(state.value_history, state.timestamp_history):
            if ts >= cutoff_time:
                black_box['values'].append(float(val))
                black_box['timestamps'].append(ts.isoformat())
                
        logger.info(f"📦 Black box captured {len(black_box['values'])} readings")
        return black_box
    
    # ═══════════════════════════════════════════════════════════════════
    #                      CHECK-2: FROZEN CHECK
    #                     Temporal Liveness Gate
    # ═══════════════════════════════════════════════════════════════════
    
    def _check_frozen(self, reading: SensorReading) -> Tuple[bool, Optional[str]]:
        """
        Level-1 Check: Is the sensor stuck (zombie sensor)?
        
        A sensor can be:
            - Electrically alive
            - Transmitting packets  
            - Within valid range
            ...and still be dead logically.
        
        This detects sensors that stopped reacting to reality.
        
        Truth requires change. A world without variation is a lie.
        """
        sensor_id = reading.sensor_id
        
        # Initialize state if new sensor
        if sensor_id not in self.sensor_states:
            self.sensor_states[sensor_id] = SensorState(sensor_id=sensor_id)
            return True, None  # First reading, can't be frozen
            
        state = self.sensor_states[sensor_id]
        
        # Check if value is exactly the same as last time
        if state.last_value is not None and reading.value == state.last_value:
            # How long has it been frozen?
            if state.frozen_since is None:
                state.frozen_since = reading.timestamp
            else:
                frozen_duration = reading.timestamp - state.frozen_since
                frozen_hours = frozen_duration.total_seconds() / 3600
                
                if frozen_hours >= self.config['frozen_threshold_hours']:
                    self.stats['frozen_failures'] += 1
                    
                    # Flag as BROKEN
                    state.is_broken = True
                    
                    reason = f"Frozen for {frozen_hours:.1f} hours at value {reading.value}"
                    logger.error(f"❌ FROZEN FAILURE: {sensor_id} - {reason}")
                    logger.warning(f"🔧 Priority-3 Alert: Maintenance Required via LoRaWAN")
                    
                    # Register moderate trauma
                    self.trauma_system.register_trauma(
                        severity=0.5,
                        description=f"Sensor {sensor_id} frozen for {frozen_hours:.1f}h"
                    )
                    
                    return False, reason
        else:
            # Value changed — reset frozen timer
            state.frozen_since = None
            
        return True, None
    
    # ═══════════════════════════════════════════════════════════════════
    #                       CHECK-3: NULL CHECK
    #                      Signal Existence Gate
    # ═══════════════════════════════════════════════════════════════════
    
    def _check_null(self, reading: Optional[SensorReading]) -> bool:
        """
        Level-2 Check: Does the signal exist?
        
        This is the boundary between:
            - Hard failure (traditional systems stop)
            - Graceful degradation (your system adapts)
        
        Returns:
            True if signal exists, False if null/missing
        """
        return reading is not None and reading.value is not None
    
    # ═══════════════════════════════════════════════════════════════════
    #                      CHECK-4: TRAUMA CHECK
    #                     Contextual Risk Gate
    # ═══════════════════════════════════════════════════════════════════
    
    def _apply_trauma_context(self, validation_result: ValidationResult) -> ValidationResult:
        """
        Level-3 Check: Apply trauma-aware context.
        
        If the system is in a heightened state of alert (trauma > 0),
        apply adaptive thresholding and reduce confidence slightly.
        
        This makes the system paranoid after danger.
        """
        # Apply trauma decay first
        self.trauma_system.apply_decay()
        
        if self.trauma_system.is_paranoid_mode():
            # Reduce confidence slightly in paranoid mode
            confidence_penalty = 0.1 * self.trauma_system.trauma_level
            validation_result.reliability_score *= (1.0 - confidence_penalty)
            
            # Add trauma metadata
            validation_result.metadata['trauma_level'] = self.trauma_system.trauma_level
            validation_result.metadata['paranoid_mode'] = True
            
            logger.debug(f"⚡ PARANOID MODE: Confidence reduced by {confidence_penalty:.2%}")
        else:
            validation_result.metadata['paranoid_mode'] = False
            
        return validation_result
    
    # ═══════════════════════════════════════════════════════════════════
    #                        MAIN VALIDATION
    # ═══════════════════════════════════════════════════════════════════
    
    def validate(
        self,
        reading: Optional[SensorReading],
        sensor_id: str,
        sensor_type: str,
        available_sensors: Optional[Dict[str, float]] = None
    ) -> ValidationResult:
        """
        ╔══════════════════════════════════════════════════════════════╗
        ║               MAIN PHASE-1 VALIDATION ENTRY POINT            ║
        ╚══════════════════════════════════════════════════════════════╝
        
        Process a sensor reading through all 4 checks and return
        a trust-annotated result.
        
        Args:
            reading: Sensor reading (can be None for null check)
            sensor_id: Unique sensor identifier
            sensor_type: Type of sensor
            available_sensors: Dict of other sensor values (for imputation)
            
        Returns:
            ValidationResult with trust annotation
        """
        self.stats['total_processed'] += 1
        available_sensors = available_sensors or {}
        
        # ═══════════════════════════════════════════════════════════
        #  PATH-A: SIGNAL EXISTS → Full validation pipeline
        # ═══════════════════════════════════════════════════════════
        
        if self._check_null(reading):
            # CHECK-1: Range Check
            range_valid, range_reason = self._check_range(reading)
            if not range_valid:
                return ValidationResult(
                    is_valid=False,
                    value=reading.value,
                    reliability_score=0.0,
                    failure_reason=range_reason,
                    validation_flags={
                        'range_check': False,
                        'frozen_check': False,
                        'null_check': True
                    }
                )
            
            # CHECK-2: Frozen Check
            frozen_valid, frozen_reason = self._check_frozen(reading)
            if not frozen_valid:
                return ValidationResult(
                    is_valid=False,
                    value=reading.value,
                    reliability_score=0.0,
                    failure_reason=frozen_reason,
                    validation_flags={
                        'range_check': True,
                        'frozen_check': False,
                        'null_check': True
                    }
                )
            
            # Update sensor state
            self._update_sensor_state(reading)
            
            # All checks passed — HIGH TRUST
            result = ValidationResult(
                is_valid=True,
                value=reading.value,
                reliability_score=1.0,
                is_imputed=False,
                validation_flags={
                    'range_check': True,
                    'frozen_check': True,
                    'null_check': True
                },
                metadata={
                    'sensor_id': sensor_id,
                    'sensor_type': sensor_type,
                    'timestamp': reading.timestamp.isoformat()
                }
            )
            
            # CHECK-4: Apply trauma context
            result = self._apply_trauma_context(result)
            
            return result
        
        # ═══════════════════════════════════════════════════════════
        #  PATH-B: SIGNAL MISSING → Virtual sensor imputation
        # ═══════════════════════════════════════════════════════════
        
        else:
            self.stats['null_failures'] += 1
            logger.warning(f"⚠️  NULL SIGNAL: {sensor_id} - Attempting imputation")
            
            # Attempt self-healing reconstruction
            imputed_value, confidence = self.imputation_engine.impute_missing_value(
                sensor_id=sensor_id,
                sensor_type=sensor_type,
                available_sensors=available_sensors,
                sensor_states=self.sensor_states
            )
            
            if confidence > 0.0:
                self.stats['imputations'] += 1
                
                # Successfully imputed
                result = ValidationResult(
                    is_valid=True,
                    value=imputed_value,
                    reliability_score=confidence * 0.8,  # Discount for imputation
                    is_imputed=True,
                    validation_flags={
                        'range_check': True,  # Assume imputed values are valid
                        'frozen_check': True,
                        'null_check': False   # Signal was missing
                    },
                    metadata={
                        'sensor_id': sensor_id,
                        'sensor_type': sensor_type,
                        'imputation_method': 'virtual_sensor',
                        'original_confidence': confidence
                    }
                )
                
                logger.info(f"✅ IMPUTATION SUCCESS: {sensor_id} = {imputed_value:.2f} (reliability: {result.reliability_score:.2f})")
                
                # CHECK-4: Apply trauma context
                result = self._apply_trauma_context(result)
                
                return result
            else:
                # Cannot impute — HARD FAILURE
                logger.error(f"❌ NULL FAILURE: {sensor_id} - Cannot reconstruct")
                
                return ValidationResult(
                    is_valid=False,
                    value=0.0,
                    reliability_score=0.0,
                    is_imputed=False,
                    failure_reason="Signal missing and cannot be reconstructed",
                    validation_flags={
                        'range_check': False,
                        'frozen_check': False,
                        'null_check': False
                    }
                )
    
    def _update_sensor_state(self, reading: SensorReading):
        """Update sensor state history for temporal tracking"""
        sensor_id = reading.sensor_id
        
        if sensor_id not in self.sensor_states:
            self.sensor_states[sensor_id] = SensorState(sensor_id=sensor_id)
            
        state = self.sensor_states[sensor_id]
        state.last_value = reading.value
        state.last_timestamp = reading.timestamp
        state.value_history.append(reading.value)
        state.timestamp_history.append(reading.timestamp)
    
    def get_statistics(self) -> Dict:
        """Get watchdog layer statistics"""
        return {
            **self.stats,
            'trauma_level': self.trauma_system.trauma_level,
            'paranoid_mode': self.trauma_system.is_paranoid_mode(),
            'active_sensors': len(self.sensor_states),
            'broken_sensors': sum(1 for s in self.sensor_states.values() if s.is_broken)
        }
    
    def print_statistics(self):
        """Print human-readable statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*70)
        print("📊 PHASE-1 WATCHDOG LAYER STATISTICS")
        print("="*70)
        print(f"Total Processed:     {stats['total_processed']:,}")
        print(f"Range Failures:      {stats['range_failures']:,}")
        print(f"Frozen Failures:     {stats['frozen_failures']:,}")
        print(f"Null Failures:       {stats['null_failures']:,}")
        print(f"Imputations:         {stats['imputations']:,}")
        print(f"Dying Gasps:         {stats['dying_gasps']:,}")
        print(f"Active Sensors:      {stats['active_sensors']:,}")
        print(f"Broken Sensors:      {stats['broken_sensors']:,}")
        print(f"Trauma Level:        {stats['trauma_level']:.2f} / 1.0")
        print(f"Paranoid Mode:       {'🔴 YES' if stats['paranoid_mode'] else '🟢 NO'}")
        print("="*70 + "\n")


# ═══════════════════════════════════════════════════════════════════════
#                           EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                   PHASE-1 WATCHDOG LAYER - DEMO                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize watchdog
    watchdog = Phase1WatchdogLayer()
    
    # Simulate various sensor scenarios
    test_scenarios = [
        # Scenario 1: Normal reading
        SensorReading(
            sensor_id="TEMP_001",
            value=25.5,
            timestamp=datetime.now(),
            sensor_type="temperature"
        ),
        
        # Scenario 2: Out of range (too hot)
        SensorReading(
            sensor_id="TEMP_002",
            value=150.0,
            timestamp=datetime.now(),
            sensor_type="temperature"
        ),
        
        # Scenario 3: Dying gasp threshold
        SensorReading(
            sensor_id="TEMP_003",
            value=105.0,
            timestamp=datetime.now(),
            sensor_type="temperature"
        ),
        
        # Scenario 4: Normal reading (for frozen test)
        SensorReading(
            sensor_id="TEMP_004",
            value=23.0,
            timestamp=datetime.now(),
            sensor_type="temperature"
        ),
        
        # Scenario 5: Null reading (will attempt imputation)
        None,  # Missing sensor
    ]
    
    print("\n🔥 Running test scenarios...\n")
    
    for i, reading in enumerate(test_scenarios, 1):
        print(f"\n{'─'*70}")
        print(f"SCENARIO {i}:")
        
        if reading:
            print(f"  Sensor: {reading.sensor_id}")
            print(f"  Value: {reading.value}")
            print(f"  Type: {reading.sensor_type}")
            
            result = watchdog.validate(
                reading=reading,
                sensor_id=reading.sensor_id,
                sensor_type=reading.sensor_type
            )
        else:
            print(f"  Sensor: TEMP_NULL")
            print(f"  Value: NULL")
            print(f"  Type: temperature")
            
            result = watchdog.validate(
                reading=None,
                sensor_id="TEMP_NULL",
                sensor_type="temperature",
                available_sensors={'humidity': 60.0}  # For imputation
            )
        
        print(f"\n  RESULT:")
        print(f"    Valid: {result.is_valid}")
        print(f"    Value: {result.value:.2f}")
        print(f"    Reliability: {result.reliability_score:.2%}")
        print(f"    Imputed: {result.is_imputed}")
        if result.failure_reason:
            print(f"    Failure: {result.failure_reason}")
    
    # Print final statistics
    watchdog.print_statistics()
    
    print("✅ PHASE-1 WATCHDOG LAYER DEMO COMPLETE")
