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
    <div className="bg-netsurface border border-netborder rounded px-3 py-2 shadow-lg">
      <p className="text-[10px] font-mono text-[#8b9ab3] mb-1">{label}</p>
      {payload.map((entry) => (
        <p
          key={entry.dataKey}
          className="text-xs font-mono"
          style={{ color: entry.color }}
        >
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
    <div className="border border-netborder bg-netsurface rounded p-4">
      <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-[#8b9ab3] mb-3">
        Traffic Flow — Last 60s
      </h3>

      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid stroke="#1a2332" strokeDasharray="3 3" opacity={0.4} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 9, fill: '#8b9ab3', fontFamily: 'JetBrains Mono' }}
            axisLine={{ stroke: '#1a2332' }}
            tickLine={false}
            interval={9}
          />
          <YAxis
            tick={{ fontSize: 9, fill: '#8b9ab3', fontFamily: 'JetBrains Mono' }}
            axisLine={{ stroke: '#1a2332' }}
            tickLine={false}
            allowDecimals={false}
            label={{
              value: 'flows/s',
              angle: -90,
              position: 'insideLeft',
              offset: 30,
              style: { fontSize: 9, fill: '#8b9ab3', fontFamily: 'JetBrains Mono' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="normal"
            stroke="#00ff88"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 3, stroke: '#00ff88' }}
          />
          <Line
            type="monotone"
            dataKey="malicious"
            stroke="#ff2d55"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 3, stroke: '#ff2d55' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
