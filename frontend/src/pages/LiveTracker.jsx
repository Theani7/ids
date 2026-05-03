import { useState, useEffect } from 'react';
import { Activity, Shield, AlertTriangle, Radio } from 'lucide-react';
import useWebSocket from '../hooks/useWebSocket';
import { getStats, startCapture, stopCapture } from '../services/api';
import StatCard from '../components/ui/StatCard';
import TrafficChart from '../components/charts/TrafficChart';
import AlertFeed from '../components/AlertFeed';
import InterfaceSelector from '../components/InterfaceSelector';

export default function LiveTracker() {
  const { alerts, isConnected, stats: liveStats } = useWebSocket();
  const [dbStats, setDbStats] = useState(null);
  const [capturing, setCapturing] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const s = await getStats();
        setDbStats(s);
      } catch (err) {
        console.error('Failed to load stats:', err);
      }
    })();
  }, []);

  const totalFlows = (dbStats?.total_flows || 0) + liveStats.total;
  const maliciousCount = (dbStats?.malicious_count || 0) + liveStats.malicious;
  const detectionRate = totalFlows > 0 ? ((maliciousCount / totalFlows) * 100).toFixed(1) : '0.0';

  const handleStart = async (iface) => {
    await startCapture(iface);
    setCapturing(true);
  };

  const handleStop = async () => {
    await stopCapture();
    setCapturing(false);
  };

  const maliciousIps = alerts.filter((a) => a.label === 'MALICIOUS').slice(0, 5);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="px-6 py-4 border-b border-netborder bg-netsurface/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-netcyan" />
            <h1 className="text-lg font-semibold text-white">Live Traffic Monitor</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-netgreen animate-pulse' : 'bg-netred'}`} />
            <span className={`text-xs font-medium ${isConnected ? 'text-netgreen' : 'text-netred'}`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 px-6 py-4">
        <StatCard
          icon={Radio}
          title="Total Flows"
          value={totalFlows.toLocaleString()}
          subtitle="Packets analyzed"
          color="cyan"
        />
        <StatCard
          icon={Shield}
          title="Threats Detected"
          value={maliciousCount.toLocaleString()}
          subtitle="Malicious flows"
          color="red"
        />
        <StatCard
          icon={AlertTriangle}
          title="Threat Rate"
          value={`${detectionRate}%`}
          subtitle="Detection ratio"
          color="orange"
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 px-6 pb-4 min-h-0">
        {/* Left - Charts & Alerts */}
        <div className="lg:col-span-2 flex flex-col gap-4 min-h-0">
          <TrafficChart alerts={alerts} />
          <div className="flex-1 min-h-0">
            <AlertFeed alerts={alerts} />
          </div>
        </div>

        {/* Right - Controls */}
        <div className="flex flex-col gap-4">
          <InterfaceSelector
            onStart={handleStart}
            onStop={handleStop}
            capturing={capturing}
          />

          {/* Recent Threats */}
          <div className="card p-4 flex-1">
            <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4 text-netred" />
              Recent Threats
            </h3>
            {maliciousIps.length === 0 ? (
              <p className="text-sm text-gray-500">No threats detected yet.</p>
            ) : (
              <div className="space-y-2">
                {maliciousIps.map((a, i) => (
                  <div key={a.id || i} className="flex items-center justify-between p-2 bg-netred/5 rounded-lg border border-netred/20">
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-netred" />
                      <span className="text-sm font-mono text-white">{a.src_ip}</span>
                    </div>
                    <span className="text-xs text-netred font-medium">
                      {((a.confidence || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
