#!/usr/bin/env python3
"""
Simple test script to verify the log display system works end-to-end
"""
import asyncio
import json
import sys
import websockets
import requests
import time

API_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"

async def test_log_system():
    print("Testing log system...")

    # 1. Create a debug job
    print("\n1. Creating debug job...")
    job_id = f"test-debug-{int(time.time())}"

    # 2. Connect to WebSocket
    print(f"2. Connecting to WebSocket for job {job_id}...")
    ws_url = f"{WS_URL}/ws/{job_id}"

    logs_received = []

    try:
        async with websockets.connect(ws_url) as websocket:
            print("   WebSocket connected ✓")

            # Get initial state
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(message)
                if data["type"] == "init":
                    print(f"   Received init message ✓")
                    print(f"   Job exists in backend: {data['data']['id']}")
            except asyncio.TimeoutError:
                print("   No init message received (job not yet created)")

            # 3. Send some test logs via the debug endpoint
            print("\n3. Sending test log messages...")
            test_messages = [
                ("Test info message", "info"),
                ("Test warning message", "warning"),
                ("Test error message", "error"),
                ("Test success message", "success"),
                ("Test debug message", "debug"),
            ]

            for message_text, level in test_messages:
                try:
                    # Send via debug endpoint
                    response = requests.post(
                        f"{API_URL}/api/debug/log",
                        data={
                            "job_id": job_id,
                            "message": message_text,
                            "level": level,
                        }
                    )

                    if response.status_code == 200:
                        print(f"   ✓ Sent: [{level}] {message_text}")
                    else:
                        print(f"   ✗ Failed to send log: {response.text}")

                    # Wait a bit and try to receive the log via WebSocket
                    try:
                        log_message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        log_data = json.loads(log_message)
                        if log_data["type"] == "log":
                            logs_received.append(log_data["data"])
                            print(f"     Received via WebSocket ✓")
                    except asyncio.TimeoutError:
                        print(f"     No WebSocket message (might still be in queue)")

                except Exception as e:
                    print(f"   ✗ Error: {e}")

            # 4. Wait a moment and check for any remaining messages
            print("\n4. Checking for remaining messages...")
            try:
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        if data["type"] == "log":
                            logs_received.append(data["data"])
                            print(f"   Received: [{data['data']['level']}] {data['data']['message']}")
                    except asyncio.TimeoutError:
                        break
            except Exception as e:
                print(f"   Error checking messages: {e}")

    except Exception as e:
        print(f"WebSocket connection error: {e}")

    # 5. Check job status via REST API
    print("\n5. Checking job status via REST API...")
    try:
        response = requests.get(f"{API_URL}/api/jobs/{job_id}")
        if response.status_code == 200:
            job_data = response.json()
            print(f"   Job status: {job_data['status']}")
            print(f"   Total logs in backend: {len(job_data['logs'])}")

            if job_data['logs']:
                print("   Sample logs:")
                for log in job_data['logs'][:3]:
                    print(f"     - [{log['level']}] {log['message']}")
    except Exception as e:
        print(f"   Error fetching job status: {e}")

    # 6. Verify results
    print("\n--- Test Results ---")
    if len(logs_received) > 0:
        print(f"✓ SUCCESS: Received {len(logs_received)} log messages via WebSocket")
        print(f"✓ Log messages were properly transmitted from backend to client")
        return True
    else:
        print("✗ FAILURE: No log messages received via WebSocket")
        print("  Logs may have been stored but not transmitted in real-time")
        # Check if logs are at least in the backend
        try:
            response = requests.get(f"{API_URL}/api/jobs/{job_id}")
            if response.status_code == 200:
                job_data = response.json()
                if job_data['logs']:
                    print(f"  However, {len(job_data['logs'])} logs were stored in the backend")
                    print("  Issue: Logs not being sent via WebSocket")
                    return False
        except:
            pass
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_log_system())
        sys.exit(0 if success else 1)
    except ImportError:
        print("websockets library not found. Please install it: pip install websockets")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
