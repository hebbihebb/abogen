import React, { useState } from 'react';
import { X, Check } from 'lucide-react';
import useStore from '../store';

const ChapterSelector = () => {
  const {
    showChapterSelector,
    toggleChapterSelector,
    fileInfo,
    selectedChapters,
    setSelectedChapters,
  } = useStore();

  const [tempSelected, setTempSelected] = useState(selectedChapters);

  if (!showChapterSelector) return null;

  const chapters = fileInfo?.chapters || [];
  const isAll = tempSelected.length === chapters.length;

  const toggleChapter = (index) => {
    setTempSelected((prev) =>
      prev.includes(index)
        ? prev.filter((i) => i !== index)
        : [...prev, index]
    );
  };

  const toggleAll = () => {
    setTempSelected(
      isAll ? [] : chapters.map((_, index) => index)
    );
  };

  const handleSave = () => {
    setSelectedChapters(tempSelected);
    toggleChapterSelector();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-800">
            Select {fileInfo?.type === 'pdf' ? 'Pages' : 'Chapters'}
          </h2>
          <button
            onClick={toggleChapterSelector}
            className="p-1 hover:bg-gray-100 rounded-full"
          >
            <X className="h-6 w-6 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mb-4">
            <button
              onClick={toggleAll}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              {isAll ? 'Deselect All' : 'Select All'}
            </button>
            <p className="text-sm text-gray-500 mt-1">
              {tempSelected.length} of {chapters.length} selected
            </p>
          </div>

          <div className="space-y-2">
            {chapters.map((chapter, index) => (
              <div
                key={index}
                onClick={() => toggleChapter(index)}
                className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                  tempSelected.includes(index)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center ${
                      tempSelected.includes(index)
                        ? 'border-blue-600 bg-blue-600'
                        : 'border-gray-300'
                    }`}
                  >
                    {tempSelected.includes(index) && (
                      <Check className="h-3 w-3 text-white" />
                    )}
                  </div>
                  <span className="font-medium text-gray-800">
                    {chapter.title}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t">
          <button
            onClick={toggleChapterSelector}
            className="flex-1 btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex-1 btn-primary"
          >
            Confirm Selection
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChapterSelector;
