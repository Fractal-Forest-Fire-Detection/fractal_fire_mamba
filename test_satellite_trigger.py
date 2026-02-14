import requests
import json

API_URL = "http://127.0.0.1:8000/api/satellite/analyze"

payload = {
    "image_filename": "Orroral_Valley_Fire_viewed_from_Tuggeranong_January_2020.jpg"
}

try:
    print(f"📡 Sending Satellite Analysis Request to {API_URL}...")
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ SUCCESS! Server responded:")
        print(json.dumps(data, indent=2))
        
        if data.get('mamba', {}).get('confidence') > 0.6:
            print("\n🔥 ALERT TRIGGERED: Fire Detected!")
            print(f"Speedup: {data.get('speedup_factor')}x faster than CNN")
        else:
            print("\n❄️ No Fire Detected (or confidence low).")
    else:
        print(f"\n❌ FAILED: Status {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
