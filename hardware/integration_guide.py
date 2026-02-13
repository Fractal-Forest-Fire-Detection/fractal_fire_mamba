"""
HARDWARE INTEGRATION GUIDE - PHASE 6 COMMUNICATION LAYER
Complete reference for LoRa and Satellite deployment

This guide provides step-by-step instructions for integrating:
1. LoRa mesh networking (RFM95W/SX1276)
2. Iridium satellite communication (RockBLOCK)
3. GPS module
4. Power management
"""

# ============================================================================
#  LORA MESH NETWORK INTEGRATION
# ============================================================================

"""
Hardware Requirements:
- RFM95W LoRa transceiver module (915 MHz for US, 868 MHz for EU)
- OR Adafruit LoRa Radio Bonnet
- Raspberry Pi (any model with GPIO)
- Antenna (1/4 wave whip or better)

Wiring (RFM95W to Raspberry Pi):
- VIN → 3.3V
- GND → GND
- SCK → GPIO 11 (SCLK)
- MISO → GPIO 9 (MISO)
- MOSI → GPIO 10 (MOSI)
- CS → GPIO 8 (CE0)
- RST → GPIO 25
- G0 (DIO0) → GPIO 22
"""

# Example LoRa implementation
def setup_lora_transceiver():
    """
    Initialize LoRa transceiver
    
    Returns:
        LoRa radio object
    """
    import board
    import busio
    import digitalio
    from adafruit_rfm9x import RFM9x
    
    # SPI setup
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    
    # Chip select and reset pins
    cs = digitalio.DigitalInOut(board.CE1)
    reset = digitalio.DigitalInOut(board.D25)
    
    # Initialize RFM95W
    rfm9x = RFM9x(
        spi, cs, reset,
        frequency=915.0,  # 915 MHz for US
        tx_power=23,      # Max power (20 dBm)
        baudrate=1000000
    )
    
    # Configure for mesh operation
    rfm9x.spreading_factor = 9  # Balance speed vs range
    rfm9x.coding_rate = 5       # Error correction
    rfm9x.signal_bandwidth = 125000  # 125 kHz
    
    return rfm9x


def transmit_lora_alert(rfm9x, alert_data: dict) -> bool:
    """
    Transmit alert via LoRa
    
    Args:
        rfm9x: LoRa radio object
        alert_data: Alert dictionary
    
    Returns:
        True if transmission successful
    """
    import json
    
    try:
        # Serialize to JSON (max 252 bytes)
        message = json.dumps(alert_data)
        
        if len(message) > 252:
            # Truncate if too long
            message = message[:252]
        
        # Send message
        rfm9x.send(bytes(message, 'utf-8'))
        
        print(f"📡 LoRa TX: {len(message)} bytes")
        return True
        
    except Exception as e:
        print(f"❌ LoRa TX failed: {e}")
        return False


def receive_lora_messages(rfm9x, timeout: float = 5.0):
    """
    Receive LoRa messages
    
    Args:
        rfm9x: LoRa radio object
        timeout: Receive timeout in seconds
    
    Returns:
        Received message or None
    """
    import json
    
    packet = rfm9x.receive(timeout=timeout)
    
    if packet:
        try:
            message = packet.decode('utf-8')
            data = json.loads(message)
            
            # Get signal strength
            rssi = rfm9x.last_rssi
            
            print(f"📡 LoRa RX: {len(message)} bytes, RSSI: {rssi} dBm")
            return data
            
        except Exception as e:
            print(f"❌ LoRa RX decode failed: {e}")
            return None
    
    return None


# ============================================================================
#  IRIDIUM SATELLITE INTEGRATION
# ============================================================================

"""
Hardware Requirements:
- RockBLOCK Iridium 9603 module
- Power supply (5V, 500mA peak)
- Active antenna
- Raspberry Pi UART (TX/RX)

Wiring (RockBLOCK to Raspberry Pi):
- 5V → 5V power supply (NOT Pi's 5V - insufficient current)
- GND → GND
- TX → GPIO 15 (RX)
- RX → GPIO 14 (TX)
- Sleep → GPIO 23 (optional, for power management)
- Network Available → GPIO 24 (optional, signal indicator)

CRITICAL: RockBLOCK requires up to 500mA during transmission.
Use external power supply, NOT the Pi's 5V rail.
"""

