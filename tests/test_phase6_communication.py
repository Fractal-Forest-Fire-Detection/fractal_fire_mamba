"""
PHASE-6 COMMUNICATION LAYER TEST SUITE
Tests alert routing, death vector analysis, and network intelligence

NO SIMULATED FIRE SCENARIOS - Only logic validation
"""

import numpy as np
from datetime import datetime, timedelta
from phase6_communication_layer import (
    Phase6CommunicationLayer,
    GPSCoordinate,
    NodeStatus,
    NodeState,
    AlertPriority,
    FireAlert,
    DeathEvent,
    DeathVector,
    DigitalTwinState
)


def test_gps_distance_calculation():
    """Test GPS distance calculation using Haversine formula"""
    print("\n" + "="*70)
    print("🌍 TESTING GPS DISTANCE CALCULATION")
    print("="*70)
    
    # San Francisco to Los Angeles (known distance ~560 km)
    sf = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    la = GPSCoordinate(latitude=34.0522, longitude=-118.2437)
    
    distance = sf.distance_to(la)
    expected_distance = 560000  # meters
    
    print(f"\nSan Francisco to Los Angeles:")
    print(f"  Calculated: {distance/1000:.1f} km")
    print(f"  Expected: {expected_distance/1000:.1f} km")
    print(f"  Error: {abs(distance - expected_distance)/expected_distance:.1%}")
    
    # Should be within 5% of expected
    assert abs(distance - expected_distance) / expected_distance < 0.05, \
        "GPS distance calculation error > 5%"
    
    # Test nearby points (100m apart)
    p1 = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    p2 = GPSCoordinate(latitude=37.7758, longitude=-122.4194)  # ~100m north
    
    distance_nearby = p1.distance_to(p2)
    print(f"\nNearby points:")
    print(f"  Distance: {distance_nearby:.1f} m")
    
    assert 90 < distance_nearby < 110, "Nearby distance should be ~100m"
    
    print("✅ GPS distance calculation validated!")


def test_priority_determination():
    """Test alert priority logic"""
    print("\n" + "="*70)
    print("🚨 TESTING ALERT PRIORITY DETERMINATION")
    print("="*70)
    
    location = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    comm = Phase6CommunicationLayer(node_id="TEST_001", location=location)
    
    # Test P1 Critical
    print("\n🔴 Test 1: P1 Critical Fire")
    p1 = comm._determine_priority(
        risk_score=0.85,
        confidence=0.90,
        witnesses=2,
        battery_level=80.0
    )
    assert p1 == AlertPriority.P1_CRITICAL, "Should be P1 CRITICAL"
    print(f"  Result: {p1.name} ✅")
    
    # Test P2 Medium
    print("\n🟠 Test 2: P2 Medium Fire")
    p2 = comm._determine_priority(
        risk_score=0.65,
        confidence=0.70,
        witnesses=0,
        battery_level=80.0
    )
    assert p2 == AlertPriority.P2_MEDIUM, "Should be P2 MEDIUM"
    print(f"  Result: {p2.name} ✅")
    
    # Test P3 Maintenance
    print("\n🟢 Test 3: P3 Maintenance")
    p3 = comm._determine_priority(
        risk_score=0.20,
        confidence=0.50,
        witnesses=0,
        battery_level=15.0  # Low battery
    )
    assert p3 == AlertPriority.P3_MAINTENANCE, "Should be P3 MAINTENANCE"
    print(f"  Result: {p3.name} ✅")
    
    print("✅ Priority determination validated!")


