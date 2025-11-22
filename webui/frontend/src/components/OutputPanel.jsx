import React, { useEffect } from 'react';
import { Download, Folder, Music, FileText, RefreshCw } from 'lucide-react';
import useStore from '../store';

const OutputPanel = () => {
  const {
    outputFolder,
    outputFiles,
    currentJob,
    fetchOutputFiles,
  } = useStore();

  useEffect(() => {
    if (currentJob && outputFiles.length === 0) {
      fetchOutputFiles(currentJob);
    }
  }, [currentJob]);

  const handleRefresh = async () => {
    if (currentJob) {
      await fetchOutputFiles(currentJob);
    }
  };

  const handleDownload = async (filename) => {
    if (!currentJob) {
      alert('No job ID available');
      return;
    }

    try {
      const API_URL = import.meta.env.DEV
        ? `http://${window.location.hostname}:8000`
        : window.location.origin;

      const response = await fetch(`${API_URL}/api/jobs/${currentJob}/files/${filename}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download file: ' + error.message);
    }
  };

  const getFileIcon = (fileType) => {
    if (fileType === 'audio') {
      return <Music className="h-4 w-4 text-blue-600" />;
    } else if (fileType === 'subtitle') {
      return <FileText className="h-4 w-4 text-green-600" />;
    }
    return <FileText className="h-4 w-4 text-gray-600" />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  if (!outputFolder || !currentJob) {
    return (
      <div className="card">
        <p className="text-sm text-gray-500 text-center">
          No output folder information available
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Output Files</h3>
        <button
          onClick={handleRefresh}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Refresh file list"
        >
          <RefreshCw className="h-4 w-4 text-gray-600" />
        </button>
      </div>

      {/* Output Folder Path */}
      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="flex items-start gap-2">
          <Folder className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-gray-600 mb-1">Output Folder:</p>
            <p className="text-sm text-gray-700 break-all font-mono">
              {outputFolder}
            </p>
          </div>
        </div>
      </div>

      {/* Files List */}
      {outputFiles.length > 0 ? (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700 mb-3">
            Generated Files ({outputFiles.length})
          </p>
          {outputFiles.map((file) => (
            <div
              key={file.name}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0 flex-1">
                {getFileIcon(file.type)}
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-800 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.size)}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleDownload(file.name)}
                className="ml-2 p-2 hover:bg-blue-100 rounded-lg transition-colors flex-shrink-0"
                title={`Download ${file.name}`}
              >
                <Download className="h-4 w-4 text-blue-600" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-4 text-center">
          <p className="text-sm text-gray-500">
            No files found in output folder
          </p>
        </div>
      )}
    </div>
  );
};

export default OutputPanel;
