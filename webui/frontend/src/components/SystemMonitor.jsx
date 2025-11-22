import { useEffect, useState } from 'react';
import { Cpu, Zap } from 'lucide-react';

export default function SystemMonitor() {
    const [cpuUsage, setCpuUsage] = useState(0);
    const [gpuUsage, setGpuUsage] = useState(null);
    const [memUsage, setMemUsage] = useState(0);

    useEffect(() => {
        // Connect to system monitor WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = import.meta.env.DEV
            ? `${window.location.hostname}:8000`
            : window.location.host;
        const wsUrl = `${protocol}//${host}/ws/system`;
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setCpuUsage(data.cpu || 0);
            setGpuUsage(data.gpu);
            setMemUsage(data.memory || 0);
        };

        ws.onerror = () => {
            console.warn('System monitor WebSocket not available');
        };

        return () => ws.close();
    }, []);

    return (
        <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-gray-600" />
                <div className="flex items-center gap-2">
                    <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-blue-500 transition-all duration-300"
                            style={{ width: `${cpuUsage}%` }}
                        />
                    </div>
                    <span className="text-gray-700 w-10 text-right">{Math.round(cpuUsage)}%</span>
                </div>
            </div>

            {gpuUsage !== null && (
                <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-gray-600" />
                    <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-green-500 transition-all duration-300"
                                style={{ width: `${gpuUsage}%` }}
                            />
                        </div>
                        <span className="text-gray-700 w-10 text-right">{Math.round(gpuUsage)}%</span>
                    </div>
                </div>
            )}
        </div>
    );
}