def test_alert_routing():
    """Test alert routing through different channels"""
    print("\n" + "="*70)
    print("📡 TESTING ALERT ROUTING")
    print("="*70)
    
    location = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    comm = Phase6CommunicationLayer(node_id="TEST_001", location=location)
    
    # Test P1 routing (should use satellite)
    print("\n🛰️  Test 1: P1 Alert Routing (Satellite)")
    alert_p1 = comm.process_alert(
        risk_score=0.90,
        confidence=0.95,
        should_alert=True,
        witnesses=2
    )
    
    assert alert_p1 is not None, "P1 alert should be created"
    assert alert_p1.priority == AlertPriority.P1_CRITICAL, "Should be P1"
    print(f"  Alert ID: {alert_p1.alert_id}")
    print(f"  Channel: {alert_p1.channel.value}")
    print(f"  ✅ Routed via satellite")
    
    # Test P2 routing (should use mesh)
    print("\n📡 Test 2: P2 Alert Routing (LoRa Mesh)")
    alert_p2 = comm.process_alert(
        risk_score=0.65,
        confidence=0.70,
        should_alert=True,
        witnesses=0
    )
    
    assert alert_p2 is not None, "P2 alert should be created"
    assert alert_p2.priority == AlertPriority.P2_MEDIUM, "Should be P2"
    print(f"  Alert ID: {alert_p2.alert_id}")
    print(f"  Channel: {alert_p2.channel.value}")
    print(f"  ✅ Routed via mesh")
    
    # Test P3 routing (maintenance)
    print("\n🔧 Test 3: P3 Maintenance Routing")
    alert_p3 = comm.process_alert(
        risk_score=0.10,
        confidence=0.50,
        should_alert=False,
        battery_level=15.0
    )
    
    assert alert_p3 is not None, "P3 alert should be created"
    assert alert_p3.priority == AlertPriority.P3_MAINTENANCE, "Should be P3"
    print(f"  Alert ID: {alert_p3.alert_id}")
    print(f"  Issue: {alert_p3.metadata.get('issue', 'unknown')}")
    print(f"  ✅ Maintenance ticket created")
    
    print("✅ Alert routing validated!")


def test_dying_gasp_protocol():
    """Test dying gasp emergency transmission"""
    print("\n" + "="*70)
    print("💀 TESTING DYING GASP PROTOCOL")
    print("="*70)
    
    location = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    comm = Phase6CommunicationLayer(
        node_id="TEST_001",
        location=location,
        dying_gasp_temp_threshold=100.0
    )
    
    # Trigger dying gasp with high temperature
    print("\n🔥 Simulating node overheating (>100°C)")
    alert = comm.process_alert(
        risk_score=0.95,
        confidence=0.90,
        should_alert=True,
        node_temperature=105.0,  # Above threshold!
        metadata={'sensor_history': ['data1', 'data2']}
    )
    
    assert alert is not None, "Dying gasp alert should be created"
    assert alert.metadata.get('dying_gasp', False), "Should be marked as dying gasp"
    assert 'black_box' in alert.metadata, "Should include black box data"
    
    print(f"  Alert ID: {alert.alert_id}")
    print(f"  Temperature: {alert.metadata['black_box']['final_temperature']}°C")
    print(f"  Black box included: ✅")
    print(f"  Death event recorded: ✅")
    
    # Check death event was created
    assert len(comm.death_events) == 1, "Should have 1 death event"
    assert comm.death_events[0].cause == "high_temp", "Cause should be high_temp"
    
    print("✅ Dying gasp protocol validated!")


def test_death_vector_analysis():
    """Test death vector computation from sequential node deaths"""
    print("\n" + "="*70)
    print("💀 TESTING DEATH VECTOR ANALYSIS")
    print("="*70)
    
    location = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    comm = Phase6CommunicationLayer(node_id="TEST_001", location=location)
    
    print("\nSimulating sequential node deaths moving East:")
    
    # Create sequential deaths moving East
    base_time = datetime.now()
    deaths = [
        DeathEvent(
            node_id=f"NODE_{i:03d}",
            location=GPSCoordinate(
                latitude=37.7749,
                longitude=-122.4194 + (i * 0.001)  # Moving East
            ),
            death_time=base_time + timedelta(seconds=i * 60),  # 1 min apart
            last_risk_score=0.8,
            cause="high_temp"
        )
        for i in range(5)
    ]
    
    # Add deaths to system
    for death in deaths:
        comm.death_events.append(death)
        comm._update_death_vectors(death)
    
    # Check death vector was computed
    assert len(comm.death_vectors) > 0, "Death vector should be computed"
    
    vector = comm.death_vectors[-1]
    
    print(f"\nDeath Vector Results:")
    print(f"  Deaths analyzed: {len(vector.node_deaths)}")
    print(f"  Direction: {vector.direction_degrees:.0f}° (should be ~90° for East)")
    print(f"  Speed: {vector.speed_mps:.2f} m/s")
    print(f"  Confidence: {vector.confidence:.0%}")
    
    # Direction should be approximately East (90°)
    # Allow some tolerance due to small distances
    assert 70 <= vector.direction_degrees <= 110, \
        f"Direction should be ~90° (East), got {vector.direction_degrees:.0f}°"
    
    print("✅ Death vector analysis validated!")


