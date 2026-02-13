from phase1_watchdog_layer import Phase1WatchdogLayer, SensorReading
from datetime import datetime
import time
import random

# Initialize watchdog
watchdog = Phase1WatchdogLayer()

print("🔥 Testing Phase-1 with simulated sensor data...\n")

# Simulate 10 sensor readings
for i in range(10):
    # Simulate temperature reading
    temp = 20 + random.uniform(-35, 115)  # 15-35°C
    
    reading = SensorReading(
        sensor_id="TEMP_001",
        value=temp,
        timestamp=datetime.now(),
        sensor_type="temperature"
    )
    
    # Validate
    result = watchdog.validate(reading, "TEMP_001", "temperature")
    
    if result.is_valid:
        print(f"✅ Reading {i+1}: {result.value:.1f}°C | Trust: {result.reliability_score:.0%}")
    else:
        print(f"❌ Reading {i+1}: FAILED - {result.failure_reason}")
    
    time.sleep(1)

# Print statistics
watchdog.print_statistics()