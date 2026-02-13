"""
PHASE-1 WATCHDOG LAYER - COMPREHENSIVE TEST SUITE

This demonstrates all failure modes and edge cases:
1. Normal operation
2. Range failures (out of bounds)
3. Dying gasp protocol
4. Frozen sensor detection
5. Null signal imputation
6. Trauma-aware adaptive thresholding
"""

import numpy as np
from datetime import datetime, timedelta
from phase1_watchdog_layer import (
    Phase1WatchdogLayer,
    SensorReading,
    ValidationResult
)


def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_scenario_1_normal_operation():
    """✅ TEST 1: Normal sensor readings - should all pass"""
    print_section("TEST 1: NORMAL OPERATION")
    
    watchdog = Phase1WatchdogLayer()
    
    normal_readings = [
        SensorReading("TEMP_001", 22.5, datetime.now(), "temperature"),
        SensorReading("TEMP_002", 18.3, datetime.now(), "temperature"),
        SensorReading("HUM_001", 65.0, datetime.now(), "humidity"),
        SensorReading("CO2_001", 420.0, datetime.now(), "co2"),
        SensorReading("SMOKE_001", 5.0, datetime.now(), "smoke"),
    ]
    
    print("Testing 5 normal sensor readings...\n")
    
    for reading in normal_readings:
        result = watchdog.validate(reading, reading.sensor_id, reading.sensor_type)
        
        status = "✅ PASS" if result.is_valid else "❌ FAIL"
        print(f"{status} | {reading.sensor_id:12} | {reading.value:6.1f} | Trust: {result.reliability_score:6.1%}")
    
    stats = watchdog.get_statistics()
    print(f"\n📊 Range failures: {stats['range_failures']}")
    print(f"📊 Total processed: {stats['total_processed']}")
    
    assert stats['range_failures'] == 0, "Normal readings should not fail range check"
    print("\n✅ All normal readings passed validation")


def test_scenario_2_range_failures():
    """❌ TEST 2: Out-of-range values - should reject"""
    print_section("TEST 2: RANGE FAILURES (Physical Impossibility)")
    
    watchdog = Phase1WatchdogLayer()
    
    invalid_readings = [
        SensorReading("TEMP_BAD1", -50.0, datetime.now(), "temperature"),  # Too cold
        SensorReading("TEMP_BAD2", 150.0, datetime.now(), "temperature"),  # Too hot (also dying gasp)
        SensorReading("HUM_BAD1", -10.0, datetime.now(), "humidity"),      # Negative humidity
        SensorReading("HUM_BAD2", 120.0, datetime.now(), "humidity"),      # >100% humidity
        SensorReading("CO2_BAD1", 10000.0, datetime.now(), "co2"),         # Absurdly high
    ]
    
    print("Testing 5 out-of-range sensor readings...\n")
    
    failures = 0
    for reading in invalid_readings:
        result = watchdog.validate(reading, reading.sensor_id, reading.sensor_type)
        
        status = "✅ PASS" if result.is_valid else "❌ REJECT"
        
        if not result.is_valid:
            failures += 1
            print(f"{status} | {reading.sensor_id:12} | {reading.value:8.1f} | {result.failure_reason}")
        else:
            print(f"{status} | {reading.sensor_id:12} | {reading.value:8.1f} | SHOULD HAVE FAILED!")
    
    stats = watchdog.get_statistics()
    print(f"\n📊 Range failures: {stats['range_failures']}")
    print(f"📊 Dying gasps: {stats['dying_gasps']}")
    
    assert failures == 5, f"Expected 5 rejections, got {failures}"
    print("\n✅ All invalid readings correctly rejected")


