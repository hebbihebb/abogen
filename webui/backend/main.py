"""
FastAPI backend for Abogen Web UI
Provides REST API and WebSocket endpoints for TTS conversion
"""
import asyncio
import json
import logging
import os
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add parent directory to path to import abogen modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from abogen import book_handler, constants, conversion, utils
from abogen.tts_backends import create_tts_engine, get_available_engines
from abogen import voice_profiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Abogen Web UI API",
    description="REST API for Abogen TTS conversion service",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve built frontend if present
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

# Global state management
class JobManager:
    """Manages TTS conversion jobs"""

    def __init__(self):
        self.jobs: Dict[str, dict] = {}
        self.websockets: Dict[str, WebSocket] = {}
        self.temp_dir = Path(tempfile.gettempdir()) / "abogen_webui"
        self.temp_dir.mkdir(exist_ok=True)

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

    def add_log(self, job_id: str, message: str, level: str = "info"):
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
                asyncio.create_task(
                    self.websockets[job_id].send_json({
                        "type": "log",
                        "data": log_entry,
                    })
                )

    def update_progress(self, job_id: str, progress: float):
        """Update job progress"""
        if job_id in self.jobs:
            self.jobs[job_id]["progress"] = progress

            # Send to WebSocket if connected
            if job_id in self.websockets:
                asyncio.create_task(
                    self.websockets[job_id].send_json({
                        "type": "progress",
                        "data": {"progress": progress},
                    })
                )

job_manager = JobManager()


# Pydantic models for API
class TTSConfig(BaseModel):
    """TTS conversion configuration"""
    engine: str = "kokoro"
    voice: str = "af_heart"
    speed: float = 1.0
    voice_formula: Optional[str] = None

    # F5-TTS specific
    reference_audio: Optional[str] = None
    reference_text: Optional[str] = None

    # Subtitle options
    generate_subtitles: str = "disabled"
    subtitle_format: str = "srt"
    max_subtitle_words: int = 10

    # Output options
    output_format: str = "wav"
    replace_single_newlines: bool = False

    # Processing options
    use_gpu: bool = False
    separate_chapters: bool = False
    separate_chapters_format: str = "wav"
    silence_between_chapters: float = 1.0


class JobResponse(BaseModel):
    """Job creation response"""
    job_id: str
    status: str


class VoiceInfo(BaseModel):
    """Voice information"""
    id: str
    name: str
    language: Optional[str] = None


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Abogen Web UI API"}


@app.get("/api/engines")
async def get_engines():
    """Get list of available TTS engines"""
    try:
        engines = get_available_engines()
        return {"engines": engines}
    except Exception as e:
        logger.error(f"Error getting engines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voices/{engine}")
async def get_voices(engine: str):
    """Get available voices for an engine"""
    try:
        if engine == "kokoro":
            # Get Kokoro voices
            voices = []
            for voice_id in constants.VOICES_INTERNAL:
                # Parse language from voice ID (e.g., "af_heart" -> "a")
                lang_code = voice_id[0]
                lang_name = constants.LANGUAGE_DESCRIPTIONS.get(lang_code, "Unknown")
                
                voices.append({
                    "id": voice_id,
                    "name": voice_id,  # Use ID as name since we don't have pretty names
                    "language": lang_name,
                })
            return {"voices": voices}
        elif engine == "f5_tts":
            # F5-TTS uses custom reference audio
            return {"voices": [], "requires_reference": True}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown engine: {engine}")
    except Exception as e:
        logger.error(f"Error getting voices for {engine}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice-profiles")
async def get_voice_profiles():
    """Get saved voice profiles"""
    try:
        profiles = voice_profiles.load_profiles()
        return {"profiles": profiles}
    except Exception as e:
        logger.error(f"Error getting voice profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice-profiles")
async def save_voice_profile(name: str = Form(...), formula: str = Form(...)):
    """Save a voice profile"""
    try:
        profiles = voice_profiles.load_profiles()
        profiles[name] = formula
        voice_profiles.save_profiles(profiles)
        return {"status": "success", "message": f"Profile '{name}' saved"}
    except Exception as e:
        logger.error(f"Error saving voice profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/voice-profiles/{name}")
