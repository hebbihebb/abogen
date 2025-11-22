import asyncio
import json
import sys
import websockets
import requests
import time

API_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"

async def verify_logs():
    print(f"Testing against {API_URL}")

    # 1. Load Demo
    print("Loading demo...")
    try:
        response = requests.post(f"{API_URL}/api/demo/load")
        response.raise_for_status()
        data = response.json()
        file_info = data["file_info"]
        reference_audio = data["reference_audio"]
        print(f"Demo loaded: {file_info['filename']}")
    except Exception as e:
        print(f"Failed to load demo: {e}")
        return

    # 2. Start Conversion
    print("Starting conversion...")
    config = {
        "engine": "kokoro", # Use kokoro for speed/reliability in test
        "voice": "af_heart",
        "speed": 1.0,
        "output_format": "wav",
        "use_gpu": False # Use CPU to avoid GPU issues in test env
    }
    
    payload = {
        "file_path": file_info["path"],
        "config_json": json.dumps(config)
    }
    
    try:
        response = requests.post(f"{API_URL}/api/convert", data=payload)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"Job started: {job_id}")
    except Exception as e:
        print(f"Failed to start conversion: {e}")
        return

    # 3. Connect to WebSocket
    print(f"Connecting to WebSocket for job {job_id}...")
    ws_url = f"{WS_URL}/ws/{job_id}"
    
    logs_received = []
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("WebSocket connected")
            
            # Wait for messages
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    
                    if data["type"] == "log":
                        log = data["data"]
                        print(f"Log received: [{log['level']}] {log['message']}")
                        logs_received.append(log)
                    elif data["type"] == "init":
                        print("Init message received")
                        if "logs" in data["data"]:
                            print(f"Init logs: {len(data['data']['logs'])}")
                            logs_received.extend(data["data"]["logs"])
                    elif data["type"] == "progress":
                        print(f"Progress: {data['data']['progress']}%")
                        if data["data"]["progress"] >= 100:
                            print("Conversion complete")
                            break
                            
                except asyncio.TimeoutError:
                    print("Timeout waiting for message")
                    break
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    break
                    
    except Exception as e:
        print(f"WebSocket connection failed: {e}")

    # 4. Verify Logs
    print("\n--- Verification Results ---")
    if len(logs_received) > 0:
        print(f"SUCCESS: Received {len(logs_received)} log messages.")
        return True
    else:
        print("FAILURE: No log messages received.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(verify_logs())
        if not success:
            sys.exit(1)
    except ImportError:
        print("websockets library not found. Please install it.")
        sys.exit(1)