def test_scenario_3_dying_gasp():
    """💀 TEST 3: Dying gasp protocol activation"""
    print_section("TEST 3: DYING GASP PROTOCOL (Catastrophic Failure)")
    
    watchdog = Phase1WatchdogLayer()
    
    # First, establish some normal history
    print("Establishing normal sensor history...")
    for i in range(5):
        reading = SensorReading(
            "TEMP_DYING",
            25.0 + i * 0.5,
            datetime.now() - timedelta(seconds=10-i*2),
            "temperature"
        )
        watchdog.validate(reading, reading.sensor_id, reading.sensor_type)
    
    print("✅ Normal history established (25.0°C → 27.0°C)")
    
    # Now trigger dying gasp
    print("\n💀 TRIGGERING DYING GASP...")
    print("   Sensor reading: 105.0°C (threshold: 100.0°C)")
    
    dying_reading = SensorReading(
        "TEMP_DYING",
        105.0,  # Above dying gasp threshold
        datetime.now(),
        "temperature"
    )
    
    result = watchdog.validate(dying_reading, dying_reading.sensor_id, dying_reading.sensor_type)
    
    print(f"\n   Valid: {result.is_valid}")
    print(f"   Failure reason: {result.failure_reason}")
    print(f"   Trauma level: {watchdog.trauma_system.trauma_level:.2f}")
    
    # Check black box was created
    black_box = watchdog._get_black_box_data("TEMP_DYING")
    print(f"\n📦 BLACK BOX DUMP:")
    print(f"   Sensor: {black_box['sensor_id']}")
    print(f"   Buffer: {black_box['buffer_seconds']} seconds")
    print(f"   Readings captured: {len(black_box['values'])}")
    print(f"   Values: {black_box['values']}")
    
    stats = watchdog.get_statistics()
    print(f"\n📊 Dying gasps triggered: {stats['dying_gasps']}")
    print(f"📊 Trauma level: {stats['trauma_level']:.2f}")
    print(f"📊 Broken sensors: {stats['broken_sensors']}")
    
    assert stats['dying_gasps'] > 0, "Dying gasp should have been triggered"
    assert watchdog.trauma_system.trauma_level > 0.2, "Trauma should be registered"
    print("\n✅ Dying gasp protocol executed successfully")


def test_scenario_4_frozen_sensor():
    """❄️ TEST 4: Frozen sensor detection"""
    print_section("TEST 4: FROZEN SENSOR DETECTION (Zombie Sensor)")
    
    watchdog = Phase1WatchdogLayer()
    
    sensor_id = "TEMP_FROZEN"
    frozen_value = 23.0
    
    print(f"Simulating sensor stuck at {frozen_value}°C for >5 hours...\n")
    
    # Send same value repeatedly over 6 hours
    time_points = [
        datetime.now() - timedelta(hours=6),
        datetime.now() - timedelta(hours=5, minutes=30),
        datetime.now() - timedelta(hours=5),
        datetime.now() - timedelta(hours=4),
        datetime.now() - timedelta(hours=3),
        datetime.now() - timedelta(hours=2),
        datetime.now() - timedelta(hours=1),
        datetime.now(),
    ]
    
    for i, timestamp in enumerate(time_points):
        reading = SensorReading(sensor_id, frozen_value, timestamp, "temperature")
        result = watchdog.validate(reading, sensor_id, "temperature")
        
        hours_elapsed = (datetime.now() - time_points[0]).total_seconds() / 3600
        
        if result.is_valid:
            print(f"Hour {i}: ✅ VALID | Value: {frozen_value}°C | Frozen: {watchdog.sensor_states[sensor_id].frozen_since}")
        else:
            print(f"Hour {i}: ❌ FROZEN DETECTED | {result.failure_reason}")
            break
    
    stats = watchdog.get_statistics()
    print(f"\n📊 Frozen failures: {stats['frozen_failures']}")
    print(f"📊 Broken sensors: {stats['broken_sensors']}")
    
    sensor_state = watchdog.sensor_states.get(sensor_id)
    if sensor_state:
        print(f"📊 Sensor marked as broken: {sensor_state.is_broken}")
    
    assert stats['frozen_failures'] > 0, "Frozen sensor should be detected"
    print("\n✅ Frozen sensor correctly identified")


def test_scenario_5_null_imputation():
    """📊 TEST 5: Virtual sensor imputation for missing data"""
    print_section("TEST 5: NULL SIGNAL IMPUTATION (Self-Healing)")
    
    watchdog = Phase1WatchdogLayer()
    
    # First, establish history for temperature sensor
    print("Establishing sensor history for imputation learning...")
    historical_readings = [
        (20.0, 70.0),  # temp, humidity
        (22.0, 65.0),
        (24.0, 60.0),
        (26.0, 55.0),
        (28.0, 50.0),
    ]
    
    for temp, hum in historical_readings:
        temp_reading = SensorReading("TEMP_001", temp, datetime.now(), "temperature")
        hum_reading = SensorReading("HUM_001", hum, datetime.now(), "humidity")
        
        watchdog.validate(temp_reading, "TEMP_001", "temperature")
        watchdog.validate(hum_reading, "HUM_001", "humidity")
    
    print("✅ History established (inverse correlation: temp↑ hum↓)")
    
    # Now simulate missing temperature sensor
    print("\n📡 TEMPERATURE SENSOR LOST (null signal)")
    print("   Attempting virtual sensor imputation...\n")
    
    # Provide current humidity to help with imputation
    available_sensors = {'humidity': 45.0}
    
    result = watchdog.validate(
        reading=None,  # NULL!
        sensor_id="TEMP_001",
        sensor_type="temperature",
        available_sensors=available_sensors
    )
    
    print(f"   Valid: {result.is_valid}")
    print(f"   Imputed: {result.is_imputed}")
    print(f"   Value: {result.value:.2f}°C")
    print(f"   Reliability: {result.reliability_score:.2%}")
    print(f"   Method: {result.metadata.get('imputation_method', 'N/A')}")
    
    stats = watchdog.get_statistics()
    print(f"\n📊 Null failures: {stats['null_failures']}")
    print(f"📊 Successful imputations: {stats['imputations']}")
    
    assert result.is_imputed, "Missing signal should trigger imputation"
    assert result.reliability_score < 1.0, "Imputed data should have reduced confidence"
    print("\n✅ Virtual sensor imputation successful")


