import React from 'react';
import { X } from 'lucide-react';
import useStore from '../store';

const Settings = () => {
  const { showSettings, toggleSettings, config, updateConfig } = useStore();

  if (!showSettings) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-800">
            Advanced Settings
          </h2>
          <button
            onClick={toggleSettings}
            className="p-1 hover:bg-gray-100 rounded-full"
          >
            <X className="h-6 w-6 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Text Processing */}
          <div>
            <h3 className="text-lg font-medium text-gray-800 mb-3">
              Text Processing
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="font-medium text-gray-700">
                    Replace Single Newlines
                  </label>
                  <p className="text-sm text-gray-500">
                    Convert single newlines to spaces
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={config.replaceSingleNewlines}
                  onChange={(e) =>
                    updateConfig({ replaceSingleNewlines: e.target.checked })
                  }
                  className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>
            </div>
          </div>

          {/* Subtitle Settings */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-800 mb-3">
              Subtitle Settings
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Words per Subtitle
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={config.maxSubtitleWords}
                  onChange={(e) =>
                    updateConfig({
                      maxSubtitleWords: parseInt(e.target.value),
                    })
                  }
                  className="input-field w-32"
                />
              </div>
            </div>
          </div>

          {/* Chapter Settings */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-800 mb-3">
              Chapter Processing
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="font-medium text-gray-700">
                    Save Chapters Separately
                  </label>
                  <p className="text-sm text-gray-500">
                    Create individual files for each chapter
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={config.separateChapters}
                  onChange={(e) =>
                    updateConfig({ separateChapters: e.target.checked })
                  }
                  className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>

              {config.separateChapters && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Separate Chapters Format
                  </label>
                  <select
                    value={config.separateChaptersFormat}
                    onChange={(e) =>
                      updateConfig({ separateChaptersFormat: e.target.value })
                    }
                    className="select-field"
                  >
                    <option value="wav">WAV</option>
                    <option value="mp3">MP3</option>
                    <option value="flac">FLAC</option>
                    <option value="opus">OPUS</option>
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Silence Between Chapters (seconds)
                </label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  step="0.5"
                  value={config.silenceBetweenChapters}
                  onChange={(e) =>
                    updateConfig({
                      silenceBetweenChapters: parseFloat(e.target.value),
                    })
                  }
                  className="input-field w-32"
                />
              </div>
            </div>
          </div>

          {/* Performance Settings */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-800 mb-3">
              Performance
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="font-medium text-gray-700">
                    Use GPU Acceleration
                  </label>
                  <p className="text-sm text-gray-500">
                    Faster processing with CUDA-enabled GPU
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={config.use_gpu}
                  onChange={(e) =>
                    updateConfig({ use_gpu: e.target.checked })
                  }
                  className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>
            </div>
          </div>

          {/* Debug Settings */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-800 mb-3">
              Debug
            </h3>
            <div className="space-y-4">
              <div className="flex gap-3">
                <button
                  onClick={() => useStore.getState().startDebugJob()}
                  className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                >
                  Start Debug Session
                </button>
                <button
                  onClick={() => useStore.getState().sendDebugLog('Test log message', 'info')}
                  className="flex-1 px-4 py-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg text-sm font-medium transition-colors"
                >
                  Send Test Log
                </button>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => useStore.getState().sendDebugLog('Warning message', 'warning')}
                  className="flex-1 px-4 py-2 bg-orange-100 hover:bg-orange-200 text-orange-700 rounded-lg text-sm font-medium transition-colors"
                >
                  Send Warning
                </button>
                <button
                  onClick={() => useStore.getState().sendDebugLog('Error message', 'error')}
                  className="flex-1 px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg text-sm font-medium transition-colors"
                >
                  Send Error
                </button>
              </div>
            </div>
          </div>

          {/* About */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-800 mb-3">About</h3>
            <div className="text-sm text-gray-600 space-y-2">
              <p>
                <strong>Abogen Web UI</strong> v1.0.0
              </p>
              <p>
                A modern web interface for the Abogen TTS conversion tool.
              </p>
              <p>
                <a
                  href="https://github.com/denizsafak/abogen"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700"
                >
                  View on GitHub
                </a>
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t">
          <button onClick={toggleSettings} className="flex-1 btn-primary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
