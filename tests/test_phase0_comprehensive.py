"""
PHASE-0 COMPREHENSIVE TEST SUITE
Tests all processors and fusion engine
"""

# Fix Python path to allow imports from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import numpy as np
from datetime import datetime
from dataclasses import dataclass

# Mock Phase-1 ValidationResult for testing
@dataclass
class MockValidationResult:
    """Mock Phase-1 validation result for testing"""
    sensor_id: str
    value: float
    is_valid: bool = True
    is_imputed: bool = False
    reliability_score: float = 1.0
    failure_reason: str = ""


def test_chemical_processor():
    """Test chemical processor"""
    print("\n" + "="*70)
    print("🧪 TESTING CHEMICAL PROCESSOR")
    print("="*70)
    
    from processors.chemical_processor import ChemicalProcessor
    
    processor = ChemicalProcessor()
    
    # Test Case 1: Normal conditions
    print("\n✅ Test 1: Normal conditions")
    validated = {
        'VOC': MockValidationResult('VOC', 120.0, reliability_score=0.95),
        'CO': MockValidationResult('CO', 15.0, reliability_score=0.98),
        'SMOKE': MockValidationResult('SMOKE', 60.0, reliability_score=0.92),
    }
    
    result = processor.process(validated)
    print(f"  VOC level: {result['voc_level']:.2f}")
    print(f"  Combustion: {result['combustion_byproducts']:.2f}")
    print(f"  Confidence: {result['chemical_confidence']:.2f}")
    assert result['voc_level'] < 0.3, "Normal VOC should be low risk"
    
    # Test Case 2: Fire conditions
    print("\n🔥 Test 2: Fire conditions")
    validated = {
        'VOC': MockValidationResult('VOC', 550.0, reliability_score=0.90),
        'TERPENE': MockValidationResult('TERPENE', 320.0, reliability_score=0.88),
        'CO': MockValidationResult('CO', 110.0, reliability_score=0.85),
        'SMOKE': MockValidationResult('SMOKE', 450.0, reliability_score=0.87),
    }
    
    result = processor.process(validated)
    print(f"  VOC level: {result['voc_level']:.2f}")
    print(f"  Terpene level: {result['terpene_level']:.2f}")
    print(f"  Combustion: {result['combustion_byproducts']:.2f}")
    print(f"  Confidence: {result['chemical_confidence']:.2f}")
    assert result['voc_level'] > 0.7, "High VOC should be high risk"
    assert result['combustion_byproducts'] > 0.7, "High combustion should be detected"
    
    # Test Case 3: Rapid spike detection
    print("\n⚡ Test 3: Rapid spike detection")
    processor2 = ChemicalProcessor()
    
    # First reading - establish baseline
    validated1 = {'VOC': MockValidationResult('VOC', 100.0)}
    result1 = processor2.process(validated1)
    
    # Second reading - spike
    validated2 = {'VOC': MockValidationResult('VOC', 250.0)}
    result2 = processor2.process(validated2)
    
    print(f"  Rapid change detected: {result2.get('rapid_change_detected', False)}")
    assert result2.get('rapid_change_detected', False), "Should detect rapid spike"
    
    print("✅ Chemical processor tests passed!")


def test_visual_processor():
    """Test visual processor"""
    print("\n" + "="*70)
    print("👁️  TESTING VISUAL PROCESSOR")
    print("="*70)
    
    from processors.visual_processor import VisualProcessor
    
    processor = VisualProcessor()
    
    # Test Case 1: No camera data
    print("\n❌ Test 1: No camera data")
    validated = {}
    result = processor.process(validated)
    
    print(f"  Smoke presence: {result['smoke_presence']:.2f}")
    print(f"  Visual confidence: {result['visual_confidence']:.2f}")
    assert result['smoke_presence'] == 0.0, "No camera = no smoke detected"
    
    # Test Case 2: Clear image (simulated)
    print("\n☀️  Test 2: Clear conditions")
    clear_image = np.random.rand(120, 160, 3) * 0.7 + 0.3  # Bright, colorful
    validated = {
        'CAMERA': MockValidationResult('CAMERA', clear_image, reliability_score=0.95)
    }
    
    result = processor.process(validated)
    print(f"  Smoke presence: {result['smoke_presence']:.2f}")
    print(f"  Color shift: {result['color_shift']:.2f}")
    print(f"  Visual confidence: {result['visual_confidence']:.2f}")
    
    # Test Case 3: Smoky image (simulated)
    print("\n🌫️  Test 3: Smoky conditions")
    # Simulate smoke: low saturation, gray haze
    smoky_image = np.ones((120, 160, 3)) * 0.5  # Gray haze
    smoky_image += np.random.rand(120, 160, 3) * 0.1  # Slight noise
    
    validated = {
        'CAMERA': MockValidationResult('CAMERA', smoky_image, reliability_score=0.85)
    }
    
    # Need to set baseline first
    processor.brightness_baseline = 0.7
    processor.color_baseline = 0.3
    processor.edge_density_baseline = 0.4
    
    result = processor.process(validated)
    print(f"  Smoke presence: {result['smoke_presence']:.2f}")
    print(f"  Color shift: {result['color_shift']:.2f}")
    print(f"  Brightness anomaly: {result['brightness_anomaly']:.2f}")
    print(f"  Visual confidence: {result['visual_confidence']:.2f}")
    
    print("✅ Visual processor tests passed!")


