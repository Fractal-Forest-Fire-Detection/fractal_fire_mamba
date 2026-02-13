"""
Node Role Configuration for "The Hive" Architecture

This module defines the node's role (Queen or Drone) and configures
hardware capabilities accordingly.

Usage:
    Set NODE_ROLE environment variable:
        export NODE_ROLE=QUEEN    # or DRONE
    
    Or edit this file directly to set DEFAULT_NODE_ROLE

Author: Fractal Fire Mamba Team
Date: 2026-02-09
"""

import os
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class NodeRole(Enum):
    """
    Node role in The Hive architecture
    
    QUEEN: Gateway node with satellite modem, handles routing for all drones
    DRONE: Lightweight sensor node, relays to Queen via LoRa mesh
    """
    QUEEN = "QUEEN"
    DRONE = "DRONE"


# Default role if environment variable not set
DEFAULT_NODE_ROLE = NodeRole.DRONE  # Most nodes are drones


@dataclass
class NodeConfig:
    """
    Configuration for a node based on its role
    
    Attributes:
        role: Queen or Drone
        has_satellite: Whether node has RockBLOCK satellite modem
        can_route_messages: Whether node can relay messages for others
        queen_node_id: ID of Queen node (for Drones to route to)
        node_id: Unique identifier for this node
        heartbeat_interval_sec: How often to ping Queen (Drones only)
        heartbeat_jitter_sec: Random delay range to prevent collision storms
    """
    role: NodeRole
    has_satellite: bool
    can_route_messages: bool
    queen_node_id: Optional[str] = None
    node_id: str = "NODE_UNKNOWN"
    heartbeat_interval_sec: int = 3600  # 1 hour default
    heartbeat_jitter_sec: int = 600  # 10 minutes jitter window
    
    @property
    def is_queen(self) -> bool:
        """Returns True if this is a Queen node"""
        return self.role == NodeRole.QUEEN
    
    @property
    def is_drone(self) -> bool:
        """Returns True if this is a Drone node"""
        return self.role == NodeRole.DRONE
    
    def get_heartbeat_delay(self) -> float:
        """
        Get randomized heartbeat delay to prevent collision storm
        
        Problem: If 49 drones boot at sunrise (solar wake-up), they might
        all send heartbeat at the same second, causing packet collisions.
        
        Solution: Add random jitter spread over 10 minutes (600s) to 
        distribute the load.
        
        Returns:
            Random delay in seconds (0 to heartbeat_jitter_sec)
        """
        import random
        return random.uniform(0, self.heartbeat_jitter_sec)


def get_node_role() -> NodeRole:
    """
    Get node role from environment variable or default
    
    Environment variable: NODE_ROLE (QUEEN or DRONE)
    
    Returns:
        NodeRole enum value
    """
    role_str = os.getenv('NODE_ROLE', DEFAULT_NODE_ROLE.value).upper()
    
    try:
        return NodeRole(role_str)
    except ValueError:
        print(f"⚠️  Invalid NODE_ROLE '{role_str}', defaulting to {DEFAULT_NODE_ROLE.value}")
        return DEFAULT_NODE_ROLE


def create_node_config(
    node_id: str,
    queen_node_id: Optional[str] = None,
    heartbeat_interval_sec: int = 3600
) -> NodeConfig:
    """
    Create node configuration based on role
    
    Args:
        node_id: Unique identifier for this node (e.g., "NODE_001")
        queen_node_id: ID of Queen node (required for Drones)
        heartbeat_interval_sec: Heartbeat interval in seconds (Drones only)
    
    Returns:
        NodeConfig with appropriate settings
    
    Raises:
        ValueError: If Drone node doesn't have queen_node_id set
    """
    role = get_node_role()
    
    if role == NodeRole.QUEEN:
        # Queen node configuration
        return NodeConfig(
            role=NodeRole.QUEEN,
            has_satellite=True,
            can_route_messages=True,
            queen_node_id=None,  # Queen doesn't route to anyone
            node_id=node_id,
            heartbeat_interval_sec=0  # Queen doesn't send heartbeats
        )
    else:
        # Drone node configuration
        if not queen_node_id:
            raise ValueError(
                "Drone nodes must specify queen_node_id. "
                "Set via environment variable QUEEN_NODE_ID or pass as argument."
            )
        
        return NodeConfig(
            role=NodeRole.DRONE,
            has_satellite=False,  # NO satellite modem
            can_route_messages=False,  # Drones don't relay for others
            queen_node_id=queen_node_id,
            node_id=node_id,
            heartbeat_interval_sec=heartbeat_interval_sec
        )


