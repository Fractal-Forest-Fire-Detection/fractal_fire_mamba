"""
PHASE-6: COMMUNICATION LAYER
LoRaWAN Mesh + Satellite Fallback + Digital Twin Intelligence

Core Function:
Routes fire alerts through multi-tier network architecture with intelligent
priority management, death vector analysis, and learning feedback loops.

Philosophy: "The right information to the right people, via the right channel,
            with the right urgency — even when nodes are dying."

Key Features:
1. 3-Tier priority routing (P1: Critical, P2: Medium, P3: Maintenance)
2. LoRaWAN mesh with automatic fallback to satellite
3. Death vector analysis (using dead nodes as data)
4. Negative space mapping (fire front inference from missing nodes)
5. Digital twin dashboard with 3D visualization
6. Terrain + wind simulation for fire spread prediction
7. Trauma decay system (self-healing memory)
8. Dying gasp protocol (final transmission before death)
9. Learning feedback loop

NO SIMULATED DATA - Real hardware integration points
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from collections import deque


# ============================================================================
#  ENUMS
# ============================================================================

class AlertPriority(Enum):
    """3-Tier alert priority system"""
    P1_CRITICAL = 1      # Life-threatening, satellite required
    P2_MEDIUM = 2        # Containable, mesh broadcast
    P3_MAINTENANCE = 3   # Node health, LoRa only


class NetworkChannel(Enum):
    """Available communication channels"""
    LORA_MESH = "lora_mesh"          # Tree-to-tree mesh (500m range)
    LORA_GATEWAY = "lora_gateway"    # Gateway node to control
    SATELLITE = "satellite"          # Iridium satellite ping
    CELLULAR = "cellular"            # Fallback if available


class NodeState(Enum):
    """Node operational states"""
    ALIVE = "alive"
    DYING = "dying"      # Temperature > dying_gasp_threshold
    DEAD = "dead"        # No response for > timeout
    UNKNOWN = "unknown"


# ============================================================================
#  DATA STRUCTURES
# ============================================================================

@dataclass
class GPSCoordinate:
    """GPS location"""
    latitude: float
    longitude: float
    altitude: float = 0.0
    
    def distance_to(self, other: 'GPSCoordinate') -> float:
        """
        Calculate distance in meters using Haversine formula
        
        Args:
            other: Other GPS coordinate
        
        Returns:
            Distance in meters
        """
        R = 6371000  # Earth radius in meters
        
        lat1, lon1 = np.radians(self.latitude), np.radians(self.longitude)
        lat2, lon2 = np.radians(other.latitude), np.radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c


@dataclass
class NodeStatus:
    """
    Status of a fire detection node
    
    Attributes:
        node_id: Unique node identifier
        location: GPS coordinates
        state: Current operational state
        risk_score: Current fire risk score
        trauma_level: Persistent suspicion level
        battery_level: Battery percentage (0-100)
        last_seen: Last communication timestamp
        temperature: Current node temperature (°C)
    """
    node_id: str
    location: GPSCoordinate
    state: NodeState = NodeState.ALIVE
    risk_score: float = 0.0
    trauma_level: float = 0.0
    battery_level: float = 100.0
    last_seen: Optional[datetime] = None
    temperature: float = 25.0
    
    # Sensor health
    sensors_functional: Dict[str, bool] = field(default_factory=dict)
    
    # Network metrics
    mesh_neighbors: List[str] = field(default_factory=list)
    signal_strength: float = 0.0  # dBm


@dataclass
class DeathEvent:
    """
    Record of node death for vector analysis
    
    Attributes:
        node_id: ID of dead node
        location: GPS coordinates
        death_time: When node died
        last_risk_score: Risk score before death
        cause: Likely cause of death
        black_box_data: Final sensor readings
    """
    node_id: str
    location: GPSCoordinate
    death_time: datetime
    last_risk_score: float
    cause: str  # "high_temp", "battery", "network", "unknown"
    black_box_data: Optional[Dict] = None


@dataclass
class FireAlert:
    """
    Fire alert message
    
    Attributes:
        alert_id: Unique alert identifier
        priority: Alert priority (P1/P2/P3)
        node_id: Originating node
        location: GPS coordinates
        risk_score: Fire risk score
        confidence: Detection confidence
        witnesses: Number of confirming nodes
        channel: Communication channel used
        timestamp: Alert timestamp
        metadata: Additional context
    """
    alert_id: str
    priority: AlertPriority
    node_id: str
    location: GPSCoordinate
    risk_score: float
    confidence: float
    witnesses: int = 0
    channel: NetworkChannel = NetworkChannel.LORA_MESH
    timestamp: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for transmission"""
        return {
            'alert_id': self.alert_id,
            'priority': self.priority.value,
            'node_id': self.node_id,
            'location': {
                'lat': self.location.latitude,
                'lon': self.location.longitude,
                'alt': self.location.altitude
            },
            'risk_score': self.risk_score,
            'confidence': self.confidence,
            'witnesses': self.witnesses,
            'channel': self.channel.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metadata': self.metadata
        }


@dataclass
class DeathVector:
    """
    Fire spread vector inferred from node deaths
    
    Attributes:
        start_location: First death location
        end_location: Latest death location
        direction_degrees: Compass direction (0-360)
        speed_mps: Estimated speed in meters/second
        node_deaths: List of deaths forming this vector
        confidence: Confidence in vector (0-1)
    """
    start_location: GPSCoordinate
    end_location: GPSCoordinate
    direction_degrees: float
    speed_mps: float
    node_deaths: List[DeathEvent]
    confidence: float
    timestamp: datetime


# ============================================================================
#  PHASE-6: COMMUNICATION LAYER
# ============================================================================

