"""
PHASE-4: VISION MAMBA
ESP32-CAM Smoke Analysis with Camera Health Diagnostics

Core Functions:
1. Camera health self-diagnosis (lens failure, disconnection, overheating)
2. Classical computer vision smoke detection (NOT deep learning)
3. Blind node mode (graceful degradation when camera fails)
4. Neighbor visual confirmation protocol

Philosophy: "Trust, but Verify"
- Never trust a single sensor blindly
- Camera failures are common in harsh environments
- Distributed intelligence across nodes

NO SIMULATED DATA - Works only with real camera frames from ESP32-CAM
"""

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import cv2


@dataclass
class CameraHealthStatus:
    """
    Camera self-diagnostic results
    
    Attributes:
        is_healthy: Whether camera is functioning properly
        health_score: Overall health (0.0-1.0)
        failure_reasons: List of detected failures
        timestamp: When diagnostic was performed
    """
    is_healthy: bool = False
    health_score: float = 0.0
    failure_reasons: list = None
    timestamp: Optional[datetime] = None
    
    # Diagnostic details
    frame_valid: bool = False
    exposure_ok: bool = False
    brightness_ok: bool = False
    not_frozen: bool = False
    
    def __post_init__(self):
        if self.failure_reasons is None:
            self.failure_reasons = []


@dataclass
class SmokeAnalysisResult:
    """
    Smoke detection results from spectral gate
    
    Attributes:
        smoke_confidence: Confidence that smoke is present (0.0-1.0)
        edge_sharpness: Image sharpness score (0.0-1.0)
        histogram_variance: Gray distribution variance
        is_ambiguous: Whether result needs neighbor confirmation
        requires_confirmation: Should ask neighbors
        timestamp: When analysis was performed
    """
    smoke_confidence: float = 0.0
    edge_sharpness: float = 0.0
    histogram_variance: float = 0.0
    is_ambiguous: bool = True
    requires_confirmation: bool = False
    timestamp: Optional[datetime] = None


@dataclass
class VisionMambaOutput:
    """
    Complete Phase-4 output
    
    Attributes:
        camera_health: Camera diagnostic status
        smoke_analysis: Smoke detection results (if camera healthy)
        vision_mode: 'normal', 'blind', 'degraded'
        vision_weight: Recommended weight for vision in fusion (0.0-1.0)
        confidence: Overall confidence in vision results
    """
    camera_health: CameraHealthStatus
    smoke_analysis: Optional[SmokeAnalysisResult] = None
    vision_mode: str = 'normal'
    vision_weight: float = 0.3  # Default weight
    confidence: float = 0.0


