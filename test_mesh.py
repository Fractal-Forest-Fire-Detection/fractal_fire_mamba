
try:
    import sys
    import os
    sys.path.append(os.getcwd())
    from phases.phase6_communication.communication_layer import MeshNetwork, GPSCoordinate
    
    print("Initializing MeshNetwork...")
    mesh = MeshNetwork()
    
    print("Registering nodes...")
    mesh.register_node("QUEEN_001", "QUEEN", GPSCoordinate(-35.0, 150.0))
    mesh.register_node("D_001", "DRONE", GPSCoordinate(-35.001, 150.001))
    
    print("Generating topology...")
    topo = mesh.get_topology()
    
    node = topo['nodes'][0]
    print(f"Node keys: {list(node.keys())}")
    
    if 'sensors' in node:
        print(f"BME688: {node['sensors'].get('bme688')}")
        print(f"Soil: {node['sensors'].get('capacitive_soil')}")
        if 'humidity_pct' in node['sensors']['bme688']:
            print("SUCCESS: Humidity data present.")
        else:
            print("FAILURE: Humidity data MISSING.")
            
        if 'capacitive_soil' in node['sensors']:
            print("SUCCESS: Soil data present.")
        else:
            print("FAILURE: Soil data MISSING.")
    else:
        print("FAILURE: Sensors dict missing.")

except Exception as e:
    import traceback
    traceback.print_exc()
