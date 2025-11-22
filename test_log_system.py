"""
Minimal test server to verify the log system without TTS dependencies
"""
import asyncio
import json
import sys
import uuid
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="Log System Test",
    description="Test server for log system",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job Manager for logs
class JobManager:
    """Manages jobs and logs"""

    def __init__(self):
        self.jobs: Dict[str, dict] = {}
        self.websockets: Dict[str, WebSocket] = {}

    def create_job(self, config: dict) -> str:
        """Create a new job and return its ID"""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "config": config,
            "progress": 0,
            "logs": [],
            "created_at": datetime.now().isoformat(),
            "output_files": [],
            "error": None,
        }
        return job_id

    def update_job(self, job_id: str, **kwargs):
        """Update job status and data"""
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)

    def get_job(self, job_id: str) -> Optional[dict]:
        """Get job by ID"""
        return self.jobs.get(job_id)

    async def add_log(self, job_id: str, message: str, level: str = "info"):
        """Add log message to job"""
        if job_id in self.jobs:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
            }
            self.jobs[job_id]["logs"].append(log_entry)

            # Send to WebSocket if connected
            if job_id in self.websockets:
                try:
                    await self.websockets[job_id].send_json({
                        "type": "log",
                        "data": log_entry,
                    })
                except Exception as e:
                    print(f"Failed to send log to WebSocket: {e}")

    async def update_progress(self, job_id: str, progress: float):
        """Update job progress"""
        if job_id in self.jobs:
            self.jobs[job_id]["progress"] = progress

            # Send to WebSocket if connected
            if job_id in self.websockets:
                try:
                    await self.websockets[job_id].send_json({
                        "type": "progress",
                        "data": {"progress": progress},
                    })
                except Exception as e:
                    print(f"Failed to send progress to WebSocket: {e}")

job_manager = JobManager()

# API Endpoints
@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "Log System Test API"}

@app.post("/api/debug/log")
async def debug_log(
    job_id: str = Form(...),
    message: str = Form(...),
    level: str = Form("info"),
):
    """Inject a debug log message"""
    try:
        # Create job if it doesn't exist (for testing without conversion)
        if job_id not in job_manager.jobs:
            job_manager.jobs[job_id] = {
                "id": job_id,
                "status": "debug",
                "config": {},
                "progress": 0,
                "logs": [],
                "created_at": datetime.now().isoformat(),
                "output_files": [],
                "error": None,
            }

        await job_manager.add_log(job_id, message, level)
        return {"status": "success"}
    except Exception as e:
        print(f"Error injecting debug log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and details"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job updates"""
    await websocket.accept()
    job_manager.websockets[job_id] = websocket

    try:
        # Send initial job state
        job = job_manager.get_job(job_id)
        if job:
            await websocket.send_json({"type": "init", "data": job})

        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data:
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        if job_id in job_manager.websockets:
            del job_manager.websockets[job_id]
        print(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        print(f"WebSocket error for job {job_id}: {e}")
        if job_id in job_manager.websockets:
            del job_manager.websockets[job_id]

if __name__ == "__main__":
    import uvicorn
    print("Starting log system test server on http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