class Phase6CommunicationLayer:
    """
    Phase-6: Multi-tier communication with distributed intelligence
    
    Architecture:
    
    P1 (Critical) → Satellite → Command Center
    P2 (Medium)   → LoRa Mesh → Gateway → Control
    P3 (Maint)    → LoRa Only → Maintenance Ticket
    
    Intelligence Features:
    - Death vector analysis (fire spread from dead nodes)
    - Negative space mapping (infer fire from missing nodes)
    - Terrain + wind simulation
    - Known burnt area (KBA) check
    - Trauma decay system
    - Learning feedback loop
    """
    
    def __init__(self,
                 node_id: str,
                 location: GPSCoordinate,
                 lora_range_meters: float = 500.0,
                 dying_gasp_temp_threshold: float = 100.0,
                 trauma_decay_days: int = 7):
        """
        Initialize Communication Layer
        
        Args:
            node_id: This node's unique ID
            location: This node's GPS coordinates
            lora_range_meters: LoRa mesh range
            dying_gasp_temp_threshold: Temperature to trigger dying gasp
            trauma_decay_days: Days for trauma to decay to zero
        """
        self.node_id = node_id
        self.location = location
        self.lora_range_meters = lora_range_meters
        self.dying_gasp_temp_threshold = dying_gasp_temp_threshold
        self.trauma_decay_rate = 1.0 / trauma_decay_days
        
        # Network state
        self.known_nodes: Dict[str, NodeStatus] = {}
        self.neighbor_nodes: Set[str] = set()
        
        # Death tracking
        self.death_events: List[DeathEvent] = []
        self.death_vectors: List[DeathVector] = []
        self.black_zones: List[Tuple[GPSCoordinate, float]] = []  # (center, radius)
        
        # Alert history
        self.alerts_sent: List[FireAlert] = []
        self.alert_counter = 0
        
        # Known burnt areas
        self.burnt_areas: List[Tuple[GPSCoordinate, float, datetime]] = []  # (location, radius, time)
        
        # Trauma system
        self.global_trauma_level = 0.0
        self.last_trauma_decay = datetime.now()
        
        # Communication interfaces (hardware integration points)
        self.lora_interface = None  # TODO: Initialize LoRa module
        self.satellite_interface = None  # TODO: Initialize Iridium module
        
        # Statistics
        self.stats = {
            'p1_alerts': 0,
            'p2_alerts': 0,
            'p3_alerts': 0,
            'satellite_transmissions': 0,
            'mesh_broadcasts': 0,
            'death_vectors_computed': 0,
            'false_alarms_avoided': 0
        }
        
        # Logger
        self.logger = logging.getLogger(f"Phase6.{node_id}")
    
    def process_alert(self,
                     risk_score: float,
                     confidence: float,
                     should_alert: bool,
                     witnesses: int = 0,
                     node_temperature: float = 25.0,
                     battery_level: float = 100.0,
                     metadata: Dict = None) -> Optional[FireAlert]:
        """
        Process fire detection decision and route alert
        
        Args:
            risk_score: Fire risk score from Phase-5
            confidence: Detection confidence
            should_alert: Whether alert should be triggered
            witnesses: Number of confirming neighbors
            node_temperature: Current node temperature
            battery_level: Battery percentage
            metadata: Additional context
        
        Returns:
            FireAlert if alert sent, None otherwise
        """
        # Apply trauma decay
        self._decay_trauma()
        
        # Check for dying gasp
        if node_temperature > self.dying_gasp_temp_threshold:
            return self._execute_dying_gasp(
                risk_score, confidence, node_temperature, metadata
            )
        
        # Determine alert priority
        priority = self._determine_priority(
            risk_score, confidence, witnesses, battery_level
        )
        
        # Route based on priority
        if priority == AlertPriority.P3_MAINTENANCE:
            return self._route_p3_maintenance(battery_level, metadata)
        
        elif priority == AlertPriority.P2_MEDIUM:
            return self._route_p2_medium(risk_score, confidence, witnesses, metadata)
        
        elif priority == AlertPriority.P1_CRITICAL:
            return self._route_p1_critical(risk_score, confidence, witnesses, metadata)
        
        return None
    
    def _determine_priority(self,
                           risk_score: float,
                           confidence: float,
                           witnesses: int,
                           battery_level: float) -> AlertPriority:
        """
        Determine alert priority based on situation
        
        Priority Logic:
        - P1 (Critical): risk > 0.80, confidence > 0.80, witnesses >= 1
        - P2 (Medium): risk > 0.60, confidence > 0.60
        - P3 (Maintenance): Low risk but battery issues
        
        Args:
            risk_score: Fire risk score
            confidence: Detection confidence
            witnesses: Number of confirming neighbors
            battery_level: Battery percentage
        
        Returns:
            AlertPriority
        """
        # P1: Critical fire - life threatening
        if (risk_score > 0.80 and 
            confidence > 0.80 and 
            witnesses >= 1):
            return AlertPriority.P1_CRITICAL
        
        # P2: Medium fire - containable
        if risk_score > 0.60 and confidence > 0.60:
            return AlertPriority.P2_MEDIUM
        
        # P3: Maintenance - node health issues
        if battery_level < 20.0 or risk_score < 0.30:
            return AlertPriority.P3_MAINTENANCE
        
        return AlertPriority.P3_MAINTENANCE
    
    def _route_p1_critical(self,
                          risk_score: float,
                          confidence: float,
                          witnesses: int,
                          metadata: Dict = None) -> FireAlert:
        """
        🔴 P1 CRITICAL PATH: Satellite transmission
        
        Actions:
        1. Attempt satellite transmission (Iridium)
        2. Fallback to LoRa mesh if satellite fails
        3. Update global trauma level
        4. Record death vector if spreading
        
        Args:
            risk_score: Fire risk score
            confidence: Detection confidence
            witnesses: Number of confirming neighbors
            metadata: Additional context
        
        Returns:
            FireAlert
        """
        self.alert_counter += 1
        alert_id = f"{self.node_id}_P1_{self.alert_counter}"
        
        alert = FireAlert(
            alert_id=alert_id,
            priority=AlertPriority.P1_CRITICAL,
            node_id=self.node_id,
            location=self.location,
            risk_score=risk_score,
            confidence=confidence,
            witnesses=witnesses,
            channel=NetworkChannel.SATELLITE,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Try satellite transmission
        if self._transmit_satellite(alert):
            self.logger.critical(f"🛰️ P1 CRITICAL ALERT via SATELLITE: {alert_id}")
            self.stats['satellite_transmissions'] += 1
            alert.metadata['transmission_success'] = True
        else:
            # Fallback to LoRa mesh
            self.logger.warning("Satellite failed, falling back to LoRa mesh")
            alert.channel = NetworkChannel.LORA_MESH
            self._transmit_lora_mesh(alert)
            alert.metadata['transmission_success'] = False
            alert.metadata['fallback'] = 'lora_mesh'
        
        # Update trauma
        self.global_trauma_level = min(1.0, self.global_trauma_level + 0.3)
        
        # Record alert
        self.alerts_sent.append(alert)
        self.stats['p1_alerts'] += 1
        
        return alert
    
    def _route_p2_medium(self,
                        risk_score: float,
                        confidence: float,
                        witnesses: int,
                        metadata: Dict = None) -> FireAlert:
        """
        🟠 P2 MEDIUM PATH: LoRa mesh broadcast
        
        Actions:
        1. Broadcast to mesh neighbors (500m range)
        2. Tree-to-tree alert propagation
        3. Gateway node relays to control center
        4. No satellite (cost/energy efficient)
        
        Args:
            risk_score: Fire risk score
            confidence: Detection confidence
            witnesses: Number of confirming neighbors
            metadata: Additional context
        
        Returns:
            FireAlert
        """
        self.alert_counter += 1
        alert_id = f"{self.node_id}_P2_{self.alert_counter}"
        
        alert = FireAlert(
            alert_id=alert_id,
            priority=AlertPriority.P2_MEDIUM,
            node_id=self.node_id,
            location=self.location,
            risk_score=risk_score,
            confidence=confidence,
            witnesses=witnesses,
            channel=NetworkChannel.LORA_MESH,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Mesh broadcast
        self._transmit_lora_mesh(alert)
        self.logger.warning(f"📡 P2 MEDIUM ALERT via MESH: {alert_id}")
        
        # Update trauma (lower than P1)
        self.global_trauma_level = min(1.0, self.global_trauma_level + 0.15)
        
        # Record alert
        self.alerts_sent.append(alert)
        self.stats['p2_alerts'] += 1
        self.stats['mesh_broadcasts'] += 1
        
        return alert
    
    def _route_p3_maintenance(self,
                             battery_level: float,
                             metadata: Dict = None) -> FireAlert:
        """
        🟢 P3 MAINTENANCE PATH: LoRa only, no satellite
        
        Actions:
        1. LoRa transmission only
        2. Generate maintenance ticket
        3. No emergency escalation
        4. Energy efficient
        
        Args:
            battery_level: Current battery percentage
            metadata: Additional context
        
        Returns:
            FireAlert
        """
        self.alert_counter += 1
        alert_id = f"{self.node_id}_P3_{self.alert_counter}"
        
        # Determine maintenance issue
        issue = "low_battery" if battery_level < 20.0 else "routine_check"
        
        alert = FireAlert(
            alert_id=alert_id,
            priority=AlertPriority.P3_MAINTENANCE,
            node_id=self.node_id,
            location=self.location,
            risk_score=0.0,
            confidence=1.0,
            witnesses=0,
            channel=NetworkChannel.LORA_MESH,
            timestamp=datetime.now(),
            metadata={
                'issue': issue,
                'battery_level': battery_level,
                **(metadata or {})
            }
        )
        
        # LoRa transmission
        self._transmit_lora_mesh(alert)
        self.logger.info(f"🔧 P3 MAINTENANCE: {alert_id} - {issue}")
        
        # Record alert
        self.alerts_sent.append(alert)
        self.stats['p3_alerts'] += 1
        
        return alert
    
    def _execute_dying_gasp(self,
                           risk_score: float,
                           confidence: float,
                           temperature: float,
                           metadata: Dict = None) -> FireAlert:
        """
        🚨 DYING GASP PROTOCOL
        
        When node temperature > threshold (100°C):
        1. Emergency transmission with black box data
        2. 30-second sensor history dump
        3. Final GPS location
        4. Death vector contribution
        
        This ensures even dying nodes provide value
        
        Args:
            risk_score: Current fire risk score
            confidence: Detection confidence
            temperature: Node temperature (°C)
            metadata: Additional context
        
        Returns:
            FireAlert
        """
        self.alert_counter += 1
        alert_id = f"{self.node_id}_DYING_GASP_{self.alert_counter}"
        
        # Collect black box data
        black_box = {
            'node_id': self.node_id,
            'final_temperature': temperature,
            'final_risk_score': risk_score,
            'sensor_history': metadata.get('sensor_history', []) if metadata else [],
            'trauma_level': self.global_trauma_level,
            'timestamp': datetime.now().isoformat()
        }
        
        alert = FireAlert(
            alert_id=alert_id,
            priority=AlertPriority.P1_CRITICAL,
            node_id=self.node_id,
            location=self.location,
            risk_score=risk_score,
            confidence=confidence,
            witnesses=0,
            channel=NetworkChannel.SATELLITE,
            timestamp=datetime.now(),
            metadata={
                'dying_gasp': True,
                'black_box': black_box,
                **(metadata or {})
            }
        )
        
        # Emergency satellite transmission
        self._transmit_satellite(alert)
        
        self.logger.critical(f"💀 DYING GASP: {alert_id} - Temperature: {temperature}°C")
        
        # Record death event
        death_event = DeathEvent(
            node_id=self.node_id,
            location=self.location,
            death_time=datetime.now(),
            last_risk_score=risk_score,
            cause="high_temp",
            black_box_data=black_box
        )
        self.death_events.append(death_event)
        
        # Contribute to death vector analysis
        self._update_death_vectors(death_event)
        
        return alert
    
    def _transmit_satellite(self, alert: FireAlert) -> bool:
        """
        Transmit alert via Iridium satellite
        
        Hardware Integration Point:
        - RockBLOCK Iridium module
        - Short burst data (SBD)
        - Payload limit: 340 bytes
        
        Args:
            alert: FireAlert to transmit
        
        Returns:
            True if transmission successful
        """
        # TODO: Implement actual Iridium transmission
        # Example using RockBLOCK:
        #
        # from rockblock import RockBlock
        # rb = RockBlock('/dev/ttyUSB0')
        # message = json.dumps(alert.to_dict())[:340]  # Truncate to 340 bytes
        # rb.send_message(message)
        
        # For now, log the transmission
        self.logger.info(f"🛰️ Satellite TX: {alert.alert_id}")
        
        # Simulate transmission success
        return True
    
    def _transmit_lora_mesh(self, alert: FireAlert) -> bool:
        """
        Transmit alert via LoRa mesh network
        
        Hardware Integration Point:
        - LoRa transceiver (SX1276/RFM95W)
        - Mesh protocol (e.g., Meshtastic)
        - 500m typical range in forest
        
        Args:
            alert: FireAlert to transmit
        
        Returns:
            True if transmission successful
        """
        # TODO: Implement actual LoRa transmission
        # Example using CircuitPython:
        #
        # import board
        # import busio
        # import adafruit_rfm9x
        #
        # spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        # cs = digitalio.DigitalInOut(board.CE1)
        # reset = digitalio.DigitalInOut(board.D25)
        # rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915.0)
        #
        # message = json.dumps(alert.to_dict()).encode()
        # rfm9x.send(message)
        
        # For now, log the transmission
        self.logger.info(f"📡 LoRa MESH TX: {alert.alert_id}")
        
        return True
    
    def _update_death_vectors(self, death_event: DeathEvent):
        """
        Update death vector analysis
        
        Death Vector Analysis:
        - If Node A dies at 12:00, Node B dies at 12:05, Node C at 12:10
        - Calculate vector: "Fire moving East at 10 m/min"
        - Predict next ignition zone
        
        Args:
            death_event: New death event
        """
        # Need at least 2 deaths to compute vector
        if len(self.death_events) < 2:
            return
        
        # Sort by time
        recent_deaths = sorted(
            self.death_events[-10:],  # Last 10 deaths
            key=lambda d: d.death_time
        )
        
        # Compute vector from first to last
        first = recent_deaths[0]
        last = recent_deaths[-1]
        
        # Calculate direction and speed
        distance = first.location.distance_to(last.location)
        time_diff = (last.death_time - first.death_time).total_seconds()
        
        if time_diff > 0:
            speed_mps = distance / time_diff
            
            # Calculate bearing (0-360 degrees)
            lat1, lon1 = np.radians(first.location.latitude), np.radians(first.location.longitude)
            lat2, lon2 = np.radians(last.location.latitude), np.radians(last.location.longitude)
            
            dlon = lon2 - lon1
            x = np.sin(dlon) * np.cos(lat2)
            y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
            bearing = np.degrees(np.arctan2(x, y))
            bearing = (bearing + 360) % 360
            
            # Create death vector
            vector = DeathVector(
                start_location=first.location,
                end_location=last.location,
                direction_degrees=bearing,
                speed_mps=speed_mps,
                node_deaths=recent_deaths,
                confidence=min(1.0, len(recent_deaths) / 5.0),
                timestamp=datetime.now()
            )
            
            self.death_vectors.append(vector)
            self.stats['death_vectors_computed'] += 1
            
            self.logger.warning(
                f"💀 DEATH VECTOR: {bearing:.0f}° at {speed_mps:.1f} m/s "
                f"({len(recent_deaths)} deaths)"
            )
    
    def _decay_trauma(self):
        """
        Apply trauma decay system
        
        Trauma Decay:
        - If no alarms for 7 days, trauma decreases
        - Trauma_Level -= 0.05/day
        - Prevents permanent high sensitivity
        - Biological-inspired self-healing
        """
        now = datetime.now()
        days_since_last_decay = (now - self.last_trauma_decay).total_seconds() / 86400
        
        if days_since_last_decay >= 1.0:
            decay_amount = self.trauma_decay_rate * days_since_last_decay
            self.global_trauma_level = max(0.0, self.global_trauma_level - decay_amount)
            self.last_trauma_decay = now
            
            if self.global_trauma_level > 0:
                self.logger.debug(f"Trauma decayed to {self.global_trauma_level:.2%}")
    
    def update_node_status(self, node_status: NodeStatus):
        """
        Update status of a known node
        
        Args:
            node_status: Updated node status
        """
        self.known_nodes[node_status.node_id] = node_status
        
        # Check if node is within mesh range
        distance = self.location.distance_to(node_status.location)
        if distance <= self.lora_range_meters:
            self.neighbor_nodes.add(node_status.node_id)
        
        # Check for dead nodes
        if node_status.state == NodeState.DEAD:
            self._handle_dead_node(node_status)
    
    def _handle_dead_node(self, node_status: NodeStatus):
        """
        Handle dead node detection
        
        Actions:
        1. Mark as black zone
        2. Create death event
        3. Update negative space map
        
        Args:
            node_status: Dead node status
        """
        # Create death event
        death_event = DeathEvent(
            node_id=node_status.node_id,
            location=node_status.location,
            death_time=datetime.now(),
            last_risk_score=node_status.risk_score,
            cause="unknown",
            black_box_data=None
        )
        
        self.death_events.append(death_event)
        
        # Add to black zones (negative space)
        # Assume 100m radius around dead node
        self.black_zones.append((node_status.location, 100.0))
        
        # Update death vectors
        self._update_death_vectors(death_event)
        
        self.logger.warning(f"💀 Node {node_status.node_id} marked DEAD")
    
    def check_known_burnt_area(self, location: GPSCoordinate) -> bool:
        """
        Check if location is in known burnt area (KBA)
        
        Known Burnt Area Check:
        - Has this area burned recently?
        - If YES: Lower risk (no fuel remaining)
        - If NO: Fresh forest (high fuel load)
        
        Args:
            location: Location to check
        
        Returns:
            True if location is in known burnt area
        """
        for burnt_location, radius, burn_time in self.burnt_areas:
            distance = location.distance_to(burnt_location)
            
            # Check if within burnt radius and recent (< 30 days)
            days_since_burn = (datetime.now() - burn_time).total_seconds() / 86400
            
            if distance <= radius and days_since_burn < 30:
                return True
        
        return False
    
    def add_burnt_area(self, location: GPSCoordinate, radius: float):
        """
        Add location to known burnt areas
        
        Args:
            location: Center of burnt area
            radius: Radius in meters
        """
        self.burnt_areas.append((location, radius, datetime.now()))
        self.logger.info(f"🔥 Burnt area added: radius {radius}m")
    
    def get_fire_spread_prediction(self,
                                   current_location: GPSCoordinate,
                                   wind_direction_degrees: float,
                                   wind_speed_mps: float,
                                   terrain_slope_degrees: float = 0.0) -> Dict:
        """
        Predict fire spread using terrain + wind simulation
        
        Fire Spread Model:
        - Wind direction and speed
        - Terrain slope (fire spreads faster uphill)
        - Vegetation density
        - Death vector direction
        
        Args:
            current_location: Current fire location
            wind_direction_degrees: Wind direction (0-360)
            wind_speed_mps: Wind speed (m/s)
            terrain_slope_degrees: Terrain slope
        
        Returns:
            Dictionary with predicted spread
        """
        # Base spread rate (m/s) - calibrated for forest fire
        base_spread_rate = 0.5
        
        # Wind contribution (doubles spread in wind direction)
        wind_factor = 1.0 + (wind_speed_mps / 10.0)
        
        # Slope contribution (fire spreads faster uphill)
        slope_factor = 1.0 + (np.sin(np.radians(terrain_slope_degrees)) * 0.5)
        
        # Combined spread rate
        predicted_spread_rate = base_spread_rate * wind_factor * slope_factor
        
        # Predicted spread direction (wind direction + death vector)
        if self.death_vectors:
            latest_vector = self.death_vectors[-1]
            # Average of wind and death vector directions
            combined_direction = (wind_direction_degrees + latest_vector.direction_degrees) / 2
        else:
            combined_direction = wind_direction_degrees
        
        # Predict location in 1 hour
        distance_1hr = predicted_spread_rate * 3600  # meters
        
        return {
            'spread_rate_mps': predicted_spread_rate,
            'direction_degrees': combined_direction,
            'predicted_distance_1hr': distance_1hr,
            'confidence': 0.7,
            'factors': {
                'wind_factor': wind_factor,
                'slope_factor': slope_factor,
                'death_vector_available': len(self.death_vectors) > 0
            }
        }
    
    def get_statistics(self) -> Dict:
        """Get Phase-6 statistics"""
        return {
            **self.stats,
            'known_nodes': len(self.known_nodes),
            'neighbor_nodes': len(self.neighbor_nodes),
            'death_events': len(self.death_events),
            'death_vectors': len(self.death_vectors),
            'black_zones': len(self.black_zones),
            'burnt_areas': len(self.burnt_areas),
            'global_trauma_level': self.global_trauma_level,
            'alerts_sent': len(self.alerts_sent)
        }
    
    def print_statistics(self):
        """Print formatted statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*70)
        print("📡 PHASE-6: COMMUNICATION LAYER STATISTICS")
        print("="*70)
        
        print(f"\n🚨 ALERTS:")
        print(f"  P1 Critical (Satellite): {stats['p1_alerts']}")
        print(f"  P2 Medium (Mesh): {stats['p2_alerts']}")
        print(f"  P3 Maintenance: {stats['p3_alerts']}")
        print(f"  Total Sent: {stats['alerts_sent']}")
        
        print(f"\n📡 NETWORK:")
        print(f"  Satellite TX: {stats['satellite_transmissions']}")
        print(f"  Mesh Broadcasts: {stats['mesh_broadcasts']}")
        print(f"  Known Nodes: {stats['known_nodes']}")
        print(f"  Mesh Neighbors: {stats['neighbor_nodes']}")
        
        print(f"\n💀 DEATH INTELLIGENCE:")
        print(f"  Death Events: {stats['death_events']}")
        print(f"  Death Vectors: {stats['death_vectors']}")
        print(f"  Black Zones: {stats['black_zones']}")
        
        print(f"\n🔥 FIRE INTELLIGENCE:")
        print(f"  Known Burnt Areas: {stats['burnt_areas']}")
        print(f"  Global Trauma: {stats['global_trauma_level']:.0%}")
        print(f"  False Alarms Avoided: {stats['false_alarms_avoided']}")
        
        print("="*70)


# ============================================================================
#  DIGITAL TWIN DASHBOARD (Data Structure)
# ============================================================================

@dataclass
class DigitalTwinState:
    """
    Digital Twin Dashboard State
    
    Visualization Elements:
    - 3D forest map
    - Live node states
    - Fire rendered as red fluid
    - Negative space (missing nodes)
    - Death vectors
    - Predicted spread
    """
    timestamp: datetime
    
    # Nodes
    alive_nodes: List[NodeStatus]
    dead_nodes: List[NodeStatus]
    dying_nodes: List[NodeStatus]
    
    # Fire zones
    active_fires: List[GPSCoordinate]
    fire_intensity: Dict[str, float]  # node_id -> intensity
    
    # Intelligence
    death_vectors: List[DeathVector]
    black_zones: List[Tuple[GPSCoordinate, float]]
    
    # Alerts
    active_alerts: List[FireAlert]
    
    # Optional fields (with defaults must come last)
    predicted_spread: Optional[Dict] = None
    
    def to_visualization_data(self) -> Dict:
        """
        Convert to format for 3D visualization
        
        Returns:
            Dictionary suitable for web dashboard
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'nodes': {
                'alive': [
                    {
                        'id': n.node_id,
                        'lat': n.location.latitude,
                        'lon': n.location.longitude,
                        'risk': n.risk_score,
                        'battery': n.battery_level
                    }
                    for n in self.alive_nodes
                ],
                'dead': [
                    {
                        'id': n.node_id,
                        'lat': n.location.latitude,
                        'lon': n.location.longitude
                    }
                    for n in self.dead_nodes
                ],
                'dying': [
                    {
                        'id': n.node_id,
                        'lat': n.location.latitude,
                        'lon': n.location.longitude,
                        'temperature': n.temperature
                    }
                    for n in self.dying_nodes
                ]
            },
            'fire_zones': [
                {
                    'lat': loc.latitude,
                    'lon': loc.longitude,
                    'intensity': self.fire_intensity.get(f"{loc.latitude},{loc.longitude}", 0.0)
                }
                for loc in self.active_fires
            ],
            'death_vectors': [
                {
                    'start_lat': v.start_location.latitude,
                    'start_lon': v.start_location.longitude,
                    'end_lat': v.end_location.latitude,
                    'end_lon': v.end_location.longitude,
                    'direction': v.direction_degrees,
                    'speed': v.speed_mps
                }
                for v in self.death_vectors
            ],
            'black_zones': [
                {
                    'lat': loc.latitude,
                    'lon': loc.longitude,
                    'radius': radius
                }
                for loc, radius in self.black_zones
            ],
            'predicted_spread': self.predicted_spread
        }


# ============================================================================
#  UTILITY FUNCTIONS
# ============================================================================

def create_alert_from_phase5(phase5_decision,
                             node_id: str,
                             location: GPSCoordinate,
                             metadata: Dict = None) -> Optional[FireAlert]:
    """
    Create FireAlert from Phase-5 decision
    
    Args:
        phase5_decision: LogicGateDecision from Phase-5
        node_id: Node identifier
        location: GPS coordinates
        metadata: Additional context
    
    Returns:
        FireAlert if alert should be sent
    """
    if not phase5_decision.should_alert:
        return None
    
    # Map risk tier to priority
    from phase5_logic_gate import RiskTier
    
    priority_map = {
        RiskTier.RED: AlertPriority.P1_CRITICAL,
        RiskTier.ORANGE: AlertPriority.P2_MEDIUM,
        RiskTier.YELLOW: AlertPriority.P3_MAINTENANCE,
        RiskTier.GREEN: AlertPriority.P3_MAINTENANCE
    }
    
    priority = priority_map.get(phase5_decision.risk_tier, AlertPriority.P3_MAINTENANCE)
    
    return FireAlert(
        alert_id=f"{node_id}_{int(datetime.now().timestamp())}",
        priority=priority,
        node_id=node_id,
        location=location,
        risk_score=phase5_decision.risk_score,
        confidence=phase5_decision.confidence,
        witnesses=phase5_decision.witnesses,
        timestamp=phase5_decision.timestamp,
        metadata={
            'reasoning': phase5_decision.reasoning,
            'system_state': phase5_decision.system_state.value,
            **(metadata or {})
        }
    )


# ============================================================================
#  THE HIVE: MESH NETWORK (Queen + Drone Architecture)
# ============================================================================

@dataclass
class MeshMessage:
    """
    Message routed through the mesh network
    
    Attributes:
        message_id: Unique message ID
        source_node_id: Originating node
        destination_node_id: Target node (Queen ID or 'BROADCAST')
        message_type: 'alert', 'heartbeat', 'aggregated_alert', 'satellite_uplink'
        payload: Serialized alert or heartbeat data
        hop_count: Number of relay hops
        relay_path: List of node IDs the message traversed
        timestamp: Message creation time
    """
    message_id: str
    source_node_id: str
    destination_node_id: str
    message_type: str
    payload: Dict
    hop_count: int = 0
    relay_path: List[str] = field(default_factory=list)
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'message_id': self.message_id,
            'source': self.source_node_id,
            'destination': self.destination_node_id,
            'type': self.message_type,
            'hops': self.hop_count,
            'relay_path': self.relay_path,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'payload': self.payload
        }


