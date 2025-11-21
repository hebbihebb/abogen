import React, { useEffect } from 'react';
import { Mic2 } from 'lucide-react';
import FileUpload from './components/FileUpload';
import TTSControls from './components/TTSControls';
import ProcessingPanel from './components/ProcessingPanel';
import LogViewer from './components/LogViewer';
import ChapterSelector from './components/ChapterSelector';
import VoiceMixer from './components/VoiceMixer';
import Settings from './components/Settings';
import useStore from './store';

function App() {
  const { fetchEngines, config } = useStore();

  useEffect(() => {
    // Initialize on mount
    fetchEngines();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Mic2 className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Abogen</h1>
              <p className="text-sm text-gray-500">
                Text-to-Speech Audio Generator
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - File Upload & Controls */}
          <div className="lg:col-span-2 space-y-6">
            {/* File Upload */}
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">
                Input File
              </h2>
              <FileUpload />
            </div>

            {/* Processing Panel */}
            <ProcessingPanel />

            {/* Log Viewer */}
            <LogViewer />
          </div>

          {/* Right Column - TTS Controls */}
          <div className="lg:col-span-1">
            <div className="card sticky top-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">
                TTS Configuration
              </h2>
              <TTSControls />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Powered by{' '}
            <a
              href="https://github.com/denizsafak/abogen"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Abogen
            </a>
            {' '}• Built with React & FastAPI
          </p>
        </div>
      </footer>

      {/* Dialogs */}
      <ChapterSelector />
      <VoiceMixer />
      <Settings />
    </div>
  );
}

export default App;