# Example Iridium implementation
def setup_rockblock():
    """
    Initialize RockBLOCK Iridium modem
    
    Returns:
        Serial connection to RockBLOCK
    """
    import serial
    import time
    
    # Open serial connection
    ser = serial.Serial(
        port='/dev/ttyS0',  # Raspberry Pi UART
        baudrate=19200,
        timeout=1
    )
    
    # Wait for modem to initialize
    time.sleep(2)
    
    # Test AT command
    ser.write(b'AT\r')
    response = ser.readline()
    
    if b'OK' in response:
        print("✅ RockBLOCK initialized")
    else:
        print("❌ RockBLOCK initialization failed")
    
    return ser


def transmit_satellite_alert(ser, alert_data: dict) -> bool:
    """
    Transmit alert via Iridium satellite
    
    Args:
        ser: Serial connection to RockBLOCK
        alert_data: Alert dictionary
    
    Returns:
        True if transmission successful
    """
    import json
    import time
    
    try:
        # Serialize to JSON (max 340 bytes for SBD)
        message = json.dumps(alert_data)
        
        if len(message) > 340:
            # Truncate if too long
            message = message[:340]
        
        # Clear mobile-originated buffer
        ser.write(b'AT+SBDD0\r')
        time.sleep(1)
        
        # Write message to buffer
        ser.write(f'AT+SBDWT={message}\r'.encode())
        time.sleep(1)
        
        # Initiate SBD session (transmit)
        print("🛰️  Initiating satellite transmission...")
        ser.write(b'AT+SBDIX\r')
        
        # Wait for response (can take 30+ seconds)
        start_time = time.time()
        while time.time() - start_time < 60:  # 60 second timeout
            response = ser.readline().decode()
            
            if '+SBDIX:' in response:
                # Parse response
                # Format: +SBDIX:<MO status>,<MOMSN>,<MT status>,<MTMSN>,<MT length>,<MTqueued>
                parts = response.split(':')[1].split(',')
                mo_status = int(parts[0])
                
                if mo_status <= 4:  # Success codes
                    print(f"✅ Satellite TX successful (status: {mo_status})")
                    return True
                else:
                    print(f"❌ Satellite TX failed (status: {mo_status})")
                    return False
        
        print("❌ Satellite TX timeout")
        return False
        
    except Exception as e:
        print(f"❌ Satellite TX error: {e}")
        return False


def get_satellite_signal_quality(ser) -> int:
    """
    Get satellite signal quality (0-5 bars)
    
    Args:
        ser: Serial connection to RockBLOCK
    
    Returns:
        Signal quality (0-5)
    """
    import time
    
    ser.write(b'AT+CSQF\r')
    time.sleep(1)
    
    response = ser.readline().decode()
    
    if '+CSQF:' in response:
        # Format: +CSQF:<quality>
        quality = int(response.split(':')[1].strip())
        print(f"🛰️  Signal quality: {quality}/5 bars")
        return quality
    
    return 0


# ============================================================================
#  GPS MODULE INTEGRATION
# ============================================================================

"""
Hardware Requirements:
- GPS module (e.g., Adafruit Ultimate GPS, u-blox NEO-6M)
- Raspberry Pi UART or USB
- Active antenna (for best results)

Wiring (GPS to Raspberry Pi):
- VIN → 3.3V or 5V (check module specs)
- GND → GND
- TX → GPIO 15 (RX) - if using UART
- RX → GPIO 14 (TX) - if using UART

Alternative: USB GPS dongle (simpler, no wiring)
"""

