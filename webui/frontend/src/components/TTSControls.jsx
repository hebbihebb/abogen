import React, { useEffect } from 'react';
import { Settings, Sliders } from 'lucide-react';
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
  } = useStore();

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
    updateConfig({ engine });
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
          <input
            type="text"
            value={config.referenceAudio || ''}
            onChange={(e) => updateConfig({ referenceAudio: e.target.value })}
            placeholder="Path to reference audio file (.wav)"
            className="input-field"
          />
          <p className="text-xs text-gray-500 mt-1">
            Provide a WAV file with the voice you want to clone
          </p>
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
          checked={config.useGpu}
          onChange={(e) => updateConfig({ useGpu: e.target.checked })}
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
