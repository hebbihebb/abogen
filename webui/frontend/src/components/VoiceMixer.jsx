import React, { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import useStore from '../store';

const VoiceMixer = () => {
  const {
    showVoiceMixer,
    toggleVoiceMixer,
    voices,
    updateConfig,
    voiceProfiles,
    fetchVoiceProfiles,
  } = useStore();

  const [weights, setWeights] = useState({});
  const [profileName, setProfileName] = useState('');

  useEffect(() => {
    if (showVoiceMixer) {
      fetchVoiceProfiles();
      // Initialize all voices with 0 weight
      const initialWeights = {};
      voices.forEach((voice) => {
        initialWeights[voice.id] = 0;
      });
      setWeights(initialWeights);
    }
  }, [showVoiceMixer]);

  if (!showVoiceMixer) return null;

  const handleWeightChange = (voiceId, value) => {
    setWeights((prev) => ({
      ...prev,
      [voiceId]: parseFloat(value),
    }));
  };

  const generateFormula = () => {
    const activeVoices = Object.entries(weights)
      .filter(([_, weight]) => weight > 0)
      .map(([voiceId, weight]) => `${voiceId}*${weight.toFixed(2)}`);

    return activeVoices.join(' + ') || '';
  };

  const handleApply = () => {
    const formula = generateFormula();
    if (formula) {
      updateConfig({ voiceFormula: formula });
      toggleVoiceMixer();
    }
  };

  const handleSaveProfile = async () => {
    if (!profileName) {
      alert('Please enter a profile name');
      return;
    }

    const formula = generateFormula();
    if (!formula) {
      alert('Please set at least one voice weight');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/voice-profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          name: profileName,
          formula: formula,
        }),
      });

      if (response.ok) {
        alert('Profile saved successfully');
        setProfileName('');
        fetchVoiceProfiles();
      }
    } catch (error) {
      alert('Failed to save profile');
    }
  };

  const loadProfile = (formula) => {
    // Parse formula like "af_heart*0.5 + am_adam*0.5"
    const newWeights = { ...weights };
    Object.keys(newWeights).forEach((key) => {
      newWeights[key] = 0;
    });

    formula.split('+').forEach((part) => {
      const [voiceId, weight] = part.trim().split('*');
      if (voiceId && weight) {
        newWeights[voiceId.trim()] = parseFloat(weight);
      }
    });

    setWeights(newWeights);
  };

  const totalWeight = Object.values(weights).reduce((sum, w) => sum + w, 0);
  const isValidFormula = totalWeight > 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-800">Voice Mixer</h2>
          <button
            onClick={toggleVoiceMixer}
            className="p-1 hover:bg-gray-100 rounded-full"
          >
            <X className="h-6 w-6 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Saved Profiles */}
          {voiceProfiles.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Saved Profiles
              </h3>
              <div className="flex flex-wrap gap-2">
                {voiceProfiles.map((profile) => (
                  <button
                    key={profile.name}
                    onClick={() => loadProfile(profile.formula)}
                    className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
                  >
                    {profile.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Voice Sliders */}
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-sm font-medium text-gray-700">
                Voice Weights
              </h3>
              <p className="text-sm text-gray-500">
                Total: {totalWeight.toFixed(2)}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {voices.map((voice) => (
                <div key={voice.id} className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm font-medium text-gray-700">
                      {voice.name}
                    </label>
                    <span className="text-sm text-gray-500">
                      {(weights[voice.id] || 0).toFixed(2)}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={weights[voice.id] || 0}
                    onChange={(e) =>
                      handleWeightChange(voice.id, e.target.value)
                    }
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Formula Preview */}
          {isValidFormula && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700 mb-1">
                Formula:
              </p>
              <code className="text-sm text-blue-600 break-all">
                {generateFormula()}
              </code>
            </div>
          )}

          {/* Save Profile */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              Save as Profile
            </h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                placeholder="Profile name"
                className="flex-1 input-field"
              />
              <button
                onClick={handleSaveProfile}
                disabled={!isValidFormula || !profileName}
                className="btn-primary flex items-center gap-2"
              >
                <Save className="h-4 w-4" />
                Save
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t">
          <button onClick={toggleVoiceMixer} className="flex-1 btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleApply}
            disabled={!isValidFormula}
            className={`flex-1 ${
              isValidFormula ? 'btn-primary' : 'bg-gray-300 text-gray-500'
            }`}
          >
            Apply Formula
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoiceMixer;