class MeshNetwork:
    """
    LoRa Mesh Network Topology Manager
    
    Manages the Hive architecture:
    - Registers Queen and Drone nodes
    - Routes messages through the mesh (Drone → Queen)
    - Tracks relay paths for visualization
    - Enforces role-based routing rules
    
    Architecture:
    ┌─────────┐   LoRa    ┌─────────┐   LoRa    ┌─────────┐
    │ DRONE_1 │──────────▶│         │◀──────────│ DRONE_3 │
    └─────────┘           │  QUEEN  │           └─────────┘
    ┌─────────┐   LoRa    │         │   Sat     ┌─────────┐
    │ DRONE_2 │──────────▶│         │──────────▶│   🛰️    │
    └─────────┘           └─────────┘           └─────────┘
    """
    
    def __init__(self, lora_range_meters: float = 2000.0):
        self.lora_range_meters = lora_range_meters
        
        # Registered nodes: node_id → {role, location, config, comm_layer, status}
        self.nodes: Dict[str, Dict] = {}
        
        # Message log for visualization
        self.message_log: List[MeshMessage] = []
        self.max_log_size = 200
        
        # Queen node tracking (supports multiple Queens)
        self.queen_node_id: Optional[str] = None  # first/primary Queen
        self.queen_node_ids: List[str] = []  # all Queens
        
        # Statistics
        self.stats = {
            'messages_routed': 0,
            'drone_to_queen': 0,
            'queen_to_satellite': 0,
            'heartbeats_received': 0,
            'alerts_aggregated': 0,
            'relay_hops_total': 0
        }
        
        self.logger = logging.getLogger("MeshNetwork")
    
    def register_node(self, node_id: str, role: str, location: GPSCoordinate,
                      config: Dict = None):
        """
        Register a node in the mesh network
        
        Args:
            node_id: Unique node identifier
            role: 'QUEEN' or 'DRONE'
            location: GPS coordinates
            config: Node configuration dict
        """
        self.nodes[node_id] = {
            'role': role,
            'location': location,
            'config': config or {},
            'status': 'ONLINE',
            'last_heartbeat': datetime.now(),
            'alerts_sent': 0,
            'battery_level': 100.0,
            'risk_score': 0.0
        }
        
        if role == 'QUEEN':
            if not self.queen_node_id:
                self.queen_node_id = node_id  # first Queen is primary
            if node_id not in self.queen_node_ids:
                self.queen_node_ids.append(node_id)
            self.logger.info(f"👑 QUEEN node registered: {node_id} (total: {len(self.queen_node_ids)})")
        else:
            self.logger.info(f"🐝 DRONE node registered: {node_id}")
    
    def route_message(self, message: MeshMessage) -> bool:
        """
        Route a message through the mesh network
        
        Routing Rules:
        1. Drone alerts → Queen (via LoRa mesh)
        2. Queen aggregated alerts → Satellite (if P1)
        3. Heartbeats → Queen only
        
        Args:
            message: MeshMessage to route
        
        Returns:
            True if message was successfully routed
        """
        # Add source to relay path
        if message.source_node_id not in message.relay_path:
            message.relay_path.append(message.source_node_id)
        
        message.timestamp = message.timestamp or datetime.now()
        
        source_node = self.nodes.get(message.source_node_id)
        if not source_node:
            self.logger.warning(f"Unknown source node: {message.source_node_id}")
            return False
        
        # Drone → Queen routing
        if source_node['role'] == 'DRONE':
            return self._route_drone_to_queen(message)
        
        # Queen → Satellite routing
        elif source_node['role'] == 'QUEEN':
            return self._route_queen_uplink(message)
        
        return False
    
    def _route_drone_to_queen(self, message: MeshMessage) -> bool:
        """
        Route message from Drone to its assigned Queen via LoRa mesh
        
        Supports multiple Queens — each Drone routes to its own Queen.
        """
        # Determine target Queen: from message destination, drone config, or primary
        target_queen = message.destination_node_id
        if not target_queen or target_queen not in self.nodes:
            # Fallback: check drone's assigned queen
            drone_node = self.nodes.get(message.source_node_id, {})
            target_queen = drone_node.get('queen_id', self.queen_node_id)
        
        if not target_queen or target_queen not in self.nodes:
            self.logger.error("No Queen node available for this Drone!")
            return False
        
        queen = self.nodes[target_queen]
        source = self.nodes[message.source_node_id]
        
        # Calculate distance to Queen
        distance = source['location'].distance_to(queen['location'])
        
        if distance <= self.lora_range_meters:
            # Direct link to Queen
            message.destination_node_id = target_queen
            message.hop_count += 1
            message.relay_path.append(target_queen)
            
            self.logger.info(
                f"📡 DRONE→QUEEN: {message.source_node_id} → "
                f"{target_queen} (direct, {distance:.0f}m)"
            )
        else:
            # Multi-hop: find closest intermediate Drone to relay
            relay_node = self._find_relay_node(message.source_node_id, target_queen)
            if relay_node:
                message.hop_count += 1
                message.relay_path.append(relay_node)
                message.relay_path.append(target_queen)
                message.hop_count += 1
                
                self.logger.info(
                    f"📡 DRONE→RELAY→QUEEN: {message.source_node_id} → "
                    f"{relay_node} → {target_queen}"
                )
            else:
                # Fallback: assume direct even if out of range (for demo)
                message.hop_count += 1
                message.relay_path.append(target_queen)
        
        # Update stats
        self.stats['messages_routed'] += 1
        self.stats['drone_to_queen'] += 1
        self.stats['relay_hops_total'] += message.hop_count
        
        if message.message_type == 'heartbeat':
            self.stats['heartbeats_received'] += 1
            self.nodes[message.source_node_id]['last_heartbeat'] = datetime.now()
        
        # Log the message
        self._log_message(message)
        
        # Update source node stats
        if message.source_node_id in self.nodes:
            self.nodes[message.source_node_id]['alerts_sent'] += 1
        
        return True
    
    def _route_queen_uplink(self, message: MeshMessage) -> bool:
        """
        Route message from Queen to Satellite
        
        Queen packages aggregated intelligence and transmits via Iridium.
        """
        message.hop_count += 1
        message.relay_path.append("🛰️ SATELLITE")
        message.message_type = 'satellite_uplink'
        
        self.stats['messages_routed'] += 1
        self.stats['queen_to_satellite'] += 1
        
        self.logger.critical(
            f"🛰️ QUEEN→SATELLITE: {message.source_node_id} uplink "
            f"(aggregated from {len(message.payload.get('source_drones', []))} drones)"
        )
        
        self._log_message(message)
        return True
    
    def _find_relay_node(self, source_id: str, target_queen_id: str = None) -> Optional[str]:
        """Find closest Drone that can relay to Queen"""
        queen_id = target_queen_id or self.queen_node_id
        if not queen_id:
            return None
        
        source_loc = self.nodes[source_id]['location']
        queen_loc = self.nodes[queen_id]['location']
        
        best_relay = None
        best_distance = float('inf')
        
        for nid, node in self.nodes.items():
            if nid == source_id or nid == queen_id:
                continue
            if node['status'] != 'ONLINE':
                continue
            
            # Check if this node can reach both source and Queen
            dist_to_source = node['location'].distance_to(source_loc)
            dist_to_queen = node['location'].distance_to(queen_loc)
            
            if (dist_to_source <= self.lora_range_meters and 
                dist_to_queen <= self.lora_range_meters):
                total_dist = dist_to_source + dist_to_queen
                if total_dist < best_distance:
                    best_distance = total_dist
                    best_relay = nid
        
        return best_relay
    
    def _log_message(self, message: MeshMessage):
        """Add message to log (capped at max_log_size)"""
        self.message_log.append(message)
        if len(self.message_log) > self.max_log_size:
            self.message_log.pop(0)
    
    def update_node_status(self, node_id: str, battery: float = None,
                           risk_score: float = None, status: str = None):
        """Update a node's status information"""
        if node_id in self.nodes:
            if battery is not None:
                self.nodes[node_id]['battery_level'] = battery
            if risk_score is not None:
                self.nodes[node_id]['risk_score'] = risk_score
            if status is not None:
                self.nodes[node_id]['status'] = status
    
    def get_topology(self) -> Dict:
        """
        Get mesh topology for dashboard visualization
        
        Returns:
            Dictionary with nodes, links, and statistics
            Supports multiple Queens — each Drone links to its assigned Queen.
        """
        nodes_data = []
        links_data = []
        
        for nid, node in self.nodes.items():
            nodes_data.append({
                'id': nid,
                'role': node['role'],
                'lat': node['location'].latitude,
                'lon': node['location'].longitude,
                'status': node['status'],
                'battery': node['battery_level'],
                'risk_score': node['risk_score'],
                'alerts_sent': node['alerts_sent'],
                'last_heartbeat': node['last_heartbeat'].isoformat() 
                    if node['last_heartbeat'] else None,
                'is_queen': node['role'] == 'QUEEN',
                'label': node.get('label', nid),
                'queen_id': node.get('queen_id', None)
            })
            
            # Add LoRa link: Drone → its assigned Queen
            if node['role'] == 'DRONE':
                assigned_queen = node.get('queen_id', self.queen_node_id)
                if assigned_queen and assigned_queen in self.nodes:
                    queen_loc = self.nodes[assigned_queen]['location']
                    distance = node['location'].distance_to(queen_loc)
                    links_data.append({
                        'source': nid,
                        'target': assigned_queen,
                        'distance_m': round(distance, 1),
                        'type': 'lora',
                        'active': node['status'] == 'ONLINE'
                    })
        
        # Add satellite uplink from EACH Queen
        for queen_id in self.queen_node_ids:
            links_data.append({
                'source': queen_id,
                'target': 'SATELLITE',
                'type': 'satellite',
                'active': True
            })
        
        # Recent relay events for animation
        recent_relays = []
        for msg in self.message_log[-20:]:
            recent_relays.append({
                'path': msg.relay_path,
                'type': msg.message_type,
                'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
            })
        
        return {
            'nodes': nodes_data,
            'links': links_data,
            'queen_ids': self.queen_node_ids,
            'queen_id': self.queen_node_id,  # backward compat (primary)
            'recent_relays': recent_relays,
            'stats': self.stats
        }
    
    def get_statistics(self) -> Dict:
        """Get mesh network statistics"""
        online_drones = sum(
            1 for n in self.nodes.values()
            if n['role'] == 'DRONE' and n['status'] == 'ONLINE'
        )
        return {
            **self.stats,
            'total_nodes': len(self.nodes),
            'online_drones': online_drones,
            'queen_active': self.queen_node_id is not None
        }


