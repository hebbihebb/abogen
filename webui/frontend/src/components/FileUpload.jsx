import React from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X } from 'lucide-react';
import useStore from '../store';

const FileUpload = () => {
  const { file, fileInfo, uploadFile, setFile, setFileInfo } = useStore();

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      try {
        await uploadFile(acceptedFiles[0]);
      } catch (error) {
        console.error('Error uploading file:', error);
      }
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/epub+zip': ['.epub'],
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/x-subrip': ['.srt'],
      'text/vtt': ['.vtt'],
    },
    multiple: false,
  });

  const clearFile = () => {
    setFile(null);
    setFileInfo(null);
  };

  return (
    <div className="w-full">
      {!file ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-lg font-medium text-gray-700 mb-2">
            {isDragActive ? 'Drop file here' : 'Drag & drop a file here'}
          </p>
          <p className="text-sm text-gray-500">
            or click to browse
          </p>
          <p className="text-xs text-gray-400 mt-4">
            Supported: EPUB, PDF, TXT, MD, SRT, VTT
          </p>
        </div>
      ) : (
        <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <File className="h-8 w-8 text-blue-600" />
              <div>
                <p className="font-medium text-gray-800">{fileInfo?.filename || file.name}</p>
                <p className="text-sm text-gray-500">
                  {fileInfo?.type?.toUpperCase()} • {(fileInfo?.size / 1024).toFixed(1)} KB
                  {fileInfo?.char_count && ` • ${fileInfo.char_count.toLocaleString()} chars`}
                </p>
              </div>
            </div>
            <button
              onClick={clearFile}
              className="p-2 hover:bg-blue-100 rounded-full transition-colors"
            >
              <X className="h-5 w-5 text-gray-600" />
            </button>
          </div>

          {fileInfo?.chapters && (
            <div className="mt-4 pt-4 border-t border-blue-200">
              <p className="text-sm text-gray-600">
                {fileInfo.chapters.length} {fileInfo.type === 'pdf' ? 'pages' : 'chapters'} available
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
