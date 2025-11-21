import React from 'react';
import { Play, StopCircle, Download } from 'lucide-react';
import useStore from '../store';

const ProcessingPanel = () => {
  const {
    processing,
    progress,
    currentJob,
    jobStatus,
    fileInfo,
    startConversion,
    cancelJob,
    downloadOutput,
  } = useStore();

  const handleStart = async () => {
    try {
      await startConversion();
    } catch (error) {
      alert('Failed to start conversion: ' + error.message);
    }
  };

  const handleDownload = async () => {
    try {
      await downloadOutput(currentJob);
    } catch (error) {
      alert('Failed to download output: ' + error.message);
    }
  };

  const canStart = fileInfo && !processing;
  const canCancel = processing;
  const canDownload = jobStatus?.status === 'completed';

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Processing</h3>

      {/* Progress Bar */}
      {processing && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all duration-300 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Status Message */}
      {jobStatus && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-700">
            Status: <span className="font-medium">{jobStatus.status}</span>
          </p>
          {jobStatus.error && (
            <p className="text-sm text-red-600 mt-1">
              Error: {jobStatus.error}
            </p>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleStart}
          disabled={!canStart}
          className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors ${
            canStart
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          <Play className="h-5 w-5" />
          Start Conversion
        </button>

        {canCancel && (
          <button
            onClick={cancelJob}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            <StopCircle className="h-5 w-5" />
            Cancel
          </button>
        )}

        {canDownload && (
          <button
            onClick={handleDownload}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            <Download className="h-5 w-5" />
            Download
          </button>
        )}
      </div>

      {/* Help Text */}
      {!fileInfo && (
        <p className="text-sm text-gray-500 mt-4 text-center">
          Upload a file to begin
        </p>
      )}
    </div>
  );
};

export default ProcessingPanel;
