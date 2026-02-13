"""
PHASE-4 MULTI-SPECTRAL VISION WRAPPER
Integrates RGB (Phase4VisionMamba) + Thermal (ThermalProcessor) with automatic mode switching

This wrapper provides:
- Power-gated thermal support (follows same activation pattern as RGB)
- Automatic day/night mode selection
- Simple integration layer that doesn't modify existing working code
"""

from typing import Optional
import numpy as np
from datetime import datetime
from .vision_mamba import Phase4VisionMamba, VisionMambaOutput, CameraHealthStatus, SmokeAnalysisResult
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from processors import thermal_processor


class MultiSpectralVision:
    """
    Wrapper that integrates RGB and Thermal vision with automatic mode switching
    
    Usage:
      # Initialize with both processors
      vision = MultiSpectralVision()
      
      # Power-gated: Only call when Phase-2/3 trigger
      if should_activate_vision():
          if is_night():
              thermal_frame = read_thermal_sensor()
              result = vision.process(thermal_frame=thermal_frame)
          else:
              rgb_frame = capture_camera()
              result = vision.process(rgb_frame=rgb_frame)
    """
    
    def __init__(self, enable_thermal: bool = True):
        """
        Initialize multi-spectral vision
        
        Args:
            enable_thermal: Whether to enable thermal camera support
        """
        # RGB processor (existing)
        self.rgb_vision = Phase4VisionMamba()
        
        # Thermal processor (new)
        self.enable_thermal = enable_thermal
        if enable_thermal:
            self.thermal_proc = thermal_processor.ThermalProcessor()
        else:
            self.thermal_proc = None
        
        # Statistics
        self.day_mode_count = 0
        self.night_mode_count = 0
        self.dual_mode_count = 0
    
    def process(self,
                rgb_frame: Optional[np.ndarray] = None,
                thermal_frame: Optional[np.ndarray] = None,
                timestamp: Optional[datetime] = None) -> VisionMambaOutput:
        """
        Process camera frames with automatic mode selection
        
        Args:
            rgb_frame: Optional RGB camera frame
            thermal_frame: Optional thermal camera frame
            timestamp: Current timestamp
        
        Returns:
            VisionMambaOutput with fire detection results
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Determine mode
        has_rgb = rgb_frame is not None
        has_thermal = thermal_frame is not None and self.enable_thermal
        
        if has_rgb and not has_thermal:
            # DAY MODE - RGB only
            self.day_mode_count += 1
            return self.rgb_vision.process(rgb_frame, timestamp)
        
        elif has_thermal and not has_rgb:
            # NIGHT MODE - Thermal only
            self.night_mode_count += 1
            return self._process_thermal_mode(thermal_frame, timestamp)
        
        elif has_rgb and has_thermal:
            # DUAL MODE - Both available (twilight)
            self.dual_mode_count += 1
            return self._process_dual_mode(rgb_frame, thermal_frame, timestamp)
        
        else:
            # BLIND MODE - No cameras
            return self._blind_mode_output(timestamp)
    
    def _process_thermal_mode(self, 
                              thermal_frame: np.ndarray,
                              timestamp: datetime) -> VisionMambaOutput:
        """
        Process thermal camera only (night mode)
        
        Args:
            thermal_frame: Thermal camera frame (temperatures in Celsius)
            timestamp: Current timestamp
        
        Returns:
            VisionMambaOutput with thermal-based fire detection
        """
        # Process thermal frame
        thermal_state = self.thermal_proc.process(thermal_frame)
        
        # Convert thermal state to smoke analysis format
        # (reuse existing data structure for compatibility)
        thermal_analysis = SmokeAnalysisResult(
            smoke_confidence=thermal_state['hot_spot_presence'],  # Hot spots = fire
            edge_sharpness=thermal_state['thermal_gradient'],     # Gradient strength
            histogram_variance=thermal_state['spread_pattern'],   # Growth rate
            is_ambiguous=thermal_state['hot_spot_presence'] < 0.6,
            requires_confirmation=0.3 < thermal_state['hot_spot_presence'] < 0.6,
            timestamp=timestamp
        )
        
        # Camera health (thermal sensor status)
        thermal_health = CameraHealthStatus(
            is_healthy=thermal_state['thermal_confidence'] > 0.5,
            health_score=thermal_state['thermal_confidence'],
            failure_reasons=[] if thermal_state['thermal_confidence'] > 0.5 else ['low_confidence'],
            timestamp=timestamp,
            frame_valid=True,
            exposure_ok=True,
            brightness_ok=True,
            not_frozen=True
        )
        
        # Vision weight (higher at night since thermal is primary)
        vision_weight = 0.35 * thermal_state['thermal_confidence']  # 35% max at night
        
        return VisionMambaOutput(
            camera_health=thermal_health,
            smoke_analysis=thermal_analysis,
            vision_mode='night',
            vision_weight=vision_weight,
            confidence=thermal_state['thermal_confidence']
        )
    
    def _process_dual_mode(self,
                          rgb_frame: np.ndarray,
                          thermal_frame: np.ndarray,
                          timestamp: datetime) -> VisionMambaOutput:
        """
        Process both RGB and thermal (twilight mode)
        
        Args:
            rgb_frame: RGB camera frame
            thermal_frame: Thermal camera frame
            timestamp: Current timestamp
        
        Returns:
            VisionMambaOutput with fused detection
        """
        # Process both sensors
        rgb_result = self.rgb_vision.process(rgb_frame, timestamp)
        thermal_state = self.thermal_proc.process(thermal_frame)
        
        # Fuse confidences (weighted average)
        rgb_conf = rgb_result.smoke_analysis.smoke_confidence if rgb_result.smoke_analysis else 0.0
        thermal_conf = thermal_state['hot_spot_presence']
        
        # Thermal gets more weight in twilight (60/40 split)
        fused_confidence = 0.4 * rgb_conf + 0.6 * thermal_conf
        
        # Create fused analysis
        fused_analysis = SmokeAnalysisResult(
            smoke_confidence=fused_confidence,
            edge_sharpness=rgb_result.smoke_analysis.edge_sharpness if rgb_result.smoke_analysis else 0.0,
            histogram_variance=thermal_state['spread_pattern'],
            is_ambiguous=fused_confidence < 0.6,
            requires_confirmation=0.3 < fused_confidence < 0.6,
            timestamp=timestamp
        )
        
        # Vision weight (both contributing)
        vision_weight = 0.4 * (rgb_result.camera_health.health_score + thermal_state['thermal_confidence']) / 2
        
        return VisionMambaOutput(
            camera_health=rgb_result.camera_health,
            smoke_analysis=fused_analysis,
            vision_mode='dual',
            vision_weight=vision_weight,
            confidence=fused_confidence
        )
    
    def _blind_mode_output(self, timestamp: datetime) -> VisionMambaOutput:
        """Return blind mode output when no cameras available"""
        return VisionMambaOutput(
            camera_health=CameraHealthStatus(
                is_healthy=False,
                health_score=0.0,
                failure_reasons=['no_camera_data'],
                timestamp=timestamp
            ),
            smoke_analysis=None,
            vision_mode='blind',
            vision_weight=0.0,
            confidence=0.0
        )
    
    def get_statistics(self):
        """Get combined statistics from both processors"""
        stats = {
            'day_mode_activations': self.day_mode_count,
            'night_mode_activations': self.night_mode_count,
            'dual_mode_activations': self.dual_mode_count,
            'rgb_stats': self.rgb_vision.get_statistics(),
        }
        
        if self.thermal_proc:
            stats['thermal_stats'] = self.thermal_proc.get_statistics()
        
        return stats


if __name__ == "__main__":
    print("\n🌓 Phase-4 Multi-Spectral Vision - RGB + Thermal Integration")
    print("=" * 70)
    print("\nAutomatic Mode Switching:")
    print("  - Day: RGB smoke detection")
    print("  - Night: Thermal heat detection")
    print("  - Twilight: Fused dual-sensor detection")
    print("\nPower-Gated:")
    print("  - Only activates when Phase-2/3 trigger")
    print("  - Follows same activation pattern as current system")
    print("\nUsage:")
    print("  vision = MultiSpectralVision()")
    print("  if should_activate_vision():")
    print("      result = vision.process(thermal_frame=frame)")
    print("=" * 70)