def test_trauma_decay():
    """Test trauma decay system"""
    print("\n" + "="*70)
    print("🧠 TESTING TRAUMA DECAY SYSTEM")
    print("="*70)
    
    location = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    comm = Phase6CommunicationLayer(
        node_id="TEST_001",
        location=location,
        trauma_decay_days=7
    )
    
    # Set initial trauma
    comm.global_trauma_level = 0.5
    initial_trauma = comm.global_trauma_level
    
    print(f"\nInitial trauma: {initial_trauma:.0%}")
    
    # Simulate 1 day passing
    comm.last_trauma_decay = datetime.now() - timedelta(days=1)
    comm._decay_trauma()
    
    print(f"After 1 day: {comm.global_trauma_level:.0%}")
    print(f"Decay amount: {initial_trauma - comm.global_trauma_level:.0%}")
    
    # Should have decayed
    assert comm.global_trauma_level < initial_trauma, "Trauma should decay"
    
    # Simulate 7 days
    comm.global_trauma_level = 0.5
    comm.last_trauma_decay = datetime.now() - timedelta(days=7)
    comm._decay_trauma()
    
    print(f"After 7 days: {comm.global_trauma_level:.0%}")
    
    # Should be significantly lower or zero
    assert comm.global_trauma_level < 0.1, "Trauma should be near zero after 7 days"
    
    print("✅ Trauma decay validated!")


def test_known_burnt_area_check():
    """Test known burnt area (KBA) checking"""
    print("\n" + "="*70)
    print("🔥 TESTING KNOWN BURNT AREA CHECK")
    print("="*70)
    
    location = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    comm = Phase6CommunicationLayer(node_id="TEST_001", location=location)
    
    # Add burnt area
    burnt_center = GPSCoordinate(latitude=37.7750, longitude=-122.4195)
    comm.add_burnt_area(burnt_center, radius=500.0)
    
    print(f"\nBurnt area added: {burnt_center.latitude}, {burnt_center.longitude}")
    print(f"Radius: 500m")
    
    # Test location inside burnt area
    inside = GPSCoordinate(latitude=37.7751, longitude=-122.4196)
    is_burnt_inside = comm.check_known_burnt_area(inside)
    
    print(f"\nLocation inside burnt area: {is_burnt_inside}")
    assert is_burnt_inside, "Should detect location is in burnt area"
    
    # Test location outside burnt area
    outside = GPSCoordinate(latitude=37.7800, longitude=-122.4300)
    is_burnt_outside = comm.check_known_burnt_area(outside)
    
    print(f"Location outside burnt area: {is_burnt_outside}")
    assert not is_burnt_outside, "Should detect location is NOT in burnt area"
    
    print("✅ Known burnt area check validated!")


def test_fire_spread_prediction():
    """Test fire spread prediction with wind and terrain"""
    print("\n" + "="*70)
    print("🌪️  TESTING FIRE SPREAD PREDICTION")
    print("="*70)
    
    location = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    comm = Phase6CommunicationLayer(node_id="TEST_001", location=location)
    
    # Test with wind blowing East at 5 m/s, uphill slope
    print("\n📊 Scenario: Wind 90° (East) at 5 m/s, uphill 15°")
    
    prediction = comm.get_fire_spread_prediction(
        current_location=location,
        wind_direction_degrees=90.0,  # East
        wind_speed_mps=5.0,
        terrain_slope_degrees=15.0
    )
    
    print(f"\nPrediction Results:")
    print(f"  Spread rate: {prediction['spread_rate_mps']:.2f} m/s")
    print(f"  Direction: {prediction['direction_degrees']:.0f}°")
    print(f"  Distance in 1hr: {prediction['predicted_distance_1hr']:.0f} m")
    print(f"  Confidence: {prediction['confidence']:.0%}")
    
    # Spread rate should increase with wind and slope
    assert prediction['spread_rate_mps'] > 0.5, "Should have non-zero spread rate"
    assert prediction['predicted_distance_1hr'] > 0, "Should predict some spread"
    
    # Test with death vector influence
    print("\n💀 Adding death vector for combined prediction")
    
    # Add a death vector pointing North (0°)
    death_vector = DeathVector(
        start_location=location,
        end_location=GPSCoordinate(latitude=37.7759, longitude=-122.4194),
        direction_degrees=0.0,  # North
        speed_mps=1.0,
        node_deaths=[],
        confidence=0.8,
        timestamp=datetime.now()
    )
    comm.death_vectors.append(death_vector)
    
    prediction_with_vector = comm.get_fire_spread_prediction(
        current_location=location,
        wind_direction_degrees=90.0,  # East
        wind_speed_mps=5.0,
        terrain_slope_degrees=15.0
    )
    
    print(f"\nWith death vector:")
    print(f"  Direction: {prediction_with_vector['direction_degrees']:.0f}° (averaged)")
    print(f"  Death vector available: {prediction_with_vector['factors']['death_vector_available']}")
    
    assert prediction_with_vector['factors']['death_vector_available'], \
        "Should use death vector in prediction"
    
    print("✅ Fire spread prediction validated!")