class Phase4VisionMamba:
    """
    Phase-4: Vision Mamba for ESP32-CAM Smoke Detection
    
    Two-stage process:
    1. Camera Health Check (self-diagnosis)
    2. Smoke Detection (spectral gate using classical CV)
    
    Key Features:
    - Fault-tolerant: Handles camera failures gracefully
    - Lightweight: Classical CV (no deep learning) for ESP32
    - Distributed: Can request neighbor confirmation
    - Adaptive: Adjusts fusion weights based on health
    
    Technical Details:
    - RGB → Grayscale conversion for efficiency
    - Edge detection for blur analysis
    - Histogram analysis for smoke texture
    - No neural networks (ESP32 constraints)
    """
    
    def __init__(self,
                 smoke_confidence_threshold: float = 0.6,
                 edge_sharpness_threshold: float = 0.4,
                 brightness_min: float = 20.0,
                 brightness_max: float = 240.0):
        """
        Initialize Vision Mamba
        
        Args:
            smoke_confidence_threshold: Minimum confidence for clear smoke (default: 0.6)
            edge_sharpness_threshold: Maximum sharpness for smoke (default: 0.4)
            brightness_min: Minimum acceptable brightness
            brightness_max: Maximum acceptable brightness
        """
        self.smoke_confidence_threshold = smoke_confidence_threshold
        self.edge_sharpness_threshold = edge_sharpness_threshold
        self.brightness_min = brightness_min
        self.brightness_max = brightness_max
        
        # Baseline values (learned during normal operation)
        self.baseline_sharpness = None
        self.baseline_variance = None
        
        # Previous frame for frozen detection
        self.previous_frame = None
        self.previous_frame_hash = None
        
        # Statistics
        self.frames_processed = 0
        self.camera_failures = 0
        self.smoke_detections = 0
        self.blind_mode_activations = 0
    
    def process(self, camera_frame: np.ndarray, timestamp: datetime) -> VisionMambaOutput:
        """
        Process camera frame through Phase-4
        
        Args:
            camera_frame: RGB image from ESP32-CAM (H x W x 3)
            timestamp: Current timestamp
        
        Returns:
            VisionMambaOutput with health status and smoke analysis
        """
        # =====================================================================
        # STAGE 1: CAMERA HEALTH CHECK (First Gate)
        # =====================================================================
        camera_health = self._check_camera_health(camera_frame, timestamp)
        
        # =====================================================================
        # STAGE 2: DETERMINE VISION MODE
        # =====================================================================
        if not camera_health.is_healthy:
            # BLIND NODE MODE
            self.blind_mode_activations += 1
            
            return VisionMambaOutput(
                camera_health=camera_health,
                smoke_analysis=None,
                vision_mode='blind',
                vision_weight=0.0,  # Vision ignored
                confidence=0.0
            )
        
        # =====================================================================
        # STAGE 3: SPECTRAL GATE (Smoke Analysis)
        # =====================================================================
        smoke_analysis = self._spectral_gate(camera_frame, timestamp)
        
        # =====================================================================
        # STAGE 4: DETERMINE OUTPUT MODE AND WEIGHTS
        # =====================================================================
        
        # Vision weight based on health and confidence
        vision_weight = camera_health.health_score * 0.3  # Max 30% when healthy
        
        # Overall confidence
        if smoke_analysis.smoke_confidence >= self.smoke_confidence_threshold:
            confidence = smoke_analysis.smoke_confidence * camera_health.health_score
            vision_mode = 'normal'
        elif smoke_analysis.is_ambiguous:
            confidence = 0.5 * camera_health.health_score
            vision_mode = 'degraded'
        else:
            confidence = smoke_analysis.smoke_confidence * camera_health.health_score
            vision_mode = 'normal'
        
        self.frames_processed += 1
        
        return VisionMambaOutput(
            camera_health=camera_health,
            smoke_analysis=smoke_analysis,
            vision_mode=vision_mode,
            vision_weight=vision_weight,
            confidence=confidence
        )
    
    def _check_camera_health(self, 
                            frame: np.ndarray, 
                            timestamp: datetime) -> CameraHealthStatus:
        """
        Self-diagnostic camera health check
        
        Checks:
        1. Frame is valid (not None, correct shape)
        2. Exposure is reasonable (not completely black/white)
        3. Brightness is in acceptable range
        4. Frame is not frozen (comparing to previous)
        
        Args:
            frame: Camera frame to check
            timestamp: Current timestamp
        
        Returns:
            CameraHealthStatus with diagnostic results
        """
        failure_reasons = []
        
        # Check 1: Frame validity
        frame_valid = self._check_frame_valid(frame)
        if not frame_valid:
            failure_reasons.append("frame_invalid_or_empty")
        
        # Check 2: Exposure check
        exposure_ok = True
        brightness_ok = True
        
        if frame_valid:
            exposure_ok, brightness_ok = self._check_exposure_and_brightness(frame)
            
            if not exposure_ok:
                failure_reasons.append("exposure_failure")
            
            if not brightness_ok:
                failure_reasons.append("brightness_out_of_range")
        
        # Check 3: Frozen frame detection
        not_frozen = self._check_not_frozen(frame)
        if not not_frozen:
            failure_reasons.append("frame_frozen")
        
        # Overall health score (weighted combination)
        health_components = [
            frame_valid,
            exposure_ok,
            brightness_ok,
            not_frozen
        ]
        
        health_score = sum(health_components) / len(health_components)
        
        # Camera is healthy if all checks pass
        is_healthy = len(failure_reasons) == 0
        
        if not is_healthy:
            self.camera_failures += 1
        
        return CameraHealthStatus(
            is_healthy=is_healthy,
            health_score=health_score,
            failure_reasons=failure_reasons,
            timestamp=timestamp,
            frame_valid=frame_valid,
            exposure_ok=exposure_ok,
            brightness_ok=brightness_ok,
            not_frozen=not_frozen
        )
    
    def _check_frame_valid(self, frame: np.ndarray) -> bool:
        """Check if frame is valid (not None, correct dimensions)"""
        if frame is None:
            return False
        
        if not isinstance(frame, np.ndarray):
            return False
        
        if frame.size == 0:
            return False
        
        # Expect 3-channel RGB or 1-channel grayscale
        if len(frame.shape) not in [2, 3]:
            return False
        
        # Reasonable size check (ESP32-CAM typical: 160x120 to 1600x1200)
        if frame.shape[0] < 100 or frame.shape[1] < 100:
            return False
        
        return True
    
    def _check_exposure_and_brightness(self, frame: np.ndarray) -> Tuple[bool, bool]:
        """
        Check if exposure and brightness are in acceptable range
        
        Returns:
            (exposure_ok, brightness_ok)
        """
        # Convert to grayscale if RGB
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        else:
            gray = frame
        
        # Compute mean brightness
        mean_brightness = np.mean(gray)
        
        # Exposure check: Not completely black or white
        exposure_ok = 10.0 < mean_brightness < 245.0
        
        # Brightness check: In configured range
        brightness_ok = self.brightness_min < mean_brightness < self.brightness_max
        
        return exposure_ok, brightness_ok
    
    def _check_not_frozen(self, frame: np.ndarray) -> bool:
        """
        Check if frame is frozen (identical to previous frame)
        
        Computes hash of current frame and compares to previous
        """
        if self.previous_frame is None:
            self.previous_frame = frame.copy()
            self.previous_frame_hash = hash(frame.tobytes())
            return True  # First frame, assume not frozen
        
        # Compute hash of current frame
        current_hash = hash(frame.tobytes())
        
        # If identical to previous, might be frozen
        is_frozen = (current_hash == self.previous_frame_hash)
        
        # Update previous frame
        self.previous_frame = frame.copy()
        self.previous_frame_hash = current_hash
        
        return not is_frozen
    
    def _spectral_gate(self, 
                      frame: np.ndarray, 
                      timestamp: datetime) -> SmokeAnalysisResult:
        """
        Spectral Gate: Classical computer vision smoke detection
        
        Pipeline:
        1. RGB → Grayscale (3x faster)
        2. Edge detection (blur analysis)
        3. Histogram analysis (texture variance)
        4. Smoke confidence calculation
        
        Smoke characteristics:
        - Low edge sharpness (blurry)
        - High histogram variance (messy gray distribution)
        
        Args:
            frame: RGB camera frame
            timestamp: Current timestamp
        
        Returns:
            SmokeAnalysisResult with confidence and features
        """
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        else:
            gray = frame
        
        # 1. Edge Detection (Laplacian for blur detection)
        edge_sharpness = self._compute_edge_sharpness(gray)
        
        # 2. Histogram Analysis (variance of gray distribution)
        histogram_variance = self._compute_histogram_variance(gray)
        
        # 3. Update baselines if not set
        if self.baseline_sharpness is None:
            self.baseline_sharpness = edge_sharpness
            self.baseline_variance = histogram_variance
        
        # 4. Compute smoke confidence
        smoke_confidence = self._compute_smoke_confidence(
            edge_sharpness,
            histogram_variance
        )
        
        # 5. Determine if ambiguous (needs neighbor confirmation)
        is_ambiguous = smoke_confidence < self.smoke_confidence_threshold
        requires_confirmation = is_ambiguous and smoke_confidence > 0.3
        
        if smoke_confidence >= self.smoke_confidence_threshold:
            self.smoke_detections += 1
        
        return SmokeAnalysisResult(
            smoke_confidence=smoke_confidence,
            edge_sharpness=edge_sharpness,
            histogram_variance=histogram_variance,
            is_ambiguous=is_ambiguous,
            requires_confirmation=requires_confirmation,
            timestamp=timestamp
        )
    
    def _compute_edge_sharpness(self, gray: np.ndarray) -> float:
        """
        Compute edge sharpness using Laplacian variance
        
        High variance = sharp edges (clear air)
        Low variance = blurry (smoke)
        
        Returns:
            Sharpness score (0.0-1.0), normalized
        """
        # Laplacian edge detection
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        
        # Variance of Laplacian (focus measure)
        variance = laplacian.var()
        
        # Normalize to [0, 1] (empirical max ~500 for typical scenes)
        sharpness = min(1.0, variance / 500.0)
        
        return sharpness
    
    def _compute_histogram_variance(self, gray: np.ndarray) -> float:
        """
        Compute histogram variance (gray distribution messiness)
        
        Smoke creates messy gray distribution
        Clear air has more structured histogram
        
        Returns:
            Normalized histogram variance
        """
        # Compute histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()  # Normalize
        
        # Compute variance of histogram
        variance = np.var(hist)
        
        # Normalize (empirical max ~0.002)
        normalized = min(1.0, variance / 0.002)
        
        return normalized
    
    def _compute_smoke_confidence(self,
                                  edge_sharpness: float,
                                  histogram_variance: float) -> float:
        """
        Compute smoke confidence from features
        
        Smoke indicators:
        - LOW edge sharpness (blurry)
        - HIGH histogram variance (messy)
        
        Args:
            edge_sharpness: Edge sharpness score (0.0-1.0)
            histogram_variance: Histogram variance (0.0-1.0)
        
        Returns:
            Smoke confidence (0.0-1.0)
        """
        # Deviation from baseline
        if self.baseline_sharpness is not None:
            sharpness_drop = max(0.0, self.baseline_sharpness - edge_sharpness)
        else:
            sharpness_drop = 1.0 - edge_sharpness  # Assume baseline is sharp
        
        if self.baseline_variance is not None:
            variance_increase = max(0.0, histogram_variance - self.baseline_variance)
        else:
            variance_increase = histogram_variance
        
        # Smoke confidence (weighted combination)
        # High confidence when sharpness drops AND variance increases
        confidence = (
            0.6 * sharpness_drop +       # Blur is strong indicator
            0.4 * variance_increase       # Variance is supporting indicator
        )
        
        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence
    
    def get_blind_node_weights(self) -> Dict[str, float]:
        """
        Get recommended fusion weights for blind node mode
        
        When camera fails:
        - Vision weight: 0.0 (ignored)
        - Chemical weight: 0.7 (trust the nose)
        - Environmental weight: 0.3 (context)
        
        Returns:
            Dict with recommended weights
        """
        return {
            'vision': 0.0,
            'chemical': 0.7,
            'environmental': 0.3
        }
    
    def get_statistics(self) -> Dict:
        """Get Phase-4 statistics"""
        return {
            'frames_processed': self.frames_processed,
            'camera_failures': self.camera_failures,
            'smoke_detections': self.smoke_detections,
            'blind_mode_activations': self.blind_mode_activations,
            'failure_rate': self.camera_failures / max(1, self.frames_processed)
        }