def get_queen_node_id() -> Optional[str]:
    """
    Get Queen node ID from environment variable
    
    Environment variable: QUEEN_NODE_ID
    
    Returns:
        Queen node ID or None
    """
    return os.getenv('QUEEN_NODE_ID')


# ============================================================================
#  USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("\n🐝 The Hive Architecture - Node Configuration\n")
    print("=" * 70)
    
    # Example 1: Queen Node
    print("\n📍 Example 1: Queen Node Configuration\n")
    os.environ['NODE_ROLE'] = 'QUEEN'
    
    queen_config = create_node_config(node_id="FOREST_A_QUEEN_001")
    
    print(f"Node ID: {queen_config.node_id}")
    print(f"Role: {queen_config.role.value}")
    print(f"Has Satellite: {queen_config.has_satellite} (RockBLOCK 9603)")
    print(f"Can Route Messages: {queen_config.can_route_messages}")
    print(f"Is Queen: {queen_config.is_queen}")
    
    # Example 2: Drone Node
    print("\n📍 Example 2: Drone Node Configuration\n")
    os.environ['NODE_ROLE'] = 'DRONE'
    os.environ['QUEEN_NODE_ID'] = 'FOREST_A_QUEEN_001'
    
    drone_config = create_node_config(
        node_id="FOREST_A_DRONE_042",
        queen_node_id=get_queen_node_id()
    )
    
    print(f"Node ID: {drone_config.node_id}")
    print(f"Role: {drone_config.role.value}")
    print(f"Has Satellite: {drone_config.has_satellite} (NO - relay to Queen)")
    print(f"Can Route Messages: {drone_config.can_route_messages}")
    print(f"Routes to Queen: {drone_config.queen_node_id}")
    print(f"Heartbeat Interval: {drone_config.heartbeat_interval_sec}s (1 hour)")
    print(f"Is Drone: {drone_config.is_drone}")
    
    # Example 3: Integration with Heartbeat Protocol
    print("\n📍 Example 3: Heartbeat with Collision Avoidance\n")
    print("""
# Heartbeat loop in communication layer:

import time
from config.node_role import create_node_config

config = create_node_config(node_id="DRONE_042", queen_node_id="QUEEN_001")

if config.is_drone:
    while True:
        # CRITICAL: Add jitter to prevent collision storm
        # If all 49 drones wake at sunrise, they'd collide without this
        jitter = config.get_heartbeat_delay()
        time.sleep(jitter)
        
        # Send heartbeat to Queen
        send_heartbeat_to_queen(config.queen_node_id)
        
        # Wait for next interval
        time.sleep(config.heartbeat_interval_sec)
        
# Jitter spreads 49 drones over 10 minutes instead of 1 second
    """)
    
    print("=" * 70)
    print("\n✅ Node configuration ready for deployment")
    print("\nDeployment Checklist:")
    print("  [ ] Set NODE_ROLE environment variable (QUEEN or DRONE)")
    print("  [ ] Set QUEEN_NODE_ID for all Drone nodes")
    print("  [ ] Configure node_id unique for each node")
    print("  [ ] Test LoRa connectivity between Drones and Queen")
    print("  [ ] Verify heartbeat protocol (Drones → Queen hourly)")
    print("")
