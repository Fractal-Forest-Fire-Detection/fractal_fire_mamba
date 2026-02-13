"""
PHASE-0 FUSION ENGINE WITH MAMBA SSM
Temporal-aware multi-modal sensor fusion

Changes from original Phase-0:
- BEFORE: Snapshot-based fusion (processes each reading independently)
- AFTER: Streaming temporal fusion (understands patterns over time)

Integration:
1. Chemical/Visual/Environmental processors compute modality scores
2. Mamba SSM processes scores temporally
3. Output is perceptual state with temporal reasoning
"""

import numpy as np
from datetime import datetime
from typing import Dict
import time

from core.environmental_state import EnvironmentalState
from processors.chemical_processor import ChemicalProcessor
from processors.visual_processor import VisualProcessor
from processors.environmental_processor import EnvironmentalContextProcessor

# Try loading Hugging Face Mamba first (Phase-0 Advanced)
try:
    from core.temporal_mamba_hf import MambaSSM_HF
    HF_MAMBA_AVAILABLE = True
except ImportError:
    HF_MAMBA_AVAILABLE = False

# Fallback to Lightweight Mamba (Phase-0 Standard)
try:
    from core.temporal_mamba_ssm_clean import MambaSSM
except ImportError:
    from core.temporal_mamba_ssm import MambaSSM


