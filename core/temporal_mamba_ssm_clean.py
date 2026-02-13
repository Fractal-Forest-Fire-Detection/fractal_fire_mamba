"""
TEMPORAL MAMBA SSM (State Space Model)
Phase-0 Temporal Coherence Engine

Replaces snapshot-based fusion with streaming temporal analysis.

Key Features:
- O(N) complexity (unlike transformers O(N²))
- Streaming-friendly (processes data as it arrives)
- Long-horizon memory (remembers patterns from minutes ago)
- Cross-sensor lag detection (learns cause-before-effect)
- Edge-device viable (runs on Raspberry Pi)

Philosophy:
Instead of asking "Is there fire NOW?", we ask:
"What has been happening over the LAST 60 SECONDS?"
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque


@dataclass
class TemporalState:
    """
    Hidden state of the Mamba SSM
    
    This encodes:
    - Trend buildup (gradual vs sudden changes)
    - Persistence (sustained vs transient signals)
    - Cross-sensor lag patterns (cause before effect)
    """
    # Hidden state vector (encodes temporal patterns)
    h: np.ndarray = field(default_factory=lambda: np.zeros(8))
    
    # Trend indicators
    chemical_trend: float = 0.0  # Rising/falling chemical signals
    visual_trend: float = 0.0    # Rising/falling visual signals
    environmental_trend: float = 0.0  # Rising/falling environmental signals
    
    # Persistence indicators
    chemical_persistence: float = 0.0  # How long chemical signal sustained
    visual_persistence: float = 0.0    # How long visual signal sustained
    
    # Cross-modal lag (chemical leads vision by N seconds)
    cross_modal_lag: float = 0.0
    
    # Temporal confidence
    temporal_confidence: float = 0.0
    
    # Last update timestamp
    timestamp: Optional[datetime] = None


class MambaSSM:
    """
    Mamba State Space Model for temporal coherence
    
    Implements a simplified Mamba-style SSM optimized for edge devices.
    
    Architecture:
    x(t) → [Selection] → u(t) → [State Update] → h(t) → [Output] → y(t)
    
    Key differences from RNN/LSTM:
    - Linear recurrence (O(N) not O(N²))
    - Selective state updates (not all data updates state equally)
    - Continuous-time formulation (handles variable sample rates)
    """
    
    def __init__(self, state_dim: int = 8, learning_rate: float = 0.01):
        """
        Initialize Mamba SSM
        
        Args:
            state_dim: Dimension of hidden state (default: 8)
            learning_rate: Learning rate for online adaptation
        """
        self.state_dim = state_dim
        self.learning_rate = learning_rate
        
        # State space matrices (initialized randomly, adapted online)
        self.A = np.eye(state_dim) * 0.9  # State transition (decay)
        self.B = np.random.randn(state_dim, 3) * 0.1  # Input projection
        self.C = np.random.randn(1, state_dim) * 0.1  # Output projection
        
        # Selection mechanism (learns which inputs matter)
        self.selection_weights = np.ones(3) / 3.0  # Start equal
        
        # Current hidden state
        self.state = TemporalState()
        
        # History buffer (last 60 seconds at 1 Hz)
        self.history_buffer = deque(maxlen=60)
        
        # Statistics
        self.update_count = 0
    
    def _selection_mechanism(self, inputs: np.ndarray, dt: float) -> np.ndarray:
        """
        Selective gating: decide which inputs to let through
        
        Key insight: Not all inputs are equally informative at all times.
        During stable periods, we suppress noise.
        During changes, we amplify signals.
        
        Args:
            inputs: [chemical, visual, environmental] scores
            dt: Time delta since last update
        
        Returns:
            Gated inputs
        """
        # Compute input variance (are things changing?)
        if len(self.history_buffer) > 0:
            # Convert deque to list for slicing
            buffer_list = list(self.history_buffer)
            recent_inputs = np.array([h['inputs'] for h in buffer_list[-10:]])
            input_variance = np.var(recent_inputs, axis=0)
        else:
            input_variance = np.ones(3)
        
        # High variance → open gate (things are changing, pay attention)
        # Low variance → close gate (stable, ignore noise)
        gate = 1.0 / (1.0 + np.exp(-5 * (input_variance - 0.1)))
        
        # Apply selection
        selected = inputs * gate * self.selection_weights
        
        return selected
    
    def _state_transition(self, h_prev: np.ndarray, u: np.ndarray, dt: float) -> np.ndarray:
        """
        State update: h(t) = A * h(t-1) + B * u(t)
        
        This is the core recurrence relation.
        
        Args:
            h_prev: Previous hidden state
            u: Selected input
            dt: Time delta
        
        Returns:
            New hidden state
        """
        # Discretize continuous-time dynamics
        # h(t) = exp(A * dt) * h(t-1) + B * u(t)
        A_discrete = np.eye(self.state_dim) + self.A * dt
        
        h_new = A_discrete @ h_prev + self.B @ u
        
        # Normalize to prevent explosion
        h_new = np.tanh(h_new)
        
        return h_new
    
    def _compute_trends(self, inputs: np.ndarray) -> Tuple[float, float, float]:
        """
        Compute trend indicators (rising/falling)
        
        Uses exponential moving average to track direction.
        
        Args:
            inputs: [chemical, visual, environmental]
        
        Returns:
            (chemical_trend, visual_trend, environmental_trend)
        """
        alpha = 0.1  # Smoothing factor
        
        if len(self.history_buffer) > 0:
            prev_inputs = self.history_buffer[-1]['inputs']
            
            # Compute delta
            delta = inputs - prev_inputs
            
            # Smooth with EMA
            prev_trends = [
                self.state.chemical_trend,
                self.state.visual_trend,
                self.state.environmental_trend
            ]
            
            trends = [
                alpha * delta[i] + (1 - alpha) * prev_trends[i]
                for i in range(3)
            ]
        else:
            trends = [0.0, 0.0, 0.0]
        
        return tuple(trends)
    
    def _compute_persistence(self, inputs: np.ndarray) -> Tuple[float, float]:
        """
        Compute persistence indicators (how long has signal been elevated?)
        
        Persistence = 1.0 means signal has been high for a long time
        Persistence = 0.0 means signal just started or is low
        
        Args:
            inputs: [chemical, visual, environmental]
        
        Returns:
            (chemical_persistence, visual_persistence)
        """
        threshold = 0.5  # Signal considered "elevated" above this
        decay = 0.95  # Decay rate for persistence
        
        # Chemical persistence
        if inputs[0] > threshold:
            chem_persist = min(1.0, self.state.chemical_persistence + 0.05)
        else:
            chem_persist = self.state.chemical_persistence * decay
        
        # Visual persistence
        if inputs[1] > threshold:
            vis_persist = min(1.0, self.state.visual_persistence + 0.05)
        else:
            vis_persist = self.state.visual_persistence * decay
        
        return chem_persist, vis_persist
    
    def _compute_cross_modal_lag(self) -> float:
        """
        Detect cross-sensor lag patterns
        
        Key insight: Chemical sensors often detect fire BEFORE visual sensors.
        This computes the typical lag between chemical spike and visual spike.
        
        Returns:
            Estimated lag in seconds (positive = chemical leads)
        """
        if len(self.history_buffer) < 20:
            return 0.0
        
        # Extract recent chemical and visual trends
        chemical_values = []
        visual_values = []
        
        for entry in self.history_buffer:
            chemical_values.append(entry['inputs'][0])
            visual_values.append(entry['inputs'][1])
        
        chemical_values = np.array(chemical_values)
        visual_values = np.array(visual_values)
        
        # Find peaks/spikes
        chemical_threshold = np.mean(chemical_values) + np.std(chemical_values)
        visual_threshold = np.mean(visual_values) + np.std(visual_values)
        
        chemical_spike_times = []
        visual_spike_times = []
        
        for i, entry in enumerate(self.history_buffer):
            if chemical_values[i] > chemical_threshold:
                chemical_spike_times.append(i)
            if visual_values[i] > visual_threshold:
                visual_spike_times.append(i)
        
        # Compute typical lag
        if len(chemical_spike_times) > 0 and len(visual_spike_times) > 0:
            first_chemical_spike = min(chemical_spike_times)
            first_visual_spike = min(visual_spike_times)
            
            # Positive lag = chemical leads
            lag = first_visual_spike - first_chemical_spike
            return float(lag)
        
        return 0.0
    
    def _compute_temporal_confidence(self, h: np.ndarray) -> float:
        """
        Compute confidence in temporal analysis
        
        Higher confidence when:
        - More history available
        - State is stable (not chaotic)
        - Patterns are clear
        
        Args:
            h: Current hidden state
        
        Returns:
            Confidence score (0.0-1.0)
        """
        # History factor (more data = more confidence)
        history_factor = min(1.0, len(self.history_buffer) / 30.0)
        
        # State stability (lower variance = more confidence)
        if len(self.history_buffer) > 5:
            # Convert deque to list for slicing
            buffer_list = list(self.history_buffer)
            recent_states = [entry['state'] for entry in buffer_list[-5:]]
            state_variance = np.var(recent_states)
            stability_factor = 1.0 / (1.0 + state_variance)
        else:
            stability_factor = 0.5
        
        # Pattern clarity (strong trends = more confidence)
        trend_magnitude = abs(self.state.chemical_trend) + abs(self.state.visual_trend)
        clarity_factor = min(1.0, trend_magnitude)
        
        # Combine factors
        confidence = 0.4 * history_factor + 0.4 * stability_factor + 0.2 * clarity_factor
        
        return confidence
    
    def update(self, 
               chemical_score: float, 
               visual_score: float, 
               environmental_score: float,
               timestamp: datetime) -> TemporalState:
        """
        Update state with new sensor readings
        
        This is the main entry point for the SSM.
        
        Args:
            chemical_score: Chemical modality score (0.0-1.0)
            visual_score: Visual modality score (0.0-1.0)
            environmental_score: Environmental score (0.0-1.0)
            timestamp: Current timestamp
        
        Returns:
            Updated temporal state
        """
        # Prepare input vector
        inputs = np.array([chemical_score, visual_score, environmental_score])
        
        # Compute time delta
        if self.state.timestamp is not None:
            dt = (timestamp - self.state.timestamp).total_seconds()
            dt = max(0.1, min(dt, 10.0))  # Clamp to reasonable range
        else:
            dt = 1.0  # Default 1 second
        
        # Selection mechanism (gate inputs based on informativeness)
        u = self._selection_mechanism(inputs, dt)
        
        # State transition (core recurrence)
        h_new = self._state_transition(self.state.h, u, dt)
        
        # Compute derived quantities
        trends = self._compute_trends(inputs)
        persistence = self._compute_persistence(inputs)
        lag = self._compute_cross_modal_lag()
        confidence = self._compute_temporal_confidence(h_new)
        
        # Create new state
        new_state = TemporalState(
            h=h_new,
            chemical_trend=trends[0],
            visual_trend=trends[1],
            environmental_trend=trends[2],
            chemical_persistence=persistence[0],
            visual_persistence=persistence[1],
            cross_modal_lag=lag,
            temporal_confidence=confidence,
            timestamp=timestamp
        )
        
        # Store in history
        self.history_buffer.append({
            'timestamp': timestamp,
            'inputs': inputs,
            'state': h_new.copy(),
            'chemical_trend': trends[0],
            'visual_trend': trends[1],
            'environmental_trend': trends[2]
        })
        
        # Update internal state
        self.state = new_state
        self.update_count += 1
        
        return new_state
    
    def get_perceptual_score(self) -> Dict:
        """
        Get current perceptual score (what Phase-0 outputs)
        
        This is NOT a binary fire/no-fire decision.
        It's a rich perceptual state with uncertainty.
        
        Returns:
            Perceptual state dict
        """
        # Base score from hidden state
        # Ensure result is scalar
        base_score_raw = self.C @ self.state.h
        if isinstance(base_score_raw, np.ndarray):
            base_score = float(base_score_raw.item())
        else:
            base_score = float(base_score_raw)
        base_score = (np.tanh(base_score) + 1.0) / 2.0  # Normalize to [0, 1]
        
        # Trend adjustment (rising trends increase score)
        trend_boost = 0.0
        if self.state.chemical_trend > 0.1:
            trend_boost += 0.1
        if self.state.visual_trend > 0.1:
            trend_boost += 0.05
        
        # Persistence adjustment (sustained signals increase score)
        persistence_boost = (
            self.state.chemical_persistence * 0.1 +
            self.state.visual_persistence * 0.05
        )
        
        # Cross-modal lag adjustment
        # If chemical leads vision by 10-30 seconds, this is fire pattern
        lag_boost = 0.0
        if 10 < self.state.cross_modal_lag < 30:
            lag_boost = 0.15  # Strong fire signature
        
        # Final fused score
        fused_score = base_score + trend_boost + persistence_boost + lag_boost
        fused_score = min(1.0, max(0.0, fused_score))  # Clamp
        
        # Determine trend direction
        avg_trend = (
            self.state.chemical_trend * 0.5 +
            self.state.visual_trend * 0.3 +
            self.state.environmental_trend * 0.2
        )
        
        if avg_trend > 0.05:
            trend = "rising"
        elif avg_trend < -0.05:
            trend = "falling"
        else:
            trend = "stable"
        
        # Modality agreement
        # High agreement when all trends point same direction
        trend_agreement = 1.0 - np.std([
            self.state.chemical_trend,
            self.state.visual_trend,
            self.state.environmental_trend
        ])
        
        return {
            'fused_score': fused_score,
            'trend': trend,
            'confidence': self.state.temporal_confidence,
            'modality_agreement': max(0.0, min(1.0, trend_agreement)),
            'chemical_trend': self.state.chemical_trend,
            'visual_trend': self.state.visual_trend,
            'persistence': max(self.state.chemical_persistence, 
                              self.state.visual_persistence),
            'cross_modal_lag': self.state.cross_modal_lag,
            'temporal_features': {
                'base_score': base_score,
                'trend_boost': trend_boost,
                'persistence_boost': persistence_boost,
                'lag_boost': lag_boost
            }
        }
    
    def reset(self):
        """Reset temporal state (e.g., after alert cleared)"""
        self.state = TemporalState()
        self.history_buffer.clear()
        self.update_count = 0
    
    def get_statistics(self) -> Dict:
        """Get SSM statistics"""
        return {
            'updates': self.update_count,
            'history_length': len(self.history_buffer),
            'state_norm': float(np.linalg.norm(self.state.h)),
            'temporal_confidence': self.state.temporal_confidence,
            'cross_modal_lag': self.state.cross_modal_lag
        }
