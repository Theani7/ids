import { useState, useEffect } from 'react';
import useWebSocket from '../hooks/useWebSocket';
import { getStats, startCapture, stopCapture } from '../api/client';
import StatCard from '../components/StatCard';
import TrafficChart from '../components/TrafficChart';
import AlertFeed from '../components/AlertFeed';
import InterfaceSelector from '../components/InterfaceSelector';
import TelegramStatus from '../components/TelegramStatus';

export default function LiveTracker() {
  const { alerts, isConnected, stats: liveStats } = useWebSocket();
  const [dbStats, setDbStats] = useState(null);
  const [capturing, setCapturing] = useState(false);

  // Fetch persisted stats on mount
  useEffect(() => {
    (async () => {
      try {
        const s = await getStats();
        setDbStats(s);
      } catch {
        // backend may not be up yet
      }
    })();
  }, []);

  // Combine live WebSocket stats with DB stats
  const totalFlows =
    (dbStats?.total_flows || 0) + liveStats.total;
  const maliciousCount =
    (dbStats?.malicious_count || 0) + liveStats.malicious;
  const normalCount =
    (dbStats?.normal_count || 0) + liveStats.normal;
  const detectionRate =
    totalFlows > 0 ? ((maliciousCount / totalFlows) * 100).toFixed(2) : '0.00';

  const handleStart = async (iface) => {
    await startCapture(iface);
    setCapturing(true);
  };

  const handleStop = async () => {
    await stopCapture();
    setCapturing(false);
  };

  const lastAlert = alerts.length > 0 ? alerts[0] : null;
  const maliciousIps = alerts
    .filter((a) => a.label === 'MALICIOUS')
    .slice(0, 5);

  return (
    <div className="flex flex-col h-full">
      {/* ── Top Bar ── */}
      <div className="px-6 py-4 flex items-center justify-between border-b border-netborder bg-netsurface/50">
        <h2 className="font-orbitron text-xl text-netcyan tracking-wide">Live Dashboard</h2>
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              isConnected ? 'bg-netgreen animate-pulse' : 'bg-netred'
            }`}
          />
          <span
            className={`text-xs font-mono tracking-wider ${
              isConnected ? 'text-netgreen' : 'text-netred'
            }`}
          >
            {isConnected ? 'NODE CONNECTED' : 'NODE OFFLINE'}
          </span>
        </div>
      </div>

      {/* ── Stats Row ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 px-6 py-4">
        <StatCard
          title="Total Flows"
          value={totalFlows.toLocaleString()}
          subtitle="All analyzed flows"
          color="cyan"
        />
        <StatCard
          title="Malicious"
          value={maliciousCount.toLocaleString()}
          subtitle="Threats detected"
          color="red"
        />
        <StatCard
          title="Detection Rate"
          value={`${detectionRate}%`}
          subtitle="Malicious / total"
          color="green"
        />
      </div>

      {/* ── Main Content ──────────────────────────────────── */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-5 gap-4 px-6 pb-4 min-h-0">
        {/* Left column — 60% */}
        <div className="lg:col-span-3 flex flex-col gap-4 min-h-0">
          <TrafficChart alerts={alerts} />
          <div className="flex-1 min-h-0">
            <AlertFeed alerts={alerts} />
          </div>
        </div>

        {/* Right column — 40% */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <InterfaceSelector
            onStart={handleStart}
            onStop={handleStop}
            capturing={capturing}
          />
          <TelegramStatus lastAlert={lastAlert} />

          {/* Mini log: last 5 malicious IPs */}
          <div className="border border-netborder bg-netsurface rounded p-4 flex-1">
            <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-[#8b9ab3] mb-3">
              Recent Threats
            </h3>

            {maliciousIps.length === 0 ? (
              <p className="text-xs font-mono text-[#8b9ab3]">
                No malicious flows detected yet.
              </p>
            ) : (
              <div className="space-y-1.5">
                {maliciousIps.map((a, i) => (
                  <div
                    key={a.id || i}
                    className="flex items-center justify-between bg-netbg/50 rounded px-3 py-1.5"
                  >
                    <div className="flex items-center gap-2">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-netred" />
                      <span className="text-xs font-mono text-netred">
                        {a.src_ip}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-[#8b9ab3]">
                      → {a.dst_ip}:{a.dst_port}
                    </span>
                    <span className="text-[10px] font-mono text-netred">
                      {((a.confidence || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Footer ────────────────────────────────────────── */}
      <footer className="px-6 py-4 border-t border-netborder bg-netsurfacetext-center">
        <p className="text-[10px] font-mono text-[#8b9ab3] tracking-wider text-center">
          IntruML SaaS Edition — Powered by XGBoost + CIC-IDS2017
        </p>
      </footer>
    </div>
  );
}
