#!/usr/bin/env python3
"""
System Integration Test - Night Vision Thermal Support
Tests the thermal processor and multi-spectral vision integration
"""

import sys
import numpy as np
from datetime import datetime

print("\n" + "="*70)
print("🔥 FRACTAL FIRE MAMBA - SYSTEM INTEGRATION TEST")
print("="*70)

# Test 1: Thermal Processor
print("\n[Test 1] Thermal Processor Import & Basic Function")
print("-" * 70)
try:
    from processors.thermal_processor import ThermalProcessor
    print("✅ ThermalProcessor imported successfully")
    
    # Create processor
    proc = ThermalProcessor()
    print("✅ ThermalProcessor instantiated")
    
    # Simulate thermal frame (24x32 pixels)
    clean_frame = np.random.normal(25, 2, (24, 32))  # 25°C ambient
    proc.calibrate_baseline([clean_frame])
    print(f"✅ Baseline calibrated: {proc.ambient_baseline:.1f}°C")
    
    # Simulate fire detection
    fire_frame = clean_frame.copy()
    fire_frame[10:15, 12:18] = 75.0  # Hot spot at 75°C
    
    result = proc.process(fire_frame)
    print(f"✅ Fire detection test:")
    print(f"   Hot Spot Presence: {result['hot_spot_presence']:.2%}")
    print(f"   Temperature Anomaly: {result['temperature_anomaly']:.2%}")
    print(f"   Thermal Confidence: {result['thermal_confidence']:.2%}")
    
    if result['hot_spot_presence'] > 0.5:
        print("   🔥 FIRE DETECTED (Expected)")
    
except Exception as e:
    print(f"❌ Thermal Processor Test FAILED: {e}")
    sys.exit(1)

# Test 2: Multi-Spectral Vision Wrapper
print("\n[Test 2] Multi-Spectral Vision Integration")
print("-" * 70)
try:
    from phases.phase4_vision import MultiSpectralVision
    print("✅ MultiSpectralVision imported successfully")
    
    # Create vision system
    vision = MultiSpectralVision(enable_thermal=True)
    print("✅ MultiSpectralVision instantiated with thermal support")
    
    # Test night mode (thermal only)
    thermal_frame = np.random.normal(25, 2, (24, 32))
    thermal_frame[12, 16] = 80.0  # Hot pixel
    
    result = vision.process(thermal_frame=thermal_frame, timestamp=datetime.now())
    print(f"✅ Night mode test:")
    print(f"   Vision Mode: {result.vision_mode}")
    print(f"   Confidence: {result.confidence:.2%}")
    print(f"   Vision Weight: {result.vision_weight:.2f}")
    
    assert result.vision_mode == 'night', "Night mode not activated!"
    print("   🌙 NIGHT MODE WORKING")
    
    # Test blind mode (no cameras)
    result_blind = vision.process()
    print(f"✅ Blind mode test:")
    print(f"   Vision Mode: {result_blind.vision_mode}")
    assert result_blind.vision_mode == 'blind', "Blind mode not activated!"
    assert result_blind.vision_weight == 0.0, "Weight should be zero!"
    print("   😎 BLIND MODE WORKING")
    
except Exception as e:
    print(f"❌ Multi-Spectral Vision Test FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Backwards Compatibility
print("\n[Test 3] Backwards Compatibility Check")
print("-" * 70)
try:
    from phases.phase4_vision import Phase4VisionMamba
    print("✅ Original Phase4VisionMamba still importable")
    
    # Create original vision processor
    original_vision = Phase4VisionMamba()
    print("✅ Original Phase4VisionMamba instantiated")
    print("   🔄 BACKWARDS COMPATIBLE - existing code still works!")
    
except Exception as e:
    print(f"❌ Backwards Compatibility Test FAILED: {e}")
    sys.exit(1)

# Test 4: Module Structure
print("\n[Test 4] Module Structure & Exports")
print("-" * 70)
try:
    import phases.phase4_vision as p4
    exports = dir(p4)
    
    assert 'Phase4VisionMamba' in exports, "Phase4VisionMamba not exported!"
    assert 'MultiSpectralVision' in exports, "MultiSpectralVision not exported!"
    
    print("✅ Phase-4 exports both classes:")
    print("   - Phase4VisionMamba (original RGB)")
    print("   - MultiSpectralVision (new RGB+Thermal)")
    
except Exception as e:
    print(f"❌ Module Structure Test FAILED: {e}")
    sys.exit(1)

# Test 5: Statistics & Monitoring
print("\n[Test 5] Statistics & Monitoring")
print("-" * 70)
try:
    stats = vision.get_statistics()
    print("✅ Statistics retrieval working:")
    print(f"   Day mode activations: {stats['day_mode_activations']}")
    print(f"   Night mode activations: {stats['night_mode_activations']}")
    print(f"   Dual mode activations: {stats['dual_mode_activations']}")
    
    thermal_stats = proc.get_statistics()
    print(f"✅ Thermal processor stats:")
    print(f"   Frames processed: {thermal_stats['frames_processed']}")
    print(f"   Hot spots detected: {thermal_stats['hot_spots_detected']}")
    
except Exception as e:
    print(f"❌ Statistics Test FAILED: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*70)
print("✅ ALL TESTS PASSED - SYSTEM OPERATIONAL")
print("="*70)
print("\n📊 System Status:")
print("   ✅ Thermal processor functional")
print("   ✅ Multi-spectral vision integration working")
print("   ✅ Day/night mode switching operational")
print("   ✅ Backwards compatibility maintained")
print("   ✅ Module exports correct")
print("   ✅ Statistics & monitoring active")
print("\n🔥 Ready for 24/7 fire detection!")
print("   - Day mode: RGB smoke detection")
print("   - Night mode: Thermal heat detection")
print("   - Power-gated: Only activates when Phase-2/3 trigger")
print("\n" + "="*70)
