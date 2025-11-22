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


def _get_file_type(suffix: str) -> str:
    """Determine file type from extension"""
    audio_exts = {'.wav', '.mp3', '.m4b', '.opus', '.flac', '.ogg', '.aac'}
    subtitle_exts = {'.srt', '.ass', '.vtt'}

    suffix_lower = suffix.lower()
    if suffix_lower in audio_exts:
        return 'audio'
    elif suffix_lower in subtitle_exts:
        return 'subtitle'
    else:
        return 'other'


def _format_srt_time(seconds: float) -> str:
    """Format time in SRT format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _write_srt_subtitles(path: Path, entries: list):
    """Write SRT subtitle file"""
    with open(path, 'w', encoding='utf-8') as f:
        for i, (start, end, text) in enumerate(entries, 1):
            f.write(f"{i}\n")
            f.write(f"{_format_srt_time(start)} --> {_format_srt_time(end)}\n")
            f.write(f"{text}\n\n")


def _write_vtt_subtitles(path: Path, entries: list):
    """Write VTT subtitle file"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for start, end, text in entries:
            f.write(f"{_format_srt_time(start)} --> {_format_srt_time(end)}\n")
            f.write(f"{text}\n\n")


def _write_ass_subtitles(path: Path, entries: list, style: str = "ass_wide"):
    """Write ASS/SSA subtitle file with styling"""
    with open(path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("[Script Info]\n")
        f.write("Title: Abogen Subtitles\n")
        f.write("ScriptType: v4.00+\n\n")

        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write("Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n")

        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for start, end, text in entries:
            start_time = _format_ass_time(start)
            end_time = _format_ass_time(end)
            f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n")


def _format_ass_time(seconds: float) -> str:
    """Format time in ASS format (H:MM:SS.cc)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

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
# Serve built frontend if present - MOVED TO END
# FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
# if FRONTEND_DIST.exists():
#     app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

# Global state management
class JobManager:
    """Manages TTS conversion jobs"""

    def __init__(self):
        self.jobs: Dict[str, dict] = {}
        self.websockets: Dict[str, WebSocket] = {}
        self.temp_dir = Path(tempfile.gettempdir()) / "abogen_webui"
        self.temp_dir.mkdir(exist_ok=True)

        # Set up persistent output directory
        project_root = Path(__file__).parent.parent.parent
        self.output_dir = project_root / "output"
        self.output_dir.mkdir(exist_ok=True)

    def create_output_folder(self, input_filename: str) -> Path:
        """Create a unique output folder for a job based on input filename"""
        # Sanitize the filename to be filesystem-safe
        sanitized = "".join(c for c in Path(input_filename).stem if c.isalnum() or c in (' ', '-', '_'))
        if not sanitized:
            sanitized = "output"

        folder_path = self.output_dir / sanitized
        folder_path.mkdir(exist_ok=True)
        return folder_path

    def create_job(self, config: dict) -> str:
        """Create a new job and return its ID"""
        job_id = str(uuid.uuid4())
        input_filename = Path(config.get("file_path", "output")).name
        output_folder = self.create_output_folder(input_filename)

        self.jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "config": config,
            "progress": 0,
            "logs": [],
            "created_at": datetime.now().isoformat(),
            "output_folder": str(output_folder),
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
                    logger.debug(f"Failed to send log to WebSocket: {e}")

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
                    logger.debug(f"Failed to send progress to WebSocket: {e}")

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
@app.get("/api/health")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Abogen Web UI API"}


@app.get("/api/engines")
async def get_engines():
    """Get list of available TTS engines"""
    try:
        # Return both available engines for the web UI
        # Kokoro is always available, F5-TTS is available for voice cloning
        engines = ["kokoro", "f5_tts"]
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
        profiles_dict = voice_profiles.load_profiles()
        # Convert dict to array of objects for frontend
        profiles_array = [
            {"name": name, "formula": formula}
            for name, formula in profiles_dict.items()
        ]
        return {"profiles": profiles_array}
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


def _convert_camel_to_snake(config: dict) -> dict:
    """Convert camelCase keys to snake_case for backend compatibility"""
    key_mapping = {
        "outputFormat": "output_format",
        "generateSubtitles": "generate_subtitles",
        "subtitleFormat": "subtitle_format",
        "maxSubtitleWords": "max_subtitle_words",
        "voiceFormula": "voice_formula",
        "referenceAudio": "reference_audio",
        "referenceText": "reference_text",
        "useGpu": "use_gpu",
        "separateChapters": "separate_chapters",
        "separateChaptersFormat": "separate_chapters_format",
        "silenceBetweenChapters": "silence_between_chapters",
        "replaceSingleNewlines": "replace_single_newlines",
        "selectedChapters": "selected_chapters",
        "selectedPages": "selected_pages",
    }

    converted = {}
    for key, value in config.items():
        # Use mapped name if it exists, otherwise keep original
        new_key = key_mapping.get(key, key)
        converted[new_key] = value

    return converted


@app.post("/api/convert")
async def start_conversion(
    file_path: str = Form(...),
    config_json: str = Form(...),
):
    """Start a TTS conversion job"""
    try:
        config = json.loads(config_json)
        # Convert camelCase keys to snake_case
        config = _convert_camel_to_snake(config)

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
        output_folder = Path(job.get("output_folder", ""))  # Get output folder set at job creation
        job_manager.update_job(job_id, status="processing")
        await job_manager.add_log(job_id, "Starting TTS conversion...", "info")

        # Load input file
        file_path = config["file_path"]
        await job_manager.add_log(job_id, f"Loading file: {Path(file_path).name}", "info")

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

        await job_manager.add_log(job_id, f"Extracted {len(text)} characters", "info")

        # Initialize TTS backend
        engine = config.get("engine", "kokoro")
        await job_manager.add_log(job_id, f"Loading {engine} engine...", "info")

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

        await job_manager.add_log(job_id, f"Using voice: {voice}", "info")

        # Generate audio
        speed = config.get("speed", 1.0)
        await job_manager.add_log(job_id, f"Generating audio at {speed}x speed...", "info")

        audio_chunks = []
        subtitle_entries = []
        total_chunks = 0
        sample_rate = None
        current_time = 0.0

        for i, result in enumerate(backend(text, voice, speed, None)):
            audio_chunks.append(result.audio)
            total_chunks += 1
            if sample_rate is None:
                sample_rate = getattr(result, "sample_rate", None)

            # Track chunk timing
            chunk_duration = len(result.audio) / sample_rate if sample_rate else 0

            # Capture subtitle data if available
            if hasattr(result, 'subtitle_data') and result.subtitle_data:
                subtitle_entries.extend(result.subtitle_data)
            elif hasattr(result, 'graphemes') and result.graphemes:
                # Collect graphemes for subtitle generation (even if disabled now, might be useful)
                grapheme_count = len(result.graphemes)
                if grapheme_count > 0:
                    time_per_grapheme = chunk_duration / grapheme_count
                    for grapheme in result.graphemes:
                        grapheme_end = current_time + time_per_grapheme
                        if grapheme.strip():  # Only add non-empty graphemes
                            subtitle_entries.append((current_time, grapheme_end, grapheme))
                        current_time = grapheme_end
                else:
                    current_time += chunk_duration
            else:
                # No graphemes available, just track time
                current_time += chunk_duration

            progress = min(90, (i + 1) * 10)  # Cap at 90% until encoding
            await job_manager.update_progress(job_id, progress)
            await job_manager.add_log(job_id, f"Generated chunk {i+1}", "debug")

        await job_manager.add_log(job_id, f"Generated {total_chunks} audio chunks", "info")

        if not audio_chunks:
            raise ValueError("No audio was generated; check input text and engine configuration.")
        if sample_rate is None:
            raise ValueError("Sample rate missing from TTS backend output.")

        # Combine audio chunks
        import numpy as np
        combined_audio = np.concatenate(audio_chunks)

        # Save audio file to output folder
        output_format = config.get("output_format", "wav").lower()
        generate_subtitles = config.get("generate_subtitles", "disabled")
        subtitle_format = config.get("subtitle_format", "srt")

        await job_manager.add_log(job_id, f"DEBUG: Output format: {output_format}, Subtitles: {generate_subtitles}, Entries collected: {len(subtitle_entries)}", "info")

        # Ensure output folder exists
        output_folder.mkdir(parents=True, exist_ok=True)

        # Get base filename from input file
        input_filename = Path(file_path).stem

        # First save as WAV (intermediate format)
        temp_wav_path = output_folder / f"{input_filename}_temp.wav"
        await job_manager.add_log(job_id, "Encoding audio...", "info")

        import soundfile as sf
        sf.write(str(temp_wav_path), combined_audio, sample_rate)

        # Convert to requested format if not WAV
        output_path = output_folder / f"{input_filename}.{output_format}"

        if output_format != "wav":
            await job_manager.add_log(job_id, f"Converting to {output_format}...", "info")
            import subprocess
            try:
                subprocess.run(
                    ["ffmpeg", "-i", str(temp_wav_path), "-q:a", "9", str(output_path)],
                    capture_output=True,
                    check=True,
                    timeout=300
                )
                # Remove temp WAV file
                temp_wav_path.unlink()
            except subprocess.CalledProcessError as e:
                await job_manager.add_log(job_id, f"FFmpeg error: {e.stderr.decode()}", "error")
                raise
        else:
            # If WAV format, just rename the temp file
            temp_wav_path.rename(output_path)

        await job_manager.update_progress(job_id, 95)
        await job_manager.add_log(job_id, "Encoding complete!", "info")

        # Generate subtitles if enabled
        output_files = []
        if generate_subtitles != "disabled" and subtitle_entries:
            await job_manager.add_log(job_id, f"Generating {subtitle_format} subtitles...", "info")
            subtitle_path = output_folder / f"{input_filename}.{subtitle_format}"

            if subtitle_format == "srt":
                _write_srt_subtitles(subtitle_path, subtitle_entries)
            elif subtitle_format.startswith("ass"):
                _write_ass_subtitles(subtitle_path, subtitle_entries, subtitle_format)
            else:
                _write_vtt_subtitles(subtitle_path, subtitle_entries)

            if subtitle_path.exists():
                file_stat = subtitle_path.stat()
                output_files.append({
                    "name": subtitle_path.name,
                    "path": str(subtitle_path),
                    "size": file_stat.st_size,
                    "type": "subtitle"
                })

        # Add main audio file to output files
        if output_path.exists():
            file_stat = output_path.stat()
            output_files.insert(0, {  # Insert at beginning so audio is first
                "name": output_path.name,
                "path": str(output_path),
                "size": file_stat.st_size,
                "type": "audio"
            })

        await job_manager.update_progress(job_id, 100)
        await job_manager.add_log(job_id, "Conversion complete!", "success")

        # Update job with output files
        job_manager.update_job(
            job_id,
            status="completed",
            output_files=output_files,
        )

    except Exception as e:
        logger.error(f"Error in conversion job {job_id}: {e}")
        await job_manager.add_log(job_id, f"Error: {str(e)}", "error")
        job_manager.update_job(job_id, status="failed", error=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and details"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/conversion-status")
async def get_conversion_status():
    """
    Get current conversion status from WebUI and desktop app.
    Returns information about active conversions from either source.
    """
    # Check for active WebUI conversions
    for job_id, job in job_manager.jobs.items():
        if job["status"] == "processing":
            return {
                "active": True,
                "source": "webui",
                "job_id": job_id,
                "progress": job.get("progress", 0),
                "current_file": job.get("config", {}).get("file_path", "Unknown"),
            }

    # Check for active desktop app conversion
    # Desktop app stores conversion status in a lock file
    desktop_lock_file = Path.home() / ".abogen" / "conversion.lock"
    if desktop_lock_file.exists():
        try:
            with open(desktop_lock_file, 'r') as f:
                desktop_status = json.load(f)
                # Validate lock file is still active (not stale)
                if desktop_status.get("is_converting", False):
                    return {
                        "active": True,
                        "source": "desktop",
                        "progress": desktop_status.get("progress", 0),
                        "current_file": desktop_status.get("current_file", "Unknown"),
                    }
        except (json.JSONDecodeError, IOError) as e:
            logger.debug(f"Error reading desktop lock file: {e}")

    # No active conversions
    return {
        "active": False,
        "source": None,
        "progress": 0,
        "current_file": None,
    }


@app.get("/api/jobs/{job_id}/files")
async def get_job_files(job_id: str):
    """Get list of files in job output folder"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    output_folder = Path(job.get("output_folder", ""))
    if not output_folder.exists():
        return {"folder": str(output_folder), "files": []}

    files = []
    for file_path in sorted(output_folder.iterdir()):
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "name": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "type": _get_file_type(file_path.suffix),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    return {
        "folder": str(output_folder),
        "files": files
    }


@app.get("/api/jobs/{job_id}/files/{filename}")
async def download_job_file(job_id: str, filename: str):
    """Download a specific file from job output folder"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    output_folder = Path(job.get("output_folder", ""))
    file_path = output_folder / filename

    # Security: ensure the file is within the output folder
    try:
        file_path.resolve().relative_to(output_folder.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        str(file_path),
        media_type="application/octet-stream",
        filename=file_path.name,
    )


@app.get("/api/jobs/{job_id}/download")
async def download_job_output(job_id: str):
    """Download job output file (main audio file for backward compatibility)"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "completed" or not job["output_files"]:
        raise HTTPException(status_code=400, detail="Job not completed or no output files")

    # Get first audio file
    output_files = job["output_files"]
    if not output_files:
        raise HTTPException(status_code=404, detail="No output files")

    # Handle both old format (string) and new format (dict)
    if isinstance(output_files[0], dict):
        output_file = output_files[0]["path"]
    else:
        output_file = output_files[0]

    if not Path(output_file).exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        output_file,
        media_type="application/octet-stream",
        filename=Path(output_file).name,
    )


