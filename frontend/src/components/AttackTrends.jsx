import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { getTrends } from '../api/client';
import { TrendingUp, Calendar, AlertTriangle, Activity } from 'lucide-react';

const COLORS = ['#ff0040', '#00f0ff', '#00ff88', '#ffaa00', '#aa00ff', '#ff00aa'];

export default function AttackTrends() {
  const [trendData, setTrendData] = useState(null);
  const [days, setDays] = useState(7);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTrends();
  }, [days]);

  const loadTrends = async () => {
    setLoading(true);
    try {
      const data = await getTrends(days);
      setTrendData(data);
    } catch (err) {
      console.error('Failed to load trends:', err);
    } finally {
      setLoading(false);
    }
  };

  const prepareHourlyData = () => {
    if (!trendData?.hourly?.labels) return [];
    return trendData.hourly.labels.map((label, i) => ({
      time: label.slice(11, 16),
      total: trendData.hourly.total[i] || 0,
      malicious: trendData.hourly.malicious[i] || 0,
    }));
  };

  const prepareDailyData = () => {
    if (!trendData?.daily?.labels) return [];
    return trendData.daily.labels.map((label, i) => ({
      date: label.slice(5),
      total: trendData.daily.total[i] || 0,
      malicious: trendData.daily.malicious[i] || 0,
    }));
  };

  const prepareAttackTypeData = () => {
    if (!trendData?.attack_types?.types) return [];
    return trendData.attack_types.types.map((type, i) => ({
      name: type || 'Unknown',
      value: trendData.attack_types.counts[i] || 0,
    })).filter(e => e.value > 0);
  };

  const calculateStats = () => {
    if (!trendData) return null;
    const totalFlows = trendData.daily?.total?.reduce((a, b) => a + b, 0) || 0;
    const totalAttacks = trendData.daily?.malicious?.reduce((a, b) => a + b, 0) || 0;
    const attackRate = totalFlows > 0 ? ((totalAttacks / totalFlows) * 100).toFixed(2) : 0;
    const peakIdx = trendData.hourly?.total?.indexOf(Math.max(...(trendData.hourly?.total || [0])));
    
    return {
      totalFlows,
      totalAttacks,
      attackRate,
      peakHour: peakIdx >= 0 ? trendData.hourly?.labels[peakIdx]?.slice(11, 16) : '--:--',
    };
  };

  const stats = calculateStats();
  const hasData = stats && stats.totalFlows > 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-mono uppercase tracking-[0.2em] text-[#8b9ab3] flex items-center gap-2">
          <TrendingUp className="w-4 h-4" />
          Attack Trends & Analysis
        </h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="bg-netbg border border-netborder text-[#e6edf3] font-mono text-xs rounded px-2 py-1"
        >
          <option value={1}>Last 24 hours</option>
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
        </select>
      </div>

      {loading && (
        <div className="text-center py-12 text-netcyan font-mono text-sm animate-pulse">
          Analyzing traffic patterns...
        </div>
      )}

      {!loading && !trendData && (
        <div className="text-center py-12 text-[#8b9ab3] font-mono">
          <Activity className="w-12 h-12 mx-auto mb-4 text-netborder" />
          <p className="text-lg">No data available</p>
          <p className="text-sm">Start capturing network traffic to see trends</p>
        </div>
      )}

      {!loading && trendData && stats && !hasData && (
        <div className="text-center py-12 text-[#8b9ab3] font-mono">
          <Activity className="w-12 h-12 mx-auto mb-4 text-netborder" />
          <p className="text-lg mb-2">No traffic data available</p>
          <p className="text-sm text-netcyan">Start capturing traffic to see attack trends</p>
        </div>
      )}

      {!loading && hasData && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="border border-netborder bg-netsurface rounded p-3">
              <p className="text-xs font-mono text-[#8b9ab3] uppercase">Total Flows</p>
              <p className="text-xl font-mono text-netcyan">{stats.totalFlows.toLocaleString()}</p>
            </div>
            <div className="border border-netborder bg-netsurface rounded p-3">
              <p className="text-xs font-mono text-[#8b9ab3] uppercase">Attacks Detected</p>
              <p className="text-xl font-mono text-netred">{stats.totalAttacks.toLocaleString()}</p>
            </div>
            <div className="border border-netborder bg-netsurface rounded p-3">
              <p className="text-xs font-mono text-[#8b9ab3] uppercase">Attack Rate</p>
              <p className="text-xl font-mono text-netorange">{stats.attackRate}%</p>
            </div>
            <div className="border border-netborder bg-netsurface rounded p-3">
              <p className="text-xs font-mono text-[#8b9ab3] uppercase">Peak Activity</p>
              <p className="text-xl font-mono text-netgreen">{stats.peakHour}</p>
            </div>
          </div>

          <div className="border border-netborder bg-netsurface rounded p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-[#8b9ab3] mb-3 flex items-center gap-2">
              <Calendar className="w-3 h-3" />
              Hourly Activity Pattern
            </h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={prepareHourlyData()}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a3a4a" />
                  <XAxis dataKey="time" stroke="#5a6a7a" fontSize={10} />
                  <YAxis stroke="#5a6a7a" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a0f1c',
                      border: '1px solid #1a2a3a',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                  />
                  <Line type="monotone" dataKey="total" stroke="#00f0ff" strokeWidth={2} dot={false} name="Total Flows" />
                  <Line type="monotone" dataKey="malicious" stroke="#ff0040" strokeWidth={2} dot={false} name="Attacks" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="border border-netborder bg-netsurface rounded p-4">
              <h3 className="text-xs font-mono uppercase tracking-wider text-[#8b9ab3] mb-3">
                Daily Breakdown
              </h3>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={prepareDailyData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a3a4a" />
                    <XAxis dataKey="date" stroke="#5a6a7a" fontSize={10} />
                    <YAxis stroke="#5a6a7a" fontSize={10} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0a0f1c',
                        border: '1px solid #1a2a3a',
                        borderRadius: '4px',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="total" fill="#00f0ff" name="Total" />
                    <Bar dataKey="malicious" fill="#ff0040" name="Attacks" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="border border-netborder bg-netsurface rounded p-4">
              <h3 className="text-xs font-mono uppercase tracking-wider text-[#8b9ab3] mb-3 flex items-center gap-2">
                <AlertTriangle className="w-3 h-3" />
                Attack Types
              </h3>
              {prepareAttackTypeData().length > 0 ? (
                <>
                  <div className="h-40">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={prepareAttackTypeData()}
                          cx="50%"
                          cy="50%"
                          outerRadius={60}
                          dataKey="value"
                          label={({ name }) => name.slice(0, 10)}
                          labelLine={false}
                        >
                          {prepareAttackTypeData().map((entry, index) => (
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
                    {prepareAttackTypeData().map((entry, i) => (
                      <span key={entry.name} className="text-xs font-mono" style={{ color: COLORS[i % COLORS.length] }}>
                        ● {entry.name}: {entry.value}
                      </span>
                    ))}
                  </div>
                </>
              ) : (
                <div className="h-40 flex items-center justify-center text-[#8b9ab3] font-mono text-sm">
                  No attack type data available
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}