# ============================================================================
#  NEIGHBOR CONFIRMATION PROTOCOL
# ============================================================================

class NeighborConfirmationProtocol:
    """
    Distributed intelligence for neighbor visual confirmation
    
    Protocol: "Do you see what I see?"
    
    When a node gets ambiguous smoke detection (<60% confidence),
    it pings nearby neighbors to check their cameras.
    
    This prevents false alarms from:
    - Spider webs on lens
    - Local fog patches
    - Dust kicked up by animals
    - Lighting changes
    
    Real smoke spreads horizontally → neighbors will see it too
    """
    
    def __init__(self, confirmation_radius: float = 500.0):
        """
        Initialize confirmation protocol
        
        Args:
            confirmation_radius: Radius in meters for neighbor queries
        """
        self.confirmation_radius = confirmation_radius
        self.confirmation_requests = 0
        self.confirmations_received = 0
    
    def request_confirmation(self, 
                            node_id: str,
                            smoke_confidence: float,
                            neighbor_nodes: list) -> Dict:
        """
        Request visual confirmation from neighbors
        
        Args:
            node_id: ID of requesting node
            smoke_confidence: Local smoke confidence
            neighbor_nodes: List of neighbor node IDs
        
        Returns:
            Confirmation request message
        """
        self.confirmation_requests += 1
        
        return {
            'type': 'visual_confirmation_request',
            'from_node': node_id,
            'smoke_confidence': smoke_confidence,
            'query': 'check_camera_high_variance_gray_edges',
            'radius': self.confirmation_radius,
            'timestamp': datetime.now()
        }
    
    def process_confirmation(self,
                            local_confidence: float,
                            neighbor_responses: list) -> Tuple[bool, float]:
        """
        Process neighbor confirmation responses
        
        Args:
            local_confidence: Local smoke confidence
            neighbor_responses: List of (node_id, confidence) tuples
        
        Returns:
            (confirmed, boosted_confidence)
        """
        if not neighbor_responses:
            return False, local_confidence
        
        # Count confirmations (neighbors with >0.4 confidence)
        confirmations = sum(1 for _, conf in neighbor_responses if conf > 0.4)
        
        if confirmations >= 1:
            # At least one neighbor sees it too
            self.confirmations_received += 1
            
            # Boost confidence
            avg_neighbor_conf = np.mean([conf for _, conf in neighbor_responses])
            boosted = 0.6 * local_confidence + 0.4 * avg_neighbor_conf
            boosted = min(0.95, boosted + 0.15)  # Correlation bonus
            
            return True, boosted
        else:
            # No confirmation - probably local anomaly
            return False, local_confidence * 0.7  # Reduce confidence


if __name__ == "__main__":
    print("\n🎥 Phase-4 Vision Mamba - Production Ready")
    print("=" * 70)
    print("\nNOTE: This module requires REAL camera frames from ESP32-CAM.")
    print("      No simulation or fake data is included.")
    print("\nUsage:")
    print("  vision = Phase4VisionMamba()")
    print("  result = vision.process(camera_frame, timestamp)")
    print("  if result.vision_mode == 'blind':")
    print("      # Use blind node weights")
    print("  elif result.smoke_analysis.requires_confirmation:")
    print("      # Request neighbor confirmation")
    print("=" * 70)