async def delete_voice_profile(name: str):
    """Delete a voice profile"""
    try:
        profiles = voice_profiles.load_profiles()
        if name in profiles:
            del profiles[name]
            voice_profiles.save_profiles(profiles)
        return {"status": "success", "message": f"Profile '{name}' deleted"}
    except Exception as e:
        logger.error(f"Error deleting voice profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for processing"""
    try:
        # Save uploaded file to temp directory
        file_path = job_manager.temp_dir / f"{uuid.uuid4()}_{file.filename}"

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Extract text based on file type
        file_info = {
            "path": str(file_path),
            "filename": file.filename,
            "size": len(content),
        }

        # Try to extract text preview and chapters
        ext = Path(file.filename).suffix.lower()

        if ext == ".epub":
            chapters = book_handler.extract_epub_chapters(str(file_path))
            file_info["type"] = "epub"
            file_info["chapters"] = [
                {"title": ch.get("title", f"Chapter {i+1}"), "index": i}
                for i, ch in enumerate(chapters)
            ]
        elif ext == ".pdf":
            pages = book_handler.extract_pdf_pages(str(file_path))
            file_info["type"] = "pdf"
            file_info["chapters"] = [
                {"title": f"Page {i+1}", "index": i}
                for i in range(len(pages))
            ]
        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            file_info["type"] = "text"
            file_info["preview"] = text[:500]
            file_info["char_count"] = len(text)
        elif ext in [".srt", ".ass", ".vtt"]:
            file_info["type"] = "subtitle"
        else:
            file_info["type"] = "unknown"

        return file_info
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/convert")
async def start_conversion(
    file_path: str = Form(...),
    config_json: str = Form(...),
):
    """Start a TTS conversion job"""
    try:
        config = json.loads(config_json)

        # Create job
        job_id = job_manager.create_job({
            "file_path": file_path,
            **config,
        })

        # Start conversion in background
        asyncio.create_task(run_conversion(job_id))

        return {"job_id": job_id, "status": "started"}
    except Exception as e:
        logger.error(f"Error starting conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_conversion(job_id: str):
    """Run TTS conversion in background"""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            return

        config = job["config"]
        job_manager.update_job(job_id, status="processing")
        job_manager.add_log(job_id, "Starting TTS conversion...", "info")

        # Load input file
        file_path = config["file_path"]
        job_manager.add_log(job_id, f"Loading file: {Path(file_path).name}", "info")

        # Extract text
        text = ""
        ext = Path(file_path).suffix.lower()

        if ext == ".epub":
            chapters = book_handler.extract_epub_chapters(file_path)
            # Use selected chapters if specified
            selected = config.get("selected_chapters", None)
            if selected:
                chapters = [chapters[i] for i in selected]
            text = "\n\n".join(ch.get("text", "") for ch in chapters)
        elif ext == ".pdf":
            pages = book_handler.extract_pdf_pages(file_path)
            selected = config.get("selected_pages", None)
            if selected:
                pages = [pages[i] for i in selected]
            text = "\n\n".join(pages)
        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        job_manager.add_log(job_id, f"Extracted {len(text)} characters", "info")

        # Initialize TTS backend
        engine = config.get("engine", "kokoro")
        job_manager.add_log(job_id, f"Loading {engine} engine...", "info")

        device = "cuda" if config.get("use_gpu", False) else "cpu"
        backend = create_tts_engine(engine, lang_code="en-us", device=device)

        # Get voice
        voice = config.get("voice", "af_heart")
        voice_formula = config.get("voice_formula")
        reference_audio = config.get("referenceAudio")

        if voice_formula and backend.supports_voice_mixing:
            voice = voice_formula
        elif reference_audio:
            # If reference audio is provided (e.g. for F5-TTS), use it as the voice
            voice = reference_audio

        job_manager.add_log(job_id, f"Using voice: {voice}", "info")

        # Generate audio
        speed = config.get("speed", 1.0)
        job_manager.add_log(job_id, f"Generating audio at {speed}x speed...", "info")

        audio_chunks = []
        total_chunks = 0
        sample_rate = None

        for i, result in enumerate(backend(text, voice, speed, None)):
            audio_chunks.append(result.audio)
            total_chunks += 1
            if sample_rate is None:
                sample_rate = getattr(result, "sample_rate", None)
            progress = min(90, (i + 1) * 10)  # Cap at 90% until encoding
            job_manager.update_progress(job_id, progress)
            job_manager.add_log(job_id, f"Generated chunk {i+1}", "debug")

        job_manager.add_log(job_id, f"Generated {total_chunks} audio chunks", "info")

        if not audio_chunks:
            raise ValueError("No audio was generated; check input text and engine configuration.")
        if sample_rate is None:
            raise ValueError("Sample rate missing from TTS backend output.")

        # Combine audio chunks
        import numpy as np
        combined_audio = np.concatenate(audio_chunks)

        # Save audio file
        output_format = config.get("output_format", "wav")
        output_path = job_manager.temp_dir / f"{job_id}.{output_format}"

        job_manager.add_log(job_id, f"Encoding to {output_format}...", "info")

        # Save using soundfile
        import soundfile as sf
        sf.write(str(output_path), combined_audio, sample_rate)

        job_manager.update_progress(job_id, 100)
        job_manager.add_log(job_id, "Conversion complete!", "success")

        # Update job with output file
        job_manager.update_job(
            job_id,
            status="completed",
            output_files=[str(output_path)],
        )

    except Exception as e:
        logger.error(f"Error in conversion job {job_id}: {e}")
        job_manager.add_log(job_id, f"Error: {str(e)}", "error")
        job_manager.update_job(job_id, status="failed", error=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and details"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/jobs/{job_id}/download")
async def download_job_output(job_id: str):
    """Download job output file"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "completed" or not job["output_files"]:
        raise HTTPException(status_code=400, detail="Job not completed or no output files")

    output_file = job["output_files"][0]
    if not Path(output_file).exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        output_file,
        media_type="application/octet-stream",
        filename=Path(output_file).name,
    )


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
            data = await websocket.receive_text()
            # Echo back for keep-alive
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        if job_id in job_manager.websockets:
            del job_manager.websockets[job_id]


@app.get("/api/config")
async def get_config():
    """Get current abogen configuration"""
    try:
        config = utils.load_config()
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config")
async def update_config(config: dict):
    """Update abogen configuration"""
    try:
        utils.save_config(config)
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/system")
async def system_monitor_websocket(websocket: WebSocket):
    """WebSocket endpoint for system resource monitoring"""
    await websocket.accept()
    try:
        import psutil
        import asyncio
        
        # Try to import GPU monitoring (optional)
        try:
            import pynvml
            pynvml.nvmlInit()
            gpu_available = True
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # First GPU
        except:
            gpu_available = False
        
        while True:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.5)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            
            # Get GPU usage if available
            gpu_percent = None
            if gpu_available:
                try:
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_percent = utilization.gpu
                except:
                    gpu_percent = None
            
            # Send data
            await websocket.send_json({
                "cpu": cpu_percent,
                "memory": memory.percent,
                "gpu": gpu_percent
            })
            
            await asyncio.sleep(2)  # Update every 2 seconds
    except Exception as e:
        logger.info(f"System monitor WebSocket closed: {e}")
    finally:
        if gpu_available:
            try:
                pynvml.nvmlShutdown()
            except:
                pass


@app.post("/api/demo/load")
async def load_demo():
    """Load demo files for testing"""
    try:
        project_root = Path(__file__).parent.parent.parent
        demo_dir = project_root / "demo"
        sample_epub = demo_dir / "sample.epub"
        sample_voice = demo_dir / "t5_voice.wav"

        if not sample_epub.exists() or not sample_voice.exists():
            raise HTTPException(status_code=404, detail="Demo files not found")

        # Copy to temp dir to simulate upload
        temp_epub = job_manager.temp_dir / f"{uuid.uuid4()}_sample.epub"
        temp_voice = job_manager.temp_dir / f"{uuid.uuid4()}_t5_voice.wav"

        import shutil
        shutil.copy2(sample_epub, temp_epub)
        shutil.copy2(sample_voice, temp_voice)

        # Process EPUB
        chapters = book_handler.extract_epub_chapters(str(temp_epub))
        
        epub_info = {
            "path": str(temp_epub),
            "filename": "sample.epub",
            "size": temp_epub.stat().st_size,
            "type": "epub",
            "chapters": [
                {"title": ch.get("title", f"Chapter {i+1}"), "index": i}
                for i, ch in enumerate(chapters)
            ]
        }

        return {
            "file_info": epub_info,
            "reference_audio": str(temp_voice)
        }

    except Exception as e:
        logger.error(f"Error loading demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
