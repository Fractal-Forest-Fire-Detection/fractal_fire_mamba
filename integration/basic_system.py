"""
🔥 COMPLETE FIRE DETECTION SYSTEM
Phase-1 Watchdog + Phase-0 Fusion (Unified)
"""

import time
import board
from datetime import datetime

from phase1_watchdog_layer import Phase1WatchdogLayer, SensorReading
from phase0_fusion_engine import Phase0FusionEngine

# ============================================================================
#  SENSOR INITIALIZATION
# ============================================================================

# ---- DHT22 ----
try:
    import adafruit_dht
    dht_sensor = adafruit_dht.DHT22(board.D4)
    HAS_DHT22 = True
except:
    HAS_DHT22 = False
    print("⚠️ DHT22 not available")

# ---- ADC (MQ Sensors) ----
try:
    import busio
    import adafruit_ads1x15.ads1015 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn

    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1015(i2c)

    smoke_sensor = AnalogIn(ads, ADS.P0)
    co2_sensor = AnalogIn(ads, ADS.P1)

    HAS_SMOKE = HAS_CO2 = True
except:
    HAS_SMOKE = HAS_CO2 = False
    print("⚠️ MQ sensors not available")

# ---- Flame Sensor ----
try:
    import RPi.GPIO as GPIO
    FLAME_PIN = 22
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(FLAME_PIN, GPIO.IN)
    HAS_FLAME = True
except:
    HAS_FLAME = False
    print("⚠️ Flame sensor not available")


# ============================================================================
#  PHASE-1 CONFIGURATION
# ============================================================================

config = {
    'sensor_ranges': {
        'temperature': {'min': -40, 'max': 120, 'dying_gasp': 100},
        'humidity': {'min': 0, 'max': 100},
        'smoke': {'min': 0, 'max': 1000, 'dying_gasp': 800},
        'co2': {'min': 0, 'max': 5000, 'dying_gasp': 4000},
        'flame': {'min': 0, 'max': 1},
    },
    'frozen_threshold_hours': 5,
    'black_box_buffer_seconds': 30
}

watchdog = Phase1WatchdogLayer(config=config)
fusion_engine = Phase0FusionEngine()


# ============================================================================
#  SENSOR READ
# ============================================================================

def read_all_sensors():
    sensors = {}
    now = datetime.now()

    if HAS_DHT22:
        try:
            sensors['TEMP_001'] = SensorReading(
                'TEMP_001', dht_sensor.temperature, now, 'temperature'
            )
            sensors['HUM_001'] = SensorReading(
                'HUM_001', dht_sensor.humidity, now, 'humidity'
            )
        except:
            sensors['TEMP_001'] = sensors['HUM_001'] = None

    if HAS_SMOKE:
        smoke_ppm = (smoke_sensor.voltage / 3.3) * 1000
        sensors['SMOKE_001'] = SensorReading(
            'SMOKE_001', smoke_ppm, now, 'smoke'
        )

    if HAS_CO2:
        co2_ppm = (co2_sensor.voltage / 3.3) * 5000
        sensors['CO2_001'] = SensorReading(
            'CO2_001', co2_ppm, now, 'co2'
        )

    if HAS_FLAME:
        flame = float(GPIO.input(FLAME_PIN))
        sensors['FLAME_001'] = SensorReading(
            'FLAME_001', flame, now, 'flame'
        )

    return sensors


# ============================================================================
#  PHASE-1 VALIDATION
# ============================================================================

def validate_all_sensors(raw):
    validated = {}
    available = {}

    for r in raw.values():
        if r and r.value is not None:
            available[r.sensor_type] = r.value

    for sid, reading in raw.items():
        result = watchdog.validate(
            reading=reading,
            sensor_id=sid,
            sensor_type=reading.sensor_type if reading else None,
            available_sensors=available
        )
        if result.is_valid:
            validated[sid] = result

    return validated


# ============================================================================
#  MAIN LOOP
# ============================================================================

def main():
    print("\n🔥 FIRE DETECTION SYSTEM ONLINE")
    print("🛡️ Phase-1 Watchdog ACTIVE")
    print("🧠 Phase-0 Fusion ACTIVE")

    try:
        while True:
            raw = read_all_sensors()
            validated = validate_all_sensors(raw)

            # 🔥 PHASE-0 DECISION (THIS IS THE BRAIN)
            env = fusion_engine.fuse(validated)

            print("\n🌲 ENVIRONMENTAL STATE")
            print(f"Fire Risk     : {env.fire_risk_score:.0%}")
            print(f"Agreement     : {env.cross_modal_agreement:.0%}")
            print(f"Confidence    : {env.overall_confidence:.0%}")

            if env.fire_detected:
                print("🚨🔥 FIRE DETECTED")
                # send_alert()
                # activate_suppression()

            if env.disagreement_flags:
                print(f"⚠️ Sensor Disagreement: {env.disagreement_flags}")

            time.sleep(10)

    except KeyboardInterrupt:
        print("\n🛑 System shutdown")
        if HAS_FLAME:
            GPIO.cleanup()


# ============================================================================
#  RUN
# ============================================================================

if __name__ == "__main__":
    main()
