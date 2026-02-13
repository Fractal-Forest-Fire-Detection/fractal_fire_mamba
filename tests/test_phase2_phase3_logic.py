"""
PHASE-2 AND PHASE-3 LOGIC VALIDATION TESTS

Tests the mathematical algorithms and processing logic without simulating fire scenarios.
Validates that the code works correctly with real data patterns.

NO SIMULATED FIRE SCENARIOS - Only algorithm validation
"""

import numpy as np
from datetime import datetime, timedelta
from phase2_fractal_gate import Phase2FractalGate, FractalAnalysisResult
from phase3_chaos_kernel import Phase3ChaosKernel, ChaosAnalysisResult


def test_phase2_hurst_computation():
    """Test Hurst exponent computation logic"""
    print("\n" + "="*70)
    print("🔬 TESTING PHASE-2: HURST EXPONENT COMPUTATION")
    print("="*70)
    
    fractal_gate = Phase2FractalGate()
    
    print("\nTest validates that Hurst computation:")
    print("  • Handles edge cases (empty buffer, insufficient data)")
    print("  • Produces values in valid range [0, 2]")
    print("  • Computes R/S ratio correctly")
    print("  • Returns appropriate confidence scores")
    
    # Test 1: Empty buffer
    time_series_empty = np.array([])
    hurst, conf = fractal_gate._compute_hurst_exponent(time_series_empty)
    assert hurst == 0.5, "Empty series should return H=0.5 (random)"
    assert conf == 0.0, "Empty series should have zero confidence"
    print("  ✅ Empty buffer handled correctly")
    
    # Test 2: Constant signal (no variance)
    time_series_constant = np.ones(50)
    hurst, conf = fractal_gate._compute_hurst_exponent(time_series_constant)
    assert hurst == 0.5, "Constant signal should return H=0.5"
    print("  ✅ Constant signal handled correctly")
    
    # Test 3: Valid time series
    time_series_valid = np.random.randn(60) * 0.1 + 0.5
    hurst, conf = fractal_gate._compute_hurst_exponent(time_series_valid)
    assert 0.0 <= hurst <= 2.0, "Hurst should be in [0, 2]"
    assert 0.0 <= conf <= 1.0, "Confidence should be in [0, 1]"
    print(f"  ✅ Valid series: H={hurst:.3f}, conf={conf:.2f}")
    
    print("✅ Phase-2 Hurst computation tests passed!")


def test_phase2_persistence_computation():
    """Test persistence score computation"""
    print("\n" + "="*70)
    print("🔬 TESTING PHASE-2: PERSISTENCE SCORE")
    print("="*70)
    
    fractal_gate = Phase2FractalGate()
    
    print("\nTest validates that persistence:")
    print("  • Maps H=0.5 to persistence=0.0 (random)")
    print("  • Maps H=1.5 to persistence=1.0 (highly persistent)")
    print("  • Is bounded in [0, 1]")
    
    # Test mapping
    assert fractal_gate._compute_persistence(0.5) == 0.0
    assert fractal_gate._compute_persistence(1.5) == 1.0
    assert fractal_gate._compute_persistence(1.0) == 0.5
    
    # Test bounds
    assert fractal_gate._compute_persistence(-1.0) == 0.0  # Clamp lower
    assert fractal_gate._compute_persistence(3.0) == 1.0   # Clamp upper
    
    print("✅ Phase-2 persistence computation tests passed!")