def test_environmental_processor():
    """Test environmental processor"""
    print("\n" + "="*70)
    print("🌍 TESTING ENVIRONMENTAL PROCESSOR")
    print("="*70)
    
    from processors.environmental_processor import EnvironmentalContextProcessor
    
    processor = EnvironmentalContextProcessor()
    
    # Test Case 1: Wet conditions (safe)
    print("\n💧 Test 1: Wet conditions")
    validated = {
        'SOIL_MOISTURE': MockValidationResult('SOIL_MOISTURE', 70.0, reliability_score=0.92),
        'TEMPERATURE': MockValidationResult('TEMPERATURE', 22.0, reliability_score=0.95),
        'HUMIDITY': MockValidationResult('HUMIDITY', 65.0, reliability_score=0.90),
    }
    
    result = processor.process(validated)
    print(f"  Soil dryness: {result['soil_dryness']:.2f}")
    print(f"  Ignition susceptibility: {result['ignition_susceptibility']:.2f}")
    print(f"  Latent risk: {result['latent_risk']:.2f}")
    assert result['soil_dryness'] < 0.5, "Wet soil should have low dryness"
    assert result['ignition_susceptibility'] < 0.3, "Wet soil should have low ignition risk"
    
    # Test Case 2: Dry conditions (dangerous)
    print("\n🔥 Test 2: Dry conditions")
    validated = {
        'SOIL_MOISTURE': MockValidationResult('SOIL_MOISTURE', 15.0, reliability_score=0.88),
        'TEMPERATURE': MockValidationResult('TEMPERATURE', 38.0, reliability_score=0.90),
        'HUMIDITY': MockValidationResult('HUMIDITY', 20.0, reliability_score=0.85),
    }
    
    result = processor.process(validated)
    print(f"  Soil dryness: {result['soil_dryness']:.2f}")
    print(f"  Ignition susceptibility: {result['ignition_susceptibility']:.2f}")
    print(f"  Latent risk: {result['latent_risk']:.2f}")
    assert result['soil_dryness'] > 0.7, "Dry soil should have high dryness"
    assert result['ignition_susceptibility'] > 0.7, "Dry soil should have high ignition risk"
    
    # Test Case 3: Drought detection
    print("\n🏜️  Test 3: Drought detection")
    processor2 = EnvironmentalContextProcessor()
    
    # Simulate 7 days of dry readings
    for _ in range(7):
        validated = {'SOIL_MOISTURE': MockValidationResult('SOIL_MOISTURE', 15.0)}
        result = processor2.process(validated)
    
    print(f"  Drought detected: {result['drought_detected']}")
    assert result['drought_detected'], "Should detect drought after 7 dry days"
    
    print("✅ Environmental processor tests passed!")


