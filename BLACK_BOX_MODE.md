# Phase-6 Communication - Black Box Mode

## Overview

When a Drone node loses LoRa connectivity to the Queen, it enters **"Black Box Mode"** - autonomous operation with local data logging for later recovery.

## Failure Scenarios

### LoRa Link Failure
- **Cause**: Queen node down, antenna damage, terrain obstruction
- **Detection**: Heartbeat ACK timeout (6 hours = 6 failed pings)
- **Response**: Enter Black Box Mode

### Queen Node Failure
- **Cause**: Hardware failure, power loss, fire destruction
- **Detection**: All Drones in sector lose heartbeat ACK
- **Response**: All Drones enter Black Box Mode independently

## Black Box Mode Behavior

### 1. Local Data Storage
```python
# When LoRa fails, save alerts to flash storage
if not lora_link_active:
    save_alert_to_local_storage({
        'timestamp': time.time(),
        'sensor_data': sensor_fusion_output,
        'vision_confidence': vision_mamba_score,
        'gps_location': gps_coords,
        'alert_level': 'CRITICAL'
    })
```

### 2. Reduced Power Mode
- Disable hourly heartbeat (saves power)
- Increase sensor polling interval: 10 min → 30 min
- Keep Vision Mamba active (fire detection is primary mission)
- Thermal camera runs at 50% duty cycle (night only)

### 3. Retry Logic
- Attempt Queen reconnection every 30 minutes
- If reconnection successful:
  - Upload buffered alerts (FIFO queue)
  - Resume normal heartbeat protocol
  - Clear local storage after confirmation

### 4. Local Alert Escalation
If fire detected in Black Box Mode:
- **Visual indicator**: Flash LED in distress pattern (SOS)
- **Audio alert**: Piezo buzzer at 1 kHz (if equipped)
- **Local storage**: Log every frame with smoke confidence >0.7

## Storage Requirements

### MicroSD Card Layout
```
/var/fractal_fire/
├── alerts/
│   ├── 2026-02-09_14-23-45_FIRE_ALERT.json
│   ├── 2026-02-09_14-25-12_FIRE_ALERT.json
│   └── ...
├── heartbeat_log.txt
└── system_health.json
```

**Capacity**: 32GB SD card stores ~50,000 alert records (~1 year of continuous fire alerts)

## Data Recovery

### Manual Recovery (Field Maintenance)
1. Remove MicroSD card from Drone node
2. Read data via laptop/field computer
3. Upload to central system via satellite link
4. Reinsert card (data auto-clears after upload)

### Automatic Recovery (Queen Restoration)
1. Queen node comes back online
2. Drones detect heartbeat ACK
3. Buffered alerts auto-upload via LoRa
4. Storage auto-clears after confirmation

## Implementation Priority

> [!NOTE]
> Black Box Mode is a **fail-safe**, not primary mode. It ensures:
> - **No data loss** even if Queen fails
> - **Mission continuity** (fire detection continues)
> - **Evidence preservation** for post-incident analysis

### Critical Design Principle
**"Drones do not speak to Satellite. If LoRa fails, Drones enter Black Box mode and save data locally."**

This is by design:
- Satellite modems cost $250 (49× Drones = $12,250 wasted)
- Satellite cost: $0.11/message (unsustainable for 49 nodes)
- Black Box Mode + field recovery is sufficient for edge cases

## Code Integration

### Communication Layer Update
```python
# phases/phase6_communication/communication_layer.py

class CommunicationLayer:
    def __init__(self, config: NodeConfig):
        self.config = config
        self.black_box_mode = False
        self.heartbeat_failures = 0
        
    def send_alert(self, message: dict):
        if self.config.is_queen:
            # Queen sends via satellite
            self.satellite.send(message)
        elif self.config.is_drone:
            if self.black_box_mode:
                # Save locally
                self.save_to_local_storage(message)
            else:
                # Try LoRa mesh
                success = self.lora.send_to_queen(message)
                if not success:
                    self.heartbeat_failures += 1
                    if self.heartbeat_failures >= 6:
                        self.enter_black_box_mode()
    
    def enter_black_box_mode(self):
        print("⚠️  LoRa link lost. Entering Black Box Mode.")
        self.black_box_mode = True
        # Disable heartbeat, reduce power
        self.heartbeat_enabled = False
```

---

**Status**: Documentation complete. Implementation in Phase-6 communication layer pending.
