#!/usr/bin/env python3
"""Test script to verify real-time log streaming via WebSocket"""

import asyncio
import json
import websockets
import time
from datetime import datetime

async def test_websocket_logs(job_id):
    """Connect to WebSocket and monitor logs in real-time"""
    uri = f"ws://localhost:8000/ws/{job_id}"

    print(f"\n{'='*60}")
    print(f"Testing WebSocket for job: {job_id}")
    print(f"Connecting to: {uri}")
    print(f"{'='*60}\n")

    received_messages = []
    init_received = False

    try:
        async with websockets.connect(uri) as websocket:
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Connected to WebSocket")

            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                    if data['type'] == 'init':
                        init_received = True
                        init_data = data['data']
                        print(f"[{timestamp}] INIT message received")
                        print(f"  - Job status: {init_data.get('status')}")
                        print(f"  - Progress: {init_data.get('progress')}%")
                        print(f"  - Has logs key: {'logs' in init_data}")
                        if 'logs' in init_data and init_data['logs']:
                            print(f"  WARNING: Init message contains {len(init_data['logs'])} logs (should be empty!)")
                        print()

                    elif data['type'] == 'log':
                        log_entry = data['data']
                        timestamp_str = log_entry.get('timestamp', '')
                        level = log_entry.get('level', 'info').upper()
                        message_text = log_entry.get('message', '')

                        received_messages.append(log_entry)
                        current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        print(f"[{current_time}] [{level:7}] {message_text}")

                    elif data['type'] == 'progress':
                        progress = data['data'].get('progress', 0)
                        current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        print(f"[{current_time}] [PROGRESS] {progress}%")

                except asyncio.TimeoutError:
                    # Keep connection alive
                    continue

    except Exception as e:
        print(f"WebSocket error: {e}")

    print(f"\n{'='*60}")
    print(f"Test Results:")
    print(f"  - Init received: {init_received}")
    print(f"  - Total log messages: {len(received_messages)}")
    if received_messages:
        print(f"  - First log: {received_messages[0]['message']}")
        print(f"  - Last log: {received_messages[-1]['message']}")
    print(f"{'='*60}\n")

    return received_messages

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_realtime_logs.py <job_id>")
        print("\nExample: python test_realtime_logs.py debug-1234567890")
        sys.exit(1)

    job_id = sys.argv[1]
    asyncio.run(test_websocket_logs(job_id))
