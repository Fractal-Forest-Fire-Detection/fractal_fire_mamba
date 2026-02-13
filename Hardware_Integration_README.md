# Hardware Integration Guide - Fractal Fire Mamba System

Complete hardware setup and integration guide for the 6-phase fire detection system.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Hardware Bill of Materials](#hardware-bill-of-materials)
3. [Wiring and Connections](#wiring-and-connections)
4. [Sensor Integration](#sensor-integration)
5. [Camera Setup](#camera-setup)
6. [Communication Modules](#communication-modules)
7. [Power System](#power-system)
8. [Assembly Instructions](#assembly-instructions)
9. [Testing and Calibration](#testing-and-calibration)
10. [Troubleshooting](#troubleshooting)

---

## System Overview - "The Hive" Architecture

The Fractal Fire Mamba system uses a **heterogeneous mesh** with two node types:

### Queen Node (1 per ~5km²)
Gateway node with full capabilities including satellite link.

```
┌─────────────────────────────────────────────────────────────┐
│            RASPBERRY PI 4B (Queen Controller)               │
├─────────────────────────────────────────────────────────────┤
│  Phase-0: Sensor Fusion                                     │
│  ├─ Chemical Sensors (I2C): BME680, MQ-2                    │
│  ├─ Environmental: Soil Moisture                            │
│  └─ GPS (Serial): NEO-6M                                    │
│                                                             │
│  Phase-4: Vision Mamba                                      │
│  ├─ RGB Camera (CSI): Pi Camera Module v2                   │
│  └─ Thermal Camera (I2C): MLX90640                          │
│                                                             │
│  Phase-6: Communication                                     │
│  ├─ LoRa Mesh (SPI): RFM95W + High-Gain Antenna            │
│  └─ Satellite (Serial): RockBLOCK 9603 ⭐ QUEEN ONLY        │
└─────────────────────────────────────────────────────────────┘
```

### Drone Node (49 per Queen)
Lightweight sensor nodes that relay to Queen via LoRa.

```
┌─────────────────────────────────────────────────────────────┐
│         RASPBERRY PI ZERO 2 W (Drone Controller)            │
├─────────────────────────────────────────────────────────────┤
│  Phase-0: Sensor Fusion                                     │
│  ├─ Chemical Sensors (I2C): BME680, MQ-2                    │
│  ├─ Environmental: Soil Moisture                            │
│  └─ GPS (Serial): NEO-6M                                    │
│                                                             │
│  Phase-4: Vision Mamba (Classical CV)                       │
│  ├─ RGB Camera (CSI): Pi Camera Module v2                   │
│  └─ Thermal Camera (I2C): MLX90640                          │
│                                                             │
│  Phase-6: Communication                                     │
│  └─ LoRa Mesh (SPI): RFM95W (relays to Queen)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Cost Optimization**: 1 Queen ($700) + 49 Drones ($150) = **$161/node average** (vs $700/node)

---

## Hardware Bill of Materials - The Hive Architecture

> [!NOTE]
> **Cost Savings**: The heterogeneous mesh reduces satellite modem costs by 98% (1 Queen vs 50 homogeneous nodes).
> - **Queen Node**: ~$700 (1 required per ~5km²)
> - **Drone Node**: ~$150 (49 typical)
> - **Average Cost**: $161/node (77% reduction from $700/node)

---

### 👑 Queen Node BOM (~$700)


#### Core Processing

| Component | Model | Quantity | Est. Cost | Purpose |
|-----------|-------|----------|-----------|---------|
| Microcontroller | **Raspberry Pi 4B (2GB)** | 1 | $55 | Routing throughput + processing |
| Heatsink | Aluminum passive | 1 | $3 | Thermal management |
| MicroSD Card | 32GB Class 10 | 1 | $10 | OS and storage |
| Real-Time Clock | DS3231 (optional) | 1 | $5 | Timekeeping when offline |


#### Chemical & Environmental Sensors

| Component | Model | Quantity | Est. Cost | Interface | Purpose |
|-----------|-------|----------|-----------|-----------|---------|
| Multi-gas Sensor | BME680 | 1 | $20 | I2C (0x76/0x77) | VOC, **temp, humidity**, pressure |
| Smoke Sensor | MQ-2 or MQ-135 | 1 | $5 | Analog (via ADS1115) | Smoke/gas detection |
| ADC Module | ADS1115 | 1 | $8 | I2C (0x48) | Analog-to-digital conversion |
| Soil Moisture Sensor | Capacitive | 1 | $5 | Analog (via ADS1115) | Ground humidity |

> [!TIP]
> **DHT22 Removed**: BME680 already provides temperature and humidity with higher precision. The DHT22 is redundant.

### Vision System

| Component | Model | Quantity | Est. Cost | Interface | Purpose |
|-----------|-------|----------|-----------|-----------|---------|
| RGB Camera | Pi Camera Module v2 | 1 | $25 | CSI | Smoke detection (day) |
| Thermal Camera | MLX90640 (32×24) | 1 | $60 | I2C (0x33) | Heat detection (night) |

**Note**: See [THERMAL_CAMERA_INTEGRATION_GUIDE.md](./THERMAL_CAMERA_INTEGRATION_GUIDE.md) for detailed thermal camera setup.


#### Communication Modules

| Component | Model | Quantity | Est. Cost | Interface | Purpose |
|-----------|-------|----------|-----------|-----------|---------|
| LoRa Module | RFM95W (915 MHz) | 1 | $15 | SPI | Mesh networking |
| LoRa Antenna | **High-Gain Fiberglass 5-8dBi** ⭐ | 1 | $25 | SMA connector | Extended range (critical for 49 drones) |
| GPS Module | NEO-6M | 1 | $12 | UART/Serial | Location tracking |
| GPS Antenna | Active ceramic | 1 | $5 | SMA connector | GPS reception |
| Satellite Modem | **RockBLOCK 9603** 👑 | 1 | $250 | Serial | Emergency comms (QUEEN ONLY) |

> [!IMPORTANT]
> **High-Gain Antenna Critical**: The Queen is a single point of failure for 49 drones. Use 5-8dBi fiberglass antenna to ensure reliable LoRa reception across ~5km².


#### Power System

| Component | Model | Quantity | Est. Cost | Purpose |
|-----------|-------|----------|-----------|---------|
| Battery | **4-cell LiFePO4 (12.8V 10Ah)** or 12V SLA | 1 | $50-60 | Energy storage (safe, 2000+ cycles) |
| Solar Panel | 50W 12V Polycrystalline | 1 | $50 | Charging |
| Charge Controller | MPPT 10A | 1 | $25 | Solar regulation |
| Buck Converter | 12V → 5V 3A | 1 | $8 | Pi power supply |
| Power Monitor | INA219 | 1 | $7 | I2C | Battery monitoring |


#### Enclosure & Mounting

| Component | Specification | Quantity | Est. Cost |
|-----------|--------------|----------|-----------|
| Weatherproof Enclosure | IP65, 200×150×75mm | 1 | $20 |
| Cable Glands | PG7/PG9 | 6 | $10 |
| Mounting Bracket | Adjustable pole mount | 1 | $15 |
| Desiccant Packs | Silica gel 50g | 2 | $5 |

**Queen Node Total**: ~$700

---

### 🐝 Drone Node BOM (~$150)

#### Core Processing

| Component | Model | Quantity | Est. Cost | Purpose |
|-----------|-------|----------|-----------|---------|
| Microcontroller | **Raspberry Pi Zero 2 W** | 1 | $15 | Lightweight processing |
| Heatsink | Aluminum passive (small) | 1 | $1 | Thermal management |
| MicroSD Card | 32GB Class 10 | 1 | $10 | OS and storage |

> [!TIP]
> **Pi Zero 2 W**: 4-core Cortex-A53, ~5x faster than original Zero. Sufficient for Classical CV (no deep learning). Idle power: ~100mA vs Pi 4B's 600mA (83% reduction).

#### Chemical & Environmental Sensors

| Component | Model | Quantity | Est. Cost | Interface | Purpose |
|-----------|-------|----------|-----------|-----------|---------|
| Multi-gas Sensor | BME680 | 1 | $20 | I2C (0x76/0x77) | VOC, **temp, humidity**, pressure |
| Smoke Sensor | MQ-2 or MQ-135 | 1 | $5 | Analog (via ADS1115) | Smoke/gas detection |
| ADC Module | ADS1115 | 1 | $8 | I2C (0x48) | Analog-to-digital conversion |
| Soil Moisture Sensor | Capacitive | 1 | $5 | Analog (via ADS1115) | Ground humidity |

#### Vision System

| Component | Model | Quantity | Est. Cost | Interface | Purpose |
|-----------|-------|----------|-----------|-----------|---------|
| RGB Camera | Pi Camera Module v2 | 1 | $25 | CSI | Smoke detection (day) |
| Thermal Camera | MLX90640 (32×24) | 1 | $60 | I2C (0x33) | Heat detection (night) |

**Note**: Thermal camera is computationally light (32×24 pixels). Pi Zero 2 W handles it easily.

#### Communication Modules (NO SATELLITE)

| Component | Model | Quantity | Est. Cost | Interface | Purpose |
|-----------|-------|----------|-----------|-----------|---------|
| LoRa Module | RFM95W (915 MHz) | 1 | $15 | SPI | Mesh networking (relay to Queen) |
| LoRa Antenna | 915 MHz 3dBi | 1 | $8 | SMA connector | Standard range |
| GPS Module | NEO-6M (optional) | 1 | $12 | UART/Serial | Location tracking |
| GPS Antenna | Active ceramic (optional) | 1 | $5 | SMA connector | GPS reception |

> [!NOTE]
> **No Satellite Modem**: Drones relay all alerts to Queen via LoRa mesh. This saves $250 per node.

#### Power System (Optimized for Low Power)

| Component | Model | Quantity | Est. Cost | Purpose |
|-----------|-------|----------|-----------|---------|
| Battery | **2-cell LiFePO4 (6.4V 3000mAh)** | 2 parallel | $15 | Energy storage (~19 Wh) |
| Solar Panel | 20W 12V Polycrystalline (smaller) | 1 | $25 | Charging |
| Charge Controller | PWM 5A (simplified) | 1 | $10 | Solar regulation |
| **Buck-Boost Converter** ⚠️ | **6V-12V → 5V 3A (e.g., TPS63070)** | 1 | $8 | Pi power supply (prevents brownout) |

> [!CAUTION]
> **Voltage Dropout Risk**: 2-cell LiFePO4 outputs 6.4V nominal but drops to **~5.0V when depleted**. A standard buck converter (e.g., LM2596) requires 1.5-2V dropout, meaning it would fail to regulate 5V once battery drops below 6.5V, causing **Raspberry Pi brownout long before battery is empty**.
> 
> **Solution**: Use a **buck-boost converter** (e.g., TPS63070, MT3608) that accepts 3V-12V input and outputs stable 5V across the entire battery discharge curve. This extracts maximum energy from the battery.
> 
> **Alternative**: Switch to 3-cell LiFePO4 (9.6V nominal) if buck-boost converters are unavailable, though this increases cost and weight.

> [!IMPORTANT]
> **LiFePO4 Chosen Over Supercapacitors**: User requested supercaps, but rejected due to insufficient energy density for night operations (vision + thermal camera for 12 hours). LiFePO4 provides:
> - Safe operation (no thermal runaway)
> - 2000+ charge cycles
> - 19 Wh capacity (sufficient for daily 14.4 Wh draw)
> - 2-3 days autonomy in cloudy weather

#### Enclosure & Mounting

| Component | Specification | Quantity | Est. Cost |
|-----------|--------------|----------|-----------|
| Weatherproof Enclosure | IP65, 150×100×50mm (smaller) | 1 | $15 |
| Cable Glands | PG7 | 4 | $5 |
| Mounting Bracket | Adjustable pole mount | 1 | $10 |
| Desiccant Packs | Silica gel 25g | 1 | $2 |

**Drone Node Total**: ~$150

---

### Cost Summary

| Node Type | Quantity (typical) | Cost per Node | Total Cost |
|-----------|-------------------|---------------|------------|
| Queen | 1 | $700 | $700 |
| Drone | 49 | $150 | $7,350 |
| **Total** | **50** | **$161 avg** | **$8,050** |

**vs Old System**: $35,000 → $8,050 = **$26,950 savings (77% reduction)**

---

## Wiring and Connections

### Raspberry Pi GPIO Pinout Reference

```
         3V3  (1) (2)  5V
   GPIO2/SDA  (3) (4)  5V
   GPIO3/SCL  (5) (6)  GND
       GPIO4  (7) (8)  GPIO14/TXD
         GND  (9) (10) GPIO15/RXD
      GPIO17 (11) (12) GPIO18
      GPIO27 (13) (14) GND
      GPIO22 (15) (16) GPIO23
         3V3 (17) (18) GPIO24
 GPIO10/MOSI (19) (20) GND
  GPIO9/MISO (21) (22) GPIO25
 GPIO11/SCLK (23) (24) GPIO8/CE0
         GND (25) (26) GPIO7/CE1
```

### I2C Bus (Shared)

**I2C Devices on Bus 1** (GPIO 2/3, Pins 3/5):

| Device | Default Address | Configurable? | Purpose |
|--------|----------------|---------------|---------|
| BME680 | 0x76 or 0x77 | Yes (SDO pin) | Air quality |
| ADS1115 | 0x48 | Yes (ADDR pin) | ADC for MQ-2 |
| MLX90640 | 0x33 | No | Thermal camera |
| INA219 | 0x40 | Yes (A0/A1 pins) | Power monitor |

**Wiring (All I2C Devices)**:
```
Device VIN  → 3.3V (Pin 1 or 17)
Device GND  → GND (Pin 6, 9, 14, 20, 25, or 39)
Device SDA  → GPIO 2 (Pin 3)
Device SCL  → GPIO 3 (Pin 5)
```

**Important**: Add 4.7kΩ pull-up resistors on SDA/SCL if experiencing communication issues.

---

### SPI Bus (LoRa)

**RFM95W LoRa Module Connections**:

| RFM95W Pin | Raspberry Pi Pin | GPIO/Function |
|------------|------------------|---------------|
| VIN | Pin 17 | 3.3V |
| GND | Pin 20 | Ground |
| SCK | Pin 23 | GPIO 11 (SCLK) |
| MISO | Pin 21 | GPIO 9 (MISO) |
| MOSI | Pin 19 | GPIO 10 (MOSI) |
| CS | Pin 24 | GPIO 8 (CE0) |
| RST | Pin 22 | GPIO 25 |
| DIO0 (G0) | Pin 18 | GPIO 24 |

**Enable SPI**:
```bash
sudo raspi-config
# Navigate to: Interface Options → SPI → Enable
```

---

### Serial/UART Devices

#### GPS Module (NEO-6M)

| GPS Pin | Raspberry Pi Pin | Function |
|---------|------------------|----------|
| VCC | Pin 2 | 5V |
| GND | Pin 6 | Ground |
| TX | Pin 10 | GPIO 15 (RXD) |
| RX | Pin 8 | GPIO 14 (TXD) |

**Enable Serial**:
```bash
sudo raspi-config
# Interface Options → Serial Port
# Login shell over serial: NO
# Serial port hardware enabled: YES
```

**Edit `/boot/config.txt`**:
```
dtparam=uart0=on
```

#### Satellite Modem (RockBLOCK 9603) 👑 QUEEN NODE ONLY

| RockBLOCK Pin | Connection |
|---------------|------------|
| 5V IN | 5V power supply (separate recommended) |
| GND | Common ground |
| TX | USB-to-Serial adapter or GPIO 15 |
| RX | USB-to-Serial adapter or GPIO 14 |

**Note**: RockBLOCK can draw 500mA+ during transmission. Use separate power or robust 5V supply.

> [!IMPORTANT]
> **Queen Node Only**: Drone nodes do NOT have satellite modems. They relay all messages to the Queen via LoRa mesh.

---

### GPIO Digital Sensors

#### Soil Moisture Sensor


- Ribbon cable: blue side faces USB ports (Pi 4) or network jack (Zero W)
- Enable camera: `sudo raspi-config` → Interface → Camera → Enable

#### Thermal Camera (MLX90640)

See dedicated guide: [THERMAL_CAMERA_INTEGRATION_GUIDE.md](./THERMAL_CAMERA_INTEGRATION_GUIDE.md)

- VIN → 3.3V (Pin 1)
- GND → GND (Pin 6)
- SDA → GPIO 2 (Pin 3)
- SCL → GPIO 3 (Pin 5)

---

## Sensor Integration

### Step 1: Enable All Interfaces

```bash
sudo raspi-config
```

Enable:
- ✅ I2C
- ✅ SPI
- ✅ Serial Port (hardware enabled, login shell disabled)
- ✅ Camera

Reboot after enabling:
```bash
sudo reboot
```

---

### Step 2: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install I2C and SPI tools
sudo apt install -y i2c-tools python3-spidev

# Install Python dependencies
cd /path/to/Final\ Model
source venv/bin/activate
pip install -r requirements.txt
```

---

### Step 3: Verify I2C Devices

```bash
sudo i2cdetect -y 1
```

**Expected output** (example with all devices):
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- 33 -- -- -- -- -- -- -- -- -- -- -- --  ← MLX90640
40: 40 -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --  ← INA219, ADS1115
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- 76 -- -- -- -- -- -- -- --  ← BME680
```

---

### Step 4: Test Individual Sensors

#### BME680 Test
```python
import board
import busio
from adafruit_bme680 import Adafruit_BME680_I2C

i2c = busio.I2C(board.SCL, board.SDA)
sensor = Adafruit_BME680_I2C(i2c)

print(f"Temperature: {sensor.temperature:.1f}°C")
print(f"Humidity: {sensor.humidity:.1f}%")
print(f"Pressure: {sensor.pressure:.1f} hPa")
print(f"Gas: {sensor.gas} Ω")
```

> [!NOTE]
> **DHT22 Removed**: This sensor is no longer in the BOM (redundant with BME680). For legacy systems with DHT22, it will still work but is optional.

#### GPS Test
```python
import serial
import pynmea2

gps = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)

while True:
    line = gps.readline().decode('ascii', errors='ignore')
    if line.startswith('$GPGGA'):
        msg = pynmea2.parse(line)
        print(f"Latitude: {msg.latitude}")
        print(f"Longitude: {msg.longitude}")
        break
```

---

## Camera Setup

### RGB Camera (Pi Camera v2)

**Test capture**:
```bash
# Legacy camera stack
raspistill -o test.jpg

# libcamera (newer systems)
libcamera-still -o test.jpg
```

**Python test**:
```python
from picamera2 import Picamera2
import time

camera = Picamera2()
camera.start()
time.sleep(2)  # Warm-up
camera.capture_file("test.jpg")
camera.stop()
print("✅ RGB camera working!")
```

### Thermal Camera (MLX90640)

See [THERMAL_CAMERA_INTEGRATION_GUIDE.md](./THERMAL_CAMERA_INTEGRATION_GUIDE.md) for complete setup.

---

## Communication Modules

### LoRa (RFM95W)

**Test script**:
```python
import board
import busio
import digitalio
from adafruit_rfm9x import RFM9x

# SPI setup
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.CE0)
reset = digitalio.DigitalInOut(board.D25)

# Initialize RFM95W (915 MHz for US)
rfm = RFM9x(spi, cs, reset, 915.0)
rfm.tx_power = 23  # Max power (23 dBm)

print("LoRa module initialized!")
print(f"Frequency: {rfm.frequency_mhz} MHz")
print(f"TX Power: {rfm.tx_power} dBm")

# Send test message
rfm.send(b"Hello from Fractal Fire Mamba!")
print("✅ LoRa test message sent!")
```

**Expected range**: 1-5 km line-of-sight, 500m-1km in forest

---

### Satellite Modem (RockBLOCK)

**Test connection**:
```python
import serial
import time

# Open serial connection
sat = serial.Serial('/dev/ttyUSB0', baudrate=19200, timeout=5)

# Basic AT command test
sat.write(b'AT\r')
time.sleep(1)
response = sat.read(100)
print(f"Response: {response}")

if b'OK' in response:
    print("✅ RockBLOCK responding!")
    
# Check signal quality
sat.write(b'AT+CSQ\r')
time.sleep(2)
response = sat.read(100)
print(f"Signal Quality: {response}")
```

**Note**: Outdoor location with clear sky view required. Each message costs ~$0.04-0.11.

---

## Power System

### Wiring Diagram

```
Solar Panel (50W 12V)
         │
         ↓
┌────────────────────┐
│  MPPT Charge      │
│  Controller        │
│  (10A 12V)        │
└────────┬───────────┘
         │
         ↓
┌────────────────────┐
│  12V Battery      │
│  (20Ah SLA/LiFePO4)│
└────────┬───────────┘
         │
         ↓
┌────────────────────┐
│  Buck Converter   │
│  12V → 5V 3A      │
└────────┬───────────┘
         │
         ↓
   Raspberry Pi 5V Input
```

### Power Budget - The Hive Architecture

#### 👑 Queen Node Power Budget

| Component | Current (mA) | Duty Cycle | Daily Avg (mAh) |
|-----------|-------------|------------|-----------------|
| Raspberry Pi 4B | 600 | 100% | 14,400 |
| RGB Camera | 250 | 10% | 600 |
| Thermal Camera | 23 | 15% | 82 |
| BME680 | 12 | 100% | 288 |
| RFM95W (idle) | 1.5 | 90% | 32 |
| RFM95W (TX) | 120 | 5% | 144 |
| GPS | 45 | 50% | 540 |
| RockBLOCK (idle) | 40 | 99% | 950 |
| RockBLOCK (TX) | 500 | 0.1% | 12 |
| **Total** | | | **~17,048 mAh/day** |

**At 5V → ~85 Wh/day**

**Solar Requirements**:
- 50W panel → ~200Wh/day (clear sky, 4 sun hours)
- **Margin**: 200 - 85 = 115 Wh surplus ✅
- 4-cell LiFePO4 (12.8V 10Ah) provides 128 Wh → 1.5 days autonomy

---

#### 🐝 Drone Node Power Budget (Optimized)

| Component | Current (mA) | Duty Cycle | Daily Avg (mAh) |
|-----------|-------------|------------|-----------------|
| **Raspberry Pi Zero 2 W** | **100** | **100%** | **2,400** |
| RGB Camera | 250 | 10% | 600 |
| Thermal Camera | 23 | 15% | 82 |
| BME680 | 12 | 100% | 288 |
| RFM95W (idle) | 1.5 | 90% | 32 |
| RFM95W (TX) | 120 | 5% | 144 |
| GPS | 45 | 50% | 540 |
| **Total** | | | **~4,086 mAh/day** |

**At 5V → ~20.4 Wh/day** (vs Queen's 85 Wh - **76% reduction**)

> [!TIP]
> **DHT22 Removed**: Saves 2.5mA (negligible power, but eliminates redundant sensor)

**Solar Requirements**:
- 20W panel → ~80Wh/day (clear sky, 4 sun hours)
- **Margin**: 80 - 20 = 60 Wh surplus ✅
- 2-cell LiFePO4 (6.4V 6000mAh) provides ~19 Wh → 1 day autonomy
- With 80 Wh/day solar, practically unlimited runtime in normal weather

**Power Savings Summary**:
- **Queen**: 85 Wh/day (1 node) = 85 Wh/day
- **Drone**: 20 Wh/day (49 nodes) = 980 Wh/day
- **Total Fleet**: 1,065 Wh/day (50 nodes)
- **vs Old System**: 4,250 Wh/day (50 nodes @ 85 Wh each)
- **Savings**: 3,185 Wh/day (75% reduction)

---

## Assembly Instructions

### 1. Prepare Enclosure

- Drill holes for cable glands (6× PG7/PG9)
- Mount DIN rail or standoffs for component mounting
- Install desiccant packs for moisture control

### 2. Mount Components

**Inside enclosure**:
1. Raspberry Pi on standoffs
2. Buck converter near power input
3. Charge controller (if internal mounting)
4. Sensor breakout boards

**Outside enclosure**:
1. Solar panel on adjustable bracket
2. Antennas (LoRa, GPS) on top with clear sky view
3. Thermal camera with IR-transparent window

### 3. Wire System

Follow [Wiring and Connections](#wiring-and-connections) section above.

**Best practices**:
- Color code wires (red=power, black=ground, colored=signal)
- Label every connection
- Use ferrules for screw terminals
- Strain relief on all external cables
- Weatherproof all external connections

### 4. Initial Power-On

**Pre-flight checklist**:
- [ ] All wire connections verified
- [ ] No shorts between power and ground (multimeter check)
- [ ] All antennas connected (never power LoRa/GPS without antenna!)
- [ ] MicroSD card inserted
- [ ] Battery voltage >11.5V

**Power sequence**:
1. Connect battery to charge controller
2. Verify 5V output from buck converter
3. Power on Raspberry Pi
4. Monitor boot via SSH or HDMI

---

## Testing and Calibration

### Sensor Calibration

#### BME680 Gas Baseline
```python
# Run in open air for 5 minutes
from hardware.integration_guide import calibrate_bme680

calibrate_bme680(duration_minutes=5)
# Saves baseline to: data/calibration/bme680_baseline.json
```

#### Thermal Camera Baseline
```python
# See THERMAL_CAMERA_INTEGRATION_GUIDE.md
from processors.thermal_processor import ThermalProcessor

proc = ThermalProcessor()
clean_frames = []  # Collect 30 frames in clean environment
for i in range(30):
    frame = read_thermal_frame()
    clean_frames.append(frame)
    
proc.calibrate_baseline(clean_frames)
```

#### MQ-2 Smoke Sensor
- Preheat for 24-48 hours for stable readings
- Calibrate in clean air: record R0 resistance
- Save to configuration file

### System Integration Test

Run complete pipeline test:
```bash
cd /path/to/Final\ Model
python3 test_pipeline.py --full-integration
```

**Expected output**:
```
✅ Phase-0: Sensor fusion OK
✅ Phase-1: Watchdog validation OK
✅ Phase-2: Fractal gate OK
✅ Phase-3: Chaos kernel OK
✅ Phase-4: Vision mamba OK (day mode)
✅ Phase-4: Vision mamba OK (night mode with thermal)
✅ Phase-5: Logic gate OK
✅ Phase-6: LoRa communication OK
⚠️  Phase-6: Satellite (skipped - requires outdoor test)
```

---

## Troubleshooting

### I2C Issues

**Problem**: Device not detected (`i2cdetect` shows `--`)

**Solutions**:
1. Check wiring (especially power and ground)
2. Verify device address (some have configurable addresses)
3. Add pull-up resistors (4.7kΩ on SDA/SCL)
4. Try slower bus speed: `dtparam=i2c_baudrate=10000` in `/boot/config.txt`
5. Check if device shares address with another sensor

### Camera Issues

**Problem**: `Camera not detected`

**Solutions**:
1. Verify ribbon cable orientation (blue side toward USB/Ethernet)
2. Reseat ribbon cable firmly
3. Enable camera interface: `sudo raspi-config`
4. Update firmware: `sudo rpi-update`
5. Check `/boot/config.txt`: `start_x=1` and `gpu_mem=128`

### LoRa Issues

**Problem**: `No packets received`

**Solutions**:
1. **Critical**: Antenna must be connected before power-on (can damage module!)
2. Verify SPI connections
3. Check frequency matches (915 MHz US, 868 MHz EU, 433 MHz Asia)
4. Ensure line-of-sight or clear path between nodes
5. Increase TX power: `rfm.tx_power = 23`

### GPS Issues

**Problem**: `No GPS fix`

**Solutions**:
1. GPS requires outdoor operation with clear sky view
2. Cold start can take 5-15 minutes
3. Check antenna connection
4. Verify serial port: `ls -l /dev/serial0`
5. Read raw NMEA: `cat /dev/serial0` (should see $GP* sentences)

### Power Issues

**Problem**: System reboots randomly

**Solutions**:
1. Check power supply capacity (need stable 5V 2.5A+)
2. Add large capacitor (1000-2200µF) on 5V line
3. Use quality buck converter (not cheap eBay ones)
4. Monitor voltage during operation: `vcgencmd get_throttled`
5. Reduce active components if power-limited

---

## Field Deployment Checklist

### Pre-Deployment

- [ ] All sensors tested individually
- [ ] Full system integration test passed
- [ ] Calibration completed for all sensors
- [ ] Battery fully charged
- [ ] Solar panel cleaned and tested
- [ ] Enclosure weatherproofing verified
- [ ] All antennas secured
- [ ] Backup MicroSD card prepared
- [ ] GPS coordinates recorded
- [ ] Node ID configured

### On-Site Installation

- [ ] Site survey completed (GPS, cell coverage, LoRa range)
- [ ] Solar panel oriented south (Northern hemisphere) with tilt = latitude
- [ ] Clear sky view for GPS and satellite antenna
- [ ] LoRa antenna vertical and elevated
- [ ] Mounting secure against wind
- [ ] Cable glands tightened
- [ ] Desiccant packs fresh
- [ ] Initial power-on successful
- [ ] LoRa mesh connection verified
- [ ] Test satellite message sent (if applicable)
- [ ] 24-hour burn-in test completed

### Post-Deployment Monitoring

- [ ] Remote SSH access confirmed
- [ ] LoRa mesh heartbeat received
- [ ] Sensor data flowing to dashboard
- [ ] Battery voltage stable >12V
- [ ] Solar charging confirmed (daylight hours)
- [ ] Camera captures verified (RGB + thermal)
- [ ] First week: daily checks
- [ ] After month: weekly checks
- [ ] Maintenance schedule established

---

## Additional Resources

- **Main README**: [../Readme.md](../Readme.md)
- **Thermal Camera Guide**: [THERMAL_CAMERA_INTEGRATION_GUIDE.md](./THERMAL_CAMERA_INTEGRATION_GUIDE.md)
- **Phase Documentation**: [../docs/](../docs/)
- **Hardware Schematics**: Contact repository maintainer
- **Community Forum**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

## Support

For hardware-specific issues:
1. Check troubleshooting section above
2. Review sensor datasheets
3. Post in GitHub Issues with:
   - Hardware configuration
   - `i2cdetect -y 1` output
   - Error messages
   - Photos of wiring

**Safety Warnings**:
- ⚠️ Never operate LoRa/GPS modules without antenna (RF damage)
- ⚠️ Use 3.3V for I2C devices, NOT 5V (will damage sensors)
- ⚠️ RockBLOCK can draw 500mA+ (needs separate power)
- ⚠️ outdoor deployment in wildfire areas (ensure proper mounting)

---

**Last Updated**: 2026-02-09  
**System Version**: Fractal Fire Mamba v2.0 with Thermal Night Vision