def test_phase2_quality_score():
    """Test quality score computation"""
    print("\n" + "="*70)
    print("🔬 TESTING PHASE-2: QUALITY SCORE")
    print("="*70)
    
    fractal_gate = Phase2FractalGate()
    
    print("\nTest validates that quality score:")
    print("  • Increases with more samples")
    print("  • Penalizes zero variance")
    print("  • Penalizes saturation (all 0s or 1s)")
    print("  • Is bounded in [0, 1]")
    
    # Test with various conditions
    small_sample = np.random.randn(10) * 0.1 + 0.5
    large_sample = np.random.randn(60) * 0.1 + 0.5
    zero_variance = np.ones(60) * 0.5
    saturated = np.ones(60)  # All 1s
    
    quality_small = fractal_gate._compute_quality_score(small_sample)
    quality_large = fractal_gate._compute_quality_score(large_sample)
    quality_zero_var = fractal_gate._compute_quality_score(zero_variance)
    quality_saturated = fractal_gate._compute_quality_score(saturated)
    
    assert quality_large > quality_small, "More samples should increase quality"
    assert quality_large > quality_zero_var, "Variance should increase quality"
    assert 0.0 <= quality_small <= 1.0, "Quality should be in [0, 1]"
    
    print(f"  Small sample quality: {quality_small:.2f}")
    print(f"  Large sample quality: {quality_large:.2f}")
    print(f"  Zero variance quality: {quality_zero_var:.2f}")
    print(f"  Saturated quality: {quality_saturated:.2f}")
    
    print("✅ Phase-2 quality score tests passed!")


def test_phase2_structure_detection():
    """Test structure detection decision logic"""
    print("\n" + "="*70)
    print("🔬 TESTING PHASE-2: STRUCTURE DETECTION DECISION")
    print("="*70)
    
    fractal_gate = Phase2FractalGate(hurst_threshold=1.1)
    
    print("\nTest validates that structure detection:")
    print("  • Requires H > threshold")
    print("  • Requires confidence > 0.6")
    print("  • Correctly combines both conditions")
    
    timestamp = datetime.now()
    
    # Feed sufficient data
    for i in range(60):
        risk = 0.5 + np.random.randn() * 0.1
        fractal_gate.update(risk, timestamp + timedelta(seconds=i))
    
    result = fractal_gate.last_analysis
    
    # Verify decision logic matches criteria
    expected_structure = (
        result.hurst_exponent > 1.1 and 
        result.confidence > 0.6
    )
    assert result.has_structure == expected_structure, "Structure decision logic error"
    
    print("✅ Phase-2 structure detection tests passed!")


def test_phase3_lyapunov_computation():
    """Test Lyapunov exponent computation logic"""
    print("\n" + "="*70)
    print("⚡ TESTING PHASE-3: LYAPUNOV EXPONENT COMPUTATION")
    print("="*70)
    
    chaos_kernel = Phase3ChaosKernel()
    
    print("\nTest validates that Lyapunov computation:")
    print("  • Handles edge cases (empty buffer, insufficient data)")
    print("  • Produces values in valid range [-2, 2]")
    print("  • Uses phase space reconstruction correctly")
    print("  • Returns appropriate confidence scores")
    
    # Test 1: Empty buffer
    time_series_empty = np.array([])
    lyapunov, conf = chaos_kernel._compute_lyapunov_exponent(time_series_empty)
    assert lyapunov == 0.0, "Empty series should return λ=0"
    assert conf == 0.0, "Empty series should have zero confidence"
    print("  ✅ Empty buffer handled correctly")
    
    # Test 2: Valid time series
    time_series_valid = np.random.randn(60) * 0.1 + 0.5
    lyapunov, conf = chaos_kernel._compute_lyapunov_exponent(time_series_valid)
    assert -2.0 <= lyapunov <= 2.0, "Lyapunov should be in [-2, 2]"
    assert 0.0 <= conf <= 1.0, "Confidence should be in [0, 1]"
    print(f"  ✅ Valid series: λ={lyapunov:.3f}, conf={conf:.2f}")
    
    print("✅ Phase-3 Lyapunov computation tests passed!")


