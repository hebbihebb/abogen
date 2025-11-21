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

### Step 1: Install Abogen

```bash
# From the root abogen directory
pip install -e .
```

### Step 2: Install Web UI Dependencies

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

### Option 1: Automatic (Recommended)

**Linux/Mac:**
```bash
cd webui
./start.sh
```

**Windows:**
```bash
cd webui
start.bat
```

### Option 2: Manual

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
```bash
# Make sure abogen is installed
pip install -e /path/to/abogen
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
