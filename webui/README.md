# Abogen Web UI

A modern, responsive web interface for Abogen - the powerful text-to-speech audio conversion tool.

## Features

✨ **Complete Feature Parity** - Access all abogen features through a clean web interface:
- 📁 Drag-and-drop file upload (EPUB, PDF, TXT, MD, SRT, VTT)
- 🎤 Multiple TTS engines (Kokoro-82M, F5-TTS)
- 🎨 Voice mixer with custom formulas
- ⚡ Real-time processing logs via WebSocket
- 📊 Progress tracking
- 🎯 Chapter/page selection for books
- 🎚️ Speed control (0.1x - 2.0x)
- 📝 Subtitle generation with multiple formats
- 🔧 Advanced settings and configurations

🎨 **Modern Design**:
- Clean white, gray, and blue color scheme
- Responsive layout (mobile, tablet, desktop)
- Intuitive component-based UI
- Real-time updates and feedback

## Architecture

```
webui/
├── backend/          # FastAPI REST API + WebSocket server
│   ├── main.py      # Main server application
│   └── requirements.txt
└── frontend/        # React + Vite application
    ├── src/
    │   ├── components/   # React components
    │   ├── store.js      # Zustand state management
    │   ├── App.jsx       # Main application
    │   └── index.css     # Tailwind styles
    └── package.json
```

## Prerequisites

- Python 3.10+ (for backend)
- Node.js 18+ (for frontend)
- All abogen dependencies installed

## Installation

### 1. Install Abogen

First, make sure abogen is installed:

```bash
pip install -e .
```

### 2. Install Backend Dependencies

```bash
cd webui/backend
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
cd webui/frontend
npm install
```

## Usage

### Quick Start (Development Mode)

**Terminal 1 - Backend:**
```bash
cd webui/backend
python main.py
```
The API server will start on `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd webui/frontend
npm run dev
```
The web UI will be available at `http://localhost:5173`

### Production Build

**Build Frontend:**
```bash
cd webui/frontend
npm run build
```

**Serve with Backend:**
```bash
cd webui/backend
# The FastAPI server can serve the built frontend
python main.py
```

## API Endpoints

### REST API

- `GET /` - Health check
- `GET /api/engines` - List available TTS engines
- `GET /api/voices/{engine}` - Get voices for an engine
- `GET /api/voice-profiles` - List saved voice profiles
- `POST /api/voice-profiles` - Save a voice profile
- `DELETE /api/voice-profiles/{name}` - Delete a voice profile
- `POST /api/upload` - Upload a file for processing
- `POST /api/convert` - Start TTS conversion
- `GET /api/jobs/{job_id}` - Get job status
- `GET /api/jobs/{job_id}/download` - Download output file
- `GET /api/config` - Get configuration
- `POST /api/config` - Update configuration

### WebSocket

- `WS /ws/{job_id}` - Real-time job updates, logs, and progress

## Configuration

The web UI respects all abogen configuration settings. You can modify settings through:

1. The web interface (Settings dialog)
2. The `~/.config/abogen/config.json` file
3. API calls to `/api/config`

## Technology Stack

### Backend
- **FastAPI** - Modern async web framework
- **WebSockets** - Real-time communication
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### Frontend
- **React 19** - UI library
- **Vite** - Build tool and dev server
- **Zustand** - State management
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Icon library
- **React Dropzone** - File upload

## Development

### Backend Development

The FastAPI server includes automatic API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Development

Hot module replacement (HMR) is enabled for instant updates during development.

**File Structure:**
```
src/
├── components/
│   ├── FileUpload.jsx       # Drag-and-drop file input
│   ├── TTSControls.jsx      # TTS configuration panel
│   ├── ProcessingPanel.jsx # Start/cancel/download controls
│   ├── LogViewer.jsx        # Real-time log display
│   ├── ChapterSelector.jsx  # Chapter/page selection dialog
│   ├── VoiceMixer.jsx       # Voice formula creator
│   └── Settings.jsx         # Advanced settings dialog
├── store.js                 # Global state management
├── App.jsx                  # Main application component
└── index.css                # Global styles
```

### Adding New Features

1. **Backend**: Add endpoints to `backend/main.py`
2. **Frontend**: Create components in `src/components/`
3. **State**: Update `src/store.js` for data management
4. **Styling**: Use Tailwind utility classes

## Customization

### Colors

Edit `frontend/tailwind.config.js` to customize the color scheme:

```js
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom blue shades
      },
    },
  },
}
```

### API URL

For production deployment, update the API URL in `frontend/src/store.js`:

```js
const API_URL = 'http://your-server.com:8000';
```

## Troubleshooting

**Backend won't start:**
- Ensure all Python dependencies are installed
- Check that port 8000 is available
- Verify abogen is properly installed

**Frontend won't start:**
- Delete `node_modules` and run `npm install` again
- Check that port 5173 is available
- Ensure Node.js version is 18+

**WebSocket connection fails:**
- Verify backend is running
- Check browser console for CORS errors
- Ensure WebSocket URL matches backend address

**File upload fails:**
- Check file format is supported
- Verify backend temp directory has write permissions
- Check file size limits

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This web UI follows the same license as Abogen (MIT).

## Support

For issues and questions:
- GitHub Issues: https://github.com/denizsafak/abogen/issues
- Documentation: https://github.com/denizsafak/abogen

## Credits

- Built with ❤️ for the Abogen project
- UI design inspired by modern web standards
- Icons by Lucide
