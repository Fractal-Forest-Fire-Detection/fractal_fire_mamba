"""
PHASE-3: CHAOS KERNEL
Nonlinear Dynamics & Instability Detection

Core Question: "Is this stable or explosive?"

Phase-2 confirmed the signal is structured (not random).
Phase-3 now asks: Is this structure stable or unstable (dangerous)?

Key Insight:
- Stable structure: A campfire (stays in one place)
- Unstable structure: A forest fire (exponential growth, self-reinforcing)

Lyapunov Exponent (λ) measures the Butterfly Effect:
- λ < 0: Stable (deviations die out)
- λ > 0: Chaotic/Explosive (deviations amplify)

When λ > 0: Positive feedback loop detected (fire feeds on itself)
This triggers SUSPICION STATE, not immediate alarm.

NO SIMULATED DATA - Works only with real sensor time series.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque


@dataclass
class ChaosAnalysisResult:
    """
    Results from chaos/instability analysis
    
    Attributes:
        lyapunov_exponent: Lyapunov exponent (λ). λ > 0 indicates chaos/instability
        is_unstable: Whether system shows explosive behavior
        positive_feedback: Degree of self-reinforcing dynamics (0.0-1.0)
        suspicion_level: How suspicious the dynamics are (0.0-1.0)
        confidence: Statistical confidence in the result (0.0-1.0)
        timestamp: When analysis was performed
    """
    lyapunov_exponent: float = 0.0
    is_unstable: bool = False
    positive_feedback: float = 0.0
    suspicion_level: float = 0.0
    confidence: float = 0.0
    timestamp: Optional[datetime] = None
    
    # Diagnostic info
    window_size: int = 0
    samples_analyzed: int = 0
    divergence_rate: float = 0.0


class Phase3ChaosKernel:
    """
    Phase-3: Chaos Kernel for Instability Detection
    
    Uses Lyapunov exponent analysis to distinguish between:
    - Stable processes (λ < 0): Normal environmental changes
    - Unstable processes (λ > 0): Runaway behavior (fire)
    
    Positive Lyapunov exponent indicates:
    - Exponential divergence of nearby trajectories
    - Sensitivity to initial conditions (butterfly effect)
    - Self-reinforcing feedback loops
    - Deterministic chaos or explosion
    
    Technical Details:
    - Uses phase space reconstruction
    - Requires minimum 40 samples for reliable estimation
    - Analyzes risk scores and temporal trends from Phase-0
    """
    
    def __init__(self,
                 lyapunov_threshold: float = 0.0,
                 min_window_size: int = 40,
                 max_window_size: int = 120,
                 embedding_dimension: int = 3):
        """
        Initialize Chaos Kernel
        
        Args:
            lyapunov_threshold: Minimum λ value for instability (default: 0.0)
            min_window_size: Minimum samples needed for analysis
            max_window_size: Maximum samples to retain in buffer
            embedding_dimension: Dimension for phase space reconstruction
        """
        self.lyapunov_threshold = lyapunov_threshold
        self.min_window_size = min_window_size
        self.max_window_size = max_window_size
        self.embedding_dimension = embedding_dimension
        
        # Time series buffer (stores Phase-0 risk scores and trends)
        self.risk_score_history = deque(maxlen=max_window_size)
        
        # Statistics
        self.analysis_count = 0
        self.instability_detected_count = 0
        self.last_analysis: Optional[ChaosAnalysisResult] = None
    
    def update(self, 
               risk_score: float, 
               temporal_trend: float,
               timestamp: datetime) -> ChaosAnalysisResult:
        """
        Update chaos analysis with new data from Phase-0
        
        Args:
            risk_score: Fire risk score from Phase-0 fusion (0.0-1.0)
            temporal_trend: Trend from Mamba SSM (rising/falling)
            timestamp: Current timestamp
        
        Returns:
            ChaosAnalysisResult with instability detection decision
        """
        # Add to history buffer
        self.risk_score_history.append({
            'risk_score': risk_score,
            'temporal_trend': temporal_trend,
            'timestamp': timestamp
        })
        
        # Need minimum samples for reliable analysis
        if len(self.risk_score_history) < self.min_window_size:
            return ChaosAnalysisResult(
                lyapunov_exponent=0.0,
                is_unstable=False,
                positive_feedback=0.0,
                suspicion_level=0.0,
                confidence=0.0,
                timestamp=timestamp,
                window_size=len(self.risk_score_history),
                samples_analyzed=len(self.risk_score_history),
                divergence_rate=0.0
            )
        
        # Extract time series
        risk_series = np.array([h['risk_score'] for h in self.risk_score_history])
        trend_series = np.array([h['temporal_trend'] for h in self.risk_score_history])
        
        # Compute Lyapunov exponent
        lyapunov, confidence = self._compute_lyapunov_exponent(risk_series)
        
        # Detect positive feedback loops
        positive_feedback = self._detect_positive_feedback(risk_series, trend_series)
        
        # Compute divergence rate
        divergence = self._compute_divergence_rate(risk_series)
        
        # Suspicion level (combines multiple indicators)
        suspicion = self._compute_suspicion_level(
            lyapunov, positive_feedback, divergence
        )
        
        # Instability detection decision
        is_unstable = (
            lyapunov > self.lyapunov_threshold and 
            positive_feedback > 0.5 and
            confidence > 0.6
        )
        
        # Create result
        result = ChaosAnalysisResult(
            lyapunov_exponent=lyapunov,
            is_unstable=is_unstable,
            positive_feedback=positive_feedback,
            suspicion_level=suspicion,
            confidence=confidence,
            timestamp=timestamp,
            window_size=len(self.risk_score_history),
            samples_analyzed=len(risk_series),
            divergence_rate=divergence
        )
        
        # Update statistics
        self.analysis_count += 1
        if is_unstable:
            self.instability_detected_count += 1
        
        self.last_analysis = result
        
        return result
    
    def _compute_lyapunov_exponent(self, 
                                   time_series: np.ndarray) -> Tuple[float, float]:
        """
        Compute Lyapunov exponent using phase space reconstruction
        
        Lyapunov exponent measures rate of exponential divergence:
        - λ < 0: Trajectories converge (stable)
        - λ = 0: Neutral stability
        - λ > 0: Trajectories diverge (chaos/explosion)
        
        Args:
            time_series: Time series of risk scores
        
        Returns:
            (lyapunov_exponent, confidence)
        """
        n = len(time_series)
        
        if n < self.min_window_size:
            return 0.0, 0.0
        
        # Phase space reconstruction using time-delay embedding
        embedded = self._time_delay_embedding(time_series, self.embedding_dimension)
        
        if embedded.shape[0] < 2:
            return 0.0, 0.0
        
        # Compute average logarithmic divergence
        divergences = []
        
        for i in range(len(embedded) - 1):
            # Current point
            x0 = embedded[i]
            
            # Next point
            x1 = embedded[i + 1]
            
            # Distance between points
            d0 = np.linalg.norm(x1 - x0)
            
            if d0 > 0:
                # Look ahead a few steps
                if i + 5 < len(embedded):
                    x_future = embedded[i + 5]
                    d_future = np.linalg.norm(x_future - x0)
                    
                    if d_future > 0:
                        # Logarithmic divergence rate
                        divergence = np.log(d_future / d0) / 5.0
                        divergences.append(divergence)
        
        if len(divergences) == 0:
            return 0.0, 0.0
        
        # Lyapunov exponent is average divergence rate
        lyapunov = np.mean(divergences)
        
        # Confidence based on sample size and stability of estimate
        confidence = min(1.0, len(divergences) / 30.0)
        if len(divergences) > 5:
            std_divergence = np.std(divergences)
            stability = 1.0 / (1.0 + std_divergence)
            confidence *= stability
        
        # Clamp to reasonable range
        lyapunov = max(-2.0, min(2.0, lyapunov))
        
        return lyapunov, confidence
    
    def _time_delay_embedding(self, 
                              time_series: np.ndarray, 
                              dimension: int,
                              delay: int = 1) -> np.ndarray:
        """
        Reconstruct phase space using time-delay embedding
        
        Takens' theorem: A time series can be embedded in higher dimensions
        to reveal the underlying dynamical system.
        
        Args:
            time_series: 1D time series
            dimension: Embedding dimension
            delay: Time delay (default: 1)
        
        Returns:
            Matrix of embedded vectors
        """
        n = len(time_series)
        m = n - (dimension - 1) * delay
        
        if m <= 0:
            return np.array([])
        
        embedded = np.zeros((m, dimension))
        
        for i in range(dimension):
            embedded[:, i] = time_series[i * delay : i * delay + m]
        
        return embedded
    
    def _detect_positive_feedback(self,
                                  risk_series: np.ndarray,
                                  trend_series: np.ndarray) -> float:
        """
        Detect positive feedback loops (self-reinforcing behavior)
        
        Fire is a positive feedback system:
        Heat → Dries fuel → Burns faster → More heat
        
        Indicators:
        - Rising risk score correlates with positive trends
        - Acceleration (rate of change increasing)
        - Convexity (upward curvature)
        
        Args:
            risk_series: Risk score time series
            trend_series: Temporal trend time series
        
        Returns:
            Positive feedback score (0.0-1.0)
        """
        if len(risk_series) < 10:
            return 0.0
        
        # 1. Check for correlation between risk and trend
        # When risk is high, trend should be positive (rising)
        recent_risk = risk_series[-10:]
        recent_trend = trend_series[-10:]
        
        correlation = np.corrcoef(recent_risk, recent_trend)[0, 1]
        correlation = max(0.0, correlation)  # Only positive correlation matters
        
        # 2. Check for acceleration (second derivative > 0)
        # Risk score should be accelerating, not just increasing
        if len(risk_series) >= 20:
            # First derivative (velocity)
            velocity = np.diff(risk_series)
            
            # Second derivative (acceleration)
            acceleration = np.diff(velocity)
            
            # Average recent acceleration
            recent_acceleration = np.mean(acceleration[-5:]) if len(acceleration) >= 5 else 0.0
            
            # Normalize to [0, 1]
            acceleration_score = max(0.0, min(1.0, recent_acceleration * 10.0))
        else:
            acceleration_score = 0.0
        
        # 3. Check for convexity (upward curvature)
        if len(risk_series) >= 15:
            # Fit quadratic to recent data
            x = np.arange(len(recent_risk))
            coeffs = np.polyfit(x, recent_risk, 2)
            
            # Positive second-order coefficient = upward curvature
            curvature_score = max(0.0, min(1.0, coeffs[0] * 100.0))
        else:
            curvature_score = 0.0
        
        # Combined positive feedback score
        feedback = 0.4 * correlation + 0.3 * acceleration_score + 0.3 * curvature_score
        
        return feedback
    
    def _compute_divergence_rate(self, risk_series: np.ndarray) -> float:
        """
        Compute rate at which system is diverging from baseline
        
        Args:
            risk_series: Risk score time series
        
        Returns:
            Divergence rate
        """
        if len(risk_series) < 10:
            return 0.0
        
        # Baseline (early readings)
        baseline = np.mean(risk_series[:min(10, len(risk_series) // 3)])
        
        # Current state (recent readings)
        current = np.mean(risk_series[-10:])
        
        # Divergence (normalized)
        divergence = (current - baseline) / (baseline + 0.01)
        
        return max(0.0, divergence)
    
    def _compute_suspicion_level(self,
                                lyapunov: float,
                                positive_feedback: float,
                                divergence: float) -> float:
        """
        Compute overall suspicion level from multiple indicators
        
        Args:
            lyapunov: Lyapunov exponent
            positive_feedback: Positive feedback score
            divergence: Divergence rate
        
        Returns:
            Suspicion level (0.0-1.0)
        """
        # Normalize Lyapunov to [0, 1]
        # λ = 0.0 → 0.5 (neutral)
        # λ > 1.0 → 1.0 (highly suspicious)
        lyapunov_score = (lyapunov + 1.0) / 2.0
        lyapunov_score = max(0.0, min(1.0, lyapunov_score))
        
        # Normalize divergence
        divergence_score = min(1.0, divergence / 2.0)
        
        # Weighted combination
        suspicion = (
            0.4 * lyapunov_score +
            0.4 * positive_feedback +
            0.2 * divergence_score
        )
        
        return suspicion
    
    def reset(self):
        """Reset chaos kernel (clear history buffer)"""
        self.risk_score_history.clear()
        self.last_analysis = None
    
    def get_statistics(self) -> Dict:
        """Get chaos kernel statistics"""
        instability_rate = (
            self.instability_detected_count / self.analysis_count
            if self.analysis_count > 0 else 0.0
        )
        
        return {
            'analyses_performed': self.analysis_count,
            'instability_detected': self.instability_detected_count,
            'instability_detection_rate': instability_rate,
            'buffer_size': len(self.risk_score_history),
            'last_lyapunov': self.last_analysis.lyapunov_exponent if self.last_analysis else 0.0,
            'last_suspicion': self.last_analysis.suspicion_level if self.last_analysis else 0.0
        }
    
    def get_suspicion_state(self) -> str:
        """
        Get current suspicion state
        
        Returns:
            "STABLE", "MONITORING", "SUSPICIOUS", or "UNSTABLE"
        """
        if self.last_analysis is None:
            return "MONITORING"
        
        suspicion = self.last_analysis.suspicion_level
        
        if self.last_analysis.is_unstable:
            return "UNSTABLE"
        elif suspicion > 0.6:
            return "SUSPICIOUS"
        elif suspicion > 0.3:
            return "MONITORING"
        else:
            return "STABLE"


# ============================================================================
#  UTILITY FUNCTIONS
# ============================================================================

def print_chaos_analysis(result: ChaosAnalysisResult):
    """
    Print human-readable chaos analysis results
    
    Args:
        result: ChaosAnalysisResult to display
    """
    print("\n" + "="*70)
    print("⚡ PHASE-3: CHAOS KERNEL ANALYSIS")
    print("="*70)
    
    print(f"\nLyapunov Exponent: {result.lyapunov_exponent:.3f}")
    
    # Interpret Lyapunov value
    if result.lyapunov_exponent < -0.5:
        interpretation = "Strongly stable (deviations die out)"
    elif result.lyapunov_exponent < 0.0:
        interpretation = "Stable (converging)"
    elif result.lyapunov_exponent < 0.5:
        interpretation = "Weakly unstable"
    elif result.lyapunov_exponent < 1.0:
        interpretation = "Chaotic dynamics"
    else:
        interpretation = "Explosive behavior"
    
    print(f"Interpretation: {interpretation}")
    print(f"Positive Feedback: {result.positive_feedback:.0%}")
    print(f"Divergence Rate: {result.divergence_rate:.3f}")
    print(f"Suspicion Level: {result.suspicion_level:.0%}")
    print(f"Confidence: {result.confidence:.0%}")
    
    print(f"\n📊 Analysis Details:")
    print(f"  Samples analyzed: {result.samples_analyzed}")
    print(f"  Window size: {result.window_size}")
    
    print(f"\n⚡ Chaos Kernel Decision:")
    if result.is_unstable:
        print("  ⚠️  INSTABILITY DETECTED - Positive feedback loop")
        print("  🔍 SUSPICION STATE: Activated")
        print("  🎥 VISION VERIFICATION: Required")
    else:
        if result.suspicion_level > 0.5:
            print("  ⚠️  SUSPICIOUS - Monitoring closely")
        else:
            print("  ✅ STABLE - No explosive behavior detected")
    
    print("="*70)


if __name__ == "__main__":
    print("\n⚡ Phase-3 Chaos Kernel - Production Ready")
    print("=" * 70)
    print("\nNOTE: This module requires REAL risk scores and trends from Phase-0.")
    print("      No simulation or fake data is included.")
    print("\nUsage:")
    print("  chaos_kernel = Phase3ChaosKernel()")
    print("  result = chaos_kernel.update(risk_score, trend, timestamp)")
    print("  if result.is_unstable:")
    print("      # Trigger suspicion state and vision verification")
    print("=" * 70)
