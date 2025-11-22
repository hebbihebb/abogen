import React from 'react';
import useStore from '../store';

export default function StatusBanner() {
  const desktopStatus = useStore((state) => state.desktopStatus);
  const jobStatus = useStore((state) => state.jobStatus);
  const processing = useStore((state) => state.processing);
  const progress = useStore((state) => state.progress);

  // Determine what's currently active
  const isWebUIConverting = processing && jobStatus?.status === 'processing';
  const isDesktopConverting = desktopStatus?.active && desktopStatus?.source === 'desktop';

  if (!isWebUIConverting && !isDesktopConverting) {
    return null;
  }

  const isDesktop = isDesktopConverting;
  const currentFile = isDesktop ? desktopStatus?.currentFile : jobStatus?.config?.file_path;
  const currentProgress = isDesktop ? desktopStatus?.progress : progress;

  return (
    <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-3 shadow-lg">
      <div className="max-w-7xl mx-auto">
        {/* Header with icon and status text */}
        <div className="flex items-center gap-3 mb-2">
          {isDesktop ? (
            <>
              <div className="text-xl">🖥️</div>
              <div className="flex-1">
                <h3 className="font-semibold text-sm">Desktop App Converting</h3>
              </div>
            </>
          ) : (
            <>
              <div className="text-xl">⚙️</div>
              <div className="flex-1">
                <h3 className="font-semibold text-sm">WebUI Converting</h3>
              </div>
            </>
          )}
        </div>

        {/* File being processed */}
        {currentFile && (
          <p className="text-xs text-blue-100 mb-2 truncate">
            Processing: <span className="font-mono">{currentFile}</span>
          </p>
        )}

        {/* Progress bar */}
        <div className="w-full bg-blue-400 rounded-full h-2 overflow-hidden">
          <div
            className="bg-white h-full rounded-full transition-all duration-300 ease-out"
            style={{ width: `${Math.min(currentProgress || 0, 100)}%` }}
          />
        </div>

        {/* Progress percentage */}
        <div className="text-right text-xs text-blue-100 mt-1">
          {Math.round(currentProgress || 0)}% complete
        </div>
      </div>
    </div>
  );
}