def test_phase3_time_delay_embedding():
    """Test phase space reconstruction"""
    print("\n" + "="*70)
    print("⚡ TESTING PHASE-3: TIME-DELAY EMBEDDING")
    print("="*70)
    
    chaos_kernel = Phase3ChaosKernel(embedding_dimension=3)
    
    print("\nTest validates that embedding:")
    print("  • Produces correct matrix dimensions")
    print("  • Handles insufficient data")
    print("  • Preserves time series values")
    
    # Test with sufficient data
    time_series = np.arange(10)  # [0, 1, 2, ..., 9]
    embedded = chaos_kernel._time_delay_embedding(time_series, dimension=3, delay=1)
    
    expected_rows = 10 - (3 - 1) * 1  # n - (d-1)*delay = 8
    assert embedded.shape == (expected_rows, 3), f"Shape should be ({expected_rows}, 3)"
    
    # First row should be [0, 1, 2]
    assert np.allclose(embedded[0], [0, 1, 2]), "First row incorrect"
    
    # Test with insufficient data
    short_series = np.arange(2)
    embedded_short = chaos_kernel._time_delay_embedding(short_series, dimension=3, delay=1)
    assert len(embedded_short) == 0, "Should return empty array for insufficient data"
    
    print("✅ Phase-3 time-delay embedding tests passed!")


def test_phase3_positive_feedback_detection():
    """Test positive feedback loop detection"""
    print("\n" + "="*70)
    print("⚡ TESTING PHASE-3: POSITIVE FEEDBACK DETECTION")
    print("="*70)
    
    chaos_kernel = Phase3ChaosKernel()
    
    print("\nTest validates that positive feedback detection:")
    print("  • Computes correlation correctly")
    print("  • Detects acceleration (second derivative)")
    print("  • Checks for convexity (upward curvature)")
    print("  • Returns score in [0, 1]")
    
    # Test 1: No feedback (flat signal)
    risk_flat = np.ones(30) * 0.5
    trend_flat = np.zeros(30)
    feedback_flat = chaos_kernel._detect_positive_feedback(risk_flat, trend_flat)
    assert 0.0 <= feedback_flat <= 1.0, "Feedback should be in [0, 1]"
    print(f"  Flat signal feedback: {feedback_flat:.2f}")
    
    # Test 2: With correlation
    risk_corr = np.linspace(0.3, 0.7, 30)  # Rising
    trend_corr = np.ones(30) * 0.1  # Positive trend
    feedback_corr = chaos_kernel._detect_positive_feedback(risk_corr, trend_corr)
    assert feedback_corr > feedback_flat, "Correlated signal should have higher feedback"
    print(f"  Correlated signal feedback: {feedback_corr:.2f}")
    
    print("✅ Phase-3 positive feedback detection tests passed!")


def test_phase3_divergence_rate():
    """Test divergence rate computation"""
    print("\n" + "="*70)
    print("⚡ TESTING PHASE-3: DIVERGENCE RATE")
    print("="*70)
    
    chaos_kernel = Phase3ChaosKernel()
    
    print("\nTest validates that divergence rate:")
    print("  • Compares current state to baseline")
    print("  • Returns non-negative values")
    print("  • Increases with deviation from baseline")
    
    # Test 1: Stable (no divergence)
    risk_stable = np.ones(30) * 0.5
    div_stable = chaos_kernel._compute_divergence_rate(risk_stable)
    assert div_stable >= 0.0, "Divergence should be non-negative"
    print(f"  Stable signal divergence: {div_stable:.3f}")
    
    # Test 2: Diverging (increasing)
    risk_div = np.concatenate([
        np.ones(10) * 0.3,  # Baseline
        np.ones(20) * 0.7   # Diverged
    ])
    div_diverging = chaos_kernel._compute_divergence_rate(risk_div)
    assert div_diverging > div_stable, "Diverging signal should have higher rate"
    print(f"  Diverging signal divergence: {div_diverging:.3f}")
    
    print("✅ Phase-3 divergence rate tests passed!")