@app.websocket("/ws/system")
async def system_monitor_websocket(websocket: WebSocket):
    """WebSocket endpoint for system resource monitoring"""
    await websocket.accept()
    logger.info("System monitor WebSocket connected")

    gpu_available = False
    handle = None

    try:
        import psutil

        # Try to import GPU monitoring (optional)
        try:
            import pynvml
            pynvml.nvmlInit()
            gpu_available = True
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # First GPU
            logger.info("GPU monitoring enabled")
        except Exception as e:
            logger.info(f"GPU monitoring not available: {e}")
            gpu_available = False

        logger.info("Starting system monitor loop")
        while True:
            try:
                # Get CPU usage with proper blocking interval on first call
                # Initial call with interval to initialize the sampling
                cpu_percent = psutil.cpu_percent(interval=0.1)

                # Get memory usage
                memory = psutil.virtual_memory()

                # Get GPU usage if available
                gpu_percent = None
                if gpu_available and handle:
                    try:
                        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        gpu_percent = utilization.gpu
                    except Exception as e:
                        logger.debug(f"Error getting GPU stats: {e}")
                        gpu_percent = None

                # Send data
                logger.debug(f"Sending system stats: CPU={cpu_percent}%, Mem={memory.percent}%")
                await websocket.send_json({
                    "cpu": cpu_percent,
                    "memory": memory.percent,
                    "gpu": gpu_percent
                })
            except Exception as e:
                logger.error(f"Error in system monitor loop: {type(e).__name__}: {e}")
                break

            await asyncio.sleep(2)  # Update every 2 seconds
    except Exception as e:
        logger.error(f"System monitor WebSocket error: {type(e).__name__}: {e}", exc_info=True)
    finally:
        logger.info("System monitor WebSocket closing")
        if gpu_available:
            try:
                pynvml.nvmlShutdown()
            except:
                pass


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

        # Keep connection alive by listening for messages
        # The background tasks will send updates via the stored websocket reference
        while True:
            try:
                # Set a short timeout to allow periodic checks
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo back for keep-alive if needed
                if data:
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # Connection is still alive, no incoming data
                # The server can still send data to the client
                pass
    except WebSocketDisconnect:
        if job_id in job_manager.websockets:
            del job_manager.websockets[job_id]
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
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
        logger.error(f"Error injecting debug log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Serve built frontend if present
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