class Phase0FusionEngineWithMamba:
    """
    Phase-0 Fusion Engine with Mamba SSM temporal coherence
    
    Architecture:
    Sensors → Processors → Modality Scores → Mamba SSM → Perceptual State
    """
    
    def __init__(self):
        """Initialize fusion engine with Mamba SSM"""
        # Modality processors
        self.chemical_processor = ChemicalProcessor()
        self.visual_processor = VisualProcessor()
        self.environmental_processor = EnvironmentalContextProcessor()
        
        # Initialize Mamba (Try HF first, then Standard)
        self.mamba_ssm = None
        self.backend_type = "Standard"
        
        if HF_MAMBA_AVAILABLE:
            try:
                print("🚀 Attempting to load Hugging Face Mamba-130m...")
                self.mamba_ssm = MambaSSM_HF()
                self.backend_type = "HuggingFace"
                print("✅ HF Mamba-130m Active (Neural Adapter Loaded)")
            except Exception as e:
                print(f"⚠️  HF Mamba load failed ({e}), falling back to Standard SSM.")
                
        if self.mamba_ssm is None:
            self.mamba_ssm = MambaSSM(state_dim=8, learning_rate=0.01)
            self.backend_type = "Standard (Lightweight)"
        
        # Statistics
        self.fusion_count = 0
        self.total_processing_time = 0.0
    
    def fuse(self, 
             validated_sensors: Dict,
             phase1_stats: Dict = None) -> EnvironmentalState:
        """
        Fuse validated sensor data with temporal reasoning
        
        Args:
            validated_sensors: Dict of validated sensor readings from Phase-1
            phase1_stats: Statistics from Phase-1 watchdog
        
        Returns:
            EnvironmentalState with temporal analysis
        """
        start_time = time.time()
        timestamp = datetime.now()
        
        # =====================================================================
        # STEP 1: Compute modality scores (same as original Phase-0)
        # =====================================================================
        
        # Process chemical sensors
        chemical_state = self.chemical_processor.process(validated_sensors)
        chemical_score = self._compute_chemical_score(chemical_state)
        
        # Process visual sensors
        visual_state = self.visual_processor.process(validated_sensors)
        visual_score = self._compute_visual_score(visual_state)
        
        # Process environmental sensors
        environmental_context = self.environmental_processor.process(validated_sensors)
        environmental_score = self._compute_environmental_score(environmental_context)
        
        # =====================================================================
        # STEP 2: UPDATE MAMBA SSM WITH TEMPORAL ANALYSIS (NEW!)
        # =====================================================================
        
        # Feed scores into Mamba SSM
        temporal_state = self.mamba_ssm.update(
            chemical_score=chemical_score,
            visual_score=visual_score,
            environmental_score=environmental_score,
            timestamp=timestamp
        )
        
        # Get perceptual state from Mamba
        perceptual = self.mamba_ssm.get_perceptual_score()
        
        # =====================================================================
        # STEP 3: COMPUTE FIRE RISK WITH TEMPORAL REASONING (ENHANCED)
        # =====================================================================
        
        # Base fire risk from perceptual fused score
        fire_risk_base = perceptual['fused_score']
        
        # Temporal adjustments
        trend_multiplier = 1.0
        if perceptual['trend'] == 'rising':
            trend_multiplier = 1.2  # Amplify risk if trending up
        elif perceptual['trend'] == 'falling':
            trend_multiplier = 0.8  # Reduce risk if trending down
        
        # Persistence multiplier
        persistence_multiplier = 1.0 + (perceptual['persistence'] * 0.3)
        
        # Cross-modal lag multiplier (classic fire signature)
        lag_multiplier = 1.0
        if 10 < perceptual['cross_modal_lag'] < 30:
            lag_multiplier = 1.3  # Chemical leads vision = fire signature
        
        # Final fire risk with temporal reasoning
        fire_risk_score = fire_risk_base * trend_multiplier * persistence_multiplier * lag_multiplier
        fire_risk_score = min(1.0, fire_risk_score)  # Clamp to [0, 1]
        
        # =====================================================================
        # STEP 4: CROSS-MODAL AGREEMENT (ENHANCED WITH TEMPORAL)
        # =====================================================================
        
        # Snapshot agreement (as before)
        modality_scores = [chemical_score, visual_score, environmental_score]
        snapshot_variance = np.var(modality_scores)
        snapshot_agreement = 1.0 - min(snapshot_variance / 0.25, 1.0)
        
        # Temporal agreement (from Mamba)
        temporal_agreement = perceptual['modality_agreement']
        
        # Combined agreement (weighted)
        cross_modal_agreement = 0.6 * snapshot_agreement + 0.4 * temporal_agreement
        
        # =====================================================================
        # STEP 5: OVERALL CONFIDENCE (ENHANCED WITH TEMPORAL)
        # =====================================================================
        
        # Base confidence from Phase-1 reliability scores
        sensor_confidences = [
            v.reliability_score for v in validated_sensors.values()
            if hasattr(v, 'reliability_score')
        ]
        
        if sensor_confidences:
            base_confidence = np.mean(sensor_confidences)
        else:
            base_confidence = 0.5
        
        # Temporal confidence from Mamba
        temporal_confidence = perceptual['confidence']
        
        # Combined confidence
        overall_confidence = 0.5 * base_confidence + 0.5 * temporal_confidence
        
        # =====================================================================
        # STEP 6: DISAGREEMENT DETECTION (ENHANCED WITH TEMPORAL)
        # =====================================================================
        
        disagreement_flags = []
        
        # Snapshot disagreements (as before)
        if chemical_score > 0.7 and visual_score < 0.3:
            disagreement_flags.append("chemical_high_visual_low")
        
        if visual_score > 0.7 and environmental_score < 0.3:
            disagreement_flags.append("visual_high_environmental_safe")
        
        # NEW: Temporal disagreements
        if perceptual['chemical_trend'] > 0.2 and perceptual['visual_trend'] < -0.1:
            disagreement_flags.append("chemical_rising_visual_falling")
        
        if perceptual['trend'] == 'rising' and fire_risk_base < 0.3:
            disagreement_flags.append("rising_trend_but_low_base_risk")
        
        # =====================================================================
        # STEP 7: FIRE DETECTION DECISION (ENHANCED WITH TEMPORAL)
        # =====================================================================
        
        fire_detected = False
        
        # Rule 1: Very high risk (emergency)
        if fire_risk_score > 0.85:
            fire_detected = True
        
        # Rule 2: High risk + good agreement
        elif fire_risk_score > 0.7 and cross_modal_agreement > 0.6:
            fire_detected = True
        
        # Rule 3: NEW - Rising trend + persistence (early warning)
        elif (perceptual['trend'] == 'rising' and 
              perceptual['persistence'] > 0.6 and
              fire_risk_score > 0.6):
            fire_detected = True
        
        # Rule 4: NEW - Classic fire signature (chemical leads visual)
        elif (perceptual['cross_modal_lag'] > 15 and
              chemical_score > 0.7 and
              visual_score > 0.5):
            fire_detected = True
        
        # =====================================================================
        # STEP 8: BUILD ENVIRONMENTAL STATE
        # =====================================================================
        
        # Count sensors
        raw_sensor_count = len(validated_sensors)
        valid_sensor_count = sum(
            1 for v in validated_sensors.values()
            if hasattr(v, 'is_valid') and v.is_valid
        )
        imputed_sensor_count = sum(
            1 for v in validated_sensors.values()
            if hasattr(v, 'is_imputed') and v.is_imputed
        )
        
        # Processing time
        processing_time_ms = (time.time() - start_time) * 1000
        self.total_processing_time += processing_time_ms
        
        # Get Phase-1 trauma if available
        phase1_trauma = phase1_stats.get('trauma_level', 0.0) if phase1_stats else 0.0
        
        # Create enhanced environmental state
        state = EnvironmentalState(
            timestamp=timestamp,
            chemical_state=chemical_state,
            visual_state=visual_state,
            environmental_context=environmental_context,
            cross_modal_agreement=cross_modal_agreement,
            overall_confidence=overall_confidence,
            disagreement_flags=disagreement_flags,
            fire_risk_score=fire_risk_score,
            fire_detected=fire_detected,
            raw_sensor_count=raw_sensor_count,
            valid_sensor_count=valid_sensor_count,
            imputed_sensor_count=imputed_sensor_count,
            phase1_trauma_level=phase1_trauma,
            processing_time_ms=processing_time_ms
        )
        
        # Add temporal metadata (NEW!)
        state.temporal_metadata = {
            'fused_score': perceptual['fused_score'],
            'trend': perceptual['trend'],
            'temporal_confidence': perceptual['confidence'],
            'chemical_trend': perceptual['chemical_trend'],
            'visual_trend': perceptual['visual_trend'],
            'persistence': perceptual['persistence'],
            'cross_modal_lag': perceptual['cross_modal_lag'],
            'temporal_features': perceptual['temporal_features']
        }
        
        self.fusion_count += 1
        
        return state
    
    def _compute_chemical_score(self, chemical_state: Dict) -> float:
        """
        Compute unified chemical risk score (0.0-1.0)
        
        Weighted combination of chemical features
        """
        voc = chemical_state.get('voc_level', 0.0)
        terpene = chemical_state.get('terpene_level', 0.0)
        combustion = chemical_state.get('combustion_byproducts', 0.0)
        
        # Weighted average
        score = 0.4 * voc + 0.3 * terpene + 0.3 * combustion
        
        # Rapid change boost
        if chemical_state.get('rapid_change_detected', False):
            score *= 1.2
        
        return min(1.0, score)
    
    def _compute_visual_score(self, visual_state: Dict) -> float:
        """
        Compute unified visual risk score (0.0-1.0)
        """
        smoke = visual_state.get('smoke_presence', 0.0)
        color_shift = visual_state.get('color_shift', 0.0)
        brightness = visual_state.get('brightness_anomaly', 0.0)
        
        # Weighted average
        score = 0.5 * smoke + 0.3 * color_shift + 0.2 * brightness
        
        return score
    
    def _compute_environmental_score(self, env_context: Dict) -> float:
        """
        Compute unified environmental risk score (0.0-1.0)
        """
        dryness = env_context.get('soil_dryness', 0.0)
        susceptibility = env_context.get('ignition_susceptibility', 0.0)
        latent_risk = env_context.get('latent_risk', 0.0)
        
        # Weighted average
        score = 0.4 * dryness + 0.4 * susceptibility + 0.2 * latent_risk
        
        # Drought boost
        if env_context.get('drought_detected', False):
            score *= 1.3
        
        return min(1.0, score)
    
    def get_statistics(self) -> Dict:
        """Get fusion engine statistics"""
        avg_time = (
            self.total_processing_time / self.fusion_count
            if self.fusion_count > 0 else 0.0
        )
        
        return {
            'fusions_processed': self.fusion_count,
            'avg_processing_time_ms': avg_time,
            **self.mamba_ssm.get_statistics()
        }
    
    def print_statistics(self):
        """Print formatted statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*70)
        print("📊 PHASE-0 FUSION ENGINE (WITH MAMBA SSM) STATISTICS")
        print("="*70)
        print(f"Total fusions: {stats['fusions_processed']}")
        print(f"Avg processing time: {stats['avg_processing_time_ms']:.2f} ms")
        print(f"\nMamba SSM:")
        print(f"  Updates: {stats['updates']}")
        print(f"  History length: {stats['history_length']}")
        print(f"  Temporal confidence: {stats['temporal_confidence']:.2%}")
        print(f"  Cross-modal lag: {stats['cross_modal_lag']:.1f} seconds")
        print("="*70)
