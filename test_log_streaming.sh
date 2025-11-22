#!/bin/bash

# Simple test for real-time log streaming
# This script starts a WebSocket listener and then sends debug logs

# Start monitoring job in background (you need to get job_id from somewhere)
# For now, we'll just show how to test this manually

echo "To test real-time log streaming:"
echo ""
echo "1. Open the WebUI in a browser: http://localhost:5173"
echo "2. Upload a file and click 'Start Conversion'"
echo "3. Watch the logs appear in real-time in the 'Processing Log' section"
echo ""
echo "Expected behavior after fix:"
echo "  - Logs should appear progressively as processing continues"
echo "  - Not all logs at once after conversion completes"
echo ""
echo "Backend is running on http://localhost:8000"
echo "Frontend dev server should be on http://localhost:5173 (if running 'npm run dev')"