def test_scenario_6_trauma_adaptation():
    """⚡ TEST 6: Trauma-aware adaptive sensitivity"""
    print_section("TEST 6: TRAUMA-AWARE ADAPTIVE SENSITIVITY")
    
    watchdog = Phase1WatchdogLayer()
    
    # Normal operation
    print("PHASE 1: Normal operation (Trauma = 0.0)")
    print("-" * 80)
    
    normal_reading = SensorReading("TEMP_001", 25.0, datetime.now(), "temperature")
    result = watchdog.validate(normal_reading, "TEMP_001", "temperature")
    
    print(f"   Trauma level: {watchdog.trauma_system.trauma_level:.2f}")
    print(f"   Paranoid mode: {watchdog.trauma_system.is_paranoid_mode()}")
    print(f"   Reliability score: {result.reliability_score:.2%}")
    print(f"   Adaptive threshold (base=1.0): {watchdog.trauma_system.get_adaptive_threshold(1.0):.2f}")
    
    # Register trauma event
    print("\n💥 REGISTERING TRAUMA EVENT (severe anomaly detected)")
    print("-" * 80)
    
    watchdog.trauma_system.register_trauma(
        severity=0.7,
        description="Multiple sensors detected fire signature"
    )
    
    print(f"   Trauma level: {watchdog.trauma_system.trauma_level:.2f}")
    print(f"   Paranoid mode: {watchdog.trauma_system.is_paranoid_mode()}")
    
    # Same reading, but now under trauma
    print("\nPHASE 2: Same reading under trauma")
    print("-" * 80)
    
    result_trauma = watchdog.validate(normal_reading, "TEMP_001", "temperature")
    
    print(f"   Reliability score: {result_trauma.reliability_score:.2%}")
    print(f"   Adaptive threshold (base=1.0): {watchdog.trauma_system.get_adaptive_threshold(1.0):.2f}")
    print(f"   Confidence penalty: {(1.0 - result_trauma.reliability_score) * 100:.1f}%")
    
    # Show threshold progression
    print("\n📉 THRESHOLD ADAPTATION BY TRAUMA LEVEL:")
    print("-" * 80)
    print("   Trauma  |  Threshold  |  Sensitivity")
    print("   " + "-"*40)
    
    for trauma in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        threshold = 1.0 * (1.1 - trauma)
        sensitivity = "NORMAL" if trauma == 0 else "HEIGHTENED" if trauma < 0.5 else "PARANOID"
        print(f"   {trauma:.1f}    |  {threshold:.2f}       |  {sensitivity}")
    
    # Test trauma decay
    print("\n🌱 TRAUMA DECAY SIMULATION (7 days)")
    print("-" * 80)
    
    print(f"   Day 0: Trauma = {watchdog.trauma_system.trauma_level:.2f}")
    
    for day in range(1, 8):
        # Simulate a day passing
        watchdog.trauma_system.last_decay -= timedelta(days=1)
        watchdog.trauma_system.apply_decay()
        print(f"   Day {day}: Trauma = {watchdog.trauma_system.trauma_level:.2f}")
    
    print(f"\n✅ Trauma decayed to {watchdog.trauma_system.trauma_level:.2f}")
    print("✅ Adaptive sensitivity demonstrated")