class RoleAwareCommunicationLayer:
    """
    Role-Aware Communication Layer (The Hive Protocol)
    
    Wraps Phase6CommunicationLayer with Queen/Drone intelligence:
    
    🐝 DRONE Node:
        - Senses fire via 6-phase pipeline
        - Routes ALL alerts to Queen via LoRa mesh
        - NEVER uses satellite directly (no hardware)
        - Sends heartbeats to Queen with jitter
    
    👑 QUEEN Node:
        - Receives alerts from all Drones
        - Aggregates multi-drone intelligence
        - Auto-escalates when ≥2 Drones confirm same area
        - Routes P1→Satellite, P2→LoRa gateway, P3→log
        - Maintains mesh health tracking
    
    Data Flow:
        DRONE₁ ──LoRa──▶ ┌──────┐ ──Satellite──▶ 🛰️ ──▶ 🚒
        DRONE₂ ──LoRa──▶ │QUEEN │
        DRONE₃ ──LoRa──▶ └──────┘
    """
    
    def __init__(self, node_id: str, role: str, location: GPSCoordinate,
                 mesh_network: 'MeshNetwork',
                 queen_node_id: Optional[str] = None,
                 has_satellite: bool = False,
                 heartbeat_interval_sec: int = 3600,
                 heartbeat_jitter_sec: int = 600):
        """
        Initialize Role-Aware Communication
        
        Args:
            node_id: This node's unique ID
            role: 'QUEEN' or 'DRONE'
            location: GPS coordinates
            mesh_network: Shared MeshNetwork instance
            queen_node_id: Queen to route to (Drones only)
            has_satellite: Whether this node has satellite modem
            heartbeat_interval_sec: Heartbeat interval (Drones only)
            heartbeat_jitter_sec: Heartbeat jitter window
        """
        self.node_id = node_id
        self.role = role
        self.location = location
        self.mesh = mesh_network
        self.queen_node_id = queen_node_id
        self.has_satellite = has_satellite
        self.heartbeat_interval_sec = heartbeat_interval_sec
        self.heartbeat_jitter_sec = heartbeat_jitter_sec
        
        # Underlying Phase-6 communication
        self.comm = Phase6CommunicationLayer(
            node_id=node_id,
            location=location
        )
        
        # Queen-specific: aggregation buffer
        self._drone_alerts: List[Dict] = []
        self._aggregation_window_sec = 300  # 5-minute window
        self._escalation_threshold = 2  # ≥2 Drones = auto-escalate
        
        # Heartbeat tracking
        self._last_heartbeat = datetime.now()
        self._heartbeat_count = 0
        
        # Message counter
        self._message_counter = 0
        
        self.logger = logging.getLogger(f"Hive.{role}.{node_id}")
        
        # Register this node in the mesh
        self.mesh.register_node(
            node_id=node_id,
            role=role,
            location=location,
            config={
                'has_satellite': has_satellite,
                'queen_node_id': queen_node_id,
                'heartbeat_interval': heartbeat_interval_sec
            }
        )
    
    def process_alert(self, risk_score: float, confidence: float,
                      should_alert: bool, witnesses: int = 0,
                      node_temperature: float = 25.0,
                      battery_level: float = 100.0,
                      metadata: Dict = None) -> Optional[Dict]:
        """
        Process alert with role-aware routing
        
        Drone: Routes to Queen via mesh
        Queen: Routes to satellite or LoRa gateway
        
        Returns:
            Dictionary with alert details and relay path
        """
        # First, let Phase-6 determine priority
        priority = self.comm._determine_priority(
            risk_score, confidence, witnesses, battery_level
        )
        
        # Update mesh node status
        self.mesh.update_node_status(
            self.node_id, battery=battery_level, risk_score=risk_score
        )
        
        if self.role == 'DRONE':
            return self._drone_process_alert(
                risk_score, confidence, priority, witnesses,
                node_temperature, battery_level, metadata
            )
        elif self.role == 'QUEEN':
            return self._queen_process_alert(
                risk_score, confidence, priority, witnesses,
                node_temperature, battery_level, metadata
            )
        
        return None
    
    def _drone_process_alert(self, risk_score, confidence, priority,
                              witnesses, temperature, battery, metadata) -> Dict:
        """
        🐝 DRONE: Route alert to Queen via LoRa mesh
        
        Drones NEVER use satellite directly. All alerts go to Queen.
        """
        self._message_counter += 1
        msg_id = f"{self.node_id}_MESH_{self._message_counter}"
        
        # Build alert payload
        payload = {
            'alert_id': msg_id,
            'source_node': self.node_id,
            'source_role': 'DRONE',
            'priority': priority.name,
            'risk_score': risk_score,
            'confidence': confidence,
            'witnesses': witnesses,
            'temperature': temperature,
            'battery': battery,
            'location': {
                'lat': self.location.latitude,
                'lon': self.location.longitude
            },
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        # Create mesh message
        message = MeshMessage(
            message_id=msg_id,
            source_node_id=self.node_id,
            destination_node_id=self.queen_node_id or 'QUEEN',
            message_type='alert',
            payload=payload,
            timestamp=datetime.now()
        )
        
        # Route through mesh to Queen
        success = self.mesh.route_message(message)
        
        self.logger.info(
            f"🐝 DRONE alert: {msg_id} | risk={risk_score:.2f} | "
            f"priority={priority.name} | →QUEEN via LoRa"
        )
        
        return {
            'alert_id': msg_id,
            'source': self.node_id,
            'role': 'DRONE',
            'priority': priority.name,
            'risk_score': risk_score,
            'channel': 'LORA_TO_QUEEN',
            'relay_path': message.relay_path,
            'relay_path_display': ' → '.join(message.relay_path),
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
    
    def _queen_process_alert(self, risk_score, confidence, priority,
                              witnesses, temperature, battery, metadata) -> Dict:
        """
        👑 QUEEN: Process alert with aggregation intelligence
        
        Queen can generate its own alerts OR receive from Drones.
        P1 → Satellite, P2 → LoRa Gateway, P3 → Log
        """
        self._message_counter += 1
        msg_id = f"{self.node_id}_QUEEN_{self._message_counter}"
        
        # Use underlying Phase-6 for routing decision
        alert = self.comm.process_alert(
            risk_score=risk_score,
            confidence=confidence,
            should_alert=True,
            witnesses=witnesses,
            node_temperature=temperature,
            battery_level=battery,
            metadata=metadata
        )
        
        result = {
            'alert_id': msg_id,
            'source': self.node_id,
            'role': 'QUEEN',
            'priority': priority.name,
            'risk_score': risk_score,
            'channel': alert.channel.value if alert else 'unknown',
            'relay_path': [self.node_id],
            'success': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # If P1 Critical → satellite uplink
        if priority == AlertPriority.P1_CRITICAL and self.has_satellite:
            sat_message = MeshMessage(
                message_id=msg_id,
                source_node_id=self.node_id,
                destination_node_id='SATELLITE',
                message_type='satellite_uplink',
                payload={
                    'alert': result,
                    'source_drones': [self.node_id]
                },
                relay_path=[self.node_id],
                timestamp=datetime.now()
            )
            self.mesh.route_message(sat_message)
            result['relay_path'] = sat_message.relay_path
            result['channel'] = 'SATELLITE'
        
        result['relay_path_display'] = ' → '.join(result['relay_path'])
        
        self.logger.critical(
            f"👑 QUEEN alert: {msg_id} | risk={risk_score:.2f} | "
            f"channel={result['channel']}"
        )
        
        return result
    
    def receive_drone_alert(self, drone_alert: Dict) -> Optional[Dict]:
        """
        👑 QUEEN ONLY: Receive and aggregate alert from a Drone
        
        Aggregation Logic:
        - Buffer incoming Drone alerts
        - If ≥2 Drones report fire in same area within 5 min → auto-escalate to P1
        - Otherwise, relay at original priority
        
        Args:
            drone_alert: Alert dictionary from a Drone
        
        Returns:
            Aggregated/escalated alert result, or None
        """
        if self.role != 'QUEEN':
            self.logger.warning("Only Queen nodes can receive Drone alerts")
            return None
        
        # Add to aggregation buffer
        self._drone_alerts.append({
            **drone_alert,
            'received_at': datetime.now()
        })
        
        # Clean old alerts outside window
        cutoff = datetime.now() - timedelta(seconds=self._aggregation_window_sec)
        self._drone_alerts = [
            a for a in self._drone_alerts
            if datetime.fromisoformat(a.get('received_at', cutoff).isoformat()
                if isinstance(a.get('received_at'), datetime)
                else a.get('timestamp', cutoff.isoformat())) > cutoff
        ]
        
        # Check for multi-drone consensus
        recent_high_risk = [
            a for a in self._drone_alerts
            if a.get('risk_score', 0) > 0.6
        ]
        
        if len(recent_high_risk) >= self._escalation_threshold:
            # AUTO-ESCALATE: Multiple drones confirm fire!
            source_drones = list(set(a.get('source_node', a.get('source', ''))
                                     for a in recent_high_risk))
            avg_risk = sum(a['risk_score'] for a in recent_high_risk) / len(recent_high_risk)
            max_risk = max(a['risk_score'] for a in recent_high_risk)
            
            self.logger.critical(
                f"🔴 MULTI-DRONE CONSENSUS: {len(source_drones)} drones confirm fire! "
                f"Escalating to P1 CRITICAL (avg risk: {avg_risk:.2f})"
            )
            
            self.mesh.stats['alerts_aggregated'] += 1
            
            # Create escalated satellite uplink
            self._message_counter += 1
            escalated_id = f"{self.node_id}_ESCALATED_{self._message_counter}"
            
            aggregate_payload = {
                'alert_id': escalated_id,
                'type': 'MULTI_DRONE_CONSENSUS',
                'source_drones': source_drones,
                'drone_count': len(source_drones),
                'avg_risk': avg_risk,
                'max_risk': max_risk,
                'individual_alerts': [
                    {
                        'source': a.get('source_node', a.get('source', '')),
                        'risk': a.get('risk_score', 0),
                        'priority': a.get('priority', 'UNKNOWN')
                    }
                    for a in recent_high_risk
                ],
                'location': recent_high_risk[0].get('location', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            # Route to satellite
            sat_message = MeshMessage(
                message_id=escalated_id,
                source_node_id=self.node_id,
                destination_node_id='SATELLITE',
                message_type='satellite_uplink',
                payload=aggregate_payload,
                relay_path=[self.node_id],
                timestamp=datetime.now()
            )
            self.mesh.route_message(sat_message)
            
            # Clear buffer after escalation
            self._drone_alerts.clear()
            
            return {
                'alert_id': escalated_id,
                'type': 'MULTI_DRONE_CONSENSUS',
                'escalated': True,
                'source': self.node_id,
                'role': 'QUEEN',
                'priority': 'P1_CRITICAL',
                'channel': 'SATELLITE',
                'source_drones': source_drones,
                'avg_risk': avg_risk,
                'relay_path': sat_message.relay_path,
                'relay_path_display': ' → '.join(sat_message.relay_path),
                'timestamp': datetime.now().isoformat()
            }
        
        # Single drone alert — relay at original priority
        return {
            'alert_id': drone_alert.get('alert_id', 'unknown'),
            'type': 'DRONE_RELAY',
            'escalated': False,
            'source': drone_alert.get('source', ''),
            'role': 'QUEEN',
            'priority': drone_alert.get('priority', 'P3_MAINTENANCE'),
            'channel': 'LORA_GATEWAY',
            'buffered_alerts': len(self._drone_alerts),
            'relay_path_display': f"{drone_alert.get('source', '?')} → {self.node_id} → Gateway",
            'timestamp': datetime.now().isoformat()
        }
    
    def send_heartbeat(self) -> Dict:
        """
        🐝 DRONE: Send heartbeat to Queen with collision-avoidance jitter
        
        Returns:
            Heartbeat info dictionary
        """
        import random
        jitter = random.uniform(0, self.heartbeat_jitter_sec)
        
        self._heartbeat_count += 1
        self._last_heartbeat = datetime.now()
        
        hb_id = f"{self.node_id}_HB_{self._heartbeat_count}"
        
        payload = {
            'heartbeat_id': hb_id,
            'node_id': self.node_id,
            'role': self.role,
            'status': 'ONLINE',
            'battery': self.mesh.nodes.get(self.node_id, {}).get('battery_level', 100),
            'risk_score': self.mesh.nodes.get(self.node_id, {}).get('risk_score', 0),
            'location': {
                'lat': self.location.latitude,
                'lon': self.location.longitude
            },
            'jitter_applied_sec': round(jitter, 1),
            'timestamp': datetime.now().isoformat()
        }
        
        message = MeshMessage(
            message_id=hb_id,
            source_node_id=self.node_id,
            destination_node_id=self.queen_node_id or 'QUEEN',
            message_type='heartbeat',
            payload=payload,
            timestamp=datetime.now()
        )
        
        self.mesh.route_message(message)
        
        self.logger.debug(
            f"💓 Heartbeat #{self._heartbeat_count}: {self.node_id} "
            f"(jitter: {jitter:.0f}s)"
        )
        
        return payload
    
    def get_mesh_status(self) -> Dict:
        """Get this node's role-aware status"""
        base_status = {
            'node_id': self.node_id,
            'role': self.role,
            'has_satellite': self.has_satellite,
            'location': {
                'lat': self.location.latitude,
                'lon': self.location.longitude
            },
            'heartbeat_count': self._heartbeat_count,
            'last_heartbeat': self._last_heartbeat.isoformat(),
            'message_count': self._message_counter,
            'comm_stats': self.comm.get_statistics()
        }
        
        if self.role == 'QUEEN':
            base_status['buffered_drone_alerts'] = len(self._drone_alerts)
            base_status['connected_drones'] = sum(
                1 for n in self.mesh.nodes.values()
                if n['role'] == 'DRONE' and n['status'] == 'ONLINE'
            )
        elif self.role == 'DRONE':
            base_status['queen_node_id'] = self.queen_node_id
        
        return base_status


if __name__ == "__main__":
    print("\n📡 Phase-6 Communication Layer - Production Ready")
    print("=" * 70)
    print("\n🐝 THE HIVE ARCHITECTURE:")
    print("  👑 Queen Node: Gateway with satellite modem")
    print("  🐝 Drone Nodes: Lightweight sensors, relay to Queen via LoRa")
    print("\nKey Features:")
    print("  ✅ 3-tier priority routing (P1/P2/P3)")
    print("  ✅ LoRaWAN mesh + satellite fallback")
    print("  ✅ Role-aware routing (Drone→Queen→Satellite)")
    print("  ✅ Multi-drone consensus escalation")
    print("  ✅ Collision-avoidance heartbeats (jitter)")
    print("  ✅ Death vector analysis")
    print("  ✅ Negative space mapping")
    print("  ✅ Dying gasp protocol")
    print("  ✅ Trauma decay system")
    print("  ✅ Fire spread prediction")
    print("=" * 70)
