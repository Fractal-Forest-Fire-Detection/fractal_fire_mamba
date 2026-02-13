"""
PHASE-2: FRACTAL GATE (TRAUMA-ADAPTIVE VERSION)
Spectral & Long-Range Structure Detection

Core Question: "Is this random noise, or a structured process unfolding over time?"

This phase acts as a randomness firewall, filtering out false alarms from:
- Random fluctuations
- Short-lived spikes
- Sensor jitter
- Environmental noise

Key Insight: Random processes do not sustain structure across scales.
Real physical phenomena (fire, chemical diffusion) produce fractal, self-similar patterns.

CRITICAL FIX (2026-02-08):
✅ Added trauma-adaptive Hurst threshold
✅ Threshold now dynamically adjusts: base_threshold * (1.1 - trauma_level)
✅ High trauma = lower threshold = more sensitive detection

NO SIMULATED DATA - Works only with real sensor time series.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque


@dataclass
class FractalAnalysisResult:
    """
    Results from fractal structure analysis
    
    Attributes:
        hurst_exponent: Hurst exponent (H). H > threshold indicates strong fractal memory
        has_structure: Whether signal passes fractal gate (trauma-adaptive)
        persistence: Degree of long-range correlation (0.0-1.0)
        confidence: Statistical confidence in the result (0.0-1.0)
        timestamp: When analysis was performed
        trauma_level: Current trauma level used for threshold adaptation
        adaptive_threshold: Actual threshold used (trauma-adjusted)
    """
    hurst_exponent: float = 0.5  # Default: pure randomness
    has_structure: bool = False
    persistence: float = 0.0
    confidence: float = 0.0
    timestamp: Optional[datetime] = None
    
    # Trauma-adaptive parameters (NEW)
    trauma_level: float = 0.0
    adaptive_threshold: float = 1.1
    base_threshold: float = 1.1
    
    # Diagnostic info
    window_size: int = 0
    samples_analyzed: int = 0
    quality_score: float = 0.0


class Phase2FractalGate:
    """
    Phase-2: Fractal Gate for Structure Detection (TRAUMA-ADAPTIVE)
    
    Uses Hurst exponent analysis to distinguish between:
    - Random noise (H ≈ 0.5)
    - Structured physical processes (H > adaptive_threshold)
    
    CRITICAL FEATURE: Threshold adapts based on system trauma:
    - trauma_level = 0.0 → threshold = 1.1 (relaxed, normal operation)
    - trauma_level = 0.5 → threshold = 0.66 (tighter, moderately paranoid)
    - trauma_level = 1.0 → threshold = 0.11 (paranoid, extremely sensitive)
    
    Only signals with H > adaptive_threshold pass through.
    This activates vision processing (power-efficient gating).
    
    Technical Details:
    - Uses R/S (Rescaled Range) analysis
    - Requires minimum 30 samples for reliable estimation
    - Analyzes risk scores from Phase-0 over time
    """
    
    def __init__(self, 
                 base_hurst_threshold: float = 1.1,
                 min_window_size: int = 30,
                 max_window_size: int = 120):
        """
        Initialize Fractal Gate
        
        Args:
            base_hurst_threshold: Base H value (before trauma adjustment, default: 1.1)
            min_window_size: Minimum samples needed for analysis
            max_window_size: Maximum samples to retain in buffer
        """
        self.base_hurst_threshold = base_hurst_threshold  # Base threshold (no trauma)
        self.min_window_size = min_window_size
        self.max_window_size = max_window_size
        
        # Time series buffer (stores Phase-0 risk scores)
        self.risk_score_history = deque(maxlen=max_window_size)
        
        # Statistics
        self.analysis_count = 0
        self.structure_detected_count = 0
        self.last_analysis: Optional[FractalAnalysisResult] = None
        
        # Trauma tracking (NEW)
        self.current_trauma_level = 0.0
        self.threshold_adjustments = 0
    
    def update(self, 
               risk_score: float, 
               timestamp: datetime,
               trauma_level: float = 0.0) -> FractalAnalysisResult:
        """
        Update fractal analysis with new risk score from Phase-0
        
        Args:
            risk_score: Fire risk score from Phase-0 fusion (0.0-1.0)
            timestamp: Current timestamp
            trauma_level: System trauma level from Phase-1 (0.0-1.0, NEW PARAMETER)
        
        Returns:
            FractalAnalysisResult with trauma-adaptive structure detection decision
        """
        # Update trauma tracking
        self.current_trauma_level = trauma_level
        
        # Add to history buffer
        self.risk_score_history.append({
            'risk_score': risk_score,
            'timestamp': timestamp
        })
        
        # Need minimum samples for reliable analysis
        if len(self.risk_score_history) < self.min_window_size:
            return FractalAnalysisResult(
                hurst_exponent=0.5,
                has_structure=False,
                persistence=0.0,
                confidence=0.0,
                timestamp=timestamp,
                trauma_level=trauma_level,
                adaptive_threshold=self._compute_adaptive_threshold(trauma_level),
                base_threshold=self.base_hurst_threshold,
                window_size=len(self.risk_score_history),
                samples_analyzed=len(self.risk_score_history),
                quality_score=0.0
            )
        
        # Extract time series
        time_series = np.array([h['risk_score'] for h in self.risk_score_history])
        
        # Compute Hurst exponent
        hurst, confidence = self._compute_hurst_exponent(time_series)
        
        # Compute persistence (normalized H value)
        persistence = self._compute_persistence(hurst)
        
        # Quality score (based on sample size and variance)
        quality = self._compute_quality_score(time_series)
        
        # ✅ CRITICAL FIX: Compute trauma-adaptive threshold
        adaptive_threshold = self._compute_adaptive_threshold(trauma_level)
        
        # ✅ Structure detection decision (NOW TRAUMA-ADAPTIVE)
        has_structure = (hurst > adaptive_threshold) and (confidence > 0.6)
        
        # Track threshold adjustments
        if trauma_level > 0.0:
            self.threshold_adjustments += 1
        
        # Create result
        result = FractalAnalysisResult(
            hurst_exponent=hurst,
            has_structure=has_structure,
            persistence=persistence,
            confidence=confidence,
            timestamp=timestamp,
            trauma_level=trauma_level,
            adaptive_threshold=adaptive_threshold,
            base_threshold=self.base_hurst_threshold,
            window_size=len(self.risk_score_history),
            samples_analyzed=len(time_series),
            quality_score=quality
        )
        
        # Update statistics
        self.analysis_count += 1
        if has_structure:
            self.structure_detected_count += 1
        
        self.last_analysis = result
        
        return result
    
    def _compute_adaptive_threshold(self, trauma_level: float) -> float:
        """
        ✅ NEW METHOD: Compute trauma-adaptive Hurst threshold
        
        Formula: adaptive_threshold = base_threshold * (1.1 - trauma_level)
        
        This implements the Physics-First trauma memory:
        - Low trauma (0.0): threshold = 1.1 * 1.1 = 1.21 (relaxed)
        - Medium trauma (0.5): threshold = 1.1 * 0.6 = 0.66 (tighter)
        - High trauma (1.0): threshold = 1.1 * 0.1 = 0.11 (paranoid)
        
        Args:
            trauma_level: System trauma level (0.0-1.0)
        
        Returns:
            Adaptive Hurst threshold
        """
        # Clamp trauma to valid range
        trauma_clamped = max(0.0, min(1.0, trauma_level))
        
        # Apply trauma adjustment formula
        # Higher trauma → lower threshold → more sensitive
        adaptive_threshold = self.base_hurst_threshold * (1.1 - trauma_clamped)
        
        # Ensure threshold stays in reasonable bounds
        # Minimum threshold: 0.05 (even in extreme trauma)
        # Maximum threshold: base_threshold * 1.1 (when trauma = 0)
        adaptive_threshold = max(0.05, min(self.base_hurst_threshold * 1.1, adaptive_threshold))
        
        return adaptive_threshold
    
    def _compute_hurst_exponent(self, time_series: np.ndarray) -> Tuple[float, float]:
        """
        Compute Hurst exponent using R/S (Rescaled Range) analysis
        
        The Hurst exponent measures long-range dependence:
        - H ≈ 0.5: Random walk (no memory)
        - H > 0.5: Persistent (trend-reinforcing)
        - H > 1.0: Strong fractal memory
        
        Args:
            time_series: Time series of risk scores
        
        Returns:
            (hurst_exponent, confidence)
        """
        n = len(time_series)
        
        if n < self.min_window_size:
            return 0.5, 0.0
        
        # Remove mean (detrend)
        mean_adjusted = time_series - np.mean(time_series)
        
        # Cumulative sum
        cumsum = np.cumsum(mean_adjusted)
        
        # Range
        R = np.max(cumsum) - np.min(cumsum)
        
        # Standard deviation
        S = np.std(time_series, ddof=1)
        
        # Avoid division by zero
        if S == 0 or R == 0:
            return 0.5, 0.0
        
        # R/S ratio
        RS = R / S
        
        # Hurst exponent from R/S scaling
        # E[R/S] ∝ n^H
        # H = log(R/S) / log(n)
        hurst = np.log(RS) / np.log(n)
        
        # Confidence based on sample size and stability
        confidence = min(1.0, n / 60.0)  # More samples = higher confidence
        
        # Clamp to reasonable range
        hurst = max(0.0, min(2.0, hurst))
        
        return hurst, confidence
    
    def _compute_persistence(self, hurst: float) -> float:
        """
        Convert Hurst exponent to persistence score (0.0-1.0)
        
        Args:
            hurst: Hurst exponent
        
        Returns:
            Persistence score normalized to [0, 1]
        """
        # H = 0.5 → persistence = 0.0 (random)
        # H = 1.5 → persistence = 1.0 (highly persistent)
        persistence = (hurst - 0.5) / 1.0
        
        return max(0.0, min(1.0, persistence))
    
    def _compute_quality_score(self, time_series: np.ndarray) -> float:
        """
        Assess quality of the time series for reliable analysis
        
        Higher quality when:
        - More samples available
        - Non-zero variance (signal present)
        - Not saturated (values not all at extremes)
        
        Args:
            time_series: Time series data
        
        Returns:
            Quality score (0.0-1.0)
        """
        n = len(time_series)
        
        # Sample size quality
        size_quality = min(1.0, n / 60.0)
        
        # Variance quality (has signal)
        variance = np.var(time_series)
        variance_quality = min(1.0, variance / 0.1)  # Normalize by expected variance
        
        # Saturation check (not all 0s or 1s)
        mean_value = np.mean(time_series)
        saturation_quality = 1.0 - abs(mean_value - 0.5) / 0.5
        
        # Combined quality
        quality = 0.5 * size_quality + 0.3 * variance_quality + 0.2 * saturation_quality
        
        return quality
    
    def reset(self):
        """Reset fractal gate (clear history buffer)"""
        self.risk_score_history.clear()
        self.last_analysis = None
        self.current_trauma_level = 0.0
    
    def get_statistics(self) -> Dict:
        """Get fractal gate statistics (now includes trauma info)"""
        structure_rate = (
            self.structure_detected_count / self.analysis_count
            if self.analysis_count > 0 else 0.0
        )
        
        return {
            'analyses_performed': self.analysis_count,
            'structure_detected': self.structure_detected_count,
            'structure_detection_rate': structure_rate,
            'buffer_size': len(self.risk_score_history),
            'last_hurst': self.last_analysis.hurst_exponent if self.last_analysis else 0.5,
            'last_confidence': self.last_analysis.confidence if self.last_analysis else 0.0,
            # NEW: Trauma-adaptive statistics
            'current_trauma_level': self.current_trauma_level,
            'threshold_adjustments': self.threshold_adjustments,
            'last_adaptive_threshold': self.last_analysis.adaptive_threshold if self.last_analysis else self.base_hurst_threshold,
            'base_threshold': self.base_hurst_threshold
        }
    
    def should_activate_vision(self) -> bool:
        """
        Determine if vision processing should be activated
        
        This is the power-efficient gating mechanism:
        - Vision only activates when fractal structure detected
        - Saves battery by avoiding constant camera operation
        - Now trauma-aware: more sensitive after trauma events
        
        Returns:
            True if vision should be activated, False otherwise
        """
        if self.last_analysis is None:
            return False
        
        # Activate vision when structure detected with high confidence
        # (Threshold is already trauma-adaptive in has_structure)
        return (
            self.last_analysis.has_structure and 
            self.last_analysis.confidence > 0.7
        )


# ============================================================================
#  UTILITY FUNCTIONS
# ============================================================================

def print_fractal_analysis(result: FractalAnalysisResult):
    """
    Print human-readable fractal analysis results (NOW WITH TRAUMA INFO)
    
    Args:
        result: FractalAnalysisResult to display
    """
    print("\n" + "="*70)
    print("🔬 PHASE-2: FRACTAL GATE ANALYSIS (TRAUMA-ADAPTIVE)")
    print("="*70)
    
    print(f"\nHurst Exponent: {result.hurst_exponent:.3f}")
    
    # Interpret Hurst value
    if result.hurst_exponent < 0.4:
        interpretation = "Anti-persistent (mean-reverting)"
    elif result.hurst_exponent < 0.6:
        interpretation = "Random walk (no memory)"
    elif result.hurst_exponent < 1.0:
        interpretation = "Persistent trend"
    elif result.hurst_exponent < 1.5:
        interpretation = "Strong fractal memory"
    else:
        interpretation = "Very strong structure"
    
    print(f"Interpretation: {interpretation}")
    print(f"Persistence: {result.persistence:.0%}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Quality Score: {result.quality_score:.0%}")
    
    # ✅ NEW: Display trauma-adaptive threshold info
    print(f"\n🧠 Trauma-Adaptive Threshold:")
    print(f"  Base threshold: {result.base_threshold:.3f}")
    print(f"  Current trauma: {result.trauma_level:.2f}")
    print(f"  Adaptive threshold: {result.adaptive_threshold:.3f}")
    
    # Show trauma state
    if result.trauma_level < 0.2:
        trauma_state = "CALM (Normal sensitivity)"
    elif result.trauma_level < 0.5:
        trauma_state = "ALERT (Heightened sensitivity)"
    elif result.trauma_level < 0.8:
        trauma_state = "STRESSED (High sensitivity)"
    else:
        trauma_state = "PARANOID (Maximum sensitivity)"
    print(f"  Trauma state: {trauma_state}")
    
    print(f"\n📊 Analysis Details:")
    print(f"  Samples analyzed: {result.samples_analyzed}")
    print(f"  Window size: {result.window_size}")
    
    print(f"\n🚪 Fractal Gate Decision:")
    if result.has_structure:
        print("  ✅ STRUCTURE DETECTED - Signal has fractal memory")
        print(f"  📈 H ({result.hurst_exponent:.3f}) > Threshold ({result.adaptive_threshold:.3f})")
        print("  🎥 VISION ACTIVATION: Recommended")
    else:
        print("  ❌ NO STRUCTURE - Likely random noise")
        print(f"  📉 H ({result.hurst_exponent:.3f}) ≤ Threshold ({result.adaptive_threshold:.3f})")
        print("  💤 VISION ACTIVATION: Not needed (power saving)")
    
    print("="*70)


if __name__ == "__main__":
    print("\n🔬 Phase-2 Fractal Gate - TRAUMA-ADAPTIVE VERSION")
    print("=" * 70)
    print("\n✅ FIXED: Dynamic Hurst threshold now adapts to trauma_level")
    print("\nFormula: adaptive_threshold = base_threshold * (1.1 - trauma_level)")
    print("\nNOTE: This module requires REAL risk scores from Phase-0.")
    print("      No simulation or fake data is included.")
    print("\nUsage:")
    print("  fractal_gate = Phase2FractalGate()")
    print("  result = fractal_gate.update(risk_score, timestamp, trauma_level)")
    print("  if fractal_gate.should_activate_vision():")
    print("      # Activate camera and vision processing")
    print("\nTrauma Response Examples:")
    print("  trauma = 0.0 → threshold = 1.21 (relaxed)")
    print("  trauma = 0.5 → threshold = 0.66 (tighter)")
    print("  trauma = 1.0 → threshold = 0.11 (paranoid)")
    print("=" * 70)