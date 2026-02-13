"""
THERMAL PROCESSOR - MLX90640 Thermal Camera Analysis
Handles thermal imaging data for night-time fire detection

Weight: 35% at night (primary), 15% during day (supplementary)

Key Features:
- Hot spot detection (>60°C threshold)
- Temperature gradient analysis (fire has characteristic thermal patterns)
- Temporal growth tracking (spreading hot regions = fire)
- Power-gated: Only runs when Phase-2/3 trigger activation
"""

from typing import Dict, Optional, List
import numpy as np
from collections import deque
from datetime import datetime, timedelta


class ThermalProcessor:
    """
    Processes thermal camera data into fire indicators.
    
    Primary night-time detection modality:
    - Works 24/7 regardless of lighting
    - Direct heat signature detection
    - More reliable than RGB in darkness
    
    Detects:
    1. Hot Spot Presence - Pixels exceeding fire temperature threshold
    2. Temperature Anomaly - Deviation from ambient baseline
    3. Spread Pattern - Growing hot regions over time
    4. Thermal Gradient - Characteristic fire temperature distribution
    
    Note: Designed for MLX90640 (32x24 pixels) but works with any thermal sensor
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize thermal processor with detection parameters
        
        Args:
            config: Optional configuration dict
        """
        self.config = config or self._default_config()
        
        # Baseline values (learned during normal operation)
        self.ambient_baseline = None
        self.max_temp_baseline = None
        
        # Historical tracking for temporal analysis
        self.hot_region_history = deque(maxlen=10)  # Last 10 frames
        self.temperature_history = deque(maxlen=30)  # Last 30 samples
        
        # Statistics
        self.frames_processed = 0
        self.hot_spots_detected = 0
    
    def _default_config(self) -> Dict:
        """
        Default thermal detection parameters
        
        Returns:
            Default config dict
        """
        return {
            # Temperature thresholds (Celsius)
            'fire_threshold': 60.0,          # Hot spot threshold (fire typically >60°C)
            'anomaly_threshold': 20.0,       # Deviation from ambient
            'ambient_max': 40.0,             # Maximum expected ambient temp
            
            # Gradient analysis
            'gradient_threshold': 5.0,       # Min gradient for fire detection (°C/pixel)
            
            # Growth tracking
            'growth_window': 10,             # Number of frames to track growth
            'growth_threshold': 0.2,         # 20% growth = spreading fire
            
            # Quality thresholds
            'min_hot_pixels': 3,             # Minimum hot pixels to consider
            'confidence_threshold': 0.6,     # Minimum confidence for detection
        }
    
    def process(self, thermal_frame: np.ndarray) -> Dict[str, float]:
        """
        Analyze thermal frame for fire indicators
        
        Args:
            thermal_frame: 2D numpy array of temperatures in Celsius (H x W)
                          For MLX90640: 24 x 32 pixels
                          Values should be calibrated temperature readings
        
        Returns:
            Thermal state dict with normalized scores (0.0-1.0):
            {
                'hot_spot_presence': float,    # Fraction of pixels above threshold
                'temperature_anomaly': float,   # Deviation from ambient baseline
                'spread_pattern': float,        # Hot region growth rate
                'thermal_gradient': float,      # Temperature gradient strength
                'thermal_confidence': float     # Overall confidence in reading
            }
        """
        thermal_state = {}
        
        # Validate thermal frame
        if not self._is_valid_frame(thermal_frame):
            return self._zero_state()
        
        # Update baseline if needed
        if self.ambient_baseline is None:
            self._initialize_baseline(thermal_frame)
            return self._zero_state()
        
        # =====================================================================
        # 1. HOT SPOT PRESENCE - Direct fire signature
        # =====================================================================
        hot_spot_score = self._detect_hot_spots(thermal_frame)
        thermal_state['hot_spot_presence'] = hot_spot_score
        
        # =====================================================================
        # 2. TEMPERATURE ANOMALY - Deviation from normal
        # =====================================================================
        anomaly_score = self._detect_temperature_anomaly(thermal_frame)
        thermal_state['temperature_anomaly'] = anomaly_score
        
        # =====================================================================
        # 3. SPREAD PATTERN - Temporal growth tracking
        # =====================================================================
        spread_score = self._analyze_spread_pattern(thermal_frame)
        thermal_state['spread_pattern'] = spread_score
        
        # =====================================================================
        # 4. THERMAL GRADIENT - Spatial fire signature
        # =====================================================================
        gradient_score = self._compute_thermal_gradient(thermal_frame)
        thermal_state['thermal_gradient'] = gradient_score
        
        # =====================================================================
        # 5. THERMAL CONFIDENCE - Overall reliability
        # =====================================================================
        confidence = self._compute_confidence(thermal_frame, thermal_state)
        thermal_state['thermal_confidence'] = confidence
        
        # Update statistics
        self.frames_processed += 1
        if hot_spot_score > 0.5:
            self.hot_spots_detected += 1
        
        return thermal_state
    
    # =========================================================================
    # FRAME VALIDATION
    # =========================================================================
    
    def _is_valid_frame(self, frame: np.ndarray) -> bool:
        """
        Check if thermal frame is valid
        
        Args:
            frame: Thermal frame to validate
        
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(frame, np.ndarray):
            return False
        
        if len(frame.shape) != 2:
            return False
        
        if frame.size == 0:
            return False
        
        # Check for reasonable temperature range (-40 to +400°C)
        if np.min(frame) < -50 or np.max(frame) > 500:
            return False
        
        return True
    
    def _zero_state(self) -> Dict[str, float]:
        """Return zero state when thermal data unavailable"""
        return {
            'hot_spot_presence': 0.0,
            'temperature_anomaly': 0.0,
            'spread_pattern': 0.0,
            'thermal_gradient': 0.0,
            'thermal_confidence': 0.0
        }
    
    # =========================================================================
    # HOT SPOT DETECTION
    # =========================================================================
    
    def _detect_hot_spots(self, thermal_frame: np.ndarray) -> float:
        """
        Detect pixels exceeding fire temperature threshold
        
        Fire typically has surface temperature >60°C in wildfire scenarios
        
        Args:
            thermal_frame: Thermal image (Celsius)
        
        Returns:
            Hot spot score: 0.0 (no hot spots) to 1.0 (many hot spots)
        """
        fire_threshold = self.config['fire_threshold']
        
        # Count pixels above threshold
        hot_pixels = np.sum(thermal_frame > fire_threshold)
        total_pixels = thermal_frame.size
        
        # Require minimum number of hot pixels (avoid single-pixel noise)
        min_hot_pixels = self.config['min_hot_pixels']
        if hot_pixels < min_hot_pixels:
            return 0.0
        
        # Fraction of hot pixels
        hot_fraction = hot_pixels / total_pixels
        
        # Scale to 0-1 (10% hot pixels = max score)
        hot_spot_score = min(hot_fraction * 10, 1.0)
        
        return hot_spot_score
    
    # =========================================================================
    # TEMPERATURE ANOMALY DETECTION
    # =========================================================================
    
    def _detect_temperature_anomaly(self, thermal_frame: np.ndarray) -> float:
        """
        Detect deviation from ambient baseline temperature
        
        Fire creates localized high-temperature anomalies
        
        Args:
            thermal_frame: Thermal image (Celsius)
        
        Returns:
            Anomaly score: 0.0 (normal) to 1.0 (extreme anomaly)
        """
        # Max temperature in frame
        max_temp = np.max(thermal_frame)
        
        # Deviation from baseline
        temp_deviation = max_temp - self.ambient_baseline
        
        # Normalize by anomaly threshold
        anomaly_threshold = self.config['anomaly_threshold']
        anomaly_score = temp_deviation / anomaly_threshold
        
        # Clamp to [0, 1]
        anomaly_score = max(0.0, min(1.0, anomaly_score))
        
        return anomaly_score
    
    # =========================================================================
    # SPREAD PATTERN ANALYSIS
    # =========================================================================
    
    def _analyze_spread_pattern(self, thermal_frame: np.ndarray) -> float:
        """
        Track hot region growth over time
        
        Fire spreads → hot regions grow
        Static hot object → hot region stays constant
        
        Args:
            thermal_frame: Current thermal frame
        
        Returns:
            Spread score: 0.0 (static/shrinking) to 1.0 (rapidly growing)
        """
        fire_threshold = self.config['fire_threshold']
        
        # Count current hot pixels
        current_hot_count = np.sum(thermal_frame > fire_threshold)
        
        # Add to history
        self.hot_region_history.append(current_hot_count)
        
        # Need at least 2 frames for comparison
        if len(self.hot_region_history) < 2:
            return 0.0
        
        # Compare to oldest frame in window
        oldest_hot_count = self.hot_region_history[0]
        
        # Avoid division by zero
        if oldest_hot_count == 0:
            return 1.0 if current_hot_count > 0 else 0.0
        
        # Growth rate
        growth_rate = (current_hot_count - oldest_hot_count) / oldest_hot_count
        
        # Normalize by growth threshold
        growth_threshold = self.config['growth_threshold']
        spread_score = growth_rate / growth_threshold
        
        # Only positive growth (spreading)
        spread_score = max(0.0, min(1.0, spread_score))
        
        return spread_score
    
    # =========================================================================
    # THERMAL GRADIENT ANALYSIS
    # =========================================================================
    
    def _compute_thermal_gradient(self, thermal_frame: np.ndarray) -> float:
        """
        Compute temperature gradient (fire has characteristic spatial patterns)
        
        Fire creates strong thermal gradients:
        - Hot center → cooler edges
        - Gradient magnitude indicates fire boundary
        
        Args:
            thermal_frame: Thermal image
        
        Returns:
            Gradient score: 0.0 (uniform) to 1.0 (strong gradient)
        """
        # Compute spatial gradients
        grad_y = np.gradient(thermal_frame, axis=0)
        grad_x = np.gradient(thermal_frame, axis=1)
        
        # Gradient magnitude
        gradient_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        # Maximum gradient in frame
        max_gradient = np.max(gradient_mag)
        
        # Normalize by gradient threshold
        gradient_threshold = self.config['gradient_threshold']
        gradient_score = max_gradient / gradient_threshold
        
        # Clamp to [0, 1]
        gradient_score = max(0.0, min(1.0, gradient_score))
        
        return gradient_score
    
    # =========================================================================
    # CONFIDENCE COMPUTATION
    # =========================================================================
    
    def _compute_confidence(self, 
                           thermal_frame: np.ndarray, 
                           thermal_state: Dict[str, float]) -> float:
        """
        Compute overall confidence in thermal reading
        
        Higher confidence when:
        - Multiple indicators agree (hot spots + anomaly + gradient)
        - Strong signal (not borderline)
        - Stable baseline available
        
        Args:
            thermal_frame: Thermal image
            thermal_state: Computed thermal state
        
        Returns:
            Confidence: 0.0 (unreliable) to 1.0 (highly confident)
        """
        # Baseline quality
        baseline_quality = 1.0 if self.ambient_baseline is not None else 0.0
        
        # Multi-indicator agreement
        indicators = [
            thermal_state.get('hot_spot_presence', 0.0),
            thermal_state.get('temperature_anomaly', 0.0),
            thermal_state.get('thermal_gradient', 0.0)
        ]
        
        # Count strong indicators (>0.5)
        strong_indicators = sum(1 for score in indicators if score > 0.5)
        agreement_score = strong_indicators / len(indicators)
        
        # Signal strength (avoid borderline detections)
        max_indicator = max(indicators)
        signal_strength = max_indicator
        
        # Combined confidence
        confidence = (
            0.4 * baseline_quality +
            0.3 * agreement_score +
            0.3 * signal_strength
        )
        
        return confidence
    
    # =========================================================================
    # BASELINE CALIBRATION
    # =========================================================================
    
    def _initialize_baseline(self, thermal_frame: np.ndarray):
        """
        Initialize baseline from first clean frame
        
        Args:
            thermal_frame: Clean thermal frame (no fire)
        """
        # Ambient temperature = median of frame
        self.ambient_baseline = np.median(thermal_frame)
        self.max_temp_baseline = np.max(thermal_frame)
    
    def calibrate_baseline(self, clean_frames: List[np.ndarray]):
        """
        Calibrate baseline from multiple clean environment frames
        
        Use this during installation to learn normal thermal signature
        
        Args:
            clean_frames: List of thermal frames from clean environment (no fire)
        """
        if not clean_frames:
            return
        
        ambient_temps = []
        max_temps = []
        
        for frame in clean_frames:
            if self._is_valid_frame(frame):
                ambient_temps.append(np.median(frame))
                max_temps.append(np.max(frame))
        
        if ambient_temps:
            # Use median to avoid outliers
            self.ambient_baseline = np.median(ambient_temps)
            self.max_temp_baseline = np.median(max_temps)
            
            print(f"✅ Thermal baselines calibrated:")
            print(f"   Ambient baseline: {self.ambient_baseline:.1f}°C")
            print(f"   Max temp baseline: {self.max_temp_baseline:.1f}°C")
    
    def get_statistics(self) -> Dict:
        """
        Get processor statistics
        
        Returns:
            Dict with processing stats
        """
        detection_rate = (
            self.hot_spots_detected / self.frames_processed 
            if self.frames_processed > 0 else 0.0
        )
        
        return {
            'frames_processed': self.frames_processed,
            'hot_spots_detected': self.hot_spots_detected,
            'detection_rate': detection_rate,
            'ambient_baseline': self.ambient_baseline,
            'max_temp_baseline': self.max_temp_baseline,
            'config': self.config
        }


if __name__ == "__main__":
    print("\n🌡️ Thermal Processor - MLX90640 Fire Detection")
    print("=" * 70)
    print("\nDesigned for night-time fire detection using thermal imaging")
    print("\nKey Features:")
    print("  - Hot spot detection (>60°C threshold)")
    print("  - Temperature anomaly analysis")
    print("  - Temporal spread pattern tracking")
    print("  - Thermal gradient computation")
    print("\nPower-Gated:")
    print("  - Only activates when Phase-2/3 trigger")
    print("  - Works with existing vision activation logic")
    print("\nHardware:")
    print("  - MLX90640: 32x24 pixels, I2C, 23mA")
    print("  - Works 24/7 regardless of lighting")
    print("=" * 70)
