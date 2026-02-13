"""
REAL SENSOR INTERFACE
Replaces MockSensorSimulator with actual hardware sensor connections

Supported Hardware:
- Chemical Sensors: BME680, CCS811, SGP30 (I2C)
- Environmental: DHT22, SHT31, Soil Moisture (Analog/I2C)
- Visual: Pi Camera, USB Camera, ESP32-CAM
- Temperature: DS18B20, BME280, DHT22
"""

import time
from datetime import datetime
from typing import Dict, Optional
import logging

# Import sensor libraries (install with pip if needed)
try:
    import board
    import busio
    import adafruit_bme680  # Chemical + Temp + Humidity + Pressure
    HAS_BME680 = True
except ImportError:
    HAS_BME680 = False
    print("⚠️  BME680 not available (pip install adafruit-circuitpython-bme680)")

try:
    import adafruit_ccs811  # VOC + CO2
    HAS_CCS811 = True
except ImportError:
    HAS_CCS811 = False
    print("⚠️  CCS811 not available (pip install adafruit-circuitpython-ccs811)")

try:
    import adafruit_dht  # Temperature + Humidity
    import RPi.GPIO as GPIO
    HAS_DHT = True
except ImportError:
    HAS_DHT = False
    print("⚠️  DHT sensor not available (pip install adafruit-circuitpython-dht)")

try:
    from picamera2 import Picamera2
    import numpy as np
    HAS_PICAMERA = True
except ImportError:
    HAS_PICAMERA = False
    print("⚠️  Pi Camera not available (pip install picamera2)")

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    print("⚠️  OpenCV not available (pip install opencv-python)")

try:
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    HAS_ADS1115 = True
except ImportError:
    HAS_ADS1115 = False
    print("⚠️  ADS1115 ADC not available (pip install adafruit-circuitpython-ads1x15)")

# Import Phase-1 SensorReading if available
try:
    from phase1_watchdog_layer import SensorReading
    HAS_PHASE1 = True
except ImportError:
    # Fallback dataclass
    from dataclasses import dataclass
    
    @dataclass
    class SensorReading:
        sensor_id: str
        value: float
        timestamp: datetime
        sensor_type: str
    
    HAS_PHASE1 = False


