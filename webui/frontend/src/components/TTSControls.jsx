import React, { useEffect } from 'react';
import { Settings, Sliders, Upload, X, FileAudio } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import useStore from '../store';

const TTSControls = () => {
  const {
    config,
    engines,
    voices,
    updateConfig,
    fetchEngines,
    fetchVoices,
    toggleSettings,
    toggleVoiceMixer,
    uploadReferenceAudio,
  } = useStore();

  const onDropReference = async (acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      try {
        await uploadReferenceAudio(acceptedFiles[0]);
      } catch (error) {
        console.error('Error uploading reference audio:', error);
      }
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onDropReference,
    accept: {
      'audio/wav': ['.wav'],
      'audio/x-wav': ['.wav'],
    },
    multiple: false,
  });

  const clearReferenceAudio = () => {
    updateConfig({ referenceAudio: null });
  };

  useEffect(() => {
    fetchEngines();
  }, []);

  useEffect(() => {
    if (config.engine) {
      fetchVoices(config.engine);
    }
  }, [config.engine]);

  const handleEngineChange = (e) => {
    const engine = e.target.value;

    // Clear engine-specific settings when switching
    const updates = { engine };
    if (engine === 'kokoro') {
      // Switching to Kokoro - clear reference audio
      updates.referenceAudio = null;
    } else if (engine === 'f5_tts') {
      // Switching to F5-TTS - clear voice formula
      updates.voiceFormula = null;
    }

    updateConfig(updates);
  };

  return (
    <div className="space-y-6">
      {/* TTS Engine Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          TTS Engine
        </label>
        <select
          value={config.engine}
          onChange={handleEngineChange}
          className="select-field"
        >
          {engines.map((engine) => (
            <option key={engine} value={engine}>
              {engine === 'kokoro' ? 'Kokoro-82M' : 'F5-TTS'}
            </option>
          ))}
        </select>
      </div>

      {/* Voice Selection */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">
            Voice
          </label>
          {config.engine === 'kokoro' && (
            <button
              onClick={toggleVoiceMixer}
              className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <Sliders className="h-4 w-4" />
              Voice Mixer
            </button>
          )}
        </div>
        <select
          value={config.voice}
          onChange={(e) => updateConfig({ voice: e.target.value })}
          className="select-field"
          disabled={config.engine === 'f5_tts'}
        >
          {voices.map((voice) => (
            <option key={voice.id} value={voice.id}>
              {voice.name} {voice.language && `(${voice.language})`}
            </option>
          ))}
          {voices.length === 0 && config.engine === 'f5_tts' && (
            <option value="">Custom Reference Audio Required</option>
          )}
        </select>
      </div>

      {/* F5-TTS Reference Audio */}
      {config.engine === 'f5_tts' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Reference Audio
          </label>

          {!config.referenceAudio ? (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${isDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                }`}
            >
              <input {...getInputProps()} />
              <Upload className="mx-auto h-8 w-8 text-gray-400 mb-2" />
              <p className="text-sm font-medium text-gray-700">
                {isDragActive ? 'Drop WAV here' : 'Click or drag WAV file'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Required for voice cloning
              </p>
            </div>
          ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center justify-between">
              <div className="flex items-center gap-2 overflow-hidden">
                <FileAudio className="h-5 w-5 text-blue-600 flex-shrink-0" />
                <span className="text-sm text-gray-700 truncate" title={config.referenceAudio}>
                  {config.referenceAudio.split(/[/\\]/).pop()}
                </span>
              </div>
              <button
                onClick={clearReferenceAudio}
                className="p-1 hover:bg-blue-100 rounded-full text-gray-500 hover:text-red-500 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          <div className="mt-2">
            <p className="text-xs text-gray-500 mb-1">Or enter path manually:</p>
            <input
              type="text"
              value={config.referenceAudio || ''}
              onChange={(e) => updateConfig({ referenceAudio: e.target.value })}
              placeholder="/path/to/audio.wav"
              className="input-field text-xs py-1"
            />
          </div>
        </div>
      )}

      {/* Speed Control */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Speed: {config.speed.toFixed(1)}x
        </label>
        <input
          type="range"
          min="0.1"
          max="2.0"
          step="0.1"
          value={config.speed}
          onChange={(e) => updateConfig({ speed: parseFloat(e.target.value) })}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>0.1x</span>
          <span>1.0x</span>
          <span>2.0x</span>
        </div>
      </div>

      {/* Subtitle Options */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Generate Subtitles
        </label>
        <select
          value={config.generateSubtitles}
          onChange={(e) => updateConfig({ generateSubtitles: e.target.value })}
          className="select-field"
        >
          <option value="disabled">Disabled</option>
          <option value="line">Line-based</option>
          <option value="sentence">Sentence-based</option>
          <option value="sentence_comma">Sentence + Comma</option>
          <option value="sentence_highlight">Sentence + Highlighting</option>
          <option value="word_1">Word-based (1 word)</option>
          <option value="word_2">Word-based (2 words)</option>
          <option value="word_3">Word-based (3+ words)</option>
        </select>
      </div>

      {/* Subtitle Format */}
      {config.generateSubtitles !== 'disabled' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Subtitle Format
          </label>
          <select
            value={config.subtitleFormat}
            onChange={(e) => updateConfig({ subtitleFormat: e.target.value })}
            className="select-field"
          >
            <option value="srt">SRT</option>
            <option value="ass_wide">ASS (Wide)</option>
            <option value="ass_narrow">ASS (Narrow)</option>
            <option value="ass_centered">ASS (Centered)</option>
          </select>
        </div>
      )}

      {/* Output Format */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Output Audio Format
        </label>
        <select
          value={config.outputFormat}
          onChange={(e) => updateConfig({ outputFormat: e.target.value })}
          className="select-field"
        >
          <option value="wav">WAV</option>
          <option value="mp3">MP3</option>
          <option value="flac">FLAC</option>
          <option value="opus">OPUS</option>
          <option value="m4b">M4B (Audiobook)</option>
        </select>
      </div>

      {/* GPU Acceleration */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="use-gpu"
          checked={config.use_gpu}
          onChange={(e) => updateConfig({ use_gpu: e.target.checked })}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="use-gpu" className="ml-2 text-sm text-gray-700">
          Use GPU Acceleration (if available)
        </label>
      </div>

      {/* Settings Button */}
      <button
        onClick={toggleSettings}
        className="w-full btn-secondary flex items-center justify-center gap-2"
      >
        <Settings className="h-4 w-4" />
        Advanced Settings
      </button>
    </div>
  );
};

export default TTSControls;
