#!/usr/bin/env python3
"""
THE HIVE: Queen-Drone Mesh Network Verification
=================================================
End-to-end test of Drone→Queen→Satellite communication architecture.

Tests:
  1. Node registration (1 Queen + 3 Drones)
  2. Drone alert routing to Queen via LoRa
  3. Queen aggregation + multi-drone escalation
  4. Satellite uplink for P1 Critical
  5. Heartbeat protocol with jitter
  6. Mesh topology serialization for dashboard
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phases.phase6_communication.communication_layer import (
    GPSCoordinate, MeshNetwork, MeshMessage,
    RoleAwareCommunicationLayer, AlertPriority
)


def test_node_registration():
    """Test: 1 Queen + 3 Drones register correctly"""
    mesh = MeshNetwork(lora_range_meters=2000.0)
    
    queen_loc = GPSCoordinate(latitude=-35.7200, longitude=150.1000)
    mesh.register_node("QUEEN_001", "QUEEN", queen_loc)
    
    drone_locs = [
        ("DRONE_001", -35.7180, 150.0970),
        ("DRONE_002", -35.7220, 150.1030),
        ("DRONE_003", -35.7190, 150.1050),
    ]
    for nid, lat, lon in drone_locs:
        mesh.register_node(nid, "DRONE", GPSCoordinate(lat, lon))
    
    assert len(mesh.nodes) == 4, f"Expected 4 nodes, got {len(mesh.nodes)}"
    assert mesh.queen_node_id == "QUEEN_001"
    assert mesh.nodes["QUEEN_001"]["role"] == "QUEEN"
    assert mesh.nodes["DRONE_001"]["role"] == "DRONE"
    print("  ✅ 1. Node registration: 1 Queen + 3 Drones")
    return mesh


def test_drone_to_queen_routing(mesh):
    """Test: Drone alert reaches Queen via LoRa mesh"""
    msg = MeshMessage(
        message_id="TEST_MSG_001",
        source_node_id="DRONE_001",
        destination_node_id="QUEEN_001",
        message_type="alert",
        payload={"risk_score": 0.75, "priority": "P2_MEDIUM"}
    )
    
    success = mesh.route_message(msg)
    assert success, "Drone→Queen routing failed"
    assert "QUEEN_001" in msg.relay_path, "Queen not in relay path"
    assert msg.hop_count >= 1, "Expected at least 1 hop"
    assert mesh.stats['drone_to_queen'] >= 1
    print(f"  ✅ 2. Drone→Queen routing: {' → '.join(msg.relay_path)}")


def test_role_aware_drone_alert():
    """Test: RoleAwareCommunicationLayer routes Drone alerts to Queen only"""
    mesh = MeshNetwork(lora_range_meters=2000.0)
    
    queen_loc = GPSCoordinate(-35.72, 150.10)
    queen = RoleAwareCommunicationLayer(
        node_id="QUEEN_001", role="QUEEN", location=queen_loc,
        mesh_network=mesh, has_satellite=True
    )
    
    drone_loc = GPSCoordinate(-35.718, 150.097)
    drone = RoleAwareCommunicationLayer(
        node_id="DRONE_001", role="DRONE", location=drone_loc,
        mesh_network=mesh, queen_node_id="QUEEN_001"
    )
    
    # Drone detects fire
    result = drone.process_alert(
        risk_score=0.85, confidence=0.90, should_alert=True,
        witnesses=2, battery_level=80.0
    )
    
    assert result is not None, "Drone alert returned None"
    assert result['role'] == 'DRONE'
    assert result['channel'] == 'LORA_TO_QUEEN'
    assert 'QUEEN_001' in result['relay_path']
    assert result['success'] is True
    print(f"  ✅ 3. Drone alert via LoRa: {result['relay_path_display']}")
    return mesh, queen, drone


def test_queen_aggregation_escalation():
    """Test: Queen escalates to P1 when ≥2 Drones confirm fire"""
    mesh = MeshNetwork(lora_range_meters=2000.0)
    
    queen_loc = GPSCoordinate(-35.72, 150.10)
    queen = RoleAwareCommunicationLayer(
        node_id="QUEEN_001", role="QUEEN", location=queen_loc,
        mesh_network=mesh, has_satellite=True
    )
    
    # Create 3 drones
    drones = []
    for i, (lat, lon) in enumerate([(-35.718, 150.097), (-35.722, 150.103), (-35.719, 150.105)]):
        d = RoleAwareCommunicationLayer(
            node_id=f"DRONE_00{i+1}", role="DRONE",
            location=GPSCoordinate(lat, lon),
            mesh_network=mesh, queen_node_id="QUEEN_001"
        )
        drones.append(d)
    
    # Drone 1 sends high-risk alert
    alert1 = drones[0].process_alert(risk_score=0.85, confidence=0.90, should_alert=True, witnesses=1)
    result1 = queen.receive_drone_alert(alert1)
    assert result1['escalated'] is False, "Should not escalate with 1 drone"
    
    # Drone 2 sends high-risk alert → should trigger escalation
    alert2 = drones[1].process_alert(risk_score=0.80, confidence=0.85, should_alert=True, witnesses=1)
    result2 = queen.receive_drone_alert(alert2)
    assert result2['escalated'] is True, "Should escalate with ≥2 drones"
    assert result2['priority'] == 'P1_CRITICAL'
    assert result2['channel'] == 'SATELLITE'
    assert mesh.stats['alerts_aggregated'] >= 1
    print(f"  ✅ 4. Multi-drone consensus → P1 SATELLITE: {result2['relay_path_display']}")


def test_queen_satellite_uplink():
    """Test: Queen P1 alert goes to satellite"""
    mesh = MeshNetwork(lora_range_meters=2000.0)
    
    queen_loc = GPSCoordinate(-35.72, 150.10)
    queen = RoleAwareCommunicationLayer(
        node_id="QUEEN_001", role="QUEEN", location=queen_loc,
        mesh_network=mesh, has_satellite=True
    )
    
    result = queen.process_alert(
        risk_score=0.95, confidence=0.95, should_alert=True,
        witnesses=3, battery_level=90.0
    )
    
    assert result is not None
    assert result['role'] == 'QUEEN'
    assert result['channel'] == 'SATELLITE'
    assert mesh.stats['queen_to_satellite'] >= 1
    print(f"  ✅ 5. Queen→Satellite uplink: {result['relay_path_display']}")


def test_heartbeat_with_jitter():
    """Test: Drone heartbeat reaches Queen with jitter"""
    mesh = MeshNetwork(lora_range_meters=2000.0)
    
    queen_loc = GPSCoordinate(-35.72, 150.10)
    RoleAwareCommunicationLayer(
        node_id="QUEEN_001", role="QUEEN", location=queen_loc,
        mesh_network=mesh, has_satellite=True
    )
    
    drone_loc = GPSCoordinate(-35.718, 150.097)
    drone = RoleAwareCommunicationLayer(
        node_id="DRONE_001", role="DRONE", location=drone_loc,
        mesh_network=mesh, queen_node_id="QUEEN_001"
    )
    
    hb = drone.send_heartbeat()
    assert hb['node_id'] == 'DRONE_001'
    assert hb['status'] == 'ONLINE'
    assert 'jitter_applied_sec' in hb
    assert mesh.stats['heartbeats_received'] >= 1
    print(f"  ✅ 6. Heartbeat with jitter: {hb['jitter_applied_sec']}s applied")


def test_mesh_topology_serialization():
    """Test: Topology JSON is valid for dashboard"""
    mesh = MeshNetwork(lora_range_meters=2000.0)
    
    mesh.register_node("QUEEN_001", "QUEEN", GPSCoordinate(-35.72, 150.10))
    mesh.register_node("DRONE_001", "DRONE", GPSCoordinate(-35.718, 150.097))
    mesh.register_node("DRONE_002", "DRONE", GPSCoordinate(-35.722, 150.103))
    
    topo = mesh.get_topology()
    
    assert 'nodes' in topo
    assert 'links' in topo
    assert 'queen_id' in topo
    assert 'stats' in topo
    assert len(topo['nodes']) == 3
    
    # Check node structure
    queen = next(n for n in topo['nodes'] if n['is_queen'])
    assert queen['id'] == 'QUEEN_001'
    assert queen['role'] == 'QUEEN'
    
    # Check links
    lora_links = [l for l in topo['links'] if l['type'] == 'lora']
    sat_links = [l for l in topo['links'] if l['type'] == 'satellite']
    assert len(lora_links) == 2, f"Expected 2 LoRa links, got {len(lora_links)}"
    assert len(sat_links) == 1, f"Expected 1 satellite link, got {len(sat_links)}"
    
    print(f"  ✅ 7. Topology serialization: {len(topo['nodes'])} nodes, {len(topo['links'])} links")


def test_drone_cannot_use_satellite():
    """Test: Drone P1 alert still goes to Queen (not satellite)"""
    mesh = MeshNetwork(lora_range_meters=2000.0)
    
    queen_loc = GPSCoordinate(-35.72, 150.10)
    RoleAwareCommunicationLayer(
        node_id="QUEEN_001", role="QUEEN", location=queen_loc,
        mesh_network=mesh, has_satellite=True
    )
    
    drone_loc = GPSCoordinate(-35.718, 150.097)
    drone = RoleAwareCommunicationLayer(
        node_id="DRONE_001", role="DRONE", location=drone_loc,
        mesh_network=mesh, queen_node_id="QUEEN_001"
    )
    
    # High-risk alert that would be P1 on a Queen
    result = drone.process_alert(
        risk_score=0.95, confidence=0.95, should_alert=True,
        witnesses=3, battery_level=90.0
    )
    
    assert result['channel'] == 'LORA_TO_QUEEN', \
        f"Drone should route via LoRa, not {result['channel']}"
    assert 'QUEEN_001' in result['relay_path']
    print(f"  ✅ 8. Drone P1 → LoRa (NOT satellite): {result['relay_path_display']}")


def run_all_tests():
    print()
    print("=" * 70)
    print("  🐝 THE HIVE: Queen-Drone Mesh Network Verification")
    print("=" * 70)
    print()
    
    mesh = test_node_registration()
    test_drone_to_queen_routing(mesh)
    test_role_aware_drone_alert()
    test_queen_aggregation_escalation()
    test_queen_satellite_uplink()
    test_heartbeat_with_jitter()
    test_mesh_topology_serialization()
    test_drone_cannot_use_satellite()
    
    print()
    print("=" * 70)
    print("  ✅ ALL 8 HIVE TESTS PASSED!")
    print("=" * 70)
    
    # Print hackathon-ready summary
    print()
    print("  🏆 HACKATHON ARCHITECTURE SUMMARY:")
    print()
    print("  ┌─────────┐   LoRa    ┌──────────┐   Sat     ┌─────┐")
    print("  │DRONE_001│──────────▶│          │──────────▶│ 🛰️  │")
    print("  └─────────┘           │ QUEEN_001│           └──┬──┘")
    print("  ┌─────────┐   LoRa    │          │              │")
    print("  │DRONE_002│──────────▶│          │              ▼")
    print("  └─────────┘           │          │           ┌─────┐")
    print("  ┌─────────┐   LoRa    │          │           │ 🚒  │")
    print("  │DRONE_003│──────────▶│          │           └─────┘")
    print("  └─────────┘           └──────────┘")
    print()
    print("  KEY FEATURES:")
    print("    ✅ Drones → Queen via LoRa mesh (no satellite)")
    print("    ✅ Queen aggregates multi-drone intelligence")
    print("    ✅ ≥2 Drones = auto-escalate to P1 SATELLITE")
    print("    ✅ Collision-avoidance heartbeats (jitter)")
    print("    ✅ Dashboard-ready mesh topology JSON")
    print("    ✅ Animated visualization in browser")
    print()


if __name__ == "__main__":
    run_all_tests()