def test_fusion_engine():
    """Test fusion engine"""
    print("\n" + "="*70)
    print("🔥 TESTING FUSION ENGINE")
    print("="*70)
    
    from phases.phase0_fusion.fusion_engine import Phase0FusionEngine
    
    engine = Phase0FusionEngine()
    
    # Test Case 1: All sensors agree - FIRE
    print("\n🔥 Test 1: All sensors agree - FIRE")
    validated = {
        'VOC': MockValidationResult('VOC', 550.0, reliability_score=0.92),
        'CO': MockValidationResult('CO', 110.0, reliability_score=0.90),
        'SMOKE': MockValidationResult('SMOKE', 450.0, reliability_score=0.88),
        'CAMERA': MockValidationResult('CAMERA', np.ones((120, 160, 3)) * 0.3, reliability_score=0.85),
        'SOIL_MOISTURE': MockValidationResult('SOIL_MOISTURE', 12.0, reliability_score=0.95),
        'TEMPERATURE': MockValidationResult('TEMPERATURE', 42.0, reliability_score=0.93),
    }
    
    # Set visual baselines
    engine.visual_processor.brightness_baseline = 0.7
    engine.visual_processor.edge_density_baseline = 0.5
    
    state = engine.fuse(validated)
    
    print(f"  Fire risk: {state.get_risk_level()} ({state.fire_risk_score:.0%})")
    print(f"  Agreement: {state.cross_modal_agreement:.0%}")
    print(f"  Confidence: {state.get_confidence_level()} ({state.overall_confidence:.0%})")
    print(f"  Fire detected: {state.fire_detected}")
    print(f"  Should alert: {state.should_alert()}")
    
    assert state.fire_detected, "Should detect fire with all sensors agreeing"
    assert state.cross_modal_agreement > 0.5, "Should have good agreement"
    
    # Test Case 2: Disagreement - Chemical says fire, but conditions are wet
    print("\n⚠️  Test 2: Disagreement - Chemical spike in wet conditions")
    validated = {
        'VOC': MockValidationResult('VOC', 450.0, reliability_score=0.90),
        'CO': MockValidationResult('CO', 80.0, reliability_score=0.88),
        'CAMERA': MockValidationResult('CAMERA', np.ones((120, 160, 3)) * 0.6, reliability_score=0.85),
        'SOIL_MOISTURE': MockValidationResult('SOIL_MOISTURE', 75.0, reliability_score=0.95),
        'HUMIDITY': MockValidationResult('HUMIDITY', 70.0, reliability_score=0.92),
    }
    
    state = engine.fuse(validated)
    
    print(f"  Fire risk: {state.get_risk_level()} ({state.fire_risk_score:.0%})")
    print(f"  Agreement: {state.cross_modal_agreement:.0%}")
    print(f"  Disagreements: {state.disagreement_flags}")
    print(f"  Fire detected: {state.fire_detected}")
    
    # Risk should be reduced by contextual modulation (wet conditions)
    assert len(state.disagreement_flags) > 0, "Should detect disagreement"
    
    # Test Case 3: Normal conditions
    print("\n✅ Test 3: Normal conditions - No fire")
    validated = {
        'VOC': MockValidationResult('VOC', 110.0, reliability_score=0.95),
        'CO': MockValidationResult('CO', 12.0, reliability_score=0.93),
        'CAMERA': MockValidationResult('CAMERA', np.random.rand(120, 160, 3) * 0.8, reliability_score=0.90),
        'SOIL_MOISTURE': MockValidationResult('SOIL_MOISTURE', 55.0, reliability_score=0.92),
    }
    
    state = engine.fuse(validated)
    
    print(f"  Fire risk: {state.get_risk_level()} ({state.fire_risk_score:.0%})")
    print(f"  Agreement: {state.cross_modal_agreement:.0%}")
    print(f"  Fire detected: {state.fire_detected}")
    
    assert not state.fire_detected, "Should not detect fire in normal conditions"
    assert state.get_risk_level() in ["SAFE", "ELEVATED"], "Risk should be low"
    
    print("✅ Fusion engine tests passed!")


def test_environmental_state():
    """Test environmental state dataclass"""
    print("\n" + "="*70)
    print("📊 TESTING ENVIRONMENTAL STATE")
    print("="*70)
    
    from core.environmental_state import EnvironmentalState
    
    # Create test state
    state = EnvironmentalState(
        timestamp=datetime.now(),
        chemical_state={'voc_level': 0.8, 'combustion_byproducts': 0.9},
        visual_state={'smoke_presence': 0.7},
        environmental_context={'soil_dryness': 0.85},
        cross_modal_agreement=0.75,
        overall_confidence=0.82,
        disagreement_flags=[],
        fire_risk_score=0.78,
        fire_detected=True
    )
    
    print(f"\n{state}")
    
    print(f"\nRisk level: {state.get_risk_level()}")
    print(f"Confidence level: {state.get_confidence_level()}")
    print(f"Should alert: {state.should_alert()}")
    
    assert state.get_risk_level() == "HIGH", "0.78 risk should be HIGH"
    assert state.get_confidence_level() == "HIGH", "0.82 confidence should be HIGH"
    assert state.should_alert(), "Should alert when fire detected with high confidence"
    
    # Test to_dict
    state_dict = state.to_dict()
    assert 'fire_risk_score' in state_dict
    assert 'timestamp' in state_dict
    
    print("✅ Environmental state tests passed!")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "🔥"*35)
    print("PHASE-0 COMPREHENSIVE TEST SUITE")
    print("🔥"*35)
    
    try:
        test_chemical_processor()
        test_visual_processor()
        test_environmental_processor()
        test_fusion_engine()
        test_environmental_state()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\n🎯 Phase-0 is ready for deployment!\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
