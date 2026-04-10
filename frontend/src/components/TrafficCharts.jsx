import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from 'recharts';
import { getTrafficStats, getProtocolStats } from '../api/client';
import { Activity, Layers, Server } from 'lucide-react';

const COLORS = ['#00f0ff', '#ff0040', '#00ff88', '#ffaa00', '#aa00ff'];

export default function TrafficCharts() {
  const [trafficData, setTrafficData] = useState(null);
  const [protocolData, setProtocolData] = useState(null);
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [hours]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [traffic, protocols] = await Promise.all([
        getTrafficStats(hours),
        getProtocolStats(hours),
      ]);
      setTrafficData(traffic);
      setProtocolData(protocols);
    } catch (err) {
      console.error('Failed to load traffic data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const prepareTrafficChart = () => {
    if (!trafficData) return [];
    return trafficData.intervals.map((interval, i) => ({
      time: interval.split(' ')[1] || interval,
      bytesIn: trafficData.bytes_in[i] || 0,
      bytesOut: trafficData.bytes_out[i] || 0,
      packetsIn: trafficData.packets_in[i] || 0,
      packetsOut: trafficData.packets_out[i] || 0,
    }));
  };

  const prepareProtocolChart = () => {
    if (!protocolData) return [];
    return protocolData.protocols.map((proto, i) => ({
      name: proto,
      value: protocolData.counts[i] || 0,
      bytes: protocolData.bytes[i] || 0,
    }));
  };

  const preparePortChart = () => {
    if (!protocolData?.top_ports) return [];
    return protocolData.top_ports.slice(0, 8).map((p) => ({
      name: `${p.protocol}:${p.port}`,
      count: p.count,
    }));
  };

  return (
    <div className="space-y-4">
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-mono uppercase tracking-[0.2em] text-[#8b9ab3] flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Traffic Analytics
        </h2>
        <select
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="bg-netbg border border-netborder text-[#e6edf3] font-mono text-xs rounded px-2 py-1"
        >
          <option value={6}>Last 6 hours</option>
          <option value={24}>Last 24 hours</option>
          <option value={48}>Last 48 hours</option>
          <option value={72}>Last 3 days</option>
          <option value={168}>Last 7 days</option>
        </select>
      </div>

      {loading && (
        <div className="text-center py-8 text-netcyan font-mono text-sm animate-pulse">
          Loading traffic data...
        </div>
      )}

      {!loading && trafficData && (
        <>
          {/* Bandwidth Chart */}
          <div className="border border-netborder bg-netsurface rounded p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-[#8b9ab3] mb-3 flex items-center gap-2">
              <Server className="w-3 h-3" />
              Bandwidth Usage
            </h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={prepareTrafficChart()}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a3a4a" />
                  <XAxis
                    dataKey="time"
                    stroke="#5a6a7a"
                    fontSize={10}
                    tickFormatter={(v) => v.slice(0, 2)}
                  />
                  <YAxis
                    stroke="#5a6a7a"
                    fontSize={10}
                    tickFormatter={formatBytes}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a0f1c',
                      border: '1px solid #1a2a3a',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                    formatter={(value) => formatBytes(value)}
                  />
                  <Line
                    type="monotone"
                    dataKey="bytesIn"
                    stroke="#00f0ff"
                    strokeWidth={2}
                    dot={false}
                    name="Inbound"
                  />
                  <Line
                    type="monotone"
                    dataKey="bytesOut"
                    stroke="#ff0040"
                    strokeWidth={2}
                    dot={false}
                    name="Outbound"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="flex gap-4 mt-2 text-xs font-mono">
              <span className="text-netcyan">● Inbound</span>
              <span className="text-netred">● Outbound</span>
            </div>
          </div>

          {/* Protocol & Port Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="border border-netborder bg-netsurface rounded p-4">
              <h3 className="text-xs font-mono uppercase tracking-wider text-[#8b9ab3] mb-3 flex items-center gap-2">
                <Layers className="w-3 h-3" />
                Protocol Distribution
              </h3>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={prepareProtocolChart()}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={70}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {prepareProtocolChart().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0a0f1c',
                        border: '1px solid #1a2a3a',
                        borderRadius: '4px',
                        fontSize: '12px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {prepareProtocolChart().map((entry, i) => (
                  <span key={entry.name} className="text-xs font-mono" style={{ color: COLORS[i % COLORS.length] }}>
                    ● {entry.name}: {entry.value}
                  </span>
                ))}
              </div>
            </div>

            <div className="border border-netborder bg-netsurface rounded p-4">
              <h3 className="text-xs font-mono uppercase tracking-wider text-[#8b9ab3] mb-3">
                Top Ports
              </h3>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={preparePortChart()} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a3a4a" />
                    <XAxis type="number" stroke="#5a6a7a" fontSize={10} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      stroke="#5a6a7a"
                      fontSize={9}
                      width={60}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0a0f1c',
                        border: '1px solid #1a2a3a',
                        borderRadius: '4px',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" fill="#00ff88" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