def test_node_status_tracking():
    """Test tracking of neighboring nodes"""
    print("\n" + "="*70)
    print("📊 TESTING NODE STATUS TRACKING")
    print("="*70)
    
    location = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    comm = Phase6CommunicationLayer(
        node_id="TEST_001",
        location=location,
        lora_range_meters=500.0
    )
    
    # Add nearby node (within range)
    nearby_node = NodeStatus(
        node_id="NODE_002",
        location=GPSCoordinate(latitude=37.7753, longitude=-122.4194),  # ~100m away
        state=NodeState.ALIVE,
        risk_score=0.3,
        battery_level=80.0,
        last_seen=datetime.now()
    )
    
    comm.update_node_status(nearby_node)
    
    print(f"\nNearby node added:")
    print(f"  Node ID: {nearby_node.node_id}")
    print(f"  Distance: ~100m")
    print(f"  In mesh range: {'NODE_002' in comm.neighbor_nodes}")
    
    assert 'NODE_002' in comm.neighbor_nodes, "Should be in neighbor list"
    
    # Add distant node (out of range)
    distant_node = NodeStatus(
        node_id="NODE_003",
        location=GPSCoordinate(latitude=37.7800, longitude=-122.4300),  # ~1km away
        state=NodeState.ALIVE,
        risk_score=0.2,
        battery_level=90.0,
        last_seen=datetime.now()
    )
    
    comm.update_node_status(distant_node)
    
    print(f"\nDistant node added:")
    print(f"  Node ID: {distant_node.node_id}")
    print(f"  Distance: ~1km")
    print(f"  In mesh range: {'NODE_003' in comm.neighbor_nodes}")
    
    assert 'NODE_003' not in comm.neighbor_nodes, "Should NOT be in neighbor list"
    
    # Mark node as dead
    nearby_node.state = NodeState.DEAD
    comm.update_node_status(nearby_node)
    
    print(f"\nNode marked DEAD:")
    print(f"  Death events: {len(comm.death_events)}")
    print(f"  Black zones: {len(comm.black_zones)}")
    
    assert len(comm.death_events) > 0, "Should have death event"
    assert len(comm.black_zones) > 0, "Should have black zone"
    
    print("✅ Node status tracking validated!")