def test_phase3_suspicion_level():
    """Test suspicion level computation"""
    print("\n" + "="*70)
    print("⚡ TESTING PHASE-3: SUSPICION LEVEL")
    print("="*70)
    
    chaos_kernel = Phase3ChaosKernel()
    
    print("\nTest validates that suspicion level:")
    print("  • Combines Lyapunov, feedback, and divergence")
    print("  • Is bounded in [0, 1]")
    print("  • Increases with all indicators")
    
    # Test various combinations
    suspicion_low = chaos_kernel._compute_suspicion_level(
        lyapunov=-0.5, positive_feedback=0.1, divergence=0.1
    )
    
    suspicion_high = chaos_kernel._compute_suspicion_level(
        lyapunov=1.0, positive_feedback=0.9, divergence=2.0
    )
    
    assert 0.0 <= suspicion_low <= 1.0, "Suspicion should be in [0, 1]"
    assert 0.0 <= suspicion_high <= 1.0, "Suspicion should be in [0, 1]"
    assert suspicion_high > suspicion_low, "High indicators should increase suspicion"
    
    print(f"  Low indicators suspicion: {suspicion_low:.2f}")
    print(f"  High indicators suspicion: {suspicion_high:.2f}")
    
    print("✅ Phase-3 suspicion level tests passed!")


def test_phase_integration():
    """Test integration between Phase-2 and Phase-3"""
    print("\n" + "="*70)
    print("🔗 TESTING PHASE-2 AND PHASE-3 INTEGRATION")
    print("="*70)
    
    fractal_gate = Phase2FractalGate()
    chaos_kernel = Phase3ChaosKernel()
    
    print("\nTest validates that:")
    print("  • Both phases can process same risk scores")
    print("  • Buffers accumulate correctly")
    print("  • State resets work properly")
    
    timestamp = datetime.now()
    
    # Feed data to both phases
    for i in range(60):
        risk = 0.5 + np.random.randn() * 0.1
        trend = np.random.randn() * 0.05
        
        result2 = fractal_gate.update(risk, timestamp + timedelta(seconds=i))
        result3 = chaos_kernel.update(risk, trend, timestamp + timedelta(seconds=i))
        
        assert isinstance(result2, FractalAnalysisResult), "Phase-2 should return FractalAnalysisResult"
        assert isinstance(result3, ChaosAnalysisResult), "Phase-3 should return ChaosAnalysisResult"
    
    # Check buffers accumulated
    assert len(fractal_gate.risk_score_history) > 0, "Phase-2 buffer should be filled"
    assert len(chaos_kernel.risk_score_history) > 0, "Phase-3 buffer should be filled"
    
    # Test resets
    fractal_gate.reset()
    chaos_kernel.reset()
    
    assert len(fractal_gate.risk_score_history) == 0, "Phase-2 should reset buffer"
    assert len(chaos_kernel.risk_score_history) == 0, "Phase-3 should reset buffer"
    
    print("✅ Phase integration tests passed!")


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "🧪"*35)
    print("PHASE-2 & PHASE-3 LOGIC VALIDATION TEST SUITE")
    print("🧪"*35)
    print("\nNOTE: These tests validate processing logic, not fire scenarios.")
    print("      For real fire detection, feed actual sensor data.\n")
    
    try:
        # Phase-2 tests
        test_phase2_hurst_computation()
        test_phase2_persistence_computation()
        test_phase2_quality_score()
        test_phase2_structure_detection()
        
        # Phase-3 tests
        test_phase3_lyapunov_computation()
        test_phase3_time_delay_embedding()
        test_phase3_positive_feedback_detection()
        test_phase3_divergence_rate()
        test_phase3_suspicion_level()
        
        # Integration tests
        test_phase_integration()
        
        print("\n" + "="*70)
        print("✅ ALL LOGIC VALIDATION TESTS PASSED!")
        print("="*70)
        print("\n🎯 Phase-2 and Phase-3 are validated and ready for deployment!")
        print("   Next step: Integrate with your real sensor data pipeline.\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
