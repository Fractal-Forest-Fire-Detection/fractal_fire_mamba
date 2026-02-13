"""
PHASE-0 FUSION ENGINE - Multi-Modal Sensor Fusion
Core intelligence that combines chemical, visual, and environmental data

This is the heart of Phase-0: weighted voting, disagreement detection,
and unified fire risk assessment.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime
import time
import numpy as np

from core.environmental_state import EnvironmentalState
from processors.chemical_processor import ChemicalProcessor
from processors.visual_processor import VisualProcessor
from processors.environmental_processor import EnvironmentalContextProcessor


class Phase0FusionEngine:
    """
    Multi-modal sensor fusion engine.
    
    Core Philosophy:
    - No single sensor tells the truth
    - Truth emerges from agreement across modalities
    - Weighted by physical reliability (chemical > visual > environmental)
    - Temporal coherence matters (not just snapshots)
    
    Pipeline:
    1. Process each modality independently
    2. Compute cross-modal agreement
    3. Detect disagreements
    4. Weighted voting for fire risk
    5. Binary decision with confidence thresholds
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize fusion engine with all processors
        
        Args:
            config: Optional configuration dict
        """
        self.config = config or self._default_config()
        
        # Initialize processors
        self.chemical_processor = ChemicalProcessor(
            config=self.config.get('chemical_config')
        )
        self.visual_processor = VisualProcessor(
            config=self.config.get('visual_config')
        )
        self.environmental_processor = EnvironmentalContextProcessor(
            config=self.config.get('environmental_config')
        )
        
        # Modality weights (as per architecture)
        self.weights = {
            'chemical': 0.50,      # Primary early warning
            'visual': 0.30,        # Contextual confirmation
            'environmental': 0.20  # Conditioning layer
        }
        
        # Decision thresholds
        self.fire_risk_threshold_high = 0.85  # Definite fire
        self.fire_risk_threshold_medium = 0.70  # Fire with agreement
        self.agreement_threshold = 0.6  # Minimum agreement for medium threshold
        self.confidence_threshold = 0.5  # Minimum confidence for decision
        
        # State tracking
        self.last_state: Optional[EnvironmentalState] = None
        self.state_history: List[EnvironmentalState] = []
        self.max_history = 100
        
        # Statistics
        self.stats = {
            'total_fusions': 0,
            'fires_detected': 0,
            'false_alarms': 0,  # To be updated externally after verification
            'disagreements': 0,
            'avg_processing_time_ms': 0.0
        }
    
    def _default_config(self) -> Dict:
        """
        Default fusion configuration
        
        Returns:
            Default config dict
        """
        return {
            'chemical_config': None,      # Use processor defaults
            'visual_config': None,
            'environmental_config': None,
            
            # Fusion parameters
            'temporal_smoothing': True,   # Use temporal coherence
            'smoothing_alpha': 0.7,       # Weight for current vs history
            
            # Disagreement detection
            'disagreement_variance_threshold': 0.3,
            'enable_contextual_modulation': True,  # Let environment modulate chemical
        }
    
    # =========================================================================
    # MAIN FUSION PIPELINE
    # =========================================================================
    
    def fuse(
        self, 
        validated_sensors: Dict,
        phase1_stats: Optional[Dict] = None
    ) -> EnvironmentalState:
        """
        Main fusion pipeline - converts validated sensors to environmental state
        
        Args:
            validated_sensors: Dict of Phase-1 validated sensor readings
                Format: {sensor_id: ValidationResult}
            phase1_stats: Optional Phase-1 statistics (trauma level, etc.)
        
        Returns:
            EnvironmentalState with complete fire risk assessment
        """
        start_time = time.time()
        
        # =====================================================================
        # STEP 1: Process each modality independently
        # =====================================================================
        chemical_state = self.chemical_processor.process(validated_sensors)
        visual_state = self.visual_processor.process(validated_sensors)
        environmental_context = self.environmental_processor.process(validated_sensors)
        
        # =====================================================================
        # STEP 2: Contextual modulation (if enabled)
        # Environment conditions the interpretation of chemical signals
        # =====================================================================
        if self.config['enable_contextual_modulation']:
            chemical_state = self._apply_contextual_modulation(
                chemical_state,
                environmental_context
            )
        
        # =====================================================================
        # STEP 3: Compute cross-modal agreement
        # =====================================================================
        agreement_score = self._compute_cross_modal_agreement(
            chemical_state,
            visual_state,
            environmental_context
        )
        
        # =====================================================================
        # STEP 4: Detect disagreements
        # =====================================================================
        disagreement_flags = self._detect_disagreements(
            chemical_state,
            visual_state,
            environmental_context
        )
        
        if disagreement_flags:
            self.stats['disagreements'] += 1
        
        # =====================================================================
        # STEP 5: Compute overall confidence
        # Weighted from Phase-1 reliability scores
        # =====================================================================
        overall_confidence = self._compute_overall_confidence(validated_sensors)
        
        # =====================================================================
        # STEP 6: Compute fire risk score
        # Weighted voting across modalities
        # =====================================================================
        fire_risk_score = self._compute_fire_risk(
            chemical_state,
            visual_state,
            environmental_context,
            agreement_score
        )
        
        # =====================================================================
        # STEP 7: Apply temporal smoothing (if enabled)
        # =====================================================================
        if self.config['temporal_smoothing'] and self.last_state:
            fire_risk_score = self._apply_temporal_smoothing(
                fire_risk_score,
                self.last_state.fire_risk_score
            )
        
        # =====================================================================
        # STEP 8: Make binary fire detection decision
        # =====================================================================
        fire_detected = self._make_fire_decision(
            fire_risk_score,
            agreement_score,
            overall_confidence
        )
        
        if fire_detected:
            self.stats['fires_detected'] += 1
        
        # =====================================================================
        # STEP 9: Build environmental state
        # =====================================================================
        processing_time = (time.time() - start_time) * 1000  # milliseconds
        
        state = EnvironmentalState(
            timestamp=datetime.now(),
            chemical_state=chemical_state,
            visual_state=visual_state,
            environmental_context=environmental_context,
            cross_modal_agreement=agreement_score,
            overall_confidence=overall_confidence,
            disagreement_flags=disagreement_flags,
            fire_risk_score=fire_risk_score,
            fire_detected=fire_detected,
            raw_sensor_count=len(validated_sensors),
            valid_sensor_count=sum(1 for r in validated_sensors.values() if r.is_valid),
            imputed_sensor_count=sum(1 for r in validated_sensors.values() if r.is_imputed),
            phase1_trauma_level=phase1_stats.get('trauma_level', 0.0) if phase1_stats else 0.0,
            processing_time_ms=processing_time
        )
        
        # =====================================================================
        # STEP 10: Update state tracking
        # =====================================================================
        self.last_state = state
        self.state_history.append(state)
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
        
        # Update statistics
        self.stats['total_fusions'] += 1
        self._update_avg_processing_time(processing_time)
        
        return state
    
    # =========================================================================
    # CROSS-MODAL AGREEMENT
    # =========================================================================
    
    def _compute_cross_modal_agreement(
        self,
        chemical: Dict,
        visual: Dict,
        environmental: Dict
    ) -> float:
        """
        Measure how well the three modalities agree on fire presence
        
        High agreement:
        - Chemical: HIGH → Visual: SMOKE → Environmental: DRY
        - All sensors vote "FIRE"
        
        Low agreement:
        - Chemical: HIGH → Visual: NOTHING → Environmental: WET
        - Sensors contradict each other
        
        Args:
            chemical: Chemical state dict
            visual: Visual state dict
            environmental: Environmental context dict
        
        Returns:
            Agreement score: 0.0 (complete disagreement) to 1.0 (perfect agreement)
        """
        # Extract fire indicators from each modality
        
        # Chemical fire indicator (average of all chemical signals)
        chem_indicators = [
            chemical.get('voc_level', 0),
            chemical.get('terpene_level', 0),
            chemical.get('combustion_byproducts', 0)
        ]
        chem_fire_score = np.mean(chem_indicators)
        
        # Visual fire indicator
        vis_indicators = [
            visual.get('smoke_presence', 0),
            visual.get('brightness_anomaly', 0)
        ]
        vis_fire_score = np.mean(vis_indicators)
        
        # Environmental fire indicator
        env_fire_score = environmental.get('ignition_susceptibility', 0)
        
        # Compute agreement as inverse of variance
        # Low variance = all agree → high agreement
        # High variance = disagree → low agreement
        
        fire_scores = [chem_fire_score, vis_fire_score, env_fire_score]
        variance = np.var(fire_scores)
        
        # Convert variance to agreement (0-1 scale)
        # Variance of 0 = agreement of 1
        # Variance of 0.25 = agreement of 0
        agreement = max(0.0, 1.0 - (variance / 0.25))
        
        return agreement
    
    # =========================================================================
    # DISAGREEMENT DETECTION
    # =========================================================================
    
    def _detect_disagreements(
        self,
        chemical: Dict,
        visual: Dict,
        environmental: Dict
    ) -> List[str]:
        """
        Detect specific disagreements between modalities
        
        This is for debugging and logging anomalous situations
        
        Args:
            chemical: Chemical state dict
            visual: Visual state dict
            environmental: Environmental context dict
        
        Returns:
            List of disagreement flags
        """
        flags = []
        
        # Extract scores
        chem_score = chemical.get('voc_level', 0) + chemical.get('combustion_byproducts', 0)
        vis_score = visual.get('smoke_presence', 0)
        env_risk = environmental.get('ignition_susceptibility', 0)
        
        # Threshold for "high" signal
        high_threshold = 0.6
        low_threshold = 0.3
        
        # Disagreement 1: Chemical HIGH but Visual LOW
        if chem_score > high_threshold and vis_score < low_threshold:
            flags.append("chemical_high_visual_low")
        
        # Disagreement 2: Visual HIGH but Chemical LOW
        if vis_score > high_threshold and chem_score < low_threshold:
            flags.append("visual_high_chemical_low")
        
        # Disagreement 3: High fire signals but Environment is SAFE (wet)
        if (chem_score > high_threshold or vis_score > high_threshold) and env_risk < 0.3:
            flags.append("fire_signals_in_safe_environment")
        
        # Disagreement 4: All three modalities completely conflict
        if len(flags) >= 2:
            flags.append("multiple_modality_conflicts")
        
        return flags
    
    # =========================================================================
    # OVERALL CONFIDENCE
    # =========================================================================
    
    def _compute_overall_confidence(self, validated_sensors: Dict) -> float:
        """
        Compute overall confidence based on Phase-1 reliability scores
        
        Factors:
        - How many sensors are working?
        - How trustworthy is each sensor?
        - Are any sensors imputed (reconstructed)?
        
        Args:
            validated_sensors: Dict of validated sensor readings
        
        Returns:
            Confidence: 0.0 (no confidence) to 1.0 (high confidence)
        """
        if not validated_sensors:
            return 0.0
        
        # Collect reliability scores from all valid sensors
        reliability_scores = []
        imputed_count = 0
        
        for sensor_id, result in validated_sensors.items():
            if result.is_valid:
                reliability_scores.append(result.reliability_score)
                
                if result.is_imputed:
                    imputed_count += 1
        
        if not reliability_scores:
            return 0.0
        
        # Average reliability
        avg_reliability = np.mean(reliability_scores)
        
        # Penalty for imputed sensors
        imputed_ratio = imputed_count / len(reliability_scores)
        imputed_penalty = imputed_ratio * 0.2  # Up to 20% penalty
        
        # Final confidence
        confidence = avg_reliability * (1.0 - imputed_penalty)
        
        return max(0.0, min(1.0, confidence))
    
    # =========================================================================
    # FIRE RISK COMPUTATION
    # =========================================================================
    
    def _compute_fire_risk(
        self,
        chemical: Dict,
        visual: Dict,
        environmental: Dict,
        agreement: float
    ) -> float:
        """
        Compute unified fire risk score via weighted voting
        
        Formula:
        risk = (chemical_risk * 0.5) + (visual_risk * 0.3) + (environmental_risk * 0.2)
        risk *= agreement_multiplier  # Penalize disagreement
        
        Args:
            chemical: Chemical state dict
            visual: Visual state dict
            environmental: Environmental context dict
            agreement: Cross-modal agreement score
        
        Returns:
            Fire risk score: 0.0 (safe) to 1.0 (critical)
        """
        # =====================================================================
        # Extract risk from each modality
        # =====================================================================
        
        # Chemical risk (average of all chemical indicators)
        chem_indicators = [
            chemical.get('voc_level', 0),
            chemical.get('terpene_level', 0),
            chemical.get('combustion_byproducts', 0)
        ]
        chem_risk = np.mean(chem_indicators)
        
        # Boost if rapid change detected
        if chemical.get('rapid_change_detected', False):
            chem_risk = min(chem_risk * 1.2, 1.0)  # 20% boost
        
        # Visual risk (smoke + brightness anomaly)
        vis_indicators = [
            visual.get('smoke_presence', 0),
            visual.get('brightness_anomaly', 0)
        ]
        vis_risk = np.mean(vis_indicators)
        
        # Environmental risk (ignition susceptibility)
        env_risk = environmental.get('ignition_susceptibility', 0)
        
        # =====================================================================
        # Weighted sum
        # =====================================================================
        base_risk = (
            chem_risk * self.weights['chemical'] +
            vis_risk * self.weights['visual'] +
            env_risk * self.weights['environmental']
        )
        
        # =====================================================================
        # Agreement multiplier
        # Low agreement reduces confidence in fire risk
        # =====================================================================
        agreement_multiplier = 0.5 + (agreement * 0.5)  # 0.5 to 1.0
        
        final_risk = base_risk * agreement_multiplier
        
        return max(0.0, min(1.0, final_risk))
    
    # =========================================================================
    # CONTEXTUAL MODULATION
    # =========================================================================
    
    def _apply_contextual_modulation(
        self,
        chemical_state: Dict,
        environmental_context: Dict
    ) -> Dict:
        """
        Let environmental context modulate chemical interpretation
        
        Same chemical reading means different things:
        - Wet soil → Discount chemical signals (likely organic decay)
        - Dry soil → Amplify chemical signals (likely fire risk)
        
        Args:
            chemical_state: Raw chemical state
            environmental_context: Environmental context
        
        Returns:
            Modulated chemical state
        """
        soil_dryness = environmental_context.get('soil_dryness', 0.5)
        
        # Modulation factor based on soil dryness
        # Wet (0.0) → 0.5x (discount)
        # Moderate (0.5) → 1.0x (no change)
        # Dry (1.0) → 1.3x (amplify)
        
        if soil_dryness < 0.3:
            # Wet conditions - discount chemical signals
            modulation_factor = 0.5 + (soil_dryness / 0.3) * 0.5  # 0.5 to 1.0
        elif soil_dryness > 0.7:
            # Dry conditions - amplify chemical signals
            modulation_factor = 1.0 + ((soil_dryness - 0.7) / 0.3) * 0.3  # 1.0 to 1.3
        else:
            # Moderate conditions - no change
            modulation_factor = 1.0
        
        # Apply modulation to all chemical indicators
        modulated = chemical_state.copy()
        
        for key in ['voc_level', 'terpene_level', 'combustion_byproducts']:
            if key in modulated:
                modulated[key] = min(modulated[key] * modulation_factor, 1.0)
        
        return modulated
    
    # =========================================================================
    # TEMPORAL SMOOTHING
    # =========================================================================
    
    def _apply_temporal_smoothing(
        self,
        current_risk: float,
        previous_risk: float
    ) -> float:
        """
        Apply temporal smoothing to reduce jitter
        
        Uses exponential moving average
        
        Args:
            current_risk: Current fire risk score
            previous_risk: Previous fire risk score
        
        Returns:
            Smoothed fire risk score
        """
        alpha = self.config['smoothing_alpha']
        
        # Exponential moving average
        smoothed = alpha * current_risk + (1 - alpha) * previous_risk
        
        return smoothed
    
    # =========================================================================
    # FIRE DECISION
    # =========================================================================
    
    def _make_fire_decision(
        self,
        fire_risk: float,
        agreement: float,
        confidence: float
    ) -> bool:
        """
        Make binary fire detection decision
        
        Decision Rules:
        1. Confidence < 0.5 → NO DECISION (insufficient data)
        2. Risk > 0.85 → FIRE (very high risk, trust it)
        3. Risk > 0.7 AND Agreement > 0.6 → FIRE (high risk + cross-modal agreement)
        4. Otherwise → NO FIRE
        
        Args:
            fire_risk: Fire risk score
            agreement: Cross-modal agreement
            confidence: Overall confidence
        
        Returns:
            True if fire detected, False otherwise
        """
        # Rule 1: Insufficient confidence
        if confidence < self.confidence_threshold:
            return False
        
        # Rule 2: Very high risk (even with low agreement)
        if fire_risk > self.fire_risk_threshold_high:
            return True
        
        # Rule 3: High risk + good agreement
        if fire_risk > self.fire_risk_threshold_medium and agreement > self.agreement_threshold:
            return True
        
        # Rule 4: Not enough evidence
        return False
    
    # =========================================================================
    # STATISTICS & UTILITIES
    # =========================================================================
    
    def _update_avg_processing_time(self, new_time_ms: float):
        """
        Update rolling average of processing time
        
        Args:
            new_time_ms: Latest processing time in milliseconds
        """
        n = self.stats['total_fusions']
        old_avg = self.stats['avg_processing_time_ms']
        
        # Running average
        new_avg = ((old_avg * (n - 1)) + new_time_ms) / n
        
        self.stats['avg_processing_time_ms'] = new_avg
    
    def get_statistics(self) -> Dict:
        """
        Get fusion engine statistics
        
        Returns:
            Dict with statistics
        """
        return {
            **self.stats,
            'state_history_length': len(self.state_history),
            'last_fire_risk': self.last_state.fire_risk_score if self.last_state else None,
            'chemical_stats': self.chemical_processor.get_statistics(),
            'visual_stats': self.visual_processor.get_statistics(),
            'environmental_stats': self.environmental_processor.get_statistics(),
        }
    
    def print_statistics(self):
        """
        Print formatted statistics
        """
        print("\n" + "="*70)
        print("📊 PHASE-0 FUSION ENGINE STATISTICS")
        print("="*70)
        
        print(f"\n🔥 FIRE DETECTION:")
        print(f"  Total fusions: {self.stats['total_fusions']}")
        print(f"  Fires detected: {self.stats['fires_detected']}")
        print(f"  Disagreements: {self.stats['disagreements']}")
        
        print(f"\n⚡ PERFORMANCE:")
        print(f"  Avg processing time: {self.stats['avg_processing_time_ms']:.2f} ms")
        
        if self.last_state:
            print(f"\n📈 LAST STATE:")
            print(f"  Fire risk: {self.last_state.get_risk_level()} ({self.last_state.fire_risk_score:.0%})")
            print(f"  Agreement: {self.last_state.cross_modal_agreement:.0%}")
            print(f"  Confidence: {self.last_state.get_confidence_level()} ({self.last_state.overall_confidence:.0%})")
        
        print("="*70)
    
    def reset_statistics(self):
        """Reset all statistics counters"""
        self.stats = {
            'total_fusions': 0,
            'fires_detected': 0,
            'false_alarms': 0,
            'disagreements': 0,
            'avg_processing_time_ms': 0.0
        }