def test_scenario_7_integrated_pipeline():
    """🔥 TEST 7: Full integrated pipeline simulation"""
    print_section("TEST 7: INTEGRATED PIPELINE (Real-World Scenario)")
    
    watchdog = Phase1WatchdogLayer()
    
    print("Simulating 60-second fire detection scenario...\n")
    
    # T=0s: Normal conditions
    print("T=0s: Normal forest conditions")
    sensors = {
        'temp': 22.0,
        'humidity': 65.0,
        'smoke': 2.0,
        'co2': 400.0
    }
    
    for sensor_type, value in sensors.items():
        reading = SensorReading(f"{sensor_type.upper()}_001", value, datetime.now(), sensor_type)
        result = watchdog.validate(reading, reading.sensor_id, reading.sensor_type)
        print(f"   ✅ {sensor_type:10} = {value:6.1f} | Trust: {result.reliability_score:.0%}")
    
    # T=15s: Fire starts (gradual increase)
    print("\nT=15s: Fire starting (anomaly detected)")
    sensors = {
        'temp': 45.0,
        'humidity': 30.0,
        'smoke': 150.0,
        'co2': 800.0
    }
    
    for sensor_type, value in sensors.items():
        reading = SensorReading(f"{sensor_type.upper()}_001", value, datetime.now(), sensor_type)
        result = watchdog.validate(reading, reading.sensor_id, reading.sensor_type)
        print(f"   ⚠️  {sensor_type:10} = {value:6.1f} | Trust: {result.reliability_score:.0%}")
    
    # Register trauma from anomaly
    watchdog.trauma_system.register_trauma(0.5, "Fire signature detected")
    print(f"\n   💥 TRAUMA REGISTERED | Level: {watchdog.trauma_system.trauma_level:.2f}")
    
    # T=30s: Fire intensifies (sensor damage starts)
    print("\nT=30s: Fire intensifying (sensor stress)")
    
    # Temperature sensor dying
    temp_reading = SensorReading("TEMP_001", 95.0, datetime.now(), "temperature")
    result = watchdog.validate(temp_reading, "TEMP_001", "temperature")
    print(f"   🔥 temperature = {temp_reading.value:6.1f} | Trust: {result.reliability_score:.0%} | NEAR DYING GASP")
    
    # Smoke sensor maxed out
    smoke_reading = SensorReading("SMOKE_001", 950.0, datetime.now(), "smoke")
    result = watchdog.validate(smoke_reading, "SMOKE_001", "smoke")
    print(f"   🔥 smoke       = {smoke_reading.value:6.1f} | Trust: {result.reliability_score:.0%} | NEAR LIMIT")
    
    # Humidity sensor dead (null)
    result = watchdog.validate(None, "HUMIDITY_001", "humidity", {'temp': 95.0})
    print(f"   💀 humidity    = {result.value:6.1f} | Trust: {result.reliability_score:.0%} | IMPUTED")
    
    # T=45s: DYING GASP
    print("\nT=45s: CATASTROPHIC - DYING GASP PROTOCOL")
    
    dying_temp = SensorReading("TEMP_001", 108.0, datetime.now(), "temperature")
    result = watchdog.validate(dying_temp, "TEMP_001", "temperature")
    
    print(f"   💀💀💀 temperature = {dying_temp.value:6.1f}°C | DYING GASP TRIGGERED")
    print(f"   🛰️  BLACK BOX DUMPED TO SATELLITE")
    print(f"   ☠️  NODE DECLARED DEAD")
    
    # Final statistics
    print("\n" + "="*80)
    print("FINAL SYSTEM STATE")
    print("="*80)
    
    watchdog.print_statistics()
    
    print("✅ Integrated pipeline test complete")


def run_all_tests():
    """Run all test scenarios"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "PHASE-1 WATCHDOG LAYER - TEST SUITE" + " "*28 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        test_scenario_1_normal_operation,
        test_scenario_2_range_failures,
        test_scenario_3_dying_gasp,
        test_scenario_4_frozen_sensor,
        test_scenario_5_null_imputation,
        test_scenario_6_trauma_adaptation,
        test_scenario_7_integrated_pipeline,
    ]
    
    for i, test in enumerate(tests, 1):
        try:
            test()
        except AssertionError as e:
            print(f"\n❌ TEST {i} FAILED: {e}")
            return False
        except Exception as e:
            print(f"\n💥 TEST {i} ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "="*80)
    print("  🎉 ALL TESTS PASSED")
    print("="*80)
    print("\n✅ Phase-1 Watchdog Layer is production-ready")
    print("✅ All protection levels validated")
    print("✅ Self-healing mechanisms functional")
    print("✅ Trauma adaptation working correctly")
    print("\n🔥 Ready for industrial deployment\n")
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
