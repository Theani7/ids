import { useState, useEffect, useRef, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

const WINDOW_SECONDS = 60;

function buildTimeSeries(alerts) {
  const now = Date.now();
  const buckets = [];

  for (let i = WINDOW_SECONDS; i >= 0; i--) {
    buckets.push({
      secondsAgo: i,
      label: i === 0 ? 'now' : `${i}s`,
      normal: 0,
      malicious: 0,
    });
  }

  for (const alert of alerts) {
    const ts = alert.timestamp ? new Date(alert.timestamp).getTime() : 0;
    const ago = Math.floor((now - ts) / 1000);
    if (ago < 0 || ago > WINDOW_SECONDS) continue;

    const idx = WINDOW_SECONDS - ago;
    if (idx >= 0 && idx < buckets.length) {
      if (alert.label === 'MALICIOUS') {
        buckets[idx].malicious += 1;
      } else {
        buckets[idx].normal += 1;
      }
    }
  }

  return buckets;
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-netsurface border border-netborder rounded-lg px-3 py-2 shadow-xl">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="text-sm font-medium" style={{ color: entry.color }}>
          {entry.dataKey}: {entry.value}
        </p>
      ))}
    </div>
  );
};

export default function TrafficChart({ alerts }) {
  const [tick, setTick] = useState(0);
  const intervalRef = useRef(null);

  // Refresh every second to slide the window
  useEffect(() => {
    intervalRef.current = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(intervalRef.current);
  }, []);

  const data = useMemo(() => buildTimeSeries(alerts), [alerts, tick]);

  return (
    <div className="card p-4">
      <h3 className="text-sm font-medium text-gray-400 mb-3">
        Traffic Flow — Last 60s
      </h3>

      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid stroke="#374151" strokeDasharray="3 3" opacity={0.3} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
            interval={9}
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#6b7280' }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="normal"
            stroke="#10b981"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, stroke: '#10b981', strokeWidth: 2 }}
          />
          <Line
            type="monotone"
            dataKey="malicious"
            stroke="#ef4444"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, stroke: '#ef4444', strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div className="flex items-center justify-center gap-6 mt-3">
        <div className="flex items-center gap-2">
          <span className="w-3 h-1 rounded-full bg-netgreen" />
          <span className="text-xs text-gray-500">Normal</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-1 rounded-full bg-netred" />
          <span className="text-xs text-gray-500">Malicious</span>
        </div>
      </div>
    </div>
  );
}
