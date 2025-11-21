import React, { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';
import useStore from '../store';

const LogViewer = () => {
  const { logs } = useStore();
  const logEndRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getLogColor = (level) => {
    switch (level) {
      case 'error':
        return 'text-red-600';
      case 'warning':
        return 'text-orange-600';
      case 'success':
        return 'text-green-600';
      case 'debug':
        return 'text-gray-500';
      default:
        return 'text-blue-600';
    }
  };

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Terminal className="h-5 w-5 text-gray-600" />
        <h3 className="text-lg font-semibold text-gray-800">Processing Log</h3>
      </div>

      <div className="bg-gray-50 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
        {logs.length === 0 ? (
          <p className="text-gray-400 text-center py-8">
            No logs yet. Start a conversion to see progress here.
          </p>
        ) : (
          <div className="space-y-1">
            {logs.map((log, index) => (
              <div key={index} className="flex gap-2">
                <span className="text-gray-400 text-xs">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className={getLogColor(log.level)}>
                  {log.message}
                </span>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        )}
      </div>
    </div>
  );
};

export default LogViewer;