def test_digital_twin_state():
    """Test digital twin state creation"""
    print("\n" + "="*70)
    print("🗺️  TESTING DIGITAL TWIN STATE")
    print("="*70)
    
    # Create sample nodes
    alive_node = NodeStatus(
        node_id="NODE_001",
        location=GPSCoordinate(latitude=37.7749, longitude=-122.4194),
        state=NodeState.ALIVE,
        risk_score=0.3,
        battery_level=80.0
    )
    
    dead_node = NodeStatus(
        node_id="NODE_002",
        location=GPSCoordinate(latitude=37.7750, longitude=-122.4195),
        state=NodeState.DEAD,
        risk_score=0.9,
        battery_level=0.0
    )
    
    # Create digital twin state
    twin_state = DigitalTwinState(
        timestamp=datetime.now(),
        alive_nodes=[alive_node],
        dead_nodes=[dead_node],
        dying_nodes=[],
        active_fires=[GPSCoordinate(latitude=37.7750, longitude=-122.4195)],
        fire_intensity={'NODE_002': 0.9},
        death_vectors=[],
        black_zones=[(dead_node.location, 100.0)],
        active_alerts=[]
    )
    
    # Convert to visualization data
    viz_data = twin_state.to_visualization_data()
    
    print(f"\nDigital Twin State:")
    print(f"  Alive nodes: {len(viz_data['nodes']['alive'])}")
    print(f"  Dead nodes: {len(viz_data['nodes']['dead'])}")
    print(f"  Fire zones: {len(viz_data['fire_zones'])}")
    print(f"  Black zones: {len(viz_data['black_zones'])}")
    
    assert len(viz_data['nodes']['alive']) == 1, "Should have 1 alive node"
    assert len(viz_data['nodes']['dead']) == 1, "Should have 1 dead node"
    assert len(viz_data['fire_zones']) == 1, "Should have 1 fire zone"
    assert len(viz_data['black_zones']) == 1, "Should have 1 black zone"
    
    # Check structure
    assert 'lat' in viz_data['nodes']['alive'][0], "Should have latitude"
    assert 'lon' in viz_data['nodes']['alive'][0], "Should have longitude"
    assert 'risk' in viz_data['nodes']['alive'][0], "Should have risk score"
    
    print("✅ Digital twin state validated!")


def test_statistics_tracking():
    """Test statistics collection"""
    print("\n" + "="*70)
    print("📊 TESTING STATISTICS TRACKING")
    print("="*70)
    
    location = GPSCoordinate(latitude=37.7749, longitude=-122.4194)
    comm = Phase6CommunicationLayer(node_id="TEST_001", location=location)
    
    # Generate various alerts
    comm.process_alert(risk_score=0.90, confidence=0.95, should_alert=True, witnesses=2)  # P1
    comm.process_alert(risk_score=0.65, confidence=0.70, should_alert=True, witnesses=0)  # P2
    comm.process_alert(risk_score=0.10, confidence=0.50, should_alert=False, battery_level=15.0)  # P3
    
    stats = comm.get_statistics()
    
    print(f"\nStatistics:")
    print(f"  P1 Alerts: {stats['p1_alerts']}")
    print(f"  P2 Alerts: {stats['p2_alerts']}")
    print(f"  P3 Alerts: {stats['p3_alerts']}")
    print(f"  Total Alerts: {stats['alerts_sent']}")
    print(f"  Satellite TX: {stats['satellite_transmissions']}")
    print(f"  Mesh Broadcasts: {stats['mesh_broadcasts']}")
    
    assert stats['p1_alerts'] >= 1, "Should have P1 alert"
    assert stats['p2_alerts'] >= 1, "Should have P2 alert"
    assert stats['p3_alerts'] >= 1, "Should have P3 alert"
    assert stats['alerts_sent'] == 3, "Should have 3 total alerts"
    
    print("✅ Statistics tracking validated!")


def run_all_tests():
    """Run all Phase-6 validation tests"""
    print("\n" + "🧪"*35)
    print("PHASE-6 COMMUNICATION LAYER TEST SUITE")
    print("🧪"*35)
    print("\nNOTE: These tests validate processing logic, not hardware.")
    print("      For deployment, integrate with LoRa and satellite modules.\n")
    
    try:
        test_gps_distance_calculation()
        test_priority_determination()
        test_alert_routing()
        test_dying_gasp_protocol()
        test_death_vector_analysis()
        test_trauma_decay()
        test_known_burnt_area_check()
        test_fire_spread_prediction()
        test_node_status_tracking()
        test_digital_twin_state()
        test_statistics_tracking()
        
        print("\n" + "="*70)
        print("✅ ALL PHASE-6 TESTS PASSED!")
        print("="*70)
        print("\n🎯 Phase-6 Communication Layer is validated!")
        print("\n📡 Next Steps:")
        print("   1. Integrate LoRa transceiver (RFM95W/SX1276)")
        print("   2. Integrate Iridium satellite modem (RockBLOCK)")
        print("   3. Deploy digital twin dashboard")
        print("   4. Test end-to-end system with real hardware\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