# Example GPS implementation
def setup_gps():
    """
    Initialize GPS module
    
    Returns:
        GPS serial connection
    """
    import serial
    
    # For UART GPS
    gps_serial = serial.Serial(
        port='/dev/ttyAMA0',  # Raspberry Pi UART
        baudrate=9600,
        timeout=1
    )
    
    return gps_serial


def get_gps_location(gps_serial) -> tuple:
    """
    Get current GPS coordinates
    
    Args:
        gps_serial: GPS serial connection
    
    Returns:
        (latitude, longitude, altitude) or (None, None, None)
    """
    import pynmea2
    
    try:
        line = gps_serial.readline().decode('ascii', errors='ignore')
        
        if line.startswith('$GPGGA'):
            msg = pynmea2.parse(line)
            
            if msg.latitude and msg.longitude:
                return (
                    msg.latitude,
                    msg.longitude,
                    msg.altitude
                )
        
    except Exception as e:
        print(f"GPS read error: {e}")
    
    return (None, None, None)


# ============================================================================
#  POWER MANAGEMENT
# ============================================================================

"""
Power Budget:
- Raspberry Pi Zero W: ~150 mA
- LoRa RFM95W (RX): ~10 mA
- LoRa RFM95W (TX): ~120 mA
- RockBLOCK (idle): ~30 mA
- RockBLOCK (TX): ~500 mA
- GPS module: ~30 mA
- Sensors: ~50 mA (total)
- Camera (when active): ~200 mA

Total (worst case): ~1050 mA

Battery Options:
1. 18650 Li-ion (3000 mAh) = ~3 hours continuous
2. 6x AA NiMH (12000 mAh) = ~12 hours continuous
3. 10000 mAh power bank = ~10 hours continuous
4. Solar + 12V SLA battery = indefinite (with proper sizing)

Recommended: Solar + 20Ah 12V SLA + charge controller
"""

def setup_power_management():
    """
    Configure power-saving features
    """
    import RPi.GPIO as GPIO
    
    # Setup GPIO for power control
    GPIO.setmode(GPIO.BCM)
    
    # Define power control pins
    LORA_POWER_PIN = 17
    GPS_POWER_PIN = 27
    CAMERA_POWER_PIN = 22
    SATELLITE_POWER_PIN = 23
    
    # Configure as outputs
    GPIO.setup(LORA_POWER_PIN, GPIO.OUT)
    GPIO.setup(GPS_POWER_PIN, GPIO.OUT)
    GPIO.setup(CAMERA_POWER_PIN, GPIO.OUT)
    GPIO.setup(SATELLITE_POWER_PIN, GPIO.OUT)
    
    return {
        'lora': LORA_POWER_PIN,
        'gps': GPS_POWER_PIN,
        'camera': CAMERA_POWER_PIN,
        'satellite': SATELLITE_POWER_PIN
    }


def enable_module(power_pins: dict, module: str):
    """
    Enable power to a module
    
    Args:
        power_pins: Dictionary of power control pins
        module: Module name ('lora', 'gps', 'camera', 'satellite')
    """
    import RPi.GPIO as GPIO
    
    if module in power_pins:
        GPIO.output(power_pins[module], GPIO.HIGH)
        print(f"⚡ {module.upper()} powered ON")


def disable_module(power_pins: dict, module: str):
    """
    Disable power to a module
    
    Args:
        power_pins: Dictionary of power control pins
        module: Module name
    """
    import RPi.GPIO as GPIO
    
    if module in power_pins:
        GPIO.output(power_pins[module], GPIO.LOW)
        print(f"💤 {module.upper()} powered OFF")


# ============================================================================
#  COMPLETE INTEGRATION EXAMPLE
# ============================================================================