class RealSensorInterface:
    """
    Interface to real hardware sensors
    
    Replaces MockSensorSimulator with actual sensor readings
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize sensor interface
        
        Args:
            config: Sensor configuration dict with GPIO pins, I2C addresses, etc.
        """
        self.config = config or self._default_config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize sensors
        self.sensors = {}
        self._init_i2c()
        self._init_chemical_sensors()
        self._init_environmental_sensors()
        self._init_camera()
        
        self.logger.info("✅ Real sensor interface initialized")
    
    def _default_config(self) -> Dict:
        """Default sensor configuration"""
        return {
            # I2C Configuration
            'i2c_bus': 1,  # Default I2C bus on Raspberry Pi
            
            # Chemical Sensors
            'bme680_address': 0x77,  # or 0x76
            'ccs811_address': 0x5A,
            'sgp30_address': 0x58,
            
            # Environmental Sensors
            'dht_pin': 4,  # GPIO pin for DHT22
            'dht_type': 'DHT22',  # or 'DHT11'
            'soil_moisture_pin': 0,  # ADC channel (ADS1115)
            
            # Camera
            'camera_type': 'picamera',  # 'picamera', 'usb', or 'esp32cam'
            'camera_resolution': (160, 120),  # Low res for processing
            'usb_camera_index': 0,  # For USB cameras
            'esp32cam_url': 'http://192.168.1.100/cam-hi.jpg',  # ESP32-CAM stream
            
            # Timing
            'sensor_warmup_time': 5,  # Seconds to warm up sensors
        }
    
    def _init_i2c(self):
        """Initialize I2C bus"""
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.logger.info("✅ I2C bus initialized")
        except Exception as e:
            self.logger.warning(f"⚠️  I2C initialization failed: {e}")
            self.i2c = None
    
    def _init_chemical_sensors(self):
        """Initialize chemical sensors"""
        # BME680: VOC, Temperature, Humidity, Pressure
        if HAS_BME680 and self.i2c:
            try:
                self.sensors['BME680'] = adafruit_bme680.Adafruit_BME680_I2C(
                    self.i2c, 
                    address=self.config['bme680_address']
                )
                # Set oversampling for better accuracy
                self.sensors['BME680'].sea_level_pressure = 1013.25
                self.logger.info("✅ BME680 initialized (VOC, Temp, Humidity, Pressure)")
            except Exception as e:
                self.logger.warning(f"⚠️  BME680 init failed: {e}")
        
        # CCS811: eCO2 and TVOC
        if HAS_CCS811 and self.i2c:
            try:
                self.sensors['CCS811'] = adafruit_ccs811.CCS811(
                    self.i2c,
                    address=self.config['ccs811_address']
                )
                # Wait for sensor to be ready
                while not self.sensors['CCS811'].data_ready:
                    time.sleep(0.5)
                self.logger.info("✅ CCS811 initialized (eCO2, TVOC)")
            except Exception as e:
                self.logger.warning(f"⚠️  CCS811 init failed: {e}")
    
    def _init_environmental_sensors(self):
        """Initialize environmental sensors"""
        # DHT22: Temperature and Humidity
        if HAS_DHT and self.config.get('dht_pin'):
            try:
                pin = getattr(board, f"D{self.config['dht_pin']}")
                if self.config['dht_type'] == 'DHT22':
                    self.sensors['DHT'] = adafruit_dht.DHT22(pin)
                else:
                    self.sensors['DHT'] = adafruit_dht.DHT11(pin)
                self.logger.info(f"✅ {self.config['dht_type']} initialized")
            except Exception as e:
                self.logger.warning(f"⚠️  DHT init failed: {e}")
        
        # ADS1115 ADC for analog sensors (soil moisture)
        if HAS_ADS1115 and self.i2c:
            try:
                self.sensors['ADS1115'] = ADS.ADS1115(self.i2c)
                self.logger.info("✅ ADS1115 ADC initialized (for analog sensors)")
            except Exception as e:
                self.logger.warning(f"⚠️  ADS1115 init failed: {e}")
    
    def _init_camera(self):
        """Initialize camera"""
        camera_type = self.config.get('camera_type', 'picamera')
        
        if camera_type == 'picamera' and HAS_PICAMERA:
            try:
                self.sensors['CAMERA'] = Picamera2()
                config = self.sensors['CAMERA'].create_still_configuration(
                    main={"size": self.config['camera_resolution']}
                )
                self.sensors['CAMERA'].configure(config)
                self.sensors['CAMERA'].start()
                time.sleep(2)  # Warm up
                self.logger.info("✅ Pi Camera initialized")
            except Exception as e:
                self.logger.warning(f"⚠️  Pi Camera init failed: {e}")
        
        elif camera_type == 'usb' and HAS_OPENCV:
            try:
                self.sensors['CAMERA'] = cv2.VideoCapture(
                    self.config['usb_camera_index']
                )
                if self.sensors['CAMERA'].isOpened():
                    self.logger.info("✅ USB Camera initialized")
                else:
                    self.logger.warning("⚠️  USB Camera failed to open")
            except Exception as e:
                self.logger.warning(f"⚠️  USB Camera init failed: {e}")
    
    def read_sensors(self) -> Dict:
        """
        Read all available sensors
        
        Returns:
            Dict of SensorReading objects
        """
        timestamp = datetime.now()
        readings = {}
        
        # Chemical sensors
        readings.update(self._read_chemical_sensors(timestamp))
        
        # Environmental sensors
        readings.update(self._read_environmental_sensors(timestamp))
        
        # Camera
        camera_reading = self._read_camera(timestamp)
        if camera_reading:
            readings['CAMERA'] = camera_reading
        
        return readings
    
    def _read_chemical_sensors(self, timestamp: datetime) -> Dict:
        """Read chemical sensors"""
        readings = {}
        
        # BME680
        if 'BME680' in self.sensors:
            try:
                sensor = self.sensors['BME680']
                
                # VOC (Gas Resistance) - lower resistance = more VOCs
                # Convert to approximate PPB (parts per billion)
                gas_resistance = sensor.gas
                voc_ppb = self._gas_resistance_to_voc(gas_resistance)
                
                readings['VOC'] = SensorReading(
                    sensor_id='VOC',
                    value=voc_ppb,
                    timestamp=timestamp,
                    sensor_type='voc'
                )
                
                # Temperature from BME680
                readings['TEMPERATURE'] = SensorReading(
                    sensor_id='TEMPERATURE',
                    value=sensor.temperature,
                    timestamp=timestamp,
                    sensor_type='temperature'
                )
                
                # Humidity from BME680
                readings['HUMIDITY'] = SensorReading(
                    sensor_id='HUMIDITY',
                    value=sensor.humidity,
                    timestamp=timestamp,
                    sensor_type='humidity'
                )
                
            except Exception as e:
                self.logger.error(f"❌ BME680 read error: {e}")
        
        # CCS811
        if 'CCS811' in self.sensors:
            try:
                sensor = self.sensors['CCS811']
                if sensor.data_ready:
                    # TVOC in PPB
                    readings['TVOC'] = SensorReading(
                        sensor_id='TVOC',
                        value=sensor.tvoc,
                        timestamp=timestamp,
                        sensor_type='voc'
                    )
                    
                    # eCO2 in PPM
                    readings['CO2'] = SensorReading(
                        sensor_id='CO2',
                        value=sensor.eco2,
                        timestamp=timestamp,
                        sensor_type='co2'
                    )
            except Exception as e:
                self.logger.error(f"❌ CCS811 read error: {e}")
        
        return readings
    
    def _read_environmental_sensors(self, timestamp: datetime) -> Dict:
        """Read environmental sensors"""
        readings = {}
        
        # DHT22
        if 'DHT' in self.sensors:
            try:
                sensor = self.sensors['DHT']
                
                # Temperature
                temp = sensor.temperature
                if temp is not None:
                    readings['TEMPERATURE_DHT'] = SensorReading(
                        sensor_id='TEMPERATURE_DHT',
                        value=temp,
                        timestamp=timestamp,
                        sensor_type='temperature'
                    )
                
                # Humidity
                humidity = sensor.humidity
                if humidity is not None:
                    readings['HUMIDITY_DHT'] = SensorReading(
                        sensor_id='HUMIDITY_DHT',
                        value=humidity,
                        timestamp=timestamp,
                        sensor_type='humidity'
                    )
                    
            except RuntimeError as e:
                # DHT sensors can timeout occasionally
                self.logger.debug(f"DHT read timeout: {e}")
            except Exception as e:
                self.logger.error(f"❌ DHT read error: {e}")
        
        # Soil Moisture (via ADS1115)
        if 'ADS1115' in self.sensors:
            try:
                ads = self.sensors['ADS1115']
                channel = AnalogIn(ads, ADS.P0)  # Use channel 0
                
                # Convert voltage to moisture percentage
                # Calibration needed: dry = ~3.3V (100%), wet = ~1.2V (0%)
                voltage = channel.voltage
                moisture_percent = self._voltage_to_moisture(voltage)
                
                readings['SOIL_MOISTURE'] = SensorReading(
                    sensor_id='SOIL_MOISTURE',
                    value=moisture_percent,
                    timestamp=timestamp,
                    sensor_type='soil_moisture'
                )
                
            except Exception as e:
                self.logger.error(f"❌ Soil moisture read error: {e}")
        
        return readings
    
    def _read_camera(self, timestamp: datetime) -> Optional[SensorReading]:
        """Read camera image"""
        if 'CAMERA' not in self.sensors:
            return None
        
        try:
            camera_type = self.config.get('camera_type', 'picamera')
            
            if camera_type == 'picamera':
                # Capture from Pi Camera
                image = self.sensors['CAMERA'].capture_array()
                # Resize to expected dimensions
                if image.shape[:2] != self.config['camera_resolution'][::-1]:
                    import cv2
                    image = cv2.resize(image, self.config['camera_resolution'])
                # Normalize to 0-1
                image = image.astype(np.float32) / 255.0
                
            elif camera_type == 'usb':
                # Capture from USB camera
                ret, frame = self.sensors['CAMERA'].read()
                if not ret:
                    return None
                # Resize and normalize
                import cv2
                image = cv2.resize(frame, self.config['camera_resolution'])
                image = image.astype(np.float32) / 255.0
            
            else:
                return None
            
            return SensorReading(
                sensor_id='CAMERA',
                value=image,
                timestamp=timestamp,
                sensor_type='camera'
            )
            
        except Exception as e:
            self.logger.error(f"❌ Camera read error: {e}")
            return None
    
    def _gas_resistance_to_voc(self, resistance: float) -> float:
        """
        Convert BME680 gas resistance to approximate VOC in PPB
        
        Calibration curve (you may need to adjust based on your sensor):
        - High resistance (>100kΩ) = clean air (~50 PPB)
        - Low resistance (<10kΩ) = high VOCs (>500 PPB)
        """
        # Logarithmic relationship
        if resistance > 0:
            # Inverse relationship: lower resistance = higher VOC
            voc = 1000.0 / (resistance / 1000.0 + 1.0)
            return min(max(voc, 0), 1000)  # Clamp to 0-1000 PPB
        return 0
    
    def _voltage_to_moisture(self, voltage: float) -> float:
        """
        Convert soil moisture sensor voltage to percentage
        
        Calibration (adjust for your sensor):
        - Dry soil: 3.3V = 0% moisture
        - Wet soil: 1.2V = 100% moisture
        """
        DRY_VOLTAGE = 3.3
        WET_VOLTAGE = 1.2
        
        # Linear interpolation
        moisture = 100.0 * (DRY_VOLTAGE - voltage) / (DRY_VOLTAGE - WET_VOLTAGE)
        return min(max(moisture, 0), 100)  # Clamp to 0-100%
    
    def calibrate_sensors(self, duration: int = 60):
        """
        Calibrate sensors by taking baseline readings
        
        Args:
            duration: Calibration duration in seconds
        """
        print(f"\n🔧 Calibrating sensors for {duration} seconds...")
        print("Ensure sensors are in clean air with normal conditions\n")
        
        readings_log = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            readings = self.read_sensors()
            readings_log.append(readings)
            
            # Print progress
            elapsed = int(time.time() - start_time)
            print(f"\rCalibrating... {elapsed}/{duration}s", end='', flush=True)
            
            time.sleep(1)
        
        print("\n\n✅ Calibration complete!")
        
        # Calculate baselines
        # TODO: Compute and save baseline values
        
    def close(self):
        """Close all sensor connections"""
        if 'CAMERA' in self.sensors:
            camera_type = self.config.get('camera_type')
            if camera_type == 'picamera':
                self.sensors['CAMERA'].close()
            elif camera_type == 'usb':
                self.sensors['CAMERA'].release()
        
        self.logger.info("✅ Sensors closed")


# ============================================================================
#  USAGE EXAMPLE
# ============================================================================

def test_real_sensors():
    """Test real sensor interface"""
    print("\n" + "="*70)
    print("🔬 TESTING REAL SENSOR INTERFACE")
    print("="*70 + "\n")
    
    # Initialize
    sensor_interface = RealSensorInterface()
    
    # Read sensors 5 times
    for i in range(5):
        print(f"\n📡 Reading {i+1}/5...")
        readings = sensor_interface.read_sensors()
        
        for sensor_id, reading in readings.items():
            if sensor_id == 'CAMERA':
                print(f"  {sensor_id}: Image {reading.value.shape}")
            else:
                print(f"  {sensor_id}: {reading.value:.2f} at {reading.timestamp.strftime('%H:%M:%S')}")
        
        time.sleep(2)
    
    # Close
    sensor_interface.close()
    print("\n✅ Test complete!")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_real_sensors()
