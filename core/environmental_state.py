"""
ENVIRONMENTAL STATE - Unified Perceptual Vector
The output of Phase-0 sensor fusion
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class EnvironmentalState:
    """
    Unified perceptual vector representing the current environmental state.
    
    This is the output of Phase-0 multi-modal sensor fusion.
    It combines chemical, visual, and environmental data into a coherent state
    that downstream decision-making can reason over.
    
    Philosophy:
    - Truth emerges from agreement across modalities
    - No single sensor tells the truth
    - Weighted by physical reliability (chemical > visual > environmental)
    """
    
    timestamp: datetime
    
    # =========================================================================
    # MODALITY 1: CHEMICAL STATE (Weight: 50%)
    # Primary early-warning system - detects pre-combustion signatures
    # =========================================================================
    chemical_state: Dict[str, float] = field(default_factory=dict)
    """
    Chemical perception from gas sensors (BME688)
    
    Expected keys:
    - 'voc_level': Volatile Organic Compounds (0.0-1.0)
    - 'terpene_level': Heat-stressed plant emissions (0.0-1.0) 
    - 'combustion_byproducts': Active fire gases (0.0-1.0)
    - 'organic_emissions': Baseline environmental gases (0.0-1.0)
    
    Why 50% weight:
    - Chemicals appear BEFORE visible smoke
    - Hard to spoof accidentally
    - Works in darkness, fog, occlusion
    - Highest semantic value for fire detection
    """
    
    # =========================================================================
    # MODALITY 2: VISUAL STATE (Weight: 30%)
    # Contextual confirmation - validates chemical signals
    # =========================================================================
    visual_state: Dict[str, float] = field(default_factory=dict)
    """
    Visual perception from camera (ESP32-CAM)
    
    Expected keys:
    - 'smoke_presence': Smoke density detected (0.0-1.0)
    - 'color_shift': Gray haze vs clear air (0.0-1.0)
    - 'brightness_anomaly': Fire glow detection (0.0-1.0)
    - 'spatial_diffusion': Smoke spread pattern (0.0-1.0)
    
    Why 30% weight:
    - Fragile: lighting dependent, occlusion prone
    - Adds semantic confirmation ("Is this smoke or just chemicals?")
    - Contextual validation, not first detection
    """
    
    # =========================================================================
    # MODALITY 3: ENVIRONMENTAL CONTEXT (Weight: 20%)
    # Conditioning layer - modulates interpretation
    # =========================================================================
    environmental_context: Dict[str, float] = field(default_factory=dict)
    """
    Environmental conditioning from soil/environmental sensors
    
    Expected keys:
    - 'soil_dryness': Dryness index (0.0=wet, 1.0=bone dry)
    - 'ignition_susceptibility': Likelihood of ignition (0.0-1.0)
    - 'latent_risk': Underlying danger level (0.0-1.0)
    
    Why 20% weight (lowest):
    - Slow-changing signal (days/weeks, not seconds)
    - Not an event detector
    - But critical for context: same chemical reading means different things
      in wet vs dry conditions
    """
    
    # =========================================================================
    # META-INFORMATION: Cross-Modal Analysis
    # =========================================================================
    cross_modal_agreement: float = 0.0
    """
    How well the three modalities agree (0.0-1.0)
    
    High agreement (>0.8):
    - Chemical: "FIRE"
    - Visual: "SMOKE DETECTED"
    - Environmental: "DRY CONDITIONS"
    → All sensors vote the same way → High confidence
    
    Low agreement (<0.4):
    - Chemical: "FIRE"
    - Visual: "NO SMOKE"
    - Environmental: "WET CONDITIONS"
    → Sensors disagree → Likely false alarm or sensor failure
    """
    
    overall_confidence: float = 0.0
    """
    Weighted confidence from Phase-1 reliability scores (0.0-1.0)
    
    Accounts for:
    - How many sensors are working
    - How trustworthy each sensor is (from Phase-1)
    - Whether any sensors are imputed
    
    <0.5: Insufficient trusted data, do not make decisions
    0.5-0.7: Moderate confidence
    >0.7: High confidence
    """
    
    disagreement_flags: List[str] = field(default_factory=list)
    """
    Specific disagreements detected between modalities
    
    Examples:
    - "chemical_high_visual_low": Chemicals detect fire but camera sees nothing
    - "visual_high_environmental_safe": Camera sees smoke but soil is wet
    - "all_modalities_conflict": Complete disagreement across all three
    
    Used for:
    - Debugging sensor issues
    - Identifying edge cases
    - Logging anomalies for later analysis
    """
    
    # =========================================================================
    # FIRE RISK ASSESSMENT: Final Decision Variables
    # =========================================================================
    fire_risk_score: float = 0.0
    """
    Unified fire risk score (0.0-1.0)
    
    Computed via weighted voting:
    risk = (chemical * 0.5) + (visual * 0.3) + (environmental * 0.2)
    risk *= cross_modal_agreement  # Penalize disagreement
    
    Interpretation:
    0.0-0.3: Safe (green)
    0.3-0.5: Elevated (yellow)
    0.5-0.7: High (orange)
    0.7-1.0: Critical (red)
    """
    
    fire_detected: bool = False
    """
    Binary fire detection decision
    
    Decision rules:
    1. fire_risk_score > 0.85 → FIRE (high confidence in any modality)
    2. fire_risk_score > 0.7 AND cross_modal_agreement > 0.6 → FIRE
    3. overall_confidence < 0.5 → NO DECISION (insufficient data)
    4. Otherwise → NO FIRE
    """
    
    # =========================================================================
    # AUXILIARY DATA: For Debugging and Logging
    # =========================================================================
    raw_sensor_count: int = 0
    """Total number of sensors that provided data"""
    
    valid_sensor_count: int = 0
    """Number of sensors that passed Phase-1 validation"""
    
    imputed_sensor_count: int = 0
    """Number of sensors whose data was reconstructed by Phase-1"""
    
    phase1_trauma_level: float = 0.0
    """Current trauma level from Phase-1 (0.0-1.0)"""
    
    processing_time_ms: float = 0.0
    """Time taken for fusion processing (milliseconds)"""
    
    # =========================================================================
    # METHODS: Utility Functions
    # =========================================================================
    
    def get_risk_level(self) -> str:
        """
        Get human-readable risk level
        
        Returns:
            "SAFE", "ELEVATED", "HIGH", or "CRITICAL"
        """
        if self.fire_risk_score < 0.3:
            return "SAFE"
        elif self.fire_risk_score < 0.5:
            return "ELEVATED"
        elif self.fire_risk_score < 0.7:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def get_confidence_level(self) -> str:
        """
        Get human-readable confidence level
        
        Returns:
            "LOW", "MODERATE", or "HIGH"
        """
        if self.overall_confidence < 0.5:
            return "LOW"
        elif self.overall_confidence < 0.7:
            return "MODERATE"
        else:
            return "HIGH"
    
    def should_alert(self) -> bool:
        """
        Determine if an alert should be triggered
        
        Criteria:
        - Fire detected
        - AND confidence is at least moderate
        - AND not too many disagreements
        
        Returns:
            True if alert should be sent, False otherwise
        """
        if not self.fire_detected:
            return False
        
        if self.overall_confidence < 0.5:
            return False  # Not confident enough
        
        if len(self.disagreement_flags) >= 2:
            return False  # Too much disagreement, likely false alarm
        
        return True
    
    def to_dict(self) -> Dict:
        """
        Convert to dictionary for logging/transmission
        
        Returns:
            Dict representation of environmental state
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'chemical_state': self.chemical_state,
            'visual_state': self.visual_state,
            'environmental_context': self.environmental_context,
            'cross_modal_agreement': self.cross_modal_agreement,
            'overall_confidence': self.overall_confidence,
            'disagreement_flags': self.disagreement_flags,
            'fire_risk_score': self.fire_risk_score,
            'fire_detected': self.fire_detected,
            'risk_level': self.get_risk_level(),
            'confidence_level': self.get_confidence_level(),
            'should_alert': self.should_alert(),
            'raw_sensor_count': self.raw_sensor_count,
            'valid_sensor_count': self.valid_sensor_count,
            'imputed_sensor_count': self.imputed_sensor_count,
            'phase1_trauma_level': self.phase1_trauma_level,
            'processing_time_ms': self.processing_time_ms
        }
    
    def __str__(self) -> str:
        """
        Human-readable string representation
        """
        return (
            f"EnvironmentalState("
            f"risk={self.get_risk_level()} {self.fire_risk_score:.0%}, "
            f"agreement={self.cross_modal_agreement:.0%}, "
            f"confidence={self.get_confidence_level()} {self.overall_confidence:.0%}, "
            f"fire={'YES' if self.fire_detected else 'NO'})"
        )