def deploy_complete_hardware_system():
    """
    Example of complete hardware integration
    """
    from phase6_communication_layer import (
        Phase6CommunicationLayer,
        GPSCoordinate,
        FireAlert,
        AlertPriority,
        NetworkChannel
    )
    import time
    
    print("\n🚀 Deploying Complete Hardware System")
    print("="*70)
    
    # 1. Initialize GPS
    print("\n📍 Initializing GPS...")
    gps = setup_gps()
    
    # Get initial location
    lat, lon, alt = get_gps_location(gps)
    while lat is None:
        print("Waiting for GPS fix...")
        time.sleep(2)
        lat, lon, alt = get_gps_location(gps)
    
    location = GPSCoordinate(latitude=lat, longitude=lon, altitude=alt)
    print(f"✅ GPS Location: {lat:.4f}, {lon:.4f}, {alt:.1f}m")
    
    # 2. Initialize LoRa
    print("\n📡 Initializing LoRa...")
    lora = setup_lora_transceiver()
    print("✅ LoRa ready")
    
    # 3. Initialize Satellite
    print("\n🛰️  Initializing RockBLOCK...")
    satellite = setup_rockblock()
    
    # Check signal quality
    signal = get_satellite_signal_quality(satellite)
    if signal >= 2:
        print(f"✅ Satellite ready (signal: {signal}/5)")
    else:
        print(f"⚠️  Weak satellite signal: {signal}/5")
    
    # 4. Initialize Communication Layer
    print("\n📞 Initializing Phase-6...")
    comm = Phase6CommunicationLayer(
        node_id="PROD_NODE_001",
        location=location
    )
    print("✅ Phase-6 ready")
    
    # 5. Test alert transmission
    print("\n🧪 Testing alert transmission...")
    
    test_alert = FireAlert(
        alert_id="TEST_001",
        priority=AlertPriority.P2_MEDIUM,
        node_id="PROD_NODE_001",
        location=location,
        risk_score=0.65,
        confidence=0.70,
        witnesses=0,
        channel=NetworkChannel.LORA_MESH
    )
    
    # Try LoRa
    print("\n📡 Testing LoRa transmission...")
    success = transmit_lora_alert(lora, test_alert.to_dict())
    
    if success:
        print("✅ LoRa test successful")
    else:
        print("❌ LoRa test failed")
    
    print("\n🎯 Hardware system ready for deployment!")
    print("="*70)


# ============================================================================
#  DEPLOYMENT CHECKLIST
# ============================================================================

"""
PRE-DEPLOYMENT CHECKLIST:

Hardware:
☐ Raspberry Pi configured and tested
☐ LoRa module wired and tested (range test performed)
☐ RockBLOCK wired with external power supply
☐ GPS module getting reliable fix
☐ All sensors calibrated
☐ Power system tested (battery + solar if applicable)
☐ Enclosure weatherproof and mounted securely
☐ Antenna properly installed (LoRa + satellite + GPS)

Software:
☐ All Python dependencies installed
☐ Phase 0-6 modules tested individually
☐ Integrated system tested
☐ Logging configured
☐ Auto-start on boot configured
☐ Watchdog timer configured (auto-restart on crash)

Network:
☐ LoRa frequency configured correctly (915 MHz US / 868 MHz EU)
☐ LoRa mesh tested with neighbor nodes
☐ Satellite account activated and funded
☐ Satellite test message sent and received
☐ Network fallback tested

Field Testing:
☐ System tested in actual deployment location
☐ GPS coordinates verified
☐ Signal strength measured (LoRa + satellite)
☐ Power consumption measured
☐ Temperature range tested
☐ Emergency scenarios tested (dying gasp, etc.)

Documentation:
☐ Node ID and location documented
☐ MAC addresses recorded
☐ Encryption keys backed up
☐ Contact information for alerts configured
☐ Maintenance schedule created

READY FOR DEPLOYMENT: ☐
"""

if __name__ == "__main__":
    print(__doc__)
    
    print("\n" + "="*70)
    print("HARDWARE INTEGRATION GUIDE")
    print("="*70)
    print("\nThis guide provides code examples for:")
    print("  1. LoRa mesh networking (RFM95W)")
    print("  2. Iridium satellite (RockBLOCK)")
    print("  3. GPS module")
    print("  4. Power management")
    print("\nFor deployment, run:")
    print("  deploy_complete_hardware_system()")
    print("="*70)
