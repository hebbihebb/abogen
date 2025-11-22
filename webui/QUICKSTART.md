# Abogen Web UI - Quick Start Guide

Get up and running with the Abogen Web UI in 5 minutes!

## Prerequisites

```bash
# Check Python version (needs 3.10+)
python --version

# Check Node.js version (needs 18+)
node --version
```

## Installation

### Step 1: Activate Virtual Environment

```bash
# From the root abogen directory
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 2: Install Abogen

```bash
# From the root abogen directory (with .venv activated)
pip install -e .
```

### Step 3: Install Web UI Dependencies

**Backend:**
```bash
cd webui/backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd webui/frontend
npm install
```

## Running the Web UI

### Option 1: Using Startup Scripts (Recommended)

The startup scripts automatically use the project's virtual environment.

**Linux/Mac:**
```bash
cd webui
./start_backend.sh  # In Terminal 1
```

**Windows:**
```bash
cd webui
start_backend.bat  # In Terminal 1
```

Then in another terminal:
```bash
cd webui/frontend
npm run dev  # In Terminal 2
```

### Option 2: Manual (with .venv activated)

Make sure you've activated the virtual environment first:
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Terminal 1 - Backend:**
```bash
cd webui/backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd webui/frontend
npm run dev
```

## Access the Application

Open your browser and navigate to:
- **Web UI**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## First Conversion

1. **Upload a file**: Drag and drop an EPUB, PDF, or TXT file
2. **Select voice**: Choose from 58+ voices or use voice mixer
3. **Configure**: Adjust speed, subtitle options, output format
4. **Start**: Click "Start Conversion" and watch real-time progress
5. **Download**: Get your audio file when complete

## Common Use Cases

### Convert an EPUB to Audiobook

1. Upload your EPUB file
2. Select chapters to include
3. Choose voice (e.g., "American Female - Heart")
4. Set output format to M4B
5. Enable subtitle generation (optional)
6. Start conversion

### Mix Custom Voice

1. Click "Voice Mixer" in TTS Configuration
2. Adjust sliders for multiple voices
3. Preview the formula
4. Save as a profile for reuse
5. Apply to your conversion

### Batch Processing Multiple Files

1. Upload first file and configure settings
2. Click "Add to Queue"
3. Upload next file and configure
4. Click "Manage Queue" to view all items
5. Process queue in order

## Tips

- **GPU Acceleration**: Enable for faster processing (requires CUDA/MPS)
- **Voice Preview**: Click voice name to hear a sample
- **Chapter Selection**: Use for long books to process specific sections
- **Speed Control**: Adjust from 0.1x to 2.0x for different pacing
- **Subtitle Formats**: Choose ASS for styled subtitles with colors

## Troubleshooting

**Port Already in Use:**
```bash
# Linux/Mac - Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Windows - Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Backend Import Error:**

If you get errors about missing modules (kokoro, misaki, etc.), make sure:
1. You've activated the virtual environment: `source .venv/bin/activate`
2. You've installed abogen and dependencies: `pip install -e .` from the root
3. You've installed backend dependencies: `pip install -r webui/backend/requirements.txt`
4. Use the startup scripts which handle the environment automatically

Or use the virtual environment's Python directly:
```bash
.venv/bin/python webui/backend/main.py  # Linux/Mac
.venv\Scripts\python.exe webui/backend/main.py  # Windows
```

**Frontend Build Error:**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore API endpoints at http://localhost:8000/docs
- Customize the UI colors in `frontend/tailwind.config.js`
- Add custom TTS backends (see abogen docs)

## Support

Need help? Check:
- [GitHub Issues](https://github.com/denizsafak/abogen/issues)
- [Abogen Documentation](https://github.com/denizsafak/abogen)

Enjoy using Abogen Web UI! 🎉